"""
google_calendar.py — Creates events in Google Calendar via the official API.

WHY GOOGLE CALENDAR INSTEAD OF APPLE CALENDAR FOR THE WEB APP?
  Apple Calendar is controlled via AppleScript — a Mac-only scripting language.
  The cloud server (Render) runs Linux. No Mac, no AppleScript.

  Google Calendar has a full REST API (HTTP requests) accessible from anywhere.
  Events created here appear on:
    - Google Calendar web (calendar.google.com)
    - iPhone Calendar app  (if you add your Google account: Settings → Calendar → Accounts)
    - Mac Calendar app     (if you add your Google account: Calendar → Preferences → Accounts)

AUTHENTICATION — HOW OAUTH 2.0 WORKS:
  OAuth is the standard way for apps to access your Google account without
  storing your password. Here's the flow:

  1. ONE TIME, on your Mac: you run setup_google_auth.py
     → A browser opens, you log into Google, click "Allow"
     → Google gives back a "refresh token" — a permanent credential

  2. EVERY TIME the app runs:
     → It uses the refresh token to get a short-lived "access token" (1 hour)
     → google-auth does this automatically behind the scenes
     → You never log in again

  Think of it like:
    Refresh token = a master key (long-lived, stored in .env)
    Access token  = a copy of the key (expires in 1 hour, auto-renewed)

TASKS AS ALL-DAY EVENTS:
  Google Tasks is a separate API requiring additional OAuth scopes.
  To keep this simple, tasks are created as all-day calendar events
  with a 📋 emoji prefix so they're visually distinct.
"""
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import date as date_type, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .validator import Event, Task


class GoogleCalendarWriter:
    def __init__(self, config, timezone: str = None):
        """
        Builds the Google Calendar API service object.

        The Credentials object holds the OAuth tokens. We pass the refresh_token
        so google-auth can get a fresh access_token automatically when needed.
        """
        self.timezone = timezone or config.timezone

        creds = Credentials(
            token=None,                                        # no current access token yet
            refresh_token=config.google_refresh_token,         # our permanent credential
            token_uri="https://oauth2.googleapis.com/token",
            client_id=config.google_client_id,
            client_secret=config.google_client_secret,
        )

        # Exchange the refresh token for a fresh access token.
        # After this, creds.token is valid and creds.expiry tells us when it expires.
        creds.refresh(Request())

        # build() creates the API client.
        # "calendar" = Google Calendar API, "v3" = version 3 (current)
        self.service = build("calendar", "v3", credentials=creds)

    def create_event(self, event: Event):
        """
        Creates a timed event in Google Calendar.

        Google Calendar API expects:
          - dateTime in ISO 8601 format: "2026-05-20T14:00:00"
          - timeZone as an IANA string: "America/New_York"
          - reminders as a list of {"method": "popup", "minutes": N}
        """
        if not event.date:
            print(f"  Skipping '{event.title}' — no date found")
            return

        start_time = event.start_time or "09:00"
        end_time   = event.end_time   or self._add_hour(start_time)

        body = {
            "summary": event.title,
            "start": {
                "dateTime": f"{event.date}T{start_time}:00",
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": f"{event.date}T{end_time}:00",
                "timeZone": self.timezone,
            },
        }

        if event.location:
            body["location"] = event.location

        if event.reminders:
            body["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": m}
                    for m in event.reminders
                ],
            }

        # calendarId="primary" inserts into the user's main calendar
        self.service.events().insert(calendarId="primary", body=body).execute()

    def create_task(self, task: Task):
        """
        Creates a task as an all-day Google Calendar event.

        All-day events use "date" (not "dateTime") in the Google API.
        The end date must be the day AFTER the start for a single-day event.
        """
        # If no deadline, create it on today so it's not lost
        target_date = task.deadline or date_type.today().isoformat()

        # Google Calendar's end date for all-day events is EXCLUSIVE —
        # it means "up to but not including this date".
        # So a single-day event on May 18 needs start="2026-05-18", end="2026-05-19".
        # Setting start == end gives an empty range and a 400 error.
        end_date = (date_type.fromisoformat(target_date) + timedelta(days=1)).isoformat()

        body = {
            "summary": f"📋 {task.title}",
            "start": {"date": target_date},
            "end":   {"date": end_date},
        }

        self.service.events().insert(calendarId="primary", body=body).execute()

    def get_today_events(self, timezone_str: str = "UTC") -> list:
        """Returns today's events from the primary Google Calendar."""
        try:
            tz = ZoneInfo(timezone_str)
        except (ZoneInfoNotFoundError, Exception):
            tz = ZoneInfo("UTC")

        now   = datetime.now(tz)
        start = now.replace(hour=0,  minute=0,  second=0,  microsecond=0)
        end   = now.replace(hour=23, minute=59, second=59, microsecond=0)

        result = self.service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=15,
        ).execute()

        events = []
        for e in result.get("items", []):
            start_raw = e["start"].get("dateTime", e["start"].get("date", ""))
            time_str  = ""
            if "T" in start_raw:
                try:
                    dt = datetime.fromisoformat(start_raw)
                    time_str = dt.strftime("%H:%M")
                except Exception:
                    pass
            events.append({
                "title":  e.get("summary", "Untitled"),
                "time":   time_str,
                "allDay": "date" in e["start"],
            })
        return events

    def list_google_calendars(self) -> list:
        """Returns all calendars in the user's Google account with colors."""
        result = self.service.calendarList().list().execute()
        return [
            {
                "id":      c["id"],
                "name":    c["summary"],
                "color":   c.get("backgroundColor", "#0D9488"),
                "primary": c.get("primary", False),
            }
            for c in result.get("items", [])
        ]

    def _add_hour(self, time_str: str) -> str:
        """Adds 1 hour to a HH:MM string."""
        h, m = map(int, time_str.split(":"))
        return f"{(h + 1) % 24:02d}:{m:02d}"
