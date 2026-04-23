# Signifyd lite.js — Complete Web API Inventory

Comprehensive list of every Web API that Signifyd's fingerprinting script
accesses, derived from the deobfuscated source (`lite.js`, 5,007 lines),
intercepted payload data (`data.json`), Firefox Profiler traces, and the
existing analysis documents in this directory.

Script source: `https://dp.signifyd.com/fp-web` endpoint
Codebase: ~75–85% derived from CreepJS (forked from commit `c17490f`,
May 20, 2023), with five Signifyd-original additions.

---

## Architecture Overview

The script collects ~385 fields across 21 categories in the raw fingerprint
payload. Before transmission, high-entropy data is SHA-hashed into 13 category
hashes. The final server payload (~118 fields) includes these hashes plus
selected plaintext metadata, encrypted with ECDH/AES-GCM, signed with ECDSA,
and POSTed to `https://dp.signifyd.com/fp-web`.

**Modules removed from CreepJS:** trash/gibberish string detection, headless
browser detection, fingerprint resistance tool detection, bot hash/scoring.

**Modules added by Signifyd:** incognito detection (detectIncognito v1.4.1),
worker context fingerprinting, in-app WebView detection, cookie monster storage
testing, crypto key persistence.

---

## 1. Canvas 2D Fingerprinting (~line 3960)

Renders 5 separate canvases (data, paint, paintCpu, text, emoji), plus a
winding-rule test and TextMetrics measurement. Produces data URIs that are
hashed for the server payload. Uses seed `500`, offset `2001000001`, a
50-color palette starting `#FF6633, #FFB399, #FF33FF, #FFFF99, #00B3E6…`,
and draws character `'A'` at position (7, 37) with emoji at (0, 37).

Pixel modification detection: reads back pixel data via `getImageData()` and
checks if values match expected output. If not, flags `canvas2d.lied = true`
with error `"pixel data modified"` or `"suspicious pixel data"`.

| Web API | Usage |
|---|---|
| `document.createElement("canvas")` | Creates off-screen canvas (7 calls across 5 renders + winding + TextMetrics) |
| `HTMLCanvasElement.getContext("2d")` | Gets 2D rendering context |
| `HTMLCanvasElement.width` / `.height` | Set to various sizes per render |
| `HTMLCanvasElement.toDataURL()` | Called 8 times: once per render, plus winding and emoji variants |
| `CanvasRenderingContext2D.rect()` | Two nested rectangles for winding-rule test: `rect(0,0,10,10)`, `rect(2,2,6,6)` |
| `CanvasRenderingContext2D.isPointInPath()` | Winding test: `isPointInPath(5, 5, "evenodd")` |
| `CanvasRenderingContext2D.fill()` | Standard fill and `fill("evenodd")` for winding test |
| `CanvasRenderingContext2D.fillStyle` | Set to 50+ colors from the palette across all renders |
| `CanvasRenderingContext2D.fillRect()` | Multiple rectangles across all renders |
| `CanvasRenderingContext2D.fillText()` | Text `'A'` at (7, 37), emoji at (0, 37), plus additional text across renders |
| `CanvasRenderingContext2D.strokeText()` | Outlined text rendering in paint canvas |
| `CanvasRenderingContext2D.font` | Set to multiple fonts per render |
| `CanvasRenderingContext2D.textBaseline` | Set to `"alphabetic"` |
| `CanvasRenderingContext2D.beginPath()` | Path operations for arcs in geometry renders |
| `CanvasRenderingContext2D.closePath()` | Closes arc paths |
| `CanvasRenderingContext2D.arc()` | Colored arcs in paint and paintCpu renders |
| `CanvasRenderingContext2D.ellipse()` | Ellipse in paintCpu render |
| `CanvasRenderingContext2D.stroke()` | Stroke text outlines and paths |
| `CanvasRenderingContext2D.strokeStyle` | Stroke color for outlined text |
| `CanvasRenderingContext2D.lineWidth` | Line width for strokes |
| `CanvasRenderingContext2D.setLineDash()` | Dashed line in paint canvas |
| `CanvasRenderingContext2D.quadraticCurveTo()` | Quadratic curve in paint canvas |
| `CanvasRenderingContext2D.moveTo()` | Move to point in paint paths |
| `CanvasRenderingContext2D.lineTo()` | Line to point in paint paths |
| `CanvasRenderingContext2D.globalCompositeOperation` | Set to `"multiply"` for geometry render |
| `CanvasRenderingContext2D.globalAlpha` | Set to `0.5` for transparency layer |
| `CanvasRenderingContext2D.shadowBlur` | Shadow blur `1` in paintCpu (CPU-forced rendering) |
| `CanvasRenderingContext2D.shadowColor` | Shadow color in paintCpu |
| `CanvasRenderingContext2D.shadowOffsetX` | Shadow X offset in paintCpu |
| `CanvasRenderingContext2D.shadowOffsetY` | Shadow Y offset in paintCpu |
| `CanvasRenderingContext2D.getImageData()` | Reads pixel data for tamper detection (~780 profiler samples) |
| `CanvasRenderingContext2D.measureText()` | Measures text metrics for font fingerprinting (see section 8) |

**Output:** `{dataURI, paintURI, paintCpuURI, textURI, emojiURI, mods.pixelImage, textMetricsSystemSum, liedTextMetrics, emojiSet, lied}` — data URIs are SHA-hashed for the server payload.

---

## 2. TextMetrics Fingerprinting (~line 4217, function Rr)

Iterates over the 48-font CSS font family list (`Ve`) and for each font calls
`measureText()`, then reads all 7 TextMetrics properties. Unique per-font
signatures are collected via a `Set`, and a `textMetricsSystemSum` is computed
as the sum of all metric values scaled by 1e-5.

Additionally (~line 4262), checks whether any bounding box values have
fractional parts (`% 1 !== 0`). If so, flags `liedTextMetrics: true` —
detecting RFP or similar protections that add noise to these values.

| Web API | Usage |
|---|---|
| `CanvasRenderingContext2D.measureText()` | Called once per font in the 48-font list |
| `TextMetrics.width` | Horizontal advance width |
| `TextMetrics.actualBoundingBoxLeft` | Left edge of bounding box |
| `TextMetrics.actualBoundingBoxRight` | Right edge of bounding box |
| `TextMetrics.actualBoundingBoxAscent` | Ascent above baseline |
| `TextMetrics.actualBoundingBoxDescent` | Descent below baseline |
| `TextMetrics.fontBoundingBoxAscent` | Font-level ascent |
| `TextMetrics.fontBoundingBoxDescent` | Font-level descent |

**Output:** `textMetricsSystemSum` (float) and `liedTextMetrics` (boolean).

**Notes:** The 7 values per font are joined into a comma-separated signature
string. These sub-pixel-precise metrics vary by font renderer (FreeType vs
DirectWrite vs CoreText), hinting settings, and OS text configuration. This is
a higher-detail fingerprint than `measureText().width` alone. No RFP target
protects `measureText()` return values — `CanvasRandomization` only protects
extracted pixel data.

---

## 3. WebGL Fingerprinting (~line 2634, function Zn)

Extracts GPU vendor and renderer strings via the WebGL debug extension. Uses
`OffscreenCanvas` when available, falling back to a standard canvas element.

| Web API | Usage |
|---|---|
| `OffscreenCanvas` constructor | `new OffscreenCanvas(256, 256)` if available |
| `document.createElement("canvas")` | Fallback if OffscreenCanvas unavailable |
| `HTMLCanvasElement.getContext("webgl")` | Gets WebGL1 context |
| `WebGLRenderingContext.getExtension("WEBGL_debug_renderer_info")` | Debug renderer extension |
| `WebGLRenderingContext.getParameter(UNMASKED_VENDOR_WEBGL)` | Real GPU vendor string (e.g. `"AMD"`) |
| `WebGLRenderingContext.getParameter(UNMASKED_RENDERER_WEBGL)` | Real GPU model (e.g. `"Radeon R9 200 Series, or similar"`) |

**Output:** `{webglVendor, webglRenderer}` — collected in main thread and
repeated inside Web Worker via OffscreenCanvas.

**Notes:** Unlike FingerprintJS Pro, Signifyd does **not** perform a full
WebGL parameter dump (~80 constants) or render a WebGL image hash. It only
extracts the vendor/renderer identity strings.

---

## 4. WebGPU Fingerprinting (~line 1596, function cn)

Queries GPU adapter limits and features via the WebGPU API. Returns 14 limit
values, a sorted feature list, adapter info, and a fallback adapter flag.

| Web API | Usage |
|---|---|
| `navigator.gpu` | WebGPU availability check |
| `navigator.gpu.requestAdapter()` | Request GPU adapter |
| `GPUAdapter.features` | Feature set (spread to sorted array) |
| `GPUAdapter.limits.maxBindGroups` | Bind group limit |
| `GPUAdapter.limits.maxDynamicUniformBuffersPerPipelineLayout` | Dynamic uniform buffer limit |
| `GPUAdapter.limits.maxDynamicStorageBuffersPerPipelineLayout` | Dynamic storage buffer limit |
| `GPUAdapter.limits.maxBufferSize` | Maximum buffer size |
| `GPUAdapter.limits.maxColorAttachments` | Color attachment limit |
| `GPUAdapter.limits.maxComputeWorkgroupStorageSize` | Compute workgroup storage limit |
| `GPUAdapter.limits.maxComputeInvocationsPerWorkgroup` | Compute invocations limit |
| `GPUAdapter.limits.maxTextureDimension1D` | 1D texture limit |
| `GPUAdapter.limits.maxTextureDimension2D` | 2D texture limit |
| `GPUAdapter.limits.maxTextureDimension3D` | 3D texture limit |
| `GPUAdapter.limits.maxStorageBuffersPerShaderStage` | Storage buffers per stage |
| `GPUAdapter.limits.maxUniformBufferBindingSize` | Uniform buffer binding limit |
| `GPUAdapter.limits.maxVertexBuffers` | Vertex buffer limit |
| `GPUAdapter.limits.maxVertexAttributes` | Vertex attribute limit |
| `GPUAdapter.info.architecture` | GPU architecture string |
| `GPUAdapter.info.device` | GPU device string |
| `GPUAdapter.info.description` | GPU description string |
| `GPUAdapter.info.vendor` | GPU vendor string |
| `GPUAdapter.isFallbackAdapter` | Whether this is a software fallback |

**Output:** `{features[], limits{14 values}, info{4 strings}, isFallbackAdapter, lied}`.

---

## 5. Audio Fingerprinting — OfflineAudioContext (~line 1940, function Dn)

Creates an `OfflineAudioContext(1, 100, 44100)`, routes a triangle-wave
oscillator through a dynamics compressor, and analyzes the rendered audio
buffer. Also reads default/min/max values from audio node parameters.

| Web API | Usage |
|---|---|
| `new OfflineAudioContext(1, 100, 44100)` | Creates offline context: 1 channel, 100 frames, 44100 Hz |
| `OfflineAudioContext.createOscillator()` | Creates oscillator node |
| `OscillatorNode.type` | Set to `"triangle"` |
| `OscillatorNode.frequency.value` | Set to `10000` |
| `OscillatorNode.connect()` | Connect to compressor |
| `OscillatorNode.start(0)` | Start oscillator |
| `OfflineAudioContext.createDynamicsCompressor()` | Creates compressor node |
| `DynamicsCompressorNode.threshold.value` | Set to `-50` |
| `DynamicsCompressorNode.knee.value` | Set to `40` |
| `DynamicsCompressorNode.attack.value` | Set to `0` |
| `DynamicsCompressorNode.reduction` | Read compressor gain reduction |
| `DynamicsCompressorNode.connect()` | Connect to analyser |
| `OfflineAudioContext.createAnalyser()` | Creates analyser node |
| `AnalyserNode.getFloatFrequencyData()` | Read frequency domain data |
| `AnalyserNode.getFloatTimeDomainData()` | Read time domain data |
| `AnalyserNode.channelCount` | Read channel count (default `2`) |
| `AnalyserNode.channelCountMode` | Read mode (default `"max"`) |
| `AnalyserNode.channelInterpretation` | Read interpretation (default `"speakers"`) |
| `AnalyserNode.fftSize` | Read FFT size (default `2048`) |
| `AnalyserNode.frequencyBinCount` | Read bin count (default `1024`) |
| `AnalyserNode.maxDecibels` | Read max dB (default `-30`) |
| `AnalyserNode.minDecibels` | Read min dB (default `-100`) |
| `AnalyserNode.numberOfInputs` | Read input count (default `1`) |
| `AnalyserNode.numberOfOutputs` | Read output count (default `1`) |
| `AnalyserNode.smoothingTimeConstant` | Read smoothing (default `0.8`) |
| `AnalyserNode.connect()` | Connect to destination |
| `OfflineAudioContext.startRendering()` | Render audio |
| `AudioBuffer.getChannelData()` | Read rendered channel data |
| `AudioBuffer.copyFromChannel()` | Copy channel data for cross-verification |
| `BiquadFilterNode.gain.maxValue` | Read gain max (default `3.4028e+38`) |
| `BiquadFilterNode.frequency.defaultValue` | Read frequency default (`350`) |
| `BiquadFilterNode.frequency.maxValue` | Read frequency max (`22050`) |
| `DynamicsCompressorNode.attack.defaultValue` | Read attack default (`0.003`) |
| `DynamicsCompressorNode.knee.defaultValue` | Read knee default (`30`) |
| `DynamicsCompressorNode.knee.maxValue` | Read knee max (`40`) |
| `DynamicsCompressorNode.ratio.defaultValue` | Read ratio default (`12`) |
| `DynamicsCompressorNode.ratio.maxValue` | Read ratio max (`20`) |
| `DynamicsCompressorNode.release.defaultValue` | Read release default (`0.25`) |
| `DynamicsCompressorNode.release.maxValue` | Read release max (`1`) |
| `DynamicsCompressorNode.threshold.defaultValue` | Read threshold default (`-24`) |
| `DynamicsCompressorNode.threshold.minValue` | Read threshold min (`-100`) |
| `OscillatorNode.detune.maxValue` | Read detune max (`3.4028e+38`) |
| `OscillatorNode.detune.minValue` | Read detune min (`-3.4028e+38`) |
| `OscillatorNode.frequency.defaultValue` | Read frequency default (`440`) |
| `OscillatorNode.frequency.maxValue` | Read frequency max (`22050`) |
| `OscillatorNode.frequency.minValue` | Read frequency min (`-22050`) |

**Output:** `{totalUniqueSamples, compressorGainReduction, floatFrequencyDataSum, floatTimeDomainDataSum, sampleSum, binsSample[100], copySample[100], values{AnalyserNode.*, BiquadFilterNode.*, DynamicsCompressorNode.*, OscillatorNode.*}, noise, lied, reliable}`.

**Notes:** The audio noise detection checks if `getChannelData` and
`copyFromChannel` return matching samples. Mismatches trigger error strings:
`"getChannelData and copyFromChannel samples mismatch"`,
`"expected -Infinity (silence) and got "`, `"sample noise detected"`.

---

## 6. AudioWorklet Fingerprinting (~line 2870, function tr)

Creates an AudioWorklet processor from a Blob URL, generates silence through
it, and reads the output channel sums. The worklet processes audio at
192000 Hz sample rate.

| Web API | Usage |
|---|---|
| `new Blob()` | Creates AudioWorklet processor script |
| `URL.createObjectURL()` | Creates Blob URL for worklet module |
| `URL.revokeObjectURL()` | Cleans up Blob URL |
| `OfflineAudioContext.audioWorklet.addModule()` | Loads worklet processor: `"profiling-audio-processor"` |
| `new AudioWorkletNode()` | Creates worklet node connected to context |
| `AudioBuffer.numberOfChannels` | Read channel count |
| `AudioBuffer.sampleRate` | Read sample rate (`192000`) |
| `AudioBuffer.duration` | Read buffer duration |
| `AudioBuffer.getChannelData()` | Read channel data from worklet output |

**Output:** `{duration, numberOfChannels, sampleRate, channel_0_sum, channel_1_sum, reliable}`.

---

## 7. SVG Fingerprinting (~line 3681, function mr)

Creates an off-screen SVG container (`position: absolute; left: -9999px`),
renders emoji text at `font-size: 200px` with `scale(1.000999)` transform,
and measures SVG element dimensions. Uses the `.shift-svg` and
`.svgrect-emoji` CSS classes.

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates container for SVG injection |
| `Element.innerHTML` | Sets SVG markup with `<text>` elements |
| `SVGRectElement.getBBox()` | Bounding box measurement |
| `SVGTextContentElement.getComputedTextLength()` | Text length of emoji strings |
| `SVGTextContentElement.getNumberOfChars()` | Character count |
| `SVGTextContentElement.getExtentOfChar()` | Extent of character 0 (width + height) |
| `SVGTextContentElement.getSubStringLength()` | Substring length: `0` to `min(10, numChars)` |
| `Element.classList.add()` / `.remove()` | `.shift-svg` class for transform-based lie detection |
| `document.getElementById()` | Find SVG elements by ID |
| `document.getElementsByClassName()` | Find emoji elements by class |

**Output:** `{bBox, extentOfChar, subStringLength, computedTextLength, emojiSet[19], svgrectSystemSum, lied}`.

**Notes:** 19 emoji codepoints are used for emoji rendering dimension
fingerprinting. The `svgrectSystemSum` is computed as a checksum of fractional
SVGRect values (same formula as `domrectSystemSum`).

---

## 8. DOMRect / ClientRects Fingerprinting (~line 4370, function Pr)

Creates 12 elements (`#cRect1`–`#cRect12`) with highly specific CSS transforms,
plus a `.rect-known` element (100×100px, `rotate(45deg)`) and a `.rect-ghost`
element (0×0px). Measures sub-pixel rendering differences across browsers.

Identical to CreepJS — same element IDs, CSS values, transform values, border
colors, and 91 emoji codepoints.

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates container with 12+ child elements |
| `Element.setAttribute()` | Sets `id` attribute on container |
| `document.getElementById()` | Finds container and elements by ID |
| `document.getElementsByClassName()` | Finds elements by class (`.rects`, `.domrect-emoji`) |
| `Element.getClientRects()` | Client rects on all 12 `#cRect` elements |
| `Element.getBoundingClientRect()` | Bounding rect on all 12 `#cRect` elements |
| `document.createRange()` | Creates Range for range-based rect measurements |
| `Range.selectNode()` | Selects element for range measurement |
| `Range.getClientRects()` | Range-based client rects on all 12 elements |
| `Range.getBoundingClientRect()` | Range-based bounding rect on all 12 elements |
| `Element.classList.add()` / `.remove()` | Shift test for lie detection |

**CSS transforms used (fingerprinting-critical values):**

| Element | Transform |
|---|---|
| `.rect-known` | `rotate(45deg)` |
| `#cRect1` | border `solid 2.715px #F72585`, padding `3.98px`, margin-left `12.12px` |
| `#cRect2` | `skewY(23.1753218deg) rotate3d(10.00099, 90, 0.100000000000009, 60000000000008.00000009deg)` |
| `#cRect3` | `skewY(-23.1753218deg) scale(1099.0000000099, 1.89) matrix(1.11, 2.0001, -1.0001, 1.009, 150, 94.4)` |
| `#cRect4` | `matrix(1.11, 2.0001, -1.0001, 1.009, 150, 94.4)` |
| `#cRect5` | margin-left `42.395pt` |
| `#cRect6` | `perspective(12890px) translateZ(101.5px)` |
| `.domrect-emoji` | `scale(1.000999)` |

**Lie detection (6 methods, identical to CreepJS):**
1. API spoof check — verifies `getClientRects`/`getBoundingClientRect` not spoofed
2. Shift test — adds/removes CSS class, compares top values
3. Math consistency — verifies `right - left === width`, etc.
4. Equal elements — compares `#cRect11` vs `#cRect12` (should be equal)
5. Hash check — verifies `.rect-known` hash against known values per engine
6. Ghost dimensions — checks `.rect-ghost` has all zeros

**Output:** `{elementClientRects[12], elementBoundingClientRect[12], rangeClientRects[12], rangeBoundingClientRect[12], emojiSet[19], domrectSystemSum, lied}`.

---

## 9. CSS Computed Styles (~line 3217, function fr)

Reads all CSS property names, 38 system colors, and 6 system fonts via
`getComputedStyle()`.

| Web API | Usage |
|---|---|
| `window.getComputedStyle()` | Read computed styles on test elements |
| `CSSStyleDeclaration.getPropertyValue()` | Read individual CSS properties |
| `document.styleSheets` | Access CSSStyleSheet list |
| `CSSStyleSheet.cssRules` | Read CSS rules |
| `HTMLElement.style` | Direct style access |

**System colors enumerated (38):** `ActiveBorder`, `ActiveCaption`,
`ActiveText`, `AppWorkspace`, `Background`, `ButtonBorder`, `ButtonFace`,
`ButtonHighlight`, `ButtonShadow`, `ButtonText`, `Canvas`, `CanvasText`,
`CaptionText`, `Field`, `FieldText`, `GrayText`, `Highlight`,
`HighlightText`, `InactiveBorder`, `InactiveCaption`, `InactiveCaptionText`,
`InfoBackground`, `InfoText`, `LinkText`, `Mark`, `MarkText`, `Menu`,
`MenuText`, `Scrollbar`, `ThreeDDarkShadow`, `ThreeDFace`,
`ThreeDHighlight`, `ThreeDLightShadow`, `ThreeDShadow`, `VisitedText`,
`Window`, `WindowFrame`, `WindowText`.

**System fonts enumerated (6):** `caption`, `icon`, `menu`, `message-box`,
`small-caption`, `status-bar`.

**CSS property enumeration (~line 3257):** Full property name enumeration via
`Object.keys()`, `Object.getPrototypeOf()`, `Object.getOwnPropertyNames()` on
the `CSSStyleDeclaration` prototype chain. Returns ~1162 property names
including vendor-prefixed variants.

**Output:** `{computedStyle.keys[], computedStyle.interfaceName, system.colors[38], system.fonts[6], lied}`.

---

## 10. CSS Media Queries (~line 3428, function ur)

Probes 13 CSS media features via both CSS `@media` rules (injected stylesheet)
and the JavaScript `matchMedia()` API, plus screen dimension binary search.

| Web API | Usage |
|---|---|
| `window.matchMedia()` | Tests 13 media queries via JS API (~106 profiler samples) |
| `MediaQueryList.matches` | Boolean result of each media query |
| `document.createElement("style")` | Injects `@media` CSS rules |
| `Element.textContent` | Sets CSS text of injected style |
| `CSSStyleDeclaration.getPropertyValue()` | Reads CSS custom properties set by `@media` rules |
| `document.head.appendChild()` | Appends style element |
| `Element.removeChild()` | Removes style element after reading |

**Media features queried (13):**

| Media Feature | Values Detected |
|---|---|
| `prefers-reduced-motion` | `no-preference` / `reduce` |
| `prefers-color-scheme` | `light` / `dark` |
| `monochrome` | `monochrome` / `non-monochrome` |
| `inverted-colors` | `inverted` / `none` |
| `forced-colors` | `active` / `none` |
| `any-hover` | `hover` / `none` |
| `hover` | `hover` / `none` |
| `any-pointer` | `fine` / `coarse` / `none` |
| `pointer` | `fine` / `coarse` / `none` |
| `device-aspect-ratio` | Computed ratio (e.g. `"16/9"`) |
| `device-screen` | Dimensions (e.g. `"3840 x 2160"`) |
| `display-mode` | `browser` / `standalone` / `fullscreen` / `minimal-ui` |
| `color-gamut` | `srgb` / `p3` / `rec2020` |

**Screen dimension probing:** Binary search using `matchMedia` with
`(device-width)` and `(device-height)` queries to determine exact screen
resolution.

**Output:** `{mediaCSS{13 features}, matchMediaCSS{13 features}, screenQuery{width, height}, orientation}`.

---

## 11. Screen Properties (~line 3587, function hr)

Reads standard screen properties and device pixel ratio.

| Web API | Usage |
|---|---|
| `Screen.width` | Screen width (e.g. `3840`) |
| `Screen.height` | Screen height (e.g. `2160`) |
| `Screen.availWidth` | Available width |
| `Screen.availHeight` | Available height |
| `Screen.colorDepth` | Color depth (e.g. `24`) |
| `Screen.pixelDepth` | Pixel depth (e.g. `24`) |
| `Screen.orientation.type` | Orientation type string |
| `window.devicePixelRatio` | Device pixel ratio |
| `window.innerWidth` | Inner window width |
| `window.innerHeight` | Inner window height |
| `window.orientation` | Window orientation (deprecated) |

**Touch detection (~line 3101):**

| Web API | Usage |
|---|---|
| `navigator.maxTouchPoints` | Touch point count (0 on desktop) |
| `'ontouchstart' in window` | Touch event support check |

**Output:** `{width, height, availWidth, availHeight, colorDepth, pixelDepth, touch, lied}`.

---

## 12. Navigator Properties (~line 2660)

Reads browser identity properties from the main `navigator` object. The same
properties are independently collected in Web Worker and SharedWorker contexts
(see section 19).

| Web API | Fingerprinting Use |
|---|---|
| `navigator.userAgent` | Full UA string — **high entropy** |
| `navigator.platform` | OS identification (e.g. `"Linux x86_64"`) |
| `navigator.appVersion` | App version string (e.g. `"5.0 (X11)"`) |
| `navigator.appCodeName` | Legacy code name (`"Mozilla"`) |
| `navigator.language` | Primary language (e.g. `"en-US"`) |
| `navigator.languages` | Ordered language preference array |
| `navigator.hardwareConcurrency` | CPU logical core count |
| `navigator.deviceMemory` | Device RAM in GiB (Chrome-only) |
| `navigator.maxTouchPoints` | Touch capability |
| `navigator.vendor` | Browser vendor (e.g. `""` in Firefox, `"Google Inc."` in Chrome) |
| `navigator.oscpu` | Firefox-only OS+arch string |
| `navigator.product` | Always `"Gecko"` (lie detection target) |
| `navigator.productSub` | Build identifier |
| `navigator.vendorSub` | Always `""` (lie detection target) |
| `navigator.buildID` | Firefox build timestamp |
| `navigator.webdriver` | Automation detection flag |
| `navigator.doNotTrack` | DNT preference (`"1"`, `"0"`, `"unspecified"`) |
| `navigator.globalPrivacyControl` | GPC signal (boolean) |
| `navigator.cookieEnabled` | Cookie support boolean |
| `navigator.connection` | NetworkInformation: downlink, effectiveType, rtt, saveData |
| `navigator.userAgentData` | Client Hints UA data object |
| `navigator.userAgentData.brands` | Brand list array |
| `navigator.userAgentData.mobile` | Mobile flag boolean |
| `navigator.userAgentData.getHighEntropyValues()` | Requests: `brands`, `mobile`, `platform`, `architecture`, `bitness`, `formFactor`, `fullVersionList`, `model`, `platformVersion`, `uaFullVersion`, `wow64` |

**Output:** Plaintext in server payload (not hashed).

---

## 13. Plugins / MIME Types (~line 2617, function Yn)

Enumerates installed plugins and MIME types from the `navigator` object.

| Web API | Usage |
|---|---|
| `navigator.plugins` | Plugin array enumeration |
| `Plugin.name` | Plugin name (e.g. `"PDF Viewer"`) |
| `Plugin.description` | Plugin description |
| `Plugin.filename` | Plugin filename (e.g. `"internal-pdf-viewer"`) |
| `Plugin.version` | Plugin version (often null) |
| `navigator.mimeTypes` | MIME type array enumeration |
| `MimeType.type` | MIME type string (e.g. `"application/pdf"`) |

**Output:** 5 standard PDF viewer plugin entries in modern browsers.

---

## 14. Intl API Fingerprinting (~line 1687, function dn)

Probes all Intl API constructors and their `resolvedOptions()` output. Tests
6 Intl constructors with specific inputs.

| Web API | Usage |
|---|---|
| `Intl.DateTimeFormat()` | Constructs formatter |
| `Intl.DateTimeFormat().resolvedOptions()` | Extracts: locale, calendar, numberingSystem, timeZone |
| `Intl.DateTimeFormat().format()` | Formats `new Date(963644400000)` |
| `Intl.DisplayNames("en-US", {type:"language"})` | Language display name |
| `Intl.ListFormat([], {style:"long", type:"disjunction"}).format(["0","1"])` | List formatting |
| `Intl.NumberFormat([], {notation:"compact", compactDisplay:"long"}).format(21000000)` | Number formatting |
| `Intl.PluralRules().select(1)` | Plural rule |
| `Intl.RelativeTimeFormat([], {localeMatcher:"best fit", numeric:"auto", style:"long"}).format(1, "year")` | Relative time |
| `Intl.Collator()` | Locale extraction |

**Output:** `{dateTimeFormat, displayNames, listFormat, numberFormat, pluralRules, relativeTimeFormat, locale, lied}`.

---

## 15. Timezone Fingerprinting (~line 3829, function yr)

Uses magic year `1113` for timezone probing, collects both the IANA timezone
name and epoch-based offset measurements.

| Web API | Usage |
|---|---|
| `new Date().getTimezoneOffset()` | Current timezone offset (e.g. `300`) |
| `new Date().toString()` | Extracts timezone name from parenthesized string |
| `new Date("7/1/1113")` | Magic year for epoch-based timezone detection |
| `Date.toISOString()` | ISO string for epoch comparison |
| `Intl.DateTimeFormat().resolvedOptions().timeZone` | IANA timezone identifier |

**Output:** `{zone, location, locationMeasured, locationEpoch, offset, offsetComputed, lied}`.

---

## 16. Performance / Timing (~line 2175 and ~line 2350)

Collects navigation timing data and measures `performance.now()` resolution.

| Web API | Usage |
|---|---|
| `performance.now()` | Called 5,000 times in tight loop to measure timing resolution (~20K profiler samples) |
| `performance.timeOrigin` | Page load time origin |
| `performance.timing.*` | All 21 PerformanceTiming properties (navigationStart through loadEventEnd) |
| `performance.navigation.type` | Navigation type (0 = direct, 1 = reload, 2 = back/forward) |
| `performance.navigation.redirectCount` | Redirect count |
| `performance.memory.jsHeapSizeLimit` | JS heap size limit (Chromium-only, used for incognito detection) |

**Output:** `{timing{21 properties}, navigation{type, redirectCount}, timeOrigin}` plus `performanceData.timingRes[2]` (resolution test).

---

## 17. WebRTC IP Detection (~line 2270, function jn)

Creates an RTCPeerConnection with STUN servers, generates ICE candidates, and
parses them for the user's IP address. **Does not** perform SDP codec
fingerprinting — the `createOffer` call is solely for triggering ICE candidate
generation.

| Web API | Usage |
|---|---|
| `new RTCPeerConnection(config)` | STUN config: `stun.l.google.com:19302`, `stun1.l.google.com:19302`, `stun2.l.google.com:19302`, `stun.services.mozilla.com` |
| `RTCPeerConnection.createDataChannel()` | Creates `"dummyChannel"` — no audio/video transceivers |
| `RTCPeerConnection.createOffer()` | Generates SDP offer to trigger ICE |
| `RTCPeerConnection.setLocalDescription()` | Sets local SDP |
| `RTCPeerConnection.onicecandidate` | ICE candidate handler — parses IPv4/IPv6 addresses, skips mDNS candidates |
| `RTCPeerConnection.close()` | Cleanup with 2000ms timeout |

**Output:** `{ipAddresses[], lied}`.

**Notes:** The high `RTCPeerConnection.constructor` sample count (124) in the
profiler is explained by the lie detection module (`searchLies`), which probes
RTCPeerConnection for API tampering by repeatedly constructing instances and
testing prototype integrity.

---

## 18. Permissions Probing (~line 2583, function Jn)

Queries the Permissions API for the state of 39 permission names. Collects
results as granted/denied/prompt/unknown arrays.

| Web API | Usage |
|---|---|
| `navigator.permissions.query()` | Called for each of 39 permission names (~78 profiler samples) |
| `PermissionStatus.state` | Read state: `granted` / `denied` / `prompt` (~18 profiler samples) |

**Permissions queried (39):** `accelerometer`, `ambient-light-sensor`,
`background-fetch`, `background-sync`, `bluetooth`, `camera`, `clipboard-read`,
`clipboard-write`, `device-info`, `display-capture`, `gamepad`, `geolocation`,
`gyroscope`, `magnetometer`, `microphone`, `midi`, `nfc`, `notifications`,
`persistent-storage`, `push`, `screen-wake-lock`, `speaker`,
`speaker-selection`, `local-fonts`, `idle-detection`, `media-session`,
`presentation`, `serial`, `storage-access`, `window-placement`, `web-share`,
`file-handling`, `screen-capture`, `usb`, `payment-handler`,
`accessibility-events`, `file-system-access`, `battery`, `sensors`.

**Output:** `{granted[], denied[], prompt[], unknown[]}`.

---

## 19. Worker Context Fingerprinting (~line 2740 — Signifyd Original)

Signifyd's most distinctive addition. Creates Web Worker and SharedWorker
instances from inline Blob scripts (~4KB each) that independently collect
full navigator profiles. Results from all three contexts (main, web worker,
shared worker) are compared to detect spoofing inconsistencies — privacy tools
often fail to consistently modify all execution contexts.

### 19a. Worker Creation

| Web API | Usage |
|---|---|
| `new Blob([code], {type:"application/javascript"})` | Creates inline worker script from string |
| `URL.createObjectURL()` | Generates Blob URL for worker |
| `URL.revokeObjectURL()` | Cleans up Blob URL after worker starts |
| `new Worker(blobURL)` | Creates dedicated Web Worker |
| `new SharedWorker(blobURL)` | Creates Shared Worker |
| `Worker.postMessage()` | Sends `null` to trigger profile collection |
| `Worker.onmessage` | Receives profile results |
| `SharedWorker.port.start()` | Starts SharedWorker port |
| `SharedWorker.port.postMessage()` | Triggers SharedWorker collection |
| `queueMicrotask()` | Deferred Blob URL cleanup |

### 19b. Data Collected Inside Each Worker

Each worker independently collects:

| Web API (inside worker) | Usage |
|---|---|
| `navigator.platform` | OS identification |
| `navigator.userAgent` | UA string |
| `navigator.appVersion` | Version string |
| `navigator.appCodeName` | Code name |
| `navigator.hardwareConcurrency` | CPU core count |
| `navigator.deviceMemory` | RAM (Chrome-only) |
| `navigator.language` | Language |
| `navigator.webdriver` | Automation flag |
| `navigator.maxTouchPoints` | Touch capability |
| `navigator.vendor` | Browser vendor |
| `navigator.oscpu` | OS/CPU (Firefox) |
| `navigator.plugins` | Plugin list (name, description, filename, version) |
| `navigator.mimeTypes` | MIME types |
| `navigator.userAgentData.brands` | UA-CH brands |
| `navigator.userAgentData.mobile` | UA-CH mobile flag |
| `navigator.userAgentData.getHighEntropyValues()` | 11 high-entropy values (see section 12) |
| `navigator.permissions.query()` | Same 39 permissions as main thread |
| `navigator.bluetooth.getAvailability()` | Bluetooth availability |
| `navigator.doNotTrack` | DNT preference |
| `navigator.globalPrivacyControl` | GPC signal |
| `navigator.storage.estimate()` | Storage quota |
| `new OffscreenCanvas(256, 256)` | WebGL in worker context |
| `OffscreenCanvas.getContext("webgl")` | Worker WebGL context |
| `WebGLRenderingContext.getExtension("WEBGL_debug_renderer_info")` | Debug extension in worker |
| `WebGLRenderingContext.getParameter(UNMASKED_VENDOR_WEBGL)` | GPU vendor in worker |
| `WebGLRenderingContext.getParameter(UNMASKED_RENDERER_WEBGL)` | GPU renderer in worker |
| `Intl.DateTimeFormat().resolvedOptions()` | Locale/timezone in worker |
| `new Date().getTimezoneOffset()` | Timezone offset in worker |

**Output:** `workers.{main,web,shared}` each containing: `{context, timezone, navigator{permissions, platform, userAgent, appVersion, hardwareConcurrency, deviceMemory, language, webdriver, maxTouchPoints, vendor, oscpu, plugins, mimeTypes, appCodeName, webGL{vendor,renderer}, userAgentData, doNotTrack, globalPrivacyControl}, intl{locale, calendar, numberingSystem, timeZone, year, month, day}, anomalies[], errors[]}`.

---

## 20. Incognito / Private Browsing Detection (~line 3060 — detectIncognito v1.4.1)

Embedded verbatim from the `detectIncognito` library by Joe12387. Uses
browser-specific storage and quota APIs to infer private browsing mode.

| Web API | Browser | Usage |
|---|---|---|
| `window.openDatabase(null, null, null, null)` | Safari macOS | Throws in private mode |
| `window.localStorage.setItem("test", "1")` | Safari macOS | Throws in private mode |
| `window.localStorage.removeItem("test")` | Safari macOS | Cleanup |
| `window.indexedDB.open(testId, 1)` | Chrome | Opens test database |
| `IDBDatabase.createObjectStore("test", {autoIncrement:true})` | Chrome | Creates test store |
| `IDBObjectStore.put(new Blob())` | Chrome | Tests Blob storage (fails in old incognito) |
| `IDBDatabase.close()` | Chrome | Closes test DB |
| `window.indexedDB.deleteDatabase(testId)` | Chrome | Deletes test DB |
| `navigator.storage.estimate()` | Chrome | Quota < 2GB indicates incognito |
| `navigator.webkitTemporaryStorage.queryUsageAndQuota()` | Legacy Chrome | Compares quota to heap limit |
| `window.performance.memory.jsHeapSizeLimit` | Chrome | Heap limit for quota comparison (also read in section 16) |
| `window.webkitRequestFileSystem(0, 1, …)` | Very old Chrome | Filesystem API fails in incognito |
| `navigator.serviceWorker` | Firefox | `undefined` in private browsing |
| `window.indexedDB` | IE | `undefined` in InPrivate |
| `navigator.msSaveBlob` | IE | IE detection (checks `!== undefined`) |
| `eval.toString().length` | IE | IE detection (length `=== 39`) |
| `navigator.brave` | Brave | Brave browser detection |

**JS engine identification:** `parseInt("-1").toFixed(-1)` generates an error
whose `message.length` identifies the engine: SpiderMonkey = `25`, V8 = `51`,
JavaScriptCore = `44`.

**Output:** `{isPrivate, browserName}`.

---

## 21. Cookie Monster (~line 720, function vt — Signifyd Original)

Reads the browser's cookie-enabled flag. Despite the name "cookie monster",
the actual implementation in `lite.js` is minimal — it only checks
`navigator.cookieEnabled`. The more elaborate storage testing described in
the standalone `lite-without-creep/fingerprint.js` extraction is not present
in the deployed script.

| Web API | Usage |
|---|---|
| `navigator.cookieEnabled` | Cookie support boolean |

**Output:** `{cookies: boolean}`.

---

## 22. In-App WebView Detection (~line 4485 — Signifyd Original)

Detects whether the page runs inside a native app's embedded browser by
matching UA string patterns and checking for missing APIs.

| Web API | Usage |
|---|---|
| `navigator.userAgent` | Regex matching for WebView indicators |
| `window.matchMedia` | Existence check — absence indicates WebView |
| `window.indexedDB` | Existence check — absence indicates WebView |
| `navigator.maxTouchPoints` | iOS device classification |
| `document.documentElement.clientWidth` | Viewport width for device classification |
| `window.innerWidth` | Window width for device classification |

**UA patterns matched:**

| Pattern | Target |
|---|---|
| `/CriOS/` | Chrome on iOS |
| `/FxiOS/` | Firefox on iOS |
| `/EdgiOS/` | Edge on iOS |
| `/OPiOS/` | Opera on iOS |
| `/DuckDuckGo/` | DuckDuckGo on iOS |
| `/YaBrowser/` | Yandex Browser on iOS |
| `/\binstagram\b/` | Instagram in-app browser |
| `/\bfbav\|fban\|fb_iab\b/` | Facebook in-app browser |
| `/\btiktok\b/` | TikTok in-app browser |
| `/\bsnapchat\b/` | Snapchat in-app browser |
| `/; wv\)/` | Android WebView |
| `/Version\/[\d.]+.*Chrome/` | Android WebView (legacy) |

**Output:** Device classification object (iOS browser type, Android WebView,
in-app WebView, desktop).

---

## 23. Window Features / Property Enumeration (~line 3927, function _r)

Enumerates all properties on the `window` object and counts vendor-prefixed
ones, providing a browser/version fingerprint.

| Web API | Usage |
|---|---|
| `Object.getOwnPropertyNames(window)` | Enumerates all window properties |

**Categorization:** Counts properties matching `/moz/`, `/webkit/`, `/apple/`
patterns; filters out `/_|\d{3,}/` patterns.

**Output:** `{keys[~970], moz (count), webkit (count), apple (count)}`.

---

## 24. Web Crypto / Persistent Identity (~line 4830, functions Lr/Kr/Vr)

Generates and persists an ECDSA P-256 key pair in IndexedDB, creating a
stable cross-session device identifier. The public key is sent in the server
payload as a persistent cryptographic fingerprint. Also generates an ECDH
P-256 key pair for encrypting the payload.

| Web API | Usage |
|---|---|
| `crypto.subtle.generateKey()` | ECDSA P-256 (signing) and ECDH P-256 (encryption) key generation |
| `crypto.subtle.exportKey("jwk", publicKey)` | Exports public key as JWK for transmission |
| `crypto.subtle.sign("ECDSA", privateKey, data)` | Signs ciphertext with SHA-256 |
| `crypto.subtle.deriveBits("ECDH", …)` | Derives shared secret from server public key |
| `crypto.subtle.importKey()` | Imports server's ECDH public key |
| `crypto.subtle.encrypt("AES-GCM", …)` | Encrypts payload with derived AES key |
| `crypto.subtle.digest("SHA-256", data)` | Hashes derived bits for AES key material |
| `crypto.getRandomValues()` | Generates IV and salt for AES-GCM |
| `indexedDB.open("signifyd-db")` | Opens persistent database |
| `IDBDatabase.createObjectStore("crypto-keys", {keyPath:"id"})` | Key store with `"id"` key path |
| `IDBObjectStore.get("primary")` | Retrieves existing key pair |
| `IDBObjectStore.put({id, publicKey, privateKey})` | Stores new key pair |

**Output:** `browserCryptoFingerPrint.publicKey` — ECDSA P-256 public key in
JWK format, persisted across sessions via IndexedDB.

---

## 25. Speech Synthesis (~line 1309)

Reads available speech synthesis voices. Single call at initialization.

| Web API | Usage |
|---|---|
| `speechSynthesis.getVoices()` | Returns array of available `SpeechSynthesisVoice` objects |

**Output:** Voice list used for lie detection — checked for API tampering but
voice data itself is not included in the server payload.

---

## 26. Battery / Network (~line 2185 and ~line 2226)

Reads battery status and network connection information.

| Web API | Usage |
|---|---|
| `navigator.getBattery()` | Returns `BatteryManager` promise |
| `BatteryManager.charging` | Charging state (boolean) |
| `BatteryManager.chargingTime` | Time to full charge |
| `BatteryManager.dischargingTime` | Time to empty |
| `BatteryManager.level` | Battery level (0–1) |
| `navigator.connection.downlink` | Effective bandwidth (Mbps) |
| `navigator.connection.effectiveType` | Connection type (`"4g"`, `"3g"`, etc.) |
| `navigator.connection.rtt` | Round-trip time (ms) |
| `navigator.connection.saveData` | Data saver mode (boolean) |
| `navigator.connection.downlinkMax` | Maximum downlink speed |
| `navigator.connection.type` | Physical connection type |
| `navigator.bluetooth.getAvailability()` | Bluetooth availability check (also collected inside workers, see section 19) |

**Output:** `performanceData.{charging, level}` in server payload; network
info collected but not in hashed output.

---

## 27. Storage Quota (~line 2199, function Zx)

Reads storage quota estimate for fingerprinting and incognito detection.

| Web API | Usage |
|---|---|
| `navigator.storage.estimate()` | Returns `{quota, usage}` — quota varies by browser/mode |
| `navigator.webkitTemporaryStorage.queryUsageAndQuota()` | Legacy Chromium equivalent |

**Output:** `performanceData.{quota, quotaIsInsecure, quotaInGigabytes}`.

**Notes:** Incognito Chrome has quota < 2GB. Normal Chrome quota is typically
~10GB. This is both a fingerprinting signal and an incognito indicator.

---

## 28. Lie Detection System (~line 1091, functions Hx/$t/xn)

Extensive API tampering detection inherited from CreepJS. Uses 17+ distinct
techniques to probe browser APIs for signs of spoofing, hooking, or
modification by privacy tools.

**Techniques employed:**

| Technique | Description |
|---|---|
| Illegal error throw | Calls function incorrectly to check error message format |
| Undefined property check | Tests if expected properties are `undefined` |
| Call/apply interface error | Tests `call`/`apply` behavior on native functions |
| New instance error | Tests `new` on non-constructable functions |
| Class extends error | Tests `class X extends target {}` |
| Null conversion error | Tests error from `.call(null)` |
| `toString` validation | Checks `Function.prototype.toString()` returns `[native code]` |
| Prototype-in-function check | Tests `"prototype" in func` |
| Descriptor check | Verifies `Object.getOwnPropertyDescriptor()` matches expected shape |
| Own property check | Tests `hasOwnProperty` on function objects |
| `Object.create` proxy error | Tests for Proxy interception via `Object.create(target)` |
| `Symbol.hasInstance` check | Tests `instanceof` behavior |
| `defineProperty` check | Tests `Object.defineProperty` on target |
| `__proto__` cycle error | Tests for prototype chain manipulation |
| Property descriptor keys | Verifies descriptor key names |
| Own property names | Checks `Object.getOwnPropertyNames` results |
| Reflect operations | Uses `Reflect.get`, `Reflect.apply`, `Reflect.setPrototypeOf` |

**API classes probed for tampering:**

| Target | Methods/Properties Tested |
|---|---|
| `AnalyserNode` | All prototype properties |
| `AudioBuffer` | `copyFromChannel`, `getChannelData` |
| `BiquadFilterNode` | `getFrequencyResponse` |
| `CanvasRenderingContext2D` | `getImageData`, `getLineDash`, `isPointInPath`, `isPointInStroke`, `measureText`, `quadraticCurveTo`, `fillText`, `strokeText`, `font` |
| `CSSStyleDeclaration` / `CSS2Properties` | `setProperty` |
| `CSSStyleSheet` / `CSSRule` | `cssRules`, `insertRule`, `deleteRule`, `style`, `cssText` |
| `Date` | 23 methods (getDate through valueOf) |
| `Document` | `createElement`, `createElementNS`, `getElementById`, `getElementsByClassName`, `getElementsByName`, `getElementsByTagName`, `getElementsByTagNameNS`, `referrer`, `write`, `writeln` |
| `DOMRect` / `DOMRectReadOnly` | All properties |
| `Element` | `append`, `appendChild`, `getBoundingClientRect`, `getClientRects`, `insertAdjacentElement`, `insertAdjacentHTML`, `insertAdjacentText`, `insertBefore`, `prepend`, `replaceChild`, `replaceWith`, `setAttribute` |
| `FontFace` | `family`, `load`, `status` |
| `GPU` / `GPUAdapter` | `requestAdapter`, `requestAdapterInfo` |
| `HTMLCanvasElement` | All prototype properties |
| `HTMLElement` | `clientHeight`, `clientWidth`, `offsetHeight`, `offsetWidth`, `scrollHeight`, `scrollWidth` |
| `HTMLIFrameElement` | `contentDocument`, `contentWindow` |
| `IntersectionObserverEntry` | `boundingClientRect`, `intersectionRect`, `rootBounds` |
| `Intl.DateTimeFormat` | `format`, `formatRange`, `formatToParts`, `resolvedOptions` |
| `Intl.RelativeTimeFormat` | `resolvedOptions` |
| `Math` | `acos`, `acosh`, `asinh`, `atan`, `atan2`, `atanh`, `cbrt`, `cos`, `cosh`, `exp`, `expm1`, `log`, `log10`, `log1p`, `sin`, `sinh`, `sqrt`, `tan`, `tanh` |
| `MediaDevices` | `enumerateDevices`, `getDisplayMedia`, `getUserMedia` |
| `Navigator` | 27 properties (appCodeName through webdriver) |
| `Node` | `appendChild`, `insertBefore`, `replaceChild` |
| `OffscreenCanvas` | `convertToBlob`, `getContext` |
| `OffscreenCanvasRenderingContext2D` | `getImageData`, `getLineDash`, `isPointInPath`, `isPointInStroke`, `measureText`, `quadraticCurveTo`, `font` |
| `Permissions` | `query` |
| `Range` | `getBoundingClientRect`, `getClientRects` |
| `RTCPeerConnection` | All prototype properties (except `peerIdentity`) |
| `Screen` | All prototype properties |
| `speechSynthesis` | `getVoices` |
| `StorageManager` | `estimate` |
| `String` | `fromCodePoint` |
| `SVGRect` / `SVGRectElement` | `getBBox` |
| `SVGTextContentElement` | `getExtentOfChar`, `getSubStringLength`, `getComputedTextLength` |
| `TextMetrics` | All properties |
| `WebGLRenderingContext` | `bufferData`, `getParameter`, `readPixels` |
| `WebGL2RenderingContext` | `bufferData`, `getParameter`, `readPixels` |
| `Plugin` / `PluginArray` / `MimeTypeArray` | All properties |
| `ServiceWorker` / `SharedWorker` / `Worker` | All properties |
| `History` | All properties |

**Output:** `anomalies.data{<class>.<method>: [error strings]}`,
`anomalies.totalLies` (integer).

---

## 29. Phantom Iframe (~line 1395, function Xt)

Creates a hidden iframe inside a closed Shadow DOM to provide a clean
execution context for fingerprinting, isolated from page-level modifications.

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates shadow host |
| `Element.attachShadow({mode:"closed"})` | Creates closed Shadow DOM |
| `document.createElement("iframe")` | Creates hidden iframe: 100% width/height, no border |
| `HTMLIFrameElement.contentWindow` | Accesses iframe's clean `window` object |
| `Object.assign(element.style, …)` | Host styling: `position:fixed, width:0, height:0, opacity:0, pointerEvents:none, zIndex:-1` |
| `document.documentElement.appendChild()` | Appends shadow host to document |

---

## 30. Data Exfiltration (~line 650, function Ux)

Encrypts the fingerprint payload with ECDH/AES-GCM, signs it with ECDSA, and
transmits via `fetch()` POST.

| Web API | Usage |
|---|---|
| `new FormData()` | Builds multipart form payload |
| `FormData.append()` | Appends encrypted Blob fields: `ciphertext`, `iv`, `salt`, `publicEncryptionKey`, `cipherTextSignature` |
| `new Blob()` | Wraps binary data for FormData |
| `fetch()` | POST to `https://dp.signifyd.com/fp-web` with header `data-order-session-id` |

---

## 31. Miscellaneous / Utility

| Web API | Usage |
|---|---|
| `location.href` / `location.origin` | Navigation URL for `navigation` payload section |
| `location.search` | Read URL search params |
| `document.currentScript.src` | Extract params from script URL |
| `URLSearchParams` | Parse URL parameters |
| `new URL()` | Parse URL for origin |
| `localStorage.getItem("dev-jw")` | Read dev override for server URL |
| `setTimeout()` | Async delay helper, worker timeouts (5s) |
| `Promise.all()` / `Promise.allSettled()` | Parallel async operations |
| `JSON.stringify()` / `JSON.parse()` | Data serialization |
| `TextEncoder.encode()` | String to Uint8Array for crypto operations |
| `atob()` / `btoa()` | Base64 encode/decode |
| `String.fromCharCode()` | Character conversion |
| `String.fromCodePoint()` | Emoji generation from codepoints |
| `Object.freeze()` | Freezes privacy signal validation object |
| `Object.defineProperty()` | Property definitions |
| `Object.getPrototypeOf()` | Prototype chain walking (CSS property enumeration, lie detection) |
| `Object.getOwnPropertyDescriptor()` / `getOwnPropertyDescriptors()` | Descriptor inspection (lie detection) |
| `Object.getOwnPropertyNames()` | Property enumeration (lie detection, CSS, window features) |
| `Reflect.getOwnPropertyDescriptor()` | Reflect-based descriptor checks (lie detection) |
| `Reflect.ownKeys()` | Reflect-based key enumeration (lie detection) |
| `Reflect.setPrototypeOf()` | Prototype manipulation (lie detection) |
| `Reflect.get()` / `Reflect.apply()` | Property/function access (anomaly detection) |
| `document.createElement("template")` | Template element for safe HTML injection |
| `HTMLTemplateElement.content` | Access template DocumentFragment |
| `document.importNode()` | Import template content into document |
| `self === top` | Cross-origin iframe detection |
| `parent.Function` | Sandbox detection |

---

## Summary

| # | Category | Unique Web APIs | Origin |
|---|----------|----------------|--------|
| 1 | Canvas 2D fingerprinting | 32 | CreepJS (identical) |
| 2 | TextMetrics fingerprinting | 8 | CreepJS (identical) |
| 3 | WebGL fingerprinting | 6 | CreepJS (similar, ~60%) |
| 4 | WebGPU fingerprinting | 22 | Signifyd addition |
| 5 | Audio fingerprinting (OfflineAudioContext) | 46 | CreepJS (identical) |
| 6 | AudioWorklet fingerprinting | 9 | Signifyd addition |
| 7 | SVG fingerprinting | 10 | CreepJS (identical) |
| 8 | DOMRect / ClientRects fingerprinting | 11 | CreepJS (identical) |
| 9 | CSS computed styles | 5 | CreepJS (identical) |
| 10 | CSS media queries | 7 | CreepJS (identical) |
| 11 | Screen properties | 13 | CreepJS (similar, ~60%) |
| 12 | Navigator properties | 24 | CreepJS (similar, ~70%) |
| 13 | Plugins / MIME types | 7 | CreepJS (similar) |
| 14 | Intl API | 9 | CreepJS (similar, ~80%) |
| 15 | Timezone | 5 | CreepJS (identical) |
| 16 | Performance / timing | 6 | Signifyd addition |
| 17 | WebRTC IP detection | 6 | Signifyd addition |
| 18 | Permissions probing | 2 | Signifyd addition (querying 39 names) |
| 19 | Worker context fingerprinting | 38 | Signifyd original |
| 20 | Incognito detection | 17 | External library (detectIncognito v1.4.1) |
| 21 | Cookie monster | 1 | Signifyd original |
| 22 | In-app WebView detection | 6 | Signifyd original |
| 23 | Window features enumeration | 1 | CreepJS (similar) |
| 24 | Web crypto / persistent identity | 12 | Signifyd original |
| 25 | Speech synthesis | 1 | CreepJS |
| 26 | Battery / network / bluetooth | 12 | Signifyd addition |
| 27 | Storage quota | 2 | Signifyd addition |
| 28 | Lie detection system | ~60+ API classes | CreepJS (identical) |
| 29 | Phantom iframe | 6 | CreepJS (identical) |
| 30 | Data exfiltration | 4 | Signifyd original |
| 31 | Miscellaneous / utility | 27 | Mixed |
| | **Total** | **~400** | |

---

## Notable Observations

1. **CreepJS lineage is forensically traceable.** The fork point is precisely
   identified as CreepJS commit `c17490f` (May 20, 2023). Features added after
   that date (e.g., `console.table` timing detection from July 2023, macOS 13
   Ventura font support from November 2023) are absent from Signifyd's code.
   Features added on or before May 20, 2023 (GPU lie detection, `"any-pointer"`
   fix) are present.

2. **Triple-context collection is unique to Signifyd.** No other fingerprinter
   in this repository independently collects full navigator profiles across
   main thread, Web Worker, and SharedWorker contexts to detect spoofing
   inconsistencies. This directly targets privacy extensions that modify
   `navigator` properties only in the main window context.

3. **The lie detection system is the most extensive in the dataset.** Testing
   35+ API classes with 17+ distinct tampering detection techniques, it
   generates 124 `RTCPeerConnection.constructor` samples and hundreds of
   other probes — not for fingerprinting, but for detecting fingerprint
   resistance tools.

4. **TextMetrics as a canvas randomization bypass.** The profile-gap-analysis
   documents that while `CanvasRandomization` (RFP target 9) adds noise to
   extracted canvas pixel data, **no noise is added to `measureText()` return
   values**. There is no TextMetrics RFP target in `RFPTargets.inc`. A
   fingerprinter could theoretically bypass canvas randomization by reading
   TextMetrics numeric values directly. The script actively detects such
   protections by checking for fractional parts (`% 1 !== 0`) in bounding
   box values.

5. **WebGPU adapter limits provide a new GPU fingerprint.** The 14 adapter
   limit values plus feature set create a GPU fingerprint that is independent
   of WebGL. As WebGL becomes more restricted by browsers, WebGPU limits may
   become the primary GPU identification vector.

6. **Signifyd removed CreepJS's headless/bot detection modules** but retained
   the core lie detection system. This suggests the lie detection is used
   primarily for fingerprint reliability assessment (flagging `lied: true`
   on individual categories) rather than for bot detection.

7. **Five separate canvas renders** (data, paint, paintCpu, text, emoji)
   provide redundancy. The `paintCpu` variant uses shadow effects to force
   CPU rendering, creating a fingerprint independent of GPU acceleration.
   This means that even if the browser normalizes GPU rendering, the CPU
   rendering path may still produce identifiable differences.

8. **The 48-font CSS_FONT_FAMILY list is frozen at the May 2023 fork point.**
   It includes fonts like `'Segoe Fluent Icons'`, `'Ink Free'`,
   `'Bahnschrift'`, `'Galvji'`, `'Bai Jamjuree'` — but lacks fonts added
   in macOS 14 Sonoma or Windows 11 23H2 updates.

9. **Persistent cryptographic identity via IndexedDB.** The ECDSA P-256 key
   pair stored in `signifyd-db` survives cookie clears and creates a
   cross-session device identifier that persists until the user clears site
   data or IndexedDB. This is independent of the browser fingerprint and
   provides exact device re-identification even if the fingerprint changes.

10. **91 emoji codepoints** are used for both DOMRect and SVG rendering
    fingerprinting. These include complex ZWJ (Zero Width Joiner) sequences
    that render differently across OS versions and emoji font implementations,
    providing an emoji rendering fingerprint that correlates with OS version.

11. **The incognito detection module is a direct copy** of `detectIncognito
    v1.4.1` by Joe12387 (MIT license, properly attributed). It uses 7
    browser-specific detection strategies covering Chrome, Firefox, Safari,
    Brave, Edge, Opera, and IE — testing 17 distinct APIs.

12. **In-app WebView detection includes TikTok and Snapchat** patterns that
    are not found in standard public detection libraries (e.g., f2etw/detect-
    inapp). This is original Signifyd code targeting modern social media
    in-app browsers.

13. **The server payload hashes 13 categories** but marks 3 as `use: false`
    (cookieMonster, screen, webrtc), meaning those hashes exist but do not
    contribute to the composite `browserFingerPrint` identifier. The 10
    active hash categories are: intl, gpu, offlineAudioContext, canvas2d,
    clientRects, css, cssMedia, svg, timezone, windowFeatures, and
    workletAudioData.
