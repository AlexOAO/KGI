from app.core.database import get_connection
from app.core.auth import hash_password, verify_password, create_session
from typing import Optional

def get_user_by_username(username: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

def authenticate(username: str, password: str) -> Optional[dict]:
    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        token = create_session(user["id"])
        return {"user_id": user["id"], "username": user["username"], "token": token, "role": user["role"]}
    return None

def create_user(username: str, password: str, role: str = "learner") -> int:
    pw_hash = hash_password(password)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, pw_hash, role)
        )
        return cursor.lastrowid
