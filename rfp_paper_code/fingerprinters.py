###############################################################################
###############################################################################
###############################################################################
###############################################################################

FPSET_SIFT_SCIENCE =  set([
    "screen_primary_resolution",
    "user_agent",
    "locale_accept_language",
    "screen_primary_color_depth",
    "platform",
    "intl_timezoneoffset",
    "prefs_cookiesenabled", # navigator.cookieEnabled → prefs_cookiebehavior != 2
    "hw_max_touch_points",
    "hw_processor_count",
    "hw_oscpu",
    "prefs_general_donottrack_enabled",
    "canvas_canvasdata12_fingerprintjs1", # This isn't the exact fingerprint they calculate, but we will approximate it with the usage of these
    "canvas_canvasdata13_fingerprintjs2",
    #"math_op_0",   # ↓ all 24 → combined_math_ops_hash
    #"math_op_1",
    #"math_op_2",
    #"math_op_3",
    #"math_op_4",
    #"math_op_5",
    #"math_op_6",
    #"math_op_7",
    #"math_op_8",
    #"math_op_9",
    #"math_op_10",
    #"math_op_11",
    #"math_op_12",
    #"math_op_13",
    #"math_op_14",
    #"math_op_15",
    #"math_op_16",
    #"math_op_17",
    #"math_op_18",
    #"math_op_19",
    #"math_op_20",
    #"math_op_21",
    #"math_op_22",
    #"math_op_23",  # ↑ all 24 → combined_math_ops_hash
    "combined_math_ops_hash",
])

"""
window.navigator.cookieEnabled
window.navigator.doNotTrack
window.navigator.hardwareConcurrency
window.navigator.javaEnabled -> constant False
window.navigator.language -> the first entry of 'langauges'
window.navigator.languages
window.navigator.maxTouchPoints
window.navigator.mimeTypes -> constant value derived from plugins
window.navigator.onLine -> true if the user is online... we'll ignore this
window.navigator.oscpu
window.navigator.platform
window.navigator.plugins -> constant value
window.navigator.product -> constant value
window.navigator.productSub -> constant value
window.navigator.userAgent ->
window.navigator.vendor -> constant value
window.navigator.vendorSub ->
window.screen.colorDepth
"""

###############################################################################
###############################################################################
###############################################################################
###############################################################################


FPSET_AKAMAI_V1 = set([
    "screen_primary_color_depth",
    "screen_primary_pixel_depth",
    "user_agent",
    "platform",
    "hw_oscpu",
    "hw_processor_count",
    "locale_accept_language",
    "prefs_general_donottrack_enabled",
    "prefs_cookiesenabled",
    "hw_max_touch_points",
])

"""
window.navigator.plugins ->  constant
window.screen.colorDepth
window.screen.pixelDepth
window.navigator.userAgent
window.navigator.appName ->  constant
window.navigator.appCodeName ->  constant
window.navigator.appVersion
window.navigator.product ->  constant
window.navigator.productSub ->  constant
window.navigator.vendor ->  constant
window.navigator.vendorSub ->  constant
window.navigator.buildID ->  constant
window.navigator.platform
window.navigator.oscpu
window.navigator.hardwareConcurrency
window.navigator.language
window.navigator.languages
window.navigator.doNotTrack
window.navigator.cookieEnabled
window.navigator.geolocation -> constant
window.navigator.maxTouchPoints
window.navigator.webdriver -> constant
window.navigator.permissions -> constant
"""

###############################################################################
###############################################################################
###############################################################################
###############################################################################

FPSET_AKAMAI_V2 = set([
    # Canvas 2D fingerprint (SHA-1 hash of rendered text + rectangles via canvas.toDataURL())
    "canvas_canvasdata12_fingerprintjs1", # Not the exact same drawing operations, but same canvas 2D surface
    "canvas_canvasdata13_fingerprintjs2",
    # navigator.userAgent
    "user_agent",
    # Font enumeration — NO font collection code exists in the script at all. The payload schema
    # declares `fonts` and `fh` (font hash) fields but no function ever writes to them.
    # screen.width x screen.height
    "screen_primary_resolution",
    # screen.availWidth x screen.availHeight
    "screen_primary_avail",
    # screen.colorDepth
    "screen_primary_color_depth",
    # screen.pixelDepth
    "screen_primary_pixel_depth",
    # navigator.hardwareConcurrency
    "hw_processor_count",
    # navigator.language / navigator.languages
    "locale_accept_language",
    # navigator.platform
    "platform",
    # navigator.oscpu
    "hw_oscpu",
    # navigator.buildID - constant in Firefox
    # navigator.doNotTrack
    "prefs_general_donottrack_enabled",
    # navigator.maxTouchPoints
    "hw_max_touch_points",
    # navigator.cookieEnabled → prefs_cookiesenabled (prefs_cookiebehavior != 2)
    "prefs_cookiesenabled",
    # window.innerWidth x window.innerHeight
    "screen_web_inner",
    # window.outerWidth x window.outerHeight
    "screen_web_outer",
    # new Date().getTimezoneOffset()
    "intl_timezone_offset_web",
    # navigator.languages
    "locale_languages",
])

FPSET_AKAMAI_V2_INOUT = (FPSET_AKAMAI_V2 - {"screen_web_inner", "screen_web_outer"}) | {
    "screen_web_outer_inner_diff",
}

"""
Akamai Bot Manager v2 — Web APIs queried
Source: deobfuscated script from /akam/13/ endpoints (xfinity, prada, americanexpress)
Reference: rfp_fingerprinters_tracking/akamai/analysis/web-api-inventory.md
Analysis: rfp_fingerprinters_tracking/akamai/

=== Provides fingerprinting entropy ===

Canvas 2D API:
  document.createElement("canvas").getContext("2d")
  ctx.fillStyle, ctx.font, ctx.textBaseline, ctx.fillText(), ctx.fillRect()
  canvas.toDataURL() → SHA-1 hashed

Navigator properties:
  navigator.userAgent                → user_agent
  navigator.platform                 → platform
  navigator.oscpu                    → hw_oscpu
  navigator.hardwareConcurrency      → hw_processor_count
  navigator.language                 → locale_accept_language (first element)
  navigator.languages                → locale_accept_language
  navigator.doNotTrack               → prefs_general_donottrack_enabled
  navigator.maxTouchPoints           → hw_max_touch_points
  navigator.cookieEnabled            → prefs_cookiesenabled (prefs_cookiebehavior != 2)
  navigator.buildID                  → NO MATCH (constant in modern Firefox)
  navigator.plugins                  → NO MATCH (constant in modern Firefox)
  navigator.appVersion               → NO MATCH (subset of userAgent)
  navigator.vendor                   → NO MATCH (constant "" in Firefox)
  navigator.productSub               → NO MATCH (constant "20100101" in Firefox)
  navigator.appName                  → NO MATCH (constant "Netscape")
  navigator.appCodeName              → NO MATCH (constant "Mozilla")
  navigator.product                  → NO MATCH (constant "Gecko")
  navigator.vendorSub                → NO MATCH (constant "")
  navigator.webdriver                → NO MATCH (automation flag, not fingerprinting)
  navigator.geolocation              → NO MATCH (presence check, constant)
  navigator.vibrate                  → NO MATCH (presence check only)

Screen / Window dimensions:
  screen.width, screen.height        → screen_primary_resolution
  screen.availWidth, screen.availHeight → screen_primary_avail
  screen.colorDepth                  → screen_primary_color_depth
  screen.pixelDepth                  → screen_primary_pixel_depth
  window.innerWidth, window.innerHeight → screen_web_inner
  window.outerWidth, window.outerHeight → screen_web_outer
  window.screenX, window.screenY     → NO MATCH (ephemeral window position)
  window.pageXOffset, window.pageYOffset → NO MATCH (ephemeral scroll offset)
  document.body.clientWidth/Height   → NO MATCH (depends on page content)

Timezone:
  new Date().getTimezoneOffset()     → intl_timezone_offset_web
  new Date().valueOf()               → NO MATCH (ephemeral timestamp)

Font enumeration:
  NO font collection code at all     → NO MATCH (dead schema fields; no CSS, JS, or plugin-based enumeration)

=== Does NOT provide fingerprinting entropy (collected but not useful) ===

Dead technology probes:
  Shockwave Flash (navigator.plugins / ActiveXObject)
  Silverlight (navigator.plugins / ActiveXObject)
  IE userData storage (document.createElement("div").style.behavior)
  ActiveX PDF viewer (ActiveXObject("PDF.PdfCtrl.*"))

DOM/BOM feature detection (constant within a Firefox version):
  window.{XDomainRequest, createPopup, removeEventListener, globalStorage,
          openDatabase, indexedDB, attachEvent, ActiveXObject, dispatchEvent,
          addBehavior, addEventListener, detachEvent, fireEvent, MutationObserver,
          HTMLMenuItemElement, Int8Array, postMessage, querySelector}
  document.{getElementsByClassName, querySelector, images, compatMode,
            documentMode, all}
  window.performance.now
  document.documentElement.contextMenu

Storage availability (near-universal):
  window.localStorage (setItem/removeItem test)
  window.sessionStorage (setItem/removeItem test)

APNG support (universal in modern browsers):
  Image + canvas drawImage of APNG test image

Battery API (blocked in modern browsers):
  navigator.getBattery()

Permissions API (not a fingerprinting vector):
  navigator.permissions.query() for 20 permission names

Browser detection (always "Firefox" within Firefox population):
  Feature-based browser name detection (InstallTrigger, etc.)

Chrome runtime check (never exists in Firefox):
  window.chrome

JavaScript version detection (constant within Firefox version):
  <script language="JavaScript1.X"> for versions 1.1–2.0

Bot detection (anti-automation, not fingerprinting):
  Selenium/webdriver attribute checks on document.documentElement
  window.external Sequentum check
  XPathResult presence, chrome runtime anomaly

Notable absent surfaces (confirmed by web-api-inventory):
  No WebGL fingerprinting (no vendor/renderer, no parameter dump, no rendered image)
  No Audio fingerprinting (no OfflineAudioContext, no Web Audio API)
  No font collection code (schema fields exist but never populated)
  No WebRTC (no RTCPeerConnection, no SDP, no IP detection)
  No CSS media queries (no matchMedia calls)
  ~40% of API surface is dead technology (Flash, Silverlight, ActiveX, IE userData, attachEvent)
  All three analyzed scripts (americanexpress, prada, xfinity) are byte-for-byte identical logic
"""

###############################################################################
###############################################################################
###############################################################################
###############################################################################

FPSET_FINGERPRINTJS_V1 = set([
    "screen_primary_color_depth",
    # "screen_primary_color_gamut",
    "screen_prefers_contrast",
    "prefs_cookiesenabled", # navigator.cookieEnabled → prefs_cookiebehavior != 2
    "screen_inverted_colors",
    "hw_processor_count",
    "screen_primary_video_dynamic_range",
    "locale_accept_language",
    "screen_monochrome",
    "hw_oscpu",
    "prefs_pdf_viewer",
    "platform",
    "screen_prefers_reduced_motion",
    "screen_primary_resolution",
    "screen_primary_avail",
    "intl_timezone",
    "intl_timezoneoffset",
    "hw_max_touch_points",
    "hw_oscpu",
    "canvas_canvasdata12_fingerprintjs1",
    "canvas_canvasdata13_fingerprintjs2",
    "audio_fingerprint",
    #"math_op_0",   # ↓ all 24 → combined_math_ops_hash
    #"math_op_1",
    #"math_op_2",
    #"math_op_3",
    #"math_op_4",
    #"math_op_5",
    #"math_op_6",
    #"math_op_7",
    #"math_op_8",
    #"math_op_9",
    #"math_op_10",
    #"math_op_11",
    #"math_op_12",
    #"math_op_13",
    #"math_op_14",
    #"math_op_15",
    #"math_op_16",
    #"math_op_17",
    #"math_op_18",
    #"math_op_19",
    #"math_op_20",
    #"math_op_21",
    #"math_op_22",
    #"math_op_23",  # ↑ all 24 → combined_math_ops_hash
    "combined_math_ops_hash",
    "fonts_fpjs_allowlisted",
    "fonts_fpjs_nonallowlisted",
    "font_font_name_list_emoji_modified",
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
    "webgl_vendor",
    "webgl2_vendor",
    "webgl_vendor_raw",
    "webgl2_vendor_raw",
    "webgl_renderer",
    "webgl2_renderer",
    "webgl_params_SHADING_LANGUAGE_VERSION",
    "webgl2_params_SHADING_LANGUAGE_VERSION",
    "webgl_precision_fragment",
    "webgl2_precision_fragment",
    "webgl_precision_vertex",
    "webgl2_precision_vertex",
    "webgl2_params_ALIASED_LINE_WIDTH_RANGE",
    "webgl2_params_ALIASED_POINT_SIZE_RANGE",
    "webgl2_params_MAX_3D_TEXTURE_SIZE",
    "webgl2_params_MAX_ARRAY_TEXTURE_LAYERS",
    "webgl2_params_MAX_CLIENT_WAIT_TIMEOUT_WEBGL",
    "webgl2_params_MAX_COLOR_ATTACHMENTS",
    "webgl2_params_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_COMBINED_TEXTURE_IMAGE_UNITS",
    "webgl2_params_MAX_COMBINED_UNIFORM_BLOCKS",
    "webgl2_params_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_CUBE_MAP_TEXTURE_SIZE",
    "webgl2_params_MAX_DRAW_BUFFERS",
    "webgl2_params_MAX_ELEMENTS_INDICES",
    "webgl2_params_MAX_ELEMENTS_VERTICES",
    "webgl2_params_MAX_ELEMENT_INDEX",
    "webgl2_params_MAX_FRAGMENT_INPUT_COMPONENTS",
    "webgl2_params_MAX_FRAGMENT_UNIFORM_BLOCKS",
    "webgl2_params_MAX_FRAGMENT_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_FRAGMENT_UNIFORM_VECTORS",
    "webgl2_params_MAX_PROGRAM_TEXEL_OFFSET",
    "webgl2_params_MAX_RENDERBUFFER_SIZE",
    "webgl2_params_MAX_SAMPLES",
    "webgl2_params_MAX_SERVER_WAIT_TIMEOUT",
    "webgl2_params_MAX_TEXTURE_IMAGE_UNITS",
    "webgl2_params_MAX_TEXTURE_LOD_BIAS",
    "webgl2_params_MAX_TEXTURE_SIZE",
    "webgl2_params_MAX_TRANSFORM_FEEDBACK_INTERLEAVED_COMPONENTS",
    "webgl2_params_MAX_TRANSFORM_FEEDBACK_SEPARATE_ATTRIBS",
    "webgl2_params_MAX_TRANSFORM_FEEDBACK_SEPARATE_COMPONENTS",
    "webgl2_params_MAX_UNIFORM_BLOCK_SIZE",
    "webgl2_params_MAX_UNIFORM_BUFFER_BINDINGS",
    "webgl2_params_MAX_VARYING_COMPONENTS",
    "webgl2_params_MAX_VARYING_VECTORS",
    "webgl2_params_MAX_VERTEX_ATTRIBS",
    "webgl2_params_MAX_VERTEX_OUTPUT_COMPONENTS",
    "webgl2_params_MAX_VERTEX_TEXTURE_IMAGE_UNITS",
    "webgl2_params_MAX_VERTEX_UNIFORM_BLOCKS",
    "webgl2_params_MAX_VERTEX_UNIFORM_COMPONENTS",
    "webgl2_params_MAX_VERTEX_UNIFORM_VECTORS",
    "webgl2_params_MAX_VIEWPORT_DIMS",
    "webgl2_params_MIN_PROGRAM_TEXEL_OFFSET",
    #"webgl2_params_SHADING_LANGUAGE_VERSION",
    "webgl2_params_UNIFORM_BUFFER_OFFSET_ALIGNMENT",
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
    #"webgl_params_SHADING_LANGUAGE_VERSION",
    #"webgl_params_extensions",  # → combined_webgl_extensions_hash
    "combined_webgl_extensions_hash",
    #"webgl2_params_extensions",  # → combined_webgl2_extensions_hash
    "combined_webgl2_extensions_hash",
    "webgl_extensions",
    "webgl2_extensions"
])


"""
colorDepth
colorGamut
contrast
cookiesEnabled
cpuClass -> undefined
deviceMemory -> undefined
domBlockers -> see https://github.com/fingerprintjs/fingerprintjs/blob/39328fd6304b61acc423b592b0e7dd7505c87a6d/docs/content_blockers.md / https://github.com/fingerprintjs/fingerprintjs/blob/39328fd6304b61acc423b592b0e7dd7505c87a6d/src/sources/dom_blockers.ts
forcedColors
hardwareConcurrency
hdr
indexedDB -> constant
invertedColors
Languages
localStorage -> constant
Monochrome
openDatabase -> constant
osCpu
pdfViewerEnabled
Platform
reducedMotion
screenFrame
screenResolution # width/height - availWidth/Height
sessionStorage -> constant
Timezone
​​touchSupport
Vendor -> constant
Privateclickmeasurement-> constant
oscpu
Canvas - Extracts 4 canvases, the first 2 have to be the same, the 2nd 2 have to be the same
Audio context - Method: dynamics compressor, generates ID (should be able to find code online)
Font
    Emoji
       "emoji": {
          "value": {
            "bottom": 28,
            "font": "serif",
            "height": 16,
            "left": 8,
            "right": 1288,
            "top": 12,
            "width": 1280,
            "x": 8,
            "y": 12
          }
    fontPreferences
       "fontPreferences": {
          "value": {
            "apple": 147.5833282470703,
            "default": 147.5833282470703,
            "min": 9.23333740234375,
            "mono": 133.1666717529297,
            "sans": 144.01666259765625,
            "serif": 147.5833282470703,
            "system": 146
          }

Math - One hashed value
MathML
        "mathML": {
          "value": {
            "bottom": 29,
            "font": "serif",
            "height": 16,
            "left": 8,
            "right": 301.8833312988281,
            "top": 13,
            "width": 293.8833312988281,
            "x": 8,
            "y": 13
          }
        },
Plugins -> constant
webGlBasics – Plaintext
    "value": {
      "renderer": "Apple M1, or similar", # got it
      "rendererUnmasked": "Intel(R) Iris(TM) Plus Graphics 655", -> Same as renderer for us
      "shadingLanguageVersion": "WebGL GLSL ES 1.0", # got it
      "vendor": "Mozilla", # got it
      "vendorUnmasked": "", # got it
      "version": "WebGL 1.0" # got it
    }
webGlExtensions - hashed
    "webGlExtensions": {
      "value": {
        "contextAttributes": "6b1ed336830d2bc96442a9d76373252a", # In FF I'm pretty sure these will all be the same
        "extensionParameters": "6d09abc5995384aa6fbd8d146b6125b9",
        "extensions": "d2cb9ee7035d15213ba778483268b89c",
        "parameters": "d3ce664cee84aa22143f52c6a7597a2f", # got it, the whole damn list of parameters
        "shaderPrecisions": "f223dfbcd580cf142da156d93790eb83" # got it
      }

"""

###############################################################################
###############################################################################
###############################################################################
###############################################################################

FPSET_FINGERPRINTJS_V2 = set([
    # === Canvas Rendered Images (s17, s76) ===
    # Canvas text hash: "Cwm fjordbank gly" + emoji U+1F603 in Times New Roman + Arial with fillRect overlay
    # Canvas geometry hash: colored arcs with globalCompositeOperation "multiply" and evenodd fill
    "canvas_canvasdata12_fingerprintjs1",
    "canvas_canvasdata13_fingerprintjs2",
    "canvas_canvasdata11_webgl",
    # === WebGL (s74, s75, s76 — s76 rendered image listed above in Canvas) ===
    # gl.getParameter(VERSION, VENDOR, RENDERER, SHADING_LANGUAGE_VERSION)
    # WEBGL_debug_renderer_info unmasked vendor/renderer
    "webgl_vendor",
    #"webgl2_vendor",
    "webgl_vendor_raw",
    #"webgl2_vendor_raw",
    "webgl_renderer",
    #"webgl2_renderer",
    # Shader precisions for all FRAGMENT/VERTEX + FLOAT/INT combos - checked
    "webgl_precision_fragment",
    #"webgl2_precision_fragment",
    "webgl_precision_vertex",
    #"webgl2_precision_vertex",
    # WebGL Extensions - all extensions wind up in the fingerprint - ones they don't know about
    #    wind up in an unsupportedExtensions list
    "webgl_extensions",
    # "webgl2_extensions" - Fingerprint JS Pro does not do this for webGL 2
    # WebGL Parameters - checked
    # While we break the values out into individual metrics, for fingerprint calculations, we can just use the long string
    #"webgl_params",  # → combined_webgl1_params_hash
    "combined_webgl1_params_hash",
    # "webgl2_params", - Fingerprint JS Pro does not do this for webGL 2
    # WebGL Extension Parameters - checked
    #"webgl_params_extensions",  # → combined_webgl_extensions_hash
    "combined_webgl_extensions_hash",
    # "webgl2_params_extensions", - Fingerprint JS Pro does not do this for webGL 2
    # === WebGPU (exp_s1016, s210 — experimental: adapter info + 31 limits + features) - checked
    # navigator.gpu.requestAdapter() → GPUAdapterInfo + GPUSupportedLimits
    # GPUAdapterInfo.description/device/vendor/architecture return empty strings in Firefox (zero entropy)
    # Similarly the navigator.gpu.wgslLanguageFeatures is a compile time constant
    "wgpu_is_fallback_adapter",
    "wgpu_missing_features",
    #"wgpu_maxtexturedimension1d",        # ↓ all 31 limits → combined_wgpu_hash
    #"wgpu_maxtexturedimension2d",
    #"wgpu_maxtexturedimension3d",
    #"wgpu_maxtexturearraylayers",
    #"wgpu_maxbindgroups",
    #"wgpu_maxbindgroupsplusvertexbuffers",
    #"wgpu_maxbindingsperbindgroup",
    #"wgpu_maxdynamicuniformbuffersperpipelinelayout",
    #"wgpu_maxdynamicstoragebuffersperpipelinelayout",
    #"wgpu_maxsampledtexturespershaderstage",
    #"wgpu_maxsamplerspershaderstage",
    #"wgpu_maxstoragebufferspershaderstage",
    #"wgpu_maxstoragetexturespershaderstage",
    #"wgpu_maxuniformbufferspershaderstage",
    #"wgpu_maxuniformbufferbindingsize",
    #"wgpu_maxstoragebufferbindingsize",
    #"wgpu_minuniformbufferoffsetalignment",
    #"wgpu_minstoragebufferoffsetalignment",
    #"wgpu_maxvertexbuffers",
    #"wgpu_maxbuffersize",
    #"wgpu_maxvertexattributes",
    #"wgpu_maxvertexbufferarraystride",
    #"wgpu_maxinterstageshadervariables",
    #"wgpu_maxcolorattachments",
    #"wgpu_maxcolorattachmentbytespersample",
    #"wgpu_maxcomputeworkgroupstoragesize",
    #"wgpu_maxcomputeinvocationsperworkgroup",
    #"wgpu_maxcomputeworkgroupsizex",
    #"wgpu_maxcomputeworkgroupsizey",
    #"wgpu_maxcomputeworkgroupsizez",
    #"wgpu_maxcomputeworkgroupsperdimension",  # ↑ all 31 limits → combined_wgpu_hash
    "combined_wgpu_hash",
    # === Audio (s21: OfflineAudioContext oscillator fingerprint) ===
    # Triangle oscillator 10kHz → DynamicsCompressor → sum of samples 4500+ from 5000 at 44.1kHz
    # This metric is the audio fingerprint calculation from FingerprintJS
    "audio_fingerprint",
    # baseLatency is constant in Firefox
    # === Speech synthesis (s52, s158, s160: speechSynthesis.getVoices()) ===
    # They collect a MurmurHash3-x64-128 hash of the voices list.
    "voices_sha1",
    # === CSS system colors (s87: ~30 system color keywords via getComputedStyle) ===
    # AccentColor, AccentColorText, ActiveText, ButtonFace, Canvas, CanvasText,
    # Field, FieldText, GrayText, Highlight, HighlightText, LinkText, Mark, MarkText, etc.
    #"font_css_system_colors",  # → combined_css_colors_hash
    "combined_css_colors_hash",
    # === Fonts (s20, s51, s206, s207) ===
    # Probes ~50 fonts against monospace/sans-serif/serif baselines using span width/height
    # TODO
    "fonts_fpjs_allowlisted",
    "fonts_fpjs_nonallowlisted",
    #"font_css_system_fonts",  # → combined_css_fonts_hash
    "combined_css_fonts_hash",
    # === Screen & display (s5, s6, s3, s36, s57, s84, s142, s150, s152, s204) ===
    # screen.width x screen.height (sorted descending)
    "screen_primary_resolution",
    # screen.availTop/Left/Width/Height (taskbar/dock offsets)
    "screen_primary_avail",
    "screen_web_avail_top",
    "screen_web_avail_left",
    # screen.colorDepth
    "screen_primary_color_depth",
    # window.devicePixelRatio
    "screen_web_pixel_ratio",
    # outerWidth/Height, innerWidth/Height
    "screen_web_inner",
    "screen_web_outer",
    # === CSS media queries (s44, s37, s41, s38, s39, s42, s43, s40, s91, s139) ===
    # prefers-color-scheme (dark/light)
    "screen_color_scheme",
    # prefers-contrast (high/more/low/less/forced/no-preference)
    "screen_prefers_contrast",
    # inverted-colors (inverted/none)
    "screen_inverted_colors",
    # monochrome (bits 0-100)
    "screen_monochrome",
    # prefers-reduced-motion (reduce/no-preference)
    "screen_prefers_reduced_motion",
    # prefers-reduced-transparency (reduce/no-preference)
    "screen_prefers_reduced_transparency",
    # dynamic-range (high/standard) — HDR detection
    "screen_primary_video_dynamic_range",
    # color-gamut (srgb/p3/rec2020) - constant in Firefox
    # forced-colors (active/none)
    "prefs_use_document_colors",
    # CSS.supports("backdrop-filter","blur(2px)") - near-constant (false on GPU-blocklisted clients, covered by existing GPU metrics)
    # === Navigator properties (s101, s1, s15, s7, s4, s2, s82, s83, s80, s19, s27, s102, s103, s104, s123, s14, s153) ===
    # navigator.userAgent
    "user_agent",
    # navigator.oscpu
    "hw_oscpu",
    # navigator.platform
    "platform",
    # navigator.hardwareConcurrency
    "hw_processor_count",
    # navigator.language + navigator.languages
    "locale_accept_language",
    # navigator.maxTouchPoints 
    "hw_max_touch_points",
    # navigator.pdfViewerEnabled
    "prefs_pdf_viewer",
    # navigator.cookieEnabled → prefs_cookiesenabled (prefs_cookiebehavior != 2)
    "prefs_cookiesenabled",
    # navigator.appVersion → NO MATCH (constant "5.0 (…)" in Firefox)
    # navigator.vendor → NO MATCH (constant "" in Firefox)
    # navigator.productSub → NO MATCH (constant "20100101" in Firefox)
    # navigator.deviceMemory → NO MATCH (Chrome-only, undefined in Firefox)
    # navigator.cpuClass → NO MATCH (IE-only, undefined in Firefox)
    # navigator.connection.rtt → NO MATCH (Chrome-only Network Information API)
    # navigator.userAgentData → NO MATCH (Chrome-only UA Client Hints)
    # === Math precision (s46: 20+ transcendental functions) ===
    # acos, acosh, asin, asinh, atanh, atan, sin, sinh, cos, cosh, tan, tanh, exp, expm1, log1p, pow
    # plus polyfill variants (acoshPf, asinhPf, atanhPf, sinhPf, coshPf, tanhPf, expm1Pf, log1pPf)
    #"math_op_0",   # ↓ all 24 → combined_math_ops_hash
    #"math_op_1",
    #"math_op_2",
    #"math_op_3",
    #"math_op_4",
    #"math_op_5",
    #"math_op_6",
    #"math_op_7",
    #"math_op_8",
    #"math_op_9",
    #"math_op_10",
    #"math_op_11",
    #"math_op_12",
    #"math_op_13",
    #"math_op_14",
    #"math_op_15",
    #"math_op_16",
    #"math_op_17",
    #"math_op_18",
    #"math_op_19",
    #"math_op_20",
    #"math_op_21",
    #"math_op_22",
    #"math_op_23",  # ↑ all 24 → combined_math_ops_hash
    "combined_math_ops_hash",
    # === Timezone (s9, s45, s200, s202: Intl.DateTimeFormat timezone + locale) ===
    # Intl.DateTimeFormat().resolvedOptions().timeZone, fallback: UTC±N from getTimezoneOffset()
    "intl_timezone_web",
    "intl_timezone_offset_web",
    # Intl.DateTimeFormat().resolvedOptions().locale
    "intl_intl_locale",
    # === MathML / text rendering (s92: MathML bounding box, s93: Unicode text) ===
    # MathML renders product operator with Greek letter sub/superscripts, measures bounding box
    #"mathml_1",  # ↓ all 10 → combined_mathml_hash
    #"mathml_2",
    #"mathml_3",
    #"mathml_4",
    #"mathml_5",
    #"mathml_6",
    #"mathml_7",
    #"mathml_8",
    #"mathml_9",
    #"mathml_10",  # ↑ all 10 → combined_mathml_hash
    "combined_mathml_hash",
    # === Media capabilities / DRM (s209/s211: MediaCapabilities.decodingInfo()) ===
    # supported/smooth/powerEfficient flags across codec+resolution combos
    #"media_capabilities",  # raw blob field — always "None" (data is in the 4 split fields below)
    #"media_capabilities_unsupported",  # ↓ all 4 → combined_media_capabilities_hash
    #"media_capabilities_not_smooth",
    #"media_capabilities_not_efficient",
    #"media_h264",  # ↑ all 4 → combined_media_capabilities_hash
    "combined_media_capabilities_hash",
    # requestMediaKeySystemAccess() → DRM system probing
    "prefs_eme_enabled",
    # === WebRTC SDP fingerprinting (s97: RTCPeerConnection.createOffer() → codec list) ===
    "sdp_codec_list",
    # === Other
    "webauthn_capabilities",
    "storage_quota",
])

FPSET_FINGERPRINTJS_V2_INOUT = (FPSET_FINGERPRINTJS_V2 - {"screen_web_inner", "screen_web_outer"}) | {
    "screen_web_outer_inner_diff",
}

"""
FingerprintJS Pro v3.12.6 — Web APIs queried
Source: deobfuscated script from https://fp.fancysteak.icu/ + Firefox Profiler runtime trace
Reference: rfp_fingerprinters_tracking/fingerprintpro/analysis/web-api-inventory.md
Analysis: rfp_fingerprinters_tracking/fingerprintpro/

~139 distinct signals organized into 3 modules (id, bd, ex) with 3 stages each.
Results encrypted and POSTed to https://api.fpjs.io/.

=== Signals with fingerprinting entropy — mapped to metrics ===

Canvas 2D (s17):
  document.createElement("canvas").getContext("2d")
  ctx.fillText("Cwm fjordbank gly" + emoji, ...) in Times New Roman + Arial
  ctx.fillRect() overlay, ctx.arc() with globalCompositeOperation "multiply"
  ctx.isPointInPath("evenodd") winding rule test
  canvas.toDataURL() → two separate hashes (text + geometry)

WebGL (s74, s75, s76):
  gl.getParameter(VERSION, VENDOR, RENDERER, SHADING_LANGUAGE_VERSION)
  WEBGL_debug_renderer_info → unmasked vendor/renderer
  ~300 GL constant values via getParameter()
  All context attributes
  All shader precisions (FRAGMENT/VERTEX × FLOAT/INT combos)
  All supported/unsupported extensions
  All extension parameter values
  WebGL rendered image hash (s76): shaders render rotating triangle, toDataURL() → canvas_canvasdata11_webgl

WebGPU (exp_s1016, s210 — experimental):
  navigator.gpu.requestAdapter()
  GPUAdapterInfo.description/device/vendor/architecture → empty strings in Firefox (zero entropy)
  GPUAdapter.features → wgpu_missing_features (complement)
  All 31 GPUSupportedLimits values     → wgpu_maxtexturedimension1d through wgpu_maxcomputeworkgroupsperdimension
  GPUAdapter.isFallbackAdapter         → wgpu_is_fallback_adapter

Audio (s21):
  OfflineAudioContext(1, 5000, 44100)
  OscillatorNode(triangle, 10000Hz) → DynamicsCompressorNode(threshold:-50,
    knee:40, ratio:12, attack:0, release:0.25)
  Sum of |channelData[4500:]|

Speech synthesis (s52, s158, s160):
  speechSynthesis.getVoices() → 3 hash variants (name, lang, localService, default)

Fonts (s20, s51, s206, s207):
  50+ fonts probed via DOM width comparison against monospace/sans-serif/serif baselines
  Test string "mmMwWLliI0O&1" at 48px in iframe
  getComputedStyle(radioInput).fontFamily (Firefox-specific)
  new FontFace("font", "local('Arial')").load() success/failure
  measureText() widths per generic font family

Screen & display (s5, s6, s3, s36, s57, s84, s142, s150, s152, s204):
  screen.width, screen.height              → screen_primary_resolution
  screen.availTop/Left/Width/Height        → screen_primary_avail
  screen.colorDepth                        → screen_primary_color_depth
  window.devicePixelRatio                  → screen_web_pixel_ratio
  window.outerWidth/Height                 → screen_web_outer
  window.innerWidth/Height                 → screen_web_inner
  matchMedia("(-webkit-min-device-pixel-ratio: 2)") → NO MATCH (derivable from pixel_ratio)
  div.5px border offsetHeight              → NO MATCH (CSS half-pixel rendering)
  overflow:scroll div offsetWidth===clientWidth → NO MATCH (scrollbar detection, partially: prefs_overlay_scrollbars)

CSS media queries (s44, s37, s41, s38, s39, s42, s43, s40, s91, s139):
  prefers-color-scheme                     → screen_color_scheme
  prefers-contrast                         → screen_prefers_contrast
  inverted-colors                          → screen_inverted_colors
  monochrome                               → screen_monochrome
  prefers-reduced-motion                   → screen_prefers_reduced_motion
  prefers-reduced-transparency             → screen_prefers_reduced_transparency
  dynamic-range                            → screen_primary_video_dynamic_range
  color-gamut                              → NO MATCH (srgb/p3/rec2020 not collected)
  forced-colors                            → prefs_use_document_colors
  CSS.supports("backdrop-filter","blur(2px)") → NO MATCH

CSS system colors (s87):
  ~30 system color keywords via getComputedStyle()
  AccentColor, AccentColorText, Canvas, CanvasText, Highlight, HighlightText,
  SelectedItem, SelectedItemText, Field, FieldText, GrayText, LinkText, etc.
  → font_css_system_colors (composite hash of all ~30 colors)

Navigator properties (s101, s1, s15, s7, s4, s2, s82, s83, s80, s19, s27, s102, s103, s104, s123, s14, s153):
  navigator.userAgent                      → user_agent
  navigator.oscpu                          → hw_oscpu
  navigator.platform                       → platform
  navigator.hardwareConcurrency            → hw_processor_count
  navigator.language + navigator.languages → locale_accept_language
  navigator.maxTouchPoints + TouchEvent    → hw_max_touch_points
  navigator.pdfViewerEnabled               → prefs_pdf_viewer
  navigator.cookieEnabled                  → prefs_cookiesenabled (prefs_cookiebehavior != 2)
  navigator.deviceMemory                   → NO MATCH (Chrome-only, undefined in Firefox)
  navigator.cpuClass                       → NO MATCH (IE-only)
  navigator.vendor                         → NO MATCH (constant "" in Firefox)
  navigator.productSub                     → NO MATCH (constant "20100101")
  navigator.appVersion                     → NO MATCH (constant "5.0 (…)")
  navigator.connection.rtt                 → NO MATCH (Chrome-only)
  navigator.userAgentData                  → NO MATCH (Chrome-only)
  navigator.onLine                         → NO MATCH (ephemeral)

Math precision (s46):
  20+ transcendental functions: acos(0.123…), acosh(1e308), asin(0.123…),
  asinh(1), atanh(0.5), atan(0.5), sin(-1e300), sinh(1), cos(10.000000000123),
  cosh(1), tan(-1e300), tanh(1), exp(1), expm1(1), log1p(10), pow(PI,-100)
  Plus polyfill variants (acoshPf, asinhPf, atanhPf, etc.)

Timezone (s9, s45, s200, s202):
  Intl.DateTimeFormat().resolvedOptions().timeZone → intl_timezone_web
  Date.getTimezoneOffset()                → intl_timezone_offset_web
  Intl.DateTimeFormat().resolvedOptions().locale → intl_intl_locale
  performance.timeOrigin                   → NO MATCH (ephemeral)
  Date.now() + timezone-adjusted           → NO MATCH (ephemeral)

MathML / text rendering (s92, s93):
  MathML product operator with Greek sub/superscripts → getBoundingClientRect()
  Unicode text sequences → getBoundingClientRect()

Cookie support (s32):
  document.cookie write/read/delete with SameSite=Strict

=== Signals with NO fingerprinting entropy within Firefox ===

Browser/engine detection (s59-s65, s201, s28, s156, s30, s66):
  IE, Edge, Chrome, Safari, Firefox, Mobile detection via feature probing
  window.{chrome, safari, __firefox__, yandex, etc.} global presence
  Object.getOwnPropertyNames(window) hash against ~30 property names
  HTMLAnchorElement.attributionSourceId (s30, s66): Attribution Reporting API presence
    → Chrome/Safari only, undefined in Firefox
  → N/A: always identifies as "Firefox" within Firefox population

Prototype/native function checks (s24, s148, s50, s119, s120, s81, s130, s132, s133, s144, s151, s155, s159, s163, s205):
  eval.toString().length (always 37 in Firefox)
  Function.prototype.bind.toString()
  Error.stack format
  Error.prototype.toSource()
  Float32Array NaN byte representation
  typeof SourceBuffer/SourceBufferList
  window.close.toString()
  window.external.toString() (s133) → "[object External]" in Firefox
  SharedArrayBuffer availability
  new URL("C:/").protocol parsing
  Object.getOwnPropertyDescriptor(document, "createElement") (s151) → tampering detection
  Function/Object deletion resilience (s159) → temporarily deletes window.Function/Object
  Iframe Error.stack format (s163) → Chrome/Safari only, null in Firefox
  → All constant within a Firefox version

Bot/automation detection (s72, s22, s146, s149, s154, s157, s165, s167):
  navigator.webdriver
  Selenium/PhantomJS/Puppeteer/CefSharp/wdio/Electron global detection
  window.process (Node.js/Electron)
  Event.isTrusted
  DevTools variable detection (s146) → checks for injected objectToInspect
  WebView detection (s154) → {wv, wvp, pr, ck, pt, fp} flags for in-app browsers
  Encrypted property name table checks
  → N/A: anti-bot, not fingerprinting

Ad blocker/privacy detection (s89, s33, s86, s106, s95, s68):
  ~200 CSS selectors from ~40 filter lists (EasyList, AdGuard, uBlock, etc.)
  Brave canvas IDAT chunk analysis
  Private/incognito mode detection
  Notification permission mismatch
  → NO MATCH: not collected

Plugins/MIME types (s16, s117, s135, s136, s118):
  navigator.plugins full enumeration
  navigator.plugins.length, navigator.mimeTypes.length
  MimeTypeArray/PluginArray prototype chain validation
  → NO MATCH: vestigial, near-zero entropy in modern browsers

Storage availability (s10, s11, s12, s13, s85):
  !!sessionStorage, !!localStorage, !!indexedDB, !!openDatabase
  IDBFactory WebKit behavior check (s85) → empty string in Firefox
  → NO MATCH: universal in Firefox (constant)

Frame/origin context (s69, s71, s98, s99):
  window.parent chain traversal
  window.origin, location.ancestorOrigins
  "serviceWorker" in Navigator.prototype
  window.isSecureContext
  → NO MATCH: per-page context, not per-user

TLS fingerprinting (s70, s56):
  Server-side TLS handshake capture via remote endpoint (s70)
  Result returned to client as s56 (HTTP status + hash)
  → NO MATCH: requires cooperating server, not client-side

Audio baseLatency (s96):
  AudioContext.baseLatency → always 0.0 in Firefox (hardcoded)
  → NO MATCH: zero entropy within Firefox

User-Agent Client Hints (s58):
  navigator.userAgentData.getHighEntropyValues() → brands, platform, architecture, etc.
  → NO MATCH: Chrome/Chromium-only, undefined in Firefox

Navigator API surface (s145, s166, s131, s49):
  Navigator prototype method/property enumeration
  document.documentElement.getAttributeNames()
  performance.now() timer resolution
  → NO MATCH: constant within Firefox version

CSS precision (s203):
  CSS calc() rounding precision
  → NO MATCH

File metadata probing (s79):
  Encrypted string table decrypts to file path(s); creates File/Blob objects
  via window constructor, extracts metadata property (likely lastModified),
  CRC32-hashes the result to produce the numeric `l` value
  Value: [{"n": "default.ini", "l": <CRC32 hash>}] — hash varies between runs
  Status -3 (degraded) in both traces; `l` values differ (2332499772 vs 1344129360)
  → NO MATCH (persistent identifier based on file metadata; potentially high entropy)

WebRTC SDP fingerprinting (s97):
  RTCPeerConnection.createOffer() → SDP codec list, RTP extensions, ICE candidates
  → sdp_codec_list

Media capabilities / DRM (s209/s211):
  MediaCapabilities.decodingInfo() → supported/smooth/powerEfficient
  → media_capabilities, media_capabilities_unsupported, media_capabilities_not_smooth,
    media_capabilities_not_efficient, media_h264
  requestMediaKeySystemAccess() → DRM system probing
  → prefs_eme_enabled (media.eme.enabled pref — whether DRM is allowed)

WebAuthn client capabilities (exp_s1014):
  PublicKeyCredential.getClientCapabilities() → dictionary of ~17 boolean capabilities
  (conditionalCreate, conditionalGet, extension:appid, extension:credProps,
   hybridTransport, passkeyPlatformAuthenticator, userVerifyingPlatformAuthenticator, etc.)
  Null in data.2.json but populated in profiler trace (Firefox 149)
  Deobs: encrypted check via `Yu` string table → resolves to getClientCapabilities()
  → webauthn_capabilities

StorageManager quota (s29):
  navigator.storage.estimate() → quota value (10737418240 = 10 GiB default in Firefox)
  Encrypted Gi call on navigator (hash dispatch); null in data.2.json,
  populated in profiler trace — different browser sessions
  → storage_quota

Persistent identifiers (s94, s55, s48):
  crypto.randomUUID() → stored/read via cookies + localStorage (s94, s55)
  Math.random() PRNG entropy sampling → array of 6 hash integers (s48)
  → N/A: tracking IDs, not device fingerprints

Custom component passthrough (s67):
  Not a fingerprinting signal — FPJS API `customComponent` option
  Deobs: `s67: customComponent ? {s:0, v:customComponent} : {s:-1, v:null}`
  Returns null when no custom component provided by the calling application
  → N/A: developer extension point, not browser-derived

Navigator property descriptor check (s162):
  Gi(navigator, 2698072953) → resolves a navigator property by CRC32 hash
  Result passed through aa() which checks property descriptors (writable, configurable)
  Returns false (boolean) in Firefox — property exists but descriptor check fails
  Exact property name unknown (hidden behind CRC32 hash 2698072953)
  → N/A: constant false within Firefox

WebKit file system probe (s23):
  Gi(window, 2796484463) → resolves a window property (likely webkitRequestFileSystem)
  4-argument callback pattern: property(0, 1, successCallback, failureCallback)
  Guards: skipped on modern Chrome (Chromium 120+); undefined in Firefox → {s:-1, v:null}
  → N/A: WebKit/Blink-only, does not exist in Firefox

Experimental signals (exp_s1013, exp_s1015):
  exp_s1013: consistently inactive/unavailable (status -4/-1 across both traces)

  exp_s1015: dictionary-compressed WebGL1 full parameter dump
    Source: function Wu (deobs line 6714), registered as stage3.exp_s1015 in "ex" module
    Encoding: JSON → UTF-8 → CompressionStream("deflate-raw") → base64 (1468 chars, ~15:1 ratio)
    Size guard: returns {s:-4, v:null} if base64 > 4096 chars

    Collection (function m, line 6562): enumerates WebGLRenderingContext prototype via
    Object.getOwnPropertyNames — NO hard-coded GL constant names or values in source.
    Calls getParameter() for each queryable enum, getSupportedExtensions(), getExtension()
    for each extension, getShaderPrecisionFormat() for all shader type × precision combos.
    Skips WEBGL_debug_renderer_info on Firefox, WEBGL_polygon_mode on Chrome.

    Dictionary T (line 6559): 609 entries mapping known WebGL strings → integer indices.
    Function _() replaces each string with its index; strings not in dictionary (e.g.
    GPU-specific renderer names) are kept as inline literals.

    Wrapper J (line 6472) splits parameters into two forms:
      - name-only: "ACTIVE_TEXTURE(34016)=null" — fingerprints WebGL API surface
      - name+value: "ACTIVE_TEXTURE=34016=33984" — fingerprints hardware

    Decoded structure (8-element JSON array):
      [0] contextAttributes (8): getContextAttributes() → alpha, antialias, depth,
          failIfMajorPerformanceCaveat, powerPreference, premultipliedAlpha, etc.
      [1] parameters (296): GL constant names/enums, queryable values replaced with null
          → fingerprints WebGL implementation (which constants exist, which are queryable)
      [2] parameters2 (296): same constants WITH getParameter() results
          → fingerprints hardware (83 of 296 differ from [1])
          Inline literals for non-dictionary values:
            RENDERER=7937=Radeon R9 200 Series, or similar
            ALIASED_POINT_SIZE_RANGE=33901=1,8191
            SUBPIXEL_BITS=3408=8
      [3] shaderPrecisions (12): FRAGMENT/VERTEX × LOW/MEDIUM/HIGH × FLOAT/INT
          → Firefox-specific: INT precision 24,24,0 (Chrome: 31,30,0)
      [4] extensions (27): supported extension names
          → Firefox-specific: WEBGL_provoking_vertex
      [5] extensionParameters (71): extension constants, name-only form
      [6] extensionParameters2 (71): extension constants with getParameter() values
          → 7 queryable extension params (MAX_COLOR_ATTACHMENTS_WEBGL, etc.)
      [7] unsupportedExtensions (0): extensions getSupportedExtensions() listed but
          getExtension() failed

    Coverage mapping:
      [0]   → webgl_context_attributes
      [1-2] → webgl_params (subset), webgl_vendor, webgl_renderer
      [3]   → webgl_shader_precisions
      [4,7] → webgl_extensions, webgl_missing_extensions
      [5-6] → webgl_ext_params
    exp_s1015 is a superset — captures all ~296 GL + ~71 extension constants vs our selective read
"""

###############################################################################
###############################################################################
###############################################################################
###############################################################################

FPSET_SIGNIFYD = set([
    # === Canvas 2D (CreepJS module: 5 canvas renders + TextMetrics) ===
    # 5 canvases: data, paint, paintCpu, text, emoji — each with distinct drawing operations
    # textMetricsSystemSum: sum of all 7 TextMetrics properties across 48-font family list
    # Actively detects RFP via bounding box fractional part check (liedTextMetrics)
    
    # Data and Paint canvas:
    #Uses the Px() drawing function (line 4134) with a seeded PRNG (seed=500, offset=2001000001, multiplier=15000). Over 10 rounds, draws:
    #  - Radial gradients (createRadialGradient) with random color stops
    #  - Arcs (arc)
    #  - Bezier curves (bezierCurveTo)
    #  - Quadratic curves (quadraticCurveTo)
    #  - Ellipses (ellipse)
    #  - Stroke text (strokeText) using the system CSS font (Paint canvas omits text)
    "canvas_canvasdata01",
    "canvas_canvasdata02",
    "canvas_canvasdata07",
    "canvas_canvasdata08",
    "canvas_canvasdata13_fingerprintjs2",
    # Asks for the paint canvas via software rendering
    "canvassoftware_canvasdata01",
    "canvassoftware_canvasdata02",
    "canvassoftware_canvasdata13_fingerprintjs2",
    # System Font: covered below
    # "A" Rendering is variant f
    # "👾" Rendering is variant g
    
    # === WebGL (vendor/renderer only — NO full parameter dump) ===
    # Uses WebGL1 only (getContext("webgl")), with OffscreenCanvas when available
    # WEBGL_debug_renderer_info → UNMASKED_VENDOR_WEBGL + UNMASKED_RENDERER_WEBGL
    # Surprisingly, does not collect WebGL Extension/Parameter data
    # Unlike FPJS Pro, does NOT read ~80 GL constants, shader precisions, or extensions
    "webgl_vendor",
    "webgl_vendor_raw",
    "webgl_renderer",
    # === WebGPU (Signifyd addition: 14 limits + features) ===
    # navigator.gpu.requestAdapter() → GPUAdapter
    # GPUAdapterInfo: architecture/device/description/vendor (empty strings in Firefox, zero entropy)
    # GPUAdapter.features → sorted feature array
    # 14 of 31 GPUSupportedLimits values read (not the full set)
    "wgpu_missing_features",
    "wgpu_is_fallback_adapter",
    "wgpu_maxtexturedimension1d",
    "wgpu_maxtexturedimension2d",
    "wgpu_maxtexturedimension3d",
    "wgpu_maxbindgroups",
    "wgpu_maxdynamicuniformbuffersperpipelinelayout",
    "wgpu_maxdynamicstoragebuffersperpipelinelayout",
    "wgpu_maxbuffersize",
    "wgpu_maxcolorattachments",
    "wgpu_maxcomputeworkgroupstoragesize",
    "wgpu_maxcomputeinvocationsperworkgroup",
    "wgpu_maxstoragebufferspershaderstage",
    "wgpu_maxuniformbufferbindingsize",
    "wgpu_maxvertexbuffers",
    "wgpu_maxvertexattributes",
    # === Audio (CreepJS module: OfflineAudioContext oscillator fingerprint) ===
    # Same technique as FPJS: Triangle oscillator 10kHz → DynamicsCompressor → sum of samples
    "audio_compressor_gain_reduction",
    "audio_fingerprint2",
    "audio_unique_samples",
    "audio_float_frequency_sum",
    "audio_float_time_domain_sum",
    # AudioWorklet data is for detecting injected noise
    # === Speech synthesis (CreepJS module: speechSynthesis.getVoices()) ===
    # Voice data is NOT included in the server payload — used only for lie detection
    # (API tampering check). Not included: voices are not part of the fingerprint.
    # === SVG Rendering
    "svg_bbox",
    "svg_computed_text_length",
    "svg_emoji_set",
    "svg_extent_of_char",
    "svg_substring_length",
    # fonts_variant_i - listed below
    # === Fonts (CreepJS module: TextMetrics + CSS system fonts) ===
    # Font fingerprinting via canvas measureText() on 48-font list + CSS system font resolution
    # FontFace API is only in lie detection, NOT used for font enumeration
    "fonts_variant_f_allowlisted",
    "fonts_variant_f_nonallowlisted",
    "fonts_variant_g_allowlisted",
    "fonts_variant_g_nonallowlisted",
    "fonts_variant_h_allowlisted",
    "fonts_variant_h_nonallowlisted",
    "fonts_variant_i_allowlisted",
    "fonts_variant_i_nonallowlisted",
    #=== Client Rect information
    #"clientrects_element_gbcr_01",  # ↓ all 12 → combined_clientrects_element_gbcr_hash
    #"clientrects_element_gbcr_02",
    #"clientrects_element_gbcr_03",
    #"clientrects_element_gbcr_04",
    #"clientrects_element_gbcr_05",
    #"clientrects_element_gbcr_06",
    #"clientrects_element_gbcr_07",
    #"clientrects_element_gbcr_08",
    #"clientrects_element_gbcr_09",
    #"clientrects_element_gbcr_10",
    #"clientrects_element_gbcr_11",
    #"clientrects_element_gbcr_12",  # ↑ all 12 → combined_clientrects_element_gbcr_hash
    "combined_clientrects_element_gbcr_hash",
    #"clientrects_element_gcr_01",  # ↓ all 12 → combined_clientrects_element_gcr_hash
    #"clientrects_element_gcr_02",
    #"clientrects_element_gcr_03",
    #"clientrects_element_gcr_04",
    #"clientrects_element_gcr_05",
    #"clientrects_element_gcr_06",
    #"clientrects_element_gcr_07",
    #"clientrects_element_gcr_08",
    #"clientrects_element_gcr_09",
    #"clientrects_element_gcr_10",
    #"clientrects_element_gcr_11",
    #"clientrects_element_gcr_12",  # ↑ all 12 → combined_clientrects_element_gcr_hash
    "combined_clientrects_element_gcr_hash",
    #"clientrects_emoji_01",  # ↓ all 6 → combined_clientrects_emoji_hash
    #"clientrects_emoji_02",
    #"clientrects_emoji_03",
    #"clientrects_emoji_04",
    #"clientrects_emoji_05",
    #"clientrects_emoji_06",  # ↑ all 6 → combined_clientrects_emoji_hash
    "combined_clientrects_emoji_hash",
    "clientrects_emoji_font_family",
    "clientrects_ghost_dimensions",
    "clientrects_known_dimensions",
    #"clientrects_range_gbcr_01",  # ↓ all 12 → combined_clientrects_range_gbcr_hash
    #"clientrects_range_gbcr_02",
    #"clientrects_range_gbcr_03",
    #"clientrects_range_gbcr_04",
    #"clientrects_range_gbcr_05",
    #"clientrects_range_gbcr_06",
    #"clientrects_range_gbcr_07",
    #"clientrects_range_gbcr_08",
    #"clientrects_range_gbcr_09",
    #"clientrects_range_gbcr_10",
    #"clientrects_range_gbcr_11",
    #"clientrects_range_gbcr_12",  # ↑ all 12 → combined_clientrects_range_gbcr_hash
    "combined_clientrects_range_gbcr_hash",
    #"clientrects_range_gcr_01",  # ↓ all 12 → combined_clientrects_range_gcr_hash
    #"clientrects_range_gcr_02",
    #"clientrects_range_gcr_03",
    #"clientrects_range_gcr_04",
    #"clientrects_range_gcr_05",
    #"clientrects_range_gcr_06",
    #"clientrects_range_gcr_07",
    #"clientrects_range_gcr_08",
    #"clientrects_range_gcr_09",
    #"clientrects_range_gcr_10",
    #"clientrects_range_gcr_11",
    #"clientrects_range_gcr_12",  # ↑ all 12 → combined_clientrects_range_gcr_hash
    "combined_clientrects_range_gcr_hash",
    "clientrects_text_font_family",
    # === Screen & display ===
    # screen.width x screen.height
    "screen_primary_resolution",
    # screen.availWidth x screen.availHeight
    "screen_primary_avail",
    # screen.colorDepth
    "screen_primary_color_depth",
    # screen.pixelDepth
    "screen_primary_pixel_depth",
    # window.devicePixelRatio
    "screen_web_pixel_ratio",
    # window.innerWidth x window.innerHeight
    "screen_web_inner",
    # window.outerWidth/Height → NOT collected by Signifyd (unlike FPJS Pro and Akamai)
    # === CSS media queries (CreepJS module: matchMedia for 14 features) ===
    # prefers-color-scheme (dark/light)
    "screen_color_scheme",
    # prefers-reduced-motion (reduce/no-preference)
    "screen_prefers_reduced_motion",
    # prefers-contrast → NOT tested by Signifyd (not in its 14 matchMedia features)
    # inverted-colors
    "screen_inverted_colors",
    # monochrome (bits)
    "screen_monochrome",
    # dynamic-range (HDR) → NOT tested by Signifyd (not in its 14 matchMedia features)
    # color-gamut (srgb/p3/rec2020) → Constant in Firefox
    # forced-colors (active/none) 
    "prefs_use_document_colors",
    # any-hover / hover / any-pointer / pointer
    "hw_pointer_type",
    "hw_any_pointer_type",
    # device-aspect-ratio - we have the screen dimentions, this is determined from that
    # display-mode -> always browser
    # orientation 
    "screen_primary_orientation",
    # === CSS system colors (CreepJS module: computed style system colors) ===
    # getComputedStyle() for CSS system color keywords (AccentColor, Canvas, Highlight, etc.)
    #"font_css_system_colors",  # → combined_css_colors_hash
    "combined_css_colors_hash",
    #"font_css_system_fonts",  # → combined_css_fonts_hash
    "combined_css_fonts_hash",
    # === Navigator properties (main thread + Worker + SharedWorker contexts) ===
    # navigator.userAgent (independently collected in all 3 contexts for lie detection)
    "user_agent",
    # navigator.platform
    "platform",
    # navigator.oscpu
    "hw_oscpu",
    # navigator.hardwareConcurrency
    "hw_processor_count",
    # navigator.languages
    "locale_accept_language",
    # navigator.maxTouchPoints
    "hw_max_touch_points",
    # navigator.doNotTrack
    "prefs_general_donottrack_enabled",
    # navigator.globalPrivacyControl
    "prefs_general_globalprivacycontrol_enabled",
    # navigator.buildID (Firefox-specific build timestamp) - constant in Firefox
    # navigator.cookieEnabled → prefs_cookiesenabled (prefs_cookiebehavior != 2)
    "prefs_cookiesenabled",
    # navigator.pdfViewerEnabled → NOT collected by Signifyd (not in web-api-inventory)
    # === Math precision ===
    # CreepJS upstream has a "maths" module that computes 24 Math function precision values.
    # Signifyd's fork REMOVED this module entirely:
    #   - creepjs-signifyd-full-comparison.md lists only 12 modules; "maths" is not among them
    #   - web-api-inventory.md: Math functions appear only in lie detection (API tampering checks)
    #   - data.json payload: no "maths" section; only mathConstants strings for lie detection
    # Therefore no math_op_* metrics are included.
    #
    # === Storage ===
    # StorageManager.estimate() → storage quota (confirmed in profiler trace and data.json)
    "storage_quota",
    # === Timezone / Intl (CreepJS module: Intl API) ===
    # Intl.DateTimeFormat().resolvedOptions().timeZone
    "intl_timezone_web",
    "intl_timezone_offset_web",
    # Intl.DateTimeFormat().resolvedOptions().locale (+ other Intl constructors)
    "intl_intl_locale",
    # MathML rendering: NOT collected by Signifyd (no MathML code in lite.js,
    # unlike CreepJS which includes a MathML module)
])

"""
Signifyd lite.js — Web APIs queried
Source: deobfuscated lite.js (CreepJS fork from May 20, 2023 commit c17490f)
       + Firefox Profiler runtime trace (29MB, 493 unique page-originated Web APIs)
Reference: rfp_fingerprinters_tracking/signifyd/analysis/web-api-inventory.md
Analysis: rfp_fingerprinters_tracking/signifyd/

CreepJS fork (~75-85% of CreepJS functionality) with 6 Signifyd additions:
WebGPU adapter/14 limits, worker context fingerprinting, incognito detection,
in-app WebView detection, cookie monster, crypto key persistence.

=== Signals with fingerprinting entropy — mapped to metrics ===

Canvas 2D (CreepJS module — 5 renders + TextMetrics):
  5 canvases: data, paint, paintCpu (CPU-forced via shadow), text, emoji
  canvas.toDataURL() × 8 (renders + winding + emoji variants)
  ctx.measureText() → all 7 TextMetrics properties per font in 48-font list:
    width, actualBoundingBoxLeft/Right, actualBoundingBoxAscent/Descent,
    fontBoundingBoxAscent/Descent
  textMetricsSystemSum: sum scaled by 1e-5
  Pixel tamper detection: getImageData() → checks expected output
  RFP detection: flags "liedTextMetrics" if bounding box values have
    unexpected fractional parts (% 1 !== 0)

WebGL (vendor/renderer identity ONLY — NOT full parameter dump):
  getContext("webgl") — WebGL1 only, with OffscreenCanvas fallback
  WEBGL_debug_renderer_info → UNMASKED_VENDOR_WEBGL, UNMASKED_RENDERER_WEBGL
  NOTE: Unlike FPJS Pro, Signifyd does NOT read ~80 GL constants, shader
    precisions, context attributes, or extensions. Only vendor/renderer identity.

WebGPU (Signifyd addition — 14 of 31 limits):
  navigator.gpu.requestAdapter()
  GPUAdapterInfo: architecture, device, description, vendor
    (all empty strings in Firefox — zero entropy from info)
  GPUAdapter.features → sorted array (complement: wgpu_missing_features)
  14 GPUSupportedLimits: maxBindGroups, maxDynamic{Uniform,Storage}BuffersPerPipelineLayout,
    maxBufferSize, maxColorAttachments, maxComputeWorkgroupStorageSize,
    maxComputeInvocationsPerWorkgroup, maxTextureDimension{1D,2D,3D},
    maxStorageBuffersPerShaderStage, maxUniformBufferBindingSize,
    maxVertexBuffers, maxVertexAttributes
  NOTE: Reads 14 limits vs FPJS Pro's full 31

Audio (CreepJS module — OfflineAudioContext + AudioWorklet):
  OfflineAudioContext(1, 100, 44100)
  OscillatorNode(triangle, 10kHz) → DynamicsCompressor → Analyser
  46 Web Audio APIs: getFloatFrequencyData, getFloatTimeDomainData,
    getChannelData, copyFromChannel, plus default/min/max parameter values
  AudioWorklet: processes at 192kHz, reads channel sums
  Noise detection: compares getChannelData vs copyFromChannel

Speech synthesis (CreepJS module):
  speechSynthesis.getVoices() — used for lie detection (API tampering check)

Fonts (CreepJS module — TextMetrics + CSS system fonts):
  48-font CSS_FONT_FAMILY list (frozen at May 2023 fork) via canvas measureText()
  6 CSS system font keywords (caption, icon, menu, message-box, small-caption,
    status-bar) → resolved fontSize + fontFamily via getComputedStyle()
  NOTE: FontFace API is only used in lie detection (tampering check), NOT for
    font enumeration. Font fingerprinting is via TextMetrics and CSS system fonts.

Screen & display:
  screen.width, screen.height        → screen_primary_resolution
  screen.availWidth, screen.availHeight → screen_primary_avail
  screen.colorDepth                  → screen_primary_color_depth
  screen.pixelDepth                  → screen_primary_pixel_depth
  window.devicePixelRatio            → screen_web_pixel_ratio
  window.innerWidth, window.innerHeight → screen_web_inner
  screen.orientation.type            → screen_primary_orientation
  window.outerWidth/Height           → NOT collected by Signifyd

CSS media queries (CreepJS module — 14 features via matchMedia + CSS @media rules):
  prefers-color-scheme               → screen_color_scheme
  prefers-reduced-motion             → screen_prefers_reduced_motion
  inverted-colors                    → screen_inverted_colors
  monochrome                         → screen_monochrome
  color-gamut                        → NO MATCH (srgb/p3/rec2020)
  forced-colors                      → prefs_use_document_colors
  any-hover / hover                  → hw_pointer_type (hover derived from pointer type)
  any-pointer / pointer              → hw_pointer_type, hw_any_pointer_type
  device-aspect-ratio                → NO MATCH (derivable from screen dims)
  device-screen (binary search)      → NO MATCH (derivable from screen dims)
  display-mode                       → NO MATCH
  orientation                        → screen_primary_orientation
  NOTE: prefers-contrast and dynamic-range are NOT tested by Signifyd
    (unlike some other fingerprinters)

CSS computed styles (CreepJS module — 38 system colors + 6 system fonts + property enumeration):
  getComputedStyle() for 38 CSS system color keywords + 6 system font keywords
  → font_css_system_colors (hash of 38 system colors)
  → font_css_system_fonts (hash of 6 system fonts)
  Object.getOwnPropertyNames() on CSSStyleDeclaration prototype chain
    → full CSS property name enumeration (~1162 names incl. vendor-prefixed)
    → NO MATCH (list of supported property names varies by browser/version)

Navigator properties (main thread + Worker + SharedWorker):
  navigator.userAgent                → user_agent
  navigator.platform                 → platform
  navigator.oscpu                    → hw_oscpu
  navigator.hardwareConcurrency      → hw_processor_count
  navigator.languages                → locale_accept_language
  navigator.maxTouchPoints           → hw_max_touch_points
  navigator.doNotTrack               → prefs_general_donottrack_enabled
  navigator.buildID                  → build_date (constant in Firefox, excluded from subset)
  navigator.cookieEnabled            → prefs_cookiesenabled (prefs_cookiebehavior != 2)
  navigator.globalPrivacyControl     → prefs_general_globalprivacycontrol_enabled
  navigator.vendor                   → NO MATCH (constant "" in Firefox)
  navigator.deviceMemory             → NO MATCH (Chrome-only, undefined in Firefox)
  navigator.plugins                  → NO MATCH (constant in modern Firefox)
  navigator.mimeTypes                → NO MATCH (constant in modern Firefox)
  navigator.appVersion               → NO MATCH (constant "5.0 (…)")
  navigator.appCodeName              → NO MATCH (constant "Mozilla")
  navigator.webdriver                → NO MATCH (automation flag)
  navigator.userAgentData            → NO MATCH (Chrome-only Client Hints: brands,
    mobile, platform, architecture, bitness, fullVersionList, etc.)
  navigator.pdfViewerEnabled         → NOT collected by Signifyd

Math precision (CreepJS module):
  Transcendental functions (same set as FPJS)

Intl API (CreepJS module — 6 Intl constructors):
  Intl.DateTimeFormat().resolvedOptions().timeZone → intl_timezone_web
  Intl.DateTimeFormat().resolvedOptions().locale  → intl_intl_locale
  Date.getTimezoneOffset()            → intl_timezone_offset_web
  Intl.DateTimeFormat.format()        → NO MATCH
  Intl.DisplayNames                   → NO MATCH
  Intl.ListFormat                     → NO MATCH
  Intl.NumberFormat                   → NO MATCH
  Intl.PluralRules                    → NO MATCH
  Intl.RelativeTimeFormat             → NO MATCH
  Intl.Collator()                    → NO MATCH (locale extraction only)

Cookie/storage testing (cookieMonster — minimal in deployed script):
  navigator.cookieEnabled             → prefs_cookiesenabled (prefs_cookiebehavior != 2)

=== Signals with NO fingerprinting entropy within Firefox ===

ClientRects/DOMRect (CreepJS module — 12 elements × 4 APIs):
  Element.getClientRects(), Element.getBoundingClientRect()
  Range.getClientRects(), Range.getBoundingClientRect()
  91 emoji codepoints for rendering fingerprint
  → clientrects_element_gbcr_*, clientrects_element_gcr_*,
    clientrects_range_gbcr_*, clientrects_range_gcr_*,
    clientrects_emoji_*, clientrects_ghost_dimensions,
    clientrects_known_dimensions, clientrects_text_font_family

SVG rendering (CreepJS module — 10 SVG APIs):
  SVGRectElement.getBBox(), SVGTextContentElement methods
  19 emoji codepoints, scale(1.000999) transform
  → svg_bbox, svg_computed_text_length, svg_emoji_set,
    svg_extent_of_char, svg_substring_length

Worker context fingerprinting (Signifyd original — 38 APIs in 3 contexts):
  Full navigator profile in Main, WebWorker, SharedWorker
  Includes WebGL vendor/renderer via OffscreenCanvas in workers
  Compares profiles across contexts to detect spoofing inconsistencies
  → NO MATCH (lie detection, not fingerprinting surface)

Incognito detection (detectIncognito v1.4.1):
  Firefox: serviceWorker availability test
  Also: JS engine identification via parseInt("-1").toFixed(-1) error length
  → NO MATCH

WebRTC (IP detection only, NOT SDP fingerprinting):
  RTCPeerConnection → ICE candidates → IPv4 address extraction
  High constructor sample count (124) is from lie detection, not fingerprinting
  → NO MATCH (IP addresses, not device fingerprinting)

Performance / timing:
  performance.now() resolution (5000 iterations)
  StorageManager.estimate() quota
  performance.timing.* (21 PerformanceTiming properties)
  performance.timeOrigin (used as baseline to normalize timing values)
  performance.navigation.type (direct/reload/back-forward)
  performance.navigation.redirectCount
  → NO MATCH

Window features:
  Object.getOwnPropertyNames(window) → moz/webkit/apple prefix counts (~970 keys)
  → NO MATCH (constant within Firefox version)

Crypto key persistence (Signifyd original):
  ECDSA P-256 key pair in IndexedDB ("signifyd-db") for cross-visit device ID
  → NO MATCH (tracking mechanism, not fingerprinting surface)

In-app WebView detection (Signifyd original):
  UA pattern matching for CriOS, FxiOS, Instagram, Facebook, TikTok, Snapchat, etc.
  → NO MATCH (derived from user_agent)

Battery / network (Signifyd addition):
  navigator.getBattery() → charging, level
  navigator.connection → downlink, effectiveType, rtt
  navigator.bluetooth.getAvailability()
  → NO MATCH (blocked in Firefox / Chrome-only / ephemeral)

Lie/spoof detection (CreepJS module — 35+ API classes, 17+ techniques):
  Prototype chain validation, toString() checks, descriptor validation
  Tests across AnalyserNode, CanvasRenderingContext2D, Date, Document,
    Element, HTMLIFrameElement, Intl, Math, Navigator, Screen,
    WebGLRenderingContext, etc.
  Phantom iframe: creates hidden iframe in shadow DOM, accesses contentWindow
    for "clean" window reference used in Object.getOwnPropertyNames(window)
  → NO MATCH (anti-tampering, not fingerprinting)

Permissions probing (39 permission names):
  navigator.permissions.query() for 39 names including accelerometer,
    camera, geolocation, gyroscope, microphone, midi, nfc, notifications, etc.
  → NO MATCH
"""

###############################################################################
###############################################################################
###############################################################################
###############################################################################

ALL_FINGERPRINTERS_UNION = (
    FPSET_AKAMAI_V1 | FPSET_AKAMAI_V2 |
    FPSET_SIFT_SCIENCE | FPSET_SIGNIFYD |
    FPSET_FINGERPRINTJS_V1 | FPSET_FINGERPRINTJS_V2
)

ALL_FINGERPRINTERS = {
  "AkamaiV1": FPSET_AKAMAI_V1,
  "AkamaiV2": FPSET_AKAMAI_V2,
  "SiftScience": FPSET_SIFT_SCIENCE,
  "Signifyd": FPSET_SIGNIFYD,
  "FPJSv1": FPSET_FINGERPRINTJS_V1,
  "FPJSv2": FPSET_FINGERPRINTJS_V2,
  "AkamaiV2_InOut": FPSET_AKAMAI_V2_INOUT,
  "FPJSv2_InOut": FPSET_FINGERPRINTJS_V2_INOUT,
  "AllFingerprinters": ALL_FINGERPRINTERS_UNION,
}



# Assert that no fingerprinter subset contains raw renderer metrics (use _vendor/_family/_model/_api instead)
for _fp_name, _fp_subset in ALL_FINGERPRINTERS.items():
    for _metric in _fp_subset:
        assert not _metric.endswith("_renderer_raw"), (
            f"Fingerprinter '{_fp_name}' contains raw renderer metric '{_metric}'. "
            "Use a classified variant (e.g. webgl_renderer_raw_vendor) instead."
        )

