import * as K from "../../src/kernel/index.mjs";

export const meta = {
  front: "-Z",
  class: "building",
  seed: 1,
  shade: { ao: 0.08, upTint: 0.12, sideTint: -0.43 },
  palette: {
    brick: "#b5412f", trim: "#5a2a22", glass: "#80a9ac", iron: "#2b2e33",
    roof: "#88817c", fixture: "#999f9d", ac: "#c0c0bf",
    coping: "#bc8c7e", surround: "#ad8067", canopy: "#528b50",
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
  add("block_core", K.box([W - 2 * T, H, D - 2 * T]).at([0, 0, D / 2]),
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
  return parts;
}
