"""Conceptual schematic (Fig 1): the model cycle (A) and how correction constrains variation (B).
Hand-drawn in matplotlib in the shared pubfig palette. No data; purely explanatory."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROJECT = os.path.dirname(HERE)
import pubfig
pubfig.apply()
COL = pubfig.COL
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse

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

# ---------------- Panel B: constrained variation ----------------
axB.set_title("Correction confines variation to admissible forms", fontweight="bold", loc="center")
pubfig.panel(axB, "B", dx=-0.10, dy=1.02)
axB.set_xlim(0, 10); axB.set_ylim(0, 10); axB.axis("off")

# admissible set (valid word forms) as a shaded region that contains the target components
adm = Ellipse((6.3, 5.6), 7.0, 6.6, angle=12, facecolor="#EAF3FA",
              edgecolor=COL["ecm"], lw=1.6, alpha=0.9, zorder=1)
axB.add_patch(adm)
axB.text(6.9, 9.0, "admissible set\n(valid word forms)", ha="center", va="center",
         color=COL["ecm"], fontsize=8.5)
for tx, ty in [(5.3, 6.2), (7.6, 4.6), (6.6, 7.2)]:
    axB.plot(tx, ty, marker="*", ms=13, color="#333333", zorder=5)
axB.text(4.9, 5.4, "target\ncomponents", ha="center", va="top", fontsize=8)

# parent near the edge
px, py = 2.0, 3.2
axB.plot(px, py, "o", ms=9, color="#333333", zorder=6)
axB.text(px, py - 0.55, "parent", ha="center", va="top", fontsize=8.5)

# uncorrected mutation: offspring scattered broadly, several outside the admissible set
offs = [(3.5, 1.0), (1.0, 5.4), (3.9, 3.1), (0.9, 2.0), (2.5, 6.7)]
for ox, oy in offs:
    axB.add_patch(FancyArrowPatch((px, py), (ox, oy), arrowstyle="-|>", mutation_scale=11,
                                  lw=1.2, color=COL["no"], alpha=0.7, zorder=3))
    axB.plot(ox, oy, "o", ms=5, color=COL["no"], zorder=4)
axB.text(1.1, 0.3, "uncorrected mutation:\ndisperses broadly", color=COL["no"], fontsize=8.5, ha="left")

# correction: projects the outside offspring onto the admissible set
for (ox, oy), (tx, ty) in [((3.5, 1.0), (4.7, 3.6)), ((0.9, 2.0), (3.5, 4.4)), ((1.0, 5.4), (3.3, 5.6))]:
    axB.add_patch(FancyArrowPatch((ox, oy), (tx, ty), arrowstyle="-|>", mutation_scale=11,
                                  lw=1.7, color=COL["ecm"], ls="--", connectionstyle="arc3,rad=0.2", zorder=4))
axB.text(8.9, 1.7, "correction:\nprojects outputs\nonto admissible forms",
         color=COL["ecm"], fontsize=8.5, ha="center")

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
plt.close(fig)
print("schematic ->", OUT)
