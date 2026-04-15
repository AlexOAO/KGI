"""Idempotent seed data - skips if users table is non-empty."""
import json
from app.core.database import get_connection
from app.core.auth import hash_password

USERS = [
    ("admin", "admin1234", "admin"),
    ("learner1", "learn1234", "learner"),
    ("learner2", "learn5678", "learner"),
]

MODULES = [
    {
        "title": "FSC 合規基礎",
        "topic_tag": "fsc_compliance",
        "duration_seconds": 420,
        "difficulty_level": "beginner",
        "cards": [
            "FSC（金融監督管理委員會）是台灣主要的金融監管機構，負責監管銀行、保險、證券等金融業。",
            "合規的核心原則包括：誠信經營、資訊透明、保護消費者權益、防範洗錢與資恐。",
            "金融從業人員必須定期完成合規培訓，確保了解最新法規要求與內部政策。",
            "客戶盡職調查（KYC）是合規的重要環節，包括確認客戶身份、了解資金來源及交易目的。",
            "違反合規規定可能導致罰款、業務暫停甚至吊銷執照，對機構聲譽造成嚴重損害。",
        ],
        "questions": [
            {
                "text": "FSC 是哪個機構的縮寫？",
                "options": ["金融監督管理委員會", "財政部", "中央銀行", "金融研訓院"],
                "answer": "金融監督管理委員會",
            },
            {
                "text": "KYC 代表什麼？",
                "options": ["了解您的客戶", "了解您的競爭對手", "了解您的合約", "了解您的法規"],
                "answer": "了解您的客戶",
            },
            {
                "text": "以下哪項不屬於合規核心原則？",
                "options": ["最大化利潤", "誠信經營", "資訊透明", "保護消費者權益"],
                "answer": "最大化利潤",
            },
        ],
    },
    {
        "title": "壽險產品概論",
        "topic_tag": "life_insurance",
        "duration_seconds": 420,
        "difficulty_level": "intermediate",
        "cards": [
            "壽險產品主要分為定期壽險、終身壽險和萬能壽險三大類，各有不同的保障期限與繳費方式。",
            "定期壽險提供特定期間的死亡保障，保費相對低廉，適合有短期財務需求的客戶。",
            "終身壽險提供終身保障，具有現金價值積累功能，可作為長期財務規劃工具。",
            "受益人是指當被保險人身故時，有權領取保險理賠金的人，可為法定繼承人或指定人。",
            "保單條款中的除外責任條款列明保險公司不承擔賠付責任的情況，如自殺、犯罪等。",
        ],
        "questions": [
            {
                "text": "以下哪種壽險提供最低保費但只有固定期限保障？",
                "options": ["定期壽險", "終身壽險", "萬能壽險", "投資型壽險"],
                "answer": "定期壽險",
            },
            {
                "text": "「受益人」在保險中指的是？",
                "options": ["有權領取保險理賠金的人", "繳納保費的人", "被保險的人", "銷售保險的人"],
                "answer": "有權領取保險理賠金的人",
            },
            {
                "text": "終身壽險與定期壽險的主要差異是？",
                "options": ["終身壽險提供終身保障且有現金價值", "定期壽險保費較高", "終身壽險只保障特定期間", "兩者完全相同"],
                "answer": "終身壽險提供終身保障且有現金價值",
            },
            {
                "text": "保單除外責任條款的目的是？",
                "options": ["列明不承擔賠付責任的情況", "增加保障範圍", "降低保費", "擴大受益人範圍"],
                "answer": "列明不承擔賠付責任的情況",
            },
        ],
    },
    {
        "title": "ILP 投資連結保險法規",
        "topic_tag": "ilp_regulation",
        "duration_seconds": 420,
        "difficulty_level": "advanced",
        "cards": [
            "投資連結保險（ILP）結合了人壽保險保障與投資功能，保單價值隨所選投資基金表現而波動。",
            "ILP 銷售人員必須具備保險業務員及投信投顧相關資格，並向客戶充分揭露風險。",
            "適合度評估（Suitability Assessment）是 ILP 銷售的法定要求，確保產品符合客戶的風險承受能力。",
            "ILP 的費用結構包括：保單管理費、基金管理費、保險成本及解約費用等，必須清楚向客戶說明。",
            "監管機關要求 ILP 銷售必須提供產品說明書（PDS），內含完整的風險揭露與費用資訊。",
        ],
        "questions": [
            {
                "text": "ILP 的全名是什麼？",
                "options": ["投資連結保險", "利率連結保單", "指數連結產品", "國際壽險計畫"],
                "answer": "投資連結保險",
            },
            {
                "text": "銷售 ILP 前必須進行哪項評估？",
                "options": ["適合度評估", "信用評估", "健康評估", "財富評估"],
                "answer": "適合度評估",
            },
            {
                "text": "PDS 在 ILP 銷售中代表什麼？",
                "options": ["產品說明書", "保費折扣方案", "個人資料表", "保單分析系統"],
                "answer": "產品說明書",
            },
            {
                "text": "以下哪項不是 ILP 的常見費用？",
                "options": ["醫療報銷費", "基金管理費", "保單管理費", "解約費用"],
                "answer": "醫療報銷費",
            },
            {
                "text": "ILP 保單價值如何決定？",
                "options": ["隨所選投資基金表現而波動", "固定不變", "由保險公司保證", "依通貨膨脹調整"],
                "answer": "隨所選投資基金表現而波動",
            },
        ],
    },
]

def seed():
    """Run idempotent seed. Skip if users table already has data."""
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return

    # Create users
    from app.models.user import create_user
    for username, password, role in USERS:
        create_user(username, password, role)

    # Create modules, cards, questions
    from app.models.module import create_module, create_flashcard
    from app.models.quiz import create_question

    for mod_data in MODULES:
        module_id = create_module(
            mod_data["title"],
            mod_data["topic_tag"],
            mod_data["duration_seconds"],
            mod_data["difficulty_level"],
        )
        for i, card_text in enumerate(mod_data["cards"], 1):
            create_flashcard(module_id, i, card_text)
        for q in mod_data["questions"]:
            create_question(module_id, q["text"], q["options"], q["answer"])
