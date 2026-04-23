from filters import Filter
from experiments import fontProtectionsFilter, fdlibmFilter

class etpFilter(fontProtectionsFilter, fdlibmFilter):
  make_constant = [
      "intl_keyboard_layout",

      "webgl2_params_MAX_VERTEX_UNIFORM_COMPONENTS",
      "webgl2_params_MIN_PROGRAM_TEXEL_OFFSET",
      "webgl2_params_UNIFORM_BUFFER_OFFSET_ALIGNMENT",
  ]

  make_platform = [
      "hw_max_touch_points",
      "user_agent"
  ]

  change_resolution = [
      "screen_primary_avail",
      "screen_web_outer",
      "screen_web_inner"
  ]

  def __init__(self, dataValues):
    fontProtectionsFilter.__init__(self, dataValues)
    fdlibmFilter.__init__(self, dataValues)

    """
    for attr in self.make_constant + self.make_platform + self.change_resolution:
      self.originals[attr] = getattr(dataValues, attr)

    for attr in self.make_constant:
      setattr(dataValues, attr, "0")

    for attr in self.make_constant:
      setattr(dataValues, attr, dataValues.platform)

    for attr in self.change_resolution:
      setattr(dataValues, attr, dataValues.screen_primary_resolution)
    """

    self.applied_effect = True

  def revert(self, dataValues):
    fontProtectionsFilter.revert(self, dataValues)
    fdlibmFilter.revert(self, dataValues)
    #for attr in self.make_constant + self.make_platform + self.change_resolution:
    #  setattr(dataValues, attr, self.originals[attr])




class rfpFilter(Filter):
  make_constant = [
      "intl_keyboard_layout",
      "locale_accept_language",
      "intl_system_locale",
      "intl_intl_locale",
      "intl_timezone",
      "intl_timezoneoffset",
      "screen_primary_color_depth",
      # "screen_color_gamut",
      "screen_color_scheme",
      "screen_primary_pixel_depth",
      "screen_web_pixel_ratio",
      "screen_prefers_contrast",
      "screen_prefers_reduced_motion",
      "screen_prefers_reduced_transparency",
      "screen_inverted_colors",
      "screen_primary_video_dynamic_range",
      "screen_monochrome",
      "screen_primary_orientation",
      "screen_primary_orientation_angle",
      "screen_size_mode",
      "screen_primary_posx",
      "screen_primary_posy",
      "screen_primary_scale_factor",
      "screen_text_anti_aliasing",
      "prefs_zoom_text_only",
      "prefs_eme_enabled",
      "prefs_block_popups",
      "prefs_general_autoscroll",
      "prefs_general_smoothscroll",
      "prefs_general_overlay_scrollbars",
      "prefs_general_donottrack_enabled",
      "prefs_general_globalprivacycontrol_enabled",
      "prefs_use_document_colors",
      "prefs_pdf_viewer",
      "prefs_cookiebehavior",
      "prefs_zoom_count",
      "prefs_changed_media_prefs",
      "hw_gamepads",
      "hw_camera_count",
      "hw_microphone_count",
      "hw_speaker_count",
      "hw_group_count",
      "hw_group_count_wo_speakers",
      "ice_order",
      "ice_sd",
      "media_capabilities_not_efficient",
      "media_capabilities_not_smooth",
      "media_capabilities_unsupported",
      "media_h264",
      "hw_processor_count",
      "hw_oscpu",
      "hw_motion_decimals",
      "hw_motion_freq",
      "hw_orientation_decimals",
      "hw_orientation_freq",
      "hw_orientationabs_decimals",
      "hw_orientationabs_freq",
      "hw_any_pointer_type",
      "hw_pointer_height",
      "hw_pointer_tiltx",
      "hw_pointer_tilty",
      "hw_pointer_twist",
      "hw_pointer_type",
      "hw_pointer_width",
      "hw_pointer_pressure",
      "hw_pointer_tangentinal_pressure",
      "hw_touch_rotation_angle",
      "audio_channels",
      "audio_frames",
      "audio_rate",
      "target_frame_rate",
      "voices_count",
      "voices_local_count",
      "voices_all_ssdeep",
      "voices_default",
      "voices_local_ssdeep",
      "voices_nonlocal_ssdeep",
      "voices_sample",
      "voices_sha1",
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
      "canvassoftware_canvasdata01",
      "canvassoftware_canvasdata02",
      "canvassoftware_canvasdata03",
      "canvassoftware_canvasdata04",
      "canvassoftware_canvasdata05",
      "canvassoftware_canvasdata06",
      "canvassoftware_canvasdata07",
      "canvassoftware_canvasdata08",
      "canvassoftware_canvasdata09",
      "canvassoftware_canvasdata10",
      "canvassoftware_canvasdata11_webgl",
      "canvassoftware_canvasdata12_fingerprintjs1",
      "canvassoftware_canvasdata13_fingerprintjs2",
      "webgl_extensions",
      "webgl_extensions_raw",
      "webgl_renderer",
      "webgl_renderer_raw",
      "webgl_vendor",
      "webgl_vendor_raw",
      "webgl_version_raw",
      "webgl_fragment_shader",
      "webgl_vertex_shader",
      "webgl_minimal_source",
      "webgl_params_extensions",
      "webgl_params",
      "webgl_precision_fragment",
      "webgl_precision_vertex",
      "webgl_context_type",
      "webgl_version_software",
      "webgl_extensions_software",
      "webgl_extensions_raw_software",
      "webgl_renderer_software",
      "webgl_renderer_raw_software",
      "webgl_vendor_software",
      "webgl_vendor_raw_software",
      "webgl_version_raw_software",
      "webgl_fragment_shader_software",
      "webgl_vertex_shader_software",
      "webgl_minimal_source_software",
      "webgl_params_extensions_software",
      "webgl_params_software",
      "webgl_precision_fragment_software",
      "webgl_precision_vertex_software",
      "webgl_context_type_software",
      "webgl2_extensions",
      "webgl2_extensions_raw",
      "webgl2_renderer",
      "webgl2_renderer_raw",
      "webgl2_vendor",
      "webgl2_vendor_raw",
      "webgl2_version_raw",
      "webgl2_fragment_shader",
      "webgl2_vertex_shader",
      "webgl2_minimal_source",
      "webgl2_params_extensions",
      "webgl2_params",
      "webgl2_precision_fragment",
      "webgl2_precision_vertex",
      "webgl2_context_type",
      "webgl2_version_software",
      "webgl2_extensions_software",
      "webgl2_extensions_raw_software",
      "webgl2_renderer_software",
      "webgl2_renderer_raw_software",
      "webgl2_vendor_software",
      "webgl2_vendor_raw_software",
      "webgl2_version_raw_software",
      "webgl2_fragment_shader_software",
      "webgl2_vertex_shader_software",
      "webgl2_minimal_source_software",
      "webgl2_params_extensions_software",
      "webgl2_params_software",
      "webgl2_precision_fragment_software",
      "webgl2_precision_vertex_software",
      "webgl2_context_type_software",
      "wgpu_missing_features",
      "wgpu_maxtexturedimension1d",
      "wgpu_maxtexturedimension2d",
      "wgpu_maxtexturedimension3d",
      "wgpu_maxtexturearraylayers",
      "wgpu_maxbindgroups",
      "wgpu_maxbindgroupsplusvertexbuffers",
      "wgpu_maxbindingsperbindgroup",
      "wgpu_maxdynamicuniformbuffersperpipelinelayout",
      "wgpu_maxdynamicstoragebuffersperpipelinelayout",
      "wgpu_maxsampledtexturespershaderstage",
      "wgpu_maxsamplerspershaderstage",
      "wgpu_maxstoragebufferspershaderstage",
      "wgpu_maxstoragetexturespershaderstage",
      "wgpu_maxuniformbufferspershaderstage",
      "wgpu_maxuniformbufferbindingsize",
      "wgpu_maxstoragebufferbindingsize",
      "wgpu_minuniformbufferoffsetalignment",
      "wgpu_minstoragebufferoffsetalignment",
      "wgpu_maxvertexbuffers",
      "wgpu_maxbuffersize",
      "wgpu_maxvertexattributes",
      "wgpu_maxvertexbufferarraystride",
      "wgpu_maxinterstageshadervariables",
      "wgpu_maxcolorattachments",
      "wgpu_maxcolorattachmentbytespersample",
      "wgpu_maxcomputeworkgroupstoragesize",
      "wgpu_maxcomputeinvocationsperworkgroup",
      "wgpu_maxcomputeworkgroupsizex",
      "wgpu_maxcomputeworkgroupsizey",
      "wgpu_maxcomputeworkgroupsizez",
      "wgpu_maxcomputeworkgroupsperdimension",
      "font_font_name_list_emoji_modified",
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
      "font_default_default_group",
      "font_default_western",
      "font_minimum_size_default_group",
      "font_minimum_size_western",
      "font_name_monospace_default_group",
      "font_name_monospace_western",
      "font_name_sans_serif_default_group",
      "font_name_sans_serif_western",
      "font_name_serif_default_group",
      "font_name_serif_western",
      "font_size_monospace_default_group",
      "font_size_monospace_western",
      "font_size_variable_default_group",
      "font_size_variable_western",
      "missing_fonts",
      "webgl_params_ALIASED_LINE_WIDTH_RANGE",
      "webgl_params_ALIASED_POINT_SIZE_RANGE",
      "webgl_params_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
      "webgl_params_MAX_CUBE_MAP_TEXTURE_SIZE",
      "webgl_params_MAX_FRAGMENT_UNIFORM_VECTORS",
      "webgl_params_MAX_RENDERBUFFER_SIZE",
      "webgl_params_MAX_TEXTURE_IMAGE_UNITS",
      "webgl_params_MAX_TEXTURE_SIZE",
      "webgl_params_MAX_VARYING_VECTORS",
      "webgl_params_MAX_VERTEX_ATTRIBS",
      "webgl_params_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
      "webgl_params_MAX_VERTEX_UNIFORM_VECTORS",
      "webgl_params_MAX_VIEWPORT_DIMS",
      "webgl_params_SHADING_LANGUAGE_VERSION",
      "webgl2_params_ALIASED_LINE_WIDTH_RANGE",
      "webgl2_params_ALIASED_POINT_SIZE_RANGE",
      "webgl2_params_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
      "webgl2_params_MAX_CUBE_MAP_TEXTURE_SIZE",
      "webgl2_params_MAX_FRAGMENT_UNIFORM_VECTORS",
      "webgl2_params_MAX_RENDERBUFFER_SIZE",
      "webgl2_params_MAX_TEXTURE_IMAGE_UNITS",
      "webgl2_params_MAX_TEXTURE_SIZE",
      "webgl2_params_MAX_VARYING_VECTORS",
      "webgl2_params_MAX_VERTEX_ATTRIBS",
      "webgl2_params_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
      "webgl2_params_MAX_VERTEX_UNIFORM_VECTORS",
      "webgl2_params_MAX_VIEWPORT_DIMS",
      "webgl2_params_SHADING_LANGUAGE_VERSION",
      "webgl2_params_MAX_3D_TEXTURE_SIZE",
      "webgl2_params_MAX_ARRAY_TEXTURE_LAYERS",
      "webgl2_params_MAX_CLIENT_WAIT_TIMEOUT_WEBGL",
      "webgl2_params_MAX_COLOR_ATTACHMENTS",
      "webgl2_params_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS",
      "webgl2_params_MAX_COMBINED_UNIFORM_BLOCKS",
      "webgl2_params_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS",
      "webgl2_params_MAX_DRAW_BUFFERS",
      "webgl2_params_MAX_ELEMENT_INDEX",
      "webgl2_params_MAX_ELEMENTS_INDICES",
      "webgl2_params_MAX_ELEMENTS_VERTICES",
      "webgl2_params_MAX_FRAGMENT_INPUT_COMPONENTS",
      "webgl2_params_MAX_FRAGMENT_UNIFORM_BLOCKS",
      "webgl2_params_MAX_FRAGMENT_UNIFORM_COMPONENTS",
      "webgl2_params_MAX_PROGRAM_TEXEL_OFFSET",
      "webgl2_params_MAX_SAMPLES",
      "webgl2_params_MAX_SERVER_WAIT_TIMEOUT",
      "webgl2_params_MAX_TEXTURE_LOD_BIAS",
      "webgl2_params_MAX_TRANSFORM_FEEDBACK_INTERLEAVED_COMPONENTS",
      "webgl2_params_MAX_TRANSFORM_FEEDBACK_SEPARATE_ATTRIBS",
      "webgl2_params_MAX_TRANSFORM_FEEDBACK_SEPARATE_COMPONENTS",
      "webgl2_params_MAX_UNIFORM_BLOCK_SIZE",
      "webgl2_params_MAX_UNIFORM_BUFFER_BINDINGS",
      "webgl2_params_MAX_VARYING_COMPONENTS",
      "webgl2_params_MAX_VERTEX_OUTPUT_COMPONENTS",
      "webgl2_params_MAX_VERTEX_UNIFORM_BLOCKS",
      "webgl2_params_MAX_VERTEX_UNIFORM_COMPONENTS",
      "webgl2_params_MIN_PROGRAM_TEXEL_OFFSET",
      "webgl2_params_UNIFORM_BUFFER_OFFSET_ALIGNMENT",
  ]

  make_platform = [
      "hw_max_touch_points",
      "user_agent"
  ]

  change_resolution = [
    "screen_primary_resolution",
      "screen_primary_avail",
      #"screen_web_outer",
      "screen_web_inner"
  ]

  def _get_stepped_size(self, x, iswidth):
    x = int(x)
    if x <= 50:
      return x
    elif x <= 500:
      return x - (x % 50)
    elif x <= 1600:
      if iswidth:
        return x - (x % 200)
      return x - (x % 100)
    else:
      return x - (x % 200)

  def __init__(self, dataValues):
    self.originals = {}

    # Apply gamepad protection
    self.originals['hw_gamepads'] = dataValues.hw_gamepads
    dataValues.hw_gamepads = ""

    # Apply media count protection
    self.originals['hw_camera_count'] = dataValues.hw_camera_count
    self.originals['hw_microphone_count'] = dataValues.hw_microphone_count
    dataValues.hw_camera_count = 1
    dataValues.hw_microphone_count = 1

    for attr in self.make_constant + self.make_platform + self.change_resolution:
      self.originals[attr] = getattr(dataValues, attr)

    for attr in self.make_constant:
      setattr(dataValues, attr, "0")

    for attr in self.make_platform:
      setattr(dataValues, attr, dataValues.platform)

    self.originals['screen_web_outer'] = dataValues.screen_web_outer
    outer_width = self._get_stepped_size(dataValues.screen_web_outer_width, iswidth=True)
    outer_height = self._get_stepped_size(dataValues.screen_web_outer_height, iswidth=False)
    dataValues.screen_web_outer = f"{outer_width}x{outer_height}"

    for attr in self.change_resolution:
      setattr(dataValues, attr, dataValues.screen_web_outer)

    self.applied_effect = True

  def revert(self, dataValues):
    for attr in self.originals:
      setattr(dataValues, attr, self.originals[attr])



ALL_MODES = {
    #"etp": [etpFilter],
    "RFP": [rfpFilter],
}

