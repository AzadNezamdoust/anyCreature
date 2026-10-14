// Concept STYLE blocks (scripts/v7/styles.json): `gold.mjs new --style <name>` composes the concept prompt with one, and
// turnaround.mjs uses the subject's (facts.json `style`, default cartoon) for the sheet / repair prompts. `cartoon` is the
// frozen scripts/make-target.mjs STYLE (styles.test.mjs pins them equal).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const STYLES_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), "styles.json");
const DOC = JSON.parse(fs.readFileSync(STYLES_FILE, "utf8"));
export const DEFAULT_STYLE = DOC.default;
export const STYLE_NAMES = Object.freeze(Object.keys(DOC.styles));

/** One style entry {about, title, text}; throws on an unknown name. */
export function styleOf(name = DEFAULT_STYLE) {
  const s = DOC.styles[name ?? DEFAULT_STYLE];
  if (!s) throw new Error(`--style ${name}: ${STYLE_NAMES.join(" | ")} (scripts/v7/styles.json)`);
  return s;
}

/** The STYLE text of a style name (default cartoon = make-target.mjs STYLE). */
export const styleText = (name) => styleOf(name).text;
