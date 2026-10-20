#!/usr/bin/env node
// Does the boolean kernel fit the edit-to-preview budget? (V2-TEST-PLAN 5:
// build + validate <= 1 s at <= 3000 tris; the v1 line was 300 ms at 8k.)
//
//   node scripts/bench-kernel.mjs
//
// Three numbers: (a) the smoke module's build, (b) twenty SEQUENTIAL cuts -
// the shape an author writes by accident - and (c) the same twenty tools
// unioned first and cut once, which is the documented fix if (b) is too slow.
import { performance } from "node:perf_hooks";

import * as K from "../src/kernel/index.mjs";
import { partsToGeometry } from "../src/kernel/toThree.mjs";
import { build, meta } from "../subjects/facade_brick/facade.mjs";

const TOOLS = 20;
const T = 0.35;

function ms(started) {
  return (performance.now() - started).toFixed(1);
}

/** Twenty 30 cm pockets cut clean through the wall, well inside every edge. */
function tools() {
  return K.repeat(TOOLS, 0.35, (i, offset) => K.box([0.3, 0.3, T + 0.02]).at([-3.5 + offset, 5, 0]));
}

await (async function main() {
  const initStarted = performance.now();
  await K.init();
  const initMs = ms(initStarted);

  K.resetCounters();
  const buildStarted = performance.now();
  const parts = build();
  const buildMs = ms(buildStarted);
  const buildBooleans = K.counters.booleans;

  const geoStarted = performance.now();
  const compiled = partsToGeometry(parts, meta.palette, meta.seed);
  const geoMs = ms(geoStarted);

  const wall = parts[0].solid;

  const seqStarted = performance.now();
  let sequential = wall;
  for (const tool of tools()) sequential = K.cut(sequential, tool);
  const seqTris = sequential.triCount();
  const seqMs = ms(seqStarted);

  const unionStarted = performance.now();
  const oneCut = K.cut(wall, K.union(tools()));
  const oneTris = oneCut.triCount();
  const unionMs = ms(unionStarted);

  console.log(`init            ${initMs} ms (wasm load)`);
  console.log(`build smoke     ${buildMs} ms, ${parts.length} parts, ${compiled.solved.triangles} tris, ${buildBooleans} booleans`);
  console.log(`toThree+merge   ${geoMs} ms (solid -> painted, merged geometry)`);
  console.log(`20 cuts (seq)   ${seqMs} ms, ${seqTris} tris`);
  console.log(`20 cuts (union) ${unionMs} ms, ${oneTris} tris`);
  console.log(`edit->preview   ${(Number(buildMs) + Number(geoMs)).toFixed(1)} ms build+geometry (budget 1000 ms)`);
})();
