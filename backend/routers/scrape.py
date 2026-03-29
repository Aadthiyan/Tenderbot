"""
TenderBot Global — /scrape Router
Triggers multi-portal discovery (fire-and-forget background task).
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.models import ScrapeRequest, ScrapeStatusResponse
from backend.services.db import users_col
from backend.config import get_settings
import logging

router = APIRouter(prefix="/scrape", tags=["Scrape"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("", response_model=ScrapeStatusResponse)
async def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Triggers a full multi-portal discovery run for a user profile.
    The scrape runs in the background — returns immediately with job status.
    The React dashboard polls /tenders to see results as they arrive.
    """
    # Fetch the user profile
    user = await users_col().find_one({"_id": req.user_id}) or \
           await users_col().find_one({"company_name": req.user_id})

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User/profile '{req.user_id}' not found. Create a profile first via POST /profile."
        )

    # Determine which portals to run
    portals_to_run = req.portals or user.get("portals_enabled", ["sam_gov", "ted_eu", "ungm"])
    portals_str = [p if isinstance(p, str) else p.value for p in portals_to_run]

    # Import here to avoid circular imports at module load
    from backend.pipelines.orchestrator import run_full_scrape

    # Fire-and-forget: run in background so API returns immediately
    background_tasks.add_task(run_full_scrape, user, portals_str)

    logger.info(f"Scrape triggered for '{user.get('company_name')}' on portals: {portals_str}")

    return ScrapeStatusResponse(
        status="triggered",
        message=f"Multi-portal discovery started for {len(portals_str)} portal(s). "
                f"Check /tenders in 60–120 seconds for results.",
        portals_triggered=portals_str,
    )
