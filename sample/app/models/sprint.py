from datetime import datetime
from app.core.database import get_conn


def start_sprint(user_id: int, module_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sprint_sessions (agent_id, module_id, start_ts, completion_status) VALUES (%s,%s,%s,'abandoned')",
                (user_id, module_id, datetime.utcnow()),
            )
            sprint_id = cur.lastrowid
            cur.execute(
                "INSERT INTO learning_journey_map (sprint_id) VALUES (%s)",
                (sprint_id,),
            )
        conn.commit()
        return sprint_id
    finally:
        conn.close()


def increment_tab_switch(sprint_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sprint_sessions SET tab_switch_count = tab_switch_count + 1 WHERE sprint_id=%s",
                (sprint_id,),
            )
        conn.commit()
    finally:
        conn.close()


def end_sprint(sprint_id: int, tab_switch_count: int, completion_status: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            now = datetime.utcnow()
            cur.execute(
                "UPDATE sprint_sessions SET end_ts=%s, tab_switch_count=%s, completion_status=%s WHERE sprint_id=%s",
                (now, tab_switch_count, completion_status, sprint_id),
            )
            # Accumulate learn seconds into user's cumulative total
            cur.execute(
                "SELECT agent_id, start_ts FROM sprint_sessions WHERE sprint_id=%s",
                (sprint_id,),
            )
            row = cur.fetchone()
            if row and row["start_ts"]:
                elapsed = int((now - row["start_ts"]).total_seconds())
                if elapsed > 0:
                    cur.execute(
                        "UPDATE users SET cumulative_learn_seconds = cumulative_learn_seconds + %s WHERE id=%s",
                        (elapsed, row["agent_id"]),
                    )
                    learn_hrs = round(elapsed / 3600, 2)
                    if learn_hrs > 0:
                        cur.execute(
                            "UPDATE users SET learning_hours = learning_hours + %s WHERE id=%s",
                            (learn_hrs, row["agent_id"]),
                        )
                        cur.execute(
                            "INSERT INTO reward_transactions (user_id, txn_type, hours_delta, note) "
                            "VALUES (%s,'earn_hours_study',%s,%s)",
                            (row["agent_id"], learn_hrs, f"完成學習衝刺（{elapsed} 秒）"),
                        )
        conn.commit()
    finally:
        conn.close()
