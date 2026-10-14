// WORKFLOW v5 — V5-3: vehicle helpers + READY calls (research/WF-V5-ACCURACY.md). Every new helper builds on the
// template body, the full READY set passes the full chain within triBudget (also with the V5-2 rounding opened), the
// READY calls cover every measured inventory feature, templates regenerate deterministically. Hermetic: reads refs/,
// subjects/ and classes/; writes only under test/.tmp-*.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import * as rules from "../src/validate/rules/vehicle.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";
import { replaceKnobValues } from "../scripts/knobs.mjs";
import { loadSubject } from "../scripts/subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TMP = path.join(ROOT, "test", `.tmp-v53-${process.pid}`);
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

async function withReady(subjectId, knobs = null) {
  const S = loadSubject(subjectId);
  const layout = S.readJson("layout");
  let text = generateForSubject(subjectId).text;
  if (knobs) text = replaceKnobValues(text, knobs);
  const F = rules.layoutFrame({ records: records((await importText(text)).build()), cls: S.cls, geo: { unionBox } });
  const calls = rules.readyCalls(layout, F, { minFeat: 0.04 });
  const body = calls.map((c) => c.call.split("\n").map((l) => `  ${l}`).join("\n")).join("\n");
  const mod = await importText(text.replace(/\n {2}return parts;/, `\n  const cab = parts.find((p) => p.id === "cab");\n${body}\n  return parts;`));
  const parts = mod.build();
  const census = Object.fromEntries(Object.entries(S.readJson("census")).filter(([k]) => !k.startsWith("_")));
  K.configure(gateConfig(S.cls));
  let report;
  try { report = await validateParts(mod.meta, parts, undefined, { cls: S.cls, rules, layout, census }); } finally { K.configure(null); }
  return { S, layout, calls, mod, parts, report, tris: parts.reduce((s, p) => s + p.solid.triCount(), 0) };
}

test("V5-3 bus: every detail helper (framed windshield, door, lamps (V5-6: no ring, the target draws an ink outline), rounded turn lenses, cap markers, bracket mirrors, stop rim + post) passes the full chain within triBudget", async () => {
  for (const knobs of [null, { roofR: 0.35, capR: 0.8, cornerR: 0.35 }]) {
    const { S, calls, parts, report, tris } = await withReady("school_bus", knobs);
    assert.equal(report.pass, true, report.text);
    assert.ok(tris <= S.cls.triBudget, `${tris} tris (knobs ${JSON.stringify(knobs)})`);
    assert.deepEqual(calls.map((c) => c.what.split(" ")[0]), ["windshield", "window", "door", "headlights", "turn", "markers", "mirrors", "stop"]);
    for (const id of ["windshield_frame", "windshield_l", "windshield_r", "door_leaf", "door_pane", "lamp_l", "turn_l", "marker_housing_l", "marker_l0", "marker_l1", "marker_r0",
      "mirror_arm_l0", "mirror_arm_l1", "stopArm_border", "stopArm_post"]) assert.ok(parts.some((p) => p.id === id), id);
    assert.equal(parts.find((p) => p.id === "marker_l0").zone, "signal");
    assert.equal(parts.find((p) => p.id === "marker_l1").zone, "orange");
    // the markers sit on the front cap, above the nose's flat face and behind the nose plane's top
    const cab = parts.find((p) => p.id === "cab").solid.aabb();
    const mk = parts.find((p) => p.id === "marker_l0").solid.aabb();
    assert.ok(mk.min[1] > 0.8 * cab.max[1] && mk.max[2] <= cab.max[2] + 0.1, JSON.stringify(mk));
  }
});

test("V5-3 pickup: windshield frame, hood crease, measured mirror z on a raked arm and the measured grille slat pass the full chain within triBudget", async () => {
  const { S, layout, calls, parts, report, tris } = await withReady("pickup");
  assert.equal(report.pass, true, report.text);
  assert.ok(tris <= S.cls.triBudget, `${tris} tris`);
  const call = (re) => calls.find((c) => re.test(c.what))?.call ?? "";
  assert.doesNotMatch(call(/^windshield/), /frame:/);   // V5-6: window.front.frame UNVERIFIED (ink outline, no frame tone)
  assert.match(call(/^mirrors/), /armFrom: \[[\d.-]+, [\d.-]+\]/);
  assert.match(call(/^grille/), /bar: [\d.]+/);
  assert.match(call(/^hood crease/), /crease: true, panel: false/);
  assert.match(call(/^door seams/), /K\.assemble\.seam/);
  for (const id of ["hoodCrease_crease_l", "mirror_arm_l", "door_l"]) assert.ok(parts.some((p) => p.id === id), id);
  // the mirror head at the measured z (mirror.at), not one head depth behind the side window
  const F = rules.layoutFrame({ records: records(parts), cls: S.cls, geo: { unionBox } });
  const head = parts.find((p) => p.id === "mirror_head_l").solid.aabb();
  assert.ok(Math.abs((head.min[2] + head.max[2]) / 2 - (F.zFront - layout["mirror.at"].value * F.L)) < 0.02);
});

test("V5-3 measurements: every bus / pickup detail key the READY calls read is measured with evidence; templates regenerate deterministically", () => {
  const bus = loadSubject("school_bus").readJson("layout")._profile.keys;
  for (const k of ["windshield.frame.top", "windshield.frame.bottom", "windshield.frame.side", "band.end", "door.pane.start", "door.pane.top", "turn.w", "turn.h",
    "stopArm.border", "stopArm.post.bottom", "stopArm.post.top", "bumper.front.wrap", "roof.upTint", "marker.housing.pad"]) {
    assert.ok(bus[k] && !bus[k].unverified && typeof bus[k].evidence?.scan === "string", k);
  }
  const pk = loadSubject("pickup").readJson("layout");
  for (const k of ["grille.slotH", "mirror.at"]) assert.ok(pk[k] && typeof pk[k].evidence?.scan === "string", k);
  // V5-6: features the target does NOT have are UNVERIFIED with a reason (the bus lamp ring, the pickup windshield frame)
  assert.match(bus["headlight.ring"].reason ?? "", /ink outline/);
  assert.match(pk._profile.keys["window.front.frame"].reason ?? "", /outline of the glass/);
  assert.ok(bus["bumper.rear.wrap"]?.evidence, "bumper.rear.wrap");
  for (const s of ["pickup", "school_bus"]) assert.equal(generateForSubject(s).text, generateForSubject(s).text);
  // colour: one body tone unless a split is measured (the bus roof is; the pickup has no roof split)
  assert.match(generateForSubject("school_bus").text, /upTint: 0\.1\d\d/);
  assert.match(generateForSubject("pickup").text, /upTint: 0,/);
});
