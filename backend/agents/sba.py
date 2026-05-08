"""
SBA Contracting Agent
Searches Small Business Administration opportunities and set-asides
Uses TinyFish to navigate SBA database and API endpoints
"""
import asyncio
import logging
import sse_client
import httpx
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)

async def run_sba_agent(keywords: list[str]) -> list[dict]:
    """
    Search SBA opportunities including:
    - Set-asides for small businesses
    - HUBZone certified contracts
    - Women-owned business contracts
    - Veteran business set-asides
    """
    
    logger.info(f"🔍 SBA Agent searching for: {keywords}")
    settings = get_settings()
    
    if not settings.tinyfish_api_key:
        logger.warning("No TinyFish API key configured")
        return []
    
    opportunities = []
    
    try:
        # Use TinyFish to navigate SBA contracting database
        goal = f"""
        Search SBA.gov for small business contracting opportunities related to: {', '.join(keywords)}
        
        Look for:
        1. Set-asides for small businesses on the SBA contracting page
        2. HUBZone certified business opportunities
        3. Women-owned small business (WOSB) contracts  
        4. Veteran-owned small business (VOSB) contracts
        5. Disadvantaged business enterprise (DBE) contracts
        
        Extract opportunities with:
        - Title/Description
        - Agency/Department
        - Link to full posting
        - Deadline (if visible)
        - Contract value (if available)
        - Type (Set-aside, HUBZone, WOSB, VOSB, etc.)
        
        Return results in markdown table format with columns:
        Title | Agency | URL | Deadline | Value | Type
        """
        
        url = "https://api.tinyfish.ai/v1/navigate"
        headers = {
            "Authorization": f"Bearer {settings.tinyfish_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "goal": goal,
            "url": "https://www.sba.gov/",
            "mode": "auto"
        }
        
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"SBA API error: {response.status_code}")
                return []
            
            # Parse SSE response
            for line in response.text.split('\n'):
                if line.startswith('data:'):
                    try:
                        import json
                        event_data = json.loads(line[5:].strip())
                        
                        if event_data.get('type') == 'COMPLETE':
                            # Extract results from completion event
                            result = event_data.get('result', {})
                            if isinstance(result, dict):
                                result_text = result.get('result', '')
                            else:
                                result_text = str(result)
                            
                            # Parse markdown table
                            opportunities.extend(
                                _parse_sba_results(result_text, keywords)
                            )
                    except Exception as e:
                        logger.debug(f"Error parsing event: {e}")
                        continue
    
    except asyncio.TimeoutError:
        logger.error("SBA Agent timeout")
    except Exception as e:
        logger.error(f"SBA Agent error: {e}")
    
    logger.info(f"✅ SBA Agent found {len(opportunities)} opportunities")
    return opportunities


def _parse_sba_results(result_text: str, keywords: list[str]) -> list[dict]:
    """Parse markdown table results from SBA search"""
    opportunities = []
    
    # Look for markdown table format: | Title | Agency | URL | Deadline | Value | Type |
    lines = result_text.split('\n')
    
    for i, line in enumerate(lines):
        if '|' not in line or 'Title' in line or '---' in line:
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue
        
        try:
            title, agency, url, deadline, value, opp_type = parts[1:7]
            
            # Skip empty rows
            if not title or not agency:
                continue
            
            # Clean up URL
            if url.startswith('[') and '](' in url:
                # Extract from markdown link format [text](url)
                url = url.split('](')[1].rstrip(')')
            
            # Parse deadline
            deadline_str = deadline.strip() if deadline and deadline.lower() != 'n/a' else None
            
            # Parse value
            value_str = value.strip() if value and value.lower() not in ['n/a', 'varies'] else None
            
            opportunity = {
                'title': title,
                'organization': agency,
                'opportunity_type': opp_type if opp_type and opp_type.lower() != 'n/a' else 'Small Business Contract',
                'url': url,
                'deadline': deadline_str,
                'estimated_value': value_str,
                'description': f"SBA Small Business opportunity: {opp_type}. {title}",
                'source': 'SBA'
            }
            
            opportunities.append(opportunity)
        
        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing SBA result row: {e}")
            continue
    
    return opportunities


if __name__ == "__main__":
    import asyncio
    results = asyncio.run(run_sba_agent(
        keywords=["cloud", "cybersecurity", "software"]
    ))
    print(f"Found {len(results)} opportunities")
    for opp in results[:3]:
        print(f"  - {opp['title']} ({opp['organization']})")
