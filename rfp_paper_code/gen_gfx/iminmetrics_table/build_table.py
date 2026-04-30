#!/usr/bin/env python3
"""Build the iterative-incremental top-20 LaTeX table (Table 3).

Reads `iterative_minmetrics_*_os_<OS>.csv` files from the provided
directory and emits a LaTeX table matching the one in
`app:detailed_incremental_construction` of `fpp_paper.tex`.

Colour rule:
    Each metric appearing in any OS's top-K (default 5) is coloured.
    Its colour is determined by the *first* OS, in priority order
    Windows → macOS → Android → Linux, where it sits in the top-K.
    The same colour is applied wherever the metric appears in any
    of the four columns.

Usage:
    python3 build_table.py <dir> [--output table.tex]
                                 [--top-n 20] [--top-k 5]
                                 [--fingerprinter-display "Fingerprint Pro"]
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# OS priority order for colour assignment. The colour of a "shared" metric
# (top-K in more than one OS) is the colour of the FIRST OS in this list
# whose top-K contains it.
OS_ORDER = ['WINNT', 'Darwin', 'Android', 'Linux']
OS_LABEL = {'WINNT': 'Windows', 'Darwin': 'macOS',
            'Android': 'Android', 'Linux': 'Linux'}
OS_COLOR = {'WINNT': 'red', 'Darwin': 'darkgreen',
            'Android': 'blue', 'Linux': 'orange'}


def load_top(csv_path, n):
    """Return the first `n` metrics ordered by K from a minmetrics CSV."""
    rows = []
    with csv_path.open() as f:
        for r in csv.DictReader(f):
            rows.append((int(r['K']), r['MetricAdded']))
    rows.sort()
    return [m for _, m in rows[:n]]


def load_name_mapping(path):
    """Read a `metric = display name` mapping file. Missing file is fine.

    Lines starting with `#` and blank lines are ignored. Whitespace around
    the `=` is stripped. Returns {} when the file does not exist.
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


def discover(directory):
    """Find iterative_minmetrics_*_os_<OS>.csv per OS. Returns {os: Path}."""
    out = {}
    pattern = re.compile(r'^iterative_minmetrics_(.+?)_os_([A-Za-z]+)\.csv$')
    for f in sorted(directory.iterdir()):
        m = pattern.match(f.name)
        if not m:
            continue
        os_name = m.group(2)
        if os_name in OS_ORDER and os_name not in out:
            out[os_name] = f
    return out


def metric_color_map(per_os, top_k):
    """For each metric in any OS's top-K, return its assigned colour."""
    colored = {}
    for osn in OS_ORDER:
        if osn not in per_os:
            continue
        for m in per_os[osn][:top_k]:
            if m not in colored:
                colored[m] = OS_COLOR[osn]
    return colored


def latex_metric(name):
    return name.replace('_', r'\_')


def render(per_os, top_n, top_k, fingerprinter_display, name_mapping=None):
    colors = metric_color_map(per_os, top_k)
    name_mapping = name_mapping or {}

    def display(m):
        # Display label is the override if present, else the raw metric name.
        # Either way, escape underscores for LaTeX. Colour-key uses the raw
        # metric name; only the displayed text swaps.
        return latex_metric(name_mapping.get(m, m))

    def cell(rank, m):
        c = colors.get(m)
        if c:
            return f"{rank} & \\textcolor{{{c}}}{{{display(m)}}}"
        return f"{rank} & {display(m)}"

    def hdr(osn, last=False):
        align = 'c' if last else 'c|'
        return (f"\\multicolumn{{2}}{{{align}}}{{\\textsf{{\\textcolor"
                f"{{{OS_COLOR[osn]}}}{{{OS_LABEL[osn]}}}}}}}")

    out = []
    out.append(r"\definecolor{darkgreen}{rgb}{0.0, 0.5, 0.0}")
    out.append(r"\begin{table}[H]")
    out.append(r"\scriptsize")
    out.append(r"\centering")
    out.append(r"\begin{tabular}{r l | r l}")
    out.append(r"\Xhline{2\arrayrulewidth}")

    # Pair OSes: (Windows + macOS) on top, (Android + Linux) below.
    pairs = [(OS_ORDER[0], OS_ORDER[1]), (OS_ORDER[2], OS_ORDER[3])]

    for i, (left, right) in enumerate(pairs):
        out.append(f"{hdr(left)} & {hdr(right, last=True)} \\\\")
        out.append(r"\Xhline{2\arrayrulewidth}")
        for k in range(top_n):
            l_m = per_os[left][k]
            r_m = per_os[right][k]
            out.append(f"{cell(k + 1, l_m)} & {cell(k + 1, r_m)} \\\\")
        out.append(r"\Xhline{2\arrayrulewidth}")
        if i < len(pairs) - 1:
            out.append(r" & & & \\")
            out.append(r"\Xhline{2\arrayrulewidth}")

    out.append(r"\end{tabular}")
    out.append(
        r"\caption{Top " + str(top_n) + r" measurements by iterative "
        r"incremental fingerprint construction, per operating system, for "
        r"\textit{" + fingerprinter_display + r"}. Rank 1 contributes the "
        r"most uniquely identifying users on its own; each subsequent rank "
        r"contributes the most additional uniquely identifying users "
        r"beyond those already captured by all higher-ranked metrics. "
        r"Colors indicate shared top-" + str(top_k) + r" metrics: "
        r"\textcolor{red}{Windows}, \textcolor{blue}{Android}, "
        r"\textcolor{darkgreen}{macOS}, \textcolor{orange}{Linux}.}"
    )
    out.append(r"\label{tab:iterative_top20_by_os}")
    out.append(r"\end{table}")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory",
                        help="Directory with iterative_minmetrics_*_os_<OS>.csv")
    parser.add_argument("--output", default="table.tex",
                        help="LaTeX output path (default: ./table.tex)")
    parser.add_argument("--top-n", type=int, default=20,
                        help="Rows per OS column (default: 20)")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Top-K used for the colour-sharing rule "
                             "(default: 5)")
    parser.add_argument("--fingerprinter-display",
                        default="Fingerprint Pro",
                        help="Fingerprinter display name in the caption "
                             "(default: 'Fingerprint Pro')")
    parser.add_argument("--name-mapping",
                        default=str(Path.cwd() / "name_mapping.txt"),
                        help="Optional `metric = display name` file used to "
                             "relabel metrics in the table "
                             "(default: ./name_mapping.txt; silently skipped "
                             "if absent)")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        sys.exit(f"ERROR: not a directory: {directory}")

    files = discover(directory)
    missing = [osn for osn in OS_ORDER if osn not in files]
    if missing:
        sys.exit(f"ERROR: missing CSVs for OS(es): {missing}")

    per_os = {osn: load_top(p, args.top_n) for osn, p in files.items()}
    for osn, metrics in per_os.items():
        if len(metrics) < args.top_n:
            print(f"WARN: {osn} has only {len(metrics)} ranked metrics "
                  f"(< --top-n={args.top_n})", file=sys.stderr)

    mapping_path = Path(args.name_mapping)
    name_mapping = load_name_mapping(mapping_path)
    if name_mapping:
        print(f"Loaded {len(name_mapping)} display-name overrides from "
              f"{mapping_path}")

    # Append any metric that appears in the table but isn't in the mapping
    # yet, so the file becomes a complete editable list. Order matches the
    # table (Windows column top-down, then macOS, Android, Linux).
    seen_in_table = []
    for osn in OS_ORDER:
        for m in per_os.get(osn, []):
            if m not in seen_in_table:
                seen_in_table.append(m)
    new_entries = [m for m in seen_in_table if m not in name_mapping]
    if new_entries:
        file_existed = mapping_path.exists()
        with mapping_path.open("a", encoding="utf-8") as f:
            if not file_existed:
                f.write("# Display-name overrides for build_table.py\n")
                f.write("# Format: metric_name = display name\n")
                f.write("# Lines starting with `#` and blank lines are "
                        "ignored.\n\n")
            elif name_mapping:
                # Add a blank-line separator before the new block so the
                # file stays readable.
                f.write("\n")
            for m in new_entries:
                f.write(f"{m} = {m}\n")
                name_mapping[m] = m  # use raw name in this run's output
        print(f"Appended {len(new_entries)} new metric(s) to {mapping_path}")

    text = render(per_os, args.top_n, args.top_k,
                  args.fingerprinter_display, name_mapping)
    out_path = Path(args.output)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path.resolve()}")


if __name__ == "__main__":
    main()
