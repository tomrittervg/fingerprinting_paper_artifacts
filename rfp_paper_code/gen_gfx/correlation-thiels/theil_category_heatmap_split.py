#!/usr/bin/env python3
"""Split-diagonal category heatmap for Theil's U.

Every cell is split by a diagonal:
  Lower-left triangle  = mean Theil's U (green colorscale)
  Upper-right triangle = max Theil's U  (yellow-to-red colorscale)

Two separate colorbars. Since Theil's U is asymmetric, the full matrix
is used (row predicts column), not mirrored.

Output:
  theil_category_heatmap_split{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
import numpy as np

from _theil_utils import (load_rows, get_category, CATEGORY_ORDER,
                           CATEGORY_COLORS, FILTER_SUFFIX, HERE)

# ── Aggregate ────────────────────────────────────────────────────────────────
n       = len(CATEGORY_ORDER)
cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
sums    = np.zeros((n, n))
maxes   = np.zeros((n, n))
counts  = np.zeros((n, n), dtype=int)

for r in load_rows():
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    u_ij = r['u_1to2']  # cat_i predicts cat_j
    u_ji = r['u_2to1']  # cat_j predicts cat_i

    sums[i, j]   += u_ij
    maxes[i, j]   = max(maxes[i, j], u_ij)
    counts[i, j] += 1

    if i != j:
        sums[j, i]   += u_ji
        maxes[j, i]   = max(maxes[j, i], u_ji)
        counts[j, i] += 1
    else:
        sums[i, i]   += u_ji
        maxes[i, i]   = max(maxes[i, i], u_ji)
        counts[i, i] += 1

with np.errstate(invalid='ignore'):
    means = np.where(counts > 0, sums / counts, 0.0)

# ── Colormaps ────────────────────────────────────────────────────────────────
cmap_mean = mcolors.LinearSegmentedColormap.from_list(
    'WhGn', ['#F7FCF5', '#C7E9C0', '#74C476', '#238B45', '#00441B'])
cmap_max = mcolors.LinearSegmentedColormap.from_list(
    'YlRd', ['#FFFFCC', '#FED976', '#FD8D3C', '#E31A1C', '#800026'])

vmax_mean = max(means.max(), 0.01)
vmax_max = max(maxes.max(), 0.01)
norm_mean = mcolors.Normalize(vmin=0, vmax=vmax_mean)
norm_max  = mcolors.Normalize(vmin=0, vmax=vmax_max)

# ── Layout ───────────────────────────────────────────────────────────────────
fig      = plt.figure(figsize=(12, 10))
ax_main  = fig.add_axes([0.15, 0.18, 0.62, 0.62])
ax_top   = fig.add_axes([0.15, 0.812, 0.62, 0.018])
ax_right = fig.add_axes([0.778, 0.18, 0.018, 0.62])
ax_cbar1 = fig.add_axes([0.82, 0.18, 0.015, 0.29])   # mean (green)
ax_cbar2 = fig.add_axes([0.82, 0.51, 0.015, 0.29])   # max (red)

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

# ── Draw cells ───────────────────────────────────────────────────────────────
ax_main.set_facecolor('white')

for i in range(n):
    for j in range(n):
        x0, x1 = j - 0.5, j + 0.5
        y0, y1 = i - 0.5, i + 0.5
        # Lower-left triangle: mean (green)
        ax_main.add_patch(Polygon(
            [(x0, y0), (x0, y1), (x1, y1)],
            closed=True, facecolor=cmap_mean(norm_mean(means[i, j])),
            edgecolor='none', zorder=2))
        # Upper-right triangle: max (yellow-red)
        ax_main.add_patch(Polygon(
            [(x0, y0), (x1, y0), (x1, y1)],
            closed=True, facecolor=cmap_max(norm_max(maxes[i, j])),
            edgecolor='none', zorder=2))

# White diagonal lines to separate triangles
for i in range(n):
    for j in range(n):
        ax_main.plot([j - 0.5, j + 0.5], [i - 0.5, i + 0.5],
                     color='white', lw=1.5, zorder=5, solid_capstyle='butt')

# ── Annotate ─────────────────────────────────────────────────────────────────
for i in range(n):
    for j in range(n):
        # Lower-left triangle centroid
        v = means[i, j]
        tc = 'white' if v > 0.4 * vmax_mean else 'black'
        ax_main.text(j - 0.18, i + 0.18, f'{v:.2f}',
                     ha='center', va='center', fontsize=6,
                     color=tc, fontweight='bold', zorder=6)
        # Upper-right triangle centroid
        v = maxes[i, j]
        tc = 'white' if v > 0.5 * vmax_max else 'black'
        ax_main.text(j + 0.18, i - 0.18, f'{v:.2f}',
                     ha='center', va='center', fontsize=6,
                     color=tc, fontweight='bold', zorder=6)

# ── Axis ─────────────────────────────────────────────────────────────────────
ax_main.set_xlim(-0.5, n - 0.5)
ax_main.set_ylim(n - 0.5, -0.5)
ax_main.set_xticks(range(n))
ax_main.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=10)
ax_main.set_yticks(range(n))
ax_main.set_yticklabels(CATEGORY_ORDER, fontsize=10)
ax_main.set_xlabel('Predicted category \u2192', fontsize=10)
ax_main.set_ylabel('\u2190 Predictor category', fontsize=10)

# ── Colorbars ────────────────────────────────────────────────────────────────
sm_mean = mcm.ScalarMappable(cmap=cmap_mean, norm=norm_mean)
sm_mean.set_array([])
cb1 = plt.colorbar(sm_mean, cax=ax_cbar1)
cb1.set_label('Mean U\n(lower-left)', fontsize=8)

sm_max = mcm.ScalarMappable(cmap=cmap_max, norm=norm_max)
sm_max.set_array([])
cb2 = plt.colorbar(sm_max, cax=ax_cbar2)
cb2.set_label('Max U\n(upper-right)', fontsize=8)

# ── Title ────────────────────────────────────────────────────────────────────
ax_top.text(0.5, 3.6,
            "Category Theil's U  (row predicts column)\n"
            "lower-left = mean (green)  |  upper-right = max (yellow\u2013red)",
            fontsize=11, ha='center', va='bottom',
            transform=ax_top.transAxes, clip_on=False)

out = HERE / f'theil_category_heatmap_split{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
