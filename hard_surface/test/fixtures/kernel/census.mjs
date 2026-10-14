// BROKEN FIXTURE — V12_CENSUS and nothing else (WF-LOOP r1 row 4).
// `meta.census` says the target has two windows; the module builds one. The
// count is taken off the ROLE, so renaming the part would not help.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1,
  census: { windows: 2 },
  palette: { brick: "#b5412f", frame: "#5a2a22" } };

const T = 0.30, FRONT = -T / 2;

export function build() {
  return [
    { id: "wall", solid: K.box([4, 4, T]), zone: "brick", role: "massing" },
    { id: "window_frame", solid: K.box([1.0, 1.4, 0.10]).at([0, 2.0, FRONT - 0.04]),
      zone: "frame", role: "window", touches: ["wall"] },
  ];
}
