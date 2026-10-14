// WF-R3 Job R3-A (research/WF-R3-PLAN.md) — building + harness truth after the Luna / Gemini-M baseline blind runs:
// H1 stale review, H4 flights hung in front of their decks (fireEscape by construction + three V11 rows), C15 roof
// ladder foot + absolute datums, author file:line in module throws. Fixtures under test/fixtures/building/ are FROZEN
// copies of the archived blind P2 modules and the run-4 building (import path re-pointed only).
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, chainContext } from "../src/validate/kernel-chain.mjs";
import * as BUILDING_RULES from "../src/validate/rules/building.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { ROOT, reviewRow3, reviewModuleHash } from "../scripts/pass.mjs";
import { authorLine } from "../scripts/check-module.mjs";
import { generateForSubject as generateBuilding } from "../scripts/template-building.mjs";
import { archived } from "./fixtures/building/archived-gates.mjs";

await K.init();
await K.assemble.ready;

const FACADE = loadSubject("facade_brick");
const FIX = path.join(ROOT, "test", "fixtures", "building");
const TMP = path.join(ROOT, "test", `.tmp-wf-r3-${process.pid}`);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));
let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text.replace(/"\.\.\/\.\.\/(\.\.\/)?src\/kernel\/index\.mjs"/, '"../../src/kernel/index.mjs"'));
  return import(pathToFileURL(file).href);
}
const opts = () => ({ cls: FACADE.cls, rules: BUILDING_RULES, layout: FACADE.readJson("layout"), census: FACADE.readJson("census") });
const row = (ctx, name) => BUILDING_RULES.validators.find(([n]) => n === name)[1](ctx).violations;
const NEW_ROWS = ["V11_FLIGHT_ON_DECK", "V11_RAIL_COVERAGE", "V11_DROP_LADDER"];

// ---------------------------------------------------------------------------------------------------- H1
test("H1: a review.md that records another module (or none) never yields a verdict row; the matching one does", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "wf-r3-review-"));
  const body = "| 3 | reads as the target | PASS with residual | ok |\n";
  fs.writeFileSync(path.join(dir, "review.md"), `# review (run 4)\nmodule: 05056b1b1b58533a\n${body}`);
  assert.equal(reviewModuleHash(fs.readFileSync(path.join(dir, "review.md"), "utf8")), "05056b1b1b58533a");
  assert.equal(reviewRow3(dir, "aaaaaaaaaaaaaaaa"), null, "a stale review is REVIEW_PENDING, never ACCEPTED");
  assert.equal(reviewRow3(dir, undefined), null);
  assert.equal(reviewRow3(dir, "05056b1b1b58533a"), "ACCEPTED_WITH_RESIDUALS");
  fs.writeFileSync(path.join(dir, "review.md"), `# review with no module line\n${body}`);
  assert.equal(reviewRow3(dir, "05056b1b1b58533a"), null);
  fs.rmSync(dir, { recursive: true, force: true });
  const blind = fs.readFileSync(path.join(ROOT, "scripts", "blind-test.mjs"), "utf8");
  assert.match(blind, /fs\.rmSync\(path\.join\(passDir, "review\.md"\)/, "blind-test deletes the pass folder's review.md before the seat runs");
});

// ---------------------------------------------------------------------------------------------------- H4
for (const seat of ["luna", "gmed"]) {
  test(`H4: blind ${seat} P2 — the kernel now refuses its gateFor, and its archived geometry fails all three new V11 rows`, async () => {
    const text = fs.readFileSync(path.join(FIX, `blind-p2-${seat}.mjs`), "utf8");
    const mod = await importText(text);
    assert.throws(() => mod.build(), /BAD_ARG: landing gateFor: flight "[^"]+" does not arrive on this deck/);
    const old = await importText(archived(text));
    const parts = old.build();
    const report = await validateParts(old.meta, parts, undefined, opts());
    assert.equal(report.pass, false);
    assert.equal(report.violations[0].v, "V11_FLIGHT_ON_DECK", report.text);
    const ctx = chainContext(old.meta, parts, undefined, opts());
    for (const name of NEW_ROWS) assert.equal(row(ctx, name).length, 1, `${seat}: ${name}`);
    assert.match(row(ctx, "V11_RAIL_COVERAGE")[0].measured, /front rail covers \d+ % of the span/);
    assert.match(row(ctx, "V11_DROP_LADDER")[0].measured, /crosses "shop_awning"/);
  });
}

test("H4: run-4 geometry (owner-accepted) is clean on V6 and every V11 row, and meets ladder.roof.bottom", async () => {
  const mod = await importText(fs.readFileSync(path.join(FIX, "run4-facade.mjs"), "utf8"));
  const parts = mod.build();
  const ctx = chainContext(mod.meta, parts, undefined, opts());
  for (const [name, fn] of BUILDING_RULES.validators) if (/^V11/.test(name)) assert.deepEqual(fn(ctx).violations, [], name);
  const report = await validateParts(mod.meta, parts, undefined, opts());
  // Only V12_LAYOUT keys measured after run 4 (storefront/door/sign/AC/landing span) remain; none is a new row.
  assert.ok(report.violations.every((v) => v.v === "V12_LAYOUT"), report.text);
  assert.ok(!/ladder\.roof\.bottom/.test(report.text), report.text);
});

test("H4: a module built from the template + ONE fireEscape call + the side roof ladder, fed by measured keys, passes the full chain", async () => {
  const mod = await importText(generateBuilding("facade_brick").text);
  const parts = mod.build();
  const L = FACADE.readJson("layout");
  const w = K.assemble.wallPlanes(parts);
  const F = BUILDING_RULES.layoutFrame({ records: parts.map((p) => ({ role: p.role, aabb: p.solid.aabb() })) });
  const levels = F.windowRowBottoms.map((b) => b + L["landing.rowY"].value * w.H);
  const awningTop = Math.max(...parts.filter((p) => p.role === "awning").map((p) => p.solid.aabb().max[1]));
  parts.push(...K.assemble.fireEscape({ wall: parts, centreX: w.streetRight + L["landing.centreX"].value * w.W, span: L["landing.span"].value * w.W,
    depth: 1.4, levels, dropLadder: { bottom: awningTop }, idPrefix: "fe" }));
  const bottom = L["ladder.roof.bottom"].value * w.H;
  const top = F.copingTop - L["ladder.topBelowCoping"].value * w.H;
  parts.push(...K.assemble.ladder({ face: "side", base: [w.streetLeft, bottom, w.front + L["ladder.roof.backFromCorner"].value * w.W],
    height: top - bottom, width: 0.5, idPrefix: "roof" }));
  const report = await validateParts(mod.meta, parts, undefined, opts());
  assert.equal(report.pass, true, report.text);
  assert.equal(report.advisories.filter((a) => a.v === "V11_HANDBUILT").length, 0);
});

test("H4: fireEscape refuses a drop ladder hung past an awning, and a deck too shallow for the flight", async () => {
  const mod = await importText(generateBuilding("facade_brick").text);
  const parts = mod.build();
  const w = K.assemble.wallPlanes(parts);
  const base = { wall: parts, centreX: w.streetRight + 0.627 * w.W, span: 0.577 * w.W, depth: 1.4, levels: [6.6, 10.5], idPrefix: "fe" };
  assert.throws(() => K.assemble.fireEscape({ ...base, dropLadder: { bottom: 0 } }), /BAD_ARG: fireEscape dropLadder\.bottom .* hangs past "shop_awning"/);
  assert.throws(() => K.assemble.fireEscape({ ...base, depth: 0.8, dropLadder: null }), /BAD_ARG: fireEscape depth 0\.800 m cannot hold the flight/);
});

// ---------------------------------------------------------------------------------------------------- C15
test("C15: the roof ladder foot is a measured, evidenced layout key with a V12 rule; MEASURED NUMBERS prints absolute datums", () => {
  const entry = FACADE.readJson("layout")["ladder.roof.bottom"];
  assert.ok(entry && Math.abs(entry.value - 0.216) < 0.01 && entry.unit === "H" && entry.evidence?.px, JSON.stringify(entry));
  assert.ok(BUILDING_RULES.layoutRules["ladder.roof.bottom"]);
  assert.match(BUILDING_RULES.layoutAbsolute("ladder.roof.bottom", entry, { x0: 0, y0: 0, W: 7, H: 16.5, faceZ: 0, wallTop: 16.5, copingTop: 17 }),
    /^y = \+3\.564 m/);
  const F = { x0: 0, y0: 0, W: 7, H: 10, faceZ: 0, wallTop: 10, copingTop: 10.3, windowRowBottoms: [3, 6] };
  assert.equal(BUILDING_RULES.layoutAbsolute("landing.rowY", { value: -0.072, unit: "H" }, F),
    "deck top y = +2.280, +5.280 m (window row bottom y +3.000, +6.000 + value x H), bottom level first");
});

// ---------------------------------------------------------------------------------------------------- item 7
test("item 7: a module throw names the author's own file:line and source", () => {
  const file = path.join(ROOT, "subjects", "x", "module.mjs");
  const source = "line one\n  const d = K.assemble.ladder({\nline three";
  const error = new Error("BAD_ARG: ladder width must be a finite number, got undefined");
  error.stack = `KernelError: ${error.message}\n    at fail (file:///D:/k/assemblies.mjs:72:9)\n    at build (${pathToFileURL(file).href}:2:13)`;
  assert.equal(authorLine(error, file, source), "module.mjs:2:13: const d = K.assemble.ladder({");
  assert.equal(authorLine(new Error("x"), file, source), null);
});

// ---------------------------------------------------------------------------------------------------- item 6
test("item 6: author docs and the facade P2 item carry no gateAt/gateFor; the item is one fireEscape call", () => {
  const readme = fs.readFileSync(path.join(ROOT, "src", "kernel", "README.md"), "utf8");
  const classDoc = fs.readFileSync(path.join(ROOT, "classes", "building.md"), "utf8");
  const p2 = FACADE.readJson("passes").find((p) => p.id === "P2");
  for (const text of [readme, classDoc, p2.item]) assert.doesNotMatch(text, /gateAt|gateFor/);
  assert.equal(p2.item.match(/K\.assemble\.fireEscape\(/g).length, 1);
  assert.ok(p2.item.length < 1500, `P2 item ${p2.item.length} chars`);
});
