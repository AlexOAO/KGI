from fastapi import APIRouter, Depends
from app.api.auth import get_current_user
from app.core.database import get_conn
from app.models.module import get_module, get_flashcards
from app.services.dashboard_service import get_due_reviews

router = APIRouter(tags=["modules"])


@router.get("/modules")
def list_modules(user=Depends(get_current_user)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT m.*, bs.best_score FROM modules m "
                "LEFT JOIN (SELECT module_id, MAX(score) as best_score "
                "FROM quiz_sessions WHERE user_id=%s GROUP BY module_id) bs "
                "ON m.id = bs.module_id",
                (user["user_id"],),
            )
            modules = cur.fetchall()
    finally:
        conn.close()

    due = get_due_reviews(user["user_id"])
    due_tags = {r["concept_tag"] for r in due}
    result = []
    for m in modules:
        tag = m.get("topic_tag", "")
        m_dict = dict(m)
        m_dict["due_review"] = any(t in tag for t in due_tags)
        result.append(m_dict)
    return result


@router.get("/modules/{module_id}")
def get_module_detail(module_id: int, user=Depends(get_current_user)):
    module = get_module(module_id)
    if not module:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Module not found")
    flashcards = get_flashcards(module_id)
    return {"module": dict(module), "flashcards": [dict(f) for f in flashcards]}
