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
                ("證券交易法核心概念", "#證券交易 #資本市場", 420, 2),
                ("銀行法監理要點", "#銀行法 #金融監理", 420, 2),
                ("個人資料保護法實務", "#個資法 #資安合規", 420, 2),
                ("期貨交易法規概述", "#期貨 #衍生性商品", 420, 3),
                ("投信投顧法規重點", "#投信 #投顧 #資產管理", 420, 3),
                ("公司治理與內部控制", "#公司治理 #內部控制", 420, 2),
                ("信託業法規要點", "#信託業 #財富管理", 420, 2),
                ("電子支付與金融科技法規", "#電子支付 #金融科技", 420, 3),
                ("資本適足率與風險管理", "#資本適足率 #巴塞爾協議", 420, 3),
            ]
            module_ids = []
            for title, tag, duration, diff in modules:
                cur.execute(
                    "INSERT INTO modules (title, topic_tag, duration_seconds, difficulty_level) VALUES (%s,%s,%s,%s)",
                    (title, tag, duration, diff),
                )
                module_ids.append(cur.lastrowid)

            # Flashcards for each module (index matches modules list above)
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
                3: [
                    ("證券交易法第1條揭示立法目的：發展國民經濟，並保障投資，以健全有價證券市場為宗旨。", None),
                    ("內線交易係指具有重大消息之內部人，在消息公開前買賣該公司股票，違反者依證交法第157條之1處以刑事責任。", None),
                    ("公開說明書係發行人募集有價證券時，應依法揭露公司財務、業務等重要資訊供投資人判斷。", None),
                    ("證券商分為承銷商、自營商、經紀商三類，各須取得主管機關許可，方可執行相應業務。", None),
                    ("市場操縱行為，包括連續買賣拉抬股價、散布謠言等，依法均屬禁止，違者依證交法受刑事及民事追訴。", None),
                ],
                4: [
                    ("銀行法第1條規定，為健全銀行業務經營，保障存款人權益，並適應產業發展，特制定本法。", None),
                    ("銀行分為商業銀行、專業銀行、信託投資公司三大類型，各有不同的業務範圍與監理要求。", None),
                    ("存款保險制度：中央存款保險公司對每一存款人在同一金融機構之存款，最高保障300萬元。", None),
                    ("銀行不得對同一人、同一關係人或同一關係企業給予超過法定比例之授信，以控制集中風險。", None),
                    ("金融控股公司法允許金融機構以控股方式跨業經營銀行、保險、證券等，但須符合防火牆規範。", None),
                ],
                5: [
                    ("個人資料保護法規範個人資料之蒐集、處理及利用，適用於公務機關與非公務機關，以保障個人隱私權。", None),
                    ("特種個人資料（敏感資料）包括醫療、基因、性生活、健康檢查等，蒐集處理須有明確法律依據。", None),
                    ("當事人得向資料控制者行使查詢、閱覽、更正、補充、刪除、停止蒐集、處理或利用之請求權。", None),
                    ("個資外洩通報義務：機關或企業發現個資外洩時，應在合理期限內通知受影響當事人，並採取補救措施。", None),
                    ("違反個資法規定者，依情節輕重，可處行政罰鍰；若意圖營利或造成重大損害，可追究刑事責任。", None),
                ],
                6: [
                    ("期貨交易係在集中市場依標準化合約買賣商品或金融工具，依期貨交易法受主管機關監管。", None),
                    ("期貨商須向主管機關申請許可，分為期貨經紀商（代客操作）及期貨自營商（自行買賣）。", None),
                    ("保證金制度：期貨交易人須繳付原始保證金，帳戶淨值低於維持保證金時，將收到追繳通知（Margin Call）。", None),
                    ("選擇權賦予買方在特定期間內，以約定價格買入（Call）或賣出（Put）標的物之權利，而非義務。", None),
                    ("期貨交易所依法設立，負責交易規則制定、結算及交割，並透過結算保證機制確保交易履行。", None),
                ],
                7: [
                    ("投信投顧法規範證券投資信託（基金）及顧問業務，旨在保護投資人並促進資本市場發展。", None),
                    ("證券投資信託事業（投信）負責募集共同基金，由基金保管機構（通常為銀行）保管基金資產。", None),
                    ("全權委託投資業務（代客操作）：投顧公司受客戶委託，全權決定有價證券買賣，需遵守嚴格利益迴避規範。", None),
                    ("投信投顧業者應公平對待所有客戶，禁止利用客戶資產為自己或特定人謀利，違者撤照並追究刑責。", None),
                    ("基金淨值（NAV）每日計算，投資人按NAV申購或贖回，基金費用（管理費、保管費）已內含於淨值中。", None),
                ],
                8: [
                    ("公司治理係指規範公司各方關係，包括董事會、管理層、股東和利害關係人之間的互動，以達到公司永續經營目標。", None),
                    ("內部控制五大要素：控制環境、風險評估、控制活動、資訊與溝通、監督作業，缺一不可，共同構成健全的內控體系。", None),
                    ("金融機構應設置獨立董事及審計委員會，審計委員會由全體獨立董事組成，負責監督財務報告及內部稽核工作。", None),
                    ("內部稽核部門應保持獨立性，直接向董事會或審計委員會報告，不受管理階層干預，確保稽核客觀公正。", None),
                    ("吹哨者保護制度：員工發現公司違規行為可向主管機關檢舉，受相關法律保護，不得遭受解雇、降薪等報復行為。", None),
                ],
                9: [
                    ("信託係指委託人將財產權移轉予受託人，使受託人依信託本旨，為受益人之利益管理或處分信託財產之法律關係。", None),
                    ("信託業法規定，信託業須經主管機關許可，並以股份有限公司組織設立，最低實收資本額依主管機關規定。", None),
                    ("受託人管理信託財產，應依善良管理人注意義務為之，並負忠實義務，不得為自己或第三人利益處理信託事務。", None),
                    ("信託財產之獨立性：信託財產不屬委託人、受益人或受託人之固有財產，受到法律特別保護，不得強制執行。", None),
                    ("特定金錢信託（指定用途信託）：委託人指定投資標的，受託人依指示操作，投資風險由委託人自行承擔。", None),
                ],
                10: [
                    ("電子支付機構管理條例規範非銀行業者辦理電子支付業務，包括代理收付款項、儲值及辦理國內外小額匯兌。", None),
                    ("開放銀行（Open Banking）政策：金融機構透過API開放金融資料，促進金融創新服務，共分三階段推動實施。", None),
                    ("監理沙盒制度（FinTech Sandbox）：創新金融業者可在受控環境下測試新服務，申請期間暫時豁免部分法規要求。", None),
                    ("虛擬資產（加密貨幣）：金管會將具投資性質之虛擬資產納入管理，業者須向金管會完成VASP登記。", None),
                    ("數位身分驗證（eKYC）：金融機構可透過視訊或電子方式驗證客戶身分，降低開戶門檻，提升普惠金融服務覆蓋率。", None),
                ],
                11: [
                    ("巴塞爾協議（Basel III）要求銀行持有足夠資本以因應三大風險：信用風險、市場風險及作業風險，最低普通股權益比率為4.5%。", None),
                    ("資本適足率（CAR）= 合格自有資本 / 風險性資產總額，銀行最低資本適足率為8%，低於標準須限期補足或限制業務。", None),
                    ("壓力測試：金融機構應定期評估極端情境下之資本充足性，主管機關亦會對系統性重要銀行（SIB）執行監理壓力測試。", None),
                    ("流動性覆蓋比率（LCR）：要求銀行持有足夠高品質流動資產，以應付30天壓力情境下之淨現金流出，最低標準100%。", None),
                    ("作業風險管理：銀行應建立完善管理框架，包括風險識別、評估、監控及緩解措施，防範內部詐欺、系統故障、人員疏失等風險。", None),
                ],
            }

            for idx, module_id in enumerate(module_ids):
                for seq, (text, img) in enumerate(flashcard_data.get(idx, []), start=1):
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
                    ("mcq", "保險合約的基本當事人不包括下列哪一方？", '["要保人","被保險人","受益人","仲裁人"]', "仲裁人"),
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
                     '["增加金融業者利潤","保護金融消費者權益","降低金融業監管","促進外資進入"]', "保護金融消費者權益"),
                ],
                2: [
                    ("mcq", "KYC代表什麼？", '["Know Your Customer","Keep Your Cash","Know Your Company","Keep Your Contract"]', "Know Your Customer"),
                    ("tf", "金融機構發現可疑交易後，可以告知客戶已申報。", '["True","False"]', "False"),
                    ("mcq", "單筆現金交易達多少金額以上須申報CTR？",
                     '["新臺幣10萬元","新臺幣30萬元","新臺幣50萬元","新臺幣100萬元"]', "新臺幣50萬元"),
                    ("tf", "洗錢防制內部控制制度需包含員工訓練計畫。", '["True","False"]', "True"),
                    ("mcq", "STR是指什麼申報？", '["大額現金交易申報","可疑交易申報","定期交易申報","跨境匯款申報"]', "可疑交易申報"),
                ],
                3: [
                    ("mcq", "證券交易法第157條之1所規範的內線交易，是指何種行為？",
                     '["公開發行公司股票上市","持有內部消息在公開前買賣股票","證券商代客操作","公司辦理現金增資"]',
                     "持有內部消息在公開前買賣股票"),
                    ("tf", "證券商不需要主管機關許可即可執行業務。", '["True","False"]', "False"),
                    ("mcq", "下列何者屬於市場操縱行為？",
                     '["依基本面長期持有","連續買賣拉抬股價","申購新股","定期定額投資"]', "連續買賣拉抬股價"),
                    ("tf", "公開說明書應揭露公司財務、業務等重要資訊供投資人判斷。", '["True","False"]', "True"),
                    ("mcq", "證券商依業務性質可分為哪三類？",
                     '["承銷商、自營商、經紀商","商業銀行、投資銀行、外商銀行","股票、債券、衍生商品","上市、上櫃、興櫃"]',
                     "承銷商、自營商、經紀商"),
                ],
                4: [
                    ("mcq", "存款保險對每一存款人在同一金融機構的最高保障金額為多少？",
                     '["100萬元","200萬元","300萬元","500萬元"]', "300萬元"),
                    ("tf", "銀行可對同一關係企業無限額授信。", '["True","False"]', "False"),
                    ("mcq", "下列何者不是銀行法所定義的銀行類型？",
                     '["商業銀行","專業銀行","信託投資公司","保險公司"]', "保險公司"),
                    ("tf", "金融控股公司可跨業經營銀行、保險、證券業務。", '["True","False"]', "True"),
                    ("mcq", "銀行法的立法目的主要為何？",
                     '["促進銀行盈利","健全銀行業務、保障存款人權益","擴大銀行規模","降低存款利率"]',
                     "健全銀行業務、保障存款人權益"),
                ],
                5: [
                    ("mcq", "下列何者屬於個資法所稱的特種個人資料？",
                     '["姓名","電話號碼","醫療及健康檢查資料","公司地址"]', "醫療及健康檢查資料"),
                    ("tf", "當事人有權要求資料控制者刪除其個人資料。", '["True","False"]', "True"),
                    ("mcq", "個資外洩時，機關或企業應採取什麼措施？",
                     '["隱匿不報","通知受影響當事人並採補救措施","等待主管機關調查","立即關閉系統"]',
                     "通知受影響當事人並採補救措施"),
                    ("tf", "個資法只適用於公務機關，不適用於私人企業。", '["True","False"]', "False"),
                    ("mcq", "違反個資法意圖營利者，可能面臨何種責任？",
                     '["僅行政罰鍰","刑事責任","僅警告","停業處分"]', "刑事責任"),
                ],
                6: [
                    ("mcq", "期貨交易中，帳戶淨值低於維持保證金時，交易人將收到什麼通知？",
                     '["利潤通知","Margin Call（追繳通知）","停損通知","強制平倉確認"]', "Margin Call（追繳通知）"),
                    ("tf", "選擇權賦予買方買賣標的物的義務。", '["True","False"]', "False"),
                    ("mcq", "Call Option（買權）賦予持有人什麼權利？",
                     '["以約定價格賣出標的物","以約定價格買入標的物","強制對方出售標的物","無限期持有標的物"]',
                     "以約定價格買入標的物"),
                    ("tf", "期貨商執行業務前須向主管機關申請許可。", '["True","False"]', "True"),
                    ("mcq", "期貨交易所的主要功能不包括下列哪一項？",
                     '["制定交易規則","執行結算及交割","提供個人投資建議","確保交易履行"]', "提供個人投資建議"),
                ],
                7: [
                    ("mcq", "投信公司募集共同基金後，基金資產應由誰保管？",
                     '["投信公司自行保管","基金保管機構（通常為銀行）","主管機關","投資人自行保管"]',
                     "基金保管機構（通常為銀行）"),
                    ("tf", "投信投顧業者可以利用客戶資產為自己謀利。", '["True","False"]', "False"),
                    ("mcq", "全權委託投資業務（代客操作）是由誰決定有價證券的買賣？",
                     '["客戶自行決定","投顧公司代為決定","主管機關指定","基金保管機構"]', "投顧公司代為決定"),
                    ("tf", "基金淨值（NAV）每日計算，投資人依NAV申購或贖回。", '["True","False"]', "True"),
                    ("mcq", "投信投顧業者違反公平對待客戶義務的後果為何？",
                     '["口頭警告","撤照並追究刑責","降低評級","暫停業務一週"]', "撤照並追究刑責"),
                ],
                8: [
                    ("mcq", "內部控制五大要素不包括下列哪一項？",
                     '["控制環境","風險評估","市場分析","監督作業"]', "市場分析"),
                    ("tf", "審計委員會應由全體獨立董事組成。", '["True","False"]', "True"),
                    ("mcq", "內部稽核部門應向誰報告以確保獨立性？",
                     '["CEO","財務長","董事會或審計委員會","主管機關"]', "董事會或審計委員會"),
                    ("tf", "員工依吹哨者保護制度檢舉後，雇主可合法予以解雇。", '["True","False"]', "False"),
                    ("mcq", "公司治理的核心目標為何？",
                     '["最大化短期利潤","達成公司永續經營","降低員工薪資","擴大市場佔有率"]', "達成公司永續經營"),
                ],
                9: [
                    ("mcq", "信託關係中，實際管理信託財產的一方稱為？",
                     '["委託人","受益人","受託人","監察人"]', "受託人"),
                    ("tf", "信託財產可以被受益人的債權人強制執行。", '["True","False"]', "False"),
                    ("mcq", "受託人管理信託財產應遵守何種注意義務標準？",
                     '["最低注意義務","善良管理人注意義務","一般人注意義務","商業判斷原則"]', "善良管理人注意義務"),
                    ("tf", "信託業須經主管機關許可才能設立。", '["True","False"]', "True"),
                    ("mcq", "特定金錢信託中，投資風險由誰承擔？",
                     '["受託人","委託人","主管機關","銀行"]', "委託人"),
                ],
                10: [
                    ("mcq", "監理沙盒制度的主要目的為何？",
                     '["阻止金融創新","在受控環境下測試新服務","處罰違規業者","提高市場准入門檻"]',
                     "在受控環境下測試新服務"),
                    ("tf", "電子支付機構可以辦理存款業務。", '["True","False"]', "False"),
                    ("mcq", "開放銀行主要透過何種技術開放金融資料？",
                     '["傳真","API","電話","郵件"]', "API"),
                    ("tf", "虛擬資產業者須向金管會申請VASP登記。", '["True","False"]', "True"),
                    ("mcq", "eKYC是指什麼？",
                     '["電子稅務申報","數位身分驗證","電子支付結算","網路銀行登入"]', "數位身分驗證"),
                ],
                11: [
                    ("mcq", "Basel III要求銀行最低普通股權益比率為多少？",
                     '["2%","4.5%","8%","10%"]', "4.5%"),
                    ("tf", "銀行資本適足率最低標準為8%。", '["True","False"]', "True"),
                    ("mcq", "流動性覆蓋比率（LCR）的最低標準為？",
                     '["50%","75%","100%","120%"]', "100%"),
                    ("tf", "壓力測試用於評估極端情境下的資本充足性。", '["True","False"]', "True"),
                    ("mcq", "下列何者不屬於作業風險的範疇？",
                     '["內部詐欺","系統故障","利率上升","人員疏失"]', "利率上升"),
                ],
            }

            for idx, module_id in enumerate(module_ids):
                for qtype, prompt, options, answer in question_data.get(idx, []):
                    cur.execute(
                        "INSERT INTO questions (module_id, type, prompt, options_json, correct_answer) VALUES (%s,%s,%s,%s,%s)",
                        (module_id, qtype, prompt, options, answer),
                    )

        conn.commit()
        print("Demo data seeded successfully")
    finally:
        conn.close()
