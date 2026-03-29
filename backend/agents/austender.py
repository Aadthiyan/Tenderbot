"""
TenderBot Global — AusTender Agent (Phase 2.5)
Autonomous TinyFish agent tailored for the Australian Government's AusTender portal.
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

AUSTENDER_CONFIG = {
    # Direct access to search view, sorting by updated desc
    "url_template": "https://www.tenders.gov.au/?event=public.atm.list",
    
    "goal": """
        You are searching AusTender (Australian Government) for open 'Approaches to Market' (ATMs).
        Search keyword: '{kw}'.
        
        Steps:
        1. Find the search or filter form on the page and enter keyword: '{kw}'.
        2. Filter the status to show only 'Open' ATMs. Submit/Click Search.
        3. Wait for the list to load.
        4. For each of the first {max_pages} pages (use pagination buttons at bottom), extract:
           - atm_id: the ATM ID or reference number
           - title: the tender title
           - agency: the issuing Australian government agency
           - close_date: the closing date for submissions
           - value: estimated contract value if visible (often hidden on AusTender, use null if so)
           - category: procurement category (UNSPSC or raw string)
           - state: the Australian state/territory of performance
           - url: the direct link to the full ATM listing
        5. Return the extracted data as a pure JSON array. Each element must contain all keys above. Use null for missing values.
        6. DO NOT click into individual ATMs to save time. Extract from the main list.
    """
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_austender_agent(keywords: list[str]) -> list[dict]:
    """Launches TinyFish agent on AusTender."""
    keyword_str = " ".join(keywords[:5]) if keywords else "digital project"
    url = AUSTENDER_CONFIG["url_template"]
    goal = AUSTENDER_CONFIG["goal"].format(
        kw=keyword_str, max_pages=settings.max_portal_pages
    )

    logger.info(f"🚀 Launching AusTender Agent | Keywords: '{keyword_str}'")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["austender", "portal_scrape"])
        except Exception:
            pass

    try:
        tenders = await _execute_tinyfish(url, goal)
        for t in tenders:
            t["_source_portal"] = "austender"
            t["country"] = "AU"

        if session:
            session.record(agentops.ActionEvent(
                action_type="austender_scrape_complete", returns={"found": len(tenders)}
            ))
            session.end_session("Success")
        logger.info(f"✅ AusTender Agent finished — {len(tenders)} tenders.")
        return tenders

    except Exception as e:
        if session:
            session.end_session("Fail")
        logger.error(f"❌ AusTender Agent failed: {e}")
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
        for k in ["tenders", "results", "atms"]:
            if isinstance(parsed.get(k), list): return parsed[k]
        return [parsed]
    except json.JSONDecodeError: return []

def _get_mock_data() -> list[dict]:
    with open("backend/sample_output/austender_10_tenders.json", "r") as f:
        return json.load(f)
