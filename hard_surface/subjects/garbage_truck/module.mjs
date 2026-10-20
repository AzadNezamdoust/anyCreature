// BLOCKOUT start module — cab-over rear-loader garbage truck (refs/garbage_truck.png). Primitive masses sized from the
// REGISTERED turnaround (subjects/garbage_truck/turnaround/views.json; front / rear / top regenerated 2026-09-27 for the
// cab-width drift, side kept: W anchor 2.5 m -> L 7.099 (green span cab nose .. hopper frame), H 3.414 (hopper lip);
// wheel R 0.593, centres z +2.467 / -1.208 read off the side-view tyre / hub components). Every number below is a
// registered metre at the knob defaults L0 / W0 / H0 and is stretched per axis with the L / W / H knobs.
// Widths: the cab is WIDER than the refuse body (cab +-1.27: front view 1.315, rear 1.273, top 1.22; body +-1.12;
// bumper +-1.50: front 1.558, rear 1.50, top 1.44) — the concept draws it that way; the W residuals are the cab vs body.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 7.099, min: 6.5, max: 10.0, unit: "m" },   // green span (cab nose .. hopper frame; side / top)
  W:      { v: 2.5, min: 2.2, max: 2.8, unit: "m" },      // anchor
  H:      { v: 3.414, min: 3.2, max: 4.3, unit: "m" },    // ground to the hopper lip
  wheelR: { v: 0.593, min: 0.5, max: 0.75, unit: "m" },
  frameScale: { v: 0.955, min: 0.7, max: 1.4, unit: "scale", group: "frame" },   // concept-view similarity (registered.mjs)
  frameX:     { v: -25.5, min: -48, max: 48, unit: "px", group: "frame" },
  frameY:     { v: -9, min: -48, max: 48, unit: "px", group: "frame" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    body: "#43863b",
    hopper: "#2d5c34",
    mouth: "#153b21",
    glass: "#a1b4c4",
    bumper: "#adacac",
    hub: "#adacac",
    tyre: "#36393c",
    trim: "#26292c",
    grille: "#7e848a",
    lamp: "#feeaa4",
  },
};

const L0 = 7.099, W0 = 2.5, H0 = 3.414;

export function build() {
  const L = KNOBS.L.v, W = KNOBS.W.v, H = KNOBS.H.v, R = KNOBS.wheelR.v;
  const X = (v) => v * W / W0, Y = (v) => v * H / H0, Z = (v) => v * L / L0;
  const parts = [];
  const add = (id, solid, zone, role, extra = {}) => parts.push({ id, solid, zone, role, ...extra });
  /** a part MEANT to sit inside its hosts (kernel contact policy: touches + embed) */
  const seat = (...hosts) => ({ touches: hosts, embed: true });
  /** axis-aligned block, registered metres */
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([(X(x0) + X(x1)) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  /** hull of x-symmetric side-profile points [[y, z], ...] at half width hw */
  const prism = (pts, hw) => K.hull(pts.flatMap(([y, z]) => [[-X(hw), Y(y), Z(z)], [X(hw), Y(y), Z(z)]]));
  /** disc on the x axis: x0..x1, centre (y, z), radius r */
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);

  // chassis rails under everything (clearance 0.39)
  add("chassis", slab(-0.8, 0.8, 0.39, 0.8, -1.98, 3.4), "trim", "chassis");
  // cab: flat front (z 3.55) to y 2.50, then leaning back to the roof edge z 3.30 at y 2.96 (side view), back at z 1.83
  // (+ the nose below the cab floor, down to the bumper bottom: the bumper seats on the nose face)
  add("cab", K.union(prism([[0.78, 1.83], [0.78, 3.55], [2.5, 3.55], [2.96, 3.3], [2.96, 1.83]], 1.27), slab(-1.27, 1.27, 0.37, 0.8, 3.2, 3.55)), "body", "cab", seat("chassis"));
  // refuse body (side view z 1.82 .. -2.16, bottom 0.66, roof 3.358; top view +-1.12)
  add("refuse_body", slab(-1.12, 1.12, 0.66, 3.358, -2.16, 1.82), "body", "body", seat("cab", "chassis"));
  // rear-loader hopper: side profile (lip 3.41 at z -1.94..-2.10, 3.16 at -2.58, the slanted tailgate down to z -3.65 at
  // y 1.58, the hopper's vertical back to 1.0; bottom 0.36)
  add("hopper", prism([[0.36, -1.94], [0.36, -3.49], [1.0, -3.65], [1.58, -3.65], [1.9, -3.4], [3.16, -2.58], [3.41, -2.1], [3.41, -1.94]], 1.1), "hopper", "body", seat("refuse_body", "chassis"));
  // the dark loading mouth: seen through the hopper's open sides (side view z -2.19..-3.48, y 0.80..3.15) and on the
  // slanted tailgate face (rear view x +-0.80, y 1.10..2.65)
  const mouthSide = [[0.86, -2.24], [0.86, -3.4], [1.64, -3.4], [2.97, -2.5], [2.97, -2.24]];
  for (const [side, sg] of [["l", 1], ["r", -1]]) {
    const [a, b] = sg > 0 ? [1.08, 1.125] : [-1.125, -1.08];
    add(`mouth_${side}`, K.hull(mouthSide.flatMap(([y, z]) => [[X(a), Y(y), Z(z)], [X(b), Y(y), Z(z)]])), "mouth", "window", seat("hopper"));
  }
  const slantZ = (y) => -3.65 + (y - 1.58) * (1.07 / 1.58);
  add("mouth_rear", K.hull([1.65, 2.65].flatMap((y) => [-0.8, 0.8].flatMap((x) => [[X(x), Y(y), Z(slantZ(y) - 0.02)], [X(x), Y(y), Z(slantZ(y) + 0.03)]]))), "mouth", "window", seat("hopper"));
  // side skirt between the wheels (side view z 1.82..-0.58, y 0.43..0.85), front bumper, rear step
  add("skirt", slab(-1.14, 1.14, 0.43, 0.85, -0.58, 1.8), "bumper", "body", seat("refuse_body", "chassis"));
  add("bumper_front", slab(-1.5, 1.5, 0.37, 0.8, 3.38, 3.76), "bumper", "bumper", seat("cab", "chassis"));   // 0.02 into the chassis front and the cab floor
  add("step_rear", slab(-0.66, 0.66, 0.4, 0.62, -3.75, -3.45), "bumper", "bumper", seat("hopper"));   // top view z -3.49..-3.71: sticks out behind the hopper
  // glass: windshield plate on the flat cab front (front view x +-1.147), door windows on both flanks
  add("windshield", slab(-1.147, 1.147, 1.8, 2.5, 3.54, 3.585), "glass", "window", seat("cab"));
  for (const [side, sg] of [["l", 1], ["r", -1]]) {
    add(`window_side_${side}`, slab(sg > 0 ? 1.255 : -1.3, sg > 0 ? 1.3 : -1.255, 1.85, 2.6, 2.29, 3.23), "glass", "window", seat("cab"));
    const [l0, l1] = sg > 0 ? [0.737, 1.129] : [-1.129, -0.737];
    add(`headlight_${side}`, slab(l0, l1, 0.933, 1.297, 3.54, 3.585), "lamp", "headlight", seat("cab"));
    // mirror heads outboard of the cab (front view x 1.39..1.716, y 1.95..2.65; top view z 2.99..3.28)
    const [m0, m1] = sg > 0 ? [1.39, 1.716] : [-1.716, -1.39];
    add(`mirror_${side}`, slab(m0, m1, 1.95, 2.65, 3.0, 3.28), "trim", "mirror");
    const [r0, r1] = sg > 0 ? [1.26, 1.4] : [-1.4, -1.26];
    add(`mirror_arm_${side}`, slab(r0, r1, 2.25, 2.3, 3.235, 3.28), "trim", "mirror", seat("cab", `mirror_${side}`));
  }
  add("grille", slab(-0.56, 0.56, 0.877, 1.353, 3.54, 3.585), "grille", "grille", seat("cab"));
  // wheels: front tyres x 0.774..1.287 (front view), rear 0.592..1.227 (rear view); hub disc on the outer face
  for (const [tag, zc, x0, x1] of [["f", 2.467, 0.774, 1.287], ["r", -1.208, 0.592, 1.227]]) {
    for (const [side, sg] of [["l", 1], ["r", -1]]) {
      const [a, b] = sg > 0 ? [X(x0), X(x1)] : [-X(x1), -X(x0)];
      add(`tyre_${tag}${side}`, disc(a, b, R, Z(zc), R), "tyre", "tyre", seat(tag === "f" ? "cab" : "refuse_body", "chassis"));
      const [h0, h1] = sg > 0 ? [b - 0.005, b + 0.04] : [a - 0.04, a + 0.005];
      add(`hub_${tag}${side}`, disc(h0, h1, R, Z(zc), 0.5 * R), "hub", "hub", seat(`tyre_${tag}${side}`));
    }
  }
  return parts;
}
