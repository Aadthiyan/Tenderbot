"""
TenderBot Global — UNGM Search Agent (Phase 2.3)
Autonomous TinyFish agent tailored for UNGM (United Nations Global Marketplace).
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

# ── UNGM Specific Configuration ───────────────────────────────────────────────
# UI Elements Documented:
# 1. Search Bar: Usually a "Title or reference" input field or general keyword field.
# 2. Dynamic Filters: Sidebar or top bar dropdowns for "Status" (must be Open) and "UN Organization".
# 3. Dynamic Loading: Results load asynchronously as you type or click filters (Angular/SPA behavior).
# 4. Organization Codes: The "organization" field often uses acronyms (e.g., WHO, UNICEF, UNDP).

UNGM_CONFIG = {
    # We point directly to the public notice board.
    "url_template": "https://www.ungm.org/Public/Notice",
    
    "goal": """
        You are browsing the UNGM (United Nations Global Marketplace) notice board for procurement opportunities.
        Search keyword: '{kw}'.
        
        Steps:
        1. Wait for the dynamic notice board to fully load. Dismiss any cookie or notification popups.
        2. Locate the search or keyword filter input field and enter '{kw}'. Press Enter or click search if required.
        3. Ensure the filter for notice status is set to 'Open' / 'Active'.
        4. Wait a few seconds for the asynchronous results to refresh.
        5. For each of the first {max_pages} pages (or up to 20 results), extract the following:
           - reference_number: the unique UNGM reference number (or agency reference)
           - title: the full notice title
           - organization: the UN agency or body issuing the notice (preserve the acronym if available, e.g., 'UNICEF', 'WHO', 'UNDP')
           - deadline: the closing/submission deadline date and time
           - category: the procurement category or UNSPSC classification if visible
           - description: a brief description or synopsis (first 300 chars, if visible without clicking)
           - url: the direct link to the notice detail page (very important)
        6. Return the extracted data as a pure JSON array. Each element must contain all keys above. Use null for missing values.
        7. DO NOT click into individual notices unless absolutely necessary to get the URL; prefer extracting from the list view.
    """
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_ungm_agent(keywords: list[str]) -> list[dict]:
    """
    Launches a TinyFish agent on UNGM.
    Includes AgentOps telemetry and specific handling for UN organization acronyms.
    """
    keyword_str = " ".join(keywords[:5]) if keywords else "technology services"
    
    url = UNGM_CONFIG["url_template"]
    goal = UNGM_CONFIG["goal"].format(
        kw=keyword_str,
        max_pages=settings.max_portal_pages,
    )

    logger.info(f"🚀 Launching UNGM TinyFish Agent | Keywords: '{keyword_str}'")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["ungm", "portal_scrape"])
        except Exception as e:
            logger.debug(f"AgentOps bypass: {e}")

    try:
        tenders = await _execute_tinyfish(url, goal)
        
        # Inject portal identifier and standardize country
        for t in tenders:
            t["_source_portal"] = "ungm"
            t["country"] = "UN"  # Universal indicator for global UN tenders
            
            # Simple organization normalization (uppercase acronyms)
            if t.get("organization"):
                org_str = str(t["organization"]).strip()
                # If it's a short acronym or clearly meant to be one, uppercase it
                if len(org_str) <= 6:
                    t["organization"] = org_str.upper()

        if session:
            session.record(agentops.ActionEvent(
                action_type="ungm_scrape_complete",
                returns={"tenders_found": len(tenders)}
            ))
            session.end_session(end_state="Success")

        logger.info(f"✅ UNGM Agent finished — Extracted {len(tenders)} tenders.")
        return tenders

    except Exception as e:
        if session:
            session.record(agentops.ActionEvent(
                action_type="ungm_scrape_failed",
                returns={"error": str(e)}
            ))
            session.end_session(end_state="Fail")
        logger.error(f"❌ UNGM Agent failed: {e}")
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
    with open("backend/sample_output/ungm_10_tenders.json", "r", encoding="utf-8") as f:
        return json.load(f)
