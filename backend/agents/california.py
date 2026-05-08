"""
California State Procurement Agent
Searches California Department of General Services (DGS) and state procurement database
Uses TinyFish to navigate CaleProcure and related databases
"""
import asyncio
import logging
import httpx
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)

async def run_california_agent(keywords: list[str]) -> list[dict]:
    """
    Search California state procurement opportunities including:
    - CaleProcure (official state procurement database)
    - State education procurement (UC, CSU, K-12)
    - Infrastructure and transportation contracts
    - Healthcare and human services contracts
    """
    
    logger.info(f"🔍 California Procurement Agent searching for: {keywords}")
    settings = get_settings()
    
    if not settings.tinyfish_api_key:
        logger.warning("No TinyFish API key configured")
        return []
    
    opportunities = []
    
    try:
        # Use TinyFish to navigate California procurement databases
        goal = f"""
        Search California state procurement opportunities related to: {', '.join(keywords)}
        
        Look for opportunities on:
        1. CaleProcure.ca.gov (main state procurement database)
        2. California Department of General Services (DGS) contracting
        3. Caltrans contracts (transportation/infrastructure)
        4. California Energy Commission (CEC) contracts
        5. University of California (UC) procurement
        6. California State University (CSU) procurement
        7. Department of Water Resources (DWR) projects
        
        Extract opportunities with:
        - Title/Description
        - Department/Agency (e.g., CalTrans, CEC, UC Davis, etc.)
        - URL/Link to posting
        - Deadline (if visible)
        - Budget/Contract value (if available)
        - Type (RFP, RFQ, Bid, Grant, etc.)
        
        Return in markdown table format:
        Title | Department | URL | Deadline | Budget | Type
        """
        
        url = "https://api.tinyfish.ai/v1/navigate"
        headers = {
            "Authorization": f"Bearer {settings.tinyfish_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "goal": goal,
            "url": "https://caleprocure.ca.gov/",
            "mode": "auto"
        }
        
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"California API error: {response.status_code}")
                return []
            
            # Parse SSE response
            for line in response.text.split('\n'):
                if line.startswith('data:'):
                    try:
                        import json
                        event_data = json.loads(line[5:].strip())
                        
                        if event_data.get('type') == 'COMPLETE':
                            result = event_data.get('result', {})
                            if isinstance(result, dict):
                                result_text = result.get('result', '')
                            else:
                                result_text = str(result)
                            
                            opportunities.extend(
                                _parse_california_results(result_text)
                            )
                    except Exception as e:
                        logger.debug(f"Error parsing event: {e}")
                        continue
    
    except asyncio.TimeoutError:
        logger.error("California Agent timeout")
    except Exception as e:
        logger.error(f"California Agent error: {e}")
    
    logger.info(f"✅ California Agent found {len(opportunities)} opportunities")
    return opportunities


def _parse_california_results(result_text: str) -> list[dict]:
    """Parse markdown table results from California procurement search"""
    opportunities = []
    
    lines = result_text.split('\n')
    
    for line in lines:
        if '|' not in line or 'Title' in line or '---' in line:
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue
        
        try:
            title, department, url, deadline, budget, opp_type = parts[1:7]
            
            if not title or not department:
                continue
            
            # Clean URL
            if url.startswith('[') and '](' in url:
                url = url.split('](')[1].rstrip(')')
            
            # Parse deadline
            deadline_str = deadline.strip() if deadline and deadline.lower() != 'n/a' else None
            
            # Parse budget
            budget_str = budget.strip() if budget and budget.lower() not in ['n/a', 'varies'] else None
            
            opportunity = {
                'title': title,
                'organization': f"California - {department}",
                'opportunity_type': opp_type if opp_type and opp_type.lower() != 'n/a' else 'State Contract',
                'url': url,
                'deadline': deadline_str,
                'estimated_value': budget_str,
                'description': f"California state procurement opportunity in {department}: {title}",
                'source': 'California State'
            }
            
            opportunities.append(opportunity)
        
        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing California result: {e}")
            continue
    
    return opportunities


if __name__ == "__main__":
    import asyncio
    results = asyncio.run(run_california_agent(
        keywords=["technology", "software", "cloud"]
    ))
    print(f"Found {len(results)} opportunities")
    for opp in results[:3]:
        print(f"  - {opp['title']} ({opp['organization']})")
