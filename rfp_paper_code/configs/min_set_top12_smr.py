"""Min-set combo analysis: top 12 metrics, combo sizes 1–5, per-OS.

Tests all C(12,k) combinations for k=1..5 using per-OS SMR orderings.
"""

from settings import MIN_SET_METRIC_AGGREGATION_PATH

script_config = {
    'per_os_analysis':              True,
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
    'min_set_combo_sizes':               {1: 12, 2: 12, 3: 12, 4: 12, 5: 12},
    'min_set_combo_fingerprinter':       'FPJSv2',
    'min_set_combo_metric_source':       'smr',
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
