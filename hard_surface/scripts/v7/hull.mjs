#!/usr/bin/env node
// WF v8 — VISUAL-HULL CONSISTENCY of a turnaround (scripts/v7/README.md hull.mjs): do the orthographic views describe ONE
// object, and is it the concept's object? No module is involved; nothing is written except --json / --png.
//
//   node scripts/v7/hull.mjs --subject <s> [--views-dir <dir>] [--res <m, 0.02>] [--aniso] [--json <file>] [--png <file>]
//                            [--no-concept] [--max-voxels 6e6] [--refine <f>]
//   node scripts/v7/hull.mjs --subject <s> --write-frame [<file>] [--from hull|facts] [--views-dir <dir>] [--res 0.03] [--dry]
//
// --write-frame (a new subject's setup, scripts/v7/README.md "New subject, once"): the concept registration quad every
// eye reads (registered.mjs registration: subject.json paths.layoutMeasured `_frame.quadPx`) — the object's camera-plane
// extent fitted to the concept foreground bbox (s = mean of the x / y px per metre, centres matched), the class anchor
// face placed with it (rms 0). --from hull (default): the registered visual hull of the live turnaround (after install);
// --from facts: the facts.json dims box, a PROVISIONAL frame so turnaround.mjs gen can measure the first set. Writes
// <file> (default paths.layoutMeasured; a file with keys beyond _comment / _frame is refused). Nothing else runs.
//
// 1. VIEWS: the live turnaround exactly as the eyes load it (scripts/v6/ortho.mjs loadTurnaround: colour families,
//    fgMax / enclosedFg / holes, per-view shift / scale), or --views-dir: the views.json file names read from <dir> with
//    the per-view shift / scale / drift / holes IGNORED (measured on the live images; one note line). Raw masks: drift
//    rects never apply (as the raw IoU, the frame fit and the measure tools).
// 2. REGISTRATION residuals W / L / H (+ Wbbox / Lbbox) per view = reg.residuals, the numbers doctor.mjs turns into its
//    residual-* rows (steplib.mjs residualRows, printed too).
// 3. THE HULL H, author frame (vehicle: nose +z, near flank +x, y up, ground y = 0): the points whose px in EVERY view —
//    orthographic along its registered axes, X = s kr (p . right) + ox, Y = -s ku (p . up) + oy — is 1-px-dilated foreground.
//    A voxel grid over the registered extent (each view's dilated foreground bbox, intersected per world axis) at --res
//    keeps a voxel when its CENTRE is in H (cap --max-voxels: res coarsened and printed). The cells H can reach but that are
//    not interior (kept, all 6 neighbours kept) are refined f x per axis (f = ceil(res x px/m): sub-cells <= 1 view px,
//    the same centre rule), so neither the re-projections nor the concept silhouette carry a res-sized staircase.
// 4. PER VIEW: H re-projected at the view's own px (right / up) and at the sub-cell spacing along its depth axis. IoU vs the
//    view's mask; viewOnly = the view's foreground px H cannot explain (every point on the px's depth line is carved away
//    by another view: a cross-view contradiction) / its foreground px; hullOnly = H px outside the mask / its foreground
//    px (the 1 px dilation ring: ~0.5 % is the floor); the top 5 viewOnly blobs (judge.mjs blobTable: 1 px opening,
//    >= 20 px, share = px / foreground px; bbox in that image's px + metres along its right / up); viewOnlyBlob = the
//    share in ALL such blobs (outline halos and 1-2 px strips drop out).
// 5. CONCEPT (unless --no-concept): H splatted through the solved concept camera + the subject's registration (the path
//    the eyes place a module on: registered.mjs registration / framed = lib.mjs projectPoint), each splat the exact
//    projected cube of a surface sub-cell (+ the interior cells under the refined shell): no pin holes. ONLY the frame
//    knobs (frameScale / frameX / frameY) are fitted, lib.mjs fitFrame on the concept IoU (grid + coordinate search) from
//    the better of identity and a bbox match. IoU = registered.mjs iou vs lib.mjs conceptTarget; conceptOnly = concept
//    foreground outside H's projection / concept foreground (H contains every object consistent with the views, so a
//    consistent set has ~0: THE contradiction number); conceptOnlyBlob = its share in >= 20 px blobs after the 1 px
//    opening; hullOnly (expected > 0: concavities four axis views cannot carve) / concept foreground; the top 5
//    conceptOnly blobs (concept px). The IoU optimum of a SUPERSET shrinks it by part of its excess: on the synthetic
//    consistent set (hull.test.mjs) conceptOnly is 0.00 % at the true frame and 0.28 % at the fitted one, all of it in
//    1-2 px boundary strips (conceptOnlyBlob 0) — read the blob share / blobs for contradictions, the raw share for totals.
// 6. --png: one row — per view grey agree / blue view-only / red hull-only, then the concept (blue concept-only, red
//    hull-only), a one-line caption each. --json: every number above (+ the hullOnly blobs).
// 7. --aniso (always with --json): the SAME H fitted to the concept with per-axis scales — s = {W, H, L}, the views'
//    object over the concept's per author axis (H's coordinates divided by them about its bbox centre before the
//    projection; frameScale 1, frameX / frameY free), fitHullAniso (ANISO: the regularised concept IoU, Nelder-Mead) ->
//    concept.aniso {scale, frame, params, IoU, conceptOnly, conceptOnlyBlob, hullOnly, blobs} and aspect = {HoverW,
//    LoverW, HoverL}: the views' proportions over the concept's - 1 = sH / sW - 1, sL / sW - 1 (+ = the views draw it
//    taller / longer; a too-big or too-tall hull hides in conceptOnly, this shows it). The PNG adds the aniso concept tile.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { anchorFaceOf, conceptRegistration, isDirectClass, subjectFrontOf } from "./conceptreg.mjs";   // WF v10: = subjectRegistration / anchorFace / subjectFront for a vehicle
import { OCCLUDED, SUBJECT, dilate, framed, iou, turnFn } from "../registered.mjs";
import { axisOf, conceptPalette, familyTable, loadTurnaround, maskOptions, pxToView, readImage, readJson, registerViews, viewFamilyTable, viewsFile } from "../v6/ortho.mjs";
import { classFrame } from "../v6/rules.mjs";
import { blobTable } from "../v6/judge.mjs";
import { residualRows } from "./steplib.mjs";
import { conceptTarget, fitFrame, parseArgs, roundFrame } from "./lib.mjs";

/** Defaults: voxel size (m), voxel cap, the keep rule's dilation (px), blob rows per image, the fit raster's supersampling. */
export const HULL = Object.freeze({ res: 0.02, maxVoxels: 6e6, dilate: 1, top: 5, supersample: 2 });
/** The per-view views.json keys measured on the live images (with their `_key` evidence notes), ignored by --views-dir. */
export const MEASURED_KEYS = Object.freeze(["shift", "scale"]);

const KEPT = 1, MAYBE = 2, INTERIOR = 4;
const r1 = (v) => Math.round(v * 10) / 10;
const r3 = (v) => Math.round(v * 1e3) / 1e3;
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const pct = (x, d = 2) => `${(x * 100).toFixed(d)} %`;
const sgnPct = (x) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(1)} %`;
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };

// ---------------------------------------------------------------------------------------------------------------------
// View sets
// ---------------------------------------------------------------------------------------------------------------------

/**
 * views.json without what was measured on the live images: per view `shift` / `scale` (and their `_shift` / `_scale`
 * notes), the per-view `families.holes` seeds (the concept's stay: the concept is the same image), the per-view `drift`
 * rects (never read by the hull anyway). -> { views, holes (families.holes minus the views, or null), dropped: ["top.shift", ...] }
 */
export function stripMeasured(spec) {
  const dropped = [];
  const views = {};
  for (const [name, v] of Object.entries(spec.views)) {
    const out = {};
    for (const [k, x] of Object.entries(v)) {
      if (MEASURED_KEYS.includes(k.replace(/^_/, ""))) { if (!k.startsWith("_")) dropped.push(`${name}.${k}`); } else out[k] = x;
    }
    views[name] = out;
  }
  const holes = {};
  for (const [k, x] of Object.entries(spec.families?.holes ?? {})) { if (spec.views[k]) dropped.push(`holes.${k}`); else holes[k] = x; }
  for (const [k, x] of Object.entries(spec.drift ?? {})) if (Array.isArray(x) && x.length && spec.views[k]) dropped.push(`drift.${k}`);
  return { views, holes: Object.keys(holes).length ? holes : null, dropped };
}

/**
 * Register a view set: each `views` entry's image (views.json {file, right, up[, shift, scale]}) read from `dir` with the
 * family table's mask rule (ortho.mjs readImage + maskOptions) — and `viewTable` ({<view>: {<family>: hex | [hex]}}, the
 * views.json families.viewTable form: that image's own colours of those families; null = none) — then ortho.mjs
 * registerViews. reg.table = table.
 */
export async function registerViewSet({ views, dir, table, anchor, origin, viewTable = null }) {
  const images = {};
  for (const [name, v] of Object.entries(views)) {
    const file = path.join(dir, v.file);
    if (!fs.existsSync(file)) throw new Error(`hull: no view image ${file}`);
    images[name] = await readImage(file, viewFamilyTable(table, { viewTable }, name), maskOptions(table, name));
  }
  const reg = registerViews(images, { views, anchor, origin, body: table.body, ...(table.spanOpen ? { spanOpen: table.spanOpen } : {}) });
  reg.table = table;
  return reg;
}

/**
 * A subject's view set: the live turnaround (ortho.mjs loadTurnaround, cached), or with `viewsDir` the views.json file
 * names read from that folder, registered like loadTurnaround does minus the measured per-view keys (stripMeasured) and
 * minus views.json's families.viewTable (sampled on the live images) — `viewTable` gives that folder's own (e.g.
 * turnaround.mjs familyProposal on its images).
 * @returns {Promise<{reg:object, table:object, spec:object, set:string, notes:string[]}>}
 */
export async function loadViewSet(subjectId, { viewsDir = null, viewTable = null } = {}) {
  if (!viewsDir) {
    const t = await loadTurnaround(subjectId);
    return { reg: t.reg, table: t.table, spec: t.spec, set: "live", notes: [] };
  }
  const spec = readJson(viewsFile(subjectId));
  const S = loadSubject(subjectId);
  const priorFile = path.join(ROOT, "subjects", subjectId, "prior.json");
  const anchor = spec.anchor ?? (fs.existsSync(priorFile) ? readJson(priorFile).anchor : null);
  if (!anchor?.dim || !(anchor.m > 0)) throw new Error(`hull: ${subjectId} views.json has no anchor {dim, m}`);
  const { views, holes, dropped } = stripMeasured(spec);
  const table = familyTable(spec.families?.table ? [] : await conceptPalette(S), { ...(spec.families ?? {}), holes });
  const origin = { ...classFrame(S.klass).origin, ...(spec.origin ?? {}) };
  const reg = await registerViewSet({ views, dir: viewsDir, table, anchor, origin, viewTable });
  const vt = spec.families?.viewTable ? Object.keys(spec.families.viewTable).filter((k) => !k.startsWith("_")) : [];
  const note = `--views-dir ${rel(viewsDir)}: views.json file names read there; per-view shift / scale / drift / holes IGNORED (measured on the live images)${dropped.length ? ` — dropped ${dropped.join(", ")}` : " — none present"}${vt.length ? `; families.viewTable (${vt.join(", ")}) ${viewTable ? "replaced by this folder's own" : "IGNORED"}` : viewTable ? "; this folder's own per-view families" : ""}`;
  return { reg, table, spec, set: rel(viewsDir), notes: [note] };
}

// ---------------------------------------------------------------------------------------------------------------------
// The hull
// ---------------------------------------------------------------------------------------------------------------------

/** A registered view's axes: world index + px map per image axis (X = kx p[ra] + ox, Y = ky p[ua] + oy), depth axis da. */
function axesOf(reg, v) {
  const V = reg.views[v];
  const [ra, sr] = axisOf(V.spec.right);
  const [ua, su] = axisOf(V.spec.up);
  if (ra === ua) throw new Error(`hull: view ${v} right and up run along the same axis`);
  const kr = V.kr ?? 1, ku = V.ku ?? 1;
  return { v, ra, ua, da: 3 - ra - ua, kx: reg.s * kr * sr, ky: -reg.s * ku * su, ox: V.ox, oy: V.oy, w: V.img.w, h: V.img.h };
}

/** px index of world coordinates along one image axis (X = floor(k c + o)), -1 outside [0, len). */
function pxIndex(coords, k, o, len) {
  const out = new Int32Array(coords.length);
  for (let i = 0; i < coords.length; i += 1) { const X = Math.floor(k * coords[i] + o); out[i] = X >= 0 && X < len ? X : -1; }
  return out;
}
const centres = (g0, n, step) => Float64Array.from({ length: n }, (_, i) => g0 + (i + 0.5) * step);

/**
 * The visual hull of a registered view set (reg: ortho.mjs registerViews + reg.views[v].img.fam). See the header (3).
 * @returns {object} { res, res0, f, sub, n, g0, extent, N, kept, boundary, interiorShell, surface (sub-cells splatted),
 *   axes, masks: {v: {fg, keep}}, fcen, flags, sx, sy, sz (surface sub-cell fine indices), icell (interior shell cells), notes }
 */
export function buildHull(reg, { res = HULL.res, maxVoxels = HULL.maxVoxels, refine = null, dil = HULL.dilate } = {}) {
  if (!(res > 0)) throw new Error(`hull: --res ${res} is not a positive size in metres`);
  const notes = [];
  const axes = Object.fromEntries(reg.names.map((v) => [v, axesOf(reg, v)]));
  // the registered extent: each view's dilated foreground bbox in metres, intersected per world axis
  const lo = [-Infinity, -Infinity, -Infinity], hi = [Infinity, Infinity, Infinity], seen = [0, 0, 0];
  for (const v of reg.names) {
    const A = axes[v], { box } = reg.views[v];
    for (const [a, k, o, p0, p1] of [[A.ra, A.kx, A.ox, box.x0 - dil, box.x1 + dil], [A.ua, A.ky, A.oy, box.y0 - dil, box.y1 + dil]]) {
      const w0 = (p0 - o) / k, w1 = (p1 - o) / k;
      lo[a] = Math.max(lo[a], Math.min(w0, w1)); hi[a] = Math.min(hi[a], Math.max(w0, w1)); seen[a] = 1;
    }
  }
  const missing = [0, 1, 2].filter((a) => !seen[a]);
  if (missing.length) throw new Error(`hull: no view measures world axis ${missing.map((a) => "xyz"[a]).join(", ")}`);
  if ([0, 1, 2].some((a) => !(hi[a] > lo[a]))) throw new Error("hull: the views' registered extents do not overlap on every axis");
  const count = (r) => [0, 1, 2].reduce((acc, a) => acc * Math.max(1, Math.ceil((hi[a] - lo[a]) / r - 1e-9)), 1);
  let r = res;
  // WF v10: a small object drawn at many px per metre (a 0.9 m weapon at ~900 px/m): the default cell would need a
  // refinement over the 16 cap (this used to throw) — size the cell at 3 view px instead (what 0.02 m is for a vehicle
  // at ~150 px/m). Only when no --refine is given and the cap would be exceeded: a vehicle's hull is unchanged.
  const kview = Math.max(...reg.names.map((v) => Math.max(Math.abs(axes[v].kx), Math.abs(axes[v].ky))));
  if (refine === null && Math.ceil(r * kview - 1e-9) > 16) {
    r = Math.ceil((3 / kview) * 1e5) / 1e5;
    notes.push(`res ${res} m -> ${r} m: ${kview.toFixed(0)} px/m (a small object: 3 view px per cell)`);
  }
  if (count(r) > maxVoxels) {
    const over = count(r);
    r *= Math.cbrt(over / maxVoxels);
    while (count(r) > maxVoxels) r *= 1.005;
    r = Math.ceil(r * 1e5) / 1e5;
    notes.push(`res ${res} m -> ${r} m: ${(over / 1e6).toFixed(2)} M voxels over the cap ${(maxVoxels / 1e6).toFixed(1)} M`);
  }
  const n = [0, 1, 2].map((a) => Math.max(1, Math.ceil((hi[a] - lo[a]) / r - 1e-9)));
  const g0 = [0, 1, 2].map((a) => (lo[a] + hi[a]) / 2 - n[a] * r / 2);
  const N = n[0] * n[1] * n[2];
  const stride = [n[1] * n[2], n[2], 1];
  const kmax = Math.max(...reg.names.map((v) => Math.max(Math.abs(axes[v].kx), Math.abs(axes[v].ky))));
  const f = refine ?? Math.max(1, Math.ceil(r * kmax - 1e-9));
  if (!(Number.isInteger(f) && f >= 1 && f <= 16)) throw new Error(`hull: --refine ${refine} is not an integer 1..16`);
  const sub = r / f;
  // masks: fg, keep = the keep rule (dil px), wide = keep grown by half a cell footprint (a cell whose centre misses it
  // holds no point of H: only those cells are skipped by the refinement)
  const masks = {};
  for (const v of reg.names) {
    const A = axes[v], { img } = reg.views[v];
    const fg = new Uint8Array(A.w * A.h);
    for (let i = 0; i < fg.length; i += 1) fg[i] = img.fam[i] !== 0 ? 1 : 0;
    const grow = Math.ceil(0.5 * r * Math.max(Math.abs(A.kx), Math.abs(A.ky)) - 1e-9);
    const keep = dilate(fg, A.w, A.h, dil);
    masks[v] = { fg, keep, wide: dilate(fg, A.w, A.h, dil + grow) };
  }
  // coarse carve: the views are axis-aligned, so each one clears whole depth lines of the grid
  const cen = [0, 1, 2].map((a) => centres(g0[a], n[a], r));
  const flags = new Uint8Array(N).fill(KEPT | MAYBE);
  for (const v of reg.names) {
    const A = axes[v], M = masks[v];
    const xi = pxIndex(cen[A.ra], A.kx, A.ox, A.w), yi = pxIndex(cen[A.ua], A.ky, A.oy, A.h);
    const sa = stride[A.ra], sb = stride[A.ua], sd = stride[A.da], nd = n[A.da];
    for (let i = 0; i < n[A.ra]; i += 1) {
      for (let j = 0; j < n[A.ua]; j += 1) {
        const q = xi[i] >= 0 && yi[j] >= 0 ? yi[j] * A.w + xi[i] : -1;
        const clear = (q >= 0 && M.keep[q] ? 0 : KEPT) | (q >= 0 && M.wide[q] ? 0 : MAYBE);
        if (!clear) continue;
        const base = i * sa + j * sb;
        for (let k = 0; k < nd; k += 1) flags[base + k * sd] &= ~clear;
      }
    }
  }
  let kept = 0, boundary = 0;
  for (let ix = 0; ix < n[0]; ix += 1) for (let iy = 0; iy < n[1]; iy += 1) for (let iz = 0; iz < n[2]; iz += 1) {
    const i = ix * stride[0] + iy * stride[1] + iz;
    const fl = flags[i];
    if (fl & KEPT) {
      kept += 1;
      if (ix > 0 && iy > 0 && iz > 0 && ix < n[0] - 1 && iy < n[1] - 1 && iz < n[2] - 1
        && flags[i - stride[0]] & KEPT && flags[i + stride[0]] & KEPT && flags[i - stride[1]] & KEPT && flags[i + stride[1]] & KEPT
        && flags[i - 1] & KEPT && flags[i + 1] & KEPT) { flags[i] = fl | INTERIOR; continue; }
    }
    if (fl & MAYBE) boundary += 1;
  }
  // refinement of the boundary cells (MAYBE, not INTERIOR): f^3 sub-cells, the same centre rule at the fine centres
  const f3 = f * f * f;
  const nf = n.map((x) => x * f);
  if (nf.some((x) => x > 65535)) throw new Error(`hull: ${nf.join(" x ")} sub-cells per axis — lower --refine or raise --res`);
  const fcen = [0, 1, 2].map((a) => centres(g0[a], nf[a], sub));
  const ord = new Int32Array(N).fill(-1);
  const bcell = new Int32Array(boundary);
  for (let i = 0, b = 0; i < N; i += 1) if ((flags[i] & MAYBE) && !(flags[i] & INTERIOR)) { ord[i] = b; bcell[b] = i; b += 1; }
  const V = reg.names.map((v) => ({ ra: axes[v].ra, ua: axes[v].ua, w: axes[v].w, keep: masks[v].keep,
    xi: pxIndex(fcen[axes[v].ra], axes[v].kx, axes[v].ox, axes[v].w), yi: pxIndex(fcen[axes[v].ua], axes[v].ky, axes[v].oy, axes[v].h) }));
  const nv = V.length;
  const occ = new Uint8Array(boundary * f3);
  const F = new Int32Array(3);
  for (let b = 0; b < boundary; b += 1) {
    const i = bcell[b];
    const ix = Math.floor(i / stride[0]), iy = Math.floor((i - ix * stride[0]) / stride[1]), iz = i - ix * stride[0] - iy * stride[1];
    let o = b * f3;
    for (let a = 0; a < f; a += 1) {
      F[0] = ix * f + a;
      for (let c = 0; c < f; c += 1) {
        F[1] = iy * f + c;
        for (let d = 0; d < f; d += 1, o += 1) {
          F[2] = iz * f + d;
          let ok = 1;
          for (let t = 0; t < nv; t += 1) {
            const W = V[t], X = W.xi[F[W.ra]], Y = W.yi[F[W.ua]];
            if (X < 0 || Y < 0 || !W.keep[Y * W.w + X]) { ok = 0; break; }
          }
          occ[o] = ok;
        }
      }
    }
  }
  // state of a sub-cell (fine indices): outside the grid 0; an INTERIOR cell 1; a boundary cell its sub-cell; else 0
  const subState = (fx, fy, fz) => {
    if (fx < 0 || fy < 0 || fz < 0 || fx >= nf[0] || fy >= nf[1] || fz >= nf[2]) return 0;
    const cx = (fx / f) | 0, cy = (fy / f) | 0, cz = (fz / f) | 0;
    const i = cx * stride[0] + cy * stride[1] + cz;
    if (flags[i] & INTERIOR) return 1;
    const b = ord[i];
    return b < 0 ? 0 : occ[b * f3 + ((fx - cx * f) * f + (fy - cy * f)) * f + (fz - cz * f)];
  };
  // the splat set: kept sub-cells with an empty 6-neighbour (the refined surface) + INTERIOR cells next to a refined cell
  let cap = 1 << 16, surface = 0;
  let sx = new Uint16Array(cap), sy = new Uint16Array(cap), sz = new Uint16Array(cap);
  const f2 = f * f;
  for (let b = 0; b < boundary; b += 1) {
    const i = bcell[b];
    const ix = Math.floor(i / stride[0]), iy = Math.floor((i - ix * stride[0]) / stride[1]), iz = i - ix * stride[0] - iy * stride[1];
    let o = b * f3;
    for (let a = 0; a < f; a += 1) for (let c = 0; c < f; c += 1) for (let d = 0; d < f; d += 1, o += 1) {
      if (!occ[o]) continue;
      const fx = ix * f + a, fy = iy * f + c, fz = iz * f + d;
      const open = (a > 0 ? !occ[o - f2] : !subState(fx - 1, fy, fz)) || (a < f - 1 ? !occ[o + f2] : !subState(fx + 1, fy, fz))
        || (c > 0 ? !occ[o - f] : !subState(fx, fy - 1, fz)) || (c < f - 1 ? !occ[o + f] : !subState(fx, fy + 1, fz))
        || (d > 0 ? !occ[o - 1] : !subState(fx, fy, fz - 1)) || (d < f - 1 ? !occ[o + 1] : !subState(fx, fy, fz + 1));
      if (!open) continue;
      if (surface === cap) {
        cap *= 2;
        const gx = new Uint16Array(cap), gy = new Uint16Array(cap), gz = new Uint16Array(cap);
        gx.set(sx); gy.set(sy); gz.set(sz); sx = gx; sy = gy; sz = gz;
      }
      sx[surface] = fx; sy[surface] = fy; sz[surface] = fz; surface += 1;
    }
  }
  const shell = [];
  for (let ix = 1; ix < n[0] - 1; ix += 1) for (let iy = 1; iy < n[1] - 1; iy += 1) for (let iz = 1; iz < n[2] - 1; iz += 1) {
    const i = ix * stride[0] + iy * stride[1] + iz;
    if (!(flags[i] & INTERIOR)) continue;
    if (ord[i - stride[0]] >= 0 || ord[i + stride[0]] >= 0 || ord[i - stride[1]] >= 0 || ord[i + stride[1]] >= 0 || ord[i - 1] >= 0 || ord[i + 1] >= 0) shell.push(i);
  }
  return {
    res0: res, res: r, f, sub, n, g0, N, stride, kept, boundary, interiorShell: shell.length, surface,
    extent: Object.fromEntries([0, 1, 2].map((a) => ["xyz"[a], [r3(g0[a]), r3(g0[a] + n[a] * r)]])),
    axes, masks: Object.fromEntries(reg.names.map((v) => [v, { fg: masks[v].fg, keep: masks[v].keep }])), fcen, flags,
    sx: sx.subarray(0, surface), sy: sy.subarray(0, surface), sz: sz.subarray(0, surface), icell: Int32Array.from(shell), notes, subState,
  };
}

/**
 * H re-projected into view v at the view's own px: a px (its centre's right / up metres) is in H's projection when its own
 * keep mask holds and some depth sample (the sub-cell centres along the view's depth axis) passes every other view.
 * The other views share either the whole image plane (per-px test) or one image axis + the depth (bitsets over depth).
 * @returns {Uint8Array} w x h, 1 = H's projection
 */
export function reprojectView(reg, hull, v) {
  const A = hull.axes[v];
  const { w, h } = A;
  const depth = hull.fcen[A.da];
  const nd = depth.length;
  const words = (nd + 31) >>> 5;
  const colW = Float64Array.from({ length: w }, (_, X) => (X + 0.5 - A.ox) / A.kx);
  const rowW = Float64Array.from({ length: h }, (_, Y) => (Y + 0.5 - A.oy) / A.ky);
  const along = (B, a) => (a === B.ra ? [B.kx, B.ox, B.w] : [B.ky, B.oy, B.h]);   // view B's px map of world axis a
  const plane = [], bits = [];
  for (const u of reg.names) {
    if (u === v) continue;
    const B = hull.axes[u], keep = hull.masks[u].keep;
    const has = (a) => a === B.ra || a === B.ua;
    if (has(A.ra) && has(A.ua)) {
      // the same image plane (front / rear): per-px lookup
      const ci = pxIndex(colW, ...along(B, A.ra)), ri = pxIndex(rowW, ...along(B, A.ua));
      plane.push({ keep, bw: B.w, ci, ri, colIsX: A.ra === B.ra });
    } else {
      // one shared image axis p + the depth: bitset over the depth samples per px along p
      const p = has(A.ra) ? A.ra : A.ua;
      const coords = p === A.ra ? colW : rowW;
      const pi = pxIndex(coords, ...along(B, p)), di = pxIndex(depth, ...along(B, A.da));
      const pIsX = p === B.ra;
      const tab = new Uint32Array(coords.length * words);
      for (let i = 0; i < coords.length; i += 1) {
        if (pi[i] < 0) continue;
        for (let k = 0; k < nd; k += 1) {
          if (di[k] < 0) continue;
          const X = pIsX ? pi[i] : di[k], Y = pIsX ? di[k] : pi[i];
          if (keep[Y * B.w + X]) tab[i * words + (k >>> 5)] |= 1 << (k & 31);
        }
      }
      bits.push({ tab, byCol: p === A.ra });
    }
  }
  const own = hull.masks[v].keep;
  const out = new Uint8Array(w * h);
  for (let Y = 0; Y < h; Y += 1) {
    for (let X = 0; X < w; X += 1) {
      const i = Y * w + X;
      if (!own[i]) continue;
      let ok = true;
      for (const P of plane) {
        const bx = P.colIsX ? P.ci[X] : P.ri[Y], by = P.colIsX ? P.ri[Y] : P.ci[X];
        if (bx < 0 || by < 0 || !P.keep[by * P.bw + bx]) { ok = false; break; }
      }
      if (!ok) continue;
      if (!bits.length) { out[i] = 1; continue; }
      let any = 0;
      for (let q = 0; q < words && !any; q += 1) {
        let m = 0xffffffff;
        for (const Bt of bits) { m &= Bt.tab[(Bt.byCol ? X : Y) * words + q]; if (!m) break; }
        any = m;
      }
      if (any) out[i] = 1;
    }
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------------------
// Concept splat + frame fit
// ---------------------------------------------------------------------------------------------------------------------

/** Author-frame linear px map of a (framed) concept registration: X = ax . p + bx, Y = ay . p + by (turnDeg folded in). */
export function conceptMap(creg) {
  const back = turnFn(-(creg.turnDeg ?? 0));   // render frame -> author frame (the inverse quarter turn)
  const R = back(creg.basis.right), U = back(creg.basis.up);
  return { ax: R.map((c) => creg.s * c), bx: creg.ox, ay: U.map((c) => -creg.s * c), by: creg.oy };
}

/** The projected footprint of an axis-aligned cube of side `a` (centre at 0): its convex hull as half-planes + bbox. */
function footprint(map, a) {
  const pts = [];
  for (const x of [-a / 2, a / 2]) for (const y of [-a / 2, a / 2]) for (const z of [-a / 2, a / 2]) {
    pts.push([map.ax[0] * x + map.ax[1] * y + map.ax[2] * z, map.ay[0] * x + map.ay[1] * y + map.ay[2] * z]);
  }
  pts.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
  const cr = (o, p, q) => (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0]);
  const lower = [], upper = [];
  for (const p of pts) { while (lower.length >= 2 && cr(lower[lower.length - 2], lower[lower.length - 1], p) <= 1e-12) lower.pop(); lower.push(p); }
  for (const p of [...pts].reverse()) { while (upper.length >= 2 && cr(upper[upper.length - 2], upper[upper.length - 1], p) <= 1e-12) upper.pop(); upper.push(p); }
  const poly = [...lower.slice(0, -1), ...upper.slice(0, -1)];
  const m = poly.length;
  const nx = new Float64Array(m), ny = new Float64Array(m), d = new Float64Array(m);
  for (let e = 0; e < m; e += 1) {
    const p = poly[e], q = poly[(e + 1) % m], ex = q[0] - p[0], ey = q[1] - p[1];
    nx[e] = ey; ny[e] = -ex; d[e] = ey * p[0] - ex * p[1] + 1e-7 * Math.hypot(ex, ey);   // inside: n . t <= d (edges shared by neighbours: both)
  }
  return { m, nx, ny, d, x0: Math.min(...pts.map((p) => p[0])), x1: Math.max(...pts.map((p) => p[0])), y0: Math.min(...pts.map((p) => p[1])), y1: Math.max(...pts.map((p) => p[1])) };
}

/** Stamp a footprint centred at (cx, cy) px: every px whose centre lies inside it. */
function stamp(out, W, H, cx, cy, P) {
  const xa = Math.max(0, Math.ceil(cx + P.x0 - 0.5)), xb = Math.min(W - 1, Math.floor(cx + P.x1 - 0.5));
  const ya = Math.max(0, Math.ceil(cy + P.y0 - 0.5)), yb = Math.min(H - 1, Math.floor(cy + P.y1 - 0.5));
  for (let py = ya; py <= yb; py += 1) {
    const qy = py + 0.5 - cy;
    for (let px = xa; px <= xb; px += 1) {
      const qx = px + 0.5 - cx;
      let e = 0;
      while (e < P.m && P.nx[e] * qx + P.ny[e] * qy <= P.d[e]) e += 1;
      if (e === P.m) out[py * W + px] = 1;
    }
  }
}

/** H's silhouette through a linear map ({ax, bx, ay, by}: author point -> px) on a W x H raster: the refined surface splat. */
export function splatHull(hull, map, W, H) {
  const out = new Uint8Array(W * H);
  const dot = (a, p) => a[0] * p[0] + a[1] * p[1] + a[2] * p[2];
  const { sub, res, g0, sx, sy, sz } = hull;
  const Ps = footprint(map, sub);
  const c0 = g0.map((g) => g + sub / 2);
  const X0 = dot(map.ax, c0) + map.bx, Y0 = dot(map.ay, c0) + map.by;
  const dX = map.ax.map((c) => c * sub), dY = map.ay.map((c) => c * sub);
  for (let m = 0; m < sx.length; m += 1) {
    stamp(out, W, H, X0 + sx[m] * dX[0] + sy[m] * dX[1] + sz[m] * dX[2], Y0 + sx[m] * dY[0] + sy[m] * dY[1] + sz[m] * dY[2], Ps);
  }
  const Pc = footprint(map, res);
  const [sa, sb] = hull.stride;
  for (const i of hull.icell) {
    const ix = Math.floor(i / sa), iy = Math.floor((i - ix * sa) / sb), iz = i - ix * sa - iy * sb;
    const p = [g0[0] + (ix + 0.5) * res, g0[1] + (iy + 0.5) * res, g0[2] + (iz + 0.5) * res];
    stamp(out, W, H, dot(map.ax, p) + map.bx, dot(map.ay, p) + map.by, Pc);
  }
  return out;
}

/** bbox {x0, y0, x1, y1} (exclusive ends) of the set px of a mask (by = the value that counts), or null. */
function maskBox(mask, W, H, by = 1) {
  let x0 = W, y0 = H, x1 = -1, y1 = -1;
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) if (mask[y * W + x] === by) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return x1 < 0 ? null : { x0, y0, x1: x1 + 1, y1: y1 + 1 };
}

/**
 * Fit ONLY the concept frame knobs {scale, tx, ty} (registered.mjs framed: about the anchor quad's centre, shifts in px at
 * a 1024 px target) for H: lib.mjs fitFrame (grid + coordinate search) on the concept IoU. H is splatted once at the
 * identity frame on a `q` x supersampled raster; a frame's IoU samples it at each concept px centre mapped back through
 * the similarity. Start: the better of identity and the bbox match.
 */
export async function fitHullFrame(hull, creg, T, W, H, { q = HULL.supersample, grid = true, search = true } = {}) {
  const m0 = conceptMap(creg);
  // identity-frame raster over the projected grid box (+2 px)
  let bx0 = Infinity, by0 = Infinity, bx1 = -Infinity, by1 = -Infinity;
  for (const x of [hull.g0[0], hull.g0[0] + hull.n[0] * hull.res]) for (const y of [hull.g0[1], hull.g0[1] + hull.n[1] * hull.res]) for (const z of [hull.g0[2], hull.g0[2] + hull.n[2] * hull.res]) {
    const X = m0.ax[0] * x + m0.ax[1] * y + m0.ax[2] * z + m0.bx, Y = m0.ay[0] * x + m0.ay[1] * y + m0.ay[2] * z + m0.by;
    bx0 = Math.min(bx0, X); bx1 = Math.max(bx1, X); by0 = Math.min(by0, Y); by1 = Math.max(by1, Y);
  }
  const OX = Math.floor(bx0) - 2, OY = Math.floor(by0) - 2;
  const RW = Math.ceil((bx1 + 2 - OX) * q), RH = Math.ceil((by1 + 2 - OY) * q);
  const R = splatHull(hull, { ax: m0.ax.map((c) => c * q), bx: (m0.bx - OX) * q, ay: m0.ay.map((c) => c * q), by: (m0.by - OY) * q }, RW, RH);
  const rb = maskBox(R, RW, RH);
  if (!rb) throw new Error("hull: the hull is empty — the views share no foreground");
  const hb = { x0: OX + rb.x0 / q, x1: OX + rb.x1 / q, y0: OY + rb.y0 / q, y1: OY + rb.y1 / q };   // identity-frame hull bbox (target px)
  const tb = maskBox(T, W, H, SUBJECT);
  if (!tb) throw new Error("hull: the concept target has no foreground");
  const quad = creg.quadPx;
  const cx = quad.reduce((a, p) => a + p[0], 0) / quad.length, cy = quad.reduce((a, p) => a + p[1], 0) / quad.length;
  const k = (creg.targetW ?? 1024) / 1024;
  const colIdx = new Int32Array(W), rowIdx = new Int32Array(H);
  const f = async (fr) => {
    const sc = fr.scale, Tx = fr.tx * k, Ty = fr.ty * k;
    const xa = Math.max(0, Math.min(tb.x0, Math.floor(cx + sc * (hb.x0 - cx) + Tx))), xb = Math.min(W, Math.max(tb.x1, Math.ceil(cx + sc * (hb.x1 - cx) + Tx)));
    const ya = Math.max(0, Math.min(tb.y0, Math.floor(cy + sc * (hb.y0 - cy) + Ty))), yb = Math.min(H, Math.max(tb.y1, Math.ceil(cy + sc * (hb.y1 - cy) + Ty)));
    for (let X = xa; X < xb; X += 1) { const c = Math.floor((cx + (X + 0.5 - cx - Tx) / sc - OX) * q); colIdx[X] = c >= 0 && c < RW ? c : -1; }
    for (let Y = ya; Y < yb; Y += 1) { const c = Math.floor((cy + (Y + 0.5 - cy - Ty) / sc - OY) * q); rowIdx[Y] = c >= 0 && c < RH ? c * RW : -1; }
    let I = 0, U = 0;
    for (let Y = ya; Y < yb; Y += 1) {
      const rr = rowIdx[Y], base = Y * W;
      for (let X = xa; X < xb; X += 1) {
        const t = T[base + X];
        if (t === OCCLUDED) continue;
        const m = rr >= 0 && colIdx[X] >= 0 && R[rr + colIdx[X]] === 1;
        if (t === SUBJECT) { U += 1; if (m) I += 1; } else if (m) U += 1;
      }
    }
    return U ? I / U : 0;
  };
  const identity = { scale: 1, tx: 0, ty: 0 };
  const sc = Math.sqrt(((tb.x1 - tb.x0) / (hb.x1 - hb.x0)) * ((tb.y1 - tb.y0) / (hb.y1 - hb.y0)));
  const bboxStart = { scale: sc, tx: ((tb.x0 + tb.x1) / 2 - cx - sc * ((hb.x0 + hb.x1) / 2 - cx)) / k, ty: ((tb.y0 + tb.y1) / 2 - cy - sc * ((hb.y0 + hb.y1) / 2 - cy)) / k };
  const vi = await f(identity), vb = await f(bboxStart);
  const start = vb > vi + 1e-6 ? { from: "bbox", frame: bboxStart, v: vb } : { from: "identity", frame: identity, v: vi };
  // search false (hull.mjs --write-frame --frame-refine box): the bbox match itself, no IoU search
  const r = search ? await fitFrame(f, start.frame, { grid }) : { frame: bboxStart, v: vb };
  return { start, identity: { frame: identity, v: vi }, bbox: { frame: bboxStart, v: vb }, frame: r.frame, v: r.v };
}

// ---------------------------------------------------------------------------------------------------------------------
// The anisotropic fit (--aniso): the views' object against the concept's proportions
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The per-axis fit: x = [ln sigma, ln aH, ln aL, frameX / 100, frameY / 100] (s = {W: sigma, H: sigma aH, L: sigma aL}),
 * maximising the concept IoU - lambda (ln^2 aH + ln^2 aL) by Nelder-Mead (a restart from its optimum each stage):
 * `coarse` on point splats of the coarse proxy, then `fine` on point splats of the refined surface, each on the concept
 * grid downsampled by q (a power of 2 with the points <= `spacing` px apart: a point splat that dense fills the
 * silhouette), only the cells / sub-cells with a camera-facing exposed face (the silhouette of a union of cubes is the
 * projection of those faces; a positive per-axis scale keeps a face camera-facing). The reported numbers use the exact
 * footprint splat (splatHull) at the fitted scales.
 * Why Nelder-Mead and the regulariser: an oblique concept camera sees W foreshortened, so W against (H, L) is weakly
 * determined — the plain IoU has a flat valley along it (garbage_truck: aH 0.91 .. 0.96 within 0.001 IoU) where the
 * coordinate search of fitFrame stalls at arbitrary points (H / W +5 .. +8 % on one set). lambda 0.25 costs 0.0023 IoU
 * per 10 % of aspect: the least distortion that explains the concept is chosen inside such a valley; a real
 * disagreement moves the IoU far more. Calibration (research/v7/HULL-BASELINE.md "aspect"): the synthetic set of
 * hull.test.mjs H / W +1.0 %, L / W -0.4 %, stretched 10 % in H -> +10.0 / -1.2 %; the five golds' own views vs their own
 * concept renders (truth 0) H / W -1.7 .. +0.1 %, L / W -1.3 .. -0.4 %; the taxi's views stretched 10 % in H -> +8.5 %
 * (the W valley); the same live set at res 0.02 / 0.025 / 0.03 moves by up to 2 pts — read aspect to about +-2 pts.
 */
export const ANISO = Object.freeze({
  lambda: 0.25,
  range: 0.45,
  spacing: 0.7,
  coarse: Object.freeze({ step: [0.02, 0.04, 0.04, 0.08, 0.08], iters: 400, tol: 1e-7 }),
  fine: Object.freeze({ step: [0.005, 0.01, 0.01, 0.02, 0.02], iters: 250, tol: 1e-7 }),
});

/** H's bbox centre in author metres (the grid extent's centre): the point the per-axis scales act about. */
export const hullCentre = (hull) => hull.g0.map((g, a) => g + (hull.n[a] * hull.res) / 2);

/**
 * The concept px map of H scaled per axis: the author coordinates p -> c3 + (p - c3) / s (s = {W, H, L}: the views' object
 * over the concept's along x / y / z; c3 = hullCentre), then the registered concept camera (frameScale 1: the three scales
 * carry it) shifted by frameX / frameY (tx, ty: px at a 1024 px target, as registered.mjs framed). A linear map, so
 * splatHull / footprint project the scaled sub-cells exactly.
 */
export function anisoMap(creg, c3, s, tx = 0, ty = 0) {
  const m0 = conceptMap(framed(creg, { scale: 1, tx, ty }));
  const inv = [1 / s.W, 1 / s.H, 1 / s.L];
  const lin = (a) => a.map((c, k) => c * inv[k]);
  const off = (a) => a.reduce((acc, c, k) => acc + c * c3[k] * (1 - inv[k]), 0);
  return { ax: lin(m0.ax), bx: m0.bx + off(m0.ax), ay: lin(m0.ay), by: m0.by + off(m0.ay) };
}

/** The author-frame direction toward the concept camera (right x up of conceptMap's axes). */
export function towardCamera(creg) {
  const m = conceptMap(creg);
  const R = m.ax, U = m.ay.map((c) => -c);
  return [R[1] * U[2] - R[2] * U[1], R[2] * U[0] - R[0] * U[2], R[0] * U[1] - R[1] * U[0]];
}

/**
 * Point sets of H (author metres) that fill its silhouette seen from `back` (the direction toward the camera; null = any):
 * "coarse" = the centres of the KEPT cells with an exposed face toward it, "fine" = the refined surface sub-cells with an
 * exposed face toward it + the interior shell's cells. -> {x, y, z: Float32Array, n, step (the sample spacing, m)}
 */
export function hullPoints(hull, which, back = null) {
  const { n, stride, flags, res, g0 } = hull;
  const signs = [0, 1, 2].map((a) => (!back || Math.abs(back[a]) < 1e-9 ? [1, -1] : [Math.sign(back[a])]));
  const xs = [], ys = [], zs = [];
  const cell = (i) => { const ix = Math.floor(i / stride[0]), iy = Math.floor((i - ix * stride[0]) / stride[1]), iz = i - ix * stride[0] - iy * stride[1]; xs.push(g0[0] + (ix + 0.5) * res); ys.push(g0[1] + (iy + 0.5) * res); zs.push(g0[2] + (iz + 0.5) * res); };
  if (which === "coarse") {
    const c = [0, 0, 0];
    for (c[0] = 0; c[0] < n[0]; c[0] += 1) for (c[1] = 0; c[1] < n[1]; c[1] += 1) for (c[2] = 0; c[2] < n[2]; c[2] += 1) {
      const i = c[0] * stride[0] + c[1] * stride[1] + c[2];
      if (!(flags[i] & KEPT)) continue;
      let open = false;
      for (let a = 0; a < 3 && !open; a += 1) for (const sg of signs[a]) {
        const j = c[a] + sg;
        if (j < 0 || j >= n[a] || !(flags[i + sg * stride[a]] & KEPT)) { open = true; break; }
      }
      if (open) cell(i);
    }
    return { x: Float32Array.from(xs), y: Float32Array.from(ys), z: Float32Array.from(zs), n: xs.length, step: res };
  }
  const { sub, sx, sy, sz, subState } = hull;
  const px = [], py = [], pz = [];
  const F = [0, 0, 0];
  for (let m = 0; m < sx.length; m += 1) {
    F[0] = sx[m]; F[1] = sy[m]; F[2] = sz[m];
    let open = false;
    for (let a = 0; a < 3 && !open; a += 1) for (const sg of signs[a]) {
      F[a] += sg;
      const st = subState(F[0], F[1], F[2]);
      F[a] -= sg;
      if (!st) { open = true; break; }
    }
    if (open) { px.push(g0[0] + (sx[m] + 0.5) * sub); py.push(g0[1] + (sy[m] + 0.5) * sub); pz.push(g0[2] + (sz[m] + 0.5) * sub); }
  }
  for (const i of hull.icell) cell(i);
  return { x: Float32Array.from([...px, ...xs]), y: Float32Array.from([...py, ...ys]), z: Float32Array.from([...pz, ...zs]), n: px.length + xs.length, step: sub };
}

/** The three-state target on a grid downsampled by q (the sample at each q x q block's centre) + its SUBJECT count. */
function downTarget(T, W, H, q) {
  if (q === 1) { let nT = 0; for (let i = 0; i < T.length; i += 1) if (T[i] === SUBJECT) nT += 1; return { T, W, H, q, nT }; }
  const Wq = Math.floor(W / q), Hq = Math.floor(H / q), o = q >> 1;
  const out = new Uint8Array(Wq * Hq);
  let nT = 0;
  for (let y = 0; y < Hq; y += 1) for (let x = 0; x < Wq; x += 1) { const t = T[(y * q + o) * W + x * q + o]; out[y * Wq + x] = t; if (t === SUBJECT) nT += 1; }
  return { T: out, W: Wq, H: Hq, q, nT };
}

/**
 * Point-splat IoU on a downsampled target: each point's projected px (map in full-res px, / q) set in a reusable raster,
 * then read and cleared over the touched bbox; OCCLUDED px count in neither I nor U (registered.mjs iou).
 */
function pointIoU(P, map, D, raster) {
  const { T, W, H, q, nT } = D;
  const k = 1 / q;
  const ax0 = map.ax[0] * k, ax1 = map.ax[1] * k, ax2 = map.ax[2] * k, bx = map.bx * k;
  const ay0 = map.ay[0] * k, ay1 = map.ay[1] * k, ay2 = map.ay[2] * k, by = map.by * k;
  let x0 = W, y0 = H, x1 = -1, y1 = -1;
  const { x, y, z, n } = P;
  for (let i = 0; i < n; i += 1) {
    const X = Math.floor(ax0 * x[i] + ax1 * y[i] + ax2 * z[i] + bx), Y = Math.floor(ay0 * x[i] + ay1 * y[i] + ay2 * z[i] + by);
    if (X < 0 || Y < 0 || X >= W || Y >= H) continue;
    raster[Y * W + X] = 1;
    if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y;
  }
  let I = 0, E = 0;
  for (let yy = y0; yy <= y1; yy += 1) {
    const base = yy * W;
    for (let xx = x0; xx <= x1; xx += 1) {
      const i = base + xx;
      if (!raster[i]) continue;
      raster[i] = 0;
      const t = T[i];
      if (t === SUBJECT) I += 1; else if (t !== OCCLUDED) E += 1;
    }
  }
  return nT + E ? I / (nT + E) : 0;
}

/** The smallest power of 2 q with step x px/m / q <= spacing. */
const gridStep = (step, pxPerM, spacing) => { let q = 1; while (step * pxPerM / q > spacing && q < 16) q *= 2; return q; };

/** Nelder-Mead MAXIMISING f over R^n from x0 (initial simplex x0 + step_i e_i). -> {x, v, evals} */
export function nelderMead(f, x0, step, { iters = 300, tol = 1e-7 } = {}) {
  const n = x0.length;
  let evals = 0;
  const F = (x) => { evals += 1; return f(x); };
  let S = [x0, ...x0.map((_, i) => x0.map((v, j) => (i === j ? v + step[i] : v)))].map((x) => ({ x, v: F(x) }));
  for (let it = 0; it < iters; it += 1) {
    S.sort((a, b) => b.v - a.v);
    const best = S[0], worst = S[n];
    if (best.v - worst.v < tol) break;
    const c = new Array(n).fill(0);
    for (let i = 0; i < n; i += 1) for (let j = 0; j < n; j += 1) c[j] += S[i].x[j] / n;
    const at = (t) => c.map((cj, j) => cj + t * (worst.x[j] - cj));
    const r = at(-1), vr = F(r);
    if (vr > best.v) { const e = at(-2), ve = F(e); S[n] = ve > vr ? { x: e, v: ve } : { x: r, v: vr }; continue; }
    if (vr > S[n - 1].v) { S[n] = { x: r, v: vr }; continue; }
    const k = vr > worst.v ? at(-0.5) : at(0.5), vk = F(k);
    if (vk > Math.max(vr, worst.v)) { S[n] = { x: k, v: vk }; continue; }
    S = S.map((p, i) => (i === 0 ? p : { x: p.x.map((xj, j) => best.x[j] + 0.5 * (xj - best.x[j])), v: 0 })).map((p, i) => (i === 0 ? p : { x: p.x, v: F(p.x) }));
  }
  S.sort((a, b) => b.v - a.v);
  return { x: S[0].x, v: S[0].v, evals };
}

const toParams = (x) => ({ sigma: Math.exp(x[0]), aH: Math.exp(x[1]), aL: Math.exp(x[2]), tx: x[3] * 100, ty: x[4] * 100 });
const toVector = (p) => [Math.log(p.sigma), Math.log(p.aH), Math.log(p.aL), p.tx / 100, p.ty / 100];

/**
 * The regularised concept IoU of H scaled per axis on the point sets of one stage: fn(params) -> {iou, v} (v = the
 * objective). which = "coarse" | "fine"; q from ANISO.spacing and the concept's px per metre.
 */
export function anisoObjective(hull, creg, T, W, H, which = "fine", { lambda = ANISO.lambda, spacing = ANISO.spacing, pxPerM = null, range = ANISO.range } = {}) {
  const c3 = hullCentre(hull);
  const m0 = conceptMap(creg);
  const ppm = pxPerM ?? Math.max(...[0, 1, 2].map((a) => Math.hypot(m0.ax[a], m0.ay[a])));
  const P = hullPoints(hull, which, towardCamera(creg));
  const q = gridStep(P.step, ppm, spacing);
  const D = downTarget(T, W, H, q);
  const raster = new Uint8Array(D.W * D.H);
  const sOf = (p) => ({ W: p.sigma, H: p.sigma * p.aH, L: p.sigma * p.aL });
  const lim = Math.log(1 + range);
  const fn = (p) => {
    const lh = Math.log(p.aH), ll = Math.log(p.aL);
    if (Math.abs(lh) > lim || Math.abs(ll) > lim) return { iou: 0, v: -1 };
    const iou = pointIoU(P, anisoMap(creg, c3, sOf(p), p.tx, p.ty), D, raster);
    return { iou, v: iou - lambda * (lh * lh + ll * ll) };
  };
  return { fn, q, points: P.n, c3, sOf };
}

/**
 * Fit H to the concept with per-axis scales (ANISO: Nelder-Mead on the regularised IoU, coarse then fine point splats),
 * started from the isotropic fit `iso` ({scale, tx, ty}: sigma = 1 / scale, aH = aL = 1, the shift converted so both
 * maps coincide). aspect = the views' object's H / W and L / W over the concept's - 1 = aH - 1, aL - 1 (+ = the views
 * draw it taller / longer).
 */
export function fitHullAniso(hull, creg, T, W, H, iso, { lambda = ANISO.lambda, coarse = ANISO.coarse, fine = ANISO.fine, from = null } = {}) {
  const t0 = Date.now();
  const c3 = hullCentre(hull);
  const k = (creg.targetW ?? 1024) / 1024;
  const quad = creg.quadPx;
  const cx = quad.reduce((a, p) => a + p[0], 0) / quad.length, cy = quad.reduce((a, p) => a + p[1], 0) / quad.length;
  const m0 = conceptMap(creg);
  const P3 = [m0.ax[0] * c3[0] + m0.ax[1] * c3[1] + m0.ax[2] * c3[2] + m0.bx, m0.ay[0] * c3[0] + m0.ay[1] * c3[1] + m0.ay[2] * c3[2] + m0.by];
  const f = iso.scale;
  const start = { sigma: 1 / f, aH: 1, aL: 1, tx: iso.tx + ((1 - f) * (cx - P3[0])) / k, ty: iso.ty + ((1 - f) * (cy - P3[1])) / k };
  const pxPerM = Math.max(...[0, 1, 2].map((a) => Math.hypot(m0.ax[a], m0.ay[a]))) * f;
  const search = {};
  // a warm start (`from`: another set's fitted params — the set before a repair) skips the coarse stage, starts the fine one
  // with half its simplex and HOLDS sigma (the W scale): a repair replaces one of four views, and with the common W scale
  // held the fit cannot slide along the flat W valley — the aspect change is the new view's, not the fit's own spread
  let x = toVector(from ?? start);
  const lock = !!from;
  const x0Sigma = x[0];
  const full = (v) => (lock ? [x0Sigma, ...v] : v);
  const stages = from ? [["fine", { ...fine, step: fine.step.map((d) => d / 2) }]] : [["coarse", coarse], ["fine", fine]];
  for (const [name, cfg] of stages) {
    const t = Date.now();
    const O = anisoObjective(hull, creg, T, W, H, name, { lambda, pxPerM });
    const g = (v) => O.fn(toParams(full(v))).v;
    const v0 = lock ? x.slice(1) : x, st0 = lock ? cfg.step.slice(1) : cfg.step;
    const a = nelderMead(g, v0, st0, cfg);
    const b = nelderMead(g, a.x, st0.map((d) => d / 2), cfg);   // one restart from the optimum
    x = full(b.v >= a.v ? b.x : a.x);
    const r = O.fn(toParams(x));
    search[name] = { q: O.q, points: O.points, evals: a.evals + b.evals, iou: r4(r.iou), ms: Date.now() - t, ...(lock ? { sigmaHeld: +Math.exp(x0Sigma).toFixed(6) } : {}) };
  }
  const p = toParams(x);
  const s = { W: p.sigma, H: p.sigma * p.aH, L: p.sigma * p.aL };
  return { c3, start, params: p, s, frame: { tx: p.tx, ty: p.ty }, lambda, warm: !!from, aspect: { HoverW: p.aH - 1, LoverW: p.aL - 1, HoverL: p.aH / p.aL - 1 }, search: { ...search, ms: Date.now() - t0 } };
}

// ---------------------------------------------------------------------------------------------------------------------
// Numbers
// ---------------------------------------------------------------------------------------------------------------------

/** IoU / only / hullOnly of a reference fg vs H's projection (care 0 = not scored: the concept's OCCLUDED px). */
function compare(ref, hull, care = null) {
  let fg = 0, hp = 0, inter = 0, union = 0, only = 0, extra = 0;
  for (let i = 0; i < ref.length; i += 1) {
    if (care && !care[i]) continue;
    const a = ref[i] === 1, b = hull[i] === 1;
    if (a) fg += 1;
    if (b) hp += 1;
    if (a && b) inter += 1;
    if (a || b) union += 1;
    if (a && !b) only += 1;
    if (b && !a) extra += 1;
  }
  return { fg, hp, iou: union ? inter / union : 0, onlyPx: only, extraPx: extra, only: fg ? only / fg : 0, extra: fg ? extra / fg : 0 };
}

/**
 * judge.mjs blobTable on ref vs hull ("missing" = reference-only, "extra" = hull-only; part fields dropped): the top rows
 * per kind + onlyPx = the px of ALL reference-only blobs (>= 20 px after the 1 px opening: outline halos, thin fit strips
 * and staircase px drop out).
 */
function blobRows(refFg, hullFg, w, h, care, refPx, place, top = HULL.top) {
  const partId = new Int32Array(w * h);
  for (let i = 0; i < partId.length; i += 1) partId[i] = hullFg[i] ? 0 : -1;
  const rows = blobTable({ refFg, modelFg: hullFg, partId, w, h, care, parts: [{ id: "hull" }], refPx, place, top: Infinity });
  const strip = ({ kind: _k, part: _p, ...b }) => b;
  const only = rows.filter((b) => b.kind === "missing");
  return { only: only.slice(0, top).map(strip), extra: rows.filter((b) => b.kind === "extra").slice(0, top).map(strip), onlyPx: only.reduce((a, b) => a + b.px, 0) };
}

/**
 * Everything: the hull, per view IoU / viewOnly / hullOnly / blobs, the concept (when given: {T three-state target, creg
 * registration (registered.mjs registration), w, h}) with its fitted frame. rasters (not in the JSON): per image {fg, hull}.
 */
export async function hullReport({ reg, concept = null, res = HULL.res, maxVoxels = HULL.maxVoxels, refine = null, aniso = false }) {
  const t0 = Date.now();
  const hull = buildHull(reg, { res, maxVoxels, refine });
  const out = {
    s: r4(reg.s), dims: Object.fromEntries(Object.entries(reg.dims).map(([k, v]) => [k, r4(v)])), residuals: reg.residuals,
    doctor: residualRows(reg.residuals).map(({ level, id, data, text }) => ({ level, id, ...(data ? { data } : {}), text })),
    res: { asked: hull.res0, used: hull.res, refine: hull.f, sub: r4(hull.sub) },
    grid: { n: hull.n, voxels: hull.N, kept: hull.kept, refined: hull.boundary, surfaceSubCells: hull.surface, interiorShell: hull.interiorShell, extent: hull.extent },
    notes: [...hull.notes], views: {}, concept: null, ...(aniso && concept ? { aspect: null } : {}),
  };
  const rasters = { views: {}, concept: null };
  for (const v of reg.names) {
    const A = hull.axes[v];
    const fg = hull.masks[v].fg;
    const hm = reprojectView(reg, hull, v);
    const c = compare(fg, hm);
    const place = (b) => {
      const X0 = b.x0, Y0 = b.y0, X1 = b.x1 + 1, Y1 = b.y1 + 1;
      const [ra0, uu1] = pxToView(reg, v, X0, Y0), [ra1, uu0] = pxToView(reg, v, X1, Y1);
      return { bbox: [X0, Y0, X1, Y1], centroid: [r1(b.cx + 0.5), r1(b.cy + 0.5)], right: [r3(ra0), r3(ra1)], up: [r3(uu0), r3(uu1)] };
    };
    const blobs = blobRows(fg, hm, A.w, A.h, null, c.fg, place);
    out.views[v] = { iou: r4(c.iou), viewOnly: r4(c.only), viewOnlyBlob: r4(c.fg ? blobs.onlyPx / c.fg : 0), hullOnly: r4(c.extra), fgPx: c.fg, hullPx: c.hp,
      viewOnlyPx: c.onlyPx, hullOnlyPx: c.extraPx, blobs: blobs.only, hullOnlyBlobs: blobs.extra };
    rasters.views[v] = { fg, hull: hm, w: A.w, h: A.h };
  }
  if (concept) {
    const { T, creg, w: W, h: H } = concept;
    const fit = await fitHullFrame(hull, creg, T, W, H);
    const m = splatHull(hull, conceptMap(framed(creg, fit.frame)), W, H);
    const ref = new Uint8Array(W * H);
    let care = null;
    for (let i = 0; i < ref.length; i += 1) {
      if (T[i] === SUBJECT) ref[i] = 1;
      else if (T[i] === OCCLUDED) { care ??= new Uint8Array(W * H).fill(1); care[i] = 0; }
    }
    const c = compare(ref, m, care);
    const cplace = (b) => ({ bbox: [b.x0, b.y0, b.x1 + 1, b.y1 + 1], centroid: [r1(b.cx + 0.5), r1(b.cy + 0.5)] });
    const blobs = blobRows(ref, m, W, H, care, c.fg, cplace);
    const fr = (x) => ({ ...roundFrame(x.frame), iou: r4(x.v) });
    out.concept = {
      frame: { start: { from: fit.start.from, ...fr(fit.start) }, identity: fr(fit.identity), bbox: fr(fit.bbox), fitted: roundFrame(fit.frame), fitIoU: r4(fit.v) },
      iou: r4(iou(T, m)), conceptOnly: r4(c.only), conceptOnlyBlob: r4(c.fg ? blobs.onlyPx / c.fg : 0), hullOnly: r4(c.extra), fgPx: c.fg, hullPx: c.hp,
      conceptOnlyPx: c.onlyPx, hullOnlyPx: c.extraPx,
      blobs: blobs.only, hullOnlyBlobs: blobs.extra,
    };
    rasters.concept = { fg: ref, hull: m, care, w: W, h: H };
    if (aniso) {
      // the same H scaled per axis to the concept (fitHullAniso): the views' proportions against the concept's
      const an = fitHullAniso(hull, creg, T, W, H, fit.frame, { from: aniso?.from ?? null });
      const ma = splatHull(hull, anisoMap(creg, an.c3, an.s, an.frame.tx, an.frame.ty), W, H);
      const ca = compare(ref, ma, care);
      const ab = blobRows(ref, ma, W, H, care, ca.fg, cplace);
      out.concept.aniso = {
        scale: { W: r4(an.s.W), H: r4(an.s.H), L: r4(an.s.L) }, frame: { tx: +an.frame.tx.toFixed(2), ty: +an.frame.ty.toFixed(2) }, centre: an.c3.map(r3),
        params: Object.fromEntries(Object.entries(an.params).map(([k, v]) => [k, +v.toFixed(6)])), warm: an.warm, lambda: an.lambda, iou: r4(iou(T, ma)), conceptOnly: r4(ca.only), conceptOnlyBlob: r4(ca.fg ? ab.onlyPx / ca.fg : 0), hullOnly: r4(ca.extra),
        conceptOnlyPx: ca.onlyPx, hullOnlyPx: ca.extraPx, blobs: ab.only, search: an.search,
      };
      out.aspect = { HoverW: r4(an.aspect.HoverW), LoverW: r4(an.aspect.LoverW), HoverL: r4(an.aspect.HoverL) };
      rasters.conceptAniso = { fg: ref, hull: ma, care, w: W, h: H };
    }
  }
  out.ms = Date.now() - t0;
  return { report: out, rasters, hull };
}

// ---------------------------------------------------------------------------------------------------------------------
// Printing + the PNG
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The doctor's `aspect` row (doctor.mjs, next to the hull row): |aspect| H/W or L/W (hullReport with aniso) above
 * gate.warn -> WARN, above gate.block -> BLOCK (gold.config.json setupHull.aspect).
 */
export function aspectRows(R, gate = { warn: 0.03, block: 0.06 }) {
  if (!R?.aspect) return [{ level: "WARN", id: "aspect", text: "aspect: no per-axis fit (hullReport without a concept or aniso)" }];
  const rank = { PASS: 0, WARN: 1, BLOCK: 2 };
  const lvl = (x) => (Math.abs(x) > gate.block + 1e-9 ? "BLOCK" : Math.abs(x) > gate.warn + 1e-9 ? "WARN" : "PASS");
  const rows = [["H/W", R.aspect.HoverW], ["L/W", R.aspect.LoverW]].map(([n, x]) => ({ n, x, l: lvl(x) }));
  const level = rows.reduce((a, r) => (rank[r.l] > rank[a] ? r.l : a), "PASS");
  const bad = rows.filter((r) => r.l !== "PASS");
  const A = R.concept?.aniso;
  const g = (x) => `${+(x * 100).toFixed(2)}`;
  const text = `aspect (hull.mjs --aniso: the views' object's proportions over the concept's) H/W ${sgnPct(R.aspect.HoverW)} · L/W ${sgnPct(R.aspect.LoverW)} (warn > ${g(gate.warn)}, block > ${g(gate.block)} %; the fit's own spread ~+-2 pts)${A ? ` · concept IoU per-axis ${A.iou.toFixed(3)} vs ${R.concept.iou.toFixed(3)}` : ""}`
    + (level === "PASS" ? "" : ` — ${bad.map((r) => `${r.n} ${sgnPct(r.x)} ${r.l}`).join(", ")}: the set is drawn ${bad.map((r) => `${r.x > 0 ? (r.n === "H/W" ? "taller" : "longer") : (r.n === "H/W" ? "lower" : "shorter")}`).join(" and ")} (against W) than the concept — regenerate, or repair a view with a proportion draft (node scripts/v7/turnaround.mjs repair --draft proportion: the concept's proportions)`);
  return [{ level, id: "aspect", data: { HoverW: R.aspect.HoverW, LoverW: R.aspect.LoverW, HoverL: R.aspect.HoverL ?? null, anisoIoU: A?.iou ?? null }, text }];
}

/** The largest |W / L / H residual| over the views (the doctor's rows), a fraction. */
export const residualMax = (residuals) => Math.max(0, ...["W", "L", "H"].flatMap((D) => Object.entries(residuals?.[D] ?? {}).filter(([k]) => k !== "meanPx" && k !== "maxAbs").map(([, x]) => Math.abs(x))));

/** The report as stdout lines (without the [hull] prefix). */
export function reportLines(subject, set, R) {
  const L = [];
  const per = (rec) => Object.entries(rec ?? {}).filter(([k]) => k !== "meanPx" && k !== "maxAbs");
  L.push(`${subject} · ${set === "live" ? "live turnaround" : set} · s ${R.s.toFixed(2)} px/m · dims ${Object.entries(R.dims).map(([k, v]) => `${k} ${v.toFixed(3)}`).join(" ")} m`);
  for (const n of R.notes) L.push(`note: ${n}`);
  for (const D of ["W", "L", "H"]) {
    if (!R.residuals[D]) continue;
    const bb = R.residuals[`${D}bbox`];
    L.push(`residual ${D} ${per(R.residuals[D]).map(([v, x]) => `${v} ${sgnPct(x)}`).join(" · ")} (mean ${R.residuals[D].meanPx} px)${bb ? ` · ${D}bbox ${per(bb).map(([v, x]) => `${v} ${sgnPct(x)}`).join(" · ")}` : ""}`);
  }
  for (const d of R.doctor) L.push(`doctor ${d.level} ${d.id}: ${d.data ? Object.entries(d.data).map(([v, x]) => `${v} ${sgnPct(x)}`).join(", ") : d.text}`);
  const g = R.grid;
  L.push(`grid ${g.n.join(" x ")} at ${R.res.used} m (refine ${R.res.refine}: sub-cells ${R.res.sub} m) · kept ${g.kept} (${pct(g.kept / g.voxels, 1)}) · extent ${Object.entries(g.extent).map(([a, [p, q]]) => `${a} ${p.toFixed(2)}..${q.toFixed(2)}`).join(" ")} m`);
  const f3 = (x) => x.toFixed(3);
  for (const [v, m] of Object.entries(R.views)) {
    L.push(`${v.padEnd(6)} IoU ${m.iou.toFixed(4)} · viewOnly ${pct(m.viewOnly)} (in blobs ${pct(m.viewOnlyBlob)}) · hullOnly ${pct(m.hullOnly)} · fg ${m.fgPx} px`);
    for (const b of m.blobs) L.push(`  viewOnly ${v} ${b.px} px ${pct(b.share)} · px x ${b.bbox[0]}..${b.bbox[2]} y ${b.bbox[1]}..${b.bbox[3]} · right ${f3(b.right[0])}..${f3(b.right[1])} up ${f3(b.up[0])}..${f3(b.up[1])} m`);
  }
  const C = R.concept;
  if (C) {
    const fr = (x) => `${x.scale.toFixed(4)} ${x.tx >= 0 ? "+" : ""}${x.tx.toFixed(2)} ${x.ty >= 0 ? "+" : ""}${x.ty.toFixed(2)}`;
    L.push(`concept frame start (${C.frame.start.from}) ${fr(C.frame.start)} IoU ${C.frame.start.iou.toFixed(4)} -> fitted frameScale / frameX / frameY ${fr(C.frame.fitted)} IoU ${C.frame.fitIoU.toFixed(4)}`);
    L.push(`concept IoU ${C.iou.toFixed(4)} · conceptOnly ${pct(C.conceptOnly)} (in blobs ${pct(C.conceptOnlyBlob)}) · hullOnly ${pct(C.hullOnly)} · fg ${C.fgPx} px`);
    for (const b of C.blobs) L.push(`  conceptOnly ${b.px} px ${pct(b.share)} · px x ${b.bbox[0]}..${b.bbox[2]} y ${b.bbox[1]}..${b.bbox[3]} · at (${b.centroid.map(Math.round).join(", ")})`);
    const A = C.aniso;
    if (A) {
      L.push(`concept aniso: s W ${A.scale.W.toFixed(4)} H ${A.scale.H.toFixed(4)} L ${A.scale.L.toFixed(4)} (the views' object over the concept's, about (${A.centre.map((x) => x.toFixed(2)).join(", ")}) m) · frameX / frameY ${A.frame.tx >= 0 ? "+" : ""}${A.frame.tx.toFixed(2)} ${A.frame.ty >= 0 ? "+" : ""}${A.frame.ty.toFixed(2)} · IoU ${A.iou.toFixed(4)} (isotropic ${C.iou.toFixed(4)}) · conceptOnly ${pct(A.conceptOnly)} (in blobs ${pct(A.conceptOnlyBlob)}) · hullOnly ${pct(A.hullOnly)} · Nelder-Mead ${A.search.coarse.evals} + ${A.search.fine.evals} evals (point splats on the concept grid / ${A.search.coarse.q}, then / ${A.search.fine.q}; lambda ${A.lambda}) ${(A.search.ms / 1000).toFixed(1)} s`);
      for (const b of A.blobs) L.push(`  conceptOnly (aniso) ${b.px} px ${pct(b.share)} · px x ${b.bbox[0]}..${b.bbox[2]} y ${b.bbox[1]}..${b.bbox[3]} · at (${b.centroid.map(Math.round).join(", ")})`);
      L.push(`aspect H/W ${sgnPct(R.aspect.HoverW)} · L/W ${sgnPct(R.aspect.LoverW)} (the views' object's proportions over the concept's - 1: + = the views draw it taller / longer; H/L ${sgnPct(R.aspect.HoverL)}${A.warm ? " · warm start" : ""})`);
    }
  }
  L.push(`SUMMARY ${subject} ${set}: residual max ${pct(residualMax(R.residuals), 1)} · viewOnly ${Object.entries(R.views).map(([v, m]) => `${v} ${pct(m.viewOnly)}`).join(" / ")}${C ? ` · concept IoU ${C.iou.toFixed(3)} conceptOnly ${pct(C.conceptOnly)} (blobs ${pct(C.conceptOnlyBlob)}) hullOnly ${pct(C.hullOnly)} frame ${fr3(C.frame.fitted)}` : ""}${R.aspect ? ` · aspect H/W ${sgnPct(R.aspect.HoverW)} L/W ${sgnPct(R.aspect.LoverW)} (aniso IoU ${C.aniso.iou.toFixed(3)}, conceptOnlyBlob ${pct(C.aniso.conceptOnlyBlob)})` : ""} · ${(R.ms / 1000).toFixed(1)} s`);
  return L;
}
const fr3 = (x) => `${x.scale.toFixed(3)} ${x.tx >= 0 ? "+" : ""}${x.tx.toFixed(1)} ${x.ty >= 0 ? "+" : ""}${x.ty.toFixed(1)}`;

const GREY = [150, 150, 150], BLUE = [40, 90, 255], RED = [230, 30, 30], LIGHT = [215, 215, 215];

/** Overlay tile of one image, cropped to the union of fg and H (+16 px): grey agree, blue ref-only, red hull-only. */
function overlayTile({ fg, hull, care = null, w, h }) {
  let x0 = w, y0 = h, x1 = 0, y1 = 0;
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) if (fg[y * w + x] || hull[y * w + x]) { x0 = Math.min(x0, x); x1 = Math.max(x1, x + 1); y0 = Math.min(y0, y); y1 = Math.max(y1, y + 1); }
  if (x1 <= x0) { x0 = 0; y0 = 0; x1 = w; y1 = h; }
  const P = 16;
  x0 = Math.max(0, x0 - P); y0 = Math.max(0, y0 - P); x1 = Math.min(w, x1 + P); y1 = Math.min(h, y1 + P);
  const tw = x1 - x0, th = y1 - y0;
  const rgb = Buffer.alloc(tw * th * 3, 255);
  for (let y = 0; y < th; y += 1) for (let x = 0; x < tw; x += 1) {
    const i = (y + y0) * w + x + x0;
    const a = fg[i] === 1, b = hull[i] === 1;
    const c = care && !care[i] ? (a || b ? LIGHT : null) : a && b ? GREY : a ? BLUE : b ? RED : null;
    if (c) { const o = (y * tw + x) * 3; rgb[o] = c[0]; rgb[o + 1] = c[1]; rgb[o + 2] = c[2]; }
  }
  return { rgb, w: tw, h: th };
}

/** --png: one row, a caption above each tile (tiles TH px high). */
export async function writeHullPng(file, title, rasters, R) {
  const TH = 300, pad = 12, titleH = 30, capH = 22, charW = 7;
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const items = [];
  for (const [v, r] of Object.entries(rasters.views)) {
    const m = R.views[v];
    items.push({ tile: overlayTile(r), cap: `${v} · IoU ${m.iou.toFixed(3)} · viewOnly ${pct(m.viewOnly)} · hullOnly ${pct(m.hullOnly)}` });
  }
  if (rasters.concept) {
    const C = R.concept;
    items.push({ tile: overlayTile(rasters.concept), cap: `concept · IoU ${C.iou.toFixed(3)} · conceptOnly ${pct(C.conceptOnly)} · hullOnly ${pct(C.hullOnly)} · frame ${fr3(C.frame.fitted)}` });
  }
  if (rasters.conceptAniso) {
    const A = R.concept.aniso;
    items.push({ tile: overlayTile(rasters.conceptAniso), cap: `concept aniso · IoU ${A.iou.toFixed(3)} · conceptOnly ${pct(A.conceptOnly)} · aspect H/W ${sgnPct(R.aspect.HoverW)} L/W ${sgnPct(R.aspect.LoverW)}` });
  }
  let x = pad;
  const comps = [];
  let texts = `<text x="${pad}" y="21" font-family="Arial" font-size="17" font-weight="bold" fill="#111">${esc(title)}</text>`;
  for (const it of items) {
    const tw = Math.max(1, Math.round(it.tile.w * TH / it.tile.h));
    const cw = Math.max(tw, it.cap.length * charW + 8);
    const png = await sharp(it.tile.rgb, { raw: { width: it.tile.w, height: it.tile.h, channels: 3 } }).resize(tw, TH).png().toBuffer();
    comps.push({ input: png, left: x + Math.round((cw - tw) / 2), top: titleH + capH });
    texts += `<text x="${x}" y="${titleH + 15}" font-family="Arial" font-size="13" fill="#222">${esc(it.cap)}</text>`;
    x += cw + pad;
  }
  const width = x, height = titleH + capH + TH + pad;
  const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">${texts}</svg>`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  await sharp({ create: { width, height, channels: 3, background: { r: 255, g: 255, b: 255 } } }).composite([...comps, { input: svg, left: 0, top: 0 }]).png().toFile(file);
}

// ---------------------------------------------------------------------------------------------------------------------
// --write-frame: the concept registration quad (layout.measured.json `_frame.quadPx`, read by registered.mjs registration)
// ---------------------------------------------------------------------------------------------------------------------

/** hull.mjs --write-frame --frame-refine: the direct-class concept frame refine (iou = the WF v10 default, unchanged). */
export const FRAME_REFINE = Object.freeze(["iou", "box", "off"]);

/** The concept's foreground bbox [x0, y0, x1, y1] (exclusive ends): darkest channel < fgMax (the 2026-09-26 setup rule). */
export function foregroundBox(data, width, height, channels, fgMax = 235) {
  let x0 = width, x1 = -1, y0 = height, y1 = -1;
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const j = (y * width + x) * channels;
    if (Math.min(data[j], data[j + 1], data[j + 2]) < fgMax) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (x1 < 0) throw new Error("hull --write-frame: the concept has no foreground");
  return [x0, y0, x1 + 1, y1 + 1];
}

/** The camera-plane extent {a0, a1, b0, b1} (a = p . right, b = -p . up, render frame after `turn`) of author points (+ pad each side). */
export function cameraExtent(points, basis, turn, pad = [0, 0]) {
  let a0 = Infinity, a1 = -Infinity, b0 = Infinity, b1 = -Infinity;
  const d = (u, v) => u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
  for (const p of points) {
    const q = turn(p), a = d(q, basis.right), b = -d(q, basis.up);
    if (a < a0) a0 = a; if (a > a1) a1 = a; if (b < b0) b0 = b; if (b > b1) b1 = b;
  }
  return { a0: a0 - pad[0], a1: a1 + pad[0], b0: b0 - pad[1], b1: b1 + pad[1] };
}

/**
 * The frame: the object's camera-plane extent fitted to the concept bbox — s = the mean of the x / y px per metre, the
 * centres matched — and the class anchor face's corners (registered.mjs anchorFace) placed with it: registration() then
 * recovers s / ox / oy exactly (rms 0). -> {s, sx, sy, ox, oy, quadPx}
 */
export function frameQuad({ ext, bbox, corners, basis, turn }) {
  const [x0, y0, x1, y1] = bbox;
  const sx = (x1 - x0) / (ext.a1 - ext.a0), sy = (y1 - y0) / (ext.b1 - ext.b0);
  const s = (sx + sy) / 2;
  const ox = (x0 + x1) / 2 - (s * (ext.a0 + ext.a1)) / 2, oy = (y0 + y1) / 2 - (s * (ext.b0 + ext.b1)) / 2;
  const d = (u, v) => u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
  const quadPx = corners.map((c) => { const p = turn(c); return [r1(s * d(p, basis.right) + ox), r1(-s * d(p, basis.up) + oy)]; });
  return { s, sx, sy, ox, oy, quadPx };
}

/**
 * The layout.measured.json record for a subject: `from` "hull" = the registered visual hull of the live turnaround (or
 * `viewsDir`) — the setup's frame, after `turnaround.mjs install`; "facts" = the facts.json dims box (L x W x H, x / z
 * centred, ground y 0) — a PROVISIONAL frame so turnaround.mjs gen can measure a first set before any turnaround exists.
 * -> {record, fit, points, file}
 */
export async function frameRecord(subject, { from = "hull", viewsDir = null, res = 0.03, frameRefine = "iou" } = {}) {
  if (!FRAME_REFINE.includes(frameRefine)) throw new Error(`hull --write-frame --frame-refine ${frameRefine}: ${FRAME_REFINE.join(" | ")}`);
  const { cameraBasis } = await import("../registered.mjs");
  const { frontRotationDeg } = await import("../../src/kernel/toThree.mjs");
  const S = loadSubject(subject);
  const anchorFace = anchorFaceOf, subjectFront = subjectFrontOf;   // WF v10: a direct class (weapon) has its own anchor (conceptreg.mjs)
  if (!S.paths.camera || !fs.existsSync(S.paths.camera)) throw new Error(`hull --write-frame: no camera (${S.rel.camera ?? "subject.json paths.camera"}): node scripts/solve-camera.mjs ${subject} --image ${S.rel.target} first`);
  if (!S.paths.layoutMeasured) throw new Error(`hull --write-frame: subjects/${subject}/subject.json has no paths.layoutMeasured`);
  const camera = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
  const basis = cameraBasis(camera);
  const turn = turnFn(frontRotationDeg(subjectFront(S)));
  const spec = readJson(viewsFile(subject));
  let pts, pad = [0, 0], fgMax = spec.families?.fgMax ?? 235, what;
  let hullRef = null;   // WF v10: the direct-class frame refinement below reads the hull
  if (from === "facts") {
    const ff = path.join(ROOT, "subjects", subject, "turnaround", "facts.json");
    const dims = fs.existsSync(ff) ? readJson(ff).dims : null;
    if (!(dims?.L > 0 && dims?.W > 0 && dims?.H > 0)) throw new Error(`hull --write-frame --from facts: subjects/${subject}/turnaround/facts.json has no dims {L, W, H}`);
    pts = [];
    for (const x of [-dims.W / 2, dims.W / 2]) for (const y of [0, dims.H]) for (const z of [-dims.L / 2, dims.L / 2]) pts.push([x, y, z]);
    what = `PROVISIONAL (before the first turnaround): the facts.json dims box L ${dims.L} x W ${dims.W} x H ${dims.H} m (x / z centred, ground y 0)`;
  } else if (from === "hull") {
    const set = await loadViewSet(subject, { viewsDir });
    fgMax = set.table.fgMax ?? fgMax;
    const hull = buildHull(set.reg, { res });
    hullRef = hull;
    const P = hullPoints(hull, "fine");
    pts = Array.from({ length: P.n }, (_, i) => [P.x[i], P.y[i], P.z[i]]);
    // a sub-cell is a cube of side P.step around its centre: its projected half extent along each camera axis
    const back = turnFn(-frontRotationDeg(subjectFront(S)));
    const R = back(basis.right), U = back(basis.up);
    pad = [(P.step / 2) * (Math.abs(R[0]) + Math.abs(R[1]) + Math.abs(R[2])), (P.step / 2) * (Math.abs(U[0]) + Math.abs(U[1]) + Math.abs(U[2]))];
    what = `the VISUAL HULL of the registered turnaround (${set.set === "live" ? `subjects/${subject}/turnaround` : set.set}: ${set.reg.names.join(" / ")} foregrounds, ${hull.res} m voxels refined x${hull.f}, ${P.n} surface / shell points)`;
  } else throw new Error(`hull --write-frame --from ${from}: hull | facts`);
  const { data, info } = await sharp(S.paths.target).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const bbox = foregroundBox(data, info.width, info.height, info.channels, fgMax);
  const ext = cameraExtent(pts, basis, turn, pad);
  const fit = frameQuad({ ext, bbox, corners: anchorFace(S).corners, basis, turn });
  // WF v10 direct class: no module carries frameScale / frameX / frameY knobs, so the similarity a gold model's knobs
  // would fit is fitted here, on the hull's concept IoU (fitHullFrame), and folded into s / ox / oy / quadPx
  // S1 fix 2026-10-10 (--frame-refine, default "iou" = unchanged): the IoU optimum trades box agreement for overlap —
  // on 6 registered weapons it made the model's concept box 2.8..9.3 % off (scale 0.93..1.06, tx +16..+56 px, always
  // right); "off" keeps the plain hull bbox fit above (0.4..3.1 %), "box" = fitHullFrame's bbox start (the hull SPLAT's
  // px box on the concept target mask's box, no IoU search). Evidence: out/score/s1fix/box_stored.json + frames/<s>.<mode>.json.
  let refined = isDirectClass(S) && hullRef && frameRefine === "off" ? { frame: { scale: 1, tx: 0, ty: 0 }, identity: true, by: "off" } : null;
  if (isDirectClass(S) && hullRef && frameRefine !== "off") {
    const { T } = await conceptTarget(subject);
    const fr = await fitHullFrame(hullRef, { s: fit.s, ox: fit.ox, oy: fit.oy, turnDeg: 0, basis, quadPx: fit.quadPx, targetW: info.width, targetH: info.height }, T, info.width, info.height, frameRefine === "box" ? { search: false } : {});
    const cx = fit.quadPx.reduce((a, q) => a + q[0], 0) / 4, cy = fit.quadPx.reduce((a, q) => a + q[1], 0) / 4, k = info.width / 1024;
    const { scale, tx, ty } = fr.frame;
    refined = { frame: fr.frame, iou: r4(fr.v), bboxIou: r4(fr.identity.v), ...(frameRefine !== "iou" ? { by: frameRefine } : {}) };
    fit.s *= scale; fit.ox = cx + scale * (fit.ox - cx) + tx * k; fit.oy = cy + scale * (fit.oy - cy) + ty * k;
    fit.quadPx = fit.quadPx.map(([x, y]) => [r1(cx + scale * (x - cx) + tx * k), r1(cy + scale * (y - cy) + ty * k)]);
  }
  const record = {
    _comment: `MEASURED (hull.mjs --write-frame --from ${from}, ${new Date().toISOString().slice(0, 10)}): ${what} projected through ${S.rel.camera}; its bbox fitted to the concept foreground bbox (s = mean of the x / y px-per-m, centres matched). Only _frame is read (scripts/registered.mjs registration).`,
    _frame: {
      camera: `theta ${camera.theta_deg} deg, phi ${camera.phi_deg} deg`,
      conceptBboxPx: bbox,
      sPxPerM: { x: r3(fit.sx), y: r3(fit.sy), used: r3(fit.s), xOverY: r4(fit.sx / fit.sy) },
      quadPx: fit.quadPx,
      ...(from === "facts" ? { provisional: true } : {}),
      // WF v10: a direct class has no registered.mjs anchor — conceptreg.mjs conceptRegistration reads the fit itself
      ...(isDirectClass(S) ? { fit: { s: fit.s, ox: fit.ox, oy: fit.oy, ...(refined ? { refined } : {}) } } : {}),
      note: "quadPx = the registered.mjs anchorFace corners (+X flank of the class default body) placed with the fitted s / ox / oy, so registration() recovers them exactly (rms 0); sPxPerM.xOverY != 1 = the concept's aspect differs from the turnaround's (drift); the module's frameScale / frameX / frameY knobs refine the fit",
    },
  };
  return { record, fit, points: pts.length, file: S.paths.layoutMeasured };
}

/** Write a frameRecord (file default = subject.json paths.layoutMeasured); a file holding more than _comment / _frame is another tool's: refused. */
export function writeFrameFile(file, record) {
  if (fs.existsSync(file)) {
    const old = JSON.parse(fs.readFileSync(file, "utf8"));
    const extra = Object.keys(old).filter((k) => k !== "_comment" && k !== "_frame");
    if (extra.length) throw new Error(`hull --write-frame: ${rel(file)} holds ${extra.slice(0, 4).join(", ")} (measured by another tool): pass --write-frame <another file>`);
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(record, null, 2)}\n`);
}

// ---------------------------------------------------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------------------------------------------------

const USAGE = "usage: node scripts/v7/hull.mjs --subject <s> [--views-dir <dir>] [--res <m, 0.02>] [--aniso] [--json <file>] [--png <file>] [--no-concept] [--max-voxels 6e6] [--refine <f>]\n       node scripts/v7/hull.mjs --subject <s> --write-frame [<file>] [--from hull|facts] [--views-dir <dir>] [--res <m, 0.03>] [--frame-refine iou|box|off] [--dry]";

async function main() {
  const t0 = Date.now();
  const args = parseArgs(process.argv.slice(2), ["no-concept", "aniso", "help", "dry"]);
  const str = (v) => (v && v !== true ? String(v) : null);
  const s = str(args.subject);
  if (args.help || !s) { console.log(USAGE); return args.help ? 0 : 3; }
  const num = (name, d) => {
    if (!str(args[name])) return d;
    const x = Number(args[name]);
    if (!(x > 0)) throw new Error(`--${name} ${args[name]} is not a positive number`);
    return x;
  };
  const viewsDir = str(args["views-dir"]) ? path.resolve(args["views-dir"]) : null;
  if (args["write-frame"]) {
    const from = str(args.from) ?? "hull";
    const { record, fit, points, file: dflt } = await frameRecord(s, { from, viewsDir, res: str(args.res) ? num("res", 0.03) : 0.03, frameRefine: str(args["frame-refine"]) ?? "iou" });
    const file = str(args["write-frame"]) ? path.resolve(args["write-frame"]) : dflt;
    if (!args.dry) writeFrameFile(file, record);
    console.log(`[hull] frame ${s} --from ${from}: ${points} points · concept bbox ${record._frame.conceptBboxPx.join(",")} · s ${fit.s.toFixed(3)} px/m (x ${fit.sx.toFixed(3)} / y ${fit.sy.toFixed(3)}, xOverY ${(fit.sx / fit.sy).toFixed(4)}) · quadPx ${JSON.stringify(fit.quadPx)}${from === "facts" ? " · PROVISIONAL: re-run with --from hull after turnaround.mjs install" : ""}`);
    console.log(args.dry ? "[hull] --dry: nothing written" : `[hull] wrote ${rel(file)} _frame`);
    return 0;
  }
  const set = await loadViewSet(s, { viewsDir });
  let concept = null;
  if (!args["no-concept"]) {
    const { img, T } = await conceptTarget(s);
    concept = { T, creg: conceptRegistration(s), w: img.w, h: img.h };
  }
  const json = str(args.json) ? path.resolve(args.json) : null;
  // the per-axis fit: --aniso, and always when a JSON is written (its `aspect` is what turnaround.mjs / the doctor read)
  const aniso = !!concept && (!!args.aniso || !!json);
  const { report, rasters } = await hullReport({ reg: set.reg, concept, aniso, res: num("res", HULL.res), maxVoxels: num("max-voxels", HULL.maxVoxels), refine: str(args.refine) ? num("refine", null) : null });
  report.notes.unshift(...set.notes);
  report.ms = Date.now() - t0;
  for (const l of reportLines(s, set.set, report)) console.log(`[hull] ${l}`);
  if (json) {
    fs.mkdirSync(path.dirname(json), { recursive: true });
    fs.writeFileSync(json, `${JSON.stringify({ subject: s, set: set.set, at: new Date().toISOString(), ...report }, null, 2)}\n`);
    console.log(`[hull] json ${rel(json)}`);
  }
  const png = str(args.png) ? path.resolve(args.png) : null;
  if (png) {
    await writeHullPng(png, `hull · ${s} · ${set.set === "live" ? "live turnaround" : set.set} · res ${report.res.used} m (refine ${report.res.refine}) · grey agree, blue image-only, red hull-only`, rasters, report);
    console.log(`[hull] png ${rel(png)}`);
  }
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((c) => { process.exitCode = c; }).catch((e) => { console.error(`[hull] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 2; });
}
