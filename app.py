"""
app.py — Flask web server for Voice Calendar AI.

THREE ROUTES:
  GET  /          → serves the mobile web page
  POST /parse     → web app endpoint (called by browser JavaScript)
  POST /telegram  → Telegram bot webhook (called by Telegram's servers)

DEPLOYMENT:
  Locally:    python app.py     (runs on http://localhost:5001)
  Production: gunicorn app:app  (Render calls this via the Procfile)
"""
import os
from flask import Flask, request, jsonify, render_template
from config import Config
from src.parser import Parser
from src.validator import validate_events
from src.transcriber_cloud import CloudTranscriber
from src.google_calendar import GoogleCalendarWriter
from src.storage import Storage
from src.telegram_bot import TelegramBot


app = Flask(__name__)


@app.route("/")
def index():
    """
    Serves the HTML web page when you open the URL in a browser.
    Flask looks for templates in the templates/ folder automatically.
    """
    return render_template("index.html")


@app.route("/parse", methods=["POST"])
def parse():
    """
    The main processing endpoint.

    WHAT IT RECEIVES (multipart form data from the browser):
      audio    — an audio file (if user recorded/uploaded)
      text     — a text message (if user typed)
      timezone — the user's timezone from the browser (e.g. "America/New_York")
      secret   — the app password for authentication

    WHAT IT RETURNS (JSON):
      {
        "transcript": "the text that was heard or sent",
        "created": [
          {"type": "event", "title": "...", "date": "...", "time": "...", "location": "..."},
          {"type": "task",  "title": "...", "deadline": "..."}
        ]
      }

    WHY JSON RESPONSE (not HTML)?
      The browser's JavaScript calls this endpoint and reads the JSON.
      JavaScript then updates the page without reloading it.
      This is called an "AJAX" request — Asynchronous JavaScript And XML
      (though we use JSON, not XML, nowadays).
    """
    config = Config()

    # ── Authentication ─────────────────────────────────────────────────────
    # Simple shared-secret check. Not cryptographically perfect,
    # but sufficient to keep strangers from adding events to your calendar.
    if config.app_secret:
        provided = request.form.get("secret", "").strip()
        if provided != config.app_secret:
            return jsonify({"error": "Incorrect password"}), 401

    # ── Step 1: Get text ───────────────────────────────────────────────────
    text = None
    # Use user's browser timezone if provided, fall back to config default
    timezone = request.form.get("timezone", config.timezone)

    if "audio" in request.files:
        audio_file = request.files["audio"]
        if not audio_file or audio_file.filename == "":
            return jsonify({"error": "Audio file was empty"}), 400

        try:
            transcriber = CloudTranscriber(api_key=config.groq_api_key)
            text = transcriber.transcribe(audio_file)
        except Exception as e:
            return jsonify({"error": f"Transcription failed: {e}"}), 500

    elif "text" in request.form:
        text = request.form["text"].strip()
        if not text:
            return jsonify({"error": "Message was empty"}), 400

    else:
        return jsonify({"error": "Send either 'text' or 'audio'"}), 400

    # ── Step 2: Parse with Groq AI ─────────────────────────────────────────
    try:
        parser = Parser(api_key=config.groq_api_key, model=config.groq_model)
        raw    = parser.parse(text)
        data   = validate_events(raw)
    except Exception as e:
        return jsonify({"error": f"AI parsing failed: {e}"}), 500

    # ── Step 3: Create calendar events ────────────────────────────────────
    created = []
    try:
        writer = GoogleCalendarWriter(config, timezone=timezone)

        for event in data.events:
            writer.create_event(event)
            created.append({
                "type":     "event",
                "title":    event.title,
                "date":     event.date,
                "time":     event.start_time,
                "location": event.location,
            })

        for task in data.tasks:
            writer.create_task(task)
            created.append({
                "type":     "task",
                "title":    task.title,
                "deadline": task.deadline,
            })

    except Exception as e:
        return jsonify({"error": f"Calendar error: {e}"}), 500

    # ── Step 4: Log everything to SQLite ──────────────────────────────────
    try:
        Storage(config.db_path).save(text, data)
    except Exception:
        pass  # Logging failure should never break a successful request

    return jsonify({"transcript": text, "created": created})


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    """
    Telegram calls this URL every time someone messages your bot.

    HOW TELEGRAM WEBHOOKS WORK:
      When you (or anyone) send a message to your Telegram bot,
      Telegram makes a POST request to this URL with the message as JSON.
      We process it and call the Telegram API to send a reply.
      We always return HTTP 200 — if we return anything else,
      Telegram thinks delivery failed and keeps retrying.

    FLOW:
      Telegram POST → parse update → transcribe (if voice) →
      Groq AI → Google Calendar → send reply back to Telegram
    """
    config = Config()

    if not config.telegram_bot_token:
        return "", 200  # bot not configured — ignore silently

    data = request.get_json(silent=True)
    if not data:
        return "", 200

    bot = TelegramBot(config)
    chat_id, reply = bot.handle_update(data)

    if chat_id and reply:
        bot.send(chat_id, reply)

    # Always 200 — Telegram must know we received the update
    return "", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
