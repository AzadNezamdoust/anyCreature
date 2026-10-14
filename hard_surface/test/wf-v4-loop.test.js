// WORKFLOW v4 — V4-3 LOOP (research/WF-V4-PLAN.md): scripts/loop.mjs with the scripted `fake` seat, no images.
// Hermetic: starts are the frozen fixtures (test/fixtures/v4/start-knobs-pickup.mjs = the template's output, and
// test/fixtures/v4/work-pickup.mjs = the Opus reference, body bottom varied for the guard cases); refs/, subjects/
// and classes/ are read only; every loop writes under test/.tmp-wf-v4-loop-<pid>/.
process.env.LLMM_SUBJECT = "pickup";
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import { runLoop, PROMPT_MAX, SHOW, applyReply, addKnobEntries, knobifyCalls, judge } from "../scripts/loop.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TMP = path.join(ROOT, "test", `.tmp-wf-v4-loop-${process.pid}`);
const WORK = fs.readFileSync(path.join(ROOT, "test/fixtures/v4/work-pickup.mjs"), "utf8");
const LIVE = ["subjects/pickup/module.mjs", "subjects/facade_brick/facade.mjs"].map((f) => path.join(ROOT, f));
const hash = (f) => createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const liveBefore = LIVE.map(hash);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

/** The work module with its body bottom at `f` x H (gate PASS over 0.24..0.26), three levels under ROOT. */
function body(f) {
  const file = path.join(TMP, "fx", `body-${f}.mjs`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const text = WORK.replace("const bodyBot = 0.24 * H;", `const bodyBot = ${f} * H;`);
  assert.notEqual(text, WORK, "the body-bottom line moved");
  fs.writeFileSync(file, text);
  return file;
}

/** Run the loop with a scripted fake seat. */
async function run(name, script, opts) {
  const dir = path.join(TMP, name);
  fs.mkdirSync(dir, { recursive: true });
  const scriptFile = path.join(dir, "script.json");
  fs.writeFileSync(scriptFile, JSON.stringify(script));
  process.env.LLMM_FAKE_SCRIPT = scriptFile;
  try {
    const r = await runLoop({ subjectId: "pickup", seat: "fake", images: false, turnaround: false, outDir: path.join(dir, "out"), workDir: path.join(dir, "work"), log: () => {},
      // the target stop fires on any IoU >= band with no MISSING row (ruling 2026-09-26); tests of the other stops disable it
      targetBand: 1.01,
      // V5-1: these V4 tests keep their bands — no per-item exact stop, no similarity knobs (tested in wf-v51)
      exactStop: false, similarity: false, ...opts });
    return { r, out: path.join(dir, "out") };
  } finally {
    delete process.env.LLMM_FAKE_SCRIPT;
  }
}
const read = (out, step, file) => fs.readFileSync(path.join(out, String(step), file), "utf8");
const verdict = (out, step) => JSON.parse(read(out, step, "verdict.json"));
const NOOP = { reply: "CHANGE: nothing to add" };

let regress = null;
const regressRun = () => (regress ??= run("regress", [NOOP, { module: body(0.26) }, { module: body(0.26) }], { from: path.relative(ROOT, body(0.25)), K: 4 }));

test("V4-3 (a) a regressing edit is rejected, the module reverts to best and the next prompt says what got worse", async () => {
  const { r, out } = await regressRun();
  const v1 = verdict(out, 1);
  assert.equal(v1.accepted, false);
  assert.ok(v1.iou < r.steps[0].iou, `${v1.iou} < ${r.steps[0].iou}`);
  assert.match(v1.verdict, /^REJECTED — whole IoU 0\.96\d+ is not >= best 0\.97\d+ \+ 0\.001/);
  assert.equal(r.best.iou, r.steps[0].iou);
  const code = (s) => s.replace(/^import .*$/m, "");   // the kernel import depth differs per folder
  assert.equal(code(read(out, "", "best.mjs")), code(read(out, "start", "module.mjs")), "best = the start module, byte for byte");
  const p2 = read(out, 2, "prompt.md");
  assert.match(p2, /last verdict: REJECTED — whole IoU [^\n]*reverted to the best one/);
  for (const [a, b] of LIVE.map((f, i) => [hash(f), liveBefore[i]])) assert.equal(a, b, "live modules untouched");
});

test("V4-3 (b) two consecutive rejects stop the loop before K", async () => {
  const { r } = await regressRun();
  assert.equal(r.stop, "2 consecutive rejects");
  assert.equal(r.exitCode, 1);
  assert.deepEqual(r.steps.map((s) => s.step), ["start", "build", "1", "2"]);
  assert.equal(r.steps.filter((s) => s.step !== "start" && s.accepted).length, 0);
});

test("V4-3 (c) two accepted gains under 0.003 stop on the plateau", async () => {
  const { r } = await run("plateau", [{ module: body(0.255) }, { module: body(0.25) }, { module: body(0.245) }], { from: path.relative(ROOT, body(0.26)), K: 4 });
  // V4-5A: the cab-relative door seam builds on this start too (it was readyDropped), so BUILD takes the first reply
  assert.deepEqual(r.steps.map((s) => s.step), ["start", "build", "1", "2"], JSON.stringify(r.iouTrace));
  assert.deepEqual(r.readyDropped ?? [], [], "no READY call dropped");
  const loopSteps = r.steps.slice(1);
  for (const s of loopSteps) assert.ok(s.accepted && s.gain >= 0.001 && s.gain < 0.003, JSON.stringify(s));
  assert.match(r.stop, /^plateau/);
  assert.ok(r.best.iou > r.steps[0].iou);
});

test("V4-3 (d) target stop on the Opus work module: no seat call (floor override, see the V4-3 receipt)", async () => {
  // MVP-STUB: the class residualFloor {0.045 m, 900 px} leaves 4 rows on this module (classes/vehicle.json
  // _residualFloor_comment), so it never reads as "target reached"; the stop rule is proven at a floor above them.
  const { r, out } = await run("target", [{ reply: "CHANGE: must not be called" }], { from: "test/fixtures/v4/work-pickup.mjs", K: 4, targetFloor: { metres: 0.09, px: 2100 }, targetBand: null });
  assert.equal(r.stop, "target");
  assert.equal(r.exitCode, 0);
  assert.deepEqual(r.steps.map((s) => s.step), ["start"]);
  assert.equal(r.best.target, true);
  assert.ok(r.best.iou >= 0.96 && r.best.pass);
  assert.equal(fs.existsSync(path.join(out, "build")), false);
});

let build = null;
const buildRun = () => (build ??= run("build", [{ echo: "READY" }, { reply: "CHANGE: none" }], { K: 1 }));

test("V4-3 (e) BUILD and LOOP prompts on the pickup stay <= 8 kB; rows follow ruling R2", async () => {
  const { r, out } = await buildRun();
  const steps = r.promptBytes.map((p) => p.step);
  assert.deepEqual(steps, ["build", "1"]);
  for (const p of r.promptBytes) {
    assert.ok(p.bytes <= PROMPT_MAX, `${p.step}: ${p.bytes} bytes`);
    assert.equal(Buffer.byteLength(read(out, p.step, "prompt.md"), "utf8"), p.bytes);
  }
  const loop = read(out, 1, "prompt.md");
  const rows = [...loop.matchAll(/^\d+\. RESIDUAL .* \((\d+) px\)$/gm)].map((m) => Number(m[1]));
  assert.ok(rows.length >= 1 && rows.length <= SHOW.rows, `${rows.length} rows`);
  for (let i = 1; i < rows.length; i += 1) assert.ok(rows[i - 1] >= rows[i] || /MISSING/.test(loop), "ranked by px x weight");
  // V4-6 item 3: each open row carries ONE edit (knob-level fixes are ABSORBed by a harness re-FIT first)
  assert.equal((loop.match(/^ {3}edit: /gm) ?? []).length, rows.length, "one edit line per row");
  assert.match(loop, /^ *\d+\| /m, "cited module lines, numbered");
});

test("V4-3 (f) R1: FIT -> BUILD (READY calls read KNOBS) -> knob entries added -> re-FIT moves them", async () => {
  const { r, out } = await buildRun();
  const start = verdict(out, "start");
  assert.ok(start.fit.to >= 0.95, JSON.stringify(start.fit));
  const b = verdict(out, "build");
  assert.equal(b.accepted, true, b.verdict);
  assert.ok(b.knobsAdded.length >= 10, `${b.knobsAdded.length} knobs added`);
  const text = read(out, "build", "module.mjs");
  const block = text.slice(text.indexOf("export const KNOBS"), text.indexOf("\n};", text.indexOf("export const KNOBS")));
  for (const n of b.knobsAdded) {
    assert.match(block, new RegExp(`\\n\\s*${n}: \\{ v: `), `${n} in the KNOBS block`);
    assert.match(text, new RegExp(`KNOBS\\.${n}\\.v`), `${n} read by a call`);
  }
  assert.ok(typeof b.refit === "object" && b.refit.evals > 0, JSON.stringify(b.refit));
  const moved = b.knobsAdded.filter((n) => b.refit.values[n] !== b.knobStart[n]);
  assert.ok(moved.length >= 1, "re-FIT moved at least one added knob");
  assert.equal(r.best.pass, true);
  assert.equal(r.best.coverage, "5/5");
  assert.ok(r.best.iou > start.iou, `${start.iou} -> ${r.best.iou}`);
});

test("V4-3 helpers: knobify dedupes |values|, addKnobEntries adds only offered names, insert block lands before return", () => {
  const offered = {};
  const [c] = knobifyCalls([{ what: "windshield pane", call: "f([[-0.8, 1.6], [0.8, 1.6]], 2)" }], { offered, span: 0.1 });
  assert.equal(c.call, "f([[-KNOBS.rc_windshield1.v, KNOBS.rc_windshield2.v], [KNOBS.rc_windshield1.v, KNOBS.rc_windshield2.v]], 2)");
  assert.deepEqual(offered.rc_windshield1, { v: 0.8, min: 0.7, max: 0.9, what: "windshield pane" });
  const mod = "export const KNOBS = {\n  a: { v: 1, min: 0, max: 2, unit: \"m\" },\n};\nexport const meta = {};\nexport function build() {\n  const parts = [];\n  return parts;\n}\n";
  const ins = applyReply(mod, "```js\nparts.push(KNOBS.rc_windshield1.v, KNOBS.zz.v);\n```\nCHANGE: x");
  assert.match(ins.text, /\n {2}parts\.push\(KNOBS\.rc_windshield1\.v, KNOBS\.zz\.v\);\n {2}return parts;/);
  const added = addKnobEntries(ins.text, offered);
  assert.deepEqual(added.added, ["rc_windshield1"]);
  assert.deepEqual(added.unknown, ["zz"]);
  assert.match(added.text, /\n {2}rc_windshield1: \{ v: 0\.8, min: 0\.7, max: 0\.9, unit: "m" \},[^\n]*\n\};/);
  const base = { loads: true, iou: 0.95, blocking: 0, codes: [], coverage: { frac: 1, have: 5, total: 5, missing: [] }, minZone: 0.7, tris: 1, triBudget: 9 };
  assert.equal(judge({ ...base, iou: 0.9505 }, base).accept, false, "a gain under 0.001 is not strictly better");
  assert.equal(judge({ ...base, iou: 0.9, blocking: 0 }, { ...base, blocking: 1, codes: ["V12_CENSUS"] }).accept, true, "a higher tier decides");
});
