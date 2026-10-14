// V5-9 (vehicles) EVIDENCE HIERARCHY: a layout key gives a knob its START, the class prior its RANGE; READY-call rc_*
// knobs are ranged by knobPriors._readyCall; accuracy-covered layout keys are advisory in the FIT / LOOP gate
// (counts stay enforced). Hermetic: in-process, no files written.
import test from "node:test";
import assert from "node:assert/strict";

import { startKnob, keyedKnob } from "../scripts/knobs.mjs";
import { knobifyCalls, readyCallSpan } from "../scripts/loop.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";

test("V5-9 startKnob: the range is the class prior around the start, not the key's tolerance; the key stays as provenance", () => {
  const sizes = { L: 5, W: 2, H: 2 };
  const k = startKnob({ v: 0.6, key: "bumper.rear.top", prior: { span: 0.1, of: "H" }, sizes });
  assert.deepEqual(k, { v: 0.6, min: 0.4, max: 0.8, key: "bumper.rear.top", unit: "m" });
  const tolRange = keyedKnob({ v: 0.6, key: "bumper.rear.top", entry: { value: 0.3, tol: 0.045 }, toM: (f) => f * 2 });
  assert.ok(tolRange.max - tolRange.min < k.max - k.min, "the old key band was narrower than the prior");
  assert.equal(startKnob({ v: 4.8, key: "x", prior: { locked: "anchor" }, sizes }).locked, "anchor");
});

test("V5-9 templates: every keyed knob of the pickup and the bus is ranged by its class prior", () => {
  for (const id of ["pickup", "school_bus"]) {
    const S = loadSubject(id);
    const P = S.cls.knobPriors;
    const text = generateForSubject(id).text;
    const rows = [...text.matchAll(/\n\s*(\w+):\s*\{ v: (-?[\d.]+), min: (-?[\d.]+), max: (-?[\d.]+), key: "([^"]+)"/g)];
    assert.ok(rows.length >= 8, `${id}: ${rows.length} keyed knobs`);
    for (const [, name, v, min, max] of rows) {
      const p = P[name] ?? P._keyed;
      const size = p.of === "m" ? 1 : { L: 4.8, W: Number(/\n\s*W:\s*\{ v: ([\d.]+)/.exec(text)[1]), H: Number(/\n\s*H:\s*\{ v: ([\d.]+)/.exec(text)[1]) }[p.of];
      const half = p.span * (p.of === "L" ? Number(/\n\s*L:\s*\{ v: ([\d.]+)/.exec(text)[1]) : size);
      assert.ok(Number(max) - Number(v) <= half + 2e-4 && Number(v) - Number(min) <= half + 2e-4, `${id} ${name}`);
      assert.ok(Number(max) - Number(min) > 0, `${id} ${name} is free`);
    }
  }
});

test("V5-9 READY-call knobs: span from knobPriors._readyCall, floored at 0.001; a class without it keeps 0.02 x anchor", () => {
  const reg = { anchor: { ref: 5, L: 5 } };
  assert.equal(readyCallSpan({ knobPriors: { _readyCall: { span: 0.04, of: "L" } } }, reg), 0.2);
  assert.equal(readyCallSpan({ knobPriors: {} }, reg), 0.1);
  const offered = {};
  knobifyCalls([{ what: "lamp", call: "K.assemble.lamp({ diameter: 0.15 })" }], { offered, span: 0.2, floor: 0.001 });
  assert.deepEqual(offered.rc_lamp1, { v: 0.15, min: 0.001, max: 0.35, what: "lamp" });
});

test("V5-9 advisoryLayout: measured non-count keys become advisory, counts / unverified / _profile stay", () => {
  const layout = {
    "bumper.rear.top": { value: 0.3, tol: 0.045, unit: "H" },
    "window.row.count": { value: 7, tol: 0, unit: "count" },
    "grille.slots": { value: 2, tol: 0, unit: "count" },
    "hood.top": { unverified: true, reason: "x" },
    _profile: { variant: "bus" },
  };
  const g = RULES.advisoryLayout(layout);
  assert.deepEqual(Object.keys(g._advisory), ["bumper.rear.top"]);
  assert.ok(!("bumper.rear.top" in g));
  for (const k of ["window.row.count", "grille.slots", "hood.top", "_profile"]) assert.ok(k in g, k);
  assert.equal(RULES.advisoryLayout({ "grille.slots": { value: 2 } })._advisory, undefined);
  assert.ok(RULES.validators.some(([n]) => n === "VEH_LAYOUT_ADVISORY"));
});
