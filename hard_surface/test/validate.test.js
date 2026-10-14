// M1 — the validators bite.
//
// Every fixture in test/fixtures/broken/ is a real spec, derived from the M0
// massing or the crate, that fails EXACTLY ONE V-code. If a fixture starts
// reporting a second code the validator has drifted, not the fixture.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { validateSpec, DEFAULT_LIMITS } from "../src/validate/index.js";
import { repair } from "../src/validate/repair.js";
import { loadSpec, ROOT, TENEMENT, EXAMPLES } from "./fixtures.mjs";

const BROKEN = path.join(ROOT, "test/fixtures/broken");
const FIXTURES = fs.readdirSync(BROKEN).filter((f) => f.endsWith(".json")).sort();
const PASSING = new Set(["v5-at-floor-pass.json", "v6-socket-overlap-pass.json"]);

const read = (file) => JSON.parse(fs.readFileSync(path.join(BROKEN, file), "utf8"));
const codes = (report) => [...new Set(report.violations.map((v) => v.v))];

test("there are 22 broken-spec fixtures", () => {
  assert.equal(FIXTURES.length, 22);
});

test("the massing and every worked example validate clean", () => {
  for (const file of [TENEMENT, ...EXAMPLES]) {
    const report = validateSpec(loadSpec(file));
    assert.equal(report.violations.length, 0, `${file}: ${report.text}`);
    assert.equal(report.pass, true);
  }
});

for (const file of FIXTURES) {
  const expected = file.split("-")[0].toUpperCase();
  test(`fixture ${file} reports exactly ${PASSING.has(file) ? "no violation" : expected}`, () => {
    const report = validateSpec(read(file));
    if (PASSING.has(file)) {
      assert.equal(report.pass, true, report.text);
      assert.equal(report.violations.length, 0);
      return;
    }
    assert.equal(report.pass, false, `${file} was expected to fail`);
    assert.deepEqual(codes(report), [expected], report.text);
  });
}

test("every violation hint states a move, and the report is at most 8 lines", () => {
  for (const file of FIXTURES) {
    const report = validateSpec(read(file));
    assert.ok(report.text.split("\n").length <= 8, `${file}: ${report.text}`);
    for (const violation of report.violations) {
      assert.ok(typeof violation.hint === "string" && violation.hint.length > 0);
      assert.equal(violation.blocking, true);
    }
  }
});

test("repair closes the 3 cm socket gap", () => {
  const spec = read("v2-gap-small.json");
  const before = validateSpec(spec);
  assert.deepEqual(codes(before), ["V2"]);

  const result = repair(spec, before);
  assert.equal(result.report.pass, true, result.report.text);
  const move = result.applied.find((m) => m.v === "V2");
  assert.equal(move.action, "embed");
  assert.ok(Math.abs(move.gap - 0.03) < 1e-6, `gap was ${move.gap} m`);
  assert.ok(move.to < move.from);
});

test("repair grows a 1 cm rail to MIN_FEAT", () => {
  const spec = read("v5-thin-rail.json");
  const before = validateSpec(spec);
  assert.deepEqual(codes(before), ["V5"]);

  const result = repair(spec, before);
  assert.equal(result.report.pass, true, result.report.text);
  const move = result.applied.find((m) => m.v === "V5");
  assert.equal(move.action, "grow");
  assert.equal(move.from, 0.01);
  assert.equal(move.to, DEFAULT_LIMITS.styleFloor.prop);
  const rail = result.spec.parts.find((p) => p.id === "rail");
  assert.ok(Math.min(...rail.dims) >= DEFAULT_LIMITS.styleFloor.prop);
});

test("repair collapses a sub-pixel repeat to one striped block", () => {
  const result = repair(read("v5-subpixel-repeat.json"), null);
  assert.equal(result.report.pass, true, result.report.text);
  const slats = result.spec.parts.find((p) => p.id === "slats");
  assert.equal(slats.repeat, undefined);
  assert.equal(slats.stripe, true);
});

test("repair deletes a duplicate and keeps the original", () => {
  const result = repair(read("v6-duplicate.json"), null);
  assert.equal(result.report.pass, true, result.report.text);
  assert.ok(result.spec.parts.some((p) => p.id === "chimney_m"));
  assert.ok(!result.spec.parts.some((p) => p.id === "chimney_dup"));
});

test("repair refuses V3, V4, V7 and an embedded V2 — those re-prompt, they never self-heal", () => {
  for (const file of ["v3-orphan.json", "v3-orphan-cluster.json", "v3-chain-unrooted.json",
    "v4-floating-ground.json", "v4-com-outside.json", "v7-door-tall.json", "v7-step-rise.json",
    "v2-embedded-shallow.json"]) {
    const spec = read(file);
    const result = repair(spec, validateSpec(spec));
    assert.equal(result.applied.length, 0, `${file} was repaired: ${JSON.stringify(result.applied)}`);
    assert.equal(result.report.pass, false);
    assert.deepEqual(result.spec, spec, `${file} was mutated`);
  }
});

test("a gap past the repair ceiling is left for the re-prompt", () => {
  const spec = read("v2-gap-large.json");
  const result = repair(spec, validateSpec(spec));
  assert.equal(result.applied.length, 0);
  assert.equal(result.report.pass, false);
});

test("every limits.json number is flagged unratified", () => {
  for (const [key, value] of Object.entries(DEFAULT_LIMITS._ratified)) {
    assert.equal(value, false, `${key} claims to be ratified`);
    assert.ok(Object.hasOwn(DEFAULT_LIMITS, key), `${key} is flagged but absent`);
  }
  for (const key of Object.keys(DEFAULT_LIMITS)) {
    if (key.startsWith("_")) continue;
    assert.ok(Object.hasOwn(DEFAULT_LIMITS._ratified, key), `${key} is not flagged`);
  }
});
