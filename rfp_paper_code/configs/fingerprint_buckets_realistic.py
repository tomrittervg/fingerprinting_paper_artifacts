"""Minimal config to compute fingerprint uniqueness for AkamaiV2_Realistic,
Signifyd_Realistic, FPJSv2_Realistic (same as fingerprint_buckets.py but with
the realistic variants that drop screen_web_inner/outer).
"""

from fingerprinters import (
    FPSET_AKAMAI_V2_REALISTIC, FPSET_SIGNIFYD_REALISTIC, FPSET_FINGERPRINTJS_V2_REALISTIC,
)

script_config = {
    'per_os_analysis':              True,
    'print_x_by_os_aggregate_graphs':                    False,
    'raw_rows_only':                 False,
    'max_procs':               2,
    'max_worker_threads':    None,  # threads per worker for parallelizing operations; None = auto (floor(100 / max_procs))
    'max_threads_graph_export':      16,
    'max_threads_experiment_merging': 4,

    'calculate_metrics_aggregated':                     False,
    'calculate_metric_experiment_aggregated':           False,
    'fingerprints':                     True,
    'fingerprints_output':              False,
    'browser_modes':                    False,
    'experiments':                      False,
    'print_cohort_size_tables':         False,

    'fingerprint_buckets':              True,
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


FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {
    "AkamaiV2_Realistic":  FPSET_AKAMAI_V2_REALISTIC,
    "Signifyd_Realistic":  FPSET_SIGNIFYD_REALISTIC,
    "FPJSv2_Realistic":    FPSET_FINGERPRINTJS_V2_REALISTIC,
}

FINGERPRINTERS_FOR_MODES      = {}
FINGERPRINTERS_FOR_EXPERIMENTS = {}
CALCULATIONS_FOR_ARCHIVING    = []
EXPERIMENTS_TO_RUN            = {}
EXPERIMENTS_TO_RUN_ADDITIVE   = []
EXPERIMENT_LONG_NAMES          = {}
METRIC_EXPERIMENTS            = []
METRIC_EXPERIMENTS_BY_KEY     = {}
