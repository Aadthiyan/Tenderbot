"""
TenderBot Global — Find a Tender Agent (Phase 2.4)
Autonomous TinyFish agent tailored for the UK Government's Find a Tender service.
"""
import httpx
import json
import logging
import agentops
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"

# ── Find a Tender (UK) Specific Configuration ─────────────────────────────────
# UI Elements Documented:
# 1. Search Form: URL handles basic keyword mapping.
# 2. Filtering: 'status=live' limits to open notices.
# 3. Data Structure: UK uses CPV codes (like the EU) but formats value/dates differently (DD/MM/YYYY).
# 4. Pagination: Standard pagination bar at the bottom.

FTS_CONFIG = {
    # Pre-filter for live statuses to save agent clicks
    "url_template": "https://www.find-a-tender.service.gov.uk/Search?keywords={kw}&status=live",
    
    "goal": """
        You are searching 'Find a Tender' (the UK government procurement portal) for live opportunities.
        Search keyword: '{kw}'.
        
        Steps:
        1. Wait for the search results page to load. If there is a cookie banner, dismiss it.
        2. Filter confirmation: The status filter should already be 'live/open'.
        3. For each notice listed on the current page, extract the following:
           - title: the opportunity title
           - buyer_name: the buying organisation or contracting authority
           - published_date: when the notice was published (often in DD/MM/YYYY format)
           - closing_date: the submission deadline or closing date (often in DD/MM/YYYY format)
           - contract_value: the estimated or exact maximum contract value (ensure it captures GBP/£ amounts if visible)
           - cpv_codes: the Common Procurement Vocabulary codes associated with the tender
           - procedure: the procedure type (e.g., Open procedure, Competitive dialogue)
           - url: the direct, full URL to view the notice details (vital)
        4. Locate the next page button in the pagination section at the bottom, and click it. 
        5. Repeat extraction until you have collected data from {max_pages} pages.
        6. Return the extracted data as a pure JSON array. Each element must contain all keys above. Use null for missing values.
        7. DO NOT click into individual notices to save time. Rely on data available in the search snippets.
    """
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_find_a_tender_agent(keywords: list[str]) -> list[dict]:
    """
    Launches a TinyFish agent on UK Find a Tender.
    Includes AgentOps telemetry, handles UK date extraction via TinyFish, and outputs verified JSON.
    """
    keyword_str = " ".join(keywords[:5]) if keywords else "digital services"
    
    url = FTS_CONFIG["url_template"].format(kw=keyword_str)
    goal = FTS_CONFIG["goal"].format(
        kw=keyword_str,
        max_pages=settings.max_portal_pages,
    )

    logger.info(f"🚀 Launching Find a Tender Agent (UK) | Keywords: '{keyword_str}'")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["find_a_tender", "portal_scrape"])
        except Exception as e:
            logger.debug(f"AgentOps bypass: {e}")

    try:
        tenders = await _execute_tinyfish(url, goal)
        
        # Inject portal identifier and standardize country
        for t in tenders:
            t["_source_portal"] = "find_a_tender"
            t["country"] = "UK"

        if session:
            session.record(agentops.ActionEvent(
                action_type="find_a_tender_scrape_complete",
                returns={"tenders_found": len(tenders)}
            ))
            session.end_session(end_state="Success")

        logger.info(f"✅ Find a Tender Agent finished — Extracted {len(tenders)} tenders.")
        return tenders

    except Exception as e:
        if session:
            session.record(agentops.ActionEvent(
                action_type="find_a_tender_scrape_failed",
                returns={"error": str(e)}
            ))
            session.end_session(end_state="Fail")
        logger.error(f"❌ Find a Tender Agent failed: {e}")
        raise


async def _execute_tinyfish(url: str, goal: str) -> list[dict]:
    """Handles SSE stream from TinyFish API."""
    if not settings.tinyfish_api_key:
        logger.warning("TinyFish API Key missing — Returning mock data instead of failing.")
        import asyncio
        await asyncio.sleep(2)
        return _get_mock_data()

    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json",
    }

    result_data = []

    async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
        async with client.stream("POST", f"{TINYFISH_BASE_URL}/automation/run-sse", headers=headers, json=payload) as response:
            if response.status_code == 401:
                raise ValueError("Unauthorized. Check TINYFISH_API_KEY.")
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line.startswith("data:"): continue
                raw = line[5:].strip()
                if raw == "[DONE]": break
                try:
                    event = json.loads(raw)
                    if event.get("type") == "result":
                        content = event.get("content", "")
                        result_data = _parse_json(content)
                        break
                    elif event.get("type") == "error":
                        raise ValueError(f"Agent error: {event.get('message')}")
                except json.JSONDecodeError:
                    pass

    return result_data


def _parse_json(content: str) -> list[dict]:
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(l for l in content.split("\n") if not l.startswith("```")).strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list): return parsed
        for key in ["tenders", "results", "data", "opportunities", "notices"]:
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        return [parsed]
    except json.JSONDecodeError:
        return []

def _get_mock_data() -> list[dict]:
    """Fallback sample data if API key is not yet configured."""
    with open("backend/sample_output/find_a_tender_10_tenders.json", "r", encoding="utf-8") as f:
        return json.load(f)
