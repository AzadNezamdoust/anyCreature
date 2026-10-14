// WORKFLOW v6 — ORTHOGRAPHIC REFERENCES (research/WF-V6-PLAN.md A) + the Node ortho rasteriser. Generic (V6-2): every
// subject with subjects/<s>/turnaround/views.json (contract: scripts/v6/README.md).
//
// A turnaround view is registered with a KNOWN orthographic camera in the class author frame (views.json right / up):
//   px:  X = s (p . right) + ox,  Y = -s (p . up) + oy.  ONE px/m scale s for every view, s = the mean measured px of the
// anchor dimension / anchor.m. Dimensions per world axis: x -> W, y -> H, z -> L. A view measures the dimension of its
// right axis and of its up axis: y (height) = the foreground bbox (ground to top, wheels included), x / z = the span of
// the BODY colour family (mirrors, bumpers excluded). Views sharing an axis share that dimension; residual = each view's
// px / the mean - 1 (target +-3 %). Offsets: per axis the class ORIGIN (rules registry, views.json `origin` overrides):
// "centre" = the middle of the span, "min" = the span edge where that world coordinate is least (vehicle ground y = 0).
//
// COLOUR FAMILIES (per subject, never hard-coded): the concept palette = the median colour of each regions.json zone's
// rects on the concept image; zones closer than MERGE_RGB are one family (single link); the family holding
// views.json families.body (default: the first region named body*) is "body". Pixels: bg = darkest channel >= FG_MAX,
// else the nearest family colour (> FAR_RGB away = "other"). A module zone's family = the family nearest its palette
// colour (partFamilies). views.json families.table {name: "#hex" | ["#hex", ...]} replaces the derived table.
// families.viewTable {<view>: {<family>: hex | [hex]}} (optional): one turnaround image's own colours of the named families
// (viewFamilyTable: names / indices unchanged; absent = byte-identical).
// families.spanOpen (opt-in, integer px >= 2): the registration's body span (spanOf) counts the body-family mask after a
// morphological opening with a spanOpen x spanOpen square — 1-px anti-alias halo columns / rows of dark outlines (mirror
// heads, lamps) whose greys classify as body drop out of the W / L spans (absent = byte-identical).
// families.enclosedFg (opt-in): bg = only the near-white connected to the image border (or to a families.holes seed);
// enclosed near-white px take the nearest family (registered.mjs borderBackground) — white parts are foreground.
// DRIFT (WF v8, views.json `drift`): per image don't-care rects -> the agree-IoU (viewTarget care, viewScore agree);
// the raw IoU never sees them.
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { faceOf } from "../project.mjs";
import { borderBackground, careMask, checkRect, turnFn } from "../registered.mjs";
import { classFrame } from "./rules.mjs";

export const FG_MAX = 235;
export const MERGE_RGB = 40;
export const FAR_RGB = 120;
export const AXIS_DIM = Object.freeze(["W", "H", "L"]);   // world axis index -> dimension letter

export const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
/**
 * {right, up, back} of a view spec (back = right x up points at the camera). WF v8 WP3: a views.json `scale: {right}`
 * (the drawing's right axis measured that many times too long) scales `right` — the rasters draw the model stretched
 * the same way; `scale: {up}` (2026-09-28) likewise scales `up`; `back` stays the unit normal (depth order, cel
 * factors). Absent = the spec's own arrays (byte-identical rasters).
 */
export function basisOf(view) {
  const kr = view.scale?.right, ku = view.scale?.up;
  return { right: kr ? view.right.map((c) => c * kr) : view.right, up: ku ? view.up.map((c) => c * ku) : view.up, back: cross(view.right, view.up) };
}
/** [axis index, sign] of an axis-aligned unit vector. */
export function axisOf(vec) {
  const a = vec.findIndex((c) => Math.abs(c) > 0.5);
  if (a < 0 || vec.filter((c) => Math.abs(c) > 1e-9).length !== 1) throw new Error(`ortho: view axis ${JSON.stringify(vec)} is not axis-aligned`);
  return [a, Math.sign(vec[a])];
}

export const turnaroundDir = (subjectId) => path.join(ROOT, "subjects", subjectId, "turnaround");
export const viewsFile = (subjectId) => path.join(turnaroundDir(subjectId), "views.json");
export const hasTurnaround = (subjectId) => fs.existsSync(viewsFile(subjectId));
export const readJson = (file) => JSON.parse(fs.readFileSync(file, "utf8"));

// ---------------------------------------------------------------------------
// Colour families
// ---------------------------------------------------------------------------

const hexRGB = (h) => [1, 3, 5].map((i) => parseInt(String(h).slice(i, i + 2), 16));
const dist2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;

/** Median RGB of every regions.json zone (its rects) on the concept image: [{region, rgb}]. */
export async function conceptPalette(S) {
  const regions = S.readJson("regions");
  if (!regions?.zones) return [];
  const { data, info } = await sharp(S.paths.target).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const out = [];
  for (const [region, z] of Object.entries(regions.zones)) {
    const ch = [[], [], []];
    for (const [x, y, w, h] of z.rects ?? []) for (let yy = y; yy < y + h; yy += 1) for (let xx = x; xx < x + w; xx += 1) {
      const j = (yy * info.width + xx) * info.channels;
      for (let c = 0; c < 3; c += 1) ch[c].push(data[j + c]);
    }
    if (ch[0].length) out.push({ region, rgb: ch.map((a) => a.sort((p, q) => p - q)[a.length >> 1]) });
  }
  return out;
}

/**
 * The subject's target-MASK rule (views.json families): { fgMax (bg = darkest channel >= fgMax), enclosedFg (bg = only
 * the near-white connected to the image border or to a hole seed), holes: {<view> | "concept": [[x, y], ...]} | null }.
 */
export const maskRule = (families = {}) => ({ fgMax: families.fgMax ?? FG_MAX, enclosedFg: !!families.enclosedFg, holes: families.holes ?? null });
/** The rule without loading the turnaround images (views.json; the defaults for a subject without one) + its `drift`. */
export function subjectMaskRule(subjectId) {
  if (!hasTurnaround(subjectId)) return maskRule({});
  const spec = readJson(viewsFile(subjectId));
  return { ...maskRule(spec.families ?? {}), drift: driftOf(spec) };
}
/**
 * registered.mjs foregroundMask / targetState options of one image of the subject: a turnaround view name or "concept".
 * Never the drift rects: an agree-IoU caller adds `dontCare: driftRects(rule, view)` itself (the raw target stays raw for
 * the IoU, the frame fit and the measure tools).
 */
export const maskOptions = (rule, view) => ({ enclosedFg: !!rule?.enclosedFg, holes: rule?.holes?.[view] ?? null });

/** WF v8 bound: a view's drift rects may cover at most this share of its reference foreground (above it: regenerate). */
export const DRIFT_MAX = 0.05;

/**
 * views.json `drift` (WF v8, scripts/v6/README.md): {<view> | "concept": [{id, rect: [x0, y0, x1, y1] (that image's own
 * px, half-open), decides, why}], <note>: "..."} -> {<view> | "concept": [{id, rect, decides, why}]} (array-valued keys
 * only; any other key, e.g. "audited", is a note), or null when absent. Throws on an unknown view or a bad rect.
 */
export function driftOf(spec) {
  const d = spec?.drift;
  if (d === undefined || d === null) return null;
  if (typeof d !== "object" || Array.isArray(d)) throw new Error('ortho: views.json drift must be an object {<view> | "concept": [{id, rect, decides, why}]}');
  const out = {};
  for (const [view, list] of Object.entries(d)) {
    if (!Array.isArray(list)) continue;
    if (view !== "concept" && !spec.views?.[view]) throw new Error(`ortho: views.json drift.${view} is not an image of the subject (views: ${Object.keys(spec.views ?? {}).join(", ")}, concept)`);
    out[view] = list.map((e, i) => ({ id: e?.id ?? `${view}${i + 1}`, rect: [...checkRect(e?.rect, `views.json drift.${view}[${i}]${e?.id ? ` (${e.id})` : ""} rect`)], decides: e?.decides ?? null, why: e?.why ?? null }));
  }
  return out;
}
/** The drift rects ([[x0, y0, x1, y1], ...], that image's px) of one image — a view name or "concept" — or null. */
export const driftRects = (rule, view) => (rule?.drift?.[view]?.length ? rule.drift[view].map((d) => d.rect) : null);

/**
 * The family table: { names: ["bg", ...families, "other"], rgb: [null, [colours of family 1], ..., null], body, zoneFams,
 * members: {name: [regions]}, ...maskRule (fgMax, enclosedFg, holes) }. Family 0 = bg, the last = other.
 */
export function familyTable(palette, spec = {}) {
  let groups;
  if (spec.table) {
    groups = Object.entries(spec.table).map(([name, hex]) => ({ name, members: [name], rgb: (Array.isArray(hex) ? hex : [hex]).map(hexRGB) }));
  } else {
    const parent = palette.map((_, i) => i);
    const find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
    for (let i = 0; i < palette.length; i += 1) for (let j = i + 1; j < palette.length; j += 1) {
      if (dist2(palette[i].rgb, palette[j].rgb) < MERGE_RGB * MERGE_RGB) parent[find(j)] = find(i);
    }
    const by = new Map();
    palette.forEach((p, i) => { const r = find(i); if (!by.has(r)) by.set(r, []); by.get(r).push(p); });
    const bodyRegion = spec.body ?? palette.find((p) => /^body/.test(p.region))?.region ?? palette[0]?.region;
    groups = [...by.values()].map((ps) => ({
      name: ps.some((p) => p.region === bodyRegion) ? "body" : ps.map((p) => p.region).join("+"),
      members: ps.map((p) => p.region), rgb: ps.map((p) => p.rgb),
    }));
  }
  if (!groups.length) throw new Error("ortho: no colour families (no regions.json zones and no views.json families.table)");
  const bodyName = spec.table ? (spec.body ?? groups[0].name) : "body";
  const names = ["bg", ...groups.map((g) => g.name), "other"];
  const body = names.indexOf(bodyName);
  if (body < 1) throw new Error(`ortho: body family "${bodyName}" not in the family table`);
  const zoneFams = names.map((_, i) => i).filter((i) => i > 0 && i < names.length - 1 && i !== body);
  return { names, rgb: [null, ...groups.map((g) => g.rgb), null], body, other: names.length - 1, zoneFams, ...maskRule(spec), members: Object.fromEntries(groups.map((g) => [g.name, g.members])), ...spanOpenOf(spec) };
}

/**
 * views.json `families.viewTable` (scripts/v6/README.md; turnaround.mjs `families`): {<view>: {<family>: "#hex" |
 * ["#hex", ...]}} — for ONE turnaround image, the colours of the named families (a generator that drew that view a
 * little lighter / darker); every name and index stays the table's, a family not named keeps its colours, "_" keys are
 * notes. -> the table that classifies that image: `table` itself when the view has no entry (absent = byte-identical).
 */
export function viewFamilyTable(table, spec, view) {
  const vt = spec?.viewTable;
  if (vt === undefined || vt === null) return table;
  if (typeof vt !== "object" || Array.isArray(vt)) throw new Error("ortho: views.json families.viewTable must be {<view>: {<family>: \"#hex\" | [\"#hex\", ...]}}");
  const over = vt[view];
  if (!over || typeof over !== "object") return table;
  const rgb = [...table.rgb];
  for (const [name, hex] of Object.entries(over)) {
    if (name.startsWith("_")) continue;
    const f = table.names.indexOf(name);
    if (f < 1 || f >= table.other) throw new Error(`ortho: views.json families.viewTable.${view}: "${name}" is not a family (${table.names.slice(1, -1).join(", ")})`);
    const list = (Array.isArray(hex) ? hex : [hex]).map(hexRGB);
    if (!list.length || list.some((c) => c.some((v) => !Number.isFinite(v)))) throw new Error(`ortho: views.json families.viewTable.${view}.${name}: not "#rrggbb" colours`);
    rgb[f] = list;
  }
  return { ...table, rgb };
}
/** The viewTable keys that are not views of the subject (views.json validation). */
export const viewTableStray = (spec) => Object.keys(spec?.families?.viewTable ?? {}).filter((k) => !k.startsWith("_") && !spec.views?.[k]);

/** Family index of one pixel colour (bg by the FG_MAX rule unless `bg` is false, "other" beyond FAR_RGB). */
export function classify(table, r, g, b, far = FAR_RGB, bg = true) {
  if (bg && Math.min(r, g, b) >= (table.fgMax ?? FG_MAX)) return 0;
  let best = table.other;
  let bd = far * far;
  const c = [r, g, b];
  for (let f = 1; f < table.other; f += 1) for (const q of table.rgb[f]) { const d = dist2(c, q); if (d < bd) { bd = d; best = f; } }
  return best;
}

/** The representative hex of a palette entry (a string, or a per-face object). */
export function paletteHex(entry, face = null) {
  if (typeof entry === "string") return entry;
  if (entry && typeof entry === "object") return (face && entry[face]) ?? entry.side ?? entry.front ?? Object.values(entry)[0];
  return "#ff00ff";
}
/**
 * Family of each part: the family nearest its zone's palette colour (no "other" cut). A near-white zone colour is
 * "other" unless the table's enclosedFg makes white parts foreground (then its nearest family, like the reference px).
 */
export function partFamilies(parts, palette, table) {
  const cache = new Map();
  return Int32Array.from(parts.map((p) => {
    if (!cache.has(p.zone)) cache.set(p.zone, classify(table, ...hexRGB(paletteHex(palette?.[p.zone])), Infinity, !table.enclosedFg) || table.other);
    return cache.get(p.zone);
  }));
}

/**
 * A reference image as family ids (0 = bg). opts = maskOptions(table, view): with enclosedFg (default: the table's),
 * near-white px not connected to the border or to a `holes` seed ([[x, y], ...], this image's px) are foreground and
 * take the nearest family (no bg cut).
 */
export async function readImage(file, table, { enclosedFg = !!table.enclosedFg, holes = null } = {}) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const n = info.width * info.height;
  const fam = new Uint8Array(n);
  const memo = new Map();
  for (let i = 0, j = 0; i < n; i += 1, j += info.channels) {
    const key = (data[j] << 16) | (data[j + 1] << 8) | data[j + 2];
    let f = memo.get(key);
    if (f === undefined) { f = classify(table, data[j], data[j + 1], data[j + 2]); memo.set(key, f); }
    fam[i] = f;
  }
  if (enclosedFg) {
    const bg = borderBackground(fam, info.width, info.height, holes);
    const inner = new Map();
    for (let i = 0, j = 0; i < n; i += 1, j += info.channels) {
      if (fam[i] !== 0 || bg[i]) continue;
      const key = (data[j] << 16) | (data[j + 1] << 8) | data[j + 2];
      let f = inner.get(key);
      if (f === undefined) { f = classify(table, data[j], data[j + 1], data[j + 2], FAR_RGB, false); inner.set(key, f); }
      fam[i] = f;
    }
  }
  return { data, w: info.width, h: info.height, c: info.channels, fam };
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

/**
 * views.json families.spanOpen (opt-in): {spanOpen: n} for the family table (an integer 2..16), {} when absent / null.
 * Throws on any other value.
 */
export function spanOpenOf(families = {}) {
  const n = families?.spanOpen;
  if (n == null) return {};
  if (!Number.isInteger(n) || n < 2 || n > 16) throw new Error(`ortho: views.json families.spanOpen ${JSON.stringify(n)} is not an integer px width in 2..16`);
  return { spanOpen: n };
}

/**
 * The morphological opening of a 0/1 mask (w x h) with an n x n square: the union of every n x n square inside the mask
 * (erosion then dilation, both separable; anchored top-left so the pair is an exact opening). Anything thinner than n px
 * along x or y drops out (1-px anti-alias halo lines at n = 2).
 */
export function openMask(mask, w, h, n) {
  if (!(n >= 2)) return mask;
  const pass = (src, erode, alongX) => {
    const out = new Uint8Array(w * h);
    const lines = alongX ? h : w;
    const len = alongX ? w : h;
    const at = alongX ? (l, i) => l * w + i : (l, i) => i * w + l;
    for (let l = 0; l < lines; l += 1) {
      // erode: out[i] = src[i .. i+n-1] all set; dilate: out[i] = any src[i-n+1 .. i] set (run counters)
      let run = 0;
      if (erode) {
        for (let i = len - 1; i >= 0; i -= 1) { run = src[at(l, i)] ? run + 1 : 0; if (run >= n) out[at(l, i)] = 1; }
      } else {
        for (let i = 0; i < len; i += 1) { run = src[at(l, i)] ? n : Math.max(0, run - 1); if (run > 0) out[at(l, i)] = 1; }
      }
    }
    return out;
  };
  return pass(pass(pass(pass(mask, true, true), true, false), false, false), false, true);
}

/**
 * [lo, hi] (px edges) of the rows / columns where family `f` covers >= frac x the densest line. open >= 2 (views.json
 * families.spanOpen): the family mask is opened with an open x open square first (openMask); else the raw mask.
 */
export function spanOf(img, f, axis, frac = 0.05, open = 0) {
  const len = axis === "x" ? img.w : img.h;
  const cnt = new Int32Array(len);
  if (open >= 2) {
    const mask = new Uint8Array(img.w * img.h);
    for (let i = 0; i < mask.length; i += 1) mask[i] = img.fam[i] === f ? 1 : 0;
    const m = openMask(mask, img.w, img.h, open);
    for (let y = 0; y < img.h; y += 1) for (let x = 0; x < img.w; x += 1) if (m[y * img.w + x]) cnt[axis === "x" ? x : y] += 1;
  } else for (let y = 0; y < img.h; y += 1) for (let x = 0; x < img.w; x += 1) if (img.fam[y * img.w + x] === f) cnt[axis === "x" ? x : y] += 1;
  const peak = Math.max(...cnt);
  let lo = -1;
  let hi = -1;
  for (let i = 0; i < len; i += 1) if (cnt[i] >= frac * peak) { if (lo < 0) lo = i; hi = i; }
  return [lo, hi + 1];
}
export function fgBox(img) {
  let x0 = img.w, y0 = img.h, x1 = -1, y1 = -1;
  for (let y = 0; y < img.h; y += 1) for (let x = 0; x < img.w; x += 1) if (img.fam[y * img.w + x] !== 0) {
    if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  return { x0, y0, x1: x1 + 1, y1: y1 + 1 };
}

/**
 * Register the views. spec: { views: {name: {right, up}}, anchor: {dim, m}, origin: {x, y, z}, body: family index,
 * spanOpen?: px (the body spans through spanOf's opening; views.json families.spanOpen) }.
 * Returns { s, names, views: {name: {img, ox, oy, box, body, spec, kr?, ku?}}, shared: {D: {view: px}}, residuals, dims: {L, W, H} }
 * (kr / ku = the view's `scale.right` / `scale.up` when set).
 */
export function registerViews(images, spec) {
  const names = Object.keys(spec.views);
  const m = {};
  const shared = {};
  const put = (key, v, px) => { (shared[key] ??= {})[v] = px; };
  for (const v of names) {
    const img = images[v];
    const box = fgBox(img);
    const bx = spanOf(img, spec.body, "x", 0.05, spec.spanOpen ?? 0);
    const by = spanOf(img, spec.body, "y", 0.05, spec.spanOpen ?? 0);
    const [ra, rs] = axisOf(spec.views[v].right);
    const [ua, us] = axisOf(spec.views[v].up);
    // WF v8 WP3: views.json per-view `scale: {right}` (measured, with evidence): the drawing's right axis is kr x too long
    // -> its px along right count 1 / kr (residuals, s, dims), basisOf draws the model kr x longer, pxToView divides by it
    const kr = spec.views[v].scale?.right ?? 1;
    if (!(kr > 0.5 && kr < 2)) throw new Error(`ortho: views.json ${v}.scale.right ${JSON.stringify(spec.views[v].scale?.right)} is not a measured factor in 0.5..2`);
    // views.json `scale: {up}` (2026-09-28, the same contract along the up axis: a top view drawn uniformly wide across)
    const ku = spec.views[v].scale?.up ?? 1;
    if (!(ku > 0.5 && ku < 2)) throw new Error(`ortho: views.json ${v}.scale.up ${JSON.stringify(spec.views[v].scale?.up)} is not a measured factor in 0.5..2`);
    // the span each image axis measures: y (height) = the foreground bbox, x / z = the body family
    const spanR = ra === 1 ? [box.x0, box.x1] : bx;
    const spanU = ua === 1 ? [box.y0, box.y1] : by;
    put(AXIS_DIM[ra], v, (spanR[1] - spanR[0]) / kr);
    put(AXIS_DIM[ua], v, (spanU[1] - spanU[0]) / ku);
    if (ra !== 1) put(`${AXIS_DIM[ra]}bbox`, v, (box.x1 - box.x0) / kr);   // overall bboxes (mirrors, bumpers): reported only
    if (ua !== 1) put(`${AXIS_DIM[ua]}bbox`, v, (box.y1 - box.y0) / ku);
    const org = (a) => spec.origin[["x", "y", "z"][a]] ?? "centre";
    // X = s sgn w + ox: "min" = the edge where w is least; Y = -s sgn w + oy
    const ox = org(ra) === "centre" ? (spanR[0] + spanR[1]) / 2 : (org(ra) === "min") === (rs > 0) ? spanR[0] : spanR[1];
    const oy = org(ua) === "centre" ? (spanU[0] + spanU[1]) / 2 : (org(ua) === "min") === (us > 0) ? spanU[1] : spanU[0];
    m[v] = { img, ox, oy, box, body: { x: bx, y: by }, spec: spec.views[v], ...(kr !== 1 ? { kr } : {}), ...(ku !== 1 ? { ku } : {}) };
  }
  const residuals = {};
  for (const [k, per] of Object.entries(shared)) {
    const vals = Object.values(per);
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    residuals[k] = Object.fromEntries(Object.entries(per).map(([v, px]) => [v, Math.round((px / mean - 1) * 1e4) / 1e4]));
    residuals[k].meanPx = Math.round(mean * 100) / 100;
    residuals[k].maxAbs = Math.max(...Object.values(per).map((px) => Math.abs(px / mean - 1)));
  }
  if (!residuals[spec.anchor.dim]) throw new Error(`ortho: no view measures the anchor dimension ${spec.anchor.dim}`);
  const s = residuals[spec.anchor.dim].meanPx / spec.anchor.m;
  // views.json per-view `shift: {right, up}` (m, measured, with evidence): moves that view's origin so what the span rule
  // put at +right / +up m becomes 0 — for a drawing whose body-colour span is skewed by an asymmetric attachment
  for (const v of names) {
    const sh = spec.views[v].shift;
    if (sh) { m[v].ox += (sh.right ?? 0) * s * (m[v].kr ?? 1); m[v].oy -= (sh.up ?? 0) * s * (m[v].ku ?? 1); }
  }
  const dims = Object.fromEntries(AXIS_DIM.filter((d) => residuals[d]).map((d) => [d, d === spec.anchor.dim ? spec.anchor.m : residuals[d].meanPx / s]));
  return { s, names, views: m, shared, residuals, dims };
}

const turnCache = new Map();
/**
 * A subject's registered turnaround (cached): { spec (views.json), prior (prior.json or null), table, reg }. The anchor
 * is views.json anchor (else prior.json anchor); the origin is views.json origin (else the class frame's).
 */
export async function loadTurnaround(subjectId) {
  if (turnCache.has(subjectId)) return turnCache.get(subjectId);
  const spec = readJson(viewsFile(subjectId));
  const S = loadSubject(subjectId);
  const priorFile = path.join(ROOT, "subjects", subjectId, "prior.json");
  const prior = fs.existsSync(priorFile) ? readJson(priorFile) : null;
  const anchor = spec.anchor ?? prior?.anchor;
  if (!anchor?.dim || !(anchor.m > 0)) throw new Error(`ortho: ${subjectId} views.json has no anchor {dim, m}`);
  const table = familyTable(spec.families?.table ? [] : await conceptPalette(S), spec.families ?? {});
  table.drift = driftOf(spec);   // WF v8: {<view> | concept: [{id, rect, decides, why}]} or null
  const stray = viewTableStray(spec);
  if (stray.length) throw new Error(`ortho: views.json families.viewTable names ${stray.join(", ")}: not a view (views: ${Object.keys(spec.views).join(", ")})`);
  const images = {};
  // families.viewTable: a view's own colours of some families (absent: the table itself, byte-identical)
  for (const [name, v] of Object.entries(spec.views)) images[name] = await readImage(path.join(turnaroundDir(subjectId), v.file), viewFamilyTable(table, spec.families, name), maskOptions(table, name));
  const origin = { ...classFrame(S.klass).origin, ...(spec.origin ?? {}) };
  const reg = registerViews(images, { views: spec.views, anchor, origin, body: table.body, ...(table.spanOpen ? { spanOpen: table.spanOpen } : {}) });
  reg.table = table;
  const out = { spec, prior, table, reg, S };
  turnCache.set(subjectId, out);
  return out;
}

/** A view's px -> metres along (right, up) (a views.json `scale: {right}` / `scale: {up}` divides that axis by it). */
export const pxToView = (reg, v, X, Y) => [(X - reg.views[v].ox) / (reg.s * (reg.views[v].kr ?? 1)), (reg.views[v].oy - Y) / (reg.s * (reg.views[v].ku ?? 1))];

/** Connected components of family f in a view (4-neighbour), bboxes in px + metres (right/up axes), area >= minPx. */
export function components(reg, v, f, minPx = 40) {
  const { img } = reg.views[v];
  const seen = new Uint8Array(img.w * img.h);
  const out = [];
  const stack = [];
  for (let i = 0; i < seen.length; i += 1) {
    if (seen[i] || img.fam[i] !== f) continue;
    let n = 0, x0 = img.w, y0 = img.h, x1 = 0, y1 = 0;
    stack.push(i); seen[i] = 1;
    while (stack.length) {
      const j = stack.pop();
      const x = j % img.w, y = (j - x) / img.w;
      n += 1; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      for (const k of [j - 1, j + 1, j - img.w, j + img.w]) if (k >= 0 && k < seen.length && !seen[k] && img.fam[k] === f && Math.abs((k % img.w) - x) <= 1) { seen[k] = 1; stack.push(k); }
    }
    if (n < minPx) continue;
    const [a0, b1] = pxToView(reg, v, x0, y0);
    const [a1, b0] = pxToView(reg, v, x1 + 1, y1 + 1);
    out.push({ n, px: [x0, y0, x1 + 1, y1 + 1], right: [a0, a1], up: [b0, b1] });
  }
  return out.sort((a, b) => b.n - a.n);
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Ortho raster (author-frame meshes from project.mjs meshParts(parts, 0)); TRUE-COLOUR CEL shade per px
// ---------------------------------------------------------------------------

/**
 * Cel factor of a unit normal seen along `back` (toward the camera): the target is flat cel-shaded, so a face toward the
 * viewer reads at 100 % of its palette colour, a top at 105 % (clamped; 100 % when the palette measured a top colour),
 * a side face at 85 %, a bottom at 70 %.
 */
export const CEL = Object.freeze({ facing: 1, top: 1.05, side: 0.85, bottom: 0.7 });
export function celFactor(n, back) {
  const nd = dot(n, back);
  if (nd >= 0.7) return CEL.facing;
  if (n[1] > 0.5) return CEL.top;
  if (n[1] < -0.5) return CEL.bottom;
  return nd >= 0.35 ? CEL.facing : CEL.side;
}

/**
 * Rasterise meshes through an orthographic basis at w x h. map: X = k (p . right) + bx, Y = -k (p . up) + by.
 * Returns { partId (Int32Array, -1 bg), shade (Float32Array cel factor), face (Uint8Array, project.mjs FACES index of the
 * render-frame normal; turnDeg = frontRotationDeg(meta.front)) }. Pixel centres, back faces culled, depth test.
 */
export function rasterOrtho(meshes, basis, map, w, h, turnDeg = 0) {
  const { right: R, up: U, back: B } = basis;
  const turn = turnFn(turnDeg);
  const partId = new Int32Array(w * h).fill(-1);
  const depth = new Float32Array(w * h).fill(-Infinity);
  const shade = new Float32Array(w * h);
  const face = new Uint8Array(w * h);
  const { k, bx, by } = map;
  for (let p = 0; p < meshes.length; p += 1) {
    const { pos, tris } = meshes[p];
    const nv = pos.length / 3;
    const sx = new Float64Array(nv), sy = new Float64Array(nv), sz = new Float64Array(nv);
    for (let i = 0; i < nv; i += 1) {
      const x = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
      sx[i] = k * (R[0] * x + R[1] * y + R[2] * z) + bx;
      sy[i] = -k * (U[0] * x + U[1] * y + U[2] * z) + by;
      sz[i] = B[0] * x + B[1] * y + B[2] * z;   // larger = nearer the camera
    }
    for (let t = 0; t < tris.length; t += 3) {
      const a = tris[t], b = tris[t + 1], c = tris[t + 2];
      const ax = sx[a], ay = sy[a], bxx = sx[b], byy = sy[b], cx = sx[c], cy = sy[c];
      const area = (bxx - ax) * (cy - ay) - (cx - ax) * (byy - ay);
      if (area >= 0) continue;
      let minX = Math.max(0, Math.ceil(Math.min(ax, bxx, cx) - 0.5)), maxX = Math.min(w - 1, Math.floor(Math.max(ax, bxx, cx) - 0.5));
      let minY = Math.max(0, Math.ceil(Math.min(ay, byy, cy) - 0.5)), maxY = Math.min(h - 1, Math.floor(Math.max(ay, byy, cy) - 0.5));
      if (minX > maxX || minY > maxY) continue;
      const ux = pos[b * 3] - pos[a * 3], uy = pos[b * 3 + 1] - pos[a * 3 + 1], uz = pos[b * 3 + 2] - pos[a * 3 + 2];
      const vx = pos[c * 3] - pos[a * 3], vy = pos[c * 3 + 1] - pos[a * 3 + 1], vz = pos[c * 3 + 2] - pos[a * 3 + 2];
      const n0 = [uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx];
      const nl = Math.hypot(...n0) || 1;
      const n = n0.map((q) => q / nl);
      const cel = celFactor(n, B);
      const fc = faceOf(...turn(n));
      const inv = 1 / area;
      const za = sz[a], zb = sz[b], zc = sz[c];
      for (let py = minY; py <= maxY; py += 1) {
        const Yc = py + 0.5;
        for (let px = minX; px <= maxX; px += 1) {
          const Xc = px + 0.5;
          const w0 = ((cx - bxx) * (Yc - byy) - (cy - byy) * (Xc - bxx)) * inv;
          if (w0 < 0) continue;
          const w1 = ((ax - cx) * (Yc - cy) - (ay - cy) * (Xc - cx)) * inv;
          if (w1 < 0) continue;
          const w2 = 1 - w0 - w1;
          if (w2 < 0) continue;
          const d = w0 * za + w1 * zb + w2 * zc;
          const i = py * w + px;
          if (d >= depth[i]) { depth[i] = d; partId[i] = p; shade[i] = cel; face[i] = fc; }
        }
      }
    }
  }
  return { partId, shade, face };
}

/** The raster map of a registered view at `size` px wide (the reference image scaled by size / img.w). */
export function viewMap(reg, v, size) {
  const f = size / reg.views[v].img.w;
  return { k: reg.s * f, bx: reg.views[v].ox * f, by: reg.views[v].oy * f, w: size, h: Math.round(reg.views[v].img.h * f) };
}

/**
 * Target rasters of a view at `size`: fg (0/1) + family ids, nearest sample at pixel centres; care (WF v8): 0 where the
 * sampled reference px lies in one of the view's drift rects (reg.table.drift), null without rects. Cached per reg.
 */
export function viewTarget(reg, v, size) {
  reg.cache ??= new Map();
  const key = `${v}:${size}`;
  if (reg.cache.has(key)) return reg.cache.get(key);
  const { img } = reg.views[v];
  const { w, h } = viewMap(reg, v, size);
  const fg = new Uint8Array(w * h);
  const fam = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    const ty = Math.min(img.h - 1, Math.floor((y + 0.5) * img.h / h));
    for (let x = 0; x < w; x += 1) {
      const tx = Math.min(img.w - 1, Math.floor((x + 0.5) * img.w / w));
      const f = img.fam[ty * img.w + tx];
      fam[y * w + x] = f;
      fg[y * w + x] = f !== 0 ? 1 : 0;
    }
  }
  const out = { w, h, fg, fam, care: careMask(driftRects(reg.table, v), w, h, img.w, img.h) };
  reg.cache.set(key, out);
  return out;
}

/** WF v8: the share of a view's reference foreground (its own px) inside its drift rects; 0 without rects. Cached per reg. */
export function viewDrift(reg, v) {
  const rects = driftRects(reg.table, v);
  if (!rects) return 0;
  reg.cache ??= new Map();
  const key = `drift:${v}`;
  if (reg.cache.has(key)) return reg.cache.get(key);
  const { img } = reg.views[v];
  const care = careMask(rects, img.w, img.h);
  let fg = 0, masked = 0;
  for (let i = 0; i < img.fam.length; i += 1) if (img.fam[i] !== 0) { fg += 1; if (!care[i]) masked += 1; }
  const share = fg ? masked / fg : 0;
  reg.cache.set(key, share);
  return share;
}

/**
 * Silhouette IoU + per-family IoU (the table's zone families: every family but bg, body, other) vs a view target, and
 * `agree` (WF v8): the silhouette IoU with the target's don't-care px (T.care 0: drift rects) in neither I nor U — the
 * same number as `iou` when T has no care raster.
 */
export function viewScore(T, partId, partFam, table) {
  const fams = table.zoneFams;
  const care = T.care ?? null;
  let inter = 0, union = 0, ci = 0, cu = 0;
  const fi = new Float64Array(table.names.length), fu = new Float64Array(table.names.length);
  for (let i = 0; i < partId.length; i += 1) {
    const m = partId[i] >= 0;
    const t = T.fg[i] === 1;
    if (m && t) inter += 1;
    if (m || t) union += 1;
    if (care && care[i]) { if (m && t) ci += 1; if (m || t) cu += 1; }
    const mf = m ? partFam[partId[i]] : -1;
    const tf = T.fam[i];
    for (const f of fams) {
      const a = mf === f, b = tf === f;
      if (a && b) fi[f] += 1;
      if (a || b) fu[f] += 1;
    }
  }
  const fam = {};
  for (const f of fams) fam[table.names[f]] = fu[f] ? fi[f] / fu[f] : 1;
  const vals = Object.values(fam);
  const raw = union ? inter / union : 0;
  return { iou: raw, agree: care ? (cu ? ci / cu : 0) : raw, fam, zone: vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 1 };
}
