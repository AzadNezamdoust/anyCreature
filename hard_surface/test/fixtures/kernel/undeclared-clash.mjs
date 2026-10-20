// BROKEN FIXTURE — V6_CLASH_UNDECLARED and nothing else (WF-LOOP r1 row 6).
// The bar is buried 0.01 m in the brick and says nothing about it. Under the
// old rule that was 16 % of the smaller solid, inside the 20 % band, and passed.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.30;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 3, T]), zone: "brick", role: "massing" },
    // No `touches`: the penetration is undeclared, which is the whole point.
    { id: "bar", solid: K.box([0.08, 2.4, 0.08]).at([1.2, 0, -T / 2 - 0.03]),
      zone: "iron", role: "baluster" },
  ];
}
