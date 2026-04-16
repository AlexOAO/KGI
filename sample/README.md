# KGI 法遵合規微學習平台 — Sample POC

金融法遵合規微學習平台的 Proof of Concept，整合間隔複習（SM-2）、7 分鐘 Sprint Reader、測驗評分，以及完整的法遵資料庫搜尋功能。

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
uv run uvicorn main:app --host 0.0.0.0 --port 7860

# 開啟瀏覽器前往 http://localhost:7860
```

**預設帳號**

| 帳號 | 密碼 | 角色 |
|------|------|------|
| learner1 | pass123 | 學習者 |
| admin1 | admin123 | 管理員 |

---

## 功能說明

### 學習模組（12 個）

| 模組名稱 | 主題標籤 | 難度 |
|----------|----------|------|
| 保險法基礎概念 | #保險法 #合規 | 1 |
| 金融消費者保護法要點 | #消費者保護 #金融法規 | 2 |
| 洗錢防制法規重點 | #洗錢防制 #合規 | 2 |
| 證券交易法核心概念 | #證券交易 #資本市場 | 2 |
| 銀行法監理要點 | #銀行法 #金融監理 | 2 |
| 個人資料保護法實務 | #個資法 #資安合規 | 2 |
| 期貨交易法規概述 | #期貨 #衍生性商品 | 3 |
| 投信投顧法規重點 | #投信 #投顧 #資產管理 | 3 |
| 公司治理與內部控制 | #公司治理 #內部控制 | 2 |
| 信託業法規要點 | #信託業 #財富管理 | 2 |
| 電子支付與金融科技法規 | #電子支付 #金融科技 | 3 |
| 資本適足率與風險管理 | #資本適足率 #巴塞爾協議 | 3 |

> **注意**：各模組的閃卡與測驗題目目前為依據台灣金融法規通用知識**手動撰寫**，尚未從提供的原始法遵資料集自動生成。

每個模組包含：
- 5 張閃卡（Sprint Reader 7 分鐘倒數計時）
- 5 題測驗（MCQ / True-False）
- SM-2 間隔複習排程（依測驗成績自動更新）

### Sprint Reader

- 7 分鐘倒數計時器，切換分頁時自動暫停
- 記錄分頁切換次數（`tab_switch_count`）
- 不可倒退翻卡
- 完成後自動進入測驗

### 測驗與 SM-2

- 答題後即時評分
- 成績對應 SM-2 quality 分數（90-100 → 5，75-89 → 4，60-74 → 3，40-59 → 2，<40 → 0）
- 自動更新下次複習日期與易度係數

### 儀表板

- 各主題掌握度長條圖（Chart.js）
- 即將到期複習清單

### 法遵資料庫

收錄四類法遵資料，共 **58,670 筆**：

| 資料集 | 筆數 | 說明 |
|--------|------|------|
| 裁罰案例 | 1,116 | 重大裁罰 / 非重大裁罰，含機構別 |
| 函令法規 | 514 | 金管會、勞動部、銀行公會等函令 |
| 全國法規 | 50,898 | 全國法規資料庫條文（法律 / 憲法層級） |
| 主管法規 | 6,142 | 金管會各局主管法規（保險局/銀行局/證期局） |

支援功能：
- 關鍵字全文搜尋（MySQL FULLTEXT BOOLEAN MODE）
- 多維度篩選（裁罰類別、機構、法規體系、法律層級）
- 點擊列表項目查看完整內容
- 分頁顯示，附結果總數

---

## 資料夾結構

```
sample/
├── docker-compose.yml        # MySQL 8.0 容器
├── .env.example              # 環境變數範本
├── pyproject.toml            # uv 依賴設定
├── main.py                   # FastAPI 應用進入點
├── templates/
│   └── index.html            # 單頁應用（SPA）
└── app/
    ├── core/
    │   ├── config.py         # 環境變數讀取
    │   └── database.py       # PyMySQL 連線
    ├── data/
    │   ├── schema.sql        # 建表 SQL（12 張表）
    │   └── loader.py         # 資料載入 + seed_demo_data()
    ├── api/
    │   ├── auth.py           # 登入 / 登出 / JWT
    │   ├── modules.py        # 模組列表 / 閃卡
    │   ├── sprint.py         # Sprint 開始 / 結束
    │   ├── quiz.py           # 測驗題目 / 提交
    │   ├── dashboard.py      # 儀表板資料
    │   └── compliance.py     # 法遵搜尋 / 詳細 / 篩選器
    └── services/
        └── sm2.py            # SM-2 間隔複習演算法
```

---

## 資料庫 Schema

**學習相關（9 張表）**：`users`、`modules`、`flashcard_pages`、`questions`、`sprint_sessions`、`quiz_sessions`、`question_responses`、`learning_journey_map`、`review_schedule`

**法遵資料（4 張表）**：`comp_penalties`、`comp_regulations`、`comp_national_laws`、`comp_fsc_directives`

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

## 已知限制 / 待改進

- 閃卡與測驗題目為手動撰寫，未從原始資料集自動生成
- 無管理員後台（新增 / 編輯模組需直接操作 DB）
- 認證為簡易 JWT，正式環境需換用成熟 Auth 方案
- 前端為單一 HTML 檔，規模擴大後應拆分為 React/Vue 前端
