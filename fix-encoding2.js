const fs = require('fs');
const path = require('path');
const dir = 'C:/Users/admin/.openclaw/workspace/modelhub';

const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));

// Map of garbled chars (from UTF-8 double-encoding) to correct chars
const replacements = {
  // These are common double-encode artifacts when a UTF-8 file was 
  // read as Windows-1252 and then saved back as UTF-8
};

files.forEach(f => {
  const fp = path.join(dir, f);
  let c = fs.readFileSync(fp, 'utf8');
  const orig = c;

  // Known replacements for specific garbled fragments
  const re = [
    // Em-dash and dashes
    [/—(?=[a-zA-Z])/g, '— '],
    [/—(?=[\<])/g, '—'],
    // Fix arrow tag
    [/\u2192\//g, '\u2192<\/'],
    // Any remaining garbled quote clusters
    [/[^\x20-\x7E\xC0-\u024F\u0370-\u03FF\u0400-\u04FF\u2000-\u2FFF\u3000-\u33FF\u4E00-\u9FFF\uAC00-\uD7AF\uF900-\uFAFF\uFE00-\uFE0F\uE000-\uF8FF\u2600-\u27BF\u1F000-\u1FFFF\u200D\uFE0F\u20E3\u203C\u2049\u2122\u2139\u2194-\u2199\u21A9\u21AA\u231A\u231B\u2328\u23CF\u23E9-\u23F3\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB\u25FC\u25FD\u25FE\u2600-\u27BF\u2934\u2935\u2B05\u2B06\u2B07\u2B1B\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299]]/g, ''),
  ];

  re.forEach(([pattern, replacement]) => {
    c = c.replace(pattern, replacement);
  });

  // Second pass: fix the garbled emoji hex blocks
  c = c.replace(/馃[\s\S]*?;/g, '');
  c = c.replace(/鈥/g, '—');
  
  // Fix standalone closing tags that got mangled
  c = c.replace(/>([^\s<])/g, '> $1');

  if (c !== orig) {
    fs.writeFileSync(fp, c, 'utf8');
    console.log(fp + ': fixed');
  } else {
    console.log(fp + ': clean');
  }
});
