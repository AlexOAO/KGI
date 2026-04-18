# 03 — Sample Code (English version)

> Review bundle file 3 / 4 — Chinese mirror: `03_samples_zh.md`
>
> Drop-in snippets for **Tier 1 (all three) + Tier 2.4 (new question types)**.
> Every snippet labels its Tier. Adapt to the existing patterns in `sample/app/` — do NOT rewrite whole files.

---

## Section 1 — Schema additions (apply once)

> **File**: `sample/app/data/schema.sql` — append the ALTERs or edit `CREATE TABLE` blocks before first-run seeding.
> Alternatively, write a one-off migration script if your DB already has data.

```sql
-- [Tier 1.1] track first-attempt correctness for SM-2 quality computation
ALTER TABLE question_responses
  ADD COLUMN attempt_number INT NOT NULL DEFAULT 1 AFTER is_correct,
  ADD COLUMN first_attempt_correct TINYINT(1) NOT NULL DEFAULT 0 AFTER attempt_number;

-- [Tier 1.2] XP and level
ALTER TABLE users
  ADD COLUMN total_xp INT NOT NULL DEFAULT 0;

ALTER TABLE quiz_sessions
  ADD COLUMN xp_earned INT NOT NULL DEFAULT 0;

-- [Tier 1.3] streak freeze
ALTER TABLE users
  ADD COLUMN streak_freeze_count INT NOT NULL DEFAULT 0,
  ADD COLUMN last_streak_day DATE NULL;

-- [Tier 2.4] extend question types
ALTER TABLE questions
  MODIFY COLUMN type ENUM('mcq','tf','match','fill') NOT NULL DEFAULT 'mcq';
```

---

## Section 2 — Backend: `/api/quiz/check` endpoint (Tier 1.1)

> **New file or append**: `sample/app/api/quiz.py`
>
> This is the forgiving-retry endpoint. It grades ONE question, does NOT end the session, and records every attempt.

```python
# sample/app/api/quiz.py  — add this to the existing router

class CheckAnswerRequest(BaseModel):
    module_id: int
    question_id: int
    user_answer: str
    attempt_number: int = 1  # frontend increments on each wrong try

@router.post("/quiz/check")
def api_check_answer(req: CheckAnswerRequest, user=Depends(get_current_user)):
    # Look up the correct answer without exposing it
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
        # On first correct attempt → worth full SM-2 quality; after retries → downgraded
        "first_attempt": req.attempt_number == 1 and is_correct,
    }
```

---

## Section 3 — Backend: modified `grade_quiz` (Tier 1.1 + 1.2)

> **File**: `sample/app/services/quiz_service.py` — REPLACE `grade_quiz` with this version.
>
> Key change: the frontend now sends `first_attempt_map` (which questions the user got on the FIRST try). Score and SM-2 quality are computed from FIRST-attempt correctness. XP is awarded accordingly.

```python
from app.services.xp_service import compute_xp, update_user_xp

def grade_quiz(
    user_id: int,
    sprint_id,
    module_id: int,
    questions: list,
    answers: dict,             # {qid: final_correct_answer}
    first_attempt_map: dict,   # {qid: bool — was first attempt correct?}
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
            "is_correct": 1,                           # by the time submit fires, all are eventually correct
            "first_attempt_correct": int(first_ok),
            "attempt_number": 1 if first_ok else 2,
            "response_time_ms": 0,
        })

    total = len(questions)
    # SM-2 quality is driven by first-attempt accuracy, not "did they eventually get there"
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

> Remember to also update `save_quiz_session` in `app/models/quiz.py` to persist `xp_earned` and each response's `first_attempt_correct` / `attempt_number`.

---

## Section 4 — Backend: `services/xp_service.py` (Tier 1.2, new file)

```python
# sample/app/services/xp_service.py
from app.core.database import get_conn

# (min_xp, title)
LEVELS = [
    (0,    "Novice Compliance Officer"),     # 新手法遵員
    (100,  "Junior Compliance Apprentice"),  # 合規見習生
    (300,  "Compliance Analyst"),            # 法遵分析師
    (700,  "Compliance Expert"),             # 合規達人
    (1500, "Compliance Master"),             # 法遵大師
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
    # +10 per first-try correct, +5 bonus per first-try correct on top,
    # +25 bonus if the whole module was perfect on first try
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

## Section 5 — Backend: `GET /api/me/level` (Tier 1.2)

> **File**: append to `sample/app/api/auth.py` or create `sample/app/api/me.py`

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

## Section 6 — Frontend CSS: shake + confetti (Tier 1.1 + 1.2)

> **File**: inside `sample/templates/index.html`'s existing `<style>` block.

```css
/* [Tier 1.1] wrong-answer shake */
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

/* [Tier 1.2] confetti — pure CSS, no libs */
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

/* [Tier 1.2] XP progress bar */
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

## Section 7 — Frontend JS: forgiving quiz retry (Tier 1.1)

> **File**: inside `sample/templates/index.html`'s existing `<script>`. Replace the current quiz option click handler.

```javascript
// [Tier 1.1] forgiving retry with per-question attempt tracking
const firstAttemptMap = {};  // { question_id: true|false }
const attemptCounts = {};    // { question_id: int }

async function handleOptionClick(questionId, optionValue, optionEl) {
  if (firstAttemptMap[questionId] !== undefined && firstAttemptMap[questionId]) {
    return; // already answered correctly; ignore
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
      attemptCounts[questionId] === 1 ? "Nailed it ✨" : "Got there — nice.",
    );
    setTimeout(() => advanceToNextQuestion(questionId, optionValue), 800);
  } else {
    optionEl.classList.add('answer-wrong');
    showMascotBubble("Not this one — try again");
    setTimeout(() => optionEl.classList.remove('answer-wrong'), 600);
    if (firstAttemptMap[questionId] === undefined) {
      firstAttemptMap[questionId] = false;
    }
  }
}

// On final submit, send first_attempt_map along with answers
async function submitQuiz() {
  const res = await fetch('/api/quiz/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sprint_id: state.sprintId,
      module_id: state.currentModule.id,
      answers: state.quizAnswers,
      first_attempt_map: firstAttemptMap,  // NEW
    }),
  });
  const data = await res.json();
  showCompletionScreen(data);   // hooks into Tier 1.2
}
```

---

## Section 8 — Frontend JS: XP progress bar + level-up (Tier 1.2)

```javascript
// [Tier 1.2] completion screen replaces the old "score only" view
function showCompletionScreen(data) {
  // data = { score, correct_first_try, total, xp_earned, total_xp, leveled_up, level_name }
  document.getElementById('quiz-screen').classList.remove('active');
  const screen = document.getElementById('completion-screen');
  screen.classList.add('active');

  screen.querySelector('.xp-delta').textContent = `+${data.xp_earned} XP`;
  screen.querySelector('.level-name').textContent = data.level_name;

  // Animate XP bar
  fetch('/api/me/level').then(r => r.json()).then(lvl => {
    screen.querySelector('.xp-bar-fill').style.width = `${lvl.progress_pct}%`;
    screen.querySelector('.xp-total').textContent = `${lvl.xp} XP`;
  });

  if (data.leveled_up) {
    showLevelUpBanner(data.level_name);
    launchConfetti();
  } else if (data.correct_first_try === data.total) {
    launchConfetti();   // perfect run also gets celebration
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

## Section 9 — Streak freeze chip on dashboard (Tier 1.3)

```javascript
// [Tier 1.3] streak flame + freeze count
async function renderStreakChip() {
  const res = await fetch('/api/dashboard');
  const data = await res.json();
  const el = document.getElementById('streak-chip');
  el.innerHTML = `
    <span class="flame">🔥</span>
    <span class="days">${data.streak} day${data.streak === 1 ? '' : 's'}</span>
    <span class="freeze" title="Streak freezes available">
      ❄️ × ${data.streak_freeze_count}
    </span>
  `;
  if (data.streak >= 7 && data.streak % 7 === 0 && data.just_unlocked_freeze) {
    showToast('Streak freeze unlocked! Miss a day and we\'ve got you covered.');
  }
}
```

> Server-side: in `app/services/dashboard_service.py`, when the streak calculation detects a missed day, check `streak_freeze_count > 0` before resetting streak to 0. If freeze is available, consume one (`-1`) and keep the streak alive.

---

## Section 10 — Tier 2.4: match-pairs and fill-blank question types

### Schema / options_json shape

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
// correct_answer column holds "50"
```

### Match-pairs render (frontend)

```javascript
// [Tier 2.4] tap pairs to match left→right
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

### Fill-blank render

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

## Section 11 — Claude Code prompt templates

Paste these into Claude Code, one at a time, in order.

### Prompt A — Tier 1.1 (forgiving retry)
```
Read app/api/quiz.py, app/services/quiz_service.py, app/models/quiz.py, and
templates/index.html's quiz screen. Then implement Duolingo-style forgiving retry:

1. Add ALTER TABLE to schema.sql for question_responses.attempt_number and
   question_responses.first_attempt_correct.
2. Add POST /api/quiz/check that returns {correct, first_attempt} for a single
   question without ending the session.
3. Modify grade_quiz to accept first_attempt_map and compute SM-2 quality from
   first-attempt accuracy, not final accuracy.
4. In index.html, replace the current option-click handler so that:
   - Wrong click = red border + shake animation + retry allowed
   - Right click = green border + advance after 0.8s
   - The frontend tracks firstAttemptMap and sends it on final submit
5. Use pure CSS for animations — no libraries.

Reference 03_samples_en.md sections 1, 2, 3, 6, 7 for concrete code.
Keep the existing code style (raw PyMySQL, no ORM, %s params).
```

### Prompt B — Tier 1.2 (XP + levels + celebration)
```
Build the XP and level system:

1. ALTER users add total_xp, quiz_sessions add xp_earned.
2. Create app/services/xp_service.py with LEVELS table (Novice → Master),
   level_for(xp), compute_xp(first_try, total), update_user_xp(user_id, delta).
3. Add GET /api/me/level returning {xp, level_name, progress_pct, next_level_xp}.
4. In grade_quiz, call compute_xp and update_user_xp, include xp_earned /
   leveled_up / level_name in the response.
5. Build a completion screen that replaces the current "score" view:
   - XP delta "+45 XP" animation
   - XP progress bar filling to current progress_pct
   - Level badge
   - CSS confetti on level-up OR perfect-first-try

Reference 03_samples_en.md sections 4, 5, 6, 8.
```

### Prompt C — Tier 2.4 (new question types)
```
Add two new question types beyond MCQ and True/False:

1. ALTER questions.type enum to add 'match' and 'fill'.
2. In app/data/loader.py, add 2 match-type questions and 2 fill-type questions
   across different modules as demo content.
3. In index.html, add renderMatchQuestion() and renderFillQuestion() functions.
   The main quiz loop should dispatch to the right renderer by question.type.
4. Match-pairs: tap left → tap right → correct pair gets green; all matched
   advances the question.
5. Fill-blank: sentence with ___, 3 choice buttons, reuse Tier 1.1's
   handleOptionClick.

Reference 03_samples_en.md section 10. Reuse the existing shake/correct CSS.
```

---

## Appendix — What to verify before you commit

- [ ] First-attempt-correct really flows into SM-2 quality (quality score drops when user had to retry)
- [ ] XP persisted across sessions (refresh browser → still see your XP)
- [ ] Confetti doesn't block the next-module button
- [ ] New question types don't break existing MCQ/TF flow
- [ ] Streak freeze actually consumes when a day is missed (test by changing system date or inserting a backdated `quiz_sessions` row)
