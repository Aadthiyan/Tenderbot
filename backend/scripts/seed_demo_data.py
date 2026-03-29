"""
TenderBot Global — Seed Demo Data
Populates your real MongoDB Atlas cluster with high-quality startup demo data.
Run this once to fill your database with realistic AI-enriched insights!
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.db import connect_db, close_db, tenders_col

DEMO_TENDERS = [
  {
    "tender_id": "DOD-2026-CLD-001",
    "title": "FedRAMP Cloud Migration & Zero Trust Security Audit",
    "agency": "Department of Defense",
    "country": "US",
    "source_portal": "sam_gov",
    "deadline": "2026-05-15T00:00:00Z",
    "days_until_deadline": 59,
    "estimated_value": 4500000,
    "relevance_score": 94,
    "action": "apply_now",
    "match_reasons": ["Zero Trust aligns with DoD mandate", "Cloud migration is core capability"],
    "disqualifiers": [],
    "our_probability": 72,
    "smb_win_rate": 41,
    "top_competitors": ["Booz Allen Hamilton", "SAIC"],
    "eligibility_score": 88,
    "enriched": True,
    "status": "active",
    "raw_url": "https://sam.gov/opp/mock001",
    "category_code": "541512",
    "reference_id": "DOD-2026-CLD-001",
    "description": "Seeking FedRAMP certified vendor for multi-cloud migration and Zero Trust rollout.",
    "intel_summary": "Defense market dominated by large integrators; SME teaming recommended.",
    "eligibility_checklist": [
      { "requirement": "Must hold an active FedRAMP Moderate or High Authorization", "status": "pass", "gap": None },
      { "requirement": "ISO 27001 or equivalent certification required", "status": "pass", "gap": None },
      { "requirement": "Minimum 5 years federal cloud migration experience", "status": "fail", "gap": "Profile shows 3 years. Need 2 more years of documented experience." },
      { "requirement": "Must be registered in SAM.gov with active CAGE code", "status": "pass", "gap": None },
      { "requirement": "DUNS or UEI number required for contract registration", "status": "unknown", "gap": None },
    ],
    "eligibility_action_plan": [
      "Obtain a DUNS/UEI number via the SAM.gov registration portal before submission.",
      "Document prior federal cloud migration work spanning back to 2021 with reference letters from client agencies.",
      "Consider teaming with a Prime that has 5+ years experience to meet the threshold."
    ],
    "amendment_history": [
      { "date": "2026-03-10", "type": "deadline_extension", "summary": "Submission deadline extended from April 1 to May 15 after vendor Q&A period.", "new_deadline": "2026-05-15", "is_cancelled": False },
      { "date": "2026-02-25", "type": "new_document", "summary": "Final RFP v2.1 released with updated technical evaluation criteria.", "new_deadline": None, "is_cancelled": False },
    ],
  },
  {
    "tender_id": "CAB-2026-DT-002",
    "title": "Digital Transformation Partner for Central Government",
    "agency": "Cabinet Office",
    "country": "UK",
    "source_portal": "find_a_tender",
    "deadline": "2026-04-25T00:00:00Z",
    "days_until_deadline": 39,
    "estimated_value": 7500000,
    "relevance_score": 87,
    "action": "apply_now",
    "match_reasons": ["GDS Digital framework alignment", "Agile delivery mindset"],
    "disqualifiers": [],
    "our_probability": 65,
    "smb_win_rate": 55,
    "top_competitors": ["CGI", "KPMG GovTech"],
    "eligibility_score": 82,
    "enriched": True,
    "status": "active",
    "raw_url": "https://find-a-tender.service.gov.uk/Notice/mock002",
    "category_code": "72224000",
    "reference_id": "CAB-2026-DT-002",
    "description": "Digital transformation and service redesign for central government departments.",
    "intel_summary": "UK market increasingly open to SMEs under G-Cloud 14 framework."
  },
  {
    "tender_id": "SSC-2026-003",
    "title": "Secure Cloud Email and Collaboration Platform",
    "agency": "Shared Services Canada",
    "country": "CA",
    "source_portal": "canadabuys",
    "deadline": "2026-04-30T00:00:00Z",
    "days_until_deadline": 44,
    "estimated_value": 3200000,
    "relevance_score": 81,
    "action": "apply_now",
    "match_reasons": ["Cloud collaboration is core", "Government-grade security required"],
    "disqualifiers": ["Must be registered in Canada"],
    "our_probability": 58,
    "smb_win_rate": 48,
    "top_competitors": ["Microsoft Canada", "Deloitte Canada"],
    "eligibility_score": 70,
    "enriched": True,
    "status": "active",
    "raw_url": "https://canadabuys.canada.ca/mock003",
    "category_code": "43231600",
    "reference_id": "SSC-2026-00456",
    "description": "Provision of M365 equivalent secure cloud collaboration for government employees.",
    "intel_summary": "Residency requirements may limit non-registered vendors."
  },
  {
    "tender_id": "MOJ-2026-004",
    "title": "AI Legal Case Review Automation Tool",
    "agency": "Ministry of Justice",
    "country": "UK",
    "source_portal": "find_a_tender",
    "deadline": "2026-05-15T00:00:00Z",
    "days_until_deadline": 59,
    "estimated_value": 1800000,
    "relevance_score": 78,
    "action": "watch",
    "match_reasons": ["AI/ML capability match", "SaaS delivery model preferred"],
    "disqualifiers": ["Must have prior public sector references"],
    "our_probability": 48,
    "smb_win_rate": 62,
    "top_competitors": ["Luminance", "Relativity"],
    "eligibility_score": 65,
    "enriched": False,
    "status": "active",
    "raw_url": "https://find-a-tender.service.gov.uk/Notice/mock004",
    "category_code": "72212450",
    "reference_id": "MOJ-2026-AI-009",
    "description": "Intelligent document review for caseload management using ML/NLP techniques.",
    "intel_summary": "Emerging LegalTech space; incumbent-free opportunity for innovative SMEs."
  },
  {
    "tender_id": "WFP-2026-005",
    "title": "UN World Food Programme Field Operations Software",
    "agency": "WFP",
    "country": "UN",
    "source_portal": "ungm",
    "deadline": "2026-06-01T00:00:00Z",
    "days_until_deadline": 76,
    "estimated_value": 2100000,
    "relevance_score": 74,
    "action": "watch",
    "match_reasons": ["Humanitarian tech alignment", "Open-source stack preference"],
    "disqualifiers": [],
    "our_probability": 44,
    "smb_win_rate": 52,
    "top_competitors": ["Palantir", "UN-OCHA Tech"],
    "eligibility_score": 72,
    "enriched": False,
    "status": "active",
    "raw_url": "https://ungm.org/Public/Notice/mock005",
    "category_code": "72212000",
    "reference_id": "WFP-2026-007",
    "description": "Field operations and logistics management SaaS for emergency food distribution.",
    "intel_summary": "UNGM favors non-profit or B-Corp certified vendors; explore partnerships."
  }
]

async def seed_data():
    print("🔌 Connecting to MongoDB Atlas...")
    await connect_db()
    
    col = tenders_col()
    print("🧹 Cleaning old startup demo data...")
    await col.delete_many({})
    
    print(f"🌱 Inserting {len(DEMO_TENDERS)} high-quality startup demo tenders...")
    await col.insert_many(DEMO_TENDERS)
    
    print("✅ Seed complete! Your startup dashboard is now rendering from real Atlas queries.")

if __name__ == "__main__":
    asyncio.run(seed_data())
