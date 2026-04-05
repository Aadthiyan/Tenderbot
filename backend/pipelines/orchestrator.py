"""
TenderBot Global — Pipeline Orchestrator (Multi-Agent)
Named agents: ScraperAgent → ScorerAgent → ResearcherAgent → DrafterAgent
Each step logs to agent_runs for LiveAgentTerminal visibility.
"""
import asyncio
import logging
from datetime import datetime
from backend.config import get_settings
from backend.services.db import upsert_tender, portal_logs_col
from backend.pipelines.normalizer import normalize_tender
from backend.services.agent_run_logger import log_agent_run
from backend.tasks import process_tender_task
import agentops

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_full_scrape(user_profile: dict, portals: list[str]) -> dict:
    """
    Multi-Agent Pipeline:
    [ScraperAgent]    → parallel portal scraping
    [ScorerAgent]     → Fireworks.ai relevance scoring + win-rate boost
    [ResearcherAgent] → RFP deep research + eligibility + competitor intel
    [DrafterAgent]    → auto-queue high-score tenders for draft approval
    """
    logger.info(f"Starting full scrape on {len(portals)} portals for '{user_profile.get('company_name')}'")
    start_time = datetime.utcnow()
    company_name = user_profile.get("company_name", "unknown")

    # ── [ScraperAgent] ────────────────────────────────────────────────────────
    await log_agent_run("ScraperAgent", "running", f"Launching {len(portals)} portal agents for {company_name}", 0)
    tasks = [_run_portal_with_logging(portal, user_profile) for portal in portals]
    portal_results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_tenders = []
    for result in portal_results:
        if isinstance(result, list):
            raw_tenders.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"Portal agent returned exception: {result}")

    await log_agent_run("ScraperAgent", "success",
        f"Collected {len(raw_tenders)} raw tenders from {len(portals)} portals", 0)
    logger.info(f"Total raw tenders collected: {len(raw_tenders)}")

    if not raw_tenders:
        logger.warning("No tenders collected from any portal.")
        return {"status": "no_data", "tenders_found": 0}

    # ── Normalise + deduplicate ───────────────────────────────────────────────
    normalized = []
    seen_ids = set()
    for raw in raw_tenders:
        try:
            tender_doc = normalize_tender(raw)
            if tender_doc["tender_id"] not in seen_ids:
                seen_ids.add(tender_doc["tender_id"])
                normalized.append(tender_doc)
        except Exception as e:
            logger.warning(f"Normalization failed for tender: {e}")

    logger.info(f"Normalized + deduplicated: {len(normalized)} tenders")

    logger.info(f"Normalized + deduplicated: {len(normalized)} tenders")

    # ── [Celery Dispatch] ─────────────────────────────────────────────────────
    await log_agent_run("Orchestrator", "running", f"Dispatching {len(normalized)} tenders to Celery workers via Redis", 0)
    
    dispatched = 0
    for tender in normalized:
        try:
            # Send to Redis message broker asynchronously
            process_tender_task.delay(tender, user_profile)
            dispatched += 1
        except Exception as e:
            logger.error(f"Failed to dispatch tender to Celery: {e}")

    await log_agent_run("Orchestrator", "success", f"Successfully queued {dispatched} jobs in Redis.", 0)

    elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    summary = {
        "status": "queued",
        "tenders_collected": len(raw_tenders),
        "tenders_normalized": len(normalized),
        "tasks_dispatched": dispatched,
        "elapsed_ms": elapsed_ms,
        "portals_run": portals,
    }
    logger.info(f"Scrape + Dispatch complete: {summary}")
    return summary


async def _run_portal_with_logging(portal: str, user_profile: dict) -> list:
    """
    Wraps isolated portal agents with portal_logs collection tracking.
    Handles timeout and exceptions per portal without blocking others.
    """
    from backend.agents.sam_gov import run_sam_gov_agent
    from backend.agents.ted_eu import run_ted_eu_agent
    from backend.agents.ungm import run_ungm_agent
    from backend.agents.find_a_tender import run_find_a_tender_agent
    from backend.agents.austender import run_austender_agent
    from backend.agents.canadabuys import run_canadabuys_agent

    portal_map = {
        "sam_gov": run_sam_gov_agent,
        "ted_eu": run_ted_eu_agent,
        "ungm": run_ungm_agent,
        "find_a_tender": run_find_a_tender_agent,
        "austender": run_austender_agent,
        "canadabuys": run_canadabuys_agent
    }

    if portal not in portal_map:
        logger.warning(f"Unknown portal: {portal}")
        return []

    agent_func = portal_map[portal]
    start = datetime.utcnow()

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=[f"portal_{portal}"])
        except Exception:
            pass

    try:
        keywords = user_profile.get("keywords", [])
        results = await asyncio.wait_for(
            agent_func(keywords),
            timeout=settings.agent_timeout_seconds
        )
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        await portal_logs_col().insert_one({
            "portal": portal,
            "run_at": datetime.utcnow(),
            "status": "success",
            "tenders_found": len(results),
            "duration_ms": elapsed,
            "error": None,
        })
        logger.info(f"✅ {portal}: {len(results)} tenders ({elapsed}ms)")

        if session:
            agentops.end_session(end_state="Success")

        return results

    except asyncio.TimeoutError:
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        logger.warning(f"⏱️ {portal}: timed out after {settings.agent_timeout_seconds}s")
        await portal_logs_col().insert_one({
            "portal": portal, "run_at": datetime.utcnow(),
            "status": "timeout", "tenders_found": 0,
            "duration_ms": elapsed, "error": "timeout",
        })
        if session:
            agentops.end_session(end_state="Fail", end_state_reason="Timeout")
        return []

    except Exception as e:
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        logger.error(f"❌ {portal}: {e}")
        await portal_logs_col().insert_one({
            "portal": portal, "run_at": datetime.utcnow(),
            "status": "failed", "tenders_found": 0,
            "duration_ms": elapsed, "error": str(e),
        })
        if session:
            agentops.end_session(end_state="Fail", end_state_reason=str(e)[:200])
        return []
