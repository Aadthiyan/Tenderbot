import asyncio
import httpx
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
from backend.config import get_settings

settings = get_settings()

async def test_tinyfish():
    if not settings.tinyfish_api_key:
        print("Missing TinyFish API Key")
        return
    
    headers = {"X-API-Key": settings.tinyfish_api_key}
    async with httpx.AsyncClient() as client:
        try:
            # According to docs, doing a POST to /run without body payload structure should return a 422 or 400 (which proves auth is OK)
            res = await client.post("https://agent.tinyfish.ai/v1/automation/run", headers=headers, json={})
            if res.status_code == 401:
                print("❌ TinyFish: Invalid API Key (401 Unauthorized)")
            else:
                print(f"✅ TinyFish: Authentication OK (Got {res.status_code})")
        except Exception as e:
            print(f"❌ TinyFish Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tinyfish())
