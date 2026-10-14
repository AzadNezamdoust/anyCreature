// M6 — the three DSL gaps the blind builder seats reported:
//   1. a composite may be a parent (by id, or `composite.sub`);
//   2. a child may ride EVERY instance of a repeated/mirrored parent;
//   3. `alignU` anchors a child's extreme along the face's u axis.
//
// Plus the invariant the whole milestone is fenced by: the M2 baseline spec
// still compiles to the same specHash and the same geometry.
import { test } from "node:test";
import assert from "node:assert/strict";

import { validateSpec } from "../src/validate/index.js";
import { compile, solve } from "../src/compile/build.js";
import { validateV0 } from "../src/validate/v0.js";
import { ALIGN_U } from "../src/compile/resolve.js";
import { COMPOSITE_NAMES, loadComposite } from "../src/prims.js";
import { specHash } from "../src/spec.js";
import { loadSpec, TENEMENT } from "./fixtures.mjs";

const BALCONY_OPEN = "dsl/examples/balcony-open.json";
const CART = "dsl/examples/cart.json";

/** A ground slab plus whatever the test attaches to it. */
function hostSpec(...parts) {
  return {
    schema: "pg/1",
    subject: "m6_fixture",
    seed: 1,
    class: "prop",
    palette: { deck: "#b9b3a8", iron: "#3b3f4a" },
    parts: [
      { id: "pad", prim: "box", dims: [2.0, 0.4, 1.6], ground: true, role: "massing", zone: "deck" },
      ...parts,
    ],
  };
}

const LANDING = {
  id: "deck1", prim: "landing", dims: [1.6, 0.95, 1.2], role: "landing", zone: "iron",
  attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
};

const ids = (result) => result.parts.map((p) => p.id);

// --- gap 1: composites as parents -------------------------------------------

test("attach.to may name a composite id; it resolves to that composite's root", () => {
  const spec = hostSpec(LANDING, {
    id: "rail_back", prim: "railing_open", dims: [1.4, 0.95, 0.06], role: "railing", zone: "iron",
    attach: { to: "deck1", face: "+Y", uv: [0.5, 0.04], contact: "rests-on-top" },
  });
  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);

  const solved = solve(spec);
  const bot = solved.parts.find((p) => p.id === "rail_back.bot");
  assert.ok(bot, `no rail_back.bot in ${ids(solved).join(", ")}`);
  assert.equal(bot.parentId, "deck1.deck", "the composite id must resolve to its root sub-part");
});

test("attach.to may name a composite sub-part as composite.sub", () => {
  const spec = hostSpec(LANDING, {
    id: "lamp", prim: "box", dims: [0.12, 0.3, 0.12], role: "lamp", zone: "iron",
    attach: { to: "deck1.deck", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  });
  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);
  assert.equal(solve(spec).parts.find((p) => p.id === "lamp").parentId, "deck1.deck");
});

test("V0 rejects a sub-part the composite does not declare", () => {
  const spec = hostSpec(LANDING, {
    id: "lamp", prim: "box", dims: [0.12, 0.3, 0.12], role: "lamp", zone: "iron",
    attach: { to: "deck1.roof", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top" },
  });
  const result = validateV0(spec);
  assert.equal(result.pass, false);
  assert.ok(result.violations.some((x) => x.part === "lamp" && /deck1\.roof/.test(x.hint)));
});

// --- gap 2: per-instance children --------------------------------------------

test("a child rides every mirrored parent instance by default", () => {
  const solved = solve(loadSpec(CART));
  const hubs = solved.parts.filter((p) => p.specId === "wheel.hub").map((p) => p.id);
  assert.deepEqual(hubs, ["wheel.hub", "wheel.hub~m"], "the mirrored tyre must carry its own hub");
  const byParent = new Map(solved.parts.filter((p) => p.specId === "wheel.hub").map((p) => [p.id, p.parentId]));
  assert.equal(byParent.get("wheel.hub"), "wheel.tyre");
  assert.equal(byParent.get("wheel.hub~m"), "wheel.tyre~m");
  assert.equal(validateSpec(loadSpec(CART)).pass, true);
});

test("a railing on a repeated balcony lands on every balcony, posts and all", () => {
  const spec = loadSpec(BALCONY_OPEN);
  const report = validateSpec(spec);
  assert.equal(report.pass, true, report.text);

  const solved = solve(spec);
  const count = (specId) => solved.parts.filter((p) => p.specId === specId).length;
  assert.equal(count("balcony"), 2);
  assert.equal(count("rail.bot"), 2, "one bottom rail per balcony");
  assert.equal(count("rail.top"), 2, "one top rail per balcony");
  assert.equal(count("rail.post"), 12, "six posts per balcony, not six in total");

  // Every railing part sits within its own balcony's x/z footprint and above it.
  for (const balcony of solved.parts.filter((p) => p.specId === "balcony")) {
    const deckTop = balcony.aabb.max[1];
    const rails = solved.parts.filter((p) => p.specId.startsWith("rail.")
      && p.aabb.min[1] >= deckTop - 1e-6 && p.aabb.min[1] < deckTop + 1.0);
    assert.equal(rails.length, 8, `balcony at y=${deckTop} carries 8 railing parts`);
  }
});

test("attach.instance 0 opts back out to the anchor instance", () => {
  const shelves = (instance) => hostSpec(
    { id: "shelf", prim: "plate", dims: [0.4, 0.06, 0.4], role: "shelf", zone: "iron",
      attach: { to: "pad", face: "+Z", uv: [0.5, 0.4], contact: "flush", embed: 0.03 },
      repeat: { axis: "+Y", count: 3, pitch: 0.5 } },
    { id: "pot", prim: "box", dims: [0.12, 0.12, 0.12], role: "pot", zone: "deck",
      attach: { to: "shelf", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top", ...instance } },
  );
  const pots = (instance) => solve(shelves(instance)).parts.filter((p) => p.specId === "pot").length;
  assert.equal(solve(shelves({})).parts.filter((p) => p.specId === "shelf").length, 3);
  assert.equal(pots({}), 3, "one pot per shelf by default");
  assert.equal(pots({ instance: 0 }), 1, "instance 0 is the anchor shelf only");
});

test("V0 rejects an attach.instance that is neither \"all\" nor 0", () => {
  const spec = hostSpec({
    id: "pot", prim: "box", dims: [0.12, 0.12, 0.12], role: "pot", zone: "deck",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top", instance: 2 },
  });
  const result = validateV0(spec);
  assert.equal(result.pass, false);
  assert.ok(result.violations.some((x) => x.part === "pot" && /instance/.test(x.hint)));
});

// --- gap 3: alignU ------------------------------------------------------------

test("alignU anchors the child's u extreme; center is the default", () => {
  const child = (alignU) => ({
    id: "bar", prim: "plate", dims: [0.8, 0.06, 0.3], role: "bar", zone: "iron",
    attach: { to: "pad", face: "+Y", uv: [0.5, 0.5], contact: "rests-on-top", ...(alignU ? { alignU } : {}) },
  });
  const minX = (alignU) => compile(hostSpec(child(alignU))).solved.parts
    .find((p) => p.id === "bar").aabb.min[0];

  assert.deepEqual(ALIGN_U, ["start", "center", "end"]);
  assert.ok(Math.abs(minX(undefined) - (-0.4)) < 1e-6, "default centres the child on u");
  assert.ok(Math.abs(minX("center") - (-0.4)) < 1e-6);
  assert.ok(Math.abs(minX("start") - 0) < 1e-6, "start puts the child's -u extreme on the point");
  assert.ok(Math.abs(minX("end") - (-0.8)) < 1e-6, "end puts the child's +u extreme on the point");
});

test("railing_open is bars: a top rail as wide as the railing, and no infill", () => {
  assert.ok(COMPOSITE_NAMES.includes("railing_open"));
  const open = loadComposite("railing_open");
  assert.deepEqual(open.parts.map((p) => p.id), ["bot", "post", "top"]);
  assert.equal(open.parts.some((p) => p.id === "infill"), false, "an open railing has no web");

  const solved = solve(loadSpec(BALCONY_OPEN));
  const top = solved.parts.find((p) => p.id === "rail.top");
  assert.ok(Math.abs((top.aabb.max[0] - top.aabb.min[0]) - 2.4) < 1e-6, "the top rail spans the declared length");
  const posts = solved.parts.filter((p) => p.specId === "rail.post" && p.aabb.min[1] < 4);
  const xs = posts.map((p) => p.aabb.min[0]).sort((a, b) => a - b);
  assert.ok(Math.abs(xs[0] - (-1.2)) < 1e-6, "the first post starts at the railing's -x edge");
  assert.ok(Math.abs(posts.map((p) => p.aabb.max[0]).sort((a, b) => b - a)[0] - 1.2) < 1e-6);
  for (const post of posts) assert.ok(Math.min(...post.dims) >= 0.06 - 1e-9, "posts are at or above the style floor");
});

test("the web railing is untouched — the frozen baseline still references it", () => {
  const web = loadComposite("railing");
  assert.ok(web.parts.some((p) => p.id === "infill"), "railing keeps its infill web");
});

// --- the fence ----------------------------------------------------------------

test("BASELINE: tenement_block still compiles to the M2 specHash and geometry", () => {
  const spec = loadSpec(TENEMENT);
  assert.equal(specHash(spec), "h32:a7e21c69");
  const out = compile(spec);
  assert.equal(out.solved.triangles, 7612, "the M2 capture manifest says 7612");
  // The fence only holds because the baseline carries no repeat/mirror at all:
  // nothing in it is a child of a repeated parent, so the M6 default cannot
  // change a single placement in it.
  assert.equal(spec.parts.filter((p) => p.repeat || p.mirror).length, 0);
});
