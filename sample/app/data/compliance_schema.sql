-- compliance_schema.sql: FTS5 content-tables for compliance data

-- 1. Penalties (裁罰)
CREATE TABLE IF NOT EXISTS compliance_penalties (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT,
    institution   TEXT,
    title         TEXT,
    issued_date   TEXT,
    content       TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS compliance_penalties_fts USING fts5(
    category,
    institution,
    title,
    issued_date   UNINDEXED,
    content,
    content       = compliance_penalties,
    content_rowid = id,
    tokenize      = 'trigram'
);
CREATE TRIGGER IF NOT EXISTS compliance_penalties_ai
AFTER INSERT ON compliance_penalties BEGIN
    INSERT INTO compliance_penalties_fts(rowid, category, institution, title, issued_date, content)
    VALUES (new.id, new.category, new.institution, new.title, new.issued_date, new.content);
END;

-- 2. Regulations (法規)
CREATE TABLE IF NOT EXISTS compliance_regulations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT,
    title       TEXT,
    issued_date TEXT,
    content     TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS compliance_regulations_fts USING fts5(
    category,
    title,
    issued_date UNINDEXED,
    content,
    content       = compliance_regulations,
    content_rowid = id,
    tokenize      = 'trigram'
);
CREATE TRIGGER IF NOT EXISTS compliance_regulations_ai
AFTER INSERT ON compliance_regulations BEGIN
    INSERT INTO compliance_regulations_fts(rowid, category, title, issued_date, content)
    VALUES (new.id, new.category, new.title, new.issued_date, new.content);
END;

-- 3. National Laws (全國法規, ArticleType='A' only)
CREATE TABLE IF NOT EXISTS compliance_national_laws (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    law_name        TEXT,
    law_level       TEXT,
    law_url         TEXT,
    article_no      TEXT,
    article_content TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS compliance_national_laws_fts USING fts5(
    law_name,
    law_level       UNINDEXED,
    law_url         UNINDEXED,
    article_no,
    article_content,
    content       = compliance_national_laws,
    content_rowid = id,
    tokenize      = 'trigram'
);
CREATE TRIGGER IF NOT EXISTS compliance_national_laws_ai
AFTER INSERT ON compliance_national_laws BEGIN
    INSERT INTO compliance_national_laws_fts(rowid, law_name, law_level, law_url, article_no, article_content)
    VALUES (new.id, new.law_name, new.law_level, new.law_url, new.article_no, new.article_content);
END;

-- 4. FSC Regulations (主管法規)
CREATE TABLE IF NOT EXISTS compliance_fsc_regs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    institution    TEXT,
    reg_category   TEXT,
    reg_name       TEXT,
    purpose        TEXT,
    effective_date TEXT,
    amendment_date TEXT,
    change_type    TEXT,
    content        TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS compliance_fsc_regs_fts USING fts5(
    institution,
    reg_category,
    reg_name,
    purpose,
    effective_date UNINDEXED,
    amendment_date UNINDEXED,
    change_type    UNINDEXED,
    content,
    content       = compliance_fsc_regs,
    content_rowid = id,
    tokenize      = 'trigram'
);
CREATE TRIGGER IF NOT EXISTS compliance_fsc_regs_ai
AFTER INSERT ON compliance_fsc_regs BEGIN
    INSERT INTO compliance_fsc_regs_fts(rowid, institution, reg_category, reg_name, purpose,
                                         effective_date, amendment_date, change_type, content)
    VALUES (new.id, new.institution, new.reg_category, new.reg_name, new.purpose,
            new.effective_date, new.amendment_date, new.change_type, new.content);
END;

-- 5. Lazy-load guard
CREATE TABLE IF NOT EXISTS compliance_load_status (
    table_name   TEXT PRIMARY KEY,
    record_count INTEGER,
    loaded_at    TEXT
);
