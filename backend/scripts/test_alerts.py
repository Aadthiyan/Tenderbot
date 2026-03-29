"""
TenderBot Global — Test Composio Alerts (Phase 7.1)
Fires all 3 alert types sequentially and measures whether each one completes < 5s.
"""
import asyncio
import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.alerts import send_alert
from backend.config import get_settings

logging.basicConfig(level=logging.WARNING, format="%(message)s")

# ── Mock data fixtures ─────────────────────────────────────────────────────────
MOCK_TENDER_HIGH = {
    "tender_id": "DOD-2026-CLD-001",
    "title": "FedRAMP Cloud Migration & Zero Trust Security Audit",
    "agency": "Department of Defense",
    "country": "US",
    "estimated_value": 4_500_000,
    "days_until_deadline": 59,
    "deadline": "2026-05-15",
    "relevance_score": 94,
    "match_reasons": [
        "Zero Trust aligns with DoD mandate",
        "Cloud migration is core capability",
        "FedRAMP certification matches requirement"
    ],
    "raw_url": "https://sam.gov/opp/DOD-2026-CLD-001",
}

MOCK_TENDER_URGENT = {
    "tender_id": "MOJ-2026-AI-009",
    "title": "AI Legal Case Review Automation Tool",
    "agency": "Ministry of Justice",
    "country": "UK",
    "estimated_value": 1_800_000,
    "days_until_deadline": 3,
    "deadline": "2026-03-21",
    "relevance_score": 78,
    "raw_url": "https://find-a-tender.service.gov.uk/Notice/mock004",
}

MOCK_AMENDMENT = {
    "change_type": "deadline_extension",
    "changes_summary": "The submission deadline has been extended by 14 days following a formal clarification period. New deadline is May 15, 2026.",
    "new_deadline": "2026-05-15",
    "is_cancelled": False,
}

MOCK_CANCELLATION = {
    "change_type": "cancellation",
    "changes_summary": "This tender has been formally withdrawn by the contracting authority.",
    "new_deadline": None,
    "is_cancelled": True,
}

# ── Runner ─────────────────────────────────────────────────────────────────────
async def run_all_alerts():
    print("=" * 65)
    print("  TESTING COMPOSIO ALERT ENGINE (TASK 7.1)")
    print("  Firing 3 alert types — measuring delivery time")
    print("=" * 65)

    settings = get_settings()
    if not settings.composio_api_key:
        print("\n⚠️  COMPOSIO_API_KEY not set — running in console simulation mode.\n")

    # ── Alert 1: New High-Score Tender ──────────────────────────────────────
    print("\n[1/3] Firing: NEW_TENDER alert (score=94)...")
    t1 = time.monotonic()
    r1 = await send_alert("new_tender", MOCK_TENDER_HIGH)
    elapsed1 = time.monotonic() - t1
    status1 = "✅ PASS" if elapsed1 < 5 else "⛔ SLOW"
    print(f"  {status1} → {r1['status']} ({elapsed1:.2f}s)")

    # ── Alert 2: Deadline Warning ────────────────────────────────────────────
    print("\n[2/3] Firing: DEADLINE_WARN alert (3 days left)...")
    t2 = time.monotonic()
    r2 = await send_alert("deadline_warn", MOCK_TENDER_URGENT)
    elapsed2 = time.monotonic() - t2
    status2 = "✅ PASS" if elapsed2 < 5 else "⛔ SLOW"
    print(f"  {status2} → {r2['status']} ({elapsed2:.2f}s)")

    # ── Alert 3: Amendment Detected ──────────────────────────────────────────
    print("\n[3/3] Firing: AMENDMENT alert (deadline_extension)...")
    t3 = time.monotonic()
    r3 = await send_alert("amendment", MOCK_TENDER_HIGH, amendment=MOCK_AMENDMENT)
    elapsed3 = time.monotonic() - t3
    status3 = "✅ PASS" if elapsed3 < 5 else "⛔ SLOW"
    print(f"  {status3} → {r3['status']} ({elapsed3:.2f}s)")

    # ── Summary ──────────────────────────────────────────────────────────────
    all_pass = all(e < 5 for e in [elapsed1, elapsed2, elapsed3])
    print("\n" + "=" * 65)
    print(f"  RESULT: {'🎉 ALL 3 ALERTS DELIVERED < 5s' if all_pass else '⚠️  SOME ALERTS SLOW'}")
    print(f"  Times: {elapsed1:.2f}s | {elapsed2:.2f}s | {elapsed3:.2f}s")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_all_alerts())
