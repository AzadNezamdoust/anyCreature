# ROM sweep probe (promoted from abc/t8/joint_graph/rom_sweep.py, 2026-10-22). Runs in headless Blender:
#   blender -b --factory-startup -P rom_probe.py -- <rigged.glb> <outdir> [--joints joints.json|auto] [--tag t]
#           [--body name] [--reweight cfg.json|default] [--no-render] [--save-glb out.glb]
# Drives each joint to its limits (flex, ext, side+-, twist+-) one at a time and measures on the skinned body:
# local volume kept in a 1.3 r ball round the pivot (ray parity, >= vol_min), max edge stretch in the joint slab
# (<= stretch_max), triangles flipped against their dominant bone's rigid rotation (<= inverted_max) and NEW BVH
# self-overlap pairs vs rest (per pose: <= max(overlap_new_max, overlap_new_frac * region tris)).
# --joints auto derives the joint list from the rig (roles: root / mid / distal limb, spine, neck, tail; .L + centre
# bones only, the .R side is the mirror). --reweight applies kit/weights.refine() to the imported body first (the
# experiment path; the build path calls it from bmkit.skin). Renders 4 combined extreme poses (clay, hero + side).
import bpy, sys, json, os, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = argv[0], argv[1]
opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
JS = opt('--joints', 'auto')
TAG = opt('--tag', 'rom')
BODY = opt('--body')
RW = opt('--reweight')
SAVE = opt('--save-glb')
RENDER = '--no-render' not in argv
os.makedirs(OUT, exist_ok=True)
GATES = dict(vol_min=0.70, stretch_max=2.0, inverted_max=0, overlap_new_max=0, overlap_new_frac=0.0)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
skinned = [o for o in meshes if any(m.type == 'ARMATURE' for m in o.modifiers)]
body = next(o for o in meshes if o.name.startswith(BODY)) if BODY else max(skinned or meshes, key=lambda o: len(o.data.vertices))
for o in [arm] + meshes:
    if o.animation_data:
        o.animation_data.action = None
PB = arm.pose.bones
AW = arm.matrix_world


def reset():
    for pb in PB:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


import weights
reset()
RWSTATS = None
if RW:
    import weights
    cfg = {} if RW == 'default' else json.load(open(RW))
    cfg.setdefault('helper_constraint', False)
    RWSTATS = weights.refine(body, arm, **cfg)
    bpy.context.view_layer.update()


def coords(ob=body):
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg)
    m = e.to_mesh()
    W = ob.matrix_world
    P = [W @ v.co for v in m.vertices]
    m.calc_loop_triangles()
    T = [tuple(t.vertices) for t in m.loop_triangles]
    polys = [tuple(p.vertices) for p in m.polygons]
    e.to_mesh_clear()
    return P, T, polys


HELP = any(weights.helper_source(b.name) for b in arm.data.bones)
R0, TRI, POLY = coords()
EDGES = [tuple(e.vertices) for e in body.data.edges]
_K = {}
CAN = [_K.setdefault((round(p.x, 5), round(p.y, 5), round(p.z, 5)), len(_K)) for p in R0]   # glTF splits verts
PSET = [set(CAN[i] for i in p) for p in POLY]
gname = {g.index: g.name for g in body.vertex_groups}
DOM = []
for v in body.data.vertices:
    best = max(v.groups, key=lambda g: g.weight, default=None)
    DOM.append(gname.get(best.group) if best else None)
lo = Vector([min(p[i] for p in R0) for i in range(3)])
hi = Vector([max(p[i] for p in R0) for i in range(3)])
SIZE = max(hi - lo)


def nrm(P, t):
    a, b, c = P[t[0]], P[t[1]], P[t[2]]
    return (b - a).cross(c - a)


def overlap_pairs(P):
    tree = BVHTree.FromPolygons(P, POLY, all_triangles=False)
    return {(i, j) for i, j in tree.overlap(tree) if i < j and not (PSET[i] & PSET[j])}


OV0 = overlap_pairs(R0)


def inside_frac(P, c, r, n=14):
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
                o = c + q * R
                tot += 1
                hits = 0
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


def deform_parent(b):
    p = b.parent
    while p is not None and not p.use_deform:
        p = p.parent
    return p


# ---------------------------------------------------------------- joints
SKIP = ('ear', 'eye', 'jaw', 'tongue', 'lid', 'horn', 'antler', 'tuft', 'fang')
ROM = dict(root=dict(type='twist', flex=60, ext=30, side=30, twist=30),
           mid=dict(type='hinge', flex=90, ext=5),
           distal=dict(type='hinge', flex=40, ext=30),
           spine=dict(type='ball', flex=20, ext=15, side=15, twist=15),
           neck=dict(type='twist', flex=30, ext=20, side=20, twist=30),
           tail=dict(type='ball', flex=30, ext=30, side=30, twist=0))


def joint_r(name):
    b = arm.data.bones[name]
    h = AW @ b.head_local
    ax = ((AW @ b.tail_local) - h).normalized()
    L = b.length
    par = deform_parent(b)
    own = {name, par.name if par else None}
    rs = []
    for i, p in enumerate(R0):
        if DOM[i] not in own:
            continue
        d = p - h
        hh = d.dot(ax)
        if abs(hh) < 0.25 * L:
            rd = (d - ax * hh).length
            if rd < 2 * L:
                rs.append(rd)
    rs.sort()
    r = rs[len(rs) // 2] if len(rs) >= 6 else 0.3 * L
    return max(min(r, 1.2 * L), 0.05 * L)


def auto_joints():
    import weights
    out = []
    counts = {}
    for d in DOM:
        counts[d] = counts.get(d, 0) + 1
    for b in arm.data.bones:
        n = b.name
        if not b.use_deform or n.endswith('.R') or deform_parent(b) is None or weights.helper_source(n):
            continue
        if any(n.lower().startswith(s) for s in SKIP) or counts.get(n, 0) < 20:
            continue
        rl = weights.role(b)
        if rl == 'spine' and 'neck' in n.lower():
            rl = 'neck'
        jt = dict(bone=n, role=rl, **ROM[rl])
        h = AW @ b.head_local
        c = ((AW @ b.tail_local) - h).normalized()
        par = deform_parent(b)
        p = ((AW @ par.tail_local) - (AW @ par.head_local)).normalized()
        if rl in ('root', 'spine', 'neck'):
            fd = Vector((0, -1, 0))
        elif rl == 'tail':
            fd = Vector((0, 0, 1))
        else:
            perp = p - c * p.dot(c)
            if perp.length > math.sin(math.radians(8)):
                fd = -perp.normalized()          # flexion deepens the rest bend
            else:
                fd = Vector((0, 1, 0)) if any(s in n.lower() for s in ('shin', 'tibia', 'calf', 'knee')) else Vector((0, -1, 0))
        jt['flex_dir'] = list(fd)
        jt['r'] = round(joint_r(n), 4)
        out.append(jt)
    return out


if JS == 'auto':
    CFG = dict(joints=auto_joints(), gates=dict(GATES, overlap_new_frac=0.05))
else:
    CFG = json.load(open(JS))
    for jt in CFG['joints']:
        jt.setdefault('r', round(joint_r(jt['bone']), 4) if jt['bone'] in PB else 0.1)
G = dict(GATES, **CFG.get('gates', {}))


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
    rots, inv = {}, 0
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
            sc = tip_move(jt['bone'], ax, s * 30).dot(fd)
            if best is None or sc > best[0]:
                best = (sc, ax, s)
    return best[1], best[2]


rows, AX, REG = [], {}, {}
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

    def _in(i, piv0=piv0, axv=axv, r=jt['r']):
        d = R0[i] - piv0; h = d.dot(axv)
        return abs(h) < r and (d - axv * h).length < 3 * r
    REG[nm] = [t for t in TRI if all(_in(i) for i in t)]
    for pname, a, deg in poses:
        if deg == 0:
            continue
        reset()
        e = [0, 0, 0]; e['XYZ'.index(a)] = math.radians(deg)
        PB[nm].rotation_euler = e
        HELP and weights.sync_helpers(arm)
        bpy.context.view_layer.update()
        P, _t, _p = coords()
        m = measure(jt, piv0, head_world(nm), P)
        ovcap = max(G['overlap_new_max'], int(G.get('overlap_new_frac', 0) * m['region_tris']))
        fails = [k for k, bad in (('vol', m['vol'] < G['vol_min']), ('stretch', m['stretch'] > G['stretch_max']),
                                  ('inverted', m['inverted'] > G['inverted_max']), ('overlap', m['overlap_new'] > ovcap)) if bad]
        m.update(bone=nm, type=jt['type'], pose=pname, deg=deg, ok=not fails, fail=fails, overlap_cap=ovcap)
        rows.append(m)
        print('ROM', json.dumps(m))
reset()

summ = dict(poses=len(rows), pass_=sum(r['ok'] for r in rows),
            min_vol=min((r['vol'] for r in rows), default=1.0), max_stretch=max((r['stretch'] for r in rows), default=1.0),
            inverted_total=sum(r['inverted'] for r in rows), overlap_new_total=sum(r['overlap_new'] for r in rows),
            fail_vol=sum('vol' in r['fail'] for r in rows), fail_stretch=sum('stretch' in r['fail'] for r in rows),
            fail_inv=sum('inverted' in r['fail'] for r in rows), fail_ov=sum('overlap' in r['fail'] for r in rows),
            body=body.name, verts=len(R0), tris=len(TRI), rest_overlap=len(OV0), joints=JS if JS != 'auto' else 'auto',
            reweight=RW)
summ['ok'] = summ['pass_'] == summ['poses']
json.dump(dict(summary=summ, rows=rows, axes=AX, joints=CFG['joints'], gates=G, reweight_stats=RWSTATS),
          open(os.path.join(OUT, f'{TAG}.json'), 'w'), indent=1)
print('BMK ROM %s: %d/%d poses pass, min vol %.3f, max stretch %.3f, inverted %d (%d poses), new overlap %d (%d poses)'
      % ('PASS' if summ['ok'] else 'FAIL', summ['pass_'], summ['poses'], summ['min_vol'], summ['max_stretch'],
         summ['inverted_total'], summ['fail_inv'], summ['overlap_new_total'], summ['fail_ov']))
for r in rows:
    if not r['ok']:
        print('BMK ROM fail %s %s %+d: vol %.3f stretch %.3f inv %d overlap %d/%d' % (
            r['bone'], r['pose'], r['deg'], r['vol'], r['stretch'], r['inverted'], r['overlap_new'], r['overlap_cap']))

if SAVE:
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=SAVE, export_format='GLB', use_selection=False, export_animations=True)

# ---------------------------------------------------------------- combined extreme poses, clay renders
JD = {j['bone']: j for j in CFG['joints']}
WW = {
 'arm_reach': {'upperarm.L': ('flex', 1.0), 'forearm.L': ('flex', 1.0), 'hand.L': ('flex', 1.0),
               'upperarm.R': ('ext', 1.0), 'forearm.R': ('flex', 0.6)},
 'arm_raise': {'upperarm.L': ('side+', 1.0), 'upperarm.R': ('side+', 1.0), 'forearm.L': ('flex', 0.5)},
 'leg_kick':  {'thigh.L': ('flex', 1.0), 'shin.L': ('flex', 1.0), 'foot.L': ('flex', 1.0), 'thigh.R': ('ext', 1.0)},
 'crouch':    {'spine': ('flex', 1.0), 'chest': ('flex', 1.0), 'neck': ('ext', 1.0), 'thigh.L': ('flex', 0.8),
               'thigh.R': ('flex', 0.8), 'shin.L': ('flex', 1.0), 'shin.R': ('flex', 1.0), 'tail0': ('flex', 1.0)},
}


def auto_ext():
    L = [j['bone'] for j in CFG['joints'] if j['bone'].endswith('.L')]
    C = [j['bone'] for j in CFG['joints'] if not j['bone'].endswith('.L')]
    both = lambda n: [n, n[:-2] + '.R']
    flexall = {}
    for n in L:
        for m in both(n):
            flexall[m] = ('flex', 1.0)
    raise_ = {}
    for n in L:
        if JD[n]['role'] == 'root':
            for m in both(n):
                raise_[m] = ('side+', 1.0)
        elif JD[n]['role'] == 'mid':
            raise_[n] = ('flex', 0.5)
    ext = {m: ('ext', 1.0) for n in L for m in both(n)}
    trunk = {n: ('flex', 1.0) for n in C}
    trunk.update({m: ('flex', 0.5) for n in L if JD[n]['role'] == 'root' for m in both(n)})
    return {'limbs_flex': flexall, 'limbs_raise': raise_, 'limbs_ext': ext, 'trunk_flex': trunk}


EXT = WW if all(n in JD for n in ('upperarm.L', 'forearm.L', 'thigh.L', 'shin.L')) else auto_ext()


def set_pose(spec):
    reset()
    for nm, (p, f) in spec.items():
        base = nm.replace('.R', '.L')
        if base not in AX or nm not in PB:
            continue
        ax, s, sax = AX[base]
        jt = JD[base]
        if p == 'flex':
            a, d = ax, s * jt['flex']
        elif p == 'ext':
            a, d = ax, -s * jt['ext']
        else:
            a, d = sax, jt.get('side', 0) * (1 if p == 'side+' else -1)
        if nm.endswith('.R') and a in 'YZ':
            d = -d
        e = [0, 0, 0]; e['XYZ'.index(a)] = math.radians(d * f)
        PB[nm].rotation_euler = e
    HELP and weights.sync_helpers(arm)
    bpy.context.view_layer.update()


if RENDER:
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (0.75, 0.73, 0.70)
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.world = bpy.data.worlds.new('w')
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    ctr = (lo + hi) * 0.5
    dist = 1.85 * SIZE
    for tag, spec in EXT.items():
        set_pose(spec)
        for vn, az, el in (('hero', 35, 12), ('side', 90, 0)):
            a = math.radians(az); e_ = math.radians(el)
            dvec = Vector((math.sin(a) * math.cos(e_), -math.cos(a) * math.cos(e_), math.sin(e_)))
            cam.location = ctr + dvec * dist
            cam.rotation_euler = (-dvec).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(OUT, f'{TAG}_pose_{tag}_{vn}.png')
            bpy.ops.render.render(write_still=True)
    # zoomed joint crops at the flex limit (the elbow / knee / groin views a reviewer reads)
    sc.render.resolution_x = sc.render.resolution_y = 384
    for jt in CFG['joints']:
        nm = jt['bone']
        if nm not in AX:
            continue
        set_pose({nm: ('flex', 1.0)})
        piv = head_world(nm)
        out_ = Vector((1 if piv.x >= 0 else -1, 0, 0)) if abs(piv.x) > 0.02 else Vector((1, 0, 0))
        for vn, dv in (('out', out_ + Vector((0, -0.35, 0.25))), ('front', Vector((0.35 * out_.x, -1, 0.2)))):
            dv = dv.normalized()
            cam.location = piv + dv * max(14.0 * jt['r'], 0.22 * SIZE)
            cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(OUT, f'{TAG}_joint_{nm}_flex_{vn}.png')
            bpy.ops.render.render(write_still=True)
    reset()
print('ROM done')
