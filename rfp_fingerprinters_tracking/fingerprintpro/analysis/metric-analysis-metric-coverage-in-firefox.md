# FingerprintJS Pro v3.12.6 — Firefox metrics.yaml Coverage Analysis

Systematic comparison of every FingerprintJS Pro signal against the data
collected in `toolkit/components/resistfingerprinting/metrics.yaml`
(the `user-characteristics` ping).

**Legend:**
- **COLLECTED** — Firefox metrics.yaml has an equivalent metric
- **NOT COLLECTED** — No equivalent metric exists
- **PARTIALLY** — Related data is collected but not an exact match
- **N/A** — Not applicable to Firefox's use case (e.g. Chrome-only APIs)

Where both FPJS analyses (data intercept and deobs) disagree on a signal's
identity, both interpretations are listed. Where a metric wasn't immediately
clear from its YAML description, the Firefox source code was consulted.

---

## 1. Browser & OS Identity

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s1 | `navigator.oscpu` | `oscpu` | **COLLECTED** |
| s15 | `navigator.platform` | `platform` | **COLLECTED** |
| s101 | `navigator.userAgent` | `user_agent` | **COLLECTED** |
| s103 | `navigator.appVersion` | *(none)* | **NOT COLLECTED** |
| s123 | `navigator.productSub` | *(none)* | **NOT COLLECTED** |
| s27 | `navigator.vendor` | *(none)* | **NOT COLLECTED** |

**Notes:** `appVersion`, `productSub`, and `vendor` are static strings in
Firefox (`"5.0 (…)"`, `"20100101"`, `""`) — they have essentially zero
entropy across the Firefox population. Firefox collects `user_agent` which
is the primary identity string. OS identity is also covered by `os_name`,
`os_version`, `os_distro`, `cpu_model`, `cpu_arch`, `firefox_binary_arch`.

---

## 2. Language & Locale

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s2 | `navigator.language` + `navigator.languages` | `languages`, `prefs_intl_accept_languages` | **COLLECTED** |
| s82 | `Intl.DateTimeFormat().resolvedOptions().locale` | `intl_locale` | **COLLECTED** |
| s83 | `navigator.languages` | `languages` | **COLLECTED** |
| s202 | Intl locale (variant cross-check) | `intl_locale` | **COLLECTED** |

**Notes:** Full coverage. `system_locale` also captures the host OS locale.

---

## 3. Timezone

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s9 | `Intl.DateTimeFormat().resolvedOptions().timeZone` | `timezone`, `timezone_web`, `timezone_offset_web` | **COLLECTED** |
| s45 | `Date.now()` + timezone-adjusted timestamp | `timezone_offset_web` | **PARTIALLY** |

**Notes:** Firefox collects the timezone string and offset. It does not
collect raw epoch timestamps or clock-skew indicators.

---

## 4. Screen & Display

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s5 | `screen.width`, `screen.height` | `screen_width`, `screen_height`, `screens` | **COLLECTED** |
| s6 | Screen available rect (taskbar offsets) | `avail_height`, `avail_width`, `screens` | **COLLECTED** |
| s3 | `screen.colorDepth` | `screens` (JSON includes colorDepth) | **COLLECTED** |
| s84 | Screen dimensions from iframe | `screen_width`, `screen_height` | **COLLECTED** |
| s150 | `outerWidth/Height`, `innerWidth/Height` | `outer_width`, `outer_height`, `inner_width`, `inner_height` | **COLLECTED** |
| s57 | `window.devicePixelRatio` | `pixel_ratio` | **COLLECTED** |
| s142 | High-DPI / Retina detection | `pixel_ratio` (derivable) | **COLLECTED** |
| s152 | CSS half-pixel border rendering (`.5px dotted offsetHeight`) | *(none)* | **NOT COLLECTED** |
| s204 | Scrollbar overlay detection | `prefs_overlay_scrollbars` | **PARTIALLY** |

**Notes:** `screens` is a JSON blob containing colorDepth, pixelDepth,
availRect, orientation, HDR support, and scale factor. The `prefs_overlay_scrollbars`
pref captures the scrollbar setting directly rather than via DOM probing.
`size_mode` (maximized/minimized/normal/fullscreen) is also collected.

---

## 5. Hardware

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s7 | `navigator.hardwareConcurrency` | `processor_count` | **COLLECTED** |
| s4 | `navigator.deviceMemory` | *(none)* | **N/A** (Chrome-only) |
| s14 | `navigator.cpuClass` | *(none)* | **N/A** (IE-only) |

**Notes:** Firefox also collects `cpu_model`, `cpu_arch`,
`machine_model_name`, and `firefox_binary_arch` — far more hardware detail
than FPJS gets from web APIs.

---

## 6. Storage Support

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s10 | `!!window.sessionStorage` | *(none)* | **NOT COLLECTED** |
| s11 | `!!window.localStorage` | *(none)* | **NOT COLLECTED** |
| s12 | `!!window.indexedDB` | *(none)* | **NOT COLLECTED** |
| s13 | `!!window.openDatabase` (WebSQL) | *(none)* | **NOT COLLECTED** |
| s32 | Cookie write/read test | `prefs_network_cookie_cookiebehavior` | **PARTIALLY** |

**Notes:** Firefox does not probe storage API availability since it knows
its own feature set. The cookie behavior pref is collected instead of a
runtime probe.

---

## 7. Touch & Input

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s19 | Touch support (maxTouchPoints, TouchEvent, ontouchstart) | `max_touch_points` | **COLLECTED** |

**Notes:** Firefox also collects extensive pointer/touch metrics:
`pointer_type`, `any_pointer_type`, `pointer_height`, `pointer_width`,
`pointer_pressure`, `pointer_tangentinal_pressure`, `pointer_tiltx`,
`pointer_tilty`, `pointer_twist`, `touch_rotation_angle`.

---

## 8. Plugins & MIME Types

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s16 | Full plugin list with MIME types | *(none)* | **NOT COLLECTED** |
| s117 | `navigator.plugins.length` | *(none)* | **NOT COLLECTED** |
| s135 | `navigator.mimeTypes.length` | *(none)* | **NOT COLLECTED** |
| s136 | MimeTypeArray prototype chain validation | *(none)* | **NOT COLLECTED** |
| s118 | PluginArray/Plugin prototype validation | *(none)* | **NOT COLLECTED** |
| s80 | `navigator.pdfViewerEnabled` | `pdf_viewer` | **COLLECTED** |

**Notes:** Plugin enumeration is largely vestigial in modern browsers.
Firefox PDF viewer support is the only remaining meaningful signal here.

---

## 9. Canvas Fingerprinting

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s17 | Canvas 2D: text hash + geometry hash + winding rule | `canvasdata12_fingerprintjs1` (text), `canvasdata13_fingerprintjs2` (geometry) | **COLLECTED** |

**Notes:** Firefox **specifically replicates** FPJS's canvas fingerprinting
technique — `canvasdata12_fingerprintjs1` is described as "a copy of
fingerprintjs' text canvas" and `canvasdata13_fingerprintjs2` as "a copy of
fingerprintjs' geometry canvas". Firefox also collects 10 additional canvas
tests (control, triangle, photographic, transparency, local fonts, system-ui
fonts, Firefox fonts, each with plain and styled variants), a WebGL canvas
hash, software-rendered variants of all tests, and raw pixel data variants.
This is far more comprehensive than FPJS's single canvas probe.

---

## 10. WebGL Fingerprinting

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s74 | WebGL vendor/renderer/version strings | `gl_vendor`, `gl_renderer`, `gl_vendor_raw`, `gl_renderer_raw`, `gl_version_raw` | **COLLECTED** |
| s75 | WebGL full parameter dump (extensions, shader precisions, ~300 constants) | `gl_extensions`, `gl_extensions_raw`, `gl_params`, `gl_params_extensions`, `gl_precision_fragment`, `gl_precision_vertex`, `gl_fragment_shader`, `gl_vertex_shader`, `gl_minimal_source`, `gl_context_type` | **COLLECTED** |
| s76 | WebGL rendered image hash | `canvasdata11_webgl` | **COLLECTED** |
| s209 | GPU pixel sampling (raw RGBA bytes) | *(none)* | **NOT COLLECTED** |

**Notes:** Firefox also collects WebGL2 equivalents (`gl2_*`), software-
rendering variants (`gl_*_software`, `gl2_*_software`), and extensive WebGPU
data (~30 `wgpu_*` limit metrics). FPJS does not collect WebGPU data.

---

## 11. Audio Fingerprinting

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s21 (data) | AudioContext oscillator fingerprint (float value) | `audio_fingerprint`, `audio_fingerprint2` | **COLLECTED** |
| s22 (data) / s96 (deobs) | `AudioContext.baseLatency` | *(none)* | **NOT COLLECTED** |

**Notes:** Firefox's audio fingerprint implementation **exactly replicates**
the FPJS technique: Triangle oscillator at 10kHz → DynamicsCompressor
(threshold:-50, knee:40, ratio:12, attack:0, release:0.25) → AnalyserNode,
rendering 5000 samples at 44.1kHz. Firefox additionally collects:
`audio_compressor_gain_reduction`, `audio_float_frequency_sum`,
`audio_float_time_domain_sum`, `audio_unique_samples`, `audio_frames`,
`audio_rate`, `audio_channels`. `AudioContext.baseLatency` is not collected.

---

## 12. Font Fingerprinting

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s20 | Font enumeration (50 fonts via DOM width comparison) | `missing_fonts`, `fonts_fpjs_allowlisted`, `fonts_fpjs_nonallowlisted`, `fonts_variant_a` through `h` (allowlisted + nonallowlisted) | **COLLECTED** |
| s51 | `measureText()` width per generic font family | *(none directly)* | **NOT COLLECTED** |
| s206 | System/default font detection (Firefox radio input font) | `css_system_fonts` | **COLLECTED** |
| s207 | `FontFace` API local font load test | *(none)* | **NOT COLLECTED** |
| s210 | Dynamic/async font detection | *(none)* | **NOT COLLECTED** |
| s211 | Extended font probing / capability flags | *(none)* | **NOT COLLECTED** |

**Notes:** Firefox's font coverage is extensive. `missing_fonts` lists fonts
absent from the platform font list. `fonts_fpjs_*` specifically hashes the
FPJS font list results. Font variants A–H test different font querying
strategies. Font preference prefs are collected: `font_default_*`,
`font_name_serif_*`, `font_name_sans_serif_*`, `font_name_monospace_*`,
`font_size_variable_*`, `font_size_monospace_*`, `font_minimum_size_*`,
`font_name_list_*_modified`, `text_anti_aliasing`,
`prefs_browser_display_use_document_fonts`.

---

## 13. Math Fingerprint

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s46 | 20+ transcendental functions (sin, cos, tan, acos, sinh, exp, log1p, pow, etc.) with specific constants + polyfill variants | `math_ops`, `math_ops_fdlibm`, `math_ops_fdlibm_2` | **COLLECTED** |

**Notes:** Firefox also collects `fpu_control_state` (FPU rounding mode and
precision settings) to diagnose math variation causes.

---

## 14. CSS Media Queries

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s44 | `prefers-color-scheme` (dark/light) | `color_scheme` | **COLLECTED** |
| s37 | `color-gamut` (srgb / p3 / rec2020) | *(none)* | **NOT COLLECTED** |
| s33 or s41 | `inverted-colors` | `inverted_colors` | **COLLECTED** |
| s38 | `prefers-contrast` | `prefers_contrast` | **COLLECTED** |
| s39 | `forced-colors` (active/none) | *(none)* | **NOT COLLECTED** |
| s40 or s43 | `prefers-reduced-motion` | `prefers_reduced_motion` | **COLLECTED** |
| s41 or s91 | `prefers-reduced-transparency` | `prefers_reduced_transparency` | **COLLECTED** |
| s42 | `monochrome` (bits) | `monochrome` | **COLLECTED** |
| s43 or s40 | `dynamic-range` (HDR) | `screens` (JSON includes `hdr` field) | **COLLECTED** |
| s139 | `CSS.supports('backdrop-filter','blur(2px)')` | *(none)* | **NOT COLLECTED** |

**Notes:** `color_scheme` tracks Firefox's internal ColorScheme enum from
ContentPrefs() rather than the CSS media query directly, but represents the
same underlying preference. `color-gamut`, `forced-colors`, and
`backdrop-filter` support are not tracked. The `screens` JSON includes an
`hdr` field covering dynamic-range.

---

## 15. CSS System Colors

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s87 | ~30 CSS system color keyword values (AccentColor, ButtonFace, Highlight, etc.) | `css_system_colors`, `color_accentcolor`, `color_accentcolortext`, `color_canvas`, `color_canvastext`, `color_highlight`, `color_highlighttext`, `color_selecteditem`, `color_selecteditemtext`, `use_document_colors` | **COLLECTED** |

**Notes:** `css_system_colors` is a JSON array of all CSS system color
keywords with their computed hex values. Individual colors also have
dedicated metrics. `css_system_fonts` collects computed font properties
for system font keywords.

---

## 16. CSS Precision / URL Probes

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s203 | CSS `calc()` rounding precision | *(none)* | **NOT COLLECTED** |
| s205 | `new URL("C:/").protocol` parsing behavior | *(none)* | **NOT COLLECTED** |

---

## 17. Browser / Engine Detection

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s59 | IE detection | *(none)* | **N/A** |
| s60 | Edge Legacy detection | *(none)* | **N/A** |
| s61 | Chrome detection | *(none)* | **N/A** |
| s62 | Safari detection | *(none)* | **N/A** |
| s63 | Desktop Safari / Gecko detection | *(none)* | **N/A** |
| s64 | Firefox detection | *(none)* | **N/A** |
| s65 | Mobile detection | *(none)* | **N/A** |
| s201 | Chromium 120+ detection | *(none)* | **N/A** |
| s28 | Window vendor globals (chrome, safari, yandex, etc.) | *(none)* | **N/A** |
| s156 | Window property name hash detection | *(none)* | **N/A** |

**Notes:** All N/A — Firefox doesn't need to detect its own engine. These
signals exist in FPJS to identify which browser is being fingerprinted.
Firefox already knows this from `version`, `channel`, `build_date`.

---

## 18. Navigator API Surface / Prototype Checks

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s145 | Navigator method/property enumeration | *(none)* | **NOT COLLECTED** |
| s166 | Navigator property layout (count + positional indices) | *(none)* | **NOT COLLECTED** |
| s131 | `document.documentElement.getAttributeNames()` | *(none)* | **NOT COLLECTED** |
| s130 | `typeof SourceBuffer`, `typeof SourceBufferList` | *(none)* | **NOT COLLECTED** |
| s133 | `window.external.toString()` | *(none)* | **NOT COLLECTED** |
| s148 | `Function.prototype.bind.toString()` | *(none)* | **NOT COLLECTED** |
| s132 | Native function `toString()` format | *(none)* | **NOT COLLECTED** |
| s119 | Error stack trace format | *(none)* | **NOT COLLECTED** |
| s120 | `Error.prototype.toSource()` | *(none)* | **NOT COLLECTED** |
| s24 | `eval.toString().length` | *(none)* | **NOT COLLECTED** |
| s81 | Float32Array NaN byte representation | `fpu_control_state` | **PARTIALLY** |
| s144 | `SharedArrayBuffer` availability | *(none)* | **NOT COLLECTED** |
| s155 | Window property getter `toString()` fingerprint | *(none)* | **NOT COLLECTED** |
| s151 | `document.createElement` override descriptor check | *(none)* | **NOT COLLECTED** |
| s159 | Function/Object deletion resilience test | *(none)* | **NOT COLLECTED** |
| s146 | Scoped variable reference / devtools detection | *(none)* | **NOT COLLECTED** |

**Notes:** These are primarily browser engine identification and tampering
detection signals. They have near-zero entropy across the Firefox population
(all Firefox users return the same values). `fpu_control_state` covers the
underlying cause of Float32Array byte representation differences.

---

## 19. Bot & Automation Detection

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s72 | `navigator.webdriver` | *(none)* | **NOT COLLECTED** |
| s157 | Automation framework globals (Selenium, PhantomJS, Puppeteer, etc.) | *(none)* | **NOT COLLECTED** |
| s154 (data) | WebView detection (Facebook, Instagram, etc.) | *(none)* | **NOT COLLECTED** |
| s165 | `Event.isTrusted` check | *(none)* | **NOT COLLECTED** |
| s149 | `window.process` (Node.js/Electron detection) | *(none)* | **NOT COLLECTED** |
| s167 | Bot fingerprint (encrypted property name table) | *(none)* | **NOT COLLECTED** |

**Notes:** All N/A for Firefox's use case. Bot detection is about identifying
non-genuine browser sessions. Firefox's telemetry only runs in real Firefox
instances.

---

## 20. Ad Blocker / Privacy Detection

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s21 (deobs) / s89 | Ad blocker detection (~200 CSS selectors from ~40 filter lists) | *(none)* | **NOT COLLECTED** |
| s33 (deobs) | Brave browser detection (canvas IDAT chunk analysis) | *(none)* | **NOT COLLECTED** |
| s86 | Private/incognito mode detection | *(none)* | **NOT COLLECTED** |
| s106 | Notification permission mismatch (incognito indicator) | *(none)* | **NOT COLLECTED** |
| s68 | Restricted browser detection (missing APIs) | *(none)* | **NOT COLLECTED** |
| s95 | Notification permission check | *(none)* | **NOT COLLECTED** |

---

## 21. Speech Synthesis

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s52 | `speechSynthesis.getVoices()` hash variant 1 | `voices_sha1`, `voices_all_ssdeep` | **COLLECTED** |
| s158 | `speechSynthesis.getVoices()` variant 2 | `voices_sha1`, `voices_local_ssdeep`, `voices_nonlocal_ssdeep` | **COLLECTED** |
| s160 | `speechSynthesis.getVoices()` variant 3 | `voices_sha1` | **COLLECTED** |

**Notes:** Firefox collects comprehensive voice data: `voices_count`,
`voices_local_count`, `voices_default`, `voices_sample` (5 sample voice
names), `voices_sha1` (hash of all voices), and ssdeep fuzzy hashes
(`voices_all_ssdeep`, `voices_local_ssdeep`, `voices_nonlocal_ssdeep`).

---

## 22. Timing & Performance Probes

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s49 | `performance.now()` timer resolution (50k iterations) | *(none)* | **NOT COLLECTED** |
| s200 | `performance.timeOrigin` / collection timestamp | *(none)* | **NOT COLLECTED** |

---

## 23. Persistent Identifiers

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s94 | Storage-based UUID (persisted across visits) | *(none)* | **N/A** |
| s79 | Browser profile file detection | *(none)* | **N/A** |

**Notes:** These are cross-visit tracking mechanisms, not fingerprinting
surface metrics. Firefox has its own `client_identifier` UUID for
deduplication.

---

## 24. Frame & Origin

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s69 | Frame hierarchy traversal | *(none)* | **NOT COLLECTED** |
| s71 | Window/location origins + ancestorOrigins | *(none)* | **NOT COLLECTED** |
| s98 | `"serviceWorker" in Navigator.prototype` | *(none)* | **NOT COLLECTED** |
| s99 | `window.isSecureContext` | *(none)* | **NOT COLLECTED** |

**Notes:** These are context-specific signals (vary per page, not per user).
They have no fingerprinting entropy across users.

---

## 25. MathML Rendering

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s92 | MathML bounding box / serif text rect | `mathml1`–`mathml10`, `mathml_diag_values`, `mathml_diag_font_family`, `mathml_diag_prefs_modified` | **COLLECTED** |
| s93 | Unicode text rendering measurement | `clientrects_emoji_*`, `clientrects_text_font_family` | **COLLECTED** |

**Notes:** Firefox collects 10 individual MathML element widths, a full
diagnostic array of all widths, the computed MathML font-family, and any
modified MathML prefs. The clientrects metrics include emoji rendering
measurements.

---

## 26. ClientRects / DOMRect

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s92, s93 | `getBoundingClientRect()` measurements | 48 `clientrects_element_*` metrics (12 via getClientRects, 12 via getBoundingClientRect), 24 `clientrects_range_*` metrics, `clientrects_emoji_*`, `clientrects_known_dimensions`, `clientrects_ghost_dimensions` | **COLLECTED** |

**Notes:** Firefox's clientrects coverage is **far more extensive** than
FPJS Pro's. FPJS collects 2-3 text bounding rectangles. Firefox collects
DOMRect measurements for 12 different CSS-styled elements using 4 different
APIs (Element.getClientRects, Element.getBoundingClientRect,
Range.getClientRects, Range.getBoundingClientRect), plus emoji rendering
metrics, SVG measurements (`svg_bbox`, `svg_computed_text_length`,
`svg_extent_of_char`, `svg_substring_length`, `svg_emoji_set`), and known-
dimension control measurements. Based on CreepJS/TU Munich research.

---

## 27. TLS Fingerprinting

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s70 | TLS fingerprint (server-side capture of TLS handshake) | *(none)* | **NOT COLLECTED** |

**Notes:** TLS fingerprinting requires a cooperating server endpoint. Not
applicable to client-side telemetry.

---

## 28. UA Client Hints

| FPJS Signal | API / Description | Firefox Metric | Status |
|---|---|---|---|
| s58 | `navigator.userAgentData.getHighEntropyValues()` | *(none)* | **N/A** (Chrome-only) |
| s104 | `navigator.connection` (Network Information API) | *(none)* | **N/A** (Chrome-only) |
| s102 | `navigator.userAgentData` presence | *(none)* | **N/A** (Chrome-only) |

---

## 29. Encrypted / Unidentified Signals

| FPJS Signal | Best-guess description | Firefox Metric | Status |
|---|---|---|---|
| s23 | Chrome+Safari engine probe | *(none)* | **N/A** |
| s29 | Complex async engine probe | *(none)* | **N/A** |
| s50 | `hardwareConcurrency` descriptor validation | *(none)* | **NOT COLLECTED** |
| s55 | Page URL hash / stored fingerprint | *(none)* | **N/A** |
| s85 | IndexedDB check (WebKit/Safari) | *(none)* | **N/A** |
| s86 | Private browsing detection | *(none)* | **NOT COLLECTED** |
| s89 | Ad blocker detection (id module) | *(none)* | **NOT COLLECTED** |
| s91 | `prefers-reduced-transparency` (deobs) | `prefers_reduced_transparency` | **COLLECTED** |
| s95 | Notification permission check | *(none)* | **NOT COLLECTED** |
| s97 | Unknown (500ms async, obfuscated) | *(none)* | **UNKNOWN** |
| s163 | Chrome/Safari iframe Error.stack probe | *(none)* | **N/A** |
| s167 | Bot fingerprint (encrypted) | *(none)* | **NOT COLLECTED** |
| s210 | Dynamic font detection | *(none)* | **NOT COLLECTED** |

---

## 30. Experimental Signals

| FPJS Signal | Description | Firefox Metric | Status |
|---|---|---|---|
| exp_s1013 | Experimental (unavailable) | *(none)* | **N/A** |
| exp_s1014 | Encrypted check | *(none)* | **N/A** |
| exp_s1015 | Likely WebGPU/extended canvas | `wgpu_*` metrics, `canvasdata*_raw` | **PARTIALLY** |
| exp_s1016 | Likely GPU detection hash | `wgpu_*` metrics | **PARTIALLY** |

---

## Summary Statistics

### By coverage status

| Status | Count | % of ~117 FPJS signals |
|--------|-------|----------------------|
| **COLLECTED** | 44 | 38% |
| **PARTIALLY COLLECTED** | 7 | 6% |
| **NOT COLLECTED** (relevant) | 31 | 26% |
| **N/A** (Chrome/IE-only, bot detection, engine detection) | 33 | 28% |
| **UNKNOWN** | 2 | 2% |

### By fingerprinting category

| Category | FPJS Signals | Collected | Partial | Not Collected | N/A |
|----------|-------------|-----------|---------|---------------|-----|
| Browser/OS identity | 6 | 3 | 0 | 3 | 0 |
| Language/locale | 4 | 4 | 0 | 0 | 0 |
| Timezone | 2 | 1 | 1 | 0 | 0 |
| Screen/display | 9 | 7 | 1 | 1 | 0 |
| Hardware | 3 | 1 | 0 | 0 | 2 |
| Storage | 5 | 0 | 1 | 4 | 0 |
| Touch/input | 1 | 1 | 0 | 0 | 0 |
| Plugins/MIME | 6 | 1 | 0 | 5 | 0 |
| Canvas | 1 | 1 | 0 | 0 | 0 |
| WebGL | 4 | 3 | 0 | 1 | 0 |
| Audio | 2 | 1 | 0 | 1 | 0 |
| Fonts | 6 | 2 | 0 | 4 | 0 |
| Math | 1 | 1 | 0 | 0 | 0 |
| CSS media queries | 10 | 7 | 0 | 3 | 0 |
| CSS system colors | 1 | 1 | 0 | 0 | 0 |
| CSS precision/URL | 2 | 0 | 0 | 2 | 0 |
| Engine detection | 10 | 0 | 0 | 0 | 10 |
| Navigator API surface | 16 | 0 | 1 | 15 | 0 |
| Bot/automation | 6 | 0 | 0 | 0 | 6 |
| Ad blocker/privacy | 6 | 0 | 0 | 6 | 0 |
| Speech synthesis | 3 | 3 | 0 | 0 | 0 |
| Timing/performance | 2 | 0 | 0 | 2 | 0 |
| Persistent IDs | 2 | 0 | 0 | 0 | 2 |
| Frame/origin | 4 | 0 | 0 | 4 | 0 |
| MathML/text rendering | 2 | 2 | 0 | 0 | 0 |
| ClientRects/DOMRect | 1 | 1 | 0 | 0 | 0 |
| TLS | 1 | 0 | 0 | 1 | 0 |
| UA Client Hints | 3 | 0 | 0 | 0 | 3 |
| Encrypted/unknown | 12 | 1 | 0 | 6 | 5 |
| Experimental | 4 | 0 | 2 | 0 | 2 |

---

## Key Gaps — Signals FPJS Pro Collects That Firefox Does Not

These are the signals that have real fingerprinting entropy and are NOT
currently tracked by Firefox's user-characteristics ping:

### High Priority (high entropy, actively used by FPJS)

1. **AudioContext.baseLatency** (s22/s96) — Numeric value with per-device
   variation. Easy to add.

2. **Plugin/MIME enumeration** (s16, s117, s135) — While largely vestigial,
   FPJS still collects this. Firefox ships 5 PDF viewer plugin entries.
   Low entropy across Firefox users, but could verify uniformity.

3. **`color-gamut` media query** (s37) — srgb vs p3 vs rec2020. Varies by
   display hardware. Easy to add.

4. **`forced-colors` media query** (s39) — Windows high-contrast mode.
   Accessibility signal with real entropy. Easy to add.

5. **`CSS.supports('backdrop-filter','blur(2px)')`** (s139) — Feature
   support boolean. Very low entropy in modern Firefox, but could verify.

6. **`measureText()` widths** (s51) — Per-font-family text measurement.
   Related to existing font metrics but not directly collected.

7. **`FontFace` API test** (s207) — `new FontFace("font","local('Arial')").load()`.
   Already tracked by FPJS but not by Firefox.

8. **Ad blocker / content blocker detection** (s21/s89) — FPJS detects
   which specific filter lists are active. This is a major fingerprinting
   vector not tracked at all.

### Medium Priority (moderate entropy or partially covered)

9. **`navigator.appVersion`** (s103) — Static on Firefox but proves browser identity.

10. **CSS half-pixel rendering** (s152) — `.5px dotted` border `offsetHeight`.
    Reveals rendering engine differences.

11. **Timer resolution** (s49) — `performance.now()` precision clamping.
    Directly related to Firefox's fingerprinting protections.

12. **CSS `calc()` rounding** (s203) — Sub-pixel rounding precision.

13. **`new URL("C:/").protocol`** (s205) — URL parsing behavior.

### Low Priority (low entropy across Firefox population)

14. **Storage API availability** (s10–s13) — All Firefox users have these.

15. **`navigator.vendor`** (s27) — Always `""` on Firefox.

16. **`navigator.productSub`** (s123) — Always `"20100101"` on Firefox.

17. **Native function `toString()` format** (s132, s148) — Same for all Firefox users.

18. **`eval.toString().length`** (s24) — Always 37 on Firefox.

19. **`Error.prototype.toSource()`** (s120) — Firefox-specific, always exists.

20. **Error stack trace format** (s119) — Same format for all Firefox users.

---

## What Firefox Collects That FPJS Pro Does NOT

Firefox's user-characteristics ping collects significant data that FPJS
Pro does not or cannot:

1. **WebGPU adapter limits** — 30 `wgpu_*` metrics covering GPU capabilities
2. **WebGL2** — Full separate set of `gl2_*` metrics
3. **Software-rendered canvas/WebGL** — All canvas and GL tests re-run with
   software rendering for comparison
4. **Raw canvas pixel data** — `canvasdata*_raw` variants
5. **Extensive DOMRect/ClientRects** — 48+ element measurements across 4 APIs
   (vs FPJS's 2-3)
6. **SVG measurements** — bbox, text length, extent of char, substring length
7. **CPU model/arch** — Specific CPU identification
8. **OS distribution** — Linux distro name and version
9. **Firefox build details** — version, channel, build date, binary arch
10. **Keyboard layout** — Current keyboard layout name
11. **Gamepad information** — Connected gamepad details
12. **Media capabilities** — H264 support levels, unsupported/not-smooth/not-efficient codecs
13. **ICE/WebRTC** — Foundation order and discovery latency
14. **Device motion/orientation** — Sensor decimal precision and frequency
15. **Pointer/touch detail** — Pressure, tilt, twist, rotation
16. **Font preferences** — All font-related prefs (not just detected fonts)
17. **MathML rendering** — 10 specific MathML element widths with diagnostics
18. **FPU control state** — Hardware-level floating point settings
19. **Zoom count** — Number of sites with custom zoom levels
20. **Canvas acceleration status** — Whether hardware-accelerated canvas is in use
