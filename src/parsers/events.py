"""Parser برای تقویم (events)."""

import re

from bs4 import BeautifulSoup
from loguru import logger

from src.models.event import Event, EventType
from src.parsers.base import BaseParser


class EventParser(BaseParser):
    """استخراج رویدادها از HTML /pages/calendar.

    ساختار HTML:
    <a href="/jaam/joinfast/{token}/{id}">
      <div title="نام درس-جلسه N" class="bbbs ...">
        نام درس-جلسه N
        » شروع از ساعت HH:MM در کلاس ...
      </div>
    </a>
    """

    JOINFAST_PATTERN = re.compile(r"/jaam/joinfast/([A-F0-9]+)/(\d+)")
    # ساده‌تر: هر HH:MM
    HOUR_PATTERN = re.compile(r"(\d{1,2}:\d{2})")

    def __init__(self, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.base_url = base_url.rstrip("/")

    def parse(self, html: str) -> list[Event]:
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen_ids: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "joinfast" not in href:
                continue

            event = self._parse_link(link)
            if event and event.id not in seen_ids:
                events.append(event)
                seen_ids.add(event.id)

        logger.info(f"{len(events)} رویداد استخراج شد")
        return events

    def _parse_link(self, link) -> Event | None:
        href = link.get("href", "")
        if not self.JOINFAST_PATTERN.search(href):
            return None

        # URL کامل
        if href.startswith("http"):
            url = href
        else:
            url = f"{self.base_url}{href}"

        # === استراتژی: div داخلی با title ===
        inner_div = link.find("div")
        if inner_div:
            # عنوان از title
            title = inner_div.get("title") or inner_div.get_text(separator=" ", strip=True)
            # متن کامل برای پیدا کردن ساعت
            full_text = inner_div.get_text(separator=" ", strip=True)
        else:
            # fallback
            title = link.get_text(separator=" ", strip=True)
            full_text = title

        if not title:
            return None

        # === پیدا کردن ساعت ===
        start_hour = None
        hour_match = self.HOUR_PATTERN.search(full_text)
        if hour_match:
            start_hour = hour_match.group(1)

        # === پاکسازی title ===
        # اگر title خیلی طولانی بود، برش بزن
        title_clean = title.strip()
        if len(title_clean) > 200:
            title_clean = title_clean[:200]

        return Event.from_joinfast(
            url=url,
            title=title_clean,
            start_hour=start_hour,
            course_id=None,
        )