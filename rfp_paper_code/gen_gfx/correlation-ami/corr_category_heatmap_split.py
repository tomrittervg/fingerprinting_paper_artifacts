#!/usr/bin/env python3
"""Split-diagonal category heatmap.

Lower-left triangle = mean AMI between categories.
Upper-right triangle = max AMI between categories.
Diagonal cells are split by a white line; each half shows the within-category value.

Outputs corr_category_heatmap_split{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
import numpy as np

from _corr_utils import (load_rows, get_category, CATEGORY_ORDER,
                          CATEGORY_COLORS, FILTER_SUFFIX, HERE)

OUT_PATH = HERE / f'corr_category_heatmap_split{FILTER_SUFFIX}.png'

# ── Aggregate ──────────────────────────────────────────────────────────────────
n       = len(CATEGORY_ORDER)
cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
sums    = np.zeros((n, n))
maxes   = np.zeros((n, n))
counts  = np.zeros((n, n), dtype=int)

for r in load_rows():
    ami = r['ami']
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    if i == j:
        sums[i, j]   += ami
        maxes[i, j]   = max(maxes[i, j], ami)
        counts[i, j] += 1
    else:
        for a, b in ((i, j), (j, i)):
            sums[a, b]   += ami
            maxes[a, b]   = max(maxes[a, b], ami)
            counts[a, b] += 1

means = np.where(counts > 0, sums / counts, 0.0)

# ── Colormap ───────────────────────────────────────────────────────────────────
cmap = mcolors.LinearSegmentedColormap.from_list(
    'WhRd', ['white', '#FFCCCC', '#FF6666', '#CC0000', '#800000']
)
norm = mcolors.Normalize(vmin=0, vmax=1)

# ── Layout ─────────────────────────────────────────────────────────────────────
fig      = plt.figure(figsize=(12, 10))
ax_main  = fig.add_axes([0.15, 0.20, 0.65, 0.62])
ax_top   = fig.add_axes([0.15, 0.832, 0.65, 0.018])
ax_right = fig.add_axes([0.808, 0.20, 0.018, 0.62])
ax_cbar  = fig.add_axes([0.840, 0.20, 0.015, 0.62])

# Category color strips
cat_rgb = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                    for c in (CATEGORY_COLORS[cat] for cat in CATEGORY_ORDER)],
                   dtype=np.uint8)
STRIP_W = 8
ax_top.imshow(np.tile(cat_rgb[np.newaxis, :, :], (STRIP_W, 1, 1)),
              aspect='auto', interpolation='nearest')
ax_top.axis('off')
ax_right.imshow(np.tile(cat_rgb[:, np.newaxis, :], (1, STRIP_W, 1)),
                aspect='auto', interpolation='nearest', origin='upper')
ax_right.axis('off')

# ── Draw cells ─────────────────────────────────────────────────────────────────
ax_main.set_facecolor('white')

for i in range(n):
    for j in range(n):
        if i == j:
            x0, x1 = j - 0.5, j + 0.5
            y0, y1 = i - 0.5, i + 0.5
            # Lower-left triangle (visually): top-left, bottom-left, bottom-right
            ax_main.add_patch(Polygon(
                [(x0, y0), (x0, y1), (x1, y1)],
                closed=True, facecolor=cmap(norm(means[i, j])),
                edgecolor='none', zorder=2))
            # Upper-right triangle (visually): top-left, top-right, bottom-right
            ax_main.add_patch(Polygon(
                [(x0, y0), (x1, y0), (x1, y1)],
                closed=True, facecolor=cmap(norm(maxes[i, j])),
                edgecolor='none', zorder=2))
        elif i > j:
            # Lower-left half of matrix: mean AMI
            ax_main.add_patch(mpatches.Rectangle(
                (j - 0.5, i - 0.5), 1.0, 1.0,
                facecolor=cmap(norm(means[i, j])), edgecolor='none', zorder=1))
        else:
            # Upper-right half of matrix: max AMI
            ax_main.add_patch(mpatches.Rectangle(
                (j - 0.5, i - 0.5), 1.0, 1.0,
                facecolor=cmap(norm(maxes[i, j])), edgecolor='none', zorder=1))

# White diagonal line to separate the two halves
for i in range(n):
    ax_main.plot([i - 0.5, i + 0.5], [i - 0.5, i + 0.5],
                 color='white', lw=5, zorder=5, solid_capstyle='butt')

# ── Annotate ───────────────────────────────────────────────────────────────────
for i in range(n):
    for j in range(n):
        if i == j:
            # Centroid of lower-left triangle: (j - 1/6, i + 1/6)
            v = means[i, j]
            tc = 'white' if v > 0.6 else 'black'
            ax_main.text(j - 0.18, i + 0.18, f'{v:.2f}',
                         ha='center', va='center', fontsize=7,
                         color=tc, fontweight='bold', zorder=6)
            # Centroid of upper-right triangle: (j + 1/6, i - 1/6)
            v = maxes[i, j]
            tc = 'white' if v > 0.6 else 'black'
            ax_main.text(j + 0.18, i - 0.18, f'{v:.2f}',
                         ha='center', va='center', fontsize=7,
                         color=tc, fontweight='bold', zorder=6)
        elif i > j:
            v, cnt = means[i, j], counts[i, j]
            tc = 'white' if v > 0.55 else 'black'
            ax_main.text(j, i, f'{v:.2f}', ha='center', va='center',
                         fontsize=9, color=tc, fontweight='bold')
            if cnt > 0:
                ax_main.text(j, i + 0.38, f'({cnt:,})', ha='center', va='center',
                             fontsize=4.5, color=tc, alpha=0.75)
        else:
            v, cnt = maxes[i, j], counts[i, j]
            tc = 'white' if v > 0.55 else 'black'
            ax_main.text(j, i, f'{v:.2f}', ha='center', va='center',
                         fontsize=9, color=tc, fontweight='bold')
            if cnt > 0:
                ax_main.text(j, i + 0.38, f'({cnt:,})', ha='center', va='center',
                             fontsize=4.5, color=tc, alpha=0.75)

# ── Axis ───────────────────────────────────────────────────────────────────────
ax_main.set_xlim(-0.5, n - 0.5)
ax_main.set_ylim(n - 0.5, -0.5)   # invert: row 0 at top
ax_main.set_xticks(range(n))
ax_main.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=10)
ax_main.set_yticks(range(n))
ax_main.set_yticklabels(CATEGORY_ORDER, fontsize=10)

# ── Colorbar ───────────────────────────────────────────────────────────────────
sm = mcm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
plt.colorbar(sm, cax=ax_cbar, label='AMI')

# ── Category labels + title ────────────────────────────────────────────────────
for k, cat in enumerate(CATEGORY_ORDER):
    ax_top.text(k, -0.5, cat, fontsize=7, rotation=45,
                ha='left', va='bottom',
                transform=ax_top.transData, clip_on=False)

ax_top.text(0.5, 3.6,
            'Category AMI  (lower-left = mean  |  upper-right = max)',
            fontsize=12, ha='center', va='bottom',
            transform=ax_top.transAxes, clip_on=False)

fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
