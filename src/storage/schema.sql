-- LMS Assistant - Database Schema (multi-tenant)

-- ============================================================
-- Identity
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    lms_username TEXT NOT NULL UNIQUE,
    lms_user_id TEXT,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_lms_username ON users(lms_username);

CREATE TABLE IF NOT EXISTS web_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_web_sessions_user ON web_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_web_sessions_token ON web_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_web_sessions_expires ON web_sessions(expires_at);

CREATE TABLE IF NOT EXISTS user_secrets (
    user_id TEXT PRIMARY KEY,
    lms_password_enc TEXT,
    quera_username TEXT,
    quera_password_enc TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- LMS data (scoped by user_id)
-- ============================================================

CREATE TABLE IF NOT EXISTS courses (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    group_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    nodeg_url TEXT,
    teacher TEXT,
    teacher_photo_url TEXT,
    code TEXT,
    term TEXT,
    status TEXT NOT NULL DEFAULT 'unknown',
    is_new INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_courses_user ON courses(user_id);
CREATE INDEX IF NOT EXISTS idx_courses_domain ON courses(domain);
CREATE INDEX IF NOT EXISTS idx_courses_group_id ON courses(group_id);

CREATE TABLE IF NOT EXISTS members (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    name TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    member_type TEXT NOT NULL DEFAULT 'unknown',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_members_user ON members(user_id);
CREATE INDEX IF NOT EXISTS idx_members_course ON members(course_id);
CREATE INDEX IF NOT EXISTS idx_members_type ON members(member_type);

CREATE TABLE IF NOT EXISTS contents (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    is_new INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_contents_user ON contents(user_id);
CREATE INDEX IF NOT EXISTS idx_contents_course ON contents(course_id);
CREATE INDEX IF NOT EXISTS idx_contents_is_new ON contents(is_new);

CREATE TABLE IF NOT EXISTS events (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    course_id TEXT,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    url TEXT,
    room_token TEXT,
    start_at TEXT,
    end_at TEXT,
    description TEXT,
    is_new INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_course ON events(course_id);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_at);

CREATE TABLE IF NOT EXISTS changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    course_id TEXT,
    data TEXT,
    detected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_changes_user ON changes(user_id);
CREATE INDEX IF NOT EXISTS idx_changes_detected ON changes(detected_at);

CREATE TABLE IF NOT EXISTS settings (
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);

CREATE TABLE IF NOT EXISTS posts (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    author TEXT NOT NULL,
    author_id TEXT,
    text TEXT NOT NULL,
    posted_at TEXT,
    posted_at_jalali TEXT,
    post_url TEXT,
    is_new INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_course ON posts(course_id);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);

CREATE TABLE IF NOT EXISTS assignments (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    post_id TEXT,
    start_at TEXT,
    deadline TEXT,
    start_at_jalali TEXT,
    deadline_jalali TEXT,
    submit_url TEXT,
    view_url TEXT,
    response_count INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 0,
    is_manual INTEGER NOT NULL DEFAULT 0,
    is_done INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_user ON assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_deadline ON assignments(deadline);

CREATE TABLE IF NOT EXISTS quera_assignments (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    course_name TEXT,
    finish_time TEXT,
    problems_json TEXT,
    problems_count INTEGER NOT NULL DEFAULT 0,
    submitted_count INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 0,
    is_manual INTEGER NOT NULL DEFAULT 0,
    is_done INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_quera_assignments_user ON quera_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_quera_assignments_finish ON quera_assignments(finish_time);

CREATE TABLE IF NOT EXISTS quera_courses (
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    teacher TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    assignments_count INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_quera_courses_user ON quera_courses(user_id);

CREATE TABLE IF NOT EXISTS course_schedules (
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    course_code TEXT,
    sessions_json TEXT,
    raw_text TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (user_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_course_schedules_user ON course_schedules(user_id);
