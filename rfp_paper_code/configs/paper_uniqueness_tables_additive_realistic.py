"""Config for cumulative (additive) experiments only — realistic variants.

Same as paper_uniqueness_tables_additive.py but uses the _Realistic
fingerprinter variants (AkamaiV2/Signifyd/FPJSv2 without
screen_web_inner / screen_web_outer).
"""

from pathlib import Path

from fingerprinters import (
    FPSET_AKAMAI_V2_REALISTIC, FPSET_SIGNIFYD_REALISTIC,
    FPSET_FINGERPRINTJS_V2_REALISTIC,
)
from configs.gen_experiments import generate_experiments, build_metric_experiments

# ── Load experiments from CSV ────────────────────────────────────────────────
_csv_path = Path(__file__).parent / 'experiments.csv'
_all_exp, EXPERIMENTS_TO_RUN_ADDITIVE, EXPERIMENT_LONG_NAMES, _meta = generate_experiments(_csv_path)
EXPERIMENT_SLUG_MAP  = _meta['slug_map']
EXPERIMENT_EQUIVALENTS = _meta['equivalents']

# Only keep Baseline-Raw and P0-C experiments (needed as starting point for additive)
EXPERIMENTS_TO_RUN = {k: v for k, v in _all_exp.items() if k.startswith('Baseline') or k.startswith('P0-C')}

# ── script_config ────────────────────────────────────────────────────────────
script_config = {
    'per_os_analysis':              True,
    'print_x_by_os_aggregate_graphs':                    False,
    'raw_rows_only':                 False,
    'max_procs':               2,
    'max_worker_threads':    None,
    'max_threads_graph_export':      2,
    'max_threads_experiment_merging': 4,

    'calculate_metrics_aggregated':             False,
    'metrics_aggregated_output':                False,
    'calculate_metric_experiment_aggregated':   True,
    'show_special_metrics_aggregated':          False,
    'show_all_metrics_aggregated':              False,
    'print_x_aggregate_tables':                False,
    'print_x_aggregate_graphs':                False,
    'print_x_aggregate_entropy':               False,
    'print_x_hhi_index':                       False,

    'print_log_scale_also':                     False,

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

FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {
    "FPJSv2_Realistic": FPSET_FINGERPRINTJS_V2_REALISTIC,
    "AkamaiV2_Realistic": FPSET_AKAMAI_V2_REALISTIC,
    "Signifyd_Realistic": FPSET_SIGNIFYD_REALISTIC,
}

FINGERPRINTERS_FOR_EXPERIMENTS = {
    "FPJSv2_Realistic": FPSET_FINGERPRINTJS_V2_REALISTIC,
    "AkamaiV2_Realistic": FPSET_AKAMAI_V2_REALISTIC,
    "Signifyd_Realistic": FPSET_SIGNIFYD_REALISTIC,
}

FINGERPRINTERS_FOR_MODES = {
    "FPJSv2_Realistic": FPSET_FINGERPRINTJS_V2_REALISTIC,
    "AkamaiV2_Realistic": FPSET_AKAMAI_V2_REALISTIC,
    "Signifyd_Realistic": FPSET_SIGNIFYD_REALISTIC,
}

METRIC_EXPERIMENTS_BY_KEY = build_metric_experiments(EXPERIMENTS_TO_RUN, EXPERIMENTS_TO_RUN_ADDITIVE)
METRIC_EXPERIMENTS = list(METRIC_EXPERIMENTS_BY_KEY.items())

CALCULATIONS_FOR_ARCHIVING = []
