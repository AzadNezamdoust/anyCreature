#!/usr/bin/env node
// solve-camera.mjs — closed-form orthographic camera solve from a reference image.
//
// Research: research/04-image-and-judge.md section D + technique 1.
//   World-up +Y, orthographic camera at azimuth phi, elevation theta.
//   Screen slopes of the two ground-edge families:
//       m_X = tan(phi) * sin(theta)
//       m_Z = sin(theta) / tan(phi)
//   =>  theta = asin(sqrt(m_X * m_Z))
//       phi   = atan(sqrt(m_X / m_Z))
//   Sanity: 2:1 game-iso slopes 0.5/0.5 -> theta 30deg, phi 45deg.
//           true iso slopes tan(30deg)=0.5774 -> theta 35.264deg, phi 45deg.
//
// Usage: node scripts/solve-camera.mjs <subject> --image refs/<file>.png [--dry]
//
// No new dependencies: PNG decoding is a minimal inflate+unfilter path on node:zlib.

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DEG = 180 / Math.PI;

// ---------------------------------------------------------------- PNG decode

const PNG_SIG = '89504e470d0a1a0a';

/**
 * Minimal PNG decoder: 8-bit RGB (colour type 2) or RGBA (colour type 6),
 * non-interlaced, compression 0 / filter method 0. Everything else is rejected.
 * Returns { width, height, channels, data } with data as raw interleaved bytes.
 */
export function decodePng(buf) {
  if (buf.length < 8 || buf.subarray(0, 8).toString('hex') !== PNG_SIG) {
    throw new Error('not a PNG file (bad signature)');
  }
  let off = 8;
  let ihdr = null;
  const idat = [];
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.subarray(off + 4, off + 8).toString('latin1');
    const body = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      ihdr = {
        width: body.readUInt32BE(0),
        height: body.readUInt32BE(4),
        bitDepth: body[8],
        colorType: body[9],
        compression: body[10],
        filter: body[11],
        interlace: body[12],
      };
    } else if (type === 'IDAT') {
      idat.push(Buffer.from(body));
    } else if (type === 'IEND') {
      break;
    }
    off += 12 + len;
  }
  if (!ihdr) throw new Error('PNG has no IHDR chunk');
  if (ihdr.bitDepth !== 8) {
    throw new Error(`unsupported PNG bit depth ${ihdr.bitDepth} (need 8-bit; re-export the reference as 8-bit RGB/RGBA)`);
  }
  if (ihdr.colorType !== 2 && ihdr.colorType !== 6) {
    throw new Error(`unsupported PNG colour type ${ihdr.colorType} (need 2=RGB or 6=RGBA; palette/greyscale not supported)`);
  }
  if (ihdr.compression !== 0 || ihdr.filter !== 0) {
    throw new Error(`unsupported PNG compression/filter method ${ihdr.compression}/${ihdr.filter}`);
  }
  if (ihdr.interlace !== 0) {
    throw new Error('unsupported interlaced PNG (Adam7); re-export non-interlaced');
  }
  if (idat.length === 0) throw new Error('PNG has no IDAT data');

  const raw = zlib.inflateSync(Buffer.concat(idat));
  const channels = ihdr.colorType === 6 ? 4 : 3;
  const { width, height } = ihdr;
  const stride = width * channels;
  if (raw.length < (stride + 1) * height) {
    throw new Error(`PNG IDAT short: got ${raw.length} bytes, need ${(stride + 1) * height}`);
  }

  const out = Buffer.alloc(stride * height);
  let prev = Buffer.alloc(stride); // scanline 0 sees an all-zero "previous" row
  let p = 0;
  for (let y = 0; y < height; y++) {
    const ft = raw[p++];
    const line = raw.subarray(p, p + stride);
    p += stride;
    const cur = out.subarray(y * stride, (y + 1) * stride);
    unfilter(ft, line, cur, prev, channels, stride);
    prev = cur;
  }
  return { width, height, channels, data: out };
}

function unfilter(ft, line, cur, prev, bpp, stride) {
  switch (ft) {
    case 0: // None
      line.copy(cur);
      break;
    case 1: // Sub
      for (let i = 0; i < stride; i++) {
        const a = i >= bpp ? cur[i - bpp] : 0;
        cur[i] = (line[i] + a) & 0xff;
      }
      break;
    case 2: // Up
      for (let i = 0; i < stride; i++) cur[i] = (line[i] + prev[i]) & 0xff;
      break;
    case 3: // Average
      for (let i = 0; i < stride; i++) {
        const a = i >= bpp ? cur[i - bpp] : 0;
        cur[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xff;
      }
      break;
    case 4: // Paeth
      for (let i = 0; i < stride; i++) {
        const a = i >= bpp ? cur[i - bpp] : 0;
        const b = prev[i];
        const c = i >= bpp ? prev[i - bpp] : 0;
        cur[i] = (line[i] + paeth(a, b, c)) & 0xff;
      }
      break;
    default:
      throw new Error(`unknown PNG filter type ${ft}`);
  }
}

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

// ------------------------------------------------------------------- masking

/**
 * Mask = pixels that are not near-white. A pixel is masked when its max channel
 * is below `maxChannel` OR its HSV saturation exceeds `sat`. Fully transparent
 * pixels (RGBA alpha < alphaMin) are always background.
 */
export function buildMask(img, opts = {}) {
  const maxChannel = opts.maxChannel ?? 235;
  const sat = opts.sat ?? 0.08;
  const alphaMin = opts.alphaMin ?? 16;
  const { width, height, channels, data } = img;
  const mask = new Uint8Array(width * height);
  for (let i = 0, px = 0; px < width * height; px++, i += channels) {
    if (channels === 4 && data[i + 3] < alphaMin) continue;
    const r = data[i], g = data[i + 1], b = data[i + 2];
    const mx = r > g ? (r > b ? r : b) : (g > b ? g : b);
    const mn = r < g ? (r < b ? r : b) : (g < b ? g : b);
    const s = mx === 0 ? 0 : (mx - mn) / mx;
    if (mx < maxChannel || s > sat) mask[px] = 1;
  }
  return { mask, width, height };
}

/** Lowest masked row per column; -1 where the column is empty. */
export function bottomBoundary({ mask, width, height }) {
  const yb = new Int32Array(width).fill(-1);
  for (let x = 0; x < width; x++) {
    for (let y = height - 1; y >= 0; y--) {
      if (mask[y * width + x]) { yb[x] = y; break; }
    }
  }
  return yb;
}

/** Leftmost / rightmost masked column per row; -1 where the row is empty. */
export function sideBoundaries({ mask, width, height }) {
  const left = new Int32Array(height).fill(-1);
  const right = new Int32Array(height).fill(-1);
  for (let y = 0; y < height; y++) {
    const row = y * width;
    for (let x = 0; x < width; x++) if (mask[row + x]) { left[y] = x; break; }
    if (left[y] < 0) continue;
    for (let x = width - 1; x >= 0; x--) if (mask[row + x]) { right[y] = x; break; }
  }
  return { left, right };
}

// ------------------------------------------------------------------ line fit

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function lsq(pts) {
  let n = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
  for (const [x, y] of pts) { n++; sx += x; sy += y; sxx += x * x; sxy += x * y; }
  const den = n * sxx - sx * sx;
  if (n < 2 || Math.abs(den) < 1e-9) return null;
  const a = (n * sxy - sx * sy) / den;
  const b = (sy - a * sx) / n;
  return { a, b, n };
}

function rms(pts, a, b) {
  let s = 0;
  for (const [x, y] of pts) { const d = y - (a * x + b); s += d * d; }
  return Math.sqrt(s / pts.length);
}

/**
 * RANSAC line fit (y = a*x + b) followed by two least-squares refits on inliers.
 * Deterministic: fixed seed, exhaustive over sampled index pairs.
 */
export function ransacLine(pts, opts = {}) {
  const threshold = opts.threshold ?? 2.0;
  const iters = opts.iters ?? 2000;
  const rand = mulberry32(opts.seed ?? 1337);
  if (pts.length < 2) return null;

  let best = null;
  for (let it = 0; it < iters; it++) {
    const i = Math.floor(rand() * pts.length);
    let j = Math.floor(rand() * pts.length);
    if (j === i) j = (j + 1) % pts.length;
    const [x1, y1] = pts[i], [x2, y2] = pts[j];
    if (x1 === x2) continue;
    const a = (y2 - y1) / (x2 - x1);
    const b = y1 - a * x1;
    let count = 0;
    for (const [x, y] of pts) if (Math.abs(y - (a * x + b)) <= threshold) count++;
    if (!best || count > best.count) best = { a, b, count };
  }
  if (!best) return null;

  let { a, b } = best;
  let inliers = pts;
  for (let pass = 0; pass < 2; pass++) {
    inliers = pts.filter(([x, y]) => Math.abs(y - (a * x + b)) <= threshold);
    if (inliers.length < 2) break;
    const f = lsq(inliers);
    if (!f) break;
    a = f.a; b = f.b;
  }
  if (inliers.length < 2) return null;
  return { a, b, inliers: inliers.length, total: pts.length, rms: rms(inliers, a, b) };
}

// ------------------------------------------------------------- camera solve

/** theta/phi from the two absolute ground-edge slopes. */
export function anglesFromSlopes(mA, mB) {
  const prod = mA * mB;
  if (!(prod > 0)) throw new Error(`degenerate slopes (${mA}, ${mB}): product must be > 0`);
  const s = Math.sqrt(prod);
  if (s > 1) throw new Error(`sqrt(mX*mZ) = ${s.toFixed(4)} > 1 — not a valid orthographic elevation`);
  const theta = Math.asin(s);
  const phiA = Math.atan(Math.sqrt(mA / mB)); // assignment mX=mA, mZ=mB
  const phiB = Math.atan(Math.sqrt(mB / mA)); // the swap
  return { theta_deg: theta * DEG, phiA_deg: phiA * DEG, phiB_deg: phiB * DEG };
}

/**
 * Full solve from a mask. Returns angles, slopes, fits and the vertical check.
 */
export function solveFromMask(maskObj, opts = {}) {
  const threshold = opts.threshold ?? 2.0;
  const span = opts.span ?? 0; // 0 = use the whole boundary on each side
  const yb = bottomBoundary(maskObj);
  const cols = [];
  for (let x = 0; x < maskObj.width; x++) if (yb[x] >= 0) cols.push(x);
  if (cols.length < 8) throw new Error('mask is empty or too small to fit ground edges');

  // Front corner = lowest point of the silhouette (centre of the tied run).
  let lowest = -1;
  for (const x of cols) if (yb[x] > lowest) lowest = yb[x];
  const tied = cols.filter((x) => yb[x] === lowest);
  const corner = { x: Math.round((tied[0] + tied[tied.length - 1]) / 2), y: lowest };

  const pick = (from, to) => {
    const out = [];
    for (let x = from; x <= to; x++) if (yb[x] >= 0) out.push([x, yb[x]]);
    return out;
  };
  const xMin = cols[0], xMax = cols[cols.length - 1];
  const loL = span > 0 ? Math.max(xMin, corner.x - span) : xMin;
  const hiR = span > 0 ? Math.min(xMax, corner.x + span) : xMax;
  const leftPts = pick(loL, corner.x);
  const rightPts = pick(corner.x, hiR);
  if (leftPts.length < 8 || rightPts.length < 8) {
    throw new Error(`too few boundary points either side of the corner (L=${leftPts.length}, R=${rightPts.length})`);
  }

  const fitL = ransacLine(leftPts, { threshold, seed: opts.seed ?? 1337 });
  const fitR = ransacLine(rightPts, { threshold, seed: (opts.seed ?? 1337) + 1 });
  if (!fitL || !fitR) throw new Error('RANSAC failed to fit one of the ground edges');

  // Image y grows downward; ground edges rise away from the front corner, so the
  // left family has positive image-slope and the right family negative. Absolute
  // values are what the closed form needs.
  const mL = Math.abs(fitL.a);
  const mR = Math.abs(fitR.a);
  const ang = anglesFromSlopes(mL, mR);
  const residual_px = Math.sqrt((fitL.rms * fitL.rms + fitR.rms * fitR.rms) / 2);

  const vertical = verticalCheck(maskObj, opts);

  return {
    corner,
    fits: { left: fitL, right: fitR },
    slopes: { left: mL, right: mR },
    angles: ang,
    residual_px,
    vertical,
  };
}

/**
 * Near-vertical silhouette edges: runs of rows where the left (or right) mask
 * boundary moves by <= tol px per row for >= minFrac of the masked height.
 * Reports each run's tilt from true vertical, in degrees.
 */
export function verticalCheck(maskObj, opts = {}) {
  const tol = opts.vertTol ?? 1;
  const minFrac = opts.vertMinFrac ?? 0.30;
  // A run only counts as a *vertical edge candidate* if it is straight and
  // roughly upright. Long boundary runs that are actually roof/ground edges
  // (steep but not vertical, or not straight at all) are rejected, not reported
  // as a huge tilt.
  const maxTilt = opts.vertMaxTilt ?? 10;
  const maxRms = opts.vertMaxRms ?? 3;
  const { left, right } = sideBoundaries(maskObj);
  const rows = [];
  for (let y = 0; y < maskObj.height; y++) if (left[y] >= 0) rows.push(y);
  if (rows.length === 0) return { runs: [], max_tilt_deg: null };
  const minLen = Math.max(8, Math.round(rows.length * minFrac));

  const runsFor = (arr, side) => {
    const out = [];
    let start = null, prevY = null;
    const flush = (endY) => {
      if (start === null) return;
      const pts = [];
      for (let y = start; y <= endY; y++) if (arr[y] >= 0) pts.push([y, arr[y]]);
      if (pts.length >= minLen) {
        const f = lsq(pts); // x = a*y + b
        if (f) {
          out.push({
            side,
            y0: start,
            y1: endY,
            length: pts.length,
            tilt_deg: Math.atan(f.a) * DEG,
            rms_px: rms(pts, f.a, f.b),
          });
        }
      }
      start = null;
    };
    for (const y of rows) {
      if (prevY === null || y !== prevY + 1 || Math.abs(arr[y] - arr[prevY]) > tol) {
        flush(prevY ?? y);
        start = y;
      }
      prevY = y;
    }
    flush(prevY);
    return out;
  };

  const all = [...runsFor(left, 'left'), ...runsFor(right, 'right')]
    .sort((a, b) => b.length - a.length);
  const runs = all.filter((r) => Math.abs(r.tilt_deg) <= maxTilt && r.rms_px <= maxRms);
  const max_tilt_deg = runs.length ? Math.max(...runs.map((r) => Math.abs(r.tilt_deg))) : null;
  return { runs, rejected: all.length - runs.length, max_tilt_deg };
}

// ------------------------------------------------------------------ CLI glue

function parseArgs(argv) {
  const out = { _: [], dry: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry') out.dry = true;
    else if (a.startsWith('--')) {
      const key = a.slice(2);
      const v = argv[++i];
      out[key] = v;
    } else out._.push(a);
  }
  return out;
}

function usage() {
  return [
    'usage: node scripts/solve-camera.mjs <subject> --image refs/<file>.png [--dry]',
    '',
    'options:',
    '  --image <path>        reference PNG (8-bit RGB/RGBA, non-interlaced)  [required]',
    '  --dry                 solve and print, write nothing',
    '  --max-channel <n>     mask: max channel below this is masked           (default 235)',
    '  --sat <f>             mask: HSV saturation above this is masked        (default 0.08)',
    '  --threshold <px>      RANSAC inlier distance                           (default 2)',
    '  --span <px>           only use boundary within N px of the front corner (default 0 = all)',
    '  --vert-tol <px>       max per-row drift for a near-vertical run        (default 1)',
    '  --vert-min-frac <f>   min run length as a fraction of masked height    (default 0.30)',
    '  --vert-max-tilt <d>   max |tilt| for a run to count as a vertical edge (default 10)',
    '  --vert-max-rms <px>   max straightness rms for a vertical-edge run     (default 3)',
    '  --x-edge <e>          auto|left|right: the ground-edge family that runs along X (the WIDTH face). Vehicle',
    '                        class = left (nose on the screen-left, +X flank rising right). auto (default) = the',
    '                        first phi <= 45 deg, the SWAPPED assignment whenever the flank slope is the shallower',
    '                        one (V4-7: refs/school_bus.png)',
    '  --out <path>          override output json path (default: subjects/<s>/subject.json paths.camera, else refs/<s>.camera.json)',
  ].join('\n');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const subject = args._[0];
  if (!subject || !args.image) {
    console.error(usage());
    process.exit(2);
  }
  const imagePath = path.resolve(ROOT, args.image);
  if (!fs.existsSync(imagePath)) {
    console.error(`image not found: ${imagePath}`);
    process.exit(2);
  }
  const buf = fs.readFileSync(imagePath);
  const sha256 = crypto.createHash('sha256').update(buf).digest('hex');
  const img = decodePng(buf);

  const opts = {
    maxChannel: args['max-channel'] !== undefined ? Number(args['max-channel']) : 235,
    sat: args.sat !== undefined ? Number(args.sat) : 0.08,
    threshold: args.threshold !== undefined ? Number(args.threshold) : 2.0,
    span: args.span !== undefined ? Number(args.span) : 0,
    vertTol: args['vert-tol'] !== undefined ? Number(args['vert-tol']) : 1,
    vertMinFrac: args['vert-min-frac'] !== undefined ? Number(args['vert-min-frac']) : 0.30,
    vertMaxTilt: args['vert-max-tilt'] !== undefined ? Number(args['vert-max-tilt']) : 10,
    vertMaxRms: args['vert-max-rms'] !== undefined ? Number(args['vert-max-rms']) : 3,
  };

  const maskObj = buildMask(img, opts);
  let masked = 0;
  for (let i = 0; i < maskObj.mask.length; i++) masked += maskObj.mask[i];

  const r = solveFromMask(maskObj, opts);

  // phi assignment: theta is symmetric under the swap, phi is not. Report both,
  // pick the one <= 45deg first (research 04:D — the two are complements).
  // V4-7: --x-edge names the X family explicitly (phiA = mX on the left family, phiB = mX on the right family).
  const xEdge = args['x-edge'] ?? 'auto';
  if (!['auto', 'left', 'right'].includes(xEdge)) {
    console.error(`--x-edge must be auto, left or right, got ${xEdge}`);
    process.exit(2);
  }
  const phis = [r.angles.phiA_deg, r.angles.phiB_deg];
  const phi = xEdge === 'left' ? r.angles.phiA_deg : xEdge === 'right' ? r.angles.phiB_deg
    : phis.filter((p) => p <= 45 + 1e-9).sort((a, b) => a - b)[0] ?? Math.min(...phis);
  const mXisLeft = Math.abs(phi - r.angles.phiA_deg) < 1e-9;
  const mX = mXisLeft ? r.slopes.left : r.slopes.right;
  const mZ = mXisLeft ? r.slopes.right : r.slopes.left;

  const relImage = path.relative(ROOT, imagePath).split(path.sep).join('/');
  const vt = r.vertical.max_tilt_deg;
  const vertWarn = vt !== null && Math.abs(vt) > 1.5;

  console.log(`image            ${relImage}  ${img.width}x${img.height}  ${img.channels === 4 ? 'RGBA' : 'RGB'}`);
  console.log(`sha256           ${sha256}`);
  console.log(`mask             ${masked} px (${((masked / (img.width * img.height)) * 100).toFixed(1)}% of frame)  maxChannel<${opts.maxChannel} || sat>${opts.sat}`);
  console.log(`front corner     x=${r.corner.x} y=${r.corner.y}`);
  console.log(`left  edge fit   slope ${r.slopes.left.toFixed(5)}  inliers ${r.fits.left.inliers}/${r.fits.left.total}  rms ${r.fits.left.rms.toFixed(3)} px`);
  console.log(`right edge fit   slope ${r.slopes.right.toFixed(5)}  inliers ${r.fits.right.inliers}/${r.fits.right.total}  rms ${r.fits.right.rms.toFixed(3)} px`);
  console.log(`residual         ${r.residual_px.toFixed(3)} px (rms, both edges)`);
  console.log('');
  console.log(`theta            ${r.angles.theta_deg.toFixed(3)} deg   (elevation; asin(sqrt(mX*mZ)))`);
  console.log(`phi candidates   ${r.angles.phiA_deg.toFixed(3)} deg  |  ${r.angles.phiB_deg.toFixed(3)} deg   (mX/mZ assignment and its swap)`);
  console.log(`phi chosen       ${phi.toFixed(3)} deg  (${xEdge === 'auto' ? 'first <= 45 deg' : `--x-edge ${xEdge}: mX on the ${xEdge} family`})`);
  console.log(`slopes           mX ${mX.toFixed(5)}   mZ ${mZ.toFixed(5)}`);
  console.log('');
  if (vt === null) {
    console.log(`vertical check   no near-vertical runs found (${r.vertical.rejected} long runs rejected as non-vertical)`);
  } else {
    for (const run of r.vertical.runs.slice(0, 6)) {
      console.log(`  ${run.side.padEnd(5)} rows ${run.y0}-${run.y1} (${run.length})  tilt ${run.tilt_deg.toFixed(3)} deg  rms ${run.rms_px.toFixed(2)} px`);
    }
    console.log(`vertical tilt    ${vt.toFixed(3)} deg (max |tilt| over ${r.vertical.runs.length} run(s); ${r.vertical.rejected} rejected as non-vertical)  ${vertWarn ? 'WARN: > 1.5 deg — reference verticals are not vertical; not orthographic-clean' : 'OK (<= 1.5 deg)'}`);
  }

  const out = {
    theta_deg: round(r.angles.theta_deg, 4),
    phi_deg: round(phi, 4),
    slopes: { mX: round(mX, 6), mZ: round(mZ, 6) },
    residual_px: round(r.residual_px, 4),
    vertical_tilt_deg: vt === null ? null : round(vt, 4),
    source: relImage,
    sha256,
    solved: new Date().toISOString(),
    provisional: false,
    method: 'two-slope ground-edge fit',
    ...(xEdge === 'auto' ? {} : { xEdge }),
  };

  // V5-8 R1: refs/** is read-only; with no --out the camera goes where subjects/<s>/subject.json paths.camera says
  // (the path every loader reads), else the legacy refs/<s>.camera.json.
  const outPath = args.out ? path.resolve(ROOT, args.out) : subjectCameraPath(subject) ?? path.join(ROOT, 'refs', `${subject}.camera.json`);
  const provPath = path.join(path.dirname(outPath), `${subject}.camera.provisional.json`);

  if (args.dry) {
    console.log('\n--dry: would write ' + path.relative(ROOT, outPath).split(path.sep).join('/'));
    console.log(JSON.stringify(out, null, 2));
    return;
  }
  if (fs.existsSync(outPath) && !fs.existsSync(provPath)) {
    fs.copyFileSync(outPath, provPath);
    console.log(`\nkept old file as ${path.relative(ROOT, provPath).split(path.sep).join('/')}`);
  }
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2) + '\n');
  console.log(`\nwrote ${path.relative(ROOT, outPath).split(path.sep).join('/')}`);
}

/** subjects/<s>/subject.json paths.camera (absolute), or null when the subject has no manifest / camera path. */
export function subjectCameraPath(subject) {
  const file = path.join(ROOT, 'subjects', subject, 'subject.json');
  if (!fs.existsSync(file)) return null;
  const rel = JSON.parse(fs.readFileSync(file, 'utf8')).paths?.camera;
  return rel ? path.join(ROOT, rel) : null;
}

function round(v, n) {
  const f = 10 ** n;
  return Math.round(v * f) / f;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
