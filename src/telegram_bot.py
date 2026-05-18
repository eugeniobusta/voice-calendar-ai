"""
src/telegram_bot.py — Core Telegram bot logic.

HOW A TELEGRAM BOT WORKS:
  1. You create a bot via @BotFather on Telegram → get a token
  2. Telegram sends every incoming message to a URL you choose (a "webhook")
  3. Your server receives it, processes it, and calls the Telegram API to reply

  The webhook is just a POST request Telegram makes to:
    https://your-app.onrender.com/telegram

  Every message becomes a Python dict. We read the text or audio,
  run it through the same pipeline as the web app, and send back a reply.

WHY WE DON'T USE python-telegram-bot LIBRARY:
  That library is async (uses asyncio). Flask is synchronous.
  Mixing them adds complexity for no real benefit here.
  Calling the Telegram API directly with 'requests' is 20 lines
  and is easier to understand and debug.

VOICE MESSAGES FROM TELEGRAM:
  Telegram stores voice messages on their servers.
  When we receive a voice message, we get a file_id.
  We use that to download the audio bytes, then send them to Groq Whisper.
  Telegram voice messages are .ogg (Opus codec) — Groq supports this.

AUTHORIZATION:
  We check every incoming message against TELEGRAM_CHAT_ID.
  Only your account can use the bot.
  Your chat ID is a number — the bot tells you what it is on /start.
"""
import requests
from .transcriber_cloud import CloudTranscriber
from .parser import Parser
from .validator import validate_events
from .google_calendar import GoogleCalendarWriter
from .storage import Storage


class TelegramBot:
    def __init__(self, config):
        self.config = config
        self.token = config.telegram_bot_token
        self.allowed_id = str(config.telegram_chat_id).strip()
        self.api = f"https://api.telegram.org/bot{self.token}"

    # ── Sending ───────────────────────────────────────────────────────────

    def send(self, chat_id: int, text: str):
        """
        Sends a reply message to a Telegram chat.
        parse_mode="HTML" lets us use <b>bold</b> and <i>italic</i> in replies.
        """
        requests.post(
            f"{self.api}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )

    # ── Receiving ─────────────────────────────────────────────────────────

    def handle_update(self, data: dict) -> tuple:
        """
        Main entry point. Receives a Telegram update dict, returns (chat_id, reply).

        A Telegram "update" is a JSON object representing one incoming event
        (a message, an edit, a button press, etc.). We only care about messages.
        """
        # Telegram sends either "message" or "edited_message"
        message = data.get("message") or data.get("edited_message")
        if not message:
            return None, None

        chat_id = message["chat"]["id"]
        text_content = message.get("text", "")

        # /start is a special command — reply with the user's chat ID
        # so they can add it to TELEGRAM_CHAT_ID in their config
        if text_content == "/start":
            return chat_id, (
                f"👋 Hi! I'm your Voice Calendar bot.\n\n"
                f"Your chat ID is: <code>{chat_id}</code>\n\n"
                f"Add this as <code>TELEGRAM_CHAT_ID</code> in your Render "
                f"environment variables, then send me any event and I'll add "
                f"it straight to your Google Calendar.\n\n"
                f"<i>Example: \"Dentist Thursday 2pm, team meeting Friday 10am\"</i>"
            )

        # Reject messages from anyone who isn't you
        if self.allowed_id and str(chat_id) != self.allowed_id:
            return chat_id, "⛔ Unauthorized."

        # ── Get text from the message ──────────────────────────────────────
        text = None

        if text_content:
            # Regular text message
            text = text_content

        elif "voice" in message or "audio" in message:
            # Voice note or audio file — download and transcribe
            file_info = message.get("voice") or message.get("audio")
            file_id = file_info["file_id"]

            try:
                audio_bytes, filename = self._download_file(file_id)
                transcriber = CloudTranscriber(api_key=self.config.groq_api_key)
                text = transcriber.transcribe_bytes(audio_bytes, filename)
            except Exception as e:
                return chat_id, f"❌ Couldn't transcribe audio: {e}"

        else:
            return chat_id, (
                "Send me a text message or voice note.\n"
                "<i>Example: \"Coffee with Sarah next Tuesday 10am at Blue Bottle\"</i>"
            )

        # ── Run the pipeline ───────────────────────────────────────────────
        return chat_id, self._process(text)

    # ── Pipeline ──────────────────────────────────────────────────────────

    def _process(self, text: str) -> str:
        """
        Runs the full pipeline: text → AI → validate → Google Calendar → reply.
        Returns a formatted HTML string to send back to the user.
        """
        # Parse with Groq AI
        try:
            parser = Parser(api_key=self.config.groq_api_key, model=self.config.groq_model)
            raw  = parser.parse(text)
            data = validate_events(raw)
        except Exception as e:
            return f"❌ AI parsing failed: {e}"

        if not data.events and not data.tasks:
            return (
                "🤔 No events or tasks found.\n\n"
                "Try being more specific:\n"
                "<i>\"Dentist Thursday at 2pm\"</i>\n"
                "<i>\"Team standup every Monday 9am\"</i>"
            )

        # Create events in Google Calendar
        try:
            writer = GoogleCalendarWriter(self.config, timezone=self.config.timezone)
            lines = ["✅ <b>Added to your calendar:</b>\n"]

            for event in data.events:
                writer.create_event(event)
                line = f"📅 <b>{event.title}</b>"
                if event.date:
                    line += f"  ·  {event.date}"
                if event.start_time:
                    line += f"  ·  {event.start_time}"
                if event.location:
                    line += f"  ·  {event.location}"
                lines.append(line)

            for task in data.tasks:
                writer.create_task(task)
                deadline = f"  ·  Due {task.deadline}" if task.deadline else ""
                lines.append(f"📋 <b>{task.title}</b>{deadline}")

        except Exception as e:
            return f"❌ Calendar error: {e}"

        # Log to SQLite
        try:
            Storage(self.config.db_path).save(text, data)
        except Exception:
            pass

        return "\n".join(lines)

    # ── File download ─────────────────────────────────────────────────────

    def _download_file(self, file_id: str) -> tuple:
        """
        Downloads a file from Telegram's servers.

        HOW IT WORKS:
          1. Call getFile API → Telegram gives us a temporary file_path
          2. Download the actual bytes from the Telegram CDN
          3. Return (bytes, filename) for the transcriber

        Telegram voice messages are stored as .oga (Ogg Vorbis/Opus).
        We rename to .ogg so Groq recognises the format correctly.
        """
        # Step 1: get the file path from Telegram
        r = requests.get(
            f"{self.api}/getFile",
            params={"file_id": file_id},
            timeout=10,
        )
        r.raise_for_status()
        file_path = r.json()["result"]["file_path"]

        # Step 2: download the actual file
        download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        r2 = requests.get(download_url, timeout=30)
        r2.raise_for_status()

        # Normalise .oga → .ogg so Groq recognises the codec
        filename = file_path.split("/")[-1].replace(".oga", ".ogg")
        return r2.content, filename
