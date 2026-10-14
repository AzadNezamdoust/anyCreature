// HEALTHY FIXTURE — the same ladder built the way the target shows it: on the
// street-left SIDE wall (author +x), set back behind the front plane. It is the
// PASSING half of the r3 C1.3 ladder.roof rule, so the row is pinned in both
// directions and "side" cannot be satisfied by an accident of grouping.
import * as K from "../../../src/kernel/index.mjs";

const T = 2.0, FRONT = -T / 2;          // the block is deep enough to have a side wall
const W = 4;

export const meta = { class: "building", seed: 1, census: false,
  layout: {
    "ladder.roof.face": { value: "side", unit: "face", source: "fixture" },
    // the stile PAIR's z centre sits 0.71 m back from the front plane on a 4 m face = 0.177 W.
    "ladder.roof.backFromCorner": { value: 0.177, unit: "W", tol: 0.027, source: "fixture" },
  },
  palette: { brick: "#b5412f", frame: "#5a2a22", iron: "#2b2e33" } };

export function build() {
  const parts = [{ id: "wall", solid: K.box([W, 4, T]), zone: "brick", role: "massing" }];
  // stiles stand PROUD of the +x side wall; the pair's z centre is 0.71 m behind -Z
  K.repeat(2, 0.40, (side, dz) => parts.push({
    id: `ladder_stile_${side}`,
    solid: K.box([0.06, 3.80, 0.06]).at([W / 2 + 0.03, 0, FRONT + 0.51 + dz]),
    zone: "iron", role: "ladder", touches: ["wall"],
  }));
  return parts;
}
