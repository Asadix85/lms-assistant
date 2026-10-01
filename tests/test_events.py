"""تست Event collection."""

import os

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant

load_dotenv()


def test_all_events():
    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        assert assistant.login()
        print(f"✅ Login. User ID: {assistant.user_id}\n")

        events = assistant.get_all_events()

        print(f"\n{'='*60}")
        print(f"📅 {len(events)} رویداد پیدا شد")
        print('='*60)

        for e in events:
            time_str = e.start_at.strftime("%H:%M") if e.start_at else "?"
            print(f"  • {e.title}")
            print(f"    ساعت: {time_str}")
            print(f"    url: {e.url}")
            print(f"    token: {e.room_token}")


if __name__ == "__main__":
    test_all_events()
    print("\n🎉 تست موفق!")