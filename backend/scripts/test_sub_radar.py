"""
TenderBot Global — Test Subcontractor Radar (Phase 5.3)
Scans direct hubs of Prime contractors (e.g. Lockheed/Boeing) seeking
subcontracting SME help matching our profile.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.subcontractor_radar import scan_for_sub_opportunities
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_subcontractor_radar():
    print("==============================================================")
    print("TESTING SUBCONTRACTOR RADAR (TASK 5.3)")
    print("Scanning Prime Contractor Hubs for SME Teaming Opportunities.")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.tinyfish_api_key:
        print("⚠️ TINYFISH_API_KEY is not set in .env!")
        print("Using local mock payloads to demonstrate extraction structure.")
        print("-" * 60)

    # Mock Company Profile focusing on DevOps/Cyber
    profile = {
        "company_name": "CloudSecure Infrastructure",
        "keywords": ["zero trust architecture", "devops", "aws govcloud"]
    }

    print("Profile Keyword Target:")
    print(f"  '{profile['keywords'][0]}'")
    print(f"\n[Action] Deploying TinyFish Agents to scan top Prime Contractor Supplier HUBS...\n")

    results = await scan_for_sub_opportunities(profile)

    if results:
        print(f"🎉 SUCCESS! Found {len(results)} active Subcontracting Opportunities:\n")
        print(json.dumps(results, indent=2))
    else:
        print("❌ No Subcontractor Opportunities located.")

if __name__ == "__main__":
    asyncio.run(test_subcontractor_radar())
