// V6 — overlap and containment.
//
// MVP-STUB: AABB not OBB. The intersection volume is computed on the world
// AABBs compile() already wrote, so a rotated part over-reports its overlap.
// Every M0 layout has rot = 0, where AABB == OBB. Exact OBB clipping (or the
// manifold-3d intersection PLAN.md 2 wants) lands with the rotated composites
// in M2.
//
// DEVIATION (M1): the clash exemption is the whole ATTACH ANCESTRY, not just
// the direct parent. `stoop_step_2` rests on `stoop_step_1`, which is socketed
// 0.1 m into `mass_l`; step 2 inherits that penetration and overlaps mass_l by
// 22 % of its own volume. A direct-parent-only rule calls the M0 massing a
// clash, which contradicts the acceptance criterion that it passes clean.
import { aabbOverlapVolume, aabbVolume } from "./obb.js";

export function validateV6(ctx, make) {
  const { parts, ancestors, limits } = ctx;
  const violations = [];

  for (let i = 0; i < parts.length; i += 1) {
    for (let j = i + 1; j < parts.length; j += 1) {
      const a = parts[i];
      const b = parts[j];
      const overlap = aabbOverlapVolume(a, b);
      if (overlap <= 0) continue;

      const smaller = Math.min(aabbVolume(a), aabbVolume(b));
      if (smaller <= 0) continue;
      const ratio = overlap / smaller;

      // An `embedded` child is DECLARED to live inside its parent (a hub in a
      // tyre's bore). DEVIATION (M5): PLAN 2 exempts embedded from the clash
      // band only, but the duplicate band would delete the hub outright — V6
      // reads AABBs and cannot see the bore it sits in. The exemption is tight:
      // it applies only between an `embedded` part and its own attach ancestry.
      if ((a.contact === "embedded" || b.contact === "embedded") && related(ancestors, a, b)) continue;

      if (ratio > limits.overlapDuplicate) {
        // Ties go to the later-declared part: the original keeps its id.
        const contained = aabbVolume(a) < aabbVolume(b) ? a : b;
        const host = contained === a ? b : a;
        violations.push(make("V6", contained.id, `${(ratio * 100).toFixed(1)}% contained`, `<= ${(limits.overlapDuplicate * 100).toFixed(0)}%`,
          `delete "${contained.id}" — it is ${(ratio * 100).toFixed(1)}% inside "${host.id}" and renders as nothing`));
        continue;
      }

      if (ratio <= limits.overlapClash) continue;
      if (related(ancestors, a, b)) continue;
      if (a.contact === "socket" || b.contact === "socket") continue;

      violations.push(make("V6", a.id, `${(ratio * 100).toFixed(1)}% intersection with "${b.id}"`, `<= ${(limits.overlapClash * 100).toFixed(0)}% unless socketed`,
        `"${a.id}" and "${b.id}" interpenetrate by ${(ratio * 100).toFixed(1)}% of the smaller part with no declared socket — move one apart or declare the contact`));
    }
  }

  return { violations, advisories: [] };
}

function related(ancestors, a, b) {
  if (a.specId === b.specId) return true;
  return (ancestors.get(a.specId) ?? new Set()).has(b.specId)
    || (ancestors.get(b.specId) ?? new Set()).has(a.specId);
}
