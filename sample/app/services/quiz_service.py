from datetime import datetime, timedelta
from app.models.quiz import create_attempt, create_question_response, get_questions_by_module
from app.models.schedule import get_schedule, upsert_schedule
from app.models.module import get_module_by_id
from app.services.sm2 import accuracy_to_quality, calculate_next_interval

def grade_quiz(user_id: int, module_id: int, sprint_session_id: int,
               answers: dict[int, str]) -> dict:
    """
    Grade a quiz attempt, save responses, update SM-2 schedule.

    Args:
        answers: {question_id: user_answer}

    Returns:
        {score, accuracy, total, attempt_id, results}
    """
    questions = get_questions_by_module(module_id)
    total = len(questions)
    if total == 0:
        return {"score": 0, "accuracy": 0.0, "total": 0, "attempt_id": None, "results": []}

    correct = 0
    results = []
    for q in questions:
        user_ans = answers.get(q["id"], "")
        is_correct = user_ans.strip() == q["correct_answer"].strip()
        if is_correct:
            correct += 1
        results.append({
            "question_id": q["id"],
            "question_text": q["question_text"],
            "user_answer": user_ans,
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
        })

    accuracy = (correct / total) * 100
    attempt_id = create_attempt(user_id, module_id, sprint_session_id, correct, accuracy)

    for r in results:
        create_question_response(attempt_id, r["question_id"], r["user_answer"], r["is_correct"])

    # Update SM-2 schedule
    module = get_module_by_id(module_id)
    concept_tag = module["topic_tag"] if module else "general"
    existing = get_schedule(user_id, module_id)

    if existing:
        reps = existing["repetitions"]
        ef = existing["ease_factor"]
        interval = existing["interval_days"]
    else:
        reps, ef, interval = 0, 2.5, 1.0

    quality = accuracy_to_quality(accuracy)
    new_reps, new_interval, new_ef = calculate_next_interval(reps, ef, interval, quality)
    next_review = datetime.now() + timedelta(days=new_interval)
    upsert_schedule(user_id, module_id, concept_tag, next_review, new_interval, new_ef, new_reps)

    return {
        "score": correct,
        "accuracy": accuracy,
        "total": total,
        "attempt_id": attempt_id,
        "results": results,
    }
