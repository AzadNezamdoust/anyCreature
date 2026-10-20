#!/usr/bin/env node
// blind-test.mjs — run ONE workflow pass with a TEST seat and leave the live subject untouched.
//
//   node scripts/blind-test.mjs --subject pickup --pass P1 --seat agy|terra|luna|gmed [--from <module file>] [--prep-previous] [--keep]
//   node scripts/blind-test.mjs --subject pickup --loop --seat luna|gmed|opus|terra|agy [--from <module file>] [--K 4] [--no-images] [--keep]
//
// WORKFLOW v4 V4-3 — `--loop` runs scripts/loop.mjs (FIT -> BUILD -> re-FIT -> LOOP) instead of pass.mjs: same
// snapshot / restore of the live module, the loop folder <outDir>/loop/ in place of the pass folder, the same retry
// on exit 2 and NO_RESULT semantics; the result lands in out/blind/<subject>/<seat>/LOOP/ (loop.json, every step,
// module.<seat>.mjs = the loop's best module). The loop itself never writes the live module.
//
// Owner 2026-09-13: the workflow passes only if Gemini 3.8 High AND GPT 5.6 Terra each produce good
// models BLIND. Every test run must start from the same frozen module and must never leak a test
// seat's output into the live subject (the failed pickup P0 seat once left a broken module there).
//
// Steps: snapshot the live module + <outDir>/<pass>/ + measurements.md → optionally copy `--from`
// over the live module (so two seats start from identical bytes) → run `pass.mjs <pass> --subject
// <s> --seat <seat> --seat-mode text` (retry once on exit 2, a transport drop) → copy the pass folder
// and the module the seat produced to out/blind/<subject>/<seat>/<pass>/ → restore the live module,
// the pass folder and measurements.md from the snapshot, byte-compared, even on failure.
// `--keep` leaves the seat's module live (only for an owner-accepted result).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

import { ROOT, loadSubject } from "./subject.mjs";

function arg(name, fallback = null) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[i + 1] : fallback;
}

const subjectId = arg("subject");
const loop = process.argv.includes("--loop");
const pass = loop ? "LOOP" : arg("pass");
const seat = arg("seat");
const from = arg("from");
const keep = process.argv.includes("--keep");
// --prep-previous: render the previous pass gate-only from the start module first, so the seat's prompt
// carries stills of the module it actually starts from (building P2 needs P1 stills of the template).
const prepPrevious = process.argv.includes("--prep-previous");
if (!subjectId || !pass || !seat) {
  console.error("usage: node scripts/blind-test.mjs --subject <id> (--pass <P#> | --loop [--K 4] [--no-images]) --seat agy|terra|luna|gmed|opus [--from <module>] [--prep-previous] [--keep]");
  process.exit(3);
}
if (!["agy", "terra", "luna", "gmed", "opus"].includes(seat)) {
  console.error(`blind-test: --seat must be a TEST seat (agy | terra | luna | gmed), got "${seat}" — examiner seats run through pass.mjs directly`);
  process.exit(3);
}

const S = loadSubject(subjectId);
const label = loop ? "LOOP" : /^P/i.test(pass) ? pass.toUpperCase() : `P${pass}`;
const modulePath = S.paths.module;
const outRoot = path.join(ROOT, S.subject.outDir ?? `out/${subjectId}`);
const passDir = path.join(outRoot, loop ? "loop" : label);
const prevLabel = `P${Number(label.slice(1)) - 1}`;
const prevDir = path.join(outRoot, prevLabel);
const measurements = path.join(outRoot, "measurements.md");
const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const snap = path.join(ROOT, "out", "blind", subjectId, ".snapshots", `${seat}-${label}-${stamp}`);
const dest = path.join(ROOT, "out", "blind", subjectId, seat, label);

const copyDir = (src, dst) => { fs.rmSync(dst, { recursive: true, force: true }); if (fs.existsSync(src)) fs.cpSync(src, dst, { recursive: true }); };
const same = (a, b) => fs.existsSync(a) && fs.existsSync(b) && fs.readFileSync(a).equals(fs.readFileSync(b));

fs.mkdirSync(snap, { recursive: true });
fs.copyFileSync(modulePath, path.join(snap, "module.live"));
copyDir(passDir, path.join(snap, label));
if (prepPrevious) copyDir(prevDir, path.join(snap, prevLabel));
if (fs.existsSync(measurements)) fs.copyFileSync(measurements, path.join(snap, "measurements.md"));
console.log(`[blind] snapshot ${path.relative(ROOT, snap)}`);

let exit = 1;
try {
  if (from) {
    fs.copyFileSync(path.resolve(ROOT, from), modulePath);
    console.log(`[blind] start module <- ${from}`);
  }
  fs.copyFileSync(modulePath, path.join(snap, "module.start"));
  if (prepPrevious && loop) throw new Error("--prep-previous is a pass.mjs option; the loop starts from --from or the template");
  if (prepPrevious) {
    if (Number(label.slice(1)) < 1) throw new Error("--prep-previous needs a pass after P0");
    const prep = spawnSync(process.execPath, [path.join(ROOT, "scripts", "pass.mjs"), prevLabel, "--subject", subjectId, "--gate-only", "--no-repair"],
      { cwd: ROOT, stdio: "inherit" });
    console.log(`[blind] prepared ${prevLabel} stills from the start module (gate-only exit=${prep.status})`);
    if (prep.status === 2 || prep.status === 3) throw new Error(`--prep-previous: ${prevLabel} gate-only could not run (exit ${prep.status})`);
    fs.copyFileSync(path.join(snap, "module.start"), modulePath);   // gate-only may recalibrate the palette
  }
  // WF-R3 H1 — a review.md left in the pass folder (restored by the snapshot) belongs to another module; it must never
  // be archived with this seat's result. The P<N-1> review is stale too once --prep-previous re-rendered that pass.
  fs.rmSync(path.join(passDir, "review.md"), { force: true });
  if (prepPrevious) fs.rmSync(path.join(prevDir, "review.md"), { force: true });
  const transports = [];
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    // START = the class template unless --from names a start module (the loop never reads the live module)
    const loopArgs = ["--subject", subjectId, "--seat", seat, ...(from ? ["--from", from] : []),
      ...(arg("K") ? ["--K", arg("K")] : []), ...(process.argv.includes("--no-images") ? ["--no-images"] : [])];
    const run = loop
      ? spawnSync(process.execPath, [path.join(ROOT, "scripts", "loop.mjs"), ...loopArgs], { cwd: ROOT, stdio: "inherit" })
      : spawnSync(process.execPath, [path.join(ROOT, "scripts", "pass.mjs"), label, "--subject", subjectId, "--seat", seat, "--seat-mode", "text"],
        { cwd: ROOT, stdio: "inherit" });
    exit = run.status ?? 2;
    console.log(`[blind] ${seat} ${subjectId} ${label} attempt ${attempt} exit=${exit}`);
    if (exit !== 2) break;
    // WF-BLIND-R2 C7 — keep EVERY dropped attempt's seat transcript; the next attempt overwrites transcript.txt.
    const transcript = path.join(passDir, loop ? "loop.json" : "transcript.txt");
    if (fs.existsSync(transcript)) {
      const keepAs = path.join(snap, `transport-attempt-${attempt}${loop ? ".json" : ".txt"}`);
      fs.copyFileSync(transcript, keepAs);
      transports.push(keepAs);
    }
  }
  fs.rmSync(dest, { recursive: true, force: true });
  if (exit === 2) {
    // WF-BLIND-R2 C8 — the seat never answered: NO_RESULT, and the pass folder (a stale or half-written run) is
    // NOT archived as the seat's result. Only the kept transport transcripts go with the record.
    fs.mkdirSync(dest, { recursive: true });
    for (const file of transports) fs.copyFileSync(file, path.join(dest, path.basename(file)));
  } else {
    copyDir(passDir, dest);
    const produced = loop ? path.join(passDir, "best.mjs") : modulePath;
    if (fs.existsSync(produced)) fs.copyFileSync(produced, path.join(dest, `module.${seat}${path.extname(modulePath)}`));
    fs.copyFileSync(path.join(snap, "module.start"), path.join(dest, `module.start${path.extname(modulePath)}`));
    if (prepPrevious) copyDir(prevDir, path.join(dest, `${prevLabel}-prep`));
  }
  const result = exit === 2 ? "NO_RESULT" : (exit === 0 ? "PASS" : (exit === 3 ? "REFUSED" : "FAIL"));
  fs.writeFileSync(path.join(dest, "blind-run.json"), `${JSON.stringify({ subject: subjectId, pass: label, seat, from, prepPrevious, exit, result, transports: transports.map((f) => path.basename(f)), at: stamp }, null, 2)}\n`);
  console.log(`[blind] ${result} -> ${path.relative(ROOT, dest)}`);
} finally {
  if (!keep) {
    fs.copyFileSync(path.join(snap, "module.live"), modulePath);
    copyDir(path.join(snap, label), passDir);
    if (prepPrevious) copyDir(path.join(snap, prevLabel), prevDir);
    if (fs.existsSync(path.join(snap, "measurements.md"))) fs.copyFileSync(path.join(snap, "measurements.md"), measurements);
    console.log(`[blind] restored live module: ${same(modulePath, path.join(snap, "module.live")) ? "byte-identical" : "MISMATCH"}`);
  } else {
    console.log("[blind] --keep: the seat's module stays live");
  }
}
process.exitCode = exit;
