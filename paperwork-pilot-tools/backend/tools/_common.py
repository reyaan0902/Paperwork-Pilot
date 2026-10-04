"""Shared helpers for every tool in backend/tools/.

Tool contract:

    run(args: dict, resolve: Callable[[str], str]) -> dict

Every tool returns a dict with:
    status         "ok" | "error"
    output         result for local use (may contain real values; never send to the LLM)
    masked_output  result that is safe to hand back to the LLM (placeholders only)
    fields_used    placeholders the tool touched, e.g. ["[PHONE_1]"]; feeds the dashboard
"""
import re
from typing import Callable

# Placeholders such as [PHONE_1], [AADHAAR_2], [FULL_NAME_1]
PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z_]*_\d+\]")

Resolver = Callable[[str], str]


def find_placeholders(text: str) -> list[str]:
    """Unique placeholders in order of first appearance."""
    return list(dict.fromkeys(PLACEHOLDER_RE.findall(text)))


def ok(output, masked_output=None, fields_used=None) -> dict:
    return {
        "status": "ok",
        "output": output,
        "masked_output": output if masked_output is None else masked_output,
        "fields_used": fields_used or [],
    }


def error(message: str) -> dict:
    return {"status": "error", "output": message, "masked_output": message, "fields_used": []}
