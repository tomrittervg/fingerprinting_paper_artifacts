#!/usr/bin/env python3
"""Full pairwise Theil's U heatmap with per-metric axis labels.

Since Theil's U is asymmetric, cell (row, col) = U(row → col), i.e.
"how well does the row metric predict the column metric". The matrix
is NOT symmetric — upper and lower triangles differ.

Ordered by category then alphabetically within category.

Optional threshold (THEIL_HEATMAP_THRESHOLD env var):
  - Unset or 0: include all metrics.
  - > 0: only metrics whose max U (either direction) >= threshold.

Output:
  theil_all_heatmap{_tN}{FILTER_SUFFIX}.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

from _theil_utils import (load_rows, get_category, CATEGORY_ORDER,
                           CATEGORY_COLORS, FILTER_SUFFIX, HERE)

THRESHOLD = float(os.environ.get('THEIL_HEATMAP_THRESHOLD', '0'))
_suffix = f'_t{THRESHOLD}' if THRESHOLD > 0 else ''
OUT_PATH = HERE / f'theil_all_heatmap{_suffix}{FILTER_SUFFIX}.png'

# ── Load rows ────────────────────────────────────────────────────────────────
print("Loading pairs...")
rows = load_rows()

# ── Metric selection ─────────────────────────────────────────────────────────
if THRESHOLD > 0:
    max_u = defaultdict(float)
    for r in rows:
        max_u[r['metric1']] = max(max_u[r['metric1']], r['u_1to2'], r['u_2to1'])
        max_u[r['metric2']] = max(max_u[r['metric2']], r['u_1to2'], r['u_2to1'])
    kept = {m for m, v in max_u.items() if v >= THRESHOLD}
    metrics = sorted(kept)
else:
    metrics = sorted({r['metric1'] for r in rows} | {r['metric2'] for r in rows})

n     = len(metrics)
m_idx = {m: i for i, m in enumerate(metrics)}
print(f"  {n} metrics" + (f" with max U >= {THRESHOLD}" if THRESHOLD > 0 else "") +
      f", {len(rows):,} pairs")

# ── Build asymmetric U matrix ────────────────────────────────────────────────
# mat[i, j] = U(metric_i -> metric_j) = how well i predicts j
print("Building matrix...")
mat = np.zeros((n, n), dtype=np.float32)
np.fill_diagonal(mat, 1.0)
for r in rows:
    m1, m2 = r['metric1'], r['metric2']
    if m1 in m_idx and m2 in m_idx:
        i, j = m_idx[m1], m_idx[m2]
        mat[i, j] = r['u_1to2']  # m1 predicts m2
        mat[j, i] = r['u_2to1']  # m2 predicts m1

# ── Order by category then alphabetical ──────────────────────────────────────
print("Ordering...")
cat_rank = {c: i for i, c in enumerate(CATEGORY_ORDER)}
order = sorted(range(n), key=lambda i: (cat_rank.get(get_category(metrics[i]), 999), metrics[i]))

mat_ordered    = mat[np.ix_(order, order)]
cats_ordered   = [get_category(metrics[i]) for i in order]
labels_ordered = [metrics[i] for i in order]

# ── Category color arrays for margin strips ──────────────────────────────────
cat_colors = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                        for c in (CATEGORY_COLORS[c] for c in cats_ordered)],
                       dtype=np.uint8)

# ── Plot ─────────────────────────────────────────────────────────────────────
print("Plotting...")
STRIP_W  = max(8, n // 50)
fig_size = max(10, round(n * 0.22))
dpi      = 150
fig      = plt.figure(figsize=(fig_size, fig_size), dpi=dpi)

ax_main  = fig.add_axes([0.12, 0.15, 0.69, 0.70])
ax_top   = fig.add_axes([0.12, 0.873, 0.69, 0.020])
ax_right = fig.add_axes([0.815, 0.15, 0.020, 0.70])
ax_cbar  = fig.add_axes([0.845, 0.15, 0.015, 0.70])

h_strip = np.tile(cat_colors[np.newaxis, :, :], (STRIP_W, 1, 1))
v_strip = np.tile(cat_colors[:, np.newaxis, :], (1, STRIP_W, 1))

ax_top.imshow(h_strip, aspect='auto', interpolation='nearest')
ax_top.axis('off')
ax_right.imshow(v_strip, aspect='auto', interpolation='nearest', origin='upper')
ax_right.axis('off')

# ── Colourmap and display matrix ─────────────────────────────────────────────
mat_display = mat_ordered.astype(float)

if THRESHOLD > 0:
    mat_display[mat_display < THRESHOLD] = np.nan
    vmin           = THRESHOLD
    boundary_color = '#888888'
    cmap = plt.cm.YlOrRd.copy()
    cmap.set_bad('white')
else:
    vmin           = 0
    boundary_color = 'white'
    cmap = 'YlOrRd'

im = ax_main.imshow(mat_display, cmap=cmap, vmin=vmin, vmax=1.0,
                    aspect='auto', interpolation='nearest', origin='upper')

# ── Axis labels ──────────────────────────────────────────────────────────────
label_fs = max(5, min(9, 140 // n))
ax_main.set_xticks(range(n))
ax_main.set_xticklabels(labels_ordered, fontsize=label_fs, rotation=90)
ax_main.set_yticks(range(n))
ax_main.set_yticklabels(labels_ordered, fontsize=label_fs)
ax_main.tick_params(axis='both', which='both', length=2, pad=2)

# ── Category boundary lines ─────────────────────────────────────────────────
for k in range(len(cats_ordered) - 1):
    if cats_ordered[k] != cats_ordered[k + 1]:
        b = k + 0.5
        ax_main.axhline(b, color=boundary_color, lw=2, zorder=4)
        ax_main.axvline(b, color=boundary_color, lw=2, zorder=4)

plt.colorbar(im, cax=ax_cbar, label="Theil's U (row \u2192 col)")

# ── Category labels above top strip (45°) ───────────────────────────────────
cat_spans = []
prev_cat, start = None, 0
for k, cat in enumerate(cats_ordered):
    if cat != prev_cat:
        if prev_cat is not None:
            cat_spans.append((prev_cat, start, k - 1))
        prev_cat, start = cat, k
cat_spans.append((prev_cat, start, len(cats_ordered) - 1))

for cat, s, e in cat_spans:
    mid = (s + e) / 2
    ax_top.text(mid, -0.5, cat, fontsize=7, rotation=45,
                ha='left', va='bottom',
                transform=ax_top.transData, clip_on=False)

if THRESHOLD > 0:
    title = f"Theil's U Between Metrics (row predicts column)\n{n} metrics shown (filtered: at least one pair with U \u2265 {THRESHOLD})"
else:
    title = f"Theil's U Between Metrics (row predicts column)  ({n} metrics)"

ax_top.text(0.5, 3.6, title, fontsize=16, ha='center', va='bottom',
            transform=ax_top.transAxes, clip_on=False)

fig.savefig(OUT_PATH, dpi=dpi, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
