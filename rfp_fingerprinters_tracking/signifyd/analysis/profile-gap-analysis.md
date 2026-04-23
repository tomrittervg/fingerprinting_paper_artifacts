# Signifyd lite.js — Profile-Based Gap Analysis

Comparison of APIs observed in the Firefox Profiler trace (`lite.json.gz`)
against those documented in prior static/data analyses. The goal is to identify
fingerprinting surfaces that the profile reveals but that were not previously
known or documented.

**Profile stats:** 29MB trace, 493 unique page-originated Web APIs across 25
categories.

**Prior analyses consulted:**
- `creepjs-signifyd-full-comparison.md` — Module-by-module comparison with CreepJS
- `creepjs-signifyd-clientrects-comparison.md` — ClientRects deep-dive
- `fork-point-analysis.md` — Fork point and modifications
- `lite-unique-sources.md` — Features unique to Signifyd
- `lite-without-creep/README.md` — Non-CreepJS feature catalog
- `data.json` — Intercepted fingerprint payload

---

## Previously Known Fingerprinting Surfaces

The following surfaces were already documented in prior analyses and are
confirmed by the profile:

| Surface | Prior Analysis | Profile Confirmation |
|---------|---------------|---------------------|
| Canvas 2D fingerprinting | full-comparison: IDENTICAL to CreepJS | 36 Canvas 2D APIs, heavy `getImageData` (780 samples) |
| WebGL vendor/renderer | full-comparison: SIMILAR | `getExtension` + `getParameter` (2+4 samples) |
| OfflineAudioContext | full-comparison: IDENTICAL to CreepJS | 52 Web Audio APIs including oscillator/compressor/analyser |
| ClientRects/DOMRect | clientrects-comparison: IDENTICAL | `getBoundingClientRect`, `getClientRects` |
| SVG rendering | full-comparison: IDENTICAL to CreepJS | 9 SVG APIs (`getBBox`, `getComputedTextLength`, etc.) |
| CSS computed styles | full-comparison: IDENTICAL to CreepJS | 62 CSS/Style APIs |
| CSS media queries | full-comparison: IDENTICAL to CreepJS | `matchMedia` (106 samples), `MediaQueryList.matches` |
| Intl API | full-comparison: SIMILAR | (not separate category, part of Window/Navigator) |
| Navigator properties | full-comparison: SIMILAR | 58 Window/Navigator APIs |
| Screen properties | full-comparison: SIMILAR | `Screen.width/height/colorDepth/pixelDepth/availWidth/availHeight` |
| Plugins/MIME types | full-comparison: Navigator | 6 legacy Plugin APIs |
| Speech synthesis | part of CreepJS | `SpeechSynthesis.getVoices` (1 sample) |
| Incognito detection | lite-unique-sources: detectIncognito | (uses serviceWorker probe, not separately visible) |
| Worker context fingerprinting | lite-unique-sources: Signifyd original | 23 Workers/Messaging APIs |
| Cookie/storage testing | lite-unique-sources: cookieMonster | IDB + Storage APIs (10 APIs) |
| WebRTC IP detection | data.json: webrtc section | 11 WebRTC APIs |
| Performance timing | data.json: timing section | 31 Performance/Timing APIs |
| WebGPU adapter + limits | data.json: gpu section | 23 WebGPU APIs |
| StorageManager.estimate | data.json: performanceData.quota | `StorageManager.estimate` (4 samples) |
| AudioWorklet fingerprint | data.json: workletAudioData | `AudioWorkletNode.constructor`, `Worklet.addModule` |
| Permissions probing | data.json: workers.main.permissions | `Permissions.query` (78 samples), `PermissionStatus.state` (18 samples) |
| Crypto key persistence | fork-point-analysis: Signifyd addition | 9 Web Crypto APIs |
| Performance timing benchmark | data.json: timingRes | `Performance.now` (20K samples) in tight loop |
| Privacy signals (DNT, GPC) | data.json: workers section | `Navigator.doNotTrack`, `Navigator.globalPrivacyControl` |

---

## New Findings from Profile

### Extended TextMetrics Properties (7 APIs, not previously documented)

**APIs observed in profile:**

| API | Samples |
|-----|---------|
| `TextMetrics.width` | 184 |
| `TextMetrics.actualBoundingBoxLeft` | 186 |
| `TextMetrics.actualBoundingBoxRight` | 186 |
| `TextMetrics.actualBoundingBoxAscent` | 186 |
| `TextMetrics.actualBoundingBoxDescent` | 186 |
| `TextMetrics.fontBoundingBoxAscent` | 186 |
| `TextMetrics.fontBoundingBoxDescent` | 186 |

**Confirmed by source code analysis** (deobfuscated `lite.js`, canvas function
`Rr()` at ~line 4217):

The script iterates over a CSS font family list (`Ve`) and for each font calls
`measureText()`, then destructures all 7 TextMetrics properties:

```javascript
const {
    actualBoundingBoxAscent: A,
    actualBoundingBoxDescent: H,
    actualBoundingBoxLeft: ne,
    actualBoundingBoxRight: k,
    fontBoundingBoxAscent: G,
    fontBoundingBoxDescent: J,
    width: re
} = s.measureText(j) || {};
```

The 7 values are joined into a comma-separated signature string per font. Unique
signatures are collected via a `Set`, and a `textMetricsSystemSum` is computed as
the sum of all metric values across all unique signatures (scaled by 1e-5). This
sum is included in the fingerprint payload.

Additionally (~line 4262), the script checks whether any bounding box values have
fractional parts (`% 1 !== 0`). If so, it flags "metric noise detected" and sets
`liedTextMetrics: true` — indicating the script actively detects RFP or similar
protections that add noise to these values.

**What's new:** Prior analyses mention `measureText()` only in the context of
font detection (measuring span widths to detect installed fonts). The profile
and source code confirm that Signifyd reads **all 7 TextMetrics properties**
including the bounding box properties for sub-pixel font renderer fingerprinting.

These properties provide sub-pixel-precise glyph metrics that vary by:
- Font renderer (FreeType vs DirectWrite vs CoreText)
- Font hinting settings
- OS-level text rendering configuration
- Specific font version installed

The bounding box values reveal vertical metrics (ascent/descent) that differ
across rendering stacks even when horizontal widths match. This is a more
detailed fingerprint than simple `measureText().width`.

**Prior CreepJS analysis:** The full-comparison document mentions canvas
fingerprinting uses `measureText` but does not mention bounding box properties.

#### Firefox Coverage Assessment

**The primary differentiating factor — font selection — is already collected.**

Bug 2014267 ("Add new font fingerprinting metrics") adds
`gfxPlatformFontList::ListFontsUsedForString()`, a C++ utility that takes a
string and a prioritized font list and returns which fonts the browser would
actually use to render it. This directly captures what drives the major
differences in TextMetrics values across users: which font is selected from the
CSS font-family list.

The bug collects:
- **Variant F:** Fonts used to render `"A"` with a fingerprinter's font list
- **Variant G:** Fonts used to render emoji `👾` with the same list
- **Variant H:** Fonts used to render a large set of emojis (including ZWJ
  sequences) with the same list
- Each variant is tested at two font visibility levels (allowlisted vs
  non-allowlisted), with SHA-256 hashed results

This is collected at the `gfxPlatformFontList` level, which filters out
GPU/canvas rendering variation and isolates the font matching decision — the
dominant signal in what Signifyd extracts.

**Residual gap: sub-pixel rendering differences are not protected.**

TextMetrics values can also vary between users who have the **same fonts** due
to font version differences, hinting settings, and FreeType/fontconfig
configuration. These are the same factors that make canvas pixel data unique.
However, while `CanvasRandomization` (RFP target 9) adds noise to extracted
canvas pixel data, **no noise is added to `measureText()` return values**. There
is no `TextMetrics` RFP target in `RFPTargets.inc`.

A fingerprinter could theoretically bypass canvas randomization by reading
TextMetrics numeric values directly rather than rendering and extracting pixel
data. In practice the font selection is the dominant signal and the residual
sub-pixel rendering differences are a much smaller fingerprinting surface — but
this is an unprotected API path that returns precise floating-point values from
the font renderer.

---

## Investigated and Dismissed: WebRTC

The profile shows 124 `RTCPeerConnection.constructor` samples and 80
`createOffer` samples, which initially appeared to indicate SDP codec
fingerprinting. However, **source code analysis confirms this is not the case.**

The actual WebRTC function (`jn()` at ~line 2270) only performs IP detection:
- Creates a single RTCPeerConnection with Google/Mozilla STUN servers
- Adds a data channel (`"dummyChannel"`) — no audio/video transceivers
- Calls `createOffer` + `setLocalDescription`
- Parses ICE candidates for IPv4 addresses (skips mDNS candidates)
- Returns `{ipAddresses: [...], lied: r}`

The high constructor sample count (124) is explained by the **lie detection
module** (`searchLies` at ~line 1519), which probes `RTCPeerConnection` for API
tampering by repeatedly constructing instances and testing prototype integrity,
descriptor validation, and `toString` behavior. This is API lie detection, not
SDP fingerprinting.

No SDP codec information, DTLS fingerprints, or RTP header extensions are
extracted.

---

## Summary

| Finding | APIs | Status |
|---------|------|--------|
| Extended TextMetrics | 7 | **Mostly covered** — font selection (the dominant signal) is collected by bug 2014267; residual sub-pixel rendering differences via `measureText()` are not protected by any RFP target |
| WebRTC SDP | 11 | **Dismissed** — source confirms IP detection + lie detection only, no SDP fingerprinting |
