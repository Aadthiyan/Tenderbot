"""
TenderBot Global — Complete Opportunity Orchestrator (Phase 2.4)
Launches ALL procurement agents:
✅ 6 Government portals (SAM.gov, TED EU, UNGM, Find-a-Tender, AusTender, CanadaBuys)
✅ Internet-wide web search
✅ Alternative sources (LinkedIn, private bidding platforms, marketplaces)

Uses company profile to tailor keyword searches by actual capabilities.
"""
import asyncio
import json
import time
import logging
from typing import Optional
from datetime import datetime

from backend.agents.sam_gov import run_sam_gov_agent
from backend.agents.ted_eu import run_ted_eu_agent
from backend.agents.ungm import run_ungm_agent
from backend.agents.find_a_tender import run_find_a_tender_agent
from backend.agents.austender import run_austender_agent
from backend.agents.canadabuys import run_canadabuys_agent
from backend.agents.web_search import run_web_search_agent
from backend.agents.alternative_sources import run_alternative_sources_agent

logger = logging.getLogger(__name__)

# Semaphore to coordinate concurrent requests across all agents
# TinyFish Pro Plan: Up to 20 concurrent agents (10x faster)
# Using 15 to balance speed with stability
tinyfish_semaphore = asyncio.Semaphore(15)

async def run_agent_with_limit(agent_name: str, agent_func, *args, semaphore=None, **kwargs):
    """Wrap agent call with semaphore limit (uses module-level semaphore if not provided)"""
    sem = semaphore or tinyfish_semaphore
    async with sem:
        logger.info(f"  ▸ {agent_name} starting...")
        try:
            result = await agent_func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"  ✗ {agent_name} error: {e}")
            raise


async def run_complete_opportunity_search(
    user_id: str = None,
    keywords: Optional[list[str]] = None,
    company_skills: Optional[str] = None,
    semaphore_limit: int = 15,
    search_name: str = None,
) -> dict:
    """
    Launch a complete procurement opportunity search using ALL agents.
    
    Args:
        user_id: Optional user ID to fetch company profile
        keywords: Search keywords (if None, uses company profile)
        company_skills: Company capabilities (if None, fetches from profile)
        semaphore_limit: Concurrency limit (default 15 for single search, use 8 for parallel)
        search_name: Name of this search (for logging in parallel mode)
    
    Returns:
        {
            'total_opportunities': int,
            'opportunities': list of opportunity objects,
            'by_source': {
                'sam_gov': list,
                'ted_eu': list,
                'ungm': list,
                'find_a_tender': list,
                'austender': list,
                'canadabuys': list,
                'web_search': list,
                'alternative_sources': list
            },
            'execution_time': float,
            'timestamp': datetime
        }
    """
    
    print("\n" + "=" * 90)
    print("🚀  TENDERBOT GLOBAL — COMPLETE OPPORTUNITY SEARCH")
    if search_name:
        print(f"    Search: {search_name}")
    print("    Searching 6 Government Portals + Internet-Wide + Alternative Sources")
    print("=" * 90 + "\n")
    
    start_time = time.time()
    
    # Create local semaphore for this search
    search_semaphore = asyncio.Semaphore(semaphore_limit)
    logger.info(f"Using Semaphore({semaphore_limit}) for this search")
    
    
    # Fetch company profile if user_id provided
    if user_id:
        try:
            from backend.services.db import get_user_profile
            profile = await get_user_profile(user_id)
            if not keywords:
                keywords = profile.get("keywords", [])
            if not company_skills:
                company_skills = ", ".join(profile.get("capabilities", []))
            logger.info(f"Using profile for {user_id}: {profile.get('company')}")
        except Exception as e:
            logger.warning(f"Could not load profile for {user_id}: {e}")
    
    # Default values
    if not keywords:
        keywords = ["cybersecurity", "cloud", "software"]
    if not company_skills:
        company_skills = "software development, cloud services, cybersecurity, consulting"
    
    print(f"Search Keywords: {', '.join(keywords)}")
    print(f"Company Skills: {company_skills}\n")
    print("=" * 90)
    print("LAUNCHING ALL AGENTS\n")
    
    # Launch all 8 agents (6 government + web search + alternative sources)
    results = await asyncio.gather(
        # Government Portals (6 agents)
        run_agent_with_limit("SAM.gov", run_sam_gov_agent, keywords, semaphore=search_semaphore),
        run_agent_with_limit("TED EU", run_ted_eu_agent, keywords, semaphore=search_semaphore),
        run_agent_with_limit("UNGM", run_ungm_agent, keywords, semaphore=search_semaphore),
        run_agent_with_limit("Find a Tender", run_find_a_tender_agent, keywords, semaphore=search_semaphore),
        run_agent_with_limit("AusTender", run_austender_agent, keywords, semaphore=search_semaphore),
        run_agent_with_limit("CanadaBuys", run_canadabuys_agent, keywords, semaphore=search_semaphore),
        
        # Internet-wide search (2 new agents)
        run_agent_with_limit("Web Search", run_web_search_agent, keywords, company_skills, semaphore=search_semaphore),
        run_agent_with_limit("Alternative Sources", run_alternative_sources_agent, keywords, company_skills, semaphore=search_semaphore),
        
        return_exceptions=True
    )
    
    # Process results
    agent_names = [
        "SAM.gov", "TED EU", "UNGM", "Find a Tender", "AusTender", "CanadaBuys",
        "Web Search", "Alternative Sources"
    ]
    
    opportunities_by_source = {}
    total_opportunities = 0
    failed_agents = []
    
    print("\n" + "=" * 90)
    print("RESULTS\n")
    
    for i, (name, result) in enumerate(zip(agent_names, results)):
        if isinstance(result, Exception):
            print(f"  ❌ {name:25} | FAILED: {str(result)[:60]}")
            failed_agents.append(name)
        else:
            count = len(result) if isinstance(result, list) else 0
            opportunities_by_source[name.lower().replace(" ", "_")] = result
            total_opportunities += count
            status = "✅" if count > 0 else "⊘"
            print(f"  {status} {name:25} | {count:4} opportunities found")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 90)
    print(f"SUMMARY")
    print(f"  Total Opportunities: {total_opportunities}")
    print(f"  Execution Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"  Success Rate: {8 - len(failed_agents)}/8 agents")
    print("=" * 90 + "\n")
    
    if failed_agents:
        print(f"⚠️  Failed agents: {', '.join(failed_agents)}\n")
    
    # Flatten all opportunities into single list
    all_opportunities = []
    for source_results in opportunities_by_source.values():
        if isinstance(source_results, list):
            all_opportunities.extend(source_results)
    
    return {
        "total_opportunities": total_opportunities,
        "opportunities": all_opportunities,
        "by_source": opportunities_by_source,
        "execution_time": elapsed,
        "timestamp": datetime.utcnow().isoformat(),
        "search_keywords": keywords,
        "company_skills": company_skills,
        "success_rate": f"{8 - len(failed_agents)}/8",
    }


if __name__ == "__main__":
    # Test run with default keywords
    result = asyncio.run(run_complete_opportunity_search(
        keywords=["cybersecurity", "cloud", "machine learning"],
        company_skills="Python, AWS, DevOps, AI/ML, cybersecurity consulting"
    ))
    print(f"\n✅ Final Results:")
    print(json.dumps({
        "total": result["total_opportunities"],
        "by_source": {k: len(v) for k, v in result["by_source"].items()},
        "time_seconds": round(result["execution_time"], 1),
    }, indent=2))
