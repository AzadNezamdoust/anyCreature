// WORKFLOW v7 — the modeller's shared toolkit (scripts/v7/README.md): helpers every v7 CLI uses. Pure helpers first
// (unit-tested in lib.test.mjs), then the subject/module context loaders, which only wire the existing exports of
// scripts/project.mjs, scripts/registered.mjs and scripts/v6/ortho.mjs together (no registration / IoU logic here).
import fs from "node:fs";
import path from "node:path";

import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { loadModule, meshParts, project } from "../project.mjs";
import { FG_MAX, frameOf, iou, readRGB, targetState } from "../registered.mjs";
import { hasTurnaround, loadTurnaround, maskOptions, readJson, turnaroundDir, viewsFile } from "../v6/ortho.mjs";
import { frontRotationDeg } from "../../src/kernel/toThree.mjs";
import * as K from "../../src/kernel/index.mjs";

// ---------------------------------------------------------------------------------------------------------------
// Pure helpers
// ---------------------------------------------------------------------------------------------------------------

/** argv -> { _: positionals, <flag>: value | true }. `--x v` takes v unless x is in `booleans` or v starts with --. */
export function parseArgs(argv, booleans = []) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (!a.startsWith("--") || /^--?\d/.test(a)) { out._.push(a); continue; }
    const eq = a.indexOf("=");
    if (eq > 0) { out[a.slice(2, eq)] = a.slice(eq + 1); continue; }
    const name = a.slice(2);
    const next = argv[i + 1];
    if (booleans.includes(name) || next === undefined || (next.startsWith("--") && !/^--?\d/.test(next))) out[name] = true;
    else { out[name] = next; i += 1; }
  }
  return out;
}

const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** Author-frame point -> image px through a framed registration ({s, ox, oy, basis:{right, up}}). */
export function projectPoint(reg, p) {
  return [reg.s * dot3(p, reg.basis.right) + reg.ox, -reg.s * dot3(p, reg.basis.up) + reg.oy];
}

/**
 * Image px (X, Y) -> the author-frame point on the plane p[axis] = value (axis 0|1|2 or "x"|"y"|"z"): solves
 * s (R.p) + ox = X, -s (U.p) + oy = Y with p[axis] fixed. Throws when the plane is edge-on to the camera.
 */
export function unprojectPoint(reg, X, Y, axis, value) {
  const ax = typeof axis === "string" ? "xyz".indexOf(axis) : axis;
  if (!(ax >= 0 && ax <= 2)) throw new Error(`unproject: axis must be x, y or z (got ${axis})`);
  const { right: R, up: U } = reg.basis;
  const r = (X - reg.ox) / reg.s, u = (reg.oy - Y) / reg.s;
  const o = [0, 1, 2].filter((k) => k !== ax);
  const rr = r - R[ax] * value, uu = u - U[ax] * value;
  const det = R[o[0]] * U[o[1]] - R[o[1]] * U[o[0]];
  if (Math.abs(det) < 1e-9) throw new Error(`unproject: the plane ${"xyz"[ax]} = ${value} is edge-on in this view`);
  const p = [0, 0, 0];
  p[ax] = value;
  p[o[0]] = (rr * U[o[1]] - uu * R[o[1]]) / det;
  p[o[1]] = (R[o[0]] * uu - U[o[0]] * rr) / det;
  return p;
}

/** Per-channel median of the px in the rect (x, y, w, h) of a raw image ({data, width, channels}). */
export function medianColour(data, width, channels, [x, y, w, h]) {
  const ch = [[], [], []];
  for (let yy = y; yy < y + h; yy += 1) for (let xx = x; xx < x + w; xx += 1) {
    const j = (yy * width + xx) * channels;
    for (let c = 0; c < 3; c += 1) ch[c].push(data[j + c]);
  }
  return ch.map((a) => a.sort((p, q) => p - q)[a.length >> 1]);
}

export const hexOf = (rgb) => "#" + rgb.map((v) => v.toString(16).padStart(2, "0")).join("");

/**
 * Runs of similar colour along a px sequence: a px joins the current run when every channel is within `tol` of the
 * run's FIRST px (tol < 0 = never merge by colour) or, with `label`, when its label equals the run's.
 * @param {number[][]} pixels  [[r, g, b], ...] in order; index i is reported as start + i
 * @returns {{s:number, e:number, c:number[], label?:string}[]}
 */
export function colourRuns(pixels, start = 0, { tol = 18, label = null } = {}) {
  const out = [];
  let run = null;
  for (let i = 0; i < pixels.length; i += 1) {
    const c = pixels[i];
    const l = label ? label(c) : undefined;
    const same = run && (label ? l === run.label : Math.max(...c.map((v, k) => Math.abs(v - run.c[k]))) <= tol);
    if (same) { run.e = start + i; continue; }
    if (run) out.push(run);
    run = { s: start + i, e: start + i, c, ...(label ? { label: l } : {}) };
  }
  if (run) out.push(run);
  return out;
}

/** The coordinate-search schedule [[scale step, px step], ...] (school_bus fitframe.mjs; delivery_truck used 0.001 last). */
export const DEFAULT_STAGES = Object.freeze([[0.02, 8], [0.01, 4], [0.005, 2], [0.0025, 1], [0.00125, 0.5]]);

/** "0.02:8,0.01:4" -> [[0.02, 8], [0.01, 4]] */
export function parseStages(text) {
  const st = String(text).split(",").map((s) => s.split(":").map(Number));
  if (!st.length || st.some((p) => p.length !== 2 || !p.every(Number.isFinite))) throw new Error(`bad --stages "${text}" (want ds:dp,ds:dp,...)`);
  return st;
}

/**
 * Coordinate search over a frame {scale, tx, ty}: per stage, try +-ds on scale, +-dp on tx, ty (in that order) and move
 * on every strict improvement (> 1e-6) until a full pass improves nothing. `f` is async frame -> score.
 * @returns {{frame, v, trace:{ds, dp, frame, v}[]}}
 */
export async function coordinateSearch(f, start, stages = DEFAULT_STAGES, startValue = null) {
  let cur = { scale: start.scale, tx: start.tx, ty: start.ty };
  let best = startValue ?? await f(cur);
  const trace = [];
  for (const [ds, dp] of stages) {
    let improved = true;
    while (improved) {
      improved = false;
      for (const [k, d] of [["scale", ds], ["tx", dp], ["ty", dp]]) {
        for (const s of [1, -1]) {
          const c = { ...cur, [k]: cur[k] + s * d };
          const v = await f(c);
          if (v > best + 1e-6) { best = v; cur = c; improved = true; }
        }
      }
    }
    trace.push({ ds, dp, frame: { ...cur }, v: best });
  }
  return { frame: cur, v: best, trace };
}

/** Coarse grid around a frame: scale x (1 + ds), tx + d, ty + d over the offset lists (the start itself included). */
export function gridFrames(start, { scale = [-0.03, -0.015, 0, 0.015, 0.03], px = [-8, -4, 0, 4, 8] } = {}) {
  const out = [];
  for (const a of scale) for (const b of px) for (const c of px) out.push({ scale: start.scale * (1 + a), tx: start.tx + b, ty: start.ty + c });
  return out;
}

export const roundFrame = (fr) => ({ scale: +fr.scale.toFixed(4), tx: +fr.tx.toFixed(2), ty: +fr.ty.toFixed(2) });

/**
 * Apply JSON overrides to a loaded module and build it. Keys naming a KNOB set that knob's `v` for this build (restored
 * after); every other key goes to buildWith(o) (one-level merge with the module's DEFAULTS when both are objects).
 * @returns {{parts, frameKnobs: object}}  frameKnobs = the KNOBS frame values in force for this build
 */
export function buildVariant(mod, overrides) {
  const knobs = mod.KNOBS ?? {};
  const knobKeys = Object.keys(overrides).filter((k) => k in knobs);
  const rest = Object.fromEntries(Object.entries(overrides).filter(([k]) => !(k in knobs)).map(([k, v]) => {
    const d = mod.DEFAULTS?.[k];
    return [k, v && typeof v === "object" && !Array.isArray(v) && d && typeof d === "object" && !Array.isArray(d) ? { ...d, ...v } : v];
  }));
  const unknown = mod.DEFAULTS ? Object.keys(rest).filter((k) => !(k in mod.DEFAULTS)) : [];
  if (unknown.length) throw new Error(`overrides ${unknown.join(", ")} are neither KNOBS nor DEFAULTS keys`);
  if (Object.keys(rest).length && typeof mod.buildWith !== "function") {
    throw new Error(`overrides ${Object.keys(rest).join(", ")} are not KNOBS and the module exports no buildWith(o)`);
  }
  const saved = Object.fromEntries(knobKeys.map((k) => [k, knobs[k].v]));
  try {
    for (const k of knobKeys) knobs[k].v = overrides[k];
    const parts = Object.keys(rest).length ? mod.buildWith(rest) : mod.build();
    return { parts, frame: frameOf(knobs) };
  } finally {
    for (const k of knobKeys) knobs[k].v = saved[k];
  }
}

/** WF v8 variant rule "concept-first" defaults: the ortho agree drop that disqualifies, the concept agree tie band. */
export const CONCEPT_FIRST = Object.freeze({ drop: 0.01, tie: 0.002 });

/**
 * WF v8 variant rule "concept-first" (research/v7/WF-REVIEW-opus.md C4; variants.mjs --rule concept-first) over judged
 * rows [{label, metrics}] ("BASE" = the module as is, "#n ..." = the n-th variant; built rows only). Agree = views[v].agree
 * (views[v].iou when absent). 1. a variant whose agree drops by more than `drop` vs BASE in any ortho view is
 * disqualified; 2. the best concept agree wins, candidates within `tie` of the best are tied; 3. a tie goes to the higher
 * minimum ortho agree; 4. a remaining tie goes to BASE, then the lowest #n.
 * @returns {{winner: string|null, dq: {tag:string, reasons:string[]}[], tied: string[], lines: string[]}}  winner = "BASE"
 *   | "#n" (null without a BASE row)
 */
export function conceptFirst(rows, { drop = CONCEPT_FIRST.drop, tie = CONCEPT_FIRST.tie } = {}) {
  const EPS = 1e-9;
  const tagOf = (r) => (r.label === "BASE" ? "BASE" : String(r.label).split(" ")[0]);
  const numOf = (r) => (r.label === "BASE" ? 0 : Number(/^#(\d+)/.exec(r.label)?.[1] ?? Infinity));
  const agree = (r, v) => r.metrics.views[v].agree ?? r.metrics.views[v].iou;
  const f4 = (x) => x.toFixed(4);
  const base = rows.find((r) => r.label === "BASE");
  if (!base) return { winner: null, dq: [], tied: [], lines: ["rule concept-first: BASE did not build — no winner"] };
  const orthos = Object.keys(base.metrics.views).filter((v) => v !== "concept");
  const minOrtho = (r) => Math.min(...orthos.map((v) => agree(r, v)));
  const dq = [];
  const cand = [];
  for (const r of rows) {
    const reasons = r === base ? [] : orthos.filter((v) => agree(base, v) - agree(r, v) > drop + EPS)
      .map((v) => `${v} agree ${f4(agree(r, v))} < BASE ${f4(agree(base, v))} - ${drop}`);
    if (reasons.length) dq.push({ tag: tagOf(r), reasons }); else cand.push(r);
  }
  const best = Math.max(...cand.map((r) => agree(r, "concept")));
  const tied = cand.filter((r) => best - agree(r, "concept") <= tie + EPS);
  const cmp = (a, b) => {
    const dm = minOrtho(b) - minOrtho(a);
    if (Math.abs(dm) > EPS) return dm;
    if ((a === base) !== (b === base)) return a === base ? -1 : 1;
    const dc = agree(b, "concept") - agree(a, "concept");
    return Math.abs(dc) > EPS ? dc : numOf(a) - numOf(b);
  };
  const order = [...tied].sort(cmp);
  const lines = [
    `rule concept-first: DQ = an ortho agree below BASE - ${drop}; best concept agree wins; within ${tie} -> higher min ortho agree -> BASE`,
    ...dq.map((d) => `  DQ ${d.tag}: ${d.reasons.join("; ")}`),
    `  concept agree: ${cand.map((r) => `${tagOf(r)} ${f4(agree(r, "concept"))}`).join(" · ")}`,
    `  tied with the best (${f4(best)}): ${order.map((r) => `${tagOf(r)} (min ortho agree ${f4(minOrtho(r))})`).join(" · ")}`,
  ];
  return { winner: tagOf(order[0]), dq, tied: order.map(tagOf), lines };
}

// ---------------------------------------------------------------------------------------------------------------
// Context loaders (subject images, modules, the concept IoU)
// ---------------------------------------------------------------------------------------------------------------

export const r3 = (v) => v.toFixed(3);
export const f3 = (v) => v.map((n) => n.toFixed(3)).join(", ");

/** Absolute path of a module given relative to the cwd (the shared loader would resolve it against ROOT). */
export const modulePathOf = (p) => {
  if (!p || p === true) throw new Error("--module <file.mjs> is required");
  const abs = path.resolve(p);
  if (!fs.existsSync(abs)) throw new Error(`no module ${abs}`);
  return abs;
};

export async function importModule(modulePath) {
  await K.init();
  return loadModule(modulePathOf(modulePath));
}

/**
 * The image a measuring command reads: `--image <file>`, else the subject's concept (`--view concept`, the default) or
 * one turnaround view (`--view side|front|...`, subjects/<s>/turnaround/views.json).
 */
export function imagePathOf(args) {
  if (args.image && args.image !== true) return path.resolve(args.image);
  if (!args.subject || args.subject === true) throw new Error("--image <file> or --subject <s> [--view concept|<ortho view>] is required");
  const view = args.view && args.view !== true ? args.view : "concept";
  if (view === "concept") return loadSubject(args.subject).paths.target;
  if (!hasTurnaround(args.subject)) throw new Error(`${args.subject} has no turnaround (subjects/${args.subject}/turnaround/views.json)`);
  const spec = readJson(viewsFile(args.subject));
  if (!spec.views[view]) throw new Error(`${args.subject} has no view "${view}" (views: concept, ${Object.keys(spec.views).join(", ")})`);
  return path.join(turnaroundDir(args.subject), spec.views[view].file);
}

export async function readRaw(file) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data, width: info.width, height: info.height, channels: info.channels };
}

/** The subject's colour-family table when it has a turnaround (else null). */
export async function familyTableOf(subjectId) {
  if (!subjectId || subjectId === true || !hasTurnaround(subjectId)) return null;
  return (await loadTurnaround(subjectId)).table;
}

/**
 * The three-state concept target exactly as judge.mjs builds it (the turnaround family table's mask rule when present:
 * fgMax, enclosedFg, holes.concept).
 */
export async function conceptTarget(subjectId) {
  const S = loadSubject(subjectId);
  const table = await familyTableOf(subjectId);
  const img = await readRGB(S.paths.target);
  return { S, img, T: targetState(S, img, table?.fgMax ?? FG_MAX, maskOptions(table, "concept")) };
}

/**
 * A cached concept-IoU function of the frame for one build (the meshes are built once): frame -> THE registered IoU
 * (registered.mjs iou against targetState, the module rendered through project() frame "target").
 */
export function conceptIoUFn(subjectId, T, built) {
  const meshed = meshParts(built.parts, frontRotationDeg(built.meta.front));
  const cache = new Map();
  return async (fr) => {
    const key = `${fr.scale.toFixed(6)},${fr.tx.toFixed(4)},${fr.ty.toFixed(4)}`;
    if (cache.has(key)) return cache.get(key);
    const proj = await project({ subjectId, frame: "target", built: { meta: built.meta, parts: built.parts, frame: fr, meshed } });
    const v = iou(T, proj.partId, { ids: true });
    cache.set(key, v);
    return v;
  };
}

/** Coarse grid (optional) then coordinate search of the concept frame. */
export async function fitFrame(f, start, { grid = true, stages = DEFAULT_STAGES } = {}) {
  const v0 = await f(start);
  let from = { ...start }, fromV = v0, gridBest = null;
  if (grid) {
    for (const g of gridFrames(start)) {
      const v = await f(g);
      if (v > fromV + 1e-6) { from = g; fromV = v; }
    }
    gridBest = { frame: from, v: fromV };
  }
  const r = await coordinateSearch(f, from, stages, fromV);
  return { start: { frame: start, v: v0 }, gridBest, ...r };
}

export { ROOT };
