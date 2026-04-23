"""Config for generating paper Tables 1, 3, and 4: experiment uniqueness results.

Runs all experiments (individual + cumulative) against three fingerprinters:
FPJSv2 (Fingerprint Pro), AkamaiV2 (Akamai), Signifyd.

Usage:
    ./analyze.py --start-day YYYYMMDD --end-day YYYYMMDD \
        -o <output-dir> --cache-dir <cache-dir> \
        -c configs/paper_uniqueness_tables.py \
        --partition-width 2
"""

from pathlib import Path

from fingerprinters import (
    FPSET_FINGERPRINTJS_V2, FPSET_AKAMAI_V2, FPSET_SIGNIFYD,
    FPSET_SIFT_SCIENCE, FPSET_AKAMAI_V1, FPSET_FINGERPRINTJS_V1,
)
from configs.gen_experiments import generate_experiments, build_metric_experiments

# ── Load experiments from CSV ────────────────────────────────────────────────
_csv_path = Path(__file__).parent / 'experiments.csv'
EXPERIMENTS_TO_RUN, EXPERIMENTS_TO_RUN_ADDITIVE, EXPERIMENT_LONG_NAMES, _meta = generate_experiments(_csv_path)
EXPERIMENT_SLUG_MAP  = _meta['slug_map']
EXPERIMENT_EQUIVALENTS = _meta['equivalents']

# ── script_config ────────────────────────────────────────────────────────────
script_config = {
    'per_os_analysis':              False,
    'raw_rows_only':                 False,
    'max_procs':               18,
    'max_worker_threads':    None,  # threads per worker for parallelizing operations; None = auto (floor(100 / max_procs))
    'max_threads_graph_export':      2,
    'max_threads_experiment_merging': 4,

    # Metric aggregation — needed for per-metric experiment data
    'calculate_metrics_aggregated':             False,
    'metrics_aggregated_output':        False,
    'calculate_metric_experiment_aggregated':   True,
    'show_special_metrics_aggregated':          False,
    'show_all_metrics_aggregated':              False,
    'print_x_aggregate_tables':                False,
    'print_x_aggregate_graphs':                False,
    'print_x_aggregate_entropy':               False,
    'print_x_hhi_index':                       False,

    'print_log_scale_also':                     False,

    # Fingerprints + experiments
    'fingerprints':                  True,
    'fingerprints_output':           False,
    'experiments':                   True,
    'browser_modes':                 True,
    'experiments_output':            False,
    'modes_output':                  False,
    'print_cohort_size_tables':      True,

    'fingerprint_buckets':           False,
    'metric_buckets':                False,
    'fingerprint_archiving':         False,

    'missing_fonts':                 False,
    'missing_font_sets':             False,

    'perform_segmentation_shitty':              False,
    'perform_segmentation_decision_tree':       False,

    'perform_single_metric_removal_analysis':      False,
    'perform_iterative_single_metric_removal_analysis': False,
    'perform_iterative_single_metric_replacement_analysis': False,
    'perform_min_set_combo_analysis':       False,

    'perform_logical_metric_removal_analysis':   False,
    'correlation_analysis':               False,
}

# ── Fingerprinters: all 3, for all analysis types ────────────────────────────
FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {
    "FPJSv2": FPSET_FINGERPRINTJS_V2,
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
    "AkamaiV2": FPSET_AKAMAI_V2,
    "AkamaiV1": FPSET_AKAMAI_V1,
    "Signifyd": FPSET_SIGNIFYD,
    "SiftScience": FPSET_SIFT_SCIENCE,
}

FINGERPRINTERS_FOR_EXPERIMENTS = {
    "FPJSv2": FPSET_FINGERPRINTJS_V2,
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
    "AkamaiV2": FPSET_AKAMAI_V2,
    "AkamaiV1": FPSET_AKAMAI_V1,
    "Signifyd": FPSET_SIGNIFYD,
    "SiftScience": FPSET_SIFT_SCIENCE,
}

FINGERPRINTERS_FOR_MODES = {
    "FPJSv2": FPSET_FINGERPRINTJS_V2,
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
    "AkamaiV2": FPSET_AKAMAI_V2,
    "AkamaiV1": FPSET_AKAMAI_V1,
    "Signifyd": FPSET_SIGNIFYD,
    "SiftScience": FPSET_SIFT_SCIENCE,
}

# ── Metric experiments (auto-built from filter affected_metrics) ─────────────
METRIC_EXPERIMENTS_BY_KEY = build_metric_experiments(EXPERIMENTS_TO_RUN, EXPERIMENTS_TO_RUN_ADDITIVE)
METRIC_EXPERIMENTS = list(METRIC_EXPERIMENTS_BY_KEY.items())

# ── Archiving (disabled) ────────────────────────────────────────────────────
CALCULATIONS_FOR_ARCHIVING = []
