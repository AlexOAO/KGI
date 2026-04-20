from app.core.database import get_conn
from fastapi import HTTPException

# Rewards per level reached (level_index 2–6)
LEVEL_REWARDS = {
    2: {"kgi_points": 100,  "learning_hours": 1.0},
    3: {"kgi_points": 250,  "learning_hours": 2.5},
    4: {"kgi_points": 500,  "learning_hours": 5.0},
    5: {"kgi_points": 1000, "learning_hours": 10.0},
    6: {"kgi_points": 2500, "learning_hours": 25.0},
}


def get_level_reward_options(level_index: int):
    """Return reward choices for the reached level, or None if no reward."""
    return LEVEL_REWARDS.get(level_index)


def claim_level_reward(user_id: int, level_reached: int, reward_type: str) -> dict:
    """
    Idempotently grant chosen reward. Raises 409 if already claimed.
    Returns updated wallet totals.
    """
    options = LEVEL_REWARDS.get(level_reached)
    if not options:
        raise HTTPException(status_code=400, detail="No reward for this level")
    if reward_type not in ("kgi_points", "learning_hours"):
        raise HTTPException(status_code=400, detail="Invalid reward_type")

    amount = options[reward_type]

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Idempotency: INSERT IGNORE
            cur.execute(
                "INSERT IGNORE INTO level_up_rewards "
                "(user_id, level_reached, reward_type, reward_amount) VALUES (%s,%s,%s,%s)",
                (user_id, level_reached, reward_type, amount),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=409, detail="Reward already claimed")

            # Credit the user
            if reward_type == "kgi_points":
                cur.execute(
                    "UPDATE users SET kgi_points = kgi_points + %s WHERE id=%s",
                    (int(amount), user_id),
                )
                cur.execute(
                    "INSERT INTO reward_transactions (user_id, txn_type, points_delta, note) "
                    "VALUES (%s,'earn_points_levelup',%s,%s)",
                    (user_id, int(amount), f"升至第{level_reached}階獎勵"),
                )
            else:
                cur.execute(
                    "UPDATE users SET learning_hours = learning_hours + %s WHERE id=%s",
                    (amount, user_id),
                )
                cur.execute(
                    "INSERT INTO reward_transactions (user_id, txn_type, hours_delta, note) "
                    "VALUES (%s,'earn_hours_levelup',%s,%s)",
                    (user_id, amount, f"升至第{level_reached}階獎勵"),
                )

            cur.execute(
                "SELECT kgi_points, learning_hours, perf_hours FROM users WHERE id=%s",
                (user_id,),
            )
            wallet = cur.fetchone()
        conn.commit()
        return {
            "ok": True,
            "reward_type": reward_type,
            "amount": amount,
            "kgi_points": wallet["kgi_points"],
            "learning_hours": float(wallet["learning_hours"]),
            "perf_hours": float(wallet["perf_hours"]),
        }
    finally:
        conn.close()


def get_wallet(user_id: int) -> dict:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT kgi_points, learning_hours, perf_hours, cumulative_learn_seconds "
                "FROM users WHERE id=%s",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return {"kgi_points": 0, "learning_hours": 0.0,
                        "perf_hours": 0.0, "cumulative_learn_seconds": 0,
                        "convertible_hours": 0.0, "claimed_levels": []}
            convertible = round(row["cumulative_learn_seconds"] / 3600, 2)
            cur.execute(
                "SELECT level_reached FROM level_up_rewards WHERE user_id=%s",
                (user_id,),
            )
            claimed_levels = [r["level_reached"] for r in cur.fetchall()]
            return {
                "kgi_points": row["kgi_points"],
                "learning_hours": float(row["learning_hours"]),
                "perf_hours": float(row["perf_hours"]),
                "cumulative_learn_seconds": row["cumulative_learn_seconds"],
                "convertible_hours": convertible,
                "claimed_levels": claimed_levels,
            }
    finally:
        conn.close()


def get_transaction_history(user_id: int, limit: int = 50) -> list:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT t.*, c.name as item_name FROM reward_transactions t "
                "LEFT JOIN reward_catalog c ON t.catalog_item_id = c.id "
                "WHERE t.user_id=%s ORDER BY t.created_at DESC LIMIT %s",
                (user_id, limit),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
