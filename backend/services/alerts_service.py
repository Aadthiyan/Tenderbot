"""
TenderBot Global — Composio Alerts Service
Sends Slack and email alerts via Composio for new tenders, deadlines, and amendments.
"""
import logging
from datetime import datetime, timedelta
from backend.config import get_settings
from backend.services.db import tenders_col, alerts_col

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_composio_toolset():
    """Lazy import so startup doesn't fail if composio isn't configured yet."""
    from composio_openai import ComposioToolSet, Action
    return ComposioToolSet(api_key=settings.composio_api_key), Action


async def sweep_and_dispatch_alerts() -> dict:
    """
    Daily alert sweep:
    1. New tenders with score >= threshold (not yet alerted)
    2. Tenders with deadline <= 48 hours
    Returns summary of alerts sent.
    """
    if not settings.composio_api_key:
        logger.warning("Composio API key not set — skipping alerts.")
        return {"sent": 0}

    sent = 0
    now = datetime.utcnow()
    deadline_cutoff = now + timedelta(hours=48)

    # ── 1. New high-score tenders ─────────────────────────────────────────────
    new_tenders = await tenders_col().find(
        {
            "relevance_score": {"$gte": settings.alert_score_threshold},
            "status": "active",
            "scraped_at": {"$gte": now - timedelta(hours=25)},  # last 25h
        },
        {"tender_id": 1, "title": 1, "agency": 1, "country": 1,
         "estimated_value": 1, "relevance_score": 1, "days_until_deadline": 1,
         "raw_url": 1, "_id": 0}
    ).limit(10).to_list(length=10)

    for tender in new_tenders:
        # Dedup: check if we already sent this alert
        existing = await alerts_col().find_one({
            "tender_id": tender["tender_id"],
            "alert_type": "new_match",
        })
        if existing:
            continue
        await send_new_tender_alert(tender)
        sent += 1

    # ── 2. Deadline approaching ───────────────────────────────────────────────
    deadline_tenders = await tenders_col().find(
        {
            "deadline": {"$lte": deadline_cutoff, "$gte": now},
            "status": "active",
            "relevance_score": {"$gte": 60},
        },
        {"tender_id": 1, "title": 1, "agency": 1, "country": 1,
         "estimated_value": 1, "relevance_score": 1, "days_until_deadline": 1,
         "raw_url": 1, "deadline": 1, "_id": 0}
    ).limit(5).to_list(length=5)

    for tender in deadline_tenders:
        existing = await alerts_col().find_one({
            "tender_id": tender["tender_id"],
            "alert_type": "deadline_48h",
        })
        if existing:
            continue
        await send_deadline_alert(tender)
        sent += 1

    logger.info(f"Alert sweep complete — {sent} alerts sent.")
    return {"sent": sent}


async def send_new_tender_alert(tender: dict) -> None:
    """Send Slack alert for a new high-score tender."""
    message = (
        f"🎯 *New High-Match Tender Found!*\n"
        f"📋 *{tender.get('title', 'Unknown')}*\n"
        f"🏢 {tender.get('agency', '?')}  |  🌍 {tender.get('country', '?')}\n"
        f"💰 ${tender.get('estimated_value') or '?':,}  |  🎯 Score: {tender.get('relevance_score', '?')}/100\n"
        f"⏰ {tender.get('days_until_deadline', '?')} days remaining\n"
        f"🔗 <{tender.get('raw_url', '#')}|View on Portal>  |  "
        f"<{settings.backend_url}/tenders/{tender.get('tender_id')}|Open in TenderBot>"
    )
    await _send_slack(message)
    await _log_alert(tender["tender_id"], "new_match", "slack", message[:100])


async def send_deadline_alert(tender: dict) -> None:
    """Send Slack alert for a tender approaching its deadline."""
    hours_left = int((tender.get("days_until_deadline") or 2) * 24)
    message = (
        f"⚠️ *Deadline Alert — {hours_left}h remaining!*\n"
        f"📋 *{tender.get('title', 'Unknown')}*\n"
        f"🏢 {tender.get('agency', '?')}  |  🌍 {tender.get('country', '?')}\n"
        f"💰 ${tender.get('estimated_value') or '?':,}  |  🎯 Score: {tender.get('relevance_score', '?')}/100\n"
        f"🔗 <{tender.get('raw_url', '#')}|Act Now on Portal>"
    )
    await _send_slack(message)
    await _log_alert(tender["tender_id"], "deadline_48h", "slack", message[:100])


async def send_amendment_alert(tender_id: str, amendment: dict) -> None:
    """Send Slack alert when an amendment is detected."""
    message = (
        f"🔔 *Tender Amendment Detected*\n"
        f"📝 Change: {amendment.get('changes_summary', 'No summary')}\n"
        f"🔗 <{settings.backend_url}/tenders/{tender_id}|View in TenderBot>"
    )
    await _send_slack(message)
    await _log_alert(tender_id, "amendment", "slack", message[:100])


async def _send_slack(message: str) -> None:
    """Execute Composio SLACK_SEND_MESSAGE action."""
    try:
        toolset, Action = _get_composio_toolset()
        toolset.execute_action(
            action=Action.SLACK_SENDS_A_MESSAGE,
            params={
                "channel": settings.slack_channel,
                "text": message,
            },
        )
        logger.info(f"Slack alert sent to {settings.slack_channel}")
    except Exception as e:
        logger.error(f"Slack send failed: {e}")
        raise


async def _log_alert(tender_id: str, alert_type: str, channel: str, preview: str) -> None:
    """Record alert in the alerts collection for dedup and UI display."""
    await alerts_col().insert_one({
        "tender_id": tender_id,
        "user_id": "default",
        "alert_type": alert_type,
        "sent_at": datetime.utcnow(),
        "channel": channel,
        "delivered": True,
        "message_preview": preview,
    })
