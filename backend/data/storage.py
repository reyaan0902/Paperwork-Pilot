import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOWS_DIR = os.path.join(DATA_DIR, "workflows")
PLANS_FILE = os.path.join(DATA_DIR, "active_plans.json")
APPROVAL_LOG_FILE = os.path.join(DATA_DIR, "approval_log.json")


def _load_json(filepath: str, default: any) -> any:
    if not os.path.exists(filepath):
        return default
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def _save_json(filepath: str, data: any) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_template(workflow_type: str) -> dict:
    """Loads a default workflow template (passport, scholarship, wifi)."""
    template_path = os.path.join(WORKFLOWS_DIR, f"{workflow_type}.json")
    if os.path.exists(template_path):
        return _load_json(template_path, {})
    return _load_json(os.path.join(WORKFLOWS_DIR, "passport.json"), {})


def save_plan(plan_data: dict) -> str:
    """Saves or updates a plan, assigning a plan_id if not present."""
    plans = _load_json(PLANS_FILE, {})
    plan_id = plan_data.get("plan_id") or f"plan_{uuid.uuid4().hex[:8]}"
    plan_data["plan_id"] = plan_id
    plan_data["updated_at"] = datetime.utcnow().isoformat()
    plans[plan_id] = plan_data
    _save_json(PLANS_FILE, plans)
    return plan_id


def get_plan(plan_id: str) -> dict:
    """Returns a specific plan for Person 2's GET /plans/{plan_id} endpoint."""
    plans = _load_json(PLANS_FILE, {})
    return plans.get(plan_id)


def log_approval(plan_id: str, task_id: str, approved: bool) -> None:
    """Audit trail logging the human-in-the-loop decision."""
    logs = _load_json(APPROVAL_LOG_FILE, [])
    logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "plan_id": plan_id,
        "task_id": task_id,
        "approved": approved
    })
    _save_json(APPROVAL_LOG_FILE, logs)
