#!/usr/bin/env python3
"""Category-level aggregate heatmaps: mean+max panel, max-only panel, counts panel.

Outputs three PNGs:
  corr_category_heatmap_meanmax{FILTER_SUFFIX}.png  — 2 panels: mean AMI + max AMI
  corr_category_heatmap_max{FILTER_SUFFIX}.png      — single panel: max AMI
  corr_category_heatmap_counts{FILTER_SUFFIX}.png   — 2 panels: mean AMI + pair count
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from _corr_utils import load_rows, get_category, CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

# ── Aggregate data ─────────────────────────────────────────────────────────────
n       = len(CATEGORY_ORDER)
cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
sums    = np.zeros((n, n))
maxes   = np.zeros((n, n))
counts  = np.zeros((n, n), dtype=int)

for r in load_rows():
    ami = r['ami']
    i = cat_idx[get_category(r['metric1'])]
    j = cat_idx[get_category(r['metric2'])]
    if i == j:
        sums[i, j]   += ami
        maxes[i, j]   = max(maxes[i, j], ami)
        counts[i, j] += 1
    else:
        for a, b in ((i, j), (j, i)):
            sums[a, b]   += ami
            maxes[a, b]   = max(maxes[a, b], ami)
            counts[a, b] += 1

means = np.where(counts > 0, sums / counts, 0.0)


def _annotate(ax, data, counts, fs=7):
    """Annotate each cell with value and pair count."""
    for i in range(n):
        for j in range(n):
            v   = data[i, j]
            cnt = counts[i, j]
            txt_color = 'white' if v > 0.55 else 'black'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                    fontsize=fs, color=txt_color, fontweight='bold')
            if cnt > 0:
                ax.text(j, i + 0.38, f'({cnt:,})', ha='center', va='center',
                        fontsize=4.5, color=txt_color, alpha=0.75)


def _add_color_strips(axes_list):
    """Add category color rectangle on the left side of each axis."""
    for ax in axes_list:
        for i, cat in enumerate(CATEGORY_ORDER):
            ax.add_patch(plt.Rectangle(
                (-1.55, i - 0.5), 0.45, 1.0,
                color=CATEGORY_COLORS[cat], clip_on=False,
                transform=ax.transData,
            ))


def _axis_labels(ax, fs=9):
    ax.set_xticks(range(n))
    ax.set_xticklabels(CATEGORY_ORDER, rotation=45, ha='right', fontsize=fs)
    ax.set_yticks(range(n))
    ax.set_yticklabels(CATEGORY_ORDER, fontsize=fs)


# ── Plot 1: mean + max (2 panels) ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(19, 8))
for ax, data, title in [
    (axes[0], means, 'Mean AMI between categories'),
    (axes[1], maxes, 'Max AMI between categories'),
]:
    im = ax.imshow(data, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')
    _axis_labels(ax)
    ax.set_title(title, fontsize=11)
    plt.colorbar(im, ax=ax, shrink=0.82)
    _annotate(ax, data, counts)
_add_color_strips(axes)
plt.suptitle('Category-Level AMI Heatmap', fontsize=13)
plt.tight_layout()
out = HERE / f'corr_category_heatmap_meanmax{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 2: max AMI only (single panel) ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(maxes, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')
_axis_labels(ax, fs=10)
ax.set_title('Max AMI between categories', fontsize=11)
plt.colorbar(im, ax=ax, shrink=0.82)
_annotate(ax, maxes, counts, fs=9)
_add_color_strips([ax])
plt.suptitle('Category-Level Max AMI Heatmap', fontsize=13)
plt.tight_layout()
out = HERE / f'corr_category_heatmap_max{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)

# ── Plot 3: mean AMI + pair count (2 panels) ──────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(19, 8))

ax = axes[0]
im = ax.imshow(means, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')
_axis_labels(ax)
ax.set_title('Mean AMI between categories', fontsize=11)
plt.colorbar(im, ax=ax, shrink=0.82)
_annotate(ax, means, counts)

ax = axes[1]
counts_f = counts.astype(float)
im2 = ax.imshow(counts_f, cmap='Blues', vmin=0, vmax=counts.max(), aspect='auto')
_axis_labels(ax)
ax.set_title('Pair count between categories', fontsize=11)
plt.colorbar(im2, ax=ax, shrink=0.82)
for i in range(n):
    for j in range(n):
        cnt = counts[i, j]
        rel = counts_f[i, j] / (counts.max() + 1e-9)
        txt_color = 'white' if rel > 0.55 else 'black'
        ax.text(j, i, f'{cnt:,}', ha='center', va='center',
                fontsize=7, color=txt_color, fontweight='bold')

_add_color_strips(axes)
plt.suptitle('Category-Level AMI and Pair Count Heatmaps', fontsize=13)
plt.tight_layout()
out = HERE / f'corr_category_heatmap_counts{FILTER_SUFFIX}.png'
fig.savefig(out, dpi=150, bbox_inches='tight')
print(f"Wrote {out}")
plt.close(fig)
