# FingerprintJS Pro — Detailed Analysis of Uncollected Signals

Six fingerprinting signals collected by FingerprintJS Pro v3.12.6 that are
not currently tracked by Firefox's `user-characteristics` ping. For each
signal: what FPJS collects, the observed value, how Firefox implements the
underlying API, what the fingerprinting surface actually is, and whether
collection would be valuable.

---

## 1. AudioContext.baseLatency

### What FPJS collects

FPJS signal **s96** (per deobs analysis, function `Zu$1 → Rt`) reads
`AudioContext.baseLatency` — a double representing the number of seconds
of processing latency incurred by the audio context passing the audio from
the AudioDestinationNode to the audio subsystem.

In the intercepted data, s96 returned `{"s": -2, "v": null}` (status -2 =
"missing prerequisite"), meaning the FPJS prerequisite check for this signal
failed on Firefox 149.

**Note on signal key confusion:** The data intercept analysis attributed
baseLatency to key **s22** with value `23`, but since Firefox's baseLatency
is hardcoded to `0.0`, the value `23` cannot be baseLatency. The deobs
analysis maps s22 to `navigator.webdriver` (duplicate in the identification
module). The true baseLatency signal is s96, which returned null.

### How Firefox implements it

**File:** `dom/media/webaudio/AudioContext.h:194-198`
```cpp
double BaseLatency() const {
  // Gecko does not do any buffering between rendering the audio and sending
  // it to the audio subsystem.
  return 0.0;
}
```

Firefox **always returns `0.0`** because Gecko performs no buffering between
audio rendering and the audio subsystem. This is hardcoded and
platform-independent.

By contrast, `outputLatency` is platform-dependent and IS spoofed by RFP:

**File:** `dom/media/webaudio/AudioContext.cpp:553-574`

| Platform | RFP-spoofed outputLatency |
|----------|--------------------------|
| macOS | `512 / sampleRate` seconds |
| Android | `0.020` seconds |
| Windows | `0.040` seconds |
| Linux | `0.025` seconds |

### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **Zero** — all Firefox users get `0.0` |
| **Cross-browser entropy** | **High** — Chrome returns hardware-dependent values (typically `128/sampleRate` to `512/sampleRate`); Safari returns similar non-zero values |
| **RFP status** | Not modified (unnecessary since value is constant) |
| **RFP target** | `RFPTarget::AudioContext` covers outputLatency but baseLatency needs no protection |

### Should Firefox collect this?

**No strong reason.** Since `baseLatency` is `0.0` for all Firefox users,
collecting it would yield a column of identical values. However, there are
two edge cases worth noting:

1. **If Firefox ever changes its audio architecture** to use buffering,
   baseLatency could become non-zero and platform-dependent, creating a
   fingerprinting surface. A metric would detect this.

2. **Cross-browser identification:** The constant `0.0` value is itself a
   fingerprint — it immediately identifies the browser as Firefox (or at
   least non-Chromium). If RFP were to spoof this to a plausible non-zero
   value, we'd need telemetry to verify the spoofed value isn't itself
   distinctive.

**Recommendation:** Low priority. The existing `audio_fingerprint`,
`audio_fingerprint2`, and related audio metrics already cover the high-
entropy audio surfaces. A `baseLatency` metric would only matter if Firefox's
audio architecture changes or if RFP spoofing is considered.

---

## 2. color-gamut CSS Media Query

### What FPJS collects

FPJS signal **s37** (function `Pu → lt`) evaluates the `color-gamut` CSS
media query, which indicates the approximate range of colors supported by
the user's display. Possible values: `srgb`, `p3`, `rec2020`.

**Observed value:** `"srgb"`

FPJS tests via `matchMedia()`:
```javascript
matchMedia('(color-gamut: rec2020)').matches  // widest gamut
matchMedia('(color-gamut: p3)').matches       // wide gamut (Apple displays)
matchMedia('(color-gamut: srgb)').matches     // standard
```

### How Firefox implements it

**File:** `layout/style/nsMediaFeatures.cpp:154-168`
```cpp
StyleColorGamut Gecko_MediaFeatures_ColorGamut(const Document* aDocument) {
  auto* dx = GetDeviceContextFor(aDocument);
  if (!dx || aDocument->ShouldResistFingerprinting(RFPTarget::CSSColorInfo)) {
    return StyleColorGamut::Srgb;
  }
  switch (dx->GetColorGamut()) {
    case dom::ScreenColorGamut::Srgb:
      return StyleColorGamut::Srgb;
    case dom::ScreenColorGamut::Rec2020:
      return StyleColorGamut::Rec2020;
    case dom::ScreenColorGamut::P3:
      return StyleColorGamut::P3;
  }
  return StyleColorGamut::Srgb;
}
```

The value comes from `DeviceContext::GetColorGamut()` which queries the
display's actual color gamut capabilities.

**RFP behavior:** When `RFPTarget::CSSColorInfo` is active, Firefox always
returns `Srgb` regardless of the actual display.

### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **Moderate** — most desktop users have sRGB displays, but wide-gamut P3 displays are increasingly common (most Apple displays since 2016, many high-end Windows monitors, some phones) |
| **Platform correlation** | macOS users disproportionately have P3 displays; Windows/Linux users are mostly sRGB |
| **Values in the wild** | `srgb` (majority), `p3` (growing minority, especially macOS), `rec2020` (rare) |
| **RFP status** | Spoofed to `srgb` when `CSSColorInfo` target is active |

### Why this matters

The `color-gamut` value correlates strongly with:
- **Hardware cost** — wide-gamut displays are more expensive
- **Platform** — nearly all modern Macs report P3
- **Display model** — can narrow down specific display hardware

Combined with `screen.colorDepth` (already collected via `screens` JSON),
this creates a display hardware profile. A user with `colorDepth: 30` and
`color-gamut: p3` is on a distinctly different display than one with
`colorDepth: 24` and `color-gamut: srgb`.

### Should Firefox collect this?

**Yes.** This is a genuinely variable signal across the Firefox population
that FPJS actively uses for fingerprinting. It's easy to collect (single
media query evaluation), and we need to understand the distribution to:

1. Verify that the RFP spoofing to `srgb` is effective
2. Understand how many users are distinguishable via wide-gamut displays
3. Assess whether a future `color-gamut: p3` spoof would be more appropriate
   as P3 displays become the majority

**Implementation:** Add a metric that reads
`Gecko_MediaFeatures_ColorGamut()` (bypassing RFP) and reports the raw
enum value. Similar to how `prefers_contrast` calls
`Gecko_MediaFeatures_PrefersContrast`.

---

## 3. forced-colors CSS Media Query

### What FPJS collects

FPJS signal **s39** (function `Tu → dt`) evaluates the `forced-colors` CSS
media query, which indicates whether the user agent is enforcing a limited
color palette on the page (e.g., Windows High Contrast mode).

**Observed value:** `false` (= `forced-colors: none`)

FPJS tests via:
```javascript
matchMedia('(forced-colors: active)').matches  // true if forced
```

### How Firefox implements it

**File:** `servo/components/style/gecko/media_features.rs:274-281`
```rust
fn eval_forced_colors(context: &Context, query_value: Option<ForcedColors>) -> bool {
    let forced = context.device().forced_colors();
    match query_value {
        Some(query_value) => query_value == forced,
        None => forced != ForcedColors::None,
    }
}
```

The `ForcedColors` enum has three values:
- `None` — page colors are not forced
- `Requested` — forced colors are requested (Chrome context only, Windows)
- `Active` — page colors are being forced

**File:** `layout/base/nsPresContext.cpp:740-779` — `UpdateForcedColors()`:

The value is determined by:
1. **BrowsingContext override** → returns `Active` if explicitly set
2. **`mUseDocumentColors` = false** (user set "Never" for "Allow pages to
   choose their own fonts/colors" in Settings) → returns `Active`
3. **Windows High Contrast** + Chrome context → returns `Requested`
4. **Default** → returns `None`

**RFP behavior:** There is **no RFP spoofing** for `forced-colors`. The
`RFPTargets.inc` file has no target for this media feature. The value always
reflects the user's actual setting.

### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **Low but significant** — the vast majority of users are `none`, but the `active` population is a small, distinctive group |
| **Who has forced-colors: active** | Users of Windows High Contrast mode, users who disabled "Allow pages to choose their own colors" in Firefox settings, users of accessibility tools |
| **Cross-correlation** | Strongly correlates with `prefers-contrast`, `use_document_colors`, system color values. Together these form an accessibility fingerprint. |
| **RFP status** | **NOT SPOOFED** — potential gap |

### Why this matters

While most users (~98%+) will report `forced-colors: none`, the signal is
important for two reasons:

1. **Accessibility fingerprinting:** The small population of users with
   `forced-colors: active` is already identifiable through the existing
   `prefers_contrast` and system color metrics, BUT we don't currently know
   the precise mapping. A user could have `prefers-contrast: more` without
   `forced-colors: active` (they just have high-contrast theme colors) or
   vice versa. Collecting both would clarify the relationship.

2. **RFP gap:** Unlike `prefers-contrast`, `prefers-reduced-motion`, and
   other media features, `forced-colors` has **no RFP spoofing target**.
   This means that even with RFP enabled, a user in High Contrast mode will
   still report `forced-colors: active` to web content. This is a potential
   information leak.

3. **Interaction with system colors:** When `forced-colors: active`, the
   browser overrides page colors with system colors. The existing
   `css_system_colors` metric captures those colors, but without knowing
   whether forced-colors is active, we can't distinguish "user has unusual
   theme colors" from "user has forced colors that override everything."

### Should Firefox collect this?

**Yes.** This fills a gap in the existing accessibility-related metrics.
Currently we collect `prefers_contrast`, `inverted_colors`,
`prefers_reduced_motion`, `prefers_reduced_transparency`, `color_scheme`,
and system colors — but we're missing the forced-colors state that ties
them together. It's also needed to identify the RFP spoofing gap.

**Implementation:** Add a metric that reads the `ForcedColors` enum value
from `nsPresContext::mForcedColors`. This parallels how `prefers_contrast`
reads from `Gecko_MediaFeatures_PrefersContrast`.

**Additionally:** Consider adding an RFP target for `forced-colors` that
spoofs it to `none` when RFP is enabled.

---

## 4. measureText() Widths Per Font Family

### What FPJS collects

FPJS signal **s51** (function `Lc`) calls `CanvasRenderingContext2D.measureText()`
with specific text and measures the `width` property across different CSS
generic font families.

**Observed value:**
```json
{
  "default": 147.5833282470703,
  "apple":   147.5833282470703,
  "serif":   147.5833282470703,
  "sans":    144.01666259765625,
  "mono":    133.1666717529297,
  "min":     9.23333740234375,
  "system":  146
}
```

Each key corresponds to a generic font family (or a specific test):
- `default` — the default canvas font
- `apple` — `-apple-system` (maps to system UI font)
- `serif` — `serif` generic family
- `sans` — `sans-serif` generic family
- `mono` — `monospace` generic family
- `min` — minimum measurable unit (single narrow character)
- `system` — `system-ui` font

### How Firefox implements measureText()

**File:** `dom/canvas/CanvasRenderingContext2D.cpp:4661-4666`
```cpp
UniquePtr<TextMetrics> CanvasRenderingContext2D::MeasureText(
    const nsAString& aRawText, ...) {
  return DrawOrMeasureText(aRawText, 0, 0, maxWidth,
                           TextDrawOperation::MEASURE, aError);
}
```

The returned `TextMetrics` object includes:
- `width` (horizontal advance)
- `actualBoundingBoxLeft`, `actualBoundingBoxRight`
- `fontBoundingBoxAscent`, `fontBoundingBoxDescent`
- `actualBoundingBoxAscent`, `actualBoundingBoxDescent`
- `emHeightAscent`, `emHeightDescent`
- `hangingBaseline`, `alphabeticBaseline`, `ideographicBaseline`

**Precision:** Results are `double` values derived from internal app-unit
calculations (60 app-units per CSS pixel on desktop), divided by
`AppUnitsPerDevPixel`. This gives sub-pixel precision that varies by
platform, font rendering engine, and font hinting settings.

### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **High** — the exact pixel width depends on the specific font resolved for each generic family, which varies by OS, installed fonts, font configuration prefs, DPI, and text rendering settings |
| **What varies** | The specific font that `serif`, `sans-serif`, `monospace`, and `system-ui` resolve to. On Linux this depends on fontconfig; on macOS it's system fonts; on Windows it's registry-based defaults. |
| **Cross-browser entropy** | Very high — different engines render text differently even with the same font |
| **RFP status** | **NOT PROTECTED** — `measureText()` returns full precision values with no rounding, noise, or spoofing |

### Why this matters

The `measureText()` values are a **high-entropy font fingerprint** that
doesn't require the traditional font enumeration technique (which Firefox
already tracks via `fonts_fpjs_*` metrics). Instead of testing whether
specific fonts exist, this measures the *precise rendering* of the fonts
the browser has already resolved.

This is significant because:

1. **Font allowlisting doesn't fully protect against this.** Even if Firefox
   restricts which fonts are visible to web content, the precise measurement
   of *allowed* fonts still varies. Two users with the same font list but
   different OS versions, DPI settings, or font hinting configuration will
   get different measurements.

2. **Sub-pixel precision leaks rendering details.** The observed values have
   ~14 digits of precision (e.g., `147.5833282470703`). Different text
   rendering stacks (DirectWrite on Windows, CoreText on macOS, FreeType
   on Linux) produce subtly different sub-pixel widths.

3. **The `system` measurement is particularly revealing.** The `system-ui`
   font resolves to entirely different fonts on each platform (San Francisco
   on macOS, Segoe UI on Windows, whatever fontconfig maps to on Linux),
   and `146` vs `147.58` immediately distinguishes platforms.

4. **`min` measures the narrowest character.** The value `9.23333740234375`
   is sensitive to the font's minimum glyph advance and the rendering
   engine's handling of very small measurements.

### Current Firefox font metrics

Firefox already collects extensive font data:
- `missing_fonts` — fonts absent from the platform
- `fonts_fpjs_*` — SHA256 of FPJS-style font enumeration results
- `fonts_variant_a` through `h` — multiple font detection strategies
- `css_system_fonts` — computed font properties for system font keywords
- Font preference prefs (`font_name_serif_western`, etc.)
- `text_anti_aliasing` — font anti-aliasing level

However, **none of these capture the exact `measureText()` pixel widths**
that FPJS uses. The `css_system_fonts` metric collects
`fontSize + fontFamily` strings (e.g., `"16px Arial"`) but not the precise
rendered measurements.

### Should Firefox collect this?

**Yes, with qualification.** This is a genuinely high-entropy fingerprinting
vector that Firefox doesn't currently track. The qualification is that the
precise values will vary with font configuration changes (which happen with
OS updates), so the metric needs to be understood in context.

**Implementation options:**
1. **Direct replication:** Run `measureText()` with the same text FPJS uses,
   across the same font families, and record the widths. This gives us exact
   FPJS-comparable data.
2. **Representative sample:** Pick 3-4 generic families (`serif`,
   `sans-serif`, `monospace`, `system-ui`) and a standard test string,
   record widths. Simpler, still captures the key variance.
3. **Hash approach:** Concatenate the width values and hash them (like
   `fonts_fpjs_*` does for font enumeration). Loses per-family detail but
   provides a single "text rendering fingerprint" value.

**Recommendation:** Option 1 for initial collection (to understand the
distribution), then potentially move to a hash once the variance is
characterized.

---

## 5. CSS calc() Rounding and URL Protocol Parsing

These are two separate signals that both fingerprint browser engine
implementation details.

### 5a. CSS calc() Rounding Precision

#### What FPJS collects

FPJS signal **s203** (function `El`, encrypted via `bl` string table) creates
an element with a CSS `calc()` value and reads back the computed value via
`getComputedStyle()`.

**Observed value:** `"calc(-0.0773484px)"`

The technique works like this:
```javascript
element.style.someProperty = "calc(very precise expression)";
computed = getComputedStyle(element).someProperty;
// Different engines round the computed value differently
```

The key insight is that CSS engines differ in how they:
- Round intermediate `calc()` results
- Represent sub-pixel values in computed style strings
- Handle precision of floating-point CSS values

#### How Firefox handles CSS precision

Firefox's layout engine uses **app units** for internal precision (60
app-units per CSS pixel on desktop). When CSS `calc()` expressions are
computed:

1. The expression is evaluated in floating-point
2. The result is converted to app-units (rounded to nearest 1/60th of a px)
3. When read back via `getComputedStyle()`, the value is converted back to
   a CSS string with the engine's default precision

Different browsers produce different serializations:
- Firefox: `"calc(-0.0773484px)"` (preserves the calc expression form)
- Chrome: might serialize as a plain value like `"-0.077px"`
- Safari: might use different precision

#### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **Near-zero** — all Firefox users on the same version produce the same `calc()` rounding behavior |
| **Cross-browser entropy** | **High** — immediately distinguishes Firefox from Chrome from Safari |
| **RFP status** | No protection |
| **Variation within Firefox** | Could differ between versions if the CSS serialization code changes |

### 5b. URL Protocol Parsing

#### What FPJS collects

FPJS signal **s205** (function `Sl`) evaluates `new URL("C:/").protocol`.

**Observed value:** `"c:"`

Different browsers handle this non-standard URL differently:
- Firefox: treats `"C:"` as a protocol → returns `"c:"`
- Chrome: normalizes to a file URL → returns `"file:"`
- Safari: similar to Chrome

#### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **Zero** — all Firefox users return `"c:"` |
| **Cross-browser entropy** | **High** — binary Firefox-vs-not-Firefox signal |
| **RFP status** | No protection (would be impractical to change URL parsing) |

### Should Firefox collect these?

**Probably not worth standalone metrics.** Both signals have zero entropy
across the Firefox population — every Firefox user produces the same
result. They function as browser-engine identifiers, not user-distinguishing
fingerprints. The `user_agent` metric already identifies the browser engine.

However, they are worth documenting because:
1. They prove that FPJS performs browser engine identification through
   behavioral probes (not just User-Agent string parsing)
2. RFP cannot realistically protect against these — changing `calc()`
   serialization or URL parsing would break web compatibility
3. They remind us that "same behavior across all Firefox users" IS the
   defense — the signal has entropy across *browsers* but not across
   *Firefox users*

**Recommendation:** No metric needed. Document as known cross-browser
fingerprinting vectors that Firefox inherently normalizes.

---

## 6. CSS.supports() for backdrop-filter

### What FPJS collects

FPJS signal **s139** (function `fs`) evaluates:
```javascript
CSS.supports("backdrop-filter", "blur(2px)")
```

**Observed value:** `true`

This tests whether the browser supports the `backdrop-filter` CSS property,
which applies graphical effects (like blur) to the area behind an element.

### How Firefox implements it

**File:** `layout/style/CSS.cpp:25-34`
```cpp
bool CSS::Supports(const GlobalObject&, const nsACString& aProperty,
                   const nsACString& aValue) {
  return Servo_CSSSupports2(&aProperty, &aValue);
}
```

Delegates to Servo's CSS parser, which checks whether the property is
recognized and the value is valid syntax.

**File:** `layout/style/nsCSSProps.h:128-132`
```cpp
static bool IsBackdropFilterAvailable(JSContext*, JSObject*) {
  return IsEnabled(eCSSProperty_backdrop_filter, EnabledState::ForAllContent);
}
```

`backdrop-filter` availability depends on **two factors:**
1. The `layout.css.backdrop-filter.enabled` preference (default: `true`
   since Firefox 103)
2. The **graphics hardware blocklist** — `gfx::gfxVars::AllowBackdropFilter()`

The graphics blocklist means that **some users will have backdrop-filter
disabled** even on current Firefox versions if their GPU/driver combination
is blocklisted.

### Fingerprinting surface

| Aspect | Detail |
|--------|--------|
| **Entropy across Firefox users** | **Low but non-zero** — most users get `true`, but users with blocklisted GPUs get `false` |
| **What causes `false`** | Blocklisted GPU/driver combinations, very old Firefox versions, or users who manually disabled the pref |
| **Cross-browser entropy** | Low — all modern browsers support backdrop-filter |
| **RFP status** | No protection |
| **Update behavior** | `GfxVarReceiver` monitors blocklist changes and dynamically updates the enabled state |

### Why this matters

This is a **feature-detection fingerprint** — it doesn't detect what the
user did (like a font choice), it detects what their hardware supports.
The small population of users where `CSS.supports("backdrop-filter",
"blur(2px)")` returns `false` is distinctive:

1. They likely have older or unusual GPU hardware
2. This correlates with other GPU-derived signals (WebGL renderer, WebGPU
   limits)
3. The blocklist changes over time, so the `false` population shifts

### Current Firefox coverage

Firefox collects related GPU information:
- `gl_renderer`, `gl_vendor` — WebGL GPU identity
- `using_accelerated_canvas` — canvas acceleration status
- `canvas_feature_status` — ACCELERATED_CANVAS2D feature status/failure
- `wgpu_is_fallback_adapter` — whether WebGPU uses software fallback

However, **none of these directly capture whether `backdrop-filter` is
enabled.** A user could have working WebGL but blocklisted backdrop-filter
(or vice versa).

### Should Firefox collect this?

**Yes, it's very easy and fills a small gap.** The implementation is
trivial — call `CSS.supports("backdrop-filter", "blur(2px)")` or check
`nsCSSProps::IsBackdropFilterAvailable()` and record the boolean.

More broadly, this is an example of a class of signals — **CSS feature
support detection** — that fingerprinters can enumerate. Other examples:
- `CSS.supports("color", "oklch(0% 0 0)")` — OKLCH color support
- `CSS.supports("container-type", "inline-size")` — container queries
- `CSS.supports("view-transition-name", "foo")` — view transitions

Each has potential to distinguish browser versions or GPU capabilities.
Rather than collecting individual `CSS.supports()` results, Firefox could
consider a broader approach: hash the support status of a standard set of
CSS features that are known to vary across the Firefox population.

**Recommendation:** Collect as a boolean metric. Consider expanding to
a small set of GPU-gated CSS features (backdrop-filter, plus any others
that depend on the graphics blocklist).

---

## Summary Table

| # | Signal | Entropy (Firefox) | Collected Elsewhere? | Recommendation |
|---|--------|-------------------|---------------------|----------------|
| 1 | AudioContext.baseLatency | Zero (always 0.0) | audio_fingerprint covers other audio surfaces | **Skip** — no within-Firefox entropy |
| 2 | color-gamut | Moderate (srgb vs p3) | screens has colorDepth but not gamut | **Collect** — real per-user variance |
| 3 | forced-colors | Low but significant | prefers_contrast is related but distinct | **Collect** — fills accessibility gap, RFP gap |
| 4 | measureText() widths | High | css_system_fonts and fonts_* are related but not equivalent | **Collect** — high-entropy vector not currently tracked |
| 5 | CSS calc() / URL parsing | Zero | user_agent identifies the engine | **Skip** — cross-browser only, no within-Firefox entropy |
| 6 | CSS.supports(backdrop-filter) | Low (GPU blocklist) | canvas_feature_status is related | **Collect** — easy, small gap in GPU-gated features |

### Priority Order

1. **measureText() widths** — highest entropy, most impactful gap
2. **color-gamut** — moderate entropy, easy to collect, RFP-relevant
3. **forced-colors** — fills RFP gap, important for accessibility fingerprinting understanding
4. **CSS.supports(backdrop-filter)** — trivial to add, fills minor GPU gap
5. ~~CSS calc() / URL parsing~~ — not recommended
6. ~~AudioContext.baseLatency~~ — not recommended
