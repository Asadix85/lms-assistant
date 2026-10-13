"""Parser برای استخراج برنامه‌ی هفتگی (زمان + مکان) از صفحه‌ی درس."""

import re

from bs4 import BeautifulSoup
from loguru import logger

from src.models.course_schedule import ClassSession, CourseSchedule


class CourseScheduleParser:
    """استخراج برنامه‌ی کلاس از HTML صفحه‌ی wall.

    ساختار:
    <div id='group_information'>
      ایجاد شده : ۲۱ مهر ۰۵, ۱۰:۱۳ عصر
      کمال جمشیدی - کد درس : 36-20-313  برگزاری : دوشنبه 09:00-10:00 در فني و مهندسي كلاس 25- ...|
    </div>
    """

    # ⚠️ بلندترین اول (تا «شنبه» داخل «دوشنبه» match نشه)
    WEEKDAYS = [
        "چهارشنبه",
        "پنج‌شنبه", "پنج شنبه", "پنجشنبه",
        "یک‌شنبه", "یک شنبه", "یکشنبه",
        "دوشنبه",
        "سه‌شنبه", "سه شنبه",
        "جمعه",
        "شنبه",  # ← آخر (کوتاه‌ترین)
    ]

    # الگوی ساعت: 09:00-10:00
    TIME_PATTERN = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")

    # الگوی کد درس
    CODE_PATTERN = re.compile(r"کد\s*درس\s*:\s*([\d\-]+)")

    def parse(self, html: str, course_id: str) -> CourseSchedule | None:
        soup = BeautifulSoup(html, "lxml")

        info_div = soup.find("div", id="group_information")
        if not info_div:
            logger.debug(f"div#group_information توی درس {course_id} پیدا نشد")
            return None

        text = info_div.get_text(separator=" ", strip=True)
        text = text.replace("\xa0", " ").replace("\u200c", "")
        text = re.sub(r"\s+", " ", text)

        logger.debug(f"متن schedule: {text[:200]}")

        # کد درس
        course_code = ""
        code_match = self.CODE_PATTERN.search(text)
        if code_match:
            course_code = code_match.group(1)

        # بخش «برگزاری»
        schedule_text = text
        if "برگزاری" in text:
            idx = text.find("برگزاری")
            schedule_text = text[idx:]

        # استخراج جلسات
        sessions = self._parse_sessions(schedule_text)

        return CourseSchedule(
            course_id=course_id,
            course_code=course_code,
            sessions=sessions,
            raw_text=text,
        )

    def _parse_sessions(self, text: str) -> list[ClassSession]:
        """استخراج جلسات از متن (با longest-match-first)."""
        sessions: list[ClassSession] = []

        # جایگزینی , با |
        text = text.replace(",", "|")

        # === استراتژی: از چپ به راست، بلندترین match ===
        # موقعیت‌های شروع رو پیدا کن
        positions = []
        i = 0
        while i < len(text):
            matched = False
            # بلندترین روز اول
            for weekday in self.WEEKDAYS:
                if text[i:i + len(weekday)] == weekday:
                    positions.append((i, weekday))
                    i += len(weekday)
                    matched = True
                    break
            if not matched:
                i += 1

        logger.debug(f"پیدا شد {len(positions)} روز: {[(p[1]) for p in positions]}")

        # === برای هر روز، جلسه رو استخراج کن ===
        for idx, (start, weekday) in enumerate(positions):
            # پایان = شروع روز بعد یا انتهای متن
            if idx + 1 < len(positions):
                end = positions[idx + 1][0]
            else:
                # آخرین جلسه: تا انتهای متن یا اولین |
                pipe_idx = text.find("|", start)
                end = pipe_idx if pipe_idx != -1 else len(text)

            session_text = text[start:end].strip()

            session = self._parse_single_session(session_text, weekday)
            if session:
                sessions.append(session)

        return sessions

    def _parse_single_session(
        self,
        text: str,
        weekday: str,
    ) -> ClassSession | None:
        """پارس یه جلسه."""
        # ساعت
        time_match = self.TIME_PATTERN.search(text)
        if not time_match:
            return None

        start_time = time_match.group(1)
        end_time = time_match.group(2)

        # === مکان: اولین «در» رو بگیر ===
        location = ""
        match = re.search(r"\sدر\s+(.+?)(?:\s*\||$)", text)
        if match:
            location = match.group(1).strip()

        # پاکسازی
        location = re.sub(r"\s+", " ", location).strip()

        # ⚠️ حذف تکرار (نصف دوم اگه با نصف اول یکیه)
        location = self._dedupe_location(location)

        return ClassSession(
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            location=location,
        )

    def _dedupe_location(self, location: str) -> str:
        """حذف تکرار در مکان.

        مثال:
        «ساختمان A ساختمان A کلاس 203» → «ساختمان A کلاس 203»
        """
        if not location:
            return location

        words = location.split()
        n = len(words)

        # اگه تعداد کلمات زوجه، چک کن نصف اول == نصف دوم
        # ولی معمولاً تکرار قبل از «کلاس» هست

        # روش: دنبال تکرار کلمه‌به‌کلمه بگرد
        # برای سادگی: اگه نصف اول متن == نصف دوم متن، حذف کن
        for split in range(n // 2, 0, -1):
            first_half = " ".join(words[:split])
            second_half = " ".join(words[split:split * 2])
            if first_half == second_half:
                # تکرار پیدا شد
                rest = " ".join(words[split * 2:])
                return f"{first_half} {rest}".strip()

        return location

        return ClassSession(
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            location=location,
        )