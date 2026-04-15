"""Lazy-load compliance data from JSON/JSONL files into SQLite FTS5 tables,
then generate 3 compliance learning modules."""
import json
import os
import sqlite3
from datetime import datetime

from app.core.config import DB_PATH, DATA_DIR

BATCH_SIZE = 500

EXPECTED_COUNTS = {
    "compliance_penalties":    1116,
    "compliance_regulations":  514,
    "compliance_national_laws": 46000,   # ArticleType='A' subset
    "compliance_fsc_regs":     6142,
}


# ── Bulk connection (performance settings) ──────────────────────────────────

def _bulk_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    return conn


# ── Lazy-load guards ─────────────────────────────────────────────────────────

def _is_loaded(conn, table_name):
    row = conn.execute(
        "SELECT record_count FROM compliance_load_status WHERE table_name = ?",
        (table_name,)
    ).fetchone()
    expected = EXPECTED_COUNTS.get(table_name, 1)
    return row is not None and row[0] >= expected


def _mark_loaded(conn, table_name, count):
    conn.execute(
        "INSERT OR REPLACE INTO compliance_load_status(table_name, record_count, loaded_at)"
        " VALUES (?, ?, ?)",
        (table_name, count, datetime.now().isoformat())
    )
    conn.commit()


# ── Loaders ──────────────────────────────────────────────────────────────────

def _load_penalties(conn):
    if _is_loaded(conn, "compliance_penalties"):
        print("  裁罰資料已載入，跳過")
        return
    print("  載入裁罰資料...")
    path = os.path.join(DATA_DIR, "裁罰.json")
    batch, count = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            batch.append((
                obj.get("資料類別", "") or "",
                obj.get("機構名稱", "") or "",
                obj.get("標題", "") or "",
                obj.get("時間", "") or "",
                obj.get("內文", "") or "",
            ))
            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO compliance_penalties(category,institution,title,issued_date,content)"
                    " VALUES(?,?,?,?,?)", batch
                )
                conn.commit()
                count += len(batch)
                batch = []
    if batch:
        conn.executemany(
            "INSERT INTO compliance_penalties(category,institution,title,issued_date,content)"
            " VALUES(?,?,?,?,?)", batch
        )
        conn.commit()
        count += len(batch)
    _mark_loaded(conn, "compliance_penalties", count)
    print(f"  裁罰資料載入完成：{count} 筆")


def _load_regulations(conn):
    if _is_loaded(conn, "compliance_regulations"):
        print("  法規資料已載入，跳過")
        return
    print("  載入法規資料...")
    path = os.path.join(DATA_DIR, "法規.json")
    batch, count = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            batch.append((
                obj.get("資料類別", "") or "",
                obj.get("標題", "") or "",
                obj.get("時間", "") or "",
                obj.get("內文", "") or "",
            ))
            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO compliance_regulations(category,title,issued_date,content)"
                    " VALUES(?,?,?,?)", batch
                )
                conn.commit()
                count += len(batch)
                batch = []
    if batch:
        conn.executemany(
            "INSERT INTO compliance_regulations(category,title,issued_date,content)"
            " VALUES(?,?,?,?)", batch
        )
        conn.commit()
        count += len(batch)
    _mark_loaded(conn, "compliance_regulations", count)
    print(f"  法規資料載入完成：{count} 筆")


def _load_national_laws(conn):
    if _is_loaded(conn, "compliance_national_laws"):
        print("  全國法規資料已載入，跳過")
        return
    print("  載入全國法規資料（首次約 15–30 秒）...")
    path = os.path.join(DATA_DIR, "全國法規資料庫 (4).jsonl")
    batch, count = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("ArticleType") != "A":
                continue
            batch.append((
                obj.get("LawName", "") or "",
                obj.get("LawLevel", "") or "",
                obj.get("LawURL", "") or "",
                obj.get("ArticleNo", "") or "",
                obj.get("ArticleConctent", "") or "",
            ))
            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO compliance_national_laws"
                    "(law_name,law_level,law_url,article_no,article_content)"
                    " VALUES(?,?,?,?,?)", batch
                )
                conn.commit()
                count += len(batch)
                batch = []
    if batch:
        conn.executemany(
            "INSERT INTO compliance_national_laws"
            "(law_name,law_level,law_url,article_no,article_content)"
            " VALUES(?,?,?,?,?)", batch
        )
        conn.commit()
        count += len(batch)
    _mark_loaded(conn, "compliance_national_laws", count)
    print(f"  全國法規資料載入完成：{count} 筆")


def _load_fsc_regs(conn):
    if _is_loaded(conn, "compliance_fsc_regs"):
        print("  主管法規資料已載入，跳過")
        return
    print("  載入主管法規資料...")
    path = os.path.join(DATA_DIR, "處理後_主管法規資料集.jsonl")
    batch, count = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            batch.append((
                obj.get("機構名稱", "") or "",
                obj.get("法規類別", "") or "",
                obj.get("法規名稱", "") or "",
                obj.get("主旨", "") or "",
                obj.get("生效日期", "") or "",
                obj.get("修正日期", "") or "",
                obj.get("異動性質", "") or "",
                obj.get("法規內容", "") or "",
            ))
            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO compliance_fsc_regs"
                    "(institution,reg_category,reg_name,purpose,"
                    " effective_date,amendment_date,change_type,content)"
                    " VALUES(?,?,?,?,?,?,?,?)", batch
                )
                conn.commit()
                count += len(batch)
                batch = []
    if batch:
        conn.executemany(
            "INSERT INTO compliance_fsc_regs"
            "(institution,reg_category,reg_name,purpose,"
            " effective_date,amendment_date,change_type,content)"
            " VALUES(?,?,?,?,?,?,?,?)", batch
        )
        conn.commit()
        count += len(batch)
    _mark_loaded(conn, "compliance_fsc_regs", count)
    print(f"  主管法規資料載入完成：{count} 筆")


def load_all_compliance_data():
    """Lazily load all 4 compliance datasets into the DB."""
    conn = _bulk_conn()
    try:
        _load_penalties(conn)
        _load_regulations(conn)
        _load_national_laws(conn)
        _load_fsc_regs(conn)
    finally:
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.close()


# ── Module generators ────────────────────────────────────────────────────────

def _gen_penalty_questions(conn):
    rows = conn.execute(
        "SELECT institution, title, issued_date FROM compliance_penalties"
        " WHERE category='重大裁罰' ORDER BY issued_date DESC LIMIT 10"
    ).fetchall()
    if not rows:
        return []

    # Distinct institutions for distractors
    all_insts = ["保險局", "銀行局", "證期局", "金管會"]

    q1_case = rows[0]
    inst = q1_case["institution"]
    opts1 = [inst] + [i for i in all_insts if i != inst][:3]

    q2_case = rows[1] if len(rows) > 1 else rows[0]
    title_short = q2_case["title"][:40]

    return [
        {
            "text": f"「{title_short}…」此裁罰案例由哪個主管機構負責監理？",
            "options": opts1,
            "answer": inst,
        },
        {
            "text": "以下哪種裁罰類型通常表示違規情節較為嚴重？",
            "options": ["重大裁罰", "非重大裁罰", "行政指導", "警示函"],
            "answer": "重大裁罰",
        },
        {
            "text": "金融機構違規遭裁罰後，正確的後續處理方式為何？",
            "options": [
                "配合主管機關要求，立即改善並回報處理結果",
                "提出申訴並拒絕繳納罰款直到法院判決",
                "暫停所有業務直到主管機關解除限制",
                "更換董事會成員即可免除法律責任",
            ],
            "answer": "配合主管機關要求，立即改善並回報處理結果",
        },
    ]


def _gen_insurance_law_questions(conn):
    return [
        {
            "text": "依保險法第 1 條，「保險」的定義為何？",
            "options": [
                "當事人約定，一方交付保險費，他方對不可預料事故負擔賠償之行為",
                "政府強制要求購買的風險保障計畫",
                "金融機構提供的儲蓄與投資服務",
                "企業之間相互約定分擔損失的協議",
            ],
            "answer": "當事人約定，一方交付保險費，他方對不可預料事故負擔賠償之行為",
        },
        {
            "text": "依保險法定義，「保險人」指的是？",
            "options": [
                "經營保險事業，承保危險事故發生時負擔賠償義務之組織",
                "對保險標的具有保險利益，負有交付保費義務之人",
                "當被保險人死亡時，有權領取保險金之人",
                "負責銷售保險產品並收取佣金之代理人",
            ],
            "answer": "經營保險事業，承保危險事故發生時負擔賠償義務之組織",
        },
        {
            "text": "依保險法定義，「要保人」的核心義務為何？",
            "options": [
                "對保險標的具有保險利益並負有交付保險費義務",
                "監管保險公司的經營行為並確保合規",
                "代理保險人處理理賠事務",
                "提供保險事故鑑定服務",
            ],
            "answer": "對保險標的具有保險利益並負有交付保險費義務",
        },
        {
            "text": "保險法在台灣的法律位階屬於？",
            "options": ["法律（立法院通過）", "行政規則", "地方自治條例", "國際條約"],
            "answer": "法律（立法院通過）",
        },
    ]


def _gen_fsc_reg_questions(conn):
    rows = conn.execute(
        "SELECT title, issued_date FROM compliance_regulations"
        " WHERE category='金管會' ORDER BY issued_date DESC LIMIT 5"
    ).fetchall()

    q2_title = rows[0]["title"][:30] if rows else "最新金管會函令"
    q2_date = rows[0]["issued_date"] if rows else "近期"

    return [
        {
            "text": "以下哪個機構發布的函令屬於金融監理「監理函令」？",
            "options": [
                "金融監督管理委員會（金管會）",
                "內政部",
                "教育部",
                "衛生福利部",
            ],
            "answer": "金融監督管理委員會（金管會）",
        },
        {
            "text": f"金管會於 {q2_date} 發布「{q2_title}…」，此類函令的法律效力為何？",
            "options": [
                "對受監管機構具有拘束力，須依規辦理",
                "僅供參考，機構可自行決定是否遵從",
                "需經立法院通過才能生效",
                "只適用於外資金融機構",
            ],
            "answer": "對受監管機構具有拘束力，須依規辦理",
        },
        {
            "text": "金融業者收到金管會函令時，標準的合規處理程序為何？",
            "options": [
                "依函令內容調整業務流程，確保符合監理要求",
                "可自行決定是否遵守，不影響執照",
                "轉知客戶後即完成義務",
                "等待下次例行檢查時再集中處理",
            ],
            "answer": "依函令內容調整業務流程，確保符合監理要求",
        },
    ]


def generate_compliance_modules():
    """Idempotently create 3 compliance learning modules from DB data."""
    from app.core.database import get_connection
    from app.models.module import create_module, create_flashcard
    from app.models.quiz import create_question

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM modules"
            " WHERE topic_tag IN ('compliance_penalties','insurance_law','fsc_regulatory')"
        ).fetchone()[0]
        if existing >= 3:
            print("  合規學習模組已存在，跳過")
            return

        print("  生成合規學習模組...")

        # ── Module 1: 近期重大裁罰案例 ──────────────────────────────────────
        cases = conn.execute(
            "SELECT institution, title, issued_date, content FROM compliance_penalties"
            " WHERE category='重大裁罰' ORDER BY issued_date DESC LIMIT 50"
        ).fetchall()

        if cases:
            mod1_id = create_module(
                "近期重大裁罰案例",
                "compliance_penalties",
                420,
                "intermediate",
            )
            for i, c in enumerate(cases[:8], 1):
                card_text = (
                    f"### {c['institution']} — {c['issued_date']}\n\n"
                    f"**{c['title'][:100]}**\n\n"
                    f"{(c['content'] or '')[:300]}"
                )
                create_flashcard(mod1_id, i, card_text)
            for q in _gen_penalty_questions(conn):
                create_question(mod1_id, q["text"], q["options"], q["answer"])
            print("  ✓ 近期重大裁罰案例")

        # ── Module 2: 保險法核心條文 ─────────────────────────────────────────
        target_articles = ["第 1 條", "第 2 條", "第 3 條", "第 5 條",
                           "第 13 條", "第 36 條", "第 54 條",
                           "第 105 條", "第 138 條", "第 149 條"]
        arts = []
        for art_no in target_articles:
            row = conn.execute(
                "SELECT article_no, article_content FROM compliance_national_laws"
                " WHERE law_name='保險法' AND article_no=?", (art_no,)
            ).fetchone()
            if row:
                arts.append(row)

        # Fallback: take first 10 if specific articles not found
        if len(arts) < 5:
            arts = conn.execute(
                "SELECT article_no, article_content FROM compliance_national_laws"
                " WHERE law_name='保險法' ORDER BY id LIMIT 10"
            ).fetchall()

        if arts:
            mod2_id = create_module(
                "保險法核心條文",
                "insurance_law",
                420,
                "intermediate",
            )
            for i, a in enumerate(arts[:10], 1):
                card_text = (
                    f"### 保險法 {a['article_no']}\n\n"
                    f"{a['article_content']}"
                )
                create_flashcard(mod2_id, i, card_text)
            for q in _gen_insurance_law_questions(conn):
                create_question(mod2_id, q["text"], q["options"], q["answer"])
            print("  ✓ 保險法核心條文")

        # ── Module 3: FSC 近期法規動態 ───────────────────────────────────────
        regs = conn.execute(
            "SELECT category, title, issued_date, content FROM compliance_regulations"
            " WHERE category='金管會' ORDER BY issued_date DESC LIMIT 30"
        ).fetchall()

        if regs:
            mod3_id = create_module(
                "FSC 近期法規動態",
                "fsc_regulatory",
                420,
                "intermediate",
            )
            for i, r in enumerate(regs[:7], 1):
                # Strip trailing date suffix added in title (e.g. "_2026-01-08")
                title = r["title"]
                if "_20" in title:
                    title = title[:title.rfind("_20")]
                card_text = (
                    f"### {title[:80]}\n\n"
                    f"**發布日期：** {r['issued_date']}\n\n"
                    f"{(r['content'] or '')[:300]}"
                )
                create_flashcard(mod3_id, i, card_text)
            for q in _gen_fsc_reg_questions(conn):
                create_question(mod3_id, q["text"], q["options"], q["answer"])
            print("  ✓ FSC 近期法規動態")

    print("  合規學習模組生成完成")
