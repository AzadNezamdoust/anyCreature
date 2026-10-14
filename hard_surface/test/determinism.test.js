import test from "node:test";
import assert from "node:assert/strict";

import { compile } from "../src/compile/build.js";
import { SHADE } from "../src/geom.js";
import { specHash } from "../src/spec.js";
import { loadSpec, TENEMENT } from "./fixtures.mjs";

/** Byte compare of a Float32 attribute, not a tolerance compare: the loop's
 *  whole determinism claim is "identical query string => identical pixels". */
function bytes(geometry, name) {
  const attribute = geometry.getAttribute(name);
  assert.ok(attribute, `geometry has no ${name} attribute`);
  return Buffer.from(attribute.array.buffer, attribute.array.byteOffset, attribute.array.byteLength);
}

test("same spec, same seed -> byte-identical position and colour buffers", () => {
  const a = compile(loadSpec(TENEMENT));
  const b = compile(loadSpec(TENEMENT));

  assert.ok(bytes(a.geometry, "position").equals(bytes(b.geometry, "position")), "positions drifted");
  assert.ok(bytes(a.geometry, "color").equals(bytes(b.geometry, "color")), "colours drifted");
  assert.equal(a.solved.triangles, b.solved.triangles);
  assert.deepEqual(a.solved.bounds, b.solved.bounds);
});

test("seed changes nothing while SHADE.jitter is 0", () => {
  const one = compile(loadSpec(TENEMENT));
  const spec2 = loadSpec(TENEMENT);
  spec2.seed = 2;
  const two = compile(spec2);

  // The seed feeds `rng("<seed>:<partId>")`, which paint() consumes ONLY for the
  // per-facet jitter — and jitter is off in the fork (geom.js SHADE.jitter = 0,
  // "random value on top of a flat zone colour reads as dirt, not as form").
  // So the seed must be inert here. If a later change turns jitter on, this
  // assertion flips to "colours differ, positions do not" and must be updated
  // deliberately, not silently.
  assert.equal(SHADE.jitter, 0, "SHADE.jitter changed: revisit this assertion");
  assert.ok(bytes(one.geometry, "position").equals(bytes(two.geometry, "position")), "seed moved geometry");
  assert.ok(bytes(one.geometry, "color").equals(bytes(two.geometry, "color")), "seed changed colour with jitter off");
});

test("specHash is stable and key-order independent", () => {
  const spec = loadSpec(TENEMENT);
  // M2: the subject now carries `facades`, so the reordered twin must too —
  // canonicalJson sorts keys at every depth, it does not invent missing ones.
  const reordered = { facades: spec.facades, parts: spec.parts, palette: spec.palette, seed: spec.seed, subject: spec.subject, schema: spec.schema, class: spec.class, note: spec.note, unit: spec.unit };
  assert.equal(specHash(spec), specHash(reordered));
  const changed = loadSpec(TENEMENT);
  changed.parts[0].dims[0] += 0.1;
  assert.notEqual(specHash(spec), specHash(changed));
});
