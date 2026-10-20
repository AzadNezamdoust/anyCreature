#!/usr/bin/env node
// One markdown row per pass, appended to out/facade/measurements.md
// (V2-TEST-PLAN §5). `pass.mjs` calls this; it also runs on its own for a pass
// whose directory already exists.
//
//   node scripts/measure.mjs <P> [--run <id>] [--manual <seconds>]
//
// Every column is MEASURED, never estimated: the numbers come out of
// out/facade/P<N>/timings.json (wall clock, tokens, repairs, kernel counters,
// capture, likeness) and report.json (the validator's own timings, tris, parts,
// V-codes). "edit-to-preview" is the §5 line item: kernel build + validate +
// capture, the seconds between a module edit and a frame a human can look at.
//
// WF-LOOP-R2 A7, three changes:
//  - a RUN and an ATTEMPT column. Fourteen rows labelled "P3" with no way to
//    tell run 1 from run 2 from the third re-gate of the same module made the
//    sheet unreadable exactly when it was needed (see the P3 block below).
//    `--run` names the run; the attempt is counted from the rows already in the
//    section, so a re-run is "P3.2", not a second "P3".
//  - the one wall-clock column is split into SEAT / GATE / CAPTURE / LIKENESS /
//    MANUAL. "seat 253 s" hid the fact that 5 s of it was the thing being
//    optimised; MANUAL is the only estimated cell in the sheet and the only one
//    a human writes (the LOOK review), so it is a column, not an average.
//  - rows are appended to the LAST table in the file. They used to be inserted
//    straight after the FIRST separator line, so every new row landed ABOVE the
//    "## Run 2" heading that was supposed to introduce it.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { loadSubject, subjectIdFromArgv } from "./subject.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");

/**
 * WORKFLOW-V3 §3 — the `tokens` cell. The total stays the first number (it is the
 * billed scalar every older row carries); the input / cached / output / reasoning
 * split follows only when the seat adapter measured it.
 */
export function tokensCell(timings) {
  const usage = timings?.usage ?? {};
  const total = String(usage.total ?? timings?.tokens ?? 0);
  const split = [["in", "input"], ["cached", "cached"], ["out", "output"], ["reason", "reasoning"]]
    .filter(([, k]) => Number.isFinite(usage[k]))
    .map(([label, k]) => `${label} ${usage[k]}`);
  return split.length ? `${total} (${split.join(" · ")})` : total;
}

export const COLUMNS = [
  "run", "pass", "attempt",
  "seat s", "gate s", "capture s", "likeness s", "manual s",
  "tokens", "repairs", "kernel build ms", "booleans", "toThree ms",
  "edit-to-preview s", "tris", "parts",
  "gate", "V-codes", "likeness", "LK-codes",
];

const HEADER = [
  "",
  "One row per `scripts/pass.mjs` run. Thresholds this table is read against live in",
  "`V2-TEST-PLAN.md` §5: <= 2 repairs total across P0-P4, edit-to-preview <= 5 s,",
  "kernel build + validate <= 1 s at <= 3000 tris, <= 15k tokens per pass and <= 75k total.",
  "None of those numbers is ratified. `manual s` is the only estimated cell: it is the",
  "reviewer's own time on the three LOOK rows, written in by hand.",
  "",
  `| ${COLUMNS.join(" | ")} |`,
  `|${COLUMNS.map(() => "---").join("|")}|`,
].join("\n");

const SHEET_TITLE = "# Façade pass measurements";

function readJson(file) {
  if (!fs.existsSync(file)) throw new Error(`missing ${path.relative(ROOT, file).replace(/\\/g, "/")}`);
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

const s1 = (ms) => (ms / 1000).toFixed(1);

export function buildRow(label, timings, report, { run = "-", attempt = 1, manual = null } = {}) {
  const kernelBuildMs = timings.kernelBuildMs ?? 0;
  const validatorMs = report?.timings?.total ?? timings.validatorMs ?? 0;
  const toThreeMs = report?.timings?.merge ?? timings.toThreeMs ?? 0;
  const captureMs = timings.captureMs ?? 0;
  const likenessMs = timings.likenessMs ?? 0;
  const editToPreview = (kernelBuildMs + validatorMs + captureMs) / 1000;

  const codes = [...new Set([
    ...(report?.violations ?? []).map((x) => x.v),
    ...(report?.advisories ?? []).map((x) => x.v),
  ])];
  const lkCodes = timings.likenessCodes ?? [];

  const cells = [
    run,
    `${label}${timings.dry ? " (dry)" : ""}`,
    String(attempt),
    (timings.codexSeconds ?? 0).toFixed(1),
    s1(kernelBuildMs + validatorMs),
    s1(captureMs),
    s1(likenessMs),
    manual === null ? "-" : Number(manual).toFixed(0),
    tokensCell(timings),
    String(timings.repairs ?? 0),
    String(kernelBuildMs),
    String(timings.booleans ?? 0),
    String(toThreeMs),
    editToPreview.toFixed(2),
    String(report?.measurements?.tris ?? "-"),
    String(report?.measurements?.parts ?? "-"),
    report?.pass ? "PASS" : "FAIL",
    codes.length > 0 ? codes.join(" ") : "none",
    timings.likenessPass === null || timings.likenessPass === undefined
      ? "-" : (timings.likenessPass ? "PASS" : "FAIL"),
    lkCodes.length > 0 ? lkCodes.join(" ") : (timings.likenessPass ? "none" : "-"),
  ];
  return `| ${cells.join(" | ")} |`;
}

/**
 * A7 — find where a row belongs: the end of the LAST table in the document. If
 * the last heading in the file has no table under it (the "## Run 2" case), the
 * section gets its own fresh header first, so a run's rows sit under the run's
 * heading instead of jumping above it.
 * @returns {{lines: string[], insertAt: number}}
 */
export function placeRow(text) {
  const lines = text.split(/\r?\n/);
  let lastSeparator = -1;
  let lastHeading = -1;
  for (let i = 0; i < lines.length; i += 1) {
    if (/^\|\s*---/.test(lines[i])) lastSeparator = i;
    if (/^#{1,6}\s/.test(lines[i]) && lines[i].trim() !== SHEET_TITLE) lastHeading = i;
  }
  if (lastSeparator === -1 || lastHeading > lastSeparator) {
    // No table at all, or the newest section has none: open one at the end.
    while (lines.length && lines[lines.length - 1].trim() === "") lines.pop();
    lines.push(...HEADER.split("\n"));
    return { lines, insertAt: lines.length };
  }
  let insertAt = lastSeparator + 1;
  while (insertAt < lines.length && lines[insertAt].startsWith("|")) insertAt += 1;
  return { lines, insertAt };
}

/** How many rows for this (run, pass) already sit in the section being appended to. */
function attemptNumber(lines, insertAt, run, label) {
  let n = 0;
  for (let i = 0; i < insertAt; i += 1) {
    if (!lines[i].startsWith("|")) continue;
    const cells = lines[i].split("|").map((c) => c.trim());
    if (cells[1] === run && (cells[2] === label || cells[2] === `${label} (dry)`)) n += 1;
  }
  return n + 1;
}

function main() {
  const argv = process.argv.slice(2);
  const valued = new Set(["--run", "--manual", "--subject"]);
  const arg = argv.find((a, i) => !a.startsWith("--") && !valued.has(argv[i - 1]));
  if (!arg) throw new Error("usage: node scripts/measure.mjs <P> [--subject <id>] [--run <id>] [--manual <seconds>]");
  const FACADE_OUT = path.join(ROOT, loadSubject(subjectIdFromArgv(argv)).subject.outDir);
  const SHEET = path.join(FACADE_OUT, "measurements.md");
  const flag = (name) => {
    const i = argv.indexOf(`--${name}`);
    return i === -1 ? null : argv[i + 1];
  };
  const label = `P${String(arg).replace(/^P/i, "")}`;
  const run = flag("run") ?? process.env.LLMM_RUN ?? "-";
  const manual = flag("manual");
  const dir = path.join(FACADE_OUT, label);

  const timings = readJson(path.join(dir, "timings.json"));
  const report = readJson(path.join(dir, "report.json"));

  fs.mkdirSync(FACADE_OUT, { recursive: true });
  if (!fs.existsSync(SHEET)) fs.writeFileSync(SHEET, `${SHEET_TITLE}\n${HEADER}\n`);

  const { lines, insertAt } = placeRow(fs.readFileSync(SHEET, "utf8"));
  const attempt = attemptNumber(lines, insertAt, run, label);
  const row = buildRow(label, timings, report, { run, attempt, manual });
  lines.splice(insertAt, 0, row);
  fs.writeFileSync(SHEET, lines.join("\n"));

  console.log(row);
  console.log(`[measure] appended to ${path.relative(ROOT, SHEET).replace(/\\/g, "/")}`);
  return 0;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    process.exitCode = main();
  } catch (error) {
    console.error(`measure: ${error.message}`);
    process.exitCode = 1;
  }
}
