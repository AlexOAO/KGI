import json
from app.core.database import get_conn


def get_questions(module_id: int, limit: int = 5):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM questions WHERE module_id = %s ORDER BY RAND() LIMIT %s",
                (module_id, limit),
            )
            rows = cur.fetchall()
            for row in rows:
                if isinstance(row.get("options_json"), str):
                    row["options_json"] = json.loads(row["options_json"])
            return rows
    finally:
        conn.close()


def save_quiz_session(sprint_id, user_id, module_id, score, responses):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO quiz_sessions (sprint_id, user_id, module_id, score) VALUES (%s,%s,%s,%s)",
                (sprint_id, user_id, module_id, score),
            )
            quiz_session_id = cur.lastrowid
            for resp in responses:
                cur.execute(
                    "INSERT INTO question_responses (quiz_session_id, question_id, user_answer, is_correct, response_time_ms) VALUES (%s,%s,%s,%s,%s)",
                    (quiz_session_id, resp["question_id"], resp["user_answer"], resp["is_correct"], resp.get("response_time_ms", 0)),
                )
            # Link to journey map
            if sprint_id:
                cur.execute(
                    "INSERT INTO learning_journey_map (sprint_id, quiz_session_id) VALUES (%s,%s) ON DUPLICATE KEY UPDATE quiz_session_id=%s",
                    (sprint_id, quiz_session_id, quiz_session_id),
                )
        conn.commit()
        return quiz_session_id
    finally:
        conn.close()
