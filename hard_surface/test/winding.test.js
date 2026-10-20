// Every prim must be a closed, outward-wound solid. This pins the loft
// cap-winding fix (geom.js FORK-FIX): an inward-wound cap is culled and lets the
// part behind show through — the roof-plate defect seen in out/m0/cap1.png.
//
// M2 widens the vocabulary past convex boxes, so the assertion is split:
//   * SIGNED VOLUME > 0 holds for every closed outward-wound surface whatever
//     its shape or genus, so it is asserted for every prim in PRIM_NAMES;
//   * "no facet normal points at the centroid" is a CONVEX test — a staircase
//     riser and the bore of a `ring` both fail it legitimately — so it is
//     asserted only for PRIM_CONVEX.
import { test } from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";

import { buildPrim, PRIM_NAMES, PRIM_CONVEX, PRIM_GENUS } from "../src/prims.js";
import { validateV1 } from "../src/validate/v1.js";

const DIMS = {
  box: [6, 9.6, 8],
  bevelBox: [2, 0.18, 0.9],
  plate: [6.2, 0.3, 8.2],
  prism: [0.5, 2.4, 0.5],
  wedge: [1.8, 0.4, 0.9],
  tube: [0.24, 3.0, 0.24],
  ring: [0.62, 0.9, 0.62],
  stepStack: [1.2, 0.9, 1.3],
};

const OPTIONS = { stepStack: { steps: 5 }, prism: { sides: 6 }, tube: { sides: 8 }, ring: { sides: 12 } };

const make = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint });

// M5: the side-mounted wheel needs a ring whose bore runs along X. It is the Y
// ring turned by a rotation, so it must still be closed, still genus 1, still
// outward-wound, and still fill its declared box exactly.
test("prim ring with axis x: bore along X, closed, genus 1, outward-wound", () => {
  const dims = [0.12, 0.27, 0.27];
  const geometry = buildPrim("ring", dims, { axis: "x", sides: 12, wall: 0.0486 });

  geometry.computeBoundingBox();
  const size = geometry.boundingBox.getSize(new THREE.Vector3());
  for (const [index, value] of [[0, size.x], [1, size.y], [2, size.z]]) {
    assert.ok(Math.abs(value - dims[index]) < 1e-5, `axis-x ring axis ${index} is ${value}, declared ${dims[index]}`);
  }
  assert.ok(Math.abs(geometry.boundingBox.min.y) < 1e-5, "axis-x ring does not start at y = 0");

  const v1 = validateV1([{ specId: "wheel", prim: "ring", genus: 1, geometry }], make);
  assert.deepEqual(v1.violations, [], v1.violations.map((x) => x.hint).join("\n"));

  const position = geometry.getAttribute("position");
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const cross = new THREE.Vector3();
  let volume = 0;
  for (let i = 0; i < position.count; i += 3) {
    a.fromBufferAttribute(position, i);
    b.fromBufferAttribute(position, i + 1);
    c.fromBufferAttribute(position, i + 2);
    volume += cross.crossVectors(b, c).dot(a) / 6;
  }
  assert.ok(volume > 0, `axis-x ring has signed volume ${volume.toFixed(6)} — the surface is inside-out`);

  // The bore is along X: a slab through the middle of the wheel is hollow, so
  // the y/z extent of the inner wall is smaller than the outer one.
  assert.ok(size.y > 2 * 0.0486, "the bore closed up");
});

for (const name of PRIM_NAMES) {
  test(`prim ${name}: closed, correct genus, outward-wound`, () => {
    const geometry = buildPrim(name, DIMS[name], OPTIONS[name] ?? {});
    const position = geometry.getAttribute("position");

    // Fills its declared box exactly — resolve.js derives contacts from dims.
    geometry.computeBoundingBox();
    const size = geometry.boundingBox.getSize(new THREE.Vector3());
    for (const [axis, value] of [["w", size.x], ["h", size.y], ["d", size.z]]) {
      const index = { w: 0, h: 1, d: 2 }[axis];
      assert.ok(Math.abs(value - DIMS[name][index]) < 1e-5,
        `${name} ${axis} is ${value}, declared ${DIMS[name][index]}`);
    }
    assert.ok(Math.abs(geometry.boundingBox.min.y) < 1e-5, `${name} does not start at y = 0`);

    // Watertight, consistently wound, chi = 2 - 2*genus.
    const v1 = validateV1([{ specId: name, prim: name, genus: PRIM_GENUS[name], geometry }], make);
    assert.deepEqual(v1.violations, [], v1.violations.map((x) => x.hint).join("\n"));

    // Signed volume of the closed surface: positive only when outward-wound.
    const a = new THREE.Vector3();
    const b = new THREE.Vector3();
    const c = new THREE.Vector3();
    const cross = new THREE.Vector3();
    let volume = 0;
    for (let i = 0; i < position.count; i += 3) {
      a.fromBufferAttribute(position, i);
      b.fromBufferAttribute(position, i + 1);
      c.fromBufferAttribute(position, i + 2);
      volume += cross.crossVectors(b, c).dot(a) / 6;
    }
    assert.ok(volume > 0, `${name} has signed volume ${volume.toFixed(6)} — the surface is inside-out`);

    if (!PRIM_CONVEX.includes(name)) return;

    const centre = geometry.boundingBox.getCenter(new THREE.Vector3());
    const n = new THREE.Vector3();
    const m = new THREE.Vector3();
    let inward = 0;
    for (let i = 0; i < position.count; i += 3) {
      a.fromBufferAttribute(position, i);
      b.fromBufferAttribute(position, i + 1);
      c.fromBufferAttribute(position, i + 2);
      n.subVectors(b, a).cross(m.subVectors(c, a));
      if (n.lengthSq() === 0) continue; // degenerate (bevel corner), ignore
      m.addVectors(a, b).add(c).divideScalar(3).sub(centre);
      if (n.dot(m) < 0) inward += 1;
    }
    assert.equal(inward, 0, `${inward} inward-wound triangles in ${name}`);
  });
}
