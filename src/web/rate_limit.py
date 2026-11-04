"""Rate limiter ساده در حافظه برای endpointهای حساس (مثل login).

برای یک instance کافی است. اگر چند worker داشته باشی، باید
Redis یا مشابه استفاده شود — الان عمداً ساده نگه داشته شده.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """محدودیت تعداد درخواست در یک پنجرهٔ زمانی."""

    def __init__(self, max_calls: int, window_seconds: float) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """True اگر مجاز؛ False اگر بیش از حد."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            cutoff = now - self.window
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.max_calls:
                return False
            q.append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            cutoff = now - self.window
            while q and q[0] < cutoff:
                q.popleft()
            return max(0, self.max_calls - len(q))

    def retry_after_seconds(self, key: str) -> int:
        """تقریباً چند ثانیه تا آزاد شدن اولین slot."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            if not q:
                return 0
            oldest = q[0]
            wait = int(self.window - (now - oldest)) + 1
            return max(1, wait)


# لاگین: ۵ تلاش / ۱۵ دقیقه per IP — ۱۰ تلاش / ۱۵ دقیقه per username
login_ip_limiter = SlidingWindowLimiter(max_calls=5, window_seconds=15 * 60)
login_user_limiter = SlidingWindowLimiter(max_calls=10, window_seconds=15 * 60)
