# CreepJS vs Signifyd Full Codebase Comparison

## Executive Summary

**Signifyd's fingerprinting library is substantially derived from CreepJS.**

- **7 modules**: Directly copied (identical code)
- **4 modules**: Significantly similar (adapted)
- **1 module**: Different implementation

---

## Module-by-Module Comparison

### IDENTICAL (Direct Copy) - 7 Modules

#### 1. DOMRECT - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| Container style | `perspective:100px;width:1000.099%` | Same |
| Element IDs | `cRect1` - `cRect12` | Same |
| Border colors | `#F72585`, `#7209B7`, `#3A0CA3`, `#4361EE`, `#4CC9F0` | Same |
| Transform | `skewY(23.1753218deg) rotate3d(10.00099, 90, 0.100000000000009, 60000000000008.00000009deg)` | Same |
| Emoji scale | `scale(1.000999)` | Same |

#### 2. SVG - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| Container style | `#svg-container {position: absolute; left: -9999px; height: auto;}` | Same |
| Shift class | `.shift-svg {transform: scale(1.000999) !important;}` | Same |
| Emoji class | `.svgrect-emoji` with `font-size: 200px` | Same |
| Text position | `<text x="32" y="32" class="svgrect-emoji">` | Same |

#### 3. TIMEZONE - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| Magic year | `year: 1113` | Same (line 3887) |
| Properties | `locationMeasured`, `locationEpoch` | Same |
| City list | `America/Santiago`, `America/Sao_Paulo`, etc. | Same |

#### 4. LIES (Lie Detection) - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| Error strings | `"failed illegal error"` | Same (line 1205) |
| | `"failed undefined properties"` | Same (line 1206) |
| | `"failed call interface error"` | Same (line 1207) |
| | `'failed "prototype" in function'` | Same (line 1213) |
| | `"failed descriptor"` | Same (line 1214) |
| | `"failed own property"` | Same (line 1215) |
| | `"failed descriptor keys"` | Same (line 1216) |
| | `"failed own property names"` | Same (line 1217) |
| Function name | `searchLies` | Same (line 1323) |

#### 5. CANVAS - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| Seed value | `seed: 500` | Same (line 4145) |
| Offset | `offset: 2001000001` | Same (line 4146) |
| Color palette | 50 colors starting with `#FF6633`, `#FFB399`, `#FF33FF`, `#FFFF99`, `#00B3E6` | Same (line 3987) |
| Text drawing | `'A'` at position (7, 37), emoji at (0, 37) | Same |
| Error messages | `"pixel data modified"`, `"suspicious pixel data"`, `"metric noise detected"` | Same |

#### 6. AUDIO - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| Context params | `OfflineAudioContext(1, 100, 44100)` | Same |
| Oscillator | `type = 'triangle'`, `frequency.value = 10000` | Same |
| Compressor | `threshold: -50`, `knee: 40`, `attack: 0` | Same |
| Error messages | `"getChannelData and copyFromChannel samples mismatch"` | Same (line 1945) |
| | `"expected -Infinity (silence) and got "` | Same |
| | `"sample noise detected"` | Same |

#### 7. CSS - IDENTICAL
| Evidence | CreepJS | Signifyd |
|----------|---------|----------|
| System colors | 38 colors: `ActiveBorder`, `ActiveCaption`, `Canvas`, `ButtonFace`, etc. | Same (line 3217) |
| System fonts | `caption`, `icon`, `menu`, `message-box`, `small-caption`, `status-bar` | Same (line 3218) |
| Method | `getComputedStyle` inspection | Same |

---

### SIMILAR (Adapted) - 4 Modules

#### 8. INTL - SIMILAR (~80%)
- Same Intl APIs: `DateTimeFormat`, `DisplayNames`, `ListFormat`, `NumberFormat`, `PluralRules`, `RelativeTimeFormat`
- Same `resolvedOptions()` pattern
- Some restructuring in implementation

#### 9. WEBGL - SIMILAR (~60%)
- Same extension: `WEBGL_debug_renderer_info`
- Same constants: `UNMASKED_VENDOR_WEBGL`, `UNMASKED_RENDERER_WEBGL`
- Different rendering/shader code

#### 10. NAVIGATOR - SIMILAR (~70%)
- Same properties: `deviceMemory`, `hardwareConcurrency`, `maxTouchPoints`, `userAgentData`
- Same `getHighEntropyValues` usage
- Restructured organization

#### 11. SCREEN - SIMILAR (~60%)
- Same basic collection: `screen.width`, `screen.height`, `screen.orientation`
- Same `matchMedia` usage
- Different structure

---

### DIFFERENT - 1 Module

#### 12. FONTS - DIFFERENT (~30%)
- Some font names overlap (from CSS_FONT_FAMILY)
- Different detection approach
- Does not use CreepJS's FontFace API inspection pattern

---

## Summary Table

| Module | Status | Confidence | Primary Evidence |
|--------|--------|------------|------------------|
| domrect | **IDENTICAL** | 100% | CSS transforms, element IDs, class names |
| svg | **IDENTICAL** | 100% | CSS structure, scale(1.000999), positioning |
| timezone | **IDENTICAL** | 100% | Magic year `1113`, property names |
| lies | **IDENTICAL** | 100% | All error strings, function names |
| canvas | **IDENTICAL** | 100% | Seed 500, offset 2001000001, color palette |
| audio | **IDENTICAL** | 100% | Audio params, oscillator config, errors |
| css | **IDENTICAL** | 100% | System colors array, system fonts array |
| intl | SIMILAR | 80% | API names, resolvedOptions pattern |
| navigator | SIMILAR | 70% | Property names, restructured |
| webgl | SIMILAR | 60% | Extension names, different shaders |
| screen | SIMILAR | 60% | Basic collection, different structure |
| fonts | DIFFERENT | 30% | Some overlap, different approach |

---

## Code Overlap Statistics

```
IDENTICAL modules:  7/12 (58%)
SIMILAR modules:    4/12 (33%)
DIFFERENT modules:  1/12 (8%)

Estimated code derivation: ~75-85% from CreepJS
```

---

## Distinctive Magic Values Found in Both

These highly specific values appear in both codebases:

| Value | Purpose | Probability of Coincidence |
|-------|---------|---------------------------|
| `1113` | Timezone year | Extremely low |
| `1.000999` | Transform scale | Extremely low |
| `23.1753218deg` | SkewY angle | Essentially zero |
| `60000000000008.00000009deg` | Rotate3d angle | Essentially zero |
| `2001000001` | Canvas offset | Extremely low |
| `500` | Canvas seed | Low |
| `#FF6633, #FFB399, #FF33FF...` | 50-color palette | Essentially zero |
| `"failed illegal error"` | Lie detection | Very low |
| `"failed undefined properties"` | Lie detection | Very low |

---

## Conclusion

Signifyd's fingerprinting code is **substantially derived from CreepJS**. The evidence includes:

1. **7 modules with identical code** - same magic numbers, strings, CSS values
2. **4 modules with significant similarity** - same APIs and patterns
3. **Unique values** that would be statistically impossible to generate independently
4. **Same error message strings** verbatim
5. **Same lie detection methodology** with identical checks

The relationship is clear: **Signifyd copied/forked CreepJS** and made modifications:
- Removed TypeScript types
- Minified/obfuscated variable names
- Possibly removed some modules (fonts appears different)
- Restructured some modules while keeping core logic

---

## CreepJS Attribution

CreepJS itself credits inspiration from TU Munich:
```javascript
// inspired by
// https://privacycheck.sec.lrz.de/active/fp_gcr/fp_getclientrects.html
// https://privacycheck.sec.lrz.de/active/fp_e/fp_emoji.html
```

### Lineage
```
TU Munich privacycheck (academic research)
         ↓
      CreepJS (open source implementation)
         ↓
      Signifyd (commercial deployment, obfuscated)
```
