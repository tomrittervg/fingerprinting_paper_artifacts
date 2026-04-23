"""Correlation analysis config for tmp_0321_01 dataset (schema >= 33, Feb 1 - Mar 20).

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./correlation.py --cache-dir /work/sandbox-cache \
    -c configs/schema33_correlation.py \
    -o /work/sandbox-analyses/schema33-full-test/correlation
"""

from fingerprinters import (
    FPSET_AKAMAI_V2, FPSET_FINGERPRINTJS_V2, FPSET_SIGNIFYD,
)
from settings import BQ_PROJECT_ID

# ---------------------------------------------------------------------------
# Correlation-specific exports
# ---------------------------------------------------------------------------

CORRELATION_BQ_TABLE = f'{BQ_PROJECT_ID}.tmp_0322_01.UserCharacteristics_x_by_y_tbl'

# The 89 metrics analyzed in the schema33 correlation run (Feb 1 - Mar 20).
# Derived from the cache files used in correlation_20260323_032218/run.log.
CORRELATION_METRIC_SET = {
    "any_pointer_type", "audio_compressor_gain_reduction", "audio_fingerprint",
    "audio_fingerprint2", "audio_float_frequency_sum", "audio_float_time_domain_sum",
    "audio_unique_samples", "avail_left", "avail_top",
    "canvasdata1", "canvasdata11_webgl", "canvasdata12_fingerprintjs1",
    "canvasdata13_fingerprintjs2", "canvasdata13_fingerprintjs2software",
    "canvasdata1software", "canvasdata2", "canvasdata2software", "canvasdata7",
    "canvasdata8", "clientrects_emoji_font_family", "clientrects_ghost_dimensions",
    "clientrects_known_dimensions", "color_scheme",
    "combined_clientrects_element_gbcr_hash", "combined_clientrects_emoji_hash",
    "combined_clientrects_range_gbcr_hash", "combined_clientrects_range_gcr_hash",
    "combined_css_colors_hash", "combined_css_fonts_hash", "combined_mathml_hash",
    "combined_math_ops_hash", "combined_media_capabilities_hash",
    "combined_webgl1_params_hash", "combined_webgl_extensions_hash",
    "combined_wgpu_hash", "fonts_variant_f_allowlisted", "fonts_variant_f_nonallowlisted",
    "fonts_variant_g_allowlisted", "fonts_variant_g_nonallowlisted",
    "fonts_variant_h_allowlisted", "fonts_variant_h_nonallowlisted",
    "fonts_variant_i_allowlisted", "fonts_variant_i_nonallowlisted",
    "gl2_precision_fragment", "gl2_precision_vertex", "gl2_renderer", "gl2_vendor",
    "gl_extensions", "gl_precision_fragment", "gl_precision_vertex",
    "gl_renderer", "gl_vendor", "intl_locale", "inverted_colors", "languages",
    "max_touch_points", "monochrome", "oscpu", "pdf_viewer", "pixel_ratio",
    "platform", "pointer_type", "prefers_contrast", "prefers_reduced_motion",
    "prefers_reduced_transparency", "prefs_intl_accept_languages",
    "prefs_media_eme_enabled", "prefs_network_cookie_cookiebehavior",
    "prefs_privacy_donottrackheader_enabled", "prefs_privacy_globalprivacycontrol_enabled",
    "processor_count", "screen_primary_avail", "screen_primary_color_depth",
    "screen_primary_orientation", "screen_primary_resolution",
    "screen_primary_video_dynamic_range", "screen_web_inner", "screen_web_outer",
    "sdp_codec_list", "storage_quota", "svg_bbox", "svg_computed_text_length",
    "svg_emoji_set", "svg_extent_of_char", "timezone_offset_web", "timezone_web",
    "use_document_colors", "user_agent", "webauthn_capabilities",
}

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
