// V9 — symmetry when the role implies it (PLAN.md 2, M5).
//
// ADVISORY ONLY, always. A one-wheeled truck is a modelling mistake the author
// should see, but it is not a compile error and it must never stop a round
// (PLAN 2: "advise", no auto-repair, no re-prompt). `index.js` therefore hands
// this validator the `advise` factory, and runs it last.
//
// Scope: only classes in `limits.symmetricClasses` (vehicle, robot) and only
// roles in `limits.v9.roles`. A part that declares `mirror: true` has already
// said what V9 wants to hear and is skipped without measuring anything.
//
// The mirror plane is x = the model's own bounds centre, not world x = 0: a
// vehicle authored a metre off the origin is still symmetric about itself. Left
// and right are X because a road wheel's axle runs along X (parts/lib/wheel.json),
// which puts a vehicle's length along Z.
//
// MVP-STUB: the twin test compares world AABBs, not geometry. Two boxes of the
// same size mirrored across the centre line satisfy it whatever their prims are
// — enough to catch "there is only one of these", which is what the rule is for.

/** Every solved instance that came from one authored part (or composite). */
function worldBox(parts, id) {
  const prefix = `${id}.`;
  let box = null;
  for (const part of parts) {
    if (part.specId !== id && !part.specId.startsWith(prefix)) continue;
    if (!part.aabb) continue;
    if (!box) {
      box = { min: [...part.aabb.min], max: [...part.aabb.max] };
      continue;
    }
    for (let i = 0; i < 3; i += 1) {
      box.min[i] = Math.min(box.min[i], part.aabb.min[i]);
      box.max[i] = Math.max(box.max[i], part.aabb.max[i]);
    }
  }
  return box;
}

/** The X-mirror of a box about the plane x = centre. */
function mirrorX(box, centre) {
  return {
    min: [2 * centre - box.max[0], box.min[1], box.min[2]],
    max: [2 * centre - box.min[0], box.max[1], box.max[2]],
  };
}

function boxesAgree(a, b, tolerance) {
  for (let i = 0; i < 3; i += 1) {
    if (Math.abs(a.min[i] - b.min[i]) > tolerance) return false;
    if (Math.abs(a.max[i] - b.max[i]) > tolerance) return false;
  }
  return true;
}

export function validateV9(ctx, advise) {
  const { spec, parts, solved, limits, EPS } = ctx;
  const advisories = [];

  const classes = limits.symmetricClasses ?? [];
  const roles = limits.v9?.roles ?? [];
  if (!classes.includes(spec.class) || roles.length === 0) return { violations: [], advisories };

  // Composites are checked as the thing the author wrote ("a wheel"), the same
  // way V7 applies its role table to the authored composite.
  const candidates = [...(spec.parts ?? []), ...(spec.composites ?? [])]
    .filter((part) => roles.includes(part.role))
    .map((part) => ({ part, box: worldBox(parts, part.id) }))
    .filter((entry) => entry.box !== null);

  const centre = solved.bounds.centre[0];
  const tolerance = 2 * EPS;

  for (const entry of candidates) {
    if (entry.part.mirror === true) continue;
    const wanted = mirrorX(entry.box, centre);
    // A part that is its own mirror (a centred part spanning the plane) counts:
    // it is already symmetric, so it is included in its own twin search.
    const twin = candidates.some((other) => other.part.role === entry.part.role
      && boxesAgree(other.box, wanted, tolerance));
    if (twin) continue;

    const span = `x ${entry.box.min[0].toFixed(3)}..${entry.box.max[0].toFixed(3)} m`;
    advisories.push(advise("V9", entry.part.id, `1 part with role "${entry.part.role}" at ${span}`,
      `a twin mirrored about x = ${centre.toFixed(3)} m (within ${tolerance.toFixed(3)} m)`,
      `"${entry.part.id}" (role ${entry.part.role}) has no mirror twin on a ${spec.class} — set "mirror": true on it, or add the opposite-side part at x ${wanted.min[0].toFixed(3)}..${wanted.max[0].toFixed(3)} m`));
  }

  return { violations: [], advisories };
}
