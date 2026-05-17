"""
tests/test_parser.py — Unit tests for the validation layer.

WHY WRITE TESTS?
  Imagine you improve the parser in 2 months. Without tests, you'd have
  to manually check every case to make sure nothing broke.
  With tests, you just run 'pytest' and get an instant green/red answer.

  Tests are also living documentation: they show exactly how functions
  are supposed to behave, better than any comment.

WHY TEST ONLY THE VALIDATOR AND NOT THE PARSER?
  The parser makes API calls to Groq, which:
  - Counts against your daily free quota
  - Requires internet access
  - Is non-deterministic (AI output varies between calls)

  The validator is pure Python logic — deterministic, free, no network.
  We test what we can test cheaply and reliably.

  Testing the parser would require "mocking" (faking) the API call.
  That's a Phase 2 addition — for now, test the validator manually
  by running the full system with a known input.

HOW TO RUN TESTS:
  pytest                          # run all tests, brief output
  pytest -v                       # verbose — shows each test name
  pytest tests/test_parser.py     # run just this file
  pytest -v -k "test_basic"       # run tests matching a name pattern
"""
import pytest
from src.validator import validate_events, CalendarData, Event, Task


class TestValidateEvents:
    """All tests for the validate_events() function."""

    def test_complete_event_passes_unchanged(self):
        """A fully-specified event should pass through without modification."""
        raw = {
            "events": [{
                "title": "Team Meeting",
                "date": "2026-05-20",
                "start_time": "14:00",
                "end_time": "15:00",
                "location": "Conference Room A",
                "reminders": [15, 30],
                "recurrence": "weekly"
            }],
            "tasks": []
        }
        result = validate_events(raw)
        assert len(result.events) == 1
        event = result.events[0]
        assert event.title == "Team Meeting"
        assert event.date == "2026-05-20"
        assert event.start_time == "14:00"
        assert event.recurrence == "weekly"

    def test_optional_fields_default_to_none(self):
        """Only 'title' is required. All other fields should default to None."""
        raw = {"events": [{"title": "Mystery Event"}], "tasks": []}
        result = validate_events(raw)
        event = result.events[0]
        assert event.date is None
        assert event.start_time is None
        assert event.end_time is None
        assert event.location is None

    def test_default_reminder_is_30_minutes(self):
        """If 'reminders' is missing, it should default to [30]."""
        raw = {"events": [{"title": "Meeting", "date": "2026-05-20"}], "tasks": []}
        result = validate_events(raw)
        assert result.events[0].reminders == [30]

    def test_default_recurrence_is_none(self):
        """If 'recurrence' is missing, it should default to 'none'."""
        raw = {"events": [{"title": "Meeting"}], "tasks": []}
        result = validate_events(raw)
        assert result.events[0].recurrence == "none"

    def test_invalid_recurrence_corrected_to_none(self):
        """
        'biweekly' is not a valid recurrence value.
        The validator should fix it to 'none' rather than crashing.
        """
        raw = {"events": [{"title": "Meeting", "recurrence": "biweekly"}], "tasks": []}
        result = validate_events(raw)
        assert result.events[0].recurrence == "none"

    def test_all_valid_recurrence_values_pass(self):
        """Every valid recurrence value should pass through unchanged."""
        for value in ["none", "daily", "weekly", "monthly", "yearly"]:
            raw = {"events": [{"title": "X", "recurrence": value}], "tasks": []}
            result = validate_events(raw)
            assert result.events[0].recurrence == value

    def test_malformed_date_becomes_none(self):
        """
        If the AI returns a non-standard date like "next Thursday" or "May 20th",
        the validator should sanitize it to None rather than crashing downstream.
        """
        raw = {"events": [{"title": "Meeting", "date": "next Thursday"}], "tasks": []}
        result = validate_events(raw)
        assert result.events[0].date is None

    def test_properly_formatted_date_passes(self):
        """A correctly formatted YYYY-MM-DD date should pass through."""
        raw = {"events": [{"title": "Meeting", "date": "2026-12-25"}], "tasks": []}
        result = validate_events(raw)
        assert result.events[0].date == "2026-12-25"

    def test_task_with_deadline(self):
        """A task with a valid deadline should pass correctly."""
        raw = {"events": [], "tasks": [{"title": "Send report", "deadline": "2026-05-25"}]}
        result = validate_events(raw)
        assert len(result.tasks) == 1
        assert result.tasks[0].title == "Send report"
        assert result.tasks[0].deadline == "2026-05-25"

    def test_task_without_deadline_defaults_to_none(self):
        """A task without a deadline should have deadline=None."""
        raw = {"events": [], "tasks": [{"title": "Buy groceries"}]}
        result = validate_events(raw)
        assert result.tasks[0].deadline is None

    def test_empty_input_returns_valid_empty_object(self):
        """Empty events and tasks lists should produce a valid CalendarData object."""
        result = validate_events({"events": [], "tasks": []})
        assert isinstance(result, CalendarData)
        assert result.events == []
        assert result.tasks == []

    def test_multiple_events_and_tasks(self):
        """All items in a mixed input should be parsed correctly."""
        raw = {
            "events": [
                {"title": "Dentist", "date": "2026-05-21", "start_time": "14:00"},
                {"title": "Gym", "date": "2026-05-22", "start_time": "07:00"},
            ],
            "tasks": [
                {"title": "Call mom"},
                {"title": "Buy milk", "deadline": "2026-05-20"},
            ]
        }
        result = validate_events(raw)
        assert len(result.events) == 2
        assert len(result.tasks) == 2
        assert result.events[0].title == "Dentist"
        assert result.tasks[1].deadline == "2026-05-20"

    def test_missing_events_key_defaults_to_empty_list(self):
        """
        If 'events' is missing, it should default to [] rather than crashing.

        WHY: The AI might return only tasks and no events — that's valid output.
        Pydantic's default (events=[]) handles this gracefully, which is correct.
        Crashing here would mean a "no events found" response breaks the whole system.
        """
        result = validate_events({"tasks": []})
        assert result.events == []

    def test_wrong_type_for_events_raises_error(self):
        """
        'events' must be a list. A string is genuinely wrong and should raise ValueError.

        WHY: Pydantic defaults empty/missing fields gracefully, but can't coerce
        a string like "none" into a list of Event objects — that's a real error.
        """
        with pytest.raises(ValueError):
            validate_events({"events": "none", "tasks": []})
