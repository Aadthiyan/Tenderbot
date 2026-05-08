"""
Load sample tender data directly and test the scoring pipeline
(Skips TinyFish, tests the rest of the system)
"""
import json
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.pipelines.scorer import score_tender

async def test_with_sample_data():
    # Load sample SAM.gov tenders
    with open("backend/sample_output/sam_gov_10_tenders.json") as f:
        tenders = json.load(f)[:3]  # Test with first 3
    
    # Mock company profile
    profile = {
        "company_name": "TechCorp Solutions",
        "sectors": ["Cloud", "AI", "Cybersecurity"],
        "keywords": ["cloud infrastructure", "machine learning", "security"],
        "min_value": 500000,
        "max_value": 5000000,
        "annual_turnover": 50000000,
        "headcount": 250,
        "certifications": ["ISO 27001", "SOC 2", "AWS Partner"],
    }
    
    print("\n" + "=" * 70)
    print("TESTING SCORING PIPELINE WITH SAMPLE DATA")
    print("=" * 70 + "\n")
    
    for i, tender in enumerate(tenders, 1):
        tender_norm = {
            "tender_id": f"SAMPLE-{i}",
            "source_portal": "sam_gov",
            "title": tender.get("title"),
            "agency": tender.get("agency"),
            "country": "US",
            "deadline": tender.get("deadline"),
            "estimated_value": tender.get("award_value"),
            "description": tender.get("description"),
            "category_code": tender.get("naics_code"),
            "raw_url": tender.get("url"),
        }
        
        print(f"\n[TENDER {i}] {tender_norm['title'][:60]}...")
        
        try:
            scored = await score_tender(tender_norm, profile)
            print(f"   Score: {scored.get('relevance_score', 'N/A')}/100")
            print(f"   Action: {scored.get('action', 'unknown')}")
            print(f"   Reasons: {', '.join(scored.get('match_reasons', [])[:2])}")
        except Exception as e:
            print(f"   ERROR: Scoring failed: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test_with_sample_data())
