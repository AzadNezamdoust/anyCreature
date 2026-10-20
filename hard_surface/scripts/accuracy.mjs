#!/usr/bin/env node
// WORKFLOW v5 — V5-1 items 3 + 4: the ACCURACY REPORT (research/WF-V5-ACCURACY.md "100 %" metric).
//
//   node scripts/accuracy.mjs --subject pickup --module <path.mjs> [--json <accuracy.json>] [--no-floor]
//
// One row per INVENTORY ITEM of the module in the registered frame (scripts/registered.mjs, target px, full
// resolution, the three-state target): an item = the visible parts of one feature group (part id without its side /
// index suffix, one zone). Its ROI = the parts' visible px boxes, padded. Target side = the target px of the parts'
// colour FAMILY inside the ROI (raw zone labels: NO ink opening, no MIN_AREA, no residual floor — small features are
// measured, never erased), minus px another part of the same family draws. Per item:
//   count  target components vs parts (groups of >= 2 parts, or items under ROI_BIG px)
//   pos    centroid dx / dy px (+ metres at the fitted scale)      size  bbox dw / dh (% and px)
//   roiIoU THE registered IoU (registered.iou) inside the ROI     edgePx symmetric mean boundary distance (small items)
//   dE     CIEDE2000, flat palette colour vs the mean target colour over the item's eroded interior
// MISSING rows: measured layout feature keys (verified) that no part builds — with the READY call that builds them,
// else `needs helper <name>`. UNOWNED rows: target components (raw zone labels, >= UNOWNED_PX px, SUBJECT px only)
// that no item of their family covers (>= half the blob inside its ROI).
// Tolerances = max(spec, the item's NOISE FLOOR): the same module rendered flat into the target frame and measured AS
// the target (render-as-target), so a tolerance is never tighter than what the harness itself can reproduce.
// Summary: "N of M items exact" (M = items + MISSING rows); `exact` = every item exact, no MISSING, no UNOWNED.
// V5-4 item 3: dE is PER FACE {top, front, side} (the projector's face-orientation id pass): each face's eroded interior
// (target px of the item that its own part draws with that face, eroded 1 px, 2 px on items >= bigPx) against the
// palette colour of that face (a palette entry may be "#hex" or {top, front, side}); the row's dE = the worst face.
// V5-4 item 4: PER-FAMILY noise floor. A floor row is TRUSTED when its render-as-target IoU >= TRUST_IOU. The pos /
// size / edge / dE tolerances of EVERY item are max(spec, its FAMILY's MEDIAN trusted floor): one contaminated row (a
// roof ladder whose ROI holds an uncalibrated grey that classifies as iron: 18 px) never loosens itself nor its family,
// body families (median 0) stay at the bare spec, a thin family whose rows are all noisy gets its own fair floor. The
// roiIoU floor is the item's own (trusted) row, else the family median. Untrusted rows (BLIND_IOU..TRUST_IOU: the
// flat colour half-classifies, e.g. the V5-1 facade wall at 0.52) are listed; the summary max is kept for the record.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { ROOT, loadSubject } from "./subject.mjs";
import { classifyTargetPixels } from "./likeness.mjs";
import { FACES, NO_FACE, loadModule, project } from "./project.mjs";
import { OCCLUDED, SUBJECT, iou, readRGB, targetState } from "./registered.mjs";
import { opening, partFamilies } from "./residuals.mjs";

/**
 * V5-5 item 1 — the plan's spec (research/WF-V5-ACCURACY.md "Exactness diagnosis"), in fractions of the ANCHOR px
 * (registration px/m x L for vehicles, x the fitted W for buildings): pos 1.5 %, size 2 % (>= sizePx), dE 6,
 * edge chamfer 2.5 px on items under bigPx, else the size-aware IoU floor max(iouMin, 1 - 4 iouE / D), D = the target's
 * equivalent diameter. shiftPx: the per-item 2-D alignment search (item 7).
 */
export const SPEC = Object.freeze({ posFrac: 0.015, sizeFrac: 0.02, sizePx: 3, iouMin: 0.85, iouE: 2, edgePx: 2.5, dE: 6, bigPx: 4000, shiftPx: 3 });
/** V5-5 item 2: target px an ink opening strips (targetOf fam) — DON'T CARE, never target. */
export const INK = -3;
/** Unowned-blob census: components of at least this many px (full resolution). */
export const UNOWNED_PX = 60;
/** Render-as-target IoU under which an item is harness-blind (its flat colour does not classify to its family). */
export const BLIND_IOU = 0.5;
/** V5-4 item 4: render-as-target IoU from which an item's own floor row is trusted (else its family's floor applies). */
export const TRUST_IOU = 0.9;
/** V5-4 item 3: fewest eroded interior px a face needs before its colour is judged. */
export const FACE_MIN_PX = 25;
/** Feature layout-key prefixes that are massing / proportions, never an inventory item of their own. */
const NOT_FEATURES = new Set(["height", "width", "wheelbase", "chassis", "massing", "face", "sideOverFront", "iron", "frame", "crown", "cornice", "cab", "sill", "body", "profile"]);
/** A layout prefix -> the part id / role words that build it (lower case). */
const BUILT_BY = { bedWall: ["bed_side", "bed_wall"], hood: ["hood"], bed: ["bed"], window: ["window", "pane", "windshield", "side_", "row"], headlight: ["headlight", "lamp"], wheel: ["wheel", "tyre"], stopArm: ["stoparm"], turn: ["turn"], marker: ["marker"],
  ladder: ["ladder"], landing: ["landing", "deck"], storefront: ["storefront", "shop"], signbox: ["sign"], ac: ["ac"], door: ["door"], awning: ["awning"], grille: ["grille"], mirror: ["mirror"], bumper: ["bumper"] };

const r2 = (v) => Math.round(v * 100) / 100;
const r3 = (v) => Math.round(v * 1000) / 1000;

// ---------------------------------------------------------------------------
// colour
// ---------------------------------------------------------------------------

function lab([r, g, b]) {
  const lin = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const [R, G, B] = [lin(r), lin(g), lin(b)];
  const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116);
  const x = f((0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.95047);
  const y = f(0.2126 * R + 0.7152 * G + 0.0722 * B);
  const z = f((0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.08883);
  return [116 * y - 16, 500 * (x - y), 200 * (y - z)];
}

/** CIEDE2000 between two sRGB triples. */
export function deltaE2000(rgb1, rgb2) {
  const [L1, a1, b1] = lab(rgb1);
  const [L2, a2, b2] = lab(rgb2);
  const d = Math.PI / 180;
  const C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cb = (C1 + C2) / 2;
  const G = 0.5 * (1 - Math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)));
  const ap1 = (1 + G) * a1, ap2 = (1 + G) * a2;
  const Cp1 = Math.hypot(ap1, b1), Cp2 = Math.hypot(ap2, b2);
  const hp = (b, a) => { if (b === 0 && a === 0) return 0; const h = Math.atan2(b, a) / d; return h >= 0 ? h : h + 360; };
  const h1 = hp(b1, ap1), h2 = hp(b2, ap2);
  const dL = L2 - L1, dC = Cp2 - Cp1;
  let dh = 0;
  if (Cp1 * Cp2 !== 0) { dh = h2 - h1; if (dh > 180) dh -= 360; else if (dh < -180) dh += 360; }
  const dH = 2 * Math.sqrt(Cp1 * Cp2) * Math.sin((dh / 2) * d);
  const Lb = (L1 + L2) / 2, Cpb = (Cp1 + Cp2) / 2;
  let hb = h1 + h2;
  if (Cp1 * Cp2 !== 0) { if (Math.abs(h1 - h2) > 180) hb = h1 + h2 < 360 ? (h1 + h2 + 360) / 2 : (h1 + h2 - 360) / 2; else hb = (h1 + h2) / 2; }
  const T = 1 - 0.17 * Math.cos((hb - 30) * d) + 0.24 * Math.cos(2 * hb * d) + 0.32 * Math.cos((3 * hb + 6) * d) - 0.2 * Math.cos((4 * hb - 63) * d);
  const SL = 1 + (0.015 * (Lb - 50) ** 2) / Math.sqrt(20 + (Lb - 50) ** 2);
  const SC = 1 + 0.045 * Cpb, SH = 1 + 0.015 * Cpb * T;
  const RT = -2 * Math.sqrt(Cpb ** 7 / (Cpb ** 7 + 25 ** 7)) * Math.sin(60 * Math.exp(-(((hb - 275) / 25) ** 2)) * d);
  return Math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH));
}

export const hexRGB = (hex) => { const m = /^#?([\da-f]{6})$/i.exec(String(hex)); if (!m) return null; const n = parseInt(m[1], 16); return [n >> 16, (n >> 8) & 255, n & 255]; };

/**
 * V5-4 item 3: the colour a palette ENTRY paints on face `fid` (project.FACES index): "#hex" everywhere, or
 * {top, front, side} by face (bottom paints as side; a missing face falls back front -> side -> top).
 */
export function faceHex(entry, fid) {
  if (!entry || typeof entry !== "object") return entry ?? null;
  const name = FACES[fid === 3 ? 2 : fid] ?? "front";
  return entry[name] ?? entry.front ?? entry.side ?? entry.top ?? null;
}

// ---------------------------------------------------------------------------
// masks
// ---------------------------------------------------------------------------

/** 4-connected components of `mask` inside the box [x0, x1] x [y0, y1]: [{n, px:[i...], x0, y0, x1, y1, cx, cy}]. */
function componentsIn(mask, w, box, keepPx = false) {
  const { x0, y0, x1, y1 } = box;
  const seen = new Uint8Array((x1 - x0 + 1) * (y1 - y0 + 1));
  const out = [];
  const stack = [];
  const bw = x1 - x0 + 1;
  for (let y = y0; y <= y1; y += 1) {
    for (let x = x0; x <= x1; x += 1) {
      const s = (y - y0) * bw + (x - x0);
      if (seen[s] || !mask[y * w + x]) continue;
      const c = { n: 0, x0: x, y0: y, x1: x, y1: y, sx: 0, sy: 0, px: keepPx ? [] : null };
      seen[s] = 1;
      stack.push(x, y);
      while (stack.length) {
        const yy = stack.pop();
        const xx = stack.pop();
        c.n += 1; c.sx += xx; c.sy += yy;
        if (c.px) c.px.push(yy * w + xx);
        if (xx < c.x0) c.x0 = xx; if (xx > c.x1) c.x1 = xx; if (yy < c.y0) c.y0 = yy; if (yy > c.y1) c.y1 = yy;
        for (const [nx, ny] of [[xx - 1, yy], [xx + 1, yy], [xx, yy - 1], [xx, yy + 1]]) {
          if (nx < x0 || nx > x1 || ny < y0 || ny > y1) continue;
          const t = (ny - y0) * bw + (nx - x0);
          if (!seen[t] && mask[ny * w + nx]) { seen[t] = 1; stack.push(nx, ny); }
        }
      }
      c.cx = c.sx / c.n; c.cy = c.sy / c.n;
      out.push(c);
    }
  }
  return out;
}

function statsOf(mask, w, box) {
  let n = 0, sx = 0, sy = 0, x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1;
  for (let y = box.y0; y <= box.y1; y += 1) {
    for (let x = box.x0; x <= box.x1; x += 1) {
      if (!mask[y * w + x]) continue;
      n += 1; sx += x; sy += y;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
  }
  return n ? { n, cx: sx / n, cy: sy / n, w: x1 - x0 + 1, h: y1 - y0 + 1 } : { n: 0 };
}

/** The part-id group: the id without index / side segments (wheel_fl -> wheel, marker_3 -> marker, window_0_1_frame -> window_frame). */
export function groupOf(id) {
  let g = String(id).replace(/_\d+(?=_|$)/g, "");
  for (let k = 0; k < 3; k += 1) g = g.replace(/(_(fl|fr|rl|rr|l|r|left|right|near|far|front|rear)\d*|_\d+)$/i, "");
  return g.replace(/_$/, "") || String(id);
}

// ---------------------------------------------------------------------------
// the report
// ---------------------------------------------------------------------------

/** The target's per-px family (raw zone labels, no opening) and three-state mask for an image. */
export function targetOf(S, img, { polygon = true, palette = null, occluded = null, inkOpen = null } = {}) {
  const regions = paletteRegions(S, palette);
  const { label, names } = classifyTargetPixels(img, regions);
  const areaFamilies = S.cls.likeness?.areaFamilies ?? {};
  const famNames = [];
  const famOfZone = names.map((name) => {
    const z = name.split("~")[0];   // V5-4 item 4: a per-face palette colour classifies to its zone's region
    const f = Object.keys(areaFamilies).find((k) => areaFamilies[k].includes(z)) ?? z;
    if (!famNames.includes(f)) famNames.push(f);
    return famNames.indexOf(f);
  });
  const state = polygon ? targetState(S, img) : targetState(null, img);
  // V5-4 item 4: the render-as-target floor keeps the REAL target's don't-care band (a wall behind a neighbour is never
  // measured on the target, so its self-measure must not be either)
  if (occluded) for (let i = 0; i < state.length; i += 1) if (occluded[i] === OCCLUDED) state[i] = OCCLUDED;
  const fam = new Int32Array(img.w * img.h);
  for (let i = 0; i < fam.length; i += 1) fam[i] = state[i] !== SUBJECT ? -1 : label[i] >= 0 ? famOfZone[label[i]] : -2;
  // V5-5 item 2: INK STRIP — per family, the px that do not survive an opening of radius classes/<c>.json
  // likeness.inkOpen (vehicle 2, building 1) are outline strokes / AA slivers: DON'T CARE (INK, care 0), never target
  const r = inkOpen ?? S?.cls?.likeness?.inkOpen ?? 0;
  if (r > 0) {
    const m = new Uint8Array(fam.length);
    famNames.forEach((_, k) => {
      let any = 0;
      for (let i = 0; i < fam.length; i += 1) { m[i] = fam[i] === k ? 1 : 0; any |= m[i]; }
      if (!any) return;
      const kept = opening(m, img.w, img.h, r);
      for (let i = 0; i < fam.length; i += 1) if (m[i] && !kept[i]) fam[i] = INK;
    });
  }
  // V5-4 item 4: CARE = the px an item may be measured on: inside the classifier's subject boxes (outside them no
  // target px is ever labelled, so a render px there is unmeasurable, not excess) and not OCCLUDED
  const care = new Uint8Array(img.w * img.h);
  for (const [bx, by, bw, bh] of regions.subjectBoxes ?? regions.building ?? [[0, 0, img.w, img.h]]) {
    for (let y = Math.max(0, by); y < Math.min(img.h, by + bh); y += 1) for (let x = Math.max(0, bx); x < Math.min(img.w, bx + bw); x += 1) care[y * img.w + x] = 1;
  }
  for (let i = 0; i < care.length; i += 1) if (state[i] === OCCLUDED || fam[i] === INK) care[i] = 0;
  return { w: img.w, h: img.h, state, fam, famNames, famOfZone, zoneNames: names, label, care };
}

/**
 * V5-4 item 4 — PER-ZONE classifier calibration. regions.json holds ONE median per target zone, so a zone whose faces
 * are cel-shaded apart (facade coping top / front / side, the bus body top vs flank) half-classifies — on the target
 * and on the render-as-target alike. Every face colour of a per-face palette entry {top, front, side} (sampled from the
 * target under that zone's parts, calibrate-palette calibrateFaces) is added as an extra median "<region>~<face>" that
 * classifies to the zone's own region / family. Plain "#hex" entries add nothing (they are the regions medians).
 */
export function paletteRegions(S, palette) {
  const regions = S.readJson("regions");
  if (!palette) return regions;
  const regionOfKey = Object.fromEntries((S.cls.paletteZones ?? []).map((z) => [z.key, z.region]));
  const extra = {};
  for (const [key, entry] of Object.entries(palette)) {
    if (!entry || typeof entry !== "object") continue;
    const region = regionOfKey[key] ?? key;
    if (!regions.zones?.[region]) continue;
    for (const [face, hex] of Object.entries(entry)) {
      const rgb = hexRGB(hex);
      if (rgb) extra[`${region}~${face}`] = { _measured: rgb, rects: [] };
    }
  }
  return Object.keys(extra).length ? { ...regions, zones: { ...regions.zones, ...extra } } : regions;
}

/** V5-5 item 4: the floor render's ink (a dark outline stroke) and the default per-face shade (src/geom.js SHADE). */
export const FLOOR_INK = Object.freeze({ rgb: [34, 34, 34], upTint: 0.1, sideTint: -0.26 });   // MVP-STUB: one fixed ink colour

/**
 * The module rendered FLAT into the target frame (palette colour per part, white elsewhere) — render-as-target.
 * V5-5 item 4, `floor: true`: the NOISE-FLOOR render — a plain "#hex" entry is shaded per face (linear light: top
 * x (1 + upTint), bottom x (1 - upTint), side x (1 + sideTint); meta.shade overrides), a 2-px dark stroke is painted on
 * every part/part and part/background boundary, then a 1-px box blur — so the floor reproduces what the target's
 * outline ink, AA and cel steps cost the harness (a real, non-zero floor).
 */
export function flatRender(proj, { floor = false } = {}) {
  const { w, h, partId } = proj;
  const data = new Uint8Array(w * h * 3).fill(255);
  const lin = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const srgb = (v) => Math.max(0, Math.min(255, Math.round(255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055))));
  const sh = { ...FLOOR_INK, ...(proj.meta.shade ?? {}) };
  const faceMul = [1 + sh.upTint, 1, 1 + sh.sideTint, 1 - sh.upTint];
  // V5-4 item 3: per part, the colour of each face (a {top, front, side} palette entry paints by face)
  const cols = proj.parts.map((p) => [0, 1, 2, 3].map((f) => {
    const entry = proj.meta.palette?.[p.zone];
    const c = hexRGB(faceHex(entry, f)) ?? [128, 128, 128];
    return floor && (!entry || typeof entry !== "object") ? c.map((v) => srgb(lin(v) * faceMul[f])) : c;
  }));
  for (let i = 0; i < w * h; i += 1) {
    const p = partId[i];
    if (p < 0) continue;
    const c = cols[p][proj.face && proj.face[i] !== NO_FACE ? proj.face[i] : 1];
    data[i * 3] = c[0]; data[i * 3 + 1] = c[1]; data[i * 3 + 2] = c[2];
  }
  if (!floor) return { data, w, h, c: 3 };
  // the 2-px stroke: both px of every 4-neighbour pair whose part ids differ (part/part and part/background)
  const ink = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = y * w + x;
      if (x + 1 < w && partId[i] !== partId[i + 1] && (partId[i] >= 0 || partId[i + 1] >= 0)) { ink[i] = 1; ink[i + 1] = 1; }
      if (y + 1 < h && partId[i] !== partId[i + w] && (partId[i] >= 0 || partId[i + w] >= 0)) { ink[i] = 1; ink[i + w] = 1; }
    }
  }
  for (let i = 0; i < w * h; i += 1) if (ink[i]) { data[i * 3] = sh.rgb[0]; data[i * 3 + 1] = sh.rgb[1]; data[i * 3 + 2] = sh.rgb[2]; }
  // 1-px box blur (3 x 3 mean, clamped at the frame)
  const out = new Uint8Array(data.length);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      for (let c = 0; c < 3; c += 1) {
        let sum = 0, n = 0;
        for (let yy = Math.max(0, y - 1); yy <= Math.min(h - 1, y + 1); yy += 1) for (let xx = Math.max(0, x - 1); xx <= Math.min(w - 1, x + 1); xx += 1) { sum += data[(yy * w + xx) * 3 + c]; n += 1; }
        out[(y * w + x) * 3 + c] = Math.round(sum / n);
      }
    }
  }
  return { data: out, w, h, c: 3 };
}

/** Inventory items (the module's visible feature groups) with their ROI boxes, from a projection. */
function itemsOf(proj, S, T) {
  const { w, h, partId } = proj;
  const pf = partFamilies(S, proj.parts, { famOfZone: T.famOfZone, zoneNames: T.zoneNames });
  const vis = proj.parts.map(() => ({ n: 0, x0: Infinity, y0: Infinity, x1: -1, y1: -1 }));
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const p = partId[y * w + x];
      if (p < 0) continue;
      const v = vis[p];
      v.n += 1; if (x < v.x0) v.x0 = x; if (x > v.x1) v.x1 = x; if (y < v.y0) v.y0 = y; if (y > v.y1) v.y1 = y;
    }
  }
  const groups = new Map();
  proj.parts.forEach((part, p) => {
    if (vis[p].n < 4 || pf[p] < 0) return;
    const key = `${groupOf(part.id)}:${part.zone}`;
    if (!groups.has(key)) groups.set(key, { id: groupOf(part.id), zone: part.zone, role: part.role, family: pf[p], parts: [] });
    groups.get(key).parts.push(p);
  });
  const items = [];
  for (const g of groups.values()) {
    const boxes = g.parts.map((p) => {
      const v = vis[p];
      const pad = Math.min(40, Math.max(4, Math.round(0.25 * Math.max(v.x1 - v.x0 + 1, v.y1 - v.y0 + 1))));
      return { x0: Math.max(1, v.x0 - pad), y0: Math.max(1, v.y0 - pad), x1: Math.min(w - 2, v.x1 + pad), y1: Math.min(h - 2, v.y1 + pad) };
    });
    const box = { x0: Math.min(...boxes.map((b) => b.x0)), y0: Math.min(...boxes.map((b) => b.y0)), x1: Math.max(...boxes.map((b) => b.x1)), y1: Math.max(...boxes.map((b) => b.y1)) };
    items.push({ ...g, boxes, box, visible: g.parts.reduce((s, p) => s + vis[p].n, 0) });
  }
  return { items, pf };
}

/** Local 4-connected components of a bw x bh 0/1 mask: [[local index...], ...]. */
function localComponents(mask, bw) {
  const seen = new Uint8Array(mask.length);
  const out = [];
  const stack = [];
  for (let s = 0; s < mask.length; s += 1) {
    if (!mask[s] || seen[s]) continue;
    const px = [];
    seen[s] = 1; stack.push(s);
    while (stack.length) {
      const i = stack.pop();
      px.push(i);
      const x = i % bw;
      for (const j of [x > 0 ? i - 1 : -1, x < bw - 1 ? i + 1 : -1, i >= bw ? i - bw : -1, i + bw < mask.length ? i + bw : -1]) {
        if (j >= 0 && mask[j] && !seen[j]) { seen[j] = 1; stack.push(j); }
      }
    }
    out.push(px);
  }
  return out;
}

/** Symmetric mean boundary distance (px) of two local masks — V5-5 item 1: chamfer (distanceTo), not O(n^2). */
function chamferOf(a, b, bw, bh) {
  const ea = boundaryOf(a, bw, bh);
  const eb = boundaryOf(b, bw, bh);
  let na = 0, nb = 0;
  for (let i = 0; i < ea.length; i += 1) { na += ea[i]; nb += eb[i]; }
  if (!na || !nb) return null;
  const da = distanceTo(ea, bw, bh);
  const db = distanceTo(eb, bw, bh);
  let sa = 0, sb = 0;
  for (let i = 0; i < ea.length; i += 1) { if (ea[i]) sa += db[i]; if (eb[i]) sb += da[i]; }
  return (sa / na + sb / nb) / 2;
}

/** V5-5 item 3: a target component belongs to an item when it touches the render item dilated by this many px. */
export const DILATE_PX = 4;

// ---------------------------------------------------------------------------
// V5-7 item 1 — THIN FEATURES (frames, sashes, ironwork: 1-4 px strokes at the target's resolution). Region measures
// (IoU, bbox, components) cannot see them: the target draws them as outline INK around a 1-2 px fill whose colour does
// not classify. A thin item is judged on its CENTRELINE instead, and a repeated one (>= minParts parallel members:
// balusters, rungs, bars, steps) also on COUNT + PITCH from a projection profile. Opt-in per class
// (classes/<c>.json likeness.thin); a class without it is measured exactly as before.
//   thin     the render item's visible px (CARE) whose 95th-percentile inner distance <= widthPx / 2
//   centre   an INK chamfer in the item's corridor (<= DILATE_PX of its own boundary), (rt + tr) / 2: rt = mean distance
//            of the render's ink (both px of every visible part boundary, flatRender's floor stroke) to the target's
//            ink (luminance < inkLum), tr = the reverse; capped 3 x DILATE_PX
//   profile  repeated-member ROLES only (likeness.thin.profileRoles: rungs, balusters, treads, deck bars), STRAIGHT
//            members only (a ring surround is not two members); their common direction u (px PCA, resultant >= parallel), bins of 1 px across it (n); per bin the
//            share of target ink / render ink over the band the nearest member covers along u (its middle 70 %);
//            [1 2 1] smoothed; peaks >= peak, non-max suppressed within max(3, 0.75 pitch); count = peaks, pitch = their
//            median gap. Ink against ink: occluders crossing the band count on both sides alike.
// ---------------------------------------------------------------------------

/** Zhang-Suen thinning of a local 0/1 mask (bw x bh): the 1-px skeleton. */
export function skeletonOf(mask, bw, bh) {
  const m = Uint8Array.from(mask);
  const at = (x, y) => (x < 0 || y < 0 || x >= bw || y >= bh ? 0 : m[y * bw + x]);
  let changed = true;
  const del = [];
  for (let guard = 0; changed && guard < 200; guard += 1) {
    changed = false;
    for (const step of [0, 1]) {
      del.length = 0;
      for (let y = 0; y < bh; y += 1) {
        for (let x = 0; x < bw; x += 1) {
          if (!m[y * bw + x]) continue;
          const p = [at(x, y - 1), at(x + 1, y - 1), at(x + 1, y), at(x + 1, y + 1), at(x, y + 1), at(x - 1, y + 1), at(x - 1, y), at(x - 1, y - 1)];
          const B = p.reduce((s, v) => s + v, 0);
          if (B < 2 || B > 6) continue;
          let A = 0;
          for (let k = 0; k < 8; k += 1) if (!p[k] && p[(k + 1) % 8]) A += 1;
          if (A !== 1) continue;
          if (step === 0 ? (p[0] * p[2] * p[4] || p[2] * p[4] * p[6]) : (p[0] * p[2] * p[6] || p[0] * p[4] * p[6])) continue;
          del.push(y * bw + x);
        }
      }
      for (const i of del) m[i] = 0;
      if (del.length) changed = true;
    }
  }
  return m;
}

/** The ink mask (luminance < lum) of an image inside a local box. */
function inkIn(img, x0, y0, bw, bh, lum) {
  const out = new Uint8Array(bw * bh);
  for (let y = 0; y < bh; y += 1) {
    for (let x = 0; x < bw; x += 1) {
      const i = ((y + y0) * img.w + x + x0) * img.c;
      if (0.299 * img.data[i] + 0.587 * img.data[i + 1] + 0.114 * img.data[i + 2] < lum) out[y * bw + x] = 1;
    }
  }
  return out;
}

/** Peaks of a [1 2 1]-smoothed profile (>= floor), non-max suppressed within `sep` bins: sorted bin indices. */
function profilePeaks(cov, floor, sep) {
  const n = cov.length;
  const s = new Float64Array(n);
  for (let i = 0; i < n; i += 1) s[i] = ((cov[i - 1] ?? 0) + 2 * cov[i] + (cov[i + 1] ?? 0)) / 4;
  const cand = [];
  for (let i = 0; i < n; i += 1) if (s[i] >= floor && s[i] >= (s[i - 1] ?? 0) && s[i] > (s[i + 1] ?? 0)) cand.push(i);
  cand.sort((a, b) => s[b] - s[a] || a - b);
  const kept = [];
  for (const i of cand) if (kept.every((j) => Math.abs(i - j) >= sep)) kept.push(i);
  return kept.sort((a, b) => a - b);
}

/** The profile's pitch by autocorrelation: the smallest lag in [lo, hi] whose (mean-removed) autocorrelation is >= 80 %
 *  of the best one there; null without a positive peak. */
function autoPitch(c, lo, hi) {
  const n = c.length;
  const m = c.reduce((s, v) => s + v, 0) / Math.max(1, n);
  const d = c.map((v) => v - m);
  const ac = [];
  for (let L = Math.ceil(lo); L <= Math.min(Math.floor(hi), n - 3); L += 1) {
    let sum = 0;
    for (let i = 0; i + L < n; i += 1) sum += d[i] * d[i + L];
    ac.push([L, sum / (n - L)]);
  }
  const best = Math.max(0, ...ac.map(([, v]) => v));
  if (!(best > 0)) return null;
  const peaks = ac.filter(([, v], i) => v >= 0.8 * best && v >= (ac[i - 1]?.[1] ?? -Infinity) && v >= (ac[i + 1]?.[1] ?? -Infinity));
  return peaks.length ? peaks[0][0] : null;
}

const medianOf = (a) => { if (!a.length) return null; const b = [...a].sort((x, y) => x - y); return b[Math.floor((b.length - 1) / 2)]; };

/**
 * The thin measure of one item in its local window (see the block comment), or null when the item is not thin.
 * @param {{bw:number, bh:number, Rc:Uint8Array, E:Uint8Array, care:Uint8Array, pl:Int32Array, Tink:Uint8Array, Rink:Uint8Array}} o
 *   local masks: Rc = the item's render px on CARE, E = its boundary px, pl = the part index per px (-1 none), Tink =
 *   target ink, Rink = render ink.
 */
export function thinMeasure({ bw, bh, Rc, E, care, pl, Tink, Rink, role = null }, cfg) {
  const n = bw * bh;
  let nR = 0;
  for (let l = 0; l < n; l += 1) nR += Rc[l];
  if (nR < 6) return null;
  const notR = new Uint8Array(n);
  for (let l = 0; l < n; l += 1) notR[l] = Rc[l] ? 0 : 1;
  const dIn = distanceTo(notR, bw, bh);
  const inner = [];
  for (let l = 0; l < n; l += 1) if (Rc[l]) inner.push(dIn[l]);
  inner.sort((a, b) => a - b);
  const stroke = inner[Math.floor(0.95 * (inner.length - 1))] <= cfg.widthPx / 2;
  // INK chamfer inside the item's CORRIDOR (<= DILATE_PX of its own boundary E): the target's ink (luminance < inkLum)
  // against the RENDER's ink (both px of every visible part/part and part/background boundary — flatRender's floor
  // stroke), so the neighbours' outlines count on both sides alike
  const cap = 3 * DILATE_PX;
  let nE = 0;
  for (let l = 0; l < n; l += 1) nE += E[l];
  if (!nE) return null;
  const dE = distanceTo(E, bw, bh);
  const tI = new Uint8Array(n), rI = new Uint8Array(n);
  for (let l = 0; l < n; l += 1) { tI[l] = Tink[l] & care[l]; rI[l] = Rink[l] & care[l]; }
  const dT = distanceTo(tI, bw, bh), dR = distanceTo(rI, bw, bh);
  let rt = 0, nr = 0, tr = 0, nt = 0;
  for (let l = 0; l < n; l += 1) {
    if (dE[l] > DILATE_PX) continue;
    if (rI[l]) { rt += Math.min(cap, dT[l]); nr += 1; }
    if (tI[l]) { tr += Math.min(cap, dR[l]); nt += 1; }
  }
  const rtPx = nr ? rt / nr : cap, trPx = nt ? tr / nt : cap;
  const out = { stroke, widthPx: r2(2 * inner[Math.floor(0.95 * (inner.length - 1))]), centrePx: r2((rtPx + trPx) / 2), rtPx: r2(rtPx), trPx: r2(trPx), count: null, pitch: null };
  // the profile of a repeated item: per member, px PCA
  const mem = new Map();
  for (let l = 0; l < n; l += 1) {
    if (!Rc[l] || pl[l] < 0) continue;
    const x = l % bw, y = (l / bw) | 0;
    let s = mem.get(pl[l]);
    if (!s) mem.set(pl[l], s = { n: 0, sx: 0, sy: 0, sxx: 0, syy: 0, sxy: 0, pts: [] });
    s.n += 1; s.sx += x; s.sy += y; s.sxx += x * x; s.syy += y * y; s.sxy += x * y; s.pts.push(l);
  }
  const members = [...mem.values()].filter((s) => s.n >= 4);
  if (members.length < cfg.minParts || !(cfg.profileRoles ?? []).includes(role)) return out;
  let cx2 = 0, sy2 = 0, wsum = 0;
  for (const s of members) {
    const mx = s.sx / s.n, my = s.sy / s.n;
    const a = s.sxx / s.n - mx * mx, b = s.syy / s.n - my * my, c = s.sxy / s.n - mx * my;
    s.theta = 0.5 * Math.atan2(2 * c, a - b);
    s.mx = mx; s.my = my;
    cx2 += s.n * Math.cos(2 * s.theta); sy2 += s.n * Math.sin(2 * s.theta); wsum += s.n;
  }
  if (Math.hypot(cx2, sy2) / wsum < cfg.parallel) return out;
  const th = 0.5 * Math.atan2(sy2, cx2);
  const ux = Math.cos(th), uy = Math.sin(th), nx = -uy, ny = ux;
  // only STRAIGHT members are counted by the profile (>= 80 % of each one's px within widthPx / 2 + 1 of its own
  // axis): a window surround is a ring, its two jambs would count as two members
  for (const s of members) {
    const snx = -Math.sin(s.theta), sny = Math.cos(s.theta), c = s.mx * snx + s.my * sny;
    let near = 0;
    for (const l of s.pts) if (Math.abs((l % bw) * snx + ((l / bw) | 0) * sny - c) <= cfg.widthPx / 2 + 1) near += 1;
    if (near < 0.8 * s.n) return out;
  }
  for (const s of members) {
    s.t = s.mx * nx + s.my * ny;
    let a = Infinity, b = -Infinity;
    for (const l of s.pts) { const v = (l % bw) * ux + ((l / bw) | 0) * uy; if (v < a) a = v; if (v > b) b = v; }
    const m = 0.15 * (b - a);
    s.a = a + m; s.b = b - m;
  }
  members.sort((p, q) => p.t - q.t);
  const ts = [];
  for (const s of members) if (!ts.length || s.t - ts[ts.length - 1] >= 1.5) ts.push(s.t);
  const gaps = ts.slice(1).map((t, i) => t - ts[i]);
  const P = Math.max(4, medianOf(gaps) ?? 4);
  const tlo = ts[0] - P, nb = Math.ceil(ts[ts.length - 1] + P - tlo) + 1;
  const near = Array.from({ length: nb }, (_, k) => {
    const t = tlo + k;
    let best = members[0];
    for (const s of members) if (Math.abs(s.t - t) < Math.abs(best.t - t)) best = s;
    return best;
  });
  const tot = new Float64Array(nb), ti = new Float64Array(nb), tr2 = new Float64Array(nb);
  for (let l = 0; l < n; l += 1) {
    const x = l % bw, y = (l / bw) | 0;
    const k = Math.round(x * nx + y * ny - tlo);
    if (k < 0 || k >= nb) continue;
    const s = near[k];
    const v = x * ux + y * uy;
    if (v < s.a || v > s.b) continue;
    if (!care[l]) continue;
    tot[k] += 1; ti[k] += Tink[l]; tr2[k] += Rink[l];
  }
  const cov = (a) => Array.from(a, (v, k) => (tot[k] >= 2 ? v / tot[k] : 0));
  // one member = one peak (its two outline lines merge): both sides suppressed within 0.75 x the member pitch, so a
  // render that matches is counted at the same scale as the target. The target profile's own pitch by
  // AUTOCORRELATION (smallest lag within 80 % of the best, 0.4..2.5 x the render pitch) is reported (pitch.ac): it
  // names the pitch a wrong render should move to (it can lock onto the outline-line spacing of wide members)
  const cT = cov(ti);
  const ac = autoPitch(cT, Math.max(3, 0.4 * P), 2.5 * P);
  // a target DENSER than the render (its autocorrelation pitch >= 0.6 x the render's, below it) is counted at its own
  // pitch, both sides alike — else a render at twice the pitch would suppress every other target member
  const sep = Math.max(3, 0.75 * (ac && ac >= 0.6 * P ? Math.min(P, ac) : P));
  const pk = { target: profilePeaks(cT, cfg.peak, sep), render: profilePeaks(cov(tr2), cfg.peak, sep) };
  const pitchOf = (p) => (p.length >= 2 ? r2(medianOf(p.slice(1).map((v, i) => v - p[i]))) : null);
  out.count = { target: pk.target.length, render: pk.render.length };
  out.pitch = { target: pitchOf(pk.target), render: pitchOf(pk.render), ac };
  return out;
}

/** V5-7 item 1: judge a thin / blind row on its ink measure (row.ink): centre <= centrePx, count equal, pitch within max(pitchPx, pitchFrac x pitch). The
 * render side is the render's own INK map, so the measure needs no noise floor (render-as-target is 0 by construction). */
export function judgeThin(row, cfg) {
  const t = row.ink;
  const fails = [];
  if (!(t.centrePx <= cfg.centrePx)) fails.push("centre");
  if (t.count && t.count.target !== t.count.render) fails.push("count");
  let tolP = null;
  if (t.pitch?.target && t.pitch?.render) {
    tolP = Math.max(cfg.pitchPx, cfg.pitchFrac * t.pitch.target);
    if (Math.abs(t.pitch.render - t.pitch.target) > tolP) fails.push("pitch");
  }
  return { status: fails.length ? "off" : "exact", fails, tol: { centrePx: cfg.centrePx, pitchPx: tolP === null ? null : r2(tolP) } };
}

/**
 * Measure every item against one target (image). Per item, in the item's padded ROI box (local window):
 *   V5-5 item 3: target = the COMPONENTS of the family's target px (minus px another part of the family draws) that
 *     touch dilate(render item, DILATE_PX) — a neighbouring same-family item or a stroke in the pad is not the item.
 *   V5-5 item 7: the render item is ALIGNED first (integer 2-D shift search +/- spec.shiftPx maximising the ROI IoU,
 *     parabolic sub-px refinement); pos = the alignment offset (the centroid offset on an axis whose shift saturates),
 *     and IoU / size / count / edge / dE are scored at the aligned shift.
 *   V5-5 item 5: dE per face over the interior eroded 2 px (3 on items >= bigPx); a face under FACE_MIN_PX px is
 *     skipped; an item with no face left is not judged on colour (dE null, dESkipped).
 */
function measureItems(proj, S, T, img, items, pf, spec = SPEC) {
  const { w, partId } = proj;
  const rows = [];
  const K = spec.shiftPx ?? 3;
  for (const it of items) {
    const own = new Set(it.parts);
    const { x0, y0, x1, y1 } = it.box;
    const bw = x1 - x0 + 1, bh = y1 - y0 + 1, n = bw * bh;
    const R0 = new Uint8Array(n);     // the item's own render px (in its boxes, care or not: the shift may move them)
    const T0 = new Uint8Array(n);     // the family's target px (care only)
    const care = new Uint8Array(n);   // 1 = measurable (in the boxes, CARE)
    const pl = new Int32Array(n).fill(-1);   // V5-7: the part per local render px (thin members)
    for (let y = y0; y <= y1; y += 1) {
      for (let x = x0; x <= x1; x += 1) {
        if (!it.boxes.some((b) => x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1)) continue;
        const i = y * w + x, l = (y - y0) * bw + (x - x0);
        const p = partId[i];
        if (own.has(p)) { R0[l] = 1; pl[l] = p; }
        if (T.care && !T.care[i]) continue;
        care[l] = 1;
        const other = p >= 0 && !own.has(p) && pf[p] === it.family;
        if (T.fam[i] === it.family && !other) T0[l] = 1;
      }
    }
    // item 3: target components that touch the dilated render item
    const dR = distanceTo(R0, bw, bh);
    const Tm = new Uint8Array(n);
    for (const c of localComponents(T0, bw)) if (c.some((l) => dR[l] <= DILATE_PX)) for (const l of c) Tm[l] = 1;
    // item 7: the alignment shift search
    const rPx = [];
    for (let l = 0; l < n; l += 1) if (R0[l]) rPx.push(l);
    let nT = 0;
    for (let l = 0; l < n; l += 1) nT += Tm[l];
    const iouAt = (sx, sy) => {
      let inter = 0, nr = 0;
      for (const l of rPx) {
        const x = (l % bw) + sx, y = ((l / bw) | 0) + sy;
        if (x < 0 || y < 0 || x >= bw || y >= bh) continue;
        const m = y * bw + x;
        if (!care[m]) continue;
        nr += 1; inter += Tm[m];
      }
      const u = nT + nr - inter;
      return u ? inter / u : 0;
    };
    let best = { sx: 0, sy: 0, v: iouAt(0, 0) };
    const grid = new Map([["0,0", best.v]]);
    if (rPx.length && nT) {
      for (let sy = -K; sy <= K; sy += 1) {
        for (let sx = -K; sx <= K; sx += 1) {
          if (!sx && !sy) continue;
          const v = iouAt(sx, sy);
          grid.set(`${sx},${sy}`, v);
          if (v > best.v + 1e-9 || (Math.abs(v - best.v) <= 1e-9 && Math.hypot(sx, sy) < Math.hypot(best.sx, best.sy))) best = { sx, sy, v };
        }
      }
    }
    const { sx, sy } = best;
    const sub = (a, b0, c) => { const d = a - 2 * b0 + c; return d < 0 ? Math.max(-0.5, Math.min(0.5, (a - c) / (2 * d))) : 0; };
    const fx = Math.abs(sx) < K ? sub(grid.get(`${sx - 1},${sy}`) ?? best.v, best.v, grid.get(`${sx + 1},${sy}`) ?? best.v) : 0;
    const fy = Math.abs(sy) < K ? sub(grid.get(`${sx},${sy - 1}`) ?? best.v, best.v, grid.get(`${sx},${sy + 1}`) ?? best.v) : 0;
    // the aligned render item (care px only); src = the render's own full-frame px (its face id)
    const R = new Uint8Array(n);
    const src = new Int32Array(n).fill(-1);
    for (const l of rPx) {
      const x = (l % bw) + sx, y = ((l / bw) | 0) + sy;
      if (x < 0 || y < 0 || x >= bw || y >= bh) continue;
      const m = y * bw + x;
      if (!care[m]) continue;
      R[m] = 1; src[m] = (y0 + ((l / bw) | 0)) * w + x0 + (l % bw);
    }
    const box = { x0: 0, y0: 0, x1: bw - 1, y1: bh - 1 };
    const rs = statsOf(R, bw, box);
    const ts = statsOf(Tm, bw, box);
    const R0c = new Uint8Array(n);   // the unaligned render item on CARE px (the saturated-shift centroid)
    for (let l = 0; l < n; l += 1) R0c[l] = R0[l] & care[l];
    const r0s = statsOf(R0c, bw, box);
    const small = ts.n < spec.bigPx;
    // count: target blobs of the family (>= a quarter of the mean part's px) vs parts
    const minBlob = Math.max(3, Math.round(0.25 * rs.n / Math.max(1, it.parts.length)));
    const counted = it.parts.length >= 2 || small;
    const tCount = counted ? componentsIn(Tm, bw, box).filter((c) => c.n >= minBlob).length : null;
    const rCount = counted ? componentsIn(R, bw, box).filter((c) => c.n >= minBlob).length : null;
    // item 5: colour per face over the eroded interior of target AND aligned render
    const entry = proj.meta.palette?.[it.zone];
    const er = ts.n >= spec.bigPx ? 3 : 2;
    const dEFaces = {};
    const fk = new Int8Array(n).fill(-1);
    for (let l = 0; l < n; l += 1) if (Tm[l] && R[l]) { const f = proj.face ? proj.face[src[l]] : 1; fk[l] = f === NO_FACE ? -1 : f === 3 ? 2 : f; }
    for (let f = 0; f < 3; f += 1) {
      let fr = 0, fg = 0, fb = 0, fn = 0;
      for (let y = er; y < bh - er; y += 1) {
        for (let x = er; x < bw - er; x += 1) {
          const l = y * bw + x;
          if (fk[l] !== f) continue;
          let inside = true;
          for (let dy = -er; dy <= er && inside; dy += 1) for (let dx = -er; dx <= er; dx += 1) if (fk[l + dy * bw + dx] !== f) { inside = false; break; }
          if (!inside) continue;
          const i = (y + y0) * w + x + x0;
          fr += img.data[i * img.c]; fg += img.data[i * img.c + 1]; fb += img.data[i * img.c + 2]; fn += 1;
        }
      }
      if (fn < FACE_MIN_PX) continue;
      const col = hexRGB(faceHex(entry, f));
      dEFaces[FACES[f]] = col ? r2(deltaE2000([fr / fn, fg / fn, fb / fn], col)) : null;
    }
    const dVals = Object.values(dEFaces);
    const dE = dVals.length && dVals.every((v) => v !== null) ? Math.max(...dVals) : null;
    const pxPerM = proj.registration?.s ?? proj.pxPerM;
    const row = {
      id: it.zone === it.id ? it.id : `${it.id}[${it.zone}]`, kind: it.role ?? "part", zone: it.zone, parts: it.parts.length,
      count: { target: tCount, render: rCount },
      px: { target: ts.n, render: rs.n },
      roi: [x0, y0, x1, y1],
    };
    // V5-4 item 2: what the per-feature FIT needs to re-score this item (not written to accuracy.json)
    Object.defineProperty(row, "feature", { enumerable: false, value: { family: it.family, boxes: it.boxes, box: it.box, partIds: it.parts.map((p) => proj.parts[p].id) } });
    if (ts.n && rs.n) {
      // pos: the alignment offset (render - target), sub-px; the centroid offset on an axis whose shift saturated
      const dx = Math.abs(sx) < K ? -(sx + fx) : r0s.cx - ts.cx;
      const dy = Math.abs(sy) < K ? -(sy + fy) : r0s.cy - ts.cy;
      row.pos = { dxPx: r2(dx), dyPx: r2(dy), dxM: r3(dx / pxPerM), dyM: r3(dy / pxPerM) };
      row.shift = [sx, sy];
      row.size = { dwPx: rs.w - ts.w, dhPx: rs.h - ts.h, dwPct: r2(100 * (rs.w - ts.w) / ts.w), dhPct: r2(100 * (rs.h - ts.h) / ts.h), target: [ts.w, ts.h], render: [rs.w, rs.h] };
      row.roiIoU = r3(best.v);
      row.edgePx = small ? r2(chamferOf(Tm, R, bw, bh) ?? Infinity) : null;
    } else {
      row.pos = null; row.size = null; row.roiIoU = 0; row.edgePx = null;
    }
    row.dE = dE;
    if (dVals.length) row.dEFaces = dEFaces;
    else row.dESkipped = `no face interior >= ${FACE_MIN_PX} px`;
    // V5-7 item 1: the thin measure (classes/<c>.json likeness.thin opts in)
    const thinCfg = S?.cls?.likeness?.thin;
    if (thinCfg) {
      const Rc = new Uint8Array(n);
      for (let l = 0; l < n; l += 1) Rc[l] = R0[l] & care[l];
      const E = new Uint8Array(n);
      for (let l = 0; l < n; l += 1) {
        if (!Rc[l]) continue;
        const i = (y0 + ((l / bw) | 0)) * w + x0 + (l % bw);
        if (partId[i - 1] !== pl[l] || partId[i + 1] !== pl[l] || partId[i - w] !== pl[l] || partId[i + w] !== pl[l]) E[l] = 1;
      }
      const Tink = inkIn(img, x0, y0, bw, bh, thinCfg.inkLum);
      const Rink = new Uint8Array(n);
      for (let l = 0; l < n; l += 1) {
        const i = (y0 + ((l / bw) | 0)) * w + x0 + (l % bw);
        const q = partId[i];
        if ((q >= 0 || partId[i - 1] >= 0) && partId[i - 1] !== q) Rink[l] = 1;
        else if ((q >= 0 || partId[i + 1] >= 0) && partId[i + 1] !== q) Rink[l] = 1;
        else if ((q >= 0 || partId[i - w] >= 0) && partId[i - w] !== q) Rink[l] = 1;
        else if ((q >= 0 || partId[i + w] >= 0) && partId[i + w] !== q) Rink[l] = 1;
      }
      const th = thinMeasure({ bw, bh, Rc, E, care, pl, Tink, Rink, role: it.role }, thinCfg);
      if (th) row.ink = th;
    }
    rows.push(row);
  }
  return rows;
}

/** V5-4 item 2: 8-neighbour chamfer distance (1, sqrt 2) of every px to the nearest set px of `mask` (w x h). */
export function distanceTo(mask, w, h) {
  const D = new Float32Array(w * h);
  const BIG = 1e9;
  for (let i = 0; i < D.length; i += 1) D[i] = mask[i] ? 0 : BIG;
  const S2 = Math.SQRT2;
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = y * w + x;
      let d = D[i];
      if (x > 0 && D[i - 1] + 1 < d) d = D[i - 1] + 1;
      if (y > 0) {
        if (D[i - w] + 1 < d) d = D[i - w] + 1;
        if (x > 0 && D[i - w - 1] + S2 < d) d = D[i - w - 1] + S2;
        if (x < w - 1 && D[i - w + 1] + S2 < d) d = D[i - w + 1] + S2;
      }
      D[i] = d;
    }
  }
  for (let y = h - 1; y >= 0; y -= 1) {
    for (let x = w - 1; x >= 0; x -= 1) {
      const i = y * w + x;
      let d = D[i];
      if (x < w - 1 && D[i + 1] + 1 < d) d = D[i + 1] + 1;
      if (y < h - 1) {
        if (D[i + w] + 1 < d) d = D[i + w] + 1;
        if (x < w - 1 && D[i + w + 1] + S2 < d) d = D[i + w + 1] + S2;
        if (x > 0 && D[i + w - 1] + S2 < d) d = D[i + w - 1] + S2;
      }
      D[i] = d;
    }
  }
  return D;
}

/** Boundary px of a 0/1 mask (a set px with a 4-neighbour unset or off the window). */
function boundaryOf(mask, w, h) {
  const e = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = y * w + x;
      if (mask[i] && (x === 0 || y === 0 || x === w - 1 || y === h - 1 || !mask[i - 1] || !mask[i + 1] || !mask[i - w] || !mask[i + w])) e[i] = 1;
    }
  }
  return e;
}

/** V5-4 item 2: weights of the per-feature score's edge-chamfer and centroid/equivalent-diameter terms. */
export const FEATURE_W = Object.freeze({ chamfer: 0.5, centre: 0.5 });

/**
 * V5-4 item 2 — ONE inventory item's per-feature score in an ROI window projection (project({roi})), full resolution,
 * the same masks as measureItems: render = the item's own parts; target = the item family's target px inside its ROI
 * boxes minus px another part of that family draws; OCCLUDED don't care.
 *   score = roiIoU - W.chamfer min(1, chamfer / D) - W.centre min(1, (|centroid d| + |D_render - D|) / D)
 * D = the target's equivalent diameter (>= 4 px), chamfer = symmetric mean boundary distance (px).
 * @param {object} win project() result with `roi`   @param {object} T targetOf() of the target image
 * @param {{family:number, boxes:object[], partIds:string[]}} feat   @param {Int32Array} pf part -> family (win.parts)
 */
export function featureScore(win, T, feat, pf) {
  const { w, h, partId } = win;
  const { x0, y0 } = win.roi ?? { x0: 0, y0: 0 };
  const own = new Uint8Array(win.parts.length);
  const ids = new Set(feat.partIds);
  win.parts.forEach((p, k) => { if (ids.has(p.id)) own[k] = 1; });
  const R = new Uint8Array(w * h);
  const Tm = new Uint8Array(w * h);
  let inter = 0, union = 0, nr = 0, nt = 0, rx = 0, ry = 0, tx = 0, ty = 0;
  for (let y = 0; y < h; y += 1) {
    const Y = y + y0;
    for (let x = 0; x < w; x += 1) {
      const X = x + x0;
      if (!feat.boxes.some((b) => X >= b.x0 && X <= b.x1 && Y >= b.y0 && Y <= b.y1)) continue;
      const i = y * w + x;
      const g = Y * T.w + X;
      if (T.care && !T.care[g]) continue;   // don't care (OCCLUDED / outside the classifier's subject boxes)
      const p = partId[i];
      const r = p >= 0 && own[p] === 1;
      const other = p >= 0 && !own[p] && pf[p] === feat.family;
      const t = T.fam[g] === feat.family && !other;
      if (r) R[i] = 1;
      if (t) Tm[i] = 1;
      if (T.state[g] === OCCLUDED) continue;
      if (r) { nr += 1; rx += x; ry += y; }
      if (t) { nt += 1; tx += x; ty += y; }
      if (r && t) inter += 1;
      if (r || t) union += 1;
    }
  }
  if (!nt) return { score: nr ? -1 : 0, roiIoU: 0, chamferPx: null, centrePx: null, diamPx: null };
  const roiIoU = union ? inter / union : 0;
  const D = Math.max(4, 2 * Math.sqrt(nt / Math.PI));
  if (!nr) return { score: -1, roiIoU: 0, chamferPx: null, centrePx: null, diamPx: null };
  const eR = boundaryOf(R, w, h);
  const eT = boundaryOf(Tm, w, h);
  const dR = distanceTo(eR, w, h);
  const dT = distanceTo(eT, w, h);
  let sa = 0, na = 0, sb = 0, nb = 0;
  for (let i = 0; i < w * h; i += 1) {
    if (eR[i]) { sa += dT[i]; na += 1; }
    if (eT[i]) { sb += dR[i]; nb += 1; }
  }
  const chamferPx = (sa / Math.max(1, na) + sb / Math.max(1, nb)) / 2;
  const centrePx = Math.hypot(rx / nr - tx / nt, ry / nr - ty / nt);
  const diamPx = 2 * Math.sqrt(nr / Math.PI) - 2 * Math.sqrt(nt / Math.PI);
  const score = roiIoU - FEATURE_W.chamfer * Math.min(1, chamferPx / D) - FEATURE_W.centre * Math.min(1, (centrePx + Math.abs(diamPx)) / D);
  return { score, roiIoU: r3(roiIoU), chamferPx: r2(chamferPx), centrePx: r2(centrePx), diamPx: r2(diamPx) };
}

/**
 * The ANCHOR px (V5-5 item 1): the registration's px/m (the module's fitted similarity applied) x the anchor length —
 * vehicles L (the registration anchor), buildings the module's fitted W (KNOBS.W, else the anchor W).
 */
export async function anchorPxOf(S, proj, modulePath) {
  const reg = proj.registration;
  if (!reg?.anchor) return null;
  let m = S.klass === "vehicle" ? reg.anchor.L : reg.anchor.W;
  if (S.klass !== "vehicle") {
    try { const mod = await loadModule(modulePath); if (Number.isFinite(mod.KNOBS?.W?.v)) m = mod.KNOBS.W.v; } catch { /* the anchor W */ }
  }
  return Number.isFinite(m) ? r2((proj.pxPerM ?? reg.s) * m) : null;
}

/**
 * Judge one row against the spec widened by its noise floor row (render-as-target). V5-5 item 1: pos / size in
 * fractions of the anchor px; the IoU floor is size-aware (items >= bigPx), items under bigPx are judged by the edge
 * chamfer; dE is not judged on an item with no face interior (dESkipped).
 */
export function judgeRow(row, floor, spec = SPEC, anchorPx = null) {
  const fails = [];
  if (!row.pos) return { status: "absent", fails: ["no target px"] };
  const A = anchorPx ?? 0;
  const D = 2 * Math.sqrt(row.px.target / Math.PI);
  const tol = {
    pos: Math.max(spec.posFrac * A, floor?.pos ? Math.max(Math.abs(floor.pos.dxPx), Math.abs(floor.pos.dyPx)) : 0),
    size: Math.max(spec.sizePx, spec.sizeFrac * A, floor?.size ? Math.max(Math.abs(floor.size.dwPx), Math.abs(floor.size.dhPx)) : 0),
    iou: Math.min(Math.max(spec.iouMin, 1 - (4 * spec.iouE) / Math.max(1, D)), floor?.roiIoU ?? 1),
    edge: Math.max(spec.edgePx, floor?.edgePx ?? 0),
    dE: Math.max(spec.dE, floor?.dE ?? 0),
  };
  const big = row.px.target >= spec.bigPx;
  if (row.count.target !== null && row.count.target !== row.count.render) fails.push("count");
  if (Math.abs(row.pos.dxPx) > tol.pos || Math.abs(row.pos.dyPx) > tol.pos) fails.push("pos");
  if (Math.abs(row.size.dwPx) > tol.size || Math.abs(row.size.dhPx) > tol.size) fails.push("size");
  if (big ? row.roiIoU < tol.iou : !(row.edgePx <= tol.edge)) fails.push(big ? "roiIoU" : "edge");
  if (row.dE === null ? !row.dESkipped : row.dE > tol.dE) fails.push("dE");
  return { status: fails.length ? "off" : "exact", fails, tol: { posPx: r2(tol.pos), sizePx: r2(tol.size), iou: r3(tol.iou), edgePx: r2(tol.edge), dE: r2(tol.dE) } };
}

/**
 * V5-4 item 4: per family, the floor of its TRUSTED rows (render-as-target IoU >= TRUST_IOU, not blind): the worst
 * |pos|, |size|, edge and dE and the lowest roiIoU — as a floor ROW judgeRow reads — plus a summary. A family with no
 * trusted row floors at the bare spec (row null).
 */
export function familyFloors(floorRows, famOfRow, blindIds = new Set()) {
  const med = (a) => { if (!a.length) return 0; const b = [...a].sort((x, y) => x - y); return b[Math.floor((b.length - 1) / 2)]; };
  const out = {};
  for (const f of floorRows) {
    const fam = famOfRow.get(f.id) ?? "?";
    out[fam] ??= { rows: [], untrusted: 0 };
    if (blindIds.has(f.id) || !f.pos) continue;
    if (f.roiIoU >= TRUST_IOU) out[fam].rows.push(f); else out[fam].untrusted += 1;
  }
  for (const [fam, v] of Object.entries(out)) {
    const t = v.rows;
    const posPx = med(t.map((r) => Math.max(Math.abs(r.pos.dxPx), Math.abs(r.pos.dyPx))));
    const sizePx = med(t.map((r) => Math.max(Math.abs(r.size.dwPx), Math.abs(r.size.dhPx))));
    const roiIoU = t.length ? med(t.map((r) => r.roiIoU)) : 1;
    const edgePx = med(t.filter((r) => Number.isFinite(r.edgePx)).map((r) => r.edgePx));
    const dE = med(t.filter((r) => r.dE !== null).map((r) => r.dE));
    out[fam] = {
      row: t.length ? { pos: { dxPx: posPx, dyPx: 0 }, size: { dwPx: sizePx, dhPx: 0 }, roiIoU, edgePx, dE } : null,
      summary: { trusted: t.length, untrusted: v.untrusted, posPx: r2(posPx), sizePx, roiIoU: r3(roiIoU), edgePx: r2(edgePx), dE: r2(dE) },
    };
  }
  return out;
}

/** Measured-but-never-built layout features -> MISSING rows (READY call name, else `needs helper <name>`). */
async function missingRows(S, parts, layout) {
  const prefixes = new Map();
  for (const [k, e] of Object.entries(layout ?? {})) {
    if (k.startsWith("_") || !e || typeof e !== "object" || e.unverified === true) continue;
    const pre = k.split(".")[0];
    if (NOT_FEATURES.has(pre)) continue;
    if (!prefixes.has(pre)) prefixes.set(pre, []);
    prefixes.get(pre).push(k);
  }
  const words = parts.flatMap((p) => [String(p.id).toLowerCase(), String(p.role ?? "").toLowerCase()]);
  let ready = [];
  try {
    const { moduleFrame } = await import("./seat-io.mjs");
    const frame = await moduleFrame(parts, S);
    ready = frame?.ready ? frame.ready(layout, null, 0.04) : [];
  } catch { ready = []; }
  const rows = [];
  for (const [pre, keys] of prefixes) {
    const want = (BUILT_BY[pre] ?? [pre.toLowerCase()]);
    if (words.some((w) => want.some((x) => w.includes(x.toLowerCase())))) continue;
    const call = ready.find((c) => (c.keys ?? []).some((k) => k === `${pre}.*` || k.startsWith(`${pre}.`)));
    rows.push({ id: pre, kind: "MISSING", keys, status: "missing", build: call ? `READY: ${call.what}` : `needs helper ${pre}` });
  }
  return rows;
}

/** Target blobs (raw zone labels, SUBJECT px, >= UNOWNED_PX) no item of their family covers. */
function unownedBlobs(T, w, h, items) {
  const out = [];
  // V5-4: a zone and its per-face palette colours ("<zone>~<face>") are one zone here
  const base = T.zoneNames.map((n) => n.split("~")[0]);
  T.zoneNames.forEach((zone, z) => {
    if (zone.includes("~")) return;
    const f = T.famOfZone[z];
    const m = new Uint8Array(w * h);
    for (let i = 0; i < m.length; i += 1) m[i] = T.state[i] === SUBJECT && T.label[i] >= 0 && base[T.label[i]] === zone ? 1 : 0;
    const fam = items.filter((it) => it.family === f);
    for (const c of componentsIn(m, w, { x0: 0, y0: 0, x1: w - 1, y1: h - 1 }, true)) {
      if (c.n < UNOWNED_PX) continue;
      let inside = 0;
      for (const i of c.px) { const x = i % w, y = (i / w) | 0; if (fam.some((it) => it.boxes.some((b) => x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1))) inside += 1; }
      if (inside * 2 >= c.n) continue;
      out.push({ zone, family: T.famNames[f], px: c.n, at: [Math.round(c.cx), Math.round(c.cy)], box: [c.x0, c.y0, c.x1, c.y1], status: "unowned" });
    }
  });
  return out.sort((a, b) => b.px - a.px);
}

/**
 * @param {{subjectId:string, modulePath:string, floor?:boolean|object[], target?:object|null, spec?:object}} o
 *   floor: true = measure the render-as-target noise floor now; an array = rows of an earlier floor run; false = none.
 */
export async function accuracy({ subjectId, modulePath, floor = true, target = null, spec = SPEC }) {
  const S = loadSubject(subjectId);
  const img = target ?? await readRGB(S.paths.target);
  const proj = await project({ subjectId, modulePath, frame: "target", size: img.w });
  const T = targetOf(S, img, { palette: proj.meta.palette });
  const { items, pf } = itemsOf(proj, S, T);
  const anchorPx = await anchorPxOf(S, proj, modulePath);
  const rows = measureItems(proj, S, T, img, items, pf, spec);
  let floorRows = Array.isArray(floor) ? floor : null;
  if (floor === true) {
    // V5-5 item 4: the floor render carries ink strokes, AA and per-face shade (a real, non-zero floor)
    const self = flatRender(proj, { floor: true });
    const TS = targetOf(S, self, { polygon: false, palette: proj.meta.palette, occluded: T.state });
    floorRows = measureItems(proj, S, TS, self, items, pf, spec);
  }
  const byId = new Map((floorRows ?? []).map((r) => [r.id, r]));
  // an item the harness cannot find in its OWN flat render (render-as-target IoU < BLIND_IOU: its palette colour does
  // not classify to its family) is BLIND — never exact, and its self-measure never widens a tolerance
  const blindIds = new Set((floorRows ?? []).filter((f) => !f.pos || f.roiIoU < BLIND_IOU).map((f) => f.id));
  // V5-4 item 4: per-family floor from the TRUSTED rows; an untrusted item is judged on its family's floor
  const famOfRow = new Map(rows.map((r) => [r.id, T.famNames[r.feature.family] ?? "?"]));
  const families = floorRows ? familyFloors(floorRows, famOfRow, blindIds) : null;
  const floors = floorRows ? true : false;
  const thinCfg = S.cls?.likeness?.thin;
  for (const r of rows) {
    const f = byId.get(r.id);
    // V5-7 item 1: a THIN item (a stroke) — and a region-BLIND one, whose flat colour never classifies — is judged on
    // its ink (centreline + count / pitch), never on regions nor as blind
    // and a REPEATED-member item (a profileRoles role, >= minParts parts: treads, rungs), whose region count only
    // counts the target's ink cells
    const repeated = (thinCfg?.profileRoles ?? []).includes(r.kind) && r.parts >= (thinCfg?.minParts ?? Infinity);
    if (thinCfg && r.ink && (r.ink.stroke || repeated || blindIds.has(r.id))) { Object.assign(r, judgeThin(r, thinCfg), { judged: "ink" }); continue; }
    if (blindIds.has(r.id)) { Object.assign(r, { status: "blind", fails: [`harness-blind (render-as-target IoU ${f?.roiIoU ?? 0})`] }); continue; }
    const trusted = !f || f.roiIoU >= TRUST_IOU;
    const fam = families?.[famOfRow.get(r.id)];
    const floorRow = fam?.row ? { ...fam.row, roiIoU: trusted && f ? f.roiIoU : fam.row.roiIoU } : (trusted ? f : null);
    Object.assign(r, judgeRow(r, floors === false ? null : floorRow, spec, anchorPx));
    if (!trusted) r.floorSource = `family ${famOfRow.get(r.id)} (own render-as-target IoU ${f.roiIoU} < ${TRUST_IOU})`;
  }
  const seen = (floorRows ?? []).filter((f) => !blindIds.has(f.id) && f.roiIoU >= TRUST_IOU);
  const { buildModule } = await import("./project.mjs");
  const built = await buildModule(modulePath);
  const missing = await missingRows(S, built.parts, S.readJson("layout"));
  const unowned = unownedBlobs(T, img.w, img.h, items);
  let occludedPx = 0;
  for (const v of T.state) if (v === OCCLUDED) occludedPx += 1;
  const exactN = rows.filter((r) => r.status === "exact").length;
  const M = rows.length + missing.length;
  const floorSummary = floorRows ? {
    posPx: r2(Math.max(0, ...seen.map((r) => Math.max(Math.abs(r.pos.dxPx), Math.abs(r.pos.dyPx))))),
    sizePx: Math.max(0, ...seen.map((r) => Math.max(Math.abs(r.size.dwPx), Math.abs(r.size.dhPx)))),
    roiIoUMin: r3(Math.min(1, ...seen.filter((r) => r.px.target >= spec.bigPx).map((r) => r.roiIoU))),
    edgePx: r2(Math.max(0, ...seen.filter((r) => Number.isFinite(r.edgePx)).map((r) => r.edgePx))),
    dE: r2(Math.max(0, ...seen.filter((r) => r.dE !== null).map((r) => r.dE))),
    blind: [...blindIds],
    trustIoU: TRUST_IOU,
    untrusted: (floorRows ?? []).filter((f) => !blindIds.has(f.id) && f.roiIoU < TRUST_IOU).map((f) => `${f.id} ${f.roiIoU}`),
    families: families ? Object.fromEntries(Object.entries(families).map(([k, v]) => [k, v.summary])) : null,
  } : null;
  return {
    subject: subjectId, module: String(modulePath).replace(/\\/g, "/"), spec, anchorPx, noiseFloor: floorSummary,
    summary: `${exactN} of ${M} items exact${unowned.length ? `, ${unowned.length} unowned blob(s)` : ""}`,
    exactN, M, exact: exactN === M && !unowned.length,
    items: [...rows, ...missing], unowned, occludedPx,
    floorRows: floorRows ?? undefined,
  };
}

/** The worst rows first (MISSING, then by number of failed checks and px). */
export function topFailing(report, n = 5) {
  return report.items.filter((r) => r.status !== "exact")
    .sort((a, b) => (b.status === "missing") - (a.status === "missing") || (a.status === "blind") - (b.status === "blind") || (b.fails?.length ?? 0) - (a.fails?.length ?? 0) || (b.px?.target ?? 0) - (a.px?.target ?? 0))
    .slice(0, n)
    .map((r) => (r.status === "missing" ? `${r.id} MISSING (${r.build})` : `${r.id} ${r.fails.join("+")}${r.judged === "ink" ? ` (ink: centre ${r.ink.centrePx} px${r.ink.count ? `, count ${r.ink.count.target}/${r.ink.count.render}, pitch ${r.ink.pitch.target}/${r.ink.pitch.render}` : ""})` : r.pos ? ` (d ${r.pos.dxPx},${r.pos.dyPx} px, IoU ${r.roiIoU}, dE ${r.dE})` : ""}`));
}

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject");
  const modulePath = arg("module");
  if (!subjectId || !modulePath) {
    console.error("usage: node scripts/accuracy.mjs --subject <id> --module <path.mjs> [--json <out.json>] [--no-floor]");
    process.exit(3);
  }
  const r = await accuracy({ subjectId, modulePath, floor: !process.argv.includes("--no-floor") });
  console.log(`[accuracy] ${r.summary}; occluded ${r.occludedPx} px; noise floor ${JSON.stringify(r.noiseFloor)}`);
  for (const line of topFailing(r, 12)) console.log(`  ${line}`);
  for (const u of r.unowned.slice(0, 8)) console.log(`  UNOWNED ${u.zone} (${u.family}) ${u.px} px at ${u.at.join(",")}`);
  const out = arg("json");
  if (out) {
    fs.mkdirSync(path.dirname(path.resolve(ROOT, out)), { recursive: true });
    fs.writeFileSync(path.resolve(ROOT, out), `${JSON.stringify({ ...r, floorRows: undefined }, null, 2)}\n`);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(error); process.exit(1); });
}
