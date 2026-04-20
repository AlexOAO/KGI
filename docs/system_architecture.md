# LexPulse — 系統架構說明

> 本文件面向 POC 目標客戶，以「服務如何啟動、流程從哪裡開始」為主軸，完整說明平台的技術架構與資料流。

---

## 一、全局架構概覽

```
瀏覽器 (Single-Page App)
        │  HTTP / Cookie
        ▼
   FastAPI (Python)          ← main.py 啟動點
        │
        ├── app/api/          ← 28 個 REST 端點
        ├── app/services/     ← 業務邏輯層
        ├── app/models/       ← 資料存取層
        └── app/data/         ← 初始化 & 遷移
                │
                ▼
           MySQL 8.0          ← Docker Container
           13 張資料表
```

**技術棧一覽**

| 層次 | 技術 |
|------|------|
| 後端框架 | Python 3.12 + FastAPI + Uvicorn |
| 前端 | 單頁應用（Jinja2 + Vanilla JS + Tailwind CSS） |
| 資料庫 | MySQL 8.0（Docker 容器） |
| 資料庫驅動 | PyMySQL（原生 SQL，無 ORM） |
| 身分驗證 | bcrypt 密碼雜湊 + HMAC-SHA256 JWT（httponly cookie） |

---

## 二、服務啟動流程

系統的入口點是 `main.py`。每次服務啟動時，會依序執行五個初始化步驟，確保資料庫結構完整且示範資料就位。

```
uvicorn main:app --port 7860
        │
        ▼
  @asynccontextmanager lifespan(app)
        │
        ├─ Step 1: create_tables()
        │          ├── 讀取 app/data/schema.sql
        │          └── 建立（或確認）13 張資料表
        │
        ├─ Step 2: run_migrations()
        │          ├── 檢查 information_schema.COLUMNS
        │          ├── 幂等地 ALTER TABLE 補齊新欄位
        │          └── seed_extra_modules() → 若模組數 < 18，植入第 13-18 個模組
        │
        ├─ Step 3: load_compliance_data()   ← 僅首次啟動執行
        │          ├── 裁罰.json        → comp_penalties
        │          ├── 法規.json        → comp_regulations
        │          ├── 全國法規資料庫.jsonl → comp_national_laws
        │          └── 主管法規資料集.jsonl → comp_fsc_directives
        │
        ├─ Step 4: seed_demo_data()         ← 僅首次啟動執行
        │          ├── 建立示範帳號（learner1, admin1）
        │          ├── 植入 12 個學習模組
        │          ├── 每模組 5 張閃卡
        │          └── 每模組 5 題測驗
        │
        └─ Step 5: seed_catalog_items()     ← 僅首次啟動執行
                   └── 植入 9 項獎勵商品
                       （禮券 3 + 紀念品 3 + 考績時數 3）
```

> **幂等設計**：Step 3-5 均以 `is_table_empty()` 先判斷，避免重複啟動時重複寫入。

---

## 三、資料庫結構（13 張資料表）

### 3.1 核心學習資料表

| 資料表 | 用途 |
|--------|------|
| `users` | 帳號、XP、點數、學習時數、連續天數凍結券 |
| `modules` | 18 個學習模組（標題、領域標籤、難度、時長） |
| `flashcard_pages` | 90 張閃卡內容（每模組 5 張，有序） |
| `questions` | 90 道測驗題（MCQ + True/False） |
| `sprint_sessions` | 每次閱讀行為記錄（開始/結束時間、切換分頁次數） |
| `quiz_sessions` | 測驗結果（分數、XP、首次作答模式） |
| `question_responses` | 每題回答明細（含回答時間 ms） |
| `learning_journey_map` | 衝刺 session ↔ 測驗 session 的 1:1 對照橋接表 |
| `review_schedule` | SM-2 複習排程（每人每概念標籤一行） |

### 3.2 獎勵系統資料表

| 資料表 | 用途 |
|--------|------|
| `level_up_rewards` | 升級獎勵領取記錄（UNIQUE 防止重複領取） |
| `reward_catalog` | 商品目錄（禮券、紀念品、考績時數） |
| `reward_transactions` | 所有點數 / 時數異動的完整稽核日誌 |

### 3.3 法遵知識庫資料表

| 資料表 | 用途 |
|--------|------|
| `comp_penalties` | 裁罰案例（FULLTEXT 全文索引） |
| `comp_regulations` | 主管機關法規 |
| `comp_national_laws` | 全國法規資料庫條文 |
| `comp_fsc_directives` | 金管會函令資料集 |

---

## 四、主要使用者流程

### 4.1 使用者登入

```
前端: POST /api/login {username, password}
      │
      ▼
app/api/auth.py → authenticate()
      ├── 查詢 users 表
      ├── bcrypt 驗證密碼
      ├── 產生 HMAC-SHA256 JWT
      └── 設定 httponly cookie (max_age 24h)
      │
      ▼
回傳: {user_id, username, role}
前端: 載入模組列表頁
```

### 4.2 七分鐘衝刺閱讀

```
1. 使用者點選模組卡片
   │
   ▼
2. 前端: GET /api/modules/{id}
   回傳: {module 詮釋資料 + 5 張閃卡}
   ↓ 顯示「衝刺前啟動畫面」
   （原始文件標題、領域標籤、7 分鐘 / 5 卡 / 隨即測驗 提示）

3. 使用者點擊「開始衝刺」
   │
   ▼
4. 前端: POST /api/sprint/start {module_id}
   後端:
   ├── 新增 sprint_sessions 資料列（status: 'abandoned'）
   └── 新增 learning_journey_map 資料列（1:1 預佔）
   回傳: sprint_id

5. 閱讀器畫面啟動
   ├── performance.now() 高精度計時（±1ms）
   ├── Page Visibility API 監聽：切換分頁 → 計時暫停
   └── 每次分頁切換: POST /api/sprint/tab-switch（fire-and-forget）

6. 計時器歸零 或 使用者讀完最後一張卡
   │
   ▼
7. finishSprint() → POST /api/sprint/end
   後端 (app/models/sprint.py):
   ├── 更新 sprint_sessions（end_ts, tab_switch_count, completion_status）
   ├── 計算 elapsed 秒數 → cumulative_learn_seconds += elapsed
   ├── learn_hrs = round(elapsed / 3600, 2)
   ├── users.learning_hours += learn_hrs        ← 自動計入學習時數
   └── 寫入 reward_transactions (earn_hours_study)

8. 900ms 交接動畫「正在生成你的測驗⋯⋯」
   │
   ▼
9. GET /api/quiz/{module_id} → 隨機抽取 5 題 → 進入測驗畫面
```

### 4.3 測驗批改與 SM-2 調度

```
使用者提交答案
│
▼
POST /api/quiz/submit
{module_id, answers{}, first_attempt_map{}, session_type}
        │
        ▼
app/services/quiz_service.py → grade_quiz()
        │
        ├─ 比對答案 → 計算 score (0-100)
        │
        ├─ compute_xp()
        │   └── 依正確題數查 XP Tier 表
        │       [20, 30, 45, 65, 90, 125] (學習場次)
        │       [10, 15, 22, 32, 45,  60] (複習場次)
        │
        ├─ update_user_xp() → 檢查是否升級
        │   └── 若升級: 傳回 level_reward_options
        │             (使用者選擇 KGI 點數 或 學習時數)
        │
        ├─ 儲存 quiz_sessions + question_responses
        │
        └─ _update_review_schedule()  ← SM-2 演算法
            ├── score → quality (0-5)
            ├── 計算 new_interval, new_ease_factor
            ├── next_review_at = today + interval_days
            └── UPSERT review_schedule (user_id, concept_tag)
        │
        ▼
回傳: {score, correct, total, xp_earned, leveled_up,
       level_name, progress_pct, level_reward_options}
```

### 4.4 XP 等級系統

```
6 個等級階梯:

  第 1 階  新手法遵員      0 – 99 XP
  第 2 階  合規見習生    100 – 299 XP
  第 3 階  法遵分析師    300 – 699 XP
  第 4 階  合規達人      700 – 1,499 XP
  第 5 階  法遵大師    1,500 – 2,999 XP
  第 6 階  法遵守護者   3,000+ XP

升級觸發:
  update_user_xp() 比對 old_level vs new_level
  若 new_level_index > old_level_index:
    → 前端顯示升級動畫（彩紙特效 + 吉祥物對話泡泡）
    → 彈出獎勵選擇面板（KGI 點數 / 學習時數 二擇一）
    → POST /api/rewards/claim-level（UNIQUE 鍵防止重複領取）
```

### 4.5 SM-2 複習排程

```
每次測驗後:
  topic_tag → (user_id, concept_tag) 的複習記錄
  quality = score_to_quality(first_attempt_score)

  SM-2 規則:
  ┌─────────────────────────────────────────────────┐
  │ quality < 3  → interval=1, repetitions 重設為 0 │
  │ reps=0       → interval=1                       │
  │ reps=1       → interval=3                       │
  │ reps>=2      → interval = round(interval × EF)  │
  │ EF 更新: max(1.3, EF + 0.1 - (5-q)×(0.08+(5-q)×0.02)) │
  └─────────────────────────────────────────────────┘

  next_review_at = today + interval_days
  → Dashboard 的「待複習」清單即來源於此
```

### 4.6 獎勵中心流程

```
錢包三種貨幣:
  kgi_points     → KGI 點數（升級獎勵、可兌換商品）
  learning_hours → 學習時數（衝刺自動計入、可換點數）
  perf_hours     → 考績時數（從商品目錄兌換，計入年度考績）

獎勵來源:
  ┌── 完成衝刺       → learning_hours += round(elapsed/3600, 2)
  ├── 升級選擇        → kgi_points 或 learning_hours（二擇一）
  └── 管理員補發      → POST /api/admin/grant

貨幣兌換:
  學習時數 → KGI 點數: 1 小時 = 50 點
  KGI 點數 → 學習時數: 100 點 = 1 小時

商品兌換 (POST /api/rewards/redeem):
  ├── 扣除 kgi_points
  ├── 減少 stock（若有限量）
  ├── 寫入 reward_transactions（完整稽核日誌）
  └── 若類別 = performance_hours → perf_hours += 對應時數
```

### 4.7 法遵知識庫查詢

```
使用者在「法遵查詢」分頁輸入關鍵字

GET /api/compliance/search
  ?q=洗錢&type=penalties&page=1&category=...
          │
          ▼
app/api/compliance.py → 動態查詢對應資料表
  ├── comp_penalties      (FULLTEXT 全文搜尋: title, content)
  ├── comp_regulations    (FULLTEXT 全文搜尋: title, content)
  ├── comp_national_laws  (FULLTEXT 全文搜尋: law_name, article_content)
  └── comp_fsc_directives (FULLTEXT 全文搜尋: subject, content)

結果: 分頁列表 + 點擊單筆顯示完整內文
```

---

## 五、API 端點總覽

### 身分驗證
```
POST  /api/login            登入（取得 JWT cookie）
POST  /api/logout           登出
GET   /api/me               當前使用者資訊
GET   /api/me/level         當前等級與進度
```

### 學習內容
```
GET   /api/modules          模組列表（附最高分、複習狀態）
GET   /api/modules/{id}     模組詳情 + 閃卡
GET   /api/quiz/{module_id} 隨機抽取 5 題
POST  /api/quiz/submit      提交答案（批改 + XP + SM-2 更新）
```

### 衝刺管理
```
POST  /api/sprint/start     開始衝刺（建立 session）
POST  /api/sprint/end       結束衝刺（計入學習時數）
POST  /api/sprint/tab-switch 記錄切換分頁事件
```

### 儀表板
```
GET   /api/dashboard        連續天數、掌握度、待複習清單
```

### 法遵知識庫
```
GET   /api/compliance/search  全文搜尋（分頁）
GET   /api/compliance/detail  單筆詳情
GET   /api/compliance/filters 篩選器選項
```

### 獎勵系統
```
GET   /api/rewards/wallet    錢包餘額（點數 / 學習時數 / 考績時數）
GET   /api/rewards/history   交易記錄
POST  /api/rewards/claim-level  升級獎勵領取
GET   /api/rewards/catalog   商品目錄
POST  /api/rewards/redeem    商品兌換
POST  /api/rewards/convert   貨幣兌換（時數 ↔ 點數）
```

### 管理員專用
```
GET   /api/admin/catalog          商品管理（含下架品）
POST  /api/admin/catalog          新增商品
PUT   /api/admin/catalog/{id}     更新商品（名稱 / 點數 / 庫存）
POST  /api/admin/grant            補發點數 / 時數給指定使用者
```

---

## 六、前端單頁應用架構

整個前端由單一 `templates/index.html` 構成，共 9 個畫面透過 JavaScript 控制顯示 / 隱藏。

```
screen-login       登入
screen-modules     模組列表（含等級英雄區塊 + XP 進度條）
screen-pre-sprint  衝刺啟動前確認（詮釋資料 + 警示文字）
screen-reader      閃卡閱讀器（計時器 + 翻頁）
screen-handoff     交接動畫（「正在生成你的測驗⋯⋯」）
screen-quiz        測驗介面（選擇 + 提交 + 批改揭示）
screen-dashboard   個人儀表板（連續天數 + 掌握度 + 待複習）
screen-compliance  法遵知識庫（4 分類 + 全文搜尋 + 篩選）
screen-rewards     獎勵中心（錢包 + 商品目錄 + 兌換 + 交易記錄）
```

---

## 七、安全設計

| 面向 | 做法 |
|------|------|
| 密碼儲存 | bcrypt（預設 salt 輪數） |
| 身分驗證 token | HMAC-SHA256 JWT，存於 httponly cookie（防 XSS） |
| SQL 注入防護 | 全面參數化查詢（`%s` 佔位符，PyMySQL 自動逸出） |
| 錢包寫入 | `FOR UPDATE` 悲觀鎖，防止並發超領 |
| 升級獎勵幂等 | `UNIQUE(user_id, level_reached)` + `INSERT IGNORE` |
| 管理員端點 | 額外 `require_admin` 依賴注入驗證 role |

---

## 八、部署流程

```bash
# 1. 啟動 MySQL 容器
docker compose up -d

# 2. 設定環境變數
cp .env.example .env
# 修改 DB_PASSWORD、JWT_SECRET

# 3. 啟動服務
uv run uvicorn main:app --host 0.0.0.0 --port 7860

# 預設示範帳號
learner1 / pass123   （學員角色）
admin1   / admin123  （管理員角色）
```

**生產環境建議**：Uvicorn + Gunicorn 多進程 → Nginx 反向代理（SSL + 靜態資源） → RDS 受管 MySQL → 環境變數改用 Vault 或雲端 Secret Manager。

---

*LexPulse POC — 版本 2026-04*
