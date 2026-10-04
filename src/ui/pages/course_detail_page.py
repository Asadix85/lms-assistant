"""Course Detail Page: صفحه‌ی جزئیات یک درس (حرفه‌ای)."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QTabWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices

from src.models.course import Course
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    PostRepository,
)
from src.ui.theme import Colors, CurrentTheme
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.widgets.post_card import PostCard
from src.ui.widgets.course_info_card import CourseInfoCard
from src.ui.widgets.course_stats_cards import CourseStatsCards
from src.ui.widgets.empty_state import EmptyState


class CourseDetailPage(QWidget):
    """صفحه‌ی جزئیات یک درس."""

    back_clicked = Signal()

    DOMAIN_META = {
        "lms3": ("🟢", "علوم پایه"),
        "lms4": ("🔵", "فنی-مهندسی"),
        "lms5": ("🔴", "اداری-تربیتی"),
    }

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db_path = db_path
        self._course: Course | None = None
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # === Header Row (Back) ===
        header_row = QHBoxLayout()
        header_row.setDirection(QHBoxLayout.RightToLeft)

        back_btn = QPushButton("←  بازگشت به دروس")
        back_btn.setObjectName("SecondaryButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        header_row.addWidget(back_btn)
        header_row.addStretch()

        layout.addLayout(header_row)

        # === Hero Section ===
        self.hero = QFrame()
        self.hero.setObjectName("HeroCard")
        self.hero.setMinimumHeight(120)

        hero_layout = QVBoxLayout(self.hero)
        hero_layout.setContentsMargins(30, 20, 30, 20)
        hero_layout.setSpacing(8)

        self.course_title = QLabel("—")
        self.course_title.setStyleSheet(
            "color: white; font-size: 22pt; font-weight: bold; "
            "background: transparent;"
        )
        self.course_title.setAlignment(Qt.AlignRight)
        hero_layout.addWidget(self.course_title)

        self.course_meta = QLabel("—")
        self.course_meta.setStyleSheet(
            "color: rgba(255,255,255,0.9); font-size: 11pt; "
            "background: transparent;"
        )
        self.course_meta.setAlignment(Qt.AlignRight)
        hero_layout.addWidget(self.course_meta)

        layout.addWidget(self.hero)

        # === Cards Row (استاد + آمار) ===
        cards_row = QHBoxLayout()
        cards_row.setSpacing(15)

        # کارت استاد
        self.info_card_container = QWidget()
        self.info_card_container.setAttribute(Qt.WA_TranslucentBackground, True)
        info_layout = QVBoxLayout(self.info_card_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_card = None

        # کارت‌های آمار
        self.stats_container = QWidget()
        self.stats_container.setAttribute(Qt.WA_TranslucentBackground, True)
        stats_layout = QVBoxLayout(self.stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats = None

        cards_row.addWidget(self.info_card_container, stretch=1)
        cards_row.addWidget(self.stats_container, stretch=2)

        layout.addLayout(cards_row)

        # === Tabs ===
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.RightToLeft)

        # Posts Tab
        self.posts_container = self._build_tab_container()
        self.tabs.addTab(self.posts_container, "📢 پیام‌ها")

        # Assignments Tab
        self.assignments_container = self._build_tab_container()
        self.tabs.addTab(self.assignments_container, "📋 تکالیف")

        # Members Tab
        self.members_container = self._build_tab_container()
        self.tabs.addTab(self.members_container, "👥 همکلاسی‌ها")

        # Contents Tab
        self.contents_container = self._build_tab_container()
        self.tabs.addTab(self.contents_container, "📄 فایل‌ها")

        layout.addWidget(self.tabs, stretch=1)

    def _build_tab_container(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAttribute(Qt.WA_TranslucentBackground, True)

        widget = QWidget()
        widget.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setAlignment(Qt.AlignTop)
        widget.setLayout(layout)

        scroll.setWidget(widget)
        scroll._content_layout = layout
        return scroll

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # === Data ===

    def load_course(self, course: Course) -> None:
        self._course = course

        # === Hero ===
        icon, _ = self.DOMAIN_META.get(course.domain, ("⚪", "?"))
        self.course_title.setText(f"{icon}  {course.name}")

        meta_parts = []
        meta_parts.append(f"🌐 {course.domain}")
        if course.code:
            meta_parts.append(f"📋 {course.code}")
        if course.term:
            meta_parts.append(f"📅 ترم {course.term}")
        self.course_meta.setText("  •  ".join(meta_parts))

        # === Info Card (استاد) ===
        self._clear_layout(self.info_card_container.layout())
        self.info_card = CourseInfoCard(course)
        self.info_card_container.layout().addWidget(self.info_card)

        # === Stats Cards ===
        self._clear_layout(self.stats_container.layout())
        self.stats = CourseStatsCards(self.db_path, course.group_id)
        self.stats_container.layout().addWidget(self.stats)

        # === Load tabs ===
        self._load_posts()
        self._load_assignments()
        self._load_contents()
        self._load_members()

        self.tabs.setCurrentIndex(0)

    def _load_posts(self) -> None:
        if not self._course:
            return

        layout = self.posts_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                repo = PostRepository(db)
                posts = repo.get_by_course(self._course.group_id, limit=50)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        if not posts:
            empty = EmptyState(
                icon_name="inbox",
                title="هنوز پیامی در این درس نیست",
                description="استاد هنوز پیامی منتشر نکرده است.",
                compact=True,
            )
            layout.addWidget(empty)
            self.tabs.setTabText(0, "📢 پیام‌ها")
            return

        for p in posts:
            card = PostCard(p)
            layout.addWidget(card)

        self.tabs.setTabText(0, f"📢 پیام‌ها ({len(posts)})")

    def _load_assignments(self) -> None:
        if not self._course:
            return

        layout = self.assignments_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                repo = AssignmentRepository(db)
                assignments = repo.get_by_course(self._course.group_id)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        if not assignments:
            empty = EmptyState(
                icon_name="clipboard-list",
                title="هنوز تکلیفی در این درس نیست",
                description="استاد هنوز تکلیفی برای این درس ثبت نکرده است.",
                compact=True,
            )
            layout.addWidget(empty)
            self.tabs.setTabText(1, "📋 تکالیف")
            return

        for a in assignments:
            card = AssignmentCard(a)
            layout.addWidget(card)

        self.tabs.setTabText(1, f"📋 تکالیف ({len(assignments)})")

    def _load_contents(self) -> None:
        if not self._course:
            return

        layout = self.contents_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                repo = ContentRepository(db)
                contents = repo.get_by_course(self._course.group_id)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        if not contents:
            empty = EmptyState(
                icon_name="file",
                title="هنوز فایلی در این درس نیست",
                description="استاد هنوز فایلی آپلود نکرده است.",
                compact=True,
            )
            layout.addWidget(empty)
            self.tabs.setTabText(3, "📄 فایل‌ها")
            return

        c = CurrentTheme.colors()

        for content in contents:
            frame = QFrame()
            frame.setObjectName("ContentRow")
            frame.setLayoutDirection(Qt.RightToLeft)

            row = QHBoxLayout(frame)
            row.setContentsMargins(18, 12, 18, 12)
            row.setSpacing(12)

            # آیکون نوع
            icon_char = "📄" if content.content_type == "pdf" else "📦"
            icon_label = QLabel(icon_char)
            icon_label.setStyleSheet(
                "font-size: 18pt; background: transparent;"
            )
            icon_label.setFixedWidth(30)
            row.addWidget(icon_label)

            # نام فایل
            name_label = QLabel(content.title)
            name_label.setStyleSheet(
                f"color: {c.TEXT_PRIMARY}; font-weight: bold; "
                "font-size: 11pt; background: transparent;"
            )
            name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            name_label.setWordWrap(True)
            row.addWidget(name_label, stretch=1)

            # نوع
            type_label = QLabel(content.content_type.upper())
            type_label.setStyleSheet(
                f"color: {c.TEXT_MUTED}; font-size: 9pt; "
                "background: transparent; font-weight: bold;"
            )
            type_label.setAlignment(Qt.AlignCenter)
            row.addWidget(type_label)

            # دانلود
            download_btn = QPushButton("⬇️ دانلود")
            download_btn.setObjectName("SecondaryButton")
            download_btn.setCursor(Qt.PointingHandCursor)
            download_btn.setMinimumWidth(100)
            download_btn.clicked.connect(
                lambda checked, u=content.url: QDesktopServices.openUrl(QUrl(u))
            )
            row.addWidget(download_btn)

            layout.addWidget(frame)

        self.tabs.setTabText(3, f"📄 فایل‌ها ({len(contents)})")

    # ⚠️ متدهای جدید - با تورفتگی درست (۴ فاصله)

    def _load_members(self) -> None:
        """بارگذاری همکلاسی‌ها."""
        if not self._course:
            return

        layout = self.members_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                from src.storage.repositories import MemberRepository
                from src.models.member import MemberType

                repo = MemberRepository(db)
                members = repo.get_by_course(self._course.group_id)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        # ⚠️ فیلتر بر اساس member_type
        students = [m for m in members if m.member_type == MemberType.STUDENT]
        teachers = [m for m in members if m.member_type == MemberType.TEACHER]
        support = [m for m in members if m.member_type == MemberType.SUPPORT]

        if not members:
            empty = EmptyState(
                icon_name="user",
                title="هنوز عضوی در این درس نیست",
                description="در Settings، گزینه‌ی «همکلاسی‌ها» رو روشن کن و Sync بزن.",
                compact=True,
            )
            layout.addWidget(empty)
            self.tabs.setTabText(2, "👥 همکلاسی‌ها")
            return

        c = CurrentTheme.colors()

        # === استادان ===
        if teachers:
            teacher_section = QLabel(f"👨‍🏫 استاد ({len(teachers)})")
            teacher_section.setStyleSheet(
                f"color: {c.TEXT_PRIMARY}; font-weight: bold; "
                "font-size: 12pt; padding: 10px 0;"
            )
            teacher_section.setAlignment(Qt.AlignRight)
            layout.addWidget(teacher_section)

            for t in teachers:
                layout.addWidget(self._make_member_row(t))

        # === همکلاسی‌ها ===
        if students:
            student_section = QLabel(f"👥 همکلاسی‌ها ({len(students)})")
            student_section.setStyleSheet(
                f"color: {c.TEXT_PRIMARY}; font-weight: bold; "
                "font-size: 12pt; padding: 10px 0;"
            )
            student_section.setAlignment(Qt.AlignRight)
            layout.addWidget(student_section)

            for s in students:
                layout.addWidget(self._make_member_row(s))

        self.tabs.setTabText(2, f"👥 همکلاسی‌ها ({len(students)})")

    def _make_member_row(self, member) -> QFrame:
        """ساخت ردیف یک عضو."""
        from src.models.member import MemberType

        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        frame = QFrame()
        frame.setObjectName("ContentRow")
        frame.setLayoutDirection(Qt.RightToLeft)

        row = QHBoxLayout(frame)
        row.setDirection(QHBoxLayout.RightToLeft)
        row.setContentsMargins(15, 10, 15, 10)
        row.setSpacing(12)

        # Avatar
        avatar = QLabel(member.name[0] if member.name else "?")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)

        # رنگ بر اساس نوع
        if member.member_type == MemberType.TEACHER:
            bg = "rgba(96, 165, 250, 0.25)" if is_dark else "rgba(59, 130, 246, 0.15)"
            color = c.PRIMARY
        elif member.member_type == MemberType.SUPPORT:
            bg = "rgba(251, 191, 36, 0.2)" if is_dark else "rgba(245, 158, 11, 0.1)"
            color = c.ACCENT
        else:  # STUDENT
            bg = "rgba(148, 163, 184, 0.2)" if is_dark else "rgba(100, 116, 139, 0.1)"
            color = c.TEXT_SECONDARY

        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                border-radius: 20px;
                font-size: 14pt;
                font-weight: bold;
            }}
        """)
        row.addWidget(avatar)

        # نام
        name_label = QLabel(member.name)
        name_label.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: 500; "
            "font-size: 11pt; background: transparent;"
        )
        name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(name_label, stretch=1)

        # دکمه‌ی مشاهده
        profile_btn = QPushButton("مشاهده")
        profile_btn.setObjectName("SecondaryButton")
        profile_btn.setCursor(Qt.PointingHandCursor)
        profile_btn.setFixedWidth(90)
        profile_btn.clicked.connect(
            lambda checked, u=member.profile_url: QDesktopServices.openUrl(QUrl(u))
        )
        row.addWidget(profile_btn)

        return frame