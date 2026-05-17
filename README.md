# Voice Calendar AI

Convert voice notes or text messages into Apple Calendar events — automatically and for free.

## Quick Demo

```bash
python main.py --text "Dentist Thursday at 2pm, team standup every Monday 9am, send the report by Friday"
```

```
[PARSING] Sending to Groq (llama-3.3-70b-versatile)...
[VALIDATING] Checking data structure...
[CALENDAR] Creating 2 event(s) and 1 reminder(s)...

  ✓ Event: 'Dentist' on 2026-05-21 at 14:00
  ✓ Event: 'Team standup' on 2026-05-18 at 09:00
  ✓ Reminder: 'Send the report' (due 2026-05-22)

✓ Done! 2 event(s) and 1 reminder(s) created.
```

---

## How It Works

```
[Voice Note] ──→ [Whisper (runs locally, free)] ──┐
                                                   ▼
[Text Input] ──────────────────────────────→ [Groq AI] ──→ [Structured JSON]
                                          (Llama 3.3 70B)
                                                                      │
                                                              [Pydantic Validator]
                                                                      │
                                             ┌────────────────────────┤
                                             ▼                        ▼
                                   [Apple Calendar]        [Apple Reminders]
                                   (via AppleScript)       (via AppleScript)
                                             └────────────────────────┘
                                                          │
                                                    [SQLite Log]
```

---

## Cost

| Component | Tool | Cost |
|---|---|---|
| Speech-to-text | Whisper (local) | Free forever |
| AI parsing | Groq — Llama 3.3 70B | Free (14,400 req/day, no card) |
| Calendar | AppleScript (built into macOS) | Free |
| Storage | SQLite (built into Python) | Free |

**Total cost: $0**

---

## Requirements

- **macOS** — Apple Calendar integration uses AppleScript, which is Mac-only
- **Python 3.9+**
- **Groq API key** — free at [console.groq.com](https://console.groq.com) (no credit card)

---

## Setup (step by step)

### Step 1 — Get your free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Click **Sign Up** — use Google or email (no credit card asked)
3. Once inside, click **API Keys** in the left sidebar
4. Click **Create API Key**, name it anything (e.g. `calendar-ai`)
5. Copy the key — it starts with `gsk_`

### Step 2 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/voice-calendar-ai.git
cd voice-calendar-ai
```

### Step 3 — Create a virtual environment

A virtual environment is an isolated space for this project's packages.
It prevents conflicts with other Python projects on your computer.

```bash
python3 -m venv venv
source venv/bin/activate
```

> You must run `source venv/bin/activate` every time you open a new terminal.
> You'll know it's active when you see `(venv)` at the start of your prompt.

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

> First run also downloads the Whisper model (~300MB). One-time only.

### Step 5 — Configure your environment

```bash
cp .env.example .env
open -e .env
```

Fill in your `.env` file:

```
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.3-70b-versatile
WHISPER_MODEL=base
CALENDAR_NAME=Home
DB_PATH=data/events.db
```

> **Finding your calendar name:** Open the Calendar app. In the left sidebar
> you'll see names like "Home", "Work", "Personal". Copy the exact name — it's case-sensitive.

### Step 6 — Run tests to verify setup

```bash
pytest -v
```

All 14 tests should pass. This confirms the code is working before you touch any APIs.

### Step 7 — Try your first real parse

```bash
python main.py --text "Coffee with Sarah next Tuesday at 10am at Blue Bottle"
```

> **First run only:** macOS will show a permission dialog:
> *"Terminal wants to control Calendar. Allow?"*
> Click **Allow**. This is a one-time security prompt.

---

## Usage

### Text input
```bash
python main.py --text "your message here"
```

### Voice note
```bash
python main.py --audio path/to/recording.m4a
```

Supported formats: `mp3`, `m4a`, `mp4`, `wav`, `flac`, `ogg`

### View history
```bash
python main.py --history
```

### Run tests
```bash
pytest -v
```

---

## What can you say?

| Input example | What it creates |
|---|---|
| `"Dentist Thursday at 2pm"` | Calendar event with date + time |
| `"Team standup every Monday 9am"` | Recurring weekly event |
| `"Coffee with Sarah next week at Blue Bottle on Market St"` | Event with location |
| `"Gym session tomorrow 7am to 8am"` | Event with explicit duration |
| `"Remind me to send the report by Friday"` | Task with deadline in Reminders |
| `"Don't forget to call mom"` | Task (no date) in Reminders |

---

## Project Structure

```
voice-calendar-ai/
├── main.py              ← Run this. Ties everything together.
├── config.py            ← All settings (reads from .env)
├── requirements.txt     ← Python packages to install
├── .env.example         ← Template for your .env file (safe to commit)
├── .env                 ← Your real secrets (NEVER commit this)
├── .gitignore           ← Tells Git to ignore .env and data/
├── src/
│   ├── transcriber.py   ← Audio → text (Whisper, runs locally)
│   ├── parser.py        ← Text → JSON (Groq AI / Llama 3.3 70B)
│   ├── validator.py     ← Validates JSON structure (Pydantic)
│   ├── calendar.py      ← Creates Apple Calendar events (AppleScript)
│   └── storage.py       ← Logs everything to SQLite
└── tests/
    └── test_parser.py   ← Unit tests (run with 'pytest')
```

---

## Troubleshooting

**"GROQ_API_KEY is missing"**
- Run `cp .env.example .env` then add your key from [console.groq.com](https://console.groq.com)

**"Calendar not found" or AppleScript error**
- Open Calendar app, check the exact name in the left sidebar
- Update `CALENDAR_NAME` in your `.env` to match exactly (case-sensitive)

**"osascript: permission denied"**
- Go to System Settings → Privacy & Security → Automation
- Allow Terminal (or your app) to control Calendar and Reminders

**Whisper takes too long**
- Change `WHISPER_MODEL=tiny` in your `.env` for faster (slightly less accurate) transcription

---

## Upgrade Roadmap

- **Phase 2:** Web interface (Flask), retry logic, `--dry-run` flag to preview without creating
- **Phase 3:** Recurring event AppleScript, Apple Shortcuts trigger from iPhone, conflict detection, fully local AI via Ollama
