"""
TenderBot Global — /tenders Router
Query tender list and individual tender detail.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pydantic import BaseModel
from backend.services.db import tenders_col
import logging

router = APIRouter(prefix="/tenders", tags=["Tenders"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_tenders(
    score_min: int = Query(0, ge=0, le=100, description="Minimum relevance score"),
    score_max: int = Query(100, ge=0, le=100, description="Maximum relevance score"),
    country: Optional[str] = Query(None, description="ISO country code filter (e.g. US, EU)"),
    portal: Optional[str] = Query(None, description="Portal key filter (e.g. sam_gov)"),
    status: Optional[str] = Query("active", description="Tender status filter"),
    enriched_only: bool = Query(False, description="Return only deep-scraped tenders"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """
    Returns tenders sorted by relevance_score DESC, then deadline ASC.
    Used by the main dashboard.
    """
    query: dict = {}

    if score_min > 0 or score_max < 100:
        query["relevance_score"] = {"$gte": score_min, "$lte": score_max}
    if country:
        query["country"] = country.upper()
    if portal:
        query["source_portal"] = portal
    if status:
        query["status"] = status
    if enriched_only:
        query["enriched"] = True

    cursor = tenders_col().find(query, {"_id": 0, "page_snapshot": 0}).sort(
        [("relevance_score", -1), ("days_until_deadline", 1)]
    ).skip(skip).limit(limit)

    tenders = await cursor.to_list(length=limit)
    total = await tenders_col().count_documents(query)

    return {"total": total, "tenders": tenders}


@router.get("/{tender_id}")
async def get_tender(tender_id: str):
    """
    Returns full tender detail including eligibility checklist, 
    amendment history, and competitor intel.
    """
    tender = await tenders_col().find_one(
        {"tender_id": tender_id},
        {"_id": 0, "page_snapshot": 0}  # exclude large snapshot field
    )
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender '{tender_id}' not found.")
    return tender


@router.get("/queue/drafts")
async def get_draft_queue(company_name: str, status: Optional[str] = "pending_approval", limit: int = 50):
    """
    Feature 1: Returns tenders queued for draft approval.
    """
    from backend.services.db import get_db
    db = get_db()
    
    query = {"company_name": company_name}
    if status:
        query["status"] = status
        
    cursor = db["draft_queue"].find(query, {"_id": 0}).sort("queued_at", -1).limit(limit)
    drafts = await cursor.to_list(length=limit)
    return {"drafts": drafts, "count": len(drafts)}


class DraftApproval(BaseModel):
    action: str  # "approve" | "reject" | "revision" | "waiver"

@router.post("/{tender_id}/approve-draft")
async def approve_draft(tender_id: str, company_name: str, req: DraftApproval):
    """
    Feature 1 & 4: Approves/rejects/revises a draft, or initiates a waiver.
    """
    from backend.services.db import get_db
    from datetime import datetime, timezone
    db = get_db()
    
    if req.action == "waiver":
        # Feature 4: HITL overridden gap. Force generate the draft.
        await db["draft_queue"].update_one(
            {"tender_id": tender_id, "company_name": company_name},
            {"$set": {"status": "pending_approval"}}
        )
        from backend.pipelines.auto_drafter import generate_draft_for_tender
        import asyncio
        asyncio.create_task(generate_draft_for_tender(tender_id, company_name))
        return {"status": "waiver_drafting_initiated"}
        
    new_status = "approved" if req.action == "approve" else ("rejected" if req.action == "reject" else "pending_approval")
    res = await db["draft_queue"].update_one(
        {"tender_id": tender_id, "company_name": company_name},
        {"$set": {"status": new_status, "approved_at": datetime.now(timezone.utc) if new_status == "approved" else None}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Draft not found in queue.")
        
    if req.action == "revision":
        from backend.pipelines.auto_drafter import regenerate_draft
        import asyncio
        asyncio.create_task(regenerate_draft(tender_id, company_name, reason="revision"))
        
    from backend.services.ws import async_publish_ws_event
    from backend.config import get_settings
    settings = get_settings()
    import asyncio
    asyncio.create_task(async_publish_ws_event(
        "DRAFT_STATE_CHANGED", 
        {"tender_id": tender_id, "new_status": new_status},
        settings.celery_broker_url
    ))
        
    return {"status": new_status}


class OutcomeRequest(BaseModel):
    outcome: str  # "won" | "lost" | "no_bid"

@router.post("/{tender_id}/outcome")
async def record_tender_outcome(tender_id: str, company_name: str, req: OutcomeRequest):
    """
    Feature 3: Records a bid outcome to feed the ML scoring loop.
    """
    from backend.services.outcome_tracker import record_outcome
    success = await record_outcome(tender_id, req.outcome, company_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record outcome.")
    return {"status": "recorded", "outcome": req.outcome}


@router.post("/{tender_id}/draft")
async def draft_proposal(tender_id: str, company_name: str):
    """Generates a markdown proposal outline using Fireworks.ai and the Knowledge Base."""
    tender = await tenders_col().find_one({"tender_id": tender_id}, {"_id": 0, "page_snapshot": 0})
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender '{tender_id}' not found.")
        
    from backend.services.db import users_col
    profile = await users_col().find_one({"company_name": company_name})
    if not profile:
        # Fallback for demo purposes
        profile = {"company_name": company_name, "sectors": [], "keywords": []}
        
    from backend.services.knowledge_base import search_knowledge_base
    kb_results = await search_knowledge_base(company_name, tender.get("title", ""))
    knowledge_text = "\n".join([f"- {res['text']}" for res in kb_results]) or "None found."

    # Record Audit Log for Zero-Trust Transparency
    if kb_results:
        from backend.services.db import audit_logs_col
        from datetime import datetime
        await audit_logs_col().insert_one({
            "company_name": company_name,
            "tender_title": tender.get("title", ""),
            "accessed_at": datetime.utcnow(),
            "reason": "AI Proposal Drafter retrieved knowledge to generate bid draft."
        })

    from backend.config import get_settings
    settings = get_settings()
    
    prompt = f"""You are an expert bid ghostwriter for {company_name}.
Write a professional 3-section concise proposal draft in Markdown format for the following tender.

TENDER:
Title: {tender.get("title")}
Description: {tender.get("description")}

COMPANY PROFILE:
{profile.get("sectors")}
{profile.get("keywords")}

OUR PRIVATE KNOWLEDGE (Use this to form the strategy):
{knowledge_text}

Format the output strictly in Markdown with these sections:
# Executive Summary
# Our Solution & Methodology
# Why Choose {company_name}
"""
    
    if not settings.fireworks_api_key:
        return {"proposal_markdown": f"# Executive Summary\nMock proposal for {tender.get('title')}.\n\n# Our Solution\nMock details leveraging {company_name}'s knowledge.\n\n# Why Choose {company_name}\nBecause we are highly qualified."}

    import httpx
    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.3,
    }
    
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post("https://api.fireworks.ai/inference/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Fireworks API error: {e}")
        content = f"# Executive Summary\nError generating proposal: {e}"
        
    return {"proposal_markdown": content}

class ChatRequest(BaseModel):
    message: str

@router.post("/{tender_id}/chat")
async def chat_with_agent(tender_id: str, company_name: str, req: ChatRequest):
    """Answers user questions about a specific tender using the Knowledge Base."""
    tender = await tenders_col().find_one({"tender_id": tender_id}, {"_id": 0, "page_snapshot": 0})
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender '{tender_id}' not found.")
        
    from backend.services.db import users_col
    profile = await users_col().find_one({"company_name": company_name})
    if not profile:
        profile = {"company_name": company_name, "agent_persona": ""}
        
    from backend.services.knowledge_base import search_knowledge_base
    kb_results = await search_knowledge_base(company_name, tender.get("title", ""))
    knowledge_text = "\n".join([f"- {res['text']}" for res in kb_results]) or "None found."

    from backend.config import get_settings
    settings = get_settings()
    
    persona = profile.get("agent_persona") or "You are a helpful bid analyst."
    
    prompt = f"""{persona}

You are evaluating this TENDER:
Title: {tender.get("title")}
Description: {tender.get("description")}
Our estimated win probability: {tender.get("our_probability", "Unknown")}%

OUR PRIVATE KNOWLEDGE:
{knowledge_text}

USER QUESTION: {req.message}

Provide a concise, analytical answer focusing entirely on the user's question. Do not restate the tender info unless necessary."""
    
    if not settings.fireworks_api_key:
        return {"reply": f"[Mock Agent]: I am answering your question '{req.message}' with mock insight about {tender.get('title')}."}

    import httpx
    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.5,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.fireworks.ai/inference/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Fireworks API error in chat: {e}")
        content = f"Error generating answer: {e}"
        
    return {"reply": content}

@router.post("/{tender_id}/submit")
async def submit_proposal_action(tender_id: str, company_name: str):
    """Executes the Auto-Submitter TinyFish Action Agent."""
    from backend.services.db import draft_queue_col, tenders_col
    from backend.agents.auto_submitter import auto_submit_proposal
    
    draft = await draft_queue_col().find_one({"tender_id": tender_id})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found in queue")
        
    tender = await tenders_col().find_one({"tender_id": tender_id})
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    result = await auto_submit_proposal(
        tender_id=tender_id,
        tender_title=tender.get("title", ""),
        company_name=company_name,
        draft_markdown=draft.get("draft_markdown", "")
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown submission error"))
        
    return result
