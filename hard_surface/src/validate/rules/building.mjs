// Class RULES for buildings (WORKFLOW-V3 §7.5). Everything in the kernel chain
// that is a FUNCTION of building semantics lives here; the data half of the
// class prior is classes/building.json. `src/validate/kernel-chain.mjs` receives
// both through `validateParts(meta, parts, limits, { cls, rules })` and imports
// this file itself only when no class prior is supplied.
//
// Contract:
//   layoutRules  key -> { roles, unit, list?, mismatchHint?, measure(ctx, F) }
//   layoutFrame  (ctx) -> F | null — the frame layout fractions are taken in
//   validators   [[name, fn(ctx) -> {violations, advisories}], ...] in chain
//                order; a validator named "V7" runs in the V7 slot right after
//                the generic closed-role check.
//
// Helpers shared with the generic chain arrive on `ctx.geo` (groupAssemblies,
// unionBox, spanOverlap, clusters, make, advise, fmt), so this module never
// imports kernel-chain.mjs and there is no import cycle.
import * as K from "../../kernel/index.mjs";

/** Author-declared storey height, for the V7 window row. */
export const DEFAULT_FLOOR_H = 3.5;

// ---------------------------------------------------------------------------
// V7 — the relative-scale role table (limits.v7), re-implemented on part AABBs.
//
// DEVIATION, declared: `src/validate/v7.js` is NOT imported. Its building rows
// read `spec.parts[].dims` and `part.attach.to` (v7.js:20-45) — an authored
// declaration and a parent link, neither of which exists on a kernel part, and
// its window row needs the host's authored storey height. The rows themselves
// are the owner's data in limits.v7 and are read from there unchanged; only the
// measurement moves from declared dims to the measured AABB.
// ---------------------------------------------------------------------------

function validateV7Rows(ctx) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  const table = ctx.limits.v7 ?? {};
  const height = (r) => r.aabb.max[1] - r.aabb.min[1];
  const withRole = (role) => ctx.records.filter((r) => r.role === role);

  const range = (role, key, label) => {
    const bounds = table[key];
    if (!bounds) return;
    for (const record of withRole(role)) {
      const h = height(record);
      if (h < bounds[0] - 1e-9 || h > bounds[1] + 1e-9) {
        violations.push(make("V7", record.id, `${label} ${fmt(h)} m`, `${bounds[0]}..${bounds[1]} m`,
          `"${record.id}" (role ${role}) has ${label} ${fmt(h)} m, outside the ${bounds[0]}..${bounds[1]} m rule — resize it`));
      }
    }
  };

  // r3 ruling (Fable): a stylised target's door is 0.127 H; limits.json's absolute
  // door_h 2.0-2.4 m would force H ~ 16 m. When the LAYOUT carries door.h the
  // measured proportion wins and the absolute band stands down (limits.json frozen).
  if (!(ctx.layout && ctx.layout["door.h"])) range("door", "door_h", "height");
  // run2 P3 fix: a handrail is a 0.06 m bar sitting ~1 m above its deck, so its OWN
  // height never lands in railing_h. Measure rail TOP above the deck it guards
  // (landing/step/roof/parapet top at or below the rail, overlapping in plan ±0.3 m);
  // only a rail with no deck under it is measured by its own height.
  {
    const bounds = table.railing_h;
    const decks = ctx.records.filter((r) => ["landing", "step", "roof", "parapet", "massing"].includes(r.role));
    const overlapPlan = (a, b, pad) => a.aabb.min[0] <= b.aabb.max[0] + pad && b.aabb.min[0] <= a.aabb.max[0] + pad
      && a.aabb.min[2] <= b.aabb.max[2] + pad && b.aabb.min[2] <= a.aabb.max[2] + pad;
    if (bounds) for (const rail of withRole("railing")) {
      // Sloped stair rails span the whole flight in y; V7_STAIR_RAIL measures those
      // against the tread line, so they are skipped here.
      if (height(rail) > 0.5) continue;
      // A rail beside a flight has treads AND its landing under it in plan; the rail
      // is right if ANY deck under it puts the rail top in band, so take the best.
      let h = null;
      for (const d of decks) {
        if (d.aabb.max[1] <= rail.aabb.min[1] + 0.02 && d.aabb.max[1] > rail.aabb.min[1] - 1.5 && overlapPlan(rail, d, 0.3)) {
          const v = rail.aabb.max[1] - d.aabb.max[1];
          if (h === null || Math.abs(v - 1.0) < Math.abs(h - 1.0)) h = v;
        }
      }
      if (h === null) h = height(rail);
      if (h < bounds[0] - 1e-9 || h > bounds[1] + 1e-9) {
        violations.push(make("V7", rail.id, `rail top ${fmt(h)} m above deck`, `${bounds[0]}..${bounds[1]} m`,
          `"${rail.id}" (role railing) tops out ${fmt(h)} m above the deck it guards, outside ${bounds[0]}..${bounds[1]} m — move or resize it`));
      }
    }
  }
  range("parapet", "parapet_h", "height");

  // r1 row 5 — step_rise is a PITCH, not a board thickness. DEVIATION, declared:
  // the band is limits.v7.step_rise (0.14..0.2 m) unchanged; only the
  // measurement moves from "the height of one step solid" (which a 0.08 m tread
  // board always failed or always passed for the wrong reason) to "the y
  // distance between consecutive treads", which is what a rise is. Landing tops
  // count as treads: the first and last riser of a flight land on them.
  const stepBand = table.step_rise;
  if (stepBand) {
    const stepRecords = ctx.records.filter((r) => r.role === "step");
    if (stepRecords.length > 0) {
      const landingTops = ctx.records.filter((r) => r.role === "landing").map((r) => r.aabb.max[1]);
      const levels = [...stepRecords.map((r) => r.aabb.max[1]), ...landingTops].sort((a, b) => a - b);
      // Collapse members that share a level (a deck is many bars at one height).
      const rungs = [];
      for (const y of levels) if (rungs.length === 0 || y - rungs[rungs.length - 1] > 1e-3) rungs.push(y);
      const flightTop = Math.max(...stepRecords.map((r) => r.aabb.max[1]));
      const flightBottom = Math.min(...stepRecords.map((r) => r.aabb.max[1]));
      const pitches = [];
      for (let i = 1; i < rungs.length; i += 1) {
        // Only the risers that belong to the flight: a landing two storeys up
        // is not a step above the top tread.
        if (rungs[i] < flightBottom - 1e-6 || rungs[i - 1] > flightTop + 1e-6) continue;
        pitches.push(rungs[i] - rungs[i - 1]);
      }
      const first = stepRecords[0];
      if (pitches.length === 0) {
        violations.push(make("V7", first.id, "one tread level only", `${stepBand[0]}..${stepBand[1]} m between treads`,
          `the flight containing "${first.id}" has no measurable rise — every tread must sit at its own height, and the flight must reach a landing top`));
      } else {
        const low = Math.min(...pitches);
        const high = Math.max(...pitches);
        if (low < stepBand[0] - 1e-9 || high > stepBand[1] + 1e-9) {
          const worst = Math.abs(low - stepBand[0]) > Math.abs(high - stepBand[1]) ? low : high;
          violations.push(make("V7", first.id, `rise ${fmt(worst)} m`, `${stepBand[0]}..${stepBand[1]} m`,
            `the flight rises ${fmt(worst)} m per tread — put ${Math.max(2, Math.ceil((flightTop - Math.min(...rungs)) / stepBand[1]))} or more treads in it so each riser lands inside ${stepBand[0]}..${stepBand[1]} m`));
        } else if (high - low > ctx.L("stepRiseVariation") + 1e-9) {
          violations.push(make("V7", first.id, `rise varies ${fmt(high - low)} m`, `<= ${fmt(ctx.L("stepRiseVariation"))} m`,
            `the treads are unevenly spaced (${fmt(low)}..${fmt(high)} m) — space them on one constant pitch with K.repeat`));
        }
      }
    }
  }

  // r1 row 5 — a flight without a handrail. Every stringer needs at least one
  // railing part over its run, at hand height above the line the treads make.
  const railBand = ctx.L("stairRailBand");
  // V5-8 R2: waived only by the subject's measured ruleOverrides.stairRails (kernel-chain prints it as RULE_OVERRIDE)
  const stairRailWaived = (ctx.waived ?? []).includes("V7_STAIR_RAIL");
  for (const stringer of stairRailWaived ? [] : ctx.records.filter((r) => r.role === "stringer")) {
    const treadLine = stringer.aabb.min[1];
    const lo = treadLine + railBand[0];
    const hi = stringer.aabb.max[1] + railBand[1];
    const found = ctx.records.some((r) => r.role === "railing"
      && Math.min(r.aabb.max[0], stringer.aabb.max[0]) - Math.max(r.aabb.min[0], stringer.aabb.min[0]) > 0
      && r.aabb.max[1] >= lo - 1e-9 && r.aabb.min[1] <= hi + 1e-9);
    if (!found) {
      violations.push(make("V7_STAIR_RAIL", stringer.id, "no railing over the run", `>= 1 railing part ${railBand[0]}..${railBand[1]} m above the treads`,
        `"${stringer.id}" is an open flight with nothing to hold — add a role "railing" part spanning its x-range, ${railBand[0]}..${railBand[1]} m above the tread line`));
    }
  }

  if (table.window_h_lt_floorH) {
    const floorH = Number.isFinite(ctx.meta?.floorH) ? ctx.meta.floorH : DEFAULT_FLOOR_H;
    for (const record of withRole("window")) {
      const h = height(record);
      if (h >= floorH - 1e-9) {
        violations.push(make("V7", record.id, `height ${fmt(h)} m`, `< floor height ${fmt(floorH)} m`,
          `"${record.id}" (role window) is ${fmt(h)} m tall, as tall as the ${fmt(floorH)} m storey — a window must be shorter than its floor`));
      }
    }
  }

  if (table.awning_bottom_ge_door_top) {
    const doors = withRole("door");
    if (doors.length > 0) {
      const doorTop = Math.max(...doors.map((r) => r.aabb.max[1]));
      for (const record of withRole("awning")) {
        if (record.aabb.min[1] < doorTop - 1e-9) {
          violations.push(make("V7", record.id, `bottom ${fmt(record.aabb.min[1])} m`, `>= door top ${fmt(doorTop)} m`,
            `raise "${record.id}" to ${fmt(doorTop)} m — an awning below the door head blocks the door`));
        }
      }
    }
  }

  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// V11 — BUILDABILITY (WF-LOOP r1 rows 2, 7, 8, 9). Four rows that every round-0
// error had in common: geometry that is physically impossible to occupy. They
// are grouped because they share one idea — a thing a person stands on, walks
// through or climbs off has to be reachable and has to bear.
// ---------------------------------------------------------------------------

/** Axis-aligned box-to-box gap, 0 when they touch or overlap. */
function boxGap(a, b) {
  let sum = 0;
  for (let i = 0; i < 3; i += 1) {
    const d = Math.max(a.min[i] - b.max[i], b.min[i] - a.max[i], 0);
    sum += d * d;
  }
  return Math.sqrt(sum);
}

/**
 * Two-pass 3-4 chamfer distance (scaled to the grid) from every supported cell.
 * Approximate to ~2 % of the true Euclidean distance, which is far inside the
 * 1 m band it is compared against, and O(cells) instead of O(cells^2).
 */
function chamfer(supported, nx, nz, grid) {
  const BIG = 1e9;
  const d = new Float64Array(nx * nz).fill(BIG);
  for (let i = 0; i < d.length; i += 1) if (supported[i]) d[i] = 0;
  const relax = (i, j, di, dj, cost) => {
    const ii = i + di;
    const jj = j + dj;
    if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) return;
    const candidate = d[ii * nz + jj] + cost;
    if (candidate < d[i * nz + j]) d[i * nz + j] = candidate;
  };
  for (let i = 0; i < nx; i += 1) {
    for (let j = 0; j < nz; j += 1) {
      relax(i, j, -1, 0, 1); relax(i, j, 0, -1, 1);
      relax(i, j, -1, -1, Math.SQRT2); relax(i, j, -1, 1, Math.SQRT2);
    }
  }
  for (let i = nx - 1; i >= 0; i -= 1) {
    for (let j = nz - 1; j >= 0; j -= 1) {
      relax(i, j, 1, 0, 1); relax(i, j, 0, 1, 1);
      relax(i, j, 1, 1, Math.SQRT2); relax(i, j, 1, -1, Math.SQRT2);
    }
  }
  let worst = 0;
  for (const value of d) worst = Math.max(worst, value === BIG ? BIG : value * grid);
  return worst;
}

/**
 * r1 row 2 — BEARING. A roof, cornice, sill, awning, landing or parapet is a
 * horizontal thing carrying load. Sample its underside on a 0.1 m grid; a
 * sample is borne when some other part's material is at that (x, z) within
 * 0.02 m of the underside. Any borne sample more than 1.0 m from the nearest
 * borne one is a cantilever nothing holds up — that is the 3.1 m roof
 * overhanging 1.1 m returns, measured instead of argued.
 */
function validateV11Bearing(ctx) {
  const { make, fmt, spanOverlap } = ctx.geo;
  const violations = [];
  const grid = ctx.L("bearingGrid");
  const drop = ctx.L("bearingDrop");
  const span = ctx.L("bearingSpan");
  const bearingRoles = ctx.cls.bearingRoles ?? [];

  for (const record of ctx.records) {
    if (!bearingRoles.includes(record.role)) continue;
    const bottom = record.aabb.min[1];
    if (bottom <= ctx.EPS) continue;                        // it stands on the ground
    const w = record.aabb.max[0] - record.aabb.min[0];
    const d = record.aabb.max[2] - record.aabb.min[2];
    const nx = Math.max(1, Math.ceil(w / grid));
    const nz = Math.max(1, Math.ceil(d / grid));
    if (nx * nz > 40000) continue;                          // pathological; V5/V10 catch it

    const carriers = ctx.records.filter((other) => other.index !== record.index
      && other.aabb.max[1] >= bottom - drop && other.aabb.min[1] <= bottom + drop
      && spanOverlap(other.aabb.min[0], other.aabb.max[0], record.aabb.min[0], record.aabb.max[0]) > 0
      && spanOverlap(other.aabb.min[2], other.aabb.max[2], record.aabb.min[2], record.aabb.max[2]) > 0);

    const supported = new Uint8Array(nx * nz);
    let any = false;
    for (let i = 0; i < nx; i += 1) {
      const x = record.aabb.min[0] + (i + 0.5) * (w / nx);
      for (let j = 0; j < nz; j += 1) {
        const z = record.aabb.min[2] + (j + 0.5) * (d / nz);
        for (const carrier of carriers) {
          if (x >= carrier.aabb.min[0] - 1e-9 && x <= carrier.aabb.max[0] + 1e-9
            && z >= carrier.aabb.min[2] - 1e-9 && z <= carrier.aabb.max[2] + 1e-9) {
            supported[i * nz + j] = 1;
            any = true;
            break;
          }
        }
      }
    }

    if (!any) {
      violations.push(make("V11_BEARING", record.id, "nothing under it anywhere", `a carrier within ${fmt(drop)} m below`,
        `"${record.id}" (role ${record.role}) has no part under its underside at y = ${fmt(bottom)} m — build what carries it, or lower it onto something that is already there`));
      continue;
    }
    const worst = chamfer(supported, nx, nz, Math.max(w / nx, d / nz));
    if (worst > span + 1e-9) {
      violations.push(make("V11_BEARING", record.id, `${fmt(worst)} m cantilever`, `<= ${fmt(span)} m`,
        `"${record.id}" (role ${record.role}) overhangs ${fmt(worst)} m past anything that carries it — carry it through (full-depth side walls and a back wall under a roof), or cut it back to ${fmt(span)} m of free span`));
    }
  }
  return { violations, advisories: [] };
}

/**
 * r1 row 7 — a landing that stands 0.425 m clear of the wall is a hole a person
 * falls down. The rear of every deck has to be within 0.15 m of the mass it
 * hangs off.
 */
function validateV11LandingGap(ctx) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  const maxGap = ctx.L("landingGapMax");
  const massing = ctx.records.filter((r) => r.role === "massing");
  if (massing.length === 0) return { violations, advisories: [] };
  for (const record of ctx.records) {
    if (record.role !== "landing") continue;
    const gap = Math.min(...massing.map((m) => boxGap(record.aabb, m.aabb)));
    if (gap > maxGap + 1e-9) {
      violations.push(make("V11_LANDING_GAP", record.id, `${fmt(gap)} m off the wall`, `<= ${fmt(maxGap)} m`,
        `"${record.id}" leaves a ${fmt(gap)} m slot between the deck and the brick — bring the deck back to the wall (the sills project, so run the deck over or under them), or close the slot`));
    }
  }
  return { violations, advisories: [] };
}

/**
 * Group parts of one role into assemblies by overlapping range on `axis`
 * (0 = x, 1 = y, 2 = z). Two ladder stiles at the same x are one ladder.
 */
function assemblies(records, axis, pad = 0) {
  const sorted = [...records].sort((a, b) => a.aabb.min[axis] - b.aabb.min[axis]);
  const groups = [];
  for (const record of sorted) {
    const last = groups[groups.length - 1];
    if (last && record.aabb.min[axis] <= last.max + pad + 1e-9) {
      last.members.push(record);
      last.max = Math.max(last.max, record.aabb.max[axis]);
      last.min = Math.min(last.min, record.aabb.min[axis]);
    } else {
      groups.push({ members: [record], min: record.aabb.min[axis], max: record.aabb.max[axis] });
    }
  }
  return groups;
}

/**
 * r1 row 8 — a drop ladder whose head comes up through a continuous railing is
 * a ladder nobody can get off. Nothing in the railing family may stand in the
 * head zone of a ladder that reaches a deck.
 */
function validateV11LadderAccess(ctx) {
  const { make, fmt, spanOverlap } = ctx.geo;
  const violations = [];
  const ladders = assemblies(ctx.records.filter((r) => r.role === "ladder"), 0, 0.7);   // two stiles = one ladder
  if (ladders.length === 0) return { violations, advisories: [] };
  const landings = ctx.records.filter((r) => r.role === "landing");
  const guards = ctx.records.filter((r) => r.role === "railing" || r.role === "baluster");
  const reach = ctx.L("ladderLandingReach");
  const slack = ctx.L("ladderHeadSlack");
  const band = ctx.L("ladderHeadBand");

  for (const ladder of ladders) {
    const top = Math.max(...ladder.members.map((r) => r.aabb.max[1]));
    for (const landing of landings) {
      if (Math.abs(landing.aabb.max[1] - top) > reach) continue;
      const lo = landing.aabb.max[1];
      const hi = lo + band;
      const zoneMin = ladder.min - slack;
      const zoneMax = ladder.max + slack;
      // run2 P3 fix: AABB alone flagged a SLOPED flight rail whose box happens to
      // cover the head zone. Broad-phase on the box, then the real solid against a
      // head-zone box (x: ladder ± slack, y: lo..hi, z: the ladder's own z extent ± slack).
      const zMin = Math.min(...ladder.members.map((r) => r.aabb.min[2])) - slack;
      const zMax = Math.max(...ladder.members.map((r) => r.aabb.max[2])) + slack;
      const zone = K.box([zoneMax - zoneMin, hi - lo, zMax - zMin]).at([(zoneMin + zoneMax) / 2, lo, (zMin + zMax) / 2]);
      const blocker = guards.find((g) => spanOverlap(g.aabb.min[0], g.aabb.max[0], zoneMin, zoneMax) > 0
        && spanOverlap(g.aabb.min[1], g.aabb.max[1], lo, hi) > 0
        && spanOverlap(g.aabb.min[2], g.aabb.max[2], zMin, zMax) > 0
        && K.intersect(g.part.solid, zone).volume() > 1e-9);
      if (blocker) {
        violations.push(make("V11_LADDER_ACCESS", blocker.id, `blocks x ${fmt(zoneMin)}..${fmt(zoneMax)} at y ${fmt(lo)}..${fmt(hi)}`,
          "a clear head zone", `"${blocker.id}" stands across the head of the ladder at "${ladder.members[0].id}" — leave a gate-width gap in the railing over the ladder (no railing or baluster between x ${fmt(zoneMin)} and ${fmt(zoneMax)} up to ${fmt(hi)} m)`));
        break;
      }
    }
  }
  return { violations, advisories: [] };
}

/**
 * r1 row 9 — a deck of bars with 0.21 m slots between them is a grating you
 * post a foot through. Within one deck level, members that are spread along
 * their own short axis must not leave a gap wider than 0.10 m. Only runs of
 * three or more are treated as a deck surface: a pair of edge members is the
 * frame, not the walking surface.
 */
function validateV11DeckGap(ctx) {
  const { make, fmt, spanOverlap } = ctx.geo;
  const violations = [];
  const maxGap = ctx.L("deckGapMax");
  const decks = ctx.records.filter((r) => r.role === "landing");
  if (decks.length < 3) return { violations, advisories: [] };

  for (const level of assemblies(decks, 1)) {                // one y-band = one deck
    for (const axis of [0, 2]) {
      const long = axis === 0 ? 2 : 0;
      const members = level.members.filter((r) =>
        (r.aabb.max[axis] - r.aabb.min[axis]) < (r.aabb.max[long] - r.aabb.min[long]));
      if (members.length < 3) continue;
      members.sort((a, b) => a.aabb.min[axis] - b.aabb.min[axis]);
      for (let i = 1; i < members.length; i += 1) {
        const prev = members[i - 1];
        const next = members[i];
        if (spanOverlap(prev.aabb.min[long], prev.aabb.max[long], next.aabb.min[long], next.aabb.max[long]) <= 0) continue;
        const gap = next.aabb.min[axis] - prev.aabb.max[axis];
        if (gap > maxGap + 1e-9) {
          violations.push(make("V11_DECK_GAP", next.id, `${fmt(gap)} m slot after "${prev.id}"`, `<= ${fmt(maxGap)} m`,
            `the deck at y = ${fmt(level.min)} m leaves a ${fmt(gap)} m slot between "${prev.id}" and "${next.id}" — close the pitch (${fmt(maxGap)} m maximum clear) or widen the members`));
          break;
        }
      }
    }
  }
  return { violations, advisories: [] };
}

/**
 * v3-backlog item 3 — a landing nobody is kept on. The target's two landings
 * carry a front rail and a return at each end; the v3-proof author built bare
 * decks and no row saw it. Every landing ASSEMBLY (landing-role members joined
 * within deckGapMax) is walked edge by edge in plan. An edge is AGAINST THE WALL
 * when a massing part's face lies within landingGapMax of it, at deck height,
 * along at least half its run; every other edge — the open front and the exposed
 * ends — needs role `railing` members whose TOP is limits.v7.railing_h above the
 * deck top, within landingGapMax of the edge line, covering its run. Not a hole:
 * a stretch no longer than one deck slot plus one bar (deckGapMax + MIN_FEAT —
 * a rail stops at the last free bar before a gate), and a GATE.
 *
 * WF-BLIND-R2 C2 — the gate is ONE computation shared with K.assemble.landing
 * (`K.assemble.gateSpans`): the plan extent, +/- ladderHeadSlack, of the part of
 * a ladder stile or stair stringer within ladderHeadBand of the deck top, next
 * to that edge. A helper-built deck's DECLARED gateAt is honoured where a real
 * head arrives inside it, clipped to one hole (deckGapMax + MIN_FEAT) past that
 * head, and a declared gate that takes a corner opens that end's first
 * bar + ladderHeadSlack. Terra's blind P2 landing (deck z -1.1..0 on the real
 * wall, rails 0.94-1.0 m, returns) failed here only because its flight gate was
 * declared as the flight width round the arrival x while the rule measured the
 * stringer's rising run.
 */
function validateV11LandingGuard(ctx) {
  const { make, fmt, spanOverlap, groupAssemblies } = ctx.geo;
  const violations = [];
  const band = ctx.limits.v7?.railing_h;
  const decks = ctx.records.filter((r) => r.role === "landing");
  if (!band || decks.length === 0) return { violations, advisories: [] };
  const reach = ctx.L("landingGapMax");
  const slack = ctx.L("ladderHeadSlack");
  const headBand = ctx.L("ladderHeadBand");
  const holeMax = ctx.L("deckGapMax") + ctx.MIN_FEAT;
  const massing = ctx.records.filter((r) => r.role === "massing");
  const rails = ctx.records.filter((r) => r.role === "railing");
  const heads = ctx.records.filter((r) => r.role === "ladder" || r.role === "stringer").map((r) => r.part.solid);

  for (const deck of groupAssemblies(decks, [0, 1, 2], ctx.L("deckGapMax"))) {
    const { box } = deck;
    const top = box.max[1];
    const { spans: real } = K.assemble.gateSpans({ box, heads, reach, slack, headBand });
    const gates = { front: [...real.front], back: [...real.back], "street-right end": [...real["street-right end"]], "street-left end": [...real["street-left end"]] };
    // Declared helper gates (numeric gateAt), honoured only where a real head arrives inside them.
    const declared = new Map();
    for (const m of deck.members) {
      const a = m.part.assembly;
      if (a && a.helper === "landing" && Array.isArray(a.gates)) declared.set(a.id, a.gates);
    }
    const unmatched = [];
    for (const gate of [...declared.values()].flat()) {
      const hits = real.front.filter(([p, q]) => Math.min(q, gate.front[1]) - Math.max(p, gate.front[0]) > 0);
      if (hits.length === 0) { unmatched.push(gate.front); continue; }
      const lo = Math.max(gate.front[0], Math.min(...hits.map((s) => s[0])) - holeMax);
      const hi = Math.min(gate.front[1], Math.max(...hits.map((s) => s[1])) + holeMax);
      gates.front.push([lo, hi]);
      if (gate.corner === "street-right end" && lo - box.min[0] <= holeMax + 1e-9) gates[gate.corner].push(gate.cornerSpan);
      if (gate.corner === "street-left end" && box.max[0] - hi <= holeMax + 1e-9) gates[gate.corner].push(gate.cornerSpan);
    }
    const misses = [];
    for (const [name, a, c, out, b] of K.assemble.landingEdges(box)) {
      const lo = box.min[b];
      const hi = box.max[b];
      const walled = massing.some((m) => m.aabb.min[1] <= top + 1e-9 && m.aabb.max[1] >= top - 1e-9
        && spanOverlap(m.aabb.min[b], m.aabb.max[b], lo, hi) >= 0.5 * (hi - lo) - 1e-9
        && Math.abs((out < 0 ? m.aabb.max[a] : m.aabb.min[a]) - c) <= reach + 1e-9);
      if (walled) continue;
      const nearEdge = (bx, pad) => spanOverlap(bx.min[a], bx.max[a], c - pad, c + pad) > -1e-9;
      const spans = rails
        .filter((r) => r.aabb.max[1] >= top + band[0] - 1e-6 && r.aabb.max[1] <= top + band[1] + 1e-6
          && r.aabb.min[1] >= top - reach - 1e-9 && nearEdge(r.aabb, reach))
        .map((r) => [r.aabb.min[b], r.aabb.max[b]]);
      spans.push(...gates[name]);
      const clipped = spans.map(([p, q]) => [Math.max(lo, p), Math.min(hi, q)]).filter(([p, q]) => q > p)
        .sort((u, v) => u[0] - v[0]);
      let at = lo;
      let worst = null;
      for (const [p, q] of [...clipped, [hi, hi]]) {
        if (p - at > holeMax + 1e-9 && (!worst || p - at > worst[1] - worst[0])) worst = [at, p];
        at = Math.max(at, q);
      }
      if (worst) misses.push({ name, along: b === 0 ? "x" : "z", worst });
    }
    if (misses.length === 0) continue;
    const first = deck.members[0];
    const unmatchedText = unmatched.length
      ? ` — declared gateAt ${unmatched.map(([p, q]) => `x ${fmt(p)}..${fmt(q)}`).join(", ")} has no ladder or flight head arriving in it`
      : "";
    violations.push(make("V11_LANDING_GUARD", first.id,
      misses.map((m) => `${m.name} open ${fmt(m.worst[1] - m.worst[0])} m (${m.along} ${fmt(m.worst[0])}..${fmt(m.worst[1])})`).join("; "),
      `a railing top ${band[0]}..${band[1]} m above the deck along every open edge; holes <= ${fmt(holeMax)} m outside gates`,
      `the landing at y = ${fmt(top)} m ("${first.id}") has no guard on its ${misses.map((m) => m.name).join(", ")}${unmatchedText} — `
      + "build the escape with K.assemble.fireEscape so the gate is exactly what arrives, "
      + `or add role "railing" members along the open front and each exposed end with their tops ${band[0]}..${band[1]} m above the deck`));
  }
  return { violations, advisories: [] };
}

// ---------------------------------------------------------------------------
// WF-R3 H4 — three rows the blind P2 baseline showed missing: Luna and Gemini-M both hung the flight IN FRONT of
// both decks, gateFor then opened gates across most of each front rail, and the drop ladder ran down past the
// awning. Each scored PASS. The flight row reads the SAME predicate K.assemble uses (K.assemble.flightArrivals).
// ---------------------------------------------------------------------------

/** Records of `role` grouped by helper assembly id, else by `fallback(loose)` (arrays of members). */
function tagged(ctx, role, fallback) {
  const byId = new Map();
  const loose = [];
  for (const r of ctx.records.filter((x) => x.role === role)) {
    const id = r.part.assembly?.id;
    if (id) { if (!byId.has(id)) byId.set(id, []); byId.get(id).push(r); } else loose.push(r);
  }
  return [...byId.values(), ...(loose.length ? fallback(loose) : [])];
}
/** Flights (treads one riser apart are one flight), ladders (stiles within 0.7 m), stringer pairs. */
const flightGroups = (ctx, maxRise) => tagged(ctx, "step", (l) => ctx.geo.groupAssemblies(l, [0, 1, 2], maxRise).map((g) => g.members));
const ladderGroups = (ctx) => tagged(ctx, "ladder", (l) => assemblies(l, 0, 0.7).map((g) => g.members));
const stringerGroups = (ctx) => tagged(ctx, "stringer", (l) => ctx.geo.groupAssemblies(l, [0, 1, 2], 1.5).map((g) => g.members));

/**
 * V11_FLIGHT_ON_DECK — each flight's bottom and top tread lie ON a landing deck: inside its plan footprint grown by
 * one tread, with the tread top within maxRise (limits.v7.step_rise max) of the deck top.
 */
function validateV11FlightOnDeck(ctx) {
  const { make, fmt } = ctx.geo;
  const violations = [];
  const maxRise = ctx.limits.v7?.step_rise?.[1];
  const decks = landingLevels(ctx).map((g) => g.box);
  if (!maxRise || decks.length === 0) return { violations, advisories: [] };
  const box = (b) => `x ${fmt(b.min[0])}..${fmt(b.max[0])} z ${fmt(b.min[2])}..${fmt(b.max[2])} top y ${fmt(b.max[1])}`;
  for (const members of flightGroups(ctx, maxRise)) {
    const a = K.assemble.flightArrivals(members.map((m) => m.aabb), decks, maxRise);
    const ends = [["bottom", a.bottom, a.bottomDeck], ["top", a.top, a.topDeck]].filter(([, , d]) => d < 0);
    if (ends.length === 0) continue;
    const id = members.find((m) => m.aabb === ends[0][1])?.id ?? members[0].id;
    violations.push(make("V11_FLIGHT_ON_DECK", id, ends.map(([n, b]) => `${n} tread ${box(b)}`).join("; "),
      `on a deck (${decks.map(box).join(" | ")}) +/- one tread, within ${fmt(maxRise)} m of its top`,
      `the flight's ${ends.map(([n]) => n).join(" and ")} tread is not on a landing — a flight starts and ends ON its decks, `
      + "not in front of them; build the landings, flight and drop ladder with one K.assemble.fireEscape call"));
  }
  return { violations, advisories: [] };
}

/**
 * V11_RAIL_COVERAGE — a deck's open front keeps its guard: every opening in the front rail is no wider than the
 * element arriving through it (a ladder's width, a flight's across-run width) + 2 x ladderHeadSlack (the gate) + one
 * deck slot and bar each side (a rail can only stop on a bar), and the rail covers >= 50 % of the deck span.
 */
function validateV11RailCoverage(ctx) {
  const { make, fmt, spanOverlap, groupAssemblies, unionBox } = ctx.geo;
  const violations = [];
  const band = ctx.limits.v7?.railing_h;
  const decks = ctx.records.filter((r) => r.role === "landing");
  if (!band || decks.length === 0) return { violations, advisories: [] };
  const reach = ctx.L("landingGapMax");
  const slack = ctx.L("ladderHeadSlack");
  const headBand = ctx.L("ladderHeadBand");
  const holeMax = ctx.L("deckGapMax") + ctx.MIN_FEAT;
  const rails = ctx.records.filter((r) => r.role === "railing");
  const extent = (b, fn) => fn(b.max[0] - b.min[0], b.max[2] - b.min[2]);
  const elements = [
    ...ladderGroups(ctx).map((ms) => ({ ms, width: extent(unionBox(ms), Math.max) })),
    ...stringerGroups(ctx).map((ms) => ({ ms, width: extent(unionBox(ms), Math.min) })),
  ];
  for (const deck of groupAssemblies(decks, [0, 1, 2], ctx.L("deckGapMax"))) {
    const { box } = deck;
    const top = box.max[1];
    const front = box.min[2];
    const lo = box.min[0];
    const hi = box.max[0];
    const spans = rails
      // the landing-guard filter: top in the railing band, foot at the deck (a sloped flight rail tops out far above)
      .filter((r) => r.aabb.max[1] >= top + band[0] - 1e-6 && r.aabb.max[1] <= top + band[1] + 1e-6
        && r.aabb.min[1] >= top - reach - 1e-9 && spanOverlap(r.aabb.min[2], r.aabb.max[2], front - reach, front + reach) > -1e-9)
      .map((r) => [Math.max(lo, r.aabb.min[0]), Math.min(hi, r.aabb.max[0])]).filter(([p, q]) => q > p)
      .sort((u, v) => u[0] - v[0]);
    let at = lo;
    let covered = 0;
    const gaps = [];
    for (const [p, q] of [...spans, [hi, hi]]) {
      if (p - at > holeMax + 1e-9) gaps.push([at, p]);
      covered += Math.max(0, q - Math.max(at, p));
      at = Math.max(at, q);
    }
    const share = covered / (hi - lo);
    const wide = [];
    for (const gap of gaps) {
      let width = 0;
      for (const e of elements) {
        const { spans: s } = K.assemble.gateSpans({ box, heads: e.ms.map((m) => m.part.solid), reach, slack, headBand });
        if (s.front.some(([p, q]) => Math.min(q, gap[1]) - Math.max(p, gap[0]) > 0)) width = Math.max(width, e.width);
      }
      const allowed = width + 2 * slack + 2 * holeMax;
      if (gap[1] - gap[0] > allowed + 1e-9) wide.push({ gap, allowed });
    }
    if (share >= 0.5 - 1e-9 && wide.length === 0) continue;
    const first = deck.members[0];
    violations.push(make("V11_RAIL_COVERAGE", first.id,
      [share < 0.5 - 1e-9 ? `front rail covers ${(share * 100).toFixed(0)} % of the span` : null,
        ...wide.map((w) => `opening x ${fmt(w.gap[0])}..${fmt(w.gap[1])} (${fmt(w.gap[1] - w.gap[0])} m > ${fmt(w.allowed)} m)`)].filter(Boolean).join("; "),
      `front rail >= 50 % of the span; each opening <= the arriving element's width + ${fmt(2 * slack + 2 * holeMax)} m`,
      `the landing at y = ${fmt(top)} m ("${first.id}") has lost its front guard to gates wider than what arrives through them — `
      + "a flight lands ON the deck and needs no front gate; build the escape with K.assemble.fireEscape"));
  }
  return { violations, advisories: [] };
}

/**
 * V11_DROP_LADDER — a ladder whose head arrives at a deck (a drop ladder) ends above every canopy (class
 * dropClearRoles, default awning) it crosses in x: one hung down to the street runs through the shopfront awning.
 * (V6 never saw it: the blind ladders stand 0.35 m clear of the awning's lip, so there is no solid overlap.)
 */
function validateV11DropLadder(ctx) {
  const { make, fmt, spanOverlap, unionBox } = ctx.geo;
  const violations = [];
  const clearRoles = ctx.cls.dropClearRoles ?? K.assemble.DEFAULT_TABLE.dropClearRoles;
  const decks = landingLevels(ctx).map((g) => g.box);
  if (decks.length === 0) return { violations, advisories: [] };
  const reach = ctx.L("ladderLandingReach");
  const pad = ctx.L("landingGapMax") + ctx.L("ladderHeadSlack");
  for (const ms of ladderGroups(ctx)) {
    const b = unionBox(ms);
    const deck = decks.find((d) => Math.abs(d.max[1] - b.max[1]) <= reach
      && spanOverlap(b.min[0], b.max[0], d.min[0] - pad, d.max[0] + pad) > 0
      && spanOverlap(b.min[2], b.max[2], d.min[2] - pad, d.max[2] + pad) > -1e-9);
    if (!deck) continue;
    const canopy = ctx.records.find((r) => clearRoles.includes(r.role)
      && spanOverlap(r.aabb.min[0], r.aabb.max[0], b.min[0], b.max[0]) > 0
      && r.aabb.max[1] > b.min[1] + 1e-6 && r.aabb.min[1] < b.max[1]);
    if (!canopy) continue;
    violations.push(make("V11_DROP_LADDER", ms[0].id, `foot y ${fmt(b.min[1])} crosses "${canopy.id}" (top y ${fmt(canopy.aabb.max[1])})`,
      `foot >= ${fmt(canopy.aabb.max[1])} m`,
      `the drop ladder under the deck at y = ${fmt(deck.max[1])} m hangs down past "${canopy.id}" (role ${canopy.role}) — end it above `
      + `the canopy: fireEscape dropLadder.bottom >= the ${canopy.role} top y ${fmt(canopy.aabb.max[1])}`));
  }
  return { violations, advisories: [] };
}

/**
 * WF-BLIND-R2 C2 — ironwork that meets V11 by construction is built by K.assemble.landing / flight / ladder. A
 * landing, stringer or ladder part the helpers did not produce (no `assembly` tag) is reported, never blocked.
 */
function validateHandbuilt(ctx) {
  const { advise } = ctx.geo;
  const hand = ctx.records.filter((r) => ["landing", "stringer", "ladder"].includes(r.role) && !r.part.assembly);
  if (hand.length === 0) return { violations: [], advisories: [] };
  return {
    violations: [],
    advisories: [advise("V11_HANDBUILT", hand[0].id, `${hand.length} landing/stringer/ladder part(s) not built by K.assemble`,
      "K.assemble.fireEscape / ladder",
      "landings, flights and ladders built with K.assemble.fireEscape / ladder pass the V11 rows by construction; hand-placed ironwork is where ladder access and landing guards trade against each other")],
  };
}

export const validators = Object.freeze([
  ["V7", validateV7Rows],
  // r1 rows 2, 7, 8, 9 — buildability, after the model is known to stand up and
  // before it is counted: there is no point counting parts of a deck nobody can
  // stand on.
  ["V11_BEARING", validateV11Bearing],
  ["V11_LANDING_GAP", validateV11LandingGap],
  ["V11_LADDER_ACCESS", validateV11LadderAccess],
  ["V11_DECK_GAP", validateV11DeckGap],
  ["V11_LANDING_GUARD", validateV11LandingGuard],
  ["V11_FLIGHT_ON_DECK", validateV11FlightOnDeck],
  ["V11_RAIL_COVERAGE", validateV11RailCoverage],
  ["V11_DROP_LADDER", validateV11DropLadder],
  ["V11_HANDBUILT", validateHandbuilt],
]);

// ---------------------------------------------------------------------------
// V12_LAYOUT measures — see the V12_LAYOUT comment in kernel-chain.mjs for the
// row itself. The frame: W, H, the -Z brick plane, and the coping line.
// ---------------------------------------------------------------------------

// WF-BLIND-R2 C3 — the start module's planes and every cited layout key in author-frame METRES, printed in the
// prompt next to MEASURED NUMBERS (blind Gemini reasoned at length about street-left/right and x signs).
const m3 = (v) => `${v >= 0 ? "+" : ""}${(Math.round(v * 1000) / 1000).toFixed(3)}`;

/** One line: the planes of the module's massing (null before P0 builds one). */
export function layoutPlanes(ctx, F) {
  if (!F) return null;
  const massing = ctx.records.filter((r) => r.role === "massing");
  const back = Math.max(...massing.map((r) => r.aabb.max[2]));
  return `front face z = ${m3(F.faceZ)}, back face z = ${m3(back)}, street-right side x = ${m3(F.x0)} (min x), `
    + `street-left side x = ${m3(F.x0 + F.W)} (max x), ground y = ${m3(F.y0)}, wall top y = ${m3(F.wallTop)}, `
    + `coping top y = ${m3(F.copingTop)}; W = ${m3(F.W)} m, H = ${m3(F.H)} m, depth = ${m3(back - F.faceZ)} m`;
}

/** A layout entry's value(s) as author-frame metres, or null for a unit that has none. */
export function layoutAbsolute(key, entry, F) {
  if (!F || !entry || entry.unverified) return null;
  const values = Array.isArray(entry.values) ? entry.values : (Number.isFinite(entry.value) ? [entry.value] : null);
  if (!values) return null;
  const list = (fn) => values.map(fn).join(" / ");
  const unit = entry.unit ?? "";
  if (unit === "W") {
    if (/centreX$/.test(key)) return `x = ${list((v) => m3(F.x0 + v * F.W))} m (x0 ${m3(F.x0)} + value x W)`;
    if (key === "ladder.roof.backFromCorner") return `z = ${list((v) => m3(F.faceZ + v * F.W))} m (front face z + value x W)`;
    return `${list((v) => m3(v * F.W))} m long`;
  }
  if (unit === "x W") return `${list((v) => m3(v * F.W))} m`;
  if (unit === "H") {
    if (/\.(top|bottom)$/.test(key)) return `y = ${list((v) => m3(F.y0 + v * F.H))} m (ground + value x H)`;
    if (key === "window.headBelowCoping") return `window head y = ${list((v) => m3(F.wallTop - v * F.H))} m (wall top - value x H)`;
    if (key === "ladder.topBelowCoping") return `ladder top y = ${list((v) => m3(F.copingTop - v * F.H))} m (coping top - value x H)`;
    // WF-R3 C15 — the deck-top DATUM per level: the start module's window rows (their lowest member) + value x H.
    if (key === "landing.rowY") {
      const rows = F.windowRowBottoms ?? [];
      if (rows.length === 0) return `${list((v) => m3(v * F.H))} m from the nearest window sill to the deck top`;
      return `deck top y = ${rows.map((b) => values.map((v) => m3(b + v * F.H)).join(" / ")).join(", ")} m (window row bottom y ${rows.map(m3).join(", ")} + value x H), bottom level first`;
    }
    return `${list((v) => m3(v * F.H))} m`;
  }
  return null;
}

export function layoutFrame(ctx) {
  const massing = ctx.records.filter((r) => r.role === "massing");
  if (massing.length === 0) return null;
  const lo = (axis) => Math.min(...massing.map((r) => r.aabb.min[axis]));
  const hi = (axis) => Math.max(...massing.map((r) => r.aabb.max[axis]));
  const W = hi(0) - lo(0);
  const H = hi(1) - lo(1);
  if (!(W > 0) || !(H > 0)) return null;
  const crown = ctx.records.filter((r) => ["roof", "parapet", "cornice"].includes(r.role));
  // WF-R3 C15 — window ROWS as merged y intervals (bottom first): the datum landing.rowY hangs the decks from.
  const rows = [];
  for (const r of ctx.records.filter((x) => x.role === "window").sort((a, b) => a.aabb.min[1] - b.aabb.min[1])) {
    const last = rows[rows.length - 1];
    if (last && r.aabb.min[1] <= last[1] + 1e-9) last[1] = Math.max(last[1], r.aabb.max[1]);
    else rows.push([r.aabb.min[1], r.aabb.max[1]]);
  }
  return {
    windowRowBottoms: rows.map(([lo]) => lo),
    W, H, x0: lo(0), y0: lo(1),
    faceZ: lo(2),                                     // the populated -Z plane
    wallTop: hi(1),                                   // where the coping sits
    copingTop: crown.length > 0 ? Math.max(...crown.map((r) => r.aabb.max[1])) : hi(1),
  };
}

const boxExtent = (box, axis) => box.max[axis] - box.min[axis];
const boxMid = (box, axis) => (box.min[axis] + box.max[axis]) / 2;

const roleGroups = (ctx, role, axes = [0, 1], pad = 0) =>
  ctx.geo.groupAssemblies(ctx.records.filter((r) => r.role === role), axes, pad)
    .sort((a, b) => (a.box.min[0] - b.box.min[0]) || (a.box.min[1] - b.box.min[1]));

/** Window ROWS as y-centre bands, bottom first. */
const windowRows = (ctx) => ctx.geo.clusters(roleGroups(ctx, "window").map((g) => boxMid(g.box, 1)), ctx.L("censusRowBand"));

/**
 * The ROOF ladder is the ladder assembly that climbs highest; the drop ladder
 * under a deck is not measured against the coping or the corner.
 */
function roofLadder(ctx) {
  return roleGroups(ctx, "ladder", [0], 0.7).reduce((a, b) => (a.box.max[1] >= b.box.max[1] ? a : b));
}

/**
 * layout key -> what it measures. `roles` gates the key: a role with no parts
 * yet means the pass that builds it has not run, so the key stands down.
 * `measure` returns `[{id, measured}]`, already in the key's unit.
 */
// Fable ruling (r2, Job B item 1): window.w / window.h are the GLASS (the audit
// measured the visible pane), not the frame+glass assembly — else 0.16 W glass and
// a 0.25× frame could never both hold. The pane = the zone "glass" member, or the
// member with the smallest x extent when no member is painted glass.
const paneOf = (g) => g.members.find((m) => m.zone === "glass")
  ?? g.members.reduce((a, b) => ((b.aabb.max[0] - b.aabb.min[0]) < (a.aabb.max[0] - a.aabb.min[0]) ? b : a));

/** Union AABB of every part of one role. */
const roleBox = (ctx, role) => ctx.geo.unionBox(ctx.records.filter((r) => r.role === role));

/** Landing deck LEVELS (landing-role members grouped by y overlap), bottom first. */
const landingLevels = (ctx) => ctx.geo.groupAssemblies(ctx.records.filter((r) => r.role === "landing"), [1])
  .sort((a, b) => a.box.min[1] - b.box.min[1]);

export const layoutRules = Object.freeze({
  "window.w": {
    roles: ["window"], unit: "W",
    measure: (ctx, F) => roleGroups(ctx, "window").map((g) => { const p = paneOf(g); return { id: p.id, measured: (p.aabb.max[0] - p.aabb.min[0]) / F.W }; }),
  },
  "window.h": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => roleGroups(ctx, "window").map((g) => { const p = paneOf(g); return { id: p.id, measured: (p.aabb.max[1] - p.aabb.min[1]) / F.H }; }),
  },
  // r3 C1.3: from the STREET-RIGHT edge of the face. Author -x is street-right,
  // so F.x0 (the massing's min x) IS that edge and no sign flip is needed — the
  // scan's (x1 - cx)/W and this (x - F.x0)/F.W are the same fraction.
  "window.centreX": {
    roles: ["window"], unit: "W", list: "window bay centres",
    measure: (ctx, F) => ctx.geo.clusters(roleGroups(ctx, "window").map((g) => boxMid(g.box, 0)), 0.05 * F.W)
      .map((x) => ({ id: null, measured: (x - F.x0) / F.W })),
  },
  "window.headBelowCoping": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => {
      const top = Math.max(...roleGroups(ctx, "window").map((g) => g.box.max[1]));
      return [{ id: null, measured: (F.wallTop - top) / F.H }];
    },
  },
  "window.rowPitch": {
    roles: ["window"], unit: "H",
    measure: (ctx, F) => {
      const rows = windowRows(ctx);
      if (rows.length < 2) return [];
      return [{ id: null, measured: (rows[rows.length - 1] - rows[0]) / (rows.length - 1) / F.H }];
    },
  },
  "frame.widthRatio": {
    roles: ["window"], unit: "x glass width",
    measure: (ctx) => roleGroups(ctx, "window").map((g) => {
      const widths = g.members.map((m) => m.aabb.max[0] - m.aabb.min[0]);
      const glass = Math.min(...widths);
      if (!(glass > 0)) return null;
      return { id: g.members[0].id, measured: (Math.max(...widths) - glass) / 2 / glass };
    }).filter(Boolean),
  },
  "frame.proud": {
    roles: ["window"], unit: "m",
    measure: (ctx, F) => roleGroups(ctx, "window").map((g) => ({ id: g.members[0].id, measured: F.faceZ - g.box.min[2] })),
  },
  // run3 P2: the target's roof reads large because the block is DEEP; a shallow
  // footprint passed every face-plane key and still looked wrong (LK_AREA roof 7.8 %
  // vs 20.2 %). Depth over face width, measured on the massing z extent.
  "massing.depthOverW": {
    roles: ["massing"], unit: "x W",
    measure: (ctx, F) => {
      const m = ctx.records.filter((r) => r.role === "massing");
      const d = Math.max(...m.map((r) => r.aabb.max[2])) - Math.min(...m.map((r) => r.aabb.min[2]));
      return [{ id: null, measured: d / F.W }];
    },
  },
  "cornice.projection": {
    roles: ["cornice"], unit: "W",
    measure: (ctx, F) => {
      const front = ctx.records.filter((r) => r.role === "cornice")
        .reduce((a, b) => (a.aabb.min[2] <= b.aabb.min[2] ? a : b));
      return [{ id: front.id, measured: (F.faceZ - front.aabb.min[2]) / F.W }];
    },
  },
  "crown.height": {
    roles: ["parapet"], unit: "H",
    measure: (ctx, F) => [{ id: null, measured: (F.copingTop - F.wallTop) / F.H }],
  },
  "landing.depth": {
    roles: ["landing"], unit: "W",
    measure: (ctx, F) => ctx.geo.groupAssemblies(ctx.records.filter((r) => r.role === "landing"), [1])
      .sort((a, b) => a.box.min[1] - b.box.min[1])
      .map((g) => ({ id: g.members[0].id, measured: boxExtent(g.box, 2) / F.W })),
  },
  "landing.rowY": {
    roles: ["landing", "window"], unit: "H",
    measure: (ctx, F) => {
      const sills = roleGroups(ctx, "window").map((g) => g.box.min[1]);
      return ctx.geo.groupAssemblies(ctx.records.filter((r) => r.role === "landing"), [1])
        .sort((a, b) => a.box.min[1] - b.box.min[1])
        .map((g) => {
          const top = g.box.max[1];
          const near = sills.reduce((a, b) => (Math.abs(b - top) < Math.abs(a - top) ? b : a));
          return { id: g.members[0].id, measured: (top - near) / F.H };
        });
    },
  },
  "signbox.h": {
    roles: ["signbox"], unit: "H",
    measure: (ctx, F) => roleGroups(ctx, "signbox").map((g) => ({ id: g.members[0].id, measured: boxExtent(g.box, 1) / F.H })),
  },
  "signbox.top": {
    roles: ["signbox"], unit: "H",
    measure: (ctx, F) => roleGroups(ctx, "signbox").map((g) => ({ id: g.members[0].id, measured: (g.box.max[1] - F.y0) / F.H })),
  },
  "awning.span": {
    roles: ["awning"], unit: "W",
    measure: (ctx, F) => {
      const box = ctx.geo.unionBox(ctx.records.filter((r) => r.role === "awning"));
      return [{ id: null, measured: boxExtent(box, 0) / F.W }];
    },
  },
  // r3 C1.1(c): the shop stack is four SEPARATE bands in the target and one
  // collapsed lump in run 3 (fable-audit L3), so the canopy's own top and
  // bottom are keys now, not a span alone.
  "awning.top": {
    roles: ["awning"], unit: "H",
    measure: (ctx, F) => [{ id: null, measured: (ctx.geo.unionBox(ctx.records.filter((r) => r.role === "awning")).max[1] - F.y0) / F.H }],
  },
  "awning.bottom": {
    roles: ["awning"], unit: "H",
    measure: (ctx, F) => [{ id: null, measured: (ctx.geo.unionBox(ctx.records.filter((r) => r.role === "awning")).min[1] - F.y0) / F.H }],
  },
  "storefront.h": {
    roles: ["storefront"], unit: "H",
    measure: (ctx, F) => roleGroups(ctx, "storefront").map((g) => ({ id: g.members[0].id, measured: boxExtent(g.box, 1) / F.H })),
  },
  // WF-BLIND-R2 C5 — the shop pane's bottom edge over the ground, the pane (like storefront.w), from F.y0.
  "storefront.bottom": {
    roles: ["storefront"], unit: "H",
    measure: (ctx, F) => roleGroups(ctx, "storefront").map((g) => { const p = paneOf(g); return { id: p.id, measured: (p.aabb.min[1] - F.y0) / F.H }; }),
  },
  "door.h": {
    roles: ["door"], unit: "H",
    measure: (ctx, F) => roleGroups(ctx, "door").map((g) => ({ id: g.members[0].id, measured: boxExtent(g.box, 1) / F.H })),
  },
  // v3-backlog (a): the keys the v3 proof ran on class defaults. Widths of an
  // opening are its PANE (like window.w); every centre is from the STREET-RIGHT
  // edge (F.x0), like window.centreX; sign box and AC are their role's union box.
  "storefront.w": {
    roles: ["storefront"], unit: "W",
    measure: (ctx, F) => roleGroups(ctx, "storefront").map((g) => { const p = paneOf(g); return { id: p.id, measured: boxExtent(p.aabb, 0) / F.W }; }),
  },
  "storefront.centreX": {
    roles: ["storefront"], unit: "W",
    measure: (ctx, F) => roleGroups(ctx, "storefront").map((g) => ({ id: g.members[0].id, measured: (boxMid(g.box, 0) - F.x0) / F.W })),
  },
  "door.w": {
    roles: ["door"], unit: "W",
    measure: (ctx, F) => roleGroups(ctx, "door").map((g) => { const p = paneOf(g); return { id: p.id, measured: boxExtent(p.aabb, 0) / F.W }; }),
  },
  "door.centreX": {
    roles: ["door"], unit: "W",
    measure: (ctx, F) => roleGroups(ctx, "door").map((g) => ({ id: g.members[0].id, measured: (boxMid(g.box, 0) - F.x0) / F.W })),
  },
  "signbox.w": {
    roles: ["signbox"], unit: "W",
    measure: (ctx, F) => [{ id: null, measured: boxExtent(roleBox(ctx, "signbox"), 0) / F.W }],
  },
  "signbox.centreX": {
    roles: ["signbox"], unit: "W",
    measure: (ctx, F) => [{ id: null, measured: (boxMid(roleBox(ctx, "signbox"), 0) - F.x0) / F.W }],
  },
  "ac.w": {
    roles: ["ac"], unit: "W",
    measure: (ctx, F) => [{ id: null, measured: boxExtent(roleBox(ctx, "ac"), 0) / F.W }],
  },
  "ac.h": {
    roles: ["ac"], unit: "H",
    measure: (ctx, F) => [{ id: null, measured: boxExtent(roleBox(ctx, "ac"), 1) / F.H }],
  },
  "ac.top": {
    roles: ["ac"], unit: "H",
    measure: (ctx, F) => [{ id: null, measured: (roleBox(ctx, "ac").max[1] - F.y0) / F.H }],
  },
  "ac.centreX": {
    roles: ["ac"], unit: "W",
    measure: (ctx, F) => [{ id: null, measured: (boxMid(roleBox(ctx, "ac"), 0) - F.x0) / F.W }],
  },
  "ac.depth": {
    roles: ["ac"], unit: "x W",
    measure: (ctx, F) => [{ id: null, measured: boxExtent(roleBox(ctx, "ac"), 2) / F.W }],
  },
  // One measurement per deck level, like landing.depth.
  "landing.span": {
    roles: ["landing"], unit: "W",
    measure: (ctx, F) => landingLevels(ctx).map((g) => ({ id: g.members[0].id, measured: boxExtent(g.box, 0) / F.W })),
  },
  "landing.centreX": {
    roles: ["landing"], unit: "W",
    measure: (ctx, F) => landingLevels(ctx).map((g) => ({ id: g.members[0].id, measured: (boxMid(g.box, 0) - F.x0) / F.W })),
  },
  "face.aspect": {
    roles: ["massing"], unit: "W/H",
    measure: (ctx, F) => [{ id: null, measured: F.W / F.H }],
  },
  "ladder.topBelowCoping": {
    roles: ["ladder"], unit: "H",
    measure: (ctx, F) => {
      const roof = roofLadder(ctx);
      return [{ id: roof.members[0].id, measured: (F.copingTop - roof.box.max[1]) / F.H }];
    },
  },
  // r3 C1.3 (Fable M5 / audit L5): the target's roof ladder climbs the SIDE
  // return, 0.18 W behind the front plane. Run 3 built it on the front face,
  // 0.25 m in front of the brick — a ladder in the air — and LK_OVERLAP passed
  // vacuously because nothing was over the face to overlap.
  "ladder.roof.face": {
    roles: ["ladder"], unit: "face",
    mismatchHint: "the target's roof ladder stands on the street-left SIDE wall, behind the front plane",
    measure: (ctx, F) => {
      const roof = roofLadder(ctx);
      const cx = boxMid(roof.box, 0);
      const measured = cx > F.x0 + F.W ? "side" : (cx < F.x0 ? "side-street-right" : "front");
      return [{ id: roof.members[0].id, measured }];
    },
  },
  // WF-R3 C15 — the roof ladder's FOOT over the ground (measure-target walks the stile contour down): a ladder
  // built ground-to-roof, or stopped short, is a layout row, not a prose rule.
  "ladder.roof.bottom": {
    roles: ["ladder"], unit: "H",
    measure: (ctx, F) => {
      const roof = roofLadder(ctx);
      return [{ id: roof.members[0].id, measured: (roof.box.min[1] - F.y0) / F.H }];
    },
  },
  // V5-7: member PITCHES (the target's ink profile; they set the member counts). Front-run balusters of each PLATE
  // deck (one landing member per level — on a grating a baluster stands on a bar, so its pitch is the bar pitch's
  // multiple and the key cannot bind it), standing on it at its front edge, median x gap; the roof ladder's rungs,
  // median y gap.
  "landing.balusterPitch": {
    roles: ["baluster"], unit: "W",
    measure: (ctx, F) => landingLevels(ctx).filter((g) => g.members.length === 1).flatMap((g) => {
      const xs = ctx.records.filter((r) => r.role === "baluster" && Math.abs(r.aabb.min[1] - g.box.max[1]) <= 0.1
        && r.aabb.min[2] <= g.box.min[2] + 0.1).map((r) => boxMid(r.aabb, 0)).sort((a, b) => a - b);
      if (xs.length < 3) return [];
      const gaps = xs.slice(1).map((x, i) => x - xs[i]).sort((a, b) => a - b);
      return [{ id: g.members[0].id, measured: gaps[Math.floor((gaps.length - 1) / 2)] / F.W }];
    }),
  },
  "ladder.roof.rungPitch": {
    roles: ["rung"], unit: "H",
    measure: (ctx, F) => {
      const roof = roofLadder(ctx);
      const b = roof.box;
      const ys = ctx.records.filter((r) => r.role === "rung" && r.aabb.max[0] >= b.min[0] - 0.1 && r.aabb.min[0] <= b.max[0] + 0.1
        && r.aabb.max[2] >= b.min[2] - 0.1 && r.aabb.min[2] <= b.max[2] + 0.1 && r.aabb.min[1] >= b.min[1] - 1e-6 && r.aabb.max[1] <= b.max[1] + 1e-6)
        .map((r) => boxMid(r.aabb, 1)).sort((u, v) => u - v);
      if (ys.length < 3) return [];
      const gaps = ys.slice(1).map((y, i) => y - ys[i]).sort((u, v) => u - v);
      return [{ id: roof.members[0].id, measured: gaps[Math.floor((gaps.length - 1) / 2)] / F.H }];
    },
  },
  "ladder.roof.backFromCorner": {
    roles: ["ladder"], unit: "W",
    measure: (ctx, F) => {
      const roof = roofLadder(ctx);
      return [{ id: roof.members[0].id, measured: (boxMid(roof.box, 2) - F.faceZ) / F.W }];
    },
  },
});
