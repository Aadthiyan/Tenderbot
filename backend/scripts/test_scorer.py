"""
TenderBot Global — Test Fireworks.ai Relevance Scorer (Phase 3.1)
Simulates parsing a single mock tender through the Llama 3.1 70B model
to demonstrate intelligent extraction of match reasons and scores.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.scorer import score_tender
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_scorer():
    print("==============================================================")
    print("TESTING FIREWORKS.AI RELEVANCE SCORING (TASK 4.1)")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.fireworks_api_key:
        print("⚠️ FIREWORKS_API_KEY is not set in .env!")
        print("Using local mock scoring fallback to demonstrate output schema.")
        print("-" * 60)

    # Mock Company Profile
    profile = {
        "company_name": "SecureData Cloud Systems",
        "sectors": ["Cybersecurity", "Cloud Hosting", "IT Consulting"],
        "keywords": ["zero trust", "AWS", "fedramp", "data migration"],
        "min_value": 100000,
        "max_value": 5000000,
        "target_countries": ["US", "UK"],
        "certifications": ["ISO 27001", "SOC 2"]
    }

    # Mock Tender (Highly Relevant)
    tender_strong = {
        "title": "FedRAMP Cloud Migration and Zero Trust Security Audit",
        "agency": "Department of Defense",
        "country": "US",
        "estimated_value": 2500000.0,
        "category_code": "541512",
        "description": "Seeking an certified IT vendor to migrate legacy systems to AWS GovCloud, implementing zero trust architecture and maintaining ISO 27001 compliance standards."
    }

    # Mock Tender (Weak/Out of Scope)
    tender_weak = {
        "title": "Construction of New Regional Hospital Wing",
        "agency": "National Health Service",
        "country": "UK",
        "estimated_value": 45000000.0,
        "category_code": "45000000",
        "description": "General contracting services for the construction of a 100-bed regional hospital wing. Requires heavy machinery operation and civil engineering expertise."
    }

    print("Company Profile:")
    print(json.dumps(profile, indent=2))
    print("\n--------------------------------------------------------------")

    print("\n[Test 1] Scoring Highly Relevant Tender...")
    result_strong = await score_tender(tender_strong.copy(), profile)
    print(json.dumps({
        "tender_title": result_strong["title"],
        "score": result_strong["relevance_score"],
        "action": result_strong["action"],
        "match_reasons": result_strong["match_reasons"],
        "disqualifiers": result_strong["disqualifiers"]
    }, indent=2))

    print("\n[Test 2] Scoring Out-of-Scope Tender...")
    result_weak = await score_tender(tender_weak.copy(), profile)
    print(json.dumps({
        "tender_title": result_weak["title"],
        "score": result_weak["relevance_score"],
        "action": result_weak["action"],
        "match_reasons": result_weak["match_reasons"],
        "disqualifiers": result_weak["disqualifiers"]
    }, indent=2))
    
    print("\n🎉 Scoring Pipeline Complete!")

if __name__ == "__main__":
    asyncio.run(test_scorer())
