#!/usr/bin/env python3
"""Generate a bar chart showing individual experiment reduction in unique users
(FPJSv2 only, weighted average across OSes).

Usage:
    python3 04_graph.py --analyze-dir <path> [<more dirs>] \
                        --experiments-csv <path/to/experiments.csv> \
                        [--output-dir <path>] [--cohort]
"""

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent

# Load 01_build_csv.py as the module 'build_csv' (its file name starts with a
# digit, which is not a legal Python identifier, so we can't `import` directly).
_spec = importlib.util.spec_from_file_location('build_csv', HERE / '01_build_csv.py')
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules['build_csv'] = _mod

from build_csv import (
    load_slug_map, read_experiment_csv,
    INDIVIDUAL_CHAIN, PHASE_NAMES, FP_DISPLAY, OS_LIST,
)


PHASE_COLORS = {
    None: 'black',
    0: '#D32F2F',   # red
    1: '#1976D2',   # blue
    2: '#388E3C',   # green
    3: '#F57C00',   # orange
    4: '#7B1FA2',   # purple
}


def _shorten(name):
    return (name
        .replace("CPU Core Count (Expert Opinion)", "CPU Count (Expert)")
        .replace("CPU Core Count (Data Driven)", "CPU Count (Data)")
        .replace("Available Screen Resolution", "Avail Screen Res.")
        .replace("Software Rendered Canvas", "SW Canvas")
        .replace("Accept-Language", "Accept-Lang")
        .replace("WebGL Renderer String", "WebGL Renderer")
        .replace("Math Functions", "Math Funcs")
        .replace("Font Updates", "Font Upd.")
        .replace("WebGL Vendor", "WebGL Vendor & Renderer")
        .replace("Minor Version", "Patch Version")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--analyze-dir", required=True, nargs='+', metavar="DIR")
    parser.add_argument("--experiments-csv", required=True, metavar="PATH")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--cohort", action="store_true",
                        help="Add cohort scores (hatched bars on bar chart)")
    args = parser.parse_args()

    analyze_dirs = [Path(d).resolve() for d in args.analyze_dir]
    experiments_csv = Path(args.experiments_csv).resolve()
    out_dir = Path(args.output_dir).resolve() if args.output_dir else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    slug_map, equivalents = load_slug_map(experiments_csv)

    # ── Collect individual experiment data (FPJSv2 only) ──
    indiv_fp = 'FPJSv2_Realistic'
    baselines_pct = {}
    baselines_coh = {}
    os_user_counts = {}
    for os_name in OS_LIST:
        data = read_experiment_csv(analyze_dirs, "Baseline-Raw", indiv_fp, slug_map,
                                   os_name=os_name, equivalents=equivalents)
        baselines_pct[os_name] = data['pct_unique'] if data else 0
        baselines_coh[os_name] = data['cohort_fitness'] if data else 0
        os_user_counts[os_name] = data['num_users'] if data else 0

    # (display_name, weighted_pct_reduction, weighted_cohort_improvement)
    indiv_results = []
    for exp_name, phase, display, visible in INDIVIDUAL_CHAIN:
        if not visible:
            continue
        w_pct_sum = 0
        w_coh_sum = 0
        total_weight = 0
        for os_name in OS_LIST:
            data = read_experiment_csv(analyze_dirs, exp_name, indiv_fp, slug_map,
                                       os_name=os_name, equivalents=equivalents)
            weight = os_user_counts.get(os_name, 0)
            if data and weight > 0:
                if baselines_pct[os_name] > 0:
                    w_pct_sum += (baselines_pct[os_name] - data['pct_unique']) * weight
                w_coh_sum += (data['cohort_fitness'] - baselines_coh[os_name]) * weight
                total_weight += weight
        if total_weight > 0:
            indiv_results.append((display, w_pct_sum / total_weight, w_coh_sum / total_weight))

    indiv_phase_colors = []
    for exp_name, phase, display, visible in INDIVIDUAL_CHAIN:
        if visible:
            indiv_phase_colors.append(PHASE_COLORS.get(phase, 'black'))

    # ── Plot ──
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    names = [r[0] for r in indiv_results]
    pct_values = [r[1] for r in indiv_results]
    coh_values = [r[2] for r in indiv_results]

    short_names = [_shorten(n) for n in names]
    y_pos = np.arange(len(short_names))
    bar_colors = [indiv_phase_colors[i] if i < len(indiv_phase_colors) else 'steelblue'
                  for i in range(len(short_names))]

    fig, ax_bar = plt.subplots(figsize=(8, 6))

    bar_height = 0.4 if args.cohort else 0.8

    # Uniqueness reduction bars (top x-axis)
    ax_top = ax_bar.twiny() if args.cohort else ax_bar
    if args.cohort:
        ax_top.barh(y_pos - bar_height / 2, pct_values, height=bar_height,
                     color=bar_colors, edgecolor='white', alpha=0.8)
        ax_top.set_xlabel("Weighted Avg. Absolute Reduction in % Unique Users", fontsize=7)
        ax_top.xaxis.set_label_position('top')
        ax_top.xaxis.tick_top()
        ax_top.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}"))

        # Cohort improvement bars (bottom x-axis, hatched)
        # Scale to 1e7 for readability
        coh_scaled = [v * 1e7 for v in coh_values]
        ax_bar.barh(y_pos + bar_height / 2, coh_scaled, height=bar_height,
                     color=bar_colors, edgecolor='white', alpha=0.4, hatch='///')
        ax_bar.set_xlabel("Absolute Improvement in Simpson Index (\u00d710\u207b\u2077)", fontsize=7)
        ax_bar.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}"))
    else:
        ax_bar.barh(y_pos, pct_values, color=bar_colors, edgecolor='white', alpha=0.8)
        ax_bar.set_xlabel("Weighted Average Absolute Reduction in % of Unique Users", fontsize=8)
        ax_bar.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}"))

    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(short_names, fontsize=7)
    for tick_label, color in zip(ax_bar.get_yticklabels(), bar_colors):
        tick_label.set_color(color)
    ax_bar.invert_yaxis()
    ax_bar.set_title("Individual Protection Impact (Fingerprint Pro)", fontsize=10, fontweight='bold')
    ax_bar.grid(axis='x', alpha=0.3)

    fig.tight_layout()

    path = out_dir / "protections_individual.png"
    fig.savefig(path, format='png', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
