"""Tool: draft an email / form text.

The LLM writes the body using placeholders ([PHONE_1] ...). This tool fills the
real values in LOCALLY via `resolve`, after the LLM step. The LLM only ever sees
`masked_output`.
"""
from .base import ok, error, find_placeholders

TOOL_SPEC = {
    "name": "draft_email",
    "description": "Fill an email/form draft with real values locally.",
    "required_fields": [],          # decided per call from the placeholders used
    "optional_fields": [],
    "needs_real_values": True,
}


def run(args: dict, resolve) -> dict:
    subject = str(args.get("subject", "")).strip()
    body = str(args.get("body", "")).strip()
    if not body:
        return error("Missing 'body'.")

    placeholders = find_placeholders(subject + "\n" + body)
    try:
        real_subject = resolve(subject)
        real_body = resolve(body)
    except KeyError as exc:
        return error(f"Unknown placeholder: {exc}")

    return ok(
        output={"subject": real_subject, "body": real_body},
        masked_output={"subject": subject, "body": body},
        fields_used=placeholders,
    )
