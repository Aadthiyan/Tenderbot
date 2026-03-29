"""
TenderBot Global — Amendment Tracker Agent (Stub → Full implementation Day 7)
Re-visits watched tender pages and detects changes using TinyFish + LLM diff.
"""
import json
import logging
import httpx
import agentops
from datetime import datetime
from backend.config import get_settings
from backend.agents.portal_configs import AMENDMENT_GOAL
from backend.services.db import tenders_col, get_db
from backend.pipelines.auto_drafter import regenerate_draft

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"


async def check_amendments(tender: dict) -> None:
    """
    Re-visits the tender's page with TinyFish and compares to stored snapshot.
    If changes detected, updates amendment_history and flags the tender.
    """
    tender_id = tender.get("tender_id")
    raw_url = tender.get("raw_url")
    snapshot = tender.get("page_snapshot", "No previous snapshot available.")

    if not raw_url:
        return

    goal = AMENDMENT_GOAL.format(url=raw_url, snapshot=snapshot[:1500])

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["amendment_check"])
        except Exception:
            pass

    try:
        headers = {
            "Authorization": f"Bearer {settings.tinyfish_api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {"url": raw_url, "goal": goal, "output_format": "json"}

        result = None
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream(
                "POST", f"{TINYFISH_BASE_URL}/agent",
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
                            result = _parse_amendment_result(event.get("content", "{}"))
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue

        if not result or not result.get("has_changes"):
            logger.debug(f"No changes detected for tender {tender_id}")
            if session:
                session.end_session("Success")
            return

        # Build amendment event
        amendment_event = {
            "at": datetime.utcnow(),
            "change_type": result.get("change_type", "unknown"),
            "changes_summary": result.get("changes_summary", ""),
            "new_deadline": result.get("new_deadline"),
            "is_cancelled": result.get("is_cancelled", False),
        }

        # Update MongoDB
        update = {
            "$push": {"amendment_history": amendment_event},
            "$set": {
                "last_checked": datetime.utcnow(),
                "page_snapshot": result.get("page_snapshot", snapshot),
            }
        }
        if result.get("is_cancelled"):
            update["$set"]["status"] = "cancelled"
        if result.get("new_deadline"):
            update["$set"]["deadline"] = result["new_deadline"]

        await tenders_col().update_one({"tender_id": tender_id}, update)

        logger.info(
            f"Amendment detected for {tender_id}: "
            f"{result.get('change_type')} — {result.get('changes_summary', '')[:80]}"
        )

        # TODO (Day 7): Trigger Composio Slack alert for amendment
        # from backend.services.alerts_service import send_amendment_alert
        # await send_amendment_alert(tender_id, amendment_event)

        # ── Feature 4: Amendment-Triggered Re-Draft ──
        # If this tender was already drafted, regenerate it.
        db = get_db()
        drafts = await db["draft_queue"].find({"tender_id": tender_id}).to_list(length=10)
        for draft in drafts:
            company_name = draft.get("company_name")
            logger.info(f"🔄 Amendment detected on drafted tender {tender_id}. Triggering re-draft for {company_name}.")
            asyncio.create_task(regenerate_draft(tender_id, company_name, reason="amendment"))

        if session:
            session.end_session("Success")

    except Exception as e:
        logger.error(f"Amendment check failed for {tender_id}: {e}")
        if session:
            session.end_session("Fail")


def _parse_amendment_result(content) -> dict:
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
    return {"has_changes": False}
