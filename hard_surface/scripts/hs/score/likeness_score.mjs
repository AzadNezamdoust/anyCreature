// Interior likeness score for a hard-surface build: compares the build's four ortho renders with the subject's
// turnaround INSIDE the silhouette (where the outline score agree/IoU is blind): interior ink/edges, structure (SSIM),
// regional tone and colour, and openings (dark bores + see-through holes). Deterministic, image-only, ~0.3 s/build.
//
//   node scripts/hs/score/likeness_score.mjs --subject <s> [--build <dir>] [--prefix pass8_] [--json] [--out <file>]
//
// <dir> defaults to out/blender-hs/<s>; it must hold <prefix>{side,front,rear,top}.png rendered by scripts/hs/run_pass.py
// (same 1024 canvas + registration as subjects/<s>/turnaround/*.png). views.json drift rects are don't-care.
// Calibration, signal meanings and limits: scripts/hs/score/README.md, CALIBRATION.md.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import sharp from "sharp";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "../../..");
export const VIEWS = ["side", "front", "rear", "top"];
export const N = 512;            // working resolution (1024 canvases box-downsampled 2x)
const SHIFT = 6;          // registration slack, working px (= 12 canvas px) — reviewers exclude a few-mm offset
const FG_MAX = 215 / 255; // foreground = darkest channel below this (white page), as scripts/hs/imgio.fg_mask

// ---------- image io ----------
export async function loadRGB(file) {
  const { data, info } = await sharp(file).flatten({ background: "#ffffff" }).removeAlpha().raw()
    .toBuffer({ resolveWithObject: true });
  if (info.width !== 2 * N || info.height !== 2 * N) throw new Error(`${file}: expected ${2 * N}x${2 * N}, got ${info.width}x${info.height}`);
  const out = new Float32Array(N * N * 3), W = info.width;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) for (let c = 0; c < 3; c++) {
    const i0 = ((2 * y) * W + 2 * x) * 3 + c, i1 = i0 + W * 3;
    out[(y * N + x) * 3 + c] = (data[i0] + data[i0 + 3] + data[i1] + data[i1 + 3]) / 1020;
  }
  return out;
}

const srgbLin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
export function analyse(rgb) {
  const n = N * N, L = new Float32Array(n), lab = new Float32Array(n * 3), fg = new Uint8Array(n);
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  for (let i = 0; i < n; i++) {
    const r = rgb[3 * i], g = rgb[3 * i + 1], b = rgb[3 * i + 2];
    fg[i] = Math.min(r, g, b) < FG_MAX ? 1 : 0;
    const R = srgbLin(r), G = srgbLin(g), B = srgbLin(b);
    const X = (0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.9505, Y = 0.2126 * R + 0.7152 * G + 0.0722 * B, Z = (0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.089;
    const fy = f(Y);
    lab[3 * i] = 116 * fy - 16; lab[3 * i + 1] = 500 * (f(X) - fy); lab[3 * i + 2] = 200 * (fy - f(Z));
    L[i] = lab[3 * i] / 100;   // perceptual lightness 0..1
  }
  return { L, lab, fg };
}

// ---------- small morphology / filters ----------
export function maxFilter(m, r) {   // binary dilation, square (2r+1), separable, running-sum O(n)
  if (r === 0) return Uint8Array.from(m);
  const t = new Uint8Array(N * N), o = new Uint8Array(N * N), cs = new Int32Array(N + 1);
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) cs[x + 1] = cs[x] + m[y * N + x];
    for (let x = 0; x < N; x++) t[y * N + x] = cs[Math.min(N, x + r + 1)] - cs[Math.max(0, x - r)] > 0 ? 1 : 0;
  }
  for (let x = 0; x < N; x++) {
    for (let y = 0; y < N; y++) cs[y + 1] = cs[y] + t[y * N + x];
    for (let y = 0; y < N; y++) o[y * N + x] = cs[Math.min(N, y + r + 1)] - cs[Math.max(0, y - r)] > 0 ? 1 : 0;
  }
  return o;
}
const notM = (m) => m.map((v) => 1 - v);
export const erode = (m, r) => notM(maxFilter(notM(m), r));
export function boxMean(a, r) {     // mean over (2r+1)^2 window, clamped at the borders (integral image)
  const W = N + 1, I = new Float64Array(W * W);
  for (let y = 0; y < N; y++) { let s = 0; for (let x = 0; x < N; x++) { s += a[y * N + x]; I[(y + 1) * W + x + 1] = I[y * W + x + 1] + s; } }
  const o = new Float32Array(N * N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const y0 = Math.max(0, y - r), y1 = Math.min(N, y + r + 1), x0 = Math.max(0, x - r), x1 = Math.min(N, x + r + 1);
    o[y * N + x] = (I[y1 * W + x1] - I[y0 * W + x1] - I[y1 * W + x0] + I[y0 * W + x0]) / ((y1 - y0) * (x1 - x0));
  }
  return o;
}
export function sobel(L) {
  const g = new Float32Array(N * N);
  for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) {
    const p = (dx, dy) => L[(y + dy) * N + x + dx];
    const gx = p(1, -1) + 2 * p(1, 0) + p(1, 1) - p(-1, -1) - 2 * p(-1, 0) - p(-1, 1);
    const gy = p(-1, 1) + 2 * p(0, 1) + p(1, 1) - p(-1, -1) - 2 * p(0, -1) - p(1, -1);
    g[y * N + x] = Math.hypot(gx, gy) / 4;
  }
  return g;
}
export function enclosedBg(fg) {    // background px NOT 4-connected to the image border = a see-through opening
  const n = N * N, out = new Uint8Array(n), seen = new Uint8Array(n), st = new Int32Array(n); let sp = 0;
  const push = (i) => { if (!fg[i] && !seen[i]) { seen[i] = 1; st[sp++] = i; } };
  for (let k = 0; k < N; k++) { push(k); push((N - 1) * N + k); push(k * N); push(k * N + N - 1); }
  while (sp) { const i = st[--sp], x = i % N, y = (i / N) | 0; if (x) push(i - 1); if (x < N - 1) push(i + 1); if (y) push(i - N); if (y < N - 1) push(i + N); }
  for (let i = 0; i < n; i++) out[i] = !fg[i] && !seen[i] ? 1 : 0;
  return out;
}
export function shifted(a, dx, dy, fill = 0) {   // a moved by (dx, dy); c channels per px
  const o = new a.constructor(a.length).fill(fill), c = a.length / (N * N), rowLen = N * c;
  for (let y = 0; y < N; y++) { const sy = y - dy; if (sy < 0 || sy >= N) continue;
    const x0 = Math.max(0, dx), x1 = Math.min(N, N + dx);
    if (x1 > x0) o.set(a.subarray(sy * rowLen + (x0 - dx) * c, sy * rowLen + (x1 - dx) * c), y * rowLen + x0 * c); }
  return o;
}
function bboxOf(a, b, pad) {
  let x0 = N, y0 = N, x1 = -1, y1 = -1;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (a[y * N + x] || b[y * N + x]) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return [Math.max(0, x0 - pad), Math.max(0, y0 - pad), Math.min(N - 1, x1 + pad), Math.min(N - 1, y1 + pad)];
}
function iouShift(a, b, dx, dy, care, bb) {   // IoU of a and b moved by (dx, dy), over care px inside bb; no allocation
  let i = 0, u = 0;
  for (let y = bb[1]; y <= bb[3]; y++) { const sy = y - dy, row = sy >= 0 && sy < N;
    for (let x = bb[0]; x <= bb[2]; x++) { const k = y * N + x; if (!care[k]) continue;
      const sx = x - dx, q = row && sx >= 0 && sx < N ? b[sy * N + sx] : 0, p = a[k]; i += p & q; u += p | q; } }
  return u ? i / u : 1;
}
export function iouOf(a, b, care) {
  let i = 0, u = 0;
  for (let k = 0; k < a.length; k++) { if (!care[k]) continue; const p = a[k], q = b[k]; i += p & q; u += p | q; }
  return u ? i / u : 1;
}
/** tolerant F1 of two binary maps (restricted to `within`): a px counts as matched if the other map has one within r. */
export function tolF1(A, B, within, r) {
  const dA = maxFilter(A, r), dB = maxFilter(B, r);
  let nA = 0, nB = 0, hA = 0, hB = 0;
  for (let i = 0; i < A.length; i++) { if (!within[i]) continue; if (A[i]) { nA++; hA += dB[i]; } if (B[i]) { nB++; hB += dA[i]; } }
  if (nA + nB === 0) return { f1: null, recall: null, precision: null, nA, nB };
  const rec = nA ? hA / nA : 0, prec = nB ? hB / nB : 0;
  return { f1: rec + prec ? (2 * rec * prec) / (rec + prec) : 0, recall: rec, precision: prec, nA, nB };
}

// ---------- per-view signals ----------
export const EDGE_T = 0.06;   // Sobel magnitude on L* (0..1) that counts as a drawn edge/ink line
const CELL = 8;               // tone grid cell, working px (= 16 canvas px)

// ---------- openings ----------
// v1 (to 2026-10-10): recess = fg px with L* < 0.25 and < 0.6 x the plain 21x21 mean. That surround included the white
// page, so the dark rim/ink band along every outline and every dark-painted part counted as an "opening", and a build
// scored higher the more near-black px it had near the source's outlines (it_grapple pass10 vs 16).
// v2 (port of part_score's PART-CALIBRATION.md fix): the surround is foreground-only, and a recess must also be darker
// than REC_REL x the image's own foreground median L* in its region (TILE grid, 3x3 tile neighbourhood), so a
// uniformly dark part or a dark-painted area is no longer a recess.
export const REC_REL = 0.65, REC_MAX = 0.25, REC_LOC = 0.6;
const REC_OPEN = 1;   // morphological opening radius (working px): removes ink lines / rims <= 2 working px wide
const TILE = 32;   // working px; region = 3x3 tiles = 96 working px (192 canvas px)
const OPEN_V1 = process.env.LIKENESS_OPEN_V1 === "1";   // reproduce the v1 rule (calibration before/after only)
function regionMedianMap(img) {
  const T = N / TILE, B = 64, hist = new Int32Array(T * T * B);
  for (let i = 0; i < N * N; i++) if (img.fg[i]) { const x = i % N, y = (i / N) | 0;
    hist[(((y / TILE) | 0) * T + ((x / TILE) | 0)) * B + Math.min(B - 1, (img.L[i] * B) | 0)]++; }
  const med = new Float32Array(T * T).fill(1);
  for (let ty = 0; ty < T; ty++) for (let tx = 0; tx < T; tx++) {
    const h = new Int32Array(B); let n = 0;
    for (let y = Math.max(0, ty - 1); y <= Math.min(T - 1, ty + 1); y++) for (let x = Math.max(0, tx - 1); x <= Math.min(T - 1, tx + 1); x++)
      for (let b = 0; b < B; b++) { h[b] += hist[(y * T + x) * B + b]; n += hist[(y * T + x) * B + b]; }
    if (!n) continue; let c = 0, b = 0; for (; b < B; b++) { c += h[b]; if (2 * c >= n) break; }
    med[ty * T + tx] = (b + 0.5) / B;
  }
  return (i) => med[(((i / N) | 0) / TILE | 0) * T + ((i % N) / TILE | 0)];
}
export function openMap(img) {
  const enc = enclosedBg(img.fg), o = new Uint8Array(N * N);
  if (OPEN_V1) {
    const loc = boxMean(img.L, 10);
    for (let i = 0; i < N * N; i++) o[i] = enc[i] || (img.fg[i] && img.L[i] < 0.25 && img.L[i] < 0.6 * loc[i]) ? 1 : 0;
    return o;
  }
  const fgf = Float32Array.from(img.fg), sL = boxMean(img.L.map((v, i) => v * img.fg[i]), 10), sF = boxMean(fgf, 10);
  const reg = regionMedianMap(img), rec = new Uint8Array(N * N);
  for (let i = 0; i < N * N; i++) {
    if (!img.fg[i]) continue;
    const loc = sL[i] / Math.max(1e-6, sF[i]);   // foreground-only surround mean
    rec[i] = img.L[i] < Math.min(REC_MAX, REC_REL * reg(i)) && img.L[i] < REC_LOC * loc ? 1 : 0;
  }
  const thick = REC_OPEN ? maxFilter(erode(rec, REC_OPEN), REC_OPEN) : rec;   // drop ink lines / thin rims
  for (let i = 0; i < N * N; i++) o[i] = enc[i] | (thick[i] & rec[i]);
  return o;
}

export function viewSignals(S, Bimg, care) {
  // registration: best integer shift of the build silhouette within +-SHIFT (searched on the care area)
  const bb = bboxOf(S.fg, Bimg.fg, SHIFT + 1);
  let best = { iou: -1, dx: 0, dy: 0 };
  const tryShift = (dx, dy) => {
    if (Math.abs(dx) > SHIFT || Math.abs(dy) > SHIFT) return;
    const v = iouShift(S.fg, Bimg.fg, dx, dy, care, bb);
    if (v > best.iou + 1e-9 || (Math.abs(v - best.iou) <= 1e-9 && Math.abs(dx) + Math.abs(dy) < Math.abs(best.dx) + Math.abs(best.dy))) best = { iou: v, dx, dy };
  };
  for (let dy = -SHIFT; dy <= SHIFT; dy += 2) for (let dx = -SHIFT; dx <= SHIFT; dx += 2) tryShift(dx, dy);   // coarse
  const c = { ...best };
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) tryShift(c.dx + dx, c.dy + dy);              // refine
  const iou0 = iouShift(S.fg, Bimg.fg, 0, 0, care, bb);
  const B = { L: shifted(Bimg.L, best.dx, best.dy, 1), lab: shifted(Bimg.lab, best.dx, best.dy, 0), fg: shifted(Bimg.fg, best.dx, best.dy) };
  for (let i = 0; i < N * N; i++) if (!B.fg[i]) { B.lab[3 * i] = 100; B.lab[3 * i + 1] = 0; B.lab[3 * i + 2] = 0; }

  const both = new Uint8Array(N * N);
  for (let i = 0; i < N * N; i++) both[i] = S.fg[i] & B.fg[i] & care[i];
  const R = erode(both, 2);                       // interior: 2 px clear of either outline
  let nR = 0; for (let i = 0; i < N * N; i++) nR += R[i];

  // 1. interior edges / ink
  const gS = sobel(S.L), gB = sobel(B.L);
  const eS = new Uint8Array(N * N), eB = new Uint8Array(N * N);
  for (let i = 0; i < N * N; i++) { eS[i] = gS[i] > EDGE_T ? 1 : 0; eB[i] = gB[i] > EDGE_T ? 1 : 0; }
  const edge = tolF1(eS, eB, R, 2);

  // 2. structure: SSIM on L* inside R (7x7 box windows)
  const r = 3, mS = boxMean(S.L, r), mB = boxMean(B.L, r);
  const sq = (a) => a.map((v) => v * v), mul = (a, b) => a.map((v, i) => v * b[i]);
  const sSS = boxMean(sq(S.L), r), sBB = boxMean(sq(B.L), r), sSB = boxMean(mul(S.L, B.L), r);
  const C1 = 0.01 ** 2, C2 = 0.03 ** 2; let ss = 0;
  for (let i = 0; i < N * N; i++) if (R[i]) {
    const vs = sSS[i] - mS[i] ** 2, vb = sBB[i] - mB[i] ** 2, cv = sSB[i] - mS[i] * mB[i];
    ss += ((2 * mS[i] * mB[i] + C1) * (2 * cv + C2)) / ((mS[i] ** 2 + mB[i] ** 2 + C1) * (vs + vb + C2));
  }
  const ssim = nR ? ss / nR : 0;

  // 3. regional tone (L*) and colour (dE76) on a 16-canvas-px grid, cells >= half interior
  let wsum = 0, dL = 0, dE = 0;
  for (let cy = 0; cy < N; cy += CELL) for (let cx = 0; cx < N; cx += CELL) {
    let k = 0; const a = [0, 0, 0], b = [0, 0, 0];
    for (let y = cy; y < cy + CELL; y++) for (let x = cx; x < cx + CELL; x++) { const i = y * N + x; if (!R[i]) continue; k++;
      for (let c = 0; c < 3; c++) { a[c] += S.lab[3 * i + c]; b[c] += B.lab[3 * i + c]; } }
    if (k < (CELL * CELL) / 2) continue;
    for (let c = 0; c < 3; c++) { a[c] /= k; b[c] /= k; }
    wsum += k; dL += k * Math.abs(a[0] - b[0]); dE += k * Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }
  const toneDL = wsum ? dL / wsum : 100, colourDE = wsum ? dE / wsum : 100;

  // 4. openings: see-through holes + dark recesses (bores, slots), inside the source's or the build's silhouette
  //    envelope; recess rule in openMap() (CALIBRATION.md "open signal v2")
  const oS = openMap(S), oB = openMap(B);
  const env = maxFilter(new Uint8Array(N * N).map((_, i) => (S.fg[i] | B.fg[i]) & care[i]), 3);
  const opening = tolF1(erode(oS, 0), oB, env, 2);

  return { dx: best.dx * 2, dy: best.dy * 2, iou0, iou: best.iou, interiorPx: nR,
    edgeF1: edge.f1 ?? 1, edgeRecall: edge.recall, edgePrecision: edge.precision,
    ssim, toneDL, colourDE,
    openF1: opening.f1 ?? 1, openRecall: opening.recall, openPrecision: opening.precision, openSrcPx: opening.nA, openBuildPx: opening.nB };
}

// ---------- combination (a priori weights; see CALIBRATION.md for what was tested) ----------
export const SIGNALS = ["edgeF1", "ssim", "toneSim", "colourSim", "openF1"];
export const WEIGHTS = { edgeF1: 0.3, ssim: 0.2, toneSim: 0.2, colourSim: 0.1, openF1: 0.2 };
export function normalise(v) {
  return { ...v, toneSim: Math.max(0, 1 - v.toneDL / 25), colourSim: Math.max(0, 1 - v.colourDE / 30) };
}
export function combine(views, weights = WEIGHTS) {
  // views are weighted by their interior area (the px each view actually contributes); equal weights are kept as
  // interiorEq for comparison (CALIBRATION.md: area weighting was picked among 4 view weightings — a post-hoc choice)
  const out = {}, area = VIEWS.map((v) => views[v].interiorPx), A = area.reduce((a, b) => a + b, 0) || 1;
  for (const k of [...SIGNALS, "iou", "iou0"]) out[k] = VIEWS.reduce((s, v, i) => s + views[v][k] * area[i], 0) / A;
  const vInt = (v) => { let t = 0, ws = 0; for (const [k, w] of Object.entries(weights)) { t += w * views[v][k]; ws += w; } return t / ws; };
  for (const v of VIEWS) views[v].interior = vInt(v);
  out.interior = VIEWS.reduce((s, v, i) => s + views[v].interior * area[i], 0) / A;
  out.interiorEq = VIEWS.reduce((s, v) => s + views[v].interior, 0) / VIEWS.length;
  out.iou = VIEWS.reduce((s, v) => s + views[v].iou, 0) / VIEWS.length;   // silhouette gate: plain view mean
  out.likeness = out.interior * out.iou;   // the silhouette still gates: a perfect interior on a wrong outline is not a likeness
  return out;
}

// ---------- public api ----------
export function careMask(subject, view) {
  const care = new Uint8Array(N * N).fill(1);
  const vj = path.join(ROOT, "subjects", subject, "turnaround", "views.json");
  if (!fs.existsSync(vj)) return care;
  const rects = JSON.parse(fs.readFileSync(vj, "utf8"))?.drift?.[view] ?? [];
  for (const { rect: [x0, y0, x1, y1] } of rects)
    for (let y = Math.max(0, Math.floor(y0 / 2)); y < Math.min(N, Math.ceil(y1 / 2)); y++)
      for (let x = Math.max(0, Math.floor(x0 / 2)); x < Math.min(N, Math.ceil(x1 / 2)); x++) care[y * N + x] = 0;
  return care;
}
const srcCache = new Map();
export async function sourceView(subject, view) {
  const key = `${subject}/${view}`;
  if (!srcCache.has(key)) srcCache.set(key, analyse(await loadRGB(path.join(ROOT, "subjects", subject, "turnaround", `${view}.png`))));
  return srcCache.get(key);
}
/** files: {side, front, rear, top} -> png paths of the build renders */
export async function scoreFiles(subject, files, weights = WEIGHTS) {
  const views = {};
  for (const v of VIEWS) views[v] = normalise(viewSignals(await sourceView(subject, v), analyse(await loadRGB(files[v])), careMask(subject, v)));
  return { subject, views, ...combine(views, weights) };
}
export async function scoreBuild(subject, dir, prefix = "", weights = WEIGHTS) {
  const files = Object.fromEntries(VIEWS.map((v) => [v, path.join(dir, `${prefix}${v}.png`)]));
  return scoreFiles(subject, files, weights);
}

// ---------- cli ----------
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const argv = process.argv.slice(2), arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
  const subject = arg("--subject");
  if (!subject) { console.error("usage: node likeness_score.mjs --subject <s> [--build <dir>] [--prefix passN_] [--json] [--out <file>]"); process.exit(2); }
  const dir = path.resolve(arg("--build") ?? path.join(ROOT, "out", "blender-hs", subject));
  const res = await scoreBuild(subject, dir, arg("--prefix") ?? "");
  const r3 = (x) => (typeof x === "number" ? Math.round(x * 1000) / 1000 : x);
  const slim = JSON.parse(JSON.stringify(res, (k, v) => r3(v)));
  if (arg("--out")) fs.writeFileSync(arg("--out"), JSON.stringify(slim, null, 1));
  if (argv.includes("--json")) console.log(JSON.stringify(slim));
  else {
    console.log(`${subject}  likeness ${r3(res.likeness)}  (interior ${r3(res.interior)} x silhouette ${r3(res.iou)})`);
    console.log("view    iou   edgeF1 ssim  tone  colour open  shift");
    for (const v of VIEWS) { const s = res.views[v];
      console.log(`${v.padEnd(6)} ${[s.iou, s.edgeF1, s.ssim, s.toneSim, s.colourSim, s.openF1].map((x) => r3(x).toFixed(3)).join(" ")}  ${s.dx},${s.dy}`); }
  }
}
