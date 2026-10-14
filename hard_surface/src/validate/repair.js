// Auto-repair — the four moves the numbers fully determine (02:T3).
//
// Everything else re-prompts. V3 (an orphan cluster: intent unknown), V4 (a
// stability failure: which mass moves is a design call) and V7 (owner-ratified
// numbers) are NEVER repaired here; that is a rule, not an omission.
//
// Each pass re-validates. A pass that introduces a violation class the previous
// report did not carry is reverted whole, and the original violation stands.
import { validateSpec, DEFAULT_LIMITS } from "./index.js";

/**
 * @param {object} spec pg/1 spec
 * @param {object} report validateSpec(spec) — re-derived if `measurements` is absent
 * @param {object} [limits]
 * @returns {{spec:object, applied:Array<object>, report:object}}
 */
export function repair(spec, report, limits = DEFAULT_LIMITS) {
  let current = clone(spec);
  let currentReport = report?.measurements ? report : validateSpec(current, limits);
  const applied = [];

  for (let pass = 0; pass < limits.maxRepairPasses; pass += 1) {
    if (currentReport.pass) break;

    const candidate = clone(current);
    const passApplied = [];
    for (const violation of currentReport.violations) {
      const move = plan(candidate, violation, currentReport, limits);
      if (move) passApplied.push(move);
    }
    if (passApplied.length === 0) break;

    const candidateReport = validateSpec(candidate, limits);
    if (regressed(currentReport, candidateReport)) break;   // revert: candidate discarded

    current = candidate;
    currentReport = candidateReport;
    applied.push(...passApplied.map((m) => ({ ...m, pass: pass + 1 })));
  }

  return { spec: current, applied, report: currentReport };
}

/** Mutates `spec` in place; returns the applied record, or null when not repairable. */
function plan(spec, violation, report, limits) {
  const byId = new Map(spec.parts.map((p) => [p.id, p]));

  if (violation.v === "V2") {
    const measured = report.measurements?.get(violation.part);
    const part = byId.get(violation.part);
    if (!measured || !part || !part.attach) return null;
    // M5: an `embedded` shortfall is not a gap — the child is in the wrong place
    // or the wrong size, and the only lever repair has (embed -> 0) would pull it
    // further OUT. It re-prompts, like V3/V4/V7.
    if (measured.contact === "embedded") return null;

    const gap = measured.median < 0 ? -measured.median : Math.abs(measured.d);
    const ceiling = Math.max(
      limits.repairGapMaxEpsMult * (report.context?.EPS ?? limits.epsAbs),
      limits.repairGapMaxChildFrac * measured.childExtentAlongN,
    );
    if (gap > ceiling) return null;   // too far gone: re-prompt, do not guess

    const from = part.attach.embed ?? measured.embed;
    // A socket closes at half the parent's thickness — deep enough to read as
    // seated, far enough from the far face that float noise cannot flip the sign.
    const to = measured.contact === "socket" ? Math.min(from, 0.5 * measured.parentExtentAlongN) : 0;
    if (Math.abs(to - from) < 1e-9) return null;
    part.attach.embed = round(to);
    return { v: "V2", part: part.id, action: "embed", from: round(from), to: round(to), gap: round(gap) };
  }

  if (violation.v === "V5") {
    const part = byId.get(violation.part);
    if (!part) return null;

    if (violation.measured.startsWith("repeat gap")) {
      // MVP-STUB: the widened axis is read off the parent-local repeat axis
      // letter. Every M0 parent frame is axis-aligned, where that is the same
      // axis the pixels ran along.
      const index = { X: 0, Y: 1, Z: 2 }[String(part.repeat.axis).slice(1)];
      if (index === undefined) return null;
      const extent = part.dims[index];
      const run = (part.repeat.count - 1) * part.repeat.pitch + extent;
      // NOTE: the brief says "set count 1". V0 requires repeat.count >= 2, so a
      // collapsed repeat drops the block instead of keeping a 1-instance one.
      delete part.repeat;
      part.dims[index] = round(run);
      part.stripe = true;
      return { v: "V5", part: part.id, action: "collapse-repeat", from: round(extent), to: round(run), stripe: true };
    }

    const MIN_FEAT = report.context?.MIN_FEAT;
    if (!MIN_FEAT) return null;
    const min = Math.min(...part.dims);
    if (min >= MIN_FEAT) return null;
    const index = part.dims.indexOf(min);
    part.dims[index] = round(MIN_FEAT);
    return { v: "V5", part: part.id, action: "grow", axis: ["w", "h", "d"][index], from: round(min), to: round(MIN_FEAT) };
  }

  if (violation.v === "V6" && violation.measured.includes("contained")) {
    const specId = String(violation.part).split("~")[0].split("#")[0];
    if (!byId.has(specId)) return null;
    if (spec.parts.some((p) => p.attach?.to === specId)) return null;   // something stands on it
    spec.parts = spec.parts.filter((p) => p.id !== specId);
    return { v: "V6", part: specId, action: "delete-duplicate" };
  }

  return null;   // V3 / V4 / V7 and anything unrecognised: never repaired
}

/** True when the candidate carries a violation class the original did not. */
function regressed(before, after) {
  if (after.violations.length > before.violations.length) return true;
  const known = new Set(before.violations.map((x) => x.v));
  return after.violations.some((x) => !known.has(x.v));
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function round(value) {
  return Math.round(value * 1e6) / 1e6;
}
