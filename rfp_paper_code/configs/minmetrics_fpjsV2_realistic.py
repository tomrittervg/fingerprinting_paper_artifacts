"""MinMetrics prefix uniqueness curve — FPJSv2_Realistic, SMR ordering.

For each K from 1 to len(SMR_TOP_METRICS) (52), compute the fingerprint
formed by XOR'ing the first K metrics of the SMR ordering and count how many
users have a unique fingerprint. Output a CSV + ASCII table per OS showing
how uniqueness grows with K.

Fingerprint-specific: uses the FPJSv2_Realistic ISMR cache and the
FPJSv2_Realistic SMR ordering from min_set_per_user.py.
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
    'minmetrics_fingerprinter':           'FPJSv2_Realistic',
    'minmetrics_metric_source':           'smr',
    'minmetrics_max_k':                   None,   # None = use full ordering length
    'minmetrics_per_os_use_overall_metrics': False,
    'smr_fingerprinters':                {'FPJSv2_Realistic'},
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
