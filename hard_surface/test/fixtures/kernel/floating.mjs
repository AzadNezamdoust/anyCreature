// BROKEN FIXTURE — V3_FLOAT and nothing else.
//
// A wall on the ground and a box hanging 1.5 m clear of it in mid-air, touching
// nothing and declaring nothing. The union of the two comes apart into two
// lumps, so V3' (a) fires before the load-path row (b) gets a chance.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  class: "building",
  seed: 1,
  palette: { brick: "#b5412f", frame: "#5a2a22" },
};

export function build() {
  return [
    { id: "wall", solid: K.box([4, 3, 0.30]), zone: "brick", role: "massing" },
    {
      id: "floater",
      // 1.5 m off the wall in z and 1.0 m above its top: no contact on any axis.
      solid: K.box([0.8, 0.8, 0.8]).at([0, 4.0, 1.65]),
      zone: "frame",
      role: "massing",
    },
  ];
}
