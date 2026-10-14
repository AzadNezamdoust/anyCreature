#!/usr/bin/env node
// WORKFLOW-V3 §7.5 item 5 — the MISSING KEY consumer.
//
// A seat that needs a layout number nobody measured says so on a `MISSING KEY`
// line (or, in run 4, as a `; MISSING KEY a, b.` clause inside its CHANGE line).
// Until now nobody read those lines. This module parses them out of every seat
// reply (last.md / repair.md), merges them into the subject's backlog file
// (`subject.paths.missingKeys`, `{key:{count, passes[], firstSeen}}`), prints the
// backlog at preflight, and — under `missingKeyPolicy:"refuse"` — names the keys
// that make a re-run of the same item pointless (count >= 2, still not in
// layout.json). pass.mjs turns that list into a RefusalError (exit 3).
//
//   node scripts/missing-keys.mjs [--subject <id>]                 print the backlog
//   node scripts/missing-keys.mjs [--subject <id>] --seed <dir> [--force]
//        seed the backlog from <dir>/P*/last.md (e.g. out/facade/run4)
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { loadSubject, subjectIdFromArgv, ROOT } from "./subject.mjs";

const KEY_RE = /^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)*$/;
const NOT_KEYS = new Set(["none", "n/a", "na", "nil"]);

/** Strip fenced code blocks — a module comment is not a seat's request. */
const withoutFences = (text) => String(text ?? "").replace(/```[\s\S]*?```/g, "");

/**
 * Keys named on `MISSING KEY[S][:] a, b` lines or clauses, in first-seen order.
 * @param {string} text a seat reply
 * @returns {string[]}
 */
export function parseMissingKeys(text) {
  const keys = [];
  for (const m of withoutFences(text).matchAll(/MISSING KEYS?\b\s*:?\s*([^\n]*)/gi)) {
    for (const raw of m[1].split(/[,;]/)) {
      const key = raw.trim().replace(/^`+|`+$/g, "").replace(/[.\s]+$/, "").replace(/^`+|`+$/g, "");
      if (!key || NOT_KEYS.has(key.toLowerCase()) || !KEY_RE.test(key)) continue;
      if (!keys.includes(key)) keys.push(key);
    }
  }
  return keys;
}

/**
 * The text-mode reply contract: one ```js fence (the COMPLETE module), one
 * `CHANGE:` line, optional `MISSING KEY:` line. The largest js fence wins so a
 * quoted snippet above the module cannot replace it.
 * @returns {{artifact:string|null, change:string|null, missingKeys:string[]}}
 */
export function parseReply(text) {
  const src = String(text ?? "");
  let artifact = null;
  for (const m of src.matchAll(/```(?:js|javascript|mjs)[^\n]*\n([\s\S]*?)```/gi)) {
    if (artifact === null || m[1].length > artifact.length) artifact = m[1];
  }
  const change = /^\s*CHANGE:\s*(.+)$/m.exec(withoutFences(src))?.[1]?.trim() ?? null;
  return { artifact, change, missingKeys: parseMissingKeys(src) };
}

/** Pure merge: every key reported once more, by `pass`, first seen at `at`. */
export function mergeMissingKeys(backlog, keys, pass, at = new Date().toISOString()) {
  const out = JSON.parse(JSON.stringify(backlog ?? {}));
  for (const key of keys) {
    const entry = out[key] ?? { count: 0, passes: [], firstSeen: at };
    entry.count += 1;
    if (!entry.passes.includes(pass)) entry.passes.push(pass);
    out[key] = entry;
  }
  return out;
}

export function readBacklog(file) {
  if (!file || !fs.existsSync(file)) return {};
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

export function writeBacklog(file, backlog) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(backlog, null, 2)}\n`);
}

/** Parse one seat reply and merge it into the backlog file. */
export function recordMissingKeys(file, pass, text, at = new Date().toISOString()) {
  const keys = parseMissingKeys(text);
  if (!file) return { keys, backlog: {} };
  const backlog = mergeMissingKeys(readBacklog(file), keys, pass, at);
  if (keys.length > 0 || fs.existsSync(file)) writeBacklog(file, backlog);
  return { keys, backlog };
}

/** layout.json keys are flat dotted names (`window.w`); `_` keys are metadata. */
export const layoutHas = (layout, key) => Boolean(layout && !key.startsWith("_") && Object.hasOwn(layout, key));

/**
 * Keys that make re-running `pass` pointless: asked for by that pass's seats at
 * least twice in total and still absent from layout.json.
 */
export function refusedKeys(backlog, layout, pass) {
  return Object.entries(backlog ?? {})
    .filter(([key, e]) => e.count >= 2 && (e.passes ?? []).includes(pass) && !layoutHas(layout, key))
    .map(([key]) => key);
}

export function backlogLines(backlog, layout) {
  const rows = Object.entries(backlog ?? {}).sort((a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0]));
  if (rows.length === 0) return ["[missing-keys] backlog empty"];
  const open = rows.filter(([k]) => !layoutHas(layout, k)).length;
  return [
    `[missing-keys] backlog ${rows.length} key(s), ${open} still absent from layout.json`,
    ...rows.map(([k, e]) => `[missing-keys]   ${k} x${e.count} (${e.passes.join(",")})${layoutHas(layout, k) ? " — now in layout" : ""}`),
  ];
}

/** Seed from `<dir>/P*\/last.md`, passes in numeric order, firstSeen = file mtime. */
export function seedBacklog(dir) {
  let backlog = {};
  const passes = fs.readdirSync(dir).filter((d) => /^P\d+$/.test(d)).sort((a, b) => Number(a.slice(1)) - Number(b.slice(1)));
  for (const label of passes) {
    const file = path.join(dir, label, "last.md");
    if (!fs.existsSync(file)) continue;
    const at = fs.statSync(file).mtime.toISOString();
    backlog = mergeMissingKeys(backlog, parseMissingKeys(fs.readFileSync(file, "utf8")), label, at);
  }
  return backlog;
}

function main() {
  const argv = process.argv.slice(2);
  const S = loadSubject(subjectIdFromArgv(argv));
  const file = S.paths.missingKeys;
  if (!file) throw new Error(`subjects/${S.id}/subject.json has no paths.missingKeys`);
  const seedAt = argv.indexOf("--seed");
  if (seedAt >= 0) {
    if (fs.existsSync(file) && !argv.includes("--force")) {
      throw new Error(`${path.relative(ROOT, file)} exists — seeding would double-count; pass --force to overwrite`);
    }
    writeBacklog(file, seedBacklog(path.resolve(ROOT, argv[seedAt + 1])));
  }
  for (const line of backlogLines(readBacklog(file), S.readJson("layout"))) console.log(line);
  return 0;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    process.exitCode = main();
  } catch (error) {
    console.error(`missing-keys: ${error.message}`);
    process.exitCode = 1;
  }
}
