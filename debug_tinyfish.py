"""
TinyFish Debug Script — Deep investigation of why agents return 0 tenders
Tests:
  1. API connectivity
  2. Raw TinyFish response parsing
  3. Portal URL accessibility
  4. Goal instruction clarity
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
print("TINYFISH DEBUGGING SUITE")
print("=" * 80)

# ──────────────────────────────────────────────────────────────────────────────
# TEST 1: Verify API Key
# ──────────────────────────────────────────────────────────────────────────────
print("\n[TEST 1] API Key Configuration")
print("-" * 80)

if not settings.tinyfish_api_key:
    print("❌ CRITICAL: TINYFISH_API_KEY is EMPTY")
    sys.exit(1)

key_preview = settings.tinyfish_api_key[:20] + "..." if len(settings.tinyfish_api_key) > 20 else settings.tinyfish_api_key
print(f"✓ API Key configured: {key_preview}")
print(f"✓ Key length: {len(settings.tinyfish_api_key)} chars")
print(f"✓ Key prefix: {settings.tinyfish_api_key[:10]}")


# ──────────────────────────────────────────────────────────────────────────────
# TEST 2: Test HTTP connectivity to TinyFish API
# ──────────────────────────────────────────────────────────────────────────────
async def test_api_connectivity():
    print("\n[TEST 2] API Connectivity")
    print("-" * 80)
    
    headers = {
        "X-API-Key": settings.tinyfish_api_key,
        "Content-Type": "application/json",
    }
    
    # Try a simple health check or status endpoint
    test_urls = [
        f"{TINYFISH_BASE_URL}/automation/run-sse",  # The actual endpoint we use
        "https://agent.tinyfish.ai/",  # Root
    ]
    
    async with httpx.AsyncClient(timeout=10) as client:
        for url in test_urls:
            try:
                print(f"\n  Testing: {url}")
                resp = await client.get(url, headers=headers, follow_redirects=True)
                print(f"    Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"    ✓ Server responding")
                elif resp.status_code == 307 or resp.status_code == 308:
                    print(f"    Redirect to: {resp.headers.get('location', 'unknown')}")
                else:
                    print(f"    Response: {resp.text[:200]}")
            except Exception as e:
                print(f"    ❌ Connection failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# TEST 3: Test with actual SAM.gov portal
# ──────────────────────────────────────────────────────────────────────────────
async def test_sam_gov_minimal():
    print("\n[TEST 3] Minimal SAM.gov Scrape Test")
    print("-" * 80)
    
    keywords = ["software", "IT"]
    kw_str = " ".join(keywords)
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Build the exact URL the agent will navigate to
    url = f"https://sam.gov/search/?index=opp&q={kw_str}&dateRange=custom&startDate={thirty_days_ago}&endDate={today}&status=active"
    
    print(f"\n  Target Portal URL:")
    print(f"    {url[:100]}...")
    
    # Test if we can even reach SAM.gov
    print(f"\n  Testing SAM.gov reachability...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://sam.gov", follow_redirects=True)
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"    ✓ SAM.gov is reachable")
                print(f"    Content length: {len(resp.content)} bytes")
            else:
                print(f"    ✗ SAM.gov returned {resp.status_code}")
    except Exception as e:
        print(f"    ❌ Could not reach SAM.gov: {e}")
        print(f"       (This might be why TinyFish gets 0 results)")
    
    # Now call TinyFish with a VERY minimal goal
    print(f"\n  Calling TinyFish API...")
    
    goal = f"""
    Navigate to SAM.gov. 
    You will see government contract opportunities for: '{kw_str}'.
    Extract the first 5 visible titles and URLs from the search results.
    Return ONLY valid JSON array with at least these fields: title, url.
    Return empty array [] if no results found.
    """
    
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
    
    print(f"  Request payload:")
    print(f"    URL: {url[:80]}...")
    print(f"    Goal: Extract first 5 titles from SAM.gov")
    print(f"    Output format: json")
    
    print(f"\n  Receiving from TinyFish (streaming)...")
    print(f"  (This may take 30-120 seconds...)\n")
    
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
                print(f"  Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    text = await response.atext()
                    print(f"  ERROR Response: {text[:500]}")
                    return
                
                print(f"  Starting to read events...\n")
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data:"):
                        raw = line[5:].strip()
                        event_count += 1
                        
                        print(f"  [Event {event_count}] {raw[:100]}..." if len(raw) > 100 else f"  [Event {event_count}] {raw}")
                        
                        if raw == "[DONE]":
                            print(f"  ✓ Stream completed with [DONE] marker")
                            break
                        
                        try:
                            event = json.loads(raw)
                            
                            if event.get("type") == "result":
                                content = event.get("content", "")
                                print(f"\n  ✓✓✓ RESULT EVENT RECEIVED ✓✓✓")
                                print(f"      Content length: {len(content)} chars")
                                print(f"      Content preview: {content[:200]}...")
                                
                                # Parse JSON from content
                                try:
                                    result_data = json.loads(content)
                                    print(f"      Parsed JSON array with {len(result_data)} items")
                                    if result_data:
                                        print(f"      First item: {json.dumps(result_data[0], indent=2)[:200]}")
                                except:
                                    print(f"      ⚠ Content is not valid JSON, trying to extract...")
                                    result_data = content
                                
                                break
                            
                            elif event.get("type") == "error":
                                error_msg = event.get("message", "Unknown error")
                                print(f"  ❌ ERROR EVENT: {error_msg}")
                                break
                            
                            elif event.get("type") == "thinking":
                                thought = event.get("content", "")
                                if thought:
                                    print(f"      [Thinking] {thought[:80]}...")
                            
                            elif event.get("type") == "action":
                                action = event.get("action", {})
                                print(f"      [Action] {action.get('type', 'unknown')}: {str(action.get('parameters', {}))[:60]}...")
                        
                        except json.JSONDecodeError as je:
                            print(f"  ✗ Failed to parse event JSON: {je}")
                            print(f"    Raw: {raw[:200]}")
        
        print(f"\n  Total events received: {event_count}")
        
        if error_msg:
            print(f"\n❌ TinyFish returned error: {error_msg}")
        elif result_data:
            if isinstance(result_data, list):
                print(f"\n✓ SUCCESS: Extracted {len(result_data)} items")
                print(f"\nFirst result:")
                print(json.dumps(result_data[0], indent=2))
            else:
                print(f"\n⚠ Result is not a list: {type(result_data)}")
                print(f"Content: {str(result_data)[:500]}")
        else:
            print(f"\n❌ No result event received. Stream may have timed out or portal had no data.")
    
    except asyncio.TimeoutError:
        print(f"\n❌ TIMEOUT: Request took >180 seconds")
        print(f"   This suggests TinyFish browser is stuck or portal is very slow")
    except Exception as e:
        print(f"\n❌ Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


# ──────────────────────────────────────────────────────────────────────────────
# TEST 4: Check portal accessibility directly  
# ──────────────────────────────────────────────────────────────────────────────
async def test_portal_accessibility():
    print("\n[TEST 4] Direct Portal Accessibility")
    print("-" * 80)
    
    portals = {
        "SAM.gov": "https://sam.gov",
        "TED EU": "https://ted.europa.eu",
        "UNGM": "https://www.ungm.org",
        "Find-a-Tender": "https://www.find-tender.service.gov.uk",
        "AusTender": "https://www.austender.com.au",
        "CanadaBuys": "https://www.buyandsell.gc.ca",
    }
    
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for name, url in portals.items():
            try:
                resp = await client.get(url)
                status = "✓" if resp.status_code == 200 else "✗"
                print(f"  {status} {name:20} {resp.status_code}")
            except Exception as e:
                print(f"  ✗ {name:20} ERROR: {str(e)[:40]}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ──────────────────────────────────────────────────────────────────────────────
async def main():
    await test_api_connectivity()
    await test_portal_accessibility()
    await test_sam_gov_minimal()
    
    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
