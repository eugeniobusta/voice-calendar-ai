"""
parser.py — Sends text to Groq AI and gets back structured JSON.

WHAT IS GROQ?
  Groq is a free cloud AI service (no credit card required).
  It runs open-source models like Llama 3.3 70B — very capable models
  that were released by Meta and are free to use.

  Free tier limits (more than enough for personal use):
    - 30 requests per minute
    - 14,400 requests per day
    - No credit card, no billing, no expiry

  Sign up at: https://console.groq.com

WHY DO WE NEED AI FOR THIS?
  Human language is full of ambiguity that simple code can't handle:
  ✗ "Let's meet next Tuesday-ish around 3" — vague time, relative date
  ✗ "Dentist appt" — no time, no date
  ✗ "Every Monday morning" — recurring pattern
  ✗ "Don't forget to call mom" — task, not an event

  Rule-based parsing (regex, etc.) would need hundreds of edge-case rules
  and would still fail constantly. LLMs understand intent the way humans do.

HOW WE ENFORCE STRICT JSON OUTPUT:
  1. System prompt tells the model to ONLY output raw JSON
  2. We strip markdown fences (```json...```) if they appear anyway
  3. json.loads() validates the syntax
  4. Pydantic (validator.py) validates the structure and types
"""
import json
from datetime import date
from groq import Groq


SYSTEM_PROMPT = """You are a calendar assistant that extracts events and tasks from natural language.

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

WHAT IS AN EVENT vs A TASK?
  Event: has a specific date/time ("meeting at 3pm", "dentist Thursday")
  Task: something to do without a fixed time ("buy groceries", "send report")

OUTPUT — return exactly this JSON structure (nothing else):
{
  "events": [
    {
      "title": "Event name",
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
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """
        Parameters:
            api_key: your Groq API key (from console.groq.com)
            model: the Groq model to use. llama-3.3-70b-versatile is the
                   best free option — very capable and fast.
        """
        self.client = Groq(api_key=api_key)
        self.model = model

    def parse(self, text: str) -> dict:
        """
        Sends text to Groq and returns a raw dict with events and tasks.

        The Groq API uses the same format as OpenAI's chat API:
          - 'system' message sets the AI's role and rules
          - 'user' message is the actual input to process
          - response.choices[0].message.content is the AI's reply

        Parameters:
            text: the message to parse (plain English)

        Returns:
            A raw Python dict (not yet validated — see validator.py)

        Raises:
            ValueError: if the AI returns something that isn't valid JSON
        """
        today = date.today().isoformat()
        user_message = f"Today's date: {today}\n\nMessage to parse:\n{text}"

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )

        raw_text = response.choices[0].message.content.strip()

        # Defensive cleanup: some models wrap output in ```json...```
        # even when told not to. Strip those fences if present.
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1]).strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"AI returned invalid JSON.\n"
                f"Parse error: {e}\n"
                f"Raw AI output was:\n{raw_text}\n\n"
                f"Try running again — this is usually a transient issue."
            )
