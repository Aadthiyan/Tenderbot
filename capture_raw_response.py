"""
Capture ALL event types from TinyFish to understand the actual response format
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
print("RAW TINYFISH RESPONSE CAPTURE")
print("="  * 80 + "\n")

async def capture_all_events():
    keywords = ["software", "IT"]
    kw_str = " ".join(keywords)
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"https://sam.gov/search/?index=opp&q={kw_str}&dateRange=custom&startDate={thirty_days_ago}&endDate={today}&status=active"
    
    goal = """Find contract opportunities on SAM.gov and return them as JSON."""
    
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
    
    print(f"Capturing ALL events from TinyFish...\n")
    
    event_types = {}
    all_events = []
    
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{TINYFISH_BASE_URL}/automation/run-sse",
                headers=headers,
                json=payload,
            ) as response:
                
                print(f"HTTP Status: {response.status_code}\n")
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    
                    raw = line[5:].strip()
                    
                    try:
                        event = json.loads(raw)
                        all_events.append(event)
                        
                        event_type = event.get("type")
                        if event_type:
                            event_types[event_type] = event_types.get(event_type, 0) + 1
                            print(f"[{event_type}]", end=" ")
                            
                            # Print key info based on type
                            if event_type == "result":
                                content = event.get("content", "")
                                print(f"Content: {content[:60]}...", end="")
                            elif event_type == "COMPLETE":
                                status = event.get("status", "")
                                print(f"status={status}", end="")
                            elif event_type == "PROGRESS":
                                purpose = event.get("purpose", "")
                                print(f"{purpose[:40]}...", end="")
                            
                            print()  # newline
                    except json.JSONDecodeError:
                        pass
        
        print(f"\n" + "=" * 80)
        print(f"SUMMARY")
        print(f"=" * 80)
        print(f"\nEvent type distribution:")
        for event_type, count in sorted(event_types.items()):
            print(f"  {event_type:15} : {count:3} events")
        
        print(f"\nTotal events: {len(all_events)}")
        
        # Look for specific events
        print(f"\n--- Looking for 'result' events ---")
        result_events = [e for e in all_events if e.get("type") == "result"]
        if result_events:
            print(f"Found {len(result_events)} result event(s):")
            for i, e in enumerate(result_events, 1):
                content = e.get("content", "")
                print(f"\n[Result {i}]")
                print(content)
        else:
            print("No 'result' events found")
        
        # Look for COMPLETE event
        print(f"\n--- Looking for 'COMPLETE' event ---")
        complete_events = [e for e in all_events if e.get("type") == "COMPLETE"]
        if complete_events:
            print(f"Found {len(complete_events)} COMPLETE event(s):")
            for i, e in enumerate(complete_events, 1):
                print(f"\n[Complete {i}]")
                print(json.dumps(e, indent=2))
        
        # Check if there's data in any other field
        print(f"\n--- Searching for data in all events ---")
        for event in all_events:
            if "content" in event and event.get("type") != "result":
                print(f"\nNon-result event with content: {event.get('type')}")
                print(f"Content: {event['content'][:100]}")
            if "data" in event:
                print(f"\nEvent with 'data' field: {event.get('type')}")
                print(json.dumps(event.get("data"), indent=2)[:200])
            if "output" in event:
                print(f"\nEvent with 'output' field: {event.get('type')}")
                print(json.dumps(event.get("output"), indent=2)[:200])
    
    except asyncio.TimeoutError:
        print(f"TIMEOUT")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(capture_all_events())
