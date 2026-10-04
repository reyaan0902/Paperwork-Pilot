"""Tool: requirements search.

Returns what a workflow (passport, scholarship, wifi) needs: fields, documents, steps.
Declares requirements only; it never receives user data.
Templates are read from backend/data/workflows/<workflow>.json (Person 4).
"""
import json
from pathlib import Path

from ._common import ok, error

SPEC = {
    "name": "search",
    "description": "Return required fields, documents and steps for a workflow.",
    "needs_real_values": False,
}

WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "data" / "workflows"


def run(args: dict, resolve=None) -> dict:
    workflow = str(args.get("workflow", "")).strip().lower()
    if not workflow or not workflow.replace("_", "").isalnum():
        return error("Invalid or missing 'workflow'.")

    path = WORKFLOW_DIR / f"{workflow}.json"
    if not path.exists():
        return error(f"No workflow found for '{workflow}'.")

    data = json.loads(path.read_text(encoding="utf-8"))
    return ok({
        "workflow": workflow,
        "required_fields": data.get("required_fields", []),
        "required_documents": data.get("required_documents", []),
        "steps": data.get("steps", []),
    })
