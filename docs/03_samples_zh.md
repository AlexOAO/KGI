# 03 — 程式碼範例（繁體中文版）

> Review 文件包 3 / 4 — 英文鏡像：`03_samples_en.md`
>
> **Tier 1 三項 + Tier 2.4 新題型** 的可抄片段。每段標了對應的 Tier。
> 請搭配 `sample/app/` 既有的風格調整，**不要整檔重寫**。

---

## Section 1 — Schema 增欄位（只做一次）

> **檔案**：`sample/app/data/schema.sql`。在首次啟動 seed 前把 ALTER 加上，或寫一個一次性 migration script 給已有資料的情況用。

```sql
-- [Tier 1.1] 追蹤首答正確性，用於 SM-2 quality 計算
ALTER TABLE question_responses
  ADD COLUMN attempt_number INT NOT NULL DEFAULT 1 AFTER is_correct,
  ADD COLUMN first_attempt_correct TINYINT(1) NOT NULL DEFAULT 0 AFTER attempt_number;

-- [Tier 1.2] XP 跟等級
ALTER TABLE users
  ADD COLUMN total_xp INT NOT NULL DEFAULT 0;

ALTER TABLE quiz_sessions
  ADD COLUMN xp_earned INT NOT NULL DEFAULT 0;

-- [Tier 1.3] Streak Freeze
ALTER TABLE users
  ADD COLUMN streak_freeze_count INT NOT NULL DEFAULT 0,
  ADD COLUMN last_streak_day DATE NULL;

-- [Tier 2.4] 擴充題型
ALTER TABLE questions
  MODIFY COLUMN type ENUM('mcq','tf','match','fill') NOT NULL DEFAULT 'mcq';
```

---

## Section 2 — 後端：`/api/quiz/check` 單題即時檢查 endpoint（Tier 1.1）

> **檔案**：接在 `sample/app/api/quiz.py` 現有 router 後面
>
> 這是「寬容重試」核心 endpoint：檢查**一題**、不結 session、不扣分，讓前端可以一直重試。

```python
# sample/app/api/quiz.py  — 加到現有 router 後面

class CheckAnswerRequest(BaseModel):
    module_id: int
    question_id: int
    user_answer: str
    attempt_number: int = 1  # 前端每次答錯就 +1 再送

@router.post("/quiz/check")
def api_check_answer(req: CheckAnswerRequest, user=Depends(get_current_user)):
    # 從 DB 查正解但不 expose 給前端
    from app.core.database import get_conn
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT correct_answer FROM questions WHERE id=%s AND module_id=%s",
                (req.question_id, req.module_id),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return {"correct": False, "error": "question_not_found"}

    is_correct = req.user_answer.strip() == row["correct_answer"].strip()
    return {
        "correct": is_correct,
        "attempt_number": req.attempt_number,
        # 第一次就答對 → SM-2 quality 滿分；重試才對 → 降一級
        "first_attempt": req.attempt_number == 1 and is_correct,
    }
```

---

## Section 3 — 後端：改造 `grade_quiz`（Tier 1.1 + 1.2 整合）

> **檔案**：`sample/app/services/quiz_service.py` — 把 `grade_quiz` 整個換成這版
>
> 重點改動：前端額外送 `first_attempt_map`（哪些題是第一次就對）。分數跟 SM-2 quality 都根據「首答正確率」算，不是「最終正確率」。XP 也是照這個規則發。

```python
from app.services.xp_service import compute_xp, update_user_xp

def grade_quiz(
    user_id: int,
    sprint_id,
    module_id: int,
    questions: list,
    answers: dict,             # {qid: 最終答對的答案}
    first_attempt_map: dict,   # {qid: bool — 第一次就對嗎?}
    topic_tag: str = None,
):
    responses = []
    correct_first_try = 0
    for q in questions:
        qid = str(q["id"])
        user_ans = answers.get(qid, "")
        first_ok = bool(first_attempt_map.get(qid, False))
        if first_ok:
            correct_first_try += 1
        responses.append({
            "question_id": q["id"],
            "user_answer": user_ans,
            "is_correct": 1,                           # 到 submit 時間點題目都「最終答對」了
            "first_attempt_correct": int(first_ok),
            "attempt_number": 1 if first_ok else 2,
            "response_time_ms": 0,
        })

    total = len(questions)
    # SM-2 quality 用首答正確率算，不用「最後有沒有對」
    score = (correct_first_try / total * 100) if total else 0
    xp_earned = compute_xp(correct_first_try, total)

    quiz_session_id = save_quiz_session(
        sprint_id, user_id, module_id, score, responses, xp_earned=xp_earned,
    )

    if topic_tag:
        quality = score_to_quality(score)
        _update_review_schedule(user_id, topic_tag, quality)

    new_total_xp, leveled_up, new_level = update_user_xp(user_id, xp_earned)

    return {
        "score": score,
        "correct_first_try": correct_first_try,
        "total": total,
        "quiz_session_id": quiz_session_id,
        "xp_earned": xp_earned,
        "total_xp": new_total_xp,
        "leveled_up": leveled_up,
        "level_name": new_level,
    }
```

> 記得 `app/models/quiz.py` 的 `save_quiz_session` 也要改，把 `xp_earned` 跟每題的 `first_attempt_correct` / `attempt_number` 寫進去。

---

## Section 4 — 後端：`services/xp_service.py`（Tier 1.2，新檔）

```python
# sample/app/services/xp_service.py
from app.core.database import get_conn

# (最低 XP, 稱號)
LEVELS = [
    (0,    "新手法遵員"),
    (100,  "合規見習生"),
    (300,  "法遵分析師"),
    (700,  "合規達人"),
    (1500, "法遵大師"),
]

def level_for(xp: int):
    current = LEVELS[0]
    next_level = None
    for i, (min_xp, name) in enumerate(LEVELS):
        if xp >= min_xp:
            current = (min_xp, name)
            next_level = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
    return {
        "xp": xp,
        "level_name": current[1],
        "level_min_xp": current[0],
        "next_level_name": next_level[1] if next_level else None,
        "next_level_xp": next_level[0] if next_level else None,
        "progress_pct": (
            (xp - current[0]) / (next_level[0] - current[0]) * 100
            if next_level else 100
        ),
    }

def compute_xp(correct_first_try: int, total: int) -> int:
    # 每題首答對 +10、首答對另加 +5 bonus、整模組 100% 首答對再 +25
    base = correct_first_try * 10
    first_try_bonus = correct_first_try * 5
    perfect_bonus = 25 if correct_first_try == total and total > 0 else 0
    return base + first_try_bonus + perfect_bonus

def update_user_xp(user_id: int, delta: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT total_xp FROM users WHERE id=%s", (user_id,))
            old = cur.fetchone()["total_xp"]
            new_total = old + delta
            cur.execute("UPDATE users SET total_xp=%s WHERE id=%s", (new_total, user_id))
            old_level = level_for(old)["level_name"]
            new_info = level_for(new_total)
            leveled_up = old_level != new_info["level_name"]
        conn.commit()
    finally:
        conn.close()
    return new_total, leveled_up, new_info["level_name"]
```

---

## Section 5 — 後端：`GET /api/me/level`（Tier 1.2）

> **檔案**：接在 `sample/app/api/auth.py` 或新建 `sample/app/api/me.py`

```python
@router.get("/me/level")
def api_me_level(user=Depends(get_current_user)):
    from app.core.database import get_conn
    from app.services.xp_service import level_for
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT total_xp FROM users WHERE id=%s", (user["user_id"],))
            row = cur.fetchone()
    finally:
        conn.close()
    return level_for(row["total_xp"] if row else 0)
```

---

## Section 6 — 前端 CSS：shake + confetti（Tier 1.1 + 1.2）

> **檔案**：加到 `sample/templates/index.html` 現有的 `<style>` 區塊

```css
/* [Tier 1.1] 答錯震動動畫 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%      { transform: translateX(-8px); }
  40%      { transform: translateX(8px); }
  60%      { transform: translateX(-6px); }
  80%      { transform: translateX(6px); }
}
.answer-wrong {
  border: 2px solid #ef4444 !important;
  background: #fef2f2;
  animation: shake 0.5s ease-in-out;
}
.answer-correct {
  border: 2px solid #10b981 !important;
  background: #ecfdf5;
  transition: all 0.3s;
}

/* [Tier 1.2] 純 CSS confetti，不引套件 */
@keyframes confetti-fall {
  0%   { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
  100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
}
.confetti {
  position: fixed;
  top: 0;
  width: 10px; height: 14px;
  pointer-events: none;
  animation: confetti-fall 2.5s linear forwards;
  z-index: 9999;
}

/* [Tier 1.2] XP 進度條 */
.xp-bar-outer {
  height: 10px; width: 100%;
  background: #e5e7eb; border-radius: 5px; overflow: hidden;
}
.xp-bar-fill {
  height: 100%; background: linear-gradient(90deg, #fbbf24, #f59e0b);
  border-radius: 5px; transition: width 0.8s ease-out;
}
```

---

## Section 7 — 前端 JS：寬容重試邏輯（Tier 1.1）

> **檔案**：放進 `sample/templates/index.html` 現有 `<script>`。把原本的「點選項 → submit 整份」改成「點選項 → 即時檢查 → 錯了重試」。

```javascript
// [Tier 1.1] 寬容重試 + 每題 attempt 追蹤
const firstAttemptMap = {};  // { question_id: true|false }
const attemptCounts = {};    // { question_id: 嘗試次數 }

async function handleOptionClick(questionId, optionValue, optionEl) {
  if (firstAttemptMap[questionId] !== undefined && firstAttemptMap[questionId]) {
    return; // 已經答對過了，忽略
  }

  attemptCounts[questionId] = (attemptCounts[questionId] || 0) + 1;

  const res = await fetch('/api/quiz/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      module_id: state.currentModule.id,
      question_id: questionId,
      user_answer: optionValue,
      attempt_number: attemptCounts[questionId],
    }),
  });
  const data = await res.json();

  if (data.correct) {
    optionEl.classList.add('answer-correct');
    if (firstAttemptMap[questionId] === undefined) {
      firstAttemptMap[questionId] = (attemptCounts[questionId] === 1);
    }
    showMascotBubble(
      attemptCounts[questionId] === 1 ? "漂亮！這題你穩的 ✨" : "嗯！答對了～",
    );
    setTimeout(() => advanceToNextQuestion(questionId, optionValue), 800);
  } else {
    optionEl.classList.add('answer-wrong');
    showMascotBubble("不是這個喔～");
    setTimeout(() => optionEl.classList.remove('answer-wrong'), 600);
    if (firstAttemptMap[questionId] === undefined) {
      firstAttemptMap[questionId] = false;
    }
  }
}

// 最後送出時，把 first_attempt_map 一起送回去
async function submitQuiz() {
  const res = await fetch('/api/quiz/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sprint_id: state.sprintId,
      module_id: state.currentModule.id,
      answers: state.quizAnswers,
      first_attempt_map: firstAttemptMap,  // 新增
    }),
  });
  const data = await res.json();
  showCompletionScreen(data);   // 接 Tier 1.2
}
```

---

## Section 8 — 前端 JS：XP 進度條 + 升級偵測（Tier 1.2）

```javascript
// [Tier 1.2] 取代舊的「只秀分數」畫面
function showCompletionScreen(data) {
  // data = { score, correct_first_try, total, xp_earned, total_xp, leveled_up, level_name }
  document.getElementById('quiz-screen').classList.remove('active');
  const screen = document.getElementById('completion-screen');
  screen.classList.add('active');

  screen.querySelector('.xp-delta').textContent = `+${data.xp_earned} XP`;
  screen.querySelector('.level-name').textContent = data.level_name;

  // 動畫 XP bar
  fetch('/api/me/level').then(r => r.json()).then(lvl => {
    screen.querySelector('.xp-bar-fill').style.width = `${lvl.progress_pct}%`;
    screen.querySelector('.xp-total').textContent = `${lvl.xp} XP`;
  });

  if (data.leveled_up) {
    showLevelUpBanner(data.level_name);
    launchConfetti();
  } else if (data.correct_first_try === data.total) {
    launchConfetti();   // 整模組首答都對也灑花
  }
}

function launchConfetti() {
  const colors = ['#fbbf24', '#10b981', '#3b82f6', '#ef4444', '#a855f7'];
  for (let i = 0; i < 80; i++) {
    const el = document.createElement('div');
    el.className = 'confetti';
    el.style.left = Math.random() * 100 + 'vw';
    el.style.background = colors[i % colors.length];
    el.style.animationDelay = (Math.random() * 0.8) + 's';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  }
}

function showLevelUpBanner(levelName) {
  const banner = document.getElementById('levelup-banner');
  banner.querySelector('.new-level').textContent = levelName;
  banner.classList.add('show');
  setTimeout(() => banner.classList.remove('show'), 3000);
}
```

---

## Section 9 — Dashboard streak freeze 小元件（Tier 1.3）

```javascript
// [Tier 1.3] streak 火焰 + freeze 計數
async function renderStreakChip() {
  const res = await fetch('/api/dashboard');
  const data = await res.json();
  const el = document.getElementById('streak-chip');
  el.innerHTML = `
    <span class="flame">🔥</span>
    <span class="days">${data.streak} 天</span>
    <span class="freeze" title="可用的 streak freeze 數">
      ❄️ × ${data.streak_freeze_count}
    </span>
  `;
  if (data.streak >= 7 && data.streak % 7 === 0 && data.just_unlocked_freeze) {
    showToast('🎉 解鎖一個 streak freeze！錯過一天也不怕斷連勝');
  }
}
```

> 後端：在 `app/services/dashboard_service.py` 算 streak 時，如果偵測到中斷，先檢查 `streak_freeze_count > 0`，有的話消耗一個（-1）、streak 照算；沒有才歸零。

---

## Section 10 — Tier 2.4：配對題 + 填空題

### Schema / options_json 格式

```json
// type = 'match'
{
  "pairs": [
    { "left": "洗錢防制法", "right": "KYC / 客戶盡職調查" },
    { "left": "個人資料保護法", "right": "當事人權利 / 目的限定" },
    { "left": "證券交易法 §157-1", "right": "內線交易禁止" }
  ]
}

// type = 'fill'
{
  "sentence": "大額現金交易申報門檻為 ___ 萬元。",
  "choices": ["30", "50", "100"]
}
// correct_answer 欄位存 "50"
```

### 配對題 render（前端）

```javascript
// [Tier 2.4] 點左邊 → 點右邊 → 配對
function renderMatchQuestion(q, container) {
  const pairs = JSON.parse(q.options_json).pairs;
  const left = pairs.map(p => p.left);
  const right = shuffle(pairs.map(p => p.right));
  let selectedLeft = null;
  const matched = new Set();

  container.innerHTML = `
    <div class="match-grid">
      <div class="match-col">${left.map((t, i) =>
        `<button class="match-item left" data-i="${i}" data-val="${t}">${t}</button>`
      ).join('')}</div>
      <div class="match-col">${right.map(t =>
        `<button class="match-item right" data-val="${t}">${t}</button>`
      ).join('')}</div>
    </div>
  `;

  container.querySelectorAll('.match-item.left').forEach(btn => {
    btn.onclick = () => {
      if (matched.has(btn.dataset.val)) return;
      container.querySelectorAll('.match-item.left').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedLeft = btn;
    };
  });
  container.querySelectorAll('.match-item.right').forEach(btn => {
    btn.onclick = () => {
      if (!selectedLeft || matched.has(btn.dataset.val)) return;
      const correctRight = pairs.find(p => p.left === selectedLeft.dataset.val).right;
      if (btn.dataset.val === correctRight) {
        btn.classList.add('answer-correct');
        selectedLeft.classList.add('answer-correct');
        matched.add(btn.dataset.val);
        if (matched.size === pairs.length) {
          setTimeout(() => advanceToNextQuestion(q.id, 'matched_all'), 600);
        }
      } else {
        btn.classList.add('answer-wrong');
        setTimeout(() => btn.classList.remove('answer-wrong'), 600);
      }
      selectedLeft.classList.remove('selected');
      selectedLeft = null;
    };
  });
}
```

### 填空題 render

```javascript
function renderFillQuestion(q, container) {
  const opts = JSON.parse(q.options_json);
  container.innerHTML = `
    <div class="fill-sentence">${opts.sentence.replace('___', '<span class="fill-blank">____</span>')}</div>
    <div class="fill-choices">
      ${opts.choices.map(c =>
        `<button class="fill-choice" data-val="${c}">${c}</button>`
      ).join('')}
    </div>
  `;
  container.querySelectorAll('.fill-choice').forEach(btn => {
    btn.onclick = () => handleOptionClick(q.id, btn.dataset.val, btn);
  });
}
```

---

## Section 11 — Claude Code prompt 範本

一次貼一個、照順序丟給 Claude Code。

### Prompt A — Tier 1.1（寬容重試）
```
先讀 app/api/quiz.py、app/services/quiz_service.py、app/models/quiz.py、
templates/index.html 的 quiz screen，然後實作 Duolingo 風格的寬容重試：

1. schema.sql 加 ALTER TABLE：question_responses 多 attempt_number 跟
   first_attempt_correct 欄位。
2. 新增 POST /api/quiz/check，對單題回 {correct, first_attempt}，不結 session。
3. 改 grade_quiz 接收 first_attempt_map，SM-2 quality 用首答正確率算，
   不是用最終正確率。
4. index.html 把原本 option 的 click handler 換成：
   - 答錯 = 紅框 + shake 動畫 + 可繼續點
   - 答對 = 綠框 + 0.8 秒後進下一題
   - 前端維護 firstAttemptMap，最後 submit 時一起送
5. 動畫用純 CSS，不要引任何套件。

參考 03_samples_zh.md 的 Section 1, 2, 3, 6, 7。
保留既有 code style（raw PyMySQL、沒 ORM、%s 參數）。
```

### Prompt B — Tier 1.2（XP + 等級 + 慶祝畫面）
```
建 XP 跟等級系統：

1. ALTER users 加 total_xp、quiz_sessions 加 xp_earned。
2. 新建 app/services/xp_service.py，含 LEVELS 對照表（新手法遵員 → 法遵大師）、
   level_for(xp)、compute_xp(first_try, total)、update_user_xp(user_id, delta)。
3. 新增 GET /api/me/level，回傳 {xp, level_name, progress_pct, next_level_xp}。
4. grade_quiz 裡呼叫 compute_xp 跟 update_user_xp，response 補上 xp_earned /
   leveled_up / level_name。
5. 做個完成畫面取代現在的「只秀分數」：
   - +45 XP 的增量動畫
   - XP 進度條填到 progress_pct
   - 等級徽章
   - 升級 or 整模組首答全對時灑 CSS confetti

參考 03_samples_zh.md 的 Section 4, 5, 6, 8。
```

### Prompt C — Tier 2.4（新題型）
```
加 MCQ 跟 TF 以外的兩種新題型：

1. ALTER questions.type enum 加 'match' 跟 'fill'。
2. app/data/loader.py 在不同模組加 2 題 match 跟 2 題 fill 當 demo 內容。
3. index.html 加 renderMatchQuestion() 跟 renderFillQuestion()。
   主 quiz loop 依 question.type 分派到對的 renderer。
4. 配對題：點左邊 → 點右邊 → 正確配對綠色；全部配完進下一題。
5. 填空題：句子加 ___、3 個選項按鈕，重用 Tier 1.1 的 handleOptionClick。

參考 03_samples_zh.md 的 Section 10。重用既有的 shake/correct CSS。
```

---

## 附錄 — commit 前自我檢查

- [ ] 首答正確率真的有傳到 SM-2 quality（重試才對 → quality 真的變低）
- [ ] XP 有持久化（refresh 瀏覽器 XP 還在）
- [ ] confetti 不會蓋到「下一個模組」按鈕
- [ ] 新題型不會弄壞既有的 MCQ/TF 流程
- [ ] Streak freeze 真的會在斷 streak 當天自動消耗（可以手動改系統時間或插一筆舊的 quiz_sessions 測）
