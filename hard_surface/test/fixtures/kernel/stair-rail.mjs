// BROKEN FIXTURE — V7_STAIR_RAIL and nothing else (WF-LOOP r1 row 5).
// The rise is legal (0.167 m over six risers) and the flight has stringers, but
// there is nothing at hand height to hold: an open flight with no handrail.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.30, FRONT = -T / 2, PITCH = 1 / 6;

export function build() {
  const parts = [{ id: "wall", solid: K.box([4, 6, T]), zone: "brick", role: "massing" }];
  for (const [id, y] of [["landing_low", 1.0], ["landing_high", 2.0]]) {
    parts.push({ id, solid: K.box([2.0, 0.10, 1.0]).at([0, y, FRONT - 0.49]),
      zone: "iron", role: "landing", touches: ["wall"] });
  }
  const steps = K.repeat(5, PITCH, (i, rise) => ({
    id: `step_${i}`,
    solid: K.box([1.2, 0.08, 0.51]).at([0, 1.10 + PITCH + rise - 0.08, FRONT - 0.245]),
    zone: "iron", role: "step", touches: ["wall"],
  }));
  parts.push(...steps);
  parts.push({ id: "stringer",
    solid: K.box([0.10, 1.00, 0.08]).at([-0.60, 1.10, FRONT - 0.42]),
    zone: "iron", role: "stringer", touches: [...steps.map((s) => s.id), "landing_low", "landing_high"] });
  return parts;
}
