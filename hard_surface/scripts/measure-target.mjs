#!/usr/bin/env node
// WF-LOOP-R3 Job C1 (row C1.1) — THE MEASURING INSTRUMENT. Round 2 seeded
// `subjects/<s>/layout.json` "from the audit" and the r2 M3 measure script was
// dropped, so six of eighteen frozen keys were off by more than their own
// tolerance and V12_LAYOUT spent run 3 forcing the author to match guesses
// (out/wf-loop/r3/fable-audit.md §2 C1/C6). The rule of round 3: **a layout key
// without evidence is invalid**. This file is where the evidence comes from.
//
//   node scripts/measure-target.mjs                 measure, write layout.measured.json
//   node scripts/measure-target.mjs --freeze        ... and REGENERATE layout.json from it
//   node scripts/measure-target.mjs --check         compare the frozen layout to the
//                                                   measurement; exit 1 on any key off by > tol
//
// Options: --subject <name> --target <png> --layout <json> --out <json> --json
//
// Inputs (all measured, none argued):
//   refs/tenement-iso.png                  the TARGET
//   subjects/<s>/subject.json paths.camera  the solved RENDER camera (phi/theta/mX/mZ; read in the face frame, faceCamera)
//   subjects/<s>/regions.json              FROZEN per-zone sampling patches -> medians
//
// METHOD — every fraction is CAMERA-RECTIFIED before it is written.
// The front face is a plane seen at phi 43.09 deg: its horizontals project to a
// straight line of slope `m` (fitted here at 0.4835 px/px off the coping/brick
// ink contour, 199 columns, max residual 0.5 px), verticals stay vertical, and
// the along-face scale is compressed by cos(phi) — which CANCELS in a fraction
// of W, so widths need no correction and heights do:
//   heightFraction(x, y) = (groundLine(x) - y) / H         groundLine(x) = G0 - m*(x - x0)
//   widthFraction(x)     = (x1 - x) / W                    measured from STREET-RIGHT (author -x)
// A bounding box is NOT a height: a feature w px wide has a box m*w px taller
// than the feature is. That is the whole of the disagreement between this file
// and the r3 audit's window.h / storefront.h / door.h (see the report).
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

/** Unratified instrument constants — every one of them is a threshold on the
 *  target's own pixels, not a number about the building. */
export const SCAN = Object.freeze({
  /** a pixel further than this from every zone median abstains (regions.areaTolerance) */
  faceRunGap: 40,          // px of non-brick a face scanline may bridge (windows, decals, ink)
  faceRunMin: 60,          // a scanline shorter than this is not the face
  edgeSearch: 6,           // px to walk outward from a brick run to find the ink contour
  inkLum: 60,              // Rec.709 luma below which a pixel is a CONTOUR line (lit brick sits at ~100)
  glassMinPx: 150,         // a smaller glass blob is a sliver, not a pane
  sashGap: 12,             // px of mullion between two sashes of ONE window
  bandFrac: 0.40,          // a rectified-height histogram bin under this share of the max is edge
  binH: 0.005,             // rectified-height histogram bin, in H
  assemblySearch: 30,      // px to walk off a pane looking for the surround's outer contour
  // v3-backlog scans
  paneColumnMin: 8,        // glass px a column under the awning needs to count as pane (rejects stray sliver px)
  paneRunGap: 3,           // empty columns a pane run may bridge; the storefront/door pier is ~20 px
  faceFill: 0.5,           // a proud box's FRONT-face column holds at least this share of the fullest column
  stripGap: 3,             // empty columns the street-left return strip may bridge (its ink outline)
  deckSearch: 0.10,        // H below an iron deck band's top searched for face-parallel ink lines
  deckSearchUp: 0.02,      // H above it: the front rail's top contour sits just over the band top
  balusterGap: 8,          // px between ink hits a deck line may bridge (baluster pitch ~10 px)
  deckLines: 6,            // longest deck lines that vote on a deck's run and return walk
  walkMax: 120,            // px limit of a return walk along mZ
  paneTallCols: 3,         // tallest pane columns whose median is the storefront height (the awning clips the rest)
  ladderGapPx: 12,         // px of no ink that ends the roof ladder's stile walk (rung pitch ~7 px, the stile is continuous)
  balusterSep: 7,          // V5-7: px within which two ink peaks are one baluster (its outline pair, 3-5 px apart; pitch ~12 px)
  rungSep: 8,              // V5-7: px within which two ink peaks are one rung (its outline pair, 4-5 px apart; pitch ~14 px)
});

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

const lum = (img, x, y) => {
  const p = at(img, x, y);
  return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
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

const dist2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;

const median = (xs) => {
  if (xs.length === 0) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s.length % 2 ? s[s.length >> 1] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2;
};

const mode = (xs) => {
  const m = new Map();
  for (const v of xs) m.set(v, (m.get(v) ?? 0) + 1);
  return [...m.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0])[0]?.[0] ?? null;
};

/** Least squares y = m*x + b, with `iters` rounds of >3 px outlier rejection. */
function fitLine(points, iters = 4) {
  let pts = points;
  let out = null;
  for (let it = 0; it <= iters; it += 1) {
    const n = pts.length;
    if (n < 8) break;
    let sx = 0; let sy = 0; let sxx = 0; let sxy = 0;
    for (const [x, y] of pts) { sx += x; sy += y; sxx += x * x; sxy += x * y; }
    const m = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    const b = (sy - m * sx) / n;
    let res = 0;
    for (const [x, y] of pts) res = Math.max(res, Math.abs(y - (m * x + b)));
    out = { m, b, n, maxResidual: res };
    if (it === iters) break;
    pts = pts.filter(([x, y]) => Math.abs(y - (m * x + b)) < 3);
  }
  return out;
}

/** Nearest zone median, `areaTolerance` cap; -1 = abstains. Same rule as likeness.mjs. */
function classify(img, regions) {
  const names = Object.keys(regions.zones);
  const medians = names.map((name) => {
    const samples = [];
    for (const [x, y, w, h] of regions.zones[name].rects) {
      for (let yy = y; yy < y + h; yy += 1) for (let xx = x; xx < x + w; xx += 1) samples.push(at(img, xx, yy));
    }
    return medianOf(samples);
  });
  const tol2 = (regions.areaTolerance ?? 32) ** 2;
  const label = new Int16Array(img.w * img.h).fill(-1);
  for (let y = 0; y < img.h; y += 1) {
    for (let x = 0; x < img.w; x += 1) {
      const p = at(img, x, y);
      let best = -1; let bestD = Infinity;
      for (let k = 0; k < medians.length; k += 1) {
        const d = dist2(p, medians[k]);
        if (d < bestD) { bestD = d; best = k; }
      }
      if (bestD <= tol2) label[y * img.w + x] = best;
    }
  }
  const index = Object.fromEntries(names.map((n, i) => [n, i]));
  return { label, names, medians, index };
}

/** 4-connected components of a label SET inside a window, as boxes. */
function components(cls, img, set, box, minPx) {
  const [x0, x1, y0, y1] = box;
  const seen = new Set();
  const out = [];
  for (let y = y0; y <= y1; y += 1) {
    for (let x = x0; x <= x1; x += 1) {
      const i = y * img.w + x;
      if (seen.has(i) || !set.has(cls.label[i])) continue;
      const stack = [i]; seen.add(i);
      let n = 0; let minx = 1e9; let maxx = -1; let miny = 1e9; let maxy = -1;
      const px = [];
      while (stack.length > 0) {
        const j = stack.pop();
        const jx = j % img.w; const jy = (j / img.w) | 0;
        n += 1; px.push([jx, jy]);
        if (jx < minx) minx = jx; if (jx > maxx) maxx = jx;
        if (jy < miny) miny = jy; if (jy > maxy) maxy = jy;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const nx = jx + dx; const ny = jy + dy;
          if (nx < x0 || nx > x1 || ny < y0 || ny > y1) continue;
          const k = ny * img.w + nx;
          if (seen.has(k) || !set.has(cls.label[k])) continue;
          seen.add(k); stack.push(k);
        }
      }
      if (n >= minPx) out.push({ n, minx, maxx, miny, maxy, px });
    }
  }
  return out.sort((a, b) => b.n - a.n);
}

// ---------------------------------------------------------------------------
// (a) THE FACE FRAME — the thing round 2 got wrong (261 px of front+side).
// ---------------------------------------------------------------------------

function faceFrame(img, cls, camera) {
  const BF = cls.index.brick_front;
  const starts = []; const ends = [];
  for (let y = 300; y <= 880; y += 1) {
    let best = null; let start = -1; let last = -1;
    for (let x = 0; x < img.w; x += 1) {
      const hit = cls.label[y * img.w + x] === BF;
      if (hit) { if (start < 0) start = x; last = x; }
      else if (start >= 0 && x - last > SCAN.faceRunGap) {
        if (!best || last - start > best[1] - best[0]) best = [start, last];
        start = -1;
      }
    }
    if (start >= 0 && (!best || last - start > best[1] - best[0])) best = [start, last];
    if (best && best[1] - best[0] >= SCAN.faceRunMin) { starts.push(best[0]); ends.push(best[1]); }
  }
  const brickL = mode(starts); const brickR = mode(ends);

  // The corner is the INK CONTOUR, not the first lit brick px: walk outward to
  // the darkest pixel within `edgeSearch` and take that column.
  const darkestOutward = (from, dir) => {
    let bestX = from; let bestL = Infinity;
    for (let k = 1; k <= SCAN.edgeSearch; k += 1) {
      const x = from + dir * k;
      const samples = [];
      for (let y = 480; y <= 660; y += 4) samples.push(lum(img, x, y));
      const l = median(samples);
      if (l < bestL) { bestL = l; bestX = x; }
    }
    return bestX;
  };
  const x0 = darkestOutward(brickL, -1);          // street-LEFT corner (author +x)
  const x1 = darkestOutward(brickR, +1);          // street-RIGHT corner (author -x)
  const W = x1 - x0;

  // Front-plane slope, off the coping/brick ink contour: the one horizontal on
  // the face that runs its whole width without a feature crossing it.
  const topPts = [];
  for (let x = brickL + 2; x <= brickR - 2; x += 1) {
    let run = 0;
    for (let y = 250; y < 600; y += 1) {
      if (cls.label[y * img.w + x] === BF) {
        run += 1;
        if (run < 5) continue;
        const base = y - 4;
        let bestY = base; let bestL = lum(img, x, base);
        for (let k = 1; k <= SCAN.edgeSearch; k += 1) {
          const l = lum(img, x, base - k);
          if (l < bestL) { bestL = l; bestY = base - k; }
        }
        if (bestL < SCAN.inkLum && bestY < 400) topPts.push([x, bestY]);
        break;
      }
      run = 0;
    }
  }
  const top = fitLine(topPts);
  const m = -top.m;                                 // px of rise per px to screen-right

  // Ground at the street-left corner columns: the ink between brick and the
  // white plate. Taken here and nowhere else — the bench and the shop stack own
  // the rest of the base line.
  const grounds = [];
  const copings = [];
  for (let x = brickL + 1; x <= brickL + 12; x += 1) {
    let lastBrick = -1;
    for (let y = 950; y > 400; y -= 1) if (cls.label[y * img.w + x] === BF) { lastBrick = y; break; }
    if (lastBrick > 0) {
      let bestY = lastBrick; let bestL = Infinity;
      for (let k = 1; k <= SCAN.edgeSearch; k += 1) {
        const l = lum(img, x, lastBrick + k);
        if (l < bestL) { bestL = l; bestY = lastBrick + k; }
      }
      if (bestL < SCAN.inkLum) grounds.push([x, bestY]);
    }
    // crown: the coping's FACE band, between the brick-top ink and the ink above it
    const brickTop = top.m * x + top.b;
    let above = null;
    for (let y = Math.round(brickTop) - 3; y > brickTop - 40; y -= 1) {
      if (lum(img, x, y) < SCAN.inkLum) { above = y; break; }
    }
    if (above !== null) copings.push(brickTop - above);
  }
  const groundFit = grounds.map(([x, y]) => y + m * x);      // G(x) = groundAtZero - m*x
  const G0 = median(groundFit);
  const H = (G0 - m * brickL) - (top.m * brickL + top.b);

  return {
    x0, x1, W, H,
    slope: m,
    topLine: (x) => top.m * x + top.b,
    groundLine: (x) => G0 - m * x,
    heightFrac(x, y) { return (this.groundLine(x) - y) / this.H; },
    widthFrac(x) { return (this.x1 - x) / this.W; },
    crownPx: median(copings),
    evidence: {
      brickRun: `${brickL}..${brickR}`,
      slopeFit: `${top.m.toFixed(5)} px/px over ${top.n} columns, max residual ${top.maxResidual.toFixed(2)} px`,
      camera: `phi ${camera.phi_deg} deg, theta ${camera.theta_deg} deg, mX ${camera.slopes.mX}, mZ ${camera.slopes.mZ}${camera.renderPhiDeg !== undefined ? ` (face frame of the render camera phi ${camera.renderPhiDeg} deg)` : ""}`,
    },
  };
}

// ---------------------------------------------------------------------------
// Rectified-height histogram: the instrument that turns a sloped band on the
// face into a horizontal band of the wall (Fable M1 steps c and d).
// ---------------------------------------------------------------------------

function heightBands(cls, img, set, F, xRange) {
  const [xa, xb] = xRange;
  const bins = new Map();
  for (let y = 150; y < img.h; y += 1) {
    for (let x = xa; x <= xb; x += 1) {
      if (!set.has(cls.label[y * img.w + x])) continue;
      const h = F.heightFrac(x, y);
      if (h < -0.02 || h > 1.05) continue;
      const b = Math.round(h / SCAN.binH);
      bins.set(b, (bins.get(b) ?? 0) + 1);
    }
  }
  const max = Math.max(0, ...bins.values());
  const cut = max * SCAN.bandFrac;
  const keep = [...bins.entries()].filter(([, n]) => n >= cut).map(([b]) => b).sort((a, b) => a - b);
  const bands = [];
  for (const b of keep) {
    const last = bands[bands.length - 1];
    if (last && b - last.hiBin <= 1) { last.hiBin = b; last.n += bins.get(b); continue; }
    bands.push({ loBin: b, hiBin: b, n: bins.get(b) });
  }
  return bands.map((band) => ({
    bottom: (band.loBin - 0.5) * SCAN.binH,
    top: (band.hiBin + 0.5) * SCAN.binH,
    px: band.n,
  }));
}

// ---------------------------------------------------------------------------
// Key records
// ---------------------------------------------------------------------------

const r3 = (v) => Math.round(v * 1000) / 1000;

/**
 * V5-7 — peaks of a 0..1 ink profile: [1 2 1] smoothed, local maxima >= floor, non-max suppressed within `sep` bins
 * (a member drawn as two outline lines is ONE peak). Sorted positions.
 */
export function inkPeaks(prof, sep, floor = 0.35) {
  const n = prof.length;
  const s = prof.map((v, i) => ((prof[i - 1] ?? 0) + 2 * v + (prof[i + 1] ?? 0)) / 4);
  const cand = [];
  for (let i = 0; i < n; i += 1) if (s[i] >= floor && s[i] >= (s[i - 1] ?? 0) && s[i] > (s[i + 1] ?? 0)) cand.push(i);
  cand.sort((a, b) => s[b] - s[a] || a - b);
  const kept = [];
  for (const i of cand) if (kept.every((j) => Math.abs(i - j) >= sep)) kept.push(i);
  return kept.sort((a, b) => a - b);
}
const gapsOf = (pk) => pk.slice(1).map((v, i) => v - pk[i]);

const key = (value, unit, scan, px) => ({ value: r3(value), unit, evidence: { scan, px } });
const keyList = (values, unit, scan, px) => ({ values: values.map(r3), unit, evidence: { scan, px } });
const unverified = (unit, reason) => ({ unverified: true, unit, reason });

// ---------------------------------------------------------------------------
// THE MEASUREMENT
// ---------------------------------------------------------------------------

/**
 * V5-8 R1 — the FACE frame of a solved RENDER camera. Every formula in this file reads the front as a plane whose
 * horizontals run along the face frame's X (slope mX, along-face scale cos phi) with its return along Z (slope mZ,
 * scale sin phi). The renderer turns meta.front onto its +X face, whose horizontals run along the render's Z: so the
 * face frame is the render camera with the axes swapped (phi -> 90 - phi, mX <-> mZ). The old refs camera (phi 43.09)
 * was solved in the FACE frame, which is why the render drew the front at 0.521 while this file measured it at
 * 0.456-0.484; subjects/facade_brick/camera.json (phi 46.91, --x-edge left) is the render camera and maps back onto
 * exactly the numbers this file always used.
 */
export function faceCamera(camera) {
  return {
    ...camera,
    phi_deg: Math.round((90 - camera.phi_deg) * 1e4) / 1e4,
    slopes: { mX: camera.slopes.mZ, mZ: camera.slopes.mX },
    renderPhiDeg: camera.phi_deg,
  };
}

export async function measureTarget({ targetFile, regionsFile, cameraFile }) {
  const img = await readImage(targetFile);
  const regions = JSON.parse(fs.readFileSync(regionsFile, "utf8"));
  const camera = faceCamera(JSON.parse(fs.readFileSync(cameraFile, "utf8")));
  const cls = classify(img, regions);
  const F = faceFrame(img, cls, camera);
  const out = {};
  const set = (...names) => new Set(names.map((n) => cls.index[n]));
  const inFace = [F.x0 + 2, F.x1 - 2, 150, img.h - 1];

  // ---- (b) glass-family components inside the face -> the upper windows ----
  const GLASS = set("glass", "door", "storefront");
  const blobs = components(cls, img, GLASS, inFace, SCAN.glassMinPx);
  // merge the two sashes of one window: same x range, mullion <= sashGap
  const merged = [];
  for (const b of blobs) {
    const host = merged.find((m) => Math.max(m.minx, b.minx) <= Math.min(m.maxx, b.maxx)
      && (b.miny - m.maxy <= SCAN.sashGap) && (m.miny - b.maxy <= SCAN.sashGap));
    if (host) {
      host.minx = Math.min(host.minx, b.minx); host.maxx = Math.max(host.maxx, b.maxx);
      host.miny = Math.min(host.miny, b.miny); host.maxy = Math.max(host.maxy, b.maxy);
      host.n += b.n; host.px.push(...b.px);
    } else merged.push({ ...b, px: [...b.px] });
  }

  // ---- (c) green family: the shop stack's two bands ----
  const greenBands = heightBands(cls, img, set("awning", "signbox"), F, [F.x0 + 2, F.x1 - 2]);
  const awn = greenBands[0] ?? null;                       // lower band
  const sign = greenBands[greenBands.length - 1] ?? null;  // upper band
  const shopTop = sign ? sign.top : 0.40;

  const windows = merged.filter((m) => F.heightFrac((m.minx + m.maxx) / 2, (m.miny + m.maxy) / 2) > shopTop + 0.05);
  const ground = merged.filter((m) => !windows.includes(m)).sort((a, b) => (b.maxx - b.minx) - (a.maxx - a.minx));

  /** True (rectified) extents: per-column height, per-row width, medians. */
  const extents = (blob, label) => {
    const cols = new Map(); const rows = new Map();
    for (const [x, y] of blob.px) {
      const c = cols.get(x) ?? [1e9, -1]; cols.set(x, [Math.min(c[0], y), Math.max(c[1], y)]);
      const r = rows.get(y) ?? [1e9, -1]; rows.set(y, [Math.min(r[0], x), Math.max(r[1], x)]);
    }
    const heights = [...cols.values()].map(([a, b]) => b - a + 1);
    const widths = [...rows.values()].map(([a, b]) => b - a + 1);
    const cx = (blob.minx + blob.maxx) / 2;
    return {
      label,
      cx,
      h: median(heights),
      w: median(widths),
      topY: median([...cols.values()].map(([a]) => a)),
      botY: median([...cols.values()].map(([, b]) => b)),
      centreH: F.heightFrac(cx, (blob.miny + blob.maxy) / 2),
      box: blob,
    };
  };

  const win = windows.map((b, i) => extents(b, `window_${i}`)).sort((a, b) => a.cx - b.cx);

  if (win.length > 0) {
    out["window.w"] = key(median(win.map((w) => w.w)) / F.W, "W",
      "glass-family components inside the face, per-row width, median over rows then over windows",
      `${median(win.map((w) => w.w))}/${F.W} px`);
    out["window.h"] = key(median(win.map((w) => w.h)) / F.H, "H",
      "same components, per-COLUMN height (a bounding box of a sloped feature is not a height)",
      `${median(win.map((w) => w.h))}/${Math.round(F.H)} px`);

    // bay centres, from the STREET-RIGHT edge of the face (author -x is right)
    const bays = [];
    for (const w of win) {
      const near = bays.find((b) => Math.abs(b.cx - w.cx) < 0.05 * F.W);
      if (near) near.xs.push(w.cx); else bays.push({ cx: w.cx, xs: [w.cx] });
    }
    const centres = bays.map((b) => F.widthFrac(median(b.xs))).sort((a, b) => a - b);
    out["window.centreX"] = keyList(centres, "W",
      "bay centres of the glass components, measured from the STREET-RIGHT face edge (x1 - cx)/W",
      `cx ${bays.map((b) => median(b.xs)).join(", ")} on face ${F.x0}..${F.x1}`);

    // The window ASSEMBLY is what V12 measures (the frame+glass group box), and
    // the target draws it as an ink-outlined surround. ABOVE the pane the head
    // trim is painted in the wall's own brick tone, so the assembly's outer top
    // is the FURTHEST contour inside the search band; BELOW the pane there is no
    // apron — the stone stool under it is zone `sill`, role `sill`, a different
    // part — so the assembly stops at the pane's own bottom contour.
    const surroundTop = (w) => {
      const x = Math.round(w.cx);
      const from = Math.round(w.topY);
      let edge = from;
      for (let k = 1; k <= SCAN.assemblySearch; k += 1) {
        const y = from - k;
        if (y < 1) break;
        if (lum(img, x, y) < SCAN.inkLum) edge = y;
      }
      return edge;
    };
    const paneBottom = (w) => {
      const x = Math.round(w.cx);
      const from = Math.round(w.botY);
      for (let k = 1; k <= SCAN.assemblySearch; k += 1) {
        const y = from + k;
        if (y >= img.h - 1) break;
        if (lum(img, x, y) < SCAN.inkLum) return y;
      }
      return from;
    };

    const rows = [];
    for (const w of win) {
      const near = rows.find((r) => Math.abs(r.h - w.centreH) < 0.05);
      if (near) { near.hs.push(w.centreH); near.wins.push(w); } else rows.push({ h: w.centreH, hs: [w.centreH], wins: [w] });
    }
    rows.sort((a, b) => a.h - b.h);
    // V12 measures the head off the TOPMOST window group, so the target must too.
    const topRow = rows[rows.length - 1];
    const heads = topRow.wins.map((w) => (surroundTop(w) - F.topLine(w.cx)) / F.H);
    out["window.headBelowCoping"] = key(median(heads), "H",
      "topmost window row: the surround's outer ink contour walked up off the pane, against the "
      + "coping/brick line at that column",
      `${heads.map((h) => Math.round(h * F.H)).join(", ")} px below the wall top`);
    if (rows.length >= 2) {
      const lo = median(rows[0].hs); const hi = median(rows[rows.length - 1].hs);
      out["window.rowPitch"] = key((hi - lo) / (rows.length - 1), "H",
        "rectified y-centres of the window rows",
        `${Math.round((hi - lo) * F.H)} px over ${rows.length - 1} gap(s)`);
    }
    out["frame.widthRatio"] = unverified("x glass width",
      "the target's surround reads as one ink-outlined band whose left/right members are the same "
      + "brick tone as the wall: a side width cannot be separated from the wall at 19 px of pane "
      + "(astra-audit C2). Measure it off a crop the owner ratifies, or drop the key.");
    out["frame.proud"] = unverified("m",
      "how far the frame stands in FRONT of the brick is a depth along z; one elevation of a flat-shaded "
      + "still carries no z for a 0.05 m feature. r2 read it off a lit inner face, which is a shading cue, "
      + "not a measurement.");

    // window BOTTOM (the sill line) — what landing.rowY is measured against
    out._windowBottoms = win.map((w) => F.heightFrac(w.cx, paneBottom(w)));
  }

  // ---- (c) awning / sign box ----
  if (awn) {
    out["awning.bottom"] = key(awn.bottom, "H", "green-family rectified height histogram, lower band",
      `${Math.round(awn.bottom * F.H)} px over the ground line`);
    out["awning.top"] = key(awn.top, "H", "green-family rectified height histogram, lower band",
      `${Math.round(awn.top * F.H)} px over the ground line`);
    const px = [];
    for (let y = 150; y < img.h; y += 1) {
      for (let x = F.x0 + 2; x <= F.x1 - 2; x += 1) {
        if (cls.label[y * img.w + x] !== cls.index.awning) continue;
        const h = F.heightFrac(x, y);
        if (h >= awn.bottom && h <= awn.top) px.push(x);
      }
    }
    if (px.length > 0) {
      out["awning.span"] = key((Math.max(...px) - Math.min(...px)) / F.W, "W",
        "x extent of the awning band inside the face",
        `${Math.min(...px)}..${Math.max(...px)} of ${F.x0}..${F.x1}`);
    }
  }
  if (sign && sign !== awn) {
    out["signbox.h"] = key(sign.top - sign.bottom, "H", "green-family rectified histogram, upper band",
      `${Math.round((sign.top - sign.bottom) * F.H)} px tall`);
    out["signbox.top"] = key(sign.top, "H", "green-family rectified histogram, upper band",
      `${Math.round(sign.top * F.H)} px over the ground line`);
  }

  // ---- v3-backlog: PROUD BOXES on the face — sign box and AC, x sizes + positions ----
  // Per-column px counts of the zone inside a rectified band. The FRONT face is
  // every column at least `faceFill` of the fullest column (an occluder — the AC
  // over the sign, the grille's ink over the AC — only drops interior columns).
  // The camera sees the street-LEFT return of anything proud of the wall, a strip
  // of the same zone left of the front face: its width `dx` is the box's
  // stand-off shift in screen x, so the box's plan centre is the front face's
  // centre minus dx. Widths need no correction (a shift moves both edges).
  const bandColumns = (labels, hLo, hHi) => {
    const counts = new Map();
    for (let x = F.x0 + 2; x <= F.x1 - 2; x += 1) {
      let n = 0; let topH = -Infinity; let botH = Infinity;
      for (let y = 150; y < img.h; y += 1) {
        if (!labels.has(cls.label[y * img.w + x])) continue;
        const h = F.heightFrac(x, y);
        if (h < hLo || h > hHi) continue;
        n += 1; topH = Math.max(topH, h); botH = Math.min(botH, h);
      }
      if (n > 0) counts.set(x, { n, topH, botH });
    }
    return counts;
  };
  const proudFace = (counts) => {
    const full = Math.max(...[...counts.values()].map((c) => c.n));
    const front = [...counts].filter(([, c]) => c.n >= SCAN.faceFill * full).map(([x]) => x);
    const left = Math.min(...front); const right = Math.max(...front);
    let stripLeft = left; let miss = 0;
    for (let x = left - 1; miss <= SCAN.stripGap; x -= 1) {
      if (counts.has(x)) { stripLeft = x; miss = 0; } else miss += 1;
    }
    return { left, right, dx: left - stripLeft, stripLeft, full };
  };
  let signDx = 0;
  if (sign && sign !== awn) {
    const s = proudFace(bandColumns(set("awning", "signbox"), sign.bottom, sign.top));
    signDx = s.dx;
    out["signbox.w"] = key((s.right - s.left + 1) / F.W, "W",
      "green-family columns inside the sign band, front face = columns >= faceFill of the fullest (the AC and the "
      + "ladder only hide interior columns)",
      `front face x ${s.left}..${s.right} of face ${F.x0}..${F.x1}`);
    out["signbox.centreX"] = key(F.widthFrac((s.left + s.right) / 2 - s.dx), "W",
      "front-face centre of the sign band, minus its street-left return strip (the box's stand-off shift), from the "
      + "STREET-RIGHT face edge",
      `centre ${(s.left + s.right) / 2} px - return ${s.stripLeft}..${s.left - 1} (${s.dx} px)`);
  }
  if (sign && Number.isFinite(out["awning.bottom"]?.value)) {
    const mZ = camera.slopes.mZ;
    const phi = camera.phi_deg * Math.PI / 180;
    const bandTop = sign.top + (sign.top - sign.bottom);
    const cols = bandColumns(set("ac"), out["awning.bottom"].value, bandTop);
    if (cols.size > 0) {
      const a = proudFace(cols);
      const faceCols = [...cols].filter(([x]) => x >= a.left && x <= a.right).map(([, c]) => c);
      // The lit TOP of the case is visible over its front face: at every front
      // column it adds (m + mZ) * dx px of the same zone above the front top edge.
      const lid = (F.slope + mZ) * a.dx / F.H;
      const topH = median(faceCols.map((c) => c.topH)) - lid;
      const botH = median(faceCols.map((c) => c.botH));
      out["ac.w"] = key((a.right - a.left + 1) / F.W, "W",
        "ac-zone columns between the awning bottom and one sign height over the sign band, front face = columns >= "
        + "faceFill of the fullest (the shaded return and the fan grille's ink fall under it)",
        `front face x ${a.left}..${a.right} of face ${F.x0}..${F.x1}`);
      out["ac.h"] = key(topH - botH, "H",
        "median per-column rectified top/bottom of the front-face columns, less the case lid (m + mZ) * dx",
        `${Math.round((topH - botH) * F.H)} px (lid ${(lid * F.H).toFixed(1)} px off ${Math.round((topH + lid - botH) * F.H)} px)`);
      out["ac.top"] = key(topH, "H",
        "same columns: the front face's top edge over the ground line (median column top less the lid)",
        `${Math.round(topH * F.H)} px over the ground line`);
      out["ac.centreX"] = key(F.widthFrac((a.left + a.right) / 2 - a.dx - signDx), "W",
        "front-face centre minus the case's own return strip and the sign box's (the case stands on the sign's front), "
        + "from the STREET-RIGHT face edge",
        `centre ${(a.left + a.right) / 2} px - return ${a.stripLeft}..${a.left - 1} (${a.dx} px) - sign return ${signDx} px`);
      out["ac.depth"] = key((a.dx / F.W) * (Math.cos(phi) / Math.sin(phi)), "x W",
        "the case's street-left return strip dx, D = dx/sin(phi) over W = Wpx/cos(phi) (the massing.depthOverW conversion)",
        `${a.dx} px return at phi ${camera.phi_deg} deg, face ${F.W} px`);
    }
  }

  // ---- the shop stack: storefront pane and door ----
  if (ground.length >= 1) {
    const s = extents(ground[0], "storefront");
    // WF-R3-B item 8 — the pane's EXTENT, not its median: the sloped awning hides the pane's head over most of
    // the span (those columns stop at the awning's underside, ~44 px), and only the street-left columns, where the
    // canopy's end rises off the pane, show the glass to its true head. A column is a lower bound on the pane
    // height, so the pane is at least as tall as its tallest columns: the median of the SCAN.paneTallCols tallest
    // columns (one stray px cannot set it). The r3 median (44 px, 0.08 H) put the template's whole pane under the
    // awning and failed the template's own LK_AREA glass (0.58x).
    const cols = new Map();
    for (const [x, y] of ground[0].px) {
      const c = cols.get(x) ?? [1e9, -1]; cols.set(x, [Math.min(c[0], y), Math.max(c[1], y)]);
    }
    const tall = [...cols.entries()].map(([x, [a, b]]) => ({ x, h: b - a + 1 })).sort((p, q) => q.h - p.h || p.x - q.x)
      .slice(0, SCAN.paneTallCols);
    const hExtent = median(tall.map((c) => c.h));
    out["storefront.h"] = key(hExtent / F.H, "H",
      `shop pane component, per-COLUMN height, median of the ${SCAN.paneTallCols} TALLEST columns (the awning hides the `
      + "pane head over the rest of the span, so a column is a lower bound; its box is m*w px taller than the pane is)",
      `${hExtent}/${Math.round(F.H)} px at x ${tall.map((c) => c.x).join(", ")} (${tall.map((c) => c.h).join(", ")} px); `
      + `median over all ${cols.size} columns ${s.h} px under the awning`);
    // WF-BLIND-R2 C5 — the pane's bottom edge over the ground line (the template read a class default here).
    const bottom = F.heightFrac(s.cx, s.botY + 1);
    out["storefront.bottom"] = key(bottom, "H",
      "shop pane component: median per-column bottom px + 1 (the first row under the pane) at its centre column, rectified over the ground line",
      `${Math.round(bottom * F.H)} px over the ground line at x ${Math.round(s.cx)}`);
  }
  // WF-R3-B item 8 — a PROUD edge reads LOW. A point d m in front of the face moves dx = d sin(phi) s px along the
  // screen (s = Wpx / (W cos phi) px/m) and, like the AC lid above, (m + mZ) dx px down the rectified frame. So a
  // band measured off a proud feature's lowest px (awning.bottom is the canopy LIP) sits under the feature's true
  // height by proudDrop x (d / W) H. The template lifts its canopy by this so the lip PROJECTS onto the band.
  // A property of the camera frame, not of the building: it lives in _frame (no V12 rule measures it).
  {
    const phi = camera.phi_deg * Math.PI / 180;
    const mZ = camera.slopes.mZ;
    F.proudDrop = r3((F.slope + mZ) * Math.tan(phi) * F.W / F.H);
    F.evidence.proudDrop = `H per (depth / W): (m + mZ) x tan(phi) x Wpx / Hpx = (${F.slope.toFixed(4)} + ${mZ}) x `
      + `tan(${camera.phi_deg} deg) x ${F.W}/${Math.round(F.H)} px — the AC-lid projection per unit depth over W`;
  }
  if (ground.length >= 2) {
    const d = extents(ground[1], "door");
    out["door.h"] = key(d.h / F.H, "H", "shop-door component, per-COLUMN height", `${d.h}/${Math.round(F.H)} px`);
  }
  // v3-backlog: the panes' x extents. Under the awning's bottom the glass family
  // is only the two shop panes (the awning hides their heads). Verticals stay
  // vertical under this camera, so a run of covered COLUMNS is a pane's true
  // width; the frame + brick between the panes is a run of empty columns. The
  // wider run is the storefront, the other the door — the same order as above.
  if (Number.isFinite(out["awning.bottom"]?.value)) {
    const covered = [];
    for (let x = F.x0 + 2; x <= F.x1 - 2; x += 1) {
      let n = 0;
      for (let y = 150; y < img.h; y += 1) {
        if (!GLASS.has(cls.label[y * img.w + x])) continue;
        const h = F.heightFrac(x, y);
        if (h >= 0 && h < out["awning.bottom"].value) n += 1;
      }
      if (n >= SCAN.paneColumnMin) covered.push(x);
    }
    const runs = [];
    for (const x of covered) {
      const last = runs[runs.length - 1];
      if (last && x - last[1] <= SCAN.paneRunGap) last[1] = x; else runs.push([x, x]);
    }
    runs.sort((a, b) => (b[1] - b[0]) - (a[1] - a[0]) || a[0] - b[0]);
    const pane = (name, [a, b]) => {
      out[`${name}.w`] = key((b - a + 1) / F.W, "W",
        `glass-family columns with >= paneColumnMin px under the awning bottom, the ${name === "door" ? "narrower" : "widest"} run`,
        `x ${a}..${b} (${b - a + 1}/${F.W} px)`);
      out[`${name}.centreX`] = key(F.widthFrac((a + b) / 2), "W",
        "centre of that run, from the STREET-RIGHT face edge (x1 - cx)/W",
        `cx ${(a + b) / 2} on face ${F.x0}..${F.x1}`);
    };
    if (runs.length >= 1) pane("storefront", runs[0]);
    if (runs.length >= 2) pane("door", runs[1]);
  }

  // ---- (d) iron row histogram -> deck lines -> landing.rowY ----
  const IRON = set("iron_landing_upper", "iron_landing_lower");
  const ironBands = heightBands(cls, img, IRON, F, [F.x0 + 2, F.x1 - 2]);
  const decks = ironBands.filter((b) => b.top - b.bottom >= 0.03);
  if (decks.length > 0 && Array.isArray(out._windowBottoms) && out._windowBottoms.length > 0) {
    const rowY = decks.map((d) => {
      const near = out._windowBottoms.reduce((a, b) => (Math.abs(b - d.top) < Math.abs(a - d.top) ? b : a));
      return d.top - near;
    });
    out["landing.rowY"] = key(median(rowY), "H",
      "iron-family rectified histogram: deck band TOPS against the nearest window-surround bottom",
      `decks at ${decks.map((d) => d.top.toFixed(3)).join(", ")} H; sills at ${out._windowBottoms.map((b) => b.toFixed(3)).join(", ")} H`);
  }

  // ---- v3-backlog: landing plan position — span and centre, per deck ----
  // Inside each deck band the balusters cross every face-parallel line, so the
  // longest ink run along a rectified line (bridging <= balusterGap px) runs from
  // the street-LEFT return's back end ON THE WALL to the FRONT-right corner: it
  // is span + dx, where dx is the deck's stand-off shift in screen x. dx is
  // walked off the street-RIGHT return: from the run's right end back along the
  // solved mZ while ink stays within 2 px (the coping walk's method). So
  //   span = run - dx,   plan centre = (left + right - dx) / 2.
  // The `deckLines` longest lines vote (medians), so one line that picks up a
  // brick contour does not decide.
  if (decks.length > 0) {
    const mZ = camera.slopes.mZ;
    const ink = (x, y) => y >= 0 && y < img.h && lum(img, x, y) < SCAN.inkLum;
    const walkBack = (x0, y0) => {
      let lastHit = 0; let miss = 0;
      for (let step = 1; step <= SCAN.walkMax; step += 1) {
        const x = x0 - step; const y = Math.round(y0 - mZ * step);
        let hit = false;
        for (let k = -2; k <= 2 && !hit; k += 1) hit = ink(x, y + k);
        if (hit) { lastHit = step; miss = 0; } else if (++miss > 3) break;
      }
      return lastHit;
    };
    const perDeck = decks.map((d) => {
      const lines = [];
      for (let hp = Math.round((d.top - SCAN.deckSearch) * F.H); hp <= Math.round((d.top + SCAN.deckSearchUp) * F.H); hp += 1) {
        let run = null; let start = null; let last = null;
        for (let x = F.x0 + 2; x <= F.x1 - 2; x += 1) {
          const y = Math.round(F.groundLine(x) - hp);
          if (!(ink(x, y - 1) || ink(x, y) || ink(x, y + 1))) continue;
          if (start === null || x - last > SCAN.balusterGap) {
            if (start !== null && (!run || last - start > run[1] - run[0])) run = [start, last];
            start = x;
          }
          last = x;
        }
        if (start !== null && (!run || last - start > run[1] - run[0])) run = [start, last];
        if (run) lines.push({ hp, run });
      }
      lines.sort((a, b) => (b.run[1] - b.run[0]) - (a.run[1] - a.run[0]) || a.hp - b.hp);
      const vote = lines.slice(0, SCAN.deckLines);
      const left = median(vote.map((l) => l.run[0]));
      const right = median(vote.map((l) => l.run[1]));
      const dx = median(vote.map((l) => walkBack(l.run[1], F.groundLine(l.run[1]) - l.hp)));
      return { left, right, dx, span: right - left - dx, centre: (left + right - dx) / 2 };
    });
    // V5-7 — BALUSTER PITCH on each deck's FRONT run (screen x left + dx .. right): every rectified line from 10 px
    // under the deck band top to 60 px over it gives an ink profile along x; its peaks (one per baluster, outline pair
    // merged within SCAN.balusterSep) are counted; the lines with the most peaks (>= max - 1) cross the balusters, and
    // the pitch is the median gap over them. W fraction = pitch px / face W px (the front run is face-parallel).
    const balusters = decks.map((d, i) => {
      const p = perDeck[i];
      const xs0 = Math.round(p.left + p.dx) + 2;
      const xs1 = Math.round(p.right) - 2;
      if (!(xs1 - xs0 > 3 * SCAN.balusterSep)) return null;
      const rows = [];
      for (let hp = Math.round(d.top * F.H) - 10; hp <= Math.round(d.top * F.H) + 60; hp += 1) {
        const prof = [];
        for (let x = xs0; x <= xs1; x += 1) prof.push(ink(x, Math.round(F.groundLine(x) - hp)) ? 1 : 0);
        rows.push({ hp, pk: inkPeaks(prof, SCAN.balusterSep) });
      }
      const most = Math.max(...rows.map((r) => r.pk.length));
      const best = rows.filter((r) => r.pk.length >= most - 1 && r.pk.length >= 3);
      const pitch = median(best.map((r) => median(gapsOf(r.pk))));
      return Number.isFinite(pitch) ? { pitch, count: most, lines: best.length, run: [xs0, xs1] } : null;
    });
    if (balusters.every(Boolean)) {
      out["landing.balusterPitch"] = key(median(balusters.map((b) => b.pitch)) / F.W, "W",
        "front-run baluster ink profile: rectified lines -10..+60 px about each deck band top, peaks per line (outline "
        + `pair merged within ${SCAN.balusterSep} px), median gap over the lines with the most peaks; median over the decks`,
        balusters.map((b) => `run x ${b.run.join("..")}: ${b.count} balusters, pitch ${b.pitch} px (${b.lines} lines)`).join("; "));
    }
    if (perDeck.every((p) => p.dx > 0 && p.span > 0)) {
      const px = perDeck.map((p) => `deck run ${p.left}..${p.right}, return dx ${p.dx}`).join("; ");
      out["landing.span"] = key(median(perDeck.map((p) => p.span)) / F.W, "W",
        "deck band: longest baluster-bridged ink run along a rectified line (street-left return's wall end to the "
        + "front-right corner), less the street-right return walked back along mZ; median over the decks",
        px);
      out["landing.centreX"] = key(F.widthFrac(median(perDeck.map((p) => p.centre))), "W",
        "same runs: plan centre (left + right - dx)/2, from the STREET-RIGHT face edge; median over the decks",
        `${px}; centres ${perDeck.map((p) => p.centre).join(", ")} px`);
    } else {
      out["landing.span"] = unverified("W", "no deck gave a return walk off its run's right end, so the run's stand-off "
        + "shift cannot be removed from it");
      out["landing.centreX"] = unverified("W", "as landing.span: without the return walk the run's centre carries the "
        + "deck's unknown stand-off shift");
    }
  }
  out["landing.depth"] = unverified("W",
    "a deck's depth projects as d*sin(phi)*mZ of vertical band, inseparable at this resolution from the "
    + "deck fascia and the railing feet inside the same band (fable-audit L6: the decks are open grilles). "
    + "r2's 0.15 W was already flagged UNVERIFIED and stays out of the gate.");

  // ---- crown ----
  if (Number.isFinite(F.crownPx)) {
    out["crown.height"] = key(F.crownPx / F.H, "H",
      "coping FACE band at the street-left corner, between the brick-top ink and the ink above it "
      + "(the lit top above it is the coping's PLAN depth, not a height)",
      `${Math.round(F.crownPx)}/${Math.round(F.H)} px`);
  }
  out["cornice.projection"] = unverified("W",
    "the target's crown reads as ONE coping band; no cornice course projects far enough to separate "
    + "from it in the still. r2's 0.02 W was already marked UNVERIFIED.");

  // ---- (e) coping walk from the front-left top corner along mZ -> D/W ----
  {
    const ROOFY = set("roof", "coping", "sill");
    const mZ = camera.slopes.mZ;
    const phi = camera.phi_deg * Math.PI / 180;
    const start = [F.x0, F.topLine(F.x0) - F.crownPx];       // the front-left COPING TOP corner
    let lastHit = 0; let miss = 0;
    for (let step = 1; step <= 400; step += 1) {
      const x = Math.round(start[0] - step);
      const y = Math.round(start[1] - mZ * step);
      if (x < 1 || y < 1) break;
      let hit = false;
      for (let k = -5; k <= 5 && !hit; k += 1) {
        if (y + k < 0 || y + k >= img.h) continue;
        if (ROOFY.has(cls.label[(y + k) * img.w + x])) hit = true;
      }
      if (hit) { lastHit = step; miss = 0; } else if (++miss > 8) break;
    }
    const depthOverW = (lastHit / F.W) * (Math.cos(phi) / Math.sin(phi));
    out["massing.depthOverW"] = key(depthOverW, "x W",
      "coping walk from the front-left coping-top corner along the solved mZ to the last coping px, "
      + "then D = dx/sin(phi) over W = Wpx/cos(phi)",
      `${lastHit} px along z at phi ${camera.phi_deg} deg, face ${F.W} px`);
  }

  // ---- v3-backlog: face.aspect — W / H through the solved orthographic camera ----
  // A face-parallel horizontal spans W cos(phi) of screen x (the same cos(phi)
  // the depth walk divides by); a vertical spans H cos(theta) of screen y
  // (theta = elevation, scripts/solve-camera.mjs). The scale cancels in the ratio.
  {
    const phi = camera.phi_deg * Math.PI / 180;
    const theta = camera.theta_deg * Math.PI / 180;
    out["face.aspect"] = key((F.W / Math.cos(phi)) / (F.H / Math.cos(theta)), "W/H",
      "rectified face frame: face width px / cos(phi) over wall height px / cos(theta)",
      `${F.W} px / cos ${camera.phi_deg} deg over ${Math.round(F.H)} px / cos ${camera.theta_deg} deg`);
  }

  // ---- (g) the roof ladder on the SIDE return ----
  // The target draws it too small to carry an interior colour: two stiles and a
  // run of rungs, all CONTOUR. So it is found as the widest run of columns in
  // the side strip whose ink fraction is "hatched" — neither a clean wall (a few
  // per cent) nor a solid line (~100 %) — inside the side face's own y band.
  {
    const phi = camera.phi_deg * Math.PI / 180;
    const mZ = camera.slopes.mZ;
    const copingAtSide = (x) => F.topLine(F.x0) - F.crownPx - (F.x0 - x) * mZ;
    const frac = [];
    for (let x = Math.max(1, F.x0 - 70); x < F.x0; x += 1) {
      const yTop = Math.round(copingAtSide(x) + 0.05 * F.H);
      const yBot = Math.round(copingAtSide(x) + 0.70 * F.H);
      let ink = 0; let n = 0;
      for (let y = yTop; y <= yBot; y += 1) { n += 1; if (lum(img, x, y) < SCAN.inkLum) ink += 1; }
      frac.push([x, n > 0 ? ink / n : 0]);
    }
    let run = null; let best = null;
    for (const [x, f] of frac) {
      if (f >= 0.15 && f <= 0.95) { run = run ?? { a: x, b: x }; run.b = x; }
      else { if (run && (!best || run.b - run.a > best.b - best.a)) best = run; run = null; }
    }
    if (run && (!best || run.b - run.a > best.b - best.a)) best = run;
    if (best && best.b - best.a >= 5) {
      const cx = (best.a + best.b) / 2;
      const back = ((F.x0 - cx) / F.W) * (Math.cos(phi) / Math.sin(phi));
      out["ladder.roof.face"] = {
        value: "side",
        unit: "face",
        evidence: {
          scan: "hatched column run in the strip街".replace("街", "") + " left of the street-left corner — the "
            + "target's roof ladder climbs the SIDE return, never the front plane (fable-audit L5)",
          px: `columns ${best.a}..${best.b} behind the corner at x ${F.x0}`,
        },
      };
      out["ladder.roof.backFromCorner"] = key(back, "W",
        "x centre of that column run behind the street-left corner, converted through the solved phi",
        `${(F.x0 - cx).toFixed(1)} px behind x ${F.x0}`);
      // The scan starts UNDER the side coping's own face band — everything above
      // it is the receding coping edge, which is contour too.
      let topY = null;
      for (let y = Math.round(copingAtSide(cx) + F.crownPx) + 3; y < img.h && topY === null; y += 1) {
        for (let x = best.a; x <= best.b; x += 1) if (lum(img, x, y) < SCAN.inkLum) { topY = y; break; }
      }
      if (topY !== null) {
        out["ladder.topBelowCoping"] = key((topY - copingAtSide(cx)) / F.H, "H",
          "topmost contour px of that run, below the side coping band, against the side return's "
          + "coping line (which rises back along mZ from the front-left coping corner)",
          `${Math.round(topY - copingAtSide(cx))} px below the coping top`);
        // WF-R3 C15 — the roof ladder's FOOT: walk down the same column run from its top while the stile contour
        // continues (a gap longer than SCAN.ladderGapPx ends it); the side return's ground line falls back along mZ
        // exactly like its coping line, so the height over the ground is (groundAtSide - foot) / H.
        let bottomY = topY;
        let miss = 0;
        for (let y = topY + 1; y < img.h && miss <= SCAN.ladderGapPx; y += 1) {
          let hit = false;
          for (let x = best.a; x <= best.b && !hit; x += 1) if (lum(img, x, y) < SCAN.inkLum) hit = true;
          if (hit) { bottomY = y; miss = 0; } else miss += 1;
        }
        const groundAtSide = F.groundLine(F.x0) - (F.x0 - cx) * mZ;
        out["ladder.roof.bottom"] = key((groundAtSide - bottomY) / F.H, "H",
          "lowest contour px of that column run, walking down from its top while the stile line continues "
          + `(gap <= ${SCAN.ladderGapPx} px), over the side return's ground line (front ground line at the corner, rising back along mZ)`,
          `foot at y ${bottomY}, side ground at y ${groundAtSide.toFixed(1)}, ${Math.round(groundAtSide - bottomY)} px over it`);
        // V5-7 — RUNG PITCH: between the stiles (the run's inner columns), a rung is a side-face horizontal, so the
        // rows are rectified along the side slope (y - (x - cx) mZ); the ink share per rectified row is a profile
        // whose peaks (outline pair merged within SCAN.rungSep) are the rungs; pitch = median gap, H fraction.
        const xa = best.b - best.a >= 8 ? best.a + 3 : Math.floor(cx);
        const xb = best.b - best.a >= 8 ? best.b - 3 : Math.ceil(cx);
        const prof = [];
        for (let yr = topY; yr <= bottomY; yr += 1) {
          let hit = 0;
          for (let x = xa; x <= xb; x += 1) if (lum(img, x, Math.round(yr + (x - cx) * mZ)) < SCAN.inkLum) hit += 1;
          prof.push(hit / (xb - xa + 1));
        }
        const rungs = inkPeaks(prof, SCAN.rungSep);
        if (rungs.length >= 3) {
          out["ladder.roof.rungPitch"] = key(median(gapsOf(rungs)) / F.H, "H",
            "rung ink profile between the stiles (columns inside the run), rows rectified along the side slope mZ, "
            + `from the ladder top to its foot; peaks (outline pair merged within ${SCAN.rungSep} px) = rungs; median gap`,
            `${rungs.length} rungs over y ${topY}..${bottomY}, columns ${xa}..${xb}, pitch ${median(gapsOf(rungs))} px`);
        }
      }
    }
  }

  // ---- (f) iron share of the front quad, (h) side/front value ----
  {
    let iron = 0; let total = 0;
    let ironB = 0; let totalB = 0;
    for (const [bx, by, bw, bh] of regions.building ?? []) {
      for (let y = by; y < by + bh; y += 1) for (let x = bx; x < bx + bw; x += 1) {
        if (cls.label[y * img.w + x] < 0) continue;
        totalB += 1;
        if (IRON.has(cls.label[y * img.w + x])) ironB += 1;
      }
    }
    const ironBuilding = totalB > 0 ? ironB / totalB : 0;
    for (let x = F.x0 + 1; x < F.x1; x += 1) {
      const yTop = Math.ceil(F.topLine(x));
      const yBot = Math.floor(F.groundLine(x));
      for (let y = yTop; y <= yBot; y += 1) {
        total += 1;
        if (IRON.has(cls.label[y * img.w + x])) iron += 1;
      }
    }
    out["iron.frontShare"] = {
      ...key(iron / total, "share of front-quad px",
        "iron-family px inside the front quad (the parallelogram x0..x1 between the coping and ground lines)",
        `${iron}/${total} px inside the quad; the same classifier gives ${(100 * ironBuilding).toFixed(1)} % `
        + "over regions.building (front + side + roof), which is the 6.2 % the r3 audit quotes"),
      measuredBy: "likeness",
    };
  }
  {
    const front = cls.medians[cls.index.brick_front];
    const side = cls.medians[cls.index.brick_side_strip];
    const v = (rgb) => Math.max(...rgb) / 255;
    out.sideOverFront = {
      ...key(v(side) / v(front), "ratio",
        "HSV value of the side-return brick median over the front brick median, from regions.json rects",
        `#${side.map((c) => c.toString(16).padStart(2, "0")).join("")} over #${front.map((c) => c.toString(16).padStart(2, "0")).join("")}`),
      measuredBy: "likeness",
    };
  }

  delete out._windowBottoms;
  return { keys: out, frame: F, cls, img, camera };
}

// ---------------------------------------------------------------------------
// WF-V4 V4-6 item 5 — THE SUBJECT MASK. refs/tenement-iso.png holds three buildings; the registered IoU of the brick
// one against the whole-image foreground is capped ~0.40 by its neighbours. Ruling: measurements are harness work,
// with evidence. Method (target px only, no hand-placed vertex):
//   1. BODY = the brick-wall + coping labels (the classifier above over regions.json: colours no neighbour carries),
//      closed with radius MASK.close (bridges ink lines and the window / sign / pane openings), largest component,
//      holes filled (the roof deck inside the coping ring, windows, storefront).
//   2. ATTACHMENTS = components of the awning / sign / AC / iron / frame labels that touch BODY dilated by
//      MASK.touch px (the fire escape, the awning's overhang past the right edge, the AC case); tan / green
//      neighbour pixels never touch it (their colours are not these labels within areaTolerance, or sit > touch px off).
//   3. BODY u ATTACHMENTS, closed again, holes filled, dilated by MASK.ink (the building's own outer ink contour),
//      then read as ONE span per row (left edge top->bottom, right edge bottom->top) and Douglas-Peucker simplified
//      to MASK.simplify px: a simple polygon, target px.
// ---------------------------------------------------------------------------

export const MASK = Object.freeze({ close: 10, touch: 3, closeAll: 4, ink: 3, simplify: 1.5, attachMinPx: 30, bodyMinPx: 400,
  corner: 8, overhang: 30, attachLeft: 10 });

function morph(mask, w, h, r, isMin) {
  const tmp = new Uint8Array(w * h);
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let v = isMin ? 1 : 0;
      for (let d = -r; d <= r && v === (isMin ? 1 : 0); d += 1) {
        const xx = x + d;
        const s = xx < 0 || xx >= w ? (isMin ? 1 : 0) : mask[y * w + xx];
        if (isMin ? !s : s) v = isMin ? 0 : 1;
      }
      tmp[y * w + x] = v;
    }
  }
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let v = isMin ? 1 : 0;
      for (let d = -r; d <= r && v === (isMin ? 1 : 0); d += 1) {
        const yy = y + d;
        const s = yy < 0 || yy >= h ? (isMin ? 1 : 0) : tmp[yy * w + x];
        if (isMin ? !s : s) v = isMin ? 0 : 1;
      }
      out[y * w + x] = v;
    }
  }
  return out;
}
const dilate = (m, w, h, r) => morph(m, w, h, r, false);
const erode = (m, w, h, r) => morph(m, w, h, r, true);

/** 4-connected components of a binary mask: {n, px:Int32Array-ish list, box}. */
function maskComponents(mask, w, h) {
  const seen = new Uint8Array(w * h);
  const out = [];
  for (let s = 0; s < w * h; s += 1) {
    if (!mask[s] || seen[s]) continue;
    const px = [s];
    seen[s] = 1;
    for (let k = 0; k < px.length; k += 1) {
      const i = px[k];
      const x = i % w;
      for (const j of [x > 0 ? i - 1 : -1, x < w - 1 ? i + 1 : -1, i - w, i + w]) {
        if (j >= 0 && j < w * h && mask[j] && !seen[j]) { seen[j] = 1; px.push(j); }
      }
    }
    let x0 = w; let x1 = -1; let y0 = h; let y1 = -1;
    for (const i of px) { const x = i % w; const y = (i / w) | 0; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    out.push({ n: px.length, px, box: [x0, y0, x1, y1] });
  }
  return out.sort((a, b) => b.n - a.n);
}

/** Holes (0-px not reachable from the image border through 0-px) set to 1. */
function fillHoles(mask, w, h) {
  const out = Uint8Array.from(mask);
  const seen = new Uint8Array(w * h);
  const stack = [];
  for (let x = 0; x < w; x += 1) for (const y of [0, h - 1]) { const i = y * w + x; if (!mask[i] && !seen[i]) { seen[i] = 1; stack.push(i); } }
  for (let y = 0; y < h; y += 1) for (const x of [0, w - 1]) { const i = y * w + x; if (!mask[i] && !seen[i]) { seen[i] = 1; stack.push(i); } }
  while (stack.length) {
    const i = stack.pop();
    const x = i % w;
    for (const j of [x > 0 ? i - 1 : -1, x < w - 1 ? i + 1 : -1, i - w, i + w]) {
      if (j >= 0 && j < w * h && !mask[j] && !seen[j]) { seen[j] = 1; stack.push(j); }
    }
  }
  for (let i = 0; i < w * h; i += 1) if (!mask[i] && !seen[i]) out[i] = 1;
  return out;
}

function douglasPeucker(pts, tol) {
  if (pts.length < 3) return pts;
  const keep = new Uint8Array(pts.length);
  keep[0] = 1; keep[pts.length - 1] = 1;
  const stack = [[0, pts.length - 1]];
  while (stack.length) {
    const [a, b] = stack.pop();
    const [ax, ay] = pts[a]; const [bx, by] = pts[b];
    const len = Math.hypot(bx - ax, by - ay) || 1;
    let far = -1; let farD = tol;
    for (let i = a + 1; i < b; i += 1) {
      const d = Math.abs((bx - ax) * (ay - pts[i][1]) - (ax - pts[i][0]) * (by - ay)) / len;
      if (d > farD) { farD = d; far = i; }
    }
    if (far >= 0) { keep[far] = 1; stack.push([a, far], [far, b]); }
  }
  return pts.filter((_, i) => keep[i]);
}

/** Even-odd scanline rasterisation of a polygon (target px) at w x h (scaled from the image size iw x ih). */
export function rasterPolygon(poly, w, h, iw = w, ih = h) {
  const m = new Uint8Array(w * h);
  const sx = w / iw; const sy = h / ih;
  const P = poly.map(([x, y]) => [x * sx, y * sy]);
  for (let y = 0; y < h; y += 1) {
    const yc = y + 0.5;
    const xs = [];
    for (let i = 0; i < P.length; i += 1) {
      const [x1, y1] = P[i]; const [x2, y2] = P[(i + 1) % P.length];
      if ((y1 <= yc && y2 > yc) || (y2 <= yc && y1 > yc)) xs.push(x1 + (yc - y1) * (x2 - x1) / (y2 - y1));
    }
    xs.sort((a, b) => a - b);
    for (let k = 0; k + 1 < xs.length; k += 2) {
      const a = Math.max(0, Math.ceil(xs[k] - 0.5)); const b = Math.min(w - 1, Math.floor(xs[k + 1] - 0.5));
      for (let x = a; x <= b; x += 1) m[y * w + x] = 1;
    }
  }
  return m;
}

/**
 * @returns {{polygon:number[][], mask:Uint8Array, evidence:object}} polygon in target px (image frame).
 */
export function subjectMask(img, cls, F, camera, crownPx = 0) {
  const { w, h } = img;
  // THE WINDOW (the face frame measured above, not a hand box): nothing right of the street-right corner x1 (+ the
  // coping corner), nothing under the ground line (front: F.groundLine; side return: it rises at the camera's mZ
  // from the street-left corner x0) — the tan neighbour and the pavement bench are outside it by construction.
  const mZ = camera?.slopes?.mZ ?? 0;
  const ground = (x) => (x >= F.x0 ? F.groundLine(x) : F.groundLine(F.x0) - mZ * (F.x0 - x));
  // ... and nothing above the roof's back-right edge: from the crown top at the street-right corner it rises at mZ
  // toward the back (the tan neighbour's parapet sits just over it and reads as coping)
  const backRight = (x) => F.topLine(F.x1) - crownPx - 2 * MASK.ink - mZ * (F.x1 - x);
  const inWindow = (x, y, right) => x <= F.x1 + right && y <= ground(x) + MASK.ink && y >= backRight(x);
  const lab = (names) => new Set(names.filter((n) => cls.index[n] !== undefined).map((n) => cls.index[n]));
  const BODY = lab(["brick_front", "brick_side_strip", "coping"]);
  const ATTACH = lab(["awning", "signbox", "ac", "iron_landing_upper", "iron_landing_lower", "frame"]);
  const raw = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i += 1) if (BODY.has(cls.label[i]) && inWindow(i % w, (i / w) | 0, MASK.corner)) raw[i] = 1;
  const closed = erode(dilate(raw, w, h, MASK.close), w, h, MASK.close);
  const comps = maskComponents(closed, w, h);
  const body = new Uint8Array(w * h);
  // the wall is cut into pieces by the awning / sign; every piece of wall colour inside the window is the building
  // grow from the largest wall piece: another wall piece (the pier under the awning) or a FRONT attachment (fire
  // escape, awning, sign, AC: box from x0 - attachLeft) joins only when it touches the grown mask within `touch` px —
  // a neighbour's parapet strip that happens to read as coping never touches it
  const att = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i += 1) if (ATTACH.has(cls.label[i]) && inWindow(i % w, (i / w) | 0, MASK.overhang)) att[i] = 1;
  const cands = [
    ...comps.slice(1).filter((c) => c.n >= MASK.bodyMinPx).map((c) => ({ c, wall: true })),
    ...maskComponents(att, w, h).filter((c) => c.n >= MASK.attachMinPx && c.box[0] >= F.x0 - MASK.attachLeft).map((c) => ({ c, wall: false })),
  ];
  for (const i of comps[0].px) body[i] = 1;
  let all = fillHoles(body, w, h);
  const kept = [comps[0]];
  const attached = [];
  const rejected = [];
  for (let grew = true; grew;) {
    grew = false;
    const near = dilate(all, w, h, MASK.touch);
    for (const k of cands) {
      if (k.done) continue;
      let touching = 0;
      let outside = 0;
      for (const i of k.c.px) { if (near[i]) touching += 1; if (!all[i]) outside += 1; }
      if (!touching) continue;
      k.done = true;
      if (!outside) continue;
      for (const i of k.c.px) all[i] = 1;
      grew = true;
      if (k.wall) kept.push(k.c);
      else attached.push({ label: cls.names[cls.label[k.c.px[0]]], px: k.c.n, outsideBodyPx: outside, box: k.c.box });
    }
    if (grew) all = fillHoles(all, w, h);
  }
  for (const k of cands) if (!k.done && k.wall) rejected.push({ px: k.c.n, box: k.c.box, why: `wall-colour piece more than ${MASK.touch} px off the building` });
  const whole = dilate(fillHoles(erode(dilate(all, w, h, MASK.closeAll), w, h, MASK.closeAll), w, h), w, h, MASK.ink);
  for (let i = 0; i < w * h; i += 1) if (whole[i] && !inWindow(i % w, (i / w) | 0, MASK.overhang + MASK.ink)) whole[i] = 0;
  // one span per row -> a simple polygon
  const left = [];
  const right = [];
  let rowsTwoSpans = 0;
  for (let y = 0; y < h; y += 1) {
    let a = -1; let b = -1; let runs = 0; let prev = 0;
    for (let x = 0; x < w; x += 1) {
      const v = whole[y * w + x];
      if (v && a < 0) a = x;
      if (v) b = x;
      if (v && !prev) runs += 1;
      prev = v;
    }
    if (a < 0) continue;
    if (runs > 1) rowsTwoSpans += 1;
    left.push([a, y]);
    right.push([b + 1, y]);
  }
  const top = left[0][1];
  const bot = left[left.length - 1][1] + 1;
  const ring = [[left[0][0], top], ...left.slice(1).map(([x, y]) => [x, y]), [left[left.length - 1][0], bot], [right[right.length - 1][0], bot],
    ...right.slice().reverse().map(([x, y]) => [x, y]), [right[0][0], top]];
  const polygon = douglasPeucker(ring, MASK.simplify).map(([x, y]) => [x, y]);
  const mask = rasterPolygon(polygon, w, h);
  let fg = 0; let fgIn = 0; let areaPx = 0; let agree = 0;
  for (let i = 0; i < w * h; i += 1) {
    const j = i * img.c;
    const d = Math.min(img.data[j], img.data[j + 1], img.data[j + 2]) < 235;
    if (d) fg += 1;
    if (d && mask[i]) fgIn += 1;
    if (mask[i]) areaPx += 1;
    if (mask[i] === whole[i]) agree += 1;
  }
  const xs = polygon.map((p) => p[0]); const ys = polygon.map((p) => p[1]);
  return {
    polygon,
    mask,
    evidence: {
      method: `window: x <= face x1 ${F.x1} + ${MASK.corner} px (walls) / + ${MASK.overhang} px (attachments), y <= the ground `
        + `line (front F.groundLine, side return rising at mZ ${mZ} left of x0 ${F.x0}) + ${MASK.ink} px, y >= the roof's back-right edge `
        + `(face top at x1 - crown ${Math.round(crownPx)} px - ${2 * MASK.ink} px, rising at mZ); `
        + `labels ${[...BODY].map((k) => cls.names[k]).join("+")} inside it closed r${MASK.close}, ${kept.length} component(s) >= ${MASK.bodyMinPx} px `
        + `(${kept.reduce((s, c) => s + c.n, 0)} px from ${raw.reduce((s, v) => s + v, 0)} raw px), holes filled; + ${attached.length} attached `
        + `${[...ATTACH].map((k) => cls.names[k]).join("/")} component(s) touching it within ${MASK.touch} px; closed r${MASK.closeAll}, `
        + `filled, dilated ${MASK.ink} px (the outer ink contour); one span per row, Douglas-Peucker ${MASK.simplify} px`,
      constants: MASK,
      bodyComponents: kept.map((c) => ({ px: c.n, box: c.box })),
      rejectedWallPieces: rejected,
      attached,
      rowsWithTwoSpans: rowsTwoSpans,
      vertices: polygon.length,
      bboxPx: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)],
      areaPx,
      rasterAgreement: Math.round((agree / (w * h)) * 1e5) / 1e5,
      targetFgPx: fg,
      targetFgInsidePx: fgIn,
      targetFgInsideShare: Math.round((fgIn / fg) * 1000) / 1000,
    },
  };
}

/** Evidence overlay: the target dimmed outside the mask, the polygon outline in red. */
export async function maskEvidencePng(img, m, file) {
  const out = Buffer.alloc(img.w * img.h * 3);
  for (let i = 0; i < img.w * img.h; i += 1) {
    for (let c = 0; c < 3; c += 1) {
      const v = img.data[i * img.c + c];
      out[i * 3 + c] = m.mask[i] ? v : Math.round(v * 0.3 + 255 * 0.7);
    }
  }
  const pts = m.polygon.map(([x, y]) => `${x},${y}`).join(" ");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${img.w}" height="${img.h}"><polygon points="${pts}" fill="none" stroke="#e01010" stroke-width="2"/></svg>`;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  await sharp(out, { raw: { width: img.w, height: img.h, channels: 3 } }).composite([{ input: Buffer.from(svg) }]).png().toFile(file);
}

/** The `_subjectMask` record layout.measured.json carries (scripts/registered.mjs subjectMaskOf reads `polygon`). */
export const subjectMaskRecord = (m, img, S) => ({
  _subjectMask: {
    _comment: "MEASURED by scripts/measure-target.mjs subjectMask (WF-V4 V4-6 item 5): the brick building's visible "
      + "silhouette — front, side return, crown / roof deck, attached fire escape, awning, sign, AC — neighbours excluded. "
      + "Registered IoU, residuals and FIT score target foreground INSIDE this polygon (target px, image frame).",
    source: S ? S.rel.target : null,
    image: { w: img.w, h: img.h },
    polygon: m.polygon,
    evidence: m.evidence,
  },
});

// ---------------------------------------------------------------------------
// layout.json generation (C1.2) and --check (C1.1)
// ---------------------------------------------------------------------------

/** Astra B2: tolerances are FEATURE-RELATIVE, never a blanket +/- 0.05. */
export const tolFor = (value) => Math.round(Math.max(0.02, 0.15 * Math.abs(value)) * 1000) / 1000;

/** The generated-file header; `_source` names the subject's own manifest paths. */
const head = (S) => ({
  _comment: "GENERATED by scripts/measure-target.mjs --freeze. Do not hand-edit: WF-LOOP-R3 C1 rules "
    + "that a layout key is a MEASUREMENT WITH EVIDENCE, and that no hand-typed number enters this file "
    + "mid-run (r2's window.w 0.16 and the orchestrator's 1.8 W depth are what that rule is for). Every "
    + "value is a fraction of the face width W (the massing x extent) or the wall height H (its y extent) "
    + "in the AUTHOR frame, so the file is camera-free: a rescale or a re-solve cannot move it. Fractions "
    + "along W are measured from the STREET-RIGHT edge (author -x, the massing's min x). V12_LAYOUT in "
    + "src/validate/kernel-chain.mjs measures these off part AABBs BY ROLE; a key whose role is not built "
    + "yet is skipped, and a key marked `unverified` is SKIPPED AND REPORTED, never enforced. Keys marked "
    + "`measuredBy: likeness` are screen-space rows for scripts/likeness.mjs, not geometry V12 can see.",
  _source: `scripts/measure-target.mjs on ${S.rel.target} + ${S.rel.camera} `
    + `+ ${S.rel.regions}`,
  _units: "value/values/min/max are in `unit`: W = fraction of face width, H = fraction of wall height, "
    + "m = metres. `tol` is FEATURE-RELATIVE (Astra B2): max(0.02, 0.15 x value) in the key's unit.",
});

export const frameRecord = (frame) => ({
  _frame: {
    facePx: `${frame.x0}..${frame.x1}`,
    W: frame.W,
    H: Math.round(frame.H),
    slope: r3(frame.slope),
    slopeFit: frame.evidence.slopeFit,
    camera: frame.evidence.camera,
    ...(Number.isFinite(frame.proudDrop) ? { proudDrop: frame.proudDrop, proudDropFit: frame.evidence.proudDrop } : {}),
    // WORKFLOW-V3 §7.1 — the measured front-face quad, px, order [top-left,
    // top-right, bottom-right, bottom-left]. likeness.mjs reads it; without it
    // every LK_AREA row ran on a fallback quad sheared by the RENDER's slope.
    quadPx: [
      [frame.x0, frame.topLine(frame.x0)], [frame.x1, frame.topLine(frame.x1)],
      [frame.x1, frame.groundLine(frame.x1)], [frame.x0, frame.groundLine(frame.x0)],
    ].map(([x, y]) => [Math.round(x * 10) / 10, Math.round(y * 10) / 10]),
    note: "the r2 file was seeded off a 261 px frame (front PLUS side return); the front plane is "
      + `${frame.W} px wide and ${Math.round(frame.H)} px tall`,
  },
});

/** A list key's tol is set by its SMALLEST member: 0.15 x 0.81 would let the
 *  0.23 bay wander a third of the face. */
function tolOf(entry) {
  if (Array.isArray(entry.values)) return tolFor(Math.min(...entry.values.map(Math.abs)));
  return Number.isFinite(entry.value) ? tolFor(entry.value) : null;   // a string key has no band
}

export function freezeLayout(measured, frame, S = loadSubject(subjectIdFromArgv())) {
  const out = { ...head(S), ...frameRecord(frame) };
  for (const [k, v] of Object.entries(measured)) {
    const tol = v.unverified ? null : tolOf(v);
    out[k] = tol === null ? { ...v } : { ...v, tol };
  }
  return out;
}

/** null when the frozen entry agrees with the measurement, else a miss line. */
export function checkKey(frozen, measuredEntry) {
  if (!measuredEntry) return { kind: "missing", text: "no measurement produces this key" };
  if (measuredEntry.unverified) {
    return frozen.unverified === true ? null
      : { kind: "unverified", text: `the measurement cannot resolve this key (${measuredEntry.reason})` };
  }
  if (frozen.unverified === true) return null;               // frozen stands down; never enforced
  const tol = Number.isFinite(frozen.tol) ? frozen.tol : tolFor(frozen.value ?? 1);
  if (typeof measuredEntry.value === "string") {
    return frozen.value === measuredEntry.value ? null
      : { kind: "value", text: `frozen "${frozen.value}" vs measured "${measuredEntry.value}"` };
  }
  if (Array.isArray(measuredEntry.values)) {
    const a = [...(frozen.values ?? [])].sort((x, y) => x - y);
    const b = [...measuredEntry.values].sort((x, y) => x - y);
    if (a.length !== b.length) return { kind: "count", text: `frozen ${a.length} values vs measured ${b.length}` };
    for (let i = 0; i < a.length; i += 1) {
      if (Math.abs(a[i] - b[i]) > tol + 1e-9) {
        return { kind: "value", text: `frozen ${a[i]} vs measured ${b[i]} (tol ${tol})` };
      }
    }
    return null;
  }
  const frozenValue = Number.isFinite(frozen.value) ? frozen.value
    : (Number.isFinite(frozen.min) && Number.isFinite(frozen.max) ? (frozen.min + frozen.max) / 2 : null);
  if (frozenValue === null) return { kind: "shape", text: "frozen entry carries no value to compare" };
  const delta = Math.abs(frozenValue - measuredEntry.value);
  return delta > tol + 1e-9
    ? { kind: "value", text: `frozen ${frozenValue} vs measured ${measuredEntry.value} (off by ${r3(delta)}, tol ${tol})` }
    : null;
}

export function checkLayout(frozenLayout, measured) {
  const rows = [];
  for (const [k, v] of Object.entries(frozenLayout)) {
    if (k.startsWith("_")) continue;
    const miss = checkKey(v, measured[k]);
    rows.push({ key: k, ok: miss === null, ...(miss ?? {}) });
  }
  for (const k of Object.keys(measured)) {
    if (!Object.hasOwn(frozenLayout, k)) rows.push({ key: k, ok: false, kind: "absent", text: "measured but not in the frozen layout" });
  }
  return rows;
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function arg(argv, name, fallback) {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
}

export async function main(argv = process.argv.slice(2)) {
  // WORKFLOW-V3 §7.5 — file paths come from subjects/<s>/subject.json; the scan
  // logic above stays subject-specific by design.
  const S = loadSubject(subjectIdFromArgv(argv));
  const HEAD = head(S);
  const targetFile = path.resolve(ROOT, arg(argv, "--target", S.rel.target));
  const regionsFile = path.resolve(ROOT, arg(argv, "--regions", S.rel.regions));
  const cameraFile = path.resolve(ROOT, arg(argv, "--camera", S.rel.camera));
  const layoutFile = path.resolve(ROOT, arg(argv, "--layout", S.rel.layout));
  const outFile = path.resolve(ROOT, arg(argv, "--out", S.rel.layoutMeasured));

  const { keys, frame, cls, img, camera } = await measureTarget({ targetFile, regionsFile, cameraFile });
  // WF-V4 V4-6 item 5: the subject mask rides every write; `--subject-mask` writes ONLY it into the existing file
  // (every other key byte-stable) plus an evidence overlay PNG (`--mask-png <file>`).
  const sm = S.klass === "building" ? subjectMask(img, cls, frame, camera, (keys["crown.height"]?.value ?? 0) * frame.H) : null;
  if (sm && arg(argv, "--mask-png", null)) await maskEvidencePng(img, sm, path.resolve(ROOT, arg(argv, "--mask-png", null)));
  if (argv.includes("--subject-mask")) {
    if (!sm) throw new Error("measure-target: --subject-mask is a building-class measurement");
    const cur = JSON.parse(fs.readFileSync(outFile, "utf8"));
    delete cur._subjectMask;
    fs.writeFileSync(outFile, `${JSON.stringify({ ...cur, ...subjectMaskRecord(sm, img, S) }, null, 2)}\n`);
    process.stdout.write(`_subjectMask: ${sm.polygon.length} vertices, ${sm.evidence.areaPx} px, target fg inside ${sm.evidence.targetFgInsidePx}/${sm.evidence.targetFgPx} px -> ${path.relative(ROOT, outFile)}\n`);
    return 0;
  }

  if (argv.includes("--json")) {
    process.stdout.write(`${JSON.stringify(keys, null, 2)}\n`);
  } else {
    process.stdout.write(`face ${frame.x0}..${frame.x1} (${frame.W} px) x ${Math.round(frame.H)} px, `
      + `slope ${frame.slope.toFixed(4)} — ${frame.evidence.slopeFit}\n`);
    for (const [k, v] of Object.entries(keys)) {
      const value = v.unverified ? "UNVERIFIED" : (Array.isArray(v.values) ? v.values.join(" / ") : v.value);
      process.stdout.write(`  ${k.padEnd(26)} ${String(value).padStart(14)} ${(v.unit ?? "").padEnd(22)} `
        + `${v.unverified ? v.reason : v.evidence.px}\n`);
    }
  }

  if (!argv.includes("--check")) {
    fs.writeFileSync(outFile, `${JSON.stringify({ ...HEAD, _comment: `MEASURED, not frozen — scripts/measure-target.mjs writes this file on every run and --freeze copies it into layout.json. ${HEAD._comment}`, ...frameRecord(frame), ...keys, ...(sm ? subjectMaskRecord(sm, img, S) : {}) }, null, 2)}\n`);
  }

  if (argv.includes("--freeze")) {
    fs.writeFileSync(layoutFile, `${JSON.stringify(freezeLayout(keys, frame, S), null, 2)}\n`);
    process.stdout.write(`froze ${path.relative(ROOT, layoutFile)}\n`);
  }

  if (argv.includes("--check")) {
    const frozen = JSON.parse(fs.readFileSync(layoutFile, "utf8"));
    const rows = checkLayout(frozen, keys);
    const bad = rows.filter((r) => !r.ok);
    for (const r of bad) process.stdout.write(`CHECK FAIL ${r.key}: ${r.text}\n`);
    process.stdout.write(bad.length === 0
      ? `CHECK PASS: ${rows.length} layout keys agree with the measurement\n`
      : `CHECK FAIL: ${bad.length}/${rows.length} layout keys disagree with the measurement\n`);
    return bad.length === 0 ? 0 : 1;
  }
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((code) => { process.exitCode = code; });
}
