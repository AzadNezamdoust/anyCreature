// node --test scripts/v7/imagegen.test.mjs — the pure parts of imagegen.mjs: the two instructions, the agents' output
// parsers and the retry classification (no CLI is run).
import test from "node:test";
import assert from "node:assert/strict";

import { classifyCall, geminiInstruction, gptInstruction, parseAgyStream, parseAgyTranscript, parseCodexHeader, promptMatch } from "./imagegen.mjs";

const PROMPT = "One image: a test.\nSecond line.";

test("the Gemini instruction: one generate_image call, the refs in order, the prompt verbatim, no file browsing", () => {
  const t = geminiInstruction({ refs: ["C:\\t\\ref-1.png", "C:\\t\\ref-2.png"], prompt: PROMPT, outDir: "C:\\t\\out", name: "x_sheet", aspect: "16:9" });
  assert.match(t, /^Call the generate_image tool exactly ONCE/);
  assert.match(t, /- ImagePaths: these image files, in this order:\n {2}C:\\t\\ref-1\.png\n {2}C:\\t\\ref-2\.png\n/);
  assert.match(t, /- AspectRatio: 16:9/);
  assert.match(t, /into the folder C:\\t\\out with one copy command, and reply with the full path of that copy and nothing else/);
  assert.match(t, /Do not list, read, view or search any files or folders/);
  assert.ok(t.endsWith(`BEGIN PROMPT\n${PROMPT}\nEND PROMPT`));
  const t0 = geminiInstruction({ refs: [], prompt: PROMPT, outDir: "o", name: "n" });   // text to image (a concept: gold.mjs new)
  assert.match(t0, /- ImagePaths: none \(no reference image/);
  assert.ok(t0.endsWith(`BEGIN PROMPT\n${PROMPT}\nEND PROMPT`));
});

test("the GPT instruction: the attached refs in order, the image shape, the prompt verbatim", () => {
  const t = gptInstruction({ refs: ["C:\\t\\ref-1.png", "C:\\t\\ref-2.png"], prompt: PROMPT, outPng: "C:\\t\\out\\v.png", aspect: "1:1" });
  assert.match(t, /save it as the PNG file C:\\t\\out\\v\.png/);
  assert.match(t, /The 2 attached images are the reference images, in this order: image 1 = ref-1\.png, image 2 = ref-2\.png/);
  assert.match(t, /Image shape: square \(1:1\)\./);
  assert.match(t, new RegExp(`BEGIN PROMPT\\n${PROMPT.replace(/\./g, "\\.")}\\nEND PROMPT\\nReply with the saved path only\\.$`));
  assert.match(gptInstruction({ refs: ["a.png"], prompt: PROMPT, outPng: "o.png", aspect: "16:9" }), /The attached image is the reference image.*\nImage shape: landscape \(16:9\)/);
  assert.match(gptInstruction({ refs: [], prompt: PROMPT, outPng: "o.png", aspect: "4:3" }), /There is no reference image: generate the image from the prompt alone\.\nImage shape: landscape \(4:3\)/);
});

test("agy stream-json: conversation, model, result, tool-step states", () => {
  const lines = [
    { event: "init", conversation_id: "c1", init: { model: "gemini-3.8-flash-high" } },
    { event: "step_update", step_update: { conversation_id: "c1", step_index: 2, state: "ACTIVE", step_type: "tool", tool_name: "generate_image" } },
    { event: "step_update", step_update: { conversation_id: "c1", step_index: 2, state: "DONE", step_type: "tool", tool_name: "generate_image" } },
    { event: "step_update", step_update: { conversation_id: "c1", step_index: 4, state: "ERROR", step_type: "tool", tool_name: "run_command" } },
    { event: "result", result: { conversation_id: "c1", status: "SUCCESS", response: "C:\\t\\out\\x.jpg\n" } },
  ].map((x) => JSON.stringify(x)).join("\n");
  const s = parseAgyStream(`${lines}\nnot json\n`);
  assert.equal(s.conversationId, "c1");
  assert.equal(s.agentModel, "gemini-3.8-flash-high");
  assert.equal(s.status, "SUCCESS");
  assert.deepEqual(s.toolSteps.map((t) => [t.index, t.tool, t.states.join(">")]), [[2, "generate_image", "ACTIVE>DONE"], [4, "run_command", "ERROR"]]);
});

test("agy transcript: tool calls and the generated image's media entry", () => {
  const t = [
    { step_index: 1, tool_calls: [{ name: "generate_image", args: { ImagePaths: ["C:\\t\\ref-1.png"], Prompt: PROMPT } }] },
    { step_index: 2, media: [{ mime_type: "image/jpeg", uri: "file:///C:/brain/c1/x_sheet_1.jpg" }, { mime_type: "text/plain", uri: "file:///C:/n.txt" }] },
  ].map((x) => JSON.stringify(x)).join("\n");
  const r = parseAgyTranscript(t);
  assert.equal(r.toolCalls.length, 1);
  assert.equal(r.toolCalls[0].name, "generate_image");
  assert.equal(r.media.length, 1);
  assert.match(r.media[0].file.replace(/\\/g, "/"), /brain\/c1\/x_sheet_1\.jpg$/);
});

test("codex header", () => {
  const h = parseCodexHeader("OpenAI Codex v0.158.0-alpha.2.1\n--------\nmodel: gpt-6-astra\nreasoning effort: high\nsandbox: workspace-write [workdir]\nsession id: 01a0e3c8\n");
  assert.deepEqual(h, { version: "v0.158.0-alpha.2.1", model: "gpt-6-astra", effort: "high", sandbox: "workspace-write [workdir]", sessionId: "01a0e3c8" });
});

test("retry classification: only a transport failure without an image is retried", () => {
  assert.equal(classifyCall({ images: 1, exitCode: 1, timedOut: true }).ok, true);
  assert.equal(classifyCall({ images: 0, timedOut: true }).failure, "transport");
  assert.equal(classifyCall({ images: 0, exitCode: 1 }).failure, "transport");
  assert.equal(classifyCall({ images: 0, exitCode: null }).failure, "transport");
  assert.equal(classifyCall({ images: 0, exitCode: 0, status: "FAILED" }).failure, "transport");
  assert.equal(classifyCall({ images: 0, exitCode: 0, status: "SUCCESS", toolErrors: 1 }).failure, "transport");
  assert.equal(classifyCall({ images: 0, exitCode: 0, status: "SUCCESS" }).failure, "agent");
  assert.equal(classifyCall({ images: 0, spawnError: "ENOENT" }).failure, "spawn");
});

test("prompt comparison: exact, whitespace-only difference, or different", () => {
  assert.equal(promptMatch(PROMPT, PROMPT), "exact");
  assert.equal(promptMatch("One image: a test.  \r\nSecond line.\n", PROMPT), "whitespace");
  assert.equal(promptMatch("One image: a test.", PROMPT), false);
  assert.equal(promptMatch(undefined, PROMPT), false);
});

test("owner 2026-10-04: gpt is the default generator; gemini is refused without allowGemini", async () => {
  const { DEFAULT_GEN, geminiRefusal, generateImage } = await import("./imagegen.mjs");
  assert.equal(DEFAULT_GEN, "gpt");
  assert.equal(geminiRefusal("gpt"), null);
  assert.equal(geminiRefusal("gemini", true), null);
  assert.match(geminiRefusal("gemini"), /refused: owner ruling 2026-10-04 "stop trying to use gemini"/);
  await assert.rejects(generateImage({ gen: "gemini", prompt: "x", out: "x.png" }), /--gen gemini is refused/);
});
