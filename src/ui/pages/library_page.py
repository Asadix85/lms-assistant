"""Library page (desktop): کتابخانه عمومی — فیچر اصلی روی نسخه وب است."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme, Radius


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class LibraryPage(BasePage):
    """صفحه کتابخانه در دسکتاپ — ارجاع به نسخه وب (جایی که محتوا عمومی و multi-user است)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            title="کتابخانه",
            subtitle="جزوه، آزمایش و لینک‌های مفید با تایید ادمین",
            parent=parent,
        )

    def _build(self) -> None:
        super()._build()

        card = QFrame()
        card.setObjectName("LibraryInfoCard")
        card.setStyleSheet(f"""
            QFrame#LibraryInfoCard {{
                background-color: {_c("GLASS_BG", "rgba(28,38,38,0.68)")};
                border: 1px solid {_c("GLASS_BORDER", "rgba(255,255,255,0.12)")};
                border-radius: {Radius.LG}px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(12)

        icon = QLabel("📚")
        icon.setAlignment(Qt.AlignRight)
        icon.setStyleSheet("font-size: 36pt; background: transparent;")
        lay.addWidget(icon)

        msg = QLabel(
            "کتابخانه یک فیچر <b>عمومی و چندکاربره</b> است:\n"
            "کاربران لینک جزوه و منبع می‌فرستند، ادمین تایید می‌کند،\n"
            "بقیه امتیاز و نظر می‌دهند و لینک‌های مرده را گزارش می‌کنند.\n\n"
            "به همین دلیل پیاده‌سازی اصلی روی <b>نسخه وب</b> است.\n"
            "از منوی «سایر امکانات» در وب، یا مستقیم از آدرس زیر وارد شوید."
        )
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignRight)
        msg.setTextFormat(Qt.RichText)
        msg.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#FFFFFF')}; font-size: 11pt; "
            f"background: transparent; line-height: 1.5;"
        )
        lay.addWidget(msg)

        row = QHBoxLayout()
        row.setDirection(QHBoxLayout.RightToLeft)
        btn = QPushButton("باز کردن کتابخانه در مرورگر")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(40)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_c("ACCENT", "#2AA6A3")};
                color: white;
                border: none;
                border-radius: {Radius.MD}px;
                font-weight: 700;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {_c("ACCENT_HOVER", "#3BBDBA")};
            }}
        """)
        # آدرس نسبی نسخه وب؛ اگر سرور محلی باشد کاربر می‌تواند تغییر دهد
        btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("http://127.0.0.1:8000/#/library"))
        )
        row.addWidget(btn)
        row.addStretch()
        lay.addLayout(row)

        note = QLabel(
            "نکته: اگر سرور وب را روی پورت دیگری اجرا کرده‌اید، آدرس را در مرورگر دستی باز کنید:\n"
            "…/#/library"
        )
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignRight)
        note.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 9pt; background: transparent;"
        )
        lay.addWidget(note)

        self.content_layout.addWidget(card)
        self.content_layout.addStretch()
