"""Iterative MinMetrics — greedy forward selection for AkamaiV2_Realistic."""

script_config = {
    'per_os_analysis':              True,
    'print_x_by_os_aggregate_graphs':                    False,
    'raw_rows_only':                 False,
    'max_procs':                     2,
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
    'perform_min_set_combo_analysis':            False,
    'perform_minmetrics_analysis':               False,
    'correlation_analysis':               False,

    'perform_iterative_minmetrics_analysis':  True,
    'iterative_minmetrics_fingerprinter':     'AkamaiV2_Realistic',
    'iterative_minmetrics_max_k':            None,
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
