// WORKFLOW v4 — V4-7: the UNSEEN-subject generality test (refs/school_bus.png), set up with the workflow's own steps.
// Hermetic: reads refs/, subjects/school_bus/ and classes/; writes only under test/.tmp-*.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import * as rules from "../src/validate/rules/vehicle.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
// two levels under ROOT, like subjects/<id>/, so the generated relative kernel import resolves
const TMP = path.join(ROOT, "test", `.tmp-v47-${process.pid}`);
const S = loadSubject("school_bus");
const LAYOUT = S.readJson("layout");
const CENSUS = Object.fromEntries(Object.entries(S.readJson("census")).filter(([k]) => !k.startsWith("_")));
const run = (args) => spawnSync(process.execPath, args, { cwd: ROOT, encoding: "utf8" });

await K.init();
if (K.assemble?.ready) await K.assemble.ready;
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `m${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return import(pathToFileURL(file).href);
}
const records = (parts) => parts.map((p) => ({ id: p.id, role: p.role, zone: p.zone, part: p, aabb: p.solid.aabb() }));
const unionBox = (ms) => ({ min: [0, 1, 2].map((a) => Math.min(...ms.map((m) => m.aabb.min[a]))), max: [0, 1, 2].map((a) => Math.max(...ms.map((m) => m.aabb.max[a]))) });
async function gate(meta, parts, census) {
  K.configure(gateConfig(S.cls));
  try { return await validateParts(meta, parts, undefined, { cls: S.cls, rules, layout: LAYOUT, census }); } finally { K.configure(null); }
}

test("V4-7 camera: --x-edge left reproduces refs/school_bus.camera.json (residual < 1 px, verticals < 1.5 deg)", () => {
  const cam = JSON.parse(fs.readFileSync(path.join(ROOT, S.rel.camera), "utf8"));
  const r = run(["scripts/solve-camera.mjs", "school_bus", "--image", S.rel.target, "--x-edge", "left", "--dry"]);
  assert.equal(r.status, 0, r.stderr);
  const out = JSON.parse(r.stdout.slice(r.stdout.lastIndexOf("\n{") + 1));
  assert.equal(out.theta_deg, cam.theta_deg);
  assert.equal(out.phi_deg, cam.phi_deg);
  assert.equal(cam.xEdge, "left");
  assert.ok(cam.residual_px < 1 && Math.abs(cam.vertical_tilt_deg) < 1.5, JSON.stringify(cam));
});

test("V4-7 measure: the bus layout and _profile are what the instruments measure (--check), every key measured or UNVERIFIED with a reason", () => {
  for (const script of ["scripts/measure-vehicle.mjs", "scripts/measure-profile.mjs"]) {
    const r = run([script, "--subject", "school_bus", "--check"]);
    assert.equal(r.status, 0, r.stdout + r.stderr);
    assert.match(r.stdout, /CHECK PASS/);
  }
  for (const [k, e] of Object.entries(LAYOUT)) {
    if (k.startsWith("_")) continue;
    assert.ok(e.unverified ? typeof e.reason === "string" && e.reason.length > 10 : typeof e.evidence?.scan === "string", k);
  }
  for (const k of ["window.row.count", "window.front.panes", "window.band.bottom", "stopArm.centreAt", "mirror.head.w", "headlight.diameter", "bumper.front.top", "bumper.rear.h"]) {
    assert.ok(LAYOUT[k] && !LAYOUT[k].unverified, `${k} measured`);
  }
  assert.equal(LAYOUT["window.front.panes"].value, 2);
  assert.equal(CENSUS.windows, LAYOUT["window.front.panes"].value + 2 * LAYOUT["window.row.count"].value);
});

test("V4-7 pickup unchanged: its template bytes and its frozen measurements", () => {
  const sha = createHash("sha256").update(generateForSubject("pickup").text).digest("hex");
  assert.equal(sha, "da7b65596be93da3a30246ce137bddaa7b3c543458d166a2a47de29d95b786ec");   // V5-9: keyed knobs ranged by the class prior (evidence hierarchy)
  const r = run(["scripts/measure-profile.mjs", "--subject", "pickup", "--check"]);
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.equal(loadSubject("pickup").cls.paletteZones.find((z) => z.key === "bed")?.region, "bed_inside", "no variant = the class prior as is");
});

test("V4-7 template: the bus body is deterministic, carries KNOBS and passes the full gate (census staged to the roles built)", async () => {
  const a = generateForSubject("school_bus");
  assert.equal(generateForSubject("school_bus").text, a.text);
  const mod = await importText(a.text);
  const names = Object.keys(mod.KNOBS);
  assert.ok(names.length >= 30, `${names.length} knobs`);
  assert.deepEqual(names.filter((n) => mod.KNOBS[n].locked), ["L", "clearance"]);
  const parts = mod.build();
  assert.ok(!parts.some((p) => ["hood", "bed", "bed_wall", "tailgate"].includes(p.role)), "no hood, no bed");
  assert.equal(parts.filter((p) => p.role === "cab").length, 1);
  const roles = new Set(parts.map((p) => p.role));
  const census = Object.fromEntries(Object.entries(CENSUS).filter(([k]) => roles.has(S.cls.censusRules[k].role)));
  const report = await gate(mod.meta, parts, census);
  assert.equal(report.pass, true, report.text);
});

test("V4-7 READY calls: every bus detail builds on the template body and the whole module passes the gate with the FULL census", async () => {
  const text = generateForSubject("school_bus").text;
  const mod0 = await importText(text);
  const F = rules.layoutFrame({ records: records(mod0.build()), cls: S.cls, geo: { unionBox } });
  const calls = rules.readyCalls(LAYOUT, F, { minFeat: 0.04 });
  assert.deepEqual(calls.map((c) => c.what.split(" ")[0]), ["windshield", "window", "door", "headlights", "turn", "markers", "mirrors", "stop"]);   // V5-3: + door, markers
  const body = calls.map((c) => c.call.split("\n").map((l) => `  ${l}`).join("\n")).join("\n");
  const mod = await importText(text.replace(/\n {2}return parts;/, `\n  const cab = parts.find((p) => p.id === "cab");\n${body}\n  return parts;`));
  const parts = mod.build();
  const report = await gate(mod.meta, parts, CENSUS);
  assert.equal(report.pass, true, report.text);
});
