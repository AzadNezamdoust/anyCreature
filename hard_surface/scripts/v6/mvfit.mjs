#!/usr/bin/env node
// WORKFLOW v6 — MULTI-VIEW FIT (research/WF-V6-PLAN.md B). A thin stage beside scripts/fit.mjs (generic since V6-2):
//
//   node scripts/v6/mvfit.mjs --subject school_bus --module out/v6/bus-start.mjs --out out/v6/B.mjs [--views concept,side,front,rear,top]
//
// Objective = the weighted MEAN over views of silhouette IoU — the concept view (registered frame, THE registered IoU of
// scripts/registered.mjs, weight CONCEPT_W) + each orthographic turnaround view (scripts/v6/ortho.mjs, weight 1) — so
// every part is seen along two axes at least and no coordinate keeps a free direction along one camera ray. Stages:
// knob group "body" (+ the concept-view "frame" similarity) first, then "feature" (ortho zone IoU of the subject's zone
// families added to each ortho term). A knob without `group`: FRAME_KNOBS -> frame, rc_* (READY calls) -> feature, else
// body (the class template's massing knobs). Coordinate descent (fixed knob order, +-step inside [min, max], halve on a double
// failure) — deterministic. The ranges are the prior card's soft ranges (subjects/<id>/prior.json); the turnaround wins.
// MVP-STUB: no kernel-chain gate per eval (K.checkParts + a successful build() only); the judge reports the checks.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import * as K from "../../src/kernel/index.mjs";
import { ROOT, loadSubject } from "../subject.mjs";
import { loadModule, meshParts, project } from "../project.mjs";
import { fitTarget, yieldTask } from "../fit.mjs";
import { FRAME_KNOBS, frameOf, iou } from "../registered.mjs";
import { replaceKnobValues } from "../knobs.mjs";
import { basisOf, loadTurnaround, partFamilies, rasterOrtho, viewMap, viewScore, viewTarget } from "./ortho.mjs";

export const CONCEPT_W = 2;
export const MV_SIZE = 256;
export const STAGE_EVALS = Object.freeze({ body: 320, feature: 120 });
const MIN_STEP = { m: 0.002, frac: 0.001, scale: 0.001, px: 0.25 };
const r4 = (v) => Math.round(v * 1e4) / 1e4;

/** The subject's registered turnaround (V6-1 name; = ortho.mjs loadTurnaround). */
export const subjectOrthos = loadTurnaround;
export { partFamilies };

/** A knob's FIT stage: its `group`, else frame / feature (rc_* READY-call knobs) / body. */
export const knobGroup = (name, k) => k.group ?? (FRAME_KNOBS.includes(name) ? "frame" : name.startsWith("rc_") ? "feature" : "body");

/**
 * Score one built part list on the requested views. weights: {concept?, side?, front?, rear?, top?}; zones: add the
 * ortho zone IoU. Returns { score, views: {name: {iou, zone?, fam?}} }.
 */
export async function scoreViews({ subjectId, meta, parts, KNOBS, weights, zones = false, size = MV_SIZE, sigma = 1 }) {
  const { reg, table } = await loadTurnaround(subjectId);
  const S = loadSubject(subjectId);
  const views = {};
  let num = 0;
  let den = 0;
  const ortho = reg.names.filter((v) => weights[v]);
  if (ortho.length) {
    const { meshes } = meshParts(parts, 0);
    const fam = partFamilies(parts, meta.palette, table);
    for (const v of ortho) {
      const m = viewMap(reg, v, size);
      const T = viewTarget(reg, v, size);
      const { partId } = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: m.k * sigma, bx: m.bx, by: m.by }, m.w, m.h);
      const s = viewScore(T, partId, fam, table);
      views[v] = { iou: r4(s.iou), zone: r4(s.zone), fam: Object.fromEntries(Object.entries(s.fam).map(([k, x]) => [k, r4(x)])) };
      num += weights[v] * (s.iou + (zones ? s.zone : 0));
      den += weights[v];
    }
  }
  if (weights.concept) {
    const T = await fitTarget(S, size);
    const proj = await project({ subjectId, frame: "target", size, built: { meta, parts, frame: frameOf(KNOBS) } });
    const c = iou(T.tfg, proj.partId, { ids: true });
    views.concept = { iou: r4(c) };
    num += weights.concept * c;
    den += weights.concept;
  }
  return { score: den ? num / den : 0, views };
}

/**
 * @param {{subjectId:string, modulePath:string, out:string, views?:string[], evals?:object, size?:number, log?:string,
 *   deadline?:number}} o  deadline: performance.now() ms after which no stage evaluates further
 */
export async function mvFit({ subjectId, modulePath, out, views = null, evals = STAGE_EVALS, size = MV_SIZE, log = null, deadline = Infinity }) {
  await K.init();
  views ??= ["concept", ...(await loadTurnaround(subjectId)).reg.names];
  const t0 = performance.now();
  const text = fs.readFileSync(path.resolve(ROOT, modulePath), "utf8");
  const mod = await loadModule(modulePath);
  const saved = Object.fromEntries(Object.entries(mod.KNOBS).map(([n, k]) => [n, k.v]));
  const weights = Object.fromEntries(views.map((v) => [v, v === "concept" ? CONCEPT_W : 1]));
  const record = { subject: subjectId, module: modulePath, out, views: weights, size, stages: [] };
  try {
    const evalOnce = async (zones) => {
      let parts;
      try {
        parts = mod.build();
        const bad = K.checkParts(mod.meta, parts);
        if (bad.length) return null;
      } catch { return null; }
      const r = await scoreViews({ subjectId, meta: mod.meta, parts, KNOBS: mod.KNOBS, weights, zones, size });
      await yieldTask();
      return r;
    };
    for (const [stage, budget] of Object.entries(evals)) {
      const zones = stage === "feature";
      const names = Object.keys(mod.KNOBS).filter((n) => {
        const g = knobGroup(n, mod.KNOBS[n]);
        if (mod.KNOBS[n].min === mod.KNOBS[n].max || mod.KNOBS[n].locked) return false;
        if (g === "frame") return stage === "body" && weights.concept;   // the concept similarity rides with the body
        return g === stage;
      });
      let best = await evalOnce(zones);
      if (!best) throw new Error(`mvfit: ${modulePath} does not build at its start values`);
      const start = best;
      const step = Object.fromEntries(names.map((n) => [n, 0.1 * (mod.KNOBS[n].max - mod.KNOBS[n].min)]));
      let used = 1;
      let accepted = 0;
      while (used < budget && performance.now() < deadline) {
        let active = false;
        for (const n of names) {
          const k = mod.KNOBS[n];
          if (step[n] < (MIN_STEP[k.unit] ?? 0.002)) continue;
          active = true;
          const v0 = k.v;
          let won = false;
          for (const dir of [1, -1]) {
            if (used >= budget || performance.now() >= deadline) break;
            const v = r4(Math.min(k.max, Math.max(k.min, v0 + dir * step[n])));
            if (v === v0) continue;
            k.v = v;
            const r = await evalOnce(zones);
            used += 1;
            if (r && r.score > best.score + 1e-6) { best = r; won = true; accepted += 1; break; }
            k.v = v0;
          }
          if (!won) step[n] /= 2;
          if (used >= budget) break;
        }
        if (!active) break;
      }
      record.stages.push({ stage, knobs: names, evals: used, accepted, start: { score: r4(start.score), views: start.views }, end: { score: r4(best.score), views: best.views } });
    }
    const values = Object.fromEntries(Object.entries(mod.KNOBS).map(([n, k]) => [n, k.v]));
    record.knobs = values;
    record.ms = Math.round(performance.now() - t0);
    if (out) {
      fs.mkdirSync(path.dirname(path.resolve(ROOT, out)), { recursive: true });
      fs.writeFileSync(path.resolve(ROOT, out), replaceKnobValues(text, values));
    }
    if (log) fs.writeFileSync(path.resolve(ROOT, log), `${JSON.stringify(record, null, 2)}\n`);
    return record;
  } finally {
    for (const [n, v] of Object.entries(saved)) mod.KNOBS[n].v = v;   // the cached module object is shared
  }
}

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject", "school_bus");
  const modulePath = arg("module");
  const out = arg("out");
  if (!modulePath || !out) { console.error("usage: node scripts/v6/mvfit.mjs --subject <id> --module <in.mjs> --out <out.mjs> [--views concept,side,...]"); process.exit(3); }
  const views = arg("views") ? arg("views").split(",") : undefined;
  const rec = await mvFit({ subjectId, modulePath, out, views, log: out.replace(/\.mjs$/, ".fit.json") });
  for (const s of rec.stages) console.log(`[mvfit] ${s.stage}: ${s.evals} evals, ${s.accepted} accepted, score ${s.start.score} -> ${s.end.score}`, JSON.stringify(Object.fromEntries(Object.entries(s.end.views).map(([k, v]) => [k, v.iou]))));
  console.log(`[mvfit] ${out} in ${(rec.ms / 1000).toFixed(0)} s`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(error); process.exit(1); });
}
