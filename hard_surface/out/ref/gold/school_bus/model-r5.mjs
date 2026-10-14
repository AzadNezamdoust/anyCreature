// GOLD school_bus — hand-built against refs/school_bus.png + subjects/school_bus/turnaround (side_right / front / rear /
// top). Author frame (vehicle class): nose +z, near flank +x, y up, ground y = 0, x and z centred on the body.
// Numbers are measurements off the orthographic turnaround (scripts/v6/ortho.mjs registration, 129.64 px/m) unless the
// comment says "concept" (the concept wins where the two disagree on a feature the concept shows).
import * as K from "../../../../src/kernel/index.mjs";

export const KNOBS = {
  // concept-view similarity (scripts/registered.mjs framed): the concept camera's scale / shift for this body
  frameScale: { v: 0.8173, min: 0.7, max: 1.4, unit: "scale", group: "frame" },
  frameX: { v: -24.35, min: -48, max: 48, unit: "px", group: "frame" },
  frameY: { v: 26.85, min: -48, max: 48, unit: "px", group: "frame" },
};

export const meta = {
  front: "+X",
  class: "vehicle",
  seed: 1,
  shade: { ao: 0, upTint: 0.147, sideTint: 0.009 },
  palette: {
    // concept flat colours (median samples): roof #fcc524, +x flank #f3b619, nose #f4b718
    body: { top: "#fcc524", front: "#f3b619", side: "#f4b718" },
    glass: "#83bae6",
    black: { top: "#26272a", front: "#222325", side: "#27282a" },
    tyre: { top: "#2a2b2d", front: "#2f3032", side: "#202224" },
    hub: "#999899",
    lamp: "#fdf3df",
    signal: "#e32328",
    amber: "#f28711",
    orange: "#e95f0f",
    white: "#fbfbfb",
    well: "#8f6912",
    mirror: "#333435",                              // concept: mirror heads a shade lighter than the frames
  },
};

/** Every dimension (metres). */
export const DEFAULTS = {
  L: 6.2633, W: 2.4408, H: 2.7848,
  sill: 0.415,                                   // side ortho: body lower edge 0.417
  R: 0.46, zF: 2.096, zR: -1.801,                // r3 concept: R ~0.46 (sign-to-arch gap; side ortho 0.478), hub centres z 2.098 / -1.801
  tyreF: { inset: 0.05, w: 0.34 },              // front ortho: tyre x 0.771..1.118
  tyreR: { inset: 0.06, w: 0.42 },              // rear ortho: dual tyre x 0.717..1.142
  hubR: 0.21,                                    // r4 concept: hub ~0.47 of the tyre (projected r 0.19-0.205; side ortho 0.243)
  bf: { top: 0.615, bot: 0.29, depth: 0.115, wrap: 0.21, out: 0.06 },  // front ortho y 0.297-0.613, x +-1.28; rear ortho: nothing under the rear one (0.335)
  br: { top: 0.73, bot: 0.35, depth: 0.05, wrap: 0.47, out: 0.015 }, // r5 A2 concept: end block 0.05 deep, 0.47 along the flank (out 0 z-fights the flank); side ortho z -2.787..-3.211, y 0.343-0.752 (top kept 0.73: the rear turn bezel starts 0.7525)
  cap: { run: 0.16, drop: 0.14, tail: 0.15, tailDrop: 0.25, segs: 5 },  // r5 K1: front cap run x drop (vertical face to 2.645); rear cap tail x tailDrop
  roofR: 0.16, edgeDrop: 0.14, roofSegs: 1,      // long roof edges: roofR (x) x edgeDrop (y) in roofSegs facets (front ortho corner ~0.2)
  noseR: 0.14, planR: 0.12, planRT: 0.12,        // plan corners: lamp panel / body front / body rear (side ortho chamfer line at z 3.005)
  pod: { flat: true, yc: 2.635, h: 0.22, d: 0.15, r: 0.09 },  // r5 K1 concept: housings 38 px, 7 px yellow gap over the 14 px frame bar -> flat on the vertical cap face, lenses facing +z
  lift: 0,                                       // the shell over the axles: everything but wheels / hubs / axles raised
  head: { x0: 1.295, x1: 1.545, y0: 1.63, y1: 2.18, zc: 2.97, d: 0.07, root: 1.04 },  // r5: zc follows the windshield face back 0.06 (C1); concept: beside the windshield, arms straight out from its frame
  cowl: { y0: 1.26, y1: 1.43, back: 0.15 },       // r5 C1 concept: a ~48 deg lit slope from the frame bottom (1.43) down; concept: the windshield face sits back of the lamp panel (hood line)
};

const A = K.assemble;
const bx = (x0, x1, y0, y1, z0, z1) => K.box([x1 - x0, y1 - y0, z1 - z0]).at([(x0 + x1) / 2, y0, (z0 + z1) / 2]);

export function build() { return buildWith(); }

export function buildWith(o = {}) {
  const D = { ...DEFAULTS, ...o };
  const { L, W, H, sill, R, zF, zR, bf, br, cap } = D;
  const zN = L / 2, zT = -L / 2, hw = W / 2;
  const parts = [];
  const add = (id, solid, zone, role, extra = {}) => { const p = { id, solid, zone, role, ...extra }; parts.push(p); return p; };

  // ---- ROUNDED shell. Upper body = the hull of stacked plan outlines: each level of the top rounding (v = 0..90 deg)
  // is the rounded-rectangle plan pulled in by r (1 - cos v) along x and by the cap run along z, at y = H - ry (1 - sin v):
  // long roof edges and front / rear caps are elliptical quadrants (r x ry, run x ry) and the four top corners blend
  // (no sharp groin where the roof edge meets the cap). Below it: the lamp panel ahead of the windshield face (the cowl
  // step, concept), and the nose / tail blocks that run down to the bumper bottoms behind the bumpers.
  const noseBlock = 0.18, tailBlock = 0.3;
  const zU = zN - D.cowl.back;              // the upper nose (windshield) face
  const rr = (a, z0, z1, c, y, k = 2, cT = c) => {   // rounded-rectangle outline (half-width a, z0..z1, corners c front / cT rear) at y
    const pts = [];
    for (const [sx, sz] of [[1, 1], [-1, 1], [-1, -1], [1, -1]]) {
      const cc = sz > 0 ? c : cT, cx = sx * (a - cc), cz = sz > 0 ? z1 - cc : z0 + cc;
      for (let j = 0; j <= k; j += 1) { const t = (Math.PI / 2) * (j / k); pts.push([cx + sx * cc * Math.cos(t), y, cz + sz * cc * Math.sin(t)]); }
    }
    return pts;
  };
  const rp = D.planR, rpT = D.planRT;
  // r5: the long roof edges, the front cap and the rear cap each have their own quadrant (inset x height, facets); the
  // levels are the union of their sample heights, each profile interpolated linearly between its own samples
  const quad = (r, drop, segs) => Array.from({ length: segs + 1 }, (_, i) => { const v = (Math.PI / 2) * (i / segs); return [r * (1 - Math.cos(v)), H - drop + drop * Math.sin(v)]; });
  const off = (q, y) => {
    if (y <= q[0][1]) return 0;
    for (let i = 1; i < q.length; i += 1) if (y <= q[i][1] + 1e-9) { const [d0, y0] = q[i - 1], [d1, y1] = q[i]; return d0 + ((d1 - d0) * (y - y0)) / (y1 - y0); }
    return q[q.length - 1][0];
  };
  const qE = quad(D.roofR, D.edgeDrop, D.roofSegs), qF = quad(cap.run, cap.drop, cap.segs), qT = quad(cap.tail, cap.tailDrop, cap.segs);
  const ys = [...new Set([...qE, ...qF, ...qT].map((p) => +p[1].toFixed(6)))].sort((a, b) => a - b);
  const levels = [rr(hw, zT, zU, rp, sill, 2, rpT)];
  for (const y of ys) {
    const dx = off(qE, y), dz = off(qF, y), dzT = off(qT, y), m = 0.5 * Math.min(dx, dz);
    levels.push(rr(hw - dx, zT + dzT, zU - dz, Math.max(0.03, rp - m), y, 2, Math.max(0.03, rpT - m)));
  }
  const upper = K.hull(levels.flat());
  const planNose = A.planSolid(K.profile.fillet([[-hw, zN - 0.4], [hw, zN - 0.4], [hw, zN], [-hw, zN]], [0, 0, D.noseR, D.noseR], 2), 0, H);
  const lamps = K.intersect(A.sideSolid([[zN - noseBlock, Math.max(bf.bot, br.bot)], [zN, Math.max(bf.bot, br.bot)], [zN, D.cowl.y0], [zU, D.cowl.y1], [zN - noseBlock, D.cowl.y1]], -hw, hw), planNose);
  const planTail = A.planSolid(K.profile.fillet([[-hw, zT], [hw, zT], [hw, zT + 0.5], [-hw, zT + 0.5]], [rpT, rpT, 0, 0], 2), 0, H);
  const tail = K.intersect(bx(-hw, hw, br.bot, sill + 0.02, zT, zT + tailBlock), planTail);
  let shell = K.union(upper, lamps, tail);

  // ---- wheel arches (side ortho): tyre + liner wide, 45 deg chamfers to a flat top just over the tyre
  const aHalf = R + 0.04, aTop = 2 * R + 0.04, tHalf = 0.55 * R, aKnee = aTop - (aHalf - tHalf);
  const arch = (zc, g = 0) => [[zc - aHalf - g, aKnee], [zc - tHalf - g * 0.414, aTop + g], [zc + tHalf + g * 0.414, aTop + g], [zc + aHalf + g, aKnee]];
  const tyres = [
    { key: "f", z: zF, x1: hw - D.tyreF.inset, x0: hw - D.tyreF.inset - D.tyreF.w },
    { key: "r", z: zR, x1: hw - D.tyreR.inset, x0: hw - D.tyreR.inset - D.tyreR.w },
  ];
  const wellX = (t) => t.x0 - 0.04;           // the back plate is MIN_FEAT (0.04) thick
  const tools = [];
  for (const t of tyres) {
    const tool = A.sideSolid([[t.z - aHalf, sill - 0.5], ...arch(t.z), [t.z + aHalf, sill - 0.5]], wellX(t), hw + 0.5);
    tools.push(tool, tool.mirrorX());
  }
  shell = K.cut(shell, K.union(tools));
  const cab = add("cab", shell, "body", "cab");

  // ---- arch wells: a khaki liner on the arch walls + the well's back plate (the tyre's inner face sits on it)
  for (const t of tyres) {
    const outer = [[t.z - aHalf - 0.0005, sill], ...arch(t.z, 0.0005), [t.z + aHalf + 0.0005, sill]];
    const inner = [[t.z - aHalf + 0.04, sill - 0.3], ...arch(t.z, -0.04), [t.z + aHalf - 0.04, sill - 0.3]];
    const band = K.cut(A.sideSolid(outer, wellX(t), hw - 0.004), A.sideSolid(inner, wellX(t) - 0.1, hw + 0.1));
    const liner = K.union(band, A.sideSolid(outer, wellX(t) - 0.0005, t.x0 + 0.0005));
    add(`arch_${t.key}l`, liner, "well", "body");
    // far side: the back plate alone (its arch walls are never seen from the reference views)
    add(`arch_${t.key}r`, A.sideSolid(outer, wellX(t) - 0.0005, t.x0 + 0.0005).mirrorX(), "well", "body");
  }

  // ---- wheels: flat tyre disc + flat grey hub, near side finer than the far side; an axle under the sill per pair
  for (const t of tyres) {
    const w = t.x1 - t.x0;
    for (const [sd, segs, place] of [["l", 20, (s) => s], ["r", 12, (s) => s.mirrorX()]]) {
      const tyre = K.revolve([[0, 0], [R, 0], [R, w], [0, w]], segs).rotZ(90).at([t.x1, R, t.z]);
      const hub = K.revolve([[0, 0], [D.hubR, 0], [D.hubR, 0.04], [0, 0.04]], sd === "l" ? 16 : 8).rotZ(90).at([t.x1 + 0.0395, R, t.z]);
      add(`wheel_${t.key}${sd}`, place(tyre), "tyre", "wheel");
      add(`hub_${t.key}${sd}`, place(hub), "hub", "hub");
    }
    // hidden behind the tyres and the bumpers; meets both tyres' inner faces and the shell's underside
    add(`axle_${t.key}`, bx(-t.x0 - 0.0005, t.x0 + 0.0005, sill + D.lift - 0.045, sill + D.lift + 0.0008, t.z - 0.05, t.z + 0.05), "tyre", "axle");
  }

  // ---- bumpers: black blocks wrapping the corners (plan U, outer corners rounded)
  const bumper = (b, dir) => {
    const z0 = dir > 0 ? zN : zT;
    const zo = z0 + dir * b.depth, zi = z0 - dir * 0.0005, zw = z0 - dir * b.wrap;
    const xb = hw + b.out, xs = hw - 0.0005;
    const pts = [[-xb, zw], [-xb, zo], [xb, zo], [xb, zw], [xs, zw], [xs, zi], [-xs, zi], [-xs, zw]];
    return A.planSolid(K.profile.fillet(pts, [0, 0.05, 0.05, 0, 0, 0, 0, 0], 2), b.bot, b.top);
  };
  add("bumper_front", bumper(bf, 1), "black", "bumper");
  add("bumper_rear", bumper(br, -1), "black", "bumper");

  // ---- windshield: two panes in a thick black frame (front ortho glass x +-1.072, post 0.108; r4 concept at x 0.55:
  // glass y 1.527-2.352, frame 1.416-2.456)
  parts.push(...A.paneFrame({ host: cab, face: "+z", bounds: K.span({ x: [-1.047, 1.047], y: [1.53, 2.35] }), panes: 2, post: 0.12,
    frame: { top: 0.10, bottom: 0.10, side: 0.12 }, body: parts, idPrefix: "windshield" }));

  // ---- side window band + 7 panes on both flanks, the door (narrow pane) at the front of the +x flank.
  // side ortho: band y 1.49-2.445, panes y 1.643-2.299, pitch 0.77, centres 2.0865 - 0.7695 i; concept: frames thicker
  // r4 concept (solved camera): band 1.39-1.42 .. 2.38-2.405 along z -2.15..0, panes 1.60-1.62 .. 2.20-2.23; at the door
  // the black ends at y 1.46-1.48 and the door pane runs 1.47-2.24
  const doorRear = 2.49;
  parts.push(...A.windowRow({ host: cab, band: [1.40, 2.39], z: [zT + 0.108, doorRear],
    panes: { front: 2.409, pitch: 0.7695, w: 0.645, count: 7, y: [1.61, 2.22] }, body: parts, idPrefix: "row" }));
  parts.push(...A.busDoor({ host: cab, face: "+x", z: [doorRear, zU - D.planR], y: [1.46, 2.39], pane: { z: [2.55, 2.915], y: [1.50, 2.26] }, body: parts, idPrefix: "door" }));
  // the far flank has no door: the band runs on to the front corner with the driver's window (turnaround: hidden side)
  parts.push(...A.busDoor({ host: cab, face: "-x", z: [doorRear, zU - D.planR], y: [1.40, 2.39], pane: { z: [2.55, 2.915], y: [1.61, 2.29] }, body: parts, idPrefix: "door_driver" }));

  // ---- rear window (rear ortho: glass x +-1.026, y 1.643-2.252, post 0.124, frame 0.108 / 0.116 / 0.123)
  parts.push(...A.paneFrame({ host: cab, face: "-z", bounds: K.span({ x: [-1.026, 1.026], y: [1.643, 2.252] }), panes: 2, post: 0.124,
    frame: { top: 0.108, bottom: 0.116, side: 0.123 }, body: parts, idPrefix: "rearWindow" }));

  // ---- nose lamps: headlights (front ortho d 0.247 + black ring to 0.293 at x +-0.87, y 0.97), amber turn lenses
  parts.push(...A.lamp({ body: parts, face: "nose", centre: [0.872, 0.97], diameter: 0.294, role: "prop", zone: "black", segs: 12, idPrefix: "lampBezel" }));
  parts.push(...A.lamp({ body: parts, face: "nose", centre: [0.872, 0.97], diameter: 0.25, thickness: 0.05, segs: 12 }));
  parts.push(...A.lamp({ body: parts, face: "nose", centre: [0.872, 0.725], role: "prop", zone: "black", shape: { w: 0.27, h: 0.125, r: 0.035 }, idPrefix: "turnBezel" }));
  parts.push(...A.lamp({ body: parts, face: "nose", centre: [0.872, 0.725], role: "prop", zone: "amber", thickness: 0.05, shape: { w: 0.231, h: 0.093, r: 0.025 }, idPrefix: "turn" }));

  // ---- tail lamps (rear ortho: red d 0.224 + ring 0.262 at x +-0.914, y 1.049; amber 0.224 x 0.077 at y 0.81)
  parts.push(...A.lamp({ body: parts, face: "tail", centre: [0.914, 1.049], diameter: 0.262, zone: "black", role: "prop", segs: 12, idPrefix: "rearLampBezel" }));
  parts.push(...A.lamp({ body: parts, face: "tail", centre: [0.914, 1.049], diameter: 0.224, thickness: 0.05, zone: "signal", role: "prop", segs: 12, idPrefix: "rearLamp" }));
  parts.push(...A.lamp({ body: parts, face: "tail", centre: [0.914, 0.81], role: "prop", zone: "black", shape: { w: 0.262, h: 0.115, r: 0.03 }, idPrefix: "rearTurnBezel" }));
  parts.push(...A.lamp({ body: parts, face: "tail", centre: [0.914, 0.81], role: "prop", zone: "amber", thickness: 0.05, shape: { w: 0.224, h: 0.077, r: 0.022 }, idPrefix: "rearTurn" }));
  // r4: the lamps sit sunk 0.035 into the nose / tail (declared embedded below): bezels stand 0.005 m proud, lenses 0.015
  // (the side silhouette shows no lamp nubs)
  for (const [ids, dz] of [[["lampBezel", "lamp", "turnBezel", "turn"], -0.035], [["rearLampBezel", "rearLamp", "rearTurnBezel", "rearTurn"], 0.035]]) {
    for (const id of ids) for (const sd of ["l", "r"]) { const p = parts.find((q) => q.id === `${id}_${sd}`); p.solid = p.solid.at([0, 0, dz]); }
  }

  // ---- cap marker pods, front and rear (front ortho: housing x 0.509..1.088, y 2.383..2.646; red lens outboard at
  // x 0.941, amber inboard at 0.656, d 0.17; rear ortho the same, y 2.414..2.677). Each pod is a rounded housing laid on
  // the cap surface (a shell that follows the rounding) with two round lenses laid on the housing.
  // r4 concept: the front housing starts ~0.07 m over the windshield frame (bottom ~2.53) -> centre 2.62
  const shellOn = (base, dir, t, prism, tIn = 0.0004) => {
    const mid = (base.aabb().min[2] + base.aabb().max[2]) / 2;
    const half = dir > 0 ? bx(-5, 5, -1, 9, mid, 99) : bx(-5, 5, -1, 9, -99, mid);
    // a layer is thin by construction: its boxes are not residual walls of a cut (the kernel's thin-cut record is dropped)
    return new K.Solid(K.intersect(K.cut(base.at([0, 0, dir * (t - tIn)]), base.at([0, 0, -dir * tIn])), prism, half)._m, [], []);
  };
  const disc = (cx, cy, r, n) => Array.from({ length: n }, (_, k) => { const t = (2 * Math.PI * (k + 0.5)) / n; return [cx + r * Math.cos(t), cy + r * Math.sin(t)]; });
  const cabBase = cab.solid;
  const P = D.pod;
  for (const [dir, pre, yc, n] of [[1, "marker", P.yc, 12], [-1, "rearMarker", 2.555, 8]]) {
    for (const sx of [1, -1]) {
      const sd = sx > 0 ? "l" : "r";
      const lx = [0.941 * sx, (dir > 0 ? 0.656 : 0.679) * sx];
      const x0 = Math.min(...lx) - 0.13, x1 = Math.max(...lx) + 0.13, hh = dir > 0 ? P.h / 2 : 0.13;
      const outline = K.profile.roundRect({ x: [x0, x1], y: [yc - hh, yc + hh], r: dir > 0 ? P.r : 0.1, segs: dir > 0 ? 3 : 2 });
      const foot = A.frontSolid(outline, -9, 9);
      const flat = dir > 0 && P.flat;
      // r4: the rear pods sit sunk (MIN_FEAT layers, declared embedded): housing 0.005 m proud of the tail cap, lenses
      // 0.015 (the side silhouette shows no tail nub); the front pods keep their depth
      // r5 K1 (flat): the front housing is a slab on the cap's vertical face (seated into the cab), lenses facing +z
      const housing = flat ? A.frontSolid(outline, zU - 0.1, zU + 0.035) : dir > 0 ? shellOn(cabBase, dir, 0.035, foot) : shellOn(cabBase, dir, 0.04, foot, 0.035);
      const hp = add(`${pre}_housing_${sd}`, housing, "black", "prop");
      if (dir < 0 || flat) Object.assign(hp, { touches: ["cab"], embed: true });
      lx.forEach((x, i) => {
        const lens = A.frontSolid(disc(x, yc, dir > 0 ? P.d / 2 : 0.085, n), -9, 9);
        // flat lens: 0.055 on z (MIN_FEAT floor), sunk 0.025 into the housing, 0.03 proud
        const solid = flat ? A.frontSolid(disc(x, yc, P.d / 2, n), zU + 0.01, zU + 0.065) : dir > 0 ? shellOn(housing, dir, 0.03, lens) : shellOn(cabBase, dir, 0.04, lens, 0.025);
        const lp = add(`${pre}_${sd}${i}`, solid, i === 0 ? "signal" : dir > 0 ? "orange" : "amber", "prop");
        if (dir < 0) Object.assign(lp, { touches: [hp.id, "cab"], embed: true });
        if (flat) Object.assign(lp, { touches: [hp.id], embed: true });
      });
    }
  }

  // ---- mirrors: dark heads (front ortho x 1.295..1.545, y 1.59..2.14, 0.25 x 0.55; side ortho depth 0.22) beside the
  // windshield (concept: the heads sit beside its frame, not ahead of the nose as the side ortho draws them)
  const h = D.head, hz = h.zc, hzz = [hz - h.d / 2, hz + h.d / 2];
  const head = K.hull(bx(h.x0, h.x1, h.y0 + 0.03, h.y1 - 0.03, ...hzz), bx(h.x0 + 0.03, h.x1 - 0.03, h.y0, h.y1, ...hzz));
  // the "[" bracket (front ortho): two arms straight out along x from the windshield frame's side, at the face, to a bar
  // inside the head's outline; the bar is two stubs (arm -> head top, head bottom -> arm), the head carries the middle
  // (the arms sit just behind the glass / frame face, so they show from the frame's edge outward)
  const armEnd = [(h.x0 + h.x1) / 2, zU - 0.0075];
  const arm = (y) => bx(h.root, armEnd[0] + 0.025, y - 0.0225, y + 0.0225, armEnd[1] - 0.0225, armEnd[1] + 0.0225);
  const stub = (y0, y1) => bx(armEnd[0] - 0.025, armEnd[0] + 0.025, y0, y1, armEnd[1] - 0.025, armEnd[1] + 0.025);
  const mirrorParts = [["mirror_head", head], ["mirror_arm", arm(h.y1 + 0.085), 0], ["mirror_arm", arm(h.y0 - 0.08), 1],
    ["mirror_arm", stub(h.y1 - 0.0005, h.y1 + 0.063), 2], ["mirror_arm", stub(h.y0 - 0.058, h.y0 + 0.0005), 3]];
  for (const [sd, f] of [["l", (s) => s], ["r", (s) => s.mirrorX()]]) {
    for (const [name, s, i] of mirrorParts) add(i === undefined ? `${name}_${sd}` : `${name}_${sd}${i}`, f(s), i === undefined ? "mirror" : "black", "mirror");
  }

  // ---- stop arm: red octagon 0.485 flat-to-flat on a white rim 0.024 with a thin dark outline; r3 concept: centred under
  // the first regular pane (z 2.09); r4 concept (solved camera): outer octagon centre y 1.25, a ~0.29 (side ortho: centre
  // z 2.37, y 1.279; black post z 2.672..2.745 from y 1.08 up to a hinge block under the band)
  // octagon profiles (flats up / down / fore / aft) in the flank plane, extruded MIN_FEAT out along +x from x0
  const octPts = (a, cz, cy) => Array.from({ length: 8 }, (_, k) => { const t = Math.PI / 8 + (k * Math.PI) / 4; return [cz + (a / Math.cos(Math.PI / 8)) * Math.cos(t), cy + (a / Math.cos(Math.PI / 8)) * Math.sin(t)]; });
  const onFlank = (outer, holes, x0) => K.extrude(outer.map(([z, y]) => [-z, y]), 0.04, holes ? { holes: holes.map((h2) => h2.map(([z, y]) => [-z, y])) } : {}).rotY(90).at([x0, 0, 0]);
  const sc = [2.09, 1.25], signR = 0.2425, plateR = signR + 0.024, rimR = plateR + 0.008;
  // the stop arm folds in front of the window band's lower edge: the band (and door leaf) inlays are notched clean through
  // under its footprint, so the white plate and its thin dark outline ring sit on the flank, the red sign on the plate
  const notch = K.extrude(octPts(rimR, sc[0], sc[1]).map(([z, y]) => [-z, y]), 0.1).rotY(90).at([hw - 0.05, 0, 0]);
  for (const id of ["row_band_l", "door_leaf"]) { const p = parts.find((q) => q.id === id); p.solid = K.cut(p.solid, notch); }
  // r4 concept: ahead of the sign's centre the black (band + door leaf) ends at y 1.46 (the step hides behind the sign)
  { const p = parts.find((q) => q.id === "row_band_l"); p.solid = K.cut(p.solid, bx(hw - 0.1, hw + 0.1, 1.3, 1.46, sc[0], doorRear + 0.05)); }
  add("stopArm_rim", onFlank(octPts(rimR, ...sc), [octPts(plateR, ...sc)], hw - 0.0003), "black", "prop");
  // r4: the white border is a ring round the sign, the red face level with it, so the white rim reads evenly (concept)
  add("stopArm_border", onFlank(octPts(plateR, ...sc), [octPts(signR, ...sc)], hw - 0.0003), "white", "prop");
  add("stopArm_sign", onFlank(octPts(signR, ...sc), null, hw - 0.0003), "signal", "prop");
  add("stopArm_post", bx(hw - 0.0005, hw + 0.045, 0.985, 1.4105, sc[0] + 0.272, sc[0] + 0.345), "black", "prop");
  // the hinge meets the raised band bottom and sits on the band groove's floor (the band is cut away under it)
  add("stopArm_hinge", bx(hw - 0.0205, hw + 0.06, 1.41, 1.4605, sc[0] + 0.23, doorRear), "black", "prop");
  // declared contacts: the post and hinge carry the sign (they meet its rim / plate at the front flat)
  for (const id of ["stopArm_rim", "stopArm_border"]) parts.find((q) => q.id === id).touches = ["stopArm_post", "stopArm_hinge"];
  // declared seats: the lamp lenses sit sunk in their bezels, the bracket arms are socketed behind the windshield frame
  const seat = (id, hosts) => { const p = parts.find((q) => q.id === id); p.touches = hosts; p.embed = true; };
  for (const sd of ["l", "r"]) {
    for (const [lens, bezel] of [["lamp", "lampBezel"], ["turn", "turnBezel"], ["rearLamp", "rearLampBezel"], ["rearTurn", "rearTurnBezel"]]) {
      seat(`${bezel}_${sd}`, ["cab"]); seat(`${lens}_${sd}`, [`${bezel}_${sd}`, "cab"]);
    }
    for (const i of [0, 1]) seat(`mirror_arm_${sd}${i}`, ["cab", "windshield_frame", `windshield_${sd}`]);
  }
  // r5 B1 variant: the shell over the axles (everything but the wheels, hubs and axles) raised by D.lift
  if (D.lift) for (const p of parts) if (!["wheel", "hub", "axle"].includes(p.role)) p.solid = p.solid.at([0, D.lift, 0]);
  return parts;
}
