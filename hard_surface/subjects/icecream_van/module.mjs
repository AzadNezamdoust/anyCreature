// BLOCKOUT start module — ice-cream van (refs/icecream_van.png). Primitive masses sized from the REGISTERED turnaround
// (subjects/icecream_van/turnaround/views.json; side / front / rear regenerated 2026-09-27 for proportion drift, top kept:
// W anchor 2.0 m -> L 4.669 (body paint span, bonnet nose .. rear face), H 4.446 incl. the roof cone sign (roof 2.95);
// wheel R 0.45, centres z +1.59 / -1.51 read off the side-view hub components). Every number below is a registered metre
// at the knob defaults L0 / W0 / H0 and is stretched per axis with the L / W / H knobs. Two-tone paint: pink below
// y 1.45, cream above. The serving window, awning and counter are on the near (+x) flank only.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 4.669, min: 3.4, max: 5.6, unit: "m" },    // body paint span (side / top)
  W:      { v: 2.0, min: 1.8, max: 2.2, unit: "m" },      // anchor
  H:      { v: 4.446, min: 3.4, max: 5.0, unit: "m" },    // ground to the top of the cone sign's scoop
  wheelR: { v: 0.45, min: 0.3, max: 0.55, unit: "m" },
  frameScale: { v: 0.97, min: 0.7, max: 1.4, unit: "scale", group: "frame" },   // concept-view similarity (registered.mjs)
  frameX:     { v: 7, min: -48, max: 48, unit: "px", group: "frame" },
  frameY:     { v: 16, min: -48, max: 48, unit: "px", group: "frame" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    pink: "#f399b4",
    cream: "#f6ecd3",
    glass: "#9eb8cd",
    bumper: "#babbbc",
    trim: "#ced1d3",
    tyre: "#3d3d3d",
    hub: "#babbbc",
    cone: "#d9ab6d",
    lamp: "#fbedad",
  },
};

const L0 = 4.669, W0 = 2.0, H0 = 4.446;

export function build() {
  const L = KNOBS.L.v, W = KNOBS.W.v, H = KNOBS.H.v, R = KNOBS.wheelR.v;
  const X = (v) => v * W / W0, Y = (v) => v * H / H0, Z = (v) => v * L / L0;
  const parts = [];
  const add = (id, solid, zone, role, extra = {}) => parts.push({ id, solid, zone, role, ...extra });
  /** a part MEANT to sit inside its hosts (kernel contact policy: touches + embed) */
  const seat = (...hosts) => ({ touches: hosts, embed: true });
  /** axis-aligned block, registered metres */
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([(X(x0) + X(x1)) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  /** hull of x-symmetric side-profile points [[y, z, hw], ...] (per-point half width) */
  const prism = (pts) => K.hull(pts.flatMap(([y, z, hw]) => [[-X(hw), Y(y), Z(z)], [X(hw), Y(y), Z(z)]]));
  /** disc on the x axis: x0..x1, centre (y, z), radius r */
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);
  /** solid of revolution about the vertical axis through (x, z): profile [[r, y], ...] (registered metres) */
  const turned = (pts, x, z, segs = 16) => K.revolve(K.profile.poly(pts.map(([r, y]) => [X(r), Y(y)])), segs).at([X(x), 0, Z(z)]);

  // pink lower body (front / rear views x +-0.92, side view y 0.43..1.45, nose face z 2.34 .. rear face -2.33) and the
  // short rounded bonnet on top of it (side view: 1.55 at z 2.25, 1.65 at 2.05, 1.70 at the windshield foot z 1.87)
  add("body_lower", slab(-0.92, 0.92, 0.43, 1.45, -2.33, 2.34), "pink", "body");
  add("bonnet", prism([[1.45, 1.87, 0.9], [1.45, 2.3, 0.9], [1.55, 2.25, 0.9], [1.65, 2.05, 0.9], [1.7, 1.87, 0.9]]), "pink", "body");
  // cream cab + box: windshield rake from (y 1.70, z 1.87) to (2.80, 1.45), roof 2.95 from z 1.25 to the rounded rear
  // corner (2.95 at -2.18, 2.75 at the rear face -2.33); the roof edges round in to x +-0.85 (front view)
  add("body_upper", prism([
    [1.45, 1.87, 0.92], [1.45, -2.33, 0.92], [2.62, -2.33, 0.92], [2.95, -2.18, 0.85],
    [2.95, 1.25, 0.85], [2.8, 1.45, 0.9], [1.7, 1.87, 0.92],
  ]), "cream", "body");
  // glass: windshield on the rake (front view x +-0.81, y 1.72..2.36), door windows (both flanks), serving window (+x)
  const rakeZ = (y) => 1.87 - (y - 1.7) * (0.42 / 1.1);
  add("windshield", K.hull([1.72, 2.36].flatMap((y) => [-0.81, 0.81].flatMap((x) => [[X(x), Y(y), Z(rakeZ(y) + 0.025)], [X(x), Y(y), Z(rakeZ(y) - 0.025)]]))), "glass", "window", seat("body_upper"));
  for (const [side, sg] of [["l", 1], ["r", -1]]) add(`window_door_${side}`, slab(sg > 0 ? 0.905 : -0.95, sg > 0 ? 0.95 : -0.905, 1.67, 2.45, 0.87, 1.6), "glass", "window", seat("body_upper"));
  add("serving_window", slab(0.905, 0.95, 1.69, 2.28, -1.94, 0.23), "glass", "window", seat("body_upper"));
  // awning (sloped, pink / cream stripes: body colours; top view x 0.99..1.30) and the grey counter below the window
  add("awning", K.hull([[0.92, 2.69], [1.3, 2.29], [0.92, 2.62], [1.3, 2.22]].flatMap(([x, y]) => [[X(x), Y(y), Z(0.4)], [X(x), Y(y), Z(-2.23)]])), "pink", "prop");
  add("counter", slab(0.92, 1.3, 1.47, 1.6, -2.09, 0.37), "trim", "prop");
  // bumpers (side view z 2.12..2.49 / -2.09..-2.43; front / rear views x +-1.0 / +-1.03) and the nose lamps + grille
  add("bumper_front", slab(-1.0, 1.0, 0.38, 0.72, 2.12, 2.49), "bumper", "bumper", seat("body_lower"));
  add("bumper_rear", slab(-1.034, 1.034, 0.38, 0.72, -2.43, -2.09), "bumper", "bumper", seat("body_lower"));
  add("grille", slab(-0.4, 0.4, 0.72, 1.05, 2.34, 2.385), "bumper", "grille");   // on the nose face, above the bumper top
  for (const [side, sg] of [["l", 1], ["r", -1]]) {
    const [l0, l1] = sg > 0 ? [0.52, 0.805] : [-0.805, -0.52];
    add(`headlight_${side}`, slab(l0, l1, 0.72, 1.04, 2.34, 2.385), "lamp", "headlight");
    // mirror heads on short arms at the door front (front view x 1.01..1.17, y 1.54..1.88; side view z ~1.8)
    const [m0, m1] = sg > 0 ? [1.01, 1.17] : [-1.17, -1.01];
    add(`mirror_${side}`, slab(m0, m1, 1.54, 1.88, 1.76, 1.86), "trim", "mirror");
    const [r0, r1] = sg > 0 ? [0.9, 1.01] : [-1.01, -0.9];
    add(`mirror_arm_${side}`, slab(r0, r1, 1.66, 1.71, 1.785, 1.835), "trim", "mirror", seat("body_upper"));
  }
  // roof cone sign: grey base plate (x +-0.27, z -0.41..0.15, y 2.95..3.08), tan cone (r 0.30 at the top, y 3.08..3.72),
  // pink scoop (r 0.46, y 3.64..4.446); axis at z -0.14 (side view)
  add("sign_base", slab(-0.27, 0.27, 2.95, 3.08, -0.41, 0.15), "trim", "prop");
  add("sign_cone", turned([[0, 3.08], [0.05, 3.08], [0.3, 3.72], [0, 3.72]], 0, -0.14), "cone", "prop");
  add("sign_scoop", turned(Array.from({ length: 9 }, (_, i) => { const a = -Math.PI / 2 + Math.PI * i / 8; return [Math.max(0, 0.46 * Math.cos(a)), 4.043 + 0.403 * Math.sin(a)]; }), 0, -0.14), "pink", "prop", seat("sign_cone"));
  // wheels: tyre x 0.57..0.91 (front view), hub disc on the outer face (side view hubs 0.47 across)
  for (const [tag, zc] of [["f", 1.59], ["r", -1.51]]) {
    for (const [side, sg] of [["l", 1], ["r", -1]]) {
      const [a, b] = sg > 0 ? [X(0.57), X(0.91)] : [-X(0.91), -X(0.57)];
      add(`tyre_${tag}${side}`, disc(a, b, R, Z(zc), R), "tyre", "tyre", seat("body_lower"));   // no wheel arches in the blockout
      const [h0, h1] = sg > 0 ? [b - 0.005, b + 0.04] : [a - 0.04, a + 0.005];
      add(`hub_${tag}${side}`, disc(h0, h1, R, Z(zc), 0.52 * R), "hub", "hub", seat(`tyre_${tag}${side}`, "body_lower"));
    }
  }
  return parts;
}
