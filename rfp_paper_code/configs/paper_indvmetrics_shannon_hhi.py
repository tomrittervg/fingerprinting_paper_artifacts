"""Analysis configuration for generating Individual Metric Analysis table data.

Enables Shannon entropy and HHI index output for use in the paper's
Individual Metric Analysis table.  All heavy analyses (fingerprints,
experiments, segmentation, etc.) are disabled to keep runs fast.

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./analyze.py --start-day YYYYMMDD --end-day YYYYMMDD \
    -o /home/sandbox/tmp --cache-dir /work/sandbox-cache \
    -c configs/paper_indvmetrics_shannon_hhi.py --skip-progress-bars
"""

from fingerprinters import (
    FPSET_AKAMAI_V2, FPSET_SIFT_SCIENCE, FPSET_FINGERPRINTJS_V1,
)

script_config = {
    'per_os_analysis':              True,
    'print_x_by_os_aggregate_graphs':                    False,
    'raw_rows_only':                 False,
    'max_procs':               10,
    'max_worker_threads':    None,  # threads per worker for parallelizing operations; None = auto (floor(100 / max_procs))
    'max_threads_graph_export':      16,
    'max_threads_experiment_merging': 4,

    # -------------------
    'calculate_metrics_aggregated':     True,
    'calculate_metric_experiment_aggregated':     False,
    'show_special_metrics_aggregated':  False,
    'show_all_metrics_aggregated':      True,
    'print_x_aggregate_tables':         True,
    'print_x_aggregate_graphs':         False,
    'print_x_aggregate_entropy':        True,   # <-- enabled for paper
    'print_x_hhi_index':                True,   # <-- enabled for paper
    'metrics_aggregated_output':        False,

    # -------------------
    'print_log_scale_also':             False,

    # -------------------
    'fingerprints':                     False,
    'browser_modes':                    False,
    'experiments':                      False,
    # -------------------
    'fingerprint_buckets':              False,
    'metric_buckets':                   False,

    # -------------------
    'fingerprint_archiving':            False,

    # -------------------
    'missing_fonts':                    False,
    'missing_font_sets':                False,

    # -------------------
    'perform_segmentation_shitty':              False,
    'perform_segmentation_decision_tree':       False,

    # -------------------
    'perform_single_metric_removal_analysis':      False,
    'perform_iterative_single_metric_removal_analysis': False,

    'perform_iterative_single_metric_replacement_analysis': False,
    'perform_min_set_combo_analysis':       False,

    'perform_logical_metric_removal_analysis':   False,
    'correlation_analysis':               False,
}


def num_modes_enabled(sc):
    return sum([
        sc['fingerprints'],
        sc['browser_modes'],
        sc['experiments'],
        sc['fingerprint_buckets'],
        sc['metric_buckets'],
        sc['fingerprint_archiving'],
        sc['missing_fonts'],
        sc['perform_segmentation_shitty'],
        sc['perform_segmentation_decision_tree'],
        sc['perform_single_metric_removal_analysis'],
        sc['perform_iterative_single_metric_removal_analysis']
    ])


def should_keep_sequencing(sc):
    return num_modes_enabled(sc) > 1


# Required exports (all disabled since fingerprints/experiments/archiving are off)
FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {}
METRIC_EXPERIMENTS = []
METRIC_EXPERIMENTS_BY_KEY = {}
CALCULATIONS_FOR_ARCHIVING = []
FINGERPRINTERS_FOR_EXPERIMENTS = {}
FINGERPRINTERS_FOR_MODES = {}
EXPERIMENTS_TO_RUN = {}
EXPERIMENTS_TO_RUN_ADDITIVE = []
EXPERIMENT_LONG_NAMES          = {}
