#!/usr/bin/env python3
"""Top-5 same-category metric pairs per category — grouped horizontal bar chart.

For each category in CATEGORY_ORDER, collects pairs where both metrics belong
to that category and plots the top 5 by AMI with a section header.
Categories with no same-category pairs are skipped.
Outputs corr_top_pairs_bycategory.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_COLORS, CATEGORY_ORDER, FILTER_SUFFIX, HERE

TOP_PER_CAT = 5
OUT_PATH    = HERE / f'corr_top_pairs_bycategory{FILTER_SUFFIX}.png'


def shorten(m, n=32):
    return m if len(m) <= n else m[:n - 1] + '…'


rows = sorted(load_rows(), key=lambda r: -r['ami'])

# Group same-category pairs by category
by_cat = defaultdict(list)
for r in rows:
    c1 = get_category(r['metric1'])
    c2 = get_category(r['metric2'])
    if c1 == c2:
        by_cat[c1].append(r)

# Build ordered list of (category, top_rows) skipping empty categories
sections = []
for cat in CATEGORY_ORDER:
    cat_rows = by_cat.get(cat, [])
    if cat_rows:
        sections.append((cat, cat_rows[:TOP_PER_CAT]))

# Flatten into plot data with section headers
bar_amis   = []
bar_colors = []
bar_labels = []
bar_is_header = []
header_positions = []

y_pos = 0
y_positions = []
header_y = []
header_labels_text = []

for cat, cat_rows in sections:
    # Record header position
    header_y.append(y_pos)
    header_labels_text.append(cat)
    y_pos += 1  # gap for header

    for r in cat_rows:
        label = f"{shorten(r['metric1'])}  ×  {shorten(r['metric2'])}"
        bar_amis.append(r['ami'])
        bar_colors.append(CATEGORY_COLORS[cat])
        bar_labels.append(label)
        y_positions.append(y_pos)
        y_pos += 1

    y_pos += 0.5  # gap between sections

fig, ax = plt.subplots(figsize=(12, 14))

# Draw bars
y_arr = np.array(y_positions, dtype=float)
ax.barh(y_arr, bar_amis, color=bar_colors, height=0.72, edgecolor='none')
ax.set_yticks(y_arr)
ax.set_yticklabels(bar_labels, fontsize=6.5)

# Draw section header text as annotations
for hy, hlabel in zip(header_y, header_labels_text):
    cat_color = CATEGORY_COLORS[hlabel]
    ax.axhline(hy + 0.5, color=cat_color, lw=0.8, alpha=0.4, xmin=0, xmax=1)
    ax.text(-0.01, hy + 0.5, hlabel,
            transform=ax.get_yaxis_transform(),
            ha='right', va='center',
            fontsize=8, fontweight='bold',
            color=cat_color)

ax.invert_yaxis()
ax.set_xlabel('AMI (Adjusted Mutual Information)')
ax.set_title(f'Top {TOP_PER_CAT} Same-Category Metric Pairs by Category  (bin threshold = 30)', fontsize=12)
ax.set_xlim(0, 1.08)
ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.grid(axis='x', lw=0.3, alpha=0.5)

handles = [mpatches.Patch(color=CATEGORY_COLORS[cat], label=cat)
           for cat, _ in sections]
ax.legend(handles=handles, fontsize=7, loc='lower right', ncol=2,
          framealpha=0.9, title='Category')

plt.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
