"""Parser برای استخراج اطلاعات جلسات (زمان + مکان) از صفحه‌ی درس."""

import re

from bs4 import BeautifulSoup
from loguru import logger

from src.models.course_schedule import CourseSchedule


class CourseScheduleParser:
    """استخراج زمان + مکان کلاس از HTML صفحه‌ی درس.

    ساختار HTML (نمونه):
    ایجاد شده: ۲۱ مهر ۱۴۰۵ ۹:۴۲ عصر
    حمید ملا - کد درس: ۲۰۳۰۶-۱۱-۱ | برگزاری: سه شنبه ۰۰:۱۶-۱۴:۰۰ |
    فنی و مهندسی ساختمان انصاری - طبقه همکف - اتاق شماره ۱۳۵
    """

    # الگوی روز هفته
    WEEKDAYS = [
        "شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "سه شنبه",
        "چهارشنبه", "پنج‌شنبه", "پنج شنبه", "جمعه",
    ]

    # الگوی ساعت: 00:16-14:00 یا 16:00-14:00 یا 14:00
    TIME_PATTERN = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")

    # الگوی اتاق
    ROOM_PATTERN = re.compile(r"اتاق\s+شماره\s+(\d+)")

    # الگوی طبقه
    FLOOR_PATTERN = re.compile(r"طبقه\s+([^\s\-|]+)")

    # الگوی ساختمان
    BUILDING_PATTERN = re.compile(r"(ساختمان\s+[^\s\-|]+|فنی\s+و\s+مهندسی[^\s\-|]*)")

    def parse(self, html: str, course_id: str) -> CourseSchedule | None:
        """استخراج اطلاعات از HTML."""
        soup = BeautifulSoup(html, "lxml")

        # === پیدا کردن متن «برگزاری» ===
        text = soup.get_text(separator=" ", strip=True)

        # پاکسازی
        text = text.replace("\xa0", " ").replace("\u200c", "")
        text = re.sub(r"\s+", " ", text)

        # === پیدا کردن بخش «برگزاری» ===
        # الگو: «برگزاری: سه شنبه 00:16-14:00 | فنی و مهندسی... - طبقه همکف - اتاق شماره 135»
        pattern = re.compile(
            r"برگزاری\s*:\s*(.+?)(?=ایجاد|$)",
            re.DOTALL,
        )
        match = pattern.search(text)

        if not match:
            logger.debug(f"بخش «برگزاری» توی درس {course_id} پیدا نشد")
            return None

        schedule_text = match.group(1).strip()

        # === استخراج روز ===
        weekday = None
        for wd in self.WEEKDAYS:
            if wd in schedule_text:
                weekday = wd
                break

        # === استخراج ساعت ===
        start_time = None
        end_time = None
        time_match = self.TIME_PATTERN.search(schedule_text)
        if time_match:
            start_time = time_match.group(1)
            end_time = time_match.group(2)

        # === استخراج اتاق ===
        room = None
        room_match = self.ROOM_PATTERN.search(schedule_text)
        if room_match:
            room = room_match.group(1)

        # === استخراج طبقه ===
        floor = None
        floor_match = self.FLOOR_PATTERN.search(schedule_text)
        if floor_match:
            floor = floor_match.group(1).strip()

        # === استخراج ساختمان ===
        building = None
        building_match = self.BUILDING_PATTERN.search(schedule_text)
        if building_match:
            building = building_match.group(1).strip()

        return CourseSchedule(
            course_id=course_id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            building=building,
            floor=floor,
            room=room,
            raw_text=schedule_text,
        )