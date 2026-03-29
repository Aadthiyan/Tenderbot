"""
TenderBot — Deadline Watchdog Service
Monitors active tender deadlines and auto-queues drafts / sends urgent alerts.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.config import get_settings
from backend.services.db import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_deadline_watch(company_name: Optional[str] = None) -> dict:
    """
    Scan all active tenders for deadline proximity.
    - ≤  7 days + score >= threshold + no draft → auto-queue and alert
    - ≤  1 day  + no approved draft → send urgent alert
    Returns summary dict.
    """
    from backend.pipelines.auto_drafter import auto_queue_for_draft
    from backend.services.agent_run_logger import log_agent_run

    start = datetime.now(timezone.utc)
    db = get_db()

    query: dict = {"status": "active", "days_until_deadline": {"$ne": None}}
    if company_name:
        pass  # tenders are global; company filtering is at draft level

    tenders = await db["tenders"].find(
        query,
        {"_id": 0, "tender_id": 1, "title": 1, "days_until_deadline": 1,
         "relevance_score": 1, "agency": 1, "deadline": 1}
    ).to_list(length=500)

    threshold = settings.scrape_score_threshold
    queued_count = 0
    urgent_count = 0
    alerts_sent = 0

    # Get all users to queue drafts per company
    users = await db["users"].find({}, {"_id": 0, "company_name": 1}).to_list(length=100)

    for tender in tenders:
        days = tender.get("days_until_deadline")
        score = tender.get("relevance_score") or 0
        tid = tender.get("tender_id")

        if days is None:
            continue

        # ── 7-day warning: auto-queue draft if high score ──────────────────────
        if days <= 7 and score >= threshold:
            for user in users:
                cn = user.get("company_name")
                existing = await db["draft_queue"].find_one({"tender_id": tid, "company_name": cn})
                if not existing:
                    user_profile = {"company_name": cn}
                    queued = await auto_queue_for_draft(tender, user_profile)
                    if queued:
                        queued_count += 1
                        logger.info(f"⏰ Watchdog queued draft: '{tender.get('title')}' ({days}d left)")

        # ── 24-hour urgent: alert if no approved draft ─────────────────────────
        if days <= 1 and score >= threshold:
            for user in users:
                cn = user.get("company_name")
                approved = await db["draft_queue"].find_one(
                    {"tender_id": tid, "company_name": cn, "status": "approved"}
                )
                if not approved:
                    urgent_count += 1
                    try:
                        from backend.services.alerts import send_alert
                        await send_alert("deadline_urgent", {**tender, "company_name": cn})
                        alerts_sent += 1
                    except Exception as e:
                        logger.warning(f"Urgent alert failed for {tid}: {e}")

    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    summary = {
        "tenders_scanned": len(tenders),
        "drafts_queued": queued_count,
        "urgent_alerts": urgent_count,
        "alerts_sent": alerts_sent,
        "elapsed_ms": elapsed_ms,
    }

    await log_agent_run(
        "DeadlineWatchdog",
        "success" if queued_count + alerts_sent > 0 else "idle",
        f"Scanned {len(tenders)} tenders. Queued {queued_count} drafts. {urgent_count} urgent alerts.",
        elapsed_ms,
        summary
    )

    logger.info(f"⏰ Deadline watchdog complete: {summary}")
    return summary
