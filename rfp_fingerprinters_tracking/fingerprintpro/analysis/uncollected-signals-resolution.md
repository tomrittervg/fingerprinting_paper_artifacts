# FingerprintJS Pro — Resolution of Uncollected Signals

Analysis of why each signal identified in `uncollected-signals-detail.md` does
not require a new metric in Firefox's `user-characteristics` ping.

---

## 1. AudioContext.baseLatency

**Zero entropy across Firefox users.**

Firefox hardcodes `baseLatency` to `0.0` in
`dom/media/webaudio/AudioContext.h:194-198` because Gecko performs no buffering
between audio rendering and the audio subsystem. Every Firefox user returns the
same value. The signal only has cross-browser entropy (Firefox returns 0.0,
Chrome returns hardware-dependent values), which is already captured by the
User-Agent string.

---

## 2. color-gamut CSS Media Query

**Zero entropy across Firefox users.**

`Screen::GetColorGamut()` in `widget/Screen.cpp:119-123` is stubbed to always
return `ScreenColorGamut::Srgb`, regardless of the actual display hardware.
There is a TODO (bug 1771373) to implement proper detection, but until that
lands, every Firefox user reports `srgb` for the `color-gamut` media query.

The `screens` metric already collects `colorDepth` per screen, which provides
the only display color information that currently varies across users. If
bug 1771373 is fixed in the future, `colorGamut` should be added to the
`screens` JSON at that time.

---

## 3. forced-colors CSS Media Query

**Already covered by `use_document_colors` metric.**

From web content's perspective (which is the fingerprinting context),
`forced-colors: active` is true if and only if `mUseDocumentColors` is false.
The `Requested` value of the `ForcedColors` enum only applies to chrome
contexts, not to web content where fingerprinting occurs.

The existing `use_document_colors` boolean metric
(`glean::characteristics::use_document_colors`) already captures this state.
A user with `use_document_colors = false` will have `forced-colors: active`
in web content, and vice versa.

Additionally, the `prefers_contrast` metric captures the related contrast
preference, and `css_system_colors` captures the actual system color values
that are forced when `forced-colors: active` applies.

---

## 4. measureText() Widths Per Font Family

**Already determined by existing font metrics.**

The `css_system_fonts` metric collects the resolved `fontSize + fontFamily`
for each generic font family (serif, sans-serif, monospace, system-ui, and
several named fonts). Given a known font and size, the `measureText()` width
is deterministic for a given rendering stack. Since the rendering stack is
determined by the OS and Firefox version (both already known), the
measureText values contain no additional information beyond what
`css_system_fonts` provides.

Furthermore, the font name preferences are collected directly:
- `font_name_serif_western` / `font_name_serif_default_group`
- `font_name_sans_serif_western` / `font_name_sans_serif_default_group`
- `font_name_monospace_western` / `font_name_monospace_default_group`

The sub-pixel precision differences FPJS observes (e.g. `147.583` vs `144.017`)
come from the specific font that each generic family resolves to, which is
exactly what these metrics capture.

---

## 5. CSS calc() Rounding / URL Protocol Parsing

**Zero entropy across Firefox users.**

Both signals produce identical results for all Firefox users on the same
version:

- **CSS calc() rounding:** All Firefox users get the same serialization of
  `calc()` expressions because the rounding behavior is engine-level, not
  user-dependent.
- **URL protocol parsing:** `new URL("C:/").protocol` returns `"c:"` on all
  Firefox instances, while Chrome returns `"file:"`. This is a browser engine
  identifier, not a user-distinguishing signal.

The `user_agent` metric already identifies the browser engine and version.

---

## 6. CSS.supports() for backdrop-filter

**Already covered by existing GPU metrics.**

The `backdrop-filter` support status is determined by two factors:
1. The `layout.css.backdrop-filter.enabled` preference (default `true` since
   Firefox 103)
2. The GPU blocklist (`gfx::gfxVars::AllowBackdropFilter()`)

Users with blocklisted GPUs already show distinct values in the existing GPU
metrics:
- `gl_renderer` / `gl_vendor` identify the GPU hardware
- `canvas_feature_status` reports canvas acceleration status and failure reasons
- `using_accelerated_canvas` reports the acceleration state
- `wgpu_is_fallback_adapter` reports WebGPU software fallback

A GPU that is blocklisted for backdrop-filter will also show anomalies in these
existing metrics. The additional boolean from `CSS.supports("backdrop-filter",
"blur(2px)")` would be redundant with the GPU identification already captured.

---

## Summary

| # | Signal | Why not needed |
|---|--------|---------------|
| 1 | AudioContext.baseLatency | Hardcoded to 0.0 for all Firefox users |
| 2 | color-gamut | Stubbed to srgb for all Firefox users (bug 1771373) |
| 3 | forced-colors | Equivalent to existing `use_document_colors` metric |
| 4 | measureText() widths | Determined by existing `css_system_fonts` + font name prefs |
| 5 | CSS calc() / URL parsing | Zero per-user entropy, browser engine identifier only |
| 6 | CSS.supports(backdrop-filter) | GPU already identified by existing gl_renderer/canvas metrics |
