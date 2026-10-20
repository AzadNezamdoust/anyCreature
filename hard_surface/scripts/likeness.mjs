#!/usr/bin/env node
// WF-LOOP-R2 A4 — the first thing in this project that compares a PIXEL of the
// render with a PIXEL of the target.
//
//   node scripts/likeness.mjs <P> [--out <dir>]
//
// Inputs (all measured, none argued):
//   subjects/facade_brick/regions.json   FROZEN target px rects per zone
//   refs/tenement-iso.png                the TARGET
//   out/facade/P<N>/target.png           the judged still (flat capture, A1)
//   out/facade/P<N>/idpass.png           the same frame as a ROLE mask (A2)
//   out/facade/P<N>/target.png.json      capture sidecar -> manifest.palette
//
// Rows, in the same shape as the validator's V-codes so a failed likeness row
// reads like a failed rule and can enter the same K=1 repair slot:
//   LK_VALUE    render/target value ratio per zone          0.85-1.15
//               plus the two A1 face rows: front brick vs its own palette hex
//               (0.90-1.05) and side/front (0.80-0.92)
//   LK_HUE      render vs target hue difference per zone    <= 12 deg
//   LK_AREA     on-screen area share per role               within +-30 %
//   LK_OVERLAP  ironwork pixels inside a window's rect      0
//   LK_VISIBLE  mask pixels per census role                 >= 50
//
// DEVIATION (A4, "area share ... vs the target rect area share"): the rects in
// regions.json are SAMPLING PATCHES on flat colour (30 x 22 px of brick), not
// the zone's extent, so their own area share carries no information about the
// building. The target share measured here is instead the share of the brick
// building's classified pixels that fall nearest that zone's median, inside the
// `building` boxes regions.json freezes for exactly this purpose. Same quantity
// on the render side: role mask px / all mask px. Flagged for the orchestrator.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

import { loadSubject, subjectIdFromArgv } from "./subject.mjs";

const require = createRequire(import.meta.url);
const sharp = require("sharp");

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "..");

/** A4 thresholds. Unratified, like every other number in this harness. */
export const LIKENESS_LIMITS = Object.freeze({
  valueRatioMin: 0.85,
  valueRatioMax: 1.15,
  hueDeg: 12,
  areaShare: 0.30,
  visiblePx: 50,
  /** A1: the front face must render at its palette hex, the side 12 % under it. */
  frontVsPaletteMin: 0.90,
  frontVsPaletteMax: 1.05,
  /** r3 C2.2 / Fable M7 — the band is the TARGET's measured ratio +- this, at
   *  runtime. The frozen 0.80-0.92 pair below is kept only so a caller that
   *  still reads it does not crash; nothing in this file enforces it any more. */
  sideOverFrontTol: 0.05,
  sideOverFrontMin: 0.80,
  sideOverFrontMax: 0.92,
  /** A window component smaller than this is a sliver, not a window. */
  windowComponentPx: 200,
  /** WF-BLIND-R2 C6 — zones of one role whose target medians lie this close (RGB distance) are ONE material:
   *  colour cannot separate them, so the render is split by screen position instead. */
  sameMaterialRgb: 12,
  /** WF-BLIND-R2 C11 — a previously visible instance keeping less than this share of its pixels is lost. */
  keptShare: 0.5,
});

// WORKFLOW-V3 §7.5 — the class tables this file used to carry (census roles,
// census instance counts, iron / overlap / thin roles, and the five
// COMMENSURABLE LK_AREA families) are DATA in `classes/<class>.json` under
// `likeness`, handed to measureLikeness as `prior`.
//
// r3 C2.2 — LK_VISIBLE is per INSTANCE, not per role: a pooled 50 px passes a
// sign box entirely hidden behind a deck as long as some other part of the role
// is on screen (Astra "A4 >= 50 px per role"). `prior.censusInstances` maps one
// role to the census key (or the keys whose SUM) counting its separate blobs.
//
// r3 C2.2 — the families: both pictures are classified by the same
// nearest-median rule inside their own front-face quad, so a family share is
// "how much of the front plane this material covers" in both. Dropped zones
// still ABSORB pixels in the classifier but carry no row and no share.

/** census -> expected instance count for one role, or undefined when uncounted. */
export function instanceCount(prior, role, census) {
  const spec = prior?.censusInstances?.[role];
  if (!census || spec === undefined) return undefined;
  if (Array.isArray(spec)) return spec.reduce((sum, key) => sum + (census[key] ?? 0), 0);
  return census[spec];
}

/**
 * The Fable r3 audit's front-face frame, used ONLY when
 * subjects/facade_brick/layout.measured.json carries no measured face quad.
 * Every row built on it is reported as a FALLBACK.
 */
export const FALLBACK_FACE_PX = Object.freeze({ x0: 556, x1: 764, topY: 345, groundY: 895 });

// ---------------------------------------------------------------------------
// Pixels
// ---------------------------------------------------------------------------

async function readImage(file) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data, w: info.width, h: info.height, c: info.channels };
}

const at = (img, x, y) => {
  const i = (y * img.w + x) * img.c;
  return [img.data[i], img.data[i + 1], img.data[i + 2]];
};

function medianOf(samples) {
  if (samples.length === 0) return null;
  const out = [];
  for (let k = 0; k < 3; k += 1) {
    const channel = samples.map((s) => s[k]).sort((a, b) => a - b);
    out.push(channel[channel.length >> 1]);
  }
  return out;
}

export function hex(rgb) {
  return `#${rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
}

export function parseHex(text) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(text).trim());
  if (!m) throw new Error(`not a 6-digit hex colour: ${text}`);
  return [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16));
}

/** HSV, V in 0..1, H in degrees. The target is read in value/hue, not in RGB. */
export function hsv([r, g, b]) {
  const R = r / 255, G = g / 255, B = b / 255;
  const mx = Math.max(R, G, B), mn = Math.min(R, G, B), d = mx - mn;
  let h = 0;
  if (d > 1e-9) {
    if (mx === R) h = 60 * (((G - B) / d) % 6);
    else if (mx === G) h = 60 * ((B - R) / d + 2);
    else h = 60 * ((R - G) / d + 4);
  }
  if (h < 0) h += 360;
  return { h, s: mx === 0 ? 0 : d / mx, v: mx };
}

/** Shortest angular distance, degrees, 0..180. */
export function hueDelta(a, b) {
  const d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

const dist2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;

/**
 * WF-BLIND-R2 C6 — the FRONT tone of a flat-shaded member: the brightest of its six most frequent colours (the same
 * ranking brickFaces uses for the massing). Thin bars show far more side than front, so a median reads the side tone.
 */
export function frontTone(samples) {
  const histogram = new Map();
  for (const p of samples) {
    const key = `${p[0]},${p[1]},${p[2]}`;
    histogram.set(key, (histogram.get(key) ?? 0) + 1);
  }
  const top = [...histogram.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
  // a tone under a tenth of the most frequent one is an antialiased edge or a speck, not a face
  const ranked = top.filter(([, n]) => n >= 0.1 * top[0][1])
    .map(([key]) => key.split(",").map(Number)).sort((a, b) => hsv(b).v - hsv(a).v);
  return ranked[0] ?? null;
}

/** WF-BLIND-R2 C6 — 1-D k-means on screen y: `k` bands of [y, r, g, b] points, top band first, as rgb lists. */
export function yBands(points, k) {
  if (points.length === 0) return Array.from({ length: k }, () => []);
  const ys = points.map((p) => p[0]).sort((a, b) => a - b);
  let centres = Array.from({ length: k }, (_, i) => ys[Math.min(ys.length - 1, Math.floor(((i + 0.5) / k) * ys.length))]);
  const nearest = (y) => centres.reduce((best, c, i) => (Math.abs(y - c) < Math.abs(y - centres[best]) ? i : best), 0);
  for (let iter = 0; iter < 20; iter += 1) {
    const sums = centres.map(() => [0, 0]);
    for (const p of points) { const i = nearest(p[0]); sums[i][0] += p[0]; sums[i][1] += 1; }
    centres = sums.map((s, i) => (s[1] ? s[0] / s[1] : centres[i]));
  }
  const order = centres.map((c, i) => [c, i]).sort((a, b) => a[0] - b[0]).map(([, i]) => i);
  const bands = centres.map(() => []);
  for (const p of points) bands[nearest(p[0])].push([p[1], p[2], p[3]]);
  return order.map((i) => bands[i]);
}

/** WF-BLIND-R2 C11 — 4-connected components of one mask label, with their pixel indices. */
function componentPixels(mask, index, w, h, minPx) {
  const seen = new Uint8Array(mask.label.length);
  const out = [];
  const inSet = labelTest(index);
  for (let start = 0; start < mask.label.length; start += 1) {
    if (seen[start] || !inSet(mask.label[start])) continue;
    const pixels = [];
    const stack = [start];
    seen[start] = 1;
    while (stack.length) {
      const i = stack.pop();
      pixels.push(i);
      const x = i % w;
      const y = (i / w) | 0;
      for (const [j, ok] of [[i - 1, x > 0], [i + 1, x + 1 < w], [i - w, y > 0], [i + w, y + 1 < h]]) {
        if (ok && !seen[j] && inSet(mask.label[j])) { seen[j] = 1; stack.push(j); }
      }
    }
    if (pixels.length < minPx) continue;
    const xs = pixels.map((i) => i % w);
    const ys = pixels.map((i) => (i / w) | 0);
    out.push({ pixels, x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys),
      cx: xs.reduce((a, b) => a + b, 0) / xs.length, cy: ys.reduce((a, b) => a + b, 0) / ys.length });
  }
  return out;
}

/**
 * WF-BLIND-R2 C11 — author-frame point -> screen px, fitted from the capture manifest's two face quads
 * (world corners + px, 8 non-coplanar points) and turned by the render's frontRotationDeg (src/kernel/toThree.mjs
 * rotationY: x' = c x + s z, z' = -s x + c z). Null when the manifest cannot support a fit.
 */
export function screenProjector(manifest) {
  const pairs = [manifest?.frontQuad, manifest?.sideQuad]
    .flatMap((q) => (q && Array.isArray(q.world) && Array.isArray(q.px) ? q.world.map((w, i) => [w, q.px[i]]) : []));
  if (pairs.length < 8) return null;
  const solve = (col) => {
    const A = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
    const b = [0, 0, 0, 0];
    for (const [w, p] of pairs) {
      const row = [w[0], w[1], w[2], 1];
      for (let i = 0; i < 4; i += 1) { b[i] += row[i] * p[col]; for (let j = 0; j < 4; j += 1) A[i][j] += row[i] * row[j]; }
    }
    for (let i = 0; i < 4; i += 1) {
      let pivot = i;
      for (let r = i + 1; r < 4; r += 1) if (Math.abs(A[r][i]) > Math.abs(A[pivot][i])) pivot = r;
      if (Math.abs(A[pivot][i]) < 1e-12) return null;
      [A[i], A[pivot]] = [A[pivot], A[i]];
      [b[i], b[pivot]] = [b[pivot], b[i]];
      for (let r = 0; r < 4; r += 1) {
        if (r === i) continue;
        const f = A[r][i] / A[i][i];
        for (let c = i; c < 4; c += 1) A[r][c] -= f * A[i][c];
        b[r] -= f * b[i];
      }
    }
    return b.map((v, i) => v / A[i][i]);
  };
  const u = solve(0);
  const v = solve(1);
  if (!u || !v) return null;
  const deg = Number(manifest.frontRotationDeg ?? 0);
  const norm = ((deg % 360) + 360) % 360;
  const quarter = new Map([[0, [1, 0]], [90, [0, 1]], [180, [-1, 0]], [270, [0, -1]]]).get(norm);
  const [c, s] = quarter ?? [Math.cos(deg * Math.PI / 180), Math.sin(deg * Math.PI / 180)];
  return ([x, y, z]) => {
    const w = [c * x + s * z, y, -s * x + c * z, 1];
    return [u.reduce((sum, k, i) => sum + k * w[i], 0), v.reduce((sum, k, i) => sum + k * w[i], 0)];
  };
}

/** Screen bbox of an author-frame AABB under a projector. */
function screenBox(project, aabb) {
  const pts = [];
  for (const x of [aabb.min[0], aabb.max[0]]) for (const y of [aabb.min[1], aabb.max[1]]) for (const z of [aabb.min[2], aabb.max[2]]) pts.push(project([x, y, z]));
  return { x0: Math.min(...pts.map((p) => p[0])), x1: Math.max(...pts.map((p) => p[0])), y0: Math.min(...pts.map((p) => p[1])), y1: Math.max(...pts.map((p) => p[1])) };
}

// ---------------------------------------------------------------------------
// The render's role mask
// ---------------------------------------------------------------------------

/**
 * idpass.png -> one role label per pixel. The id colours round-trip exactly
 * through the sRGB capture, but nearest-with-a-cap is used anyway so a single
 * resampled edge pixel joins the role it came from instead of failing the run.
 * @returns {{label: Int16Array, roles: string[], counts: number[], total: number}}
 */
export function maskFromIdpass(idpass, idColours) {
  const roles = Object.keys(idColours);
  const rgbs = roles.map((r) => parseHex(idColours[r]));
  const label = new Int16Array(idpass.w * idpass.h).fill(-1);
  const counts = new Array(roles.length).fill(0);
  let total = 0;
  for (let y = 0; y < idpass.h; y += 1) {
    for (let x = 0; x < idpass.w; x += 1) {
      const p = at(idpass, x, y);
      let best = -1;
      let bestD = Infinity;
      for (let k = 0; k < rgbs.length; k += 1) {
        const d = dist2(p, rgbs[k]);
        if (d < bestD) { bestD = d; best = k; }
      }
      if (bestD > 24 * 24) continue;         // background / antialiased edge
      label[y * idpass.w + x] = best;
      counts[best] += 1;
      total += 1;
    }
  }
  return { label, roles, counts, total };
}

/**
 * The two flat brick tones. The capture is unlit and `paint()` gives a whole
 * plane one value, so the populated face and the return are literally two
 * colours inside the massing mask — the brightest big one is the front (the
 * front rotation puts it toward the camera), the next is the side.
 */
/**
 * WF-R5 R5-A — `minShare`: a FACE tone covers at least that share of the role's px. A flat unlit vehicle capture paints
 * the whole cab one tone; the darker tone of a handle or seam inlay the cab role also carries (a few % of its px) is a
 * feature, not the return face, and read as "side" it failed the unconstrained reference's body_front/body_side row at 0.81.
 */
export function brickFaces(still, mask, roleIndex, minShare = 0) {
  const histogram = new Map();
  for (let i = 0; i < mask.label.length; i += 1) {
    if (mask.label[i] !== roleIndex) continue;
    const x = i % still.w, y = (i / still.w) | 0;
    const key = at(still, x, y).join(",");
    histogram.set(key, (histogram.get(key) ?? 0) + 1);
  }
  const total = [...histogram.values()].reduce((a, b) => a + b, 0);
  const ranked = [...histogram.entries()]
    .map(([key, n]) => ({ rgb: key.split(",").map(Number), n }))
    .filter((e) => e.n >= minShare * total)
    .sort((a, b) => b.n - a.n)
    .slice(0, 6)
    .sort((a, b) => hsv(b.rgb).v - hsv(a.rgb).v);
  if (ranked.length === 0) return { front: null, side: null };
  return { front: ranked[0].rgb, side: ranked.length > 1 ? ranked[ranked.length - 1].rgb : null };
}

// ---------------------------------------------------------------------------
// The target's zone areas
// ---------------------------------------------------------------------------

/** Nearest zone median inside the frozen `building` boxes; far pixels abstain. */
function classifyTarget(target, regions) {
  const names = Object.keys(regions.zones);
  const medians = names.map((n) => regions.zones[n]._measured);
  const tol2 = (regions.areaTolerance ?? 32) ** 2;
  const counts = new Array(names.length).fill(0);
  let total = 0;
  for (const [bx, by, bw, bh] of regions.subjectBoxes ?? regions.building) {
    for (let y = by; y < by + bh; y += 1) {
      for (let x = bx; x < bx + bw; x += 1) {
        const p = at(target, x, y);
        let best = -1;
        let bestD = Infinity;
        for (let k = 0; k < medians.length; k += 1) {
          const d = dist2(p, medians[k]);
          if (d < bestD) { bestD = d; best = k; }
        }
        if (bestD > tol2) continue;
        counts[best] += 1;
        total += 1;
      }
    }
  }
  const byZone = {};
  names.forEach((n, k) => { byZone[n] = counts[k]; });
  return { byZone, total };
}

/**
 * WORKFLOW v4 V4-1 — classifyTarget per PIXEL (scripts/residuals.mjs): the same zone medians, tolerance and subject
 * boxes, one zone index per target px (-1 = abstains / outside the boxes). `img` = {data, w, h, c}.
 */
export function classifyTargetPixels(target, regions) {
  const names = Object.keys(regions.zones);
  // measureLikeness step (1): the frozen rects' median is the zone colour (computed here when not yet measured)
  const medians = names.map((n) => regions.zones[n]._measured ?? medianOf(regions.zones[n].rects
    .flatMap(([x, y, w, h]) => Array.from({ length: w * h }, (_, k) => at(target, x + (k % w), y + ((k / w) | 0))))));
  const tol2 = (regions.areaTolerance ?? 32) ** 2;
  const label = new Int16Array(target.w * target.h).fill(-1);
  for (const [bx, by, bw, bh] of regions.subjectBoxes ?? regions.building) {
    for (let y = Math.max(0, by); y < Math.min(target.h, by + bh); y += 1) {
      for (let x = Math.max(0, bx); x < Math.min(target.w, bx + bw); x += 1) {
        const p = at(target, x, y);
        let best = -1;
        let bestD = Infinity;
        for (let k = 0; k < medians.length; k += 1) {
          const d = dist2(p, medians[k]);
          if (d < bestD) { bestD = d; best = k; }
        }
        if (bestD <= tol2) label[y * target.w + x] = best;
      }
    }
  }
  return { label, names };
}

// ---------------------------------------------------------------------------
// r3 C2.2 — the two front-face quads, and the classifier that runs inside them
// ---------------------------------------------------------------------------

const isPair = (p) => Array.isArray(p) && p.length >= 2 && Number.isFinite(Number(p[0])) && Number.isFinite(Number(p[1]));
const isQuad = (q) => Array.isArray(q) && q.length === 4 && q.every(isPair);

/**
 * Find a measured front-face quad anywhere in `layout.measured.json`, whatever
 * the other seat called it. Accepts any 4-point pixel array whose key trail
 * mentions the face / the front / a quad (`face.px`, `frontQuad.px`,
 * `massing.face.quadPx`, `{value:[...]}` under one of those, ...). Defensive on
 * purpose: this file is written by another job and its exact key is not frozen.
 */
export function findFaceQuadPx(node, trail = []) {
  if (node == null || typeof node !== "object") return null;
  const named = trail.some((k) => /face|front|quad/i.test(k));
  if (Array.isArray(node)) {
    if (named && isQuad(node)) return node.map((p) => [Number(p[0]), Number(p[1])]);
    for (const v of node) {
      const hit = findFaceQuadPx(v, trail);
      if (hit) return hit;
    }
    return null;
  }
  for (const [k, v] of Object.entries(node)) {
    if (k.startsWith("_")) continue;
    const hit = findFaceQuadPx(v, [...trail, k]);
    if (hit) return hit;
  }
  return null;
}

/** Screen RISE per pixel to the right along a quad's longest horizontal edge. */
export function quadSlope(quadPx) {
  if (!isQuad(quadPx)) return null;
  let best = null;
  for (let i = 0; i < 4; i += 1) {
    const a = quadPx[i];
    const b = quadPx[(i + 1) % 4];
    const dx = b[0] - a[0];
    if (Math.abs(dx) < 1e-6) continue;
    if (best === null || Math.abs(dx) > Math.abs(best.dx)) best = { dx, dy: b[1] - a[1] };
  }
  if (best === null) return null;
  return -(best.dy / best.dx);   // y grows downward, so a negative dy is a RISE
}

/**
 * The target's front-face quad. Measured if the other job has written it,
 * otherwise the Fable audit's three numbers, sheared by the RENDER's own face
 * slope so the two quads at least have the same shape at the same camera. The
 * provenance string is carried into every row built on it.
 */
export function resolveTargetQuad(measured, renderQuad, measuredRel = loadSubject(subjectIdFromArgv()).rel.layoutMeasured) {
  const MEASURED_REL = measuredRel;
  const framed = measured?._frame?.quadPx;                     // WORKFLOW-V3 §7.1
  const found = isQuad(framed) ? framed.map((p) => [Number(p[0]), Number(p[1])])
    : (measured ? findFaceQuadPx(measured) : null);
  if (found) return { px: found, measured: true, provenance: `${MEASURED_REL} (measured face quad)` };
  const { x0, x1, topY, groundY } = FALLBACK_FACE_PX;
  const slope = quadSlope(renderQuad?.px ?? null);
  const dy = slope === null ? 0 : slope * (x1 - x0);
  const how = slope === null
    ? "rectangle — no render quad to take the face slope from"
    : `parallelogram, face slope ${slope.toFixed(3)} px/px taken from the render's own front quad`;
  return {
    px: [[x0, topY], [x1, topY - dy], [x1, groundY - dy], [x0, groundY]],
    measured: false,
    provenance: `FALLBACK — no measured face quad in ${MEASURED_REL}; Fable r3 audit x ${x0}-${x1}, `
      + `wall top y ${topY}, ground y ${groundY} at x ${x0}; ${how}`,
  };
}

/** Convex-polygon containment: every edge cross-product on the same side. */
export function pointInQuad(quadPx, x, y) {
  let pos = 0;
  let neg = 0;
  for (let i = 0; i < 4; i += 1) {
    const [ax, ay] = quadPx[i];
    const [bx, by] = quadPx[(i + 1) % 4];
    const c = (bx - ax) * (y - ay) - (by - ay) * (x - ax);
    if (c > 1e-9) pos += 1;
    else if (c < -1e-9) neg += 1;
  }
  return pos === 0 || neg === 0;
}

/**
 * Nearest zone median inside ONE quad. Same rule, same medians, same tolerance
 * for the target image and for the render's flat still — that is the whole point
 * of C2.2: two shares of the same quantity instead of two whole pictures.
 */
export function classifyInQuad(image, quadPx, zoneNames, medians, tol) {
  const tol2 = tol * tol;
  const byZone = {};
  zoneNames.forEach((n) => { byZone[n] = 0; });
  const xs = quadPx.map((p) => p[0]);
  const ys = quadPx.map((p) => p[1]);
  const x0 = Math.max(0, Math.floor(Math.min(...xs)));
  const x1 = Math.min(image.w - 1, Math.ceil(Math.max(...xs)));
  const y0 = Math.max(0, Math.floor(Math.min(...ys)));
  const y1 = Math.min(image.h - 1, Math.ceil(Math.max(...ys)));
  let inside = 0;
  let classified = 0;
  for (let y = y0; y <= y1; y += 1) {
    for (let x = x0; x <= x1; x += 1) {
      if (!pointInQuad(quadPx, x + 0.5, y + 0.5)) continue;
      inside += 1;
      const p = at(image, x, y);
      let best = -1;
      let bestD = Infinity;
      for (let k = 0; k < medians.length; k += 1) {
        const d = dist2(p, medians[k]);
        if (d < bestD) { bestD = d; best = k; }
      }
      if (bestD > tol2) continue;
      byZone[zoneNames[best]] += 1;
      classified += 1;
    }
  }
  return { byZone, inside, classified };
}

/** Family counts and shares, normalised over the COUNTED families only. */
export function familyShares(byZone, families) {
  const counts = {};
  let total = 0;
  for (const [family, zones] of Object.entries(families)) {
    const n = zones.reduce((a, z) => a + (byZone[z] ?? 0), 0);
    counts[family] = n;
    total += n;
  }
  const share = {};
  for (const family of Object.keys(families)) share[family] = total ? counts[family] / total : 0;
  return { counts, share, total };
}

// ---------------------------------------------------------------------------
// Screen-space rows
// ---------------------------------------------------------------------------

/** 4-connected components of one role's mask, as bounding rects. */
/** A label predicate: one role index, or a Set of indices (WF-R3 H2: an instance's own assembly roles). */
function labelTest(index) {
  return index instanceof Set ? (l) => index.has(l) : (l) => l === index;
}

function components(mask, roleIndex, w, h, minPx) {
  const seen = new Uint8Array(mask.label.length);
  const rects = [];
  const stack = [];
  const inSet = labelTest(roleIndex);
  for (let start = 0; start < mask.label.length; start += 1) {
    if (seen[start] || !inSet(mask.label[start])) continue;
    let n = 0, minX = w, maxX = -1, minY = h, maxY = -1;
    stack.length = 0;
    stack.push(start);
    seen[start] = 1;
    while (stack.length) {
      const i = stack.pop();
      const x = i % w, y = (i / w) | 0;
      n += 1;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
      if (x > 0 && !seen[i - 1] && inSet(mask.label[i - 1])) { seen[i - 1] = 1; stack.push(i - 1); }
      if (x + 1 < w && !seen[i + 1] && inSet(mask.label[i + 1])) { seen[i + 1] = 1; stack.push(i + 1); }
      if (y > 0 && !seen[i - w] && inSet(mask.label[i - w])) { seen[i - w] = 1; stack.push(i - w); }
      if (y + 1 < h && !seen[i + w] && inSet(mask.label[i + w])) { seen[i + w] = 1; stack.push(i + w); }
    }
    if (n >= minPx) rects.push({ x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1, px: n });
  }
  return rects;
}

// ---------------------------------------------------------------------------
// The measurement
// ---------------------------------------------------------------------------

const make = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint, blocking: true });

/**
 * @param {object} io {regions, target, still, idpass, palette, targetQuad, renderQuad, census,
 *   prior: the class prior's `likeness` block, censusRel: census path for messages}
 * @returns {{pass:boolean, violations:Array, zones:object, areas:object, text:string}}
 */
export function measureLikeness({ regions, target, still, idpass, palette, targetQuad = null, renderQuad = null, census = null, prior, censusRel = "census.json", occlusion = null, silhouette = null }) {
  if (!prior || !prior.areaFamilies) throw new Error("measureLikeness needs `prior` — the class prior's likeness block (classes/<class>.json)");
  const L = LIKENESS_LIMITS;
  const AREA_FAMILIES = prior.areaFamilies;
  const violations = [];
  const advisories = [];
  // r3 C2.2 / Astra C10 — every row carries its own verdict: PASS, FAIL or
  // UNVERIFIED. "Not measured" is no longer spelled "clean".
  const rows = [];
  const row = (v, part, verdict, measured, limit, hint, blocking = true) => {
    const r = { v, part, verdict, measured, limit, hint, blocking };
    rows.push(r);
    if (verdict === "FAIL") (blocking ? violations : advisories).push({ ...make(v, part, measured, limit, hint), blocking });
    return r;
  };

  // (1) the frozen rects -> the target's colour per zone. The pixels are the
  //     authority; regions.json's `median` is only the record of what was frozen.
  for (const [name, zone] of Object.entries(regions.zones)) {
    const samples = [];
    for (const [x, y, w, h] of zone.rects) {
      for (let j = y; j < y + h; j += 1) for (let i = x; i < x + w; i += 1) samples.push(at(target, i, j));
    }
    zone._measured = medianOf(samples);
    zone._px = samples.length;
  }

  const idColours = idpass.idColours;
  const mask = maskFromIdpass(idpass.image, idColours);
  const roleIndex = (role) => mask.roles.indexOf(role);

  // (2) the render's colour per role, inside that role's mask.
  const renderMedian = {};
  const renderSamples = {};
  const renderPoints = {};                   // WF-BLIND-R2 C6: [y, r, g, b] per role
  for (let k = 0; k < mask.roles.length; k += 1) {
    if (mask.counts[k] === 0) continue;
    const samples = [];
    const points = [];
    for (let i = 0; i < mask.label.length; i += 1) {
      if (mask.label[i] !== k) continue;
      const y = (i / still.w) | 0;
      const p = at(still, i % still.w, y);
      samples.push(p);
      points.push([y, p[0], p[1], p[2]]);
    }
    renderMedian[mask.roles[k]] = medianOf(samples);
    renderSamples[mask.roles[k]] = samples;
    renderPoints[mask.roles[k]] = points;
  }
  // run3 P1 fix: two zones on one role (frame + glass are both role "window") share a
  // mask, so the role median is the bigger zone's colour and the other zone always
  // "fails". Split the role's pixels among its zones by nearest PALETTE hex (the
  // module's own declared colours), then take each zone's median. A zone that wins
  // fewer than 25 px keeps the role median (and its row says so).
  const zoneMedian = {};
  const zoneTone = {};                       // WF-BLIND-R2 C6: front tone for a non-massing zone marked face "front"
  {
    const byRole = {};
    const faceRole = prior.faceRole ?? "massing";
    const rectCy = (name) => {
      const rects = regions.zones[name].rects ?? [];
      return rects.reduce((sum, [, y, , h]) => sum + y + h / 2, 0) / Math.max(1, rects.length);
    };
    for (const [name, zone] of Object.entries(regions.zones)) (byRole[zone.role] ??= []).push(name);
    for (const [role, names] of Object.entries(byRole)) {
      if (!renderSamples[role]) continue;
      const wantsFront = (name) => regions.zones[name].face === "front" && role !== faceRole;
      if (names.length < 2) {
        if (wantsFront(names[0])) zoneTone[names[0]] = frontTone(renderSamples[role]);
        else if (palette && regions.zones[names[0]]._measured) {
          // WF-R5 R5-A — ONE zone on a role whose parts carry two palette tones (the two-tone grille: body-tone bars round
          // grille-tone slot inlays): the zone is the role's px nearest the palette hex nearest the zone's own target tone.
          const hexes = Object.values(palette).map(parseHex).filter(Boolean);
          const near = (p) => hexes.reduce((b, h) => (dist2(p, h) < dist2(p, b) ? h : b));
          const mine = near(regions.zones[names[0]]._measured);
          const own = renderSamples[role].filter((p) => near(p) === mine);
          if (own.length >= 25 && own.length < renderSamples[role].length) zoneMedian[names[0]] = medianOf(own);
        }
        continue;
      }
      // WF-BLIND-R2 C6 — one material under two names (upper / lower landing): split by screen position, top first.
      const sameMaterial = names.every((a) => names.every((b) =>
        Math.sqrt(dist2(regions.zones[a]._measured, regions.zones[b]._measured)) <= L.sameMaterialRgb));
      if (sameMaterial) {
        const order = [...names].sort((a, b) => rectCy(a) - rectCy(b));
        const bands = yBands(renderPoints[role], order.length);
        order.forEach((name, i) => {
          if (bands[i].length < 25) return;
          zoneMedian[name] = medianOf(bands[i]);
          if (wantsFront(name)) zoneTone[name] = frontTone(bands[i]);
        });
        continue;
      }
      // Palette keys are the author's own names (trim/enamel/...), so the split
      // cannot rely on them: k-means (k = zones) on the role's render pixels, then
      // each cluster goes to the zone whose TARGET colour is nearest.
      const px = renderSamples[role];
      const k = names.length;
      let centres = names.map((n) => regions.zones[n]._measured.slice());
      for (let iter = 0; iter < 8; iter += 1) {
        const sums = centres.map(() => [0, 0, 0, 0]);
        for (const p of px) {
          let best = 0, bd = Infinity;
          centres.forEach((c, i) => { const d = (p[0]-c[0])**2 + (p[1]-c[1])**2 + (p[2]-c[2])**2; if (d < bd) { bd = d; best = i; } });
          const s = sums[best]; s[0] += p[0]; s[1] += p[1]; s[2] += p[2]; s[3] += 1;
        }
        centres = sums.map((s, i) => (s[3] ? [s[0] / s[3], s[1] / s[3], s[2] / s[3]] : centres[i]));
      }
      const buckets = names.map(() => []);
      for (const p of px) {
        let best = 0, bd = Infinity;
        centres.forEach((c, i) => { const d = (p[0]-c[0])**2 + (p[1]-c[1])**2 + (p[2]-c[2])**2; if (d < bd) { bd = d; best = i; } });
        buckets[best].push(p);
      }
      // cluster i -> zone whose target colour is nearest to the cluster centre
      const taken = new Set();
      centres.forEach((c, i) => {
        let bestZone = null, bd = Infinity;
        names.forEach((n) => { if (taken.has(n)) return; const t = regions.zones[n]._measured; const d = (t[0]-c[0])**2 + (t[1]-c[1])**2 + (t[2]-c[2])**2; if (d < bd) { bd = d; bestZone = n; } });
        if (bestZone && buckets[i].length >= 25) { zoneMedian[bestZone] = medianOf(buckets[i]); taken.add(bestZone); }
      });
      void k;
    }
  }

  // (3) area shares.
  const targetAreas = classifyTarget(target, regions);
  const targetByRole = {};
  for (const [name, zone] of Object.entries(regions.zones)) {
    targetByRole[zone.role] = (targetByRole[zone.role] ?? 0) + targetAreas.byZone[name];
  }
  const targetRoleTotal = Object.values(targetByRole).reduce((a, b) => a + b, 0) || 1;

  // (4) the two A1 face rows, measured off the flat brick tones.
  // WORKFLOW-V3 §7.10 — which role, zones and palette key carry the two flat face tones is class data.
  const FACE_ROLE = prior.faceRole ?? "massing";
  const FRONT_ZONE = prior.faceZones?.front ?? "brick_front";
  const SIDE_ZONE = prior.faceZones?.side ?? "brick_side_strip";
  const FACE_KEY = prior.facePaletteKey ?? "brick";
  const SIDE_ROW = prior.faceZones ? `${SIDE_ZONE}/${FRONT_ZONE}` : "brick_side/front";
  const faces = brickFaces(still, mask, roleIndex(FACE_ROLE), prior.faceMinShare ?? 0);
  const facesOut = { frontHex: faces.front ? hex(faces.front) : null, sideHex: faces.side ? hex(faces.side) : null };
  const paletteBrick = palette && palette[FACE_KEY] ? parseHex(palette[FACE_KEY]) : null;
  if (faces.front && paletteBrick) {
    const ratio = hsv(faces.front).v / hsv(paletteBrick).v;
    facesOut.frontVsPalette = round3(ratio);
    row("LK_VALUE", `${FRONT_ZONE}/palette`,
      ratio < L.frontVsPaletteMin || ratio > L.frontVsPaletteMax ? "FAIL" : "PASS",
      `${ratio.toFixed(3)}x (${hex(faces.front)} vs ${palette[FACE_KEY]})`,
      `${L.frontVsPaletteMin}-${L.frontVsPaletteMax}`,
      "the capture must show the palette hex on the populated face");
  } else {
    row("LK_VALUE", `${FRONT_ZONE}/palette`, "UNVERIFIED", "no flat front tone or no palette in the manifest",
      `${L.frontVsPaletteMin}-${L.frontVsPaletteMax}`, "the still carries no massing mask or no palette");
  }
  // r3 C2.2 / Fable M7 — the side/front band is the TARGET's own ratio +-0.05,
  // recomputed from the region medians at runtime. The frozen 0.80-0.92 was
  // written off r2's wrong side sample and passed today's 0.883 (Fable L8).
  const targetSideOverFront = (regions.zones[SIDE_ZONE]?._measured && regions.zones[FRONT_ZONE]?._measured)
    ? hsv(regions.zones[SIDE_ZONE]._measured).v / hsv(regions.zones[FRONT_ZONE]._measured).v
    : null;
  facesOut.targetSideOverFront = targetSideOverFront === null ? null : round3(targetSideOverFront);
  facesOut.sideOverFrontBand = targetSideOverFront === null ? null
    : [round3(targetSideOverFront - L.sideOverFrontTol), round3(targetSideOverFront + L.sideOverFrontTol)];
  if (faces.front && faces.side && targetSideOverFront !== null) {
    const ratio = hsv(faces.side).v / hsv(faces.front).v;
    facesOut.sideOverFront = round3(ratio);
    const [lo, hi] = facesOut.sideOverFrontBand;
    row("LK_VALUE", SIDE_ROW, ratio < lo || ratio > hi ? "FAIL" : "PASS",
      `${ratio.toFixed(3)}x`, `${lo}-${hi} (target ${round3(targetSideOverFront)} +-${L.sideOverFrontTol}, measured at runtime)`,
      "the return must read exactly as much darker than the front as the target's does");
  } else {
    if (faces.front && faces.side) facesOut.sideOverFront = round3(hsv(faces.side).v / hsv(faces.front).v);
    row("LK_VALUE", SIDE_ROW, "UNVERIFIED",
      faces.side ? `regions.json carries no ${SIDE_ZONE}/${FRONT_ZONE} medians` : "no second flat brick tone in the still",
      "target ratio +-0.05", "the band is the target's own side/front value ratio");
  }

  // (5) per-zone value / hue, and per-role area.
  const zones = {};
  const seenRoleArea = new Set();
  for (const [name, zone] of Object.entries(regions.zones)) {
    const t = zone._measured;
    // A zone that names a FACE is measured against that flat tone, not against
    // the role's median: `massing` holds the front, the return and every window
    // reveal, and their median is none of the three.
    const r = (zone.face === "front" && faces.front && zone.role === FACE_ROLE) ? faces.front
      : (zone.face === "side" && faces.side) ? faces.side
        : (zoneTone[name] ?? zoneMedian[name] ?? renderMedian[zone.role] ?? null);
    const tHsv = hsv(t);
    const zoneRow = {
      role: zone.role,
      targetHex: hex(t),
      renderHex: r ? hex(r) : null,
      targetV: round3(tHsv.v),
      renderV: r ? round3(hsv(r).v) : null,
      valueRatio: null,
      hueDelta: null,
      targetAreaShare: round4(targetAreas.byZone[name] / targetRoleTotal),
      renderAreaShare: round4((mask.counts[roleIndex(zone.role)] ?? 0) / (mask.total || 1)),
      maskPx: mask.counts[roleIndex(zone.role)] ?? 0,
      rectPx: zone._px,
      sharesRoleWith: Object.entries(regions.zones)
        .filter(([other, z]) => other !== name && z.role === zone.role).map(([other]) => other),
    };
    if (r) {
      const rHsv = hsv(r);
      zoneRow.valueRatio = round3(rHsv.v / (tHsv.v || 1e-6));
      zoneRow.hueDelta = round1(hueDelta(rHsv.h, tHsv.h));
      row("LK_VALUE", name,
        zoneRow.valueRatio < L.valueRatioMin || zoneRow.valueRatio > L.valueRatioMax ? "FAIL" : "PASS",
        `${zoneRow.valueRatio.toFixed(2)}x (${zoneRow.renderHex} vs ${zoneRow.targetHex})`,
        `${L.valueRatioMin}-${L.valueRatioMax}`, `zone ${name} renders at the wrong value`);
      row("LK_HUE", name, zoneRow.hueDelta > L.hueDeg ? "FAIL" : "PASS",
        `${zoneRow.hueDelta.toFixed(0)} deg (${zoneRow.renderHex} vs ${zoneRow.targetHex})`,
        `<= ${L.hueDeg} deg`, `zone ${name} renders at the wrong hue`);
    } else {
      row("LK_VISIBLE", name, "FAIL", "0 mask px", `>= ${L.visiblePx} px`,
        `role "${zone.role}" is not on screen at the solved camera`);
    }
    zones[name] = zoneRow;
  }
  void seenRoleArea;

  // (5b) r3 C2.2 — LK_AREA, commensurable and BLOCKING. Both pictures are
  // classified by the SAME nearest-median rule inside their OWN front-face quad,
  // so "what share of the front plane is brick" is a quantity both of them have.
  // The r2 row normalised by "classified building pixels" of two differently
  // occluded pictures (Fable C2 / Astra C6) and every advisory it fired was an
  // artefact of that.
  const areaFamilies = { target: null, render: null, rows: {} };
  const quadTarget = targetQuad && isQuad(targetQuad.px) ? targetQuad : null;
  const quadRender = renderQuad && isQuad(renderQuad.px) ? renderQuad : null;
  if (!quadTarget || !quadRender) {
    const why = !quadRender
      ? "the capture manifest carries no frontQuad (re-capture with the r3 app.js)"
      : "no target front-face quad could be resolved";
    for (const family of Object.keys(AREA_FAMILIES)) {
      row("LK_AREA", family, "UNVERIFIED", why, `within +-${(L.areaShare * 100).toFixed(0)}%`,
        "the front-face quads are the frame this row is measured in");
    }
  } else {
    const zoneNames = Object.keys(regions.zones);
    const medians = zoneNames.map((n) => regions.zones[n]._measured);
    const tol = regions.areaTolerance ?? 32;
    const tClass = classifyInQuad(target, quadTarget.px, zoneNames, medians, tol);
    const rClass = classifyInQuad(still, quadRender.px, zoneNames, medians, tol);
    const tFam = familyShares(tClass.byZone, AREA_FAMILIES);
    const rFam = familyShares(rClass.byZone, AREA_FAMILIES);
    areaFamilies.target = { ...tFam, quad: quadTarget.px, inside: tClass.inside, classified: tClass.classified, provenance: quadTarget.provenance, measuredQuad: quadTarget.measured };
    areaFamilies.render = { ...rFam, quad: quadRender.px, inside: rClass.inside, classified: rClass.classified, provenance: "capture manifest frontQuad", measuredQuad: true };
    for (const family of Object.keys(AREA_FAMILIES)) {
      const tShare = tFam.share[family];
      const rShare = rFam.share[family];
      const measured = `${(rShare * 100).toFixed(1)}% vs ${(tShare * 100).toFixed(1)}%`;
      if (!(tShare > 0.002)) {
        row("LK_AREA", family, "UNVERIFIED", `${measured} — target share under 0.2 % of the front plane`,
          `within +-${(L.areaShare * 100).toFixed(0)}%`, `family ${family} is not measurable in the target's front quad`);
        areaFamilies.rows[family] = { tShare: round4(tShare), rShare: round4(rShare), ratio: null, verdict: "UNVERIFIED" };
        continue;
      }
      const ratio = rShare / tShare;
      const verdict = Math.abs(ratio - 1) > L.areaShare ? "FAIL" : "PASS";
      row("LK_AREA", family, verdict, `${measured} (${ratio.toFixed(2)}x)`,
        `within +-${(L.areaShare * 100).toFixed(0)}% of the target share`,
        `family ${family} covers the wrong share of the FRONT FACE`);
      areaFamilies.rows[family] = { tShare: round4(tShare), rShare: round4(rShare), ratio: round3(ratio), verdict };
    }
    if (!quadTarget.measured) {
      advisories.push(make("LK_AREA", "target-quad", quadTarget.provenance, "a measured face quad",
        "every LK_AREA row above is built on the FALLBACK frame, not a measurement"));
    }
  }

  // (5c) WF-R3 R3-B item 5 — LK_SILHOUETTE: SHAPE, not colour. A vertical box cab passed every row; the target's
  // windshield rakes back. IoU of the target's foreground (the render px mapped onto the target through the two
  // measured face quads) with the render's role mask, inside the class's silhouette region (classes/<class>.json
  // likeness.silhouette; the region is an author-frame box of measured keys, projected at the render's camera).
  if (prior.silhouette) {
    const band = prior.silhouette.iouMin;
    if (!silhouette?.hull || !quadTarget || !quadRender) {
      row("LK_SILHOUETTE", prior.silhouette.part ?? "shape", "UNVERIFIED", silhouette?.why ?? "no silhouette region or face quads",
        `IoU >= ${band}`, prior.silhouette.what ?? "the silhouette region is measured in the render's frame");
    } else {
      const iou = silhouetteIoU({ target, mask, w: idpass.image.w, h: idpass.image.h, hull: silhouette.hull, renderQuad: quadRender.px, targetQuad: quadTarget.px });
      row("LK_SILHOUETTE", prior.silhouette.part ?? "shape", iou.iou < band ? "FAIL" : "PASS",
        `IoU ${iou.iou.toFixed(3)} (${iou.inter} / ${iou.union} px)`, `>= ${band}`,
        prior.silhouette.what ?? "the render's outline differs from the target's in the silhouette region");
    }
  }

  // (6) SCREEN_OVERLAP — ironwork inside a window's projected rect.
  let overlapPx = 0;
  const windowRects = components(mask, roleIndex("window"), idpass.image.w, idpass.image.h, L.windowComponentPx);
  // run3 P2: the target's LANDINGS do cross the window column; only the roof LADDER
  // must stay clear of the windows (audit r2 Fable L5). Ladder + rung only.
  const ironIdx = new Set((prior.overlapRoles ?? []).map(roleIndex).filter((i) => i >= 0));
  for (const rect of windowRects) {
    let n = 0;
    for (let y = rect.y; y < rect.y + rect.h; y += 1) {
      for (let x = rect.x; x < rect.x + rect.w; x += 1) {
        if (ironIdx.has(mask.label[y * idpass.image.w + x])) n += 1;
      }
    }
    overlapPx += n;
  }
  row("LK_OVERLAP", "window", overlapPx > 0 ? "FAIL" : "PASS",
    `${overlapPx} iron px inside ${windowRects.length} window rect(s)`,
    "0 px", "ironwork must not cross a window opening on screen (target keeps them apart)");

  // (7) r3 C2.2 — VISIBLE per INSTANCE. A census assembly is on screen when it
  // owns its own blob of >= 50 id-pass pixels; `landing: 3866 px` said nothing
  // about whether BOTH landings could be seen, and the pooled row passed a sign
  // box completely hidden behind a deck (Astra "A4 >= 50px per role").
  const visible = {};
  const THIN = new Set(prior.thinRoles ?? []);
  for (const role of prior.censusRoles ?? []) {
    const idx = roleIndex(role);
    // WF-R3 H2 — an instance's OWN assembly parts (a wheel's tyre and hub) are never its occluders: they count toward
    // its visible px and its blob. Both blind pickup P1 seats ended on "wheel covered by hub_rl" (template geometry).
    const own = ownLabels(prior, role, mask);
    const px = [...own].reduce((n, k) => n + (mask.counts[k] ?? 0), 0);
    const comps = idx >= 0 ? components(mask, own, idpass.image.w, idpass.image.h, L.visiblePx) : [];
    const counted = census && prior.censusInstances?.[role] !== undefined ? instanceCount(prior, role, census) : null;
    // WORKFLOW-V3 §5 — a role the target itself shows fewer of than it counts (occluded far-side wheels).
    const expected = Number.isFinite(prior.visibleInstances?.[role]) && Number.isFinite(counted)
      ? Math.min(counted, prior.visibleInstances[role]) : counted;
    visible[role] = { px, instances: comps.length, expected, componentPx: comps.map((c) => c.px).sort((a, b) => b - a) };
    if (expected === null || expected === undefined || !Number.isFinite(expected)) {
      row("LK_VISIBLE", role, "UNVERIFIED", `${comps.length} instance(s), ${px} px`,
        `>= census count, each >= ${L.visiblePx} px`,
        `${censusRel} declares no instance count for role ${role}`);
      continue;
    }
    // run4 P2: thin members (stringer, rung, baluster) fragment behind treads and
    // rails into blobs under 50 px each; for those roles the pooled px decides.
    const seen = THIN.has(role) ? (px >= L.visiblePx * expected ? expected : 0) : comps.length;
    const lost = seen < expected ? lostInstances({ occlusion, mask, role, w: idpass.image.w, h: idpass.image.h, ownRoles: prior.instanceRoles?.[role] }) : [];
    visible[role].lost = lost;
    row("LK_VISIBLE", role, seen >= expected ? "PASS" : "FAIL",
      `${seen} of ${expected} instance(s) >= ${L.visiblePx} px (${px} px total)`,
      `${expected} instance(s), each >= ${L.visiblePx} px`,
      `${expected - comps.length} ${role} assembly/assemblies the census counts cannot be seen at the solved camera `
      + (lost.length
        ? `— ${lost.map((l) => `the ${role} seen at ${l.previousLabel} (px x ${l.x0}..${l.x1}, y ${l.y0}..${l.y1}) is now covered by `
          + `${l.part ? `part "${l.part}" (role ${l.role})` : `role "${l.role}"`}`).join("; ")}`
        : "(hidden behind another part, or merged into one blob)"));
  }

  return {
    advisories,
    rows,
    unverified: rows.filter((r) => r.verdict === "UNVERIFIED"),
    pass: violations.length === 0,
    violations,
    zones,
    faces: facesOut,
    areas: { targetByRole, targetRoleTotal, renderByRole: roleCounts(mask), renderTotal: mask.total },
    areaFamilies,
    quads: { target: quadTarget, render: quadRender },
    windows: windowRects.length,
    overlapPx,
    visible,
    text: likenessText(violations, advisories, rows.filter((r) => r.verdict === "UNVERIFIED")),
  };
}

/**
 * WF-BLIND-R2 C11 — instances of `role` that were their own blob in the PREVIOUS pass's id pass and keep less than
 * keptShare of their pixels now, each with the role (and, when the capture manifest and the report's per-part AABBs
 * allow a projection, the part) that covers most of them.
 */
// ---------------------------------------------------------------------------
// WF-R3 R3-B item 5 — LK_SILHOUETTE geometry. Pure functions (tests call them on frozen id passes).
// ---------------------------------------------------------------------------

/** Target px counts as foreground when its darkest channel is under this (the target is drawn on near-white). */
export const SILHOUETTE_FG_MAX = 235;

function solveN(A, b) {
  const n = b.length;
  const M = A.map((r, i) => [...r, b[i]]);
  for (let c = 0; c < n; c += 1) {
    let p = c;
    for (let r = c + 1; r < n; r += 1) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < n; r += 1) {
      if (r === c) continue;
      const f = M[r][c] / M[c][c];
      for (let k = c; k <= n; k += 1) M[r][k] -= f * M[c][k];
    }
  }
  return M.map((r, i) => r[n] / r[i]);
}

/** The plane homography taking quad `src` (4 px corners) onto quad `dst`: (x, y) -> [u, v]. */
export function quadHomography(src, dst) {
  const A = [];
  const b = [];
  for (let i = 0; i < 4; i += 1) {
    const [x, y] = src[i];
    const [u, v] = dst[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
  }
  const h = solveN(A, b);
  return (x, y) => { const w = h[6] * x + h[7] * y + 1; return [(h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w]; };
}

/** Convex hull (CCW in screen px) of points. */
export function convexHull(points) {
  const p = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [];
  const up = [];
  for (const q of p) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (const q of [...p].reverse()) { while (up.length >= 2 && cross(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}

function inHull(h, x, y) {
  for (let i = 0; i < h.length; i += 1) {
    const a = h[i];
    const b = h[(i + 1) % h.length];
    if ((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]) < 0) return false;
  }
  return true;
}

/** The screen hull of an author-frame box {x, y, z: [lo, hi]} under the render's projector, or null. */
export function silhouetteHull(box, manifest) {
  const project = screenProjector(manifest);
  if (!project || !box) return null;
  const pts = [];
  for (const x of box.x) for (const y of box.y) for (const z of box.z) pts.push(project([x, y, z]));
  return convexHull(pts);
}

/** IoU of target foreground (render px mapped through the face quads) and the render mask, inside `hull`. */
export function silhouetteIoU({ target, mask, w, h, hull, renderQuad, targetQuad, fgMax = SILHOUETTE_FG_MAX }) {
  const toTarget = quadHomography(renderQuad, targetQuad);
  let inter = 0;
  let union = 0;
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      if (!inHull(hull, x + 0.5, y + 0.5)) continue;
      const [u, v] = toTarget(x + 0.5, y + 0.5);
      const tx = Math.round(u - 0.5);
      const ty = Math.round(v - 0.5);
      const a = tx >= 0 && ty >= 0 && tx < target.w && ty < target.h && Math.min(...at(target, tx, ty)) < fgMax;
      const b = mask.label[y * w + x] >= 0;
      if (a && b) inter += 1;
      if (a || b) union += 1;
    }
  }
  return { iou: union > 0 ? inter / union : 0, inter, union };
}

/** WF-R3 H2 — the mask labels one instance of `role` is made of: the role plus classes/<class>.json likeness.instanceRoles[role]. */
export function ownLabels(prior, role, mask) {
  return new Set([role, ...(prior?.instanceRoles?.[role] ?? [])].map((r) => mask.roles.indexOf(r)).filter((k) => k >= 0));
}

export function lostInstances({ occlusion, mask, role, w, h, ownRoles = null }) {
  if (!occlusion?.previous) return [];
  const prev = maskFromIdpass(occlusion.previous.image, occlusion.previous.idColours);
  const prevIndex = prev.roles.indexOf(role);
  const index = mask.roles.indexOf(role);
  // WF-R3 H2 — the instance's own assembly roles (wheel + tyre + hub) keep it visible and never cover it.
  const own = new Set([role, ...(ownRoles ?? [])].map((r) => mask.roles.indexOf(r)).filter((k) => k >= 0));
  const prevOwn = new Set([role, ...(ownRoles ?? [])].map((r) => prev.roles.indexOf(r)).filter((k) => k >= 0));
  if (prevIndex < 0 || occlusion.previous.image.w !== w || occlusion.previous.image.h !== h) return [];
  const project = occlusion.manifest ? screenProjector(occlusion.manifest) : null;
  const out = [];
  for (const comp of componentPixels(prev, prevOwn.size > 1 ? prevOwn : prevIndex, w, h, LIKENESS_LIMITS.visiblePx)) {
    const tally = new Map();
    let kept = 0;
    for (const i of comp.pixels) {
      const label = mask.label[i];
      if (label === index || own.has(label)) { kept += 1; continue; }
      if (label >= 0) tally.set(label, (tally.get(label) ?? 0) + 1);
    }
    if (kept >= LIKENESS_LIMITS.keptShare * comp.pixels.length || tally.size === 0) continue;
    const [coverIndex] = [...tally.entries()].sort((a, b) => b[1] - a[1])[0];
    const coverRole = mask.roles[coverIndex];
    let part = null;
    if (project && Array.isArray(occlusion.parts)) {
      const hits = occlusion.parts.filter((p) => p.role === coverRole && p.aabb)
        .map((p) => ({ id: p.id, box: screenBox(project, p.aabb) }))
        .filter(({ box }) => comp.cx >= box.x0 && comp.cx <= box.x1 && comp.cy >= box.y0 && comp.cy <= box.y1)
        .sort((a, b) => (a.box.x1 - a.box.x0) * (a.box.y1 - a.box.y0) - (b.box.x1 - b.box.x0) * (b.box.y1 - b.box.y0));
      part = hits[0]?.id ?? null;
    }
    out.push({ previousLabel: occlusion.label ?? "the previous pass", x0: comp.x0, x1: comp.x1, y0: comp.y0, y1: comp.y1, role: coverRole, part, kept, px: comp.pixels.length });
  }
  return out;
}

function roleCounts(mask) {
  const out = {};
  mask.roles.forEach((r, k) => { if (mask.counts[k] > 0) out[r] = mask.counts[k]; });
  return out;
}

const round1 = (x) => Math.round(x * 10) / 10;
const round3 = (x) => Math.round(x * 1000) / 1000;
const round4 = (x) => Math.round(x * 10000) / 10000;

/**
 * Same shape as `reportText` in src/validate/index.js.
 * r3 C2.2 / Astra C10 — "clean" is now reserved for a run with NO advisory and
 * NO unverified row. A row nobody measured never reads as a row that passed.
 */
export function likenessText(violations, advisories = [], unverified = []) {
  const lines = [];
  if (violations.length === 0) {
    lines.push(advisories.length === 0 && unverified.length === 0
      ? "PASS: likeness clean (LK_VALUE, LK_HUE, LK_AREA, LK_OVERLAP, LK_VISIBLE)."
      : `PASS: 0 blocking likeness row(s), but ${advisories.length} advisory and ${unverified.length} UNVERIFIED — not clean.`);
  } else {
    const codes = [...new Set(violations.map((x) => x.v))].join(", ");
    lines.push(`FAIL: ${violations.length} likeness row(s) [${codes}].`);
    for (const item of violations.slice(0, 7)) {
      lines.push(`- ${item.v}${item.part ? ` ${item.part}` : ""}: ${item.hint} (measured ${item.measured}, limit ${item.limit})`);
    }
    if (violations.length > 7) lines[7] = `- … and ${violations.length - 6} more of the same class.`;
  }
  for (const item of advisories.slice(0, 4)) {
    lines.push(`- ADVISORY ${item.v}${item.part ? ` ${item.part}` : ""}: ${item.hint} (measured ${item.measured})`);
  }
  for (const item of unverified.slice(0, 4)) {
    lines.push(`- UNVERIFIED ${item.v}${item.part ? ` ${item.part}` : ""}: ${item.measured}`);
  }
  if (unverified.length > 4) lines.push(`- … and ${unverified.length - 4} more UNVERIFIED row(s).`);
  return lines.join("\n");
}

/** The table the repair prompt gets: one line per zone, numbers only. */
export function likenessTable(result) {
  const rows = [
    // r3 C2.2: the last column is the OLD whole-picture share. It is kept as
    // context only — the blocking area row is the front-quad family table below.
    "| zone | role | target | render | value ratio | d hue | whole-picture share r/t (informational) |",
    "|---|---|---|---|---|---|---|",
  ];
  for (const [name, z] of Object.entries(result.zones)) {
    rows.push(`| ${name} | ${z.role} | ${z.targetHex} V${z.targetV} | ${z.renderHex ?? "—"}${z.renderV === null ? "" : ` V${z.renderV}`} | `
      + `${z.valueRatio === null ? "—" : z.valueRatio.toFixed(2)} | ${z.hueDelta === null ? "—" : `${z.hueDelta.toFixed(0)}°`} | `
      + `${(z.renderAreaShare * 100).toFixed(1)}% / ${(z.targetAreaShare * 100).toFixed(1)}% |`);
  }
  const f = result.faces;
  const band = f.sideOverFrontBand ? `${f.sideOverFrontBand[0]}–${f.sideOverFrontBand[1]}` : "—";
  rows.push("", `front brick ${f.frontHex ?? "—"} vs palette: ${f.frontVsPalette ?? "—"}x (limit 0.90–1.05); `
    + `side ${f.sideHex ?? "—"} / front: ${f.sideOverFront ?? "—"}x (band ${band}, = target ${f.targetSideOverFront ?? "—"} ± 0.05)`);

  // r3 C2.2 — the family table, inside the FRONT QUAD of each picture.
  const fam = result.areaFamilies;
  rows.push("", "LK_AREA — share of the FRONT FACE quad, same classifier both sides:",
    "| family | target share | render share | ratio | verdict |", "|---|---|---|---|---|");
  if (!fam || !fam.target || !fam.render) {
    rows.push("| — | — | — | — | UNVERIFIED (no front-face quad) |");
  } else {
    for (const [family, r] of Object.entries(fam.rows)) {
      rows.push(`| ${family} | ${(r.tShare * 100).toFixed(1)}% | ${(r.rShare * 100).toFixed(1)}% | `
        + `${r.ratio === null ? "—" : `${r.ratio.toFixed(2)}x`} | ${r.verdict} |`);
    }
    rows.push("", `target quad: ${fam.target.provenance}`);
  }

  // r3 C2.2 — visibility per INSTANCE.
  rows.push("", "LK_VISIBLE — separate blobs of ≥ 50 id-pass px, against the frozen census:",
    "| role | instances seen | census | verdict |", "|---|---|---|---|");
  for (const [role, v] of Object.entries(result.visible ?? {})) {
    const seen = typeof v === "object" ? v.instances : "—";
    const want = typeof v === "object" ? (v.expected ?? "—") : "—";
    const verdict = want === "—" ? "UNVERIFIED" : (seen >= want ? "PASS" : "FAIL");
    rows.push(`| ${role} | ${seen} | ${want} | ${verdict} |`);
  }
  return rows.join("\n");
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

/** The census key(s) one census role is counted by, as an array (empty when uncounted). */
const censusKeysOf = (prior, role) => {
  const spec = prior?.censusInstances?.[role];
  return spec === undefined ? [] : (Array.isArray(spec) ? spec : [spec]);
};

/**
 * WF-BLIND-R1 B4 — the census roles whose census key(s) are due by pass `n` (census `_pass`), plus the
 * regions.json zones of those roles (a zone with 0 mask px reports LK_VISIBLE under its zone name).
 * @param {{prior:object, census:object|null, regions:object|null, n:number}} io  census = the RAW file, with `_pass`
 * @returns {Set<string>}
 */
export function dueVisibleParts({ prior, census, regions, n }) {
  const stage = census?._pass ?? {};
  const due = new Set();
  for (const role of prior?.censusRoles ?? []) {
    const keys = censusKeysOf(prior, role);
    if (keys.length === 0 || !keys.every((k) => Object.hasOwn(census ?? {}, k) && (stage[k] ?? 0) <= n)) continue;
    due.add(role);
    for (const [zone, z] of Object.entries(regions?.zones ?? {})) if (z.role === role) due.add(zone);
  }
  return due;
}

/**
 * WF-BLIND-R2 C5 — the pass that builds a role: the pass its census key(s) become due (census `_pass`), else the
 * first pass item that names it (`role X` / `X for the`), else the last pass.
 */
export function roleOwner(role, { prior, census, passes }) {
  const keys = censusKeysOf(prior, role).filter((k) => Object.hasOwn(census ?? {}, k));
  const stage = census?._pass ?? {};
  if (keys.length) return Math.max(...keys.map((k) => stage[k] ?? 0));
  const list = Array.isArray(passes) ? passes : [];
  const i = list.findIndex((p) => new RegExp(`\\brole ${role}\\b|\\b${role} for the\\b`).test(String(p.item ?? "")));
  return i >= 0 ? i : Math.max(0, list.length - 1);
}

/** WF-BLIND-R2 C5 — family -> the pass that owns it: the latest owner among the roles of its zones. */
export function familyOwners({ prior, regions, census, passes }) {
  const out = {};
  const last = Math.max(0, (Array.isArray(passes) ? passes.length : 1) - 1);
  for (const [family, zones] of Object.entries(prior?.areaFamilies ?? {})) {
    const roles = [...new Set(zones.map((z) => regions?.zones?.[z]?.role).filter(Boolean))];
    out[family] = roles.length ? Math.max(...roles.map((r) => roleOwner(r, { prior, census, passes }))) : last;
  }
  return out;
}

// run3 P0 fix: likeness is STAGED like the census. Before the final pass area share and overlap are
// judged on the finished assembly only. WF-BLIND-R1 B4: LK_VISIBLE is judged from the pass where the
// role's census key becomes due (a role already built is never excused until the end).
// WF-BLIND-R2 C5: with `owners` (familyOwners), an LK_AREA family is judged from the pass that builds it, its
// shares renormalised over the families built so far; at the final pass a family owned by an earlier pass is
// printed as an advisory attributed to that pass instead of blocking the last author.
const FINAL_ONLY = new Set(["LK_AREA", "LK_OVERLAP"]);
export function stageResult(result, final, dueParts = new Set(), { n = null, owners = null } = {}) {
  if (owners && Number.isFinite(n)) return stageByOwner(result, final, dueParts, n, owners);
  if (final) return result;
  const keep = (v) => !FINAL_ONLY.has(v.v) && (v.v !== "LK_VISIBLE" || dueParts.has(v.part));
  const violations = result.violations.filter(keep);
  const advisories = (result.advisories ?? []).filter(keep);
  const unverified = (result.unverified ?? []).filter(keep);
  const dueRoles = [...dueParts].filter((p) => Object.hasOwn(result.visible ?? {}, p));
  return { ...result, violations, advisories, unverified, pass: violations.length === 0,
    text: `${likenessText(violations, advisories, unverified)}\n(partial pass: LK_VISIBLE judged for the roles due by this pass`
      + `${dueRoles.length ? ` (${dueRoles.join(", ")})` : " (none yet)"}; LK_AREA / LK_OVERLAP are judged on the finished assembly)`,
    staged: "partial" };
}

function stageByOwner(result, final, dueParts, n, owners) {
  const L = LIKENESS_LIMITS;
  if (final) {
    const earlier = (v) => v.v === "LK_AREA" && Number.isFinite(owners[v.part]) && owners[v.part] < n;
    const moved = result.violations.filter(earlier);
    if (moved.length === 0) return result;
    const attributed = moved.map((v) => ({ ...v, blocking: false,
      hint: `${v.hint} — attributed to P${owners[v.part]}, the pass that builds this family (judged there; printed here, not this pass's row)` }));
    const violations = result.violations.filter((v) => !earlier(v));
    const advisories = [...(result.advisories ?? []), ...attributed];
    return { ...result, violations, advisories, pass: violations.length === 0, attributedArea: attributed.map((v) => `${v.part}:P${owners[v.part]}`),
      text: likenessText(violations, advisories, result.unverified ?? []) };
  }
  const keep = (v) => !FINAL_ONLY.has(v.v) && (v.v !== "LK_VISIBLE" || dueParts.has(v.part));
  const violations = result.violations.filter(keep);
  const advisories = (result.advisories ?? []).filter(keep);
  const unverified = (result.unverified ?? []).filter(keep);
  const owned = Object.keys(owners).filter((f) => owners[f] <= n);
  const fam = result.areaFamilies;
  const judged = [];
  if (owned.length >= 2 && fam?.target?.counts && fam?.render?.counts) {
    const shares = (counts) => {
      const total = owned.reduce((s, f) => s + (counts[f] ?? 0), 0);
      return Object.fromEntries(owned.map((f) => [f, total ? (counts[f] ?? 0) / total : 0]));
    };
    const t = shares(fam.target.counts);
    const r = shares(fam.render.counts);
    for (const f of owned) {
      const measured = `${(r[f] * 100).toFixed(1)}% vs ${(t[f] * 100).toFixed(1)}%`;
      if (!(t[f] > 0.002)) {
        unverified.push({ v: "LK_AREA", part: f, verdict: "UNVERIFIED", measured: `${measured} — target share under 0.2 %`, limit: `within +-${Math.round(L.areaShare * 100)}%`, hint: "", blocking: true });
        continue;
      }
      const ratio = r[f] / t[f];
      judged.push(f);
      if (Math.abs(ratio - 1) > L.areaShare) {
        violations.push(make("LK_AREA", f, `${measured} (${ratio.toFixed(2)}x) over the families built by P${n} (${owned.join(", ")})`,
          `within +-${Math.round(L.areaShare * 100)}% of the target share`,
          `family ${f} covers the wrong share of the FRONT FACE — built by P${owners[f]}`));
      }
    }
  }
  const dueRoles = [...dueParts].filter((p) => Object.hasOwn(result.visible ?? {}, p));
  return { ...result, violations, advisories, unverified, pass: violations.length === 0,
    text: `${likenessText(violations, advisories, unverified)}\n(partial pass: LK_VISIBLE judged for the roles due by this pass`
      + `${dueRoles.length ? ` (${dueRoles.join(", ")})` : " (none yet)"}; LK_AREA for the families built by this pass`
      + `${judged.length ? ` (${judged.join(", ")})` : " (fewer than two yet)"}; LK_OVERLAP on the finished assembly)`,
    staged: "partial" };
}

/**
 * WF-BLIND-R1 B4 — the acceptance the author is judged by, generated from the SAME config the likeness
 * rows read (LIKENESS_LIMITS, the class prior's likeness block, census, regions), shown BEFORE the attempt.
 * @param {{prior:object, census:object|null, regions:object|null, n:number, final:boolean}} io census = the RAW file
 * @returns {string}
 */
export function acceptanceBlock({ prior, census, regions, n, final, passes = null }) {
  const L = LIKENESS_LIMITS;
  const due = dueVisibleParts({ prior, census, regions, n });
  const lines = ["# ACCEPTANCE (scripts/likeness.mjs measures these on your render at Image 1's camera; a FAIL row is blocking)", ""];
  const roles = (prior?.censusRoles ?? []).filter((r) => due.has(r));
  if (roles.length) {
    lines.push(`LK_VISIBLE — every instance is its own blob of id-pass pixels at the solved camera, judged from this pass on:`, "",
      "| role | census count | visible instances required | px per instance |", "|---|---|---|---|");
    for (const role of roles) {
      const count = instanceCount(prior, role, census);
      const cap = prior.visibleInstances?.[role];
      const visible = Number.isFinite(cap) ? Math.min(count, cap) : count;
      const px = (prior.thinRoles ?? []).includes(role) ? `>= ${L.visiblePx} x ${visible} pooled (thin member)` : `>= ${L.visiblePx}`;
      lines.push(`| ${role} | ${count} | ${visible}${visible < count ? " (the target hides the rest)" : ""} | ${px} |`);
    }
    lines.push("");
    // WF-BLIND-R2 C11 — roles an EARLIER pass built stay required: blind Gemini's P1 details hid a P0 wheel.
    if (Array.isArray(passes)) {
      const built = roles.map((role) => ({ role, owner: roleOwner(role, { prior, census, passes }) })).filter((r) => r.owner < n);
      if (built.length) {
        lines.push(`Already built before P${n} — these instances must STAY visible at the solved camera; a part you add that hides one `
          + "fails LK_VISIBLE, and the row names the part that covers it:");
        for (const { role, owner } of built) {
          const count = instanceCount(prior, role, census);
          const cap = prior.visibleInstances?.[role];
          lines.push(`- ${Number.isFinite(cap) ? Math.min(count, cap) : count} ${role} instance(s) must stay visible (built in P${owner})`);
        }
        lines.push("");
      }
    }
  }
  const zones = Object.entries(regions?.zones ?? {});
  const faceFront = prior?.faceZones?.front ?? "brick_front";
  const faceSide = prior?.faceZones?.side ?? "brick_side_strip";
  lines.push(`- LK_VALUE: every zone renders at ${L.valueRatioMin}–${L.valueRatioMax} x the target's value (zones: ${zones.map(([z, v]) => `${z}/${v.role}`).join(", ")}); `
    + `the ${faceFront} face at ${L.frontVsPaletteMin}–${L.frontVsPaletteMax} x its palette hex "${prior?.facePaletteKey ?? "brick"}"; ${faceSide}/${faceFront} within +-${L.sideOverFrontTol} of the target's own ratio.`);
  lines.push(`- LK_HUE: every zone within ${L.hueDeg} deg of the target's hue.`);
  if (Array.isArray(passes)) {
    // WF-BLIND-R2 C5 — each family is judged from the pass that builds it.
    const owners = familyOwners({ prior, regions, census, passes });
    // WF-R3 R3-B item 6 — a family the target's quad cannot measure (prior.unmeasuredFamilies) is no acceptance promise.
    const families = Object.entries(prior?.areaFamilies ?? {}).filter(([f]) => !(prior?.unmeasuredFamilies ?? []).includes(f))
      .map(([f, zs]) => `${f} (${zs.join("+")}, built by P${owners[f]})`).join(", ");
    lines.push(`- LK_AREA: each family's share of the front-face quad within +-${Math.round(L.areaShare * 100)} % of the target's share, judged from the pass that builds it over the families built so far; `
      + `at the last pass a family built earlier is attributed to its own pass: ${families}.`);
  } else {
    const families = Object.entries(prior?.areaFamilies ?? {}).filter(([f]) => !(prior?.unmeasuredFamilies ?? []).includes(f))
      .map(([f, zs]) => `${f} (${zs.join("+")})`).join(", ");
    lines.push(`- LK_AREA${final ? "" : " (judged at the final pass only)"}: each family's share of the front-face quad within +-${Math.round(L.areaShare * 100)} % of the target's share: ${families}.`);
  }
  if ((prior?.overlapRoles ?? []).length) {
    lines.push(`- LK_OVERLAP${final ? "" : " (judged at the final pass only)"}: 0 px of ${prior.overlapRoles.join("/")} inside a window blob on screen.`);
  }
  if (prior?.silhouette) lines.push(`- LK_SILHOUETTE: the outline IoU with the target >= ${prior.silhouette.iouMin} in the ${prior.silhouette.part} region — ${prior.silhouette.what.replace(/^the /, "fails when the ")}.`);
  lines.push("");
  return lines.join("\n");
}

/** Runs the whole measurement for one pass directory. */

/** WF-R3 R3-B item 5 — the class rules' silhouette box in the RENDER's frame (its parts), projected to a screen hull. */
async function silhouetteFor(S, parts, manifest) {
  if (!S.cls.likeness?.silhouette) return null;
  if (!Array.isArray(parts) || parts.length === 0) return { hull: null, why: "no measured parts for this capture (the render's frame is unknown)" };
  const rules = await import(pathToFileURL(path.join(ROOT, S.cls.rules)).href);
  if (typeof rules.silhouetteBox !== "function") return { hull: null, why: `${S.cls.rules} exports no silhouetteBox` };
  const records = parts.filter((p) => p.aabb).map((p) => ({ id: p.id, role: p.role, aabb: p.aabb }));
  const box = rules.silhouetteBox(S.readJson("layout"), records, S.cls);
  if (!box) return { hull: null, why: "the silhouette keys are not measured, or the render has no body" };
  const hull = silhouetteHull(box, manifest);
  return hull ? { hull, box } : { hull: null, why: "the capture manifest cannot support a projection" };
}

export async function likenessForPass(label, outDir, { final = true, subject = null, previous = null, parts = null } = {}) {
  // WORKFLOW-V3 §7.5 — every path comes from subjects/<s>/subject.json.
  const S = loadSubject(subject ?? subjectIdFromArgv());
  const REGIONS_REL = S.rel.regions;
  const CENSUS_REL = S.rel.census;
  const MEASURED_REL = S.rel.layoutMeasured;
  const TARGET_REL = S.rel.target;
  const dir = outDir ?? path.join(ROOT, S.subject.outDir, label);
  const regions = JSON.parse(fs.readFileSync(path.join(ROOT, REGIONS_REL), "utf8"));
  const stillFile = path.join(dir, "target.png");
  const idpassFile = path.join(dir, "idpass.png");
  for (const file of [stillFile, idpassFile]) {
    if (!fs.existsSync(file)) {
      throw new Error(`missing ${path.relative(ROOT, file).replace(/\\/g, "/")} — capture the pass first `
        + "(scripts/capture2.mjs writes target.png, threeQuarter.png and idpass.png together)");
    }
  }
  const sidecar = `${stillFile}.json`;
  const manifest = fs.existsSync(sidecar) ? JSON.parse(fs.readFileSync(sidecar, "utf8")).manifest ?? {} : {};
  const idSidecar = `${idpassFile}.json`;
  const idManifest = fs.existsSync(idSidecar) ? JSON.parse(fs.readFileSync(idSidecar, "utf8")).manifest ?? {} : {};
  const idColours = idManifest.idColours;
  if (!idColours) {
    throw new Error(`${path.relative(ROOT, idSidecar).replace(/\\/g, "/")} carries no idColours — `
      + "that PNG is not an id pass (capture it with ?capture=1&idpass=1).");
  }

  const [target, still, idImage] = await Promise.all([
    readImage(path.join(ROOT, TARGET_REL)),
    readImage(stillFile),
    readImage(idpassFile),
  ]);
  if (still.w !== idImage.w || still.h !== idImage.h) {
    throw new Error(`still ${still.w}x${still.h} and id pass ${idImage.w}x${idImage.h} are different sizes`);
  }

  // r3 C2.2 — the two frames the LK_AREA rows are measured in, and the frozen
  // instance counts the LK_VISIBLE rows are measured against.
  const renderQuad = manifest.frontQuad ?? null;
  const measuredFile = path.join(ROOT, MEASURED_REL);
  const measured = fs.existsSync(measuredFile) ? JSON.parse(fs.readFileSync(measuredFile, "utf8")) : null;
  const targetQuad = resolveTargetQuad(measured, renderQuad, MEASURED_REL);
  const censusFile = path.join(ROOT, CENSUS_REL);
  const census = fs.existsSync(censusFile) ? JSON.parse(fs.readFileSync(censusFile, "utf8")) : null;

  // WF-BLIND-R2 C11 — the previous pass's id pass (same camera and size), to name what hides a lost instance.
  let occlusion = null;
  const previousIdpass = previous ? path.join(previous, "idpass.png") : null;
  if (previousIdpass && fs.existsSync(previousIdpass) && fs.existsSync(`${previousIdpass}.json`)) {
    const previousColours = JSON.parse(fs.readFileSync(`${previousIdpass}.json`, "utf8")).manifest?.idColours;
    if (previousColours) {
      occlusion = { previous: { image: await readImage(previousIdpass), idColours: previousColours }, label: path.basename(previous),
        parts, manifest: idManifest.frontQuad ? idManifest : manifest };
    }
  }
  const result = measureLikeness({
    regions,
    target,
    still,
    idpass: { image: idImage, idColours },
    palette: manifest.palette ?? null,
    targetQuad,
    renderQuad,
    census,
    prior: S.cls.likeness,
    censusRel: CENSUS_REL,
    occlusion,
    silhouette: await silhouetteFor(S, parts, idManifest.frontQuad ? idManifest : manifest),
  });
  result.pass_label = label;
  result.inputs = {
    target: TARGET_REL,
    still: path.relative(ROOT, stillFile).replace(/\\/g, "/"),
    idpass: path.relative(ROOT, idpassFile).replace(/\\/g, "/"),
    regions: REGIONS_REL,
    census: census ? CENSUS_REL : null,
    measuredLayout: measured ? MEASURED_REL : null,
    targetQuad: targetQuad.provenance,
    renderQuad: renderQuad ? "capture manifest frontQuad" : null,
  };
  return { result, dir };
}

async function main() {
  const args = process.argv.slice(2);
  const raw = args.find((a) => !a.startsWith("--"));
  if (!raw) throw new Error("usage: node scripts/likeness.mjs <P> [--out <dir>] [--json <file>]");
  const label = `P${String(raw).replace(/^P/i, "")}`;
  const outFlag = args.indexOf("--out");
  const readDir = outFlag !== -1 ? path.resolve(ROOT, args[outFlag + 1]) : undefined;
  // r3 C2 — exercise a frozen pass directory without writing into it.
  const jsonFlag = args.indexOf("--json");
  const jsonFile = jsonFlag !== -1 ? path.resolve(ROOT, args[jsonFlag + 1]) : null;

  const { result, dir } = await likenessForPass(label, readDir);
  const file = jsonFile ?? path.join(readDir ?? dir, "likeness.json");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(result, null, 2)}\n`);
  console.log(result.text);
  console.log("");
  console.log(likenessTable(result));
  console.log(`[likeness] ${path.relative(ROOT, file).replace(/\\/g, "/")}`);
  return result.pass ? 0 : 1;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    process.exitCode = await main();
  } catch (error) {
    console.error(`likeness: ${error.message}`);
    process.exitCode = 2;
  }
}
