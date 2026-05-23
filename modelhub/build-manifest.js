const fs = require('fs');
const s192 = fs.readFileSync('C:/Users/admin/.openclaw/workspace/modelhub/icons/icon-192.svg', 'utf8');
const s512 = fs.readFileSync('C:/Users/admin/.openclaw/workspace/modelhub/icons/icon-512.svg', 'utf8');
const b64 = s => Buffer.from(s).toString('base64');
const manifest = {
  name: "ModelHub — China's Best AI Models",
  short_name: 'ModelHub',
  description: "Access China's best AI models through a single OpenAI-compatible API at globally competitive prices.",
  start_url: '/index.html',
  display: 'standalone',
  background_color: '#05050a',
  theme_color: '#7c3aed',
  orientation: 'portrait',
  icons: [
    { src: 'data:image/svg+xml;base64,' + b64(s192), sizes: '192x192', type: 'image/svg+xml' },
    { src: 'data:image/svg+xml;base64,' + b64(s512), sizes: '512x512', type: 'image/svg+xml' }
  ]
};
fs.writeFileSync('C:/Users/admin/.openclaw/workspace/modelhub/manifest.json', JSON.stringify(manifest, null, 2), 'utf8');
console.log('OK');
