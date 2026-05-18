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
        # ── AI provider ───────────────────────────────────────────────────
        # "groq"   → Groq cloud API (needs internet + GROQ_API_KEY)
        # "ollama" → fully local LLM via Ollama (no internet, no key needed)
        self.ai_provider = os.getenv("AI_PROVIDER", "groq")

        # ── Groq (cloud AI) ───────────────────────────────────────────────
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # ── Ollama (local AI) ─────────────────────────────────────────────
        # Install: brew install ollama
        # Pull:    ollama pull llama3.2
        # Start:   ollama serve
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.ollama_host  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")

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

        # ── Telegram bot ──────────────────────────────────────────────────
        # Token from @BotFather. Chat ID from sending /start to your bot.
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id   = os.getenv("TELEGRAM_CHAT_ID", "")

        self._validate()

    def _validate(self):
        """Fails early with a helpful message if required config is missing."""
        if self.ai_provider == "groq" and not self.groq_api_key:
            raise EnvironmentError(
                "\n\n  GROQ_API_KEY is missing!\n"
                "  Either add your Groq key, or switch to local mode:\n"
                "  AI_PROVIDER=ollama  (then: brew install ollama && ollama pull llama3.2)\n"
            )
