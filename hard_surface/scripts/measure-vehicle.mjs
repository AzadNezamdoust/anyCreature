#!/usr/bin/env node
// WORKFLOW-V3 §5 pickup row / §7 item 10 — THE MEASURING INSTRUMENT for the
// vehicle class, the sibling of scripts/measure-target.mjs (buildings). Same rule:
// a layout key is a MEASUREMENT WITH EVIDENCE, or it is `unverified` with a reason.
//
//   node scripts/measure-vehicle.mjs --subject pickup            measure, write layout.measured.json
//   node scripts/measure-vehicle.mjs --subject pickup --freeze   ... and REGENERATE layout.json
//   node scripts/measure-vehicle.mjs --subject pickup --check    compare the frozen layout; exit 1 on drift
//   options: --target <png> --regions <json> --camera <json> --layout <json> --out <json> --overlay <png>
//
// METHOD — orthographic, so every screen offset is a LINEAR image of a world
// offset. With the solved camera (theta elevation, phi azimuth), one world metre
// along each axis moves the pixel by (y down):
//   eX = ( cos phi,  sin theta sin phi)      eZ = (-sin phi,  sin theta cos phi)      eY = (0, -cos theta)
// (this reproduces the solve's slopes mX = sin theta tan phi, mZ = sin theta / tan phi).
// The unknown scale s cancels in every fraction, so offsets are kept in "px units".
//   * FLANK frame: the vehicle's +X side is a plane x = xF seen face-on-ish; a pixel
//     on it rectifies to (z, y) by solving p - O = z eZ + y eY. O = the front wheel
//     centre. This is the side ELEVATION of the truck at true proportion.
//   * A point off the flank by a KNOWN dx rectifies the same way with dx eX added.
//   * A mirrored PAIR (headlights, mirrors) shares y and z: p_near - p_far = 2d eX
//     (checked against mX), and the midpoint lies on the centre plane dx = -W/2.
// Landmarks come off the target's own pixels: nearest-zone-median classification
// (regions.json), near-vertical ink chains, and rays from the wheel centres.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

import { loadSubject, subjectIdFromArgv } from "./subject.mjs";
import { tolFor, checkLayout } from "./measure-target.mjs";

const require = createRequire(import.meta.url);
const sharp = require("sharp");

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

/** Unratified instrument thresholds — every one is about the target's pixels, not the truck. */
export const SCAN = Object.freeze({
  inkLum: 60,            // Rec.709 luma below which a pixel is a contour line
  tyreMinPx: 2000,       // a tyre-face component smaller than this is a sliver (the far-front tyre)
  lampMinPx: 300,
  mirrorMinPx: 50,
  mirrorGroupGap: 30,    // px between mirror components that are one mirror (head + arm)
  rayFrom: 200,          // deg, rectified; the lower arc of a tyre face (the top is under the arch)
  rayTo: 340,
  rayStep: 2,
  rayMax: 160,           // px units
  rayLeave: 8,           // px units past the last tyre px before a ray stops
  chainMin: 30,          // px, a near-vertical ink chain shorter than this is not an edge
  chainDrift: 0.12,      // |dx| / length
  chainGap: 3,           // rows of missing ink a chain may bridge
  slotMinPx: 3,          // bed-interior px between the cab rear and the bed front
  slotRows: [10, 60],    // rows below the flank rim scanned for that slot
  edgeBridge: 15,        // rows the cab-rear walk may bridge where the bed bulkhead rim crosses it
  nonWhite: 240,         // a channel below this is not the background
});

// ---------------------------------------------------------------------------
// Pixels
// ---------------------------------------------------------------------------

export async function readImage(file) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data, w: info.width, h: info.height, c: info.channels };
}
const at = (img, x, y) => { const i = (y * img.w + x) * img.c; return [img.data[i], img.data[i + 1], img.data[i + 2]]; };
const lum = (p) => 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
const hex = (p) => `#${p.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
const r3 = (x) => Math.round(x * 1000) / 1000;
const r1 = (x) => Math.round(x * 10) / 10;
const median = (values) => { const s = [...values].sort((a, b) => a - b); return s.length ? s[s.length >> 1] : NaN; };

/** Zone medians from the frozen rects, with purity (share within 10/255 of the median). */
function zoneMedians(img, regions) {
  const out = {};
  for (const [name, zone] of Object.entries(regions.zones)) {
    const samples = [];
    for (const [x, y, w, h] of zone.rects) for (let j = y; j < y + h; j += 1) for (let i = x; i < x + w; i += 1) samples.push(at(img, i, j));
    const med = [0, 1, 2].map((k) => median(samples.map((p) => p[k])));
    const purity = samples.filter((p) => Math.max(...p.map((v, k) => Math.abs(v - med[k]))) <= 10).length / samples.length;
    out[name] = { rgb: med, hex: hex(med), px: samples.length, purity: r3(purity), role: zone.role };
  }
  return out;
}

/** Nearest zone median within regions.areaTolerance; 255 = abstain. */
export function classify(img, zones, tol) {
  const names = Object.keys(zones);
  const refs = names.map((n) => zones[n].rgb);
  const label = new Uint8Array(img.w * img.h).fill(255);
  const tol2 = tol * tol;
  for (let y = 0; y < img.h; y += 1) {
    for (let x = 0; x < img.w; x += 1) {
      const p = at(img, x, y);
      let best = 255, bd = Infinity;
      for (let k = 0; k < refs.length; k += 1) {
        const d = (p[0] - refs[k][0]) ** 2 + (p[1] - refs[k][1]) ** 2 + (p[2] - refs[k][2]) ** 2;
        if (d < bd) { bd = d; best = k; }
      }
      if (bd <= tol2) label[y * img.w + x] = best;
    }
  }
  return { label, names, idx: (name) => names.indexOf(name) };
}

/** 4-connected components of the pixels whose label is in `ks`. */
export function components(img, cls, ks, minPx, keepPixels = false) {
  const set = new Set(ks);
  const seen = new Uint8Array(img.w * img.h);
  const out = [];
  for (let s = 0; s < seen.length; s += 1) {
    if (seen[s] || !set.has(cls.label[s])) continue;
    const stack = [s];
    seen[s] = 1;
    let n = 0, sx = 0, sy = 0, x0 = img.w, x1 = 0, y0 = img.h, y1 = 0;
    const pts = keepPixels ? [] : null;
    while (stack.length) {
      const i = stack.pop();
      const x = i % img.w, y = (i / img.w) | 0;
      n += 1; sx += x; sy += y;
      if (pts) pts.push([x, y]);
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      for (const [j, ok] of [[i - 1, x > 0], [i + 1, x + 1 < img.w], [i - img.w, y > 0], [i + img.w, y + 1 < img.h]]) {
        if (ok && !seen[j] && set.has(cls.label[j])) { seen[j] = 1; stack.push(j); }
      }
    }
    if (n >= minPx) out.push({ n, cx: sx / n, cy: sy / n, x0, y0, x1, y1, ...(pts ? { pts } : {}) });
  }
  return out;
}

/** Near-vertical ink chains: walk down with +-1 px drift, bridging short gaps. */
function inkChains(img) {
  const ink = (x, y) => x >= 0 && y >= 0 && x < img.w && y < img.h && lum(at(img, x, y)) < SCAN.inkLum;
  const used = new Uint8Array(img.w * img.h);
  const chains = [];
  for (let y = 0; y < img.h; y += 1) {
    for (let x = 0; x < img.w; x += 1) {
      if (!ink(x, y) || used[y * img.w + x]) continue;
      const pts = [[x, y]];
      let cx = x, cy = y;
      for (;;) {
        let next = null;
        for (let g = 1; g <= SCAN.chainGap + 1 && !next; g += 1) {
          const c = [cx, cx - 1, cx + 1].find((q) => ink(q, cy + g));
          if (c !== undefined) next = [c, cy + g];
        }
        if (!next) break;
        [cx, cy] = next;
        pts.push(next);
      }
      for (const [px, py] of pts) used[py * img.w + px] = 1;
      const len = pts[pts.length - 1][1] - pts[0][1] + 1;
      if (len < SCAN.chainMin) continue;
      if (Math.abs(pts[pts.length - 1][0] - pts[0][0]) / len > SCAN.chainDrift) continue;
      chains.push({ xTop: pts[0][0], yTop: pts[0][1], xBot: cx, yBot: cy, len, xMean: pts.reduce((s, p) => s + p[0], 0) / pts.length });
    }
  }
  return chains;
}

const longest = (list) => list.reduce((a, b) => (!a || b.len > a.len ? b : a), null);
const chainPx = (c) => `x ${r1(c.xMean)}, y ${c.yTop}..${c.yBot} (${c.len} px)`;

/** 3x3 linear solve (Cramer). */
function solve3(A, b) {
  const det = (m) => m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  const D = det(A);
  return [0, 1, 2].map((k) => det(A.map((row, i) => row.map((v, j) => (j === k ? b[i] : v)))) / D);
}

/** Kasa algebraic circle fit. */
function fitCircle(points) {
  let sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0, sxz = 0, syz = 0, sz = 0;
  for (const [x, y] of points) {
    const z = x * x + y * y;
    sx += x; sy += y; sxx += x * x; syy += y * y; sxy += x * y; sxz += x * z; syz += y * z; sz += z;
  }
  const n = points.length;
  const [D, E, F] = solve3([[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]], [-sxz, -syz, -sz]);
  const cx = -D / 2, cy = -E / 2;
  const r = Math.sqrt(cx * cx + cy * cy - F);
  const rms = Math.sqrt(points.reduce((s, [x, y]) => s + (Math.hypot(x - cx, y - cy) - r) ** 2, 0) / n);
  return { cx, cy, r, rms };
}

// ---------------------------------------------------------------------------
// The measurement
// ---------------------------------------------------------------------------

export async function measureVehicle({ targetFile, regionsFile, cameraFile, variant = "pickup" }) {
  // V4-7: the class body VARIANT (subject.json `variant`, classes/vehicle.json variants) picks the landmark set; the
  // camera frame, the pixel classifier and the pair / plane rectification are shared (measureBus below).
  if (variant === "bus") return measureBus({ targetFile, regionsFile, cameraFile });
  if (variant !== "pickup") throw new Error(`measure-vehicle: unknown body variant "${variant}" (classes/vehicle.json variants)`);
  const img = await readImage(targetFile);
  const regions = JSON.parse(fs.readFileSync(regionsFile, "utf8"));
  const camera = JSON.parse(fs.readFileSync(cameraFile, "utf8"));
  if (camera.provisional !== false) throw new Error(`${cameraFile} is provisional — solve the camera first`);
  const th = (camera.theta_deg * Math.PI) / 180;
  const ph = (camera.phi_deg * Math.PI) / 180;
  const sT = Math.sin(th), cT = Math.cos(th), sP = Math.sin(ph), cP = Math.cos(ph);
  const eX = [cP, sT * sP], eZ = [-sP, sT * cP], eY = [0, -cT];

  const zones = zoneMedians(img, regions);
  const cls = classify(img, zones, regions.areaTolerance ?? 32);
  const L = (name) => cls.idx(name);
  const labelAt = (x, y) => (x >= 0 && y >= 0 && x < img.w && y < img.h ? cls.label[Math.round(y) * img.w + Math.round(x)] : 255);
  const isInk = (x, y) => x >= 0 && y >= 0 && x < img.w && y < img.h && lum(at(img, Math.round(x), Math.round(y))) < SCAN.inkLum;

  // ---- wheels -------------------------------------------------------------
  const tyres = components(img, cls, [L("tyre")], SCAN.tyreMinPx).sort((a, b) => b.n - a.n).slice(0, 2).sort((a, b) => a.cx - b.cx);
  if (tyres.length < 2) throw new Error(`found ${tyres.length} tyre face(s) >= ${SCAN.tyreMinPx} px; need the two near wheels`);
  const tyreFit = (t) => {
    let sx = 0, sy = 0, n = 0;
    for (let y = t.y0; y <= t.y1; y += 1) for (let x = t.x0; x <= t.x1; x += 1) {
      const k = cls.label[y * img.w + x];
      if (k === L("hub") || k === L("bumper")) { sx += x; sy += y; n += 1; }
    }
    let centre = n > 0 ? [sx / n, sy / n] : [t.cx, t.cy];
    let fit = null;
    let rays = 0;
    for (let iter = 0; iter < 2; iter += 1) {
      const pts = [];
      for (let a = SCAN.rayFrom; a <= SCAN.rayTo; a += SCAN.rayStep) {
        const dz = Math.cos((a * Math.PI) / 180), dy = Math.sin((a * Math.PI) / 180);
        const v = [dz * eZ[0] + dy * eY[0], dz * eZ[1] + dy * eY[1]];
        let last = 0;
        for (let s = 0; s <= SCAN.rayMax; s += 0.25) {
          if (labelAt(centre[0] + s * v[0], centre[1] + s * v[1]) === L("tyre")) last = s;
          else if (last > 0 && s - last > SCAN.rayLeave) break;
        }
        if (last > 0) pts.push([last * dz, last * dy]);
      }
      fit = fitCircle(pts);
      rays = pts.length;
      centre = [centre[0] + fit.cx * eZ[0] + fit.cy * eY[0], centre[1] + fit.cx * eZ[1] + fit.cy * eY[1]];
    }
    return { centre, r: fit.r, rms: fit.rms, rays, box: [t.x0, t.y0, t.x1, t.y1] };
  };
  const wheelF = tyreFit(tyres[0]);
  const wheelR = tyreFit(tyres[1]);

  const O = wheelF.centre;
  /** image px of a flank-frame point (dx off the flank plane, z, y). */
  const toPx = (dx, z, y) => [O[0] + dx * eX[0] + z * eZ[0], O[1] + dx * eX[1] + z * eZ[1] + y * eY[1]];
  /** (z, y) of image point p assuming it lies dx off the flank plane. */
  const rect = (p, dx = 0) => {
    const z = (O[0] + dx * eX[0] - p[0]) / sP;
    const y = (O[1] + dx * eX[1] + z * eZ[1] - p[1]) / cT;
    return { z, y };
  };

  const rearC = rect(wheelR.centre);
  const groundF = 0 - wheelF.r;
  const groundR = rearC.y - wheelR.r;
  const yG = (groundF + groundR) / 2;

  // ---- edges ----------------------------------------------------------------
  const chains = inkChains(img);
  const lamps = components(img, cls, [L("headlight")], SCAN.lampMinPx, true).sort((a, b) => b.n - a.n).slice(0, 2).sort((a, b) => a.cx - b.cx);
  if (lamps.length < 2) throw new Error("fewer than two headlight components");
  const glass = components(img, cls, [L("glass")], 500, true).sort((a, b) => b.n - a.n).slice(0, 2).sort((a, b) => a.cx - b.cx);
  const sideWindow = glass[glass.length - 1];
  const mirrorComps = components(img, cls, [L("mirror")], SCAN.mirrorMinPx, true);
  const mirrorGroups = [];
  for (const c of mirrorComps.sort((a, b) => a.cx - b.cx)) {
    const g = mirrorGroups.find((m) => c.x0 <= m.x1 + SCAN.mirrorGroupGap && m.x0 <= c.x1 + SCAN.mirrorGroupGap
      && c.y0 <= m.y1 + SCAN.mirrorGroupGap && m.y0 <= c.y1 + SCAN.mirrorGroupGap);
    if (g) { g.sx += c.cx * c.n; g.sy += c.cy * c.n; g.n += c.n; g.x0 = Math.min(g.x0, c.x0); g.x1 = Math.max(g.x1, c.x1); g.y0 = Math.min(g.y0, c.y0); g.y1 = Math.max(g.y1, c.y1); g.comps.push(c); }
    else mirrorGroups.push({ sx: c.cx * c.n, sy: c.cy * c.n, n: c.n, x0: c.x0, x1: c.x1, y0: c.y0, y1: c.y1, comps: [c] });
  }
  const mirrors = mirrorGroups.sort((a, b) => b.n - a.n).slice(0, 2).map((g) => ({ ...g, cx: g.sx / g.n, cy: g.sy / g.n })).sort((a, b) => a.cx - b.cx);

  const tF = tyres[0], tR = tyres[1];
  const noseLeft = longest(chains.filter((c) => c.xMean < lamps[0].x0));
  const frontCorner = longest(chains.filter((c) => c.xMean > lamps[1].x1 && c.xMean < tF.x0 && c.yBot < tF.cy));
  const doorFront = longest(chains.filter((c) => c.xMean > tF.x1 && c.xMean < sideWindow.cx && c.yTop > (mirrors[1]?.y1 ?? 0)));

  let bodyMaxX = -1;
  for (let i = 0; i < cls.label.length; i += 1) {
    const k = cls.label[i];
    if ((k === L("body_side") || k === L("body_front")) && i % img.w > bodyMaxX) bodyMaxX = i % img.w;
  }
  const rearCorner = longest(chains.filter((c) => c.xMean >= bodyMaxX - 2 && c.xMean <= bodyMaxX + 6));
  for (const [name, c] of [["nose-left corner", noseLeft], ["flank front corner", frontCorner], ["door front", doorFront], ["flank rear corner", rearCorner]]) {
    if (!c) throw new Error(`no ink chain found for the ${name}`);
  }

  const zFC = rect([frontCorner.xMean, frontCorner.yBot]).z;
  const zRC = rect([rearCorner.xMean, rearCorner.yBot]).z;
  const Lpx = zFC - zRC;
  const Wpx = (frontCorner.xMean - noseLeft.xMean) / cP;

  // Silhouette top vertex = the roof's far-rear corner, dx = -W off the flank.
  let topY = -1;
  const topXs = [];
  for (let y = 0; y < img.h && topY < 0; y += 1) {
    for (let x = 0; x < img.w; x += 1) if (Math.min(...at(img, x, y)) < SCAN.nonWhite) { topY = y; break; }
  }
  for (let y = topY; y <= topY + 1; y += 1) for (let x = 0; x < img.w; x += 1) if (Math.min(...at(img, x, y)) < SCAN.nonWhite) topXs.push(x);
  const topPx = [median(topXs), topY + 0.5];

  // Bed wall top = the top of the flank's rear corner edge.
  const bedTop = rect([rearCorner.xTop, rearCorner.yTop]);
  const hoodTop = rect([frontCorner.xTop, frontCorner.yTop]);

  // Cab rear / bed front: the bed-interior SLOT between two ink lines, just below the flank rim.
  const slotRows = [];
  const zAtSlot = rect([sideWindow.x1 + 40, 0]).z;
  const rimRow = Math.round(toPx(0, zAtSlot, bedTop.y)[1]);
  for (let y = rimRow + SCAN.slotRows[0]; y <= rimRow + SCAN.slotRows[1]; y += 1) {
    let x = sideWindow.x1;
    while (x < rearCorner.xMean) {
      if (!isInk(x, y)) { x += 1; continue; }
      let a = x; while (isInk(a + 1, y)) a += 1;
      let b = a + 1, slot = 0;
      while (b < rearCorner.xMean && !isInk(b, y)) { if (labelAt(b, y) === L("bed_inside")) slot += 1; b += 1; }
      if (slot >= SCAN.slotMinPx && b - a <= 12 && labelAt(a - 2, y) === L("body_side")) { slotRows.push([a, b, y]); break; }
      x = b;
    }
  }
  if (slotRows.length === 0) throw new Error("no cab/bed slot found below the flank rim");
  const cabRearX = median(slotRows.map((s) => s[0]));
  const bedFrontX = median(slotRows.map((s) => s[1]));
  const slotY = median(slotRows.map((s) => s[2]));

  // Cab roof on the flank: walk the cab-rear ink up from the slot while a body px sits left of it
  // and a bed-interior px right of it.
  let edgeX = cabRearX, edgeTop = slotY;
  for (let y = slotY - 1, miss = 0; y > 0 && miss < SCAN.edgeBridge; y -= 1) {
    let hit = null;
    for (let x = edgeX - 1 - miss; x <= edgeX + 1 + miss && hit === null; x += 1) {   // near-vertical: +-1 px per row
      if (!isInk(x, y)) continue;
      let r = x; while (isInk(r + 1, y)) r += 1;
      const leftBody = [2, 3, 4].some((d) => labelAt(x - d, y) === L("body_side"));
      const rightBed = [1, 2, 3, 4].some((d) => labelAt(r + d, y) === L("bed_inside"));
      if (leftBody && rightBed) hit = x;
    }
    if (hit === null) { miss += 1; continue; }
    miss = 0; edgeX = hit; edgeTop = y;
  }
  const cabTop = rect([edgeX, edgeTop]);
  // H = the cab roof ON the flank plane. The silhouette top (the far roof corner) is only a cross-check:
  // rectified at the height H it implies the roof's x offset from the flank, i.e. how much the cab tapers.
  const Hpx = cabTop.y - yG;
  const roofDx = (topPx[0] - O[0] - rect([edgeX, edgeTop]).z * eZ[0]) / eX[0];

  // Front bumper: down the flank front-corner column from the bottom of that edge.
  const colX = frontCorner.xBot;
  let bumperTopY = null;
  const inkRows = [];
  for (let y = frontCorner.yBot + 1; y < img.h; y += 1) {
    const white = Math.min(...at(img, colX, y)) >= SCAN.nonWhite;
    if (white) break;
    if (bumperTopY === null && labelAt(colX, y) === L("bumper")) bumperTopY = y;
    if (bumperTopY !== null && isInk(colX, y) && !isInk(colX, y - 1)) inkRows.push(y);
  }
  const bumperFront = bumperTopY !== null && inkRows.length >= 2
    ? { topY: bumperTopY, h: (inkRows[inkRows.length - 1] - inkRows[0]) / cT, inkRows }
    : null;

  // Rear bumper: its +X face is the leftmost bumper component right of the rear tyre.
  const rearBumperComps = components(img, cls, [L("bumper")], 100).filter((c) => c.cx > tR.x1).sort((a, b) => a.x0 - b.x0);
  let bumperRear = null;
  if (rearBumperComps.length > 0) {
    const face = rearBumperComps[0];
    const x = Math.round((face.x0 + face.x1) / 2);
    let up = face.y0; while (up > 0 && !isInk(x, up)) up -= 1;
    let down = face.y1; while (down < img.h - 1 && !isInk(x, down)) down += 1;
    bumperRear = { x, up, down, h: (down - up) / cT, face };
    // WF-R5 R5-A — the +X face is the LARGEST bumper component right of the rear tyre; its left (front) edge is the
    // vertical corner at z = the flank rear corner (the block's +Z face shows outboard of the flank), so that corner
    // fixes the face's outboard offset, and its top end rectifies on that plane.
    const side = [...rearBumperComps].sort((a, b) => b.n - a.n)[0];
    const cx = side.x0 + 1;
    let top = side.y0; while (top < side.y1 && labelAt(cx, top) !== L("bumper") && labelAt(cx, top) !== L("hub")) top += 1;
    let bot = side.y1; while (bot > top && labelAt(cx, bot) !== L("bumper") && labelAt(cx, bot) !== L("hub")) bot -= 1;
    const out = (side.x0 - 0.5 - O[0] - zRC * eZ[0]) / eX[0];
    const t = rect([side.x0 - 0.5, top - 0.5], out);
    const b = rect([side.x0 - 0.5, bot + 0.5], out);
    const far = rect([side.x1 + 0.5, top - 0.5], out);
    Object.assign(bumperRear, { side, out, top: t, bot: b, depth: t.z - far.z, cornerX: side.x0 - 0.5, topY: top, botY: bot });
  }

  // Mirrored pairs.
  const pair = (far, near) => {
    const dxPx = near.cx - far.cx;
    const slope = (near.cy - far.cy) / dxPx;
    const mid = [(near.cx + far.cx) / 2, (near.cy + far.cy) / 2];
    const p = rect(mid, -Wpx / 2);
    return { slope, halfDx: dxPx / (2 * cP), y: p.y, z: p.z, far, near };
  };
  const lampPair = pair(lamps[0], lamps[1]);
  const mirrorPair = mirrors.length === 2 ? pair(mirrors[0], mirrors[1]) : null;

  // ---- keys ---------------------------------------------------------------
  const H = Hpx, Lb = Lpx, W = Wpx;
  const px = (p) => `${r1(p[0])}, ${r1(p[1])}`;
  const keys = {};
  const put = (k, value, unit, scan, pxText) => { keys[k] = { value: r3(value), unit, evidence: { scan, px: pxText } }; };
  const putList = (k, values, unit, scan, pxText) => { keys[k] = { values: values.map(r3), unit, evidence: { scan, px: pxText } }; };

  put("wheel.diameterOverL", (wheelF.r + wheelR.r) / Lb, "L",
    "tyre-face rays over the lower arc (200..340 deg, rectified onto the flank plane), Kasa circle fit per wheel, DIAMETER over body length (limits.v7._note)",
    `r ${r1(wheelF.r)} / ${r1(wheelR.r)} px units (rms ${r1(wheelF.rms)} / ${r1(wheelR.rms)}, ${wheelF.rays} / ${wheelR.rays} rays); L ${r1(Lb)}`);
  putList("wheel.centreFromFront", [zFC / Lb, (zFC - rearC.z) / Lb], "L",
    "wheel centres (circle fits) along the flank from the flank's front corner edge",
    `front ${px(wheelF.centre)}, rear ${px(wheelR.centre)}; front corner edge x ${r1(frontCorner.xMean)}`);
  put("wheelbase.overL", -rearC.z / Lb, "L", "rectified z between the two wheel centres over body length",
    `${r1(-rearC.z)} / ${r1(Lb)} px units`);
  keys["wheel.farSide"] = {
    unverified: true, unit: "count/geometry",
    reason: "the two -X wheels are occluded (only a tyre sliver under the front bumper shows); census.json still counts 4 wheels, VEH_MIRROR places them",
  };
  put("height.overL", H / Lb, "x L",
    "cab rear edge walked up from the cab/bed slot (body px left, bed-interior px right) to the roof, rectified on the flank; H over the ground line both wheel fits agree on",
    `edge top ${edgeX}, ${edgeTop} -> H ${r1(H)}; ground residual front/rear ${r1(Math.abs(groundF - groundR))} px units; L ${r1(Lb)}; silhouette top ${px(topPx)} puts the far roof corner ${r1(-roofDx)} px units off the flank = ${r3(-roofDx / W)} W (the cab tapers)`);
  put("width.overL", W / Lb, "x L",
    "nose-face corner edges: (x front corner - x nose-left corner) / cos phi over body length",
    `${chainPx(noseLeft)} and ${chainPx(frontCorner)}; W ${r1(W)}`);
  put("cab.start", (zFC - rect([doorFront.xMean, doorFront.yBot]).z) / Lb, "L",
    "door front edge on the flank (the cab's lower front corner; the windshield rakes forward of it above the hood)", chainPx(doorFront));
  put("cab.end", (zFC - rect([cabRearX, slotY]).z) / Lb, "L",
    "cab rear ink edge = left side of the bed-interior slot, rows just under the flank rim (the cab back rakes: this is its base)",
    `x ${cabRearX} over ${slotRows.length} rows around y ${slotY}`);
  put("bed.start", (zFC - rect([bedFrontX, slotY]).z) / Lb, "L", "bed front ink edge = right side of the same slot",
    `x ${bedFrontX} over ${slotRows.length} rows around y ${slotY}`);
  put("bed.end", (zFC - zRC) / Lb, "L", "the flank rear corner edge; L is measured to it, so this is 1 by construction", chainPx(rearCorner));
  put("hood.top", (hoodTop.y - yG) / H, "H", "top of the flank front-corner edge (the hood's +X front corner)",
    `${frontCorner.xTop}, ${frontCorner.yTop}`);
  put("cab.roof", (cabTop.y - yG) / H, "H",
    "the cab roof IS the top of the truck: no part of the silhouette rectifies above the cab roof line, so the gate measures cab max y / model max y = 1",
    `edge top ${edgeX}, ${edgeTop}; silhouette top ${px(topPx)}`);
  put("bedWall.top", (bedTop.y - yG) / H, "H", "top of the flank rear-corner edge", `${rearCorner.xTop}, ${rearCorner.yTop}`);
  if (bumperFront) {
    put("bumper.front.top", (rect([colX, bumperFront.topY - 0.5]).y - yG) / H, "H",
      "first bumper px under the flank front-corner edge (the bumper's top-back edge meets the nose face there)", `column ${colX}, y ${bumperFront.topY}`);
    put("bumper.front.h", bumperFront.h / H, "H",
      "vertical distance between the bumper front face's top and bottom ink lines along that column (parallel X-edges, so h cos theta)", `ink rows ${bumperFront.inkRows.join(", ")}`);
  } else {
    keys["bumper.front.top"] = { unverified: true, unit: "H", reason: "no bumper run under the flank front-corner edge" };
    keys["bumper.front.h"] = { unverified: true, unit: "H", reason: "no bumper run under the flank front-corner edge" };
  }
  if (bumperRear) {
    put("bumper.rear.h", bumperRear.h / H, "H", "the rear bumper's +X face: ink above to ink below at its centre column, over cos theta",
      `column ${bumperRear.x}, y ${bumperRear.up}..${bumperRear.down}`);
  } else {
    keys["bumper.rear.h"] = { unverified: true, unit: "H", reason: "no bumper component right of the rear tyre" };
  }
  keys["bumper.rear.top"] = {
    unverified: true, unit: "H",
    reason: "the rear bumper's +X face is not on the flank plane (its front edge sits left of the flank rear corner): its inset and its z cannot be separated in one still, so its height above the ground is not rectifiable here; WF-R5 scripts/measure-profile.mjs resolves it on the face's own plane (assuming the face starts at the flank rear corner's z) into _profile.keys bumper.rear.top",
  };
  put("headlight.centreY", (lampPair.y - yG) / H, "H",
    "lamp pair: centroids share y and z, midpoint rectified on the centre plane dx = -W/2",
    `far ${px([lampPair.far.cx, lampPair.far.cy])}, near ${px([lampPair.near.cx, lampPair.near.cy])}; pair slope ${r3(lampPair.slope)} vs mX ${r3(sT * sP / cP)}; lamp z ${r1(lampPair.z)} vs nose ${r1(zFC)}`);
  putList("headlight.offsetX", [-lampPair.halfDx / W, lampPair.halfDx / W], "W",
    "half the lamp-pair separation along eX, from the centre plane", `${r1(lampPair.halfDx)} / ${r1(W)} px units`);
  if (mirrorPair) {
    put("mirror.centreY", (mirrorPair.y - yG) / H, "H",
      "mirror pair (head + arm px, grouped): centroids share y and z, midpoint rectified on the centre plane",
      `far ${px([mirrorPair.far.cx, mirrorPair.far.cy])}, near ${px([mirrorPair.near.cx, mirrorPair.near.cy])}; pair slope ${r3(mirrorPair.slope)} vs mX ${r3(sT * sP / cP)}`);
  } else {
    keys["mirror.centreY"] = { unverified: true, unit: "H", reason: `found ${mirrors.length} mirror group(s), need a pair` };
  }
  // ---- appearance keys (WF-BLIND-R1 B2): the dimensions a detail pass builds to ----------------
  // Every extent below is taken off a classified zone component's own pixels, rectified onto a KNOWN
  // plane (the flank x = xF, the nose plane z = lamp z, or a z = const plane for the mirror heads),
  // and trimmed to its 1st..99th percentile so a stray antialiased pixel cannot move it.
  const q = (values, f) => { const v = [...values].sort((a, b) => a - b); return v[Math.min(v.length - 1, Math.max(0, Math.round(f * (v.length - 1))))]; };
  const span = (values) => ({ lo: q(values, 0.01), hi: q(values, 0.99) });
  /** (dx, y) of image point p on the plane z = zPlane (dx = offset off the flank plane, + outward). */
  const onZPlane = (p, zPlane) => {
    const dx = (p[0] - O[0] - zPlane * eZ[0]) / eX[0];
    const y = (p[1] - O[1] - dx * eX[1] - zPlane * eZ[1]) / eY[1];
    return { dx, y };
  };

  // Side window (the near pane on the flank): every glass px rectified on the flank plane.
  {
    const zs = [], ys = [];
    for (const p of sideWindow.pts) { const r = rect(p); zs.push(r.z); ys.push(r.y); }
    const z = span(zs), y = span(ys);
    const ev = `glass component ${sideWindow.n} px, box ${sideWindow.x0},${sideWindow.y0}..${sideWindow.x1},${sideWindow.y1}; rectified z ${r1(z.lo)}..${r1(z.hi)}, y ${r1(y.lo - yG)}..${r1(y.hi - yG)} px units above ground`;
    const scan = "the near side window's glass px rectified onto the flank plane (1..99th percentile); the pane is inset a few cm, which moves z by the same few cm";
    put("window.side.start", (zFC - z.hi) / Lb, "L", `${scan}; front edge from the nose`, ev);
    put("window.side.end", (zFC - z.lo) / Lb, "L", `${scan}; rear edge from the nose`, ev);
    put("window.side.bottom", (y.lo - yG) / H, "H", `${scan}; bottom edge above the ground`, ev);
    put("window.side.top", (y.hi - yG) / H, "H", `${scan}; top edge above the ground`, ev);
  }

  let wsTopW = null;
  // Windshield: its lower and upper edges run along X, so their screen length along eX IS the pane width.
  if (glass.length === 2) {
    const ws = glass[0];
    const mX = eX[1] / eX[0];
    const maxY = new Map(), minY = new Map();
    for (const [x, y] of ws.pts) {
      if (!maxY.has(x) || y > maxY.get(x)) maxY.set(x, y);
      if (!minY.has(x) || y < minY.get(x)) minY.set(x, y);
    }
    /** Walk columns from `start` in `dir` while each step stays on the eX slope (+-2 px per column step, so a
     *  cel edge a fraction of a degree off the camera slope does not accumulate); returns the last column. */
    const walk = (table, start, dir) => {
      let end = start[0];
      for (let x = start[0] + dir; table.has(x); x += dir) {
        if (Math.abs(table.get(x) - (table.get(end) + (x - end) * mX)) > 2) break;
        end = x;
      }
      return end;
    };
    const B = ws.pts.reduce((a, p) => (p[1] > a[1] || (p[1] === a[1] && p[0] > a[0]) ? p : a));   // lowest = bottom-near corner
    const D = ws.pts.reduce((a, p) => (p[1] < a[1] || (p[1] === a[1] && p[0] < a[0]) ? p : a));   // highest = top-far corner
    const ax = walk(maxY, B, -1);
    const cx = walk(minY, D, +1);
    const wBottom = (B[0] - ax) / eX[0];
    const wTop = (cx - D[0]) / eX[0];
    wsTopW = wTop;
    const zCab = rect([doorFront.xMean, doorFront.yBot]).z;
    const b = onZPlane(B, zCab);
    put("window.front.w", wBottom / W, "W",
      "windshield glass: the lower edge walked column by column from its lowest px along the eX slope (+-2 px per step) — an X edge, so its screen length / cos phi is the pane width",
      `lower edge x ${ax}..${B[0]} at y ${B[1]} -> ${r1(wBottom)}; upper edge x ${D[0]}..${cx} -> ${r1(wTop)} px units (cross-check); W ${r1(W)}`);
    put("window.front.bottom", (b.y - yG) / H, "H",
      "windshield bottom-near corner rectified on the cab-start plane (the pane's lower edge sits at the cowl, level with the door front edge top)",
      `corner ${B[0]}, ${B[1]}; inset ${r1(-b.dx)} px units from the flank; cab-start z ${r1(zCab)}`);
    // WF-R3 R3-B item 5 — the RAKE. The pane's near side edge runs parallel to the flank at the bottom corner's
    // inset (b.dx), so the top-near corner (the upper X edge's near end, found by the same eX walk) rectifies on
    // the KNOWN plane x = flank + b.dx: its height and its z separate there.
    const C = [cx, minY.get(cx)];
    const t = rect(C, b.dx);
    const tb = rect(B, b.dx);
    put("window.front.top", (t.y - yG) / H, "H",
      "windshield top-near corner (the upper X edge walked from the top-far corner) rectified on the plane x = flank + the bottom corner's inset: the raked pane's near edge is parallel to the flank",
      `corner ${C[0]}, ${C[1]}; inset ${r1(-b.dx)} px units; rectified z ${r1(t.z)} vs bottom corner z ${r1(tb.z)} (rake ${r1(tb.z - t.z)} px units back over ${r1(t.y - tb.y)} up)`);
    put("window.front.topAt", (zFC - t.z) / Lb, "L",
      "the same top-near corner's z from the nose (the windshield rakes back from its lower edge at cab.start)",
      `corner ${C[0]}, ${C[1]} -> z ${r1(t.z)}; nose z ${r1(zFC)}; L ${r1(Lb)}`);
  } else {
    for (const k of ["window.front.w", "window.front.bottom", "window.front.top", "window.front.topAt"]) {
      keys[k] = { unverified: true, unit: k.endsWith(".w") ? "W" : (k.endsWith("At") ? "L" : "H"), reason: `found ${glass.length} glass component(s) >= 500 px; need windshield + side window` };
    }
  }

  // Headlights: lamp px rectified on the nose plane z = lamp z; a round lamp is a disc there.
  {
    const per = lamps.map((c) => {
      const dxs = [], ys = [];
      for (const p of c.pts) { const r = onZPlane(p, lampPair.z); dxs.push(r.dx); ys.push(r.y); }
      const a = span(dxs), b = span(ys);
      return { n: c.n, w: a.hi - a.lo, h: b.hi - b.lo, dArea: 2 * Math.sqrt(c.n / (Math.abs(eX[0] * eY[1]) * Math.PI)) };
    });
    const d = per.reduce((s, l) => s + l.dArea, 0) / per.length;
    put("headlight.diameter", d / W, "W",
      "each lamp's px rectified onto the nose plane (z = the lamp pair's z): equal-area disc diameter 2 sqrt(A / pi), mean of the pair",
      per.map((l) => `${l.n} px -> d ${r1(l.dArea)} (w ${r1(l.w)}, h ${r1(l.h)})`).join("; ") + ` px units; W ${r1(W)}`);
  }

  // Grille: the recessed slot px between the two lamps, rectified on the nose plane.
  {
    const slots = components(img, cls, [L("grille")], 20, true)
      .filter((c) => c.cx > lamps[0].cx && c.cx < lamps[1].cx && c.cy > Math.min(lamps[0].y0, lamps[1].y0) - 60 && c.cy < Math.max(lamps[0].y1, lamps[1].y1) + 60);
    if (slots.length === 0) {
      keys["grille.w"] = { unverified: true, unit: "W", reason: "no grille-zone component between the lamps" };
      keys["grille.h"] = { unverified: true, unit: "H", reason: "no grille-zone component between the lamps" };
      keys["grille.slots"] = { unverified: true, unit: "count", reason: "no grille-zone component between the lamps" };
    } else {
      const dxs = [], ys = [];
      for (const c of slots) for (const p of c.pts) { const r = onZPlane(p, lampPair.z); dxs.push(r.dx); ys.push(r.y); }
      const a = span(dxs), b = span(ys);
      const ev = `${slots.length} slot component(s), ${slots.reduce((s, c) => s + c.n, 0)} px, boxes ${slots.map((c) => `${c.x0},${c.y0}..${c.x1},${c.y1}`).join(" / ")}`;
      const scan = "the grille slot px between the lamps rectified onto the nose plane (1..99th percentile): the extent of the slot field, the ink frame around it not included";
      put("grille.w", (a.hi - a.lo) / W, "W", scan, `${ev}; w ${r1(a.hi - a.lo)} px units`);
      put("grille.h", (b.hi - b.lo) / H, "H", scan, `${ev}; h ${r1(b.hi - b.lo)} px units`);
      // WF-BLIND-R2 C12 — the slot COUNT is a measurement too: each recessed slot is its own grille-zone component.
      put("grille.slots", slots.length, "count",
        "recessed grille slots: separate grille-zone components (>= 20 px) between the two lamps, split by the lit slat between them",
        ev);
      // V5-3 — each slot's own height (the slats between them are the rest of grille.h)
      const hs = slots.map((c) => { const ys0 = c.pts.map((p) => onZPlane(p, lampPair.z).y); const q = span(ys0); return q.hi - q.lo; });
      put("grille.slotH", median(hs) / H, "H", "each grille slot component rectified onto the nose plane (1..99th percentile height), median: the slat between slots is (grille.h - slots x slotH) / (slots - 1)",
        `${hs.map((h) => r1(h)).join(" / ")} px units; H ${r1(H)}`);
    }
  }

  // Mirror heads: the largest component of each mirror group, rectified on a z = const plane (the head's face
  // spans X and Y: its top edge runs along the eX slope in the target). Reach off the flank from the pair.
  if (mirrorPair) {
    const heads = mirrors.map((g) => g.comps.reduce((a, c) => (c.n > a.n ? c : a)));
    const per = heads.map((c) => {
      const dxs = [], ys = [];
      for (const p of c.pts) { const r = onZPlane(p, 0); dxs.push(r.dx); ys.push(r.y); }
      const a = span(dxs), b = span(ys);
      return { n: c.n, w: a.hi - a.lo, h: b.hi - b.lo, box: `${c.x0},${c.y0}..${c.x1},${c.y1}` };
    });
    const near = per[per.length - 1];
    // V5-3 — the heads' own z (the group centroid includes the raked arm): the head pair's midpoint on the centre plane
    const headPair = pair(heads[0], heads[heads.length - 1]);
    put("mirror.at", (zFC - headPair.z) / Lb, "L", "the mirror HEADS (largest component of each mirror group) as a mirrored pair: their midpoint rectified on the centre plane, z from the nose (the head's z; the arm runs from there to the door)",
      `far ${px([headPair.far.cx, headPair.far.cy])}, near ${px([headPair.near.cx, headPair.near.cy])}; pair slope ${r3(headPair.slope)}; z ${r1(headPair.z)} vs nose ${r1(zFC)}`);
    const scan = "the NEAR mirror head (largest mirror-zone component of the near group) rectified on a z = const plane, 1..99th percentile; the far head is cross-check only (it is foreshortened behind the cab)";
    const ev = per.map((m) => `${m.n} px box ${m.box}: w ${r1(m.w)}, h ${r1(m.h)}`).join("; ") + " px units";
    put("mirror.head.w", near.w / W, "W", scan, `${ev}; W ${r1(W)}`);
    put("mirror.head.h", near.h / H, "H", scan, `${ev}; H ${r1(H)}`);
    putList("mirror.offsetX", [-mirrorPair.halfDx / W, mirrorPair.halfDx / W], "W",
      "half the mirror-pair separation along eX, from the centre plane (the head centres)", `${r1(mirrorPair.halfDx)} / ${r1(W)} px units`);
    const arm = mirrorPair.halfDx - W / 2 - near.w / 2;
    if (arm > 0) {
      put("mirror.arm.length", arm / W, "W",
        "reach of the head's inner edge off the flank plane: pair half-separation - W/2 - head w/2 (the arm runs along X)",
        `${r1(mirrorPair.halfDx)} - ${r1(W / 2)} - ${r1(near.w / 2)} = ${r1(arm)} px units`);
    } else {
      keys["mirror.arm.length"] = {
        unverified: true, unit: "W",
        reason: `the head's inner edge rectifies ${r1(-arm)} px units INSIDE the flank plane (the cab tapers above the belt), so the arm length is not resolvable from this still`,
      };
    }
  } else {
    for (const [k, u] of [["mirror.head.w", "W"], ["mirror.head.h", "H"], ["mirror.offsetX", "W"], ["mirror.arm.length", "W"]]) {
      keys[k] = { unverified: true, unit: u, reason: `found ${mirrors.length} mirror group(s), need a pair` };
    }
  }

  keys["chassis.clearance"] = {
    unverified: true, unit: "H",
    reason: "the chassis underside is hidden under the body and bumpers at this elevation; VEH_GROUND still enforces limits.v7.ground_clearance",
  };

  const frame = {
    origin: px(O),
    camera: `theta ${camera.theta_deg} deg, phi ${camera.phi_deg} deg, mX ${camera.slopes?.mX}, mZ ${camera.slopes?.mZ}`,
    Lpx: r1(Lb), Wpx: r1(W), Hpx: r1(H),
    ground: `front wheel ${r1(groundF)}, rear wheel ${r1(groundR)} px units below the front centre`,
    quadPx: [toPx(0, zFC, yG + H), toPx(0, zRC, yG + H), toPx(0, zRC, yG), toPx(0, zFC, yG)].map(([x, y]) => [r1(x), r1(y)]),
    note: "quadPx = the flank (+X face) from the front corner edge to the rear corner edge, ground to roof height, order [top-front, top-rear, bottom-rear, bottom-front]; the render quad is the +X face of classes/vehicle.json likeness.faceRoles",
  };
  const marks = [O, wheelR.centre, topPx, [frontCorner.xTop, frontCorner.yTop], [rearCorner.xTop, rearCorner.yTop], [cabRearX, slotY], [bedFrontX, slotY], [edgeX, edgeTop], [lampPair.far.cx, lampPair.far.cy], [lampPair.near.cx, lampPair.near.cy], ...frame.quadPx];
  // WF-R5 R5-A — the rectification context scripts/measure-profile.mjs builds the profiles on (not serialised).
  const geo = { wsTopW, roofDx, bumperRear, bumperFront, O, eX, eY, eZ, sT, cT, sP, cP, rect, toPx, onZPlane, yG, zFC, zRC, Lb, W, H, cls, L, labelAt, isInk, chains, tyres, wheelF, wheelR, lampPair, rearBumperComps, frontCorner, rearCorner, doorFront, sideWindow, bodyMaxX, slotY, cabRearX, bedFrontX };
  return { keys, frame, zones, marks, img, geo };
}

// ---------------------------------------------------------------------------
// V4-7 — the BUS variant (classes/vehicle.json variants.bus): a flat-nosed box body, no hood, no bed; the whole
// body is role cab. Same frame and rectification as the pickup (O = front wheel centre, eX / eY / eZ from the solved
// camera), different landmarks, because the target's black paint (bumpers, window band, pillars, mirrors) is the
// same colour as its drawn lines: ink CHAINS cannot tell an edge from a black panel, so edges come from LABEL RUNS
// walked along rectified lines (flank plane, nose plane) and from CREASES (a drawn line on the paint: luma under
// BUS_SCAN.crease x the surrounding paint), and black parts from an OPENING of the black mask (lines stripped,
// solid blobs kept). Rounded vertical front corners are read as a chamfer: the nose face ends on one crease, the
// flank starts on the next, and the box corner (the frame L and W are measured to) lies between them.
// ---------------------------------------------------------------------------

/** Unratified instrument thresholds of the bus variant — about the target's pixels, never about the bus. */
export const BUS_SCAN = Object.freeze({
  hubMinPx: 300,         // a grey hub disc smaller than this is not a near wheel
  lampMinPx: 150,        // headlight lens
  lensMinPx: 20,         // marker / turn lens
  paneMinPx: 150,        // a glass component smaller than this is a sliver, not a pane
  crease: 0.8,           // a drawn line on paint: luma under this share of the paint's median luma
  gapMax: 8,             // px units of drawn line between two paint runs that still meet at one edge
  runMin: 3,             // px units: a label run shorter than this is a line / antialiasing, not an area
  step: 0.5,             // px units per walk step
  openR: 3,              // opening radius (px) that strips drawn lines off the black mask, keeping solid blobs
  blobMinPx: 150,        // an opened black blob smaller than this is not a part
  pairSlopeTol: 0.06,    // |slope - mX| for two blobs to be a mirrored pair (their displacement runs along eX)
});

/** Separable square min / max filter of radius r over a 0/1 mask. */
function filterMask(src, w, h, r, isMin) {
  const tmp = new Uint8Array(w * h);
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let v = isMin ? 1 : 0;
      for (let d = -r; d <= r; d += 1) { const xx = x + d; const s = xx < 0 || xx >= w ? 0 : src[y * w + xx]; if (isMin ? s < v : s > v) v = s; }
      tmp[y * w + x] = v;
    }
  }
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let v = isMin ? 1 : 0;
      for (let d = -r; d <= r; d += 1) { const yy = y + d; const s = yy < 0 || yy >= h ? 0 : tmp[yy * w + x]; if (isMin ? s < v : s > v) v = s; }
      out[y * w + x] = v;
    }
  }
  return out;
}

/** Label runs along a walk t0..t1 (step dt): [{label, a, b}] with a..b in walk units. */
function runsAlong(fn, t0, t1, dt) {
  const out = [];
  for (let t = t0; dt > 0 ? t <= t1 + 1e-9 : t >= t1 - 1e-9; t += dt) {
    const l = fn(t);
    const last = out[out.length - 1];
    if (last && last.label === l) last.b = t; else out.push({ label: l, a: t, b: t });
  }
  return out;
}

/**
 * Deterministic seed-grown sampling patches (regions.json) from STRUCTURAL seeds (regions.seeds.json): per seed, the
 * 4-connected component of px within `uniform` (max channel) of the seed's 3x3 median, inside `reach` px; the largest
 * square window (sizes, largest first) wholly inside it, nearest the seed. Returns the regions object.
 */
export function placeRegions(img, seeds, { uniform = 12, reach = 60, sizes = [30, 20, 16, 12, 10, 8, 6, 5, 4, 3] } = {}) {
  const zones = {};
  const within = (p, c) => Math.max(...p.map((v, k) => Math.abs(v - c[k]))) <= uniform;
  for (const [name, z] of Object.entries(seeds.zones)) {
    const rects = [];
    for (const [sx, sy] of z.seeds) {
      const ring = [];
      for (let j = -1; j <= 1; j += 1) for (let i = -1; i <= 1; i += 1) ring.push(at(img, sx + i, sy + j));
      const c = [0, 1, 2].map((k) => median(ring.map((p) => p[k])));
      const inside = new Uint8Array(img.w * img.h);
      const stack = [[sx, sy]];
      inside[sy * img.w + sx] = 1;
      while (stack.length) {
        const [x, y] = stack.pop();
        for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) {
          if (nx < 0 || ny < 0 || nx >= img.w || ny >= img.h || Math.abs(nx - sx) > reach || Math.abs(ny - sy) > reach) continue;
          const k = ny * img.w + nx;
          if (inside[k] || !within(at(img, nx, ny), c)) continue;
          inside[k] = 1;
          stack.push([nx, ny]);
        }
      }
      let best = null;
      for (const s of sizes) {
        const fits = [];
        for (let y = Math.max(0, sy - reach); y <= Math.min(img.h - s, sy + reach - s + 1); y += 1) {
          for (let x = Math.max(0, sx - reach); x <= Math.min(img.w - s, sx + reach - s + 1); x += 1) {
            let ok = true;
            for (let j = 0; j < s && ok; j += 1) for (let i = 0; i < s && ok; i += 1) if (!inside[(y + j) * img.w + x + i]) ok = false;
            if (ok) fits.push([x, y, (x + s / 2 - sx) ** 2 + (y + s / 2 - sy) ** 2]);
          }
        }
        if (fits.length) { const [x, y] = fits.sort((a, b) => a[2] - b[2] || a[1] - b[1] || a[0] - b[0])[0]; best = [x, y, s, s]; break; }
      }
      if (!best) throw new Error(`placeRegions: seed ${sx},${sy} of zone ${name} has no uniform ${sizes[sizes.length - 1]} px window`);
      rects.push(best);
    }
    zones[name] = { role: z.role, ...(z.face ? { face: z.face } : {}), rects, note: z.note };
  }
  return zones;
}

async function measureBus({ targetFile, regionsFile, cameraFile }) {
  const B = BUS_SCAN;
  const img = await readImage(targetFile);
  const regions = JSON.parse(fs.readFileSync(regionsFile, "utf8"));
  const camera = JSON.parse(fs.readFileSync(cameraFile, "utf8"));
  if (camera.provisional !== false) throw new Error(`${cameraFile} is provisional — solve the camera first`);
  const th = (camera.theta_deg * Math.PI) / 180;
  const ph = (camera.phi_deg * Math.PI) / 180;
  const sT = Math.sin(th), cT = Math.cos(th), sP = Math.sin(ph), cP = Math.cos(ph);
  const eX = [cP, sT * sP], eZ = [-sP, sT * cP], eY = [0, -cT];
  const mX = eX[1] / eX[0];

  const zones = zoneMedians(img, regions);
  const cls = classify(img, zones, regions.areaTolerance ?? 32);
  const need = (name) => { const k = cls.idx(name); if (k < 0) throw new Error(`regions.json has no zone "${name}" (bus variant, classes/vehicle.json variants.bus.zones)`); return k; };
  const L = (name) => cls.idx(name);
  const Z = { side: need("body_side"), front: need("body_front"), roof: need("roof"), glass: need("glass"), tyre: need("tyre"), black: need("black"), hub: need("hub"), lamp: need("headlight") };
  const DARK = new Set([Z.tyre, Z.black]);
  const BODY = new Set([Z.side, Z.front]);
  const inImg = (x, y) => x >= 0 && y >= 0 && x < img.w && y < img.h;
  const isBg = (x, y) => !inImg(Math.round(x), Math.round(y)) || Math.min(...at(img, Math.round(x), Math.round(y))) >= SCAN.nonWhite;
  const labelAt = (x, y) => (inImg(Math.round(x), Math.round(y)) ? cls.label[Math.round(y) * img.w + Math.round(x)] : 255);
  /** walk label: "bg", a zone index, or -1 (fg with no zone: a drawn line, antialiasing) */
  const walkLabel = (p) => (isBg(p[0], p[1]) ? "bg" : (labelAt(p[0], p[1]) === 255 ? -1 : labelAt(p[0], p[1])));
  /** the walk label by MATERIAL: the two body tones are one paint ("body"), the two blacks one ("dark") */
  const walkClass = (p) => { const l = walkLabel(p); return BODY.has(l) ? "body" : DARK.has(l) ? "dark" : l; };
  /** runs of at least runMin (walk units, either direction), equal neighbours merged */
  const solid = (runs) => {
    const out = [];
    for (const r of runs.filter((x) => Math.abs(x.b - x.a) + B.step >= B.runMin)) {
      const last = out[out.length - 1];
      if (last && last.label === r.label) last.b = r.b; else out.push({ ...r });
    }
    return out;
  };
  const lumAt = (x, y) => (inImg(Math.round(x), Math.round(y)) ? lum(at(img, Math.round(x), Math.round(y))) : 255);
  const isInk = (x, y) => inImg(Math.round(x), Math.round(y)) && lum(at(img, Math.round(x), Math.round(y))) < SCAN.inkLum;
  const q = (values, f) => { const v = [...values].sort((a, b) => a - b); return v[Math.min(v.length - 1, Math.max(0, Math.round(f * (v.length - 1))))]; };
  const span = (values) => ({ lo: q(values, 0.01), hi: q(values, 0.99) });
  const px = (p) => `${r1(p[0])}, ${r1(p[1])}`;

  // ---- wheels: the grey hub discs, then tyre rays (black) over the lower arc -----------------------------
  const hubs = components(img, cls, [Z.hub], B.hubMinPx).sort((a, b) => b.n - a.n).slice(0, 2).sort((a, b) => a.cx - b.cx);
  if (hubs.length < 2) throw new Error(`found ${hubs.length} hub disc(s) >= ${B.hubMinPx} px; need the two near wheels`);
  const wheelFit = (hub) => {
    let centre = [hub.cx, hub.cy];
    let fit = null;
    let rays = 0;
    for (let iter = 0; iter < 2; iter += 1) {
      const pts = [];
      for (let a = SCAN.rayFrom; a <= SCAN.rayTo; a += SCAN.rayStep) {
        const dz = Math.cos((a * Math.PI) / 180), dy = Math.sin((a * Math.PI) / 180);
        const v = [dz * eZ[0] + dy * eY[0], dz * eZ[1] + dy * eY[1]];
        let last = 0;
        for (let s = 0; s <= SCAN.rayMax; s += 0.25) {
          if (DARK.has(labelAt(centre[0] + s * v[0], centre[1] + s * v[1]))) last = s;
          else if (last > 0 && s - last > SCAN.rayLeave) break;
        }
        if (last > 0) pts.push([last * dz, last * dy]);
      }
      fit = fitCircle(pts);
      rays = pts.length;
      centre = [centre[0] + fit.cx * eZ[0] + fit.cy * eY[0], centre[1] + fit.cx * eZ[1] + fit.cy * eY[1]];
    }
    return { centre, r: fit.r, rms: fit.rms, rays, hub };
  };
  const wheelF = wheelFit(hubs[0]);
  const wheelR = wheelFit(hubs[1]);
  const O = wheelF.centre;
  const toPx = (dx, z, y) => [O[0] + dx * eX[0] + z * eZ[0], O[1] + dx * eX[1] + z * eZ[1] + y * eY[1]];
  const rect = (p, dx = 0) => {
    const z = (O[0] + dx * eX[0] - p[0]) / sP;
    const y = (O[1] + dx * eX[1] + z * eZ[1] - p[1]) / cT;
    return { z, y };
  };
  const onZPlane = (p, zPlane) => {
    const dx = (p[0] - O[0] - zPlane * eZ[0]) / eX[0];
    const y = (p[1] - O[1] - dx * eX[1] - zPlane * eZ[1]) / eY[1];
    return { dx, y };
  };
  const rearC = rect(wheelR.centre);
  const groundF = -wheelF.r;
  const groundR = rearC.y - wheelR.r;
  const yG = (groundF + groundR) / 2;

  // ---- headlights (the lamp pair) -------------------------------------------------------------------------
  const lamps = components(img, cls, [Z.lamp], B.lampMinPx, true).sort((a, b) => b.n - a.n).slice(0, 2).sort((a, b) => a.cx - b.cx);
  if (lamps.length < 2) throw new Error("fewer than two headlight components");
  const [farLamp, nearLamp] = lamps;

  // ---- the front corner: two creases right of the near lamp (nose face | corner | flank) ------------------
  const creaseRows = [];
  for (let y = nearLamp.y0; y <= nearLamp.y1; y += 1) {
    let x = nearLamp.x1 + 1;
    for (let k = 0; k < 12 && !BODY.has(labelAt(x, y)); k += 1) x += 1;
    const row = [];
    let darkRun = 0;
    for (; x < img.w; x += 1) {
      if (isBg(x, y)) break;
      darkRun = DARK.has(labelAt(x, y)) ? darkRun + 1 : 0;
      if (darkRun >= B.runMin) break;                        // the tyre (or a bumper) ends the corner
      row.push([x, lumAt(x, y), labelAt(x, y)]);
    }
    const paint = row.filter((c) => BODY.has(c[2])).map((c) => c[1]);
    if (paint.length < 10) continue;
    const base = median(paint);
    const runs = [];
    for (const [cx, l] of row) {
      if (!(l < B.crease * base)) continue;
      const last = runs[runs.length - 1];
      if (last && cx === last.b + 1) last.b = cx; else runs.push({ a: cx, b: cx });
    }
    const lines = runs.filter((r) => r.b - r.a <= 6).map((r) => (r.a + r.b) / 2);
    if (lines.length >= 1) creaseRows.push(lines.slice(0, 2));
  }
  const twoLine = creaseRows.filter((l) => l.length === 2);
  if (creaseRows.length === 0) throw new Error("no crease right of the near headlight (the nose face's near edge)");
  const xn = median(creaseRows.map((l) => l[0]));
  const rounded = twoLine.length >= 3;
  const xf = rounded ? median(twoLine.map((l) => l[1])) : xn;
  const rC = Math.max(0, xf - xn) / (cP + sP);                  // the corner chamfer, px units along X and Z
  const zN = rect([xf, 0]).z + rC;                                // the box nose on the flank frame

  // ---- nose-left: the silhouette edge on the far lamp's rows -----------------------------------------------
  const leftRows = [];
  for (let y = farLamp.y0; y <= farLamp.y1; y += 1) {
    let x0 = -1;
    for (let x = 0; x < farLamp.x0; x += 1) if (!isBg(x, y)) { x0 = x; break; }
    if (x0 < 0) continue;
    let xb = -1;
    for (let x = x0; x < Math.min(farLamp.x0, x0 + 12); x += 1) if (BODY.has(labelAt(x, y))) { xb = x; break; }
    if (xb >= 0) leftRows.push((x0 + xb - 1) / 2);
  }
  if (leftRows.length === 0) throw new Error("no nose-left silhouette edge on the far headlight's rows");
  const xl = median(leftRows);
  const XnBox = xf - rC * sP;
  const XfBox = xl - rC * Math.min(cP, sP);
  const Wpx = (XnBox - XfBox) / cP;

  // ---- tail: the flank rear corner (the rightmost flank paint, its drawn edge) ----------------------------
  const chains = inkChains(img);
  let bodyMaxX = -1;
  for (let i = 0; i < cls.label.length; i += 1) if (BODY.has(cls.label[i]) && i % img.w > bodyMaxX) bodyMaxX = i % img.w;
  const rearCorner = longest(chains.filter((c) => c.xMean >= bodyMaxX - 2 && c.xMean <= bodyMaxX + 6));
  const xR = rearCorner ? rearCorner.xMean : bodyMaxX + 0.5;
  const zRC = rect([xR, 0]).z;
  const Lpx = zN - zRC;
  const zOf = (u) => zN - u * Lpx;

  // ---- flank top: flank paint -> drawn line -> roof paint, walked up the flank plane --------------------
  const sideRuns = (u, v0, v1) => solid(runsAlong((v) => walkClass(toPx(0, zOf(u), yG + v)), v0, v1, B.step));
  /** edges where solid run `from` is followed (within gapMax) by solid run `to` */
  const edges = (runs, from, to) => {
    const out = [];
    for (let i = 0; i + 1 < runs.length; i += 1) if (from(runs[i].label) && to(runs[i + 1].label) && runs[i + 1].a - runs[i].b <= B.gapMax) out.push((runs[i].b + runs[i + 1].a) / 2);
    return out;
  };
  const tops = [];
  for (let u = 0.3; u <= 0.95 + 1e-9; u += 0.01) {
    const e = edges(sideRuns(u, 0, 1.2 * Lpx), (l) => l === "body", (l) => l === Z.roof);
    if (e.length) tops.push(e[e.length - 1]);
  }
  if (tops.length < 5) throw new Error(`the flank top (flank paint under roof paint) was found on ${tops.length} columns`);
  const Hpx = median(tops);
  const H = Hpx, W = Wpx, Lb = Lpx;

  // silhouette top = the roof's far-rear corner: rectified at (dx = -W, z = the tail) it gives the box height it implies
  let topY = -1;
  const topXs = [];
  for (let y = 0; y < img.h && topY < 0; y += 1) for (let x = 0; x < img.w; x += 1) if (!isBg(x, y)) { topY = y; break; }
  for (let x = 0; x < img.w; x += 1) if (!isBg(x, topY) || !isBg(x, topY + 1)) topXs.push(x);
  const topPx = [median(topXs), topY + 0.5];
  const silH = (O[1] - W * eX[1] + zRC * eZ[1] - topPx[1]) / cT - yG;

  // ---- keys ---------------------------------------------------------------------------------------------
  const keys = {};
  const put = (k, value, unit, scan, pxText) => { keys[k] = { value: r3(value), unit, evidence: { scan, px: pxText } }; };
  const putList = (k, values, unit, scan, pxText) => { keys[k] = { values: values.map(r3), unit, evidence: { scan, px: pxText } }; };
  const unverified = (k, unit, reason) => { keys[k] = { unverified: true, unit, reason }; };

  put("wheel.diameterOverL", (wheelF.r + wheelR.r) / Lb, "L",
    "grey hub discs locate the near wheels; black-label rays over the lower arc (200..340 deg, rectified onto the flank plane), Kasa circle fit per wheel, DIAMETER over body length",
    `r ${r1(wheelF.r)} / ${r1(wheelR.r)} px units (rms ${r1(wheelF.rms)} / ${r1(wheelR.rms)}, ${wheelF.rays} / ${wheelR.rays} rays); L ${r1(Lb)}`);
  putList("wheel.centreFromFront", [zN / Lb, (zN - rearC.z) / Lb], "L",
    "wheel centres (circle fits) along the flank from the box nose (the chamfered front corner's box edge)",
    `front ${px(wheelF.centre)}, rear ${px(wheelR.centre)}; nose z ${r1(zN)}`);
  put("wheelbase.overL", -rearC.z / Lb, "L", "rectified z between the two wheel centres over body length", `${r1(-rearC.z)} / ${r1(Lb)} px units`);
  unverified("wheel.farSide", "count/geometry", "the two -X wheels are hidden behind the body at this camera; census.json counts 4 wheels on 2 axles, VEH_MIRROR places them");
  put("height.overL", H / Lb, "x L",
    "flank top = the edge between flank paint (body_side) and roof paint (roof) walking up the flank plane, median over u 0.30..0.95 L; H over the ground line both wheel fits agree on",
    `${tops.length} columns, H ${r1(H)}; ground residual front/rear ${r1(Math.abs(groundF - groundR))} px units; L ${r1(Lb)}; silhouette top ${px(topPx)} rectified at (-W, tail) implies ${r1(silH)} (the roof's rounded far edges sit ${r1(H - silH)} below the box corner)`);
  put("width.overL", W / Lb, "x L",
    "box width between the nose-left silhouette edge (far lamp rows) and the near box corner (between the nose crease and the flank crease right of the near lamp), each corrected by the chamfer",
    `nose-left ${r1(xl)} (${leftRows.length} rows); creases ${r1(xn)} / ${r1(xf)} (${creaseRows.length} rows, ${twoLine.length} with two) -> chamfer ${r1(rC)}; W ${r1(W)}`);
  put("cab.start", 0, "L", "bus variant: one body, role cab, from the box nose (0 by construction)", `nose z ${r1(zN)}`);
  put("cab.end", 1, "L", "bus variant: the cab runs to the flank rear corner edge; L is measured to it (1 by construction)", rearCorner ? chainPx(rearCorner) : `rightmost flank px x ${bodyMaxX}`);
  put("cab.roof", 1, "H", "the flank top IS the model top (the roof is flat; no body px rectifies above it on the flank plane): cab max y / model max y = 1", `H ${r1(H)}`);

  // ---- nose plane: headlights (pair), windshield panes, bumper, marker + turn lenses ----------------------
  const onNose = (p) => { const r = onZPlane(p, zN); return { x: (r.dx + W / 2) / W, y: (r.y - yG) / H }; };   // x from the centre plane (W), y (H)
  const pair = (far, near) => {
    const dxPx = near.cx - far.cx;
    const mid = [(near.cx + far.cx) / 2, (near.cy + far.cy) / 2];
    const p = rect(mid, -W / 2);
    return { slope: (near.cy - far.cy) / dxPx, halfDx: dxPx / (2 * cP), y: p.y, z: p.z, far, near };
  };
  const lampPair = pair(farLamp, nearLamp);
  put("headlight.centreY", (lampPair.y - yG) / H, "H", "lamp pair: centroids share y and z, midpoint rectified on the centre plane dx = -W/2",
    `far ${px([farLamp.cx, farLamp.cy])}, near ${px([nearLamp.cx, nearLamp.cy])}; pair slope ${r3(lampPair.slope)} vs mX ${r3(mX)}; lamp z ${r1(lampPair.z)} vs nose ${r1(zN)}`);
  putList("headlight.offsetX", [-lampPair.halfDx / W, lampPair.halfDx / W], "W", "half the lamp-pair separation along eX, from the centre plane", `${r1(lampPair.halfDx)} / ${r1(W)} px units`);
  {
    const per = lamps.map((c) => ({ n: c.n, d: 2 * Math.sqrt(c.n / (Math.abs(eX[0] * eY[1]) * Math.PI)) }));
    put("headlight.diameter", per.reduce((s, l) => s + l.d, 0) / per.length / W, "W",
      "each lamp's px on the nose plane: equal-area disc diameter 2 sqrt(A / pi) (A over the nose plane's px-per-unit-area), mean of the pair",
      per.map((l) => `${l.n} px -> d ${r1(l.d)}`).join("; ") + ` px units; W ${r1(W)}`);
  }
  // windshield: the glass components left of the nose crease (on the nose plane)
  const noseGlass = components(img, cls, [Z.glass], B.paneMinPx, true).filter((c) => c.cx < xn).sort((a, b) => a.cx - b.cx);
  if (noseGlass.length > 0) {
    const all = noseGlass.flatMap((c) => c.pts.map(onNose));
    const xs = span(all.map((p) => p.x)), ys = span(all.map((p) => p.y));
    const ev = `${noseGlass.length} glass component(s) left of the nose crease x ${r1(xn)}: ${noseGlass.map((c) => `${c.n} px ${c.x0},${c.y0}..${c.x1},${c.y1}`).join(" / ")}`;
    const scan = "windshield glass px rectified onto the nose plane (z = the box nose), 1..99th percentile";
    put("window.front.panes", noseGlass.length, "count", "windshield panes: separate glass components on the nose plane (split by the black centre post)", ev);
    // the NEAR pane's outer edge crosses the nose crease onto the rounded corner (its px rectify off the nose plane),
    // so the span is twice the FAR outer edge's distance from the centre plane (the windshield is mirrored)
    const farOuter = -span(noseGlass[0].pts.map((p) => onNose(p).x)).lo;
    put("window.front.w", 2 * farOuter, "W", `${scan}: twice the far pane's outer edge from the centre plane (the near pane's outer edge wraps onto the rounded corner), centre post included`, `${ev}; all glass x ${r3(xs.lo)}..${r3(xs.hi)} W from the centre plane`);
    put("window.front.bottom", ys.lo, "H", `${scan}: lower edge above the ground`, ev);
    put("window.front.top", ys.hi, "H", `${scan}: upper edge above the ground`, ev);
    if (noseGlass.length === 2) {
      const [a, b] = noseGlass.map((c) => span(c.pts.map((p) => onNose(p).x)));
      put("window.front.post", b.lo - a.hi, "W", `${scan}: the gap between the two panes (the centre post)`, `far pane x ..${r3(a.hi)}, near pane x ${r3(b.lo)}..`);
    }
    put("window.front.topAt", 0, "L", "bus variant: the windshield lies in the nose plane (both its edges rectify on z = the box nose; no rake)", ev);
  } else for (const [k, u] of [["window.front.panes", "count"], ["window.front.w", "W"], ["window.front.bottom", "H"], ["window.front.top", "H"]]) unverified(k, u, "no glass component left of the nose crease");
  // front bumper: walked down the nose plane across the middle of the width, from the lamp line
  {
    const tops = [], bots = [];
    for (let f = -0.3; f <= 0.3 + 1e-9; f += 0.02) {
      const runs = solid(runsAlong((v) => walkClass(toPx(-W / 2 + f * W, zN, yG + v)), lampPair.y - yG, -0.1 * H, -B.step));
      const i = runs.findIndex((r) => r.label === "dark");
      if (i > 0 && runs[i - 1].label === "body" && runs[i - 1].b - runs[i].a <= B.gapMax) {
        tops.push((runs[i - 1].b + runs[i].a) / 2);
        if (runs[i + 1]?.label === "bg") bots.push((runs[i].b + runs[i + 1].a) / 2);
      }
    }
    if (tops.length >= 5) {
      put("bumper.front.top", median(tops) / H, "H", "nose paint -> black paint walking down the nose plane (x -0.3..0.3 W about the centre plane): the bumper's top-back edge", `${tops.length} columns`);
      if (bots.length >= 5) put("bumper.front.h", (median(tops) - median(bots)) / H, "H", "black run to the background under it on the same columns (the bumper's front face rectified on the nose plane: its depth past the nose reads as up to 0.38 x depth of extra height)", `${bots.length} columns`);
      else unverified("bumper.front.h", "H", "the black run under the nose does not end on the background");
    } else { unverified("bumper.front.top", "H", "no nose-paint -> black edge under the lamp line"); unverified("bumper.front.h", "H", "no nose-paint -> black edge under the lamp line"); }
  }
  // lenses: the signal (red) / amber components on the nose (the stop sign is the large signal component on the flank)
  const lens = (zone) => (L(zone) >= 0 ? components(img, cls, [L(zone)], B.lensMinPx, true) : []);
  const reds = lens("signal").sort((a, b) => b.n - a.n);
  const stop = reds.find((c) => c.x0 > xf) ?? null;
  const noseLens = [...reds.filter((c) => c !== stop), ...lens("amber"), ...lens("orange")].filter((c) => c.x1 < xf + 4);
  const wsTop = keys["window.front.top"]?.value ?? 0.5;
  const markers = noseLens.filter((c) => onNose([c.cx, c.cy]).y > wsTop).sort((a, b) => a.cx - b.cx);
  const turns = noseLens.filter((c) => onNose([c.cx, c.cy]).y < (lampPair.y - yG) / H).sort((a, b) => a.cx - b.cx);
  // mirrored lens PAIRS (screen order: the i-th from the left with the i-th from the right): each pair's midpoint
  // rectifies on the centre plane (its y AND its z: a lens set back on the curved front cap is not on the nose plane)
  const lensKeys = (name, list, what) => {
    const pairs = [];
    for (let i = 0; i < Math.floor(list.length / 2); i += 1) {
      const p = pair(list[i], list[list.length - 1 - i]);
      if (Math.abs(p.slope - mX) <= B.pairSlopeTol) pairs.push(p);
    }
    if (pairs.length === 0 || pairs.length * 2 !== list.length) { for (const [k, u] of [["count", "count"], ["centreY", "H"], ["at", "L"], ["offsetX", "W"], ["diameter", "W"]]) unverified(`${name}.${k}`, u, `${list.length} ${what} lens component(s) do not all pair across the centre plane along eX`); return; }
    const ev = pairs.map((p) => `${p.far.n} + ${p.near.n} px at ${px([p.far.cx, p.far.cy])} / ${px([p.near.cx, p.near.cy])}, slope ${r3(p.slope)}`).join("; ") + ` vs mX ${r3(mX)}`;
    const d = list.map((l) => 2 * Math.sqrt(l.n / (Math.abs(eX[0] * eY[1]) * Math.PI)) / W);
    put(`${name}.count`, list.length, "count", `${what} lenses: separate lens-colour components, in mirrored pairs`, ev);
    put(`${name}.centreY`, median(pairs.map((p) => (p.y - yG) / H)), "H", `${what} lens pairs: midpoints rectified on the centre plane, median height`, ev);
    put(`${name}.at`, median(pairs.map((p) => (zN - p.z) / Lb)), "L", `${what} lens pairs: the same midpoints' z from the box nose (set back on the front cap when > 0)`, ev);
    putList(`${name}.offsetX`, pairs.flatMap((p) => [-p.halfDx / W, p.halfDx / W]), "W", `${what} lens pairs: half the pair separation along eX, from the centre plane`, ev);
    put(`${name}.diameter`, median(d), "W", `${what} lens equal-area diameter on the nose plane, median`, ev);
  };
  lensKeys("marker", markers, "roof marker (above the windshield)");
  lensKeys("turn", turns, "turn (below the headlights)");

  // ---- flank: window band, the pane row, the stop arm ------------------------------------------------------
  const bandB = [], bandT = [];
  for (let u = 0.3; u <= 0.95 + 1e-9; u += 0.01) {
    const runs = sideRuns(u, 0, Hpx);
    const i = runs.findIndex((r, k) => k > 0 && (r.label === "dark" || r.label === Z.glass) && runs[k - 1].label === "body");
    if (i < 0) continue;
    let j = i;
    while (j + 1 < runs.length && (runs[j + 1].label === "dark" || runs[j + 1].label === Z.glass || runs[j + 1].label === -1)) j += 1;
    if (runs[j + 1]?.label !== "body") continue;
    bandB.push((runs[i - 1].b + runs[i].a) / 2);
    bandT.push((runs[j].b + runs[j + 1].a) / 2);
  }
  const bandOk = bandB.length >= 10;
  if (bandOk) {
    put("window.band.bottom", median(bandB) / H, "H", "flank paint -> black / glass walking up the flank plane (u 0.30..0.95): the window band's lower edge", `${bandB.length} columns`);
    put("window.band.top", median(bandT) / H, "H", "the last black / glass run before the flank paint above it: the window band's upper edge", `${bandT.length} columns`);
  } else { unverified("window.band.bottom", "H", `band edges found on ${bandB.length} columns`); unverified("window.band.top", "H", `band edges found on ${bandB.length} columns`); }
  if (bandOk) {
    const vMid = (median(bandB) + median(bandT)) / 2;
    const row = runsAlong((u) => walkLabel(toPx(0, zOf(u), yG + vMid)), 0, 1, 0.5 / Lb).filter((r) => r.label === Z.glass && (r.b - r.a) * Lb >= B.runMin);
    const panes = row.map((r) => {
      const uc = (r.a + r.b) / 2;
      const vr = runsAlong((v) => walkLabel(toPx(0, zOf(uc), yG + v)), median(bandB) - 0.1 * H, median(bandT) + 0.05 * H, B.step).filter((s) => s.label === Z.glass && s.a <= vMid && s.b >= vMid);
      return { a: r.a, b: r.b, w: r.b - r.a, c: uc, v0: vr[0]?.a ?? NaN, v1: vr[0]?.b ?? NaN };
    });
    const wMed = median(panes.map((p) => p.w));
    const reg = panes.filter((p) => Math.abs(p.w - wMed) <= 0.25 * wMed);
    const odd = panes.filter((p) => !reg.includes(p));
    const ev = `band mid ${r3(vMid / H)} H; ${panes.length} glass run(s) u ${panes.map((p) => `${r3(p.a)}..${r3(p.b)}`).join(", ")}`;
    if (reg.length >= 2) {
      const pitch = median(reg.slice(1).map((p, i) => p.c - reg[i].c));
      put("window.row.count", reg.length, "count", "side panes: glass runs along the band's mid line on the flank plane whose length is within 25 % of the median run (a pane split by an occluder or a door pane is not a row pane)", ev);
      put("window.row.start", reg[0].a, "L", "front edge of the first row pane from the nose (glass run on the band mid line)", ev);
      put("window.row.end", reg[reg.length - 1].b, "L", "rear edge of the last row pane", ev);
      put("window.row.pitch", pitch, "L", "median centre-to-centre spacing of the row panes", ev);
      put("window.row.paneW", median(reg.map((p) => p.w)), "L", "median row-pane length along the flank", ev);
      put("window.row.bottom", median(reg.map((p) => p.v0)) / H, "H", "median glass bottom of the row panes, walked up each pane's centre column on the flank plane", ev);
      put("window.row.top", median(reg.map((p) => p.v1)) / H, "H", "median glass top of the row panes", ev);
    } else for (const [k, u] of [["window.row.count", "count"], ["window.row.start", "L"], ["window.row.end", "L"], ["window.row.pitch", "L"], ["window.row.paneW", "L"], ["window.row.bottom", "H"], ["window.row.top", "H"]]) unverified(k, u, `found ${reg.length} regular pane(s) on the band mid line`);
    keys["window.door"] = odd.length
      ? { unverified: true, unit: "L", reason: `glass run(s) off the row pitch at u ${odd.map((p) => `${r3(p.a)}..${r3(p.b)}`).join(", ")} (the entrance-door pane behind the near mirror head): its extent is occluded, so it is not measured` }
      : { unverified: true, unit: "L", reason: "no glass run off the row pitch" };
  }
  if (stop) {
    const pts = stop.pts.map((p) => rect(p)), us = span(pts.map((p) => (zN - p.z) / Lb)), vs = span(pts.map((p) => (p.y - yG) / H));
    const ev = `${stop.n} px box ${stop.x0},${stop.y0}..${stop.x1},${stop.y1}`;
    const scan = "the stop sign = the largest red (signal) component right of the flank crease, rectified on the flank plane (it folds flat against the flank; an outboard offset of 0.05 W moves u by ~0.02)";
    put("stopArm.centreAt", (us.lo + us.hi) / 2, "L", scan, ev);
    put("stopArm.centreY", (vs.lo + vs.hi) / 2, "H", scan, ev);
    put("stopArm.diameter", 2 * Math.sqrt(stop.n / (Math.abs(eZ[0] * eY[1]) * Math.PI)) / Lb, "L", `${scan}: equal-area disc diameter over L`, ev);
  } else for (const [k, u] of [["stopArm.centreAt", "L"], ["stopArm.centreY", "H"], ["stopArm.diameter", "L"]]) unverified(k, u, "no red component on the flank");

  // ---- black blobs (lines stripped by an opening): mirror heads, rear bumper ---------------------------------
  const darkMask = new Uint8Array(img.w * img.h);
  for (let i = 0; i < darkMask.length; i += 1) darkMask[i] = DARK.has(cls.label[i]) ? 1 : 0;
  const opened = filterMask(filterMask(darkMask, img.w, img.h, B.openR, true), img.w, img.h, B.openR, false);
  const blobs = components(img, { label: opened }, [1], B.blobMinPx, true);
  const hubXs = [wheelF, wheelR].map((w) => w.centre);
  const isTyre = (b) => hubXs.some((c, i) => Math.hypot(b.cx - c[0], b.cy - c[1]) < 1.6 * [wheelF, wheelR][i].r);
  // mirrors: the far head sits left of the nose-left edge; its partner is the blob displaced from it along eX
  const farHeads = blobs.filter((b) => b.cx < xl && !isTyre(b)).sort((a, b) => b.n - a.n);
  let mirrorPair = null;
  if (farHeads.length) {
    const f = farHeads[0];
    const cand = blobs.filter((b) => b !== f && !isTyre(b) && b.cx > xn && Math.abs((b.cy - f.cy) / (b.cx - f.cx) - mX) <= B.pairSlopeTol && b.n > 0.4 * f.n && b.n < 2.5 * f.n);
    const near = cand.sort((a, b) => Math.abs((a.cy - f.cy) / (a.cx - f.cx) - mX) - Math.abs((b.cy - f.cy) / (b.cx - f.cx) - mX))[0];
    if (near) mirrorPair = pair(f, near);
  }
  if (mirrorPair) {
    const heads = [mirrorPair.far, mirrorPair.near].map((c) => {
      const pts = c.pts.map((p) => onZPlane(p, mirrorPair.z));
      const a = span(pts.map((p) => p.dx)), b = span(pts.map((p) => p.y));
      return { n: c.n, w: a.hi - a.lo, h: b.hi - b.lo, box: `${c.x0},${c.y0}..${c.x1},${c.y1}` };
    });
    const near = heads[1];
    const ev = heads.map((m) => `${m.n} px box ${m.box}: w ${r1(m.w)}, h ${r1(m.h)}`).join("; ") + ` px units; pair slope ${r3(mirrorPair.slope)} vs mX ${r3(mX)}`;
    const scan = "mirror heads = opened black blobs (drawn lines stripped): the far head left of the nose-left edge, its partner the blob displaced from it along eX; heads rectified on the pair's z plane, 1..99th percentile (the near head)";
    put("mirror.centreY", (mirrorPair.y - yG) / H, "H", "mirror pair centroids share y and z, midpoint rectified on the centre plane", ev);
    put("mirror.head.w", near.w / W, "W", scan, ev);
    put("mirror.head.h", near.h / H, "H", scan, ev);
    putList("mirror.offsetX", [-mirrorPair.halfDx / W, mirrorPair.halfDx / W], "W", "half the mirror-pair separation along eX, from the centre plane", `${r1(mirrorPair.halfDx)} / ${r1(W)} px units`);
    put("mirror.at", (zN - mirrorPair.z) / Lb, "L", "the pair's rectified z from the nose (negative = ahead of the nose: the heads stand on arms forward of the front corners)", ev);
    const arm = mirrorPair.halfDx - W / 2 - near.w / 2;
    if (arm > 0) put("mirror.arm.length", arm / W, "W", "pair half-separation - W/2 - head w/2 (the arm runs along X)", `${r1(mirrorPair.halfDx)} - ${r1(W / 2)} - ${r1(near.w / 2)} = ${r1(arm)} px units`);
    else unverified("mirror.arm.length", "W", `the head's inner edge rectifies ${r1(-arm)} px units inside the flank plane`);
  } else for (const [k, u] of [["mirror.centreY", "H"], ["mirror.head.w", "W"], ["mirror.head.h", "H"], ["mirror.offsetX", "W"], ["mirror.arm.length", "W"]]) unverified(k, u, `no mirrored pair of black blobs (${farHeads.length} far-head candidate(s))`);
  // rear bumper: the opened black blob right of the rear tyre; its +X face read at the flank rear corner column
  const rearBlob = blobs.filter((b) => b.x0 > wheelR.centre[0] + wheelR.r * 0.7 && !isTyre(b)).sort((a, b) => b.n - a.n)[0];
  if (rearBlob) {
    const col = solid(runsAlong((v) => walkClass(toPx(0, zRC + 0.02 * Lb, yG + v)), 0.6 * H, -0.05 * H, -B.step));
    const i = col.findIndex((r, k) => k > 0 && r.label === "dark" && col[k - 1].label === "body");
    if (i > 0 && col[i - 1].label === "body") {
      const top = (col[i - 1].b + col[i].a) / 2;
      const bot = col[i + 1] ? (col[i].b + col[i + 1].a) / 2 : col[i].b;
      put("bumper.rear.top", top / H, "H", "flank paint -> black walking down the flank plane 0.02 L ahead of the flank rear corner: the rear bumper's top edge", `blob ${rearBlob.n} px ${rearBlob.x0},${rearBlob.y0}..${rearBlob.x1},${rearBlob.y1}`);
      put("bumper.rear.h", (top - bot) / H, "H", "the black run's length on that column (its lower end on the background)", `blob ${rearBlob.x0},${rearBlob.y0}..${rearBlob.x1},${rearBlob.y1}`);
    } else { unverified("bumper.rear.top", "H", "no flank paint -> black edge at the flank rear corner"); unverified("bumper.rear.h", "H", "no flank paint -> black edge at the flank rear corner"); }
  } else { unverified("bumper.rear.top", "H", "no black blob right of the rear tyre"); unverified("bumper.rear.h", "H", "no black blob right of the rear tyre"); }
  unverified("chassis.clearance", "H", "the chassis underside is hidden under the body and bumpers at this elevation; VEH_GROUND still enforces limits.v7.ground_clearance");

  const frame = {
    origin: px(O),
    camera: `theta ${camera.theta_deg} deg, phi ${camera.phi_deg} deg, mX ${camera.slopes?.mX}, mZ ${camera.slopes?.mZ}`,
    variant: "bus",
    Lpx: r1(Lb), Wpx: r1(W), Hpx: r1(H),
    ground: `front wheel ${r1(groundF)}, rear wheel ${r1(groundR)} px units below the front centre`,
    quadPx: [toPx(0, zN, yG + H), toPx(0, zRC, yG + H), toPx(0, zRC, yG), toPx(0, zN, yG)].map(([x, y]) => [r1(x), r1(y)]),
    note: "quadPx = the +X face of the BOX body (the chamfered front corner extended to its box edge) from the nose to the flank rear corner edge, ground to roof height, order [top-front, top-rear, bottom-rear, bottom-front]",
  };
  const marks = [O, wheelR.centre, topPx, [xn, nearLamp.cy], [xf, nearLamp.cy], [xl, farLamp.cy], [xR, 0], ...frame.quadPx];
  const geo = { variant: "bus", O, eX, eY, eZ, sT, cT, sP, cP, mX, rect, toPx, onZPlane, yG, zN, zFC: zN, zRC, Lb, W, H, rC, cls, L, Z, DARK, BODY,
    labelAt, walkLabel, walkClass, solid, lumAt, isInk, isBg, runsAlong, edges, span, q, wheelF, wheelR, lamps, farLamp, nearLamp, xn, xf, xl, xR, topPx };
  return { keys, frame, zones, marks, img, geo };
}

// ---------------------------------------------------------------------------
// Files
// ---------------------------------------------------------------------------

const head = (S) => ({
  _comment: "GENERATED by scripts/measure-vehicle.mjs --freeze. Do not hand-edit: a layout key is a MEASUREMENT WITH EVIDENCE (WF-LOOP-R3 C1). Every value is a fraction in the AUTHOR frame of classes/vehicle.md: L = body length (z extent of chassis/body/cab/hood/bed/bed_wall/tailgate, measured from the NOSE at max z), W = body width (x extent), H = the model's height. Camera-free: a rescale or re-solve cannot move it. V12_LAYOUT (src/validate/rules/vehicle.mjs) measures these off part AABBs by role; a key whose role is not built yet is skipped, an `unverified` key is reported and never enforced.",
  _source: `scripts/measure-vehicle.mjs on ${S.rel.target} + ${S.rel.camera} + ${S.rel.regions}`,
  _units: "L / W / H as above; `x L` is a ratio to L. `tol` is FEATURE-RELATIVE: max(0.02, 0.15 x value), a list's tol from its smallest |member|.",
});

function tolOf(entry) {
  if (Array.isArray(entry.values)) return tolFor(Math.min(...entry.values.map(Math.abs)));
  return Number.isFinite(entry.value) ? tolFor(entry.value) : null;
}

export function freezeLayout(keys, frame, S) {
  const out = { ...head(S), _frame: frame };
  for (const [k, v] of Object.entries(keys)) {
    const tol = v.unverified ? null : tolOf(v);
    out[k] = tol === null ? { ...v } : { ...v, tol };
  }
  return out;
}

async function writeOverlay(file, result) {
  const { img, marks } = result;
  const data = Buffer.from(img.data);
  for (const [mx, my] of marks) {
    for (let d = -6; d <= 6; d += 1) {
      for (const [x, y] of [[Math.round(mx) + d, Math.round(my)], [Math.round(mx), Math.round(my) + d]]) {
        if (x < 0 || y < 0 || x >= img.w || y >= img.h) continue;
        const i = (y * img.w + x) * img.c;
        data[i] = 255; data[i + 1] = 0; data[i + 2] = 0;
      }
    }
  }
  await sharp(data, { raw: { width: img.w, height: img.h, channels: img.c } }).png().toFile(file);
}

function arg(argv, name, fallback) {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : fallback;
}

export async function main(argv = process.argv.slice(2)) {
  const S = loadSubject(subjectIdFromArgv(argv));
  const targetFile = path.resolve(ROOT, arg(argv, "--target", S.rel.target));
  const regionsFile = path.resolve(ROOT, arg(argv, "--regions", S.rel.regions));
  const cameraFile = path.resolve(ROOT, arg(argv, "--camera", S.rel.camera));
  const layoutFile = path.resolve(ROOT, arg(argv, "--layout", S.rel.layout));
  const outFile = path.resolve(ROOT, arg(argv, "--out", S.rel.layoutMeasured));

  // V4-7: regions.json from the subject's STRUCTURAL seeds (subject.json paths.regionSeeds), then stop.
  if (argv.includes("--place-regions")) {
    if (!S.rel.regionSeeds) throw new Error(`subjects/${S.id}/subject.json names no paths.regionSeeds`);
    const seeds = JSON.parse(fs.readFileSync(S.paths.regionSeeds, "utf8"));
    const img = await readImage(targetFile);
    const zonesOut = placeRegions(img, seeds);
    let x0 = img.w, y0 = img.h, x1 = -1, y1 = -1;
    for (let y = 0; y < img.h; y += 1) for (let x = 0; x < img.w; x += 1) {
      if (Math.min(...at(img, x, y)) >= SCAN.nonWhite) continue;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    const pad = 5;
    const box = [Math.max(0, x0 - pad), Math.max(0, y0 - pad), Math.min(img.w, x1 + pad + 1) - Math.max(0, x0 - pad), Math.min(img.h, y1 + pad + 1) - Math.max(0, y0 - pad)];
    const out = {
      _comment: `GENERATED by scripts/measure-vehicle.mjs --place-regions from ${S.rel.regionSeeds} (structural seeds; each rect = the largest uniform square window inside the seed's same-colour component, nearest the seed). Rects are [x, y, w, h], origin top-left. The zone medians are recomputed from the pixels every run. role = the vehicle-class role whose id-pass mask the zone is compared against; face marks the two flat body tones (front = the +X flank, side = the +Z nose).`,
      _source: S.rel.target,
      image: { w: img.w, h: img.h },
      _subjectBoxes_comment: "the non-white bounding box of the target plus 5 px (likeness / residual classifier extent)",
      subjectBoxes: [box],
      areaTolerance: 32,
      zones: zonesOut,
    };
    fs.writeFileSync(regionsFile, `${JSON.stringify(out, null, 2)}\n`);
    const med = zoneMedians(img, out);
    for (const [name, z] of Object.entries(med)) process.stdout.write(`  zone ${name.padEnd(12)} ${z.hex}  ${String(z.px).padStart(5)} px  purity ${z.purity.toFixed(3)}  rects ${JSON.stringify(out.zones[name].rects)}\n`);
    process.stdout.write(`wrote ${path.relative(ROOT, regionsFile)}\n`);
    return 0;
  }

  const result = await measureVehicle({ targetFile, regionsFile, cameraFile, variant: S.subject.variant ?? "pickup" });
  const { keys, frame, zones } = result;

  if (argv.includes("--json")) {
    process.stdout.write(`${JSON.stringify(keys, null, 2)}\n`);
  } else {
    process.stdout.write(`flank L ${frame.Lpx}, W ${frame.Wpx}, H ${frame.Hpx} px units; ${frame.ground}\n`);
    for (const [name, z] of Object.entries(zones)) {
      process.stdout.write(`  zone ${name.padEnd(12)} ${z.hex}  ${String(z.px).padStart(5)} px  purity ${z.purity.toFixed(3)}\n`);
    }
    for (const [k, v] of Object.entries(keys)) {
      const value = v.unverified ? "UNVERIFIED" : (Array.isArray(v.values) ? v.values.join(" / ") : v.value);
      process.stdout.write(`  ${k.padEnd(22)} ${String(value).padStart(14)} ${(v.unit ?? "").padEnd(8)} ${v.unverified ? v.reason : v.evidence.px}\n`);
    }
  }
  const overlay = arg(argv, "--overlay", null);
  if (overlay) await writeOverlay(path.resolve(overlay), result);

  if (!argv.includes("--check")) {
    const h = head(S);
    fs.writeFileSync(outFile, `${JSON.stringify({ ...h, _comment: `MEASURED, not frozen — --freeze copies it into layout.json. ${h._comment}`, _frame: frame, ...keys }, null, 2)}\n`);
  }
  if (argv.includes("--freeze")) {
    const prior = fs.existsSync(layoutFile) ? JSON.parse(fs.readFileSync(layoutFile, "utf8")) : {};
    const frozen = freezeLayout(keys, frame, S);
    if (prior._profile) frozen._profile = prior._profile;       // WF-R5: owned by scripts/measure-profile.mjs
    fs.writeFileSync(layoutFile, `${JSON.stringify(frozen, null, 2)}\n`);
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
  main().then((code) => { process.exitCode = code; }).catch((error) => { console.error(`measure-vehicle: ${error.message}`); process.exitCode = 2; });
}
