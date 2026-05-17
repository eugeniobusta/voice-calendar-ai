"""
storage.py — Logs all processed events to a local SQLite database.

WHY LOG EVERYTHING?
  1. Debugging: see exactly what the AI extracted from each message
  2. History: searchable record of every event you've ever created
  3. Safety net: if Calendar fails, your parsed data isn't lost
  4. Future features: history viewer, analytics, duplicate detection

WHAT IS SQLITE?
  SQLite is a database that lives in a single file (e.g., data/events.db).
  Unlike PostgreSQL or MySQL, it needs NO server running — just a file.
  Python includes SQLite support built-in (the 'sqlite3' module).
  It's the most widely deployed database in the world (it's in every iPhone,
  every Android phone, every browser, and most desktop apps).

DATABASE STRUCTURE:
  Table: entries
  ┌────┬─────────────────────┬──────────────────┬──────────────┬─────────┬────────────┐
  │ id │     created_at      │   input_text     │ parsed_json  │ events  │   tasks    │
  ├────┼─────────────────────┼──────────────────┼──────────────┼─────────┼────────────┤
  │  1 │ 2026-05-17T14:32:10 │ Dentist thursday │ {"events":…} │       1 │          0 │
  └────┴─────────────────────┴──────────────────┴──────────────┴─────────┴────────────┘

SQL BASICS (for beginners):
  CREATE TABLE  → defines the structure of the table (like a spreadsheet header)
  INSERT INTO   → adds a new row
  SELECT        → reads rows
  ?             → a safe placeholder that prevents SQL injection attacks
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from .validator import CalendarData


class Storage:
    def __init__(self, db_path: str):
        # Create parent directories if they don't exist (e.g., the data/ folder)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connect to the SQLite database file.
        # If the file doesn't exist, SQLite creates it automatically.
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """
        Creates the 'entries' table if it doesn't already exist.
        'IF NOT EXISTS' means this is safe to call every time — it's idempotent.
        """
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL,
                input_text  TEXT    NOT NULL,
                parsed_json TEXT    NOT NULL,
                event_count INTEGER NOT NULL DEFAULT 0,
                task_count  INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.conn.commit()

    def save(self, input_text: str, data: CalendarData):
        """
        Saves one processing run to the database.

        Parameters:
            input_text: the original message or transcript
            data: the validated CalendarData object
        """
        self.conn.execute(
            """INSERT INTO entries
               (created_at, input_text, parsed_json, event_count, task_count)
               VALUES (?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(),
                input_text,
                data.model_dump_json(),   # converts the Pydantic model to JSON string
                len(data.events),
                len(data.tasks),
            )
        )
        self.conn.commit()

    def get_recent(self, limit: int = 10) -> list[tuple]:
        """Returns the most recent entries as a list of tuples."""
        cursor = self.conn.execute(
            """SELECT created_at, event_count, task_count, input_text
               FROM entries
               ORDER BY id DESC
               LIMIT ?""",
            (limit,)
        )
        return cursor.fetchall()

    def show_history(self):
        """Prints a formatted table of recent entries to the terminal."""
        rows = self.get_recent()
        if not rows:
            print("\n  No entries yet. Run with --text to create your first one.\n")
            return

        print(f"\n{'─' * 65}")
        print(f"  {'Date':<20} {'Events':>6} {'Tasks':>5}  Input preview")
        print(f"{'─' * 65}")
        for created, events, tasks, text in rows:
            preview = text[:28].replace("\n", " ")
            print(f"  {created[:19]:<20} {events:>6} {tasks:>5}  {preview}...")
        print(f"{'─' * 65}\n")
