// Dump the turnaround registration (px <-> metres) the gold judge uses, so Blender renders share its framing.
//   node scripts/hs/dump_frame.mjs --subject <s>[,<s2>...]
// Writes out/blender-hs/<s>/frame.json. Read-only use of the repo scripts (scripts/v6/ortho.mjs loadTurnaround).
// Same fields as the pilot's frame.json, plus `crops` (the gold view sheet's ortho tile windows, judge.mjs cropOf:
// reference foreground box +- 40 px) so run_pass.py can cut the current model's tiles out of model-view.png exactly.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadTurnaround } from "../v6/ortho.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const i = argv.indexOf("--subject");
if (i < 0 || !argv[i + 1]) { console.error("usage: node dump_frame.mjs --subject <s>[,<s2>...]"); process.exit(2); }
for (const subject of argv[i + 1].split(",").filter(Boolean)) {
  const { reg } = await loadTurnaround(subject);
  const out = { subject, s: reg.s, names: reg.names, views: {}, crops: {} };
  for (const v of reg.names) {
    const r = reg.views[v];
    out.views[v] = { ox: r.ox, oy: r.oy, kr: r.kr ?? 1, ku: r.ku ?? 1, w: r.img.w, h: r.img.h, spec: r.spec };
    const { box, img } = r;   // = scripts/v6/judge.mjs cropOf(reg, v)
    out.crops[v] = { x0: Math.max(0, box.x0 - 40), x1: Math.min(img.w, box.x1 + 40), y0: Math.max(0, box.y0 - 40), y1: Math.min(img.h, box.y1 + 40) };
  }
  const dir = path.resolve(HERE, "..", "..", "out", "blender-hs", subject);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "frame.json"), JSON.stringify(out, null, 1));
  console.log(`[frame] ${subject}: s ${reg.s.toFixed(3)} px/m · views ${reg.names.join(" ")} -> ${path.relative(process.cwd(), path.join(dir, "frame.json"))}`);
}
