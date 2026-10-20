// WORKFLOW-V3 items 5-7, Job D2 — seat contract, MISSING KEY consumer, prompt from class files.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  parseMissingKeys, parseReply, mergeMissingKeys, refusedKeys, recordMissingKeys, seedBacklog, readBacklog,
} from "../scripts/missing-keys.mjs";
import { runSeat as fakeSeat } from "../scripts/seats/fake.mjs";
import { runSeat as relaySeat } from "../scripts/seats/relay.mjs";
import { classifyCodexRun, rolloutUsage } from "../scripts/seats/codex.mjs";
import {
  parseArgs, seatOutcome, SeatTransportError, applySeat, withContractFail, CONTRACT_FAIL_TEXT,
  gateTokens, resolveTokens, authorReadme, assemblePrompt, rulesBlock, TEXT_CONTRACT, unifiedDiff, sumUsage, S, ROOT,
} from "../scripts/pass.mjs";
import { buildRow, tokensCell } from "../scripts/measure.mjs";

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "llmm-d2-"));
const SMOKE = path.join(ROOT, "test", "fixtures", "kernel", "smoke.mjs");

test("parseMissingKeys reads run 4's inline CHANGE clause and a MISSING KEY: line", () => {
  const run4 = "CHANGE: Added four framed windows; MISSING KEY storefront.w, storefront.centreX, ac.position.";
  assert.deepEqual(parseMissingKeys(run4), ["storefront.w", "storefront.centreX", "ac.position"]);
  assert.deepEqual(parseMissingKeys("CHANGE: x\nMISSING KEY: a.b, `c.d`\n"), ["a.b", "c.d"]);
  assert.deepEqual(parseMissingKeys("CHANGE: x; MISSING KEY none"), []);
  assert.deepEqual(parseMissingKeys("```js\n// MISSING KEY: in.code\n```\nCHANGE: y"), []);
});

test("parseReply extracts the largest js fence, CHANGE and MISSING KEY", () => {
  const reply = "```js\nconst a = 1;\n```\n```js\nexport const meta = {};\nexport function build() { return []; }\n```\nCHANGE: rebuilt\nMISSING KEY: k.one";
  const r = parseReply(reply);
  assert.match(r.artifact, /export function build/);
  assert.equal(r.change, "rebuilt");
  assert.deepEqual(r.missingKeys, ["k.one"]);
  assert.equal(parseReply("CHANGE: no fence").artifact, null);
});

test("backlog merge counts repeats, refuse lists only this pass's keys asked twice and absent from layout", () => {
  let b = mergeMissingKeys({}, ["a.x", "b.y"], "P1", "t0");
  b = mergeMissingKeys(b, ["a.x"], "P1", "t1");
  assert.deepEqual(b["a.x"], { count: 2, passes: ["P1"], firstSeen: "t0" });
  assert.equal(b["b.y"].count, 1);
  assert.deepEqual(refusedKeys(b, {}, "P1"), ["a.x"]);
  assert.deepEqual(refusedKeys(b, { "a.x": { value: 1 } }, "P1"), []);
  assert.deepEqual(refusedKeys(b, {}, "P2"), []);
});

test("recordMissingKeys writes the file; seedBacklog reads P*/last.md", () => {
  const dir = tmp();
  const file = path.join(dir, "missing-keys.json");
  recordMissingKeys(file, "P0", "CHANGE: x\nMISSING KEY: w.t", "t0");
  recordMissingKeys(file, "P0", "CHANGE: y; MISSING KEY w.t.", "t1");
  assert.equal(readBacklog(file)["w.t"].count, 2);
  fs.mkdirSync(path.join(dir, "run", "P0"), { recursive: true });
  fs.writeFileSync(path.join(dir, "run", "P0", "last.md"), "CHANGE: a; MISSING KEY roof.thickness, crown.thickness.");
  const seeded = seedBacklog(path.join(dir, "run"));
  assert.deepEqual(Object.keys(seeded), ["roof.thickness", "crown.thickness"]);
  assert.deepEqual(seeded["roof.thickness"].passes, ["P0"]);
});

// Seeds from the ARCHIVED run-4 replies, not the live backlog file: every real
// pass appends to subjects/<s>/missing-keys.json, so a count taken off it drifts.
test("the facade backlog is seeded from run 4 (24 keys, all count 1)", () => {
  const backlog = seedBacklog(path.join(path.dirname(S().paths.module), "..", "..", "out", "facade", "run4"));
  assert.equal(Object.keys(backlog).length, 24);
  assert.ok(Object.values(backlog).every((e) => e.count >= 1));
  assert.deepEqual(backlog["ladder.drop.length"].passes, ["P2"]);
});

test("fake seat, text mode: the module comes back fenced; no fence is a contract failure", async () => {
  const ok = await fakeSeat({ mode: "text", env: { LLMM_FAKE_MODULE: SMOKE, LLMM_FAKE_MISSING: "a.b" } });
  assert.equal(ok.failureClass, null);
  assert.equal(ok.artifact.trim(), fs.readFileSync(SMOKE, "utf8").trim());
  assert.deepEqual(ok.missingKeys, ["a.b"]);
  const dir = tmp();
  const reply = path.join(dir, "reply.md");
  fs.writeFileSync(reply, "I changed the roof.\nCHANGE: roof");
  const bad = await fakeSeat({ mode: "text", env: { LLMM_FAKE_REPLY: reply } });
  assert.equal(bad.failureClass, "contract");
  assert.equal(seatOutcome(bad), "contract");
});

test("transport and timeout are exit-2 SeatTransportErrors, never a counted seat", async () => {
  const drop = await fakeSeat({ mode: "text", env: { LLMM_FAKE_FAILURE: "transport" } });
  assert.throws(() => seatOutcome(drop, "P0"), SeatTransportError);
  assert.throws(() => seatOutcome({ failureClass: "timeout", seconds: 900 }), SeatTransportError);
  assert.equal(seatOutcome({ failureClass: null }), "ok");
});

test("codex classifier: the run2 'Unable to verify model access' drop is transport", () => {
  const transcript = "ERROR: Reconnecting... 5/5\nERROR: stream disconnected before completion: Unable to verify model access right now. Please retry.\ntokens used\n11,144\n";
  assert.equal(classifyCodexRun({ status: 2, transcript, answer: "" }), "transport");
  assert.equal(classifyCodexRun({ status: 0, transcript: "codex\nCHANGE: x", answer: "CHANGE: x" }), null);
  assert.equal(classifyCodexRun({ status: null, error: { code: "ETIMEDOUT" }, transcript: "" }), "timeout");
});

test("codex rolloutUsage reads the input/cached/output/reasoning split", () => {
  const home = tmp();
  const day = path.join(home, "sessions", "2026", "09", "13");
  fs.mkdirSync(day, { recursive: true });
  const line = { type: "event_msg", payload: { type: "token_count", info: { total_token_usage: { input_tokens: 100, cached_input_tokens: 60, output_tokens: 7, reasoning_output_tokens: 3, total_tokens: 107 } } } };
  fs.writeFileSync(path.join(day, "rollout-x-abc-123.jsonl"), `{"type":"session_meta"}\n${JSON.stringify(line)}\n`);
  assert.deepEqual(rolloutUsage("abc-123", home), { input: 100, cached: 60, output: 7, reasoning: 3 });
  assert.deepEqual(rolloutUsage("missing", home), {});
});

test("relay seat writes pending prompt + images and returns the done answer", async () => {
  const ws = tmp();
  const img = path.join(ws, "t.png");
  fs.writeFileSync(img, "png");
  const pending = relaySeat({ prompt: "BUILD", images: [img], workspace: ws, timeoutMs: 5000, tag: "P0", mode: "text", pollMs: 10 });
  const promptFile = path.join(ws, "relay", "pending", "P0.prompt.md");
  for (let i = 0; i < 100 && !fs.existsSync(promptFile); i += 1) await new Promise((r) => setTimeout(r, 10));
  assert.match(fs.readFileSync(promptFile, "utf8"), /BUILD/);
  assert.ok(fs.existsSync(path.join(ws, "relay", "pending", "P0.image1.png")));
  fs.writeFileSync(path.join(ws, "relay", "done", "P0.answer.md"), "```js\nexport const meta={};\n```\nCHANGE: m\nMISSING KEY: q.r");
  const r = await pending;
  assert.equal(r.failureClass, null);
  assert.match(r.artifact, /meta/);
  assert.deepEqual(r.missingKeys, ["q.r"]);
  const late = await relaySeat({ prompt: "x", workspace: ws, timeoutMs: 30, tag: "P9", pollMs: 10 });
  assert.equal(late.failureClass, "timeout");
});

test("parseArgs: default seat opus (GPT seats are test-only, owner 2026-09-26) in text mode; --subject is consumed", () => {
  const o = parseArgs(["2", "--subject", "facade_brick", "--gate-only", "--no-repair"]);
  assert.equal(o.seat, "opus");
  assert.equal(o.seatMode, "text");
  assert.equal(o.label, "P2");
  assert.equal(parseArgs(["P0", "--seat", "fake", "--seat-mode", "agent"]).seatMode, "agent");
  assert.throws(() => parseArgs(["0", "--seat", "gpt"]), /--seat/);
});

test("prompt tokens come from the gate config; unknown tokens throw", () => {
  const tokens = gateTokens(S().cls);
  assert.equal(tokens.MIN_FEAT, 0.06);
  // V5-8 R2: the facade's measured ruleOverrides.step_rise_max (0.3 m: the target's ~0.271 m riser) rides the gate
  // config, so the prompt quotes the SUBJECT's effective band; limits.json (0.14–0.2) is unchanged.
  assert.equal(resolveTokens("bars {MIN_FEAT} m, rise {STEP_RISE} m", tokens), "bars 0.06 m, rise 0.14–0.3 m");
  assert.throws(() => resolveTokens("{NOT_A_LIMIT}", tokens), /unknown prompt token/);
  const passes = JSON.parse(fs.readFileSync(S().paths.passes, "utf8"));
  for (const p of passes) assert.doesNotMatch(resolveTokens(p.item, tokens), /\{[A-Z_]+\}/);
});

test("text-mode prompt: README + class rules, ends with the contract, never asks to run check-module", () => {
  const tokens = gateTokens(S().cls);
  const readme = authorReadme(tokens);
  assert.match(readme, /# Kernel API/);
  assert.match(readme, /# Class rules — building/);
  assert.doesNotMatch(readme, /declare every contact/);
  const options = { label: "P1", n: 1, dry: false, seatMode: "text" };
  const prompt = assemblePrompt({ options, item: { item: "do it" }, moduleText: "MODULE_BODY", readme, previousReview: "| 3 | reads as the target | x | FAIL | n |\n| 1 | orientation | y | PASS | |" });
  assert.ok(prompt.trimEnd().endsWith(TEXT_CONTRACT));
  assert.doesNotMatch(prompt, /Run `node scripts\/check-module/);
  assert.match(prompt, /reads as the target/);
  assert.doesNotMatch(prompt, /\| orientation \|/);
  assert.match(rulesBlock(false, "agent"), /Run `node scripts\/check-module/);
});

test("text-mode repair prompt carries the failing rows and a diff, the module once", () => {
  const before = "export const a = 1;\nexport const b = 2;\n";
  const after = "export const a = 1;\nexport const b = 3;\n";
  const diff = unifiedDiff(before, after, "m.mjs");
  assert.match(diff, /-export const b = 2;/);
  assert.match(diff, /\+export const b = 3;/);
  const options = { label: "P0", n: 0, dry: false, seatMode: "text" };
  const prompt = assemblePrompt({ options, item: { item: "i" }, moduleText: after, readme: "R", repairReport: "FAIL: V6 x", diff });
  assert.equal(prompt.split("export const b = 3;").length - 1, 2);   // once in the module, once in the diff
  assert.match(prompt, /FAIL: V6 x/);
  assert.match(prompt, /```diff/);
});

test("applySeat writes the fence in text mode and turns a missing fence into a SEAT_CONTRACT FAIL row", () => {
  const dir = tmp();
  const mod = path.join(dir, "m.mjs");
  fs.writeFileSync(mod, "old");
  assert.equal(applySeat({ failureClass: null, artifact: "new\n" }, { seatMode: "text" }, mod), null);
  assert.equal(fs.readFileSync(mod, "utf8"), "new\n");
  const text = applySeat({ failureClass: "contract", artifact: null }, { seatMode: "text" }, mod);
  assert.equal(text, CONTRACT_FAIL_TEXT);
  assert.equal(fs.readFileSync(mod, "utf8"), "new\n");
  const failed = withContractFail({ pass: true, report: { pass: true, violations: [], text: "PASS" } }, text);
  assert.equal(failed.pass, false);
  assert.equal(failed.report.violations[0].v, "SEAT_CONTRACT");
  assert.equal(applySeat({ failureClass: null, artifact: "x" }, { seatMode: "agent" }, mod), null);
  assert.equal(fs.readFileSync(mod, "utf8"), "new\n");
});

test("usage split: summed across seats, shown in the tokens cell only when measured", () => {
  const u = sumUsage({ total: 10, input: 8, cached: 4, output: 2 }, { total: 5 });
  assert.deepEqual(u, { total: 15, input: 8, cached: 4, output: 2 });
  assert.equal(tokensCell({ tokens: 42 }), "42");
  assert.equal(tokensCell({ tokens: 15, usage: u }), "15 (in 8 · cached 4 · out 2)");
  const row = buildRow("P0", { tokens: 15, usage: { total: 15, input: 9, cached: 1, output: 5, reasoning: 2 } }, null);
  assert.match(row, /\| 15 \(in 9 · cached 1 · out 5 · reason 2\) \|/);
});
