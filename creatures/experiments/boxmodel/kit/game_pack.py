"""game_pack.py - game pack emitter for a stage-4 box-model GLB (read-only on the source).

    blender -b --factory-startup -P game_pack.py -- --glb in.glb --out dir --name hippo [--baseline]

Pack mode writes into <out>:
  LODs   : <name>_LOD0..3 (Decimate collapse 100/50/25/15 %, small pieces floored at 24 tris),
           silhouette IoU vs LOD0 from 8 azimuth views (gate >= 0.90).
  hurtbox: HB_<bone> capsule meshes (bone-parented) + glTF extras {hurtbox:1, radius, height}.
  collide: UCX_<name>_00 convex hull of LOD3 + CAP_root capsule proxy.
  sockets: socket_mouth, socket_hand_L/R (or claw/paw), socket_back empties, bone-parented.
  export : unity/<name>.glb + unity/<name>.fbx (Y-up, m);  unreal/<name>.fbx (Z-up, cm).
  verify : re-import every export: bone count, bind pose (heads, scale-normalised), clip lengths,
           socket names, LOD names, hurtbox count.
  clipqa : foot slide, ground penetration, loop continuity (same numbers for baseline: clips untouched).
  renders: readability renders of each LOD at 192 px and at its game distance size.
Baseline mode: same verify (on the GLB as-is), clip QA and renders, no emission.
Writes <out>/pack_report.json.
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d
GLB, OUT, NAME = os.path.abspath(arg('--glb')), os.path.abspath(arg('--out')), arg('--name')
BASE = '--baseline' in argv
os.makedirs(OUT, exist_ok=True)
RATIOS = [1.0, 0.5, 0.25, 0.15]
GAME_PX = [192, 128, 80, 48]


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = os.path.splitext(path)[1].lower()
    if ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    shapes = {pb.custom_shape for pb in arm.pose.bones if pb.custom_shape}
    for o in list(bpy.context.scene.objects):
        if o in shapes or (o.type == 'MESH' and o.parent is None and not o.name.startswith(('UCX_', 'CAP_'))):
            bpy.data.objects.remove(o, do_unlink=True)
    return arm


def meshes_of(arm, prefix=None):
    out = [o for o in bpy.context.scene.objects if o.type == 'MESH' and
           any(m.type == 'ARMATURE' for m in o.modifiers)]
    if prefix is not None:
        out = [o for o in out if o.name.startswith(prefix)]
    return out


def tris(objs):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)


def world_tris(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles()
        co = np.array([o.matrix_world @ v.co for v in me.vertices])
        idx = np.array([t.vertices[:] for t in me.loop_triangles])
        if len(idx):
            out.append(co[idx])
        oe.to_mesh_clear()
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def raster(T, az, lo, span, res=256):
    """orthographic silhouette from azimuth az (deg, around Z), shared frame."""
    a = math.radians(az)
    u = np.array([math.cos(a), math.sin(a), 0.0]); w = np.array([0, 0, 1.0])
    P = np.stack([T @ u, T @ w], -1)  # (n,3,2)
    P = (P - lo) / span * (res - 1)
    img = np.zeros((res, res), bool)
    for t in P:
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, res - 1), min(y1, res - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax, ay), (bx, by), (cx, cy) = t
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12:
            continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
        l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / d
        m = (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6)
        img[y0:y1 + 1, x0:x1 + 1] |= m
    return img


def frame_of(T):
    pts = T.reshape(-1, 3)
    r = np.linalg.norm(pts[:, :2] - pts[:, :2].mean(0), axis=1).max()
    lo = np.array([-r + 0 * 1, pts[:, 2].min()]); span = max(2 * r, np.ptp(pts[:, 2])) * 1.02
    c = pts[:, :2].mean(0)
    return c, lo, span


def silhouettes(objs, frame):
    T = world_tris(objs)
    c, lo, span = frame
    T = T - np.array([c[0], c[1], 0])
    return [raster(T, az, lo, span) for az in range(0, 360, 45)]


def rest(arm, on=True):
    arm.data.pose_position = 'REST' if on else 'POSE'
    bpy.context.view_layer.update()


def bone_heads(arm):
    return {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}


def height(objs):
    T = world_tris(objs).reshape(-1, 3)
    return float(np.ptp(T[:, 2])), float(T[:, 2].min())


def actions():
    return {a.name: [float(a.frame_range[0]), float(a.frame_range[1])] for a in bpy.data.actions}


def clean_act(n):
    return n.split('|')[-1]


# ---------------- clip QA ----------------
def clip_qa(arm, objs):
    rest(arm, True)
    H, ground = height(objs)
    feet = [b for b in arm.data.bones if any(k in b.name.lower() for k in ('foot', 'toe', 'paw', 'hoof', 'hand', 'flipper', 'claw'))
            and not b.children]
    feet = [b for b in feet if (arm.matrix_world @ b.tail_local).z < ground + 0.25 * H] or feet
    rest(arm, False)
    arm.animation_data_create()
    res = {}
    for a in bpy.data.actions:
        arm.animation_data.action = a
        if hasattr(arm.animation_data, 'action_slot') and a.slots:
            arm.animation_data.action_slot = a.slots[0]
        f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
        pen = 0.0; trk = {b.name: [] for b in feet}; poses = []
        for f in range(f0, f1 + 1):
            bpy.context.scene.frame_set(f)
            T = world_tris(objs).reshape(-1, 3)
            pen = min(pen, float(T[:, 2].min() - ground))
            for b in feet:
                pb = arm.pose.bones[b.name]
                trk[b.name].append(np.array(arm.matrix_world @ pb.tail))
            poses.append(np.array([np.array(arm.matrix_world @ pb.head) for pb in arm.pose.bones] +
                                  [np.array(arm.matrix_world @ pb.tail) for pb in arm.pose.bones]))
        slides = []; contacts = 0
        for n, tr in trk.items():
            tr = np.array(tr); zmin = tr[:, 2].min()
            planted = tr[:, 2] < zmin + 0.02 * H
            v = np.linalg.norm(np.diff(tr[:, :2], axis=0), axis=1)
            pl = planted[1:] & planted[:-1]
            if pl.sum() >= 2:
                contacts += int(pl.sum())
                slides.append(float(np.std(v[pl]) / H * 100))  # treadmill-consistency, % height/frame
                slides.append(float(np.median(v[pl]) / H * 100) * 0)  # placeholder keeps list numeric
        sl = [s for s in slides[::2]]
        loop = float(np.abs(poses[0] - poses[-1]).max() / H * 100)
        res[a.name] = dict(frames=f1 - f0 + 1, penetration_pctH=round(-pen / H * 100, 2),
                           foot_slide_std_pctH=round(max(sl) if sl else 0.0, 3),
                           planted_frames=contacts, loop_gap_pctH=round(loop, 2))
    arm.animation_data.action = None
    rest(arm, True)
    return dict(H=H, feet=[b.name for b in feet], clips=res)


# ---------------- renders ----------------
def render_set(objs_by_lod, arm, tag):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new('w')
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.62, 0.66, 0.62)
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree.nodes.get('Principled BSDF'):
            m.diffuse_color = tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
    allm = [o for v in objs_by_lod.values() for o in v]
    T = world_tris(objs_by_lod[0]).reshape(-1, 3)
    c = (T.min(0) + T.max(0)) / 2; R = np.linalg.norm(T.max(0) - T.min(0)) / 2
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
    cam.data.lens = 50; sc.camera = cam
    az, el = math.radians(-35), math.radians(14)
    d = R / math.tan(math.radians(17)) * 1.05
    cam.location = Vector(c) + Vector((math.sin(az) * math.cos(el) * -d, -math.cos(az) * math.cos(el) * d, math.sin(el) * d))
    cam.rotation_euler = (Vector(c) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    out = {}
    for lod, objs in objs_by_lod.items():
        for o in allm:
            o.hide_render = o not in objs
        for px in sorted({192, GAME_PX[lod]}):
            sc.render.resolution_x = sc.render.resolution_y = px
            p = os.path.join(OUT, 'renders', f'{tag}_lod{lod}_{px}.png')
            sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            out[f'lod{lod}_{px}'] = p
    for o in allm:
        o.hide_render = False
    bpy.data.objects.remove(cam)
    return out


# ---------------- verify ----------------
def verify(path, ref, scale):
    arm = load(path)
    rest(arm, True)
    names = {o.name for o in bpy.context.scene.objects}
    heads = bone_heads(arm)
    common = [k for k in ref['heads'] if k in heads]
    A = np.array([ref['heads'][k] for k in common]); B = np.array([heads[k] for k in common])
    A = A - A.mean(0); B = B - B.mean(0)
    s = np.linalg.norm(A) / max(np.linalg.norm(B), 1e-9)
    bind_err = float(np.abs(A - B * s).max() / ref['H'] * 100) if len(common) else 99.0
    acts = {clean_act(k): round(v[1] - v[0]) for k, v in actions().items()}
    want_acts = {k: round(v[1] - v[0]) for k, v in ref['acts'].items()}
    checks = dict(
        bones=(len(arm.data.bones) == ref['bones'], f"{len(arm.data.bones)}/{ref['bones']}"),
        bind_pose=(bind_err < 0.5, f"max head err {bind_err:.3f}% H, scale {s:.4f} (expect {1/scale:.4f})"),
        unit_scale=(abs(s * scale - 1) < 0.02, f"{s*scale:.4f}"),
        clips=(all(acts.get(k) == v for k, v in want_acts.items()), str(acts)),
        sockets=(all(any(n.startswith(k) for n in names) for k in ref['sockets']) and len(ref['sockets']) > 0,
                 str(sorted(n for n in names if n.startswith('socket_')))),
        lods=(all(any(n.startswith(f'{NAME}_LOD{i}') for n in names) for i in range(4)),
              str(sorted({n.split('.')[0].split('_')[-2] for n in names if '_LOD' in n}))),
        hurtboxes=(sum(n.startswith('HB_') for n in names) == ref['hurtboxes'] and ref['hurtboxes'] > 0,
                   f"{sum(n.startswith('HB_') for n in names)}/{ref['hurtboxes']}"),
        collision=(any(n.startswith('UCX_') for n in names) and any(n.startswith('CAP_') for n in names),
                   str(sorted(n for n in names if n.startswith(('UCX_', 'CAP_'))))),
    )
    return dict(file=os.path.basename(path), checks={k: dict(ok=bool(v[0]), detail=v[1]) for k, v in checks.items()},
                pass_core=all(checks[k][0] for k in ('bones', 'bind_pose', 'unit_scale', 'clips')),
                pass_all=all(v[0] for v in checks.values()))


def ref_of(arm, objs, sockets, hb):
    rest(arm, True)
    H, _ = height(objs)
    return dict(heads={k: v.tolist() for k, v in bone_heads(arm).items()}, bones=len(arm.data.bones),
                acts=actions(), H=H, sockets=sockets, hurtboxes=hb)


# ---------------- emission ----------------
def make_lods(arm, base):
    lods = {0: base}
    for o in base:
        o.name = f'{NAME}_LOD0_{o.name}'
    for i, r in enumerate(RATIOS[1:], 1):
        lods[i] = []
        for o in base:
            c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
            c.name = o.name.replace('_LOD0_', f'_LOD{i}_')
            # glTF import splits flat-shaded verts per face: weld first, or Collapse shrinks every island
            bm = bmesh.new(); bm.from_mesh(c.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bm.to_mesh(c.data); bm.free()
            for p in c.data.polygons:
                p.use_smooth = False
            n = tris([o]); rr = max(r, min(1.0, 24 / max(n, 1)))
            rr = min(1.0, rr * n / max(tris([c]), 1))  # ratio vs the original tri count
            arm_mods = [m for m in c.modifiers if m.type == 'ARMATURE']
            for m in arm_mods:
                m.show_viewport = False
            dm = c.modifiers.new('dec', 'DECIMATE'); dm.ratio = rr; dm.use_collapse_triangulate = True; dm.use_symmetry = True; dm.symmetry_axis = 'X'
            bpy.context.view_layer.objects.active = c
            with bpy.context.temp_override(object=c, active_object=c):
                bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
                bpy.ops.object.modifier_apply(modifier='dec')
            for m in arm_mods:
                m.show_viewport = True
            lods[i].append(c)
    return lods


def capsule_mesh(name, r, h, seg=8, rings=3):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings * 2, radius=r)
    for v in bm.verts:
        v.co.z += (h / 2 - r) * (1 if v.co.z > 1e-6 else -1 if v.co.z < -1e-6 else 0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me


def bone_parent(o, arm, bone, mw):
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = mw


def hurtboxes(arm, body):
    rest(arm, True)
    mw = body.matrix_world
    co = np.array([mw @ v.co for v in body.data.vertices])
    gi = {g.index: g.name for g in body.vertex_groups}
    W = {}
    for v in body.data.vertices:
        for g in v.groups:
            if g.weight > 0.5:
                W.setdefault(gi[g.group], []).append(v.index)
    made = []
    for b in arm.data.bones:
        ids = W.get(b.name, [])
        if len(ids) < 8 or b.length < 1e-4:
            continue
        h0 = np.array(arm.matrix_world @ b.head_local); t0 = np.array(arm.matrix_world @ b.tail_local)
        ax = (t0 - h0); L = np.linalg.norm(ax); ax /= L
        P = co[ids] - h0; s = P @ ax
        perp = np.linalg.norm(P - np.outer(s, ax), axis=1)
        r = float(np.percentile(perp, 70)); smin, smax = np.percentile(s, [5, 95])
        hgt = float(max(smax - smin + 2 * r * 0.6, 2 * r))
        mid = h0 + ax * (smin + smax) / 2
        me = capsule_mesh(f'HB_{b.name}', r, hgt)
        o = bpy.data.objects.new(f'HB_{b.name}', me); bpy.context.scene.collection.objects.link(o)
        o['hurtbox'] = 1; o['radius'] = round(r, 4); o['height'] = round(hgt, 4); o['bone'] = b.name
        o.display_type = 'WIRE'
        rot = Vector(ax.tolist()).to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bone_parent(o, arm, b.name, Matrix.Translation(Vector(mid.tolist())) @ rot)
        made.append(o)
    return made


def collision(arm, lod3, lod0):
    T = world_tris(lod3).reshape(-1, 3)
    bm = bmesh.new()
    for p in T:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    me = bpy.data.meshes.new(f'UCX_{NAME}_00'); bm.to_mesh(me); bm.free()
    u = bpy.data.objects.new(f'UCX_{NAME}_00', me); bpy.context.scene.collection.objects.link(u)
    u.display_type = 'WIRE'; u['collision'] = 'convex'
    T0 = world_tris(lod0).reshape(-1, 3)
    lo, hi = T0.min(0), T0.max(0)
    r = float(min(hi[0] - lo[0], hi[1] - lo[1]) / 2 * 0.9); h = float(hi[2] - lo[2])
    c = bpy.data.objects.new(f'CAP_{NAME}_root', capsule_mesh('CAP', r, max(h, 2 * r)))
    bpy.context.scene.collection.objects.link(c)
    c.location = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] + max(h, 2 * r) / 2)
    c['collision'] = 'capsule'; c['radius'] = round(r, 4); c['height'] = round(max(h, 2 * r), 4)
    c.display_type = 'WIRE'
    return u, c


def sockets(arm, body):
    rest(arm, True)
    co = np.array([body.matrix_world @ v.co for v in body.data.vertices])
    bn = {b.name.lower(): b for b in arm.data.bones}
    made = []
    def add(name, bone, pos):
        e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
        e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.05
        bone_parent(e, arm, bone.name, Matrix.Translation(Vector(pos)))
        made.append(name)
    head = next((bn[k] for k in ('head', 'jaw', 'skull') if k in bn), None)
    if head:
        h0 = np.array(arm.matrix_world @ head.head_local); t0 = np.array(arm.matrix_world @ head.tail_local)
        # mouth: the body vertex farthest along the head's forward (body -Y in this kit) near the head
        near = co[np.linalg.norm(co - (h0 + t0) / 2, axis=1) < 2.0 * max(head.length, 1e-3) + 0.05]
        fwd = near[near[:, 1].argmin()] if len(near) else t0
        add('socket_mouth', head, [fwd[0], fwd[1], fwd[2] - 0.15 * head.length])
    for side in ('L', 'R'):
        hb = next((b for b in arm.data.bones if b.name.lower().startswith(('hand', 'paw', 'claw', 'flipper', 'wing', 'forearm', 'upperarm'))
                   and b.name.endswith('.' + side) and not b.children), None)
        if hb is None:
            hb = next((b for b in arm.data.bones if b.name.endswith('.' + side) and
                       any(k in b.name.lower() for k in ('hand', 'forearm', 'arm', 'fin', 'wing', 'foot'))), None)
        if hb:
            add(f'socket_hand_{side}', hb, list(arm.matrix_world @ hb.tail_local))
    ch = next((bn[k] for k in ('chest', 'spine', 'spine1', 'hips') if k in bn), None)
    if ch:
        p = np.array(arm.matrix_world @ ch.head_local)
        col = co[np.linalg.norm(co[:, :2] - p[:2], axis=1) < 0.25 * max(np.ptp(co[:, 2]), 1e-3)]
        top = col[:, 2].max() if len(col) else p[2]
        add('socket_back', ch, [p[0], p[1], float(top)])
    return made


def export_all(arm):
    sel = [o for o in bpy.context.scene.objects]
    paths = {}
    os.makedirs(os.path.join(OUT, 'unity'), exist_ok=True); os.makedirs(os.path.join(OUT, 'unreal'), exist_ok=True)
    # push every action as an NLA strip so all clips export
    arm.animation_data_create(); arm.animation_data.action = None
    for a in bpy.data.actions:
        tr = arm.animation_data.nla_tracks.new(); tr.name = a.name
        tr.strips.new(a.name, int(a.frame_range[0]), a)
    p = os.path.join(OUT, 'unity', f'{NAME}.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', export_animation_mode='ACTIONS',
                              export_extras=True, export_yup=True, export_apply=False)
    paths['unity_glb'] = (p, 1.0)
    common = dict(use_selection=False, object_types={'ARMATURE', 'MESH', 'EMPTY'}, add_leaf_bones=False,
                  bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
                  bake_anim_force_startend_keying=True, use_custom_props=True, mesh_smooth_type='FACE',
                  primary_bone_axis='Y', secondary_bone_axis='X')
    p = os.path.join(OUT, 'unity', f'{NAME}.fbx')
    bpy.ops.export_scene.fbx(filepath=p, axis_forward='-Z', axis_up='Y', global_scale=1.0,
                             apply_scale_options='FBX_SCALE_UNITS', apply_unit_scale=True, **common)
    paths['unity_fbx'] = (p, 1.0)
    p = os.path.join(OUT, 'unreal', f'{NAME}.fbx')
    bpy.ops.export_scene.fbx(filepath=p, axis_forward='-Y', axis_up='Z', global_scale=100.0,
                             apply_scale_options='FBX_SCALE_NONE', apply_unit_scale=False, **common)
    paths['unreal_fbx'] = (p, 100.0)
    return paths


def main():
    arm = load(GLB)
    base = meshes_of(arm)
    rep = dict(name=NAME, mode='baseline' if BASE else 'pack', src=GLB)
    if BASE:
        rep['tris'] = [tris(base)]
        ref = ref_of(arm, base, ['socket_mouth', 'socket_hand', 'socket_back'], 1)
        rep['clipqa'] = clip_qa(arm, base)
        rep['renders'] = render_set({0: base}, arm, 'base')
        rep['roundtrip'] = {'baseline_glb': verify(GLB, ref, 1.0)}
    else:
        lods = make_lods(arm, base)
        rest(arm, True)
        fr = frame_of(world_tris(lods[0]))
        s0 = silhouettes(lods[0], fr)
        rep['lods'] = []
        for i in range(4):
            si = silhouettes(lods[i], fr)
            iou = [float((a & b).sum() / max((a | b).sum(), 1)) for a, b in zip(s0, si)]
            rep['lods'].append(dict(lod=i, tris=tris(lods[i]), tri_ratio=round(tris(lods[i]) / tris(lods[0]), 3),
                                    iou_min=round(min(iou), 4), iou_mean=round(float(np.mean(iou)), 4),
                                    gate=min(iou) >= 0.9))
        body = max(base, key=lambda o: len(o.data.vertices))
        hb = hurtboxes(arm, body)
        u, c = collision(arm, lods[3], lods[0])
        sk = sockets(arm, body)
        rep['hurtboxes'] = [dict(bone=o['bone'], r=o['radius'], h=o['height']) for o in hb]
        rep['sockets'] = sk
        rep['clipqa'] = clip_qa(arm, lods[0])
        for o in hb + [u, c]:
            o.hide_render = True
        rep['renders'] = render_set(lods, arm, 'pack')
        ref = ref_of(arm, lods[0], sk, len(hb))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}_pack.blend'))
        paths = export_all(arm)
        rep['roundtrip'] = {k: verify(p, ref, s) for k, (p, s) in paths.items()}
    with open(os.path.join(OUT, 'pack_report.json'), 'w') as f:
        json.dump(rep, f, indent=1)
    print('PACK_DONE', json.dumps({k: v.get('pass_all') for k, v in rep['roundtrip'].items()}))


main()
