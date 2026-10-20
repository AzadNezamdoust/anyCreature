import * as K from "../../../src/kernel/index.mjs";

// SMOKE module for the vehicle class (WORKFLOW-V3 §7 item 10): a correct but crude
// box truck on four cylinders, P0 roles only, built to subjects/pickup/layout.json.
// Frame per classes/vehicle.md: +Y up, length along Z with the nose at +Z, width
// along X centred on x = 0, and the +X flank presented (meta.front "+X").
export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0, sideTint: 0 },
  palette: {
    body: "#8ab8d9",
    bed: "#6e96b2",
    glass: "#b7c7e0",
    mirror: "#bbdcf0",
    tyre: "#5c5e5b",
    hub: "#b5babe",
    bumper: "#bbbec4",
    lamp: "#f2eba9",
    grille: "#658397",
  },
};

export function build() {
  const L = 4.8;                        // MVP-STUB: the one chosen metre; everything else is a layout fraction
  const W = 0.412 * L;                  // layout: width.overL
  const H = 0.546 * L;                  // layout: height.overL
  const zFront = L / 2;
  const fromFront = (f) => zFront - f * L;
  const r = (0.198 * L) / 2;            // layout: wheel.diameterOverL
  const t = 0.3;                        // MVP-STUB: tyre width, no layout key
  const clearance = 0.3;                // MVP-STUB: chassis.clearance is UNVERIFIED; inside the V7 band
  const deckY = 2 * r + 0.02;           // body parts rest on the chassis, clear of the wheel tops
  const wall = 0.08, floor = 0.1, bumperD = 0.15;
  const seam = 0.001;                   // 1 mm seating where parts meet, so the union is one lump
  const parts = [];
  const add = (id, solid, zone, role) => parts.push({ id, solid, zone, role });

  // Chassis: between the wheels' inner faces (seated 1 mm into them), full body length.
  add("chassis", K.box([W - 2 * t + 2 * seam, deckY - clearance, L]).at([0, clearance, 0]), "tyre", "chassis");

  // Wheels: a disc revolved about Y, turned onto the X axis, outer face flush with the flank.
  const disc = K.revolve(K.profile.poly([[0, 0], [r, 0], [r, t], [0, t]]), 16).rotZ(90);   // x -t..0
  for (const [axle, f] of [["f", 0.197], ["r", 0.82]]) {       // layout: wheel.centreFromFront
    const z = fromFront(f);
    add(`wheel_${axle}l`, disc.at([W / 2, r, z]), "tyre", "wheel");
    add(`wheel_${axle}r`, disc.at([-W / 2 + t, r, z]), "tyre", "wheel");
  }

  // Hood, cab, bed along the length.
  const hoodTop = 0.591 * H;            // layout: hood.top
  const cabFront = fromFront(0.327);    // layout: cab.start
  const cabRear = fromFront(0.585);     // layout: cab.end
  const bedFront = fromFront(0.594);    // layout: bed.start
  const bedRear = -L / 2;               // layout: bed.end = 1 (exactly the chassis end, no float drift)
  const wallTop = 0.616 * H;            // layout: bedWall.top
  const baseY = deckY - seam;
  add("hood", K.box([W, hoodTop - baseY, zFront - cabFront + seam]).at([0, baseY, (zFront + cabFront - seam) / 2]), "body", "hood");
  add("cab", K.box([W, H - baseY, cabFront - cabRear]).at([0, baseY, (cabFront + cabRear) / 2]), "body", "cab");   // layout: cab.roof = 1
  const bedLen = bedFront - bedRear;
  const bedMid = (bedFront + bedRear) / 2;
  add("bed_floor", K.box([W, floor + seam, bedLen]).at([0, baseY, bedMid]), "bed", "bed");
  const wallY = deckY + floor - seam, wallH = wallTop - wallY;
  add("bed_side_l", K.box([wall, wallH, bedLen]).at([W / 2 - wall / 2, wallY, bedMid]), "body", "bed_wall");
  add("bed_side_r", K.box([wall, wallH, bedLen]).at([-W / 2 + wall / 2, wallY, bedMid]), "body", "bed_wall");
  add("bed_bulkhead", K.box([W - 2 * wall + 2 * seam, wallH, wall]).at([0, wallY, bedFront - wall / 2]), "body", "bed_wall");
  add("tailgate", K.box([W - 2 * wall + 2 * seam, wallH, wall]).at([0, wallY, bedRear + wall / 2]), "body", "tailgate");

  // Bumpers seated 1 mm into the chassis ends.
  const frontTop = 0.368 * H, frontH = 0.101 * H;   // layout: bumper.front.top, bumper.front.h
  const rearH = 0.152 * H;                          // layout: bumper.rear.h (bumper.rear.top is UNVERIFIED)
  add("bumper_front", K.box([W, frontH, bumperD + seam]).at([0, frontTop - frontH, zFront + (bumperD - seam) / 2]), "bumper", "bumper");
  add("bumper_rear", K.box([W, rearH, bumperD + seam]).at([0, deckY - rearH, -L / 2 - (bumperD - seam) / 2]), "bumper", "bumper");
  return parts;
}
