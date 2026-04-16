from fastapi import APIRouter, Depends
from app.api.auth import get_current_user
from app.services.dashboard_service import get_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def api_dashboard(user=Depends(get_current_user)):
    data = get_dashboard(user["user_id"])
    # Convert dates to strings for JSON serialization
    reviews = []
    for r in data.get("reviews", []):
        reviews.append({
            "concept_tag": r["concept_tag"],
            "next_review_at": str(r["next_review_at"]),
            "interval_days": r["interval_days"],
            "ease_factor": round(float(r["ease_factor"]), 2),
        })
    mastery = []
    for m in data.get("mastery", []):
        mastery.append({
            "topic_tag": m.get("topic_tag", ""),
            "avg_score": round(float(m.get("avg_score", 0)), 1),
            "attempts": m.get("attempts", 0),
        })
    return {
        "modules_completed": data["modules_completed"],
        "streak": data["streak"],
        "mastery": mastery,
        "reviews": reviews,
    }
