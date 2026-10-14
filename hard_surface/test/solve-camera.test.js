import test from 'node:test';
import assert from 'node:assert/strict';
import zlib from 'node:zlib';
import {
  decodePng,
  buildMask,
  solveFromMask,
  anglesFromSlopes,
} from '../scripts/solve-camera.mjs';

const DEG = Math.PI / 180;

// --- research 04:D projection ------------------------------------------------
// X = (cos phi, -sin phi * sin theta)
// Z = (-sin phi, -cos phi * sin theta)
// Y = (0, cos theta)                        (screen-up positive)
function project([wx, wy, wz], theta, phi) {
  const sx = Math.cos(phi) * wx - Math.sin(phi) * wz;
  const sy = -Math.sin(phi) * Math.sin(theta) * wx
    + Math.cos(theta) * wy
    - Math.cos(phi) * Math.sin(theta) * wz;
  return [sx, sy];
}

/** Rasterise the convex hull of a set of image-space points into an RGBA buffer. */
function rasteriseHull(pts, width, height) {
  const hull = convexHull(pts);
  const data = Buffer.alloc(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    data[i * 4] = 255; data[i * 4 + 1] = 255; data[i * 4 + 2] = 255; data[i * 4 + 3] = 255;
  }
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (!pointInPoly(x + 0.5, y + 0.5, hull)) continue;
      const i = (y * width + x) * 4;
      data[i] = 40; data[i + 1] = 60; data[i + 2] = 90; data[i + 3] = 255;
    }
  }
  return { width, height, channels: 4, data };
}

function convexHull(pts) {
  const p = [...pts].sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [];
  for (const q of p) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop();
    lower.push(q);
  }
  const upper = [];
  for (let i = p.length - 1; i >= 0; i--) {
    const q = p[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop();
    upper.push(q);
  }
  lower.pop(); upper.pop();
  return lower.concat(upper);
}

function pointInPoly(x, y, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** Render an axis-aligned box at (theta, phi) into a white RGBA image. */
function renderBox({ theta_deg, phi_deg, size = 512, scale = 90, dims = [1, 1.2, 1] }) {
  const theta = theta_deg * DEG, phi = phi_deg * DEG;
  const [dx, dy, dz] = dims;
  const corners = [];
  for (const sx of [-dx / 2, dx / 2]) {
    for (const sy of [0, dy]) {
      for (const sz of [-dz / 2, dz / 2]) corners.push([sx, sy, sz]);
    }
  }
  const proj = corners.map((c) => project(c, theta, phi));
  const cy = proj.reduce((s, p) => s + p[1], 0) / proj.length;
  const pts = proj.map(([x, y]) => [size / 2 + x * scale, size / 2 - (y - cy) * scale]);
  return rasteriseHull(pts, size, size);
}

// --- tests -------------------------------------------------------------------

test('anglesFromSlopes: 2:1 game-iso slopes give 30/45', () => {
  const a = anglesFromSlopes(0.5, 0.5);
  assert.ok(Math.abs(a.theta_deg - 30) < 1e-9, `theta ${a.theta_deg}`);
  assert.ok(Math.abs(a.phiA_deg - 45) < 1e-9, `phi ${a.phiA_deg}`);
});

test('anglesFromSlopes: true-iso slopes give 35.264/45', () => {
  const m = Math.tan(30 * DEG);
  const a = anglesFromSlopes(m, m);
  assert.ok(Math.abs(a.theta_deg - 35.2644) < 1e-3, `theta ${a.theta_deg}`);
  assert.ok(Math.abs(a.phiA_deg - 45) < 1e-9, `phi ${a.phiA_deg}`);
});

test('solveFromMask recovers theta=30 phi=45 from a synthetic box within 1 deg', () => {
  const img = renderBox({ theta_deg: 30, phi_deg: 45 });
  const maskObj = buildMask(img);
  const r = solveFromMask(maskObj, { threshold: 1.5 });
  assert.ok(Math.abs(r.angles.theta_deg - 30) <= 1, `theta ${r.angles.theta_deg}`);
  const phi = Math.min(r.angles.phiA_deg, r.angles.phiB_deg);
  assert.ok(Math.abs(phi - 45) <= 1, `phi ${phi}`);
  assert.ok(r.residual_px < 1.5, `residual ${r.residual_px}`);
});

test('solveFromMask recovers a non-symmetric camera (theta=35, phi=33) within 1 deg', () => {
  const img = renderBox({ theta_deg: 35, phi_deg: 33, size: 640, scale: 120 });
  const maskObj = buildMask(img);
  const r = solveFromMask(maskObj, { threshold: 1.5 });
  assert.ok(Math.abs(r.angles.theta_deg - 35) <= 1, `theta ${r.angles.theta_deg}`);
  const phi = [r.angles.phiA_deg, r.angles.phiB_deg]
    .filter((p) => p <= 45 + 1e-9).sort((a, b) => a - b)[0];
  assert.ok(Math.abs(phi - 33) <= 1, `phi ${phi}`);
});

test('synthetic box has vertical silhouette edges (tilt ~0)', () => {
  const img = renderBox({ theta_deg: 30, phi_deg: 45 });
  const r = solveFromMask(buildMask(img), { threshold: 1.5 });
  assert.ok(r.vertical.max_tilt_deg !== null, 'expected at least one vertical run');
  assert.ok(Math.abs(r.vertical.max_tilt_deg) < 1.5, `tilt ${r.vertical.max_tilt_deg}`);
});

test('decodePng round-trips an RGB image exercising all five filter types', () => {
  const width = 6, height = 5, ch = 3;
  const stride = width * ch;
  const pixels = Buffer.alloc(stride * height);
  for (let i = 0; i < pixels.length; i++) pixels[i] = (i * 37 + 11) & 0xff;

  // Re-encode with filter type = row index (0..4), applying the filter forward.
  const raw = Buffer.alloc((stride + 1) * height);
  let p = 0;
  for (let y = 0; y < height; y++) {
    const ft = y % 5;
    raw[p++] = ft;
    const cur = pixels.subarray(y * stride, (y + 1) * stride);
    const prev = y > 0 ? pixels.subarray((y - 1) * stride, y * stride) : Buffer.alloc(stride);
    for (let i = 0; i < stride; i++) {
      const a = i >= ch ? cur[i - ch] : 0;
      const b = prev[i];
      const c = i >= ch ? prev[i - ch] : 0;
      let v;
      if (ft === 0) v = cur[i];
      else if (ft === 1) v = cur[i] - a;
      else if (ft === 2) v = cur[i] - b;
      else if (ft === 3) v = cur[i] - ((a + b) >> 1);
      else v = cur[i] - paeth(a, b, c);
      raw[p + i] = v & 0xff;
    }
    p += stride;
  }

  const png = encodePng(width, height, 2, zlib.deflateSync(raw));
  const out = decodePng(png);
  assert.equal(out.width, width);
  assert.equal(out.height, height);
  assert.equal(out.channels, 3);
  assert.deepEqual(Buffer.from(out.data), pixels);
});

test('decodePng rejects a palette PNG with a clear message', () => {
  const png = encodePng(2, 2, 3, zlib.deflateSync(Buffer.alloc(6)));
  assert.throws(() => decodePng(png), /unsupported PNG colour type 3/);
});

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

function chunk(type, body) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(body.length, 0);
  const td = Buffer.concat([Buffer.from(type, 'latin1'), body]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td) >>> 0, 0);
  return Buffer.concat([len, td, crc]);
}

let CRC_TABLE = null;
function crc32(buf) {
  if (!CRC_TABLE) {
    CRC_TABLE = new Int32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      CRC_TABLE[n] = c;
    }
  }
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function encodePng(width, height, colorType, idat) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = colorType; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from('89504e470d0a1a0a', 'hex'),
    chunk('IHDR', ihdr),
    chunk('IDAT', idat),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}
