// M2 — the facade grammar derives openings, and an occluder blanks the tile it
// actually covers (08:G6). These are the two claims the grammar makes that a
// still frame cannot prove: "nine windows appeared without anyone placing one"
// and "the tenth did not, because a balcony is in front of it".
import { test } from "node:test";
import assert from "node:assert/strict";

import { compile } from "../src/compile/build.js";
import { validateSpec } from "../src/validate/index.js";
import { resolveRule, facadeCells } from "../src/compile/grammar.js";
import { loadSpec } from "./fixtures.mjs";

/** One 3-storey mass, three bays a floor, nothing else. */
function baseSpec() {
  return {
    schema: "pg/1",
    subject: "grammar_fixture",
    seed: 1,
    class: "building",
    palette: { wall: "#c7b7a3", glass: "#3d4a57", iron: "#3b3f4a" },
    parts: [
      { id: "mass", prim: "box", dims: [9.0, 9.6, 7.0], ground: true, role: "massing", zone: "wall" },
    ],
    facades: [
      {
        id: "fac",
        on: "mass",
        face: "+Z",
        occlude: true,
        split: { axis: "Y", rule: [["floor", 3.2, "*3"]] },
        tile: { floor: { axis: "X", rule: [["bay", 3.0, "*3"]] } },
        elements: { bay: { window: { dims: [1.4, 1.8], inset: 0.12, zone: "glass" } } },
      },
    ],
  };
}

const windowsOf = (solved) => solved.parts.filter((p) => p.role === "window");

test("resolveRule: fixed, repeated and fill entries", () => {
  const bands = resolveRule([["base", 3.4], ["floor", 3.2, "*2"], ["cornice", 0.6]], 10.4);
  assert.deepEqual(bands.map((b) => b.name), ["base", "floor", "floor", "cornice"]);
  assert.deepEqual(bands.map((b) => b.start), [0, 3.4, 6.6, 9.8]);

  const filled = resolveRule([["pier", 0.5], ["bay", "~"], ["bay", "~"], ["pier", 0.5]], 9);
  assert.deepEqual(filled.map((b) => b.size), [0.5, 4, 4, 0.5]);
});

test("facadeCells: 3 bands x 3 columns tiles the whole face", () => {
  const cells = facadeCells(baseSpec().facades[0], [9.0, 9.6, 7.0]);
  assert.equal(cells.length, 9);
  assert.equal(cells[0].id, "fac/floor1/bay1");
  assert.equal(cells[8].id, "fac/floor3/bay3");
  const area = cells.reduce((sum, c) => sum + (c.u1 - c.u0) * (c.v1 - c.v0), 0);
  assert.ok(Math.abs(area - 9.0 * 9.6) < 1e-9, `cells cover ${area} m2, face is ${9.0 * 9.6} m2`);
});

test("3 floors x 3 bays derives 9 windows, and the spec passes V0-V7 + V10", () => {
  const spec = baseSpec();
  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 9);
  for (const window of windowsOf(solved)) {
    assert.equal(window.contact, "socket");
    assert.equal(window.parentId, "mass");
  }

  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);
});

test("a balcony proud of the face occludes exactly its own tile: 8 windows", () => {
  const spec = baseSpec();
  // Bay 2 of floor 2: u centre 4.5 m of 9.0 -> 0.5; deck at v = 3.3 m of 9.6.
  spec.parts.push({
    id: "balcony",
    prim: "bevelBox",
    dims: [2.2, 0.16, 1.2],
    role: "balcony",
    zone: "iron",
    attach: { to: "mass", face: "+Z", uv: [0.5, 0.34375], contact: "flush", embed: 0.05, align: "bottom" },
  });

  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 8);

  const blanked = solved.tiles.filter((t) => t.occludedBy !== null);
  assert.equal(blanked.length, 1);
  assert.equal(blanked[0].id, "fac/floor2/bay2");
  assert.equal(blanked[0].occludedBy, "balcony");
  assert.equal(blanked[0].name, "wall");

  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);
});

test("a part merely flush with the face is not an occluder", () => {
  const spec = baseSpec();
  // Same z extent as the host: it hides nothing, so all 9 windows survive.
  spec.parts.push({
    id: "neighbour",
    prim: "box",
    dims: [4.0, 9.6, 7.0],
    role: "massing",
    zone: "wall",
    attach: { to: "mass", face: "+X", uv: [0.5, 0.0], contact: "flush", align: "bottom" },
  });
  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 9);
});

test("dsl/examples/facade-demo.json: 8 windows, one occluded tile, PASS", () => {
  const spec = loadSpec("dsl/examples/facade-demo.json");
  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 8);
  assert.equal(solved.tiles.filter((t) => t.occludedBy !== null).length, 1);
  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);
});

test("a thin proud strip (0.15 m) does not occlude", () => {
  const spec = baseSpec();
  // A 0.3 m wide downpipe 0.2 m deep, embedded 0.05 m, stands 0.15 m proud of
  // the face — under `occludeMinProud` (0.25 m), so it hides nothing even
  // though it runs the full height of bay 2 / floor 2.
  spec.parts.push({
    id: "downpipe",
    prim: "box",
    dims: [0.3, 3.2, 0.2],
    role: "trim",
    zone: "iron",
    attach: { to: "mass", face: "+Z", uv: [0.5, 0.34375], contact: "flush", embed: 0.05, align: "bottom" },
  });

  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 9);
  assert.equal(solved.tiles.filter((t) => t.occludedBy !== null).length, 0);
});

test("a 0.3 m proud box grazing the top 0.05 m of a tile does not occlude it", () => {
  const spec = baseSpec();
  // Floor 1 spans v 0 .. 3.2 m. This 0.05 m tall valance sits at v 3.15 .. 3.20,
  // i.e. only the top 0.05 m of the tile — inside `occludeEdgeMargin` (0.10 m),
  // so it misses floor1's inset rect (v 0.10 .. 3.10). It is also short of
  // floor2's inset rect (v 3.30 .. 6.30). It stands 0.35 - 0.05 = 0.30 m proud,
  // well over `occludeMinProud`: only the edge margin saves the tiles.
  spec.parts.push({
    id: "valance",
    prim: "box",
    dims: [1.0, 0.05, 0.35],
    role: "trim",
    zone: "iron",
    attach: { to: "mass", face: "+Z", uv: [0.5, 3.15 / 9.6], contact: "flush", embed: 0.05, align: "bottom" },
  });

  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 9);
  assert.equal(solved.tiles.filter((t) => t.occludedBy !== null).length, 0);
});

test("a landing standing 1.15 m proud inside a tile does occlude it", () => {
  const spec = baseSpec();
  // 3.0 m x 2.0 m across a 3.0 m x 3.2 m tile, well inside the edge margin.
  spec.parts.push({
    id: "landing",
    prim: "box",
    dims: [3.0, 2.0, 1.2],
    role: "balcony",
    zone: "iron",
    attach: { to: "mass", face: "+Z", uv: [0.5, 0.34375], contact: "flush", embed: 0.05, align: "bottom" },
  });

  const { solved } = compile(spec);
  assert.equal(windowsOf(solved).length, 8);
  const blanked = solved.tiles.filter((t) => t.occludedBy !== null);
  assert.equal(blanked.length, 1);
  assert.equal(blanked[0].id, "fac/floor2/bay2");
  assert.equal(blanked[0].occludedBy, "landing");
  assert.equal(blanked[0].name, "wall");
});

test("an awning above the storefront, inside the same tall band, does not blank it", () => {
  const spec = baseSpec();
  // The defect this rule exists for (subjects/tenement_block_llm,
  // fac_middle_front/shop1/front2): a 4 m ground band whose storefront tops out
  // at 2.8 m, so the metre above the glass is bare wall. An awning hung in that
  // bare metre reaches the tile's inset rect and used to blank the shopfront.
  spec.parts[0].dims = [9.0, 10.8, 7.0];
  spec.facades[0].split.rule = [["shop", 4.0], ["floor", 3.4, "*2"]];
  spec.facades[0].tile.shop = { axis: "X", rule: [["pier", 0.8], ["front", 7.4], ["pier", 0.8]] };
  spec.facades[0].elements.front = { storefront: { dims: [6.0, 2.8], inset: 0.14, zone: "glass" } };
  // Canopy 1.5 m proud spanning v 3.1 .. 3.9 — above the glass (v 0 .. 2.8),
  // still inside the tile (v 0 .. 4) and inside its 0.10 m edge margin.
  spec.parts.push({
    id: "awning",
    prim: "wedge",
    dims: [6.4, 0.8, 1.55],
    role: "awning",
    zone: "iron",
    attach: { to: "mass", face: "+Z", uv: [0.5, 3.1 / 10.8], contact: "flush", embed: 0.05, align: "bottom" },
  });

  const { solved } = compile(spec);
  const front = solved.tiles.find((t) => t.id === "fac/shop1/front2");
  assert.equal(front.occludedBy, null, "the awning hangs above the glass, not over it");
  assert.equal(solved.parts.filter((p) => p.grammar?.element === "storefront").length, 1);
  // The bays two bands up are untouched as well: the canopy stops at v 3.9.
  assert.equal(solved.tiles.filter((t) => t.occludedBy !== null).length, 0);
});

test("a tile whose region names no element is never blanked", () => {
  const spec = baseSpec();
  // The same landing that blanks a bay leaves a `pier` alone — there is no
  // glass behind it to hide.
  spec.facades[0].tile.floor = { axis: "X", rule: [["pier", 3.0], ["bay", 3.0], ["pier", 3.0]] };
  spec.parts.push({
    id: "landing",
    prim: "box",
    dims: [3.0, 2.0, 1.2],
    role: "balcony",
    zone: "iron",
    attach: { to: "mass", face: "+Z", uv: [1.5 / 9.0, 0.34375], contact: "flush", embed: 0.05, align: "bottom" },
  });

  const { solved } = compile(spec);
  assert.equal(solved.tiles.filter((t) => t.occludedBy !== null).length, 0);
  assert.equal(windowsOf(solved).length, 3);
});
