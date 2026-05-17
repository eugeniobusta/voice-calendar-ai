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
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.calendar_name = os.getenv("CALENDAR_NAME", "Home")
        self.db_path = os.getenv("DB_PATH", "data/events.db")
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
