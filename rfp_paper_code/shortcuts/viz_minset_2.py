#!/usr/bin/env python3
"""Show minset combo size transitions as an ASCII table.

Reads dedup CSVs from multiple minset_top{N} directories and shows how
coverage changes between two combo sizes, per OS.

Usage:
    ./shortcuts/viz_minset_2.py --start 1 --end 2 <minset_dir> [minset_dir ...]

Example:
    ./shortcuts/viz_minset_2.py --start 1 --end 2 \\
        final-range/minset_top5_smr_* final-range/minset_top10_smr_* \\
        final-range/minset_top20_smr_*
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from viz_minset_common import (
    discover_os_variants, parse_unique_baseline_from_txt,
    parse_total_users_from_txt, extract_top_n,
)

OS_DISPLAY = {"WINNT": "Windows", "Darwin": "macOS", "Android": "Android", "Linux": "Linux"}
OS_ORDER = ["WINNT", "Darwin", "Android", "Linux"]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=int, required=True, help="Starting combo size")
    parser.add_argument("--end", type=int, required=True, help="Ending combo size")
    parser.add_argument("dirs", nargs='+', help="Minset output directories")
    parser.add_argument("--metrics", metavar='N,N,...',
                        help='Only include top-N runs where N is in this list, e.g. "5,6,7,8"')
    args = parser.parse_args()

    metrics_filter = None
    if args.metrics:
        metrics_filter = {int(x.strip()) for x in args.metrics.split(',')}

    # Parse directories, extract top-N, group by top-N to merge split runs
    from collections import defaultdict
    top_n_dirs = defaultdict(list)  # {top_n: [path, ...]}
    for d in args.dirs:
        if not os.path.isdir(d):
            print(f"Warning: '{d}' is not a directory, skipping", file=sys.stderr)
            continue
        n = extract_top_n(d)
        if n is None:
            print(f"Warning: can't determine top-N from '{d}', skipping", file=sys.stderr)
            continue
        if metrics_filter and n not in metrics_filter:
            continue
        top_n_dirs[n].append(d)

    if not top_n_dirs:
        sys.exit("ERROR: no valid minset directories found")

    top_ns = sorted(top_n_dirs.keys())

    # Collect data: {os_name: {top_n: (start_pct, end_pct)}}
    os_data = {os_name: {} for os_name in OS_ORDER}
    os_total_users = {}  # {os_name: total_users} for weighting

    for top_n in top_ns:
        dirs = top_n_dirs[top_n]
        for os_name in OS_ORDER:
            # Merge dedup data from all dirs for this top-N
            merged_dedup = {}  # combo_size -> cumulative_total
            baseline = None
            for d in dirs:
                os_variants = discover_os_variants(d)
                if os_name not in os_variants:
                    continue
                _, dedup_rows = os_variants[os_name]
                for r in dedup_rows:
                    merged_dedup[r['combo_size']] = r['cumulative_total']
                # Get baselines from any dir that has the txt
                txt_path = os.path.join(d, f"min_set_combos_os_{os_name}.txt")
                if baseline is None:
                    baseline = parse_unique_baseline_from_txt(txt_path)
                if os_name not in os_total_users:
                    t = parse_total_users_from_txt(txt_path)
                    if t:
                        os_total_users[os_name] = t

            if not baseline or not merged_dedup:
                continue
            if args.start not in merged_dedup or args.end not in merged_dedup:
                continue

            start_pct = merged_dedup[args.start] / baseline * 100
            end_pct = merged_dedup[args.end] / baseline * 100
            os_data[os_name][top_n] = (start_pct, end_pct)

    # Build ASCII table
    header_width = 18
    col_width = 16
    narrow_width = 8

    print(f"\nCombo size {args.start} -> {args.end}")
    print(f"{'':>{header_width}}", end="")
    for n in top_ns:
        print(f" | {'N=' + str(n):^{col_width}}", end="")
    print(f" | {'AvgS':^{narrow_width}} | {'AvgE':^{narrow_width}} | {'Avg Increase':^{col_width}}")
    print("-" * (header_width + (col_width + 3) * len(top_ns) + (narrow_width + 3) * 2 + (col_width + 3)))

    # Compute rows with average increase for sorting
    row_data = []
    for os_name in OS_ORDER:
        display = OS_DISPLAY.get(os_name, os_name)
        label = f"{display} {args.start} -> {args.end}"

        cells = []
        starts = []
        increases = []

        for top_n in top_ns:
            entry = os_data[os_name].get(top_n)
            if entry:
                s, e = entry
                cells.append(f"{s:.1f}% -> {e:.1f}%")
                starts.append(s)
                increases.append(e - s)
            else:
                cells.append("-")

        if starts and sum(starts) > 0:
            avg_increase = sum(increases) / len(increases)
            avg_start = sum(starts) / len(starts)
            ends = [s + i for s, i in zip(starts, increases)]
            avg_end = sum(ends) / len(ends)
            avg_ratio = avg_increase / avg_start * 100
            avg_start_cell = f"{avg_start:.1f}%"
            avg_end_cell = f"{avg_end:.1f}%"
            avg_cell = f"+{avg_increase:.1f}pp ({avg_ratio:.0f}%)"
        else:
            avg_start_cell = "-"
            avg_end_cell = "-"
            avg_cell = "-"
            avg_ratio = 0

        row_data.append((avg_ratio, label, cells, avg_start_cell, avg_end_cell, avg_cell))

    # Sort by average increase (ascending)
    row_data.sort(key=lambda x: x[0])

    for _, label, cells, avg_start_cell, avg_end_cell, avg_cell in row_data:
        print(f"{label:>{header_width}}", end="")
        for cell in cells:
            print(f" | {cell:^{col_width}}", end="")
        print(f" | {avg_start_cell:^{narrow_width}} | {avg_end_cell:^{narrow_width}} | {avg_cell:^{col_width}}")

    # Weighted average row (weighted by total users per OS)
    w_starts_by_n = {n: [] for n in top_ns}  # (start, weight) pairs
    w_ends_by_n = {n: [] for n in top_ns}
    w_all_starts = []
    w_all_ends = []
    for os_name in OS_ORDER:
        weight = os_total_users.get(os_name, 0)
        if not weight:
            continue
        for top_n in top_ns:
            entry = os_data[os_name].get(top_n)
            if entry:
                s, e = entry
                w_starts_by_n[top_n].append((s, weight))
                w_ends_by_n[top_n].append((e, weight))
                w_all_starts.append((s, weight))
                w_all_ends.append((e, weight))

    def wavg(pairs):
        if not pairs:
            return None
        total_w = sum(w for _, w in pairs)
        return sum(v * w for v, w in pairs) / total_w if total_w else None

    print("-" * (header_width + (col_width + 3) * len(top_ns) + (narrow_width + 3) * 2 + (col_width + 3)))
    label = f"Weighted {args.start} -> {args.end}"
    w_cells = []
    for top_n in top_ns:
        ws = wavg(w_starts_by_n[top_n])
        we = wavg(w_ends_by_n[top_n])
        if ws is not None and we is not None:
            w_cells.append(f"{ws:.1f}% -> {we:.1f}%")
        else:
            w_cells.append("-")

    ws_all = wavg(w_all_starts)
    we_all = wavg(w_all_ends)
    if ws_all is not None and we_all is not None and ws_all > 0:
        w_inc = we_all - ws_all
        w_ratio = w_inc / ws_all * 100
        w_start_cell = f"{ws_all:.1f}%"
        w_end_cell = f"{we_all:.1f}%"
        w_inc_cell = f"+{w_inc:.1f}pp ({w_ratio:.0f}%)"
    else:
        w_start_cell = "-"
        w_end_cell = "-"
        w_inc_cell = "-"

    print(f"{label:>{header_width}}", end="")
    for cell in w_cells:
        print(f" | {cell:^{col_width}}", end="")
    print(f" | {w_start_cell:^{narrow_width}} | {w_end_cell:^{narrow_width}} | {w_inc_cell:^{col_width}}")

    # Delta row: show weighted increase per N= column
    label2 = ""
    d_cells = []
    for top_n in top_ns:
        ws = wavg(w_starts_by_n[top_n])
        we = wavg(w_ends_by_n[top_n])
        if ws is not None and we is not None and ws > 0:
            inc = we - ws
            ratio = inc / ws * 100
            d_cells.append(f"+{inc:.1f}pp ({ratio:.0f}%)")
        else:
            d_cells.append("-")
    print(f"{label2:>{header_width}}", end="")
    for cell in d_cells:
        print(f" | {cell:^{col_width}}", end="")
    print(f" | {'':^{narrow_width}} | {'':^{narrow_width}} | {'':^{col_width}}")


if __name__ == "__main__":
    main()
