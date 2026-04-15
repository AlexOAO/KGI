import json
from app.core.database import get_connection
from typing import Optional

def get_questions_by_module(module_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM questions WHERE module_id = ?", (module_id,)).fetchall()
        result = []
        for r in rows:
            q = dict(r)
            q["options"] = json.loads(q["options_json"])
            result.append(q)
        return result

def create_question(module_id: int, question_text: str, options: list, correct_answer: str, qtype: str = "multiple_choice") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO questions (module_id, question_text, type, options_json, correct_answer) VALUES (?, ?, ?, ?, ?)",
            (module_id, question_text, qtype, json.dumps(options, ensure_ascii=False), correct_answer)
        )
        return cursor.lastrowid

def create_attempt(user_id: int, module_id: int, sprint_session_id: int, score: int, accuracy: float) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO attempts (user_id, module_id, sprint_session_id, score, accuracy) VALUES (?, ?, ?, ?, ?)",
            (user_id, module_id, sprint_session_id, score, accuracy)
        )
        return cursor.lastrowid

def create_question_response(attempt_id: int, question_id: int, user_answer: str, is_correct: bool, response_time_ms: int = 0) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO question_responses (attempt_id, question_id, user_answer, is_correct, response_time_ms) VALUES (?, ?, ?, ?, ?)",
            (attempt_id, question_id, user_answer, 1 if is_correct else 0, response_time_ms)
        )
        return cursor.lastrowid

def get_attempts_by_user(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT a.*, m.title as module_title FROM attempts a JOIN modules m ON a.module_id = m.id WHERE a.user_id = ? ORDER BY a.completed_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
