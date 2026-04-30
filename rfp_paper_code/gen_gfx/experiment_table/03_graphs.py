#!/usr/bin/env python3
"""Generate a 2x2 grid of per-OS graphs showing % unique decreasing cumulatively.

Each subplot shows one OS with phase endpoints (Baseline, Phase 0-3) on the x-axis
and one line per fingerprinter. Values match Table 4 but computed per-OS.

Usage:
    python3 03_graphs.py --analyze-dir <path> [<more dirs>] \
                         --experiments-csv <path/to/experiments.csv> \
                         [--output-dir <path>]
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
    CUMULATIVE_CHAIN, PHASE_NAMES, FP_DISPLAY, OS_LIST,
)


def _phase_endpoints():
    """Return [(display_label, experiment_key), ...] for Baseline + end of each visible phase."""
    endpoints = [("Baseline", "Baseline-Raw")]
    last_by_phase = {}
    for exp_name, phase, display, visible in CUMULATIVE_CHAIN:
        if phase is not None and visible:
            last_by_phase[phase] = exp_name
    for phase_num in sorted(last_by_phase):
        if phase_num > 4:
            continue
        endpoints.append((PHASE_NAMES[phase_num], last_by_phase[phase_num]))
    return endpoints


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--analyze-dir", required=True, nargs='+', metavar="DIR")
    parser.add_argument("--experiments-csv", required=True, metavar="PATH")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    analyze_dirs = [Path(d).resolve() for d in args.analyze_dir]
    experiments_csv = Path(args.experiments_csv).resolve()
    out_dir = Path(args.output_dir).resolve() if args.output_dir else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    slug_map, equivalents = load_slug_map(experiments_csv)
    fp_names = list(FP_DISPLAY.keys())
    endpoints = _phase_endpoints()

    # Collect data: {os: {fp: [pct_unique for each endpoint]}}
    os_data = {}
    # Collect both pct_unique and cohort_fitness per OS/fp/endpoint
    os_pct = {}
    os_cohort = {}
    for os_name in OS_LIST:
        os_pct[os_name] = {}
        os_cohort[os_name] = {}
        for fp in fp_names:
            pcts = []
            cohorts = []
            for label, exp_name in endpoints:
                data = read_experiment_csv(analyze_dirs, exp_name, fp, slug_map,
                                           os_name=os_name, equivalents=equivalents)
                pcts.append(data['pct_unique'] if data else None)
                cohorts.append(data['cohort_fitness'] if data else None)
            os_pct[os_name][fp] = pcts
            os_cohort[os_name][fp] = cohorts

    # Get user counts per OS from baseline data
    os_users = {}
    for os_name in OS_LIST:
        baseline_exp = endpoints[0][1]  # "Baseline-Raw"
        data = read_experiment_csv(analyze_dirs, baseline_exp, fp_names[0], slug_map,
                                   os_name=os_name, equivalents=equivalents)
        os_users[os_name] = data['num_users'] if data else 0

    # Plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    x_labels = [label for label, _ in endpoints]
    x_pos = list(range(len(endpoints)))

    # Color cycle: match fingerprinter colors across left/right axes
    fp_colors = {}
    color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, fp in enumerate(fp_names):
        fp_colors[fp] = color_cycle[i % len(color_cycle)]

    fig, axes_grid = plt.subplots(2, 2, figsize=(14, 8), sharey=False)
    axes = [axes_grid[0][0], axes_grid[0][1], axes_grid[1][0], axes_grid[1][1]]

    os_display = {"WINNT": "Windows", "Darwin": "macOS",
                  "Android": "Android", "Linux": "Linux"}

    for ax_idx, (ax, os_name) in enumerate(zip(axes, OS_LIST)):
        # Left axis: % unique (solid lines)
        for fp in fp_names:
            ys = os_pct[os_name][fp]
            xs = [x for x, v in zip(x_pos, ys) if v is not None]
            ys_clean = [v for v in ys if v is not None]
            if xs:
                ax.plot(xs, ys_clean, marker='o',
                        linewidth=2, markersize=6, color=fp_colors[fp])

        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, rotation=30, ha='right')
        ax.set_ylabel("% Unique Users")
        n_users = os_users.get(os_name, 0)
        n_m = n_users / 1_000_000
        n_str = f"{n_m:.1f}m" if n_m >= 1 else f".{int(n_m * 10)}m"
        ax.set_title(f"{os_display.get(os_name, os_name)} (n={n_str})")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.grid(axis='y', alpha=0.3)

        # Right axis: cohort score (dashed lines)
        ax2 = ax.twinx()
        for fp in fp_names:
            ys = os_cohort[os_name][fp]
            xs = [x for x, v in zip(x_pos, ys) if v is not None]
            ys_clean = [v for v in ys if v is not None]
            if xs:
                ax2.plot(xs, ys_clean, marker='s', linestyle='--',
                         linewidth=1.5, markersize=4, color=fp_colors[fp], alpha=0.7)

        ax2.set_ylabel("Cohort Fitness (HHI)")
        ax2.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))

        # Legend only on Android graph
        if os_name == 'Android':
            legend_handles = []
            for fp in fp_names:
                legend_handles.append(Patch(facecolor=fp_colors[fp],
                                            label=FP_DISPLAY.get(fp, fp)))
            legend_handles.append(Line2D([0], [0], color='black', linewidth=2,
                                         marker='o', markersize=5, label='% Unique'))
            legend_handles.append(Line2D([0], [0], color='black', linewidth=1.5,
                                         linestyle='--', marker='s', markersize=4,
                                         alpha=0.7, label='Cohort (HHI)'))
            ax.legend(handles=legend_handles, fontsize='small',
                      loc='upper left', bbox_to_anchor=(0.0, 0.75))

    fig.tight_layout()

    path = out_dir / "phase_endpoints_by_os.png"
    fig.savefig(path, format='png', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
