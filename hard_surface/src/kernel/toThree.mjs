// Kernel solids -> the ONE merged, flat-shaded, vertex-coloured geometry the
// studio and the capture page already know how to render.
//
// The output shape is deliberately the shape `compile()` returns
// (`src/compile/build.js:164-200`): `{ geometry, spec, solved: { parts, bounds,
// triangles } }`, plus top-level `parts`/`bounds` aliases. `app.js` therefore
// renders an authored module through the same lines it renders a spec through -
// no second render path, no second capture contract.
import * as THREE from "three";

import { mergeGeometries, paint, triangleCount } from "../geom.js";

// ---------------------------------------------------------------------------
// WF-LOOP r1 row 1 — the FRONT contract.
//
// The author always builds the populated face on -Z (`src/kernel/README.md`
// "Frame"). At the solved TARGET camera (elevation 29.2 deg, azimuth 43.1 deg)
// the camera's screen-right in world XZ is ~(+0.73, 0, -0.68) and its screen-up
// is ~(-0.33, +0.87, -0.36). A face whose horizontals run along X therefore
// FALLS to the right (dot(+X, up) < 0); a face whose horizontals run along Z
// RISES to the right (dot(-Z, up) > 0). The target brick building's window
// heads rise, so the populated face has to be the +X one at capture time.
//
// WHICH FRAME IS WHICH, and this is the documented answer to the brief's
// either/or: the VALIDATORS RUN IN THE AUTHOR FRAME, unrotated. Only the render
// rotates. That is deliberate — every V11/V12 row measures "along the facade"
// as the X axis and "off the wall" as Z (ladder x-ranges, census y-bands, deck
// gaps along the short axis), which is only true in the author frame. The
// rotation is a rigid quarter turn about Y, so it changes no quantity the chain
// measures except axis-aligned boxes, and those are exactly what must stay in
// the author frame. `partsToGeometry` therefore defaults to NO rotation (what
// `validateParts` calls) and `app.js` passes the module's front axis in.
// ---------------------------------------------------------------------------

/** Degrees about +Y that carry each declared front axis onto +X. */
export const FRONT_AXES = Object.freeze({ "-Z": -90, "+Z": 90, "+X": 0, "-X": 180 });

/** The contract default: an author who declares nothing built the front on -Z. */
export const DEFAULT_FRONT = "-Z";

/**
 * @param {string} [front] `meta.front`, one of FRONT_AXES' keys.
 * @returns {number} degrees about +Y to apply to the assembly before framing.
 */
export function frontRotationDeg(front = DEFAULT_FRONT) {
  const key = typeof front === "string" ? front.trim().toUpperCase().replace(/^Z$/, "+Z") : DEFAULT_FRONT;
  const deg = FRONT_AXES[key];
  return Number.isFinite(deg) ? deg : FRONT_AXES[DEFAULT_FRONT];
}

/** Exact cos/sin at the quarter turns, so a rotated box stays axis-aligned. */
const QUARTER = new Map([[0, [1, 0]], [90, [0, 1]], [180, [-1, 0]], [270, [0, -1]]]);

function rotationY(deg) {
  const norm = ((deg % 360) + 360) % 360;
  const exact = QUARTER.get(norm);
  const c = exact ? exact[0] : Math.cos(THREE.MathUtils.degToRad(deg));
  const s = exact ? exact[1] : Math.sin(THREE.MathUtils.degToRad(deg));
  return new THREE.Matrix4().set(c, 0, s, 0, 0, 1, 0, 0, -s, 0, c, 0, 0, 0, 0, 1);
}

/**
 * One kernel solid -> a NON-INDEXED BufferGeometry, each triangle carrying its
 * own three vertices. That is what makes `paint()` (`src/geom.js:116`) read
 * flat normals per facet; sharing vertices would average them and the brick
 * would shade like a balloon.
 * @param {{mesh:function}} solid
 * @returns {THREE.BufferGeometry}
 */
export function solidToGeometry(solid) {
  const mesh = solid.mesh();
  const stride = mesh.numProp;
  const verts = mesh.vertProperties;
  const tris = mesh.triVerts;
  const positions = new Float32Array(tris.length * 3);
  for (let i = 0; i < tris.length; i += 1) {
    const base = tris[i] * stride;
    positions[i * 3] = verts[base];
    positions[i * 3 + 1] = verts[base + 1];
    positions[i * 3 + 2] = verts[base + 2];
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}

/** 6 decimals: enough for millimetres, short enough that a report diff reads. */
function round(value) {
  return Math.round(value * 1e6) / 1e6;
}

/**
 * Every part painted from the palette, merged into one geometry.
 * @param {Array<{id:string, solid:object, zone:string, role?:string, touches?:string[]}>} parts
 * @param {Record<string,string>} palette zone -> css colour
 * @param {string|number} seed colour-jitter stream key, per part: `${seed}:${id}`
 * @param {{frontRotationDeg?:number, shade?:object, idPalette?:Record<string,string>}} [options]
 *   `frontRotationDeg` turns the whole assembly about +Y before the boxes are
 *   measured (see the FRONT contract at the top of this file). Default 0 = the
 *   author frame, which is what the validator chain calls; only the renderer
 *   passes a rotation.
 *   `idPalette` (WF-LOOP r2 A2) is the ID PASS: role -> flat colour. When it is
 *   present every part is painted that ONE colour with every shading term off,
 *   so the capture is a role mask of exactly the same geometry at exactly the
 *   same camera. A role missing from the table is an error, not magenta: an
 *   unnamed role would silently join whatever role shares its fallback.
 */
export function partsToGeometry(parts, palette = {}, seed = 1, options = {}) {
  const pieces = [];
  const out = [];
  // Applied AFTER paint() so the shading is identical in both frames: paint's
  // front/back tint reads the facet normal, and a colour that changed with the
  // camera framing would make the capture depend on it.
  const turn = Number.isFinite(options.frontRotationDeg) ? options.frontRotationDeg : 0;
  // V2 (2026-09-13, owner "too far from the truth"): the character painter's 30 % bottom-up AO
  // turned an 11 m brick wall maroon. Buildings are flat cartoon colour: light AO, a little
  // top lift. Authors may override with meta.shade = { ao, upTint } (0..1).
  // V2 r2 A1: sideTint comes from SHADE (-0.12). The front is built on +-Z by the
  // FRONT contract, so the non-front horizontal axis is x — paint()'s default.
  const shade = { ao: 0.08, upTint: 0.12, ...(options.shade ?? {}) };
  // A2: the id pass is the same geometry with every shading term switched off.
  const idPalette = options.idPalette ?? null;
  const flat = idPalette ? { ao: 0, upTint: 0, frontTint: 0, sideTint: 0, jitter: 0 } : null;
  const matrix = turn === 0 ? null : rotationY(turn);
  for (const part of parts) {
    let colour;
    if (idPalette) {
      colour = idPalette[part.role];
      if (!colour) throw new Error(`idpass: role "${part.role}" (part ${part.id}) has no id colour`);
    } else {
      colour = palette[part.zone] ?? "#ff00ff";
    }
    const painted = paint(solidToGeometry(part.solid), colour, { seed: `${seed}:${part.id}`, facets: "plane", ...(flat ?? shade) });
    if (matrix) painted.applyMatrix4(matrix);
    painted.computeBoundingBox();
    const box = painted.boundingBox;
    out.push({
      id: part.id,
      zone: part.zone,
      role: part.role,
      touches: part.touches,
      genus: part.solid.genus(),
      status: part.solid.status(),
      triCount: triangleCount(painted),
      aabb: { min: box.min.toArray().map(round), max: box.max.toArray().map(round) },
    });
    pieces.push(painted);
  }

  const geometry = mergeGeometries(pieces);
  geometry.computeBoundingBox();
  const box = geometry.boundingBox ?? new THREE.Box3();
  const size = box.getSize(new THREE.Vector3());
  const bounds = {
    w: round(size.x),
    h: round(size.y),
    d: round(size.z),
    minY: round(box.min.y),
    centre: [round((box.min.x + box.max.x) / 2), round((box.min.y + box.max.y) / 2), round((box.min.z + box.max.z) / 2)],
    min: box.min.toArray().map(round),
    max: box.max.toArray().map(round),
  };

  return {
    geometry,
    parts: out,
    bounds,
    frontRotationDeg: turn,
    spec: null,
    solved: {
      subject: null,
      seed,
      tiles: [],
      parts: out,
      bounds,
      triangles: triangleCount(geometry),
    },
  };
}
