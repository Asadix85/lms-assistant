"""کارت ادغام‌شده برنامه کلاس — زمان + مکان + دکمه‌های مسیریابی."""

from __future__ import annotations

from urllib.parse import quote

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap, QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.models.course_schedule import ClassSession
from src.models.locations import get_location
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class ScheduleLocationCard(QFrame):
    """کارت ادغام‌شده: نمایش روز/ساعت در کنار مکان دقیق (ساختمان + کلاس) و مسیریابی."""

    def __init__(self, session: ClassSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        # این متغیر حالا حاوی کل متن مکان از LMS است (مثلا: ساختمان فنی قدیم - کلاس 13 - طبقه دوم)
        self.location_text = getattr(session, "location", "") or getattr(session, "room", "")
        self.loc_data = get_location(self.location_text)

        self.setObjectName("Card")
        self.setLayoutDirection(Qt.RightToLeft)

        bg_col = _c('GLASS_BG', 'rgba(28, 38, 38, 0.68)')
        border_col = _c('GLASS_BORDER', 'rgba(255, 255, 255, 0.1)')

        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 14px;
            }}
            QFrame#Card:hover {{
                border: 1px solid {_c('GLASS_BORDER_HOVER', 'rgba(78, 205, 196, 0.45)')};
            }}
        """)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(16)

        # === بخش راست: زمان و روز ===
        time_col = QVBoxLayout()
        time_col.setSpacing(4)
        time_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        weekday_lbl = QLabel(self.session.weekday)
        weekday_lbl.setStyleSheet(f"color: {_c('PRIMARY', '#2AA6A3')}; font-weight: bold; font-size: 12pt; background: transparent; border: none;")
        time_col.addWidget(weekday_lbl)

        time_text = f"{self.session.start_time} - {self.session.end_time}"
        time_lbl = QLabel(time_text)
        time_lbl.setStyleSheet(f"color: {_c('TEXT_PRIMARY', '#FFFFFF')}; font-weight: 600; font-size: 11pt; background: transparent; border: none;")
        time_col.addWidget(time_lbl)

        lay.addLayout(time_col)

        # خط عمودی جداکننده
        v_line = QFrame()
        v_line.setFrameShape(QFrame.VLine)
        v_line.setStyleSheet(f"color: {_c('GLASS_BORDER', 'rgba(255,255,255,0.1)')};")
        lay.addWidget(v_line)

        # === بخش چپ: نقشه، نام دانشکده و مکان دقیق ===
        self.map_preview = QLabel()
        self.map_preview.setFixedSize(90, 65)
        self.map_preview.setAlignment(Qt.AlignCenter)

        bg_secondary = _c('BG_HOVER', 'rgba(44, 54, 54, 0.85)')
        self.map_preview.setStyleSheet(f"background-color: {bg_secondary}; border-radius: 6px; color: {_c('TEXT_MUTED', '#8E8E93')};")
        self.map_preview.setText("🗺️")

        if self.loc_data:
            lat, lng = self.loc_data.lat, self.loc_data.lng
            url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lng}&zoom=16&size=180x130&maptype=mapnik&markers={lat},{lng},red-pushpin"
            self._load_map_preview(url)

        lay.addWidget(self.map_preview)

        # اطلاعات متنی
        info_col = QVBoxLayout()
        info_col.setSpacing(4)

        # ۱. نام دانشکده (از دیکشنری مکان‌ها)
        faculty_name = self.loc_data.name if self.loc_data else "مکان نامشخص"
        title = QLabel(faculty_name)
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {_c('TEXT_PRIMARY', '#FFFFFF')}; font-weight: bold; font-size: 11pt; background: transparent; border: none;")
        info_col.addWidget(title)

        # ۲. مکان دقیق (شماره کلاس و طبقه که از LMS آمده)
        # از self.location_text استفاده می‌کنیم تا دقیقاً همان چیزی که در LMS است نمایش داده شود
        subtitle = QLabel(self.location_text)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {_c('TEXT_SECONDARY', '#EBEBF5')}; font-size: 9.5pt; background: transparent; border: none;")
        info_col.addWidget(subtitle)

        info_col.addStretch()

        # دکمه‌های مسیریابی
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        neshan_btn = QPushButton("🧭 نشان")
        neshan_btn.setCursor(Qt.PointingHandCursor)
        neshan_btn.setFixedHeight(28)
        neshan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_c('BG_SECONDARY', '#2C2C2C')};
                color: {_c('TEXT_PRIMARY', '#FFFFFF')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(255,255,255,0.1)')};
                border-radius: 6px;
                font-size: 8.5pt;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {_c('PRIMARY', '#2AA6A3')}; color: white; }}
        """)
        neshan_btn.clicked.connect(self._open_neshan)

        google_btn = QPushButton("🗺 گوگل مپ")
        google_btn.setCursor(Qt.PointingHandCursor)
        google_btn.setFixedHeight(28)
        google_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_c('BG_SECONDARY', '#2C2C2C')};
                color: {_c('TEXT_PRIMARY', '#FFFFFF')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(255,255,255,0.1)')};
                border-radius: 6px;
                font-size: 8.5pt;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {_c('PRIMARY', '#2AA6A3')}; color: white; }}
        """)
        google_btn.clicked.connect(self._open_google_maps)

        btn_row.addWidget(neshan_btn)
        btn_row.addWidget(google_btn)
        info_col.addLayout(btn_row)

        lay.addLayout(info_col, stretch=1)

    def _load_map_preview(self, url: str) -> None:
        self.nam = QNetworkAccessManager(self)
        req = QNetworkRequest(QUrl(url))
        req.setHeader(QNetworkRequest.UserAgentHeader, "LMSAssistant/1.0")
        self.reply = self.nam.get(req)
        self.reply.finished.connect(self._on_map_loaded)

    def _on_map_loaded(self) -> None:
        if self.reply.error() == QNetworkReply.NetworkError.NoError:
            data = self.reply.readAll()
            img = QImage.fromData(data)
            if not img.isNull():
                pix = QPixmap.fromImage(img)
                self.map_preview.setPixmap(pix.scaled(self.map_preview.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.map_preview.setText("❌")
        self.reply.deleteLater()

    def _open_neshan(self) -> None:
        lat = self.loc_data.lat if self.loc_data else 32.6072163
        lng = self.loc_data.lng if self.loc_data else 51.6583164
        url = f"https://nshn.ir/?lat={lat}&lng={lng}"
        QDesktopServices.openUrl(QUrl(url))

    def _open_google_maps(self) -> None:
        lat = self.loc_data.lat if self.loc_data else 32.6072163
        lng = self.loc_data.lng if self.loc_data else 51.6583164
        dest = f"{lat},{lng}"
        url = f"https://www.google.com/maps/dir/?api=1&destination={quote(dest)}&travelmode=driving"
        QDesktopServices.openUrl(QUrl(url))