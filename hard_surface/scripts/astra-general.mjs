#!/usr/bin/env node
// Bounded GPT Astra seat for the generalisation analysis (research/GENERAL-WORKFLOW-BRIEF.md).
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseCodexTranscript } from "./gen.mjs";
import { codexBin } from "./codex-bin.mjs";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CODEX_BIN = process.env.CODEX_BIN || codexBin();
const tIdx = process.argv.indexOf("--timeout-min");
const timeoutMs = (tIdx === -1 ? 15 : Number(process.argv[tIdx + 1])) * 60 * 1000;
const outDir = path.join(ROOT, "out", "wf-loop", "general");
mkdirSync(outDir, { recursive: true });
const brief = readFileSync(path.join(ROOT, "research", "GENERAL-WORKFLOW-BRIEF.md"), "utf8");
const prompt = [brief, "", "---",
  "Image 1 is the TARGET; image 2 is out/facade/run4/compare-final.png (best result, front faces at equal width on top).",
  "Shell access is workspace-write for READING only — do not write or edit any file. Read the listed files before",
  `answering; keep tool use short so the whole analysis finishes inside ${timeoutMs / 60000} minutes. Your final message IS the analysis.`,
].join("\n");
writeFileSync(path.join(outDir, "astra.prompt.md"), prompt);
const args = ["exec", "-c", "mcp_servers={}", "--skip-git-repo-check", "-s", "workspace-write", "-C", ROOT,
  "-m", "gpt-6-astra", "-c", 'model_reasoning_effort="high"',
  "-i", "refs/tenement-iso.png", "-i", "out/facade/run4/compare-final.png",
  "-o", path.join(outDir, "astra-general.md"), "Follow the instructions below."];
const t0 = Date.now();
const res = spawnSync(CODEX_BIN, args, { input: prompt, encoding: "utf8", timeout: timeoutMs, maxBuffer: 64 << 20, cwd: ROOT });
const secs = ((Date.now() - t0) / 1000).toFixed(1);
writeFileSync(path.join(outDir, "astra-general.transcript.txt"), (res.stderr ?? "") + "\n---STDOUT---\n" + (res.stdout ?? ""));
if (res.error) { console.error(`codex: ${res.error.message} after ${secs}s`); process.exit(1); }
const parsed = parseCodexTranscript(res.stderr ?? "", res.stdout);
const outFile = path.join(outDir, "astra-general.md");
if (!existsSync(outFile) || !readFileSync(outFile, "utf8").trim()) writeFileSync(outFile, parsed.answer);
console.log(`astra general: ${secs}s, ${parsed.tokensUsed} tokens, ${parsed.model}/${parsed.effort}, exit ${res.status}`);
