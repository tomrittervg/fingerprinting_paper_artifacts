#!/usr/bin/env python3
"""Per-metric predictability scatter using Theil's U.

For each metric, compute:
  - max_predicts:    max U(metric → other) — how well this metric predicts others
  - max_predicted_by: max U(other → metric) — how well others predict this metric

A metric with high "predicts" but low "predicted_by" is an independent predictor.
A metric with low "predicts" but high "predicted_by" is redundant (subsumed by others).

Outputs:
  theil_predictability_scatter{FILTER_SUFFIX}.png  — predicts vs predicted_by scatter
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from _theil_utils import load_per_metric, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE


def shorten(m, n=30):
    return m if len(m) <= n else m[:n - 1] + '\u2026'


per_metric = load_per_metric()

metrics = sorted(per_metric.keys())
pred    = np.array([per_metric[m]['max_u_predicts'] for m in metrics])
pred_by = np.array([per_metric[m]['max_u_predicted_by'] for m in metrics])
cats    = [get_category(m) for m in metrics]
colors  = [CATEGORY_COLORS.get(c, '#888888') for c in cats]

# ── Plot 1: Scatter — predicts vs predicted_by ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 10))
ax.scatter(pred, pred_by, c=colors, s=20, alpha=0.7, linewidths=0.3,
           edgecolors='white', zorder=3)
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.4, zorder=2)
ax.set_xlabel('Max U(metric \u2192 any other)  [predicts others]', fontsize=12)
ax.set_ylabel('Max U(any other \u2192 metric)  [predicted by others]', fontsize=12)
ax.set_title("Per-Metric Predictability (Theil's U)", fontsize=13)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.grid(lw=0.3, alpha=0.4)

# Annotate outliers (far from diagonal)
net = pred - pred_by
outlier_idx = np.argsort(-np.abs(net))[:15]
for idx in outlier_idx:
    ax.annotate(shorten(metrics[idx], 22),
                (pred[idx], pred_by[idx]),
                textcoords='offset points',
                xytext=(6, -6 if net[idx] > 0 else 6),
                fontsize=5.5, alpha=0.8,
                arrowprops=dict(arrowstyle='-', lw=0.3, color='gray'))

# Quadrant labels
ax.text(0.95, 0.05, 'Predicts others\nbut not predicted',
        ha='right', va='bottom', fontsize=8, alpha=0.4, style='italic',
        transform=ax.transAxes)
ax.text(0.05, 0.95, 'Predicted by others\nbut doesn\'t predict',
        ha='left', va='top', fontsize=8, alpha=0.4, style='italic',
        transform=ax.transAxes)

handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
ax.legend(handles=handles, fontsize=7, loc='lower right', ncol=2, framealpha=0.9)

plt.tight_layout()
out = HERE / f'theil_predictability_scatter{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
