"""Account creation, login, and cookie sessions for Campus Customs.

Passwords: PBKDF2-HMAC-SHA256 with a random per-user salt.
  - New format:    pbkdf2_sha256$<iterations>$<salt>$<hex>
  - Legacy (seed): pbkdf2_sha256$<salt>$<hex>  (120,000 iterations)
Legacy hashes are verified, then upgraded to the new format on successful login.

Sessions: a random token in an HttpOnly cookie; only its SHA-256 is stored in the DB.
"""

import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, field_validator

from db import get_db

ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-SHA256
LEGACY_ITERATIONS = 120_000
SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- password hashing ----------

def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
        _, iters, salt, expected = parts
        iterations = int(iters)
    elif len(parts) == 3 and parts[0] == "pbkdf2_sha256":
        _, salt, expected = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), expected)


def needs_upgrade(stored: str) -> bool:
    return len(stored.split("$")) != 4 or stored.split("$")[1] != str(ITERATIONS)


# Dummy hash so unknown emails take as long as wrong passwords (no user enumeration by timing).
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- sessions ----------

def ensure_sessions_table() -> None:
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )"""
        )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _start_session(conn: sqlite3.Connection, response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), user_id, expires.isoformat()),
    )
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400,
        httponly=True, samesite="lax", secure=False,  # secure=True once served over HTTPS
    )


def current_user(token: str | None) -> dict | None:
    """Return the public profile of the logged-in user, or None."""
    if not token:
        return None
    with get_db() as conn:
        row = conn.execute(
            """SELECT u.id, u.first_name, u.last_name, u.email, u.created_at, s.expires_at
               FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ?""",
            (_token_hash(token),),
        ).fetchone()
        if row is None:
            return None
        if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
            return None
        return {k: row[k] for k in ("id", "first_name", "last_name", "email", "created_at")}


def public_user(row: sqlite3.Row) -> dict:
    # Never include password_hash in anything sent to the browser or the agent.
    return {"id": row["id"], "first_name": row["first_name"], "last_name": row["last_name"], "email": row["email"]}


# ---------- routes ----------

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 60:
            raise ValueError("Name must be 1-60 characters")
        return v

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v) or len(v) > 254:
            raise ValueError("Enter a valid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
def signup(req: SignupRequest, response: Response):
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if req.password != req.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (req.email,)).fetchone():
            raise HTTPException(409, "An account with that email already exists")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{req.first_name} {req.last_name}", req.email, hash_password(req.password),
             req.first_name, req.last_name),
        )
        user_id = cur.lastrowid
        _start_session(conn, response, user_id)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return public_user(row)


@router.post("/login")
def login(req: LoginRequest, response: Response):
    email = req.email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        ok = verify_password(req.password, row["password_hash"] if row else _DUMMY_HASH)
        if not row or not ok:
            raise HTTPException(401, "Invalid email or password")
        if needs_upgrade(row["password_hash"]):
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (hash_password(req.password), row["id"]))
        _start_session(conn, response, row["id"])
        return public_user(row)


@router.post("/logout")
def logout(response: Response, cc_session: str | None = Cookie(default=None)):
    if cc_session:
        with get_db() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(cc_session),))
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)):
    user = current_user(cc_session)
    if user is None:
        raise HTTPException(401, "Not logged in")
    return user
