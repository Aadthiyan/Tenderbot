"""
TenderBot Global — TinyFish Form-Fill Agent (Stretch P2 — Day 9)
Pre-fills government application forms with company profile data. Does NOT submit.
"""
import json
import logging
import httpx
from backend.config import get_settings
from backend.agents.portal_configs import FORM_FILL_GOAL

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"


async def run_form_fill(tender_url: str, profile: dict) -> dict:
    """
    Navigates to the tender application page and pre-fills common fields.
    Returns: { fields_filled, fields_remaining, completion_pct }
    """
    import json as _json
    profile_json = _json.dumps({
        k: v for k, v in profile.items()
        if k in (
            "company_name", "annual_turnover", "headcount",
            "years_in_business", "certifications", "alert_email",
            "headquarters_country", "website"
        )
    }, indent=2)

    goal = FORM_FILL_GOAL.format(url=tender_url, profile_json=profile_json)

    try:
        headers = {
            "X-API-Key": settings.tinyfish_api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {"url": tender_url, "goal": goal, "output_format": "json"}

        result = {}
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream(
                "POST", f"{TINYFISH_BASE_URL}/automation/run-sse",
                headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "result":
                            content = event.get("content", "{}")
                            result = _parse(content)
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue

        logger.info(
            f"Form-fill: {len(result.get('fields_filled', []))} fields filled, "
            f"{result.get('completion_pct', 0):.0f}% complete"
        )
        return result

    except Exception as e:
        logger.error(f"Form-fill failed: {e}")
        return {"fields_filled": [], "fields_remaining": [], "completion_pct": 0.0}


def _parse(content) -> dict:
    if isinstance(content, dict):
        return content
    try:
        if isinstance(content, str):
            content = content.strip()
            if content.startswith("```"):
                content = "\n".join(
                    l for l in content.split("\n") if not l.startswith("```")
                ).strip()
            return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass
    return {"fields_filled": [], "fields_remaining": [], "completion_pct": 0.0}
