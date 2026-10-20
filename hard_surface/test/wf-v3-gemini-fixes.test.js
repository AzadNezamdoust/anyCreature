// WF-V3 blind Gemini pickup P1 fixes: the syntax pre-check on text-mode replies,
// and the dot-aware "Layout keys this pass must satisfy:" parser.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { runSeat as fakeSeat } from "../scripts/seats/fake.mjs";
import {
  applySeatChecked, moduleSyntaxError, withContractFail, itemLayoutKeys, gateTokens, resolveTokens, ROOT,
} from "../scripts/pass.mjs";

const SMOKE = path.join(ROOT, "test", "fixtures", "kernel", "smoke.mjs");
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "llmm-gemini-"));
const TEXT = { dry: false, seatMode: "text" };

function replyFile(dir, name, moduleText) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, ["```js", moduleText, "```", "CHANGE: test"].join("\n"));
  return file;
}

test("moduleSyntaxError: null on a module that parses, line/col + message on one that does not", () => {
  assert.equal(moduleSyntaxError(fs.readFileSync(SMOKE, "utf8")), null);
  assert.equal(moduleSyntaxError("export function f() {\n  return g(1, 2;\n}\n"), "line 2 col 15: SyntaxError: missing ) after argument list");
});

test("syntax pre-check: an unparseable fence gets ONE syntax-only follow-up; a parseable follow-up is applied", async () => {
  const dir = tmp();
  const modulePath = path.join(dir, "module.mjs");
  fs.writeFileSync(modulePath, "// previous module\n");
  const good = fs.readFileSync(SMOKE, "utf8");
  const bad = good.replace("export function build() {", "export function build( {");
  const first = await fakeSeat({ mode: "text", env: { LLMM_FAKE_REPLY: replyFile(dir, "bad.md", bad) } });
  const prompts = [];
  const retry = async (prompt) => {
    prompts.push(prompt);
    return fakeSeat({ mode: "text", env: { LLMM_FAKE_REPLY: replyFile(dir, "good.md", good) } });
  };
  const out = await applySeatChecked(first, TEXT, modulePath, { retry, tag: "P1" });
  assert.equal(out.syntaxRetries, 1);
  assert.equal(out.contractText, null);
  assert.equal(prompts.length, 1);
  assert.match(prompts[0], /^Your module does not parse: line \d+ col \d+: SyntaxError: .* — return the same module with only that fixed/);
  assert.ok(prompts[0].includes("export function build( {"), "the follow-up carries the seat's own module");
  assert.equal(fs.readFileSync(modulePath, "utf8").trim(), good.trim());
});

test("syntax pre-check: still unparseable after the follow-up keeps the previous module live and records SEAT_SYNTAX", async () => {
  const dir = tmp();
  const modulePath = path.join(dir, "module.mjs");
  fs.writeFileSync(modulePath, "// previous module\n");
  const bad = "export const meta = {;\n";
  const reply = replyFile(dir, "bad.md", bad);
  const first = await fakeSeat({ mode: "text", env: { LLMM_FAKE_REPLY: reply } });
  let calls = 0;
  const out = await applySeatChecked(first, TEXT, modulePath, {
    retry: async () => { calls += 1; return fakeSeat({ mode: "text", env: { LLMM_FAKE_REPLY: reply } }); },
  });
  assert.equal(calls, 1, "exactly one follow-up");
  assert.equal(out.syntaxRetries, 1);
  assert.equal(fs.readFileSync(modulePath, "utf8"), "// previous module\n");
  assert.match(out.contractText, /^FAIL: SEAT_SYNTAX/);
  const failed = withContractFail({ pass: true, report: { pass: true, violations: [], text: "PASS" } }, out.contractText);
  assert.equal(failed.pass, false);
  assert.equal(failed.report.violations[0].v, "SEAT_SYNTAX");
});

test("syntax pre-check: a parseable first reply is applied with no follow-up", async () => {
  const dir = tmp();
  const modulePath = path.join(dir, "module.mjs");
  const first = await fakeSeat({ mode: "text", env: { LLMM_FAKE_MODULE: SMOKE } });
  const out = await applySeatChecked(first, TEXT, modulePath, { retry: async () => assert.fail("no follow-up expected") });
  assert.deepEqual({ ...out, followUp: null }, { contractText: null, syntaxRetries: 0, followUp: null });
  assert.equal(fs.readFileSync(modulePath, "utf8").trim(), fs.readFileSync(SMOKE, "utf8").trim());
});

test("itemLayoutKeys is dot-aware: facade_brick P1 lists its 25 keys", () => {
  const passes = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects", "facade_brick", "passes.json"), "utf8"));
  const keys = itemLayoutKeys(passes.find((p) => p.id === "P1").item);
  assert.equal(keys.length, 25, keys.join(", "));
  assert.deepEqual(keys.slice(0, 3), ["window.w", "window.h", "window.centreX"]);
  assert.equal(keys[24], "face.aspect");
  assert.ok(keys.every((k) => /^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)+$/.test(k)), keys.join(", "));
});

test("{GROOVE_DEPTH_MAX} resolves from KERNEL_LIMIT_DEFAULTS in the vehicle rules and the pickup P1 item", () => {
  const tokens = gateTokens({ styleFloorKey: "vehicle" });
  assert.equal(tokens.GROOVE_DEPTH_MAX, 0.02);
  const md = resolveTokens(fs.readFileSync(path.join(ROOT, "classes", "vehicle.md"), "utf8"), tokens);
  assert.match(md, /cut at most 0\.02 m into ONE face/);
  const p1 = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects", "pickup", "passes.json"), "utf8")).find((p) => p.id === "P1");
  // WF-BLIND-R2 C12: the ungated door line left the item; the token now bounds the gated grille slots.
  // WF-R3 R3-B: the grille (and its slot depth <= GROOVE_DEPTH_MAX) is K.assemble.grille's; the item calls it.
  assert.match(resolveTokens(p1.item, tokens), /the grille with its slots between them \(K\.assemble\.grille\)/);
});
