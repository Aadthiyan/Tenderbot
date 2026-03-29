"""
TenderBot Global — Test Amendment Tracker (Phase 5.2)
Simulates asking TinyFish to revisit a URL and compare the current state 
of the live page against a historical page_snapshot.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.amendment_tracker import check_for_amendments
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_amendment_tracker():
    print("==============================================================")
    print("TESTING AMENDMENT & CANCELLATION TRACKER (TASK 5.2)")
    print("Evaluating live page changes against historical snapshots.")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.tinyfish_api_key:
        print("⚠️ TINYFISH_API_KEY is not set in .env!")
        print("Forcing AI to detect a simulated deadline extension for demonstration.")
        print("-" * 60)

    # Mock Tender that an original Deep Scrape processed two weeks ago
    tender = {
        "tender_id": "SAM_0987654",
        "title": "Quantum Computing Research Infrastructure Integration",
        "raw_url": "https://sam.gov/search/0987654",
        "page_snapshot": "This is a solicitation for Quantum Computing Hardware. Submissions are due strictly by 01 Aug 2026. No extensions will be granted.",
        # Trigger mock extraction bypass
        "force_mock_amendment": True
    }

    print("Historical Tender State:")
    print(f"  Title    : {tender['title']}")
    print(f"  Snapshot : '{tender['page_snapshot']}'")
    
    print("\n[Action] Deploying TinyFish Agent to revisit page and compare diffs...\n")

    result = await check_for_amendments(tender)

    if result and result.get("has_changes"):
        print("🚨 AI IDENTIFIED AN AMENDMENT OR CANCELLATION:")
        print(f"  Type    : {result.get('change_type').upper().replace('_', ' ')}")
        print(f"  Summary : {result.get('changes_summary')}")
        print(f"  Time    : {result.get('detected_at')}")
    else:
        print("✅ No amendments detected. Tender remains unchanged.")

if __name__ == "__main__":
    asyncio.run(test_amendment_tracker())
