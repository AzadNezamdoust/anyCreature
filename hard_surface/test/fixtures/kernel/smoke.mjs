// SMOKE MODULE - not the façade. S1 proves the kernel round-trips through node
// AND vite; Astra writes the real brick façade from P0 (V2-TEST-PLAN 6, S4).
// Everything here is the V2-TEST-PLAN 2 mini-example plus one iron bar, so a
// green capture means box + arch cut + offset reveal + a touching solid all
// survive the path solid -> MeshGL -> paint -> merge -> one draw call.
import * as K from "../../../src/kernel/index.mjs";

export const meta = {
  front: "-Z", census: false,   // frozen S1 smoke for the test suite (live subject is authored by Astra)
  class: "building",
  seed: 1,
  palette: { brick: "#b5412f", frame: "#5a2a22", glass: "#8fc1d6", iron: "#2b2e33" },
};

export function build() {
  const W = 8.0, H = 11.0, T = 0.35;                       // wall width, height, thickness (m)
  const parts = [];

  let wall = K.box([W, H, T]);                             // local: x centred, y 0..H, z -T/2..T/2
  const door = K.profile.arch({ w: 1.2, h: 2.4, rise: 0.6, segs: 12 });   // rect + half-round head
  wall = K.cut(wall, K.extrude(door, T + 0.02).at([2.6, 0, -T / 2 - 0.01]));  // through opening
  const reveal = K.extrude(K.profile.offset(door, 0.12), 0.25).at([2.6, 0, T / 2 - 0.25]);
  wall = K.cut(wall, reveal);                              // 12 cm stepped reveal, 25 cm deep
  parts.push({ id: "wall_front", solid: wall, zone: "brick", role: "massing" });

  // S2 DEVIATION, one number: the V2-TEST-PLAN §2 example (and the README copy
  // of it) makes this leaf 0.05 m thick, which is below the 0.06 m building
  // style floor the S2 V5 row measures on every part's AABB — the example
  // cannot pass its own gate. 0.06 m here, so the smoke PASSes the chain.
  // OWNER/FABLE QUESTION: does MIN_FEAT apply to a door leaf, or should the §2
  // example be restated at 0.06? Nothing else in the module moved.
  parts.push({
    id: "door_leaf",
    solid: K.extrude(door, 0.06).at([2.6, 0, -T / 2 + 0.02]),
    zone: "frame",
    role: "door",
    touches: ["wall_front"],
  });

  // One bar of the smallest section the kernel allows, stood against the front
  // face: the ironwork case in miniature (V2-TEST-PLAN 1, feature 5).
  parts.push({
    id: "bar_0",
    solid: K.box([0.06, 3, 0.06]).at([3.5, 0, T / 2 + 0.03]),
    zone: "iron",
    role: "baluster",
    touches: ["wall_front"],
  });

  return parts;
}
