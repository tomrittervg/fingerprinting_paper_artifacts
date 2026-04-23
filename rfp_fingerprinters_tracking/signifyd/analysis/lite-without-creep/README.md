# Signifyd lite.js - Non-CreepJS Features

This directory contains a standalone implementation of the fingerprinting checks that are present in Signifyd's `lite.js` but **NOT** in the base CreepJS library (or represent significant architectural changes from CreepJS).

## Background

Signifyd's `lite.js` fingerprinting script was forked from [CreepJS](https://github.com/AbrahamJuliot/creep-js) around **May 20, 2023** (commit `c17490f`). This analysis distinguishes between:

1. **Features inherited from CreepJS** - Patterns that existed in CreepJS at the fork point
2. **Features Signifyd added** - Genuinely new code written by Signifyd
3. **External libraries integrated** - Third-party code Signifyd incorporated

## Features in lite.js

### 1. Incognito / Private Mode Detection [EXTERNAL LIBRARY]
**Source:** [detectIncognito v1.4.1](https://github.com/Joe12387/detectIncognito) by Joe Rutkowski
**Origin:** Third-party library integrated by Signifyd (NOT from CreepJS)

- Uses browser-specific techniques to detect private browsing:
  - **Safari**: Tests `openDatabase` and `localStorage`
  - **Chrome/Chromium**: Tests IndexedDB blob support and storage quota
  - **Firefox**: Tests `serviceWorker` availability
  - **IE**: Tests `indexedDB` availability

### 2. Navigator Anomaly Detection [INHERITED FROM CREEPJS]
**Origin:** This pattern existed in CreepJS at the May 2023 fork point

- The `hasKnownToString()` and `[native code]` detection patterns were already present in CreepJS
- CreepJS uses this as part of its lie detection module (`documentLie()`)
- Signifyd uses the same approach: checking property getters/setters for `[native code]`
- **NOT unique to Signifyd** - this is standard CreepJS functionality

### 3. Worker Context Fingerprinting [SIGNIFYD ADDITION]
**Origin:** Genuinely new code added by Signifyd

This IS architecturally different from CreepJS's approach:
- **CreepJS approach**: Uses `documentLie()` to flag specific mismatches between contexts
- **Signifyd approach**: Has a completely separate inline worker script that collects full navigator profiles independently

Signifyd's implementation:
- Runs navigator fingerprinting in three contexts: Main thread, Web Worker, Shared Worker
- Each context collects a complete profile (platform, userAgent, hardwareConcurrency, etc.)
- Compares full profiles across contexts to detect inconsistencies
- Spoofing tools often fail to consistently modify all contexts

### 4. In-App WebView Detection [SIGNIFYD ADDITION]
**Origin:** New code added by Signifyd (not in CreepJS)

- Detects iOS in-app browsers (Facebook, Instagram, Twitter, LinkedIn, etc.)
- Identifies Android WebViews
- Checks for missing browser features that indicate WebView

### 5. Cookie Monster - Storage Detection [SIGNIFYD ADDITION]
**Origin:** New code added by Signifyd (not in CreepJS)

- Tests cookie read/write capability
- Tests sessionStorage availability
- Tests localStorage availability
- Tests IndexedDB availability
- Detects privacy-restrictive environments

## Summary Table

| Feature | Origin | Unique to Signifyd? |
|---------|--------|---------------------|
| Incognito Detection | External library (detectIncognito) | Yes (integration) |
| Navigator Anomaly Detection | CreepJS fork | **No** |
| Worker Context Fingerprinting | Signifyd code | **Yes** |
| In-App WebView Detection | Signifyd code | **Yes** |
| Cookie Monster / Storage | Signifyd code | **Yes** |

## Files

- `fingerprint.js` - Standalone JavaScript implementation of the non-CreepJS checks
- `index.html` - Demo page that displays fingerprint results
- `README.md` - This documentation

## Usage

### Browser
```html
<script src="fingerprint.js"></script>
<script>
    window.SignifydUniqueFingerprint.collect().then(results => {
        console.log(results);
    });
</script>
```

### Individual Functions
```javascript
// Incognito detection
const incognito = await window.SignifydUniqueFingerprint.detectIncognito();

// Navigator anomalies
const anomalies = window.SignifydUniqueFingerprint.detectNavigatorAnomalies(navigator);

// Worker comparison
const workerData = await window.SignifydUniqueFingerprint.runWorkerFingerprint();

// In-app WebView detection
const webview = window.SignifydUniqueFingerprint.detectInAppWebView();

// Cookie/storage testing
const storage = window.SignifydUniqueFingerprint.cookieMonster();
```

## Running Locally

```bash
# Using Python
python3 -m http.server 8000

# Using Node.js
npx serve .

# Then open http://localhost:8000
```

## What's NOT Included

This implementation does **not** include the fingerprinting techniques that are shared with CreepJS:

- Canvas fingerprinting
- WebGL fingerprinting
- Audio fingerprinting (OfflineAudioContext, AudioWorklet)
- Font enumeration
- Client rects fingerprinting
- CSS media query fingerprinting
- SVG fingerprinting
- Intl API fingerprinting
- Lie/spoof detection module (includes navigator anomaly detection patterns)
- Screen properties
- Navigator properties (basic)

For those techniques, see [CreepJS](https://github.com/AbrahamJuliot/creep-js).

## Note on Navigator Anomaly Detection

The navigator anomaly detection code is included in this demo for completeness and to show
how Signifyd uses it, but it is **NOT unique to Signifyd**. The `[native code]` checking
pattern and `hasKnownToString()` approach existed in CreepJS before the fork. CreepJS
uses this as part of its broader lie detection system (`documentLie()`).

## For Analysis Purposes Only

This code is provided for security research and analysis purposes. It demonstrates the fingerprinting techniques used by Signifyd's fraud detection system that go beyond the base CreepJS library.

## Related Files

- `../fork-point-analysis.md` - Detailed analysis of when and how lite.js was forked from CreepJS
- `../creepjs-signifyd-full-comparison.md` - Full comparison of lite.js vs CreepJS
