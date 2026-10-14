// The V2 chain, pinned by four modules that each break exactly one row plus the
// smoke module that breaks none. A fixture asserts its OWN code FIRST: the
// chain stops at the first failing validator, so "first violation" is also
// "the only class of violation reached".
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, LAYOUT_KEYS, DEFAULT_LIMITS } from "../src/validate/kernel-chain.mjs";
import * as BUILDING_RULES from "../src/validate/rules/building.mjs";
import { partsToGeometry, frontRotationDeg } from "../src/kernel/toThree.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");

await K.init();

async function validateModule(relative) {
  const mod = await import(pathToFileURL(path.join(ROOT, relative)).href);
  return { report: await validateParts(mod.meta, mod.build()), mod };
}

/** Everything except `timings`; `timings` is wall-clock and cannot be pinned. */
function deterministicPart(report) {
  const { timings, ...rest } = report;
  return rest;
}

const BROKEN = [
  ["test/fixtures/kernel/gap.mjs", ["V2_GAP"]],
  ["test/fixtures/kernel/floating.mjs", ["V3_FLOAT", "V3_UNSUPPORTED"]],
  ["test/fixtures/kernel/thin-bar.mjs", ["V5"]],
  ["test/fixtures/kernel/clash.mjs", ["V6_CLASH"]],
  // WF-LOOP r1 — one fixture per new row, each of them healthy everywhere else
  // so the chain reaches the row it is meant to pin and stops there.
  ["test/fixtures/kernel/undeclared-clash.mjs", ["V6_CLASH_UNDECLARED"]],   // row 6
  ["test/fixtures/kernel/bad-role.mjs", ["V7_ROLE"]],                       // row 5
  ["test/fixtures/kernel/step-rise.mjs", ["V7"]],                           // row 5
  ["test/fixtures/kernel/stair-rail.mjs", ["V7_STAIR_RAIL"]],               // row 5
  ["test/fixtures/kernel/bearing.mjs", ["V11_BEARING"]],                    // row 2
  ["test/fixtures/kernel/landing-gap.mjs", ["V11_LANDING_GAP"]],            // row 7
  ["test/fixtures/kernel/ladder-access.mjs", ["V11_LADDER_ACCESS"]],        // row 8
  ["test/fixtures/kernel/deck-gap.mjs", ["V11_DECK_GAP"]],                  // row 9
  ["test/fixtures/kernel/landing-guard.mjs", ["V11_LANDING_GUARD"]],        // v3-backlog item 3
  ["test/fixtures/kernel/census.mjs", ["V12_CENSUS"]],                      // row 4
];

for (const [file, codes] of BROKEN) {
  test(`${path.basename(file)} FAILs on ${codes.join("/")} first`, async () => {
    const { report } = await validateModule(file);
    assert.equal(report.pass, false, `expected ${file} to FAIL; got:\n${report.text}`);
    assert.ok(report.violations.length > 0, "a failing report must carry violations");
    assert.ok(codes.includes(report.violations[0].v),
      `first violation is ${report.violations[0].v}, expected one of ${codes.join("/")}\n${report.text}`);
    // Every violation carries the full repair-seat shape.
    for (const item of report.violations) {
      for (const key of ["v", "part", "measured", "limit", "hint", "blocking"]) {
        assert.ok(Object.hasOwn(item, key), `violation is missing "${key}"`);
      }
    }
    assert.ok(report.text.split("\n").length <= 8, "report text must be <= 8 lines");
  });
}

test("V11_LANDING_GUARD names the open front and both exposed ends, not the wall edge; guarding them clears it", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/landing-guard.mjs")).href);
  const bare = await validateParts(mod.meta, mod.build());
  const row = bare.violations.find((v) => v.v === "V11_LANDING_GUARD");
  assert.ok(row, bare.text);
  for (const edge of ["front", "street-right end", "street-left end"]) assert.match(row.measured, new RegExp(`${edge} open`));
  assert.doesNotMatch(row.measured, /back open/, "the edge on the wall needs no guard");
  const guarded = await validateParts(mod.meta, mod.build({ guarded: true }));
  assert.equal(guarded.pass, true, guarded.text);
});

test("the smoke module PASSes the whole chain", async () => {
  const { report } = await validateModule("test/fixtures/kernel/smoke.mjs");
  assert.equal(report.pass, true, report.text);
  assert.deepEqual(report.violations, []);
  assert.equal(report.text, "PASS: V0-V7 + V10 clean.");
  assert.ok(report.measurements.tris > 0 && report.measurements.tris <= 3000,
    `tris ${report.measurements.tris} outside 1..3000`);
  assert.equal(report.measurements.parts, 3);
});

test("the step-rise fixture fails on the PITCH between treads, not a tread height", async () => {
  const { report } = await validateModule("test/fixtures/kernel/step-rise.mjs");
  assert.match(report.violations[0].measured, /^rise 0\.250 m$/);
  assert.equal(report.violations[0].limit, "0.14..0.2 m");   // limits.v7.step_rise, unchanged
});

test("V12 stands down when nothing supplies a census", async () => {
  // The census fixture carries its count in `meta.census`; strip it and the row
  // has nothing to measure, which is what the S1 smoke relies on.
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/census.mjs")).href);
  const { census, ...withoutCensus } = mod.meta;
  const report = await validateParts(withoutCensus, mod.build());
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.census, "skipped");
});

test("V12 reads a census handed in by the caller", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/census.mjs")).href);
  const { census, ...withoutCensus } = mod.meta;
  const report = await validateParts(withoutCensus, mod.build(), undefined, { census: { windows: 2 } });
  assert.equal(report.pass, false);
  assert.equal(report.violations[0].v, "V12_CENSUS");
  assert.equal(report.measurements.census, "applied");
});

test("meta.census === false turns V12 off even with a census in hand", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/census.mjs")).href);
  const report = await validateParts({ ...mod.meta, census: false }, mod.build(), undefined, { census: { windows: 2 } });
  assert.equal(report.pass, true, report.text);
});

// ---------------------------------------------------------------------------
// WF-LOOP r2 row B6 — V12_LAYOUT, one fixture per key class. Each fixture is
// healthy everywhere else, so the chain reaches the layout row and stops on the
// ONE key the fixture breaks; the code is V12_LAYOUT for every key (one row,
// keys inside it, exactly like V12_CENSUS), so the key is asserted too.
// ---------------------------------------------------------------------------
const LAYOUT_BROKEN = [
  ["test/fixtures/kernel/layout-window.mjs", "window.centreX"],
  ["test/fixtures/kernel/layout-frame.mjs", "frame.proud"],
  ["test/fixtures/kernel/layout-cornice.mjs", "cornice.projection"],
  ["test/fixtures/kernel/layout-landing.mjs", "landing.depth"],
  ["test/fixtures/kernel/layout-ladder.mjs", "ladder.topBelowCoping"],
  // r3 row C1.3 — the roof ladder's MOUNTING PLANE, the gap run 3 could not see
  ["test/fixtures/kernel/layout-ladder-face.mjs", "ladder.roof.face"],
];

for (const [file, key] of LAYOUT_BROKEN) {
  test(`${path.basename(file)} FAILs on V12_LAYOUT "${key}" first`, async () => {
    const { report } = await validateModule(file);
    assert.equal(report.pass, false, `expected ${file} to FAIL; got:\n${report.text}`);
    const first = report.violations[0];
    assert.equal(first.v, "V12_LAYOUT", `first violation is ${first.v}\n${report.text}`);
    assert.ok(first.measured.startsWith(`${key} `),
      `first violation measures "${first.measured}", expected the key "${key}"\n${report.text}`);
    assert.ok(first.limit.length > 0 && first.hint.includes(key), "the fail text must name the key and its band");
    for (const key2 of ["v", "part", "measured", "limit", "hint", "blocking"]) {
      assert.ok(Object.hasOwn(first, key2), `violation is missing "${key2}"`);
    }
    assert.ok(report.text.split("\n").length <= 8, "report text must be <= 8 lines");
  });
}

test("V12_LAYOUT stands down when nothing supplies a layout", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/layout-window.mjs")).href);
  const { layout, ...withoutLayout } = mod.meta;
  const report = await validateParts(withoutLayout, mod.build());
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.layout, "skipped");
});

test("V12_LAYOUT reads a layout handed in by the caller", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/layout-window.mjs")).href);
  const { layout, ...withoutLayout } = mod.meta;
  const report = await validateParts(withoutLayout, mod.build(), undefined, { layout });
  assert.equal(report.pass, false);
  assert.equal(report.violations[0].v, "V12_LAYOUT");
  assert.equal(report.measurements.layout, "applied");
});

test("meta.layout === false turns V12_LAYOUT off even with a layout in hand", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/layout-window.mjs")).href);
  const report = await validateParts({ ...mod.meta, layout: false }, mod.build(), undefined, { layout: mod.meta.layout });
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.layout, "skipped");
});

test("a key whose role is not built yet stands down (the row stages itself)", async () => {
  // The window fixture builds no cornice, landing or ladder, so those keys are
  // not measured at all — that is how P0 survives a layout full of P1/P2 keys.
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/layout-window.mjs")).href);
  const { layout, ...withoutLayout } = mod.meta;
  const report = await validateParts(withoutLayout, mod.build(), undefined, {
    layout: {
      "cornice.projection": { max: 0.001, unit: "W" },
      "landing.depth": { value: 0.15, unit: "W" },
      "ladder.topBelowCoping": { min: 0, max: 0.02, unit: "H" },
    },
  });
  assert.equal(report.pass, true, report.text);
});

test("the roof ladder built on the SIDE wall, set back behind the front plane, passes", async () => {
  const { report } = await validateModule("test/fixtures/kernel/layout-ladder-side.mjs");
  assert.equal(report.pass, true, report.text);
});

// r3 row C1.3 — the subject's layout is now MEASURED (scripts/measure-target.mjs),
// so its tolerances are feature-relative and the smoke module (a 8x11 m wall with
// one arched door) no longer accidentally satisfies them. What must still hold is
// that the row is STAGED and BOUNDED: it may only speak about roles the module
// actually builds, and it may never enforce an `unverified` key.
test("the subject's frozen layout only measures roles the module actually builds", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/smoke.mjs")).href);
  const layout = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects/facade_brick/layout.json"), "utf8"));
  const parts = mod.build();
  const roles = new Set(parts.map((p) => p.role));
  const report = await validateParts(mod.meta, parts, undefined, { layout });
  for (const v of report.violations) {
    assert.equal(v.v, "V12_LAYOUT", `the smoke module broke a non-layout row: ${report.text}`);
    const key = v.measured.split(" ")[0];
    assert.ok(LAYOUT_KEYS.includes(key), `V12_LAYOUT fired on an unknown key "${key}"`);
    assert.ok(layout[key] && layout[key].unverified !== true,
      `V12_LAYOUT enforced "${key}", which layout.json marks unverified`);
  }
  // "window" is not among the smoke's roles, so no window key may be reported at all
  assert.ok(!roles.has("window"));
  const spoken = [...report.violations, ...report.advisories]
    .filter((x) => x.v === "V12_LAYOUT").map((x) => x.measured.split(" ")[0]);
  assert.ok(spoken.every((k) => !k.startsWith("window.")),
    `V12_LAYOUT spoke about a window key with no window built: ${spoken.join(", ")}`);
});

test("an unverified layout key is reported as an advisory and never enforced", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/layout-window.mjs")).href);
  const { layout, ...withoutLayout } = mod.meta;
  const report = await validateParts(withoutLayout, mod.build(), undefined, {
    layout: { "window.centreX": { values: [0.20], unit: "W", tol: 0.02, unverified: true, reason: "fixture" } },
  });
  assert.equal(report.pass, true, report.text);
  const row = report.advisories.find((a) => a.v === "V12_LAYOUT");
  assert.ok(row, "an unverified key must still be REPORTED");
  assert.match(row.measured, /^window\.centreX UNVERIFIED$/);
  assert.equal(row.blocking, false);
});

test("every key in the subject's layout.json is one V12_LAYOUT can measure", () => {
  const layout = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects/facade_brick/layout.json"), "utf8"));
  const keys = Object.keys(layout).filter((k) => !k.startsWith("_"));
  assert.ok(keys.length > 0, "layout.json carries no keys");
  for (const key of keys) {
    // r3 C1.2 added two SCREEN-SPACE keys (iron.frontShare, sideOverFront) that
    // scripts/likeness.mjs reads off pixels; V12 measures geometry and cannot see
    // them, so they declare their reader instead of pretending to be a V12 row.
    if (layout[key].measuredBy === "likeness") continue;
    assert.ok(LAYOUT_KEYS.includes(key), `layout.json key "${key}" is measured by no rule in kernel-chain.mjs`);
  }
});

test("every key the measurement writes carries evidence or a reason", () => {
  for (const file of ["subjects/facade_brick/layout.json", "subjects/facade_brick/layout.measured.json"]) {
    const layout = JSON.parse(fs.readFileSync(path.join(ROOT, file), "utf8"));
    for (const [key, entry] of Object.entries(layout)) {
      if (key.startsWith("_")) continue;
      if (entry.unverified === true) {
        assert.ok(typeof entry.reason === "string" && entry.reason.length > 20,
          `${file} "${key}" is unverified with no reason`);
        continue;
      }
      assert.ok(entry.evidence && entry.evidence.scan && entry.evidence.px,
        `${file} "${key}" carries a number with no evidence — the r3 rule this file exists to enforce`);
    }
  }
});

test("the frozen census stages every count onto one of the three passes", () => {
  const census = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects/facade_brick/census.json"), "utf8"));
  const passes = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects/facade_brick/passes.json"), "utf8"));
  assert.deepEqual(passes.map((p) => p.id), ["P0", "P1", "P2"]);
  for (const [key, value] of Object.entries(census)) {
    if (key.startsWith("_")) continue;
    assert.equal(typeof value, "number", `census key "${key}" is not a count`);
    const stage = census._pass[key];
    assert.ok(Number.isInteger(stage) && stage >= 0 && stage < passes.length,
      `census._pass["${key}"] is ${stage}, outside the ${passes.length} passes`);
  }
});

test("validating twice gives byte-identical report JSON", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/smoke.mjs")).href);
  const first = await validateParts(mod.meta, mod.build());
  const second = await validateParts(mod.meta, mod.build());
  assert.equal(
    JSON.stringify(deterministicPart(first)),
    JSON.stringify(deterministicPart(second)),
    "the same module text validated twice produced two different reports",
  );
});

test("a failing module's report is also deterministic", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/clash.mjs")).href);
  const first = await validateParts(mod.meta, mod.build());
  const second = await validateParts(mod.meta, mod.build());
  assert.equal(JSON.stringify(deterministicPart(first)), JSON.stringify(deterministicPart(second)));
});

test("timings carry one entry per validator that ran", async () => {
  const { report } = await validateModule("test/fixtures/kernel/smoke.mjs");
  for (const name of ["V1", "V5", "V2", "V3", "V6", "V4", "V7",
    "V11_BEARING", "V11_LANDING_GAP", "V11_LADDER_ACCESS", "V11_DECK_GAP", "V11_LANDING_GUARD", "V12", "V12_LAYOUT", "V10", "total"]) {
    assert.equal(typeof report.timings[name], "number", `no timing for ${name}`);
  }
});

// r1 row 1 — the FRONT contract. The rotation the renderer applies must be the
// quarter turn that carries the declared face onto +X, and it must leave the
// author frame (the one the validators measure in) alone.
test("frontRotationDeg maps the declared front axis onto +X", () => {
  assert.equal(frontRotationDeg("-Z"), -90);      // the contract default
  assert.equal(frontRotationDeg(), -90);          // no declaration = the default
  assert.equal(frontRotationDeg("+Z"), 90);
  assert.equal(frontRotationDeg("+X"), 0);
  assert.equal(frontRotationDeg("-X"), 180);
  assert.equal(frontRotationDeg("sideways"), -90);
});

test("the render rotation turns the -Z face onto +X and leaves the parts alone", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/smoke.mjs")).href);
  const parts = mod.build();
  const author = partsToGeometry(parts, mod.meta.palette, 1);
  const rendered = partsToGeometry(parts, mod.meta.palette, 1, { frontRotationDeg: frontRotationDeg(mod.meta.front) });

  // The smoke's populated face is -Z: its depth (0.35 m wall + the bar standing
  // off it) is on z in the author frame and on x after the turn.
  assert.ok(author.bounds.w > author.bounds.d, "author frame: the facade runs along x");
  assert.ok(rendered.bounds.d > rendered.bounds.w, "render frame: the facade runs along z");
  assert.equal(rendered.bounds.h, author.bounds.h, "a Y turn may not change the height");
  assert.equal(rendered.frontRotationDeg, -90);
  assert.equal(author.frontRotationDeg, 0, "no rotation unless one is asked for");
  assert.equal(rendered.solved.triangles, author.solved.triangles);

  // Exact quarter turn: no floating-point skew left on the axis-aligned boxes.
  assert.equal(rendered.bounds.w, author.bounds.d);
  assert.equal(rendered.bounds.d, author.bounds.w);
});

// ---------------------------------------------------------------------------
// WORKFLOW-V3 §3 — harness-inferred contact. A module that declares NO touches
// and is assembled flush (plus one member seated 1 % into the brick) passes
// V2/V3/V6; a 10 % undeclared penetration is still a V6 clash.
// ---------------------------------------------------------------------------
// Dyadic numbers on purpose: the flush face must be EXACTLY coplanar in binary
// floating point, or the "flush" bar floats 1e-17 m clear and is its own lump.
const WALL_T = 0.5;
const BAR = 0.125;
const barAt = (x, seat) => K.box([BAR, 2.5, BAR]).at([x, 0, -WALL_T / 2 - BAR / 2 + seat]);
const noTouchesMeta = { class: "building", seed: 1, census: false, palette: { brick: "#b5412f", iron: "#2b2e33" } };
const noTouchesParts = (seat) => [
  { id: "wall", solid: K.box([4, 3, WALL_T]), zone: "brick", role: "massing" },
  { id: "bar_flush", solid: barAt(1.25, 0), zone: "iron", role: "baluster" },         // surface distance 0
  { id: "bar_seated", solid: barAt(-1.25, seat), zone: "iron", role: "baluster" },    // seat / BAR of its depth
];

test("inferred contact: a flush assembly with NO touches at all passes V2/V3/V6", async () => {
  const parts = noTouchesParts(BAR * 0.01);                                         // 1 % of the bar
  assert.ok(parts.every((p) => p.touches === undefined), "the fixture must declare no touches");
  const report = await validateParts(noTouchesMeta, parts);
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.inferredPairs, 2, "both bars are in contact with the wall, inferred");
  assert.ok(report.timings.V2 >= 0 && report.timings.V3 >= 0 && report.timings.V6 >= 0);
  assert.deepEqual(report.measurements.perPart.map((p) => p.touches), [[], [], []], "declared touches stay declared-only");
});

test("inferred contact is what passes it: with inferredContactFrac 0 the 1 % seat is an undeclared clash", async () => {
  const report = await validateParts(noTouchesMeta, noTouchesParts(BAR * 0.01), { ...DEFAULT_LIMITS, inferredContactFrac: 0 });
  assert.equal(report.pass, false);
  assert.equal(report.violations[0].v, "V6_CLASH_UNDECLARED", report.text);
});

test("a 10 % undeclared penetration still fails V6_CLASH_UNDECLARED", async () => {
  const report = await validateParts(noTouchesMeta, noTouchesParts(BAR * 0.1));     // 10 % of the bar
  assert.equal(report.pass, false, report.text);
  assert.equal(report.violations[0].v, "V6_CLASH_UNDECLARED", report.text);
  assert.match(report.violations[0].measured, /\(10\.0%\)$/);
});

// ---------------------------------------------------------------------------
// WORKFLOW-V3 §7.5 — the class prior arrives through options; no prior = the
// fallback class, byte-identical.
// ---------------------------------------------------------------------------
const BUILDING = JSON.parse(fs.readFileSync(path.join(ROOT, "classes/building.json"), "utf8"));

test("an explicit building prior gives the same report as the fallback", async () => {
  for (const file of ["test/fixtures/kernel/smoke.mjs", "test/fixtures/kernel/census.mjs", "test/fixtures/kernel/step-rise.mjs", "test/fixtures/kernel/layout-window.mjs"]) {
    const mod = await import(pathToFileURL(path.join(ROOT, file)).href);
    const fallback = await validateParts(mod.meta, mod.build());
    const explicit = await validateParts(mod.meta, mod.build(), undefined, { cls: BUILDING, rules: BUILDING_RULES });
    assert.equal(JSON.stringify(deterministicPart(explicit)), JSON.stringify(deterministicPart(fallback)), file);
  }
});

test("a class prior without its rules module is refused, not silently half-applied", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/smoke.mjs")).href);
  await assert.rejects(validateParts(mod.meta, mod.build(), undefined, { cls: BUILDING }), /options\.rules/);
});

test("the closed role table comes from the class prior", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/smoke.mjs")).href);
  const cls = { ...BUILDING, roles: BUILDING.roles.filter((r) => r !== "baluster") };
  const report = await validateParts(mod.meta, mod.build(), undefined, { cls, rules: BUILDING_RULES });
  assert.equal(report.violations[0].v, "V7_ROLE", report.text);
  assert.equal(report.violations[0].part, "bar_0");
});

test("class rows come from the rules module: no validators = no step-rise row", async () => {
  const mod = await import(pathToFileURL(path.join(ROOT, "test/fixtures/kernel/step-rise.mjs")).href);
  const report = await validateParts(mod.meta, mod.build(), undefined, { cls: BUILDING, rules: { layoutRules: {}, validators: [] } });
  assert.equal(report.pass, true, report.text);
  assert.equal(report.timings.V11_BEARING, undefined, "a class without V11 rows runs none");
});

// WF-V3 blind Gemini pickup P1 — the V3_FLOAT row names EVERY lump by its parts
// (largest first) and the closest gap between the two largest, piece to piece.
test("V3_FLOAT names both pieces of a cut-split part and the gap across the cut", async () => {
  const { report } = await validateModule("test/fixtures/kernel/cut-split.mjs");
  assert.equal(report.violations[0]?.v, "V3_FLOAT", report.text);
  const row = report.violations[0];
  assert.equal(row.measured, "2 disconnected lumps");
  assert.match(row.hint, /^the model splits into 2 pieces: \[slab, post_left\] and \[slab, post_right\]; closest gap 100 mm between slab and slab/, row.hint);
  assert.match(row.hint, /slab is cut apart — rejoin them/);
  assert.ok(report.text.split("\n").length <= 8);
});
