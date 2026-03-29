"""
TenderBot Global — ElevenLabs Voice Briefing (Phase 7.2)
Generates a ~60s daily audio briefing by:
1. Composing a natural briefing script from the top scored tenders
2. Sending it to ElevenLabs TTS API
3. Persisting the MP3 to disk and returning the file path

Mock-safe: if ELEVENLABS_API_KEY is absent, synthesises a script-only
response and returns a placeholder path so the UI can still render.
"""
import httpx
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
AUDIO_DIR = Path("backend/static/briefings")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Target ≈ 60s: ElevenLabs generates ~150 words/min, so we want ~150 words
MAX_TENDERS_IN_BRIEF = 5
MAX_WORDS = 160


# ── Script Generation ─────────────────────────────────────────────────────────

def build_briefing_script(tenders: list[dict], company_name: str = "your company") -> str:
    """
    Creates a natural-language briefing script from the top scored tenders.
    Keeps within MAX_WORDS to target ~60s at ElevenLabs default pace.
    """
    today = datetime.utcnow().strftime("%A, %B %d")
    top = [t for t in tenders if (t.get("relevance_score") or 0) >= 60][:MAX_TENDERS_IN_BRIEF]

    if not top:
        return (
            f"Good morning. Today is {today}. "
            f"TenderBot has completed its daily scan across six global procurement portals. "
            f"No tenders scored above sixty today for {company_name}. "
            f"Try expanding your keywords or lowering the score threshold in your profile. "
            f"TenderBot will continue scanning automatically. Have a productive day."
        )

    apply_now = [t for t in top if t.get("action") == "apply_now"]
    watch = [t for t in top if t.get("action") == "watch"]

    lines = [
        f"Good morning. Today is {today}. Here is your TenderBot intelligence briefing."
    ]

    lines.append(
        f"TenderBot scanned six global portals and found {len(top)} high-priority "
        f"opportunit{'y' if len(top) == 1 else 'ies'} matching your profile."
    )

    if apply_now:
        t = apply_now[0]
        value = t.get("estimated_value")
        value_str = f"valued at {'${:,.0f}'.format(value)}" if value else ""
        days = t.get("days_until_deadline")
        deadline_str = f"closing in {days} days" if days else ""
        prob = t.get("our_probability")
        prob_str = f"with a {prob} percent win probability" if prob else ""
        lines.append(
            f"Top priority: {t['title']}, issued by {t.get('agency', 'a government agency')} in {t.get('country', 'an international market')}. "
            f"Relevance score {t.get('relevance_score')} out of one hundred. "
            f"{value_str}. {deadline_str}. {prob_str}. Recommended action: apply now."
        )

    if len(apply_now) > 1:
        for t in apply_now[1:2]:
            days = t.get("days_until_deadline")
            lines.append(
                f"Also flagged to apply: {t['title']} from {t.get('agency', 'an agency')}, "
                f"closing in {days} days with a score of {t.get('relevance_score')}."
            )

    if watch:
        names = ", ".join(t["title"][:40] for t in watch[:2])
        lines.append(f"Additionally, {len(watch)} tenders are on watch: {names}.")

    # Amendment check
    amended = [t for t in top if t.get("amendment_history")]
    if amended:
        t = amended[0]
        latest = t["amendment_history"][-1]
        lines.append(
            f"Important update: {t['title']} has been amended. "
            f"{latest.get('changes_summary', 'Review the latest changes before submitting.')}"
        )

    lines.append(
        "Visit your TenderBot dashboard to review full eligibility analysis, "
        "competitor intelligence, and to launch the auto form-fill assistant. "
        "Good luck today."
    )

    script = " ".join(lines)

    # Trim to MAX_WORDS to keep ~60s
    words = script.split()
    if len(words) > MAX_WORDS:
        script = " ".join(words[:MAX_WORDS]) + ". Good luck today."

    return script


# ── ElevenLabs TTS ────────────────────────────────────────────────────────────

async def generate_voice_briefing(tenders: list[dict], company_name: str = "your company") -> dict:
    """
    Generates the briefing script, converts to MP3 via ElevenLabs, saves file.
    Returns a dict with: script, audio_path, duration_estimate_s, audio_url
    """
    script = build_briefing_script(tenders, company_name)
    word_count = len(script.split())
    duration_estimate = round(word_count / 2.5)  # ~150 words/min ≈ 2.5 words/sec

    date_slug = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"briefing_{date_slug}.mp3"
    audio_path = AUDIO_DIR / filename
    audio_url = f"/static/briefings/{filename}"

    if not settings.elevenlabs_api_key:
        # Mock: write a tiny placeholder so the path exists
        _write_mock_audio(audio_path)
        return {
            "script": script,
            "audio_path": str(audio_path),
            "audio_url": audio_url,
            "duration_estimate_s": duration_estimate,
            "word_count": word_count,
            "status": "mock",
            "message": "Mock audio generated. Add ELEVENLABS_API_KEY for real TTS."
        }

    voice_id = settings.elevenlabs_voice_id
    url = ELEVEN_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.80,
            "style": 0.30,
            "use_speaker_boost": True,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            audio_path.write_bytes(response.content)
            logger.info(f"🎙️ Voice briefing saved: {audio_path} ({len(response.content)} bytes)")

        return {
            "script": script,
            "audio_path": str(audio_path),
            "audio_url": audio_url,
            "duration_estimate_s": duration_estimate,
            "word_count": word_count,
            "status": "generated",
            "message": f"ElevenLabs MP3 generated ({len(response.content) // 1024}KB)"
        }

    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        _write_mock_audio(audio_path)
        return {
            "script": script,
            "audio_path": str(audio_path),
            "audio_url": audio_url,
            "duration_estimate_s": duration_estimate,
            "word_count": word_count,
            "status": "fallback_mock",
            "error": str(e)
        }


def _write_mock_audio(path: Path):
    """Write a minimal valid MP3 stub so the endpoint doesn't 404."""
    # ID3 header + minimal MP3 frame — browsers will play 0.1s silence
    stub = (
        b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03"
        b"Lavf58.76.100\x00\xff\xfb\x90d\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    path.write_bytes(stub * 12)
