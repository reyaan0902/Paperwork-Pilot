"""Tool: look up what a workflow (passport, scholarship, wifi...) needs.

Declares required fields only. It never receives user data.
Templates live in backend/data/templates/<workflow>.json (owned by person 4).
"""
import json
from pathlib import Path

from .base import ok, error

TOOL_SPEC = {
    "name": "requirements_search",
    "description": "Return required fields, documents and steps for a workflow.",
    "required_fields": [],
    "optional_fields": [],
    "needs_real_values": False,
}

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "data" / "templates"


def run(args: dict, resolve=None) -> dict:
    workflow = str(args.get("workflow", "")).strip().lower()
    if not workflow or not workflow.replace("_", "").isalnum():
        return error("Invalid or missing 'workflow'.")

    path = TEMPLATE_DIR / f"{workflow}.json"
    if not path.exists():
        return error(f"No template found for workflow '{workflow}'.")

    template = json.loads(path.read_text(encoding="utf-8"))
    result = {
        "workflow": workflow,
        "required_fields": template.get("required_fields", []),
        "required_documents": template.get("required_documents", []),
        "steps": template.get("steps", []),
    }
    return ok(result)
