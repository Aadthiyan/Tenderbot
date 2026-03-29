"""
TenderBot Global — Test Voice Briefing Generator (Phase 7.2)
Simulates fetching top tenders and hitting the ElevenLabs TTS engine.
"""
import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.voice_briefing import generate_voice_briefing
from backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")

MOCK_TOP_TENDERS = [
    {
        "tender_id": "DOD-2026-CLD-001",
        "title": "FedRAMP Cloud Migration & Zero Trust Security Audit",
        "agency": "Department of Defense",
        "country": "US",
        "estimated_value": 4_500_000,
        "days_until_deadline": 59,
        "relevance_score": 94,
        "action": "apply_now",
        "our_probability": 72,
    },
    {
        "tender_id": "CAB-2026-DT-002",
        "title": "Digital Transformation Partner for Central Government",
        "agency": "Cabinet Office",
        "country": "UK",
        "estimated_value": 7_500_000,
        "days_until_deadline": 39,
        "relevance_score": 87,
        "action": "apply_now",
    },
    {
        "tender_id": "SSC-2026-00456",
        "title": "Secure Cloud Email and Collaboration Platform",
        "agency": "Shared Services Canada",
        "relevance_score": 81,
        "action": "watch",
    }
]

async def test_briefing():
    print("==============================================================")
    print("TESTING ELEVENLABS VOICE BRIEFING (TASK 7.2)")
    print("Generating natural script and making TTS API request.")
    print("==============================================================\n")
    
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        print("⚠️ ELEVENLABS_API_KEY is not set in .env!")
        print("Generating script and outputting mock silent MP3 file.")
        print("-" * 60)
        
    result = await generate_voice_briefing(MOCK_TOP_TENDERS, company_name="Agile Defend IT")
    
    print("🎙️ GENERATED SCRIPT:\n")
    print(result["script"])
    print(f"\nWord count: {result['word_count']} words")
    print(f"Est. Duration: {result['duration_estimate_s']} seconds")
    print(f"File Path: {result['audio_path']}")
    print(f"Status: {result['status']}")

if __name__ == "__main__":
    asyncio.run(test_briefing())
