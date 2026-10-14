// BROKEN FIXTURE — V11_LADDER_ACCESS and nothing else (WF-LOOP r1 row 8).
// The ladder head arrives at the deck under an unbroken run of railing: you can
// climb it and you cannot get off it. Everything else about the deck is legal.
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
  parts.push({ id: "landing", solid: K.box([1.3, 0.12, 0.75]).at([0, 2.00, FRONT - 0.365]),
    zone: "iron", role: "landing", touches: ["beam", "wall"] });
  for (const [id, x] of [["stile_l", -0.14], ["stile_r", 0.06]]) {
    parts.push({ id, solid: K.box([0.08, 1.60, 0.08]).at([x, 0.45, FRONT - 0.69]),
      zone: "iron", role: "ladder", touches: ["landing"] });
  }
  // One unbroken handrail across the whole deck, ladder head included.
  parts.push({ id: "guard", solid: K.box([1.30, 1.00, 0.08]).at([0, 2.11, FRONT - 0.70]),
    zone: "iron", role: "railing", touches: ["landing"] });
  return parts;
}
