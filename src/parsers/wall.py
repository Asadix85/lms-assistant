"""Parser برای wall درس (Post + Assignment)."""

import re
from datetime import datetime

import jdatetime
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.models.assignment import Assignment
from src.models.post import Post
from src.parsers.base import BaseParser


class WallParser(BaseParser):
    """استخراج Post و Assignment از wall درس."""

    ASSIGNMENT_DATE_PATTERN = re.compile(
        r"(\d{1,2})\s+(\S+)\s+(\d{4})\s*-\s*(\d{1,2}):(\d{2})"
    )

    POST_DATE_PATTERN = re.compile(
        r"(\d{1,2})\s+(\S+)\s+(\d{2,4}),\s+(\d{1,2}):(\d{2})\s*(عصر|صبح|بعدازظهر)?"
    )

    JALALI_MONTHS = {
        "فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4,
        "مرداد": 5, "شهریور": 6, "مهر": 7, "آبان": 8,
        "آذر": 9, "دی": 10, "بهمن": 11, "اسفند": 12,
        "شهريور": 6,
    }

    def __init__(self, course_id: str, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.course_id = course_id
        self.base_url = base_url.rstrip("/")

    def parse(self, html: str) -> tuple[list[Post], list[Assignment]]:
        soup = BeautifulSoup(html, "lxml")
        posts: list[Post] = []
        assignments: list[Assignment] = []

        for body in soup.find_all("div", class_="feed_item_body"):
            post = self._parse_post(body)
            if post:
                posts.append(post)

            assignment = self._parse_assignment(body, post)
            if assignment:
                assignments.append(assignment)

        logger.info(
            f"{len(posts)} پست و {len(assignments)} تکلیف در درس {self.course_id}"
        )
        return posts, assignments

    def _parse_post(self, body: Tag) -> Post | None:
        posted = body.find("span", class_="feed_item_posted")
        if not posted:
            return None

        author_el = posted.find("a", class_="feed_item_username")
        if not author_el:
            return None

        author = author_el.get_text(strip=True)
        author_id = ""
        href = author_el.get("href", "")
        match = re.search(r"/profile/(\d+)", href)
        if match:
            author_id = match.group(1)

        text_el = posted.find("span", class_="feed_item_bodytext")
        text = text_el.get_text(separator=" ", strip=True) if text_el else ""

        if not text:
            return None

        posted_at = None
        posted_at_jalali = None
        date_el = body.find("span", class_="timestamp")
        if date_el:
            posted_at_jalali = date_el.get("title", "") or date_el.get_text(strip=True)
            posted_at = self._parse_post_date(posted_at_jalali)

        post_url = None
        for a in body.find_all("a", href=True):
            if a["href"].startswith("/posts/"):
                post_url = f"{self.base_url}{a['href']}"
                break

        post_id = Post.make_id(post_url or text[:50], self.course_id)

        return Post(
            id=post_id,
            course_id=self.course_id,
            author=author,
            author_id=author_id,
            text=text,
            posted_at=posted_at,
            posted_at_jalali=posted_at_jalali,
            post_url=post_url,
        )

    def _parse_assignment(self, body: Tag, post: Post | None) -> Assignment | None:
        attachments = body.find("div", class_="feed_item_attachments")
        if not attachments:
            return None

        submit_link = None
        view_link = None
        for a in attachments.find_all("a", href=True):
            href = a["href"]
            if "/assignment/sendreplay/" in href:
                submit_link = href
            elif "/assignment/viewresponse/" in href:
                view_link = href

        if not submit_link:
            return None

        match = re.search(r"/assignment/sendreplay/(\d+)", submit_link)
        if not match:
            return None
        assignment_id = match.group(1)

        # ⚠️ استخراج نام کامل
        title = self._extract_full_title(attachments, post)
        if not title:
            return None

        start_at = None
        start_at_jalali = None
        start_el = attachments.find("span", class_="ass_st_time")
        if start_el:
            start_text = start_el.get_text(strip=True)
            start_at = self._parse_assignment_date(start_text)
            start_at_jalali = self._extract_jalali_date(start_text)

        deadline = None
        deadline_jalali = None
        deadline_el = attachments.find("div", class_="ass_en_time")
        if deadline_el:
            deadline_text = deadline_el.get_text(strip=True)
            deadline = self._parse_assignment_date(deadline_text)
            deadline_jalali = self._extract_jalali_date(deadline_text)

        response_count = 0
        count_match = re.search(r"(\d+)\s*نفر", attachments.get_text())
        if count_match:
            response_count = int(count_match.group(1))

        return Assignment(
            id=assignment_id,
            course_id=self.course_id,
            title=title,
            description=post.text if post else "",
            post_id=post.id if post else None,
            start_at=start_at,
            deadline=deadline,
            start_at_jalali=start_at_jalali,
            deadline_jalali=deadline_jalali,
            submit_url=f"{self.base_url}{submit_link}",
            view_url=f"{self.base_url}{view_link}" if view_link else None,
            response_count=response_count,
        )

    def _extract_full_title(self, attachments: Tag, post: Post | None) -> str:
        """استخراج نام کامل تکلیف.

        از get_text(separator="", strip=True) استفاده می‌کنه و فاصله‌ها رو نرمال می‌کنه.
        """
        # روش ۱: از b داخل span "عنوان"
        for span in attachments.find_all("span"):
            if "عنوان" in span.get_text():
                b = span.find("b")
                if b:
                    # ⚠️ separator="" → متن کامل
                    title = b.get_text(separator="", strip=True)
                    if title and len(title) > 5:
                        # نرمال‌سازی فاصله‌ها (شامل \xa0)
                        title = title.replace("\xa0", " ")
                        title = re.sub(r"\s+", " ", title).strip()
                        return title

                # اگر b نبود
                full_text = span.get_text(separator=" ", strip=True)
                title = re.sub(r"^عنوان\s*:\s*", "", full_text).strip()
                title = title.replace("\xa0", " ")
                title = re.sub(r"\s+", " ", title).strip()
                if title and len(title) > 5:
                    return title

        # روش ۲: از post.text
        if post:
            title = post.text.strip()
            title = title.replace("\xa0", " ")
            title = re.sub(r"\s+", " ", title).strip()
            if title:
                return title

        return ""

    def _parse_assignment_date(self, text: str) -> datetime | None:
        if not text:
            return None

        match = self.ASSIGNMENT_DATE_PATTERN.search(text)
        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))

        month = self.JALALI_MONTHS.get(month_name)
        if not month:
            return None

        try:
            jdate = jdatetime.datetime(year, month, day, hour, minute)
            return jdate.togregorian()
        except Exception as e:
            logger.warning(f"خطا در parse تاریخ '{text}': {e}")
            return None

    def _extract_jalali_date(self, text: str) -> str | None:
        if not text:
            return None

        pattern = re.compile(
            r"(\d{1,2}\s+\S+\s+\d{4}\s*-\s*\d{1,2}:\d{2})"
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

        return None

    def _parse_post_date(self, text: str) -> datetime | None:
        if not text:
            return None

        match = self.POST_DATE_PATTERN.search(text)
        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        period = match.group(6)

        if year < 100:
            year = 1400 + year

        if period == "عصر" and hour < 12:
            hour += 12

        month = self.JALALI_MONTHS.get(month_name)
        if not month:
            return None

        try:
            jdate = jdatetime.datetime(year, month, day, hour, minute)
            return jdate.togregorian()
        except Exception as e:
            logger.warning(f"خطا در parse تاریخ پست '{text}': {e}")
            return None