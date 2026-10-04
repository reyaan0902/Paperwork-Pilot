"""Tool: reminder creator.

Needs only a title and a due date. Refuses titles that contain personal data
(placeholders, phone-style or Aadhaar-style numbers) so sensitive values never
end up in reminders.

args: {"title": "Submit passport form", "due_date": "2026-11-01"}
"""
import re
from datetime import date

SPEC = {
    "name": "reminders",
    "description": "Create a reminder with a title and due date.",
    "needs_real_values": False,
}

PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z_]*_\d+\]")
SENSITIVE_RE = re.compile(r"\b\d{10}\b|\b\d{4}\s?\d{4}\s?\d{4}\b")  # phone / Aadhaar style


def _error(message: str) -> dict:
    return {"status": "error", "output": message, "masked_output": message, "fields_used": []}


def run(args: dict, resolve=None) -> dict:
    title = str(args.get("title", "")).strip()
    due = str(args.get("due_date", "")).strip()
    if not title or not due:
        return _error("Both 'title' and 'due_date' (YYYY-MM-DD) are required.")
    if PLACEHOLDER_RE.search(title) or SENSITIVE_RE.search(title):
        return _error("Reminder title must not contain personal data.")
    try:
        due_date = date.fromisoformat(due)
    except ValueError:
        return _error("'due_date' must be in YYYY-MM-DD format.")

    result = {"title": title, "due_date": due_date.isoformat()}
    return {"status": "ok", "output": result, "masked_output": result, "fields_used": []}
