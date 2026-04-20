# LexPulse — 法遵微學習平台 POC

金融法遵合規微學習平台的 Proof of Concept，整合間隔複習（SM-2）、7 分鐘 Sprint Reader、XP 等級系統，以及完整的法遵資料庫搜尋功能。

---

## Project 3 實作對照（Sprint Reader & Contextual Transition）

本節說明 POC 如何逐條實現 `project3.md` 的 User Story 與技術規格，方便 Demo 時解說。

### Screen 1 — Pre-Sprint 啟動畫面

> *「在計時器開始前，使用者會先看到一張資訊卡，從系統拉取相關知識的詮釋資料」*

| 需求 | 實作位置 | 說明 |
|------|----------|------|
| 模組標題 | `templates/index.html` `#pre-title` | `GET /modules/{id}` 回傳後填入 |
| 領域標籤 | `#pre-tags` | `module.topic_tag` 拆分為 badge 列表 |
| 來源文件 | `#pre-source-doc` | `modules.source_document` 欄位（可選） |
| 警示說明（幾張卡、幾題測驗） | `#pre-warning` | 動態帶入閃卡數量與分鐘數 |
| CTA 按鈕「開始衝刺」 | `startSprint()` | 呼叫 `POST /sprint/start` 建立 SprintSession |

### Screen 2 — 閱讀介面

> *「行動優先、類 Instagram 限時動態風格的滑動介面」*

| 需求 | 實作位置 | 說明 |
|------|----------|------|
| Card N of M 進度 | `#reader-progress` | `renderCard()` 每次更新 |
| 領域標籤 badge | `#reader-topic` | 頂部狀態列常駐顯示 |
| 倒數計時器 | `#reader-timer` + `startTimer()` | 使用 `performance.now()` 確保 ±1ms 精度，避免 `setInterval` 漂移 |
| 禁止後退 | 閱讀器只有「下一張」按鈕 | `nextCard()` 只遞增，無法倒退 |
| Visibility API 暫停 | `setupVisibility()` + `handleVisibility()` | `visibilityState === 'hidden'` 時清除 interval，恢復時重新啟動 |
| 切換分頁即時寫後端 | `POST /sprint/tab-switch` | 每次切換 fire-and-forget，中途放棄也不遺失資料 |
| 「歡迎回來，計時器已恢復」| `#reader-resume` toast | 恢復可見時顯示 3 秒後隱藏 |

### Screen 3 — Handoff 交接畫面

> *「畫面會立即鎖定並播放簡潔的 CSS 動畫，隨後自動導向測驗介面」*

| 需求 | 實作位置 | 說明 |
|------|----------|------|
| 畫面鎖定 + 動畫 | `#screen-handoff` + `.handoff-spinner` | `finishSprint()` 觸發，CSS spinner |
| 「衝刺完成。正在生成你的測驗⋯⋯」 | `#screen-handoff` 文字 | 完全符合 spec 原文 |
| 自動導向測驗 | `finishSprint()` → `loadQuiz()` → `showScreen('quiz')` | 900ms 過場後切換，`sprint_id` 同步寫入 quiz session |

### 資料庫設計

> *「資料庫必須作為 P1 生成內容與 P3 遙測資料之間的橋樑」*

**FlashcardPages**

```sql
flashcard_pages (
  id              -- page_id (PK)
  module_id       -- FK → modules
  sequence_number -- 1, 2, 3...
  page_text       -- 文字內容（spec 的 page_content_json 拆欄）
  image_url       -- 可選圖片
)
```

**SprintSessions**

```sql
sprint_sessions (
  sprint_id         -- PK
  agent_id          -- FK → users
  module_id         -- FK → modules
  start_ts          -- start_timestamp
  end_ts            -- end_timestamp（可 NULL，abandoned 時保留）
  tab_switch_count  -- 每次切換分頁即時累加
  completion_status -- ENUM('finished_early', 'timed_out', 'abandoned')
)
```

**LearningJourney_Map（連結 Sprint → Quiz）**

```sql
learning_journey_map (
  journey_id      -- PK
  sprint_id       -- FK → sprint_sessions（UNIQUE，一對一）
  quiz_session_id -- FK → quiz_sessions（nullable，quiz 完成後寫入）
)
```

> 這張表是關鍵：未來可以 JOIN 三表做 ML 分析，例如「切換分頁次數多的使用者，測驗成績是否較低？」

---

## 技術架構

| 層級 | 技術選擇 |
|------|----------|
| 後端 | Python 3.12 + FastAPI + Uvicorn |
| 前端 | 單頁應用（Jinja2 + Vanilla JS + Tailwind CDN） |
| 資料庫 | MySQL 8.0（Docker Compose） |
| DB 驅動 | PyMySQL（raw SQL，無 ORM） |
| 認證 | bcrypt + HMAC-SHA256 JWT（httponly cookie） |
| 套件管理 | uv |

---

## 快速啟動

**前置需求**：Docker Desktop、Python 3.12、[uv](https://github.com/astral-sh/uv)

```bash
# 1. 啟動 MySQL 容器
docker compose up -d

# 2. 複製環境設定
cp .env.example .env

# 3. 安裝依賴並啟動
uv run uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

開啟瀏覽器前往 `http://localhost:7860`

**預設帳號**

| 帳號 | 密碼 | 角色 |
|------|------|------|
| learner1 | pass123 | 學習者 |
| admin1 | admin123 | 管理員 |

---

## 功能一覽

### 學習模組（18 個）

涵蓋保險法、洗錢防制、證券交易、個資法、ESG 合規等台灣金融法遵核心主題，每個模組包含：
- 5 張閃卡（Sprint Reader 7 分鐘倒數）
- 5 題測驗（MCQ / True-False）
- SM-2 間隔複習排程（依測驗成績自動調整下次複習日）

### XP 等級系統

| 等級 | XP 範圍 | 首答全對 Bonus |
|------|---------|---------------|
| 新手法遵員 | 0–99 | |
| 合規見習生 | 100–299 | 每題首答正確 +15 XP |
| 法遵分析師 | 300–699 | 全對額外 +25 XP |
| 合規達人 | 700–1499 | |
| 法遵大師 | 1500–2999 | |
| 法遵守護者 | 3000+ | |

### 儀表板

- 各主題掌握度（Chart.js）
- 待複習清單（SM-2 到期提醒）
- 連續學習天數（Streak + Freeze 機制）

### 法遵資料庫搜尋

| 資料集 | 說明 |
|--------|------|
| 裁罰案例 | 重大 / 非重大裁罰，含機構別 |
| 函令法規 | 金管會等函令 |
| 全國法規 | 全國法規資料庫條文 |
| 主管法規 | 保險局 / 銀行局 / 證期局主管法規 |

支援 MySQL FULLTEXT 關鍵字搜尋、多維度篩選、分頁顯示。

---

## 資料夾結構

```
sample/
├── docker-compose.yml
├── main.py                        # FastAPI 進入點（lifespan: migration + seed）
├── templates/index.html           # 單頁應用（SPA）
└── app/
    ├── core/
    │   ├── config.py              # 環境變數（DATA_DIR 指向 data/）
    │   └── database.py            # PyMySQL 連線
    ├── data/
    │   ├── schema.sql             # 13 張表定義
    │   ├── migrations.py          # ALTER TABLE 冪等遷移 + 補充模組 seed
    │   ├── loader.py              # 法遵 JSON/JSONL 載入
    │   └── datapdf.py             # 法令遵循處原始檔轉換腳本（uv run datapdf.py）
    ├── api/
    │   ├── auth.py                # 登入 / 登出 / JWT / GET /me/level
    │   ├── modules.py             # 模組列表（含 best_score）/ 閃卡
    │   ├── sprint.py              # POST /sprint/start|end|tab-switch
    │   ├── quiz.py                # 取題 / 提交（XP 計算）
    │   ├── dashboard.py           # 儀表板（streak / mastery / reviews）
    │   └── compliance.py          # 法遵搜尋
    └── services/
        ├── quiz_service.py        # grade_quiz（SM-2 + XP）
        ├── xp_service.py          # level_for / compute_xp / update_user_xp
        └── dashboard_service.py   # streak freeze 機制
```

---

## 資料庫 Schema（13 張表）

**學習相關**：`users`、`modules`、`flashcard_pages`、`questions`、`sprint_sessions`、`quiz_sessions`、`question_responses`、`learning_journey_map`、`review_schedule`

**法遵資料**：`comp_penalties`、`comp_regulations`、`comp_national_laws`、`comp_fsc_directives`

---

## 環境變數

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=kgi
DB_PASSWORD=kgi_pass
DB_NAME=kgi_learning
TIMER_SECONDS=420
SECRET_KEY=change-me-in-production
```

---

## 已知限制

- 閃卡與測驗題目為手動撰寫，未從原始資料集自動生成
- 無管理員後台（新增 / 編輯模組需直接操作 DB）
- Push notification 尚未實作（目前以 Dashboard 到期徽章提示取代）
- 前端為單一 HTML 檔，正式產品應拆分為 React/Vue 前端
