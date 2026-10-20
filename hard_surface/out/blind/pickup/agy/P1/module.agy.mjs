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
    headlight: "#808080",
    grille: "#658397",
    mirror: "#bbdcf0",
    lamp: "#f2eba9",
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
  // Contact is measured (kernel API, Contact): no part here is seated deep, so none declares touches.
  const add = (id, solid, zone, role) => {
    parts.push({ id, solid, zone, role });
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
  // The chassis runs between the wheels' inner faces from the tail to the front wheels' leading edge; every body
  // part rests on it. It stops short of the nose whenever the front bumper can seat on the hood instead, so the far
  // front tyre shows under the front bumper at the solved camera, as in the target (classes/vehicle.json visibleInstances).
  const chassisFront = bumperTop >= baseY - seam ? Math.min(zFront, axles[0][1] + R) : zFront;
  const chassisRear = zFront - L;
  add("chassis", K.box([W - 2 * tyreW + 2 * seam, baseY - clearance, chassisFront - chassisRear]).at([0, clearance, (chassisFront + chassisRear) / 2]), "tyre", "chassis");

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
      add(`wheel_${id}`, place(tyre.at([W / 2, R, z])), "tyre", "wheel");
      add(`tread_${id}`, place(tread.at([W / 2, R, z])), "tread", "tyre");
      add(`hub_${id}`, place(hub.at([W / 2 + hubT - seam, R, z])), "hub", "hub");
    }
  }

  // ------------------------------------------------------------ hood + cab (lengths from the nose)
  const cabFront = fromNose(0.327);      // layout: cab.start
  const cabRear = fromNose(0.585);       // layout: cab.end
  const hoodTop = 0.591 * H;         // layout: hood.top
  const cabTop = 1 * H;            // layout: cab.roof (the cab is the tallest part: it realises H)
  let hood = slab(W, baseY - seam, hoodTop, cabFront - seam, zFront);
  let cab = slab(W, baseY - seam, cabTop, cabRear, cabFront);

  // ------------------------------------------------------------ P1 details: windows, recesses, door lines
  const windowRecess = 0.015;
  const paneT = 0.04;
  const seat = 0.0005;

  // Windshield on cab +Z face
  const winFrontW = 0.866 * W;       // layout: window.front.w
  const winFrontY0 = 0.633 * H;      // layout: window.front.bottom
  const winFrontY1 = 0.93 * H;
  const winFrontH = winFrontY1 - winFrontY0;
  const winFrontCut = K.box([winFrontW + 0.004, winFrontH + 0.004, windowRecess + 0.01]).at([0, winFrontY0 - 0.002, cabFront - windowRecess + (windowRecess + 0.01) / 2]);
  const paneFront = K.box([winFrontW, winFrontH, paneT]).at([0, winFrontY0, cabFront - windowRecess - seat + paneT / 2]);
  add("windshield", paneFront, "glass", "window");

  // Side windows on cab flanks (+X and -X)
  const winSideFront = fromNose(0.358); // layout: window.side.start
  const winSideRear = fromNose(0.516);  // layout: window.side.end
  const winSideL = winSideFront - winSideRear;
  const winSideZ = (winSideFront + winSideRear) / 2;
  const winSideY0 = 0.667 * H;          // layout: window.side.bottom
  const winSideY1 = 0.93 * H;           // layout: window.side.top
  const winSideH = winSideY1 - winSideY0;
  const winSideCutL = K.box([windowRecess + 0.01, winSideH + 0.004, winSideL + 0.004]).at([W / 2 - windowRecess + (windowRecess + 0.01) / 2, winSideY0 - 0.002, winSideZ]);
  const winSideCutR = winSideCutL.mirrorX();
  const paneSideL = K.box([paneT, winSideH, winSideL]).at([W / 2 - windowRecess - seat + paneT / 2, winSideY0, winSideZ]);
  const paneSideR = paneSideL.mirrorX();
  add("window_side_l", paneSideL, "glass", "window");
  add("window_side_r", paneSideR, "glass", "window");

  // Door line shallow groove on cab sides (depth <= 0.02 m, above chassis seat)
  const doorD = 0.01;
  const doorCutL = K.box([doorD + 0.01, winSideY1 - (baseY + 0.06), 0.015]).at([W / 2 - doorD + (doorD + 0.01) / 2, baseY + 0.06, fromNose(0.54)]);
  const doorCutR = doorCutL.mirrorX();

  cab = K.cut(cab, K.union([winFrontCut, winSideCutL, winSideCutR, doorCutL, doorCutR]));
  add("cab", cab, "body", "cab");

  // ------------------------------------------------------------ P1 details: grille & headlights on nose face (+Z)
  const grilleW = 0.453 * W;         // layout: grille.w
  const grilleH = 0.114 * H;         // layout: grille.h
  const grilleY0 = 0.483 * H - grilleH / 2;
  const grilleSlotD = 0.015;
  const grilleD = 0.04;
  const grilleCut = K.box([grilleW + 0.004, grilleH + 0.004, grilleSlotD + 0.01]).at([0, grilleY0 - 0.002, zFront - grilleSlotD + (grilleSlotD + 0.01) / 2]);
  hood = K.cut(hood, grilleCut);
  add("hood", hood, "body", "hood");

  const grilleSolid = K.box([grilleW, grilleH, grilleD]).at([0, grilleY0, zFront - grilleSlotD - seat + grilleD / 2]);
  add("grille", grilleSolid, "grille", "grille");

  // Headlights
  const lampR = 0.143 * W / 2;       // layout: headlight.diameter
  const lampT = 0.04;
  const lampSolid = K.revolve([[0, 0], [lampR, 0], [lampR, lampT], [0, lampT]], 16).rotX(90);
  add("headlight_l", lampSolid.at([0.38 * W, 0.483 * H, zFront - seat]), "headlight", "headlight");   // layout: headlight.centreY, headlight.offsetX
  add("headlight_r", lampSolid.at([-0.38 * W, 0.483 * H, zFront - seat]), "headlight", "headlight");

  // ------------------------------------------------------------ P1 details: mirrors (head + arm)
  const mirrorHeadW = 0.126 * W;     // layout: mirror.head.w
  const mirrorHeadH = 0.152 * H;     // layout: mirror.head.h
  const mirrorSection = 0.04;
  const armLen = 0.049 * W;          // layout: mirror.arm.length
  const mirrorZ = fromNose((0.327 + 0.358) / 2); // A-pillar z centre
  const mirrorHeadL = K.box([mirrorHeadW, mirrorHeadH, mirrorSection]).at([0.612 * W, 0.688 * H - mirrorHeadH / 2, mirrorZ]); // layout: mirror.offsetX, mirror.centreY
  const mirrorHeadR = mirrorHeadL.mirrorX();
  const mirrorArmSolidL = K.box([armLen + 2 * seat, mirrorSection, mirrorSection]).at([W / 2 + armLen / 2, 0.688 * H - mirrorSection / 2, mirrorZ]);
  const mirrorArmSolidR = mirrorArmSolidL.mirrorX();
  add("mirror_head_l", mirrorHeadL, "mirror", "mirror");
  add("mirror_head_r", mirrorHeadR, "mirror", "mirror");
  add("mirror_arm_l", mirrorArmSolidL, "mirror", "mirror");
  add("mirror_arm_r", mirrorArmSolidR, "mirror", "mirror");

  // ------------------------------------------------------------ OPEN bed: floor, side walls, bulkhead, tailgate
  // No lid: from the solved camera you see down into the floor over the near wall.
  const bedFront = Math.min(fromNose(0.594), cabRear - seam);   // layout: bed.start (never into the cab)
  const bedRear = fromNose(1);       // layout: bed.end
  const wallTop = 0.616 * H;         // layout: bedWall.top
  const floorT = 0.1, wallT = 0.08;     // class defaults (m)
  const wallBase = baseY + floorT - seam;
  add("bed_floor", slab(W, baseY - seam, baseY + floorT, bedRear, bedFront), "bed", "bed");
  add("bed_side_l", slab(wallT, wallBase, wallTop, bedRear, bedFront, (W - wallT) / 2), "body", "bed_wall");
  add("bed_side_r", slab(wallT, wallBase, wallTop, bedRear, bedFront, -(W - wallT) / 2), "body", "bed_wall");
  add("bed_bulkhead", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedFront - wallT, bedFront), "bed", "bed_wall");
  add("tailgate", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedRear, bedRear + wallT), "body", "tailgate");

  // ------------------------------------------------------------ bumpers across the full width
  const bumperD = 0.06;          // class default depth (m)
  const frontH = 0.101 * H;         // layout: bumper.front.h
  const rearH = 0.152 * H;          // layout: bumper.rear.h
  const rearTop = 0.368 * H;        // MVP-STUB: unverified key bumper.rear.top — the front bumper's top
  add("bumper_front", slab(W, bumperTop - frontH, bumperTop, zFront - seam, zFront + bumperD), "bumper", "bumper");
  add("bumper_rear", slab(W, rearTop - rearH, rearTop, zFront - L - bumperD, zFront - L + seam), "bumper", "bumper");
  return parts;
}
