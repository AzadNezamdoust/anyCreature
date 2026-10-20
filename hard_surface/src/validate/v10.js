// V10 — export sanity: one mesh, one material, no NaN/Inf, inside the class
// triangle budget. These four assertions used to live in test/budget.test.js;
// they are a validator now and the test calls this.
export function validateV10(ctx, make) {
  const { solved, geometryInfo, cls, limits } = ctx;
  const violations = [];
  const budget = limits.triBudget[cls] ?? limits.triBudget.prop;

  if (solved.triangles > budget) {
    violations.push(make("V10", null, `${solved.triangles} triangles`, `<= ${budget} (${cls})`,
      `the model is ${solved.triangles - budget} triangles over the ${cls} budget — cut repeats or drop a composite`));
  }
  if (!(solved.triangles > 0)) {
    violations.push(make("V10", null, `${solved.triangles} triangles`, "> 0",
      "the spec compiled to no geometry at all"));
  }

  const geometry = geometryInfo.geometry ?? null;
  if (!geometry) {
    violations.push(make("V10", null, "0 geometries", "exactly 1",
      "the compile output must be one merged geometry, one material, one draw call"));
    return { violations, advisories: [] };
  }

  const groups = geometry.groups ?? [];
  if (groups.length > 1) {
    violations.push(make("V10", null, `${groups.length} material groups`, "<= 1",
      "the merged geometry carries more than one material group"));
  }

  for (const name of ["position", "color"]) {
    const attribute = geometry.getAttribute(name);
    if (!attribute) {
      violations.push(make("V10", null, `no "${name}" attribute`, `"${name}" present`,
        `the merged geometry has no ${name} attribute — the GLB would export blank`));
      continue;
    }
    let bad = 0;
    for (const value of attribute.array) if (!Number.isFinite(value)) bad += 1;
    if (bad > 0) {
      violations.push(make("V10", null, `${bad} non-finite ${name} values`, "0",
        `the merged geometry carries ${bad} NaN/Inf ${name} values`));
    }
  }

  return { violations, advisories: [] };
}
