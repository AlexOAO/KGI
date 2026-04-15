# Project 3: 7-Minute Sprint Reader & Contextual Transition — Developer Specification

## Project Overview

Build a mobile-first, timed flashcard reader that delivers micro-learning content in focused 7-minute sprints. The reader primes the learner with metadata context before reading, enforces strict time discipline, tracks reading behavior as telemetry, and hands off seamlessly to the Quiz Engine (Project 2).

**Role in the System:**
- Receives content from the Content Generator (Project 1 / `MicroModules`)
- Passes session data to the Quiz Engine (Project 2 / `QuizSessions`)
- The `LearningJourney_Map` table is the connective tissue linking both phases

---

## UI/UX Specification

### Screen 1 — Pre-Sprint Splash

Displayed before the timer starts. Pulls metadata from the backend.

**Must display:**
- Module title (e.g., `"2026 FSC Travel Insurance Cross-Selling Guidelines"`)
- Domain tags (e.g., `#Compliance`, `#TravelInsurance`)
- Warning banner: `"You have 7 minutes to read 5 cards. A 3-question quiz immediately follows."`
- CTA button: `"Start Sprint"`

**Purpose:** Primes working memory — activates "active reading" mode before content begins.

---

### Screen 2 — Swipeable Card Reader

Mobile-first, Instagram Stories-style swipeable interface.

**Top Bar (persistent):**
- Progress indicator: `Card 2 of 5`
- Domain tag badge
- Countdown timer: `06:42` (counts down from 7:00)

**Card Body:**
- Renders `page_content_json` (text + optional image)
- Swipe left/right or tap arrow to advance
- No back-navigation once a card is passed (enforces forward reading flow)

**Timer Behavior (Visibility API):**
- Timer **pauses** when `document.visibilityState === 'hidden'` (app backgrounded, tab switched)
- `tab_switch_count` increments on each visibility loss event
- Timer **resumes** when visibility restored
- Visual indicator shown on resume: `"Welcome back. Timer resumed."`

---

### Screen 3 — Time's Up / Handoff

Triggered by either:
- Timer reaching `0:00`, OR
- User swiping past the final card

**Behavior:**
1. Screen locks immediately with CSS fade/lock animation
2. Display: `"Sprint Complete. Generating your quiz..."`
3. Backend call: generate `session_id`, write `SprintSession` record
4. Redirect to Quiz Engine (Project 2) with `session_id` as URL param or state payload

> ⚠️ The Quiz Engine UI itself is out of scope for this project. Only the handoff payload matters here.

---

## Database Schema

### Table 1: `FlashcardPages` — Content Segments

```sql
CREATE TABLE FlashcardPages (
  page_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id        UUID NOT NULL REFERENCES MicroModules(module_id) ON DELETE CASCADE,
  sequence_number  INTEGER NOT NULL,          -- 1, 2, 3... ordering within module
  page_content_json JSONB NOT NULL,           -- { "text": "...", "image_url": "..." }
  created_at       TIMESTAMPTZ DEFAULT now(),

  UNIQUE (module_id, sequence_number)         -- no duplicate card positions per module
);
```

**`page_content_json` shape:**
```json
{
  "text": "Under FSC 2026 guidelines, cross-selling travel insurance requires...",
  "image_url": "https://cdn.example.com/assets/chart_travel_2026.png"
}
```

---

### Table 2: `SprintSessions` — Reading Behavior Telemetry

```sql
CREATE TABLE SprintSessions (
  sprint_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id           UUID NOT NULL REFERENCES Users(user_id),
  module_id          UUID NOT NULL REFERENCES MicroModules(module_id),
  start_timestamp    TIMESTAMPTZ NOT NULL,
  end_timestamp      TIMESTAMPTZ,
  tab_switch_count   INTEGER NOT NULL DEFAULT 0,
  completion_status  VARCHAR(20) NOT NULL
                       CHECK (completion_status IN (
                         'finished_early',  -- user swiped all cards before timer expired
                         'timed_out',       -- timer hit 0:00
                         'abandoned'        -- user closed/navigated away
                       )),
  created_at         TIMESTAMPTZ DEFAULT now()
);
```

---

### Table 3: `LearningJourney_Map` — Connective Tissue

Links the reading phase (P3) directly to the quiz phase (P2) for downstream AI analysis.

```sql
CREATE TABLE LearningJourney_Map (
  journey_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sprint_id        UUID NOT NULL REFERENCES SprintSessions(sprint_id),
  quiz_session_id  UUID REFERENCES QuizSessions(quiz_session_id),  -- nullable until quiz completes
  created_at       TIMESTAMPTZ DEFAULT now(),

  UNIQUE (sprint_id)   -- one sprint maps to at most one quiz session
);
```

> **Why this table exists:** Enables future ML queries like:
> - "Do agents who switch tabs more during reading score lower on quizzes?"
> - "Does reading completion status predict quiz accuracy?"

---

## API Endpoints

### `GET /modules/:module_id/sprint`
Returns all flashcard pages + module metadata for the Pre-Sprint splash and reader.

**Response:**
```json
{
  "module_id": "uuid",
  "title": "2026 FSC Travel Insurance Cross-Selling Guidelines",
  "domain_tags": ["#Compliance", "#TravelInsurance"],
  "duration_seconds": 420,
  "card_count": 5,
  "pages": [
    { "page_id": "uuid", "sequence_number": 1, "page_content_json": { "text": "..." } },
    { "page_id": "uuid", "sequence_number": 2, "page_content_json": { "text": "...", "image_url": "..." } }
  ]
}
```

---

### `POST /sprint-sessions`
Creates a new sprint session when user taps "Start Sprint".

**Request:**
```json
{
  "agent_id": "uuid",
  "module_id": "uuid"
}
```

**Response:**
```json
{
  "sprint_id": "uuid",
  "start_timestamp": "2026-04-14T09:00:00Z"
}
```

---

### `PATCH /sprint-sessions/:sprint_id`
Updates session on completion or timeout. Also creates the `LearningJourney_Map` record and returns the `session_id` for handoff to Quiz Engine.

**Request:**
```json
{
  "end_timestamp": "2026-04-14T09:06:42Z",
  "tab_switch_count": 2,
  "completion_status": "finished_early"
}
```

**Response:**
```json
{
  "sprint_id": "uuid",
  "journey_id": "uuid",
  "handoff_session_id": "uuid",
  "redirect_url": "/quiz?session_id=uuid"
}
```

---

### `PATCH /sprint-sessions/:sprint_id/tab-switch`
Lightweight endpoint called each time `visibilitychange` fires.

**Request:**
```json
{ "tab_switch_count": 3 }
```

---

## Frontend State Machine

```
[IDLE]
  │
  ▼ user lands on module
[PRE_SPRINT]   ← fetch /modules/:id/sprint
  │
  ▼ user taps "Start Sprint" → POST /sprint-sessions
[READING]
  │  ┌─ visibilitychange → PATCH tab_switch_count
  │  ├─ timer tick (pauses when hidden)
  │  └─ swipe card → update local progress state
  │
  ▼ timer = 0 OR last card swiped
[LOCKED]       ← PATCH /sprint-sessions/:id (completion)
  │
  ▼ journey_id received
[HANDOFF]      ← redirect to Quiz Engine with session_id
```

---

## Timer Implementation Notes

```javascript
// Visibility API integration
let timerPaused = false;
let tabSwitchCount = 0;

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    timerPaused = true;
    tabSwitchCount++;
    patchTabSwitch(sprintId, tabSwitchCount); // fire-and-forget PATCH
  } else {
    timerPaused = false;
    showResumeToast("Welcome back. Timer resumed.");
  }
});

// Timer tick — only decrements when not paused
const tick = setInterval(() => {
  if (!timerPaused && secondsRemaining > 0) {
    secondsRemaining--;
    updateTimerDisplay(secondsRemaining);
  } else if (secondsRemaining === 0) {
    triggerHandoff('timed_out');
  }
}, 1000);
```

---

## Handoff Payload to Quiz Engine (Project 2)

When redirecting, pass via URL param or React/navigation state:

```json
{
  "session_id": "uuid",           // journey_id for cross-referencing
  "sprint_id": "uuid",
  "module_id": "uuid",
  "agent_id": "uuid",
  "completion_status": "finished_early",
  "tab_switch_count": 2
}
```

The Quiz Engine uses `session_id` to write back `quiz_session_id` into `LearningJourney_Map` upon quiz completion.

---

## Non-Functional Requirements

- Timer accuracy: ±100ms drift acceptable; use `performance.now()` not `Date.now()` for tick calculation
- Card swipe animation: 60fps, CSS transform-based (no JS animation libraries required)
- Session write latency: `PATCH /sprint-sessions` must complete in < 500ms to avoid blocking redirect
- All timestamps stored as `TIMESTAMPTZ` in UTC

---

## Out of Scope

- Quiz Engine UI (Project 2) — only the handoff payload format matters here
- Content authoring / module creation (Project 1)
- Offline mode / PWA caching
- Admin analytics dashboard
