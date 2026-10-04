"""Tool: email / form draft generator.

The LLM writes the text using placeholders ([PHONE_1] ...). This tool fills in the
real values LOCALLY via `resolve`, after the LLM step. The LLM only ever sees
`masked_output`.
"""
from ._common import ok, error, find_placeholders

SPEC = {
    "name": "drafts",
    "description": "Fill an email/form draft with real values locally.",
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
