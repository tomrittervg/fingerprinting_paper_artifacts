#!/usr/bin/env python3
"""
Read fingerprint_buckets.csv and per-OS variants, plot a grid:
  Columns: one per fingerprinter
  Rows: one per metric from the CSV
  Each panel: one line per OS/Overall
  x-axis: Total Users
"""

import csv
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OVERALL_PATH = HERE / "fingerprint_buckets.csv"
OUTPUT_IMG = HERE / "fingerprint_buckets_plot.png"

FP_DISPLAY_OVERRIDES = {
    "FPJSv2": "Fingerprint Pro",
    "AkamaiV2": "Akamai",
}


def parse_csv(path: Path):
    """Parse a CSV file, return list of dicts with numeric values."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        data = []
        for raw in reader:
            fingerprinter = raw["Fingerprinter"].strip()
            row = {"Fingerprinter": fingerprinter}
            for key in headers:
                if key == "Fingerprinter":
                    continue
                val = raw[key].strip()
                try:
                    row[key] = float(val)
                except (ValueError, TypeError):
                    row[key] = None
            # Derived: expected cohort sizes (N * HHI)
            total = row.get("TotalUsers")
            unique = row.get("UniqueUsers")
            hhi = row.get("HHI")
            hhi2 = row.get("HHI2")
            row["ExpCohortHHI"] = total * hhi if (total and hhi) else None
            if total is not None and unique is not None and hhi2 is not None:
                n_nonunique = total - unique
                row["ExpCohortHHI2"] = n_nonunique * hhi2 if n_nonunique > 0 else None
            else:
                row["ExpCohortHHI2"] = None
            data.append(row)
    return data


def discover_datasets(dirs):
    """Scan dirs for fingerprint_buckets*.csv files.
    Return list of (label, path) where label is 'Overall' or an OS name."""
    datasets = []
    for d in dirs:
        for p in sorted(Path(d).rglob("fingerprint_buckets*.csv")):
            stem = p.stem
            if "_os_" in stem:
                label = stem.split("_os_")[-1]
            else:
                label = "Overall"
            datasets.append((label, p))
    return datasets


LINE_STYLES = ["-", "--", ":", "-.", (0, (3, 1, 1, 1)), (0, (5, 2))]


def build_fp_display(fingerprinters):
    """Build display names: strip _Realistic unless it causes a collision."""
    stripped = {}
    for fp in fingerprinters:
        base = fp.replace("_Realistic", "")
        name = FP_DISPLAY_OVERRIDES.get(base, base)
        stripped[fp] = name
    # Check for collisions
    seen = defaultdict(list)
    for fp, name in stripped.items():
        seen[name].append(fp)
    result = {}
    for fp, name in stripped.items():
        if len(seen[name]) > 1:
            # Collision — keep original name
            result[fp] = FP_DISPLAY_OVERRIDES.get(fp, fp)
        else:
            result[fp] = name
    return result


def build_fp_linestyles(fingerprinters):
    """Assign a unique line style to each fingerprinter."""
    return {fp: LINE_STYLES[i % len(LINE_STYLES)] for i, fp in enumerate(fingerprinters)}


def plot_panel(ax, all_data, fingerprinters, os_labels, os_colors, fp_linestyle, metric, ylabel, log_scale=False, scale=1.0, show_legend=False, os_display=None, log_x=False, fp_display=None):
    """Plot one panel with all fingerprinters and OS datasets."""
    for fp in fingerprinters:
        linestyle = fp_linestyle.get(fp, "-")
        datasets_by_label = all_data[fp]

        for label, rows in sorted(datasets_by_label.items()):
            color = os_colors.get(label, "black")
            rows.sort(key=lambda r: r["TotalUsers"])

            pairs = [(r["TotalUsers"], r.get(metric)) for r in rows
                     if r.get(metric) is not None]
            if not pairs:
                continue
            x, y = zip(*pairs)
            if scale != 1.0:
                y = [v * scale for v in y]

            ax.plot(x, y, linewidth=1.5, linestyle=linestyle, color=color)

    if log_x:
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1e6:.1f}m' if x >= 1e6 else f'{x/1e3:.0f}k'))
    else:
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1e6:.0f}m'))
    if log_scale:
        ax.set_yscale("log")
    ax.set_xlim(left=-0.2e6, right=15e6)
    ax.grid(True, linestyle="--", alpha=0.35)

    if show_legend:
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch
        handles = []
        # Fingerprinter entries: black lines with different styles
        for fp in fingerprinters:
            display = fp_display.get(fp, fp) if fp_display else fp
            linestyle = fp_linestyle.get(fp, "-")
            handles.append(Line2D([0], [0], color="black", linewidth=1.5,
                                  linestyle=linestyle, label=display))
        # OS entries: colored patches
        for label in os_labels:
            color = os_colors[label]
            handles.append(Patch(facecolor=color, label=os_display(label) if os_display else label))
        ax.legend(handles=handles, fontsize=7, loc="upper right",
                  bbox_to_anchor=(1.0, 0.55))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate fingerprint bucket plots")
    parser.add_argument("dirs", nargs="+", metavar="DIR",
                        help="Directories to scan for fingerprint_buckets*.csv files")
    parser.add_argument("--log", action="store_true", help="Use log scale for x-axis")
    args = parser.parse_args()

    datasets = discover_datasets(args.dirs)

    # Parse all CSVs, organize by fingerprinter -> {label -> [rows]}
    all_data = {}
    for label, path in datasets:
        rows = parse_csv(path)
        for row in rows:
            fp = row["Fingerprinter"]
            if fp not in all_data:
                all_data[fp] = defaultdict(list)
            all_data[fp][label].append(row)

    fingerprinters = sorted(all_data.keys())
    fp_display = build_fp_display(fingerprinters)
    fp_linestyle = build_fp_linestyles(fingerprinters)

    # Build consistent OS color map
    OS_DISPLAY = {"Darwin": "macOS", "WINNT": "Windows"}
    OS_COLORS = {"WINNT": "green", "Linux": "purple", "Overall": "red"}
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    cycle_colors = [p["color"] for p in prop_cycle]
    os_labels_raw = sorted({label for fp_data in all_data.values() for label in fp_data})
    # Assign colors: use explicit overrides, then cycle for the rest
    color_idx = 0
    os_colors = {}
    for label in os_labels_raw:
        if label in OS_COLORS:
            os_colors[label] = OS_COLORS[label]
        else:
            # Skip green in the cycle since it's reserved for Windows
            while cycle_colors[color_idx % len(cycle_colors)] == "green":
                color_idx += 1
            os_colors[label] = cycle_colors[color_idx % len(cycle_colors)]
            color_idx += 1
    os_labels = os_labels_raw

    os_display = lambda label: OS_DISPLAY.get(label, label)

    # (csv_column, display_label, log_scale, scale_factor)
    metric_rows = [
        ("PctUnique", "Unique Users (%)",                      False, 1),
        # ("UserP50",   "P50 (median) cohort size (non-unique)", False, 1),
    ]
    n_rows = len(metric_rows)

    fig, axes = plt.subplots(n_rows, 1, figsize=(7, 4 * n_rows), squeeze=False)

    for row, (metric, ylabel, log_scale, scale) in enumerate(metric_rows):
        plot_panel(axes[row][0], all_data, fingerprinters, os_labels, os_colors,
                   fp_linestyle, metric, ylabel, log_scale=log_scale, scale=scale,
                   show_legend=(row == 0), os_display=os_display, log_x=args.log,
                   fp_display=fp_display)

    fig.tight_layout()
    fig.savefig(OUTPUT_IMG, dpi=150)
    print(f"Saved plot to: {OUTPUT_IMG.resolve()}")


if __name__ == "__main__":
    main()
