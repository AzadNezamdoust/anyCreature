// BROKEN FIXTURE — V11_BEARING and nothing else (WF-LOOP r1 row 2).
// A 3 m deep roof on a single 1 m wall: 2 m of it hangs over nothing. The wall
// is thick and the roof light, so the assembly still balances (V4 passes) and
// the cantilever is the only thing wrong with it.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", roof: "#918680" } };

const T = 1.0, H = 3.0;

export function build() {
  return [
    { id: "wall", solid: K.box([4, H, T]), zone: "brick", role: "massing" },
    { id: "roof", solid: K.box([4, 0.12, 3.0]).at([0, H - 0.01, -T / 2 + 1.5]),
      zone: "roof", role: "roof", touches: ["wall"] },
  ];
}
