// The V2 validator chain — the one that runs on KERNEL SOLIDS instead of on a
// spec's AABBs (V2-TEST-PLAN §3). `src/validate/index.js` and every `v*.js`
// beside it are the v1 chain and are left untouched; this is a sibling.
//
// Contract, identical to `index.js` so the repair seat never learns a second
// format:
//   {pass, violations:[{v, part, measured, limit, hint, blocking}], advisories,
//    text, measurements, timings}
// `text` is the same <= 8 line report (`index.js:169-178`, imported, not copied)
// because that text is the ONLY thing the repair spawn is ever shown.
//
// Chain order, stopping at the first validator that produces a violation
// (`index.js:135-141`):
//   V1'  manifold + winding      V5  feature size        V2'  contact
//   V3'  connectivity            V6' clash               V4   ground
//   V7   role table              V10 budget
// The order is "is it a solid at all" -> "is it made of real material" ->
// "is it assembled" -> "does it stand up" -> "does it read" -> "does it ship".
//
// Timing IS measured here, unlike in the kernel: a validator is a measuring
// instrument, not part of the deterministic artifact, so a clock read cannot
// change what the module produces.
import * as THREE from "three";
import { MeshBVH } from "three-mesh-bvh";

import * as K from "../kernel/index.mjs";
import { partsToGeometry } from "../kernel/toThree.mjs";
import { reportText } from "./index.js";
import DEFAULT_LIMITS from "./limits.json" with { type: "json" };
// WORKFLOW-V3 §7.5 — the class prior (roles, bearing roles, census rules, tri
// budget) and the class rules (functions) arrive through `options.cls` /
// `options.rules`. These two imports are the FALLBACK used only when a caller
// supplies no class prior, so every pre-V3 caller and test keeps its behaviour.
import FALLBACK_CLASS from "../../classes/building.json" with { type: "json" };
import * as FALLBACK_RULES from "./rules/building.mjs";

export { DEFAULT_LIMITS, reportText };

// ---------------------------------------------------------------------------
// WF-LOOP r1 additions. Every number below is an OWNER number that limits.json
// does not carry, and limits.json is FROZEN (config.llmmodeling.json
// frozenFiles), so the new keys default here and are overridable through the
// `limits` argument. They go into the owner packet unratified, exactly like the
// numbers already in limits.json.
// ---------------------------------------------------------------------------

export const KERNEL_LIMIT_DEFAULTS = Object.freeze({
  /** r1 row 6 — an UNDECLARED penetration is never allowed at any fraction. */
  overlapClashUndeclared: 0,
  /** WORKFLOW-V3 §3 — harness-inferred contact. Two parts within epsAbs of each
   *  other, or interpenetrating by at most this fraction of the smaller volume,
   *  are IN CONTACT whether or not either declares `touches`. Above it an
   *  undeclared penetration is still V6_CLASH_UNDECLARED. */
  inferredContactFrac: 0.02,
  /** r1 row 6 — absolute floor under that ratio: numerical kissing is not a clash. */
  undeclaredVolumeEps: 1e-6,
  /** r1 row 2 — bearing sample grid, support band, and free cantilever. */
  bearingGrid: 0.1,
  bearingDrop: 0.02,
  bearingSpan: 1.0,
  /** r1 row 7 — landing rear face to the nearest massing face. */
  landingGapMax: 0.15,
  /** r1 row 9 — adjacent deck members, measured along the deck's short axis.
   *  r3 C1.4 (Fable M6): 0.10 m forced a near-SOLID deck, and the target's decks
   *  are open grilles you can see the wall through (fable-audit L6, iron 6.2 % of
   *  the target's front quad against our 12.7 %). 0.20 m. */
  deckGapMax: 0.20,
  /** r1 row 8 — clear zone at a drop-ladder head. */
  ladderHeadBand: 1.1,
  ladderHeadSlack: 0.3,
  ladderLandingReach: 0.3,
  /** r1 row 5 — stair pitch variation between consecutive risers. */
  stepRiseVariation: 0.01,
  /** r1 row 5 — a stringer's handrail sits this far above its tread line. */
  stairRailBand: [0.9, 1.1],
  /** r1 row 4 — census y-band clustering for window ROWS. */
  censusRowBand: 0.5,
  /** WF-V3 blind Gemini pickup P1 — the deepest a panel/door/shut line or a recess
   *  may be cut into a face (m), {GROOVE_DEPTH_MAX} in prompts. Prompt-only: a
   *  deeper cut is not measured here; it shows up as V3_FLOAT when it splits a part. */
  grooveDepthMax: 0.02,
});

const limitOf = (limits, key) => (limits?.[key] !== undefined ? limits[key] : KERNEL_LIMIT_DEFAULTS[key]);

/**
 * WF-BLIND-R2 C14 — the ONE gate configuration for a class prior: the prompt tokens (pass.mjs gateTokens), the
 * kernel's cut check (K.configure, before build) and this chain's measurements all come from it, and all three carry
 * its digest. MIN_FEAT is the CLASS style floor (`cls.styleFloorKey`), never a building default.
 */
export function gateConfig(cls, baseLimits = DEFAULT_LIMITS) {
  // V5-8 R2: a subject's measured rule overrides (cls.ruleOverrides, subject.mjs) are part of the ONE gate config.
  const { limits, waived } = applyRuleOverrides(baseLimits, cls?.ruleOverrides);
  const styleFloorKey = cls?.styleFloorKey ?? "building";
  const kernel = {};
  for (const key of Object.keys(KERNEL_LIMIT_DEFAULTS)) kernel[key] = limitOf(limits, key);
  const body = {
    styleFloorKey,
    // class weapon (gold pipeline): the class prior's own floor (limits.json frozen; a class without `minFeat` unchanged)
    minFeat: Number.isFinite(cls?.minFeat) ? cls.minFeat : limits.styleFloor?.[styleFloorKey] ?? limits.styleFloor?.prop,
    epsAbs: limits.epsAbs,
    kernel,
    v7: limits.v7 ?? null,
    ...(waived.length > 0 ? { waived } : {}),
  };
  return { ...body, digest: K.configDigest(body) };
}

/**
 * V5-8 R2 (owner 2026-09-26: TARGET WINS over real-world rules) — per-subject, MEASURED rule overrides from
 * subjects/<s>/subject.json `ruleOverrides` (subject.mjs hands them over as cls.ruleOverrides). limits.json stays
 * unchanged: the overrides make an EFFECTIVE copy for this subject only, and every one prints as an advisory row
 * (RULE_OVERRIDE) so a relaxed rule is never silent. Every entry needs `value` and `evidence`; unknown names throw.
 *   step_rise_max  {value: m}        limits.v7.step_rise upper bound (the target's measured riser + margin)
 *   stairRails     {value: false}    waives V7_STAIR_RAIL (the target's flights have no handrails)
 *   flightTreads   {value: n}        construction number the template builds (no rule; listed for visibility)
 * WF v8 WP2 (research/v7/WF-V8-PLAN.md "Gate") — the class-config gaps of the gold vehicles, same contract:
 *   wheels         {value: {count, axles, diameters: "equal"|"per-axle", diameterFrac?: [lo, hi]}}
 *                  VEH_WHEELS: count / axles replace the class `wheels` (a tandem truck stands on 6 wheels on 3 axles);
 *                  "per-axle" compares diameters within each axle only (a tractor's small front / big rear wheels);
 *                  diameterFrac replaces limits.v7.wheel_diameter_frac_of_length (then checked per axle under per-axle)
 *                  running (optional, default "wheels"): what the vehicle stands on —
 *                    "wheels"  the road vehicle above (count >= 1, axles 1..count);
 *                    "tracks"  a tracked vehicle: `runners` (default 2) role "track" assemblies stand on y = 0; count /
 *                              axles = the road wheels (wheelRoles) and their stations along z, 0 / 0 when the side
 *                              skirts hide them; the wheel diameter band applies only with an explicit diameterFrac;
 *                    "skids"   a helicopter on skids: `runners` (default 2) role "skid" assemblies stand on y = 0; no
 *                              wheels (count 0, axles 0);
 *                  under tracks / skids the runner role joins the closed role table, only the runner role (+ the road
 *                  wheels of a tracked vehicle) may reach y = 0, and the chassis clearance band (a road-car number) is off
 *   paletteZones   {value: {extra: [zone, ...]}}  PALETTE_ZONE accepts these zones besides the class's author keys (the
 *                  evidence names the target colour each one paints: the chain calibrates nothing, the subject did)
 *   roles          {value: {extra: [role, ...]}}  V7_ROLE accepts these roles besides the class's closed role table (a
 *                  tank's turret / gun, a helicopter's rotor / boom: the evidence names the target part each one builds)
 *   tris           {value: n}  the V10 triangle budget for this subject (an integer 1..TRIS_OVERRIDE_CAP; the owner's
 *                  detail level, e.g. a Generals unit "detailed like the combat bike"); it replaces the class
 *                  triBudget AND a module's meta.triBudget, so measurements.triBudget (step / doctor / merge) reads it
 *   mirror         {value: {centred: ["<part id or role regex>", ...]}}  VEH_MIRROR normally requires every v9 role to
 *                  come in a pair mirrored across the body's centre plane; a single-track vehicle (motorbike: one front
 *                  tyre, one rear tyre, one headlight) has centred SINGLE parts instead. Each pattern is tested (as a
 *                  RegExp) against the role name and against every member id of a VEH_MIRROR group; a match exempts
 *                  that group from the mirrored-pair requirement, but the group must then sit on the centreline
 *                  (|x of its box centre - the body's x centre| <= mirrorTol, else VEH_MIRROR "centred part off the
 *                  centreline" — the override does not waive centring, only pairing)
 * The WP2 overrides reach the class rows through `values` (ctx.overrides); only diameterFrac changes a limits number.
 */
export const RULE_OVERRIDES = Object.freeze(["step_rise_max", "stairRails", "flightTreads", "wheels", "paletteZones", "roles", "tris", "mirror"]);

// The highest triangle budget a subject's `tris` override may set (owner 2026-09-29: detailed units, capped).
export const TRIS_OVERRIDE_CAP = 12000;

/** What a vehicle stands on (the `wheels` override's `running`) and the role its runners carry. */
export const RUNNING = Object.freeze(["wheels", "tracks", "skids"]);
export const RUNNER_ROLE = Object.freeze({ tracks: "track", skids: "skid" });

const WHEEL_DIAMETER_MODES = Object.freeze(["equal", "per-axle"]);

/** A subject's `wheels` override value, checked: {count, axles, diameters, diameterFrac?, running?, runners?}. Throws on anything else. */
function wheelsOverride(value) {
  const bad = (why) => new Error(`ruleOverrides.wheels ${why} — want {count, axles, diameters: "equal"|"per-axle", diameterFrac?: [lo, hi], running?: ${RUNNING.map((r) => `"${r}"`).join("|")}, runners?: n}`);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw bad("value must be an object");
  const known = ["count", "axles", "diameters", "diameterFrac", "running", "runners"];
  const unknown = Object.keys(value).filter((k) => !k.startsWith("_") && !known.includes(k));
  if (unknown.length > 0) throw bad(`has unknown key(s) ${unknown.join(", ")}`);
  const { count, axles, diameterFrac, running = "wheels", runners } = value;
  if (!RUNNING.includes(running)) throw bad(`running ${JSON.stringify(running)} must be one of ${RUNNING.join(", ")}`);
  const diameters = value.diameters ?? (running !== "wheels" && count === 0 ? "equal" : undefined);
  if (running === "wheels") {
    if (!(Number.isInteger(count) && count >= 1)) throw bad(`count ${JSON.stringify(count)} must be an integer >= 1`);
    if (!(Number.isInteger(axles) && axles >= 1 && axles <= count)) throw bad(`axles ${JSON.stringify(axles)} must be an integer 1..count`);
    if (runners !== undefined) throw bad("runners is for running tracks | skids only");
  } else if (running === "tracks") {
    if (!(Number.isInteger(count) && count >= 0)) throw bad(`count ${JSON.stringify(count)} (road wheels) must be an integer >= 0`);
    const lo = count === 0 ? 0 : 1;
    if (!(Number.isInteger(axles) && axles >= lo && axles <= count)) throw bad(`axles ${JSON.stringify(axles)} (road-wheel stations) must be an integer ${lo}..count`);
  } else if (count !== 0 || axles !== 0) {
    throw bad(`running skids stands on no wheels: count ${JSON.stringify(count)} / axles ${JSON.stringify(axles)} must be 0 / 0`);
  }
  if (runners !== undefined && !(Number.isInteger(runners) && runners >= 1)) throw bad(`runners ${JSON.stringify(runners)} must be an integer >= 1`);
  if (!WHEEL_DIAMETER_MODES.includes(diameters)) throw bad(`diameters ${JSON.stringify(diameters)} must be "equal" or "per-axle"`);
  const out = { count, axles, diameters };
  if (diameterFrac !== undefined) {
    const ok = Array.isArray(diameterFrac) && diameterFrac.length === 2 && diameterFrac.every(Number.isFinite)
      && diameterFrac[0] > 0 && diameterFrac[0] < diameterFrac[1];
    if (!ok) throw bad(`diameterFrac ${JSON.stringify(diameterFrac)} must be [lo, hi] with 0 < lo < hi`);
    out.diameterFrac = [diameterFrac[0], diameterFrac[1]];
  }
  // `running` / `runners` only when stated: a road vehicle's override value keeps exactly the WP2 shape
  if (value.running !== undefined) out.running = running;
  if (running !== "wheels") out.runners = runners ?? 2;
  return Object.freeze(out);
}

/** A subject's `roles` override value, checked: {extra: [role, ...]} (duplicates dropped). Throws on anything else. */
function rolesOverride(value) {
  const bad = (why) => new Error(`ruleOverrides.roles ${why} — want {extra: ["role", ...]}`);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw bad("value must be an object");
  const unknown = Object.keys(value).filter((k) => !k.startsWith("_") && k !== "extra");
  if (unknown.length > 0) throw bad(`has unknown key(s) ${unknown.join(", ")}`);
  const { extra } = value;
  if (!Array.isArray(extra) || extra.length === 0) throw bad("extra must be a non-empty list of role names");
  const roles = extra.map((z) => (typeof z === "string" ? z.trim() : ""));
  if (roles.some((z) => !/^[a-z][a-z0-9_]*$/.test(z))) throw bad(`extra ${JSON.stringify(extra)} holds a role that is not a lower-case identifier`);
  return Object.freeze({ extra: Object.freeze([...new Set(roles)]) });
}

/** A subject's `mirror` override value, checked: {centred: ["<part id or role regex>", ...]} (duplicates dropped,
 *  each pattern must compile as a RegExp). Throws on anything else. */
function mirrorOverride(value) {
  const bad = (why) => new Error(`ruleOverrides.mirror ${why} — want {centred: ["<part id or role regex>", ...]}`);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw bad("value must be an object");
  const unknown = Object.keys(value).filter((k) => !k.startsWith("_") && k !== "centred");
  if (unknown.length > 0) throw bad(`has unknown key(s) ${unknown.join(", ")}`);
  const { centred } = value;
  if (!Array.isArray(centred) || centred.length === 0) throw bad("centred must be a non-empty list of part id / role regex patterns");
  const patterns = centred.map((p) => (typeof p === "string" ? p.trim() : ""));
  if (patterns.some((p) => p === "")) throw bad(`centred ${JSON.stringify(centred)} holds a non-string or empty pattern`);
  for (const p of patterns) {
    try { new RegExp(p); } catch (e) { throw bad(`centred pattern ${JSON.stringify(p)} is not a valid regex (${e.message})`); }
  }
  return Object.freeze({ centred: Object.freeze([...new Set(patterns)]) });
}

/** A subject's `paletteZones` override value, checked: {extra: [zone, ...]} (duplicates dropped). Throws on anything else. */
function paletteZonesOverride(value) {
  const bad = (why) => new Error(`ruleOverrides.paletteZones ${why} — want {extra: ["zone", ...]}`);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw bad("value must be an object");
  const unknown = Object.keys(value).filter((k) => !k.startsWith("_") && k !== "extra");
  if (unknown.length > 0) throw bad(`has unknown key(s) ${unknown.join(", ")}`);
  const { extra } = value;
  if (!Array.isArray(extra) || extra.length === 0) throw bad("extra must be a non-empty list of zone names");
  const zones = extra.map((z) => (typeof z === "string" ? z.trim() : ""));
  if (zones.some((z) => z === "")) throw bad(`extra ${JSON.stringify(extra)} holds a non-string or empty zone name`);
  return Object.freeze({ extra: Object.freeze([...new Set(zones)]) });
}

export function applyRuleOverrides(limits, overrides) {
  const rows = [];
  const waived = [];
  const values = {};
  if (!overrides || Object.keys(overrides).length === 0) return { limits, rows, waived, values };
  let out = limits;
  for (const [name, o] of Object.entries(overrides)) {
    if (name.startsWith("_")) continue;
    if (!RULE_OVERRIDES.includes(name)) throw new Error(`ruleOverrides: unknown override "${name}" (known: ${RULE_OVERRIDES.join(", ")})`);
    if (!o || o.value === undefined || !o.evidence) throw new Error(`ruleOverrides.${name} needs {value, evidence} — an override is a measurement, not a wish`);
    let limit = "";
    if (name === "step_rise_max") {
      const base = limits.v7?.step_rise ?? [0, o.value];
      if (!(Number.isFinite(o.value) && o.value > base[0])) throw new Error(`ruleOverrides.step_rise_max ${o.value} must exceed step_rise min ${base[0]}`);
      out = { ...out, v7: { ...(out.v7 ?? {}), step_rise: [base[0], o.value] } };
      limit = `limits.v7.step_rise ${base[0]}..${base[1]} m -> ${base[0]}..${o.value} m`;
    } else if (name === "stairRails") {
      if (o.value !== false) throw new Error("ruleOverrides.stairRails only takes value false (waive V7_STAIR_RAIL)");
      waived.push("V7_STAIR_RAIL");
      limit = "V7_STAIR_RAIL waived";
    } else if (name === "wheels") {
      const w = wheelsOverride(o.value);
      values.wheels = w;
      const run = w.running ?? "wheels";
      limit = run === "wheels"
        ? `VEH_WHEELS ${w.count} wheels on ${w.axles} axles, ${w.diameters === "per-axle" ? "equal diameters within each axle" : "one diameter"}`
        : `VEH_WHEELS / VEH_GROUND running ${run}: ${w.runners} "${RUNNER_ROLE[run]}" assemblies on the ground, ${run === "tracks" ? `${w.count} road wheels on ${w.axles} stations` : "no wheels"}; chassis clearance band off`;
      if (w.diameterFrac) {
        const base = limits.v7?.wheel_diameter_frac_of_length;
        out = { ...out, v7: { ...(out.v7 ?? {}), wheel_diameter_frac_of_length: [...w.diameterFrac] } };
        limit += `; limits.v7.wheel_diameter_frac_of_length ${Array.isArray(base) ? base.join("..") : "none"} -> ${w.diameterFrac.join("..")}`
          + `${w.diameters === "per-axle" ? " (per axle)" : ""}`;
      }
    } else if (name === "mirror") {
      const m = mirrorOverride(o.value);
      values.mirror = m;
      limit = `VEH_MIRROR exempts the pairing requirement for part(s)/role(s) matching ${m.centred.join(", ")} (still must sit on the centreline)`;
    } else if (name === "paletteZones") {
      const p = paletteZonesOverride(o.value);
      values.paletteZones = p;
      limit = `PALETTE_ZONE also accepts ${p.extra.join(", ")}`;
    } else if (name === "roles") {
      const r = rolesOverride(o.value);
      values.roles = r;
      limit = `V7_ROLE also accepts ${r.extra.join(", ")}`;
    } else if (name === "tris") {
      if (!(Number.isInteger(o.value) && o.value >= 1 && o.value <= TRIS_OVERRIDE_CAP)) {
        throw new Error(`ruleOverrides.tris ${JSON.stringify(o.value)} must be an integer 1..${TRIS_OVERRIDE_CAP} (the triangle budget cap)`);
      }
      values.tris = o.value;
      limit = `V10 triangle budget -> ${o.value} (class triBudget and meta.triBudget replaced; cap ${TRIS_OVERRIDE_CAP})`;
    } else {
      limit = "construction (no rule)";
    }
    rows.push(advise("RULE_OVERRIDE", name, JSON.stringify(o.value), limit, `subject rule override (TARGET WINS, owner 2026-09-26): ${o.evidence}`));
  }
  return { limits: out, rows, waived, values };
}

const make = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint, blocking: true });
const advise = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint, blocking: false });

const fmt = (value) => (Math.round(value * 1000) / 1000).toFixed(3);
const pct = (value) => `${(value * 100).toFixed(1)}%`;

// ---------------------------------------------------------------------------
// Measured context — every number the chain reads is taken ONCE, here, from the
// solids themselves. Nothing below re-derives geometry from a declaration.
// ---------------------------------------------------------------------------

function buildContext(meta, parts, limits, options = {}, prior = {}) {
  // WF-BLIND-R2 C14 — an explicit class prior is the one source of the floor (the same gateConfig the prompt and
  // the kernel read); only a caller with no prior keeps the pre-V3 meta.class lookup.
  const styleClass = options.cls
    ? (options.cls.styleFloorKey ?? "building")
    : (Object.hasOwn(limits.styleFloor, meta?.class ?? "") ? meta.class : "prop");
  const EPS = limits.epsAbs;
  const MIN_FEAT = Number.isFinite(options.cls?.minFeat) ? options.cls.minFeat : limits.styleFloor[styleClass] ?? limits.styleFloor.prop;

  const records = parts.map((part, index) => ({
    index,
    id: part.id,
    part,
    role: part.role ?? null,
    zone: part.zone,
    touches: Array.isArray(part.touches) ? part.touches : [],
    embed: part.embed === true,
    aabb: part.solid.aabb(),
    volume: part.solid.volume(),
    tris: part.solid.triCount(),
  }));

  const byId = new Map(records.map((r) => [r.id, r]));

  const geometries = new Map();
  const trees = new Map();
  const intersections = new Map();

  /** position + index straight off the MeshGL: the cheapest exact surface. */
  const collisionGeometry = (record) => {
    if (geometries.has(record.index)) return geometries.get(record.index);
    const mesh = record.part.solid.mesh();
    const stride = mesh.numProp;
    const count = mesh.vertProperties.length / stride;
    const position = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      position[i * 3] = mesh.vertProperties[i * stride];
      position[i * 3 + 1] = mesh.vertProperties[i * stride + 1];
      position[i * 3 + 2] = mesh.vertProperties[i * stride + 2];
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(position, 3));
    geometry.setIndex(new THREE.BufferAttribute(Uint32Array.from(mesh.triVerts), 1));
    geometries.set(record.index, geometry);
    return geometry;
  };

  const tree = (record) => {
    if (trees.has(record.index)) return trees.get(record.index);
    const built = new MeshBVH(collisionGeometry(record));
    trees.set(record.index, built);
    return built;
  };

  const key = (a, b) => (a.index < b.index ? `${a.index}:${b.index}` : `${b.index}:${a.index}`);

  /** Penetration volume of two solids, in m^3. Memoised: booleans are the cost. */
  const penetration = (a, b) => {
    const k = key(a, b);
    if (intersections.has(k)) return intersections.get(k);
    const value = K.intersect(a.part.solid, b.part.solid).volume();
    intersections.set(k, value);
    return value;
  };

  const IDENTITY = new THREE.Matrix4();
  const distances = new Map();

  /** Closest surface-to-surface distance in metres (0 when they touch/overlap). */
  const distance = (a, b) => {
    const k = key(a, b);
    if (distances.has(k)) return distances.get(k);
    const hit = tree(a).closestPointToGeometry(collisionGeometry(b), IDENTITY, {}, {}, 0, Infinity);
    const value = hit && Number.isFinite(hit.distance) ? hit.distance : Infinity;
    distances.set(k, value);
    return value;
  };

  // r1 row 4 — the census is DATA the caller supplies (subjects/<s>/census.json),
  // never something this module reads off disk: the chain runs in the browser
  // too. `meta.census === false` is the author's opt-out for a module that is
  // not the subject's finished façade (the S1 smoke).
  const census = meta?.census === false ? null : (options.census ?? (meta?.census && typeof meta.census === "object" ? meta.census : null));

  // r2 row B1/B2 — the LAYOUT arrives through the same options path as the
  // census (`subjects/<s>/layout.json`), for the same reason: this module never
  // reads the filesystem. `meta.layout === false` is the opt-out for a module
  // that is not the subject's façade (the S1 smoke).
  const layout = meta?.layout === false ? null : (options.layout ?? (meta?.layout && typeof meta.layout === "object" ? meta.layout : null));

  const L = (k) => limitOf(limits, k);

  // WORKFLOW-V3 §3 — HARNESS-INFERRED CONTACT, measured once and memoised. A
  // pair is in contact when the solids interpenetrate by at most
  // inferredContactFrac of the smaller volume (or by no more than the numerical
  // volume floor), or when they do not penetrate and their surfaces are within
  // EPS. Broad phase: AABBs within EPS. Uses the same memoised booleans and
  // distances V3/V6 already pay for.
  let inferred = null;
  const inferContacts = () => {
    if (inferred) return inferred;
    inferred = { byIndex: new Map(records.map((r) => [r.index, new Set()])), pairs: 0 };
    const frac = L("inferredContactFrac");
    const volumeEps = L("undeclaredVolumeEps");
    for (let i = 0; i < records.length; i += 1) {
      for (let j = i + 1; j < records.length; j += 1) {
        const a = records[i];
        const b = records[j];
        if (!aabbOverlap(a.aabb, b.aabb, EPS)) continue;
        const overlap = penetration(a, b);
        let contact;
        if (overlap > 0) {
          const smaller = Math.min(a.volume, b.volume);
          contact = overlap <= volumeEps || (smaller > 0 && overlap / smaller <= frac);
        } else {
          contact = distance(a, b) <= EPS;
        }
        if (!contact) continue;
        inferred.byIndex.get(a.index).add(b.id);
        inferred.byIndex.get(b.index).add(a.id);
        inferred.pairs += 1;
      }
    }
    return inferred;
  };
  /** declared ∪ inferred, declared first (in declaration order). */
  const effectiveTouches = (record) => {
    const out = [...record.touches];
    for (const id of inferContacts().byIndex.get(record.index)) if (!out.includes(id)) out.push(id);
    return out;
  };

  return {
    meta, parts, limits, styleClass, EPS, MIN_FEAT, census, layout,
    cls: prior.cls, rules: prior.rules,
    L,
    records, byId,
    collisionGeometry, tree, penetration, distance,
    inferContacts, effectiveTouches,
    get inferredPairs() { return inferred ? inferred.pairs : null; },
    counts: { intersections, distances },
    // Shared measuring helpers for the class rules (rules/<class>.mjs).
    geo: { make, advise, fmt, pct, spanOverlap, groupAssemblies, groupTagged, unionBox, clusters, bands },
  };
}

function aabbOverlap(a, b, slack = 0) {
  for (let i = 0; i < 3; i += 1) {
    if (Math.min(a.max[i], b.max[i]) - Math.max(a.min[i], b.min[i]) <= -slack) return false;
  }
  return true;
}

function aabbContains(outer, inner, slack) {
  for (let i = 0; i < 3; i += 1) {
    if (inner.min[i] < outer.min[i] - slack || inner.max[i] > outer.max[i] + slack) return false;
  }
  return true;
}

// ---------------------------------------------------------------------------
// V1' — every part is a healthy manifold and the merged mesh is outward-wound.
// ---------------------------------------------------------------------------

function signedVolumeIndexed(mesh) {
  const stride = mesh.numProp;
  const verts = mesh.vertProperties;
  const tris = mesh.triVerts;
  let volume = 0;
  for (let i = 0; i < tris.length; i += 3) {
    const a = tris[i] * stride;
    const b = tris[i + 1] * stride;
    const c = tris[i + 2] * stride;
    // cross(b, c) . a / 6 — the winding.test.js maths, on the MeshGL directly.
    const cx = verts[b + 1] * verts[c + 2] - verts[b + 2] * verts[c + 1];
    const cy = verts[b + 2] * verts[c] - verts[b] * verts[c + 2];
    const cz = verts[b] * verts[c + 1] - verts[b + 1] * verts[c];
    volume += (cx * verts[a] + cy * verts[a + 1] + cz * verts[a + 2]) / 6;
  }
  return volume;
}

function signedVolumeNonIndexed(position) {
  let volume = 0;
  for (let i = 0; i < position.count; i += 3) {
    const ax = position.getX(i), ay = position.getY(i), az = position.getZ(i);
    const bx = position.getX(i + 1), by = position.getY(i + 1), bz = position.getZ(i + 1);
    const cx = position.getX(i + 2), cy = position.getY(i + 2), cz = position.getZ(i + 2);
    const nx = by * cz - bz * cy;
    const ny = bz * cx - bx * cz;
    const nz = bx * cy - by * cx;
    volume += (nx * ax + ny * ay + nz * az) / 6;
  }
  return volume;
}

function validateV1(ctx) {
  const violations = [];
  for (const record of ctx.records) {
    const status = record.part.solid.status();
    if (status !== "NoError") {
      violations.push(make("V1", record.id, `status "${status}"`, '"NoError"',
        `"${record.id}" is not a valid solid (manifold status ${status}) — rebuild it from kernel primitives instead of patching it`));
      continue;
    }
    const genus = record.part.solid.genus();
    if (!Number.isFinite(genus)) {
      violations.push(make("V1", record.id, `genus ${genus}`, "finite",
        `"${record.id}" has no finite genus — the surface is not closed; cut through cleanly instead of grazing a face`));
      continue;
    }
    const volume = signedVolumeIndexed(record.part.solid.mesh());
    if (!(volume > 0)) {
      violations.push(make("V1", record.id, `signed volume ${fmt(volume)} m3`, "> 0",
        `"${record.id}" is inside-out — its surface is inward-wound and renders as a hole`));
    }
  }
  if (violations.length > 0) return { violations, advisories: [] };

  const merged = ctx.merged.geometry.getAttribute("position");
  const mergedVolume = signedVolumeNonIndexed(merged);
  if (!(mergedVolume > 0)) {
    violations.push(make("V1", null, `merged signed volume ${fmt(mergedVolume)} m3`, "> 0",
      "the merged mesh is inward-wound — every facet is culled and the model renders as empty space"));
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V5 — minimum feature size, per part, on the measured solid AABB.
// ---------------------------------------------------------------------------

/**
 * WF-R3 R3-B item 4 — a thin wall BESIDE a shallow groove is not a V5_THIN row: when the cut tool enters the part from
 * one face no deeper than GROOVE_DEPTH_MAX, material stays behind the groove, so a narrow margin on a LATERAL side
 * (an axis other than the one the tool enters along) cannot split or thin the part. Behind-the-groove residuals, and any
 * residual of a deeper cut, are still rows.
 */
export function shallowLateral(t, grooveDepthMax) {
  const a = t.target;
  const b = t.tool;
  if (!a || !b) return false;
  let pen = Infinity;
  let penAxis = -1;
  for (let i = 0; i < 3; i += 1) {
    const outHi = b.max[i] >= a.max[i] - 1e-9;
    const outLo = b.min[i] <= a.min[i] + 1e-9;
    if (outHi === outLo) continue;                     // inside on this axis, or clean through it
    const depth = outHi ? a.max[i] - b.min[i] : b.max[i] - a.min[i];
    if (depth < pen) { pen = depth; penAxis = i; }
  }
  if (penAxis < 0) return false;
  const sideAxis = "xyz".indexOf(String(t.side ?? "")[0]);
  return sideAxis !== penAxis && pen <= grooveDepthMax + 1e-9;
}

function validateV5(ctx) {
  const violations = [];
  for (const record of ctx.records) {
    const extents = [0, 1, 2].map((i) => record.aabb.max[i] - record.aabb.min[i]);
    const min = Math.min(...extents);
    if (min < ctx.MIN_FEAT - 1e-9) {
      const axis = ["x", "y", "z"][extents.indexOf(min)];
      violations.push(make("V5", record.id, `${fmt(min)} m on ${axis}`, `>= ${fmt(ctx.MIN_FEAT)} m`,
        `grow "${record.id}" on ${axis} from ${fmt(min)} m to ${fmt(ctx.MIN_FEAT)} m — thinner than the ${ctx.styleClass} style floor and it disappears at capture`));
    }
  }
  // WF-BLIND-R2 C9 — a thin CUT is a gate row with its location, not a throw inside build(). The kernel
  // records every residual under its strictest floor; the row fires under THIS module's class floor.
  for (const record of ctx.records) {
    const thin = (typeof record.part.solid.thinCuts === "function" ? record.part.solid.thinCuts() : [])
      .filter((t) => t.remaining < ctx.MIN_FEAT - 1e-9 && !shallowLateral(t, ctx.L("grooveDepthMax")))
      .sort((a, b) => a.remaining - b.remaining);
    if (thin.length === 0) continue;
    const t = thin[0];
    const span = (box) => ["x", "y", "z"].map((a, i) => `${a} ${fmt(box.min[i])}..${fmt(box.max[i])}`).join(", ");
    const panel = fmt(ctx.MIN_FEAT + ctx.L("grooveDepthMax"));
    violations.push(make("V5_THIN", record.id, `${fmt(t.remaining)} m left on ${t.side} by a cut (tool ${span(t.tool)})`,
      `>= ${fmt(ctx.MIN_FEAT)} m of material beside and behind every cut`,
      `a cut into "${record.id}" leaves ${fmt(t.remaining)} m of material on its ${t.side} side${thin.length > 1 ? ` (${thin.length} thin cuts in this part)` : ""} — move or shrink the tool so >= ${fmt(ctx.MIN_FEAT)} m stays on every side, cut clean through, or groove only panels >= ${panel} m thick`));
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// PALETTE_ZONE — WF-BLIND-R2 C4/C10. The palette is calibrated from the target
// per CLOSED class zone (classes/<class>.json paletteZones). A part in a zone
// the class does not list is never calibrated: blind runs painted headlights
// #808080 and ironwork the AC grey that way. Closure entries (`closure: true`)
// exist for the likeness families only and are not author keys.
// ---------------------------------------------------------------------------

/** The author palette keys of a class prior, in prior order. */
export function authorPaletteKeys(cls) {
  return (cls?.paletteZones ?? []).filter((z) => z.closure !== true).map((z) => z.key);
}

function validatePaletteZone(ctx) {
  const violations = [];
  const classKeys = authorPaletteKeys(ctx.cls);
  if (classKeys.length === 0) return { violations, advisories: [] };
  // WF v8 WP2: + the zones a subject's measured `paletteZones` override adds (a RULE_OVERRIDE advisory row each run)
  const extra = ctx.overrides?.paletteZones?.extra ?? [];
  const keys = [...classKeys, ...extra.filter((z) => !classKeys.includes(z))];
  const entries = ctx.cls.paletteZones ?? [];
  const unknown = new Map();
  for (const record of ctx.records) {
    if (keys.includes(record.zone)) continue;
    if (!unknown.has(record.zone)) unknown.set(record.zone, []);
    unknown.get(record.zone).push(record.id);
  }
  for (const [zone, ids] of unknown) {
    const alias = entries.find((z) => z.key === zone || z.region === zone);
    const suggest = alias ? (alias.closure === true ? alias.material : alias.key) : null;
    violations.push(make("PALETTE_ZONE", ids[0], `zone "${zone}" on ${ids.length} part(s)`, `one of: ${keys.join(", ")}`,
      `zone "${zone}" is not a palette zone of class ${ctx.cls.class ?? "?"}, so its colour is never calibrated from the target — `
      + `${suggest && keys.includes(suggest) ? `use "${suggest}"` : "use the key of that material"} (closed list: ${keys.join(", ")})`));
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V2' — declared contact, measured on the REAL surfaces (V2-TEST-PLAN §3):
// penetration volume first, and when the solids only kiss, the closest-point
// distance between the two meshes through a BVH. A declared touch that is more
// than EPS apart is a lie about the model and fails here; a touch that is too
// DEEP is V6's business, not this one's.
// ---------------------------------------------------------------------------

function validateV2(ctx) {
  const violations = [];
  const seen = new Set();
  for (const record of ctx.records) {
    // WORKFLOW-V3 §3 — the EFFECTIVE set: declared ∪ harness-inferred. An
    // inferred pair is in contact by construction; a declared one may still lie.
    for (const otherId of ctx.effectiveTouches(record)) {
      const other = ctx.byId.get(otherId);
      if (!other) {
        violations.push(make("V2_GAP", record.id, `touches "${otherId}"`, "an existing part id",
          `"${record.id}" declares it touches "${otherId}", which is not a part — fix the id or drop the claim`));
        continue;
      }
      if (other.index === record.index) continue;
      const pairKey = record.index < other.index ? `${record.index}:${other.index}` : `${other.index}:${record.index}`;
      if (seen.has(pairKey)) continue;
      seen.add(pairKey);

      if (ctx.penetration(record, other) > 0) continue;      // solid contact, depth is V6's row
      const gap = ctx.distance(record, other);
      if (gap <= ctx.EPS) continue;                          // flush within eps
      violations.push(make("V2_GAP", record.id, `${fmt(gap)} m from "${other.id}"`, `<= ${fmt(ctx.EPS)} m`,
        `move "${record.id}" ${fmt(gap)} m towards "${other.id}" — it declares contact but floats clear of it`));
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V3' — connectivity, promoted from the v1 DEFERRED cross-check (v3.js:7-9).
// Two independent questions:
//   (a) does the union of the structure come apart into more than one lump?
//   (b) does every part reach the ground through MEASURED contacts?
// (b) is the stricter one — a chimney welded to a floating slab passes (a).
// Props (`role: "prop"`) are excluded: a bin standing beside a building is not
// part of the building.
// ---------------------------------------------------------------------------

function contactGraph(ctx, structural) {
  const edges = new Map(structural.map((r) => [r.index, new Set()]));
  const link = (a, b) => { edges.get(a.index).add(b.index); edges.get(b.index).add(a.index); };
  const tested = new Set();

  const consider = (a, b) => {
    const k = a.index < b.index ? `${a.index}:${b.index}` : `${b.index}:${a.index}`;
    if (tested.has(k)) return;
    tested.add(k);
    if (ctx.penetration(a, b) > 0 || ctx.distance(a, b) <= ctx.EPS) link(a, b);
  };

  // Effective touches first (declared ∪ inferred), then every AABB-overlapping
  // pair as the broad phase for contacts nobody declared.
  for (const record of structural) {
    for (const otherId of ctx.effectiveTouches(record)) {
      const other = ctx.byId.get(otherId);
      if (other && other.index !== record.index && edges.has(other.index)) consider(record, other);
    }
  }
  for (let i = 0; i < structural.length; i += 1) {
    for (let j = i + 1; j < structural.length; j += 1) {
      if (aabbOverlap(structural[i].aabb, structural[j].aabb, ctx.EPS)) consider(structural[i], structural[j]);
    }
  }
  return edges;
}

/** Max ids named per lump in the V3_FLOAT hint (the report is <= 8 lines). */
const FLOAT_IDS_PER_LUMP = 6;

/**
 * V3_FLOAT with a cause the author can act on (blind Gemini pickup P1: door
 * grooves cut the cab off its base, and the old row named only the smaller side).
 * Every lump is named by its parts, largest lump first; a part whose solid lies in
 * more than one lump (a cut through it) is listed in each. The closest surface gap
 * between the two largest lumps is measured piece-to-piece with ctx.distance.
 */
function floatViolation(ctx, structural, lumps) {
  const boxes = lumps.map((lump, i) => ({ i, lump, aabb: lump.aabb(), volume: lump.volume(), members: [] }));
  boxes.sort((a, b) => b.volume - a.volume);
  let pseudo = 0;
  for (const record of structural) {
    const candidates = boxes.filter((box) => aabbOverlap(box.aabb, record.aabb, ctx.EPS));
    if (candidates.length === 1) {
      candidates[0].members.push({ record, piece: record, volume: record.volume });
      continue;
    }
    for (const box of candidates) {
      const solid = K.intersect(box.lump, record.part.solid);
      const volume = solid.volume();
      if (!(volume > 0)) continue;
      // A pseudo-record (unique index far above the part indices) so the memoised
      // BVH distance helper can measure this piece of the part on its own.
      const whole = volume >= record.volume * (1 - 1e-6);
      const piece = whole ? record : { index: 1e6 + (pseudo += 1), id: record.id, part: { solid }, aabb: solid.aabb() };
      box.members.push({ record, piece, volume });
    }
  }
  for (const box of boxes) box.members.sort((a, b) => b.volume - a.volume);
  const ids = (box) => {
    const names = [...new Set(box.members.map((m) => m.record.id))];
    return `[${names.slice(0, FLOAT_IDS_PER_LUMP).join(", ")}${names.length > FLOAT_IDS_PER_LUMP ? ", …" : ""}]`;
  };
  const listed = boxes.map(ids);
  const joined = listed.length === 2 ? listed.join(" and ") : `${listed.slice(0, -1).join(", ")} and ${listed[listed.length - 1]}`;

  const [a, b] = boxes;
  let best = null;
  for (const ma of a.members) {
    for (const mb of b.members) {
      if (ma.piece === mb.piece) continue;
      const lower = aabbGap(ma.piece.aabb, mb.piece.aabb);
      if (best && lower >= best.gap) continue;
      const gap = ctx.distance(ma.piece, mb.piece);
      if (!best || gap < best.gap) best = { gap, a: ma.record.id, b: mb.record.id };
    }
  }
  const cut = a.members.filter((m) => b.members.some((n) => n.record === m.record)).map((m) => m.record.id);
  const mm = (gap) => `${(gap * 1000).toFixed(gap < 0.01 ? 1 : 0)} mm`;
  const gapText = best && Number.isFinite(best.gap) ? `; closest gap ${mm(best.gap)} between ${best.a} and ${best.b}` : "";
  const cutText = cut.length > 0 ? `; ${[...new Set(cut)].slice(0, 3).join(", ")} ${cut.length === 1 ? "is" : "are"} cut apart` : "";
  const part = b.members[0]?.record.id ?? a.members[0]?.record.id ?? structural[0].id;
  return make("V3_FLOAT", part, `${lumps.length} disconnected lumps`, "1",
    `the model splits into ${lumps.length} pieces: ${joined}${gapText}${cutText} — rejoin them (seat the parts on each other; never cut through a part's base)`);
}

/** Lower bound on the surface distance of two AABBs (0 when they overlap). */
function aabbGap(a, b) {
  let sum = 0;
  for (let axis = 0; axis < 3; axis += 1) {
    const d = Math.max(0, a.min[axis] - b.max[axis], b.min[axis] - a.max[axis]);
    sum += d * d;
  }
  return Math.sqrt(sum);
}

function validateV3(ctx) {
  const violations = [];
  const loose = ctx.cls.nonStructuralRoles ?? [];
  const structural = ctx.records.filter((r) => !loose.includes(r.role));
  if (structural.length === 0) return { violations, advisories: [] };

  // (a) one lump, measured by the kernel itself.
  if (structural.length > 1) {
    // WF-R5 R5-A: a zero-volume lump is a numerical sheet the boolean left where two faces were coplanar (an inlay laid on
    // a raked face), not a piece of the model; it cannot float and nothing renders it.
    const lumps = K.union(structural.map((r) => r.part.solid)).decompose().filter((l) => l.volume() > 1e-9);
    if (lumps.length > 1) {
      violations.push(floatViolation(ctx, structural, lumps));
      return { violations, advisories: [] };
    }
  }

  // (b) everything reaches the ground through measured contacts — not for a hand-held class (cls.grounded false: it
  // stands on nothing; (a) one lump is its whole support rule).
  if (ctx.cls.grounded === false) return { violations, advisories: [] };
  const ground = structural.filter((r) => r.aabb.min[1] <= ctx.EPS);
  if (ground.length === 0) {
    violations.push(make("V3_UNSUPPORTED", structural[0].id, "no part reaches y = 0", "at least one ground part",
      `nothing in the model touches the ground plane — drop the lowest part to y = 0`));
    return { violations, advisories: [] };
  }

  const edges = contactGraph(ctx, structural);
  const reached = new Set(ground.map((r) => r.index));
  const queue = [...reached];
  while (queue.length > 0) {
    const current = queue.pop();
    for (const next of edges.get(current) ?? []) {
      if (reached.has(next)) continue;
      reached.add(next);
      queue.push(next);
    }
  }
  const floating = structural.filter((r) => !reached.has(r.index));
  if (floating.length > 0) {
    const first = floating[0];
    violations.push(make("V3_UNSUPPORTED", first.id, `${floating.length} part(s) off the load path`, "0",
      `"${first.id}" (bottom at y = ${fmt(first.aabb.min[1])} m) reaches nothing that reaches the ground — rest it on a part that does`));
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V6' — clash and duplication, on real intersection volume (AABB is broad phase
// only). `embed: true` on a part declares that this part is MEANT to be seated
// inside the thing it touches (a bar socketed into a landing); it lifts the
// clash band for that declared pair and nothing else. Total containment is
// never excused: a part 90 % inside another renders as nothing.
// ---------------------------------------------------------------------------

function validateV6(ctx) {
  const violations = [];
  const { records, limits } = ctx;
  for (let i = 0; i < records.length; i += 1) {
    for (let j = i + 1; j < records.length; j += 1) {
      const a = records[i];
      const b = records[j];
      if (!aabbOverlap(a.aabb, b.aabb, 0)) continue;
      const smaller = Math.min(a.volume, b.volume);
      if (!(smaller > 0)) continue;
      const overlap = ctx.penetration(a, b);
      if (!(overlap > 0)) continue;
      const ratio = overlap / smaller;

      if (ratio > limits.overlapDuplicate) {
        const contained = a.volume < b.volume ? a : b;
        const host = contained === a ? b : a;
        violations.push(make("V6_DUPLICATE", contained.id, `${pct(ratio)} contained`, `<= ${pct(limits.overlapDuplicate)}`,
          `delete "${contained.id}" — it is ${pct(ratio)} inside "${host.id}" and renders as nothing`));
        continue;
      }
      const declared = a.touches.includes(b.id) || b.touches.includes(a.id);

      // r1 row 6 — an UNDECLARED penetration is a lie about the model: brackets
      // buried in brick and treads run through stringers both sat under the 20 %
      // band and read as solid. A declared touch keeps the 0.2 band; `embed:
      // true` on a declared pair keeps the 0.9 one. WORKFLOW-V3 §3: up to
      // inferredContactFrac an undeclared penetration is INFERRED CONTACT (a
      // flush-seated assembly), not a clash.
      if (!declared) {
        const undeclaredBand = Math.max(ctx.L("overlapClashUndeclared"), ctx.L("inferredContactFrac"));
        if (overlap > ctx.L("undeclaredVolumeEps") && ratio > undeclaredBand) {
          violations.push(make("V6_CLASH_UNDECLARED", a.id, `${fmt(overlap)} m3 into "${b.id}" (${pct(ratio)})`,
            `0 m3 unless "${b.id}" is in touches`,
            `"${a.id}" penetrates "${b.id}" by ${fmt(overlap)} m3 without declaring it — add "${b.id}" to "${a.id}"'s touches (and embed: true if it is meant to be seated inside), or move it clear`));
        }
        continue;
      }

      if (ratio <= limits.overlapClash) continue;
      if (a.embed || b.embed) continue;                     // explicit seating, allowed
      violations.push(make("V6_CLASH", a.id, `${pct(ratio)} into "${b.id}"`, `<= ${pct(limits.overlapClash)} unless embedded`,
        `"${a.id}" and "${b.id}" interpenetrate by ${pct(ratio)} of the smaller solid — pull them apart, or set embed: true on the one that is meant to be seated inside the other`));
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V4 — ground plane and static stability. The maths is v4.js:18-66 verbatim in
// shape, re-pointed at part AABBs and real solid volumes: the assembly sits on
// y = 0 and its centre of mass is inside the hull of the parts that touch it.
// ---------------------------------------------------------------------------

function validateV4(ctx) {
  const violations = [];
  const { records, EPS } = ctx;
  if (records.length === 0) return { violations, advisories: [] };

  const minY = Math.min(...records.map((r) => r.aabb.min[1]));
  if (Math.abs(minY) > EPS) {
    const lowest = records.find((r) => r.aabb.min[1] === minY);
    violations.push(make("V4", lowest?.id ?? null, `min y = ${fmt(minY)} m`, `0 +- ${fmt(EPS)} m`,
      `the assembly sits ${fmt(Math.abs(minY))} m ${minY > 0 ? "above" : "below"} the ground plane — move every part by ${fmt(-minY)} m in y`));
    return { violations, advisories: [] };
  }

  // a hand-held class (cls.grounded false): y = 0 is its lowest point (the frame), no static-stability footprint
  if (ctx.cls.grounded === false) return { violations, advisories: [] };
  let mass = 0;
  let cx = 0;
  let cz = 0;
  const footprint = [];
  for (const record of records) {
    const volume = record.volume;
    mass += volume;
    cx += volume * (record.aabb.min[0] + record.aabb.max[0]) / 2;
    cz += volume * (record.aabb.min[2] + record.aabb.max[2]) / 2;
    if (record.aabb.min[1] <= EPS) {
      footprint.push([record.aabb.min[0], record.aabb.min[2]], [record.aabb.max[0], record.aabb.min[2]],
        [record.aabb.max[0], record.aabb.max[2]], [record.aabb.min[0], record.aabb.max[2]]);
    }
  }
  if (mass <= 0 || footprint.length === 0) return { violations, advisories: [] };

  const com = [cx / mass, cz / mass];
  const outside = distanceOutside(convexHull(footprint), com);
  if (outside > EPS) {
    violations.push(make("V4", null, `centre of mass ${fmt(outside)} m outside the footprint`, `inside +- ${fmt(EPS)} m`,
      `the model tips: centre of mass at x ${fmt(com[0])}, z ${fmt(com[1])} is ${fmt(outside)} m outside the ground-contact hull — widen the base or move mass inboard`));
  }
  return { violations, advisories: [] };
}

/** Andrew monotone chain, counter-clockwise (v4.js:69-82). */
function convexHull(points) {
  const pts = [...points].sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  if (pts.length < 3) return pts;
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const build = (list) => {
    const out = [];
    for (const p of list) {
      while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], p) <= 0) out.pop();
      out.push(p);
    }
    out.pop();
    return out;
  };
  return [...build(pts), ...build([...pts].reverse())];
}

/** 0 when inside; otherwise the distance to the nearest hull edge (v4.js:85-99). */
function distanceOutside(hull, p) {
  if (hull.length < 3) return 0;
  let worst = -Infinity;
  for (let i = 0; i < hull.length; i += 1) {
    const a = hull[i];
    const b = hull[(i + 1) % hull.length];
    const ex = b[0] - a[0];
    const ez = b[1] - a[1];
    const length = Math.hypot(ex, ez);
    if (length < 1e-12) continue;
    const signed = ((p[0] - a[0]) * ez - (p[1] - a[1]) * ex) / length;
    if (signed > worst) worst = signed;
  }
  return Math.max(0, worst);
}

// ---------------------------------------------------------------------------
// V7 — the CLOSED role table (r1 row 5), from the class prior. An author that
// invents `tread`, `rail` or `frame` bypasses every class row after it, which
// is exactly how the 0.27 m stair rise and the 0.28 m parapet got through round
// 0. The class rows themselves (limits.v7 on measured AABBs) run in the same
// slot, from the class rules, once every role is known.
// ---------------------------------------------------------------------------

/** WF v8: the roles a subject's overrides add to the closed table — the `roles` extras + a tracks / skids runner role. */
export function overrideRoles(values) {
  const run = values?.wheels?.running;
  return [...new Set([...(values?.roles?.extra ?? []), ...(RUNNER_ROLE[run] ? [RUNNER_ROLE[run]] : [])])];
}

function validateV7(ctx) {
  const violations = [];
  const classRoles = ctx.cls.roles ?? [];
  // WF v8: + the roles a subject's overrides add (roles.extra, the tracks / skids runner role; a RULE_OVERRIDE row each run)
  const roles = [...classRoles, ...overrideRoles(ctx.overrides).filter((r) => !classRoles.includes(r))];
  const hint = ctx.cls.roleHint ?? "pick the nearest role in the closed table";
  for (const record of ctx.records) {
    if (record.role === null || record.role === undefined) {
      violations.push(make("V7_ROLE", record.id, "no role", `one of: ${roles.join(", ")}`,
        `give "${record.id}" a role from the closed list — a part with no role is measured by no rule`));
      continue;
    }
    if (!roles.includes(record.role)) {
      violations.push(make("V7_ROLE", record.id, `role "${record.role}"`, `one of: ${roles.join(", ")}`,
        `"${record.id}" uses role "${record.role}", which is not in the closed role table — ${hint}`));
    }
  }
  if (violations.length > 0) return { violations, advisories: [] };
  const classRows = ctx.rules.validators.find(([name]) => name === "V7");
  return classRows ? classRows[1](ctx) : { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V12 — CENSUS (r1 row 4). The target's contents were counted ONCE, by eye, at
// 2x zoom, and frozen into subjects/<subject>/census.json. From then on nobody
// counts by vision again: the item text cites the number and this row measures
// it. Every count is taken off ROLES, never off ids, so an author cannot pass
// by naming a part "window_3".
// ---------------------------------------------------------------------------

/** Overlap of two [min,max] intervals; negative means a gap. */
const spanOverlap = (aMin, aMax, bMin, bMax) => Math.min(aMax, bMax) - Math.max(aMin, bMin);

/** Cluster values into bands no wider than `band`; returns the band count. */
function bands(values, band) {
  const sorted = [...values].sort((a, b) => a - b);
  let count = 0;
  let anchor = -Infinity;
  for (const value of sorted) {
    if (value - anchor > band) { count += 1; anchor = value; }
  }
  return count;
}

/**
 * Union-find over "ranges overlap on every listed axis", returning the GROUPS.
 * `countAssemblies` is its length; V12_LAYOUT measures the group boxes.
 */
function groupAssemblies(records, axes, pad = 0) {
  // run2 P3 fix: a ladder is two STILES 0.4-0.6 m apart plus rungs in another role,
  // so "overlap on x" split every ladder in two; `pad` lets a rule name the gap
  // that still means one assembly (ladders 0.7 m, flights = two stringers 1.5 m).
  // Union-find over "ranges overlap on every listed axis": frame + glass + rail
  // of one window are one window; two windows a metre apart are two.
  const parent = records.map((_, i) => i);
  const find = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
  for (let i = 0; i < records.length; i += 1) {
    for (let j = i + 1; j < records.length; j += 1) {
      const joined = axes.every((axis) =>
        spanOverlap(records[i].aabb.min[axis], records[i].aabb.max[axis],
          records[j].aabb.min[axis], records[j].aabb.max[axis]) > -pad - 1e-9);
      if (joined) parent[find(i)] = find(j);
    }
  }
  const groups = new Map();
  for (let i = 0; i < records.length; i += 1) {
    const root = find(i);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(records[i]);
  }
  return [...groups.values()].map((members) => ({ members, box: unionBox(members) }));
}

/** Axis-aligned union of a set of records' AABBs. */
function unionBox(members) {
  const pick = (fn, key, axis) => fn(...members.map((m) => m.aabb[key][axis]));
  return {
    min: [0, 1, 2].map((a) => pick(Math.min, "min", a)),
    max: [0, 1, 2].map((a) => pick(Math.max, "max", a)),
  };
}

function countAssemblies(records, axes, pad = 0, by = "box") {
  return (by === "part" ? groupTagged(records) : groupAssemblies(records, axes, pad)).length;
}

/**
 * WF-R5 R5-A — group by PART / ASSEMBLY, never by bounding box (a census rule's `by: "part"`): a tapered side pane's box
 * overlaps the windshield's. A helper-built member groups by its assembly id; a hand-built glass part is one instance;
 * any other hand-built member joins the instance whose box it overlaps.
 */
function groupTagged(records) {
  const groups = new Map();
  const loose = [];
  for (const r of records) {
    const a = r.part?.assembly;
    if (a?.helper && a.id) {
      const k = `a:${a.helper}:${a.id}`;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(r);
    } else if (r.zone === "glass") groups.set(`p:${r.id}`, [r]);
    else loose.push(r);
  }
  for (const r of loose) {
    const hit = [...groups.values()].find((members) => members.some((m) => aabbOverlap(m.aabb, r.aabb, -1e-9)));
    if (hit) hit.push(r); else groups.set(`p:${r.id}`, [r]);
  }
  return [...groups.values()].map((members) => ({ members, box: unionBox(members) }));
}

function validateV12(ctx) {
  const violations = [];
  const census = ctx.census;
  if (!census || typeof census !== "object") return { violations, advisories: [] };
  const band = ctx.L("censusRowBand");

  for (const [key, rule] of Object.entries(ctx.cls.censusRules ?? {})) {
    const keys = rule.sums ?? [key];
    if (!keys.some((k) => Number.isFinite(census[k]))) continue;
    const expected = keys.reduce((sum, k) => sum + (Number.isFinite(census[k]) ? census[k] : 0), 0);
    const records = ctx.records.filter((r) => r.role === rule.role);
    const measured = rule.kind === "band"
      ? bands(records.map((r) => (r.aabb.min[rule.axis] + r.aabb.max[rule.axis]) / 2), band)
      : countAssemblies(records, rule.axes, rule.pad ?? 0, rule.by);
    if (measured !== expected) {
      violations.push(make("V12_CENSUS", null, `${measured} ${rule.label}`, `${expected}`,
        `the target has ${expected} ${rule.label} and the model has ${measured} — ${measured < expected ? `add ${expected - measured}` : `remove ${measured - expected}`} (role "${rule.role}"; the count is taken off the role, not the part name)`));
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V12_LAYOUT — MEASURED PROPORTION (r2 rows B1/B2, re-based by r3 row C1.3).
// The census counts but carries no dimension, so every metre in run 2 was
// invented by the author (WF-LOOP-R2 C3). `subjects/<s>/layout.json` carries the
// target's proportions as FRACTIONS of the face width W and the wall height H,
// measured in the author frame — camera-free, so the row cannot be fooled by a
// rescale or a re-solve. Like the census it is DATA the caller supplies through
// `options.layout`; `meta.layout === false` opts a module out, and a key whose
// role is not built yet is SKIPPED, which stages the row for free (no windows at
// P0 = no window keys measured).
//
// r3 C1.3, the three things that changed after the r3 audits:
//   1. The FILE is now generated by `scripts/measure-target.mjs --freeze` off the
//      target's pixels. Round 2's numbers came off a 261 px "face" that was the
//      front PLUS the side return, so every fraction along W was wrong and this
//      row enforced the error to +/- 0.05 (fable-audit §2 C1).
//   2. Fractions along W are measured from the STREET-RIGHT edge of the face.
//      The author frame puts street-right at -x (src/kernel/README.md), so the
//      massing's MIN x is the origin of the measurement and `(x - F.x0)/F.W` is
//      already that fraction — the same quantity the scan reads as `(x1 - cx)/W`.
//   3. A key carrying `unverified: true` is SKIPPED and REPORTED as an advisory.
//      It is never enforced: the measurement could not resolve it, and a gate
//      that enforces an unresolved number is how run 3 was lost.
// ---------------------------------------------------------------------------

/** Cluster values into bands no wider than `eps`; returns each band's mean. */
function clusters(values, eps) {
  const sorted = [...values].sort((a, b) => a - b);
  const out = [];
  let bucket = [];
  for (const value of sorted) {
    if (bucket.length > 0 && value - bucket[bucket.length - 1] > eps) { out.push(bucket); bucket = []; }
    bucket.push(value);
  }
  if (bucket.length > 0) out.push(bucket);
  return out.map((b) => b.reduce((sum, x) => sum + x, 0) / b.length);
}

/** The layout keys this row knows how to measure; a key outside it is ignored. */
export const LAYOUT_KEYS = Object.freeze(Object.keys(FALLBACK_RULES.layoutRules));

/** null when the measurement is inside the entry's band, else the band + miss. */
function layoutCheck(entry, measured) {
  if (typeof entry.value === "string" || typeof measured === "string") {
    return entry.value === measured ? null : { limit: `"${entry.value}"`, delta: 0, text: `"${measured}"` };
  }
  const tol = Number.isFinite(entry.tol) ? entry.tol : 0.05;
  if (Number.isFinite(entry.value)) {
    const delta = measured - entry.value;
    return Math.abs(delta) <= tol + 1e-9 ? null : { limit: `${fmt(entry.value)} +/- ${fmt(tol)}`, delta };
  }
  const lo = Number.isFinite(entry.min) ? entry.min : -Infinity;
  const hi = Number.isFinite(entry.max) ? entry.max : Infinity;
  if (measured >= lo - 1e-9 && measured <= hi + 1e-9) return null;
  const limit = lo === -Infinity ? `<= ${fmt(hi)}`
    : hi === Infinity ? `>= ${fmt(lo)}`
      : `${fmt(lo)}..${fmt(hi)}`;
  return { limit, delta: measured < lo ? measured - lo : measured - hi };
}

function validateV12Layout(ctx) {
  const violations = [];
  const advisories = [];
  const layout = ctx.layout;
  if (!layout || typeof layout !== "object") return { violations, advisories };
  if (typeof ctx.rules.layoutFrame !== "function") return { violations, advisories };
  const F = ctx.rules.layoutFrame(ctx);
  if (!F) return { violations, advisories };

  for (const [key, rule] of Object.entries(ctx.rules.layoutRules ?? {})) {
    const entry = layout[key];
    if (!entry || typeof entry !== "object") continue;
    // Staging for free: a key whose role has not been built yet stands down.
    if (rule.roles.some((role) => !ctx.records.some((r) => r.role === role))) continue;

    // r3 C1.3: an UNVERIFIED key is reported, never enforced.
    if (entry.unverified === true) {
      advisories.push(advise("V12_LAYOUT", null, `${key} UNVERIFIED`, "not enforced",
        `layout.json "${key}" carries no measurement — ${entry.reason ?? "the scan could not resolve it"}. `
        + "Nothing gates this dimension; do not read a number into the silence."));
      continue;
    }

    const unit = entry.unit ?? rule.unit ?? "";
    const source = entry.source ? ` (source: ${entry.source})` : "";
    const measurements = rule.measure(ctx, F);
    if (measurements.length === 0) continue;

    if (Array.isArray(entry.values)) {
      const expected = [...entry.values].sort((a, b) => a - b);
      const got = measurements.map((m) => m.measured).sort((a, b) => a - b);
      if (got.length !== expected.length) {
        violations.push(make("V12_LAYOUT", null, `${key} ${got.length} ${rule.list ?? "values"}`, `${expected.length}`,
          `layout.json "${key}" lists ${expected.length} ${rule.list ?? "values"} (${expected.map(fmt).join(", ")} ${unit}) and the model has ${got.length}${source}`));
        continue;
      }
      const extentL = typeof rule.extent === "function" ? rule.extent(layout, F) : null;
      const tol = Math.min(Number.isFinite(entry.tol) ? entry.tol : 0.05, Number.isFinite(extentL) ? (ctx.rules.POSITION_TOL_SHARE ?? 0.25) * extentL : Infinity);
      for (let i = 0; i < got.length; i += 1) {
        const delta = got[i] - expected[i];
        if (Math.abs(delta) <= tol + 1e-9) continue;
        violations.push(make("V12_LAYOUT", null, `${key} ${fmt(got[i])} ${unit}`, `${fmt(expected[i])} +/- ${fmt(tol)} ${unit}`,
          `layout.json "${key}" puts ${rule.list ?? "this feature"} at ${fmt(expected[i])} of the face (+/- ${fmt(tol)}) and the model measures ${fmt(got[i])} — move it by ${fmt(-delta * F.W)} m in x${source}`));
        break;
      }
      continue;
    }

    // WF-R3 R3-B item 3 — a POSITION key's tol is capped at a share of the feature's own extent (rule.extent).
    const extent = typeof rule.extent === "function" ? rule.extent(layout, F) : null;
    const capped = Number.isFinite(extent) && Number.isFinite(entry.value)
      ? { ...entry, tol: Math.min(Number.isFinite(entry.tol) ? entry.tol : 0.05, (ctx.rules.POSITION_TOL_SHARE ?? 0.25) * extent) } : entry;
    for (const item of measurements) {
      const miss = layoutCheck(capped, item.measured);
      if (!miss) continue;
      const who = item.id ? `"${item.id}"` : "the model";
      const got = miss.text ?? fmt(item.measured);
      violations.push(make("V12_LAYOUT", item.id, `${key} ${got} ${unit}`, `${miss.limit} ${unit}`,
        miss.text
          ? `layout.json "${key}" wants ${miss.limit} and ${who} is on ${got} — ${rule.mismatchHint ?? "match the target"}${source}`
          : `layout.json "${key}" wants ${miss.limit} ${unit} and ${who} measures ${got} — ${miss.delta > 0 ? "reduce" : "increase"} it by ${fmt(Math.abs(miss.delta))} ${unit}${source}`));
      break;                                            // one line per key, not one per part
    }
  }
  return { violations, advisories };
}

// ---------------------------------------------------------------------------
// V10 — export sanity: inside the triangle budget, one material, no NaN.
// ---------------------------------------------------------------------------

// The effective triangle budget: a subject's `tris` override, else the module's meta.triBudget, else the class's.
export function triBudgetOf(meta, cls, overrides) {
  if (Number.isFinite(overrides?.tris)) return overrides.tris;
  return Number.isFinite(meta?.triBudget) ? meta.triBudget : cls.triBudget;
}

function validateV10(ctx) {
  const violations = [];
  const budget = triBudgetOf(ctx.meta, ctx.cls, ctx.overrides);
  const tris = ctx.merged.solved.triangles;

  if (tris > budget) {
    violations.push(make("V10", null, `${tris} triangles`, `<= ${budget}`,
      `the model is ${tris - budget} triangles over the ${budget} budget — drop facet counts (arch segs, revolve segs) or merge repeats`));
  }
  if (!(tris > 0)) {
    violations.push(make("V10", null, `${tris} triangles`, "> 0", "build() produced no geometry at all"));
  }

  const geometry = ctx.merged.geometry;
  const groups = geometry.groups ?? [];
  if (groups.length > 1) {
    violations.push(make("V10", null, `${groups.length} material groups`, "<= 1",
      "the merged geometry carries more than one material group — one draw call is the contract"));
  }
  for (const name of ["position", "color"]) {
    const attribute = geometry.getAttribute(name);
    if (!attribute) {
      violations.push(make("V10", null, `no "${name}" attribute`, `"${name}" present`,
        `the merged geometry has no ${name} attribute — the GLB would export blank`));
      continue;
    }
    let bad = 0;
    for (const value of attribute.array) if (!Number.isFinite(value)) bad += 1;
    if (bad > 0) {
      violations.push(make("V10", null, `${bad} non-finite ${name} values`, "0",
        `the merged geometry carries ${bad} NaN/Inf ${name} values`));
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// The chain.
// ---------------------------------------------------------------------------

/**
 * The generic spine with the class rules spliced in: the class's "V7" rows run
 * inside the V7 slot (after the closed-role check); every other class validator
 * runs, in the class's own order, between V7 and the census — for buildings the
 * r1 rows 2, 7, 8, 9 buildability checks, after the model is known to stand up
 * and before it is counted.
 */
function chainFor(rules) {
  const classSteps = (rules.validators ?? []).filter(([name]) => name !== "V7");
  return [
    ["V1", validateV1],
    ["V5", validateV5],
    ["V2", validateV2],
    ["V3", validateV3],
    ["V6", validateV6],
    ["V4", validateV4],
    ["V7", validateV7],
    ...classSteps,
    // r1 row 4 — the frozen contents count, last before export sanity.
    ["V12", validateV12],
    // r2 rows B1/B2 — the frozen PROPORTIONS, measured once the counts are right:
    // there is no point measuring the centre of a bay that is not there yet.
    ["V12_LAYOUT", validateV12Layout],
    // WF-BLIND-R2 C4/C10 — after every geometry row, so a zone slip never hides a buildability row.
    ["PALETTE_ZONE", validatePaletteZone],
    ["V10", validateV10],
  ];
}

/** `options.cls` + `options.rules`, or the fallback class when no prior is given. */
function resolvePrior(options) {
  if (!options.cls) return { cls: FALLBACK_CLASS, rules: FALLBACK_RULES };
  if (!options.rules) {
    throw new Error(`validateParts: options.cls ("${options.cls.class ?? "?"}") was given without options.rules — `
      + "import the module the class names in `rules` and pass it too");
  }
  if (!Number.isFinite(options.cls.triBudget)) {
    throw new Error(`validateParts: class "${options.cls.class ?? "?"}" carries no numeric triBudget`);
  }
  return { cls: options.cls, rules: options.rules };
}

/**
 * Validate one authored module's output.
 *
 * @param {{class?:string, seed?:number|string, palette?:object, triBudget?:number, floorH?:number}} meta
 * @param {Array<{id:string, solid:object, zone:string, role?:string, touches?:string[], embed?:boolean}>} parts
 * @param {object} [limits] limits.json (frozen; never written by this chain)
 * @param {{census?:object|null, layout?:object|null, cls?:object, rules?:object}} [options] r1 row 4 /
 *   r2 row B2: the subject's frozen contents count
 *   (`subjects/<subject>/census.json`) and its frozen proportions
 *   (`subjects/<subject>/layout.json`), supplied by the caller — this module
 *   never touches the filesystem. V12 is skipped when no census is supplied and
 *   when the module declares `meta.census === false`; V12_LAYOUT likewise when
 *   no layout is supplied or `meta.layout === false`. WORKFLOW-V3 §7.5: `cls` is
 *   the parsed `classes/<class>.json` and `rules` the imported module it names
 *   (`{layoutRules, layoutFrame, validators}`); both absent = the fallback class.
 * @returns {Promise<{pass:boolean, violations:Array, advisories:Array, text:string,
 *                    measurements:object, timings:object}>}
 *
 * `timings` is the only non-deterministic key: two runs over the same parts
 * return byte-identical {pass, violations, advisories, text, measurements}.
 */
export async function validateParts(meta, parts, baseLimits = DEFAULT_LIMITS, options = {}) {
  const timings = {};
  const started = Date.now();

  const prior = resolvePrior(options ?? {});
  // V5-8 R2: the subject's measured overrides (options.ruleOverrides, else the class prior subject.mjs merged them into)
  const over = applyRuleOverrides(baseLimits, options?.ruleOverrides ?? prior.cls?.ruleOverrides);
  const limits = over.limits;
  const ctx = buildContext(meta ?? {}, parts ?? [], limits, options ?? {}, prior);
  ctx.waived = over.waived;
  ctx.overrides = over.values;   // WF v8 WP2: the wheels / paletteZones override values the class rows read
  const mergeStarted = Date.now();
  ctx.merged = partsToGeometry(parts ?? [], meta?.palette ?? {}, meta?.seed ?? 1);
  timings.merge = Date.now() - mergeStarted;

  const violations = [];
  const advisories = [...over.rows];
  for (const [name, step] of chainFor(prior.rules)) {
    // WORKFLOW v4 V4-2 — scripts/fit.mjs runs the cheap rows per eval and the whole chain per sweep.
    if (Array.isArray(options?.skip) && options.skip.includes(name)) continue;
    const at = Date.now();
    const result = step(ctx);
    timings[name] = Date.now() - at;
    for (const item of result.advisories ?? []) advisories.push(item);
    if (result.violations.length > 0) {
      for (const item of result.violations) violations.push(item);
      break;
    }
  }
  timings.total = Date.now() - started;

  const blocking = violations.filter((x) => x.blocking !== false);
  return {
    pass: blocking.length === 0,
    violations: blocking,
    advisories: [...advisories, ...violations.filter((x) => x.blocking === false)],
    text: reportText(blocking),
    measurements: {
      parts: ctx.records.length,
      tris: ctx.merged.solved.triangles,
      triBudget: triBudgetOf(meta, prior.cls, over.values),
      materials: 1,
      bounds: ctx.merged.bounds,
      minFeature: ctx.MIN_FEAT,
      // WF-BLIND-R2 C14 — the configuration this report measured under; pass.mjs refuses a mismatch.
      gateDigest: gateConfig(options?.ruleOverrides ? { ...prior.cls, ruleOverrides: options.ruleOverrides } : prior.cls, baseLimits).digest,
      eps: ctx.EPS,
      census: ctx.census ? "applied" : "skipped",
      layout: ctx.layout ? "applied" : "skipped",
      booleanPairs: ctx.counts.intersections.size,
      distancePairs: ctx.counts.distances.size,
      // WORKFLOW-V3 §3 — contacts the harness inferred (null when the chain
      // stopped before V2 needed them).
      inferredPairs: ctx.inferredPairs,
      perPart: ctx.records.map((r) => ({
        id: r.id, role: r.role, zone: r.zone, tris: r.tris,
        volume: Math.round(r.volume * 1e6) / 1e6,
        aabb: r.aabb, touches: r.touches,
      })),
    },
    timings,
  };
}

/**
 * WF-R3 — the measured context one validator step reads (tests call a single class row on it, past an earlier
 * failing step the chain would stop at).
 */
export function chainContext(meta, parts, baseLimits = DEFAULT_LIMITS, options = {}) {
  const prior = resolvePrior(options ?? {});
  const over = applyRuleOverrides(baseLimits, options?.ruleOverrides ?? prior.cls?.ruleOverrides);
  const ctx = buildContext(meta ?? {}, parts ?? [], over.limits, options ?? {}, prior);
  ctx.waived = over.waived;
  ctx.overrides = over.values;
  return ctx;
}

// `advise` is exported for a future non-blocking row; referenced here so the
// shape of an advisory stays pinned next to `make`.
export { make as makeViolation, advise as makeAdvisory };
