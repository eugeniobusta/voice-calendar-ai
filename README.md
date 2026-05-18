# 🎙️ Voice Calendar AI

> Speak or type naturally — events appear in your calendar instantly.
> Works from your phone, your Mac, Apple Watch, Siri, or Telegram. **100% free.**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/AI-Groq%20%2B%20Llama%203.3-F55036?style=flat)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)
![Cost](https://img.shields.io/badge/Cost-$0-22c55e?style=flat)

---

## ✨ What it does

Say this:
> *"Dentist Thursday at 2pm, gym every Monday 7am, remind me to send the report by Friday"*

Get this — automatically, in seconds:

```
✓ Event:    Dentist       → Thu May 21 · 14:00  →  Personal
✓ Event:    Gym session   → Mon May 18 · 07:00  →  Gym
✓ Reminder: Send report   → Due Fri May 22
```

---

## 🏗️ How it works

```
📱 Phone / Mac / Watch / Telegram
      │
      ├─ Voice note  ──→  🎙 Groq Whisper API  ──→  transcript
      └─ Text input  ─────────────────────────────────────┐
                                                          ▼
                                                  🤖 Llama 3.3 70B
                                                  detects events, dates,
                                                  times, and right calendar
                                                          │
                                                  ✅ Pydantic validator
                                                          │
                                        ┌─────────────────┴──────────────┐
                                        ▼                                ▼
                                 📅 Google Calendar           📋 Tasks/Reminders
                                   (timed events)              (all-day events)
                                        │
                                 syncs automatically
                                        ▼
                                 📱 iPhone Calendar app
```

---

## 🛠️ Tech stack

| Layer | Tool | Why |
|---|---|---|
| 🎙️ Speech-to-text | Groq Whisper API | Free, fast, no install |
| 🤖 AI parsing | Llama 3.3 70B via Groq | Free, understands natural language |
| ✅ Validation | Pydantic | Catches bad AI output before it causes errors |
| 📅 Calendar | Google Calendar API | Works from cloud, syncs to iPhone |
| 🌐 Web server | Flask + Gunicorn | Lightweight Python framework |
| 🖥️ CLI | Python + AppleScript | Direct Mac terminal use, offline |
| 🤖 Local AI | Ollama (optional) | 100% offline — no internet needed |
| 💾 Logging | SQLite | Zero-setup local history database |
| ☁️ Hosting | Render (free tier) | Deploys in minutes |

---

## 🚀 Two ways to use it

### 📱 From your phone (web app)
Open your Render URL in Safari → **Share → Add to Home Screen** → instant access like a native app.

Or build an Apple Shortcut: speak an event → it goes straight to your calendar, no browser needed.

### 💻 From your Mac (CLI)
```bash
# Text input
python main.py --text "Coffee with Sarah next Tuesday at 10am at Blue Bottle"

# Voice note file
python main.py --audio ~/Downloads/recording.m4a

# View history
python main.py --history
```

---

## ✨ Web app features

| Feature | Description |
|---|---|
| 🎵 Live waveform | Canvas-based audio visualizer responds to your real voice |
| 🎉 Confetti | Particle burst animation on every successful creation |
| ⏱ Recording timer | Counts up while you speak |
| 🌈 Calendar badges | Gym = green, Exams = red, Work = blue — auto-assigned |
| 📅 Today preview | Shows today's Google Calendar events at the top |
| ⚡ Quick phrases | One-tap shortcuts for your most common events |
| 📊 Stats | Total events, tasks, and most-used calendar |
| 🔄 Auto-submit | Submits automatically when you stop recording |
| 📴 Offline queue | Queues events when offline, sends when reconnected |
| 📋 Copy to clipboard | Copy any result with one tap |
| 📤 Export CSV | Download your full history as a spreadsheet |
| 🗑 Swipe to delete | Swipe left on history items to delete them |
| 🌙/☀️ Dark/light mode | System, dark, or light — remembered across sessions |
| ⚙️ Full settings | Password, timezone, default calendar, reminder time, quick phrases |

---

## 📁 Project structure

```
voice-calendar-ai/
│
├── app.py                    ← Flask web server + all API routes
├── main.py                   ← CLI entry point (Mac terminal)
├── config.py                 ← All settings, reads from .env
├── run.sh                    ← Mac Shortcut wrapper script
├── .env.example              ← Copy to .env and fill in
│
├── static/                   ← Frontend assets (served by Flask)
│   ├── css/
│   │   └── app.css           ← All styles (dark/light themes, animations)
│   └── js/
│       └── app.js            ← All JavaScript (recording, UI, API calls)
│
├── templates/
│   └── index.html            ← HTML skeleton only (287 lines)
│
├── src/                      ← Python modules
│   ├── parser.py             ← AI parsing (Groq cloud or Ollama local)
│   ├── validator.py          ← Pydantic data validation
│   ├── calendar.py           ← Apple Calendar via AppleScript (CLI only)
│   ├── google_calendar.py    ← Google Calendar API (web app)
│   ├── storage.py            ← SQLite history logging
│   ├── transcriber.py        ← Local Whisper model (CLI only)
│   ├── transcriber_cloud.py  ← Groq Whisper API (web app)
│   └── telegram_bot.py       ← Telegram bot integration
│
├── tests/
│   └── test_parser.py        ← 14 unit tests
│
├── .claude/
│   └── skills/ui-ux-pro-max/ ← Design intelligence skill (UI/UX Pro Max)
│
├── Procfile                  ← Render deployment config
└── runtime.txt               ← Python version for Render
```

---

## ⚡ Quick start

### 1 — Get a free Groq API key
Go to **[console.groq.com](https://console.groq.com)** → sign up → API Keys → Create. No credit card.

### 2 — Clone and install
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

### 4 — Run tests
```bash
pytest -v   # all 14 should pass
```

### 5 — Try the CLI
```bash
python main.py --text "Team meeting tomorrow at 3pm"
```

### 6 — Deploy to phone
See the full setup guide below.

---

## 🔧 Full setup guide

<details>
<summary><b>📱 Phone access — Google Calendar + Render deployment</b></summary>

### Step 1 — Google Calendar (one time)

1. Go to **[console.cloud.google.com](https://console.cloud.google.com)** → create a project
2. Enable **Google Calendar API**
3. **APIs & Services → Credentials → Create OAuth 2.0 Client ID** (Desktop app)
4. Download the JSON → rename to `credentials.json` → put in project root
5. **OAuth consent screen → Test users** → add your Gmail
6. Run the one-time auth script:
   ```bash
   python setup_google_auth.py
   ```
7. Copy the 3 printed values into your `.env`
8. `rm credentials.json`

### Step 2 — Deploy to Render

1. Push to GitHub: `git push`
2. Sign up at **[render.com](https://render.com)** → **New → Web Service** → connect your repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1`
5. Add all environment variables from your `.env`
6. Deploy — takes ~90 seconds

### Step 3 — Add to iPhone home screen

Open your Render URL in **Safari** → Share → **Add to Home Screen** → name it `Voice Cal`.

### Keep it awake (free)
Sign up at **[cron-job.org](https://cron-job.org)** → ping your URL every 5 minutes.
Or add `RENDER_URL` as a GitHub repo secret — the included workflow pings it automatically.

</details>

<details>
<summary><b>⚙️ Environment variables reference</b></summary>

| Variable | Where needed | Description |
|---|---|---|
| `GROQ_API_KEY` | Always | From console.groq.com |
| `GROQ_MODEL` | Always | Default: `llama-3.3-70b-versatile` |
| `AI_PROVIDER` | Always | `groq` (cloud) or `ollama` (local) |
| `APP_SECRET` | Web | Password to protect the web app |
| `TIMEZONE` | Web | e.g. `Europe/Madrid`, `America/New_York` |
| `GOOGLE_CLIENT_ID` | Web | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Web | From Google Cloud Console |
| `GOOGLE_REFRESH_TOKEN` | Web | From `setup_google_auth.py` |
| `TELEGRAM_BOT_TOKEN` | Telegram | From @BotFather |
| `TELEGRAM_CHAT_ID` | Telegram | Your chat ID (send /start to your bot) |
| `CALENDAR_NAME` | CLI only | Your Apple Calendar name |
| `WHISPER_MODEL` | CLI only | `tiny` / `base` / `small` |
| `OLLAMA_MODEL` | Local AI | Default: `llama3.2` |

</details>

<details>
<summary><b>🍎 Apple Shortcuts — phone and Mac</b></summary>

### iPhone shortcut (uses web server)
1. **Ask for Input** — Text — *"What's the event?"*
2. **Get Contents of URL** — POST to `https://your-app.onrender.com/parse`
   - Body: Form — `text` = Provided Input · `secret` = your password · `timezone` = `Europe/Madrid`
3. **Get Dictionary from** Contents of URL
4. **Get Value for** `created` in Dictionary
5. **Show Notification** — "Calendar updated ✓"

### Mac shortcut (runs fully locally, no internet)
1. **Dictate Text** — Stop Listening: After Pause
2. **Run Shell Script** — `/Users/eugenio/cool_programs/voice-calendar-ai/run.sh "$*"` — Pass input: as arguments
3. **Show Result**

Add either to Siri with a phrase like *"Add to calendar"*.

</details>

<details>
<summary><b>🤖 Telegram bot</b></summary>

1. Open Telegram → **@BotFather** → `/newbot` → copy token
2. Add `TELEGRAM_BOT_TOKEN` to your `.env` and Render env vars
3. Send `/start` to your bot — it replies with your chat ID
4. Add `TELEGRAM_CHAT_ID` to Render env vars
5. Register the webhook:
   ```bash
   python setup_telegram_webhook.py
   ```

Now send any text or voice message to your bot and it creates events directly.

</details>

<details>
<summary><b>🦙 Local AI with Ollama (no internet)</b></summary>

```bash
brew install ollama
ollama pull llama3.2
ollama serve
```

In your `.env`:
```
AI_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

Everything runs on your Mac — no API key, no internet, completely private.

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
| *"Don't forget to call mom"* | 📋 Task, no date |

---

## 🧪 Tests

```bash
pytest -v   # 14 unit tests
```

---

## 🗺️ Roadmap

- [ ] Multi-user support with Google login
- [ ] Native iOS app (SwiftUI + on-device AI)
- [ ] Recurring event full support in Google Calendar
- [ ] Conflict detection before creating

---

## 📄 License

MIT — do whatever you want with it.
