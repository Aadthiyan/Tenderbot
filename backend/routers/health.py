"""
TenderBot Global — /health Router
Returns per-portal scrape status and system health summary.
"""
from fastapi import APIRouter, Response, status
from datetime import datetime, timedelta
from backend.services.db import portal_logs_col, test_connection
from backend.models import HealthResponse, HealthPortalStatus
from backend.config import get_settings
import logging

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)
settings = get_settings()

PORTALS = ["sam_gov", "ted_eu", "ungm", "find_a_tender", "austender", "canadabuys"]


@router.get("", response_model=HealthResponse)
async def get_health(response: Response):
    """
    Returns per-portal scrape success rates, API key status, and system health.
    Returns HTTP 503 if critical systems (DB) are down.
    """
    portal_statuses = []
    overall_healthy = True
    since = datetime.utcnow() - timedelta(hours=24)

    for portal in PORTALS:
        try:
            logs = await portal_logs_col().find(
                {"portal": portal, "run_at": {"$gte": since}}
            ).sort("run_at", -1).limit(20).to_list(length=20)

            if not logs:
                portal_statuses.append(HealthPortalStatus(
                    portal=portal,
                    status="unknown",
                    success_rate_pct=None,
                    last_run=None,
                    last_error=None,
                ))
                continue

            total = len(logs)
            successes = sum(1 for l in logs if l.get("status") == "success")
            rate = round((successes / total) * 100, 1)
            last_log = logs[0]
            last_error = last_log.get("error") if last_log.get("status") != "success" else None

            if rate >= 80:
                status = "healthy"
            elif rate >= 50:
                status = "degraded"
                overall_healthy = False
            else:
                status = "down"
                overall_healthy = False

            portal_statuses.append(HealthPortalStatus(
                portal=portal,
                status=status,
                success_rate_pct=rate,
                last_run=last_log.get("run_at"),
                last_error=last_error,
            ))

        except Exception as e:
            logger.error(f"Health check failed for portal {portal}: {e}")
            portal_statuses.append(HealthPortalStatus(
                portal=portal,
                status="down",
                last_error=str(e),
            ))
            overall_healthy = False

    # Check MongoDB connectivity
    db_ok = await test_connection()
    if not db_ok:
        overall_healthy = False

    # Check scheduler (import here to avoid circular)
    from backend.scheduler import is_scheduler_running
    scheduler_ok = is_scheduler_running()

    # Check API keys
    keys_status = {
        "mongodb": getattr(settings, "mongodb_uri", "") != "",
        "tinyfish": getattr(settings, "tinyfish_api_key", "") != "",
        "fireworks": getattr(settings, "fireworks_api_key", "") != "",
        "composio": getattr(settings, "composio_api_key", "") != "",
    }
    
    # If DB is completely down, fail the healthcheck hard
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        overall="healthy" if overall_healthy else "degraded",
        portals=portal_statuses,
        scheduler_running=scheduler_ok,
        api_keys=keys_status,
        checked_at=datetime.utcnow(),
    )


@router.get("/config")
async def get_config_status():
    """
    Returns which API keys are configured (boolean only, no secrets).
    Used by the React dashboard to show a 'missing key' warning banner.
    """
    missing = []
    if not settings.tinyfish_api_key:
        missing.append("TINYFISH_API_KEY")
    if not settings.fireworks_api_key:
        missing.append("FIREWORKS_API_KEY")
    if not settings.mongodb_uri or settings.mongodb_uri == "mongodb://localhost:27017":
        missing.append("MONGODB_URI")
    if not settings.composio_api_key:
        missing.append("COMPOSIO_API_KEY")
    if not settings.elevenlabs_api_key:
        missing.append("ELEVENLABS_API_KEY")

    return {
        "all_configured": len(missing) == 0,
        "missing_keys": missing,
        "live_submit_enabled": settings.enable_live_submit,
        "demo_mode": len(missing) > 0,
    }

