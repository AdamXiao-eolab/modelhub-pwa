const fs = require('fs');
const path = require('path');
const dir = 'C:/Users/admin/.openclaw/workspace/modelhub';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));
const fixes = {
  '鈥?': "'", '鈥?': "'", '鈥?': '"', '鈥?': '"',
  '漏': '©', '鈫?': '→', '鈼?': '●', '鈽?': '★',
  '鈥檙': "'r", "鈥檚": "'s", "鈥檛": "'t",
  '鈥檒': "'l", "鈥檃": "'a", "鈥檈": "'e", "鈥檓": "'m",
  '鈥攕': "'s", '鈥攁': "'a",
  '鈥?': "'",
};
files.forEach(f => {
  const fp = path.join(dir, f);
  let c = fs.readFileSync(fp, 'utf8');
  const orig = c;
  // Fix emoji garbles specifically from the raw curl output
  c = c.replace(/馃[^^]*?[^鈥攕鈥檙鈥檃鈥檈鈥檛鈥檓鈥榤]/g, '');
  // Manual replacement for known emoji positions
  c = c.replace(/馃攲/g, '🔌');
  c = c.replace(/馃攽/g, '🔑');
  c = c.replace(/馃挸/g, '💳');
  c = c.replace(/馃敀/g, '🔒');
  c = c.replace(/馃搳/g, '📊');
  c = c.replace(/馃殌/g, '🚀');
  c = c.replace(/馃弳/g, '🏆');
  // Apply dictionary
  Object.keys(fixes).forEach(k => {
    c = c.split(k).join(fixes[k]);
  });
  if (c !== orig) {
    fs.writeFileSync(fp, c, 'utf8');
    console.log(f + ': fixed');
  } else {
    console.log(f + ': clean');
  }
});
