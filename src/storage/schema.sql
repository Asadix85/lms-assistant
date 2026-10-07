-- LMS Assistant - Database Schema

-- جدول دروس
CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
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
    last_seen_at TEXT NOT NULL
);

-- جدول اعضای درس
CREATE TABLE IF NOT EXISTS members (
    id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    name TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    member_type TEXT NOT NULL DEFAULT 'unknown',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY (id, course_id),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_members_course ON members(course_id);
CREATE INDEX IF NOT EXISTS idx_members_type ON members(member_type);
-- جدول محتوا (PDF, ZIP, ...)
CREATE TABLE IF NOT EXISTS contents (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    is_new INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- جدول رویدادها (جلسات آنلاین، آزمون‌ها)
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
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
    last_seen_at TEXT NOT NULL
);

-- جدول تغییرات (لاگ)
CREATE TABLE IF NOT EXISTS changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    course_id TEXT,
    data TEXT,
    detected_at TEXT NOT NULL
);

-- جدول تنظیمات
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL
);

-- ایندکس‌ها
CREATE INDEX IF NOT EXISTS idx_courses_domain ON courses(domain);
CREATE INDEX IF NOT EXISTS idx_courses_group_id ON courses(group_id);
CREATE INDEX IF NOT EXISTS idx_contents_course ON contents(course_id);
CREATE INDEX IF NOT EXISTS idx_contents_is_new ON contents(is_new);
CREATE INDEX IF NOT EXISTS idx_events_course ON events(course_id);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_at);
CREATE INDEX IF NOT EXISTS idx_changes_detected ON changes(detected_at);

-- جدول پست‌های wall
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
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
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- جدول تکالیف
CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
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
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- ایندکس‌ها
CREATE INDEX IF NOT EXISTS idx_posts_course ON posts(course_id);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_deadline ON assignments(deadline);

-- ============================================================
-- Quera Tables
-- ============================================================

-- جدول تمرین‌های Quera
CREATE TABLE IF NOT EXISTS quera_assignments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    course_name TEXT,
    finish_time TEXT,
    problems_json TEXT,
    problems_count INTEGER NOT NULL DEFAULT 0,
    submitted_count INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quera_assignments_finish ON quera_assignments(finish_time);
CREATE INDEX IF NOT EXISTS idx_quera_assignments_is_new ON quera_assignments(is_new);