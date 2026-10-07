"""تست login به Quera."""

from config.settings import settings
from src.core.quera_auth import QueraAuth
from src.core.quera_client import QueraHttpClient


def main() -> None:
    if not settings.quera_username or not settings.quera_password:
        print("❌ QUERA_USERNAME و QUERA_PASSWORD رو توی .env تنظیم کن")
        return

    print("=" * 50)
    print("🧪 تست Login به Quera")
    print("=" * 50)

    client = QueraHttpClient()
    auth = QueraAuth(client)

    try:
        success = auth.login(
            settings.quera_username,
            settings.quera_password,
        )

        if success:
            print("✅ Login موفق!")
            print(f"👤 Identifier: {auth.identifier}")

            # تست: گرفتن /dashboard
            print("\n📚 تست دریافت /dashboard...")
            r = client.get("/dashboard")
            print(f"   Status: {r.status_code}")
            print(f"   Size: {len(r.text)} کاراکتر")
            print(f"   URL نهایی: {r.url}")

            # ذخیره HTML
            from pathlib import Path
            Path("debug_quera_dashboard.html").write_text(
                r.text, encoding="utf-8"
            )
            print("   💾 ذخیره شد: debug_quera_dashboard.html")

            # تست: /course
            print("\n🎓 تست دریافت /course...")
            r2 = client.get("/course")
            print(f"   Status: {r2.status_code}")
            print(f"   Size: {len(r2.text)} کاراکتر")
            print(f"   URL نهایی: {r2.url}")

            Path("debug_quera_course.html").write_text(
                r2.text, encoding="utf-8"
            )
            print("   💾 ذخیره شد: debug_quera_course.html")
        else:
            print("❌ Login ناموفق")

    except Exception as e:
        print(f"❌ خطا: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    main()