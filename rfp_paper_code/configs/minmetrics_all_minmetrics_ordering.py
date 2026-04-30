"""MinMetrics prefix uniqueness curve — all 3 fingerprinters, minmetrics-reordered.

Uses the minmetrics marginal-contribution ordering instead of SMR ordering.
Metrics are reordered by how many NEW unique users each adds when appended
to the prefix, rather than standalone removal impact.
"""

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
    'perform_min_set_combo_analysis':            False,
    'correlation_analysis':               False,

    'perform_minmetrics_analysis':        True,
    'minmetrics_fingerprinter':           ['FPJSv2_Realistic', 'AkamaiV2_Realistic', 'Signifyd_Realistic'],
    'minmetrics_metric_source':           'minmetrics',
    'minmetrics_max_k':                   None,
    'minmetrics_per_os_use_overall_metrics': False,
    'smr_fingerprinters':                {'FPJSv2_Realistic', 'AkamaiV2_Realistic', 'Signifyd_Realistic'},
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
