const fs = require('fs');
const path = require('path');

const files = ['americanexpress.js', 'prada.js', 'xfinity.js'];

for (const file of files) {
  const src = fs.readFileSync(path.join('/tmp/akam', file), 'utf8');

  // Extract the string array: var _=[...];
  const arrMatch = src.match(/var _=\[((?:"[^"]*",?\s*)*)\]/);
  if (!arrMatch) { console.error(`No array found in ${file}`); continue; }

  // Parse the array - eval the hex escape sequences
  const arrStr = '[' + arrMatch[1] + ']';
  const strings = eval(arrStr);

  // Get everything after the array declaration
  let code = src.slice(src.indexOf('];') + 2);
  // Remove trailing })()
  if (code.endsWith('})()')) code = code.slice(0, -4);

  // Replace _[N] with the actual decoded string
  // Use a function to handle nested replacements
  let deobfuscated = code.replace(/_\[(\d+)\]/g, (match, idx) => {
    const i = parseInt(idx);
    if (i >= 0 && i < strings.length) {
      const s = strings[i];
      // If it looks like an identifier, return as-is for readability
      return JSON.stringify(s);
    }
    return match;
  });

  // Pretty print with basic indentation
  let indent = 0;
  let pretty = '';
  let inString = false;
  let stringChar = '';
  let escaped = false;

  for (let i = 0; i < deobfuscated.length; i++) {
    const ch = deobfuscated[i];

    if (escaped) { pretty += ch; escaped = false; continue; }
    if (ch === '\\') { pretty += ch; escaped = true; continue; }

    if (inString) {
      pretty += ch;
      if (ch === stringChar) inString = false;
      continue;
    }

    if (ch === '"' || ch === "'") {
      pretty += ch;
      inString = true;
      stringChar = ch;
      continue;
    }

    if (ch === '{') {
      indent++;
      pretty += ' {\n' + '  '.repeat(indent);
      continue;
    }
    if (ch === '}') {
      indent = Math.max(0, indent - 1);
      pretty += '\n' + '  '.repeat(indent) + '}';
      continue;
    }
    if (ch === ';') {
      pretty += ';\n' + '  '.repeat(indent);
      continue;
    }

    pretty += ch;
  }

  const outFile = file.replace('.js', '.deob.js');
  fs.writeFileSync(path.join('/tmp/akam', outFile), pretty);

  // Also output the unique per-site values for comparison
  const siteSpecific = [];
  for (let i = 0; i < strings.length; i++) {
    if (/^[0-9a-f]{32}$/.test(strings[i])) {
      siteSpecific.push({ index: i, value: strings[i], type: 'hash32' });
    }
    if (/^\d{3}$/.test(strings[i])) {
      siteSpecific.push({ index: i, value: strings[i], type: 'numeric_id' });
    }
  }
  console.log(`\n=== ${file} ===`);
  console.log(`  String count: ${strings.length}`);
  console.log(`  Site-specific values:`);
  siteSpecific.forEach(s => console.log(`    [${s.index}] ${s.type}: ${s.value}`));
}
