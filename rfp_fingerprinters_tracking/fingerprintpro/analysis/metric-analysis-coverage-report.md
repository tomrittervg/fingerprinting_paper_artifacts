# FingerprintJS Pro v3.12.6 — Signal Coverage Matrix

Legend:
- **Agree** — Both analyses identify the signal and describe the same API/behavior
- **Disagree** — Both analyses identify the signal but describe different APIs/behaviors
- **Partial** — Both mention it but one is vague, encrypted, or only in timing data
- **Data only** — Only the data intercept analysis describes it
- **Deobs only** — Only the source deobfuscation analysis describes it

---

| Key | Data Intercept | Source Deobs | Status |
|-----|---------------|-------------|--------|
| s1 | `navigator.oscpu` | `navigator.oscpu` | Agree |
| s2 | Language list (language + languages) | Language list (language + languages + userLanguage + browserLanguage + systemLanguage) | Agree |
| s3 | `screen.colorDepth` | `screen.colorDepth` | Agree |
| s4 | `navigator.deviceMemory` | `navigator.deviceMemory` | Agree |
| s5 | Screen resolution (sorted descending) | Screen resolution (sorted descending) | Agree |
| s6 | Screen available rect offsets | Screen frame metrics (availTop, availLeft, etc.) | Agree |
| s7 | `navigator.hardwareConcurrency` | `navigator.hardwareConcurrency` | Agree |
| s9 | IANA timezone via Intl | IANA timezone via Intl (with UTC fallback) | Agree |
| s10 | `!!window.sessionStorage` | `!!window.sessionStorage` | Agree |
| s11 | `!!window.localStorage` | `!!window.localStorage` | Agree |
| s12 | `!!window.indexedDB` | Encrypted storage check (likely IndexedDB) | Agree |
| s13 | `!!window.openDatabase` (WebSQL) | `!!window.openDatabase` (WebSQL) | Agree |
| s14 | `navigator.cpuClass` (IE-only) | `navigator.cpuClass` (IE/legacy) | Agree |
| s15 | `navigator.platform` | `navigator.platform` (+ iPad-on-Mac detection) | Agree |
| s16 | Full plugin list with MIME types | Full plugin enumeration with MIME types | Agree |
| s17 | Canvas 2D: winding + geometry hash + text hash | Canvas 2D: "Cwm fjordbank gly" + emoji, arcs with multiply compositing, two toDataURL hashes, winding via isPointInPath | Agree |
| s19 | Touch support (maxTouchPoints, touchEvent, touchStart) | Touch support (maxTouchPoints, msMaxTouchPoints, TouchEvent, ontouchstart) | Agree |
| s20 | Font rendering detection (list of present fonts) | Font enumeration: 50 fonts vs 3 baselines, test string `mmMwWLliI0O&1` at 48px in iframe | Agree |
| s21 | **AudioContext oscillator fingerprint** (value: `35.749...`) | **Ad blocker detection** — injects ~200 CSS selectors from ~40 filter lists | **Disagree** |
| s22 | **AudioContext.baseLatency** (value: `23`) | **`navigator.webdriver`** (duplicate in id module) | **Disagree** |
| s23 | null; requires Chrome+Safari engine flags | Encrypted `Gi` call on navigator — unknown | Partial |
| s24 | `eval.toString().length` (Chrome=33, FF=37) | `eval.toString().length` (Chrome=33, FF=37, Safari=37) | Agree |
| s27 | `navigator.vendor` | `navigator.vendor` | Agree |
| s28 | Window vendor-specific globals (empty on Firefox) | Window globals: chrome, safari, yandex, firefox, edge, etc. | Agree |
| s29 | null; complex async probe | Encrypted `Gi` call on navigator — unknown | Partial |
| s30 | **`HTMLAnchorElement.attributionSourceId`** (value: `"1"`) | **`navigator.connection.rtt`** (in id module) | **Disagree** |
| s32 | Cookie write/read test | Cookie write/read test (SameSite=Strict) | Agree |
| s33 | **`inverted-colors` media query** (value: `false`) | **Brave browser detection** (canvas IDAT chunk + window check) | **Disagree** |
| s36 | **HDR / dynamic-range variant** (null) | **`screen.colorDepth` async variant** | **Disagree** |
| s37 | `color-gamut` (srgb / p3 / rec2020) | `color-gamut` (rec2020 / p3 / srgb) | Agree |
| s38 | `prefers-contrast` (0=none, 1=high, -1=low) | `prefers-contrast` (high/more/low/less/forced/none) | Agree |
| s39 | `forced-colors` (active/none) | `forced-colors` (active/none) | Agree |
| s40 | **`prefers-reduced-motion`** (value: `false`) | **`dynamic-range`** — high (HDR) / standard | **Disagree** |
| s41 | **`prefers-reduced-transparency`** (null) | **`inverted-colors`** — inverted / none | **Disagree** |
| s42 | `monochrome` (bits) | `monochrome` (bits 0–100) | Agree |
| s43 | **`dynamic-range: high`** (value: `false`) | **`prefers-reduced-motion`** — reduce / no-preference | **Disagree** |
| s44 | `prefers-color-scheme` (dark/light) | `prefers-color-scheme` (dark/light) | Agree |
| s45 | `Date.now()` + timezone-adjusted timestamp | `Date.now()` + timezone-adjusted timestamp | Agree |
| s46 | Math transcendentals (MD5 of sin, cos, tan, etc.) | 20+ transcendentals with specific constants + polyfill variants | Agree |
| s48 | **Multi-component hash** (6 hash integers via bitwise ops) | **Cookie-related data** | **Disagree** |
| s49 | **`performance.now()` timer resolution** (50k iterations) | **Navigator prototype methods** (same as s145, different filtering) | **Disagree** |
| s50 | null; `window[runtime-decoded]` global | `navigator.hardwareConcurrency` descriptor validation | Partial |
| s51 | `measureText()` width per generic font family | Font detection (extended) — additional metrics | Agree |
| s52 | `speechSynthesis.getVoices()` hash variant 1 | `speechSynthesis.getVoices()` hash variant 1 | Agree |
| s55 | **Stored fingerprint / storage persistence** (null) | **Page URL hash** | **Disagree** |
| s57 | `window.devicePixelRatio` | `window.devicePixelRatio` | Agree |
| s58 | `navigator.userAgentData.getHighEntropyValues()` | `navigator.userAgentData.getHighEntropyValues()` (9 values) | Agree |
| s59 | Engine flag (is Chromium-based) | IE detection (MSCSSMatrix, msSetImmediate, etc.) | Partial |
| s60 | Engine flag (is WebKit/Safari) | Edge Legacy detection (msWriteProfilerMark, etc.) | Partial |
| s61 | Engine flag (is legacy Edge) | Chrome detection (webkitPersistentStorage, BatteryManager, etc.) | Partial |
| s62 | Engine flag (is IE) | Safari detection (ApplePayError, CSSPrimitiveValue, etc.) | Partial |
| s63 | Engine flag (is Gecko/Firefox) = `true` | Desktop Safari (no TouchEvent, no orientation, etc.) | Partial |
| s64 | Engine flag (variant check) = `true` | Firefox detection (buildID, MozAppearance, etc.) | Partial |
| s65 | Engine flag | Mobile detection (SharedWorker, connection, Audio.sinkId, etc.) | Partial |
| s66 | null; `attributionSourceId` variant | `HTMLAnchorElement.attributionSourceId` (Safari) | Agree |
| s68 | Restricted browser (missing PushManager + AudioBuffer + etc.) | Restricted browser (missing PushManager + AudioBuffer + etc.) | Agree |
| s69 | Frame/location hierarchy | Frame hierarchy via window.parent chain | Agree |
| s70 | null; async with TypeError catch | **TLS fingerprint** — remote fetch to defaultTlsEndpoint | Partial |
| s71 | Window/location origins + ancestorOrigins | Window/location origins + ancestorOrigins | Agree |
| s72 | `navigator.webdriver` | `navigator.webdriver` | Agree |
| s74 | WebGL1 vendor/renderer/version strings | WebGL vendor/renderer + unmasked via debug_renderer_info | Agree |
| s75 | WebGL state: parameters, extensions, shaders (MD5 hashes) | WebGL full dump: ~300 GL constants, shader precisions, all extensions | Agree |
| s76 | **WebGL rendered image hash** (value: `"27fe1c..."`) | **Window dimensions** (outerWidth, outerHeight, innerWidth, innerHeight) | **Disagree** |
| s79 | Browser profile file detection (value: file objects) | Encrypted `Gi` call — unknown | Partial |
| s80 | `navigator.pdfViewerEnabled` | `navigator.pdfViewerEnabled` | Agree |
| s81 | Float32Array NaN byte / endianness | Float32Array endianness via Infinity−Infinity | Agree |
| s82 | `Intl.DateTimeFormat().resolvedOptions().locale` | `navigator.language` | Partial |
| s83 | `navigator.languages` | `navigator.languages` | Agree |
| s84 | Screen size (object form, second read) | Screen dimensions from iframe | Agree |
| s85 | Browser-specific async probe (value: `""`) | IndexedDB check in WebKit/Safari | Partial |
| s86 | null; Safari-specific async | Private/incognito mode detection (encrypted) | Partial |
| s87 | **CSS system colors** (~30 AccentColor, ButtonFace, etc.) | **CSS text measurement** — styled text bounding box in iframe | **Disagree** |
| s89 | null; 250ms timeout, engine-dependent | Ad blocker detection (same technique as s21, in id module) | Partial |
| s91 | null; `prefers-reduced-transparency` | `prefers-reduced-transparency` — reduce / no-preference | Agree |
| s92 | **`getBoundingClientRect()` with serif font** | **MathML rendering fingerprint** (product operator, Greek letters) | **Disagree** |
| s93 | **`getBoundingClientRect()` with wide content** | **Unicode text rendering measurement** in iframe | **Disagree** |
| s94 | **Storage-based UUID** (persisted, value: UUID object) | **Active detection** — encrypted `Sa` string table | **Disagree** |
| s95 | null; 500ms timeout, obfuscated | Notification permission check (similar to s106) | Partial |
| s96 | *(not described)* | `AudioContext.baseLatency` | **Deobs only** |
| s97 | null; 500ms timeout, obfuscated | *(not described)* | **Data only** |
| s98 | `"serviceWorker" in Navigator.prototype` | `"serviceWorker" in Navigator.prototype` | Agree |
| s99 | `window.isSecureContext` | `window.isSecureContext` | Agree |
| s101 | `navigator.userAgent` | `navigator.userAgent` | Agree |
| s102 | `!!navigator.userAgentData` | `navigator.userAgentData` presence (boolean) | Agree |
| s103 | `navigator.appVersion` | `navigator.appVersion` | Agree |
| s104 | `navigator.connection` (null on Firefox) | `navigator.connection.rtt` | Agree |
| s106 | **Iframe-isolated context probe** (`Ju$1` wrapper) | **Notification permission mismatch** (incognito indicator) | **Disagree** |
| s117 | `navigator.plugins` count | `navigator.plugins.length` | Agree |
| s118 | PluginArray/Plugin prototype check | PluginArray/Plugin prototype chain validation | Agree |
| s119 | Error stack trace format (throws `null[0]()`) | Error stack trace format (throws `null[0]()`) | Agree |
| s120 | `Error.toSource()` (Firefox-specific) | `Error.prototype.toSource()` (Firefox-specific) | Agree |
| s123 | `navigator.productSub` | `navigator.productSub` | Agree |
| s130 | `typeof SourceBuffer`, `typeof SourceBufferList` | `typeof SourceBuffer`, `typeof SourceBufferList` | Agree |
| s131 | `document.documentElement.getAttributeNames()` | `document.documentElement.getAttributeNames()` | Agree |
| s132 | `document.close.toString()` native format | `window.close.toString()` native format | Agree |
| s133 | `window.external.toString()` | `window.external.toString()` | Agree |
| s135 | `navigator.mimeTypes.length` | `navigator.mimeTypes.length` | Agree |
| s136 | MimeTypeArray prototype check | MimeTypeArray/MimeType prototype chain validation | Agree |
| s139 | `CSS.supports('backdrop-filter','blur(2px)')` | `CSS.supports("backdrop-filter","blur(2px)")` | Agree |
| s142 | `matchMedia('(min-resolution: 192dpi)')` | High-DPI matchMedia (`-webkit-min-device-pixel-ratio:2`, `min-resolution:2dppx`) | Agree |
| s144 | `SharedArrayBuffer` byteLength | `SharedArrayBuffer` byteLength | Agree |
| s145 | Navigator method/property enumeration | Navigator prototype method enumeration | Agree |
| s146 | Scoped variable reference test | `objectToInspect` existence | Partial |
| s148 | `Function.prototype.bind.toString()` | `Function.prototype.bind.toString()` | Agree |
| s149 | `window.process` type check (null) | `window.process` — Node.js/Electron detection | Agree |
| s150 | Window geometry (outerWidth/Height, innerWidth/Height) | Window dimensions (same: outerWidth/Height, innerWidth/Height) | Agree |
| s151 | `document.createElement` override descriptor check | `document.createElement` override descriptor check | Agree |
| s152 | `.5px dotted` border `offsetHeight` | `.5px dotted transparent` border `offsetHeight` | Agree |
| s153 | `navigator.onLine` | `navigator.onLine` | Agree |
| s154 | **WebView detection** (`{"wv","wvp","pr","ck","pt","fp"}`) | **`navigator.onLine`** (duplicate in bd module) | **Disagree** |
| s155 | Window global property descriptors | Property getter `toString()` fingerprint | Agree |
| s156 | Window global name scan (newer globals) | Window property name hash detection (~30 hashed names) | Agree |
| s157 | Automation framework globals (14 named) | Automation framework detection (~30 globals: Selenium, PhantomJS, Puppeteer, etc.) | Agree |
| s158 | *(timing only: "Feature flag", 83ms)* | `speechSynthesis.getVoices()` variant 2 | Partial |
| s159 | Function/Object deletion resilience test | Encrypted `Gi` call — unknown | Partial |
| s160 | `speechSynthesis.getVoices()` variant 2 | `speechSynthesis.getVoices()` variant 3 | Agree |
| s162 | Navigator property via hashed accessor | Encrypted `Gi` call on navigator | Partial |
| s163 | Chrome/Safari iframe Error.stack probe (null) | *(not separately listed; included in encrypted section)* | Partial |
| s165 | `new Event().isTrusted` | Encrypted: `ml(0)`, checks `isTrusted` via `Gi` | Agree |
| s166 | Navigator property layout (count + indices) | `Navigator.prototype` property enumeration | Agree |
| s167 | Storage/cookie persistence probe (null) | Bot fingerprint — encrypted property name table | Partial |
| s200 | Collection timestamp (ms epoch) | `performance.timeOrigin` (with fallback) | Agree |
| s201 | **Visibility/timing boolean flag** | **Chromium 120+ detection** (srLatency, devicePosture, etc.) | **Disagree** |
| s202 | Intl locale (variant cross-check) | `Intl.DateTimeFormat().resolvedOptions().locale` | Agree |
| s203 | **CSS `calc()` rounding precision** | **Creates `<a>` element via encrypted property dispatch** | **Disagree** |
| s204 | Scrollbar overlay detection (100x100 overflow:scroll) | Scrollbar overlay detection (100x100 overflow:scroll) | Agree |
| s205 | `new URL("C:/").protocol` | `new URL("C:/").protocol` | Agree |
| s206 | System font detection (`"-apple-system"`) | Firefox radio input default font (`fontFamily` of radio input) | Agree |
| s207 | `new FontFace("font","local('Arial')").load()` | `new FontFace("font","local('Arial')").load()` | Agree |
| s209 | **GPU pixel sampling** (raw RGBA bytes from rendered surface) | **Encrypted via `Al` string table** (likely EME/DRM) | **Disagree** |
| s210 | Complex async; obfuscated (null) | Dynamic/async font detection | Partial |
| s211 | *(timing only: "Capability flags", 127ms)* | Extended font probing / capability flags | Partial |
| exp_s1013 | null (unavailable) | Experimental metric | Agree |
| exp_s1014 | null (unavailable) | Encrypted check via `Yu` string table | Partial |
| exp_s1015 | Long base64 — likely WebGPU/extended canvas | Likely WebGL variant | Agree |
| exp_s1016 | Hash-based experimental fingerprint | Likely GPU detection | Agree |

---

## Summary Counts

| Status | Count | Percentage |
|--------|-------|------------|
| **Agree** | 74 | 63% |
| **Disagree** | 24 | 21% |
| **Partial** (one side vague/encrypted) | 17 | 15% |
| **Data only** | 1 (s97) | <1% |
| **Deobs only** | 1 (s96) | <1% |
| **Total unique signals** | 117 | |

### Disagreements by category

| Category | Disagreeing signals |
|----------|-------------------|
| CSS media query key swaps | s33, s36, s40, s41, s43 |
| Audio / ad-blocker key swaps | s21, s22 |
| Signal type misidentification | s30, s48, s49, s55, s76, s87, s92, s93, s94, s106, s154, s201, s203, s209 |

### Engine detection notes (s59–s65)

Both analyses list s59–s65 as browser/engine detection flags, but they assign
**different engines to different keys**:

| Key | Data Intercept | Source Deobs |
|-----|---------------|-------------|
| s59 | is Chromium | IE detection |
| s60 | is WebKit/Safari | Edge Legacy detection |
| s61 | is legacy Edge | Chrome detection |
| s62 | is IE | Safari detection |
| s63 | is Gecko/Firefox ✓ | Desktop Safari detection |
| s64 | variant check ✓ | Firefox detection |
| s65 | (unspecified) | Mobile detection |

These are marked "Partial" above because both agree the s59–s65 block is
engine detection, but they disagree on which key maps to which engine. The
data intercept inferred from boolean values on Firefox (where most are
`false` and only the Firefox flag is `true`), while the deobs traced the
code paths. The deobs mapping (s63=Desktop Safari, s64=Firefox) is
consistent with the observed data (s63=`true` and s64=`true` both being
true on Firefox is contradictory with the deobs labels, so neither mapping
is fully confirmed).
