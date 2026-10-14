// The attach solver — PLAN.md 1.2, gap 08:G4.
//
// This file is the reason the LLM never writes a world coordinate. It turns
// `{to, face, uv, contact, embed, align, rot}` into one Matrix4, and it is the
// ONLY place a translation is computed. If it is ambiguous, failure mode 1
// (floating parts) walks back in through the compiler itself, so every rule
// below is stated once, here, and mirrored verbatim in `dsl/SPEC.md`.
import * as THREE from "three";

/**
 * Parent face frames. Origin sits on the face centre; `u` and `v` are the face
 * tangents, `n` the outward normal. Every row satisfies u x v = -n, so the
 * frames are consistent with each other: `v` is up (or the nearest thing to up)
 * on all four sides, and a `uv` never flips meaning between two faces of the
 * same box.
 */
export const FACE_FRAMES = Object.freeze({
  "+X": Object.freeze({ n: [1, 0, 0], u: [0, 0, 1], v: [0, 1, 0] }),
  "-X": Object.freeze({ n: [-1, 0, 0], u: [0, 0, -1], v: [0, 1, 0] }),
  "+Y": Object.freeze({ n: [0, 1, 0], u: [1, 0, 0], v: [0, 0, 1] }),
  "-Y": Object.freeze({ n: [0, -1, 0], u: [1, 0, 0], v: [0, 0, -1] }),
  "+Z": Object.freeze({ n: [0, 0, 1], u: [-1, 0, 0], v: [0, 1, 0] }),
  "-Z": Object.freeze({ n: [0, 0, -1], u: [1, 0, 0], v: [0, 1, 0] }),
});

export const FACE_NAMES = Object.freeze(Object.keys(FACE_FRAMES));

/**
 * Contact vocabulary. M0 shipped flush / rests-on-top / socket; M5 adds the two
 * the wider vocabulary always named:
 *
 *   * `hangs-below` — the child's +Y-most face touches the parent's -Y face and
 *     the child hangs UNDER it (`embed` as usual). The algebra is the flush
 *     algebra on the `-Y` face — the child's contact face is already the one
 *     whose outward normal is -n, which for n = -Y is its top — so this contact
 *     adds no new maths. What it adds is a NAME (V0 pins it to face `-Y`, so a
 *     "hanging" part cannot silently be authored on a side face) and a place for
 *     V2 to say "it hangs off" instead of "it is flush".
 *   * `embedded` — the child's CENTRE is placed at the parent point and then
 *     pushed `embed` further in along -n, so the child lives inside the parent
 *     rather than on it (a hub inside a tyre's bore, a light inside a housing).
 *     V2 measures it as a volume fraction, not a surface penetration.
 */
export const CONTACTS = Object.freeze(["flush", "rests-on-top", "socket", "hangs-below", "embedded"]);
export const ALIGNMENTS = Object.freeze(["bottom", "center", "top"]);

/**
 * M6 gap 3: `alignU` is `align`'s twin on the face's OTHER tangent. `align`
 * anchors a child extreme along `v`; `alignU` anchors one along `u`, which is
 * the axis the solver used to centre unconditionally. It is what lets a rail
 * span the full width of a parent narrower than itself (a top rail on a post),
 * so a railing no longer needs an infill web to have a full-width parent.
 * `center` is the default and reproduces the pre-M6 algebra exactly.
 */
export const ALIGN_U = Object.freeze(["start", "center", "end"]);

/** The face `hangs-below` is defined on. V0 rejects it on any other face. */
export const HANGS_BELOW_FACE = "-Y";

/** Default penetration per contact mode, in metres, when `embed` is absent. */
const DEFAULT_EMBED = Object.freeze({
  flush: 0,
  "rests-on-top": 0,
  socket: 0.05,
  "hangs-below": 0,
  embedded: 0.05,
});

export function isFace(name) {
  return typeof name === "string" && Object.hasOwn(FACE_FRAMES, name);
}

export function isContact(name) {
  return CONTACTS.includes(name);
}

export function isAlign(name) {
  return ALIGNMENTS.includes(name);
}

export function isAlignU(name) {
  return ALIGN_U.includes(name);
}

/** Half-extents of a prim from its dims alone — see the prims.js local frame. */
export function halfExtents(dims) {
  return new THREE.Vector3(dims[0] / 2, dims[1] / 2, dims[2] / 2);
}

/** Signed axis name ("+Y", "-X") to a unit vector. */
export function axisVector(name) {
  const frame = FACE_FRAMES[name];
  if (!frame) throw new Error(`axisVector: unknown axis "${name}"`);
  return new THREE.Vector3().fromArray(frame.n);
}

/**
 * Support of an axis-aligned box, rotated by `basis`, along a unit direction:
 * the distance from its centre to its extreme in that direction. Exact for a
 * box, which is every M0 prim.
 */
function support(direction, half, basis) {
  const axis = new THREE.Vector3();
  let total = 0;
  for (const [index, extent] of [[0, half.x], [1, half.y], [2, half.z]]) {
    axis.setFromMatrixColumn(basis, index);
    total += Math.abs(direction.dot(axis)) * extent;
  }
  return total;
}

/**
 * Resolve one child placement against a solved parent.
 *
 * Order of operations (PLAN 1.2), per child:
 *   1. child geometry exists at the origin at `dims` (prims.js does this);
 *   2. `rot` degrees about the attach normal `n`;
 *   3. contact face = the child face whose outward normal is -n;
 *   4. `align` anchors the child's extreme along the face tangent `v`
 *      (bottom = -v extreme, top = +v extreme, center = the child's centre);
 *      `alignU` does the same along `u` (start = -u extreme, end = +u extreme,
 *      center = the child's centre, and center is the default);
 *   5. the parent point is the face centre displaced by (uv - 0.5) * 2 * halfExtent
 *      along u and v;
 *   6. the child moves so its anchor sits on that point, then slides -n by
 *      `embed` so the two surfaces genuinely overlap — except `embedded`, whose
 *      anchor is the child's centre, not its contact face;
 *   7. the whole thing is multiplied by the parent's world matrix.
 *
 * @param {{dims:number[], matrix:THREE.Matrix4}} parent solved parent part
 * @param {{dims:number[], attach:object}} child spec part (already schema-valid)
 * @param {{uvOverride?:number[]}} [options] `uvOverride` is how `mirror` reuses this
 * @returns {{matrix:THREE.Matrix4, embed:number, contact:string, face:string}}
 */
export function resolveAttach(parent, child, options = {}) {
  const attach = child.attach;
  const frame = FACE_FRAMES[attach.face];
  if (!frame) throw new Error(`resolveAttach: unknown face "${attach.face}" on part "${child.id}"`);

  const n = new THREE.Vector3().fromArray(frame.n);
  const u = new THREE.Vector3().fromArray(frame.u);
  const v = new THREE.Vector3().fromArray(frame.v);

  const parentHalf = halfExtents(parent.dims);
  const identity = new THREE.Matrix4();

  // (5) the parent point, in parent-local space.
  const [uParam, vParam] = options.uvOverride ?? attach.uv ?? [0.5, 0.5];
  const halfN = support(n, parentHalf, identity);
  const halfU = support(u, parentHalf, identity);
  const halfV = support(v, parentHalf, identity);

  const parentCentre = new THREE.Vector3(0, parentHalf.y, 0);   // prims.js: y runs 0..h
  const parentPoint = parentCentre.clone()
    .addScaledVector(n, halfN)
    .addScaledVector(u, (uParam - 0.5) * 2 * halfU)
    .addScaledVector(v, (vParam - 0.5) * 2 * halfV);

  // (2) rotation about the attach normal, and nothing else — 08:A7.
  const rotDeg = Number(attach.rot ?? 0);
  const basis = new THREE.Matrix4().makeRotationAxis(n, THREE.MathUtils.degToRad(rotDeg));

  // (3)(4)(6) the child's centre, still in parent-local space.
  const childHalf = halfExtents(child.dims);
  const contact = attach.contact;
  const embed = Number(attach.embed ?? DEFAULT_EMBED[contact] ?? 0);
  const align = attach.align ?? "center";
  const alignU = attach.alignU ?? "center";

  // `embedded` anchors the child's CENTRE on the parent point (and then pushes
  // it `embed` further in); every other contact anchors its contact FACE there.
  const alongN = contact === "embedded" ? -embed : support(n, childHalf, basis) - embed;
  const alongV = align === "bottom"
    ? support(v, childHalf, basis)
    : align === "top" ? -support(v, childHalf, basis) : 0;
  const alongU = alignU === "start"
    ? support(u, childHalf, basis)
    : alignU === "end" ? -support(u, childHalf, basis) : 0;

  const childCentre = parentPoint.clone()
    .addScaledVector(n, alongN)
    .addScaledVector(u, alongU)
    .addScaledVector(v, alongV);

  // Part-local (bottom-centred) -> parent-local: drop to the box centre, rotate,
  // then translate. (7) parent world matrix last.
  const local = new THREE.Matrix4()
    .makeTranslation(childCentre.x, childCentre.y, childCentre.z)
    .multiply(basis)
    .multiply(new THREE.Matrix4().makeTranslation(0, -childHalf.y, 0));

  return {
    matrix: new THREE.Matrix4().multiplyMatrices(parent.matrix, local),
    embed,
    contact,
    face: attach.face,
  };
}

/** A ground part carries no attach: it sits at the world origin, bottom on y=0. */
export function resolveGround() {
  return { matrix: new THREE.Matrix4(), embed: 0, contact: "ground", face: null };
}
