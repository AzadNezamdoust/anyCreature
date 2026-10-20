// BROKEN FIXTURE — V11_DECK_GAP and nothing else (WF-LOOP r1 row 9).
// Four deck bars on a 0.30 m pitch with a 0.06 m section leave 0.24 m slots, over
// the r3 C1.4 limit of 0.20 m (raised from 0.10, which forced a near-solid deck).
// The deck meets the wall and is carried on a beam, so bearing and the landing
// gap both pass and the slot is the only thing left.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.6, FRONT = -T / 2;

export function build() {
  const parts = [{ id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" }];
  for (const [id, x] of [["arm_l", -0.55], ["arm_r", 0.55]]) {
    parts.push({ id, solid: K.box([0.12, 0.12, 0.71]).at([x, 1.88, FRONT - 0.345]),
      zone: "iron", role: "support", touches: ["wall", "beam"] });
  }
  parts.push({ id: "beam", solid: K.box([1.3, 0.13, 0.12]).at([0, 1.88, FRONT - 0.50]),
    zone: "iron", role: "support", touches: ["arm_l", "arm_r"] });
  parts.push(...K.repeat(4, 0.30, (i, pitch) => ({
    id: `deck_${i}`,
    solid: K.box([0.06, 0.12, 0.75]).at([-0.45 + pitch, 2.00, FRONT - 0.365]),
    zone: "iron", role: "landing", touches: ["beam", "wall"],
  })));
  return parts;
}
