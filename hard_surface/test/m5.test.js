// M5 — generality: the two new contacts, the wheel composite, the vehicle rows
// of the V7 table, and the V9 symmetry advisory.
//
// The broken counterpart of each contact lives in test/fixtures/broken/
// (v2-hangs-below-deep.json, v2-embedded-shallow.json) and is asserted by
// validate.test.js like every other fixture; what is asserted here is the
// PASSING side, which is the thing a spec author actually writes.
import { test } from "node:test";
import assert from "node:assert/strict";

import { validateSpec, DEFAULT_LIMITS } from "../src/validate/index.js";
import { compile } from "../src/compile/build.js";
import { expandParts } from "../src/compile/composites.js";
import { CONTACTS } from "../src/compile/resolve.js";
import { isComposite } from "../src/prims.js";
import { loadSpec } from "./fixtures.mjs";

const CART = "dsl/examples/cart.json";

/** A ground slab plus one attached part — the smallest legal host. */
function hostSpec(...parts) {
  return {
    schema: "pg/1",
    subject: "m5_fixture",
    seed: 1,
    class: "prop",
    palette: { deck: "#b9b3a8", iron: "#3b3f4a", hub: "#8d8a84" },
    parts: [
      { id: "pad", prim: "box", dims: [1.2, 0.4, 1.2], ground: true, role: "massing", zone: "deck" },
      ...parts,
    ],
  };
}

/** A minimal vehicle: one chassis on the ground, wheels hung underneath. */
function kart(...wheels) {
  return {
    schema: "pg/1",
    subject: "m5_kart",
    seed: 1,
    class: "vehicle",
    palette: { body: "#c8543f", tyre: "#2b2e33" },
    parts: [
      { id: "chassis", prim: "box", dims: [1.0, 0.3, 1.6], ground: true, role: "chassis", zone: "body" },
      ...wheels,
    ],
  };
}

const wheelBox = (id, u, extra = {}) => ({
  id, prim: "box", dims: [0.12, 0.24, 0.24], role: "wheel", zone: "tyre", ...extra,
  attach: { to: "chassis", face: "-Y", uv: [u, 0.25], contact: "hangs-below", embed: 0 },
});

const v9Advisories = (report) => report.advisories.filter((a) => a.v === "V9");

// --- contacts ----------------------------------------------------------------

test("the contact vocabulary carries hangs-below and embedded", () => {
  assert.deepEqual(CONTACTS, ["flush", "rests-on-top", "socket", "hangs-below", "embedded"]);
});

test("hangs-below: the child's top face lands on the parent's -Y face", () => {
  const spec = hostSpec({
    id: "lamp", prim: "box", dims: [0.1, 0.2, 0.1], role: "lamp", zone: "iron",
    attach: { to: "pad", face: "-Y", uv: [0.5, 0.5], contact: "hangs-below", embed: 0 },
  });
  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);

  const lamp = compile(spec).solved.parts.find((p) => p.id === "lamp");
  assert.ok(Math.abs(lamp.aabb.max[1] - 0) < 1e-6, `lamp top at ${lamp.aabb.max[1]}, expected the pad underside at 0`);
  assert.ok(Math.abs(lamp.aabb.min[1] + 0.2) < 1e-6, `lamp bottom at ${lamp.aabb.min[1]}`);
});

test("hangs-below is only defined on the parent's -Y face", () => {
  const report = validateSpec(hostSpec({
    id: "lamp", prim: "box", dims: [0.1, 0.2, 0.1], role: "lamp", zone: "iron",
    attach: { to: "pad", face: "+Z", uv: [0.5, 0.5], contact: "hangs-below" },
  }));
  assert.equal(report.pass, false);
  assert.ok(report.violations.some((v) => v.v === "V0" && /-Y face/.test(v.hint)), report.text);
});

test("embedded: the child's centre lands on the parent point, embed deeper", () => {
  const spec = hostSpec({
    id: "plug", prim: "box", dims: [0.2, 0.2, 0.2], role: "plug", zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "embedded", embed: 0.05 },
  });
  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);

  const plug = compile(spec).solved.parts.find((p) => p.id === "plug");
  const centreY = (plug.aabb.min[1] + plug.aabb.max[1]) / 2;
  assert.ok(Math.abs(centreY - (0.4 - 0.05)) < 1e-6, `plug centre at ${centreY}, expected 0.35`);
});

test("V6 does not call an embedded child a duplicate of its own parent", () => {
  const report = validateSpec(hostSpec({
    id: "plug", prim: "box", dims: [0.2, 0.2, 0.2], role: "plug", zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "embedded", embed: 0.15 },
  }));
  assert.equal(report.pass, true, report.text);
});

// --- the wheel composite ------------------------------------------------------

test("wheel expands to a ring tyre with its bore along X plus an embedded hub", () => {
  const part = {
    id: "w", prim: "wheel", dims: [0.12, 0.27, 0.27], role: "wheel", zone: "iron",
    zones: { hub: "hub" },
    attach: { to: "pad", face: "-Y", uv: [0.5, 0.5], contact: "hangs-below", embed: 0 },
  };
  assert.equal(isComposite("wheel"), true);

  const { parts, composites } = expandParts([part]);
  assert.deepEqual(parts.map((p) => p.id), ["w.tyre", "w.hub"]);
  assert.equal(parts[0].prim, "ring");
  assert.equal(parts[0].axis, "x");
  assert.deepEqual(parts[0].attach, part.attach);           // the root carries the attach
  assert.equal(parts[1].attach.contact, "embedded");
  assert.ok(Math.abs(parts[1].attach.embed - 0.06) < 1e-9);
  assert.equal(parts[1].zone, "hub");
  assert.equal(composites[0].role, "wheel");

  const report = validateSpec(hostSpec(part));
  assert.equal(report.pass, true, report.text);

  // The hub sits dead centre of the tyre, which is what "embedded" bought.
  const solved = compile(hostSpec(part)).solved;
  const tyre = solved.parts.find((p) => p.id === "w.tyre");
  const hub = solved.parts.find((p) => p.id === "w.hub");
  for (const axis of [0, 1, 2]) {
    const tyreCentre = (tyre.aabb.min[axis] + tyre.aabb.max[axis]) / 2;
    const hubCentre = (hub.aabb.min[axis] + hub.aabb.max[axis]) / 2;
    assert.ok(Math.abs(tyreCentre - hubCentre) < 1e-6, `axis ${axis}: hub off centre by ${hubCentre - tyreCentre}`);
  }
});

test("the cart smoke spec passes V0-V7 + V10 with no V9 advisory", () => {
  const report = validateSpec(loadSpec(CART));
  assert.equal(report.pass, true, report.text);
  assert.deepEqual(v9Advisories(report), []);

  const solved = compile(loadSpec(CART)).solved;
  assert.equal(solved.parts.filter((p) => p.role === "wheel").length, 2);   // mirror pair
});

// --- V7, vehicle rows ----------------------------------------------------------

test("V7 vehicle rules are flagged unratified and skip a spec with no wheels", () => {
  for (const key of ["wheel_diameter_frac_of_length", "ground_clearance", "cab_h_le_total_h"]) {
    assert.ok(Object.hasOwn(DEFAULT_LIMITS.v7, key), `${key} missing from limits.v7`);
  }
  assert.equal(DEFAULT_LIMITS._ratified.v7, false);

  // No role `wheel` anywhere: the vehicle rules cannot fire.
  const report = validateSpec(hostSpec({
    id: "crate", prim: "box", dims: [0.3, 0.3, 0.3], role: "crate", zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  }));
  assert.equal(report.pass, true, report.text);
});

test("V7 flags a wheel outside the radius band and a chassis outside the clearance band", () => {
  const [lo, hi] = DEFAULT_LIMITS.v7.wheel_diameter_frac_of_length;
  const tiny = kart({ ...wheelBox("wheel_l", 0.1), dims: [0.12, 0.1, 0.1] }, { ...wheelBox("wheel_r", 0.9), dims: [0.12, 0.1, 0.1] });
  const small = validateSpec(tiny);
  assert.equal(small.pass, false);
  assert.ok(small.violations.every((v) => v.v === "V7"), small.text);
  assert.ok(small.violations.some((v) => /role wheel/.test(v.hint) && /diameter|radius/.test(v.hint)), small.text);
  assert.ok(lo < hi);

  // Wheels well inside the radius band, but too little of them below the chassis.
  const low = kart({ ...wheelBox("wheel_l", 0.1), dims: [0.12, 0.4, 0.4], attach: { to: "chassis", face: "-Y", uv: [0.1, 0.25], contact: "hangs-below", embed: 0.3 } },
    { ...wheelBox("wheel_r", 0.9), dims: [0.12, 0.4, 0.4], attach: { to: "chassis", face: "-Y", uv: [0.9, 0.25], contact: "hangs-below", embed: 0.3 } });
  const report = validateSpec(low);
  assert.equal(report.pass, false);
  assert.ok(report.violations.some((v) => v.v === "V7" && /ground/.test(v.hint)), report.text);
});

// --- V9 -------------------------------------------------------------------------

test("V9 advises on a lone wheel and never blocks", () => {
  const report = validateSpec(kart(wheelBox("wheel_l", 0.1)));
  assert.equal(report.pass, true, report.text);          // advisory only, PLAN 2

  const advisories = v9Advisories(report);
  assert.equal(advisories.length, 1, JSON.stringify(advisories));
  assert.equal(advisories[0].part, "wheel_l");
  assert.equal(advisories[0].blocking, false);
  assert.ok(/no mirror twin/.test(advisories[0].hint), advisories[0].hint);
});

test("V9 is silent for a mirrored wheel, for a hand-authored pair, and off-class", () => {
  const mirrored = validateSpec(kart(wheelBox("wheel_l", 0.1, { mirror: true })));
  assert.equal(mirrored.pass, true, mirrored.text);
  assert.deepEqual(v9Advisories(mirrored), []);

  const pair = validateSpec(kart(wheelBox("wheel_l", 0.1), wheelBox("wheel_r", 0.9)));
  assert.equal(pair.pass, true, pair.text);
  assert.deepEqual(v9Advisories(pair), []);

  // Same geometry, class `prop`: V9 only speaks for limits.symmetricClasses.
  const prop = validateSpec({ ...kart(wheelBox("wheel_l", 0.1)), class: "prop" });
  assert.deepEqual(v9Advisories(prop), []);
  assert.deepEqual(DEFAULT_LIMITS.symmetricClasses, ["vehicle", "robot"]);
});
