"""Loading Spinner: انیمیشن چرخشی."""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QMovie

from src.ui.theme import CurrentTheme


class LoadingSpinner(QWidget):
    """اسپینر چرخشی با CSS animation."""

    def __init__(self, text: str = "در حال بارگذاری...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self._angle = 0
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build()
        self._start_animation()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Spinner (با QLabel و rotate)
        self.spinner = QLabel("◐")
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setStyleSheet(
            f"color: {c.PRIMARY}; font-size: 48pt; background: transparent;"
        )
        layout.addWidget(self.spinner)

        # Text
        self.text_label = QLabel(self._text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 11pt; "
            "background: transparent;"
        )
        layout.addWidget(self.text_label)

    def _start_animation(self) -> None:
        """شروع انیمیشن."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(100)  # هر ۱۰۰ms

    def _rotate(self) -> None:
        """چرخش."""
        chars = ["◐", "◓", "◑", "◒"]
        self._angle = (self._angle + 1) % 4
        self.spinner.setText(chars[self._angle])

    def set_text(self, text: str) -> None:
        """تغییر متن."""
        self.text_label.setText(text)

    def stop(self) -> None:
        """توقف انیمیشن."""
        if hasattr(self, "_timer"):
            self._timer.stop()