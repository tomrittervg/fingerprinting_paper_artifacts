"""Minimum Identifying Set constants.

Two metric orderings are available, selectable via the config key
'min_set_combo_metric_source' ('ismr' or 'smr', default 'ismr').

ISMR: iterative greedy removal — each step removes the metric that
      leaves the most unique users, accounting for what was already removed.
SMR:  single metric removal — ranks by standalone impact (independent).

Updated 2026-04-15 from ismr_0409_1775857451.
SMR refreshed 2026-04-24 from final-range/smr_fpjsV2_final-realistic_1776894324
      (FPJSv2_Realistic fingerprinter — excludes screen_web_inner/outer).
      Full 52-metric orderings (overall + per-OS), sorted ascending by
      UniqueUsersWhenRemoved — most impactful metrics first.
"""

# =============================================================================
# ISMR orderings (iterative greedy removal)
# =============================================================================
ISMR_TOP_METRICS = [
    # --- Top 10 ---
    'screen_web_inner',
    'webgl_renderer',
    'fonts_fpjs_nonallowlisted',
    'screen_web_outer',
    'combined_css_colors_hash',
    'canvas_canvasdata12_fingerprintjs1',
    'voices_sha1',
    'screen_web_pixel_ratio',
    'screen_primary_avail',
    'screen_primary_resolution',
    # --- 11-20 ---
    'combined_mathml_hash',
    'hw_processor_count',
    'locale_accept_language',
    'intl_intl_locale',
    'intl_timezone_web',
    'storage_quota',
    'intl_timezone_offset_web',
    'screen_web_avail_left',
    'screen_web_avail_top',
    'combined_css_fonts_hash',
    # --- 21-30 ---
    'combined_media_capabilities_hash',
    'fonts_fpjs_allowlisted',
    'user_agent',
    'hw_max_touch_points',
    'screen_color_scheme',
    'canvas_canvasdata13_fingerprintjs2',
    'canvas_canvasdata11_webgl',
    'audio_fingerprint',
    'screen_prefers_reduced_motion',
    'combined_webgl1_params_hash',
]

ISMR_TOP_METRICS_BY_OS = {
    'Android': [
        'combined_css_colors_hash',
        'screen_web_inner',
        'user_agent',
        'screen_web_outer',
        'locale_accept_language',
        'intl_intl_locale',
        'intl_timezone_web',
        'intl_timezone_offset_web',
        'voices_sha1',
        'canvas_canvasdata12_fingerprintjs1',
        'screen_web_pixel_ratio',
        'combined_mathml_hash',
        'storage_quota',
        'combined_media_capabilities_hash',
        'screen_color_scheme',
        'canvas_canvasdata13_fingerprintjs2',
        'combined_css_fonts_hash',
        'screen_prefers_reduced_motion',
        'webgl_renderer',
        'combined_webgl1_params_hash',
        'audio_fingerprint',
        'hw_processor_count',
        'canvas_canvasdata11_webgl',
        'webgl_extensions',
        'webgl2_renderer',
        'hw_max_touch_points',
        'sdp_codec_list',
        'combined_math_ops_hash',
        'combined_webgl_extensions_hash',
        'screen_inverted_colors',
    ],
    'Darwin': [
        'screen_web_inner',
        'screen_web_outer',
        'screen_primary_avail',
        'combined_css_colors_hash',
        'screen_primary_resolution',
        'fonts_fpjs_nonallowlisted',
        'voices_sha1',
        'screen_web_avail_top',
        'webgl_renderer',
        'hw_processor_count',
        'canvas_canvasdata12_fingerprintjs1',
        'screen_web_pixel_ratio',
        'screen_web_avail_left',
        'intl_timezone_web',
        'intl_intl_locale',
        'locale_accept_language',
        'intl_timezone_offset_web',
        'combined_mathml_hash',
        'combined_css_fonts_hash',
        'storage_quota',
        'screen_color_scheme',
        'canvas_canvasdata13_fingerprintjs2',
        'user_agent',
        'canvas_canvasdata11_webgl',
        'combined_media_capabilities_hash',
        'screen_prefers_reduced_motion',
        'screen_prefers_reduced_transparency',
        'screen_prefers_contrast',
        'audio_fingerprint',
        'prefs_eme_enabled',
    ],
    'Linux': [
        'screen_web_inner',
        'screen_web_outer',
        'webgl_renderer',
        'combined_css_colors_hash',
        'hw_processor_count',
        'combined_mathml_hash',
        'intl_timezone_web',
        'intl_timezone_offset_web',
        'screen_primary_avail',
        'screen_primary_resolution',
        'storage_quota',
        'canvas_canvasdata12_fingerprintjs1',
        'screen_web_pixel_ratio',
        'voices_sha1',
        'screen_web_avail_top',
        'screen_web_avail_left',
        'locale_accept_language',
        'intl_intl_locale',
        'fonts_fpjs_nonallowlisted',
        'combined_css_fonts_hash',
        'screen_color_scheme',
        'user_agent',
        'combined_webgl1_params_hash',
        'combined_media_capabilities_hash',
        'prefs_eme_enabled',
        'canvas_canvasdata13_fingerprintjs2',
        'canvas_canvasdata11_webgl',
        'webgl2_renderer',
        'audio_fingerprint',
        'webgl_extensions',
    ],
    'WINNT': [
        'webgl_renderer',
        'fonts_fpjs_nonallowlisted',
        'screen_web_inner',
        'screen_web_outer',
        'canvas_canvasdata12_fingerprintjs1',
        'voices_sha1',
        'hw_processor_count',
        'screen_web_pixel_ratio',
        'screen_primary_avail',
        'screen_primary_resolution',
        'storage_quota',
        'intl_timezone_web',
        'intl_timezone_offset_web',
        'intl_intl_locale',
        'locale_accept_language',
        'screen_web_avail_left',
        'combined_mathml_hash',
        'screen_web_avail_top',
        'combined_css_fonts_hash',
        'combined_css_colors_hash',
        'fonts_fpjs_allowlisted',
        'hw_max_touch_points',
        'screen_color_scheme',
        'combined_media_capabilities_hash',
        'user_agent',
        'canvas_canvasdata13_fingerprintjs2',
        'canvas_canvasdata11_webgl',
        'audio_fingerprint',
        'screen_prefers_reduced_motion',
        'webgl2_renderer',
    ],
}

# =============================================================================
# SMR orderings (single metric removal — standalone impact)
# =============================================================================
SMR_TOP_METRICS = [
    # --- 1-10 ---
    'combined_css_colors_hash',
    'webgl_renderer',
    'fonts_fpjs_nonallowlisted',
    'user_agent',
    'canvas_canvasdata12_fingerprintjs1',
    'screen_primary_avail',
    'voices_sha1',
    'intl_timezone_web',
    'locale_accept_language',
    'hw_processor_count',
    # --- 11-20 ---
    'combined_mathml_hash',
    'fonts_fpjs_allowlisted',
    'storage_quota',
    'screen_web_pixel_ratio',
    'combined_media_capabilities_hash',
    'screen_prefers_reduced_motion',
    'hw_max_touch_points',
    'intl_intl_locale',
    'screen_color_scheme',
    'screen_web_avail_left',
    # --- 21-30 ---
    'screen_prefers_reduced_transparency',
    'screen_web_avail_top',
    'prefs_eme_enabled',
    'audio_fingerprint',
    'combined_webgl1_params_hash',
    'combined_math_ops_hash',
    'sdp_codec_list',
    'intl_timezone_offset_web',
    'canvas_canvasdata11_webgl',
    'webgl_extensions',
    # --- 31-40 ---
    'prefs_pdf_viewer',
    'combined_css_fonts_hash',
    'wgpu_missing_features',
    'prefs_cookiesenabled',
    'screen_primary_resolution',
    'screen_inverted_colors',
    'canvas_canvasdata13_fingerprintjs2',
    'webauthn_capabilities',
    'screen_prefers_contrast',
    'combined_webgl_extensions_hash',
    # --- 41-50 ---
    'webgl_vendor',
    'combined_wgpu_hash',
    'platform',
    'screen_primary_color_depth',
    'hw_oscpu',
    'prefs_use_document_colors',
    'screen_monochrome',
    'screen_primary_video_dynamic_range',
    'webgl_precision_fragment',
    'webgl_precision_vertex',
    # --- 51-52 ---
    'webgl_vendor_raw',
    'wgpu_is_fallback_adapter',
]

SMR_TOP_METRICS_BY_OS = {
    'Android': [
        # --- 1-10 ---
        'combined_css_colors_hash',
        'user_agent',
        'locale_accept_language',
        'intl_timezone_web',
        'voices_sha1',
        'combined_mathml_hash',
        'canvas_canvasdata12_fingerprintjs1',
        'webgl_renderer',
        'screen_web_pixel_ratio',
        'storage_quota',
        # --- 11-20 ---
        'combined_media_capabilities_hash',
        'screen_prefers_reduced_motion',
        'combined_webgl1_params_hash',
        'hw_processor_count',
        'audio_fingerprint',
        'intl_timezone_offset_web',
        'canvas_canvasdata11_webgl',
        'screen_color_scheme',
        'webgl_extensions',
        'sdp_codec_list',
        # --- 21-30 ---
        'hw_max_touch_points',
        'intl_intl_locale',
        'prefs_cookiesenabled',
        'screen_inverted_colors',
        'canvas_canvasdata13_fingerprintjs2',
        'combined_css_fonts_hash',
        'combined_math_ops_hash',
        'fonts_fpjs_nonallowlisted',
        'screen_web_avail_left',
        'combined_webgl_extensions_hash',
        # --- 31-40 ---
        'prefs_pdf_viewer',
        'screen_web_avail_top',
        'webauthn_capabilities',
        'combined_wgpu_hash',
        'fonts_fpjs_allowlisted',
        'hw_oscpu',
        'platform',
        'prefs_eme_enabled',
        'prefs_use_document_colors',
        'screen_monochrome',
        # --- 41-50 ---
        'screen_prefers_contrast',
        'screen_prefers_reduced_transparency',
        'screen_primary_avail',
        'screen_primary_color_depth',
        'screen_primary_resolution',
        'screen_primary_video_dynamic_range',
        'webgl_precision_fragment',
        'webgl_precision_vertex',
        'webgl_vendor',
        'webgl_vendor_raw',
        # --- 51-52 ---
        'wgpu_is_fallback_adapter',
        'wgpu_missing_features',
    ],
    'Darwin': [
        # --- 1-10 ---
        'screen_primary_avail',
        'user_agent',
        'combined_css_colors_hash',
        'voices_sha1',
        'webgl_renderer',
        'fonts_fpjs_nonallowlisted',
        'intl_timezone_web',
        'screen_web_avail_top',
        'canvas_canvasdata12_fingerprintjs1',
        'intl_intl_locale',
        # --- 11-20 ---
        'locale_accept_language',
        'hw_processor_count',
        'screen_color_scheme',
        'screen_web_avail_left',
        'screen_prefers_reduced_transparency',
        'screen_prefers_reduced_motion',
        'screen_web_pixel_ratio',
        'combined_mathml_hash',
        'sdp_codec_list',
        'storage_quota',
        # --- 21-30 ---
        'prefs_eme_enabled',
        'audio_fingerprint',
        'intl_timezone_offset_web',
        'combined_media_capabilities_hash',
        'combined_math_ops_hash',
        'canvas_canvasdata11_webgl',
        'screen_primary_resolution',
        'combined_css_fonts_hash',
        'prefs_pdf_viewer',
        'webauthn_capabilities',
        # --- 31-40 ---
        'prefs_cookiesenabled',
        'fonts_fpjs_allowlisted',
        'screen_inverted_colors',
        'canvas_canvasdata13_fingerprintjs2',
        'webgl_extensions',
        'combined_webgl1_params_hash',
        'combined_webgl_extensions_hash',
        'combined_wgpu_hash',
        'hw_max_touch_points',
        'hw_oscpu',
        # --- 41-50 ---
        'platform',
        'prefs_use_document_colors',
        'screen_monochrome',
        'screen_prefers_contrast',
        'screen_primary_color_depth',
        'screen_primary_video_dynamic_range',
        'webgl_precision_fragment',
        'webgl_precision_vertex',
        'webgl_vendor',
        'webgl_vendor_raw',
        # --- 51-52 ---
        'wgpu_is_fallback_adapter',
        'wgpu_missing_features',
    ],
    'Linux': [
        # --- 1-10 ---
        'webgl_renderer',
        'combined_css_colors_hash',
        'user_agent',
        'combined_mathml_hash',
        'prefs_eme_enabled',
        'intl_timezone_web',
        'hw_processor_count',
        'storage_quota',
        'screen_primary_avail',
        'voices_sha1',
        # --- 11-20 ---
        'canvas_canvasdata12_fingerprintjs1',
        'screen_color_scheme',
        'screen_web_pixel_ratio',
        'locale_accept_language',
        'intl_intl_locale',
        'screen_web_avail_left',
        'fonts_fpjs_nonallowlisted',
        'screen_prefers_reduced_motion',
        'screen_web_avail_top',
        'combined_media_capabilities_hash',
        # --- 21-30 ---
        'audio_fingerprint',
        'sdp_codec_list',
        'combined_css_fonts_hash',
        'intl_timezone_offset_web',
        'combined_webgl1_params_hash',
        'canvas_canvasdata11_webgl',
        'screen_primary_resolution',
        'prefs_pdf_viewer',
        'canvas_canvasdata13_fingerprintjs2',
        'prefs_cookiesenabled',
        # --- 31-40 ---
        'webauthn_capabilities',
        'webgl_extensions',
        'webgl_vendor',
        'platform',
        'screen_primary_color_depth',
        'combined_math_ops_hash',
        'combined_webgl_extensions_hash',
        'combined_wgpu_hash',
        'fonts_fpjs_allowlisted',
        'hw_max_touch_points',
        # --- 41-50 ---
        'hw_oscpu',
        'prefs_use_document_colors',
        'screen_inverted_colors',
        'screen_monochrome',
        'screen_prefers_contrast',
        'screen_prefers_reduced_transparency',
        'screen_primary_video_dynamic_range',
        'webgl_precision_fragment',
        'webgl_precision_vertex',
        'webgl_vendor_raw',
        # --- 51-52 ---
        'wgpu_is_fallback_adapter',
        'wgpu_missing_features',
    ],
    'WINNT': [
        # --- 1-10 ---
        'webgl_renderer',
        'fonts_fpjs_nonallowlisted',
        'canvas_canvasdata12_fingerprintjs1',
        'hw_processor_count',
        'voices_sha1',
        'combined_css_colors_hash',
        'fonts_fpjs_allowlisted',
        'screen_primary_avail',
        'hw_max_touch_points',
        'intl_timezone_web',
        # --- 11-20 ---
        'user_agent',
        'storage_quota',
        'screen_web_pixel_ratio',
        'intl_intl_locale',
        'combined_media_capabilities_hash',
        'screen_prefers_reduced_motion',
        'screen_prefers_reduced_transparency',
        'screen_color_scheme',
        'screen_web_avail_left',
        'locale_accept_language',
        # --- 21-30 ---
        'audio_fingerprint',
        'screen_web_avail_top',
        'combined_math_ops_hash',
        'combined_mathml_hash',
        'prefs_eme_enabled',
        'sdp_codec_list',
        'intl_timezone_offset_web',
        'prefs_pdf_viewer',
        'canvas_canvasdata11_webgl',
        'wgpu_missing_features',
        # --- 31-40 ---
        'combined_css_fonts_hash',
        'screen_prefers_contrast',
        'prefs_cookiesenabled',
        'screen_inverted_colors',
        'webauthn_capabilities',
        'canvas_canvasdata13_fingerprintjs2',
        'webgl_extensions',
        'screen_primary_resolution',
        'combined_wgpu_hash',
        'platform',
        # --- 41-50 ---
        'combined_webgl1_params_hash',
        'combined_webgl_extensions_hash',
        'hw_oscpu',
        'prefs_use_document_colors',
        'screen_monochrome',
        'screen_primary_color_depth',
        'screen_primary_video_dynamic_range',
        'webgl_precision_fragment',
        'webgl_precision_vertex',
        'webgl_vendor',
        # --- 51-52 ---
        'webgl_vendor_raw',
        'wgpu_is_fallback_adapter',
    ],
}

# =============================================================================
# AkamaiV2_Realistic SMR orderings
# =============================================================================
SMR_TOP_METRICS_AKAMAIV2 = [
    'intl_timezone_offset_web',
    'platform',
    'screen_primary_avail',
    'canvas_canvasdata12_fingerprintjs1',
    'hw_max_touch_points',
    'screen_primary_color_depth',
    'hw_oscpu',
    'user_agent',
    'hw_processor_count',
    'locale_languages',
    'locale_accept_language',
    'screen_primary_resolution',
    'prefs_cookiesenabled',
    'prefs_general_donottrack_enabled',
    'screen_primary_pixel_depth',
    'canvas_canvasdata13_fingerprintjs2',
]

SMR_TOP_METRICS_BY_OS_AKAMAIV2 = {
    'Android': [
        'canvas_canvasdata12_fingerprintjs1',
        'user_agent',
        'intl_timezone_offset_web',
        'hw_processor_count',
        'hw_max_touch_points',
        'canvas_canvasdata13_fingerprintjs2',
        'prefs_general_donottrack_enabled',
        'prefs_cookiesenabled',
        'locale_accept_language',
        'locale_languages',
        'hw_oscpu',
        'platform',
        'screen_primary_avail',
        'screen_primary_color_depth',
        'screen_primary_pixel_depth',
        'screen_primary_resolution',
    ],
    'Darwin': [
        'screen_primary_avail',
        'canvas_canvasdata12_fingerprintjs1',
        'intl_timezone_offset_web',
        'hw_processor_count',
        'user_agent',
        'prefs_general_donottrack_enabled',
        'canvas_canvasdata13_fingerprintjs2',
        'screen_primary_resolution',
        'locale_accept_language',
        'prefs_cookiesenabled',
        'locale_languages',
        'hw_max_touch_points',
        'hw_oscpu',
        'platform',
        'screen_primary_color_depth',
        'screen_primary_pixel_depth',
    ],
    'Linux': [
        'canvas_canvasdata12_fingerprintjs1',
        'screen_primary_avail',
        'hw_processor_count',
        'intl_timezone_offset_web',
        'user_agent',
        'canvas_canvasdata13_fingerprintjs2',
        'prefs_general_donottrack_enabled',
        'locale_accept_language',
        'screen_primary_resolution',
        'prefs_cookiesenabled',
        'locale_languages',
        'platform',
        'hw_max_touch_points',
        'hw_oscpu',
        'screen_primary_color_depth',
        'screen_primary_pixel_depth',
    ],
    'WINNT': [
        'canvas_canvasdata12_fingerprintjs1',
        'hw_processor_count',
        'intl_timezone_offset_web',
        'screen_primary_avail',
        'hw_max_touch_points',
        'user_agent',
        'prefs_general_donottrack_enabled',
        'locale_accept_language',
        'canvas_canvasdata13_fingerprintjs2',
        'screen_primary_resolution',
        'locale_languages',
        'prefs_cookiesenabled',
        'platform',
        'hw_oscpu',
        'screen_primary_color_depth',
        'screen_primary_pixel_depth',
    ],
}

# =============================================================================
# Signifyd_Realistic SMR orderings
# =============================================================================
SMR_TOP_METRICS_SIGNIFYD = [
    'wgpu_maxvertexbuffers', 'user_agent', 'wgpu_maxbindgroups',
    'wgpu_maxcomputeworkgroupstoragesize', 'svg_bbox',
    'prefs_general_donottrack_enabled', 'hw_pointer_type', 'svg_extent_of_char',
    'audio_unique_samples', 'webgl_renderer',
    'screen_web_pixel_ratio', 'fonts_variant_i_nonallowlisted',
    'svg_computed_text_length', 'canvas_canvasdata13_fingerprintjs2',
    'screen_monochrome', 'fonts_variant_h_nonallowlisted',
    'clientrects_known_dimensions', 'wgpu_maxuniformbufferbindingsize',
    'fonts_variant_g_nonallowlisted', 'screen_primary_color_depth',
    'combined_clientrects_element_gcr_hash', 'canvas_canvasdata08',
    'screen_inverted_colors', 'canvassoftware_canvasdata01',
    'wgpu_maxtexturedimension1d', 'wgpu_is_fallback_adapter',
    'wgpu_maxvertexattributes', 'canvassoftware_canvasdata13_fingerprintjs2',
    'combined_clientrects_range_gbcr_hash', 'wgpu_maxcolorattachments',
    'canvassoftware_canvasdata02', 'canvas_canvasdata02',
    'storage_quota', 'screen_prefers_reduced_motion',
    'screen_color_scheme', 'prefs_general_globalprivacycontrol_enabled',
    'wgpu_maxdynamicstoragebuffersperpipelinelayout', 'prefs_cookiesenabled',
    'combined_clientrects_range_gcr_hash', 'hw_oscpu',
    'fonts_variant_f_nonallowlisted', 'hw_any_pointer_type',
    'wgpu_maxtexturedimension2d', 'wgpu_maxbuffersize',
    'canvas_canvasdata07', 'screen_primary_avail',
    'fonts_variant_g_allowlisted', 'platform',
    'svg_emoji_set', 'wgpu_maxcomputeinvocationsperworkgroup',
    'fonts_variant_f_allowlisted', 'fonts_variant_h_allowlisted',
    'screen_primary_pixel_depth', 'svg_substring_length',
    'clientrects_emoji_font_family', 'audio_compressor_gain_reduction',
    'intl_intl_locale', 'combined_css_colors_hash',
    'wgpu_maxdynamicuniformbuffersperpipelinelayout', 'clientrects_text_font_family',
    'webgl_vendor', 'combined_clientrects_element_gbcr_hash',
    'canvas_canvasdata01', 'combined_clientrects_emoji_hash',
    'wgpu_maxtexturedimension3d', 'wgpu_missing_features',
    'intl_timezone_offset_web', 'hw_processor_count',
    'fonts_variant_i_allowlisted', 'screen_primary_orientation',
    'audio_float_frequency_sum', 'prefs_use_document_colors',
    'screen_primary_resolution', 'combined_css_fonts_hash',
    'webgl_vendor_raw', 'locale_accept_language',
    'audio_fingerprint2', 'audio_float_time_domain_sum',
    'intl_timezone_web', 'hw_max_touch_points',
    'wgpu_maxstoragebufferspershaderstage', 'clientrects_ghost_dimensions',
]

SMR_TOP_METRICS_BY_OS_SIGNIFYD = {
    'Android': [
        'combined_css_colors_hash', 'user_agent', 'locale_accept_language',
        'intl_timezone_web', 'webgl_renderer', 'screen_web_pixel_ratio',
        'storage_quota', 'screen_prefers_reduced_motion', 'canvas_canvasdata08',
        'prefs_general_globalprivacycontrol_enabled',
        'canvas_canvasdata07', 'hw_any_pointer_type', 'screen_primary_orientation',
        'hw_processor_count', 'intl_timezone_offset_web', 'screen_color_scheme',
        'svg_emoji_set', 'prefs_general_donottrack_enabled', 'hw_max_touch_points',
        'intl_intl_locale',
        'fonts_variant_h_nonallowlisted', 'screen_inverted_colors',
        'prefs_cookiesenabled', 'canvas_canvasdata13_fingerprintjs2',
        'combined_css_fonts_hash', 'svg_bbox', 'fonts_variant_i_nonallowlisted',
        'canvas_canvasdata01', 'canvas_canvasdata02',
        'combined_clientrects_range_gcr_hash',
        'audio_float_frequency_sum', 'audio_compressor_gain_reduction',
        'audio_fingerprint2', 'audio_float_time_domain_sum',
        'audio_unique_samples', 'canvassoftware_canvasdata01',
        'canvassoftware_canvasdata02', 'canvassoftware_canvasdata13_fingerprintjs2',
        'clientrects_emoji_font_family', 'clientrects_ghost_dimensions',
        'clientrects_known_dimensions', 'clientrects_text_font_family',
        'combined_clientrects_element_gbcr_hash', 'combined_clientrects_element_gcr_hash',
        'combined_clientrects_emoji_hash', 'combined_clientrects_range_gbcr_hash',
        'fonts_variant_f_allowlisted', 'fonts_variant_f_nonallowlisted',
        'fonts_variant_g_allowlisted', 'fonts_variant_g_nonallowlisted',
        'fonts_variant_h_allowlisted', 'fonts_variant_i_allowlisted',
        'hw_oscpu', 'hw_pointer_type', 'platform', 'prefs_use_document_colors',
        'screen_monochrome', 'screen_primary_avail', 'screen_primary_color_depth',
        'screen_primary_pixel_depth', 'screen_primary_resolution',
        'svg_computed_text_length', 'svg_extent_of_char', 'svg_substring_length',
        'webgl_vendor', 'webgl_vendor_raw', 'wgpu_is_fallback_adapter',
        'wgpu_maxbindgroups', 'wgpu_maxbuffersize', 'wgpu_maxcolorattachments',
        'wgpu_maxcomputeinvocationsperworkgroup', 'wgpu_maxcomputeworkgroupstoragesize',
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',
        'wgpu_maxstoragebufferspershaderstage', 'wgpu_maxtexturedimension1d',
        'wgpu_maxtexturedimension2d', 'wgpu_maxtexturedimension3d',
        'wgpu_maxuniformbufferbindingsize', 'wgpu_maxvertexattributes',
        'wgpu_maxvertexbuffers', 'wgpu_missing_features',
    ],
    'Darwin': [
        'screen_primary_avail', 'combined_css_colors_hash', 'user_agent',
        'webgl_renderer', 'intl_timezone_web', 'intl_intl_locale',
        'fonts_variant_h_nonallowlisted', 'prefs_general_donottrack_enabled',
        'locale_accept_language', 'prefs_general_globalprivacycontrol_enabled',
        'hw_processor_count', 'screen_web_pixel_ratio', 'screen_color_scheme',
        'canvas_canvasdata08', 'screen_prefers_reduced_motion', 'svg_bbox',
        'screen_primary_resolution', 'storage_quota', 'intl_timezone_offset_web',
        'combined_clientrects_range_gcr_hash',
        'canvas_canvasdata07', 'combined_css_fonts_hash',
        'fonts_variant_i_nonallowlisted', 'prefs_cookiesenabled', 'svg_emoji_set',
        'audio_float_frequency_sum', 'canvas_canvasdata13_fingerprintjs2',
        'screen_inverted_colors', 'fonts_variant_h_allowlisted',
        'canvas_canvasdata02', 'canvas_canvasdata01',
        'audio_compressor_gain_reduction', 'audio_fingerprint2',
        'audio_float_time_domain_sum', 'audio_unique_samples',
        'canvassoftware_canvasdata01', 'canvassoftware_canvasdata02',
        'canvassoftware_canvasdata13_fingerprintjs2', 'clientrects_emoji_font_family',
        'clientrects_ghost_dimensions', 'clientrects_known_dimensions',
        'clientrects_text_font_family', 'combined_clientrects_element_gbcr_hash',
        'combined_clientrects_element_gcr_hash', 'combined_clientrects_emoji_hash',
        'combined_clientrects_range_gbcr_hash', 'fonts_variant_f_allowlisted',
        'fonts_variant_f_nonallowlisted', 'fonts_variant_g_allowlisted',
        'fonts_variant_g_nonallowlisted', 'fonts_variant_i_allowlisted',
        'hw_any_pointer_type', 'hw_max_touch_points', 'hw_oscpu', 'hw_pointer_type',
        'platform', 'prefs_use_document_colors', 'screen_monochrome',
        'screen_primary_color_depth', 'screen_primary_orientation',
        'screen_primary_pixel_depth', 'svg_computed_text_length',
        'svg_extent_of_char', 'svg_substring_length', 'webgl_vendor',
        'webgl_vendor_raw', 'wgpu_is_fallback_adapter', 'wgpu_maxbindgroups',
        'wgpu_maxbuffersize', 'wgpu_maxcolorattachments',
        'wgpu_maxcomputeinvocationsperworkgroup', 'wgpu_maxcomputeworkgroupstoragesize',
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',
        'wgpu_maxstoragebufferspershaderstage', 'wgpu_maxtexturedimension1d',
        'wgpu_maxtexturedimension2d', 'wgpu_maxtexturedimension3d',
        'wgpu_maxuniformbufferbindingsize', 'wgpu_maxvertexattributes',
        'wgpu_maxvertexbuffers', 'wgpu_missing_features',
    ],
    'Linux': [
        'webgl_renderer', 'combined_css_colors_hash', 'user_agent',
        'screen_primary_avail', 'intl_timezone_web', 'hw_processor_count',
        'storage_quota', 'screen_web_pixel_ratio', 'screen_color_scheme',
        'prefs_general_globalprivacycontrol_enabled',
        'canvas_canvasdata08', 'locale_accept_language', 'intl_intl_locale',
        'prefs_general_donottrack_enabled', 'screen_prefers_reduced_motion',
        'canvas_canvasdata07', 'fonts_variant_h_nonallowlisted',
        'intl_timezone_offset_web', 'audio_float_frequency_sum',
        'combined_css_fonts_hash',
        'combined_clientrects_range_gcr_hash', 'fonts_variant_i_allowlisted',
        'screen_primary_resolution', 'fonts_variant_i_nonallowlisted',
        'canvas_canvasdata01', 'canvas_canvasdata13_fingerprintjs2',
        'prefs_cookiesenabled', 'webgl_vendor', 'canvas_canvasdata02',
        'fonts_variant_h_allowlisted',
        'svg_emoji_set', 'combined_clientrects_emoji_hash', 'platform',
        'audio_compressor_gain_reduction', 'audio_fingerprint2',
        'audio_float_time_domain_sum', 'audio_unique_samples',
        'canvassoftware_canvasdata01', 'canvassoftware_canvasdata02',
        'canvassoftware_canvasdata13_fingerprintjs2', 'clientrects_emoji_font_family',
        'clientrects_ghost_dimensions', 'clientrects_known_dimensions',
        'clientrects_text_font_family', 'combined_clientrects_element_gbcr_hash',
        'combined_clientrects_element_gcr_hash', 'combined_clientrects_range_gbcr_hash',
        'fonts_variant_f_allowlisted', 'fonts_variant_f_nonallowlisted',
        'fonts_variant_g_allowlisted', 'fonts_variant_g_nonallowlisted',
        'hw_any_pointer_type', 'hw_max_touch_points', 'hw_oscpu', 'hw_pointer_type',
        'prefs_use_document_colors', 'screen_inverted_colors', 'screen_monochrome',
        'screen_primary_color_depth', 'screen_primary_orientation',
        'screen_primary_pixel_depth', 'svg_bbox', 'svg_computed_text_length',
        'svg_extent_of_char', 'svg_substring_length', 'webgl_vendor_raw',
        'wgpu_is_fallback_adapter', 'wgpu_maxbindgroups', 'wgpu_maxbuffersize',
        'wgpu_maxcolorattachments', 'wgpu_maxcomputeinvocationsperworkgroup',
        'wgpu_maxcomputeworkgroupstoragesize',
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',
        'wgpu_maxstoragebufferspershaderstage', 'wgpu_maxtexturedimension1d',
        'wgpu_maxtexturedimension2d', 'wgpu_maxtexturedimension3d',
        'wgpu_maxuniformbufferbindingsize', 'wgpu_maxvertexattributes',
        'wgpu_maxvertexbuffers', 'wgpu_missing_features',
    ],
    'WINNT': [
        'webgl_renderer', 'hw_processor_count', 'combined_css_colors_hash',
        'intl_timezone_web', 'screen_primary_avail', 'intl_intl_locale',
        'storage_quota', 'screen_prefers_reduced_motion', 'screen_web_pixel_ratio',
        'user_agent',
        'locale_accept_language', 'screen_color_scheme', 'hw_max_touch_points',
        'prefs_general_donottrack_enabled', 'prefs_general_globalprivacycontrol_enabled',
        'svg_emoji_set', 'canvas_canvasdata08', 'svg_bbox',
        'audio_float_frequency_sum', 'hw_pointer_type',
        'intl_timezone_offset_web', 'canvas_canvasdata07',
        'combined_clientrects_range_gcr_hash', 'fonts_variant_h_nonallowlisted',
        'screen_primary_orientation', 'combined_css_fonts_hash',
        'hw_any_pointer_type', 'wgpu_missing_features', 'prefs_cookiesenabled',
        'screen_inverted_colors',
        'canvas_canvasdata13_fingerprintjs2', 'screen_primary_resolution',
        'fonts_variant_i_nonallowlisted', 'wgpu_maxstoragebufferspershaderstage',
        'combined_clientrects_emoji_hash', 'canvas_canvasdata02',
        'canvassoftware_canvasdata13_fingerprintjs2', 'prefs_use_document_colors',
        'canvas_canvasdata01', 'platform',
        'webgl_vendor', 'audio_compressor_gain_reduction', 'audio_fingerprint2',
        'audio_float_time_domain_sum', 'audio_unique_samples',
        'canvassoftware_canvasdata01', 'canvassoftware_canvasdata02',
        'clientrects_emoji_font_family', 'clientrects_ghost_dimensions',
        'clientrects_known_dimensions',
        'clientrects_text_font_family', 'combined_clientrects_element_gbcr_hash',
        'combined_clientrects_element_gcr_hash', 'combined_clientrects_range_gbcr_hash',
        'fonts_variant_f_allowlisted', 'fonts_variant_f_nonallowlisted',
        'fonts_variant_g_allowlisted', 'fonts_variant_g_nonallowlisted',
        'fonts_variant_h_allowlisted', 'fonts_variant_i_allowlisted',
        'hw_oscpu', 'screen_monochrome', 'screen_primary_color_depth',
        'screen_primary_pixel_depth', 'svg_computed_text_length',
        'svg_extent_of_char', 'svg_substring_length', 'webgl_vendor_raw',
        'wgpu_is_fallback_adapter', 'wgpu_maxbindgroups', 'wgpu_maxbuffersize',
        'wgpu_maxcolorattachments', 'wgpu_maxcomputeinvocationsperworkgroup',
        'wgpu_maxcomputeworkgroupstoragesize',
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',
        'wgpu_maxtexturedimension1d', 'wgpu_maxtexturedimension2d',
        'wgpu_maxtexturedimension3d', 'wgpu_maxuniformbufferbindingsize',
        'wgpu_maxvertexattributes', 'wgpu_maxvertexbuffers',
    ],
}

# =============================================================================
# MinMetrics orderings — reordered by marginal contribution from the prefix
# uniqueness curve (minmetrics analysis). Unlike SMR ordering (which ranks by
# standalone removal impact), this ordering ranks metrics by how many NEW
# unique users each adds when appended to the prefix of all prior metrics.
# Source: minmetrics runs from 2026-04-24 final-realistic.
# =============================================================================

## Generated from minmetrics_all_smr_final-realistic_1777067638

MINMETRICS_TOP_METRICS_FPJSV2 = [
    'intl_timezone_web',  # +4,132,656
    'canvas_canvasdata12_fingerprintjs1',  # +3,484,304
    'voices_sha1',  # +2,747,144
    'screen_primary_avail',  # +2,485,413
    'fonts_fpjs_nonallowlisted',  # +1,508,953
    'locale_accept_language',  # +1,116,415
    'hw_processor_count',  # +565,379
    'user_agent',  # +407,061
    'combined_mathml_hash',  # +335,145
    'fonts_fpjs_allowlisted',  # +263,844
    'storage_quota',  # +248,954
    'webgl_renderer',  # +235,104
    'screen_web_pixel_ratio',  # +228,610
    'screen_prefers_reduced_motion',  # +155,675
    'combined_media_capabilities_hash',  # +146,684
    'hw_max_touch_points',  # +120,524
    'intl_intl_locale',  # +110,782
    'screen_prefers_reduced_transparency',  # +97,049
    'screen_color_scheme',  # +76,722
    'audio_fingerprint',  # +76,703
    'screen_web_avail_left',  # +76,188
    'screen_web_avail_top',  # +55,468
    'combined_css_colors_hash',  # +53,659
    'prefs_eme_enabled',  # +40,149
    'combined_webgl1_params_hash',  # +13,523
    'combined_math_ops_hash',  # +12,310
    'sdp_codec_list',  # +5,301
    'wgpu_missing_features',  # +5,048
    'intl_timezone_offset_web',  # +4,681
    'canvas_canvasdata11_webgl',  # +2,899
    'webgl_extensions',  # +1,655
    'prefs_pdf_viewer',  # +841
    'combined_css_fonts_hash',  # +573
    'prefs_cookiesenabled',  # +188
    'screen_primary_resolution',  # +180
    'screen_inverted_colors',  # +120
    'canvas_canvasdata13_fingerprintjs2',  # +101
    'webauthn_capabilities',  # +68
    'screen_prefers_contrast',  # +57
    'combined_webgl_extensions_hash',  # +3
    'webgl_vendor',  # +3
    'combined_wgpu_hash',  # +2
    'platform',  # +2
    'screen_primary_color_depth',  # +1
    'hw_oscpu',  # +0
    'prefs_use_document_colors',  # +0
    'screen_monochrome',  # +0
    'screen_primary_video_dynamic_range',  # +0
    'webgl_precision_fragment',  # +0
    'webgl_precision_vertex',  # +0
    'webgl_vendor_raw',  # +0
    'wgpu_is_fallback_adapter',  # +0
]

MINMETRICS_TOP_METRICS_BY_OS_FPJSV2 = {
    'Android': [
        'canvas_canvasdata12_fingerprintjs1',  # +1,419,062
        'locale_accept_language',  # +1,040,485
        'combined_mathml_hash',  # +905,014
        'intl_timezone_web',  # +635,684
        'webgl_renderer',  # +477,867
        'voices_sha1',  # +360,412
        'screen_primary_avail',  # +171,071
        'screen_web_pixel_ratio',  # +133,515
        'storage_quota',  # +121,359
        'combined_media_capabilities_hash',  # +73,561
        'screen_prefers_reduced_motion',  # +63,630
        'screen_prefers_contrast',  # +38,649
        'combined_webgl1_params_hash',  # +21,788
        'user_agent',  # +19,576
        'hw_processor_count',  # +16,725
        'combined_css_colors_hash',  # +13,360
        'audio_fingerprint',  # +3,325
        'webgl_extensions',  # +2,670
        'intl_timezone_offset_web',  # +2,312
        'canvas_canvasdata11_webgl',  # +2,118
        'screen_color_scheme',  # +1,823
        'sdp_codec_list',  # +1,432
        'hw_max_touch_points',  # +367
        'intl_intl_locale',  # +286
        'prefs_cookiesenabled',  # +126
        'screen_web_avail_left',  # +119
        'screen_inverted_colors',  # +117
        'combined_math_ops_hash',  # +76
        'canvas_canvasdata13_fingerprintjs2',  # +70
        'combined_css_fonts_hash',  # +67
        'screen_web_avail_top',  # +31
        'fonts_fpjs_nonallowlisted',  # +12
        'combined_webgl_extensions_hash',  # +3
        'prefs_pdf_viewer',  # +3
        'combined_wgpu_hash',  # +2
        'webauthn_capabilities',  # +1
        'fonts_fpjs_allowlisted',  # +0
        'hw_oscpu',  # +0
        'platform',  # +0
        'prefs_eme_enabled',  # +0
        'prefs_use_document_colors',  # +0
        'screen_monochrome',  # +0
        'screen_prefers_reduced_transparency',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_resolution',  # +0
        'screen_primary_video_dynamic_range',  # +0
        'webgl_precision_fragment',  # +0
        'webgl_precision_vertex',  # +0
        'webgl_vendor',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_is_fallback_adapter',  # +0
        'wgpu_missing_features',  # +0
    ],
    'Darwin': [
        'intl_timezone_web',  # +603,711
        'fonts_fpjs_nonallowlisted',  # +227,962
        'webgl_renderer',  # +186,481
        'screen_web_avail_top',  # +154,192
        'voices_sha1',  # +120,249
        'combined_css_colors_hash',  # +115,503
        'canvas_canvasdata12_fingerprintjs1',  # +108,690
        'intl_intl_locale',  # +88,409
        'locale_accept_language',  # +16,426
        'hw_processor_count',  # +12,789
        'screen_color_scheme',  # +11,955
        'combined_mathml_hash',  # +7,931
        'screen_primary_avail',  # +6,708
        'screen_web_avail_left',  # +5,793
        'screen_prefers_reduced_transparency',  # +4,807
        'user_agent',  # +4,117
        'screen_prefers_reduced_motion',  # +3,457
        'screen_web_pixel_ratio',  # +2,365
        'sdp_codec_list',  # +1,217
        'audio_fingerprint',  # +621
        'storage_quota',  # +618
        'prefs_eme_enabled',  # +580
        'intl_timezone_offset_web',  # +443
        'combined_media_capabilities_hash',  # +163
        'combined_math_ops_hash',  # +153
        'canvas_canvasdata11_webgl',  # +152
        'screen_primary_resolution',  # +142
        'combined_css_fonts_hash',  # +127
        'prefs_pdf_viewer',  # +66
        'webauthn_capabilities',  # +35
        'prefs_cookiesenabled',  # +27
        'fonts_fpjs_allowlisted',  # +15
        'combined_wgpu_hash',  # +15
        'screen_inverted_colors',  # +9
        'webgl_extensions',  # +7
        'canvas_canvasdata13_fingerprintjs2',  # +5
        'combined_webgl1_params_hash',  # +0
        'combined_webgl_extensions_hash',  # +0
        'hw_max_touch_points',  # +0
        'hw_oscpu',  # +0
        'platform',  # +0
        'prefs_use_document_colors',  # +0
        'screen_monochrome',  # +0
        'screen_prefers_contrast',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_video_dynamic_range',  # +0
        'webgl_precision_fragment',  # +0
        'webgl_precision_vertex',  # +0
        'webgl_vendor',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_is_fallback_adapter',  # +0
        'wgpu_missing_features',  # +0
    ],
    'Linux': [
        'intl_timezone_web',  # +545,314
        'combined_mathml_hash',  # +248,837
        'screen_primary_avail',  # +231,082
        'hw_processor_count',  # +116,468
        'combined_css_colors_hash',  # +109,165
        'prefs_eme_enabled',  # +75,565
        'storage_quota',  # +73,764
        'canvas_canvasdata12_fingerprintjs1',  # +59,219
        'voices_sha1',  # +32,367
        'user_agent',  # +32,272
        'locale_accept_language',  # +26,662
        'webgl_renderer',  # +15,677
        'screen_color_scheme',  # +7,226
        'screen_web_pixel_ratio',  # +7,017
        'screen_web_avail_left',  # +4,615
        'intl_intl_locale',  # +4,021
        'fonts_fpjs_nonallowlisted',  # +2,324
        'screen_prefers_reduced_motion',  # +1,987
        'screen_web_avail_top',  # +1,588
        'combined_media_capabilities_hash',  # +1,509
        'audio_fingerprint',  # +754
        'screen_prefers_contrast',  # +477
        'sdp_codec_list',  # +333
        'combined_css_fonts_hash',  # +209
        'intl_timezone_offset_web',  # +136
        'combined_webgl1_params_hash',  # +67
        'canvas_canvasdata11_webgl',  # +58
        'combined_wgpu_hash',  # +42
        'screen_primary_resolution',  # +32
        'prefs_pdf_viewer',  # +11
        'canvas_canvasdata13_fingerprintjs2',  # +9
        'prefs_cookiesenabled',  # +6
        'webauthn_capabilities',  # +5
        'webgl_extensions',  # +5
        'webgl_vendor',  # +3
        'platform',  # +1
        'screen_primary_color_depth',  # +1
        'combined_math_ops_hash',  # +0
        'combined_webgl_extensions_hash',  # +0
        'fonts_fpjs_allowlisted',  # +0
        'hw_max_touch_points',  # +0
        'hw_oscpu',  # +0
        'prefs_use_document_colors',  # +0
        'screen_inverted_colors',  # +0
        'screen_monochrome',  # +0
        'screen_prefers_reduced_transparency',  # +0
        'screen_primary_video_dynamic_range',  # +0
        'webgl_precision_fragment',  # +0
        'webgl_precision_vertex',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_is_fallback_adapter',  # +0
        'wgpu_missing_features',  # +0
    ],
    'WINNT': [
        'voices_sha1',  # +2,297,781
        'canvas_canvasdata12_fingerprintjs1',  # +1,711,242
        'fonts_fpjs_nonallowlisted',  # +1,106,665
        'screen_primary_avail',  # +1,065,707
        'intl_timezone_web',  # +950,007
        'combined_css_colors_hash',  # +696,538
        'hw_processor_count',  # +601,074
        'fonts_fpjs_allowlisted',  # +365,878
        'hw_max_touch_points',  # +194,228
        'intl_intl_locale',  # +164,537
        'user_agent',  # +116,759
        'storage_quota',  # +115,279
        'screen_web_pixel_ratio',  # +84,931
        'screen_prefers_reduced_motion',  # +81,824
        'audio_fingerprint',  # +74,632
        'combined_media_capabilities_hash',  # +71,428
        'screen_prefers_reduced_transparency',  # +61,759
        'screen_color_scheme',  # +57,076
        'screen_web_avail_left',  # +56,351
        'locale_accept_language',  # +50,121
        'combined_mathml_hash',  # +24,308
        'webgl_renderer',  # +16,737
        'screen_web_avail_top',  # +13,457
        'combined_math_ops_hash',  # +12,664
        'wgpu_missing_features',  # +4,989
        'prefs_eme_enabled',  # +2,529
        'sdp_codec_list',  # +2,426
        'intl_timezone_offset_web',  # +1,837
        'prefs_pdf_viewer',  # +761
        'canvas_canvasdata11_webgl',  # +732
        'combined_css_fonts_hash',  # +186
        'screen_prefers_contrast',  # +57
        'prefs_cookiesenabled',  # +43
        'screen_inverted_colors',  # +32
        'webauthn_capabilities',  # +27
        'webgl_extensions',  # +26
        'canvas_canvasdata13_fingerprintjs2',  # +18
        'screen_primary_resolution',  # +6
        'combined_wgpu_hash',  # +2
        'platform',  # +1
        'combined_webgl1_params_hash',  # +0
        'combined_webgl_extensions_hash',  # +0
        'hw_oscpu',  # +0
        'prefs_use_document_colors',  # +0
        'screen_monochrome',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_video_dynamic_range',  # +0
        'webgl_precision_fragment',  # +0
        'webgl_precision_vertex',  # +0
        'webgl_vendor',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_is_fallback_adapter',  # +0
    ],
}

MINMETRICS_TOP_METRICS_AKAMAIV2 = [
    'locale_languages',  # +2,097,249
    'canvas_canvasdata12_fingerprintjs1',  # +894,763
    'hw_processor_count',  # +686,477
    'user_agent',  # +361,968
    'prefs_general_donottrack_enabled',  # +155,958
    'screen_primary_avail',  # +125,496
    'hw_max_touch_points',  # +115,083
    'canvas_canvasdata13_fingerprintjs2',  # +52,145
    'locale_accept_language',  # +12,715
    'screen_primary_resolution',  # +8,594
    'hw_oscpu',  # +5,017
    'prefs_cookiesenabled',  # +719
    'screen_primary_color_depth',  # +129
    'platform',  # +19
    'intl_timezone_offset_web',  # +5
    'screen_primary_pixel_depth',  # +0
]

MINMETRICS_TOP_METRICS_BY_OS_AKAMAIV2 = {
    'Android': [
        'locale_accept_language',  # +856,754
        'screen_primary_avail',  # +508,971
        'intl_timezone_offset_web',  # +88,725
        'user_agent',  # +21,865
        'canvas_canvasdata12_fingerprintjs1',  # +20,127
        'hw_processor_count',  # +9,717
        'hw_max_touch_points',  # +7,765
        'canvas_canvasdata13_fingerprintjs2',  # +2,532
        'prefs_general_donottrack_enabled',  # +752
        'prefs_cookiesenabled',  # +305
        'locale_languages',  # +4
        'hw_oscpu',  # +0
        'platform',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_pixel_depth',  # +0
        'screen_primary_resolution',  # +0
    ],
    'Darwin': [
        'locale_accept_language',  # +241,069
        'intl_timezone_offset_web',  # +148,309
        'hw_processor_count',  # +110,726
        'user_agent',  # +87,968
        'canvas_canvasdata12_fingerprintjs1',  # +72,370
        'prefs_general_donottrack_enabled',  # +43,914
        'canvas_canvasdata13_fingerprintjs2',  # +9,888
        'screen_primary_avail',  # +6,708
        'screen_primary_resolution',  # +6,625
        'prefs_cookiesenabled',  # +95
        'locale_languages',  # +13
        'hw_max_touch_points',  # +0
        'hw_oscpu',  # +0
        'platform',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_pixel_depth',  # +0
    ],
    'Linux': [
        'locale_accept_language',  # +173,181
        'intl_timezone_offset_web',  # +164,851
        'screen_primary_avail',  # +111,013
        'user_agent',  # +95,333
        'hw_processor_count',  # +81,535
        'prefs_general_donottrack_enabled',  # +23,712
        'canvas_canvasdata13_fingerprintjs2',  # +23,672
        'canvas_canvasdata12_fingerprintjs1',  # +9,929
        'screen_primary_resolution',  # +433
        'screen_primary_color_depth',  # +82
        'prefs_cookiesenabled',  # +52
        'locale_languages',  # +39
        'platform',  # +6
        'hw_max_touch_points',  # +0
        'hw_oscpu',  # +0
        'screen_primary_pixel_depth',  # +0
    ],
    'WINNT': [
        'locale_accept_language',  # +584,686
        'screen_primary_avail',  # +534,478
        'hw_max_touch_points',  # +159,863
        'intl_timezone_offset_web',  # +122,328
        'user_agent',  # +72,452
        'prefs_general_donottrack_enabled',  # +67,716
        'hw_processor_count',  # +26,885
        'canvas_canvasdata12_fingerprintjs1',  # +14,892
        'canvas_canvasdata13_fingerprintjs2',  # +2,744
        'screen_primary_resolution',  # +534
        'locale_languages',  # +433
        'prefs_cookiesenabled',  # +283
        'platform',  # +3
        'hw_oscpu',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_pixel_depth',  # +0
    ],
}

MINMETRICS_TOP_METRICS_SIGNIFYD = [
    'intl_intl_locale',  # +3,522,244
    'combined_css_colors_hash',  # +2,887,964
    'screen_primary_avail',  # +1,865,835
    'intl_timezone_offset_web',  # +1,433,529
    'hw_processor_count',  # +718,795
    'intl_timezone_web',  # +674,731
    'locale_accept_language',  # +566,154
    'storage_quota',  # +488,756
    'clientrects_known_dimensions',  # +457,472
    'canvas_canvasdata08',  # +407,150
    'screen_color_scheme',  # +389,994
    'screen_web_pixel_ratio',  # +382,631
    'webgl_renderer',  # +372,761
    'screen_prefers_reduced_motion',  # +161,857
    'fonts_variant_h_nonallowlisted',  # +152,726
    'hw_any_pointer_type',  # +138,408
    'prefs_general_globalprivacycontrol_enabled',  # +122,177
    'canvas_canvasdata13_fingerprintjs2',  # +86,418
    'canvas_canvasdata07',  # +78,169
    'hw_max_touch_points',  # +74,042
    'audio_float_frequency_sum',  # +59,721
    'svg_emoji_set',  # +32,707
    'screen_primary_orientation',  # +16,137
    'combined_clientrects_range_gcr_hash',  # +15,931
    'fonts_variant_i_nonallowlisted',  # +15,918
    'svg_bbox',  # +4,053
    'screen_primary_resolution',  # +2,862
    'clientrects_emoji_font_family',  # +2,114
    'combined_css_fonts_hash',  # +1,367
    'wgpu_missing_features',  # +1,186
    'svg_extent_of_char',  # +1,115
    'prefs_general_donottrack_enabled',  # +972
    'user_agent',  # +962
    'audio_compressor_gain_reduction',  # +758
    'audio_unique_samples',  # +731
    'screen_inverted_colors',  # +718
    'prefs_cookiesenabled',  # +659
    'hw_pointer_type',  # +531
    'combined_clientrects_range_gbcr_hash',  # +318
    'canvas_canvasdata02',  # +216
    'fonts_variant_f_allowlisted',  # +176
    'fonts_variant_f_nonallowlisted',  # +162
    'fonts_variant_h_allowlisted',  # +143
    'fonts_variant_i_allowlisted',  # +122
    'screen_primary_color_depth',  # +90
    'combined_clientrects_emoji_hash',  # +48
    'canvas_canvasdata01',  # +34
    'combined_clientrects_element_gcr_hash',  # +33
    'canvassoftware_canvasdata13_fingerprintjs2',  # +33
    'webgl_vendor',  # +28
    'wgpu_maxstoragebufferspershaderstage',  # +18
    'wgpu_maxcomputeworkgroupstoragesize',  # +7
    'hw_oscpu',  # +6
    'platform',  # +5
    'prefs_use_document_colors',  # +4
    'canvassoftware_canvasdata02',  # +3
    'wgpu_maxbindgroups',  # +2
    'canvassoftware_canvasdata01',  # +2
    'fonts_variant_g_allowlisted',  # +2
    'wgpu_maxvertexbuffers',  # +0
    'svg_computed_text_length',  # +0
    'screen_monochrome',  # +0
    'wgpu_maxuniformbufferbindingsize',  # +0
    'fonts_variant_g_nonallowlisted',  # +0
    'wgpu_maxtexturedimension1d',  # +0
    'wgpu_is_fallback_adapter',  # +0
    'wgpu_maxvertexattributes',  # +0
    'wgpu_maxcolorattachments',  # +0
    'wgpu_maxdynamicstoragebuffersperpipelinelayout',  # +0
    'wgpu_maxtexturedimension2d',  # +0
    'wgpu_maxbuffersize',  # +0
    'wgpu_maxcomputeinvocationsperworkgroup',  # +0
    'screen_primary_pixel_depth',  # +0
    'svg_substring_length',  # +0
    'wgpu_maxdynamicuniformbuffersperpipelinelayout',  # +0
    'clientrects_text_font_family',  # +0
    'combined_clientrects_element_gbcr_hash',  # +0
    'wgpu_maxtexturedimension3d',  # +0
    'webgl_vendor_raw',  # +0
    'audio_fingerprint2',  # +0
    'audio_float_time_domain_sum',  # +0
    'clientrects_ghost_dimensions',  # +0
]

MINMETRICS_TOP_METRICS_BY_OS_SIGNIFYD = {
    'Android': [
        'screen_web_pixel_ratio',  # +1,266,513
        'webgl_renderer',  # +1,175,391
        'locale_accept_language',  # +1,040,485
        'intl_timezone_web',  # +635,684
        'canvas_canvasdata08',  # +297,306
        'svg_bbox',  # +221,586
        'storage_quota',  # +166,250
        'screen_primary_avail',  # +125,454
        'screen_primary_orientation',  # +83,420
        'screen_prefers_reduced_motion',  # +73,238
        'hw_any_pointer_type',  # +57,032
        'canvas_canvasdata07',  # +46,428
        'prefs_general_globalprivacycontrol_enabled',  # +43,940
        'combined_clientrects_range_gcr_hash',  # +34,328
        'user_agent',  # +19,576
        'hw_processor_count',  # +17,645
        'combined_css_colors_hash',  # +13,360
        'svg_emoji_set',  # +5,197
        'intl_timezone_offset_web',  # +2,538
        'screen_color_scheme',  # +1,925
        'audio_float_frequency_sum',  # +1,866
        'fonts_variant_h_nonallowlisted',  # +868
        'prefs_general_donottrack_enabled',  # +597
        'hw_max_touch_points',  # +461
        'intl_intl_locale',  # +356
        'combined_css_fonts_hash',  # +134
        'screen_inverted_colors',  # +130
        'prefs_cookiesenabled',  # +96
        'canvas_canvasdata13_fingerprintjs2',  # +74
        'fonts_variant_i_nonallowlisted',  # +17
        'canvas_canvasdata01',  # +10
        'canvas_canvasdata02',  # +9
        'wgpu_is_fallback_adapter',  # +2
        'audio_compressor_gain_reduction',  # +0
        'audio_fingerprint2',  # +0
        'audio_float_time_domain_sum',  # +0
        'audio_unique_samples',  # +0
        'canvassoftware_canvasdata01',  # +0
        'canvassoftware_canvasdata02',  # +0
        'canvassoftware_canvasdata13_fingerprintjs2',  # +0
        'clientrects_emoji_font_family',  # +0
        'clientrects_ghost_dimensions',  # +0
        'clientrects_known_dimensions',  # +0
        'clientrects_text_font_family',  # +0
        'combined_clientrects_element_gbcr_hash',  # +0
        'combined_clientrects_element_gcr_hash',  # +0
        'combined_clientrects_emoji_hash',  # +0
        'combined_clientrects_range_gbcr_hash',  # +0
        'fonts_variant_f_allowlisted',  # +0
        'fonts_variant_f_nonallowlisted',  # +0
        'fonts_variant_g_allowlisted',  # +0
        'fonts_variant_g_nonallowlisted',  # +0
        'fonts_variant_h_allowlisted',  # +0
        'fonts_variant_i_allowlisted',  # +0
        'hw_oscpu',  # +0
        'hw_pointer_type',  # +0
        'platform',  # +0
        'prefs_use_document_colors',  # +0
        'screen_monochrome',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_pixel_depth',  # +0
        'screen_primary_resolution',  # +0
        'svg_computed_text_length',  # +0
        'svg_extent_of_char',  # +0
        'svg_substring_length',  # +0
        'webgl_vendor',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_maxbindgroups',  # +0
        'wgpu_maxbuffersize',  # +0
        'wgpu_maxcolorattachments',  # +0
        'wgpu_maxcomputeinvocationsperworkgroup',  # +0
        'wgpu_maxcomputeworkgroupstoragesize',  # +0
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',  # +0
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',  # +0
        'wgpu_maxstoragebufferspershaderstage',  # +0
        'wgpu_maxtexturedimension1d',  # +0
        'wgpu_maxtexturedimension2d',  # +0
        'wgpu_maxtexturedimension3d',  # +0
        'wgpu_maxuniformbufferbindingsize',  # +0
        'wgpu_maxvertexattributes',  # +0
        'wgpu_maxvertexbuffers',  # +0
        'wgpu_missing_features',  # +0
    ],
    'Darwin': [
        'intl_timezone_web',  # +597,782
        'fonts_variant_h_nonallowlisted',  # +231,165
        'intl_intl_locale',  # +174,530
        'webgl_renderer',  # +152,683
        'screen_web_pixel_ratio',  # +95,189
        'combined_css_colors_hash',  # +92,431
        'canvas_canvasdata08',  # +86,078
        'prefs_general_donottrack_enabled',  # +37,910
        'locale_accept_language',  # +27,805
        'user_agent',  # +27,189
        'prefs_general_globalprivacycontrol_enabled',  # +22,478
        'hw_processor_count',  # +20,284
        'screen_color_scheme',  # +15,761
        'combined_clientrects_range_gcr_hash',  # +10,317
        'screen_primary_avail',  # +6,708
        'screen_prefers_reduced_motion',  # +5,591
        'svg_bbox',  # +4,354
        'screen_primary_resolution',  # +2,379
        'audio_float_frequency_sum',  # +1,057
        'storage_quota',  # +795
        'intl_timezone_offset_web',  # +554
        'canvas_canvasdata07',  # +171
        'combined_css_fonts_hash',  # +130
        'fonts_variant_i_nonallowlisted',  # +56
        'prefs_cookiesenabled',  # +21
        'svg_emoji_set',  # +21
        'canvas_canvasdata13_fingerprintjs2',  # +10
        'wgpu_is_fallback_adapter',  # +9
        'screen_inverted_colors',  # +8
        'fonts_variant_h_allowlisted',  # +3
        'canvas_canvasdata02',  # +2
        'clientrects_emoji_font_family',  # +2
        'canvas_canvasdata01',  # +1
        'audio_compressor_gain_reduction',  # +0
        'audio_fingerprint2',  # +0
        'audio_float_time_domain_sum',  # +0
        'audio_unique_samples',  # +0
        'canvassoftware_canvasdata01',  # +0
        'canvassoftware_canvasdata02',  # +0
        'canvassoftware_canvasdata13_fingerprintjs2',  # +0
        'clientrects_ghost_dimensions',  # +0
        'clientrects_known_dimensions',  # +0
        'clientrects_text_font_family',  # +0
        'combined_clientrects_element_gbcr_hash',  # +0
        'combined_clientrects_element_gcr_hash',  # +0
        'combined_clientrects_emoji_hash',  # +0
        'combined_clientrects_range_gbcr_hash',  # +0
        'fonts_variant_f_allowlisted',  # +0
        'fonts_variant_f_nonallowlisted',  # +0
        'fonts_variant_g_allowlisted',  # +0
        'fonts_variant_g_nonallowlisted',  # +0
        'fonts_variant_i_allowlisted',  # +0
        'hw_any_pointer_type',  # +0
        'hw_max_touch_points',  # +0
        'hw_oscpu',  # +0
        'hw_pointer_type',  # +0
        'platform',  # +0
        'prefs_use_document_colors',  # +0
        'screen_monochrome',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_orientation',  # +0
        'screen_primary_pixel_depth',  # +0
        'svg_computed_text_length',  # +0
        'svg_extent_of_char',  # +0
        'svg_substring_length',  # +0
        'webgl_vendor',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_maxbindgroups',  # +0
        'wgpu_maxbuffersize',  # +0
        'wgpu_maxcolorattachments',  # +0
        'wgpu_maxcomputeinvocationsperworkgroup',  # +0
        'wgpu_maxcomputeworkgroupstoragesize',  # +0
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',  # +0
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',  # +0
        'wgpu_maxstoragebufferspershaderstage',  # +0
        'wgpu_maxtexturedimension1d',  # +0
        'wgpu_maxtexturedimension2d',  # +0
        'wgpu_maxtexturedimension3d',  # +0
        'wgpu_maxuniformbufferbindingsize',  # +0
        'wgpu_maxvertexattributes',  # +0
        'wgpu_maxvertexbuffers',  # +0
        'wgpu_missing_features',  # +0
    ],
    'Linux': [
        'intl_timezone_web',  # +505,814
        'screen_primary_avail',  # +362,497
        'combined_css_colors_hash',  # +109,165
        'hw_processor_count',  # +105,450
        'screen_web_pixel_ratio',  # +100,140
        'canvas_canvasdata08',  # +72,958
        'storage_quota',  # +66,114
        'locale_accept_language',  # +47,884
        'combined_clientrects_range_gcr_hash',  # +35,765
        'user_agent',  # +32,272
        'fonts_variant_h_nonallowlisted',  # +27,976
        'prefs_general_globalprivacycontrol_enabled',  # +17,612
        'webgl_renderer',  # +15,677
        'screen_color_scheme',  # +15,585
        'fonts_variant_i_allowlisted',  # +10,545
        'intl_intl_locale',  # +6,960
        'prefs_general_donottrack_enabled',  # +4,737
        'screen_prefers_reduced_motion',  # +4,097
        'combined_css_fonts_hash',  # +3,258
        'audio_float_frequency_sum',  # +1,828
        'canvas_canvasdata07',  # +1,030
        'svg_bbox',  # +306
        'intl_timezone_offset_web',  # +240
        'fonts_variant_i_nonallowlisted',  # +111
        'screen_primary_resolution',  # +63
        'wgpu_is_fallback_adapter',  # +59
        'svg_emoji_set',  # +24
        'canvas_canvasdata01',  # +23
        'canvas_canvasdata13_fingerprintjs2',  # +12
        'webgl_vendor',  # +10
        'prefs_cookiesenabled',  # +6
        'clientrects_emoji_font_family',  # +6
        'fonts_variant_f_allowlisted',  # +6
        'fonts_variant_h_allowlisted',  # +5
        'canvas_canvasdata02',  # +2
        'combined_clientrects_emoji_hash',  # +1
        'platform',  # +1
        'screen_primary_color_depth',  # +1
        'audio_compressor_gain_reduction',  # +0
        'audio_fingerprint2',  # +0
        'audio_float_time_domain_sum',  # +0
        'audio_unique_samples',  # +0
        'canvassoftware_canvasdata01',  # +0
        'canvassoftware_canvasdata02',  # +0
        'canvassoftware_canvasdata13_fingerprintjs2',  # +0
        'clientrects_ghost_dimensions',  # +0
        'clientrects_known_dimensions',  # +0
        'clientrects_text_font_family',  # +0
        'combined_clientrects_element_gbcr_hash',  # +0
        'combined_clientrects_element_gcr_hash',  # +0
        'combined_clientrects_range_gbcr_hash',  # +0
        'fonts_variant_f_nonallowlisted',  # +0
        'fonts_variant_g_allowlisted',  # +0
        'fonts_variant_g_nonallowlisted',  # +0
        'hw_any_pointer_type',  # +0
        'hw_max_touch_points',  # +0
        'hw_oscpu',  # +0
        'hw_pointer_type',  # +0
        'prefs_use_document_colors',  # +0
        'screen_inverted_colors',  # +0
        'screen_monochrome',  # +0
        'screen_primary_orientation',  # +0
        'screen_primary_pixel_depth',  # +0
        'svg_computed_text_length',  # +0
        'svg_extent_of_char',  # +0
        'svg_substring_length',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_maxbindgroups',  # +0
        'wgpu_maxbuffersize',  # +0
        'wgpu_maxcolorattachments',  # +0
        'wgpu_maxcomputeinvocationsperworkgroup',  # +0
        'wgpu_maxcomputeworkgroupstoragesize',  # +0
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',  # +0
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',  # +0
        'wgpu_maxstoragebufferspershaderstage',  # +0
        'wgpu_maxtexturedimension1d',  # +0
        'wgpu_maxtexturedimension2d',  # +0
        'wgpu_maxtexturedimension3d',  # +0
        'wgpu_maxuniformbufferbindingsize',  # +0
        'wgpu_maxvertexattributes',  # +0
        'wgpu_maxvertexbuffers',  # +0
        'wgpu_missing_features',  # +0
    ],
    'WINNT': [
        'screen_primary_avail',  # +1,857,891
        'screen_web_pixel_ratio',  # +909,446
        'intl_timezone_web',  # +889,606
        'intl_intl_locale',  # +679,904
        'canvas_canvasdata08',  # +316,724
        'storage_quota',  # +278,147
        'hw_max_touch_points',  # +258,359
        'screen_prefers_reduced_motion',  # +234,769
        'audio_float_frequency_sum',  # +186,809
        'user_agent',  # +171,137
        'locale_accept_language',  # +163,054
        'screen_color_scheme',  # +143,105
        'prefs_general_donottrack_enabled',  # +106,748
        'svg_emoji_set',  # +87,365
        'combined_clientrects_range_gcr_hash',  # +70,658
        'prefs_general_globalprivacycontrol_enabled',  # +68,455
        'combined_css_colors_hash',  # +64,829
        'svg_bbox',  # +52,044
        'hw_processor_count',  # +37,221
        'wgpu_missing_features',  # +18,145
        'webgl_renderer',  # +16,737
        'canvas_canvasdata13_fingerprintjs2',  # +9,588
        'hw_pointer_type',  # +9,372
        'intl_timezone_offset_web',  # +6,024
        'canvas_canvasdata07',  # +5,668
        'fonts_variant_h_nonallowlisted',  # +3,885
        'screen_primary_orientation',  # +740
        'combined_css_fonts_hash',  # +634
        'hw_any_pointer_type',  # +508
        'prefs_cookiesenabled',  # +110
        'screen_inverted_colors',  # +99
        'fonts_variant_i_nonallowlisted',  # +71
        'clientrects_emoji_font_family',  # +69
        'screen_primary_resolution',  # +51
        'fonts_variant_f_allowlisted',  # +51
        'wgpu_maxstoragebufferspershaderstage',  # +18
        'combined_clientrects_emoji_hash',  # +12
        'canvas_canvasdata02',  # +9
        'canvassoftware_canvasdata13_fingerprintjs2',  # +7
        'prefs_use_document_colors',  # +5
        'canvas_canvasdata01',  # +1
        'platform',  # +1
        'webgl_vendor',  # +1
        'audio_compressor_gain_reduction',  # +0
        'audio_fingerprint2',  # +0
        'audio_float_time_domain_sum',  # +0
        'audio_unique_samples',  # +0
        'canvassoftware_canvasdata01',  # +0
        'canvassoftware_canvasdata02',  # +0
        'clientrects_ghost_dimensions',  # +0
        'clientrects_known_dimensions',  # +0
        'clientrects_text_font_family',  # +0
        'combined_clientrects_element_gbcr_hash',  # +0
        'combined_clientrects_element_gcr_hash',  # +0
        'combined_clientrects_range_gbcr_hash',  # +0
        'fonts_variant_f_nonallowlisted',  # +0
        'fonts_variant_g_allowlisted',  # +0
        'fonts_variant_g_nonallowlisted',  # +0
        'fonts_variant_h_allowlisted',  # +0
        'fonts_variant_i_allowlisted',  # +0
        'hw_oscpu',  # +0
        'screen_monochrome',  # +0
        'screen_primary_color_depth',  # +0
        'screen_primary_pixel_depth',  # +0
        'svg_computed_text_length',  # +0
        'svg_extent_of_char',  # +0
        'svg_substring_length',  # +0
        'webgl_vendor_raw',  # +0
        'wgpu_is_fallback_adapter',  # +0
        'wgpu_maxbindgroups',  # +0
        'wgpu_maxbuffersize',  # +0
        'wgpu_maxcolorattachments',  # +0
        'wgpu_maxcomputeinvocationsperworkgroup',  # +0
        'wgpu_maxcomputeworkgroupstoragesize',  # +0
        'wgpu_maxdynamicstoragebuffersperpipelinelayout',  # +0
        'wgpu_maxdynamicuniformbuffersperpipelinelayout',  # +0
        'wgpu_maxtexturedimension1d',  # +0
        'wgpu_maxtexturedimension2d',  # +0
        'wgpu_maxtexturedimension3d',  # +0
        'wgpu_maxuniformbufferbindingsize',  # +0
        'wgpu_maxvertexattributes',  # +0
        'wgpu_maxvertexbuffers',  # +0
    ],
}
