#!/usr/bin/env node
// WORKFLOW v4 — V4-1 item 1: the pure Node PROJECTOR (research/WF-V4-PLAN.md S2 FIT / residuals).
//
//   node scripts/project.mjs --subject pickup --module out/ref/work/pickup.mjs [--frame capture|target] [--size N]
//
// A module (build() -> parts through src/kernel) meshed part by part, turned by meta.front exactly like
// src/kernel/toThree.mjs, projected through refs/<subject>.camera.json and rasterised with a depth buffer — no
// browser. frame "capture" reproduces app.js `?capture=1&view=target&size=900` (frameTarget: ortho, centred on the
// model bounds, projected-AABB / FILL); frame "target" is the REGISTERED frame (scripts/registered.mjs: target
// image px, fixed per subject, no bbox rescale). Pixel centres are sampled (x + 0.5), back faces culled (app
// captureMaterial is FrontSide), ties go to the later part (three's LessEqual depth, draw order).
//
// API: project({ subjectId, modulePath, size, frame, scale, roi }) -> { w, h, partId (Int32Array, -1 = background),
//   depth, face (Uint8Array FACE id per px), parts: [{ id, role, zone, aabb, screen }], roles, partRole,
//   mask(roleOrPartId), foreground(), ... }
// V5-4 item 1: `roi` {x0, y0, x1, y1} (target px, frame "target" only) rasterises ONLY that orthographic sub-window at 1
// target px per px — the per-feature FIT scores a feature at full resolution for the cost of its window. V5-4 item 3:
// every px carries the FACE-ORIENTATION id of the facet it shows (render frame: top = n.y > 0.5, bottom < -0.5, else
// front = |n.x| >= |n.z| — the render turns meta.front onto +X — else side), the per-face palette's sampling pass.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as THREE from "three";

import * as K from "../src/kernel/index.mjs";
import { frontRotationDeg } from "../src/kernel/toThree.mjs";
import { ROOT, loadSubject } from "./subject.mjs";
import { frameOf, framed, registration, turnFn } from "./registered.mjs";

const KERNEL_URL = pathToFileURL(path.join(ROOT, "src", "kernel", "index.mjs")).href;
/** src/app.js FILL / CAPTURE_SIZE_DEFAULT. */
export const FILL = 0.86;
export const CAPTURE_SIZE = 900;

// ---------------------------------------------------------------------------
// Module + subject caches (kernel init once; a module re-imports only when its text changes)
// ---------------------------------------------------------------------------

const moduleCache = new Map();
const subjectCache = new Map();

/**
 * Import a module from its TEXT, with relative imports rewritten to absolute file URLs (any `.../src/kernel/index.mjs`
 * specifier goes to THIS kernel, so a module copied out of its folder still loads and shares one kernel instance).
 */
export async function loadModule(modulePath) {
  const abs = path.resolve(ROOT, modulePath);
  const text = fs.readFileSync(abs, "utf8");
  const hash = createHash("sha1").update(text).digest("hex");
  const hit = moduleCache.get(abs);
  if (hit && hit.hash === hash) return hit.mod;
  const dir = path.dirname(abs);
  const rewritten = text.replace(/(\bfrom\s*|\bimport\s*\(\s*|\bimport\s+)(["'])(\.{1,2}\/[^"']+)\2/g, (m, pre, q, spec) => {
    const url = /src\/kernel\/index\.mjs$/.test(spec) ? KERNEL_URL : pathToFileURL(path.resolve(dir, spec)).href;
    return `${pre}${q}${url}${q}`;
  });
  const mod = await import(`data:text/javascript;base64,${Buffer.from(rewritten).toString("base64")}`);
  moduleCache.set(abs, { hash, mod });
  return mod;
}

function subjectContext(subjectId) {
  let ctx = subjectCache.get(subjectId);
  if (!ctx) {
    const S = loadSubject(subjectId);
    const camera = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
    ctx = { S, camera, reg: null };
    subjectCache.set(subjectId, ctx);
  }
  return ctx;
}

/** Registration of a subject (cached). */
export function subjectRegistration(subjectId) {
  const ctx = subjectContext(subjectId);
  if (!ctx.reg) ctx.reg = registration(ctx.S);
  return ctx.reg;
}

// ---------------------------------------------------------------------------
// Build + mesh
// ---------------------------------------------------------------------------

const round6 = (v) => Math.round(v * 1e6) / 1e6;

/** build() + K.checkParts, exactly the app's compileModule order. */
export async function buildModule(modulePath) {
  await K.init();
  const mod = await loadModule(modulePath);
  if (typeof mod.build !== "function") throw new Error(`${modulePath}: no exported build()`);
  const parts = mod.build();
  const violations = K.checkParts(mod.meta, parts);
  if (violations.length > 0) throw new Error(`${modulePath}: ${violations[0]}`);
  return { meta: mod.meta, parts, frame: frameOf(mod.KNOBS) };
}

/** Every part's triangles in the RENDER frame (float32-rounded like the three geometry), plus the model bounds. */
export function meshParts(parts, turnDeg, scale = 1) {
  const turn = turnFn(turnDeg);
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  const meshes = parts.map((part) => {
    const m = part.solid.mesh();
    const stride = m.numProp;
    const vp = m.vertProperties;
    const nv = vp.length / stride;
    const pos = new Float64Array(nv * 3);
    const pmin = [Infinity, Infinity, Infinity];
    const pmax = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < nv; i += 1) {
      const p = turn([Math.fround(vp[i * stride]) * scale, Math.fround(vp[i * stride + 1]) * scale, Math.fround(vp[i * stride + 2]) * scale]);
      for (let k = 0; k < 3; k += 1) {
        const v = Math.fround(p[k]);
        pos[i * 3 + k] = v;
        if (v < pmin[k]) pmin[k] = v;
        if (v > pmax[k]) pmax[k] = v;
      }
    }
    for (let k = 0; k < 3; k += 1) { min[k] = Math.min(min[k], pmin[k]); max[k] = Math.max(max[k], pmax[k]); }
    return { pos, tris: m.triVerts, aabb: { min: pmin, max: pmax } };
  });
  const bounds = {
    min: min.map(round6),
    max: max.map(round6),
    centre: [0, 1, 2].map((k) => round6((min[k] + max[k]) / 2)),
  };
  return { meshes, bounds };
}

/** app.js frameTarget: camera matrixWorldInverse elements + the half extent (projected AABB / FILL). */
export function frameCapture(cameraSpec, bounds) {
  const centre = new THREE.Vector3().fromArray(bounds.centre);
  const theta = THREE.MathUtils.degToRad(cameraSpec.theta_deg);
  const phi = THREE.MathUtils.degToRad(cameraSpec.phi_deg);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
  cam.position.copy(centre).add(new THREE.Vector3().setFromSphericalCoords(100, Math.PI / 2 - theta, phi));
  cam.up.set(0, 1, 0);
  cam.lookAt(centre);
  cam.updateMatrixWorld(true);
  const toCamera = new THREE.Matrix4().copy(cam.matrixWorld).invert();
  const corner = new THREE.Vector3();
  let ex = 0;
  let ey = 0;
  for (let i = 0; i < 8; i += 1) {
    corner.set(i & 1 ? bounds.max[0] : bounds.min[0], i & 2 ? bounds.max[1] : bounds.min[1], i & 4 ? bounds.max[2] : bounds.min[2]).applyMatrix4(toCamera);
    ex = Math.max(ex, Math.abs(corner.x));
    ey = Math.max(ey, Math.abs(corner.y));
  }
  return { e: toCamera.elements.slice(), half: Math.max(ex, ey) / FILL, centre: bounds.centre };
}

// ---------------------------------------------------------------------------
// Raster: pixel-centre sampling, depth buffer, back-face cull
// ---------------------------------------------------------------------------

/** V5-4 item 3: face-orientation ids (render frame). The per-face palette keys are FACES[0..2]; bottom paints as side. */
export const FACES = Object.freeze(["top", "front", "side", "bottom"]);
export const NO_FACE = 255;
/** FACES index of a render-frame normal (need not be unit length). */
export function faceOf(nx, ny, nz) {
  const l = Math.hypot(nx, ny, nz) || 1;
  if (ny / l > 0.5) return 0;
  if (ny / l < -0.5) return 3;
  return Math.abs(nx) >= Math.abs(nz) ? 1 : 2;
}

/** X = kx * xc + bx, Y = -kx * yc + by (xc, yc camera-space metres). */
function rasterise(meshes, e, map, w, h) {
  const partId = new Int32Array(w * h).fill(-1);
  const depth = new Float32Array(w * h).fill(Infinity);
  const face = new Uint8Array(w * h).fill(NO_FACE);
  const { kx, bx, by } = map;
  const screen = [];
  for (let p = 0; p < meshes.length; p += 1) {
    const { pos, tris } = meshes[p];
    const nv = pos.length / 3;
    const sx = new Float64Array(nv);
    const sy = new Float64Array(nv);
    const sz = new Float64Array(nv);
    let x0b = Infinity, y0b = Infinity, x1b = -Infinity, y1b = -Infinity;
    for (let i = 0; i < nv; i += 1) {
      const x = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
      const X = kx * (e[0] * x + e[4] * y + e[8] * z + e[12]) + bx;
      const Y = -kx * (e[1] * x + e[5] * y + e[9] * z + e[13]) + by;
      sx[i] = X; sy[i] = Y;
      sz[i] = -(e[2] * x + e[6] * y + e[10] * z + e[14]);   // distance in front of the camera
      if (X < x0b) x0b = X; if (X > x1b) x1b = X; if (Y < y0b) y0b = Y; if (Y > y1b) y1b = Y;
    }
    screen.push({ x0: x0b, y0: y0b, x1: x1b, y1: y1b });
    for (let t = 0; t < tris.length; t += 3) {
      const a = tris[t], b = tris[t + 1], c = tris[t + 2];
      const ax = sx[a], ay = sy[a], bxx = sx[b], byy = sy[b], cx = sx[c], cy = sy[c];
      const area = (bxx - ax) * (cy - ay) - (cx - ax) * (byy - ay);
      if (area >= 0) continue;   // CCW in NDC (y up) is CW in pixel rows (y down): area < 0 faces the camera
      let minX = Math.ceil(Math.min(ax, bxx, cx) - 0.5), maxX = Math.floor(Math.max(ax, bxx, cx) - 0.5);
      let minY = Math.ceil(Math.min(ay, byy, cy) - 0.5), maxY = Math.floor(Math.max(ay, byy, cy) - 0.5);
      if (minX < 0) minX = 0; if (minY < 0) minY = 0; if (maxX > w - 1) maxX = w - 1; if (maxY > h - 1) maxY = h - 1;
      if (minX > maxX || minY > maxY) continue;
      const inv = 1 / area;
      const ux = pos[b * 3] - pos[a * 3], uy = pos[b * 3 + 1] - pos[a * 3 + 1], uz = pos[b * 3 + 2] - pos[a * 3 + 2];
      const vx = pos[c * 3] - pos[a * 3], vy = pos[c * 3 + 1] - pos[a * 3 + 1], vz = pos[c * 3 + 2] - pos[a * 3 + 2];
      const fid = faceOf(uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx);
      const za = sz[a], zb = sz[b], zc = sz[c];
      for (let py = minY; py <= maxY; py += 1) {
        const Y = py + 0.5;
        for (let px = minX; px <= maxX; px += 1) {
          const X = px + 0.5;
          // barycentrics (all <= 0 inside for area < 0 -> scaled by inv they are >= 0)
          const w0 = ((cx - bxx) * (Y - byy) - (cy - byy) * (X - bxx)) * inv;
          if (w0 < 0) continue;
          const w1 = ((ax - cx) * (Y - cy) - (ay - cy) * (X - cx)) * inv;
          if (w1 < 0) continue;
          const w2 = 1 - w0 - w1;
          if (w2 < 0) continue;
          const d = w0 * za + w1 * zb + w2 * zc;
          const i = py * w + px;
          if (d <= depth[i]) { depth[i] = d; partId[i] = p; face[i] = fid; }
        }
      }
    }
  }
  return { partId, depth, face, screen };
}

// ---------------------------------------------------------------------------
// project()
// ---------------------------------------------------------------------------

/**
 * @param {{subjectId:string, modulePath:string, size?:number, frame?:"capture"|"target", scale?:number,
 *   built?:{meta:object, parts:object[]}}} o
 *   size: raster px (capture default 900; target default the target image width — a smaller size keeps the frame
 *   and scales it, for FIT). scale: uniform model scale about the origin (tests: a scaled copy). built: skip build().
 */
export async function project({ subjectId, modulePath, size = null, frame = "capture", scale = 1, built = null, roi = null }) {
  const ctx = subjectContext(subjectId);
  const { meta, parts, frame: sim = null, meshed = null } = built ?? await buildModule(modulePath);
  const turnDeg = frontRotationDeg(meta.front);
  // V5-4: a caller that projects one build twice (whole frame + ROI window) meshes it once (built.meshed)
  const { meshes, bounds } = meshed ?? meshParts(parts, turnDeg, scale);
  const cap = frameCapture(ctx.camera, bounds);
  let w;
  let map;
  let reg = null;
  if (frame === "target") {
    reg = framed(subjectRegistration(subjectId), sim);   // V5-1 item 2: the module's fitted similarity
    w = size ?? reg.targetW;
    const f = w / reg.targetW;
    // target X = s (p.right) + ox; the view matrix rows are right / up, so xc = p.right + e12 and yc = p.up + e13
    map = { kx: reg.s * f, bx: (reg.ox - reg.s * cap.e[12]) * f, by: (reg.oy + reg.s * cap.e[13]) * f };
  } else {
    w = size ?? CAPTURE_SIZE;
    map = { kx: w / (2 * cap.half), bx: w / 2, by: w / 2 };
  }
  let h = frame === "target" ? Math.round(w * reg.targetH / reg.targetW) : w;
  let win = null;
  if (roi) {
    // V5-4 item 1: the orthographic sub-window [x0, x1] x [y0, y1] of the full-resolution target frame, 1 px per px
    if (frame !== "target" || w !== reg.targetW) throw new Error("project: roi needs frame \"target\" at the target's own size");
    win = { x0: Math.max(0, Math.floor(roi.x0)), y0: Math.max(0, Math.floor(roi.y0)), x1: Math.min(w - 1, Math.ceil(roi.x1)), y1: Math.min(h - 1, Math.ceil(roi.y1)) };
    map = { ...map, bx: map.bx - win.x0, by: map.by - win.y0 };
    w = win.x1 - win.x0 + 1;
    h = win.y1 - win.y0 + 1;
  }
  const { partId, depth, face, screen } = rasterise(meshes, cap.e, map, w, h);
  const roles = [...new Set(parts.map((p) => p.role))];
  const partRole = Int32Array.from(parts.map((p) => roles.indexOf(p.role)));
  const partMeta = parts.map((p, i) => ({ id: p.id, role: p.role, zone: p.zone, aabb: meshes[i].aabb, screen: screen[i] }));
  const e = cap.e;
  const toPx = ([x, y, z]) => [map.kx * (e[0] * x + e[4] * y + e[8] * z + e[12]) + map.bx, -map.kx * (e[1] * x + e[5] * y + e[9] * z + e[13]) + map.by];
  return {
    w, h, frame, partId, depth, face, roi: win, roles, partRole, parts: partMeta, meta, bounds, turnDeg, meshed: { meshes, bounds },
    capture: { centre: cap.centre, half: cap.half, size: CAPTURE_SIZE },
    registration: reg,
    /** px per metre on the screen plane */
    pxPerM: map.kx,
    toPx,
    /** foreground mask (Uint8Array) */
    foreground() { const m = new Uint8Array(w * h); for (let i = 0; i < m.length; i += 1) m[i] = partId[i] >= 0 ? 1 : 0; return m; },
    /** mask of a role name, else of a part id */
    mask(name) {
      const r = roles.indexOf(name);
      const m = new Uint8Array(w * h);
      if (r >= 0) { for (let i = 0; i < m.length; i += 1) m[i] = partId[i] >= 0 && partRole[partId[i]] === r ? 1 : 0; return m; }
      const p = parts.findIndex((q) => q.id === name);
      for (let i = 0; i < m.length; i += 1) m[i] = p >= 0 && partId[i] === p ? 1 : 0;
      return m;
    },
  };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject");
  const modulePath = arg("module");
  if (!subjectId || !modulePath) {
    console.error("usage: node scripts/project.mjs --subject <id> --module <path.mjs> [--frame capture|target] [--size N]");
    process.exit(3);
  }
  const frame = arg("frame", "capture");
  const size = arg("size") ? Number(arg("size")) : null;
  const t0 = performance.now();
  const r = await project({ subjectId, modulePath, frame, size });
  const t1 = performance.now();
  await project({ subjectId, modulePath, frame, size });
  const t2 = performance.now();
  const counts = new Map();
  for (let i = 0; i < r.partId.length; i += 1) if (r.partId[i] >= 0) { const role = r.roles[r.partRole[r.partId[i]]]; counts.set(role, (counts.get(role) ?? 0) + 1); }
  console.log(`[project] ${modulePath} frame ${frame} ${r.w}x${r.h} parts ${r.parts.length} fg ${[...counts.values()].reduce((a, b) => a + b, 0)} px; first ${(t1 - t0).toFixed(0)} ms, next ${(t2 - t1).toFixed(0)} ms`);
  console.log([...counts.entries()].map(([k, v]) => `${k} ${v}`).join(", "));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(error); process.exit(1); });
}
