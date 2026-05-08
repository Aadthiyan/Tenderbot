#!/usr/bin/env python
"""
Quick troubleshoot: What's the actual issue with parallel agents?
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.config import get_settings
from backend.agents.sam_gov import run_sam_gov_agent

async def main():
    settings = get_settings()
    
    # Step 1: Check config
    print("=" * 80)
    print("STEP 1: Configuration Check")
    print("=" * 80)
    has_key = bool(settings.tinyfish_api_key)
    print(f"TinyFish API Key configured: {has_key}")
    if has_key:
        print(f"Key starts with: {settings.tinyfish_api_key[:30]}...")
    print(f"Agent timeout: {settings.agent_timeout_seconds} seconds")
    print()
    
    # Step 2: Call single agent
    print("=" * 80)
    print("STEP 2: Calling Single Agent (SAM.gov)")
    print("=" * 80)
    keywords = ["cybersecurity", "cloud", "software"]
    
    import time
    start = time.time()
    
    try:
        result = await run_sam_gov_agent(keywords)
        elapsed = time.time() - start
        
        print(f"✅ Agent returned successfully in {elapsed:.1f} seconds")
        print(f"Result type: {type(result).__name__}")
        print(f"Result length: {len(result) if isinstance(result, list) else 'N/A'}")
        
        if isinstance(result, list):
            if len(result) > 0:
                print(f"\n✅ Got {len(result)} tenders!")
                print("\nFirst tender:\n{json.dumps({k: (str(v)[:50] + '...' if len(str(v)) > 50 else v) for k, v in result[0].items()}, indent=2)}")
            else:
                print("\n⚠️ Result is empty list")
        else:
            print(f"\n⚠️ Result is not a list: {result}")
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Agent failed after {elapsed:.1f} seconds")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 TenderBot Debugging - Single Agent Test\n")
    asyncio.run(main())
