// WF v8 WP5 — gold.mjs / goldlib.mjs: config loading, state.json <-> LEDGER.md, the brief per role and round type, close
// refusing on a changed eyes hash, the merge wiring on the WP4 fixtures (test/fixtures/wf-v8-merge), the drift boundary
// rule, the doctor's hull row, the span-preserving JSON editor. The CLI tests run gold.mjs on temp --dir copies and only
// on paths that refuse BEFORE any subject file is written. Run: node --test scripts/v7/gold.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import {
  CO_AUTHOR, LEDGER_MARK, ROOT, addItem, applyMerge, applyReport, briefAuditor, briefCritic, briefModeller, budgetLine, changedFiles, checkConfig, checkState,
  combineHashes, commitCandidates, eyeRulings, commitMessage, critiqueDrift, criticsLine, driftBoundary, driftJson, driftProposals, extraLedgerLines, eyeBoundary, eyesFileList,
  hashFiles, hullRows, importLedger, inlineJson, jsonTree, ledgerFacts, loadConfig, modellerLine, newState, nextAction, oneLine, orderState, ownerBatch, ownerPacket,
  paletteZoneViolations, parseRun, renderLedger, repairLedger, reportDir, roleOf, roundTypeOf, serializeState, setJsonKey, setupMisses, setupRulings, setupStopOf,
  setupTargetsOf, shiftTable, shiftWinner, stopRuleText, trisValue, wheelsValue, withOverride,
} from "./goldlib.mjs";
import { CLASS_ORDER, classifyItems, stopLine } from "./merge.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIX = path.join(ROOT, "test", "fixtures", "wf-v8-merge");
const readFix = (f) => JSON.parse(fs.readFileSync(path.join(FIX, f), "utf8"));
const tmpDir = (tag) => fs.mkdtempSync(path.join(os.tmpdir(), `gold-test-${tag}-`));
const gold = (argv) => spawnSync(process.execPath, [path.join(HERE, "gold.mjs"), ...argv], { cwd: ROOT, encoding: "utf8", windowsHide: true });
const ORDER = ["side", "front", "rear", "top", "concept"];

// ---------------------------------------------------------------------------------------------------------------------

test("config: gold.config.json loads, every numeric section carries the ratify marker, bad numbers throw; round types", () => {
  const c = loadConfig();
  assert.equal(c.rounds.cap, 3);
  assert.deepEqual([c.rounds.types.build.calls, c.rounds.types.list.calls, c.rounds.types.polish.calls], [100, 60, 40]);
  assert.equal(c.critics.maxTurns, 40);
  assert.equal(c.bar.agree, 0.97);
  assert.deepEqual(c.setupHull, { ...c.setupHull, viewOnly: { warn: 0.03, block: 0.06 }, conceptOnlyBlob: { warn: 0.025, block: 0.04 } });
  for (const k of ["rounds", "critics", "bar", "setupHull"]) assert.equal(c[k]._ratify, "defaults, owner ratification pending", k);
  assert.equal(c._ratify, "defaults, owner ratification pending");
  assert.throws(() => checkConfig({ ...c, rounds: { ...c.rounds, cap: 0 } }), /rounds\.cap = 0/);
  assert.throws(() => checkConfig({ ...c, bar: { agree: 1.2 } }), /bar\.agree = 1\.2/);
  assert.throws(() => checkConfig({ ...c, setupHull: { ...c.setupHull, viewOnly: { warn: 0.06, block: 0.03 } } }), /setupHull\.viewOnly: block < warn/);
  assert.deepEqual([1, 2, 3, 4].map((r) => roundTypeOf(r, 3)), ["build", "list", "polish", "polish"]);
  assert.deepEqual([1, 2, 3, 4].map((r) => roundTypeOf(r, 4)), ["build", "list", "list", "polish"]);
  assert.equal(roundTypeOf(1, 1), "build");
  assert.deepEqual(parseRun("57,23"), { calls: 57, minutes: 23 });
  assert.deepEqual(parseRun("40"), { calls: 40, minutes: null });
  assert.equal(parseRun(undefined), null);
  assert.throws(() => parseRun("x"), /want <tool calls>,<minutes>/);
});

test("state.json round trip: the contract's key order, shape errors, LEDGER.md generated from the entries", () => {
  const st = newState("fixture");
  assert.deepEqual(checkState(st), []);
  st.ledger.push({ round: 1, role: "modeller", text: "r1 modeller: model-r1 · agree .960/.950" });
  st.ledger.push({ round: 1, role: "drift", text: "drift: side — x" });
  const text = serializeState({ ledger: st.ledger, ...st, extra: 1 });
  assert.deepEqual(Object.keys(JSON.parse(text)), ["subject", "round", "phase", "roundType", "baseline", "modelHash", "eyesHash", "items", "runs", "ledger", "extra"]);
  assert.deepEqual(JSON.parse(text).ledger, st.ledger);
  assert.deepEqual(checkState(JSON.parse(text)), []);
  assert.match(checkState({ ...st, phase: "polish" }).join(), /phase "polish"/);
  assert.match(checkState({ ...st, items: { decided: [] } }).join(), /items\.tried: a list/);
  assert.match(checkState({ ...st, ledger: [{ text: "x" }] }).join(), /ledger\[0\]: \{round, role, text\}/);
  assert.deepEqual(Object.keys(orderState({ round: 2, subject: "s" })).slice(0, 3), ["subject", "round", "phase"]);
  const md = renderLedger(st, ["side", "front", "rear", "top"]);
  assert.equal(md, `# LEDGER — fixture (one factual line per step; IoU = side / front / rear / top / concept)\n${LEDGER_MARK}\nr1 modeller: model-r1 · agree .960/.950\ndrift: side — x\n`);
  const back = importLedger(md);
  assert.deepEqual(back.entries, st.ledger);
  assert.equal(back.header, "# LEDGER — fixture (one factual line per step; IoU = side / front / rear / top / concept)");
});

test("LEDGER import: every committed v7 ledger line survives verbatim (roles and rounds parsed)", () => {
  for (const s of ["taxi", "school_bus", "pickup", "delivery_truck", "tractor"]) {
    const f = path.join(ROOT, "out", "ref", "gold", s, fs.existsSync(path.join(ROOT, "out", "ref", "gold", s, "LEDGER-v7.md")) ? "LEDGER-v7.md" : "LEDGER.md");
    if (!fs.existsSync(f)) continue;
    // the committed ledger (a v7 file, or one generated since the migration: its mark line is the only addition)
    const old = fs.readFileSync(f, "utf8").replace(/\r\n/g, "\n").split("\n").filter((l) => l !== LEDGER_MARK).join("\n");
    const { header, entries } = importLedger(old);
    const st = { ...newState(s), ledger: entries };
    const regen = renderLedger(st, ["side", "front", "rear", "top"]).split("\n").filter((l) => l !== LEDGER_MARK).join("\n");
    assert.equal(regen.replace(/\n+$/, ""), old.replace(/\n+$/, ""), s);
    assert.ok(header.startsWith("# LEDGER"));
    assert.ok(entries.every((e) => Number.isInteger(e.round) && e.role), s);
  }
  assert.deepEqual(roleOf("r3 modeller: model-v22"), { role: "modeller", round: 3 });
  assert.deepEqual(roleOf("r4 critics (owner extra round): Opus"), { role: "critics", round: 4 });
  assert.deepEqual(roleOf("r1 critic (Fable): ACCEPT"), { role: "critics", round: 1 });
  assert.deepEqual(roleOf("K1 r5 (cab back rake)"), { role: "variants", round: 5 });
  assert.deepEqual(roleOf("drift: top — x", 2), { role: "drift", round: 2 });
  assert.deepEqual(roleOf("OWNER (open): length", 5), { role: "owner", round: 5 });
  assert.deepEqual(roleOf("END (4-round cap): r3", 4), { role: "end", round: 4 });
  assert.deepEqual(roleOf("audit (setup): top regenerated"), { role: "audit", round: 0 });
  assert.deepEqual(roleOf("something else", 3), { role: "note", round: 3 });
  // hand-written lines appended to a generated LEDGER.md are imported, repeats counted, the mark / header skipped
  const entries = [{ round: 1, role: "modeller", text: "r1 modeller: a" }, { round: 1, role: "drift", text: "drift: x" }];
  const file = `${renderLedger({ ...newState("s"), ledger: entries }, ["side"])}drift: x\nturnaround regenerated: side (hand)\n`;
  assert.deepEqual(extraLedgerLines(file, entries, 2), [{ role: "drift", round: 2, text: "drift: x" }, { role: "note", round: 2, text: "turnaround regenerated: side (hand)" }]);
  assert.deepEqual(extraLedgerLines(renderLedger({ ...newState("s"), ledger: entries }, ["side"]), entries), []);
});

// ---------------------------------------------------------------------------------------------------------------------

const BASE = {
  file: "out/ref/gold/fixture/baseline/r2-start.json",
  views: { side: { iou: 0.98, agree: 0.98, drift: 0 }, front: { iou: 0.9, agree: 0.93, drift: 0.02 }, rear: { iou: 0.95, agree: 0.95, drift: 0 }, top: { iou: 0.87, agree: 0.87, drift: 0 }, concept: { iou: 0.96, agree: 0.96, drift: 0 } },
  blobs: { side: [{ kind: "missing", px: 922, bbox: { right: [-1.08, -0.65], up: [1.29, 1.77] }, bboxPx: [305, 391, 386, 481], part: "windshield" }] },
  chain: { pass: true, rows: [] }, tris: 3810, budget: 4000, probes: [],
};
const ITEMS = {
  decided: [{ key: "def:zR", value: -1.21, basis: "side", round: 1, evidence: "side hub" }],
  tried: [{ key: "def:roofR", dir: "+", round: 1, result: "front -0.001" }],
  parked: [{ key: "def:planR", reason: "measured worse twice", round: 1 }],
  open: [{ key: "fact:owner-r1", text: "overall length", owner: true }],
};
const common = (over = {}) => ({
  subject: "fixture", at: "2026-09-27T00:00:00Z", dirRel: "out/ref/gold/fixture", concept: "refs/fixture.png", turnaround: "subjects/fixture/turnaround",
  viewFiles: ["side.png", "front.png", "rear.png", "top.png"], order: ORDER, bar: 0.97, dims: "L 4.7 · W 1.85 · H 2.2 m", items: ITEMS,
  drift: { audited: "2026-09-27 gold-auditor, owner-approved", front: [{ id: "D1", rect: [10, 20, 30, 40], decides: "concept", why: "bumper drawn lower" }] },
  keysText: "knob:signT = 0.385 m [feature] axis x  // roof-sign half-width", partsText: "families: body:900 sign:40\ntotal tris 3810 parts 55", ...over,
});

test("brief (modeller): round type + budget, the round-start baseline, the worksheet only for list / polish, facts, keys, eyes", () => {
  const cfg = loadConfig();
  const mk = (round, type, worksheet) => briefModeller({ ...common(), round, cap: 3, type, calls: cfg.rounds.types[type].calls, rule: cfg.rounds.types[type].rule,
    start: `model-r${round - 1}.mjs`, baseline: BASE, worksheet, eyesFiles: ["scripts/v6/judge.mjs", "subjects/fixture/turnaround/views.json"], resume: null,
    ledger: ["r1 modeller: model-r1 · agree .960", "r1 critics: fable 5 items · merged: 1 A"] });
  const build = mk(1, "build", null);
  assert.match(build, /^# gold-modeller brief — fixture, round 1 \(build · ≤ 100 tool calls\)/);
  assert.match(build, /Round 1 of 3: \*\*build\*\* — the first round/);
  assert.match(build, /None — the build round/);
  assert.match(build, /\| front \| 0\.9000 \| 0\.9300 \| 2\.0 % \| -0\.0400 \|/);
  assert.match(build, /blobs side: miss 922px ~windshield r-1\.08\.\.-0\.65 u1\.29\.\.1\.77 \(px 305,391,386,481\)/);
  assert.match(build, /node scripts\/v7\/step\.mjs --subject fixture --save --note/);
  assert.match(build, /report\/r1-modeller\.json/);
  assert.match(build, /- def:zR = -1\.21 \(r1, side\)/);
  assert.match(build, /- def:roofR \+ \(r1\): front -0\.001/);
  assert.match(build, /- def:planR \(r1\): measured worse twice/);
  assert.match(build, /- front D1 \[10, 20, 30, 40\] decides concept — bumper drawn lower/);
  assert.match(build, /knob:signT = 0\.385/);
  assert.match(build, /`scripts\/v6\/judge\.mjs` · `subjects\/fixture\/turnaround\/views\.json`/);
  const ws = { file: "out/ref/gold/fixture/critique/r1-merged.md", text: "STOP: CONTINUE — 1 MAJOR standing (B1)\n\n| B1 | B MAJ | knob:signT |" };
  const list = mk(2, "list", ws);
  assert.match(list, /round 2 \(list · ≤ 60 tool calls\)/);
  assert.match(list, /STOP: CONTINUE — 1 MAJOR standing \(B1\)/);
  assert.match(list, /`out\/ref\/gold\/fixture\/critique\/r1-merged\.md` \(scripts\/v7\/merge\.mjs\)\. Order: A, then B, CONFLICT/);
  const polish = mk(3, "polish", ws);
  assert.match(polish, /round 3 \(polish · ≤ 40 tool calls\)/);
  assert.match(polish, /A \/ B \/ C items only, no structural change/);
  const extra = briefModeller({ ...common(), round: 4, cap: 3, type: "polish", calls: 40, rule: "x", start: "model-r3.mjs", baseline: BASE, worksheet: null, eyesFiles: [], resume: { startedAt: "t0", steps: [{ file: "steps/model-v31.mjs", note: "sign" }] }, ledger: [] });
  assert.match(extra, /the owner's extra round/);
  assert.match(extra, /## RESUME — this round is already open/);
  assert.match(extra, /- steps\/model-v31\.mjs "sign"/);
});

test("brief (critic): the seat's own output files, the schema, the keys and families, the close numbers; never another seat's critique", () => {
  const st = { ...newState("fixture"), ledger: [
    { round: 1, role: "modeller", text: "r1 modeller: model-r1 · agree .960" },
    { round: 1, role: "critics", text: "r1 critics: fable 5 items · opus 3 items · merged (scripts/v7/merge.mjs): 1 A · STOP: CONTINUE" },
    { round: 1, role: "drift", text: "drift: front — bumper lower" },
  ] };
  const facts = ledgerFacts(st);
  assert.deepEqual(facts, ["r1 modeller: model-r1 · agree .960", "drift: front — bumper lower"]);
  for (const seat of ["fable", "opus", "sonnet"]) {
    const others = ["fable", "opus", "sonnet"].filter((s) => s !== seat);
    const b = briefCritic({ ...common(), round: 2, seat, maxItems: 10, sheet: "out/ref/gold/fixture/view/model-view.png", pages: ORDER.map((v) => `out/ref/gold/fixture/view/model-${v}.png`),
      baseline: BASE, families: "body, sign", resume: null, ledger: facts });
    assert.match(b, new RegExp(`^# gold-critic-${seat} brief — fixture, review of round 2`));
    assert.match(b, new RegExp(`critique/r2-${seat}\\.json\` per \`scripts/v7/critique\\.schema\\.json\``));
    assert.match(b, new RegExp(`"seat": "${seat}", "done": false`));
    assert.match(b, /≤ 10 items/);
    assert.match(b, /node scripts\/v7\/merge\.mjs --validate out\/ref\/gold\/fixture\/critique\/r2-/);
    assert.match(b, /Part families: body, sign/);
    assert.match(b, /knob:signT = 0\.385/);
    assert.match(b, /never page px/);
    for (const other of others) assert.doesNotMatch(b, new RegExp(`r\\d-${other}\\.(json|md)`));
    assert.doesNotMatch(b, /r\d-merged/);
    assert.doesNotMatch(b, /r1 critics:/);
  }
});

// ---------------------------------------------------------------------------------------------------------------------

test("merge wiring on the WP4 fixtures: tried / parked / decided / open, the critics line with the STOP line, the phase", () => {
  const fable = readFix("r2-fable.json"), opus = readFix("r2-opus.json"), state0 = readFix("state.json");
  const keys = new Map(Object.entries(readFix("keys.json")).filter(([k]) => !k.startsWith("_")).map(([k, v]) => [k, { key: k, path: v.name.split("."), ...v }]));
  // the WP4 test's frozen evidence results and drift rect (test/wf-v8-merge.test.js EV / DRIFT)
  const EV = {
    fable: { 0: { ok: true, image: "concept", text: "concept ref-only 40.0 %" }, 3: { ok: false, image: "side", text: "side colour: the same family" }, 7: { ok: true, image: "concept", text: "concept edge: 12 px differ" } },
    opus: { 3: { ok: true, image: "side", text: "side model-only 30.0 %" }, 8: { ok: true, image: "side", text: "side edge: 3 px differ" } },
  };
  const evidence = Object.fromEntries(["fable", "opus"].map((s) => [s, [...Array(10).keys()].map((i) => EV[s][i] ?? null)]));
  const DRIFT = { concept: [{ id: "D1", rect: [25, 25, 45, 45], decides: "concept", why: "flank drawn inboard" }] };
  const { items, stateAdd } = classifyItems({ critiques: { fable, opus }, evidence, keys, drift: DRIFT, state: state0, round: 2 });
  const views = { side: { iou: 0.97, agree: 0.975 }, concept: { iou: 0.98, agree: 0.981 } };
  const counts = Object.fromEntries(CLASS_ORDER.map((c) => [c, items.filter((it) => it.class === c).length]));
  // a CONFLICT settled by its variants table (the shape runMerge's rule 7 writes)
  const k = items.find((it) => it.class === "CONFLICT" && /^(knob|def):/.test(it.key));
  assert.equal(k?.key, "def:br.bot");
  k.variant = { winner: "#1", settled: "fable", rows: [{ tag: "BASE", value: 0.39 }], lines: ["WINNER #1"] };
  k.target = 0.45;
  const k2 = items.find((it) => it.id === "K2");
  k2.variant = { winner: "BASE", settled: "BASE", rows: [{ tag: "BASE", value: 0.23 }], lines: ["WINNER BASE"] };
  const mk = (round, cap) => {
    const stop = stopLine({ items, views, chainPass: true, round, cap });
    const owner = items.filter((it) => it.owner).map((it) => ({ id: it.id, class: it.class, key: it.key, reason: it.reason }));
    return { stop, subject: "fixture", round, cap, seats: { fable: { items: fable.items.length }, opus: { items: opus.items.length } }, counts, items, owner, stateAdd, views };
  };
  const merged = mk(2, 3);
  assert.equal(merged.stop.verdict, "OWNER");                     // 2 PARKED in the fixture
  const st = structuredClone(state0);
  applyMerge(st, merged, { cap: 3, runs: { fable: { calls: 31, minutes: 12 }, opus: null } });
  assert.equal(st.phase, "owner");
  assert.equal(st.round, 2);
  for (const t of stateAdd.tried) assert.ok(st.items.tried.some((x) => x.key === t.key && x.dir === t.dir && x.round === t.round));
  for (const p of stateAdd.parked) assert.ok(st.items.parked.some((x) => x.key === p.key));
  assert.equal(st.items.open.filter((o) => o.owner).length, merged.owner.length);
  assert.ok(st.items.decided.some((d) => d.key === "def:br.bot" && d.value === 0.45 && /variants concept-first r2 \(fable's want\)/.test(d.basis) && d.evidence === "K1: WINNER #1"));
  assert.ok(st.items.decided.some((d) => d.key === "def:hubR" && d.value === 0.23 && /BASE kept/.test(d.basis)));
  assert.ok(st.items.parked.some((p) => p.key === "def:roofR"));
  assert.deepEqual(st.runs, [{ role: "critic", seat: "fable", round: 2, calls: 31, minutes: 12, ok: true }, { role: "critic", seat: "opus", round: 2, calls: null, minutes: null, ok: true }]);
  const line = st.ledger[st.ledger.length - 1];
  assert.equal(line.role, "critics");
  assert.match(line.text, /^r2 critics: fable 10 items · opus 10 items · merged \(scripts\/v7\/merge\.mjs\): /);
  assert.ok(line.text.endsWith(merged.stop.line));
  assert.deepEqual(checkState(st), []);
  // applying the same merge twice adds no duplicate items
  const n = JSON.stringify(st.items);
  applyMerge(st, merged, { cap: 3 });
  assert.equal(JSON.stringify(st.items), n);
  // CONTINUE -> the next round's modeller, its type from the cap
  const cont = { ...merged, stop: { verdict: "CONTINUE", line: "STOP: CONTINUE — x" }, owner: [] };
  const st2 = applyMerge(structuredClone(state0), cont, { cap: 3 });
  assert.deepEqual([st2.phase, st2.round, st2.roundType], ["model", 3, "polish"]);
  const st3 = applyMerge({ ...structuredClone(state0), round: 1 }, { ...cont, round: 1 }, { cap: 3 });
  assert.deepEqual([st3.phase, st3.round, st3.roundType], ["model", 2, "list"]);
  assert.match(criticsLine({ round: 1, merged: cont }), /STOP: CONTINUE — x$/);
});

test("modeller report into the state: tried with its direction (the merge's TRIED key), decided, open, drift proposals", () => {
  const st = newState("fixture");
  applyReport(st, {
    items: [
      { id: "A1", key: "knob:signT", status: "done", from: 0.385, to: 0.365 },
      { id: "C2", key: "def:roofR", status: "tried", from: 0.24, to: 0.3, why: "front -0.004" },
      { id: "C3", key: "part:grille.add", status: "tried", why: "tris" },
      { id: "C4", key: "def:x", status: "tried", dir: "-", why: "given" },
    ],
    decided: [{ key: "def:cowl", value: 1.0, basis: "variants", evidence: "1.09 .9625 / 1.00 .9632" }],
    open: [{ key: "fact:paint", text: "two-tone flank needs a palette zone" }],
    drift: [{ image: "side", rect: [1, 2, 3, 4], decides: "concept", why: "arch" }],
  }, 3);
  assert.deepEqual(st.items.tried.map((t) => [t.key, t.dir, t.round]), [["def:roofR", "+", 3], ["part:grille.add", "add", 3], ["def:x", "-", 3]]);
  assert.equal(st.items.decided[0].value, 1.0);
  assert.equal(st.items.open.length, 2);
  assert.ok(st.items.open.find((o) => o.key === "drift:side" && o.owner));
  assert.equal(reportDir({ key: "knob:a", from: 1, to: 1 }), "0");
  assert.equal(reportDir({ key: "part:hub.colour", to: "#AABBCC" }), "=#aabbcc");
  assert.equal(applyReport(st, null, 3), st);
  const line = modellerLine({ round: 3, snapshot: "model-r3", views: BASE.views, base: BASE.views, order: ORDER, gate: { pass: true, rows: [] }, tris: 3810, budget: 4000, kept: 4,
    report: { items: [{ id: "A1", status: "done" }, { id: "C2", status: "tried", why: "front -0.004" }] } });
  assert.equal(line, "r3 modeller: model-r3 · agree .980/.930/.950/.870/.960 · iou .980/.900/.950/.870/.960 · vs start +.000/+.000/+.000/+.000/+.000 · gate pass · tris 3810/4000 · 4 kept steps · done A1 · tried C2 (front -0.004)");
  assert.match(modellerLine({ round: 1, snapshot: "model-r1", views: BASE.views, base: null, order: ORDER, gate: { pass: false, rows: ["V5 a", "V5 b"] }, tris: 1, budget: 2, kept: 0, report: null }), /gate FAIL \(V5 a, V5 b\) · tris 1\/2 · 0 kept steps · no report$/);
});

// ---------------------------------------------------------------------------------------------------------------------

test("drift boundary rule: only in setup / owner / done, or before a round's brief", () => {
  const st = (phase) => ({ ...newState("s"), phase, round: 2 });
  assert.equal(driftBoundary(st("setup"), false).ok, true);
  assert.equal(driftBoundary(st("owner"), true).ok, true);
  assert.equal(driftBoundary(st("done"), false).ok, true);
  assert.equal(driftBoundary(st("model"), false).ok, true);
  assert.deepEqual(driftBoundary(st("model"), true), { ok: false, why: "round 2 is open (the modeller's baseline would move)" });
  assert.match(driftBoundary(st("review"), false).why, /under review/);
});

/** A temp gold dir for a real subject (read-only use of its eyes files): state + brief meta, nothing under subjects/ written. */
function tempGold(subject, st, extra = {}) {
  const dir = tmpDir(subject);
  fs.writeFileSync(path.join(dir, "state.json"), serializeState(st));
  for (const [f, v] of Object.entries(extra)) { fs.mkdirSync(path.dirname(path.join(dir, f)), { recursive: true }); fs.writeFileSync(path.join(dir, f), typeof v === "string" ? v : JSON.stringify(v)); }
  return dir;
}

test("CLI: close refuses when an eyes file changed since the brief (naming it); drift add refuses off a round boundary", () => {
  const cfg = loadConfig();
  const S = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects", "taxi", "subject.json"), "utf8"));
  const spec = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects", "taxi", "turnaround", "views.json"), "utf8"));
  const files = hashFiles(eyesFileList(cfg, { subject: "taxi", klass: S.class, paths: S.paths, viewFiles: Object.values(spec.views).map((v) => v.file) }));
  const recorded = { ...files, "scripts/v6/ortho.mjs": "0".repeat(64) };   // the brief saw another ortho.mjs
  const st = { ...newState("taxi"), phase: "model", round: 2, roundType: "list", eyesHash: combineHashes(recorded) };
  const dir = tempGold("taxi", st, { "brief/r2-modeller.json": { round: 2, start: "model-r1.mjs", baseline: "x", stepsAtStart: 0 }, "eyes.json": { eyesHash: combineHashes(recorded), files: recorded } });
  const r = gold(["close", "--subject", "taxi", "--dir", dir]);
  assert.equal(r.status, 1, r.stdout + r.stderr);
  assert.match(r.stdout, /REFUSED: close refused: the eyes changed during round 2: scripts\/v6\/ortho\.mjs — eyes change only at a round boundary/);
  assert.deepEqual(fs.readdirSync(dir).sort(), ["brief", "eyes.json", "state.json"]);   // nothing written
  // the same state, eyes unchanged, but no brief for the round -> refused before anything runs
  const dir2 = tempGold("taxi", { ...st, eyesHash: combineHashes(files) });
  assert.match(gold(["close", "--subject", "taxi", "--dir", dir2]).stdout, /round 2 was never briefed/);
  // drift add: under review / an open round -> refused; no owner approval -> refused (views.json untouched)
  const views0 = fs.readFileSync(path.join(ROOT, "subjects", "taxi", "turnaround", "views.json"), "utf8");
  const add = ["drift", "add", "--subject", "taxi", "--image", "side", "--rect", "1,2,3,4", "--decides", "concept", "--why", "test", "--owner-approved"];
  const d1 = gold([...add, "--dir", tempGold("taxi", { ...st, phase: "review" })]);
  assert.match(d1.stdout, /REFUSED: drift add refused: round 2 is under review/);
  const d2 = gold([...add, "--dir", dir]);
  assert.match(d2.stdout, /REFUSED: drift add refused: round 2 is open/);
  const d3 = gold(["drift", "add", "--subject", "taxi", "--image", "side", "--rect", "1,2,3,4", "--decides", "concept", "--why", "t", "--dir", tempGold("taxi", { ...st, phase: "owner" })]);
  assert.match(d3.stdout, /REFUSED: drift rects are an owner decision/);
  assert.equal(fs.readFileSync(path.join(ROOT, "subjects", "taxi", "turnaround", "views.json"), "utf8"), views0);
  // merge off its phase, brief of the wrong role
  assert.match(gold(["merge", "--subject", "taxi", "--dir", dir]).stdout, /is in phase model, not review/);
  assert.match(gold(["brief", "--subject", "taxi", "--role", "critic", "--seat", "fable", "--dir", dir]).stdout, /is in phase model, not review/);
  assert.equal(gold(["brief", "--subject", "taxi", "--role", "x", "--dir", dir]).status, 3);
});

// ---------------------------------------------------------------------------------------------------------------------

test("NEXT per phase", () => {
  const f = (over = {}) => ({ cmd: "g", flags: "", doctor: { verdict: "WARN", hullLevel: "PASS", stale: false }, audit: { done: true, verdict: "READY" }, briefOpen: false, critiques: { opus: "done", sonnet: "missing" }, pairSeats: ["opus", "sonnet"], ...over });
  const st = (phase, round = 1) => ({ ...newState("s"), phase, round, roundType: "build" });
  assert.match(nextAction(st("setup"), f({ doctor: null })).cmd, /^g doctor --subject s$/);
  assert.match(nextAction(st("setup"), f({ doctor: { hullLevel: "BLOCK" } })).cmd, /turnaround\.mjs status --subject s/);
  assert.match(nextAction(st("setup"), f({ audit: null })).cmd, /^g brief --subject s --role auditor/);
  assert.match(nextAction(st("setup"), f({ audit: { done: true, semantic: true } })).cmd, /^fix the images/);
  assert.match(nextAction(st("setup"), f()).cmd, /^OWNER setup gate: .* g apply-audit --subject s --owner-approved$/);
  assert.equal(nextAction(st("model"), f()).cmd, "g brief --subject s --role modeller");
  assert.match(nextAction(st("model"), f({ briefOpen: true })).cmd, /^Agent gold-modeller with out\/ref\/gold\/s\/brief\/r1-modeller\.md; then g close/);
  // the default pair (opus + sonnet): a fresh round briefs sonnet once opus is done, then merges on both
  assert.match(nextAction(st("review"), f()).cmd, /^g brief --subject s --role critic --seat sonnet  → Agents gold-critic-sonnet in parallel$/);
  assert.match(nextAction(st("review"), f({ critiques: { opus: "done", sonnet: "done" } })).cmd, /^g merge --subject s --opus <calls>,<minutes> --sonnet <calls>,<minutes>/);
  // legacy fable pairing: a round already under fable + opus continues on that pair instead of switching to sonnet
  assert.match(nextAction(st("review"), f({ critiques: { fable: "partial", opus: "done" } })).cmd, /^g brief --subject s --role critic --seat fable  → Agents gold-critic-fable in parallel$/);
  assert.match(nextAction(st("review"), f({ critiques: { fable: "done", opus: "done" } })).cmd, /^g merge --subject s --fable <calls>,<minutes> --opus <calls>,<minutes>/);
  assert.match(nextAction(st("owner"), f()).cmd, /^OWNER: show out\/ref\/gold\/s\/OWNER\.md/);
  assert.equal(nextAction(st("done"), f()).cmd, "none");
});

test("doctor hull row: WARN above warn, BLOCK above block, per view and for the concept", () => {
  const gate = loadConfig().setupHull;
  const R = (vo, co) => ({ views: { side: { viewOnly: 0 }, front: { viewOnly: vo } }, concept: { conceptOnlyBlob: co, iou: 0.95 } });
  assert.equal(hullRows(R(0.03, 0.025), gate)[0].level, "PASS");
  assert.equal(hullRows(R(0.031, 0.01), gate)[0].level, "WARN");
  assert.equal(hullRows(R(0.01, 0.026), gate)[0].level, "WARN");
  assert.equal(hullRows(R(0.061, 0.01), gate)[0].level, "BLOCK");
  assert.equal(hullRows(R(0.01, 0.041), gate)[0].level, "BLOCK");
  const row = hullRows(R(0.071, 0.0276), gate)[0];
  assert.equal(row.id, "hull");
  assert.match(row.text, /viewOnly side 0\.0 \/ front 7\.1 % \(warn > 3, block > 6\) · conceptOnlyBlob 2\.76 % \(warn > 2\.5, block > 4\) · concept IoU \.950 — front viewOnly 7\.1 % BLOCK, conceptOnlyBlob 2\.76 % WARN/);
  assert.deepEqual(row.data, { views: { side: 0, front: 0.071 }, conceptOnlyBlob: 0.0276, conceptIoU: 0.95 });
  assert.equal(hullRows({ views: { side: { viewOnly: 0 } } }, gate)[0].level, "PASS");
});

test("eyes: the file list per subject, hashes, the combined hash, changed files", () => {
  const cfg = { eyes: { files: ["scripts/v6/judge.mjs"], subject: ["subjects/{s}/subject.json", "{views}", "{target}", "{layout}", "classes/{class}.json"] } };
  const list = eyesFileList(cfg, { subject: "taxi", klass: "vehicle", paths: { target: "refs/taxi.png" }, viewFiles: ["side.png", "top.png"] });
  assert.deepEqual(list, ["scripts/v6/judge.mjs", "subjects/taxi/subject.json", "subjects/taxi/turnaround/side.png", "subjects/taxi/turnaround/top.png", "refs/taxi.png", "classes/vehicle.json"]);
  const h = hashFiles([...list, "no/such/file.json"]);
  assert.equal(h["no/such/file.json"], null);
  assert.match(h["refs/taxi.png"], /^[0-9a-f]{64}$/);
  assert.match(combineHashes(h), /^sha256:[0-9a-f]{64}$/);
  assert.equal(combineHashes({ b: "2", a: "1" }), combineHashes({ a: "1", b: "2" }));
  assert.notEqual(combineHashes({ a: "1" }), combineHashes({ a: "2" }));
  assert.deepEqual(changedFiles({ a: "1", b: "2", c: "3" }, { a: "1", b: "x", d: "4" }), ["b", "c", "d"]);
});

test("views.json edits keep the file's own formatting (drift, families, a view's shift)", () => {
  const text = '{\n  "_comment": "x",\n  "views": {\n    "side": { "file": "side.png", "right": [0, 0, -1] },\n    "top": { "file": "top.png" }\n  },\n  "families": {\n    "body": "body"\n  }\n}\n';
  const drift = { audited: "2026-09-27 gold-auditor, owner-approved", side: [{ id: "D1", rect: [1, 2, 3, 4], decides: "concept", why: "w" }], concept: [] };
  let t = setJsonKey(text, ["drift"], (ind) => driftJson(drift, ind));
  assert.equal(t, `${text.slice(0, text.lastIndexOf("\n}"))},\n  "drift": {\n    "audited": "2026-09-27 gold-auditor, owner-approved",\n    "side": [\n      { "id": "D1", "rect": [1, 2, 3, 4], "decides": "concept", "why": "w" }\n    ],\n    "concept": []\n  }\n}\n`.replace("  }\n},\n  \"drift\"", "  },\n  \"drift\""));
  assert.deepEqual(JSON.parse(t).drift, drift);
  t = setJsonKey(t, ["families", "enclosedFg"], () => "true");
  assert.match(t, /"body": "body",\n {4}"enclosedFg": true\n {2}\}/);
  t = setJsonKey(t, ["views", "top", "shift"], () => inlineJson({ up: 0.162 }));
  assert.match(t, /"top": \{ "file": "top\.png", "shift": \{ "up": 0\.162 \} \}/);
  assert.ok(t.includes('"side": { "file": "side.png", "right": [0, 0, -1] }'));
  const rm = setJsonKey(t, ["drift"], (ind) => driftJson({ ...drift, side: [] }, ind));
  assert.deepEqual(JSON.parse(rm).drift.side, []);
  assert.equal(setJsonKey(rm, ["drift"], (ind) => driftJson(drift, ind)), t);   // replace = in place
  assert.throws(() => setJsonKey(text, ["views", "none", "x"], () => "1"), /no object at views\.none/);
  assert.equal(jsonTree('{"a": [1, {"b": "}"}]}').entries[0].node.items.length, 2);
});

test("commit: explicit pathspecs of the round's files, the message carries the co-author trailer", () => {
  const c = commitCandidates({ subject: "taxi", dirRel: "out/ref/gold/taxi", round: 2, order: ORDER });
  for (const f of ["out/ref/gold/taxi/state.json", "out/ref/gold/taxi/LEDGER.md", "out/ref/gold/taxi/model-r2.mjs", "out/ref/gold/taxi/critique/r2-merged.json", "out/ref/gold/taxi/view/model-concept.png", "subjects/taxi/turnaround/views.json"]) assert.ok(c.includes(f), f);
  assert.ok(c.every((f) => !/\*|\/$/.test(f)), "files only, never a directory or a glob");
  assert.ok(!c.some((f) => /model-v\d+|steps\/|brief\//.test(f)));
  const st = { ...newState("taxi"), ledger: [{ round: 2, role: "modeller", text: "r2 modeller: model-r2 · agree .98" }] };
  assert.equal(commitMessage(st), `LLMModeling: gold taxi — r2 modeller: model-r2 · agree .98\n\n${CO_AUTHOR}\n`);
  assert.equal(CO_AUTHOR, "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>");
  const s2 = newState("x");
  addItem(s2, "open", { key: "a", text: "t" }, (o) => [o.key, o.text]);
  addItem(s2, "open", { key: "a", text: "t" }, (o) => [o.key, o.text]);
  assert.equal(s2.items.open.length, 1);
});

// ---------------------------------------------------------------------------------------------------------------------
// 2026-09-28 polish (the five-subject marathon's hand steps and faults)
// ---------------------------------------------------------------------------------------------------------------------

test("ledger one-line bug: an entry with a double space is not re-imported; repairLedger drops the copies it left", () => {
  const raw = "setup audit applied (owner-approved): decided 15 · owner: target wins;  · doctor BLOCK";
  const st = { ...newState("f"), ledger: [{ round: 0, role: "audit", text: raw }] };
  assert.deepEqual(extraLedgerLines(renderLedger(st, ["side"]), st.ledger), []);   // was: one copy per read
  const clean = oneLine(raw);
  const bad = [{ round: 0, role: "doctor", text: "setup doctor: BLOCK" }, { round: 0, role: "audit", text: raw }, { round: 0, role: "setup", text: clean },
    { round: 0, role: "audit", text: raw }, { round: 1, role: "setup", text: clean }, { round: 1, role: "modeller", text: "r1 modeller: model-r1" }, { round: 1, role: "setup", text: clean },
    { round: 1, role: "doctor", text: "setup doctor: BLOCK" }];
  const r = repairLedger(bad);
  assert.deepEqual(r.dropped, [2, 4, 6]);
  assert.deepEqual(r.entries.map((e) => e.text), ["setup doctor: BLOCK", clean, clean, "r1 modeller: model-r1", "setup doctor: BLOCK"]);   // both apply-audit runs and both doctor runs stay
  assert.deepEqual(repairLedger(r.entries).dropped, []);
});

test("NEXT (setup): the audit gate names the gold dir (not [object Object]); a spent stop rule re-briefs the auditor instead of regenerating", () => {
  const f = (over = {}) => ({ cmd: "g", flags: "", dirRel: "out/ref/gold/s", doctor: { verdict: "BLOCK", hullLevel: "WARN", stale: false }, audit: { done: true, verdict: "READY" }, briefOpen: false, critiques: {}, ...over });
  const st = newState("s");
  const gate = nextAction(st, f()).cmd;
  assert.match(gate, /^OWNER setup gate: show out\/ref\/gold\/s\/audit\/AUDIT\.md/);
  assert.doesNotMatch(gate, /object Object/);
  assert.match(nextAction(st, f({ audit: { done: true, regenerate: true } })).cmd, /^fix the images/);
  const spent = nextAction(st, f({ audit: { done: true, regenerate: true }, turnaroundStop: { spent: true, why: "3 failed whole-set regenerations (>= 3)" } }));
  assert.match(spent.cmd, /^g brief --subject s --role auditor .*READY with target-wins rulings/);
  assert.match(spent.why, /stop rule is spent/);
  assert.match(nextAction(st, f({ doctor: { hullLevel: "BLOCK" } })).cmd, /--dir out\/turnaround\/s/);
  assert.match(nextAction(st, f({ doctor: { hullLevel: "BLOCK" }, turnaroundStop: { spent: true } })).cmd, /^OWNER setup gate/);   // spent: no more repairs
});

test("commit: the subject's setup files are candidates; the headline is the newest line this commit adds, never a stale one", () => {
  const c = commitCandidates({ subject: "van", dirRel: "out/ref/gold/van", round: 1, order: ORDER, turnaroundFiles: ["side.png", "sheet.png"] });
  for (const f of ["subjects/van/subject.json", "subjects/van/turnaround/views.json", "subjects/van/turnaround/facts.json", "subjects/van/turnaround/README.md", "subjects/van/turnaround/side.png", "subjects/van/turnaround/sheet.png", "subjects/van/probes.json"]) assert.ok(c.includes(f), f);
  assert.equal(new Set(c).size, c.length);
  const st = { ...newState("van"), ledger: [{ round: 0, role: "audit", text: "setup audit applied (owner-approved)" }, { round: 1, role: "modeller", text: "r1 modeller: model-r1" }, { round: 1, role: "setup", text: "setup r1-boundary: subject.json ruleOverrides paletteZones" }] };
  assert.equal(commitMessage(st, { prev: 1, files: [] }), `LLMModeling: gold van — setup r1-boundary: subject.json ruleOverrides paletteZones\n\n- r1 modeller: model-r1\n\n${CO_AUTHOR}\n`);
  assert.equal(commitMessage(st, { prev: 3, files: ["subjects/van/turnaround/top.png", "subjects/van/subject.json"] }), `LLMModeling: gold van — files (setup r0): turnaround, subject.json\n\n${CO_AUTHOR}\n`);
  assert.match(commitMessage(st, { prev: 0 }), /^LLMModeling: gold van — setup r1-boundary/);
});

test("brief budget lines: critic / modeller / auditor state the turn budget, 'as you go', the 75 % mark and done:true", () => {
  assert.equal(budgetLine(55, "src"), "Budget: ≤ 55 turns (src). Write each item to the JSON as you go; stop measuring at 75 % of the budget (turn 41); finish with done:true.");
  const b = briefCritic({ ...common(), round: 1, seat: "opus", maxItems: 10, sheet: "s.png", pages: [], baseline: BASE, families: "body", resume: null, ledger: [], maxTurns: 55 });
  assert.match(b, /Budget: ≤ 55 turns \(your agent's maxTurns \(\.claude\/agents\/gold-critic-opus\.md\)\)\. Write each item to the JSON as you go; stop measuring at 75 % of the budget \(turn 41\); finish with done:true\./);
  const cfg = loadConfig();
  const m = briefModeller({ ...common(), round: 3, cap: 3, type: "polish", calls: cfg.rounds.types.polish.calls, rule: "r", start: "model-r2.mjs", baseline: BASE, worksheet: null, eyesFiles: [], resume: null, ledger: [], maxTurns: 120 });
  assert.match(m, /Budget: ≤ 40 turns \(the round's ≤ 40 tool calls; your agent's maxTurns 120\)\. .* start no new item at 75 % of the budget \(turn 30\); finish the report with done:true\./);
  const a = briefAuditor({ subject: "s", at: "t", dirRel: "d", concept: "c.png", prompt: null, turnaround: "t", axes: [], doctor: { file: "d.json", verdict: "PASS", rows: [] }, hull: null, start: "d/start.mjs", maxTurns: 60, stopRule: stopRuleText({ spent: true, why: "4 failed rear repairs (>= 3)" }) });
  assert.match(a, /Budget: ≤ 60 turns .* \(turn 45\)/);
  assert.match(a, /## Setup stop rule[\s\S]*SPENT — 4 failed rear repairs \(>= 3\): REGENERATE is not an option/);
  assert.match(a, /acceptBlocks/);
});

test("eye boundary: shift / override only at setup, owner / done, model before the first step, review before any critic", () => {
  const st = (phase, round = 2) => ({ ...newState("s"), phase, round });
  assert.deepEqual(eyeBoundary(st("setup", 0)), { ok: true, why: "setup", label: "setup", rebase: null });
  assert.equal(eyeBoundary(st("model")).rebase, null);
  assert.equal(eyeBoundary(st("model")).label, "r1/r2-boundary");
  assert.equal(eyeBoundary(st("model"), { briefOpen: true, steps: 0 }).rebase, "start");
  assert.equal(eyeBoundary(st("model"), { briefOpen: true, steps: 2 }).ok, false);
  assert.deepEqual([eyeBoundary(st("review")).ok, eyeBoundary(st("review")).rebase, eyeBoundary(st("review")).label], [true, "end", "r2-boundary"]);
  assert.equal(eyeBoundary(st("review"), { criticStarted: true }).ok, false);
  assert.equal(eyeBoundary(st("owner", 3)).rebase, "end");
});

test("shift: the winner by the sum of agree over every image (BASE on a tie), the table shows every image", () => {
  const rows = [
    { label: "BASE", value: 0, views: { side: 0.97, front: 0.781, rear: 0.779, concept: 0.976 } },
    { label: "#1", value: -0.15, views: { side: 0.962, front: 0.9, rear: 0.92, concept: 0.976 } },
    { label: "#2", value: -0.165, views: { side: 0.961, front: 0.906, rear: 0.925, concept: 0.976 } },
  ];
  const r = shiftWinner(rows);
  assert.equal(r.winner.label, "#2");
  assert.ok(Math.abs(r.winner.delta.side + 0.009) < 1e-9);
  const t = shiftTable(r, ["side", "front", "rear", "concept"], { view: "front", pair: "rear" });
  assert.match(t[0], /side +front +rear +concept/);
  assert.match(t.find((l) => /WINNER/.test(l)), /front right -0\.165 \/ rear \+0\.165 +\.961-\.009 +\.906\+\.125/);
  const tie = shiftWinner([{ label: "BASE", value: 0.1, views: { a: 0.9 } }, { label: "#1", value: 0.2, views: { a: 0.9005 } }]);
  assert.equal(tie.winner.label, "BASE");
  assert.equal(shiftWinner([{ label: "BASE", value: 0, views: { a: 0.9 } }, { label: "#1", value: 0.3, views: { a: 0.95 } }, { label: "#2", value: 0.2, views: { a: 0.9495 } }]).winner.label, "#2");
});

test("override: --wheels parsing, PALETTE_ZONE rows off the chain output, withOverride merges zones and keeps the WP2 shape", () => {
  assert.deepEqual(wheelsValue("6,3,equal"), { count: 6, axles: 3, diameters: "equal" });
  assert.deepEqual(wheelsValue("4,2,per-axle,0.2,0.5"), { count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.2, 0.5] });
  assert.throws(() => wheelsValue("4,5,equal"), /axles/);
  assert.throws(() => wheelsValue("4,2,big"), /equal \| per-axle/);
  assert.throws(() => wheelsValue("4,2,equal,0.5,0.2"), /diameterFrac/);
  // --tris: the subject's triangle budget, an integer 1..cap (owner 2026-09-29: detailed Generals units at 8000)
  assert.equal(trisValue("8000"), 8000);
  assert.equal(trisValue("12000"), 12000);
  for (const bad of ["12001", "0", "7999.5", "", "lots"]) assert.throws(() => trisValue(bad), /--tris .*1\.\.12000/);
  assert.deepEqual(withOverride({}, "tris", 8000, "owner 2026-09-29: detailed like the combat bike").tris, { value: 8000, evidence: "owner 2026-09-29: detailed like the combat bike" });
  // WF v8 Generals units: --running tracks (road wheels / stations, 0,0 = hidden) and skids (no wheels)
  assert.deepEqual(wheelsValue("0,0", "tracks"), { count: 0, axles: 0, diameters: "equal", running: "tracks" });
  assert.deepEqual(wheelsValue("10,5,equal", "tracks"), { count: 10, axles: 5, diameters: "equal", running: "tracks" });
  assert.deepEqual(wheelsValue(null, "skids"), { count: 0, axles: 0, diameters: "equal", running: "skids" });
  assert.throws(() => wheelsValue("4,2,equal", "skids"), /stands on no wheels/);
  assert.throws(() => wheelsValue("0,0,equal"), /1 <= axles <= count/);
  assert.throws(() => wheelsValue("10,0,equal", "tracks"), /stations/);
  assert.throws(() => wheelsValue("4,2,equal", "hover"), /tracks \| skids \| wheels/);
  const roles = withOverride(withOverride(undefined, "roles", { extra: ["turret"] }, "turret block"), "roles", { extra: ["turret", "gun"] }, "gun barrel");
  assert.deepEqual(roles.roles, { value: { extra: ["turret", "gun"] }, evidence: "turret block; gun barrel" });
  const out = [
    "pass false tris 1414 budget 4000 parts 40",
    'VIOLATION PALETTE_ZONE stripe_box_l "zone \\"stripe\\" on 7 part(s)" one of: body, glass',
    'VIOLATION PALETTE_ZONE locker_la "zone \\"locker\\" on 3 part(s)" one of: body',
    'VIOLATION VEH_WHEELS tyre_fr "6 wheels" ...',
  ].join("\n");
  assert.deepEqual(paletteZoneViolations(out), { stripe: { parts: 7, example: "stripe_box_l" }, locker: { parts: 3, example: "locker_la" } });
  const a = withOverride(undefined, "paletteZones", { extra: ["stripe"] }, "stripe = 7 part(s)");
  assert.match(a._comment, /WP2/);
  assert.deepEqual(a.paletteZones, { value: { extra: ["stripe"] }, evidence: "stripe = 7 part(s)" });
  const b = withOverride(a, "paletteZones", { extra: ["stripe", "well"] }, "well = the wheel wells");
  assert.deepEqual(b.paletteZones, { value: { extra: ["stripe", "well"] }, evidence: "stripe = 7 part(s); well = the wheel wells" });
  const w = withOverride(b, "wheels", { count: 6, axles: 3, diameters: "equal" }, "3 per flank");
  assert.deepEqual(Object.keys(w), ["_comment", "paletteZones", "wheels"]);
  assert.equal(a.paletteZones.value.extra.length, 1);   // not mutated
});

test("owner packet: proposed drift rects deduplicated, the ones already in views.json dropped, each with a ready drift add line", () => {
  const views = { side: { file: "side.png" }, front: { file: "front.png" } };
  const crit = { items: [
    { sev: "MINOR", key: "drift:side", want: "concept", basis: "concept", at: { image: "side.png", rect: [270, 330, 352, 380], claim: "model-only" }, note: "bar drawn 0.3 m ahead" },
    { sev: "MINOR", key: "drift:concept", want: "decides front", now: null, basis: "concept", at: { image: "concept", rect: [70, 535, 90, 640], claim: "ref-only" }, note: "far cab edge fans" },
    { sev: "MAJOR", key: "part:cab.size.z", want: 2, at: { image: "side", rect: [0, 0, 5, 5], claim: "edge" } },
  ] };
  const cd = critiqueDrift(crit, 2, "opus", views);
  assert.deepEqual(cd.map((p) => [p.src, p.image, p.decides]), [["r2 opus 1", "side", "concept"], ["r2 opus 2", "concept", "front"]]);
  const sources = [...cd,
    { src: "r2 modeller 1", round: 2, image: "side", rect: [272, 331, 350, 381], decides: "concept", why: "same bar" },
    { src: "audit D4", round: 0, image: "front", rect: [10, 10, 50, 50], decides: "concept", why: "in views.json" },
    { src: "r1 fable 3", round: 1, image: "concept", rect: [300, 180, 800, 330], decides: "side", why: 'fanning "roof"' }];
  const p = driftProposals(sources, { front: [{ id: "D4", rect: [10, 10, 50, 50] }] }, { subject: "van" });
  assert.equal(p.length, 3);
  const side = p.find((e) => e.image === "side");
  assert.deepEqual(side.sources, ["r2 opus 1", "r2 modeller 1"]);
  assert.match(side.cmd, /^node scripts\/v7\/gold\.mjs drift add --subject van --image side --rect 270,330,352,380 --decides concept --why "bar drawn 0\.3 m ahead \(proposed: r2 opus 1, r2 modeller 1\)" --owner-approved$/);
  assert.ok(p.every((e) => !e.cmd.includes('"roof"')));   // quotes inside --why are made safe
  const pk = ownerPacket({ subject: "van", at: "t", round: 3, phase: "owner", stop: "STOP: OWNER", views: {}, order: ORDER, bar: 0.97, items: { ...newState("van").items, decided: [{ key: "fact:accepted-blocks", value: "residual-W", evidence: "owner" }] }, runs: [], sheet: "s", pages: [], snapshot: "m", ledgerFile: "L", drift: p, rulings: setupRulings({ decided: [{ key: "fact:accepted-blocks", value: "residual-W", evidence: "owner" }, { key: "knob:W", value: 2 }] }) });
  assert.match(pk, /## Drift rects proposed, not in views\.json \(3;/);
  assert.match(pk, /`node scripts\/v7\/gold\.mjs drift add --subject van --image side/);
  assert.match(pk, /## Setup rulings on record\n- fact:accepted-blocks = residual-W/);
  assert.match(pk, /Decide: accept/);
  assert.doesNotMatch(ownerPacket({ subject: "van", at: "t", round: 1, phase: "model", views: {}, order: ORDER, bar: 0.97, items: newState("van").items, runs: [], sheet: "s", pages: [], snapshot: "m", ledgerFile: "L" }), /Decide: accept/);
  assert.match(ownerBatch([{ subject: "van", phase: "owner", round: 3, minAgree: ".906 front", owner: 2, drift: 3, rulings: 1, file: "out/ref/gold/van/OWNER.md" }], "t"), /\| van \| owner r3 \| \.906 front \| 2 \| 3 \| 1 \|/);
});

test("setup stop rule: 3 failed sets or 3 failed repairs of one view spend it; rejudge / fix records and KEEPs do not count", () => {
  const T = setupTargetsOf(loadConfig());
  const good = { views: { side: { viewOnly: 0.01 } }, conceptOnlyBlob: 0.01, residuals: {}, aspect: { HoverW: 0.01, LoverW: 0 } };
  const bad = { ...good, aspect: { HoverW: -0.084, LoverW: 0 } };
  assert.deepEqual(setupMisses(bad, T), ["aspect H/W -8.4 %"]);
  const misses = (sm) => setupMisses(sm, T);
  const tst = (attempts, repairs = []) => ({ attempts, repairs });
  assert.equal(setupStopOf(tst([{ summary: bad }, { error: "x" }, { summary: good }]), { misses }).spent, false);
  const sets = setupStopOf(tst([{ summary: bad }, { error: "x" }, { summary: bad }]), { misses });
  assert.deepEqual([sets.spent, sets.setsSpent, sets.sets], [true, true, 3]);
  assert.match(sets.why, /3 failed whole-set regenerations \(>= 3\)/);
  const rep = (id, view, verdict) => ({ id, view, verdict });
  const views = setupStopOf(tst([{ summary: good }], [rep("repair-1-rear-gemini-mirror", "rear", "REVERT"), rep("repair-2-rear-gpt-mirror", "rear", "FAILED"), rep("rejudge-3-repair-1", "rear", "REVERT"),
    rep("fix-4-rear", "rear", "REVERT"), rep("repair-5-top-gpt-proportion", "top", "REVERT"), rep("repair-6-rear-gpt-proportion", "rear", "KEEP")]), { misses });
  assert.deepEqual([views.spent, views.views], [false, { rear: 2, top: 1 }]);
  const spentRear = setupStopOf(tst([{ summary: good }], [rep("repair-1-rear-a", "rear", "REVERT"), rep("repair-2-rear-b", "rear", "REVERT"), rep("repair-3-rear-c", "rear", "REVERT")]), { misses });
  assert.deepEqual([spentRear.spent, spentRear.setsSpent, spentRear.spentViews], [true, false, ["rear"]]);
  assert.match(stopRuleText(null), /No turnaround work folder/);
  assert.match(stopRuleText(views), /not spent/);
});

// ---------------------------------------------------------------------------------------------------------------------
// 2026-09-28 blind usability review (research/v7/SKILL-REVIEW-fable.md): a new subject's chain, the owner's BLOCK call,
// the EDIT path, the eye rulings in the packet
// ---------------------------------------------------------------------------------------------------------------------

test("NEXT (setup): a new subject's chain step first; the EDIT path names turnaround.mjs fix + install --force and the concept v2; a standing BLOCK after apply-audit is the owner's", () => {
  const f = (over = {}) => ({ cmd: "g", flags: "", doctor: { verdict: "WARN", hullLevel: "PASS", stale: false }, audit: { done: true, verdict: "READY" }, briefOpen: false, critiques: {}, ...over });
  const st = { ...newState("s"), phase: "setup" };
  assert.equal(nextAction(st, f({ chain: { step: 1, cmd: "node scripts/solve-camera.mjs s --image refs/s.png", why: "chain 1" }, doctor: null })).cmd, "node scripts/solve-camera.mjs s --image refs/s.png");
  const edit = nextAction(st, f({ audit: { done: true, semantic: true } })).cmd;
  assert.match(edit, /turnaround\.mjs fix --subject s --dir out\/turnaround\/s --view <v> --image <edited png> --why .* --rects/);
  assert.match(edit, /install --subject s --dir out\/turnaround\/s --force/);
  assert.match(edit, /refs\/s\.v2\.png \+ refs\/s\.v2\.README\.md \+ subject\.json paths\.target/);
  assert.match(nextAction(st, f({ audit: { done: true, regenerate: true } })).cmd, /REGENERATE: node scripts\/v7\/turnaround\.mjs repair --subject s --dir out\/turnaround\/s --view <v>/);
  // applied + BLOCK: never the gate again (the loop), never an id list for the orchestrator to type on its own
  const own = nextAction(st, f({ applied: true, doctor: { verdict: "BLOCK", hullLevel: "PASS", blocks: ["residual-W", "aspect"], stale: false } }));
  assert.match(own.cmd, /^OWNER: doctor BLOCK row\(s\) residual-W,aspect stand after the setup audit — the owner accepts them \(g apply-audit --subject s --owner-approved --owner-note "<the owner's words>" --accept-blocks residual-W,aspect\)/);
  assert.match(own.cmd, /a marathon parks the subject/);
  assert.match(nextAction(st, f({ applied: false, doctor: { verdict: "BLOCK", hullLevel: "PASS", blocks: ["residual-W"], stale: false } })).cmd, /^OWNER setup gate/);
  assert.match(nextAction(st, f({ applied: true })).cmd, /^OWNER setup gate/);   // applied without a BLOCK: phase model already (never reached)
});

test("owner packet: every applied override / shift ledger line listed as an eye ruling; BASE-kept sweeps and other lines are not", () => {
  const ledger = [
    { round: 1, role: "setup", text: "setup r1-boundary: subject.json ruleOverrides wheels (per-axle) · chain PASS" },
    { round: 2, role: "eyes", text: "eyes: r2-boundary eye change: views.json front / rear shift.right +0.000 -> -0.150 / +0.150 (why)" },
    { round: 2, role: "eyes", text: "eyes: r2-boundary shift sweep front right (-0.1): BASE kept, views.json unchanged — why" },
    { round: 1, role: "eyes", text: "eyes: changed at the round boundary before r1 (x) · re-baselined" },
    { round: 0, role: "setup", text: "setup: new subject (gold.mjs new)" },
  ];
  const r = eyeRulings(ledger);
  assert.deepEqual(r.map((x) => [x.round, x.kind]), [[1, "override"], [2, "shift"]]);
  const pk = ownerPacket({ subject: "van", at: "t", round: 2, phase: "owner", stop: "", views: {}, order: ORDER, bar: 0.97, items: newState("van").items, runs: [], sheet: "s", pages: [], snapshot: "m", ledgerFile: "L", drift: [], rulings: [], eyeRulings: r });
  assert.match(pk, /Boundary eye changes \(gold\.mjs override \/ shift — owner rulings pending ratification\):\n- r1 override: setup r1-boundary: subject\.json ruleOverrides wheels/);
  assert.match(pk, /- r2 shift: eyes: r2-boundary eye change: views\.json front/);
  assert.doesNotMatch(pk, /BASE kept/);
  const none = ownerPacket({ subject: "van", at: "t", round: 2, phase: "owner", stop: "", views: {}, order: ORDER, bar: 0.97, items: newState("van").items, runs: [], sheet: "s", pages: [], snapshot: "m", ledgerFile: "L", drift: [], rulings: [] });
  assert.doesNotMatch(none, /Boundary eye changes/);   // no eyeRulings passed: the packet as before
});

test("commit: the concept, its prompt README and the concept frame are candidates of a new subject (extra)", () => {
  const c = commitCandidates({ subject: "cm", dirRel: "out/ref/gold/cm", round: 0, order: ORDER, extra: ["refs/cm.png", "refs/cm.README.md", "subjects/cm/layout.measured.json"] });
  for (const f of ["refs/cm.png", "refs/cm.README.md", "subjects/cm/layout.measured.json", "subjects/cm/turnaround/facts.json"]) assert.ok(c.includes(f), f);
  assert.ok(!commitCandidates({ subject: "cm", dirRel: "out/ref/gold/cm", round: 0, order: ORDER }).includes("refs/cm.png"));
});

test("CLI: brief --role auditor refuses without the concept prompt (names the file and --no-prompt); apply-audit --accept-blocks audit without a list never invites naming ids", () => {
  // taxi has no refs/taxi.README.md; both runs refuse before any subject file is written (a temp --dir in phase setup)
  const dir = tmpDir("setup");
  fs.writeFileSync(path.join(dir, "state.json"), serializeState(newState("taxi")));
  fs.writeFileSync(path.join(dir, "doctor.json"), JSON.stringify({ verdict: "PASS", blocks: 0, warns: 0, at: "t", rows: [] }));
  const b = gold(["brief", "--subject", "taxi", "--role", "auditor", "--dir", dir]);
  assert.equal(b.status, 1, b.stdout + b.stderr);
  assert.match(b.stdout, /REFUSED: no concept prompt: refs\/taxi\.README\.md with a "## Full prompt" fenced block .* or pass --no-prompt/);
  assert.ok(!fs.existsSync(path.join(dir, "brief")));
  fs.mkdirSync(path.join(dir, "audit"));
  fs.writeFileSync(path.join(dir, "audit", "audit.json"), JSON.stringify({ done: true, semantic: [], views: {}, blocks: [], open: [] }));
  fs.writeFileSync(path.join(dir, "audit", "views.drift.json"), "{}");
  fs.writeFileSync(path.join(dir, "audit", "probes.json"), "[]");
  const a = gold(["apply-audit", "--subject", "taxi", "--owner-approved", "--owner-note", "x", "--accept-blocks", "audit", "--dir", dir]);
  assert.equal(a.status, 1, a.stdout + a.stderr);
  assert.match(a.stdout, /REFUSED: --accept-blocks audit: audit\.json has no acceptBlocks list — omit the flag when the auditor listed none \(naming ids is the owner's/);
  assert.doesNotMatch(a.stdout, /name the doctor BLOCK row ids/);
  fs.rmSync(dir, { recursive: true, force: true });
});
