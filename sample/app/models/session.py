from app.core.database import get_connection
from typing import Optional
from datetime import datetime

def create_sprint_session(user_id: int, module_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO sprint_sessions (user_id, module_id, start_timestamp, completion_status) VALUES (?, ?, ?, 'in_progress')",
            (user_id, module_id, datetime.now().isoformat())
        )
        return cursor.lastrowid

def complete_sprint_session(session_id: int, tab_switch_count: int = 0,
                             status: str = 'finished_early'):
    with get_connection() as conn:
        conn.execute(
            "UPDATE sprint_sessions SET end_timestamp = ?, completion_status = ?, tab_switch_count = ? WHERE id = ?",
            (datetime.now().isoformat(), status, tab_switch_count, session_id)
        )

def get_sprint_session(session_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sprint_sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

def create_learning_journey(sprint_session_id: int, quiz_session_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO learning_journey_map (sprint_session_id, quiz_session_id) VALUES (?, ?)",
            (sprint_session_id, quiz_session_id)
        )
        return cursor.lastrowid
