// M3 — the generation pipeline, driven by `--runner fake`.
//
// What is under test is the LOOP, not the model: lister -> A -> B (broken once) -> REPAIR ->
// C -> full chain PASS, the cache making a re-run cost zero calls, and the hand BASELINE
// staying byte-identical throughout.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";

import { generate, parseCodexTranscript, extractJson } from "../scripts/gen.mjs";
import { validateSpec } from "../src/validate/index.js";
import { ROOT, TENEMENT } from "./fixtures.mjs";
import fakeRunner, { calls } from "./fixtures/fake-runner.mjs";

const BASELINE = path.join(ROOT, TENEMENT);
const sha = (file) => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), "llmmodeling-gen-"));
const cacheDir = path.join(scratch, "cache");

const baselineBefore = sha(BASELINE);
const firstCallCount = calls.length;

const first = await generate({ subject: "tenement_block", runner: "fake", fake: fakeRunner, cacheDir, outDir: path.join(scratch, "run1") });
const afterFirst = calls.length;

const second = await generate({ subject: "tenement_block", runner: "fake", fake: fakeRunner, cacheDir, outDir: path.join(scratch, "run2") });
const afterSecond = calls.length;

test("the fake run reaches a full-chain PASS", () => {
  assert.equal(first.run.pass, true, first.report.text);
  assert.equal(first.report.violations.length, 0);
  assert.equal(first.run.tiers.map((t) => t.tier).join(""), "ABC");
  for (const tier of first.run.tiers) assert.equal(tier.pass, true, `${tier.tier}: ${tier.text}`);
});

test("tier B is caught floating and fixed by the REPAIR seat, not by auto-repair", () => {
  const tierB = first.run.tiers.find((t) => t.tier === "B");
  assert.equal(tierB.reprompts, 1);
  assert.equal(tierB.autoRepairs.length, 0);   // V3 is never auto-repaired (02:T3)

  const builderB = first.run.calls.find((c) => c.seat === "builder-b");
  assert.equal(builderB.pass, false);
  assert.ok(builderB.violations.some((v) => v.startsWith("V3")), `expected a V3 orphan, got ${builderB.violations.join(", ")}`);

  const repairCall = first.run.calls.find((c) => c.seat === "repair");
  assert.equal(repairCall.tier, "B");
  assert.equal(repairCall.model, "claude-opus-5");
  assert.equal(repairCall.pass, true);
});

test("every seat runs on its pinned model, lister on Fable", () => {
  const lister = first.run.calls.find((c) => c.seat === "lister");
  assert.equal(lister.model, "claude-fable-5-1");
  for (const call of first.run.calls.filter((c) => c.seat !== "lister")) assert.equal(call.model, "claude-opus-5");
});

test("the first run spends five seat calls, all uncached", () => {
  assert.equal(afterFirst - firstCallCount, 5);
  assert.equal(first.run.calls.length, 5);
  assert.equal(first.run.calls.filter((c) => c.cached).length, 0);
});

test("a re-run is a pure cache hit: zero runner calls, same spec", () => {
  assert.equal(afterSecond - afterFirst, 0);
  assert.equal(second.run.calls.length, 5);
  assert.equal(second.run.calls.filter((c) => c.cached).length, 5);
  assert.equal(second.run.totals.cached, 5);
  assert.equal(second.run.pass, true);
  assert.deepEqual(second.spec, first.spec);
});

test("the artefacts land and the written spec re-validates clean", () => {
  for (const file of ["spec.json", "solved.json", "report.json", "run.json"]) {
    assert.ok(fs.existsSync(path.join(first.outDir, file)), `${file} missing`);
  }
  const written = JSON.parse(fs.readFileSync(path.join(first.outDir, "spec.json"), "utf8"));
  assert.equal(validateSpec(written).pass, true);
  const run = JSON.parse(fs.readFileSync(path.join(first.outDir, "run.json"), "utf8"));
  assert.ok(run.deviations.some((d) => d.startsWith("MEASURE")), "the skipped MEASURE pass must be recorded as a deviation");
});

test("the hand BASELINE is never written", () => {
  assert.equal(sha(BASELINE), baselineBefore);
  assert.ok(!first.outDir.startsWith(path.dirname(BASELINE)));
});

test("gen refuses an --out inside subjects/tenement_block", async () => {
  await assert.rejects(
    () => generate({ subject: "tenement_block", runner: "fake", fake: fakeRunner, cacheDir, outDir: "subjects/tenement_block" }),
    /frozen/,
  );
  assert.equal(sha(BASELINE), baselineBefore);
});

test.after(() => fs.rmSync(scratch, { recursive: true, force: true }));

// --- the codex runner's transcript parser -------------------------------------------------
//
// Canned from a live `codex exec --ignore-user-config --skip-git-repo-check -s read-only
// -C . -m gpt-6-astra -c model_reasoning_effort="high" "Follow the instructions below."`
// (v0.154.0-alpha.6.2), captured with the streams merged as they arrive on a TTY. No live
// codex call happens in this suite.
const CODEX_TRANSCRIPT = [
  "Reading additional input from stdin...",
  "OpenAI Codex v0.154.0-alpha.6.2",
  "--------",
  "workdir: D:\\Git\\anyCreature\\hard_surface",
  "model: gpt-6-astra",
  "provider: openai",
  "approval: never",
  "sandbox: read-only",
  "reasoning effort: high",
  "reasoning summaries: none",
  "session id: 01a09544-1b5f-7812-9052-b27ac7b3611d",
  "--------",
  "user",
  "Follow the instructions below.",
  "",
  "<stdin>",
  "Reply with exactly this JSON and nothing else: {\"ok\":true,\"n\":3}",
  "</stdin>",
  "codex",
  "{\"ok\":true,\"n\":3}",
  "tokens used",
  "3,242",
  "{\"ok\":true,\"n\":3}",
].join("\n");

test("the codex runner parses the answer and the token count out of a real transcript", () => {
  const parsed = parseCodexTranscript(CODEX_TRANSCRIPT);
  assert.equal(parsed.model, "gpt-6-astra");
  assert.equal(parsed.effort, "high");
  assert.equal(parsed.sessionId, "01a09544-1b5f-7812-9052-b27ac7b3611d");
  assert.equal(parsed.answer, '{"ok":true,"n":3}');
  assert.equal(parsed.tokensUsed, 3242);
  assert.deepEqual(extractJson(parsed.answer), { ok: true, n: 3 });

  // piped runs split the streams: the transcript lands on stderr, the bare answer on stdout
  const piped = parseCodexTranscript(CODEX_TRANSCRIPT, '{"ok":true,"n":3}\n');
  assert.equal(piped.answer, '{"ok":true,"n":3}');
  assert.equal(piped.tokensUsed, 3242);
});

test("a transcript whose header is not Astra at high effort is fatal, never a fallback", () => {
  const lowEffort = CODEX_TRANSCRIPT.replace("reasoning effort: high", "reasoning effort: medium");
  assert.throws(() => parseCodexTranscript(lowEffort), /reasoning effort="medium".*required "high"/s);

  const noEffort = CODEX_TRANSCRIPT.split("\n").filter((l) => !l.startsWith("reasoning effort:")).join("\n");
  assert.throws(() => parseCodexTranscript(noEffort), /reasoning effort="null"/);

  const otherModel = CODEX_TRANSCRIPT.replace("model: gpt-6-astra", "model: gpt-5-codex");
  assert.throws(() => parseCodexTranscript(otherModel), /model="gpt-5-codex".*required "gpt-6-astra"/s);
});
