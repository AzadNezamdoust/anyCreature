import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
import test from "node:test";
import assert from "node:assert/strict";
import { runSeat, buildInstruction, AGY_DEFAULT_MODEL } from "../scripts/seats/agy.mjs";
import { SEATS } from "../scripts/pass.mjs";

// No agy spawn in the suite: these pin the contract and the no-network paths only.

test("agy is a registered seat and defaults to Gemini 3.8 Flash High", () => {
  assert.ok(SEATS.includes("agy"));
  assert.equal(AGY_DEFAULT_MODEL, "gemini-3.8-flash-high");
});

test("agy seat refuses agent mode as a contract failure, without spawning", async () => {
  const out = await runSeat({ prompt: "x", mode: "agent", env: { PATH: "" } });
  assert.equal(out.failureClass, "contract");
  assert.equal(out.artifact, null);
});

test("instruction points at prompt.md and the images, and forbids file edits", () => {
  const text = buildInstruction("C:/tmp/seat", ["image1.png", "image2.png"]);
  assert.match(text, /prompt\.md in C:\/tmp\/seat/);
  assert.match(text, /image1\.png is the TARGET/);
  assert.match(text, /Do not create, edit, move or delete any file/);
});

test("agy seat is blind: new project per call, never continue/resume", () => {
  const src = require("node:fs").readFileSync(new URL("../scripts/seats/agy.mjs", import.meta.url), "utf8");
  assert.match(src, /"--new-project"/);
  assert.doesNotMatch(src, /"--continue"|"-c"|"--conversation"/);
});
