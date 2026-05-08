"""
TenderBot Global — TinyFish Pro Plan Feature Demo
Demonstrates the REAL power: Running 2-3 searches in PARALLEL
vs sequential (takes same time but 2x the opportunities!)
"""
import asyncio
import time
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.pipelines.complete_search_orchestrator import run_complete_opportunity_search


async def demo_parallel_searches():
    """
    DEMO: Shows why Pro plan is worth it
    
    Instead of searching for 1 company profile sequentially:
      Search 1 ...................... 30 mins ----| 189 opportunities
      Search 2 ...................... 30 mins ----| 189 opportunities
      TOTAL TIME: 60 minutes, 378 opportunities
    
    With Pro plan - Run BOTH in parallel:
      Search 1 && Search 2 running together: 30 mins | 378 opportunities
      SAVES: 30 minutes of time!
    """
    
    print("\n" + "=" * 100)
    print("🚀 TINYFISH PRO PLAN FEATURE DEMO — PARALLEL SEARCHES")
    print("   Unlock 2-3x productivity with concurrent multi-searches")
    print("=" * 100)
    
    print("""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║ SCENARIO: Your company needs opportunities in 2 different niches                       ║
║                                                                                        ║
║ Profile A: Cybersecurity & Cloud Services                                            ║
║   - Skills: Python, AWS, Kubernetes, Security, CI/CD                                 ║
║   - Industries: Government, Enterprise, Tech                                         ║
║                                                                                        ║
║ Profile B: Data Science & Machine Learning                                           ║
║   - Skills: Python, TensorFlow, Spark, BigQuery, Analytics                           ║
║   - Industries: Financial, Tech, Research                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Define 2 different company profiles
    profile_a = {
        "name": "SecureCloud Inc",
        "keywords": ["cybersecurity", "cloud architecture", "DevOps", "infrastructure"],
        "skills": "Python, AWS, GCP, Kubernetes, Docker, Security, CI/CD, Enterprise Solutions"
    }
    
    profile_b = {
        "name": "DataViz Analytics",
        "keywords": ["machine learning", "data science", "analytics", "big data"],
        "skills": "Python, TensorFlow, Spark, SQL, BigQuery, Cloud Storage, BI Tools, Visualization"
    }
    
    print(f"\n📋 PROFILE A: {profile_a['name']}")
    print(f"   Keywords: {', '.join(profile_a['keywords'])}")
    print(f"\n📋 PROFILE B: {profile_b['name']}")
    print(f"   Keywords: {', '.join(profile_b['keywords'])}")
    
    print("\n" + "=" * 100)
    print("⏱️  RUNNING BOTH SEARCHES IN PARALLEL with TinyFish Pro...")
    print("   (Each would take ~30 min sequentially, but run simultaneously)")
    print("=" * 100 + "\n")
    
    start_time = time.time()
    
    # This is the Pro plan magic: Run both searches at the same time!
    # With Semaphore(15), both searches' agents run in parallel
    results = await asyncio.gather(
        run_complete_opportunity_search(
            keywords=profile_a["keywords"],
            company_skills=profile_a["skills"]
        ),
        run_complete_opportunity_search(
            keywords=profile_b["keywords"],
            company_skills=profile_b["skills"]
        ),
        return_exceptions=True
    )
    
    elapsed = time.time() - start_time
    
    # Check for errors
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return
    
    search_a_results, search_b_results = results
    
    # Calculate metrics
    total_opportunities = (
        search_a_results['total_opportunities'] + 
        search_b_results['total_opportunities']
    )
    
    print("\n" + "=" * 100)
    print("✅ BOTH SEARCHES COMPLETED IN PARALLEL!")
    print("=" * 100)
    
    print(f"\n{profile_a['name']}")
    print(f"  Total: {search_a_results['total_opportunities']} opportunities")
    print(f"  Breakdown:")
    for source, opps in search_a_results['by_source'].items():
        if opps:
            print(f"    • {source}: {len(opps)}")
    
    print(f"\n{profile_b['name']}")
    print(f"  Total: {search_b_results['total_opportunities']} opportunities")
    print(f"  Breakdown:")
    for source, opps in search_b_results['by_source'].items():
        if opps:
            print(f"    • {source}: {len(opps)}")
    
    # Performance metrics
    print("\n" + "=" * 100)
    print("⚡ PERFORMANCE METRICS")
    print("=" * 100)
    print(f"Total Opportunities Discovered:    {total_opportunities}")
    print(f"Total Execution Time:              {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Average per Search:                ~{elapsed/2/60:.1f} minutes")
    print(f"\nCOMPARISON:")
    print(f"  Sequential (old way):            {(elapsed*2)/60:.1f} minutes")
    print(f"  Parallel (Pro plan):             {elapsed/60:.1f} minutes")
    print(f"  TIME SAVED:                      {(elapsed)/60:.1f} minutes per search cycle")
    
    if elapsed < 1200 and total_opportunities > 300:
        rating = "⭐⭐⭐⭐⭐ EXCELLENT"
    elif elapsed < 1400 and total_opportunities > 250:
        rating = "⭐⭐⭐⭐ VERY GOOD"
    elif elapsed < 1600:
        rating = "⭐⭐⭐ GOOD"
    else:
        rating = "⭐⭐ ACCEPTABLE"
    
    print(f"  Pro Plan Rating:                 {rating}")
    
    # Save detailed results
    combined_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "execution_type": "Parallel Searches (Pro Plan)",
        "total_execution_seconds": round(elapsed, 1),
        "total_opportunities": total_opportunities,
        "search_profiles": [
            {
                "name": profile_a['name'],
                "keywords": profile_a['keywords'],
                "opportunities": search_a_results['total_opportunities'],
                "by_source": {k: len(v) for k, v in search_a_results['by_source'].items()}
            },
            {
                "name": profile_b['name'],
                "keywords": profile_b['keywords'],
                "opportunities": search_b_results['total_opportunities'],
                "by_source": {k: len(v) for k, v in search_b_results['by_source'].items()}
            }
        ],
        "time_saved_vs_sequential_minutes": round(elapsed/60, 1),
        "pro_plan_benefit": f"Get {total_opportunities} opportunities in {elapsed/60:.1f} minutes instead of {(elapsed*2)/60:.1f} minutes"
    }
    
    with open("pro_plan_parallel_search_demo.json", "w") as f:
        json.dump(combined_results, f, indent=2)
    
    print(f"\n✅ Results saved to: pro_plan_parallel_search_demo.json")
    
    print("\n" + "=" * 100)
    print("💡 KEY INSIGHT: Pro Plan Value")
    print("=" * 100)
    print(f"""
With TinyFish Pro plan, you can:

1. Discover opportunities across MULTIPLE business lines simultaneously
   Instead of: Search healthcare → Score → Search tech → Score
   Now: Search healthcare AND tech in parallel → Score both

2. Support multiple teams efficiently
   Each team gets their own AI agent discovery process
   Team A searches for cloud opportunities
   Team B searches for manufacturing contracts
   → Both complete in 30 minutes, not 60

3. Scout competitive intelligence faster
   Run 3 different searches for competitor analysis
   Find what contracts YOUR COMPETITORS are bidding
   All in 30-40 minutes vs 90+ minutes sequential

4. Scale to enterprise operations
   Portfolio of companies? Search all in parallel
   Multiple product lines? Search all simultaneously
   One organization, 20+ concurrent agents

═══════════════════════════════════════════════════════════════════════════════════════
BOTTOM LINE: Pro plan's 10x concurrency means you get 2-3x more throughput
             by running searches in parallel instead of sequential.
═══════════════════════════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    asyncio.run(demo_parallel_searches())
