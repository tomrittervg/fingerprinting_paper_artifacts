# Akamai Bot Manager — Complete Web API Inventory

Comprehensive list of every Web API that Akamai Bot Manager's fingerprinting
script accesses, derived from deobfuscated scripts (`americanexpress.deob2.js`,
`prada.deob2.js`, `xfinity.deob2.js`) and the collected data in `data.json`.

Scripts downloaded 2026-02-06 from `/akam/13/` endpoints on americanexpress.com,
prada.com, and xfinity.com. All three share identical logic; only site-specific
hex tokens differ.

---

## 1. Canvas 2D Fingerprinting (function D — "cv")

Renders specific text and rectangles on an off-screen canvas, then hashes the
resulting pixel data. This is the **highest-entropy** signal Akamai collects.

| Web API | Usage |
|---|---|
| `document.createElement("canvas")` | Creates off-screen canvas (default 300x150) |
| `HTMLCanvasElement.getContext("2d")` | Gets 2D rendering context |
| `CanvasRenderingContext2D.fillStyle` | Set 4 times: `"rgba(255,153,153,0.5)"`, `"#0000FF"`, `"#E0E0E0"`, `"#FF3333"` |
| `CanvasRenderingContext2D.font` | Set to `"18pt Tahoma"` |
| `CanvasRenderingContext2D.textBaseline` | Set to `"top"` |
| `CanvasRenderingContext2D.fillText()` | Two calls: `"Soft Ruddy Foothold 2"` at (2,2) and `"!H71JCaj)]# 1@#"` at (4,8) |
| `CanvasRenderingContext2D.fillRect()` | Three overlapping rectangles at (100,25) with sizes 30x10, 20x30, 10x15 |
| `HTMLCanvasElement.toDataURL()` | Exports canvas to PNG data URI |

**Output:** SHA-1 hash of the `toDataURL()` result (e.g. `658d2b5e3aafb5d1a0291cc0444b43ea21d39a7e`).

**Notes:** The specific text strings ("Soft Ruddy Foothold 2", "!H71JCaj)]#
1@#") and overlapping colored rectangles are chosen to maximize rendering
differences across GPU/driver/font-renderer combinations. The font `Tahoma` is
used because it renders differently on every major OS. The function also calls
`document.createElement("img").src = dataURL` but this image is never appended
to the DOM — likely dead code or a side-effect for older browser compatibility.

---

## 2. APNG Support Detection (function A — "ap")

Determines whether the browser supports Animated PNG by loading a multi-frame
APNG image and checking if the second frame rendered.

| Web API | Usage |
|---|---|
| `new Image()` | Creates image element |
| `Image.onload` | Waits for APNG to render |
| `Image.src` | Set to a base64-encoded 1x1 APNG data URI |
| `document.createElement("canvas")` | Creates canvas for pixel inspection |
| `HTMLCanvasElement.getContext("2d")` | Gets 2D context |
| `CanvasRenderingContext2D.drawImage()` | Draws the loaded APNG onto canvas |
| `CanvasRenderingContext2D.getImageData()` | Reads pixel (0,0) — checks `data[3]` (alpha channel) |

**Output:** Boolean — `true` if alpha channel is 0 (APNG supported, second frame
replaced first), `false` otherwise.

**Notes:** Low entropy in modern browsers (all support APNG). Historically useful
for distinguishing older browser engines.

---

## 3. Navigator Properties (function O — "nav")

Reads 24 `navigator` properties and enumerates installed plugins by name.

| Web API | Fingerprinting Use |
|---|---|
| `navigator.userAgent` | Full UA string — **high entropy** (includes OS, browser, version) |
| `navigator.appName` | Legacy app name (always "Netscape") |
| `navigator.appCodeName` | Legacy code name (always "Mozilla") |
| `navigator.appVersion` | Subset of UA (e.g. "5.0 (Macintosh)") |
| `navigator.appMinorVersion` | IE-only; 0 elsewhere |
| `navigator.product` | Always "Gecko" |
| `navigator.productSub` | Firefox: "20100101"; Chrome: "20030107" |
| `navigator.vendor` | Chrome: "Google Inc."; Firefox: "" |
| `navigator.vendorSub` | Always "" |
| `navigator.buildID` | Firefox-specific build timestamp (e.g. "20181001000000") |
| `navigator.platform` | OS identification — **medium entropy** (e.g. "MacIntel", "Win32", "Linux x86_64") |
| `navigator.oscpu` | Firefox-only OS+arch string — **medium entropy** (e.g. "Intel Mac OS X 10.15") |
| `navigator.hardwareConcurrency` | CPU logical core count — **medium entropy** |
| `navigator.language` | Primary language — **medium entropy** (e.g. "en-US") |
| `navigator.languages` | Ordered language preference array — **medium entropy** |
| `navigator.systemLanguage` | IE-only; 0 elsewhere |
| `navigator.userLanguage` | IE-only; 0 elsewhere |
| `navigator.doNotTrack` | DNT preference — **low-medium entropy** ("1", "0", or "unspecified") |
| `navigator.msDoNotTrack` | IE-specific DNT; 0 elsewhere |
| `navigator.cookieEnabled` | Cookie support boolean |
| `navigator.geolocation` | Checks presence (truthy/falsy), does NOT call `.getCurrentPosition()` |
| `navigator.vibrate` | Checks presence of vibrate API (truthy/falsy) |
| `navigator.maxTouchPoints` | Touch capability — **low-medium entropy** (0 on desktop, 1-10 on touch) |
| `navigator.webdriver` | Automation detection flag (true when driven by WebDriver) |
| `navigator.plugins` | Enumerates all plugin names into an array |

**Notes:** The `plugins` array has high entropy on legacy browsers but modern
browsers expose only a fixed set of 5 PDF-viewer entries. `webdriver` is not
used for fingerprinting but for bot detection.

---

## 4. Plugin Hash Fingerprinting (function R — "bp")

Deeply enumerates every plugin and its MIME types, then hashes each combination.

| Web API | Usage |
|---|---|
| `navigator.plugins` | Iterates the full PluginArray |
| `Plugin.name` | Plugin name string |
| `Plugin.description` | Plugin description |
| `Plugin.filename` | Plugin filename |
| `Plugin[i].description` | Per-MIME-type description |
| `Plugin[i].type` | MIME type string |
| `Plugin[i].suffixes` | File suffix list |

**Output:** Comma-separated list of hash integers, one per plugin+MIME-type
combination.

**Notes:** High entropy historically; near-zero entropy in modern browsers where
`navigator.plugins` is standardized to 5 fixed PDF viewer entries.

---

## 5. Screen & Window Dimensions (function B — "sr")

Reads 16 individual values from `window`, `screen`, and `document.body`,
organized into 9 keys (7 coordinate pairs + 2 scalar depth values).

| Web API | Fingerprinting Use |
|---|---|
| `window.innerWidth` | Viewport width — **low entropy** (depends on window size) |
| `window.innerHeight` | Viewport height |
| `window.outerWidth` | Window chrome width — **medium entropy** (reveals OS UI/toolbar sizes) |
| `window.outerHeight` | Window chrome height |
| `window.screenX` | Window X position on screen (ephemeral) |
| `window.screenY` | Window Y position on screen (ephemeral) |
| `window.pageXOffset` | Scroll position X (ephemeral) |
| `window.pageYOffset` | Scroll position Y (ephemeral) |
| `screen.availWidth` | Available screen width — **medium entropy** (excludes OS taskbar) |
| `screen.availHeight` | Available screen height |
| `screen.width` | Total screen width — **medium entropy** |
| `screen.height` | Total screen height |
| `document.body.clientWidth` | Body content width (page-dependent) |
| `document.body.clientHeight` | Body content height (page-dependent) |
| `screen.colorDepth` | Bits per pixel — **medium entropy** (typically 24 or 30) |
| `screen.pixelDepth` | Same as colorDepth on most systems |

**Notes:** `screenX`/`screenY`, `pageXOffset`/`pageYOffset`, and
`body.client*` are ephemeral and not useful for fingerprinting. The stable
fingerprinting signals are screen resolution, available screen area, color/pixel
depth, and outer window dimensions.

---

## 6. DOM Feature Detection (function m — "dp")

Probes for the existence of 26 APIs/properties on `window` (18), `document` (5),
`document.all` (1), `window.performance` (1), and `document.documentElement` (1).
Produces a feature vector that identifies the browser engine and version.

| Web API Probed | What It Identifies |
|---|---|
| `window.XDomainRequest` | IE 8-9 (CORS via XDR) |
| `window.createPopup` | IE 5.5-10 |
| `window.removeEventListener` | All modern browsers |
| `window.globalStorage` | Firefox 2-13 |
| `window.openDatabase` | WebSQL (Chrome, Safari; never Firefox) |
| `window.indexedDB` | IndexedDB support |
| `window.attachEvent` | IE event model |
| `window.ActiveXObject` | IE ActiveX |
| `window.dispatchEvent` | Standard DOM events |
| `window.addBehavior` | IE DHTML behaviors |
| `window.addEventListener` | Standard event listener |
| `window.detachEvent` | IE event model |
| `window.fireEvent` | IE event model |
| `window.MutationObserver` | Mutation observer support |
| `window.HTMLMenuItemElement` | Firefox-only context menu API (removed in Firefox 85) |
| `window.Int8Array` | Typed arrays (all modern browsers) |
| `window.postMessage` | Cross-origin messaging |
| `window.querySelector` | CSS selector support |
| `document.getElementsByClassName` | Class-based element selection |
| `document.querySelector` | CSS selector support |
| `document.images` | HTMLCollection of images |
| `document.compatMode` | Quirks vs standards mode (returns "CSS1Compat" or "BackCompat") |
| `document.documentMode` | IE document mode (0 elsewhere) |
| `document.all` | IE compat (exists in all browsers but is falsy in non-IE) |
| `window.performance.now` | High-resolution timing support |
| `document.documentElement.contextMenu` | Context menu element (Firefox only) |

**Output:** JSON object mapping each property name to 0 (absent) or 1 (present),
with `compatMode` as a string.

**Notes:** This is a browser-engine fingerprint, not a user fingerprint. Within
a single browser (e.g. Firefox), the vector is nearly identical for all users.
Primary use is to detect browser spoofing.

---

## 7. Date & Timezone (function F — "lt")

| Web API | Usage |
|---|---|
| `new Date()` | Gets current time |
| `Date.prototype.valueOf()` | Millisecond timestamp |
| `Date.prototype.getTimezoneOffset()` | UTC offset in minutes |

**Output:** String `"[timestamp][offset_hours]"` (e.g. `"1770398686598-5"` for
EST/UTC-5).

**Notes:** The timestamp is ephemeral; the timezone offset is the fingerprinting
signal (partial entropy — there are only ~40 distinct offsets worldwide).

---

## 8. Persistent Storage Detection (function N/k — "ps")

| Web API | Usage |
|---|---|
| `window.localStorage.setItem()` | Tests write capability |
| `window.localStorage.removeItem()` | Cleans up test |
| `window.sessionStorage.setItem()` | Tests write capability |
| `window.sessionStorage.removeItem()` | Cleans up test |

**Output:** `"true,true"` (localStorage available, sessionStorage available).

**Notes:** Low entropy. Can detect private browsing mode in some older browsers
where localStorage throws. Test key: `"__akfp_storage_test__"`.

---

## 9. Battery Status (function j — "bt")

| Web API | Usage |
|---|---|
| `navigator.getBattery()` | Returns BatteryManager promise |
| `BatteryManager.charging` | Boolean |
| `BatteryManager.chargingTime` | Seconds to full charge |
| `BatteryManager.dischargingTime` | Seconds to empty |
| `BatteryManager.level` | Battery level 0.0–1.0 |

**Output:** JSON of all BatteryManager properties, or `0` if API unavailable.

**Notes:** This API is **blocked** in Firefox (removed in Firefox 52) and
restricted to secure contexts in Chrome. Returns `0` in the test data. When
available, the precise battery level was a high-entropy fingerprint.

---

## 10. Permissions API Probing (function M — "nap")

Queries the state of 20 permission names without triggering any prompts.

| Web API | Usage |
|---|---|
| `navigator.permissions` | Checks API availability |
| `navigator.permissions.query({name: ...})` | Queries each permission |
| `PermissionStatus.state` | Reads "granted", "denied", or "prompt" |

**Permissions queried (in order):**
1. `geolocation`
2. `notifications`
3. `push`
4. `midi`
5. `camera`
6. `microphone`
7. `speaker`
8. `device-info`
9. `background-sync`
10. `bluetooth`
11. `persistent-storage`
12. `ambient-light-sensor`
13. `accelerometer`
14. `gyroscope`
15. `magnetometer`
16. `clipboard`
17. `accessibility-events`
18. `clipboard-read`
19. `clipboard-write`
20. `payment-handler`

**Output:** 20-digit string encoding each permission's state:
- `0` = denied
- `1` = prompt
- `2` = granted
- `3` = error (permission exists but threw)
- `4` = "not a valid enum value" (permission name not recognized)
- `5` = unknown state
- `6` = Permissions API not available
- `7` = exception during query

Example: `"11111133331333333000"` — first 5 are "prompt", next 4 are "error",
etc.

**Notes:** The combination of granted/denied/prompt states across 20 permissions
can be fingerprinting-relevant if the user has granted specific permissions on a
site. Many of these permission names are Chrome-only and return error code `4` in
Firefox. The script does NOT trigger any permission prompts — it only reads
existing states.

---

## 11. Browser Name Detection (function C — "br")

Feature-detection-based browser identification. Does not parse the UA string.

| Web API / Object | Browser Detected |
|---|---|
| `window.opera` | Opera (Presto) |
| `navigator.userAgent` (contains "OPR/") | Opera (Blink) |
| `InstallTrigger` (typeof check) | Firefox |
| `Object.prototype.toString.call(window.HTMLElement)` (contains "Constructor") | Safari (old) |
| `window.safari.pushNotification` | Safari |
| `window.ApplePaySession` | Safari |
| `navigator.userAgent` (contains "CriOS") | Chrome on iOS |
| `window.chrome` | Chrome |
| `window.ActiveXObject` / `document.documentMode` | Internet Explorer |
| `window.StyleMedia` | Edge (Legacy) |

**Output:** String — the detected browser name (e.g. `"Firefox"`).

**Notes:** Low entropy within a known-browser population. Primary use is
detecting UA spoofing (mismatches between UA string and feature detection).

---

## 12. Bot/Automation Detection (function w — "z")

Multi-layered detection of automation tools and headless browsers.

| Web API | Detection Purpose |
|---|---|
| Iterate all properties of `window` and `document` | Looks for known automation-injected properties |
| SHA-1 hash of property names | Matches against 32 known bot-property hashes (Selenium, Puppeteer, PhantomJS, etc.) |
| `document.documentElement.getAttribute("selenium")` | Selenium IDE markers |
| `document.documentElement.getAttribute("driver")` | WebDriver markers |
| `document.documentElement.getAttribute("webdriver")` | WebDriver markers |
| `window.external` | Checks existence of external interface |
| `window.external.toString()` | Checks for "Sequentum" (web scraping tool) |
| `window.XPathResult` / `document.XPathResult` | XPath result type — present in real browsers |
| `window.chrome` | Chrome object presence |
| `window.chrome.runtime` | Chrome runtime — absent in headless Chrome |

**Output:** Two separate payload fields:
- `z`: JSON `{a: [flags XOR site_key], b: [has_xpath], c: [chrome_without_runtime]}`
- `zh`: Comma-separated string of matched bot-property indices (0-31)

**Notes:** The 32 SHA-1 hashes correspond to property names injected by known
automation frameworks. The XOR with the site-specific key (`bazadebezolkohpepadr`)
ensures the bot-detection result is bound to the site configuration. Properties
matching are filtered to those starting with `$`, `_`, `B`, `c`, `d`, `e`, `s`,
or `w`.

---

## 13. Chrome Runtime Check (function T — "crc")

| Web API | Usage |
|---|---|
| `window.chrome` | Checks existence |

**Output:** JSON `{"window.chrome": <value or "-not-existent">}`.

**Notes:** `window.chrome` never exists in Firefox, so this is zero-entropy
within the Firefox population. Its purpose is to detect browser spoofing
(e.g. a headless Chrome pretending to be Firefox).

---

## 14. Flash Version Detection (function x — "fp")

| Web API | Usage |
|---|---|
| `navigator.plugins["Shockwave Flash"]` | Direct plugin lookup |
| `Plugin.description` | Version string extraction |
| `navigator.plugins["Shockwave Flash 2.0"]` | Legacy Flash check |
| `navigator.mimeTypes` | Accesses MimeTypeArray (fallback when plugins empty) |
| `MimeTypeArray["application/x-shockwave-flash"]` | MIME type lookup |
| `MimeType.enabledPlugin.description` | Version via MIME type |
| `new ActiveXObject("ShockwaveFlash.ShockwaveFlash[.7\|.6\|base]")` | IE ActiveX fallback — tries version 7, then 6, then unversioned |

**Output:** Version string (e.g. "32.0.0") or `false`.

**Notes:** Dead technology. Flash was removed from all browsers by end of 2020.
Always returns `false` in modern browsers. The ActiveX fallback path tries three
class strings in sequence: `.ShockwaveFlash.7`, `.ShockwaveFlash.6`, then
`.ShockwaveFlash` (no version suffix).

---

## 15. Silverlight Version Detection (function E — "sp")

| Web API | Usage |
|---|---|
| `navigator.plugins["Silverlight Plug-In"]` | Plugin lookup |
| `Plugin.description` | Version string extraction |
| `new ActiveXObject("AgControl.AgControl")` | IE ActiveX fallback |
| `AgControl.IsVersionSupported()` | Version check |

**Output:** Comma-separated version list (e.g. "1.0,2.0,3.0,4.0,5.0") or `false`.

**Notes:** Dead technology. Silverlight was end-of-life October 2021. Always
returns `false` in modern browsers.

---

## 16. IE userData Storage (function S — "ieps")

| Web API | Usage |
|---|---|
| `document.createElement("div")` | Creates test element |
| `HTMLElement.style.behavior` | Sets to `"url(#default#userData)"` (IE behavior) |
| `document.body.appendChild()` | Inserts into DOM |
| `Element.setAttribute()` | Sets test attribute `"fsfp"` |
| `Element.save()` | IE userData: persist to store `"oXMLStore"` |
| `Element.removeAttribute()` | Removes the test attribute |
| `Element.load()` | IE userData: load from store `"oXMLStore"` |
| `Element.getAttribute()` | Re-reads attribute to verify persistence |
| `document.body.removeChild()` | Cleans up DOM |

**Output:** Boolean — `true` if IE userData round-trips, `false` otherwise.

**Notes:** IE-only technology, irrelevant in modern browsers. Always `false`.

---

## 17. PDF Viewer Detection (function y — "av")

| Web API | Usage |
|---|---|
| `window.ActiveXObject` | Checks for IE |
| `new ActiveXObject("PDF.PdfCtrl.[2-9]")` | Probes Adobe PDF ActiveX versions 2–9 in a loop |
| `new ActiveXObject("PDF.PdfCtrl.1")` | Probes version 1 separately (returns "4" if found) |
| `new ActiveXObject("AcroPDF.PDF.1")` | Alternative Adobe PDF control (returns "7" if found) |

**Output:** PDF version number or `false`.

**Notes:** IE/ActiveX-only. Always `false` in modern browsers. Version 1 is probed
separately after the 2–9 loop, and oddly reports as version "4" rather than "1".

---

## 18. JavaScript Version Detection (function P — "jsv")

| Web API | Usage |
|---|---|
| `document.getElementsByTagName("head")` | Gets head element |
| `document.createElement("script")` | Creates test script elements |
| `HTMLScriptElement.setAttribute("language", "JavaScript1.X")` | Tests JS version support |
| `document.currentScript` | Gets reference to running script |
| `HTMLScriptElement.nonce` | CSP nonce propagation |
| `HTMLScriptElement.text` | Sets script body (e.g. `urhehlevkedkilrobacf="1.5"`) |
| `Node.appendChild()` / `Node.removeChild()` | DOM manipulation to execute/clean up test scripts |

**Output:** Highest supported JavaScript version string (e.g. "1.5").

**Notes:** The `language` attribute on `<script>` is deprecated. Modern browsers
all report "1.5" or similar. Low entropy; identifies browser engine era.

---

## 19. Performance Timing (not a named function — infrastructure)

| Web API | Usage |
|---|---|
| `window.performance` | Checks availability |
| `window.performance.timing` | Legacy PerformanceTiming interface |
| `window.performance.timing.responseStart` | Page load timing |
| `new Date().valueOf()` | Millisecond timestamps for profiling |

**Output:** JSON with retry timings, per-function execution times, and page load
metrics.

**Notes:** All timing data is ephemeral — it varies every page load and is not
useful for fingerprinting. Used for performance monitoring and to detect
artificial delays (bot behavior).

---

## 20. Data Exfiltration (function o — send)

| Web API | Usage |
|---|---|
| `new XMLHttpRequest()` | Creates HTTP request |
| `XMLHttpRequest.open("POST", ...)` | POST to `/akam/13/pixel_[hex]` |
| `XMLHttpRequest.setRequestHeader()` | Sets `Content-Type: application/x-www-form-urlencoded` |
| `XMLHttpRequest.send()` | Transmits fingerprint payload |
| `new ActiveXObject("Microsoft.XMLHTTP")` | IE fallback |
| `window.location.origin` | Constructs absolute URL |
| `window.location.protocol` | URL construction fallback |
| `window.location.hostname` | URL construction fallback |
| `window.location.port` | URL construction fallback |
| `window.encodeURIComponent()` | URL-encodes payload fields |

---

## 21. Event Handling & Script Bootstrap

| Web API | Usage |
|---|---|
| `document.body` | Checks if DOM is ready |
| `document.addEventListener("DOMContentLoaded", ...)` | Runs fingerprinting when DOM ready |
| `document.addEventListener("load", ...)` | Fallback for late load |
| `document.attachEvent("DOMContentLoaded", ...)` | IE fallback |
| `document.attachEvent("onload", ...)` | IE fallback |
| `window.setTimeout()` | Retry loop (100ms intervals) for bot detection re-checks |

---

## Summary: API Counts by Category

| Category | APIs Used | Fingerprinting Entropy |
|---|---|---|
| **Canvas 2D** | 8 | High |
| **Navigator properties** | 25 | High (userAgent, plugins) to Low (vendor, product) |
| **Plugin enumeration** | 7 | High (legacy), Near-zero (modern) |
| **Screen / Window** | 16 | Medium |
| **DOM feature detection** | 26 | Low (browser-engine ID) |
| **Permissions API** | 3 (querying 20 names) | Low-Medium |
| **Date / Timezone** | 3 | Partial (offset only) |
| **Storage detection** | 4 | Low |
| **Battery API** | 5 | Blocked in Firefox |
| **Bot detection** | 10 | N/A (security, not fingerprinting) |
| **Browser detection** | 10 | Low |
| **Chrome runtime** | 1 | Zero (in Firefox) |
| **APNG detection** | 7 | Low (universal support) |
| **Flash detection** | 7 | Dead |
| **Silverlight detection** | 4 | Dead |
| **IE userData** | 9 | Dead |
| **PDF viewer (ActiveX)** | 4 | Dead |
| **JS version** | 7 | Low |
| **Performance timing** | 4 | Ephemeral |
| **Network (XHR)** | 10 | N/A (data exfiltration) |
| **Event/bootstrap** | 6 | N/A (lifecycle) |

**Payload fields: 24** (22 actively populated + 2 dead: `fonts`, `fh`)
**Collection functions: 18** (16 synchronous in `compute()` + 2 async: APNG, Battery)
Note: function `w` (bot detection) produces two separate payload fields: `z` (flags) and `zh` (property indices).
**High-entropy fingerprinting signals: 3** (canvas hash, user agent, plugin hashes)
**Medium-entropy fingerprinting signals: 10** (screen dimensions, hardware concurrency, language, platform, oscpu, etc.)
**Dead/irrelevant fields: 8** (Flash, Silverlight, IE userData, PDF ActiveX, fonts, font_hash, battery, APNG)

---

## Notable Observations

1. **No WebGL fingerprinting.** Unlike FingerprintJS Pro and Signifyd, Akamai
   does not use WebGL renderer/vendor strings or parameter queries.

2. **No Audio fingerprinting.** No OfflineAudioContext or Web Audio API usage.

3. **No font collection code at all.** The payload schema declares `fonts` and
   `fh` (font hash) fields, and they are initialized to `null` in the data
   object, but **no function in the script ever writes to them**. There is no
   font enumeration code — not via CSS, not via JavaScript, not via plugins.
   These are dead schema fields, likely remnants from a version that used a
   Flash or Java applet for font detection.

4. **No WebRTC.** No RTCPeerConnection, no SDP fingerprinting, no IP detection.

5. **No CSS media queries.** No `matchMedia()` calls for display features.

6. **Heavy legacy code.** Approximately 40% of the script's API surface (Flash,
   Silverlight, ActiveX, IE userData, `attachEvent`) targets browsers that no
   longer exist. This suggests the script codebase has been maintained
   incrementally since ~2012 without removing dead code paths.

7. **Bot detection is the primary goal.** The property-hash-based detection
   system (32 known bot signatures), the multi-retry XOR-key mechanism, and the
   Selenium/WebDriver attribute checks suggest Akamai prioritizes bot detection
   over user fingerprinting.

8. **Relatively modest fingerprint surface.** Compared to FingerprintJS Pro
   (~117 signals across 29 API categories) or Signifyd/CreepJS (~50+ signals
   with ClientRects, SVG, audio, WebRTC, CSS), Akamai's fingerprint is
   deliberately lightweight — canvas + navigator + screen + plugins.

9. **Additional dead code.** The global `window.btoa` polyfill is defined but
   never called by any fingerprinting function (the variable `f` that holds it
   is always shadowed by local variables). A `window.JSON` polyfill is also
   defined but only used for internal serialization, not fingerprinting.

10. **All three scripts are identical.** Diffing `americanexpress.deob2.js`,
    `prada.deob2.js`, and `xfinity.deob2.js` confirms byte-for-byte identical
    logic. The only differences are three 32-character hex tokens on the last
    line (`g`, `p`, `O` — site identifiers) and the XOR constant in the send
    function (`"515"`, `"568"`, `"903"`).
