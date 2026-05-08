"""
TenderBot Global — Web Search Agent (Phase 2.2)
Autonomous TinyFish agent that searches the entire internet for procurement opportunities.
Uses Google/Bing search to discover RFPs, tenders, grants, and contracts across all websites.
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

WEB_SEARCH_CONFIG = {
    # Use Google Search (via TinyFish navigation) to find opportunities
    "url": "https://www.google.com/search",
    
    "goal": """
        You are searching the entire internet for procurement opportunities, RFPs, tenders, grants, and contracts.
        Company competencies: '{company_skills}'.
        Search keywords: '{keywords}'.
        
        Steps:
        1. Go to Google search.
        2. Search for: '{search_query}'
        3. For each relevant result on the first 3 pages:
           - Record the opportunity title/name
           - Extract the organization/company posting it (buyer)
           - Capture the URL link
           - Get the deadline (if visible on search result or snippet)
           - Note the opportunity type (RFP, tender, grant, contract bid, etc.)
           - Brief description from the snippet
        4. Return ONLY opportunities that match these criteria:
           - Posted in last 90 days
           - Open for application/submission (not closed/awarded)
           - Related to: {keywords}
           - Value/Budget visible (if available)
        5. Return as pure JSON array with these keys: title, organization, url, deadline, opportunity_type, description, value, posting_date
    """
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_web_search_agent(keywords: list[str], company_skills: str = None) -> list[dict]:
    """
    Launches a TinyFish web search agent to find opportunities across the entire internet.
    Includes AgentOps telemetry and outputs verified JSON.
    
    Args:
        keywords: List of search keywords (e.g., ["cybersecurity", "cloud", "software"])
        company_skills: Comma-separated company competencies (e.g., "Python, AWS, DevOps")
    
    Returns:
        List of opportunities found via web search
    """
    keyword_str = " ".join(keywords[:5]) if keywords else "technology services"
    company_skills = company_skills or "consulting, software development, cloud services"
    
    # Build a comprehensive search query
    search_terms = [keyword_str, "RFP OR tender OR contract OR grant OR bid OR procurement"]
    search_query = " ".join(search_terms)
    
    logger.info(f"🔍 Launching Web Search Agent | Keywords: '{keyword_str}' | Skills: '{company_skills}'")

    # Start AgentOps Tracker
    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["web_search", "internet_scrape"])
        except Exception as e:
            logger.debug(f"AgentOps bypass: {e}")

    try:
        opportunities = await _execute_tinyfish_search(
            search_query=search_query,
            keywords=keyword_str,
            company_skills=company_skills
        )
        
        # Inject search metadata
        for opp in opportunities:
            opp["_source_portal"] = "web_search"
            opp["_search_type"] = "internet_wide"

        if session:
            session.record(agentops.ActionEvent(
                action_type="web_search_complete",
                returns={"opportunities_found": len(opportunities)}
            ))
            session.end_session(end_state="Success")

        logger.info(f"✅ Web Search Agent finished — Found {len(opportunities)} opportunities.")
        return opportunities

    except Exception as e:
        if session:
            session.record(agentops.ActionEvent(
                action_type="web_search_failed",
                returns={"error": str(e)}
            ))
            session.end_session(end_state="Fail")
        logger.error(f"❌ Web Search Agent failed: {e}")
        raise


async def _execute_tinyfish_search(search_query: str, keywords: str, company_skills: str) -> list[dict]:
    """Handles SSE stream from TinyFish web search API."""
    if not settings.tinyfish_api_key:
        logger.warning("TinyFish API Key missing — Returning empty list.")
        return []

    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "url": WEB_SEARCH_CONFIG["url"],
        "goal": WEB_SEARCH_CONFIG["goal"].format(
            search_query=search_query,
            keywords=keywords,
            company_skills=company_skills
        ),
        "output_format": "json",
    }

    result_data = []

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
                    
                    # Handle "COMPLETE" event format (TinyFish)
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
                    
                    elif event.get("type") == "error":
                        raise ValueError(f"Agent error: {event.get('message')}")
                except json.JSONDecodeError:
                    pass

    return result_data


def _parse_json(content: str) -> list[dict]:
    """Sanitize and parse TinyFish LLM output."""
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(l for l in content.split("\n") if not l.startswith("```")).strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list): return parsed
        for key in ["opportunities", "results", "tenders", "contracts", "data"]:
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        return [parsed] if parsed else []
    except json.JSONDecodeError:
        return []
