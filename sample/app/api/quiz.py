from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from app.api.auth import get_current_user
from app.models.quiz import get_questions
from app.services.quiz_service import grade_quiz
from app.services.xp_service import level_for
from app.models.module import get_module

router = APIRouter(tags=["quiz"])


@router.get("/quiz/{module_id}")
def api_get_quiz(module_id: int, user=Depends(get_current_user)):
    questions = get_questions(module_id, limit=5)
    return {"questions": [dict(q) for q in questions]}


class SubmitQuizRequest(BaseModel):
    sprint_id: int | None = None
    module_id: int
    answers: Dict[str, str]
    first_attempt_map: Dict[str, bool] = {}


@router.post("/quiz/submit")
def api_submit_quiz(req: SubmitQuizRequest, user=Depends(get_current_user)):
    questions = get_questions(req.module_id, limit=100)
    submitted_ids = {int(k) for k in req.answers.keys()}
    questions = [q for q in questions if q["id"] in submitted_ids]

    module = get_module(req.module_id)
    topic_tag = module.get("topic_tag", "") if module else ""

    result = grade_quiz(
        user["user_id"], req.sprint_id, req.module_id, questions, req.answers, topic_tag,
        first_attempt_map=req.first_attempt_map,
    )
    level_info = level_for(result["total_xp"])
    return {
        "score": result["score"],
        "correct": result["correct"],
        "total": result["total"],
        "quiz_session_id": result["quiz_session_id"],
        "xp_earned": result["xp_earned"],
        "total_xp": result["total_xp"],
        "leveled_up": result["leveled_up"],
        "level_name": result["level_name"],
        "progress_pct": result["progress_pct"],
        "next_xp": level_info["next_xp"],
        "level_index": level_info["level_index"],
    }
