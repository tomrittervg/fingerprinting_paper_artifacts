#!/usr/bin/env python3
"""Clustered AMI heatmap filtered to metrics with meaningful correlation.

Drops any metric whose maximum AMI with any other metric falls below
MIN_AMI_THRESHOLD (default 0.10, override via CORR_MIN_AMI env var).
This removes isolated metrics that contribute visual noise (dark rows/cols)
and lets the heatmap focus on the correlated structure.

Outputs corr_all_heatmap_minami{FILTER_SUFFIX}.png.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, leaves_list
from pathlib import Path

from _corr_utils import load_rows, load_per_metric, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

MIN_AMI = float(os.environ.get('CORR_MIN_AMI', '0.10'))
OUT_PATH = HERE / f'corr_all_heatmap_minami{FILTER_SUFFIX}.png'

print("Loading pairs…")
rows = load_rows()
_, max_ami = load_per_metric(rows)

# Filter to metrics with at least one strong correlation
keep = {m for m, v in max_ami.items() if v >= MIN_AMI}
rows = [r for r in rows if r['metric1'] in keep and r['metric2'] in keep]

metrics = sorted(keep)
m_idx = {m: i for i, m in enumerate(metrics)}
n = len(metrics)
n_dropped = len(max_ami) - n
print(f"  {len(max_ami)} metrics total; kept {n} with max_AMI ≥ {MIN_AMI:.2f} (dropped {n_dropped})")
print(f"  {len(rows):,} pairs after filter")

# ── Build dense AMI matrix ────────────────────────────────────────────────────
print("Building matrix…")
mat = np.zeros((n, n), dtype=np.float32)
np.fill_diagonal(mat, 1.0)
for r in rows:
    i, j = m_idx[r['metric1']], m_idx[r['metric2']]
    mat[i, j] = r['ami']
    mat[j, i] = r['ami']

# ── Hierarchical clustering ───────────────────────────────────────────────────
print("Clustering…")
dist_condensed = squareform((1.0 - mat).astype(np.float64), checks=False)
Z = linkage(dist_condensed, method='average')
order = leaves_list(Z)

mat_ordered = mat[np.ix_(order, order)]
metrics_ordered = [metrics[i] for i in order]
cats_ordered = [get_category(m) for m in metrics_ordered]

# ── Category color arrays for margin strips ───────────────────────────────────
cat_colors = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                        for c in (CATEGORY_COLORS[cat] for cat in cats_ordered)],
                       dtype=np.uint8)

# ── Plot ──────────────────────────────────────────────────────────────────────
print("Plotting…")
STRIP_W = max(8, n // 50)
fig_size = 16
dpi = 150
fig = plt.figure(figsize=(fig_size, fig_size), dpi=dpi)

ax_main = fig.add_axes([0.06, 0.06, 0.82, 0.82])
ax_cbar = fig.add_axes([0.90, 0.06, 0.015, 0.82])
ax_top  = fig.add_axes([0.06, 0.888, 0.82, 0.025])
ax_left = fig.add_axes([0.033, 0.06, 0.025, 0.82])

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

handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.06, 0.995),
           fontsize=7, ncol=7, framealpha=0.9, title='Category (margin color strips)')

fig.suptitle(
    f'Pairwise AMI Heatmap — metrics with max AMI ≥ {MIN_AMI:.2f}  '
    f'({n} of {len(max_ami)} metrics, avg linkage)\n'
    f'bin threshold = 30  |  dropped {n_dropped} isolated metrics',
    fontsize=11, y=0.995,
)
fig.savefig(OUT_PATH, dpi=dpi, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
