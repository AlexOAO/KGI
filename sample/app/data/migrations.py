from app.core.database import get_conn


def run_migrations():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='total_xp'"
            )
            if cur.fetchone()["cnt"] == 0:
                cur.execute("ALTER TABLE users ADD COLUMN total_xp INT NOT NULL DEFAULT 0")

            cur.execute(
                "SELECT COUNT(*) as cnt FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='streak_freeze_count'"
            )
            if cur.fetchone()["cnt"] == 0:
                cur.execute("ALTER TABLE users ADD COLUMN streak_freeze_count INT NOT NULL DEFAULT 0")

            cur.execute(
                "SELECT COUNT(*) as cnt FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='quiz_sessions' AND COLUMN_NAME='xp_earned'"
            )
            if cur.fetchone()["cnt"] == 0:
                cur.execute("ALTER TABLE quiz_sessions ADD COLUMN xp_earned INT NOT NULL DEFAULT 0")

            cur.execute(
                "SELECT COUNT(*) as cnt FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='modules' AND COLUMN_NAME='source_document'"
            )
            if cur.fetchone()["cnt"] == 0:
                cur.execute("ALTER TABLE modules ADD COLUMN source_document VARCHAR(255) DEFAULT NULL")

        conn.commit()
        print("Migrations applied.")
    finally:
        conn.close()
    seed_extra_modules()


def seed_extra_modules():
    """Seed modules 13–18 if total module count is below 18."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM modules")
            if cur.fetchone()["cnt"] >= 18:
                return

            extra_modules = [
                ("外匯及跨境資金管理法規", "#外匯管理 #跨境資金", 420, 3),
                ("反賄賂與廉潔合規", "#反賄賂 #廉潔合規", 420, 2),
                ("上市櫃公司資訊揭露義務", "#資訊揭露 #上市公司", 420, 2),
                ("資訊安全與金融網路韌性", "#資安合規 #網路韌性", 420, 3),
                ("永續金融與ESG合規", "#ESG #永續金融", 420, 3),
                ("金融監理裁罰案例精析", "#裁罰案例 #監理實務", 420, 4),
            ]
            module_ids = []
            for title, tag, duration, diff in extra_modules:
                cur.execute(
                    "INSERT INTO modules (title, topic_tag, duration_seconds, difficulty_level) VALUES (%s,%s,%s,%s)",
                    (title, tag, duration, diff),
                )
                module_ids.append(cur.lastrowid)

            flashcard_data = {
                0: [
                    "外匯管制核心依據為《管理外匯條例》，居住民年累計結匯金額達新臺幣等值500萬美元以上者，須向中央銀行申報資金來源及用途。",
                    "跨境電匯Travel Rule：依FATF建議，金額達等值1萬美元以上之跨境匯款，金融機構須完整傳遞匯款人及受款人姓名、帳號、地址等資訊。",
                    "境外法人在臺開設外幣帳戶，須提供設立文件及最終受益所有人（UBO）資訊，金融機構應至少每年複審一次帳戶狀況。",
                    "SWIFT制裁篩查：辦理國際匯款前，須比對OFAC、UN、EU等制裁名單，命中者不得交易並應向主管機關通報，以免違反國際制裁規定。",
                    "違反《管理外匯條例》申報義務者，可處新臺幣三萬元至六十萬元罰鍰；若涉及洗錢，另依洗錢防制法加重刑事及行政責任。",
                ],
                1: [
                    "廉潔合規的核心法規依據包括《貪污治罪條例》及《銀行法》，禁止金融從業人員收受或給予不正利益，違者依法追究刑事責任。",
                    "利益衝突管理：金融從業人員於個人利益可能影響公正執行職務時，應主動書面申報，並迴避相關決策，確保客觀性。",
                    "反腐敗三要素：預防（政策制定與員工訓練）、偵測（吹哨管道與交易監控）、回應（調查程序與懲處機制），三者缺一不可。",
                    "禮品與招待管理：多數金融機構設定單次接受禮品上限（常見為新臺幣500元），所有禮品須登記備查，避免商業賄賂風險。",
                    "吹哨者保護：員工透過獨立管道（匿名熱線、電郵）檢舉廉潔問題，依《公益揭發者保護法》受保護，雇主不得以任何形式報復。",
                ],
                2: [
                    "重大訊息即時揭露：上市（櫃）公司發生重大事件（簽署重大合約、重大訴訟、董監事異動等），應於事實發生後兩小時內透過公開資訊觀測站揭露。",
                    "定期財務報告：上市公司須依規定期限公告年報及半年報，並由會計師查核或核閱，確保財務資訊透明、正確。",
                    "財報不實之法律責任：依證交法第20條及第32條，蓄意編製不實財務報告之發行人及負責人，須負民事損害賠償及刑事責任。",
                    "內部人持股申報：董事、監察人及持股逾10%之大股東為內部人，持股變動須依規定申報，主管機關據此監控潛在內線交易。",
                    "永續報告書義務：金管會要求實收資本額百億元以上之上市公司，須依規定年度起出具永續報告書，揭露環境、社會、治理績效指標。",
                ],
                3: [
                    "金融機構資安管理框架：金管會要求金融機構建立資訊安全管理制度（ISMS），主要參考ISO 27001標準，並每年辦理資安評估。",
                    "重大資安事件通報義務：金融機構發生重大資安事件（如資料外洩、勒索軟體攻擊），須於事件發生後1小時內通報金管會，並持續更新進展。",
                    "第三方委外資安責任：委外廠商發生資安事件，委外機構仍需承擔連帶責任，應在合約中明訂資安要求，並定期辦理廠商資安稽核。",
                    "業務持續計畫（BCP/DRP）：金融機構應定期測試災難復原計畫，確保核心系統在重大中斷後可於規定時間（通常4小時）內恢復正常運作。",
                    "零信任架構（Zero Trust）：現代資安設計原則—不預設任何內外網路信任，所有存取均需嚴格身分驗證、最小授權原則及持續行為監控。",
                ],
                4: [
                    "ESG三大支柱：環境（E）—氣候與資源；社會（S）—員工、社區與供應鏈；治理（G）—董事會、透明度與廉潔。金融機構將ESG整合至投融資決策。",
                    "TCFD氣候風險揭露框架涵蓋四大主題：治理（如何監督氣候風險）、策略（氣候對業務影響）、風險管理（識別流程）及指標與目標。",
                    "金管會「綠色金融行動方案3.0」：要求金融機構強化氣候風險管理、ESG資訊揭露品質，以及對永續相關投資與授信業務的整合。",
                    "永續連結貸款（SLL）：貸款利率與借款人的ESG績效關鍵指標（KPI）掛鉤，借款人達標可享利率優惠，反之則加碼，激勵永續行動。",
                    "漂綠風險（Greenwashing）：誇大或虛偽標榜ESG績效或永續商品特性，可能面臨主管機關調查、罰鍰及嚴重聲譽損失，需確保揭露資訊真實準確。",
                ],
                5: [
                    "金管會裁罰依據：依銀行法第129條、保險法第168條、證交法第178條等各業別法規，對違規金融機構裁處罰鍰，情節重大可命令停業或撤照。",
                    "常見裁罰態樣—洗錢防制缺失：未落實KYC審查、未依規申報CTR或STR、未建立有效的可疑交易監控機制，是金融機構遭裁罰的最常見原因。",
                    "常見裁罰態樣—適合性評估不足：未確實評估客戶風險承受能力即銷售高風險商品（如衍生商品、連動債），導致消費者受損並遭主管機關裁罰。",
                    "裁罰的連鎖效應：機構除面臨罰鍰外，還可能遭受業務暫停、聲譽受損、客戶流失，以及董事、高管依法被追究個人行政或刑事責任。",
                    "合規文化是根本防線：有效的合規文化需具備—高管層的明確支持（Tone from the Top）、充足資源投入、獨立法遵部門以及持續有效的員工教育訓練。",
                ],
            }

            question_data = {
                0: [
                    ("mcq", "居住民年累計結匯金額達多少美元以上，須向中央銀行申報？",
                     '["100萬美元","200萬美元","500萬美元","1000萬美元"]', "500萬美元"),
                    ("tf", "FATF的Travel Rule要求金融機構在跨境匯款中完整傳遞匯款人及受款人資訊。",
                     '["True","False"]', "True"),
                    ("mcq", "辦理國際匯款前比對OFAC制裁名單，主要目的為何？",
                     '["加快匯款速度","確認匯款對象未受國際制裁","計算匯率","核實收款帳戶"]', "確認匯款對象未受國際制裁"),
                    ("tf", "境外法人在臺開設外幣帳戶，無須提供最終受益所有人資訊。",
                     '["True","False"]', "False"),
                    ("mcq", "違反管理外匯條例申報義務，可處多少罰鍰？",
                     '["一萬至十萬元","三萬至六十萬元","十萬至一百萬元","五十萬至五百萬元"]', "三萬至六十萬元"),
                ],
                1: [
                    ("mcq", "金融從業人員面臨利益衝突時，正確做法為何？",
                     '["隱而不報繼續工作","主動書面申報並迴避相關決策","請同事代為處理","等主管詢問再說"]', "主動書面申報並迴避相關決策"),
                    ("tf", "反腐敗合規計畫的三要素為預防、偵測與回應。",
                     '["True","False"]', "True"),
                    ("mcq", "金融機構通常設定接受單次禮品的上限約為多少？",
                     '["新臺幣100元","新臺幣500元","新臺幣3000元","無上限"]', "新臺幣500元"),
                    ("tf", "員工依吹哨者保護制度檢舉後，雇主可合法予以降薪報復。",
                     '["True","False"]', "False"),
                    ("mcq", "《公益揭發者保護法》的主要目的為何？",
                     '["保護企業商業機密","保護檢舉不當行為之人員不受報復","規範企業財報","限制媒體報導"]', "保護檢舉不當行為之人員不受報復"),
                ],
                2: [
                    ("mcq", "上市公司發生重大事件，應於事實發生後多久內透過公開資訊觀測站揭露？",
                     '["三十分鐘內","兩小時內","二十四小時內","一週內"]', "兩小時內"),
                    ("tf", "上市公司董事為內部人，其持股變動需依規定申報。",
                     '["True","False"]', "True"),
                    ("mcq", "蓄意編製不實財務報告，依證交法規定須負何種責任？",
                     '["僅口頭警告","民事損害賠償及刑事責任","暫停上市資格","只需更正財報"]', "民事損害賠償及刑事責任"),
                    ("tf", "半年度財務報告不需要會計師核閱。",
                     '["True","False"]', "False"),
                    ("mcq", "金管會要求哪類上市公司須出具永續報告書？",
                     '["所有上市公司","實收資本額百億元以上公司","外資持股逾五成公司","員工人數逾千人公司"]', "實收資本額百億元以上公司"),
                ],
                3: [
                    ("mcq", "金融機構發生重大資安事件後，須於多久內通報金管會？",
                     '["30分鐘內","1小時內","4小時內","24小時內"]', "1小時內"),
                    ("tf", "委外廠商發生資安事件，委外金融機構無需負任何責任。",
                     '["True","False"]', "False"),
                    ("mcq", "ISO 27001主要是何種管理標準？",
                     '["財務管理","資訊安全管理系統","環境管理","品質管理"]', "資訊安全管理系統"),
                    ("tf", "業務持續計畫（BCP）需要定期測試以確保有效運作。",
                     '["True","False"]', "True"),
                    ("mcq", "零信任架構（Zero Trust）的核心原則為何？",
                     '["信任內網所有設備","不預設信任，所有存取皆需驗證","只驗證外部連線","信任已驗證一次的使用者"]', "不預設信任，所有存取皆需驗證"),
                ],
                4: [
                    ("mcq", "TCFD氣候風險揭露框架涵蓋哪四大主題？",
                     '["政策、法律、市場、聲譽","治理、策略、風險管理及指標與目標","環境、社會、治理、財務","氣候、水資源、生物多樣性、土地"]', "治理、策略、風險管理及指標與目標"),
                    ("tf", "永續連結貸款（SLL）的利率與借款人ESG績效指標掛鉤。",
                     '["True","False"]', "True"),
                    ("mcq", "「漂綠」（Greenwashing）行為可能帶來哪些主要風險？",
                     '["提高融資成本","監管處罰及聲譽損失","增加碳排放","降低ESG評分"]', "監管處罰及聲譽損失"),
                    ("tf", "金管會綠色金融行動方案要求所有金融機構立即撤出高碳產業。",
                     '["True","False"]', "False"),
                    ("mcq", "ESG中的「G」代表什麼？",
                     '["全球化（Globalization）","治理（Governance）","增長（Growth）","綠色（Green）"]', "治理（Governance）"),
                ],
                5: [
                    ("mcq", "金融機構因洗錢防制缺失遭裁罰，最常見的原因為何？",
                     '["員工薪資過高","未落實KYC或未依規申報CTR/STR","辦公室裝潢違規","過度核貸"]', "未落實KYC或未依規申報CTR/STR"),
                    ("tf", "金融機構遭主管機關裁罰後，高管人員可能被追究個人責任。",
                     '["True","False"]', "True"),
                    ("mcq", "金管會對銀行裁罰的主要法律依據為何？",
                     '["民法","銀行法第129條等業別法規","刑法","勞基法"]', "銀行法第129條等業別法規"),
                    ("tf", "適合性評估只需在客戶首次購買金融商品時辦理一次即可。",
                     '["True","False"]', "False"),
                    ("mcq", "有效合規文化的要素不包括下列哪一項？",
                     '["高管層明確支持","充足資源投入","持續員工訓練","減少法遵部門預算"]', "減少法遵部門預算"),
                ],
            }

            for idx, module_id in enumerate(module_ids):
                for seq, text in enumerate(flashcard_data.get(idx, []), start=1):
                    cur.execute(
                        "INSERT INTO flashcard_pages (module_id, sequence_number, page_text, image_url) VALUES (%s,%s,%s,%s)",
                        (module_id, seq, text, None),
                    )
                for qtype, prompt, options, answer in question_data.get(idx, []):
                    cur.execute(
                        "INSERT INTO questions (module_id, type, prompt, options_json, correct_answer) VALUES (%s,%s,%s,%s,%s)",
                        (module_id, qtype, prompt, options, answer),
                    )
        conn.commit()
        print("Extra modules (13–18) seeded.")
    finally:
        conn.close()
