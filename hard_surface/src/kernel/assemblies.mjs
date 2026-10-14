// Kernel ASSEMBLY helpers for repeated hard-surface topology (WORKFLOW-V3 §3, §7 item 9).
//
// Run 3 and run 4 both lost their ironwork rows twice: the author hand-placed
// ~200 bars and invented an AABB auto-`touches` crutch to survive V6. These
// helpers build a grate, a stair flight, a ladder, a guarded landing and a
// window frame in ONE call each, laid out so the buildability gates pass by
// construction:
//   - every member is >= the style floor (V5),
//   - every joint is a seat of `seat` metres, far inside inferredContactFrac,
//     so the harness infers the contact (V2/V3) and never sees a clash (V6),
//   - deck slots, landing gap, ladder head gate, riser pitch, stair rail band
//     and bearing come from the SAME numbers the gate reads (limits.json +
//     KERNEL_LIMIT_DEFAULTS), never from a restated constant.
//
// Every helper returns `[{ id, solid, role, zone }]` (no `touches`: the harness
// infers contact). Deterministic: pure maths over kernel boxes, no clock/RNG.
//
// Import note: kernel-chain.mjs (which owns KERNEL_LIMIT_DEFAULTS) imports the
// kernel, and rules/building.mjs imports the kernel too. A STATIC import of
// kernel-chain from here closes the cycle rules -> kernel -> here -> chain ->
// rules and the chain reads `layoutRules` before it exists whenever rules is
// loaded first. So the chain is loaded DYNAMICALLY: it resolves once the static
// graph has finished evaluating, i.e. before `await K.init()` returns. `ready`
// is the promise, for a caller that wants to await it explicitly.
import * as K from "./index.mjs";
import { KernelError, fillet, roundRect as roundRectProfile } from "./profile.mjs";
import GATE_LIMITS from "../validate/limits.json" with { type: "json" };

let KERNEL_LIMIT_DEFAULTS = null;
let chainLoadError = null;
export const ready = import("../validate/kernel-chain.mjs").then(
  (chain) => { KERNEL_LIMIT_DEFAULTS = chain.KERNEL_LIMIT_DEFAULTS; },
  (error) => { chainLoadError = error; },
);

// ---------------------------------------------------------------------------
// The defaults TABLE. The kernel hard-codes no class: role names, zone names
// and the style-floor key below are the building class's, and a caller replaces
// the whole table with `withDefaults(table)` (or overrides per call with
// `roles` / `zone(s)` / `limits`).
// ---------------------------------------------------------------------------

export const DEFAULT_TABLE = Object.freeze({
  /** limits.json styleFloor key -> MIN_FEAT. */
  styleFloorKey: "building",
  roles: Object.freeze({
    grate: Object.freeze({ deck: "landing", frame: "support" }),
    landing: Object.freeze({ deck: "landing", frame: "support", bracket: "support", rail: "railing", baluster: "baluster" }),
    flight: Object.freeze({ stringer: "stringer", step: "step", rail: "railing", post: "baluster" }),
    ladder: Object.freeze({ stile: "ladder", rung: "rung" }),
    frame: Object.freeze({ frame: "window", glass: "window", sill: "sill", bracket: "support" }),
  }),
  zones: Object.freeze({
    iron: "iron",
    frame: Object.freeze({ frame: "frame", glass: "glass", sill: "sill", bracket: "sill" }),
  }),
  // Construction choices NO gate reads (visual spacing only). Everything else
  // is derived from the gate config per call.
  construction: Object.freeze({
    rungPitch: 0.3, balusterPitch: 0.8,
    // WF-R3 H4 — fireEscape construction numbers no gate reads: flight width, the clear deck left at each end of a
    // flight, the head room a hatch opens over a flight, and the drop ladder's stile spacing.
    flightWidth: 0.72, endClear: 0.6, headroom: 2.0, dropWidth: 0.5,
  }),
  /** WF-R3 H4 — roles a drop ladder may not hang past (fireEscape refuses; V11_DROP_LADDER reports). */
  dropClearRoles: Object.freeze(["awning"]),
});

const EPS = 1e-9;

function fail(message) {
  throw new KernelError(`BAD_ARG: ${message}`);
}

const f3 = (v) => (Math.round(v * 1000) / 1000).toFixed(3);

function finite(value, what) {
  if (typeof value !== "number" || !Number.isFinite(value)) fail(`${what} must be a finite number, got ${JSON.stringify(value)}`);
  return value;
}

function vec(v, n, what) {
  if (!Array.isArray(v) || v.length < n) fail(`${what} must be [${"xyz".slice(0, n).split("").join(", ")}]`);
  return v.slice(0, n).map((x, i) => finite(x, `${what}[${i}]`));
}

/** The gate numbers for one call: limits.json + KERNEL_LIMIT_DEFAULTS, same lookup as kernel-chain. */
function gateOf(o) {
  if (!KERNEL_LIMIT_DEFAULTS) {
    throw new KernelError("KERNEL_UNINIT: K.assemble reads the gate defaults from src/validate/kernel-chain.mjs — "
      + `await K.init() (or K.assemble.ready) before building${chainLoadError ? ` (load failed: ${chainLoadError.message})` : ""}`);
  }
  const table = o.table ?? DEFAULT_TABLE;
  const limits = o.limits ?? GATE_LIMITS;
  const L = (k) => (limits?.[k] !== undefined ? limits[k] : KERNEL_LIMIT_DEFAULTS[k]);
  const floors = limits.styleFloor ?? GATE_LIMITS.styleFloor;
  const MIN_FEAT = floors[table.styleFloorKey] ?? floors.prop;
  const epsAbs = limits.epsAbs ?? GATE_LIMITS.epsAbs;
  const v7 = limits.v7 ?? GATE_LIMITS.v7;
  return {
    table,
    MIN_FEAT,
    epsAbs,
    // A seat is an overlap the chain must read as CONTACT: an order of magnitude
    // under both the contact distance and the inferred-contact fraction of the
    // thinnest legal member.
    seat: Math.min(epsAbs, L("inferredContactFrac") * MIN_FEAT) / 10,
    deckGapMax: L("deckGapMax"),
    landingGapMax: L("landingGapMax"),
    bearingGrid: L("bearingGrid"),
    bearingSpan: L("bearingSpan"),
    ladderHeadSlack: L("ladderHeadSlack"),
    ladderHeadBand: L("ladderHeadBand"),
    ladderLandingReach: L("ladderLandingReach"),
    deckGapMaxGate: L("deckGapMax"),
    stairRailBand: L("stairRailBand"),
    stepRise: v7.step_rise,
    railingH: v7.railing_h,
    grooveDepthMax: L("grooveDepthMax"),
  };
}

const mid = (band) => (band[0] + band[1]) / 2;

function rolesOf(g, helper, override) {
  return { ...g.table.roles[helper], ...(override ?? {}) };
}

function floorCheck(g, value, what) {
  if (!(value >= g.MIN_FEAT - EPS)) fail(`${what} ${f3(value)} m is under MIN_FEAT ${g.MIN_FEAT} m (V5) — raise it`);
}

/** Axis-aligned box from its min and max corners. */
function bx(lo, hi, what) {
  const d = [0, 1, 2].map((i) => hi[i] - lo[i]);
  if (d.some((v) => !(v > 0))) fail(`${what} has a non-positive extent ${d.map(f3).join(" x ")}`);
  return K.box(d).at([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]);
}

/** A bar of `section` (in the x-y plane) whose CENTRELINE runs p0 -> p1, spanning z0..z1. */
function sloped(p0, p1, section, z0, z1) {
  const dx = p1[0] - p0[0];
  const dy = p1[1] - p0[1];
  const length = Math.hypot(dx, dy);
  // K.box grows along +y from the origin; rotZ(phi) sends +y to (-sin phi, cos phi).
  const phi = Math.atan2(-dx, dy) * 180 / Math.PI;
  return K.box([section, length, z1 - z0]).rotZ(phi).at([p0[0], p0[1], (z0 + z1) / 2]);
}

/**
 * WF-BLIND-R2 C2 — every helper part carries `assembly: { helper, id }` (a landing's also its declared
 * gates), so the gate can tell helper-built ironwork from hand-placed bars and honour a helper's gateAt.
 */
const part = (id, solid, role, zone, assembly = null) => (assembly ? { id, solid, role, zone, assembly } : { id, solid, role, zone });
const tag = (helper, id, extra = {}) => Object.freeze({ helper, id, ...extra });

// ---------------------------------------------------------------------------
// WF-BLIND-R2 C2 — the wall plane is a KERNEL QUERY, never a caller guess, and
// the landing gate is ONE computation shared by K.assemble.landing and the
// V11_LANDING_GUARD row (src/validate/rules/building.mjs), so a helper-built
// landing and the rule can never disagree about where a gate is.
// ---------------------------------------------------------------------------

/**
 * The planes of the parts of `roles` (default the massing), in the author frame:
 * `{ front, back, streetRight, streetLeft, ground, top, W, H, depth }` — front = the min-z face,
 * streetRight = min x, streetLeft = max x.
 */
export function wallPlanes(parts, { roles = ["massing"] } = {}) {
  if (!Array.isArray(parts)) fail("wallPlanes needs the parts array built so far");
  const boxes = parts.filter((p) => p && roles.includes(p.role) && K.isSolid(p.solid)).map((p) => p.solid.aabb());
  if (boxes.length === 0) fail(`wallPlanes: no part of role ${roles.join("/")} to take the wall plane from — build the massing first`);
  const lo = (i) => Math.min(...boxes.map((b) => b.min[i]));
  const hi = (i) => Math.max(...boxes.map((b) => b.max[i]));
  return {
    front: lo(2), back: hi(2), streetRight: lo(0), streetLeft: hi(0), ground: lo(1), top: hi(1),
    W: hi(0) - lo(0), H: hi(1) - lo(1), depth: hi(2) - lo(2),
  };
}

/** A deck box's plan edges: [name, axis the edge is normal to, its coordinate, outward sign, axis it runs along]. */
export function landingEdges(box) {
  return [
    ["front", 2, box.min[2], -1, 0], ["back", 2, box.max[2], 1, 0],
    ["street-right end", 0, box.min[0], -1, 2], ["street-left end", 0, box.max[0], 1, 2],
  ];
}

/**
 * The GATES of one deck: every ladder stile / stair stringer solid in `heads` that reaches the deck's head zone
 * (plan box +/- (reach + slack), deck top +/- headBand) is intersected with that zone; the piece's extent along an
 * edge it lies next to (within reach + slack), widened by `slack` either side, is a gate span on that edge.
 * @returns {{ headBoxes: Array<{min:number[],max:number[]}>, spans: Record<string, Array<[number, number]>> }}
 */
export function gateSpans({ box, heads, reach, slack, headBand }) {
  const top = box.max[1];
  const spanOverlap = (aMin, aMax, bMin, bMax) => Math.min(aMax, bMax) - Math.max(aMin, bMin);
  const zone = K.box([box.max[0] - box.min[0] + 2 * (reach + slack), 2 * headBand, box.max[2] - box.min[2] + 2 * (reach + slack)])
    .at([(box.min[0] + box.max[0]) / 2, top - headBand, (box.min[2] + box.max[2]) / 2]);
  const headBoxes = [];
  for (const solid of heads) {
    const a = solid.aabb();
    if (spanOverlap(a.min[1], a.max[1], top - headBand, top + headBand) <= 0) continue;
    if (spanOverlap(a.min[0], a.max[0], box.min[0] - reach - slack, box.max[0] + reach + slack) <= 0) continue;
    if (spanOverlap(a.min[2], a.max[2], box.min[2] - reach - slack, box.max[2] + reach + slack) <= 0) continue;
    const inside = K.intersect(solid, zone);
    if (inside.volume() > 1e-9) headBoxes.push(inside.aabb());
  }
  const spans = {};
  for (const [name, a, c, , b] of landingEdges(box)) {
    const pad = reach + slack;
    spans[name] = headBoxes.filter((hb) => spanOverlap(hb.min[a], hb.max[a], c - pad, c + pad) > -1e-9)
      .map((hb) => [hb.min[b] - slack, hb.max[b] + slack]);
  }
  return { headBoxes, spans };
}

// ---------------------------------------------------------------------------
// WF-R3 H4 — ONE predicate for "a flight arrives ON a deck", shared by K.assemble.flight({ decks }), the landing's
// gateFor check, K.assemble.fireEscape and the V11_FLIGHT_ON_DECK row: a tread lies ON a deck when its plan box is
// inside the deck's plan box grown by one tread (its own going) and its top is within maxRise of the deck top.
// ---------------------------------------------------------------------------

/** Index of the deck box the tread box lies on, or -1. */
export function deckOf(tread, decks, maxRise) {
  const going = Math.min(tread.max[0] - tread.min[0], tread.max[2] - tread.min[2]);
  return decks.findIndex((d) => Math.abs(tread.max[1] - d.max[1]) <= maxRise + 1e-6
    && [0, 2].every((a) => tread.min[a] >= d.min[a] - going - 1e-9 && tread.max[a] <= d.max[a] + going + 1e-9));
}

/** A flight's bottom and top tread boxes and the deck each lies on (-1 = none). */
export function flightArrivals(treads, decks, maxRise) {
  const sorted = [...treads].sort((a, b) => a.max[1] - b.max[1]);
  const bottom = sorted[0];
  const top = sorted[sorted.length - 1];
  return { bottom, top, bottomDeck: deckOf(bottom, decks, maxRise), topDeck: deckOf(top, decks, maxRise) };
}

/** Deck boxes of the parts of role `role` (default the landing deck role), one per y level. */
export function deckBoxes(parts, role = DEFAULT_TABLE.roles.landing.deck) {
  const boxes = parts.filter((p) => p && p.role === role && K.isSolid(p.solid)).map((p) => p.solid.aabb())
    .sort((a, b) => a.min[1] - b.min[1]);
  const levels = [];
  for (const b of boxes) {
    const last = levels[levels.length - 1];
    if (last && b.min[1] <= last.max[1] + 1e-9) {
      for (let i = 0; i < 3; i += 1) { last.min[i] = Math.min(last.min[i], b.min[i]); last.max[i] = Math.max(last.max[i], b.max[i]); }
    } else levels.push({ min: [...b.min], max: [...b.max] });
  }
  return levels;
}

const overlap1 = (a0, a1, b0, b1) => Math.min(a1, b1) - Math.max(a0, b0);
/** [lo, hi] minus every [p, q] in `holes`, pieces shorter than `min` dropped. */
function subtract(lo, hi, holes, min) {
  let pieces = [[lo, hi]];
  for (const [p, q] of holes) {
    pieces = pieces.flatMap(([a, b]) => (overlap1(a, b, p, q) > 0 ? [[a, Math.min(b, p)], [Math.max(a, q), b]] : [[a, b]]));
  }
  return pieces.filter(([a, b]) => b - a >= min - EPS);
}

// ---------------------------------------------------------------------------
// grate — deck bars across the depth, carried by an edge frame underneath.
// at = [centre x, deck TOP y, z of the plane the back edge hangs off].
// The deck runs from that plane toward -z by d.
// ---------------------------------------------------------------------------

function buildGrate(o, g, roles, zone, prefix) {
  const w = finite(o.w, "grate w");
  const d = finite(o.d, "grate d");
  const bar = o.bar === undefined ? g.MIN_FEAT : finite(o.bar, "grate bar");
  const maxGap = o.maxGap === undefined ? g.deckGapMax : finite(o.maxGap, "grate maxGap");
  const [cx, top, backPlane] = vec(o.at, 3, "grate at");
  floorCheck(g, bar, "grate bar");
  if (!(maxGap > 0)) fail(`grate maxGap must be > 0, got ${maxGap}`);
  if (!(w >= bar)) fail(`grate w ${f3(w)} m is narrower than one bar (${f3(bar)} m)`);
  if (!(d > 2 * bar)) fail(`grate d ${f3(d)} m must exceed two bars (${f3(2 * bar)} m) so the frame fits under it`);

  const { seat } = g;
  const zBack = backPlane + seat;
  const zFront = zBack - d;
  const left = cx - w / 2;
  const right = cx + w / 2;
  const parts = [];

  // Bars: equal pitch, slot = pitch - bar <= maxGap (V11_DECK_GAP).
  // WF-R3 H4 — `hatches` ([{x0, x1, z0, z1}], internal to fireEscape) open the deck over a flight: a bar or bearer
  // crossing a hatch keeps only its pieces outside it (pieces under two bars long are dropped).
  const hatches = o.hatches ?? [];
  const { n, pitch, xs: barXs } = barLayout(w, bar, maxGap, cx);
  const reachesFront = [];
  // V5-7 — `plate: true`: ONE solid deck plate (the stylised targets draw a plate, not a grating: a grating's bars
  // are ink the target does not have), the hatches cut out of it. V11_DECK_GAP has no slot to see; the bearers below
  // carry it (V11_BEARING) exactly as they carry bars.
  if (o.plate) {
    let plate = bx([left, top - bar, zFront], [right, top, zBack], "grate plate");
    for (const h of hatches) plate = K.cut(plate, bx([h.x0, top - 2 * bar, Math.max(zFront - bar, h.z0)], [h.x1, top + bar, Math.min(zBack + bar, h.z1)], "grate hatch"));
    parts.push(part(`${prefix}_plate`, plate, roles.deck, zone));
    for (let i = 0; i < n; i += 1) reachesFront.push(!hatches.some((h) => overlap1(barXs[i] - bar / 2, barXs[i] + bar / 2, h.x0, h.x1) > 0 && h.z0 <= zFront + EPS));
  }
  for (let i = 0; i < (o.plate ? 0 : n); i += 1) {
    const x = barXs[i];
    const holes = hatches.filter((h) => overlap1(x - bar / 2, x + bar / 2, h.x0, h.x1) > 0).map((h) => [h.z0, h.z1]);
    const pieces = subtract(zFront, zBack, holes, 2 * bar);
    reachesFront.push(pieces.some(([a]) => a <= zFront + EPS));
    pieces.forEach(([a, b], k) => parts.push(part(`${prefix}_bar_${i}${k ? `_${k}` : ""}`,
      bx([x - bar / 2, top - bar, a], [x + bar / 2, top, b], "grate bar"), roles.deck, zone)));
  }

  // Bearers along x under the bars. V11_BEARING samples each bar on a grid and
  // needs a carrier AABB over a sample centre: an edge bearer >= grid/2 wide
  // always covers the edge sample; an interior one is a full grid wide.
  const bearerY0 = top - 2 * bar;
  const bearerY1 = top - bar + seat;
  const count = Math.max(2, Math.ceil(d / g.bearingSpan - EPS) + 1);
  const edgeW = Math.max(bar, g.bearingGrid / 2);
  const innerW = Math.max(bar, g.bearingGrid);
  const bearers = [];
  for (let i = 0; i < count; i += 1) {
    let z0;
    let z1;
    if (i === 0) { z0 = zFront; z1 = zFront + edgeW; }
    else if (i === count - 1) { z0 = zBack - edgeW; z1 = zBack; }
    else {
      const c = zFront + (i * d) / (count - 1);
      z0 = c - innerW / 2;
      z1 = c + innerW / 2;
    }
    bearers.push([z0, z1]);
    const holes = hatches.filter((h) => overlap1(z0, z1, h.z0, h.z1) > 0).map((h) => [h.x0, h.x1]);
    subtract(left, right, holes, 2 * bar).forEach(([a, b], k) => parts.push(part(`${prefix}_bearer_${i}${k ? `_${k}` : ""}`,
      bx([a, bearerY0, z0], [b, bearerY1, z1], "grate bearer"), roles.frame, zone)));
  }
  // Side edge members between consecutive bearers, under the end bars.
  for (let i = 0; i + 1 < bearers.length; i += 1) {
    const z0 = bearers[i][1] - seat;
    const z1 = bearers[i + 1][0] + seat;
    if (z1 - z0 < g.MIN_FEAT - EPS) continue;
    for (const [side, x0] of [["l", left], ["r", right - bar]]) {
      if (hatches.some((h) => overlap1(x0, x0 + bar, h.x0, h.x1) > 0 && overlap1(z0, z1, h.z0, h.z1) > 0)) continue;
      parts.push(part(`${prefix}_edge_${side}_${i}`, bx([x0, bearerY0, z0], [x0 + bar, bearerY1, z1], "grate edge"),
        roles.frame, zone));
    }
  }
  return { parts, barXs, pitch, bar, left, right, zFront, zBack, bottom: bearerY0, reachesFront };
}

/** Deck bar count, pitch and centres across a span `w` centred on `cx` (slots <= maxGap). */
function barLayout(w, bar, maxGap, cx) {
  const n = Math.max(2, Math.ceil((w - bar) / (bar + maxGap) - EPS) + 1);
  const pitch = (w - bar) / (n - 1);
  return { n, pitch, xs: Array.from({ length: n }, (_, i) => cx - w / 2 + bar / 2 + i * pitch) };
}

export function grate(o = {}) {
  const g = gateOf(o);
  const prefix = o.idPrefix ?? "grate";
  const assembly = tag("grate", prefix);
  return buildGrate(o, g, rolesOf(g, "grate", o.roles), o.zone ?? g.table.zones.iron, prefix).parts.map((p) => ({ ...p, assembly }));
}

// ---------------------------------------------------------------------------
// landing — grate + brackets to the wall + guard (front rail, returns,
// balusters) with a gate gap wherever a ladder or flight arrives.
// at = [centre x, deck TOP y]; wall = the parts built so far (the front plane is
// taken from their massing, WF-BLIND-R2 C2), or wallZ = that plane's z.
// gateFor = the flight / ladder PARTS that arrive at this deck: the gate is the
// SAME computation V11_LANDING_GUARD uses (gateSpans). gateAt = [x0, x1] or
// [[x0, x1], ...]: a declared x extent, honoured by the rule only where a real
// ladder or flight head arrives inside it (and at most one deck slot + bar wider).
// ---------------------------------------------------------------------------

export function landing(o = {}) {
  const g = gateOf(o);
  const roles = rolesOf(g, "landing", o.roles);
  const zone = o.zone ?? g.table.zones.iron;
  const prefix = o.idPrefix ?? "landing";
  const span = finite(o.span, "landing span");
  const depth = finite(o.depth, "landing depth");
  const [cx, top] = vec(o.at, 2, "landing at");
  const wallZ = o.wall !== undefined ? wallPlanes(o.wall).front : finite(o.wallZ, "landing wallZ (or pass wall: parts)");
  const railH = o.railHeight === undefined ? mid(g.railingH) : finite(o.railHeight, "landing railHeight");
  const pitchWanted = o.balusterPitch ?? g.table.construction.balusterPitch;

  // Back edge seated into the wall: gap 0 <= landingGapMax (V11_LANDING_GAP).
  const hatches = o.hatches ?? [];
  const plate = o.plate === true;
  const G = buildGrate({ w: span, d: depth + g.seat, bar: o.bar, maxGap: o.maxGap, at: [cx, top, wallZ], hatches, plate },
    g, { deck: roles.deck, frame: roles.frame }, zone, prefix);
  const bar = G.bar;
  const seat = g.seat;
  const parts = [...G.parts];

  // Cantilever brackets under the bearers, wall to front edge (V5-7: `brackets: false` omits them — no rule reads
  // them; the bearers carry the deck).
  const nb = o.brackets === false ? 0 : Math.max(2, Math.ceil(span / g.bearingSpan - EPS) + 1);
  for (let i = 0; i < nb; i += 1) {
    const x = G.left + bar / 2 + (i * (span - bar)) / (nb - 1);
    const holes = hatches.filter((h) => overlap1(x - bar / 2, x + bar / 2, h.x0, h.x1) > 0).map((h) => [h.z0, h.z1]);
    subtract(G.zFront, G.zBack, holes, 2 * bar).forEach(([a, b], k) => parts.push(part(`${prefix}_bracket_${i}${k ? `_${k}` : ""}`,
      bx([x - bar / 2, G.bottom - bar, a], [x + bar / 2, G.bottom + seat, b], "landing bracket"),
      roles.bracket, zone)));
  }

  // Gate zones: nothing in the railing family within ladderHeadSlack of what arrives.
  let gates = o.gateAt ?? [];
  if (gates.length === 2 && typeof gates[0] === "number") gates = [gates];
  const declared = gates.map((pair, i) => {
    const [a, b] = vec(pair, 2, `landing gateAt[${i}]`);
    return [Math.min(a, b) - g.ladderHeadSlack, Math.max(a, b) + g.ladderHeadSlack];
  });
  // gateFor: the real heads, through the rule's own computation.
  const deckBox = { min: [G.left, top - bar, G.zFront], max: [G.right, top, G.zBack] };
  const headRoles = [g.table.roles.ladder?.stile ?? "ladder", g.table.roles.flight?.stringer ?? "stringer"];
  const heads = (o.gateFor ?? []).filter((p) => p && headRoles.includes(p.role) && K.isSolid(p.solid)).map((p) => p.solid);
  if (o.gateFor !== undefined && !Array.isArray(o.gateFor)) fail("landing gateFor must be the array of flight / ladder parts that arrive at this deck");
  // WF-R3 H4 — gateFor opens a gate only for an element that ARRIVES on this deck: a flight whose bottom or top tread
  // lies on it (deckOf), a ladder whose head is at its top and beside it in plan. Anything else is refused.
  {
    const elements = new Map();
    for (const p of o.gateFor ?? []) {
      if (!p || !K.isSolid(p.solid)) continue;
      const k = p.assembly?.id ?? p.role;
      if (!elements.has(k)) elements.set(k, []);
      elements.get(k).push(p);
    }
    const stepRole = g.table.roles.flight?.step ?? "step";
    const stileRole = g.table.roles.ladder?.stile ?? "ladder";
    for (const [k, members] of elements) {
      const treads = members.filter((p) => p.role === stepRole).map((p) => p.solid.aabb());
      if (treads.length > 0) {
        const a = flightArrivals(treads, [deckBox], g.stepRise[1]);
        if (a.bottomDeck !== 0 && a.topDeck !== 0) {
          fail(`landing gateFor: flight "${k}" does not arrive on this deck (treads z ${f3(a.bottom.min[2])}..${f3(a.bottom.max[2])} vs deck z ${f3(deckBox.min[2])}..${f3(deckBox.max[2])}, `
            + `deck top y ${f3(top)}) — a flight lands ON its decks; build the landings, flight and drop ladder with K.assemble.fireEscape`);
        }
        continue;
      }
      const stiles = members.filter((p) => p.role === stileRole).map((p) => p.solid.aabb());
      if (stiles.length === 0) continue;
      const head = Math.max(...stiles.map((b) => b.max[1]));
      const pad = g.landingGapMax + g.ladderHeadSlack;
      const beside = stiles.every((b) => overlap1(b.min[0], b.max[0], deckBox.min[0] - pad, deckBox.max[0] + pad) > 0
        && overlap1(b.min[2], b.max[2], deckBox.min[2] - pad, deckBox.max[2] + pad) > -EPS);
      if (!beside || Math.abs(head - top) > g.ladderLandingReach + EPS) {
        fail(`landing gateFor: ladder "${k}" does not arrive at this deck (head y ${f3(head)} vs deck top ${f3(top)}) — pass only the ladder that climbs onto it`);
      }
    }
  }
  const real = heads.length > 0
    ? gateSpans({ box: deckBox, heads, reach: g.landingGapMax, slack: g.ladderHeadSlack, headBand: g.ladderHeadBand }).spans
    : { front: [], "street-right end": [], "street-left end": [] };
  const blocked = [...declared, ...real.front];
  const free = (x0, x1) => blocked.every(([a, b]) => Math.min(x1, b) - Math.max(x0, a) <= 0);

  // Balusters stand on bars (a baluster in a slot would stand on nothing).
  const every = Math.max(1, Math.round(pitchWanted / G.pitch));
  const railY0 = top + railH - bar;
  const railY1 = top + railH;
  const zRail0 = G.zFront;
  const zRail1 = G.zFront + bar;
  // Free runs of consecutive bars.
  const runs = [];
  let run = [];
  G.barXs.forEach((x, i) => {
    if (free(x - bar / 2, x + bar / 2)) run.push(i);
    else if (run.length > 0) { runs.push(run); run = []; }
  });
  if (run.length > 0) runs.push(run);
  let railIndex = 0;
  let balusterIndex = 0;
  for (const members of runs) {
    const first = members[0];
    const last = members[members.length - 1];
    // WF-R3 H4 — a baluster stands on a bar that reaches the front edge (not on a bar a hatch cut short).
    // V5-7 — on a plate deck they stand at `balusterPitch` (the measured pitch), evenly over the free run, ends included.
    let xsAt;
    if (plate) {
      const a0 = G.barXs[first], a1 = G.barXs[last];
      const k = Math.max(1, Math.round((a1 - a0) / pitchWanted));
      xsAt = a1 - a0 < bar ? [a0] : Array.from({ length: k + 1 }, (_, j) => a0 + (j * (a1 - a0)) / k);
    } else {
      xsAt = members.filter((i) => (i === first || i === last || i % every === 0) && G.reachesFront[i]).map((i) => G.barXs[i]);
    }
    for (const x of xsAt) {
      parts.push(part(`${prefix}_baluster_${balusterIndex}`,
        bx([x - bar / 2, top - seat, zRail0], [x + bar / 2, railY0 + seat, zRail1], "landing baluster"),
        roles.baluster, zone));
      balusterIndex += 1;
    }
    const x0 = G.barXs[first] - bar / 2;
    const x1 = G.barXs[last] + bar / 2;
    parts.push(part(`${prefix}_rail_${railIndex}`, bx([x0, railY0, zRail0], [x1, railY1, zRail1], "landing rail"),
      roles.rail, zone));
    railIndex += 1;
  }
  // WF-BLIND-R2 C2 — a return back to the wall at BOTH ends, always (the rule guards every exposed end). When a
  // gate takes the corner bar, the return starts behind that gate: behind the real head's span on the end edge
  // (gateFor), or bar + ladderHeadSlack behind the front edge (a declared gateAt at the corner).
  const corner = (i) => declared.some(([a, b]) => Math.min(G.barXs[i] + bar / 2, b) - Math.max(G.barXs[i] - bar / 2, a) > 0);
  const holeMax = g.deckGapMaxGate + g.MIN_FEAT;
  const cornerGates = { l: null, r: null };
  for (const [side, i, name] of [["l", 0, "street-right end"], ["r", G.barXs.length - 1, "street-left end"]]) {
    const ends = [...real[name]];
    if (corner(i)) {
      cornerGates[side] = [G.zFront, G.zFront + bar + g.ladderHeadSlack];
      ends.push(cornerGates[side]);
    }
    // MVP-STUB: a head arriving mid-way along an end edge is not gated; only spans that open at the front count.
    const start = Math.max(zRail1 - seat, ...ends.filter(([p]) => p <= zRail1 + holeMax).map(([, q]) => q));
    if (G.zBack - start < g.MIN_FEAT - EPS) continue;
    const x0 = side === "l" ? G.left : G.right - bar;
    parts.push(part(`${prefix}_return_${side}`, bx([x0, railY0, start], [x0 + bar, railY1, G.zBack], "landing return"), roles.rail, zone));
    // V5-7 — a plate deck's returns carry balusters at the same pitch (the target draws them), strictly between the
    // front corner baluster and the wall
    if (plate) {
      const z0 = Math.max(start, zRail1), len = G.zBack - z0;
      const k = Math.max(0, Math.round(len / pitchWanted) - 1);
      for (let j = 1; j <= k; j += 1) {
        const z = z0 + (j * len) / (k + 1);
        parts.push(part(`${prefix}_baluster_${side}_${j - 1}`, bx([x0, top - seat, z - bar / 2], [x0 + bar, railY0 + seat, z + bar / 2], "landing baluster"),
          roles.baluster, zone));
      }
    }
  }
  const assembly = tag("landing", prefix, {
    gates: Object.freeze(declared.map(([a, b]) => Object.freeze({
      front: Object.freeze([a, b]),
      corner: corner(0) && a <= G.barXs[0] + bar / 2 ? "street-right end" : (corner(G.barXs.length - 1) && b >= G.barXs[G.barXs.length - 1] - bar / 2 ? "street-left end" : null),
      cornerSpan: Object.freeze([G.zFront, G.zFront + bar + g.ladderHeadSlack]),
    }))),
  });
  return parts.map((p) => ({ ...p, assembly }));
}

// ---------------------------------------------------------------------------
// flight — two stringers, equal treads, two handrails on posts.
// bottom/top = [x, deck TOP y, z of the landing front edge the flight hangs on].
// MVP-STUB: the flight runs along x only (bottom z must equal top z); its
// stringer ends run half a going past each arrival point to seat on the deck edge.
// ---------------------------------------------------------------------------

export function flight(o = {}) {
  const g = gateOf(o);
  const roles = rolesOf(g, "flight", o.roles);
  const zone = o.zone ?? g.table.zones.iron;
  const prefix = o.idPrefix ?? "flight";
  const [xb, yb, zb] = vec(o.bottom, 3, "flight bottom");
  const [xt, yt, zt] = vec(o.top, 3, "flight top");
  const width = finite(o.width, "flight width");
  const bar = o.bar === undefined ? g.MIN_FEAT : finite(o.bar, "flight bar");
  const [riseLo, riseHi] = g.stepRise;
  const maxRise = o.maxRise === undefined ? riseHi : finite(o.maxRise, "flight maxRise");
  const railH = o.railHeight === undefined ? mid(g.stairRailBand) : finite(o.railHeight, "flight railHeight");
  floorCheck(g, bar, "flight bar");
  floorCheck(g, width, "flight width");
  if (Math.abs(zb - zt) > EPS) fail(`flight bottom z ${f3(zb)} and top z ${f3(zt)} differ — a flight runs along x (MVP)`);
  const totalRise = yt - yb;
  const run = Math.abs(xt - xb);
  if (!(totalRise > 0)) fail(`flight top y ${f3(yt)} must be above bottom y ${f3(yb)}`);
  if (!(run > 0)) fail("flight top x equals bottom x — a flight needs a horizontal run");
  if (railH < g.stairRailBand[0] - EPS || railH > g.stairRailBand[1] + EPS) {
    fail(`flight railHeight ${f3(railH)} m is outside the stair-rail band ${g.stairRailBand[0]}..${g.stairRailBand[1]} m`);
  }
  if (!(maxRise > 0) || maxRise > riseHi + EPS) fail(`flight maxRise ${f3(maxRise)} m must be in (0, ${riseHi}] m (limits.v7.step_rise)`);
  const risers = Math.ceil(totalRise / maxRise - EPS);
  const rise = totalRise / risers;
  if (risers < 2 || rise < riseLo - EPS) {
    throw new KernelError(`BAD_ARG: impossible flight rise — a total rise of ${f3(totalRise)} m at maxRise ${f3(maxRise)} m gives `
      + `${risers} riser(s) of ${f3(rise)} m, and a flight needs >= 2 risers inside step_rise ${riseLo}..${riseHi} m. `
      + "Move the landings so the total rise is a multiple of a legal riser, or use a ladder.");
  }
  const going = run / risers;
  floorCheck(g, going, "flight going (run / risers)");

  const { seat } = g;
  const dir = Math.sign(xt - xb);
  const slope = rise / going;
  const hv = bar / 2 / Math.cos(Math.atan(slope));        // vertical half-thickness of a sloped bar
  const X = (s) => xb + dir * s;
  const nosing = (s) => yb + s * slope;                    // tread-top line
  const yc = (s) => nosing(s) - bar / 2;                   // stringer centreline
  const yr = (s) => nosing(s) + railH - hv;                // handrail centreline (top = nosing + railH)
  const delta = g.epsAbs / 2;                              // post-to-slope seat depth

  const zBack = zb + seat;
  const sides = [
    ["back", zBack - bar, zBack],
    ["front", zBack - 2 * bar - width, zBack - bar - width],
  ];
  const parts = [];
  for (const [side, z0, z1] of sides) {
    parts.push(part(`${prefix}_stringer_${side}`,
      sloped([X(-going / 2), yc(-going / 2)], [X(run + going / 2), yc(run + going / 2)], bar, z0, z1), roles.stringer, zone));
  }
  // Treads k = 1..risers-1; landings supply the first and last riser.
  for (let k = 1; k < risers; k += 1) {
    const xa = X((k - 0.5) * going);
    const xc = X((k + 0.5) * going);
    const y = yb + k * rise;
    parts.push(part(`${prefix}_step_${k - 1}`,
      bx([Math.min(xa, xc), y - bar, zBack - bar - width - seat], [Math.max(xa, xc), y, zBack - bar + seat], "flight tread"),
      roles.step, zone));
  }
  // Handrails + posts in each stringer's plane.
  const posts = Math.max(2, Math.ceil(run / (o.postPitch ?? g.table.construction.balusterPitch) - EPS) + 1);
  for (const [side, z0, z1] of sides) {
    parts.push(part(`${prefix}_rail_${side}`, sloped([X(0), yr(0)], [X(run), yr(run)], bar, z0, z1), roles.rail, zone));
    for (let i = 0; i < posts; i += 1) {
      const s = bar + (i * (run - 2 * bar)) / (posts - 1);
      const y0 = yc(s + bar / 2) + hv - delta;             // seated on the uphill edge of the stringer top
      const y1 = yr(s - bar / 2) - hv + delta;             // seated on the downhill edge of the rail underside
      if (!(y1 - y0 > 0)) fail(`flight post ${i} has no height — raise railHeight`);
      parts.push(part(`${prefix}_post_${side}_${i}`,
        bx([X(s) - bar / 2, y0, z0], [X(s) + bar / 2, y1, z1], "flight post"), roles.post, zone));
    }
  }
  // WF-R3 H4 — given the decks it joins (`decks`: the landing parts), a flight whose bottom or top tread is not ON a
  // deck is refused: a flight hung in front of its decks passed every row and read as railless landings.
  if (o.decks !== undefined) {
    if (!Array.isArray(o.decks)) fail("flight decks must be the landing parts the flight joins");
    const boxes = deckBoxes(o.decks, g.table.roles.landing?.deck ?? "landing");
    const treads = parts.filter((p) => p.role === roles.step).map((p) => p.solid.aabb());
    const a = treads.length ? flightArrivals(treads, boxes, maxRise) : null;
    if (!a || a.bottomDeck < 0 || a.topDeck < 0) {
      const bad = !a ? null : (a.bottomDeck < 0 ? a.bottom : a.top);
      fail("flight \"" + prefix + "\" " + (!a ? "has no tread" : (a.bottomDeck < 0 ? "bottom" : "top") + " tread (z " + f3(bad.min[2]) + ".." + f3(bad.max[2]) + ") is not on a deck")
        + " — a flight starts and ends ON its landings; build the escape with K.assemble.fireEscape");
    }
  }
  const assembly = tag("flight", prefix);
  return parts.map((p) => ({ ...p, assembly }));
}

// ---------------------------------------------------------------------------
// ladder — two stiles + rungs. base = [centre, bottom y, host plane]:
//   face "front": base = [x centre, y, z of the plane it hangs on], built toward -z
//   face "side":  base = [x of the side plane, y, z centre], built toward +x
// `dir` (+1/-1) flips the build direction off the host plane.
// width = stile centre spacing.
// ---------------------------------------------------------------------------

export function ladder(o = {}) {
  const g = gateOf(o);
  const roles = rolesOf(g, "ladder", o.roles);
  const zone = o.zone ?? g.table.zones.iron;
  const prefix = o.idPrefix ?? "ladder";
  const face = o.face ?? "front";
  if (face !== "front" && face !== "side") fail(`ladder face must be "front" or "side", got ${JSON.stringify(face)}`);
  const [bx0, by, bz] = vec(o.base, 3, "ladder base");
  const height = finite(o.height, "ladder height");
  const width = finite(o.width, "ladder width");
  const bar = o.bar === undefined ? g.MIN_FEAT : finite(o.bar, "ladder bar");
  const rungPitch = o.rungPitch === undefined ? g.table.construction.rungPitch : finite(o.rungPitch, "ladder rungPitch");
  const dir = o.dir ?? (face === "front" ? -1 : 1);
  floorCheck(g, bar, "ladder stile");
  floorCheck(g, width - bar, "ladder rung length");
  if (!(rungPitch > bar)) fail(`ladder rungPitch ${f3(rungPitch)} m must exceed the rung section ${f3(bar)} m`);
  const rungs = Math.floor((height - bar / 2) / rungPitch + EPS);
  if (rungs < 1) fail(`ladder height ${f3(height)} m holds no rung at pitch ${f3(rungPitch)} m`);

  const { seat } = g;
  // Across = the axis the stiles are spaced on; off = the axis away from the host plane.
  const host = face === "front" ? bz : bx0;
  const centre = face === "front" ? bx0 : bz;
  const off0 = dir < 0 ? host - bar : host - seat;
  const off1 = dir < 0 ? host + seat : host + bar;
  const box = (a0, a1, y0, y1, what) => (face === "front"
    ? bx([a0, y0, off0], [a1, y1, off1], what)
    : bx([off0, y0, a0], [off1, y1, a1], what));

  const parts = [];
  for (const [i, c] of [centre - width / 2, centre + width / 2].entries()) {
    parts.push(part(`${prefix}_stile_${i}`, box(c - bar / 2, c + bar / 2, by, by + height, "ladder stile"), roles.stile, zone));
  }
  for (let i = 1; i <= rungs; i += 1) {
    const y = by + i * rungPitch;
    parts.push(part(`${prefix}_rung_${i - 1}`,
      box(centre - width / 2 + bar / 2 - seat, centre + width / 2 - bar / 2 + seat, y - bar / 2, y + bar / 2, "ladder rung"),
      roles.rung, zone));
  }
  const assembly = tag("ladder", prefix);
  return parts.map((p) => ({ ...p, assembly }));
}

// ---------------------------------------------------------------------------
// frame — four members proud of the wall, glass pane behind their front face,
// optional sill on brackets. at = [opening centre x, glass bottom y, wall face z].
// ---------------------------------------------------------------------------

export function frame(o = {}) {
  const g = gateOf(o);
  const roles = rolesOf(g, "frame", o.roles);
  const zones = { ...g.table.zones.frame, ...(o.zones ?? {}) };
  const prefix = o.idPrefix ?? "frame";
  const w = finite(o.w, "frame w");
  const h = finite(o.h, "frame h");
  const [cx, by, faceZ] = vec(o.at, 3, "frame at");
  const fw = o.frameWidth === undefined ? g.MIN_FEAT : finite(o.frameWidth, "frame frameWidth");
  const proud = o.proud === undefined ? 2 * g.MIN_FEAT : finite(o.proud, "frame proud");
  const inset = o.glassInset === undefined ? g.MIN_FEAT / 2 : finite(o.glassInset, "frame glassInset");
  const { seat } = g;
  floorCheck(g, fw, "frame frameWidth");
  floorCheck(g, proud + seat, "frame depth (proud)");
  floorCheck(g, proud - inset + seat, "glass thickness (proud - glassInset)");
  if (!(inset >= 0)) fail(`frame glassInset must be >= 0, got ${inset}`);
  floorCheck(g, w, "frame w");
  floorCheck(g, h, "frame h");

  const z0 = faceZ - proud;
  const z1 = faceZ + seat;
  const l = cx - w / 2;
  const r = cx + w / 2;
  const parts = [
    part(`${prefix}_jamb_l`, bx([l - fw, by - fw, z0], [l, by + h + fw, z1], "frame jamb"), roles.frame, zones.frame),
    part(`${prefix}_jamb_r`, bx([r, by - fw, z0], [r + fw, by + h + fw, z1], "frame jamb"), roles.frame, zones.frame),
    part(`${prefix}_head`, bx([l - seat, by + h, z0], [r + seat, by + h + fw, z1], "frame head"), roles.frame, zones.frame),
    part(`${prefix}_bottom`, bx([l - seat, by - fw, z0], [r + seat, by, z1], "frame bottom"), roles.frame, zones.frame),
    part(`${prefix}_glass`, bx([l - seat, by - seat, z0 + inset], [r + seat, by + h + seat, z1], "glass"), roles.glass, zones.glass),
  ];

  if (o.sill) {
    const depth = finite(o.sill.depth, "frame sill.depth");
    const sh = finite(o.sill.height, "frame sill.height");
    floorCheck(g, depth + seat, "sill depth");
    floorCheck(g, sh, "sill height");
    const x0 = l - fw;
    const x1 = r + fw;
    const top = by - fw + seat;
    const bottom = by - fw - sh;
    parts.push(part(`${prefix}_sill`, bx([x0, bottom, faceZ - depth], [x1, top, z1], "sill"), roles.sill, zones.sill));
    // Brackets carry the sill (V11_BEARING): each a full bearing grid wide so it
    // covers a sample centre, spaced <= bearingSpan.
    const bw = Math.max(g.MIN_FEAT, g.bearingGrid);
    const sillW = x1 - x0;
    const count = sillW < 2 * bw ? 1 : Math.max(2, Math.ceil((sillW - bw) / g.bearingSpan - EPS) + 1);
    for (let i = 0; i < count; i += 1) {
      const c = count === 1 ? cx : x0 + bw / 2 + (i * (sillW - bw)) / (count - 1);
      const half = count === 1 ? sillW / 2 : bw / 2;
      parts.push(part(`${prefix}_bracket_${i}`,
        bx([c - half, bottom - g.MIN_FEAT, faceZ - depth], [c + half, bottom + seat, z1], "sill bracket"),
        roles.bracket, zones.bracket));
    }
  }
  const assembly = tag("frame", prefix);
  return parts.map((p) => ({ ...p, assembly }));
}

// ---------------------------------------------------------------------------
// V5-7 options (measured, so the escape matches a stylised target by construction): deck: "plate" (one solid plate
// per deck, no brackets, balusters on the front AND both returns), balusterPitch (m), dropLadder.rungPitch (m).
// WF-R3 H4 — fireEscape: the whole escape in ONE call, correct by construction. Landings at every level seated on the
// wall's front plane; one flight between each pair of levels whose treads start and end ON the decks (a foot plate on
// the lower deck, the stringer tops seated into the first whole bar past a hatch the upper deck opens over the flight);
// the gates come from the helper's own drop ladder (the flights arrive inside the decks and need none); the drop
// ladder hangs under the lowest deck's front edge down to dropLadder.bottom and is refused below a canopy it crosses.
// Flights alternate direction; flight i sits in strip A (behind the front bearer) when i is even, strip B behind it
// when odd. MVP-STUB: >2 levels need a deck deep enough for both strips.
// ---------------------------------------------------------------------------

function deckFlight(o, g, roles, zone, prefix) {
  const { xb, xt, yL, yU, z0, z1, bar, railH } = o;
  const { seat } = g;
  const [riseLo, riseHi] = g.stepRise;
  const totalRise = yU - yL;
  const run = Math.abs(xt - xb);
  // V5-8 R2: `risers` = a MEASURED tread count + 1 (subjects/<s>/subject.json ruleOverrides.flightTreads); the rise
  // must still sit in the (possibly subject-overridden) step_rise band.
  const risers = o.risers ?? Math.ceil(totalRise / riseHi - EPS);
  const rise = totalRise / risers;
  if (risers < 2 || rise < riseLo - EPS || rise > riseHi + EPS) {
    fail(`fireEscape: impossible flight rise — ${f3(totalRise)} m between levels gives ${risers} riser(s) of ${f3(rise)} m, outside step_rise ${riseLo}..${riseHi} m`);
  }
  const going = run / risers;
  floorCheck(g, going, `fireEscape flight ${prefix} going (run / risers)`);
  const dir = Math.sign(xt - xb);
  const slope = rise / going;
  const X = (s) => xb + dir * s;
  const nosing = (s) => yL + s * slope;
  const hv = bar / 2 / Math.cos(Math.atan(slope));
  const tv = 2 * hv;                                   // vertical thickness of a stringer of perpendicular section bar
  const yr = (s) => nosing(s) + railH - hv;
  const delta = g.epsAbs / 2;
  const parts = [];

  // Foot plate on the lower deck, at least one bar pitch + bar wide so it bears on a deck bar.
  const plateTop = yL + bar - seat;
  const yF = plateTop - seat;
  const sFt = (yF - yL) / slope;
  const sFb = (yF - yL + tv) / slope;
  const footX = X((sFt + sFb) / 2);
  const half = (o.pitch + bar) / 2 + seat;
  parts.push(part(`${prefix}_foot`, bx([footX - half, yL - seat, z0], [footX + half, plateTop, z1], "flight foot"), roles.foot, zone));

  // Stringers: vertical-section parallelograms cut level on the foot plate and ending a seat into the arrival bar.
  const sEnd = run + seat;
  const sides = [["back", z1 - bar, z1], ["front", z0, z0 + bar]];
  for (const [side, za, zc] of sides) {
    let pts = [[X(sFt), yF], [X(sFb), yF], [X(sEnd), nosing(sEnd) - tv], [X(sEnd), nosing(sEnd)]];
    if (dir < 0) pts = pts.reverse();
    parts.push(part(`${prefix}_stringer_${side}`, K.extrude(K.profile.poly(pts), zc - za).at([0, 0, za]), roles.stringer, zone));
  }
  for (let k = 1; k < risers; k += 1) {
    const xa = X((k - 0.5) * going);
    const xc = X((k + 0.5) * going);
    const y = yL + k * rise;
    parts.push(part(`${prefix}_step_${k - 1}`,
      bx([Math.min(xa, xc), y - bar, z0 + bar - seat], [Math.max(xa, xc), y, z1 - bar + seat], "flight tread"), roles.step, zone));
  }
  const posts = Math.max(2, Math.ceil(run / g.table.construction.balusterPitch - EPS) + 1);
  // V5-8 R2: rails === false (a subject whose target draws no stair handrails, ruleOverrides.stairRails false) builds
  // the flight as stringers + treads only; V7_STAIR_RAIL is waived for that subject alone (advisory row).
  for (const [side, za, zc] of o.rails === false ? [] : sides) {
    parts.push(part(`${prefix}_rail_${side}`, sloped([X(0), yr(0)], [X(run), yr(run)], bar, za, zc), roles.rail, zone));
    for (let i = 0; i < posts; i += 1) {
      const sp = bar + (i * (run - 2 * bar)) / (posts - 1);
      const y0 = nosing(sp + bar / 2) - delta;
      const y1 = yr(sp - bar / 2) - hv + delta;
      if (!(y1 - y0 > 0)) fail(`fireEscape flight post ${i} has no height — raise railHeight`);
      parts.push(part(`${prefix}_post_${side}_${i}`, bx([X(sp) - bar / 2, y0, za], [X(sp) + bar / 2, y1, zc], "flight post"), roles.post, zone));
    }
  }
  // Hatch in the upper deck over the stretch where the flight comes within head room of it.
  const sH = Math.max(0, (yU - g.table.construction.headroom - yL) / slope - going);
  const hatch = { x0: Math.min(X(sH), X(run)), x1: Math.max(X(sH), X(run)) };
  return { parts, hatch, going, risers };
}

export function fireEscape(o = {}) {
  const g = gateOf(o);
  const T = g.table;
  const C = T.construction;
  const prefix = o.idPrefix ?? "fe";
  if (!Array.isArray(o.wall)) fail("fireEscape wall must be the parts built so far (the massing the escape hangs off)");
  const wallZ = wallPlanes(o.wall).front;
  const cx = finite(o.centreX, "fireEscape centreX");
  const span = finite(o.span, "fireEscape span");
  const depth = finite(o.depth, "fireEscape depth");
  if (!Array.isArray(o.levels) || o.levels.length < 2) fail("fireEscape levels must list >= 2 deck-top y values, bottom first");
  const levels = o.levels.map((y, i) => finite(y, `fireEscape levels[${i}]`));
  for (let i = 1; i < levels.length; i += 1) if (!(levels[i] > levels[i - 1])) fail(`fireEscape levels must rise: levels[${i}] ${f3(levels[i])} <= ${f3(levels[i - 1])}`);
  const width = o.flightWidth === undefined ? C.flightWidth : finite(o.flightWidth, "fireEscape flightWidth");
  const bar = o.bar === undefined ? g.MIN_FEAT : finite(o.bar, "fireEscape bar");
  const railH = o.railHeight === undefined ? mid(g.railingH) : finite(o.railHeight, "fireEscape railHeight");
  floorCheck(g, bar, "fireEscape bar");
  floorCheck(g, width, "fireEscape flightWidth");
  const stairRailH = mid(g.stairRailBand);
  const zone = o.zone ?? T.zones.iron;
  const clr = g.MIN_FEAT;
  const zFront = wallZ - depth;
  const zBack = wallZ + g.seat;
  const edgeW = Math.max(bar, g.bearingGrid / 2);
  const stripA = { z0: zFront + edgeW + clr, z1: zFront + edgeW + clr + 2 * bar + width };
  const stripB = { z0: stripA.z1 + clr, z1: stripA.z1 + clr + 2 * bar + width };
  const flights = levels.length - 1;
  const lastStrip = flights > 1 ? stripB : stripA;
  if (lastStrip.z1 + clr + 2 * bar > zBack + EPS) {
    fail(`fireEscape depth ${f3(depth)} m cannot hold ${flights > 1 ? "two flight strips" : "the flight"} (${f3(lastStrip.z1 - zFront + clr + 2 * bar)} m needed with flightWidth ${f3(width)} m) — deepen the decks`);
  }
  const endClear = C.endClear;
  const runTarget = span - 2 * endClear;
  if (!(runTarget > 0)) fail(`fireEscape span ${f3(span)} m leaves no run after ${endClear} m of deck at each end`);
  const { pitch, xs: barXs } = barLayout(span, bar, g.deckGapMax, cx);
  const dir0 = o.direction === undefined ? -1 : Math.sign(finite(o.direction, "fireEscape direction")) || -1;
  const flightRoles = { ...T.roles.flight, foot: T.roles.landing.frame };
  // V5-8 R2 — measured per-subject overrides the template copies from subjects/<s>/subject.json ruleOverrides (the
  // gate chain applies the SAME overrides, so an author cannot relax a rule by passing these): stepRise [lo, hi] m,
  // flightTreads (treads per flight), flightRails false (no handrails / posts).
  const gFlight = o.stepRise === undefined ? g : { ...g, stepRise: vec(o.stepRise, 2, "fireEscape stepRise") };
  const treads = o.flightTreads === undefined ? undefined : finite(o.flightTreads, "fireEscape flightTreads");
  if (treads !== undefined && !(Number.isInteger(treads) && treads >= 1)) fail(`fireEscape flightTreads must be an integer >= 1, got ${treads}`);

  const hatchesAt = levels.map(() => []);
  const parts = [];
  let firstRun = null;
  for (let i = 0; i < flights; i += 1) {
    const dir = i % 2 === 0 ? dir0 : -dir0;
    const strip = i % 2 === 0 ? stripA : stripB;
    const want = cx + dir * runTarget / 2;
    // The top arrives on the near face of a whole deck bar (the stringers seat into it).
    const faces = barXs.map((x) => x - dir * bar / 2);
    const xt = faces.reduce((a, b) => (Math.abs(b - want) < Math.abs(a - want) ? b : a));
    const xb = cx - dir * runTarget / 2;
    const fl = deckFlight({ xb, xt, yL: levels[i], yU: levels[i + 1], z0: strip.z0, z1: strip.z1, bar, railH: o.stairRailHeight ?? stairRailH, pitch,
      ...(treads !== undefined ? { risers: treads + 1 } : {}), ...(o.flightRails === false ? { rails: false } : {}) },
    gFlight, flightRoles, zone, `${prefix}_flight${i}`);
    firstRun ??= { xb, xt };
    hatchesAt[i + 1].push({ ...fl.hatch, z0: strip.z0 - clr, z1: strip.z1 + clr });
    const assembly = tag("flight", `${prefix}_flight${i}`);
    parts.push(...fl.parts.map((p) => ({ ...p, assembly })));
  }

  let drop = [];
  if (o.dropLadder) {
    const d = o.dropLadder;
    const bottom = finite(d.bottom, "fireEscape dropLadder.bottom");
    const w = d.width === undefined ? C.dropWidth : finite(d.width, "fireEscape dropLadder.width");
    const x = d.x === undefined ? (firstRun.xb + 3 * firstRun.xt) / 4 : finite(d.x, "fireEscape dropLadder.x");
    if (!(bottom < levels[0])) fail(`fireEscape dropLadder.bottom ${f3(bottom)} must be below the lowest deck top ${f3(levels[0])}`);
    const x0 = x - w / 2 - bar / 2;
    const x1 = x + w / 2 + bar / 2;
    const clash = o.wall.filter((p) => p && (T.dropClearRoles ?? []).includes(p.role) && K.isSolid(p.solid))
      .map((p) => ({ p, b: p.solid.aabb() }))
      .find(({ b }) => overlap1(b.min[0], b.max[0], x0, x1) > 0 && b.max[1] > bottom + EPS && b.min[1] < levels[0]);
    if (clash) {
      fail(`fireEscape dropLadder.bottom y ${f3(bottom)} hangs past "${clash.p.id}" (role ${clash.p.role}, top y ${f3(clash.b.max[1])}) — a drop ladder ends above the canopy it crosses: bottom >= ${f3(clash.b.max[1])}`);
    }
    drop = ladder({ table: o.table, limits: o.limits, zone, base: [x, bottom, zFront], height: levels[0] - bottom, width: w, bar, idPrefix: `${prefix}_drop`,
      ...(d.rungPitch !== undefined ? { rungPitch: finite(d.rungPitch, "fireEscape dropLadder.rungPitch") } : {}) });
  }

  const decks = [];
  levels.forEach((y, i) => {
    decks.push(...landing({ table: o.table, limits: o.limits, zone, span, depth, at: [cx, y], wallZ, bar, railHeight: railH,
      hatches: hatchesAt[i], gateFor: i === 0 ? drop : [], idPrefix: `${prefix}_deck${i}`,
      ...(o.deck === "plate" ? { plate: true, brackets: false } : {}), ...(o.balusterPitch !== undefined ? { balusterPitch: finite(o.balusterPitch, "fireEscape balusterPitch") } : {}) }));
  });
  return [...decks, ...parts, ...drop];
}

// ---------------------------------------------------------------------------
// WF-R3 R3-B item 2 — VEHICLE detail helpers, correct by construction. The blind P1 runs lost their details to
// hand-converted metres: panes stood as slabs above the roof / out of the flank (anchor error), mirror heads floated
// 0.5 mm off their arms (V3), headlights and glass hid inside the body. Each helper takes the metres the harness
// prints (MEASURED NUMBERS, ready arguments) and seats its parts on the host FACE it finds itself:
//   - pane: a glass layer that FOLLOWS the host face (a raked windshield included), sunk in a recess it cuts;
//   - lamp / grille: on the nose (or tail) plane of the body, never prouder than the bumper (the far wheel shows);
//   - mirror: the pair, head seated on its arm, arm seated in the flank.
// Every part carries `assembly: { helper, id }` so VEH_HANDBUILT can tell helper-built details from hand-placed ones.
// ---------------------------------------------------------------------------

export const VEHICLE_TABLE = Object.freeze({
  ...DEFAULT_TABLE,
  styleFloorKey: "vehicle",
  vehicle: Object.freeze({
    roles: Object.freeze({ pane: "window", lamp: "headlight", mirror: "mirror", grille: "grille", archLiner: "body" }),
    // WF-R5 R5-A — inlay tones (scripts/measure-profile.mjs samples them off the target; these are the pickup's):
    // seam / handle = the body family's darker tone, arch liner = the wheel-well tone, grille bars = the body.
    zones: Object.freeze({ pane: "glass", lamp: "lamp", mirror: "mirror", grille: "grille", grilleBar: "body", seam: "bed", handle: "bed", archLiner: "grille" }),
    bodyRoles: Object.freeze(["chassis", "body", "cab", "hood", "bed", "bed_wall", "tailgate"]),
    bumperRole: "bumper",
    // Construction numbers no gate reads: pane recess and grille slot depth (both capped by GROOVE_DEPTH_MAX), lamp facets.
    // WF-R5 R5-A: seam line width (the inlay's AABB carries the V5 floor, not its width), wheel-well clearance
    // inboard of the tyre, tyre clearance inside an arch liner, wheel facets (near / far pair: the far pair is
    // hidden at the solved camera; both divisible by 4 so the AABBs mirror exactly).
    construction: Object.freeze({ recess: 0.015, slotDepth: 0.015, lampSegs: 16, seamWidth: 0.02, archClear: 0.09, tyreClear: 0.02, wheelSegs: Object.freeze([20, 12]),
      // V4-5A: hub ring + cap facets (near / far pair, divisible by 4), mirror-head corner facets
      hubSegs: Object.freeze([12, 4]), cornerSegs: 2,
      // V4-5A: a flank (±x) inlay layer keeps only the skin within flankDepth of the host's outer face — never the
      // +x-facing wall of an arch well or a recess deep inside the body
      flankDepth: 0.2 }),
  }),
});

/** `K.span({ x: [lo, hi], y: [lo, hi], z: [lo, hi] })` — metre bounds (any subset of axes), sorted and checked. */
export function span(o = {}) {
  if (!o || typeof o !== "object") fail("span takes { x: [lo, hi], y: [lo, hi], z: [lo, hi] } in metres");
  const out = {};
  for (const a of ["x", "y", "z"]) {
    if (o[a] === undefined) continue;
    if (!Array.isArray(o[a]) || o[a].length !== 2) fail(`span ${a} must be [lo, hi] in metres, got ${JSON.stringify(o[a])}`);
    const [p, q] = o[a].map((v, i) => finite(v, `span ${a}[${i}]`));
    if (!(Math.abs(q - p) > EPS)) fail(`span ${a} [${f3(p)}, ${f3(q)}] has no extent`);
    out[a] = Object.freeze([Math.min(p, q), Math.max(p, q)]);
  }
  if (Object.keys(out).length === 0) fail("span needs at least one of x, y, z");
  return Object.freeze(out);
}

/** host part -> its solid before the first pane recess (pane layers follow the ORIGINAL face). */
const PANE_BASE = new WeakMap();
const vgate = (o) => gateOf({ ...o, table: o.table ?? VEHICLE_TABLE });
const vt = (g) => g.table.vehicle ?? VEHICLE_TABLE.vehicle;
const FACES = Object.freeze({ "+x": [0, 1], "-x": [0, -1], "+y": [1, 1], "-y": [1, -1], "+z": [2, 1], "-z": [2, -1] });
const AX = "xyz";

function faceOf(face, what) {
  const f = FACES[face];
  if (!f) fail(`${what} face must be one of ${Object.keys(FACES).join(", ")} (the outward direction of the host face), got ${JSON.stringify(face)}`);
  return { axis: f[0], sign: f[1] };
}

/** Helpers whose parts carry a body role but are not the body (V4-5A: the raised hood panel). */
const INLAYS = Object.freeze(["seam", "handle", "hoodPanel", "band"]);

/** The body's planes: nose (max z), tail, flanks, centre plane, top, L/W/H, and how far the bumpers stand proud. */
export function bodyPlanes(parts, { table = VEHICLE_TABLE } = {}) {
  if (!Array.isArray(parts)) fail("bodyPlanes takes the parts built so far");
  const T = table.vehicle ?? VEHICLE_TABLE.vehicle;
  // WF-R5 R5-A: seam / handle inlays (proud details in a body role) are not the body
  const boxes = parts.filter((p) => p && T.bodyRoles.includes(p.role) && K.isSolid(p.solid) && !INLAYS.includes(p.assembly?.helper)).map((p) => p.solid.aabb());
  if (boxes.length === 0) fail(`found no ${T.bodyRoles.join("/")} part — build the body first`);
  const min = [0, 1, 2].map((a) => Math.min(...boxes.map((b) => b.min[a])));
  const max = [0, 1, 2].map((a) => Math.max(...boxes.map((b) => b.max[a])));
  const bumpers = parts.filter((p) => p && p.role === T.bumperRole && K.isSolid(p.solid)).map((p) => p.solid.aabb());
  return {
    nose: max[2], tail: min[2], left: max[0], right: min[0], centreX: (min[0] + max[0]) / 2, ground: 0, top: max[1],
    L: max[2] - min[2], W: max[0] - min[0], H: max[1],
    noseProud: bumpers.length ? Math.max(...bumpers.map((b) => b.max[2])) - max[2] : Infinity,
    tailProud: bumpers.length ? min[2] - Math.min(...bumpers.map((b) => b.min[2])) : Infinity,
  };
}

/** WF-R5 R5-A — a face's own 2D frame: [z, y] on ±x (side elevation), [x, z] on ±y (plan), [x, y] on ±z (section). */
const FACE_2D = Object.freeze({ 0: [2, 1], 1: [0, 2], 2: [0, 1] });
/** extrude a side elevation [[z, y], ...] across x0..x1 */
export const sideSolid = (pts, x0, x1) => K.extrude(pts.map(([z, y]) => [-z, y]), x1 - x0).rotY(90).at([x0, 0, 0]);
/** extrude a section [[x, y], ...] along z0..z1 */
export const frontSolid = (pts, z0, z1) => K.extrude(pts, z1 - z0).at([0, 0, z0]);
/** extrude a plan [[x, z], ...] over y0..y1 */
export const planSolid = (pts, y0, y1) => K.extrude(pts, y1 - y0).rotX(90).at([0, y1, 0]);
const prismOf = (pts, axis, lo, hi) => (axis === 0 ? sideSolid(pts, lo, hi) : axis === 2 ? frontSolid(pts, lo, hi) : planSolid(pts, lo, hi));
/** A recess tool starts this far OUTSIDE its face: a tool flush with the face leaves a zero-thickness skin. */
export const RECESS_OUTSIDE = 0.01;

/**
 * The footprint of an inlay on a face: `bounds` (K.span of the two axes across the face) or `poly` (a simple polygon in
 * the face's 2D frame, FACE_2D — an angled or tapered pane). Checked inside the host's extent and >= MIN_FEAT across.
 */
function footprint(o, g, axis, hb, what) {
  const [a0, a1] = FACE_2D[axis];
  let pts;
  if (o.poly !== undefined) {
    if (!Array.isArray(o.poly) || o.poly.length < 3) fail(`${what} poly must be >= 3 points [${AX[a0]}, ${AX[a1]}] (face ${o.face})`);
    pts = o.poly.map((p, i) => vec(p, 2, `${what} poly[${i}]`));
  } else {
    const b = o.bounds;
    if (!b || typeof b !== "object") fail(`${what} needs bounds: K.span({ ${AX[a0]}, ${AX[a1]} }) or poly: [[${AX[a0]}, ${AX[a1]}], ...] across the face`);
    for (const a of [a0, a1]) if (!Array.isArray(b[AX[a]])) fail(`${what} bounds needs ${AX[a]} for face ${o.face} (K.span({ ${AX[a0]}, ${AX[a1]} }))`);
    const [p, q] = b[AX[a0]];
    const [r, t] = b[AX[a1]];
    pts = [[p, r], [q, r], [q, t], [p, t]];
  }
  [a0, a1].forEach((a, k) => {
    const lo = Math.min(...pts.map((p) => p[k]));
    const hi = Math.max(...pts.map((p) => p[k]));
    floorCheck(g, hi - lo, `${what} ${AX[a]} extent`);
    if (lo < hb.min[a] - EPS || hi > hb.max[a] + EPS) {
      fail(`${what} ${AX[a]} ${f3(lo)}..${f3(hi)} leave host "${o.host.id}" (${f3(hb.min[a])}..${f3(hb.max[a])}) — a pane lies inside its host's face`);
    }
  });
  return pts;
}

/**
 * The shared inlay construction (pane, seam, handle): a layer `t` thick laid on the host's face AS BUILT (before any
 * inlay recess, so later layers follow the original face), clipped to `prism`, its back `recess + seat` under the face;
 * the recess this call CUTS INTO host.solid starts RECESS_OUTSIDE beyond the face (no zero-thickness skin).
 */
function layer(o, g, host, axis, sign, prism, t, recess, what) {
  if (!PANE_BASE.has(host)) PANE_BASE.set(host, host.solid);
  const base = PANE_BASE.get(host);
  const shift = (d) => { const v = [0, 0, 0]; v[axis] = sign * d; return base.at(v); };
  const { seat } = g;
  // The layer and the recess tool are differences of two copies of the host; the kernel's box-based thin-cut
  // record on those copies (the layer IS thin) is an artefact of the construction, so it is not inherited.
  const clean = (x) => new K.Solid(x._m, [], []);
  // Faces parallel to the shift stay coplanar in the two copies; the boolean can leave a zero-volume sheet joined to the
  // layer across the host. The layer lives on the face's half of the host, so it is clipped to that half.
  const hb0 = base.aabb();
  const mid = (hb0.min[axis] + hb0.max[axis]) / 2;
  const lo = [-1e3, -1e3, -1e3];
  const hi = [1e3, 1e3, 1e3];
  if (sign > 0) lo[axis] = mid; else hi[axis] = mid;
  const fd = axis === 0 ? (g.table.vehicle ?? VEHICLE_TABLE.vehicle).construction?.flankDepth : undefined;
  if (Number.isFinite(fd)) { if (sign > 0) lo[axis] = Math.max(mid, hb0.max[axis] - fd); else hi[axis] = Math.min(mid, hb0.min[axis] + fd); }
  let solid = clean(K.intersect(K.cut(shift(t - recess - seat), shift(-recess - seat)), prism, bx(lo, hi, `${what} half`)));
  // V4-5A: `body: parts` — the layer never enters another part (the hood under a windshield's lower edge, a handle a
  // door seam crosses): every other part whose box meets the layer's is cut out of it
  if (Array.isArray(o.body) && solid.volume() > 0) {
    const sb = solid.aabb();
    const hit = (b) => [0, 1, 2].every((a) => b.min[a] < sb.max[a] - EPS && b.max[a] > sb.min[a] + EPS);
    const others = o.body.filter((p) => p && p !== host && K.isSolid(p.solid) && hit(p.solid.aabb())).map((p) => p.solid);
    if (others.length) solid = clean(K.cut(solid, others.length === 1 ? others[0] : K.union(others)));
  }
  if (!(solid.volume() > 0)) fail(`${what} do not meet host "${host.id}"'s ${o.face} face`);
  // V5-3: `cut: false` — the recess was already cut by a groove() over a larger footprint (a framed pane group: ONE
  // groove for the frame and every pane, not one per pane: the host keeps a fraction of the triangles)
  if (recess > 0 && o.cut !== false) groove(g, host, axis, sign, prism, recess, what);
  return solid;
}

/**
 * Cut a recess `depth` deep into host's face (axis, sign) over `prism`, starting RECESS_OUTSIDE beyond the face as
 * built (PANE_BASE). The recess keeps >= MIN_FEAT of host behind it (checked on the host's extent inside the
 * footprint), so the kernel's box-based thin-cut record — which fires on the sub-mm sliver where a raked face meets the
 * bounds — is not kept. MVP-STUB: an extent check, not a wall-thickness map; a hollow host thinner than
 * recess + MIN_FEAT behind the face would pass it.
 */
function groove(g, host, axis, sign, prism, depth, what) {
  if (!PANE_BASE.has(host)) PANE_BASE.set(host, host.solid);
  const base = PANE_BASE.get(host);
  const shift = (d) => { const v = [0, 0, 0]; v[axis] = sign * d; return base.at(v); };
  const clean = (x) => new K.Solid(x._m, [], []);
  const inside = K.intersect(base, prism).aabb();
  const deep = inside.max[axis] - inside.min[axis];
  if (deep < depth + g.MIN_FEAT - EPS) fail(`${what}: host "${host.id}" is ${f3(deep)} m deep there — a ${f3(depth)} m recess needs ${f3(depth + g.MIN_FEAT)} m`);
  const cutHost = K.cut(host.solid, clean(K.intersect(K.cut(shift(RECESS_OUTSIDE), shift(-depth)), prism)));
  host.solid = new K.Solid(cutHost._m, host.solid._thin, cutHost._cuts);
}

/**
 * pane({ host, face, bounds | poly, recess? }) — ONE glass pane on `host`'s `face` ("+x" flank, "-x", "+z" nose-facing ...).
 * `bounds` = K.span of the two axes across the face, or `poly` = a polygon in the face's 2D frame ([z, y] on a flank,
 * [x, y] on ±z) for an angled / tapered pane. The pane is the host's own face moved out by the pane thickness and
 * clipped to the footprint and to the host's outline, so it follows a raked face; it sits in a `recess`
 * (<= GROOVE_DEPTH_MAX) this call CUTS INTO host.solid, its back overlapping the recess floor by a seat.
 */
export function pane(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("pane host must be the PART the pane sits in (e.g. the cab part, with .solid)");
  const { axis, sign } = faceOf(o.face, "pane");
  const recess = o.recess === undefined ? Math.min(T.construction.recess, g.grooveDepthMax) : finite(o.recess, "pane recess");
  if (!(recess >= 0) || recess > g.grooveDepthMax + EPS) fail(`pane recess ${f3(recess)} m must be 0..${g.grooveDepthMax} m (GROOVE_DEPTH_MAX)`);
  const t = o.thickness === undefined ? g.MIN_FEAT : finite(o.thickness, "pane thickness");
  floorCheck(g, t, "pane thickness");
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const pts = footprint(o, g, axis, hb, "pane bounds");
  const prefix = o.idPrefix ?? `pane_${o.face.replace("+", "p").replace("-", "n")}`;
  // V5-3 `frame: { w, zone? }` — a frame ring w wide round the pane (the pane outline grown by w, minus the pane), an
  // inlay in the frame tone sunk GROOVE_DEPTH_MAX into the host (the pickup windshield's dark surround)
  const out = [];
  if (o.frame !== undefined) {
    const fw = finite(o.frame?.w, "pane frame.w");
    if (!(fw > 0)) fail("pane frame.w must be > 0");
    const inner = K.profile.poly(pts);
    const outer = K.profile.offset(inner, fw);
    const [a0, a1] = FACE_2D[axis];
    for (const [k, a] of [[0, a0], [1, a1]]) {
      if (Math.min(...outer.map((p) => p[k])) < hb.min[a] - EPS || Math.max(...outer.map((p) => p[k])) > hb.max[a] + EPS) fail(`pane frame ${f3(fw)} m leaves host "${host.id}" on ${AX[a]} — narrow it`);
    }
    const ring = K.cut(prismOf(outer, axis, hb.min[axis] - 1, hb.max[axis] + 1), prismOf(inner, axis, hb.min[axis] - 2, hb.max[axis] + 2));
    const fs = layer({ face: o.face, body: o.body }, g, host, axis, sign, ring, g.MIN_FEAT, g.grooveDepthMax, "pane frame");
    out.push(part(`${prefix}_frame`, fs, host.role, o.frame.zone ?? T.zones.seam, tag("band", `${prefix}_frame`)));
  }
  const solid = layer(o, g, host, axis, sign, prismOf(pts, axis, hb.min[axis] - 1, hb.max[axis] + 1), t, recess, "pane bounds");
  return [part(prefix, solid, o.role ?? T.roles.pane, o.zone ?? T.zones.pane, tag("pane", prefix)), ...out];
}

/**
 * V5-3 — paneFrame({ host, face, bounds: K.span (the GLASS FIELD: every pane + the posts between), panes?, post?,
 * frame: w | { top, bottom, side }, body?, zone?, idPrefix? }) — a framed pane group (the bus windshield: a black
 * frame round two panes and a centre mullion). The frame is ONE inlay (the field grown by the frame widths, minus the
 * pane openings) in `zone` (default "black"); `panes` (default 1) equal panes split by `post` (m) sit in the openings.
 * ONE groove (GROOVE_DEPTH_MAX) under the whole frame carries the frame and the panes, each sunk to it. The frame is
 * clamped inside the host face; ids `<prefix>_frame` and, for 2 panes, `<prefix>_r` / `<prefix>_l` (-x / +x side).
 */
export function paneFrame(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("paneFrame host must be the PART the panes sit in (the cab part)");
  const { axis, sign } = faceOf(o.face ?? "+z", "paneFrame");
  const [a0, a1] = FACE_2D[axis];
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const b = o.bounds;
  if (!b || !Array.isArray(b[AX[a0]]) || !Array.isArray(b[AX[a1]])) fail(`paneFrame bounds must be K.span({ ${AX[a0]}, ${AX[a1]} }) — the glass field`);
  const n = o.panes ?? 1;
  if (!Number.isInteger(n) || n < 1) fail(`paneFrame panes must be an integer >= 1, got ${JSON.stringify(n)}`);
  const m = g.MIN_FEAT;
  const fr = typeof o.frame === "number" ? { top: o.frame, bottom: o.frame, side: o.frame } : (o.frame ?? {});
  const [top, bottom, side] = ["top", "bottom", "side"].map((k) => Math.max(0, finite(fr[k] ?? 0, `paneFrame frame.${k}`)));
  const post = n > 1 ? Math.max(m, finite(o.post ?? m, "paneFrame post")) : 0;
  const edge = g.seat;
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const [u0, u1] = b[AX[a0]];
  const [v0, v1] = b[AX[a1]];
  const U0 = clamp(u0 - side, hb.min[a0] + edge, u0 - m / 2);
  const U1 = clamp(u1 + side, u1 + m / 2, hb.max[a0] - edge);
  const V0 = clamp(v0 - bottom, hb.min[a1] + edge, v0 - m / 2);
  const V1 = clamp(v1 + top, v1 + m / 2, hb.max[a1] - edge);
  const w = (u1 - u0 - (n - 1) * post) / n;
  if (w < m - EPS) fail(`paneFrame field ${f3(u1 - u0)} m cannot hold ${n} pane(s) of MIN_FEAT with ${f3(post)} m posts`);
  const lo = hb.min[axis] - 1;
  const hi = hb.max[axis] + 1;
  const rect = (p, q, r, s) => [[p, r], [q, r], [q, s], [p, s]];
  const openings = Array.from({ length: n }, (_, i) => [u0 + i * (w + post), u0 + i * (w + post) + w]);
  const outer = prismOf(rect(U0, U1, V0, V1), axis, lo, hi);
  groove(g, host, axis, sign, outer, g.grooveDepthMax, "paneFrame");
  const holes = openings.map(([p, q]) => prismOf(rect(p, q, v0, v1), axis, lo - 1, hi + 1));
  const strip = K.cut(outer, holes.length === 1 ? holes[0] : K.union(holes));
  const prefix = o.idPrefix ?? "windshield";
  const fs = layer({ face: o.face ?? "+z", body: o.body, cut: false }, g, host, axis, sign, strip, m, g.grooveDepthMax, "paneFrame frame");
  const out = [part(`${prefix}_frame`, fs, o.role ?? host.role, o.zone ?? "black", tag("band", `${prefix}_frame`))];
  const ids = n === 2 ? [`${prefix}_r`, `${prefix}_l`] : n === 1 ? [prefix] : openings.map((_, i) => `${prefix}_${i}`);
  openings.forEach(([p, q], i) => out.push(...pane({ table: o.table, host, face: o.face ?? "+z", bounds: span({ [AX[a0]]: [p, q], [AX[a1]]: [v0, v1] }),
    recess: g.grooveDepthMax, cut: false, role: o.paneRole, zone: o.paneZone, idPrefix: ids[i] })));
  return out;
}

/**
 * V5-3 — busDoor({ host, face?, z: [rear, front], y: [bottom, top], pane: { z, y }, body?, zone?, idPrefix? }) — the bus
 * ENTRANCE DOOR on a flank (default "+x", the near side): a door leaf inlay in `zone` (default "black") over z x y with
 * a glass pane (role prop: the census counts the windshield + row panes only) in its opening; ONE groove under the
 * leaf carries both. Every value is clamped inside the host flank (FIT may move them freely).
 */
export function busDoor(o = {}) {
  const g = vgate(o);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("busDoor host must be the body PART (the cab part of a bus)");
  const { axis, sign } = faceOf(o.face ?? "+x", "busDoor");
  if (axis !== 0) fail('busDoor face is a flank ("+x" / "-x")');
  const m = g.MIN_FEAT;
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const edge = g.seat;
  const [zr, zf] = vec(o.z, 2, "busDoor z").sort((a, b) => a - b);
  const [yb, yt] = vec(o.y, 2, "busDoor y").sort((a, b) => a - b);
  const Z0 = clamp(zr, hb.min[2] + edge, hb.max[2] - edge - 3 * m);
  const Z1 = clamp(zf, Z0 + 3 * m, hb.max[2] - edge);
  const Y0 = clamp(yb, hb.min[1] + edge, hb.max[1] - edge - 3 * m);
  const Y1 = clamp(yt, Y0 + 3 * m, hb.max[1] - edge);
  const [pz0, pz1] = vec(o.pane?.z, 2, "busDoor pane.z").sort((a, b) => a - b);
  const [py0, py1] = vec(o.pane?.y, 2, "busDoor pane.y").sort((a, b) => a - b);
  const Pz0 = clamp(pz0, Z0 + m, Z1 - 2 * m);
  const Pz1 = clamp(pz1, Pz0 + m, Z1 - m);
  const Py0 = clamp(py0, Y0 + m, Y1 - 2 * m);
  const Py1 = clamp(py1, Py0 + m, Y1 - m);
  const lo = hb.min[0] - 1;
  const hi = hb.max[0] + 1;
  const outer = sideSolid([[Z0, Y0], [Z1, Y0], [Z1, Y1], [Z0, Y1]], lo, hi);
  groove(g, host, axis, sign, outer, g.grooveDepthMax, "busDoor");
  const strip = K.cut(outer, sideSolid([[Pz0, Py0], [Pz1, Py0], [Pz1, Py1], [Pz0, Py1]], lo - 1, hi + 1));
  const prefix = o.idPrefix ?? "door";
  const leaf = layer({ face: o.face ?? "+x", body: o.body, cut: false }, g, host, axis, sign, strip, m, g.grooveDepthMax, "busDoor leaf");
  return [
    part(`${prefix}_leaf`, leaf, o.role ?? host.role, o.zone ?? "black", tag("band", `${prefix}_leaf`)),
    ...pane({ table: o.table, host, face: o.face ?? "+x", bounds: span({ z: [Pz0, Pz1], y: [Py0, Py1] }), recess: g.grooveDepthMax, cut: false, role: "prop", idPrefix: `${prefix}_pane` }),
  ];
}

/**
 * seam({ host, face, path, closed?, width? }) — WF-R5 R5-A: a door / hood seam as an INLAY LINE: the polyline `path`
 * (the face's 2D frame, metres) thickened to `width` (default construction.seamWidth), a MIN_FEAT layer in the seam
 * tone sunk GROOVE_DEPTH_MAX into a groove it cuts in the host. A flat unlit capture hides a bare groove; the inlay's
 * tone (sampled off the target, scripts/measure-profile.mjs inlays.seam) makes the line read.
 */
export function seam(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("seam host must be the PART the seam is cut in (e.g. the cab part)");
  const { axis, sign } = faceOf(o.face, "seam");
  const [a0, a1] = FACE_2D[axis];
  const w = o.width === undefined ? T.construction.seamWidth : finite(o.width, "seam width");
  if (!(w > 0)) fail("seam width must be > 0");
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const door = o.door !== undefined ? doorPath(o.door, hb, axis, w, g) : null;
  if (!door && (!Array.isArray(o.path) || o.path.length < 2)) fail(`seam path must be >= 2 points [${AX[a0]}, ${AX[a1]}] (face ${o.face}), or door: { front, rear, bottom, knee, top, rake }`);
  const path = door ?? o.path.map((p, i) => vec(p, 2, `seam path[${i}]`));
  const closed = door ? true : o.closed === true;
  for (const [i, p] of path.entries()) {
    [a0, a1].forEach((a, k) => {
      if (p[k] < hb.min[a] - EPS || p[k] > hb.max[a] + EPS) fail(`seam path[${i}] ${AX[a]} ${f3(p[k])} leaves host "${host.id}" (${f3(hb.min[a])}..${f3(hb.max[a])})`);
    });
  }
  const lo = hb.min[axis] - 1;
  const hi = hb.max[axis] + 1;
  let prism;
  if (closed) {
    prism = K.cut(prismOf(K.profile.offset(path, w / 2), axis, lo, hi), prismOf(K.profile.offset(path, -w / 2), axis, lo, hi));
  } else {
    const quads = [];
    for (let i = 0; i + 1 < path.length; i += 1) {
      const [p, q] = [path[i], path[i + 1]];
      const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
      if (!(len > EPS)) fail(`seam path[${i}] and [${i + 1}] coincide`);
      const e = [(q[0] - p[0]) / len * w / 2, (q[1] - p[1]) / len * w / 2];
      const nrm = [-e[1], e[0]];
      quads.push(prismOf([[p[0] - e[0] + nrm[0], p[1] - e[1] + nrm[1]], [q[0] + e[0] + nrm[0], q[1] + e[1] + nrm[1]],
        [q[0] + e[0] - nrm[0], q[1] + e[1] - nrm[1]], [p[0] - e[0] - nrm[0], p[1] - e[1] - nrm[1]]], axis, lo, hi));
    }
    prism = quads.length === 1 ? quads[0] : K.union(quads);
  }
  const pb = prism.aabb();
  for (const a of [a0, a1]) floorCheck(g, Math.min(pb.max[a], hb.max[a]) - Math.max(pb.min[a], hb.min[a]), `seam ${AX[a]} extent`);
  const solid = layer(o, g, host, axis, sign, prism, g.MIN_FEAT, g.grooveDepthMax, "seam path");
  const prefix = o.idPrefix ?? `seam_${o.face.replace("+", "p").replace("-", "n")}`;
  return [part(prefix, solid, o.role ?? host.role, o.zone ?? T.zones.seam, tag("seam", prefix))];
}

/**
 * V4-5A — a door outline RELATIVE to its host's face (so it follows the fitted cab by construction): `front` / `rear`
 * are insets (m) from the host's front (max z) / rear (min z) edge, `bottom` / `top` absolute y, `knee` the y where the
 * front edge starts to rake back by `rake` (dz per dy, the A-pillar). Every value is clamped inside the host face
 * (one seam width + MIN_FEAT from each edge), so no fitted knob can push the path off the host.
 */
function doorPath(d, hb, axis, w, g) {
  if (axis !== 0) fail("seam door: is a flank outline — face must be \"+x\" or \"-x\"");
  if (!d || typeof d !== "object") fail("seam door must be { front, rear, bottom, knee, top, rake } (metres)");
  const m = g.MIN_FEAT;
  const edge = w / 2 + g.seat;
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const zf = hb.max[2] - clamp(finite(d.front, "seam door.front"), edge, (hb.max[2] - hb.min[2]) / 2);
  const zr = hb.min[2] + clamp(finite(d.rear, "seam door.rear"), edge, zf - hb.min[2] - m - w);
  const yb = clamp(finite(d.bottom, "seam door.bottom"), hb.min[1] + edge, hb.max[1] - edge - m - w);
  const yt = clamp(finite(d.top, "seam door.top"), yb + m + w, hb.max[1] - edge);
  const yk = clamp(d.knee === undefined ? yb : finite(d.knee, "seam door.knee"), yb, yt);
  const rake = d.rake === undefined ? 0 : finite(d.rake, "seam door.rake");
  const zt = clamp(zf - rake * (yt - yk), zr + m + w, zf);
  return [[zr, yb], [zf, yb], [zf, yk], [zt, yt], [zr, yt]];
}

/**
 * handle({ host, face, bounds | poly }) — WF-R5 R5-A: a door handle as a MIN_FEAT inlay in the handle tone (sampled off
 * the target), sunk GROOVE_DEPTH_MAX into the face. One call per handle (loop the faces for the pair).
 */
export function handle(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("handle host must be the PART the handle sits in (e.g. the cab part)");
  const { axis, sign } = faceOf(o.face, "handle");
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const pts = footprint(o, g, axis, hb, "handle bounds");
  const solid = layer(o, g, host, axis, sign, prismOf(pts, axis, hb.min[axis] - 1, hb.max[axis] + 1), g.MIN_FEAT, g.grooveDepthMax, "handle bounds");
  const prefix = o.idPrefix ?? `handle_${o.face.replace("+", "p").replace("-", "n")}`;
  return [part(prefix, solid, o.role ?? host.role, o.zone ?? T.zones.handle, tag("handle", prefix))];
}

function noseFace(o, g, what) {
  const P = bodyPlanes(o.body, { table: g.table });
  const face = o.face ?? "nose";
  if (face !== "nose" && face !== "tail") fail(`${what} face must be "nose" or "tail", got ${JSON.stringify(face)}`);
  return face === "nose" ? { P, z: P.nose, dir: 1, proud: P.noseProud } : { P, z: P.tail, dir: -1, proud: P.tailProud };
}

/** The body part whose face at f.z carries the rect x0..x1, y0..y1 — or BAD_ARG. */
function onFace(o, g, f, x0, x1, y0, y1, what) {
  const T = vt(g);
  const ok = (p) => {
    if (!p || !T.bodyRoles.includes(p.role) || !K.isSolid(p.solid)) return false;
    const b = p.solid.aabb();
    const z = f.dir > 0 ? b.max[2] : b.min[2];
    return Math.abs(z - f.z) <= g.epsAbs && b.min[0] <= x0 + EPS && b.max[0] >= x1 - EPS && b.min[1] <= y0 + EPS && b.max[1] >= y1 - EPS;
  };
  const host = o.body.find(ok);
  if (!host) {
    fail(`${what} x ${f3(x0)}..${f3(x1)}, y ${f3(y0)}..${f3(y1)} is not on one body part's ${o.face ?? "nose"} face (z ${f3(f.z)}) — keep it inside the hood's front face`);
  }
  return host;
}

/**
 * lamp({ body: parts, face: "nose", centre: [x, y], diameter }) — the headlight PAIR: round lenses at x and its mirror
 * across the body's centre plane, seated on the nose (or tail) face. Refuses a lens prouder than the bumper.
 */
export function lamp(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  if (o.face === "cap") return capLamp(o, g);
  const f = noseFace(o, g, "lamp");
  const [x, y] = vec(o.centre, 2, "lamp centre");
  // V5-3 `shape: { w, h, r? }` — a rounded-rect lens (w across x, h up y, corner r) in place of the round one
  const shape = o.shape === undefined ? null : { w: finite(o.shape.w, "lamp shape.w"), h: finite(o.shape.h, "lamp shape.h"), r: o.shape.r === undefined ? 0 : Math.max(0, finite(o.shape.r, "lamp shape.r")) };
  const d = shape ? Math.max(shape.w, shape.h) : finite(o.diameter, "lamp diameter");
  if (shape) { floorCheck(g, shape.w, "lamp shape.w"); floorCheck(g, shape.h, "lamp shape.h"); } else floorCheck(g, d, "lamp diameter");
  const t = o.thickness === undefined ? g.MIN_FEAT : finite(o.thickness, "lamp thickness");
  floorCheck(g, t, "lamp thickness");
  // V5-3 `ring: w` — a bezel ring w wide round a round lens (role prop, `ringZone`, default "black"), sunk with it
  const ring = o.ring === undefined || o.ring === 0 ? 0 : finite(o.ring, "lamp ring");
  if (ring < 0) fail("lamp ring must be >= 0");
  if (ring > 0 && shape) fail("lamp ring is for a round lens (no shape)");
  const dOut = d + 2 * ring;
  // V4-5A flush: the lens sits in a recess (<= GROOVE_DEPTH_MAX) this call cuts into the host face, so it stands only
  // t - recess - seat proud (a flush lamp reads as a lens in the face, not a disc on it)
  const recess = o.flush === true ? (o.recess === undefined ? g.grooveDepthMax : finite(o.recess, "lamp recess")) : 0;
  if (!(recess >= 0) || recess > g.grooveDepthMax + EPS) fail(`lamp recess ${f3(recess)} m must be 0..${g.grooveDepthMax} m (GROOVE_DEPTH_MAX)`);
  if (t - g.seat - recess > f.proud + EPS) fail(`lamp stands ${f3(t - g.seat - recess)} m proud, deeper than the bumper's ${f3(f.proud)} m — it would hide the far front wheel; thin it`);
  const pair = [x, 2 * f.P.centreX - x].sort((a, b) => b - a);
  if (pair[0] - pair[1] < dOut + EPS) fail(`lamp centre x ${f3(x)} is within one diameter of the centre plane x ${f3(f.P.centreX)} — the pair would overlap`);
  const segs = o.segs ?? T.construction.lampSegs;
  const rot = (s) => s.rotX(f.dir > 0 ? 90 : -90);
  // a lens-shaped prism `depth` deep along the face normal, its back at z = 0 (turned onto the face by rot / placed below)
  const lensOf = (depth, grow = 0) => (shape
    ? frontSolid(roundRect(-shape.w / 2 - grow, shape.w / 2 + grow, -shape.h / 2 - grow, shape.h / 2 + grow, shape.r + grow, T.construction.cornerSegs ?? 2), f.dir > 0 ? 0 : -depth, f.dir > 0 ? depth : 0)
    : rot(K.revolve([[0, 0], [d / 2 + grow, 0], [d / 2 + grow, depth], [0, depth]], segs)));
  const disc = lensOf(t);
  const bezel = ring > 0 ? rot(K.revolve([[d / 2 - g.seat, 0], [dOut / 2, 0], [dOut / 2, t], [d / 2 - g.seat, t]], segs)) : null;
  const prefix = o.idPrefix ?? "lamp";
  const hh = shape ? shape.h / 2 : dOut / 2;
  const hw = shape ? shape.w / 2 : dOut / 2;
  return pair.flatMap((cx, i) => {
    const host = onFace(o, g, f, cx - hw, cx + hw, y - hh, y + hh, `lamp at x ${f3(cx)}`);
    if (recess > 0) {
      const hb = host.solid.aabb();
      if (hb.max[2] - hb.min[2] < recess + g.MIN_FEAT - EPS) fail(`lamp: host "${host.id}" is ${f3(hb.max[2] - hb.min[2])} m deep — a ${f3(recess)} m recess needs ${f3(recess + g.MIN_FEAT)} m`);
      const depth = recess + RECESS_OUTSIDE;
      const tool = lensOf(depth, ring).at([cx, y, f.z - f.dir * recess]);
      const cut = K.cut(host.solid, tool);
      host.solid = new K.Solid(cut._m, host.solid._thin, cut._cuts);
    }
    const sd = i === 0 ? "l" : "r";
    const at = [cx, y, f.z - f.dir * (g.seat + recess)];
    const out = [part(`${prefix}_${sd}`, disc.at(at), o.role ?? T.roles.lamp, o.zone ?? T.zones.lamp, tag("lamp", prefix))];
    if (bezel) out.push(part(`${prefix}_ring_${sd}`, bezel.at(at), "prop", o.ringZone ?? "black", tag("lamp", `${prefix}_ring`)));
    return out;
  });
}

/**
 * V5-3 — lamp({ host, face: "cap", body?, y, diameter, lenses: [{ x, zone }], housing?: { pad, r?, zone? }, segs?,
 * idPrefix? }) — lenses on ANY forward-facing surface of the host (the bus's rounded front cap and the nose face under
 * it): `lenses` are one side's lens centres (x > the host's centre plane), mirrored across it; each side's lenses sit
 * on one dark HOUSING (a rounded rect `pad` round them, zone default "black"). Housing and lenses are MIN_FEAT layers
 * that follow the host's +z surface as built (its fillets included), the lenses laid on the housing; role prop.
 */
function capLamp(o, g) {
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail('lamp face "cap" needs host: the body PART the lenses sit on (the cab part)');
  const m = g.MIN_FEAT;
  const d = finite(o.diameter, "lamp diameter");
  floorCheck(g, d, "lamp diameter");
  const y = finite(o.y, "lamp y");
  if (!Array.isArray(o.lenses) || o.lenses.length === 0) fail("lamp face \"cap\" needs lenses: [{ x, zone }, ...] (one side)");
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const cx = (hb.min[0] + hb.max[0]) / 2;
  const lenses = o.lenses.map((l, i) => ({ x: finite(l?.x, `lamp lenses[${i}].x`), zone: l?.zone ?? "lamp" }));
  for (const l of lenses) if (l.x - d / 2 <= cx + EPS) fail(`lamp lens x ${f3(l.x)} must lie on the +x side of the centre plane x ${f3(cx)} (one side; the other is mirrored)`);
  const pad = o.housing ? Math.max(m / 2, finite(o.housing.pad ?? m / 2, "lamp housing.pad")) : 0;
  const segs = o.segs ?? 8;
  const prefix = o.idPrefix ?? "marker";
  const lo = hb.min[2] - 1;
  const hi = hb.max[2] + 1;
  const flip = (x) => 2 * cx - x;
  const out = [];
  for (const [sd, sx] of [["l", (x) => x], ["r", flip]]) {
    const xs = lenses.map((l) => sx(l.x));
    const x0 = Math.min(...xs) - d / 2 - pad;
    const x1 = Math.max(...xs) + d / 2 + pad;
    const y0 = y - d / 2 - pad;
    const y1 = y + d / 2 + pad;
    if (x0 < hb.min[0] - EPS || x1 > hb.max[0] + EPS || y0 < hb.min[1] - EPS || y1 > hb.max[1] + EPS) fail(`lamp housing x ${f3(x0)}..${f3(x1)}, y ${f3(y0)}..${f3(y1)} leaves host "${host.id}"`);
    let seat = host;
    if (o.housing) {
      const r = o.housing.r === undefined ? 0.5 * (y1 - y0) / 2 : Math.max(0, finite(o.housing.r, "lamp housing.r"));
      // V5-6: the housing is a plate on the FORWARD-facing surface round its centre — the layer is clipped to `reach`
      // (default half its height + MIN_FEAT) behind the host surface at its centre, so on a rounded cap it does not run
      // back over the cap onto the roof (the V5-5 bus housing read 91 x 78 px against the target's 64 x 58)
      const base = PANE_BASE.get(host) ?? host.solid;
      const xm = (x0 + x1) / 2;
      const probe = K.intersect(base, bx([xm - 0.005, y - 0.005, lo], [xm + 0.005, y + 0.005, hi], "lamp housing probe"));
      const zc = probe.volume() > 0 ? probe.aabb().max[2] : hb.max[2];
      const reach = o.housing.reach === undefined ? (y1 - y0) / 2 + m : Math.max(m, finite(o.housing.reach, "lamp housing.reach"));
      const hs = layer({ face: "+z", body: o.body }, g, host, 2, 1, frontSolid(roundRect(x0, x1, y0, y1, r, 1), Math.max(lo, zc - reach), hi), m, 0, "lamp housing");
      seat = part(`${prefix}_housing_${sd}`, hs, o.role ?? "prop", o.housing.zone ?? "black", tag("lamp", `${prefix}_housing`));
      out.push(seat);
    }
    xs.forEach((lx, i) => {
      const circle = Array.from({ length: segs }, (_, k) => { const a = (2 * Math.PI * (k + 0.5)) / segs; return [lx + (d / 2) * Math.cos(a), y + (d / 2) * Math.sin(a)]; });
      const ls = layer({ face: "+z", body: o.housing ? undefined : o.body }, g, seat, 2, 1, frontSolid(circle, lo, hi), m, 0, `lamp lens ${i}`);
      out.push(part(`${prefix}_${sd}${i}`, ls, o.role ?? "prop", lenses[i].zone, tag("lamp", prefix)));
    });
  }
  return out;
}

/**
 * grille({ body: parts, face: "nose", bounds: K.span({ x, y }), slots }) — WF-R5 R5-A TWO-TONE: `bounds` is the SLOT
 * FIELD (the measured grille.w x grille.h). A frame MIN_FEAT round it and a bar of MIN_FEAT between slots (bar tone,
 * the body) stands MIN_PANEL proud of the nose; each of the `slots` horizontal slots is cut clean through the frame and
 * filled with an inlay in the slot tone (grille), GROOVE_DEPTH_MAX under the frame face — so the slots read dark
 * between lit bars in a flat unlit capture.
 */
export function grille(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const f = noseFace(o, g, "grille");
  const b = o.bounds;
  if (!b || !Array.isArray(b.x) || !Array.isArray(b.y)) fail("grille bounds must be K.span({ x: [lo, hi], y: [lo, hi] }) — the slot field");
  const n = o.slots;
  if (!Number.isInteger(n) || n < 1) fail(`grille slots must be an integer >= 1, got ${JSON.stringify(n)}`);
  const m = g.MIN_FEAT;
  const t = g.MIN_FEAT + g.grooveDepthMax;                       // MIN_PANEL: a groove leaves MIN_FEAT behind it
  if (t - g.seat > f.proud + EPS) fail(`grille panel stands ${f3(t - g.seat)} m proud, deeper than the bumper's ${f3(f.proud)} m`);
  const [x0, x1] = b.x;
  const [y0, y1] = b.y;
  // V5-3 `bar` (m, default MIN_FEAT): the slat between two slots (measured: grille.h - slots x grille.slotH)
  const bar = o.bar === undefined ? m : Math.max(m, finite(o.bar, "grille bar"));
  const slotH = (y1 - y0 - (n - 1) * bar) / n;
  if (slotH < g.MIN_FEAT - EPS) fail(`grille bounds y ${f3(y1 - y0)} m cannot hold ${n} slot(s) of MIN_FEAT with ${f3(bar)} m bars — need ${f3((n - 1) * bar + n * g.MIN_FEAT)} m`);
  floorCheck(g, x1 - x0, "grille slot length (bounds x)");
  onFace(o, g, f, x0 - m, x1 + m, y0 - m, y1 + m, "grille");
  const zb = f.z - f.dir * g.seat;
  const zf = zb + f.dir * t;
  const zz = (a, c) => [Math.min(a, c), Math.max(a, c)];
  const [pz0, pz1] = zz(zb, zf);
  const panel = bx([x0 - m, y0 - m, pz0], [x1 + m, y1 + m, pz1], "grille panel");
  const [tz0, tz1] = zz(zb - f.dir * RECESS_OUTSIDE, zf + f.dir * RECESS_OUTSIDE);
  const [iz0, iz1] = zz(zb, zf - f.dir * g.grooveDepthMax);
  const slotY = (i) => [y0 + i * (slotH + bar), y0 + i * (slotH + bar) + slotH];
  const tools = Array.from({ length: n }, (_, i) => bx([x0, slotY(i)[0], tz0], [x1, slotY(i)[1], tz1], "grille slot"));
  const prefix = o.idPrefix ?? "grille";
  const frame = K.cut(panel, tools.length === 1 ? tools[0] : K.union(tools));
  return [
    part(prefix, frame, o.role ?? T.roles.grille, o.barZone ?? T.zones.grilleBar, tag("grille", prefix)),
    ...Array.from({ length: n }, (_, i) => part(`${prefix}_slot_${i}`, bx([x0, slotY(i)[0], iz0], [x1, slotY(i)[1], iz1], "grille inlay"),
      o.role ?? T.roles.grille, o.zone ?? T.zones.grille, tag("grille", prefix))),
  ];
}

/** A rounded rectangle x0..x1, y0..y1 (counter-clockwise), corner radius r, `k` facets per corner (V5-2: K.profile.roundRect). */
const roundRect = (x0, x1, y0, y1, r, k) => roundRectProfile({ x: [x0, x1], y: [y0, y1], r, segs: k });

/**
 * V4-5A — hoodPanel({ host: hood, half: [nose, cowl], inset: [nose, cowl], crease? }): the hood's RAISED CENTRE PANEL — a
 * MIN_FEAT layer that follows the hood's top face (its slope included), over a trapezoid centred on the body's centre
 * plane: half-width `half[0]` at the nose end and `half[1]` at the cowl end, inset `inset[0]` from the hood's nose and
 * `inset[1]` from its cowl edge. Its two long edges are the creases the target draws; `crease: true` (off by default: ~140 tris) also lays
 * a seam inlay just outside each edge on the hood, so the crease reads in a flat unlit capture. Every value is clamped
 * inside the hood's top face (FIT may move them freely).
 */
export function hoodPanel(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("hoodPanel host must be the hood PART (parts.find((p) => p.id === \"hood\"))");
  const m = g.MIN_FEAT;
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const cx = (hb.min[0] + hb.max[0]) / 2;
  const hw = (hb.max[0] - hb.min[0]) / 2;
  const [hn, hc] = vec(o.half, 2, "hoodPanel half");
  const [inN, inC] = vec(o.inset ?? [0, 0], 2, "hoodPanel inset");
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const cw = T.construction.seamWidth;
  const halfN = clamp(hn, m, hw - 2 * m - cw);
  const halfC = clamp(hc, m, hw - 2 * m - cw);
  const zN = hb.max[2] - clamp(inN, 0, (hb.max[2] - hb.min[2]) / 2);
  const zC = hb.min[2] + clamp(inC, 0.01, zN - hb.min[2] - 2 * m);
  const pts = [[cx - halfC, zC], [cx + halfC, zC], [cx + halfN, zN], [cx - halfN, zN]];
  const prefix = o.idPrefix ?? "hoodPanel";
  // V5-3 `panel: false` — the crease lines only (a READY call adds the creases to a template that already built the panel)
  const out = o.panel === false ? [] : [part(prefix, layer({ face: "+y" }, g, host, 1, 1, planSolid(pts, hb.min[1] - 1, hb.max[1] + 1), m, 0, "hoodPanel"), o.role ?? host.role, o.zone ?? host.zone, tag("hoodPanel", prefix))];
  if (o.panel === false && o.crease !== true) fail("hoodPanel panel: false builds nothing without crease: true");
  if (o.crease === true) {
    // each crease line runs just OUTSIDE its panel edge (half a seam width + a seat off it): the parts never overlap.
    // MVP-STUB: a short return along the nose end widens the inlay's box to the V5 floor on both plan axes.
    const d = cw / 2 + g.seat;
    for (const [sd, sg] of [["l", 1], ["r", -1]]) {
      const line = [[cx + sg * (halfC + d), zC], [cx + sg * (halfN + d), zN - cw], [cx + sg * (halfN + d + m), zN - cw]];
      out.push(...seam({ table: o.table, host, face: "+y", path: line, body: o.body, idPrefix: `${prefix}_crease_${sd}` }));
    }
  }
  return out;
}

/**
 * mirror({ side, centreY, z, head: { w, h }, arm }) — the mirror PAIR. `side` = the +x flank plane x; each head
 * (w along x, h along y, MIN_FEAT deep in z) starts `arm` m outboard of the flank, seated on its arm, and the arm is
 * seated in the flank. Optional `body: parts` checks the arm really meets a body flank.
 */
export function mirror(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  let side = finite(o.side, "mirror side (flank plane x)");
  const cy = finite(o.centreY, "mirror centreY");
  const z = finite(o.z, "mirror z");
  const w = finite(o.head?.w, "mirror head.w");
  const h = finite(o.head?.h, "mirror head.h");
  const arm = finite(o.arm, "mirror arm");
  const cx = o.centreX !== undefined ? finite(o.centreX, "mirror centreX")
    : (Array.isArray(o.body) ? bodyPlanes(o.body, { table: g.table }).centreX : 0);
  if (!(side > cx)) fail(`mirror side ${f3(side)} must be the +x flank plane (> centre plane x ${f3(cx)})`);
  for (const [v, what] of [[w, "mirror head.w"], [h, "mirror head.h"], [arm, "mirror arm"]]) floorCheck(g, v, what);
  const s = g.MIN_FEAT;
  const { seat } = g;
  let armFrom = Infinity;
  // V5-3 `armFrom: [y, z]`: the arm's ROOT on the flank (a raked arm); the head may stand clear of the flank (ahead of a
  // raked A-pillar). The root's z is snapped onto the nearest body flank that spans its y.
  let [ay, az] = o.armFrom !== undefined ? vec(o.armFrom, 2, "mirror armFrom") : [cy, z];
  let armHost = null;
  if (Array.isArray(o.body)) {
    const flank = (p) => p && T.bodyRoles.includes(p.role) && K.isSolid(p.solid) && !INLAYS.includes(p.assembly?.helper) && Math.abs(p.solid.aabb().max[0] - side) <= g.epsAbs;
    const meets = (p) => {
      if (!flank(p)) return false;
      const bb = p.solid.aabb();
      return bb.min[1] <= ay && bb.max[1] >= ay && bb.min[2] <= az - s / 2 && bb.max[2] >= az + s / 2;
    };
    let host = o.body.find(meets);
    if (!host && o.armFrom !== undefined) {
      const near = o.body.filter((p) => flank(p) && p.solid.aabb().min[1] <= ay && p.solid.aabb().max[1] >= ay)
        .map((p) => { const bb = p.solid.aabb(); const zz = Math.min(bb.max[2] - s, Math.max(bb.min[2] + s, az)); return { p, zz, d: Math.abs(zz - az) }; })
        .sort((a, b) => a.d - b.d)[0];
      if (near) { host = near.p; az = near.zz; }
    }
    if (!host) fail(`mirror arm at y ${f3(ay)}, z ${f3(az)} does not meet a body flank at x ${f3(side)} — take side/centreY/z from MEASURED NUMBERS`);
    armHost = host;
    side = host.solid.aabb().max[0];                 // snap to the flank the arm meets: a printed mm must not open a gap
    // WF-R5 R5-A: a cab leaning in above the glass line puts the flank inside its box at the arm: the arm starts on the
    // flank surface actually under it (the host sliced at the arm's section), never in the air beside it.
    const hb = host.solid.aabb();
    // V5-3: probed on the flank AS BUILT (PANE_BASE), never on an inlay groove cut into it since (a door leaf under the arm)
    const under = K.intersect(PANE_BASE.get(host) ?? host.solid, bx([hb.min[0] - 1, ay - s / 2, az - s / 2], [hb.max[0] + 1, ay + s / 2, az + s / 2], "mirror probe"));
    if (under.volume() > 0) armFrom = under.aabb().max[0];
  }
  // V4-5A: `head.round` (m) rounds the head's four corners in its x-y outline (a rounded-rect mirror head)
  // (a passed round is floored at 0.2 x the head's short side: FIT may tune it but never square the head again)
  const round = o.head?.round === undefined ? 0 : Math.max(0.2 * Math.min(w, h), Math.min(finite(o.head.round, "mirror head.round"), Math.min(w, h) / 2 - 0.002));
  const head = round > 0.002
    ? frontSolid(roundRect(side + arm, side + arm + w, cy - h / 2, cy + h / 2, round, T.construction.cornerSegs ?? 2), z - s / 2, z + s / 2)
    : bx([side + arm, cy - h / 2, z - s / 2], [side + arm + w, cy + h / 2, z + s / 2], "mirror head");
  const flip = (solid) => solid.at([-cx, 0, 0]).mirrorX().at([cx, 0, 0]);
  const prefix = o.idPrefix ?? "mirror";
  const role = o.role ?? T.roles.mirror;
  const zone = o.zone ?? T.zones.mirror;
  // V5-3 arm PATHS: `bracket: true` — two straight arms at the head's top and bottom edge (the bus's "[" bracket);
  // `armFrom: [y, z]` — ONE angled arm (K.beam, MIN_FEAT square) from the flank at (y, z) to the head's inner edge
  // centre (the pickup's raked arm). Default: one straight arm at centreY.
  let bars;
  if (o.armFrom !== undefined) {
    // the beam runs from inside the flank to inside the head, then both are cut back out of it less a seat (x), so its
    // tilted end sections sit a seat deep in each and never further (V6)
    let beam = K.beam([Math.min(side, armFrom) - s, ay, az], [side + arm + s, cy, z], { w: s, h: s });
    beam = K.cut(beam, head.at([seat, 0, 0]));
    // every body part / inlay the beam crosses (the flank as built, a seam or door inlay on it) is cut out of it, a seat
    // short; the largest lump is the arm
    const bb = beam.aabb();
    const hit = (b) => [0, 1, 2].every((a) => b.min[a] < bb.max[a] && b.max[a] > bb.min[a]);
    const others = (Array.isArray(o.body) ? o.body : []).filter((q) => q && K.isSolid(q.solid) && (T.bodyRoles.includes(q.role) || INLAYS.includes(q.assembly?.helper)) && hit(q.solid.aabb()))
      .map((q) => (q === armHost ? (PANE_BASE.get(q) ?? q.solid) : q.solid).at([-seat, 0, 0]));
    if (others.length) beam = K.cut(beam, others.length === 1 ? others[0] : K.union(others));
    const lumps = beam.decompose();
    const big = lumps.reduce((a, c) => (c.volume() > a.volume() ? c : a), lumps[0]);
    if (!big || !(big.volume() > 0)) fail("mirror armFrom: the arm is swallowed by the body — move armFrom onto the flank under the head");
    bars = [new K.Solid(big._m, [], [])];
  } else if (o.bracket === true) {
    // inside the head's straight inner edge (its rounded corners start `round` from the top / bottom)
    const dy = Math.max(0, h / 2 - Math.max(round, 0) - s / 2);
    bars = [cy + dy, cy - dy].map((y) => bx([Math.min(side, armFrom) - seat, y - s / 2, z - s / 2], [side + arm + seat, y + s / 2, z + s / 2], "mirror arm"));
  } else {
    bars = [bx([Math.min(side, armFrom) - seat, cy - s / 2, z - s / 2], [side + arm + seat, cy + s / 2, z + s / 2], "mirror arm")];
  }
  const armId = (sd, i) => (bars.length === 1 ? `${prefix}_arm_${sd}` : `${prefix}_arm_${sd}${i}`);
  return [
    part(`${prefix}_head_l`, head, role, zone, tag("mirror", `${prefix}_l`)),
    ...bars.map((b, i) => part(armId("l", i), b, role, zone, tag("mirror", `${prefix}_l`))),
    part(`${prefix}_head_r`, flip(head), role, zone, tag("mirror", `${prefix}_r`)),
    ...bars.map((b, i) => part(armId("r", i), flip(b), role, zone, tag("mirror", `${prefix}_r`))),
  ];
}

/**
 * V4-7 — windowRow({ host, faces?, band: [y0, y1], z: [rear, front], panes: { front, pitch, w, count, y: [y0, y1] },
 * body?, zone?, idPrefix? }) — a bus WINDOW BAND with its PANE ROW on each flank face (default both, "+x" and "-x"):
 * the band is a MIN_FEAT inlay in the band tone (default "black") sunk GROOVE_DEPTH_MAX into the flank over
 * z rear..front, y band[0]..band[1], with a hole per pane; pane i is a K.assemble.pane on the same face spanning
 * z (front - i pitch - w)..(front - i pitch), y panes.y. Every value is clamped inside the host flank (FIT may move
 * them freely): the row keeps `count` panes, the band keeps MIN_FEAT round them.
 */
export function windowRow(o = {}) {
  const g = vgate(o);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("windowRow host must be the body PART (the cab part of a bus)");
  const m = g.MIN_FEAT;
  const hb = (PANE_BASE.get(host) ?? host.solid).aabb();
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const [b0, b1] = vec(o.band, 2, "windowRow band").sort((a, b) => a - b);
  const [zr, zf] = vec(o.z, 2, "windowRow z").sort((a, b) => a - b);
  const p = o.panes ?? {};
  const n = p.count;
  if (!Number.isInteger(n) || n < 1) fail(`windowRow panes.count must be an integer >= 1, got ${JSON.stringify(n)}`);
  const edge = m + g.seat;
  // V5-3 `wrap` (m, default 0): the band runs to the tail and wraps round the rear corner onto the tail face by `wrap`
  const wrap = o.wrap === undefined ? 0 : Math.max(0, finite(o.wrap, "windowRow wrap"));
  const zR = clamp(zr, hb.min[2] + (wrap > 0 ? g.seat : edge), hb.max[2] - edge - 3 * m);
  const zF = clamp(zf, zR + 3 * m, hb.max[2] - edge);
  const yb = clamp(b0, hb.min[1] + edge, hb.max[1] - edge - 3 * m);
  const yt = clamp(b1, yb + 3 * m, hb.max[1] - edge);
  const [py0, py1] = vec(p.y, 2, "windowRow panes.y").sort((a, b) => a - b);
  const pyb = clamp(py0, yb + m, yt - 2 * m);
  const pyt = clamp(py1, pyb + m, yt - m);
  const pitch = finite(p.pitch, "windowRow panes.pitch");
  const w = clamp(finite(p.w, "windowRow panes.w"), m, Math.max(m, pitch - m));
  const front = clamp(finite(p.front, "windowRow panes.front"), zR + m + w + (n - 1) * pitch, zF - m);
  const zs = Array.from({ length: n }, (_, i) => [front - i * pitch - w, front - i * pitch]);
  const faces = o.faces ?? ["+x", "-x"];
  const prefix = o.idPrefix ?? "row";
  const out = [];
  for (const face of faces) {
    const { axis, sign } = faceOf(face, "windowRow");
    if (axis !== 0) fail('windowRow faces are the flanks ("+x" / "-x")');
    const sd = sign > 0 ? "l" : "r";
    const holes = zs.map(([a, b]) => sideSolid([[a, pyb], [b, pyb], [b, pyt], [a, pyt]], hb.min[0] - 2, hb.max[0] + 2));
    const whole = sideSolid([[zR, yb], [zF, yb], [zF, yt], [zR, yt]], hb.min[0] - 1, hb.max[0] + 1);
    // V5-3: ONE groove under the whole band carries the band and every pane (each sunk to it, no per-pane recess cut)
    groove(g, host, axis, sign, whole, g.grooveDepthMax, "windowRow band");
    const strip = K.cut(whole, holes.length === 1 ? holes[0] : K.union(holes));
    const bandSolid = layer({ face, body: o.body, cut: false }, g, host, axis, sign, strip, m, g.grooveDepthMax, "windowRow band");
    const band = part(`${prefix}_band_${sd}`, bandSolid, o.role ?? host.role, o.zone ?? "black", tag("band", `${prefix}_band_${sd}`));
    out.push(band);
    zs.forEach(([a, b], i) => out.push(...pane({ table: o.table, host, face, bounds: span({ z: [a, b], y: [pyb, pyt] }), recess: g.grooveDepthMax, cut: false, idPrefix: `${prefix}_${sd}${i}` })));
    if (wrap > 0) {
      // the tail face (-z): x from the flank inward by `wrap`, the band's y; the flank band is cut out of it at the corner
      const xs = sign > 0 ? [Math.max(hb.max[0] - wrap, hb.min[0] + m), hb.max[0] + 1] : [hb.min[0] - 1, Math.min(hb.min[0] + wrap, hb.max[0] - m)];
      const tail = planSolid([[xs[0], hb.min[2] - 1], [xs[1], hb.min[2] - 1], [xs[1], hb.max[2] + 1], [xs[0], hb.max[2] + 1]], yb, yt);
      const ws = layer({ face: "-z", body: [...(Array.isArray(o.body) ? o.body : []), band] }, g, host, 2, -1, tail, m, g.grooveDepthMax, "windowRow wrap");
      out.push(part(`${prefix}_wrap_${sd}`, ws, o.role ?? host.role, o.zone ?? "black", tag("band", `${prefix}_wrap_${sd}`)));
    }
  }
  return out;
}

/**
 * V4-7 — stopArm({ host, face?, centre: [z, y], diameter, body?, post?, zone?, postZone? }) — the folded bus STOP ARM on a
 * flank (default "+x", the near side only): an octagonal sign MIN_FEAT thick seated a seat into the flank (role prop,
 * zone "signal") and, when `post` (m, its length down from the sign's centre), a MIN_FEAT square post at the sign's
 * front edge (zone "black"), both seated into the flank.
 */
export function stopArm(o = {}) {
  const g = vgate(o);
  const host = o.host;
  if (!host || !K.isSolid(host.solid)) fail("stopArm host must be the body PART it folds against");
  const { axis, sign } = faceOf(o.face ?? "+x", "stopArm");
  if (axis !== 0) fail('stopArm face is a flank ("+x" / "-x")');
  const hb = host.solid.aabb();
  const [zc, yc] = vec(o.centre, 2, "stopArm centre");
  const d = finite(o.diameter, "stopArm diameter");
  floorCheck(g, d, "stopArm diameter");
  const m = g.MIN_FEAT;
  const r = d / 2;
  if (zc - r < hb.min[2] - EPS || zc + r > hb.max[2] + EPS || yc - r < hb.min[1] - EPS || yc + r > hb.max[1] + EPS) fail(`stopArm sign z ${f3(zc - r)}..${f3(zc + r)}, y ${f3(yc - r)}..${f3(yc + r)} leaves host "${host.id}"`);
  // `body: parts` — the sign seats on the OUTERMOST surface under it (a window band inlay it crosses), never inside it
  const under = (Array.isArray(o.body) ? o.body : []).filter((p) => p && p !== host && K.isSolid(p.solid)).map((p) => p.solid.aabb())
    .filter((b) => b.min[1] < yc + r && b.max[1] > yc - r && b.min[2] < zc + r && b.max[2] > zc - r && (sign > 0 ? b.max[0] > hb.max[0] - 0.2 : b.min[0] < hb.min[0] + 0.2));
  const xFace = sign > 0 ? Math.max(hb.max[0], ...under.map((b) => b.max[0])) : Math.min(hb.min[0], ...under.map((b) => b.min[0]));
  let x0 = xFace - sign * g.seat;
  const octOf = (rr) => K.revolve([[0, 0], [rr, 0], [rr, m], [0, m]], 8).rotY(22.5).rotZ(sign > 0 ? -90 : 90);
  const prefix = o.idPrefix ?? "stopArm";
  const out = [];
  // V5-3 `border` (m): the sign's light rim — an octagon `border` wider behind the sign (zone `borderZone`, default
  // "lamp"), the red face seated on it; `post`: a length down from the sign's centre, or [yBottom, yTop] (m)
  const border = o.border === undefined ? 0 : Math.max(0, finite(o.border, "stopArm border"));
  if (zc - r - border < hb.min[2] - EPS || zc + r + border > hb.max[2] + EPS) fail(`stopArm border z ${f3(zc - r - border)}..${f3(zc + r + border)} leaves host "${host.id}"`);
  if (border > 0) {
    out.push(part(`${prefix}_border`, octOf(r + border).at([x0, yc, zc]), o.role ?? "prop", o.borderZone ?? "lamp", tag("stopArm", prefix)));
    x0 += sign * (m - g.seat);
  }
  // an octagon disc: revolved about Y with 8 facets, its axis turned onto X (outer face at x0 + sign m)
  out.unshift(part(`${prefix}_sign`, octOf(r).at([x0, yc, zc]), o.role ?? "prop", o.zone ?? "signal", tag("stopArm", prefix)));
  if (o.post !== undefined) {
    let [py0, py1] = Array.isArray(o.post) ? vec(o.post, 2, "stopArm post").sort((a, b) => a - b) : [yc - finite(o.post, "stopArm post"), yc];
    py0 = Math.max(hb.min[1] + m, py0);
    py1 = Math.min(hb.max[1] - m, py1);
    floorCheck(g, py1 - py0, "stopArm post");
    const zp = Math.min(zc + r + border, hb.max[2] - m) + m / 2 - g.seat;
    const xb = xFace - sign * g.seat;
    const [px0, px1] = [Math.min(xb, xb + sign * m), Math.max(xb, xb + sign * m)];
    out.push(part(`${prefix}_post`, bx([px0, py0, zp - m / 2], [px1, py1, zp + m / 2], "stopArm post"), o.role ?? "prop", o.postZone ?? "black", tag("stopArm", prefix)));
  }
  return out;
}

/**
 * vehicleBody({ W, H, side, section, plan?, cab, bed, sill, clearance, wheels, arches, bumpers, zones? }) — WF-R5 R5-A:
 * the P0 body from its MEASURED PROFILES (scripts/measure-profile.mjs), in metres (scripts/template-vehicle.mjs prints
 * every argument from layout.json):
 *   body = extrude(side) ∩ extrude(section) ∩ extrude(plan), sliced by ROLE: hood (cab front .. nose), cab, and an OPEN
 *   bed (body-tone walls with a rim, bed-tone inner liners, floor, bulkhead, tailgate); a wheel arch per axle cut
 *   tyre-deep into the flanks, grown until the tyre clears its well liner (wheel-well tone); a chassis between the
 *   wheels; bumpers (wrapped round the corners when `wrap` and `out` > 0); four wheels (near pair finer than the far).
 *   side: [[z, y], ...] side elevation of the painted body (nose = max z) · section: [[x, y], ...] the cab section
 *   plan: [[x, z], ...] (default the W x length rectangle) · cab: [rear z, front z] · bed: { z: [rear, front], floor, wallTop }
 *   sill: the body's lower edge y · clearance: chassis underside y · wheels: { r, width, z: [front, rear] }
 *   arches: [{ z, halfLength, rise, n }] superellipses on the sill · bumpers: [{ face, top, h, depth, out?, wrap? }]
 *   V5-2 rounding (m, default 0): roofR (section top corners) · capR (nose-top + roof-front arc) · cornerR (plan corners)
 */
export function vehicleBody(o = {}) {
  const g = vgate(o);
  const T = vt(g);
  const m = g.MIN_FEAT;
  const s = g.seat;
  const C = T.construction;
  const W = finite(o.W, "vehicleBody W");
  const H = finite(o.H, "vehicleBody H");
  const pts = (v, what) => {
    if (!Array.isArray(v) || v.length < 3) fail(`vehicleBody ${what} must be >= 3 points`);
    return v.map((p, i) => vec(p, 2, `vehicleBody ${what}[${i}]`));
  };
  const side = pts(o.side, "side");
  const section = pts(o.section, "section");
  const nose = Math.max(...side.map((p) => p[0]));
  const tail = Math.min(...side.map((p) => p[0]));
  const plan = o.plan ? pts(o.plan, "plan") : [[-W / 2, tail], [W / 2, tail], [W / 2, nose], [-W / 2, nose]];
  const Z = { body: "body", bed: "bed", tyre: "tyre", tread: "tread", hub: "hub", bumper: "bumper", liner: T.zones.archLiner, ...(o.zones ?? {}) };
  const [cabRear, cabFront] = vec(o.cab, 2, "vehicleBody cab").sort((a, b) => a - b);
  // V4-7: `bed: null` = no bed (the bus variant); `hood: false` = no hood slice, the cab runs to the nose
  const hasBed = o.bed !== null && o.bed !== false;
  const bed = hasBed ? (o.bed ?? {}) : null;
  const [bedRear, bedFront] = hasBed ? vec(bed.z, 2, "vehicleBody bed.z").sort((a, b) => a - b) : [0, 0];
  const wantFloor = !hasBed || bed.floor === undefined ? -Infinity : finite(bed.floor, "vehicleBody bed.floor");
  const wallTop = hasBed ? finite(bed.wallTop, "vehicleBody bed.wallTop") : 0;
  const hasHood = o.hood !== false;
  const sill = finite(o.sill, "vehicleBody sill");
  const clearance = finite(o.clearance, "vehicleBody clearance");
  const wh = o.wheels ?? {};
  const R = finite(wh.r, "vehicleBody wheels.r");
  const tyreW = wh.width === undefined ? 0.3 : finite(wh.width, "vehicleBody wheels.width");
  const axles = vec(wh.z, 2, "vehicleBody wheels.z");
  const [segNear, segFar] = wh.segs ?? C.wheelSegs;
  const parts = [];
  const add = (id, solid, zone, role) => { const p = part(id, solid, role, zone); parts.push(p); return p; };
  const slab = (x0, x1, y0, y1, z0, z1) => bx([x0, y0, z0], [x1, y1, z1], "vehicleBody slab");

  // ---- the profile body
  // A plan that is the bare W x length rectangle adds nothing but faces coplanar with the section's flanks (which
  // leave slivers in later inlay layers), so it is only intersected when it cuts something.
  const pb = [[Math.min(...plan.map((p) => p[0])), Math.max(...plan.map((p) => p[0]))], [Math.min(...plan.map((p) => p[1])), Math.max(...plan.map((p) => p[1]))]];
  // V5-2: optional rounding (m, default 0 = the sharp profiles, byte-identical): `roofR` the section's top corners,
  // `capR` the side elevation's nose-top and roof-front corners (an arc over the nose->roof cap), `cornerR` every plan
  // corner; `roundSegs` facets per arc (default 3). K.profile.fillet clamps each arc to half its shorter edge.
  const rad = (v, what) => (v === undefined ? 0 : Math.max(0, finite(v, `vehicleBody ${what}`)));
  const [rRoof, rCap, rCorner] = [rad(o.roofR, "roofR"), rad(o.capR, "capR"), rad(o.cornerR, "cornerR")];
  const rSegs = o.roundSegs ?? 3;
  const topY = Math.max(...section.map((p) => p[1]));
  const sectionR = rRoof > 0 ? fillet(section, section.map((p) => (p[1] >= topY - EPS ? rRoof : 0)), rSegs) : section;
  let sideR = side;
  if (rCap > 0) {
    const roofY = Math.max(...side.map((p) => p[1]));
    const noseTop = Math.max(...side.filter((p) => p[0] >= nose - EPS).map((p) => p[1]));
    const roofFront = Math.max(...side.filter((p) => p[1] >= roofY - EPS).map((p) => p[0]));
    sideR = fillet(side, side.map((p) => ((p[0] >= nose - EPS && p[1] >= noseTop - EPS) || (p[1] >= roofY - EPS && p[0] >= roofFront - EPS) ? rCap : 0)), rSegs);
  }
  const planR = rCorner > 0 ? fillet(plan, rCorner, rSegs) : plan;
  const planIsBox = planR.length === 4 && pb[0][0] <= -W / 2 + EPS && pb[0][1] >= W / 2 - EPS && pb[1][0] <= tail + EPS && pb[1][1] >= nose - EPS;
  const P = K.intersect(sideSolid(sideR, -W, W), frontSolid(sectionR, tail - 1, nose + 1), ...(planIsBox ? [] : [planSolid(planR, -1, H + 1)]));
  const zSlice = (z0, z1) => K.intersect(P, slab(-W, W, -1, H + 1, z0, z1));

  // ---- wheel arches: superellipse on the sill, grown until the tyre + tyreClear sits inside the liner's inner outline
  const archDepth = tyreW + C.archClear;
  // V5-3: arch outline facets [near (+x), far (-x)], default [12, 12] (byte-identical)
  const [archNear, archFar] = o.archSegs === undefined ? [12, 12] : vec(o.archSegs, 2, "vehicleBody archSegs").map((v) => Math.max(2, Math.round(v)));
  const arches = (o.arches ?? []).map((a, i) => {
    const zc = finite(a.z, `arch ${i} z`);
    const n = finite(a.n, `arch ${i} n`);
    let half = finite(a.halfLength, `arch ${i} halfLength`);
    let rise = finite(a.rise, `arch ${i} rise`);
    const zw = axles.reduce((b, z) => (Math.abs(z - zc) < Math.abs(b - zc) ? z : b));
    const clear = (h, r) => {
      for (let k = 0; k < 64; k += 1) {
        const t = (2 * Math.PI * k) / 64;
        const zz = zw + (R + C.tyreClear) * Math.cos(t);
        const yy = R + (R + C.tyreClear) * Math.sin(t);
        if (yy <= sill) continue;
        const u = Math.abs(zz - zc) / (h - m);
        const v = (yy - sill) / (r - m);
        if (u >= 1 || u ** n + v ** n >= 1) return false;
      }
      return true;
    };
    let grown = 0;
    while (!clear(half, rise) && grown < 60) { half += 0.01; rise += 0.01; grown += 1; }
    const curve = (h, r, k = 12) => Array.from({ length: k + 1 }, (_, j) => {
      const t = (Math.PI * j) / k;
      const c = Math.cos(t);
      return [zc + h * Math.sign(c) * Math.abs(c) ** (2 / n), sill + r * Math.abs(Math.sin(t)) ** (2 / n)];
    });
    const toolL = sideSolid([...curve(half, rise, archNear), [zc - half, -1], [zc + half, -1]], W / 2 - archDepth, W / 2 + 1);
    // V5-3 far-side LOD: the -x arch (hidden at the solved camera) may take fewer facets (archSegs[1])
    const toolR = archFar === archNear ? toolL : sideSolid([...curve(half, rise, archFar), [zc - half, -1], [zc + half, -1]], W / 2 - archDepth, W / 2 + 1);
    return { zc, half, rise, grown, curve, tool: K.union(toolL, toolR.mirrorX()) };
  });
  // the bed floor clears every arch under the bed by MIN_FEAT (bed.floor may be unmeasured: the floor is hidden)
  const floorTop = !hasBed ? 0 : Math.max(wantFloor, ...arches.filter((a) => a.zc - a.half < bedFront && a.zc + a.half > bedRear).map((a) => sill + a.rise + m + 0.005));
  if (!Number.isFinite(floorTop)) fail("vehicleBody bed.floor is required when no arch sits under the bed");
  const cutArches = (solid) => {
    let out = solid;
    for (const a of arches) {
      const b = out.aabb();
      if (b.max[2] <= a.zc - a.half || b.min[2] >= a.zc + a.half || b.min[1] >= sill + a.rise) continue;
      out = K.cut(out, a.tool);
    }
    return out;
  };

  // ---- chassis + body slices
  // V4-7: `chassisFront` (z) stops the chassis short of a nose block that drops below the sill (the bus)
  const chassisFront = o.chassisFront === undefined ? Math.max(...axles) + R : finite(o.chassisFront, "vehicleBody chassisFront");
  add("chassis", slab(-(W / 2 - tyreW + s), W / 2 - tyreW + s, clearance, sill + s, tail, chassisFront), Z.tyre, "chassis");
  if (hasHood) add("hood", cutArches(zSlice(cabFront - s, nose + 1)), Z.body, "hood");
  add("cab", cutArches(zSlice(cabRear, hasHood ? cabFront : nose + 1)), Z.body, "cab");

  // ---- open bed: skin (body) + rim, liner (bed tone) on the inside, floor over the rear arch liner
  if (hasBed) {
  const shell = zSlice(bedRear, bedFront);
  const inShell = (solid) => K.intersect(shell, solid);
  const xo = W / 2;
  const xi = W / 2 - 2 * m;
  const sideSkin = cutArches(inShell(K.union(slab(xo - m, xo + 1, -1, H + 1, bedRear - 1, bedFront + 1), slab(xi, xo + 1, wallTop - m, H + 1, bedRear - 1, bedFront + 1))));
  const sideLiner = cutArches(inShell(slab(xi, xo - m + s, floorTop - s, wallTop - m + s, bedRear + m - s, bedFront - m + s)));
  add("bed_side_l", sideSkin, Z.body, "bed_wall");
  add("bed_side_r", sideSkin.mirrorX(), Z.body, "bed_wall");
  add("bed_liner_l", sideLiner, Z.bed, "bed_wall");
  add("bed_liner_r", sideLiner.mirrorX(), Z.bed, "bed_wall");
  const endWall = (zFace, dir, id, role) => {
    const span = (a, b) => (dir > 0 ? [zFace - b, zFace - a] : [zFace + a, zFace + b]);
    const x = xi + s;
    add(id, inShell(K.union(slab(-x, x, floorTop - s, H + 1, ...span(0, m)), slab(-x, x, wallTop - m, H + 1, ...span(0, 2 * m)))), Z.body, role);
    add(`${id}_liner`, inShell(slab(-x, x, floorTop - s, wallTop - m + s, ...span(m - s, 2 * m))), Z.bed, role);
  };
  endWall(bedFront, 1, "bed_bulkhead", "bed_wall");
  endWall(bedRear, -1, "tailgate", "tailgate");
  add("bed_floor", cutArches(inShell(slab(-(xo - m + s), xo - m + s, -1, floorTop, bedRear - 1, bedFront + 1))), Z.bed, "bed");
  }

  // ---- arch liners: a shell (outer overlaps the body by a seat) + the well's back plate, clear of the tyre
  const linerOf = (a, k) => {
    const outer = a.curve(a.half + s, a.rise + s, k);
    const shellL = sideSolid([...outer, ...a.curve(a.half - m, a.rise - m, k).reverse()], W / 2 - archDepth, W / 2 - 0.01);
    const plateL = sideSolid(outer, W / 2 - archDepth - s, W / 2 - archDepth + m);
    return K.union(shellL, plateL);
  };
  // V5-6 `liner: false` — no liner parts: the arch cut's own faces (the body zone) close the well (the bus target shows
  // an unlabelled shade there, no black liner)
  for (const [i, a] of (o.liner === false ? [] : arches).entries()) {
    const liner = linerOf(a, archNear);
    const tagId = i === 0 ? "f" : "r";
    add(`arch_${tagId}l`, liner, Z.liner, T.roles.archLiner);
    add(`arch_${tagId}r`, (archFar === archNear ? liner : linerOf(a, archFar)).mirrorX(), Z.liner, T.roles.archLiner);
  }

  // ---- bumpers
  for (const b of o.bumpers ?? []) {
    const dir = b.face === "tail" ? -1 : 1;
    const zFace = dir > 0 ? nose : tail;
    const top = finite(b.top, "bumper top");
    const h = finite(b.h, "bumper h");
    const depth = finite(b.depth, "bumper depth");
    const out = b.out === undefined ? 0 : finite(b.out, "bumper out");
    const wrap = b.wrap === undefined ? 0 : finite(b.wrap, "bumper wrap");
    const zo = zFace + dir * depth;
    const zi = zFace - dir * s;
    const zw = zFace - dir * wrap;
    const xb = W / 2 + out;
    const xs = W / 2 - s;
    const outline = wrap > 0 && out > 0
      ? [[-xb, zw], [-xb, zo], [xb, zo], [xb, zw], [xs, zw], [xs, zi], [-xs, zi], [-xs, zw]]
      : [[-xb, zi], [-xb, zo], [xb, zo], [xb, zi]];
    if (dir < 0 && wrap > 0 && out > 0) outline.reverse();   // V5-6: a wrapped TAIL outline runs the other way round
    add(dir > 0 ? "bumper_front" : "bumper_rear", planSolid(outline, top - h, top), Z.bumper, "bumper");
  }

  // ---- wheels: tyre disc (role wheel) + tread ring (role tyre) + hub (role hub); +x near pair finer than the -x pair
  const sw = Math.max(m, 0.06);
  const tt = Math.max(m, 0.06);
  // V4-5A: wheels.hub = { r, ring, cap } (m) — the hub disc radius, the radial width of its RIM RING and the radius of
  // its centre CAP; ring and cap stand MIN_FEAT proud of the hub face, so the hub reads as a dished wheel (rim lip,
  // recessed dish, cap). Clamped: the hub inside the tread, the cap MIN_FEAT inside the ring. No `hub` = the plain disc.
  const hubO = wh.hub ?? null;
  const clampH = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const hubR = hubO ? clampH(finite(hubO.r, "vehicleBody wheels.hub.r"), 3 * m, R - tt) : 0.62 * R;
  // V5-6: a hub whose ring / cap is omitted (undefined or null) is the plain disc (the bus target: one flat grey disc)
  const hasRing = hubO && hubO.ring !== undefined && hubO.ring !== null;
  const hasCap = hubO && hubO.cap !== undefined && hubO.cap !== null;
  const ringW = hasRing ? clampH(finite(hubO.ring, "vehicleBody wheels.hub.ring"), 0.02, hubR / 3) : 0;
  const capR = hasCap ? clampH(finite(hubO.cap, "vehicleBody wheels.hub.cap"), m / 2, hubR - ringW - m) : 0;
  const hubT = Math.max(m, 0.06);
  const [hubSegN, hubSegF] = wh.hubSegs ?? C.hubSegs ?? [12, 4];
  // V5-6 `wheels.tread: false` — ONE tyre solid (sidewall + rolling surface, zone tyre), no separate tread ring part (a
  // target whose tyre is one flat tone has no tread item)
  const treadOn = wh.tread !== false;
  const set = (segs, hsegs) => ({
    tyre: treadOn ? K.revolve([[0, 0], [R, 0], [R, sw], [R - tt + s, sw], [R - tt + s, tyreW], [0, tyreW]], segs).rotZ(90)
      : K.revolve([[0, 0], [R, 0], [R, tyreW], [0, tyreW]], segs).rotZ(90),
    tread: K.revolve([[R - tt, sw - s], [R, sw - s], [R, tyreW], [R - tt, tyreW]], segs).rotZ(90),
    hub: K.revolve([[0, 0], [hubR, 0], [hubR, hubT], [0, hubT]], segs).rotZ(90),
    ...(hasRing ? { ring: K.revolve([[hubR - ringW, 0], [hubR, 0], [hubR, m], [hubR - ringW, m]], hsegs).rotZ(90) } : {}),
    ...(hasCap ? { cap: K.revolve([[0, 0], [capR, 0], [capR, m], [0, m]], hsegs).rotZ(90) } : {}),
  });
  const near = set(segNear, hubSegN);
  const far = segFar === segNear && hubSegF === hubSegN ? near : set(segFar, hubSegF);
  const xHub = W / 2 + hubT - s;          // the hub's outer face
  for (const [ai, z] of axles.entries()) {
    for (const [sd, w, place] of [["l", near, (x) => x], ["r", far, (x) => x.mirrorX()]]) {
      const id = `${ai === 0 ? "f" : "r"}${sd}`;
      add(`wheel_${id}`, place(w.tyre.at([W / 2, R, z])), Z.tyre, "wheel");
      if (treadOn) add(`tread_${id}`, place(w.tread.at([W / 2, R, z])), Z.tread, "tyre");
      add(`hub_${id}`, place(w.hub.at([xHub, R, z])), Z.hub, "hub");
      if (hasRing) add(`hubring_${id}`, place(w.ring.at([xHub + m - s, R, z])), Z.hub, "hub");
      if (hasCap) add(`hubcap_${id}`, place(w.cap.at([xHub + m - s, R, z])), Z.hub, "hub");
    }
  }
  return parts;
}

/** The five helpers bound to a replacement defaults table (roles, zones, style floor, construction). */
export function withDefaults(table) {
  const t = { ...DEFAULT_TABLE, ...table };
  const bind = (fn) => (o = {}) => fn({ table: t, ...o });
  return Object.freeze({ grate: bind(grate), landing: bind(landing), flight: bind(flight), ladder: bind(ladder), frame: bind(frame), fireEscape: bind(fireEscape), wallPlanes, gateSpans, landingEdges, deckOf, flightArrivals, deckBoxes });
}
