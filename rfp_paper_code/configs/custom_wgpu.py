"""Custom function: aggregate counts of wgpu metric combinations by OS.

For each user, records the tuple of (os, combined_wgpu_hash, wgpu_is_fallback_adapter,
wgpu_missing_features, and all individual wgpu limit values) and counts how many
users share each exact combination.

Run with:
    ./run.sh -o /tmp/wgpu -c configs/custom_wgpu.py
"""
from collections import defaultdict

WGPU_METRICS = [
    'combined_wgpu_hash',
    'wgpu_is_fallback_adapter',
    'wgpu_missing_features',
    'wgpu_maxbindgroups',
    'wgpu_maxbindgroupsplusvertexbuffers',
    'wgpu_maxbindingsperbindgroup',
    'wgpu_maxbuffersize',
    'wgpu_maxcolorattachmentbytespersample',
    'wgpu_maxcolorattachments',
    'wgpu_maxcomputeinvocationsperworkgroup',
    'wgpu_maxcomputeworkgroupsizex',
    'wgpu_maxcomputeworkgroupsizey',
    'wgpu_maxcomputeworkgroupsizez',
    'wgpu_maxcomputeworkgroupsperdimension',
    'wgpu_maxcomputeworkgroupstoragesize',
    'wgpu_maxdynamicstoragebuffersperpipelinelayout',
    'wgpu_maxdynamicuniformbuffersperpipelinelayout',
    'wgpu_maxinterstageshadervariables',
    'wgpu_maxsampledtexturespershaderstage',
    'wgpu_maxsamplerspershaderstage',
    'wgpu_maxstoragebufferbindingsize',
    'wgpu_maxstoragebufferspershaderstage',
    'wgpu_maxstoragetexturespershaderstage',
    'wgpu_maxtexturearraylayers',
    'wgpu_maxtexturedimension1d',
    'wgpu_maxtexturedimension2d',
    'wgpu_maxtexturedimension3d',
    'wgpu_maxuniformbufferbindingsize',
    'wgpu_maxuniformbufferspershaderstage',
    'wgpu_maxvertexattributes',
    'wgpu_maxvertexbufferarraystride',
    'wgpu_maxvertexbuffers',
    'wgpu_minstoragebufferoffsetalignment',
    'wgpu_minuniformbufferoffsetalignment',
]


def _init():
    return defaultdict(int)


def _map(dv, acc):
    os_val = dv.os
    vals = tuple(str(getattr(dv, m)) for m in WGPU_METRICS)
    acc[(os_val, vals)] += 1


def _merge(global_acc, worker_acc):
    for k, v in worker_acc.items():
        global_acc[k] += v


def _output(acc, output_dir):
    import csv, os
    path = os.path.join(output_dir, 'wgpu_combinations.csv')
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['os', 'count'] + WGPU_METRICS)
        for (os_val, vals), count in sorted(acc.items(), key=lambda x: (-x[1])):
            w.writerow([os_val, count] + list(vals))
    n_combos = len(acc)
    n_users = sum(acc.values())
    n_unique = sum(1 for v in acc.values() if v == 1)
    print(f"  Wrote {path}")
    print(f"    {n_users:,} users, {n_combos:,} unique combinations, "
          f"{n_unique:,} singletons ({n_unique/n_users*100:.1f}%)")

    # Also write a summary by OS
    os_stats = defaultdict(lambda: {'total': 0, 'combos': 0, 'singletons': 0})
    for (os_val, vals), count in acc.items():
        os_stats[os_val]['total'] += count
        os_stats[os_val]['combos'] += 1
        if count == 1:
            os_stats[os_val]['singletons'] += 1

    summary_path = os.path.join(output_dir, 'wgpu_combinations_summary.csv')
    with open(summary_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['os', 'total_users', 'unique_combinations', 'singletons', 'pct_singleton'])
        for os_val in sorted(os_stats):
            s = os_stats[os_val]
            pct = s['singletons'] / s['total'] * 100 if s['total'] else 0
            w.writerow([os_val, s['total'], s['combos'], s['singletons'], f"{pct:.2f}"])
    print(f"  Wrote {summary_path}")


CUSTOM_FUNCTIONS = [
    {
        'name': 'wgpu_combos',
        'init': _init,
        'map': _map,
        'merge': _merge,
        'output': _output,
    },
]

script_config = {
    'per_os_analysis':              False,
    'raw_rows_only':                 False,
    'max_procs':                     16,
    'max_worker_threads':            None,
    'max_threads_graph_export':      1,
    'max_threads_experiment_merging': 4,

    'calculate_metrics_aggregated':                     False,
    'calculate_metric_experiment_aggregated':            False,
    'fingerprints':                     False,
    'browser_modes':                    False,
    'experiments':                      False,
    'fingerprint_buckets':              False,
    'metric_buckets':                   False,
    'fingerprint_archiving':            False,
    'missing_fonts':                    False,
    'missing_font_sets':                False,
    'perform_segmentation_shitty':              False,
    'perform_segmentation_decision_tree':       False,
    'perform_single_metric_removal_analysis':   False,
    'perform_iterative_single_metric_removal_analysis': False,
    'perform_iterative_single_metric_replacement_analysis': False,
    'perform_min_set_combo_analysis':       False,
    'perform_logical_metric_removal_analysis':   False,
    'correlation_analysis':               False,
}

FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {}
FINGERPRINTERS_FOR_MODES = {}
FINGERPRINTERS_FOR_EXPERIMENTS = {}
CALCULATIONS_FOR_ARCHIVING = []
EXPERIMENTS_TO_RUN = {}
EXPERIMENTS_TO_RUN_ADDITIVE = []
METRIC_EXPERIMENTS = []
METRIC_EXPERIMENTS_BY_KEY = {}
EXPERIMENT_LONG_NAMES = {}
