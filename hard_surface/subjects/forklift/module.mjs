// BLOCKOUT start module — warehouse forklift (refs/forklift.png). Primitive masses sized from the REGISTERED turnaround
// (subjects/forklift/turnaround/views.json: W anchor 1.2 m -> L 2.168 (the yellow span: body + counterweight + guard),
// H 2.677 (mast top); front wheels R 0.36 at z +0.973, rear wheels R 0.27 at z -0.78, read off the side-view tyre / hub
// components). Every number below is a registered metre at the knob defaults L0 / W0 / H0 and is stretched per axis
// with the L / W / H knobs. The mast, carriage and forks (dark) stand ahead of the yellow span: mast face z 1.17..1.42,
// forks to z 2.72. The overhead guard is see-through (open posts, slatted roof): no enclosed-white rule for this subject.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 2.168, min: 1.8, max: 2.8, unit: "m" },    // yellow span (side / top): body front .. counterweight back
  W:      { v: 1.2, min: 1.0, max: 1.4, unit: "m" },      // anchor
  H:      { v: 2.677, min: 2.2, max: 3.4, unit: "m" },    // ground to the mast top
  wheelR: { v: 0.36, min: 0.28, max: 0.45, unit: "m" },   // front (drive) wheels; the rear wheels are 0.75 x
  frameScale: { v: 1, min: 0.7, max: 1.4, unit: "scale", group: "frame" },   // concept-view similarity (registered.mjs)
  frameX:     { v: 0, min: -48, max: 48, unit: "px", group: "frame" },
  frameY:     { v: 0, min: -48, max: 48, unit: "px", group: "frame" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    body: "#fbcb15",
    mast: "#444649",
    tyre: "#333436",
    seat: "#1c1c1c",
    hub: "#b2b2b4",
    beacon: "#f67006",
  },
};

const L0 = 2.168, W0 = 1.2, H0 = 2.677;

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
  /** square post between two author points (registered metres), section d */
  const post = (p0, p1, d) => K.beam([X(p0[0]), Y(p0[1]), Z(p0[2])], [X(p1[0]), Y(p1[1]), Z(p1[2])], { w: d, h: d });

  // yellow body: the low chassis tub (side view y 0.22..1.10, z -0.50..1.07), the cowl under the steering column and
  // the rounded counterweight at the back (z -0.46..-1.07, y 0.46..1.23; rear view x +-0.66)
  add("body", slab(-0.54, 0.54, 0.22, 1.08, -0.5, 1.07), "body", "body");
  add("cowl", prism([[1.08, 0.62], [1.08, 1.02], [1.4, 0.9], [1.4, 0.7]], 0.3), "body", "body");
  add("counterweight", K.hull(
    slab(-0.62, 0.62, 0.42, 1.1, -1.073, -0.46),
    slab(-0.55, 0.55, 1.1, 1.233, -1.0, -0.46),
  ), "body", "body", seat("body"));
  // overhead guard: two raked front posts, two plumb rear posts (x +-0.515), roof frame at y 2.09..2.20 with 4 slats
  for (const sg of [1, -1]) {
    const x = 0.515 * sg;
    add(`guard_post_f${sg > 0 ? "l" : "r"}`, post([x, 1.0, 0.88], [x, 2.1, 0.77], 0.09), "body", "cab", seat("body"));
    add(`guard_post_r${sg > 0 ? "l" : "r"}`, slab(x - 0.045, x + 0.045, 1.08, 2.1, -0.46, -0.34), "body", "cab");
    add(`guard_rail_${sg > 0 ? "l" : "r"}`, slab(x - 0.045, x + 0.045, 2.09, 2.2, -0.46, 0.82), "body", "cab");
  }
  add("guard_bar_f", slab(-0.56, 0.56, 2.09, 2.2, 0.74, 0.82), "body", "cab", seat("guard_rail_l", "guard_rail_r"));
  add("guard_bar_r", slab(-0.56, 0.56, 2.09, 2.2, -0.46, -0.38), "body", "cab", seat("guard_rail_l", "guard_rail_r"));
  for (const [i, x] of [-0.305, -0.1, 0.165, 0.385].entries()) add(`guard_slat_${i}`, slab(x - 0.04, x + 0.04, 2.11, 2.18, -0.38, 0.74), "body", "cab");
  add("beacon", slab(0.4, 0.5, 2.2, 2.36, -0.38, -0.26), "beacon", "prop");
  // seat + steering (dark)
  add("seat", slab(-0.25, 0.25, 1.08, 1.24, -0.3, 0.25), "seat", "cab");
  add("seat_back", slab(-0.25, 0.25, 1.24, 1.64, -0.3, -0.12), "seat", "cab");
  add("steering_column", post([0, 1.1, 0.82], [0, 1.45, 0.6], 0.08), "mast", "cab", seat("cowl"));
  // steering wheel: a disc (r 0.15) on the column top, tilted 60 deg toward the seat (side view z 0.38..0.69, y 1.34..1.57)
  const wheelDisc = K.extrude(K.profile.poly(Array.from({ length: 16 }, (_, i) => [0.15 * Math.cos(Math.PI * i / 8), 0.15 * Math.sin(Math.PI * i / 8)])), 0.03);
  add("steering_wheel", wheelDisc.rotX(60).at([0, Y(1.45), Z(0.56)]), "seat", "cab", seat("steering_column"));
  // mast: two rails (rear view x +-0.32, 0.17 wide) from the ground block to the top, three cross bars, the carriage
  // plate and the fork uprights ahead of it
  for (const sg of [1, -1]) add(`mast_rail_${sg > 0 ? "l" : "r"}`, slab(0.32 * sg - 0.085, 0.32 * sg + 0.085, 0.19, 2.677, 1.17, 1.38), "mast", "chassis");
  for (const [i, y] of [2.42, 1.83].entries()) add(`mast_bar_${i}`, slab(-0.32, 0.32, y, y + 0.13, 1.2, 1.35), "mast", "chassis", seat("mast_rail_l", "mast_rail_r"));
  add("carriage", slab(-0.4, 0.4, 0.24, 0.92, 1.38, 1.45), "mast", "chassis");
  // mast mount (tilt pivot on the front axle housing): the rails' back face z 1.17 to the body front z 1.07
  add("mast_mount", slab(-0.4, 0.4, 0.25, 0.55, 1.068, 1.172), "mast", "chassis");   // 2 mm into each: joins the union
  // forks: top view x +-(0.26..0.44), flat blades y 0.12..0.21 to z 2.72, uprights on the carriage face to y 0.91
  for (const sg of [1, -1]) {
    const [a, b] = sg > 0 ? [0.26, 0.44] : [-0.44, -0.26];
    add(`fork_${sg > 0 ? "l" : "r"}`, K.union(slab(a, b, 0.12, 0.21, 1.45, 2.72), slab(a, b, 0.12, 0.91, 1.45, 1.53)), "mast", "prop");
  }
  // wheels: front (drive) R at z 0.973, x 0.53..0.72; rear 0.75 R at z -0.78, x 0.40..0.63 (front / rear views)
  const Rr = 0.75 * R;
  for (const [tag, zc, r, x0, x1] of [["f", 0.973, R, 0.53, 0.72], ["r", -0.78, Rr, 0.4, 0.63]]) {
    for (const [side, sg] of [["l", 1], ["r", -1]]) {
      const [a, b] = sg > 0 ? [X(x0), X(x1)] : [-X(x1), -X(x0)];
      add(`tyre_${tag}${side}`, disc(a, b, r, Z(zc), r), "tyre", "tyre", seat(tag === "f" ? "body" : "counterweight"));
      const [h0, h1] = sg > 0 ? [b - 0.005, b + 0.04] : [a - 0.04, a + 0.005];   // 0.045 thick (vehicle style floor 0.04)
      add(`hub_${tag}${side}`, disc(h0, h1, r, Z(zc), 0.5 * r), "hub", "hub", seat(`tyre_${tag}${side}`));
    }
  }
  return parts;
}
