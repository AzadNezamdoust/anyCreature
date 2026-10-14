#!/usr/bin/env node
// The node gate: compile + V0-V7 + V10 on every spec named on the command line.
// Repair is OFF here on purpose — `check` reports what the author wrote, not
// what an auto-repair could make of it (08:G3: a worker must not be able to
// pass its own gate by being repaired).
//
//   node scripts/check-spec.mjs subjects/tenement_block/spec.json …
//
// Exit 1 on the first FAIL, after printing every report.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

import { validateSpec } from "../src/validate/index.js";

const files = process.argv.slice(2);
if (files.length === 0) {
  console.error("usage: node scripts/check-spec.mjs <spec.json…>");
  process.exit(2);
}

let failed = 0;
for (const file of files) {
  const label = path.relative(process.cwd(), file).replace(/\\/g, "/");
  let report;
  try {
    report = validateSpec(JSON.parse(fs.readFileSync(file, "utf8")));
  } catch (error) {
    console.log(`${label}\nFAIL: compile threw — ${error.message}`);
    failed += 1;
    continue;
  }
  console.log(`${label}\n${report.text}`);
  if (!report.pass) failed += 1;
}

if (failed > 0) console.log(`\n${failed} of ${files.length} spec(s) FAILED.`);
process.exit(failed > 0 ? 1 : 0);
