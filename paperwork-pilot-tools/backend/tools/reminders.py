"""Tool: reminder creator.

Needs only a title and a due date. Refuses titles that contain personal data so
sensitive values never end up in reminders.
"""
import re
from datetime import date

from ._common import ok, error, find_placeholders

SPEC = {
    "name": "reminders",
    "description": "Create a reminder with a title and due date.",
    "needs_real_values": False,
}

# Phone-style (10 digits) or Aadhaar-style (12 digits) numbers
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
