#!python3.14t
"""Generate missing experiment/mode output (graphs, text files, CSVs) from pickled data.

For each exp_*.bin / mode_*.bin file in the output directory, checks whether all
expected output files exist. If any are missing, loads the pickle, generates the
output, frees memory, and moves to the next.

Usage:
    ./gen_experiment_output.py <output_dir>
"""

import csv
import json
import os
import sys
import argparse
import pickle
import gc
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import config
import script_config as script_config_module
import output as _output_mod
from output import print_fingerprint_results

_default_sc = {
    'print_cohort_size_tables': True,
    'max_threads_graph_export': 4,
}
script_config_module.script_config = _default_sc
_output_mod.script_config = _default_sc


def _done_path(output_dir, filename):
    return os.path.join(output_dir, filename.replace(".bin", ".done"))


def _load_manifest(output_dir):
    """Load experiment_manifest.json if present. Returns (slug_map, equivalents) or ({}, {})."""
    path = os.path.join(output_dir, 'experiment_manifest.json')
    if not os.path.exists(path):
        return {}, {}
    with open(path) as f:
        data = json.load(f)
    return data.get('slug_map', {}), data.get('equivalents', {})


def _load_alldata_baselines(output_dir):
    """Load overall All-Data CSVs and return {fp_name: (num_unique, pct, fitness)}.
    Skips per-OS files like All-Data-WINNT-FPJSv2.csv (handled by _load_per_os_baselines)."""
    import re
    # Detect OS prefixes from per-OS filenames
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
        # Skip per-OS files: those whose fp_name starts with a known OS prefix + '-'
        if any(fp_name.startswith(f"{os_pfx}-") for os_pfx in os_prefixes):
            continue
        path = os.path.join(output_dir, fname)
        with open(path, newline='') as f:
            rows = list(csv.reader(f))
        if len(rows) >= 2:
            _, num_unique, pct, fitness = rows[1][:4]
            baselines[fp_name] = (int(num_unique), float(pct), float(fitness))
    return baselines


def _is_individual_experiment(slug):
    return slug.startswith('I-P')


def _generate_one(payload, kind, slug, display_label_override=None, baseline_by_fp=None):
    """Call print_fingerprint_results for one loaded pickle payload."""
    label    = payload['exp_name'] if kind == "exp" else payload['mode_name']
    fp_names = payload['fingerprinter_names']
    fingerprinters      = {n: None for n in fp_names}
    config.RUN_METADATA = payload.get('run_metadata', {})
    display_label = display_label_override or payload.get('display_label', label)
    print_fingerprint_results(
        label,
        payload['total_num_users'],
        payload['fp_counters'],
        payload['fp_categories'],
        fingerprinters,
        display_label=display_label,
        filters=[],
        filename_label=slug,
        baseline_by_fp=baseline_by_fp if _is_individual_experiment(slug) else None,
    )

    # Per-OS output
    fp_by_os = payload.get('fp_counters_by_os')
    if fp_by_os:
        empty_cats = {n: [] for n in fp_names}
        os_values = sorted(fp_by_os.keys())
        for os_val in os_values:
            os_fp = fp_by_os[os_val]
            # Derive user count from first fingerprinter's histogram
            first_fp = next(iter(os_fp.values()), {})
            if isinstance(first_fp, dict) and first_fp:
                # histogram format: {cohort_size: count} — total = sum(size * count)
                sample_key = next(iter(first_fp.keys()))
                if isinstance(sample_key, int):
                    os_n = sum(sz * cnt for sz, cnt in first_fp.items())
                else:
                    os_n = sum(first_fp.values())
            else:
                os_n = 0
            if os_n == 0:
                continue
            os_display = display_label_override or payload.get('display_label', label)
            from graphing import safe_filename as _sf
            print_fingerprint_results(
                f"{label}-{os_val}", os_n, os_fp,
                empty_cats, fingerprinters,
                display_label=f"{os_display} ({os_val})",
                filters=[],
                filename_label=f"{slug}_os_{_sf(os_val)}",
            )


def _find_sibling_source(output_dir, active_key, _I):
    """If output_dir is exp_ind_04##_*, look for a sibling exp_add_04##_* dir
    containing the source pickle. Returns the path if found, else None."""
    import re
    dirname = os.path.basename(output_dir)
    m = re.match(r'exp_ind(?:v)?_(04\d\d)_', dirname)
    if not m:
        print(f"{_I}  [warn] Cannot generate equivalent: "
              f"exp_{active_key}.bin not found")
        return None

    date_part = m.group(1)
    parent = os.path.dirname(output_dir)
    pattern = re.compile(rf'^exp_add_{date_part}_\d+$')
    candidates = [d for d in os.listdir(parent)
                  if pattern.match(d) and os.path.isdir(os.path.join(parent, d))]

    if len(candidates) == 1:
        sibling_dir = os.path.join(parent, candidates[0])
        source_bin = os.path.join(sibling_dir, f"exp_{active_key}.bin")
        if os.path.exists(source_bin):
            print(f"{_I}  [info] found exp_{active_key}.bin in sibling {candidates[0]}/")
            return source_bin
        else:
            print(f"{_I}  [warn] found sibling {candidates[0]}/ but exp_{active_key}.bin not in it")
            return None
    elif len(candidates) == 0:
        print(f"{_I}  [warn] looked for exp_add_{date_part}_* but could not find one")
        return None
    else:
        print(f"{_I}  [warn] looked for exp_add_{date_part}_* but found multiple: {candidates}")
        return None


def process_directory(output_dir, regen=False):
    _I = "      "  # indent prefix for output under a directory
    config.OUTPUT_FOLDER = output_dir

    baselines = _load_alldata_baselines(output_dir)
    if baselines:
        print(f"{_I}{len(baselines)} fingerprinter baseline(s)")

    slug_map, equivalents = _load_manifest(output_dir)
    if slug_map:
        print(f"{_I}{len(slug_map)} slugs, {len(equivalents)} equivalent(s)")
    else:
        print(f"{_I}no manifest — using raw names")

    exp_files  = sorted(f for f in os.listdir(output_dir) if f.startswith("exp_")  and f.endswith(".bin"))
    mode_files = sorted(f for f in os.listdir(output_dir) if f.startswith("mode_") and f.endswith(".bin"))
    all_files  = [("exp",  f) for f in exp_files] + [("mode", f) for f in mode_files]

    print(f"{_I}{len(exp_files)} experiment(s), {len(mode_files)} mode(s)")
    total = len(all_files)
    done  = 0

    # Map exp_name -> loaded payload (kept in memory only while needed for equivalents)
    payloads_for_equiv = {}

    for kind, filename in all_files:
        done_path = _done_path(output_dir, filename)
        if not regen and os.path.exists(done_path):
            exp_name = filename.removeprefix("exp_").removeprefix("mode_").removesuffix(".bin")
            print(f"{_I}  [skip] {exp_name}")
            done += 1
            continue

        path = os.path.join(output_dir, filename)
        with open(path, 'rb') as f:
            payload = pickle.load(f)

        exp_name = payload['exp_name'] if kind == "exp" else payload['mode_name']
        slug     = slug_map.get(exp_name, exp_name)

        print(f"{_I}  [gen]  {exp_name} → {slug} ({done + 1}/{total})")

        if payload.get('format') != 'histogram':
            from collections import defaultdict as _dd
            for _fp_name in payload['fp_counters']:
                _hist = _dd(int)
                for _cnt in payload['fp_counters'][_fp_name].values():
                    _hist[_cnt] += 1
                payload['fp_counters'][_fp_name] = dict(_hist)

        _generate_one(payload, kind, slug, baseline_by_fp=baselines)

        with open(done_path, "w") as f:
            f.write(f"generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

        if kind == "exp" and exp_name in equivalents.values():
            payloads_for_equiv[exp_name] = payload
        else:
            del payload
            gc.collect()
        done += 1

    if equivalents:
        print(f"{_I}{len(equivalents)} equivalent(s)...")
        for commented_key, active_key in equivalents.items():
            equiv_slug = slug_map.get(commented_key, commented_key)
            done_filename = f"equiv_{_safe_filename(commented_key)}.done"
            done_path = os.path.join(output_dir, done_filename)
            if not regen and os.path.exists(done_path):
                print(f"{_I}  [skip] {commented_key} (equiv of {active_key})")
                continue

            print(f"{_I}  [gen]  {commented_key} → {equiv_slug} (from {active_key})")

            if active_key == 'All-Data':
                _generate_from_alldata(output_dir, equiv_slug, commented_key, baselines)
            else:
                source_payload = payloads_for_equiv.get(active_key)
                if source_payload is None:
                    source_bin = os.path.join(output_dir, f"exp_{active_key}.bin")
                    if not os.path.exists(source_bin):
                        # If this is an exp_ind_04## dir, look for exp_add_04## sibling
                        source_bin = _find_sibling_source(output_dir, active_key, _I)
                        if source_bin is None:
                            continue
                    with open(source_bin, 'rb') as f:
                        source_payload = pickle.load(f)
                    if source_payload.get('format') != 'histogram':
                        from collections import defaultdict as _dd
                        for _fp_name in source_payload['fp_counters']:
                            _hist = _dd(int)
                            for _cnt in source_payload['fp_counters'][_fp_name].values():
                                _hist[_cnt] += 1
                            source_payload['fp_counters'][_fp_name] = dict(_hist)

                _generate_one(source_payload, "exp", equiv_slug,
                              display_label_override=commented_key,
                              baseline_by_fp=baselines)

            with open(done_path, "w") as f:
                f.write(f"generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

        payloads_for_equiv.clear()
        gc.collect()

    print(f"{_I}done ({done}/{total} processed)")

    _generate_summary_graphs(output_dir, slug_map, baselines, equivalents,
                             had_experiments=(total > 0))


def _read_exp_csv(output_dir, slug, fp_name, os_suffix='', equivalents=None):
    """Return (pct_unique, cohort_fitness) from a CSV, or None if missing.
    os_suffix: e.g. '_os_WINNT' for per-OS files, '' for overall.
    equivalents: {slug: equiv_key} — if the primary file is missing, try the equivalent.
    """
    path = os.path.join(output_dir, f"{slug}{os_suffix}-{fp_name}.csv")
    if not os.path.exists(path) and equivalents:
        # Look up equivalent by slug (equivalents maps exp_key -> equiv_key,
        # slug_map maps exp_key -> slug, so we need reverse lookup)
        equiv_key = equivalents.get(slug)
        if equiv_key == 'All-Data':
            # All-Data files: All-Data-{fp}.csv or All-Data-{OS}-{fp}.csv
            if os_suffix:
                os_val = os_suffix.removeprefix('_os_')
                path = os.path.join(output_dir, f"All-Data-{os_val}-{fp_name}.csv")
            else:
                path = os.path.join(output_dir, f"All-Data-{fp_name}.csv")
        elif equiv_key:
            path = os.path.join(output_dir, f"{equiv_key}{os_suffix}-{fp_name}.csv")
    if not os.path.exists(path):
        return None
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return None
    _, _, pct, fitness = rows[1][:4]
    return float(pct), float(fitness)


def _detect_os_values(output_dir):
    """Detect OS values from per-OS CSV filenames like {slug}_os_{OS}-{fp}.csv."""
    import re
    os_vals = set()
    for f in os.listdir(output_dir):
        m = re.search(r'_os_([A-Za-z]+)-[^/]+\.csv$', f)
        if m:
            os_vals.add(m.group(1))
    return sorted(os_vals)


def _load_per_os_baselines(output_dir, os_val):
    """Load All-Data-{OS}-{fp}.csv baselines for one OS. Returns {fp_name: (num_unique, pct, fitness)}."""
    baselines = {}
    for fname in os.listdir(output_dir):
        if not (fname.startswith(f'All-Data-{os_val}-') and fname.endswith('.csv')):
            continue
        fp_name = fname[len(f'All-Data-{os_val}-'):-len('.csv')]
        path = os.path.join(output_dir, fname)
        with open(path, newline='') as f:
            rows = list(csv.reader(f))
        if len(rows) >= 2:
            _, num_unique, pct, fitness = rows[1][:4]
            baselines[fp_name] = (int(num_unique), float(pct), float(fitness))
    return baselines


def _generate_summary_graphs(output_dir, slug_map, baselines, equivalents=None, had_experiments=False):
    """Generate cumulative line graph and individual bar graph from CSV data."""
    if not slug_map or not baselines:
        if had_experiments:
            _I = "      "
            if not slug_map:
                print(f"{_I}[warn] no slug map — cannot generate summary graphs")
            elif not baselines:
                print(f"{_I}[warn] no baselines — cannot generate summary graphs")
        return

    from graphing import (experiment_cumulative_line_graph,
                          experiment_individual_bar_graph,
                          experiment_cumulative_line_graph_by_fp)

    fp_order = sorted(baselines.keys())

    # Build slug -> equiv_key mapping for fallback CSV reads
    _slug_equiv = {}
    if equivalents:
        for exp_key, equiv_key in equivalents.items():
            slug = slug_map.get(exp_key)
            if slug:
                _slug_equiv[slug] = equiv_key

    def _read_csv(slug, fp_name, os_suffix=''):
        return _read_exp_csv(output_dir, slug, fp_name, os_suffix=os_suffix,
                             equivalents=_slug_equiv)

    # ── Cumulative line graph (C-P* slugs in slug order) ──────────────────────
    # Include Baseline-Raw and all C-P* slugs in slug_map order
    cumul_steps = []
    for key, slug in slug_map.items():
        if slug == 'C-P0-00-Baseline-Raw' or (slug.startswith('C-P') and '-C-' not in slug):
            # short display label: strip leading "C-PX-NN-" prefix
            parts = slug.split('-', 3)
            label = parts[3].replace('_', ' ') if len(parts) == 4 else slug
            cumul_steps.append((slug, label))

    cumul_fp_data = {}
    for fp_name in fp_order:
        cumul_fp_data[fp_name] = {}
        for slug, _ in cumul_steps:
            result = _read_csv(slug, fp_name)
            if result:
                cumul_fp_data[fp_name][slug] = result[0]

    # ── Individual bar graph (I-P* slugs in slug order) ───────────────────────
    indiv_steps = []
    for key, slug in slug_map.items():
        if slug.startswith('I-P'):
            parts = slug.split('-', 3)
            label = parts[3].replace('_', ' ') if len(parts) == 4 else slug
            indiv_steps.append((slug, label))

    indiv_fp_data = {}
    for fp_name in fp_order:
        baseline_pct = baselines[fp_name][1]
        indiv_fp_data[fp_name] = {}
        for slug, _ in indiv_steps:
            result = _read_csv(slug, fp_name)
            if result:
                indiv_fp_data[fp_name][slug] = baseline_pct - result[0]

    print("      generating summary graphs...")
    if cumul_steps:
        experiment_cumulative_line_graph(cumul_steps, cumul_fp_data, fp_order)
    if indiv_steps:
        experiment_individual_bar_graph(indiv_steps, indiv_fp_data, fp_order)

    # ── Per-OS cumulative line graphs ────────────────────────────────────────
    if not cumul_steps:
        return

    os_values = _detect_os_values(output_dir)
    if not os_values:
        return

    for os_val in os_values:
        os_suffix = f"_os_{os_val}"
        os_fp_data = {}
        for fp_name in fp_order:
            os_fp_data[fp_name] = {}
            for slug, _ in cumul_steps:
                result = _read_csv(slug, fp_name, os_suffix=os_suffix)
                if result:
                    os_fp_data[fp_name][slug] = result[0]
        if any(os_fp_data[fp].get(cumul_steps[0][0]) for fp in fp_order):
            experiment_cumulative_line_graph(
                cumul_steps, os_fp_data, fp_order,
                title=f"Cumulative Experiment Steps ({os_val}) — % Unique Users")

    # ── Combined graph: one row per FP, one line per OS + Overall ────────────
    os_fp_data_all = {}
    # Overall
    os_fp_data_all["Overall"] = cumul_fp_data
    # Per-OS
    for os_val in os_values:
        os_suffix = f"_os_{os_val}"
        os_fp_data_all[os_val] = {}
        for fp_name in fp_order:
            os_fp_data_all[os_val][fp_name] = {}
            for slug, _ in cumul_steps:
                result = _read_csv(slug, fp_name, os_suffix=os_suffix)
                if result:
                    os_fp_data_all[os_val][fp_name][slug] = result[0]

    os_order = ["Overall"] + os_values
    experiment_cumulative_line_graph_by_fp(
        cumul_steps, os_fp_data_all, fp_order, os_order)


def _generate_from_alldata(output_dir, slug, display_label, baselines):
    """Generate output for an experiment equivalent to All-Data by re-running
    print_fingerprint_analysis against each All-Data-{fp}.bin."""
    from calculations import print_fingerprint_analysis
    for fp_name in sorted(baselines.keys()):
        src_bin = os.path.join(output_dir, f"All-Data-{fp_name}.bin")
        if not os.path.exists(src_bin):
            print(f"    [warn] {src_bin} not found, skipping {fp_name}")
            continue
        with open(src_bin, 'rb') as f:
            data = pickle.load(f)
        fingerprints = data.get('fingerprints', {})
        num_users = data.get('metadata', {}).get('num_users', sum(fingerprints.values()))
        config.RUN_METADATA = data.get('metadata', {})
        baseline_info = baselines.get(fp_name)
        print_fingerprint_analysis(
            f"{slug}-{fp_name}",
            num_users,
            fingerprints,
            False,
            display_title=f"{display_label}-{fp_name}",
            baseline_info=baseline_info if _is_individual_experiment(slug) else None,
        )


def _safe_filename(s):
    """Simple filename sanitizer for .done file names."""
    import re
    return re.sub(r'[^A-Za-z0-9_\-]+', '_', s).strip('_')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dirs", nargs='+', help="Analysis output directory(ies) containing exp_*.bin / mode_*.bin files")
    parser.add_argument("-r", "--regen", action="store_true", help="Regenerate even if outputs already exist")
    args = parser.parse_args()

    print(f"gen_experiment_output — {len(args.output_dirs)} directory(ies)")
    for d in args.output_dirs:
        dirname = os.path.basename(os.path.abspath(d))
        print(f"   {dirname}/")
        if not os.path.isdir(d):
            print(f"      ERROR: not a directory")
            continue
        # Check if any experiment/mode pickles exist
        has_bins = any(f.endswith(".bin") and (f.startswith("exp_") or f.startswith("mode_"))
                       for f in os.listdir(d))
        if not has_bins:
            print(f"      no exp_*.bin / mode_*.bin — skipping")
            continue
        process_directory(d, regen=args.regen)


if __name__ == "__main__":
    main()
