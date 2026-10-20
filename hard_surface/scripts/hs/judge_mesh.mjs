// Score a triangle mesh EXACTLY the way the gold judge (scripts/v6/judge.mjs judge()) scores a model.mjs: the same
// uniform scale sigma fit (fitSigma below = judge.mjs fitSigma verbatim: golden section on the mean ortho IoU at 256 px,
// 0.6..1.8, 22 steps), the same ortho rasteriser / targets / drift-rect care masks at JUDGE_SIZE (ortho.mjs rasterOrtho,
// viewMap, viewTarget, viewScore, viewDrift), and the same concept score (project.mjs project frame "target" with the
// gold module's frame knobs, registered.mjs targetState with the subject mask rule + the concept drift rects as
// don't-care: iou = plain registered IoU, agree = drift-masked). Read-only use of the repo scripts.
//
//   node scripts/hs/judge_mesh.mjs --subject <s> --mesh <mesh.json> [--out <scores.json>]
//   node scripts/hs/judge_mesh.mjs --subject <s> --module <model.mjs> [--export <mesh.json>] [--out ...]
//
// mesh.json (author frame metres: near flank +x, y up, nose +z — the frame of model.mjs and the glb):
//   { palette: {<zone>: "#rrggbb" | {top, front, side}}, parts: [{id, role, zone, pos: [x,y,z,...], tris: [a,b,c,...]}] }
//   tris wound counter-clockwise seen from outside (manifold / Blender convention).
// --module scores a real model.mjs through this same path (self-check against judge()); --export writes its geometry
// as mesh.json (for the Blender round-trip check: scripts/hs/build_from_mesh.py).
// The meta.front (concept turn) and KNOBS (concept frame) always come from out/ref/gold/<s>/model.mjs, as in the gate.
import fs from "node:fs";
import path from "node:path";

import { ROOT, loadSubject } from "../subject.mjs";
import { buildModule, loadModule, meshParts, project } from "../project.mjs";
import { frameOf, iou, readRGB, SUBJECT, OCCLUDED, targetState } from "../registered.mjs";
import { basisOf, driftRects, loadTurnaround, maskOptions, partFamilies, rasterOrtho, viewDrift, viewMap, viewScore, viewTarget } from "../v6/ortho.mjs";
import { JUDGE_SIZE } from "../v6/judge.mjs";
import { conceptRegistration, isDirectClass } from "../v7/conceptreg.mjs";   // WF v10: a direct class (weapon) has no registered.mjs anchor

const r4 = (v) => Math.round(v * 1e4) / 1e4;
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 && argv[i + 1] ? argv[i + 1] : null; };
const subjectId = arg("--subject");
if (!subjectId || !(arg("--mesh") || arg("--module"))) {
  console.error("usage: node judge_mesh.mjs --subject <s> (--mesh <mesh.json> | --module <model.mjs> [--export <mesh.json>]) [--out <json>]");
  process.exit(2);
}

/** The sigma objective: mean ortho IoU over the turnaround views at `size` px, model drawn at k * sg. */
function sigmaObjective(reg, meshes, size) {
  return (sg) => {
    let s = 0;
    for (const v of reg.names) {
      const m = viewMap(reg, v, size);
      const { partId } = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: m.k * sg, bx: m.bx, by: m.by }, m.w, m.h);
      s += iou(viewTarget(reg, v, size).fg, partId, { ids: true });
    }
    return s / reg.names.length;
  };
}

/** = scripts/v6/judge.mjs fitSigma (not exported there): best uniform model scale shared by the orthos. */
function fitSigma(reg, meshes, size) {
  const f = sigmaObjective(reg, meshes, size);
  let a = 0.6, b = 1.8;
  const g = (Math.sqrt(5) - 1) / 2;
  let c = b - g * (b - a), d = a + g * (b - a), fc = f(c), fd = f(d);
  for (let i = 0; i < 22; i += 1) {
    if (fc > fd) { b = d; d = c; fd = fc; c = b - g * (b - a); fc = f(c); } else { a = c; c = d; fc = fd; d = a + g * (b - a); fd = f(d); }
  }
  return (a + b) / 2;
}

/** 2026-10-10 robust fit (default; `--sigma-fit golden` = the judge's fit alone). The objective is NOT unimodal: on a
 * flat / thin subject (it_bounce_pad: a few-px-tall side strip at 256 px) the mean IoU swings ~0.01-0.03 per 0.25 %
 * of scale as edge rows cross pixel centres, and golden section hops into a side lobe (pass12: 1.0153 at mean IoU
 * .9446 while 1.0025 gives .9596). So: the judge's golden-section answer is candidate 0, plus a dense global scan
 * (0.6..1.8 step 0.005), the 5 best scan points refined at 0.0005 over +-0.005, the best refined at 0.0001 over
 * +-0.0005. The judge's answer is KEPT unless a candidate beats it by more than `keep` in the objective (default
 * SIGMA_KEEP below), so where golden section found the global optimum the result is bit-identical to judge().
 * keep: a vehicle (gold judge exists) 0.005 = judge-consistency first — over the 20 gold model.mjs only ambulance
 * (+.0028: judge.mjs's own fit sits in a side lobe, 1.0175 vs 1.0361) and attack_heli (+.0012) have any gain > 4e-4,
 * both kept so the harness keeps reproducing view/model-view.json; a direct subject (no judge to agree with) 0.001.
 * Evidence + before/after: out/score/sigma/compare.txt (re-run: out/score/sigma/compare.mjs). */
const SIGMA_KEEP = () => (DIRECT_CLASS ? 1e-3 : 5e-3);   // read at call time (DIRECT_CLASS is set below)
function fitSigmaRobust(reg, meshes, size, keepTol = SIGMA_KEEP()) {
  const f = sigmaObjective(reg, meshes, size);
  const cache = new Map();
  const F = (x) => { const k = Math.round(x * 1e6); if (!cache.has(k)) cache.set(k, f(x)); return cache.get(k); };
  const golden = fitSigma(reg, meshes, size);
  const fg = f(golden);
  const grid = (lo, hi, step) => { const r = []; for (let x = lo; x <= hi + 1e-9; x += step) r.push(+x.toFixed(6)); return r; };
  const scan = grid(0.6, 1.8, 0.005).map((x) => [x, F(x)]).sort((p, q) => q[1] - p[1]);
  let refined = [];
  for (const [x0] of scan.slice(0, 5)) for (const x of grid(x0 - 0.005, x0 + 0.005, 0.0005)) refined.push([x, F(x)]);
  refined.sort((p, q) => q[1] - p[1]);
  const x1 = refined[0][0];
  const fine = grid(x1 - 0.0005, x1 + 0.0005, 0.0001).map((x) => [x, F(x)]).sort((p, q) => q[1] - p[1]);
  const [best, fb] = fine[0];
  const keep = fb <= fg + keepTol;
  return { sigma: keep ? golden : best, fit: { method: keep ? "golden" : "scan", golden: r4(golden), goldenObj: r4(fg),
    scan: r4(best), scanObj: r4(fb), keep: keepTol, evals: cache.size + 25 } };
}

/** mesh.json parts -> kernel-like parts (solid.mesh() = {numProp, vertProperties, triVerts}, all meshParts reads). */
const asParts = (mesh) => mesh.parts.map((p) => ({
  id: p.id, role: p.role ?? p.id, zone: p.zone,
  solid: { mesh: () => ({ numProp: 3, vertProperties: Float32Array.from(p.pos), triVerts: Uint32Array.from(p.tris) }) },
}));

const goldPath = path.join(ROOT, "out", "ref", "gold", subjectId, "model.mjs");
const gold = fs.existsSync(goldPath) ? await loadModule(goldPath) : null;
const DIRECT_CLASS = isDirectClass(loadSubject(subjectId));
if (!gold && !DIRECT_CLASS) console.error(`WARN judge_mesh: no ${path.relative(ROOT, goldPath)} — concept front "+Z", identity frame`);
const goldMeta = gold?.meta ?? { front: "+Z" };
const goldFrame = frameOf(gold?.KNOBS ?? null);

let parts, palette, source;
if (arg("--module")) {
  const built = await buildModule(path.resolve(ROOT, arg("--module")));
  parts = built.parts;
  palette = built.meta.palette ?? {};
  source = arg("--module");
  if (arg("--export")) {
    const { meshes } = meshParts(parts, 0);
    const out = { palette, parts: parts.map((p, i) => ({ id: p.id, role: p.role, zone: p.zone, pos: Array.from(meshes[i].pos), tris: Array.from(meshes[i].tris) })) };
    fs.writeFileSync(path.resolve(arg("--export")), JSON.stringify(out));
  }
} else {
  const mesh = JSON.parse(fs.readFileSync(path.resolve(arg("--mesh")), "utf8"));
  parts = asParts(mesh);
  palette = mesh.palette ?? {};
  source = arg("--mesh");
}

const { reg, table } = await loadTurnaround(subjectId);
const S = loadSubject(subjectId);
const { meshes } = meshParts(parts, 0);
const SIGMA_FIT = arg("--sigma-fit") ?? "robust";   // "golden" = scripts/v6/judge.mjs fitSigma alone (pre-2026-10-10)
const { sigma, fit: sigmaFit } = SIGMA_FIT === "golden" ? { sigma: fitSigma(reg, meshes, 256), fit: { method: "golden" } }
  : fitSigmaRobust(reg, meshes, 256);
const fam = partFamilies(parts, palette, table);
const res = { source, sigma: r4(sigma), sigmaRaw: sigma, sigmaFit, views: {} };
for (const v of reg.names) {
  const m = viewMap(reg, v, JUDGE_SIZE);
  const { partId } = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: m.k * sigma, bx: m.bx, by: m.by }, m.w, m.h);
  const T = viewTarget(reg, v, JUDGE_SIZE);
  const s = viewScore(T, partId, fam, table);
  let refOnly = 0, modelOnly = 0;
  for (let i = 0; i < partId.length; i += 1) { const a = partId[i] >= 0, t = T.fg[i] === 1; if (t && !a) refOnly += 1; else if (a && !t) modelOnly += 1; }
  res.views[v] = { iou: r4(s.iou), agree: r4(s.agree), drift: r4(viewDrift(reg, v)), zone: r4(s.zone),
    fam: Object.fromEntries(Object.entries(s.fam).map(([k, x]) => [k, r4(x)])), px: JUDGE_SIZE, ref_only_px: refOnly, model_only_px: modelOnly };
}
// concept: judge.mjs lines "the concept view" — unscaled (sigma is NOT applied there), the gold module's frame knobs
const img = await readRGB(S.paths.target);
// WF v10 direct class: the same registered frame (X = s p.right + ox, Y = -s p.up + oy, author frame, turn 0) drawn by the
// ortho rasteriser through conceptreg.mjs's fixed-isometric registration; a vehicle: project.mjs, unchanged
let proj;
if (DIRECT_CLASS) {
  const creg = conceptRegistration(subjectId);
  proj = rasterOrtho(meshes, creg.basis, { k: creg.s, bx: creg.ox, by: creg.oy }, img.w, img.h);
} else proj = await project({ subjectId, frame: "target", built: { meta: { ...goldMeta, palette }, parts, frame: goldFrame } });
const cOpts = maskOptions(table, "concept");
const cRects = driftRects(table, "concept");
const T0 = targetState(S, img, table.fgMax, cOpts);
const TA = cRects ? targetState(S, img, table.fgMax, { ...cOpts, dontCare: cRects }) : T0;
const cIoU = iou(T0, proj.partId, { ids: true });
let subj = 0, masked = 0, refOnly = 0, modelOnly = 0;
for (let i = 0; i < T0.length; i += 1) {
  if (T0[i] === SUBJECT) { subj += 1; if (TA[i] === OCCLUDED) masked += 1; }
  if (TA[i] === OCCLUDED) continue;
  const a = proj.partId[i] >= 0, t = TA[i] === SUBJECT;
  if (t && !a) refOnly += 1; else if (a && !t) modelOnly += 1;
}
res.views.concept = { iou: r4(cIoU), agree: r4(cRects ? iou(TA, proj.partId, { ids: true }) : cIoU), drift: r4(subj ? masked / subj : 0),
  px: img.w, ref_only_px: refOnly, model_only_px: modelOnly };
res.concept = { target: path.relative(ROOT, S.paths.target).replace(/\\/g, "/"), front: goldMeta.front, frame: goldFrame };
res.minAgree = Math.min(...Object.values(res.views).map((x) => x.agree));
res.tris = parts.reduce((a, p) => a + p.solid.mesh().triVerts.length / 3, 0);
const text = JSON.stringify(res, null, 1);
if (arg("--out")) fs.writeFileSync(path.resolve(arg("--out")), text);
console.log(text);
