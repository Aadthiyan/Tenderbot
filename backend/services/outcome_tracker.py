"""
TenderBot — Outcome Tracker Service
Records bid outcomes and computes win-rate adjustments for scorer.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.services.db import get_db

logger = logging.getLogger(__name__)


async def record_outcome(tender_id: str, outcome: str, company_name: str) -> bool:
    """
    Record the outcome of a submitted bid.
    outcome: 'won' | 'lost' | 'no_bid' | 'pending'
    """
    db = get_db()
    now = datetime.now(timezone.utc)

    # Update tender record
    await db["tenders"].update_one(
        {"tender_id": tender_id},
        {"$set": {"bid_outcome": outcome, "bid_outcome_at": now}}
    )

    # Log to outcomes collection for ML feedback
    tender = await db["tenders"].find_one({"tender_id": tender_id}, {"_id": 0, "agency": 1, "category_code": 1, "relevance_score": 1, "title": 1})
    if tender:
        await db["bid_outcomes"].update_one(
            {"tender_id": tender_id, "company_name": company_name},
            {"$set": {
                "tender_id": tender_id,
                "company_name": company_name,
                "outcome": outcome,
                "agency": tender.get("agency"),
                "category_code": tender.get("category_code"),
                "relevance_score": tender.get("relevance_score"),
                "title": tender.get("title"),
                "recorded_at": now,
            }},
            upsert=True
        )

    logger.info(f"📊 Outcome recorded: {tender_id} → {outcome} for {company_name}")
    return True


async def get_win_rate(agency: Optional[str], category_code: Optional[str], company_name: str) -> float:
    """
    Compute historical win rate for similar tenders (same agency or category).
    Returns a float between -1.0 and +1.0 as a score adjustment factor.
    0.0 = no data, +0.5 = strong history, -0.5 = poor history
    """
    db = get_db()
    query = {"company_name": company_name, "outcome": {"$in": ["won", "lost"]}}

    # Priority: agency-specific > category-specific > no data
    filters = []
    if agency:
        filters.append({**query, "agency": agency})
    if category_code:
        filters.append({**query, "category_code": category_code})

    for f in filters:
        outcomes = await db["bid_outcomes"].find(f, {"outcome": 1}).to_list(length=50)
        if len(outcomes) >= 2:  # need at least 2 data points
            wins = sum(1 for o in outcomes if o["outcome"] == "won")
            rate = wins / len(outcomes)             # 0.0 to 1.0
            return round((rate - 0.5) * 2.0, 2)    # normalize to -1.0 to +1.0

    return 0.0  # no history — no adjustment


async def get_outcome_stats(company_name: str) -> dict:
    """Return aggregate outcome stats for dashboard display."""
    db = get_db()
    outcomes = await db["bid_outcomes"].find(
        {"company_name": company_name},
        {"outcome": 1, "_id": 0}
    ).to_list(length=500)

    total = len(outcomes)
    if total == 0:
        return {"total": 0, "won": 0, "lost": 0, "no_bid": 0, "win_rate_pct": 0}

    won   = sum(1 for o in outcomes if o["outcome"] == "won")
    lost  = sum(1 for o in outcomes if o["outcome"] == "lost")
    no_bid = sum(1 for o in outcomes if o["outcome"] == "no_bid")
    decided = won + lost

    return {
        "total": total,
        "won": won,
        "lost": lost,
        "no_bid": no_bid,
        "win_rate_pct": round((won / decided * 100) if decided > 0 else 0, 1),
    }
