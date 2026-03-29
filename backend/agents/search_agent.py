"""
TenderBot Global — TinyFish Portal Search Agent
Executes a natural-language goal on a government portal and returns structured tender JSON.
"""
import httpx
import json
import logging
import agentops
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import get_settings
from backend.agents.portal_configs import PORTAL_CONFIGS

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def scrape_portal(portal_key: str, keywords: list[str]) -> list[dict]:
    """
    Launches a TinyFish agent on the specified portal.
    
    Args:
        portal_key: One of the keys in PORTAL_CONFIGS (e.g. 'sam_gov')
        keywords: List of search keywords from the user profile
    
    Returns:
        List of raw tender dicts with '_source_portal' injected.
    """
    config = PORTAL_CONFIGS.get(portal_key)
    if not config:
        logger.warning(f"Unknown portal key: '{portal_key}'")
        return []

    kw = " ".join(keywords[:5]) if keywords else "technology services"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Build URL with keyword injection
    url = config["url"].format(
        kw=kw,
        today=today,
        thirty_days_ago_=thirty_days_ago,
        **{"30d_ago": thirty_days_ago},
    )

    # Build the natural-language goal
    goal = config["goal"].format(
        kw=kw,
        max_pages=settings.max_portal_pages,
        today=today,
    )

    logger.info(f"Launching TinyFish agent on {portal_key} | keywords: '{kw}'")

    # ── AgentOps tracking ─────────────────────────────────────────────────────
    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=[portal_key, "portal_scrape"])
        except Exception:
            pass

    try:
        tenders = await _call_tinyfish(url=url, goal=goal)

        # Inject source portal for normalizer
        for t in tenders:
            t["_source_portal"] = portal_key

        if session:
            session.record(agentops.ActionEvent(
                action_type="portal_scrape_complete",
                returns={"portal": portal_key, "tenders_found": len(tenders)}
            ))
            session.end_session("Success")

        logger.info(f"TinyFish [{portal_key}]: {len(tenders)} tenders extracted")
        return tenders

    except Exception as e:
        if session:
            session.record(agentops.ActionEvent(
                action_type="portal_scrape_failed",
                returns={"portal": portal_key, "error": str(e)}
            ))
            session.end_session("Fail")
        raise


async def _call_tinyfish(url: str, goal: str) -> list[dict]:
    """
    Makes the TinyFish /agent streaming call and parses the final JSON result.
    TinyFish streams Server-Sent Events (SSE); we consume until the result event.
    """
    headers = {
        "Authorization": f"Bearer {settings.tinyfish_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json",  # instruct TinyFish to return structured JSON
    }

    result_data = []

    async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
        async with client.stream(
            "POST",
            f"{TINYFISH_BASE_URL}/agent",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        event = json.loads(raw)
                        # TinyFish sends a final "result" event with extracted data
                        if event.get("type") == "result":
                            content = event.get("content", "")
                            result_data = _parse_json_result(content)
                            break
                        elif event.get("type") == "error":
                            raise ValueError(f"TinyFish agent error: {event.get('message')}")
                    except (json.JSONDecodeError, KeyError):
                        continue

    return result_data if isinstance(result_data, list) else []


def _parse_json_result(content: str) -> list[dict]:
    """
    Extract a JSON array from TinyFish result content.
    Handles cases where content is already parsed or embedded in markdown.
    """
    if isinstance(content, list):
        return content
    if isinstance(content, dict):
        return [content]

    content = content.strip()

    # Strip markdown code fence if present
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(
            line for line in lines
            if not line.startswith("```")
        ).strip()

    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # TinyFish may wrap results: {"tenders": [...]} or {"results": [...]}
            for key in ("tenders", "results", "data", "items", "opportunities"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            return [parsed]
    except json.JSONDecodeError as e:
        logger.warning(f"Could not parse TinyFish result as JSON: {e}")
        return []

    return []
