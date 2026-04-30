#!/usr/bin/env python3
"""Category-level aggregate heatmap: mean and max AMI between metric categories.

14 × 14 grid.  Left panel = mean AMI, right panel = max AMI.
Cell counts (number of metric pairs contributing) shown as small text.
Outputs corr_category_heatmap.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_category_heatmap{FILTER_SUFFIX}.png'

n        = len(CATEGORY_ORDER)
cat_idx  = {c: i for i, c in enumerate(CATEGORY_ORDER)}
sums     = np.zeros((n, n))
maxes    = np.zeros((n, n))
counts   = np.zeros((n, n), dtype=int)

for r in load_rows():
    ami = r['ami']
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    if i == j:
        sums[i, j]  += ami
        maxes[i, j]  = max(maxes[i, j], ami)
        counts[i, j] += 1
    else:
        for a, b in ((i, j), (j, i)):
            sums[a, b]  += ami
            maxes[a, b]  = max(maxes[a, b], ami)
            counts[a, b] += 1

means = np.where(counts > 0, sums / counts, 0.0)

fig, axes = plt.subplots(1, 2, figsize=(19, 8))

for ax, data, title in [
    (axes[0], means, 'Mean AMI between categories'),
    (axes[1], maxes, 'Max AMI between categories'),
]:
    im = ax.imshow(data, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(n))
    ax.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(range(n))
    ax.set_yticklabels(CATEGORY_ORDER, fontsize=9)
    ax.set_title(title, fontsize=11)
    plt.colorbar(im, ax=ax, shrink=0.82)

    # Annotate each cell with value; add count as tiny subscript
    for i in range(n):
        for j in range(n):
            v   = data[i, j]
            cnt = counts[i, j]
            txt_color = 'white' if v > 0.55 else 'black'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                    fontsize=7, color=txt_color, fontweight='bold')
            if cnt > 0:
                ax.text(j, i + 0.38, f'({cnt:,})', ha='center', va='center',
                        fontsize=4.5, color=txt_color, alpha=0.75)

# Category color strip on left axis of each panel
for ax in axes:
    for i, cat in enumerate(CATEGORY_ORDER):
        ax.add_patch(plt.Rectangle(
            (-1.55, i - 0.5), 0.45, 1.0,
            color=CATEGORY_COLORS[cat], clip_on=False,
            transform=ax.transData,
        ))

plt.suptitle('Category-Level AMI Heatmap  (bin threshold = 30)', fontsize=13)
plt.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
