#!python3.14t
"""Generate missing metric aggregation output from metric_aggregation_output.bin.

Checks whether output has already been generated. If not, loads the pickle,
applies the saved config, runs visualize_metrics_aggregated, and exits.
Safe to re-run — skips if outputs present (sentinel: metric_aggregation_output.done).

Usage:
    ./shortcuts/gen_metrics_output.py <output_dir>
"""

import argparse
import csv
import gc
import os
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

os.environ.setdefault('MPLCONFIGDIR', '/tmp/claude-999/mpl')

import config
import script_config as script_config_module
from output import visualize_metrics_aggregated


def _outputs_exist(output_dir):
    """Return True if output has already been generated."""
    return os.path.exists(os.path.join(output_dir, "metric_aggregation_output.done"))


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

    bin_path = os.path.join(output_dir, "metric_aggregation_output.bin")
    if not os.path.exists(bin_path):
        _p("no metric_aggregation_output.bin — skipping")
        return False

    if not regen and _outputs_exist(output_dir):
        _p("already done — skipping")
        return True

    config.OUTPUT_FOLDER = output_dir
    config.terminal = sys.stderr

    run_log_path = os.path.join(output_dir, "run.log")
    run_log_file = open(run_log_path, "a", buffering=1)
    config.run_log = config.CleanStream(run_log_file)
    config.start_log_thread()
    config.log(f"\n{'='*60}")
    config.log(f"gen_metrics_output.py — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    config.log(f"  Output dir: {output_dir}")
    config.log(f"{'='*60}")

    with open(bin_path, 'rb') as f:
        payload = pickle.load(f)

    config.RUN_METADATA = payload.get('run_metadata', {})

    script_config = {}
    for k, v in payload['config_keys'].items():
        script_config[k] = v

    script_config['calculate_metrics_aggregated'] = True
    script_config_module.script_config = script_config
    import output as _output_mod
    _output_mod.script_config = script_config

    n_metrics = len(payload['metrics_to_visualize'])
    _p(f"generating ({n_metrics} metrics)")
    t0 = time.time()

    if 'metric_experiments' in payload:
        metric_experiments_by_key = dict(payload['metric_experiments'])
    else:
        metric_experiments_by_key = {
            name: list(metrics.keys())
            for name, metrics in payload['metric_aggregation_experiments'].items()
        }

    visualize_metrics_aggregated(
        payload['metric_aggregation'],
        payload['metric_aggregation_experiments'],
        payload['metrics_to_visualize'],
        payload['metrics_to_visualize_special'],
        payload['canvas_metrics'],
        metric_experiments_by_key=metric_experiments_by_key,
    )

    # Per-OS output if data is present
    if 'metric_aggregation_by_os' in payload:
        from output import visualize_metrics_by_os
        _p(f"generating per-OS output")
        script_config['calculate_metrics_by_os'] = True
        script_config_module.script_config = script_config
        _output_mod.script_config = script_config
        visualize_metrics_by_os(
            payload['metric_aggregation_by_os'],
            {},  # metric_aggregation_by_os (non-accumulating) — not used in deferred path
            payload['metrics_to_visualize'],
            payload['metrics_to_visualize_special'],
            payload['canvas_metrics'],
        )

        # Per-OS Shannon entropy, HHI CSVs, and per-metric txt files
        from math import log2
        from cohort import cohort_fitness
        by_os_acc = payload['metric_aggregation_by_os']
        # Discover OS values from the data
        os_values = set()
        for metric, (total_counts, os_counts) in by_os_acc.items():
            os_values.update(os_counts.keys())
        os_values = sorted(os_values)

        if os_values:
            os_entropy = {os_val: {} for os_val in os_values}
            os_hhi = {os_val: {} for os_val in os_values}
            for metric in payload['metrics_to_visualize']:
                if metric not in by_os_acc:
                    continue
                _, os_counts = by_os_acc[metric]
                for os_val in os_values:
                    counts = os_counts.get(os_val, {})
                    total = sum(counts.values())
                    if total > 0:
                        entropy = -sum((c / total) * log2(c / total)
                                       for c in counts.values() if c > 0)
                        os_entropy[os_val][metric] = entropy
                        os_hhi[os_val][metric] = cohort_fitness(counts)

            for os_val in os_values:
                # Shannon entropy CSV
                entropy_path = os.path.join(output_dir, f"metric_shannon_entropy_os_{os_val}.csv")
                sorted_entropy = sorted(os_entropy[os_val].items(), key=lambda x: x[1], reverse=True)
                with open(entropy_path, 'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(['Metric', 'Entropy'])
                    for metric, val in sorted_entropy:
                        w.writerow([metric, val])
                print(f"  Per-OS Shannon entropy written to {entropy_path}")

                # HHI CSV
                hhi_path = os.path.join(output_dir, f"metric_hhi_os_{os_val}.csv")
                sorted_hhi = sorted(os_hhi[os_val].items(), key=lambda x: x[1])
                with open(hhi_path, 'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(['Metric', 'HHI'])
                    for metric, val in sorted_hhi:
                        w.writerow([metric, val])
                print(f"  Per-OS HHI written to {hhi_path}")

                # Per-metric txt files (value distribution tables)
                max_lines = config.PRINT_MAX_LINES
                for metric in payload['metrics_to_visualize']:
                    if metric not in by_os_acc:
                        continue
                    _, os_counts = by_os_acc[metric]
                    counts = os_counts.get(os_val, {})
                    if not counts:
                        continue
                    total = sum(counts.values())
                    data_keys = sorted(counts, key=counts.get, reverse=True)
                    max_key_len = max(len(str(k)) for k in data_keys)
                    max_key_len = max(max_key_len, len(f"{max_lines} Other Values"))

                    txt_path = os.path.join(output_dir, f"{metric}_os_{os_val}.txt")
                    with open(txt_path, 'w') as f:
                        f.write(f"  {metric} ({os_val})\n")
                        f.write(f"  {'-' * 60}\n")
                        f.write(f"  {'Key'.ljust(max_key_len)} {'Count':>8} {'%':>8} {'Cumulative %':>12}\n")
                        f.write(f"  {'-' * (max_key_len + 31)}\n")
                        cumulative = 0
                        for i, key in enumerate(data_keys):
                            if i >= max_lines:
                                other_count = sum(counts[k] for k in data_keys[i:])
                                cumulative += other_count / total * 100
                                f.write(f"  {str(len(data_keys) - max_lines) + ' Other Values':<{max_key_len}} "
                                        f"{other_count:>8} {other_count / total * 100:>7.2f}% {cumulative:>11.2f}%\n")
                                break
                            pct = counts[key] / total * 100
                            cumulative += pct
                            f.write(f"  {str(key):<{max_key_len}} {counts[key]:>8} {pct:>7.2f}% {cumulative:>11.2f}%\n")
                print(f"  Per-OS metric txt files written for {os_val}")

    del payload
    gc.collect()

    elapsed = time.time() - t0
    _p(f"done in {elapsed:.1f}s")

    with open(os.path.join(output_dir, "metric_aggregation_output.done"), "w") as f:
        f.write(f"generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

    config.stop_log_thread()
    config.run_log = None
    run_log_file.close()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dirs", nargs='+', help="Analysis output directory(ies) containing metric_aggregation_output.bin")
    parser.add_argument("-r", "--regen", action="store_true", help="Regenerate even if outputs already exist")
    args = parser.parse_args()

    print(f"gen_metrics_output — {len(args.output_dirs)} directory(ies)")
    for d in args.output_dirs:
        dirname = os.path.basename(os.path.abspath(d))
        print(f"   {dirname}/")
        process_one(d, regen=args.regen)


if __name__ == "__main__":
    main()
