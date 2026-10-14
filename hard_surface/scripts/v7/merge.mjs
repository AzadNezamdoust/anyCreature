#!/usr/bin/env node
// WF v8 WP4 — merge.mjs: the MECHANICAL merge of the two critic seats into the round's worksheet (research/v7/
// WF-V8-PLAN.md "Merge" + "Shared data"; WF-REVIEW-opus.md C6; WF-REVIEW-fable.md C5 / C6). The orchestrator writes
// nothing by hand: this script classifies every critique item and prints the STOP line.
//
//   node scripts/v7/merge.mjs --subject <s> --round <N> [--dir out/ref/gold/<s>] [--module <dir>/model.mjs] [--cap 3] [--force]
//                             [--no-variants] [--quiet]
//   node scripts/v7/merge.mjs --validate <critique.json> ...     the schema check alone (exit 1 on an error)
//   node scripts/v7/merge.mjs --keys --module <m.mjs>            the key table: knob: / def: keys, values, comments, axis
//
// Reads <dir>/critique/rN-fable.json + rN-opus.json (scripts/v7/critique.schema.json), <dir>/state.json (written from
// LEDGER.md when absent: round + empty items), the subject's views.json drift rects and the module; writes
// <dir>/critique/rN-merged.json + rN-merged.md. The first stdout line (and of the .md) is the STOP line. Exit 0 = merged,
// 2 = blocked (rule 1), 1 = error. runMerge() is the same pipeline for gold.mjs.
//
// Rules, in order (MERGE_RULES holds the numbers):
//  1 SCHEMA   a missing file, a schema error or done:false -> blocked, nothing written ("> 10 items" only warns); a
//             state.json modelHash that no longer matches the module -> blocked (the model changed during review).
//  2 EVIDENCE every item with `at`: the model's raster of at.image at the reference's own px (orthos: the judge's sigma;
//             concept: the module's frame knobs) against the judged reference (family raster, concept OCCLUDED = don't
//             care) inside at.rect: ref-only / model-only >= 10 % of the rect's px (orchestrator 2026-09-27; was 15 %); colour = the reference's dominant
//             colour family != the model's (the cel render classified like the reference) and, for hex now / want, the
//             claim's two halves: the reference shows want's family, the model now's family; edge >= 1 px differs
//             (silhouette or family). Fail -> REJECTED with the numbers. No `at` = unverified (a MAJOR is merged as MINOR).
//             A WEAK at (2026-09-28): an edge / colour claim that passes but whose differing px are < `share` (10 %) of
//             the rect's px AND < `edgeMinPx` (250) — a big rect around a few px — counts as unverified: a MAJOR
//             merges as MINOR (never REJECTED: the claim holds, the evidence is thin).
//  3 DRIFT    an `at` whose rect lies >= 50 % inside a views.json drift rect of that image whose `decides` != the
//             item's basis -> REJECTED-DRIFT.
//  4 DECIDED  key in state.items.decided without a verified `reopens` (reopens set + `at` verified on the decided
//             item's basis image) -> DECIDED (dropped, listed).
//  5 TRIED    key in state.items.parked -> PARKED; same key + same dir as >= 2 state.items.tried entries -> PARKED (owner
//             packet; the Blind Loop stall rule, K = 2); as 1 -> TRIED (the old numbers). dir: "+" / "-" (want vs the
//             model's value, else the critic's now), "add" / "remove", else "=<want>" (dirOf).
//  6 PAIRING  exact key (part: keys by part family, inspect.mjs parts), then a part:<family>.<pos|size>.<axis> item to
//             the other seat's knob: / def: item whose comment names that family on the same axis, then F:C5's key
//             (part family, axis): pos.<a> ~ size.<a> of one family (one candidate only in both steps).
//             A = both seats, same sign, amounts within 2x (target = the mean; both shown); CONFLICT = opposite
//             signs, > 2x apart, a zero change, or different non-numeric wants; one seat: B = MAJOR with a verified
//             `at`, C = MINOR or an unverified MAJOR (F:C6). A CONFLICT without a knob: / def: key -> X (build both).
//  7 VARIANTS every A / B / CONFLICT item with a knob: / def: key: variants.mjs --rule concept-first in this process
//             (build, frame re-fit, judge) of the value it applies against one shared BASE — A: the target, B: the want,
//             CONFLICT: each seat's want (settled by the WINNER; BASE = neither). Per-view agree deltas attached;
//             the applied row losing > 0.01 agree on the item's basis view -> "verify visually".
//    LINKS    display only (orchestrator 2026-09-27): A / B / CONFLICT / X / C items whose `at` rects share an image and
//             overlap or have centres within 20 px get one link id (L1 ...), printed next to each other, "same area —
//             do together"; no class changes.
//  9 STOP     STOP when no MAJOR stands (A with a MAJOR side, B, an unsettled CONFLICT / X with a MAJOR side), every
//             view's agree >= 0.97 and the chain passes; else OWNER when round >= cap, a PARKED item exists, or an X
//             item is open at the last review (round >= cap - 1); else CONTINUE. drift: items go to the owner packet
//             and never count as MAJOR.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../../src/kernel/index.mjs";
import { gateConfig, validateParts } from "../../src/validate/kernel-chain.mjs";
import { frontRotationDeg } from "../../src/kernel/toThree.mjs";
import { ROOT, loadSubject } from "../subject.mjs";
import { meshParts } from "../project.mjs";
import { OCCLUDED, SUBJECT } from "../registered.mjs";
import { CEL, FAR_RGB, basisOf, classify, loadTurnaround, maskOptions, rasterOrtho, readImage, viewMap } from "../v6/ortho.mjs";
import { judge, shadeRGB } from "../v6/judge.mjs";
import { buildVariant, conceptFirst, conceptIoUFn, conceptTarget, fitFrame, importModule, parseArgs } from "./lib.mjs";

// Candidate critic seats, fable-first (the order legacy subjects' critiques were listed in): the standard pair going
// forward is opus + sonnet (owner 2026-10-02); fable is a rare tie-break seat, kept working for subjects whose history
// already pairs it with opus. Exactly two of these are "the pair" for a given round (runMerge: whichever two
// rN-<seat>.json files exist; DEFAULT_PAIR when none do yet).
export const SEATS = Object.freeze(["fable", "opus", "sonnet"]);
export const DEFAULT_PAIR = Object.freeze(["opus", "sonnet"]);
export const SCHEMA_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), "critique.schema.json");
/** The merge's numbers (research/v7/WF-V8-PLAN.md; WF-REVIEW-opus.md C6): claim share, pair ratio, tried K, the bar, the
 * verify-visually drop, the drift overlap, the default round cap, the critic's item cap (warn only). */
export const MERGE_RULES = Object.freeze({ share: 0.10, edgeMinPx: 250, ratio: 2, triedK: 2, bar: 0.97, verifyDrop: 0.01, driftInside: 0.5, cap: 3, maxItems: 10, linkPx: 20 });
export const CLASS_ORDER = Object.freeze(["A", "B", "CONFLICT", "X", "C", "REJECTED", "REJECTED-DRIFT", "DECIDED", "TRIED", "PARKED"]);
const ID_PREFIX = { A: "A", B: "B", CONFLICT: "K", X: "X", C: "C", REJECTED: "R", "REJECTED-DRIFT": "R", DECIDED: "D", TRIED: "T", PARKED: "P" };
export const PART_PARAMS = Object.freeze(["pos.x", "pos.y", "pos.z", "size.x", "size.y", "size.z", "rot", "colour", "shape", "count", "add", "remove"]);

const isNum = (v) => typeof v === "number" && Number.isFinite(v);
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const pct = (v) => `${(v * 100).toFixed(1)} %`;
const f3 = (v) => (isNum(v) ? String(r4(v)) : v === null || v === undefined ? "—" : String(v));
const sgn = (v) => (v > 0 ? `+${v.toFixed(4)}` : v.toFixed(4));

// ---------------------------------------------------------------------------------------------------------------------
// Rule 1 — the schema (the subset of JSON Schema critique.schema.json uses)
// ---------------------------------------------------------------------------------------------------------------------

export function loadSchema() {
  return JSON.parse(fs.readFileSync(SCHEMA_FILE, "utf8"));
}

function typeOf(v) {
  if (v === null) return "null";
  if (Array.isArray(v)) return "array";
  if (Number.isInteger(v)) return "integer";
  return typeof v;
}

/**
 * Validate `value` against a JSON Schema using type (one or a list; integer counts as number), enum, pattern,
 * minLength, maxLength, minimum, maximum, required, properties, additionalProperties: false, items, minItems, maxItems.
 * @returns {{path:string, keyword:string, message:string}[]}
 */
export function validateSchema(value, schema, p = "", out = []) {
  const err = (keyword, message) => out.push({ path: p || "/", keyword, message: `${p || "/"}: ${message}` });
  if (schema.type) {
    const types = [].concat(schema.type);
    const t = typeOf(value);
    if (!types.some((x) => x === t || (x === "number" && t === "integer"))) { err("type", `${t}, want ${types.join("|")}`); return out; }
  }
  if (schema.enum && !schema.enum.includes(value)) err("enum", `${JSON.stringify(value)} is not one of ${schema.enum.join(" | ")}`);
  if (typeof value === "string") {
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) err("pattern", `"${value}" does not match the key grammar`);
    if (schema.minLength !== undefined && value.length < schema.minLength) err("minLength", `shorter than ${schema.minLength}`);
    if (schema.maxLength !== undefined && value.length > schema.maxLength) err("maxLength", `${value.length} chars > ${schema.maxLength}`);
  }
  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) err("minimum", `${value} < ${schema.minimum}`);
    if (schema.maximum !== undefined && value > schema.maximum) err("maximum", `${value} > ${schema.maximum}`);
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) err("minItems", `${value.length} items < ${schema.minItems}`);
    if (schema.maxItems !== undefined && value.length > schema.maxItems) err("maxItems", `${value.length} items > ${schema.maxItems}`);
    if (schema.items) value.forEach((x, i) => validateSchema(x, schema.items, `${p}/${i}`, out));
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    for (const r of schema.required ?? []) if (!(r in value)) out.push({ path: `${p}/${r}`, keyword: "required", message: `${p}/${r}: required` });
    for (const [k, x] of Object.entries(value)) {
      if (schema.properties?.[k]) validateSchema(x, schema.properties[k], `${p}/${k}`, out);
      else if (schema.additionalProperties === false) out.push({ path: `${p}/${k}`, keyword: "additionalProperties", message: `${p}/${k}: not in the schema` });
    }
  }
  return out;
}

/**
 * Rule 1 for one seat's parsed file: schema errors, the file's subject / round / seat, done:true. "> maxItems items" on
 * /items is a warning (the item cap is the critic's budget rule; every item is merged).
 * @returns {{errors:string[], warnings:string[]}}
 */
export function checkCritique(obj, { subject, round, seat }, schema = loadSchema()) {
  const errors = [], warnings = [];
  for (const e of validateSchema(obj, schema)) (e.keyword === "maxItems" && e.path === "/items" ? warnings : errors).push(e.message);
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    if (subject !== undefined && obj.subject !== undefined && obj.subject !== subject) errors.push(`subject "${obj.subject}" is not ${subject}`);
    if (round !== undefined && obj.round !== undefined && obj.round !== round) errors.push(`round ${obj.round} is not ${round}`);
    if (seat !== undefined && obj.seat !== undefined && obj.seat !== seat) errors.push(`seat "${obj.seat}" is not ${seat}`);
    if (obj.done === false) errors.push(`done:false (${Array.isArray(obj.items) ? obj.items.length : 0} items written so far: resume the ${seat ?? obj.seat} critic)`);
  }
  return { errors, warnings };
}

// ---------------------------------------------------------------------------------------------------------------------
// Keys, directions, the module's key table
// ---------------------------------------------------------------------------------------------------------------------

/** A part id's family (scripts/v7/inspect.mjs parts: the id without its _l / _r / _fl / _rr / number suffix). */
export const familyOf = (id) => String(id).replace(/_[lr]\d*$|_[a-z]?[lr]\d*$|\d+$/, "");

/**
 * The key grammar -> {kind: knob|def|part|drift, key (normalised: part: keys by family), name?, path?, family?, param?,
 * axis? (x|y|z for pos.* / size.*)}; null for a key outside the grammar.
 */
export function parseKey(key) {
  const m = /^(knob|def|part|drift):(.+)$/.exec(String(key ?? ""));
  if (!m) return null;
  const [, kind, rest] = m;
  if (kind === "knob") return { kind, key: `knob:${rest}`, name: rest, path: [rest] };
  if (kind === "def") return { kind, key: `def:${rest}`, name: rest, path: rest.split(".") };
  if (kind === "drift") return { kind, key: `drift:${rest}`, view: rest };
  const i = rest.indexOf(".");
  if (i <= 0) return null;
  const family = familyOf(rest.slice(0, i));
  const param = rest.slice(i + 1);
  if (!PART_PARAMS.includes(param)) return null;
  const ax = /^(?:pos|size)\.([xyz])$/.exec(param);
  return { kind, key: `part:${family}.${param}`, family, param, axis: ax ? ax[1] : null };
}

const norm = (v) => String(v).trim().toLowerCase();
const hexRGB = (h) => (/^#[0-9a-f]{6}$/i.test(String(h).trim()) ? [1, 3, 5].map((i) => parseInt(String(h).trim().slice(i, i + 2), 16)) : null);

/** Two non-numeric wants agree: colours within 40 RGB (ortho.mjs MERGE_RGB), anything else by trimmed lower-case text. */
export function sameWant(a, b) {
  if (isNum(a) && isNum(b)) return Math.abs(a - b) < 1e-9;
  const ca = hexRGB(a), cb = hexRGB(b);
  if (ca && cb) return Math.hypot(ca[0] - cb[0], ca[1] - cb[1], ca[2] - cb[2]) < 40;
  return norm(a) === norm(b);
}

/** An item's direction for the tried / parked rule (state.items.tried[].dir uses the same convention). */
export function dirOf(item, base = item.now) {
  const pk = parseKey(item.key);
  if (pk?.param === "add" || pk?.param === "remove") return pk.param;
  if (isNum(item.want) && isNum(base)) return item.want > base + 1e-12 ? "+" : item.want < base - 1e-12 ? "-" : "0";
  return `=${norm(item.want)}`;
}

/** The axis a knob acts on: its name's axis suffix (X / Y / Z; W = x, L = z) or segment, else the first axis word of its
 * comment; null when neither says. */
export function knobAxis(name, comment = "") {
  const seg = String(name).split(".").pop();
  if (/^(x|x0|x1|hw\d?|w|inset|out|width)$/i.test(seg) || /[A-Za-z0-9](X|W)$/.test(seg) || seg === "W") return "x";
  if (/^(y|y0|y1|top|bot|bottom|h|height|drop|sill)$/i.test(seg) || /[A-Za-z0-9](Y|H)$/.test(seg) || seg === "H") return "y";
  if (/^(z|z0|z1|zc|len|length|depth|run|wrap)$/i.test(seg) || /[A-Za-z0-9](Z|L)$/.test(seg) || seg === "L") return "z";
  const c = String(comment).toLowerCase();
  const words = [["x", /half-width|\bwidth\b|\bwide\b|outboard|inboard|\bx\b/], ["y", /\bheight\b|\btall\b|\bup\b|\btop\b|\bbottom\b|\by\b/], ["z", /\blength\b|\blong\b|\bforward\b|\bback\b|\bz\b/]];
  let best = null, at = Infinity;
  for (const [ax, re] of words) { const m = re.exec(c); if (m && m.index < at) { best = ax; at = m.index; } }
  return best;
}

/** The lines of `export const <name> = { ... }` in a module's source (depth-counted braces, comments ignored). */
function exportBlock(lines, name) {
  const i = lines.findIndex((l) => new RegExp(`^export const ${name}\\s*=\\s*\\{`).test(l));
  if (i < 0) return [];
  const out = [];
  let depth = 0;
  for (let j = i; j < lines.length; j += 1) {
    for (const ch of lines[j].replace(/\/\/.*$/, "")) { if (ch === "{") depth += 1; if (ch === "}") depth -= 1; }
    out.push(lines[j]);
    if (depth <= 0) break;
  }
  return out;
}

/** The trailing // comment on the line of a block that defines `name:` (first match). */
function commentIn(lines, name) {
  const re = new RegExp(`(^|[\\s{,])${name.replace(/\$/g, "\\$")}\\s*:`);
  const l = lines.find((x) => re.test(x.replace(/\/\/.*$/, "")));
  const m = l ? /\/\/\s?(.*)$/.exec(l) : null;
  return m ? m[1].trim() : "";
}

/**
 * The module's key table: every KNOBS entry (knob:<name>) and every DEFAULTS leaf (def:<path>, arrays by index) with its
 * current value, source comment (a nested path takes its top-level key's line), unit / group (knobs) and axis.
 * @returns {Map<string, {key:string, kind:string, name:string, path:string[], value:any, comment:string, unit?:string, group?:string, axis:string|null}>}
 */
export function keyTable(mod, source = "") {
  const lines = String(source).split(/\r?\n/);
  const kb = exportBlock(lines, "KNOBS"), db = exportBlock(lines, "DEFAULTS");
  const out = new Map();
  for (const [name, k] of Object.entries(mod.KNOBS ?? {})) {
    const comment = commentIn(kb, name);
    out.set(`knob:${name}`, { key: `knob:${name}`, kind: "knob", name, path: [name], value: k?.v, comment, unit: k?.unit, group: k?.group, axis: knobAxis(name, comment) });
  }
  const walk = (o, p, comment) => {
    for (const [k, v] of Object.entries(o)) {
      const pth = [...p, k];
      const c = p.length ? comment : commentIn(db, k);
      if (v && typeof v === "object") walk(v, pth, c);
      else out.set(`def:${pth.join(".")}`, { key: `def:${pth.join(".")}`, kind: "def", name: pth.join("."), path: pth, value: v, comment: c, axis: knobAxis(pth.join("."), c) });
    }
  };
  if (mod.DEFAULTS && typeof mod.DEFAULTS === "object") walk(mod.DEFAULTS, [], "");
  return out;
}

/** buildVariant overrides that set one key to `value`: a knob by name; a DEFAULTS path as its whole top-level entry
 * (a deep copy with the leaf set — buildVariant merges objects one level). */
export function overridesFor(info, value, mod) {
  if (info.kind === "knob") return { [info.name]: value };
  const [first, ...rest] = info.path;
  if (!rest.length) return { [first]: value };
  const copy = structuredClone(mod.DEFAULTS[first]);
  let o = copy;
  for (const k of rest.slice(0, -1)) o = o[k];
  o[rest[rest.length - 1]] = value;
  return { [first]: copy };
}

/** Does a knob's comment (or its own name) name the part family? ("mirror_head" matches "mirror head(s)") */
export function namesFamily(info, family) {
  const text = `${info.comment} ${info.name}`.toLowerCase().replace(/[_\-.]/g, " ");
  const phrase = String(family).toLowerCase().replace(/_/g, " ").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|[^a-z0-9])${phrase}(e?s)?([^a-z0-9]|$)`).test(text);
}

// ---------------------------------------------------------------------------------------------------------------------
// Rule 2 — evidence: the claim tested inside the rect
// ---------------------------------------------------------------------------------------------------------------------

/**
 * Test a claim inside `rect` ([x0, y0, x1, y1], half-open image px, clipped to the raster) of one image.
 * R = {w, h, refFg, modelFg (0/1), refFam, modelFam (family ids), care (0 = don't care, e.g. concept OCCLUDED) | null,
 * names (family names)}. colour: the reference's dominant family (over its fg px in the rect) differs from the model's,
 * and — the claim's two halves — when `expect.ref` / `expect.model` are given (the families of a hex `want` / `now`)
 * the reference shows want's family and the model shows now's family there: a colour item whose rect shows another
 * part of the model (a geometry offset) is not evidence for a colour change. edge / colour: `weak` when the claim passes
 * but the differing px are < `share` of the rect's px and < `minPx` (a big rect around a few px: unverified, not rejected).
 * @returns {{ok:boolean, weak:boolean, claim:string, rect:number[], px:number, refOnly:number, modelOnly:number, differ:number,
 *   ref:{family:string|null, share:number}, model:{family:string|null, share:number}, text:string}}
 */
export function claimTest(R, rect, claim, share = MERGE_RULES.share, expect = {}, minPx = MERGE_RULES.edgeMinPx) {
  const x0 = Math.max(0, Math.floor(rect[0])), y0 = Math.max(0, Math.floor(rect[1]));
  const x1 = Math.min(R.w, Math.ceil(rect[2])), y1 = Math.min(R.h, Math.ceil(rect[3]));
  const box = [x0, y0, x1, y1];
  const base = { claim, rect: box, px: 0, refOnly: 0, modelOnly: 0, differ: 0, weak: false, ref: { family: null, share: 0 }, model: { family: null, share: 0 } };
  if (!(x1 > x0 && y1 > y0)) return { ...base, ok: false, text: `rect ${rect.join(",")} is outside the ${R.w}x${R.h} image` };
  let px = 0, refOnly = 0, modelOnly = 0, differ = 0, refN = 0, modelN = 0;
  const rc = new Map(), mc = new Map();
  for (let y = y0; y < y1; y += 1) for (let x = x0; x < x1; x += 1) {
    const i = y * R.w + x;
    if (R.care && !R.care[i]) continue;
    px += 1;
    const rf = R.refFg[i] ? 1 : 0, mf = R.modelFg[i] ? 1 : 0;
    if (rf && !mf) refOnly += 1;
    if (!rf && mf) modelOnly += 1;
    if (rf !== mf || (rf && R.refFam[i] !== R.modelFam[i])) differ += 1;
    if (rf) { refN += 1; rc.set(R.refFam[i], (rc.get(R.refFam[i]) ?? 0) + 1); }
    if (mf) { modelN += 1; mc.set(R.modelFam[i], (mc.get(R.modelFam[i]) ?? 0) + 1); }
  }
  const mode = (m) => { let b = null, n = 0; for (const [k, c] of m) if (c > n || (c === n && k < b)) { b = k; n = c; } return [b, n]; };
  const [rm, rn] = mode(rc), [mm, mn] = mode(mc);
  const name = (f) => (f === null ? null : String(R.names?.[f] ?? f));
  const ref = { family: name(rm), share: refN ? r4(rn / refN) : 0 }, model = { family: name(mm), share: modelN ? r4(mn / modelN) : 0 };
  const out = { ...base, px, refOnly, modelOnly, differ, ref, model };
  const where = `${px} px at ${box.join(",")}`;
  if (!px) return { ...out, ok: false, text: `no scored px in ${box.join(",")} (don't care)` };
  const fams = `reference ${ref.family ?? "none"} ${pct(ref.share)} · model ${model.family ?? "none"} ${pct(model.share)}`;
  if (claim === "ref-only") return { ...out, ok: refOnly / px >= share, text: `ref-only ${pct(refOnly / px)} of ${where} (needs ${pct(share)})` };
  if (claim === "model-only") return { ...out, ok: modelOnly / px >= share, text: `model-only ${pct(modelOnly / px)} of ${where} (needs ${pct(share)})` };
  if (claim === "colour") {
    const miss = [];
    if (rm === mm) miss.push("the same family");
    if (expect.ref !== null && expect.ref !== undefined && rm !== expect.ref) miss.push(`the reference does not show want's family (${name(expect.ref)})`);
    if (expect.model !== null && expect.model !== undefined && mm !== expect.model) miss.push(`the model does not show now's family (${name(expect.model)})`);
    const weak = !miss.length && isWeak(differ, px, share, minPx);
    return { ...out, ok: !miss.length, weak, text: `colour: ${fams} (${where})${miss.length ? ` — ${miss.join("; ")}` : ""}${weak ? ` — ${weakText(differ, px, share, minPx)}` : ""}` };
  }
  if (claim === "edge") {
    const weak = differ >= 1 && isWeak(differ, px, share, minPx);
    return { ...out, ok: differ >= 1, weak, text: `edge: ${differ} px differ of ${where}${weak ? ` — ${weakText(differ, px, share, minPx)}` : ""}` };
  }
  return { ...out, ok: false, text: `unknown claim "${claim}"` };
}

/** An edge / colour claim's evidence is WEAK when its differing px are below both bars: < `share` of the rect, < `minPx`. */
export const isWeak = (differ, px, share = MERGE_RULES.share, minPx = MERGE_RULES.edgeMinPx) => differ / px < share - 1e-12 && differ < minPx;
const weakText = (differ, px, share, minPx) => `weak: ${pct(differ / px)} of the rect < ${pct(share)} and ${differ} px < ${minPx} px (a MAJOR merges as MINOR)`;

/** The colour family (ortho.mjs classify, no background cut) of a "#rrggbb" value, else null. */
export function hexFamily(table, value) {
  const c = hexRGB(value);
  return c ? classify(table, c[0], c[1], c[2], FAR_RGB, false) : null;
}

/** Rule 3: the drift rect of at.image an `at` lies inside (>= `inside` of the at rect's area; the largest overlap), or null. */
export function driftHit(drift, at, inside = MERGE_RULES.driftInside) {
  const list = drift?.[at?.image];
  if (!list?.length) return null;
  const [ax0, ay0, ax1, ay1] = at.rect;
  const area = Math.max(0, ax1 - ax0) * Math.max(0, ay1 - ay0);
  if (!area) return null;
  let best = null;
  for (const d of list) {
    const [dx0, dy0, dx1, dy1] = d.rect;
    const ov = Math.max(0, Math.min(ax1, dx1) - Math.max(ax0, dx0)) * Math.max(0, Math.min(ay1, dy1) - Math.max(ay0, dy0));
    const f = ov / area;
    if (f >= inside - 1e-12 && (!best || f > best.f)) best = { ...d, f: r4(f) };
  }
  return best;
}

// ---------------------------------------------------------------------------------------------------------------------
// Rules 2-6 — classification (pure: evidence results are passed in)
// ---------------------------------------------------------------------------------------------------------------------

const cell = (seat, e) => ({
  n: e.n, sev: e.item.sev, key: e.item.key, now: e.item.now ?? null, want: e.item.want, unit: e.item.unit ?? null, views: e.item.views ?? [],
  basis: e.item.basis ?? null, at: e.item.at ?? null, reopens: e.item.reopens ?? null, note: e.item.note ?? "", evidence: e.item.evidence ?? [],
  verified: e.verified, ev: e.ev ?? null,
});

/**
 * Rules 2-6 over both seats' items. evidence[seat][i] = the claimTest result of item i ({ok, text, ...}, `image` = the
 * canonical image name) or null (no `at`); a result with ok false rejects the item. keys = keyTable(); drift =
 * {<image>: [{id, rect, decides, why}]}; state = state.json (items.decided / tried / parked).
 * @returns {{items:object[], stateAdd:{tried:object[], parked:object[]}}}  items in CLASS_ORDER with ids
 */
export function classifyItems({ critiques, evidence = {}, keys = new Map(), drift = null, state = null, round = null, rules = MERGE_RULES }) {
  const entries = [];
  for (const seat of SEATS) {
    (critiques[seat]?.items ?? []).forEach((item, i) => {
      const pk = parseKey(item.key);
      const ev = evidence[seat]?.[i] ?? null;
      entries.push({ seat, n: i + 1, item, pk, nkey: pk?.key ?? item.key, ev, verified: !!(item.at && ev?.ok && !ev?.weak) });
    });
  }
  const valueOf = (e) => keys.get(e.nkey)?.value;
  const baseOf = (e) => (isNum(valueOf(e)) ? valueOf(e) : e.item.now);
  const out = [];
  const single = (cls, e, reason, extra = {}) => out.push({ class: cls, key: e.nkey, entries: [e], reason, ...extra });
  const items = state?.items ?? {};
  const decided = items.decided ?? [], tried = items.tried ?? [], parked = items.parked ?? [];
  const keyOf = (k) => parseKey(k)?.key ?? k;
  const stateAdd = { tried: [], parked: [] };
  // the two seats actually present in `critiques` (SEATS order, fable-first — a legacy fable + opus pair keeps its
  // historical pairing order; a new opus + sonnet round pairs opus first)
  const activeSeats = SEATS.filter((s) => critiques[s] !== undefined);
  let live = [];
  for (const e of entries) {
    // rule 2: evidence
    if (e.item.at && !e.ev?.ok) { single("REJECTED", e, `evidence failed: ${e.ev?.text ?? "not checked"}`); continue; }
    // rule 3: drift
    if (e.item.at) {
      const d = driftHit(drift, { ...e.item.at, image: e.ev?.image ?? e.item.at.image }, rules.driftInside);
      if (d && d.decides !== e.item.basis) { single("REJECTED-DRIFT", e, `at inside drift ${d.id} (${pct(d.f)}; decides ${d.decides}, the item's basis is ${e.item.basis})`, { drift: d }); continue; }
    }
    // rule 4: decided
    const dec = decided.find((d) => keyOf(d.key) === e.nkey);
    if (dec) {
      const reopened = e.item.reopens && e.verified && (e.ev?.image ?? e.item.at?.image) === dec.basis;
      if (!reopened) {
        single("DECIDED", e, `decided r${dec.round ?? "?"} on ${dec.basis ?? "?"}: ${f3(dec.value)}${e.item.reopens ? ` (reopens not verified: needs a verified at on ${dec.basis})` : ""}`, { decided: dec });
        continue;
      }
      e.reopened = dec;
    }
    // rule 5: tried / parked
    const dir = dirOf(e.item, baseOf(e));
    e.dir = dir;
    const pk = parked.find((p) => keyOf(p.key) === e.nkey);
    if (pk) { single("PARKED", e, `parked r${pk.round ?? "?"}: ${pk.reason ?? ""}`.trim(), { parked: pk }); continue; }
    const hits = tried.filter((t) => keyOf(t.key) === e.nkey && t.dir === dir);
    if (hits.length >= rules.triedK) {
      single("PARKED", e, `tried ${hits.length}x in the same direction (${dir}): ${hits.map((t) => `r${t.round} ${t.result ?? ""}`.trim()).join("; ")}`, { tried: hits });
      if (!stateAdd.parked.some((p) => p.key === e.nkey)) stateAdd.parked.push({ key: e.nkey, reason: `tried ${hits.length}x (${dir}); raised again by ${e.seat} ${e.n} in review r${round}`, round });
      continue;
    }
    if (hits.length === 1) {
      single("TRIED", e, `tried r${hits[0].round} (${dir}): ${hits[0].result ?? ""}`.trim(), { tried: hits });
      if (!stateAdd.tried.some((t) => t.key === e.nkey && t.dir === dir)) stateAdd.tried.push({ key: e.nkey, dir, round, result: `raised again by ${e.seat} ${e.n} in review r${round} (TRIED)` });
      continue;
    }
    live.push(e);
  }
  // rule 6: pairing (over the two active seats; a third candidate seat with no items here never enters)
  const pairs = [];
  const byseat = (s) => live.filter((e) => e.seat === s);
  const [seatA, seatB] = activeSeats;
  if (seatA && seatB) {
    for (const f of byseat(seatA)) {
      const o = byseat(seatB).find((x) => !x.paired && x.nkey === f.nkey);
      if (o) { f.paired = o.paired = true; pairs.push({ a: f, b: o, via: "key" }); }
    }
    for (const [sa, sb] of [[seatA, seatB], [seatB, seatA]]) {
      for (const p of byseat(sa)) {
        if (p.paired || p.pk?.kind !== "part" || !p.pk.axis) continue;
        const cands = byseat(sb).filter((k) => {
          if (k.paired || !(k.pk?.kind === "knob" || k.pk?.kind === "def")) return false;
          const info = keys.get(k.nkey);
          return info && info.group !== "frame" && namesFamily(info, p.pk.family) && (info.axis === null || info.axis === p.pk.axis);
        });
        if (cands.length === 1) {
          const k = cands[0];
          p.paired = k.paired = true;
          pairs.push({ a: sa === seatA ? p : k, b: sa === seatA ? k : p, via: `family ${p.pk.family} ~ ${k.nkey}` });
        }
      }
    }
    // F:C5's pairing key (part family, axis): part:<f>.pos.<a> ~ part:<f>.size.<a> (one candidate only)
    for (const f of byseat(seatA)) {
      if (f.paired || f.pk?.kind !== "part" || !f.pk.axis) continue;
      const cands = byseat(seatB).filter((o) => !o.paired && o.pk?.kind === "part" && o.pk.family === f.pk.family && o.pk.axis === f.pk.axis);
      if (cands.length === 1) { f.paired = cands[0].paired = true; pairs.push({ a: f, b: cands[0], via: `family + axis ${f.pk.family} ${f.pk.axis}` }); }
    }
  }
  for (const { a, b, via } of pairs) {
    const knobSide = [a, b].find((e) => e.pk?.kind === "knob" || e.pk?.kind === "def") ?? null;
    const key = knobSide?.nkey ?? a.nkey;
    const ba = baseOf(a), bb = baseOf(b);
    let cls, reason, target = null;
    if (isNum(a.item.want) && isNum(b.item.want) && isNum(ba) && isNum(bb)) {
      const da = a.item.want - ba, db = b.item.want - bb;
      const lo = Math.min(Math.abs(da), Math.abs(db)), hi = Math.max(Math.abs(da), Math.abs(db));
      if (Math.sign(da) === 0 || Math.sign(db) === 0) { cls = "CONFLICT"; reason = `a zero change (${a.seat} ${sgn(da)}, ${b.seat} ${sgn(db)})`; }
      else if (Math.sign(da) !== Math.sign(db)) { cls = "CONFLICT"; reason = `opposite signs (${a.seat} ${sgn(da)}, ${b.seat} ${sgn(db)})`; }
      else if (hi > rules.ratio * lo + 1e-12) { cls = "CONFLICT"; reason = `amounts ${Math.abs(da).toFixed(4)} vs ${Math.abs(db).toFixed(4)} (> ${rules.ratio}x apart)`; }
      else {
        cls = "A";
        reason = `same sign, amounts ${Math.abs(da).toFixed(4)} / ${Math.abs(db).toFixed(4)} (within ${rules.ratio}x)`;
        // the mean want; across a part <-> knob pair the mean change applied to the knob's value; a pos ~ size pair shows
        // both wants (no common value)
        target = a.nkey === b.nkey ? r4((a.item.want + b.item.want) / 2) : knobSide ? r4(baseOf(knobSide) + (da + db) / 2) : null;
      }
    } else if (!isNum(a.item.want) && !isNum(b.item.want) && sameWant(a.item.want, b.item.want)) {
      cls = "A"; reason = "the same want"; target = a.item.want;
    } else {
      cls = "CONFLICT"; reason = `different wants (${a.seat} ${JSON.stringify(a.item.want)}, ${b.seat} ${JSON.stringify(b.item.want)})`;
    }
    if (cls === "CONFLICT" && !knobSide) { cls = "X"; reason += " — no knob / def key: build both"; }
    out.push({ class: cls, key, entries: [a, b], reason: `${via === "key" ? "" : `paired by ${via}; `}${reason}`, target, pair: via });
  }
  for (const e of live.filter((x) => !x.paired)) {
    if (e.item.sev === "MAJOR" && e.verified) single("B", e, `one seat, MAJOR with a verified at (${e.ev.text})`, { target: e.item.want });
    else single("C", e, e.item.sev === "MAJOR" ? (e.item.at && e.ev?.weak ? `one seat, MAJOR with a weak at (${e.ev.text}) -> merged as MINOR` : "one seat, MAJOR without a verified at -> merged as MINOR (F:C6)") : "one seat, MINOR", { target: e.item.want });
  }
  // one row per key for DECIDED / TRIED / PARKED raised by both seats
  const merged = [];
  for (const it of out) {
    const twin = ["DECIDED", "TRIED", "PARKED"].includes(it.class) && merged.find((m) => m.class === it.class && m.key === it.key && m.entries.every((x) => x.seat !== it.entries[0].seat));
    if (twin) twin.entries.push(...it.entries); else merged.push(it);
  }
  // finish: severity, seats, views, basis, owner flags, order + ids
  const counters = {};
  const final = merged.map((it) => {
    const seats = {};
    for (const e of it.entries) seats[e.seat] = cell(e.seat, e);
    const effMajor = it.entries.some((e) => e.item.sev === "MAJOR" && e.verified);
    const demoted = it.entries.filter((e) => e.item.sev === "MAJOR" && !e.verified && !["REJECTED", "REJECTED-DRIFT"].includes(it.class)).map((e) => e.seat);
    const views = [...new Set(it.entries.flatMap((e) => e.item.views ?? []))];
    const basis = [...new Set(it.entries.map((e) => e.item.basis).filter(Boolean))];
    const pk = parseKey(it.key);
    return {
      class: it.class, key: it.key, views, basis, sev: effMajor ? "MAJOR" : "MINOR", demoted, seats, reason: it.reason,
      target: it.target ?? null, pair: it.pair ?? null, owner: pk?.kind === "drift" || it.class === "PARKED",
      drift: it.drift ?? null, decided: it.decided ?? null, tried: it.tried ?? null, reopened: it.entries.find((e) => e.reopened)?.reopened ?? null,
      order: [CLASS_ORDER.indexOf(it.class), Math.min(...it.entries.map((e) => (activeSeats.indexOf(e.seat) < 0 ? activeSeats.length : activeSeats.indexOf(e.seat)) * 1000 + e.n))],
    };
  }).sort((p, q) => p.order[0] - q.order[0] || p.order[1] - q.order[1]);
  for (const it of final) {
    const px = ID_PREFIX[it.class];
    counters[px] = (counters[px] ?? 0) + 1;
    it.id = `${px}${counters[px]}`;
    delete it.order;
  }
  return { items: final, stateAdd };
}

// ---------------------------------------------------------------------------------------------------------------------
// Area links — a DISPLAY rule (orchestrator 2026-09-27): no class ever changes
// ---------------------------------------------------------------------------------------------------------------------

export const LINKABLE = Object.freeze(["A", "B", "CONFLICT", "X", "C"]);

/**
 * The actionable items (LINKABLE) whose `at` rects lie in the same image and overlap (a positive-area intersection) or
 * have centres within `near` px share one link id (L1, L2, ... in worksheet order): the worksheet prints them next to
 * each other, "same area — do together". Sets item.link (id or null); classes are untouched.
 * @returns {{id:string, images:string[], items:string[]}[]}
 */
export function areaLinks(items, near = MERGE_RULES.linkPx) {
  const ats = items.map((it) => (LINKABLE.includes(it.class)
    ? SEATS.map((s) => it.seats[s]).filter((c) => c?.at).map((c) => ({ image: c.ev?.image ?? c.at.image, rect: c.at.rect }))
    : []));
  const touch = (a, b) => {
    if (a.image !== b.image) return false;
    const [ax0, ay0, ax1, ay1] = a.rect, [bx0, by0, bx1, by1] = b.rect;
    const ov = Math.max(0, Math.min(ax1, bx1) - Math.max(ax0, bx0)) * Math.max(0, Math.min(ay1, by1) - Math.max(ay0, by0));
    return ov > 0 || Math.hypot((ax0 + ax1 - bx0 - bx1) / 2, (ay0 + ay1 - by0 - by1) / 2) <= near + 1e-9;
  };
  const parent = items.map((_, i) => i);
  const find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
  for (let i = 0; i < items.length; i += 1) for (let j = i + 1; j < items.length; j += 1) {
    if (ats[i].some((a) => ats[j].some((b) => touch(a, b)))) parent[find(j)] = find(i);
  }
  const groups = new Map();   // insertion order = each group's first member in worksheet order
  items.forEach((it, i) => {
    it.link = null;
    if (!ats[i].length) return;
    const r = find(i);
    if (!groups.has(r)) groups.set(r, []);
    groups.get(r).push(i);
  });
  const links = [];
  for (const members of groups.values()) {
    if (members.length < 2) continue;
    const id = `L${links.length + 1}`;
    for (const i of members) items[i].link = id;
    links.push({ id, images: [...new Set(members.flatMap((i) => ats[i].map((a) => a.image)))], items: members.map((i) => items[i].id) });
  }
  return links;
}

/** The worksheet's row order: CLASS_ORDER, each link group pulled up to its first member (next to each other). */
export function worksheetOrder(items) {
  const out = [], done = new Set();
  for (const it of items) {
    if (done.has(it)) continue;
    for (const x of it.link ? items.filter((y) => y.link === it.link) : [it]) { out.push(x); done.add(x); }
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------------------
// Rule 9 — the STOP line
// ---------------------------------------------------------------------------------------------------------------------

/**
 * @param {{items:object[], views:{[v:string]:{agree:number}}, chainPass:boolean, round:number, cap?:number, bar?:number}} o
 * @returns {{verdict:"STOP"|"OWNER"|"CONTINUE", reason:string, line:string, standing:string[]}}
 */
export function stopLine({ items, views, chainPass, round, cap = MERGE_RULES.cap, bar = MERGE_RULES.bar }) {
  const isDrift = (it) => parseKey(it.key)?.kind === "drift";
  const standing = items.filter((it) => !isDrift(it) && it.sev === "MAJOR" && (it.class === "A" || it.class === "B" || (it.class === "CONFLICT" && !it.variant?.settled) || it.class === "X"));
  const vs = Object.entries(views ?? {});
  const low = vs.filter(([, m]) => !(m.agree >= bar - 1e-12));
  const min = vs.reduce((b, [v, m]) => (!b || m.agree < b[1] ? [v, m.agree] : b), null);
  const parked = items.filter((it) => it.class === "PARKED");
  const structural = items.filter((it) => it.class === "X");
  const f = (x) => x.toFixed(3).replace(/^0/, "");
  const bits = [
    standing.length ? `${standing.length} MAJOR standing (${standing.map((it) => it.id).join(", ")})` : "no MAJOR standing",
    min ? (low.length ? `min agree ${f(min[1])} (${min[0]}) < ${f(bar)}` : `every view agree >= ${f(bar)} (min ${f(min[1])} ${min[0]})`) : "no view numbers",
    chainPass ? "chain pass" : "chain FAIL",
  ];
  let verdict = "CONTINUE";
  const owner = [];
  if (!standing.length && min && !low.length && chainPass) verdict = "STOP";
  else {
    if (round >= cap) owner.push(`round ${round} = the cap (${cap})`);
    if (parked.length) owner.push(`${parked.length} PARKED (${parked.map((it) => it.id).join(", ")})`);
    if (structural.length && round >= cap - 1) owner.push(`${structural.length} structural (${structural.map((it) => it.id).join(", ")}) open at the last review`);
    if (owner.length) verdict = "OWNER";
  }
  const reason = [...owner, ...bits].join("; ");
  return { verdict, reason, line: `STOP: ${verdict} — ${reason}`, standing: standing.map((it) => it.id) };
}

// ---------------------------------------------------------------------------------------------------------------------
// State, hashes
// ---------------------------------------------------------------------------------------------------------------------

/** A minimal state.json (research/v7/WF-V8-PLAN.md "Shared data") from LEDGER.md: the round (the last "rN modeller"
 * line, else `round`) and empty items. */
export function minimalState(subject, ledgerText = "", round = null) {
  const rounds = [...String(ledgerText).matchAll(/^r(\d+)\s+modeller/gm)].map((m) => Number(m[1]));
  const r = rounds.length ? Math.max(...rounds) : round ?? 1;
  return {
    subject, round: r, phase: "review", roundType: r <= 1 ? "build" : r === 2 ? "list" : "polish",
    baseline: null, modelHash: null, eyesHash: null,
    items: { decided: [], tried: [], parked: [], open: [] }, runs: [], ledger: [],
  };
}

/** sha256 of a file's bytes (hex). state.json modelHash may hold it, or its sha1, optionally "sha256:" / "sha1:"-prefixed. */
export function hashFile(file, algo = "sha256") {
  return createHash(algo).update(fs.readFileSync(file)).digest("hex");
}
function hashMatches(recorded, file) {
  const h = String(recorded).replace(/^(sha256|sha1):/, "").toLowerCase();
  return h === hashFile(file, "sha256") || h === hashFile(file, "sha1");
}

// ---------------------------------------------------------------------------------------------------------------------
// The worksheet (markdown)
// ---------------------------------------------------------------------------------------------------------------------

const esc = (s) => String(s).replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
function seatCell(c) {
  if (!c) return "—";
  const tag = c.sev !== "MAJOR" ? "" : c.verified ? " MAJ" : c.at && c.ev?.weak ? " MAJ (at weak)" : c.at ? " MAJ (at ✗)" : " MAJ (no at)";
  return `${f3(c.now)}→${f3(c.want)}${tag}`;
}
function evidenceCell(it) {
  const bits = it.link ? [`${it.link} same area — do together`] : [];
  for (const seat of SEATS) {
    const c = it.seats[seat];
    if (!c) continue;
    if (!c.at) bits.push(`${seat[0]}: no at`);
    else if (c.ev?.ok && c.ev?.weak) bits.push(`${seat[0]}: ✓ weak (${c.ev.differ} px)`);
    else if (c.ev?.ok) bits.push(`${seat[0]}: ✓`);
    else bits.push(`${seat[0]}: ✗ ${c.ev?.text ?? ""}`);
  }
  if (it.class === "REJECTED-DRIFT") bits.push(`in drift ${it.drift.id}`);
  if (it.class === "DECIDED" || it.class === "TRIED" || it.class === "PARKED") bits.push(it.reason);
  return bits.join(" · ");
}
function variantCell(it) {
  const v = it.variant;
  if (!v) return "—";
  if (v.error) return `error: ${v.error}`;
  const row = v.applied ? v.rows.find((r) => r.tag === v.applied) : null;
  const d = row?.delta ? Object.entries(row.delta).filter(([, x]) => Math.abs(x) >= 0.00005).map(([k, x]) => `${k} ${sgn(x)}`).join(", ") || "±0" : "";
  const settled = it.class === "CONFLICT" ? ` · settled ${v.settled ?? "—"}` : "";
  return `${row ? `${row.tag} ${f3(row.value)}: ${d}` : "BASE kept"} · WINNER ${v.winner ?? "—"}${settled}${v.verify ? " · VERIFY VISUALLY" : ""}`;
}

export function renderMarkdown(m) {
  const activeSeats = SEATS.filter((s) => m.seats[s]);
  const L = [m.stop.line, ""];
  L.push(`# ${m.subject} — round ${m.round} critiques merged (scripts/v7/merge.mjs; rules: WF-REVIEW-opus.md C6)`);
  L.push(`${activeSeats.map((s) => `${s} ${m.seats[s].items} items`).join(" · ")} · ${CLASS_ORDER.filter((c) => m.counts[c]).map((c) => `${m.counts[c]} ${c}`).join(", ")}${m.links?.length ? ` · ${m.links.length} area link${m.links.length > 1 ? "s" : ""}` : ""} · module ${m.module}`);
  for (const seat of activeSeats) for (const w of m.seats[seat].warnings) L.push(`WARN ${seat}: ${w}`);
  L.push("");
  const head = ["id", "class", "key", "views", ...activeSeats, "evidence", "variant (agree Δ)"];
  L.push(`| ${head.join(" | ")} |`);
  L.push(`|${head.map(() => "---").join("|")}|`);
  const rows = worksheetOrder(m.items);
  for (const it of rows) {
    const row = [it.id, `${it.class}${it.sev === "MAJOR" ? " MAJ" : ""}`, esc(it.key), esc(it.views.join(",")), ...activeSeats.map((s) => esc(seatCell(it.seats[s]))), esc(evidenceCell(it)), esc(variantCell(it))];
    L.push(`| ${row.join(" | ")} |`);
  }
  if (m.links?.length) {
    L.push("", "## Area links (display only: every item keeps its class)");
    for (const k of m.links) L.push(`${k.id} ${k.images.join(", ")}: ${k.items.join(" + ")} — same area — do together`);
  }
  L.push("", "## Items");
  for (const it of rows) {
    const who = SEATS.filter((s) => it.seats[s]).map((s) => `${s} ${it.seats[s].n}`).join(" + ");
    L.push(`${it.id} ${it.class} ${it.key} (${who})${it.target !== null && it.target !== undefined ? ` — target ${f3(it.target)}` : ""}: ${it.reason}`);
    for (const s of SEATS) if (it.seats[s]) L.push(`  ${s}: ${it.seats[s].sev} ${f3(it.seats[s].now)} → ${f3(it.seats[s].want)} ${it.seats[s].unit ?? ""} · basis ${it.seats[s].basis} · ${it.seats[s].note}`);
    if (it.variant?.lines) for (const l of it.variant.lines) L.push(`  ${l}`);
  }
  L.push("", "## Views (the model as merged; agree = IoU outside the drift rects)");
  L.push(Object.entries(m.views).map(([v, x]) => `${v} iou ${x.iou.toFixed(4)} agree ${x.agree.toFixed(4)}`).join(" · "));
  L.push("", "## Gate", `chain ${m.chain.pass ? "PASS" : "FAIL"} · ${m.chain.violations.length} violations${m.chain.violations.length ? ` (${m.chain.violations.slice(0, 8).join(", ")})` : ""} · tris ${m.chain.tris} / ${m.chain.budget}`);
  if (m.owner.length) { L.push("", "## Owner packet"); for (const o of m.owner) L.push(`${o.id} ${o.class} ${o.key}: ${o.reason}`); }
  if (m.stateAdd.tried.length || m.stateAdd.parked.length) {
    L.push("", "## State additions (gold.mjs applies them to state.json)");
    for (const t of m.stateAdd.tried) L.push(`tried: ${JSON.stringify(t)}`);
    for (const p of m.stateAdd.parked) L.push(`parked: ${JSON.stringify(p)}`);
  }
  return `${L.join("\n")}\n`;
}

// ---------------------------------------------------------------------------------------------------------------------
// The pipeline (I/O): rasters for the evidence, variants, chain, files
// ---------------------------------------------------------------------------------------------------------------------

/** The subject's image name for a critic's at.image: a view name, a view's file name (with or without .png), "concept"
 * or the concept file's name; null when it names no image of the subject. */
export function imageName(spec, conceptFile, image) {
  const s = String(image ?? "").trim();
  const base = s.replace(/^.*[\\/]/, "");
  if (s === "concept" || /^concept(\.png)?$/i.test(base) || base === path.basename(conceptFile ?? "")) return "concept";
  if (spec?.views?.[s]) return s;
  for (const [v, V] of Object.entries(spec?.views ?? {})) if (V.file === base || V.file.replace(/\.png$/i, "") === base) return v;
  return null;
}

/** The evidence raster of one image: the judged reference (family raster; concept: the three-state target) and the
 * model's cel render at the same px (orthos: the judge's sigma; concept: the module's frame), classified by the family table. */
async function imageRaster(ctx, image) {
  if (ctx.rasters.has(image)) return ctx.rasters.get(image);
  const { reg, table } = ctx.turn;
  const cls = new Map();
  const famOf = (r, g, b) => { const k = (r << 16) | (g << 8) | b; let f = cls.get(k); if (f === undefined) { f = classify(table, r, g, b, FAR_RGB, false); cls.set(k, f); } return f; };
  let R;
  if (image === "concept") {
    const T = ctx.T;
    const fam = (await readImage(loadSubject(ctx.subject).paths.target, table, maskOptions(table, "concept"))).fam;
    const proj = ctx.judged.proj;
    const w = proj.w, h = proj.h;
    if (T.length !== w * h) throw new Error(`concept target ${T.length} px != model raster ${w}x${h}`);
    const shade = new Float32Array(w * h);
    for (let i = 0; i < w * h; i += 1) shade[i] = proj.face[i] === 0 ? CEL.top : proj.face[i] === 3 ? CEL.bottom : CEL.facing;
    const rgb = shadeRGB(ctx.parts, ctx.mod.meta.palette, proj.partId, shade, proj.face, w, h);
    const refFg = new Uint8Array(w * h), modelFg = new Uint8Array(w * h), modelFam = new Uint8Array(w * h);
    let care = null;
    for (let i = 0; i < w * h; i += 1) {
      if (T[i] === SUBJECT) refFg[i] = 1;
      if (T[i] === OCCLUDED) { care ??= new Uint8Array(w * h).fill(1); care[i] = 0; }
      if (proj.partId[i] >= 0) { modelFg[i] = 1; modelFam[i] = famOf(rgb[i * 3], rgb[i * 3 + 1], rgb[i * 3 + 2]); }
    }
    R = { w, h, refFg, modelFg, refFam: fam, modelFam, care, names: table.names };
  } else {
    const V = reg.views[image];
    const M = viewMap(reg, image, V.img.w);
    const { meshes } = meshParts(ctx.parts, 0);
    const O = rasterOrtho(meshes, basisOf(V.spec), { k: M.k * ctx.judged.sigma, bx: M.bx, by: M.by }, M.w, M.h, frontRotationDeg(ctx.mod.meta.front));
    if (V.img.w !== M.w || V.img.h !== M.h) throw new Error(`ortho raster ${M.w}x${M.h} != reference ${V.img.w}x${V.img.h}`);
    const rgb = shadeRGB(ctx.parts, ctx.mod.meta.palette, O.partId, O.shade, O.face, M.w, M.h);
    const n = M.w * M.h;
    const refFg = new Uint8Array(n), modelFg = new Uint8Array(n), modelFam = new Uint8Array(n);
    for (let i = 0; i < n; i += 1) {
      if (V.img.fam[i] !== 0) refFg[i] = 1;
      if (O.partId[i] >= 0) { modelFg[i] = 1; modelFam[i] = famOf(rgb[i * 3], rgb[i * 3 + 1], rgb[i * 3 + 2]); }
    }
    R = { w: M.w, h: M.h, refFg, modelFg, refFam: V.img.fam, modelFam, care: null, names: table.names };
  }
  ctx.rasters.set(image, R);
  return R;
}

/** The kernel validator chain under the subject's class gate config (scripts/v7/inspect.mjs chain). */
async function runChain(S, modulePath) {
  await K.init();
  const mod = await importModule(modulePath);
  K.configure(gateConfig(S.cls));
  try {
    const parts = mod.build();
    const rules = S.cls.rules ? await import(pathToFileURL(path.join(ROOT, S.cls.rules)).href) : undefined;
    const r = await validateParts(mod.meta, parts, undefined, { cls: S.cls, rules });
    return { pass: !!r.pass, violations: r.violations.map((v) => `${v.v}${v.part ? ` ${v.part}` : ""}`), tris: r.measurements.tris, budget: r.measurements.triBudget };
  } finally {
    K.configure(null);
  }
}

/** One variants row in this process (scripts/v7/variants.mjs): build with overrides, frame re-fit (no grid), judge. */
async function evalRow(ctx, overrides) {
  const { parts, frame } = buildVariant(ctx.mod, overrides);
  const bad = K.checkParts(ctx.mod.meta, parts);
  if (bad.length) throw new Error(String(bad[0]));
  const built = { meta: ctx.mod.meta, parts, frame };
  const fr = (await fitFrame(conceptIoUFn(ctx.subject, ctx.T, built), built.frame, { grid: false })).frame;
  const { metrics } = await judge({ subjectId: ctx.subject, built: { ...built, frame: fr }, tiles: false });
  return metrics;
}

/** Rule 7 over the classified items (mutates item.variant / target / settled). */
async function runVariants(ctx, items, rules, log) {
  const todo = items.filter((it) => ["A", "B", "CONFLICT"].includes(it.class) && ["knob", "def"].includes(parseKey(it.key)?.kind));
  if (!todo.length) return;
  let base;
  try { base = await evalRow(ctx, {}); } catch (e) { for (const it of todo) it.variant = { error: `BASE: ${String(e.message ?? e).slice(0, 120)}` }; return; }
  const views = Object.keys(base.views);
  const agree = (m, v) => m.views[v].agree ?? m.views[v].iou;
  for (const it of todo) {
    const info = ctx.keys.get(it.key);
    const rowsIn = [];
    const valueFor = (c) => (c.key && parseKey(c.key)?.key === it.key ? c.want : isNum(info?.value) && isNum(c.want) && isNum(c.now) ? r4(info.value + (c.want - c.now)) : c.want);
    if (it.class === "CONFLICT") {
      for (const seat of SEATS) if (it.seats[seat]) {
        const v = valueFor(it.seats[seat]);
        if (!rowsIn.some((r) => sameWant(r.value, v))) rowsIn.push({ seat, value: v });
      }
    } else rowsIn.push({ seat: it.class === "A" ? "target" : SEATS.find((s) => it.seats[s]), value: it.target });
    const rows = [{ label: "BASE", tag: "BASE", value: info?.value ?? null, metrics: base }];
    const errors = [];
    for (const [i, r] of rowsIn.entries()) {
      const tag = `#${i + 1}`;
      const t0 = Date.now();
      try {
        if (!info) throw new Error(`${it.key} is not a key of the module`);
        const metrics = await evalRow(ctx, overridesFor(info, r.value, ctx.mod));
        rows.push({ label: `${tag} ${r.seat}`, tag, seat: r.seat, value: r.value, metrics });
      } catch (e) {
        errors.push(`${tag} ${r.seat} ${JSON.stringify(r.value)}: ${String(e.message ?? e).slice(0, 120)}`);
      }
      log?.(`  variant ${it.id} ${tag} ${it.key} = ${JSON.stringify(r.value)} ${Date.now() - t0} ms`);
    }
    const rule = conceptFirst(rows.map((r) => ({ label: r.label, metrics: r.metrics })));
    for (const r of rows) r.delta = Object.fromEntries(views.map((v) => [v, r4(agree(r.metrics, v) - agree(base, v))]));
    const winner = rule.winner;
    const winRow = rows.find((r) => r.tag === winner);
    let applied = it.class === "CONFLICT" ? (winner && winner !== "BASE" ? winner : null) : rows[1]?.tag ?? null;
    const settled = it.class === "CONFLICT" ? (winner === "BASE" ? "BASE" : winRow?.seat ?? null) : null;
    if (it.class === "CONFLICT" && settled && settled !== "BASE") it.target = winRow.value;
    const appliedRow = rows.find((r) => r.tag === applied);
    const basisViews = it.basis.filter((v) => views.includes(v));
    const loses = appliedRow ? basisViews.filter((v) => -appliedRow.delta[v] > rules.verifyDrop + 1e-12) : [];
    const lines = [
      `variants (concept-first, frame re-fit): ${rows.map((r) => `${r.tag}${r.seat && r.tag !== "BASE" ? ` ${r.seat}` : ""} ${f3(r.value)}: ${views.map((v) => `${v} ${agree(r.metrics, v).toFixed(4)}`).join(" ")}`).join(" | ")}`,
      ...rule.lines.slice(1),
      ...errors.map((e) => `variant error ${e}`),
      `WINNER ${winner ?? "none"}${loses.length ? ` · VERIFY VISUALLY: ${loses.map((v) => `${v} ${sgn(appliedRow.delta[v])}`).join(", ")} on the basis view` : ""}`,
    ];
    if (!appliedRow && it.class !== "CONFLICT") applied = null;
    it.variant = {
      winner, settled, applied, verify: loses.length > 0, dq: rule.dq.map((d) => d.tag), errors,
      rows: rows.map((r) => ({ tag: r.tag, seat: r.seat ?? null, value: r.value, delta: r.delta, agree: Object.fromEntries(views.map((v) => [v, r4(agree(r.metrics, v))])) })),
      lines,
    };
  }
}

/**
 * The merge pipeline: rule 1 (blocked -> {ok: false, blocked: [...]}, nothing written) then rules 2-9; writes
 * critique/rN-merged.json + .md unless write is false.
 * @param {{subject:string, round:number, dir?:string, module?:string, cap?:number, variants?:boolean, write?:boolean, log?:Function}} o
 */
export async function runMerge({ subject, round, dir = null, module = null, cap = MERGE_RULES.cap, variants = true, write = true, force = false, log = null, rules = MERGE_RULES, seats: wantSeats = null }) {
  const t0 = Date.now();
  const gold = path.resolve(dir ?? path.join(ROOT, "out", "ref", "gold", subject));
  const modulePath = path.resolve(module ?? path.join(gold, "model.mjs"));
  const cdir = path.join(gold, "critique");
  const schema = loadSchema();
  const blocked = [], seats = {}, critiques = {};
  // the pair for THIS round: whichever two rN-<seat>.json files exist (SEATS order, fable-first — a legacy subject's
  // rN-fable.json + rN-opus.json pair as before); one found -> its fixed partner (fable's is opus, opus's is sonnet);
  // none found -> DEFAULT_PAIR (opus + sonnet)
  const found = SEATS.filter((seat) => fs.existsSync(path.join(cdir, `r${round}-${seat}.json`)));
  // `seats` (gold.mjs: a class prior's critics.seats, class weapon = ["opus"]): exactly those seats — one is a whole merge
  const pair = Array.isArray(wantSeats) && wantSeats.length > 0 ? [...wantSeats]
    : found.length >= 2 ? found.slice(0, 2) : found.length === 1 ? [found[0], found[0] === "opus" ? "sonnet" : "opus"] : [...DEFAULT_PAIR];
  for (const seat of pair) {
    const file = path.join(cdir, `r${round}-${seat}.json`);
    const rel = path.relative(gold, file).replace(/\\/g, "/");
    if (!fs.existsSync(file)) { blocked.push(`${rel}: missing (run the ${seat} critic)`); continue; }
    let obj;
    try { obj = JSON.parse(fs.readFileSync(file, "utf8")); } catch (e) { blocked.push(`${rel}: not JSON (${e.message})`); continue; }
    const { errors, warnings } = checkCritique(obj, { subject, round, seat }, schema);
    for (const e of errors) blocked.push(`${rel}: ${e}`);
    critiques[seat] = obj;
    seats[seat] = { file: rel, items: Array.isArray(obj.items) ? obj.items.length : 0, warnings };
  }
  if (!fs.existsSync(modulePath)) blocked.push(`module ${modulePath}: missing`);
  // never replace a hand-written worksheet (the v7 rounds' rN-merged.md) unless asked
  const mdFile = path.join(cdir, `r${round}-merged.md`);
  if (write && !force && fs.existsSync(mdFile) && !fs.readFileSync(mdFile, "utf8").startsWith("STOP: ")) blocked.push(`critique/r${round}-merged.md exists and was not written by merge.mjs (a hand merge): --force replaces it`);
  // state.json (created from LEDGER.md when absent)
  const stateFile = path.join(gold, "state.json");
  let state;
  if (fs.existsSync(stateFile)) state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
  else {
    const ledger = path.join(gold, "LEDGER.md");
    state = minimalState(subject, fs.existsSync(ledger) ? fs.readFileSync(ledger, "utf8") : "", round);
    if (write) fs.writeFileSync(stateFile, `${JSON.stringify(state, null, 2)}\n`);
  }
  if (state.modelHash && fs.existsSync(modulePath) && !hashMatches(state.modelHash, modulePath)) blocked.push(`the module changed since close (state.json modelHash ${String(state.modelHash).slice(0, 16)}...): re-close the round`);
  if (blocked.length) return { ok: false, blocked, stateFile };

  // the model as merged: build, judge (views, sigma, concept projection), the key table, the chain
  await K.init();
  const S = loadSubject(subject);
  const turn = await loadTurnaround(subject);
  const mod = await importModule(modulePath);
  const keys = keyTable(mod, fs.readFileSync(modulePath, "utf8"));
  const built = buildVariant(mod, {});
  const judged = await judge({ subjectId: subject, built: { meta: mod.meta, parts: built.parts, frame: built.frame }, tiles: false });
  const { T } = await conceptTarget(subject);
  const ctx = { subject, mod, keys, parts: built.parts, judged, turn, T, rasters: new Map() };
  log?.(`model judged ${Date.now() - t0} ms`);

  // rule 2: evidence per item with `at`
  const evidence = {};
  for (const seat of pair) {
    evidence[seat] = [];
    for (const item of critiques[seat].items) {
      if (!item.at) { evidence[seat].push(null); continue; }
      const image = imageName(turn.spec, S.paths.target, item.at.image);
      if (!image) { evidence[seat].push({ ok: false, image: item.at.image, text: `at.image "${item.at.image}" is not an image of ${subject} (concept, ${turn.reg.names.join(", ")})` }); continue; }
      const expect = item.at.claim === "colour" ? { ref: hexFamily(turn.table, item.want), model: hexFamily(turn.table, item.now) } : {};
      const res = claimTest(await imageRaster(ctx, image), item.at.rect, item.at.claim, rules.share, expect, rules.edgeMinPx ?? MERGE_RULES.edgeMinPx);
      evidence[seat].push({ ...res, image, text: `${image} ${res.text}` });
    }
  }
  log?.(`evidence ${Date.now() - t0} ms`);
  const drift = turn.table.drift ?? null;
  const { items, stateAdd } = classifyItems({ critiques, evidence, keys, drift, state, round, rules });
  if (variants) await runVariants(ctx, items, rules, log);
  log?.(`variants ${Date.now() - t0} ms`);
  const links = areaLinks(items, rules.linkPx);
  const chain = await runChain(S, modulePath);
  const views = Object.fromEntries(Object.entries(judged.metrics.views).map(([v, m]) => [v, { iou: m.iou, agree: m.agree ?? m.iou }]));
  const stop = stopLine({ items, views, chainPass: chain.pass, round, cap, bar: rules.bar });
  const counts = Object.fromEntries(CLASS_ORDER.map((c) => [c, items.filter((it) => it.class === c).length]));
  const owner = items.filter((it) => it.owner || (it.class === "X" && round >= cap - 1)).map((it) => ({ id: it.id, class: it.class, key: it.key, reason: it.reason }));
  const merged = {
    stop: { verdict: stop.verdict, reason: stop.reason, line: stop.line, standing: stop.standing },
    subject, round, cap, module: path.relative(ROOT, modulePath).replace(/\\/g, "/"), moduleHash: `sha256:${hashFile(modulePath)}`,
    seats, views, chain, counts, rules, items, links, owner, stateAdd,
  };
  const md = renderMarkdown(merged);
  const files = { json: path.join(cdir, `r${round}-merged.json`), md: path.join(cdir, `r${round}-merged.md`) };
  if (write) {
    fs.writeFileSync(files.json, `${JSON.stringify(merged, null, 2)}\n`);
    fs.writeFileSync(files.md, md);
  }
  return { ok: true, merged, md, files, stateFile, ms: Date.now() - t0 };
}

// ---------------------------------------------------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------------------------------------------------

const USAGE = `usage: node scripts/v7/merge.mjs --subject <s> --round <N> [--dir out/ref/gold/<s>] [--module <m.mjs>] [--cap 3] [--no-variants] [--force] [--quiet]
       node scripts/v7/merge.mjs --validate <critique.json> ...
       node scripts/v7/merge.mjs --keys --module <m.mjs>`;

async function main() {
  const args = parseArgs(process.argv.slice(2), ["no-variants", "quiet", "keys", "force", "help"]);
  if (args.help) { console.log(USAGE); return 0; }
  if (args.validate) {
    const files = [args.validate, ...args._].filter((f) => f && f !== true);
    const schema = loadSchema();
    let bad = 0;
    for (const f of files) {
      let obj;
      try { obj = JSON.parse(fs.readFileSync(f, "utf8")); } catch (e) { console.log(`${f}: NOT JSON (${e.message})`); bad += 1; continue; }
      const { errors, warnings } = checkCritique(obj, {}, schema);
      console.log(`${f}: ${errors.length ? "ERRORS" : "OK"}${[...errors, ...warnings.map((w) => `WARN ${w}`)].map((x) => `\n  ${x}`).join("")}`);
      if (errors.length) bad += 1;
    }
    return bad ? 1 : 0;
  }
  if (args.keys) {
    if (!args.module || args.module === true) throw new Error("--keys needs --module <m.mjs>");
    const mod = await importModule(args.module);
    for (const k of keyTable(mod, fs.readFileSync(path.resolve(args.module), "utf8")).values()) {
      console.log(`${k.key} = ${JSON.stringify(k.value)}${k.unit ? ` ${k.unit}` : ""}${k.group ? ` [${k.group}]` : ""} axis ${k.axis ?? "-"}${k.comment ? `  // ${k.comment}` : ""}`);
    }
    return 0;
  }
  const round = Number(args.round);
  if (!args.subject || args.subject === true || !Number.isInteger(round) || round < 1) { console.log(USAGE); return 3; }
  const cap = args.cap !== undefined ? Number(args.cap) : MERGE_RULES.cap;
  const log = args.quiet ? null : (s) => console.error(s);
  const r = await runMerge({ subject: args.subject, round, dir: args.dir && args.dir !== true ? args.dir : null, module: args.module && args.module !== true ? args.module : null, cap, variants: !args["no-variants"], force: !!args.force, log });
  if (!r.ok) {
    console.log(`MERGE BLOCKED — ${args.subject} r${round}:`);
    for (const b of r.blocked) console.log(`  ${b}`);
    return 2;
  }
  console.log(r.merged.stop.line);
  const c = r.merged.counts;
  console.log(CLASS_ORDER.filter((k) => c[k]).map((k) => `${c[k]} ${k}`).join(", "));
  console.log(`wrote ${path.relative(process.cwd(), r.files.md)} + .json (${(r.ms / 1000).toFixed(1)} s)`);
  return 0;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase();
if (isMain) main().then((code) => process.exit(code ?? 0), (e) => { console.error(e.stack ?? e.message ?? e); process.exit(1); });
