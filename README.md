# Paperwork Pilot

An agentic AI that turns confusing government and college paperwork into a simple, step-by-step process: finding requirements, creating document checklists, tracking deadlines, drafting forms/emails, and adapting to changes, while keeping the user in control through approval at every important step.

## Run it

### 1. Backend (Python)
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      (then put your Groq key in .env)
python -m uvicorn main:app --reload
```
API docs: http://127.0.0.1:8000/docs

### 2. Frontend (React + Vite)
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Folders
- `frontend/`: React app (goal input, plan, approval card, paperwork folder)
- `backend/main.py`: accounts + plan endpoints
- `backend/auth.py`: signup, login and sessions (salted password hashes)
- `backend/agent/`: the agent loop (plan, run, check, re-plan)
- `backend/tools/`: search, checklist, drafts, reminders
- `backend/data/`: workflow templates, plan storage, approval log
- `docs/`: contract and demo script

Never commit `backend/.env` (it holds your API key).
