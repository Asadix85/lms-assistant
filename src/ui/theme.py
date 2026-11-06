"""Theme: Turquoise — Liquid Glass + Minimal (Light + Dark).

Design system دسکتاپ — هم‌سطح کیفیت وب، با هویت رنگی فیروزه‌ای.
"""

from pathlib import Path

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QBoxLayout, QWidget
from PySide6.QtCore import Qt


# === Theme Mode ===
class ThemeMode:
    LIGHT = "light"
    DARK = "dark"


# === Spacing / Radius tokens (برای استفاده در کد، نه فقط QSS) ===
class Radius:
    """شعاع‌های یکدست — نزدیک به حس Liquid Glass وب."""

    XS = 8
    SM = 12
    MD = 16
    LG = 20
    XL = 24
    PILL = 22
    CIRCLE = 999


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


# === Colors ===
class LightColors:
    """پالت روشن — فیروزه‌ای (Turquoise) + Liquid Glass."""

    PRIMARY = "#2AA6A3"
    PRIMARY_DARK = "#1E807E"
    PRIMARY_LIGHT = "rgba(42, 166, 163, 0.12)"
    PRIMARY_SOFT = "rgba(42, 166, 163, 0.18)"
    PRIMARY_RING = "rgba(42, 166, 163, 0.35)"

    SECONDARY = "#3B8EA5"
    ACCENT = "#FF9500"
    ACCENT_DARK = "#CC7700"
    ACCENT_SOFT = "rgba(255, 149, 0, 0.14)"

    SUCCESS = "#34C759"
    SUCCESS_SOFT = "rgba(52, 199, 89, 0.14)"
    WARNING = "#FF9500"
    WARNING_SOFT = "rgba(255, 149, 0, 0.14)"
    ERROR = "#FF3B30"
    ERROR_SOFT = "rgba(255, 59, 48, 0.12)"
    INFO = "#2AA6A3"
    INFO_SOFT = "rgba(42, 166, 163, 0.12)"

    BG_MAIN = "#F2F7F7"
    BG_GRADIENT_START = "#F2F7F7"
    BG_GRADIENT_END = "#E5EDED"
    BG_CARD = "rgba(255, 255, 255, 0.78)"
    BG_HOVER = "rgba(255, 255, 255, 0.90)"

    # Liquid glass hierarchy (نزدیک به وب، روی پایه فیروزه)
    GLASS_BG = "rgba(255, 255, 255, 0.55)"
    GLASS_BG_SOFT = "rgba(255, 255, 255, 0.42)"
    GLASS_BG_STRONG = "rgba(255, 255, 255, 0.78)"
    GLASS_BG_HOVER = "rgba(255, 255, 255, 0.88)"
    GLASS_BG_ACTIVE = "rgba(255, 255, 255, 0.94)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.72)"
    GLASS_BORDER_OUTER = "rgba(0, 0, 0, 0.06)"
    GLASS_BORDER_HOVER = "rgba(42, 166, 163, 0.40)"
    GLASS_HI = "rgba(255, 255, 255, 0.95)"
    GLASS_LO = "rgba(255, 255, 255, 0.22)"

    SIDEBAR_BG = "rgba(255, 255, 255, 0.72)"
    SIDEBAR_BG_HOVER = "rgba(242, 247, 247, 0.92)"
    SIDEBAR_ITEM_ACTIVE = "rgba(42, 166, 163, 0.14)"
    SEPARATOR_COLOR = "rgba(100, 116, 139, 0.22)"

    HEADER_BG = "rgba(255, 255, 255, 0.78)"

    TEXT_PRIMARY = "#1C1C1E"
    TEXT_SECONDARY = "#3A3A3C"
    TEXT_MUTED = "#8E8E93"
    TEXT_WHITE = "#FFFFFF"

    BORDER = "rgba(0, 0, 0, 0.08)"
    BORDER_LIGHT = "rgba(0, 0, 0, 0.04)"

    # Shadow (ARGB برای QGraphicsDropShadowEffect)
    SHADOW = "#1E507814"
    SHADOW_LG = "#14326E28"
    SHADOW_SOFT = "#1E50780C"

    LMS3 = "#34C759"
    LMS4 = "#2AA6A3"
    LMS5 = "#FF3B30"


class DarkColors:
    """پالت تیره — فیروزه‌ای درخشان + Liquid Glass."""

    PRIMARY = "#4ECDC4"
    PRIMARY_DARK = "#3BAAA2"
    PRIMARY_LIGHT = "rgba(78, 205, 196, 0.18)"
    PRIMARY_SOFT = "rgba(78, 205, 196, 0.24)"
    PRIMARY_RING = "rgba(78, 205, 196, 0.42)"

    SECONDARY = "#5E9EAD"
    ACCENT = "#FF9F0A"
    ACCENT_DARK = "#CC7F08"
    ACCENT_SOFT = "rgba(255, 159, 10, 0.16)"
    SEPARATOR_COLOR = "rgba(78, 205, 196, 0.28)"

    SUCCESS = "#30D158"
    SUCCESS_SOFT = "rgba(48, 209, 88, 0.16)"
    WARNING = "#FF9F0A"
    WARNING_SOFT = "rgba(255, 159, 10, 0.16)"
    ERROR = "#FF453A"
    ERROR_SOFT = "rgba(255, 69, 58, 0.16)"
    INFO = "#4ECDC4"
    INFO_SOFT = "rgba(78, 205, 196, 0.16)"

    BG_MAIN = "#0A1212"
    BG_GRADIENT_START = "#0A1212"
    BG_GRADIENT_END = "#1C2626"
    BG_CARD = "rgba(28, 38, 38, 0.78)"
    BG_HOVER = "rgba(44, 54, 54, 0.88)"

    GLASS_BG = "rgba(22, 30, 30, 0.58)"
    GLASS_BG_SOFT = "rgba(18, 26, 26, 0.48)"
    GLASS_BG_STRONG = "rgba(32, 42, 42, 0.82)"
    GLASS_BG_HOVER = "rgba(44, 54, 54, 0.86)"
    GLASS_BG_ACTIVE = "rgba(58, 68, 68, 0.92)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.12)"
    GLASS_BORDER_OUTER = "rgba(255, 255, 255, 0.06)"
    GLASS_BORDER_HOVER = "rgba(78, 205, 196, 0.48)"
    GLASS_HI = "rgba(255, 255, 255, 0.22)"
    GLASS_LO = "rgba(255, 255, 255, 0.06)"

    SIDEBAR_BG = "rgba(10, 18, 18, 0.82)"
    SIDEBAR_BG_HOVER = "rgba(28, 38, 38, 0.72)"
    SIDEBAR_ITEM_ACTIVE = "rgba(78, 205, 196, 0.20)"

    HEADER_BG = "rgba(10, 18, 18, 0.80)"

    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#EBEBF5"
    TEXT_MUTED = "#8E8E93"
    TEXT_WHITE = "#FFFFFF"

    BORDER = "rgba(255, 255, 255, 0.10)"
    BORDER_LIGHT = "rgba(255, 255, 255, 0.06)"

    SHADOW = "#00000066"
    SHADOW_LG = "#00000099"
    SHADOW_SOFT = "#00000040"

    LMS3 = "#30D158"
    LMS4 = "#4ECDC4"
    LMS5 = "#FF453A"


# === Aliases (سازگاری با کدهای قدیمی) ===
class Colors:
    PRIMARY = LightColors.PRIMARY
    PRIMARY_DARK = LightColors.PRIMARY_DARK
    PRIMARY_LIGHT = LightColors.PRIMARY_LIGHT
    SECONDARY = LightColors.SECONDARY
    ACCENT = LightColors.ACCENT
    ACCENT_DARK = LightColors.ACCENT_DARK
    SUCCESS = LightColors.SUCCESS
    WARNING = LightColors.WARNING
    ERROR = LightColors.ERROR
    INFO = LightColors.INFO
    BG_MAIN = LightColors.BG_MAIN
    BG_CARD = LightColors.BG_CARD
    BG_HOVER = LightColors.BG_HOVER
    TEXT_PRIMARY = LightColors.TEXT_PRIMARY
    TEXT_SECONDARY = LightColors.TEXT_SECONDARY
    TEXT_MUTED = LightColors.TEXT_MUTED
    TEXT_WHITE = LightColors.TEXT_WHITE
    BORDER = LightColors.BORDER
    BORDER_LIGHT = LightColors.BORDER_LIGHT
    LMS3 = LightColors.LMS3
    LMS4 = LightColors.LMS4
    LMS5 = LightColors.LMS5


# === Current Theme ===
class CurrentTheme:
    mode = ThemeMode.LIGHT

    @classmethod
    def colors(cls):
        return DarkColors if cls.mode == ThemeMode.DARK else LightColors

    @classmethod
    def set_mode(cls, mode: str):
        cls.mode = mode

    @classmethod
    def is_dark(cls) -> bool:
        return cls.mode == ThemeMode.DARK


# === Fonts ===
class Fonts:
    FAMILY = "Vazirmatn"
    FALLBACK = "Tahoma"
    SIZE_XS = 9
    SIZE_SM = 10
    SIZE_BASE = 11
    SIZE_MD = 12
    SIZE_LG = 14
    SIZE_XL = 18
    SIZE_XXL = 24
    SIZE_HERO = 32

    @classmethod
    def load(cls, fonts_dir: Path | str | None = None) -> bool:
        if fonts_dir is None:
            from src.utils.paths import get_asset_path
            fonts_dir = get_asset_path("fonts/vazirmatn")
        else:
            fonts_dir = Path(fonts_dir)

        if not fonts_dir.exists():
            print(f"❌ پوشه فونت پیدا نشد: {fonts_dir}")
            return False

        ttf_files = []
        main_ttf = fonts_dir / "fonts" / "ttf"
        if main_ttf.exists():
            ttf_files = list(main_ttf.glob("*.ttf"))
        else:
            ttf_files = [
                p for p in fonts_dir.rglob("*.ttf")
                if "misc" not in p.parts and "Round-Dots" not in p.parts
            ]

        if not ttf_files:
            print(f"❌ هیچ فایل .ttf در {fonts_dir} پیدا نشد")
            return False

        loaded = 0
        for ttf in ttf_files:
            font_id = QFontDatabase.addApplicationFont(str(ttf))
            if font_id != -1:
                loaded += 1

        print(f"✅ فونت لود شد: {loaded} فایل از {len(ttf_files)}")
        return loaded > 0

    @classmethod
    def get(cls, size: int = SIZE_BASE, weight: str = "normal") -> QFont:
        font = QFont(cls.FAMILY, size)
        font.setStyleStrategy(QFont.PreferAntialias)
        if weight == "bold":
            font.setBold(True)
        elif weight == "medium":
            font.setWeight(QFont.Medium)
        return font


# === Global QSS ===
def get_global_qss(mode: str = ThemeMode.LIGHT) -> str:
    c = LightColors if mode == ThemeMode.LIGHT else DarkColors
    f = Fonts
    r = Radius

    return f"""
    /* === Base === */
    QWidget {{
        font-family: "{f.FAMILY}", "{f.FALLBACK}", sans-serif;
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QMainWindow, QDialog {{
        background: transparent;
    }}
    QWidget#CentralWidget {{
        background: transparent;
    }}

    QLabel#HeroTitle {{
        color: white;
        font-size: 22pt;
        font-weight: bold;
        background: transparent;
    }}

    QLabel#HeroMeta {{
        color: rgba(255, 255, 255, 0.95);
        font-size: 11pt;
        background: transparent;
    }}

    /* === Section Title === */
    QLabel#SectionTitle {{
        color: {c.TEXT_PRIMARY};
        font-weight: 800;
        font-size: 13pt;
        background: transparent;
        padding: 12px 4px 6px 4px;
    }}

    /* === Hero Card (صفحه‌ی درس) === */
    QFrame#HeroCard {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {c.PRIMARY},
            stop:1 {c.PRIMARY_DARK}
        );
        border: none;
        border-radius: {r.LG}px;
    }}

    /* === Sidebar === */
    QFrame#Sidebar {{
        background-color: transparent;
        border: none;
    }}

    QFrame#SidebarTopCard {{
        background-color: {c.SIDEBAR_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.XL}px;
    }}

    QFrame#SidebarBottomCard {{
        background-color: {c.SIDEBAR_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.XL}px;
    }}

    QLabel#SidebarLogo {{
        font-size: 15pt;
        font-weight: 800;
        color: {c.PRIMARY};
        padding: 4px 4px 8px 4px;
        background: transparent;
    }}

    QLabel#SidebarSubtitle {{
        font-size: 9pt;
        color: {c.TEXT_MUTED};
        padding: 0 4px 4px 4px;
        background: transparent;
    }}

    QFrame#SidebarSeparator {{
        background-color: {c.SEPARATOR_COLOR};
        margin: 6px 12px;
        max-height: 1px;
        border: none;
    }}

    QPushButton#SidebarButton {{
        text-align: center;
        padding: 10px 14px;
        border: 1px solid transparent;
        border-radius: {r.SM}px;
        background-color: transparent;
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        margin: 1px 2px;
        font-weight: 500;
    }}

    QPushButton#SidebarButton:hover {{
        background-color: {c.SIDEBAR_BG_HOVER};
        border-color: {c.GLASS_BORDER_OUTER};
    }}

    QPushButton#SidebarButton:checked {{
        background-color: {c.SIDEBAR_ITEM_ACTIVE};
        color: {c.PRIMARY};
        font-weight: bold;
        border-color: {c.PRIMARY_RING};
    }}

    QPushButton#SidebarToggleButton {{
        background-color: {c.GLASS_BG};
        color: {c.TEXT_SECONDARY};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: 14px;
        font-size: 14pt;
        font-weight: bold;
        padding: 0;
    }}
    QPushButton#SidebarToggleButton:hover {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border-color: {c.PRIMARY};
    }}

    QLabel#SidebarVersion {{
        color: {c.TEXT_MUTED};
        font-size: 8pt;
        padding: 4px;
        background: transparent;
    }}

    /* === Header === */
    QFrame#Header {{
        background-color: {c.HEADER_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.LG}px;
        margin: 8px 8px 0 8px;
    }}

    QLabel#HeaderTitle {{
        font-size: {f.SIZE_LG}pt;
        font-weight: bold;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}

    QLabel#HeaderSubtitle {{
        font-size: {f.SIZE_SM}pt;
        color: {c.TEXT_SECONDARY};
        background: transparent;
    }}

    QLabel#HeaderChanges {{
        font-size: {f.SIZE_SM}pt;
        color: {c.PRIMARY};
        font-weight: 600;
        background: transparent;
    }}

    QLabel#HeaderElapsed {{
        font-size: {f.SIZE_XS}pt;
        color: {c.TEXT_MUTED};
        background: transparent;
    }}

    /* === Cards (Liquid Glass) === */
    QFrame#Card,
    QFrame#StatCard,
    QFrame#CourseCard,
    QFrame#PostCard,
    QFrame#AssignmentCard,
    QFrame#EventCard,
    QFrame#ChangeCard,
    QFrame#SettingCard,
    QFrame#CourseInfoHeader,
    QFrame#AssignmentTimeBox,
    QFrame#DetailPanel,
    QFrame#ContentRow,
    QFrame#TimeBox,
    QFrame#QueraCard,
    QFrame#MapCard,
    QFrame#EmptyStateCard {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.LG}px;
    }}
    QFrame#CourseCard:hover,
    QFrame#AssignmentCard:hover,
    QFrame#EventCard:hover,
    QFrame#ChangeCard:hover,
    QFrame#CourseInfoHeader:hover,
    QFrame#ContentRow:hover,
    QFrame#PostCard:hover,
    QFrame#QueraCard:hover,
    QFrame#MapCard:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border: 1px solid {c.GLASS_BORDER_HOVER};
    }}
    QFrame#UpcomingCard {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.MD}px;
    }}
    QFrame#UpcomingCard:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border: 1px solid {c.GLASS_BORDER_HOVER};
    }}

    /* === Buttons === */
    QPushButton#PrimaryButton {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border: none;
        border-radius: {r.SM}px;
        padding: 11px 22px;
        font-size: {f.SIZE_BASE}pt;
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}
    QPushButton#PrimaryButton:disabled {{
        background-color: {c.TEXT_MUTED};
    }}

    QPushButton#SoftButton {{
        background-color: {c.PRIMARY_LIGHT};
        color: {c.PRIMARY};
        border: 1px solid {c.PRIMARY_RING};
        border-radius: {r.SM}px;
        padding: 10px 18px;
        font-weight: 600;
    }}
    QPushButton#SoftButton:hover {{
        background-color: {c.PRIMARY_SOFT};
        border-color: {c.PRIMARY};
    }}

    QPushButton#GhostButton {{
        background-color: transparent;
        color: {c.TEXT_SECONDARY};
        border: 1px solid transparent;
        border-radius: {r.SM}px;
        padding: 8px 12px;
        font-weight: 500;
    }}
    QPushButton#GhostButton:hover {{
        background-color: {c.GLASS_BG_HOVER};
        color: {c.PRIMARY};
        border-color: {c.GLASS_BORDER};
    }}

    /* === Pill Progress Button === */
    QPushButton#PillButton {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border: none;
        border-radius: {r.PILL}px;
        font-size: {f.SIZE_BASE}pt;
        font-weight: 600;
        padding: 0 20px;
    }}
    QPushButton#PillButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}
    QPushButton#PillButton:pressed {{
        background-color: {c.PRIMARY_DARK};
    }}
    QPushButton#PillButton:disabled {{
        background-color: {c.TEXT_MUTED};
    }}

    QPushButton#SecondaryButton {{
        background-color: {c.GLASS_BG};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.SM}px;
        padding: 10px 18px;
    }}
    QPushButton#SecondaryButton:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-color: {c.GLASS_BORDER_HOVER};
        color: {c.PRIMARY};
    }}

    /* Filter — یک تعریف، pill مدرن */
    QPushButton#FilterButton {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.PILL}px;
        padding: 8px 16px;
        color: {c.TEXT_PRIMARY};
        font-weight: 500;
    }}
    QPushButton#FilterButton:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-color: {c.PRIMARY};
        color: {c.PRIMARY};
    }}
    QPushButton#FilterButton:checked {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border-color: {c.PRIMARY};
        font-weight: bold;
    }}

    QPushButton#CircularButton {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border: none;
        border-radius: 40px;
        font-size: 10pt;
        font-weight: 600;
        padding: 8px;
    }}
    QPushButton#CircularButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}
    QPushButton#CircularButton:disabled {{
        background-color: {c.TEXT_MUTED};
    }}

    QPushButton#DangerButton {{
        background-color: transparent;
        color: {c.ERROR};
        border: 1.5px solid {c.ERROR};
        border-radius: {r.SM}px;
        padding: 10px 18px;
        font-weight: 600;
    }}
    QPushButton#DangerButton:hover {{
        background-color: {c.ERROR_SOFT};
    }}

    /* === Input === */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: {r.SM}px;
        padding: 10px 14px;
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_PRIMARY};
        selection-background-color: {c.PRIMARY_SOFT};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1.5px solid {c.PRIMARY};
        background-color: {c.GLASS_BG_HOVER};
    }}

    /* === Text hierarchy === */
    QLabel#PageTitle {{
        font-size: {f.SIZE_XXL}pt;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#PageSubtitle {{
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_SECONDARY};
        background: transparent;
    }}
    QLabel#CardTitle {{
        font-size: {f.SIZE_MD}pt;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#CardSubtitle {{
        font-size: {f.SIZE_SM}pt;
        color: {c.TEXT_SECONDARY};
        background: transparent;
    }}
    QLabel#StatValue {{
        font-size: {f.SIZE_HERO}pt;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#StatValueAccent {{
        font-size: {f.SIZE_HERO}pt;
        font-weight: 700;
        color: {c.PRIMARY};
        background: transparent;
    }}
    QLabel#StatLabel {{
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_SECONDARY};
        background: transparent;
    }}

    /* === Dashboard Stat === */
    QLabel#DashboardStatIcon {{
        font-size: 20pt;
        background: transparent;
        border: none;
    }}
    QLabel#DashboardStatValue {{
        font-size: 24pt;
        font-weight: bold;
        color: {c.TEXT_PRIMARY};
        background: transparent;
        border: none;
    }}
    QLabel#DashboardStatLabel {{
        font-size: 10pt;
        color: {c.TEXT_SECONDARY};
        background: transparent;
        border: none;
    }}

    /* === Badges / Pills === */
    QLabel#Badge {{
        border-radius: 10px;
        padding: 2px 10px;
        font-size: {f.SIZE_XS}pt;
        font-weight: 700;
        background-color: {c.PRIMARY_LIGHT};
        color: {c.PRIMARY};
    }}
    QLabel#Badge[kind="success"] {{
        background-color: {c.SUCCESS_SOFT};
        color: {c.SUCCESS};
    }}
    QLabel#Badge[kind="warning"] {{
        background-color: {c.WARNING_SOFT};
        color: {c.WARNING};
    }}
    QLabel#Badge[kind="danger"] {{
        background-color: {c.ERROR_SOFT};
        color: {c.ERROR};
    }}
    QLabel#Badge[kind="muted"] {{
        background-color: {c.BG_HOVER};
        color: {c.TEXT_MUTED};
    }}

    QLabel#StatusPill {{
        border-radius: 13px;
        padding: 0 14px;
        font-size: {f.SIZE_SM}pt;
        font-weight: 700;
    }}
    QLabel#StatusPill[kind="success"] {{
        color: {c.SUCCESS};
        background-color: {c.SUCCESS_SOFT};
    }}
    QLabel#StatusPill[kind="danger"] {{
        color: {c.ERROR};
        background-color: {c.ERROR_SOFT};
    }}
    QLabel#StatusPill[kind="info"] {{
        color: {c.PRIMARY};
        background-color: {c.PRIMARY_LIGHT};
    }}
    QLabel#StatusPill[kind="muted"] {{
        color: {c.TEXT_MUTED};
        background-color: {c.BG_HOVER};
    }}

    /* === Login Dialog === */
    QDialog {{
        background-color: {c.BG_CARD};
        border-radius: {r.LG}px;
    }}
    QDialog QLabel {{
        background: transparent;
    }}

    /* === Scroll Bar === */
    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background-color: transparent;
        width: 12px;
        margin: 4px 2px 4px 2px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.PRIMARY},
            stop:1 {c.PRIMARY_DARK}
        );
        border-radius: 5px;
        min-height: 40px;
        margin: 0px 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.PRIMARY_DARK},
            stop:1 {c.PRIMARY}
        );
        margin: 0px 1px;
    }}
    QScrollBar::handle:vertical:pressed {{
        background: {c.PRIMARY_DARK};
        margin: 0px 0px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
        background: transparent;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 12px;
        margin: 2px 4px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {c.PRIMARY},
            stop:1 {c.PRIMARY_DARK}
        );
        border-radius: 5px;
        min-width: 40px;
        margin: 3px 0px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c.PRIMARY_DARK};
        margin: 1px 0px;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* === Progress === */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {c.BORDER_LIGHT};
        height: 5px;
    }}
    QProgressBar::chunk {{
        background-color: {c.PRIMARY};
        border-radius: 4px;
    }}

    /* === Status Bar === */
    QStatusBar {{
        background-color: {c.HEADER_BG};
        border-top: 1px solid {c.GLASS_BORDER};
        color: {c.TEXT_SECONDARY};
    }}

    /* === CheckBox === */
    QCheckBox {{
        spacing: 12px;
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        padding: 10px 8px;
        background: transparent;
        border-radius: {r.XS}px;
    }}
    QCheckBox:hover {{
        background-color: {c.BG_HOVER};
    }}
    QCheckBox::indicator {{
        width: 22px;
        height: 22px;
        border-radius: 6px;
        border: 2px solid {c.TEXT_MUTED};
        background-color: {c.GLASS_BG};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c.PRIMARY};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c.PRIMARY};
        border-color: {c.PRIMARY};
    }}
    QCheckBox::indicator:disabled {{
        background-color: {c.BORDER_LIGHT};
        border-color: {c.BORDER};
    }}
    QCheckBox:disabled {{
        color: {c.TEXT_MUTED};
    }}

    /* === Calendar & Detail === */
    QLabel#DetailHeader {{
        background: transparent;
        color: {c.PRIMARY};
        font-weight: 600;
        font-size: {f.SIZE_MD}pt;
    }}

    /* === QMessageBox === */
    QMessageBox {{
        background-color: {c.BG_CARD};
        color: {c.TEXT_PRIMARY};
    }}
    QMessageBox QLabel {{
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QMessageBox QPushButton {{
        background-color: {c.PRIMARY};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 18px;
        min-width: 80px;
        font-weight: 500;
    }}
    QMessageBox QPushButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}

    /* === Sync Tile === */
    QFrame#SyncTile {{
        background-color: {c.GLASS_BG};
        border: 1.5px solid {c.GLASS_BORDER};
        border-radius: {r.MD}px;
    }}
    QFrame#SyncTile:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-color: {c.PRIMARY};
    }}
    QFrame#SyncTile[checked="true"] {{
        border-color: {c.PRIMARY};
        background-color: {c.PRIMARY_LIGHT};
    }}

    /* === Theme Switch === */
    QToolButton#ThemeSwitch {{
        background-color: {c.GLASS_BG};
        color: {c.TEXT_PRIMARY};
        border: 1.5px solid {c.GLASS_BORDER};
        border-radius: 18px;
        font-size: {f.SIZE_BASE}pt;
        font-weight: 700;
    }}
    QToolButton#ThemeSwitch:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-color: {c.GLASS_BORDER_HOVER};
    }}
    QToolButton#ThemeSwitch:checked {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border-color: {c.PRIMARY};
    }}

    /* === Empty state helper label === */
    QLabel#EmptyIconCircle {{
        background-color: {c.PRIMARY_LIGHT};
        border: 1px solid {c.PRIMARY_RING};
        border-radius: 40px;
        min-width: 80px;
        min-height: 80px;
        max-width: 80px;
        max-height: 80px;
    }}
    """


def apply_rtl_recursive(widget):
    """اعمال RTL روی widget و همه‌ی فرزندان (recursive).

    این تابع به ماژول src.ui.rtl منتقل شده است. نسخه قبلی دو باگ
    داشت: ۱) AlignCenter برچسب‌ها/آیکون‌ها را به راست می‌پراند ۲) عناصر
    عمداً LTR (ساعت، Chat ID) را هم راست‌تراز می‌کرد. نسخه جدید در
    `src/ui/rtl.py` هر دو را اصلاح کرده و فیلتر ChildAdded هم دارد.
    """
    from src.ui.rtl import apply_rtl_recursive as _apply
    _apply(widget)
