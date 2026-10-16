"""Course Detail Page: صفحه‌ی جزئیات یک درس — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal, QTimer, QUrl
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.course import Course
from src.models.member import MemberType
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    MemberRepository,
    PostRepository,
)
from src.storage.repositories.course_schedule_repo import CourseScheduleRepository
from src.ui.theme import CurrentTheme
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.widgets.course_info_card import CourseInfoCard
from src.ui.widgets.course_stats_cards import CourseStatsCards
from src.ui.widgets.post_card import PostCard
from src.ui.widgets.schedule_card import ScheduleCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CourseDetailPage(QWidget):
    """صفحه‌ی جزئیات یک درس — Hero گرادیانتی + تب‌های مدرن."""

    back_clicked = Signal()

    DOMAIN_META = {
        "lms3": ("🟢", "علوم پایه"),
        "lms4": ("🔵", "فنی-مهندسی"),
        "lms5": ("🔴", "اداری-تربیتی"),
    }
    FILE_META = {
        "pdf": ("📄", "#FF3B30", "rgba(255, 59, 48, 0.12)"),
        "zip": ("📦", "#FF9500", "rgba(255, 149, 0, 0.12)"),
        "rar": ("📦", "#FF9500", "rgba(255, 149, 0, 0.12)"),
        "mp4": ("🎬", "#3B8EA5", "rgba(59, 142, 165, 0.12)"),
        "video": ("🎬", "#3B8EA5", "rgba(59, 142, 165, 0.12)"),
    }

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db_path = db_path
        self._course: Course | None = None
        self._anims: list = []
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self._build()

    # --------------------------------------------------------
    #  اسکلت
    # --------------------------------------------------------

    def _build(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)

        # === ردیف بالا: بازگشت + breadcrumb ===
        head = QHBoxLayout()
        head.setSpacing(12)

        back_btn = QPushButton("→")
        back_btn.setObjectName("SecondaryButton")
        back_btn.setFixedSize(40, 40)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(
            "QPushButton { border-radius: 20px; font-size: 13pt; font-weight: 700; }"
        )
        back_btn.clicked.connect(self.back_clicked.emit)
        head.addWidget(back_btn)

        self.breadcrumb = QLabel("دروس")
        self.breadcrumb.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 9.5pt; background: transparent;"
        )
        head.addWidget(self.breadcrumb)
        head.addStretch()
        layout.addLayout(head)

        # === Hero ===
        self.hero = QFrame()
        self.hero.setObjectName("HeroCard")
        self.hero.setMinimumHeight(150)

        hero_lay = QHBoxLayout(self.hero)
        hero_lay.setContentsMargins(28, 22, 28, 22)
        hero_lay.setSpacing(18)

        text_col = QVBoxLayout()
        text_col.setSpacing(12)

        self.course_title = QLabel("—")
        self.course_title.setObjectName("HeroTitle")
        self.course_title.setWordWrap(True)
        self.course_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        text_col.addWidget(self.course_title)

        self.meta_row = QHBoxLayout()
        self.meta_row.setSpacing(8)
        text_col.addLayout(self.meta_row)
        text_col.addStretch()
        hero_lay.addLayout(text_col, stretch=1)

        self.hero_deco = QLabel("📚")
        self.hero_deco.setFixedSize(96, 96)
        self.hero_deco.setAlignment(Qt.AlignCenter)
        self.hero_deco.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.16); "
            "border-radius: 48px; font-size: 40pt;"
        )
        hero_lay.addWidget(self.hero_deco)
        layout.addWidget(self.hero)

        # === کارت استاد + آمار ===
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        self.info_card_container = QWidget()
        self.info_card_container.setAttribute(Qt.WA_TranslucentBackground, True)
        QVBoxLayout(self.info_card_container).setContentsMargins(0, 0, 0, 0)

        self.stats_container = QWidget()
        self.stats_container.setAttribute(Qt.WA_TranslucentBackground, True)
        QVBoxLayout(self.stats_container).setContentsMargins(0, 0, 0, 0)

        cards_row.addWidget(self.info_card_container, stretch=1)
        cards_row.addWidget(self.stats_container, stretch=2)
        layout.addLayout(cards_row)

        # === تب‌ها ===
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.RightToLeft)
        self.tabs.setDocumentMode(True)
        self._style_tabs()

        self.posts_container = self._build_tab_container()
        self.tabs.addTab(self.posts_container, "📢 پیام‌ها")
        self.assignments_container = self._build_tab_container()
        self.tabs.addTab(self.assignments_container, "📋 تکالیف")
        self.members_container = self._build_tab_container()
        self.tabs.addTab(self.members_container, "👥 همکلاسی‌ها")
        self.contents_container = self._build_tab_container()
        self.tabs.addTab(self.contents_container, "📄 فایل‌ها")
        self.schedule_container = self._build_tab_container()
        self.tabs.addTab(self.schedule_container, "📅 برنامه کلاس")

        layout.addWidget(self.tabs, stretch=1)

    def _style_tabs(self) -> None:
        c = CurrentTheme.colors()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; top: -1px; }}
            QTabBar {{ background: transparent; }}
            QTabBar::tab {{
                background: {c.GLASS_BG};
                color: {c.TEXT_SECONDARY};
                padding: 10px 20px;
                margin-left: 6px;
                border: 1px solid {c.GLASS_BORDER};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 10pt;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {c.PRIMARY};
                color: {c.TEXT_WHITE};
                border-color: {c.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background: {c.GLASS_BG_HOVER};
                color: {c.PRIMARY};
                border-color: {c.GLASS_BORDER_HOVER};
            }}
        """)

    def _build_tab_container(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAttribute(Qt.WA_TranslucentBackground, True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        widget = QWidget()
        widget.setAttribute(Qt.WA_TranslucentBackground, True)
        lay = QVBoxLayout(widget)
        lay.setSpacing(10)
        lay.setContentsMargins(6, 12, 6, 12)
        lay.setAlignment(Qt.AlignTop)
        scroll.setWidget(widget)
        scroll._content_layout = lay
        return scroll

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _fade(self, widget: QWidget, delay: int = 0) -> None:
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anims.append(anim)
        QTimer.singleShot(delay, anim.start)

    def _hero_chip(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFixedHeight(28)
        lbl.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.18); color: #FFFFFF; "
            "border-radius: 14px; padding: 0 14px; font-size: 9pt; font-weight: 600;"
        )
        return lbl

    def _tab_empty(self, icon: str, title: str, desc: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"font-size: 34pt; color: {_c('TEXT_MUTED', '#8E8E93')}; background: transparent;")
        lay.addWidget(ic)

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 11.5pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(t)

        d = QLabel(desc)
        d.setAlignment(Qt.AlignCenter)
        d.setWordWrap(True)
        d.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9.5pt; background: transparent;"
        )
        lay.addWidget(d)
        return w

    # --------------------------------------------------------
    #  بارگذاری داده
    # --------------------------------------------------------

    def refresh_theme(self) -> None:
        """بعد از تغییر تم — بازسازی کامل صفحه با گرادیانت/رنگ‌های تم جدید.

        ⚠️ باگ قبلی: این متد وجود نداشت؛ به همین دلیل Hero، تب‌ها و کارت‌ها
        بعد از سوییچ تم با رنگ‌های تم قدیمی رندر می‌ماندند.
        """
        self._style_tabs()
        if getattr(self, "_course", None):
            self.load_course(self._course)

    def load_course(self, course: Course) -> None:
        self._course = course
        self._anims.clear()
        # ⚠️ رفع باگ رندرِ دوباره‌ی Hero در تم تیره:
        # انیمیشن opacity از طریق QGraphicsOpacityEffect شفافیت کل ویجت را
        # دستکاری می‌کند و بعد از تغییر تم باعث مات/نامرئی شدن متن روی
        # گرادیانت Hero می‌شد. در نتیجه Hero بدون fade و مستقیم نمایش داده
        # می‌شود و فقط کارت‌های پایینی انیمیشن ورود پلکانی دارند.
        self.hero.setVisible(True)
        if hasattr(self, "_hero_effect"):
            self.hero.setGraphicsEffect(None)
            self._hero_effect = None

        icon, domain_fa = self.DOMAIN_META.get(course.domain, ("⚪", course.domain))
        self.course_title.setText(course.name)
        self.hero_deco.setText(icon)
        self.breadcrumb.setText(f"دروس  /  {course.name}")

        # چیپ‌های روی Hero
        self._clear_layout(self.meta_row)
        self.meta_row.addWidget(self._hero_chip(f"🌐 {domain_fa}"))
        if course.code:
            self.meta_row.addWidget(self._hero_chip(f"📋 {course.code}"))
        if course.term:
            self.meta_row.addWidget(self._hero_chip(f"📅 ترم {course.term}"))
        self.meta_row.addStretch()

        # کارت استاد + آمار
        self._clear_layout(self.info_card_container.layout())
        self.info_card_container.layout().addWidget(CourseInfoCard(course))

        self._clear_layout(self.stats_container.layout())
        self.stats_container.layout().addWidget(
            CourseStatsCards(self.db_path, course.group_id)
        )

        self._load_posts()
        self._load_assignments()
        self._load_members()
        self._load_contents()
        self._load_schedule()
        self.tabs.setCurrentIndex(0)

        # انیمیشن ورود پلکانی (Hero حذف شد — به‌دلیل باگ opacity در تم تیره)
        self._fade(self.info_card_container, 80)
        self._fade(self.stats_container, 140)
        self._fade(self.tabs, 200)

    # --- تب پیام‌ها ---
    def _load_posts(self) -> None:
        if not self._course:
            return
        lay = self.posts_container._content_layout
        self._clear_layout(lay)
        try:
            with Database(self.db_path) as db:
                posts = PostRepository(db).get_by_course(self._course.group_id, limit=50)
        except Exception as e:
            lay.addWidget(QLabel(f"خطا: {e}"))
            return
        if not posts:
            lay.addWidget(self._tab_empty("📢", "هنوز پیامی نیست", "استاد هنوز پیامی منتشر نکرده است."))
            self.tabs.setTabText(0, "📢 پیام‌ها")
            return
        for p in posts:
            lay.addWidget(PostCard(p))
        self.tabs.setTabText(0, f"📢 پیام‌ها ({self._to_fa(len(posts))})")

    # --- تب تکالیف ---
    def _load_assignments(self) -> None:
        if not self._course:
            return
        lay = self.assignments_container._content_layout
        self._clear_layout(lay)
        try:
            with Database(self.db_path) as db:
                assignments = AssignmentRepository(db).get_by_course(self._course.group_id)
        except Exception as e:
            lay.addWidget(QLabel(f"خطا: {e}"))
            return
        if not assignments:
            lay.addWidget(self._tab_empty("📋", "هنوز تکلیفی نیست", "استاد تکلیفی برای این درس ثبت نکرده است."))
            self.tabs.setTabText(1, "📋 تکالیف")
            return
        for a in assignments:
            lay.addWidget(AssignmentCard(a))
        self.tabs.setTabText(1, f"📋 تکالیف ({self._to_fa(len(assignments))})")

    # --- تب همکلاسی‌ها ---
    def _load_members(self) -> None:
        if not self._course:
            return
        lay = self.members_container._content_layout
        self._clear_layout(lay)
        try:
            with Database(self.db_path) as db:
                members = MemberRepository(db).get_by_course(self._course.group_id)
        except Exception as e:
            lay.addWidget(QLabel(f"خطا: {e}"))
            return

        students = [m for m in members if m.member_type == MemberType.STUDENT]
        teachers = [m for m in members if m.member_type == MemberType.TEACHER]
        support = [m for m in members if m.member_type == MemberType.SUPPORT]

        if not members:
            lay.addWidget(self._tab_empty(
                "👥", "هنوز عضوی نیست",
                "در تنظیمات، گزینه‌ی «همکلاسی‌ها» رو روشن کن و Sync بزن.",
            ))
            self.tabs.setTabText(2, "👥 همکلاسی‌ها")
            return

        if teachers:
            lay.addWidget(self._member_section("👨‍ استاد", len(teachers)))
            for t in teachers:
                lay.addWidget(self._make_member_row(t))
        if support:
            lay.addWidget(self._member_section("🛟 پشتیبان", len(support)))
            for s in support:
                lay.addWidget(self._make_member_row(s))
        if students:
            lay.addWidget(self._member_section("👥 همکلاسی‌ها", len(students)))
            for s in students:
                lay.addWidget(self._make_member_row(s))

        self.tabs.setTabText(2, f"👥 همکلاسی‌ها ({self._to_fa(len(students))})")

    def _member_section(self, title: str, count: int) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(4, 12, 4, 4)
        row.setSpacing(8)

        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 800; "
            "font-size: 11.5pt; background: transparent;"
        )
        row.addWidget(lbl)

        pill = QLabel(self._to_fa(count))
        pill.setAlignment(Qt.AlignCenter)
        pill.setFixedSize(26, 22)
        pill.setStyleSheet(
            f"color: {_c('PRIMARY', '#2AA6A3')}; "
            f"background-color: {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.12)')}; "
            "border-radius: 11px; font-size: 9pt; font-weight: 700;"
        )
        row.addWidget(pill)
        row.addStretch()
        return w

    def _make_member_row(self, member) -> QFrame:
        c = CurrentTheme.colors()
        frame = QFrame()
        frame.setObjectName("ContentRow")
        frame.setLayoutDirection(Qt.RightToLeft)

        row = QHBoxLayout(frame)
        row.setContentsMargins(15, 10, 15, 10)
        row.setSpacing(12)

        # متادیتای نقش
        if member.member_type == MemberType.TEACHER:
            role, av_style = "استاد", (
                f"background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {c.PRIMARY}, stop:1 {c.PRIMARY_DARK});"
                "color: #FFFFFF;"
            )
        elif member.member_type == MemberType.SUPPORT:
            role, av_style = "پشتیبان", (
                f"background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {c.ACCENT}, stop:1 {c.ACCENT_DARK});"
                "color: #FFFFFF;"
            )
        else:
            role, av_style = "دانشجو", (
                f"background-color: {c.BG_HOVER}; color: {c.TEXT_SECONDARY};"
            )

        avatar = QLabel(member.name[0] if member.name else "?")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(av_style + "border-radius: 20px; font-size: 13pt; font-weight: 700;")
        row.addWidget(avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_lbl = QLabel(member.name)
        name_lbl.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: 600; font-size: 10.5pt; background: transparent;"
        )
        name_col.addWidget(name_lbl)
        role_lbl = QLabel(role)
        role_lbl.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 8.5pt; background: transparent;"
        )
        name_col.addWidget(role_lbl)
        row.addLayout(name_col, stretch=1)

        btn = QPushButton("مشاهده")
        btn.setObjectName("SecondaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(84, 32)
        btn.clicked.connect(
            lambda _checked, u=member.profile_url: QDesktopServices.openUrl(QUrl(u))
        )
        row.addWidget(btn)
        return frame

    # --- تب فایل‌ها ---
    def _load_contents(self) -> None:
        if not self._course:
            return
        lay = self.contents_container._content_layout
        self._clear_layout(lay)
        try:
            with Database(self.db_path) as db:
                contents = ContentRepository(db).get_by_course(self._course.group_id)
        except Exception as e:
            lay.addWidget(QLabel(f"خطا: {e}"))
            return
        if not contents:
            lay.addWidget(self._tab_empty("📄", "هنوز فایلی نیست", "استاد فایلی آپلود نکرده است."))
            self.tabs.setTabText(3, "📄 فایل‌ها")
            return

        c = CurrentTheme.colors()
        for content in contents:
            icon, fg, bg = self.FILE_META.get(
                content.content_type,
                ("📎", c.PRIMARY, c.PRIMARY_LIGHT),
            )
            frame = QFrame()
            frame.setObjectName("ContentRow")
            frame.setLayoutDirection(Qt.RightToLeft)

            row = QHBoxLayout(frame)
            row.setContentsMargins(15, 10, 15, 10)
            row.setSpacing(12)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedSize(40, 40)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(f"background-color: {bg}; border-radius: 12px; font-size: 14pt;")
            row.addWidget(icon_lbl)

            name_lbl = QLabel(content.title)
            name_lbl.setWordWrap(True)
            name_lbl.setStyleSheet(
                f"color: {c.TEXT_PRIMARY}; font-weight: 600; font-size: 10.5pt; background: transparent;"
            )
            row.addWidget(name_lbl, stretch=1)

            type_lbl = QLabel(content.content_type.upper())
            type_lbl.setFixedHeight(24)
            type_lbl.setAlignment(Qt.AlignCenter)
            type_lbl.setStyleSheet(
                f"color: {fg}; background-color: {bg}; border-radius: 8px; "
                "padding: 0 10px; font-size: 8pt; font-weight: 700;"
            )
            row.addWidget(type_lbl)

            dl_btn = QPushButton("⬇")
            dl_btn.setObjectName("SecondaryButton")
            dl_btn.setCursor(Qt.PointingHandCursor)
            dl_btn.setFixedSize(36, 36)
            dl_btn.setStyleSheet("QPushButton { border-radius: 18px; font-size: 11pt; }")
            dl_btn.clicked.connect(
                lambda _checked, u=content.url: QDesktopServices.openUrl(QUrl(u))
            )
            row.addWidget(dl_btn)

            lay.addWidget(frame)

        self.tabs.setTabText(3, f"📄 فایل‌ها ({self._to_fa(len(contents))})")

    # --- تب برنامه کلاس ---
    def _load_schedule(self) -> None:
        if not self._course:
            return
        lay = self.schedule_container._content_layout
        self._clear_layout(lay)
        try:
            with Database(self.db_path) as db:
                schedule = CourseScheduleRepository(db).get_by_id(self._course.group_id)
        except Exception as e:
            lay.addWidget(QLabel(f"خطا: {e}"))
            return
        if not schedule or not schedule.sessions:
            lay.addWidget(self._tab_empty(
                "📅", "برنامه‌ای ثبت نشده",
                "اطلاعات زمان و مکان کلاس در دسترس نیست. یک Sync جدید بزن.",
            ))
            self.tabs.setTabText(4, "📅 برنامه کلاس")
            return
        for session in schedule.sessions:
            lay.addWidget(ScheduleCard(session))
        self.tabs.setTabText(4, f"📅 برنامه کلاس ({self._to_fa(len(schedule.sessions))})")

    @staticmethod
    def _to_fa(n: int) -> str:
        fa = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa[int(d)] for d in str(n))