import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  front: "-Z",
  class: "building",
  seed: 1,
  shade: { ao: 0.08, upTint: 0.12, sideTint: -0.411 },
  palette: {
    brick: "#a85643",
    trim: "#8b7e73",
    glass: "#80a9ac",
    iron: "#887768",
    roof: "#918680",
    fixture: "#999f9d",
    ac: "#c0c0bf",
    coping: "#a77b6f",
    surround: "#ad8067",
    canopy: "#528b50",
    frame: "#8b7e73",
    sill: "#be9589",
    awning: "#538c54",
    signbox: "#668865",
    parapet: "#a77b6f",
    metal: "#c0c0bf",
  },
};

export function build() {
  // Door anchor: 0.127 H is approximately 2.1 m. The solved target face
  // (208 px wide, 550 px high) gives W/H approximately 0.454.
  const W = 7.5, H = 16.5;
  const D = 0.874 * W;                  // layout: massing.depthOverW
  const crownH = 0.031 * H;            // layout: crown.height
  // Missing layout keys: massing.wallThickness, roof.thickness,
  // crown.thickness, roof_fixture.size, roof_fixture.position.
  // These construction dimensions and fixture placements are provisional.
  const T = 0.04 * W, slabH = 0.0048 * H;
  const capH = 0.016 * W;
  const parts = [];
  const add = (id, solid, zone, role, touches) =>
    parts.push({ id, solid, zone, role, touches });

  // P1 measured layout: glass dimensions, bay centres from min x, and rows.
  const paneW = 0.089 * W, paneH = 0.12 * H;
  const headGap = 0.038 * H, rowPitch = 0.283 * H;
  // frame.widthRatio and frame.proud are UNVERIFIED: these are visual choices.
  const frame = 0.012 * W, proud = 0.016 * W;
  const seam = 0.0001 * W; // Sub-millimetre seating at shared surfaces.
  // MISSING KEY storefront.w, storefront.centreX, storefront.bottom,
  // door.w, door.centreX: provisional shop division, not measured layout.
  const openings = [];
  for (const [bay, fraction] of [0.231, 0.808].entries()) {
    for (let row = 0; row < 2; row += 1) {
      openings.push({ id: `window_${bay}_${row}`, role: "window",
        x: -W / 2 + fraction * W,
        y: H - headGap - row * rowPitch - paneH - frame,
        w: paneW, h: paneH });
    }
  }
  openings.push({ id: "shop", role: "storefront", x: 0.15 * W,
    y: 0.037 * H, w: 0.45 * W, h: 0.08 * H });
  openings.push({ id: "entrance", role: "door", x: -0.29 * W,
    y: frame, w: 0.16 * W, h: 0.127 * H - 2 * frame });
  const openingTools = K.union(openings.map((o) =>
    K.box([o.w + 2 * frame - 2 * seam,
      o.h + 2 * frame + (o.role === "door" ? 2 * seam : -2 * seam), T + 2 * proud])
      .at([o.x, o.y - frame + (o.role === "door" ? -seam : seam), T / 2])));

  // Four enclosing walls, with side walls running the entire depth.
  // A separate solid core supplies continuous bearing below the roof.
  const walls = ["wall_front", "wall_back", "wall_left", "wall_right"];
  add("wall_front", K.cut(K.box([W - 2 * T, H, T]).at([0, 0, T / 2]), openingTools),
    "brick", "massing", ["wall_left", "wall_right", "block_core", "roof_slab"]);
  add("wall_back", K.box([W - 2 * T, H, T]).at([0, 0, D - T / 2]),
    "brick", "massing", ["wall_left", "wall_right", "block_core", "roof_slab"]);
  add("wall_left", K.box([T, H, D]).at([(W - T) / 2, 0, D / 2]),
    "brick", "massing", ["wall_front", "wall_back", "block_core", "roof_slab"]);
  add("wall_right", K.box([T, H, D]).at([-(W - T) / 2, 0, D / 2]),
    "brick", "massing", ["wall_front", "wall_back", "block_core", "roof_slab"]);
  add("block_core", K.box([W - 2 * T + 2 * seam, H + seam, D - 2 * T + 2 * seam]).at([0, 0, D / 2]),
    "brick", "massing", [...walls, "roof_slab"]);
  add("roof_slab", K.box([W, slabH, D]).at([0, H, D / 2]),
    "roof", "roof", [...walls, "block_core", "parapet", "vent_box", "pipe_0", "pipe_1"]);

  // Crown height includes the thin slab edge; the parapet is an open ring.
  const parapetH = crownH - slabH - capH;
  const ring = K.cut(
    K.box([W, parapetH, D]),
    K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]),
  );
  add("parapet", ring.at([0, H + slabH, D / 2]),
    "brick", "parapet", ["roof_slab"]);

  // A stepped SECTION, extruded along each wall; the cap bears on the ring.
  // cornice.projection is UNVERIFIED; keep the moulding shallow.
  const capProfile = K.profile.stepped([
    { w: T, h: capH / 2 }, { w: T + proud, h: capH / 2 },
  ]);
  const capY = H + crownH - capH;
  const capEnd = T + proud / 2;
  for (const [name, z] of [["front", T / 2], ["back", D - T / 2]]) {
    add(`coping_${name}`, K.extrude(capProfile, W + proud).rotY(90)
      .at([-(W + proud) / 2, capY, z]), "coping", "cornice",
    ["parapet", "coping_left", "coping_right"]);
  }
  for (const [name, x] of [["left", (W - T) / 2], ["right", -(W - T) / 2]]) {
    add(`coping_${name}`, K.extrude(capProfile, D - 2 * capEnd)
      .at([x, capY, capEnd]), "coping", "cornice", ["parapet"]);
  }

  for (const o of openings) {
    const surround = K.extrude(
      K.profile.rect({ w: o.w + 2 * frame, h: o.h + 2 * frame }),
      T + proud,
      { holes: [K.profile.rect({ w: o.w, h: o.h })
        .map(([x, y]) => [x, y + frame])] },
    ).at([o.x, o.y - frame, -proud]);
    add(`${o.id}_frame`, surround, "surround", o.role, ["wall_front", "block_core"]);
    // Glass fronts are behind the frame; their backs meet the solid interior.
    const glassFront = -proud + frame - seam;
    add(`${o.id}_glass`, K.box([o.w + 2 * seam, o.h + 2 * seam, T - glassFront])
      .at([o.x, o.y - seam, (T + glassFront) / 2]),
    "glass", o.role, [`${o.id}_frame`, "block_core"]);
    if (o.role === "window") {
      add(`${o.id}_sash`, K.box([o.w + 2 * seam, frame, frame])
        .at([o.x, o.y + (o.h - frame) / 2, -proud + frame / 2]),
      "trim", "window", [`${o.id}_frame`, `${o.id}_glass`]);
      add(`${o.id}_sill`, K.box([o.w + 4 * frame, frame, T / 2 + proud])
        .at([o.x, o.y - 2 * frame, (T / 2 - proud) / 2]),
      "surround", "sill", ["wall_front", `${o.id}_frame`]);
      parts[parts.length - 1].embed = true; // Sill tail seated inside the brick.
    }
  }

  // Four separate vertical bands: canopy, sign/AC, then P2's lower deck.
  const awningBottom = 0.163 * H, awningTop = 0.278 * H;
  const signTop = 0.368 * H, signH = 0.075 * H;
  const awningSpan = 0.904 * W;
  // MISSING KEY awning.centreX, awning.depth, signbox.w, signbox.centreX,
  // signbox.depth, ac.size, ac.position: provisional construction choices.
  const canopyX = 0.015 * W, canopyDepth = 0.12 * W;
  const seat = 0.008 * W;
  const awning = K.extrude(K.profile.wedge({
    w: canopyDepth + seat, h: awningTop - awningBottom,
    run: canopyDepth,
  }), awningSpan).rotY(-90)
    .at([canopyX + awningSpan / 2, awningBottom, -canopyDepth]);
  add("shop_awning", awning, "canopy", "awning", ["wall_front", "wall_left"]);
  const signW = 0.61 * W, signX = -0.115 * W, signD = 0.025 * W;
  add("shop_sign", K.box([signW, signH, signD])
    .at([signX, signTop - signH, -signD / 2]),
  "canopy", "signbox", ["wall_front"]);
  const acW = 0.20 * W, acH = signH, acD = 0.09 * W;
  const acX = signX + signW / 2 + acW / 2;
  add("shop_ac", K.box([acW, acH, acD])
    .at([acX, signTop - acH, -acD / 2]),
  "ac", "ac", ["wall_front", "shop_sign"]);
  // Recessed grille face, with a few broad slats readable at capture scale.
  for (let i = 0; i < 5; i += 1) {
    add(`ac_grille_${i}`, K.box([acW * 0.78, seat, seat])
      .at([acX, signTop - acH + acH * (0.16 + i * 0.15), -acD - seat / 2 + seam]),
    "iron", "ac", ["shop_ac"]);
  }

  const roofY = H + slabH;
  add("vent_box", K.box([0.20 * W, 0.055 * H, 0.20 * W])
    .at([-0.25 * W, roofY, 0.70 * D]), "fixture", "roof_fixture", ["roof_slab"]);
  const pipe = (radius, height) => {
    const section = K.profile.rect({ w: radius, h: height });
    // Move the kernel rectangle onto the nonnegative radial half-plane.
    for (const point of section) point[0] += radius / 2;
    return K.revolve(section, 16);
  };
  add("pipe_0", pipe(0.016 * W, 0.045 * H).at([0.31 * W, roofY, 0.37 * D]),
    "fixture", "roof_fixture", ["roof_slab"]);
  add("pipe_1", pipe(0.015 * W, 0.037 * H).at([0.31 * W, roofY, 0.24 * D]),
    "fixture", "roof_fixture", ["roof_slab"]);
  // P2 construction spec. Only the vertical offsets and roof-ladder location
  // are measured. MISSING KEY landing.span, landing.centreX, stair.run,
  // stair.width, ladder.roof.bottom, ladder.drop.position, ladder.drop.length.
  // landing.depth is UNVERIFIED: choose a 1.4 m deck with a rear walkway
  // and an open stairwell in the upper grate, not a plate across the flight.
  const bar = 0.06, deckD = 1.4, deckW = 5.5;
  const deckMin = -deckW / 2, deckMax = deckW / 2;
  const upperY = openings[0].y - frame - 0.072 * H;
  const lowerY = upperY - rowPitch;
  const axial = [];
  const iron = (id, solid, role, touches = [], axisAligned = true, embed = false) => {
    const part = { id, solid, zone: "iron", role, touches };
    if (embed) part.embed = true;
    parts.push(part);
    if (axisAligned) axial.push(part);
    return part;
  };
  const stairRun = 3.8, stairLoX = stairRun / 2, stairHiX = -stairRun / 2;
  const stairZ = -0.97, stairW = 0.72;
  const riseCount = 26, rise = rowPitch / riseCount, going = stairRun / riseCount;
  const angle = Math.atan2(stairRun, rowPitch) * 180 / Math.PI;
  const flightLength = Math.sqrt(stairRun * stairRun + rowPitch * rowPitch);
  // Sloping members have their local lower end at the origin. Rotate first,
  // then place; the lower/upper endpoints remain inside both deck extents.
  const slope = (y, z) => K.box([bar, flightLength, bar]).rotZ(angle)
    .at([stairLoX, y, z]);
  const dropX = -1.1, dropW = 0.58, dropZ = -deckD - bar / 4;
  const gateMin = dropX - dropW / 2 - 0.3 - bar;
  const gateMax = dropX + dropW / 2 + 0.3 + bar;

  for (const [level, top] of [["lower", lowerY], ["upper", upperY]]) {
    // Edge beams carry the individual grate bars. Only the grate bars have
    // role landing: each one runs back to the brick, including at the hatch.
    iron(`${level}_ledger`, K.box([deckW, bar, bar])
      .at([0, top - 2 * bar, -0.05]), "support");
    iron(`${level}_edge`, K.box([deckW, bar, bar])
      .at([0, top - 2 * bar, -deckD + 0.75 * bar]), "support");
    K.repeat(24, (deckW - bar) / 23, (i, offset) => {
      const x = deckMin + bar / 2 + offset;
      const hatch = level === "upper" && x > stairHiX + going / 2 && x < stairLoX + going;
      const depth = hatch ? 0.60 : deckD;
      iron(`${level}_grate_${i}`, K.box([bar, bar, depth + seam])
        .at([x, top - bar, (-depth + seam) / 2]), "landing", ["wall_front"]);
    });
    // Two full-depth cantilever bearers, one below each end of the grate.
    for (const [end, x] of [["right", deckMin + bar / 2], ["left", deckMax - bar / 2]]) {
      iron(`${level}_bearer_${end}`, K.box([bar, bar, deckD + seam])
        .at([x, top - 3 * bar, (-deckD + seam) / 2]), "support", ["wall_front"]);
      iron(`${level}_return_${end}`, K.box([bar, bar, deckD + seam])
        .at([x, top + 1 - bar, (-deckD + seam) / 2]), "railing", ["wall_front"]);
      K.repeat(2, deckD - bar, (i, offset) =>
        iron(`${level}_${end}_upright_${i}`, K.box([bar, 1, bar])
          .at([x, top - bar / 2, -bar / 2 - offset]), "baluster", [], true, true));
    }
    const rails = level === "lower" ? [[deckMin, gateMin], [gateMax, deckMax]] : [[deckMin, deckMax]];
    for (const [segment, [left, right]] of rails.entries()) {
      iron(`${level}_front_rail_${segment}`, K.box([right - left, bar, bar])
        .at([(left + right) / 2, top + 1 - bar, -deckD + bar / 2]), "railing");
      const count = Math.ceil((right - left) / 0.82);
      K.repeat(count, (right - left) / count, (i, offset) => {
        // End posts already belong to the returns; infill stays within each
        // separate rail segment, leaving the drop-ladder head entirely clear.
        const x = left + (right - left) / (2 * count) + offset;
        iron(`${level}_front_upright_${segment}_${i}`, K.box([bar, 1 + bar, bar])
          .at([x, top - 1.5 * bar, -deckD + bar / 2]), "baluster", [], true, true);
      });
    }
  }

  const stringIds = ["flight_string_back", "flight_string_front"];
  for (const [level, x, top] of [["lower", stairLoX, lowerY], ["upper", stairHiX, upperY]]) {
    iron(`${level}_threshold`, K.box([0.28, bar, stairW + bar])
      .at([x, top - bar, stairZ]), "support", [], true, true);
  }
  for (const [i, z] of [stairZ + stairW / 2, stairZ - stairW / 2].entries()) {
    iron(stringIds[i], slope(lowerY - bar, z), "stringer",
      ["lower_threshold", "upper_threshold", ...(i === 1
        ? ["lower_edge", "lower_front_rail_1", "lower_front_upright_1_2", "upper_edge"] : [])], false);
  }
  K.repeat(riseCount - 1, going, (i, offset) => {
    iron(`flight_step_${i}`, K.box([going + bar, bar, stairW + bar])
      .at([stairLoX - going - offset, lowerY + (i + 1) * rise - bar, stairZ]),
    "step", [...stringIds]);
  });
  iron("flight_handrail", slope(lowerY + 1 - bar, stairZ - stairW / 2),
    "railing", ["lower_front_rail_1", "upper_edge", "upper_front_rail_0", "upper_front_upright_0_1"], false);
  K.repeat(3, stairRun / 2, (i, offset) => {
    const x = stairLoX - offset;
    iron(`flight_upright_${i}`, K.box([bar, 1 + bar, bar])
      .at([x, lowerY - bar + i * rowPitch / 2, stairZ - stairW / 2]),
    "baluster", [stringIds[1], "flight_handrail"]);
  });

  // Drop ladder hangs outside the lower front edge. Its head ends at the
  // grate top; the split guard above it leaves a clear exit onto the deck.
  const dropBottom = lowerY - 0.16 * H;
  for (const [i, x] of [dropX - dropW / 2, dropX + dropW / 2].entries()) {
    iron(`drop_stile_${i}`, K.box([bar, lowerY - dropBottom, bar])
      .at([x, dropBottom, dropZ + seam]), "ladder", ["lower_edge"]);
  }
  const dropRungs = 8;
  K.repeat(dropRungs, (lowerY - dropBottom - 0.25) / dropRungs, (i, offset) =>
    iron(`drop_rung_${i}`, K.box([dropW, bar, bar])
      .at([dropX, dropBottom + 0.12 + offset, dropZ + seam]), "rung"));

  // Street-left is +x. This ladder lies in the SIDE plane, with foot space
  // between the rung line and brick, and no over-coping handholds.
  const roofLadderZ = 0.177 * W, roofLadderX = W / 2 + 0.20;
  const roofLadderTop = H + crownH - 0.037 * H;
  const roofLadderBottom = 0.21 * H, roofLadderW = 0.58;
  for (const [i, z] of [roofLadderZ - roofLadderW / 2, roofLadderZ + roofLadderW / 2].entries()) {
    iron(`roof_stile_${i}`, K.box([bar, roofLadderTop - roofLadderBottom, bar])
      .at([roofLadderX, roofLadderBottom, z]), "ladder");
    K.repeat(2, roofLadderTop - roofLadderBottom - 0.4, (j, offset) =>
      iron(`roof_mount_${i}_${j}`, K.box([0.20, bar, bar])
        .at([W / 2 + 0.10, roofLadderBottom + 0.18 + offset, z]),
      "support", ["wall_left"]));
  }
  const roofRungs = Math.ceil((roofLadderTop - roofLadderBottom - 0.3) / 0.34);
  K.repeat(roofRungs, (roofLadderTop - roofLadderBottom - 0.3) / (roofRungs - 1), (i, offset) =>
    iron(`roof_rung_${i}`, K.box([bar, bar, roofLadderW])
      .at([roofLadderX, roofLadderBottom + 0.12 + offset, roofLadderZ]), "rung"));

  // Axis-aligned iron members are boxes, so intersecting bounds are exact
  // contacts, including flush welds. Record those joints without fusing solids.
  // Sloping members have explicit contacts above; their AABBs are not solids.
  for (let i = 0; i < axial.length; i += 1) {
    const a = axial[i], ab = a.solid.aabb();
    for (let j = i + 1; j < axial.length; j += 1) {
      const b = axial[j], bb = b.solid.aabb();
      if ([0, 1, 2].every((axis) =>
        Math.min(ab.max[axis], bb.max[axis]) >= Math.max(ab.min[axis], bb.min[axis]) - 1e-9)) {
        if (!a.touches.includes(b.id)) a.touches.push(b.id);
        if (!b.touches.includes(a.id)) b.touches.push(a.id);
      }
    }
  }
  return parts;
}
