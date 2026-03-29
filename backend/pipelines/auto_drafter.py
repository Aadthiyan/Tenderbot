"""
TenderBot — Auto Drafter Pipeline
Queues high-score tenders for AI proposal generation with human approval gate.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.config import get_settings
from backend.services.db import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"


async def auto_queue_for_draft(tender: dict, user_profile: dict) -> bool:
    """
    Queue a high-score tender for proposal drafting.
    Returns True if newly queued, False if already exists.
    """
    db = get_db()
    tender_id = tender.get("tender_id")
    company_name = user_profile.get("company_name", "Unknown")

    doc = {
        "tender_title": tender.get("title", "Untitled"),
        "tender_score": tender.get("relevance_score"),
        "tender_agency": tender.get("agency"),
        "tender_deadline": tender.get("deadline"),
        "status": "pending_approval",
        "draft_markdown": None,
        "amendment_triggered": False,
        "queued_at": datetime.now(timezone.utc),
        "approved_at": None,
        "submitted_at": None,
    }

    # Tier 1 Fix: Atomic Upsert to prevent race conditions from concurrent scrapes
    result = await db["draft_queue"].update_one(
        {"tender_id": tender_id, "company_name": company_name},
        {"$setOnInsert": doc},
        upsert=True
    )
    
    if result.upserted_id:
        logger.info(f"📋 Auto-queued draft for '{tender.get('title')}' (score={tender.get('relevance_score')})")
        return True
    
    return False


async def generate_draft_for_tender(tender_id: str, company_name: str) -> Optional[str]:
    """
    Calls Fireworks AI to generate a proposal draft for a queued tender.
    Updates the draft_queue document with the result.
    Returns the generated markdown or None on failure.
    """
    import httpx
    db = get_db()

    tender = await db["tenders"].find_one({"tender_id": tender_id}, {"_id": 0, "page_snapshot": 0, "embedding": 0})
    if not tender:
        logger.error(f"Tender {tender_id} not found for drafting.")
        return None

    profile = await db["users"].find_one({"company_name": company_name}, {"_id": 0}) or {}
    persona = profile.get("agent_persona", "You are a professional government bid writer.")

    # Construct Recon string for Feature 2
    recon_data = tender.get("competitor_recon_data", [])
    recon_text = "\n".join(recon_data) if recon_data else "No specific competitor intel available."
    
    # Feature 3: Actor-Critic Self-Refinement Loop
    max_attempts = 3
    current_draft = None
    critique_history = ""
    
    for attempt in range(max_attempts):
        logger.info(f"Drafting attempt {attempt+1}/{max_attempts} for {tender_id}")
        
        prompt = f"""{persona}

Write a professional proposal for this government tender:

TENDER: {tender.get('title')}
AGENCY: {tender.get('agency')}
DESCRIPTION: {tender.get('description', 'N/A')[:10000]}
VALUE: {tender.get('estimated_value', 'TBD')}
DEADLINE: {tender.get('deadline', 'TBD')}
WIN PROBABILITY: {tender.get('our_probability', 'N/A')}%

COMPETITOR RECONNAISSANCE:
{recon_text}

Structure your response with these sections:
# Executive Summary
# Our Approach
# Relevant Experience & Capabilities
# Why Choose {company_name} (Address our strengths against the competitors listed above)
# Proposed Timeline

{critique_history}

Keep it persuasive, concise, and focused on the agency's specific needs."""

        if not settings.fireworks_api_key:
            current_draft = f"# Mock Draft\n\n**Tender:** {tender.get('title')}\n\n*Fireworks API key not configured — this is a mock draft.*"
            break

        headers = {"Authorization": f"Bearer {settings.fireworks_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": settings.fireworks_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": 0.3,
        }

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(FIREWORKS_URL, headers=headers, json=payload)
                resp.raise_for_status()
                current_draft = resp.json()["choices"][0]["message"]["content"]
            
            # Now trigger the Critic Agent
            score, critique_feedback = await critic_agent_eval(current_draft, tender)
            logger.info(f"Critic evaluation: Score {score}/100")
            
            if score >= 90 or attempt == max_attempts - 1:
                break
            else:
                critique_history = f"\n\nCRITIQUE FROM PREVIOUS DRAFT (You scored {score}/100). FIX THESE ISSUES:\n{critique_feedback}\n"
                
        except Exception as e:
            logger.error(f"Draft generation/critique failed on attempt {attempt+1} for {tender_id}: {e}")
            if current_draft:
                break
            return None

    if current_draft:
        await db["draft_queue"].update_one(
            {"tender_id": tender_id, "company_name": company_name},
            {"$set": {"draft_markdown": current_draft, "draft_generated_at": datetime.now(timezone.utc)}}
        )
        logger.info(f"✅ Final Draft completed for tender {tender_id}")
        return current_draft

    return None


async def regenerate_draft(tender_id: str, company_name: str, reason: str = "amendment") -> bool:
    """
    Re-generate an existing draft due to an amendment or revision request.
    Resets approval status to pending_approval.
    """
    db = get_db()
    await db["draft_queue"].update_one(
        {"tender_id": tender_id, "company_name": company_name},
        {"$set": {
            "status": "pending_approval",
            "amendment_triggered": reason == "amendment",
            "draft_markdown": None,
            "approved_at": None,
        }}
    )
    draft = await generate_draft_for_tender(tender_id, company_name)
    return draft is not None


async def critic_agent_eval(draft: str, tender: dict) -> tuple[int, str]:
    """Critic Agent that grades the draft against eligibility requirements."""
    if not settings.fireworks_api_key:
        return 95, "Mock perfect score."
        
    reqs = tender.get("eligibility_requirements", [])
    reqs_text = "\n".join([f"- {r.get('requirement', 'Unknown')}" for r in reqs]) if reqs else "Standard compliance."

    prompt = f"""You are a strict QA Critic for government proposals.
Grade this draft against the tender requirements.

REQUIREMENTS WE MUST ADDRESS:
{reqs_text}

DRAFT PROPOSAL:
{draft}

Analyze it and return ONLY valid JSON in this exact format:
{{
   "score": 85,
   "critique": "- You forgot to mention pricing details.\\n- The Executive Summary needs to be punchier."
}}"""

    headers = {"Authorization": f"Bearer {settings.fireworks_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        import httpx
        import json
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(FIREWORKS_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(data)
            return int(parsed.get("score", 50)), parsed.get("critique", "Unclear critique format.")
    except Exception as e:
        logger.warning(f"Critic Agent failed: {e}")
        return 90, f"Critic failed: {e}"
