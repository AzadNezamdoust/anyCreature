// WF-V6 V6-1 — school_bus START module for the multi-view experiment (arms B and CONTROL start here).
// Structure = the v56 bus's feature inventory (windshield, window row + door, headlights, turn lenses, cap markers,
// mirrors, stop arm) + the two rear features the rear ortho shows (rear window, rear lamps).
// BODY knobs (16, metres): start values = the v56 template fit (L clamped into the prior card's soft range), ranges =
// subjects/school_bus/prior.json softRanges. FEATURES: every position is a fraction of the body (x of W/2, y of H, z of L
// from the nose / tail) MEASURED on the orthographic turnaround (scripts/v6/ortho.mjs components(), 2026-09-26, px/m
// 129.64, body 6.244 x 2.44 x 2.761 m) — two-axis measurements, never the concept view. Attached parts follow
// scripts/v6/rules.mjs (mirror arm range, bumper flush on the nose / tail face, stop arm on the flank).
import * as K from "../../src/kernel/index.mjs";
import { mirrorPlacement, stopArmPlacement } from "../../scripts/v6/rules.mjs";

export const KNOBS = {
  L:          { v: 6.2633, min: 5, max: 12.7, unit: "m", group: "body" },          // painted body length (nose face .. tail face)
  W:          { v: 2.4408, min: 2, max: 2.8, unit: "m", group: "body" },
  H:          { v: 2.7848, min: 2, max: 3.3, unit: "m", group: "body" },      // roof height
  capDrop:    { v: 0.1146, min: 0.05, max: 0.6, unit: "m", group: "body" },   // H - the flat nose face's top
  capRun:     { v: 0.1071, min: 0.05, max: 0.8, unit: "m", group: "body" },   // nose z - the roof's front edge z
  chamfer:    { v: 0.1395, min: 0.03, max: 0.25, unit: "m", group: "body" },  // vertical nose-corner chamfer
  sillY:      { v: 0.3528, min: 0.25, max: 0.7, unit: "m", group: "body" },
  wheelR:     { v: 0.5293, min: 0.3, max: 0.55, unit: "m", group: "body" },
  axleF:      { v: 1.0227, min: 0.4, max: 2, unit: "m", group: "body" },      // front axle behind the nose face
  axleR:      { v: 1.3562, min: 0.5, max: 2.5, unit: "m", group: "body" },    // rear axle ahead of the tail face
  roofR:      { v: 0.1575, min: 0, max: 0.35, unit: "m", group: "body" },
  capR:       { v: 0.34, min: 0, max: 0.8, unit: "m", group: "body" },
  bumperFTop: { v: 0.5079, min: 0.25, max: 0.8, unit: "m", group: "body" },
  bumperFH:   { v: 0.2436, min: 0.15, max: 0.45, unit: "m", group: "body" },
  bumperRTop: { v: 0.7203, min: 0.3, max: 0.9, unit: "m", group: "body" },
  bumperRH:   { v: 0.3791, min: 0.15, max: 0.45, unit: "m", group: "body" },
  frameScale: { v: 0.801, min: 0.7, max: 1.4, unit: "scale", group: "frame" },  // concept-view similarity (registered.mjs)
  frameX:     { v: -28.35, min: -48, max: 48, unit: "px", group: "frame" },
  frameY:     { v: 25.35, min: -48, max: 48, unit: "px", group: "frame" },
  // FEATURE knobs (fractions; start = the ortho measurement)
  wsY0:       { v: 0.5321, min: 0.45, max: 0.62, unit: "frac", group: "feature" },   // windshield glass bottom / H (front)
  wsY1:       { v: 0.7995, min: 0.72, max: 0.87, unit: "frac", group: "feature" },   // windshield glass top / H (front)
  bandY0:     { v: 0.5473, min: 0.45, max: 0.62, unit: "frac", group: "feature" },   // window band bottom / H (side)
  bandY1:     { v: 0.871, min: 0.8, max: 0.93, unit: "frac", group: "feature" },    // window band top / H (side)
  paneY0:     { v: 0.586, min: 0.5, max: 0.68, unit: "frac", group: "feature" },    // flank pane bottom / H (side)
  paneY1:     { v: 0.833, min: 0.75, max: 0.88, unit: "frac", group: "feature" },   // flank pane top / H (side)
  paneFront:  { v: 0.1141, min: 0.08, max: 0.16, unit: "frac", group: "feature" },  // first pane's front edge behind the nose / L
  panePitch:  { v: 0.1223, min: 0.1, max: 0.14, unit: "frac", group: "feature" },   // pane pitch / L
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0.147, sideTint: 0.009 },
  palette: {
    body: { top: "#fcc523", front: "#f4b618", side: "#f4b719" },
    glass: "#83bae6",
    black: { top: "#212324", front: "#222325", side: "#27282a" },
    tyre: { front: "#303132", side: "#202224" },
    hub: "#989899",
    lamp: "#fdf2dd",
    signal: "#e32228",
    amber: "#f28711",
    orange: "#e95f0f",
    body_front: "#f4b719",
    roof: "#fcc423",
  },
};

export function build() {
  const k = Object.fromEntries(Object.entries(KNOBS).map(([name, o]) => [name, o.v]));
  const { L, W, H } = k;
  const zN = L / 2, zT = -L / 2, seam = 0.001;
  const X = (f) => f * W / 2, Y = (f) => f * H, ZN = (f) => zN - f * L;
  const zF = zN - k.axleF, zR = zT + k.axleR;
  // arches on the axles (turnaround: arch top ~ wheel top + 0.06, half length ~ 1.05 R); the helper grows them to clear
  const halfF = 1.05 * k.wheelR, halfR = 1.05 * k.wheelR, rise = Math.max(0.1, 2 * k.wheelR + 0.06 - k.sillY);
  const zA = Math.min(zF + halfF, zN - 0.1);   // the nose block drops ahead of the front arch
  const zRa = Math.max(zR - halfR, zT + 0.05);
  // RULE bumper: the nose / tail face runs down to the bumper's bottom, so the bumper's back face is flush on it
  const yFb = k.bumperFTop - k.bumperFH;
  const yRb = Math.min(k.sillY, k.bumperRTop - k.bumperRH);
  const tailStep = yRb < k.sillY - 0.005 ? [[zT, yRb], [zRa, yRb], [zRa, k.sillY]] : [[zT, k.sillY]];
  const noseTopY = H - k.capDrop;
  const parts = K.assemble.vehicleBody({
    W, H, hood: false, bed: null,
    side: [[zN, noseTopY], [zN - k.capRun, H], [zT, H], ...tailStep, [zA, k.sillY], [zA, yFb], [zN, yFb]],
    section: [[-W / 2, 0], [W / 2, 0], [W / 2, H], [-W / 2, H]],
    plan: [[-W / 2, zT], [W / 2, zT], [W / 2, zN - k.chamfer], [W / 2 - k.chamfer, zN], [k.chamfer - W / 2, zN], [-W / 2, zN - k.chamfer]],
    cab: [zT, zN], chassisFront: zA,
    roofR: k.roofR, capR: k.capR, cornerR: 0, roundSegs: 2, liner: false,
    sill: k.sillY, clearance: 0.3,
    wheels: { r: k.wheelR, width: 0.3, z: [zF, zR], hub: { r: 0.5 * k.wheelR }, segs: [16, 8], hubSegs: [8, 4], tread: false },
    arches: [{ z: zF, halfLength: halfF, rise, n: 2 }, { z: zR, halfLength: halfR, rise, n: 2 }], archSegs: [12, 8],
    // measured: front bumper 0.14 m ahead of the nose, 0.07 m proud of the flanks, wrap 0.20 m; rear 0.10 / 0.07 / 0.33
    bumpers: [{ face: "nose", top: k.bumperFTop, h: k.bumperFH, depth: 0.14, out: 0.07, wrap: 0.2 },
      { face: "tail", top: k.bumperRTop, h: k.bumperRH, depth: 0.1, out: 0.07, wrap: 0.33 }],
    zones: { body: "body", tyre: "tyre", tread: "tyre", hub: "hub", bumper: "black", liner: "black" },
  });
  const cab = parts.find((p) => p.id === "cab");
  // windshield (front ortho: glass field x +-0.879 W/2, post 0.108, frame 0.16 / 0.08 / 0.085)
  parts.push(...K.assemble.paneFrame({ host: cab, face: "+z", bounds: K.span({ x: [-X(0.879), X(0.879)], y: [Y(k.wsY0), Y(k.wsY1)] }), panes: 2, post: 0.108, frame: { top: 0.16, bottom: 0.08, side: 0.085 }, body: parts, idPrefix: "windshield" }));
  // window band + 7 panes on both flanks (side ortho), ending at the door; door leaf + narrow pane on the near flank
  const doorRear = ZN(0.1057);
  parts.push(...K.assemble.windowRow({ host: cab, band: [Y(k.bandY0), Y(k.bandY1)], z: [zT + 0.017 * L, doorRear], panes: { front: ZN(k.paneFront), pitch: k.panePitch * L, w: 0.866 * k.panePitch * L, count: 7, y: [Y(k.paneY0), Y(k.paneY1)] }, body: parts, idPrefix: "row" }));
  parts.push(...K.assemble.busDoor({ host: cab, face: "+x", z: [doorRear, ZN(0.0183)], y: [Y(k.bandY0), Y(k.bandY1)], pane: { z: [ZN(0.0911), ZN(0.033)], y: [Y(k.paneY0), Y(k.paneY1)] }, body: parts, idPrefix: "door" }));
  // headlights + amber turn lenses (front ortho)
  parts.push(...K.assemble.lamp({ body: parts, face: "nose", centre: [X(0.718), Y(0.352)], diameter: 0.25, segs: 12 }));
  parts.push(...K.assemble.lamp({ body: parts, face: "nose", centre: [X(0.721), Y(0.263)], diameter: 0.231, role: "prop", zone: "amber", shape: { w: 0.231, h: 0.092, r: 0.03 }, idPrefix: "turn" }));
  // cap markers (front ortho: red outer, amber inner, d 0.17, housing pad 0.05)
  parts.push(...K.assemble.lamp({ host: cab, face: "cap", body: parts, y: Y(0.911), diameter: 0.17, lenses: [{ x: X(0.771), zone: "signal" }, { x: X(0.537), zone: "orange" }], housing: { pad: 0.05, zone: "black" }, idPrefix: "marker" }));
  // mirrors — RULE: head outboard of the flank on its arm (front ortho: head 0.09 m out, 0.23 w, y 0.685 H, h 0.196 H;
  // side + top orthos: head centre 0.18 m ahead of the nose); arm length clamped to 0.25-0.45 m
  const mp = mirrorPlacement({ W, noseZ: zN, chamfer: k.chamfer, centreY: Y(0.685), headOut: 0.09, ahead: 0.18, headW: 0.23, headH: Y(0.196) });
  parts.push(...K.assemble.mirror({ body: parts, side: mp.side, centreY: mp.centreY, z: mp.z, head: mp.head, arm: mp.arm, armFrom: mp.armFrom, zone: "black" }));
  // stop arm — RULE: folded on the +x flank, seated on one surface; side ortho: centre 0.1195 L behind the nose, y 0.465 H,
  // d 0.48, post from 0.40 H up to the sign's centre
  const sp = stopArmPlacement({ z: ZN(0.1195), y: Y(0.465), diameter: 0.48, border: 0.02, bandBottom: Y(k.bandY0) });
  parts.push(...K.assemble.stopArm({ host: cab, centre: sp.centre, diameter: sp.diameter, border: sp.border, post: [Y(0.4), sp.centre[1]], body: parts, idPrefix: "stopArm" }));
  // rear window (rear ortho: glass x +-0.841 W/2, y 0.592-0.816 H, post 0.124, frame 0.108 / 0.108 / 0.123) + rear lamps
  parts.push(...K.assemble.paneFrame({ host: cab, face: "-z", bounds: K.span({ x: [-X(0.841), X(0.841)], y: [Y(0.592), Y(0.816)] }), panes: 2, post: 0.124, frame: { top: 0.108, bottom: 0.108, side: 0.123 }, body: parts, idPrefix: "rearWindow" }));
  parts.push(...K.assemble.lamp({ body: parts, face: "tail", centre: [X(0.752), Y(0.38)], diameter: 0.22, zone: "signal", role: "prop", segs: 12, idPrefix: "rearLamp" }));
  return parts;
}
