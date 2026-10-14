// BROKEN FIXTURE — V12_LAYOUT "frame.proud" and nothing else (WF-LOOP-R2 row B2).
// The round-2 recipe: cut a pocket and bury the frame in it. The target's frames
// stand 0.05-0.08 m PROUD of the brick, so a frame whose front face is 0.14 m
// behind the brick plane is the r2 C4 defect, measured.
import * as K from "../../../src/kernel/index.mjs";

export const meta = { class: "building", seed: 1, census: false,
  layout: { "frame.proud": { min: 0.05, max: 0.08, unit: "m", source: "fixture" } },
  palette: { brick: "#b5412f", frame: "#5a2a22", glass: "#8fc1d6" } };

const T = 0.50, FRONT = -T / 2;

export function build() {
  const aperture = K.profile.rect({ w: 1.0, h: 1.4 });
  const surround = K.profile.offset(aperture, 0.09);
  // A 0.23 m pocket, not a through hole: 0.27 m of brick stays behind it.
  const wall = K.cut(K.box([4, 4, T]), K.extrude(surround, 0.23).at([0, 1.8, FRONT - 0.01]));
  return [
    { id: "wall", solid: wall, zone: "brick", role: "massing" },
    { id: "window_frame", solid: K.extrude(surround, 0.08, { holes: [aperture] }).at([0, 1.8, FRONT + 0.14]),
      zone: "frame", role: "window", touches: ["wall", "window_glass"] },
    { id: "window_glass", solid: K.extrude(aperture, 0.06).at([0, 1.8, FRONT + 0.16]),
      zone: "glass", role: "window", touches: ["wall", "window_frame"] },
  ];
}
