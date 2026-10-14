#!/usr/bin/env node
// WORKFLOW v4 — V4-3 LOOP (research/WF-V4-PLAN.md S3 BUILD + S4 LOOP). Replaces the P0–P3 pass split for vehicles.
//
//   node scripts/loop.mjs --subject pickup --seat <seat> [--from <start module>] [--K 4] [--no-images] [--evals 300]
//                         [--out <dir>] [--work <dir>]
//
// MEASURE is assumed done (layout / census / regions / camera exist). The live subject module is never read or
// written: the loop works on a copy in <work> (default out/ref/loop-<subject>/, under out/ref/ so the app's
// `?module=` can render it).
//
//   START  the class template (template-vehicle generateForSubject) or --from
//   FIT    scripts/fit.mjs over the module's KNOBS (no seat); a module without KNOBS is not fitted
//   V5-4: then the PER-FEATURE FIT (fit.mjs fitFeatures: each non-exact inventory item's own knobs, scored in its ROI at
//          full resolution, whole IoU held) and the PALETTE stage (calibrate-palette.mjs calibrateFaces: exact colour per
//          zone per face, sampled in the registered frame) — after the START FIT and after the BUILD re-FIT, i.e. before
//          every seat call that follows a FIT. On by default with the exact stop (featureFit / facePalette options).
//   BUILD  one seat call: the READY CALLS of every inventory feature the module lacks, their numbers rewritten as
//          `KNOBS.<name>.v` (ruling R1); the harness adds those knob entries (ranges v +/- the class prior _readyCall, V5-9)
//          to the KNOBS block, then re-FITs details + body
//   LOOP   k <= K seat calls: scoreboard + top-8 residual rows (ruling R2: px >= 300 or metres >= 0.045, ranked by
//          px x weight) each with its knobs + ranges and cited module lines +/- 2, READY CALLS for still-missing
//          features, the line-edit contract; <= 6 kB (asserted, V4-6). Images: the registered compare sheet, sent only
//          when the best module changed since the last one sent, or none with --no-images.
// V4-6: replies may copy the prompt's numbered display (`N| code` replaces line N, seat-io applyLineEdits); a reply
// that builds duplicate part ids is rejected before the gate; unknown zones (a colour FAMILY name, a region name) are
// renamed to their unique palette key before the load check; before each LOOP prompt the harness re-FITs the knobs
// the shown rows name (ABSORB) and only rows still open go to the seat, each with ONE structural edit.
// Guard: a candidate is accepted only if strictly better, lexicographic — loads; gate (blocking rows, no new code);
// coverage; min per-zone IoU; whole IoU >= best + 0.001 — with tris inside the budget; else the module reverts to
// best and the next prompt says what got worse. Stops: target (gate PASS, coverage 100 %, IoU >= band, no MISSING row,
// V4-5A: every zone at or over its class band classes/<c>.json zoneIouMin) / K / 2 consecutive rejects / 2 accepted
// gains < 0.003 / 12 min. A zone under its band is a ZONE residual row (shown first) with the class zoneProposals.
// Writes <out>/<step>/ (module.mjs, residuals.json, verdict.json, prompt.md, reply.md, sheet.png) for step = start,
// build, 1..K, plus <out>/loop.json and <out>/best.mjs. Exit 0 target reached, 1 stopped short, 2 seat transport /
// dev server down, 3 usage.
// V6-2: a subject with subjects/<s>/turnaround/views.json runs the v6 MULTI-VIEW path instead (scripts/v6/loop6.mjs:
// START template + prior soft ranges -> multi-view FIT -> BUILD -> re-FIT -> LOOP with view-tagged rows, the 6-view judge
// sheet as each step's sheet.png, no dev server); `--v5-detail on` adds the V5 single-view per-feature FIT, per-face
// palette and exactness stop inside it (default off). Subjects without a turnaround keep the path below unchanged.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import { ROOT, loadSubject } from "./subject.mjs";
import { loadModule, project, subjectRegistration } from "./project.mjs";
import { residuals, familyZoneKeys } from "./residuals.mjs";
import { addFrameKnobs } from "./registered.mjs";
import { accuracy, topFailing } from "./accuracy.mjs";
import { fit, fitFeatures, FIT_EVALS, gateLayout, yieldTask } from "./fit.mjs";
import { calibrateFaces } from "./calibrate-palette.mjs";
import { hasTurnaround } from "./v6/ortho.mjs";
import { knobNum } from "./knobs.mjs";
import { parseReply } from "./missing-keys.mjs";
import {
  NUMBERED_CONTRACT, SeatTransportError, applyLineEdits, autoFixPaletteZones, loadSeat, moduleFrame, moduleSyntaxError,
  seatOutcome, syntaxFollowUpPrompt,
} from "./seat-io.mjs";

export const PROMPT_MAX = 6144;   // V4-6 item 4 (was 8192)
/** V4-6 item 3: the per-step ABSORB re-FIT (knobs the shown rows name, zone-weighted). */
export const ABSORB_EVALS = 60;
export const ABSORB_ZONE_W = 2;
/** Ruling R2: rows a seat sees. */
export const SHOW = Object.freeze({ rows: 8, px: 300, metres: 0.045 });
/** MVP-STUB: rank weight per residual kind (a missing feature is structure, the seat's job). */
export const KIND_WEIGHT = Object.freeze({ MISSING: 2, ZONE: 1 });
export const IOU_GAIN = 0.001;
export const PLATEAU_GAIN = 0.003;
/** MVP-STUB: per-zone IoU is read at 3 decimals and flickers +/- 0.001 on AA; "not lower" allows this much. */
export const ZONE_EPS = 0.002;
export const TIME_MS = 12 * 60 * 1000;
/** V5-1 bug (a): the wall clock is enforced INSIDE every stage (FIT, re-FIT, ABSORB, knob attribution, seat calls). */
const timeLimitMs = () => Number(process.env.LLMM_LOOP_TIME_MS || TIME_MS);
export const IOU_BAND = 0.97;   // target stop (plan: class band 0.97 whole); the weak-seat PASS criterion (0.96) lives in the test protocol
const SEAT_TIMEOUT_MS = Number(process.env.LLMM_CODEX_TIMEOUT_MS || 15 * 60 * 1000);
const DEV_SERVER = "http://127.0.0.1:4210/";
const KERNEL = path.join(ROOT, "src", "kernel", "index.mjs");

const r4 = (v) => Math.round(v * 1e4) / 1e4;
const relPath = (file) => path.relative(ROOT, file).replace(/\\/g, "/");
const bytes = (s) => Buffer.byteLength(s, "utf8");
const sha = (s) => createHash("sha1").update(s).digest("hex").slice(0, 12);

// ---------------------------------------------------------------------------
// Module text helpers
// ---------------------------------------------------------------------------

/** Write `text` at `file` with its kernel import pointing at THIS kernel from there (copies load anywhere). */
export function placeModule(text, file) {
  let spec = path.relative(path.dirname(file), KERNEL).replace(/\\/g, "/");
  if (!spec.startsWith(".")) spec = `./${spec}`;
  const out = String(text).replace(/(["'])(?:\.{1,2}\/)+(?:[\w.-]+\/)*src\/kernel\/index\.mjs\1/g, `$1${spec}$1`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, out.endsWith("\n") ? out : `${out}\n`);
  return fs.readFileSync(file, "utf8");
}

/** [start, end) of the KNOBS block (end = index of the closing "\n};"), or null. */
function knobBlock(text) {
  const start = text.indexOf("export const KNOBS = {");
  if (start < 0) return null;
  const end = text.indexOf("\n};", start);
  return end < 0 ? null : { start, end };
}

/** {name: v} of the module's KNOBS block as written. */
function knobValues(text) {
  const b = knobBlock(text);
  if (!b) return {};
  return Object.fromEntries([...text.slice(b.start, b.end).matchAll(/\n\s*(\w+):\s*\{\s*v:\s*(-?[\d.]+(?:e-?\d+)?)/g)].map((m) => [m[1], Number(m[2])]));
}

/** Knob names defined in the module's KNOBS block. */
export function definedKnobs(text) {
  const b = knobBlock(text);
  if (!b) return new Set();
  return new Set([...text.slice(b.start, b.end).matchAll(/\n\s*(\w+):\s*\{\s*v:/g)].map((m) => m[1]));
}

/**
 * Ruling R1 — every `KNOBS.<name>.v` the text references that the block lacks and `table` offers gets its entry
 * (a module without a KNOBS block gets one before `export const meta`).
 * @returns {{text:string, added:string[], unknown:string[]}}
 */
export function addKnobEntries(text, table) {
  const have = definedKnobs(text);
  const refs = [...new Set([...String(text).matchAll(/\bKNOBS\.(\w+)\.v\b/g)].map((m) => m[1]))];
  const add = refs.filter((n) => !have.has(n) && table[n]);
  const unknown = refs.filter((n) => !have.has(n) && !table[n]);
  if (!add.length) return { text, added: [], unknown };
  const lines = add.map((n) => {
    const k = table[n];
    return `  ${n}: { v: ${knobNum(k.v)}, min: ${knobNum(k.min)}, max: ${knobNum(k.max)}, unit: "m" },   // READY CALL ${k.what}`;
  });
  let out = text;
  const b = knobBlock(out);
  if (b) out = `${out.slice(0, b.end)}\n${lines.join("\n")}${out.slice(b.end)}`;
  else {
    const at = out.indexOf("export const meta");
    const block = `export const KNOBS = {\n${lines.join("\n")}\n};\n\n`;
    out = at >= 0 ? out.slice(0, at) + block + out.slice(at) : block + out;
  }
  return { text: out, added: add, unknown };
}

const LITERAL = /(?<![\w.])(-?)(\d+\.\d+)(?![\w.])/g;
const HELPER_ROLE = { lamp: "headlight", grille: "grille", mirror: "mirror", pane: "window" };

/** Is the feature a READY call builds already in the parts? (idPrefix match, else the helper's role) */
export function featurePresent(call, parts) {
  const prefix = /idPrefix:\s*["'`]([A-Za-z]+)/.exec(call)?.[1];
  if (prefix && parts.some((p) => String(p.id).startsWith(prefix))) return true;
  const role = HELPER_ROLE[/K\.assemble\.(\w+)/.exec(call)?.[1]];
  if (role && parts.some((p) => p.role === role)) return true;
  return !prefix && !role;   // a call we cannot attribute is never offered as missing
}

/**
 * Ruling R1 — rewrite a READY call's metre literals as `KNOBS.<name>.v` (one knob per distinct |value| across all
 * calls, so a mirrored pair and a shared edge stay one knob). `offered` = {name: {v, min, max, what}} accumulated over
 * the run (names never collide with the module's own knobs).
 */
export function knobifyCalls(calls, { existing = new Set(), offered = {}, span, floor = -Infinity }) {
  const byValue = new Map(Object.entries(offered).map(([n, k]) => [knobNum(k.v), n]));
  const used = new Set([...existing, ...Object.keys(offered)]);
  const out = [];
  for (const c of calls) {
    const slug = (String(c.what).match(/[a-z]+/i)?.[0] ?? "feature").toLowerCase();
    const names = [];
    const call = c.call.replace(LITERAL, (m, sign, num) => {
      const v = Number(num);
      if (!(v >= 0.001)) return m;
      const key = knobNum(v);
      let name = byValue.get(key);
      if (!name) {
        let i = 1;
        while (used.has(`rc_${slug}${i}`)) i += 1;
        name = `rc_${slug}${i}`;
        used.add(name);
        byValue.set(key, name);
        offered[name] = { v: r4(v), min: r4(Math.max(floor, v - span)), max: r4(v + span), what: c.what };
      }
      names.push(name);
      return `${sign}KNOBS.${name}.v`;
    });
    out.push({ ...c, call, knobs: [...new Set(names)] });
  }
  return out;
}

/**
 * V5-9 evidence hierarchy: the +/- range of a READY-call rc_* knob is the class prior knobPriors._readyCall ({span, of:
 * "L" = the registration anchor length | "m"}, plausibility), not a layout tolerance; a class without one keeps the
 * V4 span 0.02 x the anchor.
 */
export function readyCallSpan(cls, reg) {
  const p = cls?.knobPriors?._readyCall;
  if (!p || !Number.isFinite(p.span)) return 0.02 * reg.anchor.ref;
  return p.span * (p.of === "m" || !p.of ? 1 : (reg.anchor[p.of] ?? reg.anchor.ref));
}

/** Apply a seat reply: `replace A-B` fences, else a complete module, else an insert block before `return parts;`. */
export function applyReply(text, answer) {
  const e = applyLineEdits(text, answer);
  if (e.error) return { text: null, why: e.error };
  if (e.text !== null) return { text: e.text, how: `${e.edits} line edit(s)${e.numbered ? ` (${e.numbered} numbered N|)` : ""}` };
  const art = parseReply(answer).artifact;
  if (!art || !art.trim()) return { text: null, why: "the reply had no ```js fence (no edit applied)" };
  if (/export\s+function\s+build\b/.test(art)) return { text: art, how: "complete module" };
  const lines = text.split(/\r?\n/);
  let at = -1;
  for (let i = lines.length - 1; i >= 0; i -= 1) if (/^\s*return parts;/.test(lines[i])) { at = i; break; }
  if (at < 0) return { text: null, why: "insert block, but the module has no `return parts;` line" };
  const indent = /^\s*/.exec(lines[at])[0];
  const block = art.replace(/\s+$/, "").split(/\r?\n/).map((l) => (l.trim() ? indent + l.replace(/^\s+/, "") : l));
  lines.splice(at, 0, ...block);
  return { text: lines.join("\n"), how: `insert block (${block.length} lines before \`return parts;\`)` };
}

/** V4-6 item 1: the part ids the module at `file` builds more than once (a helper call that now runs twice); null = no build. */
export async function duplicateIds(file) {
  try {
    const ids = (await loadModule(file)).build().map((p) => p.id);
    const seen = new Set();
    const dup = new Set();
    for (const id of ids) (seen.has(id) ? dup : seen).add(id);
    return [...dup];
  } catch {
    return null;
  }
}

/**
 * V4-6 item 2 — palette auto-fix BEFORE the load check (check-module rejects an unknown zone before the gate's
 * PALETTE_ZONE auto-fix could run). Every part zone that is not a meta.palette key gets its unique suggestion: a
 * colour FAMILY name ("dark") -> the family's palette key, disambiguated by the zone the same part ids (else the same
 * roles) had in `base`; a target region name -> its key; a case variant -> the key. Unresolvable names are left for
 * check-module to reject.
 * @returns {Promise<{text:string, fixes:Array<{from:string,to:string,why:string,parts:number}>}>}
 */
export async function fixZones(S, text, file, base = null) {
  placeModule(text, file);
  let mod;
  let parts;
  try { mod = await loadModule(file); parts = mod.build(); } catch { return { text, fixes: [] }; }
  const keys = Object.keys(mod.meta?.palette ?? {});
  const bad = new Map();
  for (const p of parts) if (typeof p.zone === "string" && !keys.includes(p.zone)) { if (!bad.has(p.zone)) bad.set(p.zone, []); bad.get(p.zone).push(p); }
  if (!bad.size) return { text, fixes: [] };
  const famKeys = familyZoneKeys(S);
  const baseParts = base?.parts ?? [];
  const fixes = [];
  let out = text;
  for (const [z, ps] of bad) {
    let cands;
    let why;
    if (famKeys[z]) { cands = famKeys[z].filter((k) => keys.includes(k)); why = `"${z}" is a colour family, not a zone`; }
    else {
      const byCase = keys.filter((k) => k.toLowerCase() === z.toLowerCase());
      const byRegion = (S.cls.paletteZones ?? []).filter((p) => p.region === z && keys.includes(p.key)).map((p) => p.key);
      cands = byCase.length ? byCase : byRegion;
      why = byCase.length ? `"${z}" differs from a key only in case` : `"${z}" is a target region`;
    }
    if (!cands.length) continue;
    let to = cands.length === 1 ? cands[0] : null;
    if (!to) {
      // MVP-STUB: one mapping per unknown name (not per part): the zone those part ids had in base, else their roles'
      const prev = [...new Set(ps.map((p) => baseParts.find((q) => q.id === p.id)?.zone).filter((k) => cands.includes(k)))];
      const byRole = [...new Set(baseParts.filter((q) => ps.some((p) => p.role && p.role === q.role)).map((q) => q.zone).filter((k) => cands.includes(k)))];
      to = prev.length === 1 ? prev[0] : byRole.length === 1 ? byRole[0] : null;
    }
    if (!to) continue;
    const esc = z.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const before = out;
    out = out.replace(new RegExp(`(\\b(?!id\\b|idPrefix\\b|role\\b|face\\b|host\\b)\\w+\\s*:\\s*)(["'])${esc}\\2`, "g"), `$1$2${to}$2`);
    if (out !== before) fixes.push({ from: z, to, why, parts: ps.length });
  }
  return { text: out, fixes };
}

// ---------------------------------------------------------------------------
// Measure one module
// ---------------------------------------------------------------------------

export async function calibrate(ctx, file) {
  if (!ctx.S.paths.regions || !fs.existsSync(ctx.S.paths.regions)) return;
  spawnSync(process.execPath, [path.join(ROOT, "scripts", "calibrate-palette.mjs"), "--subject", ctx.subjectId, "--module", file], { cwd: ROOT, encoding: "utf8" });
  // V5-4 item 3: the PALETTE stage — exact colour per zone per face, sampled in the registered frame
  if (ctx.facePalette) { try { await calibrateFaces({ subjectId: ctx.subjectId, modulePath: file }); } catch { /* keep the regions medians */ } }
}

function coverageOf(ctx, parts) {
  const keys = Object.keys(ctx.census).filter((k) => ctx.S.cls.censusRules?.[k]?.role);
  // MVP-STUB: presence of the census role, not the V12 count (the gate row carries the count)
  const missing = keys.filter((k) => !parts.some((p) => p.role === ctx.S.cls.censusRules[k].role));
  return { have: keys.length - missing.length, total: keys.length, frac: keys.length ? (keys.length - missing.length) / keys.length : 1, missing };
}

/** Everything the guard and the prompt read, for the module at `file`. */
export async function measure(ctx, file) {
  const text = fs.readFileSync(file, "utf8");
  const fail = (why) => ({ loads: false, why, text, hash: sha(text) });
  const syntax = moduleSyntaxError(text);
  if (syntax) return fail(`does not parse: ${syntax}`);
  const check = spawnSync(process.execPath, [path.join(ROOT, "scripts", "check-module.mjs"), file, "--subject", ctx.subjectId], { cwd: ROOT, encoding: "utf8" });
  if (check.status !== 0) return fail(`check-module: ${`${check.stdout}${check.stderr}`.trim().split(/\r?\n/).slice(0, 3).join(" / ")}`);
  let mod;
  let parts;
  try {
    mod = await loadModule(file);
    parts = mod.build();
    const bad = K.checkParts(mod.meta, parts);
    if (bad.length) return fail(`build: ${bad[0]}`);
  } catch (error) {
    return fail(`build threw: ${error.message}`);
  }
  const report = await validateParts(mod.meta, parts, undefined, { cls: ctx.S.cls, rules: ctx.rules, layout: ctx.gateLayout ?? ctx.layout, census: ctx.census });
  const res = await residuals({ subjectId: ctx.subjectId, modulePath: file });
  const zones = res.familyIoU;
  const zoneNames = Object.keys(zones);
  const minZoneName = zoneNames.reduce((a, b) => (a === null || zones[b] < zones[a] ? b : a), null);
  const zoneRows = zoneResiduals(res, ctx.zoneMin ?? {}, ctx.zoneProposals ?? {}, ctx.famKeys ?? {});
  const ranked = [...zoneRows, ...res.rows.filter((r) => r.areaPx >= SHOW.px || r.metres >= SHOW.metres)]
    .map((r) => ({ ...r, score: r.areaPx * (KIND_WEIGHT[r.kind] ?? 1) }))
    .sort((a, b) => b.score - a.score);
  // a zone under its band is always shown (it gates the stop): it takes the place of the lowest-ranked other rows
  const top = ranked.slice(0, SHOW.rows);
  const extra = zoneRows.filter((z) => !top.some((r) => r.kind === "ZONE" && r.family === z.family));
  const shown = extra.length ? ranked.filter((r) => r.kind === "ZONE" || top.slice(0, SHOW.rows - extra.length).includes(r)).slice(0, SHOW.rows) : top;
  // V5-1 item 4: the per-item accuracy report (render-as-target noise floor) — the exact stop reads it
  let acc = null;
  if (ctx.exactStop) { try { acc = await accuracy({ subjectId: ctx.subjectId, modulePath: file }); } catch (error) { acc = { exact: false, summary: `accuracy refused: ${error.message}`, items: [], unowned: [] }; } }
  return {
    loads: true, text, hash: sha(text), mod, parts, accuracy: acc,
    pass: report.pass, blocking: report.violations.length, codes: [...new Set(report.violations.map((v) => v.v))].sort(),
    gateText: report.text, violations: report.violations,
    tris: report.measurements.tris, triBudget: report.measurements.triBudget,
    iou: res.registeredIoU, zones, minZone: minZoneName ? zones[minZoneName] : 0, minZoneName, zoneRows,
    coverage: coverageOf(ctx, parts),
    ranked, shown, nRows: ranked.length,
  };
}

/**
 * V4-5A — one ZONE row per area family whose registered IoU is under its class band (classes/<c>.json zoneIouMin): its
 * size is the family's wrong px (U - I), its part the family's largest shape row, its knobs the class zoneProposals
 * entry (knob names / prefixes the ABSORB re-FIT resolves against the module's KNOBS). V4-6: the row names the family
 * as "<f>-family [its palette zone keys]" (a family is never a zone) and carries ONE proposal — the worst part's.
 */
export function zoneResiduals(res, zoneMin, proposals, famKeys = {}) {
  const out = [];
  for (const [f, band] of Object.entries(zoneMin)) {
    const iou = res.familyIoU?.[f];
    if (!Number.isFinite(iou) || iou >= band) continue;
    const px = res.familyPx?.[f] ? res.familyPx[f].U - res.familyPx[f].I : 0;
    const worst = res.rows.filter((r) => r.family === f && r.kind !== "MISSING").sort((a, b) => b.areaPx - a.areaPx)[0] ?? null;
    const prop = proposals[f] ?? {};
    const label = `${f}-family${famKeys[f]?.length ? ` [${famKeys[f].join("|")}]` : ""}`;
    const proposal = worst ? worst.proposal : `add or grow parts with a ${label} zone`;
    const text = `RESIDUAL ${label} ZONE IoU ${iou} < band ${band} (${px} px wrong)${worst ? ` — worst part "${worst.part}" ${worst.kind} side ${worst.side} ${r4(worst.metres)} m` : ""} — proposal: ${proposal}`;
    out.push({ target: label, family: f, kind: "ZONE", metres: r4(band - iou), part: worst?.part ?? "-", side: "-", areaPx: px, iou, band, knobPrefixes: prop.knobs ?? [], proposal, worst, text });
  }
  return out;
}

/** Palette auto-fix (unique closed key) before the guard reads a PALETTE_ZONE row. */
export async function measureFixed(ctx, file) {
  let m = await measure(ctx, file);
  if (m.loads && m.codes.includes("PALETTE_ZONE")) {
    const fixed = autoFixPaletteZones(m.text, m.violations);
    if (fixed.fixes.length) {
      fs.writeFileSync(file, fixed.text);
      m = await measure(ctx, file);
      m.paletteFixes = fixed.fixes;
    }
  }
  return m;
}

// ---------------------------------------------------------------------------
// Guard + stops
// ---------------------------------------------------------------------------

/**
 * Lexicographic, strictly better: the first tier that differs decides; whole IoU must gain >= IOU_GAIN when every
 * higher tier ties; tris over the budget and a module that does not load always lose.
 * @returns {{accept:boolean, reasons:string[], gain:number}}
 */
export function judge(c, b) {
  if (!c.loads) return { accept: false, reasons: [c.noEdit ? c.why : `the module does not load — ${c.why}`], gain: 0 };
  const gain = r4(c.iou - b.iou);
  if (c.tris > c.triBudget) return { accept: false, reasons: [`${c.tris} triangles, over the ${c.triBudget} budget`], gain };
  const newCodes = c.codes.filter((x) => !b.codes.includes(x));
  if (c.blocking > b.blocking || newCodes.length) {
    return { accept: false, reasons: [`gate got worse: blocking rows ${b.blocking} -> ${c.blocking}${newCodes.length ? `, new row ${newCodes.join(", ")}` : ""} — ${(String(c.gateText).split("\n")[1] ?? String(c.gateText)).replace(/^- /, "")}`.trim()], gain };
  }
  if (c.blocking < b.blocking) return { accept: true, reasons: [`gate blocking rows ${b.blocking} -> ${c.blocking}`], gain };
  if (c.coverage.frac < b.coverage.frac) return { accept: false, reasons: [`coverage ${b.coverage.have}/${b.coverage.total} -> ${c.coverage.have}/${c.coverage.total} (lost ${c.coverage.missing.filter((k) => !b.coverage.missing.includes(k)).join(", ")})`], gain };
  if (c.coverage.frac > b.coverage.frac) return { accept: true, reasons: [`coverage ${b.coverage.have} -> ${c.coverage.have} of ${c.coverage.total}`], gain };
  // V4-5A: zones under their class band (the stop's zone tier)
  const zb = (m) => (m.zoneRows ?? []).length;
  const zn = (m) => (m.zoneRows ?? []).map((r) => r.family).join(", ") || "none";
  if (zb(c) > zb(b)) return { accept: false, reasons: [`zones under band ${zb(b)} -> ${zb(c)} (${zn(c)})`], gain };
  if (zb(c) < zb(b)) return { accept: true, reasons: [`zones under band ${zb(b)} -> ${zb(c)} (${zn(c)})`], gain };
  if (c.minZone < b.minZone - ZONE_EPS) return { accept: false, reasons: [`min zone IoU ${b.minZone} (${b.minZoneName}) -> ${c.minZone} (${c.minZoneName})`], gain };
  if (c.minZone > b.minZone + ZONE_EPS) return { accept: true, reasons: [`min zone IoU ${b.minZone} -> ${c.minZone} (${c.minZoneName})`], gain };
  if (c.iou >= b.iou + IOU_GAIN - 1e-9) return { accept: true, reasons: [`whole IoU ${b.iou} -> ${c.iou}`], gain };
  return { accept: false, reasons: [`whole IoU ${c.iou} is not >= best ${b.iou} + ${IOU_GAIN} and no higher tier improved`], gain };
}

/**
 * Target reached: gate PASS, coverage 100 %, IoU >= band, no MISSING feature. Ruling 2026-09-26 (orchestrator): small
 * shape rows stay visible to the seat but never block the stop — the Opus-level module still shows ~4 rows at the
 * class floor from target-zone noise. `floor` is kept in the signature for callers; it no longer gates the stop.
 */
export function atTarget(m, floor, band = IOU_BAND, { exact = false } = {}) {
  if (!m.loads || !m.pass || m.coverage.frac < 1 || m.iou < band) return false;
  if (exact && !m.accuracy?.exact) return false;   // V5-1 item 4: every inventory item exact, no MISSING, no UNOWNED
  if ((m.zoneRows ?? []).length) return false;   // V4-5A: every zone at or over its class band
  return !m.shown.some((r) => r.kind === "MISSING");
}

// ---------------------------------------------------------------------------
// Knob attribution: which knob moves which side of which part (a perturbation per knob)
// ---------------------------------------------------------------------------

async function knobEffects(ctx, m) {
  if (ctx.effects.has(m.hash)) return ctx.effects.get(m.hash);
  const KN = m.mod.KNOBS;
  const out = {};
  if (KN && typeof KN === "object") {
    const la = ctx.reg.anchor.lengthAxis;
    const ax = la.findIndex((x) => x !== 0);
    const fwd = la[ax] > 0;
    const sides = (b) => ({ top: b.max[1], bottom: b.min[1], front: fwd ? b.max[ax] : b.min[ax], rear: fwd ? b.min[ax] : b.max[ax] });
    const boxes = (parts) => new Map(parts.map((p) => [p.id, sides(p.solid.aabb())]));
    const base = boxes(m.parts);
    for (const [name, k] of Object.entries(KN)) {
      if (k.locked || !(k.max > k.min)) continue;
      if (ctx.late()) { ctx.effectsCut = true; break; }   // V5-1: attribution stops at the wall clock
      await yieldTask();
      const d = k.unit === "exp" ? 0.25 : 0.02;
      const v0 = k.v;
      k.v = v0 + d <= k.max ? v0 + d : v0 - d;
      try {
        for (const [id, s] of boxes(m.mod.build())) {
          const b = base.get(id);
          if (!b) continue;
          for (const side of Object.keys(s)) {
            const delta = Math.abs(s[side] - b[side]);
            if (delta > 1e-4) ((out[id] ??= {})[side] ??= []).push({ name, delta });
          }
        }
      } catch { /* a knob step that breaks the build attributes nothing */ }
      k.v = v0;
    }
    for (const bySide of Object.values(out)) for (const list of Object.values(bySide)) list.sort((a, b) => b.delta - a.delta);
  }
  ctx.effects.set(m.hash, out);
  return out;
}

function rowSides(r) {
  if (r.kind === "EXTENT") return String(r.side).split("+");
  if (r.kind === "OFFSET") return r.side === "top" || r.side === "bottom" ? ["top", "bottom"] : ["front", "rear"];
  return [r.side];
}

/** The free knobs a row names: ZONE -> its class zoneProposals knobs / rc_ prefixes; shape -> the knobs moving its sides. */
function rowKnobs(m, effects, r) {
  const KN = m.mod?.KNOBS ?? {};
  const free = (n) => KN[n] && !KN[n].locked && KN[n].max > KN[n].min;
  if (r.kind === "ZONE") return r.knobPrefixes.flatMap((pre) => Object.keys(KN).filter((n) => n === pre || (pre.startsWith("rc_") && n.startsWith(pre)))).filter(free);
  return [...new Set(rowSides(r).flatMap((s) => (effects[r.part]?.[s] ?? []).slice(0, 2).map((e) => e.name)))].filter(free);
}

export const rowKey = (r) => (r.kind === "ZONE" ? `ZONE:${r.family}` : `${r.kind}:${r.part}:${r.side}:${r.target}`);

/**
 * V5-6 ruling (ABSORB guard): a harness re-FIT may never cost an exact inventory item. Kept only when the lexicographic
 * guard accepts it (IoU tiers not worse) AND the exact-item count is >= before (both counts known; an unknown count on
 * either side falls back to the plain guard).
 */
export function absorbJudge(c, b) {
  const j = judge(c, b);
  if (!j.accept) return j;
  const nb = b.accuracy?.exactN;
  const nc = c.accuracy?.exactN;
  if (Number.isFinite(nb) && Number.isFinite(nc) && nc < nb) {
    return { accept: false, reasons: [`exact items ${nb} -> ${nc} (ABSORB may not lose an exact item)`], gain: j.gain };
  }
  return j;
}

/**
 * V4-6 item 3 — ABSORB: before a LOOP prompt the harness tries the knob-level fixes itself: one short zone-weighted
 * re-FIT (ABSORB_EVALS, ABSORB_ZONE_W) over the union of the knobs the shown rows name, kept only when the guard
 * accepts it. Per row: absorbed = the re-FIT was kept and the row is no longer shown.
 */
async function absorbRows(ctx, m, dir) {
  const effects = await knobEffects(ctx, m);
  const rows = m.shown.map((r) => ({ r, knobs: rowKnobs(m, effects, r) }));
  const knobs = [...new Set(rows.flatMap((x) => x.knobs))];
  const rec = { knobs, rows: rows.map(({ r, knobs: k }) => ({ row: r.text.replace(/ — proposal: .*$/, ""), knobs: k, absorbed: false, px: [r.areaPx, r.areaPx] })) };
  if (!ctx.fitEnabled || !m.mod?.KNOBS || !knobs.length) return { ...rec, skipped: !knobs.length ? "no shown row names a free knob" : "fit disabled / no KNOBS", m };
  // V5-1 bug (b): the same best module was already ABSORBed (a rejected step reverts to it): the deterministic re-FIT
  // would repeat itself — reuse its outcome
  if (ctx.absorbedFor?.hash === m.hash) return { ...ctx.absorbedFor.rec, skipped: `same module as the last ABSORB (${ctx.absorbedFor.rec.accepted ? "kept" : "reverted"} then)`, m };
  if (ctx.late()) return { ...rec, skipped: "wall clock", m };
  const file = path.join(path.dirname(ctx.cur), "absorb.mjs");
  placeModule(m.text, file);
  let r;
  try {
    r = await fit({ subjectId: ctx.subjectId, modulePath: file, out: file, evals: ABSORB_EVALS, knobs, zoneW: ABSORB_ZONE_W, log: path.join(dir, "absorb.fit.json"), deadline: ctx.deadlineAt });
  } catch (error) {
    return { ...rec, skipped: `FIT refused: ${error.message}`, m };
  }
  const m2 = await measureFixed(ctx, file);
  const j = absorbJudge(m2, m);
  const after = j.accept ? m2 : m;
  rows.forEach(({ r: row }, i) => {
    const now = after.ranked.find((x) => rowKey(x) === rowKey(row));
    rec.rows[i].px[1] = now ? now.areaPx : 0;
    rec.rows[i].absorbed = j.accept && !after.shown.some((x) => rowKey(x) === rowKey(row));
  });
  const done = { ...rec, evals: r.evals, ms: r.ms, accepted: j.accept, verdict: j.reasons.join("; "), iou: [m.iou, m2.iou ?? null] };
  ctx.absorbedFor = { hash: m.hash, rec: done };
  return { ...done, m: after };
}

// ---------------------------------------------------------------------------
// Prompts
// ---------------------------------------------------------------------------

export function numbered(lines, keep) {
  const width = String(lines.length).length;
  const out = [];
  let last = -2;
  for (const i of [...keep].sort((a, b) => a - b)) {
    if (i !== last + 1) out.push(`${" ".repeat(width)}| …`);
    out.push(`${String(i + 1).padStart(width)}| ${lines[i]}`);
    last = i;
  }
  return out;
}

function scoreboard(ctx, m, { step, verdict }) {
  // V4-6 item 2: IoU is per colour FAMILY; a family name is never a zone — its palette zone keys ride in [ ]
  const fk = ctx.famKeys ?? {};
  const zones = Object.entries(m.zones).map(([k, v]) => `${k}${fk[k]?.length ? `[${fk[k].join("|")}]` : ""} ${v}${ctx.zoneMin?.[k] !== undefined ? ` (band ${ctx.zoneMin[k]}${v < ctx.zoneMin[k] ? " UNDER" : ""})` : ""}`).join(", ");
  const palette = Object.keys(m.mod?.meta?.palette ?? {});
  const lines = [
    `# SCOREBOARD — ${step}`,
    "",
    `- gate: ${m.pass ? "PASS" : `FAIL, ${m.blocking} blocking row(s) ${m.codes.join(", ")}`}`,
    `- registered silhouette IoU: whole ${m.iou} (best so far ${ctx.bestIoU ?? m.iou}; target >= ${ctx.band}) | per colour family [its zones]: ${zones}`,
    ...(palette.length ? [`- ZONES (closed: a part's zone is one of these meta.palette keys, never a family name): ${palette.join(", ")}`] : []),
    `- coverage: ${m.coverage.have}/${m.coverage.total} census features${m.coverage.missing.length ? ` — missing ${m.coverage.missing.join(", ")}` : ""}`,
    `- triangles: ${m.tris} / ${m.triBudget}`,
    `- last verdict: ${verdict}`,
  ];
  if (!m.pass) lines.push("", "```", ...String(m.gateText).split(/\r?\n/).filter((l) => l.trim()).slice(0, 6), "```");
  return lines;
}

export function readyBlock(ctx, m, ready) {
  if (!ready.length) return [];
  const needCab = ready.some((c) => /\bhost:\s*cab\b/.test(c.call)) && !/\b(const|let|var)\s+cab\b/.test(m.text);
  return [
    "",
    `# READY CALLS — MISSING features (insert before \`return parts;\`; every number is a KNOBS entry the harness adds and fits after you)`,
    "",
    "```js",
    ...(needCab ? ['const cab = parts.find((p) => p.id === "cab");'] : []),
    ...ready.flatMap((c) => [`// ${c.what}`, c.call]),
    "```",
  ];
}

/** The READY calls of features the module lacks, knobified (R1). */
export async function missingReady(ctx, m) {
  const frame = await moduleFrame(m.parts, ctx.S);
  const calls = frame?.ready ? frame.ready(ctx.layout, null, ctx.minFeat) : [];
  const missing = calls.filter((c) => !featurePresent(c.call, m.parts));
  const knobbed = knobifyCalls(missing, { existing: definedKnobs(m.text), offered: ctx.offered, span: ctx.span, floor: ctx.rcFloor });
  // A READY call that does not build on THIS (fitted) body is a harness fault (its measured keys disagree with the
  // fitted host), never offered to a seat: trial-insert each one alone and keep the ones that build.
  const trial = path.join(path.dirname(ctx.cur), "trial.mjs");
  const kept = [];
  for (const c of knobbed) {
    await yieldTask();
    const needCab = /\bhost:\s*cab\b/.test(c.call) && !/\b(const|let|var)\s+cab\b/.test(m.text);
    const ins = applyReply(m.text, ["```js", ...(needCab ? ['const cab = parts.find((p) => p.id === "cab");'] : []), c.call, "```"].join("\n"));
    placeModule(addKnobEntries(ins.text, ctx.offered).text, trial);
    try {
      const mod = await loadModule(trial);
      const parts = mod.build();
      if (K.checkParts(mod.meta, parts).length) throw new Error(K.checkParts(mod.meta, parts)[0]);
      kept.push(c);
    } catch (error) {
      if (!ctx.dropped.some((d) => d.what === c.what)) ctx.dropped.push({ what: c.what, why: String(error.message).split("\n")[0] });
    }
  }
  fs.rmSync(trial, { force: true });
  return kept;
}

/** V5-1 bug (b): the edits already tried on this best module and rejected — a seat must not send them again. */
export function rejectedBlock(ctx) {
  const list = (ctx.rejected ?? []).filter((r) => r.base === ctx.bestHash).slice(-3);
  if (!list.length) return [];
  return ["", "# ALREADY TRIED AND REJECTED on this module — do NOT send these again", "",
    ...list.map((r) => `- step ${r.step}: ${r.edit} -> ${r.why}`)];
}

/** The candidate's lines that differ from the base module (the edit, compact). */
export function editSummary(base, cand, max = 2) {
  const have = new Set(String(base).split(/\r?\n/).map((l) => l.trim()));
  const added = String(cand).split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !have.has(l));
  if (!added.length) return "(no line changed)";
  return added.slice(0, max).map((l) => `\`${l.length > 140 ? `${l.slice(0, 140)} …` : l}\``).join(" ; ") + (added.length > max ? ` (+${added.length - max} line(s))` : "");
}

export function assertPromptSize(text, what) {
  const n = bytes(text);
  if (n > PROMPT_MAX) throw new Error(`${what} prompt is ${n} bytes, over the ${PROMPT_MAX} byte limit`);
  return n;
}

export function buildPrompt(ctx, m, ready, board = scoreboard) {
  const lines = m.text.split(/\r?\n/);
  const b0 = lines.findIndex((l) => /export\s+function\s+build\b/.test(l));
  const ret = lines.reduce((a, l, i) => (/^\s*return parts;/.test(l) ? i : a), -1);
  const make = (whole) => {
    const keep = new Set();
    if (whole && b0 >= 0) for (let i = b0; i < lines.length; i += 1) keep.add(i);
    else for (let d = -2; d <= 2; d += 1) if (ret + d >= 0 && ret + d < lines.length) keep.add(ret + d);
    return [
      `# BUILD — subject ${ctx.subjectId} (${ctx.S.klass})`,
      "",
      `The harness has FITTED the body to the target. Your one job in this call: add the MISSING features with the READY CALLS below — paste them before line ${ret + 1} \`return parts;\`. Their numbers are \`KNOBS.<name>.v\` entries the harness adds to the KNOBS block and fits after you: never type metres.`,
      "",
      ...board(ctx, m, { step: "BUILD", verdict: "START + FIT" }),
      ...readyBlock(ctx, m, ready),
      "",
      `# YOUR MODULE — ${whole ? "build()" : "the insert point"}, numbered`,
      "",
      "```js",
      ...numbered(lines, keep),
      "```",
      "",
      "Do not run commands or read files. Reply with ONE ```js fence holding only the lines to insert before `return parts;` (the READY CALLS, adapted only where a host part id differs), or with numbered lines `N| new code` (replace line N) copied from the display above. Keep every `KNOBS.<name>.v`. Then one line `CHANGE: …`.",
    ].join("\n");
  };
  const full = make(true);
  return bytes(full) <= PROMPT_MAX ? full : make(false);
}

/**
 * V4-6 item 3 — ONE structural edit per open row (the knob-level fixes were ABSORBed by the harness first): the row's
 * own concrete proposal (ZONE: its worst part's), placed in the call that builds the part, with what FIT already did.
 */
function rowEdit(r, knobs, KN, cites) {
  const line = cites.length ? `line ${cites[0] + 1}` : null;
  const base = r.kind === "ZONE" ? r.worst : r;
  if (!base) return `add or grow parts with a zone of ${r.target}`;
  const at = knobs.filter((n) => KN[n] && (KN[n].v <= KN[n].min || KN[n].v >= KN[n].max)).map((n) => `${n} AT ${KN[n].v <= KN[n].min ? "MIN" : "MAX"}`);
  const fitNote = knobs.length ? `FIT already tried ${knobs.slice(0, 3).join(", ")}${at.length ? ` (${at.join(", ")})` : ""}, so change structure: ` : "";
  if (base.kind === "MISSING") return `${base.proposal}${line ? ` — insert after ${line}` : ""}`;
  if (base.kind === "EXTRA") return `remove part "${base.part}"${line ? ` — ${line} builds it` : ""}`;
  return `${fitNote}${base.proposal}${line ? ` — in the call on ${line}` : ""}`;
}

async function loopPrompt(ctx, m, { k, K: KK, verdict, ready, absorb = null }) {
  const effects = await knobEffects(ctx, m);
  const lines = m.text.split(/\r?\n/);
  const kb = knobBlock(m.text);
  const kbLines = kb ? [m.text.slice(0, kb.start).split("\n").length - 1, m.text.slice(0, kb.end).split("\n").length] : [-1, -1];
  const inKnobs = (i) => i >= kbLines[0] && i <= kbLines[1];
  const KN = m.mod.KNOBS ?? {};
  const citeOf = (r) => {
    const knobs = rowKnobs(m, effects, r).slice(0, r.kind === "ZONE" ? 3 : 2);
    const cites = [];
    const part = r.kind === "ZONE" ? r.worst?.part : r.part;
    // the line that BUILDS the part: a line naming it, else a line reading one of its knobs
    if (part && part !== "-") {
      const i = lines.findIndex((l, j) => !inKnobs(j) && l.includes(`"${part}"`));
      if (i >= 0) cites.push(i);
    }
    for (const n of knobs) {
      const re = new RegExp(`\\b(k|KNOBS)\\.${n}\\b`);
      const i = lines.findIndex((l, j) => !inKnobs(j) && re.test(l));
      if (i >= 0 && !cites.includes(i)) cites.push(i);
    }
    return { knobs, cites: cites.slice(0, 2) };
  };
  const ret = lines.reduce((a, l, i) => (/^\s*return parts;/.test(l) ? i : a), -1);
  const nAbs = absorb?.rows ? absorb.rows.filter((x) => x.absorbed).length : 0;
  const absorbLine = absorb?.rows?.length
    ? `The harness re-FITTED the knobs of ${absorb.rows.length} row(s) before this prompt: ${nAbs} absorbed${absorb.accepted ? ` (kept, IoU ${absorb.iou[0]} -> ${absorb.iou[1]})` : absorb.skipped ? ` (${absorb.skipped})` : " (no gain, reverted)"}. What is left needs STRUCTURE.`
    : "The harness fits every KNOBS value; what is left needs STRUCTURE.";
  const make = (nRows, context, clip) => {
    const rows = m.shown.slice(0, nRows);
    const keep = new Set();
    const rowLines = [];
    rows.forEach((r, i) => {
      const { knobs, cites } = citeOf(r);
      for (const c of cites) for (let d = -context; d <= context; d += 1) if (c + d >= 0 && c + d < lines.length) keep.add(c + d);
      rowLines.push(`${i + 1}. ${r.text.replace(/ — proposal: .*$/, "")} (${r.areaPx} px)`);
      rowLines.push(`   edit: ${rowEdit(r, knobs, KN, cites)}`);
    });
    if (ready.length && ret >= 0) for (let d = -Math.min(context, 1); d <= 0; d += 1) keep.add(ret + d);
    const shown = lines.map((l) => (clip && l.length > clip ? `${l.slice(0, clip)} …` : l));
    return [
      `# LOOP ${k} of ${KK} — subject ${ctx.subjectId} (${ctx.S.klass})`,
      "",
      `${absorbLine} You choose structure: a call's arguments, parts added or removed, what attaches where. Do row 1 first; one edit per row.`,
      "",
      ...scoreboard(ctx, m, { step: `step ${k} of ${KK}`, verdict }),
      "",
      `# OPEN RESIDUALS — top ${rows.length} of ${m.nRows} (px >= ${SHOW.px} or >= ${SHOW.metres} m, ranked by px x weight), ONE edit each`,
      "",
      ...(rowLines.length ? rowLines : ["(none)"]),
      ...rejectedBlock(ctx),
      ...readyBlock(ctx, m, ready),
      "",
      `# YOUR MODULE — the cited lines ±${context}, numbered \`N| code\``,
      "",
      "```js",
      ...numbered(shown, keep),
      "```",
      "",
      NUMBERED_CONTRACT,
      "KNOBS values are re-fitted by the harness after you; numbers you type in a structural edit are fine.",
    ].join("\n");
  };
  for (const [nRows, context, clip] of [[8, 2, 0], [8, 1, 0], [8, 0, 0], [6, 1, 0], [6, 0, 160], [4, 0, 120], [2, 0, 100]]) {
    const text = make(nRows, context, clip);
    if (bytes(text) <= PROMPT_MAX) return text;
  }
  return make(1, 0, 80);
}

// ---------------------------------------------------------------------------
// Images: the registered compare sheet
// ---------------------------------------------------------------------------

async function renderSheet(ctx, text, name, out) {
  const capture2 = await import("./capture2.mjs");
  const { captureToTarget, composeSheet, readRGB } = await import("./registered.mjs");
  const refFile = path.join(ROOT, "out", "ref", `loop-${ctx.subjectId}`, `${name}.mjs`);
  placeModule(text, refFile);
  const moduleRel = relPath(refFile);
  process.env.BLINDLOOP_CONFIG = process.env.BLINDLOOP_CONFIG || path.join(ROOT, "..", "BlindLoop", "config.llmmodeling.json");
  const q = `capture=1&subject=${ctx.subjectId}&seed=1&size=900&module=${encodeURIComponent(moduleRel)}`;
  const dir = path.dirname(out);
  const shots = [
    { name: "target-shaded", url: `${DEV_SERVER}?${q}&view=target&shade=1`, out: path.join(dir, "target-shaded.png") },
    { name: "threeQuarter-shaded", url: `${DEV_SERVER}?${q}&view=threeQuarter&shade=1`, out: path.join(dir, "threeQuarter-shaded.png") },
  ];
  await capture2.captureAll(shots);
  const target = ctx.targetImg ??= await readRGB(ctx.S.paths.target);
  const proj = await project({ subjectId: ctx.subjectId, modulePath: moduleRel, frame: "target", size: target.w });
  const map = captureToTarget(proj.registration, { centre: proj.capture.centre, half: proj.capture.half, size: 900 });
  const renderMask = proj.foreground();
  const { targetState, iou } = await import("./registered.mjs");
  const tm = targetState(ctx.S, target);   // V5-1 item 1: the three-state target (OCCLUDED = don't care)
  await composeSheet({ target, shaded: await readRGB(shots[0].out), threeQuarterFile: shots[1].out, map, renderMask, out, iouValue: iou(tm, renderMask), targetMask: tm });
  return out;
}

// ---------------------------------------------------------------------------
// The loop
// ---------------------------------------------------------------------------

function startText(subjectId, from) {
  if (from) return fs.readFileSync(path.resolve(ROOT, from), "utf8");
  const S = loadSubject(subjectId);
  if (S.klass !== "vehicle" && S.klass !== "building") throw new Error(`loop: no KNOBS template for class "${S.klass}" yet — pass --from <module>`);   // MVP-STUB
  return null;   // resolved in runLoop (dynamic import keeps the template off the building path)
}

/**
 * @param {{subjectId:string, seat:string, from?:string|null, K?:number, images?:boolean, evals?:number,
 *   outDir?:string, workDir?:string, targetFloor?:{metres:number, px:number}|null, fitEnabled?:boolean, log?:Function}} o
 * @returns {Promise<object>} the loop.json record (exitCode inside)
 */
export async function runLoop({ subjectId, seat, from = null, K: KK = 4, images = true, evals = FIT_EVALS, outDir = null, workDir = null,
  targetFloor = null, targetBand = null, zoneBands = null, fitEnabled = true, log = console.log, timeMs = null, similarity = true, exactStop: exactIn = true,
  featureFit: featureIn = null, facePalette: paletteIn = null, v5Detail = false, turnaround = true }) {
  const t0 = performance.now();
  const S = loadSubject(subjectId);
  // V6-2: the v6 multi-view path; its V5 detail (per-feature FIT, per-face palette, exactness stop) is the ablation hook
  const v6 = turnaround && hasTurnaround(subjectId) ? await import("./v6/loop6.mjs") : null;
  const exactStop = v6 ? v5Detail : exactIn;
  const featureFit = featureIn ?? exactStop;
  const facePalette = paletteIn ?? exactStop;
  await K.init();
  if (K.assemble?.ready) await K.assemble.ready;
  try { K.configure(gateConfig(S.cls)); } catch { K.configure(null); }
  const out = path.resolve(ROOT, outDir ?? path.join(S.subject.outDir ?? `out/${subjectId}`, "loop"));
  const work = path.resolve(ROOT, workDir ?? path.join("out", "ref", `loop-${subjectId}`));
  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(out, { recursive: true });
  fs.mkdirSync(work, { recursive: true });
  const reg = subjectRegistration(subjectId);
  const census = Object.fromEntries(Object.entries(S.readJson("census") ?? {}).filter(([k]) => !k.startsWith("_")));
  const ctx = {
    S, subjectId, reg, census, layout: S.readJson("layout"), rules: await import(pathToFileURL(path.join(ROOT, S.cls.rules)).href),
    floor: targetFloor ?? S.cls.residualFloor ?? { metres: 0, px: 0 }, band: targetBand ?? S.cls.iouBand ?? IOU_BAND,
    zoneMin: zoneBands ?? S.cls.zoneIouMin ?? {}, zoneProposals: S.cls.zoneProposals ?? {}, exactStop,
    span: readyCallSpan(S.cls, reg), rcFloor: S.cls.knobPriors?._readyCall ? 0.001 : -Infinity, minFeat: gateConfig(S.cls).minFeat ?? 0.04, offered: {}, effects: new Map(), bestIoU: null, dropped: [],
    fitEnabled, famKeys: familyZoneKeys(S), featureFit, facePalette,
    deadlineAt: t0 + (timeMs ?? (v6 && !process.env.LLMM_LOOP_TIME_MS ? v6.V6_TIME_MS : timeLimitMs())), rejected: [], bestHash: null, absorbedFor: null,
  };
  ctx.gateLayout = gateLayout(S, ctx.rules);   // V5-9: the accuracy report gates features; their layout keys are advisory
  ctx.late = () => performance.now() > ctx.deadlineAt;
  if (images && !v6) {   // the v6 sheet renders in-process
    try {
      const r = await fetch(DEV_SERVER);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
    } catch (error) {
      const e = new Error(`no dev server at ${DEV_SERVER} (${error.message}) — start it (preview "llmmodeling") or pass --no-images`);
      e.exitCode = 2;
      throw e;
    }
  }
  const runSeat = await loadSeat(seat);
  const cur = path.join(work, "cur.mjs");
  ctx.cur = cur;
  const cand = path.join(work, "cand.mjs");
  const steps = [];
  const seatCalls = [];
  const record = { subject: subjectId, seat, from, K: KK, images, floor: ctx.floor, band: ctx.band, zoneBands: ctx.zoneMin, steps, stop: null, exitCode: 1, ...(v6 ? { path: "v6", v5Detail } : {}) };
  const writeRecord = () => {
    record.ms = Math.round(performance.now() - t0);
    record.iouTrace = steps.map((s) => ({ step: s.step, iou: s.iou, accepted: s.accepted }));
    record.seatSeconds = r4(steps.reduce((a, s) => a + (s.seatSeconds ?? 0), 0));
    record.promptBytes = steps.filter((s) => s.promptBytes).map((s) => ({ step: s.step, bytes: s.promptBytes }));
    record.seatCalls = seatCalls;   // V4-6 item 4: every seat call (syntax follow-ups too) with its own seconds
    record.readyDropped = ctx.dropped;
    fs.writeFileSync(path.join(out, "loop.json"), `${JSON.stringify(record, null, 2)}\n`);
  };

  const stepDir = (name) => { const d = path.join(out, String(name)); fs.mkdirSync(d, { recursive: true }); return d; };
  const archive = async (name, m, verdict, extra = {}) => {
    const d = stepDir(name);
    placeModule(m.text, path.join(d, "module.mjs"));
    if (m.loads) {
      fs.writeFileSync(path.join(d, "residuals.json"), `${JSON.stringify({ iou: m.iou, zones: m.zones, nRows: m.nRows, shown: m.shown.map(({ text, kind, part, side, metres, areaPx }) => ({ text, kind, part, side, metres, areaPx })) }, null, 2)}\n`);
    }
    let acc = null;
    if (m.loads) {
      try {
        acc = m.accuracy ?? await accuracy({ subjectId, modulePath: path.join(d, "module.mjs") });
        fs.writeFileSync(path.join(d, "accuracy.json"), `${JSON.stringify({ ...acc, floorRows: undefined, top: topFailing(acc, 5) }, null, 2)}\n`);
      } catch (error) { log(`[loop] ${name}: accuracy refused — ${error.message}`); }
    }
    let sheet = null;
    if ((images || ctx.v6) && m.loads) {
      try { sheet = ctx.v6 ? await ctx.v6.sheet(m, path.join(d, "sheet.png")) : await renderSheet(ctx, m.text, `${name}-${m.hash}`, path.join(d, "sheet.png")); } catch (error) { log(`[loop] ${name}: sheet refused — ${error.message}`); }
    }
    const v = {
      step: String(name), loads: m.loads, why: m.why ?? null, pass: m.pass ?? false, blocking: m.blocking ?? null, codes: m.codes ?? [],
      iou: m.iou ?? null, zones: m.zones ?? null, minZone: m.minZone ?? null, zonesUnder: m.zoneRows ? m.zoneRows.map((r) => r.family) : null, coverage: m.coverage ?? null, tris: m.tris ?? null,
      verdict, ...extra, accuracy: acc ? acc.summary : null,
    };
    fs.writeFileSync(path.join(d, "verdict.json"), `${JSON.stringify(v, null, 2)}\n`);
    steps.push({ ...v, coverage: m.coverage ? `${m.coverage.have}/${m.coverage.total}` : null });
    return sheet;
  };

  let seatN = 0;
  const callSeat = async (prompt, imgs, name) => {
    seatN += 1;
    const d = stepDir(name);
    fs.writeFileSync(path.join(d, "prompt.md"), prompt);
    const t = performance.now();
    // V5-1 bug (a): a seat call never outlives the run's wall clock (+ 60 s to answer)
    const timeoutMs = Math.max(60 * 1000, Math.min(SEAT_TIMEOUT_MS, ctx.deadlineAt - performance.now() + 60 * 1000));
    const s = await runSeat({ prompt, images: imgs, workspace: ROOT, timeoutMs, tag: `loop-${subjectId}-${name}-${seatN}`, mode: "text", outFile: path.join(d, "reply.md"), modulePath: null });
    s.seconds = s.seconds || (performance.now() - t) / 1000;
    seatCalls.push({ step: String(name), seconds: r4(s.seconds), promptBytes: bytes(prompt), images: imgs.length });
    fs.writeFileSync(path.join(d, "reply.md"), `${s.answer ?? ""}\n`);
    seatOutcome(s, `loop ${name}`);   // transport / timeout -> SeatTransportError (exit 2)
    return s;
  };

  /** A seat reply -> a measured candidate (knob entries added, one syntax-only follow-up, palette calibrated). */
  const candidateFrom = async (best, s, name) => {
    let applied = applyReply(best.text, s.answer);
    let seconds = 0;
    if (applied.text !== null) {
      const syntax = moduleSyntaxError(applied.text);
      if (syntax) {
        const f = await callSeat(syntaxFollowUpPrompt(syntax, applied.text), [], `${name}-syntax`);
        seconds += f.seconds ?? 0;
        const art = f.artifact;
        applied = art && !moduleSyntaxError(art) ? { text: art, how: "syntax follow-up (complete module)" } : { text: null, why: `does not parse (${syntax}) after one syntax-only follow-up` };
      }
    }
    if (applied.text === null) return { m: { loads: false, noEdit: true, why: applied.why, text: best.text, hash: best.hash }, how: null, added: [], seconds };
    const withKnobs = addKnobEntries(applied.text, ctx.offered);
    // V4-6 item 2: unknown zone names -> their unique palette key, BEFORE check-module's load check
    const zf = await fixZones(ctx.S, withKnobs.text, cand, best);
    placeModule(zf.text, cand);
    // V5-1 bug (b): a candidate identical to one already rejected on this best module is refused unscored
    const candHash = sha(fs.readFileSync(cand, "utf8"));
    const again = (ctx.rejected ?? []).find((r) => r.base === best.hash && r.hash === candHash);
    if (again) {
      return { m: { loads: false, noEdit: true, why: `the same edit as step ${again.step}, already rejected (${again.why}) — send a DIFFERENT edit`, text: fs.readFileSync(cand, "utf8"), hash: best.hash }, how: applied.how, added: withKnobs.added, seconds, zoneFixes: zf.fixes, repeat: true };
    }
    // V4-6 item 1: a reply whose module builds a part id twice is refused here, with the reason, before the gate
    const dup = await duplicateIds(cand);
    if (dup && dup.length) {
      const why = `refused before build: the edit builds duplicate part ids ${dup.slice(0, 4).map((q) => `"${q}"`).join(", ")}${dup.length > 4 ? ` (+${dup.length - 4} more)` : ""} — a helper call now runs twice; to change a line, reply with that numbered line (\`N| new code\`), not a copy of it`;
      return { m: { loads: false, noEdit: true, why, text: fs.readFileSync(cand, "utf8"), hash: best.hash }, how: applied.how, added: withKnobs.added, seconds, zoneFixes: zf.fixes };
    }
    await calibrate(ctx, cand);
    const m = ctx.v6 ? await ctx.v6.measure(cand) : await measureFixed(ctx, cand);
    return { m, how: applied.how, added: withKnobs.added, unknown: withKnobs.unknown, seconds, zoneFixes: zf.fixes, placedHash: candHash };
  };

  const fitFile = async (file, name) => {
    const mod = await loadModule(file);
    if (!fitEnabled || !mod.KNOBS) return { skipped: !fitEnabled ? "fit disabled" : "no KNOBS block" };
    try {
      const before = fs.readFileSync(file, "utf8");
      const r = await fit({ subjectId, modulePath: file, out: file, evals, log: path.join(stepDir(name), "fit.json"), deadline: ctx.deadlineAt });
      // V4-5A: FIT's zone terms may trade whole-silhouette IoU away; a FIT that lowers the registered IoU is not kept
      if (r.end.registeredIoU < r.start.registeredIoU) {
        fs.writeFileSync(file, before);
        return { from: r.start.registeredIoU, to: r.start.registeredIoU, evals: r.evals, moved: 0, ms: r.ms, values: knobValues(before), reverted: `FIT lowered IoU ${r.start.registeredIoU} -> ${r.end.registeredIoU}`, start: r };
      }
      return { from: r.start.registeredIoU, to: r.end.registeredIoU, evals: r.evals, moved: Object.keys(r.knobs).length, ms: r.ms, values: r.values, start: r, ...(r.timedOut ? { timedOut: true } : {}) };
    } catch (error) {
      return { skipped: `FIT refused: ${error.message}` };
    }
  };

  /** V5-4 item 2: the per-feature FIT stage on `file` (in place), then the palette stage when it moved a knob */
  const featureFile = async (file, name) => {
    if (!featureFit || !fitEnabled || ctx.late()) return null;
    try {
      const r = await fitFeatures({ subjectId, modulePath: file, out: file, deadline: ctx.deadlineAt, log: path.join(stepDir(name), "features.json") });
      if (r.kept) await calibrate(ctx, file);
      const moved = (r.items ?? []).filter((it) => it.moved && Object.keys(it.moved).length);
      return r.skipped ? { skipped: r.skipped } : {
        evals: r.evals, ms: r.ms, kept: r.kept, reverted: r.reverted ?? null, exact: r.exact, registeredIoU: r.registeredIoU,
        items: moved.map((it) => `${it.id} ${it.before.score} -> ${it.after.score}`),
      };
    } catch (error) {
      return { skipped: `per-feature FIT refused: ${error.message}` };
    }
  };
  const featureLine = (f) => (!f ? "" : f.skipped ? `; FEATURES ${f.skipped}` : `; FEATURES ${f.kept ? "kept" : `not kept${f.reverted ? ` (${f.reverted})` : ""}`} ${f.exact.before} -> ${f.exact.after ?? "unchanged"} (${f.items.length} item(s) moved, ${f.evals} evals, ${Math.round(f.ms / 1000)} s)`);

  const accept = (m) => { placeModule(m.text, cur); ctx.bestIoU = m.iou; ctx.bestHash = m.hash; return m; };
  /** V5-1 bug (b): remember a rejected candidate (per best module) so it is never re-sent nor re-scored */
  const remember = (step, base, c, why) => {
    if (c.repeat || !c.m.text || c.m.hash === base.hash) return;
    ctx.rejected.push({ step: String(step), base: base.hash, hash: c.placedHash ?? sha(c.m.text), edit: editSummary(base.text, c.m.text), why });
  };
  let best;
  let exit = 1;
  try {
    if (v6) {
      await v6.runV6({ ctx, record, out, from, K: KK, images, log, archive, callSeat, candidateFrom, accept, remember, featureFile, setBest: (m) => { best = m; } });
      exit = record.stop === "target" ? 0 : 1;
    } else {   // ---- the v4 / v5 path (indentation kept: unchanged code)
    // ---- START + FIT
    let text = startText(subjectId, from);
    if (text === null) {
      text = S.klass === "building"
        ? (await import("./template-building.mjs")).generateForSubject(subjectId, { knobs: true }).text
        : (await import("./template-vehicle.mjs")).generateForSubject(subjectId).text;
    }
    // V5-1 item 2: the fitted similarity (absolute scale + placement are free in ortho) rides in the KNOBS block
    if (similarity) text = addFrameKnobs(text);
    placeModule(text, cur);
    await calibrate(ctx, cur);
    const f0 = await fitFile(cur, "start");
    const ff0 = f0.skipped ? null : await featureFile(cur, "start");
    if (!f0.skipped && !ff0?.kept) await calibrate(ctx, cur);   // the palette stage on the fitted geometry
    best = accept(await measureFixed(ctx, cur));
    if (!best.loads) throw new Error(`loop: the start module does not load — ${best.why}`);
    log(`[loop] START${f0.skipped ? ` (${f0.skipped})` : ` + FIT ${f0.from} -> ${f0.to} (${f0.evals} evals)`}${featureLine(ff0)}: IoU ${best.iou}, gate ${best.pass ? "PASS" : best.codes.join(",")}, coverage ${best.coverage.have}/${best.coverage.total}`);
    let bestSheet = await archive("start", best, "START", { fit: f0.skipped ? f0.skipped : { from: f0.from, to: f0.to, evals: f0.evals }, ...(ff0 ? { features: ff0 } : {}) });
    // V4-6 item 4: an image goes to the seat only when the best module changed since the last one sent
    let sentFor = null;
    const imgs = () => {
      if (!images || !bestSheet || sentFor === best.hash) return [];
      sentFor = best.hash;
      return [bestSheet];
    };
    const deadline = () => ctx.late();
    const stop = (reason) => { record.stop = reason; log(`[loop] STOP: ${reason}`); };

    let verdict = "START + FIT";
    if (atTarget(best, ctx.floor, ctx.band, { exact: ctx.exactStop })) stop("target");
    else if (deadline()) stop(`time (${Math.round(timeLimitMs() / 60000)} min, during START FIT)`);
    else {
      // ---- BUILD (+ re-FIT)
      const ready = await missingReady(ctx, best);
      if (ready.length) {
        const prompt = buildPrompt(ctx, best, ready);
        const promptBytes = assertPromptSize(prompt, "BUILD");
        const s = await callSeat(prompt, imgs(), "build");
        const c = await candidateFrom(best, s, "build");
        let refit = null;
        let feats = null;
        if (c.m.loads) {
          refit = await fitFile(cand, "build");
          if (!refit.skipped) {
            feats = await featureFile(cand, "build");
            if (!feats?.kept) await calibrate(ctx, cand);
            c.m = await measureFixed(ctx, cand);
          }
        }
        const j = judge(c.m, best);
        verdict = `BUILD ${j.accept ? "ACCEPTED" : "REJECTED"} — ${j.reasons.join("; ")}${c.how ? ` (${c.how}${c.added.length ? `, ${c.added.length} knob(s) added` : ""})` : ""}`;
        if (feats) log(`[loop] BUILD${featureLine(feats)}`);
        log(`[loop] ${verdict}`);
        const sheet = await archive("build", c.m, verdict, {
          accepted: j.accept, gain: j.gain, promptBytes, seatSeconds: r4((s.seconds ?? 0) + c.seconds), knobsAdded: c.added, knobStart: Object.fromEntries(c.added.map((n) => [n, ctx.offered[n].v])), unknownKnobs: c.unknown ?? [], zoneFixes: c.zoneFixes ?? [],
          refit: refit ? (refit.skipped ?? { from: refit.from, to: refit.to, evals: refit.evals, moved: refit.moved, ...(refit.reverted ? { reverted: refit.reverted } : {}), values: Object.fromEntries(c.added.map((n) => [n, refit.values?.[n]])) }) : null,
          ...(feats ? { features: feats } : {}),
        });
        if (j.accept) { best = accept(c.m); bestSheet = sheet ?? bestSheet; }
        if (!j.accept) { remember("build", best, c, j.reasons.join("; ")); verdict += " — the module was reverted to the fitted start"; }
      } else {
        verdict = "BUILD skipped: no missing feature has a READY call";
        log(`[loop] ${verdict}`);
      }
      if (atTarget(best, ctx.floor, ctx.band, { exact: ctx.exactStop })) stop("target");
    }

    // ---- LOOP
    let rejects = 0;
    let small = 0;
    for (let k = 1; !record.stop && k <= KK; k += 1) {
      if (deadline()) { stop(`time (${Math.round(timeLimitMs() / 60000)} min)`); break; }
      // V4-6 item 3: ABSORB — the harness re-FITs the knobs the shown rows name; only rows still open reach the seat
      const ab = await absorbRows(ctx, best, stepDir(k));
      const absorb = { knobs: ab.knobs, evals: ab.evals ?? 0, ms: ab.ms ?? 0, accepted: ab.accepted ?? false, skipped: ab.skipped ?? null, iou: ab.iou ?? null, verdict: ab.verdict ?? null, rows: ab.rows };
      log(`[loop] ${k}/${KK}: ABSORB ${ab.skipped ?? `${ab.accepted ? "kept" : "reverted"} (${ab.iou?.join(" -> ")}), ${ab.rows.filter((x) => x.absorbed).length}/${ab.rows.length} rows absorbed`}`);
      if (ab.accepted) {
        best = accept(ab.m);
        if (images) { try { bestSheet = await renderSheet(ctx, best.text, `${k}-absorb-${best.hash}`, path.join(stepDir(k), "absorb-sheet.png")); } catch (error) { log(`[loop] ${k}: absorb sheet refused — ${error.message}`); } }
        if (atTarget(best, ctx.floor, ctx.band, { exact: ctx.exactStop })) { stop("target"); steps.push({ step: `${k}-absorb`, iou: best.iou, accepted: true, absorb }); break; }
      }
      const ready = await missingReady(ctx, best);
      const prompt = await loopPrompt(ctx, best, { k, K: KK, verdict, ready, absorb });
      const promptBytes = assertPromptSize(prompt, `LOOP ${k}`);
      const s = await callSeat(prompt, imgs(), k);
      const c = await candidateFrom(best, s, k);
      const j = judge(c.m, best);
      verdict = `${j.accept ? "ACCEPTED" : "REJECTED"} — ${j.reasons.join("; ")}${j.accept ? "" : " — the module was reverted to the best one"}`;
      log(`[loop] ${k}/${KK}: ${verdict}`);
      const sheet = await archive(k, c.m, verdict, { accepted: j.accept, gain: j.gain, promptBytes, seatSeconds: r4((s.seconds ?? 0) + c.seconds), how: c.how, knobsAdded: c.added, zoneFixes: c.zoneFixes ?? [], absorb });
      if (j.accept) {
        best = accept(c.m);
        bestSheet = sheet ?? bestSheet;
        rejects = 0;
        small = j.gain < PLATEAU_GAIN ? small + 1 : 0;
        if (atTarget(best, ctx.floor, ctx.band, { exact: ctx.exactStop })) stop("target");
        else if (small >= 2) stop(`plateau (2 accepted gains < ${PLATEAU_GAIN})`);
      } else {
        remember(k, best, c, j.reasons.join("; "));
        rejects += 1;
        if (rejects >= 2) stop("2 consecutive rejects");
      }
      if (!record.stop && k === KK) stop(`K (${KK} loop steps)`);
    }
    if (!record.stop) stop(KK === 0 ? "K (0 loop steps)" : "K");
    exit = record.stop === "target" ? 0 : 1;
    }   // v4 / v5 path
  } catch (error) {
    if (error instanceof SeatTransportError) { record.stop = `seat transport: ${error.message}`; exit = 2; }
    else { record.stop = `error: ${error.message}`; exit = error.exitCode ?? 1; if (!best) { record.exitCode = exit; writeRecord(); throw error; } }
  }
  if (best) {
    placeModule(best.text, path.join(out, "best.mjs"));
    record.best = { accuracy: best.accuracy?.summary ?? null, iou: best.iou, zones: best.zones, zonesUnder: best.zoneRows.map((r) => r.family), pass: best.pass, codes: best.codes, coverage: `${best.coverage.have}/${best.coverage.total}`, tris: best.tris, target: atTarget(best, ctx.floor, ctx.band, { exact: ctx.exactStop }) };
    if (ctx.v6) Object.assign(record.best, ctx.v6.summary(best));
  }
  record.exitCode = exit;
  writeRecord();
  return record;
}

// ---------------------------------------------------------------------------

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject");
  const seat = arg("seat");
  if (!subjectId || !seat) {
    console.error("usage: node scripts/loop.mjs --subject <id> --seat <seat> [--from <module>] [--K 4] [--no-images] [--evals 300] [--out <dir>] [--work <dir>] [--no-exact] [--no-similarity] [--v5-detail on|off] [--no-v6]");
    return 3;
  }
  try {
    const r = await runLoop({
      subjectId, seat, from: arg("from"), K: Number(arg("K", 4)), images: !process.argv.includes("--no-images"),
      evals: Number(arg("evals", FIT_EVALS)), outDir: arg("out"), workDir: arg("work"), fitEnabled: !process.argv.includes("--no-fit"),
      exactStop: !process.argv.includes("--no-exact"), similarity: !process.argv.includes("--no-similarity"),
      ...(process.argv.includes("--no-features") ? { featureFit: false } : {}), ...(process.argv.includes("--no-face-palette") ? { facePalette: false } : {}),
      v5Detail: arg("v5-detail", "off") === "on", turnaround: !process.argv.includes("--no-v6"),
    });
    console.log(`[loop] ${r.stop}; accuracy ${r.best?.accuracy ?? "-"}; best IoU ${r.best?.iou} (gate ${r.best?.pass ? "PASS" : r.best?.codes?.join(",")}, coverage ${r.best?.coverage}); trace ${r.iouTrace.map((s) => `${s.step}:${s.iou}${s.accepted === false ? "x" : ""}`).join(" ")}; ${r.ms} ms`);
    return r.exitCode;
  } catch (error) {
    console.error(`loop: ${error.message}`);
    return error.exitCode ?? 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((code) => { process.exitCode = code; });   // no top-level await: scripts/v6/loop6.mjs imports this module back (V6-2)
}
