"""
TenderBot Global — Fireworks.ai Relevance Scorer
Rates each tender 0-100 against the company profile using Llama 3.1 70B.
"""
import json
import logging
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings
from backend.services.knowledge_base import search_knowledge_base
from backend.services.outcome_tracker import get_win_rate

logger = logging.getLogger(__name__)
settings = get_settings()

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

SCORING_PROMPT = """You are a senior procurement analyst representing {company_name}. 
{agent_persona}
Score how well this tender matches the company profile.

COMPANY PROFILE:
- Name: {company_name}
- Sectors: {sectors}
- Keywords: {keywords}
- Budget range: ${min_value} – ${max_value} USD
- Target countries: {countries}
- Certifications held: {certifications}

TENDER:
- Title: {title}
- Agency: {agency}
- Country: {country}
- Estimated value: ${value}
- Category code: {category_code}
- Description: {description}

INTERNAL COMPANY KNOWLEDGE (RETRIEVED):
{knowledge}

Scoring rules:
- 80-100: Strong match — sectors align, budget fits, geography matches, high chance of eligibility
- 60-79: Good match — most criteria met, some gaps
- 40-59: Partial match — sector overlap but significant gaps (value, geography, or eligibility)
- 20-39: Weak match — limited relevance
- 0-19: No match — wrong sector, geography, or far outside budget

Return ONLY valid JSON with no explanation:
{{
  "score": <integer 0-100>,
  "match_reasons": ["<reason1>", "<reason2>"],
  "disqualifiers": ["<reason if score low, else empty list>"],
  "action": "<apply_now|watch|skip>",
  "our_win_probability": <integer 0-100>,
  "winning_strategy": "<1-2 sentence strategy to differentiate from competitors>",
  "top_competitors": ["<likely competitor 1>", "<likely competitor 2>"]
}}

Rules for action:
- apply_now: score >= 75
- watch: score >= 50 and < 75
- skip: score < 50"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def score_tender(tender: dict, profile: dict) -> dict:
    """
    Calls Fireworks.ai to score a single tender against the company profile.
    Returns tender dict with scoring fields added.
    """
    if not settings.fireworks_api_key:
        import random
        score = random.randint(40, 95)
        tender["relevance_score"] = score
        tender["match_reasons"] = ["Mock Reason 1"]
        tender["disqualifiers"] = [] if score > 75 else ["Mock Disqualifier"]
        tender["action"] = "apply_now" if score >= 75 else ("watch" if score >= 50 else "skip")
        tender["our_win_probability"] = random.randint(10, 90)
        tender["winning_strategy"] = "Leverage ISO 9001 and past relationships."
        tender["top_competitors"] = ["Incumbent Vendor", "Large Systems Integrator"]
        return tender

    # RETRIEVE COMPANY-SPECIFIC KNOWLEDGE
    kb_results = await search_knowledge_base(profile.get("company_name", ""), tender.get("title", ""))
    knowledge_text = "\n".join([f"- {res['text']}" for res in kb_results]) or "None found."
    
    # Record Audit Log for Zero-Trust Transparency
    if True: # Make sure visual telemetry always works in mock or production
        from backend.services.db import audit_logs_col
        from datetime import datetime
        await audit_logs_col().insert_one({
            "company_name": profile.get("company_name", ""),
            "tender_title": tender.get("title", ""),
            "accessed_at": datetime.utcnow(),
            "reason": "AI Scorer retrieved knowledge to evaluate tender relevance." if kb_results else "AI Scorer analyzed tender (Fallback Mode)."
        })
    
    persona = profile.get("agent_persona") or ""
    if persona:
        persona = f"AGENT PERSONA INSTRUCTIONS:\n{persona}\n"

    prompt = SCORING_PROMPT.format(
        company_name=profile.get("company_name", "Unknown"),
        agent_persona=persona,
        sectors=", ".join(profile.get("sectors", [])),
        keywords=", ".join(profile.get("keywords", [])),
        min_value=profile.get("min_value", 0),
        max_value=profile.get("max_value", 10_000_000),
        countries=", ".join(profile.get("target_countries", [])),
        certifications=", ".join(profile.get("certifications", [])) or "None",
        title=tender.get("title", "")[:200],
        agency=tender.get("agency", "")[:100],
        country=tender.get("country", ""),
        value=tender.get("estimated_value") or "Not specified",
        category_code=tender.get("category_code") or "Not specified",
        description=(tender.get("description") or "")[:500],
        knowledge=knowledge_text
    )

    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.1,  # Low temperature for consistent scoring
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(FIREWORKS_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    result = _safe_parse_json(content)

    # Merge scoring results into tender
    base_score = int(result.get("score", 50))
    
    # Apply historical win-rate feedback loop (Feature 3)
    try:
        adjustment_factor = await get_win_rate(
            agency=tender.get("agency"),
            category_code=tender.get("category_code"),
            company_name=profile.get("company_name", "Unknown")
        )
        # Factor is -1.0 to 1.0. Max adjustment is ±10 points.
        adjustment_points = int(adjustment_factor * 10)
        final_score = max(0, min(100, base_score + adjustment_points))
        
        if adjustment_points != 0:
            logger.info(f"Feedback loop adjusted score for '{tender.get('title')[:30]}': {base_score} -> {final_score}")
    except Exception as e:
        logger.warning(f"Win-rate adjustment failed: {e}")
        final_score = base_score

    tender["relevance_score"] = final_score
    tender["match_reasons"] = result.get("match_reasons", [])
    tender["disqualifiers"] = result.get("disqualifiers", [])
    tender["action"] = result.get("action", "watch")
    tender["our_win_probability"] = float(result.get("our_win_probability", 50.0))
    tender["winning_strategy"] = result.get("winning_strategy", "Standard proposal required.")
    tender["top_competitors"] = result.get("top_competitors", ["Unknown"])


    logger.debug(
        f"Scored '{tender.get('title', '')[:50]}': "
        f"{tender['relevance_score']}/100 → {tender['action']}"
    )

    return tender


def _safe_parse_json(content: str) -> dict:
    """Parse LLM JSON output safely, with fallback defaults."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse scoring JSON: {content[:100]}")
        return {"score": 50, "match_reasons": [], "disqualifiers": [], "action": "watch"}
