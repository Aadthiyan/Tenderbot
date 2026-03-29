"""
TenderBot Global — Alert Sweep Service (Phase 7.1)
Runs on a schedule (ALERT_SWEEP_HOUR) to:
  1. Check all active tenders for imminent deadlines (< 7 days)
  2. Re-scrape watched tenders for amendments via TinyFish
  3. Fire the appropriate Slack alert for each finding
"""
import asyncio
import logging
from datetime import datetime
from backend.config import get_settings
from backend.services.alerts import send_alert
from backend.services.db import tenders_col
from backend.pipelines.amendment_tracker import check_for_amendments

logger = logging.getLogger(__name__)
settings = get_settings()

DEADLINE_WARN_DAYS = 7   # fire alert when deadline is this many days away or fewer
MAX_AMENDMENT_CHECKS = 20  # how many tenders to re-check per sweep run


async def run_alert_sweep() -> dict:
    """
    Full alert sweep: deadline warnings + amendment detection.
    Called by APScheduler daily or on-demand via /alerts/sweep API.
    """
    logger.info("🔔 Starting alert sweep...")
    start = datetime.utcnow()

    deadline_alerts_fired = 0
    amendment_alerts_fired = 0

    # ── 1. Deadline warnings ──────────────────────────────────────────────────
    col = tenders_col()
    cursor = col.find(
        {"status": "active", "days_until_deadline": {"$lte": DEADLINE_WARN_DAYS, "$gte": 0}},
        {"_id": 0, "page_snapshot": 0}
    ).limit(50)

    urgent_tenders = await cursor.to_list(length=50)
    if urgent_tenders:
        deadline_tasks = [send_alert("deadline_warn", t) for t in urgent_tenders]
        results = await asyncio.gather(*deadline_tasks, return_exceptions=True)
        deadline_alerts_fired = sum(1 for r in results if isinstance(r, dict) and r.get("status") in ("sent", "mock_sent"))
        logger.info(f"⏰ Deadline alerts fired: {deadline_alerts_fired}")
    else:
        logger.info("⏰ No tenders approaching deadline today.")

    # ── 2. Amendment detection ─────────────────────────────────────────────────
    # Only check tenders with a stored page_snapshot (meaning they've been deep-scraped)
    amend_cursor = col.find(
        {"status": "active", "page_snapshot": {"$exists": True, "$ne": ""}},
        {"_id": 0}  # include page_snapshot for comparison
    ).sort("last_amendment_check", 1).limit(MAX_AMENDMENT_CHECKS)

    tenders_to_check = await amend_cursor.to_list(length=MAX_AMENDMENT_CHECKS)
    logger.info(f"🔍 Checking {len(tenders_to_check)} tenders for amendments...")

    amendment_tasks = [check_for_amendments(t) for t in tenders_to_check]
    amendment_results = await asyncio.gather(*amendment_tasks, return_exceptions=True)

    for tender, result in zip(tenders_to_check, amendment_results):
        if isinstance(result, Exception) or result is None:
            continue

        if result.get("has_changes"):
            # Fire amendment alert
            await send_alert("amendment", tender, amendment=result)
            amendment_alerts_fired += 1

            # Persist the amendment to MongoDB
            try:
                await col.update_one(
                    {"tender_id": tender["tender_id"]},
                    {
                        "$push": {"amendment_history": result},
                        "$set": {
                            "page_snapshot": result.get("page_snapshot", tender.get("page_snapshot", "")),
                            "last_amendment_check": datetime.utcnow(),
                        }
                    }
                )
                if result.get("is_cancelled"):
                    await col.update_one(
                        {"tender_id": tender["tender_id"]},
                        {"$set": {"status": "cancelled"}}
                    )
            except Exception as e:
                logger.warning(f"Failed to persist amendment for {tender.get('tender_id')}: {e}")
        else:
            # Update last check timestamp even when no changes
            try:
                await col.update_one(
                    {"tender_id": tender["tender_id"]},
                    {"$set": {"last_amendment_check": datetime.utcnow()}}
                )
            except Exception:
                pass

    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    summary = {
        "status": "complete",
        "deadline_alerts": deadline_alerts_fired,
        "amendment_alerts": amendment_alerts_fired,
        "tenders_amendment_checked": len(tenders_to_check),
        "elapsed_ms": elapsed_ms,
    }
    logger.info(f"✅ Alert sweep done: {summary}")
    return summary
