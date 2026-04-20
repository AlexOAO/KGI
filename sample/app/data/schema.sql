-- Learning Tables
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('learner','admin') NOT NULL DEFAULT 'learner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    topic_tag VARCHAR(128),
    source_document VARCHAR(255) DEFAULT NULL,
    duration_seconds INT NOT NULL DEFAULT 420,
    difficulty_level TINYINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS flashcard_pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    sequence_number INT NOT NULL,
    page_text LONGTEXT,
    image_url VARCHAR(512),
    UNIQUE KEY uq_module_seq (module_id, sequence_number),
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    type ENUM('mcq','tf') NOT NULL DEFAULT 'mcq',
    prompt TEXT NOT NULL,
    options_json JSON,
    correct_answer VARCHAR(255) NOT NULL,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sprint_sessions (
    sprint_id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id INT NOT NULL,
    module_id INT NOT NULL,
    start_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_ts TIMESTAMP NULL,
    tab_switch_count INT NOT NULL DEFAULT 0,
    completion_status ENUM('finished_early','timed_out','abandoned') NOT NULL DEFAULT 'abandoned',
    FOREIGN KEY (agent_id) REFERENCES users(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quiz_sessions (
    quiz_session_id INT AUTO_INCREMENT PRIMARY KEY,
    sprint_id INT,
    user_id INT NOT NULL,
    module_id INT NOT NULL,
    score FLOAT NOT NULL DEFAULT 0,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sprint_id) REFERENCES sprint_sessions(sprint_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS question_responses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quiz_session_id INT NOT NULL,
    question_id INT NOT NULL,
    user_answer VARCHAR(255),
    is_correct TINYINT(1) NOT NULL DEFAULT 0,
    response_time_ms INT NOT NULL DEFAULT 0,
    FOREIGN KEY (quiz_session_id) REFERENCES quiz_sessions(quiz_session_id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS learning_journey_map (
    journey_id INT AUTO_INCREMENT PRIMARY KEY,
    sprint_id INT NOT NULL,
    quiz_session_id INT,
    UNIQUE KEY uq_sprint (sprint_id),
    FOREIGN KEY (sprint_id) REFERENCES sprint_sessions(sprint_id),
    FOREIGN KEY (quiz_session_id) REFERENCES quiz_sessions(quiz_session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS review_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    concept_tag VARCHAR(128) NOT NULL,
    next_review_at DATE NOT NULL,
    interval_days INT NOT NULL DEFAULT 1,
    ease_factor FLOAT NOT NULL DEFAULT 2.5,
    repetitions INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_user_concept (user_id, concept_tag),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Reward & Exchange Tables

CREATE TABLE IF NOT EXISTS level_up_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    level_reached TINYINT NOT NULL,
    reward_type ENUM('kgi_points','learning_hours') NOT NULL,
    reward_amount DECIMAL(10,2) NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_level (user_id, level_reached),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reward_catalog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category ENUM('gift','voucher','performance_hours','other') NOT NULL DEFAULT 'gift',
    points_cost INT NOT NULL,
    stock INT DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reward_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    txn_type ENUM(
        'earn_points_levelup','earn_hours_levelup',
        'convert_hours_to_points','convert_points_to_hours',
        'redeem_catalog','admin_grant_points','admin_grant_hours'
    ) NOT NULL,
    points_delta INT NOT NULL DEFAULT 0,
    hours_delta DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    catalog_item_id INT DEFAULT NULL,
    note VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (catalog_item_id) REFERENCES reward_catalog(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Compliance Tables
CREATE TABLE IF NOT EXISTS comp_penalties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(64),
    institution VARCHAR(128),
    title TEXT,
    date VARCHAR(32),
    content LONGTEXT,
    FULLTEXT KEY ft_penalty (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comp_regulations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(64),
    title TEXT,
    date VARCHAR(32),
    content LONGTEXT,
    FULLTEXT KEY ft_regulation (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comp_national_laws (
    id INT AUTO_INCREMENT PRIMARY KEY,
    law_name VARCHAR(255),
    law_level VARCHAR(64),
    law_url VARCHAR(512),
    article_no VARCHAR(64),
    article_content LONGTEXT,
    article_type VARCHAR(64),
    FULLTEXT KEY ft_national (law_name, article_content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comp_fsc_directives (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution VARCHAR(128),
    category VARCHAR(64),
    law_system VARCHAR(128),
    publish_date VARCHAR(32),
    document_no VARCHAR(255),
    change_type VARCHAR(64),
    law_status VARCHAR(64),
    effective_date VARCHAR(32),
    law_name VARCHAR(255),
    subject TEXT,
    content LONGTEXT,
    FULLTEXT KEY ft_fsc (subject, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
