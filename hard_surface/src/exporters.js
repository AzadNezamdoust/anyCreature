// Export lane: binary glTF with the vertex colours intact.
//
// Forked from CharacterStudioV2/src/exporters.js:22,35-49,69-77 minus the
// skeleton clause — a compiled asset is one static mesh, so `trs` is false and
// the transform is already baked into the merged geometry.
//
// Consumer note (08:G10): the repo has `com.unity.formats.fbx` and NO glTF
// importer, and URP Lit ignores COLOR_0 without a vertex-colour shader. Until
// the owner rules on a Unity glTF package, the acceptance criterion for this
// file is "opens in a glTF viewer with COLOR_0 intact", not "lands in Unity".
import { GLTFExporter } from "three/addons/exporters/GLTFExporter.js";

/** Frozen GLTFExporter options. Binary, baked transforms, visible only. */
const GLB_OPTIONS = Object.freeze({ binary: true, trs: false, onlyVisible: true });

/**
 * Temporarily hide every descendant marked `userData.excludeFromExport`
 * (ground plane, gizmos, overlays), then restore it.
 * @returns {() => void} restore function; always call it, even on failure
 */
function hideExcluded(root) {
  const hidden = [];
  root.traverse((object) => {
    if (object.userData && object.userData.excludeFromExport === true && object.visible) {
      object.visible = false;
      hidden.push(object);
    }
  });
  return function restore() {
    for (const object of hidden) object.visible = true;
  };
}

/**
 * Serialise an object to a binary glTF Blob. No download side effect.
 * @param {import("three").Object3D} root
 * @returns {Promise<Blob>}
 */
export async function glbBlob(root) {
  if (!root) throw new Error("glbBlob: no object given");
  const restoreVisibility = hideExcluded(root);
  try {
    const exporter = new GLTFExporter();
    const result = await new Promise((resolve, reject) => {
      exporter.parse(root, resolve, reject, GLB_OPTIONS);
    });
    const payload = result instanceof ArrayBuffer
      ? result
      : new TextEncoder().encode(JSON.stringify(result));
    return new Blob([payload], { type: "model/gltf-binary" });
  } finally {
    restoreVisibility();
  }
}

/** Serialise and hand the browser a `.glb` download. */
export async function exportGlb(root, filename = "asset.glb") {
  const blob = await glbBlob(root);
  downloadBlob(blob, filename.toLowerCase().endsWith(".glb") ? filename : `${filename}.glb`);
  return blob;
}

export function downloadBlob(blob, filename) {
  if (typeof document === "undefined" || typeof URL === "undefined" || !URL.createObjectURL) {
    throw new Error("downloadBlob: no browser document available");
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = String(filename || "download.bin");
  link.rel = "noopener";
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 10000);
  return link.download;
}
