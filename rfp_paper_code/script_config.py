"""Config key dependency map, validation, and default module-level exports.

CONFIG_DEPENDENCIES defines which config keys must be present when a
given toggle is True. Individual config files (in configs/) define
script_config dicts containing only the keys they need.

The module-level exports below (FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS,
EXPERIMENTS_TO_RUN, etc.) serve as defaults when no -c config overrides them.
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

# =============================================================================
# Config key dependency map
# =============================================================================

CONFIG_DEPENDENCIES = {
    # ── Metrics aggregation ──────────────────────────────────────────
    'calculate_metrics_aggregated': [
        'show_special_metrics_aggregated',
        'show_all_metrics_aggregated',
        'print_x_aggregate_tables',
        'print_x_aggregate_graphs',
        'print_x_aggregate_entropy',
        'print_x_hhi_index',
        'print_log_scale_also',
        'metrics_aggregated_output',
        'max_threads_graph_export',
    ],

    'calculate_metric_experiment_aggregated': [
        'show_special_metrics_aggregated',
        'show_all_metrics_aggregated',
        'print_x_aggregate_tables',
        'print_x_aggregate_graphs',
        'print_x_aggregate_entropy',
        'print_x_hhi_index',
        'print_log_scale_also',
        'metrics_aggregated_output',
        'max_threads_graph_export',
    ],

    # ── Per-OS analysis ───────────────────────────────────────────────
    'per_os_analysis': [
        'print_x_by_os_aggregate_graphs',
    ],

    # ── Fingerprints & cohort analysis ───────────────────────────────
    'fingerprints': [
        'fingerprints_output',
        'print_cohort_size_tables',
    ],

    'experiments': [
        'experiments_output',
        'print_cohort_size_tables',
        'max_threads_graph_export',
    ],

    'browser_modes': [
        'modes_output',
        'print_cohort_size_tables',
        'max_threads_graph_export',
    ],

    # ── Buckets ──────────────────────────────────────────────────────
    'fingerprint_buckets': [],
    'metric_buckets': [],

    # ── Archiving ────────────────────────────────────────────────────
    'fingerprint_archiving': [],

    # ── Missing fonts ────────────────────────────────────────────────
    'missing_fonts': [
        'missing_fonts_by_version',
        'missing_fonts_by_locale',
        'missing_font_sets',
    ],

    'missing_font_sets': [
        'missing_fonts',
    ],

    # ── Segmentation ─────────────────────────────────────────────────
    'perform_segmentation_shitty': [
        'parallel_segmentation',
        'segmentation_target_metrics',
    ],

    'perform_segmentation_decision_tree': [
        'parallel_segmentation',
        'segmentation_target_metrics',
    ],

    # ── SMR ───────────────────────────────────────────────────────────
    'perform_single_metric_removal_analysis': [
        'smr_fingerprinters',
        'smr_output',
        'perform_single_metric_removal_analysis_exclude_set',
        'perform_single_metric_removal_analysis_override_set',
    ],

    # ── LMR ───────────────────────────────────────────────────────────
    'perform_logical_metric_removal_analysis': [
        'lmr_fingerprinters',
        'lmr_output',
    ],

    # ── ISMR ──────────────────────────────────────────────────────────
    'perform_iterative_single_metric_removal_analysis': [
        'ismr_fingerprinter',
        'smr_fingerprinters',
        'perform_single_metric_removal_analysis_exclude_set',
        'perform_single_metric_removal_analysis_override_set',
    ],

    # ── ISMRP ─────────────────────────────────────────────────────────
    'perform_iterative_single_metric_replacement_analysis': [
        'ismrp_fingerprinter',
        'ismrp_rare_threshold_pct',
        'ismrp_replacement_strategy',
        'smr_fingerprinters',
        'perform_single_metric_removal_analysis_exclude_set',
        'perform_single_metric_removal_analysis_override_set',
    ],

    # ── Min-set combo analysis ───────────────────────────────────────
    'perform_min_set_combo_analysis': [
        'min_set_combo_sizes',              # {combo_size: top_n_metrics} e.g. {1: 30, 2: 20, 3: 10, 4: 10}
        'min_set_combo_fingerprinter',
        'min_set_metric_aggregation_path',
        'min_set_combo_per_os_use_overall_metrics',  # True = use overall ordering for per-OS runs (not per-OS ordering)
        'min_set_combo_metric_source',  # 'ismr' (default) or 'smr' — which metric ranking to use
        'smr_fingerprinters',
        'perform_single_metric_removal_analysis_exclude_set',
        'perform_single_metric_removal_analysis_override_set',
    ],

    # ── Correlation analysis ──────────────────────────────────────────
    'correlation_analysis': [
        'correlation_cache_only',
        'correlation_parallel_downloads',
        'correlation_parallel_workers',
        'correlation_missing_values',
        'correlation_ami',
        'correlation_ami_bin_rare_values',
        'correlation_ami_bin_thresholds',
        'correlation_ami_miller_madow',
        'correlation_theil_u',
    ],
}

CONFIG_ALWAYS_REQUIRED = [
    'raw_rows_only',
    'max_procs',
    'max_worker_threads',
    'max_threads_graph_export',
    'max_threads_experiment_merging',
    'per_os_analysis',  # False, True, or 'only'
    # All toggle keys must always be present (True or False)
    'calculate_metrics_aggregated',
    'calculate_metric_experiment_aggregated',
    'fingerprints',
    'experiments',
    'browser_modes',
    'fingerprint_buckets',
    'metric_buckets',
    'fingerprint_archiving',
    'missing_fonts',
    'missing_font_sets',
    'perform_segmentation_shitty',
    'perform_segmentation_decision_tree',
    'perform_single_metric_removal_analysis',
    'perform_logical_metric_removal_analysis',
    'perform_iterative_single_metric_removal_analysis',
    'perform_iterative_single_metric_replacement_analysis',
    'perform_min_set_combo_analysis',
    'correlation_analysis',
]


def validate_config(script_config):
    """Validate a script_config dict against CONFIG_DEPENDENCIES.

    Checks that:
    1. All CONFIG_ALWAYS_REQUIRED keys are present.
    2. For each toggle key that is True, all its dependency keys are present.
    3. No keys are present that aren't required by any enabled toggle.

    Returns the set of all valid keys for this config.
    """
    errors = []

    # Check always-required keys
    for k in CONFIG_ALWAYS_REQUIRED:
        if k not in script_config:
            errors.append(f"Missing always-required key: '{k}'")

    # Build set of all valid keys: always-required + all toggle keys + deps of enabled toggles
    valid_keys = set(CONFIG_ALWAYS_REQUIRED)
    valid_keys.update(CONFIG_DEPENDENCIES.keys())

    for toggle, deps in CONFIG_DEPENDENCIES.items():
        if script_config.get(toggle):
            for dep in deps:
                valid_keys.add(dep)
                if dep not in script_config:
                    errors.append(f"Toggle '{toggle}' is enabled but required key '{dep}' is missing")

    # Keys that are always valid but not required
    _ALWAYS_OPTIONAL = {
        'os_filter',                       # restrict analysis to one OS
        'print_x_by_os_aggregate_graphs',  # may be present even when per_os is off
        'CUSTOM_FUNCTIONS',                # optional custom map/reduce functions
    }
    valid_keys.update(_ALWAYS_OPTIONAL)

    # Check for unknown keys
    for k in script_config:
        if k not in valid_keys:
            errors.append(f"Unexpected key '{k}' — not required by any enabled toggle")

    if errors:
        for e in errors:
            print(f"  CONFIG ERROR: {e}", file=__import__('sys').stderr)
        raise SystemExit(f"Config validation failed with {len(errors)} error(s)")

    return valid_keys


# =============================================================================
# Default module-level exports (overridden by -c config files)
# =============================================================================

# No default script_config — a -c config file must always be provided.
script_config = None

FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {
    "AkamaiV2": FPSET_AKAMAI_V2,
}

METRIC_EXPERIMENTS = [
    ("P1-IB: fdLibm",                             [f'math_op_{i}' for i in range(24)]),
    ("P2-IB: Processor Count",                    ["hw_processor_count"]),
    ("P2-IB: Touch Points",                       ["hw_max_touch_points"]),
    ("P2-IB: WebGL Vendor",                       ["webgl_vendor"]),
    ("P3-IB: Software Canvas",                    [
        "canvas_canvasdata01", "canvas_canvasdata02", "canvas_canvasdata03",
        "canvas_canvasdata04", "canvas_canvasdata05", "canvas_canvasdata06",
        "canvas_canvasdata07", "canvas_canvasdata08", "canvas_canvasdata09",
        "canvas_canvasdata10", "canvas_canvasdata11_webgl",
        "canvas_canvasdata12_fingerprintjs1", "canvas_canvasdata13_fingerprintjs2",
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

CALCULATIONS_FOR_ARCHIVING = [
    (
        "Firefox No Protections",
        ["os", "intl_intl_locale"],
        [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter],
        {"AkamaiV2": FPSET_AKAMAI_V2, "SiftScience": FPSET_SIFT_SCIENCE, "FPJSv1": FPSET_FINGERPRINTJS_V1}
    ),
    (
        "Firefox Baseline",
        ["os", "intl_intl_locale"],
        [],
        {"AkamaiV2": FPSET_AKAMAI_V2, "SiftScience": FPSET_SIFT_SCIENCE, "FPJSv1": FPSET_FINGERPRINTJS_V1}
    ),
    (
        "Resist Fingerprinting Mode",
        [],
        [rfpFilter],
        {"AkamaiV2": FPSET_AKAMAI_V2, "SiftScience": FPSET_SIFT_SCIENCE, "FPJSv1": FPSET_FINGERPRINTJS_V1}
    ),
    (
        "FPP Phase 1",
        ["os", "intl_intl_locale"],
        [fontProtectionsFilter, fdlibmFilter],
        {"AkamaiV2": FPSET_AKAMAI_V2, "SiftScience": FPSET_SIFT_SCIENCE, "FPJSv1": FPSET_FINGERPRINTJS_V1}
    ),
    (
        "FPP Phase 2",
        ["os", "intl_intl_locale"],
        [fontProtectionsFilter, fdlibmFilter, procCountFilter, screenAvailFilter,
         touchPointFilter, fontListUpdatesFilterLocaleConsideration, webGLVendorRendererFilter],
        {"AkamaiV2": FPSET_AKAMAI_V2, "SiftScience": FPSET_SIFT_SCIENCE, "FPJSv1": FPSET_FINGERPRINTJS_V1}
    ),
]

FINGERPRINTERS_FOR_EXPERIMENTS = {
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
}

FINGERPRINTERS_FOR_MODES = {
    "AkamaiV2": FPSET_AKAMAI_V2,
    "SiftScience": FPSET_SIFT_SCIENCE,
    "FPJSv1": FPSET_FINGERPRINTJS_V1,
}

EXPERIMENTS_TO_RUN = {
    'P0-C: Raw': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter],
    'P0-CI: ProcCount': [removeMinorVersionProtection, noWebGLRendererSanitizing],
    'P0-C: ProcCount, WebGLRenderer Sanitizing': [removeMinorVersionProtection],
    'P0-I: Minor Version': [noWebGLRendererSanitizing, noProcessorCountFilter],
    'P0-I: WebGLRenderer Sanitizing': [removeMinorVersionProtection, noProcessorCountFilter],
    'P0-I: GamePad': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, addGamePadProtection],
    'P0-I: Media Count': [removeMinorVersionProtection, noWebGLRendererSanitizing, noProcessorCountFilter, addMediaCountProtection],
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

EXPERIMENTS_TO_RUN_ADDITIVE = [
    {
        'P0-C: ProcCount, WebGLRenderer Sanitizing, Minor Version, GamePad': [addGamePadProtection],
        'P0-C: ProcCount, WebGLRenderer Sanitizing, Minor Version, GamePad, Media Count': [addMediaCountProtection],
        'P1-C: P0, Font':                                                                     [fontProtectionsFilter],
        'P1-C: P0, Font, fdlibm':                                                             [fdlibmFilter],
        'P2-C: P0, P1, Processor':                                                            [procCountFilter],
        'P2-C: P0, P1, Processor, Screen':                                                    [screenAvailFilter],
        'P2-C: P0, P1, Processor, Screen, Touch Points':                                      [touchPointFilter],
        'P2-C: P0, P1, Processor, Screen, Touch Points, Font List Updates':                   [fontListUpdatesFilterLocaleConsideration],
        'P2-C: P0, P1, Processor, Screen, Touch Points, Font List Updates, webGL Vendor':     [webGLVendorRendererFilter],
        'P3-C: P0, P1, P2, Software Canvas':                                                  [canvasToSoftwareFilter],
        'P3-C: P0, P1, P2, Software Canvas, Accept Language':                                 [acceptLanguageLimitAndCollapseFilter],
        'P3-C: P0, P1, P2, Software Canvas, Accept Language, Timezone':                       [timezoneFilter],
        'P4-C: P0, P1, P2, P3, Shipping Missing Fonts':                                       [shippingMissingFontsFilter],
    },
]

EXPERIMENT_LONG_NAMES = {}
EXPERIMENT_SLUG_MAP = {}
EXPERIMENT_EQUIVALENTS = {}

_seen_additive_keys = set()
for _additive_set in EXPERIMENTS_TO_RUN_ADDITIVE:
    _dups = _seen_additive_keys & _additive_set.keys()
    assert not _dups, (
        f"EXPERIMENTS_TO_RUN_ADDITIVE has duplicate keys across sets: {sorted(_dups)}"
    )
    _seen_additive_keys |= _additive_set.keys()
