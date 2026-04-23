"""## Define the DataValues class

This class contains all the metrics we report through telemetry.  Whenever a new metric is added, we must also add it in to this class.

To try and reduce the amount of verbosity, we use reflection in several places (debugprinter, fingerprint algorithm with a default subset) to enumerate all the metrics we've added.

This means we must explicitly add bookkeeping members (i.e. members that don't come from telemetry) to the ignore list for the default subset.
"""

import hashlib
import json
import sys
import time
from datetime import datetime
import zoneinfo
from collections import defaultdict

import tqdm

import config
from utility import *
from filters import *
from fingerprint import SHA1Fingerprint
from data import record_has_errors

from webgl_constants import *


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

_DEFAULT_IGNORE_SET = frozenset({
    'filters', 'client_id', 'submission_date', 'channel',
    'app_name', 'screens', 'errors', 'errors_js', 'country',
})
_DEBUGPRINT_IGNORE_SET = frozenset({'filters', 'client_id'})

# CSS system color names (as reported by Firefox, case-sensitive).
# Attributes are stored as css_color_<name.lower()>.
_CSS_COLOR_NAMES = [
    "Canvas", "CanvasText", "LinkText", "VisitedText", "ActiveText",
    "ButtonFace", "ButtonText", "ButtonBorder", "ButtonHighlight",
    "Field", "FieldText", "Highlight", "HighlightText",
    "SelectedItem", "SelectedItemText", "AccentColor", "AccentColorText",
    "Mark", "MarkText", "GrayText", "ActiveBorder", "ActiveCaption",
    "AppWorkspace", "Background", "ButtonShadow", "CaptionText",
    "InactiveBorder", "InactiveCaption", "InactiveCaptionText",
    "InfoBackground", "InfoText", "Menu", "MenuText", "Scrollbar",
    "ThreeDDarkShadow", "ThreeDFace", "ThreeDHighlight", "ThreeDLightShadow",
    "ThreeDShadow", "Window", "WindowFrame", "WindowText",
]

# CSS system font keywords → Python attribute suffix (stored as css_font_<suffix>).
_CSS_FONT_ATTR_SUFFIXES = {
    "caption":          "caption",
    "icon":             "icon",
    "menu":             "menu",
    "message-box":      "message_box",
    "small-caption":    "small_caption",
    "status-bar":       "status_bar",
    "serif":            "serif",
    "sans-serif":       "sans_serif",
    "monospace":        "monospace",
    "cursive":          "cursive",
    "fantasy":          "fantasy",
    "system-ui":        "system_ui",
    "Arial":            "arial",
    "Helvetica":        "helvetica",
    "Times New Roman":  "times_new_roman",
    "Courier New":      "courier_new",
    "Verdana":          "verdana",
    "Georgia":          "georgia",
}

# Number of mathml_diag_* values (matches math[id^='new-'] elements in the HTML page).
_MATHML_DIAG_COUNT = 19

def _combined_hash(s: str) -> str:
    """Hash a JSON string to a full SHA-256 hex digest, storing hash→string in config.COMBINED_HASH_LOOKUP."""
    h = hashlib.sha256(s.encode()).hexdigest()
    config.COMBINED_HASH_LOOKUP[h] = s
    return h

# Static definition of all non-dynamic DataValues attributes.
# math_op_{i}, math_op_fdlibm_{i}, and math_op_diag_{i} are excluded (count depends on data)
# and added dynamically by _validate_and_complete_default_subset().
_DEFAULT_SUBSET_BASE = frozenset({
    "audio_channels",
    "audio_compressor_gain_reduction",
    "audio_fingerprint",
    "audio_fingerprint2",
    "audio_float_frequency_sum",
    "audio_float_time_domain_sum",
    "audio_frames",
    "audio_rate",
    "audio_unique_samples",
    "build_date",
    "canvas_canvasdata01",
    # "canvas_canvasdata01_raw",  # disabled — raw PNG bytes, not loaded
    "canvas_canvasdata02",
    # "canvas_canvasdata02_raw",
    "canvas_canvasdata03",
    # "canvas_canvasdata03_raw",
    "canvas_canvasdata04",
    # "canvas_canvasdata04_raw",
    "canvas_canvasdata05",
    # "canvas_canvasdata05_raw",
    "canvas_canvasdata06",
    # "canvas_canvasdata06_raw",
    "canvas_canvasdata07",
    # "canvas_canvasdata07_raw",
    "canvas_canvasdata08",
    # "canvas_canvasdata08_raw",
    "canvas_canvasdata09",
    # "canvas_canvasdata09_raw",
    "canvas_canvasdata10",
    # "canvas_canvasdata10_raw",
    "canvas_canvasdata11_webgl",
    # "canvas_canvasdata11_webgl_raw",
    "canvas_canvasdata12_fingerprintjs1",
    # "canvas_canvasdata12_fingerprintjs1_raw",
    "canvas_canvasdata13_fingerprintjs2",
    # "canvas_canvasdata13_fingerprintjs2_raw",
    "combined_canvas_hardware_hash",
    "canvas_dpr",
    "canvas_feature_status",
    "canvassoftware_canvasdata01",
    # "canvassoftware_canvasdata01_raw",
    "canvassoftware_canvasdata02",
    # "canvassoftware_canvasdata02_raw",
    "canvassoftware_canvasdata03",
    # "canvassoftware_canvasdata03_raw",
    "canvassoftware_canvasdata04",
    # "canvassoftware_canvasdata04_raw",
    "canvassoftware_canvasdata05",
    # "canvassoftware_canvasdata05_raw",
    "canvassoftware_canvasdata06",
    # "canvassoftware_canvasdata06_raw",
    "canvassoftware_canvasdata07",
    # "canvassoftware_canvasdata07_raw",
    "canvassoftware_canvasdata08",
    # "canvassoftware_canvasdata08_raw",
    "canvassoftware_canvasdata09",
    # "canvassoftware_canvasdata09_raw",
    "canvassoftware_canvasdata10",
    # "canvassoftware_canvasdata10_raw",
    "canvassoftware_canvasdata11_webgl",
    # "canvassoftware_canvasdata11_webgl_raw",
    "canvassoftware_canvasdata12_fingerprintjs1",
    # "canvassoftware_canvasdata12_fingerprintjs1_raw",
    "canvassoftware_canvasdata13_fingerprintjs2",
    # "canvassoftware_canvasdata13_fingerprintjs2_raw",
    "combined_canvas_software_hash",
    "clientrects_element_gbcr_01",
    "clientrects_element_gbcr_02",
    "clientrects_element_gbcr_03",
    "clientrects_element_gbcr_04",
    "clientrects_element_gbcr_05",
    "clientrects_element_gbcr_06",
    "clientrects_element_gbcr_07",
    "clientrects_element_gbcr_08",
    "clientrects_element_gbcr_09",
    "clientrects_element_gbcr_10",
    "clientrects_element_gbcr_11",
    "clientrects_element_gbcr_12",
    "clientrects_element_gcr_01",
    "clientrects_element_gcr_02",
    "clientrects_element_gcr_03",
    "clientrects_element_gcr_04",
    "clientrects_element_gcr_05",
    "clientrects_element_gcr_06",
    "clientrects_element_gcr_07",
    "clientrects_element_gcr_08",
    "clientrects_element_gcr_09",
    "clientrects_element_gcr_10",
    "clientrects_element_gcr_11",
    "clientrects_element_gcr_12",
    "clientrects_emoji_01",
    "clientrects_emoji_02",
    "clientrects_emoji_03",
    "clientrects_emoji_04",
    "clientrects_emoji_05",
    "clientrects_emoji_06",
    "combined_clientrects_element_gbcr_hash",
    "combined_clientrects_element_gcr_hash",
    "combined_clientrects_range_gbcr_hash",
    "combined_clientrects_range_gcr_hash",
    "combined_clientrects_emoji_hash",
    "clientrects_emoji_font_family",
    "clientrects_ghost_dimensions",
    "clientrects_known_dimensions",
    "clientrects_range_gbcr_01",
    "clientrects_range_gbcr_02",
    "clientrects_range_gbcr_03",
    "clientrects_range_gbcr_04",
    "clientrects_range_gbcr_05",
    "clientrects_range_gbcr_06",
    "clientrects_range_gbcr_07",
    "clientrects_range_gbcr_08",
    "clientrects_range_gbcr_09",
    "clientrects_range_gbcr_10",
    "clientrects_range_gbcr_11",
    "clientrects_range_gbcr_12",
    "clientrects_range_gcr_01",
    "clientrects_range_gcr_02",
    "clientrects_range_gcr_03",
    "clientrects_range_gcr_04",
    "clientrects_range_gcr_05",
    "clientrects_range_gcr_06",
    "clientrects_range_gcr_07",
    "clientrects_range_gcr_08",
    "clientrects_range_gcr_09",
    "clientrects_range_gcr_10",
    "clientrects_range_gcr_11",
    "clientrects_range_gcr_12",
    "clientrects_text_font_family",
    "css_color_accentcolor",
    "css_color_accentcolortext",
    "css_color_activeborder",
    "css_color_activecaption",
    "css_color_activetext",
    "css_color_appworkspace",
    "css_color_background",
    "css_color_buttonborder",
    "css_color_buttonface",
    "css_color_buttonhighlight",
    "css_color_buttonshadow",
    "css_color_buttontext",
    "css_color_canvas",
    "css_color_canvastext",
    "css_color_captiontext",
    "css_color_field",
    "css_color_fieldtext",
    "css_color_graytext",
    "css_color_highlight",
    "css_color_highlighttext",
    "css_color_inactiveborder",
    "css_color_inactivecaption",
    "css_color_inactivecaptiontext",
    "css_color_infobackground",
    "css_color_infotext",
    "css_color_linktext",
    "css_color_mark",
    "css_color_marktext",
    "css_color_menu",
    "css_color_menutext",
    "css_color_scrollbar",
    "css_color_selecteditem",
    "css_color_selecteditemtext",
    "css_color_threeddarkshadow",
    "css_color_threedface",
    "css_color_threedhighlight",
    "css_color_threedlightshadow",
    "css_color_threedshadow",
    "css_color_visitedtext",
    "css_color_window",
    "css_color_windowframe",
    "css_color_windowtext",
    "combined_css_colors_hash",
    "css_font_arial",
    "css_font_caption",
    "css_font_courier_new",
    "css_font_cursive",
    "css_font_fantasy",
    "css_font_georgia",
    "css_font_helvetica",
    "css_font_icon",
    "css_font_menu",
    "css_font_message_box",
    "css_font_monospace",
    "css_font_sans_serif",
    "css_font_serif",
    "css_font_small_caption",
    "css_font_status_bar",
    "css_font_system_ui",
    "css_font_times_new_roman",
    "css_font_verdana",
    "combined_css_fonts_hash",
    "font_css_system_colors",
    "font_css_system_fonts",
    "font_default_default_group",
    "font_default_western",
    "font_font_name_list_emoji_modified",
    "font_minimum_size_default_group",
    "font_minimum_size_western",
    "font_name_monospace_default_group",
    "font_name_monospace_western",
    "font_name_sans_serif_default_group",
    "font_name_sans_serif_western",
    "font_name_serif_default_group",
    "font_name_serif_western",
    "font_prefcolor_accentcolor",
    "font_prefcolor_accentcolortext",
    "font_prefcolor_canvas",
    "font_prefcolor_canvastext",
    "font_prefcolor_highlight",
    "font_prefcolor_highlighttext",
    "font_prefcolor_selecteditem",
    "font_prefcolor_selecteditemtext",
    "font_prefmodified_default",
    "font_prefmodified_minimum_size",
    "font_prefmodified_name_list_cursive",
    "font_prefmodified_name_list_monospace",
    "font_prefmodified_name_list_sans_serif",
    "font_prefmodified_name_list_serif",
    "font_prefmodified_name_monospace",
    "font_prefmodified_name_sans_serif",
    "font_prefmodified_name_serif",
    "font_prefmodified_size_monospace",
    "font_prefmodified_size_variable",
    "font_prefs_browser_display_use_document_fonts",
    "font_size_monospace_default_group",
    "font_size_monospace_western",
    "font_size_variable_default_group",
    "font_size_variable_western",
    "fonts_fpjs_allowlisted",
    "fonts_fpjs_nonallowlisted",
    "combined_fonts_variants_allowlisted_hash",
    "combined_fonts_variants_nonallowlisted_hash",
    "fonts_variant_a_allowlisted",
    "fonts_variant_a_nonallowlisted",
    "fonts_variant_b_allowlisted",
    "fonts_variant_b_nonallowlisted",
    "fonts_variant_c_allowlisted",
    "fonts_variant_c_nonallowlisted",
    "fonts_variant_d_allowlisted",
    "fonts_variant_d_nonallowlisted",
    "fonts_variant_e_allowlisted",
    "fonts_variant_e_nonallowlisted",
    "fonts_variant_f_allowlisted",
    "fonts_variant_f_nonallowlisted",
    "fonts_variant_g_allowlisted",
    "fonts_variant_g_nonallowlisted",
    "fonts_variant_h_allowlisted",
    "fonts_variant_h_nonallowlisted",
    "fonts_variant_i_allowlisted",
    "fonts_variant_i_nonallowlisted",
    "hw_any_pointer_type",
    "hw_camera_count",
    "hw_cpu_arch",
    "hw_cpu_model",
    "hw_firefox_binary_arch",
    "hw_fpu_control_state",
    "hw_gamepads",
    "hw_group_count",
    "hw_group_count_wo_speakers",
    "hw_machine_model",
    "hw_max_touch_points",
    "screen_count",

    "hw_microphone_count",
    "hw_motion_decimals",
    "hw_motion_freq",
    "hw_orientation_decimals",
    "hw_orientation_freq",
    "hw_orientationabs_decimals",
    "hw_orientationabs_freq",
    "hw_oscpu",
    "hw_pointer_height",
    "hw_pointer_pressure",
    "hw_pointer_tangentinal_pressure",
    "hw_pointer_tiltx",
    "hw_pointer_tilty",
    "hw_pointer_twist",
    "hw_pointer_type",
    "hw_pointer_width",
    "hw_processor_count",
    "hw_speaker_count",
    "hw_touch_rotation_angle",
    "mathml_diag_values",
    "ice_order",
    "ice_sd",
    "intl_intl_locale",
    "intl_keyboard_layout",
    "intl_system_locale",
    "intl_timezone",
    "intl_timezone_offset_web",
    "intl_timezone_web",
    "intl_timezoneoffset",
    "locale_accept_language",
    "locale_languages",
    "math_ops",
    "math_ops_fdlibm",
    "math_ops_fdlibm_2",
    "combined_math_ops_hash",
    "combined_math_ops_fdlibm_hash",
    "combined_math_ops_diag_hash",
    "mathml_1",
    "mathml_10",
    "mathml_2",
    "mathml_3",
    "mathml_4",
    "mathml_5",
    "mathml_6",
    "mathml_7",
    "mathml_8",
    "mathml_9",
    "combined_mathml_hash",
    "mathml_diag_font_family",
    "mathml_diag_prefs_modified",
    "combined_mathml_diag_hash",
    "mathml_diag_1",
    "mathml_diag_2",
    "mathml_diag_3",
    "mathml_diag_4",
    "mathml_diag_5",
    "mathml_diag_6",
    "mathml_diag_7",
    "mathml_diag_8",
    "mathml_diag_9",
    "mathml_diag_10",
    "mathml_diag_11",
    "mathml_diag_12",
    "mathml_diag_13",
    "mathml_diag_14",
    "mathml_diag_15",
    "mathml_diag_16",
    "mathml_diag_17",
    "mathml_diag_18",
    "mathml_diag_19",
    "media_capabilities_not_efficient",
    "media_capabilities_not_smooth",
    "media_capabilities_unsupported",
    "media_h264",
    "combined_media_capabilities_hash",
    "missing_fonts",
    "os",
    "os_distro",
    "os_distro_id",
    "os_distro_version",
    "os_version",
    "platform",
    "prefs_block_popups",
    "prefs_changed_media_prefs",
    "prefs_cookiebehavior",
    "prefs_cookiesenabled",
    "prefs_eme_enabled",
    "prefs_general_autoscroll",
    "prefs_general_donottrack_enabled",
    "prefs_general_globalprivacycontrol_enabled",
    "prefs_general_overlay_scrollbars",
    "prefs_general_smoothscroll",
    "prefs_pdf_viewer",
    "prefs_use_document_colors",
    "prefs_zoom_count",
    "prefs_zoom_text_only",
    "schema",
    "screen_color_scheme",
    "screen_inverted_colors",
    "screen_monochrome",
    "screen_prefers_contrast",
    "screen_prefers_reduced_motion",
    "screen_prefers_reduced_transparency",
    "screen_primary_avail",
    "screen_primary_avail_diff",
    "screen_primary_avail_height",
    "screen_primary_avail_height_diff",
    "screen_primary_avail_left",
    "screen_primary_avail_top",
    "screen_primary_avail_width",
    "screen_primary_avail_width_diff",
    "screen_primary_color_depth",
    "screen_primary_orientation",
    "screen_primary_orientation_angle",
    "screen_primary_pixel_depth",
    "screen_primary_posx",
    "screen_primary_posy",
    "screen_primary_resolution",
    "screen_primary_resolution_height",
    "screen_primary_resolution_width",
    "screen_primary_scale_factor",
    "screen_primary_video_dynamic_range",
    "screen_size_mode",
    "screen_text_anti_aliasing",
    "screen_web_avail",
    "screen_web_avail_diff",
    "screen_web_avail_height",
    "screen_web_avail_height_diff",
    "screen_web_avail_left",
    "screen_web_avail_top",
    "screen_web_avail_width",
    "screen_web_avail_width_diff",
    "screen_web_inner",
    "screen_web_inner_diff",
    "screen_web_inner_height",
    "screen_web_inner_height_diff",
    "screen_web_inner_width",
    "screen_web_inner_width_diff",
    "screen_web_outer",
    "screen_web_outer_diff",
    "screen_web_outer_height",
    "screen_web_outer_height_diff",
    "screen_web_outer_inner_diff",
    "screen_web_outer_inner_height_diff",
    "screen_web_outer_inner_width_diff",
    "screen_web_outer_width",
    "screen_web_outer_width_diff",
    "screen_web_pixel_ratio",
    "screen_web_resolution",
    "screen_web_resolution_height",
    "screen_web_resolution_width",
    "sdp_codec_list",
    "storage_quota",
    "svg_bbox",
    "svg_computed_text_length",
    "svg_emoji_set",
    "svg_extent_of_char",
    "svg_substring_length",
    "target_frame_rate",
    "user_agent",
    "using_accelerated_canvas",
    "version",
    "voices_all_ssdeep",
    "voices_count",
    "voices_default",
    "voices_local_count",
    "voices_local_ssdeep",
    "voices_nonlocal_ssdeep",
    "voices_sample",
    "voices_sha1",
    "webauthn_capabilities",
    "webgl2_alpha",
    "webgl2_alpha_software",
    "webgl2_antialias",
    "webgl2_antialias_software",
    "webgl2_context_type",
    "webgl2_context_type_software",
    "webgl2_extensions",
    "webgl2_extensions_raw",
    "webgl2_extensions_raw_software",
    "webgl2_extensions_software",
    "webgl2_fragment_shader",
    "webgl2_fragment_shader_software",
    "webgl2_minimal_source",
    "webgl2_minimal_source_software",
    "combined_webgl1_params_hash",
    "combined_webgl1_params_sw_hash",
    "combined_webgl2_params_hash",
    "combined_webgl2_params_sw_hash",
    "combined_webgl_extensions_hash",
    "combined_webgl_extensions_sw_hash",
    "combined_webgl2_extensions_hash",
    "combined_webgl2_extensions_sw_hash",
    "webgl2_params",
    "webgl2_params_extensions",
    "webgl2_params_extensions_EXT_disjoint_timer_query",
    "webgl2_params_extensions_EXT_texture_filter_anisotropic",
    "webgl2_params_extensions_OVR_multiview2",
    "webgl2_params_extensions_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL",
    "webgl2_params_extensions_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL",
    "webgl2_params_extensions_json",
    "webgl2_params_extensions_json_software",
    "webgl2_params_extensions_software",
    "webgl2_params_extensions_software_EXT_disjoint_timer_query",
    "webgl2_params_extensions_software_EXT_texture_filter_anisotropic",
    "webgl2_params_extensions_software_OVR_multiview2",
    "webgl2_params_extensions_software_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL",
    "webgl2_params_extensions_software_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL",
    "webgl2_params_json",
    "webgl2_params_json_software",
    "webgl2_params_software",
    "webgl2_precision_fragment",
    "webgl2_precision_fragment_software",
    "webgl2_precision_vertex",
    "webgl2_precision_vertex_software",
    "webgl2_renderer",
    "webgl2_renderer_raw",
    "webgl2_renderer_raw_software",
    "webgl2_renderer_software",
    "webgl2_vendor",
    "webgl2_vendor_raw",
    "webgl2_vendor_raw_software",
    "webgl2_vendor_software",
    "webgl2_version_raw",
    "webgl2_version_raw_software",
    "webgl2_version_software",
    "webgl2_vertex_shader",
    "webgl2_vertex_shader_software",
    "webgl_alpha",
    "webgl_alpha_software",
    "webgl_antialias",
    "webgl_antialias_software",
    "webgl_context_type",
    "webgl_context_type_software",
    "webgl_extensions",
    "webgl_extensions_raw",
    "webgl_extensions_raw_software",
    "webgl_extensions_software",
    "webgl_fragment_shader",
    "webgl_fragment_shader_software",
    "webgl_minimal_source",
    "webgl_minimal_source_software",
    "webgl_params",
    "webgl_params_extensions",
    "webgl_params_extensions_EXT_disjoint_timer_query",
    "webgl_params_extensions_EXT_texture_filter_anisotropic",
    "webgl_params_extensions_OVR_multiview2",
    "webgl_params_extensions_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL",
    "webgl_params_extensions_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL",
    "webgl_params_extensions_json",
    "webgl_params_extensions_json_software",
    "webgl_params_extensions_software",
    "webgl_params_extensions_software_EXT_disjoint_timer_query",
    "webgl_params_extensions_software_EXT_texture_filter_anisotropic",
    "webgl_params_extensions_software_OVR_multiview2",
    "webgl_params_extensions_software_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL",
    "webgl_params_extensions_software_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL",
    "webgl_params_json",
    "webgl_params_json_software",
    "webgl_params_software",
    "webgl_precision_fragment",
    "webgl_precision_fragment_software",
    "webgl_precision_vertex",
    "webgl_precision_vertex_software",
    "webgl_renderer",
    "webgl_renderer_raw",
    "webgl_renderer_raw_software",
    "webgl_renderer_software",
    "webgl_vendor",
    "webgl_vendor_raw",
    "webgl_vendor_raw_software",
    "webgl_vendor_software",
    "webgl_version",
    "webgl_version_raw",
    "webgl_version_raw_software",
    "webgl_version_software",
    "webgl_vertex_shader",
    "webgl_vertex_shader_software",
    "wgpu_is_fallback_adapter",
    "combined_wgpu_hash",
    "wgpu_maxbindgroups",
    "wgpu_maxbindgroupsplusvertexbuffers",
    "wgpu_maxbindingsperbindgroup",
    "wgpu_maxbuffersize",
    "wgpu_maxcolorattachmentbytespersample",
    "wgpu_maxcolorattachments",
    "wgpu_maxcomputeinvocationsperworkgroup",
    "wgpu_maxcomputeworkgroupsizex",
    "wgpu_maxcomputeworkgroupsizey",
    "wgpu_maxcomputeworkgroupsizez",
    "wgpu_maxcomputeworkgroupsperdimension",
    "wgpu_maxcomputeworkgroupstoragesize",
    "wgpu_maxdynamicstoragebuffersperpipelinelayout",
    "wgpu_maxdynamicuniformbuffersperpipelinelayout",
    "wgpu_maxinterstageshadervariables",
    "wgpu_maxsampledtexturespershaderstage",
    "wgpu_maxsamplerspershaderstage",
    "wgpu_maxstoragebufferbindingsize",
    "wgpu_maxstoragebufferspershaderstage",
    "wgpu_maxstoragetexturespershaderstage",
    "wgpu_maxtexturearraylayers",
    "wgpu_maxtexturedimension1d",
    "wgpu_maxtexturedimension2d",
    "wgpu_maxtexturedimension3d",
    "wgpu_maxuniformbufferbindingsize",
    "wgpu_maxuniformbufferspershaderstage",
    "wgpu_maxvertexattributes",
    "wgpu_maxvertexbufferarraystride",
    "wgpu_maxvertexbuffers",
    "wgpu_minstoragebufferoffsetalignment",
    "wgpu_minuniformbufferoffsetalignment",
    "wgpu_missing_features",
}
# Attributes added by webGLParamMetricFilter (applied in apply_post_pickle_corrections)
| {f"webgl_params_{p}" for p in WEBGL_PARAM_METRICS}
| {f"webgl_params_{p}_software" for p in WEBGL_PARAM_METRICS}
| {f"webgl2_params_{p}" for p in WEBGL_PARAM_METRICS + WEBGL2_PARAM_METRICS}
| {f"webgl2_params_{p}_software" for p in WEBGL_PARAM_METRICS + WEBGL2_PARAM_METRICS}
)

DEFAULT_SUBSET = set(_DEFAULT_SUBSET_BASE)
_subset_validated = False

def _validate_and_complete_default_subset(dv):
  """Add dynamic math_op_* attrs and validate static definition.
  Idempotent — skips if already run. Called by workers on first data."""
  global DEFAULT_SUBSET, DEBUGPRINT_SUBSET, _subset_validated
  if _subset_validated:
    return
  _subset_validated = True

  # Add dynamic math_op_* attrs from the actual data
  dynamic_attrs = {
    attr for attr in vars(dv)
    if attr.startswith('math_op_') or attr.startswith('math_op_fdlibm_') or attr.startswith('math_op_diag_')
  }
  DEFAULT_SUBSET.update(dynamic_attrs)

  # Build expected set from vars() (the old reflection approach)
  expected = {
    attr for attr in vars(dv)
    if not attr.startswith('__') and attr not in _DEFAULT_IGNORE_SET
  }

  # Assertion: kill the program if static definition doesn't match vars()
  if DEFAULT_SUBSET != expected:
    missing = expected - DEFAULT_SUBSET
    extra = DEFAULT_SUBSET - expected
    msg = "DEFAULT_SUBSET mismatch!\n"
    if missing:
      msg += f"  Missing from static definition: {sorted(missing)}\n"
    if extra:
      msg += f"  Extra in static definition: {sorted(extra)}\n"
    print(msg, file=sys.stderr)
    sys.exit(-1)

  DEBUGPRINT_SUBSET = {
    attr for attr in vars(dv)
    if not attr.startswith('__') and attr not in _DEBUGPRINT_IGNORE_SET
  }

DEBUGPRINT_SUBSET = set()

_NONE_SENTINEL = sys.intern("None")

def value_wrap(v, default_value=_NONE_SENTINEL):
  return v if v is not None else default_value
def value_wrapi(v, default_value=0):
  if v is not None:
    try:
      return int(v)
    except:
      print(f"Could not convert {v} to int. Setting to {default_value}")
      return default_value
  else:
    return default_value
def value_wraps(v, default_value=_NONE_SENTINEL):
  return str(v) if v is not None else default_value

def apply_correction_filters(data_values, n_threads=1):
    """Apply all correction filters to a list of DataValues.
    If n_threads > 1, splits the work across threads (benefits from GIL-free Python 3.14t)."""
    import threading, math

    from experiments import noProcessorCountFilter, noWebGLRendererSanitizing, removeMinorVersionProtection

    def _apply(dvs):
        for d in dvs:
            d.add_filter(CorrectionFilter)
            d.add_filter(CanvasSoftwareFillIn)
            d.add_filter(humanReadableValuesFilter)
            d.add_filter(cpuModelFilter)
            d.add_filter(TimezoneBugFix)
            d.add_filter(DSTNormalizationFilter)
            d.add_filter(webGLParamFilter)
            d.add_filter(webGLParamMetricFilter)
            d.add_filter(webglRendererRawFilter)
            d.add_filter(machineModelFilter)
            # Phase 0 baseline: expose raw values so all analyses
            # (fingerprints, buckets, SMR, ISMR, etc.) use the unprotected surface
            d.add_filter(noProcessorCountFilter)
            d.add_filter(noWebGLRendererSanitizing)
            d.add_filter(removeMinorVersionProtection)

    CanvasSoftwareFillIn.reset_counters()

    if n_threads <= 1 or len(data_values) < 100:
        _apply(data_values)
    else:
        chunk_size = math.ceil(len(data_values) / n_threads)
        chunks = [data_values[i:i+chunk_size] for i in range(0, len(data_values), chunk_size)]
        threads = [threading.Thread(target=_apply, args=(c,)) for c in chunks]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    # Log canvas fill-in stats (counters are not perfectly thread-safe but
    # close enough for reporting — worst case undercounts slightly)
    from filters import _canvas_fill_all_count
    if _canvas_fill_all_count > 0:
        config.log(CanvasSoftwareFillIn.report())


def parse_datavalues(raw_rows, quiet=False, n_filter_threads=1):
    # Convert all loaded data rows to DataValues instances
    skipped_records = 0
    included_records = 0
    data_values = []
    error_output = ""
    expected_errors = defaultdict(int)
    num_users = 0
    num_users_by_os = defaultdict(int)

    start = time.time()
    rows_iter = raw_rows if quiet else tqdm.tqdm(raw_rows, desc="  Scanning records", file=config.terminal)
    for r in rows_iter:
        r = Struct(**r)
        errors = record_has_errors(expected_errors, r)
        if errors:
            if isinstance(errors, str):
                error_output += errors + "\n\n"
            skipped_records += 1
            continue
        included_records += 1
        dv = DataValues(r)
        data_values.append(dv)
        num_users += 1
        num_users_by_os[dv.os] += 1

    parse_elapsed = time.time() - start

    if not quiet:
        print("")
        print("  We skipped", skipped_records, "records from the dataset because they were weird")
        print("  We included", included_records, "records")
        print("  We saw the following expected errors:")
        for k, v in expected_errors.items():
            print(f"\t{k}:", v)
        if error_output.strip():
          print("  We saw the following unexpected errors:")
          for l in error_output.split("\n"):
              print("   ", l)
        print(f"  Parsed {len(data_values):,} rows in {parse_elapsed:.2f}s\n")

        print("  Applying filters…")

    start = time.time()
    apply_correction_filters(data_values, n_threads=n_filter_threads)
    filter_elapsed = time.time() - start

    if not quiet:
        print(f"    Filters done in {filter_elapsed:.2f}s\n")

    stats = {
        'skipped': skipped_records,
        'included': included_records,
        'expected_errors': dict(expected_errors),
        'unexpected_errors': error_output,
        'parse_time': parse_elapsed,
        'filter_time': filter_elapsed,
    }
    return data_values, num_users, num_users_by_os, stats


class DataValues:
  def __init__(self, obj):
    # Any member variable you add that isn't a metric needs to be added to the ignore list
    # for the default subset above.
    self.filters = []

    self.client_id = obj.metrics['uuid']['characteristics_client_identifier']
    self.schema = obj.metrics['quantity']['characteristics_submission_schema']
    self.submission_date = obj.submission_timestamp
    self.channel = obj.normalized_channel

    def find_value(schema, metric_type, metric_name, prop_name, default_value=_NONE_SENTINEL):
      if self.schema >= schema:
        if metric_name in obj.metrics[metric_type]:
          value = obj.metrics[metric_type][metric_name]
        elif "characteristics_" + metric_name in obj.metrics[metric_type]:
          value = obj.metrics[metric_type]["characteristics_" + metric_name]
        elif "characteristics." + metric_name in obj.metrics[metric_type]:
          value = obj.metrics[metric_type]["characteristics." + metric_name]

        else:
          setattr(self, prop_name, default_value)

          print("---------------------------")
          print("Could not find", metric_name)
          print(obj)
          print(obj.metrics)
          return False

        setattr(self, prop_name, value_wrap(value, default_value))
        return True

      setattr(self, prop_name, default_value)
      return False


    self.errors = value_wrap(obj.metrics['text2']['characteristics_errors'])
    self.errors_js = value_wrap(obj.metrics['text2']['characteristics_js_errors'])

    # System
    self.channel = value_wrap(obj.metrics['string']['characteristics_channel'])
    self.build_date = str(value_wrap(obj.metrics['quantity']['characteristics_build_date']))
    self.version = value_wrap(obj.metrics['string']['characteristics_version'])

    self.country = value_wrap(obj.normalized_country_code)
    self.os = value_wrap(obj.metrics['string']['characteristics_os_name'])
    self.os_version = value_wrap(obj.metrics['string']['characteristics_os_version'])
    self.platform = value_wrap(obj.metrics['string']['characteristics_platform'])

    # Language/Locale stuff
    self.intl_keyboard_layout = value_wrap(obj.metrics['string']['characteristics_keyboard_layout'])

    self.locale_accept_language = value_wrap(obj.metrics['string']['characteristics_prefs_intl_accept_languages'])
    self.intl_system_locale = value_wrap(obj.metrics['string']['characteristics_system_locale'])
    self.intl_intl_locale = value_wrap(obj.metrics['string']['characteristics_intl_locale'])
    self.intl_timezone = value_wrap(obj.metrics['string']['characteristics_timezone'])

    try:
      tz = zoneinfo.ZoneInfo(self.intl_timezone)
      now_in_tz = datetime.now(tz)
      offset_timedelta = now_in_tz.utcoffset()
      self.intl_timezoneoffset = offset_timedelta.total_seconds()
    except Exception as e:
      o = backup_timezone(self.intl_timezone)
      if o:
        self.intl_timezoneoffset = float(o)
      else:
        self.intl_timezoneoffset = 0.0

    # schema 32→33: changed type from quantity to string
    if self.schema >= 33:
      find_value(33, 'string', 'timezone_offset_web', 'intl_timezone_offset_web')
    else:
      find_value(32, 'quantity', 'timezone_offset_web', 'intl_timezone_offset_web')
      self.intl_timezone_offset_web = str(self.intl_timezone_offset_web)
    find_value(32, 'string', 'languages', 'locale_languages')
    find_value(32, 'string', 'timezone_web', 'intl_timezone_web')

    # Screen-Related Stuff
    self.screens = []

    screens_raw = value_wrap(obj.metrics['text2']['characteristics_screens'], "")
    if not screens_raw:
      raise Exception("No screens data")
    else:
      try:
        screens = json.loads(screens_raw)
      except:
        print("Failure parsing", screens_raw)
        raise Exception(screens_raw)

      for s in screens:
        screen = {
          "color_depth": value_wrapi(s['colorDepth']),
          "pixel_depth": value_wrap(s['pixelDepth']),
          "orientation_angle": value_wrap(s.get('oAngle')),
          "orientation": value_wrap(s.get('oType')),
          "video_dynamic_range": value_wrap(s['hdr']),
          "scale_factor": value_wrap(s['scaleFactor']),
          "left": value_wrapi(s['rect'][0]),
          "top": value_wrapi(s['rect'][1]),
          "width": value_wrapi(s['rect'][2]),
          "height": value_wrapi(s['rect'][3]),
          "avail_left": value_wrapi(s['availRect'][0]),
          "avail_top": value_wrapi(s['availRect'][1]),
          "avail_width": value_wrapi(s['availRect'][2]),
          "avail_height": value_wrapi(s['availRect'][3]),
        }
        self.screens.append(Struct(**screen))

      self.screen_count = len(self.screens)
      self.screen_primary_color_depth = self.screens[0].color_depth
      self.screen_primary_pixel_depth = self.screens[0].pixel_depth
      self.screen_primary_orientation_angle = self.screens[0].orientation_angle
      self.screen_primary_orientation = self.screens[0].orientation
      self.screen_primary_video_dynamic_range = True if self.screens[0].video_dynamic_range in ['1', 'True'] else False
      try:
        self.screen_primary_scale_factor = float(self.screens[0].scale_factor)
      except:
        self.screen_primary_scale_factor = self.screens[0].scale_factor

      self.screen_primary_posx = self.screens[0].left
      self.screen_primary_posy = self.screens[0].top

      self.screen_primary_resolution = str(self.screens[0].width) + "x" + str(self.screens[0].height)
      self.screen_primary_resolution_width = str(self.screens[0].width)
      self.screen_primary_resolution_height = str(self.screens[0].height)

      self.screen_primary_avail = str(self.screens[0].avail_width) + "x" + str(self.screens[0].avail_height)
      self.screen_primary_avail_width = str(self.screens[0].avail_width)
      self.screen_primary_avail_height = str(self.screens[0].avail_height)
      self.screen_primary_avail_top = str(self.screens[0].avail_top)
      self.screen_primary_avail_left = str(self.screens[0].avail_left)

      self.screen_primary_avail_diff = str(self.screens[0].width - self.screens[0].avail_width) + "x" + str(self.screens[0].height - self.screens[0].avail_height)
      self.screen_primary_avail_width_diff = str(self.screens[0].width - self.screens[0].avail_width)
      self.screen_primary_avail_height_diff = str(self.screens[0].height - self.screens[0].avail_height)


    ## Web-visible metrics for the screen.  These may include zoom information.

    # pixel_ratio changed from quantity (schema <= 21, integer percentage)
    # to string (schema >= 26, decimal ratio like "1.25") around schema 22-25.
    # Our data (schema >= 33) is always in metrics.string.
    if self.schema >= 26:
      self.screen_web_pixel_ratio = value_wrap(obj.metrics['string']['characteristics_pixel_ratio'])
    else:
      self.screen_web_pixel_ratio = value_wraps(obj.metrics['quantity']['characteristics_pixel_ratio'])

    self.screen_web_resolution = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']))
    self.screen_web_resolution_height = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']))
    self.screen_web_resolution_width = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']))

    self.screen_web_avail = str(value_wrapi(obj.metrics['quantity']['characteristics_avail_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_avail_height']))
    self.screen_web_avail_height = str(value_wrapi(obj.metrics['quantity']['characteristics_avail_height']))
    self.screen_web_avail_width = str(value_wrapi(obj.metrics['quantity']['characteristics_avail_width']))
    if self.schema >= 34:
      self.screen_web_avail_top = value_wrapi(obj.metrics['quantity'].get('characteristics_avail_top'))
      self.screen_web_avail_left = value_wrapi(obj.metrics['quantity'].get('characteristics_avail_left'))
    else:
      self.screen_web_avail_top = 0
      self.screen_web_avail_left = 0

    self.screen_web_avail_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']) - value_wrapi(obj.metrics['quantity']['characteristics_avail_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']) - value_wrapi(obj.metrics['quantity']['characteristics_avail_height']))
    self.screen_web_avail_height_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']) - value_wrapi(obj.metrics['quantity']['characteristics_avail_height']))
    self.screen_web_avail_width_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']) - value_wrapi(obj.metrics['quantity']['characteristics_avail_width']))

    # Above and Below 25 we have the web-visible outer and inners
    self.screen_web_inner = str(value_wrapi(obj.metrics['quantity']['characteristics_inner_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_inner_height']))
    self.screen_web_inner_width = str(value_wrapi(obj.metrics['quantity']['characteristics_inner_width']))
    self.screen_web_inner_height = str(value_wrapi(obj.metrics['quantity']['characteristics_inner_height']))

    self.screen_web_inner_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']) - value_wrapi(obj.metrics['quantity']['characteristics_inner_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']) - value_wrapi(obj.metrics['quantity']['characteristics_inner_height']))
    self.screen_web_inner_width_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']) - value_wrapi(obj.metrics['quantity']['characteristics_inner_width']))
    self.screen_web_inner_height_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']) - value_wrapi(obj.metrics['quantity']['characteristics_inner_height']))

    self.screen_web_outer = str(value_wrapi(obj.metrics['quantity']['characteristics_outer_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_outer_height']))
    self.screen_web_outer_width = str(value_wrapi(obj.metrics['quantity']['characteristics_outer_width']))
    self.screen_web_outer_height = str(value_wrapi(obj.metrics['quantity']['characteristics_outer_height']))

    self.screen_web_outer_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']) - value_wrapi(obj.metrics['quantity']['characteristics_outer_width'])) + "x" + str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']) - value_wrapi(obj.metrics['quantity']['characteristics_outer_height']))
    self.screen_web_outer_width_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_width']) - value_wrapi(obj.metrics['quantity']['characteristics_outer_width']))
    self.screen_web_outer_height_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_screen_height']) - value_wrapi(obj.metrics['quantity']['characteristics_outer_height']))

    # outer - inner = browser chrome (toolbars, scrollbars, etc.)
    self.screen_web_outer_inner_width_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_outer_width']) - value_wrapi(obj.metrics['quantity']['characteristics_inner_width']))
    self.screen_web_outer_inner_height_diff = str(value_wrapi(obj.metrics['quantity']['characteristics_outer_height']) - value_wrapi(obj.metrics['quantity']['characteristics_inner_height']))
    self.screen_web_outer_inner_diff = self.screen_web_outer_inner_width_diff + "x" + self.screen_web_outer_inner_height_diff

    self.screen_color_scheme = value_wrap(obj.metrics['quantity']['characteristics_color_scheme'])
    self.screen_prefers_contrast = value_wrap(obj.metrics['quantity']['characteristics_prefers_contrast'])
    self.screen_prefers_reduced_motion = value_wrap(obj.metrics['boolean']['characteristics_prefers_reduced_motion'])
    self.screen_prefers_reduced_transparency = value_wrap(obj.metrics['boolean']['characteristics_prefers_reduced_transparency'])
    self.screen_inverted_colors = value_wrap(obj.metrics['boolean']['characteristics_inverted_colors'])
    self.screen_monochrome = value_wrap(obj.metrics['boolean']['characteristics_monochrome'])

    self.screen_size_mode = value_wrap(obj.metrics['quantity']['characteristics_size_mode'])
    self.screen_text_anti_aliasing = value_wrap(obj.metrics['string']['characteristics_text_anti_aliasing'])


    # Prefs
    self.prefs_zoom_text_only = value_wrap(obj.metrics['boolean']['characteristics_prefs_zoom_text_only'])
    self.prefs_eme_enabled = value_wrap(obj.metrics['boolean']['characteristics_prefs_media_eme_enabled'])
    self.prefs_block_popups = value_wrap(obj.metrics['boolean']['characteristics_prefs_block_popups'])
    self.prefs_general_autoscroll = value_wrap(obj.metrics['boolean']['characteristics_prefs_general_autoscroll'])
    self.prefs_general_smoothscroll = value_wrap(obj.metrics['boolean']['characteristics_prefs_general_smoothscroll'])
    self.prefs_general_overlay_scrollbars = value_wrap(obj.metrics['boolean']['characteristics_prefs_overlay_scrollbars'])
    self.prefs_general_donottrack_enabled = value_wrap(obj.metrics['boolean']['characteristics_prefs_privacy_donottrackheader_enabled'], False)
    self.prefs_general_globalprivacycontrol_enabled = value_wrap(obj.metrics['boolean']['characteristics_prefs_privacy_globalprivacycontrol_enabled'], False)
    self.prefs_use_document_colors = value_wrap(obj.metrics['boolean']['characteristics_use_document_colors'])
    self.prefs_pdf_viewer = value_wrap(obj.metrics['boolean']['characteristics_pdf_viewer'])
    self.prefs_cookiebehavior = value_wrap(obj.metrics['quantity']['characteristics_prefs_network_cookie_cookiebehavior'])
    self.prefs_cookiesenabled = str(self.prefs_cookiebehavior != 2)
    self.prefs_zoom_count = value_wrap(obj.metrics['quantity']['characteristics_zoom_count'])
    self.prefs_changed_media_prefs = value_wrap(obj.metrics['string']['characteristics_changed_media_prefs'])
    find_value(32, 'boolean', 'using_accelerated_canvas', 'using_accelerated_canvas')

    # Hardware Stuff
    if obj.metrics['string_list'] and 'characteristics_gamepads' in obj.metrics['string_list']:
      self.hw_gamepads = ", ".join(obj.metrics['string_list']['characteristics_gamepads']) if obj.metrics['string_list']['characteristics_gamepads'] else ""
    else:
      self.hw_gamepads = ""

    self.hw_camera_count = value_wrap(obj.metrics['quantity']['characteristics_camera_count'])
    self.hw_microphone_count = value_wrap(obj.metrics['quantity']['characteristics_microphone_count'])
    self.hw_speaker_count = value_wrap(obj.metrics['quantity']['characteristics_speaker_count'])
    self.hw_group_count = value_wrap(obj.metrics['quantity']['characteristics_group_count'])
    self.hw_group_count_wo_speakers = value_wrap(obj.metrics['quantity']['characteristics_group_count_wo_speakers'])

    self.ice_order = value_wrap(obj.metrics['quantity']['characteristics_ice_order'])
    self.ice_sd = value_wrap(obj.metrics['quantity']['characteristics_ice_sd'])
    self.media_capabilities_not_efficient = value_wrap(obj.metrics['text2']['characteristics_media_capabilities_not_efficient'])
    self.media_capabilities_not_smooth = value_wrap(obj.metrics['text2']['characteristics_media_capabilities_not_smooth'])
    self.media_capabilities_unsupported = value_wrap(obj.metrics['text2']['characteristics_media_capabilities_unsupported'])
    self.media_h264 = value_wrap(obj.metrics['text2']['characteristics_media_capabilities_h264'])
    self.combined_media_capabilities_hash = _combined_hash(json.dumps(
        [None if v == "None" else v for v in [
            self.media_capabilities_not_efficient,
            self.media_capabilities_not_smooth,
            self.media_capabilities_unsupported,
            self.media_h264]], separators=(',', ':')))

    self.hw_machine_model = value_wrap(obj.metrics['string']['characteristics_machine_model_name'])
    self.hw_processor_count = value_wrapi(obj.metrics['quantity']['characteristics_processor_count'])
    self.hw_cpu_model = value_wrap(obj.metrics['string']['characteristics_cpu_model'])
    self.hw_oscpu = value_wrap(obj.metrics['string']['characteristics_oscpu'])
    find_value(19, 'string', "cpu_arch", "hw_cpu_arch")
    find_value(32, 'string', 'firefox_binary_arch', 'hw_firefox_binary_arch')
    find_value(32, 'string', 'fpu_control_state', 'hw_fpu_control_state')

    self.hw_motion_decimals = value_wrap(obj.metrics['quantity']['characteristics_motion_decimals'])
    self.hw_motion_freq = value_wrap(obj.metrics['quantity']['characteristics_motion_freq'])
    self.hw_orientation_decimals = value_wrap(obj.metrics['quantity']['characteristics_orientation_decimals'])
    self.hw_orientation_freq = value_wrap(obj.metrics['quantity']['characteristics_orientation_freq'])
    self.hw_orientationabs_decimals = value_wrap(obj.metrics['quantity']['characteristics_orientationabs_decimals'])
    self.hw_orientationabs_freq = value_wrap(obj.metrics['quantity']['characteristics_orientationabs_freq'])

    self.hw_max_touch_points = value_wrapi(obj.metrics['quantity']['characteristics_max_touch_points'])
    self.hw_any_pointer_type = value_wrap(obj.metrics['quantity']['characteristics_any_pointer_type'])
    self.hw_pointer_height = value_wrap(obj.metrics['quantity']['characteristics_pointer_height'])
    self.hw_pointer_tiltx = value_wrap(obj.metrics['quantity']['characteristics_pointer_tiltx'])
    self.hw_pointer_tilty = value_wrap(obj.metrics['quantity']['characteristics_pointer_tilty'])
    self.hw_pointer_twist = value_wrap(obj.metrics['quantity']['characteristics_pointer_twist'])
    self.hw_pointer_type = value_wrap(obj.metrics['quantity']['characteristics_pointer_type'])
    self.hw_pointer_width = value_wrap(obj.metrics['quantity']['characteristics_pointer_width'])
    self.hw_pointer_pressure = value_wrap(obj.metrics['string']['characteristics_pointer_pressure'])
    self.hw_pointer_tangentinal_pressure = value_wrap(obj.metrics['string']['characteristics_pointer_tangentinal_pressure'])
    self.hw_touch_rotation_angle = value_wrap(obj.metrics['string']['characteristics_touch_rotation_angle'])

    # Audio Stuff
    self.audio_fingerprint = value_wraps(obj.metrics['quantity']['characteristics_audio_fingerprint'])
    self.audio_channels = value_wrap(obj.metrics['quantity']['characteristics_audio_channels'])
    self.audio_frames = value_wrap(obj.metrics['quantity']['characteristics_audio_frames'])
    self.audio_rate = value_wrap(obj.metrics['quantity']['characteristics_audio_rate'])
    find_value(32, 'quantity', 'audio_unique_samples', 'audio_unique_samples')
    find_value(32, 'string', 'audio_compressor_gain_reduction', 'audio_compressor_gain_reduction')
    find_value(32, 'string', 'audio_fingerprint2', 'audio_fingerprint2')
    find_value(32, 'string', 'audio_float_frequency_sum', 'audio_float_frequency_sum')
    find_value(32, 'string', 'audio_float_time_domain_sum', 'audio_float_time_domain_sum')

    # Video Stuff?
    self.target_frame_rate = value_wrap(obj.metrics['quantity']['characteristics_target_frame_rate'])

    # Voices
    self.voices_count = value_wrap(obj.metrics['quantity']['characteristics_voices_count'])
    self.voices_local_count = value_wrap(obj.metrics['quantity']['characteristics_voices_local_count'])
    self.voices_all_ssdeep = value_wrap(obj.metrics['string']['characteristics_voices_all_ssdeep'])
    self.voices_default = value_wrap(obj.metrics['string']['characteristics_voices_default'])
    self.voices_local_ssdeep = value_wrap(obj.metrics['string']['characteristics_voices_local_ssdeep'])
    self.voices_nonlocal_ssdeep = value_wrap(obj.metrics['string']['characteristics_voices_nonlocal_ssdeep'])
    self.voices_sample = value_wrap(obj.metrics['text2']['characteristics_voices_sample'])
    self.voices_sha1 = value_wrap(obj.metrics['text2']['characteristics_voices_sha1'])

    # Math — math_ops is from populateMathOps() in UserCharacteristicsPageService.sys.mjs
    # Index : Operation
    #   0   : Math.acos(0.123124234234234242)
    #   1   : Math.acosh(1e308)
    #   2   : Math.asin(0.123124234234234242)
    #   3   : Math.asinh(1)
    #   4   : Math.atanh(0.5)
    #   5   : Math.atan(0.5)
    #   6   : Math.sin(-1e300)
    #   7   : Math.sinh(1)
    #   8   : Math.cos(10.000000000123)
    #   9   : Math.cosh(1)
    #  10   : Math.tan(-1e300)
    #  11   : Math.tanh(1)
    #  12   : Math.exp(1)
    #  13   : Math.expm1(1)
    #  14   : Math.log1p(10)
    #  15   : Math.pow(Math.PI, -100)                              — polyfill for acosh
    #  16   : Math.log(1e154 + Math.sqrt(1e154*1e154 - 1))        — polyfill for acosh
    #  17   : Math.log(1 + Math.sqrt(1*1 + 1))                    — polyfill for asinh
    #  18   : Math.log((1+0.5)/(1-0.5)) / 2                       — polyfill for atanh
    #  19   : Math.exp(1) - 1/Math.exp(1)/2                       — polyfill for sinh
    #  20   : (Math.exp(1) + 1/Math.exp(1)) / 2                   — polyfill for cosh
    #  21   : Math.exp(1) - 1                                     — polyfill for expm1
    #  22   : (Math.exp(2) - 1) / (Math.exp(2) + 1)               — polyfill for tanh
    #  23   : Math.log(1 + 10)                                    — polyfill for log1p
    # math_ops_fdlibm is the same operations run inside alwaysUseFdlibm sandbox (Windows only)
    _raw_math_ops = value_wrap(obj.metrics['text2']['characteristics_math_ops'])
    self.math_ops = json.loads(_raw_math_ops)
    self.combined_math_ops_hash = _combined_hash(_raw_math_ops) if _raw_math_ops != "None" else "None"
    for i in range(len(self.math_ops)):
      setattr(self, f"math_op_{i}", self.math_ops[i])

    if self.os == "WINNT":
      _raw_math_ops_fdlibm = value_wrap(obj.metrics['text2']['characteristics_math_ops_fdlibm'], "[]")
      self.math_ops_fdlibm = json.loads(_raw_math_ops_fdlibm)
      self.combined_math_ops_fdlibm_hash = _combined_hash(_raw_math_ops_fdlibm) if _raw_math_ops_fdlibm not in ("None", "[]") else "None"
      for i in range(len(self.math_ops)):
        setattr(self, f"math_op_fdlibm_{i}", self.math_ops_fdlibm[i] if self.math_ops_fdlibm else "None")
    else:
      self.math_ops_fdlibm = []
      self.combined_math_ops_fdlibm_hash = "None"
      for i in range(len(self.math_ops)):
        setattr(self, f"math_op_fdlibm_{i}", "None")

    # math_ops_fdlibm_2 is from populateMathOpsFdlibm2() — diagnostic intermediate values
    # run inside alwaysUseFdlibm sandbox on all platforms
    # Index : Value
    #   0   : Math.PI
    #   1   : Math.E
    #   2   : Math.SQRT2
    #   3   : Math.SQRT1_2
    #   4   : Math.LN2
    #   5   : Math.LN10
    #   6   : Math.LOG2E
    #   7   : Math.LOG10E
    #   8   : Math.pow(Math.PI, -100)                              — same as math_op_15
    #   9   : 1e154                                                — input to op 16
    #  10   : 1e154 * 1e154                                        — v16^2
    #  11   : Math.sqrt(1e154*1e154 - 1)                           — sqrt for op 16
    #  12   : 1e154 + Math.sqrt(1e154*1e154 - 1)                   — arg to Math.log in op 16
    #  13   : Math.sqrt(2)                                         — sqrt for op 17
    #  14   : 1 + Math.sqrt(2)                                     — arg to Math.log in op 17
    #  15   : 1 + 0.5                                              — numerator part of op 18
    #  16   : 1 - 0.5                                              — denominator part of op 18
    #  17   : (1 + 0.5) / (1 - 0.5)                                — arg to Math.log in op 18
    #  18   : Math.exp(1)                                          — e
    #  19   : 1 / Math.exp(1)                                      — 1/e
    #  20   : 1 / Math.exp(1) / 2                                  — 1/(2e), subtracted in op 19
    #  21   : Math.exp(1) - 1/Math.exp(1)/2                        — same as math_op_19
    #  22   : Math.exp(1) + 1/Math.exp(1)                          — numerator of op 20
    #  23   : (Math.exp(1) + 1/Math.exp(1)) / 2                    — same as math_op_20
    #  24   : Math.exp(1) - 1                                      — same as math_op_21
    #  25   : Math.exp(2)                                          — e^2
    #  26   : Math.exp(2) - 1                                      — numerator of op 22
    #  27   : Math.exp(2) + 1                                      — denominator of op 22
    #  28   : (Math.exp(2) - 1) / (Math.exp(2) + 1)                — same as math_op_22
    #  29   : 1 + 10                                               — arg to Math.log in op 23
    #  30   : Math.sqrt(3)
    #  31   : Math.sqrt(5)
    #  32   : Math.pow(2, 0.5)                                     — same as Math.SQRT2
    #  33   : Math.pow(Math.E, 2)                                  — same as Math.exp(2)
    #  34   : Math.log(Math.E)                                     — should be 1.0
    #  35   : Math.log(10)                                         — same as Math.LN10
    find_value(32, 'text2', 'math_ops_fdlibm_2', 'math_ops_fdlibm_2')
    self.combined_math_ops_diag_hash = _combined_hash(self.math_ops_fdlibm_2) if self.math_ops_fdlibm_2 != "None" else "None"
    if self.schema >= 32 and self.math_ops_fdlibm_2 != "None":
      try:
        diag_list = json.loads(self.math_ops_fdlibm_2)
        for i in range(len(diag_list)):
          setattr(self, f"math_op_diag_{i}", diag_list[i])
      except (json.JSONDecodeError, TypeError):
        pass

    # MathML — getBoundingClientRect().width of math elements in usercharacteristics.html
    # mathml_1–10 are "old" metrics: complex formulas with numeric id="1"–"10"
    #   1 : Summation + integral: ∑(p prime) f(p) = ∫(t>1) f(t) dt dπ(t)
    #   2 : Overbrace/underbrace: {a,...,a k a's, b,...,b ℓ b's} — "k+ℓ elements"
    #   3 : Nested 2×2 matrices in a larger matrix pattern
    #   4 : Cauchy determinant formula: det|c₀ c₁ ... cₙ|
    #   5 : Nested subscript: y_(x_2)
    #   6 : Large superscript: x₉₂^31415 + π
    #   7 : Complex nested sub/superscripts: x_(y_b^a)^(z_c^d)
    #   8 : Triple prime: y₃^‴
    #   9 : Stirling's approximation: lim(n→+∞) √(2πn)/n! × (n/e)^n = 1
    #  10 : Determinant expansion: det(A) = Σ(σ∈Sₙ) ε(σ) ∏(i=1..n) a(i,σᵢ)
    self.mathml_1 = value_wrap(obj.metrics['string']['characteristics_mathml1'])
    self.mathml_2 = value_wrap(obj.metrics['string']['characteristics_mathml2'])
    self.mathml_3 = value_wrap(obj.metrics['string']['characteristics_mathml3'])
    self.mathml_4 = value_wrap(obj.metrics['string']['characteristics_mathml4'])
    self.mathml_5 = value_wrap(obj.metrics['string']['characteristics_mathml5'])
    self.mathml_6 = value_wrap(obj.metrics['string']['characteristics_mathml6'])
    self.mathml_7 = value_wrap(obj.metrics['string']['characteristics_mathml7'])
    self.mathml_8 = value_wrap(obj.metrics['string']['characteristics_mathml8'])
    self.mathml_9 = value_wrap(obj.metrics['string']['characteristics_mathml9'])
    self.mathml_10 = value_wrap(obj.metrics['string']['characteristics_mathml10'])
    self.combined_mathml_hash = _combined_hash(json.dumps(
        [None if getattr(self, f'mathml_{i}') == "None" else getattr(self, f'mathml_{i}')
         for i in range(1, 11)], separators=(',', ':')))
    find_value(32, 'string', 'mathml_diag_font_family', 'mathml_diag_font_family')
    find_value(32, 'string', 'mathml_diag_prefs_modified', 'mathml_diag_prefs_modified')
    # mathml_diag_1–19 are "new" diagnostic metrics: id="new-1"–"new-19" element widths
    #   1 : Algebraic baseline: x² + y² = z²
    #   2 : Pixel-based mspace (should be identical everywhere)
    #   3 : Pixel-based mspace (should be identical everywhere)
    #   4 : Em-based mspace at 16px font-size (depends only on font-size)
    #   5 : Em-based mspace at 20px font-size (depends only on font-size)
    #   6 : Fraction — tests fractionRuleThickness and shifts
    #   7 : Fraction with linethickness="0" — tests fractionRuleThickness
    #   8 : Square root (radical) — tests radicalVerticalGap and radicalRuleThickness
    #   9 : Square root (radical) — tests radical parameters
    #  10 : Subscript — tests script shift parameters
    #  11 : Superscript — tests script shift parameters
    #  12 : Subscript + superscript combined — tests script shift parameters
    #  13 : Stretchy parentheses at 100px height — tests MathVariants table
    #  14 : Stretchy parentheses at 200px height — tests MathVariants table
    #  15 : Overbar — tests overbar gap rendering
    #  16 : Underbar — tests underbar gap rendering
    #  17 : Single glyph "x" at 48px — baseline for font variation
    #  18 : Single glyph "+" at 48px — baseline for font variation
    #  19 : Single glyph "∑" at 48px — baseline for font variation
    for i in range(1, _MATHML_DIAG_COUNT + 1):
      setattr(self, f'mathml_diag_{i}', "None")
    if self.schema >= 32:
      raw = obj.metrics['text2'].get('characteristics_mathml_diag_values')
      if raw is not None:
        try:
          for i, v in enumerate(json.loads(raw), 1):
            if i <= _MATHML_DIAG_COUNT:
              setattr(self, f'mathml_diag_{i}', str(v))
        except (json.JSONDecodeError, TypeError):
          pass
    _raw_mathml_diag = obj.metrics['text2'].get('characteristics_mathml_diag_values') if self.schema >= 32 else None
    self.mathml_diag_values = value_wrap(_raw_mathml_diag)
    self.combined_mathml_diag_hash = _combined_hash(_raw_mathml_diag) if _raw_mathml_diag is not None else "None"

    # SVG
    find_value(32, 'string', 'svg_bbox', 'svg_bbox')
    find_value(32, 'string', 'svg_computed_text_length', 'svg_computed_text_length')
    find_value(32, 'string', 'svg_emoji_set', 'svg_emoji_set')
    find_value(32, 'string', 'svg_extent_of_char', 'svg_extent_of_char')
    find_value(32, 'string', 'svg_substring_length', 'svg_substring_length')

    # Canvas
    self.canvas_dpr = value_wrap(obj.metrics['string']['characteristics_canvas_dpr'])
    self.canvas_canvasdata01 = value_wrap(obj.metrics['string']['characteristics_canvasdata1'])
    self.canvas_canvasdata02 = value_wrap(obj.metrics['string']['characteristics_canvasdata2'])
    self.canvas_canvasdata03 = value_wrap(obj.metrics['string']['characteristics_canvasdata3'])
    self.canvas_canvasdata04 = value_wrap(obj.metrics['string']['characteristics_canvasdata4'])
    self.canvas_canvasdata05 = value_wrap(obj.metrics['string']['characteristics_canvasdata5'])
    self.canvas_canvasdata06 = value_wrap(obj.metrics['string']['characteristics_canvasdata6'])
    self.canvas_canvasdata07 = value_wrap(obj.metrics['string']['characteristics_canvasdata7'])
    self.canvas_canvasdata08 = value_wrap(obj.metrics['string']['characteristics_canvasdata8'])
    self.canvas_canvasdata09 = value_wrap(obj.metrics['string']['characteristics_canvasdata9'])
    self.canvas_canvasdata10 = value_wrap(obj.metrics['string']['characteristics_canvasdata10'])
    self.canvas_canvasdata11_webgl = value_wrap(obj.metrics['string']['characteristics_canvasdata11_webgl'])
    self.canvas_canvasdata12_fingerprintjs1 = value_wrap(obj.metrics['string']['characteristics_canvasdata12_fingerprintjs1'])
    self.canvas_canvasdata13_fingerprintjs2 = value_wrap(obj.metrics['string']['characteristics_canvasdata13_fingerprintjs2'])
    self.canvassoftware_canvasdata01 = value_wrap(obj.metrics['string']['characteristics_canvasdata1_software'])
    self.canvassoftware_canvasdata02 = value_wrap(obj.metrics['string']['characteristics_canvasdata2_software'])
    self.canvassoftware_canvasdata03 = value_wrap(obj.metrics['string']['characteristics_canvasdata3_software'])
    self.canvassoftware_canvasdata04 = value_wrap(obj.metrics['string']['characteristics_canvasdata4_software'])
    self.canvassoftware_canvasdata05 = value_wrap(obj.metrics['string']['characteristics_canvasdata5_software'])
    self.canvassoftware_canvasdata06 = value_wrap(obj.metrics['string']['characteristics_canvasdata6_software'])
    self.canvassoftware_canvasdata07 = value_wrap(obj.metrics['string']['characteristics_canvasdata7_software'])
    self.canvassoftware_canvasdata08 = value_wrap(obj.metrics['string']['characteristics_canvasdata8_software'])
    self.canvassoftware_canvasdata09 = value_wrap(obj.metrics['string']['characteristics_canvasdata9_software'])
    self.canvassoftware_canvasdata10 = value_wrap(obj.metrics['string']['characteristics_canvasdata10_software'])
    self.canvassoftware_canvasdata11_webgl = value_wrap(obj.metrics['string']['characteristics_canvasdata11_webgl_software'])
    self.canvassoftware_canvasdata12_fingerprintjs1 = value_wrap(obj.metrics['string']['characteristics_canvasdata12_fingerprintjs1_software'])
    self.canvassoftware_canvasdata13_fingerprintjs2 = value_wrap(obj.metrics['string']['characteristics_canvasdata13_fingerprintjs2_software'])

    _hw = [self.canvas_canvasdata01, self.canvas_canvasdata02, self.canvas_canvasdata03,
           self.canvas_canvasdata04, self.canvas_canvasdata05, self.canvas_canvasdata06,
           self.canvas_canvasdata07, self.canvas_canvasdata08, self.canvas_canvasdata09,
           self.canvas_canvasdata10, self.canvas_canvasdata11_webgl,
           self.canvas_canvasdata12_fingerprintjs1, self.canvas_canvasdata13_fingerprintjs2]
    _sw = [self.canvassoftware_canvasdata01, self.canvassoftware_canvasdata02, self.canvassoftware_canvasdata03,
           self.canvassoftware_canvasdata04, self.canvassoftware_canvasdata05, self.canvassoftware_canvasdata06,
           self.canvassoftware_canvasdata07, self.canvassoftware_canvasdata08, self.canvassoftware_canvasdata09,
           self.canvassoftware_canvasdata10, self.canvassoftware_canvasdata11_webgl,
           self.canvassoftware_canvasdata12_fingerprintjs1, self.canvassoftware_canvasdata13_fingerprintjs2]
    self.combined_canvas_hardware_hash = _combined_hash(json.dumps([None if v == "None" else v for v in _hw], separators=(',', ':')))
    self.combined_canvas_software_hash = _combined_hash(json.dumps([None if v == "None" else v for v in _sw], separators=(',', ':')))

    find_value(32, 'string', 'canvas_feature_status', 'canvas_feature_status')

    # Canvas Raw Data (disabled — raw PNG bytes are large and not used in analysis)
    # for i in range(1, 14):
    #     if i <= 10:
    #         db_name = f'canvasdata{i}_raw'
    #         db_sw_name = f'canvasdata{i}_software_raw'
    #         prop_name = f'canvas_canvasdata{i:02d}_raw'
    #         prop_sw_name = f'canvassoftware_canvasdata{i:02d}_raw'
    #     elif i == 11:
    #         db_name = 'canvasdata11_webgl_raw'
    #         db_sw_name = 'canvasdata11_webgl_software_raw'
    #         prop_name = 'canvas_canvasdata11_webgl_raw'
    #         prop_sw_name = 'canvassoftware_canvasdata11_webgl_raw'
    #     elif i == 12:
    #         db_name = 'canvasdata12_fingerprintjs1_raw'
    #         db_sw_name = 'canvasdata12_fingerprintjs1_software_raw'
    #         prop_name = 'canvas_canvasdata12_fingerprintjs1_raw'
    #         prop_sw_name = 'canvassoftware_canvasdata12_fingerprintjs1_raw'
    #     else:
    #         db_name = 'canvasdata13_fingerprintjs2_raw'
    #         db_sw_name = 'canvasdata13_fingerprintjs2_software_raw'
    #         prop_name = 'canvas_canvasdata13_fingerprintjs2_raw'
    #         prop_sw_name = 'canvassoftware_canvasdata13_fingerprintjs2_raw'
    #     find_value(32, 'text2', db_name, prop_name)
    #     find_value(32, 'text2', db_sw_name, prop_sw_name)

    # ClientRects
    for i in range(1, 13):
        find_value(32, 'string', f'clientrects_element_gbcr_{i:02d}', f'clientrects_element_gbcr_{i:02d}')
        find_value(32, 'string', f'clientrects_element_gcr_{i:02d}', f'clientrects_element_gcr_{i:02d}')
        find_value(32, 'string', f'clientrects_range_gbcr_{i:02d}', f'clientrects_range_gbcr_{i:02d}')
        find_value(32, 'string', f'clientrects_range_gcr_{i:02d}', f'clientrects_range_gcr_{i:02d}')
    for i in range(1, 7):
        find_value(32, 'string', f'clientrects_emoji_{i:02d}', f'clientrects_emoji_{i:02d}')
    find_value(32, 'string', 'clientrects_emoji_font_family', 'clientrects_emoji_font_family')
    find_value(32, 'string', 'clientrects_ghost_dimensions', 'clientrects_ghost_dimensions')
    find_value(32, 'string', 'clientrects_known_dimensions', 'clientrects_known_dimensions')
    find_value(32, 'string', 'clientrects_text_font_family', 'clientrects_text_font_family')

    # Combined clientrects JSON metrics (stored as SHA-256 hash; lookup in config.COMBINED_HASH_LOOKUP)
    if self.schema >= 32:
        self.combined_clientrects_element_gbcr_hash = _combined_hash(json.dumps(
            [None if getattr(self, f'clientrects_element_gbcr_{i:02d}') == "None"
             else getattr(self, f'clientrects_element_gbcr_{i:02d}')
             for i in range(1, 13)], separators=(',', ':')))
        self.combined_clientrects_element_gcr_hash = _combined_hash(json.dumps(
            [None if getattr(self, f'clientrects_element_gcr_{i:02d}') == "None"
             else getattr(self, f'clientrects_element_gcr_{i:02d}')
             for i in range(1, 13)], separators=(',', ':')))
        self.combined_clientrects_range_gbcr_hash = _combined_hash(json.dumps(
            [None if getattr(self, f'clientrects_range_gbcr_{i:02d}') == "None"
             else getattr(self, f'clientrects_range_gbcr_{i:02d}')
             for i in range(1, 13)], separators=(',', ':')))
        self.combined_clientrects_range_gcr_hash = _combined_hash(json.dumps(
            [None if getattr(self, f'clientrects_range_gcr_{i:02d}') == "None"
             else getattr(self, f'clientrects_range_gcr_{i:02d}')
             for i in range(1, 13)], separators=(',', ':')))
        self.combined_clientrects_emoji_hash = _combined_hash(json.dumps(
            [None if getattr(self, f'clientrects_emoji_{i:02d}') == "None"
             else getattr(self, f'clientrects_emoji_{i:02d}')
             for i in range(1, 7)], separators=(',', ':')))
    else:
        self.combined_clientrects_element_gbcr_hash = "None"
        self.combined_clientrects_element_gcr_hash  = "None"
        self.combined_clientrects_range_gbcr_hash   = "None"
        self.combined_clientrects_range_gcr_hash    = "None"
        self.combined_clientrects_emoji_hash        = "None"

    # WebGL
    self.webgl_version = value_wrap(obj.metrics['quantity']['characteristics_gl_version'], None)  # Check
    self.webgl_version_raw = value_wrap(obj.metrics['string']['characteristics_gl_version_raw'], None)  # Check
    self.webgl_renderer = value_wrap(obj.metrics['string']['characteristics_gl_renderer'], None)  # Check
    self.webgl_renderer_raw = value_wrap(obj.metrics['string']['characteristics_gl_renderer_raw'], None)  # Check
    self.webgl_vendor = value_wrap(obj.metrics['string']['characteristics_gl_vendor'], None)  # Check
    self.webgl_vendor_raw = value_wrap(obj.metrics['string']['characteristics_gl_vendor_raw'], None)  # Check
    self.webgl_extensions = value_wrap(obj.metrics['text2']['characteristics_gl_extensions'], None) # Check
    self.webgl_extensions_raw = value_wrap(obj.metrics['text2']['characteristics_gl_extensions_raw'], None) # Check
    self.webgl_fragment_shader = value_wrap(obj.metrics['string']['characteristics_gl_fragment_shader'], None) # Check
    self.webgl_vertex_shader = value_wrap(obj.metrics['string']['characteristics_gl_vertex_shader'], None) # Check
    self.webgl_minimal_source = value_wrap(obj.metrics['text2']['characteristics_gl_minimal_source'], None) # Check
    self.webgl_context_type = value_wrap(obj.metrics['string']['characteristics_gl_context_type'], None) # Check
    self.webgl_antialias = value_wrap(obj.metrics['string'].get('characteristics_gl_antialias'), None)
    self.webgl_alpha = value_wrap(obj.metrics['string'].get('characteristics_gl_alpha'), None)
    self.webgl_params = value_wrap(obj.metrics['text2']['characteristics_gl_params'], None)   # Check
    self.webgl_params_json = json.loads(self.webgl_params) if self.webgl_params else []  # Check
    self.webgl_params_extensions = value_wrap(obj.metrics['text2']['characteristics_gl_params_extensions'], None)  # Check
    self.webgl_params_extensions_json = json.loads(self.webgl_params_extensions) if self.webgl_params_extensions else [None, [None, None], None, None]  # Fixed
    self.webgl_precision_fragment = value_wrap(obj.metrics['text2']['characteristics_gl_precision_fragment'], None)
    self.webgl_precision_vertex = value_wrap(obj.metrics['text2']['characteristics_gl_precision_vertex'], None)

    self.webgl_version_software = value_wrap(obj.metrics['quantity']['characteristics_gl_version_software'], None)  # Check
    self.webgl_version_raw_software = value_wrap(obj.metrics['string']['characteristics_gl_version_raw_software'], None)  # Check
    self.webgl_renderer_software = value_wrap(obj.metrics['string']['characteristics_gl_renderer_software'], None)  # Check
    self.webgl_renderer_raw_software = value_wrap(obj.metrics['string']['characteristics_gl_renderer_raw_software'], None)  # Check
    self.webgl_vendor_software = value_wrap(obj.metrics['string']['characteristics_gl_vendor_software'], None)  # Check
    self.webgl_vendor_raw_software = value_wrap(obj.metrics['string']['characteristics_gl_vendor_raw_software'], None)  # Check
    self.webgl_extensions_software = value_wrap(obj.metrics['text2']['characteristics_gl_extensions_software'], None)
    self.webgl_extensions_raw_software = value_wrap(obj.metrics['text2']['characteristics_gl_extensions_raw_software'], None)
    self.webgl_fragment_shader_software = value_wrap(obj.metrics['string']['characteristics_gl_fragment_shader_software'], None)
    self.webgl_vertex_shader_software = value_wrap(obj.metrics['string']['characteristics_gl_vertex_shader_software'], None)
    self.webgl_minimal_source_software = value_wrap(obj.metrics['text2']['characteristics_gl_minimal_source_software'], None)
    self.webgl_context_type_software = value_wrap(obj.metrics['string']['characteristics_gl_context_type_software'], None)
    self.webgl_antialias_software = value_wrap(obj.metrics['string'].get('characteristics_gl_antialias_software'), None)
    self.webgl_alpha_software = value_wrap(obj.metrics['string'].get('characteristics_gl_alpha_software'), None)
    self.webgl_params_software = value_wrap(obj.metrics['text2']['characteristics_gl_params_software'], None)  # Check
    self.webgl_params_json_software = json.loads(self.webgl_params_software) if self.webgl_params_software else []
    self.webgl_params_extensions_software = value_wrap(obj.metrics['text2']['characteristics_gl_params_extensions_software'], None)  # Check
    self.webgl_params_extensions_json_software = json.loads(self.webgl_params_extensions_software) if self.webgl_params_extensions_software else [None, [None, None], None, None]  # Check
    self.webgl_precision_fragment_software = value_wrap(obj.metrics['text2']['characteristics_gl_precision_fragment_software'], None)
    self.webgl_precision_vertex_software = value_wrap(obj.metrics['text2']['characteristics_gl_precision_vertex_software'], None)

    #self.webgl2_version = value_wrap(obj.metrics['quantity']['characteristics_gl2_version'], None)  # Check
    self.webgl2_version_raw = value_wrap(obj.metrics['string']['characteristics_gl2_version_raw'], None)
    self.webgl2_renderer = value_wrap(obj.metrics['string']['characteristics_gl2_renderer'], None)
    self.webgl2_renderer_raw = value_wrap(obj.metrics['string']['characteristics_gl2_renderer_raw'], None)
    self.webgl2_vendor = value_wrap(obj.metrics['string']['characteristics_gl2_vendor'], None)
    self.webgl2_vendor_raw = value_wrap(obj.metrics['string']['characteristics_gl2_vendor_raw'], None)
    self.webgl2_extensions = value_wrap(obj.metrics['text2']['characteristics_gl2_extensions'], None)
    self.webgl2_extensions_raw = value_wrap(obj.metrics['text2']['characteristics_gl2_extensions_raw'], None)
    self.webgl2_fragment_shader = value_wrap(obj.metrics['string']['characteristics_gl2_fragment_shader'], None)
    self.webgl2_vertex_shader = value_wrap(obj.metrics['string']['characteristics_gl2_vertex_shader'], None)
    self.webgl2_minimal_source = value_wrap(obj.metrics['text2']['characteristics_gl2_minimal_source'], None)
    self.webgl2_context_type = value_wrap(obj.metrics['string']['characteristics_gl2_context_type'], None)
    self.webgl2_antialias = value_wrap(obj.metrics['string'].get('characteristics_gl2_antialias'), None)
    self.webgl2_alpha = value_wrap(obj.metrics['string'].get('characteristics_gl2_alpha'), None)
    self.webgl2_params = value_wrap(obj.metrics['text2']['characteristics_gl2_params'], None)  # Check
    self.webgl2_params_json = json.loads(self.webgl2_params) if self.webgl2_params else []  # Check
    self.webgl2_params_extensions = value_wrap(obj.metrics['text2']['characteristics_gl2_params_extensions'], None)
    self.webgl2_params_extensions_json = json.loads(self.webgl2_params_extensions) if self.webgl2_params_extensions else [None, [None, None], None, None]  # Check
    self.webgl2_precision_fragment = value_wrap(obj.metrics['text2']['characteristics_gl2_precision_fragment'], None)
    self.webgl2_precision_vertex = value_wrap(obj.metrics['text2']['characteristics_gl2_precision_vertex'], None)

    self.webgl2_version_software = value_wrap(obj.metrics['quantity']['characteristics_gl2_version_software'], None)
    self.webgl2_version_raw_software = value_wrap(obj.metrics['string']['characteristics_gl2_version_raw_software'], None)
    self.webgl2_renderer_software = value_wrap(obj.metrics['string']['characteristics_gl2_renderer_software'], None)
    self.webgl2_renderer_raw_software = value_wrap(obj.metrics['string']['characteristics_gl2_renderer_raw_software'], None)
    self.webgl2_vendor_software = value_wrap(obj.metrics['string']['characteristics_gl2_vendor_software'], None)
    self.webgl2_vendor_raw_software = value_wrap(obj.metrics['string']['characteristics_gl2_vendor_raw_software'], None)
    self.webgl2_extensions_software = value_wrap(obj.metrics['text2']['characteristics_gl2_extensions_software'], None)
    self.webgl2_extensions_raw_software = value_wrap(obj.metrics['text2']['characteristics_gl2_extensions_raw_software'], None)
    self.webgl2_fragment_shader_software = value_wrap(obj.metrics['string']['characteristics_gl2_fragment_shader_software'], None)
    self.webgl2_vertex_shader_software = value_wrap(obj.metrics['string']['characteristics_gl2_vertex_shader_software'], None)
    self.webgl2_minimal_source_software = value_wrap(obj.metrics['text2']['characteristics_gl2_minimal_source_software'], None)
    self.webgl2_context_type_software = value_wrap(obj.metrics['string']['characteristics_gl2_context_type_software'], None)
    self.webgl2_antialias_software = value_wrap(obj.metrics['string'].get('characteristics_gl2_antialias_software'), None)
    self.webgl2_alpha_software = value_wrap(obj.metrics['string'].get('characteristics_gl2_alpha_software'), None)
    self.webgl2_params_software = value_wrap(obj.metrics['text2']['characteristics_gl2_params_software'], None)  # Check
    self.webgl2_params_json_software = json.loads(self.webgl2_params_software) if self.webgl2_params_software else []  # Check
    self.webgl2_params_extensions_software = value_wrap(obj.metrics['text2']['characteristics_gl2_params_extensions_software'], None)
    self.webgl2_params_extensions_json_software = json.loads(self.webgl2_params_extensions_software) if self.webgl2_params_extensions_software else [None, [None, None], None, None]  # Check
    self.webgl2_precision_fragment_software = value_wrap(obj.metrics['text2']['characteristics_gl2_precision_fragment_software'], None)
    self.webgl2_precision_vertex_software = value_wrap(obj.metrics['text2']['characteristics_gl2_precision_vertex_software'], None)

    self.combined_webgl1_params_hash      = _combined_hash(self.webgl_params) if self.webgl_params else "None"
    self.combined_webgl1_params_sw_hash   = _combined_hash(self.webgl_params_software) if self.webgl_params_software else "None"
    self.combined_webgl2_params_hash      = _combined_hash(self.webgl2_params) if self.webgl2_params else "None"
    self.combined_webgl2_params_sw_hash   = _combined_hash(self.webgl2_params_software) if self.webgl2_params_software else "None"
    self.combined_webgl_extensions_hash   = _combined_hash(self.webgl_params_extensions) if self.webgl_params_extensions else "None"
    self.combined_webgl_extensions_sw_hash  = _combined_hash(self.webgl_params_extensions_software) if self.webgl_params_extensions_software else "None"
    self.combined_webgl2_extensions_hash    = _combined_hash(self.webgl2_params_extensions) if self.webgl2_params_extensions else "None"
    self.combined_webgl2_extensions_sw_hash = _combined_hash(self.webgl2_params_extensions_software) if self.webgl2_params_extensions_software else "None"

    # webgl_params_extensions ----------------------------------------------------------------------------------------------
    self.webgl_params_extensions_EXT_texture_filter_anisotropic = str(self.webgl_params_extensions_json[0])
    self.webgl_params_extensions_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL = \
      self.webgl_params_extensions_json[1][0] if self.webgl_params_extensions_json[1] and len(self.webgl_params_extensions_json[1]) == 2 else self.webgl_params_extensions_json[1]
    self.webgl_params_extensions_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL = \
      self.webgl_params_extensions_json[1][1] if self.webgl_params_extensions_json[1] and len(self.webgl_params_extensions_json[1]) == 2 else self.webgl_params_extensions_json[1]
    self.webgl_params_extensions_EXT_disjoint_timer_query = self.webgl_params_extensions_json[2]
    self.webgl_params_extensions_OVR_multiview2 = str(self.webgl_params_extensions_json[3])

    self.webgl_params_extensions_software_EXT_texture_filter_anisotropic = str(self.webgl_params_extensions_json_software[0])
    self.webgl_params_extensions_software_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL = \
      self.webgl_params_extensions_json_software[1][0] if self.webgl_params_extensions_json_software[1] and len(self.webgl_params_extensions_json_software[1]) == 2 else self.webgl_params_extensions_json_software[1]
    self.webgl_params_extensions_software_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL = \
      self.webgl_params_extensions_json_software[1][1] if self.webgl_params_extensions_json_software[1] and len(self.webgl_params_extensions_json_software[1]) == 2 else self.webgl_params_extensions_json_software[1]
    self.webgl_params_extensions_software_EXT_disjoint_timer_query = self.webgl_params_extensions_json_software[2]
    self.webgl_params_extensions_software_OVR_multiview2 = str(self.webgl_params_extensions_json_software[3])

    self.webgl2_params_extensions_EXT_texture_filter_anisotropic = str(self.webgl2_params_extensions_json[0])
    self.webgl2_params_extensions_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL = self.webgl2_params_extensions_json[1][0] if self.webgl2_params_extensions_json[1] and len(self.webgl2_params_extensions_json[1]) == 2 else self.webgl2_params_extensions_json[1]
    self.webgl2_params_extensions_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL = self.webgl2_params_extensions_json[1][1] if self.webgl2_params_extensions_json[1] and len(self.webgl2_params_extensions_json[1]) == 2 else self.webgl2_params_extensions_json[1]
    self.webgl2_params_extensions_EXT_disjoint_timer_query = self.webgl2_params_extensions_json[2]
    self.webgl2_params_extensions_OVR_multiview2 = str(self.webgl2_params_extensions_json[3])

    self.webgl2_params_extensions_software_EXT_texture_filter_anisotropic = str(self.webgl2_params_extensions_json_software[0])
    self.webgl2_params_extensions_software_WEBGL_draw_buffers_MAX_COLOR_ATTACHMENTS_WEBGL = self.webgl2_params_extensions_json_software[1][0] if self.webgl2_params_extensions_json_software[1] and len(self.webgl2_params_extensions_json_software[1]) == 2 else self.webgl2_params_extensions_json_software[1]
    self.webgl2_params_extensions_software_WEBGL_draw_buffers_MAX_DRAW_BUFFERS_WEBGL = self.webgl2_params_extensions_json_software[1][1] if self.webgl2_params_extensions_json_software[1] and len(self.webgl2_params_extensions_json_software[1]) == 2 else self.webgl2_params_extensions_json_software[1]
    self.webgl2_params_extensions_software_EXT_disjoint_timer_query = self.webgl2_params_extensions_json_software[2]
    self.webgl2_params_extensions_software_OVR_multiview2 = str(self.webgl2_params_extensions_json_software[3])

    # webgl_extensions and webgl2_extensions ----------------------------------------------------------------------------------------------
    webgl_extensions = set(self.webgl_extensions.split()) if self.webgl_extensions else set()
    log_unknown_extensions(webgl_extensions - KNOWN_WEBGL_EXTENSIONS, "webgl_extensions")
    webgl_extensions_software = set(self.webgl_extensions_software.split()) if self.webgl_extensions_software else set()
    log_unknown_extensions(webgl_extensions_software - KNOWN_WEBGL_EXTENSIONS, "webgl_extensions_software")
    webgl2_extensions = set(self.webgl2_extensions.split()) if self.webgl2_extensions else set()
    log_unknown_extensions(webgl2_extensions - KNOWN_WEBGL_EXTENSIONS, "webgl2_extensions")
    webgl2_extensions_software = set(self.webgl2_extensions_software.split()) if self.webgl2_extensions_software else set()
    log_unknown_extensions(webgl2_extensions_software - KNOWN_WEBGL_EXTENSIONS, "webgl2_extensions_software")

    """
    for ext in KNOWN_WEBGL_EXTENSIONS:
      if ext in webgl_extensions:
        setattr(self, "webgl_extensions_" + ext, "1")
      else:
        setattr(self, "webgl_extensions_" + ext, "0")
      if ext in webgl_extensions_software:
        setattr(self, "webgl_extensions_software_" + ext, "1")
      else:
        setattr(self, "webgl_extensions_software_" + ext, "0")

      if ext in webgl2_extensions:
        setattr(self, "webgl2_extensions_" + ext, "1")
      else:
        setattr(self, "webgl2_extensions_" + ext, "0")
      if ext in webgl2_extensions_software:
        setattr(self, "webgl2_extensions_software_" + ext, "1")
      else:
        setattr(self, "webgl2_extensions_software_" + ext, "0")
    """

    # webgl_extensions_raw and webgl2_extensions_raw ----------------------------------------------------------------------------------------------
    webgl_extensions_raw = set(self.webgl_extensions_raw.split()) if self.webgl_extensions_raw else set()
    log_unknown_extensions(webgl_extensions_raw - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl_extensions_raw")
    webgl_extensions_raw_software = set(self.webgl_extensions_raw_software.split()) if self.webgl_extensions_raw_software else set()
    log_unknown_extensions(webgl_extensions_raw_software - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl_extensions_raw_software")
    webgl2_extensions_raw = set(self.webgl2_extensions_raw.split()) if self.webgl2_extensions_raw else set()
    log_unknown_extensions(webgl2_extensions_raw - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl2_extensions_raw")
    webgl2_extensions_raw_software = set(self.webgl2_extensions_raw_software.split()) if self.webgl2_extensions_raw_software else set()
    log_unknown_extensions(webgl2_extensions_raw_software - KNOWN_WEBGL_EXTENSIONS_RAW, "webgl2_extensions_raw_software")

    """
    for ext in KNOWN_WEBGL_EXTENSIONS_RAW:
      if ext in webgl_extensions_raw:
        setattr(self, "webgl_extensions_raw_" + ext, "1")
      else:
        setattr(self, "webgl_extensions_raw_" + ext, "0")
      if ext in webgl_extensions_raw_software:
        setattr(self, "webgl_extensions_raw_software_" + ext, "1")
      else:
        setattr(self, "webgl_extensions_raw_software_" + ext, "0")

      if ext in webgl2_extensions_raw:
        setattr(self, "webgl2_extensions_raw_" + ext, "1")
      else:
        setattr(self, "webgl2_extensions_raw_" + ext, "0")
      if ext in webgl2_extensions_raw_software:
        setattr(self, "webgl2_extensions_raw_software_" + ext, "1")
      else:
        setattr(self, "webgl2_extensions_raw_software_" + ext, "0")

    # webgl_params_json ----------------------------------------------------------------------------------------------
    for i, param in enumerate(WEBGL_PARAM_METRICS):
      if self.webgl_params_json:
        setattr(self, "webgl_params_" + param, str(self.webgl_params_json[i]))
      else:
        setattr(self, "webgl_params_" + param, "")

      if self.webgl_params_json_software:
        setattr(self, "webgl_params_" + param + "_software", str(self.webgl_params_json_software[i]))
      else:
        setattr(self, "webgl_params_" + param + "_software", "")

    for i, param in enumerate(WEBGL_PARAM_METRICS + WEBGL2_PARAM_METRICS):
      if self.webgl2_params_json:
        setattr(self, "webgl2_params_" + param, str(self.webgl2_params_json[i]))
      else:
        setattr(self, "webgl2_params_" + param, "")

      if self.webgl2_params_json_software:
        setattr(self, "webgl2_params_" + param + "_software", str(self.webgl2_params_json_software[i]))
      else:
        setattr(self, "webgl2_params_" + param + "_software", "")
    """

    if False:
      del self.webgl_params
      del self.webgl2_params

      del self.webgl_params_software
      del self.webgl2_params_software

      del self.webgl_params_extensions
      del self.webgl2_params_extensions

      del self.webgl_params_extensions_software
      del self.webgl2_params_extensions_software

      del self.webgl_params_json
      del self.webgl_params_json_software

      del self.webgl2_params_json
      del self.webgl2_params_json_software

      del self.webgl_params_extensions_json
      del self.webgl_params_extensions_json_software

      del self.webgl2_params_extensions_json
      del self.webgl2_params_extensions_json_software

      del self.webgl_extensions
      del self.webgl_extensions_raw
      del self.webgl2_extensions
      del self.webgl2_extensions_raw

      del self.webgl_extensions_software
      del self.webgl_extensions_raw_software
      del self.webgl2_extensions_software
      del self.webgl2_extensions_raw_software


    # WebGPU
    self.wgpu_missing_features = value_wrap(obj.metrics['string']['characteristics_wgpu_missing_features'])
    self.wgpu_maxtexturedimension1d = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxtexturedimension1d'])
    self.wgpu_maxtexturedimension2d = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxtexturedimension2d'])
    self.wgpu_maxtexturedimension3d = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxtexturedimension3d'])
    self.wgpu_maxtexturearraylayers = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxtexturearraylayers'])
    self.wgpu_maxbindgroups = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxbindgroups'])
    self.wgpu_maxbindgroupsplusvertexbuffers = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxbindgroupsplusvertexbuffers'])
    self.wgpu_maxbindingsperbindgroup = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxbindingsperbindgroup'])
    self.wgpu_maxdynamicuniformbuffersperpipelinelayout = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxdynamicuniformbuffersperpipelinelayout'])
    self.wgpu_maxdynamicstoragebuffersperpipelinelayout = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxdynamicstoragebuffersperpipelinelayout'])
    self.wgpu_maxsampledtexturespershaderstage = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxsampledtexturespershaderstage'])
    self.wgpu_maxsamplerspershaderstage = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxsamplerspershaderstage'])
    self.wgpu_maxstoragebufferspershaderstage = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxstoragebufferspershaderstage'])
    self.wgpu_maxstoragetexturespershaderstage = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxstoragetexturespershaderstage'])
    self.wgpu_maxuniformbufferspershaderstage = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxuniformbufferspershaderstage'])
    self.wgpu_maxuniformbufferbindingsize = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxuniformbufferbindingsize'])
    self.wgpu_maxstoragebufferbindingsize = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxstoragebufferbindingsize'])
    self.wgpu_minuniformbufferoffsetalignment = value_wrap(obj.metrics['quantity']['characteristics_wgpu_minuniformbufferoffsetalignment'])
    self.wgpu_minstoragebufferoffsetalignment = value_wrap(obj.metrics['quantity']['characteristics_wgpu_minstoragebufferoffsetalignment'])
    self.wgpu_maxvertexbuffers = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxvertexbuffers'])
    self.wgpu_maxbuffersize = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxbuffersize'])
    self.wgpu_maxvertexattributes = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxvertexattributes'])
    self.wgpu_maxvertexbufferarraystride = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxvertexbufferarraystride'])
    self.wgpu_maxinterstageshadervariables = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxinterstageshadervariables'])
    self.wgpu_maxcolorattachments = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcolorattachments'])
    self.wgpu_maxcolorattachmentbytespersample = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcolorattachmentbytespersample'])
    self.wgpu_maxcomputeworkgroupstoragesize = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcomputeworkgroupstoragesize'])
    self.wgpu_maxcomputeinvocationsperworkgroup = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcomputeinvocationsperworkgroup'])
    self.wgpu_maxcomputeworkgroupsizex = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcomputeworkgroupsizex'])
    self.wgpu_maxcomputeworkgroupsizey = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcomputeworkgroupsizey'])
    self.wgpu_maxcomputeworkgroupsizez = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcomputeworkgroupsizez'])
    self.wgpu_maxcomputeworkgroupsperdimension = value_wrap(obj.metrics['quantity']['characteristics_wgpu_maxcomputeworkgroupsperdimension'])
    find_value(32, 'boolean', 'wgpu_is_fallback_adapter', 'wgpu_is_fallback_adapter')
    _wgpu_limits = [
        self.wgpu_maxtexturedimension1d, self.wgpu_maxtexturedimension2d,
        self.wgpu_maxtexturedimension3d, self.wgpu_maxtexturearraylayers,
        self.wgpu_maxbindgroups, self.wgpu_maxbindgroupsplusvertexbuffers,
        self.wgpu_maxbindingsperbindgroup,
        self.wgpu_maxdynamicuniformbuffersperpipelinelayout,
        self.wgpu_maxdynamicstoragebuffersperpipelinelayout,
        self.wgpu_maxsampledtexturespershaderstage, self.wgpu_maxsamplerspershaderstage,
        self.wgpu_maxstoragebufferspershaderstage, self.wgpu_maxstoragetexturespershaderstage,
        self.wgpu_maxuniformbufferspershaderstage,
        self.wgpu_maxuniformbufferbindingsize, self.wgpu_maxstoragebufferbindingsize,
        self.wgpu_minuniformbufferoffsetalignment, self.wgpu_minstoragebufferoffsetalignment,
        self.wgpu_maxvertexbuffers, self.wgpu_maxbuffersize,
        self.wgpu_maxvertexattributes, self.wgpu_maxvertexbufferarraystride,
        self.wgpu_maxinterstageshadervariables,
        self.wgpu_maxcolorattachments, self.wgpu_maxcolorattachmentbytespersample,
        self.wgpu_maxcomputeworkgroupstoragesize, self.wgpu_maxcomputeinvocationsperworkgroup,
        self.wgpu_maxcomputeworkgroupsizex, self.wgpu_maxcomputeworkgroupsizey,
        self.wgpu_maxcomputeworkgroupsizez, self.wgpu_maxcomputeworkgroupsperdimension,
    ]
    self.combined_wgpu_hash = _combined_hash(json.dumps([None if v == "None" else v for v in _wgpu_limits], separators=(',', ':')))
    find_value(32, 'quantity', 'storage_quota', 'storage_quota')


    # Fonts
    def hexify(val):
      return format(val & 0xFFFFFF, '06X')

    self.font_font_name_list_emoji_modified = value_wrap(obj.metrics['boolean']['characteristics_font_name_list_emoji_modified'])
    self.font_prefcolor_accentcolor = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_accentcolor']))
    self.font_prefcolor_accentcolortext = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_accentcolortext']))
    self.font_prefcolor_canvas = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_canvas']))
    self.font_prefcolor_canvastext = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_canvastext']))
    self.font_prefcolor_highlight = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_highlight']))
    self.font_prefcolor_highlighttext = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_highlighttext']))
    self.font_prefcolor_selecteditem = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_selecteditem']))
    self.font_prefcolor_selecteditemtext = hexify(value_wrap(obj.metrics['quantity']['characteristics_color_selecteditemtext']))
    self.font_prefmodified_default = value_wrap(obj.metrics['quantity']['characteristics_font_default_modified'])
    self.font_prefmodified_minimum_size = value_wrap(obj.metrics['quantity']['characteristics_font_minimum_size_modified'])
    self.font_prefmodified_name_list_cursive = value_wrap(obj.metrics['quantity']['characteristics_font_name_list_cursive_modified'])
    self.font_prefmodified_name_list_monospace = value_wrap(obj.metrics['quantity']['characteristics_font_name_list_monospace_modified'])
    self.font_prefmodified_name_list_sans_serif = value_wrap(obj.metrics['quantity']['characteristics_font_name_list_sans_serif_modified'])
    self.font_prefmodified_name_list_serif = value_wrap(obj.metrics['quantity']['characteristics_font_name_list_serif_modified'])
    self.font_prefmodified_name_monospace = value_wrap(obj.metrics['quantity']['characteristics_font_name_monospace_modified'])
    self.font_prefmodified_name_sans_serif = value_wrap(obj.metrics['quantity']['characteristics_font_name_sans_serif_modified'])
    self.font_prefmodified_name_serif = value_wrap(obj.metrics['quantity']['characteristics_font_name_serif_modified'])
    self.font_prefmodified_size_monospace = value_wrap(obj.metrics['quantity']['characteristics_font_size_monospace_modified'])
    self.font_prefmodified_size_variable = value_wrap(obj.metrics['quantity']['characteristics_font_size_variable_modified'])
    self.font_prefs_browser_display_use_document_fonts = value_wrap(obj.metrics['boolean']['characteristics_prefs_browser_display_use_document_fonts'])
    self.font_default_default_group = value_wrap(obj.metrics['string']['characteristics_font_default_default_group'])
    self.font_default_western = value_wrap(obj.metrics['string']['characteristics_font_default_western'])
    self.font_minimum_size_default_group = value_wrap(obj.metrics['string']['characteristics_font_minimum_size_default_group'])
    self.font_minimum_size_western = value_wrap(obj.metrics['string']['characteristics_font_minimum_size_western'])
    self.font_name_monospace_default_group = value_wrap(obj.metrics['string']['characteristics_font_name_monospace_default_group'])
    self.font_name_monospace_western = value_wrap(obj.metrics['string']['characteristics_font_name_monospace_western'])
    self.font_name_sans_serif_default_group = value_wrap(obj.metrics['string']['characteristics_font_name_sans_serif_default_group'])
    self.font_name_sans_serif_western = value_wrap(obj.metrics['string']['characteristics_font_name_sans_serif_western'])
    self.font_name_serif_default_group = value_wrap(obj.metrics['string']['characteristics_font_name_serif_default_group'])
    self.font_name_serif_western = value_wrap(obj.metrics['string']['characteristics_font_name_serif_western'])
    self.font_size_monospace_default_group = value_wrap(obj.metrics['string']['characteristics_font_size_monospace_default_group'])
    self.font_size_monospace_western = value_wrap(obj.metrics['string']['characteristics_font_size_monospace_western'])
    self.font_size_variable_default_group = value_wrap(obj.metrics['string']['characteristics_font_size_variable_default_group'])
    self.font_size_variable_western = value_wrap(obj.metrics['string']['characteristics_font_size_variable_western'])

    # Font Fingerprinting
    self.fonts_fpjs_allowlisted = value_wrap(obj.metrics['string']['characteristics_fonts_fpjs_allowlisted'])
    self.fonts_fpjs_nonallowlisted = value_wrap(obj.metrics['string']['characteristics_fonts_fpjs_nonallowlisted'])
    self.fonts_variant_a_allowlisted = value_wrap(obj.metrics['string']['characteristics_fonts_variant_a_allowlisted'])
    self.fonts_variant_a_nonallowlisted = value_wrap(obj.metrics['string']['characteristics_fonts_variant_a_nonallowlisted'])
    self.fonts_variant_b_allowlisted = value_wrap(obj.metrics['string']['characteristics_fonts_variant_b_allowlisted'])
    self.fonts_variant_b_nonallowlisted = value_wrap(obj.metrics['string']['characteristics_fonts_variant_b_nonallowlisted'])
    for v in ['c', 'd', 'e', 'f', 'g', 'h', 'i']:
        find_value(32, 'string', f'fonts_variant_{v}_allowlisted', f'fonts_variant_{v}_allowlisted')
        find_value(32, 'string', f'fonts_variant_{v}_nonallowlisted', f'fonts_variant_{v}_nonallowlisted')
    _fv_allow = [getattr(self, f'fonts_variant_{v}_allowlisted')
                 for v in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']]
    _fv_nonallow = [getattr(self, f'fonts_variant_{v}_nonallowlisted')
                    for v in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']]
    self.combined_fonts_variants_allowlisted_hash = _combined_hash(json.dumps(
        [None if v == "None" else v for v in _fv_allow], separators=(',', ':')))
    self.combined_fonts_variants_nonallowlisted_hash = _combined_hash(json.dumps(
        [None if v == "None" else v for v in _fv_nonallow], separators=(',', ':')))

    # make sure to sort the array afterwards so two arrays with identical values will be identical
    self.missing_fonts = []
    for font in obj.metrics['text2']['characteristics_missing_fonts'].split("|"):
      self.missing_fonts.append(font.lower())
    self.missing_fonts = sorted(self.missing_fonts)

    # Build navigator.userAgent
    # See nsHttpHandler::BuildUserAgent()
    if not find_value(18, 'text2', 'user_agent', 'user_agent'):
      self.user_agent = f"Mozilla/5.0 ({self.os}; {self.hw_oscpu}; rv:{self.version}) Gecko/20100101 Firefox/{self.version}"

    find_value(32, 'string', 'os_distro', 'os_distro')
    find_value(32, 'string', 'os_distro_id', 'os_distro_id')
    find_value(32, 'string', 'os_distro_version', 'os_distro_version')

    # CSS system colors — raw JSON (for fingerprinters) + individual attr per color name
    self.font_css_system_colors = "None"
    for _name in _CSS_COLOR_NAMES:
      setattr(self, 'css_color_' + _name.lower(), "None")
    if self.schema >= 32:
      _raw = obj.metrics['text2'].get('characteristics_css_system_colors')
      if _raw is not None:
        self.font_css_system_colors = _raw
        try:
          for _entry in json.loads(_raw):
            for _k, _v in _entry.items():
              setattr(self, 'css_color_' + _k.lower(), _v)
        except (json.JSONDecodeError, TypeError, AttributeError):
          pass
    self.combined_css_colors_hash = _combined_hash(self.font_css_system_colors) if self.font_css_system_colors != "None" else "None"

    # CSS system fonts — raw JSON (for fingerprinters) + individual attr per font keyword
    self.font_css_system_fonts = "None"
    for _attr_suffix in _CSS_FONT_ATTR_SUFFIXES.values():
      setattr(self, 'css_font_' + _attr_suffix, "None")
    if self.schema >= 32:
      _raw = obj.metrics['text2'].get('characteristics_css_system_fonts')
      if _raw is not None:
        self.font_css_system_fonts = _raw
        try:
          for _entry in json.loads(_raw):
            for _k, _v in _entry.items():
              if _k in _CSS_FONT_ATTR_SUFFIXES:
                setattr(self, 'css_font_' + _CSS_FONT_ATTR_SUFFIXES[_k], _v)
        except (json.JSONDecodeError, TypeError, AttributeError):
          pass
    self.combined_css_fonts_hash = _combined_hash(self.font_css_system_fonts) if self.font_css_system_fonts != "None" else "None"

    # SDP, WebAuthn
    find_value(32, 'text2', 'sdp_codec_list', 'sdp_codec_list')
    find_value(32, 'text2', 'webauthn_capabilities', 'webauthn_capabilities')


  # ----------------------------------------------------------------------------
  def add_filter(self, FilterClass):
    for f in self.filters:
      # We need to compare by strings because as we modify classes during development
      # a strict type comparison no longer works.
      if str(type(f)) == str(FilterClass):
        raise AssertionError(f"Tried to apply {FilterClass} but it is already applied: {self.list_filters()}")

    filter = FilterClass(self)
    self.filters.append(filter)
    return filter.had_an_effect()

  def pop_filter(self):
    assert len(self.filters) > 0, "Tried to pop a filter, but we have no filters"
    filter = self.filters.pop()
    filter.revert(self)

  def list_filters(self):
    return ", ".join(str(type(f)) for f in self.filters)

  # ----------------------------------------------------------------------------
  def fingerprint(self, subset = [], algorithm = SHA1Fingerprint, verbose = False):
    global DEFAULT_SUBSET

    fingerprinter = algorithm()

    # Validate and complete the static DEFAULT_SUBSET on first use
    if not _subset_validated:
      _validate_and_complete_default_subset(self)

    if not subset:
      subset = DEFAULT_SUBSET
    else:
      subset = set(subset)

    included_attributes = set()
    for attr_name in vars(self).keys():
      if attr_name in subset:
        included_attributes.add(attr_name)

        if verbose:
          print(attr_name, str(getattr(self, attr_name)).encode('utf-8'))

    for attr_name in sorted(included_attributes):
      fingerprinter.update(getattr(self, attr_name))

    if len(included_attributes) != len(subset):
      raise Exception(f"Called DataValues.fingerprint() but could not find these attributes: {subset - included_attributes}")

    # Return raw bytes for SHA1Fingerprint (20 bytes vs 40-char hex string,
    # halving memory usage in fingerprint hash dicts).
    if algorithm is SHA1Fingerprint:
        return fingerprinter.digest()
    return fingerprinter.hexdigest()

  # ----------------------------------------------------------------------------
  def debugprint(self, indent="", subset=[]):
    global DEBUGPRINT_SUBSET
    if not DEBUGPRINT_SUBSET:
      _validate_and_complete_default_subset(self)


    def _print_vars(indent, obj, attr_allowlist=[]):
      for attr_name, attr_value in vars(obj).items():
        if type(attr_value) == dict:
          print(indent, f"\t{attr_name}:")
          _print_vars(indent + "\t", attr_value)
        elif not attr_allowlist or attr_name in attr_allowlist:
          print(indent, f"\t{attr_name}={attr_value}")

    print(indent, "DataValues(")
    print(indent, f"\tFP={self.fingerprint().hex()}")
    if 'client_id' in vars(self).keys():
      print(indent, f"\tclient_id={self.client_id}")
    _print_vars(indent, self, subset or DEBUGPRINT_SUBSET)
    print(indent,")")

  def __str__(self):
    return f"DV(FP={self.fingerprint().hex()} CC={self.country} OS={self.os} {self.os_version})"

