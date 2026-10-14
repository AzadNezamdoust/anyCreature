// The primitive vocabulary.
//
// Contract shared by every prim, and relied on by the attach solver:
//   * `dims` is always `[w, h, d]` in metres.
//   * The geometry is authored in PART-LOCAL space: centred on the origin in
//     x and z, with y running from 0 (bottom) to h (top). So the local AABB is
//     exactly [-w/2, w/2] x [0, h] x [-d/2, d/2] and the local box centre is
//     (0, h/2, 0). `resolve.js` derives every half-extent from `dims` alone and
//     never inspects vertices — so a prim that does not fill its declared box
//     would make V2/V3 measure a contact that is not there. Every round prim
//     below is therefore fitted to its dims exactly (`fitToDims`).
//   * The returned geometry is non-indexed and UNPAINTED; `build.js` paints it.
//
// M0 shipped box / bevelBox / plate. M2 adds prism / wedge / tube / stepStack
// (genus 0) and ring (genus 1 — a real hole, which is why V1 compares chi
// against a DECLARED genus and never against 2, 08:E4).
import * as THREE from "three";
import { bevelBox as bevelBoxGeom, plate as plateGeom, wedge as wedgeGeom, loft } from "./geom.js";

import RAILING from "./parts/lib/railing.json" with { type: "json" };
import RAILING_OPEN from "./parts/lib/railing_open.json" with { type: "json" };
import STAIR_FLIGHT from "./parts/lib/stairFlight.json" with { type: "json" };
import LANDING from "./parts/lib/landing.json" with { type: "json" };
import PIPE from "./parts/lib/pipe.json" with { type: "json" };
import VENT from "./parts/lib/vent.json" with { type: "json" };
import AWNING from "./parts/lib/awning.json" with { type: "json" };
import TRASHCAN from "./parts/lib/trashcan.json" with { type: "json" };
import CRATE from "./parts/lib/crate.json" with { type: "json" };
import AC_UNIT from "./parts/lib/acUnit.json" with { type: "json" };
import WHEEL from "./parts/lib/wheel.json" with { type: "json" };

/** Declared genus per prim — V1 compares chi against this, never against 2. */
export const PRIM_GENUS = Object.freeze({
  box: 0,
  bevelBox: 0,
  plate: 0,
  prism: 0,
  wedge: 0,
  tube: 0,
  stepStack: 0,
  ring: 1,
});

export const PRIM_NAMES = Object.freeze(Object.keys(PRIM_GENUS));

/**
 * Prims that are convex solids. `test/winding.test.js` can assert "every facet
 * normal points away from the centroid" only for these; `stepStack` is a
 * non-convex extrusion and `ring` has an inward-facing bore, so both are pinned
 * by the signed-volume test instead.
 */
export const PRIM_CONVEX = Object.freeze(["box", "bevelBox", "plate", "prism", "wedge", "tube"]);

/**
 * Every option a prim reads off its spec part. `validate/index.js` keys its
 * per-prim geometry cache on these, so two `stepStack`s with different `steps`
 * are not deduplicated into one.
 */
export const PRIM_OPTIONS = Object.freeze(["bevel", "sides", "steps", "wall", "axis"]);

/**
 * `axis` is the one prim option that is NOT a number — it names the axis a
 * `ring`'s bore runs along. V0 validates it against this list rather than
 * against `isFiniteNumber`, and composites.js passes it through verbatim
 * instead of evaluating it as an expression.
 */
export const RING_AXES = Object.freeze(["x", "y"]);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function clampInt(value, lo, hi, fallback) {
  const n = Math.trunc(Number(value));
  if (!Number.isFinite(n)) return fallback;
  return Math.max(lo, Math.min(hi, n));
}

/**
 * Force a geometry to occupy exactly [-w/2,w/2] x [0,h] x [-d/2,d/2].
 * An inscribed n-gon is narrower than its circumscribing box, and the solver
 * only knows the box — so the geometry is stretched to the box, not the other
 * way round. Scales are positive, so winding is untouched.
 */
function fitToDims(geometry, [w, h, d]) {
  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  const size = box.getSize(new THREE.Vector3());
  const sx = size.x > 1e-9 ? w / size.x : 1;
  const sy = size.y > 1e-9 ? h / size.y : 1;
  const sz = size.z > 1e-9 ? d / size.z : 1;
  geometry.translate(-(box.min.x + box.max.x) / 2, -box.min.y, -(box.min.z + box.max.z) / 2);
  geometry.scale(sx, sy, sz);
  return geometry;
}

/** One horizontal ellipse of `sides` points as [x, z] pairs. */
function ellipse(sides, rx, rz) {
  const points = [];
  for (let i = 0; i < sides; i += 1) {
    const angle = ((i + 0.5) / sides) * Math.PI * 2;
    points.push([Math.cos(angle) * rx, Math.sin(angle) * rz]);
  }
  return points;
}

function triangles(vertices) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  return geometry;
}

// ---------------------------------------------------------------------------
// M0 prims
// ---------------------------------------------------------------------------

/**
 * Hard box. 12 triangles, quads emitted as consecutive pairs so `paint()`'s
 * facet grouping shades each face once.
 */
function box(dims) {
  const [w, h, d] = dims;
  const geometry = new THREE.BoxGeometry(w, h, d).toNonIndexed();
  geometry.translate(0, h / 2, 0);
  return geometry;
}

/** Chamfered box — the thing that stops massing reading as Minecraft cubes. */
function bevelBox(dims, part = {}) {
  const [w, h, d] = dims;
  return bevelBoxGeom({ w, h, d, ...(part.bevel === undefined ? {} : { bevel: part.bevel }) });
}

/** Thin slab: parapet coping, sills, treads, seats. `d` is the thickness. */
function plate(dims, part = {}) {
  const [w, h, d] = dims;
  return plateGeom({ w, h, thickness: d, ...(part.bevel === undefined ? {} : { bevel: part.bevel }) });
}

// ---------------------------------------------------------------------------
// M2 prims
// ---------------------------------------------------------------------------

/**
 * N-sided vertical extrusion, capped. `sides` defaults to 6 (chimneys, posts,
 * faceted columns). Built through `loft`, which already winds its caps from the
 * loop's own orientation (geom.js FORK-FIX), so genus is 0 and chi is 2.
 */
function prism(dims, part = {}) {
  const [w, h, d] = dims;
  const sides = clampInt(part.sides, 3, 64, 6);
  const lo = ellipse(sides, w / 2, d / 2).map(([x, z]) => [x, 0, z]);
  const hi = ellipse(sides, w / 2, d / 2).map(([x, z]) => [x, h, z]);
  return fitToDims(loft([lo, hi]), dims);
}

/**
 * Solid round rod: pipes, clothesline rope, handrails. Same construction as
 * `prism` with a rounder default. The HOLLOW pipe is `ring`.
 */
function tube(dims, part = {}) {
  const [w, h, d] = dims;
  const sides = clampInt(part.sides, 3, 64, 8);
  const lo = ellipse(sides, w / 2, d / 2).map(([x, z]) => [x, 0, z]);
  const hi = ellipse(sides, w / 2, d / 2).map(([x, z]) => [x, h, z]);
  return fitToDims(loft([lo, hi]), dims);
}

/** Tapered box: awning brackets, arch heads, finials, chamfered caps. */
function wedge(dims, part = {}) {
  const [w, h, d] = dims;
  return wedgeGeom({ w, h, d, ...(part.bevel === undefined ? {} : { bevel: part.bevel }) });
}

/**
 * Open-ended hollow ring — a trash-can body, a pipe collar, a bin rim.
 * GENUS 1: the bore is a real hole, chi = 0. `wall` is the wall thickness in
 * metres (default 18 % of the smaller footprint axis).
 *
 * Four quad strips — outer wall, inner wall, top annulus, bottom annulus —
 * wound so every facet normal points out of the solid (outwards on the outer
 * wall, INWARDS on the bore, which is why this prim is excluded from the convex
 * winding assertion).
 */
function ring(dims, part = {}) {
  // M5: a side-mounted wheel needs its bore along X, not Y. The X ring is the Y
  // ring built on permuted dims and turned -90 deg about Z ((x,y,z) -> (y,-x,z)),
  // which is a rotation: winding, genus and chi are all untouched, and the
  // permutation keeps `wall` measured across the two DIAMETER axes.
  if (String(part.axis ?? "y").toLowerCase() === "x") {
    const [w, h, d] = dims;
    const turned = ringY([h, w, d], part)
      .applyMatrix4(new THREE.Matrix4().makeRotationZ(-Math.PI / 2));
    return fitToDims(turned, dims);
  }
  return fitToDims(ringY(dims, part), dims);
}

/** The ring itself, bore along +Y, before `fitToDims`. */
function ringY(dims, part = {}) {
  const [w, h, d] = dims;
  const sides = clampInt(part.sides, 3, 64, 12);
  const maxWall = Math.min(w, d) * 0.45;
  const wall = Math.max(1e-3, Math.min(Number(part.wall ?? Math.min(w, d) * 0.18), maxWall));

  const outer = ellipse(sides, w / 2, d / 2);
  const inner = ellipse(sides, w / 2 - wall, d / 2 - wall);
  const at = (points, i, y) => [points[i][0], y, points[i][1]];

  const v = [];
  const push = (...points) => { for (const p of points) v.push(p[0], p[1], p[2]); };

  for (let i = 0; i < sides; i += 1) {
    const j = (i + 1) % sides;
    const oLoI = at(outer, i, 0); const oLoJ = at(outer, j, 0);
    const oHiI = at(outer, i, h); const oHiJ = at(outer, j, h);
    const iLoI = at(inner, i, 0); const iLoJ = at(inner, j, 0);
    const iHiI = at(inner, i, h); const iHiJ = at(inner, j, h);

    // Outer wall: normal points away from the axis.
    push(oLoI, oHiI, oLoJ); push(oHiI, oHiJ, oLoJ);
    // Inner wall (the bore): normal points toward the axis.
    push(iLoI, iLoJ, iHiI); push(iLoJ, iHiJ, iHiI);
    // Top annulus: +Y.
    push(iHiI, oHiJ, oHiI); push(iHiI, iHiJ, oHiJ);
    // Bottom annulus: -Y.
    push(iLoI, oLoI, oLoJ); push(iLoI, oLoJ, iLoJ);
  }

  return triangles(v);
}

/**
 * A staircase as ONE closed solid: the staircase profile in (z, y) extruded
 * along x. Steps ascend toward +Z; `steps` (default 3) sets the count, so the
 * rise is h/steps and the run is d/steps.
 *
 * DEVIATION (M2): the brief points at `geom.js stepStack`, but that helper
 * merges N separate bevelBoxes — N disconnected shells, chi = 2N — and V1
 * rejects it as a compiler bug. A stair prim has to be one manifold, so this is
 * a new builder rather than a wrapper.
 *
 * The profile is star-shaped about its bottom-back corner (for a monotone
 * staircase every interior point is visible from it), so a triangle fan from
 * that vertex is a valid, non-overlapping triangulation and needs no ear clip.
 */
function stepStack(dims, part = {}) {
  const [w, h, d] = dims;
  const steps = clampInt(part.steps, 1, 40, 3);
  const rise = h / steps;
  const run = d / steps;

  // Counter-clockwise in the (z -> right, y -> up) plot.
  const profile = [[-d / 2, 0], [d / 2, 0], [d / 2, h]];
  for (let k = steps; k >= 1; k -= 1) {
    const z = -d / 2 + (k - 1) * run;
    profile.push([z, k * rise]);
    if (k > 1) profile.push([z, (k - 1) * rise]);
  }
  return fitToDims(extrudeAlongX(profile, w), dims);
}

/**
 * Extrude a closed 2-D profile (list of `[z, y]`) along x by `w`, centred.
 * Orientation is normalised here: the caller may hand the loop in either
 * winding and every emitted facet still points out of the solid.
 */
function extrudeAlongX(profile, w) {
  let area = 0;
  for (let i = 0; i < profile.length; i += 1) {
    const [z0, y0] = profile[i];
    const [z1, y1] = profile[(i + 1) % profile.length];
    area += z0 * y1 - z1 * y0;
  }
  // Clockwise in (z, y) is the orientation for which the +x cap fan faces +X.
  const loop = area > 0 ? [...profile].reverse() : [...profile];
  const n = loop.length;

  const hi = (i) => [w / 2, loop[i][1], loop[i][0]];
  const lo = (i) => [-w / 2, loop[i][1], loop[i][0]];

  const v = [];
  const push = (...points) => { for (const p of points) v.push(p[0], p[1], p[2]); };

  for (let k = 1; k < n - 1; k += 1) {
    push(hi(0), hi(k), hi(k + 1));          // +X cap
    push(lo(0), lo(k + 1), lo(k));          // -X cap
  }
  for (let i = 0; i < n; i += 1) {
    const j = (i + 1) % n;
    push(lo(i), lo(j), hi(i));
    push(lo(j), hi(j), hi(i));
  }
  return triangles(v);
}

const BUILDERS = Object.freeze({ box, bevelBox, plate, prism, wedge, tube, ring, stepStack });

/** True only for own keys, so `prim: "toString"` cannot pass a lookup. */
export function isPrim(name) {
  return typeof name === "string" && Object.hasOwn(BUILDERS, name);
}

/**
 * Build one prim in part-local space.
 * @param {string} name
 * @param {number[]} dims [w, h, d] metres
 * @param {object} [part] the spec part, for optional prim options
 */
export function buildPrim(name, dims, part) {
  if (!isPrim(name)) throw new Error(`buildPrim: unknown prim "${name}"`);
  return BUILDERS[name](dims, part ?? {});
}

// ---------------------------------------------------------------------------
// Composite prims — the library loader (PLAN 1.1, 08:A2).
//
// A composite is NOT geometry: it is a versioned spec fragment in
// `src/parts/lib/`, expanded into ordinary parts by `compile/composites.js`
// before the solver ever runs. Imported statically (not globbed) so the node
// gate and the vite bundle see exactly the same eleven files.
// ---------------------------------------------------------------------------

export const COMPOSITE_SCHEMA = "pg/1-composite";

const COMPOSITES = Object.freeze({
  railing: RAILING,
  railing_open: RAILING_OPEN,
  stairFlight: STAIR_FLIGHT,
  landing: LANDING,
  pipe: PIPE,
  vent: VENT,
  awning: AWNING,
  trashcan: TRASHCAN,
  crate: CRATE,
  acUnit: AC_UNIT,
  wheel: WHEEL,
});

export const COMPOSITE_NAMES = Object.freeze(Object.keys(COMPOSITES));

export function isComposite(name) {
  return typeof name === "string" && Object.hasOwn(COMPOSITES, name);
}

/** The raw library fragment, or null. Callers must not mutate it. */
export function loadComposite(name) {
  return isComposite(name) ? COMPOSITES[name] : null;
}
