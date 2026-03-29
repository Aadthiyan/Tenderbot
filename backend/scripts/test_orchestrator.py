"""
TenderBot Global — Test Full Orchestration Pipeline
Tests Phase 3 (Multi-Portal Orchestration Layer) by directly invoking the 
engine behind the /scrape endpoint.
"""
import asyncio
import logging
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import get_settings
from backend.services.db import connect_db, close_db, users_col, tenders_col
from backend.pipelines.orchestrator import run_full_scrape

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

async def test_full_engine():
    print("==============================================================")
    print("TESTING FULL ORCHESTRATION ENGINE (TASK 3.6)")
    print("Agents > Normalizer > Scorer > Deep Scrape > Eligibility > DB")
    print("==============================================================\n")
    
    await connect_db()
    
    # 1. Fetch test user from DB
    user = await users_col().find_one({"company_name": "TechVentures Cloud Solutions Inc"})
    if not user:
        print("❌ Seed user not found. Did you run `python backend/scripts/seed_db.py`? "
              "We will use a fake dictionary to proceed.")
        user = {
            "company_name": "TechVentures Cloud Solutions Inc",
            "sectors": ["Cloud Infrastructure", "Cybersecurity", "AI Application Development"],
            "keywords": ["AWS migration", "kubernetes", "zero trust architecture", "machine learning"],
            "min_value": 250000,
            "max_value": 15000000,
            "target_countries": ["US", "UK", "CA", "EU"],
            "certifications": ["ISO 27001", "SOC 2 Type II", "AWS Advanced Consulting Partner"],
        }
    
    portals = ["sam_gov", "ted_eu", "ungm", "find_a_tender", "austender", "canadabuys"]
    
    try:
        # Clear out portal logs to prove a clean run
        await tenders_col().delete_many({"source_portal": {"$in": portals}, "status": "active"})
        
        print(f"User Profile   : {user.get('company_name')}")
        print(f"Target Portals : {portals}\n")
        print("Launching parallel swarm... (Please wait ~2 seconds for async mock data)\n")
        
        summary = await run_full_scrape(user, portals)
        
        print("\n--------------------------------------------------------------")
        print("🎉 SCORING AND DB PIPELINE COMPLETE!")
        print("--------------------------------------------------------------")
        print(json.dumps(summary, indent=2))
        
        if summary.get("tenders_inserted", 0) > 0:
            print("\n🔍 Checking database for enriched high-priority tender:")
            top_tender = await tenders_col().find_one(
                {"relevance_score": {"$gte": 80}, "enriched": True},
                sort=[("relevance_score", -1)]
            )
            
            if top_tender:
                print(f"  Title      : {top_tender.get('title')[:60]}...")
                print(f"  Score      : {top_tender.get('relevance_score')}/100")
                print(f"  Action     : {top_tender.get('action')}")
                print(f"  Eligibility: {top_tender.get('eligibility_score')}/100")
                
                reqs = top_tender.get("eligibility_requirements", [])
                if reqs:
                    print(f"  Req 1      : {reqs[0]}")
            else:
                print("  No enriched tenders found. (Scorer might not have triggered scores >= 80).")
                
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(test_full_engine())
