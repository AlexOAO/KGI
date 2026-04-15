import bcrypt
import secrets
from typing import Optional

# In-memory session store: token -> user_id
_sessions: dict[str, int] = {}

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    _sessions[token] = user_id
    return token

def get_user_id_from_token(token: str) -> Optional[int]:
    return _sessions.get(token)

def destroy_session(token: str):
    _sessions.pop(token, None)
