from datetime import date, timedelta
from app.core.database import get_conn
from app.services.sm2 import calculate_next_interval, score_to_quality
from app.models.quiz import save_quiz_session
from app.services.xp_service import compute_xp, update_user_xp, level_for


def grade_quiz(user_id: int, sprint_id, module_id: int, questions: list, answers: dict,
               topic_tag: str = None, first_attempt_map: dict = None):
    if first_attempt_map is None:
        first_attempt_map = {}

    responses = []
    correct = 0
    for q in questions:
        qid = str(q["id"])
        user_ans = answers.get(qid, "")
        is_correct = user_ans.strip() == q["correct_answer"].strip()
        if is_correct:
            correct += 1
        responses.append({
            "question_id": q["id"],
            "user_answer": user_ans,
            "is_correct": int(is_correct),
            "response_time_ms": 0,
        })

    score = (correct / len(questions) * 100) if questions else 0

    # Compute and award XP
    xp_earned = compute_xp(questions, first_attempt_map)
    xp_result = update_user_xp(user_id, xp_earned)

    quiz_session_id = save_quiz_session(sprint_id, user_id, module_id, score, responses, xp_earned=xp_earned)

    # Update SM-2 schedule using first-attempt quality
    if topic_tag:
        if first_attempt_map:
            first_correct = sum(1 for v in first_attempt_map.values() if v)
            first_score = (first_correct / len(questions) * 100) if questions else score
        else:
            first_score = score
        quality = score_to_quality(first_score)
        _update_review_schedule(user_id, topic_tag, quality)

    level_info = level_for(xp_result["new_xp"])

    return {
        "score": score,
        "correct": correct,
        "total": len(questions),
        "quiz_session_id": quiz_session_id,
        "xp_earned": xp_earned,
        "total_xp": xp_result["new_xp"],
        "leveled_up": xp_result["leveled_up"],
        "level_name": xp_result["new_level"],
        "progress_pct": level_info["progress_pct"],
    }


def _update_review_schedule(user_id: int, concept_tag: str, quality: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT interval_days, ease_factor, repetitions FROM review_schedule WHERE user_id=%s AND concept_tag=%s",
                (user_id, concept_tag),
            )
            row = cur.fetchone()
            if row:
                new_interval, new_ef, new_reps = calculate_next_interval(
                    row["repetitions"], row["ease_factor"], quality, row["interval_days"]
                )
                next_review = date.today() + timedelta(days=new_interval)
                cur.execute(
                    "UPDATE review_schedule SET next_review_at=%s, interval_days=%s, ease_factor=%s, repetitions=%s WHERE user_id=%s AND concept_tag=%s",
                    (next_review, new_interval, new_ef, new_reps, user_id, concept_tag),
                )
            else:
                new_interval, new_ef, new_reps = calculate_next_interval(0, 2.5, quality)
                next_review = date.today() + timedelta(days=new_interval)
                cur.execute(
                    "INSERT INTO review_schedule (user_id, concept_tag, next_review_at, interval_days, ease_factor, repetitions) VALUES (%s,%s,%s,%s,%s,%s)",
                    (user_id, concept_tag, next_review, new_interval, new_ef, new_reps),
                )
        conn.commit()
    finally:
        conn.close()
