"""
TenderBot Global — Competitor Bid Intelligence
Phase 5.1: Extracts past awards via TinyFish, then uses Fireworks LLM to estimate win probabilities.
"""
import json
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings
from backend.agents.portal_configs import COMPETITOR_INTEL_GOAL

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

INTEL_PROMPT = """You are a highly skilled government contracting intelligence analyst.
Analyze these past contract awards against the target RFP and our company profile.

COMPANY PROFILE:
- Name: {company_name}
- Turnover: ${annual_turnover}
- Geography: {countries}
- Past Contracts: {past_contracts}

TARGET RFP / TENDER:
- Title: {title}
- Agency: {agency}
- Value: ${value}
- Relevance Score: {relevance_score}/100

PAST AWARDS (COMPETITORS):
{past_awards_text}

Calculate the following:
1. our_probability: Integer 0-100 indicating our exact percentage chance of winning based on the matching relevance and competitive landscape.
2. smb_win_rate: Integer 0-100 estimating the historical win frequency for Small/Medium Businesses on this type of contract.
3. top_competitors: Array of string names of the strongest incumbent or past competitor.

Return ONLY valid JSON:
{{
  "our_probability": 72,
  "smb_win_rate": 45,
  "top_competitors": ["Competitor A", "Competitor B"],
  "intel_summary": "1-2 sentence tactical summary of the competitive landscape."
}}
"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=3, max=10), reraise=True)
async def analyze_competitors(tender: dict, profile: dict) -> dict:
    """
    1. Scrape past awards using TinyFish.
    2. Analyze likelihood of winning using Fireworks LLM.
    """
    past_awards = await _fetch_past_awards(tender)
    
    if not settings.fireworks_api_key:
        import random
        base_prob = tender.get("relevance_score", 50)
        return {
            "our_probability": max(5, base_prob - random.randint(5, 20)),
            "smb_win_rate": random.randint(20, 60),
            "top_competitors": [aw.get("winner_name", "Incumbent Corp") for aw in past_awards[:3]] or ["GlobalTech Inc.", "Federal Solutions LLC"],
            "intel_summary": "Mock competitor intelligence based on past awards."
        }

    awards_text = "\n".join([f"- {a.get('winner_name')} won ${a.get('award_value')} on {a.get('award_date')}" for a in past_awards])
    if not awards_text:
        awards_text = "No direct past awards found in public databases."

    prompt = INTEL_PROMPT.format(
        company_name=profile.get("company_name", "Unknown"),
        annual_turnover=profile.get("annual_turnover", "Unknown"),
        countries=", ".join(profile.get("target_countries", [])),
        past_contracts="; ".join(profile.get("past_contracts", [])),
        title=tender.get("title", ""),
        agency=tender.get("agency", ""),
        value=tender.get("estimated_value", 0),
        relevance_score=tender.get("relevance_score", 50),
        past_awards_text=awards_text
    )

    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.fireworks_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(FIREWORKS_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    top_competitors = []
    intel_summary = "Analysis failed."
    our_prob = None
    smb_win = None
    
    try:
        result = json.loads(content)
        our_prob = int(result.get("our_probability", 0))
        smb_win = int(result.get("smb_win_rate", 0))
        top_competitors = result.get("top_competitors", [])
        intel_summary = result.get("intel_summary", "")
    except json.JSONDecodeError:
        pass

    # Feature 2: Multi-Step Competitor Recon Agent (TinyFish exploration)
    competitor_recon = []
    if top_competitors and settings.tinyfish_api_key:
        import asyncio
        from backend.services.agent_run_logger import log_agent_run
        await log_agent_run("ResearcherAgent", "running", f"Spinning up sub-agents to web-scape competitors: {', '.join(top_competitors[:2])}", 0)
        
        recon_tasks = [_scrape_competitor_website(comp) for comp in top_competitors[:2]]  # Limit to top 2 to save time
        recon_results = await asyncio.gather(*recon_tasks, return_exceptions=True)
        
        for res in recon_results:
            if isinstance(res, dict) and "summary" in res:
                competitor_recon.append(f"{res['name']}: {res['summary']}")
                
        if competitor_recon:
            intel_summary += "\n\nDeep Recon:\n" + "\n".join(competitor_recon)

    return {
        "our_probability": our_prob,
        "smb_win_rate": smb_win,
        "top_competitors": top_competitors,
        "intel_summary": intel_summary,
        "competitor_recon_data": competitor_recon
    }


async def _scrape_competitor_website(competitor_name: str) -> dict:
    """Uses TinyFish to perform open-ended web research on a specific competitor."""
    url = f"https://www.google.com/search?q={competitor_name.replace(' ', '+')}+government+contracting"
    goal = f"""You are researching the competitor '{competitor_name}'. 
Click on their official main website from the search results. 
Scan their homepage or 'Services' page. 
Extract a 2-sentence summary of their primary technology stack and value proposition. 
Return JSON: {{"name": "{competitor_name}", "summary": "..."}}"""
    
    headers = {
        "Authorization": f"Bearer {settings.tinyfish_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json"
    }
    
    result_data = {"name": competitor_name, "summary": "Search failed or timed out."}
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            async with client.stream("POST", f"{TINYFISH_BASE_URL}/agent", headers=headers, json=payload) as response:
                if response.status_code != 200:
                    return result_data
                async for line in response.aiter_lines():
                    if not line.startswith("data:"): continue
                    raw = line[5:].strip()
                    if raw == "[DONE]": break
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "result":
                            c = event.get("content", "{}")
                            import ast
                            if isinstance(c, str):
                                try:
                                    c = json.loads(c)
                                except:
                                    pass
                            if isinstance(c, dict) and "summary" in c:
                                result_data = c
                            break
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"Competitor recon failed for {competitor_name}: {e}")
        
    return result_data


async def _fetch_past_awards(tender: dict) -> list[dict]:
    # Mock data if TinyFish key is absent
    if not settings.tinyfish_api_key:
        import asyncio
        import random
        await asyncio.sleep(1)
        if random.random() > 0.3:
            return [
                {"winner_name": "Lockheed Martin IT", "award_value": 45000000, "award_date": "2021-05-12"},
                {"winner_name": "Booz Allen Hamilton", "award_value": 31000000, "award_date": "2023-11-20"}
            ]
        return []

    # Simple keyword search on a generic award database like FPDS/USAspending
    kw = tender.get("category_code") or tender.get("agency") or "IT services"
    url = f"https://www.usaspending.gov/search/?keyword={kw}"
    goal = COMPETITOR_INTEL_GOAL.format(url=url, kw=kw)
    
    headers = {
        "Authorization": f"Bearer {settings.tinyfish_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json"
    }
    
    result_data = []
    try:
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream("POST", f"{TINYFISH_BASE_URL}/agent", headers=headers, json=payload) as response:
                if response.status_code != 200:
                    return result_data
                async for line in response.aiter_lines():
                    if not line.startswith("data:"): continue
                    raw = line[5:].strip()
                    if raw == "[DONE]": break
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "result":
                            c = event.get("content", "{}")
                            if isinstance(c, str):
                                c = json.loads(c)
                            result_data = c.get("past_awards", [])
                            break
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"Past awards scrape failed: {e}")
        
    return result_data
