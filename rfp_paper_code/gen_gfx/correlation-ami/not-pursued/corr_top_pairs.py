#!/usr/bin/env python3
"""Top metric pairs by AMI — horizontal bar charts.

Outputs four PNGs:
  corr_top_pairs_top25{FILTER_SUFFIX}.png       — top 25 pairs
  corr_top_pairs_top50{FILTER_SUFFIX}.png       — top 50 pairs
  corr_top_pairs_top100{FILTER_SUFFIX}.png      — top 100 pairs
  corr_top_pairs_bycategory{FILTER_SUFFIX}.png  — top 5 same-category pairs per category

Bars are colored by category when both metrics share a category, gray otherwise.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_COLORS, CATEGORY_ORDER, FILTER_SUFFIX, HERE


def shorten(m, n=32):
    return m if len(m) <= n else m[:n - 1] + '…'


def _legend_handles():
    handles = [mpatches.Patch(color=c, label=cat) for cat, c in CATEGORY_COLORS.items()]
    handles.append(mpatches.Patch(color='#cccccc', label='Cross-category'))
    return handles


rows = sorted(load_rows(), key=lambda r: -r['ami'])

# ── Top-N bar charts ───────────────────────────────────────────────────────────
for top_n, fig_h, label_fs in [(25, 8, 8.5), (50, 14, 6.5), (100, 22, 6.5)]:
    top    = rows[:top_n]
    amis   = [r['ami'] for r in top]
    cats1  = [get_category(r['metric1']) for r in top]
    cats2  = [get_category(r['metric2']) for r in top]
    colors = [CATEGORY_COLORS[c1] if c1 == c2 else '#cccccc'
              for c1, c2 in zip(cats1, cats2)]
    labels = [f"{shorten(r['metric1'])}  ×  {shorten(r['metric2'])}" for r in top]

    fig, ax = plt.subplots(figsize=(12, fig_h))
    y = np.arange(len(top))
    ax.barh(y, amis, color=colors, height=0.72, edgecolor='none')
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=label_fs)
    ax.invert_yaxis()
    ax.set_xlabel('AMI (Adjusted Mutual Information)')
    ax.set_title(f'Top {top_n} Metric Pairs by AMI', fontsize=12)
    ax.set_xlim(0, 1.08)
    ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
    ax.grid(axis='x', lw=0.3, alpha=0.5)
    ax.legend(handles=_legend_handles(), fontsize=7, loc='lower right', ncol=2,
              framealpha=0.9, title='Category (same-cat pairs)')
    plt.tight_layout()
    out = HERE / f'corr_top_pairs_top{top_n}{FILTER_SUFFIX}.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    print(f"Wrote {out}")
    plt.close(fig)

# ── By-category chart ─────────────────────────────────────────────────────────
TOP_PER_CAT = 5

by_cat = defaultdict(list)
for r in rows:
    c1 = get_category(r['metric1'])
    c2 = get_category(r['metric2'])
    if c1 == c2:
        by_cat[c1].append(r)

sections = [(cat, by_cat[cat][:TOP_PER_CAT])
            for cat in CATEGORY_ORDER if by_cat.get(cat)]

y_positions      = []
header_y         = []
header_labels_text = []
bar_amis         = []
bar_colors       = []
bar_labels       = []
y_pos = 0

for cat, cat_rows in sections:
    header_y.append(y_pos)
    header_labels_text.append(cat)
    y_pos += 1
    for r in cat_rows:
        bar_labels.append(f"{shorten(r['metric1'])}  ×  {shorten(r['metric2'])}")
        bar_amis.append(r['ami'])
        bar_colors.append(CATEGORY_COLORS[cat])
        y_positions.append(y_pos)
        y_pos += 1
    y_pos += 0.5

fig, ax = plt.subplots(figsize=(12, 14))
y_arr = np.array(y_positions, dtype=float)
ax.barh(y_arr, bar_amis, color=bar_colors, height=0.72, edgecolor='none')
ax.set_yticks(y_arr)
ax.set_yticklabels(bar_labels, fontsize=6.5)

for hy, hlabel in zip(header_y, header_labels_text):
    cat_color = CATEGORY_COLORS[hlabel]
    ax.axhline(hy + 0.5, color=cat_color, lw=0.8, alpha=0.4)
    ax.text(-0.01, hy + 0.5, hlabel,
            transform=ax.get_yaxis_transform(),
            ha='right', va='center', fontsize=8, fontweight='bold',
            color=cat_color)

ax.invert_yaxis()
ax.set_xlabel('AMI (Adjusted Mutual Information)')
ax.set_title(f'Top {TOP_PER_CAT} Same-Category Metric Pairs by Category', fontsize=12)
ax.set_xlim(0, 1.08)
ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.grid(axis='x', lw=0.3, alpha=0.5)
handles = [mpatches.Patch(color=CATEGORY_COLORS[cat], label=cat) for cat, _ in sections]
ax.legend(handles=handles, fontsize=7, loc='lower right', ncol=2,
          framealpha=0.9, title='Category')
plt.tight_layout()
out = HERE / f'corr_top_pairs_bycategory{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
