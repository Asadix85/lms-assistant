"""About Page: صفحه‌ی درباره من — با استایل مدرن iOS."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from src.ui.theme import CurrentTheme, Fonts


class InfoCard(QFrame):
    """کارت اطلاعات (برای ویژگی‌های تکنیکال)."""

    def __init__(
        self,
        icon: str,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon = icon
        self._title = title
        self._description = description
        self.setObjectName("Card")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(self._icon)
        icon_label.setStyleSheet("font-size: 28pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(icon_label)

        # Title
        title = QLabel(self._title)
        title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 12pt; "
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignRight)
        layout.addWidget(title)

        # Description
        desc = QLabel(self._description)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent;"
        )
        desc.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(desc)

        layout.addStretch()


class StatCard(QFrame):
    """کارت آماری کوچک."""

    def __init__(
        self,
        value: str,
        label: str,
        icon: str = "📊",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setObjectName("StatValue")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        label_widget = QLabel(label)
        label_widget.setObjectName("StatLabel")
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)


class SocialButton(QPushButton):
    """دکمه‌ی شبکه اجتماعی."""

    def __init__(
        self,
        text: str,
        url: str,
        icon: str = "🔗",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._url = url
        self.setText(f"{icon}  {text}")
        self.setObjectName("SecondaryButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.clicked.connect(self._on_click)

    def _on_click(self) -> None:
        if self._url:
            QDesktopServices.openUrl(QUrl(self._url))


class AboutPage(QWidget):
    """صفحه‌ی درباره من."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()
        f = Fonts

        # === Outer layout with scroll ===
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAttribute(Qt.WA_TranslucentBackground, True)

        content = QWidget()
        content.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ============================================
        # HERO SECTION (بطاقة بزرگ آبی)
        # ============================================
        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero.setMinimumHeight(220)

        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(40, 30, 40, 30)
        hero_layout.setSpacing(12)
        hero_layout.setAlignment(Qt.AlignCenter)

        # Avatar
        avatar = QLabel("👨‍💻")
        avatar.setStyleSheet("font-size: 48pt; background: transparent;")
        avatar.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(avatar)

        # Name
        name = QLabel("محمد اسدی")
        name.setStyleSheet(
            "font-size: 22pt; font-weight: bold; color: white; "
            "background: transparent;"
        )
        name.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(name)

        # Subtitle
        subtitle = QLabel("مهندسی کامپیوتر • ورودی ۱۴۰۴")
        subtitle.setStyleSheet(
            "font-size: 13pt; color: rgba(255, 255, 255, 0.95); "
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(subtitle)

        # University
        university = QLabel("🎓 دانشگاه اصفهان")
        university.setStyleSheet(
            "font-size: 11pt; color: rgba(255, 255, 255, 0.85); "
            "background: transparent; padding-top: 6px;"
        )
        university.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(university)

        layout.addWidget(hero)

        # ============================================
        # DESCRIPTION
        # ============================================
        desc_card = QFrame()
        desc_card.setObjectName("Card")

        desc_layout = QVBoxLayout(desc_card)
        desc_layout.setContentsMargins(24, 20, 24, 20)
        desc_layout.setSpacing(10)

        desc_title = QLabel("📖  درباره‌ی این پروژه")
        desc_title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent;"
        )
        desc_title.setAlignment(Qt.AlignRight)
        desc_layout.addWidget(desc_title)

        desc_text = QLabel(
            "LMS Assistant یک برنامه‌ی دسکتاپ شخصی است که به دانشجو امکان "
            "می‌دهد با یک کلیک، اطلاعات LMS دانشگاه اصفهان را دریافت و "
            "مدیریت کند.\n\n"
            "این برنامه به‌طور خودکار دروس، فایل‌ها، تکالیف و پیام‌های "
            "استادان را از LMS استخراج می‌کند، تغییرات جدید را تشخیص "
            "می‌دهد و به کاربر اطلاع می‌دهد.\n\n"
            "هدف: ساختن یک دستیار ساده، سریع و کاربردی که کارهای روزمره‌ی "
            "دانشجویی را آسان‌تر کند."
        )
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 11pt; line-height: 180%; "
            "background: transparent;"
        )
        desc_text.setAlignment(Qt.AlignRight)
        desc_layout.addWidget(desc_text)

        layout.addWidget(desc_card)

        # ============================================
        # TECHNICAL FEATURES (Grid of cards)
        # ============================================
        feat_title = QLabel("⚙️  ویژگی‌های فنی")
        feat_title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent; padding: 10px 5px 0 5px;"
        )
        feat_title.setAlignment(Qt.AlignRight)
        layout.addWidget(feat_title)

        # Row 1
        row1 = QHBoxLayout()
        row1.setSpacing(15)

        row1.addWidget(InfoCard(
            icon="🐍",
            title="Python + PySide6",
            description="ساخته شده با زبان پایتون و فریم‌ورک PySide6 (Qt)"
        ))
        row1.addWidget(InfoCard(
            icon="🍪",
            title="Multi-Domain SSO",
            description="پشتیبانی از lms3، lms4، lms5 با احراز هویت خودکار"
        ))
        row1.addWidget(InfoCard(
            icon="💾",
            title="SQLite Storage",
            description="ذخیره‌سازی محلی روی سیستم شما، بدون نیاز به سرور"
        ))

        layout.addLayout(row1)

        # Row 2
        row2 = QHBoxLayout()
        row2.setSpacing(15)

        row2.addWidget(InfoCard(
            icon="🔄",
            title="Change Detection",
            description="تشخیص خودکار موارد جدید بین Syncها"
        ))
        row2.addWidget(InfoCard(
            icon="📅",
            title="تقویم ددلاین‌ها",
            description="نمای هفتگی از مهلت تکالیف و رویدادهای مهم"
        ))
        row2.addWidget(InfoCard(
            icon="🎨",
            title="Liquid Glass UI",
            description="رابط کاربری مدرن با تم روشن و تیره"
        ))

        layout.addLayout(row2)

        # ============================================
        # STATS
        # ============================================
        stats_title = QLabel("📊  آمار پروژه")
        stats_title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent; padding: 10px 5px 0 5px;"
        )
        stats_title.setAlignment(Qt.AlignRight)
        layout.addWidget(stats_title)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        stats_row.addWidget(StatCard(value="۷", label="صفحه", icon="📄"))
        stats_row.addWidget(StatCard(value="۳", label="دامنه", icon="🌐"))
        stats_row.addWidget(StatCard(value="۲", label="تم", icon="🎨"))
        stats_row.addWidget(StatCard(value="۱۰۰٪", label="رایگان", icon="✨"))

        layout.addLayout(stats_row)

        # ============================================
        # CONTACT
        # ============================================
        contact_title = QLabel("📬  ارتباط")
        contact_title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent; padding: 10px 5px 0 5px;"
        )
        contact_title.setAlignment(Qt.AlignRight)
        layout.addWidget(contact_title)

        contact_row = QHBoxLayout()
        contact_row.setSpacing(10)

        contact_row.addWidget(SocialButton(
            text="GitHub",
            url="https://github.com/",
            icon="🐙",
        ))
        contact_row.addWidget(SocialButton(
            text="Telegram",
            url="https://t.me/",
            icon="✈️",
        ))
        contact_row.addWidget(SocialButton(
            text="ایمیل",
            url="mailto:example@example.com",
            icon="📧",
        ))
        contact_row.addStretch()

        layout.addLayout(contact_row)

        # ============================================
        # FOOTER
        # ============================================
        footer = QLabel(
            "LMS Assistant v0.1.0  •  ساخته شده با ❤️ برای دانشگاه اصفهان\n"
            "© ۱۴۰۵ — محمد اسدی"
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; "
            "background: transparent; padding: 20px 0 10px 0;"
        )
        layout.addWidget(footer)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        """بازخوانی — نیازی نیست."""
        pass