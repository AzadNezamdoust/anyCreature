#!/usr/bin/env node
// DEPRECATED for vehicles (WORKFLOW v4 V4-3): scripts/loop.mjs (FIT -> BUILD -> re-FIT -> LOOP) replaces the P0-P3
// passes, the K=1 repair and the review rows there. Still live for the building until template-building emits KNOBS.
// The authoring runner (V2-TEST-PLAN §4). One pass = one author seat, one item,
// one gate, at most one repair, two stills, one measurement row.
//
//   node scripts/pass.mjs <P> [--subject <id>] [--seat codex|relay|fake]
//                             [--seat-mode text|agent] [--dry] [--item "<text>"] [--no-repair] [--gate-only]
//
//   <P>          0..4, or "P0".  Reads its item from the subject's passes.json.
//   --subject    subject id (subjects/<id>/subject.json); LLMM_SUBJECT, else the default.
//   --seat       seat adapter under scripts/seats/ (default opus = relay answered by an Opus agent; GPT seats (codex/terra/luna) are for blind TESTS only — owner 2026-09-26).
//   --seat-mode  text (default): the prompt carries everything, the seat replies with
//                the whole module in one ```js fence and the harness writes it.
//                agent: the seat edits the module file itself (the pre-V3 behaviour).
//   --item       override the item text (the dry pass uses this to ask a question).
//   --dry        tell the seat NOT to edit anything and to answer the item in its
//                final message. Skips the repair. Still captures, from the
//                UNCHANGED module — the point is to prove the images reached the
//                model and to price one pass, not to change the model.
//   --no-repair  gate once; never spawn the repair seat.
//   --prompt-only [--prompt-out <file>]  WF-BLIND-R1: preflight + assemble the author prompt, call no seat,
//                write nothing under outDir; the prompt goes to <file> (else stdout).
//
// WF-BLIND-R1 B6: every attempt (seat reply, repair, revert re-measure) keeps its evidence under
// <outDir>/P<N>/attempt-<k>/; the top-level files keep today's names for the FINAL attempt.
//
// Order: prompt -> seat -> (text: write fence) -> check-module -> kernel chain ->
// capture -> likeness -> (repair) -> write <outDir>/P<N>/ -> measure.mjs.
// Everything below the gate is written even when the gate fails, because a
// failed pass is the thing Fable has to read.
//
// The Codex invocation and its reasons moved verbatim to scripts/seats/codex.mjs.
// A seat that drops its transport or times out exits 2 BEFORE anything is
// counted: no measurement row, no repair spent.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import * as chain from "../src/validate/kernel-chain.mjs";
import { createHash } from "node:crypto";
import { loadSubject, subjectIdFromArgv } from "./subject.mjs";
import { readBacklog, recordMissingKeys, refusedKeys, backlogLines } from "./missing-keys.mjs";
// WORKFLOW v4 V4-3: seat I/O moved to seat-io.mjs (shared with loop.mjs); re-exported here unchanged.
import {
  SeatTransportError, SEAT_ALIASES, SEATS, SEAT_MODES, TEXT_CONTRACT, EDIT_CONTRACT, applyLineEdits, autoFixPaletteZones,
  loadSeat, seatOutcome, SYNTAX_FAIL_PREFIX, moduleSyntaxError, syntaxFollowUpPrompt, sumUsage, moduleFrame as frameOf,
} from "./seat-io.mjs";
export {
  SeatTransportError, SEAT_ALIASES, SEATS, SEAT_MODES, TEXT_CONTRACT, EDIT_CONTRACT, applyLineEdits, autoFixPaletteZones,
  seatOutcome, SYNTAX_FAIL_PREFIX, moduleSyntaxError, syntaxFollowUpPrompt, sumUsage,
};
/** WF-BLIND-R2 C3 — the start module's layout frame (seat-io.mjs moduleFrame), defaulting to this run's subject. */
export const moduleFrame = (parts, subject = S()) => frameOf(parts, subject);

const { validateParts, DEFAULT_LIMITS } = chain;

/**
 * WORKFLOW-V3 §7.4 — a REFUSAL is deterministic (unsolved camera, layout that is
 * not the target's, an item citing an unmeasured key): retrying it spends
 * nothing and fixes nothing. It exits 3; transport failures (a Codex drop, a
 * server that is down) stay exit 2 and are the only thing worth a retry.
 *   exit 0 PASS / ACCEPTED_WITH_RESIDUALS · 1 FAIL / REVIEW_PENDING · 2 retryable · 3 refusal
 */
export class RefusalError extends Error {}

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "..");                 // hard_surface
const REPO_ROOT = path.resolve(ROOT, "..", "..", "checkout"); // D:/Git/checkout (BlindLoop)

const SEAT_TIMEOUT_MS = Number(process.env.LLMM_CODEX_TIMEOUT_MS || 15 * 60 * 1000);

const DEV_SERVER = "http://127.0.0.1:4210/";
const VIEWS = ["target", "threeQuarter"];
// Owner 2026-09-25: the author seat sees the LIT three-quarter still (shape reads); likeness measures the flat ones.
const SHADED_VIEWS = ["threeQuarter"];
const seatStill = (dir, view) => {
  const lit = path.join(dir, `${view}-shaded.png`);
  return SHADED_VIEWS.includes(view) && fs.existsSync(lit) ? lit : path.join(dir, `${view}.png`);
};

const rel = (file) => path.relative(ROOT, file).replace(/\\/g, "/");

/** The subject this run works on: set by main() from argv, else `--subject`/LLMM_SUBJECT/default. */
let SUBJ = null;
export const S = () => SUBJ ?? (SUBJ = loadSubject(subjectIdFromArgv()));

// ---------------------------------------------------------------------------
// Arguments
// ---------------------------------------------------------------------------

export function parseArgs(argv) {
  const options = { pass: null, dry: false, item: null, repair: true, seat: "opus", seatMode: "text", promptOnly: false, promptOut: null };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--dry") options.dry = true;
    else if (arg === "--gate-only") options.gateOnly = true;   // re-gate + capture the module as it is; no seat
    else if (arg === "--prompt-only") options.promptOnly = true;   // WF-BLIND-R1: assemble the prompt, call no seat, write nothing under outDir
    else if (arg === "--prompt-out") options.promptOut = argv[++i];
    else if (arg === "--no-repair") options.repair = false;
    else if (arg === "--item") options.item = argv[++i];
    else if (arg === "--subject") i += 1;                       // read by subjectIdFromArgv
    else if (arg === "--seat") options.seat = argv[++i];
    else if (arg === "--seat-mode") options.seatMode = argv[++i];
    else if (!arg.startsWith("--") && options.pass === null) options.pass = arg;
    else throw new Error(`unrecognised argument "${arg}"`);
  }
  if (options.pass === null) {
    throw new Error('usage: node scripts/pass.mjs <P> [--subject <id>] [--seat codex|relay|fake] [--seat-mode text|agent] [--dry] [--item "<text>"] [--no-repair]');
  }
  if (!SEATS.includes(options.seat)) throw new Error(`--seat must be one of ${SEATS.join("|")} (got "${options.seat}")`);
  if (!SEAT_MODES.includes(options.seatMode)) throw new Error(`--seat-mode must be text|agent (got "${options.seatMode}")`);
  const n = Number(String(options.pass).replace(/^P/i, ""));
  if (!Number.isInteger(n) || n < 0) throw new Error(`<P> must be a pass number like 0 or P0 (got "${options.pass}")`);
  options.n = n;
  options.label = `P${n}`;
  return options;
}

// ---------------------------------------------------------------------------
// Prompt
// ---------------------------------------------------------------------------


// WF-BLIND-R1 B5 — the touches/embed policy is stated ONCE, in the kernel README's Contact section.
const CONTACT_RULE = "- A part that touches nothing and stands on nothing fails the gate; contact, seating and `touches` follow the "
  + "Contact section of the kernel API above.";

/** WF-BLIND-R1 B5 — replaces "no literal vertex arrays", which contradicted the documented profile points. */
export const ARRAY_RULE = "No raw 3D mesh vertices or indices; numeric 2D profiles for K.profile.poly, K.extrude and K.revolve are allowed.";

/** WF-BLIND-R1 B2 — printed with the MEASURED NUMBERS block. */
export const MEASUREMENT_RULE = "Use supplied measurements for appearance and labelled defaults for construction; "
  + "if a required appearance dimension is absent, return MISSING KEY.";

/** The rules block, worded from V2-TEST-PLAN §4 "rules:". */
export function rulesBlock(dry, mode = "agent", moduleRel = S().rel.module) {
  const images = [
    "- Image 1 is the TARGET: it is the STYLE and the MODEL, not a trace. You are never copying pixels —",
    `  you are building the same ${S().klass}, in the same idiom, at the same proportions.`,
    "- Images 2 and 3, when present, are the current render of the module above (target view, three-quarter view).",
  ];
  if (dry && mode === "text") {
    return [
      "## Rules",
      "",
      "- Image 1 is the TARGET: it is the STYLE and the MODEL, not a trace. You are never copying pixels.",
      images[2],
      "- THIS IS A DRY PASS. Nothing you reply is applied to any file.",
      "- Answer the question in the item above in one short sentence.",
      "- End with exactly one line `CHANGE: none, dry pass`.",
      "- Do not rate your own work.",
      "",
      "Do not run commands or read files.",
    ].join("\n");
  }
  if (dry) {
    return [
      "## Rules",
      "",
      "- Image 1 is the TARGET: it is the STYLE and the MODEL, not a trace. You are never copying pixels.",
      "- Images 2 and 3, when present, are the current render of the module above (target view, three-quarter view).",
      "- THIS IS A DRY PASS. Do NOT edit any file. Do NOT run any command. Do not create, move or delete anything.",
      "- Answer the question in the item above in your final message, in one short sentence.",
      "- End your final message with exactly one line beginning with `CHANGE: ` — for this pass it must read",
      "  `CHANGE: none, dry pass`.",
      "- Do not rate your own work.",
    ].join("\n");
  }
  const common = [
    `- Use ONLY \`K.*\` from the kernel API above. No other import. ${ARRAY_RULE}`,
    "  No `Math.random`, no `Date`, no `fetch`, no `performance`, no `process`, no `require`, no `eval`.",
    "- Everything is in METRES, and every solid is built in its own local frame and then placed with `.at()`.",
    CONTACT_RULE,
  ];
  if (mode === "text") {
    return [
      "## Rules",
      "",
      ...images,
      `- The module is \`${moduleRel}\`. The harness replaces it with the module you return; no other file changes.`,
      ...common,
      "- The harness runs check-module, the validator chain, the capture and the likeness on what you return.",
      "- Do not rate your own work and do not describe your result beyond the CHANGE clause.",
      "",
      TEXT_CONTRACT,
    ].join("\n");
  }
  return [
    "## Rules",
    "",
    ...images,
    `- Edit ONLY \`${moduleRel}\`. No other file may change, for any reason.`,
    ...common,
    `- Run \`node scripts/check-module.mjs ${moduleRel}\` before you finish, and fix what it reports.`,
    "- End your final message with exactly one line beginning with `CHANGE: ` describing, factually, what you changed,",
    "  then optionally one line `MISSING KEY: k1, k2`.",
    "- Do not rate your own work and do not describe your result beyond that one clause.",
  ].join("\n");
}

/** Text mode carries only the FAIL rows of the previous review, not the whole file. */
/**
 * WF-R3 R3-B item 6 — the module as the text-mode prompt shows it: whole-line comments, one-line JSDoc and trailing
 * `// ...` comments removed (a trailing comment is only cut when the code before it has balanced quotes).
 */
export function stripComments(text) {
  const out = [];
  for (const line of String(text ?? "").split(/\r?\n/)) {
    if (/^\s*\/\//.test(line) || /^\s*\/\*\*.*\*\/\s*$/.test(line)) continue;
    const m = /^(.*?\S)\s+\/\/ .*$/.exec(line);
    const code = m ? m[1] : line;
    const balanced = ["\"", "'", "`"].every((q) => (code.split(q).length - 1) % 2 === 0);
    out.push(m && balanced ? code : line);
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n");
}

export function failRows(review) {
  const rows = String(review ?? "").split(/\r?\n/).filter((l) => l.startsWith("|") && /\bFAIL\b/.test(l));
  return rows.length ? rows.join("\n") : null;
}

export function assemblePrompt({ options, item, moduleText, readme, previousReview, repairReport, likeness = null, diff = null, budget = null, acceptance = null, frame = null }) {
  const mode = options.seatMode ?? "agent";
  const subject = S();
  let readyShown = false;                    // WF-R3 R3-B item 6: a pass fed READY CALLS drops the restatements
  const blocks = [
    `# Pass ${options.label} — ${subject.id}`,
    "",
    `You are authoring one procedural module that builds a ${subject.klass} through a closed kernel API.`,
    "Everything you are allowed to use is documented below. Read it before you write anything.",
    "",
    "---",
    "",
    "# KERNEL API",
    "",
    readme,
    "",
    "---",
    "",
    `# CURRENT MODULE — ${subject.rel.module}${mode === "text" ? " (comments stripped)" : ""}`,
    "",
    "```js",
    mode === "text" ? stripComments(moduleText) : moduleText,
    "```",
    "",
    "---",
    "",
    `# THIS PASS — ${options.label}${item.title ? `: ${item.title}` : ""}`,
    "",
    item.item,
    "",
  ];

  // WF-V3 ruling (Opus 5, 2026-09-13): a text-mode seat cannot read files, so the
  // numbers the item cites travel INSIDE the prompt: every layout key the item names
  // (value, unit, tol) and the census counts due at this pass. Run 5 P0 proved the
  // need: Astra refused to invent massing.depthOverW and crown.height.
  // WF-BLIND-R1 B2: the keys come from the pass's explicit `requiredLayoutKeys` (fallback: the item's own
  // "Layout keys this pass must satisfy:" list), never from substring hits in the prose.
  if (mode === "text") {
    const layout = loadLayout() ?? {};
    const cited = requiredLayoutKeys(item);
    const census = loadCensus();
    if (cited.length || census) {
      blocks.push("---", "", "# MEASURED NUMBERS (layout.json + census.json; do not invent others)", "");
      // WF-BLIND-R2 C3 — the start module's planes and every cited key in author-frame METRES, off its measured massing.
      if (frame) {
        blocks.push(frame.planes
          ? `- start module planes (author frame, metres): ${frame.planes}`
          : "- start module planes: none yet — this pass builds the massing that fixes W and H");
      }
      // WF-R3 R3-B items 3 + 6 — READY CALLS: the metres are already in the arguments; the keys a call carries are
      // not restated below (the gate rows still name them).
      const ready = frame && typeof frame.ready === "function" ? frame.ready(layout, cited, gateTokens(subject.cls).MIN_FEAT) : [];
      const carried = new Set(ready.flatMap((c) => c.keys));
      if (ready.length) {
        readyShown = true;
        blocks.push("READY CALLS — paste each before `return parts;` (every argument is a measured key in metres):", "```js");
        for (const c of ready) blocks.push(`// ${c.what}: ${c.keys.join(", ")}`, c.call);
        blocks.push("```");
      }
      for (const k of cited) {
        if (carried.has(k)) continue;
        const e = layout[k];
        if (!e || typeof e !== "object") { blocks.push("- " + k + ": ABSENT (not in layout.json)"); continue; }
        if (e.unverified) { blocks.push("- " + k + ": UNVERIFIED (" + (e.reason ?? "no measurement") + ")"); continue; }
        const v = Array.isArray(e.values) ? e.values.join(" / ")
          : (e.value !== undefined ? e.value : [e.min, e.max].filter((x) => x !== undefined).join(".."));
        const tol = e.tol !== undefined && e.tol !== null ? " (tol +-" + e.tol + ")" : "";
        const abs = frame && typeof frame.absolute === "function" ? frame.absolute(k, e) : null;
        blocks.push("- " + k + ": " + v + " " + (e.unit ?? "") + tol + (abs ? " -> " + abs : ""));
      }
      if (census) blocks.push("- census due now: " + Object.entries(census).map(([k, v]) => k + " " + v).join(", "));
      // WF-R3 R3-B item 6 — when every cited key rides a READY call there is nothing left to multiply.
      if (cited.some((k) => !carried.has(k))) blocks.push("", subject.cls.layoutUnits ?? "W is your massing's x extent and H its y extent: a value in W or H multiplies those. Fix W and H once, in P0.");
      blocks.push("");
      if (cited.some((k) => !carried.has(k))) blocks.push(MEASUREMENT_RULE, "");
    }
  }

  // WF-BLIND-R1 B2: labelled numbers for non-appearance construction (recess depth, seat overlap, ...).
  const defaults = Object.entries(item.constructionDefaults ?? {});
  if (defaults.length) {
    blocks.push("---", "", "# CONSTRUCTION DEFAULTS (labelled construction numbers, not target measurements)", "");
    for (const [name, d] of defaults) blocks.push(`- ${name}: ${d.value} ${d.unit ?? ""}`.trimEnd() + (d.why ? ` — ${d.why}` : ""));
    blocks.push("");
  }

  // WF-BLIND-R1 B4: the likeness acceptance, before the attempt, from the same config the rows read.
  if (acceptance) blocks.push("---", "", acceptance.trim(), "");

  // WF-V3 (Opus 5, 2026-09-13): the author sees the triangle budget left. The building
  // v3 proof failed V10 by 4 triangles because nothing told the seat what was already spent.
  if (budget && Number.isFinite(budget.used) && Number.isFinite(budget.cap)) {
    const left = budget.cap - budget.used;
    blocks.push("---", "", "# TRIANGLE BUDGET", "",
      "- the current module uses " + budget.used + " of " + budget.cap + " triangles; everything you add or change must fit in the remaining " + left + ".",
      ...(readyShown ? [] : ["- prefer K.assemble.* helpers, low revolve/arch segment counts, and K.repeat over hand-placed copies."]), "");
  }

  // WF-BLIND-R1 B3: a missing review is UNREVIEWED, never read as a clean one.
  if (options.n > 0) {
    const review = mode === "text" ? failRows(previousReview) : previousReview;
    if (previousReview === null || previousReview === undefined) {
      blocks.push("---", "", `PREVIOUS REVIEW: UNREVIEWED — no review.md of P${options.n - 1}'s module exists, so its LOOK rows were never judged; `
        + "nothing about the previous pass's look is known to be clean.", "");
    } else if (!review) {
      blocks.push("---", "", "PREVIOUS REVIEW: no failed rows", "");
    } else {
      const heading = mode === "text" ? `# FAILED LOOK ROWS OF THE PREVIOUS PASS (P${options.n - 1})` : `# REVIEW OF THE PREVIOUS PASS (P${options.n - 1})`;
      blocks.push("---", "", heading, "", review.trim(), "");
    }
  }

  if (repairReport) {
    blocks.push(
      "---",
      "",
      "# VALIDATOR REPORT ON WHAT YOU JUST WROTE",
      "",
      "```",
      repairReport.trim(),
      "```",
      "",
      "Fix only this. Change nothing else: no new features, no tidying, no renaming.",
      "",
    );
  }

  // Text-mode repair: the module above is already the seat's own output, so the
  // seat is shown WHAT it changed as a diff instead of a second copy of the module.
  if (diff) {
    blocks.push("---", "", "# WHAT YOUR LAST REPLY CHANGED (unified diff against the module before this pass)", "", "```diff", diff.trim(), "```", "");
  }

  // r2 A5 / audit C9 — the author finally sees its OWN render. Images 2 and 3 of
  // a repair call are this pass's stills, not the previous pass's, and the table
  // below is the measured difference between them and Image 1.
  if (likeness) {
    blocks.push(
      "---",
      "",
      "# LIKENESS OF WHAT YOU JUST WROTE, MEASURED AGAINST IMAGE 1",
      "",
      "Images 2 and 3 are YOUR render of the module above, at the judged camera and",
      "at three-quarter. Every number below is a script comparing those pixels with",
      "the target's; a FAIL row is as blocking as a validator row.",
      "",
      "```",
      likeness.text.trim(),
      "```",
      "",
      likeness.table.trim(),
      "",
      "Reopen whichever parameter is responsible — palette hex, a dimension, a",
      "position — and change nothing else.",
      "",
    );
  }

  let rules = rulesBlock(options.dry, mode, subject.rel.module);
  // WF-R3 R3-B item 6 — the contact rule points at the Contact section; a pass whose readme skips it (the helpers seat
  // by construction) drops the pointer.
  if (!String(readme ?? "").includes("## Contact")) rules = rules.split("\n").filter((l) => l !== CONTACT_RULE).join("\n");
  blocks.push("---", "", rules);
  return blocks.join("\n");
}

/**
 * WORKFLOW-V3 §7.2 — prompt numbers come from the config the GATE reads, never
 * from prose: "0.04 m bars" against MIN_FEAT 0.06 cost run 4 171 V5 rows.
 * `{MIN_FEAT}` is the style floor; every numeric KERNEL_LIMIT_DEFAULTS key is
 * `{SNAKE_CASE}` (`bearingSpan` -> `{BEARING_SPAN}`); every numeric limits.json
 * v7 band is its upper-cased name (`{PARAPET_H}`). Bands render `lo–hi`.
 */
export function gateTokens(cls = S().cls, moduleText = "") {
  // WF-BLIND-R2 C14 — the class prior's gate configuration is the ONE source; the module text never picks the floor.
  void moduleText;
  const gate = chain.gateConfig(cls);
  const tokens = { MIN_FEAT: gate.minFeat };
  const useful = (v) => typeof v === "number" || (Array.isArray(v) && v.every((x) => typeof x === "number"));
  const snake = (k) => k.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toUpperCase();
  for (const [k, v] of Object.entries(gate.kernel ?? {})) if (useful(v)) tokens[snake(k)] = v;
  for (const [k, v] of Object.entries(gate.v7 ?? {})) if (useful(v)) tokens[k.toUpperCase()] = v;
  // WF-BLIND-R2 C9 — the thinnest panel a groove of GROOVE_DEPTH_MAX may be cut into.
  tokens.MIN_PANEL = Math.round((tokens.MIN_FEAT + (tokens.GROOVE_DEPTH_MAX ?? 0)) * 1000) / 1000;
  // WF-BLIND-R2 C4/C10 — the closed palette zone list, beside the closed role list.
  tokens.PALETTE_ZONE_LIST = paletteZoneList(cls);
  tokens.GATE_DIGEST = gate.digest;
  return tokens;
}

/** WF-BLIND-R2 C4/C10 — the class's author palette keys, one per material, with what each paints. */
export function paletteZoneList(cls) {
  const zones = (cls?.paletteZones ?? []).filter((z) => z.closure !== true);
  if (zones.length === 0) return "";
  return [
    "## Palette zones — a CLOSED list",
    "",
    "Every part's `zone` is one of these keys, and `meta.palette` carries each key you use. The harness calibrates every",
    "key from the target after you reply (the hex you type is replaced), so choose the key by MATERIAL; a zone outside",
    "this list is never calibrated and fails `PALETTE_ZONE`.",
    ...zones.map((z) => `- \`${z.key}\` — ${z.for ?? z.region}`),
  ].join("\n");
}

/** WF-BLIND-R2 C14 — prompt, kernel and report must have measured under one configuration; anything else is a harness error. */
export function assertGateDigest(digests) {
  const values = Object.values(digests);
  if (values.some((d) => typeof d !== "string" || d === "") || new Set(values).size !== 1) {
    throw new RefusalError(`gate configuration mismatch: ${Object.entries(digests).map(([k, v]) => `${k} ${v ?? "none"}`).join(", ")} — `
      + "the prompt, the kernel's cut check and the validator must read ONE configuration (kernel-chain gateConfig); "
      + "this is a harness error and no author seat or repair is spent on it");
  }
  return values[0];
}

// ---------------------------------------------------------------------------
// WF-BLIND-R2 C12 — an appearance instruction no gate or likeness row checks is not a requirement (blind Gemini
// built a solid grille and passed; Terra built the slots and crashed). passes.json `instructionRows` maps item
// sentences to the rows that check them; the examiner (never the author) is warned about the rest.
// ---------------------------------------------------------------------------

export function itemSentences(text) {
  return String(text ?? "").split(/(?<=[.!?])\s+(?=[A-Z(])/).map((s) => s.trim()).filter(Boolean);
}

const ROW_ID = /^(V\d+[A-Z_]*|VEH_[A-Z_]+|LK_[A-Z_]+|PALETTE_ZONE|LOOK)(:.+)?$/;

/** @returns {{rows: Array<{sentence:string, rows:string[], exempt:string|null}>, warnings: string[]}} */
export function instructionCoverage(item, { layoutRules = {}, census = null } = {}) {
  const map = Array.isArray(item?.instructionRows) ? item.instructionRows : [];
  const sentences = itemSentences(item?.item);
  const label = item?.id ?? "item";
  const rows = sentences.map((sentence) => {
    const hits = map.filter((m) => typeof m.match === "string" && sentence.includes(m.match));
    return { sentence, rows: [...new Set(hits.flatMap((m) => m.rows ?? []))], exempt: hits.find((m) => m.exempt)?.exempt ?? null };
  });
  const warnings = [];
  for (const r of rows) {
    if (r.rows.length === 0 && !r.exempt) {
      warnings.push(`${label}: no gate or likeness row checks "${r.sentence.length > 120 ? `${r.sentence.slice(0, 120)}…` : r.sentence}"`);
    }
  }
  for (const m of map) {
    if (!sentences.some((s) => s.includes(m.match))) warnings.push(`${label}: instructionRows match "${m.match}" is in no item sentence`);
    for (const row of m.rows ?? []) {
      if (!ROW_ID.test(row)) { warnings.push(`${label}: "${row}" is not a row id`); continue; }
      const [code, key] = row.split(":");
      if (code === "V12_LAYOUT" && key && !Object.hasOwn(layoutRules, key)) warnings.push(`${label}: no V12_LAYOUT rule measures "${key}"`);
      if (code === "V12_CENSUS" && key && census && !Object.hasOwn(census, key)) warnings.push(`${label}: census.json has no "${key}"`);
    }
  }
  return { rows, warnings };
}

// ---------------------------------------------------------------------------
// WF-BLIND-R2 C1 — a repair that trades one gate code for another is worse, even at equal row counts.
// ---------------------------------------------------------------------------

export function repairVerdict(before, after) {
  const rowCount = (r, lk) => ({
    gate: r.pass ? 0 : Math.max(1, r.report?.violations?.length ?? 1),
    likeness: lk && !lk.pass ? Math.max(1, lk.result?.violations?.length ?? 1) : 0,
  });
  // A module that does not even load (check-module rejection or a reply with no module) is worse than ANY module
  // that loads: blind Gemini pickup P1 repair returned one that threw, and the old row count (1 = 1) let it stand.
  const broken = (r) => /check-module rejected|SEAT_CONTRACT|SEAT_SYNTAX/.test(String(r.report?.text ?? ""));
  const rank = (r) => (broken(r) ? 2 : (r.pass ? 0 : 1));
  const codes = (r) => new Set((r.report?.violations ?? []).map((v) => v.v));
  const b = rowCount(before.result, before.likeness);
  const a = rowCount(after.result, after.likeness);
  const beforeCodes = codes(before.result);
  const introduced = [...codes(after.result)].filter((c) => !beforeCodes.has(c));
  const worse = rank(after.result) > rank(before.result)
    || (rank(after.result) === rank(before.result) && (a.gate > b.gate
      || (introduced.length > 0 && a.gate >= b.gate)
      || (a.gate === b.gate && a.likeness > b.likeness)));
  return { worse, before: b, after: a, introduced };
}

export function resolveTokens(text, tokens) {
  return String(text ?? "").replace(/\{([A-Z][A-Z0-9_]*)\}/g, (_, name) => {
    if (!Object.hasOwn(tokens, name)) {
      throw new Error(`unknown prompt token {${name}} — tokens come from the gate config: ${Object.keys(tokens).join(", ")}`);
    }
    const v = tokens[name];
    return Array.isArray(v) ? v.join("–") : String(v);
  });
}

/**
 * WF-BLIND-R1 B5 — README sections wrapped in `<!-- class:a,b -->` ... `<!-- /class -->` reach only
 * authors of those classes; the marker lines never reach anyone.
 */
export function filterClassSections(text, klass, pass = null) {
  const out = [];
  let keep = true;
  let skip = false;
  for (const line of String(text ?? "").split(/\r?\n/)) {
    const open = /^<!--\s*class:\s*([\w,\s]+?)\s*-->\s*$/.exec(line);
    if (open) { keep = open[1].split(",").map((s) => s.trim()).includes(klass); continue; }
    if (/^<!--\s*\/class\s*-->\s*$/.test(line)) { keep = true; continue; }
    // WF-R3 R3-B item 6 — `<!-- skip: vehicle/P1, ... -->` ... `<!-- /skip -->`: a section that pass does not need.
    const skipOpen = /^<!--\s*skip:\s*([\w/,\s]+?)\s*-->\s*$/.exec(line);
    if (skipOpen) { skip = pass !== null && skipOpen[1].split(",").map((s) => s.trim()).includes(`${klass}/${pass}`); continue; }
    if (/^<!--\s*\/skip\s*-->\s*$/.test(line)) { skip = false; continue; }
    if (keep && !skip) out.push(line);
  }
  return out.join("\n");
}

/** Kernel API core (class-filtered) + the class's author rules, tokens resolved. */
export function authorReadme(tokens, subject = S(), pass = null) {
  const klass = subject.klass ?? subject.cls?.class;
  const parts = [filterClassSections(fs.readFileSync(path.join(ROOT, "src", "kernel", "README.md"), "utf8"), klass, pass)];
  const classRules = subject.cls.authorRules ? path.join(ROOT, subject.cls.authorRules) : null;
  if (classRules && fs.existsSync(classRules)) parts.push(filterClassSections(fs.readFileSync(classRules, "utf8"), klass, pass));
  return resolveTokens(parts.join("\n\n"), tokens).replace(/\n{3,}/g, "\n\n");
}

// ---------------------------------------------------------------------------
// Seat
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// WF-R3 R3-B item 6 — the REPAIR prompt diet. The blind repairs re-sent the whole kernel API, the whole module AND a
// diff (Luna P1: 46 kB). A repair now carries the failing rows, the READY CALLS, the numbered module lines near what
// failed (and every line the seat changed), and the diff when it fits: at most REPAIR_SHARE of the first prompt. The
// seat answers with line edits (```js replace A-B) or the complete module; applyLineEdits turns edits into the module.
// ---------------------------------------------------------------------------

export const REPAIR_SHARE = 0.6;

/** 1-based line numbers of `after` that differ from `before` (a plain LCS walk; modules are a few hundred lines). */
function changedLines(before, after) {
  const a = String(before ?? "").split(/\r?\n/);
  const b = String(after ?? "").split(/\r?\n/);
  const n = a.length;
  const m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i -= 1) for (let j = m - 1; j >= 0; j -= 1) dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out = [];
  let i = 0;
  let j = 0;
  while (j < m) {
    if (i < n && a[i] === b[j]) { i += 1; j += 1; } else if (i < n && dp[i + 1][j] >= dp[i][j + 1]) { i += 1; } else { out.push(j + 1); j += 1; }
  }
  return out;
}

/** The failing rows only: validator violation lines + likeness FAIL rows (no tables, no passes). */
export function failingRowLines(report, likeness) {
  const lines = [];
  for (const v of report?.violations ?? []) lines.push(`${v.v} ${v.part ?? ""}: ${v.hint} (measured ${v.measured}, limit ${v.limit})`.replace(/ {2,}/g, " "));
  if (lines.length === 0 && report?.text && !report.pass) lines.push(...String(report.text).split(/\r?\n/).filter((l) => l.trim()).slice(0, 12));
  for (const r of likeness?.result?.violations ?? likeness?.violations ?? []) lines.push(`${r.v} ${r.part}: ${r.measured} (limit ${r.limit}) — ${r.hint}`);
  return lines;
}

/**
 * @param {{options, item, moduleText, moduleBefore, report, likeness, ready: Array<{what, keys, call}>, firstBytes: number}} o
 * @returns {string} the repair prompt, <= REPAIR_SHARE x firstBytes whenever the failing rows themselves fit.
 */
export function assembleRepairPrompt({ options, item, moduleText, moduleBefore, report, likeness = null, ready = [], firstBytes, diff = null }) {
  const subject = S();
  const rows = failingRowLines(report, likeness);
  const lines = String(moduleText ?? "").split(/\r?\n/);
  const ids = new Set();
  for (const v of [...(report?.violations ?? []), ...(likeness?.result?.violations ?? likeness?.violations ?? [])]) {
    if (v.part) ids.add(String(v.part));
    for (const m of String(v.hint ?? "").matchAll(/"([\w.-]+)"/g)) ids.add(m[1]);
  }
  const changed = new Set(changedLines(moduleBefore, moduleText));
  const hit = (l) => [...ids].some((id) => id.length > 2 && l.includes(id));
  const budget = Math.floor(REPAIR_SHARE * firstBytes);
  const build = (context, withDiff, withChanged) => {
    const keep = new Set();
    lines.forEach((l, i) => {
      if (hit(l) || (withChanged && changed.has(i + 1))) for (let d = -context; d <= context; d += 1) if (i + d >= 0 && i + d < lines.length) keep.add(i + d);
    });
    const width = String(lines.length).length;
    const numbered = [];
    let last = -2;
    for (const i of [...keep].sort((x, y) => x - y)) {
      if (i !== last + 1) numbered.push(`${" ".repeat(width)}| …`);
      numbered.push(`${String(i + 1).padStart(width)}| ${lines[i]}`);
      last = i;
    }
    const blocks = [
      `# Pass ${options.label} — ${subject.id} — REPAIR`,
      "",
      `Your last reply (the module in ${subject.rel.module}, ${lines.length} lines) fails the rows below; Images 2 and 3 are its render,`,
      "Image 1 the target. Fix only these rows: no new features, no tidying, no renaming.",
      "",
      "# FAILING ROWS",
      "",
      "```",
      ...rows,
      "```",
      "",
    ];
    if (ready.length) blocks.push("# READY CALLS (measured, metres)", "", "```js", ...ready.map((c) => c.call), "```", "");
    if (withDiff && diff) blocks.push("# WHAT YOUR LAST REPLY CHANGED (diff against the start module)", "", "```diff", diff.trim(), "```", "");
    blocks.push("# YOUR MODULE — the lines that failed and the lines you changed, numbered", "", "```js", ...numbered, "```", "", EDIT_CONTRACT);
    return blocks.join("\n");
  };
  for (const [context, withDiff, withChanged] of [[2, true, true], [2, false, true], [1, false, true], [0, false, true], [1, false, false], [0, false, false]]) {
    const text = build(context, withDiff, withChanged);
    if (Buffer.byteLength(text, "utf8") <= budget) return text;
  }
  return build(0, false, false);
}

export const CONTRACT_FAIL_TEXT = "FAIL: SEAT_CONTRACT — the reply had no ```js fence, so no module was applied. "
  + "Reply with the COMPLETE module in one ```js fence.";

/** Text mode: write the reply's fence over the module. Returns the contract FAIL text, or null. */
export function applySeat(seat, options, modulePath) {
  if (options.dry || options.seatMode !== "text") return null;
  if (seatOutcome(seat) === "contract" || !seat.artifact) return CONTRACT_FAIL_TEXT;
  fs.writeFileSync(modulePath, `${seat.artifact.replace(/\s+$/, "")}\n`);
  console.log(`[seat] wrote ${rel(modulePath)} from the reply's js fence (${seat.artifact.length} chars)`);
  return null;
}

/**
 * Text mode with a syntax pre-check: the fence is parsed BEFORE it is written live.
 * An unparseable fence gets ONE syntax-only follow-up through `retry(prompt)` (a fresh
 * call to the same seat; not the pass's repair). Still unparseable: nothing is written,
 * the previous module stays live and `contractText` carries a SEAT_SYNTAX row.
 * @returns {Promise<{contractText:string|null, syntaxRetries:number, followUp:object|null}>}
 */
export async function applySeatChecked(seat, options, modulePath, { retry, tag = "seat" } = {}) {
  const out = { contractText: null, syntaxRetries: 0, followUp: null };
  if (options.dry || options.seatMode !== "text") return out;
  if (seatOutcome(seat) === "contract" || !seat.artifact) return { ...out, contractText: CONTRACT_FAIL_TEXT };
  const first = moduleSyntaxError(seat.artifact);
  if (!first) {
    applySeat(seat, options, modulePath);
    return out;
  }
  console.log(`[syntax] ${tag}: the reply's module does not parse (${first}) — one syntax-only follow-up to the same seat`);
  out.syntaxRetries = 1;
  const followUp = await retry(syntaxFollowUpPrompt(first, seat.artifact));
  out.followUp = followUp;
  seatOutcome(followUp, `${tag}-syntax`);     // transport / timeout: exit 2, as for any seat
  const second = followUp.artifact ? moduleSyntaxError(followUp.artifact) : "the follow-up reply had no ```js fence";
  if (!second) {
    console.log(`[syntax] ${tag}: the follow-up parses — applied`);
    applySeat(followUp, options, modulePath);
    return out;
  }
  console.log(`[syntax] ${tag}: still does not parse (${second}) — the previous module stays live (SEAT_SYNTAX)`);
  out.contractText = `${SYNTAX_FAIL_PREFIX} — the module did not parse (${second}) after one syntax-only follow-up, `
    + "so it was not applied and the previous module stays live. Reply with the COMPLETE module in one ```js fence that parses.";
  return out;
}

export function withContractFail(result, text) {
  const row = String(text).startsWith(SYNTAX_FAIL_PREFIX)
    ? { v: "SEAT_SYNTAX", part: null, measured: "module does not parse", limit: "a module that parses", hint: text, blocking: true }
    : { v: "SEAT_CONTRACT", part: null, measured: "no ```js fence", limit: "one fenced module", hint: text, blocking: true };
  const report = result.report ?? {};
  return {
    ...result,
    pass: false,
    report: { ...report, pass: false, violations: [row, ...(report.violations ?? [])], text: `${text}\n${report.text ?? ""}`.trim() },
  };
}

/** Unified diff of two module texts (git diff --no-index), for the text-mode repair prompt. */
export function unifiedDiff(before, after, label = "module") {
  if (before === after) return "(no change)";
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "llmm-diff-"));
  try {
    const a = path.join(dir, "before.mjs");
    const b = path.join(dir, "after.mjs");
    fs.writeFileSync(a, before);
    fs.writeFileSync(b, after);
    const r = spawnSync("git", ["diff", "--no-index", "--no-color", "--unified=2", a, b], { encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
    const body = String(r.stdout ?? "").split(/\r?\n/).filter((l) => !/^(diff --git|index |--- |\+\+\+ )/.test(l)).join("\n").trim();
    return body ? `--- ${label} (before)\n+++ ${label} (after)\n${body}` : "(diff unavailable)";   // MVP-STUB: needs git on PATH
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// Gate
// ---------------------------------------------------------------------------

function runCheckModule() {
  const result = spawnSync(process.execPath, [path.join(ROOT, "scripts", "check-module.mjs"), S().rel.module], {
    cwd: ROOT, encoding: "utf8", maxBuffer: 8 * 1024 * 1024,
  });
  const text = `${result.stdout ?? ""}${result.stderr ?? ""}`.trim();
  return { pass: result.status === 0, text };
}

/** The digest the prompt advertised (main sets it from gateTokens); null before the prompt exists. */
let PROMPT_DIGEST = null;

/** Fresh import every time: a repair rewrites the file inside this process. */
async function buildAndValidate() {
  await K.init();
  // WF-BLIND-R2 C14 — the kernel's cut check reads the subject's class floor BEFORE build().
  K.configure(chain.gateConfig(S().cls));
  const url = `${pathToFileURL(S().paths.module).href}?v=${process.hrtime.bigint()}`;
  const mod = await import(url);
  K.resetCounters();
  const buildStarted = Date.now();
  const parts = mod.build();
  const kernelBuildMs = Date.now() - buildStarted;
  const booleans = K.counters.booleans;
  // r1 row 4 — V12 measures against the frozen census, or stands down without it.
  // WORKFLOW-V3 §7.10 — the subject's OWN class rules (building, vehicle, …), never the building fallback.
  const rules = await import(pathToFileURL(path.join(ROOT, S().cls.rules)).href);
  const report = await validateParts(mod.meta, parts, undefined, { census: loadCensus(), layout: loadLayout(), cls: S().cls, rules });   // r2 B2
  const gateDigest = assertGateDigest({ ...(PROMPT_DIGEST ? { prompt: PROMPT_DIGEST } : {}), kernel: K.config().digest, report: report.measurements?.gateDigest });
  return { report, kernelBuildMs, booleans, parts, meta: mod.meta, gateDigest };
}

async function gate() {
  const check = runCheckModule();
  console.log(check.text);
  if (!check.pass) {
    return {
      pass: false,
      checkText: check.text,
      report: { pass: false, violations: [], advisories: [], text: `FAIL: check-module rejected the module.\n${check.text}`, measurements: {}, timings: {} },
      kernelBuildMs: 0, booleans: 0,
    };
  }
  const built = await buildAndValidate();
  console.log(built.report.text);
  return { pass: built.report.pass, checkText: check.text, ...built };
}

// ---------------------------------------------------------------------------
// Capture
// ---------------------------------------------------------------------------

/**
 * r1 row 12 — CAMERA PREFLIGHT. `app.js` falls back to PROVISIONAL_CAMERA with
 * nothing but a console warning when `refs/<subject>.camera.json` is missing,
 * and a whole round's stills were then framed by a camera nobody solved. A
 * pass that cannot be judged at the solved angle must not run at all.
 */
function assertCameraSolved() {
  const CAMERA_REL = S().rel.camera;
  const file = S().paths.camera;
  if (!file || !fs.existsSync(file)) {
    throw new RefusalError(`no ${CAMERA_REL}. Solve it first (\`node scripts/solve-camera.mjs\`) — `
      + "a still framed by the fallback camera cannot be compared with the target.");
  }
  let camera;
  try {
    camera = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    throw new RefusalError(`${CAMERA_REL} is not valid JSON (${error.message})`);
  }
  if (camera.provisional !== false) {
    throw new RefusalError(`${CAMERA_REL} is marked provisional:${JSON.stringify(camera.provisional)}. `
      + "Re-solve it against the target and set provisional:false — the loop does not judge a guessed angle.");
  }
  for (const key of ["theta_deg", "phi_deg"]) {
    if (!Number.isFinite(camera[key])) throw new RefusalError(`${CAMERA_REL} has no finite ${key}`);
  }
  console.log(`[camera] ${CAMERA_REL} theta=${camera.theta_deg} phi=${camera.phi_deg} residual=${camera.residual_px} px (solved)`);
  return camera;
}

// ---------------------------------------------------------------------------
// r3 C2.4 — the layout must be a MEASUREMENT before a seat may build to it
// ---------------------------------------------------------------------------

/**
 * Astra C10, verbatim. Printed at the final pass and quoted into the LOOK
 * checklist: it is the rule the row-3 reviewer is judging under.
 */
export const REVIEW_SENTENCE =
  "A numeric PASS cannot overrule a visible mismatch; cite the mismatch and reopen its parameter "
  + "or mark the measurement invalid.";

/**
 * `scripts/measure-target.mjs --check` re-measures the target and compares it
 * with the frozen layout. A FAIL means the numbers the gate is about to enforce
 * are not the target's numbers — the exact failure that cost run 3 two seats
 * (Fable C1/C6) — so the pass refuses to start. The script belongs to job C1; a
 * missing one is UNVERIFIED and the run continues with a printed warning.
 * @returns {{state:"PASS"|"FAIL"|"UNVERIFIED", text:string}}
 */
function checkMeasuredLayout() {
  // WORKFLOW-V3 §7.10 — the class names its measuring instrument; buildings keep measure-target.mjs.
  const script = path.join(ROOT, S().cls.measure ?? "scripts/measure-target.mjs");
  if (!fs.existsSync(script)) {
    console.log("[layout] UNVERIFIED: scripts/measure-target.mjs does not exist yet, so the frozen layout "
      + "has not been compared with the target. Continuing (WF-LOOP-R3 C2.4).");
    return { state: "UNVERIFIED", text: "scripts/measure-target.mjs missing" };
  }
  const result = spawnSync(process.execPath, [script, "--check", "--subject", S().id], {
    cwd: ROOT, encoding: "utf8", maxBuffer: 8 * 1024 * 1024,
  });
  const text = `${result.stdout ?? ""}${result.stderr ?? ""}`.trim();
  if (text) console.log(text);
  if (result.error) {
    console.log(`[layout] UNVERIFIED: could not run ${path.basename(script)} --check (${result.error.message}).`);
    return { state: "UNVERIFIED", text: result.error.message };
  }
  if (result.status !== 0) {
    throw new RefusalError(`${path.basename(script)} --check failed (exit ${result.status}): the frozen layout does not match `
      + `the target. Re-freeze it from the measurement before spending a seat.\n${text.slice(-800)}`);
  }
  console.log(`[layout] ${path.basename(script)} --check PASS — every frozen key is within tol of the measurement.`);
  return { state: "PASS", text };
}

/**
 * Fable M2 — a key marked `unverified` is not a pass item. The seat must not be
 * asked to build to a number nobody measured, and V12 must not enforce one.
 * @returns {string[]} the unverified keys this pass's item cites
 */
/** The "Layout keys this pass must satisfy:" list. Dot-aware: key names contain dots (`window.w`). */
export function itemLayoutKeys(itemText) {
  const named = /Layout keys this pass must satisfy:\s*([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*(?:\s*,\s*[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*)*)\./i.exec(itemText ?? "");
  return named ? named[1].split(",").map((s) => s.trim()).filter(Boolean) : [];
}

/** WF-BLIND-R1 B2 — the pass's explicit `requiredLayoutKeys`, else the item's own key list. */
export function requiredLayoutKeys(item) {
  return Array.isArray(item?.requiredLayoutKeys) ? [...item.requiredLayoutKeys] : itemLayoutKeys(item?.item);
}

/** WF-BLIND-R1 B2 — the unverified keys among the REQUIRED ones (no substring discovery in prose). */
export function unverifiedItemKeys(itemText, layout, required = null) {
  if (!layout) return [];
  const listed = Array.isArray(required) ? required : itemLayoutKeys(itemText);
  return listed.filter((key) => layout[key] && typeof layout[key] === "object" && layout[key].unverified === true);
}

/** Tokens resolved in the item text and in every constructionDefaults value / reason (values stay strings when tokens). */
export function resolveItem(item, tokens) {
  const out = { ...item, item: resolveTokens(item.item, tokens) };
  if (item.constructionDefaults) {
    out.constructionDefaults = Object.fromEntries(Object.entries(item.constructionDefaults).map(([name, d]) => [name, {
      ...d,
      value: typeof d.value === "string" ? resolveTokens(d.value, tokens) : d.value,
      ...(d.why ? { why: resolveTokens(d.why, tokens) } : {}),
    }]));
  }
  return out;
}

/** r1 row 4 — the frozen contents count, handed to V12. Absent = V12 stands down. */
let CENSUS_PASS = Infinity;   // set by main(): V12 only counts keys whose "_pass" <= current pass
function loadLayout() {
  return S().readJson("layout");
}

function loadCensus() {
  const raw = S().readJson("census");
  if (!raw) return null;
  // r1 fix (run2 P0): the census is STAGED — a key is enforced only from the pass
  // that introduces it (census._pass[key]); otherwise P0 fails on windows it is
  // forbidden to build and the K=1 repair is wasted on a workflow bug.
  const stage = raw._pass ?? {};
  const out = {};
  for (const [k, v] of Object.entries(raw)) {
    if (k.startsWith("_")) continue;
    if ((stage[k] ?? 0) <= CENSUS_PASS) out[k] = v;
  }
  return Object.keys(out).length ? out : null;
}

/**
 * r1 row 11 — the Fable LOOK checklist, cut to THREE rows by r2 A5.
 *
 * A blank row a script already measures is a blank row that wastes a reviewer
 * and invites a second opinion on a number: bearing is V11_BEARING, census is
 * V12_CENSUS, landing gap is V11_LANDING_GAP, clashes are V6_CLASH_UNDECLARED,
 * and colour/proportion/visibility are now the LK_ rows of scripts/likeness.mjs.
 * What survives is only what no script in this harness can do.
 */
const lookRows = (targetRel) => [
  ["orientation", `the populated face is the one turned toward the camera, and its horizontal edges RISE toward screen-right, as in ${targetRel}`],
  ["door side", "the shop entrance is on the same side of the storefront as the target's, and it is RECTANGULAR and glazed — there is no arch anywhere on this building"],
  ["reads as the target", "at a glance, next to compare.png, this is the same building in the same idiom — not a different building that passes every rule"],
];

function writeLookChecklist(outDir, label, gatePass, reportText, likeness, moduleHash = null) {
  const targetRel = S().rel.target;
  const lines = [
    `# LOOK checklist — ${label}`,
    "",
    // WF-R3 H1 — the review is bound to this module: review.md must carry this exact line, or it does not count.
    `module: ${moduleHash}`,
    "",
    "Copy the `module:` line above into `review.md` verbatim; a review that records another module (or none) is read",
    "as UNREVIEWED and the verdict stays REVIEW_PENDING.",
    "",
    "Fable fills the Verdict column in from `compare.png` in this directory and",
    `\`${targetRel}\`, then writes the same table into \`review.md\`. A row marked`,
    "FAIL is quoted verbatim into the next pass's prompt; the item wording already tells",
    "the author it may reopen earlier work to clear one.",
    "",
    "Only rows no script can measure are left here (r2 A5). Bearing, census, landing",
    "gap and clashes are validator rows; colour, proportion and visibility are",
    "`likeness.json`.",
    "",
    "r3 C2.4 / Astra C10 — row 3 is MANDATORY input to the verdict, and it outranks",
    "the numbers:",
    "",
    `> ${REVIEW_SENTENCE}`,
    "",
    "Judge row 3 on the TOP row of `compare.png`: the two FRONT FACES, cropped to",
    "their own face quads and scaled to the same pixels per face width W. Until row 3",
    "of `review.md` says PASS, the final pass's verdict is `PASS-numeric, review pending`.",
    "",
    `Validator gate for this pass: **${gatePass ? "PASS" : "FAIL"}**.`,
    `Likeness for this pass: **${likeness ? (likeness.pass ? "PASS" : "FAIL") : "not run"}**.`,
    "",
    "| # | Row | What passes | Verdict | Note |",
    "|---|---|---|---|---|",
    ...(S().cls.lookRows ?? lookRows(targetRel)).map(([row, what], i) => `| ${i + 1} | ${row} | ${what} |  |  |`),
    "",
    "## Validator report (measured, not looked at)",
    "",
    "```",
    (reportText ?? "").trim(),
    "```",
    "",
    "## Likeness (measured, not looked at)",
    "",
    "```",
    (likeness?.text ?? "not run").trim(),
    "```",
    "",
    likeness ? likeness.table : "",
    "",
  ];
  fs.writeFileSync(path.join(outDir, "look-checklist.md"), lines.join("\n"));
}

async function assertServerUp() {
  try {
    const response = await fetch(DEV_SERVER, { method: "GET" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
  } catch (error) {
    throw new Error(
      `no dev server at ${DEV_SERVER} (${error.message}). Start it with \`npm run dev\` in ${rel(ROOT)} `
      + "and re-run — capture.mjs refuses to invent a frame.",
    );
  }
}

// capture2 / likeness load in main() (not at import) so tests can import this
// file's pure helpers without a browser stack; main still loads them before any seat.
let capture2 = null;
let likenessMod = null;

/**
 * r2 A6 — both judged views AND the A2 id pass, one browser, one page. The
 * frames are `tools/BlindLoop/capture.mjs`'s (capture2.mjs imports its config
 * and repeats its assertions verbatim); what changed is that chromium is
 * launched once instead of once per view.
 */
async function captureViews(outDir, seed) {
  process.env.BLINDLOOP_CONFIG = process.env.BLINDLOOP_CONFIG
    || path.join(REPO_ROOT, "tools", "BlindLoop", "config.llmmodeling.json");
  const shots = capture2.passUrls({ base: DEV_SERVER, subject: S().id, seed, size: 900, views: VIEWS, shaded: SHADED_VIEWS })
    .map((s) => ({ ...s, out: path.join(outDir, `${s.name}.png`) }));
  const captures = {};
  let ms = 0;
  try {
    const result = await capture2.captureAll(shots);
    ms = result.ms;
    for (const shot of result.shots) {
      captures[shot.name] = { ok: true, ms: shot.ms, out: rel(shot.out) };
      console.log(`[capture] ${shot.name} OK ${shot.ms} ms`);
    }
  } catch (error) {
    console.log(`[capture] REFUSED: ${error.message}`);
    for (const shot of shots) if (!captures[shot.name]) captures[shot.name] = { ok: false, out: rel(shot.out) };
  }
  return { captures, ms };
}

/** r2 A5 — `target | render` side by side, written every pass. */
function writeCompare(outDir) {
  const result = spawnSync(process.execPath, [
    path.join(ROOT, "scripts", "compare-still.mjs"),
    path.join(outDir, "target.png"),
    path.join(outDir, "compare.png"),
  ], { cwd: ROOT, encoding: "utf8", maxBuffer: 8 * 1024 * 1024 });
  if (result.status !== 0) console.log(`[compare] REFUSED: ${`${result.stdout ?? ""}${result.stderr ?? ""}`.trim()}`);
  return result.status === 0;
}

/**
 * r2 A4/A5 — the likeness measurement, in the SAME slot as the validator chain:
 * a FAIL here spends the K=1 repair exactly like a V-code, and carries both
 * stills and the numeric table into the repair prompt.
 */
async function runLikeness(label, outDir, { parts = null } = {}) {
  const started = Date.now();
  try {
    const passes = JSON.parse(fs.readFileSync(S().paths.passes, "utf8"));
    const final = String(label).toUpperCase() === String(passes[passes.length - 1].id).toUpperCase();
    const n = Number(String(label).replace(/^P/i, ""));
    // WF-BLIND-R2 C11 — the previous pass's id pass, to name what covers an instance that was visible there.
    const previousDir = path.join(ROOT, S().subject.outDir, `P${n - 1}`);
    const previous = n > 0 && fs.existsSync(path.join(previousDir, "idpass.png")) ? previousDir : null;
    const { result: raw } = await likenessMod.likenessForPass(label, outDir, { final, previous, parts });
    // WF-BLIND-R1 B4 — LK_VISIBLE for a role is judged from the pass its census key becomes due.
    const due = likenessMod.dueVisibleParts({
      prior: S().cls.likeness, census: S().readJson("census"), regions: S().readJson("regions"), n,
    });
    // WF-BLIND-R2 C5 — an LK_AREA family is judged at the pass that builds it, and attributed there at the end.
    const owners = likenessMod.familyOwners({ prior: S().cls.likeness, census: S().readJson("census"), regions: S().readJson("regions"), passes });
    const result = likenessMod.stageResult(raw, final, due, { n, owners });
    const table = likenessMod.likenessTable(result);
    fs.writeFileSync(path.join(outDir, "likeness.json"), `${JSON.stringify(result, null, 2)}\n`);
    console.log(result.text);
    return { pass: result.pass, text: result.text, table, result, ms: Date.now() - started };
  } catch (error) {
    // A likeness that cannot run is not a silent pass: it is a FAIL with a reason.
    const text = `FAIL: likeness could not run — ${error.message}`;
    console.log(text);
    return { pass: false, text, table: "", result: null, ms: Date.now() - started };
  }
}

// ---------------------------------------------------------------------------
// WF-BLIND-R1 B6 — every attempt keeps its own evidence under one pass identity
// ---------------------------------------------------------------------------

/** The per-attempt evidence files; the top-level copies keep today's names for the FINAL attempt. */
export const ATTEMPT_FILES = Object.freeze(["report.json", "target.png", "target.png.json", "threeQuarter.png", "threeQuarter.png.json", "threeQuarter-shaded.png", "threeQuarter-shaded.png.json",
  "idpass.png", "idpass.png.json", "likeness.json", "compare.png"]);

export const attemptDir = (outDir, k) => path.join(outDir, `attempt-${k}`);

/** Remove only the `attempt-N` directories a previous run of this pass left behind. */
export function clearAttempts(outDir) {
  if (!fs.existsSync(outDir)) return;
  for (const name of fs.readdirSync(outDir)) {
    if (/^attempt-\d+$/.test(name)) fs.rmSync(path.join(outDir, name), { recursive: true, force: true });
  }
}

/**
 * Copy the final attempt's evidence to the top-level names. A file the final attempt does not have (a
 * capture refusal) is REMOVED at top level, so no stale still or measurement is ever read as this attempt's.
 * @returns {string[]} the file names copied
 */
export function finalizeAttempt(outDir, dir, moduleBase) {
  const copied = [];
  for (const name of [moduleBase, ...ATTEMPT_FILES]) {
    const src = path.join(dir, name);
    const dst = path.join(outDir, name);
    if (fs.existsSync(src)) { fs.copyFileSync(src, dst); copied.push(name); }
    else fs.rmSync(dst, { force: true });
  }
  return copied;
}

/**
 * The likeness of one attempt. A refused capture means this attempt has no stills of its own: the likeness
 * is UNVERIFIED (written to the attempt's likeness.json) and `measure` is never called on stale pixels.
 */
export async function likenessForAttempt({ label, dir, captures, measure }) {
  const refused = Object.entries(captures ?? {}).filter(([, c]) => !c?.ok).map(([name]) => name);
  if (refused.length === 0) return measure(label, dir);
  const text = `UNVERIFIED: capture refused (${refused.join(", ")}) for ${path.basename(dir)} — no likeness was measured for this `
    + "attempt; stills from an earlier attempt are never reused.";
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "likeness.json"), `${JSON.stringify({ state: "UNVERIFIED", pass_label: label, refused, text }, null, 2)}\n`);
  console.log(text);
  return { pass: false, unverified: true, text, table: "", result: null, ms: 0 };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const argv = process.argv.slice(2);
  const options = parseArgs(argv);
  SUBJ = loadSubject(subjectIdFromArgv(argv));
  process.env.LLMM_SUBJECT = SUBJ.id;            // spawned and imported scripts read the same subject
  if (!options.promptOnly) capture2 = await import("./capture2.mjs");     // r2 A6
  likenessMod = await import("./likeness.mjs");  // r2 A4
  CENSUS_PASS = Number(String(options.pass).replace(/^P/i, ""));
  const outRoot = path.join(ROOT, SUBJ.subject.outDir);
  const outDir = path.join(outRoot, options.label);
  if (!options.promptOnly) {
    fs.mkdirSync(outDir, { recursive: true });
    clearAttempts(outDir);                       // WF-BLIND-R1 B6: attempts belong to THIS run only
  }

  // Fail before a 15-minute seat is spent, not after: capture is step (d) but
  // there is no point authoring a pass that cannot be looked at.
  assertCameraSolved();                    // r1 row 12 — before a 15 min seat is spent
  const layoutCheck = checkMeasuredLayout();   // r3 C2.4 — throws on a layout that is not the target's
  if (!options.promptOnly) await assertServerUp();

  const modulePath = SUBJ.paths.module;
  const moduleTextBefore = fs.readFileSync(modulePath, "utf8");
  let currentBudget = null;                  // WF-V3: triangle budget shown to the author
  let frame = null;                          // WF-BLIND-R2 C3: the start module's planes, in metres
  try {
    const pre = await buildAndValidate();
    currentBudget = { used: pre.report?.measurements?.tris ?? null, cap: pre.report?.measurements?.triBudget ?? null };
    frame = await moduleFrame(pre.parts, SUBJ);
  } catch (error) {
    if (error instanceof RefusalError) throw error;
    currentBudget = null;
  }

  let item;
  if (options.item) {
    item = { id: options.label, title: null, item: options.item };
  } else {
    const passes = JSON.parse(fs.readFileSync(SUBJ.paths.passes, "utf8"));
    item = passes.find((p) => p.id === options.label);
    if (!item) throw new Error(`${SUBJ.rel.passes} has no item "${options.label}" — pass --item "<text>" instead`);
  }

  // WORKFLOW-V3 §7.2 — prompt numbers come from the config the GATE reads, never
  // from item prose: "0.04 m bars" against MIN_FEAT 0.06 cost run 4 171 V5 rows.
  const tokens = gateTokens(SUBJ.cls, moduleTextBefore);
  PROMPT_DIGEST = tokens.GATE_DIGEST;                          // WF-BLIND-R2 C14: every later build is checked against it
  item = resolveItem(item, tokens);
  const readme = authorReadme(tokens, SUBJ, options.label);

  // WF-BLIND-R2 C12 — examiner-side: the item sentences no gate or likeness row checks. Never shown to the author.
  const classRules = await import(pathToFileURL(path.join(ROOT, SUBJ.cls.rules)).href);
  const coverage = instructionCoverage(item, { layoutRules: classRules.layoutRules ?? {}, census: SUBJ.readJson("census") });
  const mapped = coverage.rows.filter((r) => r.rows.length).length;
  const exempt = coverage.rows.filter((r) => !r.rows.length && r.exempt).length;
  console.log(`[examiner] ${options.label} instruction map: ${coverage.rows.length} item sentence(s), ${mapped} checked by a row, `
    + `${exempt} exempt, ${coverage.rows.length - mapped - exempt} unchecked`);
  for (const line of coverage.warnings) console.log(`[examiner] WARNING ${line}`);

  // r3 C2.4 / Fable M2 — a pass item may not cite a key nobody measured.
  // WF-BLIND-R1 B2 — "cite" = the pass's requiredLayoutKeys (fallback: the item's key list).
  const unverifiedKeys = unverifiedItemKeys(item.item, loadLayout(), item.requiredLayoutKeys ?? null);
  if (unverifiedKeys.length > 0) {
    throw new RefusalError(`${options.label} cites layout key(s) marked unverified: ${unverifiedKeys.join(", ")}. `
      + "Measure them (scripts/measure-target.mjs) and re-freeze the layout, or remove them from the item — "
      + "a seat is not spent building to a number nobody measured (WF-LOOP-R3 C2.4).");
  }

  // WORKFLOW-V3 §7.5 item 5 — the MISSING KEY backlog, printed every preflight.
  const backlog = readBacklog(SUBJ.paths.missingKeys);
  for (const line of backlogLines(backlog, loadLayout())) console.log(line);
  if (!options.gateOnly && (SUBJ.subject.missingKeyPolicy ?? "report") === "refuse") {
    const refused = refusedKeys(backlog, loadLayout(), options.label);
    if (refused.length > 0) {
      throw new RefusalError(`${options.label} re-runs an item whose seats asked twice for key(s) still absent from `
        + `${SUBJ.rel.layout}: ${refused.join(", ")}. Measure them first (missingKeyPolicy "refuse").`);
    }
  }

  const previousDir = path.join(outRoot, `P${options.n - 1}`);
  const reviewPath = path.join(previousDir, "review.md");
  // WF-R3 H1 — a review counts only for the module it reviewed: review.md must record `module: <hash>` of the
  // previous pass's final module (the hash look-checklist.md carries). A stale review is UNREVIEWED, never clean.
  const previousModule = path.join(previousDir, path.basename(SUBJ.paths.module));
  const previousReview = options.n > 0 && fs.existsSync(reviewPath)
    && reviewModuleHash(fs.readFileSync(reviewPath, "utf8")) === sha(previousModule) ? fs.readFileSync(reviewPath, "utf8") : null;
  if (options.n > 0 && fs.existsSync(reviewPath) && previousReview === null) {
    console.log(`[review] ${rel(reviewPath)} does not record module ${sha(previousModule)} — read as UNREVIEWED`);
  }

  const images = [SUBJ.paths.target];
  for (const view of VIEWS) {
    const still = seatStill(previousDir, view);
    if (options.n > 0 && fs.existsSync(still)) images.push(still);
  }

  // WF-BLIND-R1 B4 — acceptance from the same likeness config the rows read, before the attempt.
  const acceptance = likenessMod.acceptanceBlock({
    prior: SUBJ.cls.likeness, census: SUBJ.readJson("census"), regions: SUBJ.readJson("regions"),
    n: options.n, final: isFinalPass(options.label), passes: SUBJ.readJson("passes"),
  });
  const prompt = assemblePrompt({ budget: currentBudget, options, item, moduleText: moduleTextBefore, readme, previousReview, repairReport: null, acceptance, frame });
  const promptBytes = Buffer.byteLength(prompt, "utf8");
  if (options.promptOnly) {
    if (options.promptOut) {
      const file = path.resolve(ROOT, options.promptOut);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, prompt);
      console.log(`[prompt-only] ${options.label} ${SUBJ.id}: ${promptBytes} bytes -> ${rel(file)} (no seat called, nothing written under ${rel(outDir)})`);
    } else {
      process.stdout.write(prompt);
    }
    return 0;
  }
  fs.writeFileSync(path.join(outDir, "prompt.md"), prompt);

  let runSeatFn = null;
  const seatCall = async (text, imgs, tag, outFile) => {
    runSeatFn ??= await loadSeat(options.seat);
    return runSeatFn({
      prompt: text, images: imgs, workspace: ROOT, timeoutMs: SEAT_TIMEOUT_MS, tag, mode: options.seatMode, outFile, modulePath,
    });
  };

  const lastPath = path.join(outDir, "last.md");
  const seat = options.gateOnly
    ? { transcript: "(gate-only: no seat spawned)", answer: "CHANGE: none (gate-only re-run)", seconds: 0, usage: { total: 0 }, failureClass: null }
    : await seatCall(prompt, images, options.label, lastPath);
  fs.writeFileSync(path.join(outDir, "transcript.txt"), seat.transcript ?? "");
  seatOutcome(seat, options.label);          // transport / timeout: exit 2 before anything is counted
  if (options.gateOnly) {
    if (!fs.existsSync(lastPath)) fs.writeFileSync(lastPath, `${seat.answer}\n`);
  } else {
    fs.writeFileSync(lastPath, `${seat.answer}\n`);
  }

  // WF-V3 blind Gemini pickup P1 — parse before a fence goes live; one syntax-only follow-up per seat reply.
  const transcriptPath = path.join(outDir, "transcript.txt");
  // WF-BLIND-R1 B6 — a syntax follow-up is part of the attempt it repairs: its files live under attempt-<k>/.
  const syntaxRetry = (tag, dir, outFile) => async (prompt) => {
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, `${tag}-prompt.md`), prompt);
    const s = await seatCall(prompt, [], tag, outFile);
    fs.appendFileSync(transcriptPath, `\n\n===== ${tag} =====\n${s.transcript ?? ""}`);
    fs.writeFileSync(outFile, `${s.answer ?? ""}\n`);
    return s;
  };
  let syntaxRetries = 0;

  const missingKeys = [];
  let contractText = null;
  let firstFollowUp = null;
  if (!options.gateOnly) {
    missingKeys.push(...recordMissingKeys(SUBJ.paths.missingKeys, options.label, seat.answer).keys);
    const applied = await applySeatChecked(seat, options, modulePath,
      { tag: options.label, retry: syntaxRetry(`${options.label}-syntax`, attemptDir(outDir, 1), path.join(attemptDir(outDir, 1), "syntax.md")) });
    contractText = applied.contractText;
    syntaxRetries += applied.syntaxRetries;
    firstFollowUp = applied.followUp;
  }

  let codexSeconds = seat.seconds + (firstFollowUp?.seconds ?? 0);
  let usage = sumUsage(seat.usage ?? { total: 0 }, firstFollowUp?.usage ?? { total: 0 });
  let repairs = 0;
  let repairSeat = null;
  let repairReverted = null;                 // WF-V3: set when a repair made the pass worse

  const seed = 1;
  let repairPromptBytes = null;
  // WF-BLIND-R1 B6 — every attempt keeps its own evidence under attempt-<k>/: module, report.json, the stills,
  // idpass, likeness.json and compare.png. A capture refusal makes THAT attempt's likeness UNVERIFIED.
  const attempts = [];
  const moduleBase = path.basename(modulePath);
  const evaluate = async (calibrate) => {
    const k = attempts.length + 1;
    const dir = attemptDir(outDir, k);
    fs.mkdirSync(dir, { recursive: true });
    if (calibrate) runCalibrate();
    let g = await gate();
    if (contractText) g = withContractFail(g, contractText);
    const shot = await captureViews(dir, seed);
    const lk = options.dry ? null : await likenessForAttempt({ label: options.label, dir, captures: shot.captures,
      measure: (l, d) => runLikeness(l, d, { parts: g.report?.measurements?.perPart ?? null }) });
    const compared = Object.values(shot.captures).every((c) => c.ok) ? writeCompare(dir) : false;
    fs.copyFileSync(modulePath, path.join(dir, moduleBase));
    fs.writeFileSync(path.join(dir, "report.json"), `${JSON.stringify(g.report, null, 2)}\n`);
    const attempt = { k, dir, result: g, captures: shot.captures, captureMs: shot.ms, likeness: lk, compared };
    attempts.push(attempt);
    console.log(`[attempt] ${options.label} attempt-${k}: gate ${g.pass ? "PASS" : "FAIL"}, likeness `
      + `${lk ? (lk.unverified ? "UNVERIFIED" : (lk.pass ? "PASS" : "FAIL")) : "n/a"} — ${rel(dir)}`);
    return attempt;
  };

  // run4 P2 fix: colour is never the seat's job. Re-freeze the palette from the
  // target regions BEFORE the gate, so LK rows and the family classifier see the
  // calibrated hexes, not whatever the author typed (brick came out #af3f2d).
  // (d) stills FIRST, then likeness, then the single repair slot. r2 A5 reorders
  // the pass for one reason: a likeness FAIL is as blocking as a V-code, and the
  // repair seat cannot be asked to fix what it has never seen. Stills are taken
  // whether or not the gate passed — a failed pass nobody can look at is a
  // failed pass nobody can diagnose.
  let current = await evaluate(!options.dry);
  let result = current.result;
  let captures = current.captures;
  let captureMs = current.captureMs;
  let likeness = current.likeness;

  // WF-R3 R3-B item 4 — deterministic rows are fixed by the harness, re-gated, and never spend the repair.
  let autoFixes = [];
  if (!options.dry && options.seatMode === "text" && !result.pass) {
    const fix = autoFixPaletteZones(fs.readFileSync(modulePath, "utf8"), result.report?.violations);
    if (fix.fixes.length > 0 && !moduleSyntaxError(fix.text)) {
      fs.writeFileSync(modulePath, fix.text);
      autoFixes = fix.fixes;
      console.log(`[auto-fix] ${fix.fixes.map((f) => `PALETTE_ZONE "${f.from}" -> "${f.to}"`).join(", ")} — re-gated before any repair`);
      current = await evaluate(true);
      result = current.result;
      captures = current.captures;
      captureMs += current.captureMs;
      likeness = current.likeness;
      result.report?.advisories?.push(...autoFixes.map((f) => ({ v: "AUTO_FIX", part: null, measured: `PALETTE_ZONE zone "${f.from}" rewritten to "${f.to}"`,
        limit: "the one closed key the row named", hint: "the harness renamed the zone (the row's only suggestion) instead of spending the repair", blocking: false })));
    }
  }

  if ((!result.pass || (likeness && !likeness.pass)) && options.repair && !options.dry) {
    repairs = 1;
    // Images 2 and 3 are THIS pass's stills now, not the previous pass's.
    const repairImages = [SUBJ.paths.target];
    for (const view of VIEWS) {
      const still = seatStill(current.dir, view);
      if (fs.existsSync(still)) repairImages.push(still);
    }
    const moduleNow = fs.readFileSync(modulePath, "utf8");
    const preRepair = { text: moduleNow, result, likeness, contract: contractText };
    if (result.report?.measurements?.tris !== undefined) {
      currentBudget = { used: result.report.measurements.tris, cap: result.report.measurements.triBudget ?? currentBudget?.cap ?? null };
    }
    const repairPrompt = options.seatMode === "text" ? assembleRepairPrompt({
      options, item, moduleText: moduleNow, moduleBefore: moduleTextBefore, report: result.pass ? null : result.report,
      likeness: likeness && !likeness.pass && !likeness.unverified ? likeness : null,
      ready: frame?.ready ? frame.ready(loadLayout(), requiredLayoutKeys(item), gateTokens(SUBJ.cls).MIN_FEAT) : [],
      firstBytes: promptBytes, diff: unifiedDiff(moduleTextBefore, moduleNow, SUBJ.rel.module),
    }) : assemblePrompt({ budget: currentBudget,
      options, item, moduleText: moduleNow, readme, previousReview,
      repairReport: result.pass ? null : result.report.text,
      likeness: likeness && !likeness.pass && !likeness.unverified ? likeness : null,
      diff: options.seatMode === "text" ? unifiedDiff(moduleTextBefore, moduleNow, SUBJ.rel.module) : null,
      acceptance, frame,
    });
    fs.writeFileSync(path.join(outDir, "repair-prompt.md"), repairPrompt);
    repairPromptBytes = Buffer.byteLength(repairPrompt, "utf8");
    const repairLast = path.join(outDir, "repair.md");
    const repairTag = `${options.label}-repair`;
    repairSeat = await seatCall(repairPrompt, repairImages, repairTag, repairLast);
    fs.appendFileSync(path.join(outDir, "transcript.txt"), `\n\n===== REPAIR =====\n${repairSeat.transcript ?? ""}`);
    seatOutcome(repairSeat, repairTag);      // a dropped repair is not a repair: exit 2
    fs.writeFileSync(repairLast, `${repairSeat.answer}\n`);
    missingKeys.push(...recordMissingKeys(SUBJ.paths.missingKeys, options.label, repairSeat.answer).keys);
    // WF-R3 R3-B item 6 — a text-mode repair may answer with line edits against the numbered module.
    if (options.seatMode === "text" && !options.dry) {
      const edited = applyLineEdits(moduleNow, repairSeat.answer);
      if (edited.text !== null) { repairSeat.artifact = edited.text; console.log(`[repair] applied ${edited.edits} line edit(s)`); }
      else if (edited.error) { repairSeat.artifact = null; console.log(`[repair] line edits refused: ${edited.error}`); }
    }
    const repairApplied = await applySeatChecked(repairSeat, options, modulePath,
      { tag: repairTag, retry: syntaxRetry(`${repairTag}-syntax`, attemptDir(outDir, 2), path.join(attemptDir(outDir, 2), "repair-syntax.md")) });
    contractText = repairApplied.contractText;
    syntaxRetries += repairApplied.syntaxRetries;
    codexSeconds += repairSeat.seconds + (repairApplied.followUp?.seconds ?? 0);
    usage = sumUsage(sumUsage(usage, repairSeat.usage), repairApplied.followUp?.usage ?? { total: 0 });
    current = await evaluate(true);          // WORKFLOW-V3 §7.3 — calibrate after EVERY author mutation
    result = current.result;
    captures = current.captures;
    captureMs += current.captureMs;
    likeness = current.likeness;

    // WF-V3 (Opus 5, 2026-09-13): a repair may never leave the pass WORSE than it found it.
    // Pickup P0: the repair added hubs and detached the wheels (V3_FLOAT, 9 lumps).
    // WF-BLIND-R2 C1: blind Gemini P2 traded V11_LADDER_ACCESS for V11_LANDING_GUARD at equal counts and it was kept.
    const verdict = repairVerdict({ result: preRepair.result, likeness: preRepair.likeness }, { result, likeness });
    const { before, after, introduced } = verdict;
    if (verdict.worse) {
      const rejected = path.join(outDir, "repair-rejected" + path.extname(modulePath));
      fs.writeFileSync(rejected, fs.readFileSync(modulePath, "utf8"));
      fs.writeFileSync(modulePath, preRepair.text);
      contractText = preRepair.contract;
      current = await evaluate(true);
      result = current.result;
      captures = current.captures;
      captureMs += current.captureMs;
      likeness = current.likeness;
      repairReverted = { before, after, introduced, attempt: current.k };
      const msg = "The repair made the pass worse (gate rows " + before.gate + " -> " + after.gate
        + ", likeness rows " + before.likeness + " -> " + after.likeness
        + (introduced.length ? ", new gate code(s) " + introduced.join(", ") : "") + "); the module was reverted to its "
        + "pre-repair state. The rejected module is " + path.basename(rejected) + " (its evidence: attempt-2/); "
        + "the reverted module is re-measured as attempt-" + current.k + "/.";
      fs.writeFileSync(path.join(outDir, "repair-reverted.md"), msg + "\n" + JSON.stringify({ introduced }) + "\n");
      console.log("[repair] REVERTED — " + msg);
    }
  }

  // (e) everything written, pass or fail. r2 A5 compare.png is written per attempt; WF-BLIND-R1 B6: the FINAL
  // attempt's module, report, stills, likeness and compare keep today's top-level names (stale ones removed).
  finalizeAttempt(outDir, current.dir, moduleBase);
  const moduleCopy = path.join(outDir, moduleBase);
  // r1 row 11 — the six blank LOOK rows the Fable reviewer fills in, written
  // every pass, pass or fail: the review is the only thing that crosses to
  // P<N+1>, and `assemblePrompt` already inlines the previous one verbatim.
  writeLookChecklist(outDir, options.label, result.pass, result.report?.text, likeness, sha(moduleCopy));

  const timings = {
    pass: options.label,
    dry: options.dry,
    item: item.item,
    gatePass: result.pass,
    // r2 A4/A7 — likeness is a first-class column, not a footnote.
    likenessPass: likeness ? likeness.pass : null,
    likenessMs: likeness ? likeness.ms : 0,
    likenessState: likeness ? (likeness.unverified ? "UNVERIFIED" : (likeness.pass ? "PASS" : "FAIL")) : null,
    likenessCodes: likeness?.result ? [...new Set(likeness.result.violations.map((v) => v.v))] : [],
    // WF-BLIND-R1 B5 — prompt size is a cost the author pays every call.
    promptBytes,
    repairPromptBytes,
    // WF-BLIND-R1 B6 — one row per attempt; the evidence is under attempt-<k>/.
    attempts: attempts.map((a) => ({
      attempt: a.k, dir: rel(a.dir), gatePass: a.result.pass,
      likeness: a.likeness ? (a.likeness.unverified ? "UNVERIFIED" : (a.likeness.pass ? "PASS" : "FAIL")) : null,
      capturesOk: Object.values(a.captures).every((c) => c.ok), compare: a.compared,
    })),
    codexSeconds: Math.round(codexSeconds * 10) / 10,
    tokens: usage.total ?? 0,
    usage,
    repairs,
    repairReverted,
    syntaxRetries,
    gateDigest: PROMPT_DIGEST,                 // WF-BLIND-R2 C14
    uncheckedInstructions: coverage.warnings,  // WF-BLIND-R2 C12 (examiner-side)
    kernelBuildMs: result.kernelBuildMs ?? 0,
    booleans: result.booleans ?? 0,
    toThreeMs: result.report?.timings?.merge ?? 0,
    validatorMs: result.report?.timings?.total ?? 0,
    validatorTimings: result.report?.timings ?? {},
    captureMs,
    captures,
    moduleChanged: fs.readFileSync(modulePath, "utf8") !== moduleTextBefore,
    seat: options.gateOnly ? null : options.seat,
    seatMode: options.seatMode,
    seatContract: contractText ? "FAIL" : null,
    missingKeys: [...new Set(missingKeys)],
    answer: seat.answer,
    model: seat.model,
    effort: seat.effort,
    sessionId: seat.sessionId,
  };
  fs.writeFileSync(path.join(outDir, "timings.json"), `${JSON.stringify(timings, null, 2)}\n`);

  const measure = spawnSync(process.execPath, [path.join(ROOT, "scripts", "measure.mjs"), options.label], {
    cwd: ROOT, encoding: "utf8",
  });
  if (measure.stdout) process.stdout.write(measure.stdout);
  if (measure.stderr) process.stderr.write(measure.stderr);

  // r2 A5 — one verdict over BOTH measurements. A pass that satisfies every rule
  // and looks nothing like the target is not a pass.
  const numeric = result.pass && (likeness ? likeness.pass : true);
  console.log(`[pass] ${options.label} ${numeric ? "PASS" : "FAIL"} `
    + `(gate ${result.pass ? "PASS" : "FAIL"}, likeness ${likeness ? (likeness.pass ? "PASS" : "FAIL") : "n/a"}`
    + `, layout ${layoutCheck.state}) — ${rel(outDir)}`);
  if (!result.pass) console.log(result.report.text);
  if (likeness && !likeness.pass) console.log(likeness.text);
  if (likeness?.result?.unverified?.length) {
    console.log(`[pass] ${likeness.result.unverified.length} likeness row(s) UNVERIFIED — not the same thing as clean.`);
  }

  // r3 C2.4 / Astra C10 — the LAST pass does not finish on numbers. The image
  // review row is mandatory input to the verdict, and until it says PASS the
  // verdict is "PASS-numeric, review pending", not PASS.
  if (isFinalPass(options.label)) {
    console.log("");
    console.log(`[review] ${REVIEW_SENTENCE}`);
    const row3 = reviewRow3(outDir, sha(moduleCopy));
    const residuals = likeness?.result ? [...new Set(likeness.result.violations.map((v) => `${v.v} ${v.part ?? ""}`.trim()))] : [];
    // FAIL | REVIEW_PENDING | ACCEPTED_WITH_RESIDUALS | PASS. A gate FAIL is never
    // accepted; a likeness residual is acceptable only when the image review says so.
    let state;
    if (!result.pass || row3 === "FAIL") state = "FAIL";
    else if (row3 === null) state = "REVIEW_PENDING";
    else if (numeric && row3 === "PASS") state = "PASS";
    else state = "ACCEPTED_WITH_RESIDUALS";
    const verdict = {
      state, pass: options.label, gate: result.pass, likeness: likeness ? likeness.pass : null, row3,
      residuals: state === "ACCEPTED_WITH_RESIDUALS" ? residuals : [],
      // bound to the exact artefacts judged: a later edit to any of them voids the verdict
      hashes: {
        module: sha(moduleCopy),
        layout: sha(SUBJ.paths.layout),
        target: sha(path.join(outDir, "target.png")),
        compare: sha(path.join(outDir, "compare.png")),
        review: sha(path.join(outDir, "review.md")),
      },
    };
    fs.writeFileSync(path.join(outDir, "verdict.json"), `${JSON.stringify(verdict, null, 2)}
`);
    console.log(`[verdict] ${options.label} ${state}${verdict.residuals.length ? ` — residuals: ${verdict.residuals.join("; ")}` : ""}`);
    if (state === "REVIEW_PENDING") {
      console.log(`[review] row 3 ("reads as the target") of ${rel(path.join(outDir, "review.md"))} is not written. `
        + "Judge it against compare.png (the two FRONT FACES at equal px per W) and write PASS, PASS with residual, or FAIL.");
    }
    return state === "PASS" || state === "ACCEPTED_WITH_RESIDUALS" ? 0 : 1;
  }
  return numeric ? 0 : 1;
}

/** Palette + sideTint from the target regions; colour is never the seat's job. */
function runCalibrate() {
  if (!S().paths.regions || !fs.existsSync(S().paths.regions)) return;
  const cal = spawnSync(process.execPath, [path.join(ROOT, "scripts", "calibrate-palette.mjs")], { cwd: ROOT, encoding: "utf8" });
  const lines = (cal.stdout || "").trim().split(String.fromCharCode(10)).map((l) => l.replace(String.fromCharCode(13), ""));
  const tint = lines.find((l) => /sideTint/.test(l));
  if (tint) console.log(`[palette]${tint}`);
  console.log(lines.pop() || "[palette] calibrate-palette ran");
}

const sha = (file) => (file && fs.existsSync(file) ? createHash("sha256").update(fs.readFileSync(file)).digest("hex").slice(0, 16) : null);

/** The last item in passes.json — the only pass the image-review row gates. */
function isFinalPass(label) {
  try {
    const passes = JSON.parse(fs.readFileSync(S().paths.passes, "utf8"));
    return String(label).toUpperCase() === String(passes[passes.length - 1].id).toUpperCase();
  } catch {
    return false;
  }
}

/**
 * The Verdict cell of LOOK row 3 ("reads as the target") in this pass's
 * review.md. Null when there is no review, or no verdict in that row.
 */
export function reviewRow3(outDir, moduleHash) {
  const file = path.join(outDir, "review.md");
  if (!fs.existsSync(file)) return null;
  const text = fs.readFileSync(file, "utf8");
  // WF-R3 H1 — a review.md that does not record the module it judged is not a review of this module.
  if (!moduleHash || reviewModuleHash(text) !== moduleHash) return null;
  for (const line of text.split(/\r?\n/)) {
    if (!line.startsWith("|") || !/reads as the target/i.test(line)) continue;
    const cells = line.split("|").map((c) => c.trim());
    const verdict = cells.find((c) => /^(PASS|FAIL|ACCEPTED)\b/i.test(c));
    if (!verdict) return null;
    if (/^FAIL/i.test(verdict)) return "FAIL";
    if (/^ACCEPTED|residual/i.test(verdict)) return "ACCEPTED_WITH_RESIDUALS";
    return "PASS";
  }
  return null;
}

/** WF-R3 H1 — the `module: <hash>` a review.md records (null when it records none). */
export function reviewModuleHash(text) {
  const m = /^\s*module:\s*([0-9a-f]{16})\b/im.exec(String(text ?? ""));
  return m ? m[1] : null;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    process.exitCode = await main();
  } catch (error) {
    console.error(`pass: ${error instanceof RefusalError ? "REFUSED — " : ""}${error.message}`);
    process.exitCode = error instanceof RefusalError ? 3 : 2;
  }
}
