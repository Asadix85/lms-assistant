"""Provider متمرکز برای credentials (keyring + .env)."""

from dataclasses import dataclass

from loguru import logger

from config.settings import settings
from src.services.credentials_manager import CredentialsManager


@dataclass
class Credentials:
    """Credentials LMS + Quera."""
    lms_username: str = ""
    lms_password: str = ""
    quera_username: str = ""
    quera_password: str = ""


class CredentialProvider:
    """منبع واحد credentials."""

    _instance: Credentials | None = None

    @classmethod
    def load(cls) -> Credentials:
        """بارخوانی از keyring یا .env."""
        if cls._instance:
            return cls._instance

        creds = Credentials()

        # === LMS از keyring ===
        lms = CredentialsManager.get_lms()
        if lms:
            creds.lms_username, creds.lms_password = lms
        else:
            # fallback به .env
            creds.lms_username = settings.lms_username or ""
            creds.lms_password = settings.lms_password or ""

        # === Quera از keyring ===
        quera = CredentialsManager.get_quera()
        if quera:
            creds.quera_username, creds.quera_password = quera
        else:
            creds.quera_username = settings.quera_username or ""
            creds.quera_password = settings.quera_password or ""

        cls._instance = creds
        return creds

    @classmethod
    def update(
        cls,
        lms_username: str,
        lms_password: str,
        quera_username: str = "",
        quera_password: str = "",
    ) -> None:
        """آپدیت credentials (بعد از Login Dialog)."""
        cls._instance = Credentials(
            lms_username=lms_username,
            lms_password=lms_password,
            quera_username=quera_username,
            quera_password=quera_password,
        )

    @classmethod
    def get(cls) -> Credentials:
        """دریافت credentials فعلی."""
        if cls._instance is None:
            return cls.load()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """ریست (برای logout)."""
        cls._instance = None