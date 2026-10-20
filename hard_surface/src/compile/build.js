// spec -> solved parts -> ONE merged, flat-shaded, vertex-coloured geometry.
//
// Compile order is fixed (08:G6): expand composites -> resolve attach ->
// expand repeat/mirror -> run the facade grammar with occlusion on the EXPANDED
// set -> solve the derived parts -> merge -> paint.
//
// The grammar runs last because that is the only order in which a balcony
// repeated up +Y can suppress the tiles it actually covers. Its output is
// ordinary spec parts, so `compile()` hands back the EFFECTIVE spec (authored
// parts, composites expanded, derived facade parts appended) and every
// validator downstream reads that, not the file the author wrote.
//
// Determinism: the only entropy is `rng("<seed>:<partId>")` from the geom fork.
// Nothing reads the clock, Math.random, or any host property.
import * as THREE from "three";

import { mergeGeometries, paint, triangleCount } from "../geom.js";
import { buildPrim, PRIM_GENUS } from "../prims.js";
import { resolveAttach, resolveGround } from "./resolve.js";
import { expand } from "./expand.js";
import { expandParts } from "./composites.js";
import { runGrammar } from "./grammar.js";

/**
 * Resolve every part to a world matrix. Pure maths — no geometry is built here,
 * so the validators can read the layout before a vertex exists.
 * @param {object} spec
 * @returns {{parts:Array<object>, byId:Map<string,object>, spec:object, tiles:Array}}
 *   `spec` is the EFFECTIVE spec described above.
 */
export function solve(spec) {
  const parts = [];
  const byId = new Map();
  /** specId -> EVERY solved instance of it, in emission order. Instance 0 is the anchor. */
  const instancesById = new Map();

  const usedIds = new Set();
  // MVP-STUB: a part that is BOTH expanded per parent instance AND carries its
  // own `repeat`/`mirror` can generate the same `#k` twice (group 1's anchor and
  // group 0's first repeat are both `post#1`). The `@n` tail is the tie-break;
  // every simple case — the ones the DSL doc shows — is untouched by it.
  const uniqueId = (id) => {
    if (!usedIds.has(id)) { usedIds.add(id); return id; }
    let n = 2;
    while (usedIds.has(`${id}@${n}`)) n += 1;
    usedIds.add(`${id}@${n}`);
    return `${id}@${n}`;
  };

  const solveOne = (part) => {
    const hosts = [];
    if (part.attach) {
      const all = instancesById.get(part.attach.to);
      if (!all || all.length === 0) {
        throw new Error(`solve: part "${part.id}" attaches to unknown or later part "${part.attach.to}"`);
      }
      // M6 gap 2: a child of a `repeat`ed or `mirror`ed parent is expanded ONCE
      // PER PARENT INSTANCE by default — that is what puts a railing on every
      // repeated balcony and a hub in every mirrored tyre from one authored
      // part. `"instance": 0` opts out, back to the anchor.
      //
      // `groupAnchor` is what keeps "the anchor" meaningful once the chain is
      // more than one deep: an instance is a group anchor when it is the first
      // of the copies its OWN repeat/mirror made for one inherited host. So
      // railing_open's top rail (`instance: 0`) sits on post 0 — but on post 0
      // OF EVERY BALCONY, not on post 0 of the first balcony alone.
      hosts.push(...(part.attach.instance === 0 ? all.filter((p) => p.groupAnchor) : all));
    } else {
      hosts.push(null);
    }

    for (const parent of hosts) {
      const placement = parent ? resolveAttach(parent, part) : resolveGround();
      // A per-instance child carries its parent instance's suffix (`#k`, `~m`)
      // so `rail#1` reads as "the rail on balcony#1" and stays unique.
      const suffix = parent && part.attach ? parent.id.slice(part.attach.to.length) : "";

      const instances = expand(
        { id: `${part.id}${suffix}`, matrix: placement.matrix },
        part,
        parent,
        parent ? (uv) => resolveAttach(parent, part, { uvOverride: uv }) : undefined,
      );

      let first = true;
      for (const instance of instances) {
        const solved = {
          id: uniqueId(instance.id),
          specId: part.id,
          prim: part.prim,
          dims: [...part.dims],
          matrix: instance.matrix,
          zone: part.zone,
          role: part.role ?? null,
          parentId: parent ? parent.id : null,
          contact: placement.contact,
          embed: placement.embed,
          face: placement.face,
          genus: PRIM_GENUS[part.prim] ?? 0,
          worldRepeatAxis: instance.worldRepeatAxis,
          grammar: part.grammar ?? null,
          triCount: 0,
          aabb: null,
          groupAnchor: first,      // not serialised; see the hosts comment above
          specPart: part,          // not serialised; carries optional prim options
        };
        first = false;
        parts.push(solved);
        if (!byId.has(part.id)) byId.set(part.id, solved);   // instance 0 is the anchor
        if (!instancesById.has(part.id)) instancesById.set(part.id, []);
        instancesById.get(part.id).push(solved);
      }
    }
  };

  // `roots` is shared by both expansion passes so a facade-derived part may
  // still name a composite the authored pass expanded (M6 gap 1).
  const roots = new Map();
  const authored = expandParts(spec.parts, roots);
  for (const part of authored.parts) solveOne(part);

  // The grammar needs world AABBs to decide occlusion, and compile() has not
  // built geometry yet — so give it the box the solver already knows about.
  for (const part of parts) if (!part.aabb) part.aabb = boxAabb(part);

  const grammar = runGrammar({ ...spec, parts: authored.parts }, { parts, byId });
  const derived = expandParts(grammar.parts, roots);
  for (const part of derived.parts) solveOne(part);

  return {
    parts,
    byId,
    instancesById,
    tiles: grammar.tiles,
    spec: {
      ...spec,
      parts: [...authored.parts, ...derived.parts],
      composites: [...authored.composites, ...derived.composites],
    },
  };
}

/** World AABB of a solved part's declared box, before any vertex exists. */
function boxAabb(part) {
  const half = new THREE.Vector3(part.dims[0] / 2, part.dims[1] / 2, part.dims[2] / 2);
  const box = new THREE.Box3();
  const corner = new THREE.Vector3();
  for (let bit = 0; bit < 8; bit += 1) {
    corner.set(
      bit & 1 ? half.x : -half.x,
      bit & 2 ? 2 * half.y : 0,
      bit & 4 ? half.z : -half.z,
    ).applyMatrix4(part.matrix);
    box.expandByPoint(corner);
  }
  return { min: box.min.toArray(), max: box.max.toArray() };
}

/**
 * Full compile: solved parts, one merged geometry, bounds and triangle count.
 * @param {object} spec
 * @returns {{solved:object, geometry:THREE.BufferGeometry, spec:object}}
 */
export function compile(spec) {
  const solvedSet = solve(spec);
  const { parts } = solvedSet;
  const palette = spec.palette ?? {};
  const pieces = [];

  for (const part of parts) {
    const raw = buildPrim(part.prim, part.dims, part.specPart);
    const painted = paint(raw, palette[part.zone] ?? "#ff00ff", { seed: `${spec.seed}:${part.id}` });
    painted.applyMatrix4(part.matrix);
    painted.computeBoundingBox();
    const box = painted.boundingBox;
    part.aabb = { min: box.min.toArray(), max: box.max.toArray() };
    part.triCount = triangleCount(painted);
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
    // M0-FIX: app.js frameTarget() projects the eight AABB corners and needs the
    // raw extremes; without these the capture path threw before ever rendering.
    min: box.min.toArray().map(round),
    max: box.max.toArray().map(round),
  };

  return {
    geometry,
    spec: solvedSet.spec,
    solved: {
      subject: spec.subject,
      seed: spec.seed,
      tiles: solvedSet.tiles,
      parts: parts.map((p) => ({
        id: p.id,
        specId: p.specId,
        prim: p.prim,
        dims: p.dims,
        matrix: p.matrix.toArray(),
        zone: p.zone,
        role: p.role,
        parentId: p.parentId,
        contact: p.contact,
        embed: p.embed,
        face: p.face,
        genus: p.genus,
        grammar: p.grammar,
        triCount: p.triCount,
        aabb: p.aabb,
        worldRepeatAxis: p.worldRepeatAxis,
      })),
      bounds,
      triangles: triangleCount(geometry),
    },
  };
}

/** 6 decimals: enough for millimetres, short enough that solved.json diffs read. */
function round(value) {
  return Math.round(value * 1e6) / 1e6;
}
