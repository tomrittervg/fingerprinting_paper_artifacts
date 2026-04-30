#!/usr/bin/env python3
"""Per-category AMI profiles: small multiples.

One panel per category. Each panel shows a horizontal bar chart of that
category's mean AMI toward every other category (including itself),
sorted descending. Makes it easy to see e.g. "Audio correlates strongly
with Canvas and WebGL but weakly with Screen."

Outputs corr_category_profiles{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_category_profiles{FILTER_SUFFIX}.png'

rows = load_rows()

# Build mean AMI from cat_a → cat_b (symmetric: include pair in both directions)
sums   = defaultdict(float)
counts = defaultdict(int)
for r in rows:
    c1, c2 = get_category(r['metric1']), get_category(r['metric2'])
    ami = r['ami']
    sums[(c1, c2)]   += ami
    counts[(c1, c2)] += 1
    if c1 != c2:
        sums[(c2, c1)]   += ami
        counts[(c2, c1)] += 1

mean_to = {}   # (from_cat, to_cat) → mean AMI
for k in sums:
    mean_to[k] = sums[k] / counts[k]

active_cats = [c for c in CATEGORY_ORDER
               if any(k[0] == c for k in mean_to)]

# ── Layout: 3 columns ─────────────────────────────────────────────────────────
NCOLS = 3
NROWS = (len(active_cats) + NCOLS - 1) // NCOLS
fig, axes = plt.subplots(NROWS, NCOLS,
                          figsize=(NCOLS * 5.5, NROWS * 3.5))
axes_flat = axes.flatten()

for idx, cat in enumerate(active_cats):
    ax = axes_flat[idx]
    color = CATEGORY_COLORS[cat]

    # Mean AMI from this cat to every other cat, sorted descending
    targets = [(to, mean_to.get((cat, to), 0)) for to in active_cats]
    targets.sort(key=lambda x: x[1], reverse=True)

    labels = [t[0] for t in targets]
    values = [t[1] for t in targets]
    bar_colors = [CATEGORY_COLORS[t[0]] for t in targets]

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=bar_colors, alpha=0.8, height=0.7)

    # Highlight self
    self_idx = labels.index(cat)
    bars[self_idx].set_edgecolor('black')
    bars[self_idx].set_linewidth(1.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('Mean AMI', fontsize=8)
    ax.set_xlim(0, max(values) * 1.15 if values else 1)
    ax.set_title(cat, fontsize=10, fontweight='bold', color=color, pad=4)
    ax.grid(axis='x', alpha=0.3, linewidth=0.5)
    ax.tick_params(axis='x', labelsize=7)

    # Value labels
    for bar, val in zip(bars, values):
        if val > 0.005:
            ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                    f'{val:.3f}', va='center', fontsize=6.5, color='#333333')

# Hide unused panels
for idx in range(len(active_cats), len(axes_flat)):
    axes_flat[idx].axis('off')

fig.suptitle(
    'Per-Category AMI Profile: mean AMI toward each other category\n'
    '(black outline = self-correlation  |  sorted descending)',
    fontsize=12, y=1.01,
)
fig.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
