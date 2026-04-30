#!/usr/bin/env python3
"""Line graph: best single combo per size vs % unique users, by OS.

Usage:
    ./shortcuts/viz_top_combo_by_os.py <minset_top5_dir> [output.png]
"""

import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

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

    dirs = [a for a in sys.argv[1:] if os.path.isdir(a)]
    if not dirs:
        print("No directories specified", file=sys.stderr)
        sys.exit(1)
    out_path = os.path.join(os.getcwd(), 'viz_top_combo_by_os.png')

    # Merge os_variants from all input directories
    os_variants = {}
    for d in dirs:
        for os_name, (combo, dedup) in discover_os_variants(d).items():
            if os_name not in os_variants:
                os_variants[os_name] = (combo, dedup)

    fig, ax = plt.subplots(figsize=(7, 5))

    for os_name in OS_ORDER:
        if os_name not in os_variants:
            continue

        os_combo, os_dedup = os_variants[os_name]
        unique_baseline = None
        for d in dirs:
            txt_path = os.path.join(d, f'min_set_combos_os_{os_name}.txt')
            unique_baseline = parse_unique_baseline_from_txt(txt_path)
            if unique_baseline:
                break
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

    # Write provenance log
    log_path = os.path.join(os.path.dirname(out_path) or '.', 'run_top_combo_by_os.log')
    write_run_log(log_path, dirs, os_variants, out_path)


def write_run_log(log_path, dirs, os_variants, out_path):
    lines = []
    lines.append('=' * 60)
    lines.append('viz_top_combo_by_os — Provenance Log')
    lines.append(f'Generated: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}')
    lines.append('=' * 60)
    lines.append('')
    lines.append(f'SOURCE DIRECTORIES: {len(dirs)}')
    for d in dirs:
        lines.append(f'  {d}')
    lines.append('')
    lines.append('PER-OS DATA')
    for os_name in OS_ORDER:
        if os_name not in os_variants:
            continue
        os_combo, os_dedup = os_variants[os_name]
        baseline = None
        for d in dirs:
            txt_path = os.path.join(d, f'min_set_combos_os_{os_name}.txt')
            baseline = parse_unique_baseline_from_txt(txt_path)
            if baseline:
                break
        n_combos = len(os_combo) if os_combo else 0
        sizes = sorted({r['combo_size'] for r in os_combo}) if os_combo else []
        baseline_str = f'{baseline:,}' if baseline else 'unknown'
        lines.append(f'  {OS_DISPLAY.get(os_name, os_name):8s}  '
                     f'baseline_unique={baseline_str}  '
                     f'combos={n_combos}  sizes={sizes}')
    lines.append('')
    lines.append('OUTPUT')
    lines.append(f'  {out_path}')
    lines.append('')

    with open(log_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote: {log_path}')


if __name__ == '__main__':
    main()
