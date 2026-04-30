#!/usr/bin/env python3
"""Generate a small-multiples grid waterfall chart for min-set combo analysis.

2x2 grid (one subplot per OS), each showing grouped bars (new users by combo
size) + cumulative lines for each run (Top 5, Top 10, Top 20 metrics).
Right y-axis shows % of OS users.

With --os, outputs a single-panel chart for the specified OS only.

Usage:
    ./grid_waterfall.py --metadata-dir <shannon_dir> <top5_dir> <top10_dir> <top20_dir>
    ./grid_waterfall.py --metadata-dir <shannon_dir> --os WINNT <dirs...>

Example:
    ./grid_waterfall.py \
      --metadata-dir final-range/shannon_hhi_0408ish_1775623494 \
      final-range/minset_top5_0408ish_1775635705 \
      final-range/minset_top10_0408ish_1775636765 \
      final-range/minset_top20_0408ish_1775644463

    ./grid_waterfall.py --os Darwin \
      --metadata-dir final-range/shannon_hhi_0408ish_1775623494 \
      final-range/minset_top5_0408ish_1775635705 \
      final-range/minset_top10_0408ish_1775636765 \
      final-range/minset_top20_0408ish_1775644463
"""

import argparse
import csv
import os
import re
import sys
import time

os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from viz_minset_common import (
    _load_dedup_csv_from_path as load_dedup_csv,
    load_metadata_from_os_txt,
)

EMIT_CSV = False


def _write_csv(png_path, headers, rows):
    """Write a CSV file with the same base name as the PNG, if EMIT_CSV is set."""
    if not EMIT_CSV:
        return
    csv_path = png_path.rsplit('.png', 1)[0] + '.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"wrote {csv_path}")


def derive_label(dirname):
    """Extract 'topN' from a directory name."""
    m = re.search(r'(top\d+)', os.path.basename(os.path.abspath(dirname)))
    return m.group(1) if m else os.path.basename(dirname)


# ── Visualization ────────────────────────────────────────────────────────────

OS_DISPLAY = {'WINNT': 'Windows', 'Darwin': 'macOS',
              'Linux': 'Linux', 'Android': 'Android'}
OS_ORDER = ['Android', 'Darwin', 'Linux', 'WINNT']


def _draw_os_subplot(ax, os_name, run_labels, run_dedup, total_users):
    """Draw one OS panel: grouped bars + cumulative lines.

    Returns list of (os_name, label, combo_size, new_pct, cumul_pct) rows
    for CSV output.
    """
    colors = plt.cm.tab10.colors
    markers = ['o', 's', 'D', '^', 'v', 'P', 'X']
    csv_rows = []

    all_sizes = sorted({r['combo_size']
                        for label in run_labels if label in run_dedup
                        for r in run_dedup[label]})
    if not all_sizes:
        return csv_rows

    n_runs = len(run_labels)
    bar_width = 0.8 / n_runs

    for i, label in enumerate(run_labels):
        dedup = run_dedup.get(label, [])
        size_to_new = {r['combo_size']: r['new_users'] for r in dedup}
        size_to_cumul = {r['combo_size']: r['cumulative_total'] for r in dedup}

        if total_users:
            values = [100.0 * size_to_new.get(s, 0) / total_users
                      for s in all_sizes]
        else:
            values = [size_to_new.get(s, 0) for s in all_sizes]
        positions = [s + (i - n_runs / 2 + 0.5) * bar_width for s in all_sizes]
        ax.bar(positions, values, width=bar_width,
               color=colors[i % len(colors)], alpha=0.7, edgecolor='white')

        cumul_sizes = sorted(size_to_cumul.keys())
        cumul_positions = [s + (i - n_runs / 2 + 0.5) * bar_width
                           for s in cumul_sizes]
        if total_users:
            cumul_values = [100.0 * size_to_cumul[s] / total_users
                            for s in cumul_sizes]
        else:
            cumul_values = [size_to_cumul[s] for s in cumul_sizes]
        ax.plot(cumul_positions, cumul_values,
                marker=markers[i % len(markers)], color=colors[i % len(colors)],
                linewidth=2, markersize=6, zorder=3)

        # Collect CSV data
        for s in all_sizes:
            new_pct = 100.0 * size_to_new.get(s, 0) / total_users if total_users else size_to_new.get(s, 0)
            cumul_pct = 100.0 * size_to_cumul.get(s, 0) / total_users if total_users else size_to_cumul.get(s, 0)
            csv_rows.append((os_name, label, s, f'{new_pct:.2f}', f'{cumul_pct:.2f}'))

    ax.set_title(OS_DISPLAY.get(os_name, os_name), fontsize=12, fontweight='bold')
    ax.set_xticks(all_sizes)
    ax.set_xticklabels([str(s) for s in all_sizes])
    ax.set_xlabel('Combo Size')
    ax.set_ylabel('% of OS Users')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
    return csv_rows


def _compute_average_pct_dedup(run_labels, all_os_run_dedup, os_users,
                               weighted=False):
    """Compute average percentage across OSes for each run and combo size.

    If weighted=True, weights each OS's percentage by its share of total users.
    If weighted=False, simple (equal-weight) average across OSes.

    Returns {label: dedup_rows} where new_users and cumulative_total are
    stored as percentages (not raw counts), and a sentinel total_users=100
    so _draw_os_subplot renders them correctly.
    """
    total_all = sum(os_users.values()) if weighted else 0
    avg_dedup = {}
    for label in run_labels:
        # {combo_size: [(pct_new, pct_cumul, weight), ...]}
        size_entries = {}
        for os_name, run_dedup in all_os_run_dedup.items():
            dedup = run_dedup.get(label, [])
            total = os_users.get(os_name, 0)
            if not dedup or not total:
                continue
            w = total / total_all if weighted and total_all else 1.0
            for r in dedup:
                sz = r['combo_size']
                size_entries.setdefault(sz, []).append((
                    100.0 * r['new_users'] / total,
                    100.0 * r['cumulative_total'] / total,
                    w,
                ))

        if not size_entries:
            continue

        rows = []
        for sz in sorted(size_entries):
            entries = size_entries[sz]
            if weighted:
                w_sum = sum(w for _, _, w in entries)
                avg_new = sum(n * w for n, _, w in entries) / w_sum
                avg_cumul = sum(c * w for _, c, w in entries) / w_sum
            else:
                avg_new = sum(n for n, _, _ in entries) / len(entries)
                avg_cumul = sum(c for _, c, _ in entries) / len(entries)
            rows.append({
                'combo_size': sz,
                'new_users': avg_new,
                'cumulative_total': avg_cumul,
            })
        avg_dedup[label] = rows

    return avg_dedup


def generate_grid(dirs, metadata, output_path, filter_os=None):
    """Generate the grid waterfall chart."""
    os_users = metadata['os_users']
    filter_lower = filter_os.lower() if filter_os else ''
    is_average = filter_lower == 'average'
    is_weighted = filter_lower == 'weighted-average'

    # Always load all OSes (needed for average mode too)
    all_os_list = [n for n in OS_ORDER if n in os_users]

    # Load per-OS dedup data for each run
    run_labels = []
    # {os_name: {label: dedup_rows}}
    all_os_run_dedup = {n: {} for n in all_os_list}

    for d in dirs:
        label = derive_label(d)
        run_labels.append(label)
        for os_name in all_os_list:
            dedup = load_dedup_csv(
                os.path.join(d, f'min_set_combos_dedup_os_{os_name}.csv'))
            if dedup:
                all_os_run_dedup[os_name][label] = dedup

    # Filter to OSes that have data
    all_os_list = [n for n in all_os_list if all_os_run_dedup[n]]
    if not all_os_list:
        print("No per-OS dedup data found", file=sys.stderr)
        return

    colors = plt.cm.tab10.colors
    all_csv_rows = []

    if is_average or is_weighted:
        # Average across all OSes → single panel
        avg_dedup = _compute_average_pct_dedup(
            run_labels, all_os_run_dedup, os_users, weighted=is_weighted)
        fig, ax = plt.subplots(figsize=(10, 6))
        title = 'Weighted OS Average' if is_weighted else 'OS Average'
        # Pass total_users=100 since values are already percentages
        all_csv_rows.extend(_draw_os_subplot(
            ax, title, run_labels, avg_dedup, 100))
    elif filter_os:
        # Single OS panel
        if filter_os not in all_os_run_dedup:
            print(f"No data for OS '{filter_os}'", file=sys.stderr)
            return
        fig, ax = plt.subplots(figsize=(10, 6))
        all_csv_rows.extend(_draw_os_subplot(
            ax, filter_os, run_labels,
            all_os_run_dedup[filter_os],
            os_users.get(filter_os, 0)))
    else:
        # 2x2 grid
        os_list = all_os_list
        ncols = 2
        nrows = (len(os_list) + 1) // 2
        fig, axes = plt.subplots(nrows, ncols, figsize=(14, 5.5 * nrows))
        if nrows == 1:
            axes = [axes]
        axes_flat = [ax for row in axes
                     for ax in (row if hasattr(row, '__len__') else [row])]

        for idx, os_name in enumerate(os_list):
            all_csv_rows.extend(_draw_os_subplot(
                axes_flat[idx], os_name, run_labels,
                all_os_run_dedup[os_name],
                os_users.get(os_name, 0)))

        # Hide unused subplots
        for idx in range(len(os_list), len(axes_flat)):
            axes_flat[idx].set_visible(False)

    # Legend
    legend_handles = []
    for i, label in enumerate(run_labels):
        m = re.match(r'top(\d+)', label)
        nice = f'Top {m.group(1)} Metrics' if m else label
        legend_handles.append(Patch(color=colors[i % len(colors)], label=nice))
    fig.legend(handles=legend_handles, loc='upper center',
               ncol=len(run_labels), fontsize=10,
               bbox_to_anchor=(0.5, 1.02))

    if is_weighted:
        title_os = 'Weighted OS Average'
    elif is_average:
        title_os = 'OS Average'
    elif filter_os:
        title_os = OS_DISPLAY.get(filter_os, filter_os)
    else:
        title_os = 'All OSes'
    fig.suptitle(f'New Users by Combo Size \u2014 {title_os}',
                 fontsize=14, y=1.05)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"wrote {output_path}")
    _write_csv(output_path,
               ['OS', 'Run', 'ComboSize', 'NewUsersPct', 'CumulativePct'],
               all_csv_rows)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'dirs', nargs='+',
        help='Min-set output directories (e.g. minset_top5 minset_top10 ...)',
    )
    parser.add_argument(
        '--metadata-dir', required=True, metavar='DIR',
        help='Shannon/HHI output directory containing os.txt with per-OS user counts',
    )
    parser.add_argument(
        '--os', dest='filter_os', default=None,
        help='Output only this OS (e.g. WINNT, Darwin, Android, Linux, '
             'average, weighted-average)',
    )
    parser.add_argument(
        '-o', '--output', default=None,
        help='Output PNG path (default: minset_waterfall_grid.png or minset_waterfall_<os>.png in cwd)',
    )
    parser.add_argument(
        '--csv', action='store_true',
        help='Also output a .csv file alongside the .png with the graph data',
    )
    args = parser.parse_args()

    if args.csv:
        global EMIT_CSV
        EMIT_CSV = True

    metadata = load_metadata_from_os_txt(args.metadata_dir)
    print(f"metadata: {metadata['total_users']:,} total users, "
          f"{len(metadata['os_users'])} OSes")

    if args.filter_os and args.filter_os.lower() not in ('average', 'weighted-average') \
            and args.filter_os not in metadata['os_users']:
        print(f"ERROR: OS '{args.filter_os}' not found in os.txt "
              f"(available: {', '.join(sorted(metadata['os_users']))}, "
              f"average, weighted-average)",
              file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        name = f'minset_waterfall_{args.filter_os.lower()}' if args.filter_os else 'minset_waterfall_grid'
        output_path = os.path.join(os.getcwd(), f'{name}.png')

    generate_grid(args.dirs, metadata, output_path,
                  filter_os=args.filter_os)

    # Write provenance log
    log_path = os.path.join(os.path.dirname(output_path), 'run_grid_waterfall.log')
    write_run_log(log_path, args, metadata, output_path)


def write_run_log(log_path, args, metadata, output_path):
    lines = []
    lines.append('=' * 60)
    lines.append('grid_waterfall — Provenance Log')
    lines.append(f'Generated: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}')
    lines.append('=' * 60)
    lines.append('')
    lines.append('METADATA SOURCE')
    lines.append(f'  {args.metadata_dir}')
    lines.append(f'  Total users: {metadata["total_users"]:,}')
    for os_name in sorted(metadata['os_users']):
        lines.append(f'    {os_name:8s}  {metadata["os_users"][os_name]:>12,}')
    lines.append('')
    lines.append('DATA DIRECTORIES')
    for d in args.dirs:
        label = derive_label(d)
        lines.append(f'  {label:8s}  {d}')
    lines.append('')
    if args.filter_os:
        lines.append(f'FILTER OS: {args.filter_os}')
        lines.append('')
    lines.append('OUTPUT')
    lines.append(f'  {output_path}')
    lines.append('')

    with open(log_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote: {log_path}')


if __name__ == '__main__':
    main()
