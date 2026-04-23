# CreepJS vs Signifyd ClientRects Code Comparison

## Executive Summary

**Conclusion: Signifyd's clientRects fingerprinting code is derived from CreepJS.**

The code is nearly identical in all aspects:
- Same CSS transforms with identical values
- Same element structure (12 rect elements + emoji elements)
- Same element IDs (cRect1-cRect12)
- Same EMOJIS array (91 emoji codepoints)
- Same CSS_FONT_FAMILY list
- Same lie detection methods
- Same hash values for browser detection
- Same return data structure

---

## Detailed Comparison

### 1. CSS Transforms - IDENTICAL

| Element | Transform Value | Match |
|---------|----------------|-------|
| .rect-known | `rotate(45deg)` | ✅ |
| #cRect2 | `skewY(23.1753218deg) rotate3d(10.00099, 90, 0.100000000000009, 60000000000008.00000009deg)` | ✅ |
| #cRect3 | `skewY(-23.1753218deg) scale(1099.0000000099, 1.89) matrix(1.11, 2.0001, -1.0001, 1.009, 150, 94.4)` | ✅ |
| #cRect4 | `matrix(1.11, 2.0001, -1.0001, 1.009, 150, 94.4)` | ✅ |
| #cRect6 | `perspective(12890px) translateZ(101.5px)` | ✅ |
| .domrect-emoji | `scale(1.000999)` | ✅ |

### 2. Element Structure - IDENTICAL

Both create:
- 1 `.rect-known` element (100x100px, rotate 45deg)
- 1 `.rect-ghost` element (0x0px)
- 12 `.rects` elements (#cRect1 through #cRect12)
- Multiple `.domrect-emoji` elements

### 3. Element Styling - IDENTICAL

| Property | CreepJS | Signifyd |
|----------|---------|----------|
| #cRect1 border | `solid 2.715px #F72585` | `solid 2.715px #f72585` |
| #cRect1 padding | `3.98px` | `3.98px` |
| #cRect1 margin-left | `12.12px` | `12.12px` |
| #cRect2 font-size | `30px` | `30px` |
| #cRect2 margin-top | `20px` | `20px` |
| #cRect3 font-size | `45px` | `45px` |
| #cRect3 margin-top | `50px` | `50px` |
| #cRect4 margin-top | `11.1331px` | `11.1331px` |
| #cRect4 margin-left | `12.1212px` | `12.1212px` |
| #cRect4 padding | `4.4545px` | `4.4545px` |
| #cRect4 left | `239.4141px` | `239.4141px` |
| #cRect4 top | `8.5050px` | `8.505px` |
| #cRect5 margin-left | `42.395pt` | `42.395pt` |
| #cRect6 padding | `12px` | `12px` |
| #cRect7 margin-top | `-350.552px` | `-350.552px` |
| #cRect7 margin-left | `0.9099rem` | `0.9099rem` |
| #cRect11/12 size | `10px` | `10px` |
| #cRect11/12 margin-left | `15.0000009099rem` | `15.0000009099rem` |

### 4. EMOJIS Array - IDENTICAL

Both use 91 emoji codepoints in the same order:

```javascript
// First 33 emojis (identical in both)
[128512], [9786], [129333, 8205, 9794, 65039], [9832], [9784], [9895], [8265], [8505],
[127987, 65039, 8205, 9895, 65039], [129394], [9785], [9760], [129489, 8205, 129456],
[129487, 8205, 9794, 65039], [9975], [129489, 8205, 129309, 8205, 129489], [9752],
[9968], [9961], [9972], [9992], [9201], [9928], [9730], [9969], [9731], [9732],
[9976], [9823], [9937], [9000], [9993], [9999],
// ... remaining 58 emojis also identical
```

Note: Signifyd has `[9e3]` which equals `[9000]` - mathematically identical.

### 5. CSS_FONT_FAMILY - IDENTICAL

Both use the same 48-font list starting with:
```
'Segoe Fluent Icons', 'Ink Free', 'Bahnschrift', 'Segoe MDL2 Assets',
'HoloLens MDL2 Assets', 'Leelawadee UI', 'Javanese Text', 'Segoe UI Emoji',
'Aldhabi', 'Gadugi', 'Myanmar Text', 'Nirmala UI', 'Lucida Console',
'Cambria Math', 'Bai Jamjuree', 'Chakra Petch', 'Charmonman', 'Fahkwang',
'K2D', 'Kodchasan', 'KoHo', 'Sarabun', 'Srisakdi', 'Galvji', ...
```

### 6. Engine Detection - IDENTICAL

| Engine | Identifier | CreepJS Variable | Signifyd Variable |
|--------|------------|------------------|-------------------|
| V8 (Blink/Chrome) | 80 | `IS_BLINK` | `ge` |
| SpiderMonkey (Gecko/Firefox) | 58 | `IS_GECKO` | `Se` |
| JavaScriptCore (WebKit/Safari) | 77 | `IS_WEBKIT` | `Le` |

Detection method: Both use `(-1).toString(-1)` error message length + array constructor string manipulation.

### 7. Known Hash Values - IDENTICAL

**For Blink (V8) browsers:**
```javascript
// CreepJS
{ '9d9215cc': true, '47ded322': true, 'd0eceaa8': true }

// Signifyd
{ "9d9215cc": !0, "47ded322": !0, d0eceaa8: !0 }
```

**For Gecko (SpiderMonkey) browsers:**
```javascript
// CreepJS
{ 'e38453f0': true }

// Signifyd
{ e38453f0: !0 }
```

### 8. Lie Detection Methods - IDENTICAL

| Method | Description | CreepJS | Signifyd |
|--------|-------------|---------|----------|
| API Spoof Check | Check if getClientRects/getBoundingClientRect/etc spoofed | ✅ | ✅ |
| Shift Test | Add/remove CSS class, compare top values | ✅ | ✅ |
| Math Consistency | Verify `right - left === width`, etc. | ✅ | ✅ |
| Equal Elements | Compare cRect11 vs cRect12 (should be equal) | ✅ | ✅ |
| Hash Check | Verify .rect-known hash against known values | ✅ | ✅ |
| Ghost Dimensions | Check .rect-ghost has all zeros | ✅ | ✅ |

### 9. Return Data Structure - IDENTICAL

Both return:
```javascript
{
    elementClientRects: [...],      // Array of 12 rect objects
    elementBoundingClientRect: [...], // Array of 12 rect objects
    rangeClientRects: [...],        // Array of 12 rect objects
    rangeBoundingClientRect: [...], // Array of 12 rect objects
    emojiSet: [...],                // Unique emoji dimensions
    domrectSystemSum: number,       // Computed from emoji dimensions
    lied: boolean                   // True if any lie detected
}
```

### 10. DOMRect Normalization - IDENTICAL

Both normalize DOMRect to plain object with same property order:
```javascript
{
    bottom: rect.bottom,
    height: rect.height,
    left: rect.left,
    right: rect.right,
    width: rect.width,
    top: rect.top,
    x: rect.x,
    y: rect.y
}
```

### 11. getBestRect Fallback Logic - IDENTICAL

Both implement the same fallback chain:
1. If `Element.getClientRects` not spoofed → use it
2. Else if `Element.getBoundingClientRect` not spoofed → use it
3. Else if `Range.getClientRects` not spoofed → use Range version
4. Else → use `Range.getBoundingClientRect`

### 12. domrectSystemSum Calculation - IDENTICAL

Both calculate:
```javascript
0.00001 * [...pattern].map(x =>
    x.split(',').reduce((acc, x) => acc += (+x||0), 0)
).reduce((acc, x) => acc += x, 0)
```

---

## Minor Differences

| Aspect | CreepJS | Signifyd | Impact |
|--------|---------|----------|--------|
| Language | TypeScript | JavaScript (minified) | None - same logic |
| Comments | Present | Removed (minification) | None |
| Variable names | Descriptive | Obfuscated | None |
| `9000` notation | `9000` | `9e3` | None - identical value |
| `#cRect4 top` | `8.5050px` | `8.505px` | None - identical value |
| Hex colors | `#F72585` | `#f72585` | None - case insensitive |

---

## Attribution Note in CreepJS

CreepJS includes this comment:
```javascript
// inspired by
// https://privacycheck.sec.lrz.de/active/fp_gcr/fp_getclientrects.html
// https://privacycheck.sec.lrz.de/active/fp_e/fp_emoji.html
```

This indicates CreepJS was inspired by TU Munich's privacy check implementation, which shares some values (like `skewY(23.1753218deg)` and `perspective(12890px)`).

---

## Lineage

```
TU Munich (privacycheck.sec.lrz.de)
         ↓ (inspiration, some values shared)
      CreepJS
         ↓ (direct copy/derivation)
      Signifyd
```

---

## Conclusion

Signifyd's clientRects fingerprinting implementation is **a direct copy or derivation of CreepJS**. The code is identical in:

- All CSS transform values (including highly specific values like `23.1753218deg`)
- All element IDs and structure
- All styling values (borders, margins, paddings, font sizes)
- All 91 emoji codepoints in exact order
- All 48 fonts in the font family list
- All browser engine detection values (80, 58, 77)
- All known hash values for lie detection
- All lie detection methods and logic
- Return data structure

The only differences are cosmetic (minification, variable naming, insignificant formatting).

**This is not coincidental similarity - this is the same codebase.**
