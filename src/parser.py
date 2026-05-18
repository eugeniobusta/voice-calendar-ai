"""
parser.py — Sends text to AI and gets back structured JSON.

TWO PROVIDERS — choose in your .env:

  AI_PROVIDER=groq    → Groq cloud API (free, needs internet, fast)
  AI_PROVIDER=ollama  → Ollama local LLM (free, no internet, runs on your Mac)

OLLAMA (fully local):
  Ollama runs open-source models directly on your Mac.
  No internet, no API key, no cost, completely private.
  Install: brew install ollama
  Model:   ollama pull llama3.2
  Start:   ollama serve  (or it starts automatically)

  The model runs on your Mac's CPU/GPU.
  llama3.2 (3B parameters) is fast on any modern Mac.
  mistral (7B) is more accurate but slower.

CALENDAR SELECTION:
  When you have multiple Apple Calendars (Personal, Gym, Exams, etc.),
  we pass the list to the AI so it can pick the right one.
  "Gym session tomorrow 7am" → Gym calendar
  "Algorithms exam Friday"   → Exams calendar
  "Coffee with Sarah"        → Personal calendar

JSON EXTRACTION:
  Local models are sometimes less strict about output format —
  they may add explanatory text around the JSON.
  _extract_json() handles this by finding the JSON object
  within whatever the model returns.
"""
import json
import requests
from datetime import date
from groq import Groq


# The base system prompt — calendar list is injected dynamically
SYSTEM_PROMPT_BASE = """You are a calendar assistant that extracts events and tasks from natural language.

STRICT RULES:
1. Output ONLY raw JSON — no explanation, no markdown, no code fences
2. Resolve ALL relative dates (tomorrow, next week, next Tuesday, etc.) to YYYY-MM-DD
3. Convert all times to 24-hour HH:MM format (e.g., 2:30 PM → 14:30)
4. If end time is unknown, set it 1 hour after start time
5. If a date is truly unknown, use null — do not guess
6. If a time is truly unknown, use null — do not guess
7. Separate calendar events (things at a specific time) from tasks (things to do)
8. Detect recurring events: "every Monday", "daily standup", "weekly review"
9. Default reminder: [30] (30 minutes before)
10. Set "calendar" to the most appropriate calendar from the list provided

WHAT IS AN EVENT vs A TASK?
  Event: has a specific date/time ("meeting at 3pm", "dentist Thursday")
  Task: something to do without a fixed time ("buy groceries", "send report")

OUTPUT — return exactly this JSON structure (nothing else):
{
  "events": [
    {
      "title": "Event name",
      "calendar": "Calendar name from the provided list",
      "date": "YYYY-MM-DD or null",
      "start_time": "HH:MM or null",
      "end_time": "HH:MM or null",
      "location": "Location string or null",
      "reminders": [30],
      "recurrence": "none or daily or weekly or monthly or yearly"
    }
  ],
  "tasks": [
    {
      "title": "Task name",
      "deadline": "YYYY-MM-DD or null"
    }
  ]
}"""


class Parser:
    def __init__(self, config):
        """
        Parameters:
            config: Config object — reads AI_PROVIDER to decide which backend to use
        """
        self.provider     = config.ai_provider
        self.groq_key     = config.groq_api_key
        self.groq_model   = config.groq_model
        self.ollama_host  = config.ollama_host
        self.ollama_model = config.ollama_model

    def parse(self, text: str, calendars: list = None, default_reminder: int = 30) -> dict:
        """
        Parses natural language into structured event data.

        Parameters:
            text:      the message to parse
            calendars: list of available Apple Calendar names.
                       The AI uses this to pick the right calendar for each event.
                       If None, defaults to ["Personal"].

        Returns:
            Raw dict with "events" and "tasks" keys (validated downstream).
        """
        today     = date.today().isoformat()
        cal_list  = calendars or ["Personal"]
        cal_str   = ", ".join(cal_list)

        # Inject today's date, calendars, and default reminder into the prompt
        system_prompt = (
            SYSTEM_PROMPT_BASE
            + f"\n\nAVAILABLE CALENDARS: {cal_str}"
            + f"\nChoose the most fitting calendar for each event."
            + f"\nIf unsure, use '{cal_list[0]}'."
            + f"\nDefault reminder: [{default_reminder}] minutes before each event."
        )

        user_message = f"Today's date: {today}\n\nMessage to parse:\n{text}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ]

        if self.provider == "ollama":
            raw_text = self._call_ollama(messages)
        else:
            raw_text = self._call_groq(messages)

        return self._extract_json(raw_text)

    # ── Groq (cloud) ──────────────────────────────────────────────────────

    def _call_groq(self, messages: list) -> str:
        client   = Groq(api_key=self.groq_key)
        response = client.chat.completions.create(
            model=self.groq_model,
            max_tokens=1024,
            messages=messages,
        )
        return response.choices[0].message.content.strip()

    # ── Ollama (local) ────────────────────────────────────────────────────

    def _call_ollama(self, messages: list) -> str:
        """
        Calls the local Ollama server using its OpenAI-compatible API.
        No extra package needed — we use 'requests' which is already installed.

        Ollama must be running: ollama serve
        Model must be pulled:   ollama pull llama3.2
        """
        try:
            response = requests.post(
                f"{self.ollama_host}/v1/chat/completions",
                json={"model": self.ollama_model, "messages": messages, "max_tokens": 1024},
                timeout=120,  # local models can be slower than cloud
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Could not connect to Ollama.\n"
                "Make sure it's running: ollama serve\n"
                f"Expected at: {self.ollama_host}"
            )

    # ── JSON extraction ───────────────────────────────────────────────────

    def _extract_json(self, text: str) -> dict:
        """
        Extracts a JSON object from the model's response.

        Cloud models (Groq) usually return pure JSON.
        Local models (Ollama) sometimes add surrounding text like:
          "Here is the extracted data: {...}"
        This method handles both cases robustly.
        """
        text = text.strip()

        # Strip markdown code fences if present (```json ... ```)
        if "```" in text:
            for block in text.split("```"):
                block = block.strip().lstrip("json").strip()
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue

        # Try direct parse first (the happy path)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find the outermost { ... } in case the model added surrounding text
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not extract valid JSON from AI response.\n"
            f"Raw output:\n{text}\n\n"
            f"If using Ollama, try a larger model: OLLAMA_MODEL=mistral"
        )
