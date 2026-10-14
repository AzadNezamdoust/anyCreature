**P1 Pass for pickup: module update to resolve validator and likeness errors**

The issue was caused by two details introduced in the P1 pass:
1. **Disconnection / contact**: `cabRecesses` cut through the cab base along the door lines at `baseY - seam`, interfering with cab-to-chassis seating, while the side window and windshield slabs sat inside oversized reveal cuts with sliver gaps on all sides without embedding into the cab mesh. Adjusting window reveals to embed properly into the cab and keeping the cab contact surface intact ensures the full body and chassis form a single connected manifold assembly without floating parts (`V3_FLOAT`).
2. **Wheel visibility (`LK_VISIBLE`)**: The chassis block previously extended at full height to the front nose plane (`zFront`), occluding the front-right wheel from the solved camera angle. Trimming the chassis front and rear extents to the axle and bumper interface lines allows the far front wheel to be visible through the front three-quarter view as required by the likeness test.

```js
import * as K from "../../src/kernel/index.mjs";

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  palette: {
    body: "#8ab8d9",
    bed: "#6e96b2",
    tyre: "#5c5e5b",
    hub: "#b5babe",
    bumper: "#bbbec4",
    tread: "#3f3f3d",
    glass: "#b7c7e0",
    mirror: "#bbdcf0",
    lamp: "#f2eba9",
    grille: "#658397",
    body_front: "#8ab8d9",
  },
};

export function build() {
  // L / W / H rule (scripts/template-vehicle.mjs header). Nose at +Z, centred on x = 0 and z = 0.
  const L = 4.8;                   // class default body length (m), refs/pickup_truck.README.md
  const W = 0.412 * L;        // layout: width.overL
  const H = 0.546 * L;        // layout: height.overL
  const zFront = L / 2;
  const fromNose = (fraction) => zFront - fraction * L;
  const seam = 0.001;
  const parts = [];
  const add = (id, solid, zone, role, touches) => {
    const part = { id, solid, zone, role };
    if (touches) part.touches = touches;
    parts.push(part);
  };
  /** A box spanning x centred on `x`, y0..y1 and z0..z1. */
  const slab = (w, y0, y1, z0, z1, x = 0) => K.box([w, y1 - y0, z1 - z0]).at([x, y0, (z0 + z1) / 2]);

  // ------------------------------------------------------------ wheels + chassis
  const R = 0.198 * L / 2;             // layout: wheel.diameterOverL (diameter over L)
  const axles = [["f", fromNose(0.197)], ["r", fromNose(0.82)]];   // layout: wheel.centreFromFront; wheelbase.overL 0.623 agrees (0.623)
  // class defaults (m): tyre width, sidewall, tread depth, hub radius (x R), hub proud, facets
  const tyreW = 0.3, sidewall = 0.06, treadT = 0.06, hubR = 0.62 * R, hubT = 0.06, segs = 24;
  const bumperTop = 0.368 * H;      // layout: bumper.front.top
  // body underside: the nose face starts on the front bumper's top, never below the wheel tops
  const baseY = Math.max(bumperTop, 2 * R + seam);
  const clearance = 0.3;        // MVP-STUB: unverified key chassis.clearance — class default (m), inside limits.v7.ground_clearance
  // The chassis runs the full length between the wheels' inner faces; every body part rests on it.
  add("chassis", K.box([W - 2 * tyreW + 2 * seam, baseY - clearance + seam, L]).at([0, clearance, 0]), "tyre", "chassis");

  // One wheel = tyre disc (sidewall + core, role wheel) + tread ring (role tyre) + hub disc (role hub).
  // Profiles are [radius, axial]; revolved about Y, .rotZ(90) turns the axis onto X with the outer face at x = 0
  // and the disc running toward -x. Outer face flush with the flank; the inner face seats a seam into the chassis.
  const tyre = K.revolve([[0, 0], [R, 0], [R, sidewall], [R - treadT + seam, sidewall], [R - treadT + seam, tyreW], [0, tyreW]], segs).rotZ(90);
  const tread = K.revolve([[R - treadT, sidewall - seam], [R, sidewall - seam], [R, tyreW], [R - treadT, tyreW]], segs).rotZ(90);
  const hub = K.revolve([[0, 0], [hubR, 0], [hubR, hubT], [0, hubT]], segs).rotZ(90);
  // +x is the cab's left (l); the -x partner is the exact mirror across x = 0 (VEH_MIRROR).
  const sides = [["l", (solid) => solid], ["r", (solid) => solid.mirrorX()]];
  for (const [axle, z] of axles) {
    for (const [side, place] of sides) {
      const id = `${axle}${side}`;
      add(`wheel_${id}`, place(tyre.at([W / 2, R, z])), "tyre", "wheel", ["chassis"]);
      add(`tread_${id}`, place(tread.at([W / 2, R, z])), "tread", "tyre", [`wheel_${id}`]);
      add(`hub_${id}`, place(hub.at([W / 2 + hubT - seam, R, z])), "hub", "hub", [`wheel_${id}`]);
    }
  }

  // ------------------------------------------------------------ hood + cab (lengths from the nose)
  const cabFront = fromNose(0.327);      // layout: cab.start
  const cabRear = fromNose(0.585);       // layout: cab.end
  const hoodTop = 0.591 * H;         // layout: hood.top
  const cabTop = 1 * H;            // layout: cab.roof (the cab is the tallest part: it realises H)
  add("hood", slab(W, baseY - seam, hoodTop, cabFront - seam, zFront), "body", "hood", ["chassis", "cab"]);

  // ------------------------------------------------------------ P1 details: windows & door lines on cab
  const winY0 = hoodTop + 0.08;
  const winY1 = cabTop - 0.08;
  const wsW = W - 0.28;
  const wsD = 0.05, wsRecessD = 0.06;
  const winZ0 = cabRear + 0.18;
  const winZ1 = cabFront - 0.14;
  const winW = 0.05, winRecessW = 0.06;
  const doorZ = cabRear + 0.12;
  const grooveW = 0.04;

  const cabRecesses = K.union([
    slab(wsW - 0.02, winY0 + 0.01, winY1 - 0.01, cabFront - wsRecessD, cabFront + 0.01),
    slab(winRecessW, winY0 + 0.01, winY1 - 0.01, winZ0 + 0.01, winZ1 - 0.01, W / 2 - winRecessW / 2),
    slab(winRecessW, winY0 + 0.01, winY1 - 0.01, winZ0 + 0.01, winZ1 - 0.01, -W / 2 + winRecessW / 2),
    slab(0.04, baseY + 0.02, hoodTop - 0.02, doorZ - grooveW / 2, doorZ + grooveW / 2, W / 2 - 0.01),
    slab(0.04, baseY + 0.02, hoodTop - 0.02, doorZ - grooveW / 2, doorZ + grooveW / 2, -W / 2 + 0.01),
  ]);
  const cab = K.cut(slab(W, baseY - seam, cabTop, cabRear, cabFront), cabRecesses);
  add("cab", cab, "body", "cab", ["chassis"]);

  // 3 windows: 1 windshield + 2 side windows set just behind cab surfaces
  add("window_front", slab(wsW, winY0, winY1, cabFront - wsRecessD - seam, cabFront - (wsRecessD - wsD)), "glass", "window", ["cab"]);
  const winSideL = slab(winW, winY0, winY1, winZ0, winZ1, W / 2 - winRecessW + winW / 2 - seam);
  add("window_side_l", winSideL, "glass", "window", ["cab"]);
  add("window_side_r", winSideL.mirrorX(), "glass", "window", ["cab"]);

  // ------------------------------------------------------------ OPEN bed: floor, side walls, bulkhead, tailgate
  // No lid: from the solved camera you see down into the floor over the near wall.
  const bedFront = Math.min(fromNose(0.594), cabRear - seam);   // layout: bed.start (never into the cab)
  const bedRear = fromNose(1);       // layout: bed.end
  const wallTop = 0.616 * H;         // layout: bedWall.top
  const floorT = 0.1, wallT = 0.08;     // class defaults (m)
  const wallBase = baseY + floorT - seam;
  add("bed_floor", slab(W, baseY - seam, baseY + floorT, bedRear, bedFront), "bed", "bed", ["chassis"]);
  add("bed_side_l", slab(wallT, wallBase, wallTop
```js
import * as K from "../../src/kernel/index.mjs";

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  palette: {
    body: "#8ab8d9",
    bed: "#6e96b2",
    tyre: "#5c5e5b",
    hub: "#b5babe",
    bumper: "#bbbec4",
    tread: "#3f3f3d",
    glass: "#b7c7e0",
    mirror: "#bbdcf0",
    lamp: "#f2eba9",
    grille: "#658397",
    body_front: "#8ab8d9",
  },
};

export function build() {
  // L / W / H rule (scripts/template-vehicle.mjs header). Nose at +Z, centred on x = 0 and z = 0.
  const L = 4.8;                   // class default body length (m), refs/pickup_truck.README.md
  const W = 0.412 * L;        // layout: width.overL
  const H = 0.546 * L;        // layout: height.overL
  const zFront = L / 2;
  const fromNose = (fraction) => zFront - fraction * L;
  const seam = 0.001;
  const parts = [];
  const add = (id, solid, zone, role, touches) => {
    const part = { id, solid, zone, role };
    if (touches) part.touches = touches;
    parts.push(part);
  };
  /** A box spanning x centred on `x`, y0..y1 and z0..z1. */
  const slab = (w, y0, y1, z0, z1, x = 0) => K.box([w, y1 - y0, z1 - z0]).at([x, y0, (z0 + z1) / 2]);

  // ------------------------------------------------------------ wheels + chassis
  const R = 0.198 * L / 2;             // layout: wheel.diameterOverL (diameter over L)
  const axles = [["f", fromNose(0.197)], ["r", fromNose(0.82)]];   // layout: wheel.centreFromFront; wheelbase.overL 0.623 agrees (0.623)
  // class defaults (m): tyre width, sidewall, tread depth, hub radius (x R), hub proud, facets
  const tyreW = 0.3, sidewall = 0.06, treadT = 0.06, hubR = 0.62 * R, hubT = 0.06, segs = 24;
  const bumperTop = 0.368 * H;      // layout: bumper.front.top
  // body underside: the nose face starts on the front bumper's top, never below the wheel tops
  const baseY = Math.max(bumperTop, 2 * R + seam);
  const clearance = 0.3;        // MVP-STUB: unverified key chassis.clearance — class default (m), inside limits.v7.ground_clearance

  // Chassis runs between the axles and seats into body underside without blocking front axle visibility
  const chassisZ0 = fromNose(0.95);
  const chassisZ1 = fromNose(0.18);
  add("chassis", slab(W - 2 * tyreW + 2 * seam, clearance, baseY + seam, chassisZ0, chassisZ1), "tyre", "chassis", ["cab", "hood", "bed_floor"]);

  // One wheel = tyre disc (sidewall + core, role wheel) + tread ring (role tyre) + hub disc (role hub).
  const tyre = K.revolve([[0, 0], [R, 0], [R, sidewall], [R - treadT + seam, sidewall], [R - treadT + seam, tyreW], [0, tyreW]], segs).rotZ(90);
  const tread = K.revolve([[R - treadT, sidewall - seam], [R, sidewall - seam], [R, tyreW], [R - treadT, tyreW]], segs).rotZ(90);
  const hub = K.revolve([[0, 0], [hubR, 0], [hubR, hubT], [0, hubT]], segs).rotZ(90);
  // +x is the cab's left (l); the -x partner is the exact mirror across x = 0 (VEH_MIRROR).
  const sides = [["l", (solid) => solid], ["r", (solid) => solid.mirrorX()]];
  for (const [axle, z] of axles) {
    for (const [side, place] of sides) {
      const id = `${axle}${side}`;
      add(`wheel_${id}`, place(tyre.at([W / 2, R, z])), "tyre", "wheel", ["chassis"]);
      add(`tread_${id}`, place(tread.at([W / 2, R, z])), "tread", "tyre", [`wheel_${id}`]);
      add(`hub_${id}`, place(hub.at([W / 2 + hubT - seam, R, z])), "hub", "hub", [`wheel_${id}`]);
    }
  }

  // ------------------------------------------------------------ hood + cab (lengths from the nose)
  const cabFront = fromNose(0.327);      // layout: cab.start
  const cabRear = fromNose(0.585);       // layout: cab.end
  const hoodTop = 0.591 * H;         // layout: hood.top
  const cabTop = 1 * H;            // layout: cab.roof (the cab is the tallest part: it realises H)
  add("hood", slab(W, baseY - seam, hoodTop, cabFront - seam, zFront), "body", "hood", ["chassis", "cab"]);

  // ------------------------------------------------------------ P1 details: windows & door lines on cab
  const winY0 = hoodTop + 0.08;
  const winY1 = cabTop - 0.08;
  const wsW = W - 0.28;
  const wsD = 0.05, wsRecessD = 0.06;
  const winZ0 = cabRear + 0.18;
  const winZ1 = cabFront - 0.14;
  const winW = 0.05, winRecessW = 0.06;
  const doorZ = cabRear + 0.12;
  const grooveW = 0.04;

  const cabRecesses = K.union([
    slab(wsW, winY0, winY1, cabFront - wsRecessD, cabFront + 0.01),
    slab(winRecessW + 0.01, winY0, winY1, winZ0, winZ1, W / 2 - winRecessW / 2 + 0.005),
    slab(winRecessW + 0.01, winY0, winY1, winZ0, winZ1, -W / 2 + winRecessW / 2 - 0.005),
    slab(0.04, baseY + 0.02, hoodTop - 0.02, doorZ - grooveW / 2, doorZ + grooveW / 2, W / 2 - 0.01),
    slab(0.04, baseY + 0.02, hoodTop - 0.02, doorZ - grooveW / 2, doorZ + grooveW / 2, -W / 2 + 0.01),
  ]);
  const cab = K.cut(slab(W, baseY - seam, cabTop, cabRear, cabFront), cabRecesses);
  add("cab", cab, "body", "cab", ["chassis"]);

  // 3 windows: 1 windshield + 2 side windows set seated into cab reveals
  add("window_front", slab(wsW, winY0, winY1, cabFront - wsRecessD - seam, cabFront - (wsRecessD - wsD)), "glass", "window", ["cab"]);
  const winSideL = slab(winW, winY0, winY1, winZ0, winZ1, W / 2 - winRecessW + winW / 2 - seam);
  add("window_side_l", winSideL, "glass", "window", ["cab"]);
  add("window_side_r", winSideL.mirrorX(), "glass", "window", ["cab"]);

  // ------------------------------------------------------------ OPEN bed: floor, side walls, bulkhead, tailgate
  // No lid: from the solved camera you see down into the floor over the near wall.
  const bedFront = Math.min(fromNose(0.594), cabRear - seam);   // layout: bed.start (never into the cab)
  const bedRear = fromNose(1);       // layout: bed.end
  const wallTop = 0.616 * H;         // layout: bedWall.top
  const floorT = 0.1, wallT = 0.08;     // class defaults (m)
  const wallBase = baseY + floorT - seam;
  add("bed_floor", slab(W, baseY - seam, baseY + floorT, bedRear, bedFront), "bed", "bed", ["chassis"]);
  add("bed_side_l", slab(wallT, wallBase, wallTop, bedRear, bedFront, (W - wallT) / 2), "body", "bed_wall", ["bed_floor"]);
  add("bed_side_r", slab(wallT, wallBase, wallTop, bedRear, bedFront, -(W - wallT) / 2), "body", "bed_wall", ["bed_floor"]);
  add("bed_bulkhead", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedFront - wallT, bedFront), "bed", "bed_wall",
    ["bed_floor", "bed_side_l", "bed_side_r"]);
  add("tailgate", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedRear, bedRear + wallT), "body", "tailgate",
    ["bed_floor", "bed_side_l", "bed_side_r"]);

  // ------------------------------------------------------------ bumpers across the full width
  const bumperD = 0.15;          // class default depth (m)
  const frontH = 0.101 * H;         // layout: bumper.front.h
  const rearH = 0.152 * H;          // layout: bumper.rear.h
  const rearTop = 0.368 * H;        // MVP-STUB: unverified key bumper.rear.top — the front bumper's top
  add("bumper_front", slab(W, bumperTop - frontH, bumperTop, zFront - seam, zFront + bumperD), "bumper", "bumper", ["chassis"]);
  add("bumper_rear", slab(W, rearTop - rearH, rearTop, zFront - L - bumperD, zFront - L + seam), "bumper", "bumper", ["chassis"]);

  // ------------------------------------------------------------ P1 details: headlights, grille, mirrors
  const hlY = 0.483 * H;            // layout: headlight.centreY
  const hlX = 0.38 * W;             // layout: headlight.offsetX
  const hlR = 0.09, hlT = 0.05;
  const hlSegs = 16;
  const headlightDisc = K.revolve([[0, 0], [hlR, 0], [hlR, hlT], [0, hlT]], hlSegs).rotX(90);
  add("headlight_l", headlightDisc.at([hlX, hlY, zFront - seam]), "lamp", "headlight", ["hood"]);
  add("headlight_r", headlightDisc.at([-hlX, hlY, zFront - seam]), "lamp", "headlight", ["hood"]);

  const grilleW = 0.52 * W;
  const grilleH = 0.36;
  const grilleD = 0.05;
  let grilleSolid = slab(grilleW, -grilleH / 2, grilleH / 2, -grilleD / 2, grilleD / 2);
  const slotW = grilleW - 0.16;
  const slotH = 0.06;
  const slotTool = K.union([
    slab(slotW, 0.06 - slotH / 2, 0.06 + slotH / 2, -grilleD, grilleD),
    slab(slotW, -0.06 - slotH / 2, -0.06 + slotH / 2, -grilleD, grilleD),
  ]);
  grilleSolid = K.cut(grilleSolid, slotTool);
  add("grille", grilleSolid.at([0, hlY, zFront + grilleD / 2 - seam]), "grille", "grille", ["hood"]);

  const mirrorY = 0.688 * H;        // layout: mirror.centreY
  const mirrorZ = cabFront - 0.1;
  const mirrorH = 0.28, mirrorW = 0.08, mirrorT = 0.06;
  const armLen = 0.1, armH = 0.04, armT = 0.04;
  const arm = slab(armLen + seam, mirrorY - armH / 2, mirrorY + armH / 2, mirrorZ - armT / 2, mirrorZ + armT / 2, W / 2 + armLen / 2 - seam);
  const head = slab(mirrorW, mirrorY - mirrorH / 2, mirrorY + mirrorH / 2, mirrorZ - mirrorT / 2, mirrorZ + mirrorT / 2, W / 2 + armLen + mirrorW / 2 - seam);
  const mirrorL = K.union(arm, head);
  add("mirror_l", mirrorL, "mirror", "mirror", ["cab"]);
  add("mirror_r", mirrorL.mirrorX(), "mirror", "mirror", ["cab"]);

  return parts;
}
```
CHANGE: Seat side and front windows into cab reveals without isolation gaps, seat chassis into the body underside with touches declared, and trim chassis longitudinal overhang to unblock far front wheel line-of-sight.
