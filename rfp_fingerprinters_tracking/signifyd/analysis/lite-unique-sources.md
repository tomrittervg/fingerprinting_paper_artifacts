# Source Analysis: Signifyd lite.js Unique Features

This document analyzes the 5 fingerprinting features unique to Signifyd's lite.js (not present in CreepJS) and identifies their likely sources.

## Summary

| Feature | Source | License | Confidence |
|---------|--------|---------|------------|
| 1. Incognito Detection | [Joe12387/detectIncognito](https://github.com/Joe12387/detectIncognito) | MIT | **100% - Exact copy** |
| 2. Navigator Anomaly Detection | CreepJS lies module (from fork) | Zlib | **High - From fork point** |
| 3. Worker Context Fingerprinting | **NEW - Signifyd original** | N/A | **High - Different from CreepJS** |
| 4. In-App WebView Detection | Industry patterns + original code | N/A | **High - Original implementation** |
| 5. Cookie Monster | Common patterns / Original | N/A | **Low - Generic code** |

---

## 1. Incognito / Private Mode Detection

### Source: [Joe12387/detectIncognito](https://github.com/Joe12387/detectIncognito)

**Confidence: 100% - EXACT COPY**

The code in lite.js explicitly credits this library in comments:

```javascript
/*!
 * detectIncognito v1.4.1
 * https://github.com/Joe12387/detectIncognito
 * MIT License
 * Copyright (c) 2021 - 2025 Joe Rutkowski <Joe@dreggle.com>
 */
```

**Detection Methods (matching exactly):**

| Browser | Method |
|---------|--------|
| Safari | Tests `openDatabase`, `localStorage`, storage quota |
| Chrome | `webkitTemporaryStorage.queryUsageAndQuota()` compares quota vs heap size |
| Firefox | Tests `serviceWorker` availability |
| IE | Tests `indexedDB` availability |

**Key identifying code pattern:**
```javascript
function getEngineIdentifier() {
    let f = 0;
    const h = parseInt("-1");
    try { h.toFixed(h); } catch (m) { f = m.message.length; }
    return f; // Returns 44 (Safari), 51 (Chrome), 25 (Firefox)
}
```

**License Compliance:** MIT License requires attribution, which Signifyd includes in comments.

---

## 2. Navigator Anomaly Detection

### Source: [CreepJS lies module](https://github.com/AbrahamJuliot/creepjs/blob/master/src/lies/index.ts) (from fork point)

**Confidence: HIGH - Included from fork point (May 2023)**

This code **existed in CreepJS at the fork point** and was included when Signifyd forked. The `hasKnownToString` function checking for `[native code]` patterns was present in commit c17490f:

```javascript
// CreepJS pattern (present at fork point)
function hasKnownToString(name) {
    return {
        [`function ${name}() { [native code] }`]: true,
        [`function get ${name}() { [native code] }`]: true,
        // ...
    }
}
```

lite.js also uses a simplified version in its worker code:

```javascript
// lite.js additional simplified check
const str = desc.get?.toString() || desc.set?.toString();
return str && !str.includes('[native code]');
```

**Key Finding:** The core `[native code]` detection came from the CreepJS fork. Signifyd added a simplified version for use in their worker context code.

**This technique is well-documented publicly:**
- [JavaScript tampering – detection and stealth](https://adtechmadness.wordpress.com/2019/03/23/javascript-tampering-detection-and-stealth/) (2019)
- Common knowledge in fingerprinting community

---

## 3. Worker Context Fingerprinting

### Source: **NEW - Signifyd Original Code**

**Confidence: HIGH - This is NOT from CreepJS or any identified public source**

Extensive searching confirmed that while the **concept** of using workers to detect spoofing is well-known, lite.js's specific **implementation architecture** does not match any identified public source code.

**Public knowledge of the technique:**
- [puppeteer-extra issue #451](https://github.com/berstend/puppeteer-extra/issues/451) - Documents that Web Workers leak true `navigator.platform` even when spoofed
- [CreepJS worker tests](https://abrahamjuliot.github.io/creepjs/tests/workers.html) - CreepJS has worker comparison tests
- [Castle.io blog](https://blog.castle.io/deep-dive-how-navigator-devicememory-can-be-used-for-fingerprinting-and-bot-detection/) - Discusses worker-based spoofing detection
- [niespodd/browser-fingerprinting](https://github.com/niespodd/browser-fingerprinting) - Documents fingerprinting techniques

**CreepJS approach (at fork point):**
```javascript
// CreepJS compares specific properties and flags as "lies":
if (platform != navigator.platform) {
  documentLie('Navigator.platform', workerScopeMatchLie)
}
if (userAgent != navigator.userAgent) {
  documentLie('Navigator.userAgent', workerScopeMatchLie)
}
```

**lite.js approach (NEW architecture):**
- Contains a **completely separate inline worker script** (~4KB of code as a string)
- Runs a **full profile collection** in each worker context (main, web worker, shared worker)
- Includes its **own anomaly detection** within workers
- Collects: navigator properties, Intl data, permissions, Bluetooth, WebGL, userAgentData
- Returns structured profiles for external comparison
- Does NOT use CreepJS's `documentLie()` approach

**Key Evidence:**
- lite.js has NO reference to `workerScopeMatchLie` (CreepJS pattern)
- lite.js worker code includes `SharedWorkerGlobalScope` detection with full profile collection
- The inline worker string is entirely custom code, not from CreepJS
- No public fingerprinting library found with matching architecture

**Search Results Summary:**
| Source Searched | Relevant? | Matching Code? |
|-----------------|-----------|----------------|
| puppeteer-extra issues | Yes - documents the vulnerability | No - just bug reports |
| CreepJS tests/workers.html | Yes - tests similar concept | No - uses documentLie() |
| niespodd/browser-fingerprinting | Yes - documents techniques | No - no inline worker code |
| Castle.io, Browserless blogs | Yes - explain the technique | No - documentation only |
| DFPM issues | Yes - mentions worker fingerprinting | No - different approach |

**Verdict:** Signifyd wrote new worker fingerprinting code that takes a different architectural approach than any identified public source. The concept of using workers to detect spoofing is well-known, but the specific implementation (inline worker script with full profile collection and independent anomaly detection) appears to be original Signifyd code.

---

## 4. In-App WebView Detection

### Source: Common patterns - Industry-standard user-agent signatures

**Confidence: HIGH - Industry-standard patterns, different architecture**

The patterns used are **industry-standard** user-agent signatures documented by browser vendors, but lite.js uses a **different code architecture** than existing libraries.

### Comparison with Public Libraries

**f2etw/detect-inapp** (most similar library):
```javascript
// Uses regex dictionary + class-based approach
const BROWSER = {
  messenger: /\bFB[\w_]+\/(Messenger|MESSENGER)/,
  facebook: /\bFB[\w_]+\//,
  instagram: /\bInstagram/i,
  twitter: /\bTwitter/i,
};
// WebView detection uses joined regex rules
const rules = ['WebView', '(iPhone|iPod|iPad)(?!.*Safari\/)', 'Android.*(wv)'];
const regex = new RegExp(`(${rules.join('|')})`, 'ig');
return Boolean(ua.match(regex));
```

**atomantic/is-ua-webview**:
```javascript
// Uses array of rules joined into single regex
module.exports = [
  'WebView',
  '(iPhone|iPod|iPad)(?!.*Safari)',
  'Android.*(;\\s+wv|Version/\\d.\\d\\s+Chrome/\\d+(\\.0){3})',
  'Linux; U; Android'
]
```

**lite.js approach** (Signifyd - from actual deobfuscated code):
```javascript
// iOS browser detection (line 3166):
/CriOS/.test(ua) ? "Chrome" : /FxiOS/.test(ua) ? "Firefox" :
/EdgiOS/.test(ua) ? "Edge" : /OPiOS/.test(ua) ? "Opera" :
/DuckDuckGo/.test(ua) ? "DuckDuckGo" : /YaBrowser/.test(ua) ? "Yandex" : "Safari"

// In-app WebView detection (line 4510):
const inAppWebView = /\binstagram\b/.test(ua) ||
                     /\bfbav|fban|fb_iab\b/.test(ua) ||   // Facebook
                     /\btiktok\b/.test(ua) ||              // NOT in detect-inapp!
                     /\bsnapchat\b/.test(ua) ||            // NOT in detect-inapp!
                     /* additional Android conditions */;
```

### Public Libraries Analyzed

| Library | Architecture | Patterns Match? |
|---------|--------------|-----------------|
| [f2etw/detect-inapp](https://github.com/f2etw/detect-inapp) | Class + regex dictionary | Core patterns similar, **missing TikTok/Snapchat** |
| [atomantic/is-ua-webview](https://github.com/atomantic/is-ua-webview) | Array of rules | Generic WebView only, **no app-specific patterns** |
| [dvlden/is-webview](https://github.com/dvlden/is-webview) | Single regex | Simpler, fewer patterns |
| [fostyfost gist](https://gist.github.com/fostyfost/0591c79f4cd7ca26e5941a53fd4bf1a4) | Array of rules | Generic WebView only |
| [luizcieslak/am-i-inapp-browser](https://github.com/luizcieslak/am-i-inapp-browser) | Uses f2etw/detect-inapp | Same as f2etw |

### Key Difference: lite.js includes TikTok and Snapchat

**f2etw/detect-inapp browser list:**
- messenger, facebook, twitter, line, wechat, puffin, miui, instagram, chrome, safari, ie, firefox

**lite.js detected apps:**
- instagram, facebook (fbav/fban/fb_iab), **tiktok**, **snapchat**

lite.js detects TikTok and Snapchat in-app browsers which are NOT in the most popular detect-inapp library. This suggests Signifyd either:
1. Added these patterns themselves (TikTok/Snapchat are newer apps)
2. Used a different/newer source that includes these apps

### Pattern Origins

The individual patterns are **well-documented industry standards**:
- `CriOS`, `FxiOS`, `EdgiOS` - iOS browser identifiers (Apple/vendor documentation)
- `FBAN`, `FBAV` - Facebook app identifiers (documented in [Medium articles](https://medium.com/geekculture/how-to-detect-if-a-user-is-using-the-facebook-in-app-browser-41ccc2c5deca))
- `; wv)` - Android WebView marker ([Chrome documentation](https://developer.chrome.com/docs/multidevice/user-agent/#webview_user_agent))
- `Instagram`, `Twitter` - App identifiers in user-agent strings

### Verdict

lite.js WebView detection uses **industry-standard patterns** but with **notable differences**:

1. **Different architecture** - Cascading if/else vs joined regex (not a direct copy)
2. **Includes TikTok and Snapchat** - Not present in f2etw/detect-inapp or other major libraries
3. **Simpler regex patterns** - Uses `/\binstagram\b/` vs `/\bInstagram/i`

This suggests **Signifyd wrote their own implementation** using documented patterns, adding support for newer apps (TikTok, Snapchat) that older libraries don't detect.

**Confidence: HIGH** - Original Signifyd code using industry-standard patterns, not a copy of any identified library.

**Not in CreepJS:** Confirmed - CreepJS does not include iOS browser variant detection or in-app browser detection.

---

## 5. Cookie Monster - Storage Detection

### Source: Generic/Common patterns, possibly original

**Confidence: LOW - Generic code**

The storage testing code is extremely common and not attributable to any single source:

```javascript
// Standard cookie test - found everywhere
document.cookie = `test=${value}; path=/`;
const read = document.cookie.includes(value);
document.cookie = 'test=; expires=Thu, 01 Jan 1970';

// Standard localStorage test
localStorage.setItem('test', '1');
const works = localStorage.getItem('test') === '1';
localStorage.removeItem('test');
```

**Similar implementations:**
- [Modernizr](https://modernizr.com/) storage detection
- Thousands of implementations across the web
- Browser compatibility testing libraries

**The term "Cookie Monster"** in fingerprinting context appears in academic literature:
- "Cookieless Monster: Exploring the Ecosystem of Web-based Device Fingerprinting" (IEEE S&P 2012)

However, this is a reference to fingerprinting WITHOUT cookies, not cookie testing itself.

---

## Conclusion

### Definite External Sources:
1. **detectIncognito** - 100% copied from Joe12387's MIT-licensed library (properly attributed)

### Derived from CreepJS (from fork point):
2. **Navigator Anomaly Detection** - Included from CreepJS lies module at fork point (May 2023)

### Original Signifyd Code:
3. **Worker Context Fingerprinting** - Genuinely new architecture, not derived from any identified public source

### Original Signifyd Code (using common patterns):
4. **In-App WebView Detection** - Original implementation using industry-standard user-agent patterns + TikTok/Snapchat detection not in major libraries
5. **Cookie Monster** - Standard storage testing code

### License Implications

| Source | License | Attribution Required | Included in lite.js |
|--------|---------|---------------------|---------------------|
| detectIncognito | MIT | Yes | ✅ Yes |
| CreepJS | Zlib | Yes (in altered form) | ❌ No |
| WebView detection | N/A (original) | N/A | N/A |

**Note:** While Signifyd properly attributes detectIncognito, the CreepJS derivation (which forms the bulk of lite.js) has no visible attribution in the production code. The WebView detection appears to be original Signifyd code using industry-standard patterns.
