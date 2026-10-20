// WF v8 WP5 — the pure half of scripts/v7/gold.mjs, the orchestrator's only interface (research/v7/WF-V8-PLAN.md WP5 +
// "Shared data"): the config (gold.config.json), state.json <-> the generated LEDGER.md, the ledger lines, the phase
// machine and its NEXT command, the merge / modeller-report updates of the items, the brief texts, the eyes file list and
// hashes, the doctor's `hull` row, the owner packet, commit pathspecs and messages, a span-preserving JSON key editor.
// No child processes and no rendering here; files are read only where a function says so (loadConfig, hashFiles).
// Unit tests: scripts/v7/gold.test.mjs.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "..", "..");
export const CONFIG_FILE = path.join(HERE, "gold.config.json");
export const PHASES = Object.freeze(["setup", "model", "review", "owner", "done"]);
export const ROUND_TYPES = Object.freeze(["build", "list", "polish"]);
// Candidate critic seats, fable-first (the order legacy subjects' critiques were listed in): the standard pair going
// forward is opus + sonnet (owner 2026-10-02); fable is a rare tie-break seat, kept working for the 15 subjects whose
// history already pairs it with opus. DEFAULT_PAIR is what a brand-new round briefs when neither seat has started.
export const SEATS = Object.freeze(["fable", "opus", "sonnet"]);
export const DEFAULT_PAIR = Object.freeze(["opus", "sonnet"]);
export const CO_AUTHOR = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>";
/** The contract's key order (WF-V8-PLAN.md "Shared data"). */
export const STATE_KEYS = Object.freeze(["subject", "round", "phase", "roundType", "baseline", "modelHash", "eyesHash", "items", "runs", "ledger"]);
export const ITEM_LISTS = Object.freeze(["decided", "tried", "parked", "open"]);
export const LEDGER_MARK = "<!-- generated from state.json by scripts/v7/gold.mjs: never edit by hand (the ledger entries live in state.json) -->";
const EPS = 1e-9;

const isNum = (v) => typeof v === "number" && Number.isFinite(v);
const f3 = (x) => (isNum(x) ? x.toFixed(3).replace(/^(-?)0\./, "$1.") : "-");
const f4 = (x) => (isNum(x) ? x.toFixed(4) : "-");
const pct = (x, d = 1) => (isNum(x) ? `${(x * 100).toFixed(d)} %` : "-");
export const oneLine = (s) => String(s ?? "").replace(/\r?\n+/g, " ").replace(/\s+/g, " ").trim();
const cut = (s, n) => { const t = oneLine(s); return t.length > n ? `${t.slice(0, n - 1)}…` : t; };

/** argv -> { _: positionals, <flag>: value | true } (scripts/v7/lib.mjs parseArgs, without its heavy imports). */
export function parseArgs(argv, booleans = []) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (!a.startsWith("--") || /^--?\d/.test(a)) { out._.push(a); continue; }
    const eq = a.indexOf("=");
    if (eq > 0) { out[a.slice(2, eq)] = a.slice(eq + 1); continue; }
    const name = a.slice(2);
    const next = argv[i + 1];
    if (booleans.includes(name) || next === undefined || (next.startsWith("--") && !/^--?\d/.test(next))) out[name] = true;
    else { out[name] = next; i += 1; }
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------------------------------------------------

/** Validate gold.config.json's numbers (throws naming every bad key); returns the config. */
export function checkConfig(c, where = "gold.config.json") {
  const errs = [];
  const num = (v, p, lo, hi, int = false) => {
    if (!(isNum(v) && v >= lo && v <= hi && (!int || Number.isInteger(v)))) errs.push(`${p} = ${JSON.stringify(v)} (want ${int ? "an integer" : "a number"} in [${lo}, ${hi}])`);
  };
  num(c?.rounds?.cap, "rounds.cap", 1, 20, true);
  for (const t of ROUND_TYPES) num(c?.rounds?.types?.[t]?.calls, `rounds.types.${t}.calls`, 1, 2000, true);
  num(c?.critics?.maxTurns, "critics.maxTurns", 1, 500, true);
  num(c?.critics?.maxItems, "critics.maxItems", 1, 50, true);
  num(c?.bar?.agree, "bar.agree", 0, 1);
  for (const k of ["viewOnly", "conceptOnlyBlob", "aspect"]) {
    num(c?.setupHull?.[k]?.warn, `setupHull.${k}.warn`, 0, 1);
    num(c?.setupHull?.[k]?.block, `setupHull.${k}.block`, 0, 1);
    if (isNum(c?.setupHull?.[k]?.warn) && isNum(c?.setupHull?.[k]?.block) && c.setupHull[k].block < c.setupHull[k].warn) errs.push(`setupHull.${k}: block < warn`);
  }
  for (const k of ["viewOnlyDrop", "conceptOnlyBlobRise", "aspectGrow"]) num(c?.setupHull?.keep?.[k], `setupHull.keep.${k}`, 0, 1);
  if (c?.setupStop !== undefined) { num(c.setupStop?.sets, "setupStop.sets", 1, 20, true); num(c.setupStop?.view, "setupStop.view", 1, 20, true); }
  if (!Array.isArray(c?.eyes?.files) || !c.eyes.files.every((f) => typeof f === "string")) errs.push("eyes.files must be a list of paths");
  if (!Array.isArray(c?.eyes?.subject) || !c.eyes.subject.every((f) => typeof f === "string")) errs.push("eyes.subject must be a list of path templates");
  if (errs.length) throw new Error(`${where}: ${errs.join("; ")}`);
  return c;
}

/** gold.config.json (or `file`), validated. */
export function loadConfig(file = CONFIG_FILE) {
  return checkConfig(JSON.parse(fs.readFileSync(file, "utf8")), path.basename(file));
}

/** The round type of round `r` under a cap: r1 build, the cap round (and any owner extra round) polish, else list. */
export const roundTypeOf = (r, cap) => (r <= 1 ? "build" : r >= cap ? "polish" : "list");

/** "32,14" (tool calls, minutes) -> {calls, minutes}; null for nothing. */
export function parseRun(v) {
  if (v === undefined || v === null || v === true || v === "") return null;
  const m = /^\s*(\d+)\s*(?:,\s*(\d+(?:\.\d+)?)\s*)?$/.exec(String(v));
  if (!m) throw new Error(`--run "${v}": want <tool calls>,<minutes> (e.g. 57,23)`);
  return { calls: Number(m[1]), minutes: m[2] !== undefined ? Number(m[2]) : null };
}

// ---------------------------------------------------------------------------------------------------------------------
// state.json
// ---------------------------------------------------------------------------------------------------------------------

export function newState(subject) {
  return { subject, round: 0, phase: "setup", roundType: "build", baseline: null, modelHash: null, eyesHash: null,
    items: { decided: [], tried: [], parked: [], open: [] }, runs: [], ledger: [] };
}

/** Shape errors of a state.json (WF-V8-PLAN.md "Shared data"); [] = valid. */
export function checkState(st) {
  const e = [];
  if (!st || typeof st !== "object" || Array.isArray(st)) return ["state.json is not an object"];
  if (typeof st.subject !== "string" || !st.subject) e.push("subject: a non-empty string");
  if (!Number.isInteger(st.round) || st.round < 0) e.push(`round ${JSON.stringify(st.round)}: an integer >= 0`);
  if (!PHASES.includes(st.phase)) e.push(`phase ${JSON.stringify(st.phase)}: one of ${PHASES.join(" | ")}`);
  if (st.roundType !== null && !ROUND_TYPES.includes(st.roundType)) e.push(`roundType ${JSON.stringify(st.roundType)}: one of ${ROUND_TYPES.join(" | ")}`);
  if (st.baseline !== null && (typeof st.baseline !== "object" || typeof st.baseline.views !== "object")) e.push("baseline: null or {file, views: {<v>: {iou, agree}}}");
  for (const k of ["modelHash", "eyesHash"]) if (st[k] !== null && typeof st[k] !== "string") e.push(`${k}: null or a string`);
  if (!st.items || typeof st.items !== "object") e.push("items: {decided, tried, parked, open}");
  else for (const k of ITEM_LISTS) if (!Array.isArray(st.items[k])) e.push(`items.${k}: a list`);
  if (!Array.isArray(st.runs)) e.push("runs: a list");
  if (!Array.isArray(st.ledger)) e.push("ledger: a list");
  else st.ledger.forEach((x, i) => { if (!x || typeof x.text !== "string" || typeof x.role !== "string" || !Number.isInteger(x.round)) e.push(`ledger[${i}]: {round, role, text}`); });
  return e;
}

/** The state with the contract's key order (extra keys kept after them). */
export function orderState(st) {
  const out = {};
  for (const k of STATE_KEYS) out[k] = st[k] ?? (k === "items" ? { decided: [], tried: [], parked: [], open: [] } : k === "runs" || k === "ledger" ? [] : null);
  for (const [k, v] of Object.entries(st)) if (!(k in out)) out[k] = v;
  return out;
}

export const serializeState = (st) => `${JSON.stringify(orderState(st), null, 2)}\n`;

// ---------------------------------------------------------------------------------------------------------------------
// LEDGER.md — generated from state.ledger (one entry = one line, verbatim)
// ---------------------------------------------------------------------------------------------------------------------

export const ledgerHeader = (subject, views) => `# LEDGER — ${subject} (one factual line per step; IoU = ${[...views, "concept"].join(" / ")})`;

export function renderLedger(st, views) {
  return `${[ledgerHeader(st.subject, views), LEDGER_MARK, ...st.ledger.map((e) => oneLine(e.text))].join("\n")}\n`;
}

/** The role and round of one v7 ledger line (the round of a line without its own = the context round). */
export function roleOf(line, context = 0) {
  let m = /^r(\d+)\s+modeller\b/.exec(line);
  if (m) return { role: "modeller", round: Number(m[1]) };
  m = /^r(\d+)\s+critics?\b/.exec(line);
  if (m) return { role: "critics", round: Number(m[1]) };
  m = /^K\d+\s+r(\d+)\b/.exec(line);
  if (m) return { role: "variants", round: Number(m[1]) };
  m = /^(drift|note|eyes|gate|open|setup|audit|end|owner|doctor|drift-rm)\b/i.exec(line);
  return { role: m ? m[1].toLowerCase() : "note", round: context };
}

/** A v7 LEDGER.md -> {header, entries: [{round, role, text}]}: every line but the header (and the generated mark) verbatim. */
export function importLedger(text) {
  const lines = String(text).split(/\r?\n/);
  while (lines.length && lines[lines.length - 1] === "") lines.pop();
  let header = null, round = 0;
  const entries = [];
  lines.forEach((line, i) => {
    if (i === 0 && line.startsWith("# LEDGER")) { header = line; return; }
    if (line === LEDGER_MARK) return;
    const r = roleOf(line, round);
    if (r.role === "modeller" || r.role === "critics") round = Math.max(round, r.round);
    entries.push({ round: r.round, role: r.role, text: line });
  });
  return { header, entries };
}

/**
 * Lines of an on-disk LEDGER.md that state.ledger does not hold (hand-written after the last generation: another worker,
 * a person) as entries to append — so the next regeneration loses nothing. The header and the generated mark are skipped.
 */
export function extraLedgerLines(fileText, entries, round = 0) {
  // compared one-lined: LEDGER.md renders every entry through oneLine, so an entry whose text carries a double space or a
  // newline must still match its own rendered line (2026-09-28: forklift's "setup audit applied" line with ";  ·" was
  // re-imported on every read — 30 copies, and every later commit message reused it as its headline)
  const have = new Map();
  for (const e of entries) { const k = oneLine(e.text); have.set(k, (have.get(k) ?? 0) + 1); }
  const out = [];
  for (const e of importLedger(fileText).entries) {
    const k = oneLine(e.text);
    const n = have.get(k) ?? 0;
    if (n > 0) { have.set(k, n - 1); continue; }
    out.push({ ...roleOf(e.text, round), text: e.text });
  }
  return out;
}

/**
 * The ledger after the extraLedgerLines one-line bug (before 2026-09-28): every entry one-lined, and every entry that is
 * the one-lined copy of an EARLIER entry whose text was not one line dropped (those copies were imported from the
 * rendered LEDGER.md on every read). Returns {entries, dropped: [index in the input]}.
 */
export function repairLedger(entries) {
  const raw = new Set();
  const out = [], dropped = [];
  entries.forEach((e, i) => {
    const t = oneLine(e.text);
    if (e.text !== t) { raw.add(t); out.push({ ...e, text: t }); return; }
    if (raw.has(t)) { dropped.push(i); return; }
    out.push(e);
  });
  return { entries: out, dropped };
}

// ---------------------------------------------------------------------------------------------------------------------
// Ledger lines (generated; a line starts with its role)
// ---------------------------------------------------------------------------------------------------------------------

const viewCols = (views, order, k) => order.map((v) => f3(views?.[v]?.[k] ?? views?.[v]?.iou)).join("/");
const hasDrift = (views) => Object.values(views ?? {}).some((m) => isNum(m?.agree) && isNum(m?.iou) && Math.abs(m.agree - m.iou) > 1e-9);

/** Per-view agree (and raw IoU where drift rects mask something) in `order`, with the change vs `base`. */
export function viewsText(views, order, base = null) {
  const bits = [`agree ${viewCols(views, order, "agree")}`];
  if (hasDrift(views)) bits.push(`iou ${viewCols(views, order, "iou")}`);
  if (base) {
    const d = order.map((v) => {
      const a = views?.[v]?.agree ?? views?.[v]?.iou, b = base?.[v]?.agree ?? base?.[v]?.iou;
      return isNum(a) && isNum(b) ? `${a - b >= 0 ? "+" : "-"}${Math.abs(a - b).toFixed(3).replace(/^0/, "")}` : "?";
    });
    bits.push(`vs start ${d.join("/")}`);
  }
  return bits.join(" · ");
}

/** The modeller's round line (close). report = the modeller's report JSON (or null). */
export function modellerLine({ round, snapshot, views, base, order, gate, tris, budget, kept, report = null, forced = null }) {
  const bits = [`r${round} modeller: ${snapshot}`, viewsText(views, order, base),
    `gate ${gate.pass ? "pass" : `FAIL (${gate.rows.slice(0, 4).join(", ")}${gate.rows.length > 4 ? `, +${gate.rows.length - 4}` : ""})`}`,
    `tris ${tris ?? "?"}/${budget ?? "?"}`, `${kept} kept step${kept === 1 ? "" : "s"}`];
  if (forced) bits.push(`closed with --force over: ${cut(forced, 160)}`);
  const items = Array.isArray(report?.items) ? report.items : null;
  if (!report) bits.push("no report");
  else if (items) {
    const by = (s) => items.filter((it) => it.status === s);
    const id = (it) => it.id ?? it.key ?? "?";
    const done = by("done");
    if (done.length) bits.push(`done ${done.map(id).join(", ")}`);
    for (const s of ["partial", "tried", "skipped"]) {
      const l = by(s);
      if (l.length) bits.push(`${s} ${l.map((it) => `${id(it)}${it.why ? ` (${cut(it.why, 90)})` : ""}`).join(", ")}`);
    }
  }
  if (Array.isArray(report?.drift) && report.drift.length) bits.push(`drift proposals ${report.drift.length} (open, owner)`);
  return bits.join(" · ");
}

/** The review's line (merge): seat item counts, the classes, the STOP line. */
export function criticsLine({ round, merged }) {
  const seats = SEATS.filter((s) => merged.seats?.[s]).map((s) => `${s} ${merged.seats[s].items ?? 0} items`).join(" · ");
  const counts = Object.entries(merged.counts ?? {}).filter(([, n]) => n).map(([c, n]) => `${n} ${c}`).join(", ") || "no items";
  const settled = (merged.items ?? []).filter((it) => it.class === "CONFLICT" && it.variant?.settled).map((it) => `${it.id} ${it.variant.settled}`);
  return `r${round} critics: ${seats} · merged (scripts/v7/merge.mjs): ${counts}${settled.length ? ` (settled ${settled.join(", ")})` : ""} · ${merged.stop.line}`;
}

/** The setup doctor's line: the verdict, the BLOCK / WARN ids and the hull numbers. */
export function doctorLine({ verdict, rows, hull = null }) {
  const ids = (l) => rows.filter((r) => r.level === l).map((r) => r.id);
  const b = ids("BLOCK"), w = ids("WARN");
  const bits = [`setup doctor: ${verdict}`, `${b.length} BLOCK${b.length ? ` (${b.join(", ")})` : ""}`, `${w.length} WARN${w.length ? ` (${w.join(", ")})` : ""}`];
  if (hull) bits.push(`hull viewOnly ${Object.entries(hull.views ?? {}).map(([v, m]) => `${v} ${(m.viewOnly * 100).toFixed(1)}`).join(" / ")} %${hull.concept ? ` · conceptOnlyBlob ${pct(hull.concept.conceptOnlyBlob)} · concept IoU ${f3(hull.concept.iou)}` : ""}${hull.aspect ? ` · aspect H/W ${hull.aspect.HoverW >= 0 ? "+" : ""}${(hull.aspect.HoverW * 100).toFixed(1)} L/W ${hull.aspect.LoverW >= 0 ? "+" : ""}${(hull.aspect.LoverW * 100).toFixed(1)} %` : ""}`);
  return bits.join(" · ");
}

// ---------------------------------------------------------------------------------------------------------------------
// Items: merge results and the modeller's report
// ---------------------------------------------------------------------------------------------------------------------

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/** Add `entry` to state.items[list] unless an equal one (by `keyFn`) is there. */
export function addItem(st, list, entry, keyFn = (x) => x.key) {
  const arr = st.items[list];
  if (!arr.some((x) => same(keyFn(x), keyFn(entry)))) arr.push(entry);
}

/**
 * The merge's result into the state (gold.mjs merge): tried / parked from merged.stateAdd; a CONFLICT settled by the
 * variants table -> decided (the winner's value, or the BASE value when BASE won); the owner packet -> open (owner);
 * the ledger line; the phase: CONTINUE -> model, round + 1; STOP / OWNER -> owner. Mutates and returns `st`.
 */
export function applyMerge(st, merged, { cap, runs = {} }) {
  const round = merged.round ?? st.round;
  for (const t of merged.stateAdd?.tried ?? []) addItem(st, "tried", t, (x) => [x.key, x.dir, x.round]);
  for (const p of merged.stateAdd?.parked ?? []) addItem(st, "parked", p);
  for (const it of merged.items ?? []) {
    if (it.class !== "CONFLICT" || !it.variant?.settled) continue;
    const base = it.variant.rows?.find((r) => r.tag === "BASE");
    const value = it.variant.settled === "BASE" ? base?.value ?? null : it.target;
    const win = (it.variant.lines ?? []).find((l) => l.startsWith("WINNER")) ?? `WINNER ${it.variant.winner}`;
    addItem(st, "decided", { key: it.key, value, basis: `variants concept-first r${round} (${it.variant.settled === "BASE" ? "BASE kept" : `${it.variant.settled}'s want`})`, round, evidence: `${it.id}: ${win}` });
  }
  for (const o of merged.owner ?? []) addItem(st, "open", { key: o.key, text: `r${round} ${o.id} ${o.class}: ${cut(o.reason, 200)}`, owner: true }, (x) => [x.key, x.text]);
  for (const seat of SEATS) {
    if (!merged.seats?.[seat]) continue;
    const r = runs[seat] ?? null;
    st.runs.push({ role: "critic", seat, round, calls: r?.calls ?? null, minutes: r?.minutes ?? null, ok: true });
  }
  st.ledger.push({ round, role: "critics", text: criticsLine({ round, merged }) });
  const v = merged.stop.verdict;
  if (v === "CONTINUE") { st.phase = "model"; st.round = round + 1; st.roundType = roundTypeOf(st.round, cap); }
  else st.phase = "owner";
  return st;
}

/** The direction a modeller's tried item moved (merge.mjs dirOf convention): explicit dir, else from -> to, else =to. */
export function reportDir(it) {
  if (typeof it.dir === "string" && it.dir) return it.dir;
  if (/\.(add|remove)$/.test(String(it.key ?? ""))) return String(it.key).split(".").pop();
  if (isNum(it.from) && isNum(it.to)) return it.to > it.from + 1e-12 ? "+" : it.to < it.from - 1e-12 ? "-" : "0";
  return `=${String(it.to ?? "").trim().toLowerCase()}`;
}

/** The modeller's report (report/rN-modeller.json) into the state: tried, decided, open, drift proposals (open, owner). */
export function applyReport(st, report, round) {
  if (!report || typeof report !== "object") return st;
  for (const it of Array.isArray(report.items) ? report.items : []) {
    if (it?.status !== "tried" || typeof it.key !== "string") continue;
    addItem(st, "tried", { key: it.key, dir: reportDir(it), round, result: cut(`${it.id ? `${it.id}: ` : ""}${it.why ?? "tried"}`, 200) }, (x) => [x.key, x.dir, x.round]);
  }
  for (const d of Array.isArray(report.decided) ? report.decided : []) {
    if (typeof d?.key !== "string") continue;
    addItem(st, "decided", { key: d.key, value: d.value ?? null, basis: d.basis ?? "modeller", round, evidence: cut(d.evidence ?? "", 240) });
  }
  for (const o of Array.isArray(report.open) ? report.open : []) {
    if (typeof o?.text !== "string") continue;
    addItem(st, "open", { key: o.key ?? `fact:r${round}-open`, text: `r${round} modeller: ${cut(o.text, 200)}`, owner: !!o.owner }, (x) => [x.key, x.text]);
  }
  for (const d of Array.isArray(report.drift) ? report.drift : []) {
    if (typeof d?.image !== "string") continue;
    addItem(st, "open", { key: `drift:${d.image}`, text: `r${round} modeller proposes a drift rect ${JSON.stringify(d.rect ?? null)} decides ${d.decides ?? "?"} — ${cut(d.why ?? "", 160)} (gold.mjs drift add, owner-approved, at a round boundary)`, owner: true }, (x) => [x.key, x.text]);
  }
  return st;
}

// ---------------------------------------------------------------------------------------------------------------------
// The phase machine: what to type next
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The NEXT command of a subject. facts: {doctor: {verdict, hullLevel, stale} | null, audit: {done, verdict, semantic,
 * regenerate} | null, briefOpen (a modeller brief exists for this round), critiques: {opus, sonnet, fable?: "missing" |
 * "partial" | "done"}, pairSeats (config.critics.seats, the default pair for a fresh round), cmd (the gold.mjs
 * invocation prefix), flags (--dir / --config to repeat), dirRel (the gold dir)}.
 * @returns {{cmd:string, why:string}}
 */
export function nextAction(st, facts) {
  const s = st.subject;
  const g = facts.cmd ?? "node scripts/v7/gold.mjs";
  const flags = facts.flags ?? "";
  const d = facts.dirRel ?? `out/ref/gold/${s}`;
  if (st.phase === "setup") {
    const doc = facts.doctor;   // (not `d`: the gold dir — 2026-09-28 NEXT printed "show [object Object]/audit/AUDIT.md")
    const stop = facts.turnaroundStop ?? null;
    if (facts.chain) return { cmd: facts.chain.cmd, why: facts.chain.why };   // a new subject's setup chain (gold.mjs new)
    if (!doc || doc.stale) return { cmd: `${g} doctor --subject ${s}${flags}`, why: doc ? "the references changed since the last doctor run" : "no doctor run yet" };
    if (doc.hullLevel === "BLOCK" && !stop?.spent) return { cmd: `node scripts/v7/turnaround.mjs status --subject ${s} --dir out/turnaround/${s} (then repair the contradicted view; gold-model skill SETUP)`, why: "the doctor's hull row BLOCKs: the views contradict each other or the concept" };
    const a = facts.audit;
    if (!a || !a.done) return { cmd: `${g} brief --subject ${s} --role auditor${flags}  → Agent gold-auditor`, why: a ? "the audit is not done (done:false): resume it" : "no setup audit yet" };
    if (a.regenerate && stop?.spent) return { cmd: `${g} brief --subject ${s} --role auditor${flags}  → Agent gold-auditor (re-audit under the setup stop rule: READY with target-wins rulings, no REGENERATE)`, why: `the setup stop rule is spent (${stop.why}) but the audit asks to regenerate` };
    if (a.semantic || a.regenerate) return { cmd: `fix the images the audit names (${a.regenerate ? `REGENERATE: node scripts/v7/turnaround.mjs repair --subject ${s} --dir out/turnaround/${s} --view <v>` : `EDIT of a view: a GPT edit inside the audit rects, then node scripts/v7/turnaround.mjs fix --subject ${s} --dir out/turnaround/${s} --view <v> --image <edited png> --why "<the feature fixed>" --rects "<audit rects>" and turnaround.mjs install --subject ${s} --dir out/turnaround/${s} --force; EDIT of the concept: refs/${s}.v2.png + refs/${s}.v2.README.md + subject.json paths.target`}), then ${g} doctor --subject ${s}${flags} and re-brief the auditor`, why: `audit verdict ${a.verdict ?? "EDIT / REGENERATE"}` };
    // apply-audit ran and doctor BLOCK rows stand unaccepted: an owner ruling, never the orchestrator's (no loop back to the gate)
    if (facts.applied && doc.verdict === "BLOCK") {
      const ids = (doc.blocks ?? []).join(",") || "<ids>";
      return { cmd: `OWNER: doctor BLOCK row(s) ${ids} stand after the setup audit — the owner accepts them (${g} apply-audit --subject ${s} --owner-approved --owner-note "<the owner's words>" --accept-blocks ${ids}${flags}) or the reference is fixed (EDIT, then doctor + re-audit); a marathon parks the subject (${g} owner-packet --subject ${s})`, why: "the setup audit is applied but the doctor still BLOCKs on rows nobody accepted" };
    }
    return { cmd: `OWNER setup gate: show ${d}/audit/AUDIT.md (+ hull.png, audit/view); after approval: ${g} apply-audit --subject ${s} --owner-approved${flags}`, why: `audit ${a.verdict ?? "READY"}` };
  }
  if (st.phase === "model") {
    if (!facts.briefOpen) return { cmd: `${g} brief --subject ${s} --role modeller${flags}`, why: `round ${st.round} (${st.roundType}) has no brief yet` };
    return { cmd: `Agent gold-modeller with ${d}/brief/r${st.round}-modeller.md; then ${g} close --subject ${s} --run <calls>,<minutes>${flags}`, why: `round ${st.round} is open` };
  }
  if (st.phase === "review") {
    const c = facts.critiques ?? {};
    // the pair for THIS round: whichever seats have already started (done or partial) — a round already under a legacy
    // fable + opus pairing continues on it; a fresh round briefs the configured default (DEFAULT_PAIR: opus + sonnet)
    // a class with ONE critic seat (class weapon: pairSeats ["opus"], owner 2026-10-12) briefs and merges that seat alone
    const single = Array.isArray(facts.pairSeats) && facts.pairSeats.length === 1;
    const def = Array.isArray(facts.pairSeats) && (facts.pairSeats.length === 2 || single) ? facts.pairSeats : DEFAULT_PAIR;
    const started = SEATS.filter((x) => c[x] && c[x] !== "missing");
    const pair = single ? [...def] : (started.length >= 2 ? started : [...new Set([...started, ...def])]).slice(0, 2);
    const todo = pair.filter((x) => c[x] !== "done");
    if (todo.length) return { cmd: todo.map((x) => `${g} brief --subject ${s} --role critic --seat ${x}${flags}`).join(" ; ") + (single ? `  → Agent gold-critic-${todo[0]}` : `  → Agents ${todo.map((x) => `gold-critic-${x}`).join(" + ")} in parallel`), why: todo.map((x) => `${x} ${c[x] ?? "missing"}`).join(", ") };
    return { cmd: `${g} merge --subject ${s} ${pair.map((x) => `--${x} <calls>,<minutes>`).join(" ")}${flags}`, why: single ? "the critique is done" : "both critiques are done" };
  }
  if (st.phase === "owner") return { cmd: `OWNER: show ${d}/OWNER.md; then ${g} owner --subject ${s} --accept | --review | --extra-round${flags}`, why: "the workflow stopped (STOP / OWNER / the round cap)" };
  return { cmd: "none", why: "done" };
}

/** Drift rects change only at a round boundary: setup / owner / done, or phase model before the round's brief. */
export function driftBoundary(st, briefOpen) {
  if (["setup", "owner", "done"].includes(st.phase)) return { ok: true, why: `phase ${st.phase}` };
  if (st.phase === "model" && !briefOpen) return { ok: true, why: `round ${st.round} not started` };
  return { ok: false, why: st.phase === "review" ? `round ${st.round} is under review (the critics were briefed on the current rects)` : `round ${st.round} is open (the modeller's baseline would move)` };
}

// ---------------------------------------------------------------------------------------------------------------------
// Eyes: the files that judge a model (change control, WF-REVIEW-opus.md C11)
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The eyes files of one subject, ROOT-relative: config.eyes.files + config.eyes.subject templates ({s}, {class},
 * {target}, {camera}, {layoutMeasured}, {layout}, {census} = subject.json paths; {views} = every turnaround view image).
 * A template naming a subject path the subject does not have is dropped.
 */
export function eyesFileList(config, { subject, klass, paths = {}, viewFiles = [] }) {
  const out = [...config.eyes.files];
  for (const t of config.eyes.subject) {
    if (t === "{views}") { for (const f of viewFiles) out.push(`subjects/${subject}/turnaround/${f}`); continue; }
    let miss = false;
    const p = t.replace(/\{(\w+)\}/g, (m, k) => {
      if (k === "s") return subject;
      if (k === "class") return klass;
      if (paths[k]) return paths[k];
      miss = true;
      return m;
    });
    if (!miss) out.push(p);
  }
  return [...new Set(out.map((p) => p.replace(/\\/g, "/")))];
}

/** sha256 of each file (ROOT-relative) or null when missing; text files hashed with CRLF -> LF (a checkout's line endings are no eye change). */
export function hashFiles(list, root = ROOT) {
  const out = {};
  for (const f of list) {
    const abs = path.resolve(root, f);
    if (!fs.existsSync(abs)) { out[f] = null; continue; }
    const buf = fs.readFileSync(abs);
    out[f] = createHash("sha256").update(/\.(mjs|js|json|md|txt)$/i.test(f) ? buf.toString("utf8").replace(/\r\n/g, "\n") : buf).digest("hex");
  }
  return out;
}

/** One hash over a {file: sha|null} map (sorted by path). */
export function combineHashes(map) {
  const h = createHash("sha256");
  for (const k of Object.keys(map).sort()) h.update(`${k}\0${map[k] ?? "missing"}\n`);
  return `sha256:${h.digest("hex")}`;
}

/** The files whose hash differs between two maps (added / removed paths count). */
export function changedFiles(a = {}, b = {}) {
  return [...new Set([...Object.keys(a), ...Object.keys(b)])].filter((k) => (a[k] ?? null) !== (b[k] ?? null)).sort();
}

// ---------------------------------------------------------------------------------------------------------------------
// The doctor's `hull` row (scripts/v7/doctor.mjs): hull.mjs hullReport -> WARN / BLOCK on gold.config.json setupHull
// ---------------------------------------------------------------------------------------------------------------------

/**
 * hull.mjs's report (views: {<v>: {viewOnly}}, concept: {conceptOnlyBlob, iou}) against the setup gate {viewOnly: {warn,
 * block}, conceptOnlyBlob: {warn, block}}: a share above warn -> WARN, above block -> BLOCK; one row, id "hull".
 */
export function hullRows(R, gate) {
  const rank = { PASS: 0, WARN: 1, BLOCK: 2 };
  const lvl = (x, g) => (x > g.block + EPS ? "BLOCK" : x > g.warn + EPS ? "WARN" : "PASS");
  let level = "PASS";
  const flagged = [];
  const views = Object.entries(R?.views ?? {});
  for (const [v, m] of views) {
    const l = lvl(m.viewOnly, gate.viewOnly);
    if (rank[l] > rank[level]) level = l;
    if (l !== "PASS") flagged.push(`${v} viewOnly ${pct(m.viewOnly)} ${l}`);
  }
  const C = R?.concept ?? null;
  if (C) {
    const l = lvl(C.conceptOnlyBlob, gate.conceptOnlyBlob);
    if (rank[l] > rank[level]) level = l;
    if (l !== "PASS") flagged.push(`conceptOnlyBlob ${pct(C.conceptOnlyBlob, 2)} ${l}`);
  }
  const g = (x) => `${+(x * 100).toFixed(2)}`;
  const text = [
    `viewOnly ${views.map(([v, m]) => `${v} ${(m.viewOnly * 100).toFixed(1)}`).join(" / ")} % (warn > ${g(gate.viewOnly.warn)}, block > ${g(gate.viewOnly.block)})`,
    C ? `conceptOnlyBlob ${pct(C.conceptOnlyBlob, 2)} (warn > ${g(gate.conceptOnlyBlob.warn)}, block > ${g(gate.conceptOnlyBlob.block)}) · concept IoU ${f3(C.iou)}` : "no concept",
  ].join(" · ") + (level === "PASS" ? "" : ` — ${flagged.join(", ")}: repair the contradicted view (node scripts/v7/turnaround.mjs status / repair; hull.mjs --png shows where)`);
  return [{ level, id: "hull", data: { views: Object.fromEntries(views.map(([v, m]) => [v, m.viewOnly])), conceptOnlyBlob: C?.conceptOnlyBlob ?? null, conceptIoU: C?.iou ?? null }, text: `hull (views vs views, views vs the concept): ${text}` }];
}

// ---------------------------------------------------------------------------------------------------------------------
// JSON text editing that keeps the file's own formatting (views.json is hand-formatted)
// ---------------------------------------------------------------------------------------------------------------------

/** A JSON text's syntax tree with spans: {type, start, end, entries: [{key, keyStart, node}] | items: [node]}. */
export function jsonTree(text) {
  let i = 0;
  const ws = () => { while (i < text.length && /\s/.test(text[i])) i += 1; };
  const fail = (what) => { throw new Error(`json: ${what} at ${i}`); };
  const str = () => {
    const s = i;
    if (text[i] !== '"') fail("expected a string");
    i += 1;
    while (i < text.length && text[i] !== '"') i += text[i] === "\\" ? 2 : 1;
    i += 1;
    return { type: "string", start: s, end: i, value: JSON.parse(text.slice(s, i)) };
  };
  const val = () => {
    ws();
    const c = text[i];
    const s = i;
    if (c === "{") {
      i += 1;
      const entries = [];
      ws();
      if (text[i] === "}") { i += 1; return { type: "object", start: s, end: i, entries }; }
      for (;;) {
        ws();
        const k = str();
        ws();
        if (text[i] !== ":") fail("expected :");
        i += 1;
        entries.push({ key: k.value, keyStart: k.start, node: val() });
        ws();
        if (text[i] === ",") { i += 1; continue; }
        if (text[i] === "}") { i += 1; break; }
        fail("expected , or }");
      }
      return { type: "object", start: s, end: i, entries };
    }
    if (c === "[") {
      i += 1;
      const items = [];
      ws();
      if (text[i] === "]") { i += 1; return { type: "array", start: s, end: i, items }; }
      for (;;) {
        items.push(val());
        ws();
        if (text[i] === ",") { i += 1; continue; }
        if (text[i] === "]") { i += 1; break; }
        fail("expected , or ]");
      }
      return { type: "array", start: s, end: i, items };
    }
    if (c === '"') return str();
    while (i < text.length && /[^\s,\]}]/.test(text[i])) i += 1;
    if (i === s) fail("expected a value");
    return { type: "literal", start: s, end: i };
  };
  const root = val();
  ws();
  if (i < text.length) fail("trailing text");
  return root;
}

const lineIndent = (text, pos) => { const ls = text.lastIndexOf("\n", pos - 1) + 1; return /^[ \t]*/.exec(text.slice(ls))[0]; };

/**
 * Set `keys` (a path of object keys) in a JSON text to the value `fmt(indent)` returns (indent = the key's line indent),
 * replacing only that value's span, or inserting the key after the object's last entry. The rest of the text is
 * byte-identical. Throws when the path's parent is not an object or the result does not parse.
 */
export function setJsonKey(text, keys, fmt) {
  const root = jsonTree(text);
  let node = root;
  for (const k of keys.slice(0, -1)) {
    const e = node.type === "object" ? node.entries.find((x) => x.key === k) : null;
    if (!e || e.node.type !== "object") throw new Error(`setJsonKey: no object at ${keys.slice(0, keys.indexOf(k) + 1).join(".")}`);
    node = e.node;
  }
  if (node.type !== "object") throw new Error("setJsonKey: the root is not an object");
  const last = keys[keys.length - 1];
  const hit = node.entries.find((x) => x.key === last);
  let out;
  if (hit) out = text.slice(0, hit.node.start) + fmt(lineIndent(text, hit.keyStart)) + text.slice(hit.node.end);
  else if (node.entries.length) {
    const le = node.entries[node.entries.length - 1];
    const multi = text.slice(node.start, node.end).includes("\n");
    const ind = multi ? lineIndent(text, le.keyStart) : "";
    out = text.slice(0, le.node.end) + (multi ? `,\n${ind}` : ", ") + `${JSON.stringify(last)}: ${fmt(ind)}` + text.slice(le.node.end);
  } else {
    const ind = `${lineIndent(text, node.start)}  `;
    out = `${text.slice(0, node.start)}{\n${ind}${JSON.stringify(last)}: ${fmt(ind)}\n${ind.slice(2)}}${text.slice(node.end)}`;
  }
  JSON.parse(out);
  return out;
}

/** One-line JSON with a space after , and : and inside {} (`{ "id": "D1", "rect": [1, 2, 3, 4] }`). */
export function inlineJson(v) {
  if (Array.isArray(v)) return `[${v.map(inlineJson).join(", ")}]`;
  if (v && typeof v === "object") { const e = Object.entries(v); return e.length ? `{ ${e.map(([k, x]) => `${JSON.stringify(k)}: ${inlineJson(x)}`).join(", ")} }` : "{}"; }
  return JSON.stringify(v);
}

/** views.json `drift` as text at `indent`: notes inline, one rect per line. */
export function driftJson(drift, indent = "  ") {
  const pad = `${indent}  `;
  const rows = Object.entries(drift).map(([k, v]) => (Array.isArray(v)
    ? (v.length ? `${pad}${JSON.stringify(k)}: [\n${v.map((e) => `${pad}  ${inlineJson(e)}`).join(",\n")}\n${pad}]` : `${pad}${JSON.stringify(k)}: []`)
    : `${pad}${JSON.stringify(k)}: ${inlineJson(v)}`));
  return rows.length ? `{\n${rows.join(",\n")}\n${indent}}` : "{}";
}

// ---------------------------------------------------------------------------------------------------------------------
// Brief texts (gold.mjs brief): the data in, markdown out
// ---------------------------------------------------------------------------------------------------------------------

/** The step.mjs blob line of one view (step.mjs blobsLine). */
export function blobLine(v, list, n = 5) {
  if (!list?.length) return `blobs ${v}: none`;
  const f2 = (x) => x.toFixed(2);
  const tok = (b) => {
    const where = Array.isArray(b.bbox) ? `x${b.bbox[0]}..${b.bbox[2]} y${b.bbox[1]}..${b.bbox[3]}` : `r${f2(b.bbox.right[0])}..${f2(b.bbox.right[1])} u${f2(b.bbox.up[0])}..${f2(b.bbox.up[1])}${b.bboxPx ? ` (px ${b.bboxPx.join(",")})` : ""}`;
    return `${b.kind === "missing" ? "miss" : "extra"} ${b.px}px ${b.kind === "missing" ? "~" : ""}${b.part ?? "-"} ${where}`;
  };
  return `blobs ${v}: ${list.slice(0, n).map(tok).join(" · ")}`;
}

/** The per-view table of a step record (views: {<v>: {iou, agree, drift}}). */
export function viewTable(views, order, bar) {
  const L = ["| image | iou | agree | drift | vs the bar |", "|---|---|---|---|---|"];
  for (const v of order) {
    const m = views?.[v];
    if (!m) continue;
    const a = m.agree ?? m.iou;
    L.push(`| ${v} | ${f4(m.iou)} | ${f4(a)} | ${pct(m.drift ?? 0)} | ${a >= bar - EPS ? "ok" : `${(a - bar).toFixed(4)}`} |`);
  }
  return L.join("\n");
}

function itemsSection(items, { tried = true, parked = true } = {}) {
  const L = [];
  const val = (x) => (x === null || x === undefined ? "—" : typeof x === "string" ? x : JSON.stringify(x));
  L.push("### Decided — do not re-litigate (reopen only with a NEW measurement on the decided item's basis image)");
  L.push(...(items.decided.length ? items.decided.map((d) => `- ${d.key} = ${val(d.value)} (r${d.round ?? "?"}, ${d.basis ?? "?"})${d.evidence ? ` — ${cut(d.evidence, 200)}` : ""}`) : ["- none"]));
  if (tried) {
    L.push("### Tried — the same key in the same direction again is TRIED (twice: PARKED)");
    L.push(...(items.tried.length ? items.tried.map((t) => `- ${t.key} ${t.dir} (r${t.round ?? "?"}): ${cut(t.result ?? "", 200)}`) : ["- none"]));
  }
  if (parked) {
    L.push("### Parked — the owner decides; do not raise or build them");
    L.push(...(items.parked.length ? items.parked.map((p) => `- ${p.key} (r${p.round ?? "?"}): ${cut(p.reason ?? "", 200)}`) : ["- none"]));
  }
  L.push("### Open");
  L.push(...(items.open.length ? items.open.map((o) => `- ${o.key}${o.owner ? " (owner)" : ""}: ${cut(o.text, 240)}`) : ["- none"]));
  return L.join("\n");
}

function driftSection(drift) {
  const L = [];
  const lists = Object.entries(drift ?? {}).filter(([, l]) => Array.isArray(l));
  if (!lists.length || lists.every(([, l]) => !l.length)) return "- none (every px of every image is scored)";
  for (const [img, list] of lists) for (const d of list) L.push(`- ${img} ${d.id} [${d.rect.join(", ")}] decides ${d.decides ?? "?"} — ${cut(d.why ?? "", 200)}`);
  if (drift.audited) L.push(`- audited: ${drift.audited}`);
  return L.join("\n");
}

const fence = (t) => `\`\`\`\n${String(t).replace(/\s+$/, "")}\n\`\`\``;

/**
 * A seat brief's turn budget line (2026-09-28: every Opus critic of the marathon hit its 40-turn cap and wrote a cut-short
 * list): the budget, where it comes from, "write as you go", the 75 % mark, how to finish.
 */
export function budgetLine(turns, source, stopWhat = "stop measuring", finish = "finish with done:true") {
  return `Budget: ≤ ${turns} turns (${source}). Write each item to the JSON as you go; ${stopWhat} at 75 % of the budget (turn ${Math.floor(turns * 0.75)}); ${finish}.`;
}

/** The ledger a critic seat may read: every line but the critic-review lines (no seat reads another seat's critique). */
export const ledgerFacts = (st) => st.ledger.filter((e) => e.role !== "critics").map((e) => e.text);

/**
 * The modeller's brief. d: {subject, round, cap, type, calls, rule, at, dirRel, start, dims, concept, turnaround, viewFiles,
 * order, bar, baseline: {file, views, blobs, probes, chain, tris, budget}, worksheet: {file, text} | null, items, drift,
 * keysText, partsText, eyesFiles, resume: {steps: [...]} | null, ledger: [text]}
 */
export function briefModeller(d) {
  const g = `node scripts/v7/step.mjs --subject ${d.subject}${d.moduleFlag ?? ""}`;
  const L = [];
  L.push(`# gold-modeller brief — ${d.subject}, round ${d.round} (${d.type}${d.round > d.cap ? ", the owner's extra round" : ""} · ≤ ${d.calls} tool calls)`);
  L.push(`Written by \`node scripts/v7/gold.mjs brief --subject ${d.subject} --role modeller\` (${d.at}). This file is your whole task; your`);
  L.push("agent body (.claude/agents/gold-modeller.md) holds the rules. Run every command from D:\\Git\\anyCreature\\hard_surface.");
  if (d.resume) {
    L.push("", "## RESUME — this round is already open", `The round started ${d.resume.startedAt}; ${d.resume.steps.length} step(s) were saved since (below). Continue from \`${d.dirRel}/model.mjs\`; the baseline stays the round start. Finish the report.`);
    for (const s of d.resume.steps) L.push(`- ${s.file}${s.note ? ` "${cut(s.note, 120)}"` : ""}`);
  }
  L.push("", "## Round");
  L.push(`- Module: \`${d.dirRel}/model.mjs\` (the round start = \`${d.start}\`). Round ${d.round} of ${d.cap}: **${d.type}** — ${d.rule}. Budget ≤ ${d.calls} tool calls.`);
  L.push(`- Registered size (the model is built to it): ${d.dims}.`);
  L.push(`- References: concept \`${d.concept}\` (THE source of truth) · turnaround \`${d.turnaround}/\` ${d.viewFiles.join(", ")} (hidden faces and proportions; where it disagrees with the concept, the concept wins, except inside a drift rect whose \`decides\` names the view).`);
  L.push(`- The bar: agree ≥ ${d.bar} in every image (agree = IoU outside the drift rects); raw IoU is reported too.`);
  L.push(`- One command per iteration: edit model.mjs → \`${g}\` → KEEP: \`${g} --save --note "<what changed>"\` · REVERT: \`${g} --revert\`.`);
  L.push(`- Look only when a number cannot tell: \`${g} --pages side,concept\` (→ \`${d.dirRel}/steps/pages/\`).`);
  L.push(`- Knob / DEFAULTS values in one call: \`node scripts/v7/variants.mjs --subject ${d.subject} --module ${d.dirRel}/model.mjs --rule concept-first '{"<knob>":<a>}' '{"<knob>":<b>}'\`.`);
  L.push(`- Report: \`${d.dirRel}/report/r${d.round}-modeller.json\` — write it FIRST (done:false), rewrite it after every item, done:true at the end.`);
  if (d.maxTurns) L.push(`- ${budgetLine(Math.min(d.maxTurns, d.calls), `the round's ≤ ${d.calls} tool calls; your agent's maxTurns ${d.maxTurns}`, "start no new item", "finish the report with done:true")}`);
  L.push("", `## Baseline — the round start (\`${d.baseline.file}\`, step.mjs --json)`);
  L.push(viewTable(d.baseline.views, d.order, d.bar));
  for (const v of d.order) L.push(`- ${blobLine(v, d.baseline.blobs?.[v])}`);
  L.push(`- gate: chain ${d.baseline.chain?.pass ? "pass" : "FAIL"}${d.baseline.chain?.rows?.length ? ` (${d.baseline.chain.rows.map((r) => `${r.v}${r.part ? ` ${r.part}` : ""}`).slice(0, 8).join(", ")})` : ""} · tris ${d.baseline.tris ?? "?"} / ${d.baseline.budget ?? "?"}`);
  if (d.baseline.probes?.length) L.push(`- probes: ${d.baseline.probes.length} (subjects/${d.subject}/probes.json; step.mjs prints them)`);
  L.push("", "## Worksheet");
  if (d.worksheet) {
    L.push(`\`${d.worksheet.file}\` (scripts/v7/merge.mjs). Order: A, then B, CONFLICT (a settled row: apply the WINNER; unsettled: measure and decide), X (build both — two variants or two edits — and keep the step.mjs / concept-first winner), then C when cheap. TRIED: find another way or leave it, and say which. REJECTED / REJECTED-DRIFT / DECIDED / PARKED: do not build.`);
    L.push("", d.worksheet.text.replace(/\s+$/, ""));
  } else {
    L.push(d.round <= 1
      ? "None — the build round. Your list: the blob table above (largest first), the decided facts and drift rects below, then the concept feature by feature (silhouette, proportions, features, colour)."
      : "None found (no merged worksheet of the previous round): work from the blob table.");
  }
  L.push("", "## Facts (state.json)", itemsSection(d.items));
  L.push("", "## Drift rects (views.json; agree ignores their px; `decides` = the image that is right inside)", driftSection(d.drift));
  L.push("", `## Keys — the names critics and merges use (\`node scripts/v7/merge.mjs --keys --module ${d.dirRel}/model.mjs\`)`, fence(d.keysText || "(none)"));
  L.push("", `## Parts (\`node scripts/v7/inspect.mjs parts --module ${d.dirRel}/model.mjs\`)`, fence(d.partsText || "(none)"));
  L.push("", "## Never edit (the eyes: `gold.mjs close` refuses when any of them changed)", d.eyesFiles.map((f) => `\`${f}\``).join(" · "));
  L.push("", "## Ledger so far", ...(d.ledger?.length ? d.ledger.map((t) => `- ${t}`) : ["- (empty)"]));
  return `${L.join("\n")}\n`;
}

/**
 * A critic seat's brief. d: {subject, round, seat, at, dirRel, dims, concept, turnaround, viewFiles, order, bar, maxItems,
 * pages: [paths], sheet, baseline: {file, views, blobs}, items, drift, keysText, partsText, families, resume: {items} | null,
 * ledger: [text] (no critics lines)}
 */
export function briefCritic(d) {
  const out = `${d.dirRel}/critique/r${d.round}-${d.seat}`;
  const L = [];
  L.push(`# gold-critic-${d.seat} brief — ${d.subject}, review of round ${d.round}`);
  L.push(`Written by \`node scripts/v7/gold.mjs brief --subject ${d.subject} --role critic --seat ${d.seat}\` (${d.at}). This file is your whole task;`);
  L.push(`your agent body (.claude/agents/gold-critic-${d.seat}.md) holds the rules. Run every command from D:\\Git\\anyCreature\\hard_surface.`);
  L.push("Work blind: another seat reviews the same model now. Never open anything under critique/ except your own two output files.");
  if (d.resume) L.push("", "## RESUME", `\`${out}.json\` exists with done:false and ${d.resume.items} item(s): keep them, continue the list, set done:true at the end.`);
  L.push("", "## What you review");
  L.push(`- The model \`${d.dirRel}/model.mjs\` (read only; = model-r${d.round}.mjs). Registered size: ${d.dims}.`);
  L.push(`- The sheet \`${d.sheet}\` (row 1 references, row 2 the model, row 3 outlines + IoU) and the pages ${d.pages.map((p) => `\`${p}\``).join(", ")} (reference | model | filled diff: blue = missing on the model, red = extra).`);
  L.push(`- References: concept \`${d.concept}\` (THE source of truth) · turnaround \`${d.turnaround}/\` ${d.viewFiles.join(", ")} (image names: concept, ${d.order.filter((v) => v !== "concept").join(", ")}).`);
  L.push("", `## Numbers at close (\`${d.baseline.file}\`, step.mjs; agree = IoU outside the drift rects, the bar ≥ ${d.bar})`);
  L.push(viewTable(d.baseline.views, d.order, d.bar));
  for (const v of d.order) L.push(`- ${blobLine(v, d.baseline.blobs?.[v])}`);
  L.push("", "## Output");
  L.push(`- \`${out}.json\` per \`scripts/v7/critique.schema.json\`: {"subject": "${d.subject}", "round": ${d.round}, "seat": "${d.seat}", "done": false, "items": []} — write it NOW, rewrite it after every item, "done": true at the end. ≤ ${d.maxItems} items, ranked by visual impact.`);
  if (d.maxTurns) L.push(`- ${budgetLine(d.maxTurns, `your agent's maxTurns (.claude/agents/gold-critic-${d.seat}.md)`, "stop measuring", "finish with done:true")}`);
  L.push(`- \`${out}.md\`: one line per item (\`N. [MAJOR|MINOR] <key> — <what> (<basis>)\`), nothing else.`);
  L.push(`- Check before you finish: \`node scripts/v7/merge.mjs --validate ${out}.json\` must print OK.`);
  L.push("- `at.rect` is in the named IMAGE's own px (the turnaround file or the concept), never page px: read px with `node scripts/v7/measure.mjs grid --subject " + d.subject + " --view <image> x0,y0,x1,y1 --module " + d.dirRel + "/model.mjs --diff --out <scratch>.png` (labels are image px).");
  L.push("", "## Keys you may use");
  L.push("`knob:<name>` / `def:<path>` from the table below · `part:<family>.<pos.x|pos.y|pos.z|size.x|size.y|size.z|rot|colour|shape|count|add|remove>` with a family from the parts below · `drift:<image>` (a drift-rect proposal: `at.rect` is the rect).");
  L.push(fence(d.keysText || "(none)"));
  L.push(`Part families: ${d.families || "(none)"}`);
  L.push("", "## Facts (state.json) — decided items stand unless you bring a new measurement on their basis image (`reopens`)", itemsSection(d.items));
  L.push("", "## Drift rects (views.json; the merge rejects an item inside one whose `decides` is another image than your basis)", driftSection(d.drift));
  L.push("", "## Ledger facts (earlier rounds; no critique text)", ...(d.ledger?.length ? d.ledger.map((t) => `- ${t}`) : ["- (none)"]));
  return `${L.join("\n")}\n`;
}

/**
 * The setup auditor's brief. d: {subject, at, dirRel, concept, prompt, turnaround, axes: [{view, file, right, up}],
 * doctor: {file, verdict, rows}, hull: {file, png, summary}, start, maxTurns}
 */
export function briefAuditor(d) {
  const L = [];
  L.push(`# gold-auditor brief — ${d.subject}, setup audit`);
  L.push(`Written by \`node scripts/v7/gold.mjs brief --subject ${d.subject} --role auditor\` (${d.at}). This file is your whole task; your`);
  L.push("agent body (.claude/agents/gold-auditor.md) holds the tasks and output formats. Run every command from D:\\Git\\anyCreature\\hard_surface.");
  L.push("", "## Inputs");
  L.push(`- Concept \`${d.concept}\`; its prompt ${d.prompt ? `\`${d.prompt}\` ("Full prompt")` : "(no prompt file: judge against the class)"}.`);
  L.push(`- Turnaround \`${d.turnaround}/\` — axes (views.json; author frame: nose +z, near flank +x, y up):`);
  for (const a of d.axes) L.push(`  - ${a.view} (${a.file}): image right = ${a.right}, image up = ${a.up}`);
  L.push(`- Start module \`${d.start}\` (a blockout: read the REFERENCE tiles of its sheet).`);
  L.push(`- Doctor \`${d.doctor.file}\`: ${d.doctor.verdict}`);
  for (const r of d.doctor.rows.filter((x) => x.level !== "PASS")) L.push(`  - ${r.level} ${r.id}: ${cut(r.text, 300)}`);
  if (d.hull) L.push(`- Hull \`${d.hull.file}\` + picture \`${d.hull.png}\`: ${d.hull.summary}`);
  L.push("", "## Output (a proposal; nothing else is written)");
  L.push(`- \`${d.dirRel}/audit/audit.json\` (done:false first, rewritten after every task, done:true at the end), \`views.drift.json\`, \`probes.json\`, \`AUDIT.md\`.`);
  L.push(`- Sheet for your reading: \`node scripts/v6/view.mjs --subject ${d.subject} --module ${d.start} --out ${d.dirRel}/audit/view --zoom\`.`);
  L.push(`- The check (must show no drift / probes BLOCK): \`node scripts/v7/doctor.mjs --subject ${d.subject} --no-tools --no-json --drift ${d.dirRel}/audit/views.drift.json --probes ${d.dirRel}/audit/probes.json\`.`);
  L.push(`- ${budgetLine(d.maxTurns, "your agent's maxTurns (.claude/agents/gold-auditor.md)", "stop measuring", "finish AUDIT.md and audit.json with done:true")}`);
  if (d.stopRule) L.push("", "## Setup stop rule (gold.config.json setupStop)", `- ${d.stopRule}`);
  return `${L.join("\n")}\n`;
}

/** The owner packet (OWNER.md). d: {subject, at, round, phase, stop, views, order, bar, chain, tris, budget, items, runs, sheet, pages, snapshot, ledgerFile} */
export function ownerPacket(d) {
  const L = [];
  L.push(`# ${d.subject} — owner packet (scripts/v7/gold.mjs, ${d.at})`);
  L.push(`Phase ${d.phase} after round ${d.round}. ${d.stop ?? ""}`.trim());
  L.push("", `Model \`${d.snapshot}\` · sheet \`${d.sheet}\` · pages ${d.pages.map((p) => `\`${p}\``).join(" ")}`);
  L.push("", viewTable(d.views, d.order, d.bar));
  const below = d.order.filter((v) => d.views?.[v] && (d.views[v].agree ?? d.views[v].iou) < d.bar - EPS);
  L.push("", below.length ? `Below the bar (${d.bar}): ${below.join(", ")} — the blob table names what explains each gap (\`node scripts/v7/step.mjs --subject ${d.subject}\`).` : `Every image at agree ≥ ${d.bar}.`);
  L.push(`Gate: chain ${d.chain?.pass ? "pass" : "FAIL"}${d.chain?.rows?.length ? ` (${d.chain.rows.map((r) => r.v).join(", ")})` : ""} · tris ${d.tris ?? "?"} / ${d.budget ?? "?"}`);
  L.push("", "## For the owner to decide");
  const own = d.items.open.filter((o) => o.owner);
  L.push(...(own.length ? own.map((o) => `- ${o.key}: ${cut(o.text, 300)}`) : ["- nothing open for the owner"]));
  if (d.items.parked.length) L.push("", "## Parked (tried twice, or parked by a merge)", ...d.items.parked.map((p) => `- ${p.key}: ${cut(p.reason, 200)}`));
  if (d.drift) {
    L.push("", `## Drift rects proposed, not in views.json (${d.drift.length}; critiques' drift:* items, modeller reports, the auditor — deduplicated)`);
    if (!d.drift.length) L.push("- none");
    for (const e of d.drift) L.push(`- ${e.image} [${e.rect.join(", ")}] decides ${e.decides ?? "? (the owner names it)"} — ${cut(e.why, 220)} (${e.sources.join(", ")})`, `  \`${e.cmd}\``);
  }
  if (d.rulings) {
    L.push("", "## Setup rulings on record");
    L.push(...(d.rulings.length ? d.rulings.map((r) => `- ${r.key} = ${cut(typeof r.value === "string" ? r.value : JSON.stringify(r.value), 300)}${r.evidence ? ` (${cut(r.evidence, 120)})` : ""}`) : ["- none"]));
    if (d.eyeRulings) {
      L.push("", "Boundary eye changes (gold.mjs override / shift — owner rulings pending ratification):");
      L.push(...(d.eyeRulings.length ? d.eyeRulings.map((r) => `- r${r.round} ${r.kind}: ${cut(r.text, 300)}`) : ["- none"]));
    }
  }
  L.push("", `## Runs (${d.runs.length})`);
  const tot = d.runs.reduce((a, r) => a + (r.calls ?? 0), 0), known = d.runs.filter((r) => isNum(r.calls)).length;
  L.push(`${d.runs.map((r) => `r${r.round} ${r.role}${r.seat ? ` ${r.seat}` : ""} ${r.calls ?? "?"} calls ${r.minutes ?? "?"} min`).join(" · ") || "none recorded"}${known ? ` · ${tot} calls recorded` : ""}`);
  L.push("", d.phase === "owner"
    ? `Ledger: \`${d.ledgerFile}\`. Decide: accept → \`node scripts/v7/gold.mjs owner --subject ${d.subject} --accept${d.flags ?? ""}\` · one more review → \`--review\` · one more modeller round → \`--extra-round\`.`
    : `Ledger: \`${d.ledgerFile}\`. Phase ${d.phase}: the workflow runs on (\`node scripts/v7/gold.mjs status --subject ${d.subject}\`); the items above wait for the owner.`);
  return `${L.join("\n")}\n`;
}

// ---------------------------------------------------------------------------------------------------------------------
// Eye changes at a round boundary: views.json shift (gold.mjs shift), subject.json ruleOverrides (gold.mjs override)
// ---------------------------------------------------------------------------------------------------------------------

/**
 * An eye change (views.json per-view shift, subject.json ruleOverrides) happens at a round boundary only: setup; owner /
 * done; model before the round's first saved step (no brief yet; or briefed with no step: the round start is
 * re-baselined); review before any critic of the round started (the round end and the critics' pages re-made).
 * f: {briefOpen, steps (saved since the brief), criticStarted (a critic brief or critique file of the round)}.
 * @returns {{ok:boolean, why:string, label:string, rebase:null|"start"|"end"}}
 */
export function eyeBoundary(st, { briefOpen = false, steps = 0, criticStarted = false } = {}) {
  const N = st.round;
  if (st.phase === "setup") return { ok: true, why: "setup", label: "setup", rebase: null };
  if (st.phase === "owner" || st.phase === "done") return { ok: true, why: `phase ${st.phase} after r${N}`, label: `r${N} ${st.phase}`, rebase: "end" };
  if (st.phase === "model") {
    if (!briefOpen) return { ok: true, why: `round ${N} not briefed yet`, label: `r${N - 1}/r${N}-boundary`, rebase: null };
    if (!steps) return { ok: true, why: `round ${N} briefed, no step saved`, label: `r${N} start`, rebase: "start" };
    return { ok: false, why: `round ${N} is open with ${steps} saved step(s) (the modeller's baseline would move)`, label: null, rebase: null };
  }
  if (st.phase === "review") {
    if (!criticStarted) return { ok: true, why: `r${N} closed, no critic started`, label: `r${N}-boundary`, rebase: "end" };
    return { ok: false, why: `round ${N} is under review (a critic was briefed on the current eyes)`, label: null, rebase: null };
  }
  return { ok: false, why: `phase ${st.phase}`, label: null, rebase: null };
}

/**
 * The shift sweep's winner. rows: [{label ("BASE" = the current value), value, views: {<image>: agree}}]; the score =
 * the sum of agree over every image (a common-scale side effect counts); rows within `tie` of the best: BASE when it is
 * among them, else the smallest |value|. @returns {{winner: row, rows: [{...row, sum, delta: {<image>: d}}]}}
 */
export function shiftWinner(rows, tie = 0.001) {
  const base = rows.find((r) => r.label === "BASE") ?? rows[0];
  const out = rows.map((r) => {
    const sum = Object.values(r.views).reduce((a, x) => a + x, 0);
    return { ...r, sum, delta: Object.fromEntries(Object.entries(r.views).map(([k, x]) => [k, x - (base.views[k] ?? x)])) };
  });
  const best = Math.max(...out.map((r) => r.sum));
  const near = out.filter((r) => r.sum >= best - tie - 1e-12);
  const winner = near.find((r) => r.label === "BASE") ?? near.sort((a, b) => Math.abs(a.value) - Math.abs(b.value))[0];
  return { winner, rows: out };
}

/** The sweep table: one line per candidate, the agree of every image (the shifted ones and the rest) and the change vs BASE. */
export function shiftTable(res, order, { view, pair = null, axis = "right" } = {}) {
  const labOf = (r) => `${r.label === "BASE" ? "BASE " : ""}${view} ${axis} ${r.value >= 0 ? "+" : ""}${r.value.toFixed(3)}${pair ? ` / ${pair} ${-r.value >= 0 ? "+" : ""}${(-r.value).toFixed(3)}` : ""}`;
  const width = Math.max(9, ...res.rows.map((r) => labOf(r).length));
  const head = `${"candidate".padEnd(width)} ${order.map((v) => v.padStart(8)).join(" ")}   sum Δ`;
  const lines = [head];
  for (const r of res.rows) {
    const lab = labOf(r);
    const cells = order.map((v) => `${f3(r.views[v])}${r.label === "BASE" ? "   " : `${r.delta[v] >= 0 ? "+" : "-"}${Math.abs(r.delta[v]).toFixed(3).replace(/^0/, "")}`}`.padStart(8));
    const dsum = r.sum - res.rows.find((x) => x.label === "BASE").sum;
    lines.push(`${lab.padEnd(width)} ${cells.join(" ")}   ${r.label === "BASE" ? "  0" : `${dsum >= 0 ? "+" : "-"}${Math.abs(dsum).toFixed(3)}`}${r === res.winner ? "  <- WINNER" : ""}`);
  }
  return lines;
}

/**
 * `--wheels count,axles,equal|per-axle[,lo,hi]` [+ `--running tracks|skids`] -> the WP2 wheels override value
 * (kernel-chain.mjs wheelsOverride's shape). Under --running tracks count / axles are the road wheels and their stations
 * (0,0 when the skirts hide them); --running skids takes no --wheels (0 / 0). Without --running: the road vehicle, unchanged.
 */
/** `gold.mjs override --tris <n>`: the subject's V10 triangle budget, an integer 1..cap (kernel-chain TRIS_OVERRIDE_CAP). */
export function trisValue(text, cap = 12000) {
  const n = Number(String(text ?? "").trim());
  if (!(Number.isInteger(n) && n >= 1 && n <= cap)) throw new Error(`--tris ${text}: an integer triangle budget 1..${cap} (the cap)`);
  return n;
}

export function wheelsValue(text, running = null) {
  if (![null, "wheels", "tracks", "skids"].includes(running)) throw new Error(`--running ${running}: tracks | skids | wheels`);
  const nonRoad = running === "tracks" || running === "skids";
  if (running === "skids" && (text === null || text === undefined || text === "")) text = "0,0,equal";
  const p = String(text ?? "").split(",").map((x) => x.trim());
  const [count, axles] = [Number(p[0]), Number(p[1])];
  const diameters = p[2] ?? (nonRoad && count === 0 ? "equal" : undefined);
  if (running === "skids" && !(count === 0 && axles === 0)) throw new Error(`--wheels ${text}: --running skids stands on no wheels (0,0 or no --wheels)`);
  const ok = nonRoad
    ? Number.isInteger(count) && count >= 0 && Number.isInteger(axles) && axles >= (count === 0 ? 0 : 1) && axles <= count
    : Number.isInteger(count) && count >= 1 && Number.isInteger(axles) && axles >= 1 && axles <= count;
  if (!ok) throw new Error(nonRoad ? `--wheels ${text}: road wheels,stations as integers (0,0 or 1 <= stations <= wheels)` : `--wheels ${text}: count,axles as integers (1 <= axles <= count)`);
  if (!["equal", "per-axle"].includes(diameters)) throw new Error(`--wheels ${text}: the third field is equal | per-axle`);
  const v = { count, axles, diameters };
  if (p.length > 3) {
    const lo = Number(p[3]), hi = Number(p[4]);
    if (!(p.length === 5 && lo > 0 && lo < hi)) throw new Error(`--wheels ${text}: diameterFrac as ,lo,hi with 0 < lo < hi`);
    v.diameterFrac = [lo, hi];
  }
  if (nonRoad) v.running = running;
  return v;
}

/** `--mirror-centred p1,p2,...`: the WP2 mirror override value {centred: [pattern, ...]} (kernel-chain.mjs mirrorOverride's
 *  shape) — each pattern is a part id or role regex that VEH_MIRROR exempts from its mirrored-pair requirement. */
export function mirrorCentredValue(text) {
  const patterns = String(text ?? "").split(",").map((x) => x.trim()).filter(Boolean);
  if (!patterns.length) throw new Error("--mirror-centred p1,p2 (part id / role regex patterns, comma separated)");
  for (const p of patterns) {
    try { new RegExp(p); } catch (e) { throw new Error(`--mirror-centred ${text}: pattern ${JSON.stringify(p)} is not a valid regex (${e.message})`); }
  }
  return { centred: [...new Set(patterns)] };
}

/** The PALETTE_ZONE rows of an `inspect.mjs chain` output: {<zone>: {parts, example}} (`VIOLATION PALETTE_ZONE <part> "zone \"<z>\" on N part(s)"`). */
export function paletteZoneViolations(text) {
  const out = {};
  for (const m of String(text).matchAll(/^VIOLATION PALETTE_ZONE (\S+) "zone \\"([^"\\]+)\\" on (\d+) part/gm)) out[m[2]] ??= { parts: Number(m[3]), example: m[1] };
  return out;
}

export const OVERRIDE_COMMENT = "WF v8 WP2 (owner 2026-09-26: TARGET WINS; override names pending ratification). Written by scripts/v7/gold.mjs override; printed as RULE_OVERRIDE advisories. limits.json unchanged.";

/**
 * subject.json ruleOverrides with one override set (WP2 shape {value, evidence}; a `_comment` added when absent).
 * paletteZones merge: the new zones join the old ones and the evidence grows by the new part.
 */
export function withOverride(overrides, name, value, evidence) {
  const out = { ...(overrides ?? {}) };
  if (!out._comment) out._comment = OVERRIDE_COMMENT;
  if ((name === "paletteZones" || name === "roles") && out[name]?.value?.extra) {
    const extra = [...new Set([...out[name].value.extra, ...value.extra])];
    const added = value.extra.filter((z) => !out[name].value.extra.includes(z));
    out[name] = { value: { ...out[name].value, extra }, evidence: added.length ? `${out[name].evidence}; ${evidence}` : out[name].evidence };
    return out;
  }
  if (name === "mirror" && out[name]?.value?.centred) {
    const centred = [...new Set([...out[name].value.centred, ...value.centred])];
    const added = value.centred.filter((z) => !out[name].value.centred.includes(z));
    out[name] = { value: { centred }, evidence: added.length ? `${out[name].evidence}; ${evidence}` : out[name].evidence };
    return out;
  }
  out[name] = { value, evidence };
  return out;
}

// ---------------------------------------------------------------------------------------------------------------------
// The owner packet's collections: proposed drift rects, rulings
// ---------------------------------------------------------------------------------------------------------------------

/** A critic's / modeller's image name -> the subject's image name (a view name, a view file, "concept"), else null. */
export function normImage(image, views = {}) {
  const base = String(image ?? "").trim().replace(/^.*[\\/]/, "").replace(/\.png$/i, "");
  if (/^concept$/i.test(base) || /^refs?$/i.test(base)) return "concept";
  if (views[base]) return base;
  for (const [v, s] of Object.entries(views)) if (String(s.file ?? "").replace(/\.png$/i, "") === base) return v;
  return null;
}

const rectIoU = (a, b) => {
  const ov = Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  const ar = (r) => Math.max(0, r[2] - r[0]) * Math.max(0, r[3] - r[1]);
  return { iou: ov / Math.max(1e-9, ar(a) + ar(b) - ov), inside: ov / Math.max(1e-9, ar(a)) };
};

/** A critique's drift:* items as proposals ({src, round, image, rect, decides, why}); `decides` from the want / now text, else the basis. */
export function critiqueDrift(critique, round, seat, views = {}) {
  const images = [...Object.keys(views), "concept"];
  const out = [];
  (critique?.items ?? []).forEach((it, i) => {
    if (!/^drift:/.test(String(it.key)) || !Array.isArray(it.at?.rect)) return;
    const image = normImage(it.at.image, views) ?? normImage(String(it.key).slice(6), views);
    if (!image) return;
    const text = `${typeof it.want === "string" ? it.want : ""} ${typeof it.now === "string" ? it.now : ""}`;
    const m = /decides\s+(\w+)/i.exec(text);
    let decides = m ? normImage(m[1], views) : typeof it.want === "string" ? normImage(it.want, views) : null;
    if (!decides && images.includes(it.basis) && it.basis !== image) decides = it.basis;
    out.push({ src: `r${round} ${seat} ${i + 1}`, round, image, rect: it.at.rect.map(Number), decides: decides && decides !== image ? decides : null, why: cut(it.note || text || it.key, 220) });
  });
  return out;
}

/**
 * Every PROPOSED drift rect not yet in views.json, deduplicated: sources [{src, round, image, rect, decides, why}] (critique
 * drift:* items, modeller report `drift` lists, the auditor's views.drift.json); `current` = views.json drift. A proposal
 * lying >= 80 % inside, or at IoU >= 0.5 with, a rect of its image already in views.json is dropped; proposals of one image
 * at IoU >= 0.5 (or one >= 80 % inside the other) are one entry (the latest round's rect, every source listed). Each entry carries a ready
 * `gold.mjs drift add ... --owner-approved` line (`--decides <image>` left for the owner when no source names one).
 */
export function driftProposals(sources, current = {}, { subject, flags = "" } = {}) {
  const have = (img) => (Array.isArray(current?.[img]) ? current[img].map((d) => d.rect) : []);
  const fresh = sources.filter((p) => Array.isArray(p.rect) && p.rect.length === 4 && p.rect.every(Number.isFinite) && p.rect[2] > p.rect[0] && p.rect[3] > p.rect[1])
    .filter((p) => !have(p.image).some((r) => { const o = rectIoU(p.rect, r); return o.iou >= 0.5 || o.inside >= 0.8; }))
    .sort((a, b) => b.round - a.round);
  const out = [];
  for (const p of fresh) {
    const hit = out.find((e) => { if (e.image !== p.image) return false; const o = rectIoU(p.rect, e.rect); return o.iou >= 0.5 || o.inside >= 0.8 || rectIoU(e.rect, p.rect).inside >= 0.8; });
    if (hit) { hit.sources.push(p.src); hit.decides ??= p.decides; continue; }
    out.push({ image: p.image, rect: p.rect, decides: p.decides, why: p.why, sources: [p.src] });
  }
  for (const e of out) {
    const why = `${e.why} (proposed: ${e.sources.join(", ")})`.replace(/"/g, "'");
    e.cmd = `node scripts/v7/gold.mjs drift add --subject ${subject} --image ${e.image} --rect ${e.rect.join(",")} --decides ${e.decides ?? "<image>"} --why "${cut(why, 300)}" --owner-approved${flags}`;
  }
  return out.sort((a, b) => a.image.localeCompare(b.image) || a.rect[1] - b.rect[1]);
}

/** The setup rulings on record (decided fact:owner-setup / fact:accepted-blocks) for the owner packet. */
export const setupRulings = (items) => items.decided.filter((d) => /^fact:(owner-setup|accepted-blocks)/.test(d.key));

/**
 * The eye rulings on record for the owner packet: every ledger line of an applied boundary eye change — `gold.mjs override`
 * (subject.json ruleOverrides, role setup) and `gold.mjs shift` (a views.json shift applied, role eyes; "BASE kept" lines
 * changed nothing) — each an owner ruling pending ratification (gold.config.json). -> [{round, kind, text}]
 */
export const eyeRulings = (ledger) => ledger.flatMap((e) => {
  if (e.role === "setup" && /subject\.json ruleOverrides/.test(e.text)) return [{ round: e.round, kind: "override", text: e.text }];
  if (e.role === "eyes" && /eye change: views\.json .*shift\./.test(e.text)) return [{ round: e.round, kind: "shift", text: e.text }];
  return [];
});

/**
 * The setup stop rule (gold.config.json setupStop; 2026-09-28, the marathon needed two re-audit passes): after `sets`
 * failed whole-set regenerations (an attempt that errored or missed a target: `misses(summary)` non-empty) or `view`
 * failed repairs of one view (REVERT / FAILED repair-* records), no more regeneration: gen / repair refuse and the
 * setup audit rules target-wins (READY with rulings) instead of REGENERATE. tst = turnaround.mjs state.json.
 * @returns {{spent:boolean, setsSpent:boolean, sets:number, views:{[v:string]:number}, spentViews:string[], why:string}}
 */
export function setupStopOf(tst, { misses = () => [], sets = 3, view = 3 } = {}) {
  const failedSets = (tst?.attempts ?? []).filter((a) => a.error || !a.summary || misses(a.summary).length).length;
  const views = {};
  for (const r of tst?.repairs ?? []) if (/^repair-/.test(r.id ?? "") && (r.verdict === "REVERT" || r.verdict === "FAILED")) views[r.view] = (views[r.view] ?? 0) + 1;
  const spentViews = Object.entries(views).filter(([, n]) => n >= view).map(([v]) => v);
  const setsSpent = failedSets >= sets;
  const why = [setsSpent ? `${failedSets} failed whole-set regenerations (>= ${sets})` : null, ...spentViews.map((v) => `${views[v]} failed ${v} repairs (>= ${view})`)].filter(Boolean).join("; ");
  return { spent: setsSpent || spentViews.length > 0, setsSpent, sets: failedSets, views, spentViews, why: why || `${failedSets} failed set(s), repairs ${Object.entries(views).map(([v, n]) => `${v} ${n}`).join(" / ") || "none failed"} (limits ${sets} / ${view} per view)` };
}

/**
 * The setup gate's misses of a turnaround.mjs summary (empty = the targets are met): every viewOnly, conceptOnlyBlob,
 * |aspect| per ratio, residuals. T = {viewOnly, conceptOnlyBlob, aspect, residual} (fractions). turnaround.mjs
 * targetMisses is this with its TARGETS; gold.mjs counts the stop rule's failed sets with it.
 */
export function setupMisses(sm, T) {
  const out = [];
  const sg = (x) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(1)} %`;
  for (const [v, m] of Object.entries(sm.views ?? {})) if (m.viewOnly > T.viewOnly + 1e-9) out.push(`viewOnly ${v} ${pct(m.viewOnly, 1)}`);
  if (sm.conceptOnlyBlob > T.conceptOnlyBlob + 1e-9) out.push(`conceptOnlyBlob ${pct(sm.conceptOnlyBlob, 2)}`);
  if (sm.aspect && T.aspect !== undefined) {
    for (const [k, name] of [["HoverW", "H/W"], ["LoverW", "L/W"]]) if (Math.abs(sm.aspect[k]) > T.aspect + 1e-9) out.push(`aspect ${name} ${sg(sm.aspect[k])}`);
  }
  for (const [D, per] of Object.entries(sm.residuals ?? {})) for (const [v, x] of Object.entries(per)) if (Math.abs(x) > T.residual + 1e-9) out.push(`residual ${D} ${v} ${sg(x)}`);
  return out;
}

/** The setup targets of gold.config.json (setupHull warn levels + the doctor's +-3 % residual band). */
export const setupTargetsOf = (config) => ({ viewOnly: config.setupHull.viewOnly.warn, conceptOnlyBlob: config.setupHull.conceptOnlyBlob.warn, aspect: config.setupHull.aspect.warn, residual: 0.03 });

/** The stop rule as the auditor brief states it. */
export function stopRuleText(stop, limits = { sets: 3, view: 3 }, dir = null) {
  const rule = `After ${limits.sets} failed whole-set regenerations or ${limits.view} failed repairs of one view the setup stops regenerating: your verdict is then READY with explicit target-wins rulings — the concept decides; every disagreement becomes a drift rect (\`decides\`) or a decided fact; every doctor BLOCK row the owner must accept goes into audit.json \`acceptBlocks: ["<row id>", ...]\` (apply-audit --accept-blocks audit) — never REGENERATE (turnaround.mjs gen / repair refuse).`;
  if (!stop) return `${rule} No turnaround work folder${dir ? ` (${dir})` : ""}: nothing counted.`;
  return `${rule} ${dir ?? "The turnaround"}: ${stop.spent ? `SPENT — ${stop.why}: REGENERATE is not an option.` : `not spent (${stop.why}).`}`;
}

/** The batch summary (out/ref/gold/OWNER-BATCH.md): one row per subject. rows: [{subject, phase, round, minAgree, owner, drift, rulings, file}] */
export function ownerBatch(rows, at) {
  const L = [`# Owner batch (scripts/v7/gold.mjs owner-packet, ${at})`, "", "| subject | phase | min agree | owner items | drift proposals | setup rulings | packet |", "|---|---|---|---|---|---|---|"];
  for (const r of rows) L.push(`| ${r.subject} | ${r.phase} r${r.round} | ${r.minAgree ?? "-"} | ${r.owner} | ${r.drift} | ${r.rulings} | \`${r.file}\` |`);
  L.push("", "Each packet lists the owner's open items, every proposed drift rect with its ready `gold.mjs drift add ... --owner-approved` line, and the setup rulings on record. Decide per subject: `node scripts/v7/gold.mjs owner --subject <s> --accept | --review | --extra-round`.");
  return `${L.join("\n")}\n`;
}

// ---------------------------------------------------------------------------------------------------------------------
// Commits
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The subject's candidate pathspecs (ROOT-relative; only existing, changed ones are committed): the round's files + the
 * subject's setup files (subject.json — ruleOverrides —, camera / prior, the turnaround's views.json, facts.json,
 * README.md and every image directly in turnaround/: `turnaroundFiles`, the caller's listing; 2026-09-28: the marathon
 * committed these by hand three times).
 */
export function commitCandidates({ subject, dirRel, round, order, turnaroundFiles = [], extra = [] }) {
  const g = dirRel;
  const t = `subjects/${subject}/turnaround`;
  const out = [`${g}/state.json`, `${g}/LEDGER.md`, `${g}/eyes.json`, `${g}/OWNER.md`, `${g}/model.mjs`, `${g}/start.mjs`, `${g}/doctor.json`, `${g}/hull.json`, `${g}/hull.png`,
    `${g}/audit/audit.json`, `${g}/audit/views.drift.json`, `${g}/audit/probes.json`, `${g}/audit/AUDIT.md`,
    `subjects/${subject}/subject.json`, `subjects/${subject}/camera.json`, `subjects/${subject}/prior.json`,
    `${t}/views.json`, `${t}/facts.json`, `${t}/README.md`, ...turnaroundFiles.map((f) => `${t}/${f}`), `subjects/${subject}/probes.json`,
    `${g}/view/model-view.png`, `${g}/view/model-view.json`, ...order.map((v) => `${g}/view/model-${v}.png`), ...extra];
  for (let r = 0; r <= round; r += 1) {
    out.push(`${g}/model-r${r}.mjs`, `${g}/baseline/r${r}-start.json`, `${g}/baseline/r${r}-end.json`, `${g}/report/r${r}-modeller.json`);
    for (const k of [...SEATS, "merged"]) out.push(`${g}/critique/r${r}-${k}.json`, `${g}/critique/r${r}-${k}.md`);
  }
  return [...new Set(out)];
}

/**
 * The commit message: the headline = the newest ledger line this commit adds (`prev` = the number of ledger entries in
 * the committed state.json; null = unknown, then the newest line); the other new lines in the body; no new line = a
 * files-only commit named by what changed (`files`). The co-author trailer last.
 */
export function commitMessage(st, { prev = null, files = [] } = {}) {
  const fresh = prev === null ? st.ledger.slice(-1) : st.ledger.slice(Math.max(0, Math.min(prev, st.ledger.length)));
  const last = fresh[fresh.length - 1];
  const kind = (f) => (/\/turnaround\//.test(f) ? "turnaround" : /\/subject\.json$/.test(f) ? "subject.json" : /\/probes\.json$/.test(f) ? "probes" : /\/(view|baseline)\//.test(f) ? "pages" : path.basename(f));
  const kinds = [...new Set(files.map(kind))];
  const head = last ? cut(last.text, 240) : `files (${st.phase} r${st.round}): ${kinds.join(", ") || "state"}`;
  const body = fresh.length > 1 ? `\n\n${fresh.slice(0, -1).map((e) => `- ${cut(e.text, 300)}`).join("\n")}` : "";
  return `LLMModeling: gold ${st.subject} — ${head}${body}\n\n${CO_AUTHOR}\n`;
}
