#!/usr/bin/env python3
"""Parse analyze.py output and produce CSVs for paper Tables 1, 3, and 4.

Usage:
    python3 build_csv.py --analyze-dir <path/to/analyze_output> [<more dirs>] \\
                         --experiments-csv <path/to/experiments.csv> \\
                         [--output-dir <path>] [--table3-fp FPJSv2] [--cohort hhi2]

Reads per-experiment .csv files from the analyze.py output directory
and produces:
    table1_baseline.csv   — Per-OS baseline uniqueness & cohort per fingerprinter
    table3_experiments.csv — Full experiment chain with deltas (one FP)
    run.log                — Provenance
"""

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent

# ── Slug resolution ──────────────────────────────────────────────────────────

def load_slug_map(experiments_csv: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return (slug_map, equivalents) derived from experiments.csv.
    slug_map: {experiment_key: filename_prefix}
    equivalents: {experiment_key: equiv_key}
    """
    code_dir = experiments_csv.parent.parent  # configs/ → code/
    sys.path.insert(0, str(code_dir))
    try:
        from configs.gen_experiments import generate_experiments
        _, _, _, meta = generate_experiments(str(experiments_csv), resolve=False)
        slug_map = dict(meta['slug_map'])
        slug_map.setdefault('All-Data', 'All-Data')
        return slug_map, dict(meta.get('equivalents', {}))
    finally:
        sys.path.pop(0)

# ── Constants ────────────────────────────────────────────────────────────────

FP_DISPLAY = {
    "FPJSv2_Realistic": "Fingerprint Pro",
    "Signifyd_Realistic": "Signifyd",
    "AkamaiV2_Realistic": "Akamai",
}

OS_LIST = ["WINNT", "Darwin", "Android", "Linux"]

# Ordered cumulative chain: (csv_file_prefix, phase_number, display_name, visible)
CUMULATIVE_CHAIN = [
    ("Baseline-Raw",            None,  "Baseline",                       True),
    ("P0-C: Processor Count",   0,     "CPU Core Count (Expert Opinion)",True),
    ("P0-C: WebGL Renderer Sanitizing", 0, "WebGL Renderer String",     True),
    ("P0-C: Minor Version",     0,     "Minor Version",                  True),
    ("P1-C: Font Protections",  1,     "Fonts",                         True),
    ("P1-C: fdLibm",            1,     "Math Functions",                True),
    ("P2-C: Processor Count",   2,     "CPU Core Count (Data Driven)",  True),
    ("P2-C: Screen Availability", 2,   "Available Screen Resolution",   True),
    ("P2-C: Font List Updates",  2,    "Font Updates",                  True),
    ("P3-C: WebGL Vendor",      3,     "WebGL Vendor",                  True),
    ("P3-C: Storage Quota",     3,     "Storage Quota",                 True),
    ("P4-C: Software Canvas",   4,     "Software Rendered Canvas",      True),
    ("P4-C: Accept Language",   4,     "Accept-Language",               True),
    ("P4-C: Timezone",          4,     "Timezone",                      True),
    ("P5-C: Shipping Missing Fonts", 5, "Shipping Missing Fonts",       False),
    ("P5-C: Letterboxing",      5,     "Letterboxing",                  False),
    ("P5-C: Voices",            5,     "Voices",                        False),
    ("P5-C: CSS System Colors", 5,     "CSS System Colors",             False),
    ("P5-C: MathML",            5,     "MathML",                        False),
]

# Individual experiments: each applied to baseline independently
# (experiment_key, phase_number, display_name, visible)
INDIVIDUAL_CHAIN = [
    ("P0-I: Processor Count",        0, "CPU Core Count (Expert Opinion)", True),
    ("P0-I: WebGL Renderer Sanitizing", 0, "WebGL Renderer String",       True),
    ("P0-I: Minor Version",          0, "Minor Version",                   True),
    ("P1-I: Font Protections",       1, "Fonts",                           True),
    ("P1-I: fdLibm",                 1, "Math Functions",                  True),
    ("P2-I: Processor Count",        2, "CPU Core Count (Data Driven)",    True),
    ("P2-I: Screen Availability",    2, "Available Screen Resolution",     True),
    ("P2-I: Font List Updates",      2, "Font Updates",                    True),
    ("P3-I: WebGL Vendor",           3, "WebGL Vendor",                    True),
    ("P3-I: Storage Quota",          3, "Storage Quota",                   True),
    ("P4-I: Software Canvas",        4, "Software Rendered Canvas",        True),
    ("P4-I: Accept Language",        4, "Accept-Language",                 True),
    ("P4-I: Timezone",               4, "Timezone",                        True),
    ("P5-I: Shipping Missing Fonts", 5, "Shipping Missing Fonts",          False),
    ("P5-I: Letterboxing",           5, "Letterboxing",                    False),
    ("P5-I: Voices",                 5, "Voices",                          False),
    ("P5-I: ClientRects Round 2dp",  5, "ClientRects Round 2dp",           False),
    ("P5-I: ClientRects Round 1dp",  5, "ClientRects Round 1dp",           False),
    ("P5-I: ClientRects Round 0dp",  5, "ClientRects Round 0dp",           False),
    ("P5-I: CSS System Colors",      5, "CSS System Colors",               False),
    ("P5-I: MathML",                 5, "MathML",                          False),
    ("PZ-I: Accept Language Limit",  None, "Accept-Language (Limit Only)",  False),
    ("PZ-I: Accept Language Collapse", None, "Accept-Language (Collapse Only)", False),
]

PHASE_NAMES = {0: "Phase 0", 1: "Phase 1", 2: "Phase 2",
               3: "Phase 3", 4: "Phase 4", 5: "Phase 5"}



# ── CSV reading ──────────────────────────────────────────────────────────────

def read_experiment_csv(analyze_dirs, experiment_name, fp_name, slug_map,
                        os_name=None, equivalents=None):
    """Read a single experiment CSV file, searching each dir in order.

    If os_name is provided, looks for {slug}_os_{os_name}-{fp}.csv.
    Otherwise looks for {slug}-{fp}.csv.
    Falls back to equivalent files (e.g. All-Data) if the primary is missing.
    Returns dict or None.
    """
    slug = slug_map.get(experiment_name, experiment_name)
    if os_name:
        filenames = [f"{slug}_os_{os_name}-{fp_name}.csv"]
    else:
        filenames = [f"{slug}-{fp_name}.csv"]

    # Add fallback filenames for equivalents
    equiv_key = (equivalents or {}).get(experiment_name)
    if equiv_key == 'All-Data':
        if os_name:
            filenames.append(f"All-Data-{os_name}-{fp_name}.csv")
        else:
            filenames.append(f"All-Data-{fp_name}.csv")
    elif equiv_key:
        equiv_slug = slug_map.get(equiv_key, equiv_key)
        if os_name:
            filenames.append(f"{equiv_slug}_os_{os_name}-{fp_name}.csv")
        else:
            filenames.append(f"{equiv_slug}-{fp_name}.csv")

    for d in analyze_dirs:
        for filename in filenames:
            path = Path(d) / filename
            if not path.exists():
                continue
            with path.open(newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            if not rows:
                return None
            r = rows[0]
            num_users = int(r['num_users'])
            num_unique = int(r['num_unique_users'])
            hhi = float(r['cohort_fitness'])
            # Read HHI2 from CSV (column name: cohort_fitness_hhi2)
            hhi2 = float(r['cohort_fitness_hhi2']) if 'cohort_fitness_hhi2' in r and r['cohort_fitness_hhi2'] else None
            p50 = int(r['p50']) if 'p50' in r and r['p50'] else None
            return {
                'num_users': num_users,
                'num_unique': num_unique,
                'pct_unique': float(r['pct_unique']),
                'cohort_fitness': hhi,
                'cohort_fitness_hhi2': hhi2,
                'p50': p50,
            }
    return None


def load_chain(analyze_dirs, fp_name, slug_map, equivalents=None):
    """Load all cumulative chain results for one fingerprinter (overall)."""
    chain = []
    for exp_name, phase, display, visible in CUMULATIVE_CHAIN:
        data = read_experiment_csv(analyze_dirs, exp_name, fp_name, slug_map,
                                   equivalents=equivalents)
        if data is None:
            slug = slug_map.get(exp_name, exp_name)
            sys.exit(f"ERROR: missing {slug}-{fp_name}.csv in {[str(d) for d in analyze_dirs]}")
        chain.append({
            'experiment': exp_name,
            'phase': phase,
            'display': display,
            'visible': visible,
            'data': data,
        })
    return chain


# ── Table builders ───────────────────────────────────────────────────────────

def build_table1(analyze_dirs, fp_names, slug_map, equivalents=None, cohort_key='cohort_fitness'):
    """Table 1: Per-OS baseline uniqueness and cohort score per fingerprinter.

    Output CSV has columns:
        Fingerprinter, {OS}_PctUnique, {OS}_CohortScore, {OS}_CohortDelta, ...
    CohortDelta is percent change from FPJSv2 baseline, per OS.
    """
    # Load per-OS data for all fingerprinters
    # {fp: {os: data_dict}}
    all_data = {}
    for fp in fp_names:
        all_data[fp] = {}
        for os_name in OS_LIST:
            data = read_experiment_csv(analyze_dirs, "Baseline-Raw", fp, slug_map,
                                      os_name=os_name, equivalents=equivalents)
            if data is None:
                slug = slug_map.get("Baseline-Raw", "Baseline-Raw")
                sys.exit(f"ERROR: missing {slug}_os_{os_name}-{fp}.csv in {[str(d) for d in analyze_dirs]}")
            all_data[fp][os_name] = data

    # Get FPJSv2 baselines per OS
    baseline_fp = "FPJSv2_Realistic"
    baselines = {}
    for os_name in OS_LIST:
        baselines[os_name] = all_data[baseline_fp][os_name][cohort_key]

    # Get FPJSv2 baseline PctUnique per OS
    pct_baselines = {}
    for os_name in OS_LIST:
        pct_baselines[os_name] = all_data[baseline_fp][os_name]['pct_unique']

    # Get user counts per OS (same across fingerprinters)
    os_user_counts = {}
    for os_name in OS_LIST:
        os_user_counts[os_name] = all_data[baseline_fp][os_name]['num_users']

    rows = []
    for fp in fp_names:
        row = {'Fingerprinter': FP_DISPLAY.get(fp, fp)}
        for os_name in OS_LIST:
            row[f'{os_name}_NumUsers'] = os_user_counts[os_name]
            data = all_data[fp][os_name]
            row[f'{os_name}_PctUnique'] = data['pct_unique']
            if fp != baseline_fp:
                pct_base = pct_baselines[os_name]
                row[f'{os_name}_PctUniqueDelta'] = round(
                    (pct_base - data['pct_unique']) / pct_base * 100, 2) if pct_base else 0
            else:
                row[f'{os_name}_PctUniqueDelta'] = 0
            row[f'{os_name}_CohortScore'] = data[cohort_key]
            if fp != baseline_fp and baselines[os_name]:
                row[f'{os_name}_CohortRatio'] = round(data[cohort_key] / baselines[os_name], 1)
            else:
                row[f'{os_name}_CohortRatio'] = 1.0
        rows.append(row)
    return rows


def _load_chain_per_os(analyze_dirs, fp_name, slug_map, equivalents=None):
    """Load cumulative chain results per OS for one fingerprinter.

    Returns {os_name: [chain_entries]} where each entry has 'data' dict.
    """
    os_chains = {}
    for os_name in OS_LIST:
        chain = []
        for exp_name, phase, display, visible in CUMULATIVE_CHAIN:
            data = read_experiment_csv(analyze_dirs, exp_name, fp_name, slug_map,
                                       os_name=os_name, equivalents=equivalents)
            if data is None:
                slug = slug_map.get(exp_name, exp_name)
                sys.exit(f"ERROR: missing {slug}_os_{os_name}-{fp_name}.csv in {[str(d) for d in analyze_dirs]}")
            chain.append({
                'experiment': exp_name,
                'phase': phase,
                'display': display,
                'visible': visible,
                'data': data,
            })
        os_chains[os_name] = chain
    return os_chains


def build_table3(analyze_dirs, fp_name, slug_map, equivalents=None, cohort_key='cohort_fitness'):
    """Table 3: Per-OS visible experiment chain with per-step deltas.

    Only includes steps where visible=True. Deltas are computed from
    the previous VISIBLE step.

    Output CSV columns: Step, Phase, Technique,
        {OS}_PctUnique, {OS}_UniqImpr, {OS}_CohortScore, {OS}_CohortImpr
    for each OS.
    """
    os_chains = _load_chain_per_os(analyze_dirs, fp_name, slug_map, equivalents)

    # Also load overall chain for step/phase/technique metadata
    overall_chain = load_chain(analyze_dirs, fp_name, slug_map, equivalents)

    # Track previous visible data per OS for delta computation
    prev_by_os = {os_name: None for os_name in OS_LIST}

    rows = []
    step_num = 0

    for chain_idx, step in enumerate(overall_chain):
        if not step['visible']:
            continue

        row = {
            'Step': step_num,
            'Phase': PHASE_NAMES.get(step['phase'], '') if step['phase'] is not None else '',
            'Technique': step['display'],
        }

        for os_name in OS_LIST:
            os_step = os_chains[os_name][chain_idx]
            d = os_step['data']
            prev = prev_by_os[os_name]

            if d is None:
                row[f'{os_name}_PctUnique'] = ''
                row[f'{os_name}_UniqImpr'] = ''
                row[f'{os_name}_CohortScore'] = ''
                prev_by_os[os_name] = None
            else:
                row[f'{os_name}_PctUnique'] = d['pct_unique']
                row[f'{os_name}_CohortScore'] = d[cohort_key]

                if prev is not None and prev['pct_unique'] > 0:
                    uniq_impr = prev['pct_unique'] - d['pct_unique']
                    row[f'{os_name}_UniqImpr'] = round(uniq_impr, 2)
                else:
                    row[f'{os_name}_UniqImpr'] = ''
                prev_by_os[os_name] = d

        rows.append(row)
        step_num += 1

    return rows


def build_table5(analyze_dirs, fp_name, slug_map, equivalents=None, cohort_key='cohort_fitness'):
    """Table 5: Per-OS individual experiment results.

    Each experiment is applied to the baseline independently. Deltas are
    computed against the Baseline-Raw for each OS.

    Output CSV columns: Step, Phase, Technique,
        {OS}_PctUnique, {OS}_UniqImpr, {OS}_CohortImpr
    for each OS.
    """
    # Load baseline per OS
    baseline_by_os = {}
    for os_name in OS_LIST:
        data = read_experiment_csv(analyze_dirs, "Baseline-Raw", fp_name, slug_map,
                                   os_name=os_name, equivalents=equivalents)
        if data is None:
            slug = slug_map.get("Baseline-Raw", "Baseline-Raw")
            sys.exit(f"ERROR: missing {slug}_os_{os_name}-{fp_name}.csv")
        baseline_by_os[os_name] = data

    rows = []

    # Add baseline row
    baseline_row = {'Step': 0, 'Phase': '', 'Technique': 'Baseline'}
    for os_name in OS_LIST:
        b = baseline_by_os[os_name]
        baseline_row[f'{os_name}_PctUnique'] = b['pct_unique']
        baseline_row[f'{os_name}_UniqImpr'] = ''
        baseline_row[f'{os_name}_CohortScore'] = b[cohort_key]
    rows.append(baseline_row)

    step_num = 1

    for exp_name, phase, display, visible in INDIVIDUAL_CHAIN:
        if not visible:
            continue

        row = {
            'Step': step_num,
            'Phase': PHASE_NAMES.get(phase, '') if phase is not None else '',
            'Technique': display,
        }

        for os_name in OS_LIST:
            d = read_experiment_csv(analyze_dirs, exp_name, fp_name, slug_map,
                                    os_name=os_name, equivalents=equivalents)
            baseline = baseline_by_os[os_name]

            if d is None:
                row[f'{os_name}_PctUnique'] = ''
                row[f'{os_name}_UniqImpr'] = ''
                row[f'{os_name}_CohortScore'] = ''
            else:
                row[f'{os_name}_PctUnique'] = d['pct_unique']
                row[f'{os_name}_CohortScore'] = d[cohort_key]
                if baseline['pct_unique'] > 0:
                    uniq_impr = baseline['pct_unique'] - d['pct_unique']
                    row[f'{os_name}_UniqImpr'] = round(uniq_impr, 2)
                else:
                    row[f'{os_name}_UniqImpr'] = ''

        rows.append(row)
        step_num += 1

    return rows


def build_overall(per_os_rows, mode, analyze_dirs, fp_name, slug_map,
                   equivalents=None, cohort_key='cohort_fitness'):
    """Build an Overall (population-weighted average) table from per-OS rows.

    mode: 'cumulative' (Δ from previous row) or 'individual' (Δ from baseline).
    Returns list of dicts with keys: Step, Phase, Technique, PctUnique,
    UniqImpr, CohortScore.
    """
    # Get per-OS user counts from baseline
    os_users = {}
    for os_name in OS_LIST:
        data = read_experiment_csv(analyze_dirs, "Baseline-Raw", fp_name, slug_map,
                                   os_name=os_name, equivalents=equivalents)
        os_users[os_name] = data['num_users'] if data else 0

    rows = []
    baseline_pct = None
    prev_pct = None

    for r in per_os_rows:
        # Compute weighted averages
        sw_pct = sw_coh = tw = 0.0
        for os_name in OS_LIST:
            pct = r.get(f'{os_name}_PctUnique', '')
            coh = r.get(f'{os_name}_CohortScore', '')
            w = os_users.get(os_name, 0)
            if pct != '' and pct is not None and w > 0:
                sw_pct += float(pct) * w
                if coh != '' and coh is not None:
                    sw_coh += float(coh) * w
                tw += w
        pct_avg = sw_pct / tw if tw > 0 else 0
        coh_avg = sw_coh / tw if tw > 0 else 0

        row = {
            'Step': r['Step'],
            'Phase': r['Phase'],
            'Technique': r['Technique'],
            'PctUnique': round(pct_avg, 4),
            'CohortScore': coh_avg,
        }

        if baseline_pct is None:
            baseline_pct = pct_avg
            prev_pct = pct_avg
            row['UniqImpr'] = ''
        else:
            ref = prev_pct if mode == 'cumulative' else baseline_pct
            row['UniqImpr'] = round(ref - pct_avg, 2)
            prev_pct = pct_avg

        rows.append(row)

    return rows


# ── Provenance ───────────────────────────────────────────────────────────────

def extract_provenance(analyze_dirs):
    """Extract provenance from run.log in the first analyze output directory."""
    run_log = Path(analyze_dirs[0]) / 'run.log'
    info = {'output_dirs': [str(d) for d in analyze_dirs], 'date_start': None,
            'date_end': None, 'num_users': None}
    if not run_log.exists():
        return info
    with run_log.open(encoding='utf-8') as f:
        for line in f:
            m = re.search(r"Date range:\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})", line)
            if m:
                info['date_start'] = m.group(1)
                info['date_end'] = m.group(2)
            m = re.search(r"Parallel processing:\s+([\d,]+)\s+DataValues", line)
            if m:
                info['num_users'] = m.group(1).replace(",", "")
    return info


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--analyze-dir", required=True, nargs='+', metavar="DIR",
                        help="Path(s) to analyze.py output directories (searched in order)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (default: script dir)")
    parser.add_argument("--table3-fp", default="FPJSv2_Realistic",
                        help="Fingerprinter for Table 3 (default: FPJSv2_Realistic)")
    parser.add_argument("--experiments-csv", required=True, metavar="PATH",
                        help="Path to experiments.csv (in rfp_paper_code/configs/)")
    parser.add_argument("--cohort", default="hhi", choices=["hhi", "hhi2"],
                        help="Cohort metric: hhi (all users, default) or hhi2 (excl. unique)")
    args = parser.parse_args()

    analyze_dirs = []
    for d in args.analyze_dir:
        p = Path(d).resolve()
        if not p.exists():
            sys.exit(f"ERROR: --analyze-dir does not exist: {p}")
        analyze_dirs.append(p)

    experiments_csv = Path(args.experiments_csv).resolve()
    if not experiments_csv.exists():
        sys.exit(f"ERROR: --experiments-csv does not exist: {experiments_csv}")

    out_dir = Path(args.output_dir).resolve() if args.output_dir else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    slug_map, equivalents = load_slug_map(experiments_csv)

    cohort_key = 'cohort_fitness' if args.cohort == 'hhi' else 'cohort_fitness_hhi2'
    print(f"Cohort metric: {args.cohort} ({cohort_key})")

    fp_names = list(FP_DISPLAY.keys())

    # ── Table 1: per-OS baseline ──
    t1 = build_table1(analyze_dirs, fp_names, slug_map, equivalents, cohort_key=cohort_key)
    t1_fieldnames = ['Fingerprinter']
    for os_name in OS_LIST:
        t1_fieldnames.extend([f'{os_name}_NumUsers', f'{os_name}_PctUnique',
                              f'{os_name}_PctUniqueDelta',
                              f'{os_name}_CohortScore', f'{os_name}_CohortRatio'])
    t1_path = out_dir / 'table1_baseline.csv'
    with t1_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=t1_fieldnames)
        w.writeheader()
        w.writerows(t1)
    print(f"Wrote {len(t1)} rows to {t1_path}")

    # ── Table 3: per-OS experiment chain ──
    t3 = build_table3(analyze_dirs, args.table3_fp, slug_map, equivalents, cohort_key=cohort_key)
    t3_fieldnames = ['Step', 'Phase', 'Technique']
    for os_name in OS_LIST:
        t3_fieldnames.extend([f'{os_name}_PctUnique', f'{os_name}_UniqImpr',
                              f'{os_name}_CohortScore'])
    t3_path = out_dir / 'table3_experiments.csv'
    with t3_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=t3_fieldnames)
        w.writeheader()
        w.writerows(t3)
    print(f"Wrote {len(t3)} rows to {t3_path} (fp: {args.table3_fp})")

    # ── Table 5: per-OS individual experiments ──
    t5 = build_table5(analyze_dirs, args.table3_fp, slug_map, equivalents, cohort_key=cohort_key)
    t5_fieldnames = ['Step', 'Phase', 'Technique']
    for os_name in OS_LIST:
        t5_fieldnames.extend([f'{os_name}_PctUnique', f'{os_name}_UniqImpr',
                              f'{os_name}_CohortScore'])
    t5_path = out_dir / 'table5_individual.csv'
    with t5_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=t5_fieldnames)
        w.writeheader()
        w.writerows(t5)
    print(f"Wrote {len(t5)} rows to {t5_path} (fp: {args.table3_fp})")

    # ── Overall tables: population-weighted averages ──
    overall_fieldnames = ['Step', 'Phase', 'Technique', 'PctUnique', 'UniqImpr', 'CohortScore']

    t3_overall = build_overall(t3, 'cumulative', analyze_dirs, args.table3_fp,
                               slug_map, equivalents, cohort_key=cohort_key)
    t3o_path = out_dir / 'table3_overall.csv'
    with t3o_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=overall_fieldnames)
        w.writeheader()
        w.writerows(t3_overall)
    print(f"Wrote {len(t3_overall)} rows to {t3o_path}")

    t5_overall = build_overall(t5, 'individual', analyze_dirs, args.table3_fp,
                               slug_map, equivalents, cohort_key=cohort_key)
    t5o_path = out_dir / 'table5_overall.csv'
    with t5o_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=overall_fieldnames)
        w.writeheader()
        w.writerows(t5_overall)
    print(f"Wrote {len(t5_overall)} rows to {t5o_path}")

    # ── Provenance ──
    prov = extract_provenance(analyze_dirs)
    log_path = out_dir / 'run.log'
    with log_path.open('w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("experiment_table — Provenance Log\n")
        f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
        f.write("=" * 60 + "\n\n")
        for i, d in enumerate(prov['output_dirs']):
            label = "Source:" if i == 0 else "       "
            f.write(f"{label}       {d}\n")
        f.write(f"Date range:   {prov['date_start']} to {prov['date_end']}\n")
        f.write(f"Users:        {prov['num_users']}\n")
        f.write(f"Table 3 FP:   {args.table3_fp} ({FP_DISPLAY.get(args.table3_fp, '?')})\n")
        f.write(f"Cohort:       {args.cohort}\n")
    print(f"Wrote provenance to {log_path}")


if __name__ == "__main__":
    main()
