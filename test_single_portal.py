"""
Debug single portal scrape with verbose logging
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from backend.agents.sam_gov import run_sam_gov_agent

async def test_single_portal():
    print("\n" + "=" * 60)
    print("Testing SAM.gov agent with verbose logging")
    print("=" * 60 + "\n")
    
    keywords = ["software development", "IT services", "technology"]
    
    try:
        results = await run_sam_gov_agent(keywords)
        print(f"\n✅ Returned {len(results)} tenders")
        if results:
            print("\nFirst tender sample:")
            import json
            print(json.dumps(results[0], indent=2, default=str))
        else:
            print("\n❌ NO TENDERS FOUND - This could indicate:")
            print("   1. Portal has no active tenders for those keywords")
            print("   2. TinyFish request timed out (120s timeout)")
            print("   3. Portal structure changed")
            print("   4. API key issue")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_portal())
