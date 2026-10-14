// BROKEN FIXTURE — V12_LAYOUT "ladder.topBelowCoping" and nothing else (WF-LOOP-R2 row B2).
// The target's roof ladder ENDS at the coping; these stiles carry on 0.40 m over
// it as invented handholds (r2 Astra L12). No landing exists, so the ladder-access
// row stands down and the chain reaches the layout row.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  layout: { "ladder.topBelowCoping": { min: 0.0, max: 0.02, unit: "H", source: "fixture" } },
  palette: { brick: "#b5412f", frame: "#5a2a22", iron: "#2b2e33" } };

const T = 0.50, FRONT = -T / 2;

export function build() {
  const parts = [
    { id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" },
    // The stiles run up past the parapet and graze it, so both ends of that
    // contact are declared — an undeclared penetration is a V6 failure at any depth.
    { id: "parapet", solid: K.box([4, 0.40, T]).at([0, 4, 0]),
      zone: "frame", role: "parapet", touches: ["wall", "ladder_stile_0", "ladder_stile_1"] },
  ];
  K.repeat(2, 0.40, (side, dx) => parts.push({
    id: `ladder_stile_${side}`,
    solid: K.box([0.06, 4.80, 0.06]).at([-0.20 + dx, 0, FRONT - 0.02]),
    zone: "iron", role: "ladder", touches: ["wall", "parapet"],
  }));
  return parts;
}
