// Class RULES for vehicles (WORKFLOW-V3 §5 pickup row, §7 item 10). Same contract
// as rules/building.mjs: the data half is classes/vehicle.json, and
// src/validate/kernel-chain.mjs receives both through
// `validateParts(meta, parts, limits, { cls, rules })`.
//
//   layoutRules  key -> { roles, unit, list?, measure(ctx, F) }
//   layoutFrame  (ctx) -> F | null   (L, W, H, zFront, zRear, xc)
//   validators   [[name, fn(ctx) -> {violations, advisories}], ...]
//
// Author frame (classes/vehicle.md): +Y up, y = 0 ground, LENGTH along Z with the
// nose at +Z, WIDTH along X centred on the mirror plane. Helpers arrive on
// `ctx.geo`, so this module never imports kernel-chain.mjs.

/** MVP-STUB: mirror-pair tolerance in metres. limits.json is frozen and carries
 *  no such key; unratified, overridable through `limits.mirrorTol`. */
export const MIRROR_TOL = 0.02;
/** MVP-STUB: equal-diameter tolerance in metres, overridable as `limits.wheelDiameterTol`. */
export const WHEEL_DIAMETER_TOL = 0.02;

export const INLAY_HELPERS = Object.freeze(["seam", "handle", "hoodPanel", "band"]);
/**
 * V4-5A — class priors of the detail helpers no layout key measures (MVP-STUB: read off refs/pickup_truck.png by eye;
 * FIT tunes every one as a knob): hub r / ring / cap as a fraction of the wheel radius R, the raised hood panel's
 * half-widths as a fraction of W and its insets in metres, the mirror head corner radius as a fraction of min(w, h).
 */
export const DETAIL_PRIORS = Object.freeze({
  hub: Object.freeze({ r: 0.62, ring: 0.1, cap: 0.3 }),
  hoodPanel: Object.freeze({ halfNose: 0.28, halfCowl: 0.22, insetNose: 0.012, insetCowl: 0.035 }),
  mirrorRound: 0.3,
  // V5-3 MVP-STUB: the pickup mirror's raked arm root, x head h below and ahead of the head centre (refs/pickup_truck.png read)
  mirrorArm: Object.freeze({ down: 0.75, ahead: 0.5 }),
});
const DEFAULT_LENGTH_ROLES = ["chassis", "body", "cab", "hood", "bed", "bed_wall", "tailgate"];
const ext = (box, axis) => box.max[axis] - box.min[axis];
const mid = (box, axis) => (box.min[axis] + box.max[axis]) / 2;

const lengthRoles = (ctx) => ctx.cls.lengthRoles ?? DEFAULT_LENGTH_ROLES;
const withRoles = (ctx, roles) => ctx.records.filter((r) => roles.includes(r.role));

/** The body's union box — the frame every vehicle rule is measured in. */
function coreBox(ctx) {
  // WF-R5 R5-A: seam / handle inlays stand MIN_FEAT - GROOVE_DEPTH_MAX proud of the body in its role; they are details, not the frame
  const core = withRoles(ctx, lengthRoles(ctx)).filter((r) => !INLAY_HELPERS.includes(r.part?.assembly?.helper));
  return core.length > 0 ? ctx.geo.unionBox(core) : (ctx.records.length > 0 ? ctx.geo.unionBox(ctx.records) : null);
}

/** One group per physical wheel: wheel + tyre + hub parts that overlap. */
export function wheelGroups(ctx) {
  const roles = ctx.cls.wheelRoles ?? ["wheel", "tyre", "hub"];
  return ctx.geo.groupAssemblies(withRoles(ctx, roles), [0, 1, 2])
    .sort((a, b) => (mid(b.box, 2) - mid(a.box, 2)) || (mid(a.box, 0) - mid(b.box, 0)));
}

/**
 * WF-R5 R5-A — WINDOWS group by part / assembly, never by bounding box: a tapered side pane's box overlaps the
 * windshield's (the unconstrained Opus reference had to trim its windshield to keep them apart). A helper-built pane is
 * its own assembly id; a hand-built glass part is one window; a hand-built non-glass member (frame, rail) joins the glass
 * window whose box it overlaps. Other roles keep the box grouping (a wheel = tyre + tread + hub overlapping).
 */
export function windowGroups(ctx, records) {
  if (typeof ctx.geo.groupTagged === 'function') return ctx.geo.groupTagged(records);
  const groups = new Map();
  const loose = [];
  for (const r of records) {
    const a = r.part?.assembly;
    const k = a?.helper && a.id ? 'a:' + a.helper + ':' + a.id : (r.zone === 'glass' ? 'p:' + r.id : null);
    if (k === null) { loose.push(r); continue; }
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(r);
  }
  const overlap = (p, q) => [0, 1, 2].every((i) => Math.min(p.max[i], q.max[i]) - Math.max(p.min[i], q.min[i]) > -1e-9);
  for (const r of loose) {
    const hit = [...groups.values()].find((members) => members.some((m) => overlap(m.aabb, r.aabb)));
    if (hit) hit.push(r); else groups.set('p:' + r.id, [r]);
  }
  return [...groups.values()].map((members) => ({ members, box: ctx.geo.unionBox(members) }));
}

const groupsOf = (ctx, role) => (role === "window" ? windowGroups(ctx, withRoles(ctx, [role]))
  : ctx.geo.groupAssemblies(withRoles(ctx, [role]), [0, 1, 2]));

/**
 * WF v8 (Generals units): what the vehicle stands on — a subject's `wheels` override `running` (kernel-chain
 * RULE_OVERRIDES): "wheels" (the class default), "tracks" (role "track" runners + road wheels) or "skids" (role "skid").
 */
const RUNNER_ROLE = Object.freeze({ tracks: "track", skids: "skid" });
export const runningOf = (ctx) => ctx.overrides?.wheels?.running ?? "wheels";
/** The runner assemblies (tracks / skids) of a non-wheeled vehicle, sorted like wheelGroups. */
export function runnerGroups(ctx) {
  const role = RUNNER_ROLE[runningOf(ctx)];
  if (!role) return [];
  return ctx.geo.groupAssemblies(withRoles(ctx, [role]), [0, 1, 2])
    .sort((a, b) => (mid(a.box, 0) - mid(b.box, 0)) || (mid(b.box, 2) - mid(a.box, 2)));
}
/** The wheel diameter band: off on a tracked vehicle's road wheels unless the subject measured one (diameterFrac). */
const wheelBand = (ctx) => (runningOf(ctx) === "wheels" || ctx.overrides?.wheels?.diameterFrac ? ctx.limits.v7?.wheel_diameter_frac_of_length : null);

// ---------------------------------------------------------------------------
// VEH_GROUND — wheels touch the ground and nothing else does.
// ---------------------------------------------------------------------------

function validateGround(ctx) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  const EPS = ctx.EPS;
  const running = runningOf(ctx);
  // WF v8: tracks / skids — the runner role stands on the ground (a tracked vehicle's road wheels may touch it too)
  const runner = RUNNER_ROLE[running] ?? null;
  const groundRoles = runner ? [runner] : (ctx.cls.groundRoles ?? ["wheel", "tyre"]);
  const mayTouch = running === "tracks" ? [runner, ...(ctx.cls.wheelRoles ?? ["wheel", "tyre", "hub"])] : groundRoles;

  for (const r of ctx.records) {
    if (mayTouch.includes(r.role) || r.aabb.min[1] > EPS) continue;
    violations.push(make("VEH_GROUND", r.id, `bottom y = ${fmt(r.aabb.min[1])} m (role ${r.role})`,
      `> ${fmt(EPS)} m — only ${mayTouch.join("/")} reach the ground`,
      `"${r.id}" (role ${r.role}) stands on the ground; only the ${runner ? `${runner}s` : "wheels"} do — lift it onto the ${runner ? "hull" : "chassis"}`));
  }

  for (const g of ctx.geo.groupAssemblies(withRoles(ctx, groundRoles), [0, 1, 2])) {
    const bottom = g.box.min[1];
    if (Math.abs(bottom) <= EPS) continue;
    violations.push(make("VEH_GROUND", g.members[0].id, `wheel bottom y = ${fmt(bottom)} m`, `0 +- ${fmt(EPS)} m`,
      `${runner ?? "wheel"} "${g.members[0].id}" ${bottom > 0 ? "floats" : "sinks"} ${fmt(Math.abs(bottom))} m — every ${runner ?? "wheel"} bottom sits on y = 0`));
  }

  // the clearance band is a road-wheel number: off under tracks / skids (the RULE_OVERRIDE row says so)
  const band = runner ? null : ctx.limits.v7?.ground_clearance;
  const chassis = withRoles(ctx, ["chassis"]);
  if (Array.isArray(band) && chassis.length > 0) {
    const clearance = Math.min(...chassis.map((r) => r.aabb.min[1]));
    if (clearance < band[0] - 1e-9 || clearance > band[1] + 1e-9) {
      const low = chassis.find((r) => r.aabb.min[1] === clearance) ?? chassis[0];
      violations.push(make("VEH_GROUND", low.id, `chassis clearance ${fmt(clearance)} m`, `${band[0]}..${band[1]} m`,
        `the chassis underside is ${fmt(clearance)} m above the ground, outside the ${band[0]}..${band[1]} m clearance band — move it`));
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// VEH_WHEELS — 4 wheels, 2 axles, one diameter, diameter/length in band.
// WF v8 (Generals units): under a `wheels` override `running: "tracks" | "skids"` it first counts the runner
// assemblies (role "track" / "skid", `runners`, default 2); count 0 then means no wheel part at all, and a tracked
// vehicle's road wheels (count / axles = wheels / stations) skip the diameter band unless diameterFrac was measured.
// limits.v7._note: the band is DIAMETER over the longer horizontal bound.
// WF v8 WP2: a subject's measured `wheels` override (kernel-chain applyRuleOverrides -> ctx.overrides.wheels) replaces
// count / axles; diameters "per-axle" compares sizes within each axle and puts each axle in the band; its diameterFrac
// already replaced the band in the effective limits (ctx.limits).
// ---------------------------------------------------------------------------

/**
 * Axles of a wheel set: the wheels' z centres split wherever consecutive centres (sorted) lie more than `eps` apart —
 * the `clusters` rule of kernel-chain.mjs, keeping which wheel sits on which axle. [{z (mean), members: [index]}], z up.
 */
export function axleClusters(zs, eps) {
  const order = zs.map((z, i) => i).sort((a, b) => zs[a] - zs[b]);
  const out = [];
  let bucket = [];
  for (const i of order) {
    if (bucket.length > 0 && zs[i] - zs[bucket[bucket.length - 1]] > eps) { out.push(bucket); bucket = []; }
    bucket.push(i);
  }
  if (bucket.length > 0) out.push(bucket);
  return out.map((members) => ({ z: members.reduce((s, i) => s + zs[i], 0) / members.length, members }));
}

/** VEH_WHEELS under a subject's `diameters: "per-axle"` override: sizes equal within each axle, each axle in the band. */
function validateWheelsPerAxle(ctx, groups, want) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  const diameters = groups.map((g) => ext(g.box, 1));
  const tol = Number.isFinite(ctx.limits.wheelDiameterTol) ? ctx.limits.wheelDiameterTol : WHEEL_DIAMETER_TOL;
  // wheels on one axle share a z centre and neighbouring axles stand at least a tyre radius apart: the SMALLEST radius
  // splits them (the whole-set mean radius the equal rule uses can exceed the spacing of a small-wheel tandem)
  const axles = axleClusters(groups.map((g) => mid(g.box, 2)), Math.min(...diameters) / 2);
  const axleD = axles.map((a) => a.members.reduce((s, i) => s + diameters[i], 0) / a.members.length);

  axles.forEach((a, k) => {
    const ds = a.members.map((i) => diameters[i]);
    const lo = Math.min(...ds);
    const hi = Math.max(...ds);
    if (hi - lo <= tol + 1e-9) return;
    // the wheel farthest from its axle's mean; a (near) tie — always the case on a two-wheel axle — names the first
    const odd = a.members.reduce((p, i) => (Math.abs(diameters[i] - axleD[k]) > Math.abs(diameters[p] - axleD[k]) + 1e-9 ? i : p), a.members[0]);
    violations.push(make("VEH_WHEELS", groups[odd].members[0].id, `diameters ${fmt(lo)}..${fmt(hi)} m on the axle at z ${fmt(a.z)}`, `equal within ${fmt(tol)} m on each axle`,
      `the wheels of one axle are the same size (subject override: diameters per axle) — "${groups[odd].members[0].id}" and the rest of its axle differ by ${fmt(hi - lo)} m`));
  });

  if (axles.length !== want.axles) {
    violations.push(make("VEH_WHEELS", groups[0].members[0].id, `${axles.length} axle position(s) along z`, `${want.axles}`,
      `wheels on one axle share a z centre; the model's wheels sit at ${axles.length} z position(s) (${axles.map((a) => fmt(a.z)).join(", ")} m)`));
  }

  const band = wheelBand(ctx);
  if (Array.isArray(band) && ctx.records.length > 0) {
    const all = ctx.geo.unionBox(ctx.records);
    const longest = Math.max(ext(all, 0), ext(all, 2));
    axles.forEach((a, k) => {
      const frac = axleD[k] / longest;
      if (frac >= band[0] - 1e-9 && frac <= band[1] + 1e-9) return;
      violations.push(make("VEH_WHEELS", groups[a.members[0]].members[0].id, `diameter/length ${fmt(frac)} on the axle at z ${fmt(a.z)}`, `${band[0]}..${band[1]}`,
        `wheel diameter ${fmt(axleD[k])} m over the ${fmt(longest)} m length is ${fmt(frac)}, outside ${band[0]}..${band[1]} — resize the wheels of the axle at z ${fmt(a.z)} m`));
    });
  }
  return { violations, advisories: [] };
}

function validateWheels(ctx) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  const over = ctx.overrides?.wheels ?? null;
  const want = over ?? ctx.cls.wheels ?? { count: 4, axles: 2 };
  const groups = wheelGroups(ctx);
  const running = runningOf(ctx);
  if (running !== "wheels") {
    // WF v8: tracks / skids — the runner assemblies first (two by default: left and right)
    const role = RUNNER_ROLE[running];
    const runners = runnerGroups(ctx);
    if (runners.length !== want.runners) {
      violations.push(make("VEH_WHEELS", runners[0]?.members[0].id ?? null, `${runners.length} ${role} assemblies`, `${want.runners}`,
        `the vehicle stands on ${want.runners} ${role}s (role "${role}") and the model has ${runners.length} — ${runners.length < want.runners ? "add" : "remove"} ${Math.abs(want.runners - runners.length)} (parts of one ${role} overlap: one assembly)`));
    }
    if (want.count === 0) {
      if (groups.length > 0) {
        violations.push(make("VEH_WHEELS", groups[0].members[0].id, `${groups.length} wheel assemblies`, "0",
          `the ${running === "skids" ? "helicopter stands on its skids" : "tracks hide the road wheels"} (subject override: no wheels) — remove the wheel parts or give them the role they build`));
      }
      return { violations, advisories: [] };
    }
    if (violations.length > 0) return { violations, advisories: [] };
  }

  if (groups.length !== want.count) {
    violations.push(make("VEH_WHEELS", groups[0]?.members[0].id ?? null, `${groups.length} wheel assemblies`, `${want.count}`,
      `the vehicle ${running === "tracks" ? "carries" : "stands on"} ${want.count} ${running === "tracks" ? "road " : ""}wheels and the model has ${groups.length} — ${groups.length < want.count ? "add" : "remove"} ${Math.abs(want.count - groups.length)} (role "wheel"; a hub or tyre touching a wheel is the same wheel)`));
    return { violations, advisories: [] };
  }
  if (over?.diameters === "per-axle") return validateWheelsPerAxle(ctx, groups, want);

  const diameters = groups.map((g) => ext(g.box, 1));
  const dMin = Math.min(...diameters);
  const dMax = Math.max(...diameters);
  const tol = Number.isFinite(ctx.limits.wheelDiameterTol) ? ctx.limits.wheelDiameterTol : WHEEL_DIAMETER_TOL;
  if (dMax - dMin > tol + 1e-9) {
    const odd = groups[diameters.indexOf(Math.abs(dMax - diameters.reduce((a, b) => a + b, 0) / diameters.length) > Math.abs(dMin - diameters.reduce((a, b) => a + b, 0) / diameters.length) ? dMax : dMin)];
    violations.push(make("VEH_WHEELS", odd.members[0].id, `diameters ${fmt(dMin)}..${fmt(dMax)} m`, `equal within ${fmt(tol)} m`,
      `every wheel is the same size — "${odd.members[0].id}" differs by ${fmt(dMax - dMin)} m`));
  }

  const mean = diameters.reduce((a, b) => a + b, 0) / diameters.length;
  const axles = ctx.geo.clusters(groups.map((g) => mid(g.box, 2)), mean / 2);
  if (axles.length !== want.axles) {
    violations.push(make("VEH_WHEELS", groups[0].members[0].id, `${axles.length} axle position(s) along z`, `${want.axles}`,
      `wheels on one axle share a z centre; the model's wheels sit at ${axles.length} z position(s) (${axles.map(fmt).join(", ")} m)`));
  }

  const band = wheelBand(ctx);
  if (Array.isArray(band) && ctx.records.length > 0) {
    const all = ctx.geo.unionBox(ctx.records);
    const longest = Math.max(ext(all, 0), ext(all, 2));
    const frac = mean / longest;
    if (frac < band[0] - 1e-9 || frac > band[1] + 1e-9) {
      violations.push(make("VEH_WHEELS", groups[0].members[0].id, `diameter/length ${fmt(frac)}`, `${band[0]}..${band[1]}`,
        `wheel diameter ${fmt(mean)} m over the ${fmt(longest)} m length is ${fmt(frac)}, outside ${band[0]}..${band[1]} — resize the wheels`));
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// VEH_MIRROR — limits.v9 roles come in pairs mirrored across the body's centre
// plane (x = middle of the lengthRoles box).
// ---------------------------------------------------------------------------

function validateMirror(ctx) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  if (!(ctx.limits.symmetricClasses ?? []).includes(ctx.cls.class)) return { violations, advisories: [] };
  const box = coreBox(ctx);
  if (!box) return { violations, advisories: [] };
  const xc = mid(box, 0);
  const tol = Number.isFinite(ctx.limits.mirrorTol) ? ctx.limits.mirrorTol : MIRROR_TOL;
  const roles = (ctx.limits.v9?.roles ?? []).filter((role) => (ctx.cls.roles ?? []).includes(role));
  // WF v8 WP2: a subject's `mirror` override (ruleOverrides.mirror.centred) exempts matching single-track parts
  // (a motorbike's one front tyre, one rear tyre, one headlight) from the mirrored-pair requirement below — the
  // part/role must still sit on the centreline, so the exemption is pairing-only, never a free pass.
  const centredPatterns = (ctx.overrides?.mirror?.centred ?? []).map((p) => new RegExp(p));
  const isCentredExempt = (role, g) => centredPatterns.some((re) => re.test(role) || g.members.some((m) => re.test(m.id)));

  for (const role of roles) {
    const groups = groupsOf(ctx, role);
    for (const g of groups) {
      if (isCentredExempt(role, g)) {
        const gxc = mid(g.box, 0);
        if (Math.abs(gxc - xc) <= tol + 1e-9) continue;        // centred single part: pairing exempt, but on the plane
        violations.push(make("VEH_MIRROR", g.members[0].id,
          `x centre ${fmt(gxc)} m`, `centreline x = ${fmt(xc)} m +/- ${fmt(tol)} m`,
          `"${g.members[0].id}" (role ${role}) is a centred part off the centreline — ruleOverrides.mirror exempts it from pairing, not from sitting on x = ${fmt(xc)} (off by ${fmt(Math.abs(gxc - xc))} m)`));
        break;                                                 // one line per role
      }
      const mirrored = { min: 2 * xc - g.box.max[0], max: 2 * xc - g.box.min[0] };
      const same = (h) => Math.abs(h.box.min[0] - mirrored.min) <= tol && Math.abs(h.box.max[0] - mirrored.max) <= tol
        && [1, 2].every((a) => Math.abs(h.box.min[a] - g.box.min[a]) <= tol && Math.abs(h.box.max[a] - g.box.max[a]) <= tol);
      if (same(g)) continue;                                   // straddles the plane symmetrically
      if (groups.some((h) => h !== g && same(h))) continue;
      violations.push(make("VEH_MIRROR", g.members[0].id,
        `no ${role} at x ${fmt(mirrored.min)}..${fmt(mirrored.max)}, y ${fmt(g.box.min[1])}..${fmt(g.box.max[1])}, z ${fmt(g.box.min[2])}..${fmt(g.box.max[2])}`,
        `a mirrored partner within ${fmt(tol)} m`,
        `"${g.members[0].id}" (role ${role}) has no partner mirrored across the centre plane x = ${fmt(xc)} — place its pair at the negated x, same y and z`));
      break;                                                   // one line per role
    }
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// VEH_HANDBUILT — WF-R3 R3-B item 2. ADVISORY: detail parts (window, headlight, grille, mirror) not built by
// K.assemble.pane / lamp / grille / mirror. The helpers seat on the host face they find, so they pass V3/V5/V6 and the
// V12 rows by construction; hand-placed details are where the blind runs lost their panes and mirror heads.
// ---------------------------------------------------------------------------

export const HELPER_ROLES = Object.freeze({ window: "pane", headlight: "lamp", grille: "grille", mirror: "mirror" });

function validateHandbuilt(ctx) {
  const hand = ctx.records.filter((r) => HELPER_ROLES[r.role] && !r.part?.assembly?.helper);
  if (hand.length === 0) return { violations: [], advisories: [] };
  const helpers = [...new Set(hand.map((r) => HELPER_ROLES[r.role]))].map((h) => `K.assemble.${h}`).join(" / ");
  return {
    violations: [],
    advisories: [{ v: "VEH_HANDBUILT", part: hand[0].id, measured: `${hand.length} detail part(s) not built by K.assemble`, limit: helpers,
      hint: "panes, lamps, grilles and mirrors built with the K.assemble vehicle helpers sit on their host face by construction; hand-placed ones are where panes float out of the cab and mirror heads come off their arms", blocking: false }],
  };
}

// ---------------------------------------------------------------------------
// V5-9 EVIDENCE HIERARCHY (orchestrator ruling) — the per-feature accuracy measurement (scripts/accuracy.mjs, full
// resolution, per inventory item) outranks the older V12 layout keys (measured earlier, at lower resolution). Every
// layout key whose feature the accuracy report covers (all measured keys except COUNTS) is ADVISORY in the FIT / LOOP
// gate: advisoryLayout() moves it off the enforced layout into `_advisory`, and VEH_LAYOUT_ADVISORY reports a miss as
// a non-blocking row. Counts (window.front.panes, window.row.count, grille.slots) stay enforced by V12_LAYOUT.
// ---------------------------------------------------------------------------

/** Is this layout key advisory under the evidence hierarchy (a measured, non-count V12 key)? */
export const isAdvisoryKey = (key) => Boolean(RULES[key]) && KIND[key] !== "count";

/** The layout the FIT / LOOP gate enforces: advisory keys moved to `_advisory` (reported, never blocking). */
export function advisoryLayout(layout) {
  if (!layout || typeof layout !== "object") return layout;
  const out = {};
  const adv = {};
  for (const [k, e] of Object.entries(layout)) {
    if (isAdvisoryKey(k) && e && typeof e === "object" && e.unverified !== true) adv[k] = e;
    else out[k] = e;
  }
  return Object.keys(adv).length ? { ...out, _advisory: adv } : layout;
}

function validateLayoutAdvisory(ctx) {
  const adv = ctx.layout?._advisory;
  if (!adv) return { violations: [], advisories: [] };
  const F = layoutFrame(ctx);
  if (!F) return { violations: [], advisories: [] };
  const advisories = [];
  for (const [key, entry] of Object.entries(adv)) {
    const rule = layoutRules[key];
    if (!rule || rule.roles.some((role) => !ctx.records.some((r) => r.role === role))) continue;
    const got = rule.measure(ctx, F).map((m) => m.measured).sort((a, b) => a - b);
    const want = Array.isArray(entry.values) ? [...entry.values].sort((a, b) => a - b) : [entry.value];
    const tol = Number.isFinite(entry.tol) ? entry.tol : 0.05;
    const off = got.findIndex((g, i) => Number.isFinite(want[Math.min(i, want.length - 1)]) && Math.abs(g - want[Math.min(i, want.length - 1)]) > tol + 1e-9);
    if (off < 0) continue;
    advisories.push({ v: "VEH_LAYOUT_ADVISORY", part: null, measured: `${key} ${Math.round(got[off] * 1e4) / 1e4}`, limit: `${want[Math.min(off, want.length - 1)]} +/- ${tol}`,
      hint: "V5-9: the accuracy report gates this feature; the older layout key is advisory", blocking: false });
  }
  return { violations: [], advisories };
}

export const validators = Object.freeze([
  ["VEH_GROUND", validateGround],
  ["VEH_WHEELS", validateWheels],
  ["VEH_MIRROR", validateMirror],
  ["VEH_HANDBUILT", validateHandbuilt],
  ["VEH_LAYOUT_ADVISORY", validateLayoutAdvisory],
]);

// ---------------------------------------------------------------------------
// V12_LAYOUT — the frame and the measures for the keys scripts/measure-vehicle.mjs
// writes. Fractions along L are taken from the NOSE (the body's max z).
// ---------------------------------------------------------------------------

// WF-BLIND-R2 C3 — the start module's planes and every cited layout key in author-frame METRES.
const m3 = (v) => `${v >= 0 ? "+" : ""}${(Math.round(v * 1000) / 1000).toFixed(3)}`;

/** One line: the body's planes (null before P0 builds a body). */
export function layoutPlanes(ctx, F) {
  if (!F) return null;
  return `nose z = ${m3(F.zFront)} (max z), tail z = ${m3(F.zRear)}, centre plane x = ${m3(F.xc)}, `
    + `flanks x = ${m3(F.xc - F.W / 2)} / ${m3(F.xc + F.W / 2)}, ground y = +0.000, top y = ${m3(F.H)}; `
    + `L = ${m3(F.L)} m, W = ${m3(F.W)} m, H = ${m3(F.H)} m`;
}

/** A layout entry's value(s) as author-frame metres, or null for a unit that has none. */
export function layoutAbsolute(key, entry, F) {
  if (!F || !entry || entry.unverified) return null;
  const inv = layoutRules[key]?.inverse;
  if (inv) {
    const vs = Array.isArray(entry.values) ? entry.values : (Number.isFinite(entry.value) ? [entry.value] : null);
    if (!vs) return null;
    return `${inv.axis === "size" ? "" : `${inv.axis} = `}${vs.map((v) => m3(inv(v, F))).join(" / ")} m`;
  }
  const values = Array.isArray(entry.values) ? entry.values : (Number.isFinite(entry.value) ? [entry.value] : null);
  if (!values) return null;
  const list = (fn) => values.map(fn).join(" / ");
  const unit = entry.unit ?? "";
  if (unit === "L") return `z = ${list((v) => m3(F.zFront - v * F.L))} m (nose z - value x L)`;
  if (unit === "x L") return `${list((v) => m3(v * F.L))} m`;
  if (unit === "W") {
    if (/offsetX$/.test(key)) {
      return Array.isArray(entry.values)
        ? `x = ${list((v) => m3(F.xc + v * F.W))} m (centre plane + value x W)`
        : `x = ${m3(F.xc - values[0] * F.W)} and ${m3(F.xc + values[0] * F.W)} m (centre plane +- value x W)`;
    }
    return `${list((v) => m3(v * F.W))} m`;
  }
  if (unit === "H") {
    if (/(centreY|bottom|top|roof)$/.test(key)) return `y = ${list((v) => m3(v * F.H))} m (ground + value x H)`;
    return `${list((v) => m3(v * F.H))} m`;
  }
  return null;
}

export function layoutFrame(ctx) {
  const box = withRoles(ctx, lengthRoles(ctx)).length > 0 ? coreBox(ctx) : null;
  if (!box) return null;
  const L = ext(box, 2);
  const W = ext(box, 0);
  // WF-R3 R3-B item 3 — H is the BODY's height (the lengthRoles box): a mirror or a pane standing above the roof
  // cannot shift H, and with it every height the prompt printed.
  const H = box.max[1];
  if (!(L > 0) || !(W > 0) || !(H > 0)) return null;
  return { L, W, H, zFront: box.max[2], zRear: box.min[2], xc: mid(box, 0) };
}

// V5-3: an inlay (seam, handle, band / frame) is not the body's extent: a frame proud of a raked face moved cab.start
const union = (ctx, roles) => { const rs = withRoles(ctx, roles); const core = rs.filter((r) => !INLAY_HELPERS.includes(r.part?.assembly?.helper)); return ctx.geo.unionBox(core.length ? core : rs); };
const axleZs = (ctx) => {
  const groups = wheelGroups(ctx);
  if (groups.length === 0) return [];
  const mean = groups.reduce((s, g) => s + ext(g.box, 1), 0) / groups.length;
  return ctx.geo.clusters(groups.map((g) => mid(g.box, 2)), mean / 2);
};
/** Bumper assemblies, nose first. */
const bumpers = (ctx) => groupsOf(ctx, "bumper").sort((a, b) => mid(b.box, 2) - mid(a.box, 2));
const BED = ["bed", "bed_wall", "tailgate"];

const RULES = {
  "wheel.diameterOverL": {
    roles: ["wheel"], unit: "L",
    measure: (ctx, F) => wheelGroups(ctx).map((g) => ({ id: g.members[0].id, measured: ext(g.box, 1) / F.L })),
  },
  "wheel.centreFromFront": {
    roles: ["wheel"], unit: "L", list: "axle positions",
    measure: (ctx, F) => axleZs(ctx).map((z) => ({ id: null, measured: (F.zFront - z) / F.L })),
  },
  "wheelbase.overL": {
    roles: ["wheel"], unit: "L",
    measure: (ctx, F) => {
      const zs = axleZs(ctx);
      return zs.length < 2 ? [] : [{ id: null, measured: (Math.max(...zs) - Math.min(...zs)) / F.L }];
    },
  },
  "height.overL": { roles: ["cab"], unit: "x L", measure: (ctx, F) => [{ id: null, measured: F.H / F.L }] },
  "width.overL": { roles: ["cab"], unit: "x L", measure: (ctx, F) => [{ id: null, measured: F.W / F.L }] },
  "cab.start": { roles: ["cab"], unit: "L", measure: (ctx, F) => [{ id: null, measured: (F.zFront - union(ctx, ["cab"]).max[2]) / F.L }] },
  "cab.end": { roles: ["cab"], unit: "L", measure: (ctx, F) => [{ id: null, measured: (F.zFront - union(ctx, ["cab"]).min[2]) / F.L }] },
  "bed.start": { roles: ["bed"], unit: "L", measure: (ctx, F) => [{ id: null, measured: (F.zFront - union(ctx, BED).max[2]) / F.L }] },
  "bed.end": { roles: ["bed"], unit: "L", measure: (ctx, F) => [{ id: null, measured: (F.zFront - union(ctx, BED).min[2]) / F.L }] },
  "hood.top": { roles: ["hood"], unit: "H", measure: (ctx, F) => [{ id: null, measured: union(ctx, ["hood"]).max[1] / F.H }] },
  "cab.roof": { roles: ["cab"], unit: "H", measure: (ctx, F) => [{ id: null, measured: union(ctx, ["cab"]).max[1] / F.H }] },
  "bedWall.top": { roles: ["bed_wall"], unit: "H", measure: (ctx, F) => [{ id: null, measured: union(ctx, ["bed_wall"]).max[1] / F.H }] },
  "bumper.front.top": {
    roles: ["bumper"], unit: "H",
    measure: (ctx, F) => { const b = bumpers(ctx)[0]; return [{ id: b.members[0].id, measured: b.box.max[1] / F.H }]; },
  },
  "bumper.front.h": {
    roles: ["bumper"], unit: "H",
    measure: (ctx, F) => { const b = bumpers(ctx)[0]; return [{ id: b.members[0].id, measured: ext(b.box, 1) / F.H }]; },
  },
  "bumper.rear.top": {
    roles: ["bumper"], unit: "H",
    measure: (ctx, F) => { const all = bumpers(ctx); if (all.length < 2) return []; const b = all[all.length - 1]; return [{ id: b.members[0].id, measured: b.box.max[1] / F.H }]; },
  },
  "bumper.rear.h": {
    roles: ["bumper"], unit: "H",
    measure: (ctx, F) => { const all = bumpers(ctx); if (all.length < 2) return []; const b = all[all.length - 1]; return [{ id: b.members[0].id, measured: ext(b.box, 1) / F.H }]; },
  },
  "headlight.centreY": {
    roles: ["headlight"], unit: "H",
    measure: (ctx, F) => groupsOf(ctx, "headlight").map((g) => ({ id: g.members[0].id, measured: mid(g.box, 1) / F.H })),
  },
  "headlight.offsetX": {
    roles: ["headlight"], unit: "W", list: "headlight centres",
    measure: (ctx, F) => groupsOf(ctx, "headlight").map((g) => ({ id: g.members[0].id, measured: (mid(g.box, 0) - F.xc) / F.W })),
  },
  "mirror.centreY": {
    roles: ["mirror"], unit: "H",
    measure: (ctx, F) => groupsOf(ctx, "mirror").map((g) => ({ id: g.members[0].id, measured: mid(g.box, 1) / F.H })),
  },
  "chassis.clearance": {
    roles: ["chassis"], unit: "H",
    measure: (ctx, F) => [{ id: null, measured: Math.min(...withRoles(ctx, ["chassis"]).map((r) => r.aabb.min[1])) / F.H }],
  },

  // -------------------------------------------------------------------------
  // APPEARANCE keys (measure-vehicle.mjs, blind-r1 B2). Every number the author
  // prompt carries is gated here, measured the way the scan defined it.
  // -------------------------------------------------------------------------

  // Headlight: the scan takes the LAMP px (equal-area disc) on the nose plane, so
  // the lens is the member painted "lamp" (a bezel in another zone is not the
  // disc); no lamp-zone member = the whole headlight group. Disc diameter from an
  // AABB = sqrt(x extent * y extent) (exact for a disc facing +Z).
  "headlight.diameter": {
    roles: ["headlight"], unit: "W",
    measure: (ctx, F) => groupsOf(ctx, "headlight").map((g) => {
      const { id, box } = zonedBox(ctx, g.members, "lamp");
      return { id, measured: Math.sqrt(ext(box, 0) * ext(box, 1)) / F.W };
    }),
  },
  // Grille: the scan takes the SLOT FIELD, not the ink frame. On AABBs the slot
  // field is the grille-role members painted "grille"; none = every grille part.
  // A frame the author paints "body"/"bumper" under role grille is excluded.
  "grille.w": {
    roles: ["grille"], unit: "W",
    measure: (ctx, F) => { const { id, box } = zonedBox(ctx, withRoles(ctx, ["grille"]), "grille"); return [{ id, measured: ext(box, 0) / F.W }]; },
  },
  // WF-BLIND-R2 C12 — the item asks for RECESSED slots; a solid grille panel used to pass. Slots are counted as the
  // connected lumps of the cut tools applied to grille-role parts (K.cut records them), or, for a grille built from
  // separate horizontal slats, the gaps between them.
  // MVP-STUB: a cut tool that only trims the panel's outline still counts as a slot.
  "grille.slots": {
    roles: ["grille"], unit: "count",
    measure: (ctx) => {
      const parts = withRoles(ctx, ["grille"]);
      const cuts = parts.reduce((n, r) => n + (typeof r.part.solid.cutTools === "function"
        ? r.part.solid.cutTools().reduce((s, t) => s + t.lumps, 0) : 0), 0);
      const slats = parts.filter((r) => ext(r.aabb, 0) > 2 * ext(r.aabb, 1)).length;
      return [{ id: parts[0].id, measured: Math.max(cuts, slats >= 2 ? slats - 1 : 0) }];
    },
  },
  "grille.h": {
    roles: ["grille"], unit: "H",
    measure: (ctx, F) => { const { id, box } = zonedBox(ctx, withRoles(ctx, ["grille"]), "grille"); return [{ id, measured: ext(box, 1) / F.H }]; },
  },
  // Mirror: the HEAD is the group member with the largest y extent (the arm is a
  // thin bar along X). A mirror built as ONE part (head unioned with its arm)
  // cannot be split on an AABB: its box is head + arm, so head.w reads wide and
  // arm.length reads ~0 — build head and arm as separate parts. Every mirror
  // group is measured (the scan measured the near head; the pair is mirrored).
  "mirror.head.w": {
    roles: ["mirror"], unit: "W",
    measure: (ctx, F) => groupsOf(ctx, "mirror").map((g) => { const h = headOf(g); return { id: h.id, measured: ext(h.aabb, 0) / F.W }; }),
  },
  "mirror.head.h": {
    roles: ["mirror"], unit: "H",
    measure: (ctx, F) => groupsOf(ctx, "mirror").map((g) => { const h = headOf(g); return { id: h.id, measured: ext(h.aabb, 1) / F.H }; }),
  },
  "mirror.offsetX": {
    roles: ["mirror"], unit: "W", list: "mirror head centres",
    measure: (ctx, F) => groupsOf(ctx, "mirror").map((g) => { const h = headOf(g); return { id: h.id, measured: (mid(h.aabb, 0) - F.xc) / F.W }; }),
  },
  // The scan's reach: |head centre| - W/2 - head w/2 = the head's inner edge off the flank plane.
  "mirror.arm.length": {
    roles: ["mirror"], unit: "W",
    measure: (ctx, F) => groupsOf(ctx, "mirror").map((g) => {
      const h = headOf(g);
      return { id: h.id, measured: (Math.abs(mid(h.aabb, 0) - F.xc) - F.W / 2 - ext(h.aabb, 0) / 2) / F.W };
    }),
  },
  // Windshield: the window group straddling the centre plane with the most
  // forward z; the PANE is its "glass" member(s), else its member with the
  // smallest x extent (a frame surrounds the pane). The scan measured the lower
  // edge (an X edge) and its height above the ground.
  "window.front.w": {
    roles: ["window"], unit: "W",
    measure: (ctx, F) => { const p = windshieldPane(ctx, F); return p ? [{ id: p.id, measured: ext(p.box, 0) / F.W }] : []; },
  },
  "window.front.bottom": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => { const p = windshieldPane(ctx, F); return p ? [{ id: p.id, measured: p.box.min[1] / F.H }] : []; },
  },
  // layout.json marks this UNVERIFIED (the rake): V12_LAYOUT reports it and never calls this.
  "window.front.top": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => { const p = windshieldPane(ctx, F); return p ? [{ id: p.id, measured: p.box.max[1] / F.H }] : []; },
  },
  // WF-R3 R3-B item 5 — the rake: the windshield pane's top edge z (its min z), from the nose.
  "window.front.topAt": {
    roles: ["window"], unit: "L",
    measure: (ctx, F) => { const p = windshieldPane(ctx, F); return p ? [{ id: p.id, measured: (F.zFront - p.box.min[2]) / F.L }] : []; },
  },
  // Side window: every window group wholly on the +X (camera) flank; the PANE is
  // its "glass" member(s), else the member with the smallest z extent. Fractions
  // along L from the nose, heights over H from the ground — as the scan rectified them.
  "window.side.start": {
    roles: ["window"], unit: "L",
    measure: (ctx, F) => nearSidePanes(ctx, F).map((p) => ({ id: p.id, measured: (F.zFront - p.box.max[2]) / F.L })),
  },
  "window.side.end": {
    roles: ["window"], unit: "L",
    measure: (ctx, F) => nearSidePanes(ctx, F).map((p) => ({ id: p.id, measured: (F.zFront - p.box.min[2]) / F.L })),
  },
  "window.side.bottom": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => nearSidePanes(ctx, F).map((p) => ({ id: p.id, measured: p.box.min[1] / F.H })),
  },
  "window.side.top": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => nearSidePanes(ctx, F).map((p) => ({ id: p.id, measured: p.box.max[1] / F.H })),
  },

  // -------------------------------------------------------------------------
  // V4-7 BUS variant keys (scripts/measure-vehicle.mjs measureBus). A row pane is a window group wholly on the +X
  // flank that is thinner across x than along z (a nose pane is the other way round); the band is the windowRow
  // helper's inlay (assembly helper "band") on the +X flank; the stop sign the stopArm helper's sign.
  // -------------------------------------------------------------------------
  "window.front.panes": {
    roles: ["window"], unit: "count",
    measure: (ctx, F) => { const n = nosePanes(ctx, F); return n.length ? [{ id: n[0].id, measured: n.length }] : []; },
  },
  "window.row.count": {
    roles: ["window"], unit: "count",
    measure: (ctx, F) => { const r = rowPanes(ctx, F); return r.length ? [{ id: r[0].id, measured: r.length }] : []; },
  },
  "window.row.start": {
    roles: ["window"], unit: "L",
    measure: (ctx, F) => { const r = rowPanes(ctx, F); return r.length ? [{ id: r[0].id, measured: (F.zFront - r[0].box.max[2]) / F.L }] : []; },
  },
  "window.row.end": {
    roles: ["window"], unit: "L",
    measure: (ctx, F) => { const r = rowPanes(ctx, F); return r.length ? [{ id: r[r.length - 1].id, measured: (F.zFront - r[r.length - 1].box.min[2]) / F.L }] : []; },
  },
  "window.row.bottom": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => rowPanes(ctx, F).map((p) => ({ id: p.id, measured: p.box.min[1] / F.H })),
  },
  "window.row.top": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => rowPanes(ctx, F).map((p) => ({ id: p.id, measured: p.box.max[1] / F.H })),
  },
  "window.band.bottom": {
    roles: ["cab"], unit: "H",
    measure: (ctx, F) => bandParts(ctx, F).map((r) => ({ id: r.id, measured: r.aabb.min[1] / F.H })),
  },
  "window.band.top": {
    roles: ["cab"], unit: "H",
    measure: (ctx, F) => bandParts(ctx, F).map((r) => ({ id: r.id, measured: r.aabb.max[1] / F.H })),
  },
  "stopArm.centreAt": {
    roles: ["prop"], unit: "L",
    measure: (ctx, F) => stopSigns(ctx).map((r) => ({ id: r.id, measured: (F.zFront - mid(r.aabb, 2)) / F.L })),
  },
  "stopArm.centreY": {
    roles: ["prop"], unit: "H",
    measure: (ctx, F) => stopSigns(ctx).map((r) => ({ id: r.id, measured: mid(r.aabb, 1) / F.H })),
  },
};

/** V4-7 — the bus's nose panes (window groups wider across x than along z, at the nose) and row panes (+X flank). */
function nosePanes(ctx, F) {
  return groupsOf(ctx, "window").filter((g) => ext(g.box, 0) > ext(g.box, 2) && g.box.max[2] > F.zFront - 0.1 * F.L)
    .map((g) => paneOf(ctx, g, 2)).sort((a, b) => a.box.min[0] - b.box.min[0]);
}
function rowPanes(ctx, F) {
  return groupsOf(ctx, "window").filter((g) => g.box.min[0] > F.xc && ext(g.box, 0) < ext(g.box, 2))
    .sort((a, b) => b.box.max[2] - a.box.max[2]).map((g) => paneOf(ctx, g, 0));
}
const bandParts = (ctx, F) => ctx.records.filter((r) => r.part?.assembly?.helper === "band" && r.aabb.min[0] > F.xc);
const stopSigns = (ctx) => ctx.records.filter((r) => r.part?.assembly?.helper === "stopArm" && r.zone === "signal");


// ---------------------------------------------------------------------------
// WF-R3 R3-B item 3 — every rule's INVERSE: a layout value -> author-frame metres (a z / x / y coordinate or a
// size), so the harness prints ready K.span / helper arguments and never asks the author to convert a fraction.
// `extent` (same unit as the key) caps a POSITION key's tol at 0.25 x the feature's own extent: a pane off by
// more than a quarter of its width is in the wrong place however loose the scan tolerance is.
// ---------------------------------------------------------------------------

const inv = (axis, fn) => Object.assign(fn, { axis });
const INVERSE = {
  z: inv("z", (v, F) => F.zFront - v * F.L),
  x: inv("x", (v, F) => F.xc + v * F.W),
  y: inv("y", (v, F) => v * F.H),
  L: inv("size", (v, F) => v * F.L),
  W: inv("size", (v, F) => v * F.W),
  H: inv("size", (v, F) => v * F.H),
  count: inv("count", (v) => v),
};
const KIND = {
  "wheel.diameterOverL": "L", "wheel.centreFromFront": "z", "wheelbase.overL": "L", "height.overL": "L", "width.overL": "L",
  "cab.start": "z", "cab.end": "z", "bed.start": "z", "bed.end": "z", "hood.top": "y", "cab.roof": "y", "bedWall.top": "y",
  "bumper.front.top": "y", "bumper.front.h": "H", "bumper.rear.top": "y", "bumper.rear.h": "H", "chassis.clearance": "y",
  "headlight.centreY": "y", "headlight.offsetX": "x", "headlight.diameter": "W", "grille.w": "W", "grille.h": "H", "grille.slots": "count",
  "mirror.centreY": "y", "mirror.offsetX": "x", "mirror.head.w": "W", "mirror.head.h": "H", "mirror.arm.length": "W",
  "window.front.w": "W", "window.front.bottom": "y", "window.front.top": "y", "window.front.topAt": "z",
  "window.side.start": "z", "window.side.end": "z", "window.side.bottom": "y", "window.side.top": "y",
  // V4-7 bus variant
  "window.front.panes": "count", "window.front.post": "W", "window.row.count": "count", "window.row.start": "z", "window.row.end": "z",
  "window.row.pitch": "L", "window.row.paneW": "L", "window.row.bottom": "y", "window.row.top": "y",
  "window.band.bottom": "y", "window.band.top": "y", "stopArm.centreAt": "z", "stopArm.centreY": "y", "stopArm.diameter": "L",
};
const val = (layout, k) => (layout?.[k] && !layout[k].unverified && Number.isFinite(layout[k].value) ? layout[k].value : null);
const pairExtent = (a, b) => (layout) => { const p = val(layout, a); const q = val(layout, b); return p !== null && q !== null ? Math.abs(q - p) : null; };
const EXTENT = {
  "window.side.start": pairExtent("window.side.start", "window.side.end"),
  "window.side.end": pairExtent("window.side.start", "window.side.end"),
  "window.side.bottom": pairExtent("window.side.bottom", "window.side.top"),
  "window.side.top": pairExtent("window.side.bottom", "window.side.top"),
  "window.front.bottom": pairExtent("window.front.bottom", "window.front.top"),
  "window.front.top": pairExtent("window.front.bottom", "window.front.top"),
  "headlight.offsetX": (layout) => val(layout, "headlight.diameter"),
  "headlight.centreY": (layout, F) => (val(layout, "headlight.diameter") !== null && F ? val(layout, "headlight.diameter") * F.W / F.H : null),
  "mirror.offsetX": (layout) => val(layout, "mirror.head.w"),
  "mirror.centreY": (layout) => val(layout, "mirror.head.h"),
};
export const POSITION_TOL_SHARE = 0.25;
export const layoutRules = Object.freeze(Object.fromEntries(Object.entries(RULES).map(([k, r]) => [k, Object.freeze({
  ...r, inverse: INVERSE[KIND[k]], ...(EXTENT[k] ? { extent: EXTENT[k] } : {}),
})])));

/**
 * WF-R3 R3-B item 3 — the P1 detail calls, READY: every argument is a cited key through its inverse, off the start
 * module's frame F. A call is printed only when every key it reads is cited and measured. `minFeat` places the mirror
 * one head depth ahead of the side window's front edge (the A-pillar; no key measures the mirror's z).
 */
export function readyCalls(layout, F, { cited = null, minFeat = 0.04 } = {}) {
  if (!F || !layout) return [];
  if (layout._profile?.variant === "bus") return busReadyCalls(layout, F, { cited, minFeat });
  const has = (...ks) => ks.every((k) => (!cited || cited.includes(k)) && layout[k] && !layout[k].unverified);
  const v = (k) => layout[k].value;
  const I = (k, x) => layoutRules[k].inverse(x ?? v(k), F);
  const n = (x) => m3(x).replace(/^\+/, "");
  const sp = (o) => `K.span({ ${Object.entries(o).map(([a, [p, q]]) => `${a}: [${n(p)}, ${n(q)}]`).join(", ")} })`;
  const out = [];
  // WF-R5 R5-A — profile keys (layout._profile.keys, scripts/measure-profile.mjs): measured, not V12-gated, never cited.
  const PK = layout._profile?.keys ?? {};
  const pv = (k) => (PK[k] && !PK[k].unverified && Number.isFinite(PK[k].value) ? PK[k].value : null);
  const poly = (pts) => `[${pts.map(([a, b]) => `[${n(a)}, ${n(b)}]`).join(", ")}]`;
  // the A-pillar rake, dz per dy (0 when unmeasured): the side glass and the door's front edge follow it
  const known = (...ks) => ks.every((k) => layout[k] && !layout[k].unverified);   // measured, cited or not (P0 keys)
  const rake = known("cab.start", "window.front.topAt", "window.front.bottom", "window.front.top")
    ? (I("cab.start") - I("window.front.topAt")) / (I("window.front.top") - I("window.front.bottom")) : 0;
  if (has("window.front.w", "window.front.bottom", "window.front.top")) {
    const w = I("window.front.w") / 2;
    const wt = pv("window.front.wTop") !== null ? pv("window.front.wTop") * F.W / 2 : w;
    const [y0, y1] = [I("window.front.bottom"), I("window.front.top")];
    out.push({ what: "windshield (follows the rake, tapers to its measured top width)", keys: ["window.front.w", "window.front.bottom", "window.front.top", ...(has("window.front.topAt") ? ["window.front.topAt"] : [])],
      call: `parts.push(...K.assemble.pane({ host: cab, face: "+z", poly: ${poly([[F.xc - w, y0], [F.xc + w, y0], [F.xc + wt, y1], [F.xc - wt, y1]])}, ${pv("window.front.frame") !== null ? `frame: { w: ${n(Math.max(0.01, pv("window.front.frame") * F.H))} }, ` : ""}body: parts, idPrefix: "windshield" }));` });
    if (pv("window.front.frame") !== null) out[out.length - 1].keys.push("_profile window.front.frame");
  }
  if (has("window.side.start", "window.side.end", "window.side.bottom", "window.side.top")) {
    const [zs, ze, y0, y1] = [I("window.side.start"), I("window.side.end"), I("window.side.bottom"), I("window.side.top")];
    out.push({ what: "side windows (one per door, front edge on the A-pillar rake)", keys: ["window.side.start", "window.side.end", "window.side.bottom", "window.side.top"],
      call: `for (const face of ["+x", "-x"]) parts.push(...K.assemble.pane({ host: cab, face, poly: ${poly([[ze, y0], [zs, y0], [zs - rake * (y1 - y0), y1], [ze, y1]])}, body: parts, idPrefix: \`side_\${face[0] === "+" ? "l" : "r"}\` }));` });
  }
  if (["handle.centreAt", "handle.centreY", "handle.length", "handle.h"].every((k) => pv(k) !== null)) {
    const zc = F.zFront - pv("handle.centreAt") * F.L;
    const yc = pv("handle.centreY") * F.H;
    const hl = Math.max(pv("handle.length") * F.L, minFeat) / 2;
    const hh = Math.max(pv("handle.h") * F.H, minFeat) / 2;
    out.push({ what: "door handles (inlays, both flanks)", keys: ["_profile handle.*"],
      call: `for (const face of ["+x", "-x"]) parts.push(...K.assemble.handle({ host: cab, face, bounds: ${sp({ z: [zc - hl, zc + hl], y: [yc - hh, yc + hh] })}, idPrefix: \`handle_\${face[0] === "+" ? "l" : "r"}\` }));` });
  }
  if (["door.start", "door.end", "door.bottom", "door.top"].every((k) => pv(k) !== null) && known("cab.start", "cab.end", "window.side.bottom")) {
    // V4-5A: the door outline is RELATIVE to the cab (insets from its front / rear edge; the helper clamps every value
    // inside the host face), so it follows the FITTED cab — an absolute path left the cab when FIT moved cab.end.
    const z = (u) => F.zFront - u * F.L;
    const front = Math.max(0.05, I("cab.start") - z(pv("door.start")));
    const rear = Math.max(0.03, z(pv("door.end")) - I("cab.end"));
    const [yb, yk, yt] = [pv("door.bottom") * F.H, I("window.side.bottom"), pv("door.top") * F.H];
    out.push({ what: "door seams (inlay lines, both flanks, relative to the cab)", keys: ["_profile door.*"],
      call: `for (const face of ["+x", "-x"]) parts.push(...K.assemble.seam({ host: cab, face, body: parts, door: { front: ${n(front)}, rear: ${n(rear)}, bottom: ${n(yb)}, knee: ${n(yk)}, top: ${n(yt)}, rake: ${n(rake)} }, idPrefix: \`door_\${face[0] === "+" ? "l" : "r"}\` }));` });
  }
  if (has("headlight.offsetX", "headlight.centreY", "headlight.diameter")) {
    const xs = Array.isArray(layout["headlight.offsetX"].values) ? layout["headlight.offsetX"].values : [v("headlight.offsetX")];
    out.push({ what: "headlights (the pair)", keys: ["headlight.offsetX", "headlight.centreY", "headlight.diameter"],
      call: `parts.push(...K.assemble.lamp({ body: parts, face: "nose", centre: [${n(I("headlight.offsetX", Math.max(...xs)))}, ${n(I("headlight.centreY"))}], diameter: ${n(I("headlight.diameter"))}, flush: true }));` });
  }
  if (has("grille.w", "grille.h", "grille.slots", "headlight.centreY")) {
    const w = I("grille.w") / 2;
    const h = I("grille.h") / 2;
    const cy = I("headlight.centreY");
    // V5-3: the slat between slots from the measured slot height (grille.slotH), else MIN_FEAT
    const bar = known("grille.slotH") && v("grille.slots") > 1 ? (2 * h - v("grille.slots") * v("grille.slotH") * F.H) / (v("grille.slots") - 1) : null;
    out.push({ what: "grille (centred on the lamp line)", keys: ["grille.w", "grille.h", "grille.slots", ...(bar !== null ? ["grille.slotH"] : [])],
      call: `parts.push(...K.assemble.grille({ body: parts, face: "nose", bounds: ${sp({ x: [F.xc - w, F.xc + w], y: [cy - h, cy + h] })}, slots: ${v("grille.slots")}${bar !== null && bar > minFeat ? `, bar: ${n(bar)}` : ""} }));` });
  }
  if (has("mirror.centreY", "mirror.head.w", "mirror.head.h", "mirror.arm.length", "window.side.start")) {
    // V5-3: the heads' measured z (mirror.at), else one head depth behind the side window's front edge (the A-pillar)
    const z = known("mirror.at") ? F.zFront - v("mirror.at") * F.L : I("window.side.start") + minFeat;
    const [hw, hh] = [I("mirror.head.w"), I("mirror.head.h")];
    const round = DETAIL_PRIORS.mirrorRound * Math.min(hw, hh);
    // MVP-STUB: the raked arm's root (DETAIL_PRIORS.mirrorArm x head h below / ahead of the head centre): no key measures it
    const from = [I("mirror.centreY") - DETAIL_PRIORS.mirrorArm.down * hh, z + DETAIL_PRIORS.mirrorArm.ahead * hh];
    out.push({ what: "mirrors (the pair, at the A-pillar, rounded-rect heads on raked arms)", keys: ["mirror.centreY", "mirror.offsetX", "mirror.head.w", "mirror.head.h", "mirror.arm.length", ...(known("mirror.at") ? ["mirror.at"] : [])],
      call: `parts.push(...K.assemble.mirror({ body: parts, side: ${n(F.xc + F.W / 2)}, centreY: ${n(I("mirror.centreY"))}, z: ${n(z)}, head: { w: ${n(hw)}, h: ${n(hh)}, round: ${n(round)} }, arm: ${n(I("mirror.arm.length"))}, armFrom: [${n(from[0])}, ${n(from[1])}] }));` });
  }
  // V5-3 — the hood's V-crease lines just outside the template's raised centre panel (K.assemble.hoodPanel crease, no
  // second panel); MVP-STUB: the panel outline is the class prior (DETAIL_PRIORS.hoodPanel), the template's start
  if (known("hood.top", "cab.start")) {
    const P = DETAIL_PRIORS.hoodPanel;
    out.push({ what: "hood crease (the V-crease lines along the raised hood panel's edges)", keys: ["hood.top", "cab.start"],
      call: `parts.push(...K.assemble.hoodPanel({ host: parts.find((p) => p.id === "hood"), half: [${n(P.halfNose * F.W)}, ${n(P.halfCowl * F.W)}], inset: [${n(P.insetNose)}, ${n(P.insetCowl)}], crease: true, panel: false, body: parts, idPrefix: "hoodCrease" }));` });
  }
  return out;
}

/**
 * V4-7 — the BUS variant's READY calls (layout._profile.variant "bus"): every argument is a measured key through its
 * inverse, off F (layout keys, or V5-3 _profile.keys from scripts/measure-profile.mjs busDetails). V5-3: the framed
 * split windshield (K.assemble.paneFrame: black frame + centre mullion), the window band + pane row wrapped round the
 * rear corner (windowRow wrap), the entrance door (busDoor), ringed headlights, rounded-rect turn lenses, the marker
 * lamps on the front cap (lamp face "cap": dark housing + red / orange lenses), the bracketed black mirrors and the
 * stop arm with its rim and post.
 */
/** Bus READY-call construction priors: turn-lens corner radius (x its short side), headlight facets (triBudget). */
export const BUS_PRIORS = Object.freeze({ turnRound: 0.3, lampSegs: 12 });
function busReadyCalls(layout, F, { cited = null, minFeat = 0.04 } = {}) {
  const ok = (k) => layout[k] && !layout[k].unverified && (Number.isFinite(layout[k].value) || Array.isArray(layout[k].values));
  const has = (...ks) => ks.every((k) => (!cited || cited.includes(k)) && ok(k));
  const v = (k) => layout[k].value;
  const PK = layout._profile?.keys ?? {};
  const pv = (k) => (PK[k] && !PK[k].unverified && Number.isFinite(PK[k].value) ? PK[k].value : null);
  const pvs = (...ks) => ks.every((k) => pv(k) !== null);
  const n = (x) => m3(x).replace(/^\+/, "");
  const zOf = (u) => F.zFront - u * F.L;
  const yOf = (f) => f * F.H;
  const sp = (o) => `K.span({ ${Object.entries(o).map(([a, [p, q]]) => `${a}: [${n(p)}, ${n(q)}]`).join(", ")} })`;
  const out = [];
  if (has("window.front.w", "window.front.bottom", "window.front.top", "window.front.panes")) {
    const half = v("window.front.w") * F.W / 2;
    const post = Math.max(minFeat, (ok("window.front.post") ? v("window.front.post") : 0) * F.W);
    const y = [yOf(v("window.front.bottom")), yOf(v("window.front.top"))];
    const framed = pvs("windshield.frame.top", "windshield.frame.bottom", "windshield.frame.side");
    const frame = framed ? `{ top: ${n(pv("windshield.frame.top") * F.H)}, bottom: ${n(pv("windshield.frame.bottom") * F.H)}, side: ${n(pv("windshield.frame.side") * F.W)} }` : "0";
    const panes = v("window.front.panes");
    out.push({ what: `windshield (${panes} pane${panes > 1 ? "s split by the centre mullion" : ""}${framed ? ", in its black frame" : ""})`, keys: ["window.front.w", "window.front.bottom", "window.front.top", "window.front.panes", "window.front.post", ...(framed ? ["_profile windshield.frame.*"] : [])],
      call: `parts.push(...K.assemble.paneFrame({ host: cab, face: "+z", bounds: ${sp({ x: [F.xc - half, F.xc + half], y })}, panes: ${panes}, post: ${n(post)}, frame: ${frame}, body: parts, idPrefix: "windshield" }));` });
  }
  const doorKeys = ["door.start", "door.end", "door.bottom", "door.top", "door.pane.start", "door.pane.end", "door.pane.bottom", "door.pane.top"];
  const door = pvs(...doorKeys);
  // the door leaf: at least MIN_FEAT round its pane (MVP-STUB: the leaf's own edges read as the pane's where the walk
  // meets the mirror head in front of it)
  // The leaf starts behind the mirror arm at the front corner (mirror.at + one arm width) when the mirrors are measured.
  const armAt = ok("mirror.at") ? Math.max(0, v("mirror.at")) + minFeat / F.L : 0;
  const leaf = door ? {
    z: [Math.max(armAt, Math.min(pv("door.start"), pv("door.pane.start") - minFeat / F.L)), Math.max(pv("door.end"), pv("door.pane.end") + minFeat / F.L)],
    y: [Math.min(pv("door.bottom"), pv("door.pane.bottom") - minFeat / F.H), Math.max(pv("door.top"), pv("door.pane.top") + minFeat / F.H)],
  } : null;
  if (has("window.row.count", "window.row.start", "window.row.pitch", "window.row.paneW", "window.row.bottom", "window.row.top", "window.band.bottom", "window.band.top", "window.row.end")) {
    const gap = Math.max(0, v("window.row.pitch") - v("window.row.paneW"));
    const wraps = pv("band.end") !== null && pv("band.end") >= 0.985;
    // the band runs from the door leaf's rear edge (else one pillar gap ahead of the row) to its measured rear end; a band
    // that reaches the rear corner runs onto it (the flank layer follows a rounded corner, cornerR). The tail face is
    // hidden at the solved camera, so no `wrap` onto it is emitted (windowRow wrap stays available to a seat).
    const front = leaf ? leaf.z[1] : Math.max(0, v("window.row.start") - gap);
    const z = [zOf(wraps ? 1 : Math.min(1, pv("band.end") ?? v("window.row.end") + gap)), zOf(front)];
    out.push({ what: `window band + pane row (both flanks${wraps ? ", wrapped round the rear corner" : ""})`, keys: ["window.row.*", "window.band.*", ...(pv("band.end") !== null ? ["_profile band.end"] : [])],
      call: `parts.push(...K.assemble.windowRow({ host: cab, band: [${n(yOf(v("window.band.bottom")))}, ${n(yOf(v("window.band.top")))}], z: [${n(z[0])}, ${n(z[1])}], panes: { front: ${n(zOf(v("window.row.start")))}, pitch: ${n(v("window.row.pitch") * F.L)}, w: ${n(v("window.row.paneW") * F.L)}, count: ${v("window.row.count")}, y: [${n(yOf(v("window.row.bottom")))}, ${n(yOf(v("window.row.top")))}] }, body: parts, idPrefix: "row" }));` });
  }
  if (door) {
    out.push({ what: "door (the entrance door on the near flank: black leaf + glass pane)", keys: ["_profile door.*"],
      call: `parts.push(...K.assemble.busDoor({ host: cab, face: "+x", z: [${n(zOf(leaf.z[1]))}, ${n(zOf(leaf.z[0]))}], y: [${n(yOf(leaf.y[0]))}, ${n(yOf(leaf.y[1]))}], pane: { z: [${n(zOf(pv("door.pane.end")))}, ${n(zOf(pv("door.pane.start")))}], y: [${n(yOf(pv("door.pane.bottom")))}, ${n(yOf(pv("door.pane.top")))}] }, body: parts, idPrefix: "door" }));` });
  }
  // V5-3: the bus lenses stand proud (flush: false) — a flush recess per lens cost ~60 cab triangles each (triBudget)
  const lampCall = (keyBase, extra) => {
    const xs = layout[`${keyBase}.offsetX`].values ?? [v(`${keyBase}.offsetX`)];
    return `parts.push(...K.assemble.lamp({ body: parts, face: "nose", centre: [${n(F.xc + Math.max(...xs) * F.W)}, ${n(yOf(v(`${keyBase}.centreY`)))}], diameter: ${n(v(`${keyBase}.diameter`) * F.W)}${extra} }));`;
  };
  if (has("headlight.offsetX", "headlight.centreY", "headlight.diameter")) {
    const ring = pv("headlight.ring");
    out.push({ what: `headlights (the pair${ring !== null ? ", ringed" : ""})`, keys: ["headlight.offsetX", "headlight.centreY", "headlight.diameter", ...(ring !== null ? ["_profile headlight.ring"] : [])],
      call: lampCall("headlight", `, segs: ${BUS_PRIORS.lampSegs}${ring !== null ? `, ring: ${n(Math.max(minFeat / 2, ring * F.W))}` : ""}`) });
  }
  if (has("turn.offsetX", "turn.centreY", "turn.diameter")) {
    const shaped = pvs("turn.w", "turn.h");
    const [w, h] = shaped ? [Math.max(minFeat, pv("turn.w") * F.W), Math.max(minFeat, pv("turn.h") * F.H)] : [0, 0];
    out.push({ what: `turn lenses (the amber pair under the headlights${shaped ? ", rounded rects" : ""})`, keys: ["turn.offsetX", "turn.centreY", "turn.diameter", ...(shaped ? ["_profile turn.w", "_profile turn.h"] : [])],
      call: lampCall("turn", `, role: "prop", zone: "amber", ${shaped ? `shape: { w: ${n(w)}, h: ${n(h)}, r: ${n(BUS_PRIORS.turnRound * Math.min(w, h))} }` : "segs: 8"}, idPrefix: "turn"`) });
  }
  if (has("marker.count", "marker.centreY", "marker.offsetX", "marker.diameter")) {
    const xs = [...new Set(layout["marker.offsetX"].values.filter((x) => x > 0))].sort((a, b) => b - a);   // outer first
    const d = v("marker.diameter") * F.W;
    const pad = pv("marker.housing.pad");
    // the outer lens of each housing is red (signal), the inner amber (orange): refs/school_bus.png roof markers
    const zones = xs.map((_, i) => (i === 0 ? "signal" : "orange"));
    out.push({ what: `markers (${v("marker.count")} roof-marker lenses on the front cap${pad !== null ? ", in two black housings" : ""})`, keys: ["marker.count", "marker.centreY", "marker.offsetX", "marker.diameter", ...(pad !== null ? ["_profile marker.housing.pad"] : [])],
      call: `parts.push(...K.assemble.lamp({ host: cab, face: "cap", body: parts, y: ${n(yOf(v("marker.centreY")))}, diameter: ${n(d)}, lenses: [${xs.map((x, i) => `{ x: ${n(F.xc + x * F.W)}, zone: "${zones[i]}" }`).join(", ")}]${pad !== null ? `, housing: { pad: ${n(Math.max(minFeat / 2, pad * F.W))}, zone: "black" }` : ""}, idPrefix: "marker" }));` });
  }
  if (has("mirror.centreY", "mirror.head.w", "mirror.head.h", "mirror.at")) {
    // MVP-STUB: mirror.arm.length is UNVERIFIED on the bus (the head's inner edge rectifies inside the flank): the arm is MIN_FEAT
    const arm = ok("mirror.arm.length") ? v("mirror.arm.length") * F.W : minFeat;
    const round = DETAIL_PRIORS.mirrorRound * Math.min(v("mirror.head.w") * F.W, v("mirror.head.h") * F.H);
    const z = Math.min(zOf(Math.max(0, v("mirror.at"))), F.zFront - minFeat);
    out.push({ what: "mirrors (the black pair on bracket arms at the front corners)", keys: ["mirror.centreY", "mirror.offsetX", "mirror.head.w", "mirror.head.h", "mirror.at"],
      call: `parts.push(...K.assemble.mirror({ body: parts, side: ${n(F.xc + F.W / 2)}, centreY: ${n(yOf(v("mirror.centreY")))}, z: ${n(z)}, head: { w: ${n(v("mirror.head.w") * F.W)}, h: ${n(v("mirror.head.h") * F.H)}, round: ${n(round)} }, arm: ${n(arm)}, bracket: true, zone: "black" }));` });
  }
  if (has("stopArm.centreAt", "stopArm.centreY", "stopArm.diameter")) {
    const border = pv("stopArm.border");
    const post = pvs("stopArm.post.bottom", "stopArm.post.top") ? [yOf(pv("stopArm.post.bottom")), yOf(pv("stopArm.post.top"))] : null;
    out.push({ what: `stop arm (folded on the near flank${border !== null ? ", light rim" : ""}${post ? ", black post" : ""})`, keys: ["stopArm.centreAt", "stopArm.centreY", "stopArm.diameter", ...(border !== null ? ["_profile stopArm.border"] : []), ...(post ? ["_profile stopArm.post.*"] : [])],
      call: `parts.push(...K.assemble.stopArm({ host: cab, centre: [${n(zOf(v("stopArm.centreAt")))}, ${n(yOf(v("stopArm.centreY")))}], diameter: ${n(v("stopArm.diameter") * F.L)}, ${border !== null ? `border: ${n(Math.max(0.01, border * F.L))}, ` : ""}${post ? `post: [${n(post[0])}, ${n(post[1])}], ` : ""}body: parts, idPrefix: "stopArm" }));` });
  }
  return out;
}

/**
 * WF-R3 R3-B item 5 — LK_SILHOUETTE's region (scripts/likeness.mjs), in the frame of the RENDERED parts: the cab's
 * front corner above the windshield's top edge — x across the body, y from window.front.top x H to the roof, z from
 * cab.start to where the measured rake (window.front.bottom at cab.start -> window.front.top at window.front.topAt)
 * meets the roof. A box cab fills that wedge; the target shows the raked roof edge and background there.
 */
export function silhouetteBox(layout, records, cls) {
  const v = (k) => (layout?.[k] && !layout[k].unverified && Number.isFinite(layout[k].value) ? layout[k].value : null);
  const [cs, wb, wt, wa] = ["cab.start", "window.front.bottom", "window.front.top", "window.front.topAt"].map(v);
  if ([cs, wb, wt, wa].some((x) => x === null) || !(wt > wb)) return null;
  const roles = cls?.lengthRoles ?? DEFAULT_LENGTH_ROLES;
  const core = records.filter((r) => roles.includes(r.role) && !INLAY_HELPERS.includes(r.part?.assembly?.helper));
  if (core.length === 0) return null;
  const min = [0, 1, 2].map((a) => Math.min(...core.map((r) => r.aabb.min[a])));
  const max = [0, 1, 2].map((a) => Math.max(...core.map((r) => r.aabb.max[a])));
  const L = max[2] - min[2];
  const H = max[1];
  const roofAt = cs + (wa - cs) * (1 - wb) / (wt - wb);
  return { x: [min[0], max[0]], y: [wt * H, H], z: [max[2] - roofAt * L, max[2] - cs * L] };
}

/** `{id, box}` of the members painted `zone`, else of all members. */
function zonedBox(ctx, members, zone) {
  const painted = members.filter((m) => m.zone === zone);
  const use = painted.length > 0 ? painted : members;
  return { id: use[0].id, box: ctx.geo.unionBox(use) };
}

/** The mirror head: the member with the largest y extent. */
function headOf(g) {
  return g.members.reduce((a, b) => (ext(b.aabb, 1) > ext(a.aabb, 1) ? b : a));
}

/** The pane of a window group: its glass member(s), else the member thinnest along `axis`. */
function paneOf(ctx, g, axis) {
  const glass = g.members.filter((m) => m.zone === "glass");
  if (glass.length > 0) return { id: glass[0].id, box: ctx.geo.unionBox(glass) };
  const m = g.members.reduce((a, b) => (ext(b.aabb, axis) < ext(a.aabb, axis) ? b : a));
  return { id: m.id, box: m.aabb };
}

function windshieldPane(ctx, F) {
  const straddle = groupsOf(ctx, "window").filter((g) => g.box.min[0] < F.xc && g.box.max[0] > F.xc);
  if (straddle.length === 0) return null;
  return paneOf(ctx, straddle.reduce((a, b) => (b.box.max[2] > a.box.max[2] ? b : a)), 0);
}

function nearSidePanes(ctx, F) {
  return groupsOf(ctx, "window").filter((g) => g.box.min[0] > F.xc)
    .sort((a, b) => b.box.max[2] - a.box.max[2])
    .map((g) => paneOf(ctx, g, 2));
}
