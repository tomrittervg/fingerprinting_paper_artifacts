#!/usr/bin/env python3
"""Generate a comparison cumulative experiment graph: Overall vs OS-average vs OS-weighted-average.

One subplot row per fingerprinter. Each row has three lines:
  1. Overall — the global pct_unique at each step
  2. OS Average — simple mean of per-OS pct_unique values
  3. OS Weighted Average — weighted mean using per-OS num_users as weights

Usage:
    ./gen_experiment_output_compare.py <output_dir>
"""

import csv
import json
import os
import sys
import argparse
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import config


def _read_csv(path):
    """Return (num_users, pct_unique) from a CSV, or None."""
    if not os.path.exists(path):
        return None
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return None
    num_users, _, pct, _ = rows[1][:4]
    return int(num_users), float(pct)


def _read_exp_csv(output_dir, slug, fp_name, os_suffix=''):
    return _read_csv(os.path.join(output_dir, f"{slug}{os_suffix}-{fp_name}.csv"))


def _load_manifest(output_dir):
    path = os.path.join(output_dir, 'experiment_manifest.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f).get('slug_map', {})


def _detect_os_values(output_dir):
    os_vals = set()
    for f in os.listdir(output_dir):
        m = re.search(r'_os_([A-Za-z]+)-[^/]+\.csv$', f)
        if m:
            os_vals.add(m.group(1))
    return sorted(os_vals)


def _load_overall_baselines(output_dir):
    """Load overall All-Data-{fp}.csv → {fp_name: ...}. Skip per-OS files."""
    os_prefixes = set()
    for fname in os.listdir(output_dir):
        m = re.match(r'All-Data-([A-Za-z]+)-[^-]+\.csv$', fname)
        if m:
            os_prefixes.add(m.group(1))

    baselines = {}
    for fname in os.listdir(output_dir):
        if not (fname.startswith('All-Data-') and fname.endswith('.csv')):
            continue
        fp_name = fname[len('All-Data-'):-len('.csv')]
        if any(fp_name.startswith(f"{p}-") for p in os_prefixes):
            continue
        baselines[fp_name] = True
    return sorted(baselines.keys())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", help="Analysis output directory")
    args = parser.parse_args()

    output_dir = args.output_dir
    config.OUTPUT_FOLDER = output_dir

    slug_map = _load_manifest(output_dir)
    if not slug_map:
        print("No experiment_manifest.json / slug_map found")
        return

    fp_order = _load_overall_baselines(output_dir)
    if not fp_order:
        print("No All-Data baselines found")
        return

    os_values = _detect_os_values(output_dir)
    if not os_values:
        print("No per-OS data found")
        return

    print(f"Fingerprinters: {fp_order}")
    print(f"OS values: {os_values}")

    # Build cumulative steps
    cumul_steps = []
    for key, slug in slug_map.items():
        if slug == 'C-P0-00-Baseline-Raw' or (slug.startswith('C-P') and '-C-' not in slug):
            parts = slug.split('-', 3)
            label = parts[3].replace('_', ' ') if len(parts) == 4 else slug
            cumul_steps.append((slug, label))

    if not cumul_steps:
        print("No cumulative steps found")
        return

    print(f"{len(cumul_steps)} cumulative steps")

    # Collect data: {fp_name: {slug: {overall, os_avg, os_wavg}}}
    fp_lines = {}  # {fp_name: {"Overall": {slug: pct}, "OS Average": {...}, "OS Weighted Avg": {...}}}
    for fp_name in fp_order:
        overall_data = {}
        os_avg_data = {}
        os_wavg_data = {}

        for slug, _ in cumul_steps:
            # Overall
            result = _read_exp_csv(output_dir, slug, fp_name)
            if result:
                overall_data[slug] = result[1]  # pct_unique

            # Per-OS
            os_pcts = []
            os_weighted = []
            total_weight = 0
            for os_val in os_values:
                os_result = _read_exp_csv(output_dir, slug, fp_name,
                                          os_suffix=f"_os_{os_val}")
                if os_result:
                    n_users, pct = os_result
                    os_pcts.append(pct)
                    os_weighted.append(pct * n_users)
                    total_weight += n_users

            if os_pcts:
                os_avg_data[slug] = sum(os_pcts) / len(os_pcts)
            if total_weight > 0:
                os_wavg_data[slug] = sum(os_weighted) / total_weight

        fp_lines[fp_name] = {
            "Overall": overall_data,
            "OS Average": os_avg_data,
            "OS Weighted Avg": os_wavg_data,
        }

    # Plot
    import warnings
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    line_order = ["Overall", "OS Average", "OS Weighted Avg"]
    x_labels = [label for _, label in cumul_steps]
    x_pos = list(range(len(cumul_steps)))
    n_fp = len(fp_order)

    title = "Cumulative Experiments — Overall vs OS Average vs OS Weighted Average"

    fig, axes = plt.subplots(n_fp, 1,
                             figsize=(max(12, len(cumul_steps) * 0.7), 5 * n_fp),
                             sharex=True)
    if n_fp == 1:
        axes = [axes]

    styles = {
        "Overall": dict(linewidth=2.5, marker='o', markersize=5),
        "OS Average": dict(linewidth=1.5, marker='s', markersize=4, linestyle='--'),
        "OS Weighted Avg": dict(linewidth=1.5, marker='^', markersize=4, linestyle='-.'),
    }

    for ax, fp_name in zip(axes, fp_order):
        for line_name in line_order:
            data = fp_lines[fp_name][line_name]
            y = [data.get(slug) for slug, _ in cumul_steps]
            xs = [x for x, v in zip(x_pos, y) if v is not None]
            ys = [v for v in y if v is not None]
            if xs:
                ax.plot(xs, ys, label=line_name, **styles[line_name])

        ax.set_ylabel("% Unique Users")
        ax.set_title(fp_name)
        ax.legend(fontsize='small')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))

    axes[-1].set_xticks(x_pos)
    axes[-1].set_xticklabels(x_labels, rotation=45, ha='right')
    axes[-1].set_xlabel("Cumulative Experiment Step")
    fig.suptitle(title, fontsize=14, y=1.0)
    fig.tight_layout()

    from graphing import safe_filename
    fname = f"{safe_filename(title)}.png"
    path = os.path.join(output_dir, fname)
    fig.savefig(path, format='png')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
