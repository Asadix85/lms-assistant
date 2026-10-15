"""مدیریت ذخیره‌ی امن credentials با keyring."""

from loguru import logger

try:
    import keyring
    import keyring.errors
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring نصب نیست — ذخیره‌ی امن غیرفعال")


SERVICE_NAME = "lms_assistant"


class CredentialsManager:
    """ذخیره و بازیابی credentials با Windows Credential Manager."""

    # === Helpers ===

    @staticmethod
    def _set(key: str, value: str) -> bool:
        """ذخیره‌ی یه کلید (internal)."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.set_password(SERVICE_NAME, key, value)
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره {key}: {e}")
            return False

    @staticmethod
    def _get(key: str) -> str | None:
        """بازیابی یه کلید (internal)."""
        if not KEYRING_AVAILABLE:
            return None
        try:
            return keyring.get_password(SERVICE_NAME, key)
        except Exception as e:
            logger.error(f"خطا در بازیابی {key}: {e}")
            return None

    @staticmethod
    def _delete(key: str) -> bool:
        """حذف یه کلید (internal)."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.delete_password(SERVICE_NAME, key)
            return True
        except keyring.errors.PasswordDeleteError:
            return True  # credential وجود نداشت
        except Exception as e:
            logger.warning(f"خطا در حذف {key}: {e}")
            return False

    # === LMS ===

    @staticmethod
    def save_lms(username: str, password: str) -> bool:
        """ذخیره‌ی LMS credentials."""
        ok1 = CredentialsManager._set("lms_username", username)
        ok2 = CredentialsManager._set("lms_password", password)
        if ok1 and ok2:
            logger.info("✅ LMS credentials ذخیره شد")
        return ok1 and ok2

    @staticmethod
    def get_lms() -> tuple[str, str] | None:
        """بازیابی LMS credentials."""
        username = CredentialsManager._get("lms_username")
        password = CredentialsManager._get("lms_password")
        if username and password:
            return username, password
        return None

    @staticmethod
    def delete_lms() -> bool:
        """حذف LMS credentials."""
        CredentialsManager._delete("lms_username")
        CredentialsManager._delete("lms_password")
        logger.info("✅ LMS credentials حذف شد")
        return True

    # === Quera ===

    @staticmethod
    def save_quera(username: str, password: str) -> bool:
        """ذخیره‌ی Quera credentials."""
        ok1 = CredentialsManager._set("quera_username", username)
        ok2 = CredentialsManager._set("quera_password", password)
        if ok1 and ok2:
            logger.info("✅ Quera credentials ذخیره شد")
        return ok1 and ok2

    @staticmethod
    def get_quera() -> tuple[str, str] | None:
        """بازیابی Quera credentials."""
        username = CredentialsManager._get("quera_username")
        password = CredentialsManager._get("quera_password")
        if username and password:
            return username, password
        return None

    @staticmethod
    def delete_quera() -> bool:
        """حذف Quera credentials."""
        CredentialsManager._delete("quera_username")
        CredentialsManager._delete("quera_password")
        logger.info("✅ Quera credentials حذف شد")
        return True

    # === Telegram ===

    @staticmethod
    def save_telegram_chat_id(chat_id: str) -> bool:
        """ذخیره‌ی Telegram Chat ID."""
        ok = CredentialsManager._set("telegram_chat_id", chat_id)
        if ok:
            logger.info(f"✅ Telegram Chat ID ذخیره شد: {chat_id}")
        return ok

    @staticmethod
    def get_telegram_chat_id() -> str | None:
        """بازیابی Telegram Chat ID."""
        return CredentialsManager._get("telegram_chat_id")

    @staticmethod
    def delete_telegram_chat_id() -> bool:
        """حذف Telegram Chat ID."""
        CredentialsManager._delete("telegram_chat_id")
        logger.info("✅ Telegram Chat ID حذف شد")
        return True

    # === Helpers ===

    @staticmethod
    def has_lms() -> bool:
        return CredentialsManager.get_lms() is not None

    @staticmethod
    def has_quera() -> bool:
        return CredentialsManager.get_quera() is not None

    @staticmethod
    def has_telegram() -> bool:
        return CredentialsManager.get_telegram_chat_id() is not None

    @staticmethod
    def clear_all() -> None:
        """حذف همه‌ی credentials."""
        CredentialsManager.delete_lms()
        CredentialsManager.delete_quera()
        CredentialsManager.delete_telegram_chat_id()