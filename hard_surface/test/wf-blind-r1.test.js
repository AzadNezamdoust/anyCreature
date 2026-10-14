// WF-BLIND-R1 rows B1-B6 (examiner job 2 after the blind Gemini pickup P1 run): the workflow gaps any
// author model hits — union seating, missing appearance numbers, handoff contradictions, hidden
// acceptance, class-foreign README text, and evidence lost between attempts.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import {
  ROOT, gateTokens, resolveTokens, authorReadme, filterClassSections, assemblePrompt, rulesBlock, parseArgs,
  unverifiedItemKeys, requiredLayoutKeys, itemLayoutKeys, resolveItem, ARRAY_RULE, MEASUREMENT_RULE,
  attemptDir, clearAttempts, finalizeAttempt, likenessForAttempt,
} from "../scripts/pass.mjs";
import { acceptanceBlock, dueVisibleParts, stageResult } from "../scripts/likeness.mjs";
import { generateForSubject as generateVehicle } from "../scripts/template-vehicle.mjs";
import { generateForSubject as generateBuilding } from "../scripts/template-building.mjs";

const read = (rel) => fs.readFileSync(path.join(ROOT, rel), "utf8");
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "llmm-blind-r1-"));
const PICKUP = loadSubject("pickup");
const FACADE = loadSubject("facade_brick");
const TEMPLATE_HEADER = "Generated starting point; edits required by this pass or its LOOK failures are allowed.";
// Two levels under ROOT, like subjects/<id>/, so a generated module's relative kernel import resolves.
const TMP_MODULES = path.join(ROOT, "test", `.tmp-blind-r1-${process.pid}`);
test.after(() => fs.rmSync(TMP_MODULES, { recursive: true, force: true }));
let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP_MODULES, { recursive: true });
  const file = path.join(TMP_MODULES, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return import(pathToFileURL(file).href);
}

// ---------------------------------------------------------------------------- B1
const UNION_RULE = "Every structural part must join the solid union; a positive gap fails V3 even within contact tolerance.";

test("B1: {INFERRED_CONTACT_FRAC} is a gate token; the union rule is stated once, in the kernel README, and both classes point to it", () => {
  assert.equal(gateTokens({ styleFloorKey: "vehicle" }).INFERRED_CONTACT_FRAC, 0.02);
  const readme = read("src/kernel/README.md");
  assert.equal(readme.split(UNION_RULE).length - 1, 1);
  assert.match(readme, /Seat a\s+part with a positive overlap no greater than \{INFERRED_CONTACT_FRAC\} of its volume/);
  for (const cls of ["vehicle", "building"]) {
    const md = read(`classes/${cls}.md`);
    assert.match(md, /\*\*Contact\*\*/, `${cls}.md references the Contact section`);
    assert.ok(!md.includes(UNION_RULE), `${cls}.md does not restate the rule`);
  }
  for (const S of [PICKUP, FACADE]) {
    const text = authorReadme(gateTokens(S.cls), S);
    assert.match(text, /no greater than 0\.02 of its volume/);
    assert.doesNotMatch(text, /\{[A-Z][A-Z0-9_]*\}/);
  }
});

// WF-R3 R3-B item 2: the hand-written pane-in-recess example became K.assemble.pane (the recess and the seat are the
// helper's); the same two facts are asserted on what the helper builds.
test("B1: K.assemble.pane seats the pane into the recess it cuts (one lump); 1 mm off the floor comes apart", async () => {
  await K.init();
  await K.assemble.ready;
  const host = { id: "cab", role: "cab", zone: "body", solid: K.box([2, 1.5, 1]) };
  const parts = K.assemble.pane({ host, face: "+z", bounds: K.span({ x: [-0.6, 0.6], y: [0.4, 1.0] }) });
  const cab = host.solid;
  const pane = parts[0].solid;
  assert.equal(parts.length, 1);
  assert.equal(K.union(cab, pane).decompose().length, 1, "seated pane joins the union");
  const frac = K.intersect(cab, pane).volume() / pane.volume();
  assert.ok(frac > 0 && frac <= 0.02, `overlap fraction ${frac}`);
  assert.equal(K.union(cab, pane.at([0, 0, 0.0015])).decompose().length, 2, "a pane 1 mm in front of the floor is a second lump");
});

// ---------------------------------------------------------------------------- B2
const APPEARANCE = ["headlight.diameter", "grille.w", "grille.h", "mirror.offsetX", "mirror.head.w", "mirror.head.h", "mirror.arm.length",
  "window.front.w", "window.front.bottom", "window.side.start", "window.side.end", "window.side.bottom", "window.side.top"];

test("B2: measure-vehicle froze the appearance keys with evidence and tol; the unresolvable one carries a reason", () => {
  const layout = PICKUP.readJson("layout");
  const measured = PICKUP.readJson("layoutMeasured");
  for (const k of APPEARANCE) {
    const e = layout[k];
    assert.ok(e && e.unverified !== true, `${k} is measured`);
    assert.ok(e.evidence?.scan && e.evidence?.px, `${k} evidence`);
    assert.ok(Number.isFinite(e.tol), `${k} tol`);
    assert.ok(measured[k], `${k} in layout.measured.json`);
  }
  // WF-R3 R3-B item 5: the rake is resolved on the plane of the pane's near edge (the bottom corner's inset).
  assert.ok(layout["window.front.top"].value > layout["window.front.bottom"].value);
  assert.match(layout["window.front.top"].evidence.scan, /rectified on the plane x = flank \+ the bottom corner's inset/);
  assert.ok(layout["window.front.topAt"].value > layout["cab.start"].value, "the windshield rakes BACK from cab.start");
  assert.ok(layout["window.side.start"].value < layout["window.side.end"].value);
  assert.ok(layout["window.side.bottom"].value < layout["window.side.top"].value);
});

test("B2: passes.json carries requiredLayoutKeys — facade copies today's lists, pickup P1 adds verified appearance keys + construction defaults", () => {
  for (const p of FACADE.readJson("passes")) assert.deepEqual(p.requiredLayoutKeys, itemLayoutKeys(p.item), `facade ${p.id}`);
  const [p0, p1] = PICKUP.readJson("passes");
  assert.deepEqual(p0.requiredLayoutKeys, itemLayoutKeys(p0.item));
  const layout = PICKUP.readJson("layout");
  for (const k of [...APPEARANCE.filter((k) => k !== "window.front.top"), "headlight.centreY", "headlight.offsetX", "mirror.centreY"]) {
    assert.ok(p1.requiredLayoutKeys.includes(k), `P1 requires ${k}`);
  }
  assert.deepEqual(unverifiedItemKeys(p1.item, layout, p1.requiredLayoutKeys), [], "P1 requires no unverified key");
  // WF-R3 R3-B items 2 + 6: the construction numbers (pane thickness, recess, seat, slot depth) live in the helpers;
  // the item is the helper calls and restates no key.
  const resolved = resolveItem(p1, gateTokens(PICKUP.cls));
  assert.equal(resolved.constructionDefaults, undefined);
  for (const h of ["pane", "lamp", "grille", "mirror"]) assert.match(resolved.item, new RegExp(`K\\.assemble\\.${h}\\b`));
  assert.doesNotMatch(resolved.item, /headlight\.diameter/);
});

test("B2: MEASURED NUMBERS prints the required keys (no substring discovery), ABSENT keys, the rule sentence; construction defaults are labelled", () => {
  const text = assemblePrompt({
    options: { seatMode: "text", label: "P0", n: 0 },
    item: {
      item: "prose that mentions crown.height",
      requiredLayoutKeys: ["massing.depthOverW", "no.such.key"],
      constructionDefaults: { "seat.overlap": { value: 0.0005, unit: "m", why: "a positive overlap" } },
    },
    moduleText: "", readme: "", previousReview: null, repairReport: null,
  });
  assert.match(text, /- massing\.depthOverW: 0\.8\d+ x W \(tol \+-/);
  assert.doesNotMatch(text, /- crown\.height:/);
  assert.match(text, /- no\.such\.key: ABSENT/);
  assert.ok(text.includes(MEASUREMENT_RULE));
  assert.match(text, /# CONSTRUCTION DEFAULTS/);
  assert.match(text, /- seat\.overlap: 0\.0005 m — a positive overlap/);
});

test("B2: the unverified refusal reads requiredLayoutKeys, falling back to the item's key list, never to prose", () => {
  const layout = { "a.b": { unverified: true }, "c.d": { value: 1 } };
  assert.deepEqual(unverifiedItemKeys("Layout keys this pass must satisfy: a.b, c.d.", layout), ["a.b"]);
  assert.deepEqual(unverifiedItemKeys("Layout keys this pass must satisfy: a.b, c.d.", layout, ["c.d"]), []);
  assert.deepEqual(unverifiedItemKeys("prose that mentions a.b", layout), []);
  assert.deepEqual(requiredLayoutKeys({ item: "Layout keys this pass must satisfy: a.b." }), ["a.b"]);
  assert.deepEqual(requiredLayoutKeys({ item: "Layout keys this pass must satisfy: a.b.", requiredLayoutKeys: ["c.d"] }), ["c.d"]);
});

// ---------------------------------------------------------------------------- B3
test("B3: both template headers invite the edits a pass or its LOOK failures require", () => {
  for (const text of [generateVehicle("pickup").text, generateBuilding("facade_brick").text]) {
    assert.ok(text.includes(TEMPLATE_HEADER));
    assert.doesNotMatch(text, /Do not hand-edit/);
  }
});

test("B3: PREVIOUS REVIEW is UNREVIEWED when missing, 'no failed rows' when clean, the rows when failed; nothing at P0", () => {
  const prompt = (n, previousReview, seatMode = "text") => assemblePrompt({
    options: { seatMode, label: `P${n}`, n }, item: { item: "i" }, moduleText: "", readme: "", previousReview, repairReport: null,
  });
  assert.match(prompt(1, null), /^PREVIOUS REVIEW: UNREVIEWED/m);
  assert.match(prompt(1, null, "agent"), /^PREVIOUS REVIEW: UNREVIEWED/m);
  assert.match(prompt(1, "| 1 | orientation | x | PASS | |"), /^PREVIOUS REVIEW: no failed rows$/m);
  const failed = prompt(1, "| 3 | reads as the target | x | FAIL | n |");
  assert.match(failed, /reads as the target/);
  assert.doesNotMatch(failed, /PREVIOUS REVIEW: (UNREVIEWED|no failed rows)/);
  assert.doesNotMatch(prompt(0, null), /PREVIOUS REVIEW/);
});

// ---------------------------------------------------------------------------- B4
const acceptance = (S, n, final) => acceptanceBlock({ prior: S.cls.likeness, census: S.readJson("census"), regions: S.readJson("regions"), n, final });

test("B4: ACCEPTANCE is generated from the likeness config: due roles with census count, visible instances, px threshold; value/hue/area bands", () => {
  const p1 = acceptance(PICKUP, 1, true);
  assert.match(p1, /^# ACCEPTANCE/);
  assert.match(p1, /\| wheel \| 4 \| 3 \(the target hides the rest\) \| >= 50 \|/);
  assert.match(p1, /\| window \| 3 \| 2 \(the target hides the rest\) \| >= 50 \|/);
  assert.match(p1, /\| headlight \| 2 \| 2 \| >= 50 \|/);
  assert.match(p1, /\| mirror \| 2 \| 2 \| >= 50 \|/);
  assert.match(p1, /LK_VALUE: every zone renders at 0\.85–1\.15 x/);
  assert.match(p1, /LK_HUE: every zone within 12 deg/);
  assert.match(p1, /LK_AREA: each family's share of the front-face quad within \+-30 %/);
  const p0 = acceptance(PICKUP, 0, false);
  assert.match(p0, /\| bumper \| 2 \| 2 \| >= 50 \|/);
  assert.doesNotMatch(p0, /\| headlight \|/);
  assert.match(p0, /LK_AREA \(judged at the final pass only\)/);
  const facade = acceptance(FACADE, 2, true);
  assert.match(facade, /\| stringer \| 1 \| 1 \| >= 50 x 1 pooled \(thin member\) \|/);
  assert.match(facade, /LK_OVERLAP: 0 px of ladder\/rung/);
  const text = assemblePrompt({ options: { seatMode: "text", label: "P1", n: 1 }, item: { item: "i" }, moduleText: "", readme: "", previousReview: null, repairReport: null, acceptance: p1 });
  assert.ok(text.includes(p1.trim()));
});

test("B4: LK_VISIBLE is judged from the pass its census key is due; LK_AREA / LK_OVERLAP stay final-only", () => {
  const prior = PICKUP.cls.likeness;
  const census = PICKUP.readJson("census");
  const regions = PICKUP.readJson("regions");
  const row = (v, part) => ({ v, part, measured: "m", limit: "l", hint: "h", blocking: true });
  const raw = {
    violations: [row("LK_VISIBLE", "wheel"), row("LK_VISIBLE", "headlight"), row("LK_VISIBLE", "glass"), row("LK_AREA", "body"), row("LK_OVERLAP", "window"), row("LK_HUE", "tyre")],
    advisories: [], unverified: [], visible: { wheel: {}, headlight: {}, window: {} },
  };
  const parts = (n) => [...stageResult(raw, false, dueVisibleParts({ prior, census, regions, n })).violations].map((v) => `${v.v} ${v.part}`);
  assert.deepEqual(parts(0), ["LK_VISIBLE wheel", "LK_HUE tyre"]);
  assert.deepEqual(parts(1), ["LK_VISIBLE wheel", "LK_VISIBLE headlight", "LK_VISIBLE glass", "LK_HUE tyre"]);
  assert.equal(stageResult(raw, true).violations.length, 6);
  assert.match(stageResult(raw, false, dueVisibleParts({ prior, census, regions, n: 0 })).text, /LK_VISIBLE judged for the roles due by this pass \(wheel\)/);
});

// ---------------------------------------------------------------------------- B5
test("B5: the author README is class-selective — the building frame, example and assemblies never reach a vehicle author", () => {
  const vehicle = authorReadme(gateTokens(PICKUP.cls), PICKUP);
  const building = authorReadme(gateTokens(FACADE.cls), FACADE);
  for (const re of [/meta\.front: "-Z"/, /K\.assemble\.fireEscape|wallPlanes/, /Mini-example/, /REPLACES the building frame/]) assert.doesNotMatch(vehicle, re);
  for (const re of [/# Class rules — vehicle/, /## Contact/, /Declare `meta\.front: "\+X"`/, /## Solid constructors/, /K\.profile\.poly/]) assert.match(vehicle, re);
  for (const re of [/meta\.front: "-Z"/, /K\.assemble\.fireEscape/, /Mini-example/, /# Class rules — building/]) assert.match(building, re);
  for (const text of [vehicle, building]) assert.doesNotMatch(text, /<!--/);
  assert.equal(filterClassSections("a\n<!-- class:building -->\nb\n<!-- /class -->\nc", "vehicle"), "a\nc");
  assert.equal(filterClassSections("a\n<!-- class:building -->\nb\n<!-- /class -->\nc", "building"), "a\nb\nc");
  assert.ok(vehicle.length < building.length - 3000, `vehicle README ${vehicle.length} vs building ${building.length} chars`);
});

test("B5: one touches/embed policy — stated once; the rules block defers to it and bans only raw 3D mesh data", () => {
  const policy = "Never write\n  `touches` without `embed: true`.";
  for (const S of [PICKUP, FACADE]) {
    const all = `${authorReadme(gateTokens(S.cls), S)}\n${rulesBlock(false, "text", S.rel.module)}`;
    assert.equal(all.split(policy).length - 1, 1, `${S.id}: the policy appears once`);
    assert.doesNotMatch(all, /name a part in `touches` only together/);
  }
  const rules = rulesBlock(false, "text", "m.mjs");
  assert.ok(rules.includes(ARRAY_RULE));
  assert.doesNotMatch(rules, /literal vertex arrays/);
});

test("B5: both templates follow the policy — no bare touches; every declared touches is an embed seat", async () => {
  await K.init();
  const vehicle = (await importText(generateVehicle("pickup").text)).build();
  assert.ok(vehicle.every((p) => p.touches === undefined && p.embed === undefined), "vehicle template declares nothing");
  const building = (await importText(generateBuilding("facade_brick").text)).build();
  const declared = building.filter((p) => p.touches !== undefined);
  assert.ok(declared.length >= 5, `building seats: ${declared.length}`);
  assert.ok(declared.every((p) => p.embed === true && p.touches.length > 0), "every touches carries embed: true");
});

test("B5/B6: parseArgs takes --prompt-only and --prompt-out", () => {
  const o = parseArgs(["P1", "--subject", "pickup", "--prompt-only", "--prompt-out", "x.md"]);
  assert.equal(o.promptOnly, true);
  assert.equal(o.promptOut, "x.md");
  assert.equal(parseArgs(["P0"]).promptOnly, false);
});

// ---------------------------------------------------------------------------- B6
const touch = (file, text) => { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, text); };

test("B6: every attempt keeps its own evidence; finalize copies the last attempt to today's names and drops stale ones", () => {
  const out = tmp();
  const a1 = attemptDir(out, 1);
  const a2 = attemptDir(out, 2);
  for (const f of ["module.mjs", "report.json", "target.png", "target.png.json", "threeQuarter.png", "idpass.png", "likeness.json", "compare.png"]) {
    touch(path.join(a1, f), `a1 ${f}`);
  }
  for (const f of ["module.mjs", "report.json", "likeness.json"]) touch(path.join(a2, f), `a2 ${f}`);   // attempt 2: capture refused
  touch(path.join(out, "target.png"), "stale");
  touch(path.join(out, "prompt.md"), "kept");
  const copied = finalizeAttempt(out, a2, "module.mjs");
  assert.deepEqual(copied.sort(), ["likeness.json", "module.mjs", "report.json"]);
  assert.equal(fs.readFileSync(path.join(out, "module.mjs"), "utf8"), "a2 module.mjs");
  assert.equal(fs.readFileSync(path.join(out, "likeness.json"), "utf8"), "a2 likeness.json");
  assert.ok(!fs.existsSync(path.join(out, "target.png")), "a stale top-level still is removed, never reused");
  assert.equal(fs.readFileSync(path.join(a1, "target.png"), "utf8"), "a1 target.png", "attempt 1 evidence is kept");
  assert.ok(fs.existsSync(path.join(out, "prompt.md")));
  clearAttempts(out);
  assert.ok(!fs.existsSync(a1) && !fs.existsSync(a2));
  assert.ok(fs.existsSync(path.join(out, "prompt.md")), "clearAttempts touches only attempt-N directories");
});

test("B6: a capture refusal marks that attempt's likeness UNVERIFIED and never measures stale stills", async () => {
  const out = tmp();
  touch(path.join(out, "target.png"), "stale still from an earlier attempt");
  const dir = attemptDir(out, 2);
  fs.mkdirSync(dir, { recursive: true });
  let calls = 0;
  const measure = async () => { calls += 1; return { pass: true, text: "PASS", table: "", result: {}, ms: 1 }; };
  const refused = await likenessForAttempt({ label: "P1", dir, captures: { target: { ok: false }, threeQuarter: { ok: true } }, measure });
  assert.equal(calls, 0);
  assert.equal(refused.pass, false);
  assert.equal(refused.unverified, true);
  assert.match(refused.text, /^UNVERIFIED: capture refused/);
  assert.equal(JSON.parse(fs.readFileSync(path.join(dir, "likeness.json"), "utf8")).state, "UNVERIFIED");
  const ok = await likenessForAttempt({ label: "P1", dir, captures: { target: { ok: true }, threeQuarter: { ok: true } }, measure });
  assert.equal(calls, 1);
  assert.equal(ok.pass, true);
});
