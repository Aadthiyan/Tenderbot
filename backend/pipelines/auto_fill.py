"""
TenderBot Global — Auto Form-Fill Assistant (Phase 5.4)
Uses TinyFish to navigate to an application page, map company profile fields 
to form inputs, and pre-fill them without submitting.
"""
import json
import logging
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings
from backend.agents.portal_configs import FORM_FILL_GOAL

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=3, max=10), reraise=True)
async def auto_fill_form(url: str, profile: dict) -> dict:
    """
    Directs TinyFish to a form URL, providing the company profile as JSON.
    TinyFish will attempt to fill the form inputs matching the profile fields,
    reporting back the completion status.
    """
    logger.info(f"Initiating auto form-fill for URL: {url}")
    
    if not settings.tinyfish_api_key:
        await asyncio.sleep(2)
        # Mocking the response for demonstration when API Key is absent
        return {
            "fields_filled": ["Company Name", "Registration Number", "Contact Email", "Address", "Years in Business"],
            "fields_remaining": ["DUNS Number", "SAM.gov CAGE Code"],
            "completion_pct": 71.4,
            "status": "success",
            "message": "Form pre-filled successfully. Awaiting user review."
        }

    profile_json = json.dumps(profile, indent=2)
    goal = FORM_FILL_GOAL.format(url=url, profile_json=profile_json)
    
    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json"
    }

    result = {}
    try:
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream("POST", f"{TINYFISH_BASE_URL}/automation/run-sse", headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"): continue
                    raw = line[5:].strip()
                    if raw == "[DONE]": break
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "result":
                            content = event.get("content", "{}")
                            if isinstance(content, str):
                                if content.strip().startswith("```"):
                                    c_lines = content.strip().split("\n")
                                    content = "\n".join(l for l in c_lines if not l.startswith("```")).strip()
                                content = json.loads(content)
                            result = content
                            break
                    except (json.JSONDecodeError, KeyError):
                        pass
        
        result["status"] = "success" if result.get("completion_pct", 0) > 0 else "action_required"
        result["message"] = "Form pre-filled with available profile data."
        return result
        
    except Exception as e:
        logger.error(f"Auto form-fill failed for {url}: {e}")
        return {
            "fields_filled": [],
            "fields_remaining": [],
            "completion_pct": 0.0,
            "status": "failed",
            "message": str(e)
        }
