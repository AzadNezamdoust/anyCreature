// WORKFLOW-V3 §7.5 — one subject manifest + one class prior, read by every
// script instead of the SUBJECT / TARGET / ROLES constants that used to live
// inside each "generic" file.
//
//   subjects/<id>/subject.json   what THIS subject is: class, target, camera, and
//                                the per-subject files (module, passes, census,
//                                layout, regions), all paths relative to ROOT.
//   classes/<class>.json         what every subject of that class obeys: closed
//                                roles, bearing roles, budgets, census kinds,
//                                id-pass colours, likeness families, palette zones.
//
// Node-only (fs). The browser app fetches the same two JSON files over the dev
// server; it does not import this module.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DEFAULT_SUBJECT = "facade_brick";

/** `--subject <id>` wins, then LLMM_SUBJECT, then the default. */
export function subjectIdFromArgv(argv = process.argv.slice(2), env = process.env) {
  const i = argv.indexOf("--subject");
  if (i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--")) return argv[i + 1];
  return env.LLMM_SUBJECT || DEFAULT_SUBJECT;
}

const readJsonFile = (file) => JSON.parse(fs.readFileSync(file, "utf8"));

/**
 * @param {string} id subject id (folder name under subjects/)
 * @returns {{id:string, klass:string, subject:object, cls:object,
 *   rel:Record<string,string>, paths:Record<string,string>,
 *   readJson:(key:string)=>object|null}}
 */
/**
 * The class prior a subject runs under, from the class (variant applied): class weapon, gold pipeline (owner 2026-10-12):
 * subject.json `pipeline: "gold"` applies the class's `gold` block (rules module, floor, palette zones, critic seats);
 * a direct subject or a class without one: the class as is. + the subject's measured ruleOverrides.
 */
export function classPriorOf(cls, subject) {
  const piped = subject.pipeline === "gold" && cls.gold ? { ...cls, ...cls.gold, pipeline: "gold" } : cls;
  return subject.ruleOverrides ? { ...piped, ruleOverrides: subject.ruleOverrides } : piped;
}

export function loadSubject(id = DEFAULT_SUBJECT) {
  const file = path.join(ROOT, "subjects", id, "subject.json");
  if (!fs.existsSync(file)) throw new Error(`no subjects/${id}/subject.json — every subject needs a manifest`);
  const subject = readJsonFile(file);
  if (subject.id !== id) throw new Error(`subjects/${id}/subject.json says id "${subject.id}"`);
  if (!subject.class) throw new Error(`subjects/${id}/subject.json has no class`);
  const classFile = path.join(ROOT, "classes", `${subject.class}.json`);
  if (!fs.existsSync(classFile)) throw new Error(`no classes/${subject.class}.json for subject ${id}`);
  const base = readJsonFile(classFile);
  // V4-7: a subject's body VARIANT (subject.json `variant`) applies classes/<class>.json variants.<v>.overrides: each
  // top-level key replaces the class's, `likeness` and `knobPriors` merge one level deep. No variant = the class as is.
  const over = subject.variant ? base.variants?.[subject.variant]?.overrides : null;
  if (subject.variant && !base.variants?.[subject.variant]) throw new Error(`subjects/${id}/subject.json variant "${subject.variant}" is not in classes/${subject.class}.json variants`);
  const merged = over
    ? { ...base, ...over, likeness: { ...base.likeness, ...(over.likeness ?? {}) }, knobPriors: { ...base.knobPriors, ...(over.knobPriors ?? {}) } }
    : base;
  // V5-8 R2: the subject's MEASURED rule overrides ride the class prior, so every gate caller (fit, loop, pass: all
  // pass S.cls to validateParts / gateConfig) applies them; src/validate/limits.json never changes.
  // class weapon, gold pipeline (owner 2026-10-12): subject.json `pipeline: "gold"` applies the class's `gold` block (its
  // rules module, floor, palette zones, critic seats) over the class; a direct subject or a class without one: unchanged.
  const cls = classPriorOf(merged, subject);
  const rel = { ...(subject.paths ?? {}) };
  const paths = Object.fromEntries(Object.entries(rel).map(([k, v]) => [k, path.join(ROOT, v)]));
  const readJson = (key) => (paths[key] && fs.existsSync(paths[key]) ? readJsonFile(paths[key]) : null);
  return { id, klass: subject.class, subject, cls, rel, paths, readJson };
}
