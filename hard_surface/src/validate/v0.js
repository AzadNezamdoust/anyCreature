// V0 — schema, DAG, ground rule, closed vocabularies.
//
// The only validator in M0. V1-V10 land in M1 (PLAN.md 2); nothing here reads
// geometry, so V0 runs before a single vertex is built and costs no tokens.
//
// A violation is `{v, part, measured, limit, hint}` and the hint states the move
// in plain terms — that text is the only thing the REPAIR seat will ever see.
import { isPrim, isComposite, PRIM_NAMES, COMPOSITE_NAMES, PRIM_OPTIONS, RING_AXES } from "../prims.js";
import { isFace, isContact, isAlign, isAlignU, FACE_NAMES, CONTACTS, ALIGNMENTS, ALIGN_U, HANGS_BELOW_FACE } from "../compile/resolve.js";
import { REPEAT_AXES } from "../compile/expand.js";
import { compositeDims, hasCompositeSub } from "../compile/composites.js";
import { ELEMENT_NAMES, EMPTY_REGIONS } from "../compile/grammar.js";
import { DSL_VERSION } from "../spec.js";

const isPlainObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const isFiniteNumber = (value) => typeof value === "number" && Number.isFinite(value);

function violation(part, measured, limit, hint) {
  return { v: "V0", part, measured, limit, hint };
}

/**
 * @param {object} spec a parsed pg/1 spec
 * @returns {{pass:boolean, violations:Array<object>}}
 */
export function validateV0(spec) {
  const violations = [];
  const add = (...args) => violations.push(violation(...args));

  if (!isPlainObject(spec)) {
    add(null, typeof spec, "object", "the spec must be a JSON object");
    return { pass: false, violations };
  }

  if (spec.schema !== DSL_VERSION) {
    add(null, String(spec.schema), DSL_VERSION, `set "schema" to "${DSL_VERSION}"`);
  }
  if (typeof spec.subject !== "string" || spec.subject === "") {
    add(null, String(spec.subject), "non-empty string", 'give the spec a "subject" name');
  }
  if (!isFiniteNumber(spec.seed) && typeof spec.seed !== "string") {
    add(null, String(spec.seed), "number or string", 'set "seed" — the compiler stream is keyed on it');
  }

  const palette = isPlainObject(spec.palette) ? spec.palette : null;
  if (!palette) {
    add(null, typeof spec.palette, "object", '"palette" must map zone names to hex colours');
  } else {
    for (const [zone, hex] of Object.entries(palette)) {
      if (typeof hex !== "string" || !/^#[0-9a-fA-F]{6}$/.test(hex)) {
        add(null, `${zone}=${hex}`, "#rrggbb", `palette zone "${zone}" needs a #rrggbb colour`);
      }
    }
  }

  if (!Array.isArray(spec.parts) || spec.parts.length === 0) {
    add(null, Array.isArray(spec.parts) ? "0 parts" : typeof spec.parts, ">= 1 part", '"parts" must be a non-empty array');
    return { pass: violations.length === 0, violations };
  }

  const seen = new Set();
  /** id -> composite prim name, for the parts declared so far (M6 gap 1). */
  const compositePrims = new Map();
  let groundCount = 0;
  let structural = 0;

  for (const part of spec.parts) {
    if (!isPlainObject(part)) {
      add(null, typeof part, "object", "every entry of parts must be an object");
      structural += 1;
      continue;
    }
    const id = part.id;
    if (typeof id !== "string" || id === "") {
      add(null, String(id), "non-empty string", "every part needs a unique string id");
      structural += 1;
      continue;
    }
    if (seen.has(id)) {
      add(id, id, "unique id", `part id "${id}" is used twice; rename one`);
      structural += 1;
    }

    const composite = isComposite(part.prim);
    if (composite) compositePrims.set(id, part.prim);
    if (!isPrim(part.prim) && !composite) {
      add(id, String(part.prim), [...PRIM_NAMES, ...COMPOSITE_NAMES].join("|"),
        `prim "${part.prim}" is in neither the prim vocabulary (${PRIM_NAMES.join(", ")}) nor the composite library (${COMPOSITE_NAMES.join(", ")})`);
    }
    const dimsOk = Array.isArray(part.dims) && part.dims.length === 3
      && part.dims.every((n) => isFiniteNumber(n) && n > 0);
    if (!dimsOk) {
      add(id, JSON.stringify(part.dims), "[w,h,d] > 0", `part "${id}" needs dims [w, h, d] in metres, all positive`);
    }
    for (const key of PRIM_OPTIONS) {
      if (part[key] === undefined) continue;
      // `axis` is the one non-numeric prim option (ring bore direction).
      if (key === "axis") {
        if (!RING_AXES.includes(part[key])) {
          add(id, `axis=${part[key]}`, RING_AXES.join("|"), `prim option "axis" on "${id}" names the ring bore direction: ${RING_AXES.join(" or ")}`);
        }
        continue;
      }
      if (!isFiniteNumber(part[key])) {
        add(id, `${key}=${part[key]}`, "number", `prim option "${key}" on "${id}" must be a number`);
      }
    }
    if (part.params !== undefined) {
      if (!composite) {
        add(id, "params", "composite prim only", `"params" on "${id}" only means something on a composite prim`);
      } else if (!isPlainObject(part.params) || !Object.values(part.params).every(isFiniteNumber)) {
        add(id, JSON.stringify(part.params), "object of numbers", `params on "${id}" must map names to finite numbers`);
      }
    }
    if (part.zones !== undefined && (!isPlainObject(part.zones)
      || !Object.values(part.zones).every((z) => palette && Object.hasOwn(palette, z)))) {
      add(id, JSON.stringify(part.zones), "object of palette zones", `zones on "${id}" must map a composite's zone keys to palette zones`);
    }
    // A composite whose library derives its own dims (stairFlight: steps x rise)
    // must not also carry a contradictory authored dims — the derived value wins
    // silently otherwise, and the spec would lie about the model.
    if (composite && dimsOk) {
      let derived = null;
      try { derived = compositeDims(part); } catch (error) { add(id, error.message, "valid composite params", `composite "${part.prim}" on "${id}": ${error.message}`); }
      if (derived && derived.some((value, axis) => Math.abs(value - part.dims[axis]) > 1e-6)) {
        add(id, JSON.stringify(part.dims), JSON.stringify(derived.map((n) => Math.round(n * 1e6) / 1e6)),
          `composite "${part.prim}" derives its dims from its params; set dims on "${id}" to [${derived.map((n) => Math.round(n * 1e6) / 1e6).join(", ")}]`);
      }
    }
    if (palette && !Object.hasOwn(palette, part.zone)) {
      add(id, String(part.zone), Object.keys(palette).join("|"), `zone "${part.zone}" is not in the palette; add it or use an existing zone`);
    }

    const attach = part.attach;
    if (attach === undefined) {
      if (part.ground === true) groundCount += 1;
      else {
        add(id, "no attach, no ground", "attach or ground:true", `part "${id}" is unrooted: attach it to an earlier part, or mark it ground:true`);
        structural += 1;
      }
    } else {
      if (part.ground === true) {
        add(id, "attach + ground:true", "exactly one", `part "${id}" cannot be both attached and ground:true; drop one`);
        structural += 1;
      }
      if (!isPlainObject(attach)) {
        add(id, typeof attach, "object", `part "${id}" has a malformed attach block`);
        structural += 1;
        seen.add(id);
        continue;
      }
      // M6 gap 1: a composite may be a parent. `to` is either an earlier part
      // id (a composite id there means its ROOT sub-part) or `composite.sub`,
      // a named sub-part of an earlier composite. Expansion rewrites both to an
      // ordinary part before the solver or any later validator sees them.
      if (!seen.has(attach.to) && !isCompositeSubRef(attach.to, compositePrims)) {
        add(id, String(attach.to), "an earlier part id or composite.sub",
          `attach.to "${attach.to}" must name a part declared BEFORE "${id}" (a composite id means its root sub-part, and "<composite>.<sub>" names one of its sub-parts) — the spec is a DAG in file order`);
        structural += 1;
      }
      if (!isFace(attach.face)) {
        add(id, String(attach.face), FACE_NAMES.join("|"), `attach.face "${attach.face}" must be one of ${FACE_NAMES.join(", ")}`);
      }
      if (!isContact(attach.contact)) {
        add(id, String(attach.contact), CONTACTS.join("|"), `attach.contact "${attach.contact}" is not in the contact vocabulary (${CONTACTS.join(", ")})`);
      }
      // `hangs-below` is DEFINED on the parent's -Y face (the child's top face
      // touches it). On any other face the name would lie about the geometry.
      if (attach.contact === "hangs-below" && attach.face !== HANGS_BELOW_FACE) {
        add(id, String(attach.face), HANGS_BELOW_FACE, `attach.contact "hangs-below" on "${id}" only means anything on the parent's ${HANGS_BELOW_FACE} face — use "flush" for a side face`);
      }
      if (attach.uv !== undefined) {
        const ok = Array.isArray(attach.uv) && attach.uv.length === 2
          && attach.uv.every((n) => isFiniteNumber(n) && n >= 0 && n <= 1);
        if (!ok) add(id, JSON.stringify(attach.uv), "[u,v] in 0..1", `attach.uv on "${id}" must be two numbers in 0..1`);
      }
      if (attach.align !== undefined && !isAlign(attach.align)) {
        add(id, String(attach.align), ALIGNMENTS.join("|"), `attach.align "${attach.align}" must be one of ${ALIGNMENTS.join(", ")}`);
      }
      if (attach.alignU !== undefined && !isAlignU(attach.alignU)) {
        add(id, String(attach.alignU), ALIGN_U.join("|"), `attach.alignU "${attach.alignU}" anchors the child along the face's u axis and must be one of ${ALIGN_U.join(", ")}`);
      }
      // M6 gap 2: opt into per-instance children. "all" puts this part on every
      // instance of a repeated/mirrored parent; 0 (the default) is the anchor.
      if (attach.instance !== undefined && attach.instance !== "all" && attach.instance !== 0) {
        add(id, String(attach.instance), '"all" | 0',
          `attach.instance on "${id}" is "all" (one child per parent instance) or 0 (the anchor instance only, the default)`);
      }
      if (attach.embed !== undefined && (!isFiniteNumber(attach.embed) || attach.embed < 0)) {
        add(id, String(attach.embed), ">= 0 metres", `attach.embed on "${id}" is a penetration depth in metres, never negative`);
      }
      if (attach.rot !== undefined && !isFiniteNumber(attach.rot)) {
        add(id, String(attach.rot), "degrees about the attach normal", `attach.rot on "${id}" must be a number of degrees`);
      }
    }

    if (part.repeat !== undefined) {
      const repeat = part.repeat;
      if (!isPlainObject(repeat)) {
        add(id, typeof repeat, "object", `repeat on "${id}" must be {axis, count, pitch}`);
      } else {
        if (!REPEAT_AXES.includes(repeat.axis)) {
          add(id, String(repeat.axis), REPEAT_AXES.join("|"), `repeat.axis on "${id}" is a parent-local signed axis`);
        }
        if (!Number.isInteger(repeat.count) || repeat.count < 2) {
          add(id, String(repeat.count), "integer >= 2", `repeat.count on "${id}" counts the total instances, so it is at least 2`);
        }
        if (!isFiniteNumber(repeat.pitch) || repeat.pitch <= 0) {
          add(id, String(repeat.pitch), "> 0 metres", `repeat.pitch on "${id}" is the metre spacing between instances`);
        }
      }
    }

    if (part.mirror !== undefined && typeof part.mirror !== "boolean") {
      add(id, String(part.mirror), "boolean", `mirror on "${id}" is true or absent in M0`);
    }

    seen.add(id);
  }

  if (spec.facades !== undefined) validateFacades(spec, seen, palette, add);

  // Only reachable when nothing structural fired: a spec in which every part
  // attaches necessarily trips the forward-reference rule on its first part.
  if (structural === 0 && groundCount === 0) {
    add(null, "0 ground parts", ">= 1", "at least one part must carry ground:true and no attach");
  }

  return { pass: violations.length === 0, violations };
}

/** `to` of the form `<composite id>.<sub id>` naming an EARLIER composite. */
function isCompositeSubRef(to, compositePrims) {
  if (typeof to !== "string") return false;
  const cut = to.indexOf(".");
  if (cut <= 0 || cut === to.length - 1) return false;
  const prim = compositePrims.get(to.slice(0, cut));
  return prim !== undefined && hasCompositeSub(prim, to.slice(cut + 1));
}

/**
 * `spec.facades[]` — the CGA-lite grammar (PLAN 1.1). Nothing here reads
 * geometry: a facade is a declaration about a face of a part that already
 * exists, so every error it can make is a V0 error.
 */
const SPLIT_AXES = ["X", "Y"];

function validateFacades(spec, partIds, palette, add) {
  if (!Array.isArray(spec.facades)) {
    add(null, typeof spec.facades, "array", '"facades" must be an array of facade declarations');
    return;
  }

  const ids = new Set();
  for (const facade of spec.facades) {
    if (!isPlainObject(facade)) {
      add(null, typeof facade, "object", "every entry of facades must be an object");
      continue;
    }
    const id = facade.id;
    if (typeof id !== "string" || id === "") {
      add(null, String(id), "non-empty string", "every facade needs a unique string id");
      continue;
    }
    if (ids.has(id)) add(id, id, "unique id", `facade id "${id}" is used twice; rename one`);
    ids.add(id);

    if (!partIds.has(facade.on)) {
      add(id, String(facade.on), "an existing part id", `facade "${id}" is "on" part "${facade.on}", which no part declares`);
    }
    if (!isFace(facade.face)) {
      add(id, String(facade.face), FACE_NAMES.join("|"), `facade.face "${facade.face}" must be one of ${FACE_NAMES.join(", ")}`);
    }
    if (facade.occlude !== undefined && typeof facade.occlude !== "boolean") {
      add(id, String(facade.occlude), "boolean", `facade.occlude on "${id}" is true (default) or false`);
    }

    checkRule(id, "split", facade.split, add);
    for (const [name, tile] of Object.entries(facade.tile ?? {})) checkRule(id, `tile.${name}`, tile, add);

    for (const [name, recipe] of Object.entries(facade.elements ?? {})) {
      if (!isPlainObject(recipe)) {
        add(id, typeof recipe, "object", `facade "${id}" elements."${name}" must be an object of element declarations`);
        continue;
      }
      for (const [element, body] of Object.entries(recipe)) {
        if (!ELEMENT_NAMES.includes(element)) {
          add(id, element, ELEMENT_NAMES.join("|"),
            `facade "${id}" element "${element}" is not in the grammar vocabulary (${ELEMENT_NAMES.join(", ")}); ${EMPTY_REGIONS.join("/")} regions carry no element at all`);
          continue;
        }
        if (!isPlainObject(body)) {
          add(id, typeof body, "object", `facade "${id}" element "${element}" must be an object`);
          continue;
        }
        if (body.zone !== undefined && palette && !Object.hasOwn(palette, body.zone)) {
          add(id, String(body.zone), Object.keys(palette).join("|"), `facade "${id}" element "${element}" names zone "${body.zone}", which is not in the palette`);
        }
        if (body.dims !== undefined) {
          const ok = Array.isArray(body.dims) && body.dims.length === 2 && body.dims.every((n) => isFiniteNumber(n) && n > 0);
          if (!ok) add(id, JSON.stringify(body.dims), "[w,h] > 0", `facade "${id}" element "${element}" dims are [width, height] on the face, in metres`);
        }
        if (body.lintel !== undefined && body.lintel !== "flat" && body.lintel !== "arch") {
          add(id, String(body.lintel), "flat|arch", `facade "${id}" element "${element}" lintel is "flat" or "arch"`);
        }
      }
    }
  }
}

function checkRule(facadeId, label, block, add) {
  if (block === undefined) {
    if (label === "split") add(facadeId, "no split", "{axis, rule}", `facade "${facadeId}" needs a split: which way the face divides and into what`);
    return;
  }
  if (!isPlainObject(block)) {
    add(facadeId, typeof block, "{axis, rule}", `facade "${facadeId}" ${label} must be {axis, rule}`);
    return;
  }
  if (!SPLIT_AXES.includes(String(block.axis).toUpperCase())) {
    add(facadeId, String(block.axis), SPLIT_AXES.join("|"), `facade "${facadeId}" ${label}.axis is "X" (across the face) or "Y" (up it)`);
  }
  if (!Array.isArray(block.rule) || block.rule.length === 0) {
    add(facadeId, JSON.stringify(block.rule), "non-empty array", `facade "${facadeId}" ${label}.rule must be a non-empty array of [name, size] entries`);
    return;
  }
  for (const entry of block.rule) {
    if (!Array.isArray(entry) || entry.length < 2 || typeof entry[0] !== "string") {
      add(facadeId, JSON.stringify(entry), '[name, size] | [name, size, "*N"] | [name, "~"]',
        `facade "${facadeId}" ${label}.rule entry ${JSON.stringify(entry)} is malformed`);
      continue;
    }
    if (entry[1] !== "~" && !(isFiniteNumber(entry[1]) && entry[1] > 0)) {
      add(facadeId, String(entry[1]), '> 0 metres or "~"', `facade "${facadeId}" ${label}.rule "${entry[0]}" needs a positive metre size, or "~" to fill what is left`);
    }
    if (entry.length > 2 && !/^\*\d+$/.test(String(entry[2]))) {
      add(facadeId, String(entry[2]), '"*N"', `facade "${facadeId}" ${label}.rule "${entry[0]}" repeat flag must look like "*3"`);
    }
  }
}

/** ≤8 lines of plain text — the only thing the REPAIR seat is ever shown. */
export function reportText(result) {
  if (result.pass) return "PASS: V0 clean.";
  return [`FAIL: ${result.violations.length} V0 violation(s).`]
    .concat(result.violations.slice(0, 7).map((x) => `- ${x.part ? `${x.part}: ` : ""}${x.hint}`))
    .join("\n");
}
