// WORKFLOW v4 — V4-1 item 2: the REGISTERED frame (research/WF-V4-PLAN.md "registered renders").
//
// The one place that says where a world point lands in the TARGET image (refs/<subject>.png, 1024 px). No
// bounding-box rescaling: compose-compare used to scale the render's foreground bounds onto the target's, which
// hid every scale and aspect error. Here the target frame is fixed per SUBJECT, never per render:
//
//   target px = ( s * (p . right) + ox ,  -s * (p . up) + oy )        p in the RENDER frame (after meta.front turn)
//
// right / up are the solved ortho camera's screen axes (refs/<s>.camera.json, the same lookAt src/app.js
// frameTarget uses). s (target px per metre) and (ox, oy) are fitted ONCE from the measured face quad
// (layout.measured.json `_frame.quadPx`, target px) against the class's METRIC ANCHOR face — the face the
// templates build at a fixed size: vehicle = the +X flank of the L x W x H body box (L = template-vehicle
// CLASS_DEFAULTS.length, W / H from width.overL / height.overL), nose at +L/2, ground y 0; building = the -Z
// front of the template-building pickFrame W x H wall, x centred, z 0. A model built at another size or position
// is therefore visibly off in the registered frame, which is the point.
//
// Every capture (900 px, framed on the model's own bounds by app.js) maps into this frame with one scale + offset
// (captureToTarget), so the browser stills and the Node projector share it.
import fs from "node:fs";
import * as THREE from "three";
import sharp from "sharp";

import { frontRotationDeg } from "../src/kernel/toThree.mjs";
import { CLASS_DEFAULTS as VEHICLE_DEFAULTS } from "./template-vehicle.mjs";
import { pickFrame } from "./template-building.mjs";
import { rasterPolygon } from "./measure-target.mjs";

/** Target foreground: darkest channel under this (the target is drawn on near-white). = likeness SILHOUETTE_FG_MAX. */
export const FG_MAX = 235;

/** Screen axes of the solved ortho camera (right, up, toward-camera), exactly the lookAt app.js frameTarget runs. */
export function cameraBasis(cameraSpec, azimuthOffsetDeg = 0) {
  const theta = THREE.MathUtils.degToRad(cameraSpec.theta_deg);
  const phi = THREE.MathUtils.degToRad(cameraSpec.phi_deg + azimuthOffsetDeg);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
  cam.position.copy(new THREE.Vector3().setFromSphericalCoords(100, Math.PI / 2 - theta, phi));
  cam.up.set(0, 1, 0);
  cam.lookAt(0, 0, 0);
  cam.updateMatrixWorld(true);
  const e = cam.matrixWorld.elements;
  return { right: [e[0], e[1], e[2]], up: [e[4], e[5], e[6]], back: [e[8], e[9], e[10]] };
}

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** Author frame -> render frame: the quarter turn toThree.mjs rotationY applies (x' = c x + s z, z' = -s x + c z). */
export function turnFn(deg) {
  const norm = ((deg % 360) + 360) % 360;
  const q = new Map([[0, [1, 0]], [90, [0, 1]], [180, [-1, 0]], [270, [0, -1]]]).get(norm);
  const [c, s] = q ?? [Math.cos(deg * Math.PI / 180), Math.sin(deg * Math.PI / 180)];
  return ([x, y, z]) => [c * x + s * z, y, -s * x + c * z];
}

const valueOf = (layout, key) => {
  const e = layout?.[key];
  return e && typeof e === "object" && Number.isFinite(e.value) ? e.value : null;
};

/**
 * The class's metric anchor face, author frame, plus the reference length the residual tolerances scale with.
 * MVP-STUB: two classes; a third class needs its template's size rule here.
 */
export function anchorFace(S) {
  const layout = S.readJson("layout");
  if (S.klass === "vehicle") {
    const L = VEHICLE_DEFAULTS.length;
    const W = (valueOf(layout, "width.overL") ?? 0.4) * L;
    const H = (valueOf(layout, "height.overL") ?? 0.5) * L;
    const x = W / 2;
    // + the quad order does not matter: registration() tries every correspondence.
    return { corners: [[x, H, L / 2], [x, H, -L / 2], [x, 0, -L / 2], [x, 0, L / 2]], L, W, H, ref: L, lengthAxis: [0, 0, 1],
      why: `vehicle +X flank, L ${L} m (template CLASS_DEFAULTS.length), W ${W.toFixed(3)}, H ${H.toFixed(3)}` };
  }
  if (S.klass === "building") {
    const { W, H } = pickFrame(layout, S.readJson("census"));
    return { corners: [[-W / 2, H, 0], [W / 2, H, 0], [W / 2, 0, 0], [-W / 2, 0, 0]], W, H, ref: H, lengthAxis: [1, 0, 0],
      why: `building -Z front, W ${W} x H ${H} m (template-building pickFrame)` };
  }
  if (S.klass === "weapon") {
    // class weapon (gold pipeline): the +X (left) flank of the facts.json dims box, as scripts/v7/conceptreg.mjs
    // anchorFaceOf — the corners hull.mjs --write-frame placed quadPx with, so registration() recovers its fit
    const f = new URL(`../subjects/${S.id}/turnaround/facts.json`, import.meta.url);
    const d = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")).dims : null;
    if (!(d?.L > 0 && d?.W > 0 && d?.H > 0)) throw new Error(`registered: subjects/${S.id}/turnaround/facts.json has no dims {L, W, H}`);
    const { L, W, H } = d, x = W / 2;
    return { corners: [[x, H, L / 2], [x, H, -L / 2], [x, 0, -L / 2], [x, 0, L / 2]], L, W, H, ref: L, lengthAxis: [0, 0, 1],
      why: `weapon +X flank of the facts.json dims box, L ${L} x W ${W} x H ${H} m` };
  }
  throw new Error(`registered: no metric anchor for class "${S.klass}"`);
}

/** The subject's front (render turn) — the class template's declared front. */
export function subjectFront(S) {
  return S.klass === "vehicle" || S.klass === "weapon" ? "+X" : "-Z";
}

/**
 * Fit (s, ox, oy) from the anchor face to the measured target quad. Every cyclic order and both directions of the
 * four corners are tried; the least-squares one wins (the quad key order is another script's convention).
 */
export function registration(S) {
  const measured = S.readJson("layoutMeasured");
  const quad = measured?._frame?.quadPx;
  if (!Array.isArray(quad) || quad.length !== 4) throw new Error(`registered: ${S.rel.layoutMeasured} has no _frame.quadPx`);
  const camera = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
  const basis = cameraBasis(camera);
  const anchor = anchorFace(S);
  const turnDeg = frontRotationDeg(subjectFront(S));
  const turn = turnFn(turnDeg);
  const ab = anchor.corners.map((c) => { const p = turn(c); return [dot(p, basis.right), -dot(p, basis.up)]; });
  let best = null;
  for (const dir of [1, -1]) {
    for (let k = 0; k < 4; k += 1) {
      const order = [0, 1, 2, 3].map((i) => (k + dir * i + 8) % 4);
      const A = order.map((i) => ab[i]);
      const ma = [A.reduce((s, p) => s + p[0], 0) / 4, A.reduce((s, p) => s + p[1], 0) / 4];
      const mq = [quad.reduce((s, p) => s + p[0], 0) / 4, quad.reduce((s, p) => s + p[1], 0) / 4];
      let num = 0;
      let den = 0;
      for (let i = 0; i < 4; i += 1) {
        const a = [A[i][0] - ma[0], A[i][1] - ma[1]];
        const q = [quad[i][0] - mq[0], quad[i][1] - mq[1]];
        num += a[0] * q[0] + a[1] * q[1];
        den += a[0] * a[0] + a[1] * a[1];
      }
      const s = num / den;
      if (!(s > 0)) continue;
      const ox = mq[0] - s * ma[0];
      const oy = mq[1] - s * ma[1];
      let err = 0;
      for (let i = 0; i < 4; i += 1) err += (s * A[i][0] + ox - quad[i][0]) ** 2 + (s * A[i][1] + oy - quad[i][1]) ** 2;
      const rms = Math.sqrt(err / 4);
      if (!best || rms < best.rmsPx) best = { s, ox, oy, rmsPx: rms };
    }
  }
  const targetMeta = { w: 1024, h: 1024 };
  try {
    const head = fs.readFileSync(S.paths.target);
    targetMeta.w = head.readUInt32BE(16);
    targetMeta.h = head.readUInt32BE(20);
  } catch { /* keep 1024 */ }
  const { s, ox, oy } = best;
  return {
    ...best, turnDeg, basis, camera, anchor, quadPx: quad, targetW: targetMeta.w, targetH: targetMeta.h,
    /** render-frame point -> target px */
    toTarget: (p) => [s * dot(p, basis.right) + ox, -s * dot(p, basis.up) + oy],
  };
}

// ---------------------------------------------------------------------------
// V5-1 item 2 — the fitted SIMILARITY on top of the registration (supersedes the "fixed metric size" ruling: in an
// ortho view absolute scale and placement are free, aspect is not). Three KNOBS a fit adds to any module:
//   frameScale (about the measured anchor quad's centre), frameX / frameY (target px at a 1024 px target).
// ---------------------------------------------------------------------------

export const FRAME_KNOBS = Object.freeze(["frameScale", "frameX", "frameY"]);
export const FRAME_RANGE = Object.freeze({ scale: [0.7, 1.4], px: 48 });

/** {scale, tx, ty} of a module's KNOBS (identity when it has none). */
export function frameOf(KNOBS) {
  const v = (n, d) => (KNOBS && KNOBS[n] && Number.isFinite(KNOBS[n].v) ? KNOBS[n].v : d);
  return { scale: v("frameScale", 1), tx: v("frameX", 0), ty: v("frameY", 0) };
}

/** The registration with the similarity applied: t' = c + scale (t - c) + (tx, ty) x targetW / 1024, c = quad centre. */
export function framed(reg, frame) {
  if (!frame || (frame.scale === 1 && !frame.tx && !frame.ty)) return reg;
  const q = reg.quadPx;
  const cx = q.reduce((a, p) => a + p[0], 0) / q.length;
  const cy = q.reduce((a, p) => a + p[1], 0) / q.length;
  const k = (reg.targetW ?? 1024) / 1024;
  const s = reg.s * frame.scale;
  const ox = cx + frame.scale * (reg.ox - cx) + frame.tx * k;
  const oy = cy + frame.scale * (reg.oy - cy) + frame.ty * k;
  const { basis } = reg;
  return { ...reg, s, ox, oy, frame, toTarget: (p) => [s * dot(p, basis.right) + ox, -s * dot(p, basis.up) + oy] };
}

/** The KNOBS lines of the similarity (identity start). */
export function frameKnobLines() {
  return [
    `  frameScale: { v: 1, min: ${FRAME_RANGE.scale[0]}, max: ${FRAME_RANGE.scale[1]}, unit: "scale" },   // V5-1 similarity: scale about the anchor quad centre`,
    `  frameX: { v: 0, min: ${-FRAME_RANGE.px}, max: ${FRAME_RANGE.px}, unit: "px" },   // V5-1 similarity: shift, target px`,
    `  frameY: { v: 0, min: ${-FRAME_RANGE.px}, max: ${FRAME_RANGE.px}, unit: "px" },   // V5-1 similarity: shift, target px`,
  ];
}

/** Add the similarity knobs to a module's KNOBS block (no block, or already there = unchanged). */
export function addFrameKnobs(text) {
  const start = text.indexOf("export const KNOBS = {");
  if (start < 0 || /\n\s*frameScale:\s*\{/.test(text)) return text;
  const end = text.indexOf("\n};", start);
  if (end < 0) return text;
  return `${text.slice(0, end)}\n${frameKnobLines().join("\n")}${text.slice(end)}`;
}

/**
 * A capture frame (framed by app.js on the model's own bounds: centre, half) -> target px, as one scale + offset:
 * tX = k * X + bx, tY = k * Y + by (X, Y capture px, continuous).
 */
export function captureToTarget(reg, { centre, half, size }) {
  const cr = dot(centre, reg.basis.right);
  const cu = dot(centre, reg.basis.up);
  const k = reg.s * 2 * half / size;
  return { k, bx: reg.s * (cr - half) + reg.ox, by: reg.oy - reg.s * (cu + half) };
}

// ---------------------------------------------------------------------------
// Pixels (vectorised JS, no per-pixel Python)
// ---------------------------------------------------------------------------

export async function readRGB(file) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data, w: info.width, h: info.height, c: info.channels };
}

/**
 * v7 ENCLOSED-FOREGROUND rule (views.json `families.enclosedFg`, opt-in per subject): of the near-white px — `label[i]
 * === 0`, i.e. darkest channel >= fgMax (a foreground mask, or an ortho family raster where family 0 = bg) — only the
 * region 4-connected to the image border or to a hole seed [x, y] (`families.holes`: a see-through opening the drawing
 * encloses) is background. Returns that region (1 = background); enclosed near-white (a white roof sign, a headlight
 * lens, a white box body) is foreground. THE one flood fill (registered.mjs foregroundMask, ortho.mjs readImage).
 */
export function borderBackground(label, w, h, holes = null) {
  const n = w * h;
  const bg = new Uint8Array(n);
  const stack = new Int32Array(n);   // every px is pushed at most once
  let top = 0;
  const push = (i) => { if (label[i] === 0 && !bg[i]) { bg[i] = 1; stack[top++] = i; } };
  for (let x = 0; x < w; x += 1) { push(x); push(n - w + x); }
  for (let y = 0; y < h; y += 1) { push(y * w); push(y * w + w - 1); }
  for (const seed of holes ?? []) {
    const [x, y] = Array.isArray(seed) ? seed : [];
    if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0 || x >= w || y >= h) throw new Error(`registered: hole seed ${JSON.stringify(seed)} is not a px [x, y] of the ${w} x ${h} image`);
    if (label[y * w + x] !== 0) throw new Error(`registered: hole seed [${x}, ${y}] is not a near-white px (it must sit inside the see-through opening)`);
    push(y * w + x);
  }
  while (top > 0) {
    const i = stack[--top];
    const x = i % w;
    if (x > 0) push(i - 1);
    if (x < w - 1) push(i + 1);
    if (i >= w) push(i - w);
    if (i < n - w) push(i + w);
  }
  return bg;
}

/**
 * Target foreground: darkest channel < fgMax. `enclosedFg` (views.json families.enclosedFg): near-white is background
 * only where it is connected to the image border or to a `holes` seed ([[x, y], ...], this image's px) — borderBackground.
 */
export function foregroundMask(img, fgMax = FG_MAX, opts = {}) {
  const { enclosedFg = false, holes = null } = opts ?? {};
  const n = img.w * img.h;
  const m = new Uint8Array(n);
  for (let i = 0, j = 0; i < n; i += 1, j += img.c) {
    const a = img.data[j], b = img.data[j + 1], c = img.data[j + 2];
    m[i] = (a < b ? (a < c ? a : c) : (b < c ? b : c)) < fgMax ? 1 : 0;
  }
  if (enclosedFg) {
    const bg = borderBackground(m, img.w, img.h, holes);
    for (let i = 0; i < n; i += 1) m[i] = bg[i] ? 0 : 1;
  }
  return m;
}

/**
 * WF-V4 V4-6 item 5 — the measured SUBJECT MASK (layout.measured.json `_subjectMask.polygon`, target px, written by
 * scripts/measure-target.mjs with its evidence) rasterised at w x h, or null when the subject has none (the target
 * holds only the subject).
 */
export function subjectMaskOf(S, w, h) {
  const rec = S.readJson("layoutMeasured")?._subjectMask;
  if (!rec || !Array.isArray(rec.polygon) || rec.polygon.length < 3) return null;
  return rasterPolygon(rec.polygon, w, h, rec.image?.w ?? w, rec.image?.h ?? h);
}

/**
 * The target foreground (binary): foregroundMask ∩ the subject mask (when measured). = targetState(...) === SUBJECT.
 * opts: foregroundMask's {enclosedFg, holes}.
 */
export function targetForeground(S, img, fgMax = FG_MAX, opts = {}) {
  const fg = foregroundMask(img, fgMax, opts);
  const m = S ? subjectMaskOf(S, img.w, img.h) : null;
  if (m) for (let i = 0; i < fg.length; i += 1) fg[i] &= m[i];
  return fg;
}

// ---------------------------------------------------------------------------
// V5-1 item 1 — the THREE-STATE target mask and the ONE IoU every scorer uses
// ---------------------------------------------------------------------------

export const BACKGROUND = 0;
export const SUBJECT = 1;
/** Don't-care: target foreground outside the subject polygon but inside its dilated convex hull (a neighbour in front). */
export const OCCLUDED = 2;
/** Dilation (px at a 1024 px target) of the subject polygon's convex hull that bounds the OCCLUDED band. */
export const OCCLUDE_PAD = 12;

function convexHull(points) {
  const pts = [...points].map(([x, y]) => [x, y]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (pts.length < 3) return pts;
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [];
  for (const p of pts) { while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop(); lower.push(p); }
  const upper = [];
  for (const p of [...pts].reverse()) { while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop(); upper.push(p); }
  return [...lower.slice(0, -1), ...upper.slice(0, -1)];
}

/** Separable square dilation of a 0/1 mask by r px. */
export function dilate(mask, w, h, r) {
  if (r <= 0) return mask;
  const tmp = new Uint8Array(w * h);
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    let last = -Infinity;   // x of the last set px seen scanning right
    const row = y * w;
    for (let x = 0; x < w + r; x += 1) {
      if (x < w && mask[row + x]) last = x;
      const t = x - r;
      if (t >= 0 && t < w && x - last <= 2 * r) tmp[row + t] = 1;
    }
  }
  for (let x = 0; x < w; x += 1) {
    let last = -Infinity;
    for (let y = 0; y < h + r; y += 1) {
      if (y < h && tmp[y * w + x]) last = y;
      const t = y - r;
      if (t >= 0 && t < h && y - last <= 2 * r) out[t * w + x] = 1;
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// WF v8 — DRIFT rects (views.json `drift`, scripts/v6/README.md): don't-care regions of one image, in its own px
// ---------------------------------------------------------------------------

/** `r` if it is a rect [x0, y0, x1, y1] (image px, x1 > x0, y1 > y0), else a thrown error naming it (`what`). */
export function checkRect(r, what = "drift rect") {
  if (!Array.isArray(r) || r.length !== 4 || !r.every(Number.isFinite) || !(r[2] > r[0]) || !(r[3] > r[1])) {
    throw new Error(`registered: ${what} ${JSON.stringify(r)} is not [x0, y0, x1, y1] px with x1 > x0 and y1 > y0`);
  }
  return r;
}

/**
 * CARE raster (1 = scored, 0 = don't care) of a w x h raster sampled from an iw x ih image the way ortho.mjs viewTarget
 * samples it (nearest, pixel centres: image px floor((x + 0.5) iw / w)): 0 where the sampled image px lies in one of
 * `rects` ([x0, y0, x1, y1], image px, half-open: px X is inside when x0 <= X + 0.5 < x1). null without rects.
 */
export function careMask(rects, w, h, iw = w, ih = h) {
  if (!rects?.length) return null;
  const care = new Uint8Array(w * h).fill(1);
  const tx = new Float64Array(w);
  for (let x = 0; x < w; x += 1) tx[x] = Math.min(iw - 1, Math.floor((x + 0.5) * iw / w)) + 0.5;
  for (const r of rects) {
    const [x0, y0, x1, y1] = checkRect(r);
    for (let y = 0; y < h; y += 1) {
      const Y = Math.min(ih - 1, Math.floor((y + 0.5) * ih / h)) + 0.5;
      if (Y < y0 || Y >= y1) continue;
      for (let x = 0; x < w; x += 1) if (tx[x] >= x0 && tx[x] < x1) care[y * w + x] = 0;
    }
  }
  return care;
}

const stateCache = new Map();
/**
 * The three-state TARGET mask at the target's own size: SUBJECT (fg inside the measured subject polygon), OCCLUDED
 * (fg outside it but inside its OCCLUDE_PAD-dilated convex hull, vertices dropped to the ground row — e.g. the facade's left wall, hidden behind the green
 * building: the model may draw there, the target cannot show it) and BACKGROUND. No subject polygon = fg is SUBJECT.
 * fgMax / opts ({enclosedFg, holes}): foregroundMask's — a subject's rule is ortho.mjs maskRule / maskOptions(rule, "concept").
 * opts.dontCare (WF v8 agree-IoU; never set by maskOptions): [[x0, y0, x1, y1], ...] rects (this image's px, careMask)
 * whose every px is OCCLUDED — in neither I nor U of `iou` (ortho.mjs driftRects(table, "concept")).
 */
export function targetState(S, img, fgMax = FG_MAX, opts = {}) {
  const fg = foregroundMask(img, fgMax, opts);
  const zones = S ? subjectZones(S, img.w, img.h) : null;   // cached per subject + size (the geometry, never the pixels)
  if (zones) for (let i = 0; i < fg.length; i += 1) fg[i] = !fg[i] ? BACKGROUND : zones.inside[i] ? SUBJECT : zones.hull[i] ? OCCLUDED : BACKGROUND;
  const care = careMask(opts?.dontCare, img.w, img.h);
  if (care) for (let i = 0; i < fg.length; i += 1) if (!care[i]) fg[i] = OCCLUDED;
  return fg;
}

/** {inside, hull} rasters of the measured subject polygon and its occlusion hull at w x h, or null. */
function subjectZones(S, w, h) {
  const key = `${S.id}:${w}x${h}`;
  if (stateCache.has(key)) return stateCache.get(key);
  const rec = S.readJson("layoutMeasured")?._subjectMask;
  let out = null;
  if (rec && Array.isArray(rec.polygon) && rec.polygon.length >= 3) {
    const iw = rec.image?.w ?? w;
    const ih = rec.image?.h ?? h;
    // the hull includes every vertex dropped to the subject's lowest row: a subject stands on the ground, so a wall a
    // neighbour hides (the facade's left wall behind the green building) runs down to it
    const yMax = Math.max(...rec.polygon.map((p) => p[1]));
    out = {
      inside: rasterPolygon(rec.polygon, w, h, iw, ih),
      hull: dilate(rasterPolygon(convexHull([...rec.polygon, ...rec.polygon.map(([x]) => [x, yMax])]), w, h, iw, ih), w, h, Math.round(OCCLUDE_PAD * w / 1024)),
    };
  }
  stateCache.set(key, out);
  return out;
}

/**
 * THE registered IoU (V5-1 item 1: registered.iou, the FIT score, residuals and render-module / composeSheet all call
 * this). `target`: 0 background, 1 subject, 2 OCCLUDED (don't care: in neither I nor U) — a binary mask is a
 * two-state target. `render`: a 0/1 mask, or with `ids` a part-id raster (-1 = background).
 */
export function iou(target, render, { ids = false } = {}) {
  let inter = 0;
  let union = 0;
  for (let i = 0; i < target.length; i += 1) {
    const t = target[i];
    if (t === OCCLUDED) continue;
    const y = ids ? render[i] >= 0 : render[i] !== 0;
    if (t && y) inter += 1;
    if (t || y) union += 1;
  }
  return union ? inter / union : 0;
}

/** Registered IoU of a render mask (target frame) against the subject's three-state target. */
export function registeredIoU(S, img, renderMask) {
  return iou(targetState(S, img), renderMask);
}

/** A capture still (size px) resampled into the target frame (w x h), nearest, white outside. */
export function resampleToTarget(img, map, w, h) {
  const out = new Uint8Array(w * h * 3).fill(255);
  for (let ty = 0; ty < h; ty += 1) {
    const Y = Math.floor((ty + 0.5 - map.by) / map.k);
    if (Y < 0 || Y >= img.h) continue;
    for (let tx = 0; tx < w; tx += 1) {
      const X = Math.floor((tx + 0.5 - map.bx) / map.k);
      if (X < 0 || X >= img.w) continue;
      const i = (Y * img.w + X) * img.c;
      const o = (ty * w + tx) * 3;
      out[o] = img.data[i]; out[o + 1] = img.data[i + 1]; out[o + 2] = img.data[i + 2];
    }
  }
  return { data: out, w, h, c: 3 };
}

function edgeOf(mask, w, h) {
  const e = new Uint8Array(w * h);
  for (let y = 1; y < h - 1; y += 1) {
    for (let x = 1; x < w - 1; x += 1) {
      const i = y * w + x;
      if (mask[i] && (!mask[i - 1] || !mask[i + 1] || !mask[i - w] || !mask[i + w])) e[i] = 1;
    }
  }
  return e;
}

const rawPanel = (img, S) => sharp(Buffer.from(img.data), { raw: { width: img.w, height: img.h, channels: img.c } }).resize(S, S).png().toBuffer();

/**
 * The registered compare sheet: TARGET | shaded render in the target frame | outlines (blue target, red render)
 * | three-quarter. `renderMask` is the render foreground in the target frame (Node projector, exact).
 */
export async function composeSheet({ target, shaded, threeQuarterFile, map, renderMask, out, iouValue, S = 700, targetMask = null }) {
  const w = target.w;
  const h = target.h;
  const reg = resampleToTarget(shaded, map, w, h);
  const tm = targetMask ?? foregroundMask(target);
  const subj = Uint8Array.from(tm, (v) => (v === SUBJECT ? 1 : 0));   // V5-1: the blue outline is the SUBJECT only
  const over = new Uint8Array(w * h * 3);
  for (let i = 0; i < w * h * 3; i += 1) over[i] = Math.round(target.data[(i / 3 | 0) * target.c + (i % 3)] * 0.65 + 255 * 0.35);
  for (let i = 0; i < w * h; i += 1) if (tm[i] === OCCLUDED) { over[i * 3] = Math.round(over[i * 3] * 0.6 + 160 * 0.4); over[i * 3 + 1] = Math.round(over[i * 3 + 1] * 0.6 + 160 * 0.4); over[i * 3 + 2] = Math.round(over[i * 3 + 2] * 0.6 + 160 * 0.4); }   // OCCLUDED greyed
  for (const [mask, col] of [[subj, [40, 90, 255]], [renderMask, [230, 30, 30]]]) {
    const e = edgeOf(mask, w, h);
    for (let i = 0; i < w * h; i += 1) if (e[i]) { over[i * 3] = col[0]; over[i * 3 + 1] = col[1]; over[i * 3 + 2] = col[2]; }
  }
  const panels = [
    await rawPanel({ data: target.c === 3 ? target.data : Uint8Array.from({ length: w * h * 3 }, (_, i) => target.data[(i / 3 | 0) * target.c + (i % 3)]), w, h, c: 3 }, S),
    await rawPanel(reg, S),
    await rawPanel({ data: over, w, h, c: 3 }, S),
    threeQuarterFile ? await sharp(threeQuarterFile).resize(S, S, { fit: "contain", background: "#ffffff" }).removeAlpha().png().toBuffer() : null,
  ];
  const titles = ["TARGET", "RENDER (shaded, registered)", `OUTLINES blue=target red=render  registered IoU ${iouValue.toFixed(3)}`, "RENDER three-quarter (shaded)"];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${S * 4}" height="40">${titles.map((t, i) => `<text x="${i * S + 8}" y="28" font-family="Arial" font-size="22">${t}</text>`).join("")}</svg>`;
  const composites = [{ input: Buffer.from(svg), left: 0, top: 0 }];
  panels.forEach((p, i) => { if (p) composites.push({ input: p, left: i * S, top: 40 }); });
  await sharp({ create: { width: S * 4, height: S + 40, channels: 3, background: "#ffffff" } }).composite(composites).png().toFile(out);
}
