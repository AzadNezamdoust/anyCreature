// Write a self-contained brief for ONE Haiku seat that explores variants of ONE part and ranks them with part_search.mjs.
//
//   node scripts/hs/search/make_batch.mjs --subject <s> --part <role|object name> --n <k> --out <dir> [--hint "<text>"]
//
// Writes <dir>/BATCH.md and <dir>/crops/<view>_{source,baseline,pair}.png (the part's crop in the source turnaround and in the
// baseline render). Renders the baseline once if it is not cached (out/search/<s>/_baseline/<sha>/). Only writes under <dir>
// and out/search/.
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";
import { loadCandidate, scorePart } from "../score/part_score.mjs";
import {
  ROOT, VIEWS, TIE, rel, ensureBaseline, readJson, topBlocks, resolvePart, roleBBox, turnaroundFile, cropBuf, finishCalls,
} from "./lib.mjs";

const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
const subject = arg("--subject"), part = arg("--part"), n = Number(arg("--n") || 6), out = arg("--out") && path.resolve(arg("--out")), hint = arg("--hint");
if (!subject || !part || !out) { console.error('usage: node scripts/hs/search/make_batch.mjs --subject <s> --part <role|object> --n <k> --out <dir> [--hint "<text>"]'); process.exit(2); }
fs.mkdirSync(path.join(out, "crops"), { recursive: true });

const base = await ensureBaseline(subject);
const meta = readJson(path.join(base.dir, "pass0_ids.json"));
const P = resolvePart(base.src, part, meta.parts), role = P.role;
const blocks = topBlocks(base.src), byName = new Map();
for (const b of blocks) for (const k of b.name.split(",")) byName.set(k, b);
const idents = (t) => [...new Set(t.replace(/#.*$/gm, "").match(/[A-Za-z_]\w*/g) || [])];

// ---- the part's functions + what they reference in the same file (assignments fully, helper defs fully, 2 levels) ----
const fnBlocks = P.fns.map((f) => byName.get(f)).filter(Boolean);
if (!fnBlocks.length) throw new Error(`no function found that builds role ${role}`);
const own = new Set(fnBlocks.map((b) => b.name)), refs = new Map();
let frontier = fnBlocks;
for (let depth = 0; depth < 2; depth++) {
  const next = [];
  for (const b of frontier) for (const id of idents(b.text)) {
    const r = byName.get(id);
    if (!r || own.has(r.name) || refs.has(r.name) || r.name === "build" || r.kind === "other") continue;
    refs.set(r.name, r); next.push(r);
  }
  frontier = next;
}
const refText = [...refs.values()].sort((a, b) => a.start - b.start).map((b) => b.text).join("\n\n");

// ---- hs helper signatures used ----
const hsSrc = fs.readFileSync(path.join(ROOT, "scripts", "hs", "hs.py"), "utf8").replace(/\r\n/g, "\n");
const hsDefs = new Map();
for (const m of hsSrc.matchAll(/^def (\w+)\(([^)]*)\):\n(?:    """([^\n]*))?/gm)) hsDefs.set(m[1], `def ${m[1]}(${m[2].replace(/\s*\n\s*/g, " ")})${m[3] ? `  # ${m[3].replace(/"""$/, "")}` : ""}`);
const used = new Set();
for (const t of [...fnBlocks, ...refs.values()].map((b) => b.text)) for (const id of idents(t)) if (hsDefs.has(id)) used.add(id);
const hsSigs = [...used].sort().map((k) => hsDefs.get(k));

// ---- safe ranges (verbatim from BUILD-DIRECT.md) ----
const bd = fs.readFileSync(path.join(ROOT, "out", "blender-hs", "BUILD-DIRECT.md"), "utf8").replace(/\r\n/g, "\n");
const i0 = bd.indexOf("## Helper safe ranges");
// BUILD-DIRECT tells a NEW build to opt in with hs.begin(..., guards=True), which lives in build() (outside this edit
// contract). part_search renders BASELINE and every candidate with HS_GUARDS=1 instead, so the seat must not touch build().
const GUARDS_NOTE = "**Guards are already on for you**: part_search renders BASELINE and every candidate with the environment " +
  "variable `HS_GUARDS=1` (hs.py forces the helper guards on), so do NOT edit `build()` or `hs.begin(...)`. Guards: parts welded at " +
  "`finish`, welded cutters, cutters carry the target's material slots, `mirror_x` heals a part touching x = 0, `bevel_mod` width and " +
  "`box(chamfer=)` clamped to 0.45 x the thinnest dimension, `tyre_section` chamfers scale with hw. Each clamp or out-of-range call " +
  "is listed as `GUARD_WARN` in `ranking.md` (and in `<variants>/vNN/run.log`): fix what it names; a clamp is a rescue, not a design value.";
function fixGuardText(text) {
  return text.replace(/\*\*Turn the hs\.py guards on\*\*[\s\S]*?a clamp is a rescue, not a design value\./, GUARDS_NOTE);
}
const safe = fixGuardText(bd.slice(i0, bd.indexOf("\n## ", i0 + 5)).trim());
const rig = bd.slice(bd.indexOf("## Riggable rules"), bd.indexOf("\n## Report")).trim();

// ---- crops + baseline score ----
const B = await loadCandidate(subject, base.dir);
const [bs] = await scorePart(subject, [B], role);
const crops = [];
for (const v of VIEWS) {
  const box = roleBBox(base.dir, role)[v];
  if (!box) continue;
  const sh = B.views[v].shift;
  const s = await cropBuf(turnaroundFile(subject, v), box, sh, 14, 640, 1, 8);
  const b = await cropBuf(path.join(base.dir, `pass0_${v}.png`), box, [0, 0], 14, 640, 1, 8);
  const f = (k) => path.join(out, "crops", `${v}_${k}.png`);
  await sharp(s.buf).toFile(f("source")); await sharp(b.buf).toFile(f("baseline"));
  await sharp({ create: { width: s.w + b.w + 8, height: Math.max(s.h, b.h), channels: 3, background: "#ffffff" } })
    .composite([{ input: s.buf, left: 0, top: 0 }, { input: b.buf, left: s.w + 8, top: 0 }]).png().toFile(f("pair"));
  const vs = bs.views[v];
  crops.push({ v, src: rel(f("source")), base: rel(f("baseline")), pair: rel(f("pair")), box, px: vs.px, score: vs.score, sig: vs });
}
const r3 = (x) => (typeof x === "number" ? x.toFixed(3) : "-");
const P_ = (p) => rel(p).replace(/\\/g, "/");
const buildRel = `out/blender-hs/${subject}/build.py`, vrel = rel(out);

const md = `# BATCH: ${subject} / ${part}${part !== role ? ` (role \`${role}\`)` : ""} — ${n} candidate variants

You are ONE Haiku seat. Work dir \`${ROOT.replace(/\\/g, "/")}\` (PowerShell or Bash). Write ONLY under \`${vrel}/\`. Never edit anything under \`out/blender-hs/\`,
\`subjects/\`, \`scripts/\`. No commits, no downloads. Do not judge your own work beyond what the ranking says.

## Goal
Write ${n} different versions of the part's function so that its renders look more like the SOURCE crops. A script renders each
one and ranks it with a per-part likeness score; you only write the candidates, run the command and report.

## The part
Role \`${role}\` = objects ${P.objects.map((o) => `\`${o}\``).join(", ")}, built by ${P.fns.map((f) => `\`${f}()\``).join(", ")} in \`${buildRel}\` (the BASELINE).
Baseline part score ${r3(bs.score)} (edge ${r3(bs.edge)}, open ${r3(bs.open)}, sil ${r3(bs.sil)}, ssim ${r3(bs.ssim)}, tone ${r3(bs.tone)}); a candidate must beat it by >= ${TIE} to count (|delta| < ${TIE} is a tie and ties keep the baseline).

### Source crops (look at these first; each \`*_pair.png\` = SOURCE | BASELINE at the same scale)
${crops.map((c) => `- ${c.v}: ${c.pair}  (source ${c.src}, baseline ${c.base}); baseline part score in this view ${r3(c.score)}, region ${c.px} px`).join("\n")}

Compare source and baseline in every view: list (to yourself) what differs (tone of recesses, openings, count of grooves, proportions,
chamfers, colours). Every candidate is a hypothesis about one such difference. The score is image-only: it sees silhouette, edges, openings
(see-through holes and dark recesses), structure and tone inside the part's region, so geometry and materials that change those pixels matter.
${hint ? `\nHint from the owner: ${hint}\n` : ""}
## Current source of the part (from \`${buildRel}\`)
\`\`\`python
${fnBlocks.map((b) => b.text).join("\n\n\n")}
\`\`\`

Module-level definitions it uses (same file; change them only through your candidate's copy of the file, and only if the part alone uses them):
\`\`\`python
${refText || "(none)"}
\`\`\`

\`hs.py\` helpers it calls (see \`scripts/hs/README.md\`):
\`\`\`
${hsSigs.join("\n") || "(none)"}
\`\`\`

## Edit contract (exact)
For k = 1..${n}:
1. Copy \`${buildRel}\` to \`${vrel}/v<kk>.py\` (kk = 01..${String(n).padStart(2, "0")}). Copy the whole file; do not rewrite it.
2. In that copy change ONLY ${P.fns.map((f) => `\`${f}()\``).join(" / ")}. A new palette entry or a constant that only this part uses is allowed; nothing else.
3. Put one comment line right under the def: \`# v<kk>: <the hypothesis, one line>\`.
4. Keep every object NAME and every \`ob["part"]\` role exactly as in the baseline (same \`finish(bm, "<name>", [...], "<role>")\` strings), the same number of objects, and the riggable clearances (below). Do not add or remove objects.
5. Other parts must stay pixel-identical: do not touch their functions, the shared constants they use, \`build()\`, or the frame (metres, muzzle +z, left flank +x, y up).
6. The ${n} candidates must differ in KIND (shape / depth / count / material / chamfer / proportion), not just a number nudged by 2 %.
7. Stay inside the safe ranges below; the render rejects a candidate whose topology is not clean or whose tris exceed the budget.

${safe}

${rig}

## Run
\`\`\`powershell
node scripts/hs/search/part_search.mjs --subject ${subject} --part ${part} --variants ${vrel}
\`\`\`
${n} renders at up to 4 Blender processes at a time, about 100 s each (the baseline is cached). If it prints an error, fix the named candidate and run again (unchanged, already rendered candidates are skipped).
Outputs in \`${vrel}/\`: \`ranking.md\`, \`ranking.json\`, \`top.png\` (rows = views, columns = SOURCE | BASELINE | best 3). Open \`top.png\` once.

## Report format (exactly this, nothing else)
1. One line per candidate, in file order: \`v<kk>: PASS|FAIL|UNSURE  part <delta>  whole <delta>  gate <ok|REJECT: reason>  — <hypothesis>\`
   (PASS = gate ok and part delta >= +${TIE}; FAIL = rejected or part delta <= -${TIE}; UNSURE = |delta| < ${TIE}). Copy the numbers from \`ranking.md\`.
2. The ranking table from \`ranking.md\` pasted verbatim (all rows).
3. One line: \`top.png: best candidate looks closer to SOURCE than BASELINE: y|n|unsure — <what you see, 12 words max>\`.
4. Any error text verbatim. No other commentary.
`;
fs.writeFileSync(path.join(out, "BATCH.md"), md);
console.log(`wrote ${rel(path.join(out, "BATCH.md"))} (${md.length} chars), ${crops.length} view crops; role ${role}, functions ${P.fns.join(", ")}, baseline part score ${r3(bs.score)}`);
