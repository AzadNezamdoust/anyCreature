#!/usr/bin/env node
// WF v8 WP3 — the SETUP DOCTOR (research/v7/WF-V8-PLAN.md WP3; WF-REVIEW-opus.md C3 table + WF-REVIEW-fable.md C3 checks):
// everything about a subject's references and start that must be decided BEFORE round 1, as commands, not as a round of
// modeller effort. No model is judged; nothing under subjects/ or out/ref/gold/ is written except the report JSON.
//
//   node scripts/v7/doctor.mjs --subject <s> [--module <start.mjs>] [--json <file> | --no-json] [--no-tools]
//                              [--drift <proposal.json>] [--probes <proposal.json>]
// --drift / --probes check an auditor's PROPOSAL (research/v7/AUDITOR.md) instead of views.json drift / probes.json:
// a `drift` object (or a views.json holding one) and a probes list — before the owner approves and the orchestrator
// applies them.
//
// Rows (BLOCK / WARN / PASS; exit 1 on any BLOCK), rules in scripts/v7/steplib.mjs:
//   files        subject.json, camera.json, the concept, turnaround/views.json + views, start.mjs -> BLOCK (prior.json -> WARN)
//   check-module start.mjs (out/ref/gold/<s>/start.mjs or --module) -> BLOCK on FAIL
//   residual-*   registration W / L / H per view beyond +-3 % -> BLOCK naming the view; Wbbox / Lbbox beyond 5 % -> WARN
//   white        enclosed near-white per view + concept (not border-connected, darkest channel >= fgMax, each >= 0.1 % of
//                the foreground) with bboxes; families.enclosedFg unset and an image >= 0.5 % -> BLOCK
//   body-colour  a body-family colour whose darkest channel >= fgMax - 8 -> BLOCK (the background rule eats the body)
//   centring-*   the symmetric axis (vehicle x): body span centre vs fg bbox and mass centres > 0.03 m, no `shift` -> WARN
//   camera       camera.json provisional, residual_px >= 1.0, world-up tilt > 0.5 deg -> WARN
//   gate         the validator chain on start.mjs: class-config rows (PALETTE_ZONE / VEH_WHEELS) WARN until the subject's
//                WP2 overrides exist, any other row -> BLOCK
//   drift        views.json drift rects over 5 % of an image's reference foreground -> BLOCK (regenerate the view); a rect
//                without a distinct id, a `decides` naming another image, or a `why` -> WARN
//   audit        views.json `drift` with `audited`, subjects/<s>/probes.json with >= 6 valid probes -> WARN when missing
//                (an invalid probes.json -> BLOCK: step.mjs reads it)
//   views        view names outside side / front / rear / top -> WARN (the brief generator's names)
//   hull         WF v8 WP5: hull.mjs hullReport on the live turnaround + the concept — a view's viewOnly (its foreground the
//                other views carve away) / the concept's conceptOnlyBlob above scripts/v7/gold.config.json setupHull warn
//                -> WARN, above block -> BLOCK (goldlib.mjs hullRows); hull.mjs failing -> BLOCK
//   aspect       hull.mjs --aniso on the same hull: |aspect| H/W or L/W (the views' object's proportions over the concept's)
//                above gold.config.json setupHull.aspect warn -> WARN, above block -> BLOCK (hull.mjs aspectRows)
//   tools        every measure / inspect / frame / variants subcommand once on the subject + the v7 unit tests -> BLOCK
//
// --direct (WF v10 direct subjects, research/PRECISION-VEHICLE-VS-DIRECT.md step 4): no gold start / module / tools —
// files (+ subjects/<s>/parts.json), the hull row (views vs views, no concept), the camera row, and the HERO-SIZE row:
// the turnaround's visual hull projected through camera.json (hull.mjs frameRecord, plain bbox fit, nothing written)
// against the hero's foreground bbox: x / y px-per-metre ratio - 1 = how much wider (+) or narrower (-) the hero
// draws the object against its height than the turnaround does. |delta| > 3 % WARN, > 6 % BLOCK. BLOCK -> repair the
// turnaround (node scripts/v7/turnaround.mjs repair, its stop rule) or re-solve the camera, never a build. The
// camera is part of the number: a hand-set camera.json is named in the row. JSON: --json <file> (default none).
// Report: one line per row + the verdict line; JSON: out/ref/gold/<s>/doctor.json (--json <file> elsewhere, --no-json none).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

import { checkModule } from "../check-module.mjs";
import { ROOT, loadSubject } from "../subject.mjs";
import { OCCLUDED, SUBJECT, careMask, readRGB, targetState } from "../registered.mjs";
import { axisOf, driftOf, hasTurnaround, loadTurnaround, maskOptions, readJson, turnaroundDir, viewsFile } from "../v6/ortho.mjs";
import { runChain } from "./inspect.mjs";
import { conceptTarget, parseArgs } from "./lib.mjs";
import { subjectRegistration } from "../project.mjs";
import { aspectRows, frameRecord, hullReport, loadViewSet } from "./hull.mjs";
import { hullRows, loadConfig } from "./goldlib.mjs";
import {
  DOCTOR, bodyColourRows, cameraRows, centringRow, doctorVerdict, enclosedWhite, gateRows, parseProbes, residualRows, whiteRows,
} from "./steplib.mjs";

const USAGE = "usage: node scripts/v7/doctor.mjs --subject <s> [--direct] [--module <start.mjs>] [--json <file> | --no-json] [--no-tools] [--drift <proposal.json>] [--probes <proposal.json>]";
const args = parseArgs(process.argv.slice(2), ["no-json", "no-tools", "help", "direct"]);
const str = (v) => (v && v !== true ? String(v) : null);
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };
const VIEW_NAMES = ["side", "front", "rear", "top"];

/** Run one tool as a child process (cwd ROOT): {code, out, err, ms}. */
function run(argv, timeoutMs = 180000) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    const p = spawn(process.execPath, argv, { cwd: ROOT, windowsHide: true });
    let out = "", err = "";
    p.stdout.on("data", (d) => { if (out.length < 20000) out += d; });
    p.stderr.on("data", (d) => { if (err.length < 20000) err += d; });
    const timer = setTimeout(() => { p.kill(); err += `\ntimed out after ${timeoutMs / 1000} s`; }, timeoutMs);
    p.on("close", (code) => { clearTimeout(timer); resolve({ code, out, err, ms: Date.now() - t0 }); });
    p.on("error", (e) => { clearTimeout(timer); resolve({ code: -1, out, err: String(e), ms: Date.now() - t0 }); });
  });
}

/** Tool smoke: every measure / inspect / frame / variants subcommand once (module ones only with a start module). */
async function toolRows(s, module, spec, conceptSize, bodyName) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), `llmm-doctor-${s}-`));
  const v0 = Object.keys(spec.views)[0];
  const [cw, ch] = conceptSize;
  const M = module ? ["--module", module] : [];
  const cmds = [
    ["measure comps", ["scripts/v7/measure.mjs", "comps", "--subject", s, "--top", "1"], /^\S+\s+\S+\s+\d+ right /m],
    // a family filter that silently matches nothing (the 24104ad bug) prints only the header: the contract catches it
    ["measure comps --family", ["scripts/v7/measure.mjs", "comps", "--subject", s, "--family", bodyName, "--top", "1"], new RegExp(`^\\S+\\s+${bodyName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s+\\d+ right `, "m")],
    ["measure sample", ["scripts/v7/measure.mjs", "sample", "--subject", s, "--view", "concept", "10,10,4,4"], /family /],
    ["measure sample --view", ["scripts/v7/measure.mjs", "sample", "--subject", s, "--view", v0, "10,10,4,4"]],
    ["measure runs --family", ["scripts/v7/measure.mjs", "runs", "--subject", s, "--view", "concept", "row", String(ch >> 1), "0", String(cw - 1), "--family"]],
    ["measure profile", ["scripts/v7/measure.mjs", "profile", "--subject", s, "--view", v0, "--step", "0.5", ...M]],
    ["measure profile concept", ["scripts/v7/measure.mjs", "profile", "--subject", s, "--view", "concept", "--axis", "col", "--from", String(cw >> 1), "--to", String(cw >> 1), ...M]],
    ["measure grid", ["scripts/v7/measure.mjs", "grid", "--subject", s, "--view", v0, "0,0,64,64", "--scale", "1", "--out", path.join(tmp, "grid.png"), ...(module ? [...M, "--diff"] : [])]],
    ...(module ? [
      ["measure project", ["scripts/v7/measure.mjs", "project", "--subject", s, ...M, "0,1,0"]],
      ["measure unproject", ["scripts/v7/measure.mjs", "unproject", "--subject", s, ...M, `${cw >> 1},${ch >> 1},y,1`]],
      ["inspect parts", ["scripts/v7/inspect.mjs", "parts", ...M]],
      ["inspect contacts", ["scripts/v7/inspect.mjs", "contacts", ...M]],
      ["inspect chain", ["scripts/v7/inspect.mjs", "chain", ...M, "--subject", s], /^pass (true|false) tris /m],
      ["frame", ["scripts/v7/frame.mjs", "--subject", s, ...M, "--no-grid", "--stages", "0.02:8"], /^best /m],
      ["frame --sigma", ["scripts/v7/frame.mjs", "--subject", s, ...M, "--sigma", "1:1:0.01"]],
      ["variants", ["scripts/v7/variants.mjs", "--subject", s, ...M, "--no-fit", "--rule", "concept-first"], /^WINNER BASE$/m],
    ] : []),
    ["unit tests", ["--test", "scripts/v7/lib.test.mjs", "scripts/v7/steplib.test.mjs"]],
  ];
  const results = [];
  const queue = [...cmds];
  const worker = async () => {
    while (queue.length) {
      const [name, argv, expect] = queue.shift();
      const r = await run(argv);
      // exit 0 AND the output contract (a filter that silently matches nothing is a failure too)
      if (r.code === 0 && expect && !expect.test(r.out)) { r.code = "output"; r.err = `no line matching ${expect} in: ${r.out.trim().split(/\r?\n/).slice(0, 2).join(" / ").slice(0, 160)}`; }
      results.push({ name, ...r });
    }
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  try { fs.rmSync(tmp, { recursive: true, force: true }); } catch { /* the OS temp dir */ }
  const bad = results.filter((r) => r.code !== 0);
  const slow = Math.max(...results.map((r) => r.ms));
  if (!bad.length) return [{ level: "PASS", id: "tools", text: `${results.length} tool runs ok${module ? "" : " (no start module: the module commands skipped)"} (slowest ${(slow / 1000).toFixed(1)} s)` }];
  return [{ level: "BLOCK", id: "tools", data: bad.map((r) => ({ name: r.name, code: r.code, err: r.err.slice(0, 400) })),
    text: `tool smoke failed: ${bad.map((r) => `${r.name} (exit ${r.code}: ${(r.err.trim().split(/\r?\n/).find((l) => l.trim()) ?? r.out.trim().split(/\r?\n/).pop() ?? "").slice(0, 120)})`).join(" · ")}` }];
}

/** HERO-SIZE row: hull-through-camera bbox aspect vs the hero's bbox aspect (gate: warn / block fractions). */
export function heroSizeRow({ sx, sy, bbox, camera }, gate = { warn: 0.03, block: 0.06 }) {
  const d = sx / sy - 1;
  const level = Math.abs(d) > gate.block + 1e-9 ? "BLOCK" : Math.abs(d) > gate.warn + 1e-9 ? "WARN" : "PASS";
  const sg = `${d >= 0 ? "+" : ""}${(d * 100).toFixed(1)} %`;
  const how = /hull silhouette fit|solve/i.test(String(camera?.method ?? "")) ? "solved camera" : `camera ${camera?.method ? "set by hand" : "of unknown method"} (theta ${camera?.theta_deg}, phi ${camera?.phi_deg}): part of this number`;
  return { level, id: "hero-size", data: { delta: +d.toFixed(4), sxPxPerM: +sx.toFixed(2), syPxPerM: +sy.toFixed(2), heroBbox: bbox },
    text: `hero-size (turnaround hull through camera.json vs the hero bbox ${bbox.join(",")}): x / y px-per-m ${sx.toFixed(1)} / ${sy.toFixed(1)} -> the hero is ${sg} ${d >= 0 ? "wider" : "narrower"} against its height than the turnaround (warn > ${gate.warn * 100}, block > ${gate.block * 100} %; ${how})`
      + (level === "PASS" ? "" : " — repair the turnaround toward the hero (node scripts/v7/turnaround.mjs repair) or re-solve the camera; never build on it") };
}

async function directMain(t0, s) {
  const rows = [];
  const add = (r) => rows.push(...(Array.isArray(r) ? r : [r]));
  let S = null;
  try { S = loadSubject(s); } catch (e) { add({ level: "BLOCK", id: "files", text: e.message }); }
  let camera = null;
  if (S) {
    const missing = [];
    for (const f of [S.paths.target, S.paths.camera, viewsFile(s)]) if (!f || !fs.existsSync(f)) missing.push(f ? rel(f) : "(a subject.json path)");
    if (hasTurnaround(s)) for (const v of Object.values(readJson(viewsFile(s)).views ?? {})) { const f = path.join(turnaroundDir(s), v.file); if (!fs.existsSync(f)) missing.push(rel(f)); }
    add(missing.length ? { level: "BLOCK", id: "files", text: `missing: ${missing.join(", ")}` } : { level: "PASS", id: "files", text: "subject.json, camera, hero, views.json + views" });
    const pj = path.join(ROOT, "subjects", s, "parts.json");
    add(fs.existsSync(pj) ? { level: "PASS", id: "parts", text: `subjects/${s}/parts.json ${(readJson(pj).parts ?? []).length} parts (the HERO gate's table)` }
      : { level: "WARN", id: "parts", text: `no subjects/${s}/parts.json: measure the hero's part table before the build (BUILD-DIRECT.md "Measured part list")` });
    if (!missing.length) {
      camera = readJson(S.paths.camera);
      try {
        const set = await loadViewSet(s);
        const { report } = await hullReport({ reg: set.reg });
        add(hullRows(report, loadConfig().setupHull));
      } catch (e) { add({ level: "BLOCK", id: "hull", text: `hull.mjs failed: ${String(e.message ?? e).slice(0, 200)}` }); }
      try {
        const { record, fit } = await frameRecord(s, { from: "hull", frameRefine: "off" });
        add(heroSizeRow({ sx: fit.sx, sy: fit.sy, bbox: record._frame.conceptBboxPx, camera }, loadConfig().setupHull.aspect));
      } catch (e) { add({ level: "BLOCK", id: "hero-size", text: `hero-size failed: ${String(e.message ?? e).slice(0, 200)}` }); }
      add(cameraRows(camera));
    }
  }
  const verdict = doctorVerdict(rows);
  const order = { BLOCK: 0, WARN: 1, PASS: 2 };
  const idw = Math.max(...rows.map((r) => r.id.length));
  console.log(`[doctor] ${s} · --direct`);
  for (const r of [...rows].sort((a, b) => order[a.level] - order[b.level])) console.log(`[doctor] ${r.level.padEnd(5)} ${r.id.padEnd(idw)} ${r.text}`);
  const jsonFile = str(args.json) ? path.resolve(args.json) : null;
  if (jsonFile) {
    fs.mkdirSync(path.dirname(jsonFile), { recursive: true });
    fs.writeFileSync(jsonFile, `${JSON.stringify({ subject: s, mode: "direct", at: new Date().toISOString(), verdict: verdict.level, blocks: verdict.blocks, warns: verdict.warns, rows }, null, 2)}
`);
  }
  console.log(`[doctor] ${verdict.level} ${s} (--direct): ${verdict.blocks} BLOCK, ${verdict.warns} WARN${jsonFile ? ` · ${rel(jsonFile)}` : ""} · ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  return verdict.level === "BLOCK" ? 1 : 0;
}

async function main() {
  const t0 = Date.now();
  const s = str(args.subject);
  if (args.help || !s) { console.log(USAGE); return args.help ? 0 : 3; }
  if (args.direct) return directMain(t0, s);
  const rows = [];
  const add = (r) => rows.push(...(Array.isArray(r) ? r : [r]));
  const module = str(args.module) ? path.resolve(args.module) : path.join(ROOT, "out", "ref", "gold", s, "start.mjs");

  // files
  let S = null;
  try { S = loadSubject(s); } catch (e) { add({ level: "BLOCK", id: "files", text: e.message }); }
  const missing = [];
  if (S) {
    for (const f of [S.paths.target, S.paths.camera, viewsFile(s), module]) if (!f || !fs.existsSync(f)) missing.push(f ? rel(f) : "(a subject.json path)");
    if (!fs.existsSync(path.join(ROOT, "subjects", s, "prior.json"))) add({ level: "WARN", id: "prior", text: `no subjects/${s}/prior.json (the prior card: real dims, anchor, stylisation; scaffold.mjs reads its wheel ratio)` });
    if (hasTurnaround(s)) for (const v of Object.values(readJson(viewsFile(s)).views ?? {})) { const f = path.join(turnaroundDir(s), v.file); if (!fs.existsSync(f)) missing.push(rel(f)); }
    add(missing.length ? { level: "BLOCK", id: "files", text: `missing: ${missing.join(", ")}` } : { level: "PASS", id: "files", text: `subject.json, camera, concept, views.json + ${Object.keys(readJson(viewsFile(s)).views).length} views, ${rel(module)}` });
  }
  const hasModule = fs.existsSync(module);
  const canTurn = S && hasTurnaround(s) && !missing.some((m) => m.includes("/turnaround/") || m === rel(S.paths.target));

  // check-module + the gate on start.mjs
  if (S && hasModule) {
    const cm = await checkModule(module, { label: rel(module), subjectId: s });
    add({ level: cm.pass ? "PASS" : "BLOCK", id: "check-module", text: cm.lines.map((l) => l.trim()).join(" ") });
    if (cm.pass) {
      let chain;
      try {
        const r = await runChain(module, s, { built: { meta: cm.meta, parts: cm.parts } });
        chain = { pass: r.pass, violations: r.violations, tris: r.measurements.tris, budget: r.measurements.triBudget };
      } catch (e) { chain = { error: String(e.message ?? e).slice(0, 200) }; }
      add(gateRows(chain));
    }
  }

  let conceptSize = [1024, 1024];
  if (canTurn) {
    const { spec, reg, table } = await loadTurnaround(s);
    // registration residuals
    add(residualRows(reg.residuals));
    // enclosed near-white per image
    const white = [];
    for (const v of reg.names) {
      const { img } = reg.views[v];
      white.push({ image: v, ...enclosedWhite(img.data, img.w, img.h, img.c, table.fgMax, { holes: table.holes?.[v] ?? null }) });
    }
    const cimg = await readRGB(S.paths.target);
    conceptSize = [cimg.w, cimg.h];
    white.push({ image: "concept", ...enclosedWhite(cimg.data, cimg.w, cimg.h, cimg.c, table.fgMax, { holes: table.holes?.concept ?? null }) });
    add(whiteRows(white, spec.families?.enclosedFg));
    // body colours vs the background rule
    add(bodyColourRows(table.rgb[table.body], table.fgMax));
    // symmetric-axis centring (vehicle author frame: x is the mirror axis)
    if (S.klass === "vehicle") {
      for (const v of reg.names) {
        const V = reg.views[v];
        const [ra] = axisOf(V.spec.right), [ua] = axisOf(V.spec.up);
        const along = ra === 0 ? "right" : ua === 0 ? "up" : null;
        if (!along) continue;
        const { img } = V;
        let sum = 0, n = 0;
        for (let y = 0; y < img.h; y += 1) for (let x = 0; x < img.w; x += 1) if (img.fam[y * img.w + x] !== 0) { sum += along === "right" ? x + 0.5 : y + 0.5; n += 1; }
        const span = along === "right" ? V.body.x : V.body.y;
        const bc = (span[0] + span[1]) / 2;
        const boxC = along === "right" ? (V.box.x0 + V.box.x1) / 2 : (V.box.y0 + V.box.y1) / 2;
        const k = along === "right" ? reg.s * (V.kr ?? 1) : -reg.s * (V.ku ?? 1);   // px per metre along +right / +up (image y runs down)
        add(centringRow({ view: v, axis: along, dBox: (boxC - bc) / k, dMass: (sum / n - bc) / k, shift: V.spec.shift?.[along] ?? null }));
      }
    }
    // drift rects (views.json, or an auditor's proposal --drift <file>): valid, each with decides / why, <= 5 % per image
    const images = [...reg.names, "concept"];
    const proposal = str(args.drift) ? readJson(path.resolve(args.drift)) : null;
    const driftSpec = proposal ? (proposal.views && proposal.drift ? proposal.drift : proposal) : spec.drift;
    const src = proposal ? `the proposal ${rel(path.resolve(args.drift))}` : "views.json";
    let drift = null;
    try { drift = driftOf({ views: spec.views, drift: driftSpec }); } catch (e) { add({ level: "BLOCK", id: "drift", text: `${src}: ${e.message}` }); }
    if (drift) {
      const shares = [], over = [], loose = [];
      const ids = new Set();
      for (const [img, list] of Object.entries(drift)) {
        for (const d of list) {
          if (!images.includes(d.decides) || d.decides === img || !String(d.why ?? "").trim() || ids.has(d.id)) loose.push(d.id);
          ids.add(d.id);
        }
        let share;
        if (img === "concept") {
          const T0 = targetState(S, cimg, table.fgMax, maskOptions(table, "concept"));
          const TA = targetState(S, cimg, table.fgMax, { ...maskOptions(table, "concept"), dontCare: list.map((d) => d.rect) });
          let subj = 0, masked = 0;
          for (let i = 0; i < T0.length; i += 1) if (T0[i] === SUBJECT) { subj += 1; if (TA[i] === OCCLUDED) masked += 1; }
          share = subj ? masked / subj : 0;
        } else {
          const { img: im } = reg.views[img];
          const care = careMask(list.map((d) => d.rect), im.w, im.h);
          let fg = 0, masked = 0;
          for (let i = 0; i < im.fam.length; i += 1) if (im.fam[i] !== 0) { fg += 1; if (care && !care[i]) masked += 1; }
          share = fg ? masked / fg : 0;
        }
        shares.push(`${img} ${(share * 100).toFixed(1)} % (${list.length})`);
        if (share > DOCTOR.driftMax) over.push(`${img} ${(share * 100).toFixed(1)} %`);
      }
      if (over.length) add({ level: "BLOCK", id: "drift", text: `${src}: drift rects over ${DOCTOR.driftMax * 100} % of the reference foreground: ${over.join(", ")} — regenerate the view (a whole-view disagreement is a setup ruling, not drift) · all: ${shares.join(" · ")}` });
      if (loose.length) add({ level: "WARN", id: "drift-entries", text: `${src}: rects ${loose.join(", ")} lack a distinct id, a \`decides\` (another image: ${images.join(" / ")}) or a \`why\`` });
      if (!over.length) add({ level: "PASS", id: "drift", text: `${src}: ${shares.length ? shares.join(" · ") : "no rects"}` });
    }
    // audit present
    const audited = driftSpec && typeof driftSpec === "object" && typeof driftSpec.audited === "string" && driftSpec.audited.trim();
    const nRects = drift ? Object.values(drift).reduce((a, l) => a + l.length, 0) : 0;
    add(audited ? { level: "PASS", id: "audit", text: `${src} drift audited "${driftSpec.audited}" (${nRects} rects)` }
      : { level: "WARN", id: "audit", text: `no audit: ${src} has no \`drift\` with \`audited\` (research/v7/AUDITOR.md; empty rect lists are fine)` });
    const pf = str(args.probes) ? path.resolve(args.probes) : path.join(ROOT, "subjects", s, "probes.json");
    if (!fs.existsSync(pf)) add({ level: "WARN", id: "probes", text: `no ${rel(pf)} (${DOCTOR.probesMin}-${DOCTOR.probesMax} scan lines through landmarks; research/v7/AUDITOR.md)` });
    else {
      try {
        const list = parseProbes(readJson(pf), [...reg.names, "concept"]);
        const ok = list.length >= DOCTOR.probesMin && list.length <= DOCTOR.probesMax;
        add({ level: ok ? "PASS" : "WARN", id: "probes", text: `${rel(pf)} ${list.length} probes${ok ? "" : ` (want ${DOCTOR.probesMin}-${DOCTOR.probesMax})`}` });
      } catch (e) { add({ level: "BLOCK", id: "probes", text: `${rel(pf)} invalid: ${e.message}` }); }
    }
    const odd = reg.names.filter((v) => !VIEW_NAMES.includes(v));
    add(odd.length ? { level: "WARN", id: "views", text: `view names ${odd.join(", ")} are not side / front / rear / top` } : { level: "PASS", id: "views", text: `views ${reg.names.join(", ")}` });
    // WF v8 WP5: the visual hull — do the views describe one object, and the concept's? (thresholds: gold.config.json)
    try {
      const { T } = await conceptTarget(s);
      const { report } = await hullReport({ reg, concept: { T, creg: subjectRegistration(s), w: cimg.w, h: cimg.h }, aniso: true });
      const gate = loadConfig().setupHull;
      add(hullRows(report, gate));
      add(aspectRows(report, gate.aspect));
    } catch (e) {
      add({ level: "BLOCK", id: "hull", text: `hull.mjs failed: ${String(e.message ?? e).slice(0, 200)}` });
    }
  }
  // the concept camera
  if (S?.paths.camera && fs.existsSync(S.paths.camera)) add(cameraRows(readJson(S.paths.camera)));

  // tool smoke
  if (!args["no-tools"] && S && canTurn) {
    const { table } = await loadTurnaround(s);
    add(await toolRows(s, hasModule ? rel(module) : null, readJson(viewsFile(s)), conceptSize, table.names[table.body]));
  }

  const verdict = doctorVerdict(rows);
  const order = { BLOCK: 0, WARN: 1, PASS: 2 };
  const shown = [...rows].sort((a, b) => order[a.level] - order[b.level]);
  const idw = Math.max(...rows.map((r) => r.id.length));
  console.log(`[doctor] ${s} · start ${rel(module)}`);
  for (const r of shown) console.log(`[doctor] ${r.level.padEnd(5)} ${r.id.padEnd(idw)} ${r.text}`);
  const jsonFile = args["no-json"] ? null : str(args.json) ? path.resolve(args.json) : path.join(ROOT, "out", "ref", "gold", s, "doctor.json");
  if (jsonFile) {
    fs.mkdirSync(path.dirname(jsonFile), { recursive: true });
    fs.writeFileSync(jsonFile, `${JSON.stringify({ subject: s, at: new Date().toISOString(), module: rel(module), verdict: verdict.level, blocks: verdict.blocks, warns: verdict.warns, rows }, null, 2)}\n`);
  }
  console.log(`[doctor] ${verdict.level} ${s}: ${verdict.blocks} BLOCK, ${verdict.warns} WARN${jsonFile ? ` · ${rel(jsonFile)}` : ""} · ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  return verdict.level === "BLOCK" ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((c) => { process.exitCode = c; }).catch((e) => { console.error(`[doctor] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 2; });
}
