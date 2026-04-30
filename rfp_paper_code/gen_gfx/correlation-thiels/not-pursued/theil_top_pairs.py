#!/usr/bin/env python3
"""Top metric pairs by Theil's U — horizontal bar charts.

Unlike AMI bar charts, these show both U directions for each pair as
side-by-side bars, making asymmetry immediately visible.

Outputs:
  theil_top_pairs_max{FILTER_SUFFIX}.png         — top 30 by max(U_1to2, U_2to1)
  theil_top_pairs_asymmetric{FILTER_SUFFIX}.png   — top 30 by |U_1to2 - U_2to1|
  theil_top_pairs_bycategory{FILTER_SUFFIX}.png   — top 5 same-cat by max U
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

from _theil_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE


def shorten(m, n=30):
    return m if len(m) <= n else m[:n - 1] + '\u2026'


rows = load_rows()

# ── Plot 1: Top 30 by max U ──────────────────────────────────────────────────
# For each pair, max(u_1to2, u_2to1) determines rank.
by_max = sorted(rows, key=lambda r: -max(r['u_1to2'], r['u_2to1']))[:30]

fig, ax = plt.subplots(figsize=(13, 10))
y = np.arange(len(by_max))
bar_h = 0.35

for i, r in enumerate(by_max):
    c1, c2 = get_category(r['metric1']), get_category(r['metric2'])
    color = CATEGORY_COLORS[c1] if c1 == c2 else '#cccccc'
    ax.barh(i - bar_h / 2, r['u_1to2'], height=bar_h, color=color, alpha=0.85,
            edgecolor='none')
    ax.barh(i + bar_h / 2, r['u_2to1'], height=bar_h, color=color, alpha=0.45,
            edgecolor='none', hatch='///')

labels = [f"{shorten(r['metric1'])}  \u00d7  {shorten(r['metric2'])}" for r in by_max]
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("Theil's U")
ax.set_title("Top 30 Metric Pairs by Max Theil's U", fontsize=12)
ax.set_xlim(0, 1.08)
ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.grid(axis='x', lw=0.3, alpha=0.5)

# Legend
handles = [
    mpatches.Patch(color='#888888', alpha=0.85, label='U(m1\u2192m2)'),
    mpatches.Patch(color='#888888', alpha=0.45, label='U(m2\u2192m1)', hatch='///'),
]
cat_handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
cat_handles.append(mpatches.Patch(color='#cccccc', label='Cross-category'))
ax.legend(handles=handles + cat_handles, fontsize=6.5, loc='lower right', ncol=2,
          framealpha=0.9, title='Direction / Category')

plt.tight_layout()
out = HERE / f'theil_top_pairs_max{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 2: Top 30 by asymmetry ──────────────────────────────────────────────
# Rank by |U_1to2 - U_2to1|, showing which direction dominates.
by_asym = sorted(rows, key=lambda r: -abs(r['u_1to2'] - r['u_2to1']))[:30]

fig, ax = plt.subplots(figsize=(13, 10))
y = np.arange(len(by_asym))

for i, r in enumerate(by_asym):
    c1, c2 = get_category(r['metric1']), get_category(r['metric2'])
    color = CATEGORY_COLORS[c1] if c1 == c2 else '#cccccc'
    # Draw the dominant direction as solid, non-dominant as hashed
    if r['u_1to2'] >= r['u_2to1']:
        ax.barh(i - bar_h / 2, r['u_1to2'], height=bar_h, color=color, alpha=0.85,
                edgecolor='none')
        ax.barh(i + bar_h / 2, r['u_2to1'], height=bar_h, color=color, alpha=0.45,
                edgecolor='none', hatch='///')
    else:
        ax.barh(i - bar_h / 2, r['u_1to2'], height=bar_h, color=color, alpha=0.45,
                edgecolor='none', hatch='///')
        ax.barh(i + bar_h / 2, r['u_2to1'], height=bar_h, color=color, alpha=0.85,
                edgecolor='none')

labels = []
for r in by_asym:
    diff = abs(r['u_1to2'] - r['u_2to1'])
    labels.append(f"{shorten(r['metric1'])}  \u00d7  {shorten(r['metric2'])}  (\u0394={diff:.2f})")
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=6.5)
ax.invert_yaxis()
ax.set_xlabel("Theil's U")
ax.set_title("Top 30 Most Asymmetric Pairs (Theil's U)", fontsize=12)
ax.set_xlim(0, 1.08)
ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.grid(axis='x', lw=0.3, alpha=0.5)

handles = [
    mpatches.Patch(color='#888888', alpha=0.85, label='Dominant direction (solid)'),
    mpatches.Patch(color='#888888', alpha=0.45, label='Other direction (hatched)', hatch='///'),
]
ax.legend(handles=handles, fontsize=7, loc='lower right', framealpha=0.9)

plt.tight_layout()
out = HERE / f'theil_top_pairs_asymmetric{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 3: Top 5 same-category pairs per category ───────────────────────────
TOP_PER_CAT = 5

by_cat = defaultdict(list)
for r in rows:
    c1, c2 = get_category(r['metric1']), get_category(r['metric2'])
    if c1 == c2:
        by_cat[c1].append(r)

# Sort each category by max U
for cat in by_cat:
    by_cat[cat].sort(key=lambda r: -max(r['u_1to2'], r['u_2to1']))

sections = [(cat, by_cat[cat][:TOP_PER_CAT])
            for cat in CATEGORY_ORDER if by_cat.get(cat)]

y_positions = []
header_y = []
header_labels_text = []
bar_data = []  # (u_1to2, u_2to1, color, label)
y_pos = 0

for cat, cat_rows in sections:
    header_y.append(y_pos)
    header_labels_text.append(cat)
    y_pos += 1
    for r in cat_rows:
        bar_data.append((r['u_1to2'], r['u_2to1'], CATEGORY_COLORS[cat],
                         f"{shorten(r['metric1'])}  \u00d7  {shorten(r['metric2'])}"))
        y_positions.append(y_pos)
        y_pos += 1
    y_pos += 0.5

fig, ax = plt.subplots(figsize=(13, 14))
bar_h = 0.35
for i, (u12, u21, color, label) in enumerate(bar_data):
    yp = y_positions[i]
    ax.barh(yp - bar_h / 2, u12, height=bar_h, color=color, alpha=0.85, edgecolor='none')
    ax.barh(yp + bar_h / 2, u21, height=bar_h, color=color, alpha=0.45, edgecolor='none',
            hatch='///')

ax.set_yticks(y_positions)
ax.set_yticklabels([d[3] for d in bar_data], fontsize=6)

for hy, hlabel in zip(header_y, header_labels_text):
    cat_color = CATEGORY_COLORS[hlabel]
    ax.axhline(hy + 0.5, color=cat_color, lw=0.8, alpha=0.4)
    ax.text(-0.01, hy + 0.5, hlabel,
            transform=ax.get_yaxis_transform(),
            ha='right', va='center', fontsize=8, fontweight='bold',
            color=cat_color)

ax.invert_yaxis()
ax.set_xlabel("Theil's U")
ax.set_title(f"Top {TOP_PER_CAT} Same-Category Pairs by Theil's U", fontsize=12)
ax.set_xlim(0, 1.08)
ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.grid(axis='x', lw=0.3, alpha=0.5)

handles = [
    mpatches.Patch(color='#888888', alpha=0.85, label='U(m1\u2192m2)'),
    mpatches.Patch(color='#888888', alpha=0.45, label='U(m2\u2192m1)', hatch='///'),
]
ax.legend(handles=handles, fontsize=7, loc='lower right', framealpha=0.9)
plt.tight_layout()
out = HERE / f'theil_top_pairs_bycategory{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
