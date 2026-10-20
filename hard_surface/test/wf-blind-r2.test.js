// WF-BLIND-R2 rows C1-C12 + C14 (examiner job 3 after the blind Gemini / Terra building P2 and pickup P1 runs):
// workflow gaps any author model hits — never tuned to one seat's output.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import * as BUILDING_RULES from "../src/validate/rules/building.mjs";
import * as VEHICLE_RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import {
  ROOT, RefusalError, gateTokens, authorReadme, assemblePrompt, repairVerdict, moduleFrame, assertGateDigest,
  instructionCoverage, itemSentences, resolveItem,
} from "../scripts/pass.mjs";
import { acceptanceBlock, familyOwners, stageResult, frontTone, yBands, lostInstances, screenProjector, maskFromIdpass } from "../scripts/likeness.mjs";
import { generateForSubject as generateBuilding, CLASS_DEFAULTS as BUILDING_DEFAULTS } from "../scripts/template-building.mjs";
import { generateForSubject as generateVehicle, CLASS_DEFAULTS as VEHICLE_DEFAULTS } from "../scripts/template-vehicle.mjs";
import { runSeat as terraSeat } from "../scripts/seats/terra.mjs";

await K.init();
await K.assemble.ready;

const FACADE = loadSubject("facade_brick");
const PICKUP = loadSubject("pickup");
const TMP = path.join(ROOT, "test", `.tmp-blind-r2-${process.pid}`);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));
let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return import(pathToFileURL(file).href);
}
const codes = (report) => report.violations.map((v) => v.v);

// ---------------------------------------------------------------------------- C1
test("C1: a repair that swaps one gate code for another at equal counts is worse, and names the introduced code", () => {
  const fail = (...vs) => ({ pass: false, report: { violations: vs.map((v) => ({ v })), text: "FAIL" } });
  const lkPass = { pass: true };
  const swapped = repairVerdict({ result: fail("V11_LADDER_ACCESS"), likeness: lkPass }, { result: fail("V11_LANDING_GUARD"), likeness: lkPass });
  assert.equal(swapped.worse, true);
  assert.deepEqual(swapped.introduced, ["V11_LANDING_GUARD"]);
  const fixedOne = repairVerdict({ result: fail("V11_LADDER_ACCESS", "V7"), likeness: lkPass }, { result: fail("V7"), likeness: lkPass });
  assert.equal(fixedOne.worse, false);
  assert.deepEqual(fixedOne.introduced, []);
});

// ---------------------------------------------------------------------------- C2
/** The P2 start module (template through P1) and its real wall planes. */
async function startModule() {
  const mod = await importText(generateBuilding("facade_brick").text);
  const parts = mod.build();
  return { mod, parts, wall: K.assemble.wallPlanes(parts) };
}

function escapeParts(wall, gates, parts) {
  const { W, H } = wall;
  const lowerY = 0.453 * H, upperY = 0.723 * H, depth = 1.1, span = 0.577 * W;
  const cx = wall.streetRight + 0.627 * W, zf = wall.front - depth;
  const xb = cx + span * 0.31, xt = cx - span * 0.19, dropX = cx - span * 0.19;
  const roof = K.assemble.ladder({ base: [wall.streetLeft, 0.3 * H, wall.front + 0.177 * W], height: 0.62 * H, width: 0.54, face: "side", idPrefix: "roof" });
  // WF-R3 H4 — "helper" is now ONE fireEscape call; "declared" keeps the r2 construction (flight hung in front of both
  // decks, gates declared round each arrival), which is the blind-P2 defect and must fail V11_FLIGHT_ON_DECK.
  if (gates === "helper") {
    return [...K.assemble.fireEscape({ wall: parts, centreX: cx, span, depth: 1.4, levels: [lowerY, upperY],
      dropLadder: { bottom: lowerY - 2.4, x: dropX, width: 0.54 }, idPrefix: "fe" }), ...roof];
  }
  const fl = K.assemble.flight({ bottom: [xb, lowerY, zf], top: [xt, upperY, zf], width: 0.72, idPrefix: "fl" });
  const drop = K.assemble.ladder({ base: [dropX, lowerY - 2.4, zf], height: 2.4, width: 0.54, idPrefix: "drop" });
  const landing = (id, y, g) => K.assemble.landing({ span, depth, at: [cx, y], idPrefix: id, ...g });
  const upper = landing("up", upperY, { wallZ: wall.front, gateAt: [xt - 0.36, xt + 0.36] });
  const lower = landing("low", lowerY, { wallZ: wall.front, gateAt: [[xb - 0.36, xb + 0.36], [dropX - 0.27, dropX + 0.27]] });
  return [...upper, ...lower, ...fl, ...drop, ...roof];
}

test("C2: wallPlanes reads the start module's real front plane, sides and ground", async () => {
  const { parts, wall } = await startModule();
  const front = parts.find((p) => p.id === "wall_front").solid.aabb();
  assert.equal(wall.front, front.min[2]);
  assert.ok(wall.streetLeft > wall.streetRight && Math.abs(wall.W - (wall.streetLeft - wall.streetRight)) < 1e-9);
  assert.equal(wall.ground, 0);
  assert.throws(() => K.assemble.wallPlanes([]), /BAD_ARG: wallPlanes/);
});

test("C2 / WF-R3: one fireEscape call against the start module's real wall passes the whole V11 family", async () => {
  const { mod, parts, wall } = await startModule();
  const iron = escapeParts(wall, "helper", parts);
  const report = await validateParts({ ...mod.meta, census: false }, [...parts, ...iron], undefined, { cls: FACADE.cls, rules: BUILDING_RULES, layout: FACADE.readJson("layout") });
  assert.ok(report.timings.V11_DROP_LADDER !== undefined, `the chain reached V11_DROP_LADDER:\n${report.text}`);
  assert.deepEqual(codes(report).filter((c) => /^V11|^V7/.test(c)), [], report.text);
  for (const side of ["l", "r"]) assert.ok(iron.some((p) => p.id === `fe_deck0_return_${side}`), `lower landing return ${side}`);
  assert.ok(iron.every((p) => p.assembly?.helper), "every helper part is tagged");
  assert.equal(report.advisories.filter((a) => a.v === "V11_HANDBUILT").length, 0);
});

test("C2 / WF-R3: the r2 declared-gate escape (flight hung in front of both decks) fails V11_FLIGHT_ON_DECK", async () => {
  const { mod, parts, wall } = await startModule();
  const report = await validateParts({ ...mod.meta, census: false }, [...parts, ...escapeParts(wall, "declared", parts)], undefined, { cls: FACADE.cls, rules: BUILDING_RULES, layout: FACADE.readJson("layout") });
  assert.deepEqual(codes(report), ["V11_FLIGHT_ON_DECK"], report.text);
});

test("C2: a declared gateAt with nothing arriving in it is still an open front, and the row says why", async () => {
  const { mod, parts, wall } = await startModule();
  const deck = K.assemble.landing({ span: 3, depth: 1.1, at: [0, 6], wallZ: wall.front, gateAt: [-0.4, 0.4], idPrefix: "lone" });
  const report = await validateParts({ ...mod.meta, census: false }, [...parts, ...deck], undefined, { cls: FACADE.cls, rules: BUILDING_RULES, layout: FACADE.readJson("layout") });
  const row = report.violations.find((v) => v.v === "V11_LANDING_GUARD");
  assert.ok(row, report.text);
  assert.match(row.hint, /declared gateAt x -0\.700\.\.0\.700 has no ladder or flight head arriving/);
  assert.match(row.hint, /fireEscape/);
});

test("C2: hand-placed landing / stringer / ladder parts are reported as V11_HANDBUILT, never blocked", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/landing-guard.mjs")).href);
  const report = await validateParts(mod.meta, mod.build({ guarded: true }), undefined, { cls: FACADE.cls, rules: BUILDING_RULES });
  assert.equal(report.pass, true, report.text);
  assert.equal(report.advisories.find((a) => a.v === "V11_HANDBUILT")?.part, "landing");
});

// ---------------------------------------------------------------------------- C3
test("C3: MEASURED NUMBERS prints the start module's planes and every cited key in author-frame metres", async () => {
  const { parts } = await startModule();
  const frame = await moduleFrame(parts, FACADE);
  const text = assemblePrompt({
    options: { seatMode: "text", label: "P2", n: 2 },
    item: { item: "i", requiredLayoutKeys: ["window.centreX", "ladder.roof.backFromCorner", "landing.span", "awning.top"] },
    moduleText: "", readme: "", previousReview: null, repairReport: null, frame,
  });
  assert.match(text, /- start module planes \(author frame, metres\): front face z = \+0\.000, back face z = \+\d\.\d{3}, street-right side x = -\d\.\d{3} \(min x\), street-left side x = \+\d\.\d{3} \(max x\), ground y = \+0\.000/);
  assert.match(text, /- window\.centreX: 0\.231 \/ 0\.808 W \(tol \+-[\d.]+\) -> x = -\d\.\d{3} \/ \+\d\.\d{3} m \(x0 -\d\.\d{3} \+ value x W\)/);
  assert.match(text, /- ladder\.roof\.backFromCorner: 0\.177 W .* -> z = \+\d\.\d{3} m \(front face z \+ value x W\)/);
  assert.match(text, /- awning\.top: 0\.278 H .* -> y = \+\d\.\d{3} m \(ground \+ value x H\)/);
  const x = /x = (-\d\.\d{3}) \/ (\+\d\.\d{3}) m/.exec(text);
  assert.ok(Math.abs(Number(x[1]) - (frame.F.x0 + 0.231 * frame.F.W)) < 1e-3);

  const vehicle = await importText(generateVehicle("pickup").text);
  const vFrame = await moduleFrame(vehicle.build(), PICKUP);
  assert.match(vFrame.planes, /^nose z = \+2\.400 \(max z\), tail z = -2\.400/);
  assert.match(vFrame.absolute("headlight.offsetX", PICKUP.readJson("layout")["headlight.offsetX"]) ?? "", /^x = -0\.\d{3} \/ \+0\.\d{3} m$/);   // WF-R3 R3-B item 3: the rule's inverse, metres only
});

// ---------------------------------------------------------------------------- C4 / C10
test("C4/C10: the palette zone list is closed, one author key per material, no cross-material aliases, printed beside the roles", () => {
  for (const S of [FACADE, PICKUP]) {
    const keys = S.cls.paletteZones.filter((z) => z.closure !== true).map((z) => z.key);
    for (const alias of ["trim", "parapet", "metal"]) assert.ok(!S.cls.paletteZones.some((z) => z.key === alias), `${S.id}: alias ${alias}`);
    assert.equal(new Set(keys).size, keys.length);
    for (const z of S.cls.paletteZones) assert.ok(z.closure === true ? keys.includes(z.material) : typeof z.for === "string", `${S.id} ${z.key}`);
    const readme = authorReadme(gateTokens(S.cls), S);
    const list = readme.slice(readme.indexOf("## Palette zones — a CLOSED list"));
    assert.ok(readme.indexOf("## Roles — a CLOSED list") < readme.indexOf("## Palette zones — a CLOSED list"));
    for (const k of keys) assert.match(list, new RegExp(`^- \`${k}\` — `, "m"));
    for (const z of S.cls.paletteZones.filter((e) => e.closure)) assert.doesNotMatch(list.split("\n## ")[0], new RegExp(`^- \`${z.key}\``, "m"));
  }
  assert.equal(PICKUP.cls.paletteZones.find((z) => z.key === "lamp").region, "headlight");
});

test("C4/C10: a part in a zone the class does not list is a PALETTE_ZONE gate row that names the right key", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/landing-guard.mjs")).href);
  const parts = mod.build({ guarded: true }).map((p) => (p.zone === "iron" ? { ...p, zone: "metal" } : p));
  const report = await validateParts({ ...mod.meta, palette: { ...mod.meta.palette, metal: "#c0c0bf" } }, parts, undefined, { cls: FACADE.cls, rules: BUILDING_RULES });
  assert.equal(report.violations[0].v, "PALETTE_ZONE", report.text);
  assert.match(report.violations[0].hint, /zone "metal" is not a palette zone of class building/);
  const smoke = await import(pathToFileURL(path.join(ROOT, "test/fixtures/vehicle/smoke.mjs")).href);
  const lamp = { id: "lamp", solid: K.box([0.2, 0.2, 0.06]).at([0, 1, 2.3]), zone: "headlight", role: "headlight" };
  const vreport = await validateParts(smoke.meta, [...smoke.build(), lamp], undefined, { cls: PICKUP.cls, rules: VEHICLE_RULES });
  const row = vreport.violations.find((v) => v.v === "PALETTE_ZONE") ?? vreport.advisories.find((v) => v.v === "PALETTE_ZONE");
  if (row) assert.match(row.hint, /use "lamp"/);
});

// ---------------------------------------------------------------------------- C5
test("C5: an LK_AREA family is owned by the pass that builds it; judged there over the families built so far, attributed there at the end", () => {
  const owners = familyOwners({ prior: FACADE.cls.likeness, regions: FACADE.readJson("regions"), census: FACADE.readJson("census"), passes: FACADE.readJson("passes") });
  // V5-8 R3 (deliberate update, old-era pin): the "green" family (awning + signbox) is split — the two share a colour
  // family, so each item's accuracy target held the other; classes/building.json likeness.areaFamilies now has awning
  // and signbox as their own families. Counts below: the old green 192 / 218 split in the same proportion.
  assert.deepEqual(owners, { brick: 0, glass: 1, iron: 2, awning: 1, signbox: 1, grey: 1 });
  const counts = (brick, glass, iron, green, grey) => ({ brick, glass, iron, awning: Math.round(green * 0.78), signbox: green - Math.round(green * 0.78), grey });
  const raw = {
    violations: [{ v: "LK_AREA", part: "glass", measured: "m", limit: "l", hint: "family glass covers the wrong share of the FRONT FACE", blocking: true }],
    advisories: [], unverified: [], visible: {},
    areaFamilies: { target: { counts: counts(560, 114, 123, 192, 10) }, render: { counts: counts(650, 67, 46, 218, 17) } },
  };
  const p1 = stageResult(raw, false, new Set(), { n: 1, owners });
  assert.deepEqual(p1.violations.map((v) => `${v.v} ${v.part}`).sort(), ["LK_AREA glass", "LK_AREA grey"]);
  assert.match(p1.violations.find((v) => v.part === "glass").measured, /over the families built by P1 \(brick, glass, awning, signbox, grey\)/);
  const p2 = stageResult(raw, true, new Set(), { n: 2, owners });
  assert.equal(p2.pass, true);
  assert.match(p2.advisories[0].hint, /attributed to P1, the pass that builds this family/);
  const text = acceptanceBlock({ prior: FACADE.cls.likeness, census: FACADE.readJson("census"), regions: FACADE.readJson("regions"), n: 2, final: true, passes: FACADE.readJson("passes") });
  assert.match(text, /glass \(glass\+door\+storefront, built by P1\)/);
});

test("C5: the building template consumes the measured storefront.bottom and builds the AC at ac.w x ac.h", async () => {
  const layout = FACADE.readJson("layout");
  assert.ok(Number.isFinite(layout["storefront.bottom"]?.value) && layout["storefront.bottom"].evidence?.px, "storefront.bottom is a measured key");
  const gen = generateBuilding("facade_brick");
  assert.ok(!gen.stubs.includes("missing key storefront.bottom"), gen.stubs.join("; "));
  const parts = (await importText(gen.text)).build();
  const pane = parts.find((p) => p.id === "storefront_0_glass").solid.aabb();
  assert.ok(Math.abs(pane.min[1] + 0.00075 - layout["storefront.bottom"].value * gen.H) < 1e-6, `pane bottom ${pane.min[1]}`);
  const ac = parts.find((p) => p.id === "shop_ac_0").solid.aabb();
  assert.ok(Math.abs(ac.max[0] - ac.min[0] - layout["ac.w"].value * gen.W) < 1e-6);
  assert.ok(Math.abs(ac.max[1] - ac.min[1] - layout["ac.h"].value * gen.H) < 1e-6);
  for (const g of parts.filter((p) => /^ac_0_grille_/.test(p.id)).map((p) => p.solid.aabb())) {
    assert.ok(g.min[0] >= ac.min[0] && g.max[0] <= ac.max[0] && g.min[1] >= ac.min[1] && g.max[1] <= ac.max[1], "the grille stays inside the case outline");
  }
});

// ---------------------------------------------------------------------------- C6
test("C6: a flat-shaded member's front tone is the brightest frequent colour; same-material zones split by screen y", () => {
  const side = [0x67, 0x59, 0x4e];
  const front = [0x8f, 0x7d, 0x6e];
  const band = [...Array(40).fill(side), ...Array(25).fill(front), ...Array(3).fill([0xff, 0xff, 0xff])];   // 3 px of white edge: a speck, not a face
  assert.deepEqual(frontTone(band), front);
  const pts = [...Array(30).fill(0).map((_, i) => [370 + (i % 9), ...side]), ...Array(20).fill(0).map((_, i) => [525 + (i % 9), ...front])];
  const [top, bottom] = yBands(pts, 2);
  assert.equal(top.length, 30);
  assert.equal(bottom.length, 20);
  const regions = FACADE.readJson("regions");
  for (const z of ["iron_landing_upper", "iron_landing_lower"]) assert.equal(regions.zones[z].face, "front");
});

// ---------------------------------------------------------------------------- C7 / C8
test("C7: a Terra transport drop keeps the transcript with the exit status; C8: blind-test records NO_RESULT without archiving a pass folder", async () => {
  const seat = await terraSeat({ prompt: "x", images: [], tag: "r2-test", env: { ...process.env, CODEX_BIN: path.join(os.tmpdir(), "no-such-codex.exe") } });
  assert.equal(seat.failureClass, "transport");
  assert.match(seat.transcript, /---EXIT--- status=null signal=none error=ENOENT/);
  const source = fs.readFileSync(path.join(ROOT, "scripts/blind-test.mjs"), "utf8");
  assert.match(source, /exit === 2 \? "NO_RESULT"/);
  assert.match(source, /if \(exit === 2\) \{[\s\S]*?\} else \{\s*copyDir\(passDir, dest\);/);
});

// ---------------------------------------------------------------------------- C9 + C14
test("C9: a thin cut no longer throws; the part carries it and the chain reports V5_THIN with side and tool box", async () => {
  K.configure(gateConfig(FACADE.cls));
  const panel = K.cut(K.box([1, 1, 0.06]).at([0, 0, 0]), K.box([0.9, 0.2, 0.02]).at([0, 0.4, -0.02]));
  assert.equal(panel.thinCuts()[0].code, "V5_THIN");
  assert.ok(Math.abs(panel.thinCuts()[0].remaining - 0.04) < 1e-9);
  const moved = panel.at([0, 1, 0]);
  assert.equal(moved.thinCuts().length, 1, "the record travels with the solid");
  const meta = { class: "building", seed: 1, census: false, layout: false, palette: { brick: "#a85643" } };
  const report = await validateParts(meta, [{ id: "wall", solid: panel, zone: "brick", role: "massing" }], undefined, { cls: FACADE.cls, rules: BUILDING_RULES });
  const row = report.violations.find((v) => v.v === "V5_THIN");
  assert.ok(row, report.text);
  assert.match(row.measured, /^0\.040 m left on z\+ by a cut \(tool x -0\.450\.\.0\.450, y 0\.400\.\.0\.600, z -0\.030\.\.-0\.010\)$/);
  assert.match(row.hint, /groove only panels >= 0\.080 m thick/);
  K.configure(null);
});

test("C9: the minimum panel thickness is a gate token in both classes and the templates' panels are at least that thick", () => {
  const building = gateTokens(FACADE.cls);
  const vehicle = gateTokens(PICKUP.cls);
  assert.equal(building.MIN_PANEL, 0.08);
  assert.equal(vehicle.MIN_PANEL, 0.06);
  for (const v of [BUILDING_DEFAULTS.wall, BUILDING_DEFAULTS.slab]) assert.ok(v >= building.MIN_PANEL, `building panel ${v}`);
  for (const v of [VEHICLE_DEFAULTS.wallT, VEHICLE_DEFAULTS.floorT, VEHICLE_DEFAULTS.bumperD]) assert.ok(v >= vehicle.MIN_PANEL, `vehicle panel ${v}`);
  assert.match(authorReadme(vehicle, PICKUP), /The thinnest panel you may groove 0\.02 m deep is 0\.06 m/);
});

test("C14: the pickup prompt's advertised MIN_FEAT is the MIN_FEAT the kernel enforces and the chain reports, under one digest", async () => {
  const tokens = gateTokens(PICKUP.cls);
  const readme = authorReadme(tokens, PICKUP);
  assert.equal(tokens.MIN_FEAT, 0.04);
  assert.match(readme, /\*\*MIN_FEAT = 0\.04 m\*\*/);
  K.configure(gateConfig(PICKUP.cls));
  assert.equal(K.config().minFeat, tokens.MIN_FEAT);
  const slot = (margin) => K.cut(K.box([0.4, 0.2, 0.2]), K.box([0.4 - 2 * margin, 0.05, 0.02]).at([0, 0.1, 0.095]));
  assert.equal(slot(0.05).thinCuts().length, 0, "0.05 m margins are legal under the vehicle floor the prompt states");
  assert.equal(slot(0.03).thinCuts().length, 1, "0.03 m margins are not");
  const smoke = await import(pathToFileURL(path.join(ROOT, "test/fixtures/vehicle/smoke.mjs")).href);
  const report = await validateParts(smoke.meta, smoke.build(), undefined, { cls: PICKUP.cls, rules: VEHICLE_RULES });
  assert.equal(report.measurements.minFeature, tokens.MIN_FEAT);
  assert.equal(assertGateDigest({ prompt: tokens.GATE_DIGEST, kernel: K.config().digest, report: report.measurements.gateDigest }), tokens.GATE_DIGEST);
  assert.throws(() => assertGateDigest({ prompt: gateTokens(FACADE.cls).GATE_DIGEST, kernel: K.config().digest }), RefusalError);
  K.configure(null);
});

// ---------------------------------------------------------------------------- C11
test("C11: ACCEPTANCE keeps visible-instance requirements for roles an earlier pass built", () => {
  const text = acceptanceBlock({ prior: PICKUP.cls.likeness, census: PICKUP.readJson("census"), regions: PICKUP.readJson("regions"), n: 1, final: true, passes: PICKUP.readJson("passes") });
  assert.match(text, /Already built before P1 — these instances must STAY visible at the solved camera/);
  assert.match(text, /^- 3 wheel instance\(s\) must stay visible \(built in P0\)$/m);
  assert.match(text, /^- 2 bumper instance\(s\) must stay visible \(built in P0\)$/m);
  assert.doesNotMatch(text, /^- \d+ headlight instance/m);
});

test("C11: an instance visible in the previous id pass and covered now is named with the covering role and part", () => {
  const colours = { wheel: "#8000ff", bumper: "#0080ff", cab: "#0000ff" };
  const image = (paint) => {
    const w = 40, h = 40, data = Buffer.alloc(w * h * 3);
    paint((x, y, hex) => { const i = (y * w + x) * 3; data[i] = parseInt(hex.slice(1, 3), 16); data[i + 1] = parseInt(hex.slice(3, 5), 16); data[i + 2] = parseInt(hex.slice(5, 7), 16); });
    return { data, w, h, c: 3 };
  };
  const blob = (set, x0, y0, hex) => { for (let y = y0; y < y0 + 10; y += 1) for (let x = x0; x < x0 + 10; x += 1) set(x, y, hex); };
  const previous = image((set) => { blob(set, 2, 2, colours.wheel); blob(set, 25, 25, colours.wheel); });
  const now = image((set) => { blob(set, 2, 2, colours.wheel); blob(set, 25, 25, colours.bumper); });
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "out/blind/pickup/agy/P1/idpass.png.json"), "utf8")).manifest;
  const project = screenProjector(manifest);
  const [u, v] = project(manifest.frontQuad.world[0]);
  assert.ok(Math.abs(u - manifest.frontQuad.px[0][0]) < 1 && Math.abs(v - manifest.frontQuad.px[0][1]) < 1, "the fitted projection reproduces the quad corners");
  const lost = lostInstances({ occlusion: { previous: { image: previous, idColours: colours }, label: "P0" }, mask: maskFromIdpass(now, colours), role: "wheel", w: 40, h: 40 });
  assert.equal(lost.length, 1);
  assert.equal(lost[0].role, "bumper");
  assert.deepEqual([lost[0].x0, lost[0].y0], [25, 25]);
});

// ---------------------------------------------------------------------------- C12
test("C12: every sentence of every pass item maps to a gate / likeness row or a stated exemption", async () => {
  for (const S of [FACADE, PICKUP]) {
    const rules = S.id === "pickup" ? VEHICLE_RULES : BUILDING_RULES;
    for (const item of S.readJson("passes")) {
      const resolved = resolveItem(item, gateTokens(S.cls));
      const coverage = instructionCoverage(resolved, { layoutRules: rules.layoutRules, census: S.readJson("census") });
      assert.deepEqual(coverage.warnings, [], `${S.id} ${item.id}`);
      assert.ok(coverage.rows.length === itemSentences(resolved.item).length);
    }
  }
  const unmapped = instructionCoverage({ id: "P9", item: "Paint the roof gold. Layout keys this pass must satisfy: a.b.", instructionRows: [{ match: "Layout keys", rows: ["V12_LAYOUT:no.such"] }] }, { layoutRules: BUILDING_RULES.layoutRules });
  assert.equal(unmapped.warnings.length, 2);
  assert.match(unmapped.warnings[0], /no gate or likeness row checks "Paint the roof gold\."/);
});

test("C12: grille.slots is measured on the target and gated — a solid grille panel fails V12_LAYOUT, a slotted one passes", async () => {
  const entry = PICKUP.readJson("layout")["grille.slots"];
  assert.equal(entry.value, 2);
  assert.match(entry.evidence.px, /2 slot component\(s\)/);
  const panel = K.box([0.8, 0.3, 0.08]).at([0, 1, 2.4]);
  const slotted = K.cut(panel, K.union([K.box([0.7, 0.08, 0.02]).at([0, 1.05, 2.475]), K.box([0.7, 0.08, 0.02]).at([0, 1.17, 2.475])]));
  const measure = (solid) => VEHICLE_RULES.layoutRules["grille.slots"].measure({ records: [{ id: "grille", role: "grille", aabb: solid.aabb(), part: { solid } }] }, {})[0].measured;
  assert.equal(measure(panel), 0);
  assert.equal(measure(slotted), 2);
  assert.equal(slotted.thinCuts().length, 0, "0.06 m of panel behind a 0.02 m slot in a 0.08 m panel is legal for a vehicle");
});
