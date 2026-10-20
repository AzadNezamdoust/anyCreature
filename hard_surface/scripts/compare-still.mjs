#!/usr/bin/env node
// usage: node scripts/compare-still.mjs <still.png> <out.png>
//
// WF-LOOP-R3 C2.3 (Fable M4). TOP ROW: the two FRONT-FACE QUADS, cropped and
// scaled to the SAME pixels per face width W, so the human "reads as the target"
// row judges the face the target actually shows. The r2 image put a 1024 px
// picture of a terrace beside a 900 px picture of a freestanding tower and the
// biggest visible difference was a blank side wall the target never shows
// (Fable L1) — a framing artefact, argued about for two rounds.
// BOTTOM ROW: the whole stills, unchanged, because the quads hide the massing.
//
// The render's quad comes from the capture manifest (`frontQuad`, app.js C2.1);
// the target's from subjects/facade_brick/layout.measured.json, or the Fable
// fallback frame, exactly as scripts/likeness.mjs resolves them — same code
// path, so the picture and the numbers can never be framed differently.
import { createRequire } from "node:module";
import path from "node:path";
import { existsSync, readFileSync } from "node:fs";

import { ROOT, resolveTargetQuad } from "./likeness.mjs";
import { loadSubject, subjectIdFromArgv } from "./subject.mjs";

// playwright lives in the sibling BlindLoop tool; derived from ROOT, never an absolute path.
const require = createRequire(path.join(ROOT, "..", "..", "checkout", "tools", "BlindLoop", "package.json"));
const { chromium } = require("playwright");

const argv = process.argv.slice(2);
const positional = argv.filter((a, i) => !a.startsWith("--") && !(i > 0 && argv[i - 1] === "--subject"));
const [still, out] = positional;
if (!still || !out) throw new Error("usage: node scripts/compare-still.mjs <still.png> <out.png> [--subject <id>]");
const S = loadSubject(subjectIdFromArgv(argv));

const b64 = (p) => `data:image/png;base64,${readFileSync(p).toString("base64")}`;
const targetFile = S.paths.target;
const target = b64(targetFile);
const right = b64(path.resolve(still));

const sidecar = `${path.resolve(still)}.json`;
const manifest = existsSync(sidecar) ? JSON.parse(readFileSync(sidecar, "utf8")).manifest ?? {} : {};
const renderQuad = manifest.frontQuad ?? null;
const measuredFile = S.paths.layoutMeasured;
const measured = existsSync(measuredFile) ? JSON.parse(readFileSync(measuredFile, "utf8")) : null;
const targetQuad = resolveTargetQuad(measured, renderQuad, S.rel.layoutMeasured);

/** The quad's own bounding box, padded, as a crop rect. */
function cropRect(quadPx, pad = 10) {
  const xs = quadPx.map((p) => p[0]);
  const ys = quadPx.map((p) => p[1]);
  return {
    x: Math.min(...xs) - pad,
    y: Math.min(...ys) - pad,
    w: (Math.max(...xs) - Math.min(...xs)) + pad * 2,
    h: (Math.max(...ys) - Math.min(...ys)) + pad * 2,
  };
}

/** The face width W in pixels: the longest horizontal edge of the quad. */
function faceWidthPx(quadPx) {
  let best = 0;
  for (let i = 0; i < 4; i += 1) {
    const a = quadPx[i];
    const b = quadPx[(i + 1) % 4];
    if (Math.abs(b[0] - a[0]) > Math.abs(best)) best = b[0] - a[0];
  }
  return Math.abs(best);
}

const W_PX = 340;             // every face is drawn this many pixels wide

/** One cropped, scaled face in a fixed-size window. */
function facePanel(src, quadPx, caption) {
  if (!quadPx) {
    return `<div style="width:${W_PX + 60}px"><div style="padding:4px">${caption}</div>`
      + `<div style="width:${W_PX + 40}px;height:420px;border:1px solid #bbb;display:flex;align-items:center;`
      + `justify-content:center;color:#900;font:13px sans-serif;text-align:center;padding:8px">`
      + "no front-face quad<br>(re-capture with the r3 app.js)</div></div>";
  }
  const rect = cropRect(quadPx);
  const scale = W_PX / faceWidthPx(quadPx);
  const boxW = Math.round(rect.w * scale);
  const boxH = Math.round(rect.h * scale);
  const poly = quadPx
    .map(([x, y]) => `${((x - rect.x) * scale).toFixed(1)},${((y - rect.y) * scale).toFixed(1)}`)
    .join(" ");
  return `<div style="width:${boxW + 20}px"><div style="padding:4px">${caption}</div>`
    + `<div style="position:relative;width:${boxW}px;height:${boxH}px;overflow:hidden;border:1px solid #bbb">`
    + `<img src="${src}" style="position:absolute;left:${(-rect.x * scale).toFixed(1)}px;`
    + `top:${(-rect.y * scale).toFixed(1)}px;transform-origin:0 0;transform:scale(${scale});image-rendering:auto">`
    + `<svg width="${boxW}" height="${boxH}" style="position:absolute;left:0;top:0">`
    + `<polygon points="${poly}" fill="none" stroke="#ff0090" stroke-width="1.5" stroke-dasharray="5 4"/></svg>`
    + "</div></div>";
}

const label = `${path.basename(path.dirname(still))}/${path.basename(still)}`;
const html = `<body style="margin:0;background:#fff;font:13px sans-serif">
<div style="padding:6px 8px 0">FRONT FACE, both at ${W_PX} px per face width W — this is the row "reads as the target" is judged on.</div>
<div style="display:flex;gap:10px;padding:4px 8px">
${facePanel(target, targetQuad.px, `TARGET front face — ${targetQuad.measured ? "measured quad" : "FALLBACK quad"}`)}
${facePanel(right, renderQuad?.px ?? null, `${label} front face`)}
</div>
<div style="padding:2px 8px;color:#555">target quad: ${targetQuad.provenance}</div>
<div style="display:flex;gap:8px;padding:6px 8px">
<div><div style="padding:4px">TARGET (style + model, not a trace)</div><img src="${target}" style="width:560px;height:560px"></div>
<div><div style="padding:4px">${label}</div><img src="${right}" style="width:560px;height:560px"></div>
</div></body>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 1160 } });
await page.setContent(html);
await page.screenshot({ path: out, fullPage: true });
await browser.close();
console.log("OK", out);
