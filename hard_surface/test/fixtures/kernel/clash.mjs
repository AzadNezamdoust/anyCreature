// BROKEN FIXTURE — V6_CLASH and nothing else.
//
// Two identical 0.20 m bars 0.08 m apart in x: they share 0.12 m of their
// 0.20 m width, so the intersection is 60 % of the smaller solid — over the
// 20 % clash band, under the 90 % duplicate band. Neither declares `embed`, so
// the exemption does not apply. Both stand on the ground against the wall, so
// V2', V3' and V5 are all clean and V6' is the first row that can fire.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  class: "building",
  seed: 1,
  palette: { brick: "#b5412f", iron: "#2b2e33" },
};

const T = 0.30;
const SECTION = 0.20;
const OVERLAP = 0.6;                    // fraction of the smaller solid
const OFFSET = SECTION * (1 - OVERLAP); // 0.08 m in x leaves 0.12 m shared

export function build() {
  const bar = () => K.box([SECTION, 2.4, SECTION]);
  return [
    { id: "wall", solid: K.box([4, 3, T]), zone: "brick", role: "massing" },
    {
      id: "bar_a",
      solid: bar().at([1.0, 0, T / 2 + SECTION / 2]),
      zone: "iron",
      role: "ironwork",
      touches: ["wall"],
    },
    {
      id: "bar_b",
      solid: bar().at([1.0 + OFFSET, 0, T / 2 + SECTION / 2]),
      zone: "iron",
      role: "ironwork",
      touches: ["wall", "bar_a"],
    },
  ];
}
