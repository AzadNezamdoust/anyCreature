// BROKEN FIXTURE — V12_LAYOUT "ladder.roof.face" and nothing else (WF-LOOP-R3 row C1.3).
// The target's roof ladder climbs the street-left SIDE return; run 3 built it on
// the front plane and 0.25 m in FRONT of the brick, which reads as a ladder in the
// air (fable-audit L5). These stiles are on the front face, so the row fires.
// No landing exists, so the ladder-access row stands down and the chain reaches
// the layout row.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  layout: { "ladder.roof.face": { value: "side", unit: "face", source: "fixture" } },
  palette: { brick: "#b5412f", frame: "#5a2a22", iron: "#2b2e33" } };

const T = 2.0, FRONT = -T / 2;

export function build() {
  const parts = [{ id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" }];
  K.repeat(2, 0.40, (side, dx) => parts.push({
    id: `ladder_stile_${side}`,
    solid: K.box([0.06, 3.80, 0.06]).at([-0.20 + dx, 0, FRONT - 0.03]),
    zone: "iron", role: "ladder", touches: ["wall"],
  }));
  return parts;
}
