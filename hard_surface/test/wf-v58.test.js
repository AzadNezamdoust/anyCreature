// V5-8 — facade camera re-solve (R1), per-subject measured rule overrides (R2), awning / sign family split (R3).
// Hermetic: the frozen target, the subject files and the kernel.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, applyRuleOverrides, gateConfig, DEFAULT_LIMITS } from "../src/validate/kernel-chain.mjs";
import * as BUILDING_RULES from "../src/validate/rules/building.mjs";
import BUILDING from "../classes/building.json" with { type: "json" };
import { loadSubject } from "../scripts/subject.mjs";
import { faceCamera, measureTarget, checkLayout } from "../scripts/measure-target.mjs";
import { subjectCameraPath } from "../scripts/solve-camera.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
await K.init();
await K.assemble.ready;

test("R1: the facade camera lives in the subject (refs/** read-only) and every loader reads paths.camera", () => {
  const S = loadSubject("facade_brick");
  assert.equal(S.rel.camera, "subjects/facade_brick/camera.json");
  assert.equal(subjectCameraPath("facade_brick"), S.paths.camera);
  const cam = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
  const old = JSON.parse(fs.readFileSync(path.join(ROOT, "refs/facade_brick.camera.json"), "utf8"));
  // the render turns meta.front onto +X, whose horizontals draw at mZ: the target front is the shallow family
  assert.equal(cam.xEdge, "left");
  assert.ok(Math.abs(cam.slopes.mZ - 0.456383) < 1e-6 && Math.abs(cam.phi_deg - 46.9075) < 1e-3, JSON.stringify(cam));
  // measure-target reads it in the FACE frame, which is exactly the frame the old refs camera was solved in
  const f = faceCamera(cam);
  assert.ok(Math.abs(f.phi_deg - old.phi_deg) < 1e-3 && f.slopes.mX === old.slopes.mX && f.slopes.mZ === old.slopes.mZ);
  for (const file of ["scripts/project.mjs", "scripts/registered.mjs", "scripts/pass.mjs"]) {
    assert.match(fs.readFileSync(path.join(ROOT, file), "utf8"), /S\(?\)?\.paths\.camera/, `${file} reads paths.camera`);
  }
  assert.match(fs.readFileSync(path.join(ROOT, "src/app.js"), "utf8"), /loadCamera\(state\.subject, paths\.camera \?/);
});

test("R1: re-measured under the new camera, the frozen layout still agrees with the instrument", async () => {
  const S = loadSubject("facade_brick");
  const m = await measureTarget({ targetFile: S.paths.target, regionsFile: S.paths.regions, cameraFile: S.paths.camera });
  const bad = checkLayout(S.readJson("layout"), m.keys).filter((r) => !r.ok);
  assert.deepEqual(bad, []);
  assert.match(S.readJson("layout")._source, /subjects\/facade_brick\/camera\.json/);
});

test("R2: measured rule overrides — effective copy, advisory rows, limits.json unchanged, unknown names refused", () => {
  const S = loadSubject("facade_brick");
  const o = S.cls.ruleOverrides;
  assert.ok(o.step_rise_max.evidence && o.stairRails.evidence && o.flightTreads.evidence);
  const { limits, rows, waived } = applyRuleOverrides(DEFAULT_LIMITS, o);
  assert.deepEqual(DEFAULT_LIMITS.v7.step_rise, [0.14, 0.2]);
  assert.deepEqual(limits.v7.step_rise, [0.14, o.step_rise_max.value]);
  assert.deepEqual(waived, ["V7_STAIR_RAIL"]);
  assert.deepEqual(rows.map((r) => `${r.v} ${r.part} ${r.blocking}`), ["RULE_OVERRIDE step_rise_max false", "RULE_OVERRIDE stairRails false", "RULE_OVERRIDE flightTreads false"]);
  assert.throws(() => applyRuleOverrides(DEFAULT_LIMITS, { door_h: { value: 1, evidence: "x" } }), /unknown override/);
  assert.throws(() => applyRuleOverrides(DEFAULT_LIMITS, { stairRails: { value: false } }), /needs \{value, evidence\}/);
  // no override = the class gate, byte-identical digest
  assert.equal(gateConfig(loadSubject("pickup").cls).digest, gateConfig({ ...loadSubject("pickup").cls, ruleOverrides: undefined }).digest);
  assert.notEqual(gateConfig(S.cls).digest, gateConfig({ ...S.cls, ruleOverrides: undefined }).digest);
});

test("R2: a railless flight with 13 steep treads fails the class gate and passes under the subject's overrides", async () => {
  const S = loadSubject("facade_brick");
  const block = { id: "block", solid: K.box([8, 12, 6]).at([0, 0, 3]), zone: "brick", role: "massing" };
  const o = S.cls.ruleOverrides;
  const fe = K.assemble.fireEscape({ wall: [block], centreX: 0, span: 5, depth: 1.4, levels: [4, 7.79], idPrefix: "fe",
    stepRise: [0.14, o.step_rise_max.value], flightTreads: o.flightTreads.value, flightRails: false });
  assert.equal(fe.filter((p) => p.role === "step").length, 13);
  assert.equal(fe.filter((p) => /flight0_(rail|post)/.test(p.id)).length, 0);
  const parts = [block, ...fe];
  const meta = { class: "building", seed: 1, palette: { brick: "#a95742", iron: "#554433" } };
  const cls = { ...S.cls, ruleOverrides: undefined };
  const plain = await validateParts(meta, parts, undefined, { cls, rules: BUILDING_RULES });
  assert.ok(plain.violations.some((v) => v.v === "V7" || v.v === "V7_STAIR_RAIL"), plain.text);
  const over = await validateParts(meta, parts, undefined, { cls: S.cls, rules: BUILDING_RULES });
  assert.ok(!over.violations.some((v) => /^V7/.test(v.v)), over.text);
  assert.equal(over.advisories.filter((a) => a.v === "RULE_OVERRIDE").length, 3);
  // without the band the kernel still refuses the steep flight
  assert.throws(() => K.assemble.fireEscape({ wall: [block], centreX: 0, span: 5, depth: 1.4, levels: [4, 7.79], flightTreads: 13 }), /impossible flight rise/);
});

test("R3: awning and sign box are separate likeness / accuracy families", () => {
  const fam = BUILDING.likeness.areaFamilies;
  assert.deepEqual(fam.awning, ["awning"]);
  assert.deepEqual(fam.signbox, ["signbox"]);
  assert.equal(fam.green, undefined);
});
