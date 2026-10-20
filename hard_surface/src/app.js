// The spec studio, and the locked capture mode the blind loop renders through.
//
// Two modes, one file (forked from CharacterStudioV2/src/studio.js:6-12):
//
//   studio  — panel, orbit controls, a rAF loop, GLB export.
//   capture — ?capture=1. No panel, no controls, no loop, no damping. Fixed
//             camera, fixed lights, fixed clear colour, exactly ONE render,
//             then window.__CAPTURE_MANIFEST__ and window.__CAPTURE_READY__.
//
// The capture invariant is load-bearing: identical query string => identical
// pixels. Nothing in the capture path may read the clock, the device pixel
// ratio, the window size, or Math.random().
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import { compile } from "./compile/build.js";
import { validate, buildPrims } from "./validate/index.js";
import { partBox, projRadius, faceVector } from "./validate/obb.js";
import { assetMaterial, captureMaterial } from "./material.js";
import { specHash, DSL_VERSION } from "./spec.js";
import { exportGlb } from "./exporters.js";
import * as K from "./kernel/index.mjs";                       // V2:
import { partsToGeometry, frontRotationDeg } from "./kernel/toThree.mjs";   // V2:
import { hash32 } from "./geom.js";                            // V2:
import { validateParts } from "./validate/kernel-chain.mjs";   // V2: S2 kernel chain

// ---------------------------------------------------------------------------
// Constants — every one of them a fixed number, never a host property.
// ---------------------------------------------------------------------------

// A subject is a named spec the capture URL may ask for. `?spec=` reaches any
// file in the served tree but is ignored under ?capture=1 (the capture URL is
// (subject, view, seed, size) and nothing else), so a spec that has to be
// CAPTURED needs a name here.
const SUBJECT_SPECS = Object.freeze({
  tenement_block: "./subjects/tenement_block/spec.json",
  tenement_block_llm: "./subjects/tenement_block_llm/spec.json",   // M3 blind LLM run
  // M5 generality subject. The file does not exist until the blind LLM run has
  // happened — loadSpec() warns and stands in a placeholder rather than throwing.
  pickup_truck: "./subjects/pickup_truck_llm/spec.json",
  facade_demo: "./dsl/examples/facade-demo.json",
  // M6 worked example: composites as parents, per-instance children, alignU.
  balcony_open: "./dsl/examples/balcony-open.json",
});

// V2: A subject with an authored kernel module is a PROGRAM (V2-TEST-PLAN 2):
// V2: imported, built through the kernel, painted by partsToGeometry into the
// V2: same {geometry, solved{parts,bounds,triangles}} `compile()` hands back, so
// V2: there is no second render path and no second capture contract.
// WORKFLOW-V3 §7.5: the module subjects are discovered, not listed — a folder
// under subjects/ with a `.mjs` in it, whose subject.json names the module, the
// class and every data path. `import.meta.glob` keeps the specifiers static for
// vite, which is what lets `vite build` bundle the module and the WASM kernel.
const SUBJECT_MODULES = import.meta.glob("../subjects/*/*.mjs");             // V2:
// Owner 2026-09-26 — reference/work modules rendered with a subject's camera and class (`?module=out/ref/x.mjs`),
// so an author can SEE its own work without touching the live subject module (scripts/render-module.mjs).
const REF_MODULES = import.meta.glob("../out/ref/**/*.mjs");
const CLASS_RULES = import.meta.glob("./validate/rules/*.mjs");
const MODULE_SUBJECTS = Object.freeze([...new Set(Object.keys(SUBJECT_MODULES)
  .map((key) => key.split("/")[2]))]);
const SUBJECTS = Object.freeze([...Object.keys(SUBJECT_SPECS), ...MODULE_SUBJECTS.filter((s) => !Object.hasOwn(SUBJECT_SPECS, s))]);
// Owner 2026-09-13: the app opens on the authored kernel subject, not the v1 tenement.
const DEFAULT_SUBJECT = "facade_brick";

const VIEWS = Object.freeze({
  /** The judged view: orthographic, angle measured off the frozen TARGET. */
  target: { label: "Target (ortho)", kind: "ortho" },
  /** Human-readable perspective three-quarter, same framing family as CS2. */
  threeQuarter: { label: "Three-quarter", kind: "perspective", yawDeg: 28, pitchDeg: 22, fov: 26 },
  /**
   * The QA back view (M2): the judged camera with the azimuth turned 180 deg, so
   * `scripts/qa-sheet.mjs` can show the faces the target view never sees. Same
   * elevation, same frustum rule, same fill — only the azimuth moves, which is
   * what makes it a regression check and not a second opinion.
   */
  back: { label: "Back (ortho +180)", kind: "ortho", azimuthOffsetDeg: 180 },
});
const DEFAULT_VIEW = "target";

const CAPTURE_SIZE_DEFAULT = 900;
/** Fraction of the frame the subject's height fills in the target view. */
const FILL = 0.86;
/** Used when refs/<subject>.camera.json is absent. Provisional, unmeasured. */
const PROVISIONAL_CAMERA = Object.freeze({ theta_deg: 30, phi_deg: 45, provisional: true });

const has = (object, key) => typeof key === "string" && Object.hasOwn(object, key);

// ---------------------------------------------------------------------------
// Query string
// ---------------------------------------------------------------------------

const QUERY = new URLSearchParams(window.location.search);
const MODULE_OVERRIDE = QUERY.get("module");

function flag(name) {
  const raw = QUERY.get(name);
  return raw === "1" || raw === "true" || raw === "yes" || raw === "on";
}

const CAPTURE = flag("capture");
/**
 * WF-LOOP r2 A2 — the ID PASS. `?capture=1&idpass=1` renders the SAME geometry
 * at the SAME camera with every part flooded with one flat colour per ROLE and
 * every shading term off. The PNG is a role mask of the judged still, which is
 * what lets `scripts/likeness.mjs` say "these render pixels are the awning" and
 * measure a colour, an area and a screen-space overlap without a human looking.
 * Ignored outside capture mode: the studio has the validator overlay instead.
 */
const IDPASS = CAPTURE && flag("idpass");
/**
 * Owner 2026-09-25 — the SHADED look still (`?capture=1&shade=1`): same camera and geometry as the flat
 * capture, lit so the SHAPE reads (faces facing the key are brighter). For humans and author seats only —
 * likeness never reads it (the flat capture stays the measured still).
 */
const SHADE = CAPTURE && !IDPASS && flag("shade");

/**
 * Role -> flat id colour, from the subject's class prior
 * (`classes/<class>.json` roleIdColours). CLOSED: `partsToGeometry` throws on a
 * role with no entry rather than letting an unnamed role inherit a neighbour's
 * mask. Set by compileModule() before anything is painted or reported.
 */
let roleIdColours = null;
/** WORKFLOW-V3 §7.10 — roles whose box is the front/side face quad (class prior likeness.faceRoles). */
let faceRoles = ["massing"];

// An unknown subject/view must NOT silently substitute another: a capture would
// then render one asset while the manifest reported a different one
// (studio.js:105-108).
function pick(requested, allowed, fallback, label) {
  if (requested === null || requested === "") return fallback;
  const ok = Array.isArray(allowed) ? allowed.includes(requested) : has(allowed, requested);
  if (ok) return requested;
  console.warn(`Unknown ${label} "${requested}"; using default "${fallback}".`);
  return fallback;
}

/** Relative, no scheme, no "..": a query string may not reach outside the served tree. */
function sanitiseSpecPath(raw) {
  if (!raw) return null;
  if (/^[a-z]+:/i.test(raw) || raw.startsWith("/") || raw.includes("..")) {
    console.warn(`Ignoring unsafe ?spec=${raw}`);
    return null;
  }
  return `./${raw.replace(/^\.\//, "")}`;
}

const state = {
  subject: pick(QUERY.get("subject"), SUBJECTS, DEFAULT_SUBJECT, "subject"),
  view: pick(QUERY.get("view"), VIEWS, DEFAULT_VIEW, "view"),
  seed: QUERY.get("seed") ?? null,
  // Dev-only: load any spec in the served tree, so a broken fixture can be
  // inspected in the overlay. Ignored under ?capture=1 — the capture URL must
  // stay (subject, view, seed, size) and nothing else.
  specPath: CAPTURE ? null : sanitiseSpecPath(QUERY.get("spec")),
  size: (() => {
    const raw = Number.parseInt(QUERY.get("size") ?? "", 10);
    return THREE.MathUtils.clamp(Number.isFinite(raw) ? raw : CAPTURE_SIZE_DEFAULT, 64, 4096);
  })(),
};

// ---------------------------------------------------------------------------
// Scene
// ---------------------------------------------------------------------------

const canvas = document.getElementById("scene");
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: true,
  preserveDrawingBuffer: true,
  powerPreference: "high-performance",
});
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;   // flat, matches the reference renders
renderer.setClearAlpha(0);

const scene = new THREE.Scene();
const stage = new THREE.Group();
scene.add(stage);

// Lighting rig: one hemisphere fill and one directional key, both at fixed
// positions in metres. No shadows in M0 — a shadow map is a second determinism
// surface and the target style has none in the massing pass.
//
// WF-LOOP r2 A1: NOT IN CAPTURE MODE. The judged still is compared with a flat
// three-value reference, and this rig (placed for the character studio) turned
// the populated face away from the key and rendered it at 0.51x its palette
// value. Under ?capture=1 the mesh is unlit `captureMaterial()` and neither
// light is ever added to the scene; the studio keeps both.
const hemisphere = new THREE.HemisphereLight(0xffffff, 0xdedad2, 0.90);
const key = new THREE.DirectionalLight(0xfff1dd, 1.85);
key.position.set(-24, 34, 27);
key.target.position.set(0, 0, 0);
if (!CAPTURE) {
  scene.add(hemisphere);
  scene.add(key);
  scene.add(key.target);
}
// Shade mode: a softer fill plus a key that rides the camera (upper left of the view), so for ANY solved camera
// the top reads brightest, the face turned toward the key next, the face turned away darkest.
const shadeFill = new THREE.HemisphereLight(0xffffff, 0xc4c0b8, 1.9);
const shadeKey = new THREE.DirectionalLight(0xffffff, 1.3);
if (SHADE) {
  scene.add(shadeFill);
  scene.add(shadeKey);
  scene.add(shadeKey.target);
}
function aimShadeKey(camera) {
  if (!SHADE) return;
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
  const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
  const back = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 2);
  const dir = back.multiplyScalar(0.55).add(up.multiplyScalar(0.8)).add(right.multiplyScalar(-0.45)).normalize();
  shadeKey.target.position.set(0, 0, 0);
  shadeKey.position.copy(dir.multiplyScalar(100));
}

const orthoCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
const perspectiveCamera = new THREE.PerspectiveCamera(26, 1, 0.1, 1000);

let mesh = null;
let controls = null;
let compiled = null;
let report = null;
/** Studio-only diagnostics. NEVER added to the scene in capture mode. */
let overlay = null;
let cameraSpec = PROVISIONAL_CAMERA;
let activeCamera = orthoCamera;

// ---------------------------------------------------------------------------
// Loading — fetch, never `import`, so a spec edit is a file edit and vite is
// not asked to hot-update a JSON module (08:G8). vite.config.js copies
// subjects/ and refs/ into dist/ so `preview` needs no network either.
// ---------------------------------------------------------------------------

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-cache" });
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

/**
 * A registered subject whose spec file has not landed yet (an LLM run that has
 * not been performed) must not take the studio down. It also must NOT silently
 * borrow another subject's spec — the capture manifest would then report one
 * asset and render another (see pick() above) — so the stand-in is a distinctly
 * named single box whose specHash can never be mistaken for the real one.
 */
function placeholderSpec(subject) {
  return {
    schema: "pg/1",
    subject: `${subject}__missing`,
    seed: 1,
    class: "prop",
    note: `Placeholder: no spec file for "${subject}" yet.`,
    palette: { missing: "#b0324a" },
    parts: [
      { id: "missing", prim: "bevelBox", dims: [0.5, 0.5, 0.5], ground: true, role: "placeholder", zone: "missing" },
    ],
  };
}

async function loadSpec() {
  const url = state.specPath ?? SUBJECT_SPECS[state.subject];
  try {
    return await loadJson(url);
  } catch (error) {
    console.warn(`No spec at ${url} (${error.message}); using the missing-spec placeholder.`);
    return placeholderSpec(state.subject);
  }
}

async function loadCamera(subject, url = `./refs/${subject}.camera.json`) {
  try {
    return await loadJson(url);
  } catch {
    console.warn(`No refs/${subject}.camera.json; using provisional theta/phi.`);
    return PROVISIONAL_CAMERA;
  }
}

// ---------------------------------------------------------------------------
// Framing
// ---------------------------------------------------------------------------

function boundsCentre(bounds) {
  return new THREE.Vector3().fromArray(bounds.centre);
}

/**
 * The judged view. Orthographic, so a facade's proportions cannot be argued
 * away by perspective; theta/phi come off the frozen TARGET, never assumed.
 */
function frameTarget(bounds) {
  const centre = boundsCentre(bounds);
  const theta = THREE.MathUtils.degToRad(cameraSpec.theta_deg);   // elevation
  const azimuthOffset = VIEWS[state.view].azimuthOffsetDeg ?? 0;
  const phi = THREE.MathUtils.degToRad(cameraSpec.phi_deg + azimuthOffset);   // azimuth

  const offset = new THREE.Vector3().setFromSphericalCoords(100, Math.PI / 2 - theta, phi);
  orthoCamera.position.copy(centre).add(offset);
  orthoCamera.up.set(0, 1, 0);
  orthoCamera.lookAt(centre);

  // DEVIATION: the brief sizes the square frustum as `AABB height / 0.86`. That
  // is only the same thing as an 0.86 fill when height dominates the PROJECTION,
  // which holds for a character and not for a 17 m wide terrace seen at 45deg —
  // taken literally it crops the tenement to a solid wall of colour. The rule
  // implemented is the one the number means: fit the projected AABB, then divide
  // by 0.86. Deterministic (eight corners through the camera matrix, no pixels
  // read back) and identical to the literal rule whenever height dominates.
  orthoCamera.updateMatrixWorld(true);
  const toCamera = new THREE.Matrix4().copy(orthoCamera.matrixWorld).invert();
  const min = new THREE.Vector3().fromArray(bounds.min);
  const max = new THREE.Vector3().fromArray(bounds.max);
  const corner = new THREE.Vector3();
  let extentX = 0;
  let extentY = 0;
  for (let i = 0; i < 8; i += 1) {
    corner.set(i & 1 ? max.x : min.x, i & 2 ? max.y : min.y, i & 4 ? max.z : min.z)
      .applyMatrix4(toCamera);
    extentX = Math.max(extentX, Math.abs(corner.x));
    extentY = Math.max(extentY, Math.abs(corner.y));
  }
  const half = Math.max(extentX, extentY) / FILL;

  orthoCamera.left = -half;
  orthoCamera.right = half;
  orthoCamera.top = half;
  orthoCamera.bottom = -half;
  orthoCamera.near = 1;
  orthoCamera.far = 400;
  orthoCamera.updateProjectionMatrix();
  return orthoCamera;
}

/** The human view: a long-lens three-quarter, framed off the bounding sphere. */
function frameThreeQuarter(bounds) {
  const view = VIEWS.threeQuarter;
  const centre = boundsCentre(bounds);
  const radius = Math.hypot(bounds.w, bounds.h, bounds.d) / 2;
  const fov = THREE.MathUtils.degToRad(view.fov);
  const distance = (radius / Math.sin(fov / 2)) * 1.02;

  const yaw = THREE.MathUtils.degToRad(view.yawDeg);
  const pitch = THREE.MathUtils.degToRad(view.pitchDeg);
  perspectiveCamera.fov = view.fov;
  perspectiveCamera.position.copy(centre).add(
    new THREE.Vector3().setFromSphericalCoords(distance, Math.PI / 2 - pitch, yaw),
  );
  perspectiveCamera.up.set(0, 1, 0);
  perspectiveCamera.lookAt(centre);
  perspectiveCamera.aspect = 1;
  perspectiveCamera.updateProjectionMatrix();
  return perspectiveCamera;
}

function frame(bounds) {
  return VIEWS[state.view].kind === "ortho" ? frameTarget(bounds) : frameThreeQuarter(bounds);
}

// ---------------------------------------------------------------------------
// r3 C2.1 — the massing's FRONT and SIDE faces, projected to capture pixels.
//
// LK_AREA compares the TARGET's front plane with the RENDER's front plane
// (WF-LOOP-R3 C2.2). The target quad is measured off the reference image; the
// render quad is not measurable from pixels (a flat capture has no corner
// marks) but it is exactly computable here, at the one place that holds both
// the solved camera and the solid: `frameTarget` already pushes the eight AABB
// corners through the camera matrix, so this is the same arithmetic carried one
// step further to NDC and then to pixels.
// ---------------------------------------------------------------------------

const px2 = (x) => Math.round(x * 100) / 100;
const m3 = (x) => Math.round(x * 1000) / 1000;

function projectToPx(point, camera, size) {
  const ndc = point.clone().project(camera);
  return [px2(((ndc.x + 1) / 2) * size), px2(((1 - ndc.y) / 2) * size)];
}

/** The AABB of every part whose role is `massing`; the whole model if none is. */
function massingBox(parts, bounds) {
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  let n = 0;
  for (const part of parts ?? []) {
    if (!faceRoles.includes(part.role) || !part.aabb) continue;
    n += 1;
    for (let k = 0; k < 3; k += 1) {
      min[k] = Math.min(min[k], part.aabb.min[k]);
      max[k] = Math.max(max[k], part.aabb.max[k]);
    }
  }
  if (n === 0) return { min: bounds.min.slice(), max: bounds.max.slice(), from: "model bounds (no massing part)" };
  return { min, max, from: `${n} massing part(s)` };
}

/**
 * One face of that box, as four screen points ordered counter-clockwise around
 * their own centroid (so the quad is a polygon a point-in-polygon test can use,
 * whatever the camera does).
 */
function faceQuad(box, axis, sign, camera, size) {
  const other = [0, 1, 2].filter((k) => k !== axis);
  const world = [];
  for (const a of [0, 1]) {
    for (const b of [0, 1]) {
      const c = [0, 0, 0];
      c[axis] = sign > 0 ? box.max[axis] : box.min[axis];
      c[other[0]] = a ? box.max[other[0]] : box.min[other[0]];
      c[other[1]] = b ? box.max[other[1]] : box.min[other[1]];
      world.push(c);
    }
  }
  const px = world.map((c) => projectToPx(new THREE.Vector3().fromArray(c), camera, size));
  const cx = px.reduce((s, p) => s + p[0], 0) / 4;
  const cy = px.reduce((s, p) => s + p[1], 0) / 4;
  const order = px
    .map((p, i) => ({ i, a: Math.atan2(p[1] - cy, p[0] - cx) }))
    .sort((m, n) => m.a - n.a)
    .map((o) => o.i);
  const xs = px.map((p) => p[0]);
  const ys = px.map((p) => p[1]);
  return {
    axis: `${sign > 0 ? "+" : "-"}${"xyz"[axis]}`,
    px: order.map((i) => px[i]),
    world: order.map((i) => world[i].map(m3)),
    bbox: { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) },
  };
}

/**
 * The populated face is built on -Z (the FRONT contract in kernel/toThree.mjs)
 * and turned by `frontRotationDeg` before it is measured, so the front normal is
 * that vector turned the same way. The SIDE face is the other horizontal face
 * of the box that this camera can see.
 */
function faceQuads(solved, camera, size, turnDeg, front = "-Z") {
  const box = massingBox(solved.parts, solved.bounds);
  // WORKFLOW-V3 §7.10 — the DECLARED front (a vehicle presents "+X"), turned like the render.
  const FRONT_VECTORS = { "-Z": [0, 0, -1], "+Z": [0, 0, 1], "+X": [1, 0, 0], "-X": [-1, 0, 0] };
  const frontKey = String(front ?? "-Z").trim().toUpperCase().replace(/^Z$/, "+Z");
  const n = new THREE.Vector3(...(FRONT_VECTORS[frontKey] ?? FRONT_VECTORS["-Z"]))
    .applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(turnDeg ?? 0));
  const frontAxis = Math.abs(n.x) >= Math.abs(n.z) ? 0 : 2;
  const frontSign = (frontAxis === 0 ? n.x : n.z) >= 0 ? 1 : -1;
  const sideAxis = frontAxis === 0 ? 2 : 0;
  const forward = camera.getWorldDirection(new THREE.Vector3());
  const sideSign = forward.getComponent(sideAxis) < 0 ? 1 : -1;
  return {
    frontQuad: { ...faceQuad(box, frontAxis, frontSign, camera, size), source: box.from },
    sideQuad: { ...faceQuad(box, sideAxis, sideSign, camera, size), source: box.from },
    massingBoxM: { min: box.min.map(m3), max: box.max.map(m3) },
  };
}

// ---------------------------------------------------------------------------
// Build
// ---------------------------------------------------------------------------

// V2: BEGIN kernel-module compile. Returns the same {spec, hash} pair the spec
// V2: path returns, where `spec` is the little descriptor the capture manifest
// V2: needs (subject, seed) and `hash` is hash32 of the module SOURCE TEXT —
// V2: the module text is the seed artifact, so it replaces specHash (plan 2).
async function moduleSourceHash(url) {                                           // V2:
  try {                                                                          // V2:
    const response = await fetch(url, { cache: "no-cache" });                    // V2:
    if (!response.ok) throw new Error(`${response.status} ${url}`);              // V2:
    const text = await response.text();                                          // V2:
    return `h32:${hash32(text).toString(16).padStart(8, "0")}`;                  // V2:
  } catch (error) {                                                              // V2:
    console.warn(`No module text at ${url} (${error.message}); hashing the path.`); // V2:
    return `h32:${hash32(url).toString(16).padStart(8, "0")}`;                   // V2:
  }                                                                              // V2:
}                                                                                // V2:

// V5-4 item 3 — PER-FACE PALETTE. The face-orientation rule of scripts/project.mjs faceOf (render frame, after the
// front turn): top n.y > 0.5, bottom n.y < -0.5 (painted as side), else front |n.x| >= |n.z|, else side.
const FACE_NAMES = ["top", "front", "side", "side"];
function faceIndex(nx, ny, nz) {
  const l = Math.hypot(nx, ny, nz) || 1;
  if (ny / l > 0.5) return 0;
  if (ny / l < -0.5) return 3;
  return Math.abs(nx) >= Math.abs(nz) ? 1 : 2;
}
const faceColour = (entry, fid) => entry[FACE_NAMES[fid]] ?? entry.front ?? entry.side ?? entry.top;

/** The palette with every per-face entry reduced to one hex (its front) for the kernel painter. */
function flatPalette(palette = {}) {
  return Object.fromEntries(Object.entries(palette).map(([k, v]) => [k, v && typeof v === "object" ? faceColour(v, 1) : v]));
}

/**
 * Repaint the zones whose palette entry is {top, front, side}: every triangle of such a part takes its face's colour
 * FLAT (the target's cel faces already carry their light: no AO / tint / jitter on top). MVP-STUB: flat in the studio
 * too. The merged geometry is non-indexed, parts in order, compiled.parts[i].triCount triangles each.
 */
function applyFacePalette(compiledGeometry, palette = {}) {
  const faces = Object.fromEntries(Object.entries(palette).filter(([, v]) => v && typeof v === "object"));
  if (!Object.keys(faces).length) return;
  const geometry = compiledGeometry.geometry;
  const pos = geometry.getAttribute("position");
  const col = geometry.getAttribute("color");
  if (!pos || !col || geometry.index) return;
  const c = new THREE.Color();
  let v0 = 0;
  for (const part of compiledGeometry.parts) {
    const n = part.triCount * 3;
    const entry = faces[part.zone];
    if (entry) {
      for (let v = v0; v < v0 + n; v += 3) {
        const ax = pos.getX(v), ay = pos.getY(v), az = pos.getZ(v);
        const ux = pos.getX(v + 1) - ax, uy = pos.getY(v + 1) - ay, uz = pos.getZ(v + 1) - az;
        const wx = pos.getX(v + 2) - ax, wy = pos.getY(v + 2) - ay, wz = pos.getZ(v + 2) - az;
        c.set(faceColour(entry, faceIndex(uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx)));
        for (let k = 0; k < 3; k += 1) col.setXYZ(v + k, c.r, c.g, c.b);
      }
    }
    v0 += n;
  }
  col.needsUpdate = true;
}

async function compileModule() {                                                 // V2:
  // WORKFLOW-V3 §7.5 — the subject manifest and its class prior, fetched like any data.
  const manifest = await loadJson(`./subjects/${state.subject}/subject.json`);
  const cls = await loadJson(`./classes/${manifest.class}.json`);
  const paths = manifest.paths ?? {};
  const url = MODULE_OVERRIDE ? `./${MODULE_OVERRIDE}` : `./${paths.module}`;
  const loader = MODULE_OVERRIDE ? REF_MODULES[`../${MODULE_OVERRIDE}`] : SUBJECT_MODULES[`../${paths.module}`]; // V2:
  if (!loader) throw new Error(`subject "${state.subject}" has no module at ${paths.module}`); // V2:
  const rulesLoader = CLASS_RULES[`./${String(cls.rules ?? "").replace(/^src\//, "")}`];
  if (!rulesLoader) throw new Error(`class "${manifest.class}" names no loadable rules module (${cls.rules})`);
  const rules = await rulesLoader();
  roleIdColours = cls.roleIdColours ?? null;
  faceRoles = cls.likeness?.faceRoles ?? ["massing"];
  const mod = await loader();                                                    // V2:
  await K.init();                                                                // V2:
  if (typeof mod.build !== "function") throw new Error(`${url}: no exported build()`); // V2:
  const parts = mod.build();                                                     // V2:
  const violations = K.checkParts(mod.meta, parts);                              // V2:
  if (violations.length > 0) throw new Error(`${url}: ${violations[0]}`);         // V2:
  const seed = state.seed !== null && state.seed !== ""                          // V2:
    ? (Number.isNaN(Number(state.seed)) ? state.seed : Number(state.seed))       // V2:
    : mod.meta.seed;                                                             // V2:
  cameraSpec = await loadCamera(state.subject, paths.camera ? `./${paths.camera}` : undefined); // V2:
  // V2: r1 row 1 — the author builds the populated face on -Z; the RENDER turns
  // V2: that face onto +X, which is the only side of this camera whose
  // V2: horizontals rise to screen-right (see src/kernel/toThree.mjs). The
  // V2: validators below deliberately get the UNROTATED parts: every V11/V12
  // V2: row measures "along the facade" as x, which only holds in the author
  // V2: frame, and a rigid quarter turn changes nothing else they measure.
  const turn = frontRotationDeg(mod.meta.front);                                 // V2:
  // V5-4 item 3: a palette entry may be {top, front, side}; the kernel painter takes one hex per zone (the front),
  // applyFacePalette then repaints those zones by face normal.
  compiled = partsToGeometry(parts, flatPalette(mod.meta.palette), seed, {         // V2:
    frontRotationDeg: turn,                                                      // V2:
    shade: mod.meta.shade,                                                       // V2:
    idPalette: IDPASS ? roleIdColours : null,            // r2 A2: role mask pass // V2:
  });                                                                            // V2:
  if (!IDPASS) applyFacePalette(compiled, mod.meta.palette);
  compiled.solved.subject = state.subject;                                       // V2:
  compiled.front = mod.meta.front ?? "-Z";
  // V2: S2 — the real chain (V1' V5 V2' V3' V6' V4 V7 V11 V12 V10) on the kernel
  // V2: solids. It is async (three-mesh-bvh builds a tree per part), which is why
  // V2: the whole module path is awaited; the capture manifest below reports its
  // V2: verdict instead of the S1 placeholder, so a still can never be captured
  // V2: from a model nobody measured.
  // V2: r1 row 4 — the frozen contents count is DATA beside the module, fetched
  // V2: the same way a spec is; a subject without one simply skips V12.
  const census = paths.census ? await loadJson(`./${paths.census}`).catch(() => null) : null; // V2:
  const layout = paths.layout ? await loadJson(`./${paths.layout}`).catch(() => null) : null; // V2: r2 B2
  report = await validateParts(mod.meta, parts, undefined, { census, layout, cls, rules }); // V2:
  return { spec: { subject: state.subject, seed, class: mod.meta.class, palette: mod.meta.palette }, hash: await moduleSourceHash(url) }; // V2:
}                                                                                // V2:
// V2: END kernel-module compile.

async function rebuild() {
  let spec;                                                                      // V2:
  let hash;                                                                      // V2:
  if (!state.specPath && MODULE_SUBJECTS.includes(state.subject)) {              // V2:
    ({ spec, hash } = await compileModule());                                    // V2:
  } else {                                                                       // V2:
  spec = await loadSpec();
  if (state.seed !== null && state.seed !== "") spec.seed = Number.isNaN(Number(state.seed)) ? state.seed : Number(state.seed);
  cameraSpec = await loadCamera(state.subject);

  compiled = compile(spec);
  // compiled.spec is the EFFECTIVE spec: composites expanded, facade grammar
  // parts appended. The overlay and the validators must read that, not the file.
  const effective = compiled.spec;
  report = validate(effective, compiled.solved, { geometry: compiled.geometry, prims: buildPrims(effective) });
  hash = specHash(spec);                                                         // V2:
  }                                                                              // V2:

  if (mesh) {
    stage.remove(mesh);
    mesh.geometry.dispose();
    mesh.material.dispose();
  }
  // r2 A1 — capture is FLAT and unlit; the studio keeps the PBR material.
  mesh = new THREE.Mesh(compiled.geometry, CAPTURE && !SHADE ? captureMaterial() : assetMaterial());
  mesh.name = spec.subject;
  stage.add(mesh);

  // The key aims at the subject so the AO ramp and the lit ramp agree.
  key.target.position.copy(boundsCentre(compiled.solved.bounds));
  key.target.updateMatrixWorld();

  // V2: the overlay reads prim/dims/matrix, which a kernel module has none of;
  // V2: its replacement is the S2 kernel chain, so module subjects skip it.
  if (!CAPTURE && compiled.spec) drawOverlay(compiled.solved, report);
  activeCamera = frame(compiled.solved.bounds);
  return { spec, hash };                                                         // V2:
}

// ---------------------------------------------------------------------------
// Validator overlay — STUDIO ONLY.
//
// Every line of it lives in one THREE.Group that is never constructed under
// ?capture=1, so the judged pixels cannot contain a diagnostic. Orphans and
// unstable masses tint red, under-size parts yellow, and each failed contact
// draws the gap as a segment from the child's contact face to the parent
// surface it claims to touch.
// ---------------------------------------------------------------------------

const OVERLAY_COLOURS = Object.freeze({
  V2: 0xff8a1f, V3: 0xff2d2d, V4: 0xff2d2d, V5: 0xffd23d, V6: 0xff5ad2, V7: 0xffd23d, V10: 0xffd23d,
});

function disposeOverlay() {
  if (!overlay) return;
  scene.remove(overlay);
  overlay.traverse((object) => {
    if (object.geometry) object.geometry.dispose();
    if (object.material) object.material.dispose();
  });
  overlay = null;
}

function tintBox(part, colour) {
  const group = new THREE.Group();
  const geometry = new THREE.BoxGeometry(part.dims[0], part.dims[1], part.dims[2]);
  geometry.translate(0, part.dims[1] / 2, 0);          // prims.js local frame
  const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
    color: colour, transparent: true, opacity: 0.3, depthWrite: false,
  }));
  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry),
    new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity: 0.9, depthTest: false }),
  );
  group.add(mesh, edges);
  group.applyMatrix4(new THREE.Matrix4().fromArray(part.matrix));
  return group;
}

/** From the child's contact-face centre to the parent surface it declares. */
function gapVector(child, parent, colour) {
  const parentBox = partBox(parent);
  const childBox = partBox(child);
  const n = faceVector(parentBox, child.face, "n");
  const from = childBox.centre.clone().addScaledVector(n, -projRadius(childBox, n));
  const surface = parentBox.centre.clone().addScaledVector(n, projRadius(parentBox, n));
  const to = from.clone().addScaledVector(n, surface.clone().sub(from).dot(n));
  if (from.distanceTo(to) < 1e-4) return null;
  const geometry = new THREE.BufferGeometry().setFromPoints([from, to]);
  return new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: colour, depthTest: false }));
}

function drawOverlay(solved, validatorReport) {
  disposeOverlay();
  if (CAPTURE || validatorReport.violations.length === 0) return;

  overlay = new THREE.Group();
  overlay.name = "validator-overlay";

  const byId = new Map(solved.parts.map((part) => [part.id, part]));
  const bySpecId = new Map();
  for (const part of solved.parts) {
    if (!bySpecId.has(part.specId)) bySpecId.set(part.specId, []);
    bySpecId.get(part.specId).push(part);
  }

  for (const violation of validatorReport.violations) {
    const colour = OVERLAY_COLOURS[violation.v] ?? 0xff2d2d;
    const ids = (violation.overlayIds ?? [violation.part]).filter(Boolean);
    const targets = ids.flatMap((id) => (byId.has(id) ? [byId.get(id)] : bySpecId.get(id) ?? []));
    for (const part of targets) overlay.add(tintBox(part, colour));
    if (violation.v === "V2") {
      for (const part of targets) {
        const parent = part.parentId ? byId.get(part.parentId) : null;
        const segment = parent ? gapVector(part, parent, colour) : null;
        if (segment) overlay.add(segment);
      }
    }
  }

  overlay.renderOrder = 10;
  scene.add(overlay);
}

// ---------------------------------------------------------------------------
// Capture mode — one frame, then the flags, then nothing else ever happens.
// ---------------------------------------------------------------------------

async function runCapture() {
  document.body.dataset.mode = "capture";
  const size = state.size;

  renderer.setPixelRatio(1);            // never devicePixelRatio: a machine variable
  renderer.setSize(size, size, true);
  perspectiveCamera.aspect = 1;

  const { spec, hash } = await rebuild();
  activeCamera.updateProjectionMatrix();
  activeCamera.updateMatrixWorld(true);
  aimShadeKey(activeCamera);
  scene.updateMatrixWorld(true);
  renderer.render(scene, activeCamera);

  const bounds = compiled.solved.bounds;
  // r3 C2.1 — the front/side face quads of the massing, in this still's pixels.
  let quads = { frontQuad: null, sideQuad: null, massingBoxM: null };
  try {
    quads = faceQuads(compiled.solved, activeCamera, size, compiled.frontRotationDeg ?? 0, compiled.front);
  } catch (error) {
    console.warn(`face quads not emitted: ${error.message}`);
  }
  window.__CAPTURE_MANIFEST__ = {
    triangles: compiled.solved.triangles,
    materials: 1,
    drawCalls: 1,
    boundsM: { w: bounds.w, h: bounds.h, d: bounds.d, minY: bounds.minY },
    // r3 C2.1 — the massing's front-face and side-face corners at this camera,
    // in pixels of THIS still, so likeness.mjs can compare the target's front
    // plane with the render's front plane instead of two whole pictures.
    frontQuad: quads.frontQuad,
    sideQuad: quads.sideQuad,
    massingBoxM: quads.massingBoxM,
    subject: state.subject,
    view: state.view,
    seed: spec.seed,
    size,
    specHash: hash,
    dslVersion: DSL_VERSION,
    validatorPass: report.pass,
    // V2: r1 row 1 — the turn applied between the author frame and this frame,
    // so a still carries the proof of which way it was pointed.
    frontRotationDeg: compiled.frontRotationDeg ?? 0,
    // r2 A1/A2 — what this still IS, so a PNG carries its own provenance.
    lit: false,
    idpass: IDPASS,
    idColours: IDPASS ? roleIdColours : null,
    // r2 A1/A4 — the palette this still was painted from, so likeness.mjs can
    // say "the front face renders at 0.97 of its palette hex" without importing
    // the module or parsing it.
    palette: spec.palette ?? null,
    violationCount: report.violations.length,
    violations: report.text,   // V2: the <= 8 line report, so a still carries its own verdict
    repairCount: 0,
    v8Dropped: 0,           // V8 lands in M2; nothing is dropped in M0.
    cameraId: VIEWS[state.view].kind === "ortho"
      ? `ortho:theta${cameraSpec.theta_deg}:phi${cameraSpec.phi_deg + (VIEWS[state.view].azimuthOffsetDeg ?? 0)}${cameraSpec.provisional ? ":provisional" : ""}`
      : `persp:${VIEWS[state.view].yawDeg}/${VIEWS[state.view].pitchDeg}/${VIEWS[state.view].fov}`,
  };
  window.__CAPTURE_READY__ = true;
  document.body.dataset.captureReady = "1";
}

// ---------------------------------------------------------------------------
// Studio mode
// ---------------------------------------------------------------------------

const dom = {
  subjects: document.getElementById("subjects"),
  views: document.getElementById("views"),
  stats: document.getElementById("stats"),
  report: document.getElementById("report"),
  exportGlb: document.getElementById("export-glb"),
  status: document.getElementById("status"),
  viewport: document.getElementById("viewport"),
};

function row(label, value) {
  return `<div class="row"><span>${label}</span><strong>${value}</strong></div>`;
}

function paintPanel() {
  const solved = compiled.solved;
  const b = solved.bounds;
  dom.stats.innerHTML = [
    row("triangles", solved.triangles),
    row("parts", solved.parts.length),
    row("materials", 1),
    row("draw calls", 1),
    row("bounds w x h x d", `${b.w} x ${b.h} x ${b.d} m`),
    row("min y", b.minY),
    row("camera", cameraSpec.provisional ? "provisional" : "measured"),
  ].join("");
  dom.report.textContent = report.text;
  dom.report.className = report.pass ? "good" : "bad";
}

function buildButtons(container, entries, current, onPick) {
  container.innerHTML = "";
  for (const [id, label] of entries) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("aria-pressed", String(id === current));
    button.addEventListener("click", () => onPick(id));
    container.appendChild(button);
  }
}

function resizeToViewport() {
  const width = Math.max(1, dom.viewport.clientWidth);
  const height = Math.max(1, dom.viewport.clientHeight);
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.setSize(width, height, false);
  perspectiveCamera.aspect = width / height;
  perspectiveCamera.updateProjectionMatrix();
  if (compiled) {
    const aspect = width / height;
    const half = compiled.solved.bounds.h / FILL / 2;
    orthoCamera.left = -half * aspect;
    orthoCamera.right = half * aspect;
    orthoCamera.updateProjectionMatrix();
  }
}

async function runStudio() {
  document.body.dataset.mode = "studio";
  await rebuild();

  controls = new OrbitControls(activeCamera, canvas);
  controls.enableDamping = true;
  controls.target.copy(boundsCentre(compiled.solved.bounds));

  buildButtons(
    dom.subjects,
    SUBJECTS.map((id) => [id, id]),
    state.subject,
    async (id) => { state.subject = id; await refresh(); },
  );
  buildButtons(
    dom.views,
    Object.entries(VIEWS).map(([id, v]) => [id, v.label]),
    state.view,
    async (id) => { state.view = id; await refresh(); },
  );

  dom.exportGlb.addEventListener("click", () => window.__exportGLB());
  window.addEventListener("resize", resizeToViewport);

  resizeToViewport();
  paintPanel();

  renderer.setAnimationLoop(() => {
    if (controls) controls.update();
    renderer.render(scene, activeCamera);
  });
}

async function refresh() {
  await rebuild();
  if (controls) {
    controls.object = activeCamera;
    controls.target.copy(boundsCentre(compiled.solved.bounds));
    controls.update();
  }
  buildButtons(dom.subjects, SUBJECTS.map((id) => [id, id]), state.subject, async (id) => { state.subject = id; await refresh(); });
  buildButtons(dom.views, Object.entries(VIEWS).map(([id, v]) => [id, v.label]), state.view, async (id) => { state.view = id; await refresh(); });
  resizeToViewport();
  paintPanel();
}

/** Studio-only export hook; the capture page never touches it. */
window.__exportGLB = async function exportGLB() {
  if (!mesh) return null;
  dom.status.textContent = "exporting…";
  try {
    await exportGlb(mesh, `${state.subject}.glb`);
    dom.status.textContent = `wrote ${state.subject}.glb`;
  } catch (error) {
    dom.status.textContent = `export failed: ${error.message}`;
    throw error;
  }
  return true;
};

const boot = CAPTURE ? runCapture() : runStudio();
boot.catch((error) => {
  console.error(error);
  if (!CAPTURE) dom.report.textContent = `BUILD FAILED: ${error.message}`;
});
