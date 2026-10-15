"""Post Card: کارت نمایش یک پیام wall — نسخه‌ی بازطراحی‌شده (خفن!)."""

from __future__ import annotations

import re

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

from src.models.post import Post
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class PostCard(QFrame):
    """کارت پیام با آواتار گرادیانتی، هدر زیبا و پشتیبانی از پیوست."""

    def __init__(self, post: Post, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._post = post
        self.setObjectName("PostCard")
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # === هدر با گرادینت ملایم ===
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.08)')},
                    stop:1 transparent);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }}
        """)
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(18, 14, 18, 14)
        header_lay.setSpacing(12)

        # آواتار گرادیانتی
        author_name = self._post.author or "کاربر"
        initial = author_name[0] if author_name else "?"
        avatar = QLabel(initial)
        avatar.setFixedSize(42, 42)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {_c('PRIMARY', '#2AA6A3')},
                    stop:1 {_c('PRIMARY_DARK', '#1E807E')});
                color: #FFFFFF;
                border-radius: 21px;
                font-size: 14pt;
                font-weight: 800;
            }}
        """)
        header_lay.addWidget(avatar)

        # اطلاعات نویسنده
        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        author_lbl = QLabel(author_name)
        author_lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 10.5pt; "
            "font-weight: 700; background: transparent;"
        )
        info_col.addWidget(author_lbl)

        date_text = self._post.posted_at_jalali or "—"
        date_lbl = QLabel(date_text)
        date_lbl.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8.5pt; background: transparent;"
        )
        info_col.addWidget(date_lbl)
        header_lay.addLayout(info_col, stretch=1)

        # آیکون پیام
        msg_icon = QLabel("💬")
        msg_icon.setStyleSheet("font-size: 14pt; background: transparent;")
        header_lay.addWidget(msg_icon)
        lay.addWidget(header)

        # === بدنه پیام ===
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(18, 14, 18, 14)
        body_lay.setSpacing(10)

        text_lbl = QLabel(self._linkify(self._post.text))
        text_lbl.setWordWrap(True)
        text_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text_lbl.setOpenExternalLinks(True)
        text_lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 10pt; "
            "line-height: 1.6; background: transparent;"
        )
        body_lay.addWidget(text_lbl)

        # === پیوست‌ها (اگر بودند) ===
        if hasattr(self._post, 'attachments') and self._post.attachments:
            attach_row = QHBoxLayout()
            attach_row.setSpacing(8)

            for att in self._post.attachments[:3]:  # حداکثر ۳ تا
                att_btn = self._make_attachment_chip(att)
                attach_row.addWidget(att_btn)

            if len(self._post.attachments) > 3:
                more = QLabel(f"+{len(self._post.attachments) - 3}")
                more.setStyleSheet(
                    f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8pt; background: transparent;"
                )
                attach_row.addWidget(more)

            attach_row.addStretch()
            body_lay.addLayout(attach_row)

        lay.addWidget(body)

        # افکت hover
        self.setStyleSheet(f"""
            QFrame#PostCard {{
                background-color: {_c('GLASS_BG', 'rgba(255,255,255,0.68)')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
            QFrame#PostCard:hover {{
                background-color: {_c('GLASS_BG_HOVER', 'rgba(255,255,255,0.85)')};
                border-color: {_c('GLASS_BORDER_HOVER', 'rgba(42,166,163,0.35)')};
            }}
        """)

    def _linkify(self, text: str) -> str:
        """تبدیل URL ها به لینک قابل کلیک."""
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
        return re.sub(url_pattern, r'<a href="\1" style="color: #2AA6A3; text-decoration: none;">\1</a>', text)

    def _make_attachment_chip(self, attachment) -> QPushButton:
        """چیپ پیوست با آیکون بر اساس نوع."""
        name = getattr(attachment, 'name', 'فایل')
        ext = name.split('.')[-1].lower() if '.' in name else ''

        icon_map = {
            'pdf': ('📄', '#FF3B30'),
            'zip': ('📦', '#FF9500'),
            'rar': ('📦', '#FF9500'),
            'mp4': ('🎬', '#3B8EA5'),
            'jpg': ('🖼️', '#34C759'),
            'png': ('🖼️', '#34C759'),
        }
        icon, color = icon_map.get(ext, ('📎', _c('PRIMARY', '#2AA6A3')))

        btn = QPushButton(f"{icon}  {name[:20]}{'...' if len(name) > 20 else ''}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}15;
                color: {color};
                border: 1px solid {color}30;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 8.5pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {color}25;
            }}
        """)

        url = getattr(attachment, 'url', '')
        if url:
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        return btn

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._build()