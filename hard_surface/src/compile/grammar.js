// CGA-lite facade grammar (PLAN 1.1, 02:§CGA, 08:G6).
//
// The author never places a window. They declare a facade on one face of one
// mass, split that face into bands, tile a band into cells, and say what an
// element named `bay` (or `base`, or `door`) is. This file turns that into
// ordinary spec parts with real `attach` blocks, which is the whole point: V2
// measures their contact, V3 roots them, V5 measures their thickness and V7
// measures their scale, exactly as if a human had typed each one.
//
// ORDER (08:G6): the grammar runs AFTER attach + repeat/mirror expansion, and
// reads the EXPANDED solved set. That is the only order in which a balcony
// repeated up +Y can suppress the tiles it actually covers.
import * as THREE from "three";

import { FACE_FRAMES } from "./resolve.js";
// Limits reach the compiler as a plain JSON import — `src/validate/index.js`
// does the same (`import DEFAULT_LIMITS from "./limits.json"`), and importing
// the module instead would close a cycle (validate/index.js re-exports `solve`
// from compile/build.js, which imports this file).
import DEFAULT_LIMITS from "../validate/limits.json" with { type: "json" };

/** A tile whose face rectangle is covered becomes this — a blank wall panel. */
const OCCLUDED_NAME = "wall";
/** A part must stand this far proud of the face before it counts as an occluder. */
const PROTRUSION_EPS = 0.01;
/** Glass sits this far proud of the reveal so V6 cannot call it a duplicate. */
const GLASS_PROUD = 0.03;

export const ELEMENT_NAMES = Object.freeze([
  "window", "door", "storefront", "sill", "lintel", "band",
]);

/** Region names that are pure geometry-free structure. */
export const EMPTY_REGIONS = Object.freeze(["pier", "wall", "base", "cornice", "spandrel"]);

// ---------------------------------------------------------------------------
// Split rules
// ---------------------------------------------------------------------------

/**
 * Resolve one `rule` against an extent in metres.
 *
 * Entries: `[name, size]`, `[name, size, "*N"]` (N copies of `size`), or
 * `[name, "~"]` (fill what is left; several `~` entries share it equally).
 *
 * @param {Array} rule
 * @param {number} extent metres available
 * @returns {Array<{name:string, start:number, size:number}>} low edge first
 */
export function resolveRule(rule, extent) {
  const slots = [];
  let fixed = 0;
  let fillers = 0;

  for (const entry of rule ?? []) {
    const [name, size, repeat] = entry;
    const count = typeof repeat === "string" && repeat.startsWith("*")
      ? Math.max(1, Math.trunc(Number(repeat.slice(1))))
      : 1;
    for (let k = 0; k < count; k += 1) {
      if (size === "~") { slots.push({ name, size: null }); fillers += 1; }
      else { slots.push({ name, size: Number(size) }); fixed += Number(size); }
    }
  }

  const share = fillers > 0 ? Math.max(0, extent - fixed) / fillers : 0;
  let cursor = 0;
  const out = [];
  for (const slot of slots) {
    const size = slot.size === null ? share : slot.size;
    out.push({ name: slot.name, start: cursor, size });
    cursor += size;
  }
  return out;
}

// ---------------------------------------------------------------------------
// The face rectangle
// ---------------------------------------------------------------------------

const AXIS_INDEX = Object.freeze({ "+X": 0, "-X": 0, "+Y": 1, "-Y": 1, "+Z": 2, "-Z": 2 });

/** Half-extent of a box with `dims` along a signed local axis name. */
function halfAlong(dims, axisName) {
  return dims[AXIS_INDEX[axisName]] / 2;
}

function axisNameOf(vector) {
  for (const [name, frame] of Object.entries(FACE_FRAMES)) {
    const n = frame.n;
    if (n[0] === vector[0] && n[1] === vector[1] && n[2] === vector[2]) return name;
  }
  throw new Error(`grammar: ${JSON.stringify(vector)} is not a signed axis`);
}

/**
 * The (u, v) rectangle of a facade's host face, in metres, plus the helpers the
 * emitter needs to turn a metre position back into an `attach.uv`.
 */
function faceRect(host, face) {
  const frame = FACE_FRAMES[face];
  const halfU = halfAlong(host.dims, axisNameOf(frame.u));
  const halfV = halfAlong(host.dims, axisNameOf(frame.v));
  const halfN = halfAlong(host.dims, face);
  return { frame, halfU, halfV, halfN, U: 2 * halfU, V: 2 * halfV };
}

// ---------------------------------------------------------------------------
// Occlusion (08:G6)
// ---------------------------------------------------------------------------

/**
 * Footprints, in face (u, v) metres, of everything already solved that stands
 * PROUD of this face — a balcony, a landing, a stair, a mass that steps forward.
 * A part merely flush with the face (the next terrace house, sharing the same
 * z extent) is not an occluder: it hides nothing.
 *
 * MVP-STUB: each candidate is reduced to the axis-aligned box of its world AABB
 * transformed into host-local space, so a rotated occluder over-reports its
 * footprint and can blank one more tile than it truly covers. Exact OBB
 * clipping is the same work V6 defers.
 */
function occluderRects(host, face, rect, parts, skipIds) {
  const inverse = new THREE.Matrix4().copy(host.matrix).invert();
  const frame = rect.frame;
  const u = new THREE.Vector3().fromArray(frame.u);
  const v = new THREE.Vector3().fromArray(frame.v);
  const n = new THREE.Vector3().fromArray(frame.n);
  const centre = new THREE.Vector3(0, host.dims[1] / 2, 0);

  const out = [];
  const corner = new THREE.Vector3();
  for (const part of parts) {
    if (part.id === host.id || skipIds.has(part.id)) continue;
    if (!part.aabb) continue;

    let minU = Infinity; let maxU = -Infinity;
    let minV = Infinity; let maxV = -Infinity;
    let maxN = -Infinity;
    for (let bit = 0; bit < 8; bit += 1) {
      corner.set(
        bit & 1 ? part.aabb.max[0] : part.aabb.min[0],
        bit & 2 ? part.aabb.max[1] : part.aabb.min[1],
        bit & 4 ? part.aabb.max[2] : part.aabb.min[2],
      ).applyMatrix4(inverse).sub(centre);
      const cu = corner.dot(u);
      const cv = corner.dot(v);
      const cn = corner.dot(n);
      if (cu < minU) minU = cu;
      if (cu > maxU) maxU = cu;
      if (cv < minV) minV = cv;
      if (cv > maxV) maxV = cv;
      if (cn > maxN) maxN = cn;
    }

    if (maxN <= rect.halfN + PROTRUSION_EPS) continue;                  // flush or behind
    if (maxU <= -rect.halfU || minU >= rect.halfU) continue;            // off the face
    if (maxV <= -rect.halfV || minV >= rect.halfV) continue;

    out.push({
      id: part.id,
      proud: maxN - rect.halfN,
      u0: minU + rect.halfU, u1: maxU + rect.halfU,
      v0: minV + rect.halfV, v1: maxV + rect.halfV,
    });
  }
  return out;
}

function overlaps(cell, rect) {
  return cell.u0 < rect.u1 - 1e-6 && cell.u1 > rect.u0 + 1e-6
    && cell.v0 < rect.v1 - 1e-6 && cell.v1 > rect.v0 + 1e-6;
}

/**
 * `rect` shrunk by `margin` on all four sides, or `null` when it is too small to
 * survive the inset. The margin is the whole point of the PROTRUSION rule
 * (Fable ruling 2026-09-12): a sill, a valance or a string course skimming the
 * edge must not blank anything, so only occluders that reach into the INTERIOR
 * count.
 */
function insetCell(cell, margin) {
  const u0 = cell.u0 + margin;
  const u1 = cell.u1 - margin;
  const v0 = cell.v0 + margin;
  const v1 = cell.v1 - margin;
  if (u1 <= u0 || v1 <= v0) return null;
  return { u0, u1, v0, v1 };
}

// ---------------------------------------------------------------------------
// Cells
// ---------------------------------------------------------------------------

/**
 * Split one facade's face into cells. Exported so `test/grammar.test.js` can
 * assert the tiling without compiling geometry.
 * @returns {Array<{name:string, id:string, u0:number,u1:number,v0:number,v1:number,
 *                  row:string, col:string}>}
 */
export function facadeCells(facade, hostDims) {
  const rect = faceRect({ dims: hostDims }, facade.face);
  const splitAxis = (facade.split?.axis ?? "Y").toUpperCase();
  const alongV = splitAxis === "Y";
  const bands = resolveRule(facade.split?.rule, alongV ? rect.V : rect.U);

  const cells = [];
  bands.forEach((band, bandIndex) => {
    const row = `${band.name}${bandIndex + 1}`;
    const tile = facade.tile?.[band.name];
    const bandExtent = alongV ? rect.U : rect.V;
    const columns = tile
      ? resolveRule(tile.rule, bandExtent)
      : [{ name: band.name, start: 0, size: bandExtent }];

    columns.forEach((column, columnIndex) => {
      const col = `${column.name}${columnIndex + 1}`;
      const u = alongV
        ? { u0: column.start, u1: column.start + column.size }
        : { u0: band.start, u1: band.start + band.size };
      const v = alongV
        ? { v0: band.start, v1: band.start + band.size }
        : { v0: column.start, v1: column.start + column.size };
      cells.push({ name: column.name, row, col, id: `${facade.id}/${row}/${col}`, ...u, ...v });
    });
  });
  return cells;
}

// ---------------------------------------------------------------------------
// Element emission
// ---------------------------------------------------------------------------

/**
 * Element dims in the CHILD's local frame.
 *
 * SEAT B FIX (M2): an element is authored in FACE space — `w` across the face,
 * `h` up it, `depth` into it — but `resolve.js` never rotates a child: it only
 * spins it about the attach normal. So the emitted `dims` must already be the
 * child's own [x, y, z] extents. On a +Z/-Z face those coincide, which is why
 * the facade demo looked right; on a +X/-X face the face-space `w` is the world
 * Z extent, and emitting [w, h, depth] made every side window a metre-wide slab
 * poking out of the wall. On a +Y/-Y face the face-space `h` is the world Z
 * extent. This helper is the whole mapping, and every emitter below goes
 * through it.
 */
function faceDims(face, w, h, depth) {
  if (face === "+X" || face === "-X") return [depth, h, w];
  if (face === "+Y" || face === "-Y") return [w, depth, h];
  return [w, h, depth];
}

/**
 * The opening (`window` / `door` / `storefront`) `emitCell` would place in this
 * cell, in face metres — or `null` when the region names no opening. Both the
 * emitter and the occlusion test go through this, so the rectangle that gets
 * tested is by construction the rectangle that gets built.
 */
function openingOf(facade, cell) {
  const recipe = facade.elements?.[cell.name];
  if (!recipe) return null;
  const opening = recipe.window ?? recipe.door ?? recipe.storefront ?? null;
  if (!opening) return null;
  const kind = recipe.window ? "window" : recipe.door ? "door" : "storefront";
  const w = Number(opening.dims?.[0] ?? (cell.u1 - cell.u0) * 0.5);
  const h = Number(opening.dims?.[1] ?? (cell.v1 - cell.v0) * 0.5);
  // A window is centred in its bay; a door or a storefront stands on the cell's
  // own floor, which is what makes `base` a ground-floor band.
  const vCentre = kind === "window" ? (cell.v0 + cell.v1) / 2 : cell.v0 + h / 2;
  return { recipe, opening, kind, w, h, cu: (cell.u0 + cell.u1) / 2, vCentre };
}

/**
 * The rectangle an occluder has to reach to blank this tile (Fable ruling
 * 2026-09-12): the ELEMENT footprint, not the whole cell. A tall ground band
 * whose storefront tops out well below the band's head must not be blanked by
 * an awning hung in the empty wall above it.
 *
 * The rect runs from the tile floor to the opening's head, not from the
 * opening's own foot: a deck, a landing or a stair standing proud across the
 * approach to the opening still blanks it (that is the balcony case the
 * grammar exists to handle), while anything above the head does not.
 * Returns `null` for a tile with no opening — nothing to blank.
 */
function elementRect(facade, cell) {
  const m = openingOf(facade, cell);
  if (m === null) return null;
  return {
    u0: m.cu - m.w / 2,
    u1: m.cu + m.w / 2,
    v0: Math.min(cell.v0, m.vCentre - m.h / 2),
    v1: m.vCentre + m.h / 2,
  };
}

function centreUv(cell, rect) {
  return [
    ((cell.u0 + cell.u1) / 2) / rect.U,
    ((cell.v0 + cell.v1) / 2) / rect.V,
  ];
}

function clamp01(value) {
  return Math.max(0, Math.min(1, value));
}

/**
 * One cell's elements. Every part comes back with a real `attach` onto the
 * facade host, so nothing downstream needs to know the grammar exists.
 */
function emitCell(facade, cell, rect, spec) {
  const recipe = facade.elements?.[cell.name];
  if (!recipe) return [];

  const host = facade.on;
  const face = facade.face;
  const out = [];
  const [cu] = centreUv(cell, rect);
  const cellW = cell.u1 - cell.u0;
  const cellH = cell.v1 - cell.v0;

  const metrics = openingOf(facade, cell);

  if (metrics) {
    const { opening, kind, w, h } = metrics;
    const inset = Number(opening.inset ?? 0.1);
    const vCentre = metrics.vCentre / rect.V;
    out.push({
      id: `${cell.id}/${kind}`,
      prim: "box",
      dims: faceDims(face, w, h, inset + GLASS_PROUD),
      zone: opening.zone ?? facade.zone ?? spec.parts[0].zone,
      role: kind === "storefront" ? "window" : kind,
      attach: {
        to: host, face, uv: [clamp01(cu), clamp01(vCentre)],
        contact: "socket", embed: inset,
      },
      grammar: { facade: facade.id, cell: cell.id, element: kind },
    });

    const openingBottom = (Number(vCentre) * rect.V) - h / 2;

    if (opening.sill !== undefined) {
      const sill = Number(opening.sill);
      out.push({
        id: `${cell.id}/sill`,
        prim: "plate",
        dims: faceDims(face, w + 2 * sill, Math.max(sill, 0.06), inset + sill),
        zone: opening.sillZone ?? facade.trimZone ?? opening.zone ?? spec.parts[0].zone,
        role: "sill",
        attach: {
          to: host, face, uv: [clamp01(cu), clamp01(openingBottom / rect.V)],
          contact: "flush", embed: inset, align: "top",
        },
        grammar: { facade: facade.id, cell: cell.id, element: "sill" },
      });
    }

    if (opening.lintel !== undefined) {
      const top = openingBottom + h;
      const arch = opening.lintel === "arch";
      // MVP-STUB: an arch head is a `wedge`, not a half-round. A true arch needs
      // an XY-plane extruder (geom.prism only extrudes along +Y), which is more
      // prim vocabulary than M2 is allowed to add. The brief permits the box
      // approximation; the wedge at least loses the square shoulders.
      out.push({
        id: `${cell.id}/lintel`,
        prim: arch ? "wedge" : "plate",
        dims: arch ? faceDims(face, w, w / 2, inset + 0.06) : faceDims(face, w + 0.12, 0.14, inset + 0.06),
        zone: opening.lintelZone ?? facade.trimZone ?? spec.parts[0].zone,
        role: "lintel",
        attach: {
          to: host, face, uv: [clamp01(cu), clamp01(top / rect.V)],
          contact: "flush", embed: inset, align: "bottom",
        },
        grammar: { facade: facade.id, cell: cell.id, element: "lintel" },
      });
    }

    if (kind === "storefront" && Array.isArray(recipe.storefront.awning)) {
      const [aw, ah, ad] = recipe.storefront.awning.map(Number);
      out.push({
        id: `${cell.id}/awning`,
        prim: "wedge",
        dims: faceDims(face, aw, ah, ad),
        zone: recipe.storefront.awningZone ?? recipe.storefront.zone ?? spec.parts[0].zone,
        role: "awning",
        attach: {
          to: host, face, uv: [clamp01(cu), clamp01((openingBottom + h) / rect.V)],
          contact: "flush", embed: 0.05, align: "bottom",
        },
        grammar: { facade: facade.id, cell: cell.id, element: "awning" },
      });
    }
  }

  if (recipe.band !== undefined) {
    const band = recipe.band;
    out.push({
      id: `${cell.id}/band`,
      prim: "plate",
      dims: faceDims(face, cellW, Math.max(Number(band.h ?? cellH), 0.06), Number(band.depth ?? 0.16)),
      zone: band.zone ?? facade.trimZone ?? spec.parts[0].zone,
      role: band.role ?? "cornice",
      attach: {
        to: host, face,
        uv: [clamp01(cu), clamp01(((cell.v0 + cell.v1) / 2) / rect.V)],
        contact: "flush", embed: 0.06,
      },
      grammar: { facade: facade.id, cell: cell.id, element: "band" },
    });
  }

  return out;
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

/**
 * Run every facade in `spec.facades` against the solved set.
 *
 * @param {object} spec the spec AFTER composite expansion
 * @param {{parts:Array<object>, byId:Map<string,object>}} solved
 * @returns {{parts:Array<object>, tiles:Array<object>}} `parts` are ordinary
 *   spec parts to be solved and appended; `tiles` is the per-cell record
 *   (including `occludedBy`) that `solved.json` carries for the studio overlay.
 */
export function runGrammar(spec, solved, limits = DEFAULT_LIMITS) {
  const derived = [];
  const tiles = [];
  if (!Array.isArray(spec.facades)) return { parts: derived, tiles };
  const minProud = Number(limits?.occludeMinProud ?? DEFAULT_LIMITS.occludeMinProud);
  const edgeMargin = Number(limits?.occludeEdgeMargin ?? DEFAULT_LIMITS.occludeEdgeMargin);

  const skipIds = new Set();
  for (const part of solved.parts) if (part.grammar) skipIds.add(part.id);

  for (const facade of spec.facades) {
    const host = solved.byId.get(facade.on);
    if (!host) continue;                       // V0 already reported it
    const rect = faceRect(host, facade.face);
    const cells = facadeCells(facade, host.dims);
    const occluders = facade.occlude === false
      ? []
      : occluderRects(host, facade.face, rect, solved.parts, skipIds);

    for (const cell of cells) {
      // OCCLUSION IS PROTRUSION, NOT AREA (Fable ruling 2026-09-12), AND IT IS
      // TESTED AGAINST THE ELEMENT, NOT THE CELL (Fable ruling 2026-09-12, 2nd).
      // A tile is blanked iff it HAS an element and SOME single occluder both
      // (a) stands at least `minProud` off the face and (b) reaches into that
      // element's rectangle past `edgeMargin` on every side. Area/union coverage
      // is gone: a fire escape's stringers together covered 40% of a bay without
      // standing in front of anything. The cell rectangle is gone too: a 4 m
      // ground band whose storefront tops out at 2.8 m had its glass blanked by
      // an awning hung in the empty metre above it. Depth is what hides glass,
      // and only glass can be hidden.
      const target = elementRect(facade, cell);
      const inset = target === null ? null : insetCell(target, edgeMargin);
      const hits = inset === null
        ? []
        : occluders.filter((r) => r.proud >= minProud - 1e-9 && overlaps(inset, r));
      if (hits.length > 0) {
        // `occludedBy` names the DEEPEST qualifying occluder.
        let hit = hits[0];
        for (const candidate of hits) if (candidate.proud > hit.proud) hit = candidate;
        tiles.push({ ...cell, name: OCCLUDED_NAME, occludedBy: hit.id });
        continue;
      }
      tiles.push({ ...cell, occludedBy: null });
      // A region with no `elements` entry emits nothing — that is what makes
      // pier / wall / base / cornice structural rather than decorative. A
      // `cornice` that DOES name a `band` gets its plate.
      derived.push(...emitCell(facade, cell, rect, spec));
    }
  }

  return { parts: derived, tiles };
}
