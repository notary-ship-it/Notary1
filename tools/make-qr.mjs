/**
 * Generates print-ready QR codes for the DMS intake page.
 * Usage: node tools/make-qr.mjs [baseUrl]
 */
import QRCode from 'qrcode';
import { writeFileSync, mkdirSync } from 'node:fs';

const BASE = process.argv[2] || 'https://notary1.vercel.app';

const targets = [
  { slug: 'standdown', label: 'Delaware VA Stand Down',
    url: `${BASE}/?src=qr-standdown&event=${encodeURIComponent('Delaware VA Stand Down')}` },
  { slug: 'general', label: 'General / everyday use', url: `${BASE}/` },
  { slug: 'business', label: 'Business & partner outreach',
    url: `${BASE}/?src=qr-business&event=${encodeURIComponent('Business Partner Intake')}` },
];

mkdirSync('qr', { recursive: true });

// High error correction so the code still scans with a logo over it, a crease,
// or a thumb on the corner of a printed sign.
const opts = { errorCorrectionLevel: 'H', margin: 2, color: { dark: '#0A1F3C', light: '#FFFFFF' } };

for (const t of targets) {
  const svg = await QRCode.toString(t.url, { ...opts, type: 'svg', width: 1200 });
  writeFileSync(`qr/dms-${t.slug}.svg`, svg);
  const png = await QRCode.toBuffer(t.url, { ...opts, width: 1200 });
  writeFileSync(`qr/dms-${t.slug}.png`, png);
  console.log(`qr/dms-${t.slug}.{svg,png}  ->  ${t.url}`);
}
