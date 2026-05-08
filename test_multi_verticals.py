"""
Test TenderBot across multiple industry verticals
Measures: Opportunities, High-Relevance Count, Execution Time, Source Breakdown
Purpose: ROI analysis by vertical to identify best markets
"""
import asyncio
import json
from datetime import datetime
from backend.pipelines.integrated_pipeline import run_complete_integrated_search

# Define industry verticals to test
VERTICALS = {
    "Cybersecurity & Cloud": {
        "keywords": ["cybersecurity", "cloud", "AWS", "security", "infrastructure"],
        "company_skills": "Python, AWS, Kubernetes, Docker, Security, DevOps, TensorFlow, Firewalls"
    },
    "Data Science & AI": {
        "keywords": ["data science", "machine learning", "AI", "analytics", "BigData", "ML"],
        "company_skills": "Python, R, TensorFlow, Spark, SQL, Analytics, Pandas, Scikit-learn, PyTorch"
    },
    "Healthcare IT": {
        "keywords": ["healthcare", "medical", "HIPAA", "health IT", "telemedicine", "EHR"],
        "company_skills": "HIPAA compliance, Java, Python, HL7, Healthcare IT, FHIR, Medical devices"
    },
    "Manufacturing & Supply Chain": {
        "keywords": ["manufacturing", "supply chain", "logistics", "IoT", "automation"],
        "company_skills": "Industrial automation, IoT, C++, PLC programming, Supply chain management, SAP"
    },
    "Renewable Energy": {
        "keywords": ["renewable energy", "solar", "wind", "green", "sustainability", "battery"],
        "company_skills": "Electrical engineering, Solar technology, Wind power, Battery storage, Grid management"
    }
}


async def test_vertical(vertical_name: str, config: dict) -> dict:
    """Test a single vertical and return metrics"""
    print(f"\n🔷 Testing: {vertical_name}")
    print("-" * 80)
    
    start_time = datetime.now()
    
    try:
        result = await run_complete_integrated_search(
            user_id=f"vertical_test_{vertical_name.lower().replace(' ', '_')}",
            keywords=config['keywords'],
            company_skills=config['company_skills'],
            search_name=f"{vertical_name} Discovery",
            min_score=60.0
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        metrics = {
            'vertical': vertical_name,
            'status': 'SUCCESS',
            'total_found': result['total_found'],
            'after_dedup': result['total_deduplicated'],
            'high_relevance': result['high_relevance'],
            'ready_to_pursue': result['ready_to_pursue'],
            'alerts_sent': result['alerts_sent'],
            'execution_time_seconds': elapsed,
            'execution_time_minutes': round(elapsed / 60, 1),
            'opportunities_per_minute': round(result['total_deduplicated'] / (elapsed / 60), 1) if elapsed > 0 else 0
        }
        
        # Breakdown by source
        by_source = {}
        for opp in result['opportunities']:
            source = opp.get('source', 'Unknown')
            by_source[source] = by_source.get(source, 0) + 1
        
        metrics['by_source'] = by_source
        
        return metrics
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            'vertical': vertical_name,
            'status': 'FAILED',
            'error': str(e)
        }


async def run_multi_vertical_test():
    """Run tests across all verticals and compare ROI"""
    
    print("\n" + "=" * 80)
    print("🌍 TENDERBOT MULTI-VERTICAL ROI TEST")
    print("=" * 80)
    print(f"Testing {len(VERTICALS)} industry verticals")
    print(f"Start time: {datetime.now().isoformat()}\n")
    
    results = {}
    
    # Test each vertical
    for vertical_name, config in VERTICALS.items():
        result = await test_vertical(vertical_name, config)
        results[vertical_name] = result
    
    # =========================================================================
    # ANALYSIS & ROI COMPARISON
    # =========================================================================
    print("\n" + "=" * 80)
    print("📊 ROI ANALYSIS - OPPORTUNITIES BY VERTICAL")
    print("=" * 80)
    
    # Sort by high-relevance count
    sorted_verticals = sorted(
        results.items(),
        key=lambda x: x[1].get('high_relevance', 0),
        reverse=True
    )
    
    print(f"\n{'Vertical':<30} {'Total':<8} {'High R':<8} {'Ready':<8} {'Time':<8} {'Opp/Min':<10} {'Top Source':<15}")
    print("-" * 95)
    
    for vertical_name, metrics in sorted_verticals:
        if metrics['status'] == 'FAILED':
            print(f"{vertical_name:<30} {'FAILED':<50}")
            continue
        
        # Find top source
        by_source = metrics.get('by_source', {})
        top_source = max(by_source.items(), key=lambda x: x[1])[0] if by_source else 'N/A'
        
        print(f"{vertical_name:<30} {metrics['total_found']:<8} {metrics['high_relevance']:<8} "
              f"{metrics['ready_to_pursue']:<8} {metrics['execution_time_minutes']:<8.1f} "
              f"{metrics['opportunities_per_minute']:<10.1f} {top_source:<15}")
    
    # Calculate totals
    total_found = sum(r.get('total_found', 0) for r in results.values() if r.get('status') == 'SUCCESS')
    total_high_rel = sum(r.get('high_relevance', 0) for r in results.values() if r.get('status') == 'SUCCESS')
    total_ready = sum(r.get('ready_to_pursue', 0) for r in results.values() if r.get('status') == 'SUCCESS')
    total_time = sum(r.get('execution_time_seconds', 0) for r in results.values() if r.get('status') == 'SUCCESS')
    
    print("-" * 95)
    print(f"{'TOTAL':<30} {total_found:<8} {total_high_rel:<8} {total_ready:<8} "
          f"{round(total_time/60, 1):<8} {'':<10.1f}")
    
    # =========================================================================
    # INSIGHTS
    # =========================================================================
    print("\n" + "=" * 80)
    print("💡 KEY INSIGHTS")
    print("=" * 80)
    
    # Best vertical for volume
    best_volume = max(sorted_verticals, key=lambda x: x[1].get('total_found', 0))
    print(f"\n1️⃣  Highest Volume: {best_volume[0]}")
    print(f"    {best_volume[1]['total_found']} opportunities, {best_volume[1]['high_relevance']} high-relevance")
    
    # Best vertical for relevance rate
    relevance_rates = []
    for vertical, metrics in results.items():
        if metrics['status'] == 'SUCCESS':
            rate = (metrics['high_relevance'] / metrics['total_deduplicated'] * 100) if metrics['total_deduplicated'] > 0 else 0
            relevance_rates.append((vertical, rate, metrics))
    
    if relevance_rates:
        best_relevance = max(relevance_rates, key=lambda x: x[1])
        print(f"\n2️⃣  Best Relevance Rate: {best_relevance[0]}")
        print(f"    {best_relevance[1]:.1f}% high-relevance ({best_relevance[2]['high_relevance']}/{best_relevance[2]['total_deduplicated']} opportunities)")
    
    # Fastest execution
    fastest = min(
        [(v, m) for v, m in results.items() if m.get('status') == 'SUCCESS'],
        key=lambda x: x[1].get('execution_time_seconds', float('inf'))
    )
    print(f"\n3️⃣  Fastest Vertical: {fastest[0]}")
    print(f"    {fastest[1]['execution_time_minutes']:.1f} minutes, {fastest[1]['opportunities_per_minute']:.1f} opp/min")
    
    # Most consistent (across sources)
    print(f"\n4️⃣  Opportunities by Primary Source:")
    source_totals = {}
    for vertical, metrics in results.items():
        if metrics['status'] == 'SUCCESS':
            for source, count in metrics.get('by_source', {}).items():
                source_totals[source] = source_totals.get(source, 0) + count
    
    for source, count in sorted(source_totals.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_found * 100) if total_found > 0 else 0
        print(f"    • {source:<30} {count:>4} opportunities ({pct:.1f}%)")
    
    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n✅ FOCUS AREAS (Highest ROI):")
    for i, (vertical, metrics) in enumerate(sorted_verticals[:2], 1):
        if metrics['status'] != 'FAILED':
            print(f"   {i}. {vertical}: {metrics['total_found']} opportunities, {metrics['high_relevance']} high-relevance")
    
    print("\n⚠️  OPPORTUNITIES FOR IMPROVEMENT:")
    failed = [v for v, m in results.items() if m['status'] == 'FAILED']
    if failed:
        print(f"   • Fix {len(failed)} failing verticals: {', '.join(failed)}")
    
    low_perf = [
        (v, m) for v, m in results.items()
        if m['status'] == 'SUCCESS' and m['total_found'] < 50
    ]
    if low_perf:
        print(f"   • Low performers (< 50 opps): {', '.join([v for v, _ in low_perf])}")
    
    print("\n🚀 DEPLOYMENT READINESS:")
    success_count = sum(1 for m in results.values() if m['status'] == 'SUCCESS')
    print(f"   • {success_count}/{len(VERTICALS)} verticals working")
    print(f"   • {total_ready} opportunities ready to pursue")
    print(f"   • Estimated daily discovery rate: {round(total_ready * 3)} opps (with 3 searches/day)")
    
    # =========================================================================
    # SAVE RESULTS
    # =========================================================================
    filename = f"multi_vertical_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output = {
        'timestamp': datetime.now().isoformat(),
        'verticals_tested': len(VERTICALS),
        'success_rate': f"{success_count}/{len(VERTICALS)}",
        'total_opportunities': total_found,
        'total_high_relevance': total_high_rel,
        'total_ready_to_pursue': total_ready,
        'total_execution_time_minutes': round(total_time / 60, 1),
        'results_by_vertical': results
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}\n")
    
    return output


if __name__ == "__main__":
    result = asyncio.run(run_multi_vertical_test())
