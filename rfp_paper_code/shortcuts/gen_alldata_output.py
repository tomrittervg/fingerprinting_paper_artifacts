#!python3.14t
"""Generate missing All-Data fingerprint output (graphs, text files, CSVs) from alldata.bin.

Checks whether all expected output files exist for each fingerprinter in alldata.bin.
If any are missing, generates them and exits. Safe to re-run — skips already-present outputs.

Usage:
    ./shortcuts/gen_alldata_output.py <output_dir>
"""

import argparse
import gc
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

os.environ.setdefault('MPLCONFIGDIR', '/tmp/claude-999/mpl')

import config
import script_config as script_config_module
import output as _output_mod
from output import print_fingerprint_results

# Provide a minimal script_config so output.py can read toggle keys
_default_sc = {
    'print_cohort_size_tables': True,
    'max_threads_graph_export': 4,
}
script_config_module.script_config = _default_sc
_output_mod.script_config = _default_sc


def _sentinel_path(output_dir):
    return os.path.join(output_dir, "alldata_output.done")


def _p(msg="", indent=6):
    """Print with consistent indentation."""
    if msg:
        print(f"{' ' * indent}{msg}")
    else:
        print()


def process_one(output_dir, regen=False):
    output_dir = os.path.abspath(output_dir)
    dirname = os.path.basename(output_dir)

    if not os.path.isdir(output_dir):
        _p(f"ERROR: not a directory")
        return False

    bin_path = os.path.join(output_dir, "alldata.bin")
    if not os.path.exists(bin_path):
        _p(f"no alldata.bin — skipping")
        return False

    if not regen and os.path.exists(_sentinel_path(output_dir)):
        _p(f"already done — skipping")
        return True

    config.OUTPUT_FOLDER = output_dir

    run_log_path = os.path.join(output_dir, "run.log")
    run_log_file = open(run_log_path, "a", buffering=1)
    config.run_log = config.CleanStream(run_log_file)
    config.start_log_thread()
    config.log(f"\n{'='*60}")
    config.log(f"gen_alldata_output.py — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    config.log(f"  Output dir: {output_dir}")
    config.log(f"{'='*60}")

    with open(bin_path, 'rb') as f:
        payload = pickle.load(f)

    fp_names = payload['fingerprinter_names']
    _p(f"generating ({len(fp_names)} fingerprinter(s): {', '.join(fp_names)})")

    config.RUN_METADATA = payload.get('run_metadata', {})
    fingerprinters = {n: None for n in fp_names}

    t0 = time.time()
    print_fingerprint_results(
        "All-Data",
        payload['total_num_users'],
        payload['fp_counters'],
        payload['fp_categories'],
        fingerprinters,
    )

    # Per-OS output
    fp_by_os = payload.get('fp_counters_by_os')
    if fp_by_os:
        os_values = sorted(set().union(*(d.keys() for d in fp_by_os.values())))
        _p(f"per-OS: {os_values}")
        empty_cats = {n: [] for n in fp_names}
        for os_val in os_values:
            os_fp = {fpn: fp_by_os[fpn].get(os_val, {}) for fpn in fp_names}
            first_fp = next(iter(os_fp.values()), {})
            os_n = sum(first_fp.values()) if first_fp else 0
            if os_n == 0:
                continue
            print_fingerprint_results(
                f"All-Data-{os_val}", os_n, os_fp,
                empty_cats, fingerprinters,
                display_label=f"All-Data ({os_val})",
            )
            _p(f"  {os_val}: {os_n:,} users")

    del payload
    gc.collect()

    elapsed = time.time() - t0
    _p(f"done in {elapsed:.1f}s")

    with open(_sentinel_path(output_dir), "w") as f:
        f.write(f"generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

    config.stop_log_thread()
    config.run_log = None
    run_log_file.close()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dirs", nargs='+', help="Analysis output directory(ies) containing alldata.bin")
    parser.add_argument("-r", "--regen", action="store_true", help="Regenerate even if outputs already exist")
    args = parser.parse_args()

    print(f"gen_alldata_output — {len(args.output_dirs)} directory(ies)")
    for d in args.output_dirs:
        dirname = os.path.basename(os.path.abspath(d))
        print(f"   {dirname}/")
        process_one(d, regen=args.regen)


if __name__ == "__main__":
    main()
