"""LMS Assistant - Entry Point."""

from config.settings import settings


def main():
    print("LMS Assistant")
    print(f"Username: {settings.lms_username}")
    print(f"Base URL: {settings.lms_base_url}")
    print(f"DB Path: {settings.db_path}")


if __name__ == "__main__":
    main()