#!/usr/bin/env python3
"""Arc network: metrics in a fixed ring grouped by category.

Metrics are placed on a circle in category order (with gaps between categories).
Correlation edges are drawn as Bezier arcs inside the circle.
Edge opacity and color encode AMI strength.
Unlike force-directed layouts, positions are stable and category structure
is always visible.

Outputs corr_arc_network{FILTER_SUFFIX}.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import numpy as np
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

MIN_AMI   = float(os.environ.get('CORR_MIN_AMI', '0.25'))
OUT_PATH  = HERE / f'corr_arc_network{FILTER_SUFFIX}.png'

# ── Load and filter ───────────────────────────────────────────────────────────
rows = load_rows()
metrics_set = sorted({r['metric1'] for r in rows} | {r['metric2'] for r in rows})

# Arrange metrics by category, with a gap between categories
GAP_FRAC   = 0.03    # fraction of circle per inter-category gap
n_cats     = len(CATEGORY_ORDER)
cat_metrics = defaultdict(list)
other = []
for m in metrics_set:
    cat = get_category(m)
    if cat in CATEGORY_ORDER:
        cat_metrics[cat].append(m)
    else:
        other.append(m)
if other:
    cat_metrics['Other'] = other

active_cats = [c for c in CATEGORY_ORDER if cat_metrics[c]] + \
              (['Other'] if cat_metrics.get('Other') else [])

n_gaps   = len(active_cats)
n_total  = len(metrics_set)
gap_used = GAP_FRAC * n_gaps
arc_used = 1.0 - gap_used

# Assign angle to each metric
angles = {}
pos = 0.0
cat_spans = {}   # cat → (start_frac, end_frac)
for cat in active_cats:
    ms = sorted(cat_metrics[cat])
    cat_start = pos
    for m in ms:
        angles[m] = pos / 1.0 * 2 * np.pi
        pos += arc_used / n_total
    cat_spans[cat] = (cat_start, pos)
    pos += GAP_FRAC

RADIUS = 1.0
coords = {m: (np.cos(a) * RADIUS, np.sin(a) * RADIUS) for m, a in angles.items()}

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 14))
ax.set_aspect('equal')
ax.axis('off')

# Draw edges (sorted by AMI so strong edges are on top)
edge_rows = sorted([r for r in rows if r['ami'] >= MIN_AMI], key=lambda r: r['ami'])
for r in edge_rows:
    m1, m2, ami = r['metric1'], r['metric2'], r['ami']
    if m1 not in coords or m2 not in coords:
        continue
    x1, y1 = coords[m1]
    x2, y2 = coords[m2]
    # Control point: pull toward center proportional to angular distance
    cx = (x1 + x2) * 0.2
    cy = (y1 + y2) * 0.2
    alpha = 0.10 + 0.65 * ((ami - MIN_AMI) / (1.0 - MIN_AMI))
    lw    = 0.4 + 2.5 * ((ami - MIN_AMI) / (1.0 - MIN_AMI))
    color = CATEGORY_COLORS.get(get_category(m1), '#888888')
    verts = [(x1, y1), (cx, cy), (x2, y2)]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
    patch = PathPatch(Path(verts, codes), facecolor='none',
                      edgecolor=color, linewidth=lw, alpha=alpha, zorder=1)
    ax.add_patch(patch)

# Draw category arcs on the outside
ARC_THICK = 0.045
for cat in active_cats:
    color = CATEGORY_COLORS.get(cat, '#888888')
    start_frac, end_frac = cat_spans[cat]
    n_ms = len(cat_metrics[cat])
    if n_ms == 0:
        continue
    # Draw thick arc from start to end
    thetas = np.linspace(start_frac * 2 * np.pi,
                         end_frac   * 2 * np.pi - 0.01, 60)
    r_inner = RADIUS + 0.04
    r_outer = RADIUS + 0.04 + ARC_THICK
    xs_outer = np.cos(thetas) * r_outer
    ys_outer = np.sin(thetas) * r_outer
    xs_inner = np.cos(thetas[::-1]) * r_inner
    ys_inner = np.sin(thetas[::-1]) * r_inner
    xs = np.concatenate([xs_outer, xs_inner])
    ys = np.concatenate([ys_outer, ys_inner])
    ax.fill(xs, ys, color=color, alpha=0.85, zorder=4)

    # Category label
    mid_frac = (start_frac + end_frac) / 2
    mid_a    = mid_frac * 2 * np.pi
    label_r  = RADIUS + 0.04 + ARC_THICK + 0.10
    lx, ly   = np.cos(mid_a) * label_r, np.sin(mid_a) * label_r
    ha = 'left' if np.cos(mid_a) > 0 else 'right'
    ax.text(lx, ly, cat, ha=ha, va='center', fontsize=8,
            fontweight='bold', color=color, zorder=5)

# Draw metric dots
for m, (x, y) in coords.items():
    color = CATEGORY_COLORS.get(get_category(m), '#888888')
    ax.plot(x, y, 'o', ms=3.5, color=color, zorder=3, alpha=0.9)

ax.set_xlim(-1.65, 1.65)
ax.set_ylim(-1.65, 1.65)

n_edges = sum(1 for r in rows if r['ami'] >= MIN_AMI)
fig.suptitle(
    f'Arc Network: {len(metrics_set)} metrics on a ring, grouped by category\n'
    f'{n_edges} edges with AMI ≥ {MIN_AMI:.2f}  |  edge width & opacity ∝ AMI',
    fontsize=11, y=0.97,
)
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
