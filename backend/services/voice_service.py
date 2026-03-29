"""
TenderBot Global — ElevenLabs Voice Briefing Service
Generates a daily 60-second audio summary of top tenders.
"""
import os
import logging
from datetime import datetime
from backend.config import get_settings
from backend.services.db import tenders_col

logger = logging.getLogger(__name__)
settings = get_settings()

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "audio")
BRIEFING_FILE = os.path.join(AUDIO_DIR, "briefing_today.mp3")


async def generate_daily_briefing() -> str | None:
    """
    1. Fetches top 3 tenders from MongoDB.
    2. Builds a natural-language script.
    3. Calls ElevenLabs TTS to produce an MP3.
    4. Saves to backend/audio/briefing_today.mp3.
    Returns path to the MP3 or None on failure.
    """
    if not settings.elevenlabs_api_key:
        logger.warning("ElevenLabs API key not set — skipping voice briefing.")
        return None

    try:
        # Fetch top tenders
        top_tenders = await tenders_col().find(
            {"status": "active", "relevance_score": {"$exists": True, "$ne": None}},
            {"title": 1, "agency": 1, "estimated_value": 1,
             "days_until_deadline": 1, "relevance_score": 1,
             "eligibility_score": 1, "our_win_probability": 1, "_id": 0}
        ).sort("relevance_score", -1).limit(3).to_list(length=3)

        total = await tenders_col().count_documents(
            {"status": "active", "scraped_at": {"$gte": datetime(datetime.utcnow().year,
                                                                  datetime.utcnow().month,
                                                                  datetime.utcnow().day)}}
        )

        script = _build_script(top_tenders, total)
        logger.info(f"Voice script ({len(script)} chars): {script[:120]}…")

        # Generate audio
        from elevenlabs.client import ElevenLabs
        from elevenlabs import save

        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        audio = client.generate(
            text=script,
            voice=settings.elevenlabs_voice_id,
            model="eleven_monolingual_v1",
        )

        os.makedirs(AUDIO_DIR, exist_ok=True)
        save(audio, BRIEFING_FILE)

        logger.info(f"✅ Voice briefing generated → {BRIEFING_FILE}")
        return BRIEFING_FILE

    except Exception as e:
        logger.error(f"Voice briefing generation failed: {e}")
        return None


def _build_script(top_tenders: list[dict], total_today: int) -> str:
    """Builds a ~60 second natural-language script from top tender data."""
    lines = [
        f"Good morning. TenderBot found {total_today} relevant tender{'s' if total_today != 1 else ''} today.",
    ]

    if not top_tenders:
        lines.append("No high-priority tenders to report today. Check back tomorrow.")
    else:
        top = top_tenders[0]
        value = top.get("estimated_value")
        value_str = f"${value / 1_000_000:.1f} million" if value and value >= 1_000_000 \
            else f"${value:,.0f}" if value else "value not disclosed"

        lines.append(
            f"Top opportunity: {top.get('title', 'Unknown tender')} "
            f"from {top.get('agency', 'unknown agency')}, "
            f"valued at {value_str}, "
            f"closing in {top.get('days_until_deadline', '?')} days. "
            f"Relevance score: {top.get('relevance_score', '?')} out of 100."
        )

        if top.get('eligibility_score'):
            lines.append(
                f"Eligibility score: {top['eligibility_score']} out of 100."
            )

        if len(top_tenders) > 1:
            second = top_tenders[1]
            lines.append(
                f"Second pick: {second.get('title', 'Another tender')} "
                f"from {second.get('agency', 'unknown')}. "
                f"Score: {second.get('relevance_score', '?')} out of 100."
            )

    lines.append("Open your TenderBot dashboard for the full ranked list. Good luck.")
    return " ".join(lines)
