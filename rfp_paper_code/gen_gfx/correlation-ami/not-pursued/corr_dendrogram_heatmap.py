#!/usr/bin/env python3
"""Clustered heatmap with dendrogram margins.

Shows the same hierarchical clustering as corr_clustered_heatmap but adds
the dendrogram tree on the top and left margins so the merging structure is
visible. Category color strips sit between the dendrogram and the heatmap.

Outputs corr_dendrogram_heatmap{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, leaves_list, dendrogram

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_dendrogram_heatmap{FILTER_SUFFIX}.png'

print("Loading pairs…")
rows    = load_rows()
metrics = sorted({r['metric1'] for r in rows} | {r['metric2'] for r in rows})
m_idx   = {m: i for i, m in enumerate(metrics)}
n       = len(metrics)
print(f"  {n} metrics, {len(rows):,} pairs")

# ── AMI matrix ────────────────────────────────────────────────────────────────
mat = np.zeros((n, n), dtype=np.float32)
np.fill_diagonal(mat, 1.0)
for r in rows:
    i, j = m_idx[r['metric1']], m_idx[r['metric2']]
    mat[i, j] = r['ami']
    mat[j, i] = r['ami']

# ── Clustering ────────────────────────────────────────────────────────────────
print("Clustering…")
dist = squareform((1.0 - mat).astype(np.float64), checks=False)
Z     = linkage(dist, method='average')
order = leaves_list(Z)

mat_ord  = mat[np.ix_(order, order)]
cats_ord = [get_category(metrics[i]) for i in order]
cat_rgb  = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                      for c in (CATEGORY_COLORS[c] for c in cats_ord)],
                     dtype=np.uint8)

# ── Figure layout ──────────────────────────────────────────────────────────────
# [left_dendro] [cat_strip_left] [heatmap] [cat_strip_top_placeholder] [colorbar]
# [           ] [               ] [top_dendro                        ]
print("Plotting…")

STRIP = max(6, n // 60)
fig = plt.figure(figsize=(17, 17), dpi=150)

# Axes: fractions of figure
L, B, W, H = 0.07, 0.07, 0.72, 0.72

ax_heat   = fig.add_axes([L,           B,           W,     H    ])
ax_cbar   = fig.add_axes([L+W+0.015,   B,           0.015, H    ])
ax_top_d  = fig.add_axes([L,           B+H+0.005,   W,     0.10 ])
ax_left_d = fig.add_axes([L-0.11,      B,           0.10,  H    ])
ax_cat_t  = fig.add_axes([L,           B+H+0.117,   W,     0.012])  # cat strip top
ax_cat_l  = fig.add_axes([L-0.012,     B,           0.010, H    ])  # cat strip left

# Draw dendrogram — top
ddata_top = dendrogram(Z, ax=ax_top_d, orientation='top',
                       no_labels=True, color_threshold=0,
                       above_threshold_color='#444444',
                       link_color_func=lambda k: '#444444')
ax_top_d.axis('off')

# Draw dendrogram — left (same Z, orientation='left')
ddata_left = dendrogram(Z, ax=ax_left_d, orientation='left',
                        no_labels=True, color_threshold=0,
                        above_threshold_color='#444444',
                        link_color_func=lambda k: '#444444')
ax_left_d.axis('off')

# Category strips
STRIP_W = max(8, n // 50)
h_strip = np.tile(cat_rgb[np.newaxis, :, :], (STRIP_W, 1, 1))
v_strip = np.tile(cat_rgb[:, np.newaxis, :], (1, STRIP_W, 1))
ax_cat_t.imshow(h_strip, aspect='auto', interpolation='nearest')
ax_cat_t.axis('off')
ax_cat_l.imshow(v_strip, aspect='auto', interpolation='nearest', origin='upper')
ax_cat_l.axis('off')

# Heatmap
im = ax_heat.imshow(mat_ord, cmap='viridis', vmin=0, vmax=1,
                    aspect='auto', interpolation='nearest', origin='upper')
ax_heat.axis('off')
plt.colorbar(im, cax=ax_cbar, label='AMI')

# Legend
handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.07, 0.995),
           fontsize=7, ncol=7, framealpha=0.9, title='Category')

fig.suptitle(
    f'Pairwise AMI — hierarchical clustering with dendrogram  ({n} metrics)\n'
    'average linkage on 1−AMI distance  |  bin threshold = 30',
    fontsize=11, y=0.998,
)
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
