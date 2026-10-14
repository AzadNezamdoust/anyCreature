// BROKEN FIXTURE — V2_GAP and nothing else.
//
// The bar declares `touches: ["wall"]` and then stands 0.05 m clear of the wall
// face (EPS is 0.01 m). Every other row is clean: both solids are healthy, the
// bar section is exactly MIN_FEAT, nothing interpenetrates.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  class: "building",
  seed: 1,
  palette: { brick: "#b5412f", iron: "#2b2e33" },
};

const T = 0.30;
const GAP = 0.05;                       // 5x EPS: unambiguously a gap, not float noise

export function build() {
  return [
    { id: "wall", solid: K.box([4, 3, T]), zone: "brick", role: "massing" },
    {
      id: "bar",
      solid: K.box([0.06, 2.4, 0.06]).at([1.2, 0, T / 2 + GAP + 0.03]),
      zone: "iron",
      role: "ironwork",
      touches: ["wall"],
    },
  ];
}
