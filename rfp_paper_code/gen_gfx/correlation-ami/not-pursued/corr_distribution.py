#!/usr/bin/env python3
"""Distribution of AMI values: all pairs, within-category vs cross-category.

Left panel: histogram (density).  Right panel: CDF.
Summary statistics printed below the figure.
Outputs corr_distribution.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from _corr_utils import load_rows, get_category, FILTER_SUFFIX, HERE

OUT_PATH = HERE / f'corr_distribution{FILTER_SUFFIX}.png'

within, cross = [], []
for r in load_rows():
    if get_category(r['metric1']) == get_category(r['metric2']):
        within.append(r['ami'])
    else:
        cross.append(r['ami'])

within = np.array(within)
cross  = np.array(cross)
all_ami = np.concatenate([within, cross])

bins = np.linspace(0, 1, 51)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# ── Histogram ─────────────────────────────────────────────────────────────────
ax = axes[0]
ax.hist(cross,  bins=bins, alpha=0.55, color='steelblue',
        label=f'Cross-category  (n={len(cross):,})', density=True)
ax.hist(within, bins=bins, alpha=0.55, color='tomato',
        label=f'Within-category  (n={len(within):,})', density=True)
for vals, color in [(cross, 'steelblue'), (within, 'tomato')]:
    ax.axvline(np.median(vals), color=color, ls='--', lw=1.5, alpha=0.9,
               label=f'median={np.median(vals):.3f}')
ax.set_xlabel('AMI')
ax.set_ylabel('Density')
ax.set_title('AMI Distribution: Within vs Cross Category')
ax.legend(fontsize=8.5)
ax.set_xlim(-0.02, 1.02)
ax.grid(axis='y', lw=0.3, alpha=0.4)

# ── CDF ───────────────────────────────────────────────────────────────────────
ax2 = axes[1]
for vals, color, label in [
    (cross,  'steelblue', 'Cross-category'),
    (within, 'tomato',    'Within-category'),
    (all_ami,'#444444',   'All pairs'),
]:
    sv  = np.sort(vals)
    cdf = np.arange(1, len(vals) + 1) / len(vals)
    ax2.plot(sv, cdf, color=color, label=label, lw=1.8)
ax2.set_xlabel('AMI')
ax2.set_ylabel('Cumulative proportion')
ax2.set_title('CDF of AMI Values')
ax2.legend(fontsize=9)
ax2.grid(lw=0.3, alpha=0.4)
ax2.set_xlim(-0.02, 1.02)
ax2.set_ylim(0, 1)

# ── Summary stats ─────────────────────────────────────────────────────────────
def stats_line(label, arr):
    return (f"{label:14s}  n={len(arr):>7,}  "
            f"median={np.median(arr):.3f}  "
            f"mean={arr.mean():.3f}  "
            f"p90={np.percentile(arr,90):.3f}  "
            f"p99={np.percentile(arr,99):.3f}")

summary = '\n'.join([
    stats_line('All pairs', all_ami),
    stats_line('Within-cat', within),
    stats_line('Cross-cat',  cross),
])
fig.text(0.5, -0.03, summary, ha='center', fontsize=8, family='monospace',
         va='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.suptitle('AMI Distribution  (bin threshold = 30)', fontsize=12, y=1.01)
plt.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
