# FingerprintJS Pro v3.12.6 — Fingerprinting Metrics Analysis

Analysis of fingerprinting data collected by FingerprintJS Pro, identified by
reading the deobfuscated source in `sample_scripts/deobfs/1.deob.js`.

Script source: researcher-controlled test host running FingerprintJS Pro v3.12.6 (retrieved 2026-02-06)

## Architecture

The script organizes collection into 3 modules, each with up to 3 stages:

- **"id"** (Jl) — Identification: the primary fingerprint used for visitor ID
- **"bd"** (Gl) — Behavioral/Device: supplementary device and bot signals
- **"ex"** (_u) — Experimental: metrics under development

Stages run in order:
- **Stage 1** — fast synchronous checks, run immediately
- **Stage 2** — async / iframe-based collection
- **Stage 3** — direct synchronous collection (largest group)

Results are serialized into an encrypted binary payload and POSTed to
`https://api.fpjs.io/`.

## Complete Metrics List

### Canvas Fingerprinting

| Key | Function | Description |
|-----|----------|-------------|
| s17 | `Iu$1` → `yn` | Canvas 2D fingerprint — draws text (`Cwm fjordbank gly` + emoji U+1F603) in Times New Roman + Arial with `fillRect` overlay, then draws colored arcs with `globalCompositeOperation: "multiply"` and evenodd fill; hashes two separate `toDataURL()` outputs (text hash + geometry hash); also tests winding rule via `isPointInPath("evenodd")` |

### WebGL

| Key | Function | Description |
|-----|----------|-------------|
| s74 | `Gu` → `It` | WebGL vendor/renderer — `gl.getParameter(VERSION)`, `VENDOR`, `RENDERER`, `SHADING_LANGUAGE_VERSION`; plus unmasked vendor/renderer via `WEBGL_debug_renderer_info` extension |
| s75 | `Hu` → `kt` | WebGL full parameter dump — all context attributes, ~300 GL constant values via `getParameter()`, shader precisions for all FRAGMENT/VERTEX + FLOAT/INT combos, all supported extensions, all extension parameter values, list of unsupported extensions |

### Audio

| Key | Function | Description |
|-----|----------|-------------|
| s96 | `Zu$1` → `Rt` | `AudioContext.baseLatency` |
| au$1 | `rn(vn,...)` → `vn` | OfflineAudioContext fingerprint — creates triangle oscillator at 10kHz through DynamicsCompressor (threshold=-50, knee=40, ratio=12, attack=0, release=0.25), renders 5000 samples at 44.1kHz, sums absolute values of channel data from sample 4500 onward |

### Speech Synthesis

| Key | Function | Description |
|-----|----------|-------------|
| s52 | `jc` → `Nc(Mc)` | `speechSynthesis.getVoices()` — variant 1 (filtered/hashed) |
| s158 | `ea` → `Nc(...)` | `speechSynthesis.getVoices()` — variant 2 (different hash) |
| s160 | `Vc` → `Nc(Fc)` | `speechSynthesis.getVoices()` — variant 3 |

### Fonts

| Key | Function | Description |
|-----|----------|-------------|
| s20 | `kc` | Font enumeration — measures 50 fonts (ARNO PRO, Agency FB, Arial Unicode MS, Calibri, Century Gothic, Futura, Gill Sans, Helvetica Neue, Lucida Bright, Menlo, Meiryo UI, Segoe UI Light, SimHei, etc.) against 3 baselines (monospace, sans-serif, serif) using span width/height comparison in iframe; test string: `mmMwWLliI0O&1` at 48px |
| s51 | `Lc` | Font detection (extended) — additional font metrics technique |
| s206 | `Il` | Firefox radio input default font — `getComputedStyle(radioInput).fontFamily`; only runs in Firefox, fingerprints the default font assigned to `<input type="radio">` |
| s207 | `kl` | FontFace API test — `new FontFace("font", "local('Arial')").load()` success/failure; tests FontFace constructor and local() source behavior |
| s210 | `Ol` | Dynamic/async font detection |
| s211 | `Zl` | Extended font probing |

### Screen and Display

| Key | Function | Description |
|-----|----------|-------------|
| s5 | `hu$1` → `En` | Screen resolution — `screen.width`, `screen.height` (sorted descending) |
| s3 | `mu` → `qn` | `screen.colorDepth` |
| s36 | `su` → `Yn` | `screen.colorDepth` (async variant, same API) |
| s57 | `ss` | `window.devicePixelRatio` |
| s6 | `lu` → `In` → `kn` | Screen frame metrics — `screen.availTop`, `screen.availLeft`, `screen.availWidth`, `screen.availHeight` (computes taskbar/dock position and size) |
| s84 | `As` | Screen dimensions measured from inside iframe — `screen.width`, `screen.height` |
| s76 | `_c` → `ai` | Window dimensions — `outerWidth`, `outerHeight`, `innerWidth`, `innerHeight` |
| s150 | `oc` → `ai` | Window dimensions (same function, in bd module) |
| s142 | `ms` | High-DPI detection — `matchMedia("(-webkit-min-device-pixel-ratio: 2), (min-resolution: 2dppx)")` |
| s152 | `hs` | CSS half-pixel rendering — div with `.5px dotted transparent` border, checks `offsetHeight` |
| s204 | `Rl` | Scrollbar detection — creates 100×100 `overflow:scroll` div, checks `offsetWidth === clientWidth` (true = overlay/hidden scrollbar) |

### Navigator Properties

| Key | Function | Description |
|-----|----------|-------------|
| s101 | `$u` → `ui` | `navigator.userAgent` |
| s103 | `Yu$1` → `ci` | `navigator.appVersion` |
| s1 | `fu` → `Xn` | `navigator.oscpu` |
| s15 | `Ru$1` → `ot` | `navigator.platform` — with iPad-on-Mac detection (checks screen ratio + MediaSource + webkitRequestFullscreen) |
| s7 | `pu` → `Kn` | `navigator.hardwareConcurrency` |
| s4 | `vu` → `zn` | `navigator.deviceMemory` |
| s27 | `Au$1` → `ct` | `navigator.vendor` |
| s14 | `Eu` → `rt` | `navigator.cpuClass` (IE/legacy) |
| s123 | `Ku` → `di` | `navigator.productSub` |
| s82 | `Es` | `navigator.language` |
| s83 | `Rs` | `navigator.languages` |
| s2 | `du$1` → `Jn` | Language list — `navigator.language`, `navigator.languages`, `navigator.userLanguage`, `navigator.browserLanguage`, `navigator.systemLanguage` |
| s80 | `Fu` → `yt` | `navigator.pdfViewerEnabled` |
| s104 | `Xu` → `si` | `navigator.connection.rtt` (Network Information API) |
| s30 | `is` → `si` | `navigator.connection.rtt` (same API, in id module) |
| s102 | `gs` | `navigator.userAgentData` presence — boolean (NavigatorUAData API) |
| s153 | `js` | `navigator.onLine` |
| s154 | `Js` | `navigator.onLine` (duplicate in bd module) |

### User-Agent Client Hints

| Key | Function | Description |
|-----|----------|-------------|
| s58 | `Wc` | `navigator.userAgentData.getHighEntropyValues()` — collects: brands, mobile, platform, platformVersion, architecture, bitness, model, uaFullVersion, fullVersionList |

### Touch and Input

| Key | Function | Description |
|-----|----------|-------------|
| s19 | `ku$1` → `ut` | Touch support — `navigator.maxTouchPoints`, `navigator.msMaxTouchPoints`, `document.createEvent("TouchEvent")`, `"ontouchstart" in window` |

### Plugins and MIME Types

| Key | Function | Description |
|-----|----------|-------------|
| s16 | `Su$1` → `it` | Full plugin enumeration — `navigator.plugins` with name, description, and all MIME types (type + suffixes) per plugin |
| s117 | `qu$1` → `li` | `navigator.plugins.length` |
| s135 | `ps` | `navigator.mimeTypes.length` |
| s136 | `tc` → `vi` | MimeType prototype chain validation — checks `MimeTypeArray.prototype` and `MimeType.prototype` integrity (detects spoofing) |
| s118 | `ws` | `PluginArray.prototype` chain validation — same technique as s136 but checks `PluginArray.prototype` and `Plugin.prototype` integrity |

### CSS Media Queries

| Key | Function | Description |
|-----|----------|-------------|
| s44 | `gc` → `wc` | `prefers-color-scheme` — dark/light |
| s37 | `Pu` → `lt` | `color-gamut` — rec2020 / p3 / srgb |
| s41 | `xu$1` → `ft` | `inverted-colors` — inverted / none |
| s39 | `Tu` → `dt` | `forced-colors` — active / none |
| s42 | `Ou$1` → `mt` | `monochrome` — bits (0–100) |
| s38 | `_u$1` → `vt` | `prefers-contrast` — high/more/low/less/forced/no-preference |
| s43 | `ju` → `ht` | `prefers-reduced-motion` — reduce / no-preference |
| s91 | `Vu$1` → `pt` | `prefers-reduced-transparency` — reduce / no-preference |
| s40 | `Nu$1` → `gt` | `dynamic-range` — high (HDR) / standard |
| s139 | `fs` | `CSS.supports("backdrop-filter", "blur(2px)")` — backdrop-filter support detection |

### Math Precision

| Key | Function | Description |
|-----|----------|-------------|
| s46 | `Mu$1` → `wt` | 20+ transcendental function results with specific constant inputs: `acos(0.123...)`, `acosh(1e308)`, `asin(0.123...)`, `asinh(1)`, `atanh(0.5)`, `atan(0.5)`, `sin(-1e300)`, `sinh(1)`, `cos(10.000000000123)`, `cosh(1)`, `tan(-1e300)`, `tanh(1)`, `exp(1)`, `expm1(1)`, `log1p(10)`, `pow(PI, -100)`; includes polyfill variants (acoshPf, asinhPf, atanhPf, sinhPf, coshPf, tanhPf, expm1Pf, log1pPf) |

### Text and MathML Rendering

| Key | Function | Description |
|-----|----------|-------------|
| s87 | `ta` | CSS text measurement — renders styled text in iframe, measures bounding box |
| s92 | `ua` | MathML rendering fingerprint — renders complex MathML (product operator with Greek letter sub/superscripts: 𝔈υτρσ, 𝔇πονξ, 𝔄δγαβ, 𝔅θηεζ, 𝔉ωψϕχ, ℭμλικ), measures bounding box |
| s93 | `ia` | Unicode text rendering measurement — specific Unicode sequences in iframe |

### Storage APIs

| Key | Function | Description |
|-----|----------|-------------|
| s10 | `wu` → `nt` | `!!window.sessionStorage` |
| s11 | `yu$1` → `tt` | `!!window.localStorage` |
| s13 | `bu$1` → `et` | `!!window.openDatabase` (WebSQL) |
| s12 | `Ls` | Encrypted storage check (likely IndexedDB) — via `Cs` string table |
| s85 | `xs` | IndexedDB check in WebKit/Safari — via `Cs` encrypted calls |

### Timezone and Time

| Key | Function | Description |
|-----|----------|-------------|
| s9 | `gu$1` → `Qn` | Timezone — `Intl.DateTimeFormat().resolvedOptions().timeZone`; fallback: `UTC±N` from `Date.getTimezoneOffset()` |
| s45 | `yc` | Timestamps — `Date.now()` and timezone-adjusted value `Date.now() - 60000 * new Date().getTimezoneOffset()` |
| s200 | `cl` | `performance.timeOrigin` (fallback: `Date.now() - performance.now()`) |
| s202 | `Bu$1` → `St` | `Intl.DateTimeFormat().resolvedOptions().locale` |

### Browser / Engine Detection

| Key | Function | Description |
|-----|----------|-------------|
| s59 | `uc` → `on` | IE detection — MSCSSMatrix, msSetImmediate, msIndexedDB, msMaxTouchPoints, msPointerEnabled |
| s60 | `cc` → `un` | Edge Legacy detection — msWriteProfilerMark, MSStream, msLaunchUri, msSaveBlob |
| s61 | `sc` → `cn` | Chrome detection — webkitPersistentStorage, webkitTemporaryStorage, vendor="Google", BatteryManager, webkitMediaStream |
| s62 | `ac` → `sn` | Safari detection — ApplePayError, CSSPrimitiveValue, Counter, vendor="Apple", WebKitMediaKeys |
| s63 | `lc` → `an` | Desktop Safari — no TouchEvent, no orientation, pointerLockElement in Document |
| s64 | `fc` → `ln` | Firefox detection — buildID in navigator, MozAppearance, onmozfullscreenchange, mozInnerScreenX, CSSMozDocumentRule |
| s65 | `dc` → `dn` | Mobile detection — SharedWorker absence, connection.ontypechange, Audio.sinkId absence (Android); orientationchange, orientation (iOS/Android) |
| s201 | `vc` → `mn` | Chromium 120+ detection — srLatency, srChannelCount, devicePosture, visualViewport.segments |
| s28 | `Cu$1` → `st` | Window global objects — probes for `chrome`, `safari`, `__crWeb`, `__gCrWeb`, `yandex`, `__yb`, `__ybro`, `__firefox__`, `__edgeTrackingPreventionStatistics`, `webkit`, `oprt`, `samsungAr`, `ucweb`, `UCShellJava`, `puffinDevice` |
| s156 | `na` | Window property name hash detection — checks `Object.getOwnPropertyNames(window)` against ~30 hashed property name values to detect browser-specific globals |

### Prototype and Native Function Checks

| Key | Function | Description |
|-----|----------|-------------|
| s24 | `Bc` | `eval.toString().length` — differs between engines (Chrome=33, Firefox=37, Safari=37) |
| s148 | `ec` → `gi` | `Function.prototype.bind.toString()` |
| s50 | `Oc` | `navigator.hardwareConcurrency` property descriptor validation — detects getter modification |
| s119 | `zu` → `fi` | Error stack trace format — triggers `null[0]()`, captures `Error.stack.toString()` |
| s120 | `vs` | `Error.prototype.toSource()` — Firefox-specific, returns true/false |
| s81 | `Du$1` → `bt` | Float32Array endianness — byte representation of `Infinity - Infinity` (NaN) |
| s130 | `ys` | `typeof SourceBuffer`, `typeof SourceBufferList` — media source extension type detection |
| s132 | `bs` | `window.close.toString()` — native function string representation |
| s144 | `ds` | `SharedArrayBuffer` — creates instance, checks `byteLength` (availability varies by cross-origin isolation) |
| s155 | `zs` | Property getter `toString()` fingerprint — enumerates getter functions on window properties matching hashed names, collects their `toString()` output |
| s205 | `Sl` | `new URL("C:/").protocol` — URL parsing behavior fingerprint (differs between engines: `"c:"` vs `"file:"`) |

### Bot and Automation Detection

| Key | Function | Description |
|-----|----------|-------------|
| s72 | `$c` | `navigator.webdriver` |
| s22 | `us` | `navigator.webdriver` (duplicate in id module) |
| s157 | `ic` → `yi` | Automation framework detection — checks window/document for: Selenium (`_Selenium_IDE_Recorder`, `_selenium`, `calledSelenium`, `__selenium_evaluate`, `__selenium_unwrapped`, regex `/^([a-z]){3}_.*_(Array\|Promise\|Symbol)$/`), WebDriver (`webdriver`, `__webdriverFunc`, `__lastWatirAlert`, `_WEBDRIVER_ELEM_CACHE`, `ChromeDriverw`, `$cdc_asdjflasutopfhvcZLmcf*`, `__$webdriverAsyncExecutor`), PhantomJS (`callPhantom`, `_phantom`), Nightmare (`__nightmare`, `nightmare`), CefSharp, Awesomium, Puppeteer (`RunPerfTest`), wdio (`wdioElectron`), Electron (`emit`), domAutomation (`domAutomation`, `domAutomationController`), Phantomas (`__phantomas`), fmget (`fmget_targets`), geb (`geb`), spawn (`spawn`) |
| s149 | `rc` → `wi` | `window.process` — Node.js/Electron environment detection |
| s167 | `pl` → `gl` → `Ns` | Bot fingerprint (encrypted) — uses encrypted property name table to check for automation markers on navigator/document |

### Privacy and Ad Blocker Detection

| Key | Function | Description |
|-----|----------|-------------|
| s21 | `au$1` → DOM blockers | Ad blocker detection — injects ~200 CSS selectors from ~40 filter lists (EasyList, AdGuard Base, uBlock, Fanboy, regional lists for 20+ countries), checks which are hidden by content blockers; reports which filter lists are active |
| s89 | `Yc` | Ad blocker detection result (same technique, in id module) |
| s33 | `hc` | Brave browser detection — checks `[66,114,97,118,101]` ("Brave") in window + canvas IDAT chunk analysis (Brave modifies canvas output) |
| s86 | `Os` | Private/incognito mode detection — uses encrypted `Gi` calls (see Encrypted section) |
| s106 | `Ju$1` → `hi` | Notification permission mismatch — `Notification.permission === "denied"` but `permissions.query({name:"notifications"}).state === "prompt"` (incognito indicator) |
| s95 | `Wa` | Notification permission check (similar to s106) |
| s68 | `mc` → `Gr` | Restricted/privacy browser detection — checks absence of `PushManager`, `AudioBuffer`, `RTCPeerConnection`, `navigator.geolocation`, `ServiceWorker` in window (browsers with stripped APIs) |

### Frame and Origin

| Key | Function | Description |
|-----|----------|-------------|
| s69 | `Zc` | Frame hierarchy — traverses `window.parent` chain collecting `location.href` and `document.referrer` at each level (hashed) |
| s71 | `Uc` | Origin detection — `window.origin`, `location.origin`, `location.ancestorOrigins` |
| s98 | `$a` | `"serviceWorker" in Navigator.prototype` |
| s99 | `Ya` | `window.isSecureContext` |

### Cookie Support

| Key | Function | Description |
|-----|----------|-------------|
| s32 | `Lu$1` → `at` | Cookie functionality — writes `cookietest=1; SameSite=Strict`, reads back, then expires it |

### TLS Fingerprinting

| Key | Function | Description |
|-----|----------|-------------|
| s70 | `rl` | TLS fingerprint — remote resource fetch via `Hl` function to `defaultTlsEndpoint`; captures TLS handshake characteristics server-side |

### Document and DOM

| Key | Function | Description |
|-----|----------|-------------|
| s131 | `Qu` → `pi` | `document.documentElement.getAttributeNames()` |
| s133 | `nc` → `mi` | `window.external.toString()` |
| s145 | `as` | Navigator prototype methods — enumerates all function names on `Object.getPrototypeOf(navigator)` |
| s49 | `xc` | Same as s145 but with different filtering |
| s66 | `Wu$1` → `Et` | `HTMLAnchorElement.attributionSourceId` — Safari Attribution API |
| s151 | `_s` | `Object.getOwnPropertyDescriptor(document, "createElement")` — checks if writable/configurable (detects overridden DOM methods) |
| s166 | `dl` | `Navigator.prototype` property enumeration — collects all property names via `O$1()` to fingerprint which navigator APIs are available |

### Encrypted / Unresolvable

These metrics use `Gi(obj, hash)` hash-based property dispatch or encrypted string
tables, making static analysis impossible without runtime execution. The property
names accessed are hidden behind 32-bit hashes.

| Key | Function | Description |
|-----|----------|-------------|
| s23 | `Is` | Encrypted `Gi` call on navigator — unknown property |
| s29 | `Ss` | Encrypted `Gi` call on navigator — unknown property |
| s79 | `rs` | Encrypted `Gi` call — unknown property |
| s86 | `Os` | Private/incognito mode detection — clear from context but exact checks encrypted via `Gi` |
| s94 | `Ia` | Active detection — uses encrypted `Sa` string table for property probing |
| s146 | `ls` | Object inspection check — `objectToInspect` existence |
| s159 | `ra` | Encrypted `Gi` call — unknown property |
| s162 | `sa` | Encrypted `Gi` call on navigator — unknown property |
| s165 | `vl` | Encrypted class instantiation via `ml(0)`, checks `isTrusted` property via `Gi` (likely Event/CustomEvent) |
| s167 | `pl` → `gl` → `Ns` | Bot fingerprint — encrypted property name table for automation marker checks |
| s203 | `El` | Creates `<a>` element via encrypted `bl(0)`, sets/reads properties via encrypted names `bl(1)`, `bl(2)` |
| s209 | `Cl` | Encrypted via `Al` string table — likely EME/DRM capability check |

### Experimental Module ("ex")

| Key | Function | Description |
|-----|----------|-------------|
| exp_s1013 | `a` | Experimental metric |
| exp_s1014 | `yu` | Encrypted check via `Yu` string table |
| exp_s1015 | `Wu` | Experimental (likely WebGL variant) |
| exp_s1016 | `gu` | Experimental (likely GPU detection) |

### Sent in Request (not from sources)

| Key | Function | Description |
|-----|----------|-------------|
| s55 | `Yl(n)` | Page URL hash |
| s48 | `cs()` | Cookie-related data |
| url | — | Current `location.href` (hashed via `Ir`) |
| cr | — | `document.referrer` (hashed via `Ir`) |

## Summary by Category

| Category | Count | Key Surfaces |
|----------|-------|-------------|
| Canvas | 1 | 2D drawing hash (text + geometry + winding) |
| WebGL | 2 | Vendor/renderer (unmasked), 300+ GL parameters, shader precisions, all extensions |
| Audio | 2 | baseLatency, OfflineAudioContext oscillator fingerprint |
| Speech synthesis | 3 | getVoices() with multiple hash variants |
| Fonts | 6 | 50+ fonts probed via DOM width, radio input font, FontFace API, extended probing |
| Screen/display | 10 | Resolution, colorDepth, devicePixelRatio, frame metrics, window dimensions, high-DPI, half-pixel rendering, scrollbar detection |
| Navigator properties | 18 | userAgent, oscpu, platform, vendor, languages, hardwareConcurrency, deviceMemory, plugins, mimeTypes, cpuClass, connection.rtt, pdfViewerEnabled, productSub, appVersion, webdriver, userAgentData, onLine |
| UA Client Hints | 1 | 9 high-entropy values via getHighEntropyValues() |
| CSS media queries/features | 10 | color-scheme, color-gamut, inverted-colors, forced-colors, monochrome, contrast, reduced-motion, reduced-transparency, dynamic-range, backdrop-filter |
| Math precision | 1 | 20+ transcendental functions with polyfill variants |
| Text/MathML rendering | 3 | CSS text metrics, MathML bounding box, Unicode rendering |
| Storage | 4-5 | sessionStorage, localStorage, openDatabase, IndexedDB |
| Timezone/time | 4 | Intl timezone, locale, timestamps, performance.timeOrigin |
| Browser/engine detection | 10 | IE, Edge, Chrome, Safari, Desktop Safari, Firefox, Mobile, Chromium 120+, window globals, window property hash detection |
| Prototype/native checks | 11 | eval.toString().length, bind.toString(), stack traces, toSource(), endianness, descriptor validation, SourceBuffer types, window.close.toString(), SharedArrayBuffer, property getter toString(), URL parsing |
| Bot detection | 5 | navigator.webdriver, 15+ automation framework markers, window.process, encrypted property checks |
| Privacy/ad blockers | 6 | 40 filter list detection, Brave detection, incognito detection, notification permission mismatch, restricted browser detection |
| Frame/origin | 4 | Frame hierarchy, ancestorOrigins, serviceWorker, isSecureContext |
| Document/DOM | 5 | documentElement attributes, external.toString(), navigator prototype methods, createElement descriptor, Navigator.prototype enumeration |
| TLS | 1 | Remote TLS fingerprint via server-side capture |
| Encrypted/unresolvable | ~12 | Property checks via Gi dispatch with encrypted name tables |
| Experimental | 4 | Under development |
| **Total** | **~115 distinct signals** | |

## Encryption and Obfuscation

The script uses several obfuscation layers beyond standard minification:

- **`Gi(obj, hash)`** — dispatches property access using a 32-bit hash of the
  property name instead of the name itself; 5 call sites
- **`Hi(uint32array, xorLen)`** — decrypts a Uint32Array into a JSON-parsed
  string lookup table; produces closures like `Vs(index)` for runtime string
  resolution; ~12 lookups via `Vs`
- **`Ui(arrays, decoders, counts)`** — multi-source encrypted string tables
  with fallback chains; used for `Xa`, `Za`, `zc` tables containing property
  names for bot detection and storage checks
- **Identity wrapper functions** — e.g. `function(n,t){return n(t)}` used
  extensively to obscure call targets from static analysis

These layers specifically target the bot detection (s157/s167), storage
probing (s12/s85), private browsing detection (s86), and TLS fingerprinting
(s70) code paths — the most sensitive signals from a counter-detection
perspective.
