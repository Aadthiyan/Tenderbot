"""
Local Government Procurement Agent
Searches city and county contracts from major metros (NYC, LA, Chicago, etc.)
Uses TinyFish to search local government procurement databases
"""
import asyncio
import logging
import httpx
from backend.config import get_settings

logger = logging.getLogger(__name__)

async def run_local_government_agent(keywords: list[str]) -> list[dict]:
    """
    Search local government (city/county) procurement opportunities from major cities:
    - New York City (NYC)
    - Los Angeles (LA)
    - Chicago (IL)
    - Houston (TX)
    - Phoenix (AZ)
    - Philadelphia (PA)
    - San Antonio (TX)
    - San Diego (CA)
    - Dallas (TX)
    - San Jose (CA)
    """
    
    logger.info(f"🔍 Local Government Agent searching for: {keywords}")
    settings = get_settings()
    
    if not settings.tinyfish_api_key:
        logger.warning("No TinyFish API key configured")
        return []
    
    opportunities = []
    
    try:
        goal = f"""
        Search local government (city and county) procurement opportunities from major US cities related to: {', '.join(keywords)}
        
        Search for contracts in these cities/systems:
        1. New York City - NYC Department of Citywide Administrative Services (DCAS)
        2. Los Angeles - LA Department of General Services
        3. Chicago - City of Chicago procurement
        4. Houston - City of Houston Purchasing
        5. Phoenix - City of Phoenix Procurement
        6. Philadelphia - City of Philadelphia Procurement
        7. San Antonio - City Purchasing
        8. San Diego - City of San Diego Contracts
        9. Dallas - Business Services procurement
        10. Los Angeles County - County Contracts
        
        Extract opportunities with:
        - Project/Contract name and description
        - City/County and Department
        - URL to full posting
        - Bid deadline (if visible)
        - Contract value/budget (if available)
        - Type (RFP, RFQ, IFB, Service Contract, Goods, etc.)
        
        Return results in markdown table:
        Title | City/County | Department | URL | Deadline | Budget | Type
        """
        
        url = "https://api.tinyfish.ai/v1/navigate"
        headers = {
            "Authorization": f"Bearer {settings.tinyfish_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "goal": goal,
            "url": "https://www.google.com/",  # Use Google as starting point to search multiple cities
            "mode": "auto"
        }
        
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Local Government API error: {response.status_code}")
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
                                _parse_local_government_results(result_text)
                            )
                    except Exception as e:
                        logger.debug(f"Error parsing event: {e}")
                        continue
    
    except asyncio.TimeoutError:
        logger.error("Local Government Agent timeout")
    except Exception as e:
        logger.error(f"Local Government Agent error: {e}")
    
    logger.info(f"✅ Local Government Agent found {len(opportunities)} opportunities")
    return opportunities


def _parse_local_government_results(result_text: str) -> list[dict]:
    """Parse markdown table results from local government search"""
    opportunities = []
    
    lines = result_text.split('\n')
    
    for line in lines:
        if '|' not in line or 'Title' in line or '---' in line:
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue
        
        try:
            title, city_county, department, url, deadline, budget, opp_type = parts[1:8]
            
            if not title or not city_county:
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
                'organization': f"{city_county} - {department}",
                'opportunity_type': opp_type if opp_type and opp_type.lower() != 'n/a' else 'Municipal Contract',
                'url': url,
                'deadline': deadline_str,
                'estimated_value': budget_str,
                'description': f"Local government procurement ({city_county}): {title}",
                'source': 'Local Government'
            }
            
            opportunities.append(opportunity)
        
        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing Local Government result: {e}")
            continue
    
    return opportunities


if __name__ == "__main__":
    import asyncio
    results = asyncio.run(run_local_government_agent(
        keywords=["technology", "IT services", "infrastructure"]
    ))
    print(f"Found {len(results)} opportunities")
    for opp in results[:3]:
        print(f"  - {opp['title']} ({opp['organization']})")
