#!/usr/bin/env node
// Bounded GPT Astra audit seat for the workflow-improvement loop.
// usage: node scripts/astra-audit.mjs <round> [--timeout-min N]
// Spawns `codex exec` (gpt-6-astra, reasoning high, workspace-write, no MCP) with the brief on
// stdin and the stills attached, writes out/wf-loop/r<R>/astra-audit.md, asserts the header.
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseCodexTranscript } from "./gen.mjs";
import { codexBin } from "./codex-bin.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CODEX_BIN = process.env.CODEX_BIN
  || codexBin();
const round = process.argv[2] ?? "1";
const tIdx = process.argv.indexOf("--timeout-min");
const timeoutMs = (tIdx === -1 ? 12 : Number(process.argv[tIdx + 1])) * 60 * 1000;
const outDir = path.join(ROOT, "out", "wf-loop", `r${round}`);
mkdirSync(outDir, { recursive: true });

const brief = readFileSync(path.join(ROOT, "research", round === "1" ? "WF-LOOP-BRIEF.md" : `WF-LOOP-BRIEF-R${round}.md`), "utf8");
const images = ["refs/tenement-iso.png"];
for (const p of (round === "1" ? [0,1,2,3,4] : round === "2" ? [4] : [2])) {
  for (const v of ["target", "threeQuarter"]) {
    const rel = `out/facade/P${p}/${v}.png`;
    if (existsSync(path.join(ROOT, rel))) images.push(rel);
  }
}
const prompt = [
  brief.replace(/round R/g, `round ${round}`),
  "",
  "---",
  "Image 1 is the TARGET (style and model, not a trace). The remaining images are the run stills in order:",
  "P0 target, P0 threeQuarter, P1 target, P1 threeQuarter, ... P4 threeQuarter.",
  "You have shell access in workspace-write for READING only — do not write or edit any file.",
  "Read out/facade/P4/facade.mjs, src/kernel/README.md, subjects/facade_brick/passes.json,",
  "src/validate/kernel-chain.mjs (skim) before answering. Keep tool use short: the whole audit",
  `must finish inside ${timeoutMs / 60000} minutes. Your final message IS the audit; nothing else.`,
].join("\n");
writeFileSync(path.join(outDir, "astra-audit.prompt.md"), prompt);

const args = [
  "exec", "-c", "mcp_servers={}", "--skip-git-repo-check", "-s", "workspace-write", "-C", ROOT,
  "-m", "gpt-6-astra", "-c", 'model_reasoning_effort="high"',
];
for (const img of images) args.push("-i", img);
args.push("-o", path.join(outDir, "astra-audit.md"), "Follow the instructions below.");

const t0 = Date.now();
const res = spawnSync(CODEX_BIN, args, { input: prompt, encoding: "utf8", timeout: timeoutMs, maxBuffer: 64 << 20, cwd: ROOT });
const secs = ((Date.now() - t0) / 1000).toFixed(1);
writeFileSync(path.join(outDir, "astra-audit.transcript.txt"), (res.stderr ?? "") + "\n---STDOUT---\n" + (res.stdout ?? ""));
if (res.error) { console.error(`codex: ${res.error.message} after ${secs}s`); process.exit(1); }
const parsed = parseCodexTranscript(res.stderr ?? "", res.stdout);
if (!existsSync(path.join(outDir, "astra-audit.md")) || !readFileSync(path.join(outDir, "astra-audit.md"), "utf8").trim()) {
  writeFileSync(path.join(outDir, "astra-audit.md"), parsed.answer);
}
console.log(`astra audit r${round}: ${secs}s, ${parsed.tokensUsed} tokens, model ${parsed.model}/${parsed.effort}, exit ${res.status}`);
