# Signifyd lite.js Fork Point Analysis

## Summary

**lite.js was forked from CreepJS at or very shortly after commit `c17490f` (May 20, 2023).**

This analysis was conducted by systematically bisecting the CreepJS commit history (2,327 commits) to identify the exact point where Signifyd's lite.js diverged from the open-source CreepJS fingerprinting library.

## Methodology

The analysis used several distinguishing markers to narrow down the fork point:

1. **Magic values**: Specific constants used in fingerprinting (e.g., `23.1753218` for skewY, `2001000001` for canvas offset)
2. **Feature presence/absence**: Checking for features added at specific commits
3. **Code patterns**: Comparing specific function implementations and property names
4. **Font lists**: Comparing platform-specific font detection lists

## Evidence Table

| Feature | Added to CreepJS | Commit | In lite.js? |
|---------|------------------|--------|-------------|
| GPU/GPUAdapter lie detection | May 8, 2023 | fd76496 | ✅ Yes |
| StorageManager.estimate lie detection | May 8, 2023 | fd76496 | ✅ Yes |
| "any-pointer" property fix (was `anyPointer`) | May 20, 2023 | c17490f | ✅ Yes |
| measure() console.table timing detection | July 10, 2023 | 2696efc | ❌ No |
| Trash accept loop optimization | July 10, 2023 | 7f7caa2 | ❌ No (module removed) |
| "Futura Bold" in font detection | Removed Aug 1, 2023 | 369756e | ✅ Has old version |
| "Roboto" in font detection | Removed Aug 1, 2023 | 369756e | ✅ Has old version |
| "suspicious" → "uncommon" text change | Aug 1, 2023 | 369756e | ✅ Has old "suspicious" |
| macOS 13 Ventura font support | Nov 28, 2023 | d08ed6a | ❌ No |

## Timeline

```
CreepJS Commit History (relevant section):

May 8, 2023  - fd76496 - refactor: expand search (GPU/StorageManager lie detection)
May 8, 2023  - a1af87a - refactor: reconfigure ratings
May 20, 2023 - c17490f - fix: destructor correct property (any-pointer fix)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                         FORK POINT - lite.js based on this commit

[No commits between May 20 and July 10]

July 10, 2023 - 973ef3d - fix: hasLied&hasErrors are undefined
July 10, 2023 - 7f7caa2 - Shorten trash accept using loops
July 10, 2023 - 11d1aa0 - refactor: simplify gibbers
July 10, 2023 - 2696efc - feat: measure (NOT in lite.js)
...
Aug 1, 2023  - 369756e - fix: polish font labels (NOT in lite.js)
Nov 28, 2023 - d08ed6a - Fix macOS 12 fonts. Add macOS 13 fonts (NOT in lite.js)
```

## Fork Window

- **Earliest possible**: May 20, 2023 (has the `any-pointer` fix)
- **Latest possible**: July 10, 2023 (lacks the `measure()` feature)
- **Most likely**: Commit c17490f (May 20, 2023) or the state immediately after

Since there were no commits between May 20 and July 10, 2023, the fork was almost certainly based on the exact state at commit c17490f.

## What Signifyd Modified

### Modules Removed
- **Trash/gibberish detection** - Detects suspicious/gibberish strings in browser properties
- **Headless detection** - Detects headless browsers (Puppeteer, Playwright, etc.)
- **Resistance detection** - Detects privacy tools and fingerprint resistance
- **Bot hash calculation** - CreepJS-specific bot scoring

### Modules Kept (Intact or with minor changes)
- **Lies module** - Detects API tampering/spoofing
- **Canvas fingerprinting** - 2D canvas and paint patterns
- **WebGL fingerprinting** - GPU and renderer detection
- **Audio fingerprinting** - AudioContext and OfflineAudioContext
- **Fonts fingerprinting** - Font enumeration via FontFace API
- **Client rects** - DOMRect and element positioning
- **CSS media queries** - Screen and display detection
- **Intl API** - Locale and timezone fingerprinting
- **SVG fingerprinting** - SVG rendering characteristics
- **Navigator properties** - Browser and device information
- **Screen properties** - Display resolution and color depth

### Features Added by Signifyd
- **detectIncognito** - Private/incognito mode detection
- **Anomaly tracking** - Navigator property anomaly detection
- **Crypto key persistence** - CryptoKey-based device identification
- **Server integration** - Custom encryption and API submission
- **Worker contexts** - Web Worker and SharedWorker fingerprinting

## Derivation Estimate

Based on this analysis, lite.js represents approximately **75-85%** of CreepJS functionality from the May 2023 timeframe. The core fingerprinting modules are substantially identical, with Signifyd selectively removing anti-fraud/bot detection modules and adding their own server integration layer.

## Verification Commands

To verify these findings, the following checks can be performed:

```bash
# Clone CreepJS and checkout the fork point
git clone https://github.com/AbrahamJuliot/creep-js /tmp/creepjs
cd /tmp/creepjs
git checkout c17490f

# Check for key markers
grep -r "23.1753218" src/           # skewY transform value
grep -r "2001000001" src/           # canvas offset
grep -r "any-pointer" src/          # should find hyphenated version
grep -r "measure" src/utils/exile.ts # should NOT find measure function
```

## Files Analyzed

- `signifyd/sample_scripts/raw/lite.js` (153KB, obfuscated)
- `signifyd/sample_scripts/deobfs/lite.js` (236KB, deobfuscated)
- CreepJS repository: https://github.com/AbrahamJuliot/creep-js (2,327 commits analyzed)

## Conclusion

Signifyd's lite.js fingerprinting script is substantially derived from the CreepJS open-source library, forked around May 20, 2023. The company removed modules focused on detecting automated browsers and fingerprint resistance tools, while retaining the core browser fingerprinting capabilities and adding their own incognito detection and server-side integration features.
