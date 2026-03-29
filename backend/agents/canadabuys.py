"""
TenderBot Global — CanadaBuys Agent (Phase 2.5)
Autonomous TinyFish agent tailored for CanadaBuys holding Canadian government RFPs.
"""
import httpx
import json
import logging
import agentops
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"

CANADABUYS_CONFIG = {
    # status=1 filters to Open tenders
    "url_template": "https://canadabuys.canada.ca/en/tender-opportunities?q={kw}&status=1",
    
    "goal": """
        You are searching CanadaBuys for active Canadian government procurement opportunities.
        Search keyword: '{kw}'.
        
        Steps:
        1. Wait for the search results to load. Dismiss any cookie or consent banners.
        2. Ensure the filter is set to 'Open' status. 
        3. For each result on the first {max_pages} pages, extract:
           - solicitation_number: the solicitation or reference identifier
           - title: the English tender title
           - department: the issuing government department (e.g. Shared Services Canada, DND)
           - closing_date: the submission deadline date and time
           - procurement_category: the category (e.g. Goods, Services, Construction)
           - region: the Canadian province or territory (if national, state 'Canada-wide')
           - url: the direct link to the tender detail page
        4. Navigate to the next page using pagination controls as needed.
        5. Return the extracted data as a pure JSON array. Each element must contain all keys above. Use null for missing values.
        6. DO NOT enter individual tender pages. Read from the list.
    """
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_canadabuys_agent(keywords: list[str]) -> list[dict]:
    """Launches TinyFish agent on CanadaBuys."""
    keyword_str = " ".join(keywords[:5]) if keywords else "technology"
    url = CANADABUYS_CONFIG["url_template"].format(kw=keyword_str)
    goal = CANADABUYS_CONFIG["goal"].format(
        kw=keyword_str, max_pages=settings.max_portal_pages
    )

    logger.info(f"🚀 Launching CanadaBuys Agent | Keywords: '{keyword_str}'")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["canadabuys", "portal_scrape"])
        except Exception:
            pass

    try:
        tenders = await _execute_tinyfish(url, goal)
        for t in tenders:
            t["_source_portal"] = "canadabuys"
            t["country"] = "CA"

        if session:
            session.record(agentops.ActionEvent(
                action_type="canadabuys_scrape_complete", returns={"found": len(tenders)}
            ))
            session.end_session("Success")
        logger.info(f"✅ CanadaBuys Agent finished — {len(tenders)} tenders.")
        return tenders

    except Exception as e:
        if session:
            session.end_session("Fail")
        logger.error(f"❌ CanadaBuys Agent failed: {e}")
        raise


async def _execute_tinyfish(url: str, goal: str) -> list[dict]:
    if not settings.tinyfish_api_key:
        import asyncio
        await asyncio.sleep(2)
        return _get_mock_data()

    headers = {"Authorization": f"Bearer {settings.tinyfish_api_key}", "Accept": "text/event-stream"}
    payload = {"url": url, "goal": goal, "output_format": "json"}
    result_data = []

    async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
        async with client.stream("POST", f"{TINYFISH_BASE_URL}/agent", headers=headers, json=payload) as response:
            if response.status_code == 401: raise ValueError("Unauthorized")
            async for line in response.aiter_lines():
                if not line.startswith("data:"): continue
                raw = line[5:].strip()
                if raw == "[DONE]": break
                try:
                    event = json.loads(raw)
                    if event.get("type") == "result":
                        result_data = _parse_json(event.get("content", ""))
                        break
                except json.JSONDecodeError: pass
    return result_data

def _parse_json(content: str) -> list[dict]:
    content = content.strip().replace("```json", "").replace("```", "")
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list): return parsed
        for k in ["tenders", "results", "opportunities"]:
            if isinstance(parsed.get(k), list): return parsed[k]
        return [parsed]
    except json.JSONDecodeError: return []

def _get_mock_data() -> list[dict]:
    with open("backend/sample_output/canadabuys_10_tenders.json", "r") as f:
        return json.load(f)
