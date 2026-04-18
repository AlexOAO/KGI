from datetime import date, timedelta, datetime
from app.core.database import get_conn


def get_dashboard(user_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Modules completed
            cur.execute(
                "SELECT COUNT(DISTINCT module_id) as cnt FROM quiz_sessions WHERE user_id=%s",
                (user_id,),
            )
            modules_completed = cur.fetchone()["cnt"]

            # Mastery per topic
            cur.execute(
                "SELECT m.topic_tag, AVG(qs.score) as avg_score, COUNT(*) as attempts "
                "FROM quiz_sessions qs JOIN modules m ON qs.module_id=m.id "
                "WHERE qs.user_id=%s GROUP BY m.topic_tag",
                (user_id,),
            )
            mastery = cur.fetchall()

            # Due reviews
            cur.execute(
                "SELECT concept_tag, next_review_at, interval_days, ease_factor "
                "FROM review_schedule WHERE user_id=%s ORDER BY next_review_at",
                (user_id,),
            )
            reviews = cur.fetchall()

            # Streak freeze count
            cur.execute("SELECT streak_freeze_count FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
            freeze_count = row["streak_freeze_count"] if row else 0

            # Streak (days with at least one quiz)
            cur.execute(
                "SELECT DATE(completed_at) as day FROM quiz_sessions WHERE user_id=%s "
                "GROUP BY DATE(completed_at) ORDER BY day DESC",
                (user_id,),
            )
            days = [r["day"] for r in cur.fetchall()]
            streak = _calc_streak(days, freeze_count=freeze_count)

        # Award freeze at 7-day milestones (only if streak just hit a multiple of 7)
        if streak > 0 and streak % 7 == 0:
            _maybe_award_freeze(user_id, streak)
            freeze_count += 1

        return {
            "modules_completed": modules_completed,
            "mastery": mastery,
            "reviews": reviews,
            "streak": streak,
            "streak_freeze_count": freeze_count,
            "unlock_progress": streak % 7,
        }
    finally:
        conn.close()


def _calc_streak(days, freeze_count=0):
    if not days:
        return 0
    streak = 0
    check = date.today()
    freeze_used = 0
    for d in days:
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        elif d == check - timedelta(days=1) and freeze_used < freeze_count:
            freeze_used += 1
            streak += 1
            check -= timedelta(days=2)
        else:
            break
    return streak


def _maybe_award_freeze(user_id: int, streak: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET streak_freeze_count = streak_freeze_count + 1 WHERE id=%s",
                (user_id,),
            )
        conn.commit()
    finally:
        conn.close()


def get_due_reviews(user_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT concept_tag, next_review_at FROM review_schedule "
                "WHERE user_id=%s AND next_review_at <= %s ORDER BY next_review_at",
                (user_id, date.today()),
            )
            return cur.fetchall()
    finally:
        conn.close()
