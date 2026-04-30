"""Shared data-loading and drawing logic for scatter plot scripts.

Exports:
  PlotSpec            — namedtuple describing one plot variant
  PLOTS               — canonical list of 4 PlotSpec entries
  load_scatter_data() — load all data once; returns a dict
  build_scatter_data()— convert PlotSpec + data dict → plot-ready arrays
  draw_scatter()      — draw one scatter panel onto an existing Axes
"""
import numpy as np
import matplotlib.patches as mpatches
from collections import defaultdict, namedtuple
from _corr_utils import (
    load_rows, load_per_metric, load_true_hhi,
    get_category, CATEGORY_ORDER, CATEGORY_COLORS,
)

# ── Config ─────────────────────────────────────────────────────────────────────

PlotSpec = namedtuple('PlotSpec', ['x_type', 'pair_filter', 'out_name'])

PLOTS = [
    PlotSpec('hhi',     'all',      'corr_scatter_hhi_maxami_all.png'),
    PlotSpec('entropy', 'all',      'corr_scatter_entropy_maxami_all.png'),
    PlotSpec('hhi',     'crosscat', 'corr_scatter_hhi_maxami_crosscat.png'),
    PlotSpec('entropy', 'crosscat', 'corr_scatter_entropy_maxami_crosscat.png'),
]

# ── Data loading ───────────────────────────────────────────────────────────────

def load_scatter_data() -> dict:
    """Load all source data once.  Returns a dict with keys:
      rows, entropy, max_ami_all, max_ami_crosscat, hhi_map
    """
    rows = load_rows()
    entropy, max_ami_all = load_per_metric(rows)
    hhi_map = load_true_hhi()

    max_ami_crosscat = defaultdict(float)
    for r in rows:
        m1, m2 = r['metric1'], r['metric2']
        if get_category(m1) != get_category(m2):
            max_ami_crosscat[m1] = max(max_ami_crosscat[m1], r['ami'])
            max_ami_crosscat[m2] = max(max_ami_crosscat[m2], r['ami'])

    return dict(rows=rows, entropy=entropy, max_ami_all=max_ami_all,
                max_ami_crosscat=max_ami_crosscat, hhi_map=hhi_map)


def build_scatter_data(spec: PlotSpec, data: dict):
    """Convert a PlotSpec + loaded data bundle into plot-ready arrays.

    Returns a dict, or None if HHI data is unavailable for an HHI spec.
    """
    entropy  = data['entropy']
    hhi_map  = data['hhi_map']
    max_ami  = data['max_ami_all'] if spec.pair_filter == 'all' \
               else data['max_ami_crosscat']

    pair_label = 'All Comparisons' if spec.pair_filter == 'all' \
                 else 'Cross-Category Comparisons Only'

    if spec.x_type == 'hhi':
        if not hhi_map:
            return None
        metrics = sorted(m for m in entropy if m in hhi_map)
        x_vals  = np.array([1 - hhi_map[m] for m in metrics])
        x_label = 'HHI Score'
        title   = f'Per-Metric: HHI Score vs. Max AMI\n{pair_label}'
        norm_x  = (1 - x_vals) / max(1 - x_vals.min(), 1e-9)
    else:
        metrics = sorted(entropy)
        x_vals  = np.array([entropy[m] for m in metrics])
        x_label = 'Shannon Entropy  (bits)'
        title   = f'Per-Metric: Entropy vs. Max AMI\n{pair_label}'
        norm_x  = x_vals / x_vals.max()

    ami_vals = np.array([max_ami[m] for m in metrics])
    colors   = [CATEGORY_COLORS.get(get_category(m), '#888888') for m in metrics]
    sizes    = 24 + 54 * norm_x ** 1.5

    return dict(
        x_vals=x_vals, ami_vals=ami_vals,
        colors=colors, sizes=sizes,
        med_x=float(np.median(x_vals)), med_ami=float(np.median(ami_vals)),
        x_label=x_label, title=title,
    )

# ── Drawing ────────────────────────────────────────────────────────────────────

def draw_scatter(ax, panel_data: dict, *,
                 fontsize_axis=18, fontsize_title=16,
                 fontsize_ticks=14, fontsize_legend=13,
                 legend_title_fontsize=14, legend_loc='lower right',
                 legend_ncol=2, show_legend=True):
    """Draw a scatter panel onto an existing Axes.

    Does NOT add a figure-level footnote — that is the caller's responsibility.
    All size/layout parameters are keyword-only so the caller can override
    selectively without affecting anything else.
    """
    ax.scatter(panel_data['x_vals'], panel_data['ami_vals'],
               c=panel_data['colors'], s=panel_data['sizes'],
               alpha=0.75, linewidths=0.3, edgecolors='white', zorder=3)
    ax.set_xlabel(panel_data['x_label'], fontsize=fontsize_axis)
    ax.set_ylabel('Max AMI with any other metric', fontsize=fontsize_axis)
    ax.set_title(panel_data['title'], fontsize=fontsize_title)
    ax.tick_params(axis='both', labelsize=fontsize_ticks)
    ax.grid(lw=0.3, alpha=0.4, zorder=0)
    ax.axhline(panel_data['med_ami'], color='gray', lw=0.8, ls='--', alpha=0.5)
    ax.axvline(panel_data['med_x'],   color='gray', lw=0.8, ls=':', alpha=0.5)

    if show_legend:
        handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c)
                   for c in CATEGORY_ORDER]
        ax.legend(handles=handles, fontsize=fontsize_legend,
                  loc=legend_loc, ncol=legend_ncol, framealpha=0.9,
                  title='Category', title_fontsize=legend_title_fontsize)
