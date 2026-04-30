#!/usr/bin/env python3
"""Category-level aggregate heatmap: mean AMI only.

Single panel showing mean AMI between metric categories.
Outputs corr_category_heatmap_mean.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_category_heatmap_mean{FILTER_SUFFIX}.png'

n       = len(CATEGORY_ORDER)
cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
sums    = np.zeros((n, n))
counts  = np.zeros((n, n), dtype=int)

for r in load_rows():
    ami = r['ami']
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    if i == j:
        sums[i, j]   += ami
        counts[i, j] += 1
    else:
        for a, b in ((i, j), (j, i)):
            sums[a, b]   += ami
            counts[a, b] += 1

means = np.where(counts > 0, sums / counts, 0.0)

# ── Custom colormap: white at 0 → dark red at 1 ──────────────────────────────
cmap = mcolors.LinearSegmentedColormap.from_list(
    'WhRd', ['white', '#FFCCCC', '#FF6666', '#CC0000', '#800000']
)

# ── Category color arrays for strips ─────────────────────────────────────────
cat_colors = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                        for c in (CATEGORY_COLORS[cat] for cat in CATEGORY_ORDER)],
                       dtype=np.uint8)

# ── Figure layout ─────────────────────────────────────────────────────────────
STRIP_W  = 8
fig      = plt.figure(figsize=(10, 9))
ax_main  = fig.add_axes([0.15, 0.20, 0.65, 0.62])
ax_top   = fig.add_axes([0.15, 0.832, 0.65, 0.018])
ax_right = fig.add_axes([0.808, 0.20, 0.018, 0.62])
ax_cbar  = fig.add_axes([0.840, 0.20, 0.015, 0.62])

h_strip = np.tile(cat_colors[np.newaxis, :, :], (STRIP_W, 1, 1))
v_strip = np.tile(cat_colors[:, np.newaxis, :], (1, STRIP_W, 1))

ax_top.imshow(h_strip, aspect='auto', interpolation='nearest')
ax_top.axis('off')
ax_right.imshow(v_strip, aspect='auto', interpolation='nearest', origin='upper')
ax_right.axis('off')

# ── Main heatmap ──────────────────────────────────────────────────────────────
im = ax_main.imshow(means, cmap=cmap, vmin=0, vmax=1, aspect='auto')
ax_main.set_xticks(range(n))
ax_main.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=10)
ax_main.set_yticks(range(n))
ax_main.set_yticklabels(CATEGORY_ORDER, fontsize=10)

# Annotate cells
for i in range(n):
    for j in range(n):
        v   = means[i, j]
        cnt = counts[i, j]
        txt_color = 'white' if v > 0.55 else 'black'
        ax_main.text(j, i, f'{v:.2f}', ha='center', va='center',
                     fontsize=9, color=txt_color, fontweight='bold')
        if cnt > 0:
            ax_main.text(j, i + 0.38, f'({cnt:,})', ha='center', va='center',
                         fontsize=4.5, color=txt_color, alpha=0.75)

plt.colorbar(im, cax=ax_cbar)
fig.suptitle('Category-Level Mean AMI Heatmap', fontsize=13, y=0.87)
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
