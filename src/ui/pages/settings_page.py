from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
    QPoint,
)
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

from config.settings import settings
from src.storage.database import Database
from src.storage.repositories import CourseRepository, SettingRepository
from src.ui.pages.base_page import BasePage
from src.ui.rtl import mark_ltr
from src.ui.theme import CurrentTheme
from src.ui.widgets.setting_card import SettingCard


def _c(name: str, fallback: str) -> str:
    """خواندن امن رنگ از تم فعلی."""
    return str(getattr(CurrentTheme.colors(), name, fallback))


# ============================================================
#  ویجت‌های اختصاصی صفحه
# ============================================================

class _SectionHeader(QWidget):
    """سربرگ گروه: آیکون در باکس رنگی + عنوان + توضیح کوتاه."""

    def __init__(self, icon: str, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 15, 0, 10)
        lay.setSpacing(15)

        # آیکون با سایه و گرادینت ملایم
        icon_container = QWidget()
        icon_container.setFixedSize(44, 44)
        icon_lay = QVBoxLayout(icon_container)
        icon_lay.setContentsMargins(0, 0, 0, 0)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {_c('PRIMARY', '#4F6EF7')}; color: #FFFFFF;"
            "border-radius: 14px; font-size: 16pt;"
        )
        # سایه نرم برای آیکون
        shadow = QGraphicsDropShadowEffect(icon_lbl)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(_c('PRIMARY', '#4F6EF7')))
        shadow.setOffset(0, 4)
        icon_lbl.setGraphicsEffect(shadow)

        icon_lay.addWidget(icon_lbl)
        lay.addWidget(icon_container)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1E293B')}; font-size: 14pt;"
            "font-weight: 800; background: transparent;"
        )
        text_col.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(
                f"color: {_c('TEXT_SECONDARY', '#64748B')}; font-size: 9.5pt;"
                "background: transparent;"
            )
            text_col.addWidget(sub_lbl)

        lay.addLayout(text_col)
        lay.addStretch()


class _SyncTile(QFrame):
    """تایل قابل‌کلیک برای انتخاب آیتم‌های سینک."""

    toggled = Signal(bool)

    def __init__(
        self,
        icon: str,
        title: str,
        subtitle: str = "",
        checked: bool = False,
        enabled: bool = True,
        badge: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._checked = checked
        self._enabled = enabled
        self._anim_scale = None

        self.setObjectName("SyncTile")
        self.setProperty("checked", checked)
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ForbiddenCursor)
        self.setMinimumHeight(70)
        self.setMaximumHeight(80)

        if not enabled:
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.5)
            self.setGraphicsEffect(eff)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(14)

        # آیکون
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {_c('BG_HOVER', '#F1F5F9')};"
            f"color: {_c('TEXT_PRIMARY', '#1E293B')};"
            "border-radius: 12px; font-size: 15pt;"
        )
        lay.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1E293B')}; font-size: 11pt;"
            "font-weight: 700; background: transparent;"
        )
        title_row.addWidget(title_lbl)

        if badge:
            badge_lbl = QLabel(badge)
            badge_lbl.setObjectName("TileBadge")
            badge_lbl.setStyleSheet(
                f"color: {_c('PRIMARY', '#4F6EF7')};"
                f"border: 1px solid {_c('PRIMARY', '#4F6EF7')};"
                "border-radius: 6px; padding: 2px 8px; font-size: 8pt;"
                "font-weight: 600; background: transparent;"
            )
            title_row.addWidget(badge_lbl)
        title_row.addStretch()
        text_col.addLayout(title_row)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(
                f"color: {_c('TEXT_SECONDARY', '#64748B')}; font-size: 9pt;"
                "background: transparent;"
            )
            text_col.addWidget(sub_lbl)
        lay.addLayout(text_col, stretch=1)

        # چک‌مارک
        self.check_dot = QLabel("✓")
        self.check_dot.setFixedSize(26, 26)
        self.check_dot.setAlignment(Qt.AlignCenter)
        self.check_dot.setVisible(checked)
        self.check_dot.setStyleSheet(
            f"background-color: {_c('PRIMARY', '#4F6EF7')}; color: #FFFFFF;"
            "border-radius: 13px; font-size: 12pt; font-weight: bold;"
        )
        lay.addWidget(self.check_dot)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool) -> None:
        if value == self._checked:
            return
        self._checked = value
        self.setProperty("checked", value)
        self.style().unpolish(self)
        self.style().polish(self)
        self.check_dot.setVisible(value)
        self.toggled.emit(value)

    def mousePressEvent(self, event) -> None:
        if self._enabled and event.button() == Qt.LeftButton:
            # انیمیشن فشار کوچک
            self._anim_scale = QPropertyAnimation(self, b"geometry")
            # اینجا فقط برای فیدبک بصری ساده، در پروژه‌های بزرگتر از GraphicsEffect استفاده میشه
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if self._enabled:
            self.setStyleSheet(self.styleSheet() + f"border-color: {_c('PRIMARY', '#4F6EF7')};")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._enabled:
            self.setStyleSheet("") # Reset to object name style
        super().leaveEvent(event)


class _StatusPill(QLabel):
    """برچسب وضعیت گرد."""

    def __init__(self, text: str, kind: str = "muted", parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusPill")
        self.setProperty("kind", kind)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(28)
        # فونت کمی ضخیم‌تر
        f = self.font()
        f.setBold(True)
        self.setFont(f)


class _ThemeSwitch(QToolButton):
    """سوییچ پیل‌مانند برای تغییر تم."""

    def __init__(self, dark: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("ThemeSwitch")
        self.setCheckable(True)
        self.setChecked(dark)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(140, 40)
        self._sync_text()
        self.toggled.connect(lambda _c: self._sync_text())

    def _sync_text(self) -> None:
        self.setText("🌙  تم تیره" if self.isChecked() else "☀️  تم روشن")


class _EstimateBar(QWidget):
    """نوار متحرک زمان تقریبی سینک."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)
        self._fraction = 0.19
        self._label = ""
        self._anim = None

    def get_fraction(self) -> float:
        return self._fraction

    def set_fraction(self, value: float) -> None:
        self._fraction = value
        self.update()

    fraction = Property(float, get_fraction, set_fraction)

    def set_value(self, seconds: int, max_seconds: int = 42, animate: bool = True) -> None:
        target = max(0.06, min(1.0, seconds / max_seconds))

        if seconds > 90:
            minutes, secs = divmod(seconds, 60)
            text = f"حدود {minutes} دقیقه و {secs} ثانیه"
        elif seconds == 8:
            text = "حدود ۸ ثانیه — سریع‌ترین حالت ⚡"
        else:
            text = f"حدود {seconds} ثانیه"

        self._label = f"⏱  زمان تقریبی: {text}"

        if animate and abs(target - self._fraction) > 0.001:
            if self._anim:
                self._anim.stop()
            self._anim = QPropertyAnimation(self, b"fraction", self)
            self._anim.setDuration(400)
            self._anim.setStartValue(self._fraction)
            self._anim.setEndValue(target)
            self._anim.setEasingCurve(QEasingCurve.OutBack) # انیمیشن فنری جذاب‌تر
            self._anim.start()
        else:
            self.set_fraction(target)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        primary = QColor(_c("PRIMARY", "#4F6EF7"))
        track = QColor(_c("BORDER_LIGHT", "#E2E8F0"))
        text_col = QColor(_c("TEXT_SECONDARY", "#64748B"))

        w, h = self.width(), self.height()

        # متن
        p.setPen(QPen(text_col))
        f = p.font()
        f.setPointSize(9)
        f.setBold(True)
        p.setFont(f)
        p.drawText(0, 0, w, h - 20, Qt.AlignRight | Qt.AlignVCenter, self._label)

        # نوار پیشرفت
        bar_h = 10
        y = h - bar_h - 5

        # پس‌زمینه نوار
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, y, w, bar_h, 5, 5)

        # پرشدگی نوار با گرادینت
        fw = int(w * self._fraction)
        if fw > 0:
            gradient = QLinearGradient(w - fw, y, w, y)
            gradient.setColorAt(0, primary.darker(110))
            gradient.setColorAt(1, primary)
            p.setBrush(gradient)
            p.drawRoundedRect(w - fw, y, fw, bar_h, 5, 5)

        p.end()


# ============================================================
#  صفحه‌ی تنظیمات
# ============================================================

class SettingsPage(BasePage):
    """صفحه‌ی تنظیمات — طراحی مدرن گروه‌بندی‌شده."""

    settings_changed = Signal()
    theme_changed = Signal()

    SYNC_SECONDS = {"contents": 7, "events": 1, "wall": 7, "members": 19}
    BASE_SECONDS = 8

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._first_build = True
        self._anims: list = []
        self._sync_tiles: dict[str, _SyncTile] = {}
        super().__init__(
            title="تنظیمات",
            subtitle="پیکربندی برنامه",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        outer = QHBoxLayout(self.scroll_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        inner = QWidget()
        inner.setMaximumWidth(900)
        self.scroll_layout = QVBoxLayout(inner)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setContentsMargins(10, 10, 10, 40)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        outer.addWidget(inner)
        outer.addStretch(1)
        scroll.setWidget(self.scroll_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def refresh(self) -> None:
        self._anims.clear()
        self._sync_tiles = {}

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._build_account_section()
        self._build_sync_section()
        self._build_notifications_section()
        self._build_appearance_section()
        self._build_data_section()
        self._build_about_section()
        self.scroll_layout.addStretch()

        if self._first_build:
            self._animate_cards()
            self._first_build = False

    def _fix_rtl(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)
        for obj in ("PageTitle", "PageSubtitle"):
            lbl = self.findChild(QLabel, obj)
            if lbl:
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _animate_cards(self) -> None:
        index = 0
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is None:
                continue
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            self._anims.append(anim)
            # تاخیر بیشتر برای حس آبشاری
            QTimer.singleShot(index * 80, anim.start)
            index += 1

    def _btn(self, text: str, object_name: str, slot, icon: str | None = None) -> QPushButton:
        btn = QPushButton((f"{icon}  " if icon else "") + text)
        btn.setObjectName(object_name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        # سایه کوچک برای دکمه‌ها
        shadow = QGraphicsDropShadowEffect(btn)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        btn.setGraphicsEffect(shadow)
        return btn

    def _wrap(self, layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(
            f"background-color: {_c('BORDER_LIGHT', '#E2E8F0')};"
            "max-height: 1px; border: none;"
        )
        return line

    def _info_box(self, text: str, hint: bool = False) -> QLabel:
        c = CurrentTheme.colors()
        box = QLabel(text)
        box.setWordWrap(True)
        bg = _c("BG_HOVER", "#F1F5F9")
        fg = _c("TEXT_MUTED", "#94A3B8") if hint else _c("TEXT_SECONDARY", "#64748B")

        # بوردر رنگی سمت چپ برای جذابیت
        border_color = _c("PRIMARY", "#4F6EF7") if not hint else _c("TEXT_MUTED", "#94A3B8")

        box.setStyleSheet(
            f"color: {fg}; background-color: {bg}; border-radius: 12px;"
            f"border-left: 4px solid {border_color}; "
            "padding: 12px 16px; font-size: 9.5pt; line-height: 1.5;"
        )
        return box

    # --------------------------------------------------------
    #  بخش‌ها (Account, Sync, etc) - همان منطق قبلی با ویجت‌های جدید
    # --------------------------------------------------------

    def _build_account_section(self) -> None:
        self.scroll_layout.addWidget(_SectionHeader(
            "👤", "حساب کاربری", "اطلاعات ورود و وضعیت همگام‌سازی"
        ))

        username = settings.lms_username or "—"
        last_sync, first_sync, domains_str = "—", "false", "—"
        try:
            with Database(self.db_path) as db:
                last_sync = SettingRepository(db).get("last_sync_at", "—")
                first_sync = SettingRepository(db).get("first_sync_done", "false")
                courses = CourseRepository(db).get_all()
                domains = sorted({c.domain for c in courses})
                if domains:
                    domains_str = "، ".join(domains)
        except Exception:
            pass
        if last_sync and last_sync != "—":
            last_sync = last_sync[:19].replace("T", " ")

        card = SettingCard(title="پروفایل", icon="")
        card.add_row("نام کاربری", username)
        card.add_row("آخرین سینک", last_sync)
        card.add_row("اولین سینک",
                     "✅ انجام شده" if first_sync == "true" else "❌ انجام نشده")
        card.add_row("دامنه‌ها", domains_str)
        self.scroll_layout.addWidget(card)

        from src.services.credential_provider import CredentialProvider
        creds = CredentialProvider.get()
        card = SettingCard(title="اطلاعات ورود", icon="🔐")
        card.add_row("نام کاربری LMS", creds.lms_username or "—")
        if creds.quera_username:
            card.add_row("نام کاربری Quera", creds.quera_username)

        card.add_widget(self._divider())

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btns.addWidget(self._btn("تغییر رمز", "SecondaryButton",
                                 self._on_change_password, "🔄"))
        btns.addWidget(self._btn("خروج از حساب", "DangerButton",
                                 self._on_logout, "🚪"))
        btns.addStretch()
        card.add_widget(self._wrap(btns))
        self.scroll_layout.addWidget(card)

    def _on_change_password(self) -> None:
        from src.services.credential_provider import CredentialProvider
        from src.ui.dialogs.login_dialog import LoginDialog

        creds = CredentialProvider.get()
        dialog = LoginDialog(
            self,
            lms_username=creds.lms_username,
            lms_password="",
            quera_username=creds.quera_username,
            quera_password="",
        )
        dialog.login_success.connect(
            lambda lu, lp, qu, qp: CredentialProvider.update(lu, lp, qu, qp)
        )
        if dialog.exec() == LoginDialog.Accepted:
            QMessageBox.information(self, "موفق", "اطلاعات ذخیره شد.")
            self.refresh()

    def _on_logout(self) -> None:
        from src.services.credential_provider import CredentialProvider
        from src.services.credentials_manager import CredentialsManager

        reply = QMessageBox.question(
            self, "خروج از حساب",
            "اطلاعات ورود حذف می‌شود. مطمئن هستی؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        CredentialsManager.clear_all()
        CredentialProvider.reset()
        QMessageBox.information(
            self, "خروج",
            "اطلاعات حذف شد. برنامه را ببند و دوباره باز کن.",
        )
        self.refresh()

    def _build_sync_section(self) -> None:
        from src.services.settings_manager import SettingsManager

        self.scroll_layout.addWidget(_SectionHeader(
            "🔄", "همگام‌سازی", "انتخاب کن چه داده‌هایی از LMS دریافت شوند"
        ))

        sync = SettingsManager.get_sync_settings()

        card = SettingCard(title="گزینه‌های سینک", icon="")
        card.add_widget(self._info_box(
            "هرچه گزینه‌ی بیشتری فعال باشد، سینک طولانی‌تر می‌شود.\n"
            "دروس همیشه دریافت می‌شوند و غیرقابل‌تغییرند."
        ))

        tiles_cfg = [
            ("courses",  "📚", "دروس",              "فهرست دروس ترم",                 True,  False, "اجباری"),
            ("contents", "📄", "فایل‌ها و محتوا",   "فایل‌ها و منابع هر درس",          True,  True,  ""),
            ("events",   "📅", "رویدادها",          "جلسات آنلاین و ددلاین‌ها",        True,  True,  ""),
            ("wall",     "📢", "پیام‌ها و تکالیف",  "wall هر درس",                     True,  True,  ""),
            ("members",  "👥", "همکلاسی‌ها",        "لیست اعضای دروس — کندتر",       False, True,  ""),
        ]

        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (key, icon, title, sub, checked, enabled, badge) in enumerate(tiles_cfg):
            tile = _SyncTile(icon, title, sub,
                             checked=checked if key != "courses" else True,
                             enabled=enabled, badge=badge)
            tile.toggled.connect(lambda _c, k=key: self._on_sync_option_changed(k))
            self._sync_tiles[key] = tile
            grid.addWidget(tile, i // 2, i % 2)

        card.add_widget(self._wrap(grid))

        self.estimate_bar = _EstimateBar()
        card.add_widget(self.estimate_bar)
        self._update_time_estimate(animate=False)

        self.scroll_layout.addWidget(card)

    def _on_sync_option_changed(self, _key: str | None = None) -> None:
        from src.services.settings_manager import SettingsManager

        values = {k: t.isChecked() for k, t in self._sync_tiles.items()}
        SettingsManager.save_sync_settings(values)
        self._update_time_estimate()

    def _update_time_estimate(self, animate: bool = True) -> None:
        seconds = self.BASE_SECONDS
        for key, extra in self.SYNC_SECONDS.items():
            tile = self._sync_tiles.get(key)
            if tile and tile.isChecked():
                seconds += extra
        self.estimate_bar.set_value(seconds, animate=animate)

    def _build_notifications_section(self) -> None:
        from src.services.credentials_manager import CredentialsManager

        self.scroll_layout.addWidget(_SectionHeader(
            "🔔", "اعلان‌ها", "دریافت هشدارها از طریق تلگرام"
        ))

        saved_id = CredentialsManager.get_telegram_chat_id()

        card = SettingCard(title="ربات تلگرام", icon="📱")
        card.add_widget(self._info_box(
            "برای دریافت نوتیفیکیشن‌ها، Chat ID خود را وارد کن.\n"
            "این اتصال از ربات مشترک برنامه استفاده می‌کند."
        ))
        card.add_widget(self._info_box(
            "📖 راهنما:\n"
            "۱. در تلگرام به @userinfobot برو\n"
            "۲. /start بزن\n"
            "۳. عدد Id را کپی کن\n"
            "۴. اینجا paste کن و «ذخیره» را بزن", hint=True))

        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        lbl = QLabel("💬 Chat ID")
        lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1E293B')}; font-size: 10pt;"
            "font-weight: 600; background: transparent;"
        )
        input_row.addWidget(lbl)

        self.telegram_input = QLineEdit()
        self.telegram_input.setPlaceholderText("مثلاً: 1837366891")
        self.telegram_input.setMinimumHeight(44)
        # Chat ID تلگرام عدد/متن لاتین است → عمداً LTR می‌ماند تا
        # apply_rtl_recursive آن را راست‌تراز و معکوس نکند.
        mark_ltr(self.telegram_input)
        self.telegram_input.setAlignment(Qt.AlignLeft)
        self.telegram_input.setText(saved_id or "")
        self.telegram_input.textChanged.connect(self._on_telegram_input_changed)
        input_row.addWidget(self.telegram_input, stretch=1)
        card.add_widget(self._wrap(input_row))

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btns.addWidget(self._btn("تست اتصال", "SecondaryButton",
                                 self._on_telegram_test, "🧪"))
        btns.addWidget(self._btn("ذخیره", "PrimaryButton",
                                 self._on_telegram_save, "💾"))
        btns.addWidget(self._btn("حذف", "DangerButton",
                                 self._on_telegram_delete, "🗑️"))
        btns.addStretch()
        card.add_widget(self._wrap(btns))

        pill = _StatusPill(
            f"✅ متصل — {saved_id}" if saved_id else "❌ متصل نیست",
            "success" if saved_id else "muted",
        )
        status_row = QHBoxLayout()
        status_row.addStretch()
        status_row.addWidget(pill)
        card.add_widget(self._wrap(status_row))

        self.scroll_layout.addWidget(card)

    def _on_telegram_input_changed(self, text: str) -> None:
        cleaned = "".join(ch for ch in text if ch.isdigit() or ch == "-")
        if cleaned != text:
            self.telegram_input.setText(cleaned)

    def _on_telegram_test(self) -> None:
        from src.services.telegram_tester import TelegramTester

        chat_id = self.telegram_input.text().strip()
        if not chat_id:
            QMessageBox.warning(self, "خطا", "Chat ID را وارد کن.")
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ok, message = TelegramTester.test_connection(chat_id)
        finally:
            QApplication.restoreOverrideCursor()
        (QMessageBox.information if ok else QMessageBox.critical)(self, "نتیجه", message)

    def _on_telegram_save(self) -> None:
        from src.services.credentials_manager import CredentialsManager

        chat_id = self.telegram_input.text().strip()
        if not chat_id:
            QMessageBox.warning(self, "خطا", "Chat ID را وارد کن.")
            return
        if CredentialsManager.save_telegram_chat_id(chat_id):
            QMessageBox.information(self, "موفق", "Chat ID ذخیره شد.")
            self.refresh()
        else:
            QMessageBox.critical(self, "خطا", "ذخیره ناموفق بود.")

    def _on_telegram_delete(self) -> None:
        from src.services.credentials_manager import CredentialsManager

        reply = QMessageBox.question(
            self, "حذف", "Chat ID حذف شود؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        CredentialsManager.delete_telegram_chat_id()
        self.refresh()

    def _build_appearance_section(self) -> None:
        self.scroll_layout.addWidget(_SectionHeader(
            "🎨", "ظاهر", "شخصی‌سازی رابط کاربری"
        ))

        card = SettingCard(title="تم برنامه", icon="")
        row = QHBoxLayout()
        row.setSpacing(16)

        desc = QLabel("تغییر بلافاصله و بدون نیاز به ری‌استارت اعمال می‌شود.")
        desc.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#64748B')}; font-size: 9.5pt;"
            "background: transparent;"
        )
        row.addWidget(desc, stretch=1)

        self.theme_switch = _ThemeSwitch(dark=CurrentTheme.is_dark())
        self.theme_switch.toggled.connect(self._on_theme_toggle)
        row.addWidget(self.theme_switch)

        card.add_widget(self._wrap(row))
        self.scroll_layout.addWidget(card)

    def _on_theme_toggle(self, checked: bool) -> None:
        from src.services.settings_manager import SettingsManager
        from src.ui.blur import enable_blur
        from src.ui.icons import Icons
        from src.ui.theme import (
            CurrentTheme,
            ThemeMode,
            apply_rtl_recursive,
            get_global_qss,
        )

        new_mode = ThemeMode.DARK if checked else ThemeMode.LIGHT
        CurrentTheme.set_mode(new_mode)
        SettingsManager.save_theme(new_mode)

        Icons.clear_cache()

        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_global_qss(new_mode))

        main_window = self.window()
        if main_window:
            color = 0xFA0A0A0F if CurrentTheme.is_dark() else 0xFAF8FAFC
            enable_blur(main_window, color=color, enable=True)
            if hasattr(main_window, "sidebar"):
                main_window.sidebar.refresh_icons()

        # ✅ refresh خود settings page
        self.refresh()

        # ✅ refresh همه صفحات دیگر
        if main_window and hasattr(main_window, 'refresh_all_pages_theme'):
            main_window.refresh_all_pages_theme()

        if main_window:
            QTimer.singleShot(
                50, lambda: self._apply_rtl_to_window(main_window))

    def _apply_rtl_to_window(self, window) -> None:
        from src.ui.theme import apply_rtl_recursive
        apply_rtl_recursive(window)
        for part in ("sidebar", "header"):
            if hasattr(window, part):
                apply_rtl_recursive(getattr(window, part))
        if hasattr(window, "stack"):
            current = window.stack.currentWidget()
            if current:
                apply_rtl_recursive(current)

    def _build_data_section(self) -> None:
        self.scroll_layout.addWidget(_SectionHeader(
            "💾", "داده‌ها", "مدیریت دیتابیس محلی"
        ))

        db_path = Path(self.db_path)
        if db_path.exists():
            size = db_path.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 ** 2:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 ** 2):.1f} MB"
        else:
            size_str = "—"

        card = SettingCard(title="دیتابیس", icon="")
        card.add_row("حجم", size_str)
        card.add_row("مسیر", str(db_path.absolute()))

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btns.addWidget(self._btn("بکاپ", "SecondaryButton",
                                 self._on_backup, "📦"))
        btns.addWidget(self._btn("پاک کردن دیتابیس", "DangerButton",
                                 self._on_clear_db, "🗑️"))
        btns.addStretch()
        card.add_widget(self._wrap(btns))

        self.scroll_layout.addWidget(card)

    def _on_backup(self) -> None:
        src = Path(self.db_path)
        if not src.exists():
            QMessageBox.warning(self, "خطا", "دیتابیس پیدا نشد.")
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "ذخیره بکاپ",
            str(src.parent / "lms_backup.db"),
            "Database (*.db)",
        )
        if not dest:
            return
        try:
            shutil.copy2(src, dest)
            QMessageBox.information(self, "✅ موفق", f"بکاپ ذخیره شد:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بکاپ:\n{e}")

    def _on_clear_db(self) -> None:
        reply = QMessageBox.question(
            self, "🗑️ پاک کردن دیتابیس",
            "همه‌ی داده‌ها پاک می‌شوند و باید دوباره سینک بزنی.\nمطمئن هستی؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            db_path = Path(self.db_path)
            if db_path.exists():
                db_path.unlink()
            QMessageBox.information(self, "موفق", "دیتابیس پاک شد.")
            self.refresh()
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در پاک کردن:\n{e}")

    def _build_about_section(self) -> None:
        self.scroll_layout.addWidget(_SectionHeader("ℹ️", "درباره"))

        card = SettingCard(title="", icon="")

        col = QVBoxLayout()
        col.setSpacing(12)
        col.setContentsMargins(20, 20, 20, 20)

        name = QLabel("LMS Desktop")
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1E293B')}; font-size: 18pt;"
            "font-weight: 900; background: transparent;"
        )
        col.addWidget(name)

        version_row = QHBoxLayout()
        version_row.addStretch()
        version_row.addWidget(_StatusPill("v0.1.0", "info"))
        version_row.addWidget(_StatusPill("دانشگاه اصفهان", "muted"))
        version_row.addStretch()
        col.addLayout(version_row)

        desc = QLabel("کلاینت دسکتاپ شخصی برای مدیریت دروس، فایل‌ها و ددلاین‌های LMS")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#64748B')}; font-size: 10pt;"
            "background: transparent;"
        )
        col.addWidget(desc)

        repo = QLabel("https://github.com/Asadix85")
        repo.setAlignment(Qt.AlignCenter)
        repo.setStyleSheet(
            f"color: {_c('PRIMARY', '#4F6EF7')}; font-size: 10pt;"
            "background: transparent;"
        )
        col.addWidget(repo)

        card.add_widget(self._wrap(col))
        self.scroll_layout.addWidget(card)