#!/usr/bin/env node
// WF v8 WP5 — gold.mjs: the gold workflow ORCHESTRATOR's only interface (research/v7/WF-V8-PLAN.md; the procedure:
// D:\Git\anyCreature\hard_surface\.claude\skills\gold-model\SKILL.md). Every state change goes through here: out/ref/gold/<s>/state.json
// is the source of truth and every state write regenerates LEDGER.md from it. The orchestrator types commands, reads
// the NEXT line, launches the pinned seats (.claude/agents/gold-*.md) with the brief files, and writes nothing by hand.
//
//   node scripts/v7/gold.mjs new         --subject s --class vehicle --desc-file <paragraph.txt> [--style cartoon|generals] [--gen gpt|gemini] [--noun "..."] [--dry [--root <dir>] [--concept <png>]]
//   node scripts/v7/gold.mjs status      [--subject s] [--json]                  phase, round, baseline, open items, runs, NEXT
//   node scripts/v7/gold.mjs doctor      --subject s [--no-tools]                doctor.mjs (+ its hull row) + hull.mjs --png, recorded
//   node scripts/v7/gold.mjs brief       --subject s --role modeller|critic|auditor [--seat opus|sonnet|fable] [--no-prompt]
//   node scripts/v7/gold.mjs close       --subject s [--run calls,minutes] [--force]      end of a modeller round
//   node scripts/v7/gold.mjs merge       --subject s [--opus calls,minutes] [--sonnet calls,minutes] [--fable calls,minutes]
//   node scripts/v7/gold.mjs commit      --subject s [--dry]                     explicit pathspecs, generated message
//   node scripts/v7/gold.mjs apply-audit --subject s --owner-approved [--owner-note "..."] [--accept-blocks id,id] [--run calls,minutes]
//   node scripts/v7/gold.mjs drift add   --subject s --image <view|concept> --rect x0,y0,x1,y1 --decides <image> --why "..." [--id D4] --owner-approved
//   node scripts/v7/gold.mjs drift rm    --subject s --id D4 --owner-approved
//   node scripts/v7/gold.mjs owner       --subject s --accept | --review | --extra-round [--note "..."]
//   node scripts/v7/gold.mjs eyes-check  [--subject s] [--update]                re-render every subject's snapshot: no change
//   node scripts/v7/gold.mjs migrate     --subject s --phase owner|setup [--rounds 1=<commit>,2=<commit>,...] [--force]
//   node scripts/v7/gold.mjs note        --subject s --text "setup ..."              one ledger line (its role from its first word)
//   node scripts/v7/gold.mjs pipeline    --subject s --set gold|direct              subject.json pipeline (class weapon items: gold); before round 1 only
//   node scripts/v7/gold.mjs shift       --subject s --view v (--sweep a,b,c | --right x | --up x) [--axis right|up] [--pair front,rear] --why "..."
//   node scripts/v7/gold.mjs override    --subject s (--wheels count,axles,equal|per-axle[,lo,hi] [--running tracks|skids] --evidence "..." | --running skids --evidence "..." | --palette-auto | --palette z1,z2 --evidence "..." | --roles r1,r2 --evidence "..." | --tris n --evidence "..." | --mirror-centred p1,p2 --evidence "...") [--note "..."]
//   node scripts/v7/gold.mjs owner-packet [--subject s]                          OWNER.md per subject + out/ref/gold/OWNER-BATCH.md
//   node scripts/v7/gold.mjs ledger-repair --subject s [--dry]                   drop the one-line bug's re-imported copies (before 2026-09-28)
//   node scripts/v7/gold.mjs hs          [--subject s]                          WF v9 HS stage (out/blender-hs/<s>): stage + NEXT (read-only)
//                                                                               WF v10: a `pipeline: "direct"` subject (class weapon) shows setup → build → review → polish → function → owner
// shift / override are eye changes: only at a round boundary (setup; model before the first saved step; review before any
// critic; owner / done) — measured, applied, re-baselined, a ledger line, the eyes reference re-recorded (eyes-check --update).
// Common: --dir <gold dir> (default out/ref/gold/<s>: a replay runs on a copy), --config <file> (default
// scripts/v7/gold.config.json). Exit 0 ok, 1 refused / a check failed, 2 blocked (merge: a critique missing or partial), 3 usage.
//
// Phases (state.json): setup -> (apply-audit) model -> (close) review -> (merge CONTINUE) model ... ; close of the cap
// round, merge STOP / OWNER -> owner -> (owner --accept) done. Files under <dir>: state.json, LEDGER.md (generated),
// eyes.json (the eyes reference: the snapshot eyes-check re-renders), model.mjs, model-rN.mjs (the round-end snapshots;
// model-r0 = the round-1 start), steps/ (step.mjs), brief/ (the seats' prompts), baseline/rN-{start,end}.json
// (step.mjs --json), report/rN-modeller.json, critique/rN-{opus,sonnet,fable,merged}.{json,md}, view/ (the critics' pages),
// OWNER.md, doctor.json, hull.{json,png}, audit/ (the auditor's proposal).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import { loadSubject } from "../subject.mjs";
import { applyRuleOverrides, DEFAULT_LIMITS, TRIS_OVERRIDE_CAP } from "../../src/validate/kernel-chain.mjs";
import {
  CONFIG_FILE, LEDGER_MARK, ROOT, SEATS, addItem, applyMerge, applyReport, briefAuditor, briefCritic, briefModeller, changedFiles,
  checkState, combineHashes, eyeRulings, commitCandidates, commitMessage, critiqueDrift, doctorLine, driftBoundary, driftJson, driftProposals, extraLedgerLines, eyeBoundary,
  eyesFileList, hashFiles, importLedger, inlineJson, ledgerFacts, loadConfig, mirrorCentredValue, modellerLine, newState, nextAction, normImage, oneLine, ownerBatch, ownerPacket,
  paletteZoneViolations, parseArgs, parseRun, renderLedger, repairLedger, roleOf, roundTypeOf, serializeState, setJsonKey, setupMisses, setupRulings, setupStopOf,
  setupTargetsOf, shiftTable, shiftWinner, stopRuleText, trisValue, viewsText, wheelsValue, withOverride,
} from "./goldlib.mjs";

const USAGE = fs.readFileSync(fileURLToPath(import.meta.url), "utf8").split(/\r?\n/).filter((l) => /^\/\/ {3}node scripts\/v7\/gold\.mjs/.test(l)).map((l) => l.slice(5)).join("\n");
const BOOL = ["help", "owner-approved", "force", "update", "json", "dry", "no-tools", "accept", "review", "extra-round", "palette-auto", "no-prompt", "allow-gemini"];
const AGENTS_DIR = path.resolve(ROOT, "..", "..", ".claude", "agents");
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };
const readJson = (f) => JSON.parse(fs.readFileSync(f, "utf8"));
const exists = (f) => fs.existsSync(f);
const sha256 = (f) => createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const sha1 = (f) => createHash("sha1").update(fs.readFileSync(f)).digest("hex");
/** A text file's sha256 with CRLF -> LF (the eyes reference must not change with a checkout's line endings). */
const textSha = (f) => createHash("sha256").update(fs.readFileSync(f, "utf8").replace(/\r\n/g, "\n")).digest("hex");
const sameBytes = (a, b) => exists(a) && exists(b) && fs.readFileSync(a).equals(fs.readFileSync(b));
const now = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");
const today = () => new Date().toISOString().slice(0, 10);
const str = (v) => (v !== undefined && v !== null && v !== true ? String(v) : null);

class Refuse extends Error { constructor(msg, code = 1) { super(msg); this.code = code; } }
const refuse = (msg, code = 1) => { throw new Refuse(msg, code); };

// ---------------------------------------------------------------------------------------------------------------------
// Context, state, child processes
// ---------------------------------------------------------------------------------------------------------------------

function ctxOf(subject, args) {
  const S = loadSubject(subject);
  const vf = path.join(ROOT, "subjects", subject, "turnaround", "views.json");
  if (!exists(vf)) refuse(`${subject}: no subjects/${subject}/turnaround/views.json`);
  const spec = readJson(vf);
  const views = Object.keys(spec.views);
  const dir = str(args.dir) ? path.resolve(args.dir) : path.join(ROOT, "out", "ref", "gold", subject);
  return {
    subject, S, spec, viewsFile: vf, views, order: [...views, "concept"], dir, dirRel: rel(dir),
    stateFile: path.join(dir, "state.json"), ledgerFile: path.join(dir, "LEDGER.md"), eyesFile: path.join(dir, "eyes.json"),
    model: path.join(dir, "model.mjs"), dirFlag: str(args.dir) ? ` --dir ${rel(dir)}` : "", configFlag: str(args.config) ? ` --config ${rel(path.resolve(args.config))}` : "",
  };
}
const flagsOf = (ctx) => `${ctx.dirFlag}${ctx.configFlag}`;

function readState(ctx) {
  if (!exists(ctx.stateFile)) return null;
  const st = readJson(ctx.stateFile);
  const bad = checkState(st);
  if (bad.length) refuse(`${rel(ctx.stateFile)}: ${bad.join("; ")}`);
  if (st.subject !== ctx.subject) refuse(`${rel(ctx.stateFile)} is for "${st.subject}", not ${ctx.subject}`);
  // LEDGER.md lines written by hand since the last generation are imported, never dropped by the next write
  if (exists(ctx.ledgerFile)) {
    const extra = extraLedgerLines(fs.readFileSync(ctx.ledgerFile, "utf8"), st.ledger, st.round);
    if (extra.length) {
      st.ledger.push(...extra);
      console.log(`[gold] note: ${extra.length} hand-written LEDGER.md line(s) imported into state.json (LEDGER.md is generated: write through gold.mjs): ${extra[0].text.slice(0, 120)}`);
    }
  }
  return st;
}
function needState(ctx) {
  const st = readState(ctx);
  if (!st) refuse(`${ctx.subject}: no ${rel(ctx.stateFile)} (a new subject: gold.mjs doctor --subject ${ctx.subject}; a v7 subject: gold.mjs migrate)`);
  return st;
}
/** Every state write regenerates LEDGER.md from it. */
function saveState(ctx, st) {
  const bad = checkState(st);
  if (bad.length) throw new Error(`refusing to write an invalid state: ${bad.join("; ")}`);
  for (const e of st.ledger) e.text = oneLine(e.text);   // one entry = one LEDGER.md line, byte for byte (extraLedgerLines)
  fs.mkdirSync(ctx.dir, { recursive: true });
  fs.writeFileSync(ctx.stateFile, serializeState(st));
  fs.writeFileSync(ctx.ledgerFile, renderLedger(st, ctx.views));
}

/** node <argv> in ROOT, synchronously: {code, out, err}. */
function runNode(argv, { timeout = 900000 } = {}) {
  const r = spawnSync(process.execPath, argv, { cwd: ROOT, encoding: "utf8", maxBuffer: 256 << 20, timeout, windowsHide: true });
  return { code: r.status ?? -1, out: r.stdout ?? "", err: `${r.stderr ?? ""}${r.error ? String(r.error) : ""}` };
}
/** The same, asynchronously (eyes-check renders in parallel). */
function runNodeAsync(argv, { timeout = 900000 } = {}) {
  return new Promise((resolve) => {
    const p = spawn(process.execPath, argv, { cwd: ROOT, windowsHide: true });
    let out = "", err = "";
    p.stdout.on("data", (d) => { out += d; });
    p.stderr.on("data", (d) => { err += d; });
    const t = setTimeout(() => { p.kill(); err += `\ntimed out after ${timeout / 1000} s`; }, timeout);
    p.on("close", (code) => { clearTimeout(t); resolve({ code, out, err }); });
    p.on("error", (e) => { clearTimeout(t); resolve({ code: -1, out, err: String(e) }); });
  });
}
const tail = (r, n = 6) => `${r.out}\n${r.err}`.trim().split(/\r?\n/).slice(-n).join("\n");

/** step.mjs --json of a module (baseline = a JSON or "none"): {code, rec, out}. code 0 KEEP, 1 REVERT; throws on a tool error. */
function stepJson(ctx, module, json, baseline = "none") {
  fs.mkdirSync(path.dirname(json), { recursive: true });
  if (exists(json)) fs.rmSync(json);
  const r = runNode(["scripts/v7/step.mjs", "--subject", ctx.subject, "--module", module, "--baseline", baseline, "--json", json]);
  if (!exists(json)) refuse(`step.mjs on ${rel(module)} wrote no record (exit ${r.code}):\n${tail(r, 10)}`);
  return { code: r.code, rec: readJson(json), out: r.out };
}
const viewsIA = (views) => Object.fromEntries(Object.entries(views ?? {}).map(([v, m]) => [v, { iou: m.iou, agree: m.agree ?? m.iou }]));

// ---------------------------------------------------------------------------------------------------------------------
// Eyes
// ---------------------------------------------------------------------------------------------------------------------

function eyesNow(ctx, config) {
  const list = eyesFileList(config, { subject: ctx.subject, klass: ctx.S.klass, paths: ctx.S.rel, viewFiles: Object.values(ctx.spec.views).map((v) => v.file) });
  const files = hashFiles(list);
  return { files, hash: combineHashes(files) };
}
const eyesRecord = (ctx) => (exists(ctx.eyesFile) ? readJson(ctx.eyesFile) : null);

/** view.mjs (the sheet + JSON, no pages) of `module` into a fresh temp dir: {json (canonical sha256, no module field), png, views}. */
async function renderRef(subject, module) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), `gold-eyes-${subject}-`));
  try {
    const r = await runNodeAsync(["scripts/v6/view.mjs", "--subject", subject, "--module", module, "--out", tmp]);
    const base = path.basename(module).replace(/\.mjs$/, "");
    const jf = path.join(tmp, `${base}-view.json`), pf = path.join(tmp, `${base}-view.png`);
    if (r.code !== 0 || !exists(jf) || !exists(pf)) return { error: `view.mjs exit ${r.code}: ${tail(r, 3)}` };
    const j = readJson(jf);
    delete j.module;
    return { json: createHash("sha256").update(JSON.stringify(j)).digest("hex"), png: sha256(pf), views: viewsIA(j.views) };
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

/** eyes.json: the eyes reference of a subject — the snapshot eyes-check re-renders, its render hashes, the eyes files. */
async function recordEyes(ctx, config, module, by) {
  const eyes = eyesNow(ctx, config);
  const render = await renderRef(ctx.subject, module);
  if (render.error) refuse(`eyes reference of ${ctx.subject}: ${render.error}`);
  const rec = { subject: ctx.subject, at: now(), by, module: rel(path.resolve(ROOT, module)), moduleSha256: textSha(path.resolve(ROOT, module)), eyesHash: eyes.hash, render, files: eyes.files };
  fs.writeFileSync(ctx.eyesFile, `${JSON.stringify(rec, null, 2)}\n`);
  return rec;
}

/** Refuse when an eyes file changed since the state recorded it (close / merge: eyes change only at a round boundary). */
function assertEyes(ctx, config, st, what, args = {}) {
  if (!st.eyesHash) return;
  const eyes = eyesNow(ctx, config);
  if (eyes.hash === st.eyesHash) return;
  // --eyes-accepted "<why>": an intended, output-neutral eye change landed mid-round (e.g. an opt-in validator key);
  // record it in the ledger and adopt the current eyes instead of refusing.
  const why = str(args["eyes-accepted"]);
  if (why) { st.ledger.push({ round: st.round, role: "setup", text: `eyes change accepted mid-round (${what}): ${why}` }); st.eyesHash = eyes.hash; return; }
  const rec = eyesRecord(ctx);
  const files = rec?.eyesHash === st.eyesHash ? changedFiles(rec.files, eyes.files) : ["(eyes.json does not hold the recorded set)"];
  refuse(`${what} refused: the eyes changed during round ${st.round}: ${files.join(", ")} — eyes change only at a round boundary: restore them (git diff -- <file>), then run it again — or, for an intended output-neutral change, pass --eyes-accepted \"<why>\"`);
}

// ---------------------------------------------------------------------------------------------------------------------
// Facts for NEXT
// ---------------------------------------------------------------------------------------------------------------------

const briefMetaFile = (ctx, round) => path.join(ctx.dir, "brief", `r${round}-modeller.json`);
const critiqueFile = (ctx, round, seat) => path.join(ctx.dir, "critique", `r${round}-${seat}.json`);

function critiqueState(ctx, round, seat) {
  const f = critiqueFile(ctx, round, seat);
  if (!exists(f)) return "missing";
  try { return readJson(f).done === true ? "done" : "partial"; } catch { return "partial"; }
}

function facts(ctx, config, st) {
  const out = { cmd: "node scripts/v7/gold.mjs", flags: flagsOf(ctx), dirRel: ctx.dirRel };
  const df = path.join(ctx.dir, "doctor.json");
  if (exists(df)) {
    const d = readJson(df);
    out.doctor = { verdict: d.verdict, hullLevel: d.rows?.find((r) => r.id === "hull")?.level ?? null, blocks: (d.rows ?? []).filter((r) => r.level === "BLOCK").map((r) => r.id), stale: st.phase === "setup" && !!st.eyesHash && eyesNow(ctx, config).hash !== st.eyesHash };
  } else out.doctor = null;
  const af = path.join(ctx.dir, "audit", "audit.json");
  if (exists(af)) {
    let a = null;
    try { a = readJson(af); } catch { a = { done: false }; }
    const md = path.join(ctx.dir, "audit", "AUDIT.md");
    const verdict = exists(md) ? (fs.readFileSync(md, "utf8").split(/\r?\n/).find((l) => /\b(READY|EDIT|REGENERATE|OWNER)\b/.test(l)) ?? "").trim() : null;
    out.audit = { done: a.done === true, verdict, semantic: Array.isArray(a.semantic) && a.semantic.length > 0, regenerate: Object.values(a.views ?? {}).some((v) => v?.regenerate) };
  } else out.audit = null;
  out.briefOpen = st.phase === "model" && exists(briefMetaFile(ctx, st.round));
  // apply-audit ran on THIS audit and these references (state.setupApplied = the audit.json sha256 + the eyes hash it
  // left): NEXT must not loop back to the gate — a new audit or changed images make it false again
  const af2 = path.join(ctx.dir, "audit", "audit.json");
  out.applied = st.phase === "setup" && !!st.setupApplied && exists(af2) && st.setupApplied.audit === sha256(af2) && st.setupApplied.eyes === st.eyesHash;
  out.critiques = Object.fromEntries(SEATS.map((s) => [s, critiqueState(ctx, st.round, s)]));
  out.pairSeats = criticSeats(ctx, config);
  out.turnaroundStop = st.phase === "setup" ? turnaroundStop(ctx, config)?.stop ?? null : null;
  out.chain = st.phase === "setup" ? setupChainStep(ctx) : null;
  return out;
}

/**
 * A new subject's first unfinished step of the setup chain (scripts/v7/README.md "New subject, once"; gold.mjs new
 * prints all of it) that the files show: camera, families, frame, turnaround, per-view colours, the hull frame, a start.
 * null = the chain is through (the doctor is next). -> {step, cmd, why} | null
 */
function setupChainStep(ctx) {
  const s = ctx.subject, t = "node scripts/v7/turnaround.mjs", d = `--dir out/turnaround/${s}`;
  const S = ctx.S, fam = ctx.spec.families ?? {};
  const live = path.join(ROOT, "subjects", s, "turnaround");
  const lm = S.paths.layoutMeasured && exists(S.paths.layoutMeasured) ? readJson(S.paths.layoutMeasured)._frame : null;
  if (!S.paths.camera || !exists(S.paths.camera)) return { step: 1, cmd: `node scripts/solve-camera.mjs ${s} --image ${S.rel.target}`, why: "new subject chain 1: no camera.json" };
  if (/^(PROPOSAL|PLACEHOLDER)/.test(String(fam._table ?? ""))) return { step: 2, cmd: `name the families: subjects/${s}/turnaround/views.json families.table (+ families.body; replace the _table note with what was decided; node scripts/v7/measure.mjs sample --image ${S.rel.target} x,y,w,h)`, why: "new subject chain 2: families.table is still gold.mjs new's proposal" };
  if (!Array.isArray(lm?.quadPx)) return { step: 4, cmd: `node scripts/v7/hull.mjs --subject ${s} --write-frame --from facts`, why: "new subject chain 4: no concept frame (layout.measured.json _frame.quadPx)" };
  if (!ctx.views.every((v) => exists(path.join(live, ctx.spec.views[v].file)))) {
    const started = exists(path.join(ROOT, "out", "turnaround", s, "state.json"));
    return { step: 5, cmd: started ? `${t} status --subject ${s} ${d} → repair --view <v> until the targets are met (the stop rule) → ${t} install --subject ${s} ${d}` : `${t} gen --subject ${s} --out out/turnaround/${s}`, why: "new subject chain 5: no installed turnaround" };
  }
  if (!fam.viewTable) return { step: 6, cmd: `${t} families --subject ${s} --apply`, why: "new subject chain 6: no per-view colours (views.json families.viewTable)" };
  if (lm.provisional) return { step: 7, cmd: `node scripts/v7/hull.mjs --subject ${s} --write-frame   (then chain 8: facts.json dims + prior.json from hull.mjs --aniso)`, why: "new subject chain 7: the concept frame is the provisional facts box" };
  if (!exists(path.join(ctx.dir, "start.mjs")) && !exists(ctx.model)) return { step: 9, cmd: `node scripts/v7/scaffold.mjs --subject ${s} --shape sedan|box|bus|pickup|machine`, why: "new subject chain 9: no start.mjs" };
  return null;
}

/** The setup stop rule on the subject's turnaround work folder (out/turnaround/<s>/state.json): {dir, stop} or null. */
function turnaroundStop(ctx, config) {
  const dir = path.join(ROOT, "out", "turnaround", ctx.subject);
  const f = path.join(dir, "state.json");
  if (!exists(f)) return null;
  let tst;
  try { tst = readJson(f); } catch { return null; }
  const L = config.setupStop ?? { sets: 3, view: 3 };
  const T = setupTargetsOf(config);
  return { dir: rel(dir), limits: L, stop: setupStopOf(tst, { misses: (sm) => setupMisses(sm, T), sets: L.sets, view: L.view }) };
}

/** A seat's maxTurns from its .claude/agents/<name>.md frontmatter (null when unreadable). */
function agentMaxTurns(name) {
  try {
    const m = /^maxTurns:\s*(\d+)\s*$/m.exec(fs.readFileSync(path.join(AGENTS_DIR, `${name}.md`), "utf8").split(/^---\s*$/m)[1] ?? "");
    return m ? Number(m[1]) : null;
  } catch { return null; }
}

// ---------------------------------------------------------------------------------------------------------------------
// status
// ---------------------------------------------------------------------------------------------------------------------

function goldSubjects() {
  const base = path.join(ROOT, "out", "ref", "gold");
  if (!exists(base)) return [];
  return fs.readdirSync(base, { withFileTypes: true }).filter((d) => d.isDirectory() && exists(path.join(ROOT, "subjects", d.name, "subject.json"))).map((d) => d.name).sort();
}

function cmdStatus(args, config) {
  const subjects = str(args.subject) ? [args.subject] : goldSubjects();
  const rows = [];
  for (const s of subjects) {
    let ctx, st;
    try { ctx = ctxOf(s, args); st = readState(ctx); } catch (e) { rows.push({ subject: s, error: e.message }); continue; }
    if (!st) { rows.push({ subject: s, missing: true, next: { cmd: `node scripts/v7/gold.mjs doctor --subject ${s}`, why: "no state.json (a new subject starts in setup)" } }); continue; }
    const f = facts(ctx, config, st);
    const next = nextAction(st, f);
    const eyes = eyesNow(ctx, config);
    const eyesChanged = st.eyesHash && eyes.hash !== st.eyesHash ? changedFiles(eyesRecord(ctx)?.files ?? {}, eyes.files) : [];
    rows.push({ subject: s, ctx, st, next, eyesChanged, f });
  }
  if (args.json) {
    console.log(JSON.stringify(rows.map((r) => (r.st ? { subject: r.subject, phase: r.st.phase, round: r.st.round, roundType: r.st.roundType, baseline: r.st.baseline, open: r.st.items.open, runs: r.st.runs.length, eyesChanged: r.eyesChanged, next: r.next } : r)), null, 2));
    return 0;
  }
  const single = subjects.length === 1;
  for (const r of rows) {
    if (r.error) { console.log(`${r.subject.padEnd(14)} ERROR ${r.error}`); continue; }
    if (r.missing) { console.log(`${r.subject.padEnd(14)} (no state) · NEXT: ${r.next.cmd}`); continue; }
    const { st, ctx } = r;
    const b = st.baseline?.views;
    const min = b ? Object.entries(b).reduce((m, [v, x]) => (!m || x.agree < m[1] ? [v, x.agree] : m), null) : null;
    const type = st.roundType ? `${st.roundType} ≤ ${config.rounds.types[st.roundType].calls} calls` : "-";
    const own = st.items.open.filter((o) => o.owner).length;
    const calls = st.runs.reduce((a, x) => a + (x.calls ?? 0), 0);
    if (!single) {
      console.log(`${r.subject.padEnd(14)} ${st.phase.padEnd(6)} r${st.round} ${(st.roundType ?? "-").padEnd(6)} · ${b ? `${viewsText(b, ctx.order)} (min ${min[1].toFixed(3).replace(/^0/, "")} ${min[0]})` : "no baseline"} · open ${st.items.open.length}${own ? ` (${own} owner)` : ""} · runs ${st.runs.length}${r.eyesChanged.length ? ` · EYES CHANGED ${r.eyesChanged.length}` : ""}`);
      console.log(`${"".padEnd(14)} NEXT: ${r.next.cmd}`);
      continue;
    }
    console.log(`${r.subject} · phase ${st.phase} · round ${st.round} of ${config.rounds.cap} (${type}) · ${rel(ctx.stateFile)}`);
    if (b) {
      console.log(`baseline ${st.baseline.file ?? "(views only)"}: ${ctx.order.map((v) => `${v} iou ${b[v]?.iou?.toFixed(4) ?? "-"} agree ${b[v]?.agree?.toFixed(4) ?? "-"}`).join(" · ")}`);
      console.log(`bar agree >= ${config.bar.agree}: ${ctx.order.filter((v) => b[v] && b[v].agree < config.bar.agree).join(", ") || "met in every image"}`);
    } else console.log("baseline: none yet");
    console.log(`items: decided ${st.items.decided.length} · tried ${st.items.tried.length} · parked ${st.items.parked.length} · open ${st.items.open.length}`);
    for (const o of st.items.open) console.log(`  open ${o.key}${o.owner ? " (owner)" : ""}: ${o.text.slice(0, 200)}`);
    console.log(`runs ${st.runs.length}${calls ? ` · ${calls} calls recorded` : ""}: ${st.runs.map((x) => `r${x.round} ${x.role}${x.seat ? `:${x.seat}` : ""}${x.calls !== null && x.calls !== undefined ? ` ${x.calls}c` : ""}${x.ok === false ? " FAILED" : ""}`).join(", ") || "none"}`);
    if (r.eyesChanged.length) console.log(`EYES CHANGED since the last record: ${r.eyesChanged.join(", ")} (${st.phase === "model" && r.f.briefOpen ? "the open round's close will refuse" : "the next brief / doctor re-records"})`);
    console.log(`last ledger: ${st.ledger.length ? st.ledger[st.ledger.length - 1].text.slice(0, 240) : "(empty)"}`);
    console.log(`NEXT: ${r.next.cmd}`);
    console.log(`  why: ${r.next.why}`);
    const dirty = dirtyFiles(ctx, st);
    if (dirty.length) console.log(`uncommitted: ${dirty.length} file(s) — node scripts/v7/gold.mjs commit --subject ${r.subject}${flagsOf(ctx)}`);
  }
  return rows.some((r) => r.error) ? 1 : 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// doctor
// ---------------------------------------------------------------------------------------------------------------------

function cmdDoctor(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = readState(ctx) ?? newState(ctx.subject);
  fs.mkdirSync(ctx.dir, { recursive: true });
  const dj = path.join(ctx.dir, "doctor.json"), hj = path.join(ctx.dir, "hull.json"), hp = path.join(ctx.dir, "hull.png");
  const start = exists(path.join(ctx.dir, "start.mjs")) ? path.join(ctx.dir, "start.mjs") : ctx.model;
  const d = runNode(["scripts/v7/doctor.mjs", "--subject", ctx.subject, "--module", start, "--json", dj, ...(args["no-tools"] ? ["--no-tools"] : [])]);
  process.stdout.write(d.out);
  if (d.code === 2 || !exists(dj)) refuse(`doctor.mjs failed (exit ${d.code}): ${tail(d, 4)}`);
  const h = runNode(["scripts/v7/hull.mjs", "--subject", ctx.subject, "--json", hj, "--png", hp]);
  const hull = exists(hj) && h.code === 0 ? readJson(hj) : null;
  if (!hull) console.log(`[gold] hull.mjs failed (exit ${h.code}): ${tail(h, 3)}`);
  const rep = readJson(dj);
  st.ledger.push({ round: st.round, role: "doctor", text: doctorLine({ verdict: rep.verdict, rows: rep.rows, hull }) });
  if (st.phase === "setup") st.eyesHash = eyesNow(ctx, config).hash;
  saveState(ctx, st);
  console.log(`[gold] ${ctx.subject}: doctor ${rep.verdict} recorded · ${rel(dj)}${hull ? ` · ${rel(hp)}` : ""}`);
  console.log(`[gold] NEXT: ${nextAction(st, facts(ctx, config, st)).cmd}`);
  return rep.verdict === "BLOCK" ? 1 : 0;   // (was: 1 in every setup run — read as a failure and retried; SKILL-REVIEW-fable.md 7)
}

// ---------------------------------------------------------------------------------------------------------------------
// brief
// ---------------------------------------------------------------------------------------------------------------------

const dimsText = (dims) => (dims ? `L ${dims.L.toFixed(3)} · W ${dims.W.toFixed(3)} · H ${dims.H.toFixed(3)} m` : "(unregistered)");

/** The registered dims (L / W / H) of a subject, via a tiny child (ortho.mjs is heavy and caches per process). */
function registeredDims(subject) {
  const code = `import("./scripts/v6/ortho.mjs").then(async (o) => { const t = await o.loadTurnaround(${JSON.stringify(subject)}); console.log(JSON.stringify(t.reg.dims)); })`;
  const r = runNode(["--input-type=module", "-e", code]);
  try { return JSON.parse(r.out.trim().split(/\r?\n/).pop()); } catch { return null; }
}

function keysAndParts(module) {
  const k = runNode(["scripts/v7/merge.mjs", "--keys", "--module", module]);
  const p = runNode(["scripts/v7/inspect.mjs", "parts", "--module", module]);
  const lines = p.out.split(/\r?\n/).filter(Boolean);
  const ids = lines.slice(1).filter((l) => !/^(families:|total tris|CHECKPARTS)/.test(l)).map((l) => l.split(/\s+/)[0]);
  const fam = lines.find((l) => l.startsWith("families:")) ?? "";
  const tot = lines.find((l) => l.startsWith("total tris")) ?? "";
  return {
    keysText: k.code === 0 ? k.out.trim() : `(merge.mjs --keys failed: ${tail(k, 2)})`,
    partsText: p.code === 0 ? [fam, tot, `ids: ${ids.join(", ")}`].filter(Boolean).join("\n") : `(inspect.mjs parts failed: ${tail(p, 2)})`,
    families: fam.replace(/^families:\s*/, "").split(/\s+/).filter(Boolean).map((x) => x.replace(/:\d+$/, "")).join(", "),
  };
}

function savedSteps(ctx) {
  const f = path.join(ctx.dir, "steps", "steps.jsonl");
  if (!exists(f)) return [];
  return fs.readFileSync(f, "utf8").split(/\r?\n/).filter((l) => l.trim()).map((l) => JSON.parse(l));
}

const common = (ctx, config) => {
  const target = ctx.S.rel.target;
  return { subject: ctx.subject, at: now(), dirRel: ctx.dirRel, concept: target, turnaround: `subjects/${ctx.subject}/turnaround`, viewFiles: Object.values(ctx.spec.views).map((v) => v.file), order: ctx.order, bar: config.bar.agree };
};

async function cmdBrief(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const role = str(args.role);
  const cap = config.rounds.cap;
  if (role === "auditor") return briefAuditorCmd(ctx, st, config, args);
  if (role === "critic") return briefCriticCmd(ctx, st, config, args);
  if (role !== "modeller") refuse(`--role modeller | critic | auditor (got ${role})`, 3);
  if (st.phase !== "model") refuse(`${ctx.subject} is in phase ${st.phase}, not model: NEXT ${nextAction(st, facts(ctx, config, st)).cmd}`);
  const N = st.round;
  const metaFile = briefMetaFile(ctx, N);
  let meta = exists(metaFile) ? readJson(metaFile) : null;
  let resume = null;
  if (!meta) {
    if (!exists(ctx.model)) {
      const start = path.join(ctx.dir, "start.mjs");
      if (!exists(start)) refuse(`${ctx.subject}: neither model.mjs nor start.mjs in ${ctx.dirRel}`);
      fs.copyFileSync(start, ctx.model);
    }
    const snap = path.join(ctx.dir, `model-r${N - 1}.mjs`);
    if (exists(snap)) { if (!sameBytes(snap, ctx.model)) refuse(`model.mjs differs from model-r${N - 1}.mjs (edited after the last close): copy model-r${N - 1}.mjs over model.mjs, or close again`); }
    else fs.copyFileSync(ctx.model, snap);
    const eyes = eyesNow(ctx, config);
    const rec = eyesRecord(ctx);
    const changed = st.eyesHash && st.eyesHash !== eyes.hash ? changedFiles(rec?.files ?? {}, eyes.files) : [];
    const json = path.join(ctx.dir, "baseline", `r${N}-start.json`);
    const { rec: base, code } = stepJson(ctx, ctx.model, json);
    if (code !== 0) console.log(`[gold] note: step.mjs on the round start says ${base.verdict?.keep ? "KEEP" : `REVERT (${(base.verdict?.reasons ?? []).join("; ")})`} — recorded as the baseline anyway`);
    st.baseline = { file: rel(json), views: viewsIA(base.views) };
    if (changed.length) st.ledger.push({ round: N, role: "eyes", text: `eyes: changed at the round boundary before r${N} (${changed.join(", ")}) · re-baselined ${viewsText(base.views, ctx.order)}` });
    st.eyesHash = eyes.hash;
    if (changed.length || !rec) await recordEyes(ctx, config, snap, `brief r${N}`);
    const steps = savedSteps(ctx);
    meta = { subject: ctx.subject, round: N, at: now(), eyesHash: eyes.hash, start: `model-r${N - 1}.mjs`, startSha256: sha256(snap), baseline: rel(json), stepsAtStart: steps.length ? steps[steps.length - 1].n : 0 };
    fs.mkdirSync(path.dirname(metaFile), { recursive: true });
    fs.writeFileSync(metaFile, `${JSON.stringify(meta, null, 2)}\n`);
    saveState(ctx, st);
  } else {
    const steps = savedSteps(ctx).filter((s) => s.n > meta.stepsAtStart);
    resume = { startedAt: meta.at, steps: steps.map((s) => ({ file: s.file, note: s.note })) };
  }
  const baseRec = exists(path.resolve(ROOT, meta.baseline)) ? readJson(path.resolve(ROOT, meta.baseline)) : { views: st.baseline?.views ?? {} };
  const prevMerged = [N - 1, N - 2].map((r) => path.join(ctx.dir, "critique", `r${r}-merged.md`)).find((f) => exists(f) && fs.readFileSync(f, "utf8").startsWith("STOP: "));
  const kp = keysAndParts(ctx.model);
  const type = st.roundType ?? roundTypeOf(N, cap);
  const text = briefModeller({
    ...common(ctx, config), round: N, cap, type, calls: config.rounds.types[type].calls, rule: config.rounds.types[type].rule,
    start: meta.start, dims: dimsText(registeredDims(ctx.subject)), moduleFlag: ctx.dir !== path.join(ROOT, "out", "ref", "gold", ctx.subject) ? ` --module ${ctx.dirRel}/model.mjs` : "",
    baseline: { file: meta.baseline, views: baseRec.views, blobs: baseRec.blobs, probes: baseRec.probes, chain: baseRec.chain, tris: baseRec.tris, budget: baseRec.budget },
    worksheet: prevMerged ? { file: rel(prevMerged), text: fs.readFileSync(prevMerged, "utf8") } : null,
    items: st.items, drift: ctx.spec.drift ?? null, keysText: kp.keysText, partsText: kp.partsText,
    eyesFiles: Object.keys(eyesNow(ctx, config).files), resume, ledger: st.ledger.map((e) => e.text), maxTurns: agentMaxTurns(config.agents.modeller),
  });
  const file = path.join(ctx.dir, "brief", `r${N}-modeller.md`);
  fs.writeFileSync(file, text);
  console.log(`[gold] ${rel(file)} (${text.split("\n").length} lines)${resume ? " — RESUME of an open round" : ""} · baseline ${meta.baseline}`);
  console.log(`[gold] AGENT subagent_type=gold-modeller description="${ctx.subject} r${N} modeller" prompt="Your brief: ${rel(file)} (run from D:\\Git\\anyCreature\\hard_surface). Read it first; it is your whole task."`);
  console.log(`[gold] then: node scripts/v7/gold.mjs close --subject ${ctx.subject} --run <tool calls>,<minutes>${flagsOf(ctx)}`);
  return 0;
}

/**
 * The critic seats of a fresh round: the subject's class prior `critics.seats` (class weapon, gold pipeline: ["opus"],
 * owner 2026-10-12), else gold.config.json critics.seats (the vehicle / building pair, unchanged).
 */
function criticSeats(ctx, config) {
  const own = ctx.S?.cls?.critics?.seats;
  return Array.isArray(own) && own.length > 0 && own.every((x) => SEATS.includes(x)) ? own : config.critics.seats;
}

function briefCriticCmd(ctx, st, config, args) {
  const seat = str(args.seat);
  if (!SEATS.includes(seat)) refuse(`--seat ${SEATS.join(" | ")}`, 3);
  if (st.phase !== "review") refuse(`${ctx.subject} is in phase ${st.phase}, not review: NEXT ${nextAction(st, facts(ctx, config, st)).cmd}`);
  const N = st.round;
  const baseFile = st.baseline?.file ? path.resolve(ROOT, st.baseline.file) : null;
  const baseRec = baseFile && exists(baseFile) ? readJson(baseFile) : { views: st.baseline?.views ?? {} };
  const cf = critiqueFile(ctx, N, seat);
  let resume = null;
  if (exists(cf)) {
    try { const c = readJson(cf); if (c.done === true) refuse(`${rel(cf)} is already done: merge (gold.mjs merge --subject ${ctx.subject})`); resume = { items: Array.isArray(c.items) ? c.items.length : 0 }; } catch (e) { if (e instanceof Refuse) throw e; resume = { items: 0 }; }
  }
  const kp = keysAndParts(ctx.model);
  const text = briefCritic({
    ...common(ctx, config), round: N, seat, dims: dimsText(registeredDims(ctx.subject)), maxItems: config.critics.maxItems,
    sheet: `${ctx.dirRel}/view/model-view.png`, pages: ctx.order.map((v) => `${ctx.dirRel}/view/model-${v}.png`),
    baseline: { file: st.baseline?.file ?? "(none)", views: baseRec.views, blobs: baseRec.blobs },
    items: st.items, drift: ctx.spec.drift ?? null, keysText: kp.keysText, partsText: kp.partsText, families: kp.families, resume,
    ledger: ledgerFacts(st), maxTurns: agentMaxTurns(config.agents.critic[seat]) ?? config.critics.maxTurns,
  });
  const file = path.join(ctx.dir, "brief", `r${N}-critic-${seat}.md`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
  console.log(`[gold] ${rel(file)} (${text.split("\n").length} lines)${resume ? ` — RESUME (${resume.items} items so far)` : ""}`);
  console.log(`[gold] AGENT subagent_type=${config.agents.critic[seat]} description="${ctx.subject} r${N} critic ${seat}" prompt="Your brief: ${rel(file)} (run from D:\\Git\\anyCreature\\hard_surface). Read it first; it is your whole task."`);
  const seats = criticSeats(ctx, config);
  const pairHint = seats.includes(seat) ? seats : [...new Set([...seats, seat])];
  console.log(`[gold] ${pairHint.length === 1 ? "the one seat (class critics.seats)" : "both seats in parallel, blind"}; then: node scripts/v7/gold.mjs merge --subject ${ctx.subject} ${pairHint.map((x) => `--${x} <calls>,<minutes>`).join(" ")}${flagsOf(ctx)}`);
  return 0;
}

function briefAuditorCmd(ctx, st, config, args = {}) {
  if (st.phase !== "setup") refuse(`${ctx.subject} is in phase ${st.phase}: the setup audit runs in setup only`);
  const dj = path.join(ctx.dir, "doctor.json");
  if (!exists(dj)) refuse(`no ${rel(dj)}: node scripts/v7/gold.mjs doctor --subject ${ctx.subject}${flagsOf(ctx)} first`);
  const d = readJson(dj);
  const hj = path.join(ctx.dir, "hull.json");
  const hull = exists(hj) ? readJson(hj) : null;
  const ax = (v) => { const names = { "0": ["+x near flank", "-x far flank"], "1": ["+y up", "-y down"], "2": ["+z nose", "-z tail"] }; const i = v.findIndex((c) => c !== 0); return i < 0 ? "?" : names[i][v[i] > 0 ? 0 : 1]; };
  const prompt = ctx.S.rel.target.replace(/\.png$/i, ".README.md");
  const promptOk = exists(path.join(ROOT, prompt)) && /^## Full prompt[\s\S]*?```/m.test(fs.readFileSync(path.join(ROOT, prompt), "utf8"));
  if (!promptOk && !args["no-prompt"]) refuse(`no concept prompt: ${prompt} with a "## Full prompt" fenced block (the auditor's semantic check reads exactly that; template refs/forklift.README.md; gold.mjs new writes it) — write it, or pass --no-prompt to audit against the class alone`);
  if (!promptOk) console.log(`[gold] WARN no concept prompt (${prompt}): the auditor's semantic check runs against the class alone (--no-prompt)`);
  const start = exists(path.join(ctx.dir, "start.mjs")) ? `${ctx.dirRel}/start.mjs` : `${ctx.dirRel}/model.mjs`;
  const ts = turnaroundStop(ctx, config);
  const text = briefAuditor({
    ...common(ctx, config), prompt: promptOk ? prompt : null, start, maxTurns: agentMaxTurns(config.agents.auditor) ?? 60,
    stopRule: stopRuleText(ts?.stop ?? null, ts?.limits ?? config.setupStop ?? { sets: 3, view: 3 }, ts?.dir ?? `out/turnaround/${ctx.subject}`),
    axes: Object.entries(ctx.spec.views).map(([v, s]) => ({ view: v, file: s.file, right: ax(s.right), up: ax(s.up) })),
    doctor: { file: rel(dj), verdict: `${d.verdict} (${d.blocks} BLOCK, ${d.warns} WARN, ${d.at})`, rows: d.rows ?? [] },
    hull: hull ? { file: rel(hj), png: `${ctx.dirRel}/hull.png`, summary: `viewOnly ${Object.entries(hull.views).map(([v, m]) => `${v} ${(m.viewOnly * 100).toFixed(1)}`).join(" / ")} %${hull.concept ? ` · conceptOnlyBlob ${(hull.concept.conceptOnlyBlob * 100).toFixed(2)} % · concept IoU ${hull.concept.iou.toFixed(3)}` : ""}` } : null,
  });
  const file = path.join(ctx.dir, "brief", "setup-auditor.md");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
  console.log(`[gold] ${rel(file)} (${text.split("\n").length} lines)`);
  console.log(`[gold] AGENT subagent_type=${config.agents.auditor} description="${ctx.subject} setup audit" prompt="Your brief: ${rel(file)} (run from D:\\Git\\anyCreature\\hard_surface). Read it first; it is your whole task."`);
  console.log(`[gold] then the OWNER setup gate (${ctx.dirRel}/audit/AUDIT.md), then: node scripts/v7/gold.mjs apply-audit --subject ${ctx.subject} --owner-approved${flagsOf(ctx)}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// close — the end of a modeller round
// ---------------------------------------------------------------------------------------------------------------------

async function cmdClose(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const cap = config.rounds.cap;
  if (st.phase !== "model") refuse(`${ctx.subject} is in phase ${st.phase}, not model: nothing to close`);
  const N = st.round;
  const metaFile = briefMetaFile(ctx, N);
  if (!exists(metaFile)) refuse(`round ${N} was never briefed (${rel(metaFile)} missing): gold.mjs brief --subject ${ctx.subject} --role modeller`);
  const meta = readJson(metaFile);
  const run = parseRun(args.run);
  assertEyes(ctx, config, st, "close", args);
  if (!exists(ctx.model)) refuse(`no ${rel(ctx.model)}`);
  const snap0 = path.join(ctx.dir, meta.start);
  const steps = savedSteps(ctx).filter((s) => s.n > meta.stepsAtStart);
  if (steps.length) {
    const last = steps[steps.length - 1];
    if (sha1(ctx.model) !== last.sha1) refuse(`model.mjs has edits after the last saved step (${last.file}): node scripts/v7/step.mjs --subject ${ctx.subject}${ctx.dirFlag ? ` --module ${ctx.dirRel}/model.mjs` : ""} then --save (KEEP) or --revert, then close`);
  } else if (!sameBytes(ctx.model, snap0)) refuse(`model.mjs changed but no step was saved this round: node scripts/v7/step.mjs --subject ${ctx.subject}${ctx.dirFlag ? ` --module ${ctx.dirRel}/model.mjs` : ""} then --save (KEEP) or --revert`);
  const json = path.join(ctx.dir, "baseline", `r${N}-end.json`);
  const { rec, code } = stepJson(ctx, ctx.model, json, path.resolve(ROOT, meta.baseline));
  let forced = null;
  if (code !== 0) {
    const why = (rec.verdict?.reasons ?? []).join("; ") || "REVERT";
    if (!args.force) refuse(`close refused: the round's model REVERTs against its round start (${why}) — node scripts/v7/step.mjs --subject ${ctx.subject}${ctx.dirFlag ? ` --module ${ctx.dirRel}/model.mjs` : ""} --revert (to the last KEEP), then close; or close --force (recorded in the ledger)`);
    forced = why;
  }
  const snap = path.join(ctx.dir, `model-r${N}.mjs`);
  fs.copyFileSync(ctx.model, snap);
  // the critics' pages (and the owner's sheet)
  const v = runNode(["scripts/v6/view.mjs", "--subject", ctx.subject, "--module", ctx.model, "--out", path.join(ctx.dir, "view"), "--zoom"]);
  if (v.code !== 0) refuse(`view.mjs --zoom failed (exit ${v.code}): ${tail(v, 4)}`);
  const reportFile = path.join(ctx.dir, "report", `r${N}-modeller.json`);
  let report = null;
  if (exists(reportFile)) { try { report = readJson(reportFile); } catch (e) { console.log(`[gold] note: ${rel(reportFile)} is not JSON (${e.message}): recorded as no report`); } }
  const baseRec = readJson(path.resolve(ROOT, meta.baseline));
  applyReport(st, report, N);
  st.ledger.push({
    round: N, role: "modeller",
    text: modellerLine({ round: N, snapshot: `model-r${N}`, views: rec.views, base: baseRec.views, order: ctx.order, gate: { pass: !!rec.chain?.pass, rows: (rec.chain?.rows ?? []).map((r) => `${r.v}${r.part ? ` ${r.part}` : ""}`) }, tris: rec.tris, budget: rec.budget, kept: steps.length, report, forced }),
    iou: Object.fromEntries(Object.entries(rec.views).map(([k, m]) => [k, m.agree ?? m.iou])), tris: rec.tris, gate: rec.chain?.pass ? "pass" : "fail",
  });
  st.runs.push({ role: "modeller", round: N, calls: run?.calls ?? null, minutes: run?.minutes ?? null, ok: true });
  st.baseline = { file: rel(json), views: viewsIA(rec.views) };
  st.modelHash = `sha256:${sha256(ctx.model)}`;
  st.phase = N >= cap ? "owner" : "review";
  await recordEyes(ctx, config, snap, `close r${N}`);
  saveState(ctx, st);
  if (st.phase === "owner") writeOwner(ctx, config, st, `The last round (${N} of cap ${cap}) is closed: no critic review follows.`);
  console.log(`[gold] closed r${N}: ${rel(snap)} · ${st.ledger[st.ledger.length - 1].text.slice(0, 300)}`);
  console.log(`[gold] phase ${st.phase} · pages ${ctx.dirRel}/view/model-*.png · NEXT: ${nextAction(st, facts(ctx, config, st)).cmd}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// merge — the two critiques into the worksheet (merge.mjs), the items and the STOP line into the state
// ---------------------------------------------------------------------------------------------------------------------

async function cmdMerge(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  if (st.phase !== "review") refuse(`${ctx.subject} is in phase ${st.phase}, not review`);
  const runs = Object.fromEntries(SEATS.map((s) => [s, parseRun(args[s])]));
  assertEyes(ctx, config, st, "merge", args);
  const { runMerge, MERGE_RULES } = await import("./merge.mjs");
  const cap = config.rounds.cap;
  // a class with its own critic seats (class weapon: one opus seat) merges exactly those; else merge.mjs picks the pair
  const own = criticSeats(ctx, config) !== config.critics.seats ? criticSeats(ctx, config) : null;
  const r = await runMerge({ subject: ctx.subject, round: st.round, dir: ctx.dir, cap, ...(own ? { seats: own } : {}), rules: { ...MERGE_RULES, bar: config.bar.agree }, log: args.quiet ? null : (l) => console.error(l) });
  if (!r.ok) {
    console.log(`MERGE BLOCKED — ${ctx.subject} r${st.round}:`);
    for (const b of r.blocked) console.log(`  ${b}`);
    console.log(`NEXT: ${nextAction(st, facts(ctx, config, st)).cmd}`);
    return 2;
  }
  applyMerge(st, r.merged, { cap, runs });
  saveState(ctx, st);
  if (st.phase === "owner") writeOwner(ctx, config, st, r.merged.stop.line);
  console.log(r.merged.stop.line);
  console.log(`[gold] ${rel(r.files.md)} + .json · ${st.ledger[st.ledger.length - 1].text.slice(0, 300)}`);
  console.log(`[gold] phase ${st.phase} r${st.round} · NEXT: ${nextAction(st, facts(ctx, config, st)).cmd}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// The owner packet
// ---------------------------------------------------------------------------------------------------------------------

/** Every drift rect proposed for a subject: critiques' drift:* items, modeller reports' `drift` lists, the auditor's proposal. */
function driftSources(ctx) {
  const out = [];
  const cdir = path.join(ctx.dir, "critique"), rdir = path.join(ctx.dir, "report");
  if (exists(cdir)) for (const f of fs.readdirSync(cdir).sort()) {
    const m = /^r(\d+)-(fable|opus|sonnet)\.json$/.exec(f);
    if (!m) continue;
    try { out.push(...critiqueDrift(readJson(path.join(cdir, f)), Number(m[1]), m[2], ctx.spec.views)); } catch { /* a broken critique names nothing */ }
  }
  if (exists(rdir)) for (const f of fs.readdirSync(rdir).sort()) {
    const m = /^r(\d+)-modeller\.json$/.exec(f);
    if (!m) continue;
    let rep;
    try { rep = readJson(path.join(rdir, f)); } catch { continue; }
    (Array.isArray(rep.drift) ? rep.drift : []).forEach((d, i) => {
      const image = normImage(d?.image, ctx.spec.views);
      if (image && Array.isArray(d.rect)) out.push({ src: `r${m[1]} modeller ${i + 1}`, round: Number(m[1]), image, rect: d.rect.map(Number), decides: normImage(d.decides, ctx.spec.views), why: oneLine(d.why ?? "") });
    });
  }
  const af = path.join(ctx.dir, "audit", "views.drift.json");
  if (exists(af)) {
    try {
      const p = readJson(af);
      const drift = p.views && p.drift ? p.drift : p;
      for (const [img, list] of Object.entries(drift)) if (Array.isArray(list)) for (const d of list) {
        const image = normImage(img, ctx.spec.views);
        if (image && Array.isArray(d.rect)) out.push({ src: `audit ${d.id ?? ""}`.trim(), round: 0, image, rect: d.rect.map(Number), decides: normImage(d.decides, ctx.spec.views), why: oneLine(d.why ?? "") });
      }
    } catch { /* no proposal */ }
  }
  return out;
}

function writeOwner(ctx, config, st, stop) {
  const bf = st.baseline?.file ? path.resolve(ROOT, st.baseline.file) : null;
  const rec = bf && exists(bf) ? readJson(bf) : { views: st.baseline?.views ?? {} };
  const snap = exists(path.join(ctx.dir, `model-r${st.round}.mjs`)) ? `${ctx.dirRel}/model-r${st.round}.mjs` : `${ctx.dirRel}/model.mjs`;
  const drift = driftProposals(driftSources(ctx), ctx.spec.drift ?? {}, { subject: ctx.subject, flags: flagsOf(ctx) });
  const rulings = setupRulings(st.items);
  const eyeR = eyeRulings(st.ledger);
  const text = ownerPacket({ subject: ctx.subject, at: now(), round: st.round, phase: st.phase, stop, views: rec.views, order: ctx.order, bar: config.bar.agree,
    chain: rec.chain, tris: rec.tris, budget: rec.budget, items: st.items, runs: st.runs, sheet: `${ctx.dirRel}/view/model-view.png`,
    pages: ctx.order.map((v) => `${ctx.dirRel}/view/model-${v}.png`), snapshot: snap, ledgerFile: rel(ctx.ledgerFile), flags: flagsOf(ctx), drift, rulings, eyeRulings: eyeR });
  fs.writeFileSync(path.join(ctx.dir, "OWNER.md"), text);
  return { drift, rulings: [...rulings, ...eyeR], views: rec.views };
}

/** The STOP line an owner packet opens with: the current OWNER.md's own (same phase and round), else from the ledger
 * (the last review's STOP line, or the cap round's close). */
function stopOf(st, config, ctx = null) {
  const of = ctx ? path.join(ctx.dir, "OWNER.md") : null;
  if (of && exists(of)) {
    const m = /^Phase (\w+) after round (\d+)\.\s*(.*)$/m.exec(fs.readFileSync(of, "utf8"));
    if (m && m[1] === st.phase && Number(m[2]) === st.round && m[3].trim()) return m[3].trim();
  }
  const last = [...st.ledger].reverse().find((e) => e.role === "critics" || e.role === "modeller");
  if (last?.role === "modeller" && st.round >= config.rounds.cap) return `The last round (${st.round} of cap ${config.rounds.cap}) is closed: no critic review follows.`;
  const m = last ? /STOP: .*$/.exec(last.text) : null;
  return m ? m[0] : "";
}

/** owner-packet: OWNER.md per subject (the owner items, every proposed drift rect with its ready line, the setup rulings) + OWNER-BATCH.md. */
function cmdOwnerPacket(args, config) {
  const subjects = str(args.subject) ? [args.subject] : goldSubjects();
  const rows = [];
  for (const s of subjects) {
    const ctx = ctxOf(s, args);
    const st = readState(ctx);
    if (!st) continue;
    const r = writeOwner(ctx, config, st, stopOf(st, config, ctx));
    const ag = Object.entries(r.views ?? {}).map(([v, m]) => [v, m.agree ?? m.iou]).filter(([, a]) => Number.isFinite(a));
    const min = ag.length ? ag.reduce((b, x) => (x[1] < b[1] ? x : b)) : null;
    rows.push({ subject: s, phase: st.phase, round: st.round, minAgree: min ? `${min[1].toFixed(3)} ${min[0]}` : null, owner: st.items.open.filter((o) => o.owner).length, drift: r.drift.length, rulings: r.rulings.length, file: `${ctx.dirRel}/OWNER.md` });
    console.log(`[gold] ${s}: ${ctx.dirRel}/OWNER.md · phase ${st.phase} r${st.round} · owner items ${rows[rows.length - 1].owner} · drift proposals ${r.drift.length} · setup rulings ${r.rulings.length}`);
  }
  if (!str(args.dir) && !str(args.subject)) {   // the batch covers every subject: only a run over all of them rewrites it
    const f = path.join(ROOT, "out", "ref", "gold", "OWNER-BATCH.md");
    fs.writeFileSync(f, ownerBatch(rows, now()));
    console.log(`[gold] ${rel(f)} (${rows.length} subject(s))`);
  }
  return 0;
}

/** ledger-repair: the one-line bug's re-imported copies dropped, every entry one line (goldlib repairLedger). */
function cmdLedgerRepair(args) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const { entries, dropped } = repairLedger(st.ledger);
  if (!dropped.length && entries.every((e, i) => e.text === st.ledger[i].text)) { console.log(`[gold] ${ctx.subject}: ledger clean (${st.ledger.length} lines)`); return 0; }
  console.log(`[gold] ${ctx.subject}: ${dropped.length} re-imported copy line(s) ${args.dry ? "would be " : ""}dropped (entries ${dropped.join(", ")}) · ${st.ledger.length} -> ${entries.length} lines`);
  if (args.dry) return 0;
  st.ledger = entries;
  saveState(ctx, st);
  return 0;
}

function cmdOwner(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  if (st.phase !== "owner") refuse(`${ctx.subject} is in phase ${st.phase}: the owner decides in phase owner`);
  const note = str(args.note);
  const n = [args.accept, args.review, args["extra-round"]].filter(Boolean).length;
  if (n !== 1) refuse("one of --accept | --review | --extra-round", 3);
  if (args.accept) { st.phase = "done"; st.ledger.push({ round: st.round, role: "owner", text: `owner: accepted r${st.round}${note ? ` — ${note}` : ""}` }); }
  else if (args.review) { st.phase = "review"; st.ledger.push({ round: st.round, role: "owner", text: `owner: one more critic review of r${st.round}${note ? ` — ${note}` : ""}` }); }
  else {
    st.phase = "model"; st.round += 1; st.roundType = roundTypeOf(st.round, config.rounds.cap);
    st.ledger.push({ round: st.round, role: "owner", text: `owner: extra round r${st.round} (${st.roundType})${note ? ` — ${note}` : ""}` });
  }
  saveState(ctx, st);
  console.log(`[gold] ${ctx.subject}: phase ${st.phase} r${st.round} · NEXT: ${nextAction(st, facts(ctx, config, st)).cmd}`);
  return 0;
}

/** note — one ledger line written through the state (a setup step outside gold.mjs: turnaround.mjs, a semantic fix). */
/**
 * `pipeline --subject s --set gold|direct`: subject.json `pipeline` (owner 2026-10-12: the game items run gold v8 as class
 * weapon). gold applies classes/<class>.json `gold` (scripts/subject.mjs); only before round 1 (no state, or phase setup).
 */
function cmdPipeline(args) {
  const s = str(args.subject), to = str(args.set);
  if (!["gold", "direct"].includes(to)) refuse("--set gold | direct", 3);
  const sf = path.join(ROOT, "subjects", s, "subject.json");
  if (!exists(sf)) refuse(`no ${rel(sf)}`);
  const sj = readJson(sf);
  if (to === "gold" && !readJson(path.join(ROOT, "classes", `${sj.class}.json`)).gold) refuse(`classes/${sj.class}.json has no gold block (class ${sj.class} runs gold without one: no --set needed)`);
  const stf = path.join(ROOT, "out", "ref", "gold", s, "state.json");
  const phase = exists(stf) ? readJson(stf).phase : null;
  if (phase && phase !== "setup") refuse(`${s} is in phase ${phase}: the pipeline changes only before round 1 (it changes the gate and the eyes)`);
  if (sj.pipeline === to) { console.log(`[gold] ${s}: pipeline already ${to}`); return 0; }
  sj.pipeline = to;
  fs.writeFileSync(sf, `${JSON.stringify(sj, null, 2)}
`);
  console.log(`[gold] ${rel(sf)}: pipeline ${to}${to === "gold" ? ` (classes/${sj.class}.json gold block applies)` : ""}`);
  return 0;
}

function cmdNote(args) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const text = str(args.text);
  if (!text || !text.trim()) refuse('note --text "<one line>" (its first word is its role: setup / audit / eyes / drift / note ...)', 3);
  if (text.includes("\n") || text.includes("\r")) refuse("a ledger line is one line", 3);
  const r = roleOf(text.trim(), st.round);
  st.ledger.push({ round: st.round, role: r.role, text: text.trim() });
  saveState(ctx, st);
  console.log(`[gold] ${ctx.subject}: ledger line (${r.role}, r${st.round}) recorded · ${rel(ctx.ledgerFile)}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// commit — explicit pathspecs only, git add -f for out/, a generated message
// ---------------------------------------------------------------------------------------------------------------------

function git(argv, opts = {}) {
  const r = spawnSync("git", argv, { cwd: ROOT, encoding: "utf8", maxBuffer: 64 << 20, windowsHide: true, ...opts });
  return { code: r.status ?? -1, out: r.stdout ?? "", err: r.stderr ?? "" };
}

function dirtyFiles(ctx, st) {
  const tdir = path.join(ROOT, "subjects", ctx.subject, "turnaround");
  const turnaroundFiles = exists(tdir) ? fs.readdirSync(tdir, { withFileTypes: true }).filter((d) => d.isFile() && /\.png$/i.test(d.name)).map((d) => d.name) : [];
  // + the concept, its prompt README and the concept frame (a new subject's setup: gold.mjs new, hull.mjs --write-frame)
  const extra = [ctx.S.rel.target, ctx.S.rel.target?.replace(/[.]png$/i, ".README.md"), ctx.S.rel.layoutMeasured].filter(Boolean);
  const cands = commitCandidates({ subject: ctx.subject, dirRel: ctx.dirRel, round: st.round, order: ctx.order, turnaroundFiles, extra }).filter((f) => exists(path.join(ROOT, f)));
  if (!cands.length || path.isAbsolute(ctx.dirRel)) return [];
  // cwd-relative on both sides (git status --porcelain would print repo-root paths): new = not tracked, else changed vs HEAD
  const lines = (r) => new Set(r.out.split(/\r?\n/).filter(Boolean));
  const tracked = lines(git(["ls-files", "--", ...cands]));
  const changed = lines(git(["diff", "--name-only", "--relative", "HEAD", "--", ...cands]));
  return cands.filter((f) => !tracked.has(f) || changed.has(f));
}

function cmdCommit(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  if (path.isAbsolute(ctx.dirRel)) refuse(`${ctx.dirRel} is outside the repo: nothing to commit (a replay copy)`);
  const files = dirtyFiles(ctx, st);
  if (!files.length) { console.log(`[gold] ${ctx.subject}: nothing to commit`); return 0; }
  // the headline = the newest ledger line this commit adds (the committed state.json's ledger length), never a stale one
  const head = git(["show", `HEAD:./${ctx.dirRel}/state.json`]);
  let prev = null;
  if (head.code === 0) { try { prev = JSON.parse(head.out).ledger?.length ?? null; } catch { prev = null; } } else prev = 0;
  const msg = commitMessage(st, { prev, files });
  if (args.dry) { console.log(`[gold] would commit ${files.length} file(s):\n  ${files.join("\n  ")}\n--- message ---\n${msg}`); return 0; }
  const a = git(["add", "-f", "--", ...files]);
  if (a.code !== 0) refuse(`git add failed: ${a.err.trim()}`);
  const c = git(["commit", "-F", "-", "--", ...files], { input: msg });
  if (c.code !== 0) refuse(`git commit failed: ${(c.err || c.out).trim()}`);
  const h = git(["rev-parse", "--short", "HEAD"]).out.trim();
  console.log(`[gold] committed ${h}: ${files.length} file(s) · ${msg.split("\n")[0].slice(0, 160)}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// apply-audit — the owner-approved setup proposal into views.json / probes.json / the state
// ---------------------------------------------------------------------------------------------------------------------

async function cmdApplyAudit(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  if (st.phase !== "setup") refuse(`${ctx.subject} is in phase ${st.phase}, not setup`);
  if (!args["owner-approved"]) refuse("apply-audit applies an OWNER-approved proposal: pass --owner-approved once the owner has approved audit/AUDIT.md (the setup gate)");
  const ad = path.join(ctx.dir, "audit");
  const af = path.join(ad, "audit.json"), df = path.join(ad, "views.drift.json"), pf = path.join(ad, "probes.json");
  for (const f of [af, df, pf]) if (!exists(f)) refuse(`missing ${rel(f)} (the auditor's proposal)`);
  const audit = readJson(af);
  if (audit.done !== true) refuse(`${rel(af)} has done:false: resume the auditor`);
  if (Array.isArray(audit.semantic) && audit.semantic.length) refuse(`the audit lists ${audit.semantic.length} semantic defect(s) (${audit.semantic.map((x) => x.id).join(", ")}): fix the images, re-run the doctor and the auditor`);
  const regen = Object.entries(audit.views ?? {}).filter(([, v]) => v?.regenerate).map(([k]) => k);
  if (regen.length) {
    const ts = turnaroundStop(ctx, config);
    if (ts?.stop.spent) refuse(`the audit asks to regenerate ${regen.join(", ")} but the setup stop rule is spent (${ts.stop.why}): re-brief the auditor (gold.mjs brief --subject ${ctx.subject} --role auditor: READY with target-wins rulings), then apply`);
    refuse(`the audit asks to regenerate ${regen.join(", ")}: regenerate, re-run the doctor and the auditor`);
  }
  const ownerQs = [...(audit.blocks ?? []).filter((b) => b.decision === "owner"), ...(audit.open ?? []).filter((o) => o.owner)];
  const note = str(args["owner-note"]);
  if (ownerQs.length && !note) refuse(`the audit asks the owner ${ownerQs.length} question(s) (${ownerQs.map((q) => q.id ?? q.key).join(", ")}): pass --owner-note "<the owner's answer>"`);
  const run = parseRun(args.run);
  const acceptArg = str(args["accept-blocks"]);
  if (acceptArg === "audit" && !(Array.isArray(audit.acceptBlocks) && audit.acceptBlocks.length)) refuse("--accept-blocks audit: audit.json has no acceptBlocks list — omit the flag when the auditor listed none (naming ids is the owner's: a standing BLOCK parks the subject for the owner packet)");
  if (acceptArg && !note) refuse("--accept-blocks records an owner ruling: pass --owner-note too");
  // views.json: drift (owner-approved), families, per-view shift / scale — span-preserving edits
  let text = fs.readFileSync(ctx.viewsFile, "utf8");
  const proposal = readJson(df);
  const drift = proposal.views && proposal.drift ? proposal.drift : proposal;
  const audited = `${String(drift.audited ?? `${today()} gold-auditor`).replace(/\s*\(proposal\)\s*$/, "")}, owner-approved ${today()}`;
  const newDrift = { audited, ...Object.fromEntries(Object.entries(drift).filter(([k]) => k !== "audited")) };
  text = setJsonKey(text, ["drift"], (ind) => driftJson(newDrift, ind));
  const fam = audit.families ?? {};
  for (const k of ["enclosedFg", "holes", "fgMax"]) if (fam[k] !== undefined && fam[k] !== null) text = setJsonKey(text, ["families", k], () => JSON.stringify(fam[k]));
  const applied = [];
  for (const [v, x] of Object.entries(audit.views ?? {})) {
    if (!ctx.spec.views[v]) refuse(`audit.json views.${v}: not a view of ${ctx.subject}`);
    for (const k of ["shift", "scale"]) if (x?.[k]) { text = setJsonKey(text, ["views", v, k], () => inlineJson(x[k])); applied.push(`${v}.${k} ${JSON.stringify(x[k])}`); }
  }
  // validate before writing: the drift must parse (ortho.mjs driftOf) and every rect exist
  const { driftOf } = await import("../v6/ortho.mjs");
  const parsed = JSON.parse(text);
  driftOf(parsed);
  fs.writeFileSync(ctx.viewsFile, text);
  fs.copyFileSync(pf, path.join(ROOT, "subjects", ctx.subject, "probes.json"));
  for (const d of audit.decided ?? []) if (typeof d?.key === "string") addItem(st, "decided", { key: d.key, value: d.value ?? null, basis: d.basis ?? "setup audit", round: 0, evidence: String(d.evidence ?? "").slice(0, 240) });
  for (const o of audit.open ?? []) if (typeof o?.text === "string" && !o.owner) addItem(st, "open", { key: o.key ?? "fact:setup", text: `setup: ${o.text}`, owner: false }, (x) => [x.key, x.text]);
  if (note) addItem(st, "decided", { key: "fact:owner-setup", value: note, basis: "owner (setup gate)", round: 0, evidence: ownerQs.map((q) => q.id ?? q.key).join(", ") });
  st.runs.push({ role: "auditor", seat: "opus", round: 0, calls: run?.calls ?? null, minutes: run?.minutes ?? null, ok: true });
  const nRects = Object.entries(newDrift).filter(([, l]) => Array.isArray(l)).map(([k, l]) => `${k} ${l.length}`).join(" / ");
  // the doctor on the applied setup
  const dj = path.join(ctx.dir, "doctor.json");
  const d = runNode(["scripts/v7/doctor.mjs", "--subject", ctx.subject, "--no-tools", "--json", dj, ...(exists(path.join(ctx.dir, "start.mjs")) ? ["--module", path.join(ctx.dir, "start.mjs")] : [])]);
  process.stdout.write(d.out);
  const rep = exists(dj) ? readJson(dj) : { verdict: "BLOCK", rows: [] };
  const ctx2 = ctxOf(ctx.subject, args);   // views.json re-read
  st.eyesHash = eyesNow(ctx2, config).hash;
  st.ledger.push({ round: 0, role: "audit", text: `setup audit applied (owner-approved ${today()}): drift rects ${nRects || "none"} · probes ${readJson(pf).length ?? "?"} · families ${JSON.stringify(fam)}${applied.length ? ` · views ${applied.join(", ")}` : ""} · decided ${(audit.decided ?? []).length}${note ? ` · owner: ${note.slice(0, 160)}` : ""} · doctor ${rep.verdict}` });
  // --accept-blocks id,id: the owner accepts named doctor BLOCK rows as setup rulings (recorded; needs --owner-note)
  // `--accept-blocks audit`: the rows the auditor listed (audit.json acceptBlocks: its target-wins rulings, the setup stop rule)
  const accept = acceptArg === "audit" ? audit.acceptBlocks.map(String) : acceptArg ? acceptArg.split(",").map((x) => x.trim()).filter(Boolean) : [];
  if (accept.length && !note) refuse("--accept-blocks records an owner ruling: pass --owner-note too");
  const blocks = (rep.rows ?? []).filter((r) => r.level === "BLOCK").map((r) => r.id);
  const unaccepted = blocks.filter((id) => !accept.includes(id));
  if (accept.length && blocks.length) {
    addItem(st, "decided", { key: "fact:accepted-blocks", value: blocks.filter((id) => accept.includes(id)).join(", "), basis: "owner (setup gate)", round: 0, evidence: note.slice(0, 240) });
    st.ledger.push({ round: 0, role: "audit", text: `doctor BLOCK row(s) accepted by owner ruling: ${blocks.filter((id) => accept.includes(id)).join(", ")}${unaccepted.length ? ` · still BLOCK: ${unaccepted.join(", ")}` : ""}` });
  }
  // a standing (unaccepted) doctor BLOCK is the owner's call: one open owner item (the owner packet shows it; NEXT names it)
  st.items.open = st.items.open.filter((o) => o.key !== "setup:doctor-block");
  if (rep.verdict === "BLOCK" && unaccepted.length) addItem(st, "open", { key: "setup:doctor-block", text: `doctor BLOCK row(s) ${unaccepted.join(", ")} stand after the setup audit: the owner accepts them (apply-audit --owner-approved --owner-note "<the owner's words>" --accept-blocks ${unaccepted.join(",")}) or the reference is fixed`, owner: true });
  if (rep.verdict !== "BLOCK" || (blocks.length && !unaccepted.length)) { st.phase = "model"; st.round = 1; st.roundType = roundTypeOf(1, config.rounds.cap); }
  await recordEyes(ctx2, config, exists(path.join(ctx.dir, "start.mjs")) ? path.join(ctx.dir, "start.mjs") : ctx.model, "apply-audit");
  if (st.phase === "setup") st.setupApplied = { audit: sha256(af), eyes: st.eyesHash }; else delete st.setupApplied;
  saveState(ctx2, st);
  console.log(`[gold] ${ctx.subject}: audit applied · doctor ${rep.verdict}${accept.length ? ` (accepted: ${accept.join(", ")})` : ""} · phase ${st.phase}${st.phase === "setup" ? " (round 1 starts only on a doctor PASS / WARN or every BLOCK row accepted with --accept-blocks)" : ""} · NEXT: ${nextAction(st, facts(ctx2, config, st)).cmd}`);
  return rep.verdict === "BLOCK" ? 1 : 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// drift add | rm — only at a round boundary, owner-approved; re-baselines
// ---------------------------------------------------------------------------------------------------------------------

async function driftShare(ctx, image, rects) {
  const { loadTurnaround, maskOptions } = await import("../v6/ortho.mjs");
  const { careMask, targetState, readRGB, SUBJECT, OCCLUDED } = await import("../registered.mjs");
  const { reg, table } = await loadTurnaround(ctx.subject);
  if (image === "concept") {
    const img = await readRGB(ctx.S.paths.target);
    const T0 = targetState(ctx.S, img, table.fgMax, maskOptions(table, "concept"));
    const TA = targetState(ctx.S, img, table.fgMax, { ...maskOptions(table, "concept"), dontCare: rects });
    let n = 0, m = 0;
    for (let i = 0; i < T0.length; i += 1) if (T0[i] === SUBJECT) { n += 1; if (TA[i] === OCCLUDED) m += 1; }
    return n ? m / n : 0;
  }
  const { img } = reg.views[image];
  const care = careMask(rects, img.w, img.h);
  let n = 0, m = 0;
  for (let i = 0; i < img.fam.length; i += 1) if (img.fam[i] !== 0) { n += 1; if (care && !care[i]) m += 1; }
  return n ? m / n : 0;
}

async function cmdDrift(args, config) {
  const op = args._[0];
  if (op !== "add" && op !== "rm") refuse("drift add | rm", 3);
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const gate = driftBoundary(st, exists(briefMetaFile(ctx, st.round)));
  if (!gate.ok) refuse(`drift ${op} refused: ${gate.why} — drift rects change only at a round boundary (after merge, before brief; setup; owner)`);
  if (!args["owner-approved"]) refuse("drift rects are an owner decision: pass --owner-approved once the owner approved this rect");
  let text = fs.readFileSync(ctx.viewsFile, "utf8");
  const spec = JSON.parse(text);
  const drift = spec.drift && typeof spec.drift === "object" ? structuredClone(spec.drift) : { audited: `${today()} gold.mjs drift` };
  const images = [...ctx.views, "concept"];
  let line;
  let image;
  if (op === "add") {
    image = str(args.image);
    const decides = str(args.decides), why = str(args.why);
    if (!images.includes(image)) refuse(`--image one of ${images.join(", ")}`, 3);
    if (!images.includes(decides) || decides === image) refuse(`--decides another image (${images.join(", ")})`, 3);
    if (!why) refuse("--why \"<one line with the measurement>\"", 3);
    const rect = String(args.rect ?? "").split(",").map(Number);
    if (rect.length !== 4 || rect.some((x) => !Number.isFinite(x)) || !(rect[2] > rect[0] && rect[3] > rect[1])) refuse("--rect x0,y0,x1,y1 (that image's px, x1 > x0, y1 > y0)", 3);
    const used = new Set(Object.values(drift).filter(Array.isArray).flat().map((d) => d.id));
    let id = str(args.id);
    if (!id) { let k = 1; while (used.has(`D${k}`)) k += 1; id = `D${k}`; }
    if (used.has(id)) refuse(`drift id ${id} exists`);
    drift[image] = [...(Array.isArray(drift[image]) ? drift[image] : []), { id, rect, decides, why }];
    const share = await driftShare(ctx, image, drift[image].map((d) => d.rect));
    if (share > 0.05 + 1e-9) refuse(`${image} drift rects would cover ${(share * 100).toFixed(1)} % of its reference foreground (> 5 %): a whole-view disagreement is a setup ruling (regenerate the view), not drift`);
    line = `drift: add ${id} ${image} [${rect.join(", ")}] decides ${decides} — ${why} (owner-approved; ${image} ${(share * 100).toFixed(1)} % masked)`;
  } else {
    const id = str(args.id);
    image = Object.keys(drift).find((k) => Array.isArray(drift[k]) && drift[k].some((d) => d.id === id));
    if (!image) refuse(`no drift rect ${id}`);
    const gone = drift[image].find((d) => d.id === id);
    drift[image] = drift[image].filter((d) => d.id !== id);
    line = `drift: rm ${id} ${image} [${gone.rect.join(", ")}] (owner-approved)`;
  }
  text = setJsonKey(text, ["drift"], (ind) => driftJson(drift, ind));
  const { driftOf } = await import("../v6/ortho.mjs");
  driftOf(JSON.parse(text));
  fs.writeFileSync(ctx.viewsFile, text);
  const ctx2 = ctxOf(ctx.subject, args);
  // re-baseline: a closed round's end numbers under the new rects (setup / an unbriefed round: the next brief does it)
  if (["owner", "done", "review"].includes(st.phase) && exists(ctx.model)) {
    const json = path.join(ctx.dir, "baseline", `r${st.round}-end.json`);
    const { rec } = stepJson(ctx2, ctx.model, json);
    st.baseline = { file: rel(json), views: viewsIA(rec.views) };
    line += ` · re-baselined ${viewsText(rec.views, ctx.order)}`;
  }
  st.eyesHash = eyesNow(ctx2, config).hash;
  st.ledger.push({ round: st.round, role: "drift", text: line });
  const ref = eyesRecord(ctx2)?.module;
  if (ref && exists(path.resolve(ROOT, ref))) await recordEyes(ctx2, config, path.resolve(ROOT, ref), `drift ${op}`);
  saveState(ctx2, st);
  console.log(`[gold] ${line}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// Eye changes at a round boundary: shift (views.json per-view shift) and override (subject.json ruleOverrides)
// ---------------------------------------------------------------------------------------------------------------------

/** Where the subject stands for an eye change (goldlib eyeBoundary) + the module the change is measured on. */
function boundaryOf(ctx, st) {
  const mf = briefMetaFile(ctx, st.round);
  const briefOpen = st.phase === "model" && exists(mf);
  let steps = 0, meta = null;
  if (briefOpen) { meta = readJson(mf); steps = savedSteps(ctx).filter((s) => s.n > meta.stepsAtStart).length; }
  const criticStarted = st.phase === "review" && SEATS.some((s) => exists(path.join(ctx.dir, "brief", `r${st.round}-critic-${s}.md`)) || exists(critiqueFile(ctx, st.round, s)));
  const b = eyeBoundary(st, { briefOpen, steps, criticStarted });
  if (b.ok && b.rebase === "start" && !sameBytes(ctx.model, path.join(ctx.dir, meta.start))) return { ...b, ok: false, why: `round ${st.round} is open and model.mjs differs from ${meta.start} (unsaved edits)` };
  const start = path.join(ctx.dir, "start.mjs");
  const module = st.phase === "setup" ? (exists(start) ? start : ctx.model) : ctx.model;
  // setup before the scaffold: no module yet — an override is written unmeasured (the doctor measures start.mjs later)
  if (b.ok && !exists(module)) return st.phase === "setup" ? { ...b, module: null, meta } : { ...b, ok: false, why: `no module to measure on (${rel(module)})` };
  return { ...b, module, meta };
}

/**
 * After an eye change: re-baseline where the phase needs it (the round end + the critics' / owner's pages, or an open
 * round's start), the state's eyes hash, the eyes reference re-recorded (= eyes-check --update of this subject).
 * Returns {ctx (views.json re-read), notes}.
 */
async function afterEyeChange(args, config, st, b, by) {
  const ctx = ctxOf(args.subject, args);
  const notes = [];
  if (b.rebase === "end" && exists(ctx.model)) {
    const json = path.join(ctx.dir, "baseline", `r${st.round}-end.json`);
    const { rec } = stepJson(ctx, ctx.model, json);
    st.baseline = { file: rel(json), views: viewsIA(rec.views) };
    const v = runNode(["scripts/v6/view.mjs", "--subject", ctx.subject, "--module", ctx.model, "--out", path.join(ctx.dir, "view"), "--zoom"]);
    notes.push(`re-baselined r${st.round} end ${viewsText(rec.views, ctx.order)}${v.code === 0 ? " · pages re-made" : ` · view.mjs --zoom FAILED (exit ${v.code})`}`);
  } else if (b.rebase === "start") {
    const json = path.resolve(ROOT, b.meta.baseline);
    const { rec } = stepJson(ctx, ctx.model, json);
    st.baseline = { file: rel(json), views: viewsIA(rec.views) };
    fs.writeFileSync(briefMetaFile(ctx, st.round), `${JSON.stringify({ ...b.meta, eyesHash: eyesNow(ctx, config).hash }, null, 2)}\n`);
    notes.push(`re-baselined the r${st.round} start ${viewsText(rec.views, ctx.order)} — re-brief the modeller (gold.mjs brief --subject ${ctx.subject} --role modeller${flagsOf(ctx)})`);
  }
  st.eyesHash = eyesNow(ctx, config).hash;
  const ref = eyesRecord(ctx)?.module;
  if (ref && exists(path.resolve(ROOT, ref))) await recordEyes(ctx, config, path.resolve(ROOT, ref), by);
  return { ctx, notes };
}

const signed = (x) => `${x >= 0 ? "+" : "-"}${Math.abs(x).toFixed(3)}`;

/**
 * shift — a view's shift measured (view.mjs per candidate on the current model; --pair: the other view gets the mirrored
 * value), the agree table printed, the best (or --right / --up x) applied with a `_shift` evidence note, a ledger line, the
 * eyes reference re-recorded. The live views.json is restored byte for byte after the sweep.
 */
async function cmdShift(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const b = boundaryOf(ctx, st);
  if (!b.ok) refuse(`shift refused: ${b.why} — a view shift is an eye change: only at a round boundary (setup; model before the first saved step; review before any critic; owner / done)`);
  const view = str(args.view);
  if (!view || !ctx.spec.views[view]) refuse(`--view one of ${ctx.views.join(", ")}`, 3);
  const why = str(args.why);
  if (!why) refuse('--why "<what skews the view: one line>"', 3);
  const direct = ["right", "up"].filter((k) => str(args[k]) !== null);
  if (direct.length > 1 || (direct.length && str(args.sweep))) refuse("one of --sweep a,b,c | --right x | --up x", 3);
  const axis = direct[0] ?? str(args.axis) ?? "right";
  if (!["right", "up"].includes(axis)) refuse("--axis right | up", 3);
  const values = (direct.length ? [str(args[axis])] : String(str(args.sweep) ?? "").split(",")).filter((x) => x.trim() !== "").map(Number);
  if (!values.length || values.some((x) => !Number.isFinite(x) || Math.abs(x) > 2)) refuse("--sweep a,b,c | --right x | --up x: shifts in metres (|x| <= 2)", 3);
  let pair = null;
  if (str(args.pair)) {
    const p = str(args.pair).split(",").map((x) => x.trim());
    if (p.length !== 2 || !p.includes(view) || p.some((v) => !ctx.spec.views[v]) || p[0] === p[1]) refuse(`--pair <view>,<other view> naming --view ${view}`, 3);
    if (axis !== "right") refuse("--pair mirrors a right shift (front / rear): --axis right", 3);
    pair = p.find((v) => v !== view);
  }
  const original = fs.readFileSync(ctx.viewsFile, "utf8");
  const r4 = (x) => Math.round(x * 1e4) / 1e4;
  const cur = ctx.spec.views[view].shift?.[axis] ?? 0;
  const textFor = (val) => {
    let t = setJsonKey(original, ["views", view, "shift"], () => inlineJson({ ...(ctx.spec.views[view].shift ?? {}), [axis]: r4(val) }));
    if (pair) t = setJsonKey(t, ["views", pair, "shift"], () => inlineJson({ ...(ctx.spec.views[pair].shift ?? {}), right: r4(-val) }));
    return t;
  };
  const measure = async () => {
    const r = await renderRef(ctx.subject, rel(b.module));
    if (r.error) throw new Error(r.error);
    return Object.fromEntries(ctx.order.map((v) => [v, r.views[v]?.agree ?? NaN]));
  };
  const rows = [];
  try {
    rows.push({ label: "BASE", value: cur, views: await measure() });
    for (const [i, val] of values.entries()) {
      if (Math.abs(val - cur) < 1e-9 && (!pair || Math.abs((ctx.spec.views[pair].shift?.right ?? 0) + val) < 1e-9)) continue;
      fs.writeFileSync(ctx.viewsFile, textFor(val));
      rows.push({ label: `#${i + 1}`, value: val, views: await measure() });
    }
  } finally {
    fs.writeFileSync(ctx.viewsFile, original);
  }
  if (fs.readFileSync(ctx.viewsFile, "utf8") !== original) refuse(`${rel(ctx.viewsFile)} was not restored: git diff -- ${rel(ctx.viewsFile)}`);
  const res = shiftWinner(rows);
  if (direct.length) res.winner = res.rows.find((r) => r.label !== "BASE") ?? res.rows[0];
  console.log(`[gold] shift ${ctx.subject} ${view}${pair ? ` / ${pair}` : ""} ${axis} at ${b.label} on ${rel(b.module)} (agree per image; Δ vs BASE):`);
  for (const l of shiftTable(res, ctx.order, { view, pair, axis })) console.log(`  ${l}`);
  const w = res.winner, base = res.rows.find((r) => r.label === "BASE");
  const shifted = [view, ...(pair ? [pair] : [])];
  const agreeText = [...shifted.map((v) => `${v} ${base.views[v].toFixed(3).replace(/^0/, "")}->${w.views[v].toFixed(3).replace(/^0/, "")}`),
    ...ctx.order.filter((v) => !shifted.includes(v)).map((v) => `${v} ${signed(w.delta[v])}`)].join(", ");
  const sweep = `candidates ${res.rows.filter((r) => r.label !== "BASE").map((r) => signed(r.value)).join(" / ")} vs BASE ${signed(cur)}`;
  if (w.label === "BASE") {
    st.ledger.push({ round: st.round, role: "eyes", text: `eyes: ${b.label} shift sweep ${view}${pair ? ` / ${pair}` : ""} ${axis} (${sweep}) on ${rel(b.module)}: BASE kept, views.json unchanged — ${why}` });
    saveState(ctx, st);
    console.log("[gold] BASE wins: views.json unchanged (ledger line recorded)");
    return 0;
  }
  const note = `${today()} gold.mjs shift at ${b.label}: ${why}; measured on ${rel(b.module)} (${sweep}): agree ${agreeText}`;
  let text = textFor(w.value);
  text = setJsonKey(text, ["views", view, "_shift"], () => JSON.stringify(note));
  if (pair) text = setJsonKey(text, ["views", pair, "_shift"], () => JSON.stringify(`${note} (the pair of ${view}: the mirrored value)`));
  const { driftOf } = await import("../v6/ortho.mjs");
  driftOf(JSON.parse(text));
  fs.writeFileSync(ctx.viewsFile, text);
  const { ctx: ctx2, notes } = await afterEyeChange(args, config, st, b, `shift ${view}`);
  st.ledger.push({ round: st.round, role: "eyes", text: `eyes: ${b.label} eye change: views.json ${view}${pair ? ` / ${pair}` : ""} shift.${axis} ${signed(cur)} -> ${signed(w.value)}${pair ? ` / ${signed(-w.value)}` : ""} (${why}; measured on ${rel(b.module)}: agree ${agreeText}; ${sweep})${notes.length ? ` · ${notes.join(" · ")}` : ""}` });
  saveState(ctx2, st);
  if (st.phase === "owner") writeOwner(ctx2, config, st, stopOf(st, config, ctx));
  console.log(`[gold] applied ${view}${pair ? ` / ${pair}` : ""} shift.${axis} ${signed(w.value)}${pair ? ` / ${signed(-w.value)}` : ""} · ${notes.join(" · ") || "no re-baseline needed"} · eyes reference re-recorded`);
  console.log(`[gold] NEXT: ${nextAction(st, facts(ctx2, config, st)).cmd} (then gold.mjs commit --subject ${ctx.subject}${flagsOf(ctx)})`);
  return 0;
}

/**
 * override — subject.json ruleOverrides (WP2 {value, evidence}): --wheels, --palette z1,z2, or --palette-auto (the
 * PALETTE_ZONE zones the chain rejects on the current model, their parts as evidence); the chain re-run, a ledger line,
 * the eyes reference re-recorded. A value the chain rejects restores subject.json.
 */
async function cmdOverride(args, config) {
  const ctx = ctxOf(args.subject, args);
  const st = needState(ctx);
  const b = boundaryOf(ctx, st);
  if (!b.ok) refuse(`override refused: ${b.why} — a rule override is an eye change: only at setup or a round boundary`);
  // --running skids alone is a wheels override (no wheels); --running with --wheels qualifies it (WF v8 Generals units)
  const modes = ["wheels", "palette", "palette-auto", "roles", "tris", "mirror-centred"].filter((k) => (k === "palette-auto" ? !!args[k] : k === "wheels" ? str(args.wheels) !== null || str(args.running) !== null : str(args[k]) !== null));
  if (modes.length !== 1) refuse("one of --wheels count,axles,equal|per-axle[,lo,hi] [--running tracks|skids] | --running skids | --palette z1,z2 | --palette-auto | --roles r1,r2 | --tris <n> | --mirror-centred p1,p2", 3);
  const mode = modes[0];
  const evidenceArg = str(args.evidence);
  if (mode !== "palette-auto" && !evidenceArg) refuse('--evidence "<the measurement: what the target draws>" (an override is a measurement, not a wish)', 3);
  const chainOf = () => runNode(["scripts/v7/inspect.mjs", "chain", "--module", b.module, "--subject", ctx.subject]);
  if (mode === "palette-auto" && !b.module) refuse("--palette-auto measures the chain: scaffold start.mjs first", 3);
  let name, value, evidence, what;
  if (mode === "wheels") {
    try { value = wheelsValue(str(args.wheels), str(args.running)); } catch (e) { refuse(e.message, 3); }
    name = "wheels"; evidence = evidenceArg;
    what = `wheels ${value.count}/${value.axles} ${value.diameters}${value.diameterFrac ? ` [${value.diameterFrac.join(", ")}]` : ""}${value.running ? ` running ${value.running}` : ""}`;
  } else if (mode === "tris") {
    try { value = trisValue(str(args.tris), TRIS_OVERRIDE_CAP); } catch (e) { refuse(e.message, 3); }
    name = "tris"; evidence = evidenceArg; what = `tris ${value}`;
  } else if (mode === "roles") {
    const roles = str(args.roles).split(",").map((x) => x.trim()).filter(Boolean);
    if (!roles.length || roles.some((z) => !/^[a-z][a-z0-9_]*$/.test(z))) refuse("--roles r1,r2 (lower-case role names)", 3);
    name = "roles"; value = { extra: roles }; evidence = evidenceArg; what = `roles extra ${roles.join(", ")}`;
  } else if (mode === "mirror-centred") {
    try { value = mirrorCentredValue(str(args["mirror-centred"])); } catch (e) { refuse(e.message, 3); }
    name = "mirror"; evidence = evidenceArg; what = `mirror centred ${value.centred.join(", ")}`;
  } else if (mode === "palette") {
    const zones = str(args.palette).split(",").map((x) => x.trim()).filter(Boolean);
    if (!zones.length || zones.some((z) => !/^[A-Za-z][\w-]*$/.test(z))) refuse("--palette z1,z2 (zone names)", 3);
    name = "paletteZones"; value = { extra: zones }; evidence = evidenceArg; what = `paletteZones extra ${zones.join(", ")}`;
  } else {
    const c = chainOf();
    const zones = paletteZoneViolations(c.out);
    if (!Object.keys(zones).length) { console.log(`[gold] ${ctx.subject}: no PALETTE_ZONE rows on ${rel(b.module)} (${(/^pass (true|false)/m.exec(c.out) ?? [])[0] ?? tail(c, 2)}): nothing to add`); return 0; }
    name = "paletteZones"; value = { extra: Object.keys(zones) };
    evidence = `parts the target draws in their own flat colours that the ${ctx.S.klass} class list lacks (gold.mjs override --palette-auto on ${rel(b.module)}): ${Object.entries(zones).map(([z, e]) => `${z} = ${e.parts} part(s), e.g. ${e.example}`).join("; ")}`;
    if (evidenceArg) evidence = `${evidence}; ${evidenceArg}`;
    what = `paletteZones extra ${Object.keys(zones).join(", ")} (auto)`;
  }
  const sf = path.join(ROOT, "subjects", ctx.subject, "subject.json");
  const original = fs.readFileSync(sf, "utf8");
  const next = withOverride(JSON.parse(original).ruleOverrides, name, value, evidence);
  const text = setJsonKey(original, ["ruleOverrides"], (ind) => JSON.stringify(next, null, 2).replace(/\n/g, `\n${ind}`));
  fs.writeFileSync(sf, text);
  let chainText;
  if (b.module) {
    const c = chainOf();
    const pass = /^pass (true|false)/m.exec(c.out);
    if (!pass) { fs.writeFileSync(sf, original); refuse(`the chain rejects the override (subject.json restored): ${tail(c, 4)}`); }
    const rows = c.out.split(/\r?\n/).filter((l) => l.startsWith("VIOLATION")).map((l) => l.split(/\s+/).slice(1, 3).join(" "));
    chainText = `chain ${pass[1] === "true" ? "PASS" : `FAIL (${rows.slice(0, 6).join(", ")}${rows.length > 6 ? `, +${rows.length - 6}` : ""})`} on ${rel(b.module)}`;
  } else {
    // setup before the scaffold: no module to measure on — the chain's own parser still checks the value's shape
    try { applyRuleOverrides(DEFAULT_LIMITS, next); } catch (e) { fs.writeFileSync(sf, original); refuse(`the chain rejects the override (subject.json restored): ${e.message}`); }
    chainText = "chain not run (setup, no start.mjs yet)";
  }
  const { ctx: ctx2, notes } = await afterEyeChange(args, config, st, b, `override ${name}`);
  const note = str(args.note);
  st.ledger.push({ round: st.round, role: "setup", text: `setup ${b.label}: subject.json ruleOverrides ${what} (WP2 target-wins; gold.mjs override) · ${chainText}${note ? ` · ${note}` : ""}${notes.length ? ` · ${notes.join(" · ")}` : ""}` });
  saveState(ctx2, st);
  if (st.phase === "owner") writeOwner(ctx2, config, st, stopOf(st, config, ctx));
  console.log(`[gold] ${ctx.subject}: ruleOverrides.${name} written · ${chainText}${notes.length ? ` · ${notes.join(" · ")}` : ""} · eyes reference re-recorded`);
  console.log(`[gold] NEXT: ${nextAction(st, facts(ctx2, config, st)).cmd} (then gold.mjs commit --subject ${ctx.subject}${flagsOf(ctx)})`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// eyes-check — every subject's eyes reference re-rendered with view.mjs: must show no change
// ---------------------------------------------------------------------------------------------------------------------

async function cmdEyesCheck(args, config) {
  const subjects = str(args.subject) ? [args.subject] : goldSubjects();
  const jobs = [];
  for (const s of subjects) {
    const ctx = ctxOf(s, args);
    const rec = eyesRecord(ctx);
    const st = readState(ctx);
    let module = rec?.module ? path.resolve(ROOT, rec.module) : null;
    if (!module && args.update && st) {
      const cands = [path.join(ctx.dir, `model-r${st.round}.mjs`), path.join(ctx.dir, `model-r${Math.max(0, st.round - 1)}.mjs`), path.join(ctx.dir, "start.mjs"), ctx.model];
      module = cands.find(exists) ?? null;
    }
    jobs.push({ s, ctx, rec, st, module });
  }
  let bad = 0;
  const queue = [...jobs];
  const out = new Map();
  const worker = async () => {
    while (queue.length) {
      const j = queue.shift();
      if (!j.module || !exists(j.module)) { out.set(j.s, { line: `${j.s.padEnd(14)} ${j.rec ? `MISSING ${j.rec.module}` : "no eyes reference (eyes-check --update records one)"}`, fail: !!j.rec }); continue; }
      if (j.rec && j.rec.moduleSha256 !== textSha(j.module)) { out.set(j.s, { line: `${j.s.padEnd(14)} CHANGED the reference snapshot ${rel(j.module)} itself was edited (snapshots are immutable)`, fail: true }); continue; }
      const r = await renderRef(j.s, rel(j.module));
      if (r.error) { out.set(j.s, { line: `${j.s.padEnd(14)} ERROR ${r.error}`, fail: true }); continue; }
      const eyes = eyesNow(j.ctx, config);
      const files = j.rec ? changedFiles(j.rec.files, eyes.files) : [];
      if (args.update) {
        await recordEyes(j.ctx, config, j.module, "eyes-check --update");
        if (j.st && j.st.phase !== "model") { j.st.eyesHash = eyes.hash; saveState(j.ctx, j.st); }
        out.set(j.s, { line: `${j.s.padEnd(14)} RECORDED ${rel(j.module)} · ${viewsText(r.views, j.ctx.order)}${files.length ? ` · eyes files changed: ${files.join(", ")}` : ""}` });
        continue;
      }
      if (!j.rec) { out.set(j.s, { line: `${j.s.padEnd(14)} no eyes reference (eyes-check --update records one)` }); continue; }
      const same = r.json === j.rec.render.json && r.png === j.rec.render.png;
      const deltas = j.ctx.order.map((v) => {
        const a = r.views[v], b = j.rec.render.views?.[v];
        return a && b && (a.iou !== b.iou || a.agree !== b.agree) ? `${v} iou ${b.iou.toFixed(4)} -> ${a.iou.toFixed(4)} agree ${b.agree.toFixed(4)} -> ${a.agree.toFixed(4)}` : null;
      }).filter(Boolean);
      out.set(j.s, {
        line: `${j.s.padEnd(14)} ${same ? "same" : "CHANGED"} ${rel(j.module)} (view JSON ${r.json === j.rec.render.json ? "=" : "≠"}, sheet ${r.png === j.rec.render.png ? "=" : "≠"})${deltas.length ? ` · ${deltas.join(" · ")}` : ""}${files.length ? ` · eyes files changed since ${j.rec.at}: ${files.join(", ")}${same ? " (outputs identical)" : ""}` : ""}`,
        fail: !same,
      });
    }
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  for (const j of jobs) { const o = out.get(j.s); console.log(`[eyes] ${o.line}`); if (o.fail) bad += 1; }
  console.log(`[eyes] ${bad ? `FAIL ${bad} subject(s) changed` : `clean: ${jobs.length} subject(s)${args.update ? " recorded" : ", no change"}`}`);
  return bad ? 1 : 0;
}

// ---------------------------------------------------------------------------------------------------------------------
// migrate — a v7 subject (LEDGER.md + critique files) into state.json
// ---------------------------------------------------------------------------------------------------------------------

async function cmdMigrate(args, config) {
  const ctx = ctxOf(args.subject, args);
  if (exists(ctx.stateFile) && !args.force) refuse(`${rel(ctx.stateFile)} exists (--force replaces it)`);
  const phase = str(args.phase);
  if (phase !== "owner" && phase !== "setup") refuse("--phase owner | setup", 3);
  const oldText = exists(ctx.ledgerFile) ? fs.readFileSync(ctx.ledgerFile, "utf8") : "";
  const { header, entries } = importLedger(oldText);
  const st = newState(ctx.subject);
  st.ledger = entries;
  // runs: the modeller rounds and the critic seats the ledger and the critique files show
  const rounds = [...new Set(entries.filter((e) => e.role === "modeller").map((e) => e.round))].sort((a, b) => a - b);
  for (const r of rounds) st.runs.push({ role: "modeller", round: r, calls: null, minutes: null, ok: true });
  const seen = new Set();
  for (const e of entries.filter((x) => x.role === "critics")) {
    for (const seat of SEATS) if (new RegExp(`\\b${seat}\\b`, "i").test(e.text)) seen.add(`${e.round}|${seat}`);
  }
  const cdir = path.join(ctx.dir, "critique");
  if (exists(cdir)) for (const f of fs.readdirSync(cdir)) { const m = /^r(\d+)-(fable|opus|sonnet)\.md$/.exec(f); if (m) seen.add(`${Number(m[1])}|${m[2]}`); }
  for (const k of [...seen].sort()) { const [r, seat] = k.split("|"); st.runs.push({ role: "critic", seat, round: Number(r), calls: null, minutes: null, ok: true }); }
  st.runs.sort((a, b) => a.round - b.round || (a.role === "modeller" ? -1 : 1));
  let snap;
  if (phase === "owner") {
    const N = rounds.length ? rounds[rounds.length - 1] : 0;
    st.round = N; st.phase = "owner"; st.roundType = roundTypeOf(N, config.rounds.cap);
    // model-rN.mjs = model.mjs as committed at each round's commit (--rounds 1=<commit>,...)
    const map = Object.fromEntries(String(args.rounds ?? "").split(",").filter(Boolean).map((x) => x.split("=")));
    for (const [r, c] of Object.entries(map)) {
      const g = git(["show", `${c}:./${rel(ctx.model)}`]);   // ./ = relative to hard_surface, not the repo root
      if (g.code !== 0) refuse(`git show ${c}:./${rel(ctx.model)} failed: ${g.err.trim()}`);
      fs.writeFileSync(path.join(ctx.dir, `model-r${r}.mjs`), g.out);
    }
    snap = path.join(ctx.dir, `model-r${N}.mjs`);
    if (!exists(snap)) fs.copyFileSync(ctx.model, snap);
    if (!sameBytes(snap, ctx.model)) refuse(`model-r${N}.mjs (from ${map[N] ?? "model.mjs"}) differs from model.mjs: check --rounds`);
    for (const e of entries.filter((x) => x.role === "owner")) addItem(st, "open", { key: `fact:owner-r${e.round}`, text: e.text.replace(/^OWNER\s*\(open\):\s*/i, ""), owner: true }, (x) => [x.key, x.text]);
    const json = path.join(ctx.dir, "baseline", `r${N}-end.json`);
    const { rec } = stepJson(ctx, ctx.model, json);
    st.baseline = { file: rel(json), views: viewsIA(rec.views) };
    st.modelHash = `sha256:${sha256(ctx.model)}`;
  } else {
    snap = exists(path.join(ctx.dir, "start.mjs")) ? path.join(ctx.dir, "start.mjs") : ctx.model;
    const json = path.join(ctx.dir, "baseline", "r0-start.json");
    const { rec } = stepJson(ctx, snap, json);
    st.baseline = { file: rel(json), views: viewsIA(rec.views) };
  }
  st.eyesHash = eyesNow(ctx, config).hash;
  await recordEyes(ctx, config, snap, `migrate (${phase})`);
  saveState(ctx, st);
  if (phase === "owner") writeOwner(ctx, config, st, "Migrated from the v7 run (4-round cap + the owner's extra round 5): no v8 merge exists; the open items are the ledger's OWNER lines.");
  // round trip: the regenerated LEDGER.md must hold every old line
  const regen = fs.readFileSync(ctx.ledgerFile, "utf8").split(/\r?\n/).filter((l) => l !== LEDGER_MARK).join("\n");
  const same = regen.replace(/\n+$/, "") === oldText.replace(/\r\n/g, "\n").replace(/\n+$/, "");
  const headerSame = !header || header === regen.split("\n")[0];
  if (!same) fs.writeFileSync(path.join(ctx.dir, "LEDGER-v7.md"), oldText);
  console.log(`[gold] ${ctx.subject}: migrated (${phase}, r${st.round}) · ${entries.length} ledger lines · ${st.runs.length} runs · open ${st.items.open.length} · LEDGER round trip ${same ? "identical (+ the generated mark)" : `DIFFERS${headerSame ? "" : " (header)"}: kept LEDGER-v7.md`} · eyes ${rel(ctx.eyesFile)}`);
  return same ? 0 : 1;
}

// ---------------------------------------------------------------------------------------------------------------------
// new — a brand-new subject from one description paragraph (scripts/v7/newsubject.mjs)
// ---------------------------------------------------------------------------------------------------------------------

async function cmdNew(args) {
  const { newSubject, dryRoot } = await import("./newsubject.mjs");
  const df = str(args["desc-file"]);
  if (!df || !exists(path.resolve(df))) refuse("new --desc-file <paragraph.txt>: the parts, their colours and the real size (\"About 3.2 m long, 1.2 m wide and 2.2 m tall\")", 3);
  if (str(args.root) && !args.dry) refuse("--root is for --dry only (a real subject lives under hard_surface)", 3);
  if (str(args.concept) && !args.dry) refuse("--concept is for --dry only (a real concept is generated: TARGETs are frozen)", 3);
  const root = args.dry ? (str(args.root) ? path.resolve(args.root) : dryRoot()) : ROOT;
  const s = args.subject;
  let r;
  try {
    r = await newSubject({ root, subject: s, klass: str(args.class) ?? "vehicle", desc: fs.readFileSync(path.resolve(df), "utf8"), noun: str(args.noun) ?? undefined,
      gen: str(args.gen) ?? "gpt", allowGemini: !!args["allow-gemini"], style: str(args.style) ?? undefined, dry: !!args.dry, concept: str(args.concept), aspect: str(args.aspect) ?? undefined, log: (l) => console.log(l) });
  } catch (e) { refuse(e.message); }
  console.log(`[gold] new ${s}${args.dry ? ` --dry (root ${root}; no generation)` : ""}: ${r.files.length} file(s): ${r.files.join(", ")}`);
  if (r.families) console.log(`[gold] families proposed from the concept: ${Object.entries(r.families.table).map(([k, v]) => `${k} ${v} (${r.families.shares[k]} %)`).join(", ")}`);
  console.log(r.direct ? `[gold] pipeline direct (WF v10, WORKFLOW-V10.md): no gold state, no rounds — the remaining setup chain:` : `[gold] the remaining setup chain (scripts/v7/README.md "New subject, once"; then the gold-model skill SETUP 3-5):`);
  for (const l of r.chain) console.log(`  ${l}`);
  return 0;
}

// ---------------------------------------------------------------------------------------------------------------------

// ---------------------------------------------------------------------------------------------------------------------
// hs (WF v9): the Blender hard-surface look stage after the gold rounds — read-only, the stage from the files present
// ---------------------------------------------------------------------------------------------------------------------

/** WF v10: subjects/<s>/subject.json `pipeline: "direct"` (else its class's): no gold rounds (WORKFLOW-V10.md). */
function hsDirect(s) {
  try {
    const sj = readJson(path.join(ROOT, "subjects", s, "subject.json"));
    if ("pipeline" in sj) return sj.pipeline === "direct";
    return readJson(path.join(ROOT, "classes", `${sj.class}.json`)).pipeline === "direct";
  } catch { return false; }
}

/** The stage of a direct subject from the files present: setup -> build -> review -> polish -> function -> owner. */
function hsReviewComplete(text) {
  if (!text?.trim()) return false;
  const marker = /^\s*ReviewStatus\s*:\s*(\S+)/im.exec(text);
  // Preserve completed legacy reviews; explicit markers take precedence.
  return !marker || marker[1].toUpperCase() === "COMPLETE";
}

function hsFunctionEvidence(f, mtime) {
  let rig = null, error = null;
  if (exists(f("rig_stats.json"))) {
    try { rig = readJson(f("rig_stats.json")); } catch (e) { error = e.message; }
  }
  const missing = ["build.py", "rig.json", "stats.json"].filter(n => !exists(f(n)));
  const stale = ["build.py", "rig.json", "stats.json"].filter(n => mtime(n) > mtime("rig_stats.json"));
  return { rig, error, missing, stale, ready: rig?.pass === true && !missing.length && !stale.length };
}

function hsFunctionNote(evidence) {
  if (evidence.error) return `function: incomplete (unreadable rig_stats.json: ${evidence.error})`;
  if (!evidence.rig) return "function: incomplete (missing rig_stats.json)";
  const rg = evidence.rig;
  return `function: ${evidence.stale.length || evidence.missing.length ? `STALE/incomplete (${[...evidence.stale.map(n => `${n} newer`), ...evidence.missing.map(n => `${n} missing`)].join(", ")}) — was ` : ""}rig ${rg.pass === true ? "PASS" : "FAIL"} ${rg.passed}/${rg.total}${(rg.failed ?? []).length ? ` (failed: ${rg.failed.join(", ")})` : ""}`;
}

function hsStageDirect(s, row, f, mtime) {
  row.pipeline = "direct";
  const P = (...x) => path.join(ROOT, ...x);
  const t = "node scripts/v7/turnaround.mjs", d = `--dir out/turnaround/${s}`;
  const setup = (next) => { row.stage = "setup"; row.next = next; return row; };
  let sj = null, views = null, lm = null;
  try { sj = readJson(P("subjects", s, "subject.json")); } catch { /* below */ }
  if (!sj) return setup(`node scripts/v7/gold.mjs new --subject ${s} --class weapon --style fps --gen gpt --desc-file subjects/_weapons/${s}.txt`);
  if (!exists(P(sj.paths.target))) return setup(`no concept ${sj.paths.target}: node scripts/v7/gold.mjs new --subject ${s} ... (a TARGET is frozen once made)`);
  try { views = readJson(P("subjects", s, "turnaround", "views.json")); } catch { /* below */ }
  try { lm = readJson(P(sj.paths.layoutMeasured)); } catch { /* none yet */ }
  const haveViews = views && Object.values(views.views).every((v) => exists(P("subjects", s, "turnaround", v.file)));
  if (!haveViews) {
    if (!lm?._frame) return setup(`LOOK at ${sj.paths.target}, edit subjects/${s}/turnaround/facts.json (sides / asymmetric / faces), then node scripts/v7/hull.mjs --subject ${s} --write-frame --from facts`);
    if (!exists(P("out", "turnaround", s, "current"))) return setup(`${t} gen --subject ${s} --out out/turnaround/${s} --gen gpt   (then LOOK at out/turnaround/${s}/current/*.png)`);
    return setup(`${t} status --subject ${s} ${d} -> repair --view <v> --gen gpt until the targets are met (the setup stop rule) -> ${t} install --subject ${s} ${d}`);
  }
  if (!lm?._frame || lm._frame.provisional) return setup(`node scripts/v7/hull.mjs --subject ${s} --write-frame   (the installed set's hull fitted to the concept box; the frame is still ${lm?._frame ? "PROVISIONAL (from facts)" : "missing"})`);
  if (!exists(f("frame.json")) || !exists(f("concept_cam.json")) || mtime("concept_cam.json") < fs.statSync(P(sj.paths.layoutMeasured)).mtimeMs) {
    return setup(`node scripts/hs/dump_frame.mjs --subject ${s}; node scripts/hs/dump_concept_cam.mjs --subject ${s}`);
  }
  if (exists(f("stats.json"))) {
    const st = readJson(f("stats.json"));
    const g = st.gate ?? {};
    const low = Object.entries(g.below_best_earlier ?? {}).map(([v, x]) => `${v} ${x.toFixed(3)}`);
    row.notes.push(`final pass ${st.pass}: tris ${st.tris}/${st.budget} · topology ${st.topology_clean ? "clean" : "NOT clean"} · gate ${g.pass ? "pass" : `FAIL${low.length ? ` (${low.join(", ")} below the best earlier pass)` : ""}`} (direct: no gold; agree ${Object.entries(st.scores ?? {}).map(([v, x]) => `${v} ${x.agree.toFixed(3)}`).join(" ")})`);
  }
  const reviewText = ["review_fable.md", "review_opus.md"].map((n) => (exists(f(n)) ? fs.readFileSync(f(n), "utf8") : "")).find((t) => t) || "";
  const reviewComplete = hsReviewComplete(reviewText);
  if (reviewComplete) {
    const m = /likeness score:?\**\s*\**\s*([\d.]+)\s*\/\s*10/i.exec(reviewText);
    if (m) row.notes.push(`Independent likeness ${m[1]} / 10 (before polish)`);
  }
  // New passes after review prove work started, not that its response is complete.
  const polished = exists(f("POLISH.md"));
  if (!polished && reviewComplete && mtime("stats.json") > mtime("review_fable.md")) {
    row.notes.push("polish work exists but POLISH.md is missing: resume the interrupted K = 1 response; do not start another polish round");
  }
  if (!exists(f("stats.json"))) { row.stage = "build"; row.next = `Agent gold-hs-modeller (Sonnet 5.5), prompt "subject: ${s}, mode: build, pipeline: direct" (brief out/blender-hs/BUILD-DIRECT.md)${row.passes ? ` (resumes: ${row.passes} passes, no --final yet)` : ""}`; }
  else if (!reviewComplete) { row.stage = "review"; row.next = `Opus reviewer (general-purpose, model opus, body of .claude/agents/gold-hs-reviewer-fable.md), prompt "subject: ${s}" (blind: no modeller report; finish ReviewStatus: COMPLETE)`; }
  else if (!polished) { row.stage = "polish"; row.next = `Opus (general-purpose, model opus, body of gold-hs-modeller.md), prompt "subject: ${s}, mode: polish, pipeline: direct" (K = 1)`; }
  else if (!hsFunctionEvidence(f, mtime).ready) {
    row.stage = "function";
    row.next = `Agent gold-hs-modeller (Sonnet 5.5), prompt "Subject s = ${s}. Read and follow out/blender-hs/RIG-BRIEF.md (section 'Handheld weapons')" (rig.json physics.mode handheld + scripts/hs/rig_pass.py; one agent per subject)`;
  } else { row.stage = "owner"; row.next = `owner packet: show out/blender-hs/${s}/compare.png + rig_sheet.png${exists(f("POLISH.md")) ? ` + POLISH.md (## Owner items)` : ""}; no further polish round`; }
  if (exists(f("rig_stats.json"))) row.notes.push(hsFunctionNote(hsFunctionEvidence(f, mtime)));
  return row;
}

function hsStage(s, config) {
  const dir = path.join(ROOT, "out", "blender-hs", s);
  const f = (n) => path.join(dir, n);
  const mtime = (n) => (exists(f(n)) ? fs.statSync(f(n)).mtimeMs : 0);
  let phase = null;
  try { phase = readJson(path.join(ROOT, "out", "ref", "gold", s, "state.json")).phase; } catch { /* no gold state */ }
  const passes = exists(dir) ? fs.readdirSync(dir).filter((n) => /^pass\d+_stats\.json$/.test(n)).length : 0;
  const row = { subject: s, phase, passes, stage: null, next: null, notes: [] };
  if (hsDirect(s)) return hsStageDirect(s, row, f, mtime);   // WF v10: no gold rounds for a direct subject
  if (!exists(f("build.py")) && !["owner", "done"].includes(phase)) {
    row.stage = "wait"; row.next = `gold rounds first (gold phase ${phase ?? "none"}; HS starts at phase owner / done)`; return row;
  }
  if (!exists(f("frame.json")) || !exists(f("concept_cam.json"))) row.notes.push(`setup: node scripts/hs/dump_frame.mjs --subject ${s}; node scripts/hs/dump_concept_cam.mjs --subject ${s} (the modeller does it too)`);
  if (exists(f("stats.json"))) {
    const st = readJson(f("stats.json"));
    // gate (scripts/hs/method.md, owner 2026-10-04): no ortho view more than .04 below gold; the concept is not gated
    const low = Object.entries(st.delta_agree ?? {}).filter(([v, d]) => v !== "concept" && d < -0.04).map(([v, d]) => `${v} ${d.toFixed(3)}`);
    row.notes.push(`final pass ${st.pass}: tris ${st.tris}/${st.budget} · topology ${st.topology_clean ? "clean" : "NOT clean"} · gate ${low.length ? `FAIL (${low.join(", ")} below gold)` : "pass"}`);
  }
  const reviewText = ["review_fable.md", "review_opus.md"].map((n) => (exists(f(n)) ? fs.readFileSync(f(n), "utf8") : "")).find((t) => t) || "";
  const reviewComplete = hsReviewComplete(reviewText);
  if (reviewComplete) {
    const m = /likeness score:?\**\s*\**\s*([\d.]+)\s*\/\s*10/i.exec(reviewText);
    if (m) row.notes.push(`Independent likeness ${m[1]} / 10 (before polish)`);
  }
  const polished = exists(f("POLISH.md")) || (reviewComplete && mtime("stats.json") > mtime("review_fable.md"));
  if (!exists(f("stats.json"))) { row.stage = "build"; row.next = `Agent gold-hs-modeller (Sonnet 5.5), prompt "subject: ${s}, mode: build"${passes ? ` (resumes: ${passes} passes, no --final yet)` : ""}`; }
  else if (!reviewComplete) { row.stage = "review"; row.next = `Opus reviewer (general-purpose, model opus, body of .claude/agents/gold-hs-reviewer-fable.md), prompt "subject: ${s}" (blind: no modeller report; finish ReviewStatus: COMPLETE)`; }
  else if (!polished) { row.stage = "polish"; row.next = `Opus (general-purpose, model opus, body of gold-hs-modeller.md), prompt "subject: ${s}, mode: polish" (K = 1)`; }
  else if (!hsFunctionEvidence(f, mtime).ready) {
    row.stage = "function";
    row.next = `Agent gold-hs-modeller (Sonnet 5.5), prompt "Subject s = ${s}. Read and follow out/blender-hs/RIG-BRIEF.md" (rig.json + scripts/hs/rig_pass.py; one agent per subject)`;
  } else { row.stage = "owner"; row.next = `owner packet: show out/blender-hs/${s}/compare.png + rig_sheet.png${exists(f("POLISH.md")) ? ` + POLISH.md (## Owner items)` : ""}; no further polish round`; }
  if (exists(f("rig_stats.json"))) row.notes.push(hsFunctionNote(hsFunctionEvidence(f, mtime)));
  return row;
}

// items-30 stage labels (research/PLAN-ITEMS30.md pipeline S1..S4): printed next to the stage word by `hs`
const HS_STAGE_LABEL = {
  setup: "S1 setup (Opus lane: hero, turnaround, camera, parts.json, doctor --direct)",
  wait: "waiting for the gold rounds",
  build: "S2 build (Sonnet class A / Opus class B; gate HERO + SIGMA + topology + tris + chunky) -> owner pair #1",
  review: "S3a blind reviews (Fable + Opus, heroratio table first, chunky + FPS rows)",
  polish: "S3b Opus reconcile + polish, K=1 -> S3c verify -> owner pair #2",
  function: "S4 FUNCTION.md + rig (pose: / hero-led look tests) -> owner pair #3",
  owner: "owner gate",
};

function cmdHs(args, config) {
  const base = path.join(ROOT, "out", "blender-hs");
  let subjects;
  if (str(args.subject)) subjects = [args.subject];
  else {
    const hsDirs = exists(base) ? fs.readdirSync(base, { withFileTypes: true }).filter((d) => d.isDirectory() && !d.name.startsWith("_")).map((d) => d.name) : [];
    // WF v10: + every direct subject (no gold state, maybe no HS folder yet)
    const sdir = path.join(ROOT, "subjects");
    const directs = fs.readdirSync(sdir, { withFileTypes: true }).filter((d) => d.isDirectory() && !d.name.startsWith("_") && exists(path.join(sdir, d.name, "subject.json")) && hsDirect(d.name)).map((d) => d.name);
    subjects = [...new Set([...hsDirs, ...goldSubjects(), ...directs])].filter((s) => exists(path.join(ROOT, "subjects", s, "subject.json"))).sort();
  }
  const rows = subjects.map((s) => hsStage(s, config));
  if (args.json) { console.log(JSON.stringify(rows, null, 1)); return 0; }
  for (const r of rows) {
    console.log(`[hs] ${r.subject}: stage ${r.stage}${HS_STAGE_LABEL[r.stage] ? ` = ${HS_STAGE_LABEL[r.stage]}` : ""} (${r.pipeline === "direct" ? "pipeline direct: setup → build → review → polish → function → owner" : `gold phase ${r.phase ?? "none"}`}, ${r.passes} passes)`);
    for (const n of r.notes) console.log(`  ${n}`);
    console.log(`  NEXT ${r.next}`);
  }
  return 0;
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest, BOOL);
  if (!cmd || cmd === "--help" || args.help) { console.log(USAGE); return cmd ? 0 : 3; }
  const config = loadConfig(str(args.config) ? path.resolve(args.config) : CONFIG_FILE);
  const needSubject = !["status", "eyes-check", "owner-packet", "hs"].includes(cmd);
  if (needSubject && !str(args.subject)) { console.log(USAGE); return 3; }
  switch (cmd) {
    case "new": return cmdNew(args);
    case "status": return cmdStatus(args, config);
    case "doctor": return cmdDoctor(args, config);
    case "brief": return cmdBrief(args, config);
    case "close": return cmdClose(args, config);
    case "merge": return cmdMerge(args, config);
    case "commit": return cmdCommit(args, config);
    case "apply-audit": return cmdApplyAudit(args, config);
    case "drift": return cmdDrift(args, config);
    case "owner": return cmdOwner(args, config);
    case "eyes-check": return cmdEyesCheck(args, config);
    case "migrate": return cmdMigrate(args, config);
    case "note": return cmdNote(args);
    case "pipeline": return cmdPipeline(args);
    case "shift": return cmdShift(args, config);
    case "override": return cmdOverride(args, config);
    case "owner-packet": return cmdOwnerPacket(args, config);
    case "ledger-repair": return cmdLedgerRepair(args);
    case "hs": return cmdHs(args, config);
    default: console.log(USAGE); return 3;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase()) {
  main().then((c) => { process.exitCode = c ?? 0; }).catch((e) => {
    if (e instanceof Refuse) { console.log(`[gold] REFUSED: ${e.message}`); process.exitCode = e.code; return; }
    console.error(`[gold] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`);
    process.exitCode = 1;
  });
}
