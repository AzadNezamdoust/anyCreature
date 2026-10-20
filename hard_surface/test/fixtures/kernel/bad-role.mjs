// BROKEN FIXTURE — V7_ROLE and nothing else (WF-LOOP r1 row 5).
// The bar calls itself "ironwork", which is not in the closed role table, so
// every role-based rule below it measures nothing. Geometry is healthy.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.30;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 3, T]), zone: "brick", role: "massing" },
    { id: "bar", solid: K.box([0.08, 2.4, 0.08]).at([1.2, 0, -T / 2 - 0.03]),
      zone: "iron", role: "ironwork", touches: ["wall"] },
  ];
}
