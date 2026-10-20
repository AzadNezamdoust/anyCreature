#!/usr/bin/env node
// WORKFLOW v7 — a module's own structure (no references):
//
//   node scripts/v7/inspect.mjs parts    --module <m.mjs> [--filter <id substring>]
//   node scripts/v7/inspect.mjs contacts --module <m.mjs> [--ground-roles wheel,tyre] [--deep 0.02]
//   node scripts/v7/inspect.mjs chain    --module <m.mjs> [--subject <s>] [--layout] [--skip a,b] [--top 30]
//
// parts: per part id, role, zone, tris, aabb (m), LUMPS (disconnected pieces) and THIN (thin-cut residuals); then tris
// per part family (the id without its _l / _r / number suffix) and the total. contacts: the contact graph (overlap or
// face contact within 2 mm) -> connected components (every component but the largest is FLOATING), overlaps deeper than
// --deep of the smaller part's volume (declared seats {embed: true, touches: [host]} skipped), and parts reaching the ground (y < 5 mm) whose role is not a ground role.
// chain: the kernel validator chain (src/validate/kernel-chain.mjs) under the subject's class (else meta.class) gate
// config — pass, tris / budget, violations, advisories, report text; --layout adds the subject's census / layout.
// WF v8 WP3: `runChain(modulePath, subjectId, {skip, layout, built})` is the chain as a function (step.mjs, doctor.mjs).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../../src/kernel/index.mjs";
import { gateConfig, validateParts } from "../../src/validate/kernel-chain.mjs";
import { ROOT, loadSubject } from "../subject.mjs";
import { importModule, parseArgs } from "./lib.mjs";

const [cmd, ...rest] = process.argv.slice(2);
const args = parseArgs(rest, ["layout", "help"]);
const USAGE = "usage: node scripts/v7/inspect.mjs <parts|contacts|chain> --module <m.mjs> [...] (see the header / scripts/v7/README.md)";

const vol = (s) => { try { return s.volume(); } catch { return 0; } };
const near = (a, b, e) => [0, 1, 2].every((k) => a.min[k] <= b.max[k] + e && b.min[k] <= a.max[k] + e);
const fx = (v) => v.map((n) => n.toFixed(3)).join(",");

async function built() {
  const mod = await importModule(args.module);
  const parts = mod.build();
  const bad = K.checkParts(mod.meta, parts);
  for (const b of bad.slice(0, 10)) console.log("CHECKPARTS", b);
  return { mod, parts };
}

async function partsCmd() {
  const { parts } = await built();
  const filter = args.filter && args.filter !== true ? args.filter : "";
  const iw = Math.max(4, ...parts.map((p) => p.id.length));
  let total = 0;
  const groups = new Map();
  console.log("id".padEnd(iw), "role".padEnd(10), "zone".padEnd(10), " tris", "aabb min .. max (m)");
  for (const p of parts) {
    const t = p.solid.triCount();
    total += t;
    const g = p.id.replace(/_[lr]\d*$|_[a-z]?[lr]\d*$|\d+$/, "");
    groups.set(g, (groups.get(g) ?? 0) + t);
    if (filter && !p.id.includes(filter)) continue;
    const a = p.solid.aabb();
    const lumps = p.solid.decompose().length;
    const thin = p.solid.thinCuts();
    console.log(p.id.padEnd(iw), String(p.role ?? "").padEnd(10), String(p.zone ?? "").padEnd(10), String(t).padStart(5), fx(a.min), "..", fx(a.max),
      lumps > 1 ? `LUMPS ${lumps}` : "", thin.length ? `THIN ${thin.map((r) => `${r.side} rem ${r.remaining.toFixed(4)}`).join("; ")}` : "");
  }
  console.log("families:", [...groups.entries()].sort((a, b) => b[1] - a[1]).map(([g, n]) => `${g}:${n}`).join("  "));
  console.log("total tris", total, "parts", parts.length);
}

async function contactsCmd() {
  const { parts } = await built();
  const bb = parts.map((p) => p.solid.aabb());
  const E = 0.002;
  const touches = (i, j) => {
    if (!near(bb[i], bb[j], E)) return false;
    const a = parts[i].solid, b = parts[j].solid;
    if (vol(K.intersect(a, b)) > 1e-10) return true;
    for (const d of [[E, 0, 0], [-E, 0, 0], [0, E, 0], [0, -E, 0], [0, 0, E], [0, 0, -E]]) if (vol(K.intersect(a, b.at(d))) > 1e-10) return true;
    return false;
  };
  const n = parts.length, par = [...Array(n).keys()];
  const find = (x) => (par[x] === x ? x : (par[x] = find(par[x])));
  for (let i = 0; i < n; i += 1) for (let j = i + 1; j < n; j += 1) if (find(i) !== find(j) && touches(i, j)) par[find(i)] = find(j);
  const comps = new Map();
  for (let i = 0; i < n; i += 1) { const r = find(i); if (!comps.has(r)) comps.set(r, []); comps.get(r).push(parts[i].id); }
  const list = [...comps.values()].sort((a, b) => b.length - a.length);
  console.log(`components: ${list.length} (${list[0]?.length ?? 0} parts in the main one)`);
  for (const c of list.slice(1)) console.log("  FLOATING:", c.join(", "));
  const deepMin = Number(args.deep ?? 0.02);
  const deep = [];
  let seats = 0;
  // a declared seat (part {embed: true, touches: [host]}: decals, lenses, hubs) is meant to sink into its host
  const seated = (a, b) => (a.embed && a.touches?.includes(b.id)) || (b.embed && b.touches?.includes(a.id));
  for (let i = 0; i < n; i += 1) for (let j = i + 1; j < n; j += 1) {
    if (!near(bb[i], bb[j], 0)) continue;
    if (seated(parts[i], parts[j])) { seats += 1; continue; }
    const v = vol(K.intersect(parts[i].solid, parts[j].solid));
    if (v <= 1e-9) continue;
    const f = v / Math.min(vol(parts[i].solid), vol(parts[j].solid));
    if (f > deepMin) deep.push([f, parts[i].id, parts[j].id]);
  }
  deep.sort((a, b) => b[0] - a[0]);
  console.log(`overlaps > ${(deepMin * 100).toFixed(0)}% of the smaller part: ${deep.length} (declared seats skipped: ${seats})`);
  for (const [f, a, b] of deep.slice(0, 25)) console.log(`  ${(f * 100).toFixed(1)}%  ${a} x ${b}`);
  const groundRoles = String(args["ground-roles"] && args["ground-roles"] !== true ? args["ground-roles"] : "wheel,tyre").split(",");
  const ground = parts.filter((p, i) => bb[i].min[1] < 0.005 && !groundRoles.includes(p.role));
  console.log(`ground (y < 5 mm) parts outside roles [${groundRoles.join(",")}]: ${ground.length}`);
  for (const p of ground) console.log("  GROUND", p.id, p.role, p.solid.aabb().min[1].toFixed(4));
}

/**
 * WF v8 WP3 — the validator chain as a function (the `chain` command prints it; scripts/v7/step.mjs and doctor.mjs call
 * it): the module under the subject's class gate config (else its meta.class's), built here — or `built` {meta, parts}
 * already built under that config (check-module's build) — then src/validate/kernel-chain.mjs validateParts.
 * @returns {Promise<{pass:boolean, violations:object[], advisories:object[], measurements:object, text:string, cls:object,
 *   meta:object, parts:object[]}>}
 */
export async function runChain(modulePath, subjectId = null, { skip = [], layout = false, built = null, log = null } = {}) {
  await K.init();
  const mod = built ? null : await importModule(modulePath);
  const meta = built ? built.meta : mod.meta;
  let cls, S = null;
  if (subjectId) { S = loadSubject(subjectId); cls = S.cls; }
  else cls = JSON.parse(fs.readFileSync(path.join(ROOT, "classes", `${meta?.class ?? "vehicle"}.json`), "utf8"));
  K.configure(gateConfig(cls));   // the gate config BEFORE build (the kernel's cut check measures under it)
  try {
    const parts = built ? built.parts : mod.build();
    const rules = cls.rules ? await import(pathToFileURL(path.join(ROOT, cls.rules)).href) : undefined;
    const opts = { cls, rules, skip };
    if (layout) {
      if (!S) throw new Error("--layout needs --subject");
      opts.census = S.readJson("census") ?? undefined;
      opts.layout = S.readJson("layout") ?? undefined;
      log?.(`census ${opts.census ? "yes" : "none"} layout ${opts.layout ? "yes" : "none"}`);
    }
    const r = await validateParts(meta, parts, undefined, opts);
    return { ...r, cls, meta, parts };
  } finally {
    K.configure(null);
  }
}

async function chainCmd() {
  const r = await runChain(args.module, args.subject && args.subject !== true ? args.subject : null, {
    skip: String(args.skip && args.skip !== true ? args.skip : "").split(",").filter(Boolean), layout: !!args.layout, log: (l) => console.log(l) });
  const top = Number(args.top ?? 30);
  console.log("pass", r.pass, "tris", r.measurements.tris, "budget", r.measurements.triBudget, "parts", r.measurements.parts);
  for (const v of r.violations) console.log("VIOLATION", v.v, v.part ?? "", JSON.stringify(v.measured ?? "").slice(0, 160), String(v.hint ?? "").slice(0, 200));
  for (const a of (r.advisories ?? []).slice(0, top)) console.log("advisory", a.v, a.part ?? "", String(a.hint ?? JSON.stringify(a)).slice(0, 200));
  if ((r.advisories ?? []).length > top) console.log(`... ${r.advisories.length - top} more advisories (--top N)`);
  console.log(r.text.slice(0, 2000));
}

const COMMANDS = { parts: partsCmd, contacts: contactsCmd, chain: chainCmd };
// WF v8 WP3: importable (runChain) — the CLI runs only when this file is the entry point
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (!COMMANDS[cmd] || args.help || !args.module) {
    console.log(USAGE);
    process.exit(!COMMANDS[cmd] || !args.module ? 3 : 0);
  }
  COMMANDS[cmd]().catch((e) => { console.error(e.message ?? e); process.exit(1); });
}
