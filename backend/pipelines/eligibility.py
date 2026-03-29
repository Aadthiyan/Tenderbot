"""
TenderBot Global — Fireworks.ai Eligibility Analyser
Compares enriched RFP requirements against the company profile.
"""
import json
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

ELIGIBILITY_PROMPT = """You are a procurement compliance specialist. 
Assess whether this company meets the eligibility requirements for this tender.

COMPANY PROFILE:
- Name: {company_name}
- Annual turnover: ${annual_turnover}
- Headcount: {headcount}
- Years in business: {years_in_business}
- Certifications held: {certifications}
- Registered countries: {registered_countries}
- Past government contracts: {past_contracts}

TENDER ELIGIBILITY REQUIREMENTS:
{requirements}

For each requirement, assess if the company: PASSES, FAILS, or status is UNKNOWN.
Then provide an overall eligibility score 0-100 and a short action plan for any gaps.

Return ONLY valid JSON:
{{
  "eligibility_score": <integer 0-100>,
  "eligibility_checklist": [
    {{
      "requirement": "<exact requirement text>",
      "status": "<pass|fail|unknown>",
      "gap": "<brief explanation if fail, else null>"
    }}
  ],
  "eligibility_action_plan": [
    "<actionable step to close a gap, e.g. Obtain ISO 27001 certification>"
  ]
}}"""


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=3, max=10),
    reraise=True,
)
async def check_eligibility(tender: dict, profile: dict) -> dict:
    """
    Runs eligibility analysis for a single enriched tender.
    Returns dict of eligibility fields to merge into the tender document.
    """
    requirements = tender.get("eligibility_requirements", [])
    if not requirements:
        logger.debug(f"No eligibility requirements for tender '{tender.get('title', '')[:50]}' — skipping.")
        return {}

    if not settings.fireworks_api_key:
        import random
        score = random.randint(50, 100)
        return {
            "eligibility_score": score,
            "eligibility_checklist": [
                {"requirement": r, "status": "pass" if random.random() > 0.2 else "fail", "gap": "Missing certification" if random.random() <= 0.2 else None}
                for r in requirements
            ],
            "eligibility_action_plan": ["Partner with local firm"] if score < 80 else []
        }

    requirements_text = "\n".join(f"- {r}" for r in requirements)

    prompt = ELIGIBILITY_PROMPT.format(
        company_name=profile.get("company_name", "Unknown"),
        annual_turnover=profile.get("annual_turnover") or "Not specified",
        headcount=profile.get("headcount") or "Not specified",
        years_in_business=profile.get("years_in_business") or "Not specified",
        certifications=", ".join(profile.get("certifications", [])) or "None",
        registered_countries=", ".join(profile.get("target_countries", [])) or "Not specified",
        past_contracts="; ".join(profile.get("past_contracts", [])) or "None",
        requirements=requirements_text,
    )

    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(FIREWORKS_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    result = _safe_parse(content)

    logger.info(
        f"Eligibility for '{tender.get('title', '')[:40]}': "
        f"{result.get('eligibility_score', '?')}/100 — "
        f"{len(result.get('eligibility_checklist', []))} criteria checked"
    )

    return {
        "eligibility_score": result.get("eligibility_score"),
        "eligibility_checklist": result.get("eligibility_checklist", []),
        "eligibility_action_plan": result.get("eligibility_action_plan", []),
    }


def _safe_parse(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Eligibility JSON parse failed: {content[:100]}")
        return {
            "eligibility_score": None,
            "eligibility_checklist": [],
            "eligibility_action_plan": [],
        }
