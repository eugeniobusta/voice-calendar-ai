"""
calendar.py — Creates events in Apple Calendar using AppleScript.

APPLE CALENDAR — HONEST EXPLANATION OF HOW INTEGRATION WORKS:
==============================================================
Apple does NOT provide a public REST API for Calendar (unlike Google Calendar).
There is no endpoint you can POST to. Apple keeps Calendar closed to third parties.

OUR SOLUTION: AppleScript
  AppleScript is a scripting language built into every Mac since 1993.
  It can control any Mac application directly, including Calendar and Reminders.

  We generate an AppleScript program as a Python string, then run it using
  the 'osascript' command-line tool that ships with macOS.

THE FLOW:
  Python string (our script) → subprocess.run(['osascript', '-e', script])
                             → macOS runs AppleScript
                             → Calendar app creates the event

WHY SET DATES COMPONENT-BY-COMPONENT?
  The most obvious approach would be: date "05/20/2026 14:00"

  But AppleScript date string parsing is LOCALE-DEPENDENT.
  In the US: MM/DD/YYYY → May 20
  In Europe: DD/MM/YYYY → the 5th of August (wrong!)

  Setting year, month, day as integers is ALWAYS unambiguous, regardless
  of the user's language or region settings.

PERMISSIONS:
  The first time Python controls Calendar via AppleScript, macOS shows
  a permission dialog: "Terminal wants to control Calendar. Allow?"
  You must click Allow. This is a one-time prompt.

ALTERNATIVES (for reference):
  - CalDAV: Apple Calendar supports CalDAV sync, but requires iCloud credentials
  - .ics files: can be imported, but not fully automated
  - Apple Shortcuts: can be triggered via URL schemes, but less reliable for scripting
  AppleScript is the most direct and reliable option on macOS.
"""
import subprocess
from .validator import Event, Task


class CalendarWriter:
    def __init__(self, calendar_name: str = "Home"):
        """
        Parameters:
            calendar_name: must match a calendar name in your Calendar app exactly.
                           Open Calendar and check the left sidebar.
        """
        self.calendar_name = calendar_name

    def create_event(self, event: Event):
        """Creates a calendar event in Apple Calendar via AppleScript."""
        if not event.date:
            print(f"    ⚠ Skipped '{event.title}' — no date could be determined")
            return

        year, month, day = event.date.split("-")
        start_h, start_m = (event.start_time or "09:00").split(":")

        # Compute end time: use provided end_time, or add 1 hour to start
        if event.end_time:
            end_h, end_m = event.end_time.split(":")
        else:
            end_h = str((int(start_h) + 1) % 24).zfill(2)
            end_m = start_m

        location_line = ""
        if event.location:
            location_line = f'set location of the_event to "{self._escape(event.location)}"'

        script = f"""
tell application "Calendar"
    tell calendar "{self.calendar_name}"
        -- Build start date by setting each numeric component individually.
        -- This avoids locale-dependent date string parsing issues.
        set start_date to current date
        set year of start_date to {int(year)}
        set month of start_date to {int(month)}
        set day of start_date to {int(day)}
        set hours of start_date to {int(start_h)}
        set minutes of start_date to {int(start_m)}
        set seconds of start_date to 0

        -- Build end date the same way
        set end_date to current date
        set year of end_date to {int(year)}
        set month of end_date to {int(month)}
        set day of end_date to {int(day)}
        set hours of end_date to {int(end_h)}
        set minutes of end_date to {int(end_m)}
        set seconds of end_date to 0

        set the_event to make new event with properties {{summary:"{self._escape(event.title)}", start date:start_date, end date:end_date}}
        {location_line}
    end tell
end tell
"""
        self._run(script, context=f"creating event '{event.title}'")

    def create_reminder(self, task: Task):
        """Creates a reminder in the Apple Reminders app via AppleScript."""
        deadline_block = ""

        if task.deadline:
            year, month, day = task.deadline.split("-")
            deadline_block = f"""
        set due_date to current date
        set year of due_date to {int(year)}
        set month of due_date to {int(month)}
        set day of due_date to {int(day)}
        set hours of due_date to 9
        set minutes of due_date to 0
        set seconds of due_date to 0
        set due date of the_reminder to due_date"""

        script = f"""
tell application "Reminders"
    tell default list
        set the_reminder to make new reminder with properties {{name:"{self._escape(task.title)}"}}
        {deadline_block}
    end tell
end tell
"""
        self._run(script, context=f"creating reminder '{task.title}'")

    def _escape(self, text: str) -> str:
        """
        Escapes special characters for AppleScript string literals.

        AppleScript strings use double quotes. If the event title contains
        a double quote (e.g., 3" Meeting), it would break the script.
        We escape backslashes first, then quotes.
        """
        if not text:
            return ""
        return text.replace("\\", "\\\\").replace('"', '\\"')

    def _run(self, script: str, context: str = ""):
        """
        Runs an AppleScript and raises a clear error if it fails.

        subprocess.run() is Python's way of running shell commands.
        capture_output=True captures stdout/stderr instead of printing them.
        text=True decodes bytes to strings automatically.
        """
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            error = result.stderr.strip()
            raise RuntimeError(
                f"AppleScript failed while {context}.\n"
                f"Error: {error}\n\n"
                f"Common fixes:\n"
                f"  - Check that '{self.calendar_name}' exists in your Calendar app\n"
                f"  - Make sure Terminal has permission to control Calendar\n"
                f"    (System Preferences → Privacy & Security → Automation)"
            )
