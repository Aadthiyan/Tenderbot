"""
Minimal test: Call SAM.gov agent once, print results
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.agents.sam_gov import run_sam_gov_agent

async def main():
    print("Testing SAM.gov agent...")
    keywords = ["cybersecurity", "cloud", "software"]
    try:
        result = await run_sam_gov_agent(keywords)
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        print(f"Result: {result}")
        if result:
            print(f"First item: {result[0]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
