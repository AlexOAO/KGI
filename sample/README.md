# 法遵合規微學習平台（Compliance Micro-Learning Platform）

金融法遵合規知識庫 × Sprint 式微學習 × SM-2 間隔複習的整合 POC 平台。
使用 Python + Gradio 建構，資料來源涵蓋金管會裁罰案例、監理函令、全國法規資料庫與主管機關法規資料集。

---

## 專案目的

台灣金融業（保險、銀行、證券）法遵人員每年須消化大量監理函令、裁罰案例與法條更新。本平台針對以下痛點設計：

| 痛點 | 解法 |
|------|------|
| 法規量龐大、難以消化 | Sprint 式微學習：7 分鐘一個主題，卡片式呈現核心要點 |
| 記了又忘 | SM-2 演算法自動排程複習，依掌握程度動態調整間隔 |
| 想查法條或裁罰案例要開多個網站 | 合規知識庫：全文搜尋裁罰、函令、全國法規、主管法規 |
| 培訓成效難量化 | 學習儀表板：連續天數、正確率趨勢、模組掌握度一目了然 |

> **POC 定位：** Gradio 介面僅供驗證核心商業邏輯。
> 所有 `app/models/`、`app/services/` 程式碼均與 Gradio 零耦合，
> 後續可直接包裝為 FastAPI + HTML/JS 前端，無需重寫業務邏輯。

---

## 功能總覽

### 微學習流程

```
登入 → 選擇模組 → Pre-Sprint 預覽
     → Sprint Reader（7 分鐘計時 + 卡片翻頁 + 分頁偵測）
     → 即時測驗（最多 5 題選擇題）
     → 學習儀表板（成績 / 掌握度 / 複習排程）
```

- **Sprint Reader**：7 分鐘倒數計時，離開頁面自動暫停並記錄切換次數
- **即時測驗**：閱讀結束後立即進行選擇題，自動批改並顯示錯題解析
- **SM-2 間隔複習**：依答題正確率計算下次複習間隔（1 天 → 3 天 → n × ease factor）
- **學習儀表板**：連續學習天數、各模組掌握度長條圖、複習排程表、近期答題記錄

### 合規知識庫查詢

登入後點擊「**合規查詢**」進入全文搜尋介面，支援以下 4 個資料集：

| 分頁 | 資料來源 | 筆數 |
|------|----------|------|
| 裁罰案例 | 金管會歷年裁罰紀錄 | ~1,116 筆 |
| 監理函令 | 金管會 / 銀行公會 / 證券期貨相關函令 | ~514 筆 |
| 全國法規 | 全國法規資料庫（條文級，含保險法、銀行法等） | ~46,862 條 |
| 主管法規 | 保險局 / 銀行局 / 證期局主管法規資料集 | ~6,142 筆 |

- 搜尋採用 SQLite **FTS5 + trigram tokenizer**，支援任意中文關鍵字全文比對
- 每頁顯示 10 筆，支援翻頁
- **建議輸入 3 個以上字元**以觸發 trigram 索引（例：`保險法`、`洗錢防制`、`罰鍰`）

### 自動生成合規學習模組

首次啟動時，平台會從合規資料庫自動生成 3 個學習模組：

| 模組名稱 | 內容來源 | 卡片數 | 題數 |
|---------|----------|--------|------|
| 近期重大裁罰案例 | 金管會最新 8 件重大裁罰 | 8 | 3 |
| 保險法核心條文 | 保險法第 1、2、3、5、13、36、54、105、138、149 條 | 10 | 4 |
| FSC 近期法規動態 | 金管會最新 7 件函令 | 7 | 3 |

這 3 個模組可直接進入 Sprint 學習流程，與手動建立的模組完全相同。

---

## 安裝與啟動

### 前置需求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 套件管理工具
- 合規資料集（位於 `../data/`，見下方說明）

### 資料集準備

將以下 4 個檔案放至 `KGI/data/` 目錄（與 `sample/` 同層）：

```
KGI/
├── data/
│   ├── 裁罰.json                      # 金管會裁罰案例（JSONL 格式）
│   ├── 法規.json                      # 監理函令資料集（JSONL 格式）
│   ├── 全國法規資料庫 (4).jsonl        # 全國法規條文（JSONL 格式）
│   └── 處理後_主管法規資料集.jsonl     # 主管機關法規（JSONL 格式）
└── sample/                            # 本專案目錄
```

### 啟動指令

```bash
cd KGI/sample
uv run python main.py
```

**首次啟動**會自動執行：
1. 建立 SQLite Schema（含 FTS5 全文索引表）
2. 匯入 4 個資料集（約需 **15–30 秒**，全國法規 46K 條）
3. 生成 3 個合規學習模組
4. 啟動 Gradio 伺服器

**後續啟動**：資料已匯入則跳過，直接啟動（< 3 秒）。

啟動後開啟瀏覽器前往：[http://localhost:7860](http://localhost:7860)

---

## 預設帳號

| 用戶名 | 密碼 | 角色 |
|--------|------|------|
| learner1 | learn1234 | 學習者 |
| learner2 | learn5678 | 學習者 |
| admin | admin1234 | 管理員 |

---

## 資料夾結構

```
sample/
├── main.py                        # Gradio 應用程式入口、所有 UI 與事件接線
├── pyproject.toml                 # 專案依賴（gradio, bcrypt, pytest）
├── microlearning.db               # SQLite 資料庫（自動建立）
│
├── app/
│   ├── core/
│   │   ├── config.py              # 設定常數（DB_PATH, DATA_DIR, TIMER_SECONDS 等）
│   │   ├── database.py            # get_connection(), init_db(), init_compliance_db()
│   │   └── auth.py                # bcrypt 密碼雜湊、session token 管理
│   │
│   ├── data/
│   │   ├── schema.sql             # 學習平台主 Schema（8 張資料表）
│   │   ├── compliance_schema.sql  # 合規 FTS5 Schema（4 個 content-table 組）
│   │   ├── seed.py                # 種子資料（帳號 + 3 個基礎學習模組）
│   │   └── compliance_loader.py   # 合規資料批次匯入 + 3 個合規模組生成
│   │
│   ├── models/
│   │   ├── user.py                # 用戶驗證、建立
│   │   ├── module.py              # 模組、閃卡 CRUD
│   │   ├── quiz.py                # 題目 CRUD、作答記錄
│   │   ├── session.py             # Sprint session 管理
│   │   ├── schedule.py            # 複習排程 CRUD（SM-2 資料層）
│   │   └── compliance.py          # 合規 FTS5 搜尋（4 個資料集）
│   │
│   ├── services/
│   │   ├── sprint_service.py      # 啟動 / 結束 Sprint session
│   │   ├── quiz_service.py        # 批改測驗、計算 SM-2、寫入排程
│   │   ├── dashboard_service.py   # 儀表板資料彙整（連續天數、掌握度等）
│   │   ├── sm2.py                 # SM-2 間隔複習演算法
│   │   └── compliance_service.py  # 合規搜尋調度 + Markdown 結果格式化
│   │
│   └── ui/                        # 未使用的 UI 元件（保留供參考）
│
└── tests/                         # pytest 測試套件（24 tests）
    ├── test_models.py
    ├── test_quiz_service.py
    ├── test_sm2.py
    └── test_integration.py
```

---

## 資料庫 Schema 概覽

### 學習平台（`schema.sql`）

| 資料表 | 用途 |
|--------|------|
| `users` | 帳號、密碼雜湊、角色 |
| `modules` | 學習模組（標題、主題標籤、難度） |
| `flashcard_pages` | 模組閃卡（序號、Markdown 內容） |
| `questions` | 選擇題（題目、選項 JSON、正解） |
| `sprint_sessions` | Sprint 紀錄（開始/結束時間、切換次數、完成狀態） |
| `attempts` | 測驗成績（得分、正確率、完成時間） |
| `question_responses` | 每題作答明細（是否正確、答題時間） |
| `review_schedule` | SM-2 複習排程（下次複習日、間隔天數、ease factor） |

### 合規知識庫（`compliance_schema.sql`）

每個資料集由一組 **base table + FTS5 virtual table + INSERT trigger** 組成：

| Base Table | FTS5 Table | 說明 |
|-----------|-----------|------|
| `compliance_penalties` | `compliance_penalties_fts` | 裁罰案例 |
| `compliance_regulations` | `compliance_regulations_fts` | 監理函令 |
| `compliance_national_laws` | `compliance_national_laws_fts` | 全國法規條文 |
| `compliance_fsc_regs` | `compliance_fsc_regs_fts` | 主管法規 |
| `compliance_load_status` | — | 資料匯入狀態（lazy-load 守衛） |

FTS5 使用 `tokenize='trigram'`，支援任意子字串比對，不需斷詞。

---

## 執行測試

```bash
cd KGI/sample
uv run pytest tests/ -v
```

預期：**24 tests 全部通過**（覆蓋 SM-2 演算法、model CRUD、測驗批改、完整學習流程）。

---

## SM-2 間隔複習演算法

答題正確率轉換為品質分數（Q），再依 SM-2 公式計算下次複習間隔：

| 正確率 | 品質分數 Q |
|--------|-----------|
| 90–100% | 5（完全記住）|
| 75–89% | 4 |
| 60–74% | 3 |
| 40–59% | 2 |
| 0–39% | 1（幾乎忘記）|

**間隔計算規則：**
- Q < 3：重置，下次間隔 1 天
- 第 1 次通過：間隔 1 天
- 第 2 次通過：間隔 3 天
- 之後：間隔 × ease factor（初始 2.5，最低 1.3）

---

## 未來架構分離規劃

Gradio 僅為 POC 驗證介面，正式產品將分離為：

```
現在（POC）                         分離後
─────────────────────────────────────────────────────
sample/app/models/    ← 零 Gradio  → backend/app/models/
sample/app/services/  ← 零 Gradio  → backend/app/services/
sample/app/data/      ← 零 Gradio  → backend/app/data/
sample/app/core/      ← 零 Gradio  → backend/app/core/
sample/main.py        ← Gradio POC → 廢棄

                                      backend/main_api.py  （FastAPI）
                                      frontend/index.html  （HTML/CSS/JS）
```

分離步驟：
1. `backend/`：複製 `app/` 目錄，新增 `main_api.py`，將 service 函數包裝為 REST endpoints（`/api/search`, `/api/modules`, `/api/auth` 等）
2. `frontend/`：HTML + CSS + JS，呼叫 FastAPI endpoints
3. `compliance_loader.py` → FastAPI `lifespan` hook（應用啟動時執行）

所有 service / model 函數的回傳值均為 JSON serializable（`list[dict]`，dict 值只含 Python 基礎型別），無需修改即可直接用於 API 回應。

---

## 注意事項

- **資料庫**：`microlearning.db` 於首次執行時自動建立於 `sample/` 目錄
- **計時器**：預設 7 分鐘（`TIMER_SECONDS = 420`），可於 `app/core/config.py` 調整
- **分頁切換偵測**：依賴瀏覽器 `visibilitychange` 事件，隱私模式或部分瀏覽器可能行為不一致
- **搜尋最小長度**：FTS5 trigram 需至少 **3 個字元**才能有效搜尋；1–2 字元查詢不會報錯但結果為空
- **合規資料更新**：替換 `KGI/data/` 下的 JSONL 檔案後，刪除 `microlearning.db` 重新啟動即可重新匯入
