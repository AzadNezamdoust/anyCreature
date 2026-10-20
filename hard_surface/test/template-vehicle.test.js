// The vehicle template is deterministic, passes the vehicle gate at P0 with the
// frozen census + layout, and follows the layout it reads.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts } from "../src/validate/kernel-chain.mjs";
import * as rules from "../src/validate/rules/vehicle.mjs";
import { generateForSubject, CLASS_DEFAULTS } from "../scripts/template-vehicle.mjs";
import { passKeys } from "../scripts/template-building.mjs";
import { loadSubject } from "../scripts/subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SUBJECT = "pickup";
// Two levels under ROOT, like subjects/<id>/, so the generated relative kernel import resolves.
const TMP = path.join(ROOT, "test", `.tmp-template-vehicle-${process.pid}`);
const SCRIPT = path.join(ROOT, "scripts", "template-vehicle.mjs");

let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return { file, mod: await import(pathToFileURL(file).href) };
}

const stagedCensus = (raw, n) => Object.fromEntries(Object.entries(raw).filter(([k]) => !k.startsWith("_") && (raw._pass?.[k] ?? 0) <= n));

test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

test("generation is deterministic (in-process twice, and the CLI writes the same bytes)", () => {
  const a = generateForSubject(SUBJECT).text;
  assert.equal(generateForSubject(SUBJECT).text, a);
  fs.mkdirSync(TMP, { recursive: true });
  const out = path.join(TMP, "cli.mjs");
  const r = spawnSync(process.execPath, [SCRIPT, "--subject", SUBJECT, "--through", "P0", "--out", out], { cwd: ROOT, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
  assert.equal(fs.readFileSync(out, "utf8"), a);
  assert.ok(!/Math\.random|\bDate\b/.test(a));
});

test("the CLI refuses to overwrite the live module and refuses the details pass", () => {
  const S = loadSubject(SUBJECT);
  const live = spawnSync(process.execPath, [SCRIPT, "--subject", SUBJECT, "--out", S.paths.module], { cwd: ROOT, encoding: "utf8" });
  assert.equal(live.status, 3);
  assert.throws(() => generateForSubject(SUBJECT, { through: "P1" }), /does not build: .*window/);
});

test("P0 template passes check-module and validateParts with census staged to P0 and the layout", async () => {
  const S = loadSubject(SUBJECT);
  const gen = generateForSubject(SUBJECT);
  const { file, mod } = await importText(gen.text);
  const check = spawnSync(process.execPath, [path.join(ROOT, "scripts", "check-module.mjs"), file], { cwd: ROOT, encoding: "utf8" });
  assert.equal(check.status, 0, check.stdout);

  const layout = S.readJson("layout");
  await K.init();
  const parts = mod.build();
  const report = await validateParts(mod.meta, parts, undefined, { census: stagedCensus(S.readJson("census"), 0), layout, cls: S.cls, rules });
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.layout, "applied");
  assert.equal(report.measurements.census, "applied");

  const keys = passKeys(S.readJson("passes")[0].item);
  assert.equal(keys.length, 15, keys.join(", "));
  const roles = new Set(parts.map((p) => p.role));
  for (const k of keys) {
    assert.ok(layout[k] && !layout[k].unverified, `${k} is a verified key`);
    for (const role of rules.layoutRules[k].roles) assert.ok(roles.has(role), `${k}: role ${role} built, so V12_LAYOUT measured it`);
  }
  for (const code of ["VEH_GROUND", "VEH_WHEELS", "VEH_MIRROR", "V3", "V12_LAYOUT"]) {
    assert.ok(!report.violations.some((v) => v.v.startsWith(code)), code);
  }
  assert.ok(gen.text.includes("MVP-STUB: chassis.clearance unverified"), "chassis.clearance");
  // WF-R5 R5-A: bumper.rear.top is measured on the rear bumper face's own plane (layout _profile), no longer a stub
  assert.match(gen.text, /bumper.rear.*/);
});

test("changing wheel.diameterOverL changes the wheel radius", async () => {
  const S = loadSubject(SUBJECT);
  const base = S.readJson("layout");
  const before = generateForSubject(SUBJECT);
  const after = generateForSubject(SUBJECT, { overrides: { layout: { "wheel.diameterOverL": { ...base["wheel.diameterOverL"], value: 0.17 } } } });
  assert.notEqual(before.text, after.text);
  await K.init();
  const radius = async (text) => {
    const { mod } = await importText(text);
    const box = mod.build().find((p) => p.id === "wheel_fl").solid.aabb();
    return (box.max[1] - box.min[1]) / 2;
  };
  const L = CLASS_DEFAULTS.length;
  assert.ok(Math.abs(await radius(before.text) - (base["wheel.diameterOverL"].value * L) / 2) < 1e-6);
  assert.ok(Math.abs(await radius(after.text) - (0.17 * L) / 2) < 1e-6);
});

// WF-V3 blind Gemini pickup P1 — the target shows the far front tyre under the front
// bumper (refs/pickup_truck.png dark component x 122..237, y 691..746 px, 633 px), so
// the chassis stops at the front wheels' leading edge and the bumper seats on the hood.
test("the chassis stops short of the nose so the far front tyre can show under the bumper", async () => {
  const gen = generateForSubject(SUBJECT);
  const { mod } = await importText(gen.text);
  await K.init();
  const parts = mod.build();
  const byId = Object.fromEntries(parts.map((p) => [p.id, p]));
  const nose = byId.hood.solid.aabb().max[2];
  const chassis = byId.chassis.solid.aabb();
  const wheel = byId.wheel_fl.solid.aabb();
  assert.ok(chassis.max[2] < nose - 0.2, `chassis front ${chassis.max[2]} vs nose ${nose}`);
  assert.ok(Math.abs(chassis.max[2] - wheel.max[2]) < 1e-6, "chassis ends at the front wheel's leading edge");
  // WF-BLIND-R1 B5: contact is measured, never declared — the bumper seats on the hood by geometry alone.
  assert.equal(byId.bumper_front.touches, undefined);
  const bumper = byId.bumper_front.solid.aabb();
  assert.ok(bumper.min[2] < nose && bumper.max[1] > byId.hood.solid.aabb().min[1], "the front bumper overlaps the hood's nose face");
});
