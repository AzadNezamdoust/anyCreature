// BROKEN FIXTURE — V3_FLOAT from a CUT, not from a part placed in mid-air.
//
// A slab on the ground with a post on each end; a through-cut 0.1 m wide splits
// the slab into two lumps (the blind Gemini pickup P1 failure class: a "groove"
// cut through a part's whole section). The V3 hint must name both pieces by
// their parts and give the gap across the cut.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  class: "building",
  seed: 1,
  palette: { brick: "#b5412f", frame: "#5a2a22" },
};

export function build() {
  const slab = K.cut(K.box([4, 0.5, 1]), K.box([0.1, 2, 2]).at([0.5, -0.5, 0]));
  return [
    { id: "slab", solid: slab, zone: "brick", role: "massing" },
    { id: "post_left", solid: K.box([0.4, 2, 0.4]).at([-1.5, 0.499, 0]), zone: "frame", role: "massing", touches: ["slab"] },
    { id: "post_right", solid: K.box([0.4, 1, 0.4]).at([1.5, 0.499, 0]), zone: "frame", role: "massing", touches: ["slab"] },
  ];
}
