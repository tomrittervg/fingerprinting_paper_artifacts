#!/usr/bin/env python3
"""AMI distribution by category: within vs. cross-category.

For each category, two violin plots side by side:
  - within: AMI for pairs where both metrics are in this category
  - cross:  AMI for pairs where one metric is in this category (the other isn't)

Reveals whether metrics within the same category are actually more correlated
than metrics across categories, and quantifies by how much.

Outputs corr_ami_distribution{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_ami_distribution{FILTER_SUFFIX}.png'

rows = load_rows()

within = defaultdict(list)   # cat → [ami, ...]
cross  = defaultdict(list)   # cat → [ami, ...]

for r in rows:
    c1, c2 = get_category(r['metric1']), get_category(r['metric2'])
    ami = r['ami']
    if c1 == c2:
        within[c1].append(ami)
    else:
        cross[c1].append(ami)
        cross[c2].append(ami)

# Only categories with enough data to plot
active = [c for c in CATEGORY_ORDER if within[c] or cross[c]]
n = len(active)

fig, ax = plt.subplots(figsize=(max(12, n * 1.4), 7))

positions_w = np.arange(n) * 3.0
positions_c = positions_w + 1.0

def make_violin(ax, data_list, positions, colors, side):
    parts = ax.violinplot(
        [d if d else [0] for d in data_list],
        positions=positions,
        widths=0.85,
        showmedians=True,
        showextrema=False,
    )
    for pc, color in zip(parts['bodies'], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.65)
        pc.set_edgecolor('white')
        pc.set_linewidth(0.5)
    parts['cmedians'].set_color('white')
    parts['cmedians'].set_linewidth(1.5)

colors = [CATEGORY_COLORS[c] for c in active]

make_violin(ax, [within[c] for c in active], positions_w, colors, 'within')
make_violin(ax, [cross[c]  for c in active], positions_c,
            ['#aaaaaa'] * n, 'cross')

# Stats annotation: median within vs cross
for i, cat in enumerate(active):
    w = within[cat]
    c = cross[cat]
    if w and c:
        delta = np.median(w) - np.median(c)
        ax.text(positions_w[i] + 0.5, ax.get_ylim()[1] * 0.97,
                f'{delta:+.3f}', ha='center', va='top',
                fontsize=7, color='#333333')

ax.set_xticks(positions_w + 0.5)
ax.set_xticklabels(active, rotation=35, ha='right', fontsize=9)
ax.set_ylabel('AMI', fontsize=11)
ax.set_title(
    'AMI distribution by category: within-category (colored) vs. cross-category (grey)\n'
    'Numbers above = median(within) − median(cross)',
    fontsize=11,
)
ax.grid(axis='y', alpha=0.3, linewidth=0.5)
ax.set_xlim(-0.8, positions_c[-1] + 0.8)
ax.set_ylim(bottom=0)

handles = [
    mpatches.Patch(color='steelblue', alpha=0.7, label='Within-category'),
    mpatches.Patch(color='#aaaaaa',   alpha=0.7, label='Cross-category'),
]
ax.legend(handles=handles, fontsize=9, loc='upper right')

fig.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
