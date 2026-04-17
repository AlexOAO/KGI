from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from app.api.auth import get_current_user
from app.models.quiz import get_questions
from app.services.quiz_service import grade_quiz
from app.models.module import get_module

router = APIRouter(tags=["quiz"])


@router.get("/quiz/{module_id}")
def api_get_quiz(module_id: int, user=Depends(get_current_user)):
    questions = get_questions(module_id, limit=5)
    return {"questions": [dict(q) for q in questions]}


class SubmitQuizRequest(BaseModel):
    sprint_id: int | None = None
    module_id: int
    answers: Dict[str, str]  # {question_id: answer}


@router.post("/quiz/submit")
def api_submit_quiz(req: SubmitQuizRequest, user=Depends(get_current_user)):
    # Need correct answers to grade
    questions = get_questions(req.module_id, limit=100)
    # Filter to only submitted question IDs
    submitted_ids = {int(k) for k in req.answers.keys()}
    questions = [q for q in questions if q["id"] in submitted_ids]

    module = get_module(req.module_id)
    topic_tag = module.get("topic_tag", "") if module else ""

    score, correct, total, quiz_session_id = grade_quiz(
        user["user_id"], req.sprint_id, req.module_id, questions, req.answers, topic_tag
    )
    return {
        "score": score,
        "correct": correct,
        "total": total,
        "quiz_session_id": quiz_session_id,
    }
