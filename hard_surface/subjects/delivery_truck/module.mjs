// BLOCKOUT start module — box delivery truck (refs/delivery_truck.png). Primitive masses sized from the REGISTERED
// turnaround (subjects/delivery_truck/turnaround/views.json: W anchor 2.4 m -> L 4.899, H 2.896; wheel R 0.408, centres
// z +1.494 / -0.93 / -1.75 read off the side-view hub components: one front axle + a TANDEM rear pair, as drawn). Every
// number below is a registered metre at the knob defaults L0 / W0 / H0, stretched per axis by the L / W / H knobs.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 4.899, min: 4.4, max: 9.0, unit: "m" },   // body paint span (side / top)
  W:      { v: 2.4, min: 2.1, max: 2.6, unit: "m" },     // anchor
  H:      { v: 2.896, min: 2.6, max: 3.8, unit: "m" },   // ground to the box roof
  wheelR: { v: 0.408, min: 0.35, max: 0.5, unit: "m" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    body: "#e8e7e2",
    glass: "#5a7487",
    stripe: "#378a47",
    chassis: "#3b3f40",
    tyre: "#2c2e2f",
    bumper: "#818181",
    hub: "#818181",
  },
};

const L0 = 4.899, W0 = 2.4, H0 = 2.896;

export function build() {
  const L = KNOBS.L.v, W = KNOBS.W.v, H = KNOBS.H.v, R = KNOBS.wheelR.v;
  const X = (v) => v * W / W0, Y = (v) => v * H / H0, Z = (v) => v * L / L0;
  const parts = [];
  const add = (id, solid, zone, role) => parts.push({ id, solid, zone, role });
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([(X(x0) + X(x1)) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  /** hull of x-symmetric side-profile points [[y, z], ...] at half width hw */
  const prism = (pts, hw) => K.hull(pts.flatMap(([y, z]) => [[-X(hw), Y(y), Z(z)], [X(hw), Y(y), Z(z)]]));
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);
  // the cab nose: vertical to the bumper top (z 2.30, y 0.70), then leaning back to z 2.07 at the roof (side view)
  const noseZ = (y) => (y <= 0.7 ? 2.3 : 2.3 - (y - 0.7) * (0.23 / (2.23 - 0.7)));

  add("cab", prism([[0.36, 0.92], [0.36, 2.3], [0.7, 2.3], [2.23, 2.07], [2.23, 0.92]], 1.04), "body", "cab");
  add("box", slab(-1.155, 1.155, 0.83, 2.88, -2.42, 0.91), "body", "body");
  add("stripe", slab(-1.165, 1.165, 1.6, 2.07, -2.43, 0.9), "stripe", "body");
  add("chassis", slab(-0.75, 0.75, 0.5, 0.84, -2.35, 1.9), "chassis", "chassis");
  // glass: the side windows (both flanks) and the windshield plate on the leaning nose
  add("window_side", slab(-1.045, 1.045, 1.43, 2.08, 1.13, 1.9), "glass", "window");
  add("windshield", K.hull([1.32, 2.04].flatMap((y) => [-0.93, 0.93].flatMap((x) => [[X(x), Y(y), Z(noseZ(y) - 0.05)], [X(x), Y(y), Z(noseZ(y) + 0.015)]]))), "glass", "window");
  add("bumper_front", slab(-1.1, 1.1, 0.37, 0.66, 2.11, 2.43), "bumper", "bumper");
  // wheels: tyre x 0.72..1.00 (front / rear views), hub disc on the outer face
  for (const [tag, zc] of [["f", 1.494], ["r1", -0.93], ["r2", -1.75]]) {
    for (const [side, sg] of [["l", 1], ["r", -1]]) {
      const [a, b] = sg > 0 ? [X(0.72), X(1.0)] : [-X(1.0), -X(0.72)];
      add(`tyre_${tag}${side}`, disc(a, b, R, Z(zc), R), "tyre", "tyre");
      const [h0, h1] = sg > 0 ? [b - 0.005, b + 0.015] : [a - 0.015, a + 0.005];
      add(`hub_${tag}${side}`, disc(h0, h1, R, Z(zc), 0.45 * R), "hub", "hub");
    }
  }
  return parts;
}
