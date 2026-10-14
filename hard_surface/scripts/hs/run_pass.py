"""
run_pass.py -- per-subject Blender harness pass (generalised from out/blender-pilot/apc_8x8/run_pass.py).

  cd D:\\Git\\anyCreature\\hard_surface
  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" -b --factory-startup --python-exit-code 1 ^
      --python scripts/hs/run_pass.py -- --subject <s> --pass N [--final] [--build <py>] [--out-dir <dir>]

Builds out/blender-hs/<s>/build.py (build() -> (root, parts)), checks topology (non-manifold / boundary / zero-area /
duplicate / loose / coincident-across-objects), exports <s>.glb, counts tris against the budget (subjects/<s>/
subject.json ruleOverrides.tris, else 8000), renders the four turnaround orthos in the gold judge's framing
(<s>/frame.json, dump_frame.mjs) + the judge's registered concept camera (<s>/concept_cam.json, dump_concept_cam.mjs),
and writes a comparison sheet (reference | current gold model.mjs from out/ref/gold/<s>/view/model-view.png | this
Blender model).

SCORING = the gold judge's, not the renders': the built parts' triangles (author frame, one pseudo-part per material)
go to scripts/hs/judge_mesh.mjs, which runs scripts/v6/judge.mjs's own pipeline on them — the uniform scale sigma fit
(golden section on the mean ortho IoU), ortho iou / agree at JUDGE_SIZE with the views.json drift rects, and the concept
view's registered iou (plain) + agree (concept drift rects don't-care), concept unscaled as in the judge. The ortho
renders are drawn at that sigma so the sheet shows what was scored. build.py must NOT pre-scale the model.

--sigma-fit golden scores with scripts/v6/judge.mjs's golden-section sigma fit alone (judge_mesh.mjs default since
2026-10-10: that answer plus a dense scan, kept unless the scan beats it clearly; scripts/hs/README.md "Sigma fit").
--keep-mesh leaves passN_mesh.json (the scored triangles) for offline re-scoring with judge_mesh.mjs --mesh.

--gate-ref mature|all (direct subjects only; default mature): which earlier passes the direct gate's reference is
taken from. mature = the best agree per view over earlier passes that are not block-outs (the folder's first pass and
any pass under 5 % of the tri budget); all = every earlier pass (the rule before 2026-10-10). Vehicles: ignored.

--dump-part-boxes: every mesh object's author-metre bbox + its projection through concept_cam.json (all of it and the
part seen first by rays: scripts/hs/part_boxes.py) into passN_stats.json `parts` and passN_parts.json. Additive.
--hero report|gate (implies --dump-part-boxes; needs subjects/<s>/parts.json): runs scripts/hs/score/heroratio.mjs
(hull-relative part ratios vs the hero, > 10 % or a count off = FAIL; a parts.json part or a FEATURES.md keep-list
object with no build object = FAIL; a parts.json `opening` drawn solid = FAIL), prints its table + a `HERO` line after the
judge, writes passN_hero.json and stats `hero`. report = information only; gate (direct subjects) = the GATE also
needs HERO PASS (BUILD-DIRECT.md: pass 2 must pass it before any detail). Without the flags nothing changes.

--concept-cam <json> reads the concept camera from that file instead of <s>/concept_cam.json (a `persp` block =
the solve_persp_cam.py pinhole: the concept tile and the part boxes / HERO go through it; scripts/hs/concept_camera.py).
--build <py> scores another build file (e.g. scripts/hs/build_from_mesh.py), --out-dir <dir> writes the pass outputs
there instead of out/blender-hs/<s>/ (frame.json / concept_cam.json are still read from out/blender-hs/<s>/).

WF v11 (research/WORKFLOW-V11.md; scripts/hs/v11gate.py): a subject with subjects/<s>/spec.json runs the v11 gate
(--v10 opts out). The concept camera must be the FROZEN spec-proxy camera (solve_persp_cam.py --proxy spec; refused:
no `frozen` block, a build-fitted camera, spec.json changed since the freeze, a camera changed since the folder's
first v11 pass unless --accept-camera). Part boxes + the HERO check always run. From pass 2: --fix <key[,key]> must
cite hard-failing keys of the previous pass (--fix detail only after a pass with 0 hard fails). After the judge:
score/specgate.mjs (SPEC), score/bands.mjs (BANDS side / top hard, front advisory), HERO through the frozen camera
(contested / camera-contested rows advisory), SIGMA 0.98..1.03, topology, tris, chunky at --final; pass 1 (the
generated block-out) is report-only. Prints the SPEC / BANDS / HERO tables, a SCORE line (IMPROVED / NEUTRAL /
REGRESSED vs the best earlier pass, + ROLLBACK to passK_build.py) and `GATE pass|FAIL {...}`; writes passN_spec.json.
The ortho .04 rule is an advisory WARN. --final is refused unless the pass is the best or equal-best.
WF v11.1 (§11.2): BANDS vs the turnaround is an advisory WARN (never a hard key); HBANDS (score/hbands.mjs, passN_concept
vs the hero through the frozen camera) is printed, advisory; the spec's owner-picked key ratios are hard SPEC rows.

Writes into out/blender-hs/<s>/: passN_{side,front,rear,top,concept}.png, passN_compare.png, passN_stats.json,
passN_<s>.glb, passN_build.py (a snapshot of the build that produced the pass). --final also copies them to
side.png ... concept.png, compare.png, stats.json, <s>.glb.
"""
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))                   # hard_surface/scripts/hs
ROOTDIR = os.path.abspath(os.path.join(HERE, "..", ".."))           # hard_surface
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import imgio  # noqa: E402
from hs import A  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


SUBJECT = _arg("--subject")
if not SUBJECT:
    raise SystemExit("run_pass.py: --subject <s> is required (after the Blender '--')")
PASS = int(_arg("--pass", "0"))
FINAL = "--final" in argv
TAG = f"pass{PASS}"
SDIR = os.path.join(ROOTDIR, "out", "blender-hs", SUBJECT)
BUILD = os.path.abspath(os.path.join(ROOTDIR, _arg("--build"))) if _arg("--build") else os.path.join(SDIR, "build.py")
ODIR = os.path.abspath(os.path.join(ROOTDIR, _arg("--out-dir"))) if _arg("--out-dir") else SDIR
os.makedirs(ODIR, exist_ok=True)
GOLD = os.path.join(ROOTDIR, "out", "ref", "gold", SUBJECT)
TURN = os.path.join(ROOTDIR, "subjects", SUBJECT, "turnaround")
DEFAULT_TRIS = 8000
DIRECT_GATE = 0.04     # WF v10 direct: no ortho view more than this below the best earlier pass (scripts/hs/method.md)
BLOCKOUT_SHARE = 0.05  # direct gate: an earlier pass under this share of the tri budget is a block-out, never a reference
GATE_REF = _arg("--gate-ref", "mature")   # direct gate reference: mature (default) | all (pre-2026-10-10 rule)
if GATE_REF not in ("mature", "all"):
    raise SystemExit(f"run_pass.py: --gate-ref {GATE_REF}: expected mature or all")
HERO = _arg("--hero")                     # None | report | gate (research/PRECISION-VEHICLE-VS-DIRECT.md step 3)
if HERO not in (None, "report", "gate"):
    raise SystemExit(f"run_pass.py: --hero {HERO}: expected report or gate")
DUMP_PARTS = "--dump-part-boxes" in argv or HERO is not None
PARTS_JSON = os.path.join(ROOTDIR, "subjects", SUBJECT, "parts.json")
# --concept-cam <json>: the concept camera file (default <s>/concept_cam.json), e.g. a concept_cam.persp.json under trial
CONCEPT_CAM = os.path.abspath(os.path.join(ROOTDIR, _arg("--concept-cam"))) if _arg("--concept-cam") else None
# WF v11: a subject with subjects/<s>/spec.json (unless --v10) runs the v11 gate (scripts/hs/v11gate.py)
SPEC_JSON = os.path.join(ROOTDIR, "subjects", SUBJECT, "spec.json")
V11 = os.path.exists(SPEC_JSON) and "--v10" not in argv
if HERO and not os.path.exists(PARTS_JSON):
    raise SystemExit(f"run_pass.py: --hero {HERO}: {PARTS_JSON} missing (BUILD-DIRECT.md 'Measured part list')")


def _direct():
    """WF v10: subjects/<s>/subject.json `pipeline: "direct"` (else its class's) = no gold model: no gold row in the
    sheet, the reference numbers are the best earlier pass per view. A vehicle (no such key) is unchanged."""
    try:
        with open(os.path.join(ROOTDIR, "subjects", SUBJECT, "subject.json"), encoding="utf-8") as f:
            sj = json.load(f)
        if "pipeline" in sj:
            return sj["pipeline"] == "direct"
        with open(os.path.join(ROOTDIR, "classes", f"{sj.get('class')}.json"), encoding="utf-8") as f:
            return json.load(f).get("pipeline") == "direct"
    except (OSError, ValueError):
        return False


DIRECT = _direct()


def _json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


for need in ("build.py", "frame.json", "concept_cam.json"):
    if not os.path.exists(BUILD if need == "build.py" else os.path.join(SDIR, need)):
        hint = {"build.py": "copy scripts/hs/build_template.py",
                "frame.json": f"node scripts/hs/dump_frame.mjs --subject {SUBJECT}",
                "concept_cam.json": f"node scripts/hs/dump_concept_cam.mjs --subject {SUBJECT}"}[need]
        raise SystemExit(f"run_pass.py: {BUILD if need == 'build.py' else os.path.join(SDIR, need)} missing ({hint})")

VIEWS_JSON = _json(os.path.join(TURN, "views.json"))
FG_MAX = VIEWS_JSON.get("families", {}).get("fgMax", 235) / 255  # reference fg: darkest channel under this (registered.mjs FG_MAX)


def tri_budget():
    try:
        v = _json(os.path.join(ROOTDIR, "subjects", SUBJECT, "subject.json")).get("ruleOverrides", {}).get("tris", {})
        v = v.get("value") if isinstance(v, dict) else v
        return int(v) if v else DEFAULT_TRIS
    except (OSError, ValueError, TypeError):
        return DEFAULT_TRIS


# ------------------------------------------------------------------------------------------------ current gold numbers
def direct_reference():
    """WF v10 direct subject: the reference numbers of a pass = per view the BEST agree of the earlier passes
    (passK_stats.json, K < this pass, in the out dir and the subject's dir), with that pass's iou. Without --pass
    (rig_pass.py): the look stage's stats.json `current` (the final pass's own reference). No earlier pass = none.
    --gate-ref mature (default, 2026-10-10): block-outs are never a reference: the first pass found (the folder's
    pass 1: BUILD-DIRECT "block-out from the size") and any pass with tris < BLOCKOUT_SHARE x the budget. A block-out
    can fill a hollow / see-through part (ring shroud, solid housing) and outscore the correct model in a view forever
    (replay of the direct pass histories: out/score/gate2/replay.py -> replay.txt). With only block-outs so far
    there is no reference. --gate-ref all: every earlier pass (the old rule)."""
    if "--pass" not in argv:
        st = os.path.join(SDIR, "stats.json")
        cur = (_json(st).get("current") or {}) if os.path.exists(st) else {}
        return dict(cur.get("agree") or {}), dict(cur.get("iou") or {}), cur.get("source", "none")
    ag, io, src = {}, {}, {}
    earlier = {}   # pass number -> stats (first file found wins: the out dir before the subject dir)
    # a separate build written into its own out dir (--build + --out-dir, e.g. out/blender-hs-exp/) is its own
    # reference: the subject folder's passes belong to another build (2026-10-09, Haiku ray_pistol report)
    for d in ((ODIR,) if (_arg("--build") and ODIR != SDIR) else dict.fromkeys((ODIR, SDIR))):
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            m = re.fullmatch(r"pass(\d+)_stats\.json", n)
            if not m or int(m.group(1)) >= PASS or int(m.group(1)) in earlier:
                continue
            try:
                earlier[int(m.group(1))] = _json(os.path.join(d, n))
            except (OSError, ValueError):
                continue
    skipped = []
    if GATE_REF == "mature" and earlier:
        floor = BLOCKOUT_SHARE * tri_budget()
        first = min(earlier)
        skipped = sorted(k for k, st in earlier.items() if k == first or float(st.get("tris") or 0) < floor)
    for k in sorted(earlier):
        if k in skipped:
            continue
        for v, x in (earlier[k].get("scores") or {}).items():
            if isinstance(x, dict) and "agree" in x and (v not in ag or float(x["agree"]) > ag[v]):
                ag[v], io[v], src[v] = float(x["agree"]), float(x.get("iou", x["agree"])), k
    skip = (f"; block-outs skipped: {', '.join(f'pass{k}' for k in skipped)}" if skipped else "")
    if not ag:
        return {}, {}, ("none (direct: the first pass is its own reference)" if not earlier
                        else f"none (direct --gate-ref mature: only block-outs so far{skip})")
    return ag, io, (f"best earlier pass per view (direct, --gate-ref {GATE_REF}): "
                    + ", ".join(f"{v} pass{k}" for v, k in src.items()) + skip)


def current_scores():
    """CURRENT agree / IoU of the gold model.mjs: state.json baseline.views (the gate's numbers) -> view/model-view.json
    -> parsed `node scripts/v7/gold.mjs status` baseline line. Returns ({agree}, {iou}, source)."""
    if DIRECT:
        return direct_reference()
    def pack(views, src):
        ag = {v: float(s["agree"]) for v, s in views.items() if isinstance(s, dict) and "agree" in s}
        io = {v: float(s["iou"]) for v, s in views.items() if isinstance(s, dict) and "iou" in s}
        return (ag, io, src) if ag and io else None
    st = os.path.join(GOLD, "state.json")
    if os.path.exists(st):
        b = (_json(st).get("baseline") or {})
        r = pack(b.get("views") or {}, f"out/ref/gold/{SUBJECT}/state.json baseline ({b.get('file', '?')})")
        if r:
            return r
    mv = os.path.join(GOLD, "view", "model-view.json")
    if os.path.exists(mv):
        r = pack(_json(mv).get("views") or {}, f"out/ref/gold/{SUBJECT}/view/model-view.json")
        if r:
            return r
    try:
        out = subprocess.run(["node", "scripts/v7/gold.mjs", "status", "--subject", SUBJECT], cwd=ROOTDIR,
                             capture_output=True, text=True, timeout=120).stdout
        line = next((ln for ln in out.splitlines() if ln.startswith("baseline ")), "")
        views = {m[0]: {"iou": m[1], "agree": m[2]} for m in re.findall(r"(\w+) iou ([\d.]+) agree ([\d.]+)", line)}
        r = pack(views, "gold.mjs status")
        if r:
            return r
    except (OSError, subprocess.SubprocessError) as e:
        print("WARN gold.mjs status:", e)
    return {}, {}, "none"


CURRENT_AGREE, CURRENT_IOU, CURRENT_SRC = current_scores()


def current_sigma():
    """The gold model's judge sigma (view/model-view.json `sigma`), or None."""
    mv = os.path.join(GOLD, "view", "model-view.json")
    try:
        return float(_json(mv)["sigma"]) if os.path.exists(mv) else None
    except (KeyError, TypeError, ValueError):
        return None


CURRENT_SIGMA = current_sigma()


# ------------------------------------------------------------------------------------------------ build import
def load_build():
    sys.path.insert(0, os.path.dirname(BUILD))
    spec = importlib.util.spec_from_file_location(f"build_{SUBJECT}", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise SystemExit(f"run_pass.py: {BUILD} defines no build() -> (root, parts)")
    return mod


# ------------------------------------------------------------------------------------------------ checks
def topology_report(objs):
    rep = {"objects": {}, "tris": 0}
    tot = {"non_manifold_edges": 0, "boundary_edges": 0, "zero_area_faces": 0, "duplicate_faces": 0, "loose": 0}
    face_keys = {}
    for ob in objs:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        nm = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        bd = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        loose = sum(1 for v in bm.verts if not v.link_faces) + sum(1 for e in bm.edges if not e.link_faces)
        seen = set()
        dup = 0
        for f in bm.faces:
            k = frozenset(v.index for v in f.verts)
            dup += k in seen
            seen.add(k)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        zero = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
        tris = len(bm.faces)
        # coincident faces across objects (centroid within 1 mm, parallel normals) = z-fighting duplicates
        for f in bm.faces:
            c = f.calc_center_median()
            key = (round(c.x, 3), round(c.y, 3), round(c.z, 3))
            face_keys.setdefault(key, []).append((ob.name, f.normal.copy()))
        bm.free()
        rep["objects"][ob.name] = {"tris": tris, "non_manifold_edges": nm, "boundary_edges": bd,
                                   "zero_area_faces": zero, "duplicate_faces": dup, "loose": loose}
        rep["tris"] += tris
        tot["non_manifold_edges"] += nm
        tot["boundary_edges"] += bd
        tot["zero_area_faces"] += zero
        tot["duplicate_faces"] += dup
        tot["loose"] += loose
    cross = 0
    for lst in face_keys.values():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[i][0] != lst[j][0] and abs(lst[i][1].dot(lst[j][1])) > 0.999:
                    cross += 1
    tot["coincident_faces_across_objects"] = cross
    rep["totals"] = tot
    return rep


# ------------------------------------------------------------------------------------------------ render setup
DOTS = []


def set_light(L_author):
    """Cel key light = a fixed direction dotted with the flat face normal in the shader (no lamps, no ambient):
    deterministic bands."""
    L = A(*L_author).normalized()
    for d in DOTS:
        d.inputs[1].default_value = L


def toon_materials():
    """Cel look for the renders only (the glb keeps plain Principled base colours): Normal . L -> 6-band constant
    ramp -> x base colour -> emission."""
    for m in bpy.data.materials:
        if "srgb" not in m:
            continue
        nt = m.node_tree
        base = m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:]
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        DOTS.append(dot)
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        els = ramp.color_ramp.elements
        bands = [(-2.0, 0.58), (0.10, 0.62), (0.25, 0.68), (0.45, 0.78), (0.65, 0.90), (0.85, 1.0)]  # cos(n, L)
        els[0].position, els[0].color = bands[0][0], (bands[0][1],) * 3 + (1,)
        els[1].position, els[1].color = bands[1][0], (bands[1][1],) * 3 + (1,)
        for pos, val in bands[2:]:
            e = els.new(pos)
            e.color = (val,) * 3 + (1,)
        mul = nt.nodes.new("ShaderNodeVectorMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = base[:3]
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        L = nt.links
        L.new(geo.outputs["Normal"], dot.inputs[0])
        L.new(dot.outputs["Value"], ramp.inputs[0])
        L.new(ramp.outputs["Color"], mul.inputs[0])
        L.new(mul.outputs[0], em.inputs["Color"])
        L.new(em.outputs[0], out.inputs["Surface"])


def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
    except TypeError as e:  # pragma: no cover
        print("WARN view transform:", e)
    try:
        sc.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0, 0, 0)
    if sc.world.node_tree:
        bg = sc.world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Strength"].default_value = 0.0
    sun = bpy.data.lights.new("key", "SUN")
    sun.energy = math.pi
    sun.angle = math.radians(2)
    so = bpy.data.objects.new("key", sun)
    sc.collection.objects.link(so)
    L = A(0.40, 1.0, 0.25).normalized()
    so.rotation_euler = L.to_track_quat("Z", "Y").to_euler()
    # ink lines (Freestyle): silhouettes, borders, creases
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = 1.5
    fs = sc.view_layers[0].freestyle_settings
    fs.crease_angle = math.radians(134)
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("ink")
    ls.select_by_edge_types = True
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    ls.select_edge_mark = True          # build.py may mark shallow facet edges (hs.mark_edges: the "freestyle_edge" attribute) to ink them
    ls.linestyle.color = (0.06, 0.06, 0.05)
    ls.linestyle.thickness = 1.5
    return sc


def camera_for(right, up, ox, oy, s, w=1024, h=1024):
    """Orthographic camera such that author point P lands on px = ox + s (P.right), py = oy - s (P.up)."""
    r, u = Vector(right).normalized(), Vector(up).normalized()
    back = r.cross(u)
    c = r * ((w / 2 - ox) / s) + u * ((oy - h / 2) / s) + back * 60.0
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(w, h) / s
    cam.clip_start, cam.clip_end = 1.0, 200.0
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    R = Matrix((A(*r), A(*u), A(*back))).transposed()  # columns = camera X, Y, Z in Blender coords
    ob.matrix_world = Matrix.Translation(A(*c)) @ R.to_4x4()
    return ob


def render_to(path, cam, w=1024, h=1024):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    a = imgio.load(path)
    rgb = a[..., :3] * a[..., 3:4] + (1 - a[..., 3:4])  # composite on white
    out = np.concatenate([rgb, np.ones_like(a[..., :1])], axis=2)
    imgio.save(path, out)
    render_to.last = out
    return a[..., 3] > 0.5, out


# Blender object-scale component of an author axis: author x = Blender X, author y = Blender Z, author z = -Blender Y
_SCALE_IDX = {0: 0, 1: 2, 2: 1}


def view_scale(root, V):
    """views.json scale.right / scale.up (frame kr / ku): squeeze the author axis that the view's right / up runs
    along (the judge divides that axis' metres by it). Root is at the origin, so the squeeze is about the origin."""
    sc = [1.0, 1.0, 1.0]
    for key, k in (("right", V.get("kr", 1)), ("up", V.get("ku", 1))):
        if k != 1:
            ax = max(range(3), key=lambda i: abs(V["spec"][key][i]))
            sc[_SCALE_IDX[ax]] *= k
    root.scale = sc


# ------------------------------------------------------------------------------------------------ scoring
def dump_mesh(objs, path):
    """The built parts as judge_mesh.mjs mesh.json: AUTHOR-frame metres (author x = Blender X, y = Z, z = -Y; a proper
    rotation, so the CCW-outward winding survives), triangulated (loop triangles keep the polygon winding), one
    pseudo-part per (object, material) so the judge's zone families see each material; zone = material name, palette =
    the materials' sRGB hex. Call with the root at identity scale."""
    dg = bpy.context.evaluated_depsgraph_get()
    parts, palette = [], {}
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        mw = ob.matrix_world
        co = [mw @ v.co for v in me.vertices]
        mats = [ms.material for ms in ob.material_slots]
        groups = {}
        for t in me.loop_triangles:
            groups.setdefault(t.material_index, []).append(t.vertices[:])
        for mi, tris in sorted(groups.items()):
            m = mats[mi] if mi < len(mats) and mats[mi] is not None else None
            zone = m.name if m is not None else "default"
            if m is not None and "srgb" in m:
                palette[zone] = m["srgb"]
            remap, pos, idx = {}, [], []
            for tri in tris:
                for vi in tri:
                    if vi not in remap:
                        remap[vi] = len(remap)
                        c = co[vi]
                        pos += [c.x, c.z, -c.y]
                    idx.append(remap[vi])
            pid = ob.name if len(groups) == 1 else f"{ob.name}:{zone}"
            parts.append({"id": pid, "role": ob.get("part", ob.name), "zone": zone, "pos": pos, "tris": idx})
        ev.to_mesh_clear()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"palette": palette, "parts": parts}, f)


def judge_scores(mesh_path, out_path, sigma_fit=None):
    """Run scripts/hs/judge_mesh.mjs (the gold judge's sigma fit + ortho / concept scoring) on the dumped mesh.
    sigma_fit: None = judge_mesh's default (robust, 2026-10-10), "golden" = the judge's golden section alone
    (`--sigma-fit golden` on this script; rig_pass.py uses it for a look stage scored before the robust fit)."""
    cmd = ["node", os.path.join(HERE, "judge_mesh.mjs"), "--subject", SUBJECT, "--mesh", mesh_path, "--out", out_path]
    sigma_fit = sigma_fit or _arg("--sigma-fit")
    if sigma_fit:
        cmd += ["--sigma-fit", sigma_fit]
    r = subprocess.run(cmd, cwd=ROOTDIR, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not os.path.exists(out_path):
        raise SystemExit(f"run_pass.py: judge_mesh.mjs failed ({r.returncode}): {r.stderr[-3000:]}")
    for ln in r.stderr.splitlines():
        if ln.startswith("WARN"):
            print(ln)
    return _json(out_path)


# ------------------------------------------------------------------------------------------------ sheet
FONT = {
    "A": "01110100011000111111100011000110001", "B": "11110100011000111110100011000111110",
    "C": "01110100011000010000100001000101110", "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111", "F": "11111100001000011110100001000010000",
    "G": "01110100011000010111100011000101111", "H": "10001100011000111111100011000110001",
    "I": "01110001000010000100001000010001110", "J": "00111000100001000010000101001001100",
    "K": "10001100101010011000101001001010001", "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001", "N": "10001100011100110101100111000110001",
    "O": "01110100011000110001100011000101110", "P": "11110100011000111110100001000010000",
    "Q": "01110100011000110001101011001001101", "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110", "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110", "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011010101010", "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100", "Z": "11111000010001000100010001000011111",
    "0": "01110100011001110101110011000101110", "1": "00100011000010000100001000010001110",
    "2": "01110100010000100010001000100011111", "3": "11111000100010000010000011000101110",
    "4": "00010001100101010010111110001000010", "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110", "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110", "9": "01110100011000101111000010001001100",
    ".": "00000000000000000000000000110001100", "-": "00000000000000011111000000000000000",
    "/": "00001000010001000100010001000010000", ":": "00000011000110000000011000110000000",
    " ": "0" * 35, "|": "00100001000010000100001000010000100", "+": "00000001000010011111001000010000000",
    "=": "00000000001111100000111110000000000", "(": "00010001000100001000010000010000010",
    ")": "01000001000001000010000100010001000", "<": "00010001000100010000010000010000010",
    ">": "01000001000001000001000100010001000", "_": "00000000000000000000000000000011111",
}


def draw_text(img, x, y, text, scale=2, color=(0.1, 0.1, 0.1)):
    H, W = img.shape[:2]
    for ch in text.upper():
        g = FONT.get(ch, FONT[" "])
        if x + 5 * scale > W:
            break
        for r in range(7):
            for c in range(5):
                if g[r * 5 + c] == "1":
                    img[y + r * scale:y + (r + 1) * scale, x + c * scale:x + (c + 1) * scale, :3] = color
        x += 6 * scale
    return x


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def fit_tile(img, h):
    H, W = img.shape[:2]
    w = max(1, int(round(W * h / H)))
    return imgio.resize_area(img[..., :3], w, h)


# model-view.png layout (scripts/v6/view.mjs viewSheet -> judge.mjs composeRows(rows, out, 240, cols)):
# gap 10, label strip 26, rowH 240 -> row 2 (MODEL) tiles at y 312..552; each ortho tile's width is
# round(crop w * 240 / crop h) with crop = judge.mjs cropOf (frame.json `crops`); the concept tile fills the rest.
SHEET_GAP, SHEET_LABEL, SHEET_ROWH = 10, 26, 240


def current_tiles(names, frame):
    """The current gold model's tiles (orthos + concept) cut from out/ref/gold/<s>/view/model-view.png (row 2),
    each trimmed to its foreground."""
    p = os.path.join(GOLD, "view", "model-view.png")
    if not os.path.exists(p):
        return []
    mv = imgio.load(p)
    y0 = SHEET_GAP + SHEET_LABEL + SHEET_ROWH + SHEET_GAP + SHEET_LABEL
    band = mv[y0:y0 + SHEET_ROWH, :, :3]
    fg = band.min(axis=2) < FG_MAX
    crops = frame.get("crops")
    if crops and all(v in crops for v in names):
        segs, x = [], SHEET_GAP
        for v in names:
            c = crops[v]
            w = int(math.floor((c["x1"] - c["x0"]) * SHEET_ROWH / (c["y1"] - c["y0"]) + 0.5))  # JS Math.round
            segs.append((x, x + w))
            x += w + SHEET_GAP
        segs.append((x, mv.shape[1] - SHEET_GAP))
    else:  # pilot fallback: split the band at >15 px foreground-free column runs
        cols = np.nonzero(fg.any(axis=0))[0]
        if not len(cols):
            return []
        segs, start = [], cols[0]
        for a, b in zip(cols, cols[1:]):
            if b - a > 15:
                segs.append((start, a + 1))
                start = b
        segs.append((start, cols[-1] + 1))
    out = []
    for x0, x1 in segs[:len(names) + 1]:
        m = fg[:, x0:x1]
        if not m.any():
            out.append(np.ones((SHEET_ROWH, max(1, x1 - x0), 3), np.float32))
            continue
        rows = np.nonzero(m.any(axis=1))[0]
        cs = np.nonzero(m.any(axis=0))[0]
        out.append(band[rows[0]:rows[-1] + 1, x0 + cs[0]:x0 + cs[-1] + 1])
    return out


def compose_sheet(path, names, refs, news, scores, tris, budget, label, frame):
    cur = [] if DIRECT else current_tiles(names, frame)
    nrow = 2 if DIRECT else 3      # WF v10 direct: reference | Blender (no gold row)
    cols_names = names + ["concept"]
    TH = 230
    cols = []
    for i, v in enumerate(cols_names):
        rm = refs[v][..., :3].min(axis=2) < FG_MAX
        nm = news[v][..., :3].min(axis=2) < FG_MAX
        Hh, Ww = rm.shape
        x0, y0, x1, y1 = bbox(rm | nm)
        x0, y0, x1, y1 = max(0, x0 - 10), max(0, y0 - 10), min(Ww, x1 + 10), min(Hh, y1 + 10)
        r = fit_tile(refs[v][y0:y1, x0:x1], TH)
        n = fit_tile(news[v][y0:y1, x0:x1], TH)
        c = cur[i] if i < len(cur) else np.ones((TH, TH, 3), np.float32)
        c = fit_tile(c, TH)
        if c.shape[1] > r.shape[1]:  # keep the column width of the reference crop
            c = fit_tile(c, int(TH * r.shape[1] / c.shape[1]))
        cols.append((v, r, c, n))
    gap, lab = 24, 34
    minw = 264 if DIRECT else 0     # WF v10: a weapon's front / rear tiles are narrower than the score text
    W = sum(max(t[1].shape[1], t[2].shape[1], minw) for t in cols) + gap * (len(cols) + 1)
    H = nrow * (TH + lab) + 40
    sheet = np.ones((H, W, 3), np.float32)
    rows = [f"REFERENCE: TURNAROUND {' / '.join(names)} + CONCEPT",
            f"CURRENT: OUT/REF/GOLD/{SUBJECT}/MODEL.MJS (JS KERNEL)"
            + (f" - SIGMA {CURRENT_SIGMA:.4f}" if CURRENT_SIGMA else ""),
            f"NEW: BLENDER BUILD.PY {label} - TRIS {tris}/{budget}"]
    if DIRECT:
        rows = [rows[0], f"BLENDER BUILD.PY (DIRECT) {label} - TRIS {tris}/{budget}"]
    x = gap
    for v, r, c, n in cols:
        cw = max(r.shape[1], c.shape[1], minw)
        for k, t in enumerate((r, n) if DIRECT else (r, c, n)):
            y = k * (TH + lab) + lab
            off = (cw - t.shape[1]) // 2
            hh = min(TH, t.shape[0])
            sheet[y:y + hh, x + off:x + off + t.shape[1]] = t[:hh]
        if v in scores:
            s = scores[v]
            draw_text(sheet, x, nrow * (TH + lab) + 4, f"IOU {s['iou']:.3f} AGREE {s['agree']:.3f}", 2, (0.6, 0.05, 0.05))
            if v in CURRENT_IOU and v in CURRENT_AGREE:
                draw_text(sheet, x, nrow * (TH + lab) + 22, f"{'BEST' if DIRECT else 'CUR'} {CURRENT_IOU[v]:.3f} / {CURRENT_AGREE[v]:.3f}", 2,
                          (0.25, 0.25, 0.25))
        x += cw + gap
    for k, t in enumerate(rows):
        draw_text(sheet, gap, k * (TH + lab) + 10, t, 2)
    imgio.save(path, sheet)


# ------------------------------------------------------------------------------------------------ main
def out(name):
    return os.path.join(ODIR, name)


def main():
    budget = tri_budget()
    v11 = None
    hero_mode, dump_parts = HERO, DUMP_PARTS
    cam_file = CONCEPT_CAM or os.path.join(SDIR, "concept_cam.json")
    if V11:   # refusals happen before anything is built or written
        import v11gate
        v11 = v11gate.preflight(ROOTDIR, SUBJECT, SDIR, ODIR, PASS, cam_file, _arg, argv)
        dump_parts = True
        if os.path.exists(PARTS_JSON):
            hero_mode = hero_mode or "gate"
    mod = load_build()
    root, parts = mod.build()
    objs = [o for o in parts if o.type == "MESH"]
    topo = topology_report(objs)
    clean = all(v == 0 for v in topo["totals"].values())
    print("TRIS", topo["tris"], "/", budget, "TOPO", json.dumps(topo["totals"]))
    if topo["tris"] > budget:
        print(f"WARN tris {topo['tris']} over the budget {budget}")
    if not clean:
        bad = {n: {k: v for k, v in o.items() if k != "tris" and v} for n, o in topo["objects"].items()}
        print("WARN topology:", json.dumps({n: b for n, b in bad.items() if b}))
    if abs(root.scale[0] - 1) + abs(root.scale[1] - 1) + abs(root.scale[2] - 1) > 1e-9:
        print(f"WARN root scale {tuple(root.scale)} reset to 1: the harness fits the judge's sigma itself, never pre-scale")
        root.scale = (1.0, 1.0, 1.0)
    shutil.copyfile(BUILD, out(f"{TAG}_build.py"))
    glb = out(f"{TAG}_{SUBJECT}.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=False, export_apply=True,
                              export_yup=True)
    # scoring: the gold judge's own pipeline on the built triangles (judge_mesh.mjs)
    bpy.context.view_layer.update()
    mesh_path = out(f"{TAG}_mesh.json")
    dump_mesh(objs, mesh_path)
    J = judge_scores(mesh_path, out(f"{TAG}_judge.json"))
    if "--keep-mesh" not in argv:   # --keep-mesh: leave passN_mesh.json for offline re-scoring (judge_mesh.mjs --mesh)
        os.remove(mesh_path)
    sigma = float(J["sigmaRaw"])
    part_rec = None
    if dump_parts:   # root at identity scale here (before the ortho renders squeeze it)
        import part_boxes
        part_rec = part_boxes.part_boxes(objs, part_boxes.load_concept_cam(SUBJECT, CONCEPT_CAM))
        with open(out(f"{TAG}_parts.json"), "w", encoding="utf-8") as f:
            json.dump(part_rec, f, indent=1)
    scores = {v: {k: J["views"][v][k] for k in ("iou", "agree", "drift", "ref_only_px", "model_only_px")}
              for v in J["views"]}
    print(f"SIGMA {J['sigma']:.4f} (gold {CURRENT_SIGMA if CURRENT_SIGMA is not None else '?'})" if not DIRECT
          else f"SIGMA {J['sigma']:.4f} (direct: no gold model; 1.0 = built at the registered size)")
    toon_materials()
    setup_scene()
    frame = _json(os.path.join(SDIR, "frame.json"))
    s = frame["s"]
    names = list(frame["names"])
    refs, news = {}, {}
    for v in names:
        V = frame["views"][v]
        spec = V["spec"]
        view_scale(root, V)
        root.scale = tuple(c * sigma for c in root.scale)   # the judge draws the orthos at k * sigma about the origin
        bpy.context.view_layer.update()
        cam = camera_for(spec["right"], spec["up"], V["ox"], V["oy"], s, V["w"], V["h"])
        back = Vector(spec["right"]).cross(Vector(spec["up"]))
        set_light(tuple(back + Vector((0, 0.8, 0)) + Vector(spec["right"]) * -0.15))
        render_to(out(f"{TAG}_{v}.png"), cam, V["w"], V["h"])
        root.scale = (1.0, 1.0, 1.0)
        refs[v] = imgio.load(os.path.join(TURN, spec.get("file", f"{v}.png")))
        news[v] = render_to.last
    bpy.context.view_layer.update()
    cc = _json(CONCEPT_CAM or os.path.join(SDIR, "concept_cam.json"))
    cpath = os.path.join(ROOTDIR, J["concept"]["target"])
    if cc.get("target") and os.path.normpath(os.path.join(ROOTDIR, cc["target"])) != os.path.normpath(cpath):
        print(f"WARN concept_cam.json was fitted to {cc['target']}, the judge scores against {J['concept']['target']}")
    if isinstance(cc.get("persp"), dict):   # solve_persp_cam.py pinhole (concept_camera.py); else the ortho camera
        import concept_camera
        cam = concept_camera.blender_camera(cc)
        print(f"CONCEPT CAMERA persp FOV {cc['persp']['fov_deg']:.2f} deg ({os.path.relpath(CONCEPT_CAM or os.path.join(SDIR, 'concept_cam.json'), ROOTDIR)})")
    else:
        cam = camera_for(cc["basis"]["right"], cc["basis"]["up"], cc["o"][0], cc["o"][1], cc["s"],
                         cc.get("w", 1024), cc.get("h", 1024))
    set_light((0.15, 1.0, 0.2))  # concept: light from above; vertical walls ~0.62 of the roof
    bpy.context.view_layer.update()   # concept: unscaled (the judge applies no sigma to the concept view)
    render_to(out(f"{TAG}_concept.png"), cam, cc.get("w", 1024), cc.get("h", 1024))
    refs["concept"] = imgio.load(cpath)
    news["concept"] = render_to.last
    for v in names + ["concept"]:
        print("VIEW", v, json.dumps(scores[v]), "| best earlier" if DIRECT else "| gold", json.dumps({"iou": CURRENT_IOU.get(v), "agree": CURRENT_AGREE.get(v)}))
    compose_sheet(out(f"{TAG}_compare.png"), names, refs, news, scores, topo["tris"], budget,
                  f"PASS {PASS} - SIGMA {sigma:.4f}", frame)
    stats = {"subject": SUBJECT, "pass": PASS, "tris": topo["tris"], "budget": budget,
             "over_budget": topo["tris"] > budget, "topology_clean": clean, "topology": topo,
             "scoring": "judge_mesh.mjs = scripts/v6/judge.mjs sigma fit + ortho/concept iou/agree", "sigma": J["sigma"],
             "scores": scores, "judge": J,
             "current": {"source": CURRENT_SRC, "sigma": CURRENT_SIGMA, "agree": CURRENT_AGREE, "iou": CURRENT_IOU},
             "delta_agree": {v: round(scores[v]["agree"] - CURRENT_AGREE[v], 4) for v in scores if v in CURRENT_AGREE},
             "delta_iou": {v: round(scores[v]["iou"] - CURRENT_IOU[v], 4) for v in scores if v in CURRENT_IOU},
             "concept_ref": J["concept"]["target"]}
    if part_rec is not None:
        stats["parts"] = {k: v for k, v in part_rec.items() if k != "mask"}   # the see-through mask stays in passN_parts.json
    hero = None
    if hero_mode:
        hj = out(f"{TAG}_hero.json")
        v11args = ["--spec", SPEC_JSON, "--cam", cam_file] if v11 is not None else []   # contested rows 12 %, advisory rows
        r = subprocess.run(["node", os.path.join(HERE, "score", "heroratio.mjs"), "--subject", SUBJECT,
                            "--boxes", out(f"{TAG}_parts.json"), "--json", hj, *v11args], cwd=ROOTDIR, capture_output=True, text=True,
                           timeout=120)
        if r.returncode not in (0, 1) or not os.path.exists(hj):
            raise SystemExit(f"run_pass.py: heroratio.mjs failed ({r.returncode}): {r.stderr[-2000:]}")
        print(r.stdout.rstrip())
        H_ = _json(hj)
        hero = {"mode": hero_mode, "verdict": H_["verdict"], "fails": H_["fails"], "rows": H_["rows"], "hull": H_["hull"],
                "advisory_fails": H_.get("advisory_fails"), "file": os.path.basename(hj)}
        stats["hero"] = hero
    if DIRECT:
        # WF v10 gate of a direct subject: tris <= budget, topology 0, no ORTHO view more than DIRECT_GATE below the
        # best earlier pass (a sanity check; the concept is a look reference, not gated)
        low = {v: d for v, d in stats["delta_agree"].items() if v != "concept" and d < -DIRECT_GATE}
        stats["pipeline"] = "direct"
        stats["gate"] = {"rule": f"tris <= budget, topology 0, no ortho view more than {DIRECT_GATE} below the best earlier pass"
                                 + (f" (--gate-ref mature: block-outs = the first pass and passes under {BLOCKOUT_SHARE:.0%}"
                                    " of the budget are not a reference)" if GATE_REF == "mature" else " (--gate-ref all)"),
                         "ref_rule": GATE_REF, "ref_source": CURRENT_SRC,
                         "tris_ok": topo["tris"] <= budget, "topology_clean": clean, "below_best_earlier": low,
                         "pass": topo["tris"] <= budget and clean and not low}
        if hero and hero_mode == "gate":   # --hero gate: the HERO verdict is part of the gate
            stats["gate"]["rule"] += ", HERO PASS (heroratio.mjs vs subjects/<s>/parts.json)"
            stats["gate"]["hero"] = hero["verdict"]
            stats["gate"]["pass"] = stats["gate"]["pass"] and hero["verdict"] == "PASS"
        if v11 is None:
            print("GATE", "pass" if stats["gate"]["pass"] else "FAIL", json.dumps(stats["gate"]))
    if DIRECT and dump_parts and os.path.exists(out(f"{TAG}_parts.json")):   # report-only (scripts/hs/score/chunky.mjs)
        cj = out(f"{TAG}_chunky.json")
        r = subprocess.run(["node", os.path.join(HERE, "score", "chunky.mjs"), "--subject", SUBJECT, "--pass", str(PASS),
                            "--glb", glb, "--json", cj], cwd=ROOTDIR, capture_output=True, text=True, timeout=120)
        print(r.stdout.rstrip() if r.returncode == 0 else f"CHUNKY check failed ({r.returncode}): {r.stderr[-300:]}")
        if r.returncode == 0 and os.path.exists(cj):
            stats["chunky_hits"] = len(_json(cj)["hits"])
    refuse_final = False
    if v11 is not None:   # WF v11 gate (scripts/hs/v11gate.py): replaces the direct gate; the .04 rule is advisory
        stats["v11"] = v11gate.finish(v11, ROOTDIR, HERE, SUBJECT, ODIR, TAG, PASS, FINAL, float(J["sigma"]), clean,
                                      topo["tris"], budget, hero, stats.get("chunky_hits"), stats.get("delta_agree"), DIRECT_GATE)
        stats["gate"] = {"rule": "WF v11: SPEC + BANDS(side, top) + HERO(frozen camera, check) + SIGMA 0.98..1.03 + topology + tris"
                                 " (+ chunky 0 at --final); pass 1 report-only; ortho .04 advisory",
                         "pass": stats["v11"]["gate_pass"], "hard_fail_keys": stats["v11"]["hard_fail_keys"],
                         "label": stats["v11"]["label"], "pre_v11": stats.get("gate")}
        if FINAL and stats["v11"]["label"] == "REGRESSED":
            refuse_final = True
            print(f"REFUSED --final: pass {PASS} is REGRESSED against pass {stats['v11']['best_earlier']} (finish from the best pass)")
    with open(out(f"{TAG}_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    os.remove(out(f"{TAG}_judge.json"))
    print("DELTA agree vs current", json.dumps(stats["delta_agree"]))
    print("DELTA iou vs current", json.dumps(stats["delta_iou"]))
    if refuse_final:
        raise SystemExit(1)
    if FINAL:
        for v in names + ["concept", "compare"]:
            shutil.copyfile(out(f"{TAG}_{v}.png"), out(f"{v}.png"))
        shutil.copyfile(glb, out(f"{SUBJECT}.glb"))
        shutil.copyfile(out(f"{TAG}_stats.json"), out("stats.json"))
    print("DONE", out(f"{TAG}_compare.png"))


main()
