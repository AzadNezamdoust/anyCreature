// V5 — minimum feature size, in metres AND in capture pixels.
//
// MIN_FEAT = max(styleFloor[class], minFeaturePx * PX) and
// PX = (bounds.h / fill) / captureSize — the world size of one pixel of the
// frozen 900 px capture. NOTE: app.js frameTarget() sizes the ortho frustum from
// the PROJECTED AABB (its M0 DEVIATION comment says why), so for a wide subject
// seen at 45 deg the real frustum is larger and the real pixel is coarser than
// this. PX here is therefore a floor: V5 can under-report a sub-pixel feature,
// never invent one. Matching frameTarget exactly needs the camera solve, which
// is a browser input the node gate does not have.
import * as THREE from "three";

import { partBox, projRadius } from "./obb.js";

export function validateV5(ctx, make) {
  const { spec, byId, MIN_FEAT, PX, limits } = ctx;
  const violations = [];

  for (const part of spec.parts) {
    const solved = byId.get(part.id);
    if (!solved) continue;

    const min = Math.min(...part.dims);
    if (min < MIN_FEAT - 1e-9) {
      const axis = ["w", "h", "d"][part.dims.indexOf(min)];
      violations.push(make("V5", part.id, `${fmt(min)} m (${(min / PX).toFixed(1)} px)`, `>= ${fmt(MIN_FEAT)} m`,
        `grow "${part.id}" ${axis} from ${fmt(min)} m to ${fmt(MIN_FEAT)} m — thinner than the style floor and under ${limits.minFeaturePx} px at capture`));
    }

    if (part.repeat && solved.worldRepeatAxis) {
      const direction = new THREE.Vector3().fromArray(solved.worldRepeatAxis);
      const extent = 2 * projRadius(partBox(solved), direction);
      const gap = Number(part.repeat.pitch) - extent;
      if (gap < 2 * PX - 1e-12) {
        const run = (part.repeat.count - 1) * part.repeat.pitch + extent;
        violations.push(make("V5", part.id, `repeat gap ${fmt(gap)} m (${(gap / PX).toFixed(1)} px)`, `>= ${fmt(2 * PX)} m (2 px)`,
          `collapse the repeat on "${part.id}" to one block ${fmt(run)} m along ${part.repeat.axis} with a stripe zone — ${part.repeat.count} instances ${fmt(gap)} m apart are sub-pixel at capture`));
      }
    }
  }

  return { violations, advisories: [] };
}

function fmt(value) {
  return (Math.round(value * 1000) / 1000).toFixed(3);
}
