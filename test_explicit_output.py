"""
SAM.gov Agent with EXPLICIT output format instructions
Forces JSON return at the end
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
print("SAM.GOV Agent Test — With EXPLICIT Output Format")
print("=" * 80 + "\n")

async def test_explicit_output_format():
    """
    Tests with EXPLICIT instruction to output JSON result at the very end
    """
    
    keywords = ["software", "IT"]
    kw_str = " ".join(keywords)
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"https://sam.gov/search/?index=opp&q={kw_str}&dateRange=custom&startDate={thirty_days_ago}&endDate={today}&status=active"
    
    # EXPLICIT OUTPUT INSTRUCTION
    explicit_goal = """
You are searching SAM.gov for government contract opportunities.

OVERALL OBJECTIVE:
Extract government procurement opportunities and return them as JSON.

STEPS:
1. Accept any popups/consent banners.
2. Navigate to or wait for the SAM.gov search results page.
3. You should see a list of opportunities matching your search.
4. For each visible opportunity in the search results (aim for the first 5-10), extract:
   - Title: The name of the opportunity
   - Agency: The issuing government agency
   - Solicitation ID: The unique ID/reference number
   - Deadline: The bid submission deadline date
   - Value: The estimated contract value (if shown)
   - Description: A brief description
   - URL: The direct link to the full opportunity

FINAL STEP (CRITICAL - YOU MUST DO THIS):
After extracting all the opportunities you can see, output them as a JSON array.
Return ONLY a valid JSON array. Nothing else.

Example format (you must return exactly like this):
[
  {
    "title": "Software Development Services",
    "agency": "Department of Defense",
    "solicitation_number": "FA8771-26-R001",
    "deadline": "2026-04-15",
    "value": "2500000",
    "description": "Development of cloud-based applications",
    "url": "https://sam.gov/opp/..."
  },
  {
    "title": "IT Infrastructure",
    "agency": "Department of Veterans Affairs",
    "solicitation_number": "VA-26-RFQ-001",
    "deadline": "2026-04-10",
    "value": "1500000",
    "description": "Infrastructure modernization",
    "url": "https://sam.gov/opp/..."
  }
]

If you find ZERO opportunities, return: []

Do NOT include any text before or after the JSON array.
    """
    
    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    
    payload = {
        "url": url,
        "goal": explicit_goal,
        "output_format": "json",  # Tell TinyFish we expect JSON
    }
    
    print(f"Testing SAM.gov with EXPLICIT output format instructions...")
    print(f"Looking for: '{kw_str}' opportunities\n")
    print(f"Starting TinyFish agent...\n")
    
    result_data = []
    all_content = []
    event_count = 0
    
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
                        event_type = event.get("type", "UNKNOWN")
                        
                        if event_type == "result":
                            content = event.get("content", "")
                            all_content.append(content)
                            print(f"\n{'='*80}")
                            print(f"RESULT EVENT #{len(all_content)} RECEIVED!")
                            print(f"{'='*80}")
                            print(f"Content:")
                            print(f"{content}\n")
                            
                            # Try to parse
                            try:
                                parsed = json.loads(content)
                                if isinstance(parsed, list):
                                    result_data.extend(parsed)
                                    print(f"✓ Parsed as JSON array with {len(parsed)} items\n")
                                else:
                                    print(f"⚠ Parsed but not a list: {type(parsed)}\n")
                            except json.JSONDecodeError as e:
                                print(f"⚠ Not valid JSON: {e}\n")
                        
                        elif event_type == "error":
                            msg = event.get("message", "Unknown")
                            print(f"\n❌ ERROR: {msg}\n")
                            break
                        
                        elif event_type == "PROGRESS":
                            purpose = event.get("purpose", "")
                            if purpose:
                                print(f"  {purpose[:75]}")
                        
                        elif event_type == "COMPLETE":
                            print(f"\n✓ Agent completed")
                            break
                    
                    except json.JSONDecodeError:
                        pass
        
        print(f"\n{'='*80}")
        print(f"FINAL RESULTS")
        print(f"{'='*80}")
        print(f"Total events received: {event_count}")
        print(f"Total result contents extracted: {len(all_content)}")
        print(f"Total opportunities parsed: {len(result_data)}\n")
        
        if result_data:
            print(f"✓✓✓ SUCCESS! Extracted {len(result_data)} opportunities:\n")
            for i, opp in enumerate(result_data[:5], 1):  # Show first 5
                print(f"[{i}] {opp.get('title', 'N/A')}")
                print(f"    Agency: {opp.get('agency', 'N/A')}")
                print(f"    ID: {opp.get('solicitation_number', 'N/A')}")
                print(f"    Deadline: {opp.get('deadline', 'N/A')}\n")
        else:
            print(f"❌ No opportunities extracted")
            if all_content:
                print(f"\nRaw content received:")
                for i, content in enumerate(all_content, 1):
                    print(f"\n--- Content {i} ---")
                    print(content[:500])
    
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT after 180 seconds")
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_explicit_output_format())
