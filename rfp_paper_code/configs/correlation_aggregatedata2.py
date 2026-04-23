"""Per-OS correlation analysis config for the aggregatedata2 dataset.

Run once per OS by setting CORRELATION_OS before importing, or edit the
CORRELATION_OS line below:

  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  PYTHON_GIL=0 \
  ./correlation.py --cache-dir /work/sandbox-cache \
    -c configs/correlation_aggregatedata2.py \
    -o /home/sandbox/tmp --skip-progress-bars

  Add --cache-only to download data without running analysis.

To change OS, edit CORRELATION_OS below or set the CORRELATION_OS env var:
  CORRELATION_OS=Mac ./correlation.py ...
"""

import os

from fingerprinters import (
    FPSET_AKAMAI_V2, FPSET_SIFT_SCIENCE, FPSET_FINGERPRINTJS_V1,
    FPSET_FINGERPRINTJS_V2, FPSET_SIGNIFYD,
)
from settings import BQ_PROJECT_ID

# ---------------------------------------------------------------------------
# Correlation-specific exports
# ---------------------------------------------------------------------------

# Set which OS to analyze: Windows, Mac, Linux, Android, or All (merged)
CORRELATION_OS = os.environ.get('CORRELATION_OS', 'Windows')

CORRELATION_BQ_TABLE = (
    f'{BQ_PROJECT_ID}.aggregatedata2'
    f'.UserCharacteristics_{CORRELATION_OS}_x_by_y_tbl'
)

# None = all metrics in the table
CORRELATION_METRIC_SET = None

# ---------------------------------------------------------------------------
# Standard script_config
# ---------------------------------------------------------------------------

script_config = {
    'raw_rows_only':                 False,
    'max_procs':               16,
    'max_worker_threads':    None,
    'max_threads_graph_export':      16,
    'max_threads_experiment_merging': 4,

    'calculate_metrics_aggregated':                     False,
    'calculate_metric_experiment_aggregated':           False,
    'show_special_metrics_aggregated':                   False,
    'show_all_metrics_aggregated':                       False,
    'print_x_aggregate_tables':                          False,
    'print_x_aggregate_graphs':                          False,
    'print_x_aggregate_entropy':                         False,
    'print_x_hhi_index':                                 False,
    'print_log_scale_also':                              False,
    'metrics_aggregated_output':                         False,

    'fingerprints':                                      False,
    'fingerprints_output':                               False,
    'print_cohort_size_tables':                          False,
    'fingerprint_archiving':                              False,
    'fingerprint_buckets':                                False,
    'metric_buckets':                                     False,

    'experiments':                                        False,
    'experiments_output':                                  False,
    'browser_modes':                                      False,
    'modes_output':                                        False,

    'missing_fonts':                                      False,

    'perform_single_metric_removal_analysis':             False,
    'perform_logical_metric_removal_analysis':            False,
    'perform_min_set_combo_analysis':                     False,
    'perform_iterative_smr_analysis':                     False,

    'correlation_cache_only':                             False,
    'correlation_analysis':                               True,

    'correlation_ami':                                     True,
    'correlation_theil_u':                                 True,
    'correlation_ami_bin_rare':                            True,
    'correlation_ami_bin_thresholds':                     [10],
    'correlation_ami_miller_madow':                        True,
    'correlation_parallel_workers':                        16,
    'correlation_parallel_downloads':                       8,
}
