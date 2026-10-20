// BROKEN FIXTURE — V12_LAYOUT "cornice.projection" and nothing else (WF-LOOP-R2 row B2).
// The target's crown is a thin lip (<= 0.02 W); this one is a 0.30 m tray. It
// still BEARS (0.30 m of free span, well inside the 1.0 m V11 band), so the
// chain reaches the layout row.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  layout: { "cornice.projection": { max: 0.02, unit: "W", source: "fixture" } },
  palette: { brick: "#b5412f", frame: "#5a2a22" } };

const T = 0.50;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" },
    { id: "cornice", solid: K.box([4.2, 0.30, T + 0.60]).at([0, 4, 0]),
      zone: "frame", role: "cornice", touches: ["wall"] },
  ];
}
