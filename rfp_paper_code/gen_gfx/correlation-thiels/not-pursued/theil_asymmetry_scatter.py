#!/usr/bin/env python3
"""Scatter plot of U(m1→m2) vs U(m2→m1) for all metric pairs.

Points on the diagonal are symmetric pairs; off-diagonal points reveal
metrics where one predicts the other but not vice versa.

Outputs:
  theil_asymmetry_scatter{FILTER_SUFFIX}.png     — all pairs
  theil_asymmetry_scatter_top{FILTER_SUFFIX}.png  — annotated top asymmetric pairs
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from _theil_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE


def shorten(m, n=25):
    return m if len(m) <= n else m[:n - 1] + '\u2026'


rows = load_rows()

u12  = np.array([r['u_1to2'] for r in rows])
u21  = np.array([r['u_2to1'] for r in rows])
asym = np.abs(u12 - u21)

cats1 = [get_category(r['metric1']) for r in rows]
cats2 = [get_category(r['metric2']) for r in rows]
colors = [CATEGORY_COLORS[c1] if c1 == c2 else '#aaaaaa'
          for c1, c2 in zip(cats1, cats2)]

# ── Plot 1: Full scatter ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 10))
ax.scatter(u12, u21, c=colors, s=8, alpha=0.5, linewidths=0, zorder=3)
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.4, zorder=2)
ax.set_xlabel('Theil\'s U(metric1 → metric2)', fontsize=12)
ax.set_ylabel('Theil\'s U(metric2 → metric1)', fontsize=12)
ax.set_title('Theil\'s U Asymmetry: All Metric Pairs', fontsize=13)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.grid(lw=0.3, alpha=0.4)

handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
handles.append(mpatches.Patch(color='#aaaaaa', label='Cross-category'))
ax.legend(handles=handles, fontsize=7, loc='upper left', ncol=2, framealpha=0.9)

plt.tight_layout()
out = HERE / f'theil_asymmetry_scatter{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 2: Top asymmetric pairs annotated ────────────────────────────────────
from adjustText import adjust_text

# Sort by asymmetry, take top 20
top_idx = np.argsort(-asym)[:20]

fig, ax = plt.subplots(figsize=(12, 12))
# Background: all pairs faintly
ax.scatter(u12, u21, c='#dddddd', s=4, alpha=0.3, linewidths=0, zorder=2)
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.4, zorder=1)

# Highlight top asymmetric
top_x, top_y = [], []
for idx in top_idx:
    r = rows[idx]
    c1, c2 = cats1[idx], cats2[idx]
    color = CATEGORY_COLORS[c1] if c1 == c2 else '#666666'
    ax.scatter(u12[idx], u21[idx], c=color, s=50, alpha=0.9,
               linewidths=0.5, edgecolors='black', zorder=4)
    top_x.append(u12[idx])
    top_y.append(u21[idx])

texts = []
for idx in top_idx:
    r = rows[idx]
    label = f"{shorten(r['metric1'])} \u00d7 {shorten(r['metric2'])}"
    texts.append(ax.text(u12[idx], u21[idx], label, fontsize=5.5, alpha=0.85,
                         zorder=6))

ax.set_xlabel('Theil\'s U(metric1 \u2192 metric2)', fontsize=12)
ax.set_ylabel('Theil\'s U(metric2 \u2192 metric1)', fontsize=12)
ax.set_title('Top 20 Most Asymmetric Metric Pairs (Theil\'s U)', fontsize=13)
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)
ax.set_aspect('equal')
ax.grid(lw=0.3, alpha=0.4)

adjust_text(texts, x=top_x, y=top_y, ax=ax,
            arrowprops=dict(arrowstyle='->', color='gray', lw=0.6, shrinkA=5, shrinkB=5),
            force_points=(3.0, 3.0), force_text=(1.5, 1.5),
            expand_points=(3.0, 3.0), expand_text=(2.0, 2.0),
            min_arrow_len=15)

plt.tight_layout()
out = HERE / f'theil_asymmetry_scatter_top{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
