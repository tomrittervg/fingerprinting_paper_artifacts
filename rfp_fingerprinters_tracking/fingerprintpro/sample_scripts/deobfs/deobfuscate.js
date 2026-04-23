#!/usr/bin/env node
// Deobfuscator for FingerprintJS Pro v3.12.6 minified scripts
// Transforms: pretty-print, void 0 -> undefined, !0 -> true, !1 -> false,
//             bracket-to-dot notation, strip /*#__PURE__*/ annotations

const fs = require("fs");

const inputFile = process.argv[2];
const outputFile = process.argv[3];

if (!inputFile || !outputFile) {
  console.error("Usage: node deobfuscate.js <input.js> <output.js>");
  process.exit(1);
}

let code = fs.readFileSync(inputFile, "utf8");

// === Pass 1: Simple text transforms (before pretty-print) ===

// void 0 -> undefined
code = code.replace(/\bvoid 0\b/g, "undefined");

// !0 -> true, !1 -> false (but not inside strings - handled by doing it on raw code
// where these patterns are unambiguous in minified JS)
code = code.replace(/!0\b/g, "true");
code = code.replace(/!1\b/g, "false");

// Strip /*#__PURE__*/ annotations (Terser/Rollup tree-shaking hints)
code = code.replace(/\/\*#__PURE__\*\//g, "");

// Bracket-to-dot notation: obj["property"] -> obj.property
// Only for valid identifier property names, preceded by a word char or ) or ]
function bracketToDot(src) {
  let prev;
  do {
    prev = src;
    src = src.replace(
      /([a-zA-Z0-9_$)\]])\["([a-zA-Z_$][a-zA-Z0-9_$]*)"\]/g,
      "$1.$2"
    );
    // Also handle single-quoted
    src = src.replace(
      /([a-zA-Z0-9_$)\]])\['([a-zA-Z_$][a-zA-Z0-9_$]*)'\]/g,
      "$1.$2"
    );
  } while (src !== prev);
  return src;
}

code = bracketToDot(code);

// === Pass 2: Pretty-print with proper indentation ===
// Handles strings (single, double, backtick/template), regex literals, comments

function prettyPrint(src) {
  const out = [];
  let indent = 0;
  let i = 0;
  const len = src.length;
  let lineStart = true;
  let lastNonSpace = "";

  function pushIndent() {
    out.push("\n");
    out.push("  ".repeat(indent));
    lineStart = true;
  }

  function pushChar(ch) {
    if (lineStart && ch !== "\n" && ch !== " ") lineStart = false;
    out.push(ch);
    if (ch.trim()) lastNonSpace = ch;
  }

  while (i < len) {
    const ch = src[i];

    // === Skip strings ===
    if (ch === '"' || ch === "'") {
      const quote = ch;
      let str = ch;
      i++;
      while (i < len && src[i] !== quote) {
        if (src[i] === "\\") {
          str += src[i] + (src[i + 1] || "");
          i += 2;
        } else {
          str += src[i];
          i++;
        }
      }
      if (i < len) str += src[i++]; // closing quote
      pushChar(str);
      continue;
    }

    // === Template literals ===
    if (ch === "`") {
      let str = ch;
      i++;
      let depth = 0;
      while (i < len) {
        if (src[i] === "\\" && depth === 0) {
          str += src[i] + (src[i + 1] || "");
          i += 2;
          continue;
        }
        if (src[i] === "$" && src[i + 1] === "{" && depth === 0) {
          str += "${";
          i += 2;
          depth++;
          continue;
        }
        if (depth > 0) {
          if (src[i] === "{") depth++;
          else if (src[i] === "}") {
            depth--;
            if (depth === 0) {
              str += "}";
              i++;
              continue;
            }
          }
          str += src[i];
          i++;
          continue;
        }
        if (src[i] === "`") {
          str += "`";
          i++;
          break;
        }
        str += src[i];
        i++;
      }
      pushChar(str);
      continue;
    }

    // === Regex literals ===
    if (ch === "/") {
      // Check if this is a regex (not division)
      // Regex follows: ( , ; = [ ! & | ? : ~ ^ { } + - * / % < > newline return
      // or keywords: return, typeof, instanceof, in, delete, void, throw, new, case
      const canBeRegex = !lastNonSpace ||
        "(,;=[!&|?:~^{}+-*/%<>\n".includes(lastNonSpace) ||
        /\b(return|typeof|instanceof|in|delete|void|throw|new|case)\s*$/.test(
          out.slice(-10).join("")
        );

      if (canBeRegex && src[i + 1] !== "/" && src[i + 1] !== "*") {
        // Regex literal
        let regex = ch;
        i++;
        let inCharClass = false;
        while (i < len) {
          if (src[i] === "\\") {
            regex += src[i] + (src[i + 1] || "");
            i += 2;
            continue;
          }
          if (src[i] === "[") inCharClass = true;
          else if (src[i] === "]") inCharClass = false;
          else if (src[i] === "/" && !inCharClass) {
            regex += src[i];
            i++;
            // Consume flags
            while (i < len && /[gimsuy]/.test(src[i])) {
              regex += src[i];
              i++;
            }
            break;
          }
          regex += src[i];
          i++;
        }
        pushChar(regex);
        continue;
      }

      // Line comment
      if (src[i + 1] === "/") {
        let comment = "";
        while (i < len && src[i] !== "\n") {
          comment += src[i];
          i++;
        }
        pushChar(comment);
        continue;
      }

      // Block comment
      if (src[i + 1] === "*") {
        let comment = "/*";
        i += 2;
        while (i < len && !(src[i] === "*" && src[i + 1] === "/")) {
          comment += src[i];
          i++;
        }
        if (i < len) {
          comment += "*/";
          i += 2;
        }
        pushChar(comment);
        continue;
      }

      // Division operator
      pushChar(ch);
      i++;
      continue;
    }

    // === Structural characters ===
    if (ch === "{") {
      pushChar(" {");
      indent++;
      pushIndent();
      i++;
      continue;
    }

    if (ch === "}") {
      indent = Math.max(0, indent - 1);
      pushIndent();
      pushChar("}");
      // Check what follows: else, catch, finally, while (do-while), comma, semicolon, )
      let peek = i + 1;
      while (peek < len && src[peek] === " ") peek++;
      if (peek < len) {
        const rest = src.substring(peek);
        if (
          rest.startsWith("else") ||
          rest.startsWith("catch") ||
          rest.startsWith("finally") ||
          rest.startsWith("while")
        ) {
          pushChar(" ");
        } else if (src[peek] === "," || src[peek] === ")" || src[peek] === "]") {
          // don't add newline
        } else if (src[peek] === ";") {
          // don't add newline before semicolon
        } else {
          pushIndent();
        }
      }
      i++;
      continue;
    }

    if (ch === ";") {
      pushChar(";");
      // Newline after semicolon, unless inside a for(...) header
      // Simple heuristic: check if we're likely in a for() by scanning back
      let peek = i + 1;
      while (peek < len && src[peek] === " ") peek++;
      if (peek < len && src[peek] !== "}" && src[peek] !== ")") {
        // Check if this semicolon is inside a for() by counting parens
        // Look backwards for unmatched (
        let parenDepth = 0;
        let inFor = false;
        for (let j = out.length - 1; j >= 0 && j >= out.length - 200; j--) {
          const c = out[j];
          if (c === ")") parenDepth++;
          else if (c === "(") {
            parenDepth--;
            if (parenDepth < 0) {
              // Found unmatched open paren - check if preceded by "for"
              const prior = out.slice(Math.max(0, j - 5), j).join("").trim();
              if (prior.endsWith("for")) inFor = true;
              break;
            }
          }
        }
        if (!inFor) {
          pushIndent();
        }
      }
      i++;
      continue;
    }

    // Newlines in source - preserve but re-indent
    if (ch === "\n") {
      pushIndent();
      i++;
      continue;
    }

    // Regular character
    pushChar(ch);
    i++;
  }

  return out.join("");
}

code = prettyPrint(code);

// === Pass 3: Post-processing cleanup ===

// Fix keyword spacing: "functionX(" -> "function X("
code = code.replace(/\bfunction([a-zA-Z_$])/g, "function $1");
code = code.replace(/\breturn([a-zA-Z_$({[!"'`+-])/g, "return $1");
code = code.replace(/\btypeof([a-zA-Z_$("'])/g, "typeof $1");
code = code.replace(/\bnew([a-zA-Z_$])/g, "new $1");
code = code.replace(/\bthrow([a-zA-Z_$"'])/g, "throw $1");
code = code.replace(/\bcase([a-zA-Z_$"'])/g, "case $1");
code = code.replace(/\bdelete([a-zA-Z_$])/g, "delete $1");
code = code.replace(/\bconst([a-zA-Z_$])/g, "const $1");
code = code.replace(/\blet([a-zA-Z_$])/g, "let $1");
code = code.replace(/\bvar([a-zA-Z_$])/g, "var $1");
code = code.replace(/\bawait([a-zA-Z_$])/g, "await $1");
code = code.replace(/\byield([a-zA-Z_$*])/g, "yield $1");
code = code.replace(/\bextends([a-zA-Z_$])/g, "extends $1");
code = code.replace(/\bimport([a-zA-Z_${])/g, "import $1");
code = code.replace(/\bexport([a-zA-Z_{])/g, "export $1");
code = code.replace(/\binstanceof([a-zA-Z_$])/g, "instanceof $1");
code = code.replace(/\belse if\b/g, "else if");

// Remove trailing whitespace on each line
code = code.replace(/[ \t]+$/gm, "");

// Collapse multiple blank lines into one
code = code.replace(/\n{3,}/g, "\n\n");

// Trim leading/trailing whitespace
code = code.trim() + "\n";

fs.writeFileSync(outputFile, code, "utf8");

const lines = code.split("\n").length;
console.log(`Wrote ${outputFile} (${code.length} bytes, ${lines} lines)`);
