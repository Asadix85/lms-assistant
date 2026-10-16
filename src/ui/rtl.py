"""زیرساخت مرکزی RTL برای کل رابط کاربری.

چرا این ماژول لازم است؟
در Qt، جهت چیدمان (LayoutDirection) به‌صورت "ميراثی" از والد به فرزندان
جاری می‌شود — اما دو حالت وجود دارد که در آن میراث قطع می‌شود و عناصر
سمت‌چپ می‌مانند:

1. ویجت‌هایی که بعداً به صفحه اضافه می‌شوند (کارت‌های داینامیک، ردیف‌های
   جدول، لیست‌های پس از همگام‌سازی) — اگر در زمان ساخت، والد نداشتند،
   جهت پیش‌فرض چپ‌به‌راست را گرفته و دیگر تصحیح نمی‌شوند.
2. توست‌ها (Toasts)، دیالوگ‌ها و منوهایی که مستقیماً فرزند پنجره اصلی
   نیستند یا parent=None ساخته می‌شوند.

راه‌حل سه‌لایه:
- لایه ۱ (اپلیکیشن): ``app.setLayoutDirection(RightToLeft)`` + فیلتر رویداد
  QEvent.ChildAdded در ``install_rtl_event_filter(app)`` که هر ویجت جدیدی
  را بلافاصله RTL می‌کند (هزینه O(1) در هر افزودن).
- لایه ۲ (ویجت‌ها): کلاس پایه ``RTLWidgetMixin`` که در ``__init__`` خودش
  را RTL می‌کند — حتی وقتی parent ندارد (مثل Toast).
- لایه ۳ (تمیزسازی): ``apply_rtl_recursive`` با اصلاحات زیر نسبت به نسخه
  قبلی: حفظ AlignCenter، احترام به فلگ صریح LTR (برای ساعت/عدد لاتین)،
  و اعمال LayoutDirection روی خود layoutها.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPersistentModelIndex,
    Qt,
    QTranslator,
)
from PySide6.QtGui import QAbstractTextDocumentLayout, QPalette, QTextDocument
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def is_ltr_forced(widget: QWidget) -> bool:
    """آیا روی ویجت به‌صورت صریح «LTR بمان» علامت زده شده است؟

    برای عناصری مثل ساعت (14:30)، شماره تلفن، Chat ID تلگرام و متن‌های
    لاتین باید Qt.AlignLeft | Qt.LayoutDirectionMixed ست شود تا توابع RTL
    آن‌ها را دست‌نخورده رها کنند.
    """
    return bool(widget.property("_rtl_force_ltr"))


def mark_ltr(widget: QWidget) -> QWidget:
    """علامت‌گذاری یک ویجت برای ماندن در حالت چپ‌به‌راست (ساعت/عدد لاتین)."""
    widget.setProperty("_rtl_force_ltr", True)
    widget.setLayoutDirection(Qt.LeftToRight)
    return widget


class RTLWidgetMixin:
    """میکسین RTL برای همه ویجت‌های سفارشی (کارت‌ها، توست‌ها، دیالوگ‌ها).

    استفاده::

        class CourseCard(RTLWidgetMixin, QFrame):
            ...

    ترتیب MRO مهم است: میکسین باید قبل از کلاس پایه Qt بیاید.
    با فراخوانی معمول ``super().__init__(parent)`` در کلاس فرزند نیز
    درست کار می‌کند (parent=None ارسال نمی‌شود).
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not is_ltr_forced(self):
            self.setLayoutDirection(Qt.RightToLeft)


def ensure_rtl(widget: QWidget) -> QWidget:
    """RTL کردن یک ویجت خاص به‌همراه فرزندان مستقیم موجود (بدون دست‌زدن
    به AlignCenter و موارد mark_ltr شده). برای کارت‌هایی که در زمان ساخت
    parent ندارند کافی است؛ فیلتر ChildAdded بقیه را می‌گیرد."""
    _apply_one(widget)
    for child in widget.findChildren(QWidget):
        _apply_one(child)
    return widget


class RTLLabel(QLabel):
    """برچسب RTL-aware: مرکزِ خالی (AlignCenter) حفظ می‌شود و فقط برچسب‌های
    واقعاً سمت‌چپ به راست منتقل می‌گردند. با فلگ صریح LTR کار نمی‌کند."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setLayoutDirection(Qt.RightToLeft)
        # راست‌تراز کردن اولیه فقط اگر کاربر align نداده باشد
        if not (self.alignment() & Qt.AlignHorizontal_Mask):
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def setAlignment(self, flag) -> None:  # noqa: N802 (APIQt)
        super().setAlignment(flag)
        # اگر صراحتاً LTR خواسته شد، جهت چیدمان را هم قفل کن
        if isinstance(flag, int) and flag & Qt.AlignLeft:
            self.setProperty("_rtl_force_ltr", True)
            self.setLayoutDirection(Qt.LeftToRight)


class _ChildAddedFilter(QObject):
    """فیلتر رویداد: هر ویجت تازه‌متولد/منتقل‌شده را فوری RTL می‌کند.

    این فیلتر روی QApplication نصب می‌شود و مشکل «کارت‌های داینامیک
    سمت‌چپ» را ریشه‌ای حل می‌کند — بدون نیاز به فراخوانی دستی بعد از
    هر addWidget.
    """

    def eventFilter(self, obj, event) -> bool:  # noqa: ANN001
        if event.type() == QEvent.ChildAdded:
            child = event.child()
            if isinstance(child, QWidget):
                w: QWidget = child
                if not is_ltr_forced(w):
                    w.setLayoutDirection(Qt.RightToLeft)
                    # children-i که داخل layout خودشان ساخته شده‌اند هنوز
                    # parent ندارند؛ یک پاس کوچک روی مستقیم‌ترین فرزندانشان
                    for sub in w.findChildren(QWidget):
                        if not is_ltr_forced(sub):
                            sub.setLayoutDirection(Qt.RightToLeft)
        return False


def install_rtl_event_filter(app) -> _ChildAddedFilter:
    """نصب فیلتر ChildAdded روی کل اپلیکیشن. یک‌بار در نقطه ورود صدا زده شود."""
    f = _ChildAddedFilter(app)
    app.installEventFilter(f)
    return f


def load_qt_translations(app) -> None:
    """بارگذاری ترجمه رسمی Qt فارسی (OK/Cancel/… و نام ماه‌های شمسی).

    فایل‌های qm در مجله‌ی translations کنار PySide6 بسته‌شده‌اند. اگر
    پیدا نشوند بی‌صدا رد می‌شویم (مثلاً در محیط تست).
    """
    import sys
    from pathlib import Path

    candidates: list[Path] = []
    try:
        import PySide6

        pkg_dir = Path(PySide6.__file__).parent / "translations"
        candidates.append(pkg_dir)
    except Exception:
        pass
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates.append(base / "_internal" / "PySide6" / "translations")
        candidates.append(base / "translations")

    translator = QTranslator(app)
    for d in candidates:
        for name in ("qtbase_fa", "qt_fa"):
            f = d / f"{name}.qm"
            if f.exists() and translator.load(str(f)):
                app.installTranslator(translator)
                return


def apply_rtl_recursive(widget: QWidget | None) -> None:
    """اعمال RTL روی ویجت و همه فرزندان — نسخه اصلاح‌شده.

    تفاوت‌های کلیدی با نسخه قبلی:
    - AlignCenter دیگر خراب نمی‌شود (نسخه قبلی با ماسک AlignRight،
      مرکزِ آیکون‌ها/پیل‌ها/بَج‌ها را به راست می‌پراند).
    - ویجت‌های علامت‌گذاری‌شده با ``mark_ltr`` (ساعت، عدد لاتین، Chat ID)
      دست‌نخورده می‌مانند.
    - LayoutDirection روی خودِ layout آبجکت‌ها هم ست می‌شود (سازگار با
      QSS و رفتار صحیح stretch در Fusion).
    - تراز پیش‌فرض برچسب خالی → راست (نه اینکه تغییر نکند).
    """
    if widget is None:
        return

    _apply_one(widget)
    for child in widget.findChildren(QWidget):
        _apply_one(child)

    # layoutهای داخلی (روی خود widget و فرزندان)
    applied_layouts: set[int] = set()
    for holder in [widget, *widget.findChildren(QWidget)]:
        lay = holder.layout()
        while lay is not None and id(lay) not in applied_layouts:
            applied_layouts.add(id(lay))
            _set_layout_direction(lay, holder)
            parent_item = lay.parent()
            lay = parent_item.layout() if parent_item is not None else None


def _set_layout_direction(lay, holder: QWidget) -> None:
    """ست کردن جهت layout با سازگاری کامل PySide6.

    نکته مهم: QBoxLayout (V/HBox) متد ``setDirection`` را دارد که فقط
    ``QBoxLayout.Direction`` (TopToBottom/LeftToRight/...) می‌پذیرد و ست
    کردن ``Qt.LayoutDirection`` روی آن TypeError می‌دهد. برای همه layoutها
    روش امن و یکسان، ست کردن ``setLayoutDirection(Qt.LayoutDirection)``
    است که در QLayout پایه وجود دارد و رفتار RTL صحیحی هم می‌دهد.
    """
    direction = (
        Qt.RightToLeft
        if holder.layoutDirection() == Qt.RightToLeft
        else Qt.LeftToRight
    )
    try:
        # روش استاندارد و امن برای همه نوع layout (QVBoxLayout/QHBoxLayout/
        # QGridLayout/QFormLayout/...) — در PySide6 و PyQt هر دو پشتیبانی می‌شود
        lay.setLayoutDirection(direction)
    except (AttributeError, TypeError):
        # fallback: اگر نسخه‌ای setLayoutDirection را نداشته باشد، فقط برای
        # layoutهایی که واقعا Qt.LayoutDirection می‌پذیرند امتحان کن
        setter = getattr(lay, "setDirection", None)
        if setter is not None:
            try:
                setter(direction)
            except TypeError:
                # QBoxLayout.setDirection انتظار QBoxLayout.Direction دارد؛
                # تغییر جهت نمی‌دهد → نادیده بگیر (setLayoutDirection کافی است)
                pass


def _apply_one(w: QWidget) -> None:
    if is_ltr_forced(w):
        return

    w.setLayoutDirection(Qt.RightToLeft)

    # لیبل‌ها: فقط افقی را عوض کن، عمودی و center حفظ شود
    if isinstance(w, QLabel):
        a = w.alignment()
        if not a & Qt.AlignHorizontal_Mask or a & Qt.AlignLeft:
            w.setAlignment((a & ~Qt.AlignHorizontal_Mask) | Qt.AlignRight)

    elif isinstance(w, (QLineEdit, QTextEdit, QPlainTextEdit)):
        doc = _document_of(w)
        if doc is not None:
            doc.setDefaultTextOption(_persian_text_option(doc.defaultTextOption()))
        a = w.alignment()
        if not a & Qt.AlignHorizontal_Mask or a & Qt.AlignLeft:
            w.setAlignment((a & ~Qt.AlignHorizontal_Mask) | Qt.AlignRight)

    elif isinstance(w, QCheckBox):
        # تیک‌باکس RTL: جعبه در سمت راست متن
        w.setLayoutDirection(Qt.RightToLeft)

    elif isinstance(w, QRadioButton):
        w.setLayoutDirection(Qt.RightToLeft)

    elif isinstance(w, QComboBox):
        w.setLayoutDirection(Qt.RightToLeft)

    elif isinstance(w, QAbstractItemView):
        header = w.horizontalHeader()
        if header is not None:
            header.setLayoutDirection(Qt.RightToLeft)
        v = w.verticalScrollBar()
        h = w.horizontalScrollBar()
        if v is not None:
            v.setLayoutDirection(Qt.RightToLeft)
        if h is not None:
            h.setLayoutDirection(Qt.RightToLeft)

    elif isinstance(w, QScrollArea):
        # اسکرول‌بار عمودی در RTL باید سمت چپ باشد؛ Fusion این را خودش
        # مدیریت می‌کند، فقط مطمئن شویم جهت درست ست شده
        w.setLayoutDirection(Qt.RightToLeft)


def _document_of(w):
    if isinstance(w, QLineEdit):
        return w.document() if hasattr(w, "document") else None
    if isinstance(w, (QTextEdit, QPlainTextEdit)):
        return w.document() if hasattr(w, "document") else None
    return None


def _persian_text_option(option: QTextDocument.TextOption) -> QTextDocument.TextOption:
    """افزودن پرچم‌های فارسی به TextOption بدون خراب کردن تنظیمات دیگر."""
    option.setFlags(
        option.flags()
        | QTextDocument.TextOption.UsePersianLineSeparators
        | QTextDocument.TextOption.UsePersianShortDate
    )
    return option


def fix_table_view(tv: QTableView) -> None:
    """اصلاح کامل RTL برای جداول: هدر، اسکرول‌بار و تراز سلول‌ها.

    توجه: Qt هنگام RTL بودن view، منطق section را معکوس می‌کند؛ پس در
    delegate/overlay نباید دوباره x را معکوس کرد (باگ شناخته‌شده قدیمی).
    """
    tv.setLayoutDirection(Qt.RightToLeft)
    hdr = tv.horizontalHeader()
    if hdr is not None:
        hdr.setLayoutDirection(Qt.RightToLeft)
    tv.verticalScrollBar().setLayoutDirection(Qt.RightToLeft)
    tv.horizontalScrollBar().setLayoutDirection(Qt.RightToLeft)
    tv.setStyleSheet(
        tv.styleSheet()
        + "\nQHeaderView::section { border-left: none; }\n"
    )


def rtl_grid_position(grid_layout, row: int, col: int, total_cols: int):
    """محاسبه موقعیت ستون در QGridLayout برای چیدمان شطرنجی RTL.

    در RTL اولین آیتم باید راست‌ترین ستون باشد؛ اگر دستی addItem می‌کنید
    از این تابع برای نگاشت col → ستون فیزیکی استفاده کنید.
    """
    return row, (total_cols - 1 - col)
