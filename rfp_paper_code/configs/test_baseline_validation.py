"""Minimal config for validating the baseline change.

Runs:
- All-Data fingerprints (3 fingerprinters)
- Cumulative experiments: P0-C steps + first 2 P1-C steps (via additive chain)
- Individual experiments: P0-I (3) + P1-I fdLibm
"""

from pathlib import Path

from fingerprinters import (
    FPSET_FINGERPRINTJS_V2, FPSET_AKAMAI_V2, FPSET_SIGNIFYD,
)
from configs.gen_experiments import generate_experiments

# ── Load experiments from CSV ────────────────────────────────────────────────
_csv_path = Path(__file__).parent / 'experiments.csv'
_all_exp, _all_additive, EXPERIMENT_LONG_NAMES, _meta = generate_experiments(_csv_path)
EXPERIMENT_SLUG_MAP = _meta['slug_map']
EXPERIMENT_EQUIVALENTS = _meta['equivalents']

# Individual: P0-I experiments + one P1-I
EXPERIMENTS_TO_RUN = {k: v for k, v in _all_exp.items()
                      if k.startswith('P0-I') or k.startswith('Baseline')
                      or k == 'P1-I: fdLibm'}

# Additive: P0-C steps + truncate after P1-C: fdLibm
_trimmed = {}
_stop_after = 'P1-C: fdLibm'
for k, v in _all_additive[0].items():
    _trimmed[k] = v
    if k == _stop_after:
        break
EXPERIMENTS_TO_RUN_ADDITIVE = [_trimmed]

# ── script_config ────────────────────────────────────────────────────────────
script_config = {
    'per_os_analysis':              False,
    'raw_rows_only':                 False,
    'max_procs':                     4,
    'max_worker_threads':            None,
    'max_threads_graph_export':      1,
    'max_threads_experiment_merging': 4,

    'calculate_metrics_aggregated':                     False,
    'calculate_metric_experiment_aggregated':            False,
    'fingerprints':                     True,
    'fingerprints_output':              True,
    'browser_modes':                    False,
    'experiments':                      True,
    'experiments_output':                True,
    'print_cohort_size_tables':         False,

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
    'perform_logical_metric_removal_analysis':   False,
    'correlation_analysis':               False,
}


FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {
    "FPJSv2": FPSET_FINGERPRINTJS_V2,
    "AkamaiV2": FPSET_AKAMAI_V2,
    "Signifyd": FPSET_SIGNIFYD,
}
FINGERPRINTERS_FOR_MODES = {}
FINGERPRINTERS_FOR_EXPERIMENTS = {
    "FPJSv2": FPSET_FINGERPRINTJS_V2,
    "AkamaiV2": FPSET_AKAMAI_V2,
    "Signifyd": FPSET_SIGNIFYD,
}
CALCULATIONS_FOR_ARCHIVING = []
METRIC_EXPERIMENTS = []
METRIC_EXPERIMENTS_BY_KEY = {}
