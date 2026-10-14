import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  front: "-Z",
  class: "building",
  seed: 1,
  shade: { ao: 0.08, upTint: 0.12, sideTint: -0.411 },
  palette: {
    brick: "#a85643",
    roof: "#918680",
    coping: "#a77b6f",
    frame: "#8b7e73",
    sill: "#be9589",
    glass: "#80a9ac",
    iron: "#887768",
    awning: "#538c54",
    signbox: "#668865",
    ac: "#c0c0bf",
    fixture: "#939395",
    brick_side: "#843b2e",
    iron_lower: "#887568",
    door: "#81acaf",
    storefront: "#85adb2",
  },
};

export function build() {
  const W = 6.274, H = 13.88;
  const D = 0.874 * W;
  const crownH = 0.031 * H;
  const T = 0.3, slabT = 0.08, capH = 0.12, seam = 0.00075;
  const parts = [];
  const add = (id, solid, zone, role, seatedIn) => {
    const part = { id, solid, zone, role };
    if (seatedIn) { part.touches = seatedIn; part.embed = true; }
    parts.push(part);
  };

  const frame = 0.09;
  const proud = 0.12;
  const openings = [];
  const paneW = 0.089 * W;
  const paneH = 0.12 * H;
  const headGap = 0.038 * H;
  const rowPitch = 0.283 * H;
  const bayX = [0.231, 0.808];

  {
    let placed = 0;
    for (let row = 0; row < 2; row += 1) {
      for (const [bay, fraction] of bayX.entries()) {
        if (placed >= 4) break;
        placed += 1;
        openings.push({
          id: `window_${bay}_${row}`,
          role: "window",
          x: -W / 2 + fraction * W,
          y: H - headGap - row * rowPitch - frame - paneH,
          w: paneW,
          h: paneH,
        });
      }
    }
  }

  openings.push({
    id: "storefront_0",
    role: "storefront",
    x: -W / 2 + 0.685 * W,
    y: 0.08 * H,
    w: 0.404 * W,
    h: 0.08 * H - 2 * frame,
  });
  openings.push({
    id: "door_0",
    role: "door",
    x: -W / 2 + 0.32 * W,
    y: frame,
    w: 0.125 * W,
    h: 0.127 * H - 2 * frame,
  });

  const openingTools = K.union(openings.map((o) => {
    const door = o.role === "door";
    return K.box([
      o.w + 2 * frame - 2 * seam,
      o.h + 2 * frame + (door ? 2 * seam : -2 * seam),
      T + 2 * proud,
    ]).at([o.x, o.y - frame + (door ? -seam : seam), T / 2]);
  }));

  const front = K.box([W - 2 * T, H, T]).at([0, 0, T / 2]);
  add("wall_front", K.cut(front, openingTools), "brick", "massing");
  add("wall_back", K.box([W - 2 * T, H, T]).at([0, 0, D - T / 2]), "brick", "massing");
  add("wall_left", K.box([T, H, D]).at([(W - T) / 2, 0, D / 2]), "brick", "massing");
  add("wall_right", K.box([T, H, D]).at([-(W - T) / 2, 0, D / 2]), "brick", "massing");
  add(
    "block_core",
    K.box([W - 2 * T + 2 * seam, H - slabT + seam, D - 2 * T + 2 * seam])
      .at([0, 0, D / 2]),
    "brick",
    "massing",
  );
  add(
    "roof_slab",
    K.box([W - 2 * T + 2 * seam, slabT, D - 2 * T + 2 * seam])
      .at([0, H - slabT, D / 2]),
    "roof",
    "roof",
  );

  const parapetH = crownH - capH;
  const ring = K.cut(
    K.box([W, parapetH + seam, D]),
    K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]),
  );
  add("parapet", ring.at([0, H - seam, D / 2]), "coping", "parapet");

  const cornice = 0.12;
  const capProfile = K.profile.stepped([
    { w: T, h: capH / 2 },
    { w: T + cornice, h: capH / 2 },
  ]);
  const capY = H + parapetH;
  const capEnd = T + cornice / 2;
  for (const [name, z] of [["front", T / 2], ["back", D - T / 2]]) {
    add(
      `coping_${name}`,
      K.extrude(capProfile, W + cornice).rotY(90)
        .at([-(W + cornice) / 2, capY, z]),
      "coping",
      "cornice",
    );
  }
  for (const [name, x] of [["left", (W - T) / 2], ["right", -(W - T) / 2]]) {
    add(
      `coping_${name}`,
      K.extrude(capProfile, D - 2 * capEnd).at([x, capY, capEnd]),
      "coping",
      "cornice",
    );
  }

  for (const o of openings) {
    const surround = K.extrude(
      K.profile.rect({ w: o.w + 2 * frame, h: o.h + 2 * frame }),
      T + proud,
      {
        holes: [
          K.profile.rect({ w: o.w, h: o.h })
            .map(([x, y]) => [x, y + frame]),
        ],
      },
    ).at([o.x, o.y - frame, -proud]);
    add(`${o.id}_frame`, surround, "frame", o.role);

    const glassFront = -proud + frame - seam;
    add(
      `${o.id}_glass`,
      K.box([o.w + 2 * seam, o.h + 2 * seam, T - glassFront])
        .at([o.x, o.y - seam, (T + glassFront) / 2]),
      "glass",
      o.role,
    );

    if (o.role !== "window") continue;
    add(
      `${o.id}_sash`,
      K.box([o.w + 2 * seam, frame, frame])
        .at([o.x, o.y + (o.h - frame) / 2, -proud + frame / 2]),
      "frame",
      "window",
    );
    add(
      `${o.id}_sill`,
      K.box([o.w + 4 * frame, frame, T / 2 + proud])
        .at([o.x, o.y - 2 * frame, (T / 2 - proud) / 2]),
      "sill",
      "sill",
      ["wall_front", `${o.id}_frame`],
    );
  }

  const awningBottom = 0.163 * H;
  const awningTop = 0.278 * H;
  const awningSpan = 0.904 * W;
  const awningX = -W / 2 + 0.515 * W;
  const canopyDepth = 0.9;
  const awningSeat = 0.06;
  const awningTouches = ["wall_front"];
  if (awningX + awningSpan / 2 > W / 2 - T) awningTouches.push("wall_left");
  if (awningX - awningSpan / 2 < -(W / 2 - T)) awningTouches.push("wall_right");
  add(
    "shop_awning",
    K.extrude(
      K.profile.wedge({
        w: canopyDepth + awningSeat,
        h: awningTop - awningBottom,
        run: canopyDepth,
      }),
      awningSpan,
    ).rotY(-90).at([awningX + awningSpan / 2, awningBottom, -canopyDepth]),
    "awning",
    "awning",
    awningTouches,
  );

  const signTop = 0.368 * H;
  const signH = 0.075 * H;
  const signX = -W / 2 + 0.522 * W;
  const signW = 0.913 * W;
  const signD = 0.19;
  add(
    "shop_sign_0",
    K.box([signW, signH, signD]).at([signX, signTop - signH, -signD / 2]),
    "signbox",
    "signbox",
  );

  const acW = 0.212 * W;
  const acD = 0.051 * W;
  const acH = 0.062 * H;
  const acTop = 0.34 * H;
  const acX = -W / 2 + 0.825 * W;
  const acBack = -signD + seam;
  const grille = 0.06;
  add(
    "shop_ac_0",
    K.box([acW, acH, acD]).at([acX, acTop - acH, acBack - acD / 2]),
    "ac",
    "ac",
  );
  for (let s = 0; s < 5; s += 1) {
    add(
      `ac_0_grille_${s}`,
      K.box([acW * 0.78, grille, grille])
        .at([acX, acTop - acH + acH * (0.16 + s * 0.15), acBack - acD - grille / 2 + seam]),
      "ac",
      "ac",
    );
  }

  const roofY = H - seam;
  add(
    "vent_0",
    K.box([0.2 * W, 0.055 * H, 0.2 * W])
      .at([-W / 2 + 0.25 * W, roofY, 0.7 * D]),
    "fixture",
    "roof_fixture",
  );
  const pipe = (radius, height) => {
    const section = K.profile.rect({ w: radius, h: height });
    for (const point of section) point[0] += radius / 2;
    return K.revolve(section, 8);
  };
  for (let i = 0; i < 2; i += 1) {
    add(
      `pipe_${i}`,
      pipe(0.016 * W, 0.045 * H * (1 - 0.18 * (i % 2)))
        .at([-W / 2 + 0.81 * W, roofY, (0.37 - 0.13 * i) * D]),
      "fixture",
      "roof_fixture",
    );
  }

  // The landing tops sit one measured landing.rowY below each row's sill.
  const upperY = H - headGap - 2 * frame - paneH - 0.072 * H;
  const lowerY = upperY - rowPitch;
  const landingX = -W / 2 + 0.627 * W;
  const landingSpan = 0.577 * W;
  const landingDepth = 1.25;
  const landingFrontZ = -landingDepth;

  // Build the arriving flight and drop ladder before the landings so their
  // gate widths are included in the landing railings.
  const flightParts = K.assemble.flight({
    bottom: [2.25, lowerY, landingFrontZ],
    top: [-0.65, upperY, landingFrontZ],
    width: 0.72,
    maxRise: 0.18,
    railHeight: 0.95,
    idPrefix: "escape_flight",
  });
  const dropLadder = K.assemble.ladder({
    base: [-0.65, 0, landingFrontZ],
    height: lowerY,
    width: 0.42,
    rungPitch: 0.28,
    face: "front",
    idPrefix: "drop_ladder",
  });

  parts.push(
    ...K.assemble.landing({
      span: landingSpan,
      depth: landingDepth,
      at: [landingX, upperY],
      wall: parts,
      railHeight: 1.0,
      gateFor: flightParts,
      idPrefix: "upper_landing",
    }),
  );
  parts.push(
    ...K.assemble.landing({
      span: landingSpan,
      depth: landingDepth,
      at: [landingX, lowerY],
      wall: parts,
      railHeight: 1.0,
      gateFor: [...flightParts, ...dropLadder],
      idPrefix: "lower_landing",
    }),
  );
  parts.push(...flightParts, ...dropLadder);

  // Roof access climbs the street-left side wall, behind the front corner.
  parts.push(
    ...K.assemble.ladder({
      base: [(W - T) / 2 + T / 2, 0, 0.177 * W],
      height: H + crownH - 0.037 * H,
      width: 0.42,
      rungPitch: 0.28,
      face: "side",
      idPrefix: "roof_ladder",
    }),
  );

  return parts;
}
