import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"
MAX_REPLANS = 2
TOOL_NAMES = ["search_requirements", "make_checklist", "draft_email", "set_reminder"]


# ---------- TOOLS (fake until Person 3 finishes) ----------
def _fake_tool(name):
    def run(args):
        return {"ok": True, "output": f"(fake result from {name})"}
    return run

TOOLS = {name: _fake_tool(name) for name in TOOL_NAMES}

try:
    from tools import TOOLS as REAL_TOOLS   # Person 3's real tools
    TOOLS.update(REAL_TOOLS)                # real ones replace fake ones
except ImportError:
    pass


# ---------- HELPERS ----------
def ask_for_tasks(prompt):
    """Ask Groq for a JSON list of tasks."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)["tasks"]


def build_tasks(items, start_number):
    """Turn the AI's list into tasks in our contract format."""
    tasks = []
    for i, t in enumerate(items, start=start_number):
        tool = t.get("tool")
        if tool not in TOOL_NAMES:      # safety: AI picked a tool that doesn't exist
            tool = "make_checklist"
        tasks.append({
            "id": f"t{i}",
            "title": t["title"],
            "status": "pending",
            "tool": tool,
            "needs_approval": bool(t.get("needs_approval", False)),
            "result": None,
        })
    return tasks


# ---------- STEP 1: UNDERSTAND + PLAN ----------
def create_plan(goal):
    prompt = f"""The user wants to get this done: "{goal}"
Break it into 4 to 6 tasks. Reply ONLY with JSON in this format:
{{"tasks": [{{"title": "...", "tool": "...", "needs_approval": false}}]}}
"tool" must be one of: {TOOL_NAMES}.
Set needs_approval to true for anything consequential, like sending an email or submitting something."""
    return build_tasks(ask_for_tasks(prompt), start_number=1)


# ---------- STEP 2: ADAPT (new) ----------
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

    new_tasks = build_tasks(ask_for_tasks(prompt), start_number=len(plan["tasks"]) + 1)

    position = plan["tasks"].index(failed_task)
    plan["tasks"][position + 1:position + 1] = new_tasks   # insert right after the failed task
    failed_task["replaced"] = True                          # so the loop skips it from now on
    plan["replans"] = plan.get("replans", 0) + 1
    return True


# ---------- STEP 3: RUN + CHECK ----------
def run_task(task, goal):
    task["status"] = "running"
    try:
        result = TOOLS[task["tool"]]({"goal": goal, "title": task["title"]})
        if result.get("ok"):
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
            return
        run_task(task, plan["goal"])
        if task["status"] == "failed":
            if replan(plan, task, task["result"]):
                advance(plan)                   # continue with the new tasks
            return


# ---------- STEP 4: HUMAN DECISION ----------
def handle_approval(plan, task_id, approved):
    for task in plan["tasks"]:
        if task["id"] == task_id and task["status"] == "needs_approval":
            if approved:
                run_task(task, plan["goal"])
                if task["status"] == "done":
                    advance(plan)
                elif replan(plan, task, task["result"]):
                    advance(plan)
            else:
                task["status"] = "failed"
                task["result"] = "Rejected by user"
                if replan(plan, task, "The user rejected this action"):
                    advance(plan)               # the agent adapts instead of giving up
            return
