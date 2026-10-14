#!/usr/bin/env node
// WF-LOOP-R2 A6 — one browser, one page, every view of a pass in sequence.
//
//   node scripts/capture2.mjs --dir out/facade/P4 --subject facade_brick --seed 1
//   node scripts/capture2.mjs --url "<url>" --out <file.png>        # one frame
//
// Why this exists: `pass.mjs` spawned `tools/BlindLoop/capture.mjs` once per
// view, and each spawn paid a node start, a chromium launch and a context
// teardown — 4-12 s of the pass's wall clock for two 900px frames, and the id
// pass (A2) makes it three. This launches chromium ONCE and drives the same
// page through every URL.
//
// It is NOT a second capture contract. `tools/BlindLoop/capture.mjs` is FROZEN
// and stays the definition of a frame; this file imports its `loadConfig`, uses
// the identical context options, the identical ready/drift assertions and the
// identical `page.screenshot` options, and is proved byte-for-byte against it
// on a fixture before it is trusted (see the A6 row of the r2 report). If the
// two ever disagree, this one is wrong.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import { loadConfig } from "../../../checkout/tools/BlindLoop/capture.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "..");
const REPO_ROOT = path.resolve(ROOT, "..", "..", "checkout"); // BlindLoop stays in D:/Git/checkout/tools

// playwright lives in the sibling BlindLoop tool; derived from ROOT, never an absolute path.
const require = createRequire(path.join(REPO_ROOT, "tools", "BlindLoop", "package.json"));
const { chromium } = require("playwright");
const DEFAULT_CONFIG = "tools/BlindLoop/config.llmmodeling.json";

class CaptureDrift extends Error {
  constructor(message) { super(message); this.name = "CaptureDrift"; }
}

/** The judged views, plus the A2 role mask. `idpass` rides the target camera. */
export function passUrls({ base, subject, seed = 1, size = 900, views = ["target", "threeQuarter"], idpass = true, shaded = [] }) {
  const out = views.map((view) => ({
    name: view,
    url: `${base}?capture=1&subject=${subject}&seed=${seed}&view=${view}&size=${size}`,
  }));
  // Owner 2026-09-25: lit look stills (<view>-shaded.png) so the shape reads; never measured by likeness.
  for (const view of shaded) {
    out.push({ name: `${view}-shaded`, url: `${base}?capture=1&shade=1&subject=${subject}&seed=${seed}&view=${view}&size=${size}` });
  }
  if (idpass) {
    out.push({
      name: "idpass",
      url: `${base}?capture=1&idpass=1&subject=${subject}&seed=${seed}&view=target&size=${size}`,
    });
  }
  return out;
}

/**
 * Drive one already-open page to one URL and write one PNG + its sidecar.
 * Every assertion here is capture.mjs's, in capture.mjs's order.
 */
async function shoot(page, cap, url, out) {
  const settings = {
    url,
    viewport: { width: cap.viewport.width, height: cap.viewport.height },
    deviceScaleFactor: cap.deviceScaleFactor,
    readyFlag: cap.readyFlag,
    manifestFlag: cap.manifestFlag,
    capturedAt: new Date().toISOString(),
  };

  const response = await page.goto(url, { waitUntil: "load", timeout: cap.navigationTimeoutMs });
  if (response && !response.ok()) {
    throw new CaptureDrift(`page responded ${response.status()} for ${url} (dev server not serving the capture page?)`);
  }
  try {
    await page.waitForFunction((flag) => window[flag] === true, cap.readyFlag, { timeout: cap.readyTimeoutMs });
  } catch {
    throw new CaptureDrift(`window.${cap.readyFlag} never became true within ${cap.readyTimeoutMs}ms for ${url}`);
  }

  const actual = await page.evaluate((manifestFlag) => ({
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    devicePixelRatio: window.devicePixelRatio,
    manifest: window[manifestFlag] ?? null,
  }), cap.manifestFlag);

  const drift = [];
  if (actual.innerWidth !== cap.viewport.width) drift.push(`viewport width ${actual.innerWidth} != ${cap.viewport.width}`);
  if (actual.innerHeight !== cap.viewport.height) drift.push(`viewport height ${actual.innerHeight} != ${cap.viewport.height}`);
  if (actual.devicePixelRatio !== cap.deviceScaleFactor) drift.push(`deviceScaleFactor ${actual.devicePixelRatio} != ${cap.deviceScaleFactor}`);
  if (actual.manifest === null) drift.push(`window.${cap.manifestFlag} is absent`);
  if (drift.length) throw new CaptureDrift(`capture settings drifted: ${drift.join("; ")}`);

  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  const buffer = await page.screenshot({
    type: "png",
    fullPage: false,
    animations: "disabled",
    caret: "hide",
    scale: "css",
  });
  fs.writeFileSync(out, buffer);
  fs.writeFileSync(`${out}.json`, `${JSON.stringify({
    settings,
    observed: { innerWidth: actual.innerWidth, innerHeight: actual.innerHeight, devicePixelRatio: actual.devicePixelRatio },
    manifest: actual.manifest,
    bytes: buffer.length,
  }, null, 2)}\n`);
  return { out, bytes: buffer.length, manifest: actual.manifest };
}

/**
 * @param {Array<{name:string, url:string, out:string}>} shots
 * @returns {Promise<{shots:object[], ms:number}>}
 */
export async function captureAll(shots, config = loadConfig()) {
  const cap = config.capture;
  const started = Date.now();
  const browser = await chromium.launch({ headless: true });
  let context;
  const done = [];
  try {
    context = await browser.newContext({
      viewport: { width: cap.viewport.width, height: cap.viewport.height },
      deviceScaleFactor: cap.deviceScaleFactor,
      reducedMotion: "reduce",
      colorScheme: "light",
      forcedColors: "none",
    });
    const page = await context.newPage();
    page.setDefaultTimeout(cap.navigationTimeoutMs);
    for (const shot of shots) {
      const at = Date.now();
      const result = await shoot(page, cap, shot.url, shot.out);
      done.push({ name: shot.name, ok: true, ms: Date.now() - at, ...result });
    }
  } finally {
    if (context) await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
  return { shots: done, ms: Date.now() - started };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) args[key] = true;
    else { args[key] = next; i += 1; }
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!process.env.BLINDLOOP_CONFIG) process.env.BLINDLOOP_CONFIG = path.join(REPO_ROOT, DEFAULT_CONFIG);
  const config = loadConfig(args.config ? path.resolve(args.config) : undefined);

  let shots;
  if (args.url) {
    if (!args.out) throw new Error("--url needs --out <file.png>");
    shots = [{ name: "single", url: args.url, out: path.resolve(args.out) }];
  } else {
    const dir = path.resolve(ROOT, args.dir ?? ".");
    const base = config.project.devServerUrl;
    shots = passUrls({
      base,
      // `--subject`, then LLMM_SUBJECT (scripts/subject.mjs), then the frozen capture
      // config's default — a spec subject has no subject.json, so no manifest is required.
      subject: args.subject ?? (process.env.LLMM_SUBJECT || config.capture.defaults.subject),
      seed: args.seed ?? config.capture.defaults.seed,
      size: args.size ?? config.capture.defaults.size,
      idpass: args.idpass !== "false",
    }).map((s) => ({ ...s, out: path.join(dir, `${s.name}.png`) }));
  }

  const { shots: done, ms } = await captureAll(shots, config);
  for (const s of done) console.log(`OK ${path.relative(ROOT, s.out).replace(/\\/g, "/")} (${s.ms} ms, ${s.bytes} bytes)`);
  console.log(`[capture2] ${done.length} frame(s) in ${(ms / 1000).toFixed(2)} s, one browser`);
  return 0;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    process.exitCode = await main();
  } catch (error) {
    console.error(`REFUSED: ${error.message}`);
    process.exitCode = 1;
  }
}
