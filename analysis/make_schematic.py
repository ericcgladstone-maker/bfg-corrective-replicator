"""Conceptual schematic (Fig 1): the model cycle (A) and the finishing mechanism (B).
Hand-drawn in matplotlib in the shared pubfig palette. No data; purely explanatory."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROJECT = os.path.dirname(HERE)
import pubfig
pubfig.apply()
COL = pubfig.COL
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(PROJECT, "figures", "pub", "fig1_schematic.png")

fig, (axA, axB) = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})

# ---------------- Panel A: the generation cycle ----------------
axA.set_xlim(0, 10); axA.set_ylim(0, 10); axA.axis("off")
pubfig.panel(axA, "A", dx=-0.02, dy=1.02)
axA.set_title("A single generation", fontweight="bold", loc="center")

boxes = [
    (1.6, 7.3, "Replicator\n(a sentence)", "#EEEEEE"),
    (5.0, 7.3, "Mutation\nrandom character edits", "#FBE3D3"),
    (8.4, 7.3, "Correction\nsnap words to the\nnearest real words", "#D6E7F2"),
]
bw, bh = 2.6, 1.9
cx = {}
for x, y, label, fc in boxes:
    b = FancyBboxPatch((x - bw / 2, y - bh / 2), bw, bh, boxstyle="round,pad=0.08,rounding_size=0.18",
                       linewidth=1.3, edgecolor="#888888", facecolor=fc)
    axA.add_patch(b)
    axA.text(x, y, label, ha="center", va="center", fontsize=9.5)
    cx[label[:4]] = (x, y)

# selection box (wider, below)
sel = FancyBboxPatch((2.7, 2.2), 4.6, 2.0, boxstyle="round,pad=0.08,rounding_size=0.18",
                     linewidth=1.3, edgecolor="#888888", facecolor="#DFF0E6")
axA.add_patch(sel)
axA.text(5.0, 3.2, "Selection into peak niches\n(fittest fill each peak's slots;\nthe rest wait in the valley pool)",
         ha="center", va="center", fontsize=9.5)

def arrow(x1, y1, x2, y2, color="#555555", style="-|>", rad=0.0, lw=1.6):
    axA.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                  linewidth=lw, color=color,
                                  connectionstyle=f"arc3,rad={rad}"))

arrow(2.9, 7.3, 3.7, 7.3)               # replicator -> mutation
arrow(6.3, 7.3, 7.1, 7.3)               # mutation -> correction
arrow(8.4, 6.35, 6.9, 4.2, rad=-0.25)   # correction -> selection
arrow(3.1, 4.2, 1.6, 6.35, rad=-0.25, color=COL["accent"])  # selection -> next gen (loop)
axA.text(1.0, 5.3, "next\ngeneration", color=COL["accent"], fontsize=8.5, ha="center", style="italic")

# worked example strip
axA.text(5.0, 0.9, "example:  “to be or not to be”  →  “tob eor nvt to be”  →  “to be or not to be”",
         ha="center", va="center", fontsize=9, family="monospace")
axA.text(5.0, 0.2, "original            mutated (non-words)          corrected", ha="center", va="center",
         fontsize=7.5, color="#777777")

# ---------------- Panel B: the finishing mechanism ----------------
axB.set_title("Why correction helps: it finishes the climb", fontweight="bold", loc="center")
pubfig.panel(axB, "B", dx=-0.10, dy=1.02)
x = np.linspace(0, 10, 500)
land = (np.exp(-((x - 2.2) ** 2) / 0.7) * 0.55 +
        np.exp(-((x - 5.2) ** 2) / 0.5) * 1.0 +
        np.exp(-((x - 8.0) ** 2) / 0.8) * 0.75)
axB.plot(x, land, color="#999999", lw=2)
axB.fill_between(x, 0, land, color="#F2F2F2")
axB.set_xlim(0, 10); axB.set_ylim(0, 1.5)
axB.set_xlabel("genotype space"); axB.set_ylabel("fitness")
axB.set_xticks([]); axB.set_yticks([])
axB.spines["left"].set_visible(True)

peak_x, peak_y = 5.2, 1.0
axB.plot([peak_x], [peak_y], marker="*", ms=18, color="#333333", zorder=5)
axB.text(peak_x, peak_y + 0.12, "exact solution", ha="center", fontsize=9)

# a near-correct variant just below the peak
nx, ny = 4.55, 0.80
axB.plot([nx], [ny], "o", ms=10, color="#333333", zorder=6)
axB.text(nx - 0.15, ny - 0.16, "near-correct\nvariant", ha="center", va="top", fontsize=8.5)

# without correction: mutation knocks it back down (vermillion)
axB.add_patch(FancyArrowPatch((nx, ny), (3.0, 0.28), arrowstyle="-|>", mutation_scale=15,
                              linewidth=2.2, color=COL["no"], connectionstyle="arc3,rad=0.35", zorder=4))
axB.text(2.9, 0.42, "without correction:\nmutation displaces it", color=COL["no"], fontsize=8.5, ha="center")

# with correction: protected, completes the climb (blue)
axB.add_patch(FancyArrowPatch((nx, ny), (peak_x - 0.12, peak_y - 0.03), arrowstyle="-|>", mutation_scale=15,
                              linewidth=2.4, color=COL["ecm"], connectionstyle="arc3,rad=-0.3", zorder=4))
axB.text(4.9, 1.28, "with correction:\nheld until it finishes", color=COL["ecm"], fontsize=8.5, ha="center")

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
print("schematic ->", OUT)
