// BLOCKOUT start module — farm tractor (refs/tractor.png). Primitive masses sized from the REGISTERED turnaround
// (subjects/tractor/turnaround/views.json: W anchor 2.2 m over the rear fenders -> L 3.25 (red span), H 2.536 to the
// canopy; wheels read off the side-view hub components: front R 0.408 at z +1.304, rear R 0.733 at z -1.057). Every
// number below is a registered metre at the knob defaults L0 / W0 / H0, stretched per axis by the L / W / H knobs.
// Asymmetric props follow the CONCEPT (exhaust on the -x side of the hood, step ladder on the +x flank); the
// turnaround front / rear views draw them mirrored.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:           { v: 3.25, min: 3.0, max: 4.2, unit: "m" },    // red paint span (side / top)
  W:           { v: 2.2, min: 1.9, max: 2.4, unit: "m" },     // anchor: over the rear fenders / tyres
  H:           { v: 2.536, min: 2.3, max: 2.9, unit: "m" },   // ground to the canopy roof
  wheelR:      { v: 0.733, min: 0.6, max: 0.8, unit: "m" },   // rear
  frontWheelR: { v: 0.408, min: 0.35, max: 0.48, unit: "m" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    body: "#c9312d",
    frame: "#454545",
    tyre: "#323231",
    hub: "#a4a4a4",
    lamp: "#f4f4f4",
  },
};

const L0 = 3.25, W0 = 2.2, H0 = 2.536;

export function build() {
  const L = KNOBS.L.v, W = KNOBS.W.v, H = KNOBS.H.v, R = KNOBS.wheelR.v, RF = KNOBS.frontWheelR.v;
  const X = (v) => v * W / W0, Y = (v) => v * H / H0, Z = (v) => v * L / L0;
  const parts = [];
  const add = (id, solid, zone, role) => parts.push({ id, solid, zone, role });
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([(X(x0) + X(x1)) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);

  add("hood", slab(-0.4, 0.4, 0.65, 1.5, 0.28, 1.62), "body", "hood");
  add("grille", slab(-0.26, 0.26, 0.75, 1.36, 1.61, 1.66), "frame", "grille");
  add("engine", slab(-0.3, 0.3, 0.42, 0.7, -0.4, 1.5), "frame", "chassis");
  add("body", slab(-0.6, 0.6, 0.6, 1.25, -0.97, 0.28), "body", "body");
  add("fender_l", slab(0.6, 1.15, 1.3, 1.57, -1.62, -0.4), "body", "body");
  add("fender_r", slab(-1.15, -0.6, 1.3, 1.57, -1.62, -0.4), "body", "body");
  add("seat", slab(-0.25, 0.25, 1.25, 1.75, -0.75, -0.35), "frame", "prop");
  add("canopy", slab(-0.69, 0.69, 2.42, 2.53, -1.05, 0.25), "body", "prop");
  for (const [i, [x, z]] of [[0.62, 0.18], [-0.62, 0.18], [0.62, -0.98], [-0.62, -0.98]].entries()) {
    add(`post_${i}`, slab(x - 0.035, x + 0.035, 1.2, 2.42, z - 0.035, z + 0.035), "frame", "prop");
  }
  add("exhaust", slab(-0.26, -0.14, 1.45, 2.3, 0.89, 1.01), "frame", "prop");
  add("step", slab(0.6, 0.7, 0.4, 0.9, -0.15, 0.12), "hub", "prop");
  add("headlamp_l", slab(0.34, 0.49, 0.98, 1.19, 1.6, 1.7), "lamp", "headlight");
  add("headlamp_r", slab(-0.49, -0.34, 0.98, 1.19, 1.6, 1.7), "lamp", "headlight");
  add("axle_front", slab(-0.6, 0.6, 0.33, 0.48, 1.25, 1.36), "frame", "axle");
  // wheels: rear tyre x 0.60..1.10, front 0.55..0.85 (front / top views), hub disc on the outer face
  for (const [tag, zc, r, x0, x1, hub] of [["f", 1.304, RF, 0.55, 0.85, 0.42], ["r", -1.057, R, 0.6, 1.1, 0.51]]) {
    for (const [side, sg] of [["l", 1], ["r", -1]]) {
      const [a, b] = sg > 0 ? [X(x0), X(x1)] : [-X(x1), -X(x0)];
      add(`tyre_${tag}${side}`, disc(a, b, r, Z(zc), r), "tyre", "tyre");
      const [h0, h1] = sg > 0 ? [b - 0.005, b + 0.015] : [a - 0.015, a + 0.005];
      add(`hub_${tag}${side}`, disc(h0, h1, r, Z(zc), hub * r), "hub", "hub");
    }
  }
  return parts;
}
