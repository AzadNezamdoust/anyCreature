#!/usr/bin/env node
// The gate every authored subject module passes before anything renders it.
//
//   node scripts/check-module.mjs subjects/facade_brick/facade.mjs
//
// Static half: the module may import the kernel and NOTHING else, and may not
// reach the clock, the network, the host or the compiler (V2-TEST-PLAN 2).
// Dynamic half: it exports `meta` + `build`, and `build()` returns parts the
// kernel recognises. Exit 0 = PASS, 1 = FAIL, at most 8 lines of output.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { gateConfig } from "../src/validate/kernel-chain.mjs";
import { loadSubject, subjectIdFromArgv } from "./subject.mjs";

const KERNEL_IMPORT = /(^|[\\/])src[\\/]kernel[\\/]index\.mjs$/;

/** Banned constructs, as {label, regex} on comment-stripped source. */
const BANNED = [
  ["Math.random", /\bMath\s*\.\s*random\b/],
  ["Date", /\bDate\b/],
  ["fetch", /\bfetch\s*\(/],
  ["performance", /\bperformance\b/],
  ["require", /\brequire\s*\(/],
  ["process", /\bprocess\b/],
  ["dynamic import()", /\bimport\s*\(/],
  ["eval", /\beval\s*\(/],
  ["new Function", /\bnew\s+Function\b/],
];

/** Drop // and /* *\/ comments so a word in prose is never a violation. */
function stripComments(source) {
  return source.replace(/\/\*[\s\S]*?\*\//g, " ").replace(/(^|[^:])\/\/[^\n]*/g, "$1");
}

function staticGate(file, source) {
  const bad = [];
  const code = stripComments(source);
  const specifiers = [
    ...[...code.matchAll(/\bfrom\s*["']([^"']+)["']/g)].map((m) => m[1]),
    ...[...code.matchAll(/\bimport\s*["']([^"']+)["']/g)].map((m) => m[1]),
  ];
  for (const spec of specifiers) {
    const resolved = spec.startsWith(".") ? path.resolve(path.dirname(file), spec) : spec;
    if (!KERNEL_IMPORT.test(resolved.replace(/\\/g, "/"))) bad.push(`import "${spec}": only src/kernel/index.mjs is allowed`);
  }
  for (const [label, pattern] of BANNED) {
    if (pattern.test(code)) bad.push(`banned: ${label}`);
  }
  return bad;
}

/**
 * WF-R3 item 7 — the author's own line in a throw: the first stack frame inside the module file, as
 * "<file>:<line>:<col>: <source line>". Gemini-M's blind P2 attempt 1 died on "ladder width undefined" with no line.
 */
export function authorLine(error, file, source) {
  const href = pathToFileURL(file).href;
  const stack = String(error?.stack ?? "");
  let m = null;
  for (const where of [href, file]) {
    const i = stack.indexOf(`${where}:`);
    if (i >= 0) { m = /^:(\d+):(\d+)/.exec(stack.slice(i + where.length)); if (m) break; }
  }
  if (!m) return null;
  const text = (source ?? "").split("\n")[Number(m[1]) - 1]?.trim() ?? "";
  return `${path.basename(file)}:${m[1]}:${m[2]}${text ? `: ${text.slice(0, 160)}` : ""}`;
}

/**
 * The whole gate as a function (WF v8 WP3: scripts/v7/step.mjs runs it in-process). `file` = the module path; `label` =
 * the name the lines print (the CLI prints its argument as given); `subjectId` = whose class gate config the cut check
 * reads (the CLI: --subject / LLMM_SUBJECT / the default subject; null = the kernel default floor). The module is imported
 * by its file URL and built once, under that config (reset to none afterwards).
 * @returns {Promise<{pass:boolean, lines:string[], mod?:object, meta?:object, parts?:object[], tris?:number}>}  lines =
 *   exactly what the CLI prints (at most 8); on PASS mod / meta / parts / tris are the built module
 */
export async function checkModule(file, { label = file, subjectId = null } = {}) {
  const fail = (...rest) => ({ pass: false, lines: [`FAIL ${label}`, ...rest] });
  if (!fs.existsSync(file)) return { pass: false, lines: [`FAIL no such module: ${label}`] };

  const source = fs.readFileSync(file, "utf8");
  const bad = staticGate(file, source);
  if (bad.length > 0) return fail(...bad.slice(0, 6).map((line) => `  ${line}`));

  let mod;
  try {
    mod = await import(pathToFileURL(file).href);
  } catch (error) {
    const at = authorLine(error, file, source);
    return fail(`  import threw: ${error.message}`, ...(at ? [`  at ${at}`] : []));
  }

  if (typeof mod.build !== "function") return fail("  build: missing exported function");

  await K.init();
  // WF-BLIND-R2 C14 — the cut check reads the SUBJECT's class floor (LLMM_SUBJECT / --subject), set before build().
  try { K.configure(subjectId ? gateConfig(loadSubject(subjectId).cls) : null); } catch { K.configure(null); }
  let parts;
  try {
    K.resetCounters();   // the boolean count of this build alone (a fresh CLI process starts at 0 anyway)
    parts = mod.build();
  } catch (error) {
    const at = authorLine(error, file, source);
    return fail(`  build() threw: ${error.message}`, ...(at ? [`  at ${at}`] : []));
  } finally {
    K.configure(null);
  }

  const violations = K.checkParts(mod.meta, parts);
  if (violations.length > 0) return fail(...violations.slice(0, 6).map((line) => `  ${line}`));

  const tris = parts.reduce((sum, p) => sum + p.solid.triCount(), 0);
  // WF-BLIND-R2 C9 — a thin cut is not a contract failure: the chain reports it as a V5_THIN row with its location.
  const thin = parts.filter((p) => p.solid.thinCuts().length > 0).length;
  return { pass: true, mod, meta: mod.meta, parts, tris, lines: [`PASS ${label} — ${parts.length} parts, ${tris} tris, ${K.counters.booleans} booleans`
    + `${thin ? `; ${thin} part(s) carry a thin cut (the gate reports V5_THIN)` : ""}`] };
}

async function main() {
  const arg = process.argv[2];
  if (!arg) { console.log("FAIL usage: node scripts/check-module.mjs <module.mjs>"); return 1; }
  const r = await checkModule(path.resolve(arg), { label: arg, subjectId: subjectIdFromArgv(process.argv.slice(3)) });
  for (const line of r.lines) console.log(line);
  return r.pass ? 0 : 1;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) process.exitCode = await main();
