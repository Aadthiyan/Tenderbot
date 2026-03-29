"""
TenderBot Global — Test Competitor Intelligence (Phase 5.1)
Simulates fetching past contract award data (mocking the TinyFish FPSD query) 
and using Fireworks LLM to determine win probability and incumbent adversaries.
"""
import asyncio
import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.competitor_intel import analyze_competitors
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_intel_pipeline():
    print("==============================================================")
    print("TESTING COMPETITOR INTELLIGENCE PIPELINE (TASK 5.1)")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.fireworks_api_key or not settings.tinyfish_api_key:
        print("⚠️ API Keys are missing in .env!")
        print("Using local mock payload to demonstrate tactical extraction schema.")
        print("-" * 60)

    # Mock Company Profile
    profile = {
        "company_name": "Agile Defend IT",
        "annual_turnover": "12,000,000",
        "target_countries": ["US"],
        "past_contracts": ["Navy Network Defenses 2023", "VA Cloud Migration 2022"]
    }

    # Target Tender
    tender = {
        "title": "DoD Enterprise Cyber Risk Assessment",
        "agency": "Department of Defense",
        "estimated_value": 35000000.0,
        "relevance_score": 88
    }

    print("Analyzing Target RFP:")
    print(json.dumps(tender, indent=2))
    print("\nFetching past award data and querying AI Analyst... (Simulating ~2s scraped latency)\n")

    result = await analyze_competitors(tender, profile)

    print("🎉 INTELLIGENCE PACKET RETURNED:")
    print(f"  🥇 Our Estimated Win Probability : {result.get('our_probability')}%")
    print(f"  🏢 SMB Market Win Rate           : {result.get('smb_win_rate')}%")
    print("\n  🔍 Top Competitors (Incumbents):")
    for comp in result.get('top_competitors', []):
        print(f"      - {comp}")
    
    print(f"\n  📝 Analyst Summary:\n     {result.get('intel_summary')}")

if __name__ == "__main__":
    asyncio.run(test_intel_pipeline())
