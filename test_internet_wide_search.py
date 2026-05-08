"""
TenderBot Global — Test Complete Internet-Wide Search
Launches the full orchestrator to search:
- 6 Government procurement portals
- Entire internet (Google search)
- Alternative/private procurement platforms
"""
import asyncio
import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipelines.complete_search_orchestrator import run_complete_opportunity_search


async def test_complete_search():
    """
    Test the complete opportunity search with expanded internet-wide coverage.
    Searches across government portals + web + private platforms.
    """
    
    # Example with custom keywords and company skills
    keywords = ["cybersecurity", "cloud", "software", "IT services", "consulting"]
    company_skills = "Python, AWS, cloud architecture, cybersecurity, DevOps, machine learning, enterprise solutions"
    
    # Run complete search
    results = await run_complete_opportunity_search(
        keywords=keywords,
        company_skills=company_skills
    )
    
    # Display detailed results
    print("\n📊 DETAILED BREAKDOWN BY SOURCE:\n")
    
    for source_name, opportunities in results["by_source"].items():
        if opportunities:
            print(f"\n{'─' * 80}")
            print(f"{source_name.upper()} — {len(opportunities)} opportunities")
            print(f"{'─' * 80}")
            
            for i, opp in enumerate(opportunities[:2], 1):  # Show first 2 from each source
                title = opp.get("title", "N/A")[:60]
                org = opp.get("organization") or opp.get("agency") or opp.get("contracting_authority") or "N/A"
                deadline = opp.get("deadline", "N/A")
                url = opp.get("url", "N/A")
                
                print(f"\n  [{i}] {title}...")
                print(f"      Organization: {org}")
                print(f"      Deadline: {deadline}")
                print(f"      URL: {url[:70]}")
    
    # Save full results to file
    with open("opportunity_search_results.json", "w") as f:
        # Convert to serializable format
        output = {
            "summary": {
                "total": results["total_opportunities"],
                "time_seconds": round(results["execution_time"], 1),
                "timestamp": results["timestamp"],
                "success_rate": results["success_rate"],
            },
            "by_source": {
                k: len(v) for k, v in results["by_source"].items()
            },
            "search_params": {
                "keywords": results["search_keywords"],
                "company_skills": results["company_skills"]
            }
        }
        json.dump(output, f, indent=2)
        print(f"\n✅ Full results saved to opportunity_search_results.json")


if __name__ == "__main__":
    print("\n" + "=" * 90)
    print("🌍 TENDERBOT GLOBAL — INTERNET-WIDE OPPORTUNITY SEARCH")
    print("    Government Portals × Internet Search × Alternative Platforms")
    print("=" * 90)
    
    asyncio.run(test_complete_search())
