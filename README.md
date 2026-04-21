# LexPulse

> 為台灣金融法遵專業人員打造的遊戲化微學習平台

---

## 這個專案在解決什麼問題？

金融法遵人員每天面對大量更新的法規、函令與裁罰案例，卻幾乎沒有時間系統性地學習。傳統教育訓練冗長、缺乏回饋、學完就忘。

LexPulse 的答案是：**每次只要 7 分鐘**。一個模組、五張閃卡、一次小測驗，搭配科學化的間隔複習排程，讓合規知識在零碎時間中真正被記住。

---

## 核心設計精神

**學習要短、要有感、要持續。**

- **Sprint Reader** — 類限時動態的滑動閱讀，計時器製造適度緊張感，促進專注
- **即測即反饋** — 閱讀完立即進入測驗，趁記憶新鮮時鞏固
- **SM-2 間隔複習** — 答得好的概念隔得久再複習，答錯的隔天就回來，不浪費時間也不遺漏弱點
- **XP 與等級** — 把枯燥的合規學習轉化為可量化的成長感，從「新手法遵員」晉升到「法遵守護者」

---

## 功能地圖

| 功能 | 說明 |
|------|------|
| 7 分鐘 Sprint Reader | 行動優先的滑動閃卡，精準倒數計時，切換分頁自動暫停 |
| 即時測驗 | Sprint 結束後自動銜接，MCQ / True-False 即時批改 |
| SM-2 間隔複習 | 依答題成績自動排定下次複習日，儀表板顯示到期提醒 |
| XP 等級系統 | 6 級晉升制度，升級觸發獎勵兌換 |
| 學習分析儀表板 | 各主題掌握度圓餅圖、連續學習 Streak、Freeze 機制 |
| 法遵資料庫 | 70MB+ 台灣金融法規全文搜尋（裁罰、函令、全國法規、主管法規） |

---

## 技術架構

| 層級 | 技術選擇 |
|------|----------|
| 後端 | Python 3.12 + FastAPI + Uvicorn |
| 前端 | Vanilla JS + Tailwind CSS + Chart.js（POC 階段） |
| 資料庫 | MySQL 8.0（Docker Compose） |
| 認證 | bcrypt + HMAC-SHA256 JWT |
| 套件管理 | uv |

---

## XP 等級系統

| 等級 | XP 門檻 |
|------|---------|
| 新手法遵員 | 0 |
| 合規見習生 | 100 |
| 法遵分析師 | 300 |
| 合規達人 | 700 |
| 法遵大師 | 1,500 |
| 法遵守護者 | 3,000 |

---

## 資料庫 Schema（13 張表）

**學習核心**：`users`、`modules`、`flashcard_pages`、`questions`、`sprint_sessions`、`quiz_sessions`、`question_responses`、`learning_journey_map`、`review_schedule`

**法遵資料**：`comp_penalties`、`comp_regulations`、`comp_national_laws`、`comp_fsc_directives`

---

## 架構演進方向

本專案以 `sample/` 作為整合型 POC 驗證核心功能與使用者流程。POC 確認可行後，將逐步拆解為獨立的前後端服務：

```
KGI/
├── sample/      # 整合型 POC — FastAPI 同時負責 API 與前端渲染（現行）
├── backend/     # 拆解後的 API 服務（FastAPI，Pure REST）
└── frontend/    # 拆解後的前端應用（React / Vue，獨立部署）
```

**拆解的動機：**
- POC 階段使用 Jinja2 Server-Side Rendering + 單一 HTML 快速驗證想法
- 正式產品需要前端獨立迭代、元件化測試、更好的狀態管理
- 後端獨立後可橫向擴展，並在不影響前端的情況下替換資料庫或底層服務

`backend/` 與 `frontend/` 目前為預留目錄，持續開發中。

---

## 資料來源

平台內建的法遵資料庫來自台灣公開法規資料：

- 金管會裁罰案例
- 金管會函令法規
- 全國法規資料庫
- 保險局 / 銀行局 / 證期局主管法規

---

## 相關文件

| 文件 | 說明 |
|------|------|
| [`sample/README.md`](sample/README.md) | POC 技術細節、API 端點、啟動方式 |
| [`docs/design_philosophy.md`](docs/design_philosophy.md) | 設計決策與取捨說明 |
| [`docs/system_architecture.md`](docs/system_architecture.md) | 系統架構圖與資料流 |
| [`docs/microlearning_app_spec.md`](docs/microlearning_app_spec.md) | 功能規格書 |
