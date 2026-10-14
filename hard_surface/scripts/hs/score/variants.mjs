// Controlled single-part variants for PART-CALIBRATION.md: each one edits ONE part of a copy of
// out/blender-hs/<s>/build.py and is known-worse than the baseline (the subject's current build).
//
//   node scripts/hs/score/variants.mjs --make            # write out/score/variants/<s>/<key>/build.py (+ base_a/base_b)
//   node scripts/hs/score/variants.mjs --run [--jobs 4]  # render each (scripts/hs/score/part_pass.py) that has no pass0_ids.json
//
// Never touches a subject folder: run_pass.py is called with --build <variant> --out-dir <variant dir>.
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../../..");
export const VDIR = path.join(ROOT, "out", "score", "variants");
const BLENDER = "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe";

// post-build transform of one object (author frame metres; scale about the vertex centroid)
const xform = (name, { s = 1, d = [0, 0, 0] }) => ({ post: `
def _variant(parts):
    from mathutils import Vector as _V
    n = 0
    for ob in parts:
        if ob.name != ${JSON.stringify(name)}:
            continue
        vs = ob.data.vertices
        c = sum((v.co for v in vs), _V()) / len(vs)
        off = A(${d.join(", ")})
        for v in vs:
            v.co = c + (v.co - c) * ${s} + off
        n += 1
    assert n == 1, "variant: object ${name} not found"
` });

// key -> { part: ob["part"] role, what, edits: [[find, replace]] | post }
export const VARIANTS = {
  pistol: {
    bore_closed: { part: "barrel", what: "muzzle bore closed (no bore cut)",
      edits: [["    bore(bm, f[-1], wall=0.0024, depth=0.030, mat=1)\n", ""]] },
    bore_wall_thick: { part: "barrel", what: "barrel wall 2.4 -> 4.5 mm (bore dia 11.6 -> 7.4 mm)",
      edits: [["bore(bm, f[-1], wall=0.0024,", "bore(bm, f[-1], wall=0.0045,"]] },
    notch_closed: { part: "sight", what: "rear sight notch closed",
      edits: [["    box(cb, (0, y1 - 0.0043 + 0.010, Z(824)), (0.0045, 0.020, 0.030))\n    diff(ob, cb)\n", ""]] },
    serr_3: { part: "slide", what: "slide serrations 6 -> 3",
      edits: [["SERR_N, SERR_X0, SERR_PITCH, SERR_W, SERR_SLOPE = 6,", "SERR_N, SERR_X0, SERR_PITCH, SERR_W, SERR_SLOPE = 3,"]] },
    trigger_move5: { part: "trigger", what: "trigger moved 5 mm toward the muzzle", ...xform("trigger", { d: [0, 0, 0.005] }) },
    safety_move5: { part: "selector", what: "thumb safety moved 5 mm down", ...xform("safety", { d: [0, -0.005, 0] }) },
    mag_scale110: { part: "magazine", what: "magazine (floor plate) scaled 110 %", ...xform("magazine", { s: 1.1 }) },
  },
  pump_shotgun: {
    bore_closed: { part: "barrel", what: "muzzle bore closed (no bore cut)",
      edits: [["    bore(bm, f[-1], wall=0.0020, depth=zm - Z(506), mat=1)\n", ""]] },
    bore_wall_thick: { part: "barrel", what: "barrel wall +4 mm (bore cut wall 2 -> 6 mm)",
      edits: [["bore(bm, f[-1], wall=0.0020,", "bore(bm, f[-1], wall=0.0060,"]] },
    guard_small: { part: "trigger_guard", what: "trigger-guard opening shrunk (cutter 70 % about its centre)",
      edits: [["    prism(cb, PX([(592, 495), (637, 495), (637, 512), (635.5, 518), (632, 522.5), (626, 526.5), (603, 526.5),\n                   (598, 522.5), (594.5, 518), (592, 511)]), \"x\", -0.03, 0.03)",
        "    _g = [(592, 495), (637, 495), (637, 512), (635.5, 518), (632, 522.5), (626, 526.5), (603, 526.5),\n                   (598, 522.5), (594.5, 518), (592, 511)]\n    _g = [(614.5 + (x - 614.5) * 0.7, 512 + (y - 512) * 0.7) for x, y in _g]\n    prism(cb, PX(_g), \"x\", -0.03, 0.03)"]] },
    grooves_2: { part: "pump", what: "pump grooves 4 -> 2",
      edits: [["GROOVE_X = (288.0, 319.3, 350.7, 382.0)", "GROOVE_X = (288.0, 382.0)"]] },
    stock_scale110: { part: "stock", what: "stock scaled 110 %", ...xform("stock", { s: 1.1 }) },
    grip_move10: { part: "grip", what: "grip moved 10 mm back", ...xform("grip", { d: [0, 0, -0.010] }) },
    trigger_move5: { part: "trigger", what: "trigger moved 5 mm toward the muzzle", ...xform("trigger", { d: [0, 0, 0.005] }) },
  },
  gatling_gun: {
    bores_closed: { part: "barrel_cluster", what: "all six bores closed (no bore cut)",
      edits: [["    union(ob, ub)\n    diff(ob, cb)\n    axes = [spin(", "    union(ob, ub)\n    axes = [spin("]] },
    bore_small: { part: "barrel_cluster", what: "bore dia 23 -> 14 mm (wall 10 -> 14.5 mm)",
      edits: [["BAR_R, BAR_r, BORE_r = 0.0530, 0.0215, 0.0115", "BAR_R, BAR_r, BORE_r = 0.0530, 0.0215, 0.0070"]] },
    grip_open_small: { part: "grip", what: "spade-grip opening shrunk (70 % about its centre)",
      edits: [["    prism(cb, PX(GRIP_IN), \"x\", -0.06, 0.06)",
        "    prism(cb, PX([(838 + (x - 838) * 0.7, 454 + (y - 454) * 0.7) for x, y in GRIP_IN]), \"x\", -0.06, 0.06)"]] },
    handle_move15: { part: "handle", what: "carry handle moved 15 mm up", ...xform("handle", { d: [0, 0.015, 0] }) },
    drum_scale110: { part: "drum", what: "drum scaled 110 %", ...xform("drum", { s: 1.1 }) },
    trigger_move10: { part: "trigger", what: "trigger moved 10 mm toward the muzzle", ...xform("trigger", { d: [0, 0, 0.010] }) },
  },
};
export const BASES = ["base_a", "base_b"];

function make() {
  for (const [s, vs] of Object.entries(VARIANTS)) {
    const src = fs.readFileSync(path.join(ROOT, "out", "blender-hs", s, "build.py"), "utf8").replace(/\r\n/g, "\n");
    for (const b of BASES) { fs.mkdirSync(path.join(VDIR, s, b), { recursive: true }); fs.writeFileSync(path.join(VDIR, s, b, "build.py"), src); }
    for (const [k, v] of Object.entries(vs)) {
      let out = src;
      for (const [f, r] of v.edits ?? []) {
        const n = out.split(f).length - 1;
        if (n !== 1) throw new Error(`${s}/${k}: edit anchor found ${n} times: ${f.slice(0, 60)}`);
        out = out.replace(f, () => r);
      }
      if (v.post) {
        const i = out.lastIndexOf("    return root, parts");
        if (i < 0) throw new Error(`${s}/${k}: no 'return root, parts'`);
        out = out.slice(0, i) + "    _variant(parts)\n" + out.slice(i) + "\n" + v.post;
      }
      if (out === src) throw new Error(`${s}/${k}: no change`);
      const d = path.join(VDIR, s, k);
      fs.mkdirSync(d, { recursive: true });
      fs.writeFileSync(path.join(d, "build.py"), out);
      fs.writeFileSync(path.join(d, "variant.json"), JSON.stringify({ subject: s, key: k, part: v.part, what: v.what }, null, 1));
    }
  }
  console.log("made", Object.entries(VARIANTS).map(([s, v]) => `${s}: ${Object.keys(v).length} + ${BASES.length} bases`).join(", "));
}

function runOne(s, k) {
  const d = path.join(VDIR, s, k), rel = (p) => path.relative(ROOT, p).replace(/\\/g, "/");
  return new Promise((res) => {
    const t0 = Date.now(), log = fs.openSync(path.join(d, "run.log"), "w");
    const p = spawn(BLENDER, ["-b", "--factory-startup", "--python-exit-code", "1", "--python", "scripts/hs/score/part_pass.py", "--",
      "--subject", s, "--build", rel(path.join(d, "build.py")), "--out-dir", rel(d)], { cwd: ROOT, stdio: ["ignore", log, log] });
    p.on("close", (code) => { fs.closeSync(log); console.log(`${s}/${k} exit ${code} ${((Date.now() - t0) / 1000).toFixed(0)} s`); res(code); });
  });
}

async function run(jobs) {
  const todo = [];
  for (const s of Object.keys(VARIANTS)) for (const k of [...BASES, ...Object.keys(VARIANTS[s])])
    if (!fs.existsSync(path.join(VDIR, s, k, "pass0_ids.json"))) todo.push([s, k]);
  console.log(`${todo.length} to render, ${jobs} at a time`);
  let i = 0;
  await Promise.all(Array.from({ length: jobs }, async () => { while (i < todo.length) { const [s, k] = todo[i++]; await runOne(s, k); } }));
}

const argv = process.argv.slice(2);
if (argv.includes("--make")) make();
if (argv.includes("--run")) await run(Math.min(4, Number(argv[argv.indexOf("--jobs") + 1]) || 4));
