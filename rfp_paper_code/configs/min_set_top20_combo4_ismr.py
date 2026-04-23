"""Min-set combo analysis: top 20 metrics, combo sizes 1–3, per-OS.

Tests all C(20,k) combinations for k=1..3 using per-OS ISMR orderings.
C(20,3) = 1140 combos per OS.
"""

from settings import MIN_SET_METRIC_AGGREGATION_PATH

script_config = {
    'per_os_analysis':              'only',
    'print_x_by_os_aggregate_graphs':                    False,
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
    'missing_font_sets':                    False,
    'perform_segmentation_shitty':              False,
    'perform_segmentation_decision_tree':       False,
    'perform_single_metric_removal_analysis':             False,
    'perform_iterative_single_metric_removal_analysis':   False,
    'perform_iterative_single_metric_replacement_analysis': False,
    'perform_logical_metric_removal_analysis':   False,
    'correlation_analysis':               False,

    'perform_min_set_combo_analysis':     True,
    'min_set_combo_sizes':               {4: 20},
    'min_set_combo_fingerprinter':       'FPJSv2',
    'min_set_combo_metric_source':       'ismr',
    'min_set_combo_per_os_use_overall_metrics': False,
    'min_set_metric_aggregation_path':   MIN_SET_METRIC_AGGREGATION_PATH,
    'smr_fingerprinters':                {'FPJSv2'},
    'perform_single_metric_removal_analysis_exclude_set': set(),
    'perform_single_metric_removal_analysis_override_set': set(),
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
