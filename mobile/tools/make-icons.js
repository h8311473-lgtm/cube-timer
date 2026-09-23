/*!
 * 生成 PWA 图标（纯 Node，无依赖）：圆角方形渐变底 + 秒表图形。
 * 用法：node tools/make-icons.js
 */
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

function crc32(buf) {
  let c, crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    c = (crc ^ buf[i]) & 0xff;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}

function writePng(file, w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 4 + 1)] = 0;
    rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
  fs.writeFileSync(file, png);
}

/** 圆角方形覆盖率（4x4 超采样抗锯齿） */
function roundRectCoverage(x, y, size, radius, inset) {
  const x0 = inset, y0 = inset, x1 = size - inset, y1 = size - inset;
  let hit = 0;
  for (let sy = 0; sy < 4; sy++) {
    for (let sx = 0; sx < 4; sx++) {
      const px = x + (sx + 0.5) / 4;
      const py = y + (sy + 0.5) / 4;
      if (px < x0 || px > x1 || py < y0 || py > y1) continue;
      const cx = Math.min(Math.max(px, x0 + radius), x1 - radius);
      const cy = Math.min(Math.max(py, y0 + radius), y1 - radius);
      const dx = px - cx, dy = py - cy;
      if (dx * dx + dy * dy <= radius * radius) hit++;
    }
  }
  return hit / 16;
}

function makeIcon(size) {
  const rgba = Buffer.alloc(size * size * 4);
  const inset = size * 0.06;
  const radius = size * 0.235;
  const cx = size / 2, cy = size * 0.545;
  const ringR = size * 0.245, ringW = size * 0.062;
  const crownW = size * 0.115, crownH = size * 0.075;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      const cov = roundRectCoverage(x, y, size, radius, inset);
      if (cov <= 0) continue;

      // 底色：斜向渐变（柔紫 -> 天蓝）
      const t = (x / size) * 0.55 + (y / size) * 0.45;
      let r = Math.round(124 + (96 - 124) * t);
      let g = Math.round(108 + (176 - 108) * t);
      let b = Math.round(240 + (250 - 240) * t);

      // 秒表圆环
      const dx = x + 0.5 - cx, dy = y + 0.5 - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist <= ringR + ringW / 2 && dist >= ringR - ringW / 2) {
        r = 255; g = 255; b = 255;
      }
      // 顶部按钮
      if (Math.abs(x + 0.5 - cx) <= crownW / 2 &&
          y + 0.5 >= cy - ringR - crownH * 1.15 && y + 0.5 <= cy - ringR - crownH * 0.15) {
        r = 255; g = 255; b = 255;
      }
      // 指针（指向右上）
      const ang = -Math.PI / 3.2;
      const hx = Math.cos(ang), hy = Math.sin(ang);
      const proj = (x + 0.5 - cx) * hx + (y + 0.5 - cy) * hy;
      const perp = Math.abs(-(x + 0.5 - cx) * hy + (y + 0.5 - cy) * hx);
      if (proj > 0 && proj < ringR * 0.72 && perp < size * 0.028) {
        r = 255; g = 255; b = 255;
      }

      rgba[i] = r; rgba[i + 1] = g; rgba[i + 2] = b;
      rgba[i + 3] = Math.round(255 * cov);
    }
  }
  return rgba;
}

const out = path.join(__dirname, '..');
[180, 512].forEach((size) => {
  const file = path.join(out, 'icon-' + size + '.png');
  writePng(file, size, size, makeIcon(size));
  console.log('已生成', file, fs.statSync(file).size + ' 字节');
});
