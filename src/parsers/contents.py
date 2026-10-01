"""Parser برای صفحه listofcontent (پشتیبانی از multi-domain)."""

import re

from bs4 import BeautifulSoup
from loguru import logger

from src.models.content import Content
from src.parsers.base import BaseParser


class ContentParser(BaseParser):
    """استخراج فایل‌های محتوا از HTML listofcontent.

    الگوی URL فایل‌ها (در lms3 و lms4):
    /public/group/{a}/{b}/{c}/{id}_{hash}.{ext}
    """

    FILE_URL_PATTERN = re.compile(
        r"/public/group/[^/]+/[^/]+/[^/]+/[^/]+\.\w+",
        re.IGNORECASE,
    )

    ALLOWED_EXTENSIONS = {
        "pdf", "zip", "rar", "docx", "doc", "pptx", "ppt",
        "xlsx", "xls", "txt", "mp4", "mp3", "wav",
        "jpg", "jpeg", "png", "gif", "svg",
    }

    def __init__(self, course_id: str, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.course_id = course_id
        self.base_url = base_url.rstrip("/")

    def parse(self, html: str) -> list[Content]:
        soup = BeautifulSoup(html, "lxml")
        contents: list[Content] = []
        seen_urls: set[str] = set()

        for link in soup.find_all("a", href=True):
            content = self._parse_link(link)
            if content and content.url not in seen_urls:
                contents.append(content)
                seen_urls.add(content.url)

        logger.info(f"{len(contents)} فایل در درس {self.course_id} استخراج شد")
        return contents

    def _parse_link(self, link) -> Content | None:
        href = link.get("href", "")
        if not href:
            return None

        if href.startswith("/"):
            full_url = f"{self.base_url}{href}"
        elif href.startswith("http"):
            full_url = href
        else:
            return None

        if not self.FILE_URL_PATTERN.search(full_url):
            return None

        title = link.get_text(strip=True)
        if not title:
            return None

        ext = full_url.rsplit(".", 1)[-1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return None

        return Content.from_url_and_title(
            url=full_url,
            title=title,
            course_id=self.course_id,
        )