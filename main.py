#!/usr/bin/env python3
"""
main.py — The entry point for Voice Calendar AI.

This is the file you run. It ties all the other modules together
and orchestrates the full pipeline from input to calendar event.

USAGE:
  python main.py --text "Team meeting tomorrow at 3pm at the office"
  python main.py --audio voice_note.m4a
  python main.py --history

PIPELINE (what happens when you run this):
  1. Parse command-line arguments (--text, --audio, or --history)
  2. Load configuration from .env file
  3. If --audio: use Whisper to transcribe audio → text  [src/transcriber.py]
  4. Send text to Groq AI → get structured JSON            [src/parser.py]
  5. Validate the JSON structure                           [src/validator.py]
  6. Create events in Apple Calendar via AppleScript       [src/calendar.py]
  7. Create reminders in Apple Reminders via AppleScript   [src/calendar.py]
  8. Log everything to SQLite database                     [src/storage.py]

WHAT IS __name__ == "__main__"?
  Every Python file has a special variable called __name__.
  When you RUN a file directly (python main.py), __name__ is "__main__".
  When a file is IMPORTED by another file, __name__ is the module name.
  This guard means main() only runs when you execute this file directly,
  not when some other file imports from it (useful for testing).
"""
import argparse
import sys

from config import Config
from src.transcriber import Transcriber
from src.parser import Parser
from src.validator import validate_events
from src.calendar import CalendarWriter
from src.storage import Storage


def main():
    args = parse_args()

    # Load all settings from .env (raises clear error if API key is missing)
    config = Config()

    # Initialize the database (creates data/ folder and events.db if needed)
    storage = Storage(config.db_path)

    # ── Handle --history flag ──────────────────────────────────────────────
    if args.history:
        storage.show_history()
        return

    # ── Step 1: Get input text ─────────────────────────────────────────────
    if args.text:
        text = args.text
        print(f"\n[INPUT] {text[:80]}{'...' if len(text) > 80 else ''}\n")

    elif args.audio:
        print(f"\n[TRANSCRIBING] {args.audio}")
        transcriber = Transcriber(model_size=config.whisper_model)
        text = transcriber.transcribe(args.audio)
        print(f"\n[TRANSCRIPT] {text}\n")

    else:
        # argparse's required=True on the group handles this,
        # but this is a safety net in case of future refactoring
        print("Error: provide --text or --audio")
        sys.exit(1)

    # ── Step 2: Read available Apple Calendars ────────────────────────────
    writer = CalendarWriter(calendar_name=config.calendar_name)
    calendars = writer.list_calendars()
    if calendars:
        print(f"[CALENDARS] Found: {', '.join(calendars)}\n")

    # ── Step 3: Parse text into structured JSON ────────────────────────────
    provider_label = f"Ollama ({config.ollama_model})" if config.ai_provider == "ollama" else f"Groq ({config.groq_model})"
    print(f"[PARSING] Sending to {provider_label}...")
    parser = Parser(config=config)
    raw_output = parser.parse(text, calendars=calendars)

    # ── Step 4: Validate the structure ────────────────────────────────────
    print("[VALIDATING] Checking data structure...")
    data = validate_events(raw_output)

    if not data.events and not data.tasks:
        print("\n⚠ No events or tasks found in this message.")
        print("  Try being more specific about dates and times.\n")
        return

    # ── Step 5: Create calendar events and reminders ───────────────────────
    print(f"[CALENDAR] Creating {len(data.events)} event(s) and {len(data.tasks)} reminder(s)...\n")

    for event in data.events:
        try:
            writer.create_event(event)
            parts = [f"'{event.title}'"]
            if event.date:       parts.append(f"on {event.date}")
            if event.start_time: parts.append(f"at {event.start_time}")
            parts.append(f"→ {event.calendar}")
            print(f"  ✓ Event: {' '.join(parts)}")
        except RuntimeError as e:
            print(f"  ✗ Failed: {e}")

    for task in data.tasks:
        try:
            writer.create_reminder(task)
            deadline = f" (due {task.deadline})" if task.deadline else ""
            print(f"  ✓ Reminder: '{task.title}'{deadline}")
        except RuntimeError as e:
            print(f"  ✗ Failed: {e}")

    # ── Step 6: Log to database ────────────────────────────────────────────
    storage.save(text, data)

    print(f"\n✓ Done! {len(data.events)} event(s) and {len(data.tasks)} reminder(s) created.")
    print(f"  Run 'python main.py --history' to see past entries.\n")


def parse_args() -> argparse.Namespace:
    """
    Defines and parses command-line arguments.

    argparse is Python's built-in library for this.
    It automatically:
    - Generates --help documentation
    - Validates that required arguments are present
    - Provides clear error messages for wrong usage
    """
    p = argparse.ArgumentParser(
        description="Convert voice notes or text into Apple Calendar events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python main.py --text "Dentist Thursday at 2pm"
  python main.py --text "Team standup every Monday 9am, send report by Friday"
  python main.py --audio voice_note.m4a
  python main.py --history
        """
    )

    # add_mutually_exclusive_group means exactly ONE of these must be provided
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--text",
        type=str,
        metavar="MESSAGE",
        help="Text message to parse into events"
    )
    group.add_argument(
        "--audio",
        type=str,
        metavar="FILE",
        help="Audio file to transcribe and parse (mp3, m4a, wav, etc.)"
    )
    group.add_argument(
        "--history",
        action="store_true",
        help="Show recent processing history from the database"
    )

    return p.parse_args()


if __name__ == "__main__":
    main()
