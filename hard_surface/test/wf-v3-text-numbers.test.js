import test from "node:test";
import assert from "node:assert/strict";
import { assemblePrompt } from "../scripts/pass.mjs";

// WF-V3 ruling (Opus 5, 2026-09-13): a text-mode seat cannot read files, so the
// layout numbers the item cites must be inside the prompt. The first live text
// P0 failed without them (Astra refused to invent massing.depthOverW / crown.height).

test("text-mode prompt carries the layout numbers the item cites", () => {
  const text = assemblePrompt({
    options: { seatMode: "text", label: "P0", n: 0 },
    item: { item: "Layout keys this pass must satisfy: massing.depthOverW, crown.height." },
    moduleText: "", readme: "", previousReview: null, repairReport: null,
  });
  assert.match(text, /# MEASURED NUMBERS/);
  assert.match(text, /- massing\.depthOverW: 0\.8\d+ x W \(tol \+-/);
  assert.match(text, /- crown\.height: 0\.0\d+ H \(tol \+-/);
});

test("agent-mode prompt does not inline the numbers", () => {
  const text = assemblePrompt({
    options: { seatMode: "agent", label: "P0", n: 0 },
    item: { item: "massing.depthOverW" }, moduleText: "", readme: "", previousReview: null, repairReport: null,
  });
  assert.doesNotMatch(text, /# MEASURED NUMBERS/);
});

// WF-V3 (Opus 5, 2026-09-13): the building v3 proof failed V10 by 4 triangles because
// the seat was never told what the current module already spends.
test("prompt shows the triangle budget left when one is known", () => {
  const text = assemblePrompt({
    options: { seatMode: "text", label: "P2", n: 2 },
    item: { item: "Add the fire escape." }, moduleText: "", readme: "", previousReview: null, repairReport: null,
    budget: { used: 928, cap: 3000 },
  });
  assert.match(text, /# TRIANGLE BUDGET/);
  assert.match(text, /uses 928 of 3000 triangles; .* remaining 2072\./);
});

test("no budget block when the budget is unknown", () => {
  const text = assemblePrompt({
    options: { seatMode: "text", label: "P2", n: 2 },
    item: { item: "Add the fire escape." }, moduleText: "", readme: "", previousReview: null, repairReport: null,
  });
  assert.doesNotMatch(text, /# TRIANGLE BUDGET/);
});
