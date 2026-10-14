#!/usr/bin/env node
// WF-R5 R5-A item 1 — the PROFILE instrument for the vehicle class (research/WF-R5-FIDELITY.md item 1).
// scripts/measure-vehicle.mjs measures KEYS (one number per landmark); this script measures SHAPE: the flank's
// lower edge (sill + wheel arches), the hood's rise, the cab's tumblehome, the door seams and handle, and the
// feature colours the inlay helpers paint (arch liner, handle, seam, grille slot / bar), all rectified through
// the solved camera on the SAME frame measure-vehicle uses (its `geo` context), so every value is a fraction of
// L / W / H with evidence. Output: `_profile` in layout.measured.json (and layout.json with --freeze). The
// underscore keeps it out of V12_LAYOUT (MVP-STUB: profile keys are consumed by the template and the ready
// calls; no gate rule measures them back yet).
//
//   node scripts/measure-profile.mjs --subject pickup            measure, write layout.measured.json `_profile`
//   node scripts/measure-profile.mjs --subject pickup --freeze   ... and into layout.json
//   node scripts/measure-profile.mjs --subject pickup --check    compare with layout.json `_profile`; exit 1 on drift
//
// METHOD. A flank-plane point (u from the nose over L, v above the ground over H) projects to one pixel
// (measure-vehicle toPx). Walking v upward at each u gives the flank's LOWER EDGE (the first run of body
// pixels): the sill between the wheels and the arch outline above each wheel; a superellipse
// (u - zc)^n / a^n + (v - sill)^n / b^n = 1 is fitted to each arch by grid search. Walking on from there gives
// the flank's TOP over the hood (a line fit: the hood rises toward the cowl). Door seams are the rows / columns
// of peak ink density inside the door; the handle is the darker body-family component on the door.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { loadSubject, subjectIdFromArgv } from "./subject.mjs";
import { measureVehicle, components, ROOT } from "./measure-vehicle.mjs";

export const PROFILE_SCAN = Object.freeze({
  uStep: 0.005,        // L, the flank column walk
  vStep: 0.002,        // H
  runMin: 3,           // consecutive body samples that start the lower edge (skips antialiased ink)
  archPad: 0.012,      // H above the sill that marks an arch point
  archReach: 0.17,     // L either side of a wheel centre searched for its arch
  simplify: 0.004,     // Douglas-Peucker tolerance (H) of the stored lower edge
  inkRow: 0.5,         // a seam row / column must be ink over at least this share of its run
  handlePx: [50, 3000],
});

const r3 = (v) => Math.round(v * 1000) / 1000;
const r4 = (v) => Math.round(v * 10000) / 10000;
const median = (v) => { const s = [...v].sort((a, b) => a - b); return s.length ? s[s.length >> 1] : NaN; };
const pct = (v, f) => { const s = [...v].sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.max(0, Math.round(f * (s.length - 1))))]; };
const hex = (p) => `#${p.map((c) => Math.round(c).toString(16).padStart(2, "0")).join("")}`;

/** Douglas-Peucker on [[u, v], ...] with tolerance `eps` in v units (u scaled 1:1). */
export function simplify(points, eps) {
  if (points.length <= 2) return points.map((p) => [...p]);
  const [a, b] = [points[0], points[points.length - 1]];
  let worst = -1, at = -1;
  for (let i = 1; i < points.length - 1; i += 1) {
    const [x, y] = points[i];
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const d = Math.abs(dy * x - dx * y + b[0] * a[1] - b[1] * a[0]) / (Math.hypot(dx, dy) || 1);
    if (d > worst) { worst = d; at = i; }
  }
  if (worst <= eps) return [[...a], [...b]];
  const left = simplify(points.slice(0, at + 1), eps);
  return [...left.slice(0, -1), ...simplify(points.slice(at), eps)];
}

/** Superellipse arch height above its base at u: b (1 - |(u - zc) / a|^n)^(1/n) inside, else 0. */
export function archRise(arch, u) {
  const t = Math.abs((u - arch.zc) / arch.a);
  return t >= 1 ? 0 : arch.b * (1 - t ** arch.n) ** (1 / arch.n);
}

function fitArch(points, sill, wu, S) {
  const top = Math.max(...points.map((p) => p[1]));
  const b = top - sill;
  let best = null;
  for (let zc = wu - 0.05; zc <= wu + 0.05 + 1e-9; zc += 0.0025) {
    for (let a = 0.06; a <= S.archReach + 1e-9; a += 0.0025) {
      for (let n = 1.5; n <= 6 + 1e-9; n += 0.25) {
        const arch = { zc, a, b, n };
        let err = 0, cnt = 0;
        for (const [u, v] of points) {
          const inside = Math.abs(u - zc) < a;
          const arch_ = v > sill + S.archPad && Math.abs(u - wu) < 0.12;
          if (!inside && !arch_) continue;
          err += Math.abs(sill + archRise(arch, u) - v);
          cnt += 1;
        }
        const e = err / Math.max(cnt, 1);
        if (!best || e < best.err - 1e-12) best = { ...arch, err: e, cnt };
      }
    }
  }
  return { zc: r4(best.zc), a: r4(best.a), b: r4(best.b), n: best.n, top: r4(top), err: r4(best.err), cnt: best.cnt };
}

export async function measureProfile({ targetFile, regionsFile, cameraFile, cls, variant = "pickup" }) {
  const S = PROFILE_SCAN;
  const res = await measureVehicle({ targetFile, regionsFile, cameraFile, variant });
  if (res.geo.variant === "bus") return busProfile(res, S);
  const { geo: g, keys: k, img } = res;
  const names = Object.keys(res.zones);
  const v = (key) => { if (k[key]?.unverified || !Number.isFinite(k[key]?.value ?? k[key]?.values?.[0])) throw new Error(`measure-profile needs the verified key ${key}`); return k[key].value ?? k[key].values; };
  const label = (p) => (g.isInk(p[0], p[1]) ? "ink" : (g.labelAt(p[0], p[1]) === 255 ? "bg" : names[g.labelAt(p[0], p[1])]));
  const onFlank = (u, vv, dx = 0) => g.toPx(dx, g.zFC - u * g.Lb, g.yG + vv * g.H);
  const body = (l) => l === "body_side" || l === "body_front";
  const px = (p) => `${Math.round(p[0])},${Math.round(p[1])}`;
  const regionKey = (zone) => (cls?.paletteZones ?? []).find((z) => z.region === zone && z.closure !== true)?.key
    ?? (cls?.paletteZones ?? []).find((z) => z.region === zone)?.material ?? zone;

  // ---- 1. flank columns: lower edge everywhere, top edge over the hood ---------------------------------
  const nU = Math.round(1 / S.uStep);
  const cols = [];
  for (let i = 1; i < nU; i += 1) {
    const u = i * S.uStep;
    let bottom = null, top = null, run = 0;
    for (let j = 0; j * S.vStep <= 0.85; j += 1) {
      const vv = j * S.vStep;
      const isB = body(label(onFlank(u, vv)));
      if (bottom === null) {
        run = isB ? run + 1 : 0;
        if (run === S.runMin) bottom = vv - (S.runMin - 1) * S.vStep;
      } else if (!isB) { top = vv; break; }
    }
    if (bottom !== null) cols.push({ u: r4(u), bottom: r4(bottom), top: top === null ? null : r4(top) });
  }
  const cabStart = v("cab.start"), cabEnd = v("cab.end"), bedStart = v("bed.start");
  const wheelU = v("wheel.centreFromFront");

  // ---- 2. sill: the lower edge between and behind the arches ------------------------------------------
  const lowRun = cols.filter((c) => c.u >= cabStart && c.u <= 0.99);
  const floor = Math.min(...lowRun.map((c) => c.bottom));
  const sillCols = lowRun.filter((c) => c.bottom <= floor + 0.02);
  const sill = median(sillCols.map((c) => c.bottom));

  // ---- 3. wheel arches: superellipse fit around each wheel --------------------------------------------
  const arches = wheelU.map((wu, i) => {
    const pts = cols.filter((c) => Math.abs(c.u - wu) <= S.archReach).map((c) => [c.u, c.bottom]);
    return { name: i === 0 ? "front" : "rear", wheel: wu, ...fitArch(pts, sill, wu, S) };
  });

  // ---- 4. hood rise: line fit to the flank top from the nose to the cab --------------------------------
  let hoodPts = cols.filter((c) => c.u >= 0.02 && c.u <= cabStart - 0.03 && c.top !== null).map((c) => [c.u, c.top]);
  const lineFit = (pts) => {
    const n = pts.length, su = pts.reduce((s, p) => s + p[0], 0), sv = pts.reduce((s, p) => s + p[1], 0);
    const suu = pts.reduce((s, p) => s + p[0] * p[0], 0), suv = pts.reduce((s, p) => s + p[0] * p[1], 0);
    const b = (n * suv - su * sv) / (n * suu - su * su);
    return { a: (sv - b * su) / n, b };
  };
  let hood = lineFit(hoodPts);
  hoodPts = hoodPts.filter(([u, vv]) => Math.abs(hood.a + hood.b * u - vv) <= 0.01);
  hood = lineFit(hoodPts);

  // ---- 5. door seams: peak ink density rows / columns inside the door ---------------------------------
  const inkShare = (fn, lo, hi, step) => {
    let ink = 0, n = 0;
    for (let t = lo; t <= hi + 1e-9; t += step) { const p = fn(t); n += 1; if (g.isInk(p[0], p[1])) ink += 1; }
    return n ? ink / n : 0;
  };
  const peak = (lo, hi, step, share) => {
    let best = null;
    for (let t = lo; t <= hi + 1e-9; t += step) { const s = share(t); if (!best || s > best.s) best = { t, s }; }
    return best;
  };
  const wsStart = v("window.side.start"), wsEnd = v("window.side.end"), wsBot = v("window.side.bottom"), wsTop = v("window.side.top");
  // The cab leans in above the glass line as its A-pillars do: the windshield's side edges (its bottom and top widths,
  // both measured along eX) give the lean per H, carried from the side glass line to the roof. The silhouette top (the
  // far roof corner) is only a cross-check: its z is the cab back's, which rakes, so its x offset absorbs that rake.
  const wFront = v("window.front.w"), wfb = v("window.front.bottom"), wft = v("window.front.top");
  const silInset = (g.W + g.roofDx) / g.W;
  const roofInset = g.wsTopW && wft > wfb ? Math.max(0, (wFront - g.wsTopW / g.W) / 2 / (wft - wfb) * (1 - wsBot)) : null;
  const doorBottom = peak(sill + 0.01, 0.5, S.vStep, (vv) => inkShare((u) => onFlank(u, vv), cabStart + 0.03, cabEnd - 0.06, S.uStep / 2));
  const colShare = (u) => inkShare((vv) => onFlank(u, vv), doorBottom.t + 0.03, wsBot - 0.03, S.vStep);
  const doorEnd = peak(wsEnd, cabEnd - 0.005, S.uStep / 2, colShare);
  const doorStart = peak(cabStart - 0.02, wsStart, S.uStep / 2, colShare);
  // above the glass the cab leans in: rectify each row on its own tumblehome plane (roof inset, linear from the glass line)
  const lean = (vv) => (roofInset === null ? 0 : -roofInset * g.W * Math.min(1, Math.max(0, (vv - wsBot) / (1 - wsBot))));
  const doorTop = peak(wsTop + 0.005, 0.995, S.vStep, (vv) => inkShare((u) => onFlank(u, vv, lean(vv)), wsStart + 0.02, wsEnd - 0.02, S.uStep / 2));

  // ---- 6. handle: the darker body-family component on the door -----------------------------------------
  const dark = components(img, g.cls, [g.L("bed_inside"), g.L("grille")], S.handlePx[0], true)
    .filter((c) => c.n <= S.handlePx[1])
    .map((c) => {
      const us = [], vs = [];
      for (const p of c.pts) { const q = g.rect(p); us.push((g.zFC - q.z) / g.Lb); vs.push((q.y - g.yG) / g.H); }
      return { c, u: [pct(us, 0.01), pct(us, 0.99)], v: [pct(vs, 0.01), pct(vs, 0.99)] };
    })
    .filter((h) => h.u[0] >= doorStart.t && h.u[1] <= doorEnd.t && h.v[0] >= doorBottom.t && h.v[1] <= wsBot)
    .sort((a, b) => b.c.n - a.c.n);
  const handle = dark[0] ?? null;

  // ---- 7. feature colours for the inlay helpers --------------------------------------------------------
  const sample = (pts) => {
    const counts = new Map(), rgb = [];
    for (const p of pts) {
      const l = label(p);
      if (l === "ink" || l === "bg") continue;
      counts.set(l, (counts.get(l) ?? 0) + 1);
      const i = (Math.round(p[1]) * img.w + Math.round(p[0])) * img.c;
      rgb.push([img.data[i], img.data[i + 1], img.data[i + 2]]);
    }
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
    return top ? { region: top[0], n: top[1], of: pts.length, reads: hex([0, 1, 2].map((ch) => median(rgb.map((c) => c[ch])))) } : null;
  };
  // The wheel well is a tone NO zone median claims (darker than the grille slots): collect the unclassified,
  // non-white, non-ink px under each fitted arch on the flank plane, and hand the median to the NEAREST zone.
  const wellRgb = [];
  for (const a of arches) {
    for (let u = a.zc - 0.9 * a.a; u <= a.zc + 0.9 * a.a + 1e-9; u += S.uStep / 2) {
      for (let vv = sill + 0.02; vv <= sill + archRise(a, u) - 0.01; vv += S.vStep) {
        const p = onFlank(u, vv);
        if (label(p) !== "bg") continue;
        const i = (Math.round(p[1]) * img.w + Math.round(p[0])) * img.c;
        const c = [img.data[i], img.data[i + 1], img.data[i + 2]];
        if (Math.max(...c) < 200) wellRgb.push(c);
      }
    }
  }
  const wellHex = wellRgb.length ? hex([0, 1, 2].map((ch) => median(wellRgb.map((c) => c[ch])))) : null;
  const nearestZone = (h) => {
    const rgb = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
    let best = null;
    for (const [name, z] of Object.entries(res.zones)) {
      const t = [1, 3, 5].map((i) => parseInt(z.hex.slice(i, i + 2), 16));
      // chroma (r - g, g - b) weighted x2 over luma: a slate well is a darker GRILLE tone, not a grey tyre
      const q = (c) => [c[0] - c[1], c[1] - c[2], 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]];
      const [a, b] = [q(t), q(rgb)];
      const d = 4 * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) + (a[2] - b[2]) ** 2;
      if (!best || d < best.d) best = { name, d };
    }
    return best.name;
  };
  const well = wellHex ? { region: nearestZone(wellHex), n: wellRgb.length, of: wellRgb.length, reads: wellHex } : null;
  const handleTone = handle ? sample(handle.c.pts) : null;
  const slotTone = sample((() => { const out = []; for (let f = 0.35; f <= 0.65; f += 0.01) for (const vv of [0.44, 0.52]) out.push(g.toPx(-f * g.W, g.zFC, g.yG + vv * g.H)); return out; })());
  const barTone = sample((() => { const out = []; for (let f = 0.35; f <= 0.65; f += 0.01) out.push(g.toPx(-f * g.W, g.zFC, g.yG + 0.482 * g.H)); return out; })());

  // ---- 8. assemble -------------------------------------------------------------------------------------
  const keys = {};
  const put = (name, value, unit, scan, evidence) => { keys[name] = { value: r3(value), unit, evidence: { scan, px: evidence } }; };
  put("body.sill", sill, "H", "flank lower edge (first run of body px walking up the flank plane) between the front arch and the tail, where it sits within 0.02 H of its lowest: median",
    `${sillCols.length} of ${lowRun.length} columns at u ${cabStart.toFixed(3)}..0.99; lowest ${r3(floor)}`);
  for (const a of arches) {
    const ev = `wheel at ${a.wheel}; top ${a.top} H; fit error ${a.err} H over ${a.cnt} columns`;
    const scan = `the flank lower edge within ${S.archReach} L of the ${a.name} wheel, superellipse fit (centre, half-length a over L, rise b over H, exponent n) by grid search`;
    put(`arch.${a.name}.centre`, a.zc, "L", scan, ev);
    put(`arch.${a.name}.halfLength`, a.a, "L", scan, ev);
    put(`arch.${a.name}.rise`, a.b, "H", scan, ev);
    put(`arch.${a.name}.n`, a.n, "exponent", scan, ev);
  }
  put("hood.front", hood.a, "H", "flank top edge over the hood (first non-body sample above the lower-edge run), line fit, value at the nose",
    `${hoodPts.length} columns u 0.02..${r3(cabStart - 0.03)}; slope ${r3(hood.b)} H per L`);
  put("hood.rear", hood.a + hood.b * cabStart, "H", "the same line fit at cab.start (the cowl end of the hood)", `slope ${r3(hood.b)} H per L`);
  put("door.bottom", doorBottom.t, "H", "flank row of peak ink density across the door (cab.start + 0.03 .. cab.end - 0.06)", `ink share ${r3(doorBottom.s)}`);
  put("door.start", doorStart.t, "L", "flank column of peak ink density from cab.start - 0.02 to the side window's front edge, over the door below the glass", `ink share ${r3(doorStart.s)}`);
  put("door.end", doorEnd.t, "L", "flank column of peak ink density from the side window's rear edge to cab.end, over the door below the glass", `ink share ${r3(doorEnd.s)}`);
  put("door.top", doorTop.t, "H", "row of peak ink density above the side window, each row rectified on its tumblehome plane (roof inset, linear from the glass line)", `ink share ${r3(doorTop.s)}`);
  if (roofInset !== null) {
    put("cab.roofInset", roofInset, "W", "the windshield side edges' lean ((window.front.w - window.front.wTop) / 2 per (window.front.top - window.front.bottom)) carried from the side glass line (window.side.bottom) to the roof, each side",
      `w ${r3(wFront)} -> wTop ${r3(g.wsTopW / g.W)} W over ${r3(wft - wfb)} H; cross-check REJECTED: the silhouette top (far roof corner ${r3(-g.roofDx / g.W)} W off the flank) implies ${r3(silInset)} W, but its z is the raked cab back's, not the flank rear corner's`);
  } else keys["cab.roofInset"] = { unverified: true, unit: "W", reason: "no windshield top width to take the A-pillar lean from" };
  // V5-3 — the windshield's dark FRAME: in each image column through the middle of the windshield glass, the px between
  // the glass run and the body paint above / below it (drawn line + frame), over the glass run's px, times its height (H)
  {
    const ws = components(img, g.cls, [g.L("glass")], 5000, true).sort((a, b) => b.n - a.n)[0];
    const wfb0 = k["window.front.bottom"], wft0 = k["window.front.top"];
    if (ws && wfb0 && !wfb0.unverified && wft0 && !wft0.unverified) {
      const isGlass = (x, y) => g.labelAt(x, y) === g.L("glass");
      const isBody = (x, y) => body(names[g.labelAt(x, y)]);
      const fr = [];
      const sidePx = [];   // V5-6: per column, the frame's mean width in image px (above / below the glass)
      for (let x = Math.round(ws.x0 + 0.3 * (ws.x1 - ws.x0)); x <= ws.x0 + 0.7 * (ws.x1 - ws.x0); x += 2) {
        const ys = ws.pts.filter((q) => q[0] === x).map((q) => q[1]);
        if (ys.length < 10) continue;
        const [y0, y1] = [Math.min(...ys), Math.max(...ys)];
        let up = 0; while (up < 40 && !isBody(x, y0 - 1 - up) && !isGlass(x, y0 - 1 - up)) up += 1;
        let dn = 0; while (dn < 40 && !isBody(x, y1 + 1 + dn) && !isGlass(x, y1 + 1 + dn)) dn += 1;
        if (up < 40 && dn < 40) {
          fr.push((up + dn) / 2 / (y1 - y0 + 1));
          sidePx.push((up + dn) / 2);
        }
      }
      // V5-6: a frame no wider than the ink the accuracy report strips (an opening of radius likeness.inkOpen: 2 r + 1 px)
      // is the drawn outline of a glass set in the body paint, no frame (V5-5 windshield_frame: harness-blind, IoU 0)
      const inkPx = 2 * (cls?.likeness?.inkOpen ?? 2) + 1;
      if (fr.length >= 5 && median(sidePx) <= inkPx) keys["window.front.frame"] = { unverified: true, unit: "H", reason: `the px between glass and paint are ${r3(median(sidePx))} px wide (median of ${fr.length} columns) <= ${inkPx} px (likeness.inkOpen): the drawn outline of the glass, no frame tone` };
      else if (fr.length >= 5) put("window.front.frame", median(fr) * (wft0.value - wfb0.value), "H", "the windshield's dark frame: per image column through the middle 40 % of the windshield glass, the non-glass non-paint px above and below the glass run (drawn line + frame, mean of the two) over the glass run's px, times the windshield height (window.front.top - bottom); median", `${fr.length} columns, ${r3(median(sidePx))} px wide; glass ${ws.n} px box ${ws.x0},${ws.y0}..${ws.x1},${ws.y1}`);
      else keys["window.front.frame"] = { unverified: true, unit: "H", reason: `glass -> paint found on ${fr.length} columns` };
    }
  }
  if (g.wsTopW) put("window.front.wTop", g.wsTopW / g.W, "W", "windshield upper edge walked along the eX slope from its top-far corner (measure-vehicle window.front.w cross-check)", `${r3(g.wsTopW)} px units`);
  if (handle) {
    const h = handle;
    put("handle.centreAt", (h.u[0] + h.u[1]) / 2, "L", "the door's darker body-family component (bed_inside / grille labels, 50..3000 px) rectified on the flank, 1..99th percentile", `${h.c.n} px box ${h.c.x0},${h.c.y0}..${h.c.x1},${h.c.y1}`);
    put("handle.centreY", (h.v[0] + h.v[1]) / 2, "H", "same component, centre height", `v ${r3(h.v[0])}..${r3(h.v[1])}`);
    put("handle.length", h.u[1] - h.u[0], "L", "same component, extent along the flank", `u ${r3(h.u[0])}..${r3(h.u[1])}`);
    put("handle.h", h.v[1] - h.v[0], "H", "same component, extent in height", `v ${r3(h.v[0])}..${r3(h.v[1])}`);
  } else for (const n of ["handle.centreAt", "handle.centreY", "handle.length", "handle.h"]) keys[n] = { unverified: true, unit: "L", reason: "no darker body-family component on the door" };
  if (g.bumperRear?.top) {
    const br = g.bumperRear;
    put("bumper.rear.top", (br.top.y - g.yG) / g.H, "H", "the rear bumper's +X face (largest bumper component right of the rear tyre): its front corner edge is taken at the flank rear corner's z, which fixes the face's offset off the flank; the corner's top end rectified on that plane (an inset error of 0.1 W moves it 0.03 H)", `corner x ${r3(br.cornerX)}, y ${br.topY}..${br.botY}; corner z ${r3(br.top.z)} vs flank rear corner ${r3(g.zRC)}`);
    put("bumper.rear.depth", br.depth / g.Lb, "L", "the rear bumper's +X face length along the flank, rectified on its own plane (measure-vehicle bumper.rear.top)", `corner x ${r3(br.cornerX)} .. far edge x ${br.side.x1 + 0.5}`);
    put("bumper.rear.out", br.out / g.W, "W", "the rear bumper's +X face offset off the flank (+ outboard), from its front corner edge at the flank rear corner's z", `corner x ${r3(br.cornerX)}`);
  }
  keys["bed.floor"] = {
    unverified: true, unit: "H",
    reason: "the floor / far-wall junction is hidden behind the near bed wall at this elevation (no ink line of the bed-inside tone runs along eZ below the rim); the template raises the floor over the rear arch liner",
  };
  const inlay = (tone, scan) => (tone ? { zone: regionKey(tone.region), region: tone.region, reads: tone.reads, px: `${tone.n} of ${tone.of} samples`, scan } : null);
  const inlays = {
    archLiner: inlay(well, "unclassified non-white px under each fitted arch (flank plane): the wheel-well tone, handed to the nearest zone median by chroma (x2) and luma"),
    handle: inlay(handleTone, "the handle component's own pixels"),
    seam: { zone: regionKey("bed_inside"), region: "bed_inside", reads: null, px: "seam pixels are ink (outlines excluded)",
      scan: "a door seam is an ink line in the target; its inlay takes the body family's darker tone (bed_inside, the tone the handle slot reads) so the groove reads in a flat unlit capture" },
    grilleSlot: inlay(slotTone, "nose-plane samples inside the two grille bands (0.44 / 0.52 H, 0.35..0.65 W)"),
    grilleBar: inlay(barTone, "nose-plane samples on the slat between the grille bands (0.482 H, 0.35..0.65 W)"),
  };
  const bottom = simplify(cols.map((c) => [c.u, c.bottom]), S.simplify).map(([a, b]) => [r4(a), r4(b)]);
  const vb = wsBot;
  return {
    _comment: "GENERATED by scripts/measure-profile.mjs (WF-R5 R5-A). SHAPE measurements on measure-vehicle's frame: u from the nose over L, v above the ground over H, x over W from the centre plane. The template (scripts/template-vehicle.mjs) builds the body as extrude(side) ∩ extrude(front) ∩ extrude(plan) from these and the layout keys. MVP-STUB: no V12 rule measures them back.",
    side: {
      bottom,
      hoodTop: [[0, r4(hood.a)], [r4(cabStart), r4(hood.a + hood.b * cabStart)]],
      scan: `flank lower edge per ${S.uStep} L column (first ${S.runMin} body samples walking up the flank plane), Douglas-Peucker ${S.simplify} H; hood top = line fit of the flank top edge`,
      px: `${cols.length} columns; origin ${px(g.O)}`,
    },
    front: {
      points: roofInset === null ? [[-0.5, 0], [0.5, 0], [0.5, 1], [-0.5, 1]]
        : [[-0.5, 0], [0.5, 0], [0.5, r4(vb)], [r4(0.5 - roofInset), 1], [r4(-0.5 + roofInset), 1], [-0.5, r4(vb)]],
      scan: "the cab section: full width to the side glass line (window.side.bottom), leaning in to the roof by cab.roofInset each side (the A-pillar lean); the nose-plane top edge is flat (every column's first ink above the lamps sits within 0.01 H of hood.top)",
    },
    plan: {
      points: [[-0.5, 0], [0.5, 0], [0.5, 1], [-0.5, 1]],
      scan: "no plan-view curvature is resolvable at theta 29 deg: the nose-face corner edges and the flank corners are straight verticals (measure-vehicle width.overL / bed.end chains)",
    },
    keys,
    inlays,
    arches: arches.map((a) => ({ name: a.name, zc: a.zc, a: a.a, b: a.b, n: a.n, err: a.err })),
  };
}

/**
 * V4-7 — the BUS profile (classes/vehicle.json variants.bus): a box body with a flat nose, on measure-vehicle's bus
 * frame: the flank lower edge (sill between the arches + the two arch superellipses, the same fit as the pickup), the
 * nose face's top (where the windshield frame gives way to the lit front cap), the roof's front edge (the cap's depth,
 * walked along the roof plane) and the chamfered front corners (measure-vehicle's two creases).
 */
function busProfile(res, S) {
  const { geo: g, keys: k } = res;
  const v = (key) => { if (k[key]?.unverified || !Number.isFinite(k[key]?.value ?? k[key]?.values?.[0])) throw new Error(`measure-profile (bus) needs the verified key ${key}`); return k[key].value ?? k[key].values; };
  const cls = (p) => g.walkClass(p);
  const onFlank = (u, vv, dx = 0) => g.toPx(dx, g.zN - u * g.Lb, g.yG + vv * g.H);
  const wheelU = v("wheel.centreFromFront");
  // ---- 1. flank lower edge per column: the first run of body paint walking up the flank plane
  const nU = Math.round(1 / S.uStep);
  const cols = [];
  for (let i = 1; i < nU; i += 1) {
    const u = i * S.uStep;
    let bottom = null, run = 0;
    for (let j = 0; j * S.vStep <= 0.85 && bottom === null; j += 1) {
      run = cls(onFlank(u, j * S.vStep)) === "body" ? run + 1 : 0;
      if (run === S.runMin) bottom = (j - (S.runMin - 1)) * S.vStep;
    }
    if (bottom !== null) cols.push({ u: r4(u), bottom: r4(bottom) });
  }
  // ---- 2. sill: between the two arches (the nose drops to the bumper, so the sill is never read ahead of the front arch)
  const between = cols.filter((c) => c.u >= wheelU[0] + S.archReach && c.u <= wheelU[1] - S.archReach);
  const floor = Math.min(...between.map((c) => c.bottom));
  const sillCols = between.filter((c) => c.bottom <= floor + 0.02);
  const sill = median(sillCols.map((c) => c.bottom));
  const arches = wheelU.map((wu, i) => {
    const pts = cols.filter((c) => Math.abs(c.u - wu) <= S.archReach).map((c) => [c.u, c.bottom]);
    return { name: i === 0 ? "front" : "rear", wheel: wu, ...fitArch(pts, sill, wu, S) };
  });
  // ---- 3. nose top: up the nose plane about the centre plane, the windshield frame's black gives way to the lit cap
  const wsTop = v("window.front.top");
  const noseTops = [];
  for (let f = -0.2; f <= 0.2 + 1e-9; f += 0.05) {
    let prev = null, edge = null;
    for (let vv = wsTop - 0.05; vv <= 1.05 && edge === null; vv += S.vStep) {
      const c = cls(g.toPx(-g.W / 2 + f * g.W, g.zN, g.yG + vv * g.H));
      if (prev === "dark" && c === g.Z.roof) edge = vv;
      if (c === "dark" || c === g.Z.roof) prev = c;
    }
    if (edge !== null) noseTops.push(edge);
  }
  // ---- 4. roof front: along the roof plane (y = H) about the centre plane, from inside the roof forward to its edge
  const roofFront = [];
  for (let f = -0.2; f <= 0.2 + 1e-9; f += 0.05) {
    let last = null;
    for (let u = 0.3; u >= -0.05; u -= S.uStep / 2) {
      const c = cls(g.toPx(-g.W / 2 + f * g.W, g.zN - u * g.Lb, g.yG + g.H));
      if (c === g.Z.roof) last = u; else if (last !== null) break;   // the drawn roof-edge line ends the roof
    }
    if (last !== null) roofFront.push(last);
  }
  const keys = {};
  const put = (name, value, unit, scan, evidence) => { keys[name] = { value: r3(value), unit, evidence: { scan, px: evidence } }; };
  put("body.sill", sill, "H", "flank lower edge (first run of body paint walking up the flank plane) between the two arches, within 0.02 H of its lowest: median",
    `${sillCols.length} of ${between.length} columns at u ${r3(wheelU[0] + S.archReach)}..${r3(wheelU[1] - S.archReach)}; lowest ${r3(floor)}`);
  for (const a of arches) {
    const ev = `wheel at ${a.wheel}; top ${a.top} H; fit error ${a.err} H over ${a.cnt} columns`;
    const scan = `the flank lower edge within ${S.archReach} L of the ${a.name} wheel, superellipse fit (centre, half-length a over L, rise b over H, exponent n) by grid search`;
    put(`arch.${a.name}.centre`, a.zc, "L", scan, ev);
    put(`arch.${a.name}.halfLength`, a.a, "L", scan, ev);
    put(`arch.${a.name}.rise`, a.b, "H", scan, ev);
    put(`arch.${a.name}.n`, a.n, "exponent", scan, ev);
  }
  if (noseTops.length >= 3) put("nose.top", median(noseTops), "H", "up the nose plane (x -0.2..0.2 W about the centre plane) from the windshield top: the black frame -> lit cap paint edge (where the flat nose face ends)", `${noseTops.length} columns`);
  else keys["nose.top"] = { unverified: true, unit: "H", reason: `black -> cap edge found on ${noseTops.length} columns` };
  if (roofFront.length >= 3) put("roof.front", median(roofFront), "L", "along the roof plane (y = H) about the centre plane, from the roof forward: the last roof-paint u from the nose (the front cap's depth back from the nose)", `${roofFront.length} columns`);
  else keys["roof.front"] = { unverified: true, unit: "L", reason: `roof paint edge found on ${roofFront.length} columns` };
  const rCW = g.rC / g.W, rCL = g.rC / g.Lb;
  put("corner.chamfer", rCW, "W", "the rounded vertical front corner read as a chamfer: (flank crease - nose crease) / (cos phi + sin phi) on measure-vehicle's bus frame", `${r3(g.rC)} px units`);
  busDetails(res, keys, put);
  const bumperTop = v("bumper.front.top");
  const nt = keys["nose.top"]?.value ?? wsTop;
  const rf = keys["roof.front"]?.value ?? 0;
  const bottom = simplify(cols.map((c) => [c.u, c.bottom]), S.simplify).map(([a, b]) => [r4(a), r4(b)]);
  return {
    _comment: "GENERATED by scripts/measure-profile.mjs (V4-7 bus variant). SHAPE on measure-vehicle's bus frame: u from the box nose over L, v above the ground over H, x over W from the centre plane. scripts/template-vehicle.mjs builds the bus body from side (elevation), front (section) and plan. MVP-STUB: no V12 rule measures them back.",
    variant: "bus",
    side: {
      bottom,
      nose: [[0, r4(bumperTop)], [0, r4(nt)], [r4(rf), 1]],
      scan: `flank lower edge per ${S.uStep} L column; nose = the flat face from the bumper top to nose.top, then the cap back to roof.front on the roof`,
      px: `${cols.length} columns`,
    },
    front: { points: [[-0.5, 0], [0.5, 0], [0.5, 1], [-0.5, 1]], scan: "the flank top is ONE drawn line (flank paint -> roof paint, measure-vehicle height.overL): no tumblehome or roof-edge chamfer is resolvable on the flank" },
    plan: {
      points: [[-0.5, 0], [0.5, 0], [0.5, r4(1 - rCL)], [r4(0.5 - rCW), 1], [r4(-0.5 + rCW), 1], [-0.5, r4(1 - rCL)]],
      axes: "[x over W from the centre plane, t over L from the TAIL (1 = the box nose)]",
      scan: "the chamfered front corners (corner.chamfer); the tail corners are straight (the flank rear corner is one vertical drawn edge)",
    },
    keys,
    inlays: {},
    arches: arches.map((a) => ({ name: a.name, zc: a.zc, a: a.a, b: a.b, n: a.n, err: a.err })),
  };
}

/**
 * V5-3 — the bus DETAIL instrument: every visible detail the READY calls build gets a measured key (walk units = px
 * units on measure-vehicle's rectified planes; nose plane x from the centre plane, flank plane z from the box nose).
 * Label walks: paint = body tones + roof, "dark" = tyre / black paint; a key that finds too few samples is UNVERIFIED
 * with a reason.
 */
function busDetails(res, keys, put) {
  const { geo: g, keys: k, zones, img } = res;
  const val = (key) => (k[key] && !k[key].unverified ? (k[key].value ?? k[key].values) : null);
  const unv = (name, unit, reason) => { keys[name] = { unverified: true, unit, reason }; };
  const B = { step: 0.5, runMin: 1.5 };
  const runs = (fn, t0, t1) => {
    const dt = t1 >= t0 ? B.step : -B.step;
    const out = [];
    for (const r of g.runsAlong(fn, t0, t1, dt)) {
      if (Math.abs(r.b - r.a) + B.step < B.runMin) continue;   // a line / antialiasing sliver
      const last = out[out.length - 1];
      if (last && last.label === r.label) last.b = r.b; else out.push({ ...r });
    }
    return out;
  };
  const paint = (l) => l === "body" || l === g.Z.roof;
  const noseP = (x, y) => g.toPx(-g.W / 2 + x, g.zN, g.yG + y);
  const flankP = (z, y) => g.toPx(0, g.zN - z, g.yG + y);
  const cls = (p) => g.walkClass(p);
  /** from inside a run of `inside` walking t0 -> t1: the gap (walk units) between its end and the next run `stop` */
  const gapAfter = (fn, t0, t1, inside, stop) => {
    const rs = runs(fn, t0, t1);
    const i = rs.findIndex((r) => inside(r.label));
    if (i !== 0) return null;
    const j = rs.findIndex((r, n) => n > i && stop(r.label));
    return j > 0 ? { gap: Math.abs(rs[j].a - rs[i].b), end: rs[i].b, next: rs[j].a } : null;
  };
  const wsB = val("window.front.bottom"), wsT = val("window.front.top"), wsW = val("window.front.w"), post = val("window.front.post") ?? 0;
  // ---- windshield frame (black) round the two panes: up / down the nose plane at each pane's centre, out at mid height
  if ([wsB, wsT, wsW].every((x) => x !== null)) {
    const half = wsW * g.W / 2;
    const cx = (half + post * g.W / 2) / 2;
    const [y0, y1] = [wsB * g.H, wsT * g.H];
    const ym = (y0 + y1) / 2;
    const glass = (l) => l === g.Z.glass;
    const tops = [], bots = [], sides = [];
    for (const s of [-1, 1]) for (const f of [-0.3, -0.15, 0, 0.15, 0.3]) {
      const x = s * cx + f * (half - post * g.W / 2) / 2;
      const up = gapAfter((y) => cls(noseP(x, y)), ym, y1 + 0.15 * g.H, glass, paint);
      if (up) tops.push(up.gap);
      const dn = gapAfter((y) => cls(noseP(x, y)), ym, y0 - 0.2 * g.H, glass, paint);
      if (dn) bots.push(dn.gap);
    }
    for (const f of [-0.3, -0.15, 0, 0.15, 0.3]) {
      const sd = gapAfter((x) => cls(noseP(x, ym + f * (y1 - y0) / 2)), -cx, -half - 0.15 * g.W, glass, (l) => paint(l) || l === "bg");
      if (sd) sides.push(sd.gap);
    }
    const ev = `${tops.length} / ${bots.length} / ${sides.length} walks; pane centres x ±${r3(cx / g.W)} W`;
    const scan = "the windshield's black frame: the non-paint gap between a pane's glass and the nose paint (or the cap) walking up / down the nose plane at each pane's centre columns, and out past the far pane's outer edge at mid height; median";
    if (tops.length >= 3) put("windshield.frame.top", median(tops) / g.H, "H", scan, ev); else unv("windshield.frame.top", "H", `glass -> paint above found on ${tops.length} walks`);
    if (bots.length >= 3) put("windshield.frame.bottom", median(bots) / g.H, "H", scan, ev); else unv("windshield.frame.bottom", "H", `glass -> paint below found on ${bots.length} walks`);
    if (sides.length >= 3) put("windshield.frame.side", median(sides) / g.W, "W", scan, ev); else unv("windshield.frame.side", "W", `glass -> paint beside found on ${sides.length} walks`);
  }
  // ---- window band: its rear end along the band mid line (>= 0.985 L = it runs round the rear corner)
  const bb = val("window.band.bottom"), bt = val("window.band.top");
  if (bb !== null && bt !== null) {
    const vm = (bb + bt) / 2 * g.H;
    const rs = runs((z) => cls(flankP(z, vm)), 0.3 * g.Lb, 1.03 * g.Lb);
    const band = rs.filter((r) => r.label === "dark" || r.label === g.Z.glass || r.label === -1);
    if (band.length) put("band.end", band[band.length - 1].b / g.Lb, "L", "the last black / glass run along the window band's mid line on the flank plane (u 0.30..1.03): the band's rear end; >= 0.985 = it runs round the rear corner", `band mid ${r3(vm / g.H)} H; last run u ${r3(band[band.length - 1].a / g.Lb)}..${r3(band[band.length - 1].b / g.Lb)}`);
    else unv("band.end", "L", "no black / glass run on the band mid line");
  }
  // ---- the entrance door: the glass component ahead of the pane row on the flank, its black leaf round it
  const rowStart = val("window.row.start");
  const glassComps = components(img, g.cls, [g.Z.glass], 150, true);
  const onFlank = (p) => { const r = g.rect(p); return { u: (g.zN - r.z) / g.Lb, v: (r.y - g.yG) / g.H }; };
  const doorGlass = rowStart === null ? [] : glassComps.filter((c) => c.x0 > g.xn).map((c) => ({ c, f: onFlank([c.cx, c.cy]) })).filter((d) => d.f.u > 0 && d.f.u < rowStart).sort((a, b) => b.c.n - a.c.n);
  if (doorGlass.length) {
    const d = doorGlass[0].c;
    const pts = d.pts.map(onFlank);
    const us = g.span(pts.map((p) => p.u)), vs = g.span(pts.map((p) => p.v));
    const uc = (us.lo + us.hi) / 2 * g.Lb, vc = (vs.lo + vs.hi) / 2 * g.H;
    const glass = (l) => l === g.Z.glass;
    const notDark = (l) => l !== "dark" && l !== -1;
    const rear = gapAfter((z) => cls(flankP(z, vc)), uc, uc + 0.15 * g.Lb, glass, notDark);
    const down = gapAfter((y) => cls(flankP(uc, y)), vc, vc - 0.3 * g.H, glass, notDark);
    const up = gapAfter((y) => cls(flankP(uc, y)), vc, vc + 0.3 * g.H, glass, notDark);
    const ev = `glass ${d.n} px box ${d.x0},${d.y0}..${d.x1},${d.y1} (u ${r3(us.lo)}..${r3(us.hi)}, v ${r3(vs.lo)}..${r3(vs.hi)}); leaf gaps rear ${rear ? r3(rear.gap / g.Lb) : "-"} L, below ${down ? r3(down.gap / g.H) : "-"} H, above ${up ? r3(up.gap / g.H) : "-"} H`;
    const scan = "the entrance door: the largest glass component right of the nose crease whose rectified centroid lies ahead of window.row.start (1..99th percentile on the flank plane; its front is behind the near mirror head, so the leaf runs to the flank's front corner); the leaf = the black run past the glass walking back / down / up from its centre";
    put("door.start", g.rC / g.Lb, "L", `${scan}: the leaf's front = the flank crease (corner chamfer)`, ev);
    put("door.pane.start", us.lo, "L", scan, ev);
    put("door.pane.end", us.hi, "L", scan, ev);
    put("door.pane.bottom", vs.lo, "H", scan, ev);
    put("door.pane.top", vs.hi, "H", scan, ev);
    put("door.end", us.hi + (rear ? rear.gap / g.Lb : 0), "L", scan, ev);
    put("door.bottom", vs.lo - (down ? down.gap / g.H : 0), "H", scan, ev);
    put("door.top", vs.hi + (up ? up.gap / g.H : 0), "H", scan, ev);
  } else unv("door.pane.start", "L", "no glass component ahead of the pane row on the flank");
  // ---- turn lenses: rounded rects on the nose plane (their rectified extent)
  const zi = (name) => g.cls.idx(name);
  const lampY = val("headlight.centreY");
  const turnComps = zi("amber") < 0 || lampY === null ? [] : components(img, g.cls, [zi("amber")], 20, true).filter((c) => (g.onZPlane([c.cx, c.cy], g.zN).y - g.yG) / g.H < lampY && c.x1 < g.xf + 4);
  if (turnComps.length >= 2) {
    const ext = turnComps.map((c) => { const pts = c.pts.map((p) => g.onZPlane(p, g.zN)); const a = g.span(pts.map((p) => p.dx)), b = g.span(pts.map((p) => p.y)); return { w: a.hi - a.lo, h: b.hi - b.lo, c }; });
    const ev = ext.map((e) => `${e.c.n} px box ${e.c.x0},${e.c.y0}..${e.c.x1},${e.c.y1}: w ${r3(e.w / g.W)} W, h ${r3(e.h / g.H)} H`).join("; ");
    const scan = "turn lenses (amber components under the lamp line) rectified onto the nose plane, 1..99th percentile extent; median";
    put("turn.w", median(ext.map((e) => e.w)) / g.W, "W", scan, ev);
    put("turn.h", median(ext.map((e) => e.h)) / g.H, "H", scan, ev);
  } else { unv("turn.w", "W", `${turnComps.length} amber component(s) under the lamp line`); unv("turn.h", "H", `${turnComps.length} amber component(s) under the lamp line`); }
  // ---- headlight rings: radial walks on the nose plane from each lamp's centre: lens -> ring (non-paint) -> paint
  const rings = [];
  const ringDark = [];   // V5-6: per walk, the share of the gap whose px classify to the dark paint (a bezel), not ink / AA
  for (const c of g.lamps ?? []) {
    const r0 = g.onZPlane([c.cx, c.cy], g.zN);
    for (let a = 0; a < 360; a += 22.5) {
      const dx = Math.cos((a * Math.PI) / 180), dy = Math.sin((a * Math.PI) / 180);
      const rs = runs((t) => cls(g.toPx(r0.dx + t * dx, g.zN, r0.y + t * dy)), 0, 0.12 * g.W);
      if (!rs.length || rs[0].label !== g.Z.lamp) continue;
      const j = rs.findIndex((r, n) => n > 0 && paint(r.label));
      if (j < 1) continue;
      const gap = Math.abs(rs[j].a - rs[0].b);
      rings.push(gap);
      ringDark.push(gap > 0 ? rs.slice(1, j).filter((r) => r.label === "dark").reduce((s, r) => s + Math.abs(r.b - r.a), 0) / gap : 0);
    }
  }
  // V5-6: a gap that is NOT dark paint (ink / anti-aliasing / unlabelled px: the drawn OUTLINE of the lens) is no bezel —
  // the target has no ring then (V5-5 lamp_ring: 4 render blobs, 0 target px)
  const dark = ringDark.length ? median(ringDark) : 0;
  if (rings.length >= 8 && dark < 0.5) unv("headlight.ring", "W", `the lens -> paint gap (median ${r3(median(rings) / g.W)} W over ${rings.length} walks) is ${r3(100 * dark)} % dark paint: the drawn ink outline of the lens, not a bezel ring`);
  else if (rings.length >= 8) put("headlight.ring", median(rings) / g.W, "W", "headlight rings: radial walks (16 per lamp) on the nose plane from each lamp's centroid — the non-paint gap between the lens and the nose paint (>= 50 % dark paint); median", `${rings.length} walks, ${r3(100 * dark)} % dark`);
  else unv("headlight.ring", "W", `lens -> paint found on ${rings.length} radial walks`);
  // ---- stop arm: its light border (radial walks on the flank plane) and the black post ahead of it
  const reds = zi("signal") < 0 ? [] : components(img, g.cls, [zi("signal")], 20, true).sort((a, b) => b.n - a.n);
  const stop = reds.find((c) => c.x0 > g.xf) ?? null;
  const sc = val("stopArm.centreAt"), sy = val("stopArm.centreY"), sd = val("stopArm.diameter");
  if (stop && sc !== null && sy !== null && sd !== null) {
    const zc = sc * g.Lb, yc = sy * g.H;
    const red = (l) => l === zi("signal");
    const border = [];
    for (let a = 0; a < 360; a += 22.5) {
      const dz = Math.cos((a * Math.PI) / 180), dy = Math.sin((a * Math.PI) / 180);
      const gp = gapAfter((t) => cls(flankP(zc + t * dz, yc + t * dy)), 0, sd * g.Lb, red, (l) => paint(l) || l === "dark" || l === g.Z.glass);
      if (gp) border.push(gp.gap);
    }
    if (border.length >= 6) put("stopArm.border", median(border) / g.Lb, "L", "the stop sign's light rim: radial walks (16) on the flank plane from its centre — the gap between the red face and the paint / black / glass round it; median", `${border.length} walks`);
    else unv("stopArm.border", "L", `red -> surround found on ${border.length} walks`);
    // the post: the first black run walking forward (toward the nose) from the sign's centre, past the rim
    const fwd = runs((z) => cls(flankP(z, yc)), zc, zc - sd * g.Lb);
    const i = fwd.findIndex((r) => r.label === "dark");
    if (i > 0) {
      const pz = (fwd[i].a + fwd[i].b) / 2;
      const col = runs((y) => cls(flankP(pz, y)), yc, yc - 0.4 * g.H);
      const colUp = runs((y) => cls(flankP(pz, y)), yc, yc + 0.3 * g.H);
      const dk = (rs) => (rs[0]?.label === "dark" ? rs[0].b : null);
      const [bot, top] = [dk(col), dk(colUp)];
      const ev = `post column u ${r3(pz / g.Lb)} (run ${r3(fwd[i].a / g.Lb)}..${r3(fwd[i].b / g.Lb)} L); black ${bot === null ? "-" : r3(bot / g.H)}..${top === null ? "-" : r3(top / g.H)} H`;
      if (bot !== null && top !== null) {
        const scan = "the stop-arm post: the first black run walking forward along the flank plane from the sign's centre, then its black run up / down that column";
        put("stopArm.post.at", pz / g.Lb, "L", scan, ev);
        put("stopArm.post.bottom", bot / g.H, "H", scan, ev);
        put("stopArm.post.top", top / g.H, "H", scan, ev);
      } else unv("stopArm.post.at", "L", `the post column's black run is not continuous through the sign's centre (${ev})`);
    } else unv("stopArm.post.at", "L", "no black run ahead of the stop sign");
  }
  // ---- front bumper wrap: the black run from the nose back along the flank plane at the bumper's mid height
  const bft = val("bumper.front.top"), bfh = val("bumper.front.h");
  if (bft !== null && bfh !== null) {
    const vm = (bft - bfh / 2) * g.H;
    const rs = runs((z) => cls(flankP(z, vm)), -0.02 * g.Lb, 0.3 * g.Lb);
    const i = rs.findIndex((r) => r.label === "dark");
    if (i >= 0 && rs[i].a <= 0.02 * g.Lb) put("bumper.front.wrap", Math.max(0, rs[i].b) / g.Lb, "L", "the front bumper's black run from the nose back along the flank plane at its mid height (rs until the first non-black run: the flank paint or the tyre's gap)", `run u ${r3(rs[i].a / g.Lb)}..${r3(rs[i].b / g.Lb)}; next ${rs[i + 1]?.label ?? "-"}`);
    else unv("bumper.front.wrap", "L", "no black run from the nose along the flank at the bumper's mid height");
  }
  // ---- V5-6 rear bumper wrap: the black run from behind the tail forward along the flank plane at the rear bumper's mid
  // height (refs/school_bus.png: the rear bumper is a block round the rear corner, its +X face ~0.2 m along the flank)
  const brt = val("bumper.rear.top"), brh = val("bumper.rear.h");
  if (brt !== null && brh !== null) {
    const vm = (brt - brh / 2) * g.H;
    const rs = runs((z) => cls(flankP(z, vm)), 1.03 * g.Lb, 0.7 * g.Lb);
    const i = rs.findIndex((r) => r.label === "dark");
    if (i >= 0 && rs[i].a >= 0.97 * g.Lb) put("bumper.rear.wrap", Math.max(0, g.Lb - rs[i].b) / g.Lb, "L", "the rear bumper's black run from behind the tail forward along the flank plane at its mid height (until the first non-black run: the flank paint)", `run u ${r3(rs[i].a / g.Lb)}..${r3(rs[i].b / g.Lb)}; next ${rs[i + 1]?.label ?? "-"}`);
    else unv("bumper.rear.wrap", "L", "no black run from the tail along the flank at the rear bumper's mid height");
  }
  // ---- roof tone: the lit roof vs the flank paint, as the renderer's up-facing multiplier (linear light)
  if (zones.roof && zones.body_side) {
    const lin = (v) => { const c = v / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
    const Y = (rgb) => 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2]);
    const t = Y(zones.roof.rgb) / Y(zones.body_side.rgb) - 1;
    put("roof.upTint", t, "ratio", "regions.json roof vs body_side medians: linear-light luminance ratio - 1 (src/geom.js shade upTint lifts +y faces by it); a split is measured when |t| > 0.03", `roof ${zones.roof.hex} (${zones.roof.px} px), body_side ${zones.body_side.hex} (${zones.body_side.px} px)`);
  }
  // ---- marker housings: the black blob round each marker lens pair, rectified on the markers' z plane
  const mY = val("marker.centreY"), mAt = val("marker.at"), mX = val("marker.offsetX"), mD = val("marker.diameter");
  if ([mY, mAt, mX, mD].every((x) => x !== null)) {
    const zp = g.zN - mAt * g.Lb;
    const blacks = components(img, g.cls, [g.Z.black], 100, true).sort((a, b) => a.n - b.n);   // the smallest blob holding the lenses (not the windshield frame)
    const pos = [...new Set(mX.map((x) => Math.sign(x)))].map((s) => mX.filter((x) => Math.sign(x) === s));
    const found = [];
    for (const side of pos) {
      const px = side.map((x) => g.toPx(-g.W / 2 + x * g.W, zp, g.yG + mY * g.H));
      const blob = blacks.find((b) => px.every(([x, y]) => x >= b.x0 - 2 && x <= b.x1 + 2 && y >= b.y0 - 2 && y <= b.y1 + 2));
      if (!blob) continue;
      const pts = blob.pts.map((p) => g.onZPlane(p, zp));
      const a = g.span(pts.map((p) => p.dx)), b = g.span(pts.map((p) => p.y));
      const lensSpan = (Math.max(...side) - Math.min(...side)) * g.W + mD * g.W;
      found.push({ blob, padX: ((a.hi - a.lo) - lensSpan) / 2, padY: ((b.hi - b.lo) - mD * g.W) / 2, h: b.hi - b.lo });
    }
    if (found.length >= 1) {
      const ev = found.map((f) => `${f.blob.n} px box ${f.blob.x0},${f.blob.y0}..${f.blob.x1},${f.blob.y1}: pad x ${r3(f.padX / g.W)} W, y ${r3(f.padY / g.W)} W`).join("; ");
      put("marker.housing.pad", median(found.flatMap((f) => [f.padX, f.padY])) / g.W, "W", "marker housings: the black component holding each lens pair, rectified on the markers' z plane (marker.at); pad = (housing extent - lens extent) / 2 across and up, median", ev);
    } else unv("marker.housing.pad", "W", "no black component holds a marker lens pair");
  }
}

function arg(argv, name, fallback) {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : fallback;
}

export async function main(argv = process.argv.slice(2)) {
  const S = loadSubject(subjectIdFromArgv(argv));
  const file = (name, key) => path.resolve(ROOT, arg(argv, name, S.rel[key]));
  const profile = await measureProfile({ targetFile: file("--target", "target"), regionsFile: file("--regions", "regions"), cameraFile: file("--camera", "camera"), cls: S.cls, variant: S.subject.variant ?? "pickup" });
  for (const [k, e] of Object.entries(profile.keys)) process.stdout.write(`  ${k.padEnd(22)} ${String(e.unverified ? "UNVERIFIED" : e.value).padStart(10)} ${e.unit.padEnd(8)} ${e.unverified ? e.reason : e.evidence.px}\n`);
  for (const [k, e] of Object.entries(profile.inlays)) process.stdout.write(`  inlay ${k.padEnd(12)} ${e ? `${e.zone} (${e.region} ${e.reads ?? "-"}, ${e.px})` : "none"}\n`);
  const layoutFile = file("--layout", "layout");
  if (argv.includes("--check")) {
    const frozen = JSON.parse(fs.readFileSync(layoutFile, "utf8"))._profile;
    const same = JSON.stringify(frozen) === JSON.stringify(profile);
    process.stdout.write(same ? "CHECK PASS _profile\n" : "CHECK FAIL _profile differs from the frozen layout\n");
    if (!same) process.exitCode = 1;
    return profile;
  }
  const outFile = file("--out", "layoutMeasured");
  const merge = (f) => { const j = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : {}; j._profile = profile; fs.writeFileSync(f, `${JSON.stringify(j, null, 2)}\n`); };
  merge(outFile);
  if (argv.includes("--freeze")) { merge(layoutFile); process.stdout.write(`froze _profile into ${path.relative(ROOT, layoutFile)}\n`); }
  return profile;
}

const invoked = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main().catch((e) => { console.error(`measure-profile: ${e.message}`); process.exitCode = 1; });
