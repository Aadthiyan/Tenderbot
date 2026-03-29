"""
TenderBot Global — Subcontractor Radar (Phase 5.3)
Autonomously searches known Prime Contractor portals or teaming boards 
for explicitly listed SME sub-bidding opportunities using TinyFish.
"""
import json
import logging
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings
from backend.agents.portal_configs import SUBCONTRACTOR_RADAR_GOAL

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"

# Known prime hubs or public teaming opportunity boards
# In production, this can parse dynamically from `top_competitors`
PRIME_HUBS = [
    "https://lockheedmartin.com/en-us/suppliers/opportunities.html",
    "https://www.boeing.com/company/about-bca/supplier-management/",
]

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=3, max=10), reraise=True)
async def scan_for_sub_opportunities(profile: dict) -> list[dict]:
    """
    Scans predefined hubs for sub-bidding opportunities matching the user's profile.
    """
    keywords = profile.get("keywords", [])
    kw = keywords[0] if keywords else "technology"
    
    if not settings.tinyfish_api_key:
        await asyncio.sleep(2)
        return [
            {
                "prime_contractor": "Lockheed Martin",
                "project_title": "Navy Secure Network Redesign",
                "sub_role_needed": "Zero Trust Architect - Clearance Required",
                "contact_info": "supplier.teaming@lmco.proxy.mock",
                "deadline": "2026-06-15"
            },
            {
                "prime_contractor": "Booz Allen Hamilton",
                "project_title": "DHS Cloud Infrastructure Build",
                "sub_role_needed": "AWS DevOps Subcontractor",
                "contact_info": "teaming_partner_intake@bah.mock",
                "deadline": "2026-05-30"
            },
            {
                "prime_contractor": "BAE Systems",
                "project_title": "NextGen Avionics Diagnostics",
                "sub_role_needed": "Hardware Quality Assurance Tester",
                "contact_info": "https://baesystems.suppliers.mock/apply",
                "deadline": "2026-07-01"
            }
        ]

    tasks = [_scrape_hub(hub_url, kw) for hub_url in PRIME_HUBS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_opportunities = []
    for res in results:
        if isinstance(res, list):
            all_opportunities.extend(res)
        else:
            logger.warning(f"Subcontractor scraping failed: {res}")
            
    return all_opportunities

async def _scrape_hub(url: str, kw: str) -> list[dict]:
    goal = SUBCONTRACTOR_RADAR_GOAL.format(url=url, kw=kw)
    headers = {
        "Authorization": f"Bearer {settings.tinyfish_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    payload = {"url": url, "goal": goal, "output_format": "json"}
    
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
                            result_data = c.get("sub_opportunities", [])
                            break
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"Failed to scrape Subcontractor Hub {url}: {e}")
        
    return result_data
