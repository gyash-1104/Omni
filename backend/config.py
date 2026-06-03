"""
Aadhya – AI Interior Design Consultant
Configuration via environment variables (Pydantic Settings)
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

# Project root (parent of backend/) — load .env from here regardless of shell cwd
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    # Set true only after Twilio Content templates for quick-reply buttons are configured
    twilio_whatsapp_quick_reply: bool = False
    # Twilio Content template SID for interactive WhatsApp MCQ/list messages
    # The template should support content variables for prompt/options/payloads.
    twilio_whatsapp_interactive_content_sid: str = ""
    # Variable-based list picker for service menu (no AVA welcome). See scripts/create_service_list_content.py
    twilio_service_selection_content_sid: str = ""

    # Vapi
    vapi_api_key: str = ""
    vapi_assistant_id: str = ""

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Upstash Redis
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""
    session_ttl_hours: int = 24

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Admin
    admin_password: str = "changeme"
    admin_api_key: str = "changeme"

    # App
    environment: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    # Public-facing base URL — used by Vapi to self-reference the webhook URL
    # Set this to your deployed domain, e.g. https://aadhya.onrender.com
    base_url: str = "http://localhost:8000"
    # Allowed CORS origins — comma-separated list, e.g. https://admin.tatvaops.com
    # Use * only during local development
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS_ORIGINS env var into a list."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
