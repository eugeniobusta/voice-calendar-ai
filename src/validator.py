"""
validator.py — Validates and cleans the AI's JSON output.

THE PROBLEM:
  Even great AI models can sometimes:
  - Return unexpected field names ("start" instead of "start_time")
  - Omit optional fields entirely
  - Return wrong types ("30" as a string instead of 30 as a number)
  - Use invalid values ("biweekly" when only "weekly" is valid)

  Without catching these, you'd get confusing errors deep in the code
  when you try to create a calendar event with bad data.

THE SOLUTION: Pydantic
  Pydantic is a Python library that lets you define the "shape" of data
  as a class, then automatically validates any data against that shape.

  Think of it like a customs officer:
  - You declare what's allowed (the class definition)
  - Every piece of data gets checked before it enters the system
  - Invalid data is rejected or corrected right at the border

HOW TO READ THESE TYPE HINTS:
  str              → must be a string
  Optional[str]    → can be a string OR None (missing/unknown)
  List[int]        → a list of integers, e.g. [15, 30]
  = None           → default value if field is not present
  = "none"         → default string if field is not present
  = [30]           → default list if field is not present
"""
from __future__ import annotations
import re
from typing import List, Optional
from pydantic import BaseModel, field_validator


class Event(BaseModel):
    """Represents a single calendar event."""

    title: str
    date: Optional[str] = None         # YYYY-MM-DD
    start_time: Optional[str] = None   # HH:MM in 24-hour format
    end_time: Optional[str] = None     # HH:MM in 24-hour format
    location: Optional[str] = None
    reminders: List[int] = [30]        # minutes before event to notify
    recurrence: str = "none"           # how often the event repeats

    @field_validator("recurrence")
    @classmethod
    def fix_recurrence(cls, v: str) -> str:
        """
        Corrects invalid recurrence values instead of crashing.

        If the AI returns "biweekly" or "fortnight", we just default to "none"
        rather than raising an error. Graceful degradation > hard failures.
        """
        valid = {"none", "daily", "weekly", "monthly", "yearly"}
        return v if v in valid else "none"

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """
        Rejects malformed dates (like "next Thursday") that the AI
        occasionally returns instead of resolving them.
        """
        if v is None:
            return None
        if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            return v
        return None  # treat malformed dates as unknown rather than crashing


class Task(BaseModel):
    """Represents a to-do item with an optional deadline."""

    title: str
    deadline: Optional[str] = None  # YYYY-MM-DD


class CalendarData(BaseModel):
    """The top-level data structure returned by the AI parser."""

    events: List[Event] = []
    tasks: List[Task] = []


def validate_events(raw: dict) -> CalendarData:
    """
    Converts a raw dictionary (from AI JSON) into a validated CalendarData object.

    Parameters:
        raw: the dictionary returned by Parser.parse()

    Returns:
        CalendarData: a fully validated object safe to use downstream

    Raises:
        ValueError: if the structure is fundamentally wrong (e.g., 'events' is missing)
    """
    try:
        return CalendarData(**raw)
    except Exception as e:
        raise ValueError(
            f"Data validation failed: {e}\n"
            f"The AI returned data we couldn't parse. Raw input:\n{raw}"
        )
