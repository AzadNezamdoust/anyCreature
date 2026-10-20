// Compile + validate timing, in node, on the real subject spec.
//
// PLAN.md 5 targets <= 300 ms for compile + V0..V7 + V10 at 8k triangles. M1 is
// the milestone that can finally measure it: `build+V0` is the M0 floor and
// `build+all` is the number the budget was written about.
//
//   node scripts/bench.mjs [runs]
import { performance } from "node:perf_hooks";

import { compile } from "../src/compile/build.js";
import { validateV0 } from "../src/validate/v0.js";
import { validate, buildPrims } from "../src/validate/index.js";
import { loadSpec, TENEMENT, EXAMPLES } from "../test/fixtures.mjs";

const RUNS = Number.parseInt(process.argv[2] ?? "20", 10);

function median(samples) {
  const sorted = [...samples].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function bench(label, file) {
  const spec = loadSpec(file);

  // One warm-up: the first compile pays for three.js class initialisation and
  // would otherwise be reported as the compiler's cost.
  validateV0(spec);
  const warm = compile(spec);
  validate(spec, warm.solved, { geometry: warm.geometry, prims: buildPrims(spec) });

  const v0Only = [];
  const full = [];
  let report = null;
  let solved = null;

  for (let i = 0; i < RUNS; i += 1) {
    let start = performance.now();
    validateV0(spec);
    const built = compile(spec);
    v0Only.push(performance.now() - start);

    start = performance.now();
    const again = compile(spec);
    report = validate(spec, again.solved, { geometry: again.geometry, prims: buildPrims(spec) });
    full.push(performance.now() - start);

    solved = built.solved;
    if (!report.pass) throw new Error(`${file} does not validate: ${report.text}`);
  }

  console.log(
    `${label.padEnd(16)} tris ${String(solved.triangles).padStart(5)}  parts ${String(solved.parts.length).padStart(3)}` +
    `  build+V0 ${median(v0Only).toFixed(2)} ms` +
    `  build+V0-V7+V10 ${median(full).toFixed(2)} ms  (min ${Math.min(...full).toFixed(2)} max ${Math.max(...full).toFixed(2)}, n=${RUNS})`,
  );
}

console.time("bench total");
bench("tenement_block", TENEMENT);
for (const file of EXAMPLES) bench(file.split("/").pop().replace(".json", ""), file);
console.timeEnd("bench total");
