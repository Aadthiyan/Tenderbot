"""
TenderBot Global — Alternative Sources Agent (Phase 2.3)
Discovers opportunities on non-traditional platforms:
- LinkedIn (contract/freelance projects)
- Private bidding platforms (BidNet, CompeteForward, etc.)
- Global marketplace sites (Alibaba, Upwork, Toptal)
- Grant/funding aggregators
"""
import httpx
import json
import logging
import agentops
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"

ALTERNATIVE_SOURCES_CONFIG = {
    "sources": [
        {
            "name": "LinkedIn Procurement",
            "url": "https://www.linkedin.com/jobs/search",
            "search_params": "keywords={keywords}&geoId=92000000",
            "focus": "Contract projects, RFP bids, corporate procurement needs"
        },
        {
            "name": "BidNet (SAM Alternative)",
            "url": "https://www.bidnet.com",
            "search_params": "s={keywords}",
            "focus": "State/local government RFP bids, construction, services"
        },
        {
            "name": "Global Tenders Database",
            "url": "https://www.globalmarket.com/search",
            "search_params": "keywords={keywords}",
            "focus": "International opportunities, private sector tenders"
        },
        {
            "name": "Alibaba.com Procurement",
            "url": "https://www.alibaba.com/trade/search",
            "search_params": "SearchText={keywords}&pageNum=1",
            "focus": "B2B supply contracts, manufacturing, wholesale tenders"
        },
        {
            "name": "Upwork + Toptal (Services)",
            "url": "https://www.upwork.com/search/jobs",
            "search_params": "q={keywords}&location=anywhere",
            "focus": "Contract service opportunities, consulting bids"
        }
    ]
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_alternative_sources_agent(keywords: list[str], company_skills: str = None) -> list[dict]:
    """
    Searches alternative (non-government) procurement platforms for opportunities.
    Covers LinkedIn, private bidding sites, marketplaces, and grant aggregators.
    
    Args:
        keywords: List of search keywords
        company_skills: Company capabilities for filtering
    
    Returns:
        List of opportunities from alternative sources
    """
    keyword_str = " ".join(keywords[:5]) if keywords else "technology services"
    company_skills = company_skills or "consulting, software development, services"
    
    logger.info(f"🌐 Launching Alternative Sources Agent | Keywords: '{keyword_str}'")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["alternative_sources", "non_government"])
        except Exception as e:
            logger.debug(f"AgentOps bypass: {e}")

    try:
        all_opportunities = []
        
        # Search each alternative source
        for source in ALTERNATIVE_SOURCES_CONFIG["sources"]:
            try:
                opps = await _search_single_source(source, keyword_str, company_skills)
                for opp in opps:
                    opp["_source_portal"] = f"alt_{source['name'].lower().replace(' ', '_')}"
                    opp["_source_type"] = "alternative"
                all_opportunities.extend(opps)
            except Exception as e:
                logger.warning(f"⚠️ Failed to search {source['name']}: {e}")
                continue

        if session:
            session.record(agentops.ActionEvent(
                action_type="alternative_sources_complete",
                returns={"opportunities_found": len(all_opportunities)}
            ))
            session.end_session(end_state="Success")

        logger.info(f"✅ Alternative Sources Agent finished — Found {len(all_opportunities)} opportunities.")
        return all_opportunities

    except Exception as e:
        if session:
            session.end_session(end_state="Fail")
        logger.error(f"❌ Alternative Sources Agent failed: {e}")
        raise


async def _search_single_source(source: dict, keywords: str, company_skills: str) -> list[dict]:
    """Search a single alternative procurement source."""
    if not settings.tinyfish_api_key:
        return []

    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    
    goal = f"""
        You are searching {source['name']} for procurement opportunities that match: {keywords}
        Company skills: {company_skills}
        
        Steps:
        1. Navigate to {source['name']}
        2. Use their search function with keywords: {keywords}
        3. Filter for: {source['focus']}
        4. Extract from each result:
           - title: opportunity/project title
           - organization: client/buyer name
           - url: direct link to opportunity
           - deadline: submission/application deadline
           - budget_range: estimated value (if shown)
           - description: brief overview
           - opportunity_type: RFP, contract, freelance project, grant, etc.
           - posted_date: when it was posted
        5. Focus on active opportunities only (not closed/filled)
        6. Return as JSON array with all fields above (use null for missing values)
    """
    
    payload = {
        "url": source["url"],
        "goal": goal,
        "output_format": "json",
    }

    result_data = []

    try:
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream("POST", f"{TINYFISH_BASE_URL}/automation/run-sse", headers=headers, json=payload) as response:
                if response.status_code == 401:
                    raise ValueError("Unauthorized. Check TINYFISH_API_KEY.")
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.startswith("data:"): 
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]": 
                        break
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "COMPLETE":
                            result_obj = event.get("result", {})
                            if isinstance(result_obj, dict):
                                content = result_obj.get("result", "")
                            else:
                                content = result_obj
                            
                            if content:
                                if isinstance(content, str):
                                    result_data = _parse_json(content)
                                elif isinstance(content, list):
                                    result_data = content
                                elif isinstance(content, dict):
                                    result_data = [content]
                                break
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        logger.warning(f"Error searching {source['name']}: {e}")
        return []

    return result_data


def _parse_json(content: str) -> list[dict]:
    """Parse TinyFish LLM output."""
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(l for l in content.split("\n") if not l.startswith("```")).strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list): return parsed
        for key in ["opportunities", "results", "projects", "opportunities_list", "data"]:
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        return [parsed] if parsed else []
    except json.JSONDecodeError:
        return []
