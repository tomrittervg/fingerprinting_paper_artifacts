"""Analysis configuration: metric aggregation + experiments + cumulative experiments + SMR.

Builds on configs/metrics.py but also enables:
  - experiments (individual, from raw baseline)
  - calculate_metric_experiment_aggregated (per-metric impact of each experiment)
  - EXPERIMENTS_TO_RUN_ADDITIVE (cumulative Phase 1→2→3→4 progression)
  - perform_single_metric_removal_analysis (SMR)
"""

from fingerprinters import (
    FPSET_AKAMAI_V2, FPSET_SIFT_SCIENCE, FPSET_FINGERPRINTJS_V1,
)
from experiments import (
    fdlibmFilter, procCountFilter, touchPointFilter, webGLVendorRendererFilter,
    canvasToSoftwareFilter, timezoneFilter, noProcessorCountFilter,
    fontListUpdatesFilter, fontListUpdatesFilterLocaleConsideration,
    acceptLanguageLimitFilter, acceptLanguageCollapseFilter,
    acceptLanguageLimitAndCollapseFilter,
    removeMinorVersionProtection, noWebGLRendererSanitizing,
    fontProtectionsFilter, screenAvailFilter,
    addGamePadProtection, addMediaCountProtection,
    shippingMissingFontsFilter,
)
from modes import rfpFilter

script_config = {
    'per_os_analysis':              False,
    'raw_rows_only':                 False,
    'max_procs':               8,
    'max_worker_threads':    None,  # threads per worker for parallelizing operations; None = auto (floor(100 / max_procs))
    'max_threads_graph_export':      16,
    'max_threads_experiment_merging': 4,

    # Metric aggregation
    'calculate_metrics_aggregated':              True,
    'calculate_metric_experiment_aggregated':    True,
    'show_special_metrics_aggregated':           False,
    'show_all_metrics_aggregated':               True,
    'print_x_aggregate_tables':                  True,
    'print_x_aggregate_graphs':                  False,
    'print_x_aggregate_entropy':                 False,
    'print_x_hhi_index':                         False,
    'metrics_aggregated_output':                 False,

    'print_log_scale_also':                      False,

    # Fingerprints / experiments / modes
    'fingerprints':                              False,
    'browser_modes':                             False,
    'experiments':                               True,
    'experiments_output':                        False,
    'print_cohort_size_tables':                  True,

    # Buckets / archiving / fonts
    'fingerprint_buckets':                       False,
    'metric_buckets':                            False,
    'fingerprint_archiving':                     False,
    'missing_fonts':                             False,
    'missing_font_sets':                         False,

    # Segmentation
    'perform_segmentation_shitty':               False,
    'perform_segmentation_decision_tree':        False,

    # SMR
    'perform_single_metric_removal_analysis':           True,
    'perform_iterative_single_metric_removal_analysis': False,
    'smr_output':                                       False,
    'smr_fingerprinters':                {'AkamaiV2', 'FPJSv2', 'Signifyd'},
    'perform_single_metric_removal_analysis_exclude_set': set(),
    'perform_single_metric_removal_analysis_override_set': set(),
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


# =============================================================================
# Fingerprinter / experiment constants
# =============================================================================

FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {
    "AkamaiV2": FPSET_AKAMAI_V2,
}

METRIC_EXPERIMENTS = [
    ("P1-IB: fdLibm",                             [f'math_op_{i}' for i in range(24)]),
    ("P2-IB: Processor Count",                    ["hw_processor_count"]),
    ("P2-IB: Touch Points",                       ["hw_max_touch_points"]),
    ("P2-IB: WebGL Vendor",                       ["webgl_vendor"]),
    ("P3-IB: Software Canvas",                    [
        "canvas_canvasdata01",
        "canvas_canvasdata02",
        "canvas_canvasdata03",
        "canvas_canvasdata04",
        "canvas_canvasdata05",
        "canvas_canvasdata06",
        "canvas_canvasdata07",
        "canvas_canvasdata08",
        "canvas_canvasdata09",
        "canvas_canvasdata10",
        "canvas_canvasdata11_webgl",
        "canvas_canvasdata12_fingerprintjs1",
        "canvas_canvasdata13_fingerprintjs2",
    ]),
    ("P3-IB: Timezone",                           ["intl_timezone"]),
    ("P0-I: Minor Version",                       ["hw_processor_count"]),
    ("P2-IB: OLD Font Updates",                   ["fonts_fpjs_allowlisted"]),
    ("P2-IB: Font Updates",                       ["fonts_fpjs_allowlisted"]),
    ("PZ-IB: Accept Language Limit To One",       ["locale_accept_language"]),
    ("PZ-IB: Accept Language Collapse",           ["locale_accept_language"]),
    ("P3-IB: Accept Language Limit and Collapse", ["locale_accept_language"]),
]

METRIC_EXPERIMENTS_BY_KEY = {key: metrics for key, metrics in METRIC_EXPERIMENTS}

CALCULATIONS_FOR_ARCHIVING = []

FINGERPRINTERS_FOR_EXPERIMENTS = {
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
}

FINGERPRINTERS_FOR_MODES = {
    "AkamaiV2": FPSET_AKAMAI_V2,
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
}

EXPERIMENTS_TO_RUN = {
    # --- P0: Cumulative removal (baseline without protections) ---
    'P0-C: Raw': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter],
    'P0-CI: ProcCount': [removeMinorVersionProtection, noWebGLRendererSanitizing],
    'P0-C: ProcCount, WebGLRenderer Sanitizing': [removeMinorVersionProtection],

    # --- P0: Individual isolation ---
    'P0-I: Minor Version': [noWebGLRendererSanitizing, noProcessorCountFilter],
    'P0-I: WebGLRenderer Sanitizing': [removeMinorVersionProtection, noProcessorCountFilter],
    'P0-I: GamePad': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, addGamePadProtection],
    'P0-I: Media Count': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, addMediaCountProtection],

    # --- P1–P4: Individual from-raw ---
    'P1-IB: Font Protections': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, fontProtectionsFilter],
    "P1-IB: fdLibm": [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, fdlibmFilter],

    'P2-IB: Processor Count': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, procCountFilter],
    'P2-IB: Screen Availability': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, screenAvailFilter],
    'P2-IB: Touch Points': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, touchPointFilter],
    'P2-IB: OLD Font Updates': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, fontListUpdatesFilter],
    'P2-IB: Font Updates': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, fontListUpdatesFilterLocaleConsideration],
    'P2-IB: WebGL Vendor': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, webGLVendorRendererFilter],

    'P3-IB: Software Canvas': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, canvasToSoftwareFilter],
    "P3-IB: Accept Language Limit and Collapse": [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, acceptLanguageLimitAndCollapseFilter],
    "P3-IB: Timezone": [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, timezoneFilter],

    'P4-IB: Shipping Missing Fonts': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, shippingMissingFontsFilter],

    'PZ-IB: Accept Language Limit To One': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, acceptLanguageLimitFilter],
    'PZ-IB: Accept Language Collapse':     [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, acceptLanguageCollapseFilter],
}

for _key in METRIC_EXPERIMENTS_BY_KEY:
    assert _key in EXPERIMENTS_TO_RUN, (
        f"METRIC_EXPERIMENTS key '{_key}' not found in EXPERIMENTS_TO_RUN"
    )

# Cumulative Phase 1 → 2 → 3 → 4 progression
EXPERIMENTS_TO_RUN_ADDITIVE = [
    {
        'P0-C: ProcCount, WebGLRenderer Sanitizing, Minor Version, GamePad':                   [addGamePadProtection],
        'P0-C: ProcCount, WebGLRenderer Sanitizing, Minor Version, GamePad, Media Count':      [addMediaCountProtection],
        'P1-C: P0, Font':                                                                      [fontProtectionsFilter],
        'P1-C: P0, Font, fdlibm':                                                              [fdlibmFilter],
        'P2-C: P0, P1, Processor':                                                             [procCountFilter],
        'P2-C: P0, P1, Processor, Screen':                                                     [screenAvailFilter],
        'P2-C: P0, P1, Processor, Screen, Touch Points':                                       [touchPointFilter],
        'P2-C: P0, P1, Processor, Screen, Touch Points, Font List Updates':                    [fontListUpdatesFilterLocaleConsideration],
        'P2-C: P0, P1, Processor, Screen, Touch Points, Font List Updates, webGL Vendor':      [webGLVendorRendererFilter],
        'P3-C: P0, P1, P2, Software Canvas':                                                   [canvasToSoftwareFilter],
        'P3-C: P0, P1, P2, Software Canvas, Accept Language':                                  [acceptLanguageLimitAndCollapseFilter],
        'P3-C: P0, P1, P2, Software Canvas, Accept Language, Timezone':                        [timezoneFilter],
        'P4-C: P0, P1, P2, P3, Shipping Missing Fonts':                                        [shippingMissingFontsFilter],
    },
]

EXPERIMENT_LONG_NAMES = {}

_seen_additive_keys = set()
for _additive_set in EXPERIMENTS_TO_RUN_ADDITIVE:
    _dups = _seen_additive_keys & _additive_set.keys()
    assert not _dups, (
        f"EXPERIMENTS_TO_RUN_ADDITIVE has duplicate keys across sets: {sorted(_dups)}"
    )
    _seen_additive_keys |= _additive_set.keys()
