import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

import auth
from agent.loop import advance, create_plan, handle_approval
from data.storage import get_plan as load_plan, list_plans, log_approval, save_plan
from db import supabase

app = FastAPI()

# lets the React app (Vite runs on port 5173) talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sync_plan_to_supabase(plan: dict, user_email: str = ""):
    """Helper to upsert plan data into the Supabase 'plans' table."""
    try:
        payload = {
            "plan_id": str(plan["plan_id"]),
            "owner": str(plan["owner"]),
            "user_email": user_email or plan.get("user_email", ""),
            "goal": str(plan.get("goal", "")),
            "site_url": str(plan.get("site_url", "")),
            "replans": int(plan.get("replans", 0)),
            "tasks": plan.get("tasks", []),
            "have_documents": plan.get("have_documents", []),
        }
        supabase.table("plans").upsert(payload, on_conflict="plan_id").execute()
    except Exception as e:
        print(f"[Supabase Sync Warning]: Failed to sync plan {plan.get('plan_id')}: {e}")


class SignupIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class GoalIn(BaseModel):
    goal: str
    site_url: str = ""      # optional: the registration website


class ApprovalIn(BaseModel):
    approved: bool
    feedback: str = ""      # optional note from the user, used when re-planning
    edits: dict | None = None   # the user's edits to the draft: {to, subject, body}


class DocumentsIn(BaseModel):
    have: list[str]         # documents the user ticked as "I have this"


# ---------- accounts ----------
@app.post("/auth/signup")
def signup(body: SignupIn):
    user = auth.signup(body.name, body.email, body.password)
    return {"token": auth.create_session(user["id"]), "user": auth.public_user(user)}


@app.post("/auth/login")
def login(body: LoginIn):
    user = auth.login(body.email, body.password)
    return {"token": auth.create_session(user["id"]), "user": auth.public_user(user)}


@app.get("/auth/me")
def me(user: dict = Depends(auth.current_user)):
    return auth.public_user(user)


@app.post("/auth/logout")
def logout(creds: HTTPAuthorizationCredentials = Depends(auth.bearer)):
    if creds is not None:
        auth.end_session(creds.credentials)
    return {"ok": True}


# ---------- plans (each user only sees their own) ----------
def _own_plan(plan_id: str, user: dict) -> dict:
    plan = load_plan(plan_id)
    if plan is None or plan.get("owner") != user["id"]:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.get("/plans")
def my_plans(user: dict = Depends(auth.current_user)):
    # Try fetching from Supabase first; fallback to local storage
    try:
        res = (
            supabase.table("plans")
            .select("*")
            .eq("owner", str(user["id"]))
            .order("created_at", desc=True)
            .execute()
        )
        if res.data:
            return res.data
    except Exception as e:
        print(f"[Supabase Read Error]: {e}")

    return list_plans(user["id"])


@app.post("/goals")
def create_goal(body: GoalIn, user: dict = Depends(auth.current_user)):
    goal = body.goal.strip()
    if not goal:
        raise HTTPException(status_code=400, detail="Please enter a goal")
    site_url = _clean_url(body.site_url)
    try:
        tasks = create_plan(goal)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"The AI could not make a plan: {e}")

    plan = {
        "plan_id": str(uuid.uuid4())[:8],
        "owner": user["id"],
        "user_email": user.get("email", ""),
        "goal": goal,
        "site_url": site_url,
        "replans": 0,
        "tasks": tasks,
    }
    advance(plan)           # start working immediately
    save_plan(plan)         # save to local active_plans.json
    _sync_plan_to_supabase(plan, user_email=user.get("email", ""))  # save to Supabase
    return plan


@app.get("/plans/{plan_id}")
def get_plan(plan_id: str, user: dict = Depends(auth.current_user)):
    return _own_plan(plan_id, user)


@app.post("/plans/{plan_id}/tasks/{task_id}/approve")
def approve(plan_id: str, task_id: str, body: ApprovalIn, user: dict = Depends(auth.current_user)):
    plan = _own_plan(plan_id, user)

    waiting = [t for t in plan["tasks"] if t["id"] == task_id and t["status"] == "needs_approval"]
    if not waiting:
        raise HTTPException(status_code=400, detail="That task is not waiting for approval")

    log_approval(plan_id, task_id, body.approved)       # audit trail (data/approval_log.json)

    # Sync approval log event to Supabase
    try:
        supabase.table("approval_logs").insert({
            "plan_id": str(plan_id),
            "task_id": str(task_id),
            "approved": bool(body.approved),
            "user_email": str(user.get("email", ""))
        }).execute()
    except Exception as e:
        print(f"[Supabase Approval Log Warning]: Failed to sync approval: {e}")

    try:
        handle_approval(plan, task_id, body.approved, body.feedback, body.edits)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"The agent hit a problem: {e}")

    save_plan(plan)
    _sync_plan_to_supabase(plan, user_email=user.get("email", ""))  # sync updated state
    return plan


@app.post("/plans/{plan_id}/documents")
def save_documents(plan_id: str, body: DocumentsIn, user: dict = Depends(auth.current_user)):
    plan = _own_plan(plan_id, user)
    plan["have_documents"] = [d[:200] for d in body.have][:50]
    save_plan(plan)
    _sync_plan_to_supabase(plan, user_email=user.get("email", ""))  # sync documents list
    return plan


def _clean_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if "." not in url.split("//", 1)[1]:
        raise HTTPException(status_code=400, detail="That website address does not look right")
    return url[:300]