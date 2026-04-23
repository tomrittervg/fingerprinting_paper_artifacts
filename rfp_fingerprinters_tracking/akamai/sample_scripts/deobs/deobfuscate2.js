const fs = require('fs');
const path = require('path');

const files = ['americanexpress.deob.js', 'prada.deob.js', 'xfinity.deob.js'];

for (const file of files) {
  let code = fs.readFileSync(path.join('/tmp/akam', file), 'utf8');

  // 1. Convert bracket notation to dot notation for valid identifiers
  //    Only when preceded by a word char or ) (i.e. it's a property access, not an array literal)
  //    Run in a loop to handle chained brackets: ["a"]["b"]["c"]
  let prev;
  do {
    prev = code;
    code = code.replace(/([a-zA-Z0-9_$)\]])\["([a-zA-Z_$][a-zA-Z0-9_$]*)"\]/g, '$1.$2');
  } while (code !== prev);

  // 2. Replace void 0 with undefined
  code = code.replace(/void 0/g, 'undefined');

  // 3. Replace !0 with true and !1 with false
  code = code.replace(/(?<![a-zA-Z0-9_$"])!0(?![a-zA-Z0-9_$])/g, 'true');
  code = code.replace(/(?<![a-zA-Z0-9_$"])!1(?![a-zA-Z0-9_$])/g, 'false');

  // 4. Replace known global aliases with their real names (only as property access base)
  //    b.X -> window.X, u.X -> document.X, etc.
  //    We do targeted replacements for known property accesses.

  // b -> window
  const windowProps = [
    'XMLHttpRequest', 'ActiveXObject', 'setTimeout', 'location', 'performance',
    'Image', 'XDomainRequest', 'createPopup', 'removeEventListener', 'globalStorage',
    'openDatabase', 'indexedDB', 'attachEvent', 'dispatchEvent', 'addBehavior',
    'addEventListener', 'detachEvent', 'fireEvent', 'MutationObserver',
    'HTMLMenuItemElement', 'Int8Array', 'postMessage', 'querySelector',
    'innerWidth', 'outerWidth', 'screenX', 'pageXOffset', 'innerHeight',
    'outerHeight', 'screenY', 'pageYOffset', 'XPathResult', 'chrome', 'opera',
    'safari', 'StyleMedia', 'external', 'parseInt', 'encodeURIComponent',
    'btoa', 'Date', 'HTMLElement', 'JSON',
    'bazadebezolkohpepadr', 'ApplePaySession',
  ];
  for (const prop of windowProps) {
    const re = new RegExp('\\bb\\.' + prop.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g');
    code = code.replace(re, 'window.' + prop);
  }
  // b[varName] patterns -> window[varName]
  code = code.replace(/\bb\[([a-z])\]/g, 'window[$1]');

  // u -> document
  const docProps = [
    'createElement', 'body', 'documentElement', 'getElementsByTagName',
    'addEventListener', 'attachEvent', 'getElementsByClassName', 'querySelector',
    'images', 'compatMode', 'documentMode', 'all', 'currentScript',
    'XPathResult',
  ];
  for (const prop of docProps) {
    const re = new RegExp('\\bu\\.' + prop.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g');
    code = code.replace(re, 'document.' + prop);
  }

  // l -> navigator (only as base of property access, not as local param)
  const navProps = ['plugins', 'userAgent', 'mimeTypes', 'getBattery', 'permissions'];
  for (const prop of navProps) {
    const re = new RegExp('\\bl\\.' + prop.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g');
    code = code.replace(re, 'navigator.' + prop);
  }

  // s -> screen
  const screenProps = ['availWidth', 'availHeight', 'width', 'height', 'colorDepth', 'pixelDepth'];
  for (const prop of screenProps) {
    const re = new RegExp('\\bs\\.' + prop.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g');
    code = code.replace(re, 'screen.' + prop);
  }

  // d.stringify -> JSON.stringify
  code = code.replace(/\bd\.stringify\b/g, 'JSON.stringify');

  // 5. Now re-prettify with proper indentation
  // First, normalize whitespace
  code = code.replace(/\s+/g, ' ').trim();

  let pretty = '';
  let indent = 0;
  let inString = false;
  let stringChar = '';
  let inRegex = false;
  let inCharClass = false; // inside [...] in regex
  let escaped = false;
  // Track last significant (non-space) char for regex detection
  let lastSig = '';

  for (let i = 0; i < code.length; i++) {
    const ch = code[i];

    if (escaped) { pretty += ch; escaped = false; continue; }
    if (ch === '\\') { pretty += ch; escaped = true; continue; }

    // Inside a regex literal - scan through until closing /
    if (inRegex) {
      pretty += ch;
      if (ch === '[') inCharClass = true;
      else if (ch === ']') inCharClass = false;
      else if (ch === '/' && !inCharClass) {
        inRegex = false;
        // consume flags
        while (i + 1 < code.length && /[gimsuy]/.test(code[i + 1])) {
          i++;
          pretty += code[i];
        }
        lastSig = '/';
      }
      continue;
    }

    // Inside a string literal
    if (inString) {
      pretty += ch;
      if (ch === stringChar) { inString = false; lastSig = ch; }
      continue;
    }

    // Start of string literal
    if (ch === '"' || ch === "'") {
      pretty += ch;
      inString = true;
      stringChar = ch;
      continue;
    }

    // Detect start of regex literal: / after operator, keyword, or start
    if (ch === '/' && '=(!&|,;:?[{~^%*/+-'.includes(lastSig) || (ch === '/' && lastSig === '')) {
      // But not // (comment) or /* (comment) - shouldn't appear in minified code, but check
      const nextCh = code[i + 1] || '';
      if (nextCh !== '/' && nextCh !== '*') {
        pretty += ch;
        inRegex = true;
        inCharClass = false;
        continue;
      }
    }

    if (ch === '{') {
      indent++;
      pretty += ' {\n' + '  '.repeat(indent);
      lastSig = '{';
      continue;
    }
    if (ch === '}') {
      indent = Math.max(0, indent - 1);
      pretty += '\n' + '  '.repeat(indent) + '}';
      lastSig = '}';
      continue;
    }
    if (ch === ';') {
      pretty += ';\n' + '  '.repeat(indent);
      lastSig = ';';
      continue;
    }
    // Skip redundant spaces at line start
    if (ch === ' ' && pretty.endsWith('\n' + '  '.repeat(indent))) {
      continue;
    }
    pretty += ch;
    if (ch !== ' ') lastSig = ch;
  }

  // 6. Fix missing spaces: "function<name>(" -> "function <name>("
  pretty = pretty.replace(/\bfunction([a-zA-Z_$])/g, 'function $1');
  // Fix "var<name>" -> "var <name>"
  pretty = pretty.replace(/\bvar([a-zA-Z_$])/g, 'var $1');
  // Fix "return!" -> "return !"  and similar
  pretty = pretty.replace(/\breturn([!"'\[({a-zA-Z0-9_$+\-~])/g, 'return $1');
  // Fix "typeof<name>" -> "typeof <name>"
  pretty = pretty.replace(/\btypeof([a-zA-Z_$])/g, 'typeof $1');
  // Fix "new<name>" -> "new <name>"
  pretty = pretty.replace(/\bnew([a-zA-Z_$])/g, 'new $1');
  // Fix "throw new" already ok, but "throw<name>"
  pretty = pretty.replace(/\bthrow([a-zA-Z_$])/g, 'throw $1');
  // Fix "case<value>" -> "case <value>"
  pretty = pretty.replace(/\bcase([0-9"'])/g, 'case $1');
  // Fix "in<name>" when it's the 'in' operator
  // This is tricky; skip for now

  // 7. Add blank lines between top-level function declarations for readability
  pretty = pretty.replace(/\n(function )/g, '\n\n$1');

  // 8. Clean up the alias declarations at the bottom
  pretty = pretty.replace(/,b=window,u=window\.document,l=window\.navigator,s=window\.screen/g, '');
  pretty = pretty.replace(/,b=window,u=b\.document,l=b\.navigator,s=b\.screen/g, '');

  // 9. Add header comment
  const header = `// Akamai Bot Manager fingerprinting script (deobfuscated)
// Global aliases originally used:
//   b = window, u = document, l = navigator, s = screen
//   d = JSON (with polyfill), c = SHA-1 hasher, f = btoa polyfill
//   h = hash memoization cache
//   v = window.bazadebezolkohpepadr (site-specific XOR key)
//   g, p, O = site-specific 32-char hex hashes
//

`;

  const outFile = file.replace('.deob.js', '.deob2.js');
  fs.writeFileSync(path.join('/tmp/akam', outFile), header + pretty);
  console.log(`Wrote ${outFile} (${(header + pretty).length} bytes)`);
}
