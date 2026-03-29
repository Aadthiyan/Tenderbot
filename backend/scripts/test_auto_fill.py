"""
TenderBot Global — Test Auto Form-Fill Assistant (Phase 5.4)
Simulates instructing TinyFish to visit an application form and strategically map
Company Profile JSON fields into the HTML DOM without hitting the submit button.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.auto_fill import auto_fill_form
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_form_fill():
    print("==============================================================")
    print("TESTING AUTO FORM-FILL ASSISTANT (TASK 5.4)")
    print("Injecting Company profile data into remote SAM.gov form.")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.tinyfish_api_key:
        print("⚠️ TINYFISH_API_KEY is not set in .env!")
        print("Using local mock extraction to simulate form field interactions.")
        print("-" * 60)

    # Mock Company Profile containing actionable form inputs
    profile = {
        "company_name": "Agile Defend IT",
        "registration_id": "UK-12345678",
        "alert_email": "bidding@agiledefend.co.uk",
        "address": "123 Cyber Lane, London, UK",
        "years_in_business": 10,
        "certifications": ["ISO 27001", "Cyber Essentials"]
    }

    application_url = "https://sam.gov/mock/application-portal-123"

    print("Profile Fields to Inject:")
    print(json.dumps(profile, indent=2))
    print(f"\n[Action] Deploying TinyFish Agent to: {application_url}\n")

    result = await auto_fill_form(application_url, profile)

    print("🎉 FORM-FILL COMPLETION REPORT:")
    if result.get('status') == "success":
        print(f"  ✅ Completion Rate : {result.get('completion_pct')}%")
        print("\n  ✍️ Extracted and Filled Fields:")
        for idx, field in enumerate(result.get("fields_filled", []), 1):
            print(f"     {idx}. {field}")
            
        print("\n  ⚠️ Missing Data - User action required before submission:")
        for field in result.get("fields_remaining", []):
            print(f"     - [BLANK] {field}")
    else:
        print("❌ Form filling failed to initialize correctly.")

if __name__ == "__main__":
    asyncio.run(test_form_fill())
