// M2 — composite prims are spec fragments, not geometry: they must expand into
// ordinary parts that the whole validator chain accepts, and their derived
// dimensions must be the ones the params say.
import { test } from "node:test";
import assert from "node:assert/strict";

import { compile } from "../src/compile/build.js";
import { validateSpec } from "../src/validate/index.js";
import { evaluateExpression, expandParts, compositeDims } from "../src/compile/composites.js";
import { COMPOSITE_NAMES, isComposite, loadComposite, COMPOSITE_SCHEMA } from "../src/prims.js";

/** A ground slab plus one composite on top of it — the smallest legal host. */
function hostSpec(part) {
  return {
    schema: "pg/1",
    subject: "composite_fixture",
    seed: 1,
    class: "prop",
    palette: { deck: "#b9b3a8", iron: "#3b3f4a", louvre: "#22252c" },
    parts: [
      { id: "pad", prim: "box", dims: [3.0, 0.3, 2.0], ground: true, role: "massing", zone: "deck" },
      part,
    ],
  };
}

test("every library fragment declares the composite schema and at least one part", () => {
  assert.ok(COMPOSITE_NAMES.length >= 5, `only ${COMPOSITE_NAMES.length} composites`);
  for (const name of COMPOSITE_NAMES) {
    const fragment = loadComposite(name);
    assert.equal(fragment.schema, COMPOSITE_SCHEMA, name);
    assert.ok(Array.isArray(fragment.parts) && fragment.parts.length >= 1, name);
    assert.equal(fragment.parts[0].attach, undefined, `${name}: the root sub-part must not carry its own attach`);
  }
});

test("expression evaluator: numbers, params, precedence, parentheses", () => {
  const params = { w: 2.4, n: 6, t: 0.06 };
  assert.equal(evaluateExpression("$w", params), 2.4);
  assert.equal(evaluateExpression("$w - 2 * $t", params), 2.4 - 0.12);
  assert.equal(evaluateExpression("$w / ($n - 1)", params), 0.48);
  assert.equal(evaluateExpression("-$t + 1", params), 0.94);
  assert.throws(() => evaluateExpression("$nope", params), /unknown param/);
});

test("railing expands to four sub-parts, root carries the composite attach", () => {
  const part = {
    id: "rail",
    prim: "railing",
    dims: [2.4, 0.95, 0.06],
    role: "railing",
    zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  };
  const { parts, composites } = expandParts([part]);
  assert.deepEqual(parts.map((p) => p.id), ["rail.bot", "rail.infill", "rail.post", "rail.top"]);
  assert.deepEqual(parts[0].attach, part.attach);
  assert.equal(parts[1].attach.to, "rail.bot");
  assert.equal(parts[2].repeat.count, 6);
  assert.ok(Math.abs(parts[2].repeat.pitch - (2.4 - 0.06) / 5) < 1e-9);
  assert.equal(composites.length, 1);
  assert.equal(composites[0].role, "railing");

  // Heights add back up to the composite height.
  const total = parts[0].dims[1] + parts[1].dims[1] + parts[3].dims[1];
  assert.ok(Math.abs(total - 0.95) < 1e-9, `sub-part heights sum to ${total}`);
});

test("railing on a pad: every sub-part passes V1-V7 + V10", () => {
  const report = validateSpec(hostSpec({
    id: "rail",
    prim: "railing",
    dims: [2.4, 0.95, 0.06],
    role: "railing",
    zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  }));
  assert.equal(report.pass, true, report.text);
});

test("stairFlight derives its dims: top step height = steps * rise", () => {
  const params = { steps: 5, rise: 0.18, run: 0.26, width: 0.9 };
  const part = {
    id: "flight",
    prim: "stairFlight",
    dims: [0.9, 0.9, 1.3],
    role: "stair",
    zone: "deck",
    params,
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  };
  assert.deepEqual(compositeDims(part), [0.9, 5 * 0.18, 5 * 0.26]);

  const { solved } = compile(hostSpec(part));
  const flight = solved.parts.find((p) => p.id === "flight.flight");
  assert.equal(flight.dims[1], 5 * 0.18);
  // The pad top is at y = 0.3, so the flight's highest vertex is pad + rise*steps.
  assert.ok(Math.abs(flight.aabb.max[1] - (0.3 + 5 * 0.18)) < 1e-6, `top at ${flight.aabb.max[1]}`);

  const report = validateSpec(hostSpec(part));
  assert.equal(report.pass, true, report.text);
});

test("stairFlight rejects authored dims that contradict its params", () => {
  const report = validateSpec(hostSpec({
    id: "flight",
    prim: "stairFlight",
    dims: [0.9, 1.0, 1.3],
    role: "stair",
    zone: "deck",
    params: { steps: 5, rise: 0.18, run: 0.26, width: 0.9 },
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  }));
  assert.equal(report.pass, false);
  assert.ok(report.violations.some((v) => v.v === "V0" && /derives its dims/.test(v.hint)), report.text);
});

test("landing nests railing composites and still passes the chain", () => {
  const report = validateSpec(hostSpec({
    id: "land",
    prim: "landing",
    dims: [1.6, 1.1, 1.2],
    role: "landing",
    zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  }));
  assert.equal(report.pass, true, report.text);
});

test("pipe and vent expand and pass; vent honours its zones map", () => {
  const pipe = validateSpec(hostSpec({
    id: "pipe", prim: "pipe", dims: [0.34, 1.4, 0.34], role: "pipe", zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.25, 0.5], contact: "rests-on-top" },
  }));
  assert.equal(pipe.pass, true, pipe.text);

  const ventPart = {
    id: "vent", prim: "vent", dims: [1.0, 0.9, 0.7], role: "vent", zone: "deck",
    zones: { louvre: "louvre" },
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  };
  const { parts } = expandParts([ventPart]);
  assert.equal(parts.find((p) => p.id === "vent.louvre").zone, "louvre");
  const report = validateSpec(hostSpec(ventPart));
  assert.equal(report.pass, true, report.text);
});

test("a composite name is not a prim name", () => {
  for (const name of COMPOSITE_NAMES) assert.equal(isComposite(name), true);
  assert.equal(isComposite("box"), false);
  assert.equal(isComposite("constructor"), false);
});
