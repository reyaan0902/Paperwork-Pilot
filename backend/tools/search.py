"""Tool: requirements search.

Returns what a workflow (passport, scholarship, wifi) needs: required fields,
required documents and steps. It only declares requirements; it never receives
user data.

Workflow files live in backend/data/workflows/<workflow>.json (Person 4) with keys:
    required_fields, required_documents, steps
"""
import json
from pathlib import Path

SPEC = {
    "name": "search",
    "description": "Return required fields, documents and steps for a workflow.",
    "needs_real_values": False,
}

WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "data" / "workflows"


def _error(message: str) -> dict:
    return {"status": "error", "output": message, "masked_output": message, "fields_used": []}


def list_workflows() -> list[str]:
    """Names of all available workflows (file names without .json)."""
    return sorted(p.stem for p in WORKFLOW_DIR.glob("*.json"))


def _pick_workflow(args: dict) -> str:
    """Use args['workflow'] if given, else find a workflow name inside args['query']."""
    workflow = str(args.get("workflow", "")).strip().lower()
    if workflow:
        return workflow
    query = str(args.get("query", "")).lower().replace("-", "").replace("_", "")
    for name in list_workflows():
        if name.replace("-", "").replace("_", "") in query:
            return name
    return ""


def run(args: dict, resolve=None) -> dict:
    workflow = _pick_workflow(args)
    if not workflow or not workflow.replace("_", "").replace("-", "").isalnum():
        return _error(f"Missing or unknown workflow. Available: {', '.join(list_workflows()) or 'none'}.")

    path = WORKFLOW_DIR / f"{workflow}.json"
    if not path.exists():
        return _error(f"No workflow '{workflow}'. Available: {', '.join(list_workflows()) or 'none'}.")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _error(f"Workflow file '{workflow}.json' is empty or not valid JSON.")

    result = {
        "workflow": workflow,
        "required_fields": data.get("required_fields", []),
        "required_documents": data.get("required_documents", []),
        "steps": data.get("steps", []),
    }
    return {"status": "ok", "output": result, "masked_output": result, "fields_used": []}
