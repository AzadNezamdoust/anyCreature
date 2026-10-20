// Repetition and symmetry macros — `repeat` and `mirror`.
//
// Expansion runs AFTER the attach solve and BEFORE the contact table, so the
// facade grammar (M2) reads the expanded set and can suppress the tiles a
// repeated balcony actually covers (08:G6).
//
// `repeat.axis` is stated in the PARENT's local frame; the compiler resolves it
// to a world direction and writes that into the solved part, so V5's
// screen-space test measures the direction the pixels actually got (08:G5).
import * as THREE from "three";
import { axisVector } from "./resolve.js";

export const REPEAT_AXES = Object.freeze(["+X", "-X", "+Y", "-Y", "+Z", "-Z"]);

/**
 * World direction of a parent-local signed axis.
 * @param {THREE.Matrix4} parentMatrix
 * @param {string} axisName "+X" .. "-Z"
 */
export function worldAxis(parentMatrix, axisName) {
  const basis = new THREE.Matrix3().setFromMatrix4(parentMatrix);
  return axisVector(axisName).applyMatrix3(basis).normalize();
}

/**
 * Expand one resolved placement into its instances.
 *
 * `mirror: true` duplicates the part at `u -> 1 - u` on the same parent face.
 * MVP-STUB: mirroring about the parent face's u centre is exact only because
 * every M0 prim is symmetric in u; the general case (reflect the geometry and
 * flip the winding, geom.js `mirrorX`) arrives with the asymmetric prims in M2.
 *
 * @param {{id:string, matrix:THREE.Matrix4}} base placement from resolveAttach
 * @param {{repeat?:object, mirror?:boolean}} part the spec part
 * @param {{matrix:THREE.Matrix4}|null} parent solved parent, for the repeat frame
 * @param {(uv:number[])=>{matrix:THREE.Matrix4}} [reresolve] re-runs the solver for `mirror`
 * @returns {Array<{id:string, matrix:THREE.Matrix4, worldRepeatAxis:number[]|null}>}
 */
export function expand(base, part, parent, reresolve) {
  const bases = [{ id: base.id, matrix: base.matrix }];

  if (part.mirror === true && part.attach && typeof reresolve === "function") {
    const [u, v] = part.attach.uv ?? [0.5, 0.5];
    bases.push({ id: `${base.id}~m`, matrix: reresolve([1 - u, v]).matrix });
  }

  const repeat = part.repeat;
  if (!repeat) return bases.map((b) => ({ ...b, worldRepeatAxis: null }));

  const frame = parent ? parent.matrix : new THREE.Matrix4();
  const direction = worldAxis(frame, repeat.axis);
  const axisArray = direction.toArray();
  const count = Math.trunc(repeat.count);
  const pitch = Number(repeat.pitch);

  const out = [];
  for (const b of bases) {
    for (let k = 0; k < count; k += 1) {
      const step = direction.clone().multiplyScalar(k * pitch);
      const matrix = new THREE.Matrix4()
        .makeTranslation(step.x, step.y, step.z)
        .multiply(b.matrix);
      out.push({
        id: k === 0 ? b.id : `${b.id}#${k}`,
        matrix,
        worldRepeatAxis: axisArray,
      });
    }
  }
  return out;
}
