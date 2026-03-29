"""
TenderBot Global — Test Find a Tender (UK) TinyFish Agent
"""
import asyncio
import sys
import os
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.find_a_tender import run_find_a_tender_agent
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_agent():
    print("=" * 60)
    print("TESTING FIND-A-TENDER (UK) TINYFISH AGENT")
    print("=" * 60)
    
    settings = get_settings()
    if not settings.tinyfish_api_key:
        print("⚠️ TINYFISH_API_KEY is not set in .env!")
        print("Using local mock data fallback to demonstrate output schema parsing.")
        print("-" * 60)

    try:
        tenders = await run_find_a_tender_agent(["digital services", "cloud", "agile"])
        
        print("\n🎉 Agent Execution Complete!")
        print(f"Extracted {len(tenders)} valid structured UK tenders.\n")
        
        print(json.dumps(tenders[:2], indent=2))
        print(f"\n... and {len(tenders) - 2} more results.")
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
