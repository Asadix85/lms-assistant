"""کارت مکان کلاس — ساده، بدون دیالوگ و با دکمه‌های مسیریابی مستقیم."""

from __future__ import annotations

from urllib.parse import quote

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap, QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.models.locations import get_location
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class ClassLocationCard(QFrame):
    """کارت مکان کلاس — نقشه استاتیک + اطلاعات + دکمه‌های مسیریابی مستقیم."""

    def __init__(self, location_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.location_text = location_text or "مکان نامشخص"
        self.loc_data = get_location(self.location_text)

        self.setObjectName("Card")
        self.setLayoutDirection(Qt.RightToLeft)

        bg_col = _c('GLASS_BG', 'rgba(28, 38, 38, 0.68)')
        border_col = _c('GLASS_BORDER', 'rgba(255, 255, 255, 0.1)')

        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 12px;
            }}
            QFrame#Card:hover {{
                border: 1px solid {_c('GLASS_BORDER_HOVER', 'rgba(78, 205, 196, 0.45)')};
            }}
        """)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(16)

        # --- سمت چپ: نقشه کوچک (استاتیک) ---
        self.map_preview = QLabel()
        self.map_preview.setFixedSize(140, 90)
        self.map_preview.setAlignment(Qt.AlignCenter)

        bg_secondary = _c('BG_HOVER', 'rgba(44, 54, 54, 0.85)')
        self.map_preview.setStyleSheet(f"background-color: {bg_secondary}; border-radius: 8px; color: {_c('TEXT_MUTED', '#8E8E93')};")
        self.map_preview.setText("🗺️ نقشه")

        if self.loc_data:
            lat, lng = self.loc_data.lat, self.loc_data.lng
            url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lng}&zoom=16&size=280x180&maptype=mapnik&markers={lat},{lng},red-pushpin"
            self._load_map_preview(url)

        lay.addWidget(self.map_preview)

        # --- سمت راست: اطلاعات و دکمه‌ها ---
        info_col = QVBoxLayout()
        info_col.setSpacing(8)

        # نام دانشکده
        faculty_name = self.loc_data.name if self.loc_data else "دانشکده نامشخص"
        title = QLabel(faculty_name)
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {_c('TEXT_PRIMARY', '#FFFFFF')}; font-weight: bold; font-size: 11pt; background: transparent; border: none;")
        info_col.addWidget(title)

        # نام ساختمان / کلاس
        building_name = self.loc_data.building if self.loc_data else self.location_text
        subtitle = QLabel(building_name)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {_c('TEXT_SECONDARY', '#EBEBF5')}; font-size: 9.5pt; background: transparent; border: none;")
        info_col.addWidget(subtitle)

        info_col.addStretch()

        # دکمه‌های مسیریابی
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        neshan_btn = QPushButton("🧭 نشان")
        neshan_btn.setCursor(Qt.PointingHandCursor)
        neshan_btn.setFixedHeight(32)
        neshan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_c('BG_SECONDARY', '#2C2C2C')};
                color: {_c('TEXT_PRIMARY', '#FFFFFF')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(255,255,255,0.1)')};
                border-radius: 6px;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {_c('PRIMARY', '#2AA6A3')};
                color: white;
            }}
        """)
        neshan_btn.clicked.connect(self._open_neshan)

        google_btn = QPushButton("🗺 گوگل مپ")
        google_btn.setCursor(Qt.PointingHandCursor)
        google_btn.setFixedHeight(32)
        google_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_c('BG_SECONDARY', '#2C2C2C')};
                color: {_c('TEXT_PRIMARY', '#FFFFFF')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(255,255,255,0.1)')};
                border-radius: 6px;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {_c('PRIMARY', '#2AA6A3')};
                color: white;
            }}
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
            self.map_preview.setText("خطا در بارگذاری")
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