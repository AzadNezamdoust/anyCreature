// Dump the concept-view projection the gold judge uses (registered.mjs + the current gold model's frame knobs
// frameScale / frameX / frameY) as an affine map author-frame metres -> concept px: px = M p + o (orthographic).
//   node scripts/hs/dump_concept_cam.mjs --subject <s>[,<s2>...]
// Writes out/blender-hs/<s>/concept_cam.json. Read-only use of the repo scripts. The frame knobs come from
// out/ref/gold/<s>/model.mjs KNOBS (identity when there is no gold model); `target` = the concept the registration
// was fitted to (subject.json paths.target).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { ROOT, loadSubject } from "../subject.mjs";
import { frameOf, framed, turnFn } from "../registered.mjs";
import { conceptRegistration } from "../v7/conceptreg.mjs";   // WF v10: = registered.mjs registration for a vehicle; the fixed-isometric fit for a direct class (weapon)

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const i = argv.indexOf("--subject");
if (i < 0 || !argv[i + 1]) { console.error("usage: node dump_concept_cam.mjs --subject <s>[,<s2>...]"); process.exit(2); }
for (const subject of argv[i + 1].split(",").filter(Boolean)) {
  const S = loadSubject(subject);
  const goldModel = path.join(ROOT, "out", "ref", "gold", subject, "model.mjs");
  let knobs = null;
  if (fs.existsSync(goldModel)) knobs = (await import(pathToFileURL(goldModel).href)).KNOBS ?? null;
  const frame = frameOf(knobs);
  const reg = framed(conceptRegistration(subject), frame);
  const turn = turnFn(reg.turnDeg);
  const P = (p) => reg.toTarget(turn(p));
  const o = P([0, 0, 0]);
  const M = [[1, 0, 0], [0, 1, 0], [0, 0, 1]].map((e) => { const q = P(e); return [q[0] - o[0], q[1] - o[1]]; });
  const out = { turnDeg: reg.turnDeg, s: reg.s, o, Mx: M.map((c) => c[0]), My: M.map((c) => c[1]), basis: reg.basis, w: reg.targetW, h: reg.targetH,
    subject, frame, target: path.relative(ROOT, path.resolve(ROOT, S.paths.target)).replace(/\\/g, "/") };
  const dir = path.resolve(HERE, "..", "..", "out", "blender-hs", subject);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "concept_cam.json"), JSON.stringify(out, null, 1));
  console.log(`[concept] ${subject}: turn ${reg.turnDeg} deg · s ${reg.s.toFixed(3)} · frame ${JSON.stringify(frame)} · target ${out.target}`);
}
