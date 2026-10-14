// BLOCKOUT start module — taxi (refs/taxi.png). Primitive masses sized from the REGISTERED turnaround
// (subjects/taxi/turnaround/views.json: W anchor 1.85 m -> L 4.04, H 2.258 incl. the roof sign; wheel R 0.418, centres
// z +1.321 / -1.212 read off the side-view hub components). Every number below is a registered metre at the knob
// defaults L0 / W0 / H0 and is stretched per axis with the L / W / H knobs.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 4.04, min: 3.8, max: 5.4, unit: "m" },    // body paint span (side / top)
  W:      { v: 1.85, min: 1.6, max: 2.1, unit: "m" },    // anchor
  H:      { v: 2.258, min: 1.5, max: 2.4, unit: "m" },   // ground to the roof-sign top
  wheelR: { v: 0.418, min: 0.3, max: 0.45, unit: "m" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    body: "#fecb17",
    glass: "#84c4fb",
    trim: "#2f2f2f",
    tyre: "#2f2f2f",
    bumper: "#757474",
    hub: "#a9a9a9",
    sign: "#f0f0f0",
  },
};

const L0 = 4.04, W0 = 1.85, H0 = 2.258;

export function build() {
  const L = KNOBS.L.v, W = KNOBS.W.v, H = KNOBS.H.v, R = KNOBS.wheelR.v;
  const X = (v) => v * W / W0, Y = (v) => v * H / H0, Z = (v) => v * L / L0;
  const parts = [];
  const add = (id, solid, zone, role) => parts.push({ id, solid, zone, role });
  /** axis-aligned block, registered metres */
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([(X(x0) + X(x1)) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  /** frustum between two x-symmetric rectangles (y, z0, z1, halfW) */
  const frustum = (lo, hi) => K.hull([lo, hi].flatMap(([y, z0, z1, hw]) => [[-X(hw), Y(y), Z(z0)], [X(hw), Y(y), Z(z0)], [-X(hw), Y(y), Z(z1)], [X(hw), Y(y), Z(z1)]]));
  /** disc on the x axis: x0..x1, centre (y, z), radius r */
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);

  // masses
  add("body", slab(-0.97, 0.97, 0.33, 0.93, -2.06, 2.02), "body", "body");           // lower body (front view +-0.99 at 0.63-0.92)
  add("stripe", slab(-0.98, 0.98, 0.93, 1.08, -2.05, 2.01), "trim", "body");          // the black side stripe band
  add("beltline", slab(-0.88, 0.88, 1.08, 1.27, -2.02, 1.98), "body", "body");        // hood / deck level (front view +-0.84)
  add("greenhouse", frustum([1.27, -1.17, 1.05, 0.8], [1.88, -0.77, 0.62, 0.7]), "glass", "window");
  add("roof", slab(-0.68, 0.68, 1.86, 2.0, -0.8, 0.62), "body", "body");
  add("sign", slab(-0.43, 0.43, 2.0, 2.25, -0.18, 0.18), "sign", "prop");
  add("bumper_front", slab(-1.03, 1.03, 0.43, 0.71, 1.8, 2.12), "bumper", "bumper");
  add("bumper_rear", slab(-1.03, 1.03, 0.43, 0.71, -2.14, -1.79), "bumper", "bumper");
  // wheels: tyre x 0.72..0.97 (front view), hub disc on the outer face
  for (const [tag, zc] of [["f", 1.321], ["r", -1.212]]) {
    for (const [side, sg] of [["l", 1], ["r", -1]]) {
      const [a, b] = sg > 0 ? [X(0.72), X(0.97)] : [-X(0.97), -X(0.72)];
      add(`tyre_${tag}${side}`, disc(a, b, R, Z(zc), R), "tyre", "tyre");
      const [h0, h1] = sg > 0 ? [b - 0.005, b + 0.015] : [a - 0.015, a + 0.005];
      add(`hub_${tag}${side}`, disc(h0, h1, R, Z(zc), 0.48 * R), "hub", "hub");
    }
  }
  return parts;
}
