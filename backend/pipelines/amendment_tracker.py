"""
TenderBot Global — Amendment & Cancellation Tracker (Phase 5.2)
Uses TinyFish to revisit a tender URL, compare against the previous plain-text snapshot,
and automatically detect deadline changes, new documents, or cancellations.
"""
import json
import logging
import httpx
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings
from backend.agents.portal_configs import AMENDMENT_GOAL

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=4, max=15), reraise=True)
async def check_for_amendments(tender: dict) -> dict | None:
    """
    Re-visits a tender URL using TinyFish and provides the previous snapshot for comparison.
    Returns an amendment JSON object if meaningful changes occurred, otherwise None.
    """
    if "raw_url" not in tender or not tender.get("page_snapshot"):
        logger.debug(f"Tender {tender.get('tender_id')} missing URL or snapshot for amendment check.")
        return None

    goal = AMENDMENT_GOAL.format(
        url=tender["raw_url"],
        snapshot=tender["page_snapshot"]
    )
    
    if not settings.tinyfish_api_key:
        import asyncio
        import random
        await asyncio.sleep(1)
        
        # In this mock, we force an amendment to simulate detecting a deadline change
        if tender.get("force_mock_amendment", False):
            return {
                "has_changes": True,
                "change_type": "deadline_extension",
                "changes_summary": "The submission deadline has been extended by 14 days due to clarification questions.",
                "new_deadline": "2026-08-15T00:00:00Z",
                "is_cancelled": False,
                "page_snapshot": tender["page_snapshot"] + "\n\n[UPDATE] Deadline extended to 15 Aug 2026.",
                "detected_at": datetime.utcnow().isoformat()
            }
        return None

    headers = {
        "Authorization": f"Bearer {settings.tinyfish_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "url": tender["raw_url"],
        "goal": goal,
        "output_format": "json"
    }

    result = {}
    try:
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream("POST", f"{TINYFISH_BASE_URL}/agent", headers=headers, json=payload) as response:
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
                        continue
                        
        if result and result.get("has_changes") is True:
            result["detected_at"] = datetime.utcnow().isoformat()
            logger.info(f"🚨 Amendment detected for {tender.get('tender_id')}: {result.get('change_type')}")
            return result
            
        logger.debug(f"No amendments for {tender.get('tender_id')}.")
        return None
        
    except Exception as e:
        logger.error(f"Amendment check failed for {tender.get('raw_url')}: {e}")
        return None
