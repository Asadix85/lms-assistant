"""تست LMSHttpClient."""

from src.core.http_client import LMSHttpClient


def test_client_creation():
    """تست ساخت client."""
    client = LMSHttpClient(base_url="https://lms4.ui.ac.ir")
    assert client.base_url == "https://lms4.ui.ac.ir"
    assert not client.is_closed
    client.close()
    assert client.is_closed


def test_client_get():
    """تست GET ساده."""
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        r = client.get("/")
        assert r.status_code == 200
        assert len(r.text) > 0
        print(f"✅ GET / → {r.status_code} ({len(r.text)} bytes)")


def test_client_context_manager():
    """تست context manager."""
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        assert not client.is_closed
    assert client.is_closed


if __name__ == "__main__":
    test_client_creation()
    test_client_get()
    test_client_context_manager()
    print("همه تست‌ها موفق!")