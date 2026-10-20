// WF v8 WP4 — merge.mjs: one frozen fixture per rule (research/v7/WF-V8-PLAN.md "Merge"; WF-REVIEW-opus.md C6).
// Pure rules on test/fixtures/wf-v8-merge (a critique pair, a state.json, a frozen key table) and synthetic rasters; one
// integration test replays the school_bus round-3 "near-black arch" item on the committed round-3 model (read-only,
// writes nothing).
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  CLASS_ORDER, MERGE_RULES, areaLinks, checkCritique, claimTest, classifyItems, dirOf, driftHit, familyOf, keyTable, knobAxis, loadSchema,
  minimalState, namesFamily, overridesFor, parseKey, renderMarkdown, runMerge, sameWant, stopLine, validateSchema, worksheetOrder,
} from "../scripts/v7/merge.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIX = path.join(HERE, "fixtures", "wf-v8-merge");
const ROOT = path.resolve(HERE, "..");
const read = (f) => JSON.parse(fs.readFileSync(path.join(FIX, f), "utf8"));
const fable = read("r2-fable.json");
const opus = read("r2-opus.json");
const state = read("state.json");
const keys = new Map(Object.entries(read("keys.json")).filter(([k]) => !k.startsWith("_")).map(([k, v]) => [k, { key: k, path: v.name.split("."), ...v }]));
// the frozen evidence results (claimTest output shape) of the items with `at`
const EV = {
  fable: { 0: { ok: true, image: "concept", text: "concept ref-only 40.0 %" }, 3: { ok: false, image: "side", text: "side colour: the same family" }, 7: { ok: true, image: "concept", text: "concept edge: 12 px differ" } },
  opus: { 3: { ok: true, image: "side", text: "side model-only 30.0 %" }, 8: { ok: true, image: "side", text: "side edge: 3 px differ" } },
};
const evidence = Object.fromEntries(["fable", "opus"].map((s) => [s, [...Array(10).keys()].map((i) => EV[s][i] ?? null)]));
const DRIFT = { concept: [{ id: "D1", rect: [25, 25, 45, 45], decides: "concept", why: "flank drawn inboard" }] };
const merged = () => classifyItems({ critiques: { fable, opus }, evidence, keys, drift: DRIFT, state, round: 2 });
const find = (items, key, cls) => items.filter((it) => it.key === key && (!cls || it.class === cls));

test("rule 1 schema: the fixtures validate; done:false, a bad key, a missing field, a wrong seat are errors; > 10 items only warns", () => {
  const schema = loadSchema();
  assert.deepEqual(checkCritique(fable, { subject: "fixture", round: 2, seat: "fable" }, schema), { errors: [], warnings: [] });
  assert.deepEqual(checkCritique(opus, { subject: "fixture", round: 2, seat: "opus" }, schema).errors, []);
  const partial = { ...fable, done: false, items: fable.items.slice(0, 3) };
  assert.match(checkCritique(partial, { seat: "fable" }, schema).errors.join(), /done:false \(3 items written so far: resume the fable critic\)/);
  const badKey = { ...fable, items: [{ ...fable.items[0], key: "part:mirror.width" }] };
  assert.match(checkCritique(badKey, {}, schema).errors.join(), /\/items\/0\/key: "part:mirror.width" does not match/);
  const { note, ...noNote } = fable.items[1];
  assert.match(checkCritique({ ...fable, items: [noNote] }, {}, schema).errors.join(), /\/items\/0\/note: required/);
  assert.match(checkCritique(fable, { seat: "opus" }, schema).errors.join(), /seat "fable" is not opus/);
  const eleven = { ...fable, items: [...fable.items, fable.items[1]] };
  const r = checkCritique(eleven, {}, schema);
  assert.deepEqual(r.errors, []);
  assert.match(r.warnings.join(), /11 items > 10/);
  assert.equal(validateSchema({ a: 1 }, { type: "object", additionalProperties: false, properties: {} })[0].keyword, "additionalProperties");
  assert.equal(validateSchema(3, { type: "number" }).length, 0);
  assert.equal(validateSchema(3.5, { type: "integer" })[0].keyword, "type");
});

test("rule 1 schema: runMerge is blocked (nothing written) on a missing seat file and on done:false", async () => {
  const dir = path.join(FIX, "blocked");
  const module = path.join(ROOT, "out", "ref", "gold", "school_bus", "model-v21.mjs");
  const r = await runMerge({ subject: "school_bus", round: 3, dir, module, write: false, variants: false });
  assert.equal(r.ok, false);
  assert.deepEqual(r.blocked, [
    "critique/r3-fable.json: done:false (1 items written so far: resume the fable critic)",
    "critique/r3-opus.json: missing (run the opus critic)",
  ]);
  assert.equal(fs.existsSync(path.join(dir, "state.json")), false);
  assert.equal(fs.existsSync(path.join(dir, "critique", "r3-merged.json")), false);
});

/** A w x h raster: ref / model fg + family from functions of (x, y). */
function raster(w, h, { ref, model, refFam = () => 1, modelFam = () => 1, care = null }) {
  const R = { w, h, refFg: new Uint8Array(w * h), modelFg: new Uint8Array(w * h), refFam: new Uint8Array(w * h), modelFam: new Uint8Array(w * h), care: null, names: ["bg", "body", "tyre", "orange", "other"] };
  if (care) R.care = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) {
    const i = y * w + x;
    if (ref(x, y)) { R.refFg[i] = 1; R.refFam[i] = refFam(x, y); }
    if (model(x, y)) { R.modelFg[i] = 1; R.modelFam[i] = modelFam(x, y); }
    if (care) R.care[i] = care(x, y) ? 1 : 0;
  }
  return R;
}

test("rule 2 evidence: ref-only / model-only need 10 % of the rect's px, colour a different family (and now / want's), edge 1 px", () => {
  // reference 10 x 10 square, model the same minus a 4-column strip on the right (x 6..9): 40 ref-only px of 100
  const R = raster(10, 10, { ref: () => true, model: (x) => x < 6 });
  assert.equal(claimTest(R, [0, 0, 10, 10], "ref-only").ok, true);
  assert.match(claimTest(R, [0, 0, 10, 10], "ref-only").text, /ref-only 40\.0 % of 100 px/);
  assert.equal(claimTest(R, [0, 0, 6, 10], "ref-only").ok, false);          // no difference inside
  assert.equal(claimTest(R, [0, 0, 10, 10], "model-only").ok, false);
  const thin = raster(20, 10, { ref: () => true, model: (x) => x < 19 });   // 10 ref-only px of 200 = 5 %
  assert.equal(claimTest(thin, [0, 0, 20, 10], "ref-only").ok, false);
  assert.equal(claimTest(thin, [0, 0, 20, 10], "ref-only", 0.05).ok, true);
  assert.equal(claimTest(raster(20, 10, { ref: () => true, model: (x) => x < 18 }), [0, 0, 20, 10], "ref-only").ok, true);   // exactly 10 %
  // colour: the reference is tyre (2) in rows 5+, the model body (1) above row 7 and orange (3) below
  const C = raster(10, 10, { ref: () => true, model: () => true, refFam: (x, y) => (y >= 3 ? 2 : 1), modelFam: (x, y) => (y >= 7 ? 3 : 1) });
  const c = claimTest(C, [0, 0, 10, 10], "colour");
  assert.equal(c.ok, true);                                                  // tyre 70 % vs body 70 %: different families
  assert.deepEqual([c.ref, c.model], [{ family: "tyre", share: 0.7 }, { family: "body", share: 0.7 }]);
  // ... but the claim's halves: now = orange (3) is not what the model shows there (body) -> fails, with the reason
  const halves = claimTest(C, [0, 0, 10, 10], "colour", 0.15, { ref: 2, model: 3 });
  assert.equal(halves.ok, false);
  assert.match(halves.text, /the model does not show now's family \(orange\)/);
  assert.equal(claimTest(C, [0, 7, 10, 10], "colour", 0.15, { ref: 2, model: 3 }).ok, true);   // lower rows: tyre vs orange
  assert.equal(claimTest(C, [0, 0, 10, 3], "colour").ok, false);            // body in both
  // edge: >= 1 px differs (silhouette or family)
  assert.equal(claimTest(C, [0, 0, 10, 3], "edge").ok, false);
  assert.equal(claimTest(C, [0, 2, 10, 4], "edge").ok, true);
  assert.match(claimTest(R, [20, 20, 30, 30], "edge").text, /outside the 10x10 image/);
  // don't-care px (concept OCCLUDED) are neither counted nor differences
  const D = raster(10, 10, { ref: () => true, model: (x) => x < 6, care: (x) => x < 6 });
  assert.equal(claimTest(D, [0, 0, 10, 10], "ref-only").ok, false);
  assert.equal(claimTest(D, [0, 0, 10, 10], "ref-only").px, 60);
});

test("rule 2 evidence: a WEAK edge / colour at (< 10 % of the rect AND < edgeMinPx) passes but a MAJOR merges as MINOR", () => {
  // a 100 x 100 rect whose reference and model differ in one 5-px column strip of 20 rows: 100 px = 1 % of 10000 px
  const R = raster(100, 100, { ref: () => true, model: (x, y) => !(x < 5 && y < 20) });
  const e = claimTest(R, [0, 0, 100, 100], "edge");
  assert.equal(e.ok, true);
  assert.equal(e.weak, true);
  assert.match(e.text, /weak: 1\.0 % of the rect < 10\.0 % and 100 px < 250 px/);
  assert.equal(claimTest(R, [0, 0, 100, 100], "edge", 0.10, {}, 100).weak, false);   // >= the px bar
  assert.equal(claimTest(R, [0, 0, 20, 20], "edge").weak, false);                   // 100 of 400 px = 25 %
  // colour: the families differ only in a thin band (the modal family still differs: ok, but weak)
  const C = raster(100, 100, { ref: () => true, model: () => true, refFam: () => 2, modelFam: (x, y) => (y < 2 ? 2 : 1) });
  assert.equal(claimTest(C, [0, 0, 100, 100], "colour").weak, false);                // 9800 px differ
  const C2 = raster(100, 100, { ref: () => true, model: () => true, refFam: (x, y) => (y < 2 ? 2 : 1), modelFam: () => 1 });
  const c2 = claimTest(C2, [0, 96, 100, 100], "colour");
  assert.equal(c2.ok, false);                                                        // body in both there
  // classification: one seat, MAJOR with a weak at -> C (unverified); strong -> B
  const item = (claim) => ({ sev: "MAJOR", key: "knob:W", now: 1, want: 1.2, unit: "m", views: ["side"], basis: "side", at: { image: "side", rect: [0, 0, 100, 100], claim }, evidence: [], note: "" });
  const crit = (it) => ({ subject: "t", round: 1, seat: "fable", done: true, items: [it] });
  const weak = classifyItems({ critiques: { fable: crit(item("edge")), opus: { ...crit(item("edge")), seat: "opus", items: [] } }, evidence: { fable: { 0: { ...e, image: "side" } } } });
  assert.equal(weak.items[0].class, "C");
  assert.equal(weak.items[0].sev, "MINOR");
  assert.match(weak.items[0].reason, /MAJOR with a weak at/);
  const strong = classifyItems({ critiques: { fable: crit(item("edge")), opus: { ...crit(item("edge")), seat: "opus", items: [] } }, evidence: { fable: { 0: { ...e, weak: false, image: "side" } } } });
  assert.equal(strong.items[0].class, "B");
});

test("rule 2 evidence: a failed at is REJECTED with its numbers; a MAJOR without at is merged as MINOR", () => {
  const { items } = merged();
  const rej = find(items, "part:arch.colour");
  assert.equal(rej.length, 1);
  assert.equal(rej[0].class, "REJECTED");
  assert.match(rej[0].reason, /evidence failed: side colour: the same family/);
  const roof = find(items, "part:roof.pos.y")[0];
  assert.equal(roof.class, "C");
  assert.equal(roof.sev, "MINOR");
  assert.deepEqual(roof.demoted, ["fable"]);
  assert.match(roof.reason, /MAJOR without a verified at -> merged as MINOR/);
});

test("rule 3 drift: an at >= 50 % inside a drift rect whose decides differs from the basis is REJECTED-DRIFT", () => {
  const { items } = merged();
  const d = find(items, "knob:paneZ")[0];
  assert.equal(d.class, "REJECTED-DRIFT");
  assert.match(d.reason, /at inside drift D1 \(100\.0 %; decides concept, the item's basis is side\)/);
  assert.equal(driftHit(DRIFT, { image: "concept", rect: [40, 40, 50, 50] }), null);            // 25 % inside
  assert.equal(driftHit(DRIFT, { image: "concept", rect: [35, 35, 45, 45] }).id, "D1");         // 100 %
  assert.equal(driftHit(DRIFT, { image: "side", rect: [30, 30, 40, 40] }), null);               // another image
  // the same at with basis concept (the image that decides there) stands
  const same = { ...fable, items: [{ ...fable.items[7], basis: "concept" }] };
  const r = classifyItems({ critiques: { fable: same, opus: { items: [] } }, evidence: { fable: [EV.fable[7]], opus: [] }, keys, drift: DRIFT, state, round: 2 });
  assert.equal(r.items[0].class, "B");
});

test("rule 4 decided: a decided key is DECIDED unless reopens carries a verified at on the decided basis", () => {
  const { items } = merged();
  const dec = find(items, "def:zR", "DECIDED");
  assert.equal(dec.length, 1);
  assert.deepEqual(Object.keys(dec[0].seats), ["fable"]);
  assert.match(dec[0].reason, /decided r1 on side: -1\.8/);
  const reopened = find(items, "def:zR", "C");                               // opus: reopens + a verified at on side
  assert.equal(reopened.length, 1);
  assert.equal(reopened[0].reopened.basis, "side");
  // reopens with an at on another image than the decided basis stays DECIDED
  const other = { ...opus, items: [{ ...opus.items[8], at: { image: "concept", rect: [0, 0, 4, 4], claim: "edge" } }] };
  const r = classifyItems({ critiques: { fable: { items: [] }, opus: other }, evidence: { fable: [], opus: [{ ok: true, image: "concept", text: "" }] }, keys, state, round: 2 });
  assert.equal(r.items[0].class, "DECIDED");
  assert.match(r.items[0].reason, /reopens not verified: needs a verified at on side/);
});

test("rule 5 tried / parked: one earlier try in the same direction -> TRIED, two -> PARKED (owner), parked stays parked", () => {
  const { items, stateAdd } = merged();
  const t = find(items, "def:mD")[0];
  assert.equal(t.class, "TRIED");
  assert.match(t.reason, /tried r1 \(-\): concept -0\.001, front -0\.004/);
  const p = find(items, "def:roofR")[0];
  assert.equal(p.class, "PARKED");
  assert.equal(p.owner, true);
  assert.match(p.reason, /tried 2x in the same direction \(\+\)/);
  assert.equal(find(items, "def:planR")[0].class, "PARKED");
  assert.match(find(items, "def:planR")[0].reason, /parked r1: measured worse twice/);
  // the other direction of a tried key is not TRIED (hubR "+" was tried; both seats ask "-")
  assert.equal(find(items, "def:hubR")[0].class, "CONFLICT");
  assert.deepEqual(stateAdd, {
    tried: [{ key: "def:mD", dir: "-", round: 2, result: "raised again by fable 10 in review r2 (TRIED)" }],
    parked: [{ key: "def:roofR", reason: "tried 2x (+); raised again by opus 8 in review r2", round: 2 }],
  });
  // the recorded TRIED line makes the next review's raise the second -> PARKED
  const next = { ...state, items: { ...state.items, tried: [...state.items.tried, ...stateAdd.tried] } };
  const r = classifyItems({ critiques: { fable: { items: [fable.items[9]] }, opus: { items: [] } }, evidence: { fable: [null], opus: [] }, keys, state: next, round: 3 });
  assert.equal(r.items[0].class, "PARKED");
  assert.equal(dirOf({ key: "def:mD", now: 0.16, want: 0.11 }), "-");
  assert.equal(dirOf({ key: "def:mD", now: 9, want: 0.11 }, 0.1), "+");                          // the model's value wins
  assert.equal(dirOf({ key: "part:tail.add", now: null, want: "lamp" }), "add");
  assert.equal(dirOf({ key: "part:tail.shape", now: "square", want: " Round " }), "=round");
});

test("rule 6 pairing: A (same sign, within 2x, target = mean), CONFLICT (opposite / > 2x), X, B, C; part family ~ knob comment", () => {
  const { items } = merged();
  const a = find(items, "knob:signT")[0];
  assert.equal(a.class, "A");
  assert.equal(a.sev, "MAJOR");                                              // fable's MAJOR has a verified at
  assert.equal(a.target, 0.3525);
  assert.deepEqual([a.seats.fable.want, a.seats.opus.want], [0.345, 0.36]);
  const mh = find(items, "knob:mh")[0];
  assert.equal(mh.class, "A");
  assert.match(mh.reason, /paired by family mirror_head ~ knob:mh/);
  assert.equal(mh.seats.fable.key, "part:mirror_head_l.size.y");
  assert.equal(mh.target, 0.35);
  assert.match(find(items, "def:br.bot")[0].reason, /opposite signs \(fable -0\.0500, opus \+0\.0700\)/);
  assert.match(find(items, "def:hubR")[0].reason, /amounts 0\.0100 vs 0\.1300 \(> 2x apart\)/);
  const x = find(items, "part:tail.shape")[0];
  assert.equal(x.class, "X");
  assert.match(x.reason, /different wants .* no knob \/ def key: build both/);
  assert.equal(find(items, "def:R")[0].class, "B");
  assert.equal(find(items, "def:cap.drop")[0].class, "C");
  // classes in CLASS_ORDER, ids per class letter
  assert.deepEqual(items.map((it) => it.id), ["A1", "A2", "B1", "K1", "K2", "X1", "C1", "C2", "C3", "R1", "R2", "D1", "T1", "P1", "P2"]);
  assert.deepEqual([...new Set(items.map((it) => it.class))], CLASS_ORDER);
  // F:C5's key (part family, axis): pos.y ~ size.y of one family pairs; another axis does not
  const item = (key, now, want) => ({ sev: "MINOR", key, now, want, unit: "m", views: ["rear"], basis: "rear", at: null, evidence: [], reopens: null, note: "" });
  const fa = { items: [item("part:rear_window.pos.y", 1.8, 1.835), item("part:tail.pos.x", 0.7, 0.75)] };
  const op = { items: [item("part:rear_window.size.y", 1.786, 1.825), item("part:tail.size.z", 0.2, 0.25)] };
  const r = classifyItems({ critiques: { fable: fa, opus: op }, evidence: { fable: [null, null], opus: [null, null] }, keys, round: 2 });
  assert.equal(r.items[0].class, "A");
  assert.match(r.items[0].reason, /paired by family \+ axis rear_window y; same sign/);
  assert.equal(r.items[0].target, null);                                   // pos vs size: both wants shown, no mean
  assert.deepEqual(r.items.slice(1).map((it) => it.class), ["C", "C"]);
  // a part item never pairs with a frame knob or with two candidates
  assert.equal(namesFamily({ comment: "mirror head height", name: "mh" }, "mirror_head"), true);
  assert.equal(namesFamily({ comment: "mirror heads (both)", name: "x" }, "mirror_head"), true);
  assert.equal(namesFamily({ comment: "rear mirror", name: "x" }, "mirror_head"), false);
  assert.equal(sameWant("#2a2a20", "#262620"), true);
  assert.equal(sameWant("#2a2a20", "#8f6912"), false);
  assert.equal(sameWant("Round", "round "), true);
});

test("rule 9 STOP line: STOP / CONTINUE / OWNER (cap, PARKED, X at the last review); settled CONFLICTs and drift items do not stand", () => {
  const good = { side: { agree: 0.975 }, concept: { agree: 0.981 } };
  const minor = [{ id: "C1", class: "C", key: "def:a", sev: "MINOR" }];
  assert.equal(stopLine({ items: minor, views: good, chainPass: true, round: 1 }).line, "STOP: STOP — no MAJOR standing; every view agree >= .970 (min .975 side); chain pass");
  assert.equal(stopLine({ items: minor, views: good, chainPass: false, round: 1 }).verdict, "CONTINUE");
  const low = { ...good, front: { agree: 0.962 } };
  assert.equal(stopLine({ items: minor, views: low, chainPass: true, round: 1 }).line, "STOP: CONTINUE — no MAJOR standing; min agree .962 (front) < .970; chain pass");
  const b = [{ id: "B1", class: "B", key: "knob:signT", sev: "MAJOR" }];
  assert.equal(stopLine({ items: b, views: good, chainPass: true, round: 1 }).line, "STOP: CONTINUE — 1 MAJOR standing (B1); every view agree >= .970 (min .975 side); chain pass");
  assert.equal(stopLine({ items: b, views: good, chainPass: true, round: 3, cap: 3 }).line, "STOP: OWNER — round 3 = the cap (3); 1 MAJOR standing (B1); every view agree >= .970 (min .975 side); chain pass");
  const settled = [{ id: "K1", class: "CONFLICT", key: "def:a", sev: "MAJOR", variant: { settled: "fable" } }, { id: "A1", class: "A", key: "drift:side", sev: "MAJOR" }];
  assert.equal(stopLine({ items: settled, views: good, chainPass: true, round: 1 }).verdict, "STOP");
  const unsettled = [{ id: "K1", class: "CONFLICT", key: "def:a", sev: "MAJOR", variant: null }];
  assert.deepEqual(stopLine({ items: unsettled, views: good, chainPass: true, round: 1 }).standing, ["K1"]);
  const x = [{ id: "X1", class: "X", key: "part:tail.shape", sev: "MINOR" }];
  assert.equal(stopLine({ items: x, views: low, chainPass: true, round: 1, cap: 3 }).verdict, "CONTINUE");       // build both next round
  assert.match(stopLine({ items: x, views: low, chainPass: true, round: 2, cap: 3 }).line, /^STOP: OWNER — 1 structural \(X1\) open at the last review/);
  // the fixture merge: an A-MAJOR and a B stand, two PARKED -> OWNER
  const { items } = merged();
  const s = stopLine({ items, views: good, chainPass: true, round: 1, cap: 3 });
  assert.equal(s.line, "STOP: OWNER — 2 PARKED (P1, P2); 2 MAJOR standing (A1, B1); every view agree >= .970 (min .975 side); chain pass");
});

test("area links (display only): overlapping or near at rects in one image share a link id and sit together; classes stay", () => {
  const mk = (id, cls, image, rect, seat = "fable") => ({ id, class: cls, key: `def:${id}`, seats: { [seat]: { at: { image, rect, claim: "edge" }, ev: { image } } } });
  const items = [
    mk("A1", "A", "concept", [100, 100, 120, 120]),
    mk("B1", "B", "side", [0, 0, 10, 10]),
    mk("C1", "C", "concept", [115, 115, 130, 130], "opus"),   // overlaps A1
    mk("C2", "C", "concept", [140, 100, 150, 110]),           // no overlap, centres 35 px from A1's: alone
    mk("C3", "C", "side", [12, 12, 20, 20]),                  // centres 15.6 px from B1's: linked
    mk("C4", "C", "front", [0, 0, 10, 10]),                   // B1's rect in another image: never linked
    mk("R1", "REJECTED", "concept", [100, 100, 120, 120]),    // not actionable: never linked
    { id: "C5", class: "C", key: "def:x", seats: { fable: { at: null } } },
  ];
  const links = areaLinks(items);
  assert.deepEqual(links, [{ id: "L1", images: ["concept"], items: ["A1", "C1"] }, { id: "L2", images: ["side"], items: ["B1", "C3"] }]);
  assert.deepEqual(items.map((it) => it.link), ["L1", "L2", "L1", null, "L2", null, null, null]);
  assert.deepEqual(items.map((it) => it.class), ["A", "B", "C", "C", "C", "C", "REJECTED", "C"]);
  assert.deepEqual(worksheetOrder(items).map((it) => it.id), ["A1", "C1", "B1", "C3", "C2", "C4", "R1", "C5"]);
  assert.equal(areaLinks(items, 10).length, 1);                                                   // near 10 px: B1 / C3 part
});

test("worksheet: the STOP line first, one table row per item", () => {
  const { items, stateAdd } = merged();
  const views = { side: { iou: 0.97, agree: 0.975 }, concept: { iou: 0.98, agree: 0.981 } };
  const stop = stopLine({ items, views, chainPass: true, round: 2 });
  const counts = Object.fromEntries(CLASS_ORDER.map((c) => [c, items.filter((it) => it.class === c).length]));
  const md = renderMarkdown({ stop, subject: "fixture", round: 2, module: "m.mjs", seats: { fable: { items: 10, warnings: [] }, opus: { items: 10, warnings: [] } }, counts, items, views, chain: { pass: true, violations: [], tris: 100, budget: 4000 }, owner: [], stateAdd });
  const lines = md.split("\n");
  assert.equal(lines[0], stop.line);
  assert.equal(lines.filter((l) => /^\| [A-Z]\d+ \|/.test(l)).length, items.length);
  assert.match(md, /\| A1 \| A MAJ \| knob:signT \| front,concept \| 0\.385→0\.345 MAJ \| 0\.385→0\.36 \|/);
  assert.match(md, /\| C1 \| C \| part:roof\.pos\.y \| side \| 1\.9→2 MAJ \(no at\) \|/);
});

test("keys: parseKey / familyOf / knobAxis / keyTable / overridesFor", () => {
  assert.deepEqual(parseKey("part:mirror_head_l.size.y"), { kind: "part", key: "part:mirror_head.size.y", family: "mirror_head", param: "size.y", axis: "y" });
  assert.equal(parseKey("part:arch_rl.colour").key, "part:arch.colour");
  assert.equal(parseKey("part:arch.width"), null);
  assert.deepEqual(parseKey("def:br.bot").path, ["br", "bot"]);
  assert.equal(familyOf("wheel_fl"), "wheel");
  assert.equal(familyOf("row_l3"), "row");
  assert.equal(familyOf("tyre_r1a"), "tyre_r1a");
  assert.deepEqual(["tyreX", "mirrorDY", "mirrorZ", "W", "H", "L", "hw0", "cabRearL", "wsBottomH", "br.bot", "head.zc", "bumpFW"].map((n) => knobAxis(n)), ["x", "y", "z", "x", "y", "z", "x", "z", "y", "y", "z", "x"]);
  assert.equal(knobAxis("signT", "roof-sign half-width at the top"), "x");
  assert.equal(knobAxis("roofFil", "side-profile fillet"), null);
  const src = [
    "export const KNOBS = {",
    "  signT: { v: 0.385, min: 0.25, max: 0.45, unit: \"m\", group: \"feature\" }, // roof-sign half-width at the top",
    "};",
    "export const DEFAULTS = {",
    "  br: { top: 0.73, bot: 0.38 },   // rear bumper",
    "  stripe: [1.69, 2.165],",
    "};",
  ].join("\n");
  const mod = { KNOBS: { signT: { v: 0.385, unit: "m", group: "feature" } }, DEFAULTS: { br: { top: 0.73, bot: 0.38 }, stripe: [1.69, 2.165] } };
  const t = keyTable(mod, src);
  assert.deepEqual([...t.keys()], ["knob:signT", "def:br.top", "def:br.bot", "def:stripe.0", "def:stripe.1"]);
  assert.equal(t.get("knob:signT").comment, "roof-sign half-width at the top");
  assert.equal(t.get("def:br.bot").comment, "rear bumper");
  assert.equal(t.get("def:br.bot").value, 0.38);
  assert.deepEqual(overridesFor(t.get("def:br.bot"), 0.35, mod), { br: { top: 0.73, bot: 0.35 } });
  assert.deepEqual(overridesFor(t.get("def:stripe.1"), 2.2, mod), { stripe: [1.69, 2.2] });
  assert.deepEqual(overridesFor(t.get("knob:signT"), 0.36, mod), { signT: 0.36 });
  assert.equal(mod.DEFAULTS.br.bot, 0.38);                                   // the module's DEFAULTS are untouched
});

test("state: a minimal state.json from LEDGER.md (the last modeller round, empty items)", () => {
  const s = minimalState("taxi", "# LEDGER\nr1 modeller: x\nr1 critics: y\nr2 modeller: z\nr2 critics: w\n", 5);
  assert.equal(s.round, 2);
  assert.equal(s.roundType, "list");
  assert.deepEqual(s.items, { decided: [], tried: [], parked: [], open: [] });
  assert.equal(minimalState("taxi", "", 3).round, 3);
  assert.equal(MERGE_RULES.triedK, 2);
});

test("seats: opus + sonnet is the standard pair now (schema accepts it; pairing, reasons and seats keys use the real seat names)", () => {
  const schema = loadSchema();
  assert.deepEqual(checkCritique({ ...opus, seat: "sonnet" }, { seat: "sonnet" }, schema), { errors: [], warnings: [] });
  // relabel the fixture pair opus -> opus (unchanged) / fable -> sonnet: activeSeats is derived from the critiques keys
  // (SEATS fable-first; "fable" absent here so opus sorts first), same as a legacy fable + opus pair did
  const critiques2 = { opus: { ...opus, seat: "opus" }, sonnet: { ...fable, seat: "sonnet" } };
  const evidence2 = { opus: evidence.opus, sonnet: evidence.fable };
  const r = classifyItems({ critiques: critiques2, evidence: evidence2, keys, drift: DRIFT, state, round: 2 });
  const a = find(r.items, "knob:signT")[0];
  assert.equal(a.class, "A");
  assert.deepEqual(Object.keys(a.seats), ["opus", "sonnet"]);
  assert.match(find(r.items, "def:br.bot")[0].reason, /opposite signs \(opus \+0\.0700, sonnet -0\.0500\)/);
  const decRow = find(r.items, "def:zR", "DECIDED")[0];
  assert.deepEqual(Object.keys(decRow.seats), ["sonnet"]);   // was fable's item in the original fixture
});

test("gate: the school_bus round-3 'near-black arch' item (side px ~ 244, 566) is REJECTED by the evidence rule", async () => {
  const module = path.join(ROOT, "out", "ref", "gold", "school_bus", "model-v21.mjs");
  const r = await runMerge({ subject: "school_bus", round: 3, dir: path.join(FIX, "bus-r3"), module, write: false, variants: false });
  assert.equal(r.ok, true, JSON.stringify(r.blocked));
  const arch = r.merged.items.find((it) => it.key === "part:arch.colour");
  assert.equal(arch.class, "REJECTED");
  const ev = arch.seats.fable.ev;
  assert.equal(ev.image, "side");
  assert.equal(ev.ref.family, "tyre+black");                               // the reference px there are the tyre
  assert.notEqual(ev.model.family, "orange");                               // the model does not show its khaki well there
  assert.match(arch.reason, /the model does not show now's family \(orange\)/);
});
