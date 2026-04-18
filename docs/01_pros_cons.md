# 01 — POC 現況評估（Pros / Cons）

> 給 Alex 的週末 review 文件 #1 / 共 4 份
> 目的：先弄清楚「這個 POC 已經做到哪裡、哪裡還不夠」，再決定週末要加什麼。
> 原則：**跳過枝微末節的工程瑕疵**，專注在「MA 審核委員第一次玩會不會被記住」。

---

## ✅ 這個 POC 真正紮實的地方（Pros）

| # | 項目 | 證據（檔案／函式） |
|---|------|-------------------|
| 1 | **SM-2 真的接好了**，不是擺設 | `app/services/quiz_service.py` 的 submit 流程 → 呼叫 `score_to_quality()` → `calculate_next_interval()` → 寫回 `review_schedule`。學理 + 落地，整條 pipe 通了 |
| 2 | **Sprint Reader 的反作弊設計有完成度** | 前端 `visibilitychange` 暫停計時器 + 遞增 `tab_switch_count`，後端 `sprint_sessions` 收這個欄位。這在 POC 層級已經算用心 |
| 3 | **埋好了 ML 分析 hook** | `learning_journey_map` 把 `sprint_id` ↔ `quiz_session_id` 綁在一起。未來任何「切頁次數 vs 測驗分數」類的 query 都能直接跑，不用 refactor |
| 4 | **58,670 筆真實台灣法規資料** | `data/` 底下四個檔（裁罰、函令、全國法規、主管法規），首次啟動自動 ingest 到 `comp_*` 四張表 + FULLTEXT 索引。**不是假資料**，這在 POC 很難得 |
| 5 | **後端分層乾淨、沒有 SQL injection 風險** | `api/` → `services/` → `core/database.py`，全部 raw PyMySQL + `%s` 參數化 SQL，沒有 ORM 也沒有字串拼接 |
| 6 | **現代工具鏈** | Python 3.12 + `uv` + Docker Compose + FastAPI lifespan 啟動 seed — 2026 的實習生該會的都用到了 |
| 7 | **Dashboard 視覺化已經有** | Chart.js 長條圖秀各主題掌握度 + streak 天數 + 即將到期複習清單。基礎框架已在位 |
| 8 | **安全設定不踩雷** | bcrypt + httponly cookie + `samesite=lax`，POC 階段這樣夠了 |

---

## ⚠️ 為什麼「不夠 stand out」（Cons — 週末要補的方向）

這些都不是 bug，是「功能合格但情感記憶點為零」的問題。MA 審核委員玩一次不會想玩第二次。

| # | 問題 | 什麼感覺 |
|---|------|----------|
| A | **測驗沒有 per-question feedback** | 5 題答完交卷 → 只看到「60 / 100 及格」。根本不知道哪題錯、為什麼錯。審核委員會覺得：「這不就是傳統線上測驗？」 |
| B | **沒有 gamification 的情感回饋** | 完成模組那一刻，沒有動畫、沒有獎勵、沒有「再來一回合」的鉤子。分數 59 紅字、60 綠字，就這樣 |
| C | **題型單一** | 只有 MCQ + True/False。12 個模組玩下來完全同一種節奏，沒新鮮感 |
| D | **答錯就扣分、不給重試** | 跟 Duolingo 證實有效的「寬容重試」哲學相反。用戶會有「被評分」的壓力感而不是「被陪伴學習」 |
| E | **Streak 有記錄但沒慶祝、沒保護** | `dashboard_service.py` 已經在算連續天數，但前端只是個數字。loss aversion 這個強力心理槓桿完全沒用到 |
| F | **沒有 XP / level / 角色** | 沒有累積感、沒有成長儀式感。完成一個模組和完成十個模組，體感差不多 |
| G | **12 模組的 flashcard + 題目全部手寫** | 寫死在 `app/data/loader.py` 裡，跟 `data/` 那 58k 筆法規完全沒連起來。內容深度受限。**週末解不了，但要在 pitch 時點出這是下一步 roadmap** |

---

## 💬 一句話總結

> 目前 POC 像是「一份有學理依據的合格測驗系統」，週末要把它變成「一個會讓審核委員想再玩一次的微學習產品」。

**這份 review 系列的其他文件：**
- `02_weekend_plan.md` — 菜單式改進清單，Alex 挑想做的勾選
- `03_samples_en.md` / `03_samples_zh.md` — 關鍵項目的可抄 code 片段

---

## 📝 Alex 的補充 / 自己看到的 pros 或 cons

> 預留這塊給 Alex 自己加。你玩過自己寫的東西最清楚，如果你覺得我漏了什麼、或有我沒意識到的強項／弱點，寫在這邊：

-

-

-
