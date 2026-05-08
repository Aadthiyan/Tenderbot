# 🎯 Expand to 12-16 Agents — Discovery Opportunity Analysis

## Current Coverage (8 Agents)
✅ SAM.gov (US Federal)
✅ TED EU (European Tenders)
✅ UNGM (UN/Multilateral)
✅ Find a Tender (Mixed UK/International)
✅ AusTender (Australia)
✅ CanadaBuys (Canada)
✅ Web Search (Internet-wide)
✅ Alternative Sources (LinkedIn, BidNet, Alibaba, etc.)

---

## Proposed New Agents (4-8 Additional)

### TIER 1: High-Value US Government (Add 3)
**Coverage Gap:** Local & state government procurement

1. **SBA (Small Business Administration)**
   - URL: https://www.sba.gov/
   - Use Case: Small business set-asides, minority-owned business contracts
   - Expected Yield: 15-30 opportunities/search
   - Time: 2 hours to build
   - Priority: **🔴 HIGH** - Untapped market

2. **State-Level Portals** (Start with CA, NY, TX)
   - California: https://caleprocure.ca.gov/
   - New York: https://www.nyscoppn.ogs.ny.gov/
   - Texas: https://www.txdps.state.tx.us/
   - Expected Yield: 50-100 opportunities/search (combined)
   - Time: 4-6 hours to build (one per state)
   - Priority: **🔴 HIGH** - $Billions in state contracts

3. **Local Government (City/County)**
   - Use Govspend API or city procurement databases
   - Start with major cities: NYC, LA, Chicago, Houston, Phoenix
   - Expected Yield: 30-50 opportunities/search
   - Time: 3 hours to build
   - Priority: **🟡 MEDIUM** - Good size, regional variation

---

### TIER 2: Non-Government & Academic (Add 2-3)

4. **Nonprofit & Foundation Grants**
   - Sources: Foundation Center, Grants.gov (non-federal), GiveWell, Candid
   - Use Case: Nonprofit contracting, consulting opportunities
   - Expected Yield: 20-40 opportunities/search
   - Time: 2-3 hours
   - Priority: **🟡 MEDIUM** - Growing market

5. **University & Research RFPs**
   - Sources: NSF, NIH, University consortiums
   - Use Case: R&D contracts, academic partnerships
   - Expected Yield: 15-30 opportunities/search
   - Time: 2 hours
   - Priority: **🟡 MEDIUM** - High-value contracts

6. **Private Sector Contracting**
   - Sources: Certify (pre-vetted suppliers), Vendor platforms, B2B networks
   - Use Case: Private company subcontracting
   - Expected Yield: 25-40 opportunities/search
   - Time: 2 hours
   - Priority: **🟡 MEDIUM** - High frequency

---

### TIER 3: International & Specialized (Add 1-2)

7. **Asian Government Portals** (Japan, Singapore, South Korea)
   - Expected Yield: 20-35 opportunities/search
   - Time: 3 hours
   - Priority: **🟢 LOW** - Lower English content

8. **Industry-Specific Clearinghouses** (Healthcare, Manufacturing, Energy, Defense)
   - Expected Yield: Varies by industry
   - Time: 2-3 hours each
   - Priority: **🟢 LOW** - Use if focusing on specific verticals

---

## Implementation Plan

### Phase 1: Quick Wins (This Week) - 3 Agents
- ✅ SBA agent (highest ROI, 2hr build)
- ✅ State-Level pilot (CA only, 2hr build, expandable)
- ✅ Local Government (2hr build)
**Total Time:** 6 hours | **Expected Yield Increase:** +75-150 opps/search

### Phase 2: Diversification (Next Week) - 2-3 Agents
- ✅ Nonprofit/Foundation agent (2hr)
- ✅ University RFP agent (2hr)
- ✅ Private Sector Contracting (2hr)
**Total Time:** 6 hours | **Expected Yield Increase:** +60-110 opps/search

### Phase 3: Global & Specialized (Later) - 2+ Agents
- ✅ Asian portals (3hr)
- ✅ Industry-specific (2-3hr each)
**Total Time:** 5-9 hours | **Expected Yield Increase:** +40-75 opps/search

---

## ROI Analysis

### Current System (8 Agents)
- **Time per search:** 29.3 minutes
- **Opportunities per search:** 189
- **Opportunities per minute:** 6.4
- **Coverage:** US Federal (main), Europe, UN, Australia, Canada, Alternative

### With Phase 1 (11 Agents)
- **Time per search:** ~40 minutes (est.)
- **Opportunities per search:** 260-340 (conservative estimate)
- **Opportunities per minute:** 6.5-8.5
- **ROI:** +40-80% more opportunities, only +37% more time

### With Phase 1+2 (14 Agents)
- **Time per search:** ~55 minutes (est.)
- **Opportunities per search:** 320-450
- **Opportunities per minute:** 5.8-8.2
- **ROI:** +70-140% more opportunities, +90% more time (but more coverage targets market gaps)

---

## Build Strategy

### Standard Agent Template
```python
async def run_NEW_AGENT(keywords: list[str]) -> list[dict]:
    """
    Returns:
        [{
            'title': str,
            'organization': str,
            'url': str,
            'deadline': str (YYYY-MM-DD or null),
            'opportunity_type': str (Contract, Grant, RFP, etc.),
            'estimated_value': str or null,
            'description': str (250-500 words),
            'source': 'NEW_AGENT_NAME'
        }]
    """
```

### Testing Each Agent
1. Test with 3 keyword sets
2. Verify data quality (non-null critical fields)
3. Validate deadline parsing
4. Check for duplicates vs existing agents
5. Measure execution time
6. Add timeout handling (300s per agent)

---

## Recommendation: START HERE

**Build in this order:**

1. **SBA Agent** (1-2 hours)
   - Highest ROI for US-focused businesses
   - API-based, well-documented
   - Testing: 15-30 opportunities expected

2. **State Portal Agent** (CA only first, 2 hours)
   - Proven market (CA budget: $1T+)
   - Repeatable pattern for other states
   - Testing: 20-40 opportunities

3. **Local Government Agent** (2 hours)
   - Hundreds of cities, millions in contracts
   - Web scraping or API integration
   - Testing: 15-30 opportunities

**Total time:** 5-6 hours | **Expected gain:** +50-100 opportunities/search

---

## Questions to Clarify Before Building

1. Which geographies are priority? (US only? EMEA? APAC?)
2. Which industries? (Any, or focus on specific sectors?)
3. What's your minimum contract value? (Filter out micro-bids?)
4. Need real-time vs. batch? (Daily updates needed?)
5. Budget constraints? (Some APIs cost $$)

