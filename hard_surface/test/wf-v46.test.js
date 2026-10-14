// WORKFLOW v4 — V4-6 (the v4.5 blind pickup evidence, commit 1eb96e9): numbered replies, zone names, the subject mask.
// Hermetic: the replies are the seats' ACTUAL step-1 replies (test/fixtures/v4/{luna,gmed}-step1-reply.md) against the
// module they were numbered on (test/fixtures/v4/step1-base-pickup.mjs = out/blind/pickup/*/LOOP/build/module.mjs);
// refs/, subjects/ and classes/ are read only; candidates go under test/.tmp-wf-v46-<pid>/.
process.env.LLMM_SUBJECT = "pickup";
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { applyLineEdits, NUMBERED_CONTRACT } from "../scripts/seat-io.mjs";
import { applyReply, duplicateIds, fixZones, zoneResiduals, PROMPT_MAX } from "../scripts/loop.mjs";
import { loadModule } from "../scripts/project.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { familyZoneKeys, residuals } from "../scripts/residuals.mjs";
import { subjectMaskOf, targetForeground, foregroundMask, readRGB } from "../scripts/registered.mjs";
import { measureTarget, subjectMask } from "../scripts/measure-target.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const FX = (f) => fs.readFileSync(path.join(ROOT, "test/fixtures/v4", f), "utf8");
const BASE = FX("step1-base-pickup.mjs");
// three levels under ROOT, like the fixture, so the module's relative kernel import resolves unchanged
const TMP = path.join(ROOT, "test", `.tmp-wf-v46-${process.pid}`, "m");
fs.mkdirSync(TMP, { recursive: true });
test.after(() => fs.rmSync(path.dirname(TMP), { recursive: true, force: true }));
test.before(async () => { await K.init(); if (K.assemble?.ready) await K.assemble.ready; });
const lines = (t) => t.split(/\r?\n/);

test("V4-6 item 1: Luna's numbered reply (`121| …`, `144| …`) replaces lines 121 and 144 — no duplicate mirror", async () => {
  const r = applyReply(BASE, FX("luna-step1-reply.md"));
  assert.ok(r.text, r.why);
  assert.match(r.how, /2 line edit\(s\) \(2 numbered N\|\)/);
  const a = lines(BASE);
  const b = lines(r.text);
  assert.equal(b.length, a.length, "a replacement, not an insert");
  const changed = b.map((l, i) => (l !== a[i] ? i + 1 : 0)).filter(Boolean);
  assert.deepEqual(changed, [121, 144]);
  assert.match(b[120], /^ {4}wheels: \{ r: k\.wheelR \+ 0\.03,/, "the one space after `|` is the display's, the indent is kept");
  const file = path.join(TMP, "luna.mjs");
  fs.writeFileSync(file, r.text);
  assert.deepEqual(await duplicateIds(file), []);
  // the v4.5 reading (an insert block before `return parts;`) is what built the mirror twice: refused before build
  const ins = BASE.replace(/\n(\s*return parts;)/, `\n${lines(FX("luna-step1-reply.md"))[5].replace(/^144\| /, "")}\n$1`);
  const dupFile = path.join(TMP, "luna-insert.mjs");
  fs.writeFileSync(dupFile, ins);
  assert.deepEqual((await duplicateIds(dupFile)).slice(0, 2), ["mirror_head_l", "mirror_arm_l"]);
});

test("V4-6 item 1: the numbered format — ranges, `N|code`, inserted lines, gap markers; `replace A-B` still works", () => {
  const mod = ["a", "b", "c", "d", "e"].join("\n");
  const t = (reply) => applyLineEdits(mod, reply);
  assert.equal(t("```js\n2| B\n3|C\n```").text, "a\nB\nC\nd\ne", "consecutive numbers = one range, space optional");
  assert.equal(t("```\n2| b\n  new\n```").text, "a\nb\n  new\nc\nd\ne", "an unnumbered line under N| is inserted after N");
  assert.equal(t("```js\n1| A\n  | …\n5| E\n```").text, "A\nb\nc\nd\nE", "the display's gap marker splits edits");
  assert.equal(t("```js replace 2-3\nX\n```").text, "a\nX\nd\ne");
  assert.match(t("```js\n9| z\n```").error, /numbered line 9\| is outside the module's 1\.\.5 lines/);
  assert.match(t("```js replace 2-3\nX\n```\n```js\n3| y\n```").error, /overlaps/);
  assert.match(NUMBERED_CONTRACT, /`N\| new code` replaces line N/);
  assert.equal(PROMPT_MAX, 6144);
});

test("V4-6 item 2: Gemini's zone \"dark\" (a family) is renamed to its palette key before the load check", async () => {
  const S = loadSubject("pickup");
  const fk = familyZoneKeys(S);
  assert.deepEqual(fk.dark, ["tyre", "grille", "tread"]);
  const r = applyReply(BASE, FX("gmed-step1-reply.md"));
  assert.ok(r.text, r.why);
  const baseFile = path.join(TMP, "base.mjs");
  fs.writeFileSync(baseFile, BASE);
  const base = { parts: (await loadModule(baseFile)).build() };
  const z = await fixZones(S, r.text, path.join(TMP, "gmed.mjs"), base);
  assert.deepEqual(z.fixes.map(({ from, to }) => ({ from, to })), [{ from: "dark", to: "grille" }], "the arch liners were grille in the base");
  assert.match(z.text, /zones: \{ liner: "grille" \}/);
  assert.doesNotMatch(z.text, /"dark"/);
  // ZONE rows print the family with its keys, never as a bare zone name
  const res = await residuals({ subjectId: "pickup", modulePath: baseFile });
  const rows = zoneResiduals(res, { dark: 1 }, S.cls.zoneProposals, fk);
  assert.match(rows[0].text, /^RESIDUAL dark-family \[tyre\|grille\|tread\] ZONE /);
  for (const row of res.rows.filter((x) => x.kind === "MISSING")) assert.ok(!fk[row.zone], `MISSING row zone ${row.zone} is a key`);
});

test("V4-6 item 5: the facade subject mask is measured (deterministic), excludes the neighbours and lifts the registered IoU", async () => {
  const S = loadSubject("facade_brick");
  const rec = S.readJson("layoutMeasured")._subjectMask;
  const m = await measureTarget({ targetFile: S.paths.target, regionsFile: S.paths.regions, cameraFile: S.paths.camera });
  const sm = subjectMask(m.img, m.cls, m.frame, m.camera, m.keys["crown.height"].value * m.frame.H);
  assert.deepEqual(sm.polygon, rec.polygon, "layout.measured.json _subjectMask is the measurement's output");
  const [x0, y0, x1, y1] = sm.evidence.bboxPx;
  assert.ok(x1 <= m.frame.x1 + 30 && x0 >= 350 && y0 >= 130 && y1 <= 915, `bbox ${sm.evidence.bboxPx}`);
  const img = await readRGB(S.paths.target);
  const mask = subjectMaskOf(S, img.w, img.h);
  // the green neighbour's roof vent and the tan neighbour's balconies are outside; the awning's overhang is inside
  for (const [x, y, inside] of [[200, 230, 0], [880, 400, 0], [900, 560, 0], [650, 380, 1], [770, 700, 1], [540, 600, 1], [650, 230, 1]]) {
    assert.equal(mask[y * img.w + x], inside, `(${x}, ${y})`);
  }
  const fg = foregroundMask(img).reduce((s, v) => s + v, 0);
  const tfg = targetForeground(S, img).reduce((s, v) => s + v, 0);
  assert.ok(tfg < 0.4 * fg && tfg > 0.25 * fg, `${tfg} of ${fg}`);
  const r = await residuals({ subjectId: "facade_brick", modulePath: "test/fixtures/v4/start-knobs-facade.mjs" });
  assert.ok(r.registeredIoU >= 0.6, `registered IoU ${r.registeredIoU} (whole-image ~0.40)`);
  assert.equal(subjectMaskOf(loadSubject("pickup"), 64, 64), null, "a subject alone in its target has no mask");
});
