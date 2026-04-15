from app.core.database import get_connection
from typing import Optional

def get_all_modules() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM modules ORDER BY id").fetchall()
        return [dict(r) for r in rows]

def get_module_by_id(module_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM modules WHERE id = ?", (module_id,)).fetchone()
        return dict(row) if row else None

def get_flashcards(module_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM flashcard_pages WHERE module_id = ? ORDER BY sequence_number",
            (module_id,)
        ).fetchall()
        return [dict(r) for r in rows]

def create_module(title: str, topic_tag: str, duration_seconds: int = 420, difficulty_level: str = "intermediate") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO modules (title, topic_tag, duration_seconds, difficulty_level) VALUES (?, ?, ?, ?)",
            (title, topic_tag, duration_seconds, difficulty_level)
        )
        return cursor.lastrowid

def create_flashcard(module_id: int, sequence_number: int, text_content: str, image_url: str = None) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO flashcard_pages (module_id, sequence_number, text_content, image_url) VALUES (?, ?, ?, ?)",
            (module_id, sequence_number, text_content, image_url)
        )
        return cursor.lastrowid
