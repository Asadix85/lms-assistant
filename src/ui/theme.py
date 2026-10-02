"""Theme: رنگ‌ها، فونت، استایل‌های سراسری."""

from pathlib import Path

from PySide6.QtGui import QFontDatabase, QFont

# === Colors ===

class Colors:
    """پالت رنگ مرکزی."""

    # Primary
    PRIMARY = "#00C4C4"          # فیروزه‌ای (یونیکو)
    PRIMARY_DARK = "#00A8A8"
    PRIMARY_LIGHT = "#E0F7F7"

    # Secondary
    SECONDARY = "#5DADE2"        # آبی روشن
    SECONDARY_DARK = "#3498DB"

    # Accent
    ACCENT = "#F39C12"           # نارنجی
    ACCENT_DARK = "#E67E22"

    # Status
    SUCCESS = "#27AE60"
    WARNING = "#F39C12"
    ERROR = "#E74C3C"
    INFO = "#3498DB"

    # Backgrounds
    BG_MAIN = "#F5F7FA"          # پس‌زمینه اصلی
    BG_CARD = "#FFFFFF"          # کارت‌ها
    BG_SIDEBAR = "#FFFFFF"       # منوی کنار
    BG_HOVER = "#F0F2F5"

    # Text
    TEXT_PRIMARY = "#2C3E50"     # متن اصلی
    TEXT_SECONDARY = "#7F8C8D"   # متن کم‌رنگ
    TEXT_MUTED = "#BDC3C7"       # متن خیلی کم‌رنگ
    TEXT_WHITE = "#FFFFFF"

    # Borders
    BORDER = "#E1E4E8"
    BORDER_LIGHT = "#F0F2F5"

    # Domain colors
    LMS3 = "#27AE60"             # سبز
    LMS4 = "#3498DB"             # آبی
    LMS5 = "#E74C3C"             # قرمز


# === Fonts ===

class Fonts:
    """مدیریت فونت‌ها."""

    FAMILY = "Vazirmatn"
    FALLBACK = "Tahoma"

    # Sizes (pt)
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
        """بارگذاری فونت‌ها (recursive). True اگر موفق."""
        fonts_dir = Path(fonts_dir)
        if not fonts_dir.exists():
            print(f"❌ پوشه فونت پیدا نشد: {fonts_dir}")
            return False

        # جستجوی بازگشتی برای ttfها (فقط پوشه اصلی، نه misc)
        # از glob استفاده می‌کنیم روی fonts/ttf مشخص
        ttf_files = []

        # اول تلاش برای مسیر مشخص
        main_ttf = fonts_dir / "fonts" / "ttf"
        if main_ttf.exists():
            ttf_files = list(main_ttf.glob("*.ttf"))
        else:
            # fallback: recursive اما فقط در fonts/ (نه misc/)
            ttf_files = [
                p for p in fonts_dir.rglob("*.ttf")
                if "misc" not in p.parts and "Round-Dots" not in p.parts
            ]

        if not ttf_files:
            print(f"❌ هیچ فایل .ttf در {fonts_dir} پیدا نشد")
            return False

        loaded = 0
        loaded_families = set()

        for ttf in ttf_files:
            font_id = QFontDatabase.addApplicationFont(str(ttf))
            if font_id != -1:
                loaded += 1
                families = QFontDatabase.applicationFontFamilies(font_id)
                for fam in families:
                    loaded_families.add(fam)

        print(f"✅ فونت لود شد: {loaded} فایل از {len(ttf_files)}")
        print(f"   Familyها: {loaded_families}")

        return loaded > 0

    @classmethod
    def get(cls, size: int = SIZE_BASE, weight: str = "normal") -> QFont:
        """دریافت QFont."""
        font = QFont(cls.FAMILY, size)
        font.setStyleStrategy(QFont.PreferAntialias)

        if weight == "bold":
            font.setBold(True)
        elif weight == "medium":
            font.setWeight(QFont.Medium)

        return font


# === QSS (Global Stylesheet) ===

def get_global_qss() -> str:
    """استایل سراسری برای کل برنامه."""
    c = Colors
    f = Fonts

    return f"""
    /* === Base === */
    QWidget {{
        font-family: "{f.FAMILY}", "{f.FALLBACK}", sans-serif;
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_PRIMARY};
        background-color: {c.BG_MAIN};
    }}

    QMainWindow, QDialog {{
        background-color: {c.BG_MAIN};
    }}

    /* === Header === */
    QFrame#Header {{
        background-color: {c.BG_CARD};
        border-bottom: 1px solid {c.BORDER};
        border-radius: 0;
    }}

    QLabel#HeaderTitle {{
        font-size: {f.SIZE_LG}pt;
        font-weight: bold;
        color: {c.TEXT_PRIMARY};
    }}

    QLabel#HeaderSubtitle {{
        font-size: {f.SIZE_SM}pt;
        color: {c.TEXT_SECONDARY};
    }}

    /* === Sidebar === */
    QFrame#Sidebar {{
        background-color: {c.BG_SIDEBAR};
        border-left: 1px solid {c.BORDER};
        border-radius: 0;
    }}

    QPushButton#SidebarButton {{
        text-align: right;
        padding: 12px 15px;
        border: none;
        border-radius: 8px;
        background-color: transparent;
        color: {c.TEXT_PRIMARY};
        font-size: {f.SIZE_BASE}pt;
        margin: 2px 8px;
    }}

    QPushButton#SidebarButton:hover {{
        background-color: {c.BG_HOVER};
    }}

    QPushButton#SidebarButton:checked {{
        background-color: {c.PRIMARY_LIGHT};
        color: {c.PRIMARY_DARK};
        font-weight: bold;
    }}

    /* === Cards === */
    QFrame#Card {{
        background-color: {c.BG_CARD};
        border: 1px solid {c.BORDER};
        border-radius: 12px;
    }}

    QFrame#Card:hover {{
        border-color: {c.PRIMARY};
    }}

    QFrame#StatCard {{
        background-color: {c.BG_CARD};
        border: 1px solid {c.BORDER};
        border-radius: 12px;
        padding: 15px;
    }}

        QFrame#HeroCard {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.PRIMARY}, stop:1 {c.SECONDARY});
        border-radius: 16px;
        padding: 20px;
    }}

    QFrame#HeroCard QLabel {{
        background-color: transparent;
        color: white;
    }}

    /* === Buttons === */
    QPushButton#PrimaryButton {{
        background-color: {c.PRIMARY};
        color: {c.TEXT_WHITE};
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: {f.SIZE_BASE}pt;
        font-weight: bold;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: {c.PRIMARY_DARK};
    }}

    QPushButton#PrimaryButton:disabled {{
        background-color: {c.TEXT_MUTED};
    }}

    QPushButton#SecondaryButton {{
        background-color: {c.BG_CARD};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 10px 20px;
    }}

    QPushButton#SecondaryButton:hover {{
        background-color: {c.BG_HOVER};
    }}

    /* === Input === */
    QLineEdit {{
        background-color: {c.BG_CARD};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: {f.SIZE_BASE}pt;
    }}

    QLineEdit:focus {{
        border-color: {c.PRIMARY};
    }}

    /* === Text === */
    QLabel#PageTitle {{
        font-size: {f.SIZE_XXL}pt;
        font-weight: bold;
        color: {c.TEXT_PRIMARY};
    }}

    QLabel#PageSubtitle {{
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_SECONDARY};
    }}

    QLabel#CardTitle {{
        font-size: {f.SIZE_MD}pt;
        font-weight: bold;
        color: {c.TEXT_PRIMARY};
    }}

    QLabel#CardSubtitle {{
        font-size: {f.SIZE_SM}pt;
        color: {c.TEXT_SECONDARY};
    }}

    QLabel#StatValue {{
        font-size: {f.SIZE_HERO}pt;
        font-weight: bold;
        color: {c.PRIMARY};
    }}

    QLabel#StatLabel {{
        font-size: {f.SIZE_BASE}pt;
        color: {c.TEXT_SECONDARY};
    }}

    /* === Scroll === */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c.BORDER};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c.TEXT_MUTED};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* === Progress === */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {c.BORDER_LIGHT};
        height: 6px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {c.PRIMARY};
        border-radius: 4px;
    }}

    /* === Tabs === */
    QTabWidget::pane {{
        border: none;
        background-color: transparent;
    }}

    QTabBar::tab {{
        background-color: transparent;
        color: {c.TEXT_SECONDARY};
        padding: 8px 20px;
        border: none;
        border-bottom: 2px solid transparent;
    }}

    QTabBar::tab:selected {{
        color: {c.PRIMARY};
        border-bottom: 2px solid {c.PRIMARY};
        font-weight: bold;
    }}

    QTabBar::tab:hover {{
        color: {c.TEXT_PRIMARY};
    }}

    /* === Status Bar === */
    QStatusBar {{
        background-color: {c.BG_CARD};
        border-top: 1px solid {c.BORDER};
        color: {c.TEXT_SECONDARY};
    }}
    """