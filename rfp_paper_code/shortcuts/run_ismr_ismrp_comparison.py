#!/usr/bin/env python3
"""Generate a side-by-side ISMR vs ISMRP comparison graphic.

Takes two directories: one containing ISMR results, one containing ISMRP results.
Produces a figure with ISMR on the left, ISMRP on the right, connected by arrows
showing how each metric's rank changed.

Usage:
    ./shortcuts/run_ismr_ismrp_comparison.py <ismr_dir> <ismrp_dir>
    ./shortcuts/run_ismr_ismrp_comparison.py <dir>   # if both are in the same dir
"""

import argparse
import csv
import datetime
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
os.environ.setdefault('MPLCONFIGDIR', '/tmp/claude-999/mpl')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def load_ismr_csv(directory):
    """Load ISMR results CSV. Returns list of (metric, unique_after, pct)."""
    results = []
    for f in os.listdir(directory):
        if f.startswith('ismr_results_') and f.endswith('.csv') and 'ismrp' not in f:
            path = os.path.join(directory, f)
            with open(path, newline='') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    results.append((
                        row['MetricRemoved'],
                        int(row['UniqueUsersAfter']),
                        float(row['PctUnique']),
                    ))
            return results, f
    return None, None


def load_ismrp_csv(directory):
    """Load ISMRP results CSV. Returns list of (metric, unique_after, pct)."""
    results = []
    for f in os.listdir(directory):
        if f.startswith('ismrp_results_') and f.endswith('.csv'):
            path = os.path.join(directory, f)
            with open(path, newline='') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    results.append((
                        row['MetricReplaced'],
                        int(row['UniqueUsersAfter']),
                        float(row['PctUnique']),
                    ))
            return results, f
    return None, None


def make_comparison(ismr_data, ismrp_data, output_path, ismr_label, ismrp_label):
    """Generate the side-by-side comparison figure."""
    # Build position maps: metric -> row index
    ismr_metrics = {m: i for i, (m, _, _) in enumerate(ismr_data)}
    ismrp_metrics = {m: i for i, (m, _, _) in enumerate(ismrp_data)}

    # All metrics that appear in either list
    all_metrics = set(ismr_metrics.keys()) | set(ismrp_metrics.keys())

    n_left = len(ismr_data)
    n_right = len(ismrp_data)
    n_rows = max(n_left, n_right)

    row_height = 0.32
    fig_height = max(8, n_rows * row_height + 2)
    fig, ax = plt.subplots(figsize=(12, fig_height))
    ax.set_xlim(-0.3, 7.3)
    ax.set_ylim(-n_rows - 0.5, 1.5)
    ax.axis('off')

    # Column positions
    left_rank_x = 0.0
    left_metric_x = 0.3
    left_pct_x = 3.0
    center_x = 3.65
    right_rank_x = 4.3
    right_metric_x = 4.6
    right_pct_x = 7.0

    # Title
    ax.text((left_rank_x + center_x) / 2, 1.2, 'ISMR (Removal)',
            fontsize=14, fontweight='bold', ha='center', va='center')
    ax.text((right_rank_x + right_pct_x) / 2, 1.2, 'ISMRP (Replacement)',
            fontsize=14, fontweight='bold', ha='center', va='center')

    # Headers
    header_y = 0.5
    header_kw = dict(fontsize=9, fontweight='bold', va='center', color='#444444')
    ax.text(left_rank_x, header_y, '#', ha='center', **header_kw)
    ax.text(left_metric_x, header_y, 'Metric', ha='left', **header_kw)
    ax.text(left_pct_x, header_y, '%', ha='right', **header_kw)
    ax.text(right_rank_x, header_y, '#', ha='center', **header_kw)
    ax.text(right_metric_x, header_y, 'Metric', ha='left', **header_kw)
    ax.text(right_pct_x, header_y, '%', ha='right', **header_kw)

    # Vertical divider
    ax.plot([center_x, center_x], [1.0, -n_rows - 0.2], color='#999999',
            linewidth=1.5, linestyle='-', zorder=1)

    # Draw rows
    row_kw = dict(fontsize=8, va='center', fontfamily='monospace')

    def shorten(name, maxlen=28):
        return name if len(name) <= maxlen else name[:maxlen-1] + '…'

    # Left side (ISMR)
    for i, (metric, unique, pct) in enumerate(ismr_data):
        y = -i
        bg_color = '#f7f7f7' if i % 2 == 0 else '#ffffff'
        ax.fill_between([left_rank_x - 0.2, center_x - 0.1], y - 0.15, y + 0.15,
                       color=bg_color, zorder=0)
        ax.text(left_rank_x, y, str(i + 1), ha='center', color='#888888', **row_kw)
        ax.text(left_metric_x, y, shorten(metric), ha='left', **row_kw)
        ax.text(left_pct_x, y, f'{pct:.1f}%', ha='right', color='#666666', **row_kw)

    # Right side (ISMRP)
    for i, (metric, unique, pct) in enumerate(ismrp_data):
        y = -i
        bg_color = '#f7f7f7' if i % 2 == 0 else '#ffffff'
        ax.fill_between([center_x + 0.1, right_pct_x + 0.2], y - 0.15, y + 0.15,
                       color=bg_color, zorder=0)
        ax.text(right_rank_x, y, str(i + 1), ha='center', color='#888888', **row_kw)
        ax.text(right_metric_x, y, shorten(metric), ha='left', **row_kw)
        ax.text(right_pct_x, y, f'{pct:.1f}%', ha='right', color='#666666', **row_kw)

    # Draw arrows connecting matching metrics
    for metric in all_metrics:
        if metric not in ismr_metrics or metric not in ismrp_metrics:
            continue
        left_row = ismr_metrics[metric]
        right_row = ismrp_metrics[metric]
        y_left = -left_row
        y_right = -right_row

        rank_diff = right_row - left_row
        if rank_diff == 0:
            color = '#333333'   # same position — black
            alpha = 0.4
        elif rank_diff < 0:
            color = '#22aa22'   # higher rank (lower index) in ISMRP — green
            alpha = 0.6
        else:
            color = '#cc2222'   # lower rank in ISMRP — red
            alpha = 0.6

        ax.annotate('',
                    xy=(center_x + 0.12, y_right),
                    xytext=(center_x - 0.12, y_left),
                    arrowprops=dict(
                        arrowstyle='->', color=color, alpha=alpha,
                        linewidth=1.2, connectionstyle='arc3,rad=0.0',
                    ),
                    zorder=2)

    # Legend
    legend_y = -n_rows - 0.3
    legend_kw = dict(fontsize=8, va='center')
    ax.plot([], [], color='#333333', linewidth=1.5, label='Same rank')
    ax.plot([], [], color='#22aa22', linewidth=1.5, label='Higher rank in ISMRP')
    ax.plot([], [], color='#cc2222', linewidth=1.5, label='Lower rank in ISMRP')
    ax.legend(loc='lower center', ncol=3, fontsize=8, framealpha=0.8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Wrote {output_path}")

    # Copy to 000-img
    img_dir = "/work/sandbox-cache/000-img"
    if os.path.isdir(img_dir):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(img_dir, f"{ts}_{os.path.basename(output_path)}")
        shutil.copy2(output_path, dest)
        print(f"Copied to {dest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dirs", nargs='+',
                        help="One or two directories containing ISMR/ISMRP result CSVs")
    args = parser.parse_args()

    if len(args.dirs) == 1:
        ismr_dir = ismrp_dir = os.path.abspath(args.dirs[0])
    elif len(args.dirs) == 2:
        ismr_dir = os.path.abspath(args.dirs[0])
        ismrp_dir = os.path.abspath(args.dirs[1])
    else:
        parser.error("Provide one or two directories")

    ismr_data, ismr_file = load_ismr_csv(ismr_dir)
    if not ismr_data:
        print(f"ERROR: No ismr_results_*.csv found in {ismr_dir}", file=sys.stderr)
        sys.exit(1)
    print(f"ISMR: {len(ismr_data)} metrics from {ismr_file}")

    ismrp_data, ismrp_file = load_ismrp_csv(ismrp_dir)
    if not ismrp_data:
        print(f"ERROR: No ismrp_results_*.csv found in {ismrp_dir}", file=sys.stderr)
        sys.exit(1)
    print(f"ISMRP: {len(ismrp_data)} metrics from {ismrp_file}")

    # Determine output path
    out_dir = ismr_dir if ismr_dir == ismrp_dir else os.path.dirname(ismr_dir)
    output_path = os.path.join(out_dir, "ismr_vs_ismrp_comparison.png")

    make_comparison(ismr_data, ismrp_data, output_path,
                    os.path.basename(ismr_dir), os.path.basename(ismrp_dir))


if __name__ == "__main__":
    main()
