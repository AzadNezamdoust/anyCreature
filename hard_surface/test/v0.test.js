import test from "node:test";
import assert from "node:assert/strict";

import { validateV0 } from "../src/validate/v0.js";
import { loadSpec, TENEMENT, EXAMPLES } from "./fixtures.mjs";

// Every worked example ships in-context to the model. A broken example teaches
// an invalid program (08:E1), so they are gated here, not merely eyeballed.
for (const file of [TENEMENT, ...EXAMPLES]) {
  test(`V0 passes: ${file}`, () => {
    const result = validateV0(loadSpec(file));
    assert.deepEqual(result.violations, [], `${file} must be V0-clean`);
    assert.equal(result.pass, true);
  });
}

const PALETTE = { a: "#112233" };

/** Each of these must fail with EXACTLY one violation — a validator that fires
 *  three times on one defect cannot tell the REPAIR seat what to move. */
const BROKEN = {
  "forward reference (cycle in file order)": {
    schema: "pg/1", subject: "cycle", seed: 1, palette: PALETTE,
    parts: [
      { id: "a", prim: "box", dims: [1, 1, 1], zone: "a",
        attach: { to: "b", face: "+X", uv: [0.5, 0.5], contact: "flush" } },
      { id: "b", prim: "box", dims: [1, 1, 1], zone: "a", ground: true },
    ],
  },
  "missing ground": {
    schema: "pg/1", subject: "unrooted", seed: 1, palette: PALETTE,
    parts: [{ id: "a", prim: "box", dims: [1, 1, 1], zone: "a" }],
  },
  "unknown prim": {
    schema: "pg/1", subject: "badprim", seed: 1, palette: PALETTE,
    parts: [{ id: "a", prim: "sphere", dims: [1, 1, 1], zone: "a", ground: true }],
  },
};

for (const [label, spec] of Object.entries(BROKEN)) {
  test(`V0 fails once: ${label}`, () => {
    const result = validateV0(spec);
    assert.equal(result.pass, false);
    assert.equal(result.violations.length, 1, JSON.stringify(result.violations, null, 2));
    assert.equal(result.violations[0].v, "V0");
    assert.ok(result.violations[0].hint.length > 0, "a violation must carry a hint");
  });
}
