"""
Improved SAM.gov Agent with Better Goal Clarity
Tests with extremely specific instructions
"""
import asyncio
import httpx
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.config import get_settings

settings = get_settings()
TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"

print("\n" + "=" * 80)
print("IMPROVED SAM.GOV AGENT TEST — Simplified Goal")
print("=" * 80 + "\n")

async def test_improved_sam_gov():
    """
    Tests with a MUCH simpler, clearer goal that focuses on:
    1. Finding ANY visible text that looks like tender titles
    2. Extracting basic fields
    3. Returning JSON even if incomplete
    """
    
    keywords = ["software", "IT"]
    kw_str = " ".join(keywords)
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"https://sam.gov/search/?index=opp&q={kw_str}&dateRange=custom&startDate={thirty_days_ago}&endDate={today}&status=active"
    
    # SIMPLIFIED GOAL
    improved_goal = """
You are at SAM.gov searching for government contract opportunities.

Your task is to extract procurement opportunities from the search results.

Instructions:
1. Accept any cookie consent popups or warnings first.
2. Wait for the page to fully load (you should see a list/table of opportunities).
3. Look for entries that contain:
   - A title/name of the opportunity
   - An agency or organization name
   - A deadline date
   - An opportunity ID or number
   - Optionally: contract value, location, description

4. From the visible search results, extract the first 3-10 opportunities you can clearly see.
   For each one, create a JSON object with these fields:
   - title (string): The name/title of the opportunity
   - agency (string): The issuing agency
   - deadline (string): When bids are due (any format)
   - solicitation_number (string): ID or reference number
   - url (string): Direct link to this specific opportunity
   - description (string): Any visible description (first 100 chars)

5. If the page shows "No results found" or is empty, return: []

6. Return ONLY valid JSON as a list/array. Example:
[
  {"title": "Cloud Services RFP", "agency": "DoD", "deadline": "04/15/2026", "solicitation_number": "FA8123-456", "url": "https://...", "description": "Cloud migration..."},
  {...}
]

Do not add any explanatory text. Return only the JSON array.
    """
    
    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    
    payload = {
        "url": url,
        "goal": improved_goal,
        "output_format": "json",
    }
    
    print(f"Target: SAM.gov + '{kw_str}' keyword")
    print(f"Date range: {thirty_days_ago} to {today}")
    print(f"Goal: Extract first 3-10 opportunities\n")
    print(f"Sending request to TinyFish...\n")
    
    result_data = []
    event_count = 0
    error_msg = None
    
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST",
                f"{TINYFISH_BASE_URL}/automation/run-sse",
                headers=headers,
                json=payload,
            ) as response:
                
                if response.status_code != 200:
                    text = await response.atext()
                    print(f"ERROR {response.status_code}: {text}")
                    return
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    
                    raw = line[5:].strip()
                    event_count += 1
                    
                    try:
                        event = json.loads(raw)
                        
                        if event.get("type") == "result":
                            content = event.get("content", "")
                            print(f"\n{'='*80}")
                            print(f"RESULT EVENT RECEIVED!")
                            print(f"{'='*80}\n")
                            print(f"Content (raw):\n{content}\n")
                            
                            # Try to parse
                            try:
                                result_data = json.loads(content)
                                print(f"✓ Parsed as JSON array with {len(result_data)} items\n")
                                
                                if result_data:
                                    for i, item in enumerate(result_data[:3], 1):
                                        print(f"[Opportunity {i}]")
                                        print(f"  Title: {item.get('title', 'N/A')}")
                                        print(f"  Agency: {item.get('agency', 'N/A')}")
                                        print(f"  Deadline: {item.get('deadline', 'N/A')}")
                                        print(f"  ID: {item.get('solicitation_number', 'N/A')}")
                                        print(f"  URL: {item.get('url', 'N/A')[:60]}...\n")
                                else:
                                    print("Array is empty []")
                            except json.JSONDecodeError:
                                print(f"⚠ Content is not JSON: {content[:200]}")
                            
                            break
                        
                        elif event.get("type") == "error":
                            error_msg = event.get("message", "Unknown")
                            print(f"\nERROR: {error_msg}\n")
                            break
                        
                        elif event.get("type") == "PROGRESS":
                            purpose = event.get("purpose", "")
                            if purpose:
                                print(f"[Progress] {purpose[:70]}...")
                        
                        elif event.get("type") == "COMPLETE":
                            print(f"\n[Complete] Agent finished (but no result event received)")
                            break
                        
                        elif event.get("type") == "HEARTBEAT":
                            pass  # Skip heartbeats in output
                    
                    except json.JSONDecodeError:
                        pass
        
        print(f"\nTotal events: {event_count}")
        
        if error_msg:
            print(f"\n❌ Error: {error_msg}")
        elif result_data:
            print(f"\n✓ SUCCESS! Got {len(result_data)} opportunities")
        else:
            print(f"\n❌ No result received - agent may need better instructions")
    
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT: TinyFish took >180 seconds")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_sam_gov())
