"""Shared chart style so every notebook figure looks the same on the slides."""

import matplotlib.pyplot as plt

# Validated categorical palette (colorblind-safe for these 3 adjacent hues). Fixed order, never cycled.
GROUP_COLORS = {"cafe": "#2a78d6", "restaurant": "#eb6834", "bar": "#1baf7a"}
SINGLE_COLOR = "#2a78d6"
TEXT, MUTED, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"


def use_style() -> None:
    """Thin marks, recessive axes and grid, text in ink colors (never series colors)."""
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": TEXT,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#e4e3df",
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": TEXT,
            "legend.frameon": False,
            "figure.dpi": 110,
            "savefig.bbox": "tight",
        }
    )
