#!/usr/bin/env python3
"""Generate missing LMR output from lmr.bin.

Checks whether LMR output files already exist. If not, loads lmr.bin,
runs the analysis, and exits. Safe to re-run — skips if outputs present.

Usage:
    ./shortcuts/gen_lmr_output.py <output_dir>
"""

import argparse
import gc
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

import config
from smr import run_lmr_analysis


def _sentinel_path(output_dir):
    return os.path.join(output_dir, "lmr_output.done")


def _p(msg="", indent=6):
    if msg:
        print(f"{' ' * indent}{msg}")
    else:
        print()


def process_one(output_dir, regen=False):
    output_dir = os.path.abspath(output_dir)

    if not os.path.isdir(output_dir):
        _p("ERROR: not a directory")
        return False

    bin_path = os.path.join(output_dir, "lmr.bin")
    if not os.path.exists(bin_path):
        _p("no lmr.bin — skipping")
        return False

    if not regen and os.path.exists(_sentinel_path(output_dir)):
        _p("already done — skipping")
        return True

    config.OUTPUT_FOLDER = output_dir
    config.terminal = sys.stderr

    run_log_path = os.path.join(output_dir, "run.log")
    run_log_file = open(run_log_path, "a", buffering=1)
    config.run_log = config.CleanStream(run_log_file)
    config.start_log_thread()
    config.log(f"\n{'='*60}")
    config.log(f"gen_lmr_output.py — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    config.log(f"  Output dir: {output_dir}")
    config.log(f"{'='*60}")

    with open(bin_path, 'rb') as f:
        payload = pickle.load(f)

    config.RUN_METADATA = payload.get('run_metadata', {})

    if payload.get('format') != 'histogram':
        _p("converting legacy histograms...")
        from collections import defaultdict
        for fp_name_conv in payload['lmr_fingerprints']:
            fp_dict = payload['lmr_fingerprints'][fp_name_conv]
            for unit_key in list(fp_dict.keys()):
                hist = defaultdict(int)
                for cnt in fp_dict[unit_key].values():
                    hist[cnt] += 1
                fp_dict[unit_key] = dict(hist)

    fp_names = list(payload['lmr_baselines'].keys())
    _p(f"generating ({len(fp_names)} fingerprinter(s): {', '.join(fp_names)})")
    t0 = time.time()

    run_lmr_analysis(
        payload['lmr_fingerprints'],
        payload['lmr_unit_lists'],
        payload['lmr_baselines'],
    )

    # Per-OS output
    lmr_by_os = payload.get('lmr_fingerprints_by_os')
    baselines_by_os = payload.get('lmr_baselines_by_os', {})
    if lmr_by_os:
        for os_val in sorted(set().union(*(d.keys() for d in lmr_by_os.values()))):
            os_fps = {}
            os_baselines = {}
            os_units = {}
            for fp_name in fp_names:
                if fp_name in lmr_by_os and os_val in lmr_by_os[fp_name]:
                    os_bl = baselines_by_os.get(fp_name, {}).get(os_val)
                    if not os_bl:
                        continue
                    os_fp_name = f"{fp_name} ({os_val})"
                    os_fps[os_fp_name] = lmr_by_os[fp_name][os_val]
                    os_baselines[os_fp_name] = os_bl
                    os_units[os_fp_name] = payload['lmr_unit_lists'][fp_name]
            if os_fps:
                _p(f"per-OS: {os_val}")
                run_lmr_analysis(os_fps, os_units, os_baselines)

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
    parser.add_argument("output_dirs", nargs='+', help="Analysis output directory(ies) containing lmr.bin")
    parser.add_argument("-r", "--regen", action="store_true", help="Regenerate even if outputs already exist")
    args = parser.parse_args()

    print(f"gen_lmr_output — {len(args.output_dirs)} directory(ies)")
    for d in args.output_dirs:
        dirname = os.path.basename(os.path.abspath(d))
        print(f"   {dirname}/")
        process_one(d, regen=args.regen)


if __name__ == "__main__":
    main()
