"""
TenderBot Global — /alerts Router
Configure notification preferences and view alert history.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.models import AlertConfigRequest
from backend.services.db import users_col, alerts_col
import logging

router = APIRouter(prefix="/alerts", tags=["Alerts"])
logger = logging.getLogger(__name__)


@router.post("/config", status_code=200)
async def configure_alerts(req: AlertConfigRequest):
    """
    Save Slack webhook and/or email address for a user.
    Used by the Alerts Center settings panel.
    """
    update = {"updated_at": datetime.utcnow()}
    if req.slack_webhook:
        update["slack_webhook"] = req.slack_webhook
    if req.alert_email:
        update["alert_email"] = req.alert_email

    result = await users_col().update_one(
        {"_id": req.user_id},
        {"$set": update}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"User '{req.user_id}' not found.")

    return {"status": "ok", "message": "Alert configuration saved."}


@router.get("/history/{user_id}")
async def get_alert_history(user_id: str, limit: int = 50):
    """
    Returns recent alert records for a user — shown in the Alerts Center UI.
    """
    alerts = await alerts_col().find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(length=limit)

    return {"total": len(alerts), "alerts": alerts}


@router.post("/sweep")
async def trigger_alert_sweep(background_tasks):
    """
    Manually triggers the full alert sweep:
    - Fires deadline_warn alerts for tenders ≤ 7 days away
    - Re-scrapes monitored tenders for amendments
    """
    from backend.services.alert_sweep import run_alert_sweep
    from fastapi import BackgroundTasks
    background_tasks.add_task(run_alert_sweep)
    return {"status": "sweep_started", "message": "Alert sweep launched in background."}


@router.post("/test/{alert_type}")
async def fire_test_alert(alert_type: str):
    """
    Fires a single test alert — useful for verifying Composio + Slack is connected.
    Valid types: new_tender | deadline_warn | amendment
    """
    from backend.services.alerts import send_alert
    mock_tender = {
        "tender_id": "TEST-001",
        "title": "Test Tender — Alert Verification",
        "agency": "TenderBot System",
        "country": "US",
        "estimated_value": 1_000_000,
        "days_until_deadline": 5,
        "deadline": "2026-03-23",
        "relevance_score": 88,
        "match_reasons": ["System test alert", "Verifies Composio integration"],
        "raw_url": "https://tenderbot.example.com",
    }
    mock_amendment = {
        "change_type": "deadline_extension",
        "changes_summary": "Test amendment: deadline extended by 7 days.",
        "new_deadline": "2026-03-30",
        "is_cancelled": False,
    }
    if alert_type not in ("new_tender", "deadline_warn", "amendment"):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown alert_type '{alert_type}'. Use: new_tender | deadline_warn | amendment"
        )
    result = await send_alert(
        alert_type,  # type: ignore
        mock_tender,
        amendment=mock_amendment if alert_type == "amendment" else None
    )
    return result
