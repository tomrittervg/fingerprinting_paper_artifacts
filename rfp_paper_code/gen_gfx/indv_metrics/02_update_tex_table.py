#!/usr/bin/env python3
"""Update the Individual Metric Analysis table in fpp_paper.tex.

Reads metric_table.csv (produced by build_csv.py) and regenerates the LaTeX
table body in fpp_paper.tex in-place.

Usage:
    python3 update_tex_table.py [--csv PATH] [--tex PATH]

Defaults:
    --csv  <this script's directory>/metric_table.csv
    --tex  <rfp_paper repo root>/fpp_paper.tex
"""

import argparse
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
# Defaults are anchored to the current working directory so the script can be
# run from anywhere (typically the rfp_paper repo, which contains both
# metric_table.csv and fpp_paper.tex). Pass --csv / --tex to override.
DEFAULT_CSV = Path.cwd() / "metric_table.csv"
DEFAULT_TEX = Path.cwd() / "fpp_paper.tex"


def load_metric_table(path: Path):
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(dict(row))
    return rows


def escape_metric(name):
    return name.replace("_", r"\_")


def format_hhi(value):
    try:
        return f"{float(value):.10g}"
    except (ValueError, TypeError):
        return str(value)


def format_entropy(value):
    try:
        return f"{float(value):.10g}"
    except (ValueError, TypeError):
        return str(value)


def format_smr_uniqueness(value):
    if value in ("", None):
        return ""
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return str(value)


def format_smr_cohort(value):
    if value in ("", "n/a", None):
        return "n/a"
    try:
        s = f"{float(value):.17f}".rstrip("0").rstrip(".")
        return r"\multicolumn{1}{r}{" + s + "}"
    except (ValueError, TypeError):
        return str(value)


def build_row(row):
    m = escape_metric(row["Metric"])
    h = format_hhi(row.get("HHI Index", ""))
    e = format_entropy(row.get("Shannon Entropy", ""))
    u = format_smr_uniqueness(row.get("SMR Removal (Uniqueness)", ""))
    c = format_smr_cohort(row.get("SMR Removal (Cohort)", "n/a"))
    return f"{m} & {h} & {e} & {u} & {c} \\\\"


def build_table_body(rows):
    header = (
        r"\textbf{Metric} & "
        r"\multicolumn{1}{l}{\textbf{HHI Index}} & "
        r"\multicolumn{1}{l}{\textbf{Shannon Entropy}} & "
        r"\multicolumn{1}{l}{\textbf{SMR Removal (Uniqueness)}} & "
        r"\textbf{SMR Removal (Cohort)} \\"
    )
    return [header] + [build_row(r) for r in rows]


def update_tex_table(tex_path: Path, new_body_lines):
    content = tex_path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(Individual Metric Analysis\s*\n"
        r"\s*\\begin\{table\}\[.*?\]\s*\n"
        r"\s*\\tiny\s*\n"
        r"\s*\\begin\{tabular\}\{[^}]*\}\s*\n)"
        r".*?"
        r"(\\end\{tabular\}\s*\n"
        r"\s*\\end\{table\})",
        re.DOTALL,
    )

    body_text = "\n".join(new_body_lines) + "\n"
    new_content, count = re.subn(pattern, lambda m: m.group(1) + body_text + m.group(2), content)

    if count == 0:
        print("SKIP: Individual Metric Analysis table not found in .tex file (removed).",
              file=sys.stderr)
        return

    tex_path.write_text(new_content, encoding="utf-8")
    print(f"Updated table in {tex_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=str(DEFAULT_CSV),
                        help=f"Path to metric_table.csv (default: {DEFAULT_CSV})")
    parser.add_argument("--tex", default=str(DEFAULT_TEX),
                        help=f"Path to fpp_paper.tex (default: {DEFAULT_TEX})")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    tex_path = Path(args.tex)

    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run build_csv.py first.")
    if not tex_path.exists():
        sys.exit(f"ERROR: {tex_path} not found.")

    rows = load_metric_table(csv_path)

    # Sort by HHI ascending (lowest HHI = most diverse = most interesting first)
    rows.sort(key=lambda r: float(r["HHI Index"]) if r.get("HHI Index") else float("inf"))

    print(f"Loaded {len(rows)} metrics from {csv_path}")
    smr_count = sum(1 for r in rows if r.get("SMR Removal (Uniqueness)", "").strip())
    print(f"  {smr_count} metrics have SMR data")

    body_lines = build_table_body(rows)
    update_tex_table(tex_path, body_lines)
    print("Done.")


if __name__ == "__main__":
    main()
