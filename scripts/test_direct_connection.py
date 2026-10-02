"""تست اتصال مستقیم بدون Proxy."""

import httpx


def test_direct():
    print("=== تست با trust_env=False ===")
    with httpx.Client(
        timeout=30,
        trust_env=False,
        follow_redirects=True,
    ) as client:
        try:
            r = client.get("https://lms4.ui.ac.ir/")
            print(f"✅ اتصال موفق: {r.status_code} ({len(r.text)} bytes)")
        except Exception as e:
            print(f"❌ خطا: {type(e).__name__}: {e}")


def test_with_proxy():
    print("\n=== تست با Proxy سیستمی ===")
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        try:
            r = client.get("https://lms4.ui.ac.ir/")
            print(f"✅ اتصال موفق: {r.status_code} ({len(r.text)} bytes)")
        except Exception as e:
            print(f"❌ خطا: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_direct()
    test_with_proxy()