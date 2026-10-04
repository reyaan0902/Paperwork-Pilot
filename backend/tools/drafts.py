"""Tool: email / form draft generator.

The LLM writes the text using placeholders such as [PHONE_1] or [FULL_NAME_1].
This tool fills in the real values LOCALLY through `resolve`, after the LLM step.
The LLM only ever sees `masked_output` (placeholders), never `output`.

args: {"subject": "...", "body": "Hello, I am [FULL_NAME_1], call me on [PHONE_1]"}
"""
import re

SPEC = {
    "name": "drafts",
    "description": "Fill an email/form draft with real values locally.",
    "needs_real_values": True,
}

PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z_]*_\d+\]")


def _error(message: str) -> dict:
    return {"status": "error", "output": message, "masked_output": message, "fields_used": []}


def run(args: dict, resolve) -> dict:
    subject = str(args.get("subject", "")).strip()
    body = str(args.get("body", "")).strip()
    if not body:
        return _error("Missing 'body'.")

    # unique placeholders, in order of first appearance
    used = list(dict.fromkeys(PLACEHOLDER_RE.findall(subject + "\n" + body)))

    try:
        real_subject = resolve(subject)
        real_body = resolve(body)
    except KeyError as exc:
        return _error(f"Unknown placeholder: {exc}")

    return {
        "status": "ok",
        "output": {"subject": real_subject, "body": real_body},          # keep local
        "masked_output": {"subject": subject, "body": body},             # safe for the LLM
        "fields_used": used,                                              # for the dashboard
    }
