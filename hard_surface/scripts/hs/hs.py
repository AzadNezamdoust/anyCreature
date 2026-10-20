"""
hs.py -- generic hard-surface helpers for the per-subject Blender harness (out/blender-hs/<subject>/build.py).

Lifted from the apc_8x8 pilot (out/blender-pilot/apc_8x8/build_apc.py); the subject-specific parts stay in each
subject's build.py. Import it from build.py with `import hs` (run_pass.py puts this folder on sys.path).

FRAME. Every helper takes METRES in the subject's AUTHOR frame (subjects/<s>/turnaround/views.json): near flank +x,
y up, nose +z, ground y = 0, x and z centred. A(x, y, z) maps it to Blender (Z-up): Blender = (x, -z, y), i.e. the
nose points to Blender -Y and the near flank to Blender +X. The glTF exporter's +Y-up conversion turns that back into
the author frame exactly, so <s>.glb lands in the same frame as the turnaround / model.mjs.

Lifecycle used by a build.py:
    root = hs.begin("<subject>", PALETTE)     # wipe the scene, make flat materials, create the root empty
    parts = [part_a(), *part_b(), ...]        # each part = hs.finish(bm, name, [material names], role)
    hs.end(parts)                             # weld + dissolve degenerates, flat shading
    return root, parts

GUARDS (2026-10-10, scripts/hs/fuzz/FINDINGS.md: a 4000-case stress test of these helpers). New builds opt in with
    root = hs.begin("<subject>", PALETTE, guards=True)
Guards OFF (the default, every build finished before 2026-10-10) runs exactly the pre-guard code path (proof:
fuzz/matfix_all.py, all 30 finished builds identical; fuzz/regress.py, stats.json reproduced).
Guards ON adds:
    finish()      welds + dissolves degenerates on every part at creation (before it can be a boolean target)
    temp_object() welds the cutter (1e-5)
    boolean()     a slot-less cutter carries the target's material slots (cut walls take the target's slot of their
                  own face index instead of a new empty slot)
    apply_modifiers() drops EMPTY (None) material slots that no face uses
    mirror_x()    a part whose inner face is within 2e-5 of x = 0 is snapped to x = 0, welded and its in-plane wall
                  deleted (else the two halves share a doubled internal wall)
    bevel_mod()   width clamped to 0.45 x the part's thinnest dimension; a warning outside the safe range
                  (<= 0.25 x thinnest on an uncut primitive, <= 0.1 after a boolean)
    box(chamfer=) chamfer clamped to 0.45 x the thinnest side
    tyre_section  the 0.01 sidewall draft / 0.045 tread-edge chamfer scale with hw (hw < 0.2), else hw < 0.045 inverts
Clamps and out-of-safe-range calls are appended to hs.GUARD_WARN (strings); a build may print them.
The material fix is guarded too: 7 finished builds (laser_smg, revolver, sniper_rifle, smg, plasma_rifle, ray_pistol,
gravity_gun) fill the empty slot themselves after a cut (`if m is None: ob.data.materials[i] = ...`), so dropping it
changes their slot lists; the cutter-slot copy also re-materials cut walls (fuzz/matfix_probe.py, out/fuzz/matfix_v1).
Safe ranges for callers: out/blender-hs/BUILD-DIRECT.md "Helper safe ranges".
Added 2026-10-10 (tube_path, pyramid, ring_stack; additive, existing builds do not call them): with guards ON they
sanitise degenerate input (duplicate path points, n < 3, radius / half-size < 1e-4, a flat pyramid) and log it to
GUARD_WARN; with guards OFF they run the raw code.
Added 2026-10-10: torus (a ring in any plane; additive, same guard pattern; tests out/fuzz/helpers_test/test_helpers.py)
and mark_edges (Freestyle ink marks via the "freestyle_edge" edge attribute; Blender 5.x has no use_freestyle_mark).
Added 2026-10-12 (WF v11, research/WORKFLOW-V11.md §4 / §7): load_spec / consts (the measured part spec
subjects/<s>/spec.json as numbers a build.py reads: SPEC.part("receiver").L, C["REC_L"]; HS_CONST_JSON overrides for
mutants and the phase-2 fit; used keys logged in SPEC_USED for spec_lint.py), and cylinder(n=None): 16 segments for
r >= 0.02, else 12 (every existing build passes n explicitly, so none changes).
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

MATS = {}
GUARDS = False      # set by begin(..., guards=True); see the module docstring
GUARD_WARN = []     # guard clamps / out-of-safe-range calls (strings), cleared by begin()
CUT_PARTS = set()   # as_pointer() of objects a boolean has touched (bevel_mod's safe range), cleared by begin()
ROOT = None  # every finished part is parented to this empty (run_pass scales it for views.json scale.right / up)


# ---------------------------------------------------------------------------------------------------------------- frame
def A(x, y, z):
    """author frame (x near flank, y up, z nose) -> Blender (Z-up, nose -Y)."""
    return Vector((x, -z, y))


# ---------------------------------------------------------------------------------------------------------------- materials
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def make_materials(palette, roughness=0.85):
    """Flat materials from {name: '#rrggbb' (sRGB)}. Principled base colour for the glb; m['srgb'] marks it for the
    cel-render pass in run_pass.py (which rebuilds the node tree for the renders only)."""
    for name, hx in palette.items():
        m = bpy.data.materials.new(name)
        lin = [srgb_to_linear(c) for c in hex_rgb(hx)]
        m.diffuse_color = (*lin, 1.0)
        nt = m.node_tree
        if nt is None:  # Blender < 5 needs use_nodes; 5.x always has a tree (use_nodes is deprecated there)
            m.use_nodes = True
            nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = 0.0
        m["srgb"] = hx
        MATS[name] = m
    return MATS


# ---------------------------------------------------------------------------------------------------------------- scene
def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            coll.remove(d)
    MATS.clear()


def begin(name, palette, guards=False):
    """Wipe the scene, make the palette's materials, create the root empty every part parents to. Returns it.
    guards=True turns the helper guards on for this build (new builds: always; see the module docstring); the
    environment variable HS_GUARDS=1 forces them on for any build without editing it."""
    global ROOT, GUARDS
    ROOT = None
    GUARDS = bool(guards) or os.environ.get("HS_GUARDS") == "1"   # HS_GUARDS=1: force on (regression / what-if runs)
    GUARD_WARN.clear()
    CUT_PARTS.clear()
    reset_scene()
    make_materials(palette)
    ROOT = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ROOT)
    return ROOT


# ---------------------------------------------------------------------------------------------------------------- spec (WF v11)
SPEC_USED = set()   # spec keys a build read (C["KEY"], SPEC.part(id).DIM): spec_lint.py lists the unused ones


class SpecPart:
    """one spec.json part: attributes L H W (D) pos size_author tier section axis ...; dim reads are logged."""

    def __init__(self, rec):
        object.__setattr__(self, "_rec", rec)

    def __getattr__(self, k):
        rec = object.__getattribute__(self, "_rec")
        if k not in rec:
            raise AttributeError(f"spec part {rec.get('id')}: no '{k}'")
        if k in ("L", "H", "W", "D"):
            SPEC_USED.add(f"{rec['id']}.{k}")
        v = rec[k]
        return list(v) if isinstance(v, list) else v

    def get(self, k, default=None):
        return object.__getattribute__(self, "_rec").get(k, default)


class Spec:
    """subjects/<s>/spec.json (scripts/hs/spec_build.mjs) for a build.py: SPEC.part(id), SPEC.data, SPEC.anchor."""

    def __init__(self, data, path=None):
        self.data, self.path = data, path
        self.anchor = data.get("anchor", {})
        self._parts = {P["id"]: SpecPart(P) for P in data.get("parts", [])}

    def part(self, pid):
        if pid not in self._parts:
            raise KeyError(f"spec has no part '{pid}' (parts: {', '.join(self._parts)})")
        return self._parts[pid]

    def parts(self):
        return list(self._parts.values())


def _overrides(overrides):
    import json as _j
    if overrides is None:
        overrides = os.environ.get("HS_CONST_JSON")
    if not overrides:
        return {}
    return _j.loads(overrides) if isinstance(overrides, str) else dict(overrides)


def load_spec(subject_or_path, overrides=None):
    """SPEC = hs.load_spec(SUBJECT): subjects/<s>/spec.json (or a path). overrides / HS_CONST_JSON may set a part dim by
    "<id>.<L|H|W|D>" (the part's size_author follows, centred on its pos); const keys are applied by consts()."""
    import json as _j
    here = os.path.dirname(os.path.abspath(__file__))
    p = subject_or_path if str(subject_or_path).endswith(".json") else os.path.join(here, "..", "..", "subjects", subject_or_path, "spec.json")
    with open(p, encoding="utf-8") as f:
        data = _j.load(f)
    ov = {k: v for k, v in _overrides(overrides).items() if "." in k}
    axes = {"z": {"L": 2, "H": 1, "W": 0}, "x": {"L": 0, "H": 1, "W": 2}, "y": {"L": 1, "W": 0, "H": 2}}
    for k, v in ov.items():
        pid, d = k.split(".", 1)
        P = next((q for q in data.get("parts", []) if q["id"] == pid), None)
        if P is None or d not in ("L", "H", "W", "D"):
            raise KeyError(f"override {k}: no such spec part dim")
        A_ = axes[P.get("axis", "z")]
        for dd in (("H", "W") if d == "D" else (d,)):
            P[dd] = v
            P["size_author"][A_[dd]] = v
        if d == "D":
            P["D"] = v
    return Spec(data, p)


class _Consts(dict):
    def __getitem__(self, k):
        SPEC_USED.add(k)
        return dict.__getitem__(self, k)


def consts(spec, overrides=None):
    """C = hs.consts(SPEC, overrides=os.environ.get("HS_CONST_JSON")): spec.json `const` (<= 12 named numbers) with
    overrides applied (a JSON string or dict; None = the HS_CONST_JSON environment variable). An override key the spec
    does not declare is refused (a mutant / fit may only move declared constants); "<id>.<dim>" keys belong to
    load_spec. Reads are logged in SPEC_USED."""
    base = dict((spec.data if isinstance(spec, Spec) else spec).get("const", {}))
    for k, v in _overrides(overrides).items():
        if "." in k:
            continue
        if k not in base:
            raise KeyError(f"HS_CONST_JSON / overrides: '{k}' is not a spec const ({', '.join(base)})")
        base[k] = v
    return _Consts(base)


def end(parts, weld=1e-5):
    """Weld + dissolve degenerates on every part, flat faceted shading (Generals look)."""
    for ob in parts:
        cleanup(ob, weld)
        for p in ob.data.polygons:
            p.use_smooth = False
    return parts


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    if ROOT is not None:
        ob.parent = ROOT
    return ob


def finish(bm, name, mats, part):
    """bmesh -> object parented to ROOT. mats = material names (face.material_index indexes this list); part = the
    semantic role stored as ob['part']."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mn in mats:
        me.materials.append(MATS[mn])
    ob = bpy.data.objects.new(name, me)
    ob["part"] = part
    if GUARDS:   # weld / dissolve before the part can be a boolean target (octagon ch=0/0.5, collapsed lofts are raw-dirty)
        cleanup(ob)
    return link(ob)


def temp_object(bm, name):
    """A hidden helper object (boolean cutter). NOT parented to ROOT: cutters stay in the same local frame as the
    target (both identity), so the boolean never sees a parent transform."""
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if GUARDS:   # welded cutter
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.hide_render = True
    return ob


def kill(ob):
    me = ob.data
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)


def cleanup(ob, dist=1e-5):
    """Weld coincident verts and dissolve the zero-length edges / zero-area faces that booleans, bevels and
    zero-thickness insets leave behind."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()


# ---------------------------------------------------------------------------------------------------------------- modifiers
def apply_modifiers(ob):
    """Bake an object's modifier stack into its mesh (no bpy.ops: depsgraph evaluation + new_from_object)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)
    if GUARDS and any(m is None for m in me.materials):   # GUARD: a Boolean with a slot-less cutter leaves an EMPTY slot
        used = {p.material_index for p in me.polygons}
        for i in reversed(range(len(me.materials))):
            if me.materials[i] is None and i not in used:
                me.materials.pop(index=i)
    return ob


def add_mirror_x(ob):
    """Mirror across author x = 0 (Blender X == author x, flank to flank). Build the +x side, then mirror."""
    m = ob.modifiers.new("mirror_x", "MIRROR")
    m.use_axis = (True, False, False)
    m.use_mirror_merge = False
    return m


def mirror_x(ob, tol=2e-5):
    """add_mirror_x + apply. GUARD: a part whose inner face lies within `tol` of x = 0 would keep a doubled internal wall
    (4 faces on its border edges); snap those verts onto x = 0, weld, delete the in-plane faces."""
    if not GUARDS:
        add_mirror_x(ob)
        return apply_modifiers(ob)
    if ob.modifiers:
        apply_modifiers(ob)
    add_mirror_x(ob)
    near = [v for v in ob.data.vertices if abs(v.co.x) < tol]
    if not near:
        return apply_modifiers(ob)
    for v in near:
        v.co.x = 0.0
    apply_modifiers(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2 * tol)
    wall = [f for f in bm.faces if all(abs(v.co.x) < tol for v in f.verts)]
    bmesh.ops.delete(bm, geom=wall, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    return ob


BEVEL_SAFE_PRIM = 0.25   # bevel width / thinnest dimension, 1 segment, on a part no boolean has touched yet
BEVEL_SAFE_CUT = 0.10    # ... after a boolean (scripts/hs/fuzz data, 2026-10-11 re-read per step: primitive + 1 segment
#                          0.2-0.9 % defects at ratio 0.05-0.15, 1.7 % at 0.15-0.20, 0 % at 0.20-0.45 (n 60-2466);
#                          after a cut 7.5-12.6 % at every ratio up to 0.30, 16 % at 0.30-0.45). Main-mass chamfers of
#                          12-20 mm (BUILD-DIRECT.md "Chunky detail") are safe on a primitive >= 0.05-0.08 m thick.


def bevel_mod(ob, width, angle_deg=30.0, segments=1):
    """Angle-limited chamfer on every hard edge (1 segment = the Generals flat bevel).
    GUARD: width clamped to 0.45 x the thinnest dimension of the part's base mesh; a warning outside the safe range
    (1 segment, width/seg >= 0.3 mm, width <= BEVEL_SAFE_PRIM x thinnest on an uncut primitive, BEVEL_SAFE_CUT x
    thinnest once a boolean has touched the part: boolean() / cut() record it in CUT_PARTS; no custom property, so the
    glb extras stay as they were)."""
    if GUARDS and ob.data.vertices:
        md = min(max(v.co[i] for v in ob.data.vertices) - min(v.co[i] for v in ob.data.vertices) for i in range(3))
        if width > 0.45 * md:   # >= half the thinnest dimension inverts / self-intersects the part
            GUARD_WARN.append(f"{ob.name}: bevel_mod width {width:.4f} > 0.45 x thinnest dimension {md:.4f}: clamped")
            width = 0.45 * md
        cut_ = ob.as_pointer() in CUT_PARTS or any(m.type == "BOOLEAN" for m in ob.modifiers)
        lim = BEVEL_SAFE_CUT if cut_ else BEVEL_SAFE_PRIM
        if width / segments < 3e-4 or width > lim * md + 1e-7 or segments > 1:
            GUARD_WARN.append(f"{ob.name}: bevel_mod width {width:.4f} segments {segments} thinnest {md:.4f}: outside the "
                              f"safe range (1 segment, width/seg >= 0.3 mm, width <= {lim} x thinnest"
                              f"{' after a boolean: bevel the primitive first' if cut_ else ''})")
    m = ob.modifiers.new("chamfer", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle_deg)
    m.use_clamp_overlap = True
    m.harden_normals = False
    return m


def boolean(ob, cutter, op):
    """Boolean modifier with the MANIFOLD solver (Blender 4.5+/5.x: manifold-in, manifold-out, fast). op is
    'DIFFERENCE' | 'UNION' | 'INTERSECT'. Stack several, then apply_modifiers once."""
    if GUARDS and not cutter.data.materials:   # GUARD: cutter carries the target's slots (no empty slot left behind)
        for mat in ob.data.materials:
            cutter.data.materials.append(mat)
    m = ob.modifiers.new("bool_" + op.lower(), "BOOLEAN")
    CUT_PARTS.add(ob.as_pointer())   # bevel_mod's safe range drops to BEVEL_SAFE_CUT once a boolean touched the part
    m.operation = op
    m.object = cutter
    m.solver = "MANIFOLD"
    return m


def cut(ob, cutter_bm, op="DIFFERENCE", name="cutter"):
    """One-shot boolean: bmesh cutter -> temp object -> MANIFOLD boolean -> apply -> cutter deleted.
    (Any modifiers already on `ob` are applied too, in stack order.)"""
    cutter = temp_object(cutter_bm, name)
    boolean(ob, cutter, op)
    apply_modifiers(ob)
    kill(cutter)
    return ob


# ---------------------------------------------------------------------------------------------------------------- bmesh primitives
def loft(bm, rings, cap0=True, cap1=True, mat=0):
    """Connect rings (lists of Blender Vectors, equal length, closed loops) with quads; cap the ends.
    Returns (verts per ring, faces) with faces[-1] = the last cap when cap1."""
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    faces = []
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    if cap0:
        faces.append(bm.faces.new(list(reversed(vs[0]))))
    if cap1:
        faces.append(bm.faces.new(vs[-1]))
    for f in faces:
        f.material_index = mat
    return vs, faces


def prism(bm, poly, axis, a0, a1, mat=0):
    """2D polygon extruded along an author axis from a0 to a1. axis 'x': poly is (z, y); 'z': (x, y); 'y': (x, z)."""
    def P(u, v, w):
        if axis == "x":
            return A(w, v, u)
        if axis == "z":
            return A(u, v, w)
        return A(u, w, v)
    return loft(bm, [[P(u, v, a0) for u, v in poly], [P(u, v, a1) for u, v in poly]], mat=mat)


def mirror_profile(half):
    """Right half of a symmetric profile [(x, y), ...] from the bottom centre up -> the full closed loop."""
    return [(-x, y) for x, y in reversed(half)] + list(half)


def profile_object(name, poly, axis, a0, a1, mats, part, bevel=0.0, angle_deg=30.0, mat=0):
    """Beveled extrusion: prism of a profile -> object, optional angle-limited chamfer, applied."""
    bm = bmesh.new()
    prism(bm, poly, axis, a0, a1, mat=mat)
    ob = finish(bm, name, mats, part)
    if bevel > 0:
        bevel_mod(ob, bevel, angle_deg)
        apply_modifiers(ob)
    return ob


def box(bm, c, size, mat=0, chamfer=0.0):
    """Axis-aligned author box (centre, full size); optional chamfer on every edge (bmesh bevel, 1 segment)."""
    cx, cy, cz = c
    sx, sy, sz = (s / 2 for s in size)
    ring = lambda y: [A(cx - sx, y, cz - sz), A(cx + sx, y, cz - sz), A(cx + sx, y, cz + sz), A(cx - sx, y, cz + sz)]
    vs, faces = loft(bm, [ring(cy - sy), ring(cy + sy)], mat=mat)
    if chamfer > 0:
        if GUARDS and chamfer > 0.45 * min(size):   # chamfer >= 0.49 x the thinnest side breaks 92 % of boxes
            GUARD_WARN.append(f"box chamfer {chamfer:.4f} > 0.45 x thinnest side {min(size):.4f}: clamped")
            chamfer = 0.45 * min(size)
        edges = list({e for f in faces for e in f.edges})
        bmesh.ops.bevel(bm, geom=edges, offset=chamfer, offset_type="OFFSET", segments=1, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
    return faces


def oriented_box(bm, centre, axes, size, mat=0):
    """Box with arbitrary orthonormal author axes (u, v, w) and full size (su, sv, sw)."""
    u, v, w = (Vector(a).normalized() for a in axes)
    c = Vector(centre)
    hu, hv, hw = (s / 2 for s in size)
    ring = lambda t: [c + u * a * hu + v * b * hv + w * t * hw for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return loft(bm, [[A(*p) for p in ring(-1)], [A(*p) for p in ring(1)]], mat=mat)


def circle(centre, axis_u, axis_v, r, n, phase=0.0):
    """author-frame circle points (returned as Blender vectors)."""
    c = Vector(centre)
    u, v = Vector(axis_u), Vector(axis_v)
    out = []
    for i in range(n):
        t = phase + 2 * math.pi * i / n
        p = c + u * (r * math.cos(t)) + v * (r * math.sin(t))
        out.append(A(*p))
    return out


def cylinder(bm, c0, c1, r, n=None, mat=0, r1=None, phase=None):
    """Closed cylinder / frustum from author point c0 to c1 (radius r -> r1). faces[-1] = the c1 cap.
    n = segments; None (WF v11) = 16 when r >= 0.02 (a round part reads round), else 12."""
    if n is None:
        n = 16 if r >= 0.02 else 12
    c0, c1 = Vector(c0), Vector(c1)
    ax = (c1 - c0).normalized()
    u = ax.orthogonal().normalized()
    v = ax.cross(u).normalized()
    ph = math.pi / n if phase is None else phase
    return loft(bm, [circle(c0, u, v, r, n, ph), circle(c1, u, v, r if r1 is None else r1, n, ph)], mat=mat)


def tube_path(bm, points, r, n=8, mat=0):
    """Closed round tube swept along an open polyline of author points (hoses, cables, pipes, handles), end caps
    included. One ring per point, perpendicular to the bisector of the two adjoining segments and widened by
    1/cos(half bend angle) (capped at 2) so the wall keeps its thickness through a bend; the ring frame is parallel
    transported, so the tube does not twist. r = radius, n = facets. Keep r well under the shortest segment / bend
    radius or the wall folds into itself (topology stays closed, the shape is wrong). Returns (rings, faces) like loft.
    GUARDS: consecutive points closer than 1e-5 are dropped, n >= 3, r >= 1e-4, a <2-point path draws nothing, a path
    that folds back > 171 degrees is only warned about (its walls overlap); every fix is appended to GUARD_WARN."""
    pts = [Vector(p) for p in points]
    if GUARDS:
        keep = [pts[0]] if pts else []
        for p in pts[1:]:
            if (p - keep[-1]).length >= 1e-5:
                keep.append(p)
        if len(keep) != len(pts):
            GUARD_WARN.append(f"tube_path: {len(pts) - len(keep)} duplicate point(s) dropped")
        pts = keep
        if n < 3:
            GUARD_WARN.append(f"tube_path n={n} < 3: set to 3")
            n = 3
        if r < 1e-4:
            GUARD_WARN.append(f"tube_path r={r:.5f} < 1e-4: set to 1e-4")
            r = 1e-4
        if len(pts) < 2:
            GUARD_WARN.append("tube_path: fewer than 2 distinct points, nothing built")
            return [], []
    segs = [(b - a).normalized() for a, b in zip(pts, pts[1:])]
    if GUARDS and any(a.dot(b) < -0.99 for a, b in zip(segs, segs[1:])):
        GUARD_WARN.append("tube_path: the path folds back on itself (> 171 degrees); the walls overlap, split the path")
    tans, scales = [], []
    for i in range(len(pts)):
        if i == 0 or i == len(pts) - 1:
            tans.append(segs[0] if i == 0 else segs[-1])
            scales.append(1.0)
        else:
            t = segs[i - 1] + segs[i]
            t = t.normalized() if t.length > 1e-6 else segs[i]      # a 180 degree fold has no bisector
            tans.append(t)
            scales.append(min(2.0, 1.0 / max(segs[i - 1].dot(t), 0.5)))
    u = tans[0].orthogonal().normalized()
    rings = []
    for p, t, k in zip(pts, tans, scales):
        u = (u - t * u.dot(t))                                      # parallel transport: keep the last u, re-square it
        u = u.normalized() if u.length > 1e-6 else t.orthogonal().normalized()
        v = t.cross(u).normalized()
        rings.append([A(*(p + u * (r * k * math.cos(2 * math.pi * i / n)) + v * (r * k * math.sin(2 * math.pi * i / n))))
                      for i in range(n)])
    return loft(bm, rings, mat=mat)


def pyramid(bm, base_c, base_hw, base_hd, tip, mat=0, axis="y"):
    """Closed four-sided point: a rectangle (centre base_c, half-sizes base_hw / base_hd) plus an apex `tip` (author
    points). The base lies in the plane normal to `axis` ('y': hw along x, hd along z -- a spike pointing up/down;
    'z': hw along x, hd along y -- a pick / chisel pointing along the barrel; 'x': hw along z, hd along y). The tip may
    sit anywhere off that plane (a leaning spike, an off-centre wedge). Returns (verts, faces) with faces[0] the base.
    GUARDS: half-sizes >= 1e-4; a tip within 1e-4 of the base plane (flat, not closed) is pushed 1e-4 off it; every
    fix is appended to GUARD_WARN."""
    c, tip = Vector(base_c), Vector(tip)
    ia = {"x": 0, "y": 1, "z": 2}[axis]
    iu, iv = {"y": (0, 2), "z": (0, 1), "x": (2, 1)}[axis]
    if GUARDS:
        if base_hw < 1e-4 or base_hd < 1e-4:
            GUARD_WARN.append(f"pyramid half-size ({base_hw:.5f}, {base_hd:.5f}) < 1e-4: raised")
            base_hw, base_hd = max(base_hw, 1e-4), max(base_hd, 1e-4)
        if abs(tip[ia] - c[ia]) < 1e-4:
            GUARD_WARN.append("pyramid tip lies in the base plane: pushed 1e-4 off it")
            tip[ia] = c[ia] + 1e-4
    ring = []
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = c.copy()
        p[iu] += a * base_hw
        p[iv] += b * base_hd
        ring.append(p)
    nrm = (ring[1] - ring[0]).cross(ring[2] - ring[0])
    if nrm.dot(tip - c) < 0:                                        # ring counter-clockwise seen from the tip
        ring.reverse()
    b = [bm.verts.new(A(*p)) for p in ring]
    t = bm.verts.new(A(*tip))
    faces = [bm.faces.new(list(reversed(b)))]
    for i in range(4):
        faces.append(bm.faces.new((b[i], b[(i + 1) % 4], t)))
    for f in faces:
        f.material_index = mat
    return [b + [t]], faces


def ring_stack(bm, axis_c0, axis_c1, radii, n, mat=0):
    """Closed lofted stack along the axis c0 -> c1 (author points): len(radii) rings equally spaced, ring i of radius
    radii[i]. Alternating radii make a ribbed grip / bellows / hose ([0.020, 0.024] * 6 + [0.020]); a smooth taper is a
    plain ramp. Both ends are capped. Returns (verts per ring, faces) like loft; faces[-1] = the c1 cap.
    GUARDS: n >= 3, every radius >= 1e-3 (a 0 radius would collapse a ring into zero-area faces), fewer than 2 rings or
    c0 == c1 draws nothing; every fix is appended to GUARD_WARN."""
    c0, c1 = Vector(axis_c0), Vector(axis_c1)
    radii = list(radii)
    if GUARDS:
        if n < 3:
            GUARD_WARN.append(f"ring_stack n={n} < 3: set to 3")
            n = 3
        if any(r < 1e-3 for r in radii):
            GUARD_WARN.append("ring_stack: radius < 1e-3 raised to 1e-3")
            radii = [max(r, 1e-3) for r in radii]
        if len(radii) < 2 or (c1 - c0).length < 1e-5:
            GUARD_WARN.append("ring_stack: needs >= 2 radii and c0 != c1, nothing built")
            return [], []
    ax = (c1 - c0).normalized()
    u = ax.orthogonal().normalized()
    v = ax.cross(u).normalized()
    m = len(radii) - 1
    rings = [circle(c0 + (c1 - c0) * (i / m), u, v, r, n, math.pi / n) for i, r in enumerate(radii)]
    return loft(bm, rings, mat=mat)


def octagon(cx, cz, y, hf, hr, hx, ch=0.38):
    """Irregular chamfered octagon ring at author height y (turret bodies): front half-depth hf, rear hr,
    half-width hx, corner chamfer fraction ch. Loft several for a faceted turret."""
    pts = [(hx * (1 - ch), hf), (hx, hf * (1 - ch)), (hx, -hr * (1 - ch)), (hx * (1 - ch), -hr),
           (-hx * (1 - ch), -hr), (-hx, -hr * (1 - ch)), (-hx, hf * (1 - ch)), (-hx * (1 - ch), hf)]
    return [A(cx + x, y, cz + z) for x, z in pts]


def bore(bm, cap_face, wall=0.015, depth=0.06, mat=None):
    """Hollow muzzle / tube end / pit: a flat lip (inset, thickness = wall, no depth) then straight walls (a second,
    zero-thickness inset pushed `depth` inward). One inset with depth would make a funnel. Returns the wall faces."""
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.inset_individual(bm, faces=[cap_face], thickness=wall, depth=0.0, use_even_offset=True)
    res = bmesh.ops.inset_individual(bm, faces=[cap_face], thickness=0.0, depth=-depth, use_even_offset=True)
    if mat is not None:
        cap_face.material_index = mat
        for f in res["faces"]:
            f.material_index = mat
    return res["faces"]


pit = bore  # an inset pit (grille, recess) is the same two-step inset


def plane_cutter(bm, p0, p1, p2, out, half=0.9, depth=2.0):
    """A slab cutter whose face is the plane through three author points, extending `depth` along the side of
    `out` (author vector). DIFFERENCE it to chamfer a corner (nose / rear corner facets)."""
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    n = (p1 - p0).cross(p2 - p0).normalized()
    if n.dot(Vector(out)) < 0:
        n = -n
    c = (p0 + p1 + p2) / 3
    u = (p1 - p0).normalized()
    v = n.cross(u).normalized()
    ring = lambda d: [A(*(c + u * a * half + v * b * half + n * d)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return loft(bm, [ring(0.0), ring(depth)])


def torus_x_y(bm, centre, R, r, nu=6, nv=4, mat=0):
    """Low-poly torus in the author x-y plane (axis along z): shackles, rings. Returns the faces."""
    cx, cy, zr = centre
    rings = []
    for i in range(nu):
        t = 2 * math.pi * i / nu
        cen = Vector((cx + R * math.cos(t), cy + R * math.sin(t), zr))
        radial = Vector((math.cos(t), math.sin(t), 0))
        rings.append([A(*(cen + radial * (r * math.cos(2 * math.pi * k / nv)) + Vector((0, 0, r * math.sin(2 * math.pi * k / nv)))))
                      for k in range(nv)])
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    faces = []
    for i in range(nu):
        j = (i + 1) % nu
        for k in range(nv):
            kk = (k + 1) % nv
            f = bm.faces.new((vs[i][k], vs[i][kk], vs[j][kk], vs[j][k]))
            f.material_index = mat
            faces.append(f)
    return faces


def torus(bm, centre, axis, R, r, nu=16, nv=8, mat=0):
    """Closed low-poly torus (a ring: collar, grommet, shroud lip, shackle, hose clamp) in ANY plane. centre = author
    point, axis = the ring's axis as an author vector or 'x' / 'y' / 'z' (the ring lies in the plane normal to it), R =
    the centre-line radius, r = the tube radius, nu = segments round the ring, nv = segments round the tube. The section
    polygon is centred on R, so the volume is exactly nu sin(2 pi / nu) x (nv / 2) sin(2 pi / nv) r^2 x R.
    torus_x_y(bm, (x, y, z), R, r, nu, nv) == torus(bm, (x, y, z), 'z', R, r, nu, nv) up to the start angle.
    Returns (verts per ring, faces) like loft. Keep r < R (r >= R folds the inner wall through the axis).
    GUARDS: nu, nv >= 3; r >= 1e-4; r >= R is clamped to 0.95 R; a zero axis or R < 1e-4 draws nothing; every fix is
    appended to GUARD_WARN."""
    if isinstance(axis, str):
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    a = Vector(axis)
    if GUARDS:
        if nu < 3 or nv < 3:
            GUARD_WARN.append(f"torus nu={nu} nv={nv}: raised to >= 3")
            nu, nv = max(nu, 3), max(nv, 3)
        if a.length < 1e-9 or R < 1e-4:
            GUARD_WARN.append("torus: zero axis or R < 1e-4, nothing built")
            return [], []
        if r < 1e-4:
            GUARD_WARN.append(f"torus r={r:.5f} < 1e-4: set to 1e-4")
            r = 1e-4
        if r >= R:
            GUARD_WARN.append(f"torus r={r:.5f} >= R={R:.5f}: the inner wall crosses the axis, r clamped to 0.95 R")
            r = 0.95 * R
    a = a.normalized()
    u = a.orthogonal().normalized()
    v = a.cross(u).normalized()      # u x v = a: rings ordered round +a, faces wound outward
    c = Vector(centre)
    rings = []
    for i in range(nu):
        t = 2 * math.pi * i / nu
        e = u * math.cos(t) + v * math.sin(t)
        rings.append([A(*(c + e * (R + r * math.cos(2 * math.pi * k / nv)) + a * (r * math.sin(2 * math.pi * k / nv))))
                      for k in range(nv)])
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    faces = []
    for i in range(nu):
        j = (i + 1) % nu
        for k in range(nv):
            kk = (k + 1) % nv
            f = bm.faces.new((vs[i][k], vs[j][k], vs[j][kk], vs[i][kk]))
            f.material_index = mat
            faces.append(f)
    return vs, faces


def mark_edges(target, edges):
    """Freestyle edge marks (run_pass inks marked edges: shallow facet lines the crease rule skips, panel seams).
    Blender 5.x has NO MeshEdge.use_freestyle_mark (AttributeError); the mark is the generic BOOLEAN EDGE attribute
    "freestyle_edge" (verified 5.1.2, out/score/gate2/freestyle_test.py). target = a mesh object or a bmesh; edges =
    an iterable of edge indices (or BMEdges for a bmesh), or a callable f(a, b) -> bool given each edge's two end points
    in the AUTHOR frame. Returns the number of edges marked. Mark LAST, on the finished part (after hs.cut / mirror_x /
    hs.end), since booleans and welds renumber edges."""
    def author(co):
        return Vector((co.x, co.z, -co.y))
    if isinstance(target, bmesh.types.BMesh):
        bm = target
        bm.edges.ensure_lookup_table()
        lay = bm.edges.layers.bool.get("freestyle_edge") or bm.edges.layers.bool.new("freestyle_edge")
        if callable(edges):
            sel = [e for e in bm.edges if edges(author(e.verts[0].co), author(e.verts[1].co))]
        else:
            sel = [bm.edges[e] if isinstance(e, int) else e for e in edges]
        for e in sel:
            e[lay] = True
        return len(sel)
    me = target.data
    if callable(edges):
        vs = me.vertices
        sel = [e.index for e in me.edges if edges(author(vs[e.vertices[0]].co), author(vs[e.vertices[1]].co))]
    else:
        sel = list(edges)
    at = me.attributes.get("freestyle_edge") or me.attributes.new("freestyle_edge", "BOOLEAN", "EDGE")
    for i in sel:
        at.data[i].value = True
    return len(sel)


def wire_cage(ob, thickness=0.026):
    """Turn an open lofted frame into bars (Wireframe modifier, replace). Apply with apply_modifiers / mirror_x."""
    wf = ob.modifiers.new("bars", "WIREFRAME")
    wf.thickness = thickness
    wf.use_even_offset = True
    wf.use_relative_offset = False
    wf.use_replace = True
    wf.use_boundary = True
    return wf


# ---------------------------------------------------------------------------------------------------------------- wheels
def tyre_section(r, hw):
    """Default chamfered tyre cross-section (radius, u along the axle from the tyre centre plane), scaled from the
    apc pilot (R 0.468, hw 0.20: bore 0.285, shoulder 0.425, 0.045 tread-edge chamfer, 0.01 sidewall draft)."""
    k = r / 0.468
    if not GUARDS:
        return [(0.285 * k, -hw + 0.01), (0.425 * k, -hw), (r, -hw + 0.045), (r, 0.0),
                (r, hw - 0.045), (0.425 * k, hw), (0.285 * k, hw - 0.01)]
    kw = min(1.0, hw / 0.20)   # GUARD: the 0.01 / 0.045 offsets were absolute; hw < 0.045 inverted the section
    return [(0.285 * k, -hw + 0.01 * kw), (0.425 * k, -hw), (r, -hw + 0.045 * kw), (r, 0.0),
            (r, hw - 0.045 * kw), (0.425 * k, hw), (0.285 * k, hw - 0.01 * kw)]


def tyre(bm, centre, r, hw, tread_h=0.042, nseg=16, section=None, lug_len=0.8, lug_drop=0.03, side=1):
    """One tyre (axle along author x) at author `centre` = (x of the tyre centre plane, y, z): the section revolved
    in nseg steps, plus staggered block tread: every face lane at the full radius is extruded tread_h outward, lane j
    on segments i % 2 == j % 2; lugs keep lug_len of the base in the rolling direction and the shoulder-side edge
    wraps over the shoulder (dropped lug_drop). side = +1 builds outward to +x (mirror it), -1 to -x."""
    sec = section or tyre_section(r, hw)
    sec = [(rr, u * side) for rr, u in sec]
    R = max(rr for rr, _ in sec)
    n = len(sec)
    cx, cy, cz = centre
    ctr = Vector((cx, cy, cz))
    rings = []
    for i in range(nseg):
        t = 2 * math.pi * i / nseg
        radial = Vector((0, math.cos(t), math.sin(t)))
        rings.append([A(*(ctr + radial * rr + Vector((u, 0, 0)))) for rr, u in sec])
    verts = [[bm.verts.new(p) for p in ring] for ring in rings]
    lane_ks = [k for k in range(n) if sec[k][0] == R and sec[(k + 1) % n][0] == R]
    lanes = {k: [] for k in lane_ks}
    for i in range(nseg):
        j = (i + 1) % nseg
        for k in range(n):
            kk = (k + 1) % n
            f = bm.faces.new((verts[i][k], verts[i][kk], verts[j][kk], verts[j][k]))
            if k in lanes:
                lanes[k].append((i, f))
    blocks = []
    for li, k in enumerate(lane_ks):
        blocks += [f for i, f in lanes[k] if i % 2 == li % 2]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    res = bmesh.ops.extrude_discrete_faces(bm, faces=blocks)
    X = Vector((1, 0, 0))
    cB = A(cx, cy, cz)
    u_rim = abs(sec[0][1])                     # sidewall half width at the bore
    u_edge = abs(sec[2][1]) if n > 2 else hw   # tread edge (start of the shoulder chamfer)
    wrap = u_rim / u_edge * 2 - 1
    for f in res["faces"]:
        fc = f.calc_center_median()
        rad = Vector((0, fc.y - cB.y, fc.z - cB.z)).normalized()
        tan = X.cross(rad)
        top = fc + rad * tread_h
        for v in f.verts:
            d = v.co - fc
            du, dt = d.x, d.dot(tan)
            outer = abs(v.co.x - cx) > hw * 0.5
            v.co = top + tan * dt * lug_len + X * (du * wrap if outer else du)
            if outer:
                v.co -= rad * lug_drop
    return res["faces"]


HUB_RINGS = [(None, 0.29), (0.0, 0.29), (0.025, 0.26), (0.025, 0.13), (0.08, 0.13), (0.095, 0.10)]


def hub(bm, centre, hw, rings=None, n=10, recess=0.06, bolts=8, bolt_r=0.195, bolt_size=(0.024, 0.015),
        bolt_dx=(0.02, 0.05), scale=1.0, side=1):
    """Recessed rim + raised hub boss + bolt studs for a tyre at author centre (x of the tyre centre plane, y, z).
    rings = (dx outward from the rim face, radius); dx None = the inner disc inside the tyre bore (x - hw + 0.03).
    The rim face sits `recess` inside the sidewall. scale multiplies every radius / offset (apc pilot = 1.0 at a
    0.468 m tyre: pass r / 0.468). side = +1 outward to +x (mirror it), -1 to -x."""
    rings = rings or HUB_RINGS
    cx, cy, cz = centre
    rim_out = cx + side * (hw - recess * scale)
    ax = lambda u, r: circle((u, cy, cz), (0, 1, 0), (0, 0, 1), r, n, math.pi / n)
    loop = []
    for dx, r in rings:
        u = cx - side * (hw - 0.03 * scale) if dx is None else rim_out + side * dx * scale
        loop.append(ax(u, r * scale))
    loft(bm, loop)
    for b in range(bolts):
        t = 2 * math.pi * b / bolts + math.pi / bolts
        y, z = cy + bolt_r * scale * math.cos(t), cz + bolt_r * scale * math.sin(t)
        cylinder(bm, (rim_out + side * bolt_dx[0] * scale, y, z), (rim_out + side * bolt_dx[1] * scale, y, z),
                 bolt_size[0] * scale, 4, r1=bolt_size[1] * scale)


def wheel(bm_tyre, bm_hub, centre, r, hw, **kw):
    """tyre() into bm_tyre + hub() into bm_hub (kw split by name: tread_h/nseg/section/lug_len/lug_drop -> tyre,
    rings/recess/bolts/bolt_r/bolt_size/bolt_dx/scale -> hub; side -> both)."""
    tk = {k: kw[k] for k in ("tread_h", "nseg", "section", "lug_len", "lug_drop", "side") if k in kw}
    hk = {k: kw[k] for k in ("rings", "n", "recess", "bolts", "bolt_r", "bolt_size", "bolt_dx", "scale", "side") if k in kw}
    tyre(bm_tyre, centre, r, hw, **tk)
    hub(bm_hub, centre, hw, **hk)
