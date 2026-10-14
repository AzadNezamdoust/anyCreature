import fs from "node:fs";
import path from "node:path";
import { defineConfig } from "vite";

// Relative base so a built page can be served from any path, including a
// BlindLoop worktree served by `vite preview` on an orchestrator-chosen port.
//
// `subjects/` and `refs/` are data, not modules: the page loads them with
// fetch() so a spec edit is a file edit, not a rebuild. Vite's dev server
// already serves any file under the project root, but `vite build` would leave
// them out of `dist/`, and `vite preview` — the path capture-candidate.mjs
// uses — would then 404. This plugin copies both trees verbatim into `dist/`
// so preview has no network dependency (PLAN 4, 08:G8).
function copyDataTrees(dirs) {
  return {
    name: "llmmodeling-copy-data-trees",
    apply: "build",
    closeBundle() {
      const root = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
      for (const dir of dirs) {
        const from = path.join(root, dir);
        if (!fs.existsSync(from)) continue;
        fs.cpSync(from, path.join(root, "dist", dir), { recursive: true });
      }
    },
  };
}

export default defineConfig({
  base: "./",
  server: { host: "127.0.0.1", port: 4210, strictPort: true },
  preview: { host: "127.0.0.1", port: 4210, strictPort: true },
  build: { outDir: "dist", target: "es2022" },
  // V2: manifold-3d ships an emscripten ESM that locates manifold.wasm through
  // `new URL(..., import.meta.url)`. Pre-bundling rewrites that URL and the dev
  // server then 404s the wasm, so the package is excluded from optimizeDeps —
  // the documented workaround (V2-TEST-PLAN 3).
  optimizeDeps: { exclude: ["manifold-3d"] },
  assetsInclude: ["**/*.wasm"],
  plugins: [copyDataTrees(["subjects", "refs", "dsl", "classes"])],   // WORKFLOW-V3 §7.5: class priors are data too
});
