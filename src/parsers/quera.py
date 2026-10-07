"""Parser برای Quera (از __NEXT_DATA__ JSON)."""

import json
import re
from datetime import datetime

from bs4 import BeautifulSoup
from loguru import logger

from src.models.quera_assignment import QueraAssignment, QueraProblem


class QueraParser:
    """استخراج تمرین‌ها از HTML کوئرا."""

    NEXT_DATA_PATTERN = re.compile(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        re.DOTALL,
    )

    def parse_course_page(self, html: str) -> list[QueraAssignment]:
        """پارس صفحه‌ی /course.

        از `__NEXT_DATA__` لیست تمرین‌های پیش رو رو استخراج می‌کنه.
        """
        next_data = self._extract_next_data(html)
        if not next_data:
            logger.warning("__NEXT_DATA__ پیدا نشد")
            return []

        # مسیر: props.pageProps.course.course_deadline_widget_data
        try:
            data = (
                next_data
                .get("props", {})
                .get("pageProps", {})
                .get("course", {})
                .get("course_deadline_widget_data", [])
            )
        except AttributeError:
            logger.warning("ساختار __NEXT_DATA__ غیرمنتظره")
            return []

        assignments: list[QueraAssignment] = []

        for item in data:
            assignment = self._parse_assignment(item)
            if assignment:
                assignments.append(assignment)

        logger.info(f"{len(assignments)} تمرین از Quera استخراج شد")
        return assignments

    def _extract_next_data(self, html: str) -> dict | None:
        """استخراج __NEXT_DATA__ JSON."""
        match = self.NEXT_DATA_PATTERN.search(html)
        if not match:
            return None

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            logger.error(f"خطا در parse __NEXT_DATA__: {e}")
            return None

    def _parse_assignment(self, data: dict) -> QueraAssignment | None:
        """پارس یه تمرین."""
        try:
            assignment_id = str(data.get("id", ""))
            name = data.get("name", "")
            course_name = data.get("course_name", "")
            finish_time_str = data.get("finish_time")

            if not assignment_id or not name:
                return None

            # parse finish_time
            finish_time = None
            if finish_time_str:
                try:
                    # ISO 8601: 2026-10-09T20:29:59+00:00
                    dt = datetime.fromisoformat(finish_time_str)
                    # ⚠️ تبدیل به timezone ایران (یا حذف timezone)
                    if dt.tzinfo is not None:
                        # تبدیل به timezone محلی
                        dt = dt.astimezone()
                        # حذف timezone (naive local)
                        dt = dt.replace(tzinfo=None)
                    finish_time = dt
                except (ValueError, TypeError) as e:
                    logger.debug(f"خطا در parse finish_time: {e}")

            # parse problems
            problems = []
            for p in data.get("problems", []):
                problem = self._parse_problem(p)
                if problem:
                    problems.append(problem)

            return QueraAssignment(
                id=assignment_id,
                name=name,
                course_name=course_name,
                finish_time=finish_time,
                problems=problems,
            )

        except Exception as e:
            logger.warning(f"خطا در parse assignment: {e}")
            return None

    def _parse_problem(self, data: dict) -> QueraProblem | None:
        """پارس یه سؤال."""
        try:
            problem_id = str(data.get("id", ""))
            name = data.get("name", "")

            if not problem_id or not name:
                return None

            return QueraProblem(
                id=problem_id,
                name=name,
                type=data.get("type", "U"),
                submission_score=data.get("submission_score"),
                state=data.get("state", "NO_SUBMIT"),
            )
        except Exception as e:
            logger.warning(f"خطا در parse problem: {e}")
            return None