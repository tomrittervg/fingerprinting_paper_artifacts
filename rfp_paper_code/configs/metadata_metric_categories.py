"""Authoritative category definitions and metric → category mapping.

Primary keys are DataValues names (current codebase).  Where the DB/CSV name
(schema-37) differs, an alias entry is also included so this dict works with
both old and new correlation CSVs.
"""

CATEGORY_ORDER = [
    'WebGL', 'WebGPU',
    'ClientRects', 'MathML',
    'Fonts', 'Canvas', 'Screen',
    'Audio', 'OS/HW', 'Tracking Preferences', 'Locale', 'Other',
]

CATEGORY_COLORS = {
    'WebGL':                '#1f77b4',
    'WebGPU':               '#9467bd',
    'ClientRects':          '#d62728',
    'MathML':               '#8c564b',
    'Fonts':                '#ff9896',
    'Canvas':               '#ff7f0e',
    'Screen':               '#ffbb78',
    'Audio':                '#17becf',
    'OS/HW':                '#bcbd22',
    'Tracking Preferences': '#e377c2',
    'Locale':               '#c5b0d5',
    'Other':                '#999999',
}

METRIC_CATEGORIES = {
    # ── Audio ─────────────────────────────────────────────────────────────────
    "audio_compressor_gain_reduction":              "Audio",
    "audio_fingerprint":                            "Audio",
    "audio_fingerprint2":                           "Audio",
    "audio_float_frequency_sum":                    "Audio",
    "audio_float_time_domain_sum":                  "Audio",
    "audio_unique_samples":                         "Audio",

    # ── Canvas ────────────────────────────────────────────────────────────────
    "canvas_canvasdata01":                          "Canvas",
    "canvas_canvasdata02":                          "Canvas",
    "canvas_canvasdata07":                          "Canvas",
    "canvas_canvasdata08":                          "Canvas",
    "canvas_canvasdata11_webgl":                    "Canvas",
    "canvas_canvasdata12_fingerprintjs1":           "Canvas",
    "canvas_canvasdata13_fingerprintjs2":           "Canvas",
    "canvassoftware_canvasdata01":                  "Canvas",
    "canvassoftware_canvasdata02":                  "Canvas",
    "canvassoftware_canvasdata13_fingerprintjs2":   "Canvas",
    # DB aliases
    "canvasdata1":                                  "Canvas",
    "canvasdata2":                                  "Canvas",
    "canvasdata7":                                  "Canvas",
    "canvasdata8":                                  "Canvas",
    "canvasdata11_webgl":                           "Canvas",
    "canvasdata12_fingerprintjs1":                  "Canvas",
    "canvasdata13_fingerprintjs2":                  "Canvas",
    "canvasdata1software":                          "Canvas",
    "canvasdata2software":                          "Canvas",
    "canvasdata13_fingerprintjs2software":          "Canvas",

    # ── ClientRects ───────────────────────────────────────────────────────────
    "clientrects_emoji_font_family":                "Fonts",
    "clientrects_ghost_dimensions":                 "ClientRects",
    "clientrects_known_dimensions":                 "ClientRects",
    "clientrects_text_font_family":                 "Fonts",
    "combined_clientrects_element_gbcr_hash":       "ClientRects",
    "combined_clientrects_element_gcr_hash":        "ClientRects",
    "combined_clientrects_emoji_hash":              "ClientRects",
    "combined_clientrects_range_gbcr_hash":         "ClientRects",
    "combined_clientrects_range_gcr_hash":          "ClientRects",
    "svg_bbox":                                     "ClientRects",
    "svg_computed_text_length":                     "ClientRects",
    "svg_emoji_set":                                "ClientRects",
    "svg_extent_of_char":                           "ClientRects",
    "svg_substring_length":                         "ClientRects",

    # ── Fonts ─────────────────────────────────────────────────────────────────
    "combined_css_colors_hash":                     "Fonts",
    "combined_css_fonts_hash":                      "Fonts",
    "fonts_fpjs_allowlisted":                       "Fonts",
    "fonts_fpjs_nonallowlisted":                    "Fonts",
    "fonts_variant_f_allowlisted":                  "Fonts",
    "fonts_variant_f_nonallowlisted":               "Fonts",
    "fonts_variant_g_allowlisted":                  "Fonts",
    "fonts_variant_g_nonallowlisted":               "Fonts",
    "fonts_variant_h_allowlisted":                  "Fonts",
    "fonts_variant_h_nonallowlisted":               "Fonts",
    "fonts_variant_i_allowlisted":                  "Fonts",
    "fonts_variant_i_nonallowlisted":               "Fonts",
    "prefs_use_document_colors":                    "Fonts",
    "use_document_colors":                          "Fonts",    # DB alias

    # ── Locale ────────────────────────────────────────────────────────────────
    "intl_intl_locale":                             "Locale",
    "intl_locale":                                  "Locale",   # DB alias
    "intl_timezone_offset_web":                     "Locale",
    "timezone_offset_web":                          "Locale",   # DB alias
    "intl_timezone_web":                            "Locale",
    "timezone_web":                                 "Locale",   # DB alias
    "locale_accept_language":                       "Locale",
    "prefs_intl_accept_languages":                  "Locale",   # DB alias
    "locale_languages":                             "Locale",
    "languages":                                    "Locale",   # DB alias

    # ── MathML ────────────────────────────────────────────────────────────────
    "combined_mathml_hash":                         "MathML",

    # ── OS/HW ─────────────────────────────────────────────────────────────────
    "combined_math_ops_hash":                       "OS/HW",
    "combined_media_capabilities_hash":             "OS/HW",
    "hw_any_pointer_type":                          "OS/HW",
    "any_pointer_type":                             "OS/HW",    # DB alias
    "hw_max_touch_points":                          "OS/HW",
    "max_touch_points":                             "OS/HW",    # DB alias
    "hw_oscpu":                                     "OS/HW",
    "oscpu":                                        "OS/HW",    # DB alias
    "hw_pointer_type":                              "OS/HW",
    "pointer_type":                                 "OS/HW",    # DB alias
    "hw_processor_count":                           "OS/HW",
    "processor_count":                              "OS/HW",    # DB alias
    "platform":                                     "OS/HW",
    "prefs_eme_enabled":                            "OS/HW",
    "prefs_media_eme_enabled":                      "OS/HW",    # DB alias
    "prefs_pdf_viewer":                             "OS/HW",
    "pdf_viewer":                                   "OS/HW",    # DB alias
    "sdp_codec_list":                               "OS/HW",
    "storage_quota":                                "OS/HW",
    "user_agent":                                   "OS/HW",
    "voices_sha1":                                  "OS/HW",
    "webauthn_capabilities":                        "OS/HW",

    # ── Screen ────────────────────────────────────────────────────────────────
    "screen_inverted_colors":                       "Screen",
    "inverted_colors":                              "Screen",   # DB alias
    "screen_monochrome":                            "Screen",
    "monochrome":                                   "Screen",   # DB alias
    "screen_primary_avail":                         "Screen",
    "screen_primary_color_depth":                   "Screen",
    "screen_primary_orientation":                   "Screen",
    "screen_primary_pixel_depth":                   "Screen",
    "screen_primary_resolution":                    "Screen",
    "screen_primary_video_dynamic_range":           "Screen",
    "screen_web_avail_left":                        "Screen",
    "avail_left":                                   "Screen",   # DB alias
    "screen_web_avail_top":                         "Screen",
    "avail_top":                                    "Screen",   # DB alias
    "screen_web_inner":                             "Screen",
    "screen_web_outer":                             "Screen",
    "screen_web_pixel_ratio":                       "Screen",
    "pixel_ratio":                                  "Screen",   # DB alias

    # ── Tracking Preferences ──────────────────────────────────────────────────
    "screen_color_scheme":                          "Tracking Preferences",
    "color_scheme":                                 "Tracking Preferences", # DB alias
    "screen_prefers_contrast":                      "Tracking Preferences",
    "prefers_contrast":                             "Tracking Preferences", # DB alias
    "screen_prefers_reduced_motion":                "Tracking Preferences",
    "prefers_reduced_motion":                       "Tracking Preferences", # DB alias
    "screen_prefers_reduced_transparency":          "Tracking Preferences",
    "prefers_reduced_transparency":                 "Tracking Preferences", # DB alias
    "prefs_cookiesenabled":                         "Tracking Preferences",
    "prefs_network_cookie_cookiebehavior":          "Tracking Preferences", # DB alias (semantic mismatch; best proxy)
    "prefs_general_donottrack_enabled":             "Tracking Preferences",
    "prefs_privacy_donottrackheader_enabled":       "Tracking Preferences", # DB alias
    "prefs_general_globalprivacycontrol_enabled":   "Tracking Preferences",
    "prefs_privacy_globalprivacycontrol_enabled":   "Tracking Preferences", # DB alias

    # ── WebGL ─────────────────────────────────────────────────────────────────
    "combined_webgl1_params_hash":                  "WebGL",
    "combined_webgl_extensions_hash":               "WebGL",
    "webgl2_precision_fragment":                    "WebGL",
    "gl2_precision_fragment":                       "WebGL",    # DB alias
    "webgl2_precision_vertex":                      "WebGL",
    "gl2_precision_vertex":                         "WebGL",    # DB alias
    "webgl2_renderer":                              "WebGL",
    "gl2_renderer":                                 "WebGL",    # DB alias
    "webgl2_vendor":                                "WebGL",
    "gl2_vendor":                                   "WebGL",    # DB alias
    "webgl2_vendor_raw":                            "WebGL",
    "gl2_vendor_raw":                               "WebGL",    # DB alias
    "webgl_extensions":                             "WebGL",
    "gl_extensions":                                "WebGL",    # DB alias
    "webgl_precision_fragment":                     "WebGL",
    "gl_precision_fragment":                        "WebGL",    # DB alias
    "webgl_precision_vertex":                       "WebGL",
    "gl_precision_vertex":                          "WebGL",    # DB alias
    "webgl_renderer":                               "WebGL",
    "gl_renderer":                                  "WebGL",    # DB alias
    "webgl_vendor":                                 "WebGL",
    "gl_vendor":                                    "WebGL",    # DB alias
    "webgl_vendor_raw":                             "WebGL",
    "gl_vendor_raw":                                "WebGL",    # DB alias

    "gl_params":                                    "WebGL",
    "gl_params_extensions":                         "WebGL",

    # ── WebGPU ────────────────────────────────────────────────────────────────
    "combined_wgpu_hash":                           "WebGPU",
    "wgpu_is_fallback_adapter":                     "WebGPU",
    "wgpu_missing_features":                        "WebGPU",

    # ── CSS Colors (OS theme) ────────────────────────────────────────────────
    **{m: "OS/HW" for m in [
        "css_color_accentcolor", "css_color_accentcolortext",
        "css_color_activeborder", "css_color_activecaption", "css_color_activetext",
        "css_color_appworkspace", "css_color_background",
        "css_color_buttonborder", "css_color_buttonface", "css_color_buttonhighlight",
        "css_color_buttonshadow", "css_color_buttontext",
        "css_color_canvas", "css_color_canvastext", "css_color_captiontext",
        "css_color_field", "css_color_fieldtext", "css_color_graytext",
        "css_color_highlight", "css_color_highlighttext",
        "css_color_inactiveborder", "css_color_inactivecaption", "css_color_inactivecaptiontext",
        "css_color_infobackground", "css_color_infotext",
        "css_color_linktext", "css_color_mark", "css_color_marktext",
        "css_color_menu", "css_color_menutext", "css_color_scrollbar",
        "css_color_selecteditem", "css_color_selecteditemtext",
        "css_color_threeddarkshadow", "css_color_threedface", "css_color_threedhighlight",
        "css_color_threedlightshadow", "css_color_threedshadow",
        "css_color_visitedtext", "css_color_window", "css_color_windowframe", "css_color_windowtext",
        "combined_css_colors_hash", "css_system_colors", "color_scheme",
    ]},

    # ── CSS Fonts ────────────────────────────────────────────────────────────
    **{m: "Fonts" for m in [
        "css_font_arial", "css_font_caption", "css_font_courier_new",
        "css_font_cursive", "css_font_fantasy", "css_font_georgia",
        "css_font_helvetica", "css_font_icon", "css_font_menu",
        "css_font_message_box", "css_font_monospace", "css_font_sans_serif",
        "css_font_serif", "css_font_small_caption", "css_font_status_bar",
        "css_font_system_ui", "css_font_times_new_roman", "css_font_verdana",
        "combined_css_fonts_hash", "css_system_fonts",
        "fonts_fpjs_allowlisted", "fonts_fpjs_nonallowlisted",
        "fonts_variant_f_allowlisted", "fonts_variant_f_nonallowlisted",
        "fonts_variant_g_allowlisted", "fonts_variant_g_nonallowlisted",
        "fonts_variant_h_allowlisted", "fonts_variant_h_nonallowlisted",
        "fonts_variant_i_allowlisted", "fonts_variant_i_nonallowlisted",
    ]},

    # ── Media ────────────────────────────────────────────────────────────────
    **{m: "Audio" for m in [
        "media_capabilities_h264", "media_capabilities_not_efficient",
        "media_capabilities_not_smooth", "media_capabilities_unsupported",
        "combined_media_capabilities_hash",
    ]},

    # ── MathML/MathOps (DB names) ────────────────────────────────────────────
    **{f"mathml{i}": "MathML" for i in range(1, 11)},
    "math_ops":                                     "MathML",
    "combined_math_ops_hash":                       "MathML",
    "combined_mathml_hash":                         "MathML",

    # ── Individual ClientRects (DB names) ────────────────────────────────────
    **{f"clientrects_element_gbcr_{i:02d}": "ClientRects" for i in range(1, 13)},
    **{f"clientrects_element_gcr_{i:02d}": "ClientRects" for i in range(1, 13)},
    **{f"clientrects_range_gbcr_{i:02d}": "ClientRects" for i in range(1, 13)},
    **{f"clientrects_range_gcr_{i:02d}": "ClientRects" for i in range(1, 13)},
    **{f"clientrects_emoji_{i:02d}": "ClientRects" for i in range(1, 7)},

    # ── Individual wgpu params (DB names) ────────────────────────────────────
    **{m: "WebGPU" for m in [
        "wgpu_maxbindgroups", "wgpu_maxbindgroupsplusvertexbuffers",
        "wgpu_maxbindingsperbindgroup", "wgpu_maxbuffersize",
        "wgpu_maxcolorattachmentbytespersample", "wgpu_maxcolorattachments",
        "wgpu_maxcomputeinvocationsperworkgroup", "wgpu_maxcomputeworkgroupsizex",
        "wgpu_maxcomputeworkgroupsizey", "wgpu_maxcomputeworkgroupsizez",
        "wgpu_maxcomputeworkgroupsperdimension", "wgpu_maxcomputeworkgroupstoragesize",
        "wgpu_maxdynamicstoragebuffersperpipelinelayout", "wgpu_maxdynamicuniformbuffersperpipelinelayout",
        "wgpu_maxinterstageshadervariables", "wgpu_maxsampledtexturespershaderstage",
        "wgpu_maxsamplerspershaderstage", "wgpu_maxstoragebufferbindingsize",
        "wgpu_maxstoragebufferspershaderstage", "wgpu_maxstoragetexturespershaderstage",
        "wgpu_maxtexturearraylayers", "wgpu_maxtexturedimension1d",
        "wgpu_maxtexturedimension2d", "wgpu_maxtexturedimension3d",
        "wgpu_maxuniformbufferbindingsize", "wgpu_maxuniformbufferspershaderstage",
        "wgpu_maxvertexattributes", "wgpu_maxvertexbufferarraystride",
        "wgpu_maxvertexbuffers", "wgpu_minstoragebufferoffsetalignment",
        "wgpu_minuniformbufferoffsetalignment",
    ]},

    # ── Screen (DB names that match DataValues names) ────────────────────────
    **{m: "Screen" for m in [
        "screen_primary_avail", "screen_primary_color_depth",
        "screen_primary_orientation", "screen_primary_pixel_depth",
        "screen_primary_resolution", "screen_primary_video_dynamic_range",
        "screen_web_inner", "screen_web_outer", "avail_left", "avail_top",
        "storage_quota",
    ]},

    # ── Tracking Preferences (DB names) ──────────────────────────────────────
    **{m: "Tracking Preferences" for m in [
        "prefs_intl_accept_languages", "prefs_media_eme_enabled",
        "prefs_network_cookie_cookiebehavior",
        "prefs_privacy_donottrackheader_enabled",
        "prefs_privacy_globalprivacycontrol_enabled",
    ]},

    # ── Locale (DB names) ────────────────────────────────────────────────────
    "intl_locale":                                  "Locale",
    "languages":                                    "Locale",

    # ── OS/HW (DB names) ────────────────────────────────────────────────────
    **{m: "OS/HW" for m in [
        "any_pointer_type", "inverted_colors", "max_touch_points", "monochrome",
        "oscpu", "pdf_viewer", "pixel_ratio", "platform", "pointer_type",
        "prefers_contrast", "prefers_reduced_motion", "prefers_reduced_transparency",
        "processor_count", "sdp_codec_list", "timezone_offset_web", "timezone_web",
        "use_document_colors", "user_agent", "voices_sha1", "webauthn_capabilities",
    ]},
}
