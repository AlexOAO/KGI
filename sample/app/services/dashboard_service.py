from datetime import datetime, timedelta
from app.models.quiz import get_attempts_by_user
from app.models.schedule import get_all_schedules, get_due_reviews

def calculate_streak(user_id: int) -> int:
    """Calculate consecutive days with completed attempts."""
    attempts = get_attempts_by_user(user_id)
    if not attempts:
        return 0

    dates = set()
    for a in attempts:
        try:
            dt = datetime.fromisoformat(a["completed_at"])
            dates.add(dt.date())
        except (ValueError, TypeError):
            continue

    if not dates:
        return 0

    today = datetime.now().date()
    streak = 0
    current = today

    while current in dates:
        streak += 1
        current -= timedelta(days=1)

    if streak == 0 and (today - timedelta(days=1)) in dates:
        current = today - timedelta(days=1)
        while current in dates:
            streak += 1
            current -= timedelta(days=1)

    return streak

def calculate_mastery(user_id: int) -> dict[int, float]:
    """Calculate mastery percentage per module based on latest attempt accuracy."""
    attempts = get_attempts_by_user(user_id)
    mastery = {}
    for a in attempts:
        mid = a["module_id"]
        if mid not in mastery:
            mastery[mid] = a["accuracy"]
    return mastery

def get_dashboard_data(user_id: int) -> dict:
    """Aggregate dashboard statistics."""
    attempts = get_attempts_by_user(user_id)
    streak = calculate_streak(user_id)
    mastery = calculate_mastery(user_id)
    schedules = get_all_schedules(user_id)
    due = get_due_reviews(user_id)

    total_attempts = len(attempts)
    avg_accuracy = sum(a["accuracy"] for a in attempts) / total_attempts if total_attempts > 0 else 0.0

    return {
        "streak": streak,
        "total_attempts": total_attempts,
        "avg_accuracy": avg_accuracy,
        "mastery_by_module": mastery,
        "recent_attempts": attempts[:5],
        "review_schedule": schedules,
        "due_reviews": due,
    }
