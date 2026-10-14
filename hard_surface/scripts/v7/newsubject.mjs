// WF v8 — `gold.mjs new`: a brand-new subject from one description paragraph (research/v7/SKILL-REVIEW-fable.md: the
// hand-built setup chain as ONE entry point). It composes the concept prompt (the description + the hidden-face rule of
// the 2026-09-27 RUNBOOK + scripts/make-target.mjs STYLE verbatim), generates refs/<s>.png through scripts/v7/imagegen.mjs
// (text to image; padded white to a square, 1024 px lanczos3 — the refs/forklift.README.md construction), writes
// refs/<s>.README.md with the `## Full prompt` fenced block the auditor brief reads, subjects/<s>/subject.json,
// turnaround/views.json (vehicle axes, the W anchor, families proposed from the concept's colour clusters, spanOpen 2),
// turnaround/facts.json (from the description), prior.json (soft: the stated size), out/ref/gold/<s>/state.json (phase
// setup) + LEDGER.md, and returns the numbered remaining chain (scripts/v7/README.md "New subject, once"). --dry skips
// the generation (no GPT / Gemini call) and writes into a temp root. GPT / Gemini only generate the image.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import sharp from "sharp";

import { STYLE } from "../make-target.mjs";
import { DEFAULT_STYLE, styleOf } from "./styles.mjs";
import { newState, renderLedger, serializeState } from "./goldlib.mjs";

/** The RUNBOOK prompt rule (2026-09-27): a feature on a face the concept view cannot show is written as hidden. */
export const HIDDEN_FACE = "Anything on a face this view cannot show (the rear face, the far flank, the underside) faces away and is not visible in this view: never move it onto a visible face; the visible faces are drawn exactly as described.";
export const CLASSES = Object.freeze(["vehicle", "weapon"]);
/** WF v10: classes whose subjects are `pipeline: "direct"` (no gold state, no JS-kernel rounds; classes/<class>.json `pipeline`). */
export const DIRECT_CLASSES = Object.freeze(["weapon"]);
/** The fixed concept camera of a direct class = the isometric sentence every style text starts with (conceptreg.mjs FIXED_ISO). */
export const FIXED_ISO = Object.freeze({ theta_deg: 30, phi_deg: 45 });
export const VIEWS_VEHICLE = Object.freeze({
  side: { file: "side.png", right: [0, 0, -1], up: [0, 1, 0] },
  front: { file: "front.png", right: [1, 0, 0], up: [0, 1, 0] },
  rear: { file: "rear.png", right: [-1, 0, 0], up: [0, 1, 0] },
  top: { file: "top.png", right: [0, 0, -1], up: [-1, 0, 0] },
});
const r2 = (x) => Math.round(x * 100) / 100;
const hex = (c) => `#${c.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("")}`;
const today = () => new Date().toISOString().slice(0, 10);
const oneSpace = (t) => String(t).trim().replace(/\s+/g, " ");

/**
 * The concept prompt: description (one paragraph) + the hidden-face rule + the style's STYLE block, verbatim
 * (scripts/v7/styles.json; the default cartoon = the frozen make-target.mjs STYLE).
 */
export const conceptPrompt = (desc, style = DEFAULT_STYLE) => `${oneSpace(desc)} ${HIDDEN_FACE} ${style === DEFAULT_STYLE ? STYLE : styleOf(style).text}`;

/**
 * The stated real size of a description: "<n> m long", "<n> m wide", "<n> m tall | high" (metres / m). -> {L, W, H,
 * sentences: the sentences stating them, rest: the description without them}; a missing dimension is null.
 */
export function parseSize(desc) {
  const text = oneSpace(desc);
  const num = (re) => { const m = re.exec(text); return m ? Number(m[1]) : null; };
  const u = "(?:m|metres?|meters?)";
  const L = num(new RegExp(`(\\d+(?:\\.\\d+)?)\\s*${u}\\s+long`, "i"));
  const W = num(new RegExp(`(\\d+(?:\\.\\d+)?)\\s*${u}\\s+wide`, "i"));
  const H = num(new RegExp(`(\\d+(?:\\.\\d+)?)\\s*${u}\\s+(?:tall|high)`, "i"));
  const parts = text.split(/(?<=[.!?;])\s+(?=[A-Z])/);   // a sentence ends at . ! ? ; before a capital (never inside 8.5)
  const isSize = (s) => new RegExp(`\\d\\s*${u}\\s+(long|wide|tall|high)`, "i").test(s);
  return { L, W, H, sentences: parts.filter(isSize).map((s) => s.trim()), rest: parts.filter((s) => !isSize(s)).map((s) => s.trim()).join(" ") };
}

/** facts.json of a new subject (research/v7/TURNAROUND-PROMPT.md "facts.json"): shapes from the stated size; sides symmetric until edited. */
export function factsFrom({ subject, noun, desc, style = DEFAULT_STYLE }) {
  const z = parseSize(desc);
  const { L, W, H } = z;
  const f = (x) => r2(x).toFixed(2);
  return {
    subject, noun,
    // the concept's style (scripts/v7/styles.json): turnaround.mjs prompts with it; absent = cartoon
    ...(style !== DEFAULT_STYLE ? { style } : {}),
    sources: `gold.mjs new ${today()}: description + proportions = the concept prompt's paragraph (refs/${subject}.README.md Full prompt; its size sentence as the proportions); shape / dims = that stated size (estimates: re-measure dims on the installed set, hull.mjs); sides / asymmetric / faces: edit from the concept (hidden faces, parts on one flank)`,
    description: z.rest,
    proportions: `${z.sentences.join(" ")} (length : width : height = ${f(L / W)} : 1 : ${f(H / W)})`,
    sides: `the ${noun} is symmetric left to right.`,
    shape: {
      side: `in this view the ${noun} is ${f(L / H)} times as long as it is tall`,
      front: `in this view its width is ${f(W / H)} of its height`,
      rear: `in this view its width is ${f(W / H)} of its height`,
      top: `in this view it is ${f(L / W)} times as long as it is wide`,
    },
    faces: {},
    asymmetric: [],
    dims: { L, W, H, _: "ESTIMATE from the concept prompt's stated size (gold.mjs new); after turnaround.mjs install re-measure: L / W = the body-family span (views.json families.body), H = the foreground bbox height (hull.mjs prints the registered dims)" },
  };
}

/**
 * views.json families proposed from the concept's foreground colour clusters (turnaround.mjs colourClusters): clusters
 * >= `minShare` of the foreground, at most `max`; the most common not-dark cluster is `body`, the darkest `dark`, the
 * rest f2, f3 ... — names and the body choice are a PROPOSAL the orchestrator renames before turnaround gen.
 */
export async function proposeFamilies(png, { fgMax = 235, minShare = 0.02, max = 8 } = {}) {
  const { colourClusters } = await import("./turnaround.mjs");
  const { data, info } = await sharp(png).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const n = info.width * info.height;
  const fam = new Uint8Array(n);
  for (let i = 0, j = 0; i < n; i += 1, j += info.channels) fam[i] = Math.min(data[j], data[j + 1], data[j + 2]) < fgMax ? 1 : 0;
  const { clusters } = colourClusters(data, info.channels, fam, { minShare });
  const top = clusters.slice(0, max);
  const lum = (c) => 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2];
  const bodyI = top.findIndex((c) => lum(c.rgb) >= 60);
  const darkI = top.reduce((b, c, i) => (lum(c.rgb) < 60 && (b < 0 || lum(c.rgb) < lum(top[b].rgb)) ? i : b), -1);
  const table = {};
  let k = 2;
  top.forEach((c, i) => { table[i === bodyI ? "body" : i === darkI ? "dark" : `f${k++}`] = hex(c.rgb); });
  const shares = Object.fromEntries(Object.keys(table).map((name, i) => [name, r2(top[i].share * 100)]));
  return { table, shares };
}

export function viewsTemplate({ dims, families = null, klass = "vehicle" }) {
  if (DIRECT_CLASSES.includes(klass)) {
    // WF v10 weapon: the scale anchor is the stated LENGTH (side + top measure it over ~800 px; the width is a few cm) and
    // ONE family holds every flat colour, so the registration's L / W spans are the whole foreground (stock, barrel).
    const colours = families ? Object.values(families.table) : ["#808080"];
    return {
      _comment: `WF-V6 per-subject turnaround contract (scripts/v6/README.md), written by gold.mjs new --class ${klass} ${today()} (WF v10, pipeline direct). Author frame: muzzle +z, the weapon's left flank +x, y up, y = 0 at its lowest point, x and z centred (classes/${klass}.md). Views: side = the left flank with the muzzle to the image left, front = muzzle on, rear = butt on, top = plan with the muzzle to the image left.`,
      views: VIEWS_VEHICLE,
      anchor: { dim: "L", m: dims.L },
      families: {
        body: "body",
        spanOpen: 2,
        enclosedFg: false,
        _enclosedFg: "off: a trigger-guard opening / skeleton stock is background",
        table: { body: colours },
        _table: `ONE family (classes/${klass}.json _anchor_comment): body = every foreground colour cluster >= 2 % of the concept${families ? ` (share % ${JSON.stringify(families.shares)})` : " (PLACEHOLDER: no concept yet)"}; the registration's spans are then the whole foreground. Add a colour here when a view's part classifies as "other" (> 120 RGB from every listed colour).`,
      },
    };
  }
  return {
    _comment: `WF-V6 per-subject turnaround contract (scripts/v6/README.md), written by gold.mjs new ${today()}. Vehicle author frame: nose +z, near flank +x, y up, ground y = 0, x and z centred. No regions.json: families.table = flat colours of the concept; families.body names the body family.`,
    views: VIEWS_VEHICLE,
    anchor: { dim: "W", m: dims.W },
    families: {
      body: "body",
      spanOpen: 2,
      enclosedFg: false,
      _enclosedFg: "off until the setup audit decides (see-through parts stay background)",
      table: families?.table ?? { body: "#808080" },
      _table: families ? `PROPOSAL (gold.mjs new: the concept's foreground colour clusters >= 2 %, share % ${JSON.stringify(families.shares)}): rename each family after its parts, check families.body = the body colour, merge clusters of one part (measure.mjs sample --image <concept> x,y,w,h) before turnaround.mjs gen` : "PLACEHOLDER (no concept yet): sample the concept's colours (measure.mjs sample --image <concept> x,y,w,h) before turnaround.mjs gen",
    },
  };
}

export function priorTemplate({ klass, dims }) {
  const band = (x) => [r2(x * 0.8), r2(x * 1.25)];
  if (DIRECT_CLASSES.includes(klass)) {
    return {
      _comment: `PRIOR CARD, gold.mjs new --class ${klass} ${today()} (WF v10): real = the description's stated size; the L anchor fixes px/m of the turnaround; a direct build is blocked out from these metres (out/blender-hs/BUILD-DIRECT.md).`,
      class: klass,
      real: { source: "the concept prompt's stated size (gold.mjs new)", L: dims.L, W: dims.W, H: dims.H },
      anchor: { dim: "L", m: dims.L, why: "the stated overall length; fixes px/m of the turnaround" },
      stylisation: { _comment: "ESTIMATE from the stated size: re-measure after install (hull.mjs prints the registered dims)", WoverL: Math.round((dims.W / dims.L) * 1e4) / 1e4, HoverL: Math.round((dims.H / dims.L) * 1e4) / 1e4 },
      softRanges: { L: band(dims.L), W: band(dims.W), H: band(dims.H) },
    };
  }
  return {
    _comment: `WF-V6 PRIOR CARD (schema = subjects/school_bus/prior.json), gold.mjs new ${today()}: real = the concept prompt's stated size (soft plausibility only; the turnaround wins); stylisation to re-measure on the installed turnaround at the W anchor (scripts/v6/README.md 'bus card'; wheelDoverH is what scaffold.mjs reads).`,
    class: klass,
    real: { source: "the concept prompt's stated size (gold.mjs new)", L: dims.L, W: dims.W, H: dims.H },
    anchor: { dim: "W", m: dims.W, why: "the stated width; fixes px/m of the turnaround" },
    stylisation: { _comment: "ESTIMATE from the stated size: re-measure after install", LoverW: r2(dims.L / dims.W), HoverW: r2(dims.H / dims.W) },
    softRanges: { L: band(dims.L), W: band(dims.W), H: band(dims.H) },
  };
}

export const subjectTemplate = ({ subject, klass, title, style = DEFAULT_STYLE }) => ({
  id: subject, class: klass, title,
  ...(style !== DEFAULT_STYLE ? { style } : {}),
  // WF v10: no gold rounds — setup -> Blender build -> Fable review + polish -> function (WORKFLOW-V10.md)
  ...(DIRECT_CLASSES.includes(klass) ? { pipeline: "direct" } : {}),
  _comment: `Minimal v6 manifest (gold.mjs new ${today()}): target + solved concept camera; layoutMeasured holds only _frame.quadPx (hull.mjs --write-frame). Colour families come from turnaround/views.json families.table.`,
  paths: { target: `refs/${subject}.png`, camera: `subjects/${subject}/camera.json`, layoutMeasured: `subjects/${subject}/layout.measured.json` },
  outDir: `out/${subject}`,
  missingKeyPolicy: "report",
  ...(DIRECT_CLASSES.includes(klass) ? { ruleOverrides: { tris: { value: 8000, evidence: "WF v10 weapon class budget (owner 2026-10-04: tri budget 8000 each)" } } } : {}),
});

/** subjects/<s>/camera.json of a direct class: the style's fixed isometric (no ground quad to solve; conceptreg.mjs). */
export const fixedCamera = ({ subject, klass }) => ({
  ...FIXED_ISO,
  slopes: null, residual_px: null, vertical_tilt_deg: null,
  source: `refs/${subject}.png`,
  solved: new Date().toISOString(),
  provisional: false,
  method: `fixed style isometric (WF v10, class ${klass}: a handheld object has no ground quad for scripts/solve-camera.mjs; every styles.json text starts with "30 degree elevation, 45 degree azimuth from front-left")`,
});

/** The numbered remaining chain of a direct subject (WORKFLOW-V10.md S1 -> S2). */
export function chainLinesDirect(s) {
  const t = `node scripts/v7/turnaround.mjs`, d = `--dir out/turnaround/${s}`;
  const blender = `& "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" -b --factory-startup --python-exit-code 1 --python`;
  return [
    `1. LOOK at refs/${s}.png: the weapon described, whole, one object, no text / hands (else move refs/${s}.png + refs/${s}.README.md + subjects/${s} + out/concept/${s} aside and run new again)`,
    `2. facts: subjects/${s}/turnaround/facts.json — sides / asymmetric (ejection port, charging handle, selector flank) / faces (what the muzzle-on and butt-on views show); check: ${t} prompt --subject ${s}`,
    `3. provisional frame: node scripts/v7/hull.mjs --subject ${s} --write-frame --from facts`,
    `4. turnaround: ${t} gen --subject ${s} --out out/turnaround/${s} --gen gpt -> LOOK at out/turnaround/${s}/current/*.png -> ${t} status --subject ${s} ${d} -> ${t} repair --subject ${s} ${d} --view <v> --gen gpt (the setup stop rule) -> ${t} install --subject ${s} ${d}`,
    `5. camera + frame: node scripts/v7/solve-camera-hull.mjs --subject ${s}; node scripts/v7/hull.mjs --subject ${s} --write-frame   (the concept camera fitted to the installed views' hull, then the hull fitted to the concept -> subjects/${s}/layout.measured.json _frame.fit / quadPx); read: node scripts/v7/hull.mjs --subject ${s} --aniso`,
    `6. registration for Blender: node scripts/hs/dump_frame.mjs --subject ${s}; node scripts/hs/dump_concept_cam.mjs --subject ${s}`,
    `7. stage + NEXT: node scripts/v7/gold.mjs hs --subject ${s}   (build -> review -> polish -> function -> owner; builder brief out/blender-hs/BUILD-DIRECT.md)`,
    `   pass: ${blender} scripts/hs/run_pass.py -- --subject ${s} --pass N [--final]`,
  ];
}

/** refs/<s>.README.md in the shape of refs/forklift.README.md (the auditor brief reads its `## Full prompt` block). */
export function readmeText({ subject, gen, prompt, raw = null, image = null, prov = null, from = null, style = DEFAULT_STYLE }) {
  const L = [`# TARGET provenance — ${subject}`, "", `- date: ${today()}`];
  if (from) L.push(`- generator: none (gold.mjs new --dry --concept ${from}: an existing image, not generated from this prompt)`);
  else if (gen) L.push(`- generator: ${gen === "gpt" ? "GPT image generation" : "Gemini image generation"} through scripts/v7/imagegen.mjs --gen ${gen} (text to image, no reference; agent ${prov?.agentModel ?? "?"}); GPT / Gemini are used only to generate the image`);
  else L.push("- generator: none yet (gold.mjs new --dry: the prompt only)");
  if (raw) L.push(`- raw output: ${raw.width} x ${raw.height} px, ${raw.bytes} bytes, sha256 ${raw.sha256} (${raw.file})`);
  if (image) L.push(`- image: refs/${subject}.png = the raw output padded with white to a square (centred) and resized to 1024 x 1024 (lanczos3); nothing else changed`, `- bytes: ${image.bytes}`, `- sha256: ${image.sha256}`);
  L.push(style === DEFAULT_STYLE
    ? "- style: the frozen STYLE of scripts/make-target.mjs, after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new)"
    : `- style: ${style} (scripts/v7/styles.json styles.${style}.text), after the description and the hidden-face rule (RUNBOOK 2026-09-27; gold.mjs new --style ${style})`, "", "## Full prompt (image prompt, verbatim)", "", "```", prompt, "```", "");
  return L.join("\n");
}

/** Pad an image with white to a centred square and resize it to `size` px (lanczos3). */
export async function padSquare(src, dst, size = 1024) {
  const m = await sharp(src).metadata();
  const side = Math.max(m.width, m.height);
  const left = Math.floor((side - m.width) / 2), top = Math.floor((side - m.height) / 2);
  const buf = await sharp(src).removeAlpha().extend({ left, right: side - m.width - left, top, bottom: side - m.height - top, background: { r: 255, g: 255, b: 255 } }).png().toBuffer();
  await sharp(buf).resize(size, size, { kernel: "lanczos3" }).png().toFile(dst);
}

/** The numbered remaining chain after `new` (also scripts/v7/README.md "New subject, once"). */
export function chainLines(s) {
  const t = `node scripts/v7/turnaround.mjs`, d = `--dir out/turnaround/${s}`;
  return [
    `1. camera: node scripts/solve-camera.mjs ${s} --image refs/${s}.png   (writes subjects/${s}/camera.json)`,
    `2. families: subjects/${s}/turnaround/views.json families.table is a PROPOSAL — rename each family after its parts, families.body = the body colour (node scripts/v7/measure.mjs sample --image refs/${s}.png x,y,w,h)`,
    `3. facts: subjects/${s}/turnaround/facts.json — add sides / asymmetric / faces (hidden faces) from the concept (research/v7/TURNAROUND-PROMPT.md); check: ${t} prompt --subject ${s}`,
    `4. provisional frame: node scripts/v7/hull.mjs --subject ${s} --write-frame --from facts`,
    `5. turnaround: ${t} gen --subject ${s} --out out/turnaround/${s} → ${t} status --subject ${s} ${d} → ${t} repair --subject ${s} ${d} --view <v> until status meets its targets (the setup stop rule) → ${t} install --subject ${s} ${d}`,
    `6. per-view colours: ${t} families --subject ${s} --apply`,
    `7. frame: node scripts/v7/hull.mjs --subject ${s} --write-frame   (the registered hull → subjects/${s}/layout.measured.json _frame.quadPx)`,
    `8. dims + prior: node scripts/v7/hull.mjs --subject ${s} --aniso prints the registered dims → facts.json dims, prior.json stylisation (LoverW, HoverW, wheelDoverH; scripts/v6/README.md "bus card")`,
    `9. start: node scripts/v7/scaffold.mjs --subject ${s} --shape sedan|box|bus|pickup|machine   (two fit: both with --out out/tmp/${s}-<shape>, keep the better step verdict + agree as out/ref/gold/${s}/start.mjs)`,
    `10. doctor: node scripts/v7/gold.mjs doctor --subject ${s}   (exit 1 = a BLOCK row: read the verdict line)`,
    `11. audit: node scripts/v7/gold.mjs brief --subject ${s} --role auditor → Agent gold-auditor; then the gold-model skill SETUP 3-5 · commit: node scripts/v7/gold.mjs commit --subject ${s}`,
  ];
}

const shaOf = async (f) => (await import("node:crypto")).createHash("sha256").update(fs.readFileSync(f)).digest("hex");

/**
 * Create a new subject under `root`. opts: {root, subject, klass, desc, noun, title, gen, dry, concept (an existing
 * png used instead of generating: padded like a generated one), aspect, generate (injected imagegen generateImage), log}.
 * Refuses when refs/<s>.png or subjects/<s>/subject.json exists, or the description states no L / W / H.
 * -> {files: [root-relative], chain: [lines], prompt}
 */
export async function newSubject(opts) {
  const { root, subject: s, klass = "vehicle", gen = "gpt", dry = false, style = DEFAULT_STYLE, log = () => {} } = opts;
  const styleEntry = styleOf(style);   // throws on an unknown --style
  if (!/^[a-z][a-z0-9_]*$/.test(s ?? "")) throw new Error(`new: --subject ${s}: lower-case letters, digits, _`);
  if (!CLASSES.includes(klass)) throw new Error(`new: --class ${klass}: ${CLASSES.join(" | ")} (a building subject needs its census / layout: scripts/measure-target.mjs)`);
  if (!["gpt", "gemini"].includes(gen)) throw new Error(`new: --gen ${gen}: gpt | gemini`);
  const direct = DIRECT_CLASSES.includes(klass);
  if (!dry && !opts.concept && gen === "gemini" && !opts.allowGemini) throw new Error('new: --gen gemini is refused: owner ruling 2026-10-04 "stop trying to use gemini" — use --gen gpt (the default); --allow-gemini overrides for an explicit owner exception');
  const desc = oneSpace(opts.desc ?? "");
  if (desc.length < 40) throw new Error("new: --desc-file: one paragraph naming the parts, their colours and the real size");
  const size = parseSize(desc);
  const miss = ["L", "W", "H"].filter((k) => !(size[k] > 0));
  if (miss.length) throw new Error(`new: the description states no ${miss.join(" / ")}: add the real size ("About 3.2 m long, 1.2 m wide and 2.2 m tall")`);
  const P = (...p) => path.join(root, ...p);
  const target = P("refs", `${s}.png`);
  if (fs.existsSync(target)) throw new Error(`new: refs/${s}.png exists (a TARGET is frozen): pick another subject id`);
  if (fs.existsSync(P("subjects", s, "subject.json"))) throw new Error(`new: subjects/${s}/subject.json exists`);
  if (fs.existsSync(P("out", "ref", "gold", s, "state.json"))) throw new Error(`new: out/ref/gold/${s}/state.json exists`);
  const noun = opts.noun ?? s.replace(/_/g, " ");
  const prompt = conceptPrompt(desc, style);
  const files = [];
  const write = (rel, text) => { const f = P(rel); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, text); files.push(rel.replace(/\\/g, "/")); };
  const cdir = P("out", "concept", s);
  fs.mkdirSync(cdir, { recursive: true });
  const promptFile = path.join(cdir, "concept.txt");
  fs.writeFileSync(promptFile, `${prompt}\n`);
  // the concept: generated (not --dry), or --concept <png> padded the same way, or none (--dry alone)
  let raw = null, prov = null, source = opts.concept ? path.resolve(opts.concept) : null;
  if (!dry && !source) {
    const generate = opts.generate ?? (await import("./imagegen.mjs")).generateImage;
    const r = await generate({ gen, refs: [], promptFile, out: path.join(cdir, "raw.png"), aspect: opts.aspect ?? "1:1", name: `${s}_concept`, log, allowGemini: !!opts.allowGemini });
    if (!r.ok) throw new Error(`new: ${gen} generated no image (${r.provenance?.reason ?? "?"}; ${path.relative(root, r.provenanceFile ?? cdir)}) — nothing else written; run again`);
    source = r.out; prov = r.provenance;
  }
  let image = null;
  if (source) {
    const m = await sharp(source).metadata();
    raw = { file: path.relative(root, source).replace(/\\/g, "/"), width: m.width, height: m.height, bytes: fs.statSync(source).size, sha256: await shaOf(source) };
    fs.mkdirSync(path.dirname(target), { recursive: true });
    await padSquare(source, target);
    files.push(`refs/${s}.png`);
    image = { bytes: fs.statSync(target).size, sha256: await shaOf(target) };
  }
  write(`refs/${s}.README.md`, readmeText({ subject: s, gen: source && !opts.concept ? gen : null, prompt, raw, image, prov, from: opts.concept ? raw.file : null, style }));
  const dims = { L: size.L, W: size.W, H: size.H };
  write(`subjects/${s}/subject.json`, `${JSON.stringify(subjectTemplate({ subject: s, klass, style, title: opts.title ?? `${styleEntry.title} ${noun} (${DIRECT_CLASSES.includes(klass) ? "WF v10 direct subject" : "WF v8 gold subject"}; gold.mjs new${style !== DEFAULT_STYLE ? ` --style ${style}` : ""})` }), null, 2)}\n`);
  if (direct) write(`subjects/${s}/camera.json`, `${JSON.stringify(fixedCamera({ subject: s, klass }), null, 2)}\n`);
  const families = image ? await proposeFamilies(target) : null;
  write(`subjects/${s}/turnaround/views.json`, `${JSON.stringify(viewsTemplate({ dims, families, klass }), null, 2)}\n`);
  write(`subjects/${s}/turnaround/facts.json`, `${JSON.stringify(factsFrom({ subject: s, noun, desc, style }), null, 2)}\n`);
  write(`subjects/${s}/prior.json`, `${JSON.stringify(priorTemplate({ klass, dims }), null, 2)}\n`);
  // WF v10: a direct subject has no gold state (no rounds); its stage is `gold.mjs hs --subject <s>` from the files present
  if (direct) return { files, chain: chainLinesDirect(s), prompt, families, direct: true };
  const st = newState(s);
  st.ledger.push({ round: 0, role: "setup", text: `setup: new subject (gold.mjs new${dry ? " --dry" : ""}${style !== DEFAULT_STYLE ? ` --style ${style}` : ""}): concept ${image ? `refs/${s}.png (${opts.concept ? `from ${raw.file}` : gen})` : "not generated"} · prompt refs/${s}.README.md · subject.json, turnaround/views.json (families ${families ? "proposed" : "placeholder"}), facts.json (L ${dims.L} W ${dims.W} H ${dims.H} m stated), prior.json` });
  write(`out/ref/gold/${s}/state.json`, serializeState(st));
  write(`out/ref/gold/${s}/LEDGER.md`, renderLedger(st, Object.keys(VIEWS_VEHICLE)));
  return { files, chain: chainLines(s), prompt, families };
}

/** A temp root for --dry (the refs / subjects / out folders are created on write). */
export const dryRoot = () => fs.mkdtempSync(path.join(os.tmpdir(), "llmm-new-"));
