#!/usr/bin/env node
// WF v8 WP3 — the modeller's ONE-COMMAND iteration (research/v7/WF-V8-PLAN.md WP3, WF-REVIEW-opus.md C4). One process,
// <= 15 s, <= 40 printed lines, read-only unless a flag says otherwise:
//
//   node scripts/v7/step.mjs --subject <s> [--module <m.mjs>] [--baseline <json>] [--save [--note "<what changed>"]]
//                            [--revert] [--pages side,concept | all] [--json <file>] [--out <dir>] [--probes <file>]
//
// The module (default out/ref/gold/<s>/model.mjs) is built ONCE: check-module (scripts/check-module.mjs checkModule) ->
// the validator chain (inspect.mjs runChain, only rows NEW vs the baseline print) -> the concept frame refit (lib.mjs
// fitFrame from the module's knob frame, no grid; WARN when the scale moves > 1 % or a shift > 6 px) -> the judge at the
// refitted frame (scripts/v6/judge.mjs: raw + agree IoU per view, the placement checks, the blob table) -> probes
// (subjects/<s>/probes.json, or --probes <file>: a proposal) -> ONE verdict line, `KEEP` or `REVERT: <reasons>` (steplib.mjs stepVerdict).
// Baseline (the round start): --baseline <view or step JSON> (`none`: no comparison, a fresh start), else <dir>/state.json
// `baseline` (its `file`, else its `views`), else <dir>/view/model-view.json; chain rows come from a step JSON (--json
// writes one), else from the last saved step. <dir> = the module's folder.
//   --save   on KEEP only: <dir>/steps/model-vNN.mjs (the next number; the refitted frame knobs written in) + <dir>/model.mjs
//            (+ the module itself when the frame moved) + one line in <dir>/steps/steps.jsonl
//   --revert restore the module (and <dir>/model.mjs) from the last saved step; nothing is judged
//   --pages  only those view.mjs critic pages (views and / or concept), into --out (default <dir>/steps/pages)
//   --json   write this step's full record (a baseline for the next round: views, checks, chain rows, blobs, probes)
// Exit 0 = KEEP, 1 = REVERT (or nothing to revert), 2 = the tool failed, 3 = usage.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import { checkModule } from "../check-module.mjs";
import { ROOT } from "../subject.mjs";
import { meshParts } from "../project.mjs";
import { BACKGROUND, frameOf } from "../registered.mjs";
import { knobNum } from "../knobs.mjs";
import { basisOf, loadTurnaround, rasterOrtho, viewMap } from "../v6/ortho.mjs";
import { judge } from "../v6/judge.mjs";
import { viewSheet } from "../v6/view.mjs";
import { runChain } from "./inspect.mjs";
import { conceptIoUFn, conceptTarget, fitFrame, parseArgs } from "./lib.mjs";
import { STEP, agreeOf, baselineOf, chainKey, frameMove, lineRuns, parseProbes, probeLine, stepVerdict, withFrameKnobs } from "./steplib.mjs";

const USAGE = "usage: node scripts/v7/step.mjs --subject <s> [--module <m.mjs>] [--baseline <json>] [--save [--note \"...\"]] [--revert] [--pages side,concept|all] [--json <file>] [--out <dir>] [--probes <file>]";
const args = parseArgs(process.argv.slice(2), ["save", "revert", "help"]);
const str = (v) => (v && v !== true ? String(v) : null);
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };
const readJson = (f) => JSON.parse(fs.readFileSync(f, "utf8"));
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const f4 = (x) => (Number.isFinite(x) ? x.toFixed(4) : "   -  ");
const s4 = (x) => (Number.isFinite(x) ? `${x >= 0 ? "+" : ""}${x.toFixed(4)}` : "   -   ");

/** The saved steps (<dir>/steps/steps.jsonl), oldest first. */
function savedSteps(dir) {
  const f = path.join(dir, "steps", "steps.jsonl");
  if (!fs.existsSync(f)) return [];
  return fs.readFileSync(f, "utf8").split(/\r?\n/).filter((l) => l.trim()).map((l) => JSON.parse(l));
}

/** The round baseline: {file, json, from} or null (see the header). */
function loadBaseline(dir) {
  const b = str(args.baseline);
  if (b === "none") return null;   // a fresh start (scaffold.mjs): nothing to compare against
  if (b) { const f = path.resolve(b); return { file: f, json: readJson(f), from: "--baseline" }; }
  const st = path.join(dir, "state.json");
  if (fs.existsSync(st)) {
    const sb = readJson(st).baseline;
    if (sb?.file) for (const f of [path.resolve(ROOT, sb.file), path.resolve(dir, sb.file)]) if (fs.existsSync(f)) return { file: f, json: readJson(f), from: "state.json" };
    if (sb?.views) return { file: st, json: { views: sb.views }, from: "state.json views" };
  }
  const mv = path.join(dir, "view", "model-view.json");
  return fs.existsSync(mv) ? { file: mv, json: readJson(mv), from: "latest view" } : null;
}

function revert(dir, modulePath) {
  const steps = savedSteps(dir);
  if (!steps.length) { console.log(`[step] nothing to revert: no saved step in ${rel(path.join(dir, "steps", "steps.jsonl"))}`); return 1; }
  const last = steps[steps.length - 1];
  const text = fs.readFileSync(path.resolve(dir, last.file), "utf8");
  const wrote = [];
  for (const t of new Set([modulePath, path.join(dir, "model.mjs")])) {
    if (fs.existsSync(t) && fs.readFileSync(t, "utf8") === text) continue;
    fs.writeFileSync(t, text);
    wrote.push(rel(t));
  }
  const agree = Object.entries(last.views ?? {}).map(([v, m]) => `${v} ${f4(agreeOf(m))}`).join(" · ");
  console.log(`[step] ${wrote.length ? `reverted ${wrote.join(" + ")}` : "unchanged (already"} to ${last.file}${wrote.length ? "" : ")"} — step v${last.n}${last.note ? ` "${last.note}"` : ""}${agree ? ` · agree ${agree}` : ""}`);
  return 0;
}

/** One printed blob-table line of a view: the top `n` blobs (miss = reference only, ~part = the nearest part; extra = model only). */
function blobsLine(v, list, n) {
  if (!list?.length) return `blobs ${v}: none`;
  const f2 = (x) => x.toFixed(2);
  const tok = (b) => {
    const where = Array.isArray(b.bbox) ? `x${b.bbox[0]}..${b.bbox[2]} y${b.bbox[1]}..${b.bbox[3]}` : `r${f2(b.bbox.right[0])}..${f2(b.bbox.right[1])} u${f2(b.bbox.up[0])}..${f2(b.bbox.up[1])}`;
    return `${b.kind === "missing" ? "miss" : "extra"} ${b.px}px ${b.kind === "missing" ? "~" : ""}${b.part ?? "-"} ${where}`;
  };
  return `blobs ${v}: ${list.slice(0, n).map(tok).join(" · ")}`;
}

async function main() {
  const t0 = Date.now();
  const subjectId = str(args.subject);
  if (args.help || !subjectId) { console.log(USAGE); return args.help ? 0 : 3; }
  if (args.save && args.revert) throw new Error("--save and --revert exclude each other");
  const modulePath = str(args.module) ? path.resolve(args.module) : path.join(ROOT, "out", "ref", "gold", subjectId, "model.mjs");
  const dir = path.dirname(modulePath);
  if (args.revert) return revert(dir, modulePath);
  const { reg } = await loadTurnaround(subjectId);
  const images = [...reg.names, "concept"];
  const pagesArg = str(args.pages);
  const pages = pagesArg ? (pagesArg === "all" ? images : pagesArg.split(",").map((s) => s.trim()).filter(Boolean)) : null;
  for (const p of pages ?? []) if (!images.includes(p)) throw new Error(`--pages ${p}: not one of ${images.join(", ")}`);

  const out = [];
  const say = (l) => out.push(`[step] ${l}`);
  const base = loadBaseline(dir);
  const B = baselineOf(base?.json);
  const steps = savedSteps(dir);
  let chainFrom = B?.chainRows ? "baseline" : null;
  if (B && !B.chainRows && steps.length && Array.isArray(steps[steps.length - 1].chain?.rows)) {
    B.chainRows = steps[steps.length - 1].chain.rows.map(chainKey);
    chainFrom = `saved step v${steps[steps.length - 1].n}`;
  }
  const baseNote = base ? `${rel(base.file)} (${base.from}${base.json.views && Object.values(base.json.views).some((m) => m.agree === undefined) ? "; no agree: its iou" : ""})` : "none";

  // 1. check-module: the one build (under the subject's gate config)
  const cm = await checkModule(modulePath, { label: rel(modulePath), subjectId });
  const header = () => `${subjectId} · ${rel(modulePath)} · baseline ${baseNote}`;
  if (!cm.pass) {
    const v = stepVerdict({ checkModule: { pass: false, line: cm.lines.slice(1).join(" ").trim() }, views: {}, floats: [], clips: [], chainRows: [], tris: 0, budget: null }, B);
    say(header());
    for (const l of cm.lines) say(`check-module ${l.trim()}`);
    say(v.line);
    for (const l of out) console.log(l);
    return 1;
  }
  // 2. the validator chain on that build
  let chain = null, chainError = null;
  try { chain = await runChain(modulePath, subjectId, { built: { meta: cm.meta, parts: cm.parts } }); } catch (e) { chainError = String(e.message ?? e).slice(0, 160); }
  // 3. the concept frame refit from the knob frame (no grid), rounded as the knobs store it
  const knobFrame = frameOf(cm.mod.KNOBS);
  const built = { meta: cm.meta, parts: cm.parts, frame: knobFrame };
  const { T } = await conceptTarget(subjectId);
  const fit = await fitFrame(conceptIoUFn(subjectId, T, built), knobFrame, { grid: false });
  const fr = { scale: r4(fit.frame.scale), tx: r4(fit.frame.tx), ty: r4(fit.frame.ty) };
  const move = frameMove(knobFrame, fr);
  // 4. the judge at the refitted frame (+ the blob table; + tiles for --pages)
  const judged = await judge({ subjectId, built: { ...built, frame: fr }, tiles: !!pages, blobs: true });
  const m = judged.metrics;
  // 5. probes (subjects/<s>/probes.json): reference vs model runs along named scan lines
  const probeFile = str(args.probes) ? path.resolve(args.probes) : path.join(ROOT, "subjects", subjectId, "probes.json");
  const probes = [];
  if (fs.existsSync(probeFile)) {
    const list = parseProbes(readJson(probeFile), images);
    let meshes = null;
    const rasters = new Map();
    for (const p of list) {
      let W, refAt, modAt;
      if (p.view === "concept") {
        W = judged.proj.w;
        refAt = (i) => T[i] !== BACKGROUND;   // the judged target (occluded counted as foreground, as measure.mjs profile)
        modAt = (i) => judged.proj.partId[i] >= 0;
      } else {
        const V = reg.views[p.view];
        W = V.img.w;
        if (!rasters.has(p.view)) {
          meshes ??= meshParts(cm.parts, 0).meshes;
          const M = viewMap(reg, p.view, V.img.w);
          rasters.set(p.view, rasterOrtho(meshes, basisOf(V.spec), { k: M.k * judged.sigma, bx: M.bx, by: M.by }, M.w, M.h).partId);
        }
        const pid = rasters.get(p.view);
        refAt = (i) => V.img.fam[i] !== 0;
        modAt = (i) => pid[i] >= 0;
      }
      const H = p.view === "concept" ? judged.proj.h : reg.views[p.view].img.h;
      const lim = p.axis === "row" ? W - 1 : H - 1;
      if (p.index > (p.axis === "row" ? H - 1 : W - 1)) throw new Error(`probe ${p.id}: index ${p.index} outside the ${W} x ${H} ${p.view} image`);
      const at = (i) => (p.axis === "row" ? p.index * W + i : i * W + p.index);
      const a = Math.min(p.from, lim), b = Math.min(p.to, lim);
      probes.push({ ...p, ref: lineRuns((i) => refAt(at(i)), a, b), model: lineRuns((i) => modAt(at(i)), a, b) });
    }
  }
  // 6. the verdict
  const floats = (m.checks?.groups ?? []).filter((g) => g.float).map((g) => ({ name: g.name, why: g.why }));
  const clips = m.checks?.clips ?? [];
  const chainRows = chain ? chain.violations.map((v) => ({ v: v.v, part: v.part ?? null })) : null;
  const tris = chain?.measurements?.tris ?? m.tris;
  const budget = chain?.measurements?.triBudget ?? null;
  const verdict = stepVerdict({ checkModule: { pass: true, line: cm.lines[0] }, views: m.views, floats, clips, chainRows, chainError, tris, budget }, B);

  // 7. the report (<= 40 lines)
  const secs = () => ((Date.now() - t0) / 1000).toFixed(1);
  say(header());   // the time is filled in last
  const headAt = out.length - 1;
  say(`check-module ${cm.lines[0].replace(`PASS ${rel(modulePath)} — `, "PASS — ")}`);
  if (chain) {
    const newRows = verdict.newRows;
    say(`chain pass ${chain.pass} · tris ${tris}/${budget} · ${chain.violations.length} violations (${chainFrom ? `${newRows.length} new vs ${chainFrom}` : `no baseline rows: ${newRows.length} count, class-config rows are notes`}) · ${(chain.advisories ?? []).length} advisories`);
    for (const r of newRows.slice(0, 3)) {
      const v = chain.violations.find((x) => x.v === r.v && (x.part ?? null) === r.part);
      say(`  NEW ${r.v} ${r.part ?? ""} ${String(v?.hint ?? "").slice(0, 150)}`);
    }
    if (newRows.length > 3) say(`  ... ${newRows.length - 3} more new rows (--json)`);
  } else say(`chain ERROR ${chainError}`);
  say(`checks ${m.checks?.pass ? "PASS" : "FAIL"} · float ${floats.map((g) => g.name).join(", ") || "none"} · clips ${clips.map((c) => `${c.a}x${c.b}`).join(", ") || "none"}${m.symmetry !== undefined ? ` · symmetry ${m.symmetry}` : ""} · sigma ${m.sigma}`);
  const fmtFr = (x) => `${knobNum(x.scale)},${knobNum(x.tx)},${knobNum(x.ty)}`;
  say(`frame knobs ${fmtFr(knobFrame)} -> fit ${fmtFr(fr)} (scale ${move.dScale >= 0 ? "+" : ""}${(move.dScale * 100).toFixed(2)} %, shift ${move.dx >= 0 ? "+" : ""}${move.dx.toFixed(1)} / ${move.dy >= 0 ? "+" : ""}${move.dy.toFixed(1)} px) · concept iou ${f4(fit.start.v)} at the knobs -> ${f4(m.views.concept.iou)}`);
  if (move.warn) say(move.warn);
  const bv = B?.views ?? {};
  say(`${"view".padEnd(8)} ${"iou".padStart(6)} ${"agree".padStart(6)} ${"drift".padStart(6)}  ${"base".padStart(6)} ${"d.agree".padStart(8)} ${"d.iou".padStart(8)}`);
  for (const v of images) {
    const c = m.views[v], b = bv[v];
    say(`${v.padEnd(8)} ${f4(c.iou)} ${f4(c.agree)} ${`${((c.drift ?? 0) * 100).toFixed(1)}%`.padStart(6)}  ${b ? f4(agreeOf(b)) : "   -  "} ${b ? s4(c.agree - agreeOf(b)).padStart(8) : "      - "} ${b ? s4(c.iou - b.iou).padStart(8) : "      - "}`);
  }
  for (const v of images) say(blobsLine(v, m.blobs?.[v], STEP.blobTop));
  const room = STEP.maxLines - out.length - 3 - Math.min(2, verdict.notes.length);   // 3 = pages, saved, verdict
  const cap = Math.max(0, Math.min(STEP.maxProbes, room));
  const shownProbes = probes.length > cap ? probes.slice(0, Math.max(0, cap - 1)) : probes;   // the "... more" line fits too
  for (const p of shownProbes) say(probeLine(p, p.ref, p.model));
  if (probes.length > shownProbes.length) say(`... ${probes.length - shownProbes.length} more probes (--json)`);
  for (const n of verdict.notes.slice(0, 2)) say(`note ${n}`);

  // 8. files (only on request)
  const record = {
    subject: subjectId, module: rel(modulePath), at: new Date().toISOString(), baseline: base ? rel(base.file) : null,
    note: str(args.note), views: m.views, minAgree: m.minAgree, minOrtho: m.minOrtho, minView: m.minView, score: m.score,
    sigma: m.sigma, symmetry: m.symmetry, tris, budget, checks: m.checks, placementRows: m.placementRows, blobs: m.blobs,
    chain: chain ? { pass: chain.pass, tris, budget, rows: chain.violations.map((v) => ({ v: v.v, part: v.part ?? null, hint: String(v.hint ?? "").slice(0, 200) })) } : { error: chainError },
    checkModule: { pass: true, line: cm.lines[0] },
    frame: { knobs: knobFrame, fit: fr, knobIoU: r4(fit.start.v), fitIoU: m.views.concept.iou },
    probes: probes.map((p) => ({ id: p.id, view: p.view, axis: p.axis, index: p.index, from: p.from, to: p.to, ref: p.ref, model: p.model })),
    verdict: { keep: verdict.keep, reasons: verdict.reasons, notes: verdict.notes },
  };
  if (pages) {
    const outDir = str(args.out) ? path.resolve(args.out) : path.join(dir, "steps", "pages");
    const r = await viewSheet({ subjectId, modulePath, outDir, zoom: 520, judged, pages });
    say(`pages ${r.zoomed.map(rel).join(" · ")}`);
  }
  const jsonFile = str(args.json);
  if (jsonFile) { fs.mkdirSync(path.dirname(path.resolve(jsonFile)), { recursive: true }); fs.writeFileSync(path.resolve(jsonFile), `${JSON.stringify(record, null, 2)}\n`); }
  if (args.save) {
    if (!verdict.keep) say("not saved (REVERT)");
    else {
      const stepsDir = path.join(dir, "steps");
      fs.mkdirSync(stepsDir, { recursive: true });
      const nums = [...fs.readdirSync(stepsDir), ...fs.readdirSync(dir)].map((f) => /^model-v(\d+)\.mjs$/.exec(f)?.[1]).filter(Boolean).map(Number);
      const n = (nums.length ? Math.max(...nums) : 0) + 1;
      const name = `model-v${String(n).padStart(2, "0")}.mjs`;
      let text = fs.readFileSync(modulePath, "utf8");
      const moved = knobNum(fr.scale) !== knobNum(knobFrame.scale) || knobNum(fr.tx) !== knobNum(knobFrame.tx) || knobNum(fr.ty) !== knobNum(knobFrame.ty);
      if (moved) text = withFrameKnobs(text, fr);
      fs.writeFileSync(path.join(stepsDir, name), text);
      const wrote = [`steps/${name}`];
      for (const t of new Set([path.join(dir, "model.mjs"), ...(moved ? [modulePath] : [])])) {
        if (fs.existsSync(t) && fs.readFileSync(t, "utf8") === text) continue;
        fs.writeFileSync(t, text);
        wrote.push(path.basename(t));
      }
      const line = { n, file: `steps/${name}`, sha1: createHash("sha1").update(text).digest("hex"), ...record, blobs: undefined, checks: { groups: m.checks?.groups, clips: m.checks?.clips, pass: m.checks?.pass }, placementRows: undefined };
      fs.appendFileSync(path.join(stepsDir, "steps.jsonl"), `${JSON.stringify(line)}\n`);
      say(`saved v${String(n).padStart(2, "0")}: ${wrote.join(" + ")}${moved ? " (fitted frame knobs written)" : ""} · steps.jsonl`);
    }
  }
  out[headAt] += ` · ${secs()} s`;
  say(verdict.line);
  for (const l of out.slice(0, STEP.maxLines - 1)) console.log(l);
  if (out.length > STEP.maxLines - 1) console.log(out[out.length - 1]);
  return verdict.keep ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((c) => { process.exitCode = c; }).catch((e) => { console.error(`[step] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 2; });
}
