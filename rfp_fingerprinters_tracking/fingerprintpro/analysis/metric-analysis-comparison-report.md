# FingerprintJS Pro v3.12.6 — Comparison of Two Analysis Methods

## Analysis Methods

1. **Data Intercept** (`metric-analysis-based-on-data2.md`) — Intercepted the
   actual XHR payload sent to `api.fpjs.io`, reversed the encoding pipeline
   (custom binary JSON → deflate → XOR encryption), and examined the real
   transmitted values. Signal identity was inferred from the **observed values**.

2. **Source Deobfuscation** (`metric-analysis-from-deobs.md`) — Read the
   deobfuscated source code (`sample_scripts/deobfs/1.deob.js`), traced each
   signal's collection function, and documented what API each function calls.
   Signal identity was determined from the **code structure and API calls**.

Both analyses target the same library version (v3.12.6).

---

## Summary

| | Agree | Disagree | Partial / One-sided |
|--|-------|----------|---------------------|
| Signal key → API mapping | ~65 signals | ~20 signals | ~15 signals |
| Signal descriptions | High agreement where key mapping matches | Diverge where key mapping differs | — |
| Overall signal count | Both identify ~115 distinct signals | — | — |
| Architecture | Both describe encrypted POST to api.fpjs.io | Data intercept describes binary format in detail; deobs describes module/stage architecture | — |

---

## Areas of Strong Agreement

These signals are mapped to the same key and described consistently by both
analyses.

### Navigator / Browser Identity

| Key | Both agree on |
|-----|---------------|
| s1 | `navigator.oscpu` |
| s2 | Language list (navigator.language + navigator.languages) |
| s4 | `navigator.deviceMemory` (Chrome-only, null on Firefox) |
| s7 | `navigator.hardwareConcurrency` |
| s14 | `navigator.cpuClass` (IE-only) |
| s15 | `navigator.platform` (deobs adds iPad-on-Mac detection detail) |
| s27 | `navigator.vendor` |
| s80 | `navigator.pdfViewerEnabled` |
| s82 | `Intl.DateTimeFormat().resolvedOptions().locale` |
| s83 | `navigator.languages` |
| s101 | `navigator.userAgent` |
| s102 | `navigator.userAgentData` presence (boolean) |
| s103 | `navigator.appVersion` |
| s104 | `navigator.connection` (Chrome-only, null on Firefox) |
| s123 | `navigator.productSub` |
| s153 | `navigator.onLine` |

### Screen & Display

| Key | Both agree on |
|-----|---------------|
| s3 | `screen.colorDepth` |
| s5 | Screen resolution (width, height sorted descending) |
| s6 | Screen available rect / taskbar offsets |
| s57 | `window.devicePixelRatio` |
| s84 | Screen dimensions from iframe |
| s142 | High-DPI / Retina detection via matchMedia |
| s150 | Window geometry (outerWidth/Height, innerWidth/Height) |
| s152 | CSS half-pixel border rendering (`offsetHeight` of `.5px dotted`) |
| s204 | Scrollbar overlay detection (100x100 overflow:scroll div) |

### Canvas

| Key | Both agree on |
|-----|---------------|
| s17 | Canvas 2D fingerprint — winding rule test + hashed geometry/text renders. Deobs adds detail: specific text ("Cwm fjordbank gly" + emoji), Times New Roman + Arial, `globalCompositeOperation: "multiply"`, evenodd fill |

### WebGL (partial)

| Key | Both agree on |
|-----|---------------|
| s74 | WebGL vendor/renderer strings (VERSION, VENDOR, RENDERER, SHADING_LANGUAGE_VERSION, unmasked variants) |
| s75 | Full WebGL parameter dump (context attributes, ~300 GL constants, shader precisions, extensions) |

### Fonts

| Key | Both agree on |
|-----|---------------|
| s20 | Font enumeration via DOM width/height comparison. Deobs specifies: 50 fonts tested (ARNO PRO, Agency FB, Arial Unicode MS, etc.) against 3 baselines, test string `mmMwWLliI0O&1` at 48px in iframe |
| s206 | System/default font detection (data2 sees `-apple-system`; deobs identifies it as Firefox radio input font) |
| s207 | FontFace API — `new FontFace("font","local('Arial')").load()` |

### Math Precision

| Key | Both agree on |
|-----|---------------|
| s46 | 20+ transcendental math functions with specific constant inputs. Both list acos, acosh, asin, asinh, atanh, atan, sin, sinh, cos, cosh, tan, tanh, exp, expm1, log1p, pow. Deobs adds polyfill variants. |

### Storage

| Key | Both agree on |
|-----|---------------|
| s10 | `!!window.sessionStorage` |
| s11 | `!!window.localStorage` |
| s13 | `!!window.openDatabase` (WebSQL) |
| s32 | Cookie write/read test |

### Timezone & Time

| Key | Both agree on |
|-----|---------------|
| s9 | IANA timezone via `Intl.DateTimeFormat` |
| s45 | `Date.now()` + timezone-adjusted timestamp |
| s200 | Collection timestamp (data2: millisecond epoch; deobs: `performance.timeOrigin` with fallback) |
| s202 | Intl resolved locale |

### Plugins & MIME Types

| Key | Both agree on |
|-----|---------------|
| s16 | Full plugin enumeration with MIME types |
| s117 | `navigator.plugins.length` |
| s118 | Plugin/PluginArray prototype chain validation |
| s135 | `navigator.mimeTypes.length` |
| s136 | MimeTypeArray/MimeType prototype chain validation |

### Touch & Input

| Key | Both agree on |
|-----|---------------|
| s19 | Touch support (maxTouchPoints, TouchEvent, ontouchstart) |

### Prototype & Native Function Checks

| Key | Both agree on |
|-----|---------------|
| s24 | `eval.toString().length` (Chrome=33, Firefox=37, Safari=37) |
| s81 | Float32Array NaN byte representation / endianness |
| s119 | Error stack trace format (throws `null[0]()`) |
| s120 | `Error.prototype.toSource()` (Firefox-specific) |
| s130 | `typeof SourceBuffer`, `typeof SourceBufferList` |
| s132 | Native function `toString()` format (data2: `document.close`; deobs: `window.close`) |
| s144 | `SharedArrayBuffer` availability |
| s148 | `Function.prototype.bind.toString()` |
| s205 | `new URL("C:/").protocol` — URL parsing behavior |

### Browser/Engine Detection

| Key | Both agree on |
|-----|---------------|
| s28 | Window global vendor objects (chrome, safari, yandex, firefox, etc.) |
| s59–s65 | Engine detection flags (IE, Edge, Chrome, Safari, Firefox, Mobile) |
| s68 | Restricted browser detection (missing PushManager, AudioBuffer, etc.) |
| s156 | Window property name hash detection |
| s201 | Chromium 120+ detection |

### Bot & Automation Detection

| Key | Both agree on |
|-----|---------------|
| s72 | `navigator.webdriver` |
| s157 | Automation framework detection (Selenium, PhantomJS, Puppeteer, etc.). Deobs provides the full list of ~30 specific globals checked. |

### Frame & Origin

| Key | Both agree on |
|-----|---------------|
| s69 | Frame hierarchy traversal |
| s71 | Window/location origins + ancestorOrigins |
| s98 | `"serviceWorker" in Navigator.prototype` |
| s99 | `window.isSecureContext` |

### UA Client Hints

| Key | Both agree on |
|-----|---------------|
| s58 | `navigator.userAgentData.getHighEntropyValues()` (null on Firefox) |

### Other

| Key | Both agree on |
|-----|---------------|
| s44 | `prefers-color-scheme` (dark/light) |
| s49 | `performance.now()` timer resolution |
| s131 | `document.documentElement.getAttributeNames()` |
| s133 | `window.external.toString()` |
| s139 | `CSS.supports("backdrop-filter","blur(2px)")` |
| s145 | Navigator prototype method enumeration |
| s151 | `document.createElement` descriptor override check |
| s155 | Window property getter `toString()` fingerprint |
| s165 | `Event.isTrusted` check (both agree on isTrusted concept) |
| s166 | Navigator.prototype property enumeration |

---

## Areas of Disagreement

These signals are assigned to the **same key** but described as **different
APIs or behaviors** by the two analyses. These are the most significant
findings.

### Signal Key Mapping Conflicts

| Key | Data Intercept says | Deobs says | Notes |
|-----|--------------------|-----------|----|
| **s21** | AudioContext oscillator fingerprint (value: `35.749...`) | Ad blocker detection — injects ~200 CSS selectors from ~40 filter lists | The floating-point value in the intercepted data is consistent with an audio fingerprint, not ad blocker results. Deobs may have the wrong key mapping. |
| **s22** | `AudioContext.baseLatency` (value: `23`) | `navigator.webdriver` (duplicate in id module) | The numeric value 23 is consistent with baseLatency, not a boolean webdriver flag. Deobs may have swapped this. |
| **s30** | `HTMLAnchorElement.attributionSourceId` (value: `"1"`) | `navigator.connection.rtt` (Network Information API) | Completely different APIs. |
| **s33** | `inverted-colors` CSS media query (value: `false`) | Brave browser detection (canvas IDAT chunk analysis + window check for "Brave") | Fundamentally different signal types. |
| **s36** | HDR / dynamic-range media query variant (value: `null`) | `screen.colorDepth` async variant | Data2 puts this in display; deobs puts it in screen. |
| **s40** | `prefers-reduced-motion` (value: `false`) | `dynamic-range` — high (HDR) / standard | **Swapped with s43.** |
| **s41** | `prefers-reduced-transparency` (value: `null`) | `inverted-colors` — inverted / none | Different media query. |
| **s43** | `dynamic-range: high` (value: `false`) | `prefers-reduced-motion` — reduce / no-preference | **Swapped with s40.** |
| **s48** | Multi-component hash (array of 6 hash integers) | Cookie-related data | Different descriptions. |
| **s55** | Stored fingerprint / storage persistence check | Page URL hash | Different descriptions. |
| **s76** | WebGL rendered image hash (value: `"27fe1c..."`) | Window dimensions (outerWidth, outerHeight, innerWidth, innerHeight) | Major disagreement — WebGL vs screen data. Data2 maps s150 to window dimensions, so deobs may have s76 wrong. |
| **s87** | CSS system colors (~30 AccentColor/ButtonFace/Highlight/etc. values) | CSS text measurement (renders styled text in iframe, measures bounding box) | Completely different things measured. |
| **s92** | `getBoundingClientRect()` with serif font | MathML rendering fingerprint (product operator with Greek letters) | Related concept (both measure rendered elements) but different content. |
| **s93** | `getBoundingClientRect()` with wide content | Unicode text rendering measurement | Similar divergence as s92. |
| **s94** | Storage-based UUID (persisted across visits) | Active detection via encrypted `Sa` string table | Data2 shows full UUID object; deobs couldn't fully decode it. |
| **s96** | *(not listed)* | `AudioContext.baseLatency` | Deobs puts baseLatency here; data2 puts it at s22. |
| **s154** | WebView detection (Facebook, Instagram, etc.) | `navigator.onLine` (duplicate in bd module) | Data2 shows a rich object `{"wv","wvp","pr","ck","pt","fp"}`; deobs says simple boolean. |
| **s203** | CSS `calc()` rounding precision | Creates `<a>` element via encrypted property dispatch | Different mechanisms. |
| **s209** | GPU pixel sampling (raw RGBA bytes from rendered surface) | Encrypted via `Al` string table (likely EME/DRM check) | Major disagreement on what this signal captures. |

### CSS Media Query Signal Assignment — Systematic Swap

The most notable pattern is that several CSS media query signals are assigned
to **different keys** in the two analyses:

| Media Query | Data Intercept key | Deobs key |
|-------------|-------------------|-----------|
| `inverted-colors` | s33 | s41 |
| `prefers-reduced-transparency` | s41 | s91 |
| `dynamic-range` | s43 | s40 |
| `prefers-reduced-motion` | s40 | s43 |
| Brave detection | *(not separated)* | s33 |

This suggests one of the analyses has incorrect signal-to-key mappings for
this group of CSS probes. The deobs approach traces code paths which should
be reliable for key assignment; the data intercept approach infers from values
which can be ambiguous when multiple signals return `false` or `null`.

### Audio Signal Assignment Conflict

| What | Data Intercept key | Deobs key |
|------|-------------------|-----------|
| AudioContext oscillator fingerprint | s21 | au$1 (function name, no explicit s-key assigned) |
| AudioContext.baseLatency | s22 | s96 |
| Ad blocker detection | *(not s21)* | s21 |
| navigator.webdriver (duplicate) | *(not s22)* | s22 |

The data intercept's s21 value (`35.749...`) is clearly a floating-point
audio fingerprint, not an ad blocker result. However, the deobs traces the
s21 code path to DOM blocker injection. This is a hard conflict — either the
intercepted payload's key order doesn't match the source code's signal
registration order, or one analysis has a mapping error.

---

## Signals Identified by Only One Analysis

### Only in Data Intercept

| Key | Description |
|-----|-------------|
| `m`, `mo`, `c` | Request mode, modules requested, API key (top-level metadata) |
| `ab` | A/B test bucket |
| `epv` | Endpoint version hash |
| `lr` section | Full operational telemetry: per-signal timing, visibility changes, cache/identification/fallback API attempts, page ID, agent ID |
| `sd` (signal durations) | Millisecond timing for every signal collected |
| Encoding pipeline detail | Full binary layout: baseByte, flags, padding, 9-byte XOR key, payload |

### Only in Deobs

| Key | Description |
|-----|-------------|
| s70 | **TLS fingerprint** — remote resource fetch to `defaultTlsEndpoint` for server-side TLS handshake capture. Data intercept listed this as null/unknown. |
| s106 | Notification permission mismatch (incognito detection). Data intercept listed a different description. |
| s210 | Dynamic/async font detection |
| s211 | Extended font probing / capability flags |
| Module architecture | Three-module system (id, bd, ex) with 3 stages each |
| Obfuscation techniques | Detailed documentation of `Gi()` hash dispatch, `Hi()` encrypted string tables, `Ui()` multi-source tables |
| Function-level tracing | Every signal mapped to its specific deobfuscated function name |
| Canvas rendering detail | Exact text drawn ("Cwm fjordbank gly" + U+1F603), specific operations and composite modes |
| Font probe specifics | All 50 font names tested, baseline fonts, test string, iframe technique |
| Bot detection specifics | Full list of ~30 automation globals checked |
| Ad blocker specifics | ~200 CSS selectors from ~40 named filter lists (EasyList, AdGuard, uBlock, Fanboy, regional) |
| Audio pipeline detail | Triangle oscillator at 10kHz, DynamicsCompressor parameters, 5000 samples at 44.1kHz, sum from sample 4500+ |

---

## Encrypted / Unresolvable Signals

Both analyses identify a set of signals that resist full identification.

| Key | Data Intercept | Deobs |
|-----|---------------|-------|
| s23 | null; "requires Chrome+Safari engine flags" | "Encrypted Gi call on navigator — unknown property" |
| s29 | null; "complex async probe" | "Encrypted Gi call on navigator — unknown property" |
| s50 | null; "runtime-decoded global" | "`navigator.hardwareConcurrency` descriptor validation" |
| s79 | "Browser profile file detection" (based on value) | "Encrypted Gi call — unknown property" |
| s86 | null; "Safari-specific" | "Private/incognito mode detection (context clues)" |
| s89 | null; "250ms timeout, engine-dependent" | "Ad blocker detection result (same technique, in id module)" |
| s95 | null; "500ms timeout, obfuscated" | "Notification permission check (similar to s106)" |
| s97 | null; "500ms timeout, obfuscated" | Not listed |
| s146 | "Scoped variable reference test" | "`objectToInspect` existence" |
| s159 | "Function/Object deletion resilience" | "Encrypted Gi call — unknown property" |
| s162 | "Navigator property via hashed accessor" | "Encrypted Gi call on navigator — unknown property" |
| s167 | null; "storage/cookie persistence" | "Bot fingerprint — encrypted property name table" |

The data intercept approach can see the actual returned value (even if null),
giving clues about what was measured. The deobs approach can identify the
function structure and surrounding code context, but `Gi()` hash-based
property dispatch defeats static analysis for ~12 signals.

---

## Experimental Signals

Both analyses identify 4 experimental signals:

| Key | Data Intercept | Deobs |
|-----|---------------|-------|
| exp_s1013 | null (unavailable) | "Experimental metric" |
| exp_s1014 | null (unavailable) | "Encrypted check via Yu string table" |
| exp_s1015 | Long base64 string — "likely WebGPU or extended canvas" | "Likely WebGL variant" |
| exp_s1016 | `{"b": {"0": 2281898568, "1": 17054720}}` — "hash-based fingerprint" | "Likely GPU detection" |

Agreement: exp_s1015 and exp_s1016 are graphics/GPU-related. Neither analysis
can fully identify them.

---

## Strengths and Weaknesses of Each Method

### Data Intercept (metric-analysis-based-on-data2.md)

**Strengths:**
- Shows the **actual transmitted values**, which can confirm or rule out
  what a signal measures (e.g. s21's float value proves it's audio, not ad
  blocking)
- Captures the full encoding pipeline specification
- Includes operational telemetry (timing, cache, visibility events)
- Provides ground truth for what the server actually receives

**Weaknesses:**
- Signal-to-key mapping is **inferred from values**, which is ambiguous when
  multiple signals return `false`, `null`, or similar-looking data
- Cannot identify signals that returned null (23 signals were null on Firefox)
- Reflects only one browser (Firefox 149) — signals that are Chrome/Safari-only
  appear as empty stubs
- No insight into code structure, obfuscation techniques, or collection logic

### Source Deobfuscation (metric-analysis-from-deobs.md)

**Strengths:**
- Shows exactly **which API each signal calls** and how
- Documents specific parameters: font names, canvas text, math constants,
  audio pipeline settings, automation globals
- Identifies the module architecture (id/bd/ex, 3 stages)
- Documents obfuscation techniques (Gi, Hi, Ui)
- Can identify signals even when they return null on a specific browser
- Provides function-level traceability

**Weaknesses:**
- Signal-to-key mapping may have errors where registration order is complex
  or dynamic (evidenced by the CSS media query and audio conflicts)
- Cannot determine actual runtime values
- Encrypted property dispatch (`Gi` with hashed names) blocks identification
  of ~12 signals
- Deobfuscation may introduce interpretation errors in heavily minified code

---

## Conclusions

1. **The two analyses are largely consistent** on the identity of ~65 signals,
   covering all major categories: navigator properties, screen/display, canvas,
   WebGL (vendor/params), fonts, math, storage, timezone, plugins, touch,
   engine detection, bot detection, and prototype checks.

2. **~20 signals have conflicting key assignments**, concentrated in:
   - CSS media queries (s33, s36, s40, s41, s43 — systematic swap pattern)
   - Audio signals (s21, s22 vs s96)
   - Several individual signals (s30, s76, s87, s92, s93, s94, s154, s203, s209)

3. **The CSS media query mapping conflict is systematic**, suggesting the
   signal registration order in the source code doesn't straightforwardly
   match the key numbering. The data intercept can't easily disambiguate
   signals that all return `false` or `null`, and the deobs may have a
   registration-order error.

4. **For the audio signals, the data intercept is more convincing**: s21's
   value of `35.749...` is unmistakably an audio fingerprint, and s22's value
   of `23` matches a baseLatency reading. The deobs analysis mapped these to
   ad blocking and webdriver respectively, which doesn't match the data.

5. **Each method fills gaps the other can't**: the data intercept provides
   ground truth on values; the deobs provides the implementation detail
   (specific font lists, canvas operations, automation globals checked,
   obfuscation techniques). A combined approach using both is necessary for
   complete coverage.

6. **~12 signals remain unidentified by both analyses** due to runtime
   hash-based property dispatch (`Gi`), which defeats both static analysis
   and value-based inference.
