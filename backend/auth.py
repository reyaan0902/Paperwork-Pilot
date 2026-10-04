"""Simple email + password accounts for the demo.

- Passwords are never stored. We keep a salted PBKDF2 hash.
- Logging in gives a random token. The frontend sends it as `Authorization: Bearer <token>`.
- Users and sessions are saved in data/users.json and data/sessions.json.
"""
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from data.storage import DATA_DIR, _load_json, _save_json
import os

USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
SESSION_DAYS = 7

bearer = HTTPBearer(auto_error=False)


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()


def public_user(user: dict) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def signup(name: str, email: str, password: str) -> dict:
    name, email = name.strip(), email.strip().lower()
    if not name:
        raise HTTPException(400, "Please enter your name")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Please enter a valid email address")
    if len(password) < 6:
        raise HTTPException(400, "Your password needs at least 6 characters")

    users = _load_json(USERS_FILE, {})
    if any(u["email"] == email for u in users.values()):
        raise HTTPException(409, "An account with this email already exists. Try logging in")

    salt = secrets.token_hex(16)
    user = {"id": uuid.uuid4().hex[:10], "name": name, "email": email,
            "salt": salt, "password_hash": _hash(password, salt)}
    users[user["id"]] = user
    _save_json(USERS_FILE, users)
    return user


def login(email: str, password: str) -> dict:
    email = email.strip().lower()
    users = _load_json(USERS_FILE, {})
    user = next((u for u in users.values() if u["email"] == email), None)
    if not user or not hmac.compare_digest(user["password_hash"], _hash(password, user["salt"])):
        raise HTTPException(401, "Email or password is incorrect")
    return user


def create_session(user_id: str) -> str:
    sessions = _load_json(SESSIONS_FILE, {})
    token = secrets.token_urlsafe(32)
    sessions[token] = {"user_id": user_id, "created": datetime.utcnow().isoformat()}
    _save_json(SESSIONS_FILE, sessions)
    return token


def end_session(token: str) -> None:
    sessions = _load_json(SESSIONS_FILE, {})
    if sessions.pop(token, None) is not None:
        _save_json(SESSIONS_FILE, sessions)


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """Use as a dependency on any endpoint that needs a logged-in user."""
    if creds is None:
        raise HTTPException(401, "Please log in")
    session = _load_json(SESSIONS_FILE, {}).get(creds.credentials)
    if session is None:
        raise HTTPException(401, "Your session has ended. Please log in again")
    if datetime.utcnow() - datetime.fromisoformat(session["created"]) > timedelta(days=SESSION_DAYS):
        end_session(creds.credentials)
        raise HTTPException(401, "Your session has ended. Please log in again")
    user = _load_json(USERS_FILE, {}).get(session["user_id"])
    if user is None:
        raise HTTPException(401, "Please log in again")
    return user
