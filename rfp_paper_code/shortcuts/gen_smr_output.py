#!python3.14t
"""Generate missing SMR output from smr.bin.

Checks whether SMR output files already exist per fingerprinter. If not,
loads smr.bin, runs the analysis, and exits.
Safe to re-run — skips fingerprinters whose CSV output already exists.

Usage:
    ./shortcuts/gen_smr_output.py <output_dir>
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
from smr import output_smr, _fp_slug


def _sentinel_path(output_dir):
    return os.path.join(output_dir, "smr_output.done")


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

    bin_path = os.path.join(output_dir, "smr.bin")
    if not os.path.exists(bin_path):
        _p("no smr.bin — skipping")
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
    config.log(f"gen_smr_output.py — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    config.log(f"  Output dir: {output_dir}")
    config.log(f"{'='*60}")

    with open(bin_path, 'rb') as f:
        payload = pickle.load(f)

    config.RUN_METADATA = payload.get('run_metadata', {})

    if payload.get('format') != 'histogram':
        _p("converting legacy histograms...")
        from collections import defaultdict
        for fp_name_conv in payload['smr_fingerprints']:
            fp_dict = payload['smr_fingerprints'][fp_name_conv]
            for metric_key in list(fp_dict.keys()):
                hist = defaultdict(int)
                for cnt in fp_dict[metric_key].values():
                    hist[cnt] += 1
                fp_dict[metric_key] = dict(hist)

    fp_names = list(payload['smr_baselines'].keys())
    _p(f"generating ({len(fp_names)} fingerprinter(s): {', '.join(fp_names)})")

    for fp_name in fp_names:
        if fp_name not in payload['smr_fingerprints']:
            _p(f"{fp_name}: no SMR fingerprint data (baselines only) — skipping")
            continue
        t0 = time.time()
        _bl = payload['smr_baselines'][fp_name]
        num_users, num_unique_users, baseline_fitness = _bl[0], _bl[1], _bl[2]
        baseline_fitness_hhi2 = _bl[3] if len(_bl) > 3 else None
        baseline_p50 = _bl[4] if len(_bl) > 4 else None
        output_smr(
            payload['smr_fingerprints'][fp_name],
            payload['smr_metric_lists'][fp_name],
            num_users,
            num_unique_users,
            baseline_fitness,
            fp_name,
            baseline_fitness_hhi2=baseline_fitness_hhi2,
            baseline_p50=baseline_p50,
        )
        _p(f"{fp_name} done in {time.time() - t0:.1f}s")

    # Per-OS output
    smr_by_os = payload.get('smr_fingerprints_by_os')
    baselines_by_os = payload.get('smr_baselines_by_os', {})
    if smr_by_os:
        for fp_name in fp_names:
            if fp_name not in smr_by_os:
                continue
            for os_val in sorted(smr_by_os[fp_name].keys()):
                os_bl = baselines_by_os.get(fp_name, {}).get(os_val)
                if not os_bl:
                    continue
                os_n, os_u, os_fit = os_bl[0], os_bl[1], os_bl[2]
                os_fit2 = os_bl[3] if len(os_bl) > 3 else None
                os_p50 = os_bl[4] if len(os_bl) > 4 else None
                os_fp_name = f"{fp_name} ({os_val})"
                t0 = time.time()
                output_smr(
                    smr_by_os[fp_name][os_val],
                    payload['smr_metric_lists'][fp_name],
                    os_n, os_u, os_fit, os_fp_name,
                    baseline_fitness_hhi2=os_fit2,
                    baseline_p50=os_p50,
                )
                _p(f"{os_fp_name} done in {time.time() - t0:.1f}s")

    del payload
    gc.collect()

    with open(_sentinel_path(output_dir), "w") as f:
        f.write(f"generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

    config.stop_log_thread()
    config.run_log = None
    run_log_file.close()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dirs", nargs='+', help="Analysis output directory(ies) containing smr.bin")
    parser.add_argument("-r", "--regen", action="store_true", help="Regenerate even if outputs already exist")
    args = parser.parse_args()

    print(f"gen_smr_output — {len(args.output_dirs)} directory(ies)")
    for d in args.output_dirs:
        dirname = os.path.basename(os.path.abspath(d))
        print(f"   {dirname}/")
        process_one(d, regen=args.regen)


if __name__ == "__main__":
    main()
