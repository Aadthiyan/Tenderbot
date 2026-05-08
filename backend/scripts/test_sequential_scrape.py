"""
Test: Run ONE agent at a time (sequential, not parallel)
to see if they each work individually
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.sam_gov import run_sam_gov_agent
from backend.agents.ted_eu import run_ted_eu_agent
from backend.agents.ungm import run_ungm_agent
from backend.agents.find_a_tender import run_find_a_tender_agent
from backend.agents.austender import run_austender_agent
from backend.agents.canadabuys import run_canadabuys_agent

async def test_sequential_scrape():
    print("=" * 80)
    print("TESTING AGENTS SEQUENTIALLY (One at a time)")
    print("=" * 80 + "\n")
    
    keywords = ["cybersecurity", "cloud", "software"]
    
    agents = [
        ("SAM.gov", run_sam_gov_agent),
        ("TED EU", run_ted_eu_agent),
        ("UNGM", run_ungm_agent),
        ("Find a Tender", run_find_a_tender_agent),
        ("AusTender", run_austender_agent),
        ("CanadaBuys", run_canadabuys_agent),
    ]
    
    all_tenders = []
    
    for name, agent_func in agents:
        print(f"\n{'='*80}")
        print(f"Running {name}...")
        print(f"{'='*80}")
        
        start = time.time()
        try:
            result = await agent_func(keywords)
            elapsed = time.time() - start
            
            print(f"✅ {name} completed in {elapsed:.1f}s")
            print(f"   Returned: {len(result)} tenders (type: {type(result).__name__})")
            
            if isinstance(result, list):
                if len(result) > 0:
                    print(f"   First tender keys: {list(result[0].keys())}")
                    all_tenders.extend(result)
                else:
                    print(f"   WARNING: Empty list returned!")
            else:
                print(f"   ERROR: Not a list! Got {type(result).__name__}")
                
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ {name} failed after {elapsed:.1f}s: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"SEQUENTIAL TEST COMPLETE")
    print(f"Total tenders: {len(all_tenders)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_sequential_scrape())
