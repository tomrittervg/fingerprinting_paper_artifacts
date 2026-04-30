#!/usr/bin/env python3
"""Chord diagram: inter-category AMI.

Categories arranged around a circle. Bezier chords connect category pairs;
chord width at each end is proportional to the mean AMI for that direction.
Chords below MIN_MEAN_AMI are omitted for clarity.

Outputs corr_chord{FILTER_SUFFIX}.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc, FancyArrowPatch
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import numpy as np
from collections import defaultdict

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

MIN_MEAN_AMI = 0.05   # skip chords below this mean AMI

OUT_PATH = HERE / f'corr_chord{FILTER_SUFFIX}.png'

# ── Accumulate mean AMI between category pairs ────────────────────────────────
rows = load_rows()
sums   = defaultdict(float)
counts = defaultdict(int)
for r in rows:
    c1, c2 = get_category(r['metric1']), get_category(r['metric2'])
    key = tuple(sorted([c1, c2]))
    sums[key]   += r['ami']
    counts[key] += 1

mean_ami = {k: sums[k] / counts[k] for k in sums}

# Only categories that appear
active_cats = [c for c in CATEGORY_ORDER
               if any(c in k for k in mean_ami)]
n = len(active_cats)
cat_idx = {c: i for i, c in enumerate(active_cats)}

# ── Layout: categories evenly spaced on unit circle ───────────────────────────
GAP_DEG   = 4.0       # gap between category arcs (degrees)
ARC_WIDTH = 0.08      # radial width of arc band
RADIUS    = 1.0
arc_deg   = (360.0 - n * GAP_DEG) / n
gap_rad   = np.deg2rad(GAP_DEG)
arc_rad   = np.deg2rad(arc_deg)

# Start angle for each category (counterclockwise)
starts = {}
angle = np.pi / 2    # start at top
for cat in active_cats:
    starts[cat] = angle
    angle += arc_rad + gap_rad

def cat_mid_angle(cat):
    return starts[cat] + arc_rad / 2

def chord_control(a1, a2, depth=0.5):
    """Bezier control point pulled toward center for a chord between two angles."""
    mx = np.cos((a1 + a2) / 2) * depth
    my = np.sin((a1 + a2) / 2) * depth
    return mx, my

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect('equal')
ax.axis('off')

# Draw chords (behind arcs)
for c1 in active_cats:
    for c2 in active_cats:
        if c2 <= c1:
            continue
        key = tuple(sorted([c1, c2]))
        ami = mean_ami.get(key, 0)
        if ami < MIN_MEAN_AMI:
            continue

        a1 = cat_mid_angle(c1)
        a2 = cat_mid_angle(c2)
        x1, y1 = np.cos(a1) * RADIUS, np.sin(a1) * RADIUS
        x2, y2 = np.cos(a2) * RADIUS, np.sin(a2) * RADIUS
        cx, cy = chord_control(a1, a2, depth=0.35)

        lw = 1.0 + ami * 18
        color = CATEGORY_COLORS[c1]
        verts = [(x1, y1), (cx, cy), (x2, y2)]
        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(verts, codes)
        patch = PathPatch(path, facecolor='none', edgecolor=color,
                          linewidth=lw, alpha=0.45, zorder=1)
        ax.add_patch(patch)

# Draw category arcs (on top of chords)
for cat in active_cats:
    color = CATEGORY_COLORS[cat]
    a_start = np.rad2deg(starts[cat])
    a_end   = a_start + arc_deg

    # Outer arc band
    for r_off, lw in [(RADIUS, 12), (RADIUS + ARC_WIDTH, 3)]:
        arc = Arc((0, 0), 2*r_off, 2*r_off,
                  angle=0, theta1=a_start, theta2=a_end,
                  color=color, linewidth=lw, zorder=2)
        ax.add_patch(arc)

    # Category label
    mid = np.deg2rad(a_start + arc_deg / 2)
    label_r = RADIUS + ARC_WIDTH + 0.13
    lx, ly = np.cos(mid) * label_r, np.sin(mid) * label_r
    ha = 'left' if np.cos(mid) > 0 else 'right'
    ax.text(lx, ly, cat, ha=ha, va='center', fontsize=9,
            fontweight='bold', color=color, zorder=3)

ax.set_xlim(-1.55, 1.55)
ax.set_ylim(-1.55, 1.55)

# Self-loops: within-category AMI shown as arc radius bump
for cat in active_cats:
    key = (cat, cat)
    ami = mean_ami.get(key, 0)
    if ami < MIN_MEAN_AMI:
        continue
    a_start = np.rad2deg(starts[cat])
    a_end   = a_start + arc_deg
    mid = np.deg2rad(a_start + arc_deg / 2)
    bump_r = RADIUS + ARC_WIDTH + 0.03 + ami * 0.18
    arc = Arc((0, 0), 2*bump_r, 2*bump_r,
              angle=0, theta1=a_start, theta2=a_end,
              color=CATEGORY_COLORS[cat], linewidth=2 + ami*8,
              linestyle='--', alpha=0.6, zorder=2)
    ax.add_patch(arc)

fig.suptitle(
    f'Inter-Category AMI Chord Diagram  (min mean AMI = {MIN_MEAN_AMI:.2f})\n'
    'Chord width ∝ mean AMI  |  dashed arc = within-category mean AMI',
    fontsize=11, y=0.97,
)
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
