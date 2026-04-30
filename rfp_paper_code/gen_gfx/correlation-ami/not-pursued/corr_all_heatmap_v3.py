#!/usr/bin/env python3
"""Full pairwise AMI heatmap with hierarchical clustering (Ward linkage).

Same as corr_all_heatmap.py but uses method='ward' for linkage.
Ward requires euclidean metric, so uses squareform of 1-AMI matrix directly.
Outputs corr_all_heatmap_ward.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, leaves_list
from pathlib import Path

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_all_heatmap_ward{FILTER_SUFFIX}.png'

print("Loading pairs…")
rows    = load_rows()
metrics = sorted({r['metric1'] for r in rows} | {r['metric2'] for r in rows})
m_idx   = {m: i for i, m in enumerate(metrics)}
n       = len(metrics)
print(f"  {n} metrics, {len(rows):,} pairs")

# ── Build dense AMI matrix ────────────────────────────────────────────────────
print("Building matrix…")
mat = np.zeros((n, n), dtype=np.float32)
np.fill_diagonal(mat, 1.0)
for r in rows:
    i, j = m_idx[r['metric1']], m_idx[r['metric2']]
    mat[i, j] = r['ami']
    mat[j, i] = r['ami']

# ── Hierarchical clustering ───────────────────────────────────────────────────
# Ward linkage requires euclidean distances; use 1-AMI distance matrix directly.
print("Clustering (ward linkage)…")
dist_condensed = squareform((1.0 - mat).astype(np.float64), checks=False)
Z     = linkage(dist_condensed, method='ward')
order = leaves_list(Z)

mat_ordered  = mat[np.ix_(order, order)]
cats_ordered = [get_category(metrics[i]) for i in order]

# ── Category color arrays for margin strips ───────────────────────────────────
cat_colors = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                        for c in (CATEGORY_COLORS[c] for c in cats_ordered)],
                       dtype=np.uint8)

# ── Plot ──────────────────────────────────────────────────────────────────────
print("Plotting…")
STRIP_W  = max(8, n // 50)   # width (pixels) of category color strip
fig_size = 16
dpi      = 150
fig = plt.figure(figsize=(fig_size, fig_size), dpi=dpi)

# Main axes: the heatmap fills almost the full figure
# We carve out space for color strips and a colorbar
ax_main  = fig.add_axes([0.06, 0.06, 0.82, 0.82])
ax_cbar  = fig.add_axes([0.90, 0.06, 0.015, 0.82])
ax_top   = fig.add_axes([0.06, 0.888, 0.82, 0.025])   # top strip
ax_left  = fig.add_axes([0.033, 0.06, 0.025, 0.82])   # left strip

# Build RGB strip images
h_strip = np.tile(cat_colors[np.newaxis, :, :], (STRIP_W, 1, 1))
v_strip = np.tile(cat_colors[:, np.newaxis, :], (1, STRIP_W, 1))

ax_top.imshow(h_strip, aspect='auto', interpolation='nearest')
ax_top.axis('off')

ax_left.imshow(v_strip, aspect='auto', interpolation='nearest', origin='upper')
ax_left.axis('off')

im = ax_main.imshow(mat_ordered, cmap='viridis', vmin=0, vmax=1,
                    aspect='auto', interpolation='nearest', origin='upper')
ax_main.axis('off')

plt.colorbar(im, cax=ax_cbar, label='AMI')

# ── Category legend ───────────────────────────────────────────────────────────
handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.06, 0.995),
           fontsize=7, ncol=7, framealpha=0.9, title='Category (margin color strips)')

fig.suptitle(
    f'Pairwise AMI Heatmap  ({n} metrics, hierarchically clustered by ward linkage)\n'
    'bin threshold = 30',
    fontsize=11, y=0.995,
)
fig.savefig(OUT_PATH, dpi=dpi, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
