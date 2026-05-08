"""
TenderBot Global — Complete Integrated Pipeline
Phase 4: Search → Score → Eligibility → Alerts

This orchestrates the FULL workflow:
1. Search using all 11 agents
2. Normalize and deduplicate results
3. Score each opportunity (relevance to company)
4. Check eligibility
5. Trigger alerts for high-value opportunities
6. Store in database
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from backend.pipelines.expanded_search_orchestrator import run_expanded_opportunity_search
from backend.pipelines.scorer import score_opportunities
from backend.pipelines.eligibility import check_eligibility
from backend.services.alerts_service import check_and_send_alerts

logger = logging.getLogger(__name__)


async def run_complete_integrated_search(
    user_id: str,
    keywords: Optional[list[str]] = None,
    company_skills: Optional[str] = None,
    semaphore_limit: int = 15,
    search_name: str = None,
    min_score: float = 60.0,  # Minimum relevance score to process
) -> dict:
    """
    Run complete integrated pipeline:
    Search → Normalize → Score → Eligibility → Alerts → Save
    
    Args:
        user_id: User/company ID for profile lookup and scoring
        keywords: Search keywords
        company_skills: Company capabilities
        semaphore_limit: Concurrency for agents (15 for single, 8 for parallel)
        search_name: Name for this search
        min_score: Minimum relevance score to include
    
    Returns:
        {
            'total_found': int,          # Raw opportunities from search
            'total_scored': int,         # Opportunities with scores
            'high_relevance': int,       # Score >= min_score
            'has_gaps': int,             # Eligibility gaps detected
            'alerts_sent': int,          # Alerts generated
            'opportunities': list,       # Full processed results
            'execution_time': float,
            'timestamp': str
        }
    """
    
    print("\n" + "=" * 110)
    print("🚀  TENDERBOT GLOBAL — COMPLETE INTEGRATED PIPELINE")
    print("    Search → Score → Eligibility → Alerts → Database")
    if search_name:
        print(f"    Search: {search_name}")
    print("=" * 110 + "\n")
    
    start_time = datetime.now()
    
    # ============================================================================
    # PHASE 1: DISCOVERY (Search all 11 agents)
    # ============================================================================
    print("\n📍 PHASE 1: DISCOVERY (Searching 11 agents for opportunities...)")
    print("-" * 110)
    
    search_results = await run_expanded_opportunity_search(
        user_id=user_id,
        keywords=keywords,
        company_skills=company_skills,
        semaphore_limit=semaphore_limit,
        search_name=search_name
    )
    
    raw_opportunities = search_results.get("opportunities", [])
    total_found = len(raw_opportunities)
    
    print(f"\n✅ DISCOVERY COMPLETE: {total_found} opportunities found")
    print(f"   - Execution time: {search_results['execution_time']:.1f} seconds")
    print(f"   - Success rate: {search_results['success_rate']}")
    
    # ============================================================================
    # PHASE 2: NORMALIZE & DEDUPE (Clean up results)
    # ============================================================================
    print("\n📍 PHASE 2: NORMALIZE & DEDUPLICATE")
    print("-" * 110)
    
    # Remove duplicates based on title + organization
    seen = set()
    normalized_opportunities = []
    
    for opp in raw_opportunities:
        key = (opp.get('title', '').lower(), opp.get('organization', '').lower())
        if key not in seen:
            seen.add(key)
            # Ensure all required fields exist
            normalized_opportunities.append({
                'title': opp.get('title', 'Unknown'),
                'organization': opp.get('organization', 'Unknown'),
                'opportunity_type': opp.get('opportunity_type', 'Contract'),
                'url': opp.get('url', ''),
                'deadline': opp.get('deadline'),
                'estimated_value': opp.get('estimated_value'),
                'description': opp.get('description', ''),
                'source': opp.get('source', 'Unknown'),
                'discovered_at': datetime.utcnow().isoformat()
            })
    
    after_dedup = len(normalized_opportunities)
    print(f"✅ DEDUPLICATE: {total_found} → {after_dedup} unique opportunities")
    print(f"   (Removed {total_found - after_dedup} duplicates)")
    
    # ============================================================================
    # PHASE 3: SCORE (Relevance to company)
    # ============================================================================
    print("\n📍 PHASE 3: SCORING (Relevance analysis...)")
    print("-" * 110)
    
    scored_opportunities = []
    try:
        scored_opportunities = await score_opportunities(
            opportunities=normalized_opportunities,
            user_id=user_id,
            keywords=keywords,
            company_skills=company_skills
        )
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        # Fallback: mark all as moderate relevance
        scored_opportunities = [
            {**opp, 'relevance_score': 50.0, 'match_reason': 'Generic match'}
            for opp in normalized_opportunities
        ]
    
    high_relevance = sum(1 for opp in scored_opportunities if opp.get('relevance_score', 0) >= min_score)
    
    print(f"✅ SCORING COMPLETE: {len(scored_opportunities)} opportunities scored")
    print(f"   - High relevance (≥{min_score}): {high_relevance}")
    print(f"   - Score distribution:")
    score_80plus = sum(1 for opp in scored_opportunities if opp.get('relevance_score', 0) >= 80)
    score_60_79 = sum(1 for opp in scored_opportunities if 60 <= opp.get('relevance_score', 0) < 80)
    score_below60 = sum(1 for opp in scored_opportunities if opp.get('relevance_score', 0) < 60)
    print(f"     • Excellent (80+): {score_80plus}")
    print(f"     • Good (60-79): {score_60_79}")
    print(f"     • Fair (<60): {score_below60}")
    
    # ============================================================================
    # PHASE 4: ELIGIBILITY CHECK
    # ============================================================================
    print("\n📍 PHASE 4: ELIGIBILITY CHECK")
    print("-" * 110)
    
    opportunities_with_eligibility = []
    gaps_count = 0
    
    try:
        for opp in scored_opportunities:
            # Only check eligibility for high-relevance opportunities
            if opp.get('relevance_score', 0) >= min_score:
                try:
                    eligibility_result = await check_eligibility(
                        opportunity=opp,
                        user_id=user_id
                    )
                    opp['eligibility'] = eligibility_result
                    
                    if eligibility_result.get('has_gaps', False):
                        gaps_count += 1
                    
                    opportunities_with_eligibility.append(opp)
                except Exception as e:
                    logger.warning(f"Eligibility check failed for {opp['title']}: {e}")
                    # Add opportunity anyway, mark as unchecked
                    opp['eligibility'] = {'has_gaps': None, 'reason': 'Check failed'}
                    opportunities_with_eligibility.append(opp)
            else:
                opportunities_with_eligibility.append(opp)
    
    except Exception as e:
        logger.error(f"Eligibility phase error: {e}")
        opportunities_with_eligibility = scored_opportunities
    
    print(f"✅ ELIGIBILITY CHECK COMPLETE")
    print(f"   - Opportunities checked: {high_relevance}")
    print(f"   - With gaps/issues: {gaps_count}")
    print(f"   - Ready to pursue: {high_relevance - gaps_count}")
    
    # ============================================================================
    # PHASE 5: ALERTS
    # ============================================================================
    print("\n📍 PHASE 5: ALERTS & NOTIFICATIONS")
    print("-" * 110)
    
    alerts_sent = 0
    try:
        alerts_sent = await check_and_send_alerts(
            opportunities=opportunities_with_eligibility,
            user_id=user_id,
            min_score=min_score
        )
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        alerts_sent = 0
    
    print(f"✅ ALERTS PROCESSED: {alerts_sent} alerts sent/queued")
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 110)
    print("✨ COMPLETE INTEGRATED PIPELINE FINISHED")
    print("=" * 110)
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Total Found ............ {total_found} raw opportunities")
    print(f"   After Deduplication ... {after_dedup} unique opportunities")
    print(f"   High Relevance ........ {high_relevance} (≥{min_score} score)")
    print(f"   Eligibility Gaps ...... {gaps_count} opportunities")
    print(f"   Ready to Pursue ....... {high_relevance - gaps_count} opportunities")
    print(f"   Alerts Sent ........... {alerts_sent}")
    print(f"\n⏱️  Total Time: {execution_time:.1f} seconds ({execution_time/60:.1f} minutes)")
    print(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    print("\n" + "=" * 110 + "\n")
    
    return {
        'total_found': total_found,
        'total_deduplicated': after_dedup,
        'total_scored': len(scored_opportunities),
        'high_relevance': high_relevance,
        'has_gaps': gaps_count,
        'ready_to_pursue': high_relevance - gaps_count,
        'alerts_sent': alerts_sent,
        'opportunities': opportunities_with_eligibility,
        'execution_time': execution_time,
        'timestamp': datetime.utcnow().isoformat(),
        'search_config': {
            'keywords': keywords,
            'company_skills': company_skills,
            'min_score': min_score,
            'semaphore_limit': semaphore_limit
        }
    }


if __name__ == "__main__":
    # Example: Run integrated pipeline for a user
    result = asyncio.run(run_complete_integrated_search(
        user_id="demo_user",
        keywords=["cybersecurity", "cloud", "DevOps"],
        company_skills="Python, AWS, Kubernetes, Docker, Security, DevOps",
        search_name="Cybersecurity & Cloud Search"
    ))
    
    print("\n✅ Pipeline Output:")
    summary = {
        "total_found": result["total_found"],
        "after_dedup": result["total_deduplicated"],
        "high_relevance": result["high_relevance"],
        "ready_to_pursue": result["ready_to_pursue"],
        "alerts_sent": result["alerts_sent"],
        "time_minutes": round(result["execution_time"] / 60, 1)
    }
    print(json.dumps(summary, indent=2))
