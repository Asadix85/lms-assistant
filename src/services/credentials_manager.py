"""مدیریت ذخیره‌ی امن credentials با keyring."""

from loguru import logger

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring نصب نیست — ذخیره‌ی امن غیرفعال")


SERVICE_NAME = "lms_assistant"


class CredentialsManager:
    """ذخیره و بازیابی credentials با Windows Credential Manager."""

    # === LMS ===

    @staticmethod
    def save_lms(username: str, password: str) -> bool:
        """ذخیره‌ی LMS credentials."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.set_password(SERVICE_NAME, "lms_username", username)
            keyring.set_password(SERVICE_NAME, "lms_password", password)
            logger.info("✅ LMS credentials ذخیره شد")
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره LMS: {e}")
            return False

    @staticmethod
    def get_lms() -> tuple[str, str] | None:
        """بازیابی LMS credentials."""
        if not KEYRING_AVAILABLE:
            return None
        try:
            username = keyring.get_password(SERVICE_NAME, "lms_username")
            password = keyring.get_password(SERVICE_NAME, "lms_password")
            if username and password:
                return username, password
            return None
        except Exception as e:
            logger.error(f"خطا در بازیابی LMS: {e}")
            return None

    @staticmethod
    def delete_lms() -> bool:
        """حذف LMS credentials."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.delete_password(SERVICE_NAME, "lms_username")
            keyring.delete_password(SERVICE_NAME, "lms_password")
            logger.info("✅ LMS credentials حذف شد")
            return True
        except Exception as e:
            logger.warning(f"خطا در حذف LMS: {e}")
            return False

    # === Quera ===

    @staticmethod
    def save_quera(username: str, password: str) -> bool:
        """ذخیره‌ی Quera credentials."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.set_password(SERVICE_NAME, "quera_username", username)
            keyring.set_password(SERVICE_NAME, "quera_password", password)
            logger.info("✅ Quera credentials ذخیره شد")
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره Quera: {e}")
            return False

    @staticmethod
    def get_quera() -> tuple[str, str] | None:
        """بازیابی Quera credentials."""
        if not KEYRING_AVAILABLE:
            return None
        try:
            username = keyring.get_password(SERVICE_NAME, "quera_username")
            password = keyring.get_password(SERVICE_NAME, "quera_password")
            if username and password:
                return username, password
            return None
        except Exception as e:
            logger.error(f"خطا در بازیابی Quera: {e}")
            return None

    @staticmethod
    def delete_quera() -> bool:
        """حذف Quera credentials."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.delete_password(SERVICE_NAME, "quera_username")
            keyring.delete_password(SERVICE_NAME, "quera_password")
            logger.info("✅ Quera credentials حذف شد")
            return True
        except Exception as e:
            logger.warning(f"خطا در حذف Quera: {e}")
            return False

    # === Helpers ===

    @staticmethod
    def has_lms() -> bool:
        """آیا LMS credentials ذخیره شده؟"""
        return CredentialsManager.get_lms() is not None

    @staticmethod
    def has_quera() -> bool:
        """آیا Quera credentials ذخیره شده؟"""
        return CredentialsManager.get_quera() is not None

    @staticmethod
    def clear_all() -> None:
        """حذف همه‌ی credentials."""
        CredentialsManager.delete_lms()
        CredentialsManager.delete_quera()