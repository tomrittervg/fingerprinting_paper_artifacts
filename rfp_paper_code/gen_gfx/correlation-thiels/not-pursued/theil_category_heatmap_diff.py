#!/usr/bin/env python3
"""Category-level Theil's U asymmetry heatmap: mean U(i→j) - mean U(j→i).

Positive (red) = row category predicts column better than vice versa.
Derived from the mean heatmap data — same info, just highlights directionality.

Output:
  theil_category_heatmap_diff{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from _theil_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

n       = len(CATEGORY_ORDER)
cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}

sums    = np.zeros((n, n))
counts  = np.zeros((n, n), dtype=int)

for r in load_rows():
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    u_ij = r['u_1to2']
    u_ji = r['u_2to1']

    sums[i, j]   += u_ij
    counts[i, j] += 1
    if i != j:
        sums[j, i]   += u_ji
        counts[j, i] += 1
    else:
        sums[i, i]   += u_ji
        counts[i, i] += 1

with np.errstate(invalid='ignore'):
    means = np.where(counts > 0, sums / counts, 0.0)

diff = means - means.T


def _axis_labels(ax, fs=9):
    ax.set_xticks(range(n))
    ax.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=fs)
    ax.set_yticks(range(n))
    ax.set_yticklabels(CATEGORY_ORDER, fontsize=fs)


def _add_color_strips(ax):
    for i, cat in enumerate(CATEGORY_ORDER):
        ax.add_patch(plt.Rectangle(
            (-1.55, i - 0.5), 0.45, 1.0,
            color=CATEGORY_COLORS[cat], clip_on=False,
            transform=ax.transData,
        ))


fig, ax = plt.subplots(figsize=(10, 8))
vmax = max(abs(diff.min()), abs(diff.max()), 0.01)
im = ax.imshow(diff, cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='auto')
_axis_labels(ax, fs=10)
ax.set_title("Theil's U Asymmetry: mean U(row\u2192col) \u2212 mean U(col\u2192row)", fontsize=11)
ax.set_xlabel('Column category', fontsize=10)
ax.set_ylabel('Row category', fontsize=10)
plt.colorbar(im, ax=ax, shrink=0.82, label='Red = row predicts col better')
for i in range(n):
    for j in range(n):
        v = diff[i, j]
        txt_color = 'white' if abs(v) > 0.55 else 'black'
        ax.text(j, i, f'{v:.3f}', ha='center', va='center',
                fontsize=6.5, color=txt_color, fontweight='bold')
_add_color_strips(ax)
plt.tight_layout()
out = HERE / f'theil_category_heatmap_diff{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
