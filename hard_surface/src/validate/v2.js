// V2 — the declared contact is real.
//
// M5: `hangs-below` is measured by the flush rule below — its algebra IS the
// flush algebra on the parent's -Y face, so |d| <= EPS on >= 90 % of samples is
// exactly the right test for it. `embedded` is not a surface contact at all and
// takes the volume branch at the top of the loop.
//
// SCOPE (M1 ruling, see report): V2 validates ONE contact per spec part — the
// anchor instance, the only one `attach` actually describes. Where a `repeat`
// or `mirror` instance ends up is a global-layout question and belongs to V3;
// checking every instance here would make the same physical fault report twice
// under two different V-codes.
import * as THREE from "three";

import { partBox, projRadius, penetrationAlong, faceVector, axisLabel, aabbOverlapVolume, aabbVolume } from "./obb.js";

/** 5 x 5 over the shared face region, inset so a bevelled corner is not the test. */
const FRACTIONS = [0.1, 0.3, 0.5, 0.7, 0.9];

/**
 * @returns {{violations:Array, advisories:Array, measurements:Map<string,object>}}
 *   `measurements` is what repair.js reads: per spec-part id, the signed
 *   shortfall `d` in metres and the direction that closes it.
 */
export function validateV2(ctx, make) {
  const { spec, byId, limits, EPS } = ctx;
  const violations = [];
  const measurements = new Map();

  for (const part of spec.parts) {
    if (!part.attach) continue;
    const child = byId.get(part.id);
    const parent = byId.get(part.attach.to);
    if (!child || !parent) continue;   // V0 already said so

    // `embedded` is not a surface contact: the child lives INSIDE the parent, so
    // the thing to measure is how much of the child the parent actually contains
    // (PLAN 2: child volume n parent >= 50 %). Sampling a contact face here would
    // measure a face that is nowhere near the parent's surface.
    // MVP-STUB: AABB n AABB, like V6 — exact for the rot = 0 layouts M5 authors,
    // and it over-reports containment for a rotated child, never under-reports.
    if (child.contact === "embedded") {
      const childVolume = aabbVolume(child);
      const frac = childVolume > 0 ? aabbOverlapVolume(child, parent) / childVolume : 0;
      measurements.set(part.id, { d: 0, median: frac, gap: 0, embed: child.embed, contact: child.contact,
        parent: part.attach.to, containedFrac: frac });
      if (frac < limits.embeddedMinFrac - 1e-9) {
        violations.push(make("V2", part.id, `${(frac * 100).toFixed(1)}% of "${part.id}" inside "${part.attach.to}"`,
          `>= ${(limits.embeddedMinFrac * 100).toFixed(0)}%`,
          `push "${part.id}" further into "${part.attach.to}" (declared embedded, embed ${fmt(child.embed)} m) or shrink it — only ${(frac * 100).toFixed(1)}% of it is inside its parent`));
      }
      continue;
    }

    const parentBox = partBox(parent);
    const childBox = partBox(child);
    const n = faceVector(parentBox, child.face, "n");
    const u = faceVector(parentBox, child.face, "u");
    const v = faceVector(parentBox, child.face, "v");

    const halfN = projRadius(parentBox, n);
    const halfU = projRadius(parentBox, u);
    const halfV = projRadius(parentBox, v);
    const faceCentre = parentBox.centre.clone().addScaledVector(n, halfN);

    // The child's contact face is the one whose outward normal is -n.
    const childHalfN = projRadius(childBox, n);
    const childFace = childBox.centre.clone().addScaledVector(n, -childHalfN);
    const childHalfU = projRadius(childBox, u);
    const childHalfV = projRadius(childBox, v);

    const rel = childFace.clone().sub(faceCentre);
    const cu = rel.dot(u);
    const cv = rel.dot(v);
    const cn = rel.dot(n);

    // MVP-STUB: a rotated child is clipped by its u/v bounding interval, not by
    // its exact rotated rectangle. Every M0 spec has rot = 0, where the two agree.
    const loU = Math.max(cu - childHalfU, -halfU);
    const hiU = Math.min(cu + childHalfU, halfU);
    const loV = Math.max(cv - childHalfV, -halfV);
    const hiV = Math.min(cv + childHalfV, halfV);

    if (hiU - loU <= 1e-9 || hiV - loV <= 1e-9) {
      const shortU = Math.max(0, loU - hiU);
      const shortV = Math.max(0, loV - hiV);
      const axis = shortV >= shortU ? axisLabel(v) : axisLabel(u);
      const slide = Math.max(shortU, shortV, Math.min(2 * childHalfU, 2 * childHalfV) * 0.5);
      violations.push(make("V2", part.id, "0.000 m2 shared contact area", "> 0 m2",
        `slide ${part.id} ${fmt(slide)} m along ${axis} onto "${part.attach.to}" ${child.face} — its contact face shares no area with that face (change attach.uv or attach.align)`));
      continue;
    }

    const embed = child.embed;
    const socket = child.contact === "socket";
    const point = new THREE.Vector3();
    const pens = [];
    let ok = 0;
    for (const fu of FRACTIONS) {
      for (const fv of FRACTIONS) {
        point.copy(faceCentre)
          .addScaledVector(u, loU + fu * (hiU - loU))
          .addScaledVector(v, loV + fv * (hiV - loV))
          .addScaledVector(n, cn);
        const pen = penetrationAlong(parentBox, point, n);
        pens.push(pen);
        const good = socket
          ? pen >= 0.5 * embed - 1e-9 && pen <= 1.5 * embed + 1e-9
          : Math.abs(pen - embed) <= EPS + 1e-9;
        if (good) ok += 1;
      }
    }

    pens.sort((a, b) => a - b);
    const median = pens[Math.floor(pens.length / 2)];
    const d = median - embed;                 // < 0 = short of the parent
    measurements.set(part.id, { d, median, gap: -d, embed, contact: child.contact, parent: part.attach.to,
      childExtentAlongN: 2 * childHalfN, parentExtentAlongN: 2 * halfN, into: axisLabel(n.clone().negate()) });

    if (ok / pens.length >= limits.contactSampleFrac - 1e-9) continue;

    const direction = d < 0 ? axisLabel(n.clone().negate()) : axisLabel(n);
    const limit = socket
      ? `penetration ${fmt(0.5 * embed)}..${fmt(1.5 * embed)} m on ${Math.round(limits.contactSampleFrac * 100)}% of samples`
      : `|d| <= ${fmt(EPS)} m on ${Math.round(limits.contactSampleFrac * 100)}% of samples`;
    violations.push(make("V2", part.id, `penetration ${fmt(median)} m (${ok}/25 samples in range)`, limit,
      `move ${part.id} ${fmt(Math.abs(d))} m along ${direction} to touch ${part.attach.to} (declared ${child.contact}, embed ${fmt(embed)} m, measured ${fmt(median)} m)`));
  }

  return { violations, advisories: [], measurements };
}

function fmt(value) {
  return (Math.round(value * 1000) / 1000).toFixed(3);
}
