"""
TenderBot — RFP Researcher Pipeline
Auto-fetches and analyses RFP documents on discovery, flags knowledge gaps.
"""
import logging
from datetime import datetime, timezone
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"


async def research_tender(tender: dict, user_profile: dict) -> dict:
    """
    Feature 2: Self-Research on Discovery.
    Fetches tender RFP text, extracts requirements, cross-checks knowledge base,
    and flags gaps where company data is missing.
    Returns dict with: requirements, gaps, research_summary, research_confidence
    """
    import httpx
    from backend.services.knowledge_base import search_knowledge_base

    tender_id = tender.get("tender_id", "")
    company_name = user_profile.get("company_name", "")
    title = tender.get("title", "")

    # Search company KB for relevant context
    try:
        kb_results = await search_knowledge_base(company_name, title)
        kb_text = "\n".join([f"- {r['text'][:300]}" for r in kb_results]) if kb_results else "None available."
    except Exception as e:
        logger.warning(f"KB search failed during research for {tender_id}: {e}")
        kb_text = "None available."

    description = tender.get("description") or tender.get("page_snapshot") or "No description available."
    description = description[:2000]  # cap to avoid token overflow

    prompt = f"""You are a bid analyst reviewing a government tender.

TENDER: {title}
AGENCY: {tender.get('agency', 'Unknown')}
DESCRIPTION: {description}

COMPANY KNOWLEDGE BASE:
{kb_text}

Tasks:
1. Extract the TOP 5 key requirements from this tender as a JSON list under "requirements"
2. Identify any requirement gaps where the company knowledge base has NO evidence — list as "gaps"
3. Write a 2-sentence "research_summary" of what this tender is looking for
4. Rate "confidence" from 0-100 on how well the company knowledge matches this tender

Respond ONLY as valid JSON:
{{
  "requirements": ["req1", "req2", "req3", "req4", "req5"],
  "gaps": ["gap1", "gap2"],
  "research_summary": "...",
  "confidence": 75
}}"""

    if not settings.fireworks_api_key:
        return {
            "requirements": ["Budget compliance", "Technical capability", "Local presence", "Experience", "Certifications"],
            "gaps": ["No evidence of local presence in knowledge base"],
            "research_summary": f"This tender by {tender.get('agency')} seeks services in: {title}.",
            "research_confidence": 50,
        }

    headers = {"Authorization": f"Bearer {settings.fireworks_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.1,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(FIREWORKS_URL, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

        # Parse JSON from response
        import json, re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "requirements": data.get("requirements", []),
                "gaps": data.get("gaps", []),
                "research_summary": data.get("research_summary", ""),
                "research_confidence": data.get("confidence", 0),
                "researched_at": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        logger.warning(f"RFP research failed for {tender_id}: {e}")

    return {
        "requirements": [],
        "gaps": [],
        "research_summary": "Research could not be completed.",
        "research_confidence": 0,
    }
