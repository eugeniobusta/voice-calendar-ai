# 🎙️ Voice Calendar AI

> Speak or type naturally — events appear in your calendar instantly.
> Works from your phone, your Mac, or Siri. **100% free.**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/AI-Groq%20%2B%20Llama%203.3-F55036?style=flat)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)
![Cost](https://img.shields.io/badge/Cost-$0-22c55e?style=flat)

---

## ✨ What it does

Say this:
> *"Dentist Thursday at 2pm, team standup every Monday 9am at the office, and remind me to send the report by Friday"*

Get this — automatically, in seconds:

```
✓ Event:    Dentist          → Thu May 21 · 14:00
✓ Event:    Team standup     → Mon May 18 · 09:00 · Office
✓ Reminder: Send the report  → Due Fri May 22
```

---

## 🏗️ How it works

```
📱 iPhone / Mac
      │
      ├─ Voice note  ──→  🎙 Groq Whisper API  ──→  transcript
      └─ Text input  ──────────────────────────────────────┐
                                                           ▼
                                                   🤖 Llama 3.3 70B
                                                   (extracts events)
                                                           │
                                                   ✅ Pydantic validator
                                                           │
                                         ┌─────────────────┴──────────────────┐
                                         ▼                                    ▼
                                  📅 Google Calendar               📋 Google Calendar
                                    (timed events)                  (tasks / reminders)
                                         │
                                  syncs automatically
                                         │
                                         ▼
                                  📱 iPhone Calendar app
```

---

## 🛠️ Tech stack

| Layer | Tool | Why |
|---|---|---|
| 🎙️ Speech-to-text | Groq Whisper API | Free, fast, cloud-based |
| 🤖 AI parsing | Llama 3.3 70B via Groq | Free, understands natural language |
| ✅ Validation | Pydantic | Catches bad AI output before it breaks things |
| 📅 Calendar | Google Calendar API | Works from anywhere, syncs to iPhone |
| 🌐 Web server | Flask + Gunicorn | Simple Python web framework |
| 🖥️ CLI | Python + AppleScript | Direct Mac terminal use |
| 💾 Logging | SQLite | Zero-setup local history |
| ☁️ Hosting | Render (free tier) | Deploys in minutes |

---

## 🚀 Two ways to use it

### 📱 From your phone (web app)
Open your Render URL in Safari → add to home screen → use like a native app.
Or set up an Apple Shortcut to trigger it from Siri.

### 💻 From your Mac (CLI)
```bash
# Text
python main.py --text "Coffee with Sarah next Tuesday at 10am at Blue Bottle"

# Voice note
python main.py --audio ~/Downloads/recording.m4a

# History
python main.py --history
```

---

## 📁 Project structure

```
voice-calendar-ai/
│
├── 🚀 main.py                 ← CLI entry point (Mac terminal)
├── 🌐 app.py                  ← Web server (Flask, for phone access)
├── ⚙️  config.py               ← All settings, reads from .env
├── 🔐 .env.example            ← Template — copy to .env and fill in
│
├── src/
│   ├── 🎙️  transcriber.py      ← Local Whisper (CLI)
│   ├── ☁️  transcriber_cloud.py ← Groq Whisper API (web app)
│   ├── 🤖 parser.py           ← Groq AI → structured JSON
│   ├── ✅ validator.py         ← Validates AI output (Pydantic)
│   ├── 📅 calendar.py         ← Apple Calendar via AppleScript (CLI)
│   ├── 📅 google_calendar.py  ← Google Calendar API (web app)
│   └── 💾 storage.py          ← SQLite logging
│
├── templates/
│   └── 🎨 index.html          ← Mobile-friendly web UI
│
└── tests/
    └── 🧪 test_parser.py      ← 14 unit tests
```

---

## ⚡ Quick start

### 1 — Get your free API key
Sign up at **[console.groq.com](https://console.groq.com)** — no credit card, takes 2 minutes.

### 2 — Clone & install
```bash
git clone https://github.com/YOUR_USERNAME/voice-calendar-ai.git
cd voice-calendar-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3 — Configure
```bash
cp .env.example .env
open -e .env   # add your Groq key and settings
```

### 4 — Run the CLI
```bash
python main.py --text "Team meeting tomorrow at 3pm"
```

### 5 — Deploy to phone (optional)
See the [full setup guide](#full-setup-guide) below.

---

## 🔧 Full setup guide

<details>
<summary><b>📱 Phone access via Render + Google Calendar</b></summary>

### Google Calendar setup (one time)

1. Go to **[console.cloud.google.com](https://console.cloud.google.com)**
2. Create a project → enable **Google Calendar API**
3. **APIs & Services → Credentials → Create OAuth 2.0 Client ID** (Desktop app)
4. Download the JSON → rename to `credentials.json` → place in project root
5. Add your Gmail as a test user: **OAuth consent screen → Test users**
6. Run the auth script:
   ```bash
   python setup_google_auth.py
   ```
7. Copy the three printed values into your `.env`
8. Delete `credentials.json`

### Deploy to Render

1. Push to GitHub: `git push`
2. Sign up at **[render.com](https://render.com)** → **New → Web Service** → connect your repo
3. Settings:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1`
4. Add all environment variables from your `.env`
5. Deploy → visit your URL on iPhone → **Share → Add to Home Screen**

### Keep it awake (free)
Sign up at **[cron-job.org](https://cron-job.org)** and ping your Render URL every 5 minutes.
Or use the included GitHub Actions workflow — just add `RENDER_URL` as a repo secret.

</details>

<details>
<summary><b>⚙️ Environment variables</b></summary>

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Always | From console.groq.com |
| `GROQ_MODEL` | ✅ Always | Default: `llama-3.3-70b-versatile` |
| `APP_SECRET` | 🌐 Web only | Password to protect your web app |
| `TIMEZONE` | 🌐 Web only | e.g. `Europe/Madrid`, `America/New_York` |
| `GOOGLE_CLIENT_ID` | 🌐 Web only | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | 🌐 Web only | From Google Cloud Console |
| `GOOGLE_REFRESH_TOKEN` | 🌐 Web only | From `setup_google_auth.py` |
| `CALENDAR_NAME` | 💻 CLI only | Your Apple Calendar name |
| `WHISPER_MODEL` | 💻 CLI only | `tiny` / `base` / `small` (default: `base`) |

</details>

<details>
<summary><b>🍎 Apple Shortcuts integration</b></summary>

Create a shortcut with these actions:

1. **Ask for Input** — Text — *"What's the event?"*
2. **Get Contents of URL**
   - URL: `https://your-app.onrender.com/parse`
   - Method: `POST`
   - Body: `Form`
   - Fields: `text` = Provided Input · `secret` = your password · `timezone` = `Europe/Madrid`
3. **Get Dictionary from** Contents of URL
4. **Get Value for** `created` in Dictionary
5. **Show Notification** — title: *"Calendar updated ✓"*

Add to Siri with a phrase like *"Add to calendar"* — then just say it.

</details>

---

## 💡 What it understands

| You say | What gets created |
|---|---|
| *"Dentist Thursday at 2pm"* | 📅 Event with date & time |
| *"Team standup every Monday 9am"* | 📅 Recurring event |
| *"Coffee with Sarah at Blue Bottle on Market St"* | 📅 Event with location |
| *"Gym tomorrow 7am to 8am"* | 📅 Event with duration |
| *"Remind me to send the report by Friday"* | 📋 Task with deadline |
| *"Don't forget to call mom"* | 📋 Task (no date) |

---

## 🧪 Tests

```bash
pytest -v   # runs 14 unit tests
```

---

## 🗺️ Roadmap

- [ ] Multi-user support with Google login
- [ ] Native iOS app with on-device AI (no API costs)
- [ ] Recurring event full support
- [ ] Conflict detection

---

## 📄 License

MIT — do whatever you want with it.
