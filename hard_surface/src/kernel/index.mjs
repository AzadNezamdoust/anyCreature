// The closed kernel an authored subject module is allowed to see.
//
// One import, one namespace:  `import * as K from "../../src/kernel/index.mjs"`.
// Everything is METRES and every frame is LOCAL; nothing here reads the clock,
// Math.random, the network or the filesystem, so the same module text always
// produces the same MeshGL (V2-TEST-PLAN 2).
//
// Solids are immutable wrappers over manifold-3d Manifolds: every transform
// and every boolean returns a NEW solid and leaves its inputs untouched, so a
// tool solid can be reused across twenty cuts.
import Module from "manifold-3d";

import * as profileFns from "./profile.mjs";
import { KernelError } from "./profile.mjs";

export { KernelError };
export const profile = Object.freeze({ ...profileFns });

/**
 * Smallest wall/bar a cut may leave behind for the STRICTEST class (limits.json styleFloor building).
 * WF-BLIND-R2 C9: a thinner residual is RECORDED on the result solid (`solid.thinCuts()`), never thrown;
 * the validator chain reports it as a V5_THIN gate row against the module's own class floor.
 */
export const MIN_FEAT = 0.06;

/** Float slop below which a residual wall is treated as an exact through-cut. */
const FLUSH_EPS = 1e-6;

let wasm = null;

/**
 * V5-1 bug (a): every Solid owns one manifold-3d WASM object and nothing ever freed it — a school-bus build leaks
 * ~11 MB of WASM heap, so a FIT / knob-attribution run of a few hundred builds grew the heap to its 4 GB cap
 * (thrash, then `Aborted()`). A Solid's manifold is deleted when the Solid is garbage-collected. Finalizers never
 * run inside synchronous code, so a manifold is never freed while build() (or a boolean) still holds its Solid.
 */
const owners = new WeakMap();   // manifold -> how many live Solids wrap it (assemblies re-wrap `x._m` in a new Solid)
const freeManifold = typeof FinalizationRegistry === "function"
  ? new FinalizationRegistry((m) => {
    const n = (owners.get(m) ?? 1) - 1;
    if (n > 0) { owners.set(m, n); return; }
    owners.delete(m);
    try { m.delete(); } catch { /* already gone */ }
  })
  : null;

/**
 * Boolean counter, for `scripts/bench-kernel.mjs` and the S2 measurement row.
 * A plain integer and nothing else: the kernel never reads a clock (the ms
 * column of V2-TEST-PLAN 5 is timed by the bench script, outside the kernel),
 * because determinism here is "same module text, same MeshGL".
 */
export const counters = { booleans: 0, thinCuts: 0 };

// ---------------------------------------------------------------------------
// WF-BLIND-R2 C14 — ONE gate configuration. The harness hands the kernel the
// configuration the prompt advertised and the chain measures with
// (kernel-chain.mjs gateConfig: the subject's class style floor), BEFORE build().
// Terra's pickup was told MIN_FEAT 0.04 m and the cut check enforced 0.06 m.
// ---------------------------------------------------------------------------

/** Deterministic FNV-1a digest of a JSON-able object (node and browser alike). */
export function configDigest(object) {
  const text = JSON.stringify(object);
  let h1 = 0x811c9dc5;
  let h2 = 0x01000193;
  for (let i = 0; i < text.length; i += 1) {
    const c = text.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 0x01000193) >>> 0;
    h2 = Math.imul(h2 ^ c, 0x811c9dc5) >>> 0;
  }
  return `${h1.toString(16).padStart(8, "0")}${h2.toString(16).padStart(8, "0")}`;
}

let gate = null;

/** Set (or with null, clear) the gate configuration the cut check reads. `minFeat` is required. */
export function configure(config) {
  if (config === null || config === undefined) { gate = null; return null; }
  if (!Number.isFinite(config.minFeat) || config.minFeat <= 0) throw new KernelError("BAD_ARG: configure needs a finite minFeat > 0");
  const { digest, ...body } = config;
  gate = Object.freeze({ ...body, digest: configDigest(body) });
  return gate;
}

/** The configuration the kernel is enforcing: `{ minFeat, digest, ... }`; unconfigured = the strictest floor, digest null. */
export function config() {
  return gate ?? { minFeat: MIN_FEAT, digest: null };
}

export function resetCounters() {
  counters.booleans = 0;
  counters.thinCuts = 0;
}

const NO_THIN = Object.freeze([]);
const mergeThin = (...lists) => {
  const out = lists.flatMap((l) => l ?? NO_THIN);
  return out.length === 0 ? NO_THIN : Object.freeze(out);
};

/**
 * Load the WASM. Idempotent, and every other call in this file throws until it
 * has resolved. Node and the browser both go through this one path.
 */
export async function init() {
  if (wasm) return;
  const loaded = await Module();
  loaded.setup();
  wasm = loaded;
}

function M() {
  if (!wasm) throw new KernelError("KERNEL_UNINIT: call `await K.init()` before any kernel call");
  return wasm;
}

function dims3(dims, what) {
  if (!Array.isArray(dims) || dims.length !== 3) throw new KernelError(`BAD_ARG: ${what} must be [w, h, d]`);
  return dims.map((v, i) => {
    if (typeof v !== "number" || !Number.isFinite(v) || v <= 0) {
      throw new KernelError(`BAD_ARG: ${what}[${i}] must be a finite number > 0, got ${JSON.stringify(v)}`);
    }
    return v;
  });
}

function vec3(v, what) {
  if (!Array.isArray(v) || v.length !== 3) throw new KernelError(`BAD_ARG: ${what} must be [x, y, z]`);
  return v.map((n, i) => {
    if (typeof n !== "number" || !Number.isFinite(n)) throw new KernelError(`BAD_ARG: ${what}[${i}] must be finite`);
    return n;
  });
}

function deg(value, what) {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new KernelError(`BAD_ARG: ${what} must be finite degrees`);
  return value;
}

/** An immutable solid. Never constructed directly by an author. */
export class Solid {
  constructor(manifold, thin = NO_THIN, cuts = NO_THIN) {
    this._m = manifold;
    if (freeManifold && manifold && typeof manifold.delete === "function") {
      owners.set(manifold, (owners.get(manifold) ?? 0) + 1);
      freeManifold.register(this, manifold);
    }
    // WF-BLIND-R2 C12 — every cut tool this solid was cut by (box + connected lumps), so a gate row can COUNT
    // recessed slots instead of trusting the item text.
    this._cuts = cuts;
    // WF-BLIND-R2 C9 — thin-cut records travel with the solid through every transform and boolean,
    // so the chain can name the PART a thin cut ended up in. Coordinates are the frame the cut was made in.
    this._thin = thin;
  }

  /** Translate by [x, y, z] metres. Returns a NEW solid. */
  at(v) { return new Solid(this._m.translate(vec3(v, "at")), this._thin, this._cuts); }

  /** Rotate about the local +Y axis, degrees, right-handed. NEW solid. */
  rotY(d) { return new Solid(this._m.rotate([0, deg(d, "rotY"), 0]), this._thin, this._cuts); }

  /** Rotate about the local +X axis, degrees. NEW solid. */
  rotX(d) { return new Solid(this._m.rotate([deg(d, "rotX"), 0, 0]), this._thin, this._cuts); }

  /** Rotate about the local +Z axis, degrees. NEW solid. */
  rotZ(d) { return new Solid(this._m.rotate([0, 0, deg(d, "rotZ")]), this._thin, this._cuts); }

  /** Mirror across the x = 0 plane. NEW solid. */
  mirrorX() { return new Solid(this._m.mirror([1, 0, 0]), this._thin, this._cuts); }

  /**
   * WF-BLIND-R2 C9 — every `K.cut` that left a residual wall thinner than MIN_FEAT somewhere in this
   * solid's history: `[{ code: "V5_THIN", side, remaining, tool: {min,max}, target: {min,max} }]`.
   */
  thinCuts() { return this._thin.map((t) => ({ ...t })); }

  /** WF-BLIND-R2 C12 — every `K.cut` tool applied in this solid's history: `[{ tool: {min,max}, lumps }]`. */
  cutTools() { return this._cuts.map((t) => ({ ...t })); }

  /** Enclosed volume in cubic metres. */
  volume() { return this._m.volume(); }

  /** World-axis-aligned bounds of this solid: `{min:[x,y,z], max:[x,y,z]}`. */
  aabb() {
    const box = this._m.boundingBox();
    return { min: [box.min[0], box.min[1], box.min[2]], max: [box.max[0], box.max[1], box.max[2]] };
  }

  /** manifold-3d status string; "NoError" is the only healthy value. */
  status() { return this._m.status(); }

  /** Topological genus: 0 = a ball, 1 = one through-hole, and so on. */
  genus() { return this._m.genus(); }

  /** Split into disconnected lumps. Length 1 means one connected solid. */
  decompose() { return this._m.decompose().map((m) => new Solid(m, this._thin, this._cuts)); }

  /** manifold-3d MeshGL (numProp / vertProperties / triVerts). */
  mesh() { return this._m.getMesh(); }

  /** Triangle count of this solid alone. */
  triCount() { return this._m.numTri(); }
}

export function isSolid(value) {
  return value instanceof Solid;
}

function unwrap(value, what) {
  if (!(value instanceof Solid)) throw new KernelError(`BAD_ARG: ${what} must be a kernel solid`);
  return value._m;
}

/**
 * Box with the v1 primitive frame (prims.js:5-8): x and z centred on the
 * origin, y running 0 (bottom) to h (top).
 */
export function box(dims) {
  const [w, h, d] = dims3(dims, "box dims");
  const cube = M().Manifold.cube([w, h, d], false);
  const solid = new Solid(cube.translate([-w / 2, 0, -d / 2]));
  cube.delete();
  return solid;
}

function crossSection(points, what) {
  const contour = profileFns.poly(points).map(([x, y]) => [x, y]);
  const cs = new (M().CrossSection)([contour], "Positive");
  if (cs.isEmpty()) throw new KernelError(`BAD_PROFILE: ${what} produced an empty cross-section`);
  return cs;
}

/**
 * Extrude a 2D profile along +Z, from z = 0 to z = depth.
 * `holes` are profiles in the same frame and are subtracted from the section.
 */
export function extrude(profileOrPoints, depth, { holes } = {}) {
  if (typeof depth !== "number" || !Number.isFinite(depth) || depth <= 0) {
    throw new KernelError(`BAD_ARG: extrude depth must be a finite number > 0, got ${JSON.stringify(depth)}`);
  }
  let section = crossSection(profileOrPoints, "extrude profile");
  if (holes) {
    if (!Array.isArray(holes)) throw new KernelError("BAD_ARG: extrude holes must be an array of profiles");
    for (const [i, hole] of holes.entries()) {
      const h = crossSection(hole, `hole ${i}`);
      const next = M().CrossSection.difference(section, h);
      h.delete();
      section.delete();
      section = next;
    }
  }
  const solid = new Solid(M().Manifold.extrude(section, depth));
  section.delete();   // V5-1: the cross-section is a temporary WASM object
  return solid;
}

/**
 * Revolve a 2D profile around the LOCAL +Y axis. The profile's x is the radius
 * (must be >= 0) and its y is the height, so a profile based at y = 0 gives a
 * solid based at y = 0. `segs` is the facet count around the full turn.
 */
export function revolve(profileOrPoints, segs = 16) {
  if (!Number.isInteger(segs) || segs < 3) throw new KernelError(`BAD_ARG: revolve segs must be an integer >= 3, got ${segs}`);
  const section = crossSection(profileOrPoints, "revolve profile");
  // manifold revolves around the section's Y and returns that axis as +Z;
  // -90 deg about X brings the axis of revolution back to the local +Y.
  const raw = M().Manifold.revolve(section, segs);
  section.delete();
  const solid = new Solid(raw.rotate([-90, 0, 0]));
  raw.delete();
  return solid;
}

/**
 * V5-2 — extrude a profile along +Z (z = 0..h) while scaling it about the profile origin (x = 0, y = 0) to `scaleTop`
 * at z = h: a number, or `[sx, sy]`, each >= 0 (0 closes to an apex). A frustum / tapered post / raked pillar.
 */
export function taper(profileOrPoints, h, scaleTop) {
  if (typeof h !== "number" || !Number.isFinite(h) || h <= 0) throw new KernelError(`BAD_ARG: taper h must be a finite number > 0, got ${JSON.stringify(h)}`);
  const scale = Array.isArray(scaleTop) ? scaleTop : [scaleTop, scaleTop];
  if (scale.length !== 2 || !scale.every((v) => typeof v === "number" && Number.isFinite(v) && v >= 0) || (scale[0] === 0) !== (scale[1] === 0)) {
    throw new KernelError(`BAD_ARG: taper scaleTop must be a number >= 0 or [sx, sy] (both 0 or both > 0), got ${JSON.stringify(scaleTop)}`);
  }
  const section = crossSection(profileOrPoints, "taper profile");
  const solid = new Solid(M().Manifold.extrude(section, h, 0, 0, scale));
  section.delete();
  return solid;
}

const isPoint = (v) => Array.isArray(v) && v.length === 3 && v.every((n) => typeof n === "number");

/**
 * V5-2 — convex hull (manifold-3d Manifold.hull) of solids and/or `[x, y, z]` points, passed as arguments or arrays.
 * Throws BAD_ARG when the hull is flat (all points on one plane). Deterministic: same inputs, same mesh.
 */
export function hull(...args) {
  const items = [];
  for (const a of args) {
    if (Array.isArray(a) && !isPoint(a)) items.push(...a);
    else items.push(a);
  }
  if (items.length === 0) throw new KernelError("BAD_ARG: hull needs solids or [x, y, z] points");
  const list = items.map((v, i) => (v instanceof Solid ? v._m : vec3(v, `hull point ${i}`)));
  const m = M().Manifold.hull(list);
  if (m.status() !== "NoError" || m.isEmpty() || m.volume() <= 1e-12) throw new KernelError("BAD_ARG: hull is flat or empty (need points off one plane)");
  return new Solid(m);
}

/**
 * V5-2 — a straight beam from `p0` to `p1` ([x, y, z]): the hull of its two end sections, each a `w` x `h` rectangle
 * square to the beam (`w` across it horizontally, `h` across it in the vertical plane; a vertical beam has w along x,
 * h along z). `w` / `h` may be `[atP0, atP1]` for a tapered arm. 12 triangles.
 */
export function beam(p0, p1, { w, h } = {}) {
  const a = vec3(p0, "beam p0");
  const b = vec3(p1, "beam p1");
  const pairOf = (v, what) => {
    const pr = Array.isArray(v) ? v : [v, v];
    if (pr.length !== 2 || !pr.every((n) => typeof n === "number" && Number.isFinite(n) && n > 0)) throw new KernelError(`BAD_ARG: beam ${what} must be > 0 or [atP0, atP1], got ${JSON.stringify(v)}`);
    return pr;
  };
  const [w0, w1] = pairOf(w, "w");
  const [h0, h1] = pairOf(h, "h");
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const len = Math.hypot(...d);
  if (len < 1e-9) throw new KernelError("BAD_ARG: beam p0 and p1 coincide");
  const ax = d.map((v) => v / len);
  // side = axis x up (horizontal); a vertical beam takes x
  let side = [ax[2], 0, -ax[0]];
  const sl = Math.hypot(...side);
  side = sl < 1e-9 ? [1, 0, 0] : side.map((v) => v / sl);
  const up = [side[1] * ax[2] - side[2] * ax[1], side[2] * ax[0] - side[0] * ax[2], side[0] * ax[1] - side[1] * ax[0]];
  const corners = (p, ww, hh) => [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([i, j]) => [0, 1, 2].map((k) => p[k] + (i * ww * side[k]) / 2 + (j * hh * up[k]) / 2));
  return hull([...corners(a, w0, h0), ...corners(b, w1, h1)]);
}

function countedBoolean(fn) {
  counters.booleans += 1;
  return fn();
}

function solidList(args, what) {
  const flat = args.flat();
  if (flat.length < 2) throw new KernelError(`BAD_ARG: ${what} needs at least two solids`);
  return flat.map((s, i) => unwrap(s, `${what} operand ${i}`));
}

const thinOf = (args) => mergeThin(...args.flat().map((s) => (s instanceof Solid ? s._thin : NO_THIN)));
const cutsOf = (args) => mergeThin(...args.flat().map((s) => (s instanceof Solid ? s._cuts : NO_THIN)));

/**
 * Subtract `b` from `a`. Inputs unchanged.
 * WF-BLIND-R2 C9: a cut that would leave less than MIN_FEAT of `a` standing on
 * any axis NO LONGER THROWS (one thin groove used to destroy the whole module
 * inside build()). The thinnest residual is recorded on the result
 * (`solid.thinCuts()`) and the validator chain reports it as a `V5_THIN` gate
 * row, with its location, against the module's class floor. The check is the
 * cheap one: the residual slabs of `a`'s bounding box outside `b`'s.
 */
export function cut(a, b) {
  const left = unwrap(a, "cut a");
  const right = unwrap(b, "cut b");
  const record = thinResidual(a.aabb(), b.aabb());
  if (record) counters.thinCuts += 1;
  const thin = record ? mergeThin(a._thin, b._thin, [record]) : mergeThin(a._thin, b._thin);
  const box = b.aabb();
  const cuts = mergeThin(a._cuts, [Object.freeze({ tool: { min: [...box.min], max: [...box.max] }, lumps: right.decompose().length })]);
  return new Solid(countedBoolean(() => M().Manifold.difference(left, right)), thin, cuts);
}

/** Union of two or more solids (arrays are flattened). Inputs unchanged. */
export function union(...solids) {
  return new Solid(countedBoolean(() => M().Manifold.union(solidList(solids, "union"))), thinOf(solids), cutsOf(solids));
}

/** Intersection of two or more solids (arrays are flattened). Inputs unchanged. */
export function intersect(...solids) {
  return new Solid(countedBoolean(() => M().Manifold.intersection(solidList(solids, "intersect"))), thinOf(solids), cutsOf(solids));
}

const AXES = ["x", "y", "z"];

/** The thinnest partial residual wall a cut leaves (under MIN_FEAT), or null. */
function thinResidual(a, b) {
  for (let i = 0; i < 3; i += 1) {
    const overlap = Math.min(a.max[i], b.max[i]) - Math.max(a.min[i], b.min[i]);
    if (overlap <= FLUSH_EPS) return null;     // the tool misses on this axis: no cut, no wall
  }
  let worst = null;
  for (let i = 0; i < 3; i += 1) {
    const residuals = [[`${AXES[i]}-`, b.min[i] - a.min[i]], [`${AXES[i]}+`, a.max[i] - b.max[i]]];
    for (const [side, thickness] of residuals) {
      if (thickness > FLUSH_EPS && thickness < config().minFeat - FLUSH_EPS && (!worst || thickness < worst.remaining)) {
        worst = { code: "V5_THIN", side, remaining: thickness, tool: { min: [...b.min], max: [...b.max] }, target: { min: [...a.min], max: [...a.max] } };
      }
    }
  }
  return worst ? Object.freeze(worst) : null;
}

/**
 * The author contract, in one place so `scripts/check-module.mjs` and `app.js`
 * enforce exactly the same thing: `meta` carries class/seed/palette and every
 * part is `{id (unique), solid, zone (a palette key)}`.
 * @returns {string[]} violations; empty means the module is well-formed.
 */
export function checkParts(meta, parts) {
  const bad = [];
  if (!meta || typeof meta !== "object") return ["meta: missing export"];
  if (typeof meta.class !== "string" || meta.class === "") bad.push("meta.class: missing string");
  if (meta.seed === undefined || meta.seed === null) bad.push("meta.seed: missing");
  const palette = meta.palette;
  if (!palette || typeof palette !== "object" || Object.keys(palette).length === 0) bad.push("meta.palette: missing object");
  if (!Array.isArray(parts) || parts.length === 0) return [...bad, "build(): must return a non-empty array of parts"];
  const seen = new Set();
  for (const [i, part] of parts.entries()) {
    const where = `part ${i}`;
    if (!part || typeof part !== "object") { bad.push(`${where}: not an object`); continue; }
    if (typeof part.id !== "string" || part.id === "") bad.push(`${where}: id must be a non-empty string`);
    else if (seen.has(part.id)) bad.push(`${where}: duplicate id "${part.id}"`);
    else seen.add(part.id);
    if (!isSolid(part.solid)) bad.push(`${where} (${part.id}): solid must come from the kernel`);
    if (typeof part.zone !== "string" || !(palette && part.zone in palette)) {
      bad.push(`${where} (${part.id}): zone "${part.zone}" is not a key of meta.palette`);
    }
  }
  return bad;
}

/**
 * Pure helper: call `fn(i, i * pitch)` for i in 0..n-1 and collect the results.
 * Whatever `fn` returns is what you get - solids, parts, arrays.
 */
export function repeat(n, pitch, fn) {
  if (!Number.isInteger(n) || n < 0) throw new KernelError(`BAD_ARG: repeat n must be an integer >= 0, got ${n}`);
  if (typeof pitch !== "number" || !Number.isFinite(pitch)) throw new KernelError("BAD_ARG: repeat pitch must be finite");
  if (typeof fn !== "function") throw new KernelError("BAD_ARG: repeat fn must be a function");
  const out = [];
  for (let i = 0; i < n; i += 1) out.push(fn(i, i * pitch));
  return out;
}

/**
 * Assembly helpers for repeated hard-surface topology (WORKFLOW-V3 §7.9):
 * `K.assemble.grate / landing / flight / ladder / frame`, each returning parts
 * laid out to pass the buildability gates by construction. See assemblies.mjs.
 */
export * as assemble from "./assemblies.mjs";
/** WF-R3 R3-B — `K.span({ x: [lo, hi], y: [lo, hi], z: [lo, hi] })`, the metre bounds the vehicle helpers take. */
export { span } from "./assemblies.mjs";
