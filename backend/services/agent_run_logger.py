"""
TenderBot — Agent Run Logger
Persists named agent execution events to MongoDB for LiveAgentTerminal display.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.services.db import get_db

logger = logging.getLogger(__name__)


async def log_agent_run(
    agent_name: str,
    status: str,
    summary: str,
    duration_ms: int = 0,
    metadata: Optional[dict] = None,
) -> None:
    """
    Store a single agent run event to the agent_runs collection.
    status: 'running' | 'success' | 'warning' | 'error'
    """
    try:
        db = get_db()
        await db["agent_runs"].insert_one({
            "agent_name": agent_name,
            "status": status,
            "summary": summary,
            "duration_ms": duration_ms,
            "metadata": metadata or {},
            "run_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Failed to log agent run ({agent_name}): {e}")


async def get_recent_runs(limit: int = 50) -> list:
    """Fetch most recent agent run events for LiveAgentTerminal."""
    db = get_db()
    cursor = db["agent_runs"].find({}, {"_id": 0}).sort("run_at", -1).limit(limit)
    runs = await cursor.to_list(length=limit)
    for r in runs:
        if "run_at" in r:
            r["run_at"] = r["run_at"].isoformat()
    return runs


async def get_agent_status() -> dict:
    """Return current status of each named agent (last run result)."""
    db = get_db()
    agent_names = ["ScraperAgent", "ScorerAgent", "ResearcherAgent", "DrafterAgent", "DeadlineWatchdog", "AmendmentTracker"]
    status = {}
    for name in agent_names:
        last = await db["agent_runs"].find_one(
            {"agent_name": name},
            {"_id": 0, "status": 1, "summary": 1, "run_at": 1},
            sort=[("run_at", -1)]
        )
        if last:
            if "run_at" in last:
                last["run_at"] = last["run_at"].isoformat()
            status[name] = last
        else:
            status[name] = {"status": "idle", "summary": "Never run", "run_at": None}
    return status
