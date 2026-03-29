"""
TenderBot Global — APScheduler Job Definitions
All background cron jobs run inside the FastAPI process on Railway.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from backend.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level scheduler instance (checked by /health)
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


def is_scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running


async def _daily_scrape_job():
    """
    Triggered every day at DAILY_SCRAPE_HOUR UTC.
    Fetches all user profiles and runs full multi-portal discovery for each.
    """
    from backend.services.db import users_col
    from backend.pipelines.orchestrator import run_full_scrape

    logger.info("⏰ Daily scrape job triggered.")
    users = await users_col().find({}, {"_id": 0}).to_list(length=100)

    if not users:
        logger.warning("No user profiles found — skipping daily scrape.")
        return

    for user in users:
        portals = user.get("portals_enabled", ["sam_gov", "ted_eu", "ungm"])
        portals_str = [p if isinstance(p, str) else p.value for p in portals]
        try:
            await run_full_scrape(user, portals_str)
            logger.info(f"✅ Daily scrape done for '{user.get('company_name')}'.")
        except Exception as e:
            logger.error(f"❌ Daily scrape failed for '{user.get('company_name')}': {e}")


async def _amendment_check_job():
    """
    Triggered every AMENDMENT_CHECK_INTERVAL_HOURS hours.
    Re-visits active watched tenders and detects changes.
    """
    from backend.services.db import tenders_col
    from backend.agents.amendment import check_amendments

    logger.info("⏰ Amendment check job triggered.")
    tenders = await tenders_col().find(
        {"status": "active", "enriched": True},
        {"tender_id": 1, "raw_url": 1, "page_snapshot": 1, "_id": 0}
    ).limit(50).to_list(length=50)

    for tender in tenders:
        try:
            await check_amendments(tender)
        except Exception as e:
            logger.error(f"Amendment check failed for tender {tender.get('tender_id')}: {e}")


async def _alert_sweep_job():
    """
    Triggered every day at ALERT_SWEEP_HOUR UTC.
    Sends Slack/email alerts for approaching deadlines and new high-score tenders.
    """
    from backend.services.alerts_service import sweep_and_dispatch_alerts

    logger.info("⏰ Alert sweep job triggered.")
    try:
        await sweep_and_dispatch_alerts()
    except Exception as e:
        logger.error(f"Alert sweep failed: {e}")


async def _voice_briefing_job():
    """
    Triggered every day at ALERT_SWEEP_HOUR UTC (runs after alert sweep).
    Generates the daily ElevenLabs voice briefing MP3.
    """
    from backend.services.voice_service import generate_daily_briefing

    logger.info("⏰ Voice briefing job triggered.")
    try:
        await generate_daily_briefing()
    except Exception as e:
        logger.error(f"Voice briefing generation failed: {e}")


async def _deadline_watchdog_job():
    """
    Triggered every day at DAILY_SCRAPE_HOUR + 1 UTC.
    Checks for approaching deadlines, auto-queues drafts, and sends urgent alerts.
    """
    from backend.services.deadline_watchdog import run_deadline_watch

    logger.info("⏰ Deadline watchdog job triggered.")
    try:
        await run_deadline_watch()
    except Exception as e:
        logger.error(f"Deadline watchdog failed: {e}")

def start_scheduler():
    """
    Registers all cron jobs and starts the scheduler.
    Called once during FastAPI lifespan startup.
    """
    scheduler = get_scheduler()
    scrape_hour = settings.daily_scrape_hour
    alert_hour = settings.alert_sweep_hour
    amend_hours = settings.amendment_check_interval_hours

    # Daily multi-portal scrape
    scheduler.add_job(
        _daily_scrape_job,
        trigger=CronTrigger(hour=scrape_hour, minute=0),
        id="daily_scrape",
        name="Daily Multi-Portal Discovery",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Amendment checks every N hours
    scheduler.add_job(
        _amendment_check_job,
        trigger=IntervalTrigger(hours=amend_hours),
        id="amendment_check",
        name="Amendment Tracker",
        replace_existing=True,
        misfire_grace_time=120,
    )

    # Daily alert sweep
    scheduler.add_job(
        _alert_sweep_job,
        trigger=CronTrigger(hour=alert_hour, minute=0),
        id="alert_sweep",
        name="Alert Sweep",
        replace_existing=True,
        misfire_grace_time=120,
    )

    # Daily voice briefing (runs 5 min after alert sweep)
    scheduler.add_job(
        _voice_briefing_job,
        trigger=CronTrigger(hour=alert_hour, minute=5),
        id="voice_briefing",
        name="Voice Briefing Generator",
        replace_existing=True,
        misfire_grace_time=120,
    )

    # Deadline Watchdog (Feature 6) - runs 1 hour after scrape
    scheduler.add_job(
        _deadline_watchdog_job,
        trigger=CronTrigger(hour=(scrape_hour + 1) % 24, minute=0),
        id="deadline_watchdog",
        name="Deadline Watchdog",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info(
        f"✅ APScheduler started — "
        f"daily scrape: {scrape_hour:02d}:00 UTC · "
        f"watchdog: {(scrape_hour + 1) % 24:02d}:00 UTC · "
        f"alerts+voice: {alert_hour:02d}:00 UTC"
    )
