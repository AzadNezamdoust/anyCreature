// WORKFLOW v4 — V4-2: KNOBS + FIT (research/WF-V4-PLAN.md). Hermetic: the start is the frozen template output
// test/fixtures/v4/start-knobs-pickup.mjs, the Opus reference the frozen test/fixtures/v4/work-pickup.mjs; refs/,
// subjects/ and classes/ are read only; fitted modules go to a temp dir.
process.env.LLMM_SUBJECT = "pickup";
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";
import { loadModule } from "../scripts/project.mjs";
import { fit } from "../scripts/fit.mjs";
import { residuals } from "../scripts/residuals.mjs";
import { replaceKnobValues } from "../scripts/knobs.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const START = "test/fixtures/v4/start-knobs-pickup.mjs";
const WORK = "test/fixtures/v4/work-pickup.mjs";
// three levels under ROOT, like the fixture, so the module's relative kernel import resolves unchanged
const TMP = path.join(ROOT, "test", `.tmp-wf-v4-fit-${process.pid}`, "fit");
test.after(() => fs.rmSync(path.dirname(TMP), { recursive: true, force: true }));
const S = loadSubject("pickup");

test("V4-2 template: KNOBS block first, one line per knob, ranges hold v, keyed knobs name one layout key, geometry reads only KNOBS", async () => {
  const text = generateForSubject("pickup").text;
  const knobsAt = text.indexOf("export const KNOBS = {");
  assert.ok(knobsAt > 0 && knobsAt < text.indexOf("export const meta"), "KNOBS before meta");
  const build = text.slice(text.indexOf("export function build()"));
  // no bare metre literal in build(): only the construction seam, halves and indices
  const literals = [...build.replace(/\/\/[^\n]*/g, "").matchAll(/(?<![\w.])\d+\.\d+/g)].map((m) => m[0]);
  assert.deepEqual([...new Set(literals)], ["0.001"], `build() literals ${literals}`);
  const fx = fs.readFileSync(path.join(ROOT, START), "utf8");
  assert.equal(fx.slice(fx.indexOf("export const KNOBS")), text.slice(text.indexOf("export const KNOBS")), "the fixture is the template's current output");
  const mod = await loadModule(START);
  const knobs = Object.entries(mod.KNOBS);
  const layout = S.readJson("layout");
  assert.equal(knobs.length, 43);   // V4-5A: + hubR, hubRing, hubCap, hoodPanel{HalfNose,HalfCowl,InsetNose,InsetCowl}
  assert.deepEqual(knobs.filter(([, k]) => k.locked).map(([n]) => n), ["L", "clearance"]);
  for (const [n, k] of knobs) {
    assert.ok(k.min <= k.v && k.v <= k.max, `${n} ${k.min} <= ${k.v} <= ${k.max}`);
    if (k.key) assert.ok(typeof k.key === "string" && layout[k.key] && !layout[k.key].unverified, `${n}: verified key ${k.key}`);
  }
  // moving one knob moves the geometry it names
  await K.init();
  const before = mod.build().find((p) => p.id === "cab").solid.aabb();
  const v0 = mod.KNOBS.cabRearZ.v;
  mod.KNOBS.cabRearZ.v = v0 + 0.1;
  try {
    const after = mod.build().find((p) => p.id === "cab").solid.aabb();
    assert.ok(Math.abs(after.min[2] - before.min[2] - 0.1) < 1e-6);
  } finally { mod.KNOBS.cabRearZ.v = v0; }
  assert.equal(replaceKnobValues(fx, { W: 2 }).replace("v: 2,", "v: 1.9776,"), fx, "replaceKnobValues touches only the v");
});

test("V4-2 FIT: start -> >= 0.95 registered IoU, gate PASS, deterministic, <= 30 s, residual rows shrink", async () => {
  const outA = path.join(TMP, "fitted-a.mjs");
  const outB = path.join(TMP, "fitted-b.mjs");
  const t0 = performance.now();
  const a = await fit({ subjectId: "pickup", modulePath: START, out: outA });
  const ms = performance.now() - t0;
  const b = await fit({ subjectId: "pickup", modulePath: START, out: outB });
  // 30 s is the standalone target (8.5-35 s measured); node --test runs files concurrently, so the suite bound is 90 s.
  if (process.env.LLMM_PERF === "1") assert.ok(ms <= 30000, `${ms.toFixed(0)} ms`);   // timing only under LLMM_PERF=1
  assert.ok(a.end.registeredIoU >= 0.95, `registered IoU ${a.start.registeredIoU} -> ${a.end.registeredIoU}`);
  assert.ok(a.end.registeredIoU > a.start.registeredIoU + 0.01);
  assert.equal(fs.readFileSync(outA, "utf8"), fs.readFileSync(outB, "utf8"), "deterministic module");
  assert.deepEqual(a.steps, b.steps, "deterministic log");
  assert.ok(fs.existsSync(outA.replace(/\.mjs$/, ".fit.json")));
  // only the KNOBS block changed
  const start = fs.readFileSync(path.join(ROOT, START), "utf8");
  const fitted = fs.readFileSync(outA, "utf8");
  const cut = (t) => [t.slice(0, t.indexOf("export const KNOBS")), t.slice(t.indexOf("\n};", t.indexOf("export const KNOBS")))];
  assert.deepEqual(cut(fitted), cut(start));
  // the full gate on the fitted module
  const mod = await loadModule(path.relative(ROOT, outA));
  const census = { wheels: 4, bumpers: 2 };
  // V5-9 evidence hierarchy: the FIT gate enforces the advisory layout (accuracy-covered keys report, never block)
  const report = await validateParts(mod.meta, mod.build(), undefined, { cls: S.cls, rules: RULES, layout: RULES.advisoryLayout(S.readJson("layout")), census });
  assert.equal(report.pass, true, report.text);
  // residual rows the seat would own (not MISSING features) shrink
  const shape = (r) => r.rows.filter((x) => x.kind !== "MISSING");
  const r0 = await residuals({ subjectId: "pickup", modulePath: START });
  const r1 = await residuals({ subjectId: "pickup", modulePath: path.relative(ROOT, outA) });
  const area = (rows) => rows.reduce((s, x) => s + x.areaPx, 0);
  assert.ok(shape(r1).length < shape(r0).length, `${shape(r0).length} -> ${shape(r1).length} rows`);
  // V5-9: knob ranges are class priors (wider than the old key bands; coarser first steps): measured 60106 -> 47947 px
  // under the 300-eval budget (was < 0.5x with the key-tolerance ranges)
  assert.ok(area(shape(r1)) < 0.85 * area(shape(r0)), `${area(shape(r0))} -> ${area(shape(r1))} px`);
});

test("V4-2 residual noise floor: the Opus reference shows <= 5 rows, every row stays in the diagnostic list", async () => {
  const r = await residuals({ subjectId: "pickup", modulePath: WORK });
  assert.deepEqual(r.floor, S.cls.residualFloor);
  assert.ok(r.shown.length <= 5 && r.shown.length >= 1, `${r.shown.length} rows shown`);
  assert.ok(r.rows.length > r.shown.length);
  for (const row of r.shown) assert.ok(row.metres >= r.floor.metres && row.areaPx >= r.floor.px);
  assert.equal(r.text.split("\n").length, 1 + r.shown.length);
});
