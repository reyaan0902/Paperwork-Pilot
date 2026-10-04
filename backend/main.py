import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.loop import create_plan, advance, handle_approval

app = FastAPI()

# lets the React app (Person 1) talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PLANS = {}   # temporary storage in memory; Person 4's database replaces this later


class GoalIn(BaseModel):
    goal: str

class ApprovalIn(BaseModel):
    approved: bool


@app.post("/goals")
def create_goal(body: GoalIn):
    plan_id = str(uuid.uuid4())[:8]
    plan = {"plan_id": plan_id, "goal": body.goal, "tasks": create_plan(body.goal)}
    PLANS[plan_id] = plan
    advance(plan)          # start working immediately
    return plan


@app.get("/plans/{plan_id}")
def get_plan(plan_id: str):
    if plan_id not in PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PLANS[plan_id]


@app.post("/plans/{plan_id}/tasks/{task_id}/approve")
def approve(plan_id: str, task_id: str, body: ApprovalIn):
    if plan_id not in PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    handle_approval(PLANS[plan_id], task_id, body.approved)
    return PLANS[plan_id]
