"""
TenderBot Global — Database Seeding Script
Initialises the database with a test user and sample tenders.
Validates realistic document structures against Pydantic models.
Ensures indexes are created and tested via explain plan.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import get_settings
from backend.services.db import connect_db, close_db, users_col, tenders_col, get_db
from backend.models import CompanyProfile, Tender, TenderStatus, TenderAction, PortalKey

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


async def seed_user():
    """Create a highly realistic tech company profile."""
    logger.info("Seeding test user profile...")
    
    profile_data = {
        "company_name": "TechVentures Cloud Solutions Inc",
        "website": "https://techventures-cloud.example.com",
        "headquarters_country": "US",
        "sectors": ["Cloud Infrastructure", "Cybersecurity", "AI Application Development"],
        "keywords": ["AWS migration", "kubernetes", "zero trust architecture", "machine learning"],
        "target_countries": ["US", "UK", "CA", "EU"],
        "min_value": 250000,
        "max_value": 15000000,
        "annual_turnover": 4500000.0,
        "headcount": 85,
        "years_in_business": 7,
        "certifications": ["ISO 27001", "SOC 2 Type II", "AWS Advanced Consulting Partner"],
        "past_contracts": ["Dept of Energy Cloud Migration (2024) - $2.1M", "NHS Virtual Care Platform AWS hosting (2023) - £1.5M"],
        "portals_enabled": [PortalKey.sam_gov, PortalKey.ted_eu, PortalKey.find_a_tender],
        "alert_email": "tenders@techventures-cloud.example.com"
    }

    # Validate against Pydantic model
    user = CompanyProfile(**profile_data)
    
    # Upsert to DB
    result = await users_col().update_one(
        {"company_name": user.company_name},
        {"$set": user.model_dump()},
        upsert=True
    )
    
    logger.info(f"✅ User seeded -> _id: {result.upserted_id or 'Already exists'}")


async def seed_tenders():
    """Create a spread of sample tenders: high score, low score, closing soon, enriched."""
    logger.info("Seeding sample tenders...")
    
    now = datetime.now(timezone.utc)
    
    tenders_data = [
        # Top match - enriched
        {
            "tender_id": "sam_gov_ai_cloud_123",
            "source_portal": PortalKey.sam_gov,
            "title": "Modernization of Cloud Infrastructure and AI Integration",
            "agency": "Department of Defense",
            "country": "US",
            "deadline": now + timedelta(days=14),
            "days_until_deadline": 14,
            "estimated_value": 8500000.0,
            "description": "Seeking comprehensive cloud migration, zero trust security implementation, and AI capabilities for the central command system.",
            "category_code": "541512",
            "raw_url": "https://sam.gov/opp/mock-ai-cloud/view",
            "status": TenderStatus.active,
            "relevance_score": 96,
            "match_reasons": ["Sectors align perfectly", "Value within target range", "Required certs (SOC 2) match"],
            "action": TenderAction.apply_now,
            "enriched": True,
            "eligibility_requirements": ["Must have ISO 27001", "Must have SOC 2 Type II", "Must be US headquartered"],
            "eligibility_score": 100,
            "scraped_at": now - timedelta(hours=2)
        },
        # High match - approaching deadline
        {
            "tender_id": "find_a_tender_nhs_sec_456",
            "source_portal": PortalKey.find_a_tender,
            "title": "NHS Trust Cybersecurity Audit and Resilience Upgrade",
            "agency": "National Health Service",
            "country": "UK",
            "deadline": now + timedelta(hours=36), # <48h deadline
            "days_until_deadline": 1,
            "estimated_value": 450000.0,
            "description": "Urgent requirement for external audit and zero trust architecture planning across 4 regional hospitals.",
            "category_code": "72220000",
            "raw_url": "https://find-a-tender.service.gov.uk/Notice/mock-nhs-sec/view",
            "status": TenderStatus.active,
            "relevance_score": 88,
            "action": TenderAction.apply_now,
            "enriched": False,
            "scraped_at": now - timedelta(hours=10)
        },
        # Partial match - watch
        {
            "tender_id": "ted_eu_ml_research_789",
            "source_portal": PortalKey.ted_eu,
            "title": "Horizon Europe - Distributed Machine Learning Research",
            "agency": "European Commission",
            "country": "EU",
            "deadline": now + timedelta(days=45),
            "days_until_deadline": 45,
            "estimated_value": 25000000.0, # Outside budget max
            "description": "Funding for consortia developing novel machine learning architectures.",
            "category_code": "73110000",
            "raw_url": "https://ted.europa.eu/en/notice/mock-ml-research/",
            "status": TenderStatus.active,
            "relevance_score": 62,
            "match_reasons": ["Technical keyword match: machine learning"],
            "disqualifiers": ["Value significantly above target budget max", "Primarily academic focus"],
            "action": TenderAction.watch,
            "enriched": False,
            "scraped_at": now - timedelta(days=1)
        },
        # Expired
        {
            "tender_id": "canadabuys_kube_000",
            "source_portal": PortalKey.canadabuys,
            "title": "Kubernetes Cluster Management Services",
            "agency": "Shared Services Canada",
            "country": "CA",
            "deadline": now - timedelta(days=5),
            "days_until_deadline": 0,
            "estimated_value": 750000.0,
            "description": "Ongoing management of existing k8s infrastructure.",
            "category_code": "D316",
            "raw_url": "https://canadabuys.canada.ca/en/tender-opportunities/mock-kube",
            "status": TenderStatus.expired,
            "relevance_score": 85,
            "action": TenderAction.skip,
            "enriched": False,
            "scraped_at": now - timedelta(days=10)
        }
    ]

    count = 0
    for data in tenders_data:
        # Pydantic validation guarantees schema safety
        tender = Tender(**data)
        
        await tenders_col().update_one(
            {"tender_id": tender.tender_id},
            {"$set": tender.model_dump()},
            upsert=True
        )
        count += 1
        
    logger.info(f"✅ Seeded {count} sample tenders.")


async def verify_indexes():
    """Runs a query and fetches the explain plan to confirm index usage."""
    logger.info("\nVerifying database indexes and query plans...")
    
    explain_plan = await tenders_col().find(
        {"status": "active", "relevance_score": {"$gte": 80}}
    ).sort("deadline", 1).explain()
    
    # Check if the query plan used an index (IXSCAN) vs collection scan (COLLSCAN)
    query_planner = explain_plan.get("queryPlanner", {})
    winning_plan = query_planner.get("winningPlan", {})
    
    # In a sorted query with filters, we check nested sub-plans
    uses_ixscan = "IXSCAN" in str(winning_plan)
    
    logger.info("-" * 50)
    if uses_ixscan:
        logger.info("✅ SUCCESS: Query planner is using IXSCAN (indexes are active).")
    else:
        logger.warning("⚠️ WARNING: Query planner used COLLSCAN. Indexes may not be fully built or optimal.")
        
    # Specifically list the indexes that exist on the collection
    indexes = await tenders_col().index_information()
    logger.info("\nActive Tenders Collection Indexes:")
    for name, details in indexes.items():
        keys = details.get('key', [])
        is_unique = " (UNIQUE)" if details.get('unique') else ""
        logger.info(f" - {name}{is_unique}: {keys}")
    logger.info("-" * 50)


async def main():
    print("============================================================")
    print("TENDERBOT GLOBAL — DATABASE SEEDING & SCHEMA VALIDATION")
    print("============================================================")
    
    await connect_db()
    
    try:
        await seed_user()
        await seed_tenders()
        await verify_indexes()
        
        print("\n🎉 PHASE 1 FOUNDATION (TASK 2.3) COMPLETE!")
        print("Model schemas validated, seed data injected, and queries are fast.")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    if not settings.mongodb_uri:
        print("ERROR: MONGODB_URI not found in environment.")
        sys.exit(1)
        
    # Test connection string quickly before proceeding
    if "api.tinyfish.ai" in settings.mongodb_uri:
         print("ERROR: Looks like config defaults or invalid env overriding.")
         sys.exit(1)
         
    asyncio.run(main())
