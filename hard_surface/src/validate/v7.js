// V7 — relative-scale logic, keyed by `role`. Numbers live in limits.v7 and are
// owner-gated: this validator never repairs, it re-prompts (PLAN.md 2, 02:T3).
//
// A rule whose role is absent from the spec is skipped, so the railing / window
// / awning rules ship as data now and start biting the moment M2 authors those
// roles.
export function validateV7(ctx, make) {
  const { spec, parts, limits, solved } = ctx;
  const table = limits.v7;
  const violations = [];

  // A composite is expanded before anything measures it, and none of a
  // railing's four sub-parts is 0.95 m tall — so the role table is applied to
  // the AUTHORED composite as well, which is the thing the rule is about.
  const roleParts = [...spec.parts, ...(spec.composites ?? [])];

  const range = (role, key, label) => {
    const bounds = table[key];
    if (!bounds) return;
    for (const part of roleParts) {
      if (part.role !== role) continue;
      const h = part.dims[1];
      if (h < bounds[0] - 1e-9 || h > bounds[1] + 1e-9) {
        violations.push(make("V7", part.id, `${label} ${h.toFixed(3)} m`, `${bounds[0]}..${bounds[1]} m`,
          `"${part.id}" (role ${role}) has ${label} ${h.toFixed(3)} m, outside the ${bounds[0]}..${bounds[1]} m rule — resize it`));
      }
    }
  };

  range("door", "door_h", "height");
  range("step", "step_rise", "rise");
  range("parapet", "parapet_h", "height");
  range("railing", "railing_h", "height");

  if (table.window_h_lt_floorH) {
    for (const part of spec.parts) {
      if (part.role !== "window" || !part.attach) continue;
      const host = spec.parts.find((p) => p.id === part.attach.to);
      if (!host) continue;
      if (part.dims[1] >= host.dims[1] - 1e-9) {
        violations.push(make("V7", part.id, `height ${part.dims[1].toFixed(3)} m`, `< host floor height ${host.dims[1].toFixed(3)} m`,
          `"${part.id}" (role window) is as tall as "${part.attach.to}" — a window must be shorter than its floor`));
      }
    }
  }

  if (table.awning_bottom_ge_door_top) {
    const doors = parts.filter((p) => p.role === "door");
    const awnings = parts.filter((p) => p.role === "awning");
    if (doors.length > 0) {
      const doorTop = Math.max(...doors.map((p) => p.aabb.max[1]));
      for (const awning of awnings) {
        if (awning.aabb.min[1] < doorTop - 1e-9) {
          violations.push(make("V7", awning.id, `bottom ${awning.aabb.min[1].toFixed(3)} m`, `>= door top ${doorTop.toFixed(3)} m`,
            `raise "${awning.id}" to ${doorTop.toFixed(3)} m — an awning below the door head blocks the door`));
        }
      }
    }
  }

  // --- M5 vehicle rules -----------------------------------------------------
  // These three are measured on the SOLVED parts, not on the authored dims,
  // because two of them are about where the wheels ended up. A rule whose role
  // is absent is skipped, exactly like the building rules above.
  const bounds = solved?.bounds ?? null;
  const byRole = (role) => parts.filter((p) => p.role === role);
  const firstPerSpecId = (list) => {
    const seen = new Set();
    return list.filter((p) => (seen.has(p.specId) ? false : (seen.add(p.specId), true)));
  };
  // Fable ruling 2026-09-12: the vehicle rows apply to class "vehicle" only — a
  // prop cart or a robot may carry any wheel it likes.
  const wheels = spec?.class === "vehicle" ? byRole("wheel") : [];

  // Length is the longer horizontal extent: a wheel rolls about X (see
  // parts/lib/wheel.json), so a vehicle's length runs along Z and its width
  // along X, and `max(w, d)` picks the length whichever way it was authored.
  const length = bounds ? Math.max(bounds.w, bounds.d) : 0;

  if (table.wheel_diameter_frac_of_length && wheels.length > 0 && length > 0) {
    const [lo, hi] = table.wheel_diameter_frac_of_length;
    for (const wheel of firstPerSpecId(wheels)) {
      // The wheel's two DIAMETER axes are the two largest of its dims; the third
      // is its width (the axle direction).
      const diameter = Math.max(...[...wheel.dims].sort((a, b) => b - a).slice(0, 2));
      const radius = diameter / 2;
      const frac = diameter / length;   // Fable ruling 2026-09-12: DIAMETER / length; band unchanged, still unratified
      if (frac < lo - 1e-9 || frac > hi + 1e-9) {
        violations.push(make("V7", wheel.specId, `radius ${radius.toFixed(3)} m = ${frac.toFixed(3)} of the ${length.toFixed(3)} m length`,
          `${lo}..${hi} of length`,
          `resize "${wheel.specId}" (role wheel) to diameter ${(lo * length).toFixed(3)}..${(hi * length).toFixed(3)} m — a wheel that is ${frac.toFixed(3)} of the vehicle's length reads as the wrong vehicle`));
      }
    }
  }

  if (table.ground_clearance && wheels.length > 0) {
    const [lo, hi] = table.ground_clearance;
    // The wheel bottoms ARE the ground for a vehicle: the chassis is measured
    // off them, not off world y = 0 (a wheel hung below a ground chassis puts
    // the whole model's datum under the world plane).
    const datum = Math.min(...wheels.map((w) => w.aabb.min[1]));
    for (const chassis of firstPerSpecId(byRole("chassis"))) {
      const clearance = chassis.aabb.min[1] - datum;
      if (clearance < lo - 1e-9 || clearance > hi + 1e-9) {
        violations.push(make("V7", chassis.specId, `ground clearance ${clearance.toFixed(3)} m`, `${lo}..${hi} m`,
          `move "${chassis.specId}" (role chassis) to ${(datum + lo).toFixed(3)}..${(datum + hi).toFixed(3)} m above the wheel bottoms — it currently rides ${clearance.toFixed(3)} m off the ground`));
      }
    }
  }

  // MVP-STUB: with every prim inside its own declared box, a cab's height can
  // never exceed the bounds it is itself part of, so this rule is an invariant
  // guard rather than a live check. It ships because the limits key is
  // owner-dictated (M5 brief item 3) and because a future prim that escapes its
  // box would trip it. See the report: the owner may have meant a fraction.
  if (table.cab_h_le_total_h && bounds) {
    for (const cab of firstPerSpecId(byRole("cab"))) {
      if (cab.dims[1] > bounds.h + 1e-9) {
        violations.push(make("V7", cab.specId, `cab height ${cab.dims[1].toFixed(3)} m`, `<= total height ${bounds.h.toFixed(3)} m`,
          `shrink "${cab.specId}" (role cab) below the vehicle's total height ${bounds.h.toFixed(3)} m`));
      }
    }
  }

  return { violations, advisories: [] };
}
