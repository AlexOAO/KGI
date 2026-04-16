import bcrypt
from app.core.database import get_conn


def authenticate(username: str, password: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return user
        return None
    finally:
        conn.close()


def get_user(user_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, role, created_at FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()
