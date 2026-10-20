// BROKEN FIXTURE — V11_LANDING_GUARD and nothing else (v3-backlog item 3).
// A bare deck hung off the wall: it bears, it sits on the brick, and nothing
// stops a person walking off its front or its ends. `build({ guarded: true })`
// adds the front rail and the two returns, railing_h above the deck, and must
// clear the row.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.6, FRONT = -T / 2;
const DECK_TOP = 2.12, RAIL = 1.0, BAR = 0.08;

export function build({ guarded = false } = {}) {
  const parts = [{ id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" }];
  for (const [id, x] of [["arm_l", -0.55], ["arm_r", 0.55]]) {
    parts.push({ id, solid: K.box([0.12, 0.12, 0.71]).at([x, 1.88, FRONT - 0.345]),
      zone: "iron", role: "support", touches: ["wall", "beam"] });
  }
  parts.push({ id: "beam", solid: K.box([1.3, 0.13, 0.12]).at([0, 1.88, FRONT - 0.50]),
    zone: "iron", role: "support", touches: ["arm_l", "arm_r"] });
  parts.push({ id: "landing", solid: K.box([1.3, 0.12, 0.75]).at([0, 2.00, FRONT - 0.365]),
    zone: "iron", role: "landing", touches: ["beam", "wall"] });
  if (!guarded) return parts;
  // Front rail over the whole deck edge, one return at each end back to the wall.
  const zFront = FRONT - 0.74;
  parts.push({ id: "guard_front", solid: K.box([1.3, RAIL, BAR]).at([0, DECK_TOP, zFront + BAR / 2]),
    zone: "iron", role: "railing", touches: ["landing"] });
  for (const [id, x] of [["guard_l", -0.65 + BAR / 2], ["guard_r", 0.65 - BAR / 2]]) {
    parts.push({ id, solid: K.box([BAR, RAIL, 0.73 - BAR]).at([x, DECK_TOP, FRONT - (0.73 + BAR) / 2]),
      zone: "iron", role: "railing", touches: ["landing", "guard_front"] });
  }
  return parts;
}
