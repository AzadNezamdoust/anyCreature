# ROM sweep gate (t8/joint_graph). Headless:
#   blender -b --factory-startup -P rom_sweep.py -- <rigged.glb> <joints.json> <outdir> [--body body]
# Drives each declared joint to its limits (flex, ext, side+-, twist+-) one at a time and measures, on the skinned
# body: local volume kept around the joint (tet fan to the pivot, >= vol_min), max edge stretch (<= stretch_max),
# triangles flipped against their dominant bone's rigid rotation, and NEW BVH self-overlap pairs vs rest.
# Also renders 4 combined extreme poses (clay, hero + side) for side-by-side comparison.
import bpy, sys, json, os, math
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, JS, OUT = argv[0], argv[1], argv[2]
BODY = argv[argv.index('--body') + 1] if '--body' in argv else None
os.makedirs(OUT, exist_ok=True)
CFG = json.load(open(JS))
G = CFG['gates']

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
skinned = [o for o in meshes if any(m.type == 'ARMATURE' for m in o.modifiers)]
if BODY:
    body = next(o for o in meshes if o.name.startswith(BODY))
else:
    body = max(skinned or meshes, key=lambda o: len(o.data.vertices))
for o in [arm] + meshes:
    if o.animation_data:
        o.animation_data.action = None
dg = bpy.context.evaluated_depsgraph_get()
PB = arm.pose.bones
AW = arm.matrix_world


def reset():
    for pb in PB:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def coords(ob=body):
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg)
    m = e.to_mesh()
    W = ob.matrix_world
    P = [W @ v.co for v in m.vertices]
    T = [tuple(t.vertices) for t in m.loop_triangles] if m.loop_triangles else None
    if T is None:
        m.calc_loop_triangles(); T = [tuple(t.vertices) for t in m.loop_triangles]
    polys = [tuple(p.vertices) for p in m.polygons]
    e.to_mesh_clear()
    return P, T, polys


reset()
R0, TRI, POLY = coords()
EDGES = [tuple(e.vertices) for e in body.data.edges]
_K = {}
CAN = [_K.setdefault((round(p.x, 5), round(p.y, 5), round(p.z, 5)), len(_K)) for p in R0]   # glTF splits verts
PSET = [set(CAN[i] for i in p) for p in POLY]
# dominant bone per vertex
gname = {g.index: g.name for g in body.vertex_groups}
DOM = []
for v in body.data.vertices:
    best = max(v.groups, key=lambda g: g.weight, default=None)
    DOM.append(gname.get(best.group) if best else None)


def nrm(P, t):
    a, b, c = P[t[0]], P[t[1]], P[t[2]]
    return (b - a).cross(c - a)


def overlap_pairs(P):
    tree = BVHTree.FromPolygons(P, POLY, all_triangles=False)
    out = set()
    for i, j in tree.overlap(tree):
        if i >= j:
            continue
        if PSET[i] & PSET[j]:
            continue
        out.add((i, j))
    return out


OV0 = overlap_pairs(R0)


_GRID = None
def inside_frac(P, c, r, n=14):
    # occupied fraction of the ball (radius 1.3 r) around the pivot: ray parity against the closed body
    tree = BVHTree.FromPolygons(P, POLY, all_triangles=False)
    R = 1.3 * r
    tot = ins = 0
    d = Vector((0.5773, 0.5774, 0.5773))
    for i in range(n):
        for j in range(n):
            for k in range(n):
                q = Vector(((i + .5) / n * 2 - 1, (j + .5) / n * 2 - 1, (k + .5) / n * 2 - 1))
                if q.length > 1:
                    continue
                p = c + q * R
                tot += 1
                hits, o = 0, p
                for _ in range(64):
                    h = tree.ray_cast(o, d)
                    if h[0] is None:
                        break
                    hits += 1; o = h[0] + d * 1e-5
                ins += hits & 1
    return ins / max(tot, 1)


def head_world(name):
    return AW @ PB[name].head


def bone_rot(name):
    pb = PB[name]
    M = AW @ pb.matrix @ pb.bone.matrix_local.inverted() @ AW.inverted()
    return M.to_3x3().normalized()


def measure(jt, pivot_rest, pivot_pose, P):
    r = jt['r']
    reg = REG[jt['bone']]
    vs = {i for t in reg for i in t}
    v0, v1 = inside_frac(R0, pivot_rest, r), inside_frac(P, pivot_pose, r)
    vk = v1 / v0 if v0 > 1e-9 else 1.0
    st = 0.0
    for a, b in EDGES:
        if a in vs and b in vs:
            l0 = (R0[a] - R0[b]).length
            if l0 > 1e-7:
                st = max(st, (P[a] - P[b]).length / l0)
    rots = {}
    inv = 0
    for t in reg:
        n0, n1 = nrm(R0, t), nrm(P, t)
        if n0.length < 1e-10 or n1.length < 1e-10:
            continue
        b = DOM[t[0]]
        if b not in rots:
            rots[b] = bone_rot(b) if b in PB else Matrix.Identity(3)
        if (rots[b] @ n0).dot(n1) < 0:
            inv += 1
    ov = overlap_pairs(P) - OV0
    return dict(vol=round(vk, 3), stretch=round(st, 3), inverted=inv, overlap_new=len(ov), region_tris=len(reg))


def tip_move(name, axis, deg):
    reset()
    t0 = AW @ PB[name].tail
    e = [0, 0, 0]; e['XYZ'.index(axis)] = math.radians(deg)
    PB[name].rotation_euler = e
    bpy.context.view_layer.update()
    d = AW @ PB[name].tail - t0
    reset()
    return d


def flex_axis(jt):
    fd = Vector(jt['flex_dir'])
    best = None
    for ax in 'XZ':
        for s in (1, -1):
            d = tip_move(jt['bone'], ax, s * 30)
            sc = d.dot(fd)
            if best is None or sc > best[0]:
                best = (sc, ax, s)
    return best[1], best[2]


rows = []
AX = {}
REG = {}
for jt in CFG['joints']:
    nm = jt['bone']
    if nm not in PB:
        print('ROM missing bone', nm); continue
    ax, s = flex_axis(jt)
    side_ax = 'Z' if ax == 'X' else 'X'
    AX[nm] = (ax, s, side_ax)
    poses = [('flex', ax, s * jt['flex']), ('ext', ax, -s * jt['ext'])]
    if jt['type'] != 'hinge':
        poses += [('side+', side_ax, jt.get('side', 0)), ('side-', side_ax, -jt.get('side', 0))]
        if jt.get('twist'):
            poses += [('twist+', 'Y', jt['twist']), ('twist-', 'Y', -jt['twist'])]
    reset()
    piv0 = head_world(nm)
    axv = (AW @ PB[nm].tail - piv0).normalized()
    def _in(i):     # slab +-r along the bone axis around the joint, radial < 3r
        d = R0[i] - piv0; h = d.dot(axv)
        return abs(h) < jt['r'] and (d - axv * h).length < 3 * jt['r']
    REG[nm] = [t for t in TRI if all(_in(i) for i in t)]
    for pname, a, deg in poses:
        if deg == 0:
            continue
        reset()
        e = [0, 0, 0]; e['XYZ'.index(a)] = math.radians(deg)
        PB[nm].rotation_euler = e
        bpy.context.view_layer.update()
        P, _t, _p = coords()
        m = measure(jt, piv0, head_world(nm), P)
        ok = (m['vol'] >= G['vol_min'] and m['stretch'] <= G['stretch_max'] and m['inverted'] <= G['inverted_max']
              and m['overlap_new'] <= G['overlap_new_max'])
        m.update(bone=nm, type=jt['type'], pose=pname, deg=deg, ok=ok)
        rows.append(m)
        print('ROM', json.dumps(m))
reset()

summ = dict(poses=len(rows), pass_=sum(r['ok'] for r in rows),
            min_vol=min(r['vol'] for r in rows), max_stretch=max(r['stretch'] for r in rows),
            inverted_total=sum(r['inverted'] for r in rows), overlap_new_total=sum(r['overlap_new'] for r in rows),
            fail_vol=sum(r['vol'] < G['vol_min'] for r in rows), fail_stretch=sum(r['stretch'] > G['stretch_max'] for r in rows),
            fail_inv=sum(r['inverted'] > G['inverted_max'] for r in rows),
            fail_ov=sum(r['overlap_new'] > G['overlap_new_max'] for r in rows),
            body=body.name, verts=len(R0), tris=len(TRI), rest_overlap=len(OV0))
json.dump(dict(summary=summ, rows=rows, axes=AX), open(os.path.join(OUT, 'rom.json'), 'w'), indent=1)
print('ROMSUMMARY', json.dumps(summ))

# ---- combined extreme poses, clay renders
EXT = {
 'arm_reach': {'upperarm.L': ('flex', 1.0), 'forearm.L': ('flex', 1.0), 'hand.L': ('flex', 1.0),
               'upperarm.R': ('ext', 1.0), 'forearm.R': ('flex', 0.6)},
 'arm_raise': {'upperarm.L': ('side+', 1.0), 'upperarm.R': ('side+', 1.0), 'forearm.L': ('flex', 0.5)},
 'leg_kick':  {'thigh.L': ('flex', 1.0), 'shin.L': ('flex', 1.0), 'foot.L': ('flex', 1.0), 'thigh.R': ('ext', 1.0)},
 'crouch':    {'spine': ('flex', 1.0), 'chest': ('flex', 1.0), 'neck': ('ext', 1.0), 'thigh.L': ('flex', 0.8),
               'thigh.R': ('flex', 0.8), 'shin.L': ('flex', 1.0), 'shin.R': ('flex', 1.0), 'tail0': ('flex', 1.0)},
}
JD = {j['bone']: j for j in CFG['joints']}


def set_pose(spec):
    reset()
    for nm, (p, f) in spec.items():
        base = nm.replace('.R', '.L')
        if base not in AX or nm not in PB:
            continue
        ax, s, sax = AX[base]
        jt = JD[base]
        mir = -1 if nm.endswith('.R') else 1
        if p == 'flex':
            a, d = ax, s * jt['flex']
        elif p == 'ext':
            a, d = ax, -s * jt['ext']
        else:
            a, d = sax, jt.get('side', 0) * (1 if p == 'side+' else -1)
        if nm.endswith('.R') and a in 'YZ':
            d = -d      # mirror the non-flex axes for the right side
        e = [0, 0, 0]; e['XYZ'.index(a)] = math.radians(d * f)
        PB[nm].rotation_euler = e
    bpy.context.view_layer.update()


sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.75, 0.73, 0.70)
sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
ctr = Vector((0, 0, 1.05))
for tag, spec in EXT.items():
    set_pose(spec)
    for vn, az, el in (('hero', 35, 12), ('side', 90, 0)):
        a = math.radians(az); e_ = math.radians(el)
        dvec = Vector((math.sin(a) * math.cos(e_), -math.cos(a) * math.cos(e_), math.sin(e_)))
        cam.location = ctr + dvec * 4.0
        cam.rotation_euler = (-dvec).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f'pose_{tag}_{vn}.png')
        bpy.ops.render.render(write_still=True)
reset()
print('ROM done')
