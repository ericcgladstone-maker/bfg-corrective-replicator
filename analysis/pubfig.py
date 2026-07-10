"""Shared publication figure style for the manuscript. Colorblind-safe (Wong) palette,
consistent fonts/sizes, clean spines, 300 dpi. Import and call apply() before plotting;
use COL for the standard condition colors and panel() for A/B labels."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Wong colorblind-safe palette
COL = {
    "ecm": "#0072B2",       # blue: error correction / fitness pruning
    "no": "#D55E00",        # vermillion: no correction / random pruning
    "accent": "#009E73",    # green: advantage / difference
    "gray": "#555555",
    "light": "#CCCCCC",
}


def apply():
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11.5,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "grid.color": "#E6E6E6",
        "grid.linewidth": 0.8,
        "legend.frameon": False,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "lines.linewidth": 2.0,
        "lines.markersize": 6,
        "errorbar.capsize": 3,
    })


def panel(ax, letter, dx=-0.14, dy=1.06):
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=14, fontweight="bold",
            va="top", ha="left")


def finish(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
