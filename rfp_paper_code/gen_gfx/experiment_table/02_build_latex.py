#!/usr/bin/env python3
"""Generate LaTeX table bodies for paper Tables 1, 3, and 4 from CSVs.

Usage:
    python3 build_latex.py [--csv-dir PATH] [--tex PATH]

Reads table1_baseline.csv and table3_experiments.csv (produced by
build_csv.py) and updates the corresponding tables in fpp_paper.tex
in-place.

This script does NO math — all values come directly from the CSVs.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent  # artifacts/experiment_table → artifacts → rfp_paper
DEFAULT_TEX = REPO_ROOT / "fpp_paper.tex"


# ── CSV reading ──────────────────────────────────────────────────────────────

def read_csv_rows(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# ── Table 1: Per-OS baseline uniqueness ──────────────────────────────────────

OS_ORDER = [
    ("WINNT",   "Windows"),
    ("Darwin",  "macOS"),
    ("Android", "Android"),
    ("Linux",   "Linux"),
]

# Display-name overrides applied to the Technique column when emitting
# LaTeX. Source CSVs and `01_build_csv.py` keep the original names.
TECHNIQUE_DISPLAY = {
    "Minor Version": "Patch Version",
    "CPU Core Count (Expert Opinion)": "CPU Count (Expert)",
    "CPU Core Count (Data Driven)": "CPU Count (Data)",
    "Available Screen Resolution": "Available Screen Res.",
}


def _display_technique(name):
    return TECHNIQUE_DISPLAY.get(name, name)


def _fmt_delta(val):
    """Format a cohort delta value. 0 → '---', otherwise signed percentage."""
    if val == '' or val is None:
        return '---'
    v = float(val)
    if v == 0:
        return '---'
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:,.0f}\\%"


def build_table1_latex(rows):
    """Generate LaTeX rows for Table 1 (tab:fingerprinters) from CSV rows.

    CSV columns: Fingerprinter, {OS}_PctUnique, {OS}_CohortScore, {OS}_CohortDelta
    Returns (lines, col_spec).

    Two columns per OS: % Uniq, Sim ($\\times 10^{-7}$), plus a final
    Weighted Avg. column (% Uniq only, weighted by user count across OSes).

    Matches the paper's manual formatting: r-aligned columns, vertical lines
    via \\multicolumn, \\hspace for column widths on Fingerprint Pro row.
    """
    n_os = len(OS_ORDER)
    # col_spec has no vertical lines — they come from \multicolumn in headers
    col_spec = "l r r r r  r r  r r  r"

    lines = []
    lines.append("\\Xhline{2\\arrayrulewidth}")

    # OS header row — include user count from first data row
    # First OS gets |c|, rest get c|; each on its own line with leading &
    first_row = rows[0] if rows else {}
    os_header_lines = []
    for idx, (os_key, display) in enumerate(OS_ORDER):
        num_users = first_row.get(f'{os_key}_NumUsers', '')
        if num_users != '' and num_users is not None:
            n = float(num_users)
            if n >= 1_000_000:
                count_str = f"{n/1_000_000:.1f}m"
            elif n >= 1_000:
                count_str = f"{n/1_000:.0f}k"
            else:
                count_str = f"{n:.0f}"
            label = f"{display} ({count_str})"
        else:
            label = display
        if idx == 0:
            col_fmt = "|c|"
        else:
            col_fmt = "c|"
        part = f"\\multicolumn{{2}}{{{col_fmt}}}{{\\textsf{{{label}}}}}"
        if idx == 0:
            os_header_lines.append(f" & {part} ")
        else:
            os_header_lines.append(f" & {part} ")
    os_header_lines.append(" & \\textsf{Weighted Avg.} \\\\")
    lines.append("\n".join(os_header_lines))
    lines.append("")

    # Sub-header row — r-aligned with vertical lines via \multicolumn
    # All OS Sim columns get trailing |; each pair on its own line
    sub_lines = []
    for idx in range(n_os):
        if idx == 0:
            part = ("\\multicolumn{1}{|r}{\\textbf{\\% Uniq}} & "
                    "\\multicolumn{1}{r|}{\\textbf{Sim ($\\times 10^{-7}$)}} ")
            sub_lines.append(f"\\textbf{{Service}} \n& {part}")
        else:
            part = ("\\multicolumn{1}{r}{\\textbf{\\%}} & "
                    "\\multicolumn{1}{r|}{\\textbf{Sim}} ")
            sub_lines.append(f"& {part}")
    sub_lines.append("& \\textbf{\\%} \\\\")
    lines.append("\n".join(sub_lines))
    lines.append("")

    row_idx = 0
    for r in rows:
        name = r['Fingerprinter']
        # Collect per-OS cells and data for weighted average
        os_cell_lines = []
        weighted_sum = 0.0
        total_users = 0.0
        for idx, (os_key, _) in enumerate(OS_ORDER):
            pct = r.get(f'{os_key}_PctUnique', '')
            cohort_score = r.get(f'{os_key}_CohortScore', '')
            num_users = r.get(f'{os_key}_NumUsers', '')
            # All OS pct cells get \hspace for column width (Fingerprint Pro row only)
            hspace = "\\hspace{0.2cm} " if name == "Fingerprint Pro" else ""
            if pct != '' and pct is not None:
                pct_val = float(pct)
                pct_str = f"{hspace}{pct_val:.1f}\\%"
                if num_users != '' and num_users is not None:
                    n = float(num_users)
                    weighted_sum += pct_val * n
                    total_users += n
            else:
                pct_str = f"{hspace}---"
            if cohort_score != '' and cohort_score is not None:
                scaled = float(cohort_score) * 1e7
                sim_str = f"{scaled:.2f}"
            else:
                sim_str = "---"
            os_cell_lines.append(f"& {pct_str} & {sim_str} ")
        # Weighted average column
        if total_users > 0:
            wavg = weighted_sum / total_users
            wavg_str = f"{wavg:.1f}\\%"
        else:
            wavg_str = "---"
        os_cell_lines.append(f"& {wavg_str} \\\\")

        if row_idx % 2 == 0:
            lines.append("\\rowcolor{gray!25}")
        # Extra hspace on Fingerprint Pro to widen the name column
        name_tex = f"\\textit{{{name} \\hspace{{1.5cm}}}}" if name == "Fingerprint Pro" else f"\\textit{{{name}}}"
        lines.append(f"{name_tex} \n" + "\n".join(os_cell_lines))
        lines.append("")
        row_idx += 1

    lines.append("\\Xhline{2\\arrayrulewidth}")
    return lines, col_spec


# ── Table 3: Experiment improvements ─────────────────────────────────────────

PHASE_HEADERS = {
    "Phase 0": "FPT Phase 0 (Pre-2023 - Expert Opinion and Best Effort)",
    "Phase 1": "FPT Phase 1 (2023-2024 - Expert Opinion and Best Effort)",
    "Phase 2": "FPT Phase 2 (2025 - Data-Driven Analysis)",
    "Phase 3": "FPT Phase 3 (2025-2026 - Data-Driven Analysis)",
    "Phase 4": "FPT Phase 4 (2026 and Beyond - Data-Driven Analysis)",
    "Phase 5": "FPT Phase 5 (Future)",
}


def _fmt_pct(val, decimals=1):
    """Format a percentage value for the table."""
    if val == '' or val is None:
        return '-'
    v = float(val)
    return f"{v:.{decimals}f}\\%"


def _fmt_delta_pp(val, decimals=1):
    """Format a delta value as plain percentage points (no \\% suffix)."""
    if val == '' or val is None:
        return '-'
    v = float(val)
    return f"{v:.{decimals}f}"


def _fmt_ratio(val):
    """Format a cohort improvement ratio."""
    if val == '' or val is None:
        return '-'
    v = float(val)
    return f"{v:.1f}$\\times$"


def _build_per_os_experiment_latex(rows, has_baseline=True):
    """Generate LaTeX rows for a per-OS experiment table.

    3 columns per OS: % Unique, Uniq Δ, Cohort ×
    Used by both Table 3 (cumulative) and Table 5 (individual).
    """
    n_os = len(OS_ORDER)
    n_data_cols = 3 * n_os
    total_cols = 1 + n_data_cols  # technique + data
    col_spec = "l" + " | r r r" * n_os

    lines = []
    lines.append("\\Xhline{2\\arrayrulewidth}")

    # OS header row — last OS has no trailing |
    os_header_parts = []
    for idx, (os_key, display) in enumerate(OS_ORDER):
        sep = "c|" if idx < n_os - 1 else "c"
        os_header_parts.append(f"\\multicolumn{{3}}{{{sep}}}{{\\textsf{{{display}}}}}")
    lines.append(f" & {' & '.join(os_header_parts)} \\\\")

    # Sub-header row — full labels for first OS, compact for rest;
    # last OS has no trailing |
    sub_parts = []
    for idx in range(n_os):
        sim_sep = "c|" if idx < n_os - 1 else "c"
        if idx == 0:
            sub_parts.append(
                "\\multicolumn{1}{c}{\\textbf{\\% Uniq}} & "
                "\\multicolumn{1}{c}{\\textbf{Uniq $\\Delta$}} & "
                f"\\multicolumn{{1}}{{{sim_sep}}}{{\\textbf{{Sim ({{\\tiny $\\times 10^{{-7}}$}})}}}}")
        else:
            sub_parts.append(
                "\\multicolumn{1}{c}{\\textbf{\\%}} & "
                "\\multicolumn{1}{c}{\\textbf{$\\Delta$}} & "
                f"\\multicolumn{{1}}{{{sim_sep}}}{{\\textbf{{Sim}}}}")
    lines.append(f"\\textbf{{Technique}} & {' & '.join(sub_parts)} \\\\")
    current_phase = None
    phase_data_idx = 0

    for r in rows:
        phase = r['Phase']
        technique = _display_technique(r['Technique'])

        # Phase separator
        if phase and phase != current_phase:
            current_phase = phase
            header_text = PHASE_HEADERS.get(phase, phase)
            lines.append(f" %--------- {phase}")
            lines.append("  \\rowcolor{black}")
            lines.append(
                f" \\multicolumn{{{total_cols}}}{{c}}{{\\color{{white}} "
                f"\\colorbox{{black}}{{ \\textsf{{{header_text}}}}}}}\\\\")
            phase_data_idx = 0

        # Data cells per OS
        cells = []
        for os_key, _ in OS_ORDER:
            pct = r.get(f'{os_key}_PctUnique', '')
            uniq_impr = r.get(f'{os_key}_UniqImpr', '')
            cohort_score = r.get(f'{os_key}_CohortScore', '')

            cells.append(_fmt_pct(pct))
            if has_baseline and technique == 'Baseline':
                cells.append('-')
            else:
                cells.append(_fmt_delta_pp(uniq_impr))
            if cohort_score != '' and cohort_score is not None:
                scaled = float(cohort_score) * 1e7
                cells.append(f"{scaled:.2f}")
            else:
                cells.append('-')

        if phase_data_idx % 2 == 0:
            lines.append("\\rowcolor{gray!25}")
        lines.append(f"  {technique} & {' & '.join(cells)} \\\\")
        phase_data_idx += 1

    lines.append("\\Xhline{2\\arrayrulewidth}")
    return lines, col_spec


def build_table3_latex(rows):
    """Table 3: cumulative experiments (has Baseline row)."""
    return _build_per_os_experiment_latex(rows, has_baseline=True)


def build_table5_latex(rows):
    """Table 5: individual experiments (with Baseline row)."""
    return _build_per_os_experiment_latex(rows, has_baseline=True)


# ── Overall (weighted average) tables ──────────────────────────────────────

OVERALL_PHASE_HEADERS = {
    "Phase 0": "FPT Phase 0 (Pre-2023)",
    "Phase 1": "FPT Phase 1 (2023-2024)",
    "Phase 2": "FPT Phase 2 (2025)",
    "Phase 3": "FPT Phase 3 (2025-2026)",
    "Phase 4": "FPT Phase 4 (2026 and Beyond)",
    "Phase 5": "FPT Phase 5 (Future)",
}


def _build_overall_latex(rows):
    """Generate LaTeX rows for an Overall (weighted average) table.

    Compact format: 3 data columns (% Uniq, Uniq Δ, Sim).
    """
    lines = []
    lines.append("\\Xhline{2\\arrayrulewidth}")
    lines.append(
        "\\textbf{Technique} & \\textbf{\\% Uniq} & \\textbf{Uniq $\\Delta$} "
        "& \\textbf{Sim ({\\tiny $\\times 10^{-7}$})} \\\\")

    current_phase = None
    phase_data_idx = 0

    for r in rows:
        phase = r['Phase']
        technique = _display_technique(r['Technique'])

        if phase and phase != current_phase:
            current_phase = phase
            header_text = OVERALL_PHASE_HEADERS.get(phase, phase)
            lines.append("  \\rowcolor{black}")
            lines.append(
                f" \\multicolumn{{4}}{{c}}{{\\color{{white}} "
                f"\\colorbox{{black}}{{ \\textsf{{{header_text}}}}}}}\\\\")
            phase_data_idx = 0

        pct = r.get('PctUnique', '')
        uniq_impr = r.get('UniqImpr', '')
        cohort_score = r.get('CohortScore', '')

        pct_str = _fmt_pct(pct) if pct != '' else '-'
        delta_str = '-' if uniq_impr == '' or uniq_impr is None else _fmt_delta_pp(uniq_impr)
        if cohort_score != '' and cohort_score is not None:
            sim_str = f"{float(cohort_score) * 1e7:.2f}"
        else:
            sim_str = '-'

        if phase_data_idx % 2 == 0:
            lines.append("\\rowcolor{gray!25}")
        lines.append(f"  {technique} & {pct_str} & {delta_str} & {sim_str} \\\\")
        phase_data_idx += 1

    lines.append("\\Xhline{2\\arrayrulewidth}")
    return lines


def build_overall_cumulative_latex(rows):
    return _build_overall_latex(rows)


def build_overall_individual_latex(rows):
    return _build_overall_latex(rows)


# ── Table replacement in .tex ────────────────────────────────────────────────

def replace_table_body(content, label, new_body_lines, col_spec=None):
    """Replace the table body for a given label in the .tex content.

    Finds the \\begin{table} ... \\end{table} environment containing
    \\label{<label>}, then replaces the tabular body within it.
    If col_spec is provided, also replaces the \\begin{tabular}{...} column spec.
    """
    label_pattern = re.escape(label)

    label_match = re.search(r'\\label\{' + label_pattern + r'\}', content)
    if not label_match:
        print(f"WARNING: Could not find \\label{{{label}}} in tex file", file=sys.stderr)
        return content

    label_pos = label_match.start()

    env_start = content.rfind('\\begin{table', 0, label_pos)
    if env_start == -1:
        print(f"WARNING: Could not find \\begin{{table}} before \\label{{{label}}}", file=sys.stderr)
        return content

    is_star = content[env_start:env_start+20].startswith('\\begin{table*}')
    end_tag = '\\end{table*}' if is_star else '\\end{table}'
    env_end = content.find(end_tag, label_pos)
    if env_end == -1:
        print(f"WARNING: Could not find {end_tag} after \\label{{{label}}}", file=sys.stderr)
        return content
    env_end += len(end_tag)

    env_content = content[env_start:env_end]
    # Match tabular spec — use greedy match up to the closing } followed by
    # whitespace+newline, handling nested braces like @{\,}
    tabular_re = re.compile(
        r'(\\begin\{tabular\}\{)((?:[^{}]|\{[^{}]*\})*)(}\s*\n)'
        r'(.*?)'
        r'(\\end\{tabular\})',
        re.DOTALL
    )
    m = tabular_re.search(env_content)
    if not m:
        print(f"WARNING: Could not find tabular in table environment for \\label{{{label}}}", file=sys.stderr)
        return content

    body_text = "\n".join(new_body_lines) + "\n"

    if col_spec:
        abs_spec_start = env_start + m.start(2)
        abs_spec_end = env_start + m.end(2)
        abs_body_start = env_start + m.start(4)
        abs_body_end = env_start + m.end(4)
        new_content = (content[:abs_spec_start] + col_spec + content[abs_spec_end:abs_body_start]
                       + body_text + content[abs_body_end:])
    else:
        abs_body_start = env_start + m.start(4)
        abs_body_end = env_start + m.end(4)
        new_content = content[:abs_body_start] + body_text + content[abs_body_end:]

    return new_content


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-dir", default=str(HERE),
                        help="Directory containing table CSVs (default: script dir)")
    parser.add_argument("--tex", default=str(DEFAULT_TEX),
                        help=f"Path to fpp_paper.tex (default: {DEFAULT_TEX})")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    tex_path = Path(args.tex)

    if not tex_path.exists():
        sys.exit(f"ERROR: {tex_path} not found")

    content = tex_path.read_text(encoding='utf-8')
    updated = False

    # ── Table 1 ──
    t1_path = csv_dir / 'table1_baseline.csv'
    if t1_path.exists():
        t1_rows = read_csv_rows(t1_path)
        t1_lines, t1_col_spec = build_table1_latex(t1_rows)
        new_content = replace_table_body(content, 'tab:fingerprinters', t1_lines, col_spec=t1_col_spec)
        if new_content != content:
            content = new_content
            updated = True
            print(f"Updated Table 1 (tab:fingerprinters) from {t1_path}")
    else:
        print(f"Skipping Table 1: {t1_path} not found")

    # ── Table 3 ──
    t3_path = csv_dir / 'table3_experiments.csv'
    if t3_path.exists():
        t3_rows = read_csv_rows(t3_path)
        t3_lines, t3_col_spec = build_table3_latex(t3_rows)
        new_content = replace_table_body(content, 'tab:improvements', t3_lines, col_spec=t3_col_spec)
        if new_content != content:
            content = new_content
            updated = True
            print(f"Updated Table 3 (tab:improvements) from {t3_path}")
    else:
        print(f"Skipping Table 3: {t3_path} not found")

    # ── Table 5 ──
    t5_path = csv_dir / 'table5_individual.csv'
    if t5_path.exists():
        t5_rows = read_csv_rows(t5_path)
        t5_lines, t5_col_spec = build_table5_latex(t5_rows)
        new_content = replace_table_body(content, 'tab:individual', t5_lines, col_spec=t5_col_spec)
        if new_content != content:
            content = new_content
            updated = True
            print(f"Updated Table 5 (tab:individual) from {t5_path}")
    else:
        print(f"Skipping Table 5: {t5_path} not found")

    # ── Overall cumulative ──
    t3o_path = csv_dir / 'table3_overall.csv'
    if t3o_path.exists():
        t3o_rows = read_csv_rows(t3o_path)
        t3o_lines = build_overall_cumulative_latex(t3o_rows)
        new_content = replace_table_body(content, 'tab:improvements_overall', t3o_lines)
        if new_content != content:
            content = new_content
            updated = True
            print(f"Updated Overall cumulative (tab:improvements_overall) from {t3o_path}")
    else:
        print(f"Skipping Overall cumulative: {t3o_path} not found")

    # ── Overall individual ──
    t5o_path = csv_dir / 'table5_overall.csv'
    if t5o_path.exists():
        t5o_rows = read_csv_rows(t5o_path)
        t5o_lines = build_overall_individual_latex(t5o_rows)
        new_content = replace_table_body(content, 'tab:individual_overall', t5o_lines)
        if new_content != content:
            content = new_content
            updated = True
            print(f"Updated Overall individual (tab:individual_overall) from {t5o_path}")
    else:
        print(f"Skipping Overall individual: {t5o_path} not found")

    if updated:
        tex_path.write_text(content, encoding='utf-8')
        print(f"Wrote updated {tex_path}")
    else:
        print("No tables updated.")


if __name__ == "__main__":
    main()
