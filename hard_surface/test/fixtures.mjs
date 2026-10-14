// Shared spec loading for the node test suite and scripts/bench.mjs.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function loadSpec(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relativePath), "utf8"));
}

export const TENEMENT = "subjects/tenement_block/spec.json";
export const EXAMPLES = ["dsl/examples/crate.json", "dsl/examples/bench.json", "dsl/examples/cart.json"];
