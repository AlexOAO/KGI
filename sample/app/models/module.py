from app.core.database import get_conn


def get_modules():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM modules ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()


def get_module(module_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM modules WHERE id = %s", (module_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_flashcards(module_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM flashcard_pages WHERE module_id = %s ORDER BY RAND() LIMIT 5",
                (module_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()
