"""ثابت‌های پروژه."""

LOGIN_PATH = "/login"
LOGOUT_PATH = "/logout"
DASHBOARD_PATH = "/pages/nodemain"
COURSES_PATH = "/pages/nodeclass"
CALENDAR_PATH = "/pages/calendar"
NEWS_PATH = "/pages/news"
ARCHIVE_PATH = "/pages/archive-group/"

GROUP_URL_PATTERN = r"/group/(\d+)"
COURSE_CODE_PATTERN = r"کد درس\s*:\s*([\d\-]+)"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DB_SCHEMA_FILE = "schema.sql"