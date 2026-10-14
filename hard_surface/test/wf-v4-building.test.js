// WORKFLOW v4 — V4-5B: the building through v4 (research/WF-V4-PLAN.md). Hermetic: the start is the frozen KNOBS
// template output test/fixtures/v4/start-knobs-facade.mjs; refs/, subjects/ and classes/ are read only; fitted
// modules go to a temp dir.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/building.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { generateForSubject, pickFrame } from "../scripts/template-building.mjs";
import { loadModule } from "../scripts/project.mjs";
import { fit } from "../scripts/fit.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const START = "test/fixtures/v4/start-knobs-facade.mjs";
// three levels under ROOT, like the fixture, so the module's relative kernel import resolves unchanged
const TMP = path.join(ROOT, "test", `.tmp-wf-v4-building-${process.pid}`, "fit");
test.after(() => fs.rmSync(path.dirname(TMP), { recursive: true, force: true }));
const S = loadSubject("facade_brick");
const census = Object.fromEntries(Object.entries(S.readJson("census")).filter(([k]) => !k.startsWith("_")));

async function gate(file) {
  await K.init();
  await K.assemble.ready;
  K.configure(gateConfig(S.cls));
  const mod = await loadModule(file);
  const parts = mod.build();
  const report = await validateParts(mod.meta, parts, undefined, { cls: S.cls, rules: RULES, layout: S.readJson("layout"), census });
  return { mod, parts, report };
}

test("V4-5B template: the whole building as KNOBS (W/H/D start at pickFrame, fitted since V5-1), full gate PASS incl. V11, ironwork by K.assemble", async () => {
  const text = generateForSubject("facade_brick", { knobs: true }).text;
  assert.equal(text, generateForSubject("facade_brick", { knobs: true }).text, "deterministic");
  const fx = fs.readFileSync(path.join(ROOT, START), "utf8");
  assert.equal(fx.slice(fx.indexOf("export const KNOBS")), text.slice(text.indexOf("export const KNOBS")), "the fixture is the template's current output");
  const { mod, parts, report } = await gate(START);
  const knobs = Object.entries(mod.KNOBS);
  assert.equal(knobs.length, 55);   // V5-7: + feBaluster, ladderRung (measured member pitches)
  assert.deepEqual(knobs.filter(([, k]) => k.locked).map(([n]) => n), [], "V5-1 item 2: W / H / D are free (aspect fitted)");
  for (const n of ["W", "H", "D"]) assert.ok(mod.KNOBS[n].max > mod.KNOBS[n].min, `${n} has a range`);
  const { W, H } = pickFrame(S.readJson("layout"), S.readJson("census"));
  assert.equal(mod.KNOBS.W.v, W);
  assert.equal(mod.KNOBS.H.v, H);
  const layout = S.readJson("layout");
  for (const [n, k] of knobs) {
    assert.ok(k.min <= k.v && k.v <= k.max, `${n} ${k.min} <= ${k.v} <= ${k.max}`);
    if (k.key) assert.ok(layout[k.key] && !layout[k.key].unverified, `${n}: verified key ${k.key}`);
  }
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.layout, "applied");
  assert.equal(report.measurements.census, "applied");
  assert.ok(!/V11_/.test(report.text), `no V11 row or advisory:\n${report.text}`);
  for (const role of ["landing", "stringer", "ladder"]) {
    const ps = parts.filter((p) => p.role === role);
    assert.ok(ps.length > 0 && ps.every((p) => p.assembly), `${role} built by K.assemble`);
  }
});

test("V4-5B FIT: the building fit raises the objective, keeps the gate (V11 included) and only rewrites KNOBS values", async () => {
  const out = path.join(TMP, "fitted.mjs");
  const r = await fit({ subjectId: "facade_brick", modulePath: START, out, evals: 40 });
  assert.ok(r.end.score > r.start.score, `score ${r.start.score} -> ${r.end.score}`);
  // the zone term carries the gain: refs/tenement-iso.png holds THREE buildings, so the whole-image silhouette IoU of
  // the middle one is capped near 0.4 and FIT keeps it level (300 evals: 0.4021 -> 0.4026)
  // V5-8 R1: under the re-solved camera the start registers closer (40 evals: 0.506 -> 0.5235), so the bar is +0.01
  assert.ok(r.end.zone > r.start.zone + 0.01, `zone IoU ${r.start.zone} -> ${r.end.zone}`);
  assert.ok(r.end.registeredIoU >= r.start.registeredIoU - 0.002, `IoU ${r.start.registeredIoU} -> ${r.end.registeredIoU}`);
  assert.ok(Object.keys(r.knobs).length > 0);
  const a = fs.readFileSync(path.join(ROOT, START), "utf8");
  const b = fs.readFileSync(out, "utf8");
  const strip = (t) => t.replace(/(\n\s*\w+:\s*\{\s*v:\s*)-?[\d.]+/g, "$1#");
  assert.equal(strip(b), strip(a), "only KNOBS v: numbers change");
  const { report } = await gate(out);
  assert.equal(report.pass, true, report.text);
  assert.ok(!/V11_/.test(report.text), report.text);
});
