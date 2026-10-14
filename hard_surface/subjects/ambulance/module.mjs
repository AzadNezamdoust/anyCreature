// BLOCKOUT start module — box-body ambulance (refs/ambulance.png). Primitive masses sized from the REGISTERED turnaround
// (subjects/ambulance/turnaround/views.json: W anchor 2.2 m -> 160.3 px/m; nose z +2.595 .. patient-box rear z -2.52,
// box roof 2.46; wheel R 0.4025, centres z +1.974 / -0.72 read off the side-view hub components). Every number below is a
// registered metre at the knob defaults L0 / W0 / H0 and is stretched per axis with the L / W / H knobs.
// Widths: the front view draws the box +-1.055, the rear view +-1.085, the top view +-1.03 (LEDGER drift line); the
// blockout uses +-1.07 for the box and +-1.0 for the cab (front view).
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 5.115, min: 4.6, max: 6.4, unit: "m" },    // body paint span: cab nose .. patient-box rear (side / top)
  W:      { v: 2.2, min: 2.0, max: 2.5, unit: "m" },      // anchor
  H:      { v: 2.47, min: 2.2, max: 2.9, unit: "m" },     // ground to the patient-box roof
  wheelR: { v: 0.4025, min: 0.34, max: 0.48, unit: "m" },
  frameScale: { v: 0.9775, min: 0.7, max: 1.4, unit: "scale", group: "frame" },   // concept-view similarity (registered.mjs)
  frameX:     { v: -6.5, min: -48, max: 48, unit: "px", group: "frame" },
  frameY:     { v: 3, min: -48, max: 48, unit: "px", group: "frame" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table + concept samples (flat colours)
  palette: {
    body: "#f0f0f0",
    stripe: "#d3241d",
    glass: "#8ca8bb",
    mirror: "#474a4e",
    tyre: "#35383c",
    hub: "#a7aaac",
    bumper: "#a5a7a9",
    lamp: "#fdf9d2",
    grille: "#5e6266",
  },
};

const L0 = 5.115, W0 = 2.2, H0 = 2.47;
const T = 0.04, PROUD = 0.008;   // vehicle style floor: every detail >= 0.04 m on each axis, seated, 8 mm proud

export function build() {
  const L = KNOBS.L.v, W = KNOBS.W.v, H = KNOBS.H.v, R = KNOBS.wheelR.v;
  const X = (v) => v * W / W0, Y = (v) => v * H / H0, Z = (v) => v * L / L0;
  const parts = [];
  const add = (id, solid, zone, role, extra = {}) => parts.push({ id, solid, zone, role, ...extra });
  // contact declarations (kernel README "Contact"): seat = meant to sit inside its hosts
  const seat = (...hosts) => ({ touches: hosts, embed: true });
  /** axis-aligned block, registered metres */
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([(X(x0) + X(x1)) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  /** hull of x-symmetric side-profile points [[y, z], ...] at half width hw */
  const prism = (pts, hw) => K.hull(pts.flatMap(([y, z]) => [[-X(hw), Y(y), Z(z)], [X(hw), Y(y), Z(z)]]));
  /** disc on the x axis: x0..x1 (world m), centre (y, z), radius r */
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);
  /** a detail plate on the flank face x = +-xf (world thickness T, PROUD outside), registered y / z */
  const plateX = (xf, sg, y0, y1, z0, z1) => {
    const a = X(xf) + PROUD - T, b = X(xf) + PROUD;
    return K.box([T, Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([sg * (a + b) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  };
  /** a detail plate on a face z = zf looking along +z (dir 1) or -z (dir -1) */
  const plateZ = (zf, dir, x0, x1, y0, y1) => {
    const c = Z(zf) + dir * (PROUD - T / 2);
    return K.box([X(x1) - X(x0), Y(y1) - Y(y0), T]).at([(X(x0) + X(x1)) / 2, Y(y0), c]);
  };
  const LR = [["l", 1], ["r", -1]];

  // patient box: full width above the wheel arches (y 0.78), a core between the tyres (x +-0.664) down to the flank
  // bottom 0.335, and the flank skirts around the rear arch (z -1.18 .. -0.26; behind it the door sill sits at 0.555)
  add("box", K.union(
    slab(-1.07, 1.07, 0.78, 2.46, -2.52, 0.79),
    slab(-0.664, 0.664, 0.335, 0.78, -2.52, 0.79),
    slab(-1.07, 1.07, 0.335, 0.78, -0.26, 0.79),
    slab(-1.07, 1.07, 0.555, 0.78, -2.52, -1.18),
  ), "body", "body");
  // cab: lower body with the hood slope (nose z 2.595 at y 1.135 -> windshield base z 2.01 at y 1.354), greenhouse with
  // the raked windshield (-> roof edge z 1.60 at y 2.05), sill core + skirts around the front arch (z 1.51 .. 2.43; the
  // sill and the nose skirt behind the bumper at 0.34)
  add("cab", K.union(
    prism([[0.86, 0.79], [0.86, 2.595], [1.135, 2.595], [1.354, 2.01], [1.354, 0.79]], 1.0),
    prism([[1.354, 0.79], [1.354, 2.01], [2.05, 1.6], [2.05, 0.79]], 1.0),
    slab(-0.664, 0.664, 0.34, 0.86, 0.79, 2.595),
    slab(-1.0, 1.0, 0.34, 0.86, 0.79, 1.51),
    slab(-1.0, 1.0, 0.34, 0.86, 2.43, 2.595),
  ), "body", "cab");

  // glass: windshield plate on the raked face (front view +-0.883, y 1.36 .. 1.93), door windows, box door windows
  const rake = (y) => 2.01 - 0.589 * (y - 1.354);
  const nY = 0.508, nZ = 0.862;   // raked-face outward normal (y, z)
  const ws = [1.36, 1.93].flatMap((y) => [PROUD - T, PROUD].flatMap((o) => [-1, 1].map((sx) => [sx * X(0.883), Y(y) + nY * o, Z(rake(y)) + nZ * o])));
  add("windshield", K.hull(ws), "glass", "window", seat("cab"));
  for (const [t, sg] of LR) {
    add(`window_door_${t}`, plateX(1.0, sg, 1.266, 1.878, 0.986, 1.722), "glass", "window", seat("cab"));
    add(`window_boxdoor_${t}a`, plateX(1.07, sg, 1.466, 2.027, -1.709, -1.298), "glass", "window", seat("box"));
    add(`window_boxdoor_${t}b`, plateX(1.07, sg, 1.466, 2.027, -2.314, -1.903), "glass", "window", seat("box"));
    add(`window_rear_${t}`, plateZ(-2.52, -1, sg > 0 ? 0.094 : -0.53, sg > 0 ? 0.53 : -0.094, 1.453, 2.009), "glass", "window", seat("box"));
  }

  // red paint: the side stripe (box y 0.967 .. 1.266, cab 0.89 .. 1.14), front and rear bands
  for (const [t, sg] of LR) {
    add(`stripe_box_${t}`, plateX(1.07, sg, 0.967, 1.266, -1.19, 0.79), "stripe", "body", seat("box"));
    add(`stripe_boxtail_${t}`, plateX(1.07, sg, 0.967, 1.266, -2.52, -2.41), "stripe", "body", seat("box", `stripe_rear_${t}`));
    add(`stripe_cab_${t}`, plateX(1.0, sg, 0.89, 1.14, 0.79, 2.595), "stripe", "body", seat("cab"));
    add(`stripe_rear_${t}`, plateZ(-2.52, -1, sg > 0 ? 0.63 : -1.07, sg > 0 ? 1.07 : -0.63, 0.99, 1.273), "stripe", "body", seat("box"));
  }
  add("stripe_front", plateZ(2.595, 1, -0.926, 0.926, 0.917, 1.06), "stripe", "body", seat("cab"));
  // light bar on the cab roof; red marker lamps on the box (front-face top corners, three per flank, rear corners)
  add("lightbar", slab(-0.664, 0.664, 2.05, 2.24, 1.017, 1.497), "stripe", "prop");
  for (const [t, sg] of LR) {
    const [f0, f1] = sg > 0 ? [0.727, 0.964] : [-0.964, -0.727];
    add(`marker_${t}`, plateZ(0.79, 1, f0, f1, 2.233, 2.383), "stripe", "prop", seat("box"));
    add(`rearLamp_${t}`, plateZ(-2.52, -1, f0, f1, 2.208, 2.389), "stripe", "prop", seat("box"));
    for (const [k, z0, z1] of [["a", 0.399, 0.655], ["b", -1.547, -1.291], ["c", -2.402, -2.146]]) {
      add(`sidelamp_${t}${k}`, plateX(1.07, sg, 2.196, 2.383, z0, z1), "stripe", "prop", seat("box"));
    }
  }

  // nose: headlights, grille; bumpers (front z 2.377 .. 2.651, rear step z -2.657 .. -1.148; the step is +-1.14 in the
  // rear view but hidden behind the +-1.082 front bumper in the front view: +-1.10)
  for (const [t, sg] of LR) {
    add(`lamp_${t}`, plateZ(2.595, 1, sg > 0 ? 0.558 : -0.87, sg > 0 ? 0.87 : -0.558, 0.655, 0.848), "lamp", "headlight", seat("cab"));
  }
  add("grille", plateZ(2.595, 1, -0.48, 0.48, 0.605, 0.873), "grille", "grille", seat("cab"));
  add("bumper_front", slab(-1.082, 1.082, 0.31, 0.575, 2.377, 2.651), "bumper", "bumper", seat("cab"));
  add("step_rear", slab(-1.1, 1.1, 0.31, 0.58, -2.657, -1.148), "bumper", "bumper", seat("box"));

  // mirrors: heads x 1.107 .. 1.313, y 1.229 .. 1.528 (front view), z 1.67 .. 1.87 (side view); a diagonal arm from the
  // door's front edge (root z 1.99, seated in the cab; the concept's stub runs toward the nose) back to the head's inner
  // edge -> arm 0.26 m (vehicle rule 0.25 .. 0.45)
  for (const [t, sg] of LR) {
    const [m0, m1] = sg > 0 ? [1.107, 1.313] : [-1.313, -1.107];
    add(`mirror_head_${t}`, slab(m0, m1, 1.229, 1.528, 1.67, 1.87), "mirror", "mirror", seat(`mirror_arm_${t}`));
    const ends = [[0.97, 1.02, 1.94, 1.99], [1.077, 1.127, 1.745, 1.795]];
    const arm = K.hull(ends.flatMap(([x0, x1, z0, z1]) => [x0, x1].flatMap((x) => [z0, z1].flatMap((z) => [1.33, 1.39].map((y) => [sg * X(x), Y(y), Z(z)])))));
    add(`mirror_arm_${t}`, arm, "mirror", "mirror", seat("cab", `mirror_head_${t}`));
  }

  // wheels: tyre x 0.664 .. 1.014 (front / rear views, inner face flush with the body core), hub disc seated in the
  // outer face (side-view hub R 0.215)
  for (const [tag, zc] of [["f", 1.974], ["r", -0.72]]) {
    for (const [t, sg] of LR) {
      const [a, b] = sg > 0 ? [X(0.664), X(1.014)] : [-X(1.014), -X(0.664)];
      add(`tyre_${tag}${t}`, disc(a, b, R, Z(zc), R), "tyre", "tyre");
      const [h0, h1] = sg > 0 ? [b + PROUD - T, b + PROUD] : [a - PROUD, a - PROUD + T];
      add(`hub_${tag}${t}`, disc(h0, h1, R, Z(zc), 0.535 * R), "hub", "hub", seat(`tyre_${tag}${t}`));
    }
  }
  return parts;
}
