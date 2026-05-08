"""
Debug script: Single SAM.gov agent test with full event dumping
"""
import asyncio
import httpx
import json
import logging
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.config import get_settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = get_settings()
TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"

async def test_single_portal_debug():
    print("=" * 80)
    print("TESTING SINGLE SAM.GOV PORTAL WITH FULL DEBUG OUTPUT")
    print("=" * 80)
    
    keywords = ["cybersecurity", "cloud", "software"]
    keyword_str = " ".join(keywords[:5])
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"https://sam.gov/search/?index=opp&q={keyword_str}&dateRange=custom&startDate={thirty_days_ago}&endDate={today}&status=active"
    
    goal = f"""
        You are searching SAM.gov for active US government procurement opportunities.
        Search keyword: '{keyword_str}'.
        
        Steps:
        1. If a cookie consent or popup warning you about accessing a US Government Information System appears, accept/dismiss it immediately.
        2. Wait for the main search results table/list to render.
        3. Verify the filter for 'Status: Active' is applied via the left sidebar. If not, apply it.
        4. For each result on the first 2 pages, extract:
           - title: the opportunity title
           - agency: the issuing sub-tier and main agency name
           - naics_code: NAICS code if visible
           - deadline: response/close date (Due date)
           - award_value: estimated contract value if shown
           - place_of_performance: primary location (state/city)
           - solicitation_number: the solicitation/notice ID
           - description: brief description or synopsis (first 300 chars)
           - url: the direct link to the opportunity (very important)
        5. Navigate to the next page using the pagination controls at the bottom, and repeat until you have scanned 2 pages.
        6. Return the extracted data as a pure JSON array. Each element must contain all keys above. Use null for missing values.
        7. DO NOT open individual tender pages — only extract data from the listing view to save time.
    """
    
    print(f"\nURL: {url}")
    print(f"\nGoal: {goal[:200]}...\n")
    
    if not settings.tinyfish_api_key:
        print("ERROR: TINYFISH_API_KEY not configured!")
        return
    
    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json",
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    print("=" * 80)
    print("STREAMING RESPONSE FROM TINYFISH")
    print("=" * 80)
    
    event_count = 0
    result_data = []
    
    async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
        async with client.stream("POST", f"{TINYFISH_BASE_URL}/automation/run-sse", headers=headers, json=payload) as response:
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                response.raise_for_status()
            
            print("\n")
            
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                    
                print(f"[RAW] {line[:120]}")
                
                if not line.startswith("data:"): 
                    continue
                    
                raw = line[5:].strip()
                if raw == "[DONE]": 
                    print("\n✅ Stream ended with [DONE]")
                    break
                
                try:
                    event = json.loads(raw)
                    event_count += 1
                    event_type = event.get("type", "unknown")
                    
                    print(f"  → Event #{event_count}: type={event_type}")
                    
                    # Print event details
                    if event_type == "PROGRESS":
                        print(f"    Progress: {event.get('progress', {}).get('status', 'N/A')}")
                    elif event_type == "COMPLETE":
                        result_obj = event.get("result", {})
                        print(f"    Result type: {type(result_obj).__name__}")
                        if isinstance(result_obj, dict):
                            content = result_obj.get("result", "")
                            print(f"    Content type: {type(content).__name__}")
                            if isinstance(content, str) and len(content) > 0:
                                print(f"    Content preview: {content[:150]}...")
                                # Try to parse it
                                try:
                                    if content.startswith("```"):
                                        parsed_content = "\n".join(l for l in content.split("\n") if not l.startswith("```")).strip()
                                    else:
                                        parsed_content = content
                                    parsed = json.loads(parsed_content)
                                    print(f"    ✅ Successfully parsed JSON! Type: {type(parsed).__name__}")
                                    if isinstance(parsed, list):
                                        print(f"    Array length: {len(parsed)}")
                                        if len(parsed) > 0:
                                            print(f"    First item keys: {list(parsed[0].keys())}")
                                        result_data = parsed
                                    elif isinstance(parsed, dict) and "tenders" in parsed:
                                        print(f"    Found 'tenders' key with {len(parsed['tenders'])} items")
                                        result_data = parsed["tenders"]
                                except json.JSONDecodeError as e:
                                    print(f"    ❌ Failed to parse JSON: {e}")
                        elif isinstance(result_obj, list):
                            print(f"    Direct list received with {len(result_obj)} items")
                            result_data = result_obj
                    elif event_type == "HEARTBEAT":
                        print(f"    Heartbeat (still alive)")
                    elif event_type == "STARTED":
                        print(f"    Agent started")
                    
                except json.JSONDecodeError as e:
                    print(f"  ❌ Failed to parse event JSON: {e}")
                    print(f"    Raw: {raw}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Received {event_count} events")
    print(f"Final result_data type: {type(result_data).__name__}")
    print(f"Final result_data length: {len(result_data) if isinstance(result_data, list) else 'N/A'}")
    
    if isinstance(result_data, list) and len(result_data) > 0:
        print(f"\nFirst tender:")
        print(json.dumps(result_data[0], indent=2))
    else:
        print("\n⚠️ No tender data extracted!")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_single_portal_debug())
