"""
Test parallel searches with Semaphore(8) per search
Tests Option 2: Parallel execution of multiple industry searches
Expected: ~60 minutes total, 350-400 opportunities from 2 searches
"""
import asyncio
import hashlib
import json
from datetime import datetime
from backend.pipelines.complete_search_orchestrator import run_complete_opportunity_search

async def test_parallel_searches():
    """Run 2 searches in parallel, each with Semaphore(8)"""
    
    print("=" * 80)
    print("PARALLEL SEARCH TEST - Semaphore(8) per search")
    print("=" * 80)
    print(f"Start time: {datetime.now().isoformat()}")
    print()
    
    # Define two different industry searches
    search_configs = [
        {
            "name": "Cloud & Cybersecurity",
            "keywords": ["cloud", "cybersecurity", "AWS", "infrastructure", "security"],
            "company_skills": "Python, AWS, Kubernetes, Docker, Security, DevOps, TensorFlow"
        },
        {
            "name": "Data Science & AI",
            "keywords": ["data science", "machine learning", "AI", "analytics", "BigData"],
            "company_skills": "Python, R, TensorFlow, Spark, SQL, Analytics, Pandas, Scikit-learn"
        }
    ]
    
    # Run both searches in parallel
    print(f"Launching {len(search_configs)} parallel searches...\n")
    
    start_time = datetime.now()
    
    tasks = [
        run_complete_opportunity_search(
            keywords=config["keywords"],
            company_skills=config["company_skills"],
            search_name=config["name"],
            semaphore_limit=8  # Reduced from 15 for parallel safety
        )
        for config in search_configs
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Process results
    print("\n" + "=" * 80)
    print("PARALLEL SEARCH RESULTS")
    print("=" * 80)
    
    total_opportunities = 0
    search_results = []
    
    for i, (config, result) in enumerate(zip(search_configs, results)):
        print(f"\n📊 Search {i+1}: {config['name']}")
        print("-" * 80)
        
        if isinstance(result, Exception):
            print(f"❌ FAILED: {str(result)}")
            search_results.append({
                "search_name": config["name"],
                "status": "FAILED",
                "error": str(result),
                "opportunities": 0
            })
        else:
            opps = result.get("opportunities", [])
            count = len(opps)
            total_opportunities += count
            
            # Group by source
            by_source = {}
            for opp in opps:
                source = opp.get("source", "Unknown")
                by_source[source] = by_source.get(source, 0) + 1
            
            print(f"✅ SUCCESS: {count} opportunities")
            print(f"   Sources: {json.dumps(by_source, indent=6)}")
            
            search_results.append({
                "search_name": config["name"],
                "status": "SUCCESS",
                "opportunities": count,
                "by_source": by_source,
                "results": opps
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("PARALLEL EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total execution time: {execution_time:.2f} seconds ({execution_time/60:.1f} minutes)")
    print(f"Total opportunities found: {total_opportunities}")
    print(f"Searches completed: {sum(1 for r in search_results if r['status'] == 'SUCCESS')}/{len(search_configs)}")
    print(f"Success rate: {sum(1 for r in search_results if r['status'] == 'SUCCESS') / len(search_configs) * 100:.0f}%")
    
    # Save results
    output = {
        "test_type": "PARALLEL_SEARCHES_SEM8",
        "timestamp": datetime.now().isoformat(),
        "execution_time_seconds": execution_time,
        "execution_time_minutes": execution_time / 60,
        "total_opportunities": total_opportunities,
        "searches": search_results
    }
    
    filename = f"parallel_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to: {filename}")
    
    # Performance verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    if sum(1 for r in search_results if r['status'] == 'SUCCESS') == len(search_configs):
        if execution_time < 3600:  # Less than 1 hour
            print("✅ PARALLEL EXECUTION SUCCESSFUL")
            print(f"✅ Both searches completed without errors")
            print(f"✅ Semaphore(8) is SAFE for parallel searches")
            print(f"\n🚀 READY FOR PRODUCTION: Deploy parallel search capability")
        else:
            print("⚠️ PARALLEL EXECUTION SUCCESSFUL BUT SLOW")
            print(f"⚠️ Both searches completed without errors")
            print(f"⚠️ Time: {execution_time/60:.1f} minutes (slightly over 1 hour)")
            print(f"⚠️ Recommend: Monitor performance, may need sequential mode for time-critical deployment")
    else:
        print("❌ PARALLEL EXECUTION FAILED")
        print(f"❌ {sum(1 for r in search_results if r['status'] == 'FAILED')} searches failed")
        print(f"❌ Semaphore(8) not sufficient for parallel searches")
        print(f"\n💡 RECOMMENDATION: Use sequential searches or Semaphore(4) per search")
    
    return output

if __name__ == "__main__":
    result = asyncio.run(test_parallel_searches())
