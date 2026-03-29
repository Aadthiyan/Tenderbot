"""
TenderBot Global — Test Deep RFP Enrichment (Phase 4.2)
Simulates selecting tenders with score >= 75 and passing them to the
TinyFish deep_scrape agent to extract full eligibility requirements and documents.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.deep_scrape import deep_scrape_tender
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_deep_scraper_batch():
    print("==============================================================")
    print("TESTING DEEP RFP ENRICHMENT AGENT (TASK 4.2)")
    print("Processing high-priority tenders (score >= 75)")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.tinyfish_api_key:
        print("⚠️ TINYFISH_API_KEY is not set in .env!")
        print("Using local mock extraction fallback to demonstrate data structure.")
        print("-" * 60)

    # Simulate 12 high-score tenders from the DB
    high_score_tenders = [
        {"tender_id": f"mock_tnd_{i}", "title": f"Strategic Government Cloud Migration #{i}", "relevance_score": 85 + i, "raw_url": f"https://mock-portal.gov/tender/{i}"}
        for i in range(1, 13)
    ]

    print(f"Found {len(high_score_tenders)} tenders with score >= 75. Commencing Deep Scrape...\n")

    # Run deep scrapes concurrently (simulating orchestrator batching)
    tasks = [deep_scrape_tender(t["raw_url"]) for t in high_score_tenders]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    enriched_tenders = []
    success_count = 0

    for i, res in enumerate(results):
        tender = high_score_tenders[i].copy()
        if isinstance(res, Exception):
            print(f"❌ Deep scrape failed for {tender['tender_id']}: {res}")
        else:
            tender.update(res)
            tender["enriched"] = True
            enriched_tenders.append(tender)
            success_count += 1
            print(f"✅ Enriched {tender['tender_id']} - Found {len(tender.get('eligibility_requirements', []))} eligibility rules.")

    print("\n--------------------------------------------------------------")
    print(f"🎉 BATCH DEEP SCRAPE COMPLETE!")
    success_rate = (success_count / len(high_score_tenders)) * 100
    print(f"Success Rate: {success_rate:.1f}% ({success_count}/{len(high_score_tenders)} scraped)")
    print("--------------------------------------------------------------")
    
    if enriched_tenders:
        print("\nSample Enriched Data Structure:")
        sample = enriched_tenders[0]
        # Hide the giant page_snapshot to keep console clean
        sample["page_snapshot"] = "<HTML CONTENT TRUNCATED FOR DISPLAY>"
        print(json.dumps(sample, indent=2))

if __name__ == "__main__":
    asyncio.run(test_deep_scraper_batch())
