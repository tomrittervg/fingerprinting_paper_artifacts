#!/usr/bin/env python3
"""Full pairwise AMI heatmap with per-metric axis labels.

Ordered by category then alphabetically within category.

Optional threshold mode (CORR_THRESHOLD env var):
  - Unset or 0: include all metrics, full viridis colour scale.
  - > 0 (e.g. 0.6): only metrics whose max AMI reaches the threshold are
    included; cells below threshold are shown white; colour scale starts
    at the threshold value.

Outputs:
  CORR_THRESHOLD unset/0  →  corr_all_heatmap_labeled{FILTER_SUFFIX}.png
  CORR_THRESHOLD=0.6      →  corr_all_heatmap_labeled_t0.6{FILTER_SUFFIX}.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

THRESHOLD   = float(os.environ.get('CORR_THRESHOLD', '0'))
LOWER_ONLY  = bool(os.environ.get('CORR_LOWER_ONLY', ''))

_suffix = (f'_t{THRESHOLD}' if THRESHOLD > 0 else '') + ('_lower' if LOWER_ONLY else '')
OUT_PATH = HERE / f'corr_all_heatmap_labeled{_suffix}.png'

# ── Load rows ─────────────────────────────────────────────────────────────────
print("Loading pairs…")
rows = load_rows()

# ── Metric selection ──────────────────────────────────────────────────────────
if THRESHOLD > 0:
    max_ami = defaultdict(float)
    for r in rows:
        max_ami[r['metric1']] = max(max_ami[r['metric1']], r['ami'])
        max_ami[r['metric2']] = max(max_ami[r['metric2']], r['ami'])
    kept    = {m for m, v in max_ami.items() if v >= THRESHOLD}
    metrics = sorted(kept)
else:
    metrics = sorted({r['metric1'] for r in rows} | {r['metric2'] for r in rows})

n     = len(metrics)
m_idx = {m: i for i, m in enumerate(metrics)}
print(f"  {n} metrics" + (f" with max AMI ≥ {THRESHOLD}" if THRESHOLD > 0 else "") +
      f", {len(rows):,} pairs")

# ── Build dense AMI matrix ────────────────────────────────────────────────────
print("Building matrix…")
mat = np.zeros((n, n), dtype=np.float32)
np.fill_diagonal(mat, 1.0)
for r in rows:
    m1, m2 = r['metric1'], r['metric2']
    if m1 in m_idx and m2 in m_idx:
        i, j = m_idx[m1], m_idx[m2]
        mat[i, j] = r['ami']
        mat[j, i] = r['ami']

# ── Order by category then alphabetical ──────────────────────────────────────
print("Ordering…")
cat_rank = {c: i for i, c in enumerate(CATEGORY_ORDER)}
order = sorted(range(n), key=lambda i: (cat_rank.get(get_category(metrics[i]), 999), metrics[i]))

mat_ordered    = mat[np.ix_(order, order)]
cats_ordered   = [get_category(metrics[i]) for i in order]
labels_ordered = [metrics[i] for i in order]

# ── Category color arrays for margin strips ───────────────────────────────────
cat_colors = np.array([[int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
                        for c in (CATEGORY_COLORS[c] for c in cats_ordered)],
                       dtype=np.uint8)

# ── Plot ──────────────────────────────────────────────────────────────────────
print("Plotting…")
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

# ── Colourmap and display matrix ──────────────────────────────────────────────
mat_display = mat_ordered.astype(float)

if THRESHOLD > 0:
    mat_display[mat_display < THRESHOLD] = np.nan
    vmin           = THRESHOLD
    boundary_color = '#888888'
else:
    vmin           = 0
    boundary_color = 'white'

if LOWER_ONLY:
    ui, uj = np.triu_indices(n, k=1)   # upper triangle, above diagonal
    mat_display[ui, uj] = np.nan
    boundary_color = '#888888'         # gray lines visible on white

if THRESHOLD > 0 or LOWER_ONLY:
    cmap = plt.cm.viridis.copy()
    cmap.set_bad('white')
else:
    cmap = 'viridis'

im = ax_main.imshow(mat_display, cmap=cmap, vmin=vmin, vmax=1.0,
                    aspect='auto', interpolation='nearest', origin='upper')

# ── Axis labels ───────────────────────────────────────────────────────────────
label_fs = max(5, min(9, 140 // n))
ax_main.set_xticks(range(n))
ax_main.set_xticklabels(labels_ordered, fontsize=label_fs, rotation=90)
ax_main.set_yticks(range(n))
ax_main.set_yticklabels(labels_ordered, fontsize=label_fs)
ax_main.tick_params(axis='both', which='both', length=2, pad=2)

# ── Category boundary lines ───────────────────────────────────────────────────
for k in range(len(cats_ordered) - 1):
    if cats_ordered[k] != cats_ordered[k + 1]:
        b = k + 0.5
        if LOWER_ONLY:
            # Clip lines to lower triangle: horizontal stops at diagonal,
            # vertical starts at diagonal
            ax_main.plot([-0.5, b], [b, b], color=boundary_color, lw=2, zorder=4)
            ax_main.plot([b, b], [b, n - 0.5], color=boundary_color, lw=2, zorder=4)
        else:
            ax_main.axhline(b, color=boundary_color, lw=2, zorder=4)
            ax_main.axvline(b, color=boundary_color, lw=2, zorder=4)

plt.colorbar(im, cax=ax_cbar, label='AMI')

# ── Category labels above top strip (45°) ────────────────────────────────────
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
    title = f'AMI Heatmap — Metrics with Max AMI ≥ {THRESHOLD}  ({n} metrics)'
else:
    title = 'AMI Correlation Between Metrics'

ax_top.text(0.5, 3.6, title, fontsize=16, ha='center', va='bottom',
            transform=ax_top.transAxes, clip_on=False)

fig.savefig(OUT_PATH, dpi=dpi, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
