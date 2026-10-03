"""Theme: Liquid Glass style with Neutral Blue palette (Light + Dark)."""

from pathlib import Path

from PySide6.QtGui import QFontDatabase, QFont


# === Theme Mode ===

class ThemeMode:
    LIGHT = "light"
    DARK = "dark"


# === Colors ===

class LightColors:
    """پالت رنگ تم روشن — Neutral Blue (روشن)."""

    PRIMARY = "#3B82F6"
    PRIMARY_DARK = "#2563EB"
    PRIMARY_LIGHT = "rgba(59, 130, 246, 0.12)"

    SECONDARY = "#6366F1"
    ACCENT = "#F59E0B"
    ACCENT_DARK = "#D97706"

    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"

    BG_GRADIENT_START = "#F8FAFC"      # ← Slate-50
    BG_GRADIENT_END = "#F1F5F9"
    BG_MAIN = "#F8FAFC"

    # کارت‌ها (روشن‌تر و با کنتراست)
    GLASS_BG = "rgba(255, 255, 255, 0.75)"
    GLASS_BG_HOVER = "rgba(255, 255, 255, 0.88)"
    GLASS_BG_ACTIVE = "rgba(255, 255, 255, 0.95)"

    GLASS_BORDER = "rgba(203, 213, 225, 0.6)"
    GLASS_BORDER_HOVER = "rgba(59, 130, 246, 0.5)"

    SIDEBAR_BG = "rgba(248, 250, 252, 0.75)"
    SIDEBAR_BG_HOVER = "rgba(255, 255, 255, 0.85)"
    SIDEBAR_ITEM_ACTIVE = "rgba(59, 130, 246, 0.15)"

    HEADER_BG = "rgba(248, 250, 252, 0.8)"

    BG_CARD = "rgba(255, 255, 255, 0.75)"
    BG_HOVER = "rgba(241, 245, 249, 0.6)"

    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#64748B"
    TEXT_MUTED = "#94A3B8"
    TEXT_WHITE = "#FFFFFF"

    BORDER = "rgba(15, 23, 42, 0.08)"
    BORDER_LIGHT = "rgba(15, 23, 42, 0.04)"

    LMS3 = "#10B981"
    LMS4 = "#3B82F6"
    LMS5 = "#EF4444"

class DarkColors:
    """پالت رنگ تم تیره — Slate + Neutral Blue (تیره‌ی خوانا)."""

    # Primary
    PRIMARY = "#60A5FA"
    PRIMARY_DARK = "#3B82F6"
    PRIMARY_LIGHT = "rgba(96, 165, 250, 0.22)"

    # Secondary
    SECONDARY = "#818CF8"

    # Accent
    ACCENT = "#FBBF24"
    ACCENT_DARK = "#F59E0B"

    # Status
    SUCCESS = "#34D399"
    WARNING = "#FBBF24"
    ERROR = "#F87171"
    INFO = "#60A5FA"

    # پس‌زمینه
    BG_GRADIENT_START = "#0F172A"
    BG_GRADIENT_END = "#1E293B"
    BG_MAIN = "#0F172A"

    # ⚠️ کارت‌ها تیره‌تر و با alpha بالاتر (کنتراست بهتر)
    GLASS_BG = "rgba(15, 23, 42, 0.78)"
    GLASS_BG_HOVER = "rgba(30, 41, 59, 0.88)"
    GLASS_BG_ACTIVE = "rgba(51, 65, 85, 0.92)"

    # حاشیه
    GLASS_BORDER = "rgba(148, 163, 184, 0.18)"
    GLASS_BORDER_HOVER = "rgba(96, 165, 250, 0.6)"

    # Sidebar — تیره‌تر از کارت‌ها
    SIDEBAR_BG = "rgba(2, 6, 23, 0.85)"
    SIDEBAR_BG_HOVER = "rgba(30, 41, 59, 0.7)"
    SIDEBAR_ITEM_ACTIVE = "rgba(96, 165, 250, 0.22)"

    # Header
    HEADER_BG = "rgba(15, 23, 42, 0.85)"

    BG_CARD = "rgba(15, 23, 42, 0.78)"
    BG_HOVER = "rgba(30, 41, 59, 0.5)"

    # متن
    TEXT_PRIMARY = "#F1F5F9"       # ← Slate-100 (روشن‌تر)
    TEXT_SECONDARY = "#CBD5E1"     # ← Slate-300 (روشن‌تر از قبل)
    TEXT_MUTED = "#94A3B8"         # ← Slate-400
    TEXT_WHITE = "#FFFFFF"

    BORDER = "rgba(148, 163, 184, 0.12)"
    BORDER_LIGHT = "rgba(148, 163, 184, 0.06)"

    LMS3 = "#34D399"
    LMS4 = "#60A5FA"
    LMS5 = "#F87171"

# === Aliases ===

class Colors:
    """Alias برای LightColors (سازگاری)."""
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
        if cls.mode == ThemeMode.DARK:
            return DarkColors
        return LightColors

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
    def load(cls, fonts_dir: Path | str = "assets/fonts/vazirmatn") -> bool:
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


# === Global QSS (Liquid Glass with Neutral Blue) ===

def get_global_qss(mode: str = ThemeMode.LIGHT) -> str:
    c = LightColors if mode == ThemeMode.LIGHT else DarkColors
    f = Fonts

    # ⚠️ پس‌زمینه‌ی Solid (نه شفاف) — رنگ دقیق
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

    /* === Sidebar === */
    QFrame#Sidebar {{
        background-color: {c.SIDEBAR_BG};
        border: none;
        border-left: 1px solid {c.GLASS_BORDER};
    }}

    QPushButton#SidebarButton {{
        text-align: right;
        padding: 12px 18px;
        border: 1px solid transparent;
        border-radius: 14px;
        background-color: transparent;
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        margin: 3px 10px;
        font-weight: 500;
    }}

    QPushButton#SidebarButton:hover {{
        background-color: {c.SIDEBAR_BG_HOVER};
    }}

    QPushButton#SidebarButton:checked {{
        background-color: {c.SIDEBAR_ITEM_ACTIVE};
        color: {c.PRIMARY};
        font-weight: bold;
    }}

    /* === Header === */
    QFrame#Header {{
        background-color: {c.HEADER_BG};
        border-bottom: 1px solid {c.GLASS_BORDER};
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

    /* === Cards (با Border و tint برای عمق) === */
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
    QFrame#TimeBox {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-bottom: 2px solid {c.BORDER};
        border-radius: 18px;
    }}

    QFrame#CourseCard:hover,
    QFrame#AssignmentCard:hover,
    QFrame#EventCard:hover,
    QFrame#ChangeCard:hover,
    QFrame#CourseInfoHeader:hover,
    QFrame#ContentRow:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border: 1px solid {c.GLASS_BORDER_HOVER};
        border-bottom: 2px solid {c.PRIMARY};
    }}

    /* === Buttons === */
    QPushButton#PrimaryButton {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border: 1px solid {c.PRIMARY_DARK};
        border-radius: 14px;
        padding: 12px 24px;
        font-size: {f.SIZE_BASE}pt;
        font-weight: bold;
        text-align: center;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}

    QPushButton#PrimaryButton:disabled {{
        background-color: {c.TEXT_MUTED};
        border-color: {c.TEXT_MUTED};
    }}

    QPushButton#SecondaryButton {{
        background-color: {c.GLASS_BG};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: 14px;
        padding: 10px 20px;
        text-align: center;
    }}

    QPushButton#SecondaryButton:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-color: {c.GLASS_BORDER_HOVER};
    }}

    QPushButton#FilterButton {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: 12px;
        padding: 8px 16px;
        color: {c.TEXT_PRIMARY};
        text-align: center;
    }}

    QPushButton#FilterButton:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-color: {c.GLASS_BORDER_HOVER};
        color: {c.PRIMARY};
    }}

    QPushButton#FilterButton:checked {{
        background-color: {c.PRIMARY};
        color: white;
        border-color: {c.PRIMARY};
    }}

    /* === Input === */
    QLineEdit {{
        background-color: {c.GLASS_BG};
        border: 1px solid {c.GLASS_BORDER};
        border-radius: 14px;
        padding: 10px 16px;
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_PRIMARY};
    }}

    QLineEdit:focus {{
        border: 2px solid {c.PRIMARY};
        background-color: {c.GLASS_BG_HOVER};
    }}

    /* === Text === */
    QLabel#PageTitle {{
        font-size: {f.SIZE_XXL}pt;
        font-weight: bold;
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
        font-weight: bold;
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
        font-weight: bold;
        color: {c.PRIMARY};
        background: transparent;
    }}

    QLabel#StatLabel {{
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_SECONDARY};
        background: transparent;
    }}

    /* === Scroll === */
    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        border-radius: 5px;
        margin: 4px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c.TEXT_MUTED};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c.TEXT_SECONDARY};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* === Progress === */
    QProgressBar {{
        border: none;
        border-radius: 6px;
        background-color: {c.BORDER_LIGHT};
        height: 6px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {c.PRIMARY};
        border-radius: 6px;
    }}

    /* === Tabs === */
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}

    QTabBar::tab {{
        background-color: transparent;
        color: {c.TEXT_SECONDARY};
        padding: 10px 24px;
        border: none;
        border-radius: 12px;
        margin: 4px;
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        background-color: {c.SIDEBAR_ITEM_ACTIVE};
        color: {c.PRIMARY};
        font-weight: bold;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {c.GLASS_BG};
        color: {c.TEXT_PRIMARY};
    }}

    /* === Status Bar === */
    QStatusBar {{
        background-color: {c.HEADER_BG};
        border-top: 1px solid {c.GLASS_BORDER};
        color: {c.TEXT_SECONDARY};
    }}

    /* === Post Card === */
    QLabel#PostAuthor {{
        font-weight: bold;
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_MD}pt;
        background: transparent;
    }}

    QLabel#PostDate {{
        color: {c.TEXT_MUTED};
        font-size: {f.SIZE_SM}pt;
        background: transparent;
    }}

    QLabel#PostText {{
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        background: transparent;
    }}

    /* === Calendar === */
    QFrame#CalendarGrid {{
        background-color: transparent;
        border: none;
    }}

    QLabel#DayLabel {{
        color: {c.TEXT_PRIMARY};
        font-weight: bold;
        font-size: 10pt;
        background-color: {c.GLASS_BG};
        border-radius: 8px;
        padding: 4px;
    }}

    QLabel#DayEmpty {{
        color: {c.TEXT_MUTED};
        font-size: 12pt;
        background: transparent;
    }}

    QLabel#CalEventTitle {{
        color: {c.TEXT_PRIMARY};
        font-size: 8pt;
        font-weight: bold;
        background: transparent;
    }}

    QLabel#CalEventDeadline {{
        color: {c.ERROR};
        font-size: 7pt;
        font-weight: bold;
        background: transparent;
    }}

    QLabel#DetailHeader {{
        background: transparent;
        color: {c.PRIMARY};
        font-weight: bold;
        font-size: {f.SIZE_MD}pt;
    }}
    
    /* === Hero Card (بیشتر برای About) === */
    
    QFrame#HeroCard {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {c.PRIMARY}, stop:0.5 {c.PRIMARY_DARK}, stop:1 {c.SECONDARY});
        border: 1px solid {c.GLASS_BORDER};
        border-radius: 24px;
    }}

    QFrame#HeroCard QLabel {{
        background: transparent;
        color: white;
    }}
    
        /* === Horizontal Timeline === */
    QFrame#TimelineContainer {{
        background: transparent;
        border: none;
    }}

    QFrame#TimelineLine {{
        background-color: {c.BORDER};
        margin: 12px 60px 0 60px;
        border-radius: 1px;
    }}

    /* === Hover Link (الگوی یونیکو با رنگ خودمون) === */
    QPushButton#LinkButton {{
        background: transparent;
        color: {c.TEXT_PRIMARY};
        border: none;
        border-bottom: 2px solid transparent;
        padding: 8px 14px;
        text-align: center;
        font-weight: 500;
        font-size: {f.SIZE_BASE}pt;
    }}

    QPushButton#LinkButton:hover {{
        color: {c.PRIMARY};
        border-bottom: 2px solid {c.PRIMARY};
    }}

    QPushButton#LinkButton:checked {{
        color: {c.PRIMARY};
        border-bottom: 3px solid {c.PRIMARY};
        font-weight: bold;
    }}

    /* === Secondary Button با Hover Link === */
    QPushButton#SecondaryButton {{
        background-color: {c.GLASS_BG};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.GLASS_BORDER};
        border-bottom: 2px solid {c.GLASS_BORDER};
        border-radius: 14px;
        padding: 10px 20px;
        text-align: center;
    }}

    QPushButton#SecondaryButton:hover {{
        background-color: {c.GLASS_BG_HOVER};
        border-bottom: 2px solid {c.PRIMARY};
        color: {c.PRIMARY};
    }}
    
    /* === Header Progress === */
    QProgressBar#HeaderProgress {{
        border: none;
        border-radius: 2px;
        background-color: {c.BORDER_LIGHT};
        height: 4px;
        text-align: center;
    }}

    QProgressBar#HeaderProgress::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.PRIMARY}, stop:1 {c.SECONDARY});
        border-radius: 2px;
    }}
    
        /* === QCheckBox === */
    QCheckBox {{
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        spacing: 10px;
        background: transparent;
        padding: 6px 0;
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 2px solid {c.BORDER};
        background-color: {c.GLASS_BG};
    }}

    QCheckBox::indicator:hover {{
        border-color: {c.PRIMARY};
        background-color: {c.GLASS_BG_HOVER};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c.PRIMARY};
        border-color: {c.PRIMARY};
        image: none;
    }}

    QCheckBox::indicator:checked:hover {{
        background-color: {c.PRIMARY_DARK};
        border-color: {c.PRIMARY_DARK};
    }}

    QCheckBox::indicator:disabled {{
        background-color: {c.BORDER_LIGHT};
        border-color: {c.BORDER_LIGHT};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {c.PRIMARY};
        border-color: {c.PRIMARY};
        image: url(assets/icons/check.svg);
    }}
    
        /* === QMessageBox === */
    QMessageBox {{
        background-color: {c.BG_CARD};
        color: {c.TEXT_PRIMARY};
    }}

    QMessageBox QLabel {{
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        background: transparent;
    }}

    QMessageBox QPushButton {{
        background-color: {c.PRIMARY};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 8px 20px;
        min-width: 80px;
        font-weight: 500;
    }}

    QMessageBox QPushButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}

    /* === QDialog (برای همه دیالوگ‌ها) === */
    QDialog {{
        background-color: {c.BG_CARD};
        color: {c.TEXT_PRIMARY};
    }}

    QDialog QLabel {{
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    """