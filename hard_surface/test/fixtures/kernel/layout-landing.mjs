// BROKEN FIXTURE — V12_LAYOUT "landing.depth" and nothing else (WF-LOOP-R2 row B2).
// The deck is carried, meets the brick and has no slot in it, so V11 is happy —
// it is simply twice as deep as the target's (0.30 W against 0.15 W), which is
// the r2 L8 defect no rule could see. It carries a front rail and two returns
// (v3-backlog item 3) so V11_LANDING_GUARD stays quiet too.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  layout: { "landing.depth": { value: 0.15, unit: "W", tol: 0.05, source: "fixture" } },
  palette: { brick: "#b5412f", iron: "#2b2e33" } };

const T = 0.60, FRONT = -T / 2;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" },
    { id: "bracket", solid: K.box([0.12, 0.13, 1.22]).at([0, 1.88, FRONT - 0.60]),
      zone: "iron", role: "support", touches: ["wall", "landing"] },
    { id: "landing", solid: K.box([1.2, 0.12, 1.2]).at([0, 2.00, FRONT - 0.60]),
      zone: "iron", role: "landing", touches: ["wall", "bracket"] },
    // guard: tops 1.0 m over the 2.12 m deck top, front edge + both ends back to the wall
    { id: "rail_front", solid: K.box([1.2, 1.0, 0.08]).at([0, 2.12, FRONT - 1.16]),
      zone: "iron", role: "railing", touches: ["landing"] },
    { id: "rail_l", solid: K.box([0.08, 1.0, 1.12]).at([-0.56, 2.12, FRONT - 0.56]),
      zone: "iron", role: "railing", touches: ["landing", "rail_front"] },
    { id: "rail_r", solid: K.box([0.08, 1.0, 1.12]).at([0.56, 2.12, FRONT - 0.56]),
      zone: "iron", role: "railing", touches: ["landing", "rail_front"] },
  ];
}
