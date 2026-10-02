"""User Parser: استخراج نام کاربر از HTML."""

import re

from bs4 import BeautifulSoup
from loguru import logger


class UserParser:
    """استخراج اطلاعات کاربر از صفحات LMS."""

    def parse_full_name(self, html: str) -> str | None:
        """استخراج نام کامل کاربر از HTML.

        در HTML LMS:
        <button class="nodemenu">
            <img src="..." />
            اسدی - محمد
        </button>
        """
        soup = BeautifulSoup(html, "lxml")

        # روش ۱: از button.nodemenu
        for btn in soup.find_all("button", class_="nodemenu"):
            text = btn.get_text(strip=True)
            if text:
                # پاکسازی: "اسدی - محمد" → "محمد اسدی"
                name = self._normalize_name(text)
                if name:
                    return name

        # روش ۲: از عنوان tab (fallback)
        for el in soup.find_all(["span", "div"], string=re.compile(r"اسدی|خوش آمد")):
            text = el.get_text(strip=True)
            if text and " - " in text:
                name = self._normalize_name(text)
                if name:
                    return name

        logger.warning("نام کاربر در HTML پیدا نشد")
        return None

    def _normalize_name(self, raw: str) -> str | None:
        """نرمال‌سازی نام.

        'اسدی - محمد' → 'محمد اسدی'
        """
        raw = raw.strip()
        if not raw or len(raw) > 60:
            return None

        # اگر با " - " جدا شده
        if " - " in raw:
            parts = [p.strip() for p in raw.split(" - ")]
            if len(parts) == 2:
                # parts[0] = نام خانوادگی، parts[1] = نام
                return f"{parts[1]} {parts[0]}"

        # اگر با فاصله
        if len(raw.split()) >= 2:
            return raw

        return None