CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'learner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    topic_tag TEXT NOT NULL,
    duration_seconds INTEGER DEFAULT 420,
    difficulty_level TEXT DEFAULT 'intermediate'
);

CREATE TABLE IF NOT EXISTS flashcard_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    image_url TEXT,
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'multiple_choice',
    options_json TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

CREATE TABLE IF NOT EXISTS sprint_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    start_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_timestamp TIMESTAMP,
    tab_switch_count INTEGER DEFAULT 0,
    completion_status TEXT DEFAULT 'in_progress',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    sprint_session_id INTEGER,
    score INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (module_id) REFERENCES modules(id),
    FOREIGN KEY (sprint_session_id) REFERENCES sprint_sessions(id)
);

CREATE TABLE IF NOT EXISTS question_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    user_answer TEXT,
    is_correct INTEGER DEFAULT 0,
    response_time_ms INTEGER DEFAULT 0,
    FOREIGN KEY (attempt_id) REFERENCES attempts(id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS review_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    concept_tag TEXT NOT NULL,
    next_review_at TIMESTAMP NOT NULL,
    interval_days REAL DEFAULT 1.0,
    ease_factor REAL DEFAULT 2.5,
    repetitions INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

CREATE TABLE IF NOT EXISTS learning_journey_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_session_id INTEGER,
    quiz_session_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sprint_session_id) REFERENCES sprint_sessions(id),
    FOREIGN KEY (quiz_session_id) REFERENCES attempts(id)
);
