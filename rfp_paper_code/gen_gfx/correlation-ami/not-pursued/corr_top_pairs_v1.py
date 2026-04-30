#!/usr/bin/env python3
"""Top-25 metric pairs by AMI — horizontal bar chart.

Bars are colored by category when both metrics share a category,
gray otherwise.  Outputs corr_top_pairs_top25.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

from _corr_utils import load_rows, get_category, CATEGORY_COLORS, FILTER_SUFFIX, HERE

TOP_N    = 25
OUT_PATH = HERE / f'corr_top_pairs_top25{FILTER_SUFFIX}.png'


def shorten(m, n=32):
    return m if len(m) <= n else m[:n - 1] + '…'


rows = sorted(load_rows(), key=lambda r: -r['ami'])
top  = rows[:TOP_N]

amis   = [r['ami'] for r in top]
cats1  = [get_category(r['metric1']) for r in top]
cats2  = [get_category(r['metric2']) for r in top]
colors = [CATEGORY_COLORS[c1] if c1 == c2 else '#cccccc'
          for c1, c2 in zip(cats1, cats2)]
labels = [f"{shorten(r['metric1'])}  ×  {shorten(r['metric2'])}"
          for r in top]

fig, ax = plt.subplots(figsize=(12, 8))
y = np.arange(len(top))
ax.barh(y, amis, color=colors, height=0.72, edgecolor='none')
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel('AMI (Adjusted Mutual Information)')
ax.set_title(f'Top 25 Metric Pairs by AMI  (bin threshold = 30)', fontsize=12)
ax.set_xlim(0, 1.08)
ax.axvline(1.0, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.grid(axis='x', lw=0.3, alpha=0.5)

handles = [mpatches.Patch(color=c, label=cat)
           for cat, c in CATEGORY_COLORS.items()]
handles.append(mpatches.Patch(color='#cccccc', label='Cross-category'))
ax.legend(handles=handles, fontsize=7, loc='lower right', ncol=2,
          framealpha=0.9, title='Category (same-cat pairs)')

plt.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
