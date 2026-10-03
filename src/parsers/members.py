"""Parser برای اعضای درس."""

import re

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.models.member import Member, MemberType
from src.parsers.base import BaseParser


class MemberParser(BaseParser):
    """استخراج اعضای درس از HTML widget."""

    MEMBER_LI_PATTERN = re.compile(r"group_member_(\d+)")

    # IDهای سیستم/پشتیبانی که همیشه نادیده گرفته می‌شن
    SYSTEM_USER_IDS = {
        "1", "10", "20399", "24794", "34399", "49873",
    }

    # کلمات کلیدی پشتیبانی
    SUPPORT_KEYWORDS = [
        "پشتیبانی",
        "کارشناس",
        "پاسخگو",
        "مدیر مرکز",
        "همیار فنی",
        "سیستم",
    ]

    def __init__(self, course_id: str, teacher_name: str | None = None, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.course_id = course_id
        self.teacher_name = (teacher_name or "").replace("استاد ", "").strip()
        self.base_url = base_url.rstrip("/")

    def parse(self, html: str, is_admin_page: bool = False) -> list[Member]:
        """استخراج اعضا از HTML widget."""
        soup = BeautifulSoup(html, "lxml")
        members: list[Member] = []

        for li in soup.find_all("li", id=self.MEMBER_LI_PATTERN):
            member = self._parse_li(li, is_admin_page=is_admin_page)
            if member:
                members.append(member)

        logger.info(f"{len(members)} عضو در {self.course_id} (admin_page={is_admin_page})")
        return members

    def _parse_li(self, li: Tag, is_admin_page: bool = False) -> Member | None:
        """Parse یک <li> عضو."""
        # user_id
        li_id = li.get("id", "")
        match = self.MEMBER_LI_PATTERN.match(li_id)
        if not match:
            return None
        user_id = match.group(1)

        # نام
        name = ""
        for td in li.find_all("td"):
            if td.get("width") == "70%":
                name = td.get_text(strip=True)
                break

        if not name:
            return None

        # تشخیص نوع
        member_type = self._detect_type(user_id, name, is_admin_page)

        return Member(
            id=user_id,
            course_id=self.course_id,
            name=name,
            profile_url=f"{self.base_url}/profile/{user_id}",
            member_type=member_type,
        )

    def _detect_type(self, user_id: str, name: str, is_admin_page: bool) -> MemberType:
        """تشخیص نوع عضو."""
        # ۱. پشتیبان/سیستم
        if user_id in self.SYSTEM_USER_IDS:
            return MemberType.SUPPORT

        for kw in self.SUPPORT_KEYWORDS:
            if kw in name:
                return MemberType.SUPPORT

        # ۲. اگه در صفحه‌ی admin هست، احتمالاً استاد
        if is_admin_page:
            # اما فقط اگه با teacher_name مطابقت داره
            if self._is_teacher(name):
                return MemberType.TEACHER
            # اگه در admin هست اما نامش مطابقت نداره → استاد کمکی/دستیار
            return MemberType.TEACHER

        # ۳. استاد بر اساس نام
        if self._is_teacher(name):
            return MemberType.TEACHER

        # ۴. در غیر این صورت → دانشجو
        return MemberType.STUDENT

    def _is_teacher(self, name: str) -> bool:
        """آیا این کاربر استاد است؟"""
        if not self.teacher_name:
            return False

        name_clean = name.replace("استاد ", "").strip()

        if self.teacher_name in name_clean or name_clean in self.teacher_name:
            return True

        teacher_parts = set(self.teacher_name.split())
        name_parts = set(name_clean.split())
        if len(teacher_parts & name_parts) >= 2:
            return True

        return False