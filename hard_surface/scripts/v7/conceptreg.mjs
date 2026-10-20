// WF v10 — the concept registration of ANY subject, vehicle or direct class, without touching the eyes
// (scripts/registered.mjs / project.mjs stay byte-identical: gold.config.json `eyes` hashes them per round).
//
// scripts/registered.mjs registration() knows two classes (vehicle, building): its anchorFace() throws for a third.
// A `pipeline: "direct"` class (classes/weapon.json) has no ground quad to solve a camera from and no template body, so:
//   camera  = the style's fixed isometric (30 deg elevation, 45 deg azimuth from front-left: every scripts/v7/styles.json
//             text starts with that sentence) — subjects/<s>/camera.json, written by gold.mjs new;
//   s/ox/oy = the object's camera-plane extent fitted to the concept's foreground box (hull.mjs --write-frame: the
//             facts.json dims box before the first turnaround, the registered visual hull after install), stored as
//             layout.measured.json `_frame.fit` next to the usual `_frame.quadPx`.
// conceptRegistration() returns the registered.mjs registration() shape, so hull.mjs / turnaround.mjs / the HS harness
// read it like a vehicle's. For a vehicle / building it IS project.mjs subjectRegistration() (unchanged).
import fs from "node:fs";
import path from "node:path";

import { ROOT, loadSubject } from "../subject.mjs";
import { subjectRegistration } from "../project.mjs";
import { anchorFace, cameraBasis, subjectFront } from "../registered.mjs";

export const DIRECT_CLASSES = Object.freeze(["weapon"]);
export const FIXED_ISO = Object.freeze({ theta_deg: 30, phi_deg: 45 });
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** A class registered.mjs has no anchor for: its concept registration is the fixed-isometric one of this file. */
export const isDirectClass = (S) => DIRECT_CLASSES.includes(S.klass);
/** subject.json `pipeline: "direct"` (or the class's): no gold rounds, the HS build is made straight from the sources. */
export const isDirectPipeline = (S) => (S.subject.pipeline ?? S.cls.pipeline) === "direct";

export function factsDims(subjectId) {
  const f = path.join(ROOT, "subjects", subjectId, "turnaround", "facts.json");
  const d = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")).dims : null;
  if (!(d?.L > 0 && d?.W > 0 && d?.H > 0)) throw new Error(`conceptreg: subjects/${subjectId}/turnaround/facts.json has no dims {L, W, H}`);
  return d;
}

/** The anchor face: registered.mjs anchorFace for its classes; a direct class = the +X flank of the facts.json dims box. */
export function anchorFaceOf(S) {
  if (!isDirectClass(S)) return anchorFace(S);
  const { L, W, H } = factsDims(S.id);
  const x = W / 2;
  return { corners: [[x, H, L / 2], [x, H, -L / 2], [x, 0, -L / 2], [x, 0, L / 2]], L, W, H, ref: L, lengthAxis: [0, 0, 1],
    why: `${S.klass} +X flank of the facts.json dims box, L ${L} x W ${W} x H ${H} m` };
}

/** The render turn's front: a direct class is built in the vehicle frame (flank +X presented, muzzle / nose +Z). */
export const subjectFrontOf = (S) => (isDirectClass(S) ? "+X" : subjectFront(S));

/** The registration (registered.mjs registration() shape) of a subject's concept. */
export function conceptRegistration(subjectId) {
  const S = loadSubject(subjectId);
  if (!isDirectClass(S)) return subjectRegistration(subjectId);
  const measured = S.readJson("layoutMeasured");
  const fit = measured?._frame?.fit, quad = measured?._frame?.quadPx;
  if (!(fit?.s > 0) || !Array.isArray(quad) || quad.length !== 4) throw new Error(`conceptreg: ${S.rel.layoutMeasured} has no _frame.fit / quadPx (node scripts/v7/hull.mjs --subject ${subjectId} --write-frame [--from facts])`);
  if (!S.paths.camera || !fs.existsSync(S.paths.camera)) throw new Error(`conceptreg: no ${S.rel.camera} (gold.mjs new writes the fixed isometric for class ${S.klass})`);
  const camera = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
  const basis = cameraBasis(camera);
  const target = { w: 1024, h: 1024 };
  try { const head = fs.readFileSync(S.paths.target); target.w = head.readUInt32BE(16); target.h = head.readUInt32BE(20); } catch { /* keep 1024 */ }
  const { s, ox, oy } = fit;
  return { s, ox, oy, rmsPx: 0, turnDeg: 0, basis, camera, anchor: anchorFaceOf(S), quadPx: quad, targetW: target.w, targetH: target.h,
    toTarget: (p) => [s * dot(p, basis.right) + ox, -s * dot(p, basis.up) + oy] };
}
