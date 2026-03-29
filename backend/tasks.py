"""
TenderBot Global — Celery Tasks
Executes heavy, long-running AI operations in background worker processes.
"""
import asyncio
from backend.celery_app import celery_app
import logging
from backend.pipelines.scorer import score_tender
from backend.pipelines.eligibility import check_eligibility
from backend.pipelines.competitor_intel import analyze_competitors
from backend.pipelines.rfp_researcher import research_tender
from backend.pipelines.auto_drafter import auto_queue_for_draft
from backend.agents.deep_scrape import deep_scrape_tender
from backend.services.db import upsert_tender, get_db
from backend.services.alerts import send_alert
from datetime import datetime
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def async_process_tender(tender: dict, user_profile: dict):
    """
    The actual async workload for processing a single tender.
    Scoring -> Deep Scrape -> Eligibility -> Drafter
    """
    company_name = user_profile.get("company_name", "unknown")
    
    # 1. Scorer
    try:
        tender = await score_tender(tender, user_profile)
    except Exception as e:
        logger.warning(f"Celery: Scoring failed: {e}")
        return
        
    score = tender.get("relevance_score", 0)
    if score < settings.scrape_score_threshold:
        await upsert_tender(tender)
        return  # Stop processing if low score
        
    # 2. Deep Scrape & Research
    logger.info(f"Celery: Deep scraping '{tender.get('title')}' (Score: {score})")
    try:
        enriched = await asyncio.wait_for(
            deep_scrape_tender(tender["raw_url"]),
            timeout=settings.agent_timeout_seconds
        )
        tender.update(enriched)
        tender["enriched"] = True
        
        # Parallel research operations
        eligibility, intel, research = await asyncio.gather(
            check_eligibility(tender, user_profile),
            analyze_competitors(tender, user_profile),
            research_tender(tender, user_profile),
            return_exceptions=True
        )
        if not isinstance(eligibility, Exception): tender.update(eligibility)
        if not isinstance(intel, Exception): tender.update(intel)
        if not isinstance(research, Exception): tender.update(research)
            
    except Exception as e:
        logger.warning(f"Celery: Deep scrape failed: {e}")

    # 3. Save to DB
    await upsert_tender(tender)
    
    # 4. Draft Queue + HITL Checks
    if score >= settings.alert_score_threshold:
        has_gap = any(c.get("status") == "fail" for c in tender.get("eligibility_checklist", []))
        if has_gap:
            await send_alert("clarification_needed", tender)
            db = get_db()
            await db["draft_queue"].update_one(
                {"tender_id": tender["tender_id"], "company_name": company_name},
                {"$set": {
                    "tender_title": tender.get("title", "Untitled"),
                    "tender_score": score,
                    "tender_agency": tender.get("agency"),
                    "tender_deadline": tender.get("deadline"),
                    "status": "blocked_waiting_human",
                    "queued_at": datetime.utcnow(),
                }},
                upsert=True
            )
            from backend.services.ws import publish_ws_event
            publish_ws_event("DRAFT_QUEUED", {"tender_id": tender["tender_id"]}, settings.celery_broker_url)
        else:
            await auto_queue_for_draft(tender, user_profile)
            from backend.services.ws import publish_ws_event
            publish_ws_event("DRAFT_QUEUED", {"tender_id": tender["tender_id"]}, settings.celery_broker_url)
            
        await send_alert("new_tender", tender)


@celery_app.task(name="process_tender_task", bind=True, max_retries=3)
def process_tender_task(self, tender: dict, user_profile: dict):
    """
    Synchronous Celery wrapper that runs the async pipeline.
    """
    logger.info(f"Picked up tender {tender.get('tender_id')} from Redis queue.")
    try:
        # Run the async code inside the sync Celery worker
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(async_process_tender(tender, user_profile))
    except Exception as exc:
        logger.error(f"Task failed, retrying: {exc}")
        raise self.retry(exc=exc, countdown=60)
