# Micro-Learning Application — Developer Specification

## Project Overview

Build a mobile-first micro-learning platform for financial services agents and internal employees. The system leverages spaced repetition and reinforcement learning algorithms to combat the Forgetting Curve, delivering bite-sized training modules during idle moments throughout the workday.

**Target Users:**
- Customer-facing sales agents (field-based, mobile-heavy)
- Internal employees (developers, operations staff)

**Core Problem:** Traditional training (60-min e-learning videos, 50-page PDFs, 2-hour webinars) causes cognitive overload and rapid knowledge decay (~80% forgotten within 5 days without reinforcement).

---

## Key Product Requirements

### 1. Content Delivery — Micro-Modules

- Each learning module: **≤ 7 minutes** to complete
- Module types: interactive scenarios, short videos, flashcards, quick reads
- Topic domains: FSC regulatory compliance, insurance product knowledge, cross-selling frameworks, internal tooling
- Designed for fragmented attention: commute, waiting rooms, work transitions
- No forced sequential progression; users can pick available modules

### 2. Assessment — Self-Tests

- Each module ends with a quick self-test (3–5 questions)
- Question types: multiple choice, scenario-based, true/false
- Results logged immediately: score, response time per question, accuracy
- No grade gates — assessments are diagnostic, not pass/fail blockers

### 3. Spaced Repetition Engine

Implement a spaced repetition scheduler based on user performance data.

**Algorithm Logic:**
```
Day 1  → User completes module + self-test
Day 3  → System pushes recall quiz (basic retrieval)
Day 10 → System pushes harder scenario-based quiz
Day 21 → Final reinforcement nudge (if needed)
```

- Intervals are dynamic: strong performance → longer interval; weak performance → shorter interval
- Use a modified SM-2 algorithm or equivalent
- Each topic/concept tracked independently per user

**Data points logged per interaction:**
- `user_id`
- `module_id`
- `concept_tags[]`
- `score` (0–100)
- `response_time_ms`
- `accuracy_rate`
- `timestamp`
- `next_review_date` (calculated by scheduler)

### 4. Adaptive Push Notifications

- System sends push notification when `next_review_date` is reached
- Notification content: short scenario question or prompt (2-minute recall quiz)
- Notification suppressed during: calendar-blocked hours, user-defined quiet periods
- Deep link directly to the recall quiz on tap

### 5. User Performance Dashboard

Each user sees:
- Modules completed
- Current mastery level per topic (e.g., "Term Life: Strong", "ILP Regulations: Needs Review")
- Upcoming review schedule
- Streak / engagement metrics

Admin/manager sees:
- Team-wide knowledge gap heatmaps
- Compliance module completion rates
- Individual progress reports

---

## Technical Architecture

### Stack (Recommended)

| Layer | Technology |
|---|---|
| Mobile Frontend | React Native (iOS + Android) |
| Web Admin Panel | React + TypeScript |
| Backend API | Node.js / Express or FastAPI (Python) |
| Database | PostgreSQL (structured data) + Redis (session/queue) |
| Push Notifications | Firebase Cloud Messaging (FCM) |
| ML / Scheduler | Python service (spaced repetition logic) |
| Auth | JWT + OAuth2 (SSO integration ready) |

### Core Data Models

```sql
-- Users
users (id, name, role, department, created_at, settings_json)

-- Content
modules (id, title, topic_tag, duration_seconds, content_url, difficulty_level)
questions (id, module_id, type, prompt, options_json, correct_answer)

-- Learning Records
attempts (id, user_id, module_id, score, accuracy, duration_ms, completed_at)
question_responses (id, attempt_id, question_id, user_answer, is_correct, response_time_ms)

-- Spaced Repetition Scheduler
review_schedule (id, user_id, concept_tag, next_review_at, interval_days, ease_factor, repetitions)
```

### API Endpoints (MVP)

```
POST   /auth/login
GET    /modules             → list available modules for user
GET    /modules/:id         → module content
POST   /attempts            → submit completed attempt + answers
GET    /users/:id/dashboard → user stats + upcoming reviews
GET    /users/:id/queue     → due recall quizzes
POST   /notifications/schedule → trigger push for due reviews (internal cron)
GET    /admin/team-report   → manager analytics view
```

---

## Spaced Repetition Algorithm Detail

Based on SM-2. Per `(user_id, concept_tag)` pair:

```python
def calculate_next_interval(repetitions, ease_factor, quality):
    """
    quality: 0-5 (0=total blackout, 5=perfect recall)
    """
    if quality < 3:
        repetitions = 0
        interval = 1
    elif repetitions == 0:
        interval = 1
    elif repetitions == 1:
        interval = 3
    else:
        interval = round(interval * ease_factor)

    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    repetitions += 1

    return interval, ease_factor, repetitions
```

Map quiz accuracy → quality score:
- 90–100% → quality 5
- 75–89% → quality 4
- 60–74% → quality 3
- 40–59% → quality 2
- < 40% → quality 0–1

---

## MVP Scope (Phase 1)

**In Scope:**
- [ ] User auth (login, JWT)
- [ ] Module browsing + 7-min content player
- [ ] Self-test after each module
- [ ] Basic spaced repetition scheduler (SM-2)
- [ ] Push notification for due reviews
- [ ] Personal dashboard (mastery per topic, streak)

**Out of Scope (Phase 2+):**
- Manager/admin analytics panel
- AI-generated content
- Live leaderboards
- LMS/HRIS integration
- Offline mode

---

## Non-Functional Requirements

- **Performance:** Module load time < 2s on 4G
- **Availability:** 99.5% uptime SLA
- **Security:** All user learning data encrypted at rest; PDPA compliant (Taiwan)
- **Scalability:** Support up to 10,000 concurrent users
- **Localization:** Traditional Chinese (zh-TW) + English

---

## Regulatory & Compliance Notes

- Module completion records must be audit-log immutable (for FSC compliance reporting)
- Compliance-related modules require mandatory completion tracking
- Do not allow users to skip compliance modules marked `required: true`
- Retain completion records for minimum 5 years

---

## File Structure (Suggested)

```
/
├── mobile/              # React Native app
│   ├── src/
│   │   ├── screens/     # Home, Module, Quiz, Dashboard
│   │   ├── components/
│   │   ├── services/    # API calls
│   │   └── utils/       # spaced repetition helpers
├── backend/
│   ├── api/             # Express/FastAPI routes
│   ├── models/          # DB models
│   ├── scheduler/       # Spaced repetition engine (Python)
│   └── notifications/   # FCM integration
├── admin/               # React web panel
└── docs/
    └── microlearning_app_spec.md  # This file
```

---

## Open Questions for Product Team

1. Will content be authored internally or sourced from a third-party LMS?
2. Is SSO (e.g., Azure AD / Google Workspace) required at launch?
3. What is the target device split (iOS vs Android)?
4. Are agents expected to use personal devices or company-issued phones?
5. Should recall quizzes count toward any formal compliance record?
