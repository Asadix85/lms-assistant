"""تست theme و فونت."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import Colors, Fonts, get_global_qss


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تست فونت و تم")
        self.resize(700, 500)

        # Load fonts
        loaded = Fonts.load()
        print(f"\nنتیجه: {'✅' if loaded else '❌'}")

        # Apply QSS
        self.setStyleSheet(get_global_qss())

        # Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # === Title ===
        title = QLabel("سلام! این یک تست است 🎉")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignRight)
        layout.addWidget(title)

        # === Subtitle ===
        subtitle = QLabel(
            "اگر این متن را با فونت وزیرمتن می‌بینی، همه چیز کار می‌کند. "
            "اعداد: ۱۲۳۴۵۶۷۸۹۰ — حروف: ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setAlignment(Qt.AlignRight)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # === Stat Card ===
        stat_card = QFrame()
        stat_card.setObjectName("StatCard")
        stat_layout = QVBoxLayout(stat_card)
        stat_layout.setAlignment(Qt.AlignCenter)

        stat_value = QLabel("۱۲")
        stat_value.setObjectName("StatValue")
        stat_value.setAlignment(Qt.AlignCenter)
        stat_layout.addWidget(stat_value)

        stat_label = QLabel("درس فعال")
        stat_label.setObjectName("StatLabel")
        stat_label.setAlignment(Qt.AlignCenter)
        stat_layout.addWidget(stat_label)

        layout.addWidget(stat_card)

        # === Hero Card ===
        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(hero)

        hero_title = QLabel("🎓 LMS Assistant")
        hero_title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        hero_layout.addWidget(hero_title)

        hero_subtitle = QLabel("دستیار LMS دانشگاه اصفهان")
        hero_subtitle.setStyleSheet("color: white; font-size: 12pt;")
        hero_layout.addWidget(hero_subtitle)

        layout.addWidget(hero)

        layout.addStretch()

        # RTL
        self.setLayoutDirection(Qt.RightToLeft)


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())