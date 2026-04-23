#!/usr/bin/env python3
"""Line graph: best single combo per size vs % unique users, by OS.

Usage:
    ./shortcuts/viz_top_combo_by_os.py <minset_top5_dir> [output.png]
"""

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('MPLCONFIGDIR', '/tmp/claude-999/mpl')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from viz_minset_common import (
    discover_os_variants, parse_unique_baseline_from_txt,
)

OS_ORDER = ['WINNT', 'Darwin', 'Android', 'Linux']
OS_DISPLAY = {'WINNT': 'Windows', 'Darwin': 'macOS', 'Android': 'Android', 'Linux': 'Linux'}
OS_COLORS = {'WINNT': '#1f77b4', 'Darwin': '#ff7f0e', 'Android': '#2ca02c', 'Linux': '#d62728'}
OS_MARKERS = {'WINNT': 'o', 'Darwin': 's', 'Android': '^', 'Linux': 'D'}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_dir = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(input_dir, 'viz_top_combo_by_os.png')

    os_variants = discover_os_variants(input_dir)

    fig, ax = plt.subplots(figsize=(7, 5))

    for os_name in OS_ORDER:
        if os_name not in os_variants:
            continue

        os_combo, os_dedup = os_variants[os_name]
        txt_path = os.path.join(input_dir, f'min_set_combos_os_{os_name}.txt')
        unique_baseline = parse_unique_baseline_from_txt(txt_path)
        if not unique_baseline or not os_combo:
            continue

        # Find the best combo (highest ComboUnique) per size
        best_by_size = {}
        for r in os_combo:
            sz = r['combo_size']
            u = r['combo_unique']
            if sz not in best_by_size or u > best_by_size[sz][0]:
                best_by_size[sz] = (u, r['combo_name'])

        sizes = sorted(best_by_size.keys())
        pcts = [100 * best_by_size[sz][0] / unique_baseline for sz in sizes]

        ax.plot(sizes, pcts,
                marker=OS_MARKERS[os_name], color=OS_COLORS[os_name],
                linewidth=2, markersize=7, label=OS_DISPLAY[os_name])

        # Annotate the endpoints
        ax.annotate(f'{pcts[-1]:.0f}%', (sizes[-1], pcts[-1]),
                    textcoords='offset points', xytext=(8, 0),
                    fontsize=9, color=OS_COLORS[os_name])

    ax.set_xlabel('Combination Size (number of metrics)')
    ax.set_ylabel('% of Unique Users Identified')
    ax.set_xticks(sizes)
    ax.set_ylim(0, 105)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f'Saved: {out_path}')

    # Also copy to 000-img
    import shutil, time
    img_dir = '/work/sandbox-cache/000-img'
    if os.path.isdir(img_dir):
        ts = time.strftime('%Y%m%d_%H%M%S')
        dest = os.path.join(img_dir, f'{ts}_viz_top_combo_by_os.png')
        shutil.copy2(out_path, dest)
        print(f'Copied: {dest}')


if __name__ == '__main__':
    main()
