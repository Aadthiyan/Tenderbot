"""
TenderBot — Agents Router
Exposes agent run history and status for LiveAgentTerminal.
"""
from fastapi import APIRouter, Query
from backend.services.agent_run_logger import get_recent_runs, get_agent_status
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/runs")
async def list_agent_runs(limit: int = Query(50, ge=1, le=200)):
    """Return recent agent run events for LiveAgentTerminal display."""
    runs = await get_recent_runs(limit=limit)
    return {"runs": runs, "count": len(runs)}


@router.get("/status")
async def agent_status():
    """Return latest status of each named agent."""
    status = await get_agent_status()
    return {"agents": status}
