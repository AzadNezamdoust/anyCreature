import test from "node:test";
import assert from "node:assert/strict";

import { compile } from "../src/compile/build.js";
import { validateV10 } from "../src/validate/v10.js";
import { DEFAULT_LIMITS } from "../src/validate/index.js";
import { loadSpec, TENEMENT, EXAMPLES } from "./fixtures.mjs";

// M1: the budget/NaN/one-mesh assertions moved into V10 and the numbers moved
// into src/validate/limits.json (still PROVISIONAL, still owner-gated — see
// PLAN.md 8.1). These tests now call the validator so there is one owner of the
// rule and one owner of the number.
const make = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint, blocking: true });

function v10(file) {
  const spec = loadSpec(file);
  const { solved, geometry } = compile(spec);
  const cls = Object.hasOwn(DEFAULT_LIMITS.triBudget, spec.class ?? "") ? spec.class : "prop";
  return {
    solved,
    result: validateV10({ solved, geometryInfo: { geometry }, cls, limits: DEFAULT_LIMITS }, make),
  };
}

test("tenement massing passes V10 inside the provisional building budget", () => {
  const { solved, result } = v10(TENEMENT);
  assert.deepEqual(result.violations, [], JSON.stringify(result.violations));
  assert.ok(solved.triangles > 0 && solved.triangles < DEFAULT_LIMITS.triBudget.building);
});

test("worked examples pass V10 inside the provisional prop budget", () => {
  for (const file of EXAMPLES) {
    const { solved, result } = v10(file);
    assert.deepEqual(result.violations, [], `${file}: ${JSON.stringify(result.violations)}`);
    assert.ok(solved.triangles < DEFAULT_LIMITS.triBudget.prop, `${file}: ${solved.triangles} triangles`);
  }
});

test("compiled geometry carries no NaN or Inf", () => {
  const { geometry } = compile(loadSpec(TENEMENT));
  for (const name of ["position", "color"]) {
    for (const value of geometry.getAttribute(name).array) {
      assert.ok(Number.isFinite(value), `${name} contains ${value}`);
    }
  }
});

test("ground part sits on y = 0", () => {
  const { solved } = compile(loadSpec(TENEMENT));
  assert.ok(Math.abs(solved.bounds.minY) < 1e-6, `minY = ${solved.bounds.minY}`);
});
