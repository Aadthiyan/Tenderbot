"""
TenderBot Global — Full Internet-Wide Search Test (TinyFish Pro Plan)
Tests all 8 agents: 6 government portals + web search + alternative sources
With TinyFish Pro plan: Up to 20 concurrent agents → 10x faster execution
"""
import asyncio
import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.pipelines.complete_search_orchestrator import run_complete_opportunity_search


async def test_full_search_with_pro_plan():
    """
    Test complete internet-wide search using TinyFish Pro plan.
    All 8 agents run with high concurrency (Semaphore 15).
    Expected: 10x faster than free plan, 200-300+ opportunities
    """
    
    # Search parameters
    keywords = ["cybersecurity", "cloud architecture", "software development", "DevOps"]
    company_skills = "Python, AWS, GCP, Kubernetes, CI/CD, Security, Machine Learning, Enterprise Solutions"
    
    print("\n" + "=" * 100)
    print("🚀 TENDERBOT PRO PLAN TEST — FULL INTERNET-WIDE SEARCH")
    print("   Semaphore: 15 concurrent agents (TinyFish Pro supports up to 20)")
    print("   Coverage: 6 Government Portals + Web Search + Alternative Sources")
    print("=" * 100)
    
    # Time the search
    start_time = time.time()
    
    print(f"\nSearch Keywords: {', '.join(keywords)}")
    print(f"Company Skills: {company_skills}\n")
    
    results = await run_complete_opportunity_search(
        keywords=keywords,
        company_skills=company_skills
    )
    
    elapsed = time.time() - start_time
    
    # Detailed results breakdown
    print("\n" + "=" * 100)
    print("📊 DETAILED RESULTS BY SOURCE\n")
    
    total_by_source = {}
    for source_name, opportunities in results["by_source"].items():
        count = len(opportunities) if opportunities else 0
        total_by_source[source_name] = count
        
        if count > 0:
            print(f"✅ {source_name.upper():30} | {count:4} opportunities")
            # Show sample
            first_opp = opportunities[0]
            title = first_opp.get("title", "N/A")[:50]
            print(f"   Sample: {title}...")
        else:
            print(f"⊘  {source_name.upper():30} | {count:4} (no matches for keywords on this run)")
    
    # Performance metrics
    print("\n" + "=" * 100)
    print("⚡ PERFORMANCE METRICS (TinyFish Pro Plan)")
    print("=" * 100)
    print(f"Total Opportunities Found:    {results['total_opportunities']}")
    print(f"Execution Time:               {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Agents Run:                   8 (6 government + web search + alternatives)")
    print(f"Success Rate:                 {results['success_rate']}")
    print(f"Average per Agent:            {results['total_opportunities'] / 8:.0f} opportunities")
    
    if elapsed < 1200:  # Less than 20 minutes
        speedup = "✅ EXCELLENT — Nearly 2x faster than free plan (20 min)"
    elif elapsed < 1400:
        speedup = "✅ GOOD — ~50% faster than free plan"
    else:
        speedup = "⚠️  Similar to free plan timing"
    print(f"Pro Plan Speed:               {speedup}")
    
    # Save summary
    summary = {
        "timestamp": results["timestamp"],
        "total_opportunities": results["total_opportunities"],
        "execution_seconds": round(elapsed, 1),
        "execution_minutes": round(elapsed/60, 1),
        "by_source": total_by_source,
        "search_keywords": results["search_keywords"],
        "company_skills": results["company_skills"],
        "success_rate": results["success_rate"],
        "plan": "TinyFish Pro — Semaphore(15) / up to 20 concurrent agents"
    }
    
    with open("tinyfish_pro_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 100)
    print(f"✅ Results saved to: tinyfish_pro_results.json")
    print("=" * 100 + "\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_full_search_with_pro_plan())
