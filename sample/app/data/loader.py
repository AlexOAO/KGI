import json
import os
from app.core.database import get_conn
from app.core.config import DATA_DIR


def _load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _load_json_array_or_jsonl(path):
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    if content.startswith("["):
        return json.loads(content)
    # Try JSONL
    records = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def load_compliance_data():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 裁罰.json
            penalty_path = os.path.join(DATA_DIR, "裁罰.json")
            if os.path.exists(penalty_path):
                records = _load_json_array_or_jsonl(penalty_path)
                for r in records:
                    cur.execute(
                        "INSERT INTO comp_penalties (category, institution, title, date, content) VALUES (%s,%s,%s,%s,%s)",
                        (r.get("資料類別"), r.get("機構名稱"), r.get("標題"), r.get("時間"), r.get("內文")),
                    )
                print(f"Loaded {len(records)} penalty records")

            # 法規.json
            reg_path = os.path.join(DATA_DIR, "法規.json")
            if os.path.exists(reg_path):
                records = _load_json_array_or_jsonl(reg_path)
                for r in records:
                    cur.execute(
                        "INSERT INTO comp_regulations (category, title, date, content) VALUES (%s,%s,%s,%s)",
                        (r.get("資料類別"), r.get("標題"), r.get("時間"), r.get("內文")),
                    )
                print(f"Loaded {len(records)} regulation records")

            # 全國法規資料庫.jsonl
            nat_path = os.path.join(DATA_DIR, "全國法規資料庫.jsonl")
            if os.path.exists(nat_path):
                records = _load_jsonl(nat_path)
                for r in records:
                    cur.execute(
                        "INSERT INTO comp_national_laws (law_name, law_level, law_url, article_no, article_content, article_type) VALUES (%s,%s,%s,%s,%s,%s)",
                        (r.get("LawName"), r.get("LawLevel"), r.get("LawURL"), r.get("ArticleNo"), r.get("ArticleConctent"), r.get("ArticleType")),
                    )
                print(f"Loaded {len(records)} national law records")

            # 主管法規資料集.jsonl
            fsc_path = os.path.join(DATA_DIR, "主管法規資料集.jsonl")
            if os.path.exists(fsc_path):
                records = _load_jsonl(fsc_path)
                for r in records:
                    cur.execute(
                        "INSERT INTO comp_fsc_directives (institution, category, law_system, publish_date, document_no, change_type, law_status, effective_date, law_name, subject, content) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            r.get("機構名稱"), r.get("法規類別"), r.get("法規體系"),
                            r.get("公發布日"), r.get("發文字號"), r.get("異動性質"),
                            r.get("生效狀態"), r.get("生效日期"), r.get("法規名稱"),
                            r.get("主旨"), r.get("法規內容"),
                        ),
                    )
                print(f"Loaded {len(records)} FSC directive records")

        conn.commit()
    finally:
        conn.close()


def seed_demo_data():
    import bcrypt
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Demo users
            for username, password, role in [("learner1", "pass123", "learner"), ("admin1", "admin123", "admin")]:
                pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cur.execute(
                    "INSERT IGNORE INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
                    (username, pw_hash, role),
                )

            # Demo modules
            modules = [
                ("保險法基礎概念", "#保險法 #合規", 420, 1),
                ("金融消費者保護法要點", "#消費者保護 #金融法規", 420, 2),
                ("洗錢防制法規重點", "#洗錢防制 #合規", 420, 2),
            ]
            module_ids = []
            for title, tag, duration, diff in modules:
                cur.execute(
                    "INSERT INTO modules (title, topic_tag, duration_seconds, difficulty_level) VALUES (%s,%s,%s,%s)",
                    (title, tag, duration, diff),
                )
                module_ids.append(cur.lastrowid)

            # Flashcards for each module
            flashcard_data = {
                0: [
                    ("保險法第1條規定，保險為當事人約定，一方交付保險費於他方，他方對於因不可預料，或不可抗力之事故所致之損害，負擔賠償財物之行為。", None),
                    ("保險業的設立需符合保險法第136條規定，需向主管機關申請核准，資本額須達法定標準，並繳存保證金。", None),
                    ("保險合約的基本要素包括：要保人、被保險人、受益人、保險人四方，各有其法律義務與權利。", None),
                    ("保險法第54條規定，保險契約應以書面為之，並應載明法定事項，違反者保險契約無效。", None),
                    ("保險費的繳納方式分為一次繳清、分期繳納等，要保人需依約定方式繳納，逾期可能導致契約失效。", None),
                ],
                1: [
                    ("金融消費者保護法旨在保護金融消費者權益，規範金融服務業提供金融商品或服務之行為。", None),
                    ("金融服務業對金融消費者負有適合性原則義務，須了解消費者的財務狀況、風險承受能力及投資目的。", None),
                    ("金融消費者評議中心提供爭議解決機制，消費者可向評議中心申請評議，金融服務業須接受評議結果。", None),
                    ("金融服務業提供金融商品前，須進行商品審查及風險評估，確保商品適合目標客群。", None),
                    ("違反金融消費者保護法規定者，主管機關得處以罰鍰，情節重大者得撤銷許可或停業。", None),
                ],
                2: [
                    ("洗錢防制法規定金融機構須執行客戶盡職調查（KYC），確認客戶身分及交易目的。", None),
                    ("可疑交易申報（STR）：金融機構發現可疑交易須於特定時間內向調查局申報，不得告知客戶。", None),
                    ("大額現金交易申報（CTR）：單筆現金交易達新臺幣50萬元以上須向主管機關申報。", None),
                    ("金融機構應建立洗錢防制內部控制制度，包括風險評估、監控機制及員工訓練計畫。", None),
                    ("違反洗錢防制義務者，依洗錢防制法第6條、第7條規定，得處罰鍰或刑事處罰。", None),
                ],
            }

            for idx, module_id in enumerate(module_ids):
                for seq, (text, img) in enumerate(flashcard_data[idx], start=1):
                    cur.execute(
                        "INSERT INTO flashcard_pages (module_id, sequence_number, page_text, image_url) VALUES (%s,%s,%s,%s)",
                        (module_id, seq, text, img),
                    )

            # Quiz questions for each module
            question_data = {
                0: [
                    ("mcq", "保險法第1條中，保險的核心定義是什麼？",
                     '["當事人約定互相幫助的行為","當事人約定一方交付保險費，他方對不可預料事故所致損害負賠償責任","政府對人民提供保障的制度","銀行對存款人提供的保障服務"]',
                     "當事人約定一方交付保險費，他方對不可預料事故所致損害負賠償責任"),
                    ("tf", "保險業設立不需要向主管機關申請核准。", '["True","False"]', "False"),
                    ("mcq", "保險契約應以何種形式訂立？", '["口頭","書面","電子郵件","任何形式均可"]', "書面"),
                    ("tf", "保險費逾期繳納可能導致保險契約失效。", '["True","False"]', "True"),
                    ("mcq", "保險合約的基本當事人不包括下列哪一方？",
                     '["要保人","被保險人","受益人","仲裁人"]', "仲裁人"),
                ],
                1: [
                    ("mcq", "金融服務業對金融消費者的適合性原則義務，主要是要了解消費者的什麼？",
                     '["外貌特徵","財務狀況、風險承受能力及投資目的","家庭背景","社交媒體使用習慣"]',
                     "財務狀況、風險承受能力及投資目的"),
                    ("tf", "金融消費者可以向金融消費者評議中心申請爭議評議。", '["True","False"]', "True"),
                    ("mcq", "違反金融消費者保護法，情節重大時主管機關可以採取什麼措施？",
                     '["僅口頭警告","撤銷許可或停業","降低評級","公開道歉"]', "撤銷許可或停業"),
                    ("tf", "金融服務業提供金融商品前，不需要進行商品審查。", '["True","False"]', "False"),
                    ("mcq", "金融消費者保護法主要目的為何？",
                     '["增加金融業者利潤","保護金融消費者權益","降低金融業監管","促進外資進入"]',
                     "保護金融消費者權益"),
                ],
                2: [
                    ("mcq", "KYC代表什麼？", '["Know Your Customer","Keep Your Cash","Know Your Company","Keep Your Contract"]', "Know Your Customer"),
                    ("tf", "金融機構發現可疑交易後，可以告知客戶已申報。", '["True","False"]', "False"),
                    ("mcq", "單筆現金交易達多少金額以上須申報CTR？",
                     '["新臺幣10萬元","新臺幣30萬元","新臺幣50萬元","新臺幣100萬元"]', "新臺幣50萬元"),
                    ("tf", "洗錢防制內部控制制度需包含員工訓練計畫。", '["True","False"]', "True"),
                    ("mcq", "STR是指什麼申報？",
                     '["大額現金交易申報","可疑交易申報","定期交易申報","跨境匯款申報"]', "可疑交易申報"),
                ],
            }

            for idx, module_id in enumerate(module_ids):
                for qtype, prompt, options, answer in question_data[idx]:
                    cur.execute(
                        "INSERT INTO questions (module_id, type, prompt, options_json, correct_answer) VALUES (%s,%s,%s,%s,%s)",
                        (module_id, qtype, prompt, options, answer),
                    )

        conn.commit()
        print("Demo data seeded successfully")
    finally:
        conn.close()
