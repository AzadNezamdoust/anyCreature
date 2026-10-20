// node --test scripts/v7/newsubject.test.mjs — `gold.mjs new` (scripts/v7/newsubject.mjs) without any GPT / Gemini call:
// the prompt composition, the size parse, facts.json the turnaround templates accept, the families proposal, a --dry run
// into a temp root (with and without --concept), an injected generator for the non-dry path, the refusals.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

import { STYLE } from "../make-target.mjs";
import { ROOT, checkState } from "./goldlib.mjs";
import { ISO_SENTENCE, checkFacts, loadTemplates, sheetPrompt, styleOrtho } from "./turnaround.mjs";
import { DEFAULT_STYLE, STYLE_NAMES, styleOf, styleText } from "./styles.mjs";
import { familyTable } from "../v6/ortho.mjs";
import { HIDDEN_FACE, chainLines, conceptPrompt, factsFrom, newSubject, parseSize, proposeFamilies } from "./newsubject.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "newsubject-test-"));
const DESC = "A chunky cartoon cement mixer truck: a short boxy white cab at the front, a big orange mixer drum tilted up toward the rear, a dark grey chute at the rear end. Tyres dark charcoal, hubs light grey, three axles. About 8.5 m long, 2.5 m wide and 3.9 m tall; the wheels clearly visible.";
const CONCEPT = path.join(ROOT, "refs", "forklift.png");   // read only (a --concept stand-in)
const FENCE = "```";

test("the concept prompt: the description, the hidden-face rule, then make-target.mjs STYLE verbatim", () => {
  const p = conceptPrompt(`  ${DESC}\n`);
  assert.ok(p.startsWith("A chunky cartoon cement mixer truck:"));
  assert.ok(p.endsWith(` ${HIDDEN_FACE} ${STYLE}`));
  assert.match(HIDDEN_FACE, /faces away and is not visible in this view: never move it onto a visible face/);
  assert.doesNotMatch(p, /\n/);
});

test("the stated size: L / W / H, the size sentence split off (8.5 stays one number)", () => {
  const z = parseSize(DESC);
  assert.deepEqual([z.L, z.W, z.H], [8.5, 2.5, 3.9]);
  assert.deepEqual(z.sentences, ["About 8.5 m long, 2.5 m wide and 3.9 m tall; the wheels clearly visible."]);
  assert.match(z.rest, /three axles\.$/);
  const v = parseSize("A van 5 metres long and 2 m high.");
  assert.deepEqual([v.L, v.W, v.H], [5, null, 2]);
});

test("facts.json from the description: every key the turnaround templates need, shapes from the stated size", () => {
  const f = factsFrom({ subject: "cm", noun: "cement mixer", desc: DESC });
  checkFacts(f);
  assert.deepEqual([f.dims.L, f.dims.W, f.dims.H], [8.5, 2.5, 3.9]);
  assert.equal(f.shape.side, "in this view the cement mixer is 2.18 times as long as it is tall");
  assert.equal(f.shape.top, "in this view it is 3.40 times as long as it is wide");
  assert.match(f.proportions, /^About 8\.5 m long.*\(length : width : height = 3\.40 : 1 : 1\.56\)$/);
  assert.doesNotMatch(sheetPrompt(loadTemplates(), f), /\{/);
});

test("families proposal off the concept: body = the most common not-dark colour, dark = the darkest, the rest f2..", async () => {
  const P = await proposeFamilies(CONCEPT);
  const names = Object.keys(P.table);
  assert.equal(names[0], "body");
  assert.ok(names.includes("dark"));
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(P.table.body.slice(i, i + 2), 16));
  assert.ok(r > 200 && g > 170 && b < 80, `forklift body yellow, got ${P.table.body}`);
  assert.ok(Object.values(P.shares).every((x) => x >= 2));
  familyTable([], { table: P.table, body: "body" });   // a valid views.json table
});

test("new --dry into a temp root: every setup file, the README's Full prompt block (the auditor brief's regex), a valid state; refusals", async () => {
  const root = tmp();
  const r = await newSubject({ root, subject: "cm", klass: "vehicle", desc: DESC, dry: true, concept: CONCEPT });
  assert.deepEqual(r.files, ["refs/cm.png", "refs/cm.README.md", "subjects/cm/subject.json", "subjects/cm/turnaround/views.json", "subjects/cm/turnaround/facts.json", "subjects/cm/prior.json", "out/ref/gold/cm/state.json", "out/ref/gold/cm/LEDGER.md"]);
  const m = await sharp(path.join(root, "refs", "cm.png")).metadata();
  assert.deepEqual([m.width, m.height], [1024, 1024]);
  const readme = fs.readFileSync(path.join(root, "refs", "cm.README.md"), "utf8");
  assert.match(readme, /^## Full prompt[\s\S]*?```/m);
  assert.ok(readme.includes(`${FENCE}\n${r.prompt}\n${FENCE}`));
  assert.match(readme, /generator: none \(gold\.mjs new --dry --concept/);
  const subj = JSON.parse(fs.readFileSync(path.join(root, "subjects", "cm", "subject.json"), "utf8"));
  assert.deepEqual(subj.paths, { target: "refs/cm.png", camera: "subjects/cm/camera.json", layoutMeasured: "subjects/cm/layout.measured.json" });
  const views = JSON.parse(fs.readFileSync(path.join(root, "subjects", "cm", "turnaround", "views.json"), "utf8"));
  assert.deepEqual(Object.keys(views.views), ["side", "front", "rear", "top"]);
  assert.deepEqual(views.views.top, { file: "top.png", right: [0, 0, -1], up: [-1, 0, 0] });
  assert.deepEqual(views.anchor, { dim: "W", m: 2.5 });
  assert.equal(views.families.spanOpen, 2);
  assert.match(views.families._table, /^PROPOSAL/);
  checkFacts(JSON.parse(fs.readFileSync(path.join(root, "subjects", "cm", "turnaround", "facts.json"), "utf8")));
  const st = JSON.parse(fs.readFileSync(path.join(root, "out", "ref", "gold", "cm", "state.json"), "utf8"));
  assert.deepEqual(checkState(st), []);
  assert.equal(st.phase, "setup");
  assert.match(st.ledger[0].text, /^setup: new subject \(gold\.mjs new --dry\)/);
  assert.match(fs.readFileSync(path.join(root, "out", "ref", "gold", "cm", "LEDGER.md"), "utf8"), /setup: new subject/);
  assert.equal(r.chain.length, 11);
  assert.match(r.chain[3], /^4\. provisional frame: node scripts\/v7\/hull\.mjs --subject cm --write-frame --from facts$/);
  assert.match(r.chain[8], /scaffold\.mjs --subject cm --shape sedan\|box\|bus\|pickup\|machine/);
  // refusals: the frozen TARGET, no stated size, a bad id or class
  await assert.rejects(newSubject({ root, subject: "cm", desc: DESC, dry: true }), /refs\/cm\.png exists \(a TARGET is frozen\)/);
  await assert.rejects(newSubject({ root, subject: "cm2", desc: DESC.replace(/About.*$/, "Big."), dry: true }), /states no L \/ W \/ H/);
  await assert.rejects(newSubject({ root, subject: "Bad-Id", desc: DESC, dry: true }), /lower-case/);
  await assert.rejects(newSubject({ root, subject: "b1", klass: "building", desc: DESC, dry: true }), /--class building: vehicle/);
  // --dry without a concept: the prompt only, families a placeholder
  const r2 = await newSubject({ root, subject: "cm3", desc: DESC, dry: true });
  assert.ok(!r2.files.includes("refs/cm3.png"));
  assert.match(JSON.parse(fs.readFileSync(path.join(root, "subjects", "cm3", "turnaround", "views.json"), "utf8")).families._table, /^PLACEHOLDER/);
  assert.match(fs.readFileSync(path.join(root, "refs", "cm3.README.md"), "utf8"), /generator: none yet/);
  fs.rmSync(root, { recursive: true, force: true });
});

test("new (not --dry) with an injected generator: text to image (no refs), the raw padded to a 1024 square, a failed generation writes nothing", async () => {
  const root = tmp();
  const calls = [];
  const generate = async (o) => {
    calls.push(o);
    await sharp({ create: { width: 400, height: 300, channels: 3, background: { r: 250, g: 200, b: 20 } } }).png().toFile(o.out);
    return { ok: true, out: o.out, provenance: { agentModel: "stub" } };
  };
  await newSubject({ root, subject: "gx", desc: DESC, gen: "gpt", generate });
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0].refs, []);
  assert.equal(calls[0].gen, "gpt");
  assert.equal(fs.readFileSync(calls[0].promptFile, "utf8").trim(), conceptPrompt(DESC));
  const img = await sharp(path.join(root, "refs", "gx.png")).raw().toBuffer({ resolveWithObject: true });
  assert.deepEqual([img.info.width, img.info.height], [1024, 1024]);
  assert.deepEqual([...img.data.subarray(0, 3)], [255, 255, 255]);   // the padding is white
  assert.match(fs.readFileSync(path.join(root, "refs", "gx.README.md"), "utf8"), /generator: GPT image generation through scripts\/v7\/imagegen\.mjs --gen gpt \(text to image, no reference; agent stub\)/);
  const fail = async () => ({ ok: false, provenance: { reason: "timeout" }, provenanceFile: null });
  await assert.rejects(newSubject({ root, subject: "gy", desc: DESC, generate: fail }), /generated no image \(timeout/);
  assert.ok(!fs.existsSync(path.join(root, "subjects", "gy")) && !fs.existsSync(path.join(root, "refs", "gy.png")));
  fs.rmSync(root, { recursive: true, force: true });
});

test("CLI: gold.mjs new --dry prints the numbered chain; --root / --concept only with --dry; a missing --desc-file is a usage error", () => {
  const root = tmp();
  const df = path.join(root, "desc.txt");
  fs.writeFileSync(df, DESC);
  const run = (argv) => spawnSync(process.execPath, [path.join(HERE, "gold.mjs"), ...argv], { cwd: ROOT, encoding: "utf8", windowsHide: true });
  const r = run(["new", "--subject", "cm", "--class", "vehicle", "--desc-file", df, "--dry", "--root", root]);
  assert.equal(r.status, 0, r.stdout + r.stderr);
  for (const l of chainLines("cm")) assert.ok(r.stdout.includes(`  ${l}`), l);
  assert.ok(fs.existsSync(path.join(root, "subjects", "cm", "subject.json")));
  assert.equal(run(["new", "--subject", "cm", "--desc-file", df, "--root", root]).status, 3);
  assert.equal(run(["new", "--subject", "cm", "--desc-file", df, "--concept", CONCEPT]).status, 3);
  assert.equal(run(["new", "--subject", "cm", "--dry"]).status, 3);
  fs.rmSync(root, { recursive: true, force: true });
});

test("styles.json: cartoon = the frozen make-target.mjs STYLE; every style keeps the camera + background sentences; no game named", () => {
  assert.equal(DEFAULT_STYLE, "cartoon");
  assert.deepEqual(STYLE_NAMES, ["cartoon", "generals", "fps", "scifi_toon", "grounded", "grounded_gear", "chunky_gear", "chunky_weapon"]);   // fps: WF v10 (a new key, never an edit of a used one)
  assert.equal(styleText("cartoon"), STYLE);
  assert.equal(conceptPrompt(DESC), conceptPrompt(DESC, "cartoon"));
  for (const name of STYLE_NAMES) {
    const t = styleText(name);
    assert.ok(t.startsWith(ISO_SENTENCE), name);
    assert.ok(t.endsWith("Solid white background, whole object in frame with margin, centred."), name);
    assert.doesNotMatch(styleOrtho(t), /isometric/);
    assert.ok(styleOf(name).title, name);
  }
  const g = styleText("generals");
  assert.match(g, /early-2000s real-time-strategy/);
  assert.match(g, /olive drab, desert tan or dark grey/);
  assert.match(g, /dark gunmetal for weapons and tracks/);
  assert.match(g, /no text, no numbers, no insignia/);
  assert.match(g, /No crew/);
  assert.doesNotMatch(g, /generals|command|conquer|electronic arts|westwood|EA/i);
  assert.throws(() => styleOf("anime"), /--style anime: cartoon \| generals/);
});

test("new --style generals --dry: the generals STYLE in the prompt / README, subject.json + facts.json name it, the sheet prompt uses it", async () => {
  const root = tmp();
  const r = await newSubject({ root, subject: "tk", desc: DESC, dry: true, style: "generals" });
  assert.ok(r.prompt.endsWith(` ${HIDDEN_FACE} ${styleText("generals")}`));
  const readme = fs.readFileSync(path.join(root, "refs", "tk.README.md"), "utf8");
  assert.match(readme, /- style: generals \(scripts\/v7\/styles\.json styles\.generals\.text\)/);
  assert.ok(readme.includes(`${FENCE}
${r.prompt}
${FENCE}`));
  const subj = JSON.parse(fs.readFileSync(path.join(root, "subjects", "tk", "subject.json"), "utf8"));
  assert.equal(subj.style, "generals");
  assert.match(subj.title, /^RTS-style tk/);
  const facts = JSON.parse(fs.readFileSync(path.join(root, "subjects", "tk", "turnaround", "facts.json"), "utf8"));
  assert.equal(facts.style, "generals");
  const sheet = sheetPrompt(loadTemplates(), facts);
  assert.ok(sheet.includes(styleOrtho(styleText("generals"))));
  assert.ok(!sheet.includes(styleOrtho(STYLE)));
  // the default writes no style key (the existing subjects' files keep their shape) and the cartoon sheet
  const c = factsFrom({ subject: "cm", noun: "cement mixer", desc: DESC });
  assert.ok(!("style" in c));
  assert.ok(sheetPrompt(loadTemplates(), c).includes(styleOrtho(STYLE)));
  await assert.rejects(newSubject({ root, subject: "tk2", desc: DESC, dry: true, style: "anime" }), /--style anime/);
  fs.rmSync(root, { recursive: true, force: true });
});

test("WF v10: new --class weapon --style fps --dry — pipeline direct, the L anchor, ONE family, the fixed isometric camera, no gold state; gemini refused", async () => {
  const root = tmp();
  const WDESC = "A stylised assault rifle: a dark gunmetal receiver and barrel, a matte black polymer stock, grip and handguard, a curved black magazine, an orange charging handle on the left flank. The ejection port is on the right flank, hidden in this view. About 0.9 m long, 0.07 m wide and 0.26 m tall.";
  const r = await newSubject({ root, subject: "ar", klass: "weapon", desc: WDESC, dry: true, style: "fps", concept: CONCEPT });
  assert.deepEqual(r.files, ["refs/ar.png", "refs/ar.README.md", "subjects/ar/subject.json", "subjects/ar/camera.json", "subjects/ar/turnaround/views.json", "subjects/ar/turnaround/facts.json", "subjects/ar/prior.json"]);
  assert.ok(r.direct && !fs.existsSync(path.join(root, "out", "ref", "gold", "ar")));
  assert.ok(r.prompt.endsWith(` ${HIDDEN_FACE} ${styleText("fps")}`));
  const subj = JSON.parse(fs.readFileSync(path.join(root, "subjects", "ar", "subject.json"), "utf8"));
  assert.equal(subj.pipeline, "direct");
  assert.equal(subj.class, "weapon");
  assert.equal(subj.ruleOverrides.tris.value, 8000);
  const cam = JSON.parse(fs.readFileSync(path.join(root, "subjects", "ar", "camera.json"), "utf8"));
  assert.deepEqual([cam.theta_deg, cam.phi_deg], [30, 45]);
  const views = JSON.parse(fs.readFileSync(path.join(root, "subjects", "ar", "turnaround", "views.json"), "utf8"));
  assert.deepEqual(views.anchor, { dim: "L", m: 0.9 });
  assert.deepEqual(Object.keys(views.families.table), ["body"]);
  assert.ok(Array.isArray(views.families.table.body) && views.families.table.body.length >= 2);
  familyTable([], views.families);
  const facts = JSON.parse(fs.readFileSync(path.join(root, "subjects", "ar", "turnaround", "facts.json"), "utf8"));
  assert.equal(facts.style, "fps");
  assert.ok(sheetPrompt(loadTemplates(), facts).includes(styleOrtho(styleText("fps"))));
  assert.match(r.chain[2], /^3\. provisional frame: node scripts\/v7\/hull\.mjs --subject ar --write-frame --from facts$/);
  assert.match(r.chain.join("\n"), /gold\.mjs hs --subject ar/);
  const f = styleText("fps");
  assert.match(f, /first-person-shooter weapon/);
  assert.match(f, /No hands, no people/);
  // owner 2026-10-04: gemini is refused unless explicitly allowed (the generator is never reached)
  let called = 0;
  const generate = async () => { called += 1; return { ok: false, provenance: { reason: "stub" } }; };
  await assert.rejects(newSubject({ root, subject: "ar2", klass: "weapon", desc: WDESC, gen: "gemini", generate }), /--gen gemini is refused: owner ruling 2026-10-04/);
  assert.equal(called, 0);
  await assert.rejects(newSubject({ root, subject: "ar2", klass: "weapon", desc: WDESC, gen: "gemini", allowGemini: true, generate }), /generated no image/);
  assert.equal(called, 1);
  fs.rmSync(root, { recursive: true, force: true });
});
