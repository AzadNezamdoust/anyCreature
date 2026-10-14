// BROKEN FIXTURE — V11_LANDING_GAP and nothing else (WF-LOOP r1 row 7).
// The deck is carried on a bracket and bears fine, but its back face stands
// 0.40 m clear of the brick: a slot you put a foot through.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.6, FRONT = -T / 2;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" },
    { id: "bracket", solid: K.box([0.12, 0.13, 0.62]).at([0, 1.88, FRONT - 0.30]),
      zone: "iron", role: "support", touches: ["wall", "landing"] },
    { id: "landing", solid: K.box([1.2, 0.12, 0.40]).at([0, 2.00, FRONT - 0.60]),
      zone: "iron", role: "landing", touches: ["bracket"] },
  ];
}
