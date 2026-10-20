import * as K from "../../../src/kernel/index.mjs";

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
    tread: "#3f3f3d",
    body_front: "#8ab8d9",
  },
};

export function build() {
  const parts = K.assemble.vehicleBody({
    W: 1.978, H: 2.621,
    side: [[2.4, 1.549], [0.83, 1.659], [0.557, 2.621], [-0.408, 2.621], [-0.408, 1.614], [-2.4, 1.614], [-2.4, 0.608], [1.514, 0.608], [1.514, 0.963], [2.4, 0.963]],
    section: [[-0.989, 0], [0.989, 0], [0.989, 1.748], [0.922, 2.621], [-0.922, 2.621], [-0.989, 1.748]],
    plan: [[-0.989, 2.4], [0.989, 2.4], [0.989, -2.4], [-0.989, -2.4]],
    cab: [-0.408, 0.83],
    bed: { z: [-2.4, -0.451], wallTop: 1.614 },
    sill: 0.608, clearance: 0.3,
    wheels: { r: 0.4752, width: 0.3, z: [1.454, -1.536] },
    arches: [{ z: 1.514, halfLength: 0.54, rise: 0.556, n: 3.5 }, { z: -1.5, halfLength: 0.528, rise: 0.514, n: 3.5 }],
    bumpers: [{ face: "nose", top: 0.964, h: 0.265, depth: 0.06, out: 0.04, wrap: 0.2 },
      { face: "tail", top: 0.823, h: 0.398, depth: 0.235, out: -0.047 }],
    zones: { liner: "grille" },
  });
  const cab = parts.find((p) => p.id === "cab");

  parts.push(...K.assemble.pane({ host: cab, face: "+z", poly: [[-0.856, 1.659], [0.856, 1.659], [0.802, 2.369], [-0.802, 2.369]], idPrefix: "windshield" }));

  for (const face of ["+x", "-x"]) parts.push(...K.assemble.pane({ host: cab, face, poly: [[-0.077, 1.748], [0.682, 1.748], [0.486, 2.438], [-0.077, 2.438]], idPrefix: `side_${face[0] === "+" ? "l" : "r"}` }));

  for (const face of ["+x", "-x"]) parts.push(...K.assemble.seam({ host: cab, face, closed: true, path: [[-0.278, 0.702], [0.780, 0.702], [0.780, 1.748], [0.553, 2.550], [-0.278, 2.550]], idPrefix: `door_${face[0] === "+" ? "l" : "r"}` }));

  for (const face of ["+x", "-x"]) parts.push(...K.assemble.handle({ host: cab, face, bounds: K.span({ z: [-0.204, 0.022], y: [1.449, 1.512] }), idPrefix: `handle_${face[0] === "+" ? "l" : "r"}` }));

  parts.push(...K.assemble.lamp({ body: parts, face: "nose", centre: [0.752, 1.266], diameter: 0.283 }));

  parts.push(...K.assemble.grille({ body: parts, face: "nose", bounds: K.span({ x: [-0.448, 0.448], y: [1.117, 1.415] }), slots: 2 }));

  parts.push(...K.assemble.mirror({ body: parts, side: 0.989, centreY: 1.803, z: 0.722, head: { w: 0.249, h: 0.398 }, arm: 0.097 }));

  return parts;
}
