#!/usr/bin/env node
// WORKFLOW v4 — V4-2 stage S2 FIT (research/WF-V4-PLAN.md): the HARNESS fits continuous shape, no seat.
//
//   node scripts/fit.mjs --subject pickup --module <in.mjs> --out <out.mjs> [--evals 300] [--size 384] [--log <fit.json>]
//
// Coordinate descent over the module's unlocked KNOBS (scripts/knobs.mjs), each knob stepping +/- step inside its
// [min, max]; a knob whose two moves both fail halves its step (the shrinking-step pass), until every step is under
// its floor or the eval budget is spent. Objective, in the REGISTERED frame (scripts/registered.mjs, target px, the
// Node projector at `size` px):
//   whole-silhouette IoU + mean per-family IoU - ZONE_SHORT_W x sum of each family's shortfall under its class band
//   (classes/<c>.json zoneIouMin, V4-5A) (target families from likeness classifyTargetPixels via
//   residuals.targetFamilies vs the projected parts' zone families; target px of a family the model has no part in,
//   and ink px, are not scored — the body is not pulled over the glass it will carry later)
// Gate: every eval runs build() + K.checkParts + the kernel chain without V2/V3/V6 (contact, support, seat depth) —
// V-rules, VEH_*, V12 census (staged to the roles built) and V12_LAYOUT; a failing candidate is rejected. After each
// sweep the WHOLE chain runs; if it fails, that sweep's accepted moves are reverted newest first until it passes.
// Deterministic (fixed knob order, fixed steps, 4-decimal values). Writes the fitted module (only the KNOBS `v:`
// numbers change) and a fit.json log (score / IoU per accepted step).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import { ROOT, loadSubject } from "./subject.mjs";
import { loadModule, meshParts, project } from "./project.mjs";
import { frontRotationDeg } from "../src/kernel/toThree.mjs";
import { FRAME_KNOBS, frameOf, iou, readRGB } from "./registered.mjs";
import { partFamilies, targetFamilies } from "./residuals.mjs";
import { accuracy, featureScore, targetOf } from "./accuracy.mjs";
import { replaceKnobValues } from "./knobs.mjs";

export const FIT_SIZE = 384;
export const FIT_EVALS = 300;
/** Smallest step per unit before a knob is converged. */
const MIN_STEP = { m: 0.002, exp: 0.05, scale: 0.001, px: 0.25 };
/** V5-1 item 2: the knobs of the massing-first stage, and its share of the eval budget. */
export const MASSING_KNOBS = Object.freeze([...FRAME_KNOBS, "W", "H", "D", "L"]);
export const MASSING_SHARE = 0.35;
const ACCEPT = 1e-6;
/** V4-5A: weight of the per-zone band shortfall term (a family under its zoneIouMin band pulls the score down). */
export const ZONE_SHORT_W = 1;
/** V4-5A: a move may trade at most this much whole-silhouette IoU (fit raster) for zone terms. */
export const WHOLE_SLACK = 0.0003;
const FAST_SKIP = ["V2", "V3", "V6"];   // contact, support, seat depth: ~300 ms together, run once per sweep

const r4 = (v) => Math.round(v * 1e4) / 1e4;

/**
 * V5-9 EVIDENCE HIERARCHY — the layout the FIT / LOOP gate enforces: the class rules' advisoryLayout() (vehicles: every
 * measured non-count key the per-feature accuracy report covers moves to `_advisory`, reported, never blocking); a
 * class without one enforces its layout as is.
 */
export function gateLayout(S, rules) {
  const layout = S.readJson("layout");
  return typeof rules?.advisoryLayout === "function" ? rules.advisoryLayout(layout) : layout;
}
/** V5-1 bug (a): one macrotask turn, so the kernel's FinalizationRegistry frees the WASM of the builds before it. */
export const yieldTask = () => new Promise((resolve) => setImmediate(resolve));

const targetCache = new Map();
/** Target families at full resolution, sampled at the fit raster's pixel centres (nearest). */
export async function fitTarget(S, size) {
  const key = `${S.subject.id}:${size}`;
  if (targetCache.has(key)) return targetCache.get(key);
  const img = await readRGB(S.paths.target);
  const full = targetFamilies(S, img);
  const w = size;
  const h = Math.round(size * img.h / img.w);
  const tfg = new Uint8Array(w * h);
  const tFam = new Int32Array(w * h);
  for (let y = 0; y < h; y += 1) {
    const ty = Math.min(img.h - 1, Math.floor((y + 0.5) * img.h / h));
    for (let x = 0; x < w; x += 1) {
      const tx = Math.min(img.w - 1, Math.floor((x + 0.5) * img.w / w));
      tfg[y * w + x] = full.tfg[ty * img.w + tx];
      tFam[y * w + x] = full.tFam[ty * img.w + tx];
    }
  }
  const out = { img, full, w, h, tfg, tFam, nf: full.famNames.length };
  targetCache.set(key, out);
  return out;
}

/**
 * whole IoU + mean per-family IoU over the families the model has parts in - the band shortfall. `bandOff` (V4-5A):
 * per family, full-resolution IoU minus fit-raster IoU at the start module — the bands are calibrated at the target's
 * own resolution, so the raster value is shifted onto that scale before it is held to its band.
 */
export function score(T, proj, S, bandOff = {}, zoneW = ZONE_SHORT_W) {
  const pf = partFamilies(S, proj.parts, T.full);
  const present = new Uint8Array(T.nf);
  for (const f of pf) if (f >= 0) present[f] = 1;
  const fi = new Float64Array(T.nf);
  const fu = new Float64Array(T.nf);
  const { partId } = proj;
  for (let i = 0; i < partId.length; i += 1) {
    const p = partId[i];
    const m = p >= 0;
    const tf = T.tFam[i];
    if (tf === -3) continue;   // V5-1: OCCLUDED don't-care
    if (tf === -2 || (tf >= 0 && !present[tf])) continue;
    const mf = m ? pf[p] : -1;
    if (tf >= 0) { fu[tf] += 1; if (mf === tf) fi[tf] += 1; }
    if (mf >= 0 && mf !== tf) fu[mf] += 1;
  }
  const fam = {};
  let sum = 0;
  let n = 0;
  for (let k = 0; k < T.nf; k += 1) {
    if (!present[k] || fu[k] === 0) continue;
    fam[T.full.famNames[k]] = r4(fi[k] / fu[k]);
    sum += fi[k] / fu[k];
    n += 1;
  }
  const whole = iou(T.tfg, partId, { ids: true });   // V5-1 item 1: THE registered IoU (registered.mjs)
  const zone = n ? sum / n : 0;
  let short = 0;
  for (const [f, band] of Object.entries(S.cls.zoneIouMin ?? {})) {
    const v = fam[f] + (bandOff[f] ?? 0);
    if (Number.isFinite(v) && v < band) short += band - v;
  }
  return { score: whole + zone - zoneW * short, whole, zone, short, fam };
}

/** The `v:` of every knob as written in the module text (the cached module object may have been mutated). */
function knobsFromText(text, names) {
  const out = {};
  for (const n of names) {
    const m = new RegExp(`\\n\\s*${n}:\\s*\\{\\s*v:\\s*(-?[\\d.]+(?:e-?\\d+)?)`).exec(text);
    if (!m) throw new Error(`fit: KNOBS block has no knob "${n}"`);
    out[n] = Number(m[1]);
  }
  return out;
}

/**
 * V4-6 item 3: `knobs` restricts the free set to those names (the loop's per-row absorb re-FIT); `zoneW` weights the
 * band-shortfall term (zone-weighted absorb).
 * @param {{subjectId:string, modulePath:string, out?:string|null, evals?:number, size?:number, log?:string|null,
 *   knobs?:string[]|null, zoneW?:number}} o
 * @returns {Promise<object>} the fit.json record
 */
export async function fit({ subjectId, modulePath, out = null, evals = FIT_EVALS, size = FIT_SIZE, log = null, knobs = null, zoneW = ZONE_SHORT_W, deadline = null }) {
  const t0 = performance.now();
  const S = loadSubject(subjectId);
  await K.init();
  if (K.assemble?.ready) await K.assemble.ready;
  try { K.configure(gateConfig(S.cls)); } catch { K.configure(null); }
  const rules = await import(pathToFileURL(path.join(ROOT, S.cls.rules)).href);
  const layout = gateLayout(S, rules);   // V5-9: accuracy-covered layout keys are advisory
  const inPath = path.resolve(ROOT, modulePath);
  const text = fs.readFileSync(inPath, "utf8");
  const mod = await loadModule(modulePath);
  if (!mod.KNOBS || typeof mod.KNOBS !== "object") throw new Error(`fit: ${modulePath} exports no KNOBS block`);
  const KN = mod.KNOBS;
  const names = Object.keys(KN);
  const start = knobsFromText(text, names);
  const T = await fitTarget(S, size);

  const setKnobs = (vals) => { for (const n of names) KN[n].v = vals[n]; };
  let census = null;
  const gate = async (meta, parts, skip) => validateParts(meta, parts, undefined, { cls: S.cls, rules, layout, census, ...(skip ? { skip } : {}) });
  const build = (vals) => {
    setKnobs(vals);
    try {
      const parts = mod.build();
      return K.checkParts(mod.meta, parts).length ? null : parts;
    } catch {
      return null;
    }
  };
  let nEval = 0;
  const bandOff = {};
  /** score a candidate; the per-eval gate runs only when it would be accepted (`bar`): a rejected one needs none */
  // V5-1 bug (a): the caller's wall-clock deadline (performance.now() ms) ends the descent where it stands
  let timedOut = false;
  const late = () => { if (deadline !== null && performance.now() > deadline) timedOut = true; return timedOut; };
  const evaluate = async (vals, bar = -Infinity) => {
    nEval += 1;
    await yieldTask();
    const parts = build(vals);
    if (!parts) return null;
    const proj = await project({ subjectId, modulePath, frame: "target", size: T.w, built: { meta: mod.meta, parts, frame: frameOf(KN) } });
    const s = score(T, proj, S, bandOff, zoneW);
    if (s.score <= bar) return s;
    return (await gate(mod.meta, parts, FAST_SKIP)).pass ? s : null;
  };
  const fullIoU = async (vals) => {
    const parts = build(vals);
    const proj = await project({ subjectId, modulePath, frame: "target", size: T.img.w, built: { meta: mod.meta, parts, frame: frameOf(KN) } });
    return r4(iou(T.full.tfg, proj.foreground()));   // V4-6 item 5: target fg inside the subject mask
  };

  try {
    // census staged to the roles the module builds (a knob never changes the structure)
    const startParts = build(start);
    if (!startParts) throw new Error(`fit: ${modulePath} does not build at its own KNOBS`);
    const rolesBuilt = new Set(startParts.map((p) => p.role));
    const raw = S.readJson("census") ?? {};
    census = Object.fromEntries(Object.entries(raw).filter(([k]) => !k.startsWith("_") && rolesBuilt.has(S.cls.censusRules?.[k]?.role)));
    const startGate = await gate(mod.meta, startParts, null);
    if (!startGate.pass) throw new Error(`fit: the start module fails the gate — ${startGate.text.split("\n")[0]}`);

    // V4-5A: the band offsets (full resolution vs the fit raster), once, at the start module
    {
      const TF = await fitTarget(S, T.img.w);
      const full = score(TF, await project({ subjectId, modulePath, frame: "target", size: TF.w, built: { meta: mod.meta, parts: startParts, frame: frameOf(KN) } }), S).fam;
      const small = score(T, await project({ subjectId, modulePath, frame: "target", size: T.w, built: { meta: mod.meta, parts: startParts, frame: frameOf(KN) } }), S).fam;
      for (const f of Object.keys(full)) if (Number.isFinite(small[f])) bandOff[f] = full[f] - small[f];
    }
    let cur = { ...start };
    let best = await evaluate(cur);
    if (!best) throw new Error("fit: the start module fails the per-eval gate");
    const first = best;
    const free = names.filter((n) => !KN[n].locked && KN[n].max > KN[n].min && (!knobs || knobs.includes(n)));
    const step = Object.fromEntries(free.map((n) => [n, (KN[n].max - KN[n].min) / 4]));
    const pref = Object.fromEntries(free.map((n) => [n, 1]));
    const minStep = (n) => MIN_STEP[KN[n].unit] ?? MIN_STEP.m;
    const steps = [];
    const sweeps = [];
    let sweep = 0;
    const descend = async (list, stage, until) => {
    while (nEval < until && !late()) {
      sweep += 1;
      const accepted = [];
      let active = false;
      for (const n of list) {
        if (nEval >= until || late()) break;
        if (step[n] < minStep(n)) continue;
        active = true;
        let moved = false;
        for (const dir of [pref[n], -pref[n]]) {
          const c = r4(Math.min(KN[n].max, Math.max(KN[n].min, cur[n] + dir * step[n])));
          if (c === cur[n]) continue;
          const cand = { ...cur, [n]: c };
          const s = await evaluate(cand, best.score + ACCEPT);
          if (s && s.score > best.score + ACCEPT && s.whole >= best.whole - WHOLE_SLACK) {
            accepted.push({ n, from: cur[n], to: c });
            cur = cand;
            best = s;
            pref[n] = dir;
            moved = true;
            steps.push({ eval: nEval, sweep, knob: n, v: c, score: r4(s.score), iou: r4(s.whole), zone: r4(s.zone) });
            break;
          }
          if (nEval >= until) break;
        }
        if (!moved) step[n] /= 2;
      }
      // the whole chain once per sweep; revert that sweep's moves newest first until it passes
      let reverted = 0;
      if (accepted.length) {
        let ok = (await gate(mod.meta, build(cur), null)).pass;
        while (!ok && accepted.length) {
          const a = accepted.pop();
          cur = { ...cur, [a.n]: a.from };
          step[a.n] /= 2;
          reverted += 1;
          steps.push({ eval: nEval, sweep, knob: a.n, v: a.from, reverted: true });
          ok = (await gate(mod.meta, build(cur), null)).pass;
        }
        if (reverted) best = await evaluate(cur);
      }
      sweeps.push({ sweep, stage, evals: nEval, accepted: accepted.length, reverted, score: r4(best.score), iou: r4(best.whole) });
      if (!active) break;
    }
    };
    // V5-1 item 2: MASSING FIRST — the similarity (frameScale / frameX / frameY: absolute scale and placement are free in
    // ortho) and the massing sizes (W / H / D / L: the aspect is NOT free, it is fitted) before any detail knob
    const massing = free.filter((n) => MASSING_KNOBS.includes(n));
    if (!knobs && massing.some((n) => FRAME_KNOBS.includes(n))) {
      await descend(massing, "massing", Math.min(evals, nEval + Math.ceil(evals * MASSING_SHARE)));
      for (const n of massing) step[n] = Math.max(step[n], (KN[n].max - KN[n].min) / 16);
    }
    await descend(free, "all", evals);

    const record = {
      subject: subjectId,
      module: path.relative(ROOT, inPath).replace(/\\/g, "/"),
      out: out ? path.relative(ROOT, path.resolve(ROOT, out)).replace(/\\/g, "/") : null,
      size: T.w,
      evals: nEval,
      ...(timedOut ? { timedOut: true } : {}),
      free: free.length,
      locked: names.length - free.length,
      start: { score: r4(first.score), iou: r4(first.whole), zone: r4(first.zone), fam: first.fam, registeredIoU: await fullIoU(start) },
      end: { score: r4(best.score), iou: r4(best.whole), zone: r4(best.zone), fam: best.fam, registeredIoU: await fullIoU(cur) },
      knobs: Object.fromEntries(free.filter((n) => cur[n] !== start[n]).map((n) => [n, { from: start[n], to: cur[n] }])),
      sweeps,
      steps,
      ms: Math.round(performance.now() - t0),
    };
    if (out) {
      const outPath = path.resolve(ROOT, out);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, replaceKnobValues(text, cur));
      const logPath = path.resolve(ROOT, log ?? out.replace(/\.mjs$/, "") + ".fit.json");
      fs.writeFileSync(logPath, `${JSON.stringify(record, null, 2)}\n`);
      record.log = path.relative(ROOT, logPath).replace(/\\/g, "/");
    }
    record.values = cur;
    return record;
  } finally {
    setKnobs(start);   // the module object is cached by text: leave it as its file says
  }
}

// ---------------------------------------------------------------------------
// V5-4 item 2 — the PER-FEATURE FIT stage (research/WF-V5-ACCURACY.md, Opus audit item 5)
//
// After the global FIT / re-FIT, before a seat call: for every inventory item the accuracy report does not call exact
// (status "off"), coordinate descent over ONLY the knobs that move that item's parts (attribution: each free non-massing
// knob is stepped once and every part whose aabb / volume changes is "moved" by it — rc_<feature>N and whatever else
// builds that feature), scored INSIDE the item's ROI at full resolution (project.mjs roi window, 1 target px per px) by
// accuracy.featureScore: ROI IoU - edge-chamfer term - centroid / equivalent-diameter term. Every accepted move keeps
// the whole-silhouette IoU (fit raster) >= the stage start - WHOLE_SLACK and passes the per-eval gate; each item's moves
// pass the whole chain or are reverted together. Items nearest to exact go first (fewest failed checks, then px).
// Deterministic (fixed order, fixed steps, 4-decimal values), bounded by `evals`, FEATURE_TIME_MS and the caller's
// deadline. The written module is kept only if the accuracy report's exact count does not drop and the registered IoU
// does not fall more than FEATURE_IOU_EPS; else the input text is restored (record.reverted says why).
// ---------------------------------------------------------------------------

export const FEATURE_EVALS = 320;
export const FEATURE_ITEM_EVALS = 24;
export const FEATURE_PAD = 6;
export const FEATURE_TIME_MS = 240 * 1000;   // V5-5 item 6: raised (still capped by the caller's deadline) so every item is visited
export const FEATURE_IOU_EPS = 0.0005;
const FEATURE_ACCEPT = 1e-4;
const GEOMETRY_FAILS = ["pos", "size", "roiIoU", "edge"];

/** A part's shape signature (aabb + volume): a knob "moves" a part when it changes this. */
function sigOf(part) {
  const b = part.solid.aabb();
  const flat = [...(b.min ?? b[0] ?? []), ...(b.max ?? b[1] ?? [])];
  return `${flat.map((v) => Math.round(v * 1e5)).join(",")}|${Math.round(part.solid.volume() * 1e6)}`;
}

/**
 * @param {{subjectId:string, modulePath:string, out?:string|null, evals?:number, perItem?:number, deadline?:number|null,
 *   size?:number, report?:object|null, log?:string|null}} o   report: an in-process accuracy() of modulePath (reused)
 * @returns {Promise<object>} {items: [{id, fails, knobs, evals, before, after, moved}], evals, ms, values, kept, ...}
 */
export async function fitFeatures({ subjectId, modulePath, out = null, evals = FEATURE_EVALS, perItem = FEATURE_ITEM_EVALS, deadline = null, size = FIT_SIZE, report = null, log = null }) {
  const t0 = performance.now();
  const stopAt = Math.min(deadline ?? Infinity, t0 + FEATURE_TIME_MS);
  const late = () => performance.now() > stopAt;
  const S = loadSubject(subjectId);
  await K.init();
  if (K.assemble?.ready) await K.assemble.ready;
  try { K.configure(gateConfig(S.cls)); } catch { K.configure(null); }
  const rules = await import(pathToFileURL(path.join(ROOT, S.cls.rules)).href);
  const layout = gateLayout(S, rules);   // V5-9: accuracy-covered layout keys are advisory
  const inPath = path.resolve(ROOT, modulePath);
  const text = fs.readFileSync(inPath, "utf8");
  const mod = await loadModule(modulePath);
  if (!mod.KNOBS || typeof mod.KNOBS !== "object") return { skipped: "no KNOBS block", items: [], evals: 0, ms: 0 };
  const KN = mod.KNOBS;
  const names = Object.keys(KN);
  const start = knobsFromText(text, names);
  const setKnobs = (vals) => { for (const n of names) KN[n].v = vals[n]; };
  const build = (vals) => {
    setKnobs(vals);
    try { const parts = mod.build(); return K.checkParts(mod.meta, parts).length ? null : parts; } catch { return null; }
  };
  let census = null;
  const gate = async (parts, skip) => validateParts(mod.meta, parts, undefined, { cls: S.cls, rules, layout, census, ...(skip ? { skip } : {}) });
  try {
    const rep0 = report ?? await accuracy({ subjectId, modulePath });
    const img = await readRGB(S.paths.target);
    const TF = targetOf(S, img, { palette: mod.meta.palette });
    const T = await fitTarget(S, size);
    const startParts = build(start);
    if (!startParts) throw new Error(`fitFeatures: ${modulePath} does not build at its own KNOBS`);
    const rolesBuilt = new Set(startParts.map((p) => p.role));
    const raw = S.readJson("census") ?? {};
    census = Object.fromEntries(Object.entries(raw).filter(([k]) => !k.startsWith("_") && rolesBuilt.has(S.cls.censusRules?.[k]?.role)));
    if (!(await gate(startParts, null)).pass) return { skipped: "the start module fails the gate", items: [], evals: 0, ms: Math.round(performance.now() - t0) };

    // attribution: knob -> the part ids it moves (one deterministic step each, + first, else -)
    const free = names.filter((n) => !KN[n].locked && KN[n].max > KN[n].min && !MASSING_KNOBS.includes(n));
    const baseSig = new Map(startParts.map((p) => [p.id, sigOf(p)]));
    const moves = {};
    for (const n of free) {
      if (late()) break;
      await yieldTask();
      const d = (KN[n].max - KN[n].min) / 8;
      let parts = null;
      for (const c of [r4(Math.min(KN[n].max, start[n] + d)), r4(Math.max(KN[n].min, start[n] - d))]) {
        if (c === start[n]) continue;
        parts = build({ ...start, [n]: c });
        if (parts) break;
      }
      if (!parts) { moves[n] = new Set(); continue; }
      const now = new Map(parts.map((p) => [p.id, sigOf(p)]));
      moves[n] = new Set([...new Set([...baseSig.keys(), ...now.keys()])].filter((id) => baseSig.get(id) !== now.get(id)));
    }

    let nEval = 0;
    let cur = { ...start };
    const wholeProj = (parts) => project({ subjectId, modulePath, frame: "target", size: T.w, built: { meta: mod.meta, parts, frame: frameOf(KN) } });
    const turnDeg = frontRotationDeg(mod.meta.front);
    /** the ROI score first; the whole-frame raster (the hold) only for a candidate that beats bar */
    const evaluate = async (vals, roi, feat, bar = -Infinity) => {
      nEval += 1;
      await yieldTask();
      const parts = build(vals);
      if (!parts) return null;
      const meshed = meshParts(parts, turnDeg);
      const win = await project({ subjectId, modulePath, frame: "target", size: img.w, roi, built: { meta: mod.meta, parts, frame: frameOf(KN), meshed } });
      const f = featureScore(win, TF, feat, partFamilies(S, win.parts, TF));
      if (f.score <= bar) return { ...f, whole: null, parts };
      const whole = await project({ subjectId, modulePath, frame: "target", size: T.w, built: { meta: mod.meta, parts, frame: frameOf(KN), meshed } });
      return { ...f, whole: iou(T.tfg, whole.partId, { ids: true }), parts };
    };
    const wholeOf = async (vals) => iou(T.tfg, (await wholeProj(build(vals))).partId, { ids: true });
    const regIoU = async (vals) => {
      const p = await project({ subjectId, modulePath, frame: "target", size: img.w, built: { meta: mod.meta, parts: build(vals), frame: frameOf(KN) } });
      return iou(TF.state, p.partId, { ids: true });   // THE registered IoU (three-state target, full resolution)
    };
    const whole0 = await wholeOf(start);
    const reg0 = await regIoU(start);
    const wholeFloor = whole0 - WHOLE_SLACK;
    const minStep = (n) => MIN_STEP[KN[n].unit] ?? MIN_STEP.m;
    // a row off on colour / count only has nothing a knob can fix
    // V5-5 item 6: BIG items first (their knobs move the most px), then fewest failed checks
    const todo = rep0.items.filter((r) => r.status === "off" && r.feature && r.fails.some((f) => GEOMETRY_FAILS.includes(f)))
      .map((r, k) => ({ r, k }))
      .sort((a, b) => (b.r.px.target - a.r.px.target) || (a.r.fails.length - b.r.fails.length) || (a.k - b.k))
      .map(({ r }) => r);
    // V5-5 item 6: a knob that moves any part of an already-EXACT item is locked for this stage
    const exactIds = new Set(rep0.items.filter((r) => r.status === "exact" && r.feature).flatMap((r) => r.feature.partIds));
    const items = [];
    for (const [idx, row] of todo.entries()) {
      if (nEval >= evals || late()) { items.push({ id: row.id, fails: row.fails, skipped: late() ? "time" : "stage eval budget" }); continue; }
      const feat = row.feature;
      const ids = new Set(feat.partIds);
      const touching = free.filter((n) => [...(moves[n] ?? [])].some((id) => ids.has(id)));
      const knobs = touching.filter((n) => ![...moves[n]].some((id) => exactIds.has(id)));
      if (!knobs.length) { items.push({ id: row.id, fails: row.fails, skipped: touching.length ? "every knob that moves it moves an exact item" : "no free knob moves it" }); continue; }
      const roi = { x0: feat.box.x0 - FEATURE_PAD, y0: feat.box.y0 - FEATURE_PAD, x1: feat.box.x1 + FEATURE_PAD, y1: feat.box.y1 + FEATURE_PAD };
      const itemStart = { ...cur };
      let best = await evaluate(cur, roi, feat);
      if (!best) { items.push({ id: row.id, fails: row.fails, skipped: "does not build" }); continue; }
      const snap = (b) => ({ score: r4(b.score), roiIoU: b.roiIoU, chamferPx: b.chamferPx, centrePx: b.centrePx, diamPx: b.diamPx });
      const before = snap(best);
      // V5-5 item 6: a fair share of the remaining evals so the last item is visited too
      const until = Math.min(evals, nEval + Math.min(perItem, Math.max(6, Math.floor((evals - nEval) / (todo.length - idx)))));
      const step = Object.fromEntries(knobs.map((n) => [n, (KN[n].max - KN[n].min) / 8]));
      const pref = Object.fromEntries(knobs.map((n) => [n, 1]));
      const moved = {};
      while (nEval < until && !late()) {
        let active = false;
        for (const n of knobs) {
          if (nEval >= until || late()) break;
          if (step[n] < minStep(n)) continue;
          active = true;
          let ok = false;
          for (const dir of [pref[n], -pref[n]]) {
            const c = r4(Math.min(KN[n].max, Math.max(KN[n].min, cur[n] + dir * step[n])));
            if (c === cur[n]) continue;
            const cand = { ...cur, [n]: c };
            const s = await evaluate(cand, roi, feat, best.score + FEATURE_ACCEPT);
            if (s && s.score > best.score + FEATURE_ACCEPT && s.whole >= wholeFloor && (await gate(s.parts, FAST_SKIP)).pass) {
              moved[n] = [moved[n]?.[0] ?? cur[n], c];
              cur = cand; best = s; pref[n] = dir; ok = true;
              break;
            }
            if (nEval >= until) break;
          }
          if (!ok) step[n] /= 2;
        }
        if (!active) break;
      }
      let reverted = null;
      if (Object.keys(moved).length && !(await gate(build(cur), null)).pass) { cur = itemStart; reverted = "the whole chain fails"; }
      items.push({ id: row.id, fails: row.fails, knobs: knobs.length, evals: nEval, before, after: reverted ? before : snap(best), moved: reverted ? {} : moved, ...(reverted ? { reverted } : {}) });
    }
    const reg1 = await regIoU(cur);
    const record = {
      subject: subjectId, module: path.relative(ROOT, inPath).replace(/\\/g, "/"), evals: nEval, free: free.length,
      wholeFit: [r4(whole0), r4(await wholeOf(cur))], registeredIoU: [r4(reg0), r4(reg1)], items, ms: 0, values: cur, kept: false,
      exact: { before: rep0.summary, after: null },
      ...(late() ? { timedOut: true } : {}),
    };
    setKnobs(start);
    const changed = names.some((n) => cur[n] !== start[n]);
    if (out && changed) {
      const outPath = path.resolve(ROOT, out);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, replaceKnobValues(text, cur));
      // kept only if the exact count does not drop and the registered IoU holds
      const rep1 = await accuracy({ subjectId, modulePath: out });
      record.exact.after = rep1.summary;
      if (rep1.exactN < rep0.exactN || reg1 < reg0 - FEATURE_IOU_EPS) {
        fs.writeFileSync(outPath, text);
        record.reverted = `exact ${rep0.exactN} -> ${rep1.exactN}, registered IoU ${r4(reg0)} -> ${r4(reg1)}`;
        record.values = start;
      } else { record.kept = true; record.report = rep1; }
    } else if (out && path.resolve(ROOT, out) !== inPath) {
      fs.writeFileSync(path.resolve(ROOT, out), text);
    }
    record.ms = Math.round(performance.now() - t0);
    if (log) fs.writeFileSync(path.resolve(ROOT, log), `${JSON.stringify({ ...record, values: undefined, report: undefined }, null, 2)}\n`);
    return record;
  } finally {
    setKnobs(start);
  }
}

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject");
  const modulePath = arg("module");
  const out = arg("out");
  if (!subjectId || !modulePath || !out) {
    console.error("usage: node scripts/fit.mjs --subject <id> --module <in.mjs> --out <out.mjs> [--evals 300] [--size 384] [--log <fit.json>]");
    process.exit(3);
  }
  const r = await fit({ subjectId, modulePath, out, evals: Number(arg("evals", FIT_EVALS)), size: Number(arg("size", FIT_SIZE)), log: arg("log") });
  console.log(`[fit] ${r.module} -> ${r.out}: ${r.evals} evals, ${r.free} free / ${r.locked} locked knobs, ${r.ms} ms`);
  console.log(`  registered IoU ${r.start.registeredIoU} -> ${r.end.registeredIoU}; score ${r.start.score} -> ${r.end.score} (zone ${r.start.zone} -> ${r.end.zone})`);
  console.log(`  moved: ${Object.entries(r.knobs).map(([k, v]) => `${k} ${v.from} -> ${v.to}`).join(", ") || "none"}`);
  console.log(`  log ${r.log}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(`fit: ${error.message}`); process.exit(1); });
}
