#!/usr/bin/env python3
"""
Reads metric_table.csv (sibling file). SMR Removal (Uniqueness) is plotted on
its own x-axis ("% Unique Users No Longer Unique") after inversion
(max - value, so higher = more uniqueness protection benefit). The remaining
three columns (Simpson Index, Shannon Entropy, SMR Removal (Cohort)) are each
scaled to 0–100 relative to their column maximum and share a second x-axis
("Scaled Value"). For Simpson Index, each raw value is transformed as
(1 - value) before scaling. Only metrics with at least one SMR data point are
included. Metrics are sorted by SMR Removal (Uniqueness) value (largest at
top). Metrics below 20% in all columns are filtered out.

Usage:
    python3 make_graph_scatter.py [--csv PATH] [--output PATH]
"""

import argparse
import csv
from pathlib import Path
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DEFAULT_CONFIGS_DIR = HERE.parent.parent / "configs"
METRIC_MAPPING = DEFAULT_CONFIGS_DIR / "metadata_metric_name_mapping.txt"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def load_name_mapping(path: Path):
    """Read a `metric = display name` mapping file. Missing file is fine.

    Lines starting with `#` and blank lines are ignored. Whitespace around the
    `=` is stripped. Anything after `=` (including spaces) becomes the display
    label. Returns {} if the file does not exist.
    """
    if not path.exists():
        return {}
    mapping = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key:
            mapping[key] = value
    return mapping


def col_max(rows, col, transform=None):
    m = 0.0
    for r in rows:
        try:
            v = float((r.get(col) or "").strip())
            if transform:
                v = transform(v)
            if v > m:
                m = v
        except ValueError:
            continue
    return m


def scale_value(v, m):
    return (v / m) * 100.0 if m > 0 else 0.0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=str(Path.cwd() / "metric_table.csv"),
                        help="Path to metric_table.csv (default: ./metric_table.csv)")
    parser.add_argument("--output", default=str(Path.cwd() / "metric_scatter.png"),
                        help="Output image path (default: ./metric_scatter.png)")
    parser.add_argument("--configs-dir", default=str(DEFAULT_CONFIGS_DIR), metavar="DIR",
                        help="Path to fingerprinting-data configs/ directory")
    parser.add_argument("--name-mapping", default=str(Path.cwd() / "name_mapping.txt"),
                        help="Optional `metric = display name` file used to "
                             "relabel y-axis ticks (default: ./name_mapping.txt; "
                             "silently skipped if absent)")
    args = parser.parse_args()

    global METRIC_MAPPING
    METRIC_MAPPING = Path(args.configs_dir) / "metadata_metric_name_mapping.txt"

    csv_path = Path(args.csv)
    output_img = Path(args.output)
    name_mapping = load_name_mapping(Path(args.name_mapping))
    if name_mapping:
        print(f"Loaded {len(name_mapping)} display-name overrides from "
              f"{Path(args.name_mapping)}")

    headers, rows = read_csv(csv_path)

    metric_col = headers[0]
    value_cols = headers[1:5]  # four value columns
    simpson_col = value_cols[0]
    smr_uniq_col = "SMR Removal (Uniqueness)"
    smr_cohort_col = "SMR Removal (Cohort)"
    scaled_cols = [c for c in value_cols if c != smr_uniq_col]  # Simpson, Shannon, Cohort

    allowed = {
        line.split()[0]
        for line in METRIC_MAPPING.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    }
    rows = [r for r in rows if (r.get(metric_col) or "").strip() in allowed]

    # Exclude metrics that are removed from the fingerprinter model
    EXCLUDE_METRICS = {"screen_web_inner", "screen_web_outer"}
    rows = [r for r in rows if (r.get(metric_col) or "").strip() not in EXCLUDE_METRICS]

    # Filter to only metrics that have at least one SMR data point
    def has_smr(r):
        for col in (smr_uniq_col, smr_cohort_col):
            v = (r.get(col) or "").strip()
            if v and v != "n/a":
                return True
        return False

    rows = [r for r in rows if has_smr(r)]

    # Pre-compute column min/max for columns that need baseline subtraction
    def col_vals(rows, col):
        result = []
        for r in rows:
            try:
                result.append(float((r.get(col) or "").strip()))
            except ValueError:
                pass
        return result

    smr_uniq_vals = col_vals(rows, smr_uniq_col)
    smr_uniq_max = max(smr_uniq_vals) if smr_uniq_vals else 1.0

    # SMR Cohort: subtract baseline (min) so zero-contribution metrics score 0
    smr_cohort_vals = col_vals(rows, smr_cohort_col)
    smr_cohort_baseline = min(smr_cohort_vals) if smr_cohort_vals else 0.0

    # Compute maxima only for scaled columns (Simpson, Shannon, Cohort)
    maxima = {}
    for col in scaled_cols:
        if col == simpson_col:
            maxima[col] = col_max(rows, col, transform=lambda x: 1 - x)
        elif col == smr_cohort_col:
            maxima[col] = max(smr_cohort_vals) - smr_cohort_baseline if smr_cohort_vals else 1.0
        else:
            maxima[col] = col_max(rows, col)

    # SMR Uniqueness baseline = max(UniqueUsersWhenRemoved), i.e. the metric
    # whose removal has the least impact.  pct = (baseline - value) / baseline * 100
    smr_uniq_baseline = smr_uniq_max

    processed = []
    for r in rows:
        metric = (r.get(metric_col) or "").strip()
        entry = {"metric": metric}

        # SMR Uniqueness: % of unique users no longer unique when metric removed
        try:
            raw_uniq = float((r.get(smr_uniq_col) or "").strip())
        except ValueError:
            raw_uniq = smr_uniq_baseline
        entry["smr_uniq_pct"] = ((smr_uniq_baseline - raw_uniq) / smr_uniq_baseline * 100.0
                                  if smr_uniq_baseline > 0 else 0.0)

        # Scaled columns (0-100)
        for col in scaled_cols:
            try:
                raw = float((r.get(col) or "").strip())
            except ValueError:
                raw = 0.0
            if col == simpson_col:
                raw = 1 - raw
            elif col == smr_cohort_col:
                raw = max(0.0, raw - smr_cohort_baseline)
            entry[col] = scale_value(raw, maxima[col])
        processed.append(entry)

    processed = [e for e in processed
                 if e["smr_uniq_pct"] >= 0.5
                 or any(e[col] >= 65 for col in scaled_cols)]
    processed.sort(key=lambda e: e["smr_uniq_pct"], reverse=True)

    # ── Dual-axis scatter plot ───────────────────────────────────────────────
    n = len(processed)
    fig, ax = plt.subplots(figsize=(7, max(6, n * 0.3)))
    ax2 = ax.twiny()

    SMR_COLOR = "#E91E63"
    SCALED_COLORS = {
        simpson_col: "#2196F3",
        "Shannon Entropy": "#4CAF50",
        smr_cohort_col: "#FF9800",
    }

    y_positions = list(range(n))
    # Plot scaled columns on primary axis (bottom) — all on same y line
    for j, col in enumerate(scaled_cols):
        label = col
        color = SCALED_COLORS.get(col, f"C{j+1}")
        xj = [entry[col] for entry in processed]
        ax.scatter(xj, y_positions, label=label, s=22, color=color, marker="D",
                   alpha=0.75, zorder=3)

    # Plot SMR on secondary axis (top)
    for y, entry in zip(y_positions, processed):
        ax2.scatter(entry["smr_uniq_pct"], y, color=SMR_COLOR, s=28, zorder=3)

    # Primary axis (bottom) — Scaled Value
    ax.set_xlim(0, 105)
    ax.set_xlabel("Scaled Value (0–100)", fontsize=9, color="black")
    ax.tick_params(axis="x", labelsize=8, colors="black")
    ax.grid(True, axis="x", linestyle="--", alpha=0.25)

    # Secondary axis (top) — SMR
    smr_max = max(e["smr_uniq_pct"] for e in processed) if processed else 1.0
    ax2.set_xlim(0, smr_max * 1.1)
    ax2.set_xlabel("% Unique Users No Longer Unique (SMR - FPJS)", fontsize=9,
                   color="black")
    ax2.tick_params(axis="x", colors="black", labelsize=8)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    # Y-axis
    ax.set_yticks(y_positions)
    ax.set_yticklabels([name_mapping.get(entry["metric"], entry["metric"])
                        for entry in processed])
    ax.invert_yaxis()

    # Combined legend
    import matplotlib.lines as mlines
    smr_handle = mlines.Line2D([0], [0], color=SMR_COLOR, marker="o",
                                markersize=5, linewidth=1.2,
                                label="SMR (% unique lost)")
    handles = [smr_handle] + ax.get_legend_handles_labels()[0]
    labels = ["SMR (% unique lost)"] + ax.get_legend_handles_labels()[1]
    ax.legend(handles, labels, fontsize=7, loc="lower right")

    fig.tight_layout()
    fig.savefig(output_img, dpi=150, bbox_inches="tight")
    print(f"Saved plot to: {output_img.resolve()}")


if __name__ == "__main__":
    main()
