"""
TenderBot Global — Test Eligibility Pre-Qualification (Phase 4.3)
Simulates analyzing a deeply scraped tender's explicit requirements
against the company profile using Llama 3.1 70B.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.eligibility import check_eligibility
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_eligibility():
    print("==============================================================")
    print("TESTING ELIGIBILITY PRE-QUALIFICATION (TASK 4.3)")
    print("Fireworks.ai Llama 3.1 70B generating PASS/FAIL/ACTION PLAN")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.fireworks_api_key:
        print("⚠️ FIREWORKS_API_KEY is not set in .env!")
        print("Using local mock scoring fallback to demonstrate output schema.")
        print("-" * 60)

    # Mock Company Profile
    profile = {
        "company_name": "TechVentures Infrastructure",
        "annual_turnover": "5,000,000",
        "headcount": "45",
        "years_in_business": "5",
        "target_countries": ["US", "CA"],
        "certifications": ["SOC 2 Type II"],
        "past_contracts": ["Local City Gov IT Support 2024", "State University Network Upgrade"]
    }

    # Mock Deep-Scraped Tender Requirements
    mock_tender = {
        "title": "Federal Data Center Migration Project",
        "eligibility_requirements": [
            "Company must have an annual turnover exceeding $10,000,000.",
            "Must possess an active ISO 27001 Certification.",
            "Must have been in business for at least 3 years.",
            "Vendor must be registered or headquartered in the United States."
        ]
    }

    print("Company Profile Summary:")
    print(f"  Turnover: ${profile['annual_turnover']}")
    print(f"  Years in Business: {profile['years_in_business']}")
    print(f"  Certifications: {', '.join(profile['certifications'])}")
    print("\nDeep Scrape Extracted Requirements:")
    for req in mock_tender['eligibility_requirements']:
        print(f"  - {req}")
    print("\n--------------------------------------------------------------")

    print("\nRunning AI Eligibility Analyzer...")
    eligibility_result = await check_eligibility(mock_tender, profile)
    
    print("\n🎉 ELIGIBILITY ANALYSIS COMPLETE:")
    print(json.dumps(eligibility_result, indent=2))
    
    print("\nChecklist Breakdown:")
    for item in eligibility_result.get("eligibility_checklist", []):
        status = item.get('status', '').upper()
        icon = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '❓'
        print(f"  {icon} [{status}] {item.get('requirement')}")
        if status == 'FAIL' and item.get('gap'):
            print(f"      Gap: {item.get('gap')}")

if __name__ == "__main__":
    asyncio.run(test_eligibility())
