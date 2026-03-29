"""
TenderBot Global — Application Configuration
Loads all settings from environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── TinyFish ──────────────────────────────────────────────────────────────
    tinyfish_api_key: str = ""
    enable_live_submit: bool = False

    # ── Security Moats ────────────────────────────────────────────────────────
    kms_secret_key: str = ""

    # ── Fireworks.ai ──────────────────────────────────────────────────────────
    fireworks_api_key: str = ""
    fireworks_model: str = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "tenderbot"

    # ── Celery/Redis ──────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # ── Composio ──────────────────────────────────────────────────────────────
    composio_api_key: str = ""
    slack_channel: str = "#procurement-alerts"

    # ── ElevenLabs ────────────────────────────────────────────────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # ── AgentOps ──────────────────────────────────────────────────────────────
    agentops_api_key: str = ""

    # ── App URLs ──────────────────────────────────────────────────────────────
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # ── App Config ────────────────────────────────────────────────────────────
    scrape_score_threshold: int = 75
    alert_score_threshold: int = 80
    daily_scrape_hour: int = 6
    alert_sweep_hour: int = 7
    amendment_check_interval_hours: int = 12
    max_portal_pages: int = 2
    agent_timeout_seconds: int = 120

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
