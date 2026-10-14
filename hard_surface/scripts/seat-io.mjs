// Seat I/O shared by scripts/pass.mjs (P0-P3 passes, still live for the building) and scripts/loop.mjs (WORKFLOW v4
// V4-3): seat adapters + aliases, the text / line-edit contracts, applyLineEdits, the syntax pre-check, the palette-zone
// auto-fix and the module frame (READY CALLS). Moved verbatim out of pass.mjs, which re-exports every name.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

/** A seat that never answered (transport drop, timeout). Exit 2; not a seat. */
export class SeatTransportError extends Error {}

// Named TEST seats (owner 2026-09-25): an alias runs an existing adapter with a pinned model + effort, so
// blind runs record the seat by name (out/blind/<subject>/<seat>/) and never depend on the caller env.
export const SEAT_ALIASES = Object.freeze({
  luna: { adapter: "terra", env: { LLMM_TERRA_MODEL: "gpt-6-luna", LLMM_TERRA_EFFORT: "high" } },
  gmed: { adapter: "agy", env: { LLMM_AGY_MODEL: "gemini-3.8-flash-medium", LLMM_AGY_EFFORT: "medium" } },
  // REFERENCE seat: an Opus 5.5 agent answers the relay folder (fresh agent per prompt). It sets the bar for
  // "technically correct"; it is not a test seat and never counts toward the owner pass rule.
  opus: { adapter: "relay", env: {} },
});
export const SEATS = Object.freeze(["codex", "relay", "fake", "agy", "terra", ...Object.keys(SEAT_ALIASES)]);   // agy: Antigravity, default gemini-3.8-flash-high
export const SEAT_MODES = Object.freeze(["text", "agent"]);

/** WORKFLOW-V3 §3 — the last words of every text-mode prompt. */
export const TEXT_CONTRACT = "Do not run commands or read files. Reply with the COMPLETE module in one ```js fence, "
  + "then one line `CHANGE: …`, then optionally one line `MISSING KEY: k1, k2`.";

export const EDIT_CONTRACT = "Do not run commands or read files. Reply with one ```js replace A-B fence per edit, holding the NEW text of "
  + "lines A..B of the numbered module above (to add lines, replace a line with itself plus the new ones; to delete, leave "
  + "the fence empty), or with the COMPLETE module in one ```js fence. Then one line `CHANGE: …`.";

/**
 * WF-V4 V4-6 item 1 — the NUMBERED edit contract (scripts/loop.mjs prompts): a seat copies the prompt's numbered
 * display `N| code` and changes the code. The exact format the prompts print (loop.mjs numbered()).
 */
export const NUMBERED_CONTRACT = "Do not run commands or read files. Reply with ```js fences of numbered lines in the format shown "
  + "above: `N| new code` replaces line N (consecutive numbers replace that range; an unnumbered line right under `N| …` is "
  + "inserted after line N; `N|` with nothing after it empties line N). Keep the number, change the code. "
  + "(```js replace A-B fences or the COMPLETE module also work.) Then one line `CHANGE: …`.";

const NUM_LINE = /^[ \t]*(\d+)[ \t]?\|(.*)$/;
const GAP_LINE = /^[ \t]*\|[ \t]*(?:…|\.\.\.)?[ \t]*$/;

/** The edits of one numbered fence body: consecutive `N|` lines are one range; unnumbered lines join the range above. */
function numberedEdits(body) {
  const lines = body.replace(/\r/g, "").split("\n");
  while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
  const edits = [];
  let cur = null;
  let pre = [];
  for (const line of lines) {
    if (GAP_LINE.test(line)) { cur = null; continue; }
    const m = NUM_LINE.exec(line);
    if (m) {
      const n = Number(m[1]);
      const code = m[2].startsWith(" ") ? m[2].slice(1) : m[2];
      if (cur && n === cur.b + 1 && !cur.inserted) { cur.b = n; cur.lines.push(code); }
      else { cur = { a: n, b: n, lines: [...pre, code], inserted: false }; pre = []; edits.push(cur); }
    } else if (cur) { cur.lines.push(line); cur.inserted = true; }
    else if (line.trim()) pre.push(line);
  }
  return edits.map((e) => ({ a: e.a, b: e.b, body: e.lines.join("\n"), numbered: true }));
}

/**
 * Apply ```js replace A-B fences and NUMBERED fences (any fence whose first non-blank line is `N| code`; V4-6 item 1),
 * 1-based, inclusive, numbered against `moduleText`, bottom-up.
 * @returns {{text: string|null, edits: number, error: string|null, numbered?: number}} text null when the reply carries no edit.
 */
export function applyLineEdits(moduleText, answer) {
  const edits = [];
  let numbered = 0;
  for (const m of String(answer ?? "").matchAll(/```([^\n`]*)\r?\n([\s\S]*?)```/g)) {
    const rep = /^(?:js|javascript|mjs)[ \t]+replace[ \t]+(\d+)[ \t]*-[ \t]*(\d+)[ \t]*$/i.exec(m[1].trim());
    if (rep) { edits.push({ a: Number(rep[1]), b: Number(rep[2]), body: m[2].replace(/\r?\n$/, "") }); continue; }
    const first = m[2].split(/\r?\n/).find((l) => l.trim());
    if (first && NUM_LINE.test(first)) {
      const e = numberedEdits(m[2]);
      numbered += e.length;
      edits.push(...e);
    }
  }
  if (edits.length === 0) return { text: null, edits: 0, error: null };
  const lines = String(moduleText ?? "").split(/\r?\n/);
  edits.sort((x, y) => y.a - x.a);
  const label = (e) => (e.numbered ? (e.a === e.b ? `numbered line ${e.a}|` : `numbered lines ${e.a}..${e.b}|`) : `replace ${e.a}-${e.b}`);
  for (let k = 0; k < edits.length; k += 1) {
    const e = edits[k];
    if (!(e.a >= 1 && e.b >= e.a && e.b <= lines.length)) return { text: null, edits: edits.length, error: `${label(e)} is outside the module's 1..${lines.length} lines` };
    if (k > 0 && e.b >= edits[k - 1].a) return { text: null, edits: edits.length, error: `${label(e)} overlaps ${label(edits[k - 1])}` };
  }
  for (const e of edits) lines.splice(e.a - 1, e.b - e.a + 1, ...(e.body === "" && !e.numbered ? [] : e.body.split(/\r?\n/)));
  return { text: lines.join("\n"), edits: edits.length, error: null, numbered };
}

// ---------------------------------------------------------------------------
// WF-R3 R3-B item 4 — deterministic rows are fixed by the harness before a repair is spent: a PALETTE_ZONE row whose
// hint names exactly one closed key is a rename of `zone: "<bad>"` (and the palette key), recorded as an advisory.
// ---------------------------------------------------------------------------

/** @returns {{text: string, fixes: Array<{from: string, to: string}>}} */
export function autoFixPaletteZones(moduleText, violations) {
  let text = String(moduleText ?? "");
  const fixes = [];
  for (const v of violations ?? []) {
    if (v.v !== "PALETTE_ZONE") continue;
    const from = /zone "([^"]+)"/.exec(String(v.measured ?? ""))?.[1];
    const to = [...String(v.hint ?? "").matchAll(/use "([^"]+)"/g)].map((m) => m[1]);
    if (!from || to.length !== 1) continue;
    const esc = from.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const before = text;
    text = text.replace(new RegExp(`(\\bzone\\s*:\\s*)(["'])${esc}\\2`, "g"), `$1$2${to[0]}$2`);
    // the palette key: rename it, or drop it when the target key is already there
    const keyRe = new RegExp(`^(\\s*)(["']?)${esc}\\2(\\s*:\\s*["']#[0-9a-fA-F]{3,8}["'],?)\\s*$`, "m");
    if (new RegExp(`^\\s*(["']?)${to[0].replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\1\\s*:`, "m").test(text)) text = text.replace(keyRe, "");
    else text = text.replace(keyRe, `$1$2${to[0]}$2$3`);
    if (text !== before) fixes.push({ from, to: to[0] });
  }
  return { text: text.replace(/\n\s*\n(\s*\n)+/g, "\n\n"), fixes };
}

export async function loadSeat(name) {
  if (!SEATS.includes(name)) throw new Error(`no seat adapter "${name}"`);
  const alias = SEAT_ALIASES[name];
  const runSeat = (await import(`./seats/${alias ? alias.adapter : name}.mjs`)).runSeat;
  if (!alias) return runSeat;
  return (opts = {}) => runSeat({ ...opts, env: { ...(opts.env ?? process.env), ...alias.env } });
}

/**
 * transport / timeout -> SeatTransportError (exit 2, the seat is not counted);
 * contract -> "contract" (a repair-eligible FAIL); null -> "ok".
 */
export function seatOutcome(seat, tag = "seat") {
  const fc = seat?.failureClass ?? null;
  if (fc === "transport" || fc === "timeout") {
    throw new SeatTransportError(`${tag}: seat ${fc} after ${Number(seat.seconds ?? 0).toFixed(1)} s — not counted as a seat; retry`);
  }
  if (fc === "contract") return "contract";
  if (fc !== null) throw new Error(`${tag}: unknown seat failureClass "${fc}"`);
  return "ok";
}


export const SYNTAX_FAIL_PREFIX = "FAIL: SEAT_SYNTAX";

/**
 * WF-V3 blind Gemini pickup P1: a repair reply that did not parse consumed the
 * pass's only repair. `node --check` on a temp .mjs copy (no new dependency).
 * @returns {string|null} null when the module parses, else "line L col C: message".
 */
export function moduleSyntaxError(moduleText) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "llmm-syntax-"));
  try {
    const file = path.join(dir, "module.mjs");
    fs.writeFileSync(file, String(moduleText ?? ""));
    const r = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
    if (r.status === 0) return null;
    const lines = String(r.stderr ?? "").split(/\r?\n/);
    const at = lines.findIndex((l) => /module\.mjs:\d+\s*$/.test(l));
    const lineNo = at >= 0 ? Number(/:(\d+)\s*$/.exec(lines[at])[1]) : null;
    const caret = at >= 0 ? (lines[at + 2] ?? "") : "";
    const col = /^\s*\^/.test(caret) ? caret.indexOf("^") + 1 : null;
    const message = (lines.find((l) => /^\w*Error\b/.test(l)) ?? "the module does not parse").trim();
    return `${lineNo ? `line ${lineNo}${col ? ` col ${col}` : ""}: ` : ""}${message}`;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/** The one syntax-only follow-up: same module back, only the parse error fixed. */
export function syntaxFollowUpPrompt(error, moduleText) {
  return [
    `Your module does not parse: ${error} — return the same module with only that fixed. Change nothing else.`,
    "",
    "```js",
    String(moduleText ?? "").replace(/\s+$/, ""),
    "```",
    "",
    TEXT_CONTRACT,
  ].join("\n");
}


/** Sum two usage records; split fields survive only when present. */
export function sumUsage(a = {}, b = {}) {
  const out = { total: (a.total ?? 0) + (b.total ?? 0) };
  for (const k of ["input", "cached", "output", "reasoning"]) {
    if (Number.isFinite(a[k]) || Number.isFinite(b[k])) out[k] = (a[k] ?? 0) + (b[k] ?? 0);
  }
  return out;
}


/** WF-BLIND-R2 C3 — the live start module's layout frame, planes and a metres formatter, from its measured parts. */
export async function moduleFrame(parts, subject) {
  if (!Array.isArray(parts) || parts.length === 0) return null;
  const rules = await import(pathToFileURL(path.join(ROOT, subject.cls.rules)).href);
  if (typeof rules.layoutFrame !== "function") return null;
  const unionBox = (members) => ({
    min: [0, 1, 2].map((a) => Math.min(...members.map((m) => m.aabb.min[a]))),
    max: [0, 1, 2].map((a) => Math.max(...members.map((m) => m.aabb.max[a]))),
  });
  const records = parts.map((p, index) => ({ index, id: p.id, role: p.role ?? null, zone: p.zone, aabb: p.solid.aabb(), part: p }));
  const ctx = { records, cls: subject.cls, geo: { unionBox } };
  const F = rules.layoutFrame(ctx);
  return {
    F,
    planes: F && typeof rules.layoutPlanes === "function" ? rules.layoutPlanes(ctx, F) : null,
    absolute: (key, entry) => (F && typeof rules.layoutAbsolute === "function" ? rules.layoutAbsolute(key, entry, F) : null),
    // WF-R3 R3-B item 3 — the class's detail calls with every argument in metres (rules.readyCalls), or [].
    ready: (layout, cited, minFeat) => (F && typeof rules.readyCalls === "function" ? rules.readyCalls(layout, F, { cited, minFeat }) : []),
  };
}

