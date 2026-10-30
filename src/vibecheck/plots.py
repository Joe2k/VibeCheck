"""Chart style shared by the notebooks."""

import matplotlib.pyplot as plt

# Colorblind-safe for these three. Keep the order fixed.
GROUP_COLORS = {"cafe": "#2a78d6", "restaurant": "#eb6834", "bar": "#1baf7a"}
SINGLE_COLOR = "#2a78d6"
TEXT, MUTED, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"


def use_style() -> None:
    """Light grid, no top/right spines, muted axis text."""
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
