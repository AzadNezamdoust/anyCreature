// BROKEN FIXTURE — V7 step_rise and nothing else (WF-LOOP r1 row 5).
// Three treads span the 1.0 m between two landing tops, so every riser is
// 0.25 m: a stair nobody climbs. The band is limits.v7.step_rise (0.14..0.20).
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.30, FRONT = -T / 2;

export function build() {
  const parts = [{ id: "wall", solid: K.box([4, 6, T]), zone: "brick", role: "massing" }];
  for (const [id, y] of [["landing_low", 1.0], ["landing_high", 2.0]]) {
    parts.push({ id, solid: K.box([2.0, 0.10, 1.0]).at([0, y, FRONT - 0.49]),
      zone: "iron", role: "landing", touches: ["wall"] });
  }
  parts.push(...K.repeat(3, 0.25, (i, rise) => ({
    id: `step_${i}`,
    solid: K.box([1.2, 0.08, 0.51]).at([0, 1.10 + 0.25 + rise - 0.08, FRONT - 0.245]),
    zone: "iron", role: "step", touches: ["wall"],
  })));
  return parts;
}
