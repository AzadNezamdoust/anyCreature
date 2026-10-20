import * as K from "../../src/kernel/index.mjs";

export const meta = {
  front: "-Z",
  class: "building",
  seed: 1,
  shade: { ao: 0.08, upTint: 0.12, sideTint: -0.43 },
  palette: {
    brick: "#b5412f", trim: "#5a2a22", glass: "#8fc1d6", iron: "#2b2e33",
    roof: "#88817c", fixture: "#999f9d",
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
  const T = 0.04 * W, slabH = 0.006 * H;
  const parts = [];
  const add = (id, solid, zone, role, touches) =>
    parts.push({ id, solid, zone, role, touches });

  // Four enclosing walls, with side walls running the entire depth.
  // A separate solid core supplies continuous bearing below the roof.
  const walls = ["wall_front", "wall_back", "wall_left", "wall_right"];
  add("wall_front", K.box([W - 2 * T, H, T]).at([0, 0, T / 2]),
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
  const parapetH = crownH - slabH;
  const ring = K.cut(
    K.box([W, parapetH, D]),
    K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]),
  );
  add("parapet", ring.at([0, H + slabH, D / 2]),
    "brick", "parapet", ["roof_slab"]);

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
