#!/usr/bin/env node
// WORKFLOW v4 — V4-1 item 3: NAMED RESIDUAL rows (research/WF-V4-PLAN.md "Residual rows").
//
//   node scripts/residuals.mjs --subject pickup --module <path.mjs> [--json <out.json>] [--rows N]
//
// Target vs projection in ONE registered frame (scripts/registered.mjs, target px): target zone masks
// (likeness classifyTargetPixels over regions.json, grouped by the class likeness.areaFamilies) against the
// projected parts (scripts/project.mjs, frame "target", each part's zone mapped through classes/<c>.json
// paletteZones to a region and its family). Every mismatched pixel is charged to a PART: excess pixels to the part
// drawn there, missing pixels to the nearest part of the pixel's family (chamfer label propagation), and split by
// the side of that part's screen box (top / bottom / front / rear; front = the side the class length axis points
// to on screen). Per part and axis the sides combine into EXCESS / DEFICIT / OFFSET (excess one side + deficit the
// other) / EXTENT (both sides the same way); target family blobs with no part of that family near them are
// MISSING; parts whose pixels land almost nowhere on their own family are EXTRA. Magnitudes are metres (mean band
// thickness / px per metre along the part-plane axis); rows under 0.5 x tol are suppressed; ranked by px area.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { ROOT, loadSubject } from "./subject.mjs";
import { classifyTargetPixels } from "./likeness.mjs";
import { project } from "./project.mjs";
import { OCCLUDED, iou, readRGB, targetState, turnFn } from "./registered.mjs";
import { maskOptions, subjectMaskRule } from "./v6/ortho.mjs";

/** tol = TOL_FRAC x the anchor's reference size (vehicle L, building H) — the layout's floor tolerance (0.02). */
export const TOL_FRAC = 0.02;
/** Target fg px with no zone (ink outline, AA) this close to the render are not charged. */
export const INK_PX = 4;
/** A band needs this many px to become a row. */
export const MIN_AREA = 40;
/** A family deficit further than this (x ref) from any part of that family is MISSING, not a part's DEFICIT. */
export const MISS_FRAC = 0.12;
/** A part whose px sit on its own family less than this share is EXTRA. */
export const EXTRA_SHARE = 0.1;

/** Opening radius (px) that strips ink strokes from the target zone masks. */
export const INK_OPEN = 2;

const SQ2 = Math.SQRT2;

/** Separable square min / max filter of radius r (erode = min). */
function filter1(src, w, h, r, isMin) {
  const tmp = new Uint8Array(w * h);
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let v = isMin ? 1 : 0;
      for (let d = -r; d <= r; d += 1) {
        const xx = x + d;
        const s = xx < 0 || xx >= w ? 0 : src[y * w + xx];
        if (isMin ? s < v : s > v) v = s;
      }
      tmp[y * w + x] = v;
    }
  }
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let v = isMin ? 1 : 0;
      for (let d = -r; d <= r; d += 1) {
        const yy = y + d;
        const s = yy < 0 || yy >= h ? 0 : tmp[yy * w + x];
        if (isMin ? s < v : s > v) v = s;
      }
      out[y * w + x] = v;
    }
  }
  return out;
}
export function opening(mask, w, h, r) { return filter1(filter1(mask, w, h, r, true), w, h, r, false); }

/** Two-pass chamfer propagation: every px gets the nearest seed's label and distance (px). */
export function propagate(seed, w, h) {
  const dist = new Float32Array(w * h).fill(Infinity);
  const lab = new Int32Array(w * h).fill(-1);
  for (let i = 0; i < seed.length; i += 1) if (seed[i] >= 0) { dist[i] = 0; lab[i] = seed[i]; }
  const relax = (i, j, c) => { const d = dist[j] + c; if (d < dist[i]) { dist[i] = d; lab[i] = lab[j]; } };
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = y * w + x;
      if (x > 0) relax(i, i - 1, 1);
      if (y > 0) { relax(i, i - w, 1); if (x > 0) relax(i, i - w - 1, SQ2); if (x < w - 1) relax(i, i - w + 1, SQ2); }
    }
  }
  for (let y = h - 1; y >= 0; y -= 1) {
    for (let x = w - 1; x >= 0; x -= 1) {
      const i = y * w + x;
      if (x < w - 1) relax(i, i + 1, 1);
      if (y < h - 1) { relax(i, i + w, 1); if (x < w - 1) relax(i, i + w + 1, SQ2); if (x > 0) relax(i, i + w - 1, SQ2); }
    }
  }
  return { dist, lab };
}

function components(mask, w, h, minPx) {
  const seen = new Uint8Array(w * h);
  const out = [];
  const stack = [];
  for (let s = 0; s < mask.length; s += 1) {
    if (!mask[s] || seen[s]) continue;
    let n = 0, x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1, sx = 0, sy = 0;
    stack.push(s); seen[s] = 1;
    while (stack.length) {
      const i = stack.pop();
      const x = i % w, y = (i / w) | 0;
      n += 1; sx += x; sy += y;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      for (const j of [x > 0 ? i - 1 : -1, x < w - 1 ? i + 1 : -1, y > 0 ? i - w : -1, y < h - 1 ? i + w : -1]) {
        if (j >= 0 && mask[j] && !seen[j]) { seen[j] = 1; stack.push(j); }
      }
    }
    if (n >= minPx) out.push({ n, x0, y0, x1, y1, cx: sx / n, cy: sy / n });
  }
  return out;
}

/**
 * The target's area FAMILIES per px (target resolution): -1 background, -2 fg with no zone (ink, AA, strokes the
 * INK_OPEN opening strips), else the index into famNames (classes/<c>.json likeness.areaFamilies over regions.json).
 * Shared by residuals() and scripts/fit.mjs.
 */
export function targetFamilies(S, img, regions = S.readJson("regions")) {
  const { w, h } = img;
  const { label: zoneLabel, names: zoneNames } = classifyTargetPixels(img, regions);
  const areaFamilies = S.cls.likeness?.areaFamilies ?? {};
  const famNames = [];
  const famOfZone = zoneNames.map((z) => {
    const f = Object.keys(areaFamilies).find((k) => areaFamilies[k].includes(z)) ?? z;
    if (!famNames.includes(f)) famNames.push(f);
    return famNames.indexOf(f);
  });
  // V4-6 item 5 + V5-1 item 1: the three-state target (SUBJECT / BACKGROUND / OCCLUDED don't-care = -3), under the
  // subject's mask rule as the judge's concept view reads it (views.json families: fgMax, enclosedFg, holes.concept)
  const rule = subjectMaskRule(S.id);
  const tfg = targetState(S, img, rule.fgMax, maskOptions(rule, "concept"));
  const tFam = new Int32Array(w * h);
  for (let i = 0; i < w * h; i += 1) tFam[i] = !tfg[i] ? -1 : tfg[i] === OCCLUDED ? -3 : zoneLabel[i] >= 0 ? famOfZone[zoneLabel[i]] : -2;
  // ink outlines read as the dark zones: a family px that does not survive an opening of radius INK_OPEN is
  // "fg, no zone" (never charged near the render) — zones are areas, strokes are not.
  famNames.forEach((_, k) => {
    const m = new Uint8Array(w * h);
    for (let i = 0; i < w * h; i += 1) m[i] = tFam[i] === k ? 1 : 0;
    const kept = opening(m, w, h, INK_OPEN);
    for (let i = 0; i < w * h; i += 1) if (m[i] && !kept[i]) tFam[i] = -2;
  });
  return { w, h, tfg, tFam, famNames, famOfZone, zoneNames, zoneLabel };
}

/** Each projected part's family index (its zone -> paletteZones region -> family), -1 = none. */
export function partFamilies(S, parts, { famOfZone, zoneNames }) {
  const regionOfKey = Object.fromEntries((S.cls.paletteZones ?? []).map((p) => [p.key, p.region]));
  return Int32Array.from(parts.map((p) => {
    const region = regionOfKey[p.zone] ?? (zoneNames.includes(p.zone) ? p.zone : null);
    return region ? famOfZone[zoneNames.indexOf(region)] : -1;
  }));
}

const r3 = (v) => Math.round(v * 1000) / 1000;

/**
 * V4-6 item 2 — family -> the CLOSED palette zone keys whose region is in it (classes/<c>.json paletteZones over
 * likeness.areaFamilies). A family name ("dark") is never a zone; prompts print these keys instead.
 */
export function familyZoneKeys(S) {
  const fams = S.cls.likeness?.areaFamilies ?? {};
  const out = {};
  for (const [f, regions] of Object.entries(fams)) {
    out[f] = (S.cls.paletteZones ?? []).filter((p) => regions.includes(p.region)).sort((a, b) => Number(!!a.closure) - Number(!!b.closure)).map((p) => p.key);
  }
  return out;
}

/** The palette key a target region is painted with (a non-closure key first), or null. */
export function keyOfRegion(S, region) {
  const ps = (S.cls.paletteZones ?? []).filter((p) => p.region === region).sort((a, b) => Number(!!a.closure) - Number(!!b.closure));
  return ps[0]?.key ?? null;
}
const OPP = { top: "bottom", bottom: "top", front: "rear", rear: "front" };

/**
 * @returns {{rows:object[], suppressed:number, tolM:number, registeredIoU:number, familyIoU:object, text:string}}
 */
export async function residuals({ subjectId, modulePath, target = null, built = null }) {
  const S = loadSubject(subjectId);
  const img = target ?? await readRGB(S.paths.target);
  const regions = S.readJson("regions");
  const proj = await project({ subjectId, modulePath, frame: "target", size: img.w, built });
  const reg = proj.registration;   // V5-1 item 2: the module's similarity applied (px per metre = its fitted scale)
  const { w, h, partId } = proj;
  const tolM = TOL_FRAC * reg.anchor.ref;

  // ---- families: zone -> family, part -> family
  const fam = targetFamilies(S, img, regions);
  const { famNames, tfg, tFam } = fam;
  const partFam = partFamilies(S, proj.parts, fam);

  // ---- scoreboard
  const rfg = proj.foreground();
  const registeredIoU = iou(tfg, rfg);
  const familyIoU = {};
  const familyPx = {};   // V4-5A: {I, U} per family (U - I = the family's wrong px, a ZONE row's size)
  famNames.forEach((f, k) => {
    let I = 0, U = 0;
    for (let i = 0; i < w * h; i += 1) { if (tFam[i] === -3) continue; const a = tFam[i] === k; const b = partId[i] >= 0 && partFam[partId[i]] === k; if (a && b) I += 1; if (a || b) U += 1; }
    if (U) { familyIoU[f] = r3(I / U); familyPx[f] = { I, U }; }
  });

  // ---- nearest part: any, and per family
  const near = propagate(partId, w, h);
  const famNear = famNames.map((_, k) => {
    const seed = new Int32Array(w * h).fill(-1);
    let any = false;
    for (let i = 0; i < w * h; i += 1) if (partId[i] >= 0 && partFam[partId[i]] === k) { seed[i] = partId[i]; any = true; }
    return any ? propagate(seed, w, h) : null;
  });
  const missPx = MISS_FRAC * reg.anchor.ref * reg.s;

  // ---- charge pixels: bands[part][kind][side] = {n, cols:Set, rows:Set}
  const nParts = proj.parts.length;
  const bands = Array.from({ length: nParts }, () => ({}));
  const ownShare = new Float64Array(nParts);
  const visible = new Float64Array(nParts);
  const missing = famNames.map(() => new Uint8Array(w * h));
  // front = the screen side the class length axis (+) points to
  const L = turnFn(reg.turnDeg)(reg.anchor.lengthAxis);
  const noseRight = L[0] * reg.basis.right[0] + L[1] * reg.basis.right[1] + L[2] * reg.basis.right[2] >= 0;
  const side = (p, x, y) => {
    const b = proj.parts[p].screen;
    const cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2;
    const nx = (x + 0.5 - cx) / Math.max(1, (b.x1 - b.x0) / 2);
    const ny = (y + 0.5 - cy) / Math.max(1, (b.y1 - b.y0) / 2);
    if (Math.abs(ny) >= Math.abs(nx)) return ny < 0 ? "top" : "bottom";
    return (nx > 0) === noseRight ? "front" : "rear";
  };
  const charge = (p, kind, x, y) => {
    const s = side(p, x, y);
    const key = `${kind}:${s}`;
    const band = bands[p][key] ?? (bands[p][key] = { kind, side: s, n: 0, cols: new Set(), rows: new Set() });
    band.n += 1; band.cols.add(x); band.rows.add(y);
  };
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = y * w + x;
      const p = partId[i];
      const t = tFam[i];
      if (t === -3) continue;   // OCCLUDED: neither charged nor owed
      if (p >= 0) {
        visible[p] += 1;
        if (t >= 0 && t === partFam[p]) ownShare[p] += 1;
        if (t === -1 || (t >= 0 && partFam[p] >= 0 && t !== partFam[p])) charge(p, "EXCESS", x, y);
      }
      if (t >= 0 && (p < 0 || (partFam[p] >= 0 && partFam[p] !== t))) {
        const fn = famNear[t];
        if (!fn || fn.dist[i] > missPx) missing[t][i] = 1;
        else charge(fn.lab[i], "DEFICIT", x, y);
      } else if (t === -2 && p < 0 && near.dist[i] > INK_PX && near.lab[i] >= 0) {
        charge(near.lab[i], "DEFICIT", x, y);
      }
    }
  }

  // ---- metres: top/bottom along world Y, front/rear along the length axis (on the part's plane)
  // MVP-STUB: axis-wise inverse (px / (s x |axis . screen|)), not a full per-plane screenProjector inverse.
  const pxPerMY = reg.s * Math.abs(reg.basis.up[1]);
  const pxPerML = reg.s * Math.hypot(L[0] * reg.basis.right[0] + L[2] * reg.basis.right[2], L[0] * reg.basis.up[0] + L[2] * reg.basis.up[2]);
  const metres = (band) => {
    const vertical = band.side === "top" || band.side === "bottom";
    const span = vertical ? band.cols.size : band.rows.size;
    return (band.n / Math.max(1, span)) / (vertical ? pxPerMY : pxPerML);
  };

  const rows = [];
  let suppressed = 0;
  const push = (row) => {
    if (row.metres < 0.5 * tolM || row.areaPx < MIN_AREA) { suppressed += 1; return; }
    rows.push(row);
  };
  const verb = { top: "top edge", bottom: "bottom edge", front: "front edge", rear: "rear edge" };
  const dirOf = { top: "up", bottom: "down", front: "forward", rear: "back" };
  proj.parts.forEach((part, p) => {
    const base = { part: part.id, role: part.role, zone: part.zone, family: partFam[p] >= 0 ? famNames[partFam[p]] : null };
    if (visible[p] >= MIN_AREA && partFam[p] >= 0 && ownShare[p] / visible[p] < EXTRA_SHARE) {
      push({ ...base, target: part.id, kind: "EXTRA", metres: r3(Math.sqrt(visible[p]) / reg.s), side: "-", areaPx: visible[p],
        proposal: `remove part "${part.id}" or move/recolour it: ${Math.round((1 - ownShare[p] / visible[p]) * 100)} % of its px are not ${famNames[partFam[p]]} in the target` });
      return;
    }
    const b = bands[p];
    const used = new Set();
    for (const [s1, s2] of [["top", "bottom"], ["front", "rear"]]) {
      const E1 = b[`EXCESS:${s1}`], D1 = b[`DEFICIT:${s1}`], E2 = b[`EXCESS:${s2}`], D2 = b[`DEFICIT:${s2}`];
      const m = (x) => (x ? metres(x) : 0);
      const big = (x) => x && x.n >= MIN_AREA && metres(x) >= 0.5 * tolM;
      // OFFSET: excess on one side and deficit on the other
      for (const [E, D, toward] of [[E1, D2, s1], [E2, D1, s2]]) {
        if (big(E) && big(D) && !used.has(E) && !used.has(D)) {
          const mm = (m(E) + m(D)) / 2;
          push({ ...base, target: part.id, kind: "OFFSET", metres: r3(mm), side: toward, areaPx: E.n + D.n,
            proposal: `move part "${part.id}" ${dirOf[OPP[toward]]} by ${r3(mm)} m (it sits ${dirOf[toward]} of the target)` });
          used.add(E); used.add(D);
        }
      }
      // EXTENT: both sides the same way
      for (const [A, B, kind] of [[E1, E2, "EXCESS"], [D1, D2, "DEFICIT"]]) {
        if (big(A) && big(B) && !used.has(A) && !used.has(B)) {
          const mm = m(A) + m(B);
          push({ ...base, target: part.id, kind: "EXTENT", metres: r3(kind === "EXCESS" ? -mm : mm), side: `${s1}+${s2}`, areaPx: A.n + B.n,
            proposal: `${kind === "EXCESS" ? "shrink" : "grow"} part "${part.id}" by ${r3(mm)} m ${s1 === "top" ? "in height" : "in length"}` });
          used.add(A); used.add(B);
        }
      }
    }
    for (const band of Object.values(b)) {
      if (used.has(band)) continue;
      const mm = metres(band);
      push({ ...base, target: part.id, kind: band.kind, metres: r3(mm), side: band.side, areaPx: band.n,
        proposal: band.kind === "EXCESS"
          ? `pull the ${verb[band.side]} of "${part.id}" in by ${r3(mm)} m`
          : `push the ${verb[band.side]} of "${part.id}" out by ${r3(mm)} m` });
    }
  });
  // MISSING: target family blobs with no part of that family near them. V4-6 item 2: the row names the palette ZONE
  // KEY painted over most of the blob (its majority target region), never the family.
  famNames.forEach((f, k) => {
    for (const c of components(missing[k], w, h, MIN_AREA)) {
      const votes = new Map();
      for (let y = c.y0; y <= c.y1; y += 1) for (let x = c.x0; x <= c.x1; x += 1) { const i = y * w + x; if (missing[k][i] && fam.zoneLabel[i] >= 0) votes.set(fam.zoneLabel[i], (votes.get(fam.zoneLabel[i]) ?? 0) + 1); }
      const region = fam.zoneNames[[...votes.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]] ?? null;
      const key = (region && keyOfRegion(S, region)) ?? familyZoneKeys(S)[f]?.[0] ?? f;
      const wm = (c.x1 - c.x0 + 1) / reg.s;
      const hm = (c.y1 - c.y0 + 1) / pxPerMY;
      const nearest = near.lab[Math.round(c.cy) * w + Math.round(c.cx)];
      const host = nearest >= 0 ? proj.parts[nearest].id : "-";
      push({ target: key, kind: "MISSING", metres: r3(Math.max(wm, hm)), part: host, role: null, zone: key, family: f,
        side: side(nearest >= 0 ? nearest : 0, Math.round(c.cx), Math.round(c.cy)), areaPx: c.n,
        at: [Math.round(c.cx), Math.round(c.cy)],
        proposal: `add one part with zone "${key}" ~${r3(wm)} x ${r3(hm)} m at target px (${Math.round(c.cx)}, ${Math.round(c.cy)}), next to part "${host}"` });
    }
  });

  rows.sort((a, b) => b.areaPx - a.areaPx);
  for (const r of rows) {
    const signed = r.kind === "EXCESS" ? -r.metres : r.metres;
    r.text = `RESIDUAL ${r.target} ${r.kind} ${signed >= 0 ? "+" : ""}${signed.toFixed(3)} m — part "${r.part}" side ${r.side} — proposal: ${r.proposal}`;
  }
  // WORKFLOW v4 V4-2 ruling — the class NOISE FLOOR (classes/<c>.json residualFloor {metres, px}): only rows at or over
  // both are SHOWN (the text a seat reads); `rows` keeps every row over the 0.5 x tol cut for diagnostics.
  const floor = S.cls.residualFloor ?? null;
  const shown = floor ? rows.filter((r) => r.metres >= floor.metres && r.areaPx >= floor.px) : rows;
  const head = `registered IoU ${registeredIoU.toFixed(4)} | family IoU ${Object.entries(familyIoU).map(([k, v]) => `${k} ${v}`).join(", ")} | tol ${r3(tolM)} m (rows < ${r3(0.5 * tolM)} m suppressed: ${suppressed})`
    + (floor ? ` | noise floor ${floor.metres} m / ${floor.px} px: ${shown.length} of ${rows.length} rows shown` : "");
  return { subject: subjectId, module: modulePath, registeredIoU: Math.round(registeredIoU * 1e4) / 1e4, familyIoU, familyPx, tolM: r3(tolM), suppressed, floor, rows, shown, text: [head, ...shown.map((r) => r.text)].join("\n") };
}

/** Plain text table of the top rows. */
export function residualTable(result, n = 12, list = result.shown ?? result.rows) {
  const lines = [`${"#".padEnd(3)}${"target".padEnd(18)}${"kind".padEnd(9)}${"metres".padStart(8)}  ${"part".padEnd(20)}${"side".padEnd(13)}${"px".padStart(7)}`];
  list.slice(0, n).forEach((r, i) => {
    const signed = r.kind === "EXCESS" ? -r.metres : r.metres;
    lines.push(`${String(i + 1).padEnd(3)}${String(r.target).slice(0, 17).padEnd(18)}${r.kind.padEnd(9)}${signed.toFixed(3).padStart(8)}  ${String(r.part).slice(0, 19).padEnd(20)}${String(r.side).padEnd(13)}${String(r.areaPx).padStart(7)}`);
  });
  return lines.join("\n");
}

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject");
  const modulePath = arg("module");
  if (!subjectId || !modulePath) {
    console.error("usage: node scripts/residuals.mjs --subject <id> --module <path.mjs> [--json <out.json>] [--rows N]");
    process.exit(3);
  }
  const result = await residuals({ subjectId, modulePath });
  console.log(result.text.split("\n")[0]);
  console.log(residualTable(result, Number(arg("rows", 12))));
  console.log("");
  for (const r of result.shown.slice(0, Number(arg("rows", 12)))) console.log(r.text);
  const out = arg("json");
  if (out) {
    fs.mkdirSync(path.dirname(path.resolve(ROOT, out)), { recursive: true });
    fs.writeFileSync(path.resolve(ROOT, out), `${JSON.stringify({ ...result, text: undefined }, null, 2)}\n`);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(error); process.exit(1); });
}
