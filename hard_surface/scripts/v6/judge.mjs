// WORKFLOW v6 — the 6-VIEW JUDGE (research/WF-V6-PLAN.md D) — deterministic part only (no VLM seat). Generic (V6-2).
//
// judge({ subjectId, modulePath | built }) renders the module TRUE-COLOUR CEL shaded (ortho.mjs CEL: palette colour at
// 100 % on faces toward the viewer, 85 % sides, 105 % tops) in the subject's turnaround orthos (views.json; the reference
// registration, one uniform model scale sigma shared by all of them and fitted per module, so an arbitrary metric size
// is not scored, proportions are) + 2 three-quarter views (front-left = the solved concept camera, rear-right = the same
// camera turned 180 deg), and measures: per-view silhouette IoU vs the turnaround (+ zone-family IoU), the concept view's
// registered IoU at full resolution, the class placement checks (rules registry: float / clip / ...), symmetry (the
// class's symmetry view mirrored, near-side-only parts removed), and the weighted multi-view score (concept CONCEPT_W,
// each ortho 1). WF v8: per view `agree` = the same IoU with the views.json drift rects don't-care (= iou without drift),
// `drift` = the share of the reference foreground they cover, minAgree; judge({blobs: true}) adds the BLOB TABLE.
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { FACES, buildModule, meshParts, project } from "../project.mjs";
import { OCCLUDED, SUBJECT, cameraBasis, careMask, iou, readRGB, targetState, turnFn } from "../registered.mjs";
import { frontRotationDeg } from "../../src/kernel/toThree.mjs";
import { CEL, DRIFT_MAX, basisOf, cross, driftRects, loadTurnaround, maskOptions, paletteHex, partFamilies, pxToView, rasterOrtho, viewDrift, viewMap, viewScore, viewTarget } from "./ortho.mjs";
import { rulesFor } from "./rules.mjs";
import { CONCEPT_W } from "./mvfit.mjs";

export const JUDGE_SIZE = 512;
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const r3 = (v) => Math.round(v * 1e3) / 1e3;
const r1 = (v) => Math.round(v * 10) / 10;

const hex = (h) => [1, 3, 5].map((i) => parseInt(String(h).slice(i, i + 2), 16));

/**
 * TRUE-COLOUR cel raster (white background): each px = its zone's palette colour for the px's face (a per-face palette
 * entry: top / front / side, the concept's measured cel tones) x the cel factor (a top with a measured top colour: 100 %).
 */
export function shadeRGB(parts, palette, partId, shade, face, w, h) {
  const cache = new Map();
  const colour = (p, f) => {
    const key = `${p}:${f}`;
    if (!cache.has(key)) cache.set(key, hex(paletteHex(palette?.[parts[p].zone], FACES[f])));
    return cache.get(key);
  };
  const out = Buffer.alloc(w * h * 3, 255);
  for (let i = 0; i < w * h; i += 1) {
    const p = partId[i];
    if (p < 0) continue;
    const c = colour(p, face[i]);
    const e = palette?.[parts[p].zone];
    const s = Math.abs(shade[i] - CEL.top) < 1e-6 && e && typeof e === "object" && e.top ? 1 : shade[i];
    out[i * 3] = Math.min(255, Math.round(c[0] * s)); out[i * 3 + 1] = Math.min(255, Math.round(c[1] * s)); out[i * 3 + 2] = Math.min(255, Math.round(c[2] * s));
  }
  return out;
}

// ---------------------------------------------------------------------------
// VIEW-TAGGED residual rows (the seat's evidence): silhouette edges + zone-family components, per ortho view
// ---------------------------------------------------------------------------

export const ROW_M = 0.045;          // a row is reported at >= this many metres (loop.mjs SHOW.metres)
export const ROW_MIN_PX = 30;        // components under this many px (JUDGE_SIZE raster) are noise
const DEFAULT_WORDS = { "+x": "+x", "-x": "-x", "+y": "high", "-y": "low", "+z": "+z", "-z": "-z" };
const r2 = (v) => Math.round(v * 100) / 100;
const wordOf = (words, a, sgn) => ({ ...DEFAULT_WORDS, ...words })[`${sgn > 0 ? "+" : "-"}${"xyz"[a]}`];

/** Direction words of a world displacement (x: outboard / inboard of a part centred at cx; y high / low; z class words). */
function dirWords(d, centre, words) {
  const out = [];
  for (let a = 0; a < 3; a += 1) {
    if (Math.abs(d[a]) < ROW_M) continue;
    let w = wordOf(words, a, d[a]);
    if (a === 0 && Math.abs(centre[0]) > 0.05) w = Math.sign(d[0]) === Math.sign(centre[0]) ? "outboard" : "inboard";
    out.push(`${r2(Math.abs(d[a]))} m too far ${w}`);
  }
  return out;
}

export const ROW_OPEN = 2;           // px: ink strokes (the turnaround's outlines join every dark part) are opened away

/** Box min / max filter of radius r (separable), 0/1 masks. */
function boxFilter(mask, w, h, r, max) {
  // sliding count of set px in the window (out of range = unset): max -> any set, min -> all 2r+1 set
  const need = max ? 1 : 2 * r + 1;
  const pass = (src, n, m, stride, step) => {
    const out = new Uint8Array(w * h);
    for (let a = 0; a < m; a += 1) {
      const base = a * stride;
      let cnt = 0;
      for (let q = 0; q < Math.min(r, n); q += 1) cnt += src[base + q * step];
      for (let b = 0; b < n; b += 1) {
        if (b + r < n) cnt += src[base + (b + r) * step];
        if (b - r - 1 >= 0) cnt -= src[base + (b - r - 1) * step];
        out[base + b * step] = cnt >= need ? 1 : 0;
      }
    }
    return out;
  };
  return pass(pass(mask, w, h, w, 1), h, w, 1, w);
}
/** Morphological opening (erode then dilate, radius r). */
export const openMask = (mask, w, h, r = ROW_OPEN) => boxFilter(boxFilter(mask, w, h, r, false), w, h, r, true);

/**
 * Connected components (4-neighbour) of `mask(i)` on a w x h raster, >= minPx (default ROW_MIN_PX): [{n, x0, y0, x1, y1
 * (inclusive px), cx, cy (mean px), ids (idOf(px) -> count), seed (the first px index)}].
 */
export function blobs(w, h, mask, idOf = null, minPx = ROW_MIN_PX) {
  const seen = new Uint8Array(w * h);
  const out = [];
  const stack = [];
  for (let i = 0; i < w * h; i += 1) {
    if (seen[i] || !mask(i)) continue;
    const b = { n: 0, x0: w, y0: h, x1: 0, y1: 0, sx: 0, sy: 0, ids: new Map(), seed: i };
    stack.push(i); seen[i] = 1;
    while (stack.length) {
      const j = stack.pop();
      const x = j % w, y = (j - x) / w;
      b.n += 1; b.sx += x; b.sy += y;
      if (x < b.x0) b.x0 = x; if (x > b.x1) b.x1 = x; if (y < b.y0) b.y0 = y; if (y > b.y1) b.y1 = y;
      if (idOf) { const id = idOf(j); b.ids.set(id, (b.ids.get(id) ?? 0) + 1); }
      if (x > 0 && !seen[j - 1] && mask(j - 1)) { seen[j - 1] = 1; stack.push(j - 1); }
      if (x < w - 1 && !seen[j + 1] && mask(j + 1)) { seen[j + 1] = 1; stack.push(j + 1); }
      if (y > 0 && !seen[j - w] && mask(j - w)) { seen[j - w] = 1; stack.push(j - w); }
      if (y < h - 1 && !seen[j + w] && mask(j + w)) { seen[j + w] = 1; stack.push(j + w); }
    }
    b.cx = b.sx / b.n; b.cy = b.sy / b.n;
    if (b.n >= minPx) out.push(b);
  }
  return out;
}

/**
 * Rows of one ortho view: [{view, part, score (px x metres), text}]. Silhouette: each bbox edge of the model vs the
 * reference foreground; zone families: every reference component matched to the nearest unused model component of the
 * same family (largest first, <= 0.6 m) -> centre offset + size; an unmatched reference component is MISSING.
 * Metres are MODEL metres (the reference scaled by the module's sigma).
 */
export function viewRows({ v, spec, T, partId, fam, parts, table, map, sigma, words = {} }) {
  const { w, h } = map;
  const k = map.k * sigma;
  const V = v.toUpperCase();
  const toWorld = (dx, dy) => [0, 1, 2].map((a) => (dx * spec.right[a] + dy * spec.up[a]) / k);   // right / up px -> metres
  const worldAt = (X, Y) => toWorld(X - map.bx, map.by - Y);
  const rows = [];
  let mx0 = w, mx1 = -1, my0 = h, my1 = -1, tx0 = w, tx1 = -1, ty0 = h, ty1 = -1;
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) {
    const i = y * w + x;
    if (partId[i] >= 0) { if (x < mx0) mx0 = x; if (x > mx1) mx1 = x; if (y < my0) my0 = y; if (y > my1) my1 = y; }
    if (T.fg[i]) { if (x < tx0) tx0 = x; if (x > tx1) tx1 = x; if (y < ty0) ty0 = y; if (y > ty1) ty1 = y; }
  }
  if (mx1 >= 0 && tx1 >= 0) {
    const edgePart = (test) => {
      const c = new Map();
      for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) {
        const p = partId[y * w + x];
        if (p >= 0 && test(x, y)) c.set(p, (c.get(p) ?? 0) + 1);
      }
      return [...c.entries()].sort((p, q) => q[1] - p[1])[0]?.[0];
    };
    for (const [mE, tE, sgn, dir, test, len] of [
      [mx1, tx1, 1, spec.right, (x) => x >= mx1 - 1, my1 - my0], [mx0, tx0, -1, spec.right.map((c) => -c), (x) => x <= mx0 + 1, my1 - my0],
      [my0, ty0, -1, spec.up, (x, y) => y <= my0 + 1, mx1 - mx0], [my1, ty1, 1, spec.up.map((c) => -c), (x, y) => y >= my1 - 1, mx1 - mx0]]) {
      const over = (mE - tE) * sgn / k;           // + = the model reaches past the reference
      if (Math.abs(over) < ROW_M) continue;
      const a = dir.findIndex((c) => c !== 0);
      const p = edgePart(test);
      rows.push({ view: v, part: p !== undefined ? parts[p].id : "-", score: Math.abs(over) * len,
        text: `${V}: silhouette ${wordOf(words, a, dir[a])} edge ${r2(Math.abs(over))} m ${over > 0 ? "past" : "short of"} the reference${p !== undefined ? ` (part "${parts[p].id}" at that edge)` : ""}` });
    }
  }
  for (const f of table.zoneFams) {
    // the same opening on both sides: reference ink strokes (and equally thin model parts) are not components
    const t0 = new Uint8Array(w * h);
    const m0 = new Uint8Array(w * h);
    let any = false;
    for (let i = 0; i < w * h; i += 1) {
      if (T.fam[i] === f) { t0[i] = 1; any = true; }
      if (partId[i] >= 0 && fam[partId[i]] === f) { m0[i] = 1; any = true; }
    }
    if (!any) continue;
    const tm = openMask(t0, w, h);
    const mm = openMask(m0, w, h);
    const tb = blobs(w, h, (i) => tm[i] === 1).sort((a, b) => b.n - a.n);
    const mb = blobs(w, h, (i) => mm[i] === 1, (i) => partId[i]);
    const used = new Set();
    const fname = table.names[f];
    for (const t of tb) {
      let best = -1;
      let bd = Infinity;
      mb.forEach((m, j) => { if (used.has(j)) return; const d = Math.hypot(m.cx - t.cx, m.cy - t.cy); if (d < bd) { bd = d; best = j; } });
      if (best < 0 || bd / k > 0.6) {
        const c = worldAt(t.cx, t.cy);
        rows.push({ view: v, part: "-", score: t.n * 0.1, text: `${V}: MISSING ${fname} ${r2((t.x1 - t.x0 + 1) / k)} x ${r2((t.y1 - t.y0 + 1) / k)} m at (x ${r2(c[0])}, y ${r2(c[1])}, z ${r2(c[2])}) m` });
        continue;
      }
      used.add(best);
      const m = mb[best];
      const off = toWorld(m.cx - t.cx, t.cy - m.cy);
      const bits = dirWords(off, worldAt(m.cx, m.cy), words);
      const dw = (m.x1 - m.x0 - (t.x1 - t.x0)) / k, dh = (m.y1 - m.y0 - (t.y1 - t.y0)) / k;
      if (Math.abs(dw) >= ROW_M) bits.push(`${r2(Math.abs(dw))} m too ${dw > 0 ? "wide" : "narrow"} along ${"xyz"[spec.right.findIndex((c) => c !== 0)]}`);
      if (Math.abs(dh) >= ROW_M) bits.push(`${r2(Math.abs(dh))} m too ${dh > 0 ? "tall" : "short"} along ${"xyz"[spec.up.findIndex((c) => c !== 0)]}`);
      if (!bits.length) continue;
      const pid = parts[[...m.ids.entries()].sort((p, q) => q[1] - p[1])[0][0]].id;
      rows.push({ view: v, part: pid, score: t.n * Math.max(Math.hypot(...off), Math.abs(dw), Math.abs(dh)), text: `${V}: part "${pid}" (${fname}) ${bits.join(", ")}` });
    }
  }
  return rows;
}

// ---------------------------------------------------------------------------
// WF v8 BLOB TABLE (research/v7/WF-V8-PLAN.md WP1): the silhouette differences of each view as numbers
// ---------------------------------------------------------------------------

export const BLOB_OPEN = 1;      // px: the opening that drops outline halos and anti-alias strips (< 3 px wide)
export const BLOB_MIN_PX = 20;   // px (the view's own resolution): smaller components are noise
export const BLOB_TOP = 5;       // rows per kind per view

/** The most frequent key of a Map key -> count (the smaller key on a tie), or -1 when empty. */
function modeOf(counts) {
  let best = -1, bn = 0;
  for (const [k, n] of counts) if (n > bn || (n === bn && k < best)) { best = k; bn = n; }
  return best;
}

/**
 * The model part nearest a blob: the blob (flooded from `seed` through `inBlob`) grows by 4-neighbour rings across
 * non-model px until a ring meets model px (partId >= 0); returns the most frequent part id of that ring, -1 when the
 * raster has no model px. stamp / queue: w x h scratch shared by the blobs of one table, `tag` unique per blob.
 */
function nearestPart(seed, inBlob, partId, w, h, stamp, queue, tag) {
  const n = w * h;
  let tail = 0;
  const grow = (k) => { if (stamp[k] !== tag && inBlob(k)) { stamp[k] = tag; queue[tail++] = k; } };
  stamp[seed] = tag; queue[tail++] = seed;
  for (let head = 0; head < tail; head += 1) {
    const j = queue[head], x = j % w;
    if (x > 0) grow(j - 1);
    if (x < w - 1) grow(j + 1);
    if (j >= w) grow(j - w);
    if (j + w < n) grow(j + w);
  }
  const hits = new Map();
  const ring = (k) => {
    if (stamp[k] === tag) return;
    stamp[k] = tag;
    if (partId[k] >= 0) hits.set(partId[k], (hits.get(partId[k]) ?? 0) + 1);
    else queue[tail++] = k;
  };
  for (let lo = 0, hi = tail; lo < hi; lo = hi, hi = tail) {
    for (let q = lo; q < hi; q += 1) {
      const j = queue[q], x = j % w;
      if (x > 0) ring(j - 1);
      if (x < w - 1) ring(j + 1);
      if (j >= w) ring(j - w);
      if (j + w < n) ring(j + w);
    }
    if (hits.size) return modeOf(hits);
  }
  return -1;
}

/**
 * The BLOB TABLE of one view: 4-neighbour components of refOnly (reference fg, no model: kind "missing") and modelOnly
 * (model, no reference fg: "extra") px, each mask opened by `open` px first (outline halos and anti-alias strips drop
 * out), don't-care px (care 0: drift rects / OCCLUDED) removed, >= minPx px, the `top` largest per kind. part: "extra" =
 * the most frequent part over the blob; "missing" = the nearest model part (grown from the blob border). share = px /
 * refPx (the view's reference-foreground px). place(b) -> the view's position fields ({bbox, centroid, ...}) of a blob
 * b = {x0, y0, x1, y1 (inclusive px), cx, cy (mean px)}.
 * @returns {{kind:string, px:number, share:number, bbox:any, centroid:number[], part:string|null}[]} largest first
 */
export function blobTable({ refFg, modelFg, partId, w, h, care = null, parts, refPx, place, open = BLOB_OPEN, minPx = BLOB_MIN_PX, top = BLOB_TOP }) {
  const miss = new Uint8Array(w * h);
  const extra = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i += 1) {
    if (care && !care[i]) continue;
    if (refFg[i]) { if (!modelFg[i]) miss[i] = 1; } else if (modelFg[i]) extra[i] = 1;
  }
  let stamp = null, queue = null, tag = 0;   // nearestPart scratch, allocated on the first missing blob
  const out = [];
  for (const [kind, raw] of [["missing", miss], ["extra", extra]]) {
    const m = open > 0 ? openMask(raw, w, h, open) : raw;
    const inBlob = (i) => m[i] === 1;
    const found = blobs(w, h, inBlob, kind === "extra" ? (i) => partId[i] : null, minPx).sort((a, b) => b.n - a.n || a.seed - b.seed).slice(0, top);
    for (const b of found) {
      if (kind === "missing" && !stamp) { stamp = new Int32Array(w * h); queue = new Int32Array(w * h); }
      const pid = kind === "extra" ? modeOf(b.ids) : nearestPart(b.seed, inBlob, partId, w, h, stamp, queue, ++tag);
      out.push({ kind, px: b.n, share: r4(refPx ? b.n / refPx : 0), ...place(b), part: pid >= 0 ? parts[pid]?.id ?? String(pid) : null });
    }
  }
  return out.sort((a, b) => b.px - a.px);
}

/**
 * metrics.blobs {<view>: blobTable rows}: every ortho on its page tile (the reference's own px, cropped by cropOf; bbox /
 * centroid in metres along the view's right / up via pxToView — reference metres, as measure.mjs comps; bboxPx = the
 * reference px) and the concept at the target's own px against the judged target (T0 raw, TA with the drift don't-care).
 */
function judgeBlobs({ reg, tiles, parts, T0, TA, conceptPartId, W, H }) {
  const out = {};
  for (const v of reg.names) {
    const t = tiles[v];
    const { img } = reg.views[v];
    const c = cropOf(reg, v);
    const refFg = new Uint8Array(t.w * t.h);
    let refPx = 0;
    for (let y = 0; y < t.h; y += 1) for (let x = 0; x < t.w; x += 1) if (img.fam[(y + c.y0) * img.w + x + c.x0] !== 0) { refFg[y * t.w + x] = 1; refPx += 1; }
    const rects = driftRects(reg.table, v);
    const care = rects ? careMask(rects.map(([x0, y0, x1, y1]) => [x0 - c.x0, y0 - c.y0, x1 - c.x0, y1 - c.y0]), t.w, t.h) : null;
    const place = (b) => {
      const X0 = b.x0 + c.x0, Y0 = b.y0 + c.y0, X1 = b.x1 + 1 + c.x0, Y1 = b.y1 + 1 + c.y0;
      const [r0, u1] = pxToView(reg, v, X0, Y0);
      const [r1_, u0] = pxToView(reg, v, X1, Y1);
      return { bbox: { right: [r3(r0), r3(r1_)], up: [r3(u0), r3(u1)] }, centroid: pxToView(reg, v, b.cx + 0.5 + c.x0, b.cy + 0.5 + c.y0).map(r3), bboxPx: [X0, Y0, X1, Y1] };
    };
    out[v] = blobTable({ refFg, modelFg: t.fg, partId: t.partId, w: t.w, h: t.h, care, parts, refPx, place });
  }
  const n = W * H;
  const refFg = new Uint8Array(n);
  const modelFg = new Uint8Array(n);
  let care = null, refPx = 0;
  for (let i = 0; i < n; i += 1) {
    if (T0[i] === SUBJECT) refPx += 1;
    if (TA[i] === SUBJECT) refFg[i] = 1;
    if (conceptPartId[i] >= 0) modelFg[i] = 1;
    if (TA[i] === OCCLUDED) { care ??= new Uint8Array(n).fill(1); care[i] = 0; }
  }
  out.concept = blobTable({ refFg, modelFg, partId: conceptPartId, w: W, h: H, care, parts, refPx,
    place: (b) => ({ bbox: [b.x0, b.y0, b.x1 + 1, b.y1 + 1], centroid: [r1(b.cx + 0.5), r1(b.cy + 0.5)] }) });
  return out;
}

/** One printed line of a blob-table row of view `v` (orthos: metres along the view's right / up; concept: px). */
export function blobLine(v, b) {
  const f = (x) => x.toFixed(3);
  const where = Array.isArray(b.bbox)
    ? `px x ${b.bbox[0]}..${b.bbox[2]} y ${b.bbox[1]}..${b.bbox[3]} · at (${b.centroid.map(Math.round).join(", ")})`
    : `right ${f(b.bbox.right[0])}..${f(b.bbox.right[1])} up ${f(b.bbox.up[0])}..${f(b.bbox.up[1])} m · at (${b.centroid.map(f).join(", ")})`;
  return `blob ${v} ${b.kind} ${b.px} px ${(b.share * 100).toFixed(2)} % · ${where} · ${b.kind === "extra" ? "part" : "nearest part"} ${b.part ?? "-"}`;
}

/** WARN lines: the views whose drift rects cover more than DRIFT_MAX of the reference foreground. */
export function driftWarnings(metrics) {
  return Object.entries(metrics.views).filter(([, m]) => (m.drift ?? 0) > DRIFT_MAX)
    .map(([v, m]) => `WARN drift ${v}: the rects cover ${(m.drift * 100).toFixed(1)} % of the reference foreground (> ${DRIFT_MAX * 100} %: regenerate the view instead)`);
}

/** Best uniform model scale shared by the orthos (golden section on the mean silhouette IoU). */
function fitSigma(reg, meshes, size) {
  const f = (sg) => {
    let s = 0;
    for (const v of reg.names) {
      const m = viewMap(reg, v, size);
      const { partId } = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: m.k * sg, bx: m.bx, by: m.by }, m.w, m.h);
      s += iou(viewTarget(reg, v, size).fg, partId, { ids: true });
    }
    return s / reg.names.length;
  };
  let a = 0.6, b = 1.8;
  const g = (Math.sqrt(5) - 1) / 2;
  let c = b - g * (b - a), d = a + g * (b - a), fc = f(c), fd = f(d);
  for (let i = 0; i < 22; i += 1) {
    if (fc > fd) { b = d; d = c; fd = fc; c = b - g * (b - a); fc = f(c); } else { a = c; c = d; fc = fd; d = a + g * (b - a); fd = f(d); }
  }
  return (a + b) / 2;
}

/** A three-quarter cel tile (size x size) from the concept camera turned by azimuth (deg), framed on the model. */
function threeQuarter(parts, palette, meshes, turnDeg, camera, azimuth, size) {
  const br = cameraBasis(camera, azimuth);
  const back = turnFn(-turnDeg);   // render frame -> author frame (the inverse quarter turn)
  const right = back(br.right), up = back(br.up);
  const basis = { right, up, back: cross(right, up) };
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const { pos } of meshes) for (let i = 0; i < pos.length; i += 3) {
    const p = [pos[i], pos[i + 1], pos[i + 2]];
    const a = p[0] * right[0] + p[1] * right[1] + p[2] * right[2];
    const b = p[0] * up[0] + p[1] * up[1] + p[2] * up[2];
    if (a < x0) x0 = a; if (a > x1) x1 = a; if (b < y0) y0 = b; if (b > y1) y1 = b;
  }
  const k = 0.86 * size / Math.max(x1 - x0, y1 - y0);
  const map = { k, bx: size / 2 - k * (x0 + x1) / 2, by: size / 2 + k * (y0 + y1) / 2 };
  const { partId, shade, face } = rasterOrtho(meshes, basis, map, size, size, turnDeg);
  return shadeRGB(parts, palette, partId, shade, face, size, size);
}

/** Crop window (reference px) of an ortho tile: the reference foreground +- 40 px. */
export function cropOf(reg, v) {
  const { box, img } = reg.views[v];
  return { x0: Math.max(0, box.x0 - 40), x1: Math.min(img.w, box.x1 + 40), y0: Math.max(0, box.y0 - 40), y1: Math.min(img.h, box.y1 + 40) };
}
const crop = (rgb, W, c) => {
  const w = c.x1 - c.x0, h = c.y1 - c.y0;
  const out = Buffer.alloc(w * h * 3);
  for (let y = 0; y < h; y += 1) rgb.copy(out, y * w * 3, ((y + c.y0) * W + c.x0) * 3, ((y + c.y0) * W + c.x1) * 3);
  return { rgb: out, w, h };
};

/**
 * The model in every ortho at the reference's own resolution (cel RGB + fg mask + part ids, cropped like the reference
 * tiles).
 * @returns {{[view:string]: {rgb:Buffer, fg:Uint8Array, partId:Int32Array, w:number, h:number}}}
 */
export function orthoTiles(reg, parts, palette, meshes, sigma, turnDeg) {
  const tiles = {};
  for (const v of reg.names) {
    const { img } = reg.views[v];
    const M = viewMap(reg, v, img.w);
    const R = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: M.k * sigma, bx: M.bx, by: M.by }, M.w, M.h, turnDeg);
    const c = cropOf(reg, v);
    const t = crop(shadeRGB(parts, palette, R.partId, R.shade, R.face, M.w, M.h), M.w, c);
    t.fg = new Uint8Array(t.w * t.h);
    t.partId = new Int32Array(t.w * t.h);   // WF v8: the part of each tile px (-1 = none), for the blob table
    for (let y = 0; y < t.h; y += 1) for (let x = 0; x < t.w; x += 1) {
      const p = R.partId[(y + c.y0) * M.w + x + c.x0];
      t.partId[y * t.w + x] = p;
      t.fg[y * t.w + x] = p >= 0 ? 1 : 0;
    }
    tiles[v] = t;
  }
  return tiles;
}

/**
 * @param {{subjectId:string, modulePath?:string, built?:{meta, parts, frame}, tiles?:boolean, blobs?:boolean}} o  tiles:
 *   false skips the full-resolution tiles (metrics only); blobs: true adds metrics.blobs (the blob table, judgeBlobs)
 * @returns {Promise<{metrics:object, tiles:object, sigma:number}>}
 */
export async function judge({ subjectId, modulePath = null, built = null, tiles: withTiles = true, blobs: withBlobs = false }) {
  const { reg, table } = await loadTurnaround(subjectId);
  const S = loadSubject(subjectId);
  const rules = await rulesFor(S.klass);
  const { meta, parts, frame } = built ?? await buildModule(modulePath);
  const turnDeg = frontRotationDeg(meta.front);
  const { meshes } = meshParts(parts, 0);
  const sigma = fitSigma(reg, meshes, 256);
  const fam = partFamilies(parts, meta.palette, table);
  const metrics = { module: modulePath, sigma: r4(sigma), views: {} };
  const rows = [];
  for (const v of reg.names) {
    const m = viewMap(reg, v, JUDGE_SIZE);
    const { partId } = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: m.k * sigma, bx: m.bx, by: m.by }, m.w, m.h);
    const T = viewTarget(reg, v, JUDGE_SIZE);
    const s = viewScore(T, partId, fam, table);
    metrics.views[v] = { iou: r4(s.iou), agree: r4(s.agree), drift: r4(viewDrift(reg, v)), zone: r4(s.zone), fam: Object.fromEntries(Object.entries(s.fam).map(([k, x]) => [k, r4(x)])) };
    rows.push(...viewRows({ v, spec: reg.views[v].spec, T, partId, fam, parts, table, map: m, sigma, words: rules.axisWords }));
  }
  metrics.viewRows = rows.sort((a, b) => b.score - a.score);
  // symmetry: the class's symmetry view without the near-side-only parts vs its mirror about the right-axis origin
  const sym = rules.symmetry;
  if (sym && reg.names.includes(sym.view)) {
    const keep = parts.map((p) => !sym.exclude?.test(p.id));
    const m = viewMap(reg, sym.view, JUDGE_SIZE);
    const { partId } = rasterOrtho(meshes.filter((_, i) => keep[i]), basisOf(reg.views[sym.view].spec), { k: m.k * sigma, bx: m.bx, by: m.by }, m.w, m.h);
    let inter = 0, union = 0;
    for (let y = 0; y < m.h; y += 1) for (let x = 0; x < m.w; x += 1) {
      const xm = Math.round(2 * m.bx - x - 1);
      const a = partId[y * m.w + x] >= 0;
      const b = xm >= 0 && xm < m.w && partId[y * m.w + xm] >= 0;
      if (a && b) inter += 1;
      if (a || b) union += 1;
    }
    metrics.symmetry = r4(union ? inter / union : 0);
  }
  // the concept view: THE registered IoU at the target's own resolution (the subject's mask rule: fgMax, enclosedFg);
  // agree: the same with the concept's drift rects OCCLUDED (don't care); drift: the SUBJECT px share they cover
  const img = await readRGB(S.paths.target);
  const proj = await project({ subjectId, frame: "target", built: { meta, parts, frame } });
  const cOpts = maskOptions(table, "concept");
  const cRects = driftRects(table, "concept");
  const T0 = targetState(S, img, table.fgMax, cOpts);
  const TA = cRects ? targetState(S, img, table.fgMax, { ...cOpts, dontCare: cRects }) : T0;
  const cIoU = iou(T0, proj.partId, { ids: true });
  let subj = 0, masked = 0;
  if (cRects) for (let i = 0; i < T0.length; i += 1) if (T0[i] === SUBJECT) { subj += 1; if (TA[i] === OCCLUDED) masked += 1; }
  metrics.views.concept = { iou: r4(cIoU), agree: r4(cRects ? iou(TA, proj.partId, { ids: true }) : cIoU), drift: r4(subj ? masked / subj : 0) };
  metrics.checks = rules.checks(parts);
  metrics.placementRows = rules.rows(metrics.checks);
  const orthoIoU = reg.names.map((v) => metrics.views[v].iou);
  metrics.minOrtho = Math.min(...orthoIoU);
  metrics.minView = Math.min(metrics.minOrtho, metrics.views.concept.iou);
  metrics.minAgree = Math.min(...[...reg.names, "concept"].map((v) => metrics.views[v].agree));
  metrics.score = r4((CONCEPT_W * metrics.views.concept.iou + orthoIoU.reduce((a, b) => a + b, 0)) / (CONCEPT_W + orthoIoU.length));
  metrics.tris = parts.reduce((a, p) => a + p.solid.mesh().triVerts.length / 3, 0);
  const tiles = {};
  const ortho = withTiles || withBlobs ? orthoTiles(reg, parts, meta.palette, meshes, sigma, turnDeg) : null;
  if (withBlobs) metrics.blobs = judgeBlobs({ reg, tiles: ortho, parts, T0, TA, conceptPartId: proj.partId, W: img.w, H: img.h });
  if (withTiles) {
    Object.assign(tiles, ortho);
    const camera = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
    const TQ = 420;
    tiles.frontLeft = { rgb: threeQuarter(parts, meta.palette, meshes, turnDeg, camera, 0, TQ), w: TQ, h: TQ };
    tiles.rearRight = { rgb: threeQuarter(parts, meta.palette, meshes, turnDeg, camera, 180, TQ), w: TQ, h: TQ };
  }
  return { metrics, tiles, sigma, proj, parts, meta };
}

/** Reference tiles: the turnaround crops + the concept image (front-left); rear-right has none (grey). */
export async function referenceTiles(subjectId) {
  const { reg } = await loadTurnaround(subjectId);
  const S = loadSubject(subjectId);
  const tiles = {};
  for (const v of reg.names) {
    const { img } = reg.views[v];
    tiles[v] = crop(img.data, img.w, cropOf(reg, v));
  }
  const TQ = 420;
  const concept = await sharp(S.paths.target).removeAlpha().resize(TQ, TQ).raw().toBuffer();
  tiles.frontLeft = { rgb: concept, w: TQ, h: TQ };
  tiles.rearRight = { rgb: Buffer.alloc(TQ * TQ * 3, 235), w: TQ, h: TQ };
  return tiles;
}

/** Column order of a sheet: the subject's orthos (views.json order), then the two three-quarter tiles. */
export const sheetOrder = (reg) => [...reg.names, "frontLeft", "rearRight"];

/**
 * Compose rows of tiles (each row: {label, tiles, notes?: {view: text}, lines?: [text]}) into one PNG. Every tile is
 * scaled to rowH px high; a label strip sits above each row (+ one strip per extra line). `order` = the tile keys.
 */
export async function composeRows(rows, out, rowH = 220, order = null) {
  const gap = 10, labelH = 26, lineH = 20;
  order ??= Object.keys(rows[0].tiles);
  const scaled = [];
  let width = 0;
  for (const row of rows) {
    const items = [];
    let x = gap;
    for (const v of order) {
      const t = row.tiles[v];
      if (!t) continue;
      const w = Math.round(t.w * rowH / t.h);
      const png = await sharp(t.rgb, { raw: { width: t.w, height: t.h, channels: 3 } }).resize(w, rowH).png().toBuffer();
      items.push({ v, png, x, w });
      x += w + gap;
    }
    width = Math.max(width, x);
    scaled.push(items);
  }
  const rowTop = [];
  let height = gap;
  for (const row of rows) { rowTop.push(height); height += labelH + (row.lines?.length ?? 0) * lineH + rowH + gap; }
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const composites = [];
  let texts = "";
  rows.forEach((row, r) => {
    const y = rowTop[r];
    const top = y + labelH + (row.lines?.length ?? 0) * lineH;
    texts += `<text x="${gap}" y="${y + 18}" font-family="Arial" font-size="17" font-weight="bold" fill="#111">${esc(row.label)}</text>`;
    (row.lines ?? []).forEach((l, i) => { texts += `<text x="${gap}" y="${y + labelH + i * lineH + 15}" font-family="Arial" font-size="14" fill="#333">${esc(l)}</text>`; });
    for (const it of scaled[r]) {
      composites.push({ input: it.png, left: it.x, top });
      const note = row.notes?.[it.v];
      if (note) texts += `<text x="${it.x + 4}" y="${top + rowH - 6}" font-family="Arial" font-size="14" fill="#c00000">${esc(note)}</text>`;
    }
  });
  const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">${texts}</svg>`);
  fs.mkdirSync(path.dirname(path.resolve(ROOT, out)), { recursive: true });
  await sharp({ create: { width, height, channels: 3, background: { r: 255, g: 255, b: 255 } } }).composite([...composites, { input: svg, left: 0, top: 0 }]).png().toFile(path.resolve(ROOT, out));
}
