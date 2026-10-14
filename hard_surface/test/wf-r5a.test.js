// WF-R5 R5-A (research/WF-R5-FIDELITY.md items 1 + 3) — the profile body, the inlay helpers (seam, handle, angled pane,
// two-tone grille), the no-skin recess, part/assembly window grouping, and the ready calls that print them. Hermetic: the
// target is refs/pickup_truck.png (frozen), the start is the frozen copy test/fixtures/vehicle/start-r5a.mjs.
process.env.LLMM_SUBJECT = "pickup";
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, chainContext } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { ROOT, moduleFrame } from "../scripts/pass.mjs";
import { measureProfile, archRise } from "../scripts/measure-profile.mjs";
import { brickFaces } from "../scripts/likeness.mjs";

await K.init();
await K.assemble.ready;

const PICKUP = loadSubject("pickup");
const LAYOUT = PICKUP.readJson("layout");
const P1 = PICKUP.readJson("passes").find((p) => p.id === "P1");
const START = fs.readFileSync(path.join(ROOT, "test", "fixtures", "vehicle", "start-r5a.mjs"), "utf8");
const TMP = path.join(ROOT, "test", `.tmp-wf-r5a-${process.pid}`);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));
let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return import(pathToFileURL(file).href);
}
const META = { front: "+X", class: "vehicle", seed: 1, palette: { body: "#808080", bed: "#808080", glass: "#808080", lamp: "#808080", grille: "#808080", mirror: "#808080", bumper: "#808080", tyre: "#808080" } };
const gate = (parts, census = false) => validateParts(META, parts, undefined, { cls: PICKUP.cls, rules: RULES, census, layout: false });

test("profile round-trip: measure-profile reproduces the frozen _profile, and the start's sill + arches trace the measured lower edge", async () => {
  const S = PICKUP;
  const fresh = await measureProfile({ targetFile: S.paths.target, regionsFile: S.paths.regions, cameraFile: S.paths.camera, cls: S.cls });
  assert.deepEqual(fresh, LAYOUT._profile, "layout.json _profile is the measurement (measure-profile --check)");
  const P = LAYOUT._profile;
  for (const [k, e] of Object.entries(P.keys)) assert.ok(e.unverified ? e.reason : e.evidence?.scan && e.evidence?.px, `${k} carries evidence or a reason`);
  const sill = P.keys["body.sill"].value;
  // model lower edge (analytic, the same superellipses vehicleBody cuts) vs the measured lower edge, arch + sill runs
  let worst = 0;
  for (const [u, v] of P.side.bottom) {
    if (u < 0.08 || u > 0.965 || (u > 0.575 && u < 0.605)) continue;   // nose, the rear bumper block and the cab-bed slot are not flank
    const model = sill + Math.max(0, ...P.arches.map((a) => archRise(a, u)));
    worst = Math.max(worst, Math.abs(model - v));
  }
  assert.ok(worst <= 0.03, `lower edge within 0.03 H of the measurement (worst ${worst.toFixed(3)})`);
  // the built start: hood / cab rest on the sill, the arch liners carry the measured wheel-well tone
  const parts = (await importText(START)).build();
  const H = LAYOUT["height.overL"].value * 4.8;
  const cab = parts.find((p) => p.id === "cab").solid.aabb();
  assert.ok(Math.abs(cab.min[1] - sill * H) < 0.002, `cab bottom ${cab.min[1]} at the sill ${sill * H}`);
  assert.equal(parts.find((p) => p.id === "arch_fl").zone, P.inlays.archLiner.zone);
  const report = await validateParts((await importText(START)).meta, parts, undefined, { cls: S.cls, rules: RULES, layout: LAYOUT, census: { wheels: 4, bumpers: 2 } });
  assert.equal(report.pass, true, report.text);
});

test("inlay helpers on every face (seam, handle, angled pane) and the two-tone grille pass V3/V5/V6", async () => {
  const cab = { id: "cab", role: "cab", zone: "body", solid: K.box([2, 2.1, 4]) };
  const parts = [cab,
    { id: "bumper_f", role: "bumper", zone: "bumper", solid: K.box([2, 0.2, 0.081]).at([0, 0.3, 2.04]) },
    { id: "bumper_r", role: "bumper", zone: "bumper", solid: K.box([2, 0.2, 0.081]).at([0, 0.3, -2.04]) }];
  for (const face of ["+x", "-x"]) {
    parts.push(...K.assemble.pane({ host: cab, face, poly: [[-1, 1.2], [1, 1.2], [0.7, 1.9], [-1, 1.9]], idPrefix: `side${face}` }));
    parts.push(...K.assemble.seam({ host: cab, face, closed: true, path: [[-1.5, 0.4], [1.5, 0.4], [1.5, 1.1], [-1.5, 1.1]], idPrefix: `seam${face}` }));
    parts.push(...K.assemble.handle({ host: cab, face, bounds: K.span({ z: [-1.3, -1.05], y: [0.8, 0.86] }), idPrefix: `handle${face}` }));
  }
  for (const face of ["+z", "-z"]) {
    parts.push(...K.assemble.pane({ host: cab, face, poly: [[-0.8, 1.3], [0.8, 1.3], [0.6, 1.9], [-0.6, 1.9]], idPrefix: `end${face}` }));
    parts.push(...K.assemble.seam({ host: cab, face, path: [[-0.9, 1.15], [0.9, 1.15], [0.9, 1.25]], idPrefix: `line${face}` }));
  }
  parts.push(...K.assemble.seam({ host: cab, face: "+y", path: [[-0.5, -1], [0.5, 1]], idPrefix: "roofline" }));
  // a seam is an inlay PART: its box must clear the V5 floor across the face, so a lone straight 0.02 m line is refused
  assert.throws(() => K.assemble.seam({ host: cab, face: "+z", path: [[-0.9, 0.5], [0.9, 0.5]] }), /seam y extent 0.020 m is under MIN_FEAT/);
  parts.push(...K.assemble.grille({ body: parts, face: "nose", bounds: K.span({ x: [-0.3, 0.3], y: [0.7, 1.0] }), slots: 2 }));
  parts.push(...K.assemble.grille({ body: parts, face: "tail", bounds: K.span({ x: [-0.3, 0.3], y: [0.7, 1.0] }), slots: 2, idPrefix: "tail_grille" }));
  const report = await gate(parts);
  const bad = report.violations.filter((v) => /^(V3|V5|V6)/.test(v.v));
  assert.deepEqual(bad.map((v) => `${v.v} ${v.part}`), [], report.text);
  const grille = parts.filter((p) => p.assembly?.id === "grille");
  assert.deepEqual(grille.map((p) => p.zone), ["body", "grille", "grille"], "bars in the body tone, slot inlays in the grille tone");
  assert.equal(grille[0].solid.cutTools().reduce((n, t) => n + t.lumps, 0), 2, "grille.slots still counts the slots");
  for (const p of parts.filter((q) => q.assembly?.helper === "seam" || q.assembly?.helper === "handle")) {
    assert.equal(p.zone, "bed", `${p.id} in the darker body-family tone`);
    assert.equal(p.solid.decompose().length, 1, p.id);
  }
});

test("no-skin cut: a pane / seam recess leaves no host material over the inlay (the tool starts outside the face)", async () => {
  const cab = { id: "cab", role: "cab", zone: "body", solid: K.box([2, 2, 4]) };
  K.assemble.pane({ host: cab, face: "+x", bounds: K.span({ z: [-1, 1], y: [1, 1.8] }) });
  K.assemble.seam({ host: cab, face: "-x", closed: true, path: [[-1.5, 0.3], [1.5, 0.3], [1.5, 0.8], [-1.5, 0.8]] });
  // host material between the recess floor and the face, inside the footprints: none
  const paneBand = K.intersect(cab.solid, K.box([0.012, 0.7, 1.9]).at([1 - 0.007, 1.05, 0]));
  assert.ok(paneBand.volume() < 1e-9, `pane recess skin ${paneBand.volume()}`);
  const seamBand = K.intersect(cab.solid, K.box([0.018, 0.01, 2.9]).at([-1 + 0.01, 0.295, 0]));
  assert.ok(seamBand.volume() < 1e-9, `seam groove skin ${seamBand.volume()}`);
  assert.ok(K.assemble.RECESS_OUTSIDE > 0);
});

test("windows group by part / assembly: a tapered side pane overlapping the windshield's box is its own window", async () => {
  const cab = { id: "cab", role: "cab", zone: "body", solid: K.box([2, 2.1, 4]) };
  const parts = [cab];
  parts.push(...K.assemble.pane({ host: cab, face: "+z", poly: [[-0.999, 1.2], [0.999, 1.2], [0.9, 2], [-0.9, 2]], idPrefix: "windshield" }));
  for (const face of ["+x", "-x"]) parts.push(...K.assemble.pane({ host: cab, face, poly: [[-1, 1.2], [2, 1.2], [2, 2], [-1, 2]], idPrefix: `side${face}` }));
  const ctx = chainContext(META, parts, undefined, { cls: PICKUP.cls, rules: RULES });
  const win = ctx.records.filter((r) => r.role === "window");
  assert.equal(ctx.geo.groupAssemblies(win, [0, 1, 2]).length, 1, "the old box grouping merges all three");
  assert.equal(RULES.windowGroups(ctx, win).length, 3);
  const report = await gate(parts, { windows: 3 });
  assert.ok(!report.violations.some((v) => v.v === "V12_CENSUS"), report.text);
  // hand-built: two glass parts are two windows even when their boxes touch
  const hand = [cab, { id: "g1", role: "window", zone: "glass", solid: K.box([1, 0.5, 0.05]).at([0, 1.2, 2]) },
    { id: "g2", role: "window", zone: "glass", solid: K.box([0.05, 0.5, 1]).at([0.99, 1.2, 1.5]) }];
  const hctx = chainContext(META, hand, undefined, { cls: PICKUP.cls, rules: RULES });
  assert.equal(RULES.windowGroups(hctx, hctx.records.filter((r) => r.role === "window")).length, 2);
});

test("READY CALLS print the new helpers with metre arguments, and the pasted start passes the chain", async () => {
  const start = await importText(START);
  const frame = await moduleFrame(start.build(), PICKUP);
  const calls = RULES.readyCalls(LAYOUT, frame.F, { cited: P1.requiredLayoutKeys, minFeat: 0.04 });
  const text = calls.map((c) => c.call).join("\n");
  for (const h of ["pane", "seam", "handle", "lamp", "grille", "mirror"]) assert.match(text, new RegExp(`K\\.assemble\\.${h}\\(\\{`), h);
  assert.match(text, /face: "\+z", poly: \[\[/, "tapered windshield");
  assert.match(text, /K\.assemble\.pane\(\{ host: cab, face, poly: \[\[/, "raked side glass");
  assert.doesNotMatch(text, /fromNose|\* H|\* L/, "metres only");
  const mod = await importText(START.replace("  return parts;\n}", `  ${calls.map((c) => c.call).join("\n  ")}\n  return parts;\n}`));
  const parts = mod.build();
  const report = await validateParts(mod.meta, parts, undefined, { cls: PICKUP.cls, rules: RULES, layout: LAYOUT, census: { wheels: 4, bumpers: 2, headlights: 2, mirrors: 2, windows: 3 } });
  assert.equal(report.pass, true, report.text);
  assert.ok(parts.reduce((n, p) => n + p.solid.triCount(), 0) <= 4000, "inside the vehicle triangle budget");
  assert.ok(!report.advisories.some((a) => a.v === "VEH_HANDBUILT"));
});

test("LK_VALUE faces: a darker inlay tone under the face share is not the return face (flat unlit capture)", () => {
  const w = 20, h = 20;
  const still = { w, h, c: 3, data: Buffer.alloc(w * h * 3) };
  const mask = { label: new Uint8Array(w * h).fill(1) };
  for (let i = 0; i < w * h; i += 1) {
    const inlay = i < 12;                                  // 3 % of the cab px: a handle
    still.data.set(inlay ? [0x6d, 0x96, 0xb2] : [0x8a, 0xb8, 0xd9], i * 3);
  }
  assert.deepEqual(brickFaces(still, mask, 1).side, [0x6d, 0x96, 0xb2], "without a share floor the handle reads as the side face");
  assert.equal(brickFaces(still, mask, 1, PICKUP.cls.likeness.faceMinShare).side, null, "with the class floor there is one face tone");
});
