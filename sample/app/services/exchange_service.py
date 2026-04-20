from app.core.database import get_conn
from fastapi import HTTPException

HOURS_TO_POINTS_RATE = 50    # points per learning hour
POINTS_TO_HOURS_RATE = 0.01  # learning hours per point (100 pts = 1 hr)


def convert_hours_to_points(user_id: int, hours: float) -> dict:
    if hours <= 0:
        raise HTTPException(status_code=400, detail="時數必須大於 0")
    points_earned = int(hours * HOURS_TO_POINTS_RATE)
    if points_earned == 0:
        raise HTTPException(status_code=400, detail="時數太少，無法兌換")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT learning_hours FROM users WHERE id=%s FOR UPDATE", (user_id,)
            )
            row = cur.fetchone()
            if not row or float(row["learning_hours"]) < hours:
                raise HTTPException(status_code=400, detail="學習時數不足")

            cur.execute(
                "UPDATE users SET learning_hours = learning_hours - %s, "
                "kgi_points = kgi_points + %s WHERE id=%s",
                (hours, points_earned, user_id),
            )
            cur.execute(
                "INSERT INTO reward_transactions (user_id, txn_type, points_delta, hours_delta, note) "
                "VALUES (%s,'convert_hours_to_points',%s,%s,%s)",
                (user_id, points_earned, -hours, f"時數兌換點數 {hours}hr → {points_earned}pts"),
            )
            cur.execute(
                "SELECT kgi_points, learning_hours FROM users WHERE id=%s", (user_id,)
            )
            wallet = cur.fetchone()
        conn.commit()
        return {
            "ok": True,
            "points_earned": points_earned,
            "kgi_points": wallet["kgi_points"],
            "learning_hours": float(wallet["learning_hours"]),
        }
    finally:
        conn.close()


def convert_points_to_hours(user_id: int, points: int) -> dict:
    if points <= 0:
        raise HTTPException(status_code=400, detail="點數必須大於 0")
    hours_earned = round(points * POINTS_TO_HOURS_RATE, 2)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT kgi_points FROM users WHERE id=%s FOR UPDATE", (user_id,)
            )
            row = cur.fetchone()
            if not row or row["kgi_points"] < points:
                raise HTTPException(status_code=400, detail="KGI 點數不足")

            cur.execute(
                "UPDATE users SET kgi_points = kgi_points - %s, "
                "learning_hours = learning_hours + %s WHERE id=%s",
                (points, hours_earned, user_id),
            )
            cur.execute(
                "INSERT INTO reward_transactions (user_id, txn_type, points_delta, hours_delta, note) "
                "VALUES (%s,'convert_points_to_hours',%s,%s,%s)",
                (user_id, -points, hours_earned, f"點數兌換時數 {points}pts → {hours_earned}hr"),
            )
            cur.execute(
                "SELECT kgi_points, learning_hours FROM users WHERE id=%s", (user_id,)
            )
            wallet = cur.fetchone()
        conn.commit()
        return {
            "ok": True,
            "hours_earned": hours_earned,
            "kgi_points": wallet["kgi_points"],
            "learning_hours": float(wallet["learning_hours"]),
        }
    finally:
        conn.close()


def redeem_catalog_item(user_id: int, catalog_item_id: int) -> dict:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reward_catalog WHERE id=%s AND is_active=1 FOR UPDATE",
                (catalog_item_id,),
            )
            item = cur.fetchone()
            if not item:
                raise HTTPException(status_code=404, detail="商品不存在或已下架")
            if item["stock"] is not None and item["stock"] <= 0:
                raise HTTPException(status_code=400, detail="商品已售罄")

            cur.execute(
                "SELECT kgi_points FROM users WHERE id=%s FOR UPDATE", (user_id,)
            )
            user = cur.fetchone()
            if not user or user["kgi_points"] < item["points_cost"]:
                raise HTTPException(status_code=400, detail="KGI 點數不足")

            # Deduct points
            cur.execute(
                "UPDATE users SET kgi_points = kgi_points - %s WHERE id=%s",
                (item["points_cost"], user_id),
            )
            # Decrement stock if limited
            if item["stock"] is not None:
                cur.execute(
                    "UPDATE reward_catalog SET stock = stock - 1 WHERE id=%s",
                    (catalog_item_id,),
                )
            # Write transaction
            cur.execute(
                "INSERT INTO reward_transactions "
                "(user_id, txn_type, points_delta, catalog_item_id, note) "
                "VALUES (%s,'redeem_catalog',%s,%s,%s)",
                (user_id, -item["points_cost"], catalog_item_id, f"兌換：{item['name']}"),
            )
            # If performance_hours category, credit perf_hours
            if item["category"] == "performance_hours":
                perf_hrs = round(item["points_cost"] * POINTS_TO_HOURS_RATE, 2)
                cur.execute(
                    "UPDATE users SET perf_hours = perf_hours + %s WHERE id=%s",
                    (perf_hrs, user_id),
                )

            cur.execute(
                "SELECT kgi_points, learning_hours, perf_hours FROM users WHERE id=%s",
                (user_id,),
            )
            wallet = cur.fetchone()
        conn.commit()
        return {
            "ok": True,
            "item_name": item["name"],
            "points_spent": item["points_cost"],
            "kgi_points": wallet["kgi_points"],
            "learning_hours": float(wallet["learning_hours"]),
            "perf_hours": float(wallet["perf_hours"]),
        }
    finally:
        conn.close()


def get_catalog(active_only: bool = True) -> list:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if active_only:
                cur.execute(
                    "SELECT * FROM reward_catalog WHERE is_active=1 ORDER BY points_cost"
                )
            else:
                cur.execute("SELECT * FROM reward_catalog ORDER BY points_cost")
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
