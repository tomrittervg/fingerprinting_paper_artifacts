#!/usr/bin/env python3
"""Metric isolation chart — which metrics are least connected to others.

For each metric, computes max U across all pairs in either direction:
  isolation_score = max( max U(m→other), max U(other→m) )

Low score = isolated (independent of everything else).
High score = connected (at least one strong predictive relationship).

Sorted ascending: most isolated at top.

Output:
  theil_isolation{FILTER_SUFFIX}.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from _theil_utils import load_per_metric, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE


def shorten(m, n=35):
    return m if len(m) <= n else m[:n - 1] + '\u2026'


per_metric = load_per_metric()

metrics = sorted(per_metric.keys())
max_either = np.array([max(per_metric[m]['max_u_predicts'],
                           per_metric[m]['max_u_predicted_by'])
                       for m in metrics])
cats   = [get_category(m) for m in metrics]
colors = [CATEGORY_COLORS.get(c, '#888888') for c in cats]

# Exclude constant metrics (max U = 0 with everything, i.e. zero entropy)
constant_mask = max_either == 0
# Filter to isolated metrics only (max U < threshold, excluding constants)
ISOLATION_THRESHOLD = float(os.environ.get('THEIL_ISOLATION_THRESHOLD', '0.35'))
isolated_mask = (max_either < ISOLATION_THRESHOLD) & ~constant_mask
isolated_idx = np.where(isolated_mask)[0]
sorted_idx = isolated_idx[np.argsort(max_either[isolated_idx])]

n_shown = len(sorted_idx)
fig, ax = plt.subplots(figsize=(12, max(6, n_shown * 0.3)))
y = np.arange(n_shown)

bar_colors = [colors[i] for i in sorted_idx]
bar_vals = [max_either[i] for i in sorted_idx]
bar_labels = [shorten(metrics[i]) for i in sorted_idx]

ax.barh(y, bar_vals, color=bar_colors, height=0.72, edgecolor='none', alpha=0.85)
ax.invert_yaxis()

# Add partner annotation: which metric produced the max U
for yi, idx in enumerate(sorted_idx):
    m = metrics[idx]
    pm = per_metric[m]
    if pm['max_u_predicts'] >= pm['max_u_predicted_by']:
        partner = pm.get('max_u_predicts_partner', '')
        direction = '\u2192'
    else:
        partner = pm.get('max_u_predicted_by_partner', '')
        direction = '\u2190'
    if partner:
        ax.text(bar_vals[yi] + 0.008, yi, f'{direction} {shorten(partner, 25)}',
                ha='left', va='center', fontsize=4.5, alpha=0.55, style='italic')

ax.set_yticks(y)
ax.set_yticklabels(bar_labels, fontsize=6)
ax.set_xlabel("Max Theil's U (either direction, any pair)", fontsize=10)
n_constant = int(constant_mask.sum())
ax.set_title(f"Isolated Metrics \u2014 Max Theil's U < {ISOLATION_THRESHOLD} ({n_shown} of {len(metrics)} metrics, {n_constant} constant excluded)\n"
             "Most isolated (least connected) at top",
             fontsize=12)
ax.grid(axis='x', lw=0.3, alpha=0.5)
ax.axvline(0.5, color='gray', lw=0.8, ls=':', alpha=0.5)
ax.set_xlim(0, min(1.3, max(bar_vals) + 0.15))

handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
ax.legend(handles=handles, fontsize=6, loc='lower right', ncol=2, framealpha=0.9)

plt.tight_layout()
out = HERE / f'theil_isolation_t{ISOLATION_THRESHOLD}{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
