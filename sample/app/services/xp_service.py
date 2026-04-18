from app.core.database import get_conn

LEVELS = [
    {"name": "新手法遵員",  "min_xp": 0,    "next_xp": 100},
    {"name": "合規見習生",  "min_xp": 100,  "next_xp": 300},
    {"name": "法遵分析師",  "min_xp": 300,  "next_xp": 700},
    {"name": "合規達人",    "min_xp": 700,  "next_xp": 1500},
    {"name": "法遵大師",    "min_xp": 1500, "next_xp": None},
]


def level_for(total_xp: int) -> dict:
    current = LEVELS[0]
    for lvl in LEVELS:
        if total_xp >= lvl["min_xp"]:
            current = lvl
    next_xp = current["next_xp"]
    if next_xp is None:
        progress_pct = 100
    else:
        span = next_xp - current["min_xp"]
        progress_pct = int((total_xp - current["min_xp"]) / span * 100)
    return {
        "name": current["name"],
        "min_xp": current["min_xp"],
        "next_xp": next_xp,
        "progress_pct": progress_pct,
        "total_xp": total_xp,
    }


def compute_xp(questions: list, first_attempt_map: dict) -> int:
    xp = 0
    all_correct = True
    for q in questions:
        qid = str(q["id"])
        correct_first = first_attempt_map.get(qid, False)
        if correct_first:
            xp += 15
        else:
            xp += 10
            all_correct = False
    if all_correct and questions:
        xp += 25
    return xp


def update_user_xp(user_id: int, delta: int) -> dict:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT total_xp FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
            old_xp = row["total_xp"] if row else 0
            new_xp = old_xp + delta
            cur.execute("UPDATE users SET total_xp=%s WHERE id=%s", (new_xp, user_id))
        conn.commit()
        old_level = level_for(old_xp)
        new_level = level_for(new_xp)
        return {
            "old_xp": old_xp,
            "new_xp": new_xp,
            "old_level": old_level["name"],
            "new_level": new_level["name"],
            "leveled_up": old_level["name"] != new_level["name"],
        }
    finally:
        conn.close()
