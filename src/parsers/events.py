"""Parser برای تقویم (events) — با استخراج تاریخ شمسی."""

import re
from datetime import datetime

import jdatetime
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.models.event import Event, EventType
from src.parsers.base import BaseParser


class EventParser(BaseParser):
    """استخراج رویدادها از HTML /pages/calendar."""

    JOINFAST_PATTERN = re.compile(r"/jaam/joinfast/([A-F0-9]+)/(\d+)")
    HOUR_PATTERN = re.compile(r"(\d{1,2}:\d{2})")

    # الگوی تاریخ شمسی
    JALALI_DATE_PATTERN = re.compile(
        r"(\d{1,2})\s+"
        r"(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)"
        r"(?:\s+ماه)?\s+"
        r"(\d{4})"
    )

    PERSIAN_MONTHS = {
        "فروردین": 1, "اردیبهشت": 2, "خرداد": 3,
        "تیر": 4, "مرداد": 5, "شهریور": 6,
        "مهر": 7, "آبان": 8, "آذر": 9,
        "دی": 10, "بهمن": 11, "اسفند": 12,
    }

    def __init__(self, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.base_url = base_url.rstrip("/")

    def parse(self, html: str) -> list[Event]:
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen_ids: set[str] = set()

        # === پیدا کردن همه‌ی div.dattime (با class_ ساده) ===
        day_containers = soup.find_all("div", class_="dattime")

        logger.debug(f"پیدا شد: {len(day_containers)} div.dattime")

        for container in day_containers:
            # === استخراج تاریخ از متن container ===
            start_date = self._extract_date_from_container(container)

            if start_date:
                logger.debug(
                    f"  📅 تاریخ پیدا شد: {start_date.strftime('%Y-%m-%d')}"
                )
            else:
                # لاگ متن برای debug
                text = container.get_text(separator=" ", strip=True)[:100]
                logger.debug(f"  ⚠️ تاریخ پیدا نشد. متن: {text}")

            # === همه‌ی aهای joinfast داخل ===
            for link in container.find_all("a", href=True):
                href = link["href"]
                if "joinfast" not in href:
                    continue

                event = self._parse_link(link, start_date)
                if event and event.id not in seen_ids:
                    events.append(event)
                    seen_ids.add(event.id)

        # === fallback ===
        if not day_containers:
            logger.warning("div.dattime پیدا نشد — fallback")
            for link in soup.find_all("a", href=True):
                if "joinfast" not in link["href"]:
                    continue
                event = self._parse_link(link, None)
                if event and event.id not in seen_ids:
                    events.append(event)
                    seen_ids.add(event.id)

        logger.info(f"{len(events)} رویداد استخراج شد")
        return events

    def _extract_date_from_container(self, container: Tag) -> datetime | None:
        """استخراج تاریخ از متن div.dattime."""
        # متن کامل
        text = container.get_text(separator=" ", strip=True)

        # ⚠️ پاکسازی کاراکترهای عجیب
        text = text.replace("\xa0", " ").replace("\u200c", " ")
        text = re.sub(r"\s+", " ", text)

        # جستجوی الگو
        match = self.JALALI_DATE_PATTERN.search(text)
        if not match:
            return None

        try:
            day = int(match.group(1))
            month_name = match.group(2)
            year = int(match.group(3))
            month = self.PERSIAN_MONTHS[month_name]

            jd = jdatetime.date(year, month, day)
            gd = jd.togregorian()

            return datetime(gd.year, gd.month, gd.day)

        except (ValueError, KeyError) as e:
            logger.warning(f"خطا در parse: {match.group(0)} — {e}")
            return None

    def _parse_link(
        self,
        link: Tag,
        start_date: datetime | None,
    ) -> Event | None:
        """Parse یک لینک joinfast."""
        href = link.get("href", "")
        if not self.JOINFAST_PATTERN.search(href):
            return None

        if href.startswith("http"):
            url = href
        else:
            url = f"{self.base_url}{href}"

        # عنوان و متن
        inner_div = link.find("div")
        if inner_div:
            title = (
                inner_div.get("title")
                or inner_div.get_text(separator=" ", strip=True)
            )
            full_text = inner_div.get_text(separator=" ", strip=True)
        else:
            title = link.get_text(separator=" ", strip=True)
            full_text = title

        if not title:
            return None

        # پاکسازی
        full_text = full_text.replace("\xa0", " ")

        # ساعت
        start_hour = None
        hour_match = self.HOUR_PATTERN.search(full_text)
        if hour_match:
            start_hour = hour_match.group(1)

        # عنوان
        title_clean = title.strip()
        if len(title_clean) > 200:
            title_clean = title_clean[:200]

        return self._create_event(
            url=url,
            title=title_clean,
            start_date=start_date,
            start_hour=start_hour,
        )

    def _create_event(
        self,
        url: str,
        title: str,
        start_date: datetime | None,
        start_hour: str | None,
    ) -> Event:
        """ساخت Event."""
        token = None
        room_id = None
        parts = url.rstrip("/").split("/")
        if "joinfast" in parts:
            idx = parts.index("joinfast")
            if idx + 1 < len(parts):
                token = parts[idx + 1]
            if idx + 2 < len(parts):
                room_id = parts[idx + 2]

        if room_id:
            event_id = f"jaam_{room_id}"
        else:
            import hashlib
            event_id = hashlib.sha256(url.encode()).hexdigest()[:16]

        # ترکیب تاریخ + ساعت
        start_at = None
        if start_date:
            if start_hour:
                try:
                    h, m = start_hour.split(":")
                    start_at = start_date.replace(
                        hour=int(h), minute=int(m), second=0, microsecond=0
                    )
                except (ValueError, AttributeError):
                    start_at = start_date
            else:
                start_at = start_date

        return Event(
            id=event_id,
            course_id=None,
            title=title.strip(),
            event_type=EventType.LIVE_SESSION,
            url=url,
            room_token=token,
            start_at=start_at,
        )