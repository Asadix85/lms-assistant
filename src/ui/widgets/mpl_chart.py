"""نمودار matplotlib قابل جاسازی در Qt."""

import re

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import font_manager

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from src.ui.theme import CurrentTheme


# === ثبت فونت Vazirmatn برای matplotlib ===
FONT_PATHS = [
    "assets/fonts/vazirmatn/fonts/ttf/Vazirmatn-Regular.ttf",
    "assets/fonts/vazirmatn/fonts/ttf/Vazirmatn-Bold.ttf",
    "assets/fonts/vazirmatn/fonts/ttf/Vazirmatn-Medium.ttf",
]

_loaded_fonts = []
for path in FONT_PATHS:
    try:
        font_manager.fontManager.addfont(path)
        _loaded_fonts.append(path)
    except Exception as e:
        print(f"⚠️ خطا در لود فونت {path}: {e}")

if _loaded_fonts:
    matplotlib.rcParams["font.family"] = "Vazirmatn"
    print(f"✅ فونت Vazirmatn برای matplotlib لود شد ({len(_loaded_fonts)} فایل)")

matplotlib.rcParams["axes.unicode_minus"] = False


# === Helper: تبدیل رنگ CSS به matplotlib ===
def _parse_color(color) -> str | tuple:
    """تبدیل رنگ CSS (`rgba(...)`) به فرمت matplotlib.

    matplotlib فقط hex، tuple یا اسم رنگ قبول می‌کنه.

    Examples:
        "rgba(42, 166, 163, 0.12)" → (0.165, 0.651, 0.639, 0.12)
        "#2AA6A3" → "#2AA6A3"
        (0.5, 0.5, 0.5) → (0.5, 0.5, 0.5)
    """
    if not isinstance(color, str):
        return color

    # rgba(r, g, b, a) یا rgb(r, g, b)
    match = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)",
        color,
    )
    if match:
        r = int(match.group(1)) / 255
        g = int(match.group(2)) / 255
        b = int(match.group(3)) / 255
        a = float(match.group(4)) if match.group(4) else 1.0
        return (r, g, b, a)

    # hex یا اسم رنگ
    return color


class MplChart(QWidget):
    """نمودار matplotlib قابل جاسازی در Qt."""

    def __init__(self, width: float = 5, height: float = 3) -> None:
        super().__init__()
        self.setStyleSheet("background: transparent;")

        self.fig = Figure(figsize=(width, height), dpi=100)
        self.fig.patch.set_alpha(0)  # پس‌زمینه شفاف

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def clear(self) -> None:
        """پاک کردن نمودار."""
        self.fig.clear()

    def draw(self) -> None:
        """رسم مجدد."""
        self.canvas.draw()

    # ============================================================
    # Pie Chart
    # ============================================================

    def plot_pie(
        self,
        data: dict[str, int],
        title: str = "",
        colors: list[str] | None = None,
    ) -> None:
        """نمودار دایره‌ای."""
        self.clear()

        c = CurrentTheme.colors()
        ax = self.fig.add_subplot(111)

        labels = list(data.keys())
        values = list(data.values())

        # فیلتر صفرها
        filtered = [(l, v) for l, v in zip(labels, values) if v > 0]
        if not filtered:
            ax.text(
                0.5, 0.5, "داده‌ای نیست",
                ha="center", va="center",
                fontsize=12,
                color=_parse_color(c.TEXT_MUTED),
                transform=ax.transAxes,
            )
            ax.axis("off")
            self.draw()
            return

        labels, values = zip(*filtered)

        # رنگ‌ها
        if colors is None:
            colors = [
                c.SUCCESS,
                c.WARNING,
                c.ERROR,
                c.PRIMARY,
                c.INFO,
                c.SECONDARY,
            ][:len(labels)]
        else:
            colors = [_parse_color(col) for col in colors]

        # نمودار
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.0f%%",
            colors=colors,
            startangle=90,
            textprops={
                "fontsize": 10,
                "color": _parse_color(c.TEXT_PRIMARY),
                "fontfamily": "Vazirmatn",
            },
        )

        # درصدها: سفید و بولد
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(9)

        if title:
            ax.set_title(
                title,
                fontsize=12,
                fontweight="bold",
                color=_parse_color(c.TEXT_PRIMARY),
                pad=12,
            )

        ax.axis("equal")
        self.fig.tight_layout()
        self.draw()

    # ============================================================
    # Bar Chart
    # ============================================================

    def plot_bar(
        self,
        data: dict[str, int],
        title: str = "",
        horizontal: bool = True,
    ) -> None:
        """نمودار میله‌ای (افقی یا عمودی)."""
        self.clear()

        c = CurrentTheme.colors()
        ax = self.fig.add_subplot(111)

        labels = list(data.keys())
        values = list(data.values())

        if not labels:
            ax.text(
                0.5, 0.5, "داده‌ای نیست",
                ha="center", va="center",
                fontsize=12,
                color=_parse_color(c.TEXT_MUTED),
                transform=ax.transAxes,
            )
            ax.axis("off")
            self.draw()
            return

        bar_color = _parse_color(c.PRIMARY)

        if horizontal:
            # افقی (برای RTL طبیعی‌تر)
            bars = ax.barh(
                labels, values,
                color=bar_color,
                height=0.6,
            )
            ax.invert_yaxis()  # بالاترین در بالا

            # اعداد روی میله‌ها
            for bar, val in zip(bars, values):
                ax.text(
                    val + max(values) * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    str(val),
                    va="center",
                    ha="left",
                    fontsize=10,
                    fontweight="bold",
                    color=bar_color,
                    fontfamily="Vazirmatn",
                )

            ax.set_xlim(0, max(values) * 1.15)

        else:
            # عمودی
            bars = ax.bar(
                labels, values,
                color=bar_color,
                width=0.6,
            )

            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    val + max(values) * 0.02,
                    str(val),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color=bar_color,
                    fontfamily="Vazirmatn",
                )

            ax.set_ylim(0, max(values) * 1.15)

        # استایل
        ax.tick_params(
            axis="both",
            labelsize=10,
            colors=_parse_color(c.TEXT_PRIMARY),
        )
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily("Vazirmatn")
            label.set_color(_parse_color(c.TEXT_PRIMARY))

        # حذف حاشیه‌ها
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(_parse_color(c.BORDER_LIGHT))
        ax.spines["bottom"].set_color(_parse_color(c.BORDER_LIGHT))

        # grid سبک
        ax.grid(
            axis="x" if horizontal else "y",
            linestyle="--",
            alpha=0.3,
            color=_parse_color(c.BORDER),
        )
        ax.set_axisbelow(True)

        if title:
            ax.set_title(
                title,
                fontsize=12,
                fontweight="bold",
                color=_parse_color(c.TEXT_PRIMARY),
                pad=12,
            )

        self.fig.tight_layout()
        self.draw()

    # ============================================================
    # Line Chart
    # ============================================================

    def plot_line(
        self,
        x_labels: list[str],
        y_values: list[int],
        title: str = "",
    ) -> None:
        """نمودار خطی."""
        self.clear()

        c = CurrentTheme.colors()
        ax = self.fig.add_subplot(111)

        if not x_labels:
            ax.text(
                0.5, 0.5, "داده‌ای نیست",
                ha="center", va="center",
                fontsize=12,
                color=_parse_color(c.TEXT_MUTED),
                transform=ax.transAxes,
            )
            ax.axis("off")
            self.draw()
            return

        line_color = _parse_color(c.PRIMARY)

        ax.plot(
            x_labels, y_values,
            marker="o",
            linewidth=2.5,
            markersize=8,
            color=line_color,
            markerfacecolor=line_color,
            markeredgecolor="white",
            markeredgewidth=1.5,
        )

        # پر کردن زیر نمودار
        ax.fill_between(
            range(len(x_labels)),
            y_values,
            alpha=0.15,
            color=line_color,
        )

        # استایل
        ax.tick_params(
            axis="both",
            labelsize=10,
            colors=_parse_color(c.TEXT_PRIMARY),
        )
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily("Vazirmatn")
            label.set_color(_parse_color(c.TEXT_PRIMARY))

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(_parse_color(c.BORDER_LIGHT))
        ax.spines["bottom"].set_color(_parse_color(c.BORDER_LIGHT))

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3,
            color=_parse_color(c.BORDER),
        )
        ax.set_axisbelow(True)

        if title:
            ax.set_title(
                title,
                fontsize=12,
                fontweight="bold",
                color=_parse_color(c.TEXT_PRIMARY),
                pad=12,
            )

        self.fig.tight_layout()
        self.draw()