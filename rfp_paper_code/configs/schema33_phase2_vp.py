"""Value-predictability config for schema33 data (tmp_0322_01), phase2 metric set.

Uses the phase2fp=1 metrics from metadata_metric_name_mapping.txt.

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./value_predictability.py --cache-dir /work/sandbox-cache \
    -c configs/schema33_phase2_vp.py \
    -o /work/sandbox-analyses/schema33-full-02/value_pred
"""

import os

from settings import BQ_PROJECT_ID

# ---------------------------------------------------------------------------
# Build phase2 metric set from the authoritative mapping file
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_MAPPING = os.path.join(_HERE, 'metadata_metric_name_mapping.txt')

CORRELATION_BQ_TABLE = f'{BQ_PROJECT_ID}.tmp_0322_01.UserCharacteristics_x_by_y_tbl'

# Read db_names where phase2fp == 1, skipping absent (~) entries.
CORRELATION_METRIC_SET = set()
with open(_MAPPING) as _f:
    for _line in _f:
        _line = _line.strip()
        if not _line or _line.startswith('#'):
            continue
        _parts = _line.split()
        if len(_parts) >= 3 and _parts[2] == '1':
            _db_name = _parts[1]
            if not _db_name.startswith('~'):
                CORRELATION_METRIC_SET.add(_db_name)

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
