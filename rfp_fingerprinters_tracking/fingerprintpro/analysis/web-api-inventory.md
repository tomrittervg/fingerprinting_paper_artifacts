# FingerprintJS Pro v3.12.6 — Complete Web API Inventory

Comprehensive list of every Web API that FingerprintJS Pro's fingerprinting
script accesses, derived from the deobfuscated source (`1.deob.js`), intercepted
payload data (`data.2.json`), Firefox Profiler traces, and the existing analysis
documents in this directory.

Script source: researcher-controlled test host running FingerprintJS Pro v3.12.6 (retrieved 2026-02-06)
Version: FingerprintJS Pro v3.12.6 (`js/3.12.6`)

---

## Architecture Overview

The script organizes collection into 3 modules, each with up to 3 stages:

- **"id"** — Identification: the primary fingerprint for visitor ID (91 signals)
- **"bd"** — Behavioral/Device: supplementary device and bot signals (69 signals)
- **"ex"** — Experimental: metrics under development (4 signals)

Stages run in order:
1. **Stage 1** — fast async checks, run first (TLS, storage UUID, bot markers)
2. **Stage 2** — async / iframe-based collection (canvas, fonts, WebGL, speech, WebRTC)
3. **Stage 3** — synchronous collection, largest group (navigator, screen, math, CSS, etc.)

Results are serialized into an encrypted binary payload and POSTed to
`https://api.fpjs.io/`.

---

## 1. Canvas 2D Fingerprinting (s17)

Renders specific text and geometric shapes on an off-screen canvas, then hashes
the resulting pixel data. Two separate renders produce independent hashes, plus
a winding-rule test.

| Web API | Usage |
|---|---|
| `document.createElement("canvas")` | Creates off-screen canvas |
| `HTMLCanvasElement.getContext("2d")` | Gets 2D rendering context |
| `CanvasRenderingContext2D.rect()` | Two nested rectangles for winding test: `rect(0,0,10,10)`, `rect(2,2,6,6)` |
| `CanvasRenderingContext2D.isPointInPath("evenodd")` | Tests `evenodd` winding rule support at point (5,5) |
| `HTMLCanvasElement.width` / `.height` | Set to 240x60 (text), then 122x110 (geometry) |
| `CanvasRenderingContext2D.textBaseline` | Set to `"alphabetic"` |
| `CanvasRenderingContext2D.fillStyle` | Set multiple times: `"#f60"`, `"#069"`, `"rgba(102, 204, 0, 0.2)"`, `"#f2f"`, `"#2ff"`, `"#ff2"`, `"#f9c"` |
| `CanvasRenderingContext2D.fillRect()` | One rectangle: `fillRect(100, 1, 62, 20)` |
| `CanvasRenderingContext2D.font` | Set to `'11pt "Times New Roman"'` then `"18pt Arial"` |
| `CanvasRenderingContext2D.fillText()` | Text: `"Cwm fjordbank gly "` + emoji U+1F603 drawn twice at different positions/fonts |
| `CanvasRenderingContext2D.globalCompositeOperation` | Set to `"multiply"` for geometry render |
| `CanvasRenderingContext2D.beginPath()` | Three separate path operations |
| `CanvasRenderingContext2D.arc()` | Three colored arcs at (40,40), (80,40), (60,80) with radius 40; plus two concentric arcs at (60,60) radii 60 and 20 |
| `CanvasRenderingContext2D.closePath()` | Closes each arc path |
| `CanvasRenderingContext2D.fill()` | Standard fill for arcs; `fill("evenodd")` for concentric rings |
| `HTMLCanvasElement.toDataURL()` | Called twice: once for text render, once for geometry render |

**Output:** `{winding: boolean, geometry: "hash...", text: "hash..."}` — hashes via MurmurHash3.

**Notes:** The text string "Cwm fjordbank gly" is a pangram-like phrase chosen
to exercise many glyphs across font renderers. The emoji U+1F603 tests color
emoji rendering. The `globalCompositeOperation: "multiply"` and evenodd winding
rule are operations that vary across GPU/driver implementations.

---

## 2. WebGL Fingerprinting (s74, s75, s76)

Three separate WebGL signals: GPU identity strings, full parameter dump, and
rendered image hash.

### 2a. WebGL Vendor/Renderer (s74)

| Web API | Usage |
|---|---|
| `document.createElement("canvas")` | Creates canvas |
| `HTMLCanvasElement.getContext("webgl")` | Gets WebGL1 context (fallback: `"experimental-webgl"`) |
| `WebGLRenderingContext.getParameter(VERSION)` | GL version string |
| `WebGLRenderingContext.getParameter(VENDOR)` | GL vendor string |
| `WebGLRenderingContext.getParameter(RENDERER)` | GL renderer string |
| `WebGLRenderingContext.getParameter(SHADING_LANGUAGE_VERSION)` | GLSL version |
| `WebGLRenderingContext.getExtension("WEBGL_debug_renderer_info")` | Gets debug extension |
| `WebGLRenderingContext.getParameter(UNMASKED_VENDOR_WEBGL)` | Real GPU vendor (skipped on Firefox) |
| `WebGLRenderingContext.getParameter(UNMASKED_RENDERER_WEBGL)` | Real GPU model (skipped on Firefox) |

### 2b. WebGL Full Parameter Dump (s75)

| Web API | Usage |
|---|---|
| `WebGLRenderingContext.getContextAttributes()` | All context attributes |
| `WebGLRenderingContext.getSupportedExtensions()` | Full extension list |
| `WebGLRenderingContext.getParameter()` | Called with ~80 GL constants (see list below) |
| `WebGLRenderingContext.getExtension()` | Activates each supported extension |
| `WebGLRenderingContext.getShaderPrecisionFormat()` | Called 12 times: FRAGMENT_SHADER and VERTEX_SHADER × LOW_FLOAT, MEDIUM_FLOAT, HIGH_FLOAT, LOW_INT, MEDIUM_INT, HIGH_INT |

**GL constants queried via getParameter():** `10752, 2849, 2884, 2885, 2886, 2928,
2929, 2930, 2931, 2932, 2960, 2961, 2962, 2963, 2964, 2965, 2966, 2967, 2968,
2978, 3024, 3042, 3088, 3089, 3106, 3107, 32773, 32777, 32823, 32824, 32936,
32937, 32938, 32939, 32968, 32969, 32970, 32971, 3317, 33170, 3333, 3379, 3386,
33901, 33902, 34016, 34024, 34076, 3408, 3410, 3411, 3412, 3413, 3414, 3415,
34467, 34816, 34817, 34818, 34819, 34877, 34921, 34930, 35660, 35661, 35724,
35738, 35739, 36003, 36004, 36005, 36347, 36348, 36349, 37440, 37441, 37443,
7936, 7937, 7938` (80 constants)

**Extension parameter constants:** `34047, 35723, 36063, 34852, 34853, 34854,
34229, 36392, 36795, 38449` (10 constants)

### 2c. WebGL Rendered Image (s76)

| Web API | Usage |
|---|---|
| `document.createElement("canvas")` | Creates canvas |
| `HTMLCanvasElement.getContext("webgl")` | Gets WebGL1 context |
| `WebGLRenderingContext.createShader()` | Creates vertex and fragment shaders |
| `WebGLRenderingContext.shaderSource()` | Sets shader source code |
| `WebGLRenderingContext.compileShader()` | Compiles shaders |
| `WebGLRenderingContext.createProgram()` | Creates shader program |
| `WebGLRenderingContext.attachShader()` | Attaches shaders |
| `WebGLRenderingContext.linkProgram()` | Links program |
| `WebGLRenderingContext.useProgram()` | Activates program |
| `WebGLRenderingContext.createBuffer()` | Creates vertex buffer |
| `WebGLRenderingContext.bindBuffer()` | Binds buffer |
| `WebGLRenderingContext.bufferData()` | Uploads triangle vertex data |
| `WebGLRenderingContext.getAttribLocation()` | Gets vertex attribute location |
| `WebGLRenderingContext.vertexAttribPointer()` | Sets vertex layout |
| `WebGLRenderingContext.enableVertexAttribArray()` | Enables attribute |
| `WebGLRenderingContext.getUniformLocation()` | Gets uniform `t` location |
| `WebGLRenderingContext.uniform1f()` | Sets rotation angle to 3.65 |
| `WebGLRenderingContext.clearColor()` | Sets blue background |
| `WebGLRenderingContext.clear()` | Clears canvas |
| `WebGLRenderingContext.drawArrays()` | Draws red rotating triangle |
| `HTMLCanvasElement.toDataURL()` | Exports rendered scene for hashing |

**Output:** MurmurHash3 of `toDataURL()`.

**Notes:** The vertex shader applies a rotation matrix with `uniform float t = 3.65`,
and the fragment shader outputs solid red `vec4(1,0,0,1)`. The rendered image's
hash varies by GPU, driver, and antialiasing implementation.

---

## 3. WebGPU Adapter & Limits (exp_s1016, s210 — experimental)

Probes the WebGPU API for GPU hardware identification, exposed via the newer
WebGPU surface rather than WebGL.

| Web API | Usage |
|---|---|
| `navigator.gpu` | Accesses WebGPU entry point |
| `GPU.requestAdapter()` | Obtains GPUAdapter for the default GPU |
| `GPUAdapter.info` | Accesses GPUAdapterInfo |
| `GPUAdapterInfo.description` | GPU description string |
| `GPUAdapterInfo.device` | GPU device identifier |
| `GPUAdapterInfo.isFallbackAdapter` | Whether using software fallback |
| `GPUAdapter.limits` | Accesses GPUSupportedLimits object |
| `GPUSupportedLimits.maxBindGroups` | |
| `GPUSupportedLimits.maxBindGroupsPlusVertexBuffers` | |
| `GPUSupportedLimits.maxBindingsPerBindGroup` | |
| `GPUSupportedLimits.maxBufferSize` | |
| `GPUSupportedLimits.maxColorAttachmentBytesPerSample` | |
| `GPUSupportedLimits.maxColorAttachments` | |
| `GPUSupportedLimits.maxComputeInvocationsPerWorkgroup` | |
| `GPUSupportedLimits.maxComputeWorkgroupSizeX` | |
| `GPUSupportedLimits.maxComputeWorkgroupSizeY` | |
| `GPUSupportedLimits.maxComputeWorkgroupSizeZ` | |
| `GPUSupportedLimits.maxComputeWorkgroupStorageSize` | |
| `GPUSupportedLimits.maxComputeWorkgroupsPerDimension` | |
| `GPUSupportedLimits.maxDynamicStorageBuffersPerPipelineLayout` | |
| `GPUSupportedLimits.maxDynamicUniformBuffersPerPipelineLayout` | |
| `GPUSupportedLimits.maxInterStageShaderVariables` | |
| `GPUSupportedLimits.maxSampledTexturesPerShaderStage` | |
| `GPUSupportedLimits.maxSamplersPerShaderStage` | |
| `GPUSupportedLimits.maxStorageBufferBindingSize` | |
| `GPUSupportedLimits.maxStorageBuffersPerShaderStage` | |
| `GPUSupportedLimits.maxStorageTexturesPerShaderStage` | |
| `GPUSupportedLimits.maxTextureArrayLayers` | |
| `GPUSupportedLimits.maxTextureDimension1D` | |
| `GPUSupportedLimits.maxTextureDimension2D` | |
| `GPUSupportedLimits.maxTextureDimension3D` | |
| `GPUSupportedLimits.maxUniformBufferBindingSize` | |
| `GPUSupportedLimits.maxUniformBuffersPerShaderStage` | |
| `GPUSupportedLimits.maxVertexAttributes` | |
| `GPUSupportedLimits.maxVertexBufferArrayStride` | |
| `GPUSupportedLimits.maxVertexBuffers` | |
| `GPUSupportedLimits.minStorageBufferOffsetAlignment` | |
| `GPUSupportedLimits.minUniformBufferOffsetAlignment` | |
| `GPUAdapter.features` | Set of supported GPU features |

**Output:** Hash of adapter info + 31 limit values + features set.

**Notes:** Discovered via Firefox Profiler traces — the code path is hidden behind
encrypted string tables (`Gi` hash dispatch), making static identification
impossible. The 31 numeric limit values form a high-entropy hardware fingerprint
independent of WebGL. This is a significant new fingerprinting vector.

---

## 4. Audio Fingerprinting (s21/au, s96)

### 4a. OfflineAudioContext Fingerprint (s21/au)

| Web API | Usage |
|---|---|
| `OfflineAudioContext(1, 5000, 44100)` | Creates offline context (1 channel, 5000 samples, 44.1kHz) |
| `OfflineAudioContext.createOscillator()` | Creates oscillator node |
| `OscillatorNode.type` | Set to `"triangle"` |
| `OscillatorNode.frequency.value` | Set to `10000` (10kHz) |
| `OfflineAudioContext.createDynamicsCompressor()` | Creates compressor node |
| `DynamicsCompressorNode.threshold.value` | Set to `-50` |
| `DynamicsCompressorNode.knee.value` | Set to `40` |
| `DynamicsCompressorNode.ratio.value` | Set to `12` |
| `DynamicsCompressorNode.attack.value` | Set to `0` |
| `DynamicsCompressorNode.release.value` | Set to `0.25` |
| `OscillatorNode.connect()` | Connects oscillator → compressor |
| `DynamicsCompressorNode.connect()` | Connects compressor → destination |
| `OscillatorNode.start(0)` | Starts oscillator |
| `OfflineAudioContext.startRendering()` | Renders audio buffer |
| `AudioBuffer.getChannelData(0)` | Gets Float32Array of samples |
| `Float32Array.subarray(4500)` | Takes samples 4500–4999 |

**Output:** Sum of absolute values of samples 4500–4999 (e.g. `35.749972093850374`).

### 4b. AudioContext Base Latency (s96)

| Web API | Usage |
|---|---|
| `new AudioContext()` | Creates real-time audio context |
| `AudioContext.baseLatency` | Reads base output latency |

**Output:** Latency value in seconds (e.g. `0.01` on Chrome, `0` on Firefox).

**Notes:** The audio fingerprint is high-entropy because the DynamicsCompressor
implementation varies across browser engines and audio backends. Firefox hardcodes
`baseLatency` to `0.0` under RFP.

---

## 5. Speech Synthesis (s52, s158, s160)

| Web API | Usage |
|---|---|
| `window.speechSynthesis` | Accesses speech synthesis API |
| `SpeechSynthesis.getVoices()` | Returns array of available voices |
| `SpeechSynthesis.addEventListener("voiceschanged", ...)` | Waits for voices to load (async on some browsers) |
| `SpeechSynthesisVoice.voiceURI` | Voice identifier |
| `SpeechSynthesisVoice.name` | Human-readable voice name |
| `SpeechSynthesisVoice.lang` | Voice language |
| `SpeechSynthesisVoice.localService` | Whether voice is local or remote |
| `SpeechSynthesisVoice.default` | Whether voice is the default |

**Output:** Multiple hash variants of the voice list (s52 uses filter `Mc`,
s160 uses filter `Fc`, s158 uses a different hash — each extracts different
subsets of voice properties for independent fingerprints).

**Notes:** High entropy — the available voices vary significantly by OS, OS version,
language packs installed, and browser. Three separate signal IDs produce different
hashes of the same underlying data for robustness.

---

## 6. Font Detection & Measurement (s20, s51, s206, s207)

### 6a. Font Enumeration via DOM Width (s20)

| Web API | Usage |
|---|---|
| `document.createElement("iframe")` | Creates isolated iframe for measurement |
| `document.createElement("span")` | Creates measurement elements |
| `HTMLElement.style.fontFamily` | Set to `"'<test font>', <baseline>"` |
| `HTMLElement.style.fontSize` | Set to `"48px"` |
| `HTMLElement.offsetWidth` | Measures rendered width |
| `HTMLElement.offsetHeight` | Measures rendered height |
| `HTMLElement.textContent` | Set to test string `"mmMwWLliI0O&1"` |

**50 fonts tested (array `Ic`):**
`sans-serif-thin`, `ARNO PRO`, `Agency FB`, `Arabic Typesetting`,
`Arial Unicode MS`, `AvantGarde Bk BT`, `BankGothic Md BT`, `Batang`,
`Bitstream Vera Sans Mono`, `Calibri`, `Century`, `Century Gothic`,
`Clarendon`, `EUROSTILE`, `Franklin Gothic`, `Futura Bk BT`, `Futura Md BT`,
`GOTHAM`, `Gill Sans`, `HELV`, `Haettenschweiler`, `Helvetica Neue`,
`Humanst521 BT`, `Leelawadee`, `Letter Gothic`, `Levenim MT`, `Lucida Bright`,
`Lucida Sans`, `Menlo`, `MS Mincho`, `MS Outlook`, `MS Reference Specialty`,
`MS UI Gothic`, `MT Extra`, `MYRIAD PRO`, `Marlett`, `Meiryo UI`,
`Microsoft Uighur`, `Minion Pro`, `Monotype Corsiva`, `PMingLiU`, `Pristina`,
`SCRIPTINA`, `Segoe UI Light`, `Serifa`, `SimHei`, `Small Fonts`,
`Staccato222 BT`, `TRAJAN PRO`, `Univers CE 55 Medium`, `Vrinda`, `ZWAdobeF`

**3 baseline fonts:** `monospace`, `sans-serif`, `serif`

**Output:** Array of font names present on the system.

### 6b. Font Metrics via measureText (s51)

| Web API | Usage |
|---|---|
| `CanvasRenderingContext2D.measureText()` | Measures text width |
| `TextMetrics.width` | Reads measured width |

**Test string:** `"mmMwWLliI0fiflO&1"` (includes fi/fl ligatures)

**Font families tested:** default, `-apple-system-body`, serif, sans-serif,
monospace, 1px (minimum), system-ui

**Output:** Object with width per font family (e.g. `{default: 147.58, serif: 147.58, ...}`).

### 6c. Firefox Radio Input Font (s206)

| Web API | Usage |
|---|---|
| `document.createElement("input")` | Creates radio button |
| `HTMLInputElement.type` | Set to `"radio"` |
| `window.getComputedStyle()` | Gets computed style |
| `CSSStyleDeclaration.fontFamily` | Reads default font assigned to radio input |

**Output:** Font family string (e.g. `"-apple-system"`). Firefox-only signal.

### 6d. FontFace API (s207)

| Web API | Usage |
|---|---|
| `new FontFace("font", "local('Arial')")` | Creates FontFace with local source |
| `FontFace.load()` | Attempts to load the local font |

**Output:** Boolean — success or failure of `local()` font loading.

---

## 7. Screen & Display (s5, s3, s6, s57, s84, s150, s142, s152, s204)

| Web API | Signal | Fingerprinting Use |
|---|---|---|
| `screen.width` | s5 | Screen width — **medium entropy** |
| `screen.height` | s5 | Screen height (sorted: larger dimension first) |
| `screen.colorDepth` | s3 | Bits per pixel — **medium entropy** (typically 24 or 30) |
| `screen.availTop` | s6 | Distance from top of screen to available area |
| `screen.availLeft` | s6 | Distance from left to available area |
| `screen.availWidth` | s6 | Available screen width |
| `screen.availHeight` | s6 | Available screen height |
| `window.devicePixelRatio` | s57 | Device pixel ratio — **medium entropy** (1, 1.25, 1.5, 2, 3) |
| `window.outerWidth` | s150 | Window chrome width |
| `window.outerHeight` | s150 | Window chrome height |
| `window.innerWidth` | s150 | Viewport width |
| `window.innerHeight` | s150 | Viewport height |
| `screen.width` (iframe) | s84 | Cross-origin screen width check |
| `screen.height` (iframe) | s84 | Cross-origin screen height check |
| `window.matchMedia("(-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi)")` | s142 | High-DPI / Retina detection |

**Scrollbar detection (s204):**

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates test element in iframe |
| `HTMLElement.style.overflow` | Set to `"scroll"` |
| `HTMLElement.style.width` / `.height` | Set to `"100px"` |
| `HTMLElement.offsetWidth` | Measures outer width |
| `HTMLElement.clientWidth` | Measures inner width (equals offsetWidth if overlay scrollbar) |

**Sub-pixel rendering (s152):**

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates test element |
| `HTMLElement.style.border` | Set to `".5px dotted transparent"` |
| `HTMLElement.offsetHeight` | Reads rendered height (0 vs 1 reveals sub-pixel support) |

**Notes:** The screen available area metrics (s6) reveal taskbar/dock size and
position, which varies by OS and user configuration. `innerWidth/innerHeight` vs
`outerWidth/outerHeight` reveals toolbar and DevTools state.

---

## 8. Navigator Properties (s1, s2, s4, s7, s14, s15, s27, s80, s82, s83, s101, s102, s103, s104, s123, s153)

| Web API | Signal | Fingerprinting Use |
|---|---|---|
| `navigator.userAgent` | s101 | Full UA string — **high entropy** |
| `navigator.appVersion` | s103 | App version string |
| `navigator.oscpu` | s1 | Firefox-specific OS+arch — **medium entropy** |
| `navigator.platform` | s15 | OS identification — **medium entropy** (with iPad-on-Mac detection via `screen` ratio + `MediaSource` + `webkitRequestFullscreen`) |
| `navigator.hardwareConcurrency` | s7 | CPU core count — **medium entropy** |
| `navigator.deviceMemory` | s4 | RAM in GB — **medium entropy** (Chrome-only; null in Firefox) |
| `navigator.cpuClass` | s14 | CPU class (IE-only; null elsewhere) |
| `navigator.vendor` | s27 | Browser vendor string (Chrome: `"Google Inc."`; Firefox: `""`) |
| `navigator.productSub` | s123 | Build date string (Firefox: `"20100101"`) |
| `navigator.language` | s2, s82 | Primary language — **medium entropy** |
| `navigator.languages` | s2, s83 | Language preference array |
| `navigator.userLanguage` | s2 | IE-only language |
| `navigator.browserLanguage` | s2 | IE-only language |
| `navigator.systemLanguage` | s2 | IE-only language |
| `navigator.pdfViewerEnabled` | s80 | PDF viewer capability |
| `navigator.connection` | s104 | Network Information API (Chrome-only) |
| `navigator.connection.rtt` | s104 | Round-trip time estimate |
| `navigator.userAgentData` | s102 | UA Client Hints API presence (boolean) |
| `navigator.onLine` | s153 | Online/offline status |

**Notes:** Language collection (s2) reads 5 separate properties to get a
comprehensive language list across engines. The iPad-on-Mac detection in s15
cross-references screen aspect ratio, `MediaSource` support, and
`webkitRequestFullscreen` presence to distinguish iPadOS from macOS.

---

## 9. User-Agent Client Hints (s58)

| Web API | Usage |
|---|---|
| `navigator.userAgentData` | Checks API availability |
| `navigator.userAgentData.getHighEntropyValues()` | Requests high-entropy UA data |

**Values requested:** `brands`, `mobile`, `platform`, `platformVersion`,
`architecture`, `bitness`, `model`, `uaFullVersion`, `fullVersionList`

**Output:** Object with all requested UA-CH values, or `null` on Firefox.

**Notes:** Chrome/Chromium-only API. Returns null on Firefox and Safari. When
available, provides extremely high entropy data including exact platform version,
CPU architecture, and device model.

---

## 10. Touch & Input (s19)

| Web API | Usage |
|---|---|
| `navigator.maxTouchPoints` | Maximum touch points |
| `navigator.msMaxTouchPoints` | IE-specific variant |
| `document.createEvent("TouchEvent")` | Tests TouchEvent support (try/catch) |
| `"ontouchstart" in window` | Tests touch event handler availability |

**Output:** `{maxTouchPoints: N, touchEvent: bool, touchStart: bool}`.

---

## 11. Plugins & MIME Types (s16, s117, s118, s135, s136)

### 11a. Full Plugin Enumeration (s16)

| Web API | Usage |
|---|---|
| `navigator.plugins` | Accesses PluginArray |
| `Plugin.name` | Plugin name |
| `Plugin.description` | Plugin description |
| `Plugin[i].type` | MIME type string |
| `Plugin[i].suffixes` | File suffix list |

### 11b. Plugin/MIME Counts (s117, s135)

| Web API | Usage |
|---|---|
| `navigator.plugins.length` | Plugin count |
| `navigator.mimeTypes.length` | MIME type count |

### 11c. Prototype Chain Validation (s118, s136)

| Web API | Usage |
|---|---|
| `Object.getPrototypeOf(navigator.plugins)` | Verifies `=== PluginArray.prototype` |
| `Object.getPrototypeOf(navigator.plugins[i])` | Verifies `=== Plugin.prototype` for each plugin |
| `Object.getPrototypeOf(navigator.mimeTypes)` | Verifies `=== MimeTypeArray.prototype` |
| `Object.getPrototypeOf(navigator.mimeTypes[i])` | Verifies `=== MimeType.prototype` for each entry |

**Notes:** The prototype chain validation (s118, s136) detects spoofing — if
someone overrides `navigator.plugins` with a plain object, the prototype chain
won't match the browser-native prototypes.

---

## 12. CSS Media Queries & Features (s37, s38, s39, s40, s41, s42, s43, s44, s91, s139, s142)

All CSS media queries are tested via `window.matchMedia()`.

| Web API / Query | Signal | What It Detects |
|---|---|---|
| `matchMedia("(color-gamut: rec2020)")`, `(color-gamut: p3)`, `(color-gamut: srgb)` | s37 | Display color gamut |
| `matchMedia("(prefers-contrast: high\|more\|low\|less\|forced\|no-preference)")` | s38 | Contrast preference |
| `matchMedia("(forced-colors: active)")`, `(forced-colors: none)` | s39 | Windows high-contrast mode |
| `matchMedia("(dynamic-range: high)")`, `(dynamic-range: standard)` | s40 | HDR display capability |
| `matchMedia("(inverted-colors: inverted)")`, `(inverted-colors: none)` | s41 | Color inversion accessibility |
| `matchMedia("(monochrome: 0)")` through `(monochrome: 100)` | s42 | Monochrome display bit depth |
| `matchMedia("(prefers-reduced-motion: reduce)")`, `(no-preference)` | s43 | Reduced motion preference |
| `matchMedia("(prefers-color-scheme: dark)")`, `(light)` | s44 | Dark/light mode |
| `matchMedia("(prefers-reduced-transparency: reduce)")`, `(no-preference)` | s91 | Reduced transparency preference |
| `matchMedia("(-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi)")` | s142 | High-DPI detection |
| `CSS.supports("backdrop-filter", "blur(2px)")` | s139 | CSS backdrop-filter support |

**Notes:** Signal key assignment for CSS media queries has known ambiguities
between static analysis and intercepted data (see comparison report). The
assignments above follow the deobfuscated source code mapping.

---

## 13. Math Precision (s46)

Tests 20+ transcendental math functions with specific constant inputs. Different
floating-point implementations produce subtly different results.

| Web API | Arguments |
|---|---|
| `Math.acos()` | `0.12312423423423424` |
| `Math.acosh()` | `1e308` |
| `Math.asin()` | `0.12312423423423424` |
| `Math.asinh()` | `1` |
| `Math.atanh()` | `0.5` |
| `Math.atan()` | `0.5` |
| `Math.sin()` | `-1e300` |
| `Math.sinh()` | `1` |
| `Math.cos()` | `10.000000000123` |
| `Math.cosh()` | `1` |
| `Math.tan()` | `-1e300` |
| `Math.tanh()` | `1` |
| `Math.exp()` | `1` |
| `Math.expm1()` | `1` |
| `Math.log1p()` | `10` |
| `Math.pow()` | `Math.PI, -100` |
| `Math.log()` | Used in polyfill variants |
| `Math.sqrt()` | Used in polyfill variants |
| `Math.PI` | Used as constant input |

**Polyfill variants also tested:** `acoshPf`, `asinhPf`, `atanhPf`, `sinhPf`,
`coshPf`, `tanhPf`, `expm1Pf`, `log1pPf` — these reimplement each function
using basic operations (`exp`, `log`, `sqrt`) to detect engines where the native
function and polyfill disagree.

**Output:** MD5 hash of concatenated results.

---

## 14. Text & MathML Rendering Measurement (s87, s92, s93)

### 14a. CSS System Colors (s87)

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates measurement elements in iframe |
| `HTMLElement.style.color` | Set to CSS system color keywords |
| `window.getComputedStyle()` | Reads resolved color values |
| `CSSStyleDeclaration.color` | Gets computed color |

**~30 CSS system color keywords tested:** `AccentColor`, `AccentColorText`,
`ActiveText`, `ActiveBorder`, `ButtonFace`, `ButtonText`, `Canvas`, `CanvasText`,
`Field`, `FieldText`, `GrayText`, `Highlight`, `HighlightText`, `LinkText`,
`Mark`, `MarkText`, `VisitedText`, and others.

**Output:** Object mapping abbreviated keys to resolved color values.

### 14b. MathML Rendering (s92)

| Web API | Usage |
|---|---|
| `document.createElement("math")` (MathML) | Creates MathML content |
| `Element.getBoundingClientRect()` | Measures rendered bounding box |

**MathML content:** Product operator (∏) with Greek letter sub/superscripts:
`𝔈υτρσ`, `𝔇πονξ`, `𝔄δγαβ`, `𝔅θηεζ`, `𝔉ωψϕχ`, `ℭμλικ`.

### 14c. Unicode/Emoji Rendering (s93)

| Web API | Usage |
|---|---|
| `document.createElement("span")` | Creates text elements in iframe |
| `Element.getBoundingClientRect()` | Measures rendered dimensions |

**Content:** Specific Unicode sequences (emoji range 128512–128591) rendered to
test emoji rendering differences.

**Notes:** The bounding box dimensions of rendered text/MathML vary by font
renderer, OS text stack, and installed fonts — creating a rendering fingerprint
distinct from the canvas fingerprint.

---

## 15. Storage APIs (s10, s11, s12, s13, s85)

| Web API | Signal | Usage |
|---|---|---|
| `window.sessionStorage` | s10 | Checks existence (coerced to boolean) |
| `window.localStorage` | s11 | Checks existence (coerced to boolean) |
| `window.indexedDB` | s12 | Checks existence (via encrypted code path) |
| `window.openDatabase` | s13 | WebSQL availability (deprecated; Chrome-only) |
| `IDBFactory` (IndexedDB) | s85 | WebKit/Safari IndexedDB behavior check (via encrypted `Cs` string table) |

**Notes:** s12 and s85 use encrypted property access (`Cs` string table),
making the exact IndexedDB operations invisible to static analysis. The
`openDatabase` check (s13) detects WebSQL support, which was only ever
implemented in WebKit/Blink.

---

## 16. Cookie Support (s32)

| Web API | Usage |
|---|---|
| `document.cookie` (write) | Sets `cookietest=1; SameSite=Strict` |
| `document.cookie` (read) | Reads back to verify |
| `document.cookie` (write) | Expires the test cookie |
| `navigator.cookieEnabled` | Checks browser cookie permission state |

**Output:** Boolean — whether cookies can be written and read back.

---

## 17. Timezone & Time (s9, s45, s200, s202)

| Web API | Signal | Usage |
|---|---|---|
| `Intl.DateTimeFormat()` | s9, s202 | Creates DateTimeFormat instance |
| `Intl.DateTimeFormat().resolvedOptions().timeZone` | s9 | IANA timezone string (e.g. `"America/New_York"`) |
| `Intl.DateTimeFormat().resolvedOptions().locale` | s202 | Resolved locale string |
| `Date.now()` | s45 | Current millisecond timestamp |
| `Date.prototype.getTimezoneOffset()` | s45 | UTC offset for timezone-adjusted timestamp |
| `performance.timeOrigin` | s200 | Navigation start time (fallback: `Date.now() - performance.now()`) |
| `performance.now()` | s200 | High-resolution elapsed time |

---

## 18. Browser/Engine Detection (s28, s59–s65, s156, s201)

### 18a. Engine Feature Detection (s59–s65)

| Web API / Object | Signal | Engine Detected |
|---|---|---|
| `MSCSSMatrix`, `msSetImmediate`, `msIndexedDB`, `msMaxTouchPoints`, `msPointerEnabled` | s59 | IE |
| `msWriteProfilerMark`, `MSStream`, `msLaunchUri`, `msSaveBlob` | s60 | Edge Legacy |
| `webkitPersistentStorage`, `webkitTemporaryStorage`, `navigator.vendor="Google"`, `BatteryManager`, `webkitMediaStream` | s61 | Chrome |
| `ApplePayError`, `CSSPrimitiveValue`, `Counter`, `navigator.vendor="Apple"`, `WebKitMediaKeys` | s62 | Safari |
| `TouchEvent` absence, `orientation` absence, `document.pointerLockElement` | s63 | Desktop Safari |
| `navigator.buildID`, `MozAppearance`, `onmozfullscreenchange`, `mozInnerScreenX`, `CSSMozDocumentRule` | s64 | Firefox |
| `SharedWorker` absence, `connection.ontypechange`, `Audio.sinkId` absence (Android); `orientationchange`, `orientation` (iOS/Android) | s65 | Mobile |
| `srLatency`, `srChannelCount`, `devicePosture`, `visualViewport.segments` | s201 | Chromium 120+ |

### 18b. Window Vendor Objects (s28)

| Web API | Purpose |
|---|---|
| `window.chrome` | Chrome/Chromium |
| `window.safari` | Safari |
| `window.__crWeb` / `window.__gCrWeb` | Chrome WebView on iOS |
| `window.yandex` / `window.__yb` / `window.__ybro` | Yandex Browser |
| `window.__firefox__` | Firefox for iOS |
| `window.__edgeTrackingPreventionStatistics` | Edge |
| `window.webkit` | WebKit-based browsers |
| `window.oprt` | Opera |
| `window.samsungAr` | Samsung Internet |
| `window.ucweb` / `window.UCShellJava` | UCBrowser |
| `window.puffinDevice` | Puffin Browser |

### 18c. Window Property Name Hash Detection (s156)

| Web API | Usage |
|---|---|
| `Object.getOwnPropertyNames(window)` | Enumerates all window property names |

Scans for ~30 specific global names (matched via CRC32 hashes) that are
characteristic of particular browser versions or extensions.

---

## 19. Prototype & Native Function Integrity (s24, s50, s81, s119, s120, s130, s132, s144, s145, s148, s155, s159, s166, s205)

| Web API | Signal | Usage |
|---|---|---|
| `eval.toString().length` | s24 | Engine identification: Chrome=33, Firefox=37, Safari=37 |
| `Function.prototype.bind.toString()` | s148 | Native function string format (differs by engine) |
| `window.close.toString()` | s132 | Native function string representation check |
| `Error.stack` (triggered via `null[0]()`) | s119 | Stack trace format — varies by engine |
| `Error.prototype.toSource()` | s120 | Firefox-specific (returns boolean for existence) |
| `Float32Array`, `Uint8Array` | s81 | NaN byte representation: `float[0] = Infinity - Infinity`, reads `Uint8Array[3]` |
| `typeof SourceBuffer`, `typeof SourceBufferList` | s130 | Media Source Extensions type strings |
| `new SharedArrayBuffer(1).byteLength` | s144 | SharedArrayBuffer availability (requires cross-origin isolation) |
| `navigator.hardwareConcurrency` descriptor | s50 | `Object.getOwnPropertyDescriptor()` — detects getter modification |
| `Object.getPrototypeOf(navigator)` | s145 | Enumerates all method/property names on navigator prototype |
| `Navigator.prototype` property enumeration | s166 | Total property count + positional indices of specific properties |
| `Object.getOwnPropertyDescriptor(window, ...)` | s155 | Checks property descriptors of specific window properties (detects overrides) |
| `new URL("C:/").protocol` | s205 | URL parsing: Chrome returns `"c:"`, Firefox returns `"c:"`, Safari may differ |
| `Object.getOwnPropertyDescriptor(document, "createElement")` | s151 | Detects if `createElement` has been overridden (tampering) |
| Function/Object deletion resilience | s159 | Temporarily deletes `window.Function`/`window.Object`, checks if descriptors still behave natively |

---

## 20. Bot & Automation Detection (s72, s157, s149, s165, s167)

### 20a. navigator.webdriver (s72)

| Web API | Usage |
|---|---|
| `navigator.webdriver` | Reads WebDriver automation flag |

### 20b. Automation Framework Globals (s157)

Checks `window` and `document` for properties injected by automation tools:

| Framework | Properties Checked |
|---|---|
| Selenium | `_Selenium_IDE_Recorder`, `_selenium`, `calledSelenium`, `__selenium_evaluate`, `__selenium_unwrapped`, regex `/^([a-z]){3}_.*_(Array\|Promise\|Symbol)$/` |
| WebDriver | `webdriver`, `__webdriverFunc`, `__lastWatirAlert`, `__lastWatirConfirm`, `__lastWatirPrompt`, `_WEBDRIVER_ELEM_CACHE`, `ChromeDriverw`, `$cdc_asdjflasutopfhvcZLmcf*`, `__$webdriverAsyncExecutor` |
| PhantomJS | `callPhantom`, `_phantom` |
| Nightmare | `__nightmare`, `nightmare` |
| CefSharp | `CefSharp` |
| Puppeteer/CEF | `RunPerfTest` |
| wdio/Electron | `wdioElectron`, `emit` |
| domAutomation | `domAutomation`, `domAutomationController` |
| Phantomas | `__phantomas` |
| fmget | `fmget_targets` |
| geb | `geb` |
| spawn/Rhino | `spawn` |

Also checks `document` for: `__selenium_evaluate`, `selenium-evaluate`,
`__selenium_unwrapped`, `__webdriver_script_fn`, `__driver_evaluate`,
`__webdriver_evaluate`, `__fxdriver_evaluate`, `__driver_unwrapped`,
`__webdriver_unwrapped`, `__fxdriver_unwrapped`, `__webdriver_script_func`,
`__webdriver_script_function`, `$chrome_asyncScriptInfo`

### 20c. Node.js/Electron Detection (s149)

| Web API | Usage |
|---|---|
| `window.process` | Checks for Node.js process object |

### 20d. Event Trust Check (s165)

| Web API | Usage |
|---|---|
| `new Event()` | Creates synthetic event |
| `Event.isTrusted` | Checks if `isTrusted` is `false` (synthetic events always report false) |

### 20e. Encrypted Bot Detection (s167)

Uses encrypted property name table (`Ns`) to check for additional automation
markers on `navigator` and `document`. Exact property names hidden behind
32-bit hash dispatch.

---

## 21. Privacy & Ad Blocker Detection (s89, s33, s68, s86, s106, s95)

**Note:** The deobs analysis maps s21 to ad blocker detection, but the
intercepted data shows s21 has a floating-point value (`35.749...`) consistent
with the audio fingerprint. The signal key assignment for ad blocker detection
may be s89 rather than s21. See `metric-analysis-comparison-report.md` for
the full discussion of this conflict.

### 21a. Ad Blocker / Filter List Detection (s21/s89)

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates ~200 test elements |
| `HTMLElement.style` | Sets CSS selectors matching known filter list rules |
| `HTMLElement.offsetHeight` / `getComputedStyle()` | Checks if element was hidden by content blocker |

**~40 filter lists detected:** EasyList, AdGuard Base, AdGuard Mobile,
uBlock Origin, Fanboy's Annoyance, Fanboy's Social, EasyPrivacy, and
regional lists for 20+ countries (Finland, France, Germany, Japan, Korea,
Netherlands, Poland, Romania, Russia, Turkey, etc.).

### 21b. Brave Browser Detection (s33)

| Web API | Usage |
|---|---|
| `window` property check | Checks for char codes `[66,114,97,118,101]` ("Brave") |
| Canvas IDAT chunk analysis | Detects Brave's canvas noise injection |

### 21c. Restricted Browser Detection (s68)

| Web API | Usage |
|---|---|
| `window.PushManager` | Checks existence |
| `window.AudioBuffer` | Checks existence |
| `window.RTCPeerConnection` | Checks existence |
| `navigator.geolocation` | Checks existence |
| `window.ServiceWorker` | Checks existence |

**Output:** `true` if 3+ of these APIs are missing (indicates embedded/restricted browser).

### 21d. Incognito/Private Mode Detection (s86, s106, s95)

| Web API | Signal | Usage |
|---|---|---|
| `window.openDatabase` (WebSQL) | s86 | Safari private mode detection (encrypted via `Gi`) |
| `Notification.permission` | s106 | Reads notification permission |
| `navigator.permissions.query({name: "notifications"})` | s106 | Queries notification permission state |
| `PermissionStatus.state` | s106 | Compares: `"denied"` permission + `"prompt"` state = incognito indicator |

---

## 22. Frame & Origin (s69, s71, s98, s99)

| Web API | Signal | Usage |
|---|---|---|
| `window.parent` | s69 | Traverses frame hierarchy |
| `window.location.href` | s69 | Hashed at each frame level |
| `document.referrer` | s69 | Hashed at each frame level |
| `window.origin` | s71 | Window origin |
| `location.origin` | s71 | Location origin |
| `location.ancestorOrigins` | s71 | Ancestor origin chain |
| `"serviceWorker" in Navigator.prototype` | s98 | Service Worker availability on prototype |
| `window.isSecureContext` | s99 | HTTPS/secure context check |

---

## 23. Document & DOM Inspection (s131, s133)

| Web API | Signal | Usage |
|---|---|---|
| `document.documentElement.getAttributeNames()` | s131 | HTML root element attributes (e.g. `["lang"]`) |
| `window.external.toString()` | s133 | External interface string representation |

**Notes:** Signals s145 (navigator prototype method enumeration), s151
(`createElement` descriptor check), and s166 (Navigator.prototype property
enumeration) are documented in section 19 (Prototype & Native Function Integrity)
as they primarily serve tampering detection.

---

## 24. WebRTC SDP Fingerprinting (s97)

Discovered via Firefox Profiler traces. The code is hidden behind encrypted
string tables (`Gi` hash dispatch).

| Web API | Usage |
|---|---|
| `new RTCPeerConnection()` | Creates peer connection |
| `RTCPeerConnection.createDataChannel()` | Creates data channel |
| `RTCPeerConnection.createOffer()` | Generates SDP offer |
| `RTCPeerConnection.setLocalDescription()` | Sets local description to trigger ICE gathering |
| `RTCPeerConnection.generateCertificate()` | Generates DTLS certificate |
| `RTCPeerConnection.close()` | Cleans up connection |
| `RTCPeerConnection.connectionState` | Reads connection state |
| `new RTCIceCandidate()` | ICE candidate construction |

**SDP offer reveals:**
- Media codec list and ordering (opus, VP8, VP9, H.264, AV1, etc.)
- RTP header extensions and their URIs
- DTLS certificate fingerprint
- ICE candidates (mDNS-obfuscated in Firefox)
- BUNDLE and RTCP-mux capabilities
- Data channel parameters (SCTP port, max message size)

**Output:** Hash of SDP codec/parameter sections (null on Firefox in test data —
likely timed out within 500ms ICE gathering window).

**Notes:** This is a **high-entropy** fingerprint. The codec list and ordering
varies by browser version, OS media stack, and hardware acceleration capabilities.
Static analysis identified this as "500ms timeout, obfuscated" — the 500ms is the
ICE gathering delay.

---

## 25. Media Capabilities & DRM Probing (s209/s211)

Discovered via Firefox Profiler traces. Hidden behind encrypted `Al` string table.

### 25a. MediaCapabilities (s211)

| Web API | Usage |
|---|---|
| `navigator.mediaCapabilities` | Accesses MediaCapabilities API |
| `MediaCapabilities.decodingInfo()` | Queries decoding capability for 8 codec configurations |

**Tests:** Various codec/resolution/bitrate combinations. Returns `supported`,
`smooth`, and `powerEfficient` booleans for each — the `powerEfficient` flag
reveals hardware acceleration, varying by GPU and driver.

### 25b. DRM/EME System Probing (part of s209)

| Web API | Usage |
|---|---|
| `navigator.requestMediaKeySystemAccess()` | Probes DRM system support |

**Key systems probed:**
- `com.widevine.alpha` — Widevine (Linux, Chrome, Firefox)
- `com.apple.fps` — FairPlay (Safari, macOS/iOS)
- `com.microsoft.playready` — PlayReady (Edge, Windows)
- `org.w3.clearkey` — Clear Key (universal)

**Output:** Which DRM systems are available, their supported configurations,
robustness levels, and session types.

---

## 26. WebAuthn Client Capabilities (new signal)

Discovered via Firefox Profiler traces. Possibly added after v3.12.6 static
analysis, or hidden in encrypted code path.

| Web API | Usage |
|---|---|
| `navigator.credentials` | Accesses Credential Management API |
| `PublicKeyCredential.getClientCapabilities()` | Queries WebAuthn client capabilities |

**Capabilities checked:** `conditionalCreate`, `conditionalGet`, `hybridTransport`,
`passkeyPlatformAuthenticator`, `userVerifyingPlatformAuthenticator`,
`relatedOrigins`, `signalAllAcceptedCredentials`, `signalCurrentUserDetails`,
`signalUnknownCredential`.

**Notes:** Varies by OS (Windows Hello vs Touch ID vs Linux), browser version,
and platform authenticator availability.

---

## 27. StorageManager & Quota (new signal)

Discovered via Firefox Profiler traces. Hidden in encrypted code path.

| Web API | Usage |
|---|---|
| `navigator.storage.estimate()` | Returns total quota and current usage |
| `navigator.storage.getDirectory()` | Tests OPFS (Origin Private File System) availability |

**Output:** The quota value is derived from available disk space and reveals
disk configuration. Private browsing mode reduces the quota.

---

## 28. Notification & Permissions API (s106, s95)

| Web API | Usage |
|---|---|
| `Notification.permission` | Reads current notification permission ("granted", "denied", "prompt") |
| `navigator.permissions.query({name: "notifications"})` | Queries notification permission state |
| `PermissionStatus.state` | Reads queried state |

**Output:** Mismatch between `Notification.permission === "denied"` and
`permissions.query(...).state === "prompt"` indicates incognito/private mode.

---

## 29. TLS Fingerprinting (s70 — server-side; result sent as s56)

| Web API | Usage |
|---|---|
| `XMLHttpRequest` or `fetch()` | Makes request to TLS fingerprinting endpoint |

**Mechanism:** The script sends a request to a dedicated TLS endpoint
(`defaultTlsEndpoint` configured per deployment, triggered by signal s70).
The **server** captures the TLS Client Hello message, extracting:
- Cipher suite list and ordering
- TLS extensions and their values
- Supported elliptic curves and point formats
- ALPN protocol list

**Output:** Server-generated TLS fingerprint hash. The result is included
in the main payload as `s56`.

**Notes:** This is a server-side fingerprint — the browser's Web API surface is
only used to make the HTTP request. The actual fingerprinting happens at the TLS
layer. The TLS fingerprint (JA3/JA4 style) is high-entropy and extremely
difficult to spoof from JavaScript.

---

## 30. Performance & Timing Probes (s45, s49, s200)

| Web API | Signal | Usage |
|---|---|---|
| `performance.now()` | s49 | Timer resolution test — runs 50,000 iterations, records two smallest observed deltas |
| `performance.timeOrigin` | s200 | Navigation start timestamp |
| `Date.now()` | s45, s200 | Current timestamp |
| `Date.prototype.getTimezoneOffset()` | s45 | UTC offset |

**Notes:** The `performance.now()` resolution test (s49) detects timer precision
clamping — Firefox reduces resolution to 1ms (or more) under RFP. The two
smallest deltas reveal whether sub-millisecond precision is available.

---

## 31. Persistent Identifiers (s94, s55, s48)

| Web API | Signal | Usage |
|---|---|---|
| `crypto.randomUUID()` or UUID generation | s94 | Generates a persistent visitor UUID |
| `document.cookie` (read/write) | s94, s55 | Persists and reads back visitor token cookie |
| `window.localStorage.getItem()` / `.setItem()` | s94, s55 | Persists and reads back visitor token in localStorage |
| `Math.random()` | s48 | PRNG entropy sampling (array of 6 hash integers from multiple `Math.random()` calls) |

**Output:** s94 generates a UUID (`a53af0f6-fce5-042a-...`) and persists it
across visits via multiple storage mechanisms (cookies, localStorage). s55
reads back the stored visitor token. s48 samples `Math.random()` entropy.

**Notes:** s94 is a stage-1 signal (runs first) because the persistent ID
needs to be available for the TLS endpoint request. The exact storage mechanism
is hidden behind encrypted string tables (`Sa`).

---

## 32. CSS Precision & Rendering Probes (s152, s203)

| Web API | Signal | Usage |
|---|---|---|
| `HTMLElement.style.border` | s152 | Set to `".5px dotted transparent"` |
| `HTMLElement.offsetHeight` | s152 | Reads height — sub-pixel rendering varies by engine |
| CSS `calc()` expression | s203 | Computed value of a `calc()` expression with sub-pixel rounding |

**Output:** s152 returns `0` or `1` depending on whether the browser rounds
0.5px up. s203 returns the computed value (e.g. `"calc(-0.0773484px)"`) — the
rounding behavior differs across engines.

---

## 33. Data Exfiltration

| Web API | Usage |
|---|---|
| `new XMLHttpRequest()` | Creates HTTP request |
| `XMLHttpRequest.open("POST", ...)` | POST to `https://api.fpjs.io/?ci=js/3.12.6&q=<apiKey>` |
| `XMLHttpRequest.setRequestHeader("Content-Type", "text/plain")` | Sets content type |
| `XMLHttpRequest.withCredentials` | Set to `true` (sends cookies cross-origin) |
| `XMLHttpRequest.send()` | Transmits encrypted payload |
| `XMLHttpRequest.onreadystatechange` | Reads response |
| `CompressionStream("deflate-raw")` | Compresses payload when > 1024 bytes |
| `Response.arrayBuffer()` | Reads compressed stream output |
| `window.crypto.getRandomValues()` | Generates random XOR encryption key (9 bytes) + random padding |
| `TextEncoder.encode()` | Encodes payload to bytes |
| `document.addEventListener("securitypolicyviolation", ...)` | Detects CSP violations blocking the request |

**Encoding pipeline:**
1. Custom binary JSON serializer (`Kt`) — not `JSON.stringify`
2. Deflate compression via `CompressionStream("deflate-raw")` if payload > 1024 bytes
3. XOR encryption with random 9-byte key embedded in output header
4. Binary layout: `[random_byte][xored_salt][xored_padding_count][padding...][9-byte key][encrypted_payload]`
5. Salt values: `[3,13]` for uncompressed, `[3,14]` for compressed

---

## 34. Event Handling & Bootstrap

| Web API | Usage |
|---|---|
| `document.addEventListener("DOMContentLoaded", ...)` | Initializes on DOM ready |
| `document.addEventListener("visibilitychange", ...)` | Tracks page visibility for analytics |
| `document.visibilityState` | Reads current visibility |
| `window.setTimeout()` | Various async coordination and timeouts |
| `window.Promise` | Extensive use for async signal collection |
| `window.requestAnimationFrame()` | Used for rendering-dependent signals |

---

## Summary: API Counts by Category

| # | Category | APIs Used | Fingerprinting Entropy |
|---|---|---|---|
| 1 | **Canvas 2D** | 16 | High |
| 2 | **WebGL** | 30+ (vendor/renderer) + 80+ (getParameter constants) + 21 (render) | High |
| 3 | **WebGPU** | 39 | High (experimental) |
| 4 | **Audio** | 18 | High |
| 5 | **Speech synthesis** | 8 | High |
| 6 | **Font detection** | 15 (testing 50 fonts + 7 families) | High |
| 7 | **Screen / display** | 23 | Medium |
| 8 | **Navigator properties** | 19 | High (UA) to Low (vendor) |
| 9 | **UA Client Hints** | 2 (requesting 9 values) | High (Chrome-only) |
| 10 | **Touch / input** | 4 | Low-Medium |
| 11 | **Plugins / MIME** | 11 | Low (modern) |
| 12 | **CSS media queries** | 11 (10 matchMedia + 1 CSS.supports) | Medium |
| 13 | **Math precision** | 19+ functions | Medium |
| 14 | **Text / MathML rendering** | 8 | Medium |
| 15 | **Storage APIs** | 5 | Low |
| 16 | **Cookie support** | 4 | Low |
| 17 | **Timezone / time** | 7 | Medium (timezone) |
| 18 | **Browser / engine detection** | 40+ probes across 9 functions | Low (engine ID) |
| 19 | **Prototype / native integrity** | 15 | Low (engine ID + tampering) |
| 20 | **Bot / automation detection** | 30+ globals + 4 APIs | N/A (security) |
| 21 | **Privacy / ad blocker** | ~200 CSS selectors + 8 APIs | Medium |
| 22 | **Frame / origin** | 8 | Low |
| 23 | **Document / DOM** | 2 (+ 3 in section 19) | Low |
| 24 | **WebRTC SDP** | 8 | High |
| 25 | **Media capabilities / DRM** | 3 | Medium |
| 26 | **WebAuthn** | 2 | Low-Medium |
| 27 | **StorageManager** | 2 | Low |
| 28 | **Notification / permissions** | 3 | Low (incognito detection) |
| 29 | **TLS fingerprint** | 1 (server-side) | High |
| 30 | **Performance / timing** | 4 | Low (timer clamping detection) |
| 31 | **Persistent identifiers** | 4 | N/A (tracking, not fingerprinting) |
| 32 | **CSS precision** | 3 | Low (see also s152 in section 7) |
| 33 | **Data exfiltration** | 11 | N/A (transport) |
| 34 | **Event / bootstrap** | 6 | N/A (lifecycle) |

**Signal IDs:** ~138 unique across 3 modules (91 in `id`, 69 in `bd`, 4 in `ex`; many shared between `id` and `bd`)
**Distinct signals:** ~115 unique (after deduplication across modules)
**Collection functions:** ~100 distinct collection functions
**High-entropy fingerprinting surfaces:** Canvas, WebGL (params + render), WebGPU limits, Audio (oscillator), Fonts (50 probes), Speech voices, WebRTC SDP, TLS, User-Agent
**Encrypted/unresolvable signals:** ~12 (property names hidden behind `Gi` hash dispatch and `Hi`/`Ui` encrypted string tables)

---

## Notable Observations

1. **Massively broader API surface than Akamai.** FPJS accesses ~30+ distinct
   API categories vs Akamai's ~8 relevant categories. The total API call count
   is an order of magnitude larger.

2. **WebGL parameter enumeration is exhaustive.** ~80 GL constants queried via
   `getParameter()`, all shader precisions for all shader types, every extension
   enabled and its parameters read. This alone creates a high-dimensional
   hardware fingerprint.

3. **Three independent rendering fingerprints.** Canvas 2D (text + geometry),
   WebGL (rendered scene), and WebGPU (experimental) provide redundant GPU
   fingerprints that are difficult to spoof consistently.

4. **Audio fingerprint uses unusual DynamicsCompressor parameters.** The specific
   combination of threshold=-50, knee=40, ratio=12, attack=0, release=0.25 with
   a triangle oscillator at 10kHz is carefully chosen to maximize cross-engine
   variation in the compressor implementation.

5. **Font detection uses iframe isolation.** All font measurements are performed
   inside a freshly-created iframe to avoid CSS contamination from the host page.
   Two test strings are used: `"mmMwWLliI0O&1"` (s20 enumeration) and
   `"mmMwWLliI0fiflO&1"` (s51 metrics, includes fi/fl ligatures). Both include
   characters that vary most across fonts (M, W for wide; l, I, 0, O for ambiguous).

6. **Prototype chain validation detects spoofing.** Signals s118 and s136
   verify that `navigator.plugins` and `navigator.mimeTypes` objects have the
   correct prototype chain — a simple object replacement won't pass.

7. **~12 signals are statically unresolvable.** The `Gi(obj, hash)` function
   dispatches property access using a CRC32 hash instead of the property name.
   Without runtime execution, these property names cannot be determined.
   The encrypted signals cover the most sensitive areas: bot detection, storage
   probing, private browsing detection, and TLS fingerprinting.

8. **Server-side TLS fingerprinting.** Unlike all other signals which are
   JavaScript-based, the TLS fingerprint (s70/s94) is captured server-side by
   analyzing the TLS Client Hello. This is immune to JavaScript-level
   countermeasures — only a TLS-level proxy can modify it.

9. **Incognito detection via permission mismatch.** Signal s106 exploits the
   fact that in private mode, `Notification.permission` returns `"denied"` but
   `permissions.query()` returns `"prompt"` — a discrepancy that reveals
   incognito/private browsing.

10. **Ad blocker fingerprinting is remarkably detailed.** ~200 CSS selectors
    from ~40 named filter lists (covering 20+ countries) are injected. The
    specific combination of blocked selectors identifies not just whether an
    ad blocker is present, but exactly which filter lists are subscribed — this
    is a surprisingly high-entropy signal.

11. **Extensive tampering detection.** Multiple signals (s50, s118, s132, s136,
    s148, s151, s155, s159) specifically check for JavaScript environment
    modifications — overridden DOM methods, modified property descriptors,
    altered native function `toString()` output. These make automated spoofing
    significantly harder.

12. **WebRTC SDP and WebGPU are the newest vectors.** Both were discovered only
    through runtime profiling, not static analysis, because the code paths are
    fully encrypted. These represent the cutting edge of browser fingerprinting
    and are not yet widely mitigated.

13. **Math polyfill detection is clever.** Signal s46 computes both the native
    `Math.acosh(x)` and a manual polyfill `Math.log(x + Math.sqrt(x*x - 1))`.
    If the results differ, it reveals which math functions the engine implements
    natively vs via polyfill — a subtle engine-version fingerprint.
