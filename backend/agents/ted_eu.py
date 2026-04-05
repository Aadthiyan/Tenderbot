"""
TenderBot Global — TED EU Search Agent (Phase 2.2)
Autonomous TinyFish agent tailored for TED (Tenders Electronic Daily) procurement discovery.
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

# ── TED EU Specific Configuration ─────────────────────────────────────────────
# UI Elements Documented:
# 1. Cookie Consent: Intrusive banner at the bottom or modal, must be accepted.
# 2. Search URL: Pre-filtered for active ('ALL' scope) and sorted by publication date descending.
# 3. Multilingual UI: Titles may appear in national languages, but English versions are often available.
# 4. Pagination: Standard numbered pagination at the bottom.

TED_EU_CONFIG = {
    "url_template": "https://ted.europa.eu/en/search?q={kw}&scope=ALL&sortColumn=ND_OJ&sortOrder=desc",
    
    "goal": """
        You are searching TED (Tenders Electronic Daily) for active EU government procurement notices.
        Search keyword: '{kw}'.
        
        Steps:
        1. Accept or close the cookie consent banner/modal immediately if it appears.
        2. Wait for the search results list to fully render.
        3. For each result on the current page, extract the following:
           - title: the opportunity title (if multiple languages are shown, extract the ENGLISH title. If only local language is shown, extract that but try to translate to English if possible).
           - contracting_authority: the buyer or agency name.
           - country: the ISO country code of the contracting authority (e.g., DE, FR, IT). If not explicitly stated as a code, infer it from the location/buyer name.
           - cpv_code: The main CPV (Common Procurement Vocabulary) code if visible.
           - deadline: the submission/closing date for the tender.
           - estimated_value: the contract value. Extract only the EUR amount if possible.
           - procedure_type: e.g., Open, Restricted, Negotiated.
           - url: the direct link to the full notice HTML page.
        4. Navigate to the next page using the pagination controls and repeat until you have scanned {max_pages} pages.
        5. Return the extracted data as a pure JSON array. Each element must contain all keys above. Use null for missing values.
        6. DO NOT enter individual tender pages — only extract data from the search listing to save time.
    """
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def run_ted_eu_agent(keywords: list[str]) -> list[dict]:
    """
    Launches a TinyFish agent on TED EU.
    Includes AgentOps telemetry, multilingual instruction, and outputs verified JSON.
    """
    keyword_str = " ".join(keywords[:5]) if keywords else "technology services"
    
    url = TED_EU_CONFIG["url_template"].format(kw=keyword_str)
    goal = TED_EU_CONFIG["goal"].format(
        kw=keyword_str,
        max_pages=settings.max_portal_pages,
    )

    logger.info(f"🚀 Launching TED EU TinyFish Agent | Keywords: '{keyword_str}'")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["ted_eu", "portal_scrape"])
        except Exception as e:
            logger.debug(f"AgentOps bypass: {e}")

    try:
        tenders = await _execute_tinyfish(url, goal)
        
        # Inject portal identifier and standardize
        for t in tenders:
            t["_source_portal"] = "ted_eu"
            
            # Country fallback logic if TinyFish failed to extract an ISO code
            if not t.get("country"):
                t["country"] = "EU"
            else:
                t["country"] = str(t["country"]).upper()[:2] # Ensure 2-letter ISO

        if session:
            session.record(agentops.ActionEvent(
                action_type="ted_eu_scrape_complete",
                returns={"tenders_found": len(tenders)}
            ))
            session.end_session(end_state="Success")

        logger.info(f"✅ TED EU Agent finished — Extracted {len(tenders)} tenders.")
        return tenders

    except Exception as e:
        if session:
            session.record(agentops.ActionEvent(
                action_type="ted_eu_scrape_failed",
                returns={"error": str(e)}
            ))
            session.end_session(end_state="Fail")
        logger.error(f"❌ TED EU Agent failed: {e}")
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
    with open("backend/sample_output/ted_eu_10_tenders.json", "r", encoding="utf-8") as f:
        return json.load(f)
