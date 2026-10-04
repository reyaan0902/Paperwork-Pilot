"""Tool: create a reminder.

Needs only a title and a date. Refuses anything that looks like personal data so
sensitive values never end up in reminders.
"""
import re
from datetime import date

from .base import ok, error, find_placeholders

TOOL_SPEC = {
    "name": "reminder",
    "description": "Create a reminder with a title and due date.",
    "required_fields": [],
    "optional_fields": [],
    "needs_real_values": False,
}

# 12-digit Aadhaar-style or 10-digit phone-style numbers
SENSITIVE_RE = re.compile(r"\b\d{10}\b|\b\d{4}\s?\d{4}\s?\d{4}\b")


def run(args: dict, resolve=None) -> dict:
    title = str(args.get("title", "")).strip()
    due = str(args.get("due_date", "")).strip()
    if not title or not due:
        return error("Both 'title' and 'due_date' (YYYY-MM-DD) are required.")
    if find_placeholders(title) or SENSITIVE_RE.search(title):
        return error("Reminder title must not contain personal data.")
    try:
        due_date = date.fromisoformat(due)
    except ValueError:
        return error("'due_date' must be in YYYY-MM-DD format.")

    return ok({"title": title, "due_date": due_date.isoformat()})
