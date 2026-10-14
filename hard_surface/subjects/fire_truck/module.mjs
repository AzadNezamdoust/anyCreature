// BLOCKOUT start module — fire engine with roof ladder (refs/fire_truck.png). Primitive masses sized from the REGISTERED
// turnaround (subjects/fire_truck/turnaround/views.json: W anchor 2.5 m -> 119.6 px/m; cab nose z +3.612 .. body rear
// z -3.612, body roof 2.40, ladder top 2.667; wheel R 0.472, centres z +2.3745 / -1.275 / -2.358 read off the side-view hub
// components). Every number below is a registered metre at the knob defaults L0 / W0 / H0 and is stretched per axis with
// the L / W / H knobs. Widths: cab +-1.24 (front / top views), body +-1.25 (top +-1.23, rear +-1.296).
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.
import * as K from "../../src/kernel/index.mjs";

export const KNOBS = {
  L:      { v: 7.224, min: 6.2, max: 8.6, unit: "m" },    // body paint span: cab nose .. equipment-body rear (side / top)
  W:      { v: 2.5, min: 2.2, max: 2.8, unit: "m" },      // anchor
  H:      { v: 2.4, min: 2.1, max: 2.9, unit: "m" },      // ground to the equipment-body roof (ladder on top)
  wheelR: { v: 0.472, min: 0.4, max: 0.56, unit: "m" },
  frameScale: { v: 0.98, min: 0.7, max: 1.4, unit: "scale", group: "frame" },   // concept-view similarity (registered.mjs)
  frameX:     { v: 4, min: -48, max: 48, unit: "px", group: "frame" },
  frameY:     { v: 4, min: -48, max: 48, unit: "px", group: "frame" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // turnaround/views.json families.table (concept flat colours)
  palette: {
    body: "#d9241c",
    bar: "#b3201c",
    stripe: "#f5f5f5",
    locker: "#a6a7a9",
    ladder: "#bbbbbc",
    glass: "#8aaec8",
    mirror: "#a6a7a9",
    tyre: "#333435",
    hub: "#a6a7a9",
    bumper: "#a6a7a9",
    lamp: "#fbf9ec",
    grille: "#a6a7a9",
  },
};

const L0 = 7.224, W0 = 2.5, H0 = 2.4;
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
  /** hull of side-profile points [[y, z, halfWidth], ...] mirrored across x = 0 */
  const hullYZ = (pts) => K.hull(pts.flatMap(([y, z, hw]) => [[-X(hw), Y(y), Z(z)], [X(hw), Y(y), Z(z)]]));
  /** disc on the x axis: x0..x1 (world m), centre (y, z), radius r */
  const disc = (x0, x1, yc, zc, r, n = 20) => K.extrude(K.profile.poly(Array.from({ length: n }, (_, i) => [r * Math.cos(2 * Math.PI * i / n), r * Math.sin(2 * Math.PI * i / n)])), x1 - x0).rotY(90).at([x0, yc, zc]);
  /** a detail plate on the flank face x = +-xf (world thickness T, PROUD outside), registered y / z */
  const plateX = (xf, sg, y0, y1, z0, z1) => {
    const a = X(xf) + PROUD - T, b = X(xf) + PROUD;
    return K.box([T, Y(y1) - Y(y0), Z(z1) - Z(z0)]).at([sg * (a + b) / 2, Y(y0), (Z(z0) + Z(z1)) / 2]);
  };
  /** a detail plate on a face z = zf looking along +z (dir 1) or -z (dir -1) */
  const plateZ = (zf, dir, x0, x1, y0, y1) => K.box([X(x1) - X(x0), Y(y1) - Y(y0), T]).at([(X(x0) + X(x1)) / 2, Y(y0), Z(zf) + dir * (PROUD - T / 2)]);
  const LR = [["l", 1], ["r", -1]];
  const mx = (sg, a, b) => (sg > 0 ? [a, b] : [-b, -a]);

  // crew cab: vertical nose z 3.612 up to 1.40, raked windshield face to z 3.30 at 2.18, roof 2.34 (side view); +-1.24,
  // top corners chamfered to +-1.12 (front view); sill core between the tyres + skirts around the front arch (z 1.85 .. 2.90)
  add("cab", K.union(
    hullYZ([[0.95, 1.095, 1.24], [0.95, 3.612, 1.24], [1.4, 3.612, 1.24], [2.0, 3.372, 1.24], [2.0, 1.095, 1.24]]),
    hullYZ([[2.0, 1.095, 1.24], [2.0, 3.372, 1.24], [2.18, 3.3, 1.18], [2.34, 3.2, 1.12], [2.34, 1.095, 1.12]]),
    slab(-0.727, 0.727, 0.41, 0.95, 1.095, 3.612),
    slab(-1.24, 1.24, 0.41, 0.95, 1.095, 1.85),
    slab(-1.24, 1.24, 0.41, 0.95, 2.9, 3.612),
  ), "body", "cab");
  // connector between the cab and the equipment body (side view z 0.828 .. 1.095, top view +-1.04)
  add("connector", slab(-1.04, 1.04, 0.46, 2.316, 0.828, 1.095), "body", "body");
  // equipment body: full width above the tandem arch (y 1.0), core between the rear tyres (x +-0.76) down to 0.40,
  // skirts ahead of (z > -0.75) and behind (z < -2.88) the tandem
  add("body", K.union(
    slab(-1.25, 1.25, 1.0, 2.4, -3.612, 0.828),
    slab(-0.76, 0.76, 0.4, 1.0, -3.612, 0.828),
    slab(-1.25, 1.25, 0.4, 1.0, -0.75, 0.828),
    slab(-1.25, 1.25, 0.4, 1.0, -3.612, -2.88),
  ), "body", "body");

  // glass: windshield on the raked face (side view glass y 1.40 .. 2.18; front view +-1.137), crew-cab side windows
  const rake = (y) => 3.612 - 0.4 * (y - 1.4);
  const nY = 0.371, nZ = 0.928;   // raked-face outward normal (y, z)
  const ws = [1.42, 2.14].flatMap((y) => [PROUD - T, PROUD].flatMap((o) => [-1, 1].map((sx) => [sx * X(1.137), Y(y) + nY * o, Z(rake(y)) + nZ * o])));
  add("windshield", K.hull(ws), "glass", "window", seat("cab"));
  for (const [t, sg] of LR) {
    for (const [k, z0, z1] of [["a", 2.525, 3.152], ["b", 1.948, 2.357], ["c", 1.229, 1.781]]) {
      add(`window_${t}${k}`, plateX(1.24, sg, 1.497, 2.166, z0, z1), "glass", "window", seat("cab"));
    }
  }

  // lockers (grey roll-up doors) on both body flanks + the rear roll-up door; the white stripe band
  for (const [t, sg] of LR) {
    add(`locker_${t}a`, plateX(1.25, sg, 1.112, 2.166, -0.552, 0.727), "locker", "body", seat("body"));
    add(`locker_${t}b`, plateX(1.25, sg, 1.279, 2.166, -1.957, -0.661), "locker", "body", seat("body"));
    add(`locker_${t}c`, plateX(1.25, sg, 1.279, 2.166, -3.361, -2.065), "locker", "body", seat("body"));
    add(`stripe_body_${t}`, plateX(1.25, sg, 1.12, 1.279, -3.612, 0.828), "stripe", "body", seat("body", `locker_${t}a`, `locker_${t}b`, `locker_${t}c`));
    add(`stripe_cab_${t}`, plateX(1.24, sg, 1.07, 1.221, 1.095, 3.612), "stripe", "body", seat("cab"));
  }
  add("locker_rear", plateZ(-3.612, -1, -0.828, 0.828, 1.263, 2.09), "locker", "body", seat("body"));
  add("stripe_rear", plateZ(-3.612, -1, -1.25, 1.25, 1.045, 1.204), "stripe", "body", seat("body"));

  // light bar on the cab roof (side view z 2.36 .. 3.17, top 2.567; front view +-0.85, white centre +-0.19)
  add("lightbar_l", slab(0.19, 0.85, 2.34, 2.567, 2.36, 3.17), "bar", "prop");
  add("lightbar_r", slab(-0.85, -0.19, 2.34, 2.567, 2.36, 3.17), "bar", "prop");
  add("lightbar_centre", slab(-0.19, 0.19, 2.34, 2.567, 2.36, 3.17), "stripe", "prop");
  // red roof lamps at the body's rear corners (top view x +-0.72 .. 1.03; side view z -3.20 .. -3.50, top 2.49) and
  // the small red lamps on the rear face (rear view +-0.94 .. 1.20, y 1.98 .. 2.11)
  for (const [t, sg] of LR) {
    const [a, b] = mx(sg, 0.72, 1.03);
    add(`rooflamp_${t}`, slab(a, b, 2.4, 2.49, -3.5, -3.2), "bar", "prop");
    const [c, d] = mx(sg, 0.94, 1.2);
    add(`rearLamp_${t}`, plateZ(-3.612, -1, c, d, 1.98, 2.11), "bar", "headlight", seat("body"));
  }

  // roof ladder: rails x +-0.37 .. 0.56, y 2.508 .. 2.667, z -3.077 .. 1.154 (side / front views), posts down to the roof
  // at z 0.62 / -1.01 / -2.68, nine rungs
  for (const [t, sg] of LR) {
    const [a, b] = mx(sg, 0.37, 0.56);
    add(`ladder_rail_${t}`, slab(a, b, 2.508, 2.667, -3.077, 1.154), "ladder", "prop");
    for (const [k, zc] of [["a", 0.62], ["b", -1.01], ["c", -2.68]]) {
      add(`ladder_post_${t}${k}`, slab(a, b, 2.4, 2.52, zc - 0.07, zc + 0.07), "ladder", "prop", seat(`ladder_rail_${t}`));
    }
  }
  for (let i = 0; i < 9; i += 1) {
    const zc = 0.95 - i * 0.48;
    add(`ladder_rung_${i}`, slab(-0.38, 0.38, 2.56, 2.62, zc - 0.03, zc + 0.03), "ladder", "prop", seat("ladder_rail_l", "ladder_rail_r"));
  }

  // nose: headlights, grille; bumpers (front z 3.40 .. 3.73, rear z -3.72 .. -3.35)
  for (const [t, sg] of LR) {
    const [a, b] = mx(sg, 0.702, 1.104);
    add(`lamp_${t}`, plateZ(3.612, 1, a, b, 0.744, 0.945), "lamp", "headlight", seat("cab"));
  }
  add("grille", plateZ(3.612, 1, -0.573, 0.573, 0.652, 1.062), "grille", "grille", seat("cab"));
  add("bumper_front", slab(-1.3, 1.3, 0.35, 0.64, 3.4, 3.73), "bumper", "bumper", seat("cab"));
  add("bumper_rear", slab(-1.33, 1.33, 0.4, 0.66, -3.72, -3.35), "bumper", "bumper", seat("body"));

  // mirrors: heads x 1.313 .. 1.522, y 1.35 .. 1.75 (front / side views), z 3.08 .. 3.21; a diagonal arm from the cab
  // flank ahead of the head (root z 3.40) -> arm 0.27 m (vehicle rule 0.25 .. 0.45)
  for (const [t, sg] of LR) {
    const [a, b] = mx(sg, 1.313, 1.522);
    add(`mirror_head_${t}`, slab(a, b, 1.35, 1.75, 3.08, 3.21), "mirror", "mirror", seat(`mirror_arm_${t}`));
    const ends = [[1.21, 1.26, 3.37, 3.42], [1.293, 1.343, 3.12, 3.17]];
    const arm = K.hull(ends.flatMap(([x0, x1, z0, z1]) => [x0, x1].flatMap((x) => [z0, z1].flatMap((z) => [1.3, 1.36].map((y) => [sg * X(x), Y(y), Z(z)])))));
    add(`mirror_arm_${t}`, arm, "mirror", "mirror", seat("cab", `mirror_head_${t}`));
  }

  // wheels: front tyres x 0.727 .. 1.212 (front view), rear tandem x 0.76 .. 1.263 (rear view), inner faces flush with the
  // body cores; hub discs seated in the outer faces (side-view hub R 0.2385)
  for (const [tag, zc, x0, x1] of [["f", 2.3745, 0.727, 1.212], ["m", -1.275, 0.76, 1.263], ["r", -2.358, 0.76, 1.263]]) {
    for (const [t, sg] of LR) {
      const [a, b] = sg > 0 ? [X(x0), X(x1)] : [-X(x1), -X(x0)];
      add(`tyre_${tag}${t}`, disc(a, b, R, Z(zc), R), "tyre", "tyre");
      const [h0, h1] = sg > 0 ? [b + PROUD - T, b + PROUD] : [a - PROUD, a - PROUD + T];
      add(`hub_${tag}${t}`, disc(h0, h1, R, Z(zc), 0.505 * R), "hub", "hub", seat(`tyre_${tag}${t}`));
    }
  }
  return parts;
}
