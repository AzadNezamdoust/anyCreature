// The one material every compiled asset shares.
//
// Forked from CharacterStudioV2/src/geom.js:181-189 (`characterMaterial`) and
// renamed. One material for the whole subject is what keeps the merged mesh at
// one draw call; vertex colours carry every zone, flat shading keeps the facets
// readable without a single texture.
import * as THREE from "three";

export function assetMaterial() {
  return new THREE.MeshStandardMaterial({
    vertexColors: true,
    flatShading: true,
    roughness: 0.92,
    metalness: 0.0,
    side: THREE.FrontSide,
  });
}

/**
 * WF-LOOP r2 A1 — the FLAT capture material.
 *
 * The judged still is measured against `refs/tenement-iso.png`, which is three
 * flat values (front > side > roof) and no lit gradient at all. The PBR rig
 * (`app.js` hemisphere + key at (-24, 34, 27)) was placed for the character
 * studio: after the front rotation the populated face turns AWAY from the key
 * and rendered at 0.51x its palette value, which is what the r2 audits both
 * blamed on the palette seat. Unlit basic + vertex colours makes the capture
 * report the baked value and nothing else, so `palette hex == what the front
 * face shows`, and the front/side step is the baked `SHADE.sideTint`.
 *
 * Studio mode keeps `assetMaterial()` and the lights.
 */
export function captureMaterial() {
  return new THREE.MeshBasicMaterial({
    vertexColors: true,
    side: THREE.FrontSide,
  });
}
