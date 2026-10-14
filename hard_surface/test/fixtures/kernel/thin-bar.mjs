// BROKEN FIXTURE — V5 and nothing else.
//
// The bar's section is 0.03 m, half the building style floor (limits.json:8
// styleFloor.building = 0.06). It is otherwise a healthy solid standing flush
// against the wall, so V1' passes and V5 is the first row that can fire.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  class: "building",
  seed: 1,
  palette: { brick: "#b5412f", iron: "#2b2e33" },
};

const T = 0.30;
const SECTION = 0.03;                   // half of MIN_FEAT

export function build() {
  return [
    { id: "wall", solid: K.box([4, 3, T]), zone: "brick", role: "massing" },
    {
      id: "bar",
      solid: K.box([SECTION, 2.4, SECTION]).at([1.2, 0, T / 2 + SECTION / 2]),
      zone: "iron",
      role: "ironwork",
      touches: ["wall"],
    },
  ];
}
