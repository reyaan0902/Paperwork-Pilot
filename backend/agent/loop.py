import json
import os
from datetime import date, timedelta

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"
MAX_REPLANS = 2

# The names the AI, the plan and the frontend use (the "contract" names)
TOOL_NAMES = ["search_requirements", "make_checklist", "draft_email", "set_reminder"]

# Contract name -> the name Person 3 used in backend/tools
REAL_TOOL_NAME = {
    "search_requirements": "search",
    "make_checklist": "checklist",
    "draft_email": "drafts",
    "set_reminder": "reminders",
}

try:
    from tools import TOOLS as REAL_TOOLS   # Person 3's real tools
except ImportError:
    REAL_TOOLS = {}


# ---------- WHICH PAPERWORK PROCESS IS THIS? ----------
WORKFLOW_WORDS = {
    "passport": ["passport"],
    "scholarship": ["scholar"],
    "wifi": ["wifi", "wi-fi", "wi fi", "internet", "network"],
}


def detect_workflow(goal):
    """Match the goal to one of the stored templates. None means we have no template."""
    text = goal.lower()
    for name, words in WORKFLOW_WORDS.items():
        if any(w in text for w in words):
            return name
    return None


_requirements_cache = {}


def get_requirements(goal):
    """For goals with no template, ask the AI what is needed, so any goal can work."""
    if goal in _requirements_cache:
        return _requirements_cache[goal]
    prompt = f"""The user wants to get this done: "{goal}"
List what they will need. Reply ONLY with JSON in this format:
{{"required_fields": ["..."], "required_documents": ["..."], "steps": ["..."]}}
Use 3 to 6 short items in each list. Never invent personal details."""
    try:
        data = ask_for_json(prompt)
        result = {k: [str(x) for x in data.get(k, [])][:8]
                  for k in ("required_fields", "required_documents", "steps")}
    except Exception:
        result = {
            "required_fields": ["Full name", "Phone number"],
            "required_documents": ["ID proof", "Address proof"],
            "steps": ["Find the official website", "Fill in the form", "Submit it and keep the receipt"],
        }
    _requirements_cache[goal] = result
    return result


# ---------- TOOLS ----------
def _resolve(text):
    """Fills placeholders like [PHONE_1] with real values.
    There is no private vault yet, so placeholders stay as they are."""
    return text


def call_tool(name, args):
    """Run one tool. Falls back to a fake result if the real tool is missing."""
    if "_generated" in args:                      # goal with no template: AI-made requirements
        info = args["_generated"]
        if name == "search_requirements":
            output = {"workflow": "custom", **info}
        else:
            docs = info["required_documents"]
            output = {"workflow": "custom", "missing": docs,
                      "checklist": [{"document": d, "status": "missing"} for d in docs]}
        return {"status": "ok", "output": output, "fields_used": []}
    real = REAL_TOOLS.get(REAL_TOOL_NAME[name])
    if real is None:
        return {"status": "ok", "output": f"(fake result from {name})", "fields_used": []}
    return real(args, resolve=_resolve)


def build_args(task, goal):
    """Person 3's tools expect specific inputs. Build them from the task."""
    tool = task["tool"]
    if tool in ("search_requirements", "make_checklist"):
        workflow = detect_workflow(goal)
        args = {"workflow": workflow} if workflow else {"_generated": get_requirements(goal)}
        if tool == "make_checklist":
            args["available_documents"] = []
        return args
    if tool == "draft_email":
        draft = task.get("preview") or write_draft(goal, task["title"])
        return {"subject": draft["subject"], "body": draft["body"]}
    if tool == "set_reminder":
        due = date.today() + timedelta(days=7)
        return {"title": task["title"], "due_date": due.isoformat()}
    return {}


# ---------- HELPERS ----------
def ask_for_json(prompt):
    """Ask Groq and get a Python dict back."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def ask_for_tasks(prompt):
    return ask_for_json(prompt)["tasks"]


def build_tasks(items, start_number, added_by_agent=False):
    """Turn the AI's list into tasks in our contract format."""
    tasks = []
    for i, t in enumerate(items, start=start_number):
        tool = t.get("tool")
        if tool not in TOOL_NAMES:      # safety: AI picked a tool that doesn't exist
            tool = "make_checklist"
        task = {
            "id": f"t{i}",
            "title": t["title"],
            "status": "pending",
            "tool": tool,
            "needs_approval": bool(t.get("needs_approval", False)),
            "result": None,
        }
        if added_by_agent:
            task["added_by_agent"] = True   # the frontend shows a badge for these
        tasks.append(task)
    return tasks


def write_draft(goal, title):
    """Ask the AI to write the email/form text. Personal details stay as placeholders."""
    prompt = f"""The user's goal: "{goal}"
Write the text for this step: "{title}"
Rules:
- Never invent personal details. Use placeholders such as [FULL_NAME_1], [PHONE_1], [ADDRESS_1].
- Keep it short and polite.
Reply ONLY with JSON in this format: {{"subject": "...", "body": "..."}}"""
    try:
        data = ask_for_json(prompt)
        return {"to": "", "subject": str(data["subject"]), "body": str(data["body"])}
    except Exception:
        return {
            "to": "",
            "subject": title,
            "body": f"Hello,\n\nI am [FULL_NAME_1] and I need help with: {goal}.\nPlease contact me on [PHONE_1].\n\nThank you.",
        }


# ---------- STEP 1: UNDERSTAND + PLAN ----------
def create_plan(goal):
    prompt = f"""The user wants to get this done: "{goal}"
Break it into 4 to 6 tasks. Reply ONLY with JSON in this format:
{{"tasks": [{{"title": "...", "tool": "...", "needs_approval": false}}]}}
"tool" must be one of: {TOOL_NAMES}.
Set needs_approval to true for anything consequential, like sending an email or submitting something."""
    return build_tasks(ask_for_tasks(prompt), start_number=1)


# ---------- STEP 2: ADAPT ----------
def replan(plan, failed_task, reason):
    """Ask the AI for replacement tasks. Returns True if the plan was changed."""
    if plan.get("replans", 0) >= MAX_REPLANS:
        return False

    prompt = f"""The user's goal: "{plan['goal']}"
This task could not be completed: "{failed_task['title']}"
Reason: {reason}
Suggest 1 to 3 replacement tasks that still move the user toward the goal but avoid this problem.
Reply ONLY with JSON in this format:
{{"tasks": [{{"title": "...", "tool": "...", "needs_approval": false}}]}}
"tool" must be one of: {TOOL_NAMES}.
Set needs_approval to true for anything consequential."""

    new_tasks = build_tasks(
        ask_for_tasks(prompt),
        start_number=len(plan["tasks"]) + 1,
        added_by_agent=True,
    )

    position = plan["tasks"].index(failed_task)
    plan["tasks"][position + 1:position + 1] = new_tasks   # insert right after the failed task
    failed_task["replaced"] = True                          # so the loop skips it from now on
    plan["replans"] = plan.get("replans", 0) + 1
    return True


# ---------- STEP 3: RUN + CHECK ----------
def run_task(task, goal):
    task["status"] = "running"
    try:
        result = call_tool(task["tool"], build_args(task, goal))
        task["fields_used"] = result.get("fields_used", [])
        if result.get("status") == "ok":
            task["result"] = result["output"]
            task["status"] = "done"
        else:
            task["status"] = "failed"
            task["result"] = result.get("output")
    except Exception as e:
        task["status"] = "failed"
        task["result"] = str(e)


def advance(plan):
    """Run tasks one by one. Stop when one needs approval. Replan when one fails."""
    for task in plan["tasks"]:
        if task["status"] == "done" or task.get("replaced"):
            continue
        if task["status"] in ("needs_approval", "failed"):
            return
        if task["needs_approval"]:
            task["status"] = "needs_approval"   # pause, wait for the human
            if task["tool"] == "draft_email" and not task.get("preview"):
                task["preview"] = write_draft(plan["goal"], task["title"])   # so the human can read it first
            return
        run_task(task, plan["goal"])
        if task["status"] == "failed":
            if replan(plan, task, task["result"]):
                advance(plan)                   # continue with the new tasks
            return


# ---------- STEP 4: HUMAN DECISION ----------
def handle_approval(plan, task_id, approved, feedback="", edits=None):
    for task in plan["tasks"]:
        if task["id"] == task_id and task["status"] == "needs_approval":
            if approved:
                if edits and isinstance(task.get("preview"), dict):    # the user edited the email
                    for key in ("to", "subject", "body"):
                        if isinstance(edits.get(key), str):
                            task["preview"][key] = edits[key][:5000]
                run_task(task, plan["goal"])
                if task["status"] == "done":
                    advance(plan)
                elif replan(plan, task, task["result"]):
                    advance(plan)
            else:
                task["status"] = "failed"
                task["result"] = "Rejected by user"
                reason = "The user rejected this action"
                if feedback.strip():
                    reason += f". The user said: {feedback.strip()}"
                if replan(plan, task, reason):
                    advance(plan)               # the agent adapts instead of giving up
            return
