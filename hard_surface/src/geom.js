// Flat-shaded, vertex-coloured primitives for one continuous soft body mass.
//
// Contract (frozen — every part module builds through these):
//   * Every builder returns a NON-INDEXED BufferGeometry with a `color` attribute
//     already written. One material for the whole character, so one draw call.
//   * Colour comes from a zone name, never a literal hex, so palettes stay swappable.
//   * Shading is baked per FACET — never per triangle, or the two halves of a
//     quad mismatch and the part reads as mottled: a vertical ambient-occlusion
//     ramp and a normal tint, and nothing random. No lights are required to read
//     the silhouette, and no textures are ever needed.
//   * Geometry is authored in the PART's local space and positioned by the caller.
//   * The workhorses are `ring` / `wall` / `fan` / `tube` / `ball`: gently faceted
//     lofted surfaces, 8-12 sides. `wall` can skin an ARC of the ring instead of
//     the whole loop, which is how a painted colour region (a bib, a beard, an
//     apron panel) covers only the front of the body mass. The chamfered-box
//     builders below are kept for the few props that still want a hard edge.
import * as THREE from "three";

export const SHADE = Object.freeze({
  // Per-face random multiplier. OFF. Random value on top of a flat zone colour
  // reads as dirt, not as form: it breaks one part into mismatched light and
  // dark patches and puts two tones on a single shin. The only tonal moves left
  // are the ones that MEAN something — the vertical AO ramp and the form-turn
  // wrap — so a part holds one tone with a single soft light-to-shadow break.
  jitter: 0,
  ao: 0.30,          // how much darker the bottom of a part gets
  upTint: 0.10,      // faces pointing up brighten, faces pointing down darken
  frontTint: 0.03,
  // WF-LOOP r2 A1 — the SIDE step. The capture is now unlit (app.js paints the
  // merged mesh with MeshBasicMaterial), so the only thing that can separate the
  // populated face from the return is baked value. The target is three flat
  // values, front > side > roof (front V .65, side V .52); this is the
  // front->side step. Applied to facets whose normal runs along the NON-FRONT
  // horizontal axis (the author builds the front on +-Z, so that axis is x).
  //
  // DEVIATION from WF-LOOP-R2 A1, one number, measured not argued. A1 asks for
  // "sideTint (default -0.12)" AND for a captured side/front value ratio of
  // 0.80-0.92 ("side -12 %"). Those are two different numbers: `shade` multiplies
  // the LINEAR working colour, and the capture writes sRGB, so a linear -0.12
  // shows up on screen as 0.88^(1/2.2) = -4.3 % (measured: side/front 0.958,
  // gate FAIL). -0.26 linear is the -12 % the README sentence and the gate both
  // ask for: measured side/front 0.88. The name and the meaning A1 states are
  // kept ("the side reads 12 % darker than the front in the capture"); only the
  // encoding of that 12 % moved into the gamma it is actually written through.
  sideTint: -0.26,
});

// Baked form-turn axis, in the xz plane. A lofted volume only READS as a barrel
// if its facets step in TONE as they turn around it: with one even value across
// every side facet the section collapses to a card, and deepening that card only
// makes it a wider card. The axis sits mostly frontal so the falloff is roughly
// symmetric about the centre line (it still reads round when the figure turns),
// leaned toward the studio key so the baked step and the lit step agree instead
// of cancelling. `wrapPivot` is the mean turn the visible band carries, so the
// step redistributes value around the zone colour rather than lifting it.
// Sign matches OUTWARD normals; the wrap was tuned against the old inward
// normals, so both components negate with the winding fix to keep the judged ramp.
export const WRAP_DIR = Object.freeze({ x: 0.662, z: -0.749 });
export const WRAP_PIVOT = 0.60;

/** Deterministic 32-bit hash — the whole generator must be seed-reproducible. */
export function hash32(value) {
  let h = 2166136261 >>> 0;
  const text = String(value);
  for (let i = 0; i < text.length; i += 1) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

/** Small deterministic PRNG; every part gets its own stream keyed by seed + part id. */
export function rng(seedValue) {
  let state = (hash32(seedValue) || 1) >>> 0;
  return function next() {
    state ^= state << 13; state >>>= 0;
    state ^= state >>> 17;
    state ^= state << 5; state >>>= 0;
    return state / 4294967296;
  };
}

/**
 * Triangle groups that make up ONE facet. `wall` and `loft` both emit a quad as
 * two consecutive triangles across a shared diagonal, and on an elliptical loft
 * that quad is slightly non-planar — so the two halves carried different
 * normals, different centroid heights and therefore different tones. A flat
 * chest then read as a patchwork of triangles and a shin as two tones side by
 * side. A consecutive pair sharing exactly two corner positions is one facet and
 * is shaded once, off the averaged normal and centroid. Greedy pairing stays in
 * step because every quad run has an even triangle count.
 * @param {THREE.BufferAttribute} position non-indexed positions
 * @returns {number[][]} lists of first-vertex indices, one list per facet
 */
// V2 (2026-09-13): boolean output from manifold-3d triangulates one wall face into
// many irregular triangles, so the quad-pair grouping below splits a coplanar face
// into as many AO tones as triangles and the seams read as diagonal "lighting".
// `paint({facets:"plane"})` groups by plane instead: same unit normal (3 dp) and
// same signed offset n·p (3 dp) => one tone. Used by src/kernel/toThree.mjs only;
// v1 callers keep the quad grouping so their captures do not move.
function facetGroupsByPlane(position, normal) {
  const triangles = position.count / 3;
  const map = new Map();
  for (let t = 0; t < triangles; t += 1) {
    const i = t * 3;
    let nx = 0, ny = 0, nz = 0;
    for (let v = 0; v < 3; v += 1) { nx += normal.getX(i + v); ny += normal.getY(i + v); nz += normal.getZ(i + v); }
    const len = Math.hypot(nx, ny, nz) || 1;
    nx /= len; ny /= len; nz /= len;
    const d = nx * position.getX(i) + ny * position.getY(i) + nz * position.getZ(i);
    const key = `${nx.toFixed(3)},${ny.toFixed(3)},${nz.toFixed(3)}|${d.toFixed(3)}`;
    let group = map.get(key);
    if (!group) { group = []; map.set(key, group); }
    group.push(i);
  }
  return [...map.values()];
}

function facetGroups(position) {
  const triangles = position.count / 3;
  const corners = [];
  for (let t = 0; t < triangles; t += 1) {
    const base = t * 3;
    corners.push([
      `${position.getX(base)},${position.getY(base)},${position.getZ(base)}`,
      `${position.getX(base + 1)},${position.getY(base + 1)},${position.getZ(base + 1)}`,
      `${position.getX(base + 2)},${position.getY(base + 2)},${position.getZ(base + 2)}`,
    ]);
  }
  const groups = [];
  let t = 0;
  while (t < triangles) {
    if (t + 1 < triangles) {
      let shared = 0;
      for (const corner of corners[t]) if (corners[t + 1].indexOf(corner) !== -1) shared += 1;
      if (shared === 2) {
        groups.push([t * 3, (t + 1) * 3]);
        t += 2;
        continue;
      }
    }
    groups.push([t * 3]);
    t += 1;
  }
  return groups;
}

/**
 * Bake per-face colour into a non-indexed geometry.
 * @param {THREE.BufferGeometry} geometry non-indexed
 * @param {THREE.Color|string|number} baseColor
 * `aoMin`/`aoMax` pin the vertical AO window to something bigger than this
 * geometry's own bounds — the body mass is emitted as many bone/colour segments
 * and every one of them has to sit on the SAME ramp or the seams read as stripes.
 * @param {{seed?:string|number, jitter?:number, ao?:number, upTint?:number, frontTint?:number, sideTint?:number, sideAxis?:"x"|"z", aoMin?:number, aoMax?:number, wrap?:number, wrapPivot?:number}} options
 */
export function paint(geometry, baseColor, options = {}) {
  const source = geometry.index ? geometry.toNonIndexed() : geometry;
  source.computeVertexNormals();
  const position = source.getAttribute("position");
  const normal = source.getAttribute("normal");
  const count = position.count;
  const colors = new Float32Array(count * 3);
  const base = new THREE.Color(baseColor);

  source.computeBoundingBox();
  const box = source.boundingBox;
  const aoMin = options.aoMin ?? box.min.y;
  const aoMax = options.aoMax ?? box.max.y;
  const spanY = Math.max(1e-6, aoMax - aoMin);

  const jitterAmount = options.jitter ?? SHADE.jitter;
  const aoAmount = options.ao ?? SHADE.ao;
  const upAmount = options.upTint ?? SHADE.upTint;
  const frontAmount = options.frontTint ?? SHADE.frontTint;
  // WF-LOOP r2 A1 — front/side value step, see SHADE.sideTint.
  const sideAmount = options.sideTint ?? SHADE.sideTint;
  const sideAxisZ = options.sideAxis === "z";
  // `wrap` is opt-in: only volumes that must read as round ask for it.
  const wrapAmount = options.wrap ?? 0;
  const wrapPivot = options.wrapPivot ?? WRAP_PIVOT;
  const next = rng(options.seed ?? "part");
  const color = new THREE.Color();

  // One tone per FACET, not per triangle: the two halves of a quad share a
  // centroid and a normal here, so a facet never splits into two values.
  const groups = options.facets === "plane" ? facetGroupsByPlane(position, normal) : facetGroups(position);
  for (const group of groups) {
    let sumY = 0;
    let nx = 0;
    let ny = 0;
    let nz = 0;
    for (const i of group) {
      sumY += position.getY(i) + position.getY(i + 1) + position.getY(i + 2);
      nx += normal.getX(i);
      ny += normal.getY(i);
      nz += normal.getZ(i);
    }
    const length = Math.hypot(nx, ny, nz) || 1;
    nx /= length; ny /= length; nz /= length;
    const midY = sumY / (group.length * 3);
    const height = Math.min(1, Math.max(0, (midY - aoMin) / spanY));   // 0 bottom .. 1 top

    let shade = 1;
    shade *= 1 - aoAmount * (1 - height);                   // vertical AO ramp
    shade *= 1 + upAmount * ny;                             // top faces lift, undersides sink
    shade *= 1 + frontAmount * nz;                          // faint front/back separation
    // The side step: |n| along the non-front horizontal axis, so the two returns
    // take the same value and the front face and the roof take none of it.
    if (sideAmount !== 0) shade *= 1 + sideAmount * Math.abs(sideAxisZ ? nz : nx);
    if (wrapAmount !== 0) {
      // How far this facet has turned off the form axis: the facet square to it
      // takes the top of the ramp, the ones folding away to either silhouette
      // take the bottom, and the pivot keeps the average where the flat zone
      // colour already was. Every facet of the barrel now holds its own value.
      const turn = nx * WRAP_DIR.x + nz * WRAP_DIR.z;
      shade *= 1 + wrapAmount * (turn - wrapPivot);
    }
    // One draw per facet, so a quad never splits. Off by default (see SHADE).
    if (jitterAmount !== 0) shade *= 1 + (next() - 0.5) * 2 * jitterAmount;

    color.copy(base).multiplyScalar(Math.max(0.18, shade));
    for (const i of group) for (let v = 0; v < 3; v += 1) color.toArray(colors, (i + v) * 3);
  }
  source.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  return source;
}

/** The one material every generated character shares. */
export function characterMaterial() {
  return new THREE.MeshStandardMaterial({
    vertexColors: true,
    flatShading: true,
    roughness: 0.92,
    metalness: 0.0,
    side: THREE.FrontSide,
  });
}

// ---------------------------------------------------------------------------
// Primitives. All of them accept `{ w, h, d }` in metres and are centred on the
// origin in x/z with y running from 0 (bottom) upward unless noted.
// ---------------------------------------------------------------------------

/**
 * Chamfered box: the reference style reads as boxes whose vertical edges are cut,
 * which is what stops them looking like Minecraft cubes.
 * @param {{w:number,h:number,d:number,bevel?:number,bevelTop?:number,bevelBottom?:number}} spec
 */
export function bevelBox(spec) {
  const { w, h, d } = spec;
  const bevel = spec.bevel ?? Math.min(w, d) * 0.16;
  const top = spec.bevelTop ?? 0;
  const bottom = spec.bevelBottom ?? 0;
  const ring = (halfW, halfD, y) => {
    const b = Math.min(bevel, halfW * 0.9, halfD * 0.9);
    return [
      [-halfW + b, y, -halfD], [halfW - b, y, -halfD],
      [halfW, y, -halfD + b], [halfW, y, halfD - b],
      [halfW - b, y, halfD], [-halfW + b, y, halfD],
      [-halfW, y, halfD - b], [-halfW, y, -halfD + b],
    ];
  };
  const rings = [
    { points: ring(w / 2 - bottom, d / 2 - bottom, 0) },
    { points: ring(w / 2, d / 2, Math.min(h * 0.5, bottom + 1e-4)) },
    { points: ring(w / 2, d / 2, Math.max(h * 0.5, h - top - 1e-4)) },
    { points: ring(w / 2 - top, d / 2 - top, h) },
  ];
  return loft(rings.map((r) => r.points));
}

/**
 * Tapered box: separate top and bottom footprints. Used for torsos, limbs, skirts.
 * @param {{wBottom:number,dBottom:number,wTop:number,dTop:number,h:number,bevel?:number,shearZ?:number}} spec
 */
export function taperBox(spec) {
  const bevel = spec.bevel ?? Math.min(spec.wBottom, spec.dBottom) * 0.14;
  const shear = spec.shearZ ?? 0;
  const ring = (halfW, halfD, y, z) => {
    const b = Math.min(bevel, halfW * 0.9, halfD * 0.9);
    return [
      [-halfW + b, y, z - halfD], [halfW - b, y, z - halfD],
      [halfW, y, z - halfD + b], [halfW, y, z + halfD - b],
      [halfW - b, y, z + halfD], [-halfW + b, y, z + halfD],
      [-halfW, y, z + halfD - b], [-halfW, y, z - halfD + b],
    ];
  };
  return loft([
    ring(spec.wBottom / 2, spec.dBottom / 2, 0, 0),
    ring(spec.wTop / 2, spec.dTop / 2, spec.h, shear),
  ]);
}

/**
 * N-sided prism swept through a list of rings, for coats, capes and skirts that
 * flare. Each ring is { y, rx, rz, z? }.
 * @param {Array<{y:number,rx:number,rz:number,z?:number}>} rings
 * @param {number} sides
 */
export function prism(rings, sides = 8) {
  const loops = rings.map((ring) => {
    const points = [];
    for (let i = 0; i < sides; i += 1) {
      const angle = (i / sides) * Math.PI * 2 + Math.PI / sides;
      points.push([Math.sin(angle) * ring.rx, ring.y, Math.cos(angle) * ring.rz + (ring.z ?? 0)]);
    }
    return points;
  });
  return loft(loops);
}

/**
 * Stack of slabs, each with its own footprint — boots, stepped hair, shoulder pads.
 * @param {Array<{h:number,w:number,d:number,y?:number,z?:number,bevel?:number}>} levels
 */
export function stepStack(levels) {
  const parts = [];
  let cursor = 0;
  for (const level of levels) {
    const geometry = bevelBox({ w: level.w, h: level.h, d: level.d, bevel: level.bevel });
    geometry.translate(0, level.y ?? cursor, level.z ?? 0);
    parts.push(geometry);
    cursor = (level.y ?? cursor) + level.h;
  }
  return mergeGeometries(parts);
}

/** A flat plate — lapels, aprons, brims, straps. Centred in x, y up from 0. */
export function plate(spec) {
  const geometry = bevelBox({
    w: spec.w,
    h: spec.h,
    d: spec.thickness ?? 0.018,
    bevel: spec.bevel ?? 0.008,
  });
  if (spec.taper) {
    const position = geometry.getAttribute("position");
    for (let i = 0; i < position.count; i += 1) {
      const t = position.getY(i) / spec.h;
      position.setX(i, position.getX(i) * (1 - (1 - spec.taper) * t));
    }
    position.needsUpdate = true;
  }
  return geometry;
}

/** Wedge / cone-ish shape for noses, crests, buckles. */
export function wedge(spec) {
  return taperBox({
    wBottom: spec.w, dBottom: spec.d,
    wTop: spec.wTop ?? spec.w * 0.25, dTop: spec.dTop ?? spec.d * 0.25,
    h: spec.h, bevel: spec.bevel ?? spec.w * 0.1,
  });
}

// ---------------------------------------------------------------------------
// Soft mass primitives — the body language of the target style.
//
// A character is one continuous lofted profile, so everything here works on
// horizontal RINGS. `wall` skins the quads between rings; give it a subset of
// side indices and it skins only that arc, which is how one colour region on the
// mass is emitted separately from the rest without splitting the silhouette.
// ---------------------------------------------------------------------------

function fromTriangles(vertices) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  return geometry;
}

/**
 * One horizontal ring of `sides` points. Side 0 sits just clockwise of the +Z
 * centre line, so the character's front is always between side `sides-1` and 0.
 * @param {number} sides
 * @param {{y:number,rx:number,rz:number,z?:number,phase?:number}} spec
 * @returns {number[][]}
 */
export function ring(sides, spec) {
  const points = [];
  const phase = spec.phase ?? 0;
  for (let i = 0; i < sides; i += 1) {
    const angle = (i / sides) * Math.PI * 2 + Math.PI / sides + phase;
    points.push([
      Math.sin(angle) * spec.rx,
      spec.y,
      Math.cos(angle) * spec.rz + (spec.z ?? 0),
    ]);
  }
  return points;
}

/**
 * Quads between consecutive rings. `indices` selects which sides to skin; quad
 * `i` spans ring vertex `i` to `i + 1`. Omit it for the whole closed loop.
 * @param {number[][][]} loops
 * @param {number[]} [indices]
 */
export function wall(loops, indices) {
  const sides = loops[0].length;
  const list = indices ?? Array.from({ length: sides }, (unused, i) => i);
  const vertices = [];
  const push = (point) => vertices.push(point[0], point[1], point[2]);
  for (let r = 0; r < loops.length - 1; r += 1) {
    const lo = loops[r];
    const hi = loops[r + 1];
    for (const raw of list) {
      const i = ((raw % sides) + sides) % sides;
      const j = (i + 1) % sides;
      // Counter-clockwise from OUTSIDE. The first cut of this wound every quad
      // inward: front-face culling then showed the inside of the far wall, which
      // mirrored every front feature left-right and inverted the baked shading.
      push(lo[i]); push(lo[j]); push(hi[i]);
      push(lo[j]); push(hi[j]); push(hi[i]);
    }
  }
  return fromTriangles(vertices);
}

/** Flat fan cap over one ring. `up` caps the top, otherwise the bottom. */
export function fan(loop, up) {
  const sides = loop.length;
  let cx = 0;
  let cz = 0;
  for (const point of loop) { cx += point[0]; cz += point[2]; }
  const centre = [cx / sides, loop[0][1], cz / sides];
  const vertices = [];
  const push = (point) => vertices.push(point[0], point[1], point[2]);
  for (let i = 0; i < sides; i += 1) {
    const j = (i + 1) % sides;
    push(centre);
    if (up) { push(loop[i]); push(loop[j]); } else { push(loop[j]); push(loop[i]); }
  }
  return fromTriangles(vertices);
}

/**
 * Lofted tube through a list of ring specs. The single workhorse for the body
 * mass, limbs, hair shells and hat crowns.
 * @param {Array<{y:number,rx:number,rz:number,z?:number}>} specs
 * @param {number} sides
 * @param {{indices?:number[], capBottom?:boolean, capTop?:boolean}} [options]
 */
export function tube(specs, sides, options = {}) {
  const loops = specs.map((spec) => ring(sides, spec));
  const pieces = [wall(loops, options.indices)];
  if (options.capBottom) pieces.push(fan(loops[0], false));
  if (options.capTop) pieces.push(fan(loops[loops.length - 1], true));
  return mergeGeometries(pieces);
}

/**
 * Gently faceted rounded blob — googly eyes, mitt hands, stub shoes, hair knots.
 * Authored with its base on y = 0 and centred in x/z, like every other builder,
 * and normalised so `rx`/`ry`/`rz` are true half-extents.
 * @param {{rx:number, ry?:number, rz?:number, sides?:number, stacks?:number}} spec
 */
export function ball(spec) {
  const sides = Math.max(5, Math.min(12, Math.round(spec.sides ?? 8)));
  const stacks = Math.max(2, Math.round(spec.stacks ?? 3));
  const rx = spec.rx;
  const ry = spec.ry ?? spec.rx;
  const rz = spec.rz ?? spec.rx;

  const angles = [];
  for (let s = 0; s <= stacks; s += 1) {
    angles.push(((s + 0.5) / (stacks + 1) - 0.5) * Math.PI);
  }
  const sinMax = Math.sin(angles[angles.length - 1]);
  let cosMax = 1e-6;
  for (const angle of angles) cosMax = Math.max(cosMax, Math.cos(angle));

  const specs = angles.map((angle) => ({
    y: ry + (ry * Math.sin(angle)) / sinMax,
    rx: (rx * Math.cos(angle)) / cosMax,
    rz: (rz * Math.cos(angle)) / cosMax,
  }));
  return tube(specs, sides, { capBottom: true, capTop: true });
}

/**
 * Side indices whose quads face the front (+Z), or the back with `back` set.
 * `width` is the fraction of the circumference the arc covers.
 */
export function arcIndices(sides, width, back = false) {
  const half = Math.PI * Math.max(0.02, Math.min(0.98, width));
  const list = [];
  for (let i = 0; i < sides; i += 1) {
    let angle = (2 * Math.PI * (i + 1)) / sides + (back ? Math.PI : 0);
    angle = Math.atan2(Math.sin(angle), Math.cos(angle));
    if (Math.abs(angle) <= half + 1e-6) list.push(i);
  }
  return list;
}

/** Every side index NOT in `list`, in ascending order. */
export function complementIndices(sides, list) {
  const taken = new Set(list.map((i) => ((i % sides) + sides) % sides));
  const out = [];
  for (let i = 0; i < sides; i += 1) if (!taken.has(i)) out.push(i);
  return out;
}

// ---------------------------------------------------------------------------
// Loft / merge helpers
// ---------------------------------------------------------------------------

/** Skin a stack of equal-length point loops into a closed solid. */
export function loft(loops) {
  const vertices = [];
  const indices = [];
  const sides = loops[0].length;
  for (const loop of loops) for (const point of loop) vertices.push(point[0], point[1], point[2]);

  for (let ring = 0; ring < loops.length - 1; ring += 1) {
    for (let side = 0; side < sides; side += 1) {
      const next = (side + 1) % sides;
      const a = ring * sides + side;
      const b = ring * sides + next;
      const c = (ring + 1) * sides + side;
      const d = (ring + 1) * sides + next;
      indices.push(a, c, b, b, c, d);
    }
  }
  const capBottom = vertices.length / 3;
  const first = loops[0];
  let cx = 0; let cz = 0;
  for (const point of first) { cx += point[0]; cz += point[2]; }
  vertices.push(cx / sides, first[0][1], cz / sides);

  const capTop = vertices.length / 3;
  const last = loops[loops.length - 1];
  cx = 0; cz = 0;
  for (const point of last) { cx += point[0]; cz += point[2]; }
  vertices.push(cx / sides, last[0][1], cz / sides);

  // FORK-FIX (LLMModeling M0): the side quads above face outward only when the
  // loop runs clockwise seen from +Y (signed xz area > 0, which is what
  // bevelBox's ring() emits), and the cap fans as originally written face
  // outward only for the OPPOSITE orientation — so bevelBox/plate caps were
  // inside-out and culled (roof plates showed the mass top through them).
  // Wind the caps from the loop's actual orientation so both agree.
  let signedArea = 0;
  for (let side = 0; side < sides; side += 1) {
    const p = last[side];
    const q = last[(side + 1) % sides];
    signedArea += p[0] * q[2] - q[0] * p[2];
  }
  const clockwiseFromAbove = signedArea > 0;
  for (let side = 0; side < sides; side += 1) {
    const next = (side + 1) % sides;
    const offset = (loops.length - 1) * sides;
    if (clockwiseFromAbove) {
      indices.push(capBottom, side, next);
      indices.push(capTop, offset + next, offset + side);
    } else {
      indices.push(capBottom, next, side);
      indices.push(capTop, offset + side, offset + next);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  return geometry.toNonIndexed();
}

/** Concatenate non-indexed geometries that share the same attribute set. */
export function mergeGeometries(list) {
  const usable = list.filter(Boolean).map((g) => (g.index ? g.toNonIndexed() : g));
  if (usable.length === 0) return new THREE.BufferGeometry();
  if (usable.length === 1) return usable[0];

  const hasColor = usable.every((g) => g.getAttribute("color"));
  let total = 0;
  for (const g of usable) total += g.getAttribute("position").count;

  const positions = new Float32Array(total * 3);
  const colors = hasColor ? new Float32Array(total * 3) : null;
  let offset = 0;
  for (const g of usable) {
    positions.set(g.getAttribute("position").array, offset * 3);
    if (colors) colors.set(g.getAttribute("color").array, offset * 3);
    offset += g.getAttribute("position").count;
  }
  const merged = new THREE.BufferGeometry();
  merged.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  if (colors) merged.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  merged.computeVertexNormals();
  return merged;
}

/** Mirror a geometry across x. Winding is flipped so normals stay outward. */
export function mirrorX(geometry) {
  const clone = geometry.clone();
  const position = clone.getAttribute("position");
  for (let i = 0; i < position.count; i += 1) position.setX(i, -position.getX(i));
  position.needsUpdate = true;
  // flip winding: swap vertex 1 and 2 of every triangle across every attribute
  for (const name of Object.keys(clone.attributes)) {
    const attribute = clone.getAttribute(name);
    const size = attribute.itemSize;
    const array = attribute.array;
    for (let i = 0; i < attribute.count; i += 3) {
      for (let k = 0; k < size; k += 1) {
        const a = (i + 1) * size + k;
        const b = (i + 2) * size + k;
        const tmp = array[a]; array[a] = array[b]; array[b] = tmp;
      }
    }
    attribute.needsUpdate = true;
  }
  clone.computeVertexNormals();
  return clone;
}

/** Count triangles in a geometry or an Object3D subtree. */
export function triangleCount(target) {
  let total = 0;
  const add = (geometry) => {
    if (!geometry) return;
    total += geometry.index ? geometry.index.count / 3 : geometry.getAttribute("position").count / 3;
  };
  if (target.isBufferGeometry) add(target);
  else target.traverse((object) => { if (object.isMesh && !object.userData.excludeFromExport) add(object.geometry); });
  return Math.round(total);
}
