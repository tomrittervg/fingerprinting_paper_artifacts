#!/usr/bin/env python3
"""Generate a 2x2 grid of cumulative-protection line charts.

Layout (clockwise from top-left):
  - Top-left:     Overall — population-weighted average across OSes, one
                  line per fingerprinter.
  - Top-right:    Fingerprint Pro,  one line per OS.
  - Bottom-right: Akamai,           one line per OS.
  - Bottom-left:  SignifyD,         one line per OS.

All four panels share a y-axis and use the same x-axis ordering of
cumulative protection-phase steps. With --cohort, each panel additionally
plots the Simpson Index on a secondary y-axis (dashed lines).

The Overall panel is a weighted mean of the per-OS % Unique values, with
weights equal to the per-OS total submission count from the Baseline-Raw
row (which is OS-population, not fingerprinter-specific).

Usage:
    python3 05_graph.py --analyze-dir <path> [<more dirs>] \
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
    CUMULATIVE_CHAIN, PHASE_NAMES, FP_DISPLAY, OS_LIST,
)


OS_DISPLAY = {"WINNT": "Windows", "Darwin": "macOS",
              "Android": "Android", "Linux": "Linux"}
OS_COLORS = {"WINNT": "green", "Darwin": "#1f77b4", "Android": "#ff7f0e", "Linux": "purple"}

# Fingerprinter display labels (override Signifyd → SignifyD) + colors for the
# Overall panel.
FP_LABEL_OVERRIDE = {
    'FPJSv2_Realistic':   'Fingerprint Pro',
    'AkamaiV2_Realistic': 'Akamai',
    'Signifyd_Realistic': 'SignifyD',
}
FP_OVERALL_COLORS = {
    'FPJSv2_Realistic':   '#D32F2F',  # red
    'AkamaiV2_Realistic': '#17becf',  # teal
    'Signifyd_Realistic': '#e377c2',  # magenta
}

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
                        help="Add cohort scores (dashed lines on line graphs, hatched bars on bar chart)")
    args = parser.parse_args()

    analyze_dirs = [Path(d).resolve() for d in args.analyze_dir]
    experiments_csv = Path(args.experiments_csv).resolve()
    out_dir = Path(args.output_dir).resolve() if args.output_dir else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    slug_map, equivalents = load_slug_map(experiments_csv)
    fp_names = list(FP_DISPLAY.keys())

    # ── Collect cumulative data per protection step ──
    visible_cum = [(exp_name, phase, display) for exp_name, phase, display, visible
                   in CUMULATIVE_CHAIN if visible and exp_name != "Baseline-Raw"]
    cum_labels = ["Baseline"] + [display for _, _, display in visible_cum]

    cum_pct = {}   # {fp: {os: [pct_unique, ...]}}
    cum_coh = {}   # {fp: {os: [cohort_fitness, ...]}}
    for fp in fp_names:
        cum_pct[fp] = {}
        cum_coh[fp] = {}
        for os_name in OS_LIST:
            data = read_experiment_csv(analyze_dirs, "Baseline-Raw", fp, slug_map,
                                       os_name=os_name, equivalents=equivalents)
            pcts = [data['pct_unique'] if data else None]
            cohs = [data['cohort_fitness'] if data else None]
            for exp_name, phase, display in visible_cum:
                data = read_experiment_csv(analyze_dirs, exp_name, fp, slug_map,
                                           os_name=os_name, equivalents=equivalents)
                pcts.append(data['pct_unique'] if data else None)
                cohs.append(data['cohort_fitness'] if data else None)
            cum_pct[fp][os_name] = pcts
            cum_coh[fp][os_name] = cohs

    # ── Compute Overall (weighted average across OSes) ──
    # Use any fingerprinter's baseline to get per-OS user counts; they reflect
    # the population, not the fingerprinter.
    os_weights = {os_name: 0 for os_name in OS_LIST}
    for os_name in OS_LIST:
        data = read_experiment_csv(analyze_dirs, "Baseline-Raw", 'FPJSv2_Realistic',
                                   slug_map, os_name=os_name, equivalents=equivalents)
        if data:
            os_weights[os_name] = data['num_users']

    cum_overall = {}   # {fp: [weighted-avg pct per phase index]}
    cum_overall_coh = {}
    for fp in fp_names:
        ov_pct, ov_coh = [], []
        for i in range(len(cum_labels)):
            sw_p = sw_c = tw = 0.0
            for os_name in OS_LIST:
                v = cum_pct[fp][os_name][i]
                c = cum_coh[fp][os_name][i]
                w = os_weights.get(os_name, 0)
                if v is not None and w > 0:
                    sw_p += v * w
                    if c is not None:
                        sw_c += c * w
                    tw += w
            ov_pct.append(sw_p / tw if tw > 0 else None)
            ov_coh.append(sw_c / tw if tw > 0 else None)
        cum_overall[fp] = ov_pct
        cum_overall_coh[fp] = ov_coh

    # Build phase color lists
    cum_phase_colors = ['black']
    for exp_name, phase, display, visible in CUMULATIVE_CHAIN:
        if visible and exp_name != "Baseline-Raw":
            cum_phase_colors.append(PHASE_COLORS.get(phase, 'black'))

    # ── Plot ──
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    x_labels = [_shorten(l) for l in cum_labels]
    x_pos = list(range(len(cum_labels)))

    fig, axes_grid = plt.subplots(2, 2, figsize=(14, 9), sharey=True)

    # Clockwise from top-left: Overall, Fingerprint Pro, Akamai, SignifyD.
    panel_map = {
        (0, 0): 'overall',
        (0, 1): 'FPJSv2_Realistic',
        (1, 1): 'AkamaiV2_Realistic',
        (1, 0): 'Signifyd_Realistic',
    }

    for (r, c), key in panel_map.items():
        ax = axes_grid[r][c]
        if key == 'overall':
            for fp in fp_names:
                ys = cum_overall[fp]
                xs = [x for x, v in zip(x_pos, ys) if v is not None]
                ys_clean = [v for v in ys if v is not None]
                if xs:
                    ax.plot(xs, ys_clean, marker='o', linewidth=2.2, markersize=5,
                            color=FP_OVERALL_COLORS[fp])
            ax.set_title('Overall (weighted avg across OSes)',
                         fontsize=11, fontweight='bold')

            if args.cohort:
                ax2 = ax.twinx()
                for fp in fp_names:
                    ys = cum_overall_coh[fp]
                    xs = [x for x, v in zip(x_pos, ys) if v is not None]
                    ys_clean = [v for v in ys if v is not None]
                    if xs:
                        ax2.plot(xs, ys_clean, linestyle='--', linewidth=1.5,
                                 marker='s', markersize=3,
                                 color=FP_OVERALL_COLORS[fp], alpha=0.6)
                ax2.set_ylabel("Simpson Index", fontsize=8, alpha=0.7)
                ax2.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))
        else:
            fp = key
            for os_name in OS_LIST:
                ys = cum_pct[fp][os_name]
                xs = [x for x, v in zip(x_pos, ys) if v is not None]
                ys_clean = [v for v in ys if v is not None]
                if xs:
                    ax.plot(xs, ys_clean, marker='o', linewidth=2, markersize=5,
                            color=OS_COLORS[os_name])
            ax.set_title(FP_LABEL_OVERRIDE.get(fp, FP_DISPLAY[fp]),
                         fontsize=11, fontweight='bold')

            if args.cohort:
                ax2 = ax.twinx()
                for os_name in OS_LIST:
                    ys = cum_coh[fp][os_name]
                    xs = [x for x, v in zip(x_pos, ys) if v is not None]
                    ys_clean = [v for v in ys if v is not None]
                    if xs:
                        ax2.plot(xs, ys_clean, linestyle='--', linewidth=1.5,
                                 marker='s', markersize=3,
                                 color=OS_COLORS[os_name], alpha=0.6)
                ax2.set_ylabel("Simpson Index", fontsize=8, alpha=0.7)
                ax2.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))

        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, rotation=30, ha='right', fontsize=7)
        for tick_label, color in zip(ax.get_xticklabels(), cum_phase_colors):
            tick_label.set_color(color)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.grid(axis='y', alpha=0.3)
        # Right-column panels: show y-axis tick labels
        if c == 1:
            ax.tick_params(axis='y', labelleft=True)

    fig.tight_layout()
    # Carve out room in the centre of the figure for a shared legend
    fig.subplots_adjust(wspace=0.3, hspace=0.38)

    # Legend ordering: 4 OSes first, then 3 fingerprinters with FPJSv2 last.
    # Use identical linewidth/markersize so the colour glyphs are the same
    # length in both legends.
    legend_fp_order = ['AkamaiV2_Realistic', 'Signifyd_Realistic', 'FPJSv2_Realistic']
    os_handles = [
        Line2D([], [], color=OS_COLORS[osn], linewidth=2, marker='o',
               markersize=5, label=OS_DISPLAY[osn])
        for osn in OS_LIST
    ]
    fp_handles = [
        Line2D([], [], color=FP_OVERALL_COLORS[fp], linewidth=2, marker='o',
               markersize=5, label=FP_LABEL_OVERRIDE.get(fp, FP_DISPLAY[fp]))
        for fp in legend_fp_order
    ]
    # Two separate legends sharing a left edge so the colour glyphs line up
    # vertically between the two groups. Anchor both at the same x with
    # loc='center left'.
    LEGEND_X = 0.46
    leg_os = fig.legend(handles=os_handles, loc='center left',
                        bbox_to_anchor=(LEGEND_X, 0.60), ncol=1, fontsize=9,
                        frameon=False)
    fig.add_artist(leg_os)
    fig.legend(handles=fp_handles, loc='center left',
               bbox_to_anchor=(LEGEND_X, 0.51), ncol=1, fontsize=9,
               frameon=False)

    path = out_dir / "protection_overview.png"
    fig.savefig(path, format='png', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
