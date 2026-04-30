#!/usr/bin/env python3
"""Compare Theil's U with AMI for the same metric pairs.

Shows where the two measures agree and disagree. AMI is symmetric while
Theil's U is directional, so we compare AMI vs max(U_1to2, U_2to1) and
AMI vs min(U_1to2, U_2to1).

Requires both THEIL_CSV and AMI_CSV environment variables.

Outputs:
  theil_vs_ami_maxu{FILTER_SUFFIX}.png  — AMI vs max(U) scatter
  theil_vs_ami_asym{FILTER_SUFFIX}.png  — AMI vs asymmetry(U) scatter
"""
import os
import csv
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from _theil_utils import (load_rows as load_theil_rows, get_category,
                          CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE)

# Load AMI data
AMI_CSV = os.environ.get('AMI_CSV', '')
if not AMI_CSV or not os.path.exists(AMI_CSV):
    print(f"""\
Error: AMI CSV not found. Set AMI_CSV environment variable.

  AMI_CSV=path/to/ami_threshold_30.csv
""", file=sys.stderr)
    sys.exit(1)

ami_lookup = {}
with open(AMI_CSV) as f:
    for r in csv.DictReader(f):
        key = (r['metric1'], r['metric2'])
        ami_lookup[key] = float(r['ami'])

# Load Theil's U data and match
theil_rows = load_theil_rows()

matched = []
for r in theil_rows:
    key = (r['metric1'], r['metric2'])
    key_rev = (r['metric2'], r['metric1'])
    ami = ami_lookup.get(key) or ami_lookup.get(key_rev)
    if ami is not None:
        matched.append({**r, 'ami': ami})

print(f"Matched {len(matched)} pairs between Theil's U and AMI CSVs")

if not matched:
    sys.exit(0)

ami_vals = np.array([r['ami'] for r in matched])
max_u    = np.array([max(r['u_1to2'], r['u_2to1']) for r in matched])
min_u    = np.array([min(r['u_1to2'], r['u_2to1']) for r in matched])
asym     = np.array([abs(r['u_1to2'] - r['u_2to1']) for r in matched])

cats1 = [get_category(r['metric1']) for r in matched]
cats2 = [get_category(r['metric2']) for r in matched]
colors = [CATEGORY_COLORS[c1] if c1 == c2 else '#aaaaaa'
          for c1, c2 in zip(cats1, cats2)]

# ── Plot 1: AMI vs max(U) ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

ax = axes[0]
ax.scatter(ami_vals, max_u, c=colors, s=8, alpha=0.5, linewidths=0, zorder=3)
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.4)
ax.set_xlabel('AMI (symmetric)', fontsize=12)
ax.set_ylabel("max Theil's U (either direction)", fontsize=12)
ax.set_title('AMI vs. Max Theil\'s U', fontsize=13)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.grid(lw=0.3, alpha=0.4)

ax = axes[1]
ax.scatter(ami_vals, min_u, c=colors, s=8, alpha=0.5, linewidths=0, zorder=3)
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.4)
ax.set_xlabel('AMI (symmetric)', fontsize=12)
ax.set_ylabel("min Theil's U (weaker direction)", fontsize=12)
ax.set_title('AMI vs. Min Theil\'s U', fontsize=13)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.grid(lw=0.3, alpha=0.4)

handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
handles.append(mpatches.Patch(color='#aaaaaa', label='Cross-cat'))
axes[1].legend(handles=handles, fontsize=6.5, loc='upper left', ncol=2, framealpha=0.9)

plt.suptitle("Theil's U vs AMI Comparison", fontsize=14)
plt.tight_layout()
out = HERE / f'theil_vs_ami_maxu{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 2: AMI vs Asymmetry ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
ax.scatter(ami_vals, asym, c=colors, s=10, alpha=0.5, linewidths=0, zorder=3)
ax.set_xlabel('AMI (symmetric)', fontsize=12)
ax.set_ylabel("|U(m1\u2192m2) \u2212 U(m2\u2192m1)|  [asymmetry]", fontsize=12)
ax.set_title("AMI vs. Theil's U Asymmetry", fontsize=13)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, max(0.5, asym.max() * 1.05))
ax.grid(lw=0.3, alpha=0.4)

handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
handles.append(mpatches.Patch(color='#aaaaaa', label='Cross-cat'))
ax.legend(handles=handles, fontsize=6.5, loc='upper right', ncol=2, framealpha=0.9)

plt.tight_layout()
out = HERE / f'theil_vs_ami_asym{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
