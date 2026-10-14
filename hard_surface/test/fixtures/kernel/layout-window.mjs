// BROKEN FIXTURE — V12_LAYOUT "window.centreX" and nothing else (WF-LOOP-R2 row B2).
// The frozen layout puts the bay centre at 0.35 of the face width; this module
// builds it at 0.20. Nothing else about the module is wrong, so the chain runs
// all the way to the layout row and stops there.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  layout: { "window.centreX": { values: [0.35], unit: "W", tol: 0.05, source: "fixture" } },
  palette: { brick: "#b5412f", frame: "#5a2a22", glass: "#8fc1d6" } };

const T = 0.30, FRONT = -T / 2;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" },
    { id: "window_frame", solid: K.box([1.0, 1.4, 0.10]).at([-1.2, 2.0, FRONT - 0.04]),
      zone: "frame", role: "window", touches: ["wall"] },
  ];
}
