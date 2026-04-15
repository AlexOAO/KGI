from app.core.database import get_connection
from typing import Optional
from datetime import datetime

def get_schedule(user_id: int, module_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM review_schedule WHERE user_id = ? AND module_id = ?",
            (user_id, module_id)
        ).fetchone()
        return dict(row) if row else None

def upsert_schedule(user_id: int, module_id: int, concept_tag: str, next_review_at: datetime,
                    interval_days: float, ease_factor: float, repetitions: int):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM review_schedule WHERE user_id = ? AND module_id = ?",
            (user_id, module_id)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE review_schedule SET concept_tag=?, next_review_at=?, interval_days=?,
                   ease_factor=?, repetitions=? WHERE user_id=? AND module_id=?""",
                (concept_tag, next_review_at.isoformat(), interval_days, ease_factor, repetitions, user_id, module_id)
            )
        else:
            conn.execute(
                """INSERT INTO review_schedule (user_id, module_id, concept_tag, next_review_at,
                   interval_days, ease_factor, repetitions) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, module_id, concept_tag, next_review_at.isoformat(), interval_days, ease_factor, repetitions)
            )

def get_due_reviews(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT rs.*, m.title as module_title FROM review_schedule rs
               JOIN modules m ON rs.module_id = m.id
               WHERE rs.user_id = ? AND rs.next_review_at <= ?
               ORDER BY rs.next_review_at""",
            (user_id, datetime.now().isoformat())
        ).fetchall()
        return [dict(r) for r in rows]

def get_all_schedules(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT rs.*, m.title as module_title FROM review_schedule rs
               JOIN modules m ON rs.module_id = m.id
               WHERE rs.user_id = ?
               ORDER BY rs.next_review_at""",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
