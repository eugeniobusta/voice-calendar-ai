"""
config.py — The "settings panel" for the whole system.

All configuration lives here in one place. We read settings from
environment variables, which come from the .env file at startup.

WHY environment variables instead of hardcoding values?
  - Security: your API key never appears in code (never commit secrets)
  - Flexibility: change settings without touching code
  - Industry standard: every real project uses this pattern

HOW it works:
  1. python-dotenv reads the .env file
  2. load_dotenv() loads those values into os.environ
  3. os.getenv("KEY", "default") reads them (with a fallback default)
"""
import os
from dotenv import load_dotenv

# Reads the .env file and loads all KEY=VALUE pairs into the environment
load_dotenv()


class Config:
    def __init__(self):
        # ── Groq (AI parsing + cloud transcription) ────────────────────────
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # ── Local Whisper (CLI only) ───────────────────────────────────────
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")

        # ── Apple Calendar (CLI / Mac only) ───────────────────────────────
        self.calendar_name = os.getenv("CALENDAR_NAME", "Home")

        # ── Storage ───────────────────────────────────────────────────────
        self.db_path = os.getenv("DB_PATH", "data/events.db")

        # ── Web app ───────────────────────────────────────────────────────
        # Password to protect your web app from strangers
        self.app_secret = os.getenv("APP_SECRET", "")

        # Your timezone — events are created in this zone
        # Find yours at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        # Examples: America/New_York, America/Los_Angeles, Europe/London, Europe/Rome
        self.timezone = os.getenv("TIMEZONE", "America/New_York")

        # ── Google Calendar (web app only) ────────────────────────────────
        # These come from setup_google_auth.py — run it once on your Mac
        self.google_client_id      = os.getenv("GOOGLE_CLIENT_ID", "")
        self.google_client_secret  = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.google_refresh_token  = os.getenv("GOOGLE_REFRESH_TOKEN", "")

        self._validate()

    def _validate(self):
        """Fails early with a helpful message if required config is missing."""
        if not self.groq_api_key:
            raise EnvironmentError(
                "\n\n  GROQ_API_KEY is missing!\n"
                "  Steps to fix:\n"
                "  1. Go to https://console.groq.com and sign up (free, no credit card)\n"
                "  2. Click 'API Keys' → 'Create API Key'\n"
                "  3. Copy the key and paste it into your .env file as:\n"
                "     GROQ_API_KEY=gsk_...\n"
            )
        # Google Calendar credentials are only checked when GoogleCalendarWriter is used,
        # so we don't validate them here (CLI mode doesn't need them)
