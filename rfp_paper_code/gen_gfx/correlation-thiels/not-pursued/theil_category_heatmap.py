#!/usr/bin/env python3
"""Category-level Theil's U heatmaps — asymmetric (non-mirrored).

Unlike AMI category heatmaps which are symmetric, Theil's U heatmaps use the
full matrix: cell (i,j) = aggregate U(category_i → category_j), meaning
"how well do metrics in category i predict metrics in category j".

Outputs:
  theil_category_heatmap_mean{FILTER_SUFFIX}.png  — mean U per direction
  theil_category_heatmap_max{FILTER_SUFFIX}.png   — max U per direction
  theil_category_heatmap_diff{FILTER_SUFFIX}.png  — asymmetry: mean(i→j) - mean(j→i)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from _theil_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

# ── Aggregate data ────────────────────────────────────────────────────────────
n       = len(CATEGORY_ORDER)
cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}

# Directional: sums[i,j] accumulates U where category i predicts category j
sums    = np.zeros((n, n))
maxes   = np.zeros((n, n))
counts  = np.zeros((n, n), dtype=int)

for r in load_rows():
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    u_ij = r['u_1to2']  # m1 predicts m2 → cat_i predicts cat_j
    u_ji = r['u_2to1']  # m2 predicts m1 → cat_j predicts cat_i

    sums[i, j]   += u_ij
    maxes[i, j]   = max(maxes[i, j], u_ij)
    counts[i, j] += 1

    if i != j:
        sums[j, i]   += u_ji
        maxes[j, i]   = max(maxes[j, i], u_ji)
        counts[j, i] += 1
    else:
        # Same category: both directions contribute to (i,i)
        sums[i, i]   += u_ji
        maxes[i, i]   = max(maxes[i, i], u_ji)
        counts[i, i] += 1

with np.errstate(invalid='ignore'):
    means = np.where(counts > 0, sums / counts, 0.0)


def _annotate(ax, data, fmt='.2f', fs=7):
    for i in range(n):
        for j in range(n):
            v = data[i, j]
            txt_color = 'white' if abs(v) > 0.55 else 'black'
            ax.text(j, i, f'{v:{fmt}}', ha='center', va='center',
                    fontsize=fs, color=txt_color, fontweight='bold')


def _axis_labels(ax, fs=9):
    ax.set_xticks(range(n))
    ax.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=fs)
    ax.set_yticks(range(n))
    ax.set_yticklabels(CATEGORY_ORDER, fontsize=fs)


def _add_color_strips(axes_list):
    for ax in axes_list:
        for i, cat in enumerate(CATEGORY_ORDER):
            ax.add_patch(plt.Rectangle(
                (-1.55, i - 0.5), 0.45, 1.0,
                color=CATEGORY_COLORS[cat], clip_on=False,
                transform=ax.transData,
            ))


# ── Plot 1: Mean Theil's U (directional) ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(means, cmap='YlOrRd', vmin=0, vmax=max(0.5, means.max()), aspect='auto')
_axis_labels(ax, fs=10)
ax.set_title("Mean Theil's U by Category (row predicts column)", fontsize=11)
ax.set_xlabel('Predicted category \u2192', fontsize=10)
ax.set_ylabel('\u2190 Predictor category', fontsize=10)
plt.colorbar(im, ax=ax, shrink=0.82)
_annotate(ax, means)
_add_color_strips([ax])
plt.tight_layout()
out = HERE / f'theil_category_heatmap_mean{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 2: Max Theil's U (directional) ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(maxes, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')
_axis_labels(ax, fs=10)
ax.set_title("Max Theil's U by Category (row predicts column)", fontsize=11)
ax.set_xlabel('Predicted category \u2192', fontsize=10)
ax.set_ylabel('\u2190 Predictor category', fontsize=10)
plt.colorbar(im, ax=ax, shrink=0.82)
_annotate(ax, maxes)
_add_color_strips([ax])
plt.tight_layout()
out = HERE / f'theil_category_heatmap_max{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)