from datetime import date
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

            # Streak (days with at least one quiz)
            cur.execute(
                "SELECT DATE(completed_at) as day FROM quiz_sessions WHERE user_id=%s "
                "GROUP BY DATE(completed_at) ORDER BY day DESC",
                (user_id,),
            )
            days = [r["day"] for r in cur.fetchall()]
            streak = _calc_streak(days)

        return {
            "modules_completed": modules_completed,
            "mastery": mastery,
            "reviews": reviews,
            "streak": streak,
        }
    finally:
        conn.close()


def _calc_streak(days):
    if not days:
        return 0
    streak = 0
    check = date.today()
    for d in days:
        if isinstance(d, str):
            from datetime import datetime
            d = datetime.strptime(d, "%Y-%m-%d").date()
        if d == check:
            streak += 1
            from datetime import timedelta
            check -= timedelta(days=1)
        else:
            break
    return streak


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
