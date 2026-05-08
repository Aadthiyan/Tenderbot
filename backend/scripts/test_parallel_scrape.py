"""
TenderBot Global — Test Parallel Multi-Agent Scraper
Proves that we can launch 6 TinyFish agents, reducing total scrape time.
Uses concurrent limits to avoid rate limiting or connection issues.
"""
import asyncio
import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.sam_gov import run_sam_gov_agent
from backend.agents.ted_eu import run_ted_eu_agent
from backend.agents.ungm import run_ungm_agent
from backend.agents.find_a_tender import run_find_a_tender_agent
from backend.agents.austender import run_austender_agent
from backend.agents.canadabuys import run_canadabuys_agent

# Semaphore to limit concurrent TinyFish requests (avoid overwhelming the API)
# TinyFish Pro Plan: Up to 20 concurrent agents enabled! Using 15 for this test.
tinyfish_semaphore = asyncio.Semaphore(15)

async def run_agent_with_limit(agent_name, agent_func, keywords):
    """Wrap agent call with semaphore limit"""
    async with tinyfish_semaphore:
        print(f"  ▸ {agent_name} starting...")
        try:
            result = await agent_func(keywords)
            return result
        except Exception as e:
            print(f"  ✗ {agent_name} error: {e}")
            raise

async def test_parallel_scrape():
    print("==============================================================")
    print("LAUNCHING ALL 6 TINYFISH PORTAL AGENTS IN PARALLEL")
    print("==============================================================\n")
    
    keywords = ["cybersecurity", "cloud", "software"]
    start_time = time.time()

    # asyncio.gather with semaphore limits concurrent requests
    print("Starting all 6 agents...\n")
    results = await asyncio.gather(
        run_agent_with_limit("SAM.gov", run_sam_gov_agent, keywords),
        run_agent_with_limit("TED EU", run_ted_eu_agent, keywords),
        run_agent_with_limit("UNGM", run_ungm_agent, keywords),
        run_agent_with_limit("Find a Tender", run_find_a_tender_agent, keywords),
        run_agent_with_limit("AusTender", run_austender_agent, keywords),
        run_agent_with_limit("CanadaBuys", run_canadabuys_agent, keywords),
        return_exceptions=True
    )
    
    end_time = time.time()
    
    all_tenders = []
    failed_agents = 0
    
    for i, res in enumerate(results):
        name = ["SAM.gov", "TED EU", "UNGM", "Find a Tender", "AusTender", "CanadaBuys"][i]
        if isinstance(res, Exception):
            print(f"❌ {name} failed with exception: {type(res).__name__}: {str(res)[:100]}")
            import traceback
            traceback.print_exception(type(res), res, res.__traceback__)
            failed_agents += 1
        else:
            print(f"✅ {name} returned {len(res)} tenders (type: {type(res).__name__})")
            if len(res) == 0:
                print(f"   → WARNING: Got empty list!")
            all_tenders.extend(res)
            
    print("\n--------------------------------------------------------------")
    print(f"🎉 PARALLEL SCRAPE COMPLETE in {end_time - start_time:.2f} seconds!")
    print(f"Total Tenders Extracted: {len(all_tenders)}")
    print(f"Success Rate: {6 - failed_agents}/6 portals")
    print("--------------------------------------------------------------\n")
    
    if all_tenders:
        print("Sample Data Structure (first record from each portal that succeeded):")
        samples = {}
        for t in all_tenders:
            p = t.get("_source_portal")
            if p not in samples:
                samples[p] = t
        
        print(json.dumps(list(samples.values()), indent=2))

if __name__ == "__main__":
    asyncio.run(test_parallel_scrape())
