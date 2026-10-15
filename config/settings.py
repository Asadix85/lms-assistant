"""تنظیمات برنامه، خوانده‌شده از .env"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.paths import get_env_path


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

    # === Telegram Bot ===
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_proxy_url: str = ""

    # === Database ===
    db_path: Path = Path("./data/lms.db")

    # === Logging ===
    log_level: str = "INFO"
    log_file: Path = Path("./logs/lms-assistant.log")

    # === Sync ===
    request_timeout: int = 30
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=str(get_env_path()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()