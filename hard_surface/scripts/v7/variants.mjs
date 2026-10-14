#!/usr/bin/env node
// WORKFLOW v7 — variant experiments: build a module with JSON overrides, re-fit its concept frame, judge it; one table,
// best score first. Try several values of one uncertain dimension in one call instead of editing and re-rendering.
//
//   node scripts/v7/variants.mjs --subject <s> --module <m.mjs> [--no-fit] [--grid] [--rule concept-first] '<json>' ...
//
// A variant is a JSON object: a key naming a KNOB sets that knob's v for the build; any other key goes to the module's
// buildWith(o) (an object value merges one level into the module's DEFAULTS entry of that name). '{}' = the module as
// is (always included first as BASE). Per variant: frame re-fit (scripts/v7/frame.mjs search from the module's frame;
// --grid adds the coarse grid, --no-fit keeps the knob frame), then scripts/v6/judge.mjs: per-view IoU, score
// (concept x2 + orthos), the class placement checks (floats / clips), triangles. WF v8: a subject with views.json drift
// rects adds per-view agree columns (a.<view>; agree = IoU elsewhere); `--rule concept-first` (lib.mjs conceptFirst)
// picks the winner on agree and prints `WINNER BASE` or `WINNER #n` last.
import process from "node:process";

import { driftWarnings, judge } from "../v6/judge.mjs";
import { driftRects } from "../v6/ortho.mjs";
import * as K from "../../src/kernel/index.mjs";
import { buildVariant, conceptFirst, conceptIoUFn, conceptTarget, familyTableOf, fitFrame, importModule, parseArgs, roundFrame } from "./lib.mjs";

const RULES = ["concept-first"];
const args = parseArgs(process.argv.slice(2), ["no-fit", "grid", "help"]);
if (args.help || !args.subject || !args.module || (args.rule !== undefined && !RULES.includes(args.rule))) {
  console.log(`usage: node scripts/v7/variants.mjs --subject <s> --module <m.mjs> [--no-fit] [--grid] [--rule ${RULES.join("|")}] '<json overrides>' ...`);
  process.exit(args.help ? 0 : 3);
}

async function main() {
  const mod = await importModule(args.module);
  const { T } = await conceptTarget(args.subject);
  const list = ["{}", ...args._.filter((v) => v.trim() !== "{}")];
  const rows = [];
  for (const text of list) {
    let o;
    try { o = JSON.parse(text); } catch (e) { throw new Error(`variant ${text} is not JSON: ${e.message}`); }
    const label = text === "{}" ? "BASE" : `#${list.indexOf(text)} ${text}`;   // #n = the n-th variant argument
    let built;
    try {
      const { parts, frame } = buildVariant(mod, o);
      const bad = K.checkParts(mod.meta, parts);
      if (bad.length) throw new Error(bad[0]);
      built = { meta: mod.meta, parts, frame };
    } catch (e) {
      rows.push({ label, error: String(e.message ?? e).slice(0, 160) });
      continue;
    }
    let frame = built.frame;
    if (!args["no-fit"]) frame = (await fitFrame(conceptIoUFn(args.subject, T, built), built.frame, { grid: !!args.grid })).frame;
    const { metrics } = await judge({ subjectId: args.subject, built: { ...built, frame }, tiles: false });
    const floats = (metrics.checks?.groups ?? []).filter((g) => g.float).map((g) => g.name);
    const clips = (metrics.checks?.clips ?? []).map((c) => `${c.a}x${c.b}`);
    rows.push({ label, metrics, frame, checks: metrics.checks?.pass ? "PASS" : `FAIL${floats.length ? ` float ${floats.join(",")}` : ""}${clips.length ? ` clip ${clips.join(",")}` : ""}` });
  }
  const ok = rows.filter((r) => !r.error).sort((a, b) => b.metrics.score - a.metrics.score);
  const views = ok.length ? Object.keys(ok[0].metrics.views) : [];
  // WF v8: agree columns (a.<view>) when the subject has drift rects (without them agree = IoU)
  const table = await familyTableOf(args.subject);
  const agreeViews = views.some((v) => driftRects(table, v)) ? views : [];
  const aw = (v) => Math.max(7, v.length + 2);
  const lw = Math.min(60, Math.max(7, ...rows.map((r) => r.label.length)));
  console.log(["variant".padEnd(lw), "score ", ...views.map((v) => v.padStart(7)), ...agreeViews.map((v) => `a.${v}`.padStart(aw(v))), "   tris", " frame(scale,tx,ty)".padEnd(28), "checks"].join(" "));
  const base = ok.find((r) => r.label === "BASE");
  for (const r of ok) {
    const fr = roundFrame(r.frame);
    const d = base && r !== base ? ` (${r.metrics.score - base.metrics.score >= 0 ? "+" : ""}${(r.metrics.score - base.metrics.score).toFixed(5)})` : "";
    console.log([r.label.slice(0, lw).padEnd(lw), r.metrics.score.toFixed(4), ...views.map((v) => r.metrics.views[v].iou.toFixed(4).padStart(7)),
      ...agreeViews.map((v) => r.metrics.views[v].agree.toFixed(4).padStart(aw(v))), String(r.metrics.tris).padStart(7), ` ${fr.scale},${fr.tx},${fr.ty}`.padEnd(28), r.checks + d].join(" "));
  }
  for (const r of rows.filter((x) => x.error)) console.log(r.label.slice(0, lw).padEnd(lw), "ERROR", r.error);
  // labels cut to the column: the full overrides once, by variant number
  const cut = rows.filter((r) => r.label.length > lw);
  if (cut.length) for (const r of cut) console.log(r.label);
  for (const w of base ? driftWarnings(base.metrics) : []) console.log(w);
  if (args.rule === "concept-first") {
    const r = conceptFirst(ok);
    for (const l of r.lines) console.log(l);
    console.log(`WINNER ${r.winner ?? "none"}`);
  }
}

main().catch((e) => { console.error(e.message ?? e); process.exit(1); });
