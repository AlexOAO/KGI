# 02 — 週末改進菜單（Weekend Plan）

> 給 Alex 的週末 review 文件 #2 / 共 4 份
> 目的：**菜單，不是腳本**。挑你想做的打勾，沒時間做的直接跳過。
> Deadline：Monday afternoon（今天 Friday 2026-04-17）

---

## 🎯 核心論述（pitch 時可以直接講）

> **「用 SM-2 做對抗遺忘的科學內核，用 Duolingo 機制做持續回訪的情感外殼。」**

- SM-2 處理「學完會忘」— 已經做到了
- Duolingo 機制處理「沒動力回來學」— 這週末要補
- 這兩個加起來才是 2026 的 micro-learning，不是傳統的「上課打卡」

**為什麼 MA 審核會加分：** 你不只是「把需求做出來」，你對 learning science（Ebbinghaus forgetting curve）+ behavioral design（loss aversion, variable rewards）有觀點，而且用產品決策反映了這個觀點。

**研究佐證（可以在簡報引用）：**
- Duolingo streak 讓 commitment +60%，每 5 位 DAU 就有 1 位 streak > 365 天
- XP + leaderboard 讓每週完成課程 +40%
- Streak Freeze 讓瀕臨斷 streak 的用戶 churn -21%

---

## 📋 怎麼用這份菜單

每個項目格式：

```
[ ] Tier X.Y — 標題（~時數）
  目的 · 用戶故事 · 改到哪些檔 · 依賴 · 預期效果
  → Claude Code prompt 範本（貼上去可以直接 vibe）
```

**勾選規則：** 大部分項目彼此獨立；有依賴會明寫「依賴：Tier X.Y」。

---

## Tier 1 — 高槓桿（推薦全做，預估 6–8h）

> 「只做這三項 demo 就會脫胎換骨」。三項彼此完全獨立。

### `[ ]` Tier 1.1 — 寬容重試 + 首答記錄 + 震動動畫（~2h）

- **目的**：把測驗從「考試」變「陪伴學習」— 這是最能讓審核委員第一眼注意到的改動
- **用戶故事**：我選錯答案 → 紅框閃爍 + shake 動畫 + 「不是這個喔 🤔」提示 → 我可以繼續點其他選項 → 直到選對才進下一題 → 但 DB 偷偷記了我「第一次就對 vs 重試才對」
- **改到哪些檔**：
  - `sample/app/data/schema.sql` — `question_responses` 加 `attempt_number` + `first_attempt_correct`
  - `sample/app/api/quiz.py` — 新增 `POST /api/quiz/check`（單題檢查、不結 session）
  - `sample/app/services/quiz_service.py` — submit 時根據「有幾題第一次就對」算 SM-2 quality
  - `sample/templates/index.html` — quiz 畫面改成即時判定 + shake CSS
- **依賴**：無
- **預期效果**：demo 時故意答錯一題 → shake → 換對的 → 進下一題，觀眾第一次看會愣一下「欸這個不是傳統 quiz」

**Claude Code prompt 範本：**
```
在 templates/index.html 的 quiz screen 實作 Duolingo 風格的寬容重試：
1. 點選答案後立即檢查對錯（call 新的 POST /api/quiz/check）
2. 答錯時：該選項紅框 + shake 動畫 1 秒 + 上方顯示「不是這個喔」toast
3. 答錯不進下一題、不扣分、選項可以繼續點
4. 答對時：綠框 + 打勾 + 1 秒後進下一題
5. 背後呼叫後端記錄 attempt_number 和 first_attempt_correct
先讀 app/api/quiz.py 跟 templates/index.html 的現有結構再改，不要重寫整個 quiz flow。
```

---

### `[ ]` Tier 1.2 — XP 系統 + 等級頭銜 + 完成慶祝畫面（~3h）

- **目的**：取代死板的「60 分及格」分數畫面，改成遊戲式的通關儀式
- **用戶故事**：完成模組那一刻 → XP 進度條向前跑 → 秀「+45 XP」→ 如果升級就跳「🎉 升級！合規見習生 → 法遵分析師」→ 全屏 CSS confetti
- **等級對照表（建議）：**
  - 0–99 XP：新手法遵員
  - 100–299 XP：合規見習生
  - 300–699 XP：法遵分析師
  - 700–1499 XP：合規達人
  - 1500+ XP：法遵大師
- **XP 規則：** 答對 +10、第一次就對額外 +5、整個模組 100% 第一次就對 +25 bonus
- **改到哪些檔**：
  - `sample/app/data/schema.sql` — `users` 加 `total_xp INT DEFAULT 0`；`quiz_sessions` 加 `xp_earned INT DEFAULT 0`
  - `sample/app/services/xp_service.py`（新檔）— XP 計算 + 等級查表
  - `sample/app/api/auth.py` or 新 endpoint `GET /api/me/level` — 回傳當前 XP / 等級 / 下一級所需 XP
  - `sample/templates/index.html` — 完成畫面改造 + XP bar component + confetti CSS
- **依賴**：無（和 Tier 1.1 獨立；但兩者都做會互相加分）
- **預期效果**：審核委員看到升級動畫會笑出來

**Claude Code prompt 範本：**
```
實作 XP + 等級系統：
1. ALTER TABLE 加欄位 users.total_xp, quiz_sessions.xp_earned
2. 新建 app/services/xp_service.py，包含等級查表與計算函式
3. 在 quiz_service.py submit 時計算 xp_earned 並累加到 users.total_xp
4. 新增 GET /api/me/level 回傳 {xp, level_name, next_level_xp, progress_pct}
5. 前端完成畫面：XP bar 動畫 + 等級徽章 + (升級時) confetti 全屏動畫
純 CSS animation，不要引入任何套件。參考 03_samples_* 文件有完整 code。
```

---

### `[ ]` Tier 1.3 — Streak 慶祝 + Streak Freeze（~1h）

- **目的**：已經有的 streak 數字，把它變成情感觸發點
- **用戶故事**：Dashboard 右上角 🔥 火焰 + 大字「連續 5 天」→ 連續 7 天解鎖一個 streak freeze 存起來 → 某天沒玩，自動消耗 freeze 保護連勝
- **改到哪些檔**：
  - `sample/app/data/schema.sql` — `users` 加 `streak_freeze_count INT DEFAULT 0`
  - `sample/app/services/dashboard_service.py` — 計算 streak 時套用 freeze 保護邏輯
  - `sample/app/api/dashboard.py` — response 多回 freeze_count 和 unlock 進度
  - `sample/templates/index.html` — dashboard 右上角 🔥 元件 + 每 7 天解鎖動畫
- **依賴**：無
- **預期效果**：低成本，但放大了既有的 streak 邏輯，情感上很抓人

---

## Tier 2 — 有時間再加分（預估 4–6h）

### `[ ]` Tier 2.4 — 兩種新題型：配對題 + 填空題（~3h）

- **目的**：視覺變化最大的改動，一眼就能看出「不只 MCQ」
- **用戶故事**：
  - **配對題**：左欄法規名稱（洗錢防制法 / 個資法 / …）、右欄條文重點（KYC / 資料當事人權利 / …），tap 配對，全對才進下一題
  - **填空題**：「大額現金交易申報門檻為 ___ 萬元」→ 3 個選項 [30 / 50 / 100]
- **改到哪些檔**：
  - `sample/app/data/schema.sql` — `questions.type` enum 擴充成 `('mcq','tf','match','fill')`
  - `sample/app/data/loader.py` — seed 2–3 題 match 和 fill 當 demo 資料
  - `sample/templates/index.html` — 新增兩個 component render function
- **依賴**：如果要算 XP → 依賴 Tier 1.2
- **預期效果**：demo 時至少展示 2 種新題型，觀眾會覺得「這不只是把 MCQ 做出來」

---

### `[ ]` Tier 2.5 — 吉祥物 + 情境鼓勵訊息（~1h）

- **目的**：給產品一個臉，提高記憶點
- **建議角色**：戴眼鏡拿放大鏡的柴犬 / 小狐狸（金融檢查員形象）。可以純 emoji 🦊 + 文字氣泡，**不用畫圖、不用 Lottie**
- **7 種情境台詞（直接抄）：**
  - 開始 sprint：「準備好了嗎？7 分鐘，一起！」
  - 答對：「漂亮！這題你穩的 ✨」
  - 答錯：「欸欸，再想想～」
  - 連對 3 題：「狀態來了！繼續 🔥」
  - 完成模組：「今天的份搞定！明天見～」
  - 升級：「哇！你現在是 {new_level} 了 🎉」
  - 斷 streak：「沒關係，我們重新開始」
- **改到哪些檔**：`sample/templates/index.html` 加一個角色氣泡 component
- **依賴**：無（但和 Tier 1 配合效果最好）

---

### `[ ]` Tier 2.6 — Hearts / 生命值系統（~2h）

- **目的**：Duolingo 最標誌性的機制
- **用戶故事**：每天 5 顆心 ❤️ → 答錯第一次扣 1 顆（只扣第一次錯的那題）→ 心用完當日鎖測驗（只能看 flashcard）→ 每 4 小時補 1 顆 / 看完 1 篇 compliance 資料庫文章 +1（**把現有的搜尋頁變成 gamify 入口！**）
- **改到哪些檔**：
  - `sample/app/data/schema.sql` — `users` 加 `hearts INT DEFAULT 5`, `hearts_refill_at TIMESTAMP`
  - `sample/app/services/quiz_service.py` — 扣心邏輯
  - `sample/app/api/compliance.py` — 詳閱文章 → 加心 endpoint
  - `sample/templates/index.html` — top bar 秀心數
- **依賴**：Tier 1.1（要有「第一次錯」的概念才能扣對心）
- **注意**：扣心平衡不好反而惹毛審核委員；如果時間不夠寧可跳過

---

## Tier 3 — 超有餘裕才碰

### `[ ]` Tier 3.7 — 假 leaderboard（~1.5h）
塞 10 個假使用者資料，Dashboard 加個「本週 XP 排行榜」區塊。審核委員玩 demo 帳號會看到自己在第 X 名 → 有社交壓力感。

### `[ ]` Tier 3.8 — Dashboard 改成「今日任務」卡片式 UI（~2h）
把現在的「模組列表」包裝成「今日任務卡 / 複習任務卡 / 挑戰任務卡」三張卡片的首頁。更像手遊。

---

## 🍱 建議套餐（根據你實際能投入的時數）

| 你有 | 建議做 | 預期效果 |
|------|--------|----------|
| **4h** | Tier 1.1 + 1.3 | 視覺改變最明顯、風險最低 |
| **8h（週六整天）** | Tier 1 全包（1.1 + 1.2 + 1.3） | Demo 就脫胎換骨 |
| **14h（週六 + 週日半天）** | Tier 1 全包 + Tier 2.4 + Tier 2.5 | 視覺豐富度最高 |
| **週末 all-in（~20h+）** | Tier 1 + Tier 2 全包，視情況挑 Tier 3 | 最完整，但注意 Tier 2.6 風險 |

**我的建議：先做完 Tier 1，如果還有時間，Tier 2.4（新題型）CP 值最高，其次 Tier 2.5（吉祥物）。Tier 2.6（Hearts）和 Tier 3 只有在 **週日晚上還精神飽滿** 時才碰。**

---

## 🎬 Demo 3 分鐘腳本（週一簡報前先自己彩排一次）

| 時間 | 畫面 | 講什麼 |
|------|------|--------|
| 0:00–0:30 | 登入 → Dashboard | 指出 🔥 streak、XP 等級徽章、掌握度長條圖 |
| 0:30–1:30 | 點模組 → Pre-sprint → Sprint Reader | **故意切換分頁** 秀 `tab_switch_count` 埋點；講「這是為了偵測專注度，未來可以餵 ML 分析」 |
| 1:30–2:30 | 測驗 → **故意答錯** → shake 動畫 → 答對 → 完成 → confetti + 升級 | 講 SM-2 + 寬容重試並存：「科學內核 + 情感外殼」 |
| 2:30–3:00 | 切到法遵搜尋 | 秀 58,670 筆真實法規、講 roadmap（下一步 LLM 自動從這批資料生題目 + 管理後台） |

**Roadmap 段（給問答時用）：**
- Phase 2：LLM pipeline 自動從 `data/` 58k 筆資料生 flashcard + MCQ（現在是手寫）
- Phase 3：推播 + 管理員 dashboard（團隊弱點熱力圖）
- Phase 4：React Native mobile app（現在是 SPA）

---

## 📝 Alex 的自主擴充 / 我自己想做的（My own ideas）

> 這塊完全留給你。你玩過自己寫的東西，比任何人都清楚哪裡可以更有趣。
> 把你週末想到的新點子寫在這邊（寫的時候順便估工時），週一簡報同時秀「接收回饋」+「自主發揮」。
>
> 範例格式：
> - `[ ]` 我的點子 X — 做什麼 / 估 1h / 為什麼想做

- `[ ]`

- `[ ]`

- `[ ]`

---

## ✅ 週末結束前自我檢查

- [ ] 至少完成 Tier 1 三項中的 2 項
- [ ] demo 能完整跑過 3 分鐘腳本不卡
- [ ] git commit 紀錄清楚（方便審核委員看過程）
- [ ] `CLAUDE.md` 更新（repo root 已有一份，新增的 feature 加進去）
- [ ] 有一句話能回答「這個 POC 的差異化是什麼」
