// Oriented-box maths shared by V2-V6.
//
// DEVIATION (M1): the brief's file list does not name this module; it exists so
// V2..V6 can share one box model without importing index.js (which imports
// them). Nothing here is a validator — it is pure geometry.
//
// MVP-STUB: every M0 prim (box / bevelBox / plate) is treated as its local
// bounding box [-w/2,w/2] x [0,h] x [-d/2,d/2]. The bevel of a bevelBox and the
// chamfer of a plate are inside that box, so contact/overlap numbers are
// optimistic by at most `bevel` at a corner. Exact prim SDF lands with the
// non-box vocabulary in M2.
import * as THREE from "three";

import { FACE_FRAMES, FACE_NAMES } from "../compile/resolve.js";

/** World OBB of a solved part. Matrices out of resolve.js are rigid. */
export function partBox(part) {
  const m = Array.isArray(part.matrix) ? new THREE.Matrix4().fromArray(part.matrix) : part.matrix;
  const half = new THREE.Vector3(part.dims[0] / 2, part.dims[1] / 2, part.dims[2] / 2);
  const axes = [0, 1, 2].map((i) => new THREE.Vector3().setFromMatrixColumn(m, i).normalize());
  const centre = new THREE.Vector3(0, half.y, 0).applyMatrix4(m);   // prims.js: y runs 0..h
  return { centre, axes, half, id: part.id };
}

/** Half-width of a box's shadow on a unit direction. Exact for a box. */
export function projRadius(box, direction) {
  return Math.abs(direction.dot(box.axes[0])) * box.half.x
    + Math.abs(direction.dot(box.axes[1])) * box.half.y
    + Math.abs(direction.dot(box.axes[2])) * box.half.z;
}

/** World point -> box-local coordinates. */
export function toLocal(box, p) {
  const d = p.clone().sub(box.centre);
  return new THREE.Vector3(d.dot(box.axes[0]), d.dot(box.axes[1]), d.dot(box.axes[2]));
}

/** Signed distance from a world point to an oriented box (negative = inside). */
export function signedDistance(box, p) {
  const q = toLocal(box, p);
  const dx = Math.abs(q.x) - box.half.x;
  const dy = Math.abs(q.y) - box.half.y;
  const dz = Math.abs(q.z) - box.half.z;
  const outside = Math.hypot(Math.max(dx, 0), Math.max(dy, 0), Math.max(dz, 0));
  return outside + Math.min(Math.max(dx, dy, dz), 0);
}

/**
 * How deep `p` sits inside `box` measured ALONG -n from the face whose outward
 * normal is n. This is the number V2 wants, and it is NOT `-signedDistance`:
 * the SDF of a point 10 cm inside a wall but 1 cm above the wall's own base
 * reads 1 cm, which would call every stoop step a failed socket. Negative means
 * outside — in front of the face, or out through the far one.
 */
export function penetrationAlong(box, p, n) {
  const q = toLocal(box, p);
  const half = [box.half.x, box.half.y, box.half.z];
  const local = [q.x, q.y, q.z];

  let axis = 0;
  let dot = 0;
  for (let i = 0; i < 3; i += 1) {
    const d = box.axes[i].dot(n);
    if (Math.abs(d) > Math.abs(dot)) { dot = d; axis = i; }
  }
  const sign = dot < 0 ? -1 : 1;

  const depth = half[axis] - sign * local[axis];
  const thickness = 2 * half[axis];
  let pen = depth <= thickness + 1e-9 ? depth : thickness - depth;

  let lateral = 0;
  for (let i = 0; i < 3; i += 1) {
    if (i !== axis) lateral = Math.max(lateral, Math.abs(local[i]) - half[i]);
  }
  if (lateral > 0) pen -= lateral;
  return pen;
}

/**
 * Separating-axis gap between two oriented boxes: the largest interval
 * separation over the 15 candidate axes. > 0 means disjoint. CHOICE (V3): this
 * is exact whenever the boxes separate along a face axis — which is every M0
 * layout, since `rot` is 0 throughout — and a lower bound on the true distance
 * otherwise, so V3 can only ever over-connect, never invent an orphan.
 */
export function boxGap(a, b) {
  const axes = [...a.axes, ...b.axes];
  for (const u of a.axes) {
    for (const v of b.axes) {
      const c = new THREE.Vector3().crossVectors(u, v);
      if (c.lengthSq() > 1e-12) axes.push(c.normalize());
    }
  }
  const delta = b.centre.clone().sub(a.centre);
  let gap = -Infinity;
  for (const axis of axes) {
    const sep = Math.abs(delta.dot(axis)) - (projRadius(a, axis) + projRadius(b, axis));
    if (sep > gap) gap = sep;
  }
  return gap;
}

/** World direction of a parent face frame vector ("n" | "u" | "v"). */
export function faceVector(parentBox, face, key) {
  const frame = FACE_FRAMES[face];
  if (!frame) throw new Error(`faceVector: unknown face "${face}"`);
  const [x, y, z] = frame[key];
  return parentBox.axes[0].clone().multiplyScalar(x)
    .addScaledVector(parentBox.axes[1], y)
    .addScaledVector(parentBox.axes[2], z)
    .normalize();
}

/** Nearest signed world axis name to a direction — for hints a human can act on. */
export function axisLabel(direction) {
  let best = FACE_NAMES[0];
  let score = -Infinity;
  for (const name of FACE_NAMES) {
    const n = FACE_FRAMES[name].n;
    const d = direction.x * n[0] + direction.y * n[1] + direction.z * n[2];
    if (d > score) { score = d; best = name; }
  }
  return best;
}

/** World AABB overlap volume of two solved parts (compile wrote `aabb`). */
export function aabbOverlapVolume(a, b) {
  let volume = 1;
  for (let i = 0; i < 3; i += 1) {
    const lo = Math.max(a.aabb.min[i], b.aabb.min[i]);
    const hi = Math.min(a.aabb.max[i], b.aabb.max[i]);
    if (hi <= lo) return 0;
    volume *= hi - lo;
  }
  return volume;
}

export function aabbVolume(part) {
  return (part.aabb.max[0] - part.aabb.min[0])
    * (part.aabb.max[1] - part.aabb.min[1])
    * (part.aabb.max[2] - part.aabb.min[2]);
}
