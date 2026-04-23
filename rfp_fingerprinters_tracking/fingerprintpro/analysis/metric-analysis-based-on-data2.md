# FingerprintJS Pro v3.12.6 — Metric Analysis

Decoded from an intercepted XHR payload to `api.fpjs.io`. The library
collects all signals client-side, encodes them into a custom binary JSON
format, deflate-compresses the result, XOR-encrypts it with a random
embedded key, and POSTs the opaque blob. The data below was recovered by
reversing that pipeline.

Every signal uses the envelope `{s: <status>, v: <value>}`.
Status codes: `0` = success, `-1` = API unavailable, `-2` = missing
prerequisite, `-3` = unexpected behaviour, `-5` = server error.

---

## Top-level metadata

| Key | Example value | Meaning |
|-----|---------------|---------|
| `c` | `"xx-fpjs-api-token-xx"` | Customer API key |
| `m` | `"e"` | Request mode (`"e"` = error/retry) |
| `mo` | `["bd","ex","id"]` | Modules requested (bot detection, extended, identification) |
| `sc.u` | script URL | URL the library was loaded from |
| `url` | page URL | Page that triggered collection |
| `cr` | referrer | HTTP Referer |
| `ii` | `[]` | Integration info |
| `gt` | `1` | `get()` call attempt number |
| `epv` | `"df994e8"` | Endpoint version hash |
| `ab` | `{"noop":"b"}` | A/B test bucket |
| `lr` | array of objects | Log records — telemetry for every `get()` call (see section at end) |

---

## Fingerprint signals

### Browser & OS identity

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s1` | `navigator.oscpu` | `"Intel Mac OS X 10.15"` | OS/CPU string (Firefox-specific) |
| `s15` | `navigator.platform` | `"MacIntel"` | Platform identifier |
| `s101` | `navigator.userAgent` | `"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:149.0) Gecko/20100101 Firefox/149.0"` | Full User-Agent string |
| `s103` | `navigator.appVersion` | `"5.0 (Macintosh)"` | App version string |
| `s123` | `navigator.productSub` | `"20100101"` | Build date string |
| `s27` | `navigator.vendor` | `""` | Vendor string (empty on Firefox, `"Google Inc."` on Chrome) |

### Language & locale

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s2` | `navigator.language` + `navigator.languages` | `[["en-US"],["en-US"]]` | Language preferences (two sources) |
| `s82` | `Intl.DateTimeFormat().resolvedOptions().locale` | `"en-US"` | Resolved Intl locale |
| `s83` | `navigator.languages` | `["en-US"]` | Language list (direct read) |
| `s202` | Intl locale (variant) | `"en-US"` | Additional locale cross-check |

### Timezone

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s9` | `Intl.DateTimeFormat().resolvedOptions().timeZone` | `"America/New_York"` | IANA timezone string |

### Screen & display

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s5` | `screen.width`, `screen.height` | `[1680, 1050]` | Screen resolution (sorted descending) |
| `s6` | Screen available rect offsets | `[0, 0, 76, 0]` | Taskbar/dock offsets (availTop, availLeft, etc.) |
| `s3` | `screen.colorDepth` | `30` | Color depth in bits |
| `s84` | `screen.width`, `screen.height` | `{"w": 1680, "h": 1050}` | Screen size (object form, second read) |
| `s150` | `window.outerWidth/Height`, `window.innerWidth/Height` | `{"outerWidth": 1680, "outerHeight": 940, "innerWidth": 1370, "innerHeight": 856}` | Window geometry (reveals toolbar/devtools size) |

### Hardware

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s7` | `navigator.hardwareConcurrency` | `4` | CPU logical core count |
| `s4` | `navigator.deviceMemory` | `null` | Device RAM in GB (Chrome-only; Firefox returns null) |
| `s14` | `navigator.cpuClass` | `null` | CPU class (IE-only) |

### Storage support

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s10` | `!!window.sessionStorage` | `true` | Session storage available |
| `s11` | `!!window.localStorage` | `true` | Local storage available |
| `s12` | `!!window.indexedDB` | `true` | IndexedDB available |
| `s13` | `!!window.openDatabase` | `false` | Web SQL available (deprecated; Chrome-only) |
| `s32` | Cookie write test | `true` | Can set and read back a cookie |

### Touch & input

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s19` | Touch API probes | `{"maxTouchPoints": 0, "touchEvent": false, "touchStart": false}` | Touch support detection |

### Plugins & MIME types

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s16` | `navigator.plugins` | 5 PDF viewer entries | Full plugin list with MIME types |
| `s117` | Plugin/MIME count | `5` | Number of plugins |
| `s135` | `navigator.mimeTypes.length` | `2` | MIME type count |
| `s136` | MimeTypeArray prototype check | `true` | `Object.getPrototypeOf(mimeTypes) === MimeTypeArray.prototype` |
| `s118` | MimeType prototype validation | `true` | Per-entry prototype chain check |
| `s80` | `navigator.pdfViewerEnabled` | `true` | PDF viewer flag |

### Canvas fingerprinting

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s17` | Canvas 2D rendering | `{"winding": true, "geometry": "a75b38...", "text": "2013bb..."}` | Canvas winding rule support + MD5 hashes of rendered geometry and text |

### WebGL fingerprinting

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s74` | WebGL1 `getParameter()` | `{"version": "WebGL 1.0", "vendor": "Mozilla", "vendorUnmasked": "", "renderer": "Radeon R9 200 Series, or similar", "rendererUnmasked": "", "shadingLanguageVersion": "WebGL GLSL ES 1.0"}` | GPU identity strings |
| `s75` | WebGL state hashing | `{"contextAttributes": "48e630...", "parameters": "075059...", "shaderPrecisions": "1aabf5...", "extensions": "1a3d1a...", ...}` | MD5 hashes of all WebGL parameters, extensions, shader precisions |
| `s76` | WebGL rendered image hash | `"27fe1c..."` | Hash of a rendered WebGL scene |
| `s209` | GPU pixel sampling | `{"s": [4 hash ints], "p": [64 RGBA bytes], "d": 4}` | Raw pixel data from a rendered surface |

### Audio fingerprinting

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s21` | AudioContext oscillator | `35.749972093850374` | Audio processing pipeline fingerprint (OscillatorNode → DynamicsCompressorNode → AnalyserNode) |
| `s22` | `AudioContext.baseLatency` | `23` | Audio output latency |

### Font fingerprinting

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s20` | Font rendering detection | `["Arial Unicode MS", "Gill Sans", "Helvetica Neue", "Menlo"]` | Fonts confirmed present via rendering comparison |
| `s51` | Text width measurement | `{"default": 147.58, "apple": 147.58, "serif": 147.58, "sans": 144.01, "mono": 133.16, "min": 9.23, "system": 146}` | `measureText()` width per generic font family |
| `s206` | System font detection | `"-apple-system"` | Resolved system UI font |
| `s92` | `getBoundingClientRect()` (serif) | `{"x": 8, "y": 10.5, "width": 285.7, "height": 16, ...}` | Text bounding rect with serif font |
| `s93` | `getBoundingClientRect()` (wide) | `{"x": 8, "y": 12, "width": 1280, "height": 16, ...}` | Text bounding rect with different content |
| `s24` | `eval.toString().length` | `37` | Length of `eval.toString()` — differs per engine (Chrome=33, Firefox=37, Safari=37) |

### Math fingerprint

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s46` | Math transcendental functions | `"5f030fa7d2e5f9f757bfaf81642eb1a6"` | MD5 of `Math.sin(-1e300)`, `Math.cos(10.000000000123)`, `Math.tan(-1e300)`, `Math.acos(0.123...)`, `Math.sinh(1)`, `Math.exp(1)`, `Math.log1p(10)`, `Math.pow(PI, -100)`, etc. |

### CSS media queries

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s37` | `(color-gamut: *)` | `"srgb"` | Display color gamut (srgb / p3 / rec2020) |
| `s33` | `(inverted-colors: inverted)` | `false` | Inverted colors accessibility setting |
| `s38` | `(prefers-contrast: *)` | `0` | Contrast preference (0=no-preference, 1=high, -1=low) |
| `s39` | `(forced-colors: active)` | `false` | Windows high-contrast mode |
| `s40` | `(prefers-reduced-motion: reduce)` | `false` | Reduced motion preference |
| `s41` | `(prefers-reduced-transparency: reduce)` | `null` | Reduced transparency preference |
| `s42` | `(monochrome: *)` | `0` | Monochrome display depth |
| `s43` | `(dynamic-range: high)` | `false` | HDR display capability |
| `s36` | HDR detection (variant) | `null` | Additional HDR check |

### CSS system colors

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s87` | `getComputedStyle` of CSS system color keywords | Object with ~30 color values | System theme colors. Keys map to CSS keywords: `ac`=AccentColor, `act`=AccentColorText, `at`=ActiveText, `ab`=ActiveBorder (deprecated), `b`=ButtonFace variant, `bt`=ButtonText, `ft`=FieldText, `h`=Highlight, `ht`=HighlightText, `lt`=LinkText, `vt`=VisitedText, `m`=Mark, etc. Reveals OS theme and dark/light mode. |

### CSS precision fingerprint

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s203` | CSS `calc()` rounding | `"calc(-0.0773484px)"` | Computed value of a CSS `calc()` expression; sub-pixel rounding differs across browser engines |
| `s205` | CSS string probe | `"c:"` | Short CSS-based identifier |

### Browser engine detection (boolean flags)

| Signal | Example value | Description |
|--------|---------------|-------------|
| `s59` | `false` | Engine detection flag (is Chromium-based) |
| `s60` | `false` | Engine detection flag (is WebKit/Safari) |
| `s61` | `false` | Engine detection flag (is legacy Edge) |
| `s62` | `false` | Engine detection flag (is IE) |
| `s63` | `true` | Engine detection flag (is Gecko/Firefox) |
| `s64` | `true` | Engine detection flag (variant check) |
| `s65` | `false` | Engine detection flag |
| `s68` | `false` | Engine detection flag (Brave-specific) |
| `s72` | `navigator.webdriver` | `false` | WebDriver automation flag |
| `s57` | `window.devicePixelRatio` | `2` | Device pixel ratio |

### Navigator API surface fingerprinting

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s145` | Navigator method/property enumeration | `["javaEnabled", "getGamepads", "", "requestMediaKeySystemAccess", "getAutoplayPolicy", "taintEnabled", "Navigator"]` | Lists specific navigator methods — their presence/absence and order is browser-specific |
| `s166` | Navigator property layout | `{"l": 35, "p": [{"i": 1, "n": "getGamepads"}, {"i": 22, "n": "webdriver"}, {"i": 33, "n": "onLine"}]}` | Total property count and positional indices of specific properties — reveals prototype chain differences |
| `s131` | `document.documentElement.getAttributeNames()` | `["lang"]` | HTML root element attributes |
| `s130` | `window.process` type check | `["function", "function"]` | Checks for Node.js process object (Electron detection) |
| `s133` | `window.external.toString()` | `"[object External]"` | External interface string representation |
| `s148` | `Function.prototype.bind.toString()` | `"function bind() {\n    [native code]\n}"` | Native function toString format (differs across engines) |
| `s132` | `document.close.toString()` | `"function close() {\n    [native code]\n}"` | Native function string format check |
| `s119` | Error stack trace format | stack string with function names | Throws `null[0]()` and captures the stack trace — format reveals engine and source mapping |

### Bot & automation detection

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s157` | Window/navigator property probes | `{"awesomium": false, "cef": false, "cefsharp": false, "coachjs": false, "fminer": false, "geb": false, "nightmarejs": false, "phantomas": false, "phantomjs": false, "rhino": false, "selenium": false, "webdriverio": false, "webdriver": false, "headless_chrome": false}` | Checks for 14 automation framework globals |
| `s154` | WebView detection | `{"wv": false, "wvp": false, "pr": false, "ck": true, "pt": false, "fp": false}` | In-app webview indicators (Facebook, Instagram, etc.) |
| `s165` | `new Event().isTrusted` | `{"isTrusted": false}` | Checks if synthetically created events report as trusted |

### Vendor-specific window properties

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s28` | Window property enumeration | `[]` | Vendor-specific window properties (ad blocker detection) |
| `s71` | Window/location origins | `{"w": "http://...", "l": "http://...", "a": []}` | Window origin, location origin, ancestor origins |
| `s69` | Frame/location hierarchy | `[{"l": "page URL", "f": "parent frame URL"}]` | Location and frame ancestor chain |
| `s156` | Global object detection | `["Iterator"]` | Checks for presence of specific newer globals |

### High-entropy User-Agent Client Hints

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s58` | `navigator.userAgentData.getHighEntropyValues()` | `null` | Chromium UA-CH API (brands, platform, architecture, bitness, model, fullVersionList). Firefox returns null. |
| `s104` | `navigator.connection` | `null` | Network Information API (effectiveType, downlink, rtt). Firefox returns null. |

### Persistent identifiers

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s94` | Storage-based UUID | `{"u": "a53af0f6-fce5-042a-8043-8cd2c3160b31", "e": [], "s": []}` | Generates a UUID and persists it across visits via multiple storage mechanisms |
| `s79` | Browser profile file detection | `[{"n": "default.ini", "l": 2332499772}]` | Probes for known browser profile files/configs (reveals profile age or identity) |
| `s45` | Timestamps | `[1770400830599, 1770382830599]` | Performance timing values (potentially used for clock skew or uptime) |
| `s200` | Collection timestamp | `1770400830290` | Millisecond timestamp of fingerprint collection |

### Color scheme

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s44` | `matchMedia('(prefers-color-scheme: dark/light)')` | `false` | Dark mode active (`true`=dark, `false`=light, `null`=unknown) |

### Timing & performance probes

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s49` | `performance.now()` timer resolution | `[1, 1]` | Runs 50k iterations of `performance.now()`, records the two smallest observed deltas. Reveals timer precision clamping (privacy protections reduce resolution). |
| `s45` | `Date.now()` + timezone offset | `[1770400830599, 1770382830599]` | Current timestamp and timezone-adjusted timestamp |

### Speech synthesis fingerprint

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s52` | `speechSynthesis.getVoices()` | `"e3926e1e..."` | Hash of available TTS voices (variant 1 via `Mc` voice list) |
| `s160` | `speechSynthesis.getVoices()` | `false` | Hash of available TTS voices (variant 2 via `Fc` voice list) |

### Hash / combined fingerprint signals

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s48` | Multi-component hash | `[-1002408801, 431892172, ...]` | Array of 6 hash integers — combined fingerprint from multiple signals using bitwise operations |

### URL & protocol probes

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s30` | `HTMLAnchorElement.attributionSourceId` | `"1"` | Attribution Reporting API support |
| `s205` | `new URL("C:/").protocol` | `"c:"` | URL protocol parsing behaviour — how the browser handles non-standard schemes |

### Numeric / byte-level probes

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s81` | `Float32Array` NaN byte | `255` | Sets `float[0] = Infinity - Infinity` (NaN), reads `Uint8Array[3]` — reveals FP byte representation / endianness |
| `s24` | `eval.toString().length` | `37` | Length of `eval.toString()` — Chrome=33, Firefox=37, Safari=37 |

### Feature & API support detection

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s57` | `window.devicePixelRatio` | `2` | Device pixel ratio |
| `s72` | `navigator.webdriver` | `false` | WebDriver automation flag (`null`→`s:-1`, `undefined`→`s:-2`, otherwise value) |
| `s85` | Browser-specific async probe | `""` | Engine-specific string from `sn`/`ln` checks + async `Ts` probe |
| `s98` | `"serviceWorker" in Navigator.prototype` | `false` | ServiceWorker on Navigator prototype chain |
| `s99` | `window.isSecureContext` | `false` | Secure context (HTTPS) |
| `s102` | `!!navigator.userAgentData` | `false` | UA Client Hints API present (Chrome-only) |
| `s106` | Iframe-isolated context probe | `true` | Runs `hi` collector inside an isolated iframe (`Ju$1` wrapper) — cross-context consistency check |
| `s118` | `PluginArray`/`Plugin` prototype check | `true` | Validates `Object.getPrototypeOf(plugins[i]) === Plugin.prototype` for each plugin — tampering detection |
| `s120` | `Error.toSource()` | `false` | Firefox-specific — `true` if `Error.toSource()` exists |
| `s130` | `typeof SourceBuffer`, `typeof SourceBufferList` | `["function","function"]` | Media Source Extensions API types |
| `s139` | `CSS.supports('backdrop-filter','blur(2px)')` | `true` | CSS backdrop-filter support |
| `s142` | `matchMedia('(min-resolution: 192dpi)')` | `true` | High-DPI / Retina display detection |
| `s144` | `new SharedArrayBuffer(1).byteLength` | `null` | SharedArrayBuffer availability — blocked without cross-origin isolation |
| `s146` | Scoped variable reference test | `false` | Tests if a specific undeclared variable throws — debugger/devtools detection |
| `s151` | `Object.getOwnPropertyDescriptor(document, 'createElement')` | `null` | Checks if `document.createElement` has been overridden (tampering detection) |
| `s152` | `.5px dotted border` `offsetHeight` | `1` | Renders a `0.5px dotted` border, reads `offsetHeight` — sub-pixel rendering differs across engines |
| `s153` | `navigator.onLine` | `true` | Online status |
| `s155` | `Object.getOwnPropertyDescriptor` of window globals | `{}` | Checks property descriptors of specific window properties via `qs(0)` — detects overrides/polyfills |
| `s156` | Window global name scan | `["Iterator"]` | Scans `Object.getOwnPropertyNames(window)` for specific newer global names (e.g. `Iterator`) |
| `s158` | `navigator.webdriver` (iframe context) | `false` | Reads `navigator.webdriver` inside an isolated iframe — detects inconsistent webdriver state |
| `s159` | `Function`/`Object` deletion resilience test | `false` | Temporarily deletes `window.Function` and `window.Object`, checks if property descriptors still behave natively — tampering detection |
| `s162` | Navigator property (obfuscated hash) | `false` | Reads a navigator property via `Gi` hashed accessor — runtime-decoded name |
| `s201` | Visibility/timing flag | `false` | Boolean from `mn` — `(n,t) => n(t)` combinator wrapper; exact probe obfuscated |
| `s204` | Scrollbar rendering test (iframe) | `true` | Creates 100x100 `overflow:scroll` div in iframe, compares `clientWidth` vs `offsetWidth` — overlay vs classic scrollbar detection |
| `s207` | `FontFace` local font load | `true` | `new FontFace("font","local('Arial')").load()` — tests CSS Font Loading API |
| `s211` | Multi-probe capability flags | `[3,7,7,7,7,7,7,7]` | Array of 8 integers from multiple feature probes — version/capability encoding |

### Restricted browser detection (s68)

| Signal | Collected API | Example value | Description |
|--------|--------------|---------------|-------------|
| `s68` | `!PushManager && !AudioBuffer && !RTCPeerConnection && !geolocation && !ServiceWorker` | `false` | Detects restricted/embedded browsers — `true` if >=3 of these APIs are missing |

### Still-unidentified signals

These use heavy combinator-style obfuscation (`Gi` runtime hashed
property accessor) that defeats static analysis. The function bodies
are syntactically readable but all property/method names are computed
at runtime from integer hash seeds.

| Signal | Function | Example value | Notes |
|--------|----------|---------------|-------|
| `s23` | `Is` | `null` | Async; requires Chrome+Safari engine flags; null on Firefox |
| `s29` | `Ss` | `null` | Complex async probe with multiple engine checks |
| `s50` | `Oc` | `null` | Accesses `window[Tc[0]]` — runtime-decoded global |
| `s55` | `Yl` | `null` | Storage probe via `so(n)` — likely a stored fingerprint cookie/localStorage check |
| `s70` | `rl` | `null` | Async with `TypeError` catch; likely CSP or security context probe |
| `s86` | `Os` | `null` | Safari-specific async probe (checks `sn` and `Fr` flags) |
| `s89` | `Yc` | `null` | Async with 250ms timeout; engine-dependent |
| `s91` | `pt` | `null` | `prefers-reduced-transparency: reduce` media query (limited browser support) |
| `s95` | `Wa` | `null` | Async 500ms timeout; checks `Ma` flag; heavily obfuscated body |
| `s97` | `Ba` | `null` | Async 500ms timeout; checks `Ga`, `Qc` conditions; heavily obfuscated |
| `s163` | `al` | `null` | Chrome/Safari only; iframe-based `Error` construction — likely Error.stack format in isolated context |
| `s167` | `pl` | `null` | Uses `esc` flag + `gl`/`Ns` helpers; likely storage/cookie persistence probe |
| `s210` | `Ol` | `null` | Complex async; reads from `ol` data source, iterates `xl` property list; likely expanded hardware/GPU info via obfuscated path |

### Experimental signals

| Signal | Example value | Description |
|--------|---------------|-------------|
| `exp_s1013` | `null` | Experimental signal (unavailable) |
| `exp_s1014` | `null` | Experimental signal (unavailable) |
| `exp_s1015` | Long base64 string | Large encoded payload — likely WebGPU rendering fingerprint or extended canvas data |
| `exp_s1016` | `{"b": {"0": 2281898568, "1": 17054720}}` | Hash-based experimental fingerprint |

### Signals returning null (unavailable in Firefox 149)

These signals were collected but returned null, indicating Firefox does
not expose the underlying API or the signal requires a different engine:

- `s4` — `navigator.deviceMemory` (Chrome-only)
- `s14` — `navigator.cpuClass` (IE-only)
- `s23` — `Is`: async probe requiring Chrome+Safari engine flags
- `s29` — `Ss`: complex async probe with engine checks
- `s36` — HDR / `dynamic-range` media query
- `s41` — `prefers-reduced-transparency` media query
- `s50` — `Oc`: runtime-decoded global property access
- `s55` — `Yl`: stored fingerprint / storage persistence check
- `s58` — `navigator.userAgentData` (Chrome-only UA Client Hints)
- `s66` — `HTMLAnchorElement.attributionSourceId` variant
- `s86` — `Os`: Safari-specific API probe
- `s89` — `Yc`: 250ms async probe, engine-dependent
- `s91` — `prefers-reduced-transparency: reduce`
- `s95` — `Wa`: 500ms async, obfuscated body
- `s97` — `Ba`: 500ms async, obfuscated body
- `s104` — `navigator.connection` (Chrome-only Network Info API)
- `s144` — `SharedArrayBuffer` (requires cross-origin isolation)
- `s149` — `window.process` (Node.js/Electron-only)
- `s151` — `document.createElement` override check
- `s163` — `al`: Chrome/Safari iframe Error.stack probe
- `s167` — `pl`: storage/cookie persistence probe with `esc` flag
- `s210` — `Ol`: expanded hardware/GPU info via obfuscated path
- `exp_s1013`, `exp_s1014` — experimental (unavailable)

---

## Log records (`lr`) — telemetry section

The `lr` array contains one entry per `get()` call. This is not
fingerprint data but operational telemetry sent alongside it.

| Field | Example | Meaning |
|-------|---------|---------|
| `am` | `"get"` | API method |
| `v` | `"1"` | Protocol version |
| `dt` | `"2026-02-06T17:49:57.399Z"` | Timestamp |
| `ci` | `"js/3.12.6"` | Client identifier (library version) |
| `pi` | `"ZjRmWHYgwT"` | Page ID |
| `ai` | `"s0RLqg11"` | Agent ID |
| `ri` | `"8naO13VXnE2q"` | Request ID |
| `c` | `"xx-fpjs-api-token-xx"` | API key |
| `er` | `"Response cannot be parsed"` | Error message (expected — we faked the server response) |
| `sd` | object | **Signal durations** — milliseconds each signal took to collect |
| `ca` | array | Cache API call attempts |
| `ia` | array | Identification API call attempts (URL, timing) |
| `fa` | array | Fallback API call attempts |
| `vs` | `[{"t": 192, "s": "h"}, {"t": 625, "s": "v"}]` | Page visibility state changes (`h`=hidden, `v`=visible) |
| `ls`/`le` | 192 / 209 | Load start/end (ms from page load) |
| `ss`/`se` | 193 / 702 | Signal collection start/end |
| `gs`/`ge` | 209 / 710 | `get()` call start/end |

---

## Signal collection timing (`lr[].sd`)

The `sd` object inside each log record shows how long each signal took
to collect, in milliseconds from the start of collection. Slowest
signals in this capture:

| Signal | Duration (ms) | What it measures |
|--------|--------------|------------------|
| `s106` | 164 | Feature flag |
| `s154` | 164 | WebView detection |
| `s52` | 162 | Combined hash |
| `s211` | 127 | Capability flags |
| `s158` | 83 | Feature flag |
| `s20` | 82 | Font detection |
| `s97` | 83 | Unknown |
| `s70` | 80 | Unknown |
| `s79` | 72 | Profile file detection |
| `s85` | 70 | Unknown |
| `s84` | 66 | Screen dimensions |
| `s160` | 164 | Feature flag |

Most navigator property reads (`s1`, `s2`, `s5`, `s7`, `s15`, etc.)
complete in 0-1 ms. Font detection (`s20`) and canvas/WebGL hashing
(`s17`, `s74`, `s75`) take noticeably longer.

---

## Encoding pipeline

The raw signal object (above) is transmitted through:

1. **Kt()** — Custom binary JSON encoder (outputs UTF-8 JSON as a byte array)
2. **Ti()** — Deflate compression via `CompressionStream("deflate-raw")` if payload > 1024 bytes
3. **Vi() / zr()** — XOR encryption with a random 9-byte key embedded in the output header

Binary layout: `[baseByte][flag+base, flag+base][paddingCount+base][random padding...][9-byte XOR key][encrypted payload]`

Flags `[3,14]` = compressed, `[3,13]` = uncompressed.

The result is POSTed as `Content-Type: text/plain` to
`https://api.fpjs.io/?ci=js/3.12.6&q=<apiKey>`.
