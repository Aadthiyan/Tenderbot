"""
TenderBot Global — /briefing Router
Generate and serve today's ElevenLabs voice briefing.
"""
from fastapi import APIRouter, HTTPException
import logging
from backend.services.db import tenders_col
from backend.services.voice_briefing import generate_voice_briefing

router = APIRouter(prefix="/briefing", tags=["Briefing"])
logger = logging.getLogger(__name__)

# Basic memory cache for today's briefing
LATEST_BRIEFING = None


@router.post("/generate")
async def trigger_briefing_generation():
    """
    Manually forces the generation of a new voice briefing.
    Queries top active tenders, generates script, and calls ElevenLabs TTS.
    Returns the script and URL to the audio file.
    """
    global LATEST_BRIEFING

    cursor = tenders_col().find(
        {"status": "active"},
        {"_id": 0, "page_snapshot": 0}
    ).sort([("relevance_score", -1), ("days_until_deadline", 1)]).limit(10)

    tenders = await cursor.to_list(length=10)
    
    result = await generate_voice_briefing(tenders, company_name="Agile Defend IT")
    
    LATEST_BRIEFING = result
    return result


@router.get("/latest")
async def get_latest_briefing():
    """
    Returns the most recently generated briefing data (script + audio URL).
    If none exists in memory, attempts to generate one.
    """
    global LATEST_BRIEFING
    if not LATEST_BRIEFING:
        # Fallback to generation if missing
        LATEST_BRIEFING = await trigger_briefing_generation()
        
    return LATEST_BRIEFING


# ── Auto-Fill (legacy location) ────────────────────────────────────────────────
from backend.models import AutoFillRequest, AutoFillResponse

@router.post("/auto-fill", response_model=AutoFillResponse)
async def auto_fill_application(req: AutoFillRequest):
    """
    Triggers the TinyFish Form-Fill Agent on a tender's application page.
    Maps company profile fields → form inputs. Does NOT submit the form.
    """
    from backend.services.db import tenders_col, users_col
    from backend.agents.form_fill import run_form_fill

    # Fetch tender and user
    tender = await tenders_col().find_one({"tender_id": req.tender_id}, {"_id": 0})
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender '{req.tender_id}' not found.")

    user = await users_col().find_one({"_id": req.user_id}, {"_id": 0}) or \
           await users_col().find_one({"company_name": req.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{req.user_id}' not found.")

    result = await run_form_fill(
        tender_url=tender["raw_url"],
        profile=user
    )

    return AutoFillResponse(
        fields_filled=result.get("fields_filled", []),
        fields_remaining=result.get("fields_remaining", []),
        completion_pct=result.get("completion_pct", 0.0),
    )
