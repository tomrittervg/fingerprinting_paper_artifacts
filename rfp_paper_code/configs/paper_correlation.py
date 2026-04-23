"""Analysis configuration for correlation analysis (AMI + Theil's U).

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./correlation.py --cache-dir /work/sandbox-cache \
    -c configs/paper_correlation.py \
    -o /home/sandbox/tmp

  Add --cache-only to download data without running analysis.
"""

from fingerprinters import (
    FPSET_AKAMAI_V2, FPSET_SIFT_SCIENCE, FPSET_FINGERPRINTJS_V1,
    FPSET_FINGERPRINTJS_V2, FPSET_SIGNIFYD,
)
from settings import BQ_PROJECT_ID

# ---------------------------------------------------------------------------
# Correlation-specific exports
# ---------------------------------------------------------------------------

CORRELATION_BQ_TABLE = f'{BQ_PROJECT_ID}.tmp_0316_1.UserCharacteristics_x_by_y_tbl'

# Set of metrics to analyze. Use None for all metrics in the BQ table.
# Combine fingerprinter sets with | (union):
CORRELATION_METRIC_SET = None  # all metrics

# ---------------------------------------------------------------------------
# Standard script_config (correlation keys only matter here)
# ---------------------------------------------------------------------------

script_config = {
    'per_os_analysis':              False,
    'raw_rows_only':                 False,
    'max_procs':               16,
    'max_worker_threads':    None,  # threads per worker for parallelizing operations; None = auto (floor(100 / max_procs))
    'max_threads_graph_export':      16,
    'max_threads_experiment_merging': 4,

    'calculate_metrics_aggregated':                     False,
    'calculate_metric_experiment_aggregated':           False,
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

    # --- Correlation analysis ---
    'correlation_analysis':               True,
    'correlation_cache_only':             False,
    'correlation_parallel_downloads':     8,
    'correlation_parallel_workers':       48,
    'correlation_missing_values':         {'None'},
    'correlation_ami':                    True,
    'correlation_ami_bin_rare_values':    True,
    'correlation_ami_bin_thresholds':     [30],
    'correlation_ami_miller_madow':       False,
    'correlation_theil_u':                True,

    'perform_logical_metric_removal_analysis':   False,
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
        sc['perform_iterative_single_metric_removal_analysis'],
    ])


def should_keep_sequencing(sc):
    return num_modes_enabled(sc) > 1


FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {}
FINGERPRINTERS_FOR_MODES      = {}
FINGERPRINTERS_FOR_EXPERIMENTS = {}
CALCULATIONS_FOR_ARCHIVING    = []
EXPERIMENTS_TO_RUN            = {}
EXPERIMENTS_TO_RUN_ADDITIVE   = []
EXPERIMENT_LONG_NAMES          = {}
METRIC_EXPERIMENTS            = []
METRIC_EXPERIMENTS_BY_KEY     = {}
