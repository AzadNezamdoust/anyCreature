// Accuracy-ceiling reference: the pickup in refs/pickup_truck.png, built free-hand (no template restriction).
// Every layout number is a layout.json key (value x L / W / H); numbers marked "read off" were rectified from the
// target through refs/pickup_truck.camera.json (flank plane, 1 px unit = L / 869.9) because no key measures them.
// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  // calibrated reads (classes/vehicle.json paletteZones), flat cel colours, no outlines
  palette: {
    body: "#8ab8d9",
    bed: "#6d96b2",
    glass: "#b7c7e0",
    mirror: "#bbdcf0",
    tyre: "#5c5e5b",
    hub: "#b5babe",
    bumper: "#bcbfc5",
    lamp: "#f2eba9",
    grille: "#668296",
    tread: "#3f3f3d",
  },
};

export function build() {
  // ------------------------------------------------------------------ frame (layout.json)
  const L = 4.8;                        // class default length (m); every other size is a fraction of it
  const W = 0.412 * L;                  // width.overL
  const H = 0.546 * L;                  // height.overL: the unit every layout fraction of H is read against
  // read off (solved camera, roof corners at the tumbled-in roof edge): the roof sits at 0.962 H — the layout's H edge
  // point is the cab rear edge rectified on the flank plane, but the roof edge is 0.08 m inboard of it
  const roofY = 0.962 * H;
  const zF = L / 2;
  const fromNose = (f) => zF - f * L;
  const s = 0.001;                      // seat: sub-mm overlap the harness reads as contact
  const parts = [];
  const add = (id, solid, zone, role, extra = {}) => { const p = { id, solid, zone, role, ...extra }; parts.push(p); return p; };

  // ------------------------------------------------------------------ construction helpers
  const ccw = (pts) => {
    let a = 0;
    for (let i = 0; i < pts.length; i += 1) { const [x0, y0] = pts[i]; const [x1, y1] = pts[(i + 1) % pts.length]; a += x0 * y1 - x1 * y0; }
    return a > 0 ? pts : [...pts].reverse();
  };
  /** side profile [[z, y], ...] pushed across x0..x1 */
  const side = (pts, x0 = -W, x1 = W) => K.extrude(K.profile.poly(ccw(pts.map(([z, y]) => [-z, y]))), x1 - x0).rotY(90).at([x0, 0, 0]);
  /** front profile [[x, y], ...] pushed along z0..z1 */
  const front = (pts, z0, z1) => K.extrude(K.profile.poly(ccw(pts)), z1 - z0).at([0, 0, z0]);
  /** plan profile [[x, z], ...] pushed over y0..y1 */
  const plan = (pts, y0, y1) => K.extrude(K.profile.poly(ccw(pts.map(([x, z]) => [x, z]))), y1 - y0).rotX(90).at([0, y1, 0]);
  const slab = (x0, x1, y0, y1, z0, z1) => K.box([x1 - x0, y1 - y0, z1 - z0]).at([(x0 + x1) / 2, y0, (z0 + z1) / 2]);
  const big = K.box([30, 30, 30]).at([0, -10, 0]);
  const shift = (solid, axis, d) => solid.at(axis === 0 ? [d, 0, 0] : axis === 1 ? [0, d, 0] : [0, 0, d]);
  /** the outer skin of `base` on its (axis, sign) faces, `depth` deep — built with intersect only (no thin record) */
  const skin = (base, axis, sign, d0, d1) => K.intersect(shift(base, axis, -sign * d0), K.cut(big, shift(base, axis, -sign * d1)));
  /** half-disc / half-annulus arch profile in (z, y) about (zc, yc), with an optional skirt below yc */
  const arc = (zc, yc, r, n) => Array.from({ length: n + 1 }, (_, i) => [zc + r * Math.cos(Math.PI * i / n), yc + r * Math.sin(Math.PI * i / n)]);

  // ------------------------------------------------------------------ heights (layout.json unless noted)
  const bodyBot = 0.24 * H;             // read off: door / bed-side bottom edge, rectified at 3 points (0.234, 0.241, 0.240 H)
  const bumperTop = 0.368 * H;          // bumper.front.top
  const bumperBot = bumperTop - 0.101 * H;   // bumper.front.h
  const hoodTop = 0.591 * H;            // hood.top (the fender tops at the flank front corner)
  const wsBottom = 0.633 * H;           // window.front.bottom
  const wsTop = 0.927 * H;              // read off: glass top corners 2.43 m (window.front.top 0.904 is the frame's inner edge)
  const wallTop = 0.616 * H;            // bedWall.top
  const floorTop = 0.416 * H;           // read off: far bed wall inner face drops ~0.22 H to the floor (0.393 H), raised to clear the arch liner

  // ------------------------------------------------------------------ lengths (from the nose)
  const cabFront = fromNose(0.327);     // cab.start
  const cabRear = fromNose(0.585);      // cab.end
  const bedFront = fromNose(0.594);     // bed.start (the cab/bed slot is real: 0.009 L)
  const bedRear = fromNose(1);          // bed.end
  const roofFront = fromNose(0.355);    // read off: roof front corners (both sides) at 0.355 L
  const rake = (cabFront - roofFront) / (roofY - wsBottom);          // dz per dy of the A-pillar
  const cabRearTop = fromNose(0.573);   // read off: roof rear corners 0.570..0.574 L (the cab back leans forward)

  // ------------------------------------------------------------------ wheels, axles, chassis
  const R = 0.206 * L / 2;              // wheel.diameterOverL 0.198 is the tyre-face fit; the tread silhouette reads 0.206
  const axles = [["f", fromNose(0.197)], ["r", fromNose(0.82)]];   // wheel.centreFromFront (wheelbase 0.623 L agrees)
  const tyreW = 0.34, sw = 0.06, tT = 0.06, chamf = 0.035;
  const dishR = 0.66 * R, dishD = 0.085, hubR = 0.62 * R, capR = 0.3 * R;
  const segsNear = 24, segsFar = 8;     // the -X pair is hidden at the solved camera (same AABB: segs divisible by 4)
  const tyreP = [[0, dishD], [dishR, dishD], [dishR, 0], [R - chamf, 0], [R, chamf], [R, sw], [R - tT + s, sw], [R - tT + s, tyreW], [0, tyreW]];
  const treadP = [[R - tT, sw - s], [R, sw - s], [R, tyreW], [R - tT, tyreW]];
  // hub: recessed disc (target: pale disc with the dish wall showing lower-right) and a raised centre cap
  const hubP = [[0, 0], [capR, 0], [capR, 0.03], [hubR, 0.03], [hubR, 0.09], [0, 0.09]];
  const wheelParts = (segs) => ({
    tyre: K.revolve(ccw(tyreP), segs).rotZ(90),
    tread: K.revolve(ccw(treadP), segs).rotZ(90),
    hub: K.revolve(ccw(hubP), segs).rotZ(90),
  });
  const near = wheelParts(segsNear), far = wheelParts(segsFar);
  const inner = W / 2 - tyreW;          // wheel inner face
  for (const [a, z] of axles) {
    for (const [sd, set, place] of [["l", near, (x) => x], ["r", far, (x) => x.mirrorX()]]) {
      add(`wheel_${a}${sd}`, place(set.tyre.at([W / 2, R, z])), "tyre", "wheel");
      add(`tread_${a}${sd}`, place(set.tread.at([W / 2, R, z])), "tread", "tyre");
      add(`hub_${a}${sd}`, place(set.hub.at([W / 2 - dishD - s + 0.09, R, z])), "hub", "hub");
    }
    add(`axle_${a}`, slab(-inner - s, inner + s, 0.371, 0.451, z - 0.04, z + 0.04), "tyre", "axle");
  }
  // narrow frame rail: inboard far enough that the flank's bottom edge hides it at the solved camera
  const chassisTop = bodyBot + s;
  add("chassis", slab(-0.35, 0.35, 0.45, chassisTop, fromNose(1) + 0.1, axles[0][1] + 0.15), "tyre", "chassis");

  // ------------------------------------------------------------------ wheel arches (read off: semicircle r 0.52 m
  // about the wheel's z at the body's bottom edge — top 1.13-1.15 m, rear leg near-vertical down to the sill)
  // read off: the arches are rounded trapezoids, not semicircles — 1.16 m wide on the sill, 0.88 m across a flat top
  // at 1.15 m, the sides leaning in; top corners rounded r 0.2
  const archR = 0.58, archT = 0.44, archTop = 1.15, archRound = 0.2, linerT = 0.065;
  const archPts = (zc, g, y0 = bodyBot) => {
    const B1 = [zc + archR + g, y0], T1 = [zc + archT + g, archTop + g], T0 = [zc - archT - g, archTop + g], B0 = [zc - archR - g, y0];
    const toward = (a, b, d) => { const l = Math.hypot(b[0] - a[0], b[1] - a[1]); return [a[0] + (b[0] - a[0]) * d / l, a[1] + (b[1] - a[1]) * d / l]; };
    const corner = (prev, c, next) => {
      const p0 = toward(c, prev, archRound), p2 = toward(c, next, archRound);
      return Array.from({ length: 5 }, (_, i) => { const t = i / 4, u = 1 - t; return [u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1]]; });
    };
    return [B1, ...corner(B1, T1, T0), ...corner(T1, T0, B0), B0];
  };
  const archTool = (zc, x0) => side([[zc + archR, bodyBot - 0.3], ...archPts(zc, 0), [zc - archR, bodyBot - 0.3]], x0, W / 2 + 0.2);
  const archShell = (zc, x0, x1) => K.cut(side([[zc + archR + s, bodyBot], ...archPts(zc, s).slice(1, -1), [zc - archR - s, bodyBot]], x0, x1),
    side(archPts(zc, -linerT, bodyBot - 0.3), x0 - 0.1, x1 + 0.1));

  // ------------------------------------------------------------------ front: nose + fenders + sloped hood panel (role hood)
  const zcF = axles[0][1];
  // read off: the fender tops rise from hood.top at the nose to the cowl (1.64 m, just under the windshield); the hood
  // panel stands 0.08 m proud of them at the nose (the step at each grille-width notch, and the wedge of its +x side
  // face) and runs almost level back to the cowl, where it is flush with the fenders.
  const cowlY = wsBottom - 0.02;
  let nose = side([[cabFront - s, bodyBot], [zcF + archR, bodyBot], [zcF + archR, bumperBot], [zF, bumperBot], [zF, hoodTop], [cabFront - s, cowlY]], -W / 2, W / 2);
  // hood panel: a trapezoid from the grille-width notches (read off 0.27 W half-width) to the windshield width at the cowl
  const hw0 = 0.27 * W, hw1 = 0.433 * W;
  const hw = (z) => hw0 + (hw1 - hw0) * (zF - z) / (zF - cabFront);
  const trap = (z0, z1) => [[-hw(z1), z1], [hw(z1), z1], [hw(z0), z0], [-hw(z0), z0]];
  const panelFront = hoodTop + 0.08, panelRear = cowlY + 0.01;
  const panel = K.intersect(plan(trap(cabFront - s, zF), hoodTop - 0.2, H), side([[cabFront - s, 0], [zF, 0], [zF, panelFront], [cabFront - s, panelRear]]));
  nose = K.union(nose, panel);
  // grille: one recess for the slot field (grille.w x grille.h, centred on the lamp line; read off 0.434..0.548 H)
  const gw = 0.453 * W / 2, gy0 = 0.434 * H, gy1 = gy0 + 0.114 * H;
  const pocketD = 0.07;                // the slot field is a real recess: its lit inner walls read as the frame
  nose = K.cut(nose, K.union(
    slab(-gw, gw, gy0, gy1, zF - pocketD, zF + 0.1),
    archTool(zcF, W / 2 - tyreW - 0.09),
    archTool(zcF, W / 2 - tyreW - 0.09).mirrorX(),
  ));
  const hood = add("hood", nose, "body", "hood");
  // arch liners: dark wheel-well shell + inner plate (the target shows the well's inside, darker than the body)
  const linerF = K.union(archShell(zcF, W / 2 - tyreW - 0.09, W / 2 - 0.02),
    side([[zcF + archR + s, bodyBot], ...archPts(zcF, s).slice(1, -1), [zcF - archR - s, bodyBot]], W / 2 - tyreW - 0.09, W / 2 - tyreW - 0.03));
  add("arch_liner_fl", linerF, "bed", "body");
  add("arch_liner_fr", linerF.mirrorX(), "bed", "body");

  // ------------------------------------------------------------------ grille (hand-built: dark slot field, lit slat)
  // the recess floor is the dark slot tone 0.05 m deep; one body-tone bar crosses it at mid height, 0.012 m under the
  // nose face (grille.slots 2)
  const slatY0 = (gy0 + gy1) / 2 - 0.03, slatY1 = slatY0 + 0.06;
  // dark panel seated at the back of the recess, the two slots grooved 0.02 m into it through its ends
  const grillePanel = K.cut(slab(-gw, gw, gy0, gy1, zF - pocketD - 0.03, zF - 0.03), K.union(
    slab(-gw - 0.05, gw + 0.05, slatY1, gy1 + 0.05, zF - 0.05, zF + 0.01),
    slab(-gw - 0.05, gw + 0.05, gy0 - 0.05, slatY0, zF - 0.05, zF + 0.01),
  ));
  add("grille", grillePanel, "grille", "grille", { touches: ["hood"], embed: true });
  add("grille_slat", slab(-gw, gw, slatY0, slatY1, zF - 0.052, zF - 0.012), "body", "grille", { touches: ["grille", "hood"], embed: true });

  // ------------------------------------------------------------------ cab: raked side profile x tumblehome section
  const belt = 1.85;                    // taper starts above the mirror arm
  const taper = 0.079;                  // read off: far roof corner 0.901 W off the flank (layout height.overL evidence), halved toward the windshield's own 0.81 W top
  const tx = (y) => W / 2 - taper * (y - belt) / (roofY - belt);
  const section = front([[-W / 2, bodyBot - 0.2], [W / 2, bodyBot - 0.2], [W / 2, belt], [tx(roofY + 0.2), roofY + 0.2], [-tx(roofY + 0.2), roofY + 0.2], [-W / 2, belt]], cabRear - 0.2, cabFront + 0.2);
  const cabBase = K.intersect(side([[cabRear, bodyBot], [cabFront, bodyBot], [cabFront, wsBottom], [roofFront, roofY], [cabRearTop, roofY]]), section);
  const cab = add("cab", cabBase, "body", "cab");

  // glass: a 60 mm pane 8..68 mm under its face, in a 20 mm recess cut from the same face (follows the rake and the
  // tumblehome); seated deep, so declared as a seat.
  const recess = 0.02, g0 = 0.008, gT = 0.06;
  const glass = (axis, sign, prism, toolPrism = prism) => ({
    tool: K.intersect(skin(cabBase, axis, sign, -0.01, recess), toolPrism),   // starts 10 mm outside the face: no coplanar skin left behind
    pane: K.intersect(skin(cabBase, axis, sign, g0, g0 + gT), prism),
  });
  const wsHalfBot = 0.425 * W;          // window.front.w 0.866 W, trimmed 0.008 W so the pane box stays clear of the tumbled-in side glass (V12 groups windows by AABB)
  const wsHalfTop = 0.405 * W;          // read off: windshield upper edge 290.4 px units (0.81 W), layout evidence
  const wsPrism = (y0) => front([[-wsHalfBot, y0], [wsHalfBot, y0], [wsHalfTop, wsTop], [-wsHalfTop, wsTop]], cabRear - 0.5, cabFront + 0.5);
  // the recess runs 10 mm down the cowl face so it meets the cab's front plane (no sliver at the kink)
  const ws = glass(2, 1, wsPrism(wsBottom + 0.003), wsPrism(wsBottom - 0.01));
  const swz0 = fromNose(0.358), swz1 = fromNose(0.516), swy0 = 0.667 * H, swy1 = 0.93 * H;   // window.side.*
  const sidePrism = side([[swz0, swy0], [swz1, swy0], [swz1, swy1], [swz0 - rake * (swy1 - swy0), swy1]], 0, W);
  const sg = glass(0, 1, sidePrism);
  // door outline: 20 mm groove, 20 mm deep, front edge following the A-pillar rake above the belt (read off:
  // door front at cab.start + 0.07, rear 0.563 L, bottom 0.28 H, top under the roof rail)
  const dz0 = cabFront - 0.07, dz1 = fromNose(0.563), dy0 = 0.28 * H, dy1 = roofY - 0.12;
  const door = [[dz0, dy0], [dz1, dy0], [dz1, dy1], [dz0 - rake * (dy1 - swy0), dy1], [dz0, swy0]];
  const doorRing = K.extrude(K.profile.poly(ccw(door.map(([z, y]) => [-z, y]))), W, { holes: [K.profile.offset(ccw(door.map(([z, y]) => [-z, y])), -0.02)] }).rotY(90).at([0, 0, 0]);
  const doorTool = K.intersect(skin(cabBase, 0, 1, -0.01, 0.02), doorRing);
  cab.solid = K.cut(cabBase, K.union(ws.tool, sg.tool, sg.tool.mirrorX(), doorTool, doorTool.mirrorX()));
  add("windshield", ws.pane, "glass", "window", { touches: ["cab"], embed: true });
  add("window_l", sg.pane, "glass", "window", { touches: ["cab"], embed: true });
  add("window_r", sg.pane.mirrorX(), "glass", "window", { touches: ["cab"], embed: true });
  // door handles (read off: centre 0.532 L, 0.556 H; darker than the body), half sunk into the door skin
  const handle = slab(W / 2 - 0.03, W / 2 + 0.03, 0.556 * H - 0.035, 0.556 * H + 0.035, fromNose(0.532) - 0.12, fromNose(0.532) + 0.12);
  add("handle_l", handle, "bed", "cab", { touches: ["cab"], embed: true });
  add("handle_r", handle.mirrorX(), "bed", "cab", { touches: ["cab"], embed: true });

  // ------------------------------------------------------------------ open bed: L-section walls (body skin + rim),
  // dark inner liners, bulkhead, tailgate, T-section floor clear of the tyres
  const wT = 0.12, skinT = 0.06, rimH = 0.06;
  const zcR = axles[1][1];
  const bedArch = archTool(zcR, W / 2 - wT - 0.0005);
  const wallBody = K.cut(K.union(slab(W / 2 - skinT, W / 2, bodyBot, wallTop, bedRear, bedFront),
    slab(W / 2 - wT, W / 2, wallTop - rimH, wallTop, bedRear, bedFront)), bedArch);
  const wallLiner = K.cut(slab(W / 2 - wT, W / 2 - skinT + s, bodyBot, wallTop - rimH + s, bedRear, bedFront), bedArch);
  add("bed_side_l", wallBody, "body", "bed_wall");
  add("bed_side_r", wallBody.mirrorX(), "body", "bed_wall");
  add("bed_liner_l", wallLiner, "bed", "bed_wall");
  add("bed_liner_r", wallLiner.mirrorX(), "bed", "bed_wall");
  const linerR = archShell(zcR, W / 2 - wT, W / 2 - 0.02);
  add("arch_liner_rl", linerR, "bed", "body");
  add("arch_liner_rr", linerR.mirrorX(), "bed", "body");
  const xi = W / 2 - wT;                // inner face of the walls
  add("bed_floor", K.union(slab(-xi + 0.001, xi - 0.001, floorTop - 0.07, floorTop, bedRear, bedFront),
    slab(-(inner - 0.03), inner - 0.03, bodyBot, floorTop - 0.07 + s, bedRear, bedFront)), "bed", "bed");
  const endWall = (z0, dir, id, role) => {       // dir +1: body skin on the +z side (bulkhead); -1: on the -z side (tailgate)
    const zs = dir > 0 ? [z0 - skinT, z0] : [z0, z0 + skinT];
    const zr = dir > 0 ? [z0 - wT, z0] : [z0, z0 + wT];
    const zl = dir > 0 ? [z0 - wT, z0 - skinT + s] : [z0 + skinT - s, z0 + wT];
    add(id, K.union(slab(-xi - s, xi + s, floorTop - s, wallTop, zs[0], zs[1]), slab(-xi - s, xi + s, wallTop - rimH, wallTop, zr[0], zr[1])), "body", role);
    add(`${id}_liner`, slab(-xi - s, xi + s, floorTop - s, wallTop - rimH + s, zl[0], zl[1]), "bed", role);
  };
  endWall(bedFront, 1, "bed_bulkhead", "bed_wall");
  endWall(bedRear, -1, "tailgate", "tailgate");

  // ------------------------------------------------------------------ bumpers, wrapped round the corners
  const bumper = (zFace, dir, depth, wrap, out, y0, y1, id) => {
    const zo = zFace + dir * depth, zw = zFace - dir * wrap, c = 0.05, xo = W / 2 + out, xi2 = W / 2 - s;
    const outline = [[-xo, zw], [-xo, zo - dir * c], [-xo + c, zo], [xo - c, zo], [xo, zo - dir * c], [xo, zw], [xi2, zw], [xi2, zFace - dir * s], [-xi2, zFace - dir * s], [-xi2, zw]];
    const ch = 0.03;
    const prof = side([[zw - dir * 0.2, y0], [zo - dir * ch, y0], [zo, y0 + ch], [zo, y1 - ch], [zo - dir * ch, y1], [zw - dir * 0.2, y1]]);
    add(id, K.intersect(plan(outline, y0, y1), prof), "bumper", "bumper");
  };
  bumper(zF, 1, 0.16, 0.28, 0.06, bumperBot, bumperTop, "bumper_front");        // wrap read off: returns end 0.28 m back
  // read off (bumper.rear.top is unverified): a block 0.60..0.865 m (stretched to 0.55..0.89 for bumper.rear.h), 0.09 m proud of the flanks, 0.08 m behind the
  // tailgate, wrapping 0.15 m forward
  bumper(bedRear, -1, 0.10, 0.24, 0.12, 0.57, 0.905, "bumper_rear");   // 0.34 m: bumper.rear.h floor

  // ------------------------------------------------------------------ details through K.assemble
  // headlights (hand-built: the target's lenses are flush discs with no visible rim) — headlight.offsetX / centreY /
  // diameter; each lens sits in a 0.03 m pocket and stands 0.01 m proud of the nose
  const lampR = 0.143 * W / 2, lampX = 0.38 * W, lampY = 0.483 * H, lampT = 0.045;
  const lens = K.revolve([[0, 0], [lampR, 0], [lampR, lampT], [0, lampT]], 20).rotX(90);
  hood.solid = K.cut(hood.solid, K.union(lens.at([lampX, lampY, zF - 0.03]), lens.at([-lampX, lampY, zF - 0.03])));
  add("lamp_l", lens.at([lampX, lampY, zF - 0.035]), "lamp", "headlight", { touches: ["hood"], embed: true });
  add("lamp_r", lens.at([-lampX, lampY, zF - 0.035]), "lamp", "headlight", { touches: ["hood"], embed: true });
  // mirrors (hand-built: the target's heads are rounded rectangles on a raked stalk). Read off: head centre x 0.612 W
  // (mirror.offsetX), 1.80 m high (mirror.centreY 0.688 H), mirror.head.w x mirror.head.h, at 0.318 L; the stalk
  // leaves the fender flank at 1.52 m just ahead of the cowl and climbs outward into the head's lower half.
  const mw = 0.126 * W, mh = 0.152 * H, mcx = 0.612 * W, mcy = 0.688 * H, mz = fromNose(0.318), mT = 0.06, mr = 0.07;
  const rrect = (w, h, r) => {
    const pts = [];
    for (const [cx, cy, a0] of [[w / 2 - r, h / 2 - r, 0], [-w / 2 + r, h / 2 - r, 90], [-w / 2 + r, -h / 2 + r, 180], [w / 2 - r, -h / 2 + r, 270]]) {
      for (let i = 0; i <= 3; i += 1) { const a = (a0 + 30 * i) * Math.PI / 180; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
    }
    return pts;
  };
  const mHead = K.extrude(K.profile.poly(ccw(rrect(mw, mh, mr))), mT).at([mcx, mcy, mz - mT / 2]);
  const rod = (p0, p1, t) => {
    const dx = p1[0] - p0[0], dy = p1[1] - p0[1], l = Math.hypot(dx, dy), nx = -dy / l * t / 2, ny = dx / l * t / 2;
    return [[p0[0] + nx, p0[1] + ny], [p0[0] - nx, p0[1] - ny], [p1[0] - nx, p1[1] - ny], [p1[0] + nx, p1[1] + ny]];
  };
  // the stalk runs in FRONT of the head (target: it crosses the head's lower half), seated 0.01 m into its face
  const mArm = K.extrude(K.profile.poly(ccw(rod([W / 2 - 0.04, 1.50], [mcx - 0.02, mcy - 0.06], 0.06))), 0.05).at([0, 0, mz + mT / 2 - 0.01]);
  add("mirror_head_l", mHead, "mirror", "mirror", { touches: ["mirror_arm_l"], embed: true });
  add("mirror_arm_l", mArm, "mirror", "mirror", { touches: ["hood"], embed: true });
  add("mirror_head_r", mHead.mirrorX(), "mirror", "mirror", { touches: ["mirror_arm_r"], embed: true });
  add("mirror_arm_r", mArm.mirrorX(), "mirror", "mirror", { touches: ["hood"], embed: true });
  void hood;
  return parts;
}
