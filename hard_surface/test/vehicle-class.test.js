// WORKFLOW-V3 §7 item 10 — the second CLASS (vehicle) and the `pickup` subject.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { measureVehicle, main as measureMain } from "../scripts/measure-vehicle.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const readJson = (rel) => JSON.parse(fs.readFileSync(path.join(ROOT, rel), "utf8"));
const CLS = readJson("classes/vehicle.json");
const S = loadSubject("pickup");
const REGIONS = S.readJson("regions");
const LAYOUT = S.readJson("layout");
const CENSUS = S.readJson("census");

await K.init();
// FROZEN fixture: the committed smoke module. Never the live subjects/pickup/module.mjs, which passes rewrite.
const SMOKE_REL = "test/fixtures/vehicle/smoke.mjs";
const smoke = await import("./fixtures/vehicle/smoke.mjs");

/** census.json staged the way pass.mjs stages it. */
const staged = (pass) => Object.fromEntries(Object.entries(CENSUS)
  .filter(([k]) => !k.startsWith("_") && (CENSUS._pass?.[k] ?? 0) <= pass));
const gate = (parts, pass = 0) => validateParts(smoke.meta, parts, undefined, { census: staged(pass), layout: LAYOUT, cls: CLS, rules: RULES });
const firstCode = (report) => report.violations[0]?.v ?? null;
const swap = (parts, id, fn) => parts.map((p) => (p.id === id ? { ...p, solid: fn(p.solid) } : p));

test("vehicle prior is closed: every role has one distinct id colour, every table names real roles", () => {
  const roles = new Set(CLS.roles);
  assert.equal(CLS.class, "vehicle");
  assert.deepEqual(Object.keys(CLS.roleIdColours).sort(), [...roles].sort());
  assert.equal(new Set(Object.values(CLS.roleIdColours)).size, roles.size);
  for (const role of [...CLS.groundRoles, ...CLS.lengthRoles, ...CLS.wheelRoles, ...CLS.bearingRoles]) assert.ok(roles.has(role), role);
  for (const rule of Object.values(CLS.censusRules)) assert.ok(roles.has(rule.role), rule.role);
  const lk = CLS.likeness;
  assert.ok(roles.has(lk.faceRole));
  for (const role of [...lk.censusRoles, ...lk.faceRoles, ...Object.keys(lk.visibleInstances)]) assert.ok(roles.has(role), role);
  for (const [role, key] of Object.entries(lk.censusInstances)) {
    assert.ok(lk.censusRoles.includes(role), role);
    assert.ok(Number.isFinite(CENSUS[key]), `census.json has ${key}`);
  }
  assert.equal(CLS.triBudget, 4000);
  assert.equal(CLS.styleFloorKey, "vehicle");
  for (const rel of [CLS.rules, CLS.authorRules, CLS.measure]) assert.ok(fs.existsSync(path.join(ROOT, rel)), rel);
  assert.ok(fs.readFileSync(path.join(ROOT, CLS.authorRules), "utf8").trimEnd().split("\n").length <= 60, "vehicle.md <= 60 lines");
});

test("likeness families cover every regions.json zone exactly once, zones name real roles, palette zones resolve", () => {
  const families = Object.values(CLS.likeness.areaFamilies).flat();
  const covered = [...families, ...CLS.likeness.droppedAreaZones];
  for (const [name, zone] of Object.entries(REGIONS.zones)) {
    assert.equal(covered.filter((z) => z === name).length, 1, `zone ${name} in exactly one family`);
    assert.ok(CLS.roles.includes(zone.role), `zone ${name} role ${zone.role}`);
    assert.ok(zone.rects.reduce((s, [, , w, h]) => s + w * h, 0) >= 25, `zone ${name} >= 25 px`);
  }
  for (const z of families) assert.ok(REGIONS.zones[z], `family zone ${z} exists`);
  for (const z of Object.values(CLS.likeness.faceZones)) assert.ok(REGIONS.zones[z], `face zone ${z}`);
  for (const z of CLS.paletteZones) assert.ok(REGIONS.zones[z.region], `palette zone ${z.key} -> ${z.region}`);
  assert.equal(S.klass, "vehicle");
});

test("palette closure: every regions zone named by a module palette key or a likeness family has a paletteZones entry", () => {
  // Module palette keys from modules no live pass rewrites: the frozen smoke and the deterministic template.
  const templateKeys = [...generateForSubject("pickup").text.match(/palette: \{([\s\S]*?)\}/)[1].matchAll(/^\s*(\w+):/gm)].map((m) => m[1]);
  const moduleKeys = new Set([...Object.keys(smoke.meta.palette), ...templateKeys]);
  const families = new Set(Object.values(CLS.likeness.areaFamilies).flat());
  const mapped = new Set(CLS.paletteZones.map((z) => z.region));
  const due = Object.keys(REGIONS.zones).filter((zone) => moduleKeys.has(zone) || families.has(zone));
  assert.ok(due.includes("tread") && due.includes("body_front"), due.join(", "));
  for (const zone of due) assert.ok(mapped.has(zone), `regions zone ${zone} has no paletteZones entry in classes/vehicle.json`);
});

test("the smoke module passes check-module and validateParts with the vehicle prior (P0 census + frozen layout)", async () => {
  const check = spawnSync(process.execPath, [path.join(ROOT, "scripts/check-module.mjs"), SMOKE_REL], { cwd: ROOT, encoding: "utf8" });
  assert.equal(check.status, 0, check.stdout);
  const report = await gate(smoke.build());
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.layout, "applied");
  assert.equal(report.measurements.census, "applied");
});

test("VEH_GROUND fails a floating wheel", async () => {
  const report = await gate(swap(smoke.build(), "wheel_fl", (s) => s.at([0, 0.03, 0])));
  assert.equal(firstCode(report), "VEH_GROUND", report.text);
  assert.match(report.violations[0].hint, /floats/);
});

test("VEH_GROUND fails a chassis standing on the ground", async () => {
  const parts = smoke.build().map((p) => {
    if (p.id !== "chassis") return p;
    const box = p.solid.aabb();
    const size = [0, 1, 2].map((a) => box.max[a] - box.min[a]);
    return { ...p, solid: K.box([size[0], box.max[1], size[2]]).at([(box.min[0] + box.max[0]) / 2, 0, (box.min[2] + box.max[2]) / 2]) };
  });
  const report = await gate(parts);
  assert.equal(firstCode(report), "VEH_GROUND", report.text);
  assert.equal(report.violations[0].part, "chassis");
});

/** Two mirrors on the cab sides at the measured height; `shiftZ` moves the -X one. */
function withMirrors(shiftZ) {
  const parts = smoke.build();
  const cab = parts.find((p) => p.id === "cab").solid.aabb();
  const H = Math.max(...parts.map((p) => p.solid.aabb().max[1]));
  const y = LAYOUT["mirror.centreY"].value * H - 0.125;
  const z = cab.max[2] - 0.2;
  const head = K.box([0.1, 0.25, 0.06]);
  // seated 1 mm into the cab side, so the union is one lump
  parts.push({ id: "mirror_l", solid: head.at([cab.max[0] + 0.049, y, z]), zone: "mirror", role: "mirror" });
  parts.push({ id: "mirror_r", solid: head.at([cab.min[0] - 0.049, y, z + shiftZ]), zone: "mirror", role: "mirror" });
  return parts;
}

test("VEH_MIRROR passes a mirrored pair and fails an unmirrored mirror", async () => {
  const good = await gate(withMirrors(0));
  assert.ok(!good.violations.some((v) => v.v === "VEH_MIRROR"), good.text);
  const bad = await gate(withMirrors(-0.3));                 // still on the cab side, 0.3 m behind its partner
  assert.equal(firstCode(bad), "VEH_MIRROR", bad.text);
});

/**
 * A single "mirror"-role part (motorbike-like: one centred detail, no mirrored partner), bbox centre at `xOffset`.
 * VEH_MIRROR already auto-passes a lone part within MIRROR_TOL/2 (0.01 m) of the centreline (it "mirrors itself");
 * ruleOverrides.mirror widens that to the full MIRROR_TOL (0.02 m) for parts it names, pairing waived. Seated 1 mm
 * into the hood's nose (z = hood.max[2]), the way withMirrors seats a side mirror 1 mm into the cab.
 */
function withSingleMirror(xOffset) {
  const parts = smoke.build();
  const hood = parts.find((p) => p.id === "hood").solid.aabb();
  const head = K.box([0.1, 0.08, 0.06]);
  parts.push({ id: "mirror_c", solid: head.at([xOffset, hood.min[1], hood.max[2] + 0.029]), zone: "mirror", role: "mirror" });
  return parts;
}

// V12_LAYOUT measures pickup's own mirror.* / headlight.* / wheel.* layout keys (two mirrors, specific offsets) —
// irrelevant to this synthetic single-part fixture, so it's skipped; VEH_MIRROR is what this test is about.
const gateOverride = (parts, ruleOverrides) =>
  validateParts(smoke.meta, parts, undefined, { census: staged(0), layout: LAYOUT, cls: CLS, rules: RULES, ruleOverrides, skip: ["V12_LAYOUT"] });

test("ruleOverrides.mirror exempts a single-track centred part from VEH_MIRROR pairing, but not from centring", async () => {
  // 0.015 m off centre: outside the trivial self-mirror pass (MIRROR_TOL/2 = 0.01 m) but inside the override's
  // full MIRROR_TOL (0.02 m) — without the override a lone, unpaired "mirror" there fails VEH_MIRROR.
  const bare = await gateOverride(withSingleMirror(0.015));
  assert.equal(firstCode(bare), "VEH_MIRROR", bare.text);

  const overrides = { mirror: { value: { centred: ["mirror"] }, evidence: "test: single centred part, motorbike-like" } };

  // With the override, that same near-centred single part passes.
  const good = await gateOverride(withSingleMirror(0.015), overrides);
  assert.ok(!good.violations.some((v) => v.v === "VEH_MIRROR"), good.text);
  assert.ok(good.advisories.some((a) => a.v === "RULE_OVERRIDE" && a.part === "mirror"), good.text);

  // An exempt-but-off-centre part (0.03 m, past the full tolerance) still fails VEH_MIRROR — pairing is waived,
  // centring is not.
  const bad = await gateOverride(withSingleMirror(0.03), overrides);
  assert.equal(firstCode(bad), "VEH_MIRROR", bad.text);
  assert.match(bad.violations[0].hint, /centred part off the centreline/);
});

test("VEH_WHEELS fails three wheels", async () => {
  const report = await gate(smoke.build().filter((p) => p.id !== "wheel_rr"));
  assert.equal(firstCode(report), "VEH_WHEELS", report.text);
  assert.match(report.violations[0].measured, /^3 wheel/);
});

const INPUTS = {
  targetFile: path.join(ROOT, S.rel.target),
  regionsFile: path.join(ROOT, S.rel.regions),
  cameraFile: path.join(ROOT, S.rel.camera),
};

test("measure-vehicle is deterministic, and every key carries evidence or a reason", async () => {
  const a = await measureVehicle(INPUTS);
  const b = await measureVehicle(INPUTS);
  assert.deepEqual(a.keys, b.keys);
  assert.deepEqual(a.frame, b.frame);
  for (const [k, v] of Object.entries(a.keys)) {
    if (v.unverified) assert.ok(v.reason, `${k} reason`);
    else assert.ok(v.evidence?.scan && v.evidence?.px, `${k} evidence`);
  }
  assert.equal(a.frame.quadPx.length, 4);
  assert.ok(a.keys["wheel.farSide"].unverified, "the occluded wheels are unverified");
});

test("measure-vehicle --check passes after --freeze (temp files) and on the committed layout", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "llmm-veh-"));
  const layout = path.join(dir, "layout.json");
  const out = path.join(dir, "layout.measured.json");
  // child processes, so the script's stdout never mixes with the test reporter's
  const run = (...args) => spawnSync(process.execPath, [path.join(ROOT, "scripts/measure-vehicle.mjs"), "--subject", "pickup", ...args], { cwd: ROOT, encoding: "utf8" });
  try {
    const freeze = run("--freeze", "--layout", layout, "--out", out);
    assert.equal(freeze.status, 0, freeze.stderr);
    const temp = run("--check", "--layout", layout);
    assert.equal(temp.status, 0, temp.stdout.slice(-400));
    assert.match(temp.stdout, /CHECK PASS/);
    const committed = run("--check");
    assert.equal(committed.status, 0, committed.stdout.slice(-400));
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  assert.equal(typeof measureMain, "function");
});
