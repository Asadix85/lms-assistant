from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """تنظیمات برنامه، خوانده‌شده از .env"""

    # === LMS Credentials ===
    lms_username: str = ""
    lms_password: str = ""

    # === LMS URLs ===
    lms_base_url: str = "https://lms4.ui.ac.ir"

    # === Quera Credentials ===
    quera_username: str = ""
    quera_password: str = ""

    # === Quera URLs ===
    quera_base_url: str = "https://quera.org"

    # === Database ===
    db_path: Path = Path("./data/lms.db")

    # === Logging ===
    log_level: str = "INFO"
    log_file: Path = Path("./logs/lms-assistant.log")

    # === Sync ===
    request_timeout: int = 30
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()