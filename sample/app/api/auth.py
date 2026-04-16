import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, Response, HTTPException, Depends, Cookie
from pydantic import BaseModel
import hmac, hashlib, base64, json, os

router = APIRouter(tags=["auth"])

SECRET = os.getenv("JWT_SECRET", "kgi-secret-key-change-in-prod")


def _make_token(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{header}.{body}.{sig_b64}"


def _verify_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("bad token")
        header, body, sig = parts
        expected_sig = hmac.new(SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        if not hmac.compare_digest(sig, expected_b64):
            raise ValueError("bad signature")
        # Add padding back
        padded = body + "=" * (4 - len(body) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(session: str = Cookie(default=None)):
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _verify_token(session)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest, response: Response):
    from app.core.database import get_conn
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (req.username,))
            user = cur.fetchone()
    finally:
        conn.close()
    if not user or not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    payload = {"user_id": user["id"], "username": user["username"], "role": user["role"]}
    token = _make_token(payload)
    response.set_cookie("session", token, httponly=True, samesite="lax", max_age=86400)
    return {"user_id": user["id"], "username": user["username"], "role": user["role"]}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user
