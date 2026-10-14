#!/usr/bin/env node
// turnaround.mjs — the setup's turnaround step (research/v7/IMAGEGEN-AB.md decision, RUNBOOK §0 step 1): ONE 2 x 2 sheet
// generated from the concept (scripts/v7/imagegen.mjs; Gemini by default, GPT the second generator), normalised like the
// live sets (normalize-views.mjs --like subjects/<s>/turnaround; a first set, no live side: --side-l 800 --canvas 1024), measured with hull.mjs (views vs views: viewOnly; views vs
// the concept: conceptOnlyBlob; the registration residuals); then the repair of the contradicted view, ONE view per call,
// kept only when the hull numbers improve. GPT / Gemini only generate images; every number and verdict here is the script's.
// The prompt = research/v7/TURNAROUND-PROMPT.md filled from subjects/<s>/turnaround/facts.json.
//
//   node scripts/v7/turnaround.mjs gen    --subject <s> --out <dir> [--gen gemini|gpt] [--attempts 1] [--add-sheet <png>
//                                         [--add-provenance <json>]] [--mirror <view,...>] [--keep-main <px>] [--concurrency 2]
//                                         [--rechoose] [--dry]
//   node scripts/v7/turnaround.mjs repair --subject <s> --dir <dir> --view <v> [--gen gemini|gpt] [--draft mirror|proportion] [--dry]
//   node scripts/v7/turnaround.mjs status --subject <s> --dir <dir> [--loo]
//   node scripts/v7/turnaround.mjs renorm --subject <s> --dir <dir> --attempt attempt-<k> [--mirror <view,...>] [--why <text>]
//   node scripts/v7/turnaround.mjs prompt --subject <s> [--view <v> --draft mirror|proportion]
//   node scripts/v7/turnaround.mjs install --subject <s> --dir <dir> [--force]   (swap-in, after `git mv` of the old set)
//   node scripts/v7/turnaround.mjs sheet  --subject <s>                            (rebuild subjects/<s>/turnaround/sheet.png)
//
// <dir> holds state.json, attempt-<k>/ (raw/sheet.png + provenance, the normalised views, normalize.json, hull.json / .png),
// current/ (the chosen attempt + the KEPT repairs) and repair-<n>-<view>-<gen>-<draft>/ (draft.png, prompt.txt, raw/, the
// candidate set, hull.json / .png).
// gen: attempts run in parallel (--concurrency); --add-sheet registers an existing raw sheet (e.g. the A/B's) as an
//   attempt. Each attempt: normalise (a view whose drawing bbox grows > 3 px by stray marks outside the main drawing —
//   labels — is re-normalised with --keep-main 10, noted), orientation check of side / top against the live views
//   (WARN only), hull. The chosen attempt = the lowest conceptOnlyBlob + worst viewOnly (score; ties: the earlier);
//   re-chosen on every gen unless a repair was KEPT (then only with --rechoose).
// repair: image 1 = the current view, image 2 = a draft: `mirror` (front <-> rear only: the other end view mirrored left
//   to right — keep this view's face details, match the mirrored OUTLINE) or `proportion` (the view stretched to the
//   facts.json dims on the registration's own spans: front / rear W / H, side L / H, top W / L). Default: mirror for
//   front / rear, proportion for side / top. The new view is normalised to the current set's targets (a side repair
//   re-normalises front / rear to the new side height), a COPY check against both references (fg IoU >= 0.985 and mean
//   |RGB diff| <= 6 on the union: the generator returned an input), then hull. KEEP only when that view's viewOnly drops
//   and conceptOnlyBlob does not rise (and it is no copy); else REVERT — current/ untouched. Which of front / rear to
//   repair is the caller's call: the one whose viewOnly blobs the concept contradicts (the concept shows the front face;
//   when unsure, the rear, to match the front); `status --loo` prints the evidence.
// SETUP STOP RULE (gold.config.json setupStop, 2026-09-28): after 3 failed whole-set regenerations (attempts that errored or
//   missed a target) or 3 failed repairs of one view, gen / that view's repair refuse (--owner-override "<the owner's
//   words>" records an explicit exception in state.json stopOverrides); status prints the rule's state; the setup audit
//   then rules target-wins (READY with drift rects / decided facts / audit.json acceptBlocks) instead of REGENERATE.
// status: the current set's hull + residual summary, the targets (every viewOnly <= 3 %, conceptOnlyBlob <= 2.5 %, no
//   residual BLOCK +-3 %), the history; --loo: per view, the concept px that view alone carves away (hull without it,
//   splatted at the same frame): "supported" = concept foreground it removes (it contradicts the concept there),
//   "unsupported" = volume it removes that the concept does not show (it is right there).
// install: current/ -> subjects/<s>/turnaround/ (views.json file names), views.json minus the per-view shift / scale /
//   drift / holes measured on the old images (+ `_note`), sheet.png rebuilt (concept, side, front, rear, top: 480 px tiles,
//   sharp lanczos3 — the old sheets' construction), README.md from state.json. Refuses while the old view images are still
//   there (`git mv` them to turnaround-1-gpt/ first) unless --force.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { conceptRegistration } from "./conceptreg.mjs";   // WF v10: = project.mjs subjectRegistration for a vehicle; the fixed-isometric fit for a direct class
import { OCCLUDED, SUBJECT, framed, readRGB as readTarget, targetState } from "../registered.mjs";
import { STYLE } from "../make-target.mjs";
import { styleText } from "./styles.mjs";
import { conceptPalette, familyTable, maskOptions, readImage, readJson, viewFamilyTable, viewsFile } from "../v6/ortho.mjs";
import { buildHull, conceptMap, hullReport, loadViewSet, reportLines, residualMax, splatHull, stripMeasured, writeHullPng } from "./hull.mjs";
import { conceptTarget, hexOf, parseArgs } from "./lib.mjs";
import { loadConfig, setupMisses, setupStopOf } from "./goldlib.mjs";
import { DOCTOR } from "./steplib.mjs";
import { bboxOf, drawingMask, normalizeView, readRGB } from "./normalize-views.mjs";
import { generateImage, geminiRefusal, GEN } from "./imagegen.mjs";

export const VIEWS = Object.freeze(["side", "front", "rear", "top"]);
export const TEMPLATE_FILE = path.join(ROOT, "research", "v7", "TURNAROUND-PROMPT.md");
export const ISO_SENTENCE = "Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical.";
/**
 * The setup gate's targets (fractions) and the set-level repair KEEP rule's numbers: scripts/v7/gold.config.json
 * setupHull (its warn levels — every view's viewOnly, conceptOnlyBlob, |aspect| per ratio — and `keep`; defaults, owner
 * ratification pending) + the doctor's residual band (steplib.mjs DOCTOR.band: no residual BLOCK).
 */
export function setupTargets(config = loadConfig()) {
  const h = config.setupHull ?? {};
  return Object.freeze({
    viewOnly: h.viewOnly?.warn ?? 0.03, conceptOnlyBlob: h.conceptOnlyBlob?.warn ?? 0.025, aspect: h.aspect?.warn ?? 0.03, residual: DOCTOR.band,
    keep: Object.freeze({ viewOnlyDrop: 0.003, conceptOnlyBlobRise: 0.0025, aspectGrow: 0.005, ...(h.keep ?? {}) }),
  });
}
export const TARGETS = setupTargets();
/** A generated view this close to one of its references is a copy of it (the A/B's Gemini per-view failure). */
export const COPY = Object.freeze({ iou: 0.985, diff: 6 });
export const KEEP_MAIN_PX = 10;
export const STRAY_PX = 3;
export const OTHER_END = Object.freeze({ front: "rear", rear: "front" });
const ASPECT = Object.freeze({ side: "16:9", top: "16:9", front: "1:1", rear: "1:1" });
const TODAY = () => new Date().toISOString().slice(0, 10);

const r4 = (v) => Math.round(v * 1e4) / 1e4;
const pct = (x, d = 2) => (x === null || x === undefined ? "-" : `${(x * 100).toFixed(d)} %`);
const sgn = (x, d = 1) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(d)} %`;
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };
const sha256 = (buf) => crypto.createHash("sha256").update(buf).digest("hex");
const shaFile = (f) => sha256(fs.readFileSync(f));
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

// ---------------------------------------------------------------------------------------------------------------------
// The prompt (pure)
// ---------------------------------------------------------------------------------------------------------------------

/** research/v7/TURNAROUND-PROMPT.md -> {sheet, repair, views: {side..top}, projection, drafts: {mirror, proportion}}. */
export function parseTemplates(md) {
  const blocks = {};
  let head = null; let buf = null;
  for (const line of String(md).split(/\r?\n/)) {
    if (buf) {
      if (line.trim() === "```") { if (head && !(head in blocks)) blocks[head] = buf.join("\n"); buf = null; } else buf.push(line);
      continue;
    }
    const h = /^##\s+(.+?)\s*$/.exec(line);
    if (h) { head = h[1]; continue; }
    if (line.trim() === "```text") buf = [];
  }
  for (const k of ["Sheet template", "Repair template", "View conventions", "Projection rules", "Draft sentences"]) {
    if (!blocks[k]) throw new Error(`turnaround: the template has no \`\`\`text block under "## ${k}"`);
  }
  const keyed = (txt, what, keys) => {
    const out = {};
    for (const l of txt.split("\n")) { if (!l.trim()) continue; const i = l.indexOf(":"); out[l.slice(0, i).trim()] = l.slice(i + 1).trim(); }
    for (const k of keys) if (!out[k]) throw new Error(`turnaround: "## ${what}" has no "${k}:" line`);
    return out;
  };
  return { sheet: blocks["Sheet template"].trim(), repair: blocks["Repair template"].trim(), views: keyed(blocks["View conventions"], "View conventions", VIEWS),
    projection: blocks["Projection rules"].trim(), drafts: keyed(blocks["Draft sentences"], "Draft sentences", ["mirror", "proportion"]) };
}
export const loadTemplates = (file = TEMPLATE_FILE) => parseTemplates(fs.readFileSync(file, "utf8"));

/** {name} / {a.b} placeholders from vars; a missing value or a surviving brace is an error. */
export function fillTemplate(tpl, vars) {
  const out = tpl.replace(/\{([A-Za-z]+(?:\.[A-Za-z]+)?)\}/g, (m, key) => {
    const v = key.split(".").reduce((o, k) => (o === null || o === undefined ? undefined : o[k]), vars);
    if (v === undefined || v === null || typeof v === "object") throw new Error(`turnaround: no value for {${key}}`);
    return String(v);
  });
  const left = /[{}]/.exec(out);
  if (left) throw new Error(`turnaround: a brace survives the fill near "${out.slice(Math.max(0, left.index - 30), left.index + 30)}"`);
  return out;
}

/** The frozen STYLE (scripts/make-target.mjs) with its isometric sentence replaced. */
export function styleOrtho(style = STYLE) {
  if (!style.startsWith(ISO_SENTENCE)) throw new Error("turnaround: scripts/make-target.mjs STYLE changed (its isometric sentence is not at the start)");
  return style.replace(ISO_SENTENCE, "True orthographic elevation, no perspective.");
}

/** facts.json sanity: the keys the templates need + the asymmetric entries. */
export function checkFacts(f) {
  const miss = ["noun", "description", "proportions", "sides"].filter((k) => typeof f?.[k] !== "string" || !f[k].trim());
  for (const v of VIEWS) if (typeof f?.shape?.[v] !== "string") miss.push(`shape.${v}`);
  for (const d of ["L", "W", "H"]) if (!(f?.dims?.[d] > 0)) miss.push(`dims.${d}`);
  if (miss.length) throw new Error(`turnaround: facts.json misses ${miss.join(", ")}`);
  for (const [i, a] of (f.asymmetric ?? []).entries()) {
    if (typeof a.part !== "string" || !["left", "right"].includes(a.flank) || ![undefined, null, "front", "middle", "rear"].includes(a.along)) {
      throw new Error(`turnaround: facts.json asymmetric[${i}] needs {part, flank: left | right, along?: front | middle | rear | null}`);
    }
  }
  return f;
}

/**
 * One asymmetric part in one view, as the IMAGE side it shows on (vehicle axes: the left flank is image RIGHT in the
 * front view, image LEFT in the rear view, image BOTTOM in the top view; the top view's front points LEFT).
 */
export function asymSentence(a, view, noun) {
  const Part = cap(a.part);
  const is = a.plural ? "are" : "is";
  const stick = a.plural ? "stick" : "sticks";
  const flank = a.flank;
  const endSide = a.along === "front" ? "LEFT" : a.along === "rear" ? "RIGHT" : null;   // side / top views: the front points left
  if (view === "side") {
    const at = endSide ? `, toward the ${endSide} end of the image` : "";
    if (flank === "right") return `${Part} ${is} on the far (right) side and not drawn in this view.`;
    return a.protrudes ? `${Part} ${is} on this flank (the ${noun}'s left)${at}.` : `${Part} ${is} on the near (left) side, visible in this view${at}.`;
  }
  const img = { front: { left: "RIGHT", right: "LEFT" }, rear: { left: "LEFT", right: "RIGHT" }, top: { left: "BOTTOM", right: "TOP" } }[view]?.[flank];
  if (!img) throw new Error(`turnaround: no view ${view}`);
  const other = { RIGHT: "LEFT", LEFT: "RIGHT", TOP: "BOTTOM", BOTTOM: "TOP" }[img];
  if (view === "top") {
    const end = endSide ? `, toward the ${endSide} end` : "";
    return a.protrudes
      ? `${Part} ${stick} out beyond the body outline at the ${img} of the image only${end} (the ${noun}'s ${flank} flank); nothing sticks out at the ${other}.`
      : `${Part} ${is} in the ${img === "BOTTOM" ? "lower" : "upper"} half of the plan${end} (the ${noun}'s ${flank} side), not in the ${img === "BOTTOM" ? "upper" : "lower"} half.`;
  }
  return a.protrudes
    ? `${Part} ${stick} out beyond the body outline on the ${img} of the image only (the ${noun}'s ${flank} flank); the ${other} side of the outline is plain.`
    : `${Part} ${is} on the ${img} half of the image (the ${noun}'s ${flank} side), not on the ${other} half.`;
}

/** The extra sentences of one view: facts.faces[view] + one asymSentence per asymmetric part ("" when none). */
export function viewExtra(facts, view) {
  const parts = [];
  if (facts.faces?.[view]?.trim()) parts.push(facts.faces[view].trim());
  for (const a of facts.asymmetric ?? []) parts.push(asymSentence(a, view, facts.noun));
  return parts.length ? ` ${parts.join(" ")}` : "";
}

function baseVars(T, facts) {
  checkFacts(facts);
  return {
    noun: facts.noun, description: facts.description.trim(), proportions: facts.proportions.trim(), sides: facts.sides.trim(),
    shape: facts.shape, extra: Object.fromEntries(VIEWS.map((v) => [v, viewExtra(facts, v)])),
    view: Object.fromEntries(VIEWS.map((v) => [v, fillTemplate(T.views[v], { noun: facts.noun })])),
    // the subject's concept style (facts.json `style`, scripts/v7/styles.json); absent = the frozen make-target.mjs STYLE
    projection: T.projection, style: styleOrtho(facts.style ? styleText(facts.style) : STYLE),
  };
}

/** The 2 x 2 sheet prompt. */
export const sheetPrompt = (T, facts) => fillTemplate(T.sheet, baseVars(T, facts));

/** The one-view repair prompt (image 1 = the current view, image 2 = the draft). */
export function repairPrompt(T, facts, view, draft) {
  if (!VIEWS.includes(view)) throw new Error(`turnaround: --view ${view} (${VIEWS.join(" | ")})`);
  if (!T.drafts[draft]) throw new Error(`turnaround: --draft ${draft} (mirror | proportion)`);
  const other = OTHER_END[view];
  if (draft === "mirror" && !other) throw new Error(`turnaround: a mirror draft exists only for front / rear, not ${view}`);
  const b = baseVars(T, facts);
  const d = fillTemplate(T.drafts[draft], { noun: facts.noun, VIEW: view.toUpperCase(), view, OTHER: (other ?? "").toUpperCase(), other: other ?? "" });
  return fillTemplate(T.repair, { ...b, VIEW: view.toUpperCase(), viewSentence: b.view[view], shape: facts.shape[view], extra: b.extra[view], draft: d });
}

export function readFacts(subject) {
  const f = path.join(ROOT, "subjects", subject, "turnaround", "facts.json");
  if (!fs.existsSync(f)) throw new Error(`turnaround: no ${rel(f)} (research/v7/TURNAROUND-PROMPT.md "facts.json")`);
  return checkFacts(JSON.parse(fs.readFileSync(f, "utf8")));
}

// ---------------------------------------------------------------------------------------------------------------------
// Numbers and verdicts (pure)
// ---------------------------------------------------------------------------------------------------------------------

/** hull report -> the numbers the loop decides on (fractions, rounded like the report). */
export function summarize(R) {
  const views = {};
  for (const [v, m] of Object.entries(R.views)) views[v] = { viewOnly: m.viewOnly, viewOnlyBlob: m.viewOnlyBlob, iou: m.iou };
  let worstView = null; let worstViewOnly = -1;
  for (const [v, m] of Object.entries(views)) if (m.viewOnly > worstViewOnly) { worstView = v; worstViewOnly = m.viewOnly; }
  const residuals = {};
  for (const D of ["W", "L", "H"]) {
    if (!R.residuals?.[D]) continue;
    residuals[D] = Object.fromEntries(Object.entries(R.residuals[D]).filter(([k]) => k !== "meanPx" && k !== "maxAbs"));
  }
  const C = R.concept;
  const A = C?.aniso ?? null;
  return {
    residualMax: r4(residualMax(R.residuals)), residuals,
    blocks: (R.doctor ?? []).filter((d) => d.level === "BLOCK").map((d) => `${d.id}${d.data ? ` ${Object.entries(d.data).map(([v, x]) => `${v} ${sgn(x)}`).join(", ")}` : ""}`),
    views, worstView, worstViewOnly,
    conceptIoU: C?.iou ?? null, conceptOnly: C?.conceptOnly ?? null, conceptOnlyBlob: C?.conceptOnlyBlob ?? null, conceptHullOnly: C?.hullOnly ?? null, frame: C?.frame?.fitted ?? null,
    aspect: R.aspect ?? null, aniso: A ? { scale: A.scale, params: A.params, iou: A.iou, conceptOnlyBlob: A.conceptOnlyBlob } : null,
    s: R.s, dims: R.dims,
  };
}

/** The (D, view) pairs of a summary's residuals outside the doctor's band: the residual BLOCKs, e.g. ["W rear", "W top"]. */
export function residualBlocks(sm, band = TARGETS.residual) {
  const out = [];
  for (const [D, per] of Object.entries(sm.residuals ?? {})) for (const [v, x] of Object.entries(per)) if (Math.abs(x) > band + 1e-9) out.push(`${D} ${v}`);
  return out;
}

/** The largest |aspect| ratio of a summary (0 without the aniso fit). */
export const aspectMax = (sm) => (sm.aspect ? Math.max(Math.abs(sm.aspect.HoverW), Math.abs(sm.aspect.LoverW)) : 0);

/** The attempt score: conceptOnlyBlob + the worst view's viewOnly (lower is better). */
export const score = (sm) => r4((sm.conceptOnlyBlob ?? 1) + sm.worstViewOnly);

/** Pick the attempt with the lowest score (ties: the first in the list). [{id, summary}] -> id | null */
export function chooseAttempt(attempts) {
  let best = null;
  for (const a of attempts) if (a.summary && (!best || score(a.summary) < score(best.summary))) best = a;
  return best?.id ?? null;
}

/** The setup gate's misses (empty = the targets are met): every viewOnly, conceptOnlyBlob, |aspect| per ratio, residuals
 * (goldlib.mjs setupMisses: gold.mjs counts the setup stop rule's failed sets with the same function). */
export function targetMisses(sm, T = TARGETS) {
  return setupMisses(sm, T);
}
/**
 * The setup stop rule (gold.config.json setupStop, goldlib.mjs setupStopOf): after `sets` failed whole-set regenerations
 * or `view` failed repairs of one view, gen / repair refuse (`--owner-override "<the owner's words>"` records an explicit
 * owner exception) and the setup audit rules target-wins instead of REGENERATE.
 */
export function stopRule(st, config = loadConfig()) {
  const L = config.setupStop ?? { sets: 3, view: 3 };
  return setupStopOf(st, { misses: (sm) => targetMisses(sm), sets: L.sets, view: L.view });
}
/** The refusal of a gen / repair under the stop rule (null = allowed). */
export function stopRefusal(stop, what, view = null) {
  if (what === "gen" && stop.setsSpent) return `gen refused by the setup stop rule: ${stop.why} — no more regeneration: the setup audit rules target-wins (READY with drift rects / decided facts / acceptBlocks); --owner-override "<the owner's words>" for an explicit exception`;
  if (what === "repair" && stop.spentViews.includes(view)) return `repair ${view} refused by the setup stop rule: ${stop.why} — no more regeneration of ${view}: the setup audit rules target-wins; --owner-override "<the owner's words>" for an explicit exception`;
  return null;
}
/** The set's registered L / W and H / W against facts.json dims (the same span measures): relative deviations (not a target). */
export function factsDeviation(dims, factsDims) {
  const out = {};
  for (const d of ["L", "H"]) if (dims?.[d] > 0 && dims?.W > 0 && factsDims?.[d] > 0 && factsDims?.W > 0) out[`${d}/W`] = r4((dims[d] / dims.W) / (factsDims[d] / factsDims.W) - 1);
  return out;
}
const devText = (sm, facts) => `proportions vs facts.json dims (not a target): ${Object.entries(factsDeviation(sm.dims, facts.dims)).map(([k, x]) => `${k} ${(sm.dims[k[0]] / sm.dims.W).toFixed(3)} vs ${(facts.dims[k[0]] / facts.dims.W).toFixed(3)} (${sgn(x)})`).join(", ")}`;

/**
 * KEEP / REVERT of a repair, judged on the WHOLE SET (the orchestrator's rule, 2026-09-28; numbers: TARGETS.keep): a copy of
 * a reference is never kept; KEEP when the repaired set meets every target (targetMisses empty); else KEEP only when ALL of
 * the set's worst viewOnly drops by >= keep.viewOnlyDrop, conceptOnlyBlob rises by <= keep.conceptOnlyBlobRise, no |aspect|
 * ratio grows by > keep.aspectGrow, and no residual BLOCK (D, view) appears that the set before did not have; otherwise
 * REVERT. -> {verdict, reasons, met}
 */
export function repairVerdict(before, after, view, { copyOf = null, T = TARGETS } = {}) {
  const reasons = [];
  if (copyOf) return { verdict: "REVERT", reasons: [`the generated view is a copy of ${copyOf}`], met: false };
  const met = targetMisses(after, T).length === 0;
  if (met) return { verdict: "KEEP", reasons: ["the repaired set meets every target"], met };
  const k = T.keep;
  const drop = before.worstViewOnly - after.worstViewOnly;
  if (!(drop >= k.viewOnlyDrop - 1e-9)) reasons.push(`worst viewOnly ${before.worstView} ${pct(before.worstViewOnly)} -> ${after.worstView} ${pct(after.worstViewOnly)} did not drop by >= ${(k.viewOnlyDrop * 100).toFixed(2)} pts`);
  const rise = after.conceptOnlyBlob - before.conceptOnlyBlob;
  if (rise > k.conceptOnlyBlobRise + 1e-9) reasons.push(`conceptOnlyBlob rose ${pct(before.conceptOnlyBlob)} -> ${pct(after.conceptOnlyBlob)} (> ${(k.conceptOnlyBlobRise * 100).toFixed(2)} pts)`);
  if (before.aspect && after.aspect) {
    for (const [key, name] of [["HoverW", "H/W"], ["LoverW", "L/W"]]) {
      const g = Math.abs(after.aspect[key]) - Math.abs(before.aspect[key]);
      if (g > k.aspectGrow + 1e-9) reasons.push(`|aspect ${name}| grew ${sgn(before.aspect[key])} -> ${sgn(after.aspect[key])} (> ${(k.aspectGrow * 100).toFixed(1)} pts)`);
    }
  } else if (!after.aspect) reasons.push("no aspect (the aniso fit did not run)");
  const had = new Set(residualBlocks(before, T.residual));
  const fresh = residualBlocks(after, T.residual).filter((x) => !had.has(x));
  if (fresh.length) reasons.push(`new residual BLOCK ${fresh.join(", ")}`);
  return { verdict: reasons.length ? "REVERT" : "KEEP", reasons: reasons.length ? reasons : ["the set improved: worst viewOnly, conceptOnlyBlob, aspect, residuals within the rule"], met };
}

/** One line: the whole set's numbers (for the before -> after print). */
export const setLine = (sm) => `worst viewOnly ${sm.worstView} ${pct(sm.worstViewOnly)} · conceptOnlyBlob ${pct(sm.conceptOnlyBlob)} · aspect H/W ${sm.aspect ? sgn(sm.aspect.HoverW) : "-"} L/W ${sm.aspect ? sgn(sm.aspect.LoverW) : "-"} · residual max ${pct(sm.residualMax, 1)}${residualBlocks(sm).length ? ` (BLOCK ${residualBlocks(sm).join(", ")})` : ""}`;

/**
 * The proportion draft's stretch of one view: the view's measured spans (registration: W / L = body-family spans, H =
 * the foreground bbox height; px) against facts.json dims. front / rear: x by (W / H)target / (W / H)now; side: x by
 * (L / H); top: y by (W / L). -> {kx, ky, now, target, what}
 */
export function proportionFactors(view, m, dims) {
  const f = (what, now, target, axis) => ({ kx: axis === "x" ? target / now : 1, ky: axis === "y" ? target / now : 1, now: r4(now), target: r4(target), what });
  if (view === "front" || view === "rear") return f("W / H", m.W / m.H, dims.W / dims.H, "x");
  if (view === "side") return f("L / H", m.L / m.H, dims.L / dims.H, "x");
  if (view === "top") return f("W / L", m.W / m.L, dims.W / dims.L, "y");
  throw new Error(`turnaround: no proportion draft for ${view}`);
}

/**
 * The proportion draft's target dims: the CONCEPT's proportions when the set's aspect is off (|H/W| or |L/W| above
 * T.aspect: the registered dims corrected by the aniso fit — H / (1 + aspect H/W), L / (1 + aspect L/W), W as registered),
 * else facts.json dims (the registration's own span measures either way). -> {dims, from}
 */
export function draftDims(sm, factsDims, T = TARGETS) {
  if (sm?.aspect && sm.dims && aspectMax(sm) > T.aspect + 1e-9) {
    return { dims: { W: sm.dims.W, H: sm.dims.H / (1 + sm.aspect.HoverW), L: sm.dims.L / (1 + sm.aspect.LoverW) }, from: `the concept's proportions (aniso aspect H/W ${sgn(sm.aspect.HoverW)} L/W ${sgn(sm.aspect.LoverW)})` };
  }
  return { dims: factsDims, from: "facts.json dims" };
}

/**
 * Where a stretched drawing lands: bbox (w, h) x (kx, ky), uniformly shrunk to fit a C px canvas with `margin` px (the
 * normaliser rescales anyway; only the aspect matters). -> {w, h, fit}
 */
export function stretchBox(w, h, kx, ky, C, margin = 8) {
  let W = w * kx; let H = h * ky; let fit = 1;
  const room = C - 2 * margin;
  if (W > room || H > room) { fit = Math.min(room / W, room / H); W *= fit; H *= fit; }
  return { w: Math.max(1, Math.round(W)), h: Math.max(1, Math.round(H)), fit: r4(fit) };
}

/** Mirror an RGB raster left to right. */
export function mirrorRGB({ data, width, height }) {
  const out = Buffer.alloc(data.length);
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const s = (y * width + x) * 3; const d = (y * width + (width - 1 - x)) * 3;
    out[d] = data[s]; out[d + 1] = data[s + 1]; out[d + 2] = data[s + 2];
  }
  return { data: out, width, height };
}

/** The registration's spans of one view (px): {W, L, H} as proportionFactors reads them. */
export function viewMeasures(reg, view) {
  const V = reg.views[view];
  const span = (s) => s[1] - s[0];
  const H = V.box.y1 - V.box.y0;
  if (view === "front" || view === "rear") return { W: span(V.body.x), H };
  if (view === "side") return { L: span(V.body.x), H };
  return { L: span(V.body.x), W: span(V.body.y) };
}

/** views.json for a regenerated set: the per-view keys measured on the old images dropped, a dated `_note`. */
export function regeneratedSpec(spec, note) {
  const { dropped } = stripMeasured(spec);
  const out = JSON.parse(JSON.stringify(spec));
  for (const [name, v] of Object.entries(out.views)) for (const k of Object.keys(v)) if (["shift", "scale", "_shift", "_scale"].includes(k)) delete v[k];
  if (out.families?.holes) {
    for (const k of Object.keys(out.families.holes)) if (out.views[k]) delete out.families.holes[k];
    if (!Object.keys(out.families.holes).length) delete out.families.holes;
  }
  if (out.drift) {
    for (const k of Object.keys(out.drift)) if (out.views[k]) delete out.drift[k];
    if (!Object.keys(out.drift).some((k) => Array.isArray(out.drift[k]))) delete out.drift;
  }
  const text = `${note} Dropped (measured on the previous images): ${dropped.length ? dropped.join(", ") : "none present"}.`;
  const ordered = {};
  for (const [k, v] of Object.entries(out)) { ordered[k] = v; if (k === "_comment") ordered._note = text; }
  if (!("_note" in ordered)) return { spec: { _note: text, ...out }, dropped };
  return { spec: ordered, dropped };
}

// ---------------------------------------------------------------------------------------------------------------------
// Per-view colour families (families; views.json families.viewTable, scripts/v6/README.md)
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The per-view family proposal's numbers: clusters = 5-bit colour bins grown greedily from the most frequent within
 * `radius` RGB, kept from `minShare` of the view's foreground; `major` clusters (>= 1 %) set the offset and the table;
 * the offset = the share-weighted per-channel median of (cluster - nearest anchor) over the major clusters within
 * `inlier`, capped at `maxOffset` (Euclidean) — a generator draws a whole view a little lighter / darker, never across
 * two families (hopper and body green are ~23 apart on the garbage truck); a major cluster is AMBIGUOUS when its runner-up
 * family is within `gap` RGB or `ratio` x its distance, FAR (left out of the table) beyond `far`.
 */
export const FAMILIES = Object.freeze({ radius: 18, minShare: 0.002, major: 0.01, inlier: 25, maxOffset: 20, far: 40, gap: 12, ratio: 0.75 });

const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const hexRound = (c) => hexOf(c.map((v) => Math.max(0, Math.min(255, Math.round(v)))));

/** Colour clusters of an image's foreground (fam != 0): -> {fg, clusters: [{rgb, n, share}]} by share. */
export function colourClusters(data, channels, fam, { radius = FAMILIES.radius, minShare = FAMILIES.minShare } = {}) {
  const bins = new Map();
  let fg = 0;
  for (let i = 0, j = 0; i < fam.length; i += 1, j += channels) {
    if (!fam[i]) continue;
    fg += 1;
    const r = data[j], g = data[j + 1], b = data[j + 2];
    const k = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3);
    let e = bins.get(k);
    if (!e) { e = [0, 0, 0, 0]; bins.set(k, e); }
    e[0] += 1; e[1] += r; e[2] += g; e[3] += b;
  }
  const list = [...bins.entries()].map(([k, e]) => ({ k, n: e[0], c: [e[1] / e[0], e[2] / e[0], e[3] / e[0]] })).sort((a, b) => b.n - a.n || a.k - b.k);
  const used = new Uint8Array(list.length);
  const out = [];
  for (let i = 0; i < list.length; i += 1) {
    if (used[i]) continue;
    const seed = list[i].c;
    let n = 0;
    const sum = [0, 0, 0];
    for (let j = i; j < list.length; j += 1) {
      if (used[j] || dist(list[j].c, seed) > radius) continue;
      used[j] = 1; n += list[j].n;
      for (let c = 0; c < 3; c += 1) sum[c] += list[j].c[c] * list[j].n;
    }
    if (fg && n / fg >= minShare) out.push({ rgb: sum.map((v) => v / n), n, share: n / fg });
  }
  return { fg, clusters: out.sort((a, b) => b.share - a.share) };
}

/** Share-weighted median of values [{v, w}]. */
function wmedian(items) {
  const s = [...items].sort((a, b) => a.v - b.v);
  const half = s.reduce((a, x) => a + x.w, 0) / 2;
  let acc = 0;
  for (const x of s) { acc += x.w; if (acc >= half) return x.v; }
  return 0;
}

/**
 * Match clusters to the table's families with ONE per-view colour offset (FAMILIES): each cluster -> the family of its
 * nearest (anchor + offset) and the runner-up family. -> {offset, rows: [{rgb, share, family, d, family2, d2, major,
 * ambiguous, far}]}
 */
export function matchClusters(clusters, table, o = FAMILIES) {
  const anchors = [];
  for (let f = 1; f < table.other; f += 1) for (const a of table.rgb[f]) anchors.push({ f, a });
  const nearest = (c, off) => {
    let best = null, second = null;
    for (const { f, a } of anchors) {
      const d = dist(c, [a[0] + off[0], a[1] + off[1], a[2] + off[2]]);
      if (!best || d < best.d) { if (best && best.f !== f) second = best; best = { f, d, a }; } else if (f !== best.f && (!second || d < second.d)) second = { f, d, a };
    }
    return { best, second };
  };
  let off = [0, 0, 0];
  for (let it = 0; it < 3; it += 1) {
    const inl = clusters.filter((c) => c.share >= o.major).map((c) => ({ c, m: nearest(c.rgb, off) })).filter((x) => x.m.best.d <= o.inlier);
    if (!inl.length) break;
    let next = [0, 1, 2].map((k) => wmedian(inl.map((x) => ({ v: x.c.rgb[k] - x.m.best.a[k], w: x.c.share }))));
    const len = Math.hypot(...next);
    if (len > o.maxOffset) next = next.map((v) => (v * o.maxOffset) / len);
    if (dist(next, off) < 0.05) { off = next; break; }
    off = next;
  }
  const rows = clusters.map((c) => {
    const { best, second } = nearest(c.rgb, off);
    const major = c.share >= o.major;
    const far = major && best.d > o.far;
    const ambiguous = major && !far && !!second && (second.d - best.d < o.gap || best.d > o.ratio * second.d);
    return { rgb: c.rgb, share: c.share, family: table.names[best.f], d: best.d, family2: second ? table.names[second.f] : null, d2: second?.d ?? null, major, ambiguous, far };
  });
  return { offset: off, rows };
}

/**
 * The per-view table: every family's colours moved by the view's offset, plus the view's own colour of each major cluster
 * that matches its family UNAMBIGUOUSLY within `inlier` (an ambiguous or far cluster is only reported: a human decides).
 * Every family keeps its moved anchors: the thin outline / anti-alias px classify as with the table (first version of
 * this pass replaced the lists by the clusters alone — the garbage truck's grey outlines turned body in the top view and
 * its body span grew from the refuse body to the bumpers, L residual -1.3 -> -14.1 %). -> {family: [hex, ...]}
 */
export function proposalTable(rows, table, offset = [0, 0, 0], o = FAMILIES) {
  const out = {};
  for (let f = 1; f < table.other; f += 1) out[table.names[f]] = table.rgb[f].map((a) => hexRound([a[0] + offset[0], a[1] + offset[1], a[2] + offset[2]]));
  for (const r of rows) {
    if (!r.major || r.ambiguous || r.far || r.d > o.inlier) continue;
    const list = out[r.family];
    const hx = hexRound(r.rgb);
    const c = hx.match(/[0-9a-f]{2}/g).map((x) => parseInt(x, 16));
    if (list.every((h) => dist(h.match(/[0-9a-f]{2}/g).map((x) => parseInt(x, 16)), c) > 3)) list.push(hx);
  }
  return out;
}

/** Per family (the table's names, bg / other excluded) its share of the foreground of a family-id raster. */
function familyShares(fam, table) {
  const cnt = new Float64Array(table.names.length);
  let fg = 0;
  for (let i = 0; i < fam.length; i += 1) if (fam[i]) { fg += 1; cnt[fam[i]] += 1; }
  return Object.fromEntries(table.names.slice(1).map((n, i) => [n, fg ? r4(cnt[i + 1] / fg) : 0]));
}

/**
 * The per-view family proposal of a view set (the live turnaround, or `dir`: the views.json file names read there): per
 * view the colour clusters matched to the concept's families (matchClusters), the proposed table, the family shares with
 * the subject's table (before) and with the proposal (after), and the concept's shares. `holes` only for the live images.
 */
export async function familyProposal(subject, { dir = null } = {}) {
  const spec = readJson(viewsFile(subject));
  const S = loadSubject(subject);
  const table = familyTable(spec.families?.table ? [] : await conceptPalette(S), spec.families ?? {});
  const live = path.join(ROOT, "subjects", subject, "turnaround");
  const tdir = dir ? path.resolve(dir) : live;
  const isLive = path.resolve(tdir) === path.resolve(live);
  const cimg = await readImage(S.paths.target, table, maskOptions(table, "concept"));
  const out = { subject, dir: rel(tdir), at: new Date().toISOString(), families: table.names.slice(1, -1), numbers: FAMILIES, concept: { shares: familyShares(cimg.fam, table) }, views: {}, viewTable: {} };
  for (const [v, vs] of Object.entries(spec.views)) {
    const file = path.join(tdir, vs.file);
    const mo = isLive ? maskOptions(table, v) : { enclosedFg: !!table.enclosedFg, holes: null };
    const img = await readImage(file, table, mo);
    const { fg, clusters } = colourClusters(img.data, img.c, img.fam);
    const m = matchClusters(clusters, table);
    const vt = proposalTable(m.rows, table, m.offset);
    const after = await readImage(file, viewFamilyTable(table, { viewTable: { [v]: vt } }, v), mo);
    out.views[v] = {
      file: rel(file), fg, offset: m.offset.map((x) => +x.toFixed(1)),
      clusters: m.rows.filter((r) => r.major).map((r) => ({ hex: hexRound(r.rgb), share: r4(r.share), family: r.family, d: +r.d.toFixed(1), family2: r.family2, d2: r.d2 === null ? null : +r.d2.toFixed(1), ...(r.ambiguous ? { ambiguous: true } : {}), ...(r.far ? { far: true } : {}) })),
      table: vt, shares: { before: familyShares(img.fam, table), after: familyShares(after.fam, table) },
    };
    out.viewTable[v] = vt;
  }
  return out;
}

/** The [start, end) of the value of a top-level key in a JSON text (string-aware), or null. */
export function jsonValueSpan(text, key) {
  let depth = 0, i = 0;
  const n = text.length;
  const skipString = (j) => { j += 1; while (j < n && text[j] !== '"') j += text[j] === "\\" ? 2 : 1; return j + 1; };
  while (i < n) {
    const ch = text[i];
    if (ch === '"') {
      const end = skipString(i);
      if (depth === 1 && text.slice(i + 1, end - 1) === key) {
        let j = end;
        while (/\s/.test(text[j])) j += 1;
        if (text[j] !== ":") { i = end; continue; }
        j += 1;
        while (/\s/.test(text[j])) j += 1;
        const s = j;
        if (text[j] === '"') return [s, skipString(j)];
        if (text[j] === "{" || text[j] === "[") {
          let d = 0;
          while (j < n) {
            const c = text[j];
            if (c === '"') { j = skipString(j); continue; }
            if (c === "{" || c === "[") d += 1;
            else if (c === "}" || c === "]") { d -= 1; if (d === 0) return [s, j + 1]; }
            j += 1;
          }
          return null;
        }
        while (j < n && !/[,}\s]/.test(text[j])) j += 1;
        return [s, j];
      }
      i = end;
      continue;
    }
    if (ch === "{" || ch === "[") depth += 1;
    else if (ch === "}" || ch === "]") depth -= 1;
    i += 1;
  }
  return null;
}

const inline = (v) => (v && typeof v === "object" && !Array.isArray(v)
  ? `{ ${Object.entries(v).map(([k, x]) => `${JSON.stringify(k)}: ${inline(x)}`).join(", ")} }`
  : Array.isArray(v) ? `[${v.map(inline).join(", ")}]` : JSON.stringify(v));

/** A views.json `families` object as text: one key per line; object values one entry per line, entries inline. */
export function familiesText(fam, ind = "  ") {
  const i1 = `${ind}  `, i2 = `${ind}    `;
  const lines = Object.entries(fam).map(([k, v]) => (v && typeof v === "object" && !Array.isArray(v)
    ? `${i1}${JSON.stringify(k)}: {\n${Object.entries(v).map(([kk, x]) => `${i2}${JSON.stringify(kk)}: ${inline(x)}`).join(",\n")}\n${i1}}`
    : `${i1}${JSON.stringify(k)}: ${inline(v)}`));
  return `{\n${lines.join(",\n")}\n${ind}}`;
}

/** views.json text with its `families` object replaced by `fam` (the rest of the file byte-identical). */
export function withFamilies(text, fam) {
  const span = jsonValueSpan(text, "families");
  if (!span) throw new Error("turnaround: views.json has no top-level \"families\" object");
  const lineStart = text.lastIndexOf("\n", span[0]) + 1;
  const ind = /^\s*/.exec(text.slice(lineStart, span[0]))[0];
  const out = `${text.slice(0, span[0])}${familiesText(fam, ind)}${text.slice(span[1])}`;
  JSON.parse(out);
  return out;
}

/** Report lines of a proposal: per view the offset, per family before -> after share vs the concept's, the flags. */
export function proposalLines(P) {
  const L = [];
  const p1 = (x) => `${(x * 100).toFixed(1)} %`;
  for (const [v, V] of Object.entries(P.views)) {
    const amb = V.clusters.filter((c) => c.ambiguous), far = V.clusters.filter((c) => c.far);
    L.push(`${v}: offset ${V.offset.map((x) => `${x >= 0 ? "+" : ""}${x}`).join(" ")} · ${V.clusters.length} major clusters${amb.length ? ` · ${amb.length} AMBIGUOUS` : ""}${far.length ? ` · ${far.length} FAR (left out)` : ""}`);
    for (const fam of P.families) {
      const b = V.shares.before[fam] ?? 0, a = V.shares.after[fam] ?? 0, c = P.concept.shares[fam] ?? 0;
      if (!b && !a && !c) continue;
      L.push(`  ${fam.padEnd(8)} ${p1(b).padStart(7)} -> ${p1(a).padStart(7)} (concept ${p1(c)})${V.table[fam] ? ` · ${V.table[fam].join(" ")}` : " · (the table's colours)"}`);
    }
    const o = (V.shares.after.other ?? 0);
    if (o || V.shares.before.other) L.push(`  other    ${p1(V.shares.before.other ?? 0).padStart(7)} -> ${p1(o).padStart(7)}`);
    for (const c of amb) L.push(`  AMBIGUOUS ${c.hex} ${p1(c.share)}: ${c.family} ${c.d} vs ${c.family2} ${c.d2} (after the offset) — check it, set viewTable.${v} by hand if the runner-up is right`);
    for (const c of far) L.push(`  FAR ${c.hex} ${p1(c.share)}: nearest ${c.family} ${c.d} > ${FAMILIES.far} — left out (its px take the nearest listed colour)`);
  }
  return L;
}

// ---------------------------------------------------------------------------------------------------------------------
// Sets on disk: normalise, measure
// ---------------------------------------------------------------------------------------------------------------------

function runNode(args) {
  const r = spawnSync(process.execPath, args, { cwd: ROOT, encoding: "utf8", maxBuffer: 64 << 20 });
  return { status: r.status, out: `${r.stdout || ""}${r.stderr || ""}`.trim() };
}

/** Views whose drawing bbox grows > STRAY_PX by marks outside the main drawing (labels): {view: px}. */
async function strayMarks(dir, views = VIEWS) {
  const out = {};
  for (const v of views) {
    const f = path.join(dir, `${v}.png`);
    if (!fs.existsSync(f)) continue;
    const img = await readRGB(f);
    const a = bboxOf(drawingMask(img).mask, img.width, img.height);
    const b = bboxOf(drawingMask(img, { keepMain: KEEP_MAIN_PX }).mask, img.width, img.height);
    if (!a || !b) continue;
    const d = Math.max(Math.abs(a.x0 - b.x0), Math.abs(a.y0 - b.y0), Math.abs(a.x1 - b.x1), Math.abs(a.y1 - b.y1));
    if (d > STRAY_PX) out[v] = d;
  }
  return out;
}

/** normalize-views.mjs --sheet on one raw sheet (+ the stray-mark re-run). -> {command, output, notes} */
/**
 * normalize-views.mjs's size arguments: `--like subjects/<s>/turnaround` when a live side view exists (views.json
 * views.side.file, else side.png), else — a new subject's first set — `--side-l 800 --canvas 1024` (the live sets' rule).
 */
export function likeArgs(subject, root = ROOT) {
  const tdir = path.join(root, "subjects", subject, "turnaround");
  let side = "side.png";
  try { side = JSON.parse(fs.readFileSync(path.join(tdir, "views.json"), "utf8")).views?.side?.file ?? side; } catch { /* no views.json */ }
  return fs.existsSync(path.join(tdir, side)) ? ["--like", `subjects/${subject}/turnaround`] : ["--side-l", "800", "--canvas", "1024"];
}

async function normalizeSheet(subject, sheet, dir, { mirror = [], keepMain = null } = {}) {
  const base = ["scripts/v7/normalize-views.mjs", "--sheet", rel(sheet), "--out", rel(dir), ...likeArgs(subject)];
  if (mirror.length) base.push("--mirror", mirror.join(","));
  let args = keepMain ? [...base, "--keep-main", String(keepMain)] : base;
  let r = runNode(args);
  if (r.status !== 0) throw new Error(`normalize-views failed: ${r.out}`);
  const notes = [];
  if (!keepMain) {
    const stray = await strayMarks(dir);
    if (Object.keys(stray).length) {
      notes.push(`stray marks outside the drawing (labels) grew the bbox of ${Object.entries(stray).map(([v, d]) => `${v} by ${d} px`).join(", ")}: re-normalised with --keep-main ${KEEP_MAIN_PX}`);
      args = [...base, "--keep-main", String(KEEP_MAIN_PX)];
      r = runNode(args);
      if (r.status !== 0) throw new Error(`normalize-views failed: ${r.out}`);
    }
  }
  return { command: `node ${args.join(" ")}`, output: r.out, notes };
}

/** Foreground IoU + mean |RGB diff| over the union of two same-size renders (the copy check; fgMax = the subject's
 *  views.json families.fgMax, so a near-white body counts as foreground). */
async function similarity(fileA, fileB, fgMax = 235) {
  const A = await readRGB(fileA); const B = await readRGB(fileB);
  if (A.width !== B.width || A.height !== B.height) return { iou: 0, diff: 255 };
  const ma = drawingMask(A, { fgMax }).mask; const mb = drawingMask(B, { fgMax }).mask;
  let inter = 0; let uni = 0; let diff = 0;
  for (let i = 0; i < ma.length; i += 1) {
    if (!ma[i] && !mb[i]) continue;
    uni += 1; if (ma[i] && mb[i]) inter += 1;
    const p = i * 3;
    diff += (Math.abs(A.data[p] - B.data[p]) + Math.abs(A.data[p + 1] - B.data[p + 1]) + Math.abs(A.data[p + 2] - B.data[p + 2])) / 3;
  }
  return { iou: uni ? r4(inter / uni) : 1, diff: uni ? Math.round((diff / uni) * 10) / 10 : 0 };
}
const isCopy = (sim) => sim.iou >= COPY.iou && sim.diff <= COPY.diff;

/** Orientation of side / top against the live views (fg IoU as is vs mirrored / flipped): WARN lines only. */
async function orientationWarnings(subject, dir) {
  const live = path.join(ROOT, "subjects", subject, "turnaround");
  const spec = readJson(viewsFile(subject));
  const warns = [];
  for (const v of ["side", "top"]) {
    const a = path.join(dir, `${v}.png`); const b = path.join(live, spec.views[v]?.file ?? `${v}.png`);
    if (!fs.existsSync(a) || !fs.existsSync(b)) continue;
    const A = await readRGB(a); const B = await readRGB(b);
    if (A.width !== B.width || A.height !== B.height) continue;
    const ma = drawingMask(A).mask; const mb = drawingMask(B).mask;
    const W = A.width; const H = A.height;
    const iouOf = (map) => { let i = 0; let u = 0; for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) { const p = ma[map(x, y)]; const q = mb[y * W + x]; if (p || q) { u += 1; if (p && q) i += 1; } } return u ? i / u : 0; };
    const cand = { as: iouOf((x, y) => y * W + x), mirrored: iouOf((x, y) => y * W + (W - 1 - x)) };
    if (v === "top") cand.flipped = iouOf((x, y) => (H - 1 - y) * W + x);
    const best = Object.entries(cand).sort((p, q) => q[1] - p[1])[0];
    if (best[0] !== "as" && best[1] > cand.as + 0.03) warns.push(`${v} looks ${best[0]} against the live ${v} (fg IoU ${cand.as.toFixed(3)} as drawn vs ${best[1].toFixed(3)} ${best[0]}): check the orientation, re-normalise with --mirror if it is a pure mirror`);
  }
  return warns;
}

const conceptCache = new Map();
async function conceptOf(subject) {
  if (!conceptCache.has(subject)) {
    const spec = readJson(viewsFile(subject));
    const live = path.join(ROOT, "subjects", subject, "turnaround");
    let img, T;
    if (Object.values(spec.views).every((v) => fs.existsSync(path.join(live, v.file)))) ({ img, T } = await conceptTarget(subject));
    else {
      // a new subject's first set (no live views yet): the concept target from views.json's mask rule alone — the table
      // loadTurnaround would build (it never depends on the view images)
      const S = loadSubject(subject);
      const table = familyTable(spec.families?.table ? [] : await conceptPalette(S), spec.families ?? {});
      img = await readTarget(S.paths.target);
      T = targetState(S, img, table.fgMax, maskOptions(table, "concept"));
    }
    let creg;
    try { creg = conceptRegistration(subject); } catch (e) {
      throw new Error(`${e.message} — a new subject: node scripts/v7/hull.mjs --subject ${subject} --write-frame --from facts (a provisional frame from facts.json dims; --from hull after install)`);
    }
    conceptCache.set(subject, { T, creg, w: img.w, h: img.h });
  }
  return conceptCache.get(subject);
}

/**
 * hull.mjs on a set folder (views.json names read there, measured keys ignored; when views.json carries
 * families.viewTable, the per-view families re-derived for THESE images by familyProposal) + the aniso fit (`anisoFrom`:
 * a warm start, e.g. the set before a repair) -> {report, summary, reg, hull, families}.
 */
export async function measureSet(subject, dir, { json = null, png = null, title = null, anisoFrom = null } = {}) {
  const spec = readJson(viewsFile(subject));
  const families = spec.families?.viewTable ? await familyProposal(subject, { dir }) : null;
  const set = await loadViewSet(subject, { viewsDir: path.resolve(dir), viewTable: families?.viewTable ?? null });
  const concept = await conceptOf(subject);
  const { report, rasters, hull } = await hullReport({ reg: set.reg, concept, aniso: anisoFrom ? { from: anisoFrom } : true });
  report.notes.unshift(...set.notes);
  if (families) {
    report.families = {
      offsets: Object.fromEntries(Object.entries(families.views).map(([v, V]) => [v, V.offset])), viewTable: families.viewTable,
      ambiguous: Object.entries(families.views).flatMap(([v, V]) => V.clusters.filter((c) => c.ambiguous).map((c) => `${v} ${c.hex} ${c.family}/${c.family2}`)),
    };
  }
  if (json) fs.writeFileSync(json, `${JSON.stringify({ subject, set: set.set, at: new Date().toISOString(), ...report }, null, 2)}\n`);
  if (png) await writeHullPng(png, title ?? `hull · ${subject} · ${set.set} · grey agree, blue image-only, red hull-only`, rasters, report);
  return { report, summary: summarize(report), reg: set.reg, hull, families };
}

/** Per view u: the concept px the hull gains without u, at the full set's fitted frame (see the header, status --loo). */
async function looRows(subject, m) {
  const concept = await conceptOf(subject);
  const { T, creg, w: W, h: H } = concept;
  const frame = m.report.concept.frame.fitted;
  const map = conceptMap(framed(creg, frame));
  const base = splatHull(m.hull, map, W, H);
  let fgPx = 0;
  for (let i = 0; i < T.length; i += 1) if (T[i] === SUBJECT) fgPx += 1;
  const rows = [];
  for (const u of m.reg.names) {
    const Hu = buildHull({ ...m.reg, names: m.reg.names.filter((n) => n !== u) });
    const mu = splatHull(Hu, map, W, H);
    let sup = 0; let uns = 0;
    for (let i = 0; i < mu.length; i += 1) {
      if (!mu[i] || base[i]) continue;
      if (T[i] === SUBJECT) sup += 1; else if (T[i] !== OCCLUDED) uns += 1;
    }
    rows.push({ view: u, supported: r4(sup / fgPx), unsupported: r4(uns / fgPx) });
  }
  return rows;
}

// ---------------------------------------------------------------------------------------------------------------------
// state.json
// ---------------------------------------------------------------------------------------------------------------------

const statePath = (dir) => path.join(dir, "state.json");
function readState(dir, subject) {
  const f = statePath(dir);
  if (!fs.existsSync(f)) return { subject, created: new Date().toISOString(), tool: "scripts/v7/turnaround.mjs", attempts: [], chosen: null, repairs: [], current: null };
  const st = JSON.parse(fs.readFileSync(f, "utf8"));
  if (subject && st.subject !== subject) throw new Error(`turnaround: ${rel(f)} is for ${st.subject}, not ${subject}`);
  return st;
}
function writeState(dir, st) { st.updated = new Date().toISOString(); fs.writeFileSync(statePath(dir), `${JSON.stringify(st, null, 2)}\n`); }

/** Copy a set's view images (+ aliases) and normalize.json. */
function copySet(from, to, { views = VIEWS, extras = ["normalize.json"] } = {}) {
  fs.mkdirSync(to, { recursive: true });
  const nj = path.join(from, "normalize.json");
  const aliases = fs.existsSync(nj) ? Object.fromEntries(Object.entries(JSON.parse(fs.readFileSync(nj, "utf8")).views ?? {}).map(([v, x]) => [v, x.alias])) : {};
  for (const v of views) {
    for (const name of [`${v}.png`, aliases[v]].filter(Boolean)) if (fs.existsSync(path.join(from, name))) fs.copyFileSync(path.join(from, name), path.join(to, name));
  }
  for (const e of extras) if (fs.existsSync(path.join(from, e))) fs.copyFileSync(path.join(from, e), path.join(to, e));
}

const line = (sm) => `resid ${pct(sm.residualMax, 1)} · viewOnly ${VIEWS.map((v) => (sm.views[v] ? (sm.views[v].viewOnly * 100).toFixed(2) : "-")).join(" / ")} % · cOnlyBlob ${pct(sm.conceptOnlyBlob)} · IoU ${sm.conceptIoU?.toFixed(3)}${sm.aspect ? ` · aspect H/W ${sgn(sm.aspect.HoverW)} L/W ${sgn(sm.aspect.LoverW)}` : ""}`;

function attemptTable(st, log) {
  log("[turnaround] attempt     source            resid    side   front    rear     top   cOnlyBlob  score");
  for (const a of st.attempts) {
    if (!a.summary) { log(`[turnaround] ${a.id.padEnd(11)} ${String(a.source).slice(0, 16).padEnd(16)}  FAILED ${a.error ?? ""}`); continue; }
    const s = a.summary;
    const vo = VIEWS.map((v) => `${(s.views[v].viewOnly * 100).toFixed(2).padStart(6)}`).join("  ");
    log(`[turnaround] ${a.id.padEnd(11)} ${String(a.source).slice(0, 16).padEnd(16)} ${pct(s.residualMax, 1).padStart(7)}  ${vo}  ${pct(s.conceptOnlyBlob).padStart(8)}  ${(score(s) * 100).toFixed(2).padStart(6)}${st.chosen === a.id ? "  <- chosen" : ""}`);
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------------------------------------------------

async function pool(items, n, fn) {
  const out = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.max(1, Math.min(n, items.length)) }, async () => {
    while (next < items.length) { const i = next; next += 1; out[i] = await fn(items[i], i); }
  }));
  return out;
}

/** An A/B provenance.json (calls[]) -> the call whose raw file is this sheet; any other JSON as is. */
function importedProvenance(file, sheet) {
  if (!file || !fs.existsSync(file)) return null;
  const j = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!Array.isArray(j.calls)) return j;
  const c = j.calls.find((x) => x.raw?.file && path.resolve(ROOT, x.raw.file) === path.resolve(sheet));
  return c ? { from: rel(file), call: c, generators: j.generators ?? null } : { from: rel(file), note: "no call of that provenance names this sheet" };
}

async function cmdGen(a, log) {
  const s = a.subject; const out = path.resolve(a.out);
  const gen = a.gen ?? "gpt";   // owner 2026-10-04: GPT is the default generator; gemini only with --allow-gemini
  if (!GEN[gen]) throw new Error(`--gen ${gen} (gpt | gemini)`);
  if (!a.dry && geminiRefusal(gen, !!a["allow-gemini"])) throw new Error(geminiRefusal(gen, !!a["allow-gemini"]));
  const T = loadTemplates(); const facts = readFacts(s);
  const prompt = sheetPrompt(T, facts);
  if (a.dry) { log(prompt); return 0; }
  const S = loadSubject(s);
  const concept = S.paths.target;
  fs.mkdirSync(out, { recursive: true });
  const st = readState(out, s);
  st.concept ??= { file: rel(concept), sha256: shaFile(concept) };
  if (st.concept.sha256 !== shaFile(concept)) log(`[turnaround] WARN the concept changed since this dir was started (${st.concept.file} -> ${rel(concept)})`);
  const mirror = typeof a.mirror === "string" ? a.mirror.split(",").map((x) => x.trim()).filter(Boolean) : [];
  const keepMain = a["keep-main"] && a["keep-main"] !== true ? Number(a["keep-main"]) : null;
  const adds = [].concat(a["add-sheet"] ?? []).filter((x) => x && x !== true);
  const n = a.attempts === undefined ? 1 : Number(a.attempts);
  let k = Math.max(-1, ...st.attempts.map((x) => Number(x.id.split("-")[1]))) + 1;
  const jobs = [...adds.map((f) => ({ kind: "import", sheet: path.resolve(f), id: `attempt-${k++}` })), ...Array.from({ length: n }, () => ({ kind: "gen", id: `attempt-${k++}` }))];
  if (!jobs.length) throw new Error("gen: nothing to do (--attempts 0 and no --add-sheet)");
  if (n > 0) stopGate(st, a, "gen", null, log);
  log(`[turnaround] ${s}: ${jobs.map((j) => `${j.id} ${j.kind === "gen" ? gen : `import ${rel(j.sheet)}`}`).join(", ")}`);
  // 1. the raw sheets (generation in parallel)
  await pool(jobs, Number(a.concurrency ?? 2), async (j) => {
    const adir = path.join(out, j.id); const raw = path.join(adir, "raw");
    fs.mkdirSync(raw, { recursive: true });
    fs.writeFileSync(path.join(adir, "prompt.txt"), `${prompt}\n`);
    j.raw = path.join(raw, "sheet.png");
    if (j.kind === "import") {
      fs.copyFileSync(j.sheet, j.raw);
      const orig = path.join(path.dirname(j.sheet), "sheet.orig.jpg");
      if (fs.existsSync(orig)) fs.copyFileSync(orig, path.join(raw, "sheet.orig.jpg"));
      const prov = importedProvenance(a["add-provenance"] && a["add-provenance"] !== true ? path.resolve(a["add-provenance"]) : null, j.sheet);
      fs.writeFileSync(path.join(raw, "sheet.provenance.json"), `${JSON.stringify({ imported: rel(j.sheet), sha256: shaFile(j.sheet), provenance: prov, note: "an existing sheet registered as an attempt; its prompt is the one in its own provenance, not attempt prompt.txt" }, null, 2)}\n`);
      j.source = `import`;
      j.generator = prov?.call?.generator ?? null;
      j.promptSha256 = prov?.call?.promptSha256 ?? null;
      j.ok = true;
      return;
    }
    const r = await generateImage({ gen, refs: [concept], prompt, out: j.raw, aspect: "1:1", name: `${s}-sheet-${j.id}`, log, allowGemini: !!a["allow-gemini"] });
    j.source = gen; j.generator = gen; j.promptSha256 = sha256(prompt); j.ok = r.ok;
    j.error = r.ok ? null : `${r.provenance.failure}: ${r.provenance.reason}`;
    j.checks = r.provenance.checks;
  });
  // 2. normalise + measure (sequential: CPU)
  for (const j of jobs) {
    const adir = path.join(out, j.id);
    const rec = { id: j.id, source: j.source, generator: j.generator, raw: rel(j.raw), ...(j.kind === "import" ? { importedFrom: rel(j.sheet) } : {}), promptSha256: j.promptSha256, at: new Date().toISOString() };
    if (!j.ok) { rec.error = j.error; st.attempts.push(rec); log(`[turnaround] ${j.id}: generation FAILED (${j.error})`); continue; }
    try {
      const nz = await normalizeSheet(s, j.raw, adir, { mirror, keepMain });
      rec.normalize = { command: nz.command, notes: nz.notes };
      for (const note of nz.notes) log(`[turnaround] ${j.id}: NOTE ${note}`);
      const warns = await orientationWarnings(s, adir);
      if (warns.length) { rec.warnings = warns; for (const w of warns) log(`[turnaround] ${j.id}: WARN ${w}`); }
      const m = await measureSet(s, adir, { json: path.join(adir, "hull.json"), png: path.join(adir, "hull.png"), title: `hull · ${s} · ${j.id} (${j.source})` });
      rec.summary = m.summary;
      if (j.checks?.warnings) rec.generationWarnings = j.checks.warnings;
      log(`[turnaround] ${j.id}: ${line(m.summary)}`);
    } catch (e) {
      rec.error = e.message.split("\n")[0];
      log(`[turnaround] ${j.id}: FAILED ${rec.error}`);
    }
    st.attempts.push(rec);
  }
  chooseAndReport(st, out, a, log);
  return st.current ? 0 : 1;
}

/** The setup stop rule before a generation: refuse, or record an explicit owner exception (--owner-override). */
function stopGate(st, a, what, view, log) {
  const stop = stopRule(st);
  const refusal = stopRefusal(stop, what, view);
  if (!refusal) return;
  const words = a["owner-override"];
  if (!words || words === true) throw new Error(refusal);
  (st.stopOverrides ??= []).push({ at: new Date().toISOString(), what, view, words, why: stop.why });
  log(`[turnaround] setup stop rule overridden by the owner (${words}): ${stop.why}`);
}

/** Re-choose the best attempt into current/ (unless a repair was KEPT), write state, print the table. */
function chooseAndReport(st, out, a, log) {
  const kept = st.repairs.filter((r) => r.verdict === "KEEP").length;
  const best = chooseAttempt(st.attempts);
  if (best && (!kept || a.rechoose)) {
    if (best !== st.chosen || !st.current) {
      const cur = path.join(out, "current");
      fs.rmSync(cur, { recursive: true, force: true });
      copySet(path.join(out, best), cur, { extras: ["normalize.json", "hull.json", "hull.png"] });
      const sm = st.attempts.find((x) => x.id === best).summary;
      st.current = { from: best, repairs: [], summary: sm };
    }
    st.chosen = best;
  } else if (best && kept) log(`[turnaround] current/ carries ${kept} KEPT repair(s): not re-chosen (--rechoose to start over from ${best})`);
  writeState(out, st);
  attemptTable(st, log);
  if (st.current) {
    const miss = targetMisses(st.current.summary);
    log(`[turnaround] current (${st.current.from}${st.current.repairs.length ? ` + ${st.current.repairs.join(", ")}` : ""}): ${line(st.current.summary)} · targets ${miss.length ? `MISSED: ${miss.join("; ")}` : "met"}`);
  }
}

/**
 * renorm: normalise one attempt's raw sheet again with an orientation fix (--mirror <views>: a recorded PURE mirror, e.g.
 * a side drawn with the front to the right) or --keep-main, re-measure it, re-choose.
 */
async function cmdRenorm(a, log) {
  const s = a.subject; const out = path.resolve(a.dir);
  const st = readState(out, s);
  const rec = st.attempts.find((x) => x.id === a.attempt);
  if (!rec) throw new Error(`renorm: no ${a.attempt} in ${rel(out)}/state.json`);
  const mirror = typeof a.mirror === "string" ? a.mirror.split(",").map((x) => x.trim()).filter(Boolean) : [];
  const keepMain = a["keep-main"] && a["keep-main"] !== true ? Number(a["keep-main"]) : null;
  const adir = path.join(out, rec.id);
  const nz = await normalizeSheet(s, path.resolve(ROOT, rec.raw), adir, { mirror, keepMain });
  rec.normalize = { command: nz.command, notes: nz.notes, orientation: a.why && a.why !== true ? a.why : (mirror.length ? `mirrored ${mirror.join(", ")}` : null) };
  const warns = await orientationWarnings(s, adir);
  rec.warnings = warns;
  for (const w of warns) log(`[turnaround] ${rec.id}: WARN ${w}`);
  const m = await measureSet(s, adir, { json: path.join(adir, "hull.json"), png: path.join(adir, "hull.png"), title: `hull · ${s} · ${rec.id} (${rec.source}, renormalised)` });
  rec.summary = m.summary; delete rec.error;
  log(`[turnaround] ${rec.id}: ${line(m.summary)}`);
  if (st.chosen === rec.id && !st.repairs.some((r) => r.verdict === "KEEP")) st.current = null;   // re-copy it
  chooseAndReport(st, out, a, log);
  return 0;
}

/** Normalise one generated view onto the current set's targets -> the written file's normaliser record. */
async function normalizeOne(view, rawFile, outFile, curDir) {
  const nj = JSON.parse(fs.readFileSync(path.join(curDir, "normalize.json"), "utf8"));
  const C = nj.canvas; const fgMax = nj.fgMax ?? 235; const minBlob = nj.minBlob ?? 30; const margin = nj.margin ?? 3; const bgClean = nj.bgClean ?? 240;
  let target; let axis;
  if (view === "front" || view === "rear") {
    axis = "h";
    const side = await readRGB(path.join(curDir, "side.png"));
    target = bboxOf(drawingMask(side, { fgMax, minBlob }).mask, side.width, side.height).h;
  } else { axis = "w"; target = nj.sideL; }
  const img = await readRGB(rawFile);
  let keepMain = 0;
  let r = await normalizeView(img, { axis, target, C, fgMax, minBlob, keepMain, margin, bgClean });
  const write = async (res) => sharp(res.img.data, { raw: { width: C, height: C, channels: 3 } }).png().toFile(outFile);
  await write(r);
  const stray = await strayMarks(path.dirname(outFile), [path.basename(outFile, ".png")]);
  const notes = [...r.notes];
  if (Object.keys(stray).length) {
    keepMain = KEEP_MAIN_PX;
    r = await normalizeView(img, { axis, target, C, fgMax, minBlob, keepMain, margin, bgClean });
    await write(r);
    notes.push(`stray marks outside the drawing: re-normalised with keepMain ${KEEP_MAIN_PX}`);
  }
  return { axis, target, C, scale: r.scale, rawBbox: r.raw, outBbox: r.out, keepMain: keepMain || null, notes };
}

/** A draft for view `view` from the current set -> {file, info}. */
async function makeDraft(kind, view, curDir, m, facts, outFile) {
  const nj = JSON.parse(fs.readFileSync(path.join(curDir, "normalize.json"), "utf8"));
  const C = nj.canvas; const fgMax = nj.fgMax ?? 235;
  if (kind === "mirror") {
    const other = OTHER_END[view];
    const src = await readRGB(path.join(curDir, `${other}.png`));
    const img = mirrorRGB(src);
    await sharp(img.data, { raw: { width: img.width, height: img.height, channels: 3 } }).png().toFile(outFile);
    return { kind, from: `current/${other}.png mirrored left to right` };
  }
  const target = draftDims(m.summary, facts.dims);
  const f = proportionFactors(view, viewMeasures(m.reg, view), target.dims);
  const src = await readRGB(path.join(curDir, `${view}.png`));
  const bb = bboxOf(drawingMask(src, { fgMax }).mask, src.width, src.height);
  const pad = 3;
  const cw = bb.w + 2 * pad; const ch = bb.h + 2 * pad;
  const box = stretchBox(cw, ch, f.kx, f.ky, C);
  const crop = await sharp(src.data, { raw: { width: src.width, height: src.height, channels: 3 } })
    .extract({ left: Math.max(0, bb.x0 - pad), top: Math.max(0, bb.y0 - pad), width: Math.min(cw, src.width - Math.max(0, bb.x0 - pad)), height: Math.min(ch, src.height - Math.max(0, bb.y0 - pad)) })
    .resize(box.w, box.h, { kernel: "lanczos3", fit: "fill" }).png().toBuffer();
  await sharp({ create: { width: C, height: C, channels: 3, background: { r: 255, g: 255, b: 255 } } })
    .composite([{ input: crop, left: Math.round((C - box.w) / 2), top: Math.round((C - box.h) / 2) }]).png().toFile(outFile);
  return { kind, from: `current/${view}.png stretched to ${target.from}`, what: f.what, now: f.now, target: f.target, kx: r4(f.kx), ky: r4(f.ky), fit: box.fit };
}

/** A repair's set-level before -> after lines and verdict. */
function verdictLines(id, b, f, v, log) {
  log(`[turnaround] ${id}: set before: ${setLine(b)}`);
  log(`[turnaround] ${id}: set after:  ${setLine(f)}`);
  log(`[turnaround] ${id}: ${v.verdict} (set rule: ${v.reasons.join("; ")})`);
}

/** KEEP a candidate set into current/: current/ backed up to `backup` first (verdict --revert restores it). */
function keepCandidate(st, dir, id, view, cand, hullDir, backup, summary) {
  const cur = path.join(dir, "current");
  fs.rmSync(backup, { recursive: true, force: true });
  copySet(cur, backup, { extras: ["normalize.json", "hull.json", "hull.png"] });
  copySet(cand, cur, { views: view === "side" ? VIEWS : [view], extras: [] });
  for (const f of ["hull.json", "hull.png"]) if (fs.existsSync(path.join(hullDir, f))) fs.copyFileSync(path.join(hullDir, f), path.join(cur, f));
  st.current = { from: st.current.from, repairs: [...st.current.repairs, id], summary };
}

async function cmdRepair(a, log) {
  const s = a.subject; const dir = path.resolve(a.dir); const view = a.view;
  if (!VIEWS.includes(view)) throw new Error(`--view ${view} (${VIEWS.join(" | ")})`);
  const gen = a.gen ?? "gpt";   // owner 2026-10-04: GPT is the default generator; gemini only with --allow-gemini
  if (!GEN[gen]) throw new Error(`--gen ${gen} (gpt | gemini)`);
  if (!a.dry && geminiRefusal(gen, !!a["allow-gemini"])) throw new Error(geminiRefusal(gen, !!a["allow-gemini"]));
  const draftKind = a.draft ?? (OTHER_END[view] ? "mirror" : "proportion");
  const st = readState(dir, s);
  if (!st.current) throw new Error(`repair: ${rel(dir)} has no current set (run gen first)`);
  if (!a.dry) stopGate(st, a, "repair", view, log);
  const cur = path.join(dir, "current");
  const T = loadTemplates(); const facts = readFacts(s);
  const prompt = repairPrompt(T, facts, view, draftKind);
  const n = st.repairs.length + 1;
  const id = `repair-${n}-${view}-${gen}-${draftKind}`;
  const rdir = path.join(dir, id);
  fs.mkdirSync(rdir, { recursive: true });
  const before = await measureSet(s, cur);
  const draftFile = path.join(rdir, "draft.png");
  const draft = await makeDraft(draftKind, view, cur, before, facts, draftFile);
  fs.writeFileSync(path.join(rdir, "prompt.txt"), `${prompt}\n`);
  log(`[turnaround] ${id}: draft ${draft.from}${draft.what ? ` (${draft.what} ${draft.now} -> ${draft.target}: kx ${draft.kx} ky ${draft.ky})` : ""} -> ${rel(draftFile)}`);
  if (a.dry) { log(prompt); return 0; }   // the draft and prompt stay for a look; state.json is not touched
  const rec = { id, view, gen, draft, rule: "set", at: new Date().toISOString(), before: before.summary };
  const raw = path.join(rdir, "raw", `${view}.png`);
  const g = await generateImage({ gen, refs: [path.join(cur, `${view}.png`), draftFile], prompt, out: raw, aspect: ASPECT[view], name: `${s}-${view}-r${n}`, log, allowGemini: !!a["allow-gemini"] });
  if (!g.ok) {
    Object.assign(rec, { verdict: "FAILED", reasons: [`generation ${g.provenance.failure}: ${g.provenance.reason}`] });
    st.repairs.push(rec); writeState(dir, st);
    log(`[turnaround] ${id}: generation FAILED (${g.provenance.failure}: ${g.provenance.reason}) — current/ unchanged`);
    return 1;
  }
  if (g.provenance.checks?.warnings) rec.generationWarnings = g.provenance.checks.warnings;
  // the candidate set: current + the new view (a side repair also re-normalises front / rear to the new side height)
  const cand = path.join(rdir, "candidate");
  fs.rmSync(cand, { recursive: true, force: true });
  copySet(cur, cand);
  rec.normalize = await normalizeOne(view, raw, path.join(cand, `${view}.png`), cand);
  if (view === "side") {
    rec.renormalized = {};
    for (const v of ["front", "rear"]) rec.renormalized[v] = await normalizeOne(v, path.join(cur, `${v}.png`), path.join(cand, `${v}.png`), cand);
  }
  // the copy check (against image 1 and the draft normalised the same way)
  const draftNorm = path.join(rdir, "draft-normalised.png");
  await normalizeOne(view, draftFile, draftNorm, cand);
  const fgMaxSubj = readJson(viewsFile(s)).families?.fgMax ?? 235;
  const simCur = await similarity(path.join(cand, `${view}.png`), path.join(cur, `${view}.png`), fgMaxSubj);
  const simDraft = await similarity(path.join(cand, `${view}.png`), draftNorm, fgMaxSubj);
  rec.similarity = { current: simCur, draft: simDraft };
  const copyOf = isCopy(simCur) ? "image 1 (the current view)" : isCopy(simDraft) ? "image 2 (the draft)" : null;
  // the whole set after, the aniso fit warm-started from the set before (the same stretch of a flat valley)
  const after = await measureSet(s, cand, { json: path.join(rdir, "hull.json"), png: path.join(rdir, "hull.png"), title: `hull · ${s} · ${id}`, anisoFrom: before.summary.aniso?.params ?? null });
  const v = repairVerdict(before.summary, after.summary, view, { copyOf });
  Object.assign(rec, { after: after.summary, verdict: v.verdict, reasons: v.reasons, met: v.met });
  if (v.verdict === "KEEP") { rec.backup = rel(path.join(rdir, "before")); keepCandidate(st, dir, id, view, cand, rdir, path.join(rdir, "before"), after.summary); }
  st.repairs.push(rec);
  writeState(dir, st);
  log(`[turnaround] ${id}: similarity current IoU ${simCur.iou} diff ${simCur.diff} · draft IoU ${simDraft.iou} diff ${simDraft.diff}`);
  verdictLines(id, before.summary, after.summary, v, log);
  if (v.verdict === "KEEP") log(`[turnaround] ${id}: LOOK at ${rel(path.join(cand, `${view}.png`))} — a feature error you can see (a part on the wrong flank, a missing part) is a REVERT regardless of the numbers: turnaround.mjs verdict --subject ${s} --dir ${rel(dir)} --repair ${id} --revert --why "..."`);
  const miss = targetMisses(st.current.summary);
  log(`[turnaround] current: ${line(st.current.summary)} · targets ${miss.length ? `MISSED: ${miss.join("; ")}` : "met"}`);
  return 0;
}

/**
 * rejudge: an earlier repair's candidate set judged again under the current KEEP rule (the set before = current/ now);
 * refused when current/ changed since in a view the candidate did not replace. KEEP applies it like a repair.
 */
async function cmdRejudge(a, log) {
  const s = a.subject; const dir = path.resolve(a.dir);
  const st = readState(dir, s);
  const r0 = st.repairs.find((r) => r.id === a.repair);
  if (!r0) throw new Error(`rejudge: no repair ${a.repair} in ${rel(dir)}/state.json (${st.repairs.map((r) => r.id).join(", ")})`);
  const rdir = path.join(dir, r0.id), cand = path.join(rdir, "candidate"), cur = path.join(dir, "current");
  if (!fs.existsSync(path.join(cand, `${r0.view}.png`))) throw new Error(`rejudge: ${rel(cand)} holds no ${r0.view}.png`);
  const replaced = r0.view === "side" ? VIEWS : [r0.view];
  const stale = VIEWS.filter((v) => !replaced.includes(v)).filter((v) => shaFile(path.join(cand, `${v}.png`)) !== shaFile(path.join(cur, `${v}.png`)));
  if (stale.length) throw new Error(`rejudge: ${rel(cand)} differs from current/ in ${stale.join(", ")} (current/ changed since ${r0.id}): repair again instead`);
  if (st.repairs.some((r) => r.rejudgeOf === r0.id && r.verdict === "KEEP")) throw new Error(`rejudge: ${r0.id} was judged again and kept already`);
  if (st.repairs.some((r) => r.rejudgeOf === r0.id) && !a.again) throw new Error(`rejudge: ${r0.id} was judged again already (--again: once more, e.g. after a tool fix; both records stay)`);
  const id = `rejudge-${st.repairs.length + 1}-${r0.id}`;
  const before = await measureSet(s, cur);
  const after = await measureSet(s, cand, { json: path.join(rdir, "hull-rejudge.json"), png: path.join(rdir, "hull-rejudge.png"), title: `hull · ${s} · ${id}`, anisoFrom: before.summary.aniso?.params ?? null });
  const sim = r0.similarity ?? null;
  const copyOf = sim && isCopy(sim.current) ? "image 1 (the current view)" : sim && isCopy(sim.draft) ? "image 2 (the draft)" : null;
  const v = repairVerdict(before.summary, after.summary, r0.view, { copyOf });
  const rec = { id, rejudgeOf: r0.id, view: r0.view, gen: r0.gen, draft: r0.draft, rule: "set", at: new Date().toISOString(), before: before.summary, after: after.summary, verdict: v.verdict, reasons: v.reasons, met: v.met, similarity: sim };
  if (v.verdict === "KEEP") {
    const hdir = path.join(rdir, "rejudge-hull");
    fs.mkdirSync(hdir, { recursive: true });
    for (const [f0, f1] of [["hull-rejudge.json", "hull.json"], ["hull-rejudge.png", "hull.png"]]) fs.copyFileSync(path.join(rdir, f0), path.join(hdir, f1));
    rec.backup = rel(path.join(rdir, "before-rejudge"));
    keepCandidate(st, dir, id, r0.view, cand, hdir, path.join(rdir, "before-rejudge"), after.summary);
  }
  st.repairs.push(rec);
  writeState(dir, st);
  log(`[turnaround] ${id}: ${r0.id} (${r0.verdict} under the ${r0.rule ?? "view"} rule) judged again under the set rule`);
  verdictLines(id, before.summary, after.summary, v, log);
  const miss = targetMisses(st.current.summary);
  log(`[turnaround] current: ${line(st.current.summary)} · targets ${miss.length ? `MISSED: ${miss.join("; ")}` : "met"}`);
  return 0;
}

/** verdict --revert: the LAST kept repair undone for a feature error seen on the image (current/ restored from its backup). */
async function cmdVerdict(a, log) {
  const s = a.subject; const dir = path.resolve(a.dir);
  const st = readState(dir, s);
  const rec = st.repairs.find((r) => r.id === a.repair);
  if (!rec) throw new Error(`verdict: no repair ${a.repair}`);
  if (a.keep) return verdictKeep(a, s, dir, st, rec, log);
  if (!a.revert || !a.why || a.why === true) throw new Error("verdict: --revert --why \"<the feature error you see>\" (a KEEP is only ever overridden to REVERT)");
  if (rec.verdict !== "KEEP") throw new Error(`verdict: ${rec.id} is ${rec.verdict}, nothing to revert`);
  const last = st.current.repairs[st.current.repairs.length - 1];
  if (last !== rec.id) throw new Error(`verdict: only the last kept repair (${last}) can be reverted`);
  const backup = rec.backup ? path.resolve(ROOT, rec.backup) : null;
  if (!backup || !fs.existsSync(backup)) throw new Error(`verdict: ${rec.id} has no backup of the set before it`);
  const cur = path.join(dir, "current");
  copySet(backup, cur, { extras: ["normalize.json", "hull.json", "hull.png"] });
  rec.verdict = "REVERT";
  rec.override = { at: new Date().toISOString(), why: a.why, by: "visual check: a feature error regardless of the numbers" };
  rec.reasons = [...(rec.reasons ?? []), `feature error (visual check): ${a.why}`];
  st.current = { from: st.current.from, repairs: st.current.repairs.slice(0, -1), summary: rec.before };
  writeState(dir, st);
  log(`[turnaround] ${rec.id}: KEEP -> REVERT (${a.why}); current/ restored from ${rel(backup)}`);
  return 0;
}

/**
 * verdict --keep --ruling "<the audit / orchestrator ruling>": a REVERTed repair's candidate applied anyway — the audit
 * proposed REGENERATE for that view with its own acceptance criteria (e.g. a measured proportion) that the set-level rule
 * cannot see (its worst viewOnly sits in another view). Refused for a copy, a failed generation, a fix, a rejudge record,
 * a KEEP, and when current/ changed since in a view the candidate does not replace (as rejudge). The record keeps the
 * set rule's REVERT reasons and adds `override` {by: "ruling", ruling}; current/ is backed up (verdict --revert restores it).
 * -> the refusal text, or null
 */
export function keepOverrideRefusal(rec, stale = []) {
  if (rec.verdict !== "REVERT") return `${rec.id} is ${rec.verdict}: only a REVERTed repair can be kept by a ruling`;
  if (rec.rule === "fix" || rec.rejudgeOf) return `${rec.id} is a ${rec.rule === "fix" ? "fix" : "rejudge"} record: repair / rejudge instead`;
  if (rec.override) return `${rec.id} was overridden already`;
  if ((rec.reasons ?? []).some((r) => /copy of/.test(r))) return `${rec.id} is a copy of a reference: never kept`;
  if (stale.length) return `${rec.id}'s candidate differs from current/ in ${stale.join(", ")} (current/ changed since): repair again instead`;
  return null;
}
async function verdictKeep(a, s, dir, st, rec, log) {
  if (!a.ruling || a.ruling === true) throw new Error("verdict --keep: --ruling \"<the audit / orchestrator ruling that decides this view>\"");
  const rdir = path.join(dir, rec.id), cand = path.join(rdir, "candidate"), cur = path.join(dir, "current");
  if (!fs.existsSync(path.join(cand, `${rec.view}.png`))) throw new Error(`verdict --keep: ${rel(cand)} holds no ${rec.view}.png`);
  const replaced = rec.view === "side" ? VIEWS : [rec.view];
  const stale = VIEWS.filter((v) => !replaced.includes(v)).filter((v) => shaFile(path.join(cand, `${v}.png`)) !== shaFile(path.join(cur, `${v}.png`)));
  const why = keepOverrideRefusal(rec, stale);
  if (why) throw new Error(`verdict --keep: ${why}`);
  const before = await measureSet(s, cur);
  const after = await measureSet(s, cand, { json: path.join(rdir, "hull-keep.json"), png: path.join(rdir, "hull-keep.png"), title: `hull · ${s} · ${rec.id} (kept by ruling)`, anisoFrom: before.summary.aniso?.params ?? null });
  const hdir = path.join(rdir, "keep-hull");
  fs.mkdirSync(hdir, { recursive: true });
  for (const [f0, f1] of [["hull-keep.json", "hull.json"], ["hull-keep.png", "hull.png"]]) fs.copyFileSync(path.join(rdir, f0), path.join(hdir, f1));
  rec.override = { at: new Date().toISOString(), by: "ruling", ruling: a.ruling, before: before.summary, after: after.summary };
  rec.verdict = "KEEP";
  rec.reasons = [...(rec.reasons ?? []).map((r) => `set rule: ${r}`), `kept by ruling: ${a.ruling}`];
  rec.backup = rel(path.join(rdir, "before"));
  keepCandidate(st, dir, rec.id, rec.view, cand, hdir, path.join(rdir, "before"), after.summary);
  writeState(dir, st);
  verdictLines(rec.id, before.summary, after.summary, { verdict: "KEEP", reasons: [`ruling: ${a.ruling}`] }, log);
  const miss = targetMisses(st.current.summary);
  log(`[turnaround] current: ${line(st.current.summary)} · targets ${miss.length ? `MISSED: ${miss.join("; ")}` : "met"}`);
  return 0;
}

/**
 * `--rects "x0,y0,x1,y1[;...]"` (fix): the audit's defect rects in that image's px, half-open like views.json drift rects
 * (px X is inside when x0 <= X < x1). -> [[x0, y0, x1, y1], ...]; throws on anything else.
 */
export function parseRects(text) {
  const rects = String(text).split(";").map((r) => r.trim()).filter(Boolean).map((r) => r.split(",").map((v) => Number(v.trim())));
  if (!rects.length || rects.some((r) => r.length !== 4 || r.some((v) => !Number.isInteger(v) || v < 0) || r[2] <= r[0] || r[3] <= r[1])) {
    throw new Error(`fix: --rects "${text}" is not "x0,y0,x1,y1[;x0,y0,x1,y1...]" (integer px, x1 > x0, y1 > y0)`);
  }
  return rects;
}
export const inRects = (rects, x, y) => rects.some(([x0, y0, x1, y1]) => x >= x0 && x < x1 && y >= y0 && y < y1);

/**
 * The fix rule (pure): without rects a semantic fix is kept unless it moves > 0.5 % of the view's foreground (a recolour
 * inside a region); with the audit's rects (an EDIT that adds or removes a part) every changed px must lie inside them —
 * any px changed outside is a REVERT — and the foreground may move (recorded). -> {verdict, reasons}
 */
export function fixVerdict({ why, changed, moved, rects = null, outside = 0 }) {
  if (rects) {
    if (outside > 0) return { verdict: "REVERT", reasons: [`${outside} px changed outside the audit rects ${JSON.stringify(rects)}: not a region fix`] };
    return { verdict: "KEEP", reasons: [`semantic fix inside the audit rects ${JSON.stringify(rects)} (${why}); ${changed} px changed, foreground moved ${pct(moved)}`] };
  }
  if (moved > 0.005) return { verdict: "REVERT", reasons: [`the edit moves ${pct(moved)} of the view's foreground (> 0.5 %): not a region fix`] };
  return { verdict: "KEEP", reasons: [`semantic fix (${why}); ${changed} px changed, foreground moved ${pct(moved)}`] };
}

/**
 * fix: a view edited OUTSIDE this tool (a semantic fix: a GPT edit composited into its own region, the procedure of
 * refs/garbage_truck.v2.README.md) registered as a repair: the image replaces current/<view>.png as is (same canvas, no
 * normalisation), the set is measured before / after and recorded; a semantic fix is kept regardless of the numbers (an
 * audit ruling), unless it moves the view's foreground by more than 0.5 % (then it is no region fix: REVERT). With
 * `--rects` (the audit's EDIT rects: a part added / removed) the foreground may move, but every changed px must lie inside
 * the rects (fixVerdict).
 */
async function cmdFix(a, log) {
  const s = a.subject; const dir = path.resolve(a.dir); const view = a.view;
  if (!VIEWS.includes(view)) throw new Error(`--view ${view} (${VIEWS.join(" | ")})`);
  if (!a.image || a.image === true || !a.why || a.why === true) throw new Error("fix: --image <edited png> --why \"<the feature fixed>\"");
  const st = readState(dir, s);
  if (!st.current) throw new Error(`fix: ${rel(dir)} has no current set`);
  const cur = path.join(dir, "current");
  const img = path.resolve(a.image);
  const A = await readRGB(path.join(cur, `${view}.png`)); const B = await readRGB(img);
  if (A.width !== B.width || A.height !== B.height) throw new Error(`fix: ${rel(img)} is ${B.width} x ${B.height}, current/${view}.png ${A.width} x ${A.height}`);
  const rects = a.rects && a.rects !== true ? parseRects(a.rects) : null;
  const n = st.repairs.length + 1;
  const id = `fix-${n}-${view}`;
  const rdir = path.join(dir, id);
  const cand = path.join(rdir, "candidate");
  fs.rmSync(cand, { recursive: true, force: true });
  copySet(cur, cand);
  fs.copyFileSync(img, path.join(cand, `${view}.png`));
  const fgMax = readJson(viewsFile(s)).families?.fgMax ?? 235;
  const ma = drawingMask(A, { fgMax }).mask, mb = drawingMask(B, { fgMax }).mask;
  let changed = 0, fg = 0, fgMoved = 0, outside = 0;
  for (let i = 0; i < ma.length; i += 1) {
    if (ma[i]) fg += 1;
    if (ma[i] !== mb[i]) fgMoved += 1;
    const p = i * 3;
    if (A.data[p] !== B.data[p] || A.data[p + 1] !== B.data[p + 1] || A.data[p + 2] !== B.data[p + 2]) {
      changed += 1;
      if (rects && !inRects(rects, i % A.width, Math.floor(i / A.width))) outside += 1;
    }
  }
  const before = await measureSet(s, cur);
  const after = await measureSet(s, cand, { json: path.join(rdir, "hull.json"), png: path.join(rdir, "hull.png"), title: `hull · ${s} · ${id}`, anisoFrom: before.summary.aniso?.params ?? null });
  const moved = fg ? fgMoved / fg : 0;
  const fv = fixVerdict({ why: a.why, changed, moved, rects, outside });
  const v = { ...fv, met: fv.verdict === "KEEP" && targetMisses(after.summary).length === 0 };
  const rec = { id, view, fix: { image: rel(img), sha256: shaFile(img), why: a.why, changedPx: changed, fgMoved: r4(moved), ...(rects ? { rects, changedOutside: outside } : {}) }, rule: "fix", at: new Date().toISOString(), before: before.summary, after: after.summary, verdict: v.verdict, reasons: v.reasons, met: v.met };
  if (v.verdict === "KEEP") { rec.backup = rel(path.join(rdir, "before")); keepCandidate(st, dir, id, view, cand, rdir, path.join(rdir, "before"), after.summary); }
  st.repairs.push(rec);
  writeState(dir, st);
  verdictLines(id, before.summary, after.summary, v, log);
  const miss = targetMisses(st.current.summary);
  log(`[turnaround] current: ${line(st.current.summary)} · targets ${miss.length ? `MISSED: ${miss.join("; ")}` : "met"}`);
  return 0;
}

async function cmdFamilies(a, log) {
  const s = a.subject;
  const out = a.dir && a.dir !== true ? path.resolve(a.dir) : path.join(ROOT, "out", "turnaround", s);
  const viewsDir = a["views-dir"] && a["views-dir"] !== true ? path.resolve(a["views-dir"]) : null;
  const P = await familyProposal(s, { dir: viewsDir });
  log(`[families] ${s} · ${P.dir}: per view the foreground colour clusters (>= ${FAMILIES.major * 100} %) matched to the families with one colour offset; share of the foreground: the table -> the proposal (the concept's)`);
  for (const l of proposalLines(P)) log(`[families] ${l}`);
  fs.mkdirSync(out, { recursive: true });
  const pf = path.join(out, "families.proposal.json");
  fs.writeFileSync(pf, `${JSON.stringify(P, null, 2)}\n`);
  log(`[families] proposal ${rel(pf)}`);
  if (a.apply) {
    if (viewsDir) throw new Error("families --apply writes the LIVE views' tables: drop --views-dir");
    applyViewTable(s, P, pf, log);
  }
  return 0;
}

/** views.json families.viewTable (+ `_viewTable`) = the proposal's; the rest of the file byte-identical. */
export function applyViewTable(subject, P, proposalFile, log = () => {}) {
  const vf = viewsFile(subject);
  const text = fs.readFileSync(vf, "utf8");
  const spec = JSON.parse(text);
  const fam = { ...spec.families };
  delete fam.viewTable; delete fam._viewTable;
  const amb = Object.entries(P.views).flatMap(([v, V]) => V.clusters.filter((c) => c.ambiguous).map((c) => `${v} ${c.hex} ${(c.share * 100).toFixed(1)} % ${c.family} (vs ${c.family2})`));
  fam.viewTable = P.viewTable;
  fam._viewTable = `${TODAY()}: per-view colours of the families (scripts/v7/turnaround.mjs families --apply; ${rel(proposalFile)}): each view's foreground colour clusters (>= ${FAMILIES.major * 100} %) matched to the table's families with ONE per-view colour offset (${Object.entries(P.views).map(([v, V]) => `${v} ${V.offset.map((x) => `${x >= 0 ? "+" : ""}${x}`).join(" ")}`).join(" · ")}); ambiguous: ${amb.length ? amb.join("; ") : "none"}. Measured on these images: turnaround.mjs re-derives it for any other image set and install writes it for the installed one.`;
  fs.writeFileSync(vf, withFamilies(text, fam));
  log(`[families] ${rel(vf)}: families.viewTable written (${Object.keys(P.viewTable).join(", ")})`);
}

async function cmdStatus(a, log) {
  const s = a.subject; const dir = path.resolve(a.dir);
  const st = readState(dir, s);
  if (!st.current) throw new Error(`status: ${rel(dir)} has no current set`);
  const cur = path.join(dir, "current");
  const m = await measureSet(s, cur, { json: path.join(cur, "hull.json"), png: path.join(cur, "hull.png"), title: `hull · ${s} · current` });
  for (const l of reportLines(s, rel(cur), m.report)) if (!/^\s+(viewOnly|conceptOnly|conceptOnly \(aniso\)) /.test(l) || a.blobs) log(`[turnaround] ${l}`);
  if (m.families) log(`[turnaround] per-view families re-derived for these images: offsets ${Object.entries(m.report.families.offsets).map(([v, o]) => `${v} ${o.join(",")}`).join(" · ")}${m.report.families.ambiguous.length ? ` · ambiguous ${m.report.families.ambiguous.join("; ")}` : ""}`);
  attemptTable(st, log);
  for (const r of st.repairs) {
    log(`[turnaround] ${r.id}: ${r.verdict}${r.rule === "set" ? " (set rule)" : " (view rule)"}${r.after ? ` · worst viewOnly ${pct(r.before.worstViewOnly)} -> ${pct(r.after.worstViewOnly)} · cOnlyBlob ${pct(r.before.conceptOnlyBlob)} -> ${pct(r.after.conceptOnlyBlob)}${r.after.aspect ? ` · aspect H/W ${r.before.aspect ? sgn(r.before.aspect.HoverW) : "-"} -> ${sgn(r.after.aspect.HoverW)} L/W ${r.before.aspect ? sgn(r.before.aspect.LoverW) : "-"} -> ${sgn(r.after.aspect.LoverW)}` : ""}` : ""}${r.reasons?.length ? ` (${r.reasons.join("; ")})` : ""}`);
  }
  st.current.summary = m.summary;
  if (a.mark && a.mark !== true) { st.marks ??= {}; st.marks[a.mark] = { at: new Date().toISOString(), repairs: [...st.current.repairs], summary: m.summary }; log(`[turnaround] marked "${a.mark}"`); }
  writeState(dir, st);
  const miss = targetMisses(m.summary);
  log(`[turnaround] current (${st.current.from}${st.current.repairs.length ? ` + ${st.current.repairs.join(", ")}` : ""}): ${line(m.summary)}`);
  log(`[turnaround] targets (gold.config.json setupHull: every viewOnly <= ${pct(TARGETS.viewOnly, 1)}, conceptOnlyBlob <= ${pct(TARGETS.conceptOnlyBlob, 1)}, |aspect| <= ${pct(TARGETS.aspect, 1)} per ratio, residual within +-${pct(TARGETS.residual, 0)}): ${miss.length ? `MISSED — ${miss.join("; ")}` : "MET"}`);
  log(`[turnaround] ${devText(m.summary, readFacts(s))} · hullOnly (concept) ${pct(m.report.concept.hullOnly)}`);
  const stop = stopRule(st);
  log(`[turnaround] setup stop rule (gold.config.json setupStop): ${stop.spent ? `SPENT — ${stop.why}: no more regeneration${stop.setsSpent ? "" : ` of ${stop.spentViews.join(", ")}`}; the setup audit rules target-wins (READY with rulings, audit.json acceptBlocks)` : `not spent — ${stop.why}`}`);
  if (a.loo) {
    const rows = await looRows(s, m);
    for (const r of rows) log(`[turnaround] loo without ${r.view.padEnd(5)}: the concept px it alone carves — supported (concept fg: it contradicts the concept) ${pct(r.supported)} · unsupported (not in the concept: it is right) ${pct(r.unsupported)}`);
    const fr = Object.fromEntries(rows.map((r) => [r.view, r]));
    if (fr.front && fr.rear) {
      const d = fr.front.supported - fr.rear.supported;
      log(`[turnaround] loo front vs rear: ${Math.abs(d) < 0.002 ? "unsure -> repair the rear to match the front (the concept shows the front face)" : d > 0 ? "the front carves more concept foreground -> the front contradicts the concept" : "the rear carves more concept foreground -> the rear contradicts the concept"}`);
    }
  }
  return 0;
}

async function cmdPrompt(a, log) {
  const T = loadTemplates(); const facts = readFacts(a.subject);
  log(a.view ? repairPrompt(T, facts, a.view, a.draft ?? (OTHER_END[a.view] ? "mirror" : "proportion")) : sheetPrompt(T, facts));
  return 0;
}

/** subjects/<s>/turnaround/sheet.png: concept, side, front, rear, top, each 480 x 480 (sharp lanczos3), side by side. */
export async function buildSheet(subject, { tile = 480, out = null } = {}) {
  const S = loadSubject(subject);
  const dir = path.join(ROOT, "subjects", subject, "turnaround");
  const spec = readJson(viewsFile(subject));
  const files = [S.paths.target, ...VIEWS.map((v) => path.join(dir, spec.views[v].file))];
  const tiles = [];
  for (const f of files) tiles.push(await sharp(f).flatten({ background: "#ffffff" }).removeAlpha().resize(tile, tile, { fit: "contain", background: "#ffffff" }).png().toBuffer());
  out ??= path.join(dir, "sheet.png");
  await sharp({ create: { width: tile * files.length, height: tile, channels: 3, background: { r: 255, g: 255, b: 255 } } })
    .composite(tiles.map((input, i) => ({ input, left: i * tile, top: 0 }))).png().toFile(out);
  return out;
}

/** One repair's README entry: the view rule (before 2026-09-28) or the set rule, the verdict and its reasons. */
function repairEntry(r) {
  const head = `${r.id} (${r.draft?.from ?? r.draft?.kind ?? "-"})`;
  if (!r.after) return `${head}: ${r.verdict}${r.reasons?.length ? ` (${r.reasons.join("; ")})` : ""}`;
  const b = r.before, f = r.after;
  const nums = r.rule === "set"
    ? `set worst viewOnly ${b.worstView} ${pct(b.worstViewOnly, 1)} → ${f.worstView} ${pct(f.worstViewOnly, 1)}, conceptOnlyBlob ${pct(b.conceptOnlyBlob)} → ${pct(f.conceptOnlyBlob)}, aspect H/W ${b.aspect ? sgn(b.aspect.HoverW) : "-"} → ${f.aspect ? sgn(f.aspect.HoverW) : "-"} L/W ${b.aspect ? sgn(b.aspect.LoverW) : "-"} → ${f.aspect ? sgn(f.aspect.LoverW) : "-"}, residual max ${pct(b.residualMax, 1)} → ${pct(f.residualMax, 1)}`
    : `viewOnly ${r.view} ${pct(b.views[r.view].viewOnly, 1)} → ${pct(f.views[r.view].viewOnly, 1)}, conceptOnlyBlob ${pct(b.conceptOnlyBlob)} → ${pct(f.conceptOnlyBlob)}, residual max ${pct(b.residualMax, 1)} → ${pct(f.residualMax, 1)}`;
  return `${head}${r.rejudgeOf ? ` [${r.rejudgeOf}'s candidate judged again]` : ""}: ${nums} ${r.verdict}${r.rule === "set" ? " (set rule)" : " (view rule)"}${r.reasons?.length ? ` (${r.reasons.join("; ")})` : ""}`;
}

/** The whole set's numbers for a README line. */
const readmeSet = (sm) => `worst viewOnly ${pct(sm.worstViewOnly, 1)} (${sm.worstView}), viewOnly side / front / rear / top ${VIEWS.map((v) => (sm.views[v].viewOnly * 100).toFixed(1)).join(" / ")} %, conceptOnlyBlob ${pct(sm.conceptOnlyBlob)}, aspect H/W ${sm.aspect ? sgn(sm.aspect.HoverW) : "-"} L/W ${sm.aspect ? sgn(sm.aspect.LoverW) : "-"}, residual max ${pct(sm.residualMax, 1)}${residualBlocks(sm).length ? ` (BLOCK ${residualBlocks(sm).join(", ")})` : ""}, concept IoU ${sm.conceptIoU?.toFixed(3)}`;

function chosenGeneratorText(chosen, cli) {
  if (chosen?.importedFrom) return `imported from ${chosen.importedFrom} (see its recorded provenance)`;
  let provenance = null;
  if (chosen?.raw) {
    const file = path.resolve(ROOT, chosen.raw.replace(/\.png$/i, ".provenance.json"));
    const relative = path.relative(ROOT, file);
    if (!relative.startsWith("..") && !path.isAbsolute(relative) && fs.existsSync(file)) provenance = readJson(file);
  }
  const source = provenance?.generator ?? chosen?.generator ?? chosen?.source;
  const model = provenance?.agentModel ?? provenance?.agentModelAsked ?? GEN[source]?.agent;
  const version = provenance?.cli?.version ?? cli;
  if (source === "gpt") return `generated by GPT (Codex${version ? ` ${version}` : ""}, agent ${model}, image_gen)`;
  if (source === "gemini") return `generated by Gemini (Antigravity${version ? ` ${version}` : ""}, agent ${model}, generate_image)`;
  return `from recorded source ${source ?? "unknown"} (see state.json and image provenance; generator not inferred)`;
}

export function readmeText(subject, st, { cli = null } = {}) {
  const S = loadSubject(subject);
  const a0 = st.attempts.find((x) => x.summary);
  const chosen = st.attempts.find((x) => x.id === st.chosen);
  const fin = st.current.summary;
  const facts = path.join(ROOT, "subjects", subject, "turnaround", "facts.json");
  const nz = chosen?.normalize?.command ?? "";
  const made = String(st.created ?? new Date().toISOString()).slice(0, 10);
  const lines = [];
  lines.push(`Orthographic turnaround of ${S.rel.target} (sha256 ${shaFile(S.paths.target).slice(0, 16)}…), regenerated ${made} with scripts/v7/turnaround.mjs (research/v7/IMAGEGEN-AB.md decision): ONE 2 x 2 sheet (side, front, rear, top) ${chosenGeneratorText(chosen, cli)}, the concept as the reference image; prompt = research/v7/TURNAROUND-PROMPT.md filled from turnaround/facts.json (facts sha256 ${shaFile(facts).slice(0, 16)}…), split on its gutters and normalised with scripts/v7/normalize-views.mjs --like the previous set (a first set: --side-l 800) (1024 px canvas; side bbox length = the previous side's, front / rear bbox height = the side's, top bbox length = the side's). Image generators only generate images; every measurement and decision is the script's.`);
  lines.push("");
  lines.push(`Attempts (score = conceptOnlyBlob + worst viewOnly, scripts/v7/hull.mjs): ${st.attempts.map((x) => `${x.id} (${x.importedFrom ? `the sheet ${x.importedFrom}` : x.source}) ${x.summary ? `${(score(x.summary) * 100).toFixed(2)}` : `failed: ${x.error}`}`).join("; ")} → chosen ${st.chosen}.`);
  const reps = st.repairs;
  lines.push("");
  lines.push(reps.length
    ? `Repairs (one view regenerated from image 1 = the current view + image 2 = a draft). View rule (until 2026-09-28): KEEP only if that view's viewOnly drops and conceptOnlyBlob does not rise. Set rule (from 2026-09-28, gold.config.json setupHull): KEEP when the repaired set meets every target, else only when the set's worst viewOnly drops >= ${(TARGETS.keep.viewOnlyDrop * 100).toFixed(2)} pts AND conceptOnlyBlob rises <= ${(TARGETS.keep.conceptOnlyBlobRise * 100).toFixed(2)} pts AND no |aspect| ratio grows > ${(TARGETS.keep.aspectGrow * 100).toFixed(1)} pts AND no new residual BLOCK; a feature error seen on the image is a REVERT regardless.${reps.some((r) => r.override?.by === "ruling") ? " A setup-audit REGENERATE ruling can keep a candidate the set rule reverted (turnaround.mjs verdict --keep --ruling: its reasons and the ruling are recorded)." : ""} ${reps.map(repairEntry).join("; ")}.`
    : "Repairs: none.");
  for (const [k, m] of Object.entries(st.marks ?? {})) {
    lines.push("");
    lines.push(`Before the pass "${k}" (${m.at.slice(0, 10)}, set ${[st.current.from, ...m.repairs].join(" + ")}; measured with this tool): ${readmeSet(m.summary)} → this set: ${readmeSet(fin)}.`);
  }
  lines.push("");
  lines.push(`Hull, first sheet (${a0?.id}) → this set: residual max ${pct(a0?.summary.residualMax, 1)} → ${pct(fin.residualMax, 1)}; viewOnly side / front / rear / top ${VIEWS.map((v) => (a0.summary.views[v].viewOnly * 100).toFixed(1)).join(" / ")} → ${VIEWS.map((v) => (fin.views[v].viewOnly * 100).toFixed(1)).join(" / ")} %; conceptOnlyBlob ${pct(a0?.summary.conceptOnlyBlob)} → ${pct(fin.conceptOnlyBlob)}; concept IoU ${a0?.summary.conceptIoU?.toFixed(3)} → ${fin.conceptIoU?.toFixed(3)}${fin.aspect ? `; aspect (hull.mjs --aniso: the views' object's proportions over the concept's) H/W ${sgn(fin.aspect.HoverW)}, L/W ${sgn(fin.aspect.LoverW)}` : ""}. Targets (gold.config.json setupHull: every viewOnly <= ${pct(TARGETS.viewOnly, 0)}, conceptOnlyBlob <= ${pct(TARGETS.conceptOnlyBlob, 1)}, |aspect| <= ${pct(TARGETS.aspect, 0)} per ratio, no residual BLOCK +-${pct(TARGETS.residual, 0)}): ${targetMisses(fin).length ? `missed — ${targetMisses(fin).join("; ")}` : "met"}.`);
  const dev = factsDeviation(fin.dims, JSON.parse(fs.readFileSync(facts, "utf8")).dims);
  lines.push("");
  lines.push(`Proportions of the registered set against facts.json dims (not a gate target; the modeller's registration): ${Object.entries(dev).map(([k, x]) => `${k} ${sgn(x)}`).join(", ")}; concept hullOnly ${pct(fin.conceptHullOnly)}.`);
  const spec = readJson(viewsFile(subject));
  if (spec.families?.viewTable) { lines.push(""); lines.push(`Colour families: views.json families.viewTable = these images' own colours of the families (turnaround.mjs families; its \`_viewTable\` note has the offsets and the ambiguous clusters).`); }
  if (nz) { lines.push(""); lines.push(`Normalisation: \`${nz}\`${chosen.normalize.notes?.length ? ` (${chosen.normalize.notes.join("; ")})` : ""}.`); }
  for (const n of st.notes ?? []) { lines.push(""); lines.push(n.text); }
  lines.push("");
  lines.push(`The previous GPT set is in ../turnaround-1-gpt. Work folder (attempts, drafts, repairs, provenance JSON per generation): out/turnaround/${subject}/ (state.json). Pending: the semantic audit (research/v7/AUDITOR.md task 0) and the owner setup gate.`);
  return `${lines.join("\n")}\n`;
}

async function cmdInstall(a, log) {
  const s = a.subject; const dir = path.resolve(a.dir);
  const st = readState(dir, s);
  if (!st.current) throw new Error(`install: ${rel(dir)} has no current set`);
  const cur = path.join(dir, "current");
  const tdir = path.join(ROOT, "subjects", s, "turnaround");
  const vfile = viewsFile(s);
  const spec = readJson(vfile);
  const names = [...VIEWS.map((v) => spec.views[v].file), "sheet.png"];
  const present = names.filter((f) => fs.existsSync(path.join(tdir, f)));
  // --note "<paragraph>": kept in state.json, printed in README.md (replaces a note with the same first 40 characters)
  const notes = [].concat(a.note ?? []).filter((x) => x && x !== true);
  const withNotes = (x) => {
    const out = [...(x.notes ?? [])];
    for (const n of notes) { const i = out.findIndex((o) => o.text.slice(0, 40) === n.slice(0, 40)); if (i >= 0) out[i] = { at: new Date().toISOString(), text: n }; else out.push({ at: new Date().toISOString(), text: n }); }
    return out;
  };
  if (a.dry) {
    const note0 = `${TODAY()}: turnaround regenerated (dry run)`;
    const { dropped: d0 } = regeneratedSpec(spec, note0);
    log(`[turnaround] install --dry ${s}: would copy current/{${VIEWS.join(",")}}.png over ${present.length ? present.join(", ") : "(nothing: the old set is moved)"}; views.json drops ${d0.length ? d0.join(", ") : "nothing"}; README.md:
${readmeText(s, { ...st, notes: withNotes(st) })}`);
    return 0;
  }
  if (present.length && !a.force) throw new Error(`install: subjects/${s}/turnaround still holds ${present.join(", ")} — git mv the old set to subjects/${s}/turnaround-1-gpt/ first (or --force)`);
  for (const v of VIEWS) fs.copyFileSync(path.join(cur, `${v}.png`), path.join(tdir, spec.views[v].file));
  // fresh numbers of the installed set (the concept target reads the live turnaround's mask rule, so after the copy)
  const fresh = await measureSet(s, cur, { json: path.join(cur, "hull.json"), png: path.join(cur, "hull.png"), title: `hull · ${s} · current (install)` });
  st.current.summary = fresh.summary;
  st.notes = withNotes(st);
  st.installed = { at: new Date().toISOString(), repairs: [...st.current.repairs] };
  writeState(dir, st);
  // views.json: drop the keys measured on the old images; a text insertion when nothing is dropped (minimal diff)
  const note = `${TODAY()}: turnaround regenerated (image-generated sheet + repairs, scripts/v7/turnaround.mjs; generator recorded per attempt in out/turnaround/<s>/state.json; any previous set is kept beside it); per-view shift / scale / drift / holes measured on the previous images are not carried over — re-measure them on these images at the setup audit.`;
  const { spec: next, dropped } = regeneratedSpec(spec, note);
  const raw = fs.readFileSync(vfile, "utf8");
  if (!dropped.length && /^\s*"_note":.*,\s*$/m.test(raw)) {
    fs.writeFileSync(vfile, raw.replace(/^(\s*)"_note":.*,\s*$/m, (m0, ind) => `${ind}"_note": ${JSON.stringify(next._note)},`));
  } else if (!dropped.length && /^\s*"_comment":.*,\s*$/m.test(raw)) {
    fs.writeFileSync(vfile, raw.replace(/^(\s*)("_comment":.*,)\s*$/m, (m0, ind, c) => `${ind}${c}\n${ind}"_note": ${JSON.stringify(next._note)},`));
  } else fs.writeFileSync(vfile, `${JSON.stringify(next, null, 2)}\n`);
  JSON.parse(fs.readFileSync(vfile, "utf8"));
  // the per-view families of the installed images (when the subject has them): the same table measureSet derived
  if (fresh.families) {
    const pf = path.join(dir, "families.proposal.json");
    fs.writeFileSync(pf, `${JSON.stringify(fresh.families, null, 2)}\n`);
    applyViewTable(s, fresh.families, pf, log);
  }
  const sheet = await buildSheet(s);
  const agy = spawnSync(process.env.AGY_BIN || path.join(process.env.LOCALAPPDATA || "", "agy", "bin", "agy.exe"), ["--version"], { encoding: "utf8" });
  fs.writeFileSync(path.join(tdir, "README.md"), readmeText(s, st, { cli: (agy.stdout || "").trim() || null }));
  log(`[turnaround] install ${s}: ${VIEWS.map((v) => spec.views[v].file).join(", ")} + ${rel(sheet)} + README.md; views.json ${dropped.length ? `dropped ${dropped.join(", ")}` : "_note set (nothing measured to drop)"}`);
  let provisional = false;
  try { const S = loadSubject(s); provisional = !!JSON.parse(fs.readFileSync(S.paths.layoutMeasured, "utf8"))._frame?.provisional; } catch { /* no frame file */ }
  if (provisional) log(`[turnaround] next (a new subject, scripts/v7/README.md "New subject, once"): ${fresh.families ? "" : `node scripts/v7/turnaround.mjs families --subject ${s} --apply · `}node scripts/v7/hull.mjs --subject ${s} --write-frame (replaces the provisional facts-box frame)`);
  log(`[turnaround] next: node scripts/v7/doctor.mjs --subject ${s} --no-json · node scripts/v7/hull.mjs --subject ${s} --aniso · node scripts/v6/view.mjs --subject ${s} --module out/ref/gold/${s}/model.mjs --out out/ref/gold/${s}/view`);
  return 0;
}

const USAGE = [
  "usage: node scripts/v7/turnaround.mjs gen      --subject <s> --out <dir> [--gen gpt|gemini --allow-gemini] [--attempts 1] [--add-sheet <png> [--add-provenance <json>]] [--mirror <view,...>] [--keep-main <px>] [--concurrency 2] [--rechoose] [--dry] [--owner-override \"<words>\"]",
  "       node scripts/v7/turnaround.mjs repair   --subject <s> --dir <dir> --view side|front|rear|top [--gen gemini|gpt] [--draft mirror|proportion] [--dry] [--owner-override \"<words>\"]",
  "       node scripts/v7/turnaround.mjs rejudge  --subject <s> --dir <dir> --repair <repair id> [--again]",
  "       node scripts/v7/turnaround.mjs verdict  --subject <s> --dir <dir> --repair <repair id> --revert --why \"<the feature error>\" | --keep --ruling \"<the audit ruling>\"",
  "       node scripts/v7/turnaround.mjs status   --subject <s> --dir <dir> [--loo] [--blobs] [--mark <label>]",
  "       node scripts/v7/turnaround.mjs fix      --subject <s> --dir <dir> --view <v> --image <edited png> --why \"<the feature fixed>\" [--rects \"x0,y0,x1,y1;...\"]",
  "       node scripts/v7/turnaround.mjs families --subject <s> [--dir <out dir>] [--views-dir <images>] [--apply]",
  "       node scripts/v7/turnaround.mjs renorm   --subject <s> --dir <dir> --attempt attempt-<k> [--mirror <view,...>] [--keep-main <px>] [--why <text>]",
  "       node scripts/v7/turnaround.mjs prompt   --subject <s> [--view <v> [--draft mirror|proportion]]",
  "       node scripts/v7/turnaround.mjs install  --subject <s> --dir <dir> [--force] [--dry] [--note \"<README paragraph>\"]",
  "       node scripts/v7/turnaround.mjs sheet    --subject <s>",
].join("\n");

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const a = parseArgs(rest, ["dry", "loo", "blobs", "force", "rechoose", "help", "apply", "revert", "again", "keep", "allow-gemini"]);
  const log = (l) => console.log(l);
  if (!cmd || a.help || !a.subject || a.subject === true) { console.log(USAGE); return cmd ? 3 : 0; }
  switch (cmd) {
    case "gen": if (!a.out || a.out === true) break; return cmdGen(a, log);
    case "repair": if (!a.dir || a.dir === true || !a.view) break; return cmdRepair(a, log);
    case "status": if (!a.dir || a.dir === true) break; return cmdStatus(a, log);
    case "rejudge": if (!a.dir || a.dir === true || !a.repair || a.repair === true) break; return cmdRejudge(a, log);
    case "verdict": if (!a.dir || a.dir === true || !a.repair || a.repair === true) break; return cmdVerdict(a, log);
    case "families": return cmdFamilies(a, log);
    case "fix": if (!a.dir || a.dir === true || !a.view) break; return cmdFix(a, log);
    case "renorm": if (!a.dir || a.dir === true || !a.attempt || a.attempt === true) break; return cmdRenorm(a, log);
    case "prompt": return cmdPrompt(a, log);
    case "install": if (!a.dir || a.dir === true) break; return cmdInstall(a, log);
    case "sheet": log(`[turnaround] wrote ${rel(await buildSheet(a.subject))}`); return 0;
    default: break;
  }
  console.log(USAGE);
  return 3;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((c) => { process.exitCode = c; }).catch((e) => { console.error(`[turnaround] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 2; });
}
