"""clipkit.py - clip QA and clip repair for a stage-4 box-model GLB (Blender side; kit/clip_gate.py drives it).

    blender -b --factory-startup -P clipkit.py -- --glb in.glb --qa out.json
    blender -b --factory-startup -P clipkit.py -- --glb in.glb --fix out.glb --qa out.json [--sheet dir]

QA (per action): ground penetration (% H below the rest floor), planted-foot slide (std of planted-frame
foot speed, % H/frame, same metric as game_pack.py), loop gap (% H), NaN / flipped-quaternion keys.

Fix (animation only; meshes, skin weights and bind pose are re-exported as imported):
  1. sample the authored FK pose every frame;
  2. per foot (leaf limb bone near the floor): stance windows from contact height, falling back to the
     gait phase table (GAITS) when a move clip never brings the foot down; stance targets lock the
     contact point on the floor and move it at constant velocity across the window (zero for idle and
     attack plants, treadmill speed for in-place move cycles); swing targets keep the authored path but
     never dip under the floor; 2-frame blends at window edges;
  3. pelvis / root height compensation: the root bone lifts by the frame's body penetration;
  4. analytic two-bone IK (bend plane and knee side from the authored pose, end bone keeps its world
     orientation), then a per-foot vertex clamp lifts the foot target until its own skin clears the floor;
  5. every frame keyed (linear), quaternions sign-continuous, loop frame copied from frame 0.
"""
import bpy, sys, os, json, math, re
import numpy as np
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d

CLEAR = 0.05     # swing apex lift, fraction of H
DROP = 0.03      # max pelvis drop per frame for an over-extended stance leg, fraction of H
FOOT_KEYS = ('foot', 'toe', 'paw', 'hoof', 'flipper', 'claw', 'hand', 'shin', 'leg', 'ankle', 'shank', 'tarsus')
# gait phase tables: stance start phase and duty factor per limb role (fraction of the cycle)
GAITS = {
    'biped_walk': dict(duty=0.60, start={'L': 0.0, 'R': 0.5}),
    'quad_walk': dict(duty=0.75, start={'HL': 0.0, 'FL': 0.25, 'HR': 0.5, 'FR': 0.75}),
    'quad_trot': dict(duty=0.55, start={'HL': 0.0, 'FR': 0.0, 'HR': 0.5, 'FL': 0.5}),
    # 8 legs, alternating tetrapod: L1 R2 L3 R4 vs R1 L2 R3 L4 (role key = leg index + side)
    'octo_tetrapod': dict(duty=0.6, start={'1L': 0.0, '2R': 0.0, '3L': 0.0, '4R': 0.0,
                                           '1R': 0.5, '2L': 0.5, '3R': 0.5, '4L': 0.5}),
}


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    shapes = {pb.custom_shape for pb in arm.pose.bones if pb.custom_shape}
    for o in list(bpy.context.scene.objects):
        if o in shapes:
            bpy.data.objects.remove(o, do_unlink=True)
    return arm


def skinned(arm):
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]


def world_verts(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3); M = np.array(o.matrix_world)
        out.append(co @ M[:3, :3].T + M[:3, 3])
        oe.to_mesh_clear()
    return np.concatenate(out) if out else np.zeros((0, 3))


def owners(arm, objs):
    """dominant bone name per vertex (same order as world_verts)."""
    out = []
    for o in objs:
        names = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            best = max(v.groups, key=lambda g: g.weight, default=None)
            out.append(names.get(best.group) if best else None)
    return np.array(out, dtype=object)


def rest(arm, on):
    arm.data.pose_position = 'REST' if on else 'POSE'
    bpy.context.view_layer.update()


def set_action(arm, a):
    arm.animation_data_create()
    arm.animation_data.action = a
    if hasattr(arm.animation_data, 'action_slot') and getattr(a, 'slots', None):
        arm.animation_data.action_slot = a.slots[0]


NOT_FEET = ('tail', 'ear', 'wing', 'jaw', 'head', 'neck', 'tongue', 'horn', 'antenna', 'fin', 'spine', 'chest', 'trunk', 'snout', 'beak')


class Foot:
    """a ground limb: limb = [upper, lower, end, ...] from the limb root to the leaf; sole = the rest-pose
    lowest vertex of the end bones (glTF leaf tails are invented by the importer, so contact is a vertex)."""
    def __init__(self, name, limb, sole, parts, foot_parts):
        self.name, self.limb, self.sole, self.parts, self.foot_parts = name, limb, sole, parts, foot_parts

    @property
    def chain(self):
        L = self.limb
        if len(L) == 2:              # upper + leaf foot (importer-invented leaf tail): aim the upper bone only
            return (L[0], None, L[1])
        return (L[0], L[1], L[2])


def root_xy(arm):
    r = next(pb for pb in arm.pose.bones if pb.parent is None)
    h = arm.matrix_world @ r.head
    return np.array([h.x, h.y, 0.0])


def root_motion(rxy, H):
    """a clip whose root travels > 5 % H (lunge, pounce) carries root motion: feet are judged in the root frame."""
    R = np.array(rxy)
    return R - R[0] if float(np.ptp(R[:, :2], 0).max()) > 0.05 * H else np.zeros_like(R)


def pick_frame(tracks, RM, H):
    """world frame unless the low (contact) feet move less in the root frame: the clip then carries root motion.
    CFG world_plants: plants are always judged / locked in the world (root sway is not root motion)."""
    if not RM.any() or CFG.get('world_plants'):
        return RM
    def cost(off):
        c = 0.0
        for tr in tracks:
            t = np.array(tr)[:len(off)] - off; low = t[:, 2] < t[:, 2].min() + 0.03 * H
            v = np.linalg.norm(np.diff(t[:, :2], axis=0), axis=1)
            c += float(v[(low[1:] & low[:-1])].sum())
        return c
    return RM if cost(RM) < 0.5 * cost(np.zeros_like(RM)) else np.zeros_like(RM)


CFG = {}


def find_feet(arm, objs, ground, H, own):
    """CFG (per-creature clips.json): feet = [] (swimmer / no feet: penetration + loop only) or an explicit
    leaf-bone list; exclude = leaf bones (or name prefixes) never treated as feet."""
    if CFG.get('feet') == []:
        return []
    rest(arm, True)
    V = world_verts(objs)
    rest(arm, False)
    feet = []
    for b in arm.data.bones:
        if b.children:
            continue
        limb = [b]
        while limb[0].parent and len(limb[0].parent.children) == 1 and limb[0].parent.parent:
            limb.insert(0, limb[0].parent)
        if CFG.get('feet') and b.name not in CFG['feet']:
            continue
        if any(b.name.startswith(x) for x in CFG.get('exclude', [])):
            continue
        if len(limb) < 2 or any(t.startswith(k) for x in limb for t in re.split('[^a-z]+', x.name.lower()) for k in NOT_FEET):
            continue
        names = [x.name for x in limb]
        endb = names[2:] if len(names) >= 3 else names[-1:]
        fm = np.isin(own, endb)
        if not fm.any():
            continue
        idx = np.where(fm)[0]
        sole = int(idx[np.argmin(V[idx, 2])])
        if V[sole, 2] > ground + 0.06 * H:
            continue
        feet.append(Foot(b.name, names, sole, np.isin(own, names), fm))
    return feet


def role(b, arm):
    n = b.name.lower()
    side = 'L' if (n.endswith(('_l', '.l', 'l')) and ('_l' in n or '.l' in n)) else None
    x = (arm.matrix_world @ b.head_local).x
    side = side or ('L' if x > 0 else 'R')
    fwd = 'F' if any(k in n for k in ('hand', 'front', 'fore', 'arm', '_f', 'fl', 'fr')) else 'H'
    return side, fwd


# ---------------- QA ----------------
def qa(arm, objs, H, ground, feet, own):
    res = {}
    rest(arm, True); Vr = world_verts(objs); rest(arm, False)
    zrest = {f.name: float(Vr[f.sole, 2]) for f in feet}
    for a in bpy.data.actions:
        set_action(arm, a)
        deep = (0.0, None, None)
        f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1]))
        pen = 0.0; trk = {b.name: [] for b in feet}; poses = []; rxy = []
        for f in range(f0, f1 + 1):
            bpy.context.scene.frame_set(f)
            V = world_verts(objs)
            j = int(np.argmin(V[:, 2]))
            if V[j, 2] - ground < pen:
                deep = (V[j, 2] - ground, own[j], f)
            pen = min(pen, float(V[:, 2].min() - ground))
            for b in feet:
                trk[b.name].append(V[b.sole].copy())
            rxy.append(root_xy(arm))
            poses.append(np.array([np.array(arm.matrix_world @ pb.head) for pb in arm.pose.bones] +
                                  [np.array(arm.matrix_world @ pb.tail) for pb in arm.pose.bones]))
        sl = []; sa = []; contacts = 0; worstf = []; dbg = {}
        RM = pick_frame(list(trk.values()), root_motion(rxy, H), H)
        for n, tr in trk.items():
            tr = np.array(tr) - RM; zmin = min(tr[:, 2].min(), zrest[n])
            planted = tr[:, 2] < zrest[n] + 0.02 * H          # on the floor, not just at its own lowest
            v = np.linalg.norm(np.diff(tr[:, :2], axis=0), axis=1)
            pl = planted[1:] & planted[:-1]
            if pl.sum() >= 2:
                contacts += int(pl.sum())
                sl.append(float(np.std(v[pl]) / H * 100))     # treadmill consistency (game_pack metric)
                sa.append(float(np.mean(v[pl]) / H * 100))    # absolute planted speed
                worstf.append((sl[-1], n))
                dbg[n] = dict(z=[round(float(x - zrest[n]) / H * 100, 2) for x in tr[:, 2]],
                              v=[round(float(x) / H * 100, 2) for x in v])
        loop = float(np.abs(poses[0] - poses[-1]).max() / H * 100)
        nan, flips = 0, 0
        for fc in fcurves_of(a):
            ys = [k.co[1] for k in fc.keyframe_points]
            nan += sum(1 for y in ys if not math.isfinite(y))
        for bn, qs in quat_tracks(a).items():
            for i in range(1, len(qs)):
                if np.dot(qs[i], qs[i - 1]) < 0:
                    flips += 1
        res[clean(a.name)] = dict(frames=f1 - f0 + 1, penetration_pctH=round(-pen / H * 100, 3),
                                  foot_slide_std_pctH=round(max(sl) if sl else 0.0, 3),
                                  foot_speed_planted_pctH=round(max(sa) if sa else 0.0, 3), planted_frames=contacts,
                                  loop_gap_pctH=round(loop, 3), nan_keys=nan, quat_flips=flips,
                                  deepest=[deep[1], deep[2]], slide_foot=max(worstf)[1] if worstf else None,
                                  track=dbg.get(max(worstf)[1]) if worstf else None)
    arm.animation_data.action = None
    return res


def clean(n):
    return n.split('|')[-1]


def fcurves_of(a):
    if hasattr(a, 'fcurves') and len(getattr(a, 'fcurves', [])):
        return list(a.fcurves)
    out = []
    for L in getattr(a, 'layers', []):
        for s in L.strips:
            for cb in getattr(s, 'channelbags', []):
                out += list(cb.fcurves)
    return out


def quat_tracks(a):
    by = {}
    for fc in fcurves_of(a):
        if fc.data_path.endswith('rotation_quaternion') and '"' in fc.data_path:
            bn = fc.data_path.split('"')[1]
            by.setdefault(bn, {})[fc.array_index] = fc
    out = {}
    for bn, d in by.items():
        if len(d) < 4:
            continue
        fr = sorted({k.co[0] for k in d[0].keyframe_points})
        out[bn] = [np.array([d[i].evaluate(f) for i in range(4)]) for f in fr]
    return out


# ---------------- fix ----------------
def rot_about(M, pivot, R):
    T = Matrix.Translation(pivot); Ti = Matrix.Translation(-pivot)
    return T @ R.to_matrix().to_4x4() @ Ti @ M


def set_world(arm, pb, Mw):
    pb.matrix = arm.matrix_world.inverted() @ Mw
    bpy.context.view_layer.update()


def W(arm, pb):
    return arm.matrix_world @ pb.matrix


def two_bone(arm, A, B, E, t):
    """place the effector (E head, or B tail without an end bone) at world point t; bend plane and knee side
    from the current pose; E keeps its world rotation (its children follow their own FK)."""
    mw = arm.matrix_world
    pa = arm.pose.bones[A]
    pe = arm.pose.bones[E] if E else None
    Erot = W(arm, pe).to_quaternion() if pe else None
    if B is None:                    # one-bone aim: swing A so E's head points at t, E keeps its world rotation
        a = mw @ pa.head; e = mw @ pe.head
        R = (e - a).rotation_difference(t - a)
        set_world(arm, pa, rot_about(W(arm, pa), a, R))
        M = W(arm, pe); h = M.translation.copy()
        M2 = Erot.to_matrix().to_4x4() @ Matrix.Diagonal(M.to_scale().to_4d()); M2.translation = h
        set_world(arm, pe, M2)
        return
    pbb = arm.pose.bones[B]
    a = mw @ pa.head; b = mw @ pbb.head
    e = (mw @ pe.head) if pe else (mw @ pbb.tail)
    l1 = (b - a).length; l2 = (e - b).length
    if l1 < 1e-6 or l2 < 1e-6:
        return
    d_vec = t - a; d = d_vec.length
    d = min(max(d, abs(l1 - l2) + 1e-5), l1 + l2 - 1e-5)
    u = d_vec.normalized() if d_vec.length > 1e-9 else (e - a).normalized()
    n = (b - a).cross(e - b)
    if n.length < 1e-6 * l1 * l2:
        n = (b - a).cross(Vector((1, 0, 0)))
        if n.length < 1e-9:
            n = Vector((0, 1, 0))
    n.normalize()
    v = n.cross(u); v = v - u * v.dot(u); v.normalize()
    side = (b - a) - u * (b - a).dot(u)
    if side.dot(v) < 0:
        v = -v
    x = (l1 * l1 - l2 * l2 + d * d) / (2 * d); y = math.sqrt(max(l1 * l1 - x * x, 0.0))
    k = a + u * x + v * y
    tt = a + u * d
    R1 = (b - a).rotation_difference(k - a)
    set_world(arm, pa, rot_about(W(arm, pa), a, R1))
    b2 = mw @ pbb.head
    e2 = (mw @ pe.head) if pe else (mw @ pbb.tail)
    R2 = (e2 - b2).rotation_difference(tt - b2)
    set_world(arm, pbb, rot_about(W(arm, pbb), b2, R2))
    if pe:
        M = W(arm, pe); h = M.translation.copy()
        M2 = Erot.to_matrix().to_4x4() @ Matrix.Diagonal(M.to_scale().to_4d()); M2.translation = h
        set_world(arm, pe, M2)


def reach(arm, f, t):
    """(excess length, hip head, limb vector) of effector target t beyond 0.985 x full extension."""
    A, B, E = f.chain
    mw = arm.matrix_world
    a = mw @ arm.pose.bones[A].head
    if B is None:                    # one-bone aim leg: fixed length
        return (t - a).length - 0.985 * (mw @ arm.pose.bones[E].head - a).length, a, 0.985 * (mw @ arm.pose.bones[E].head - a).length
    b = mw @ arm.pose.bones[B].head
    e = (mw @ arm.pose.bones[E].head) if E else (mw @ arm.pose.bones[B].tail)
    L = 0.985 * ((b - a).length + (e - b).length)
    return (t - a).length - L, a, L


def toe_roll(arm, f, goal, sole):
    """end-bone roll: pivot the end bone about its head so the sole swings onto the goal (leg at full stretch)."""
    A, B, E = f.chain
    if not E:
        return
    pe = arm.pose.bones[E]; M = W(arm, pe); h = M.translation.copy()
    s = Vector(sole) - h; g = goal - h
    if s.length < 1e-6 or g.length < 1e-6:
        return
    R = s.rotation_difference(g)
    ang = min(R.angle, math.radians(CFG.get('roll_max_deg', 35)))
    R = Quaternion(R.axis, ang)
    set_world(arm, pe, rot_about(M, h, R))


def effector(arm, f):
    A, B, E = f.chain
    mw = arm.matrix_world
    return Vector(mw @ arm.pose.bones[E].head) if E else Vector(mw @ arm.pose.bones[B].tail)



def runs(mask):
    """cyclic contiguous True runs over n unique frames -> list of index lists."""
    n = len(mask)
    if mask.all():
        return [list(range(n))]
    if not mask.any():
        return []
    s = int(np.argmin(mask))          # start scanning at a False
    out, cur = [], []
    for j in range(n):
        i = (s + j) % n
        if mask[i]:
            cur.append(i)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def plan_targets(f, tr, zc, H, N, cyc, is_move, gait, arm):
    """per-frame sole target from the authored track: stance lock + swing clearance + edge blends."""
    z = tr[:, 2]
    thr = min(0.03 * H, max(0.006 * H, 0.35 * float(np.ptp(z))))   # shuffles: contact = lowest third of the lift
    st = z < max(z.min(), zc) + thr
    if not is_move:                   # idle / attack: a plant does not travel; a low dragging foot is a swing
        sp = np.linalg.norm(tr[:, :2] - np.roll(tr[:, :2], 1, 0), axis=1)
        sp = np.maximum(sp, np.roll(sp, -1))
        st &= sp < 0.004 * H
        if float(np.ptp(z)) < 0.02 * H:   # a support foot that never really lifts: planted for the whole clip
            st[:] = True
    src = 'contact'
    if is_move and 2 <= st.sum() < N:  # move: close 1-2 frame lift flickers, drop 1-frame touches
        for r in runs(~st):
            if len(r) <= 2:
                st[r] = True
        for r in runs(st):
            if len(r) <= 1:
                st[r] = False
    if is_move and CFG.get('one_stance', True) and len(runs(st)) > 1 and st.sum() < N:   # one plant per cycle
        rr = runs(st); keep = max(rr, key=len)
        for r in rr:
            if r is not keep:
                st[r] = False
    if is_move and gait and (st.all() or st.sum() < 2 or gait in CFG.get('force_gait', [])):
        sd, fw = role(arm.data.bones[f.name], arm); g = GAITS[gait]
        if gait == 'octo_tetrapod':
            fw = (re.findall(r'\d', f.name) or ['1'])[0]
        key = sd if gait.startswith('biped') else fw + sd
        ph = (np.arange(N) / N - g['start'].get(key, 0.0)) % 1.0
        st = ph < g['duty']; src = 'gait:' + gait
    tgt = tr.copy(); w = np.zeros(N)
    tgt[:, 2] = np.maximum(tgt[:, 2], zc)
    for r in runs(st):
        if len(r) == N:               # planted the whole clip (idle, attack plants): lock at the mean
            tgt[:, 0:2] = tr[:, 0:2].mean(0); tgt[:, 2] = zc; w[:] = 1; continue
        p_s, p_e = tr[r[0], :2], tr[r[-1], :2]
        if not is_move:               # idle / attack plant: no travel inside the window
            p_s = p_e = tr[r, :2].mean(0)
        for j, i in enumerate(r):
            s = j / max(len(r) - 1, 1)
            tgt[i, :2] = p_s + (p_e - p_s) * s; tgt[i, 2] = zc; w[i] = 1.0
    for r in runs(~st):               # swing: lift off fast, travel high, set down fast (no low sliding frames)
        h = CLEAR * H if is_move else max(0.03 * H, min(CLEAR * H, float(z[r].max() - zc)))   # a moving foot clears the floor
        for j, i in enumerate(r):
            s = (j + 1) / (len(r) + 1)
            # lift >= 2.5 % H from the first swing frame: a travelling foot never skims inside the plant band
            tgt[i, 2] = max(tgt[i, 2], zc + max(min(h, 0.025 * H), h * min(1.0, 3.0 * math.sin(math.pi * s))))
    w2 = w.copy()                     # 2-frame blend outside each window
    for i in range(N):
        if w[i] == 0:
            nb = [w[(i + d) % N] if cyc else (w[i + d] if 0 <= i + d < N else 0) for d in (-2, -1, 1, 2)]
            w2[i] = 0.66 if (nb[1] or nb[2]) else (0.33 if (nb[0] or nb[3]) else 0.0)
    w2 = w                            # windows meet the authored path at their ends: no extra blend
    swing = tr.copy(); swing[:, 2] = np.maximum(swing[:, 2], tgt[:, 2])
    out = swing * (1 - w2[:, None]) + tgt * w2[:, None]
    out[:, 2] = np.maximum(out[:, 2], zc)
    f.stance = st
    return out, dict(stance=int(st.sum()), src=src, xy_range_pctH=[round(float(np.ptp(tr[:, k])) / H * 100, 2) for k in (0, 1)],
                     z_range_pctH=round(float(np.ptp(z)) / H * 100, 2))


def fix_action(arm, objs, own, a, H, ground, feet, is_move, gait):
    set_action(arm, a)
    f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1]))
    frames = list(range(f0, f1 + 1))
    # 1. sample FK
    fk_basis = []; contact = {f.name: [] for f in feet}; first = last = None; rxy = []
    for fr in frames:
        bpy.context.scene.frame_set(fr)
        fk_basis.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy() if pb.rotation_mode == 'QUATERNION'
                                   else pb.rotation_euler.to_quaternion(), pb.scale.copy()) for pb in arm.pose.bones})
        V = world_verts(objs)
        for f in feet:
            contact[f.name].append(V[f.sole].copy())
        rxy.append(root_xy(arm))
        P = np.array([np.array(arm.matrix_world @ pb.head) for pb in arm.pose.bones])
        first = P if first is None else first; last = P
    cyc = bool(np.abs(first - last).max() / H < 0.002)
    N = len(frames) - 1 if cyc else len(frames)
    rest(arm, True)
    Vr = world_verts(objs)
    rest(arm, False)
    RM = pick_frame(list(contact.values()), root_motion(rxy, H), H)
    targets = {}; info = {}
    for f in feet:
        zc = float(Vr[f.sole, 2])
        targets[f.name], info[f.name] = plan_targets(f, np.array(contact[f.name][:N]) - RM[:N], zc, H, N, cyc, is_move, gait, arm)
        f.zc = zc
    ai = CFG.get('aim_ik')
    ik = [f for f in feet if f.chain[1] is not None or ai is True or (isinstance(ai, list) and clean(a.name) in ai)]
    replans = {}
    aim = [f for f in feet if f.chain[1] is None]     # one-bone legs: pelvis height carries the contact
    # 2. per frame: IK to sole targets, root lift for body penetration, per-foot skin clamp
    root = next(pb for pb in arm.pose.bones if pb.parent is None)
    limb_mask = np.zeros(len(own), bool)
    for f in feet:
        limb_mask |= f.parts
    for pas in range(2):        # pass 2 re-plans plants the legs could not hold (reach limit): spread the slip
        out = []; resid = []; drops = []; rolls = {}; dbg = {}; ach = {f.name: [None] * N for f in ik}
        for i in range(N):
            bpy.context.scene.frame_set(frames[i])
            arm.animation_data.action = None
            for pb in arm.pose.bones:
                l, q, s = fk_basis[i][pb.name]
                pb.rotation_mode = 'QUATERNION'; pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            bpy.context.view_layer.update()
            V = world_verts(objs)
            pl = [f for f in aim if f.stance[i]]
            if pl:                         # pelvis height: the lowest planted short-leg foot touches the floor
                dz = -min(float(V[f.sole, 2]) - f.zc for f in pl)
                M = W(arm, root); M.translation.z += dz; set_world(arm, root, M)
                V = world_verts(objs)
            goal = {f.name: Vector(targets[f.name][i] + RM[i]) for f in ik}
            eff = {f.name: effector(arm, f) + (goal[f.name] - Vector(V[f.sole])) for f in ik}
            # pelvis drop: a stance foot past full extension pulls the root down (capped), so the plant stays reachable
            drop = 0.0
            for f in ik:
                if f.stance[i]:
                    ex, a0, L = reach(arm, f, eff[f.name])
                    if ex > 0:
                        v = eff[f.name] - a0; hz = (v.x * v.x + v.y * v.y) ** 0.5
                        if v.z < 0:
                            drop = max(drop, -v.z - (L * L - hz * hz) ** 0.5 if hz < L else -v.z)
            drop = min(drop, DROP * H)
            if drop > 1e-6:                # a swing foot reaching out (swipe, stride) must not be dragged down by the drop
                sw = [f for f in ik if not f.stance[i]]
                ex0 = {f.name: reach(arm, f, eff[f.name])[0] for f in sw}
                M0 = W(arm, root)
                for _ in range(4):
                    M = M0.copy(); M.translation.z -= drop; set_world(arm, root, M)
                    if all(reach(arm, f, eff[f.name])[0] <= max(0.0, ex0[f.name]) + 1e-4 * H for f in sw):
                        break
                    drop *= 0.5
                else:
                    set_world(arm, root, M0); drop = 0.0
                if drop > 1e-6:
                    drops.append(drop / H * 100)
            for it in range(10):
                for f in ik:
                    A, B, E = f.chain
                    two_bone(arm, A, B, E, eff[f.name])
                V = world_verts(objs)
                moved = False
                body = V[~limb_mask] if (~limb_mask).any() else V
                dz = ground - float(body[:, 2].min())
                if dz > 1e-5:
                    M = W(arm, root); M.translation.z += dz; set_world(arm, root, M)
                    continue
                lf = aim + (ik if it >= 5 else [])   # short legs, or IK that cannot clear the floor: lift the root
                fz = max([ground - float(V[f.parts][:, 2].min()) for f in lf] or [0.0])
                if fz > 1e-5:
                    M = W(arm, root); M.translation.z += fz; set_world(arm, root, M)
                    continue
                for f in ik:
                    err = goal[f.name] - Vector(V[f.sole])
                    fz = ground - float(V[f.parts][:, 2].min())
                    if fz > 1e-5:
                        goal[f.name].z += fz * 1.02; err.z += fz * 1.02
                    if err.length > 1e-4 * H:
                        eff[f.name] += err; moved = True
                if not moved:
                    break
            else:                          # the last pass may have lifted the root: re-solve so the feet follow it
                for f in ik:
                    A, B, E = f.chain
                    two_bone(arm, A, B, E, eff[f.name])
            for f in ik:                   # toe / end-bone roll when the IK clamps at full stretch
                if not f.stance[i]:
                    continue
                E = f.chain[2]
                if not E or reach(arm, f, effector(arm, f) + (goal[f.name] - Vector(world_verts(objs)[f.sole])))[0] < 0:
                    continue
                for _ in range(3):
                    V = world_verts(objs)
                    g = goal[f.name].copy(); g.z = max(f.zc, min(g.z, float(V[f.sole, 2])))   # roll for the plant spot
                    if (g - Vector(V[f.sole])).length < 0.002 * H:
                        break
                    keep = arm.pose.bones[E].matrix.copy()
                    toe_roll(arm, f, g, V[f.sole])
                    V2 = world_verts(objs)
                    if ground - float(V2[:, 2].min()) > 1e-4 * H + max(0.0, ground - float(V[:, 2].min())):   # roll may not dig in
                        arm.pose.bones[E].matrix = keep; bpy.context.view_layer.update()
                        break
                    rolls[f.name] = rolls.get(f.name, 0) + 1
            V = world_verts(objs); j = int(np.argmin(V[:, 2]))
            for f in ik:
                dbg.setdefault(f.name, []).append([int(f.stance[i]), round((goal[f.name].z - f.zc) / H * 100, 2),
                                                   round((float(V[f.sole, 2]) - f.zc) / H * 100, 2),
                                                   round((goal[f.name] - Vector(V[f.sole])).length / H * 100, 2),
                                                   round(reach(arm, f, eff[f.name])[0] / H * 100, 2),
                                                   round((eff[f.name] - effector(arm, f)).length / H * 100, 2), it])
            for f in ik:
                ach[f.name][i] = np.array(V[f.sole]) - RM[i]
            resid.append((frames[i], round(float(ground - V[j, 2]) / H * 100, 3), own[j], it))
            out.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in arm.pose.bones})
            set_action(arm, a)
        bad = {}
        for f in ik:
            A = np.array(ach[f.name]); T = targets[f.name]
            e = np.linalg.norm(A[:, :2] - T[:, :2], axis=1)
            b = f.stance & (e > 0.0015 * H)
            if b.any():
                bad[f.name] = (A, b)
        if pas or not bad:
            break
        for f in ik:
            if f.name not in bad:
                continue
            A, b = bad[f.name]; T = targets[f.name]
            k = np.exp(-0.5 * (np.arange(-6, 7) / 2.5) ** 2); k /= k.sum()
            idx = np.arange(N)
            sm = np.stack([sum(k[j] * A[(idx + j - 6) % N if cyc else np.clip(idx + j - 6, 0, N - 1), c] for j in range(13))
                           for c in (0, 1)], 1)
            near = np.zeros(N, bool)    # an unreachable plant becomes a quick step: lift, follow the body, set down
            for i in np.where(b)[0]:
                for d in range(-1, 2):
                    near[(i + d) % N if cyc else min(max(i + d, 0), N - 1)] = True
            m = near & f.stance
            for r in runs(m):
                for j, i in enumerate(r):
                    s_ = (j + 1) / (len(r) + 1)
                    T[i, :2] = sm[i]; T[i, 2] = f.zc + max(0.025 * H, CLEAR * H * min(1.0, 3.0 * math.sin(math.pi * s_)))
            f.stance = f.stance & ~m
        replans['n'] = len(bad)
    if cyc:
        out.append(out[0])
    else:
        frames = frames[:len(out)]
    # 5. key into a fresh action, replace the old one
    name = a.name
    na = bpy.data.actions.new(name + '_fix')
    arm.animation_data.action = None
    set_action(arm, na)
    prev = {}
    for f, pose in zip(frames, out):
        for pb in arm.pose.bones:
            l, q, s = pose[pb.name]
            if pb.name in prev and q.dot(prev[pb.name]) < 0:
                q = -q
            prev[pb.name] = q
            pb.rotation_mode = 'QUATERNION'
            pb.location = l; pb.rotation_quaternion = q; pb.scale = s
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('scale', frame=f)
    for fc in fcurves_of(na):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    arm.animation_data.action = None
    a.name = name + '_old'
    bpy.data.actions.remove(a)
    na.name = name
    na.use_fake_user = True
    return dict(feet=info, cyclic=cyc, pelvis_drop_max_pctH=round(max(drops or [0]), 3), roll_frames=rolls, replanned_feet=replans.get('n', 0), dbg=dbg, chains={f.name: list(f.limb) for f in feet}, worst_resid=list(max(resid, key=lambda r: r[1])))


def export(arm, path):
    arm.animation_data_create(); arm.animation_data.action = None
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    for a in bpy.data.actions:
        tr = arm.animation_data.nla_tracks.new(); tr.name = a.name
        tr.strips.new(a.name, int(a.frame_range[0]), a); tr.mute = True
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                              export_def_bones=False, export_skins=True, export_vertex_color='ACTIVE',
                              export_all_vertex_colors=False, export_materials='EXPORT', export_extras=False,
                              export_attributes=False, export_image_format='NONE', export_morph=False)


def sheet(arm, objs, outdir, tag, ground, H):
    """side-view workbench frames of every clip (4 phases) with a floor line."""
    os.makedirs(outdir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x = 360; sc.render.resolution_y = 300
    V = world_verts(objs); c = V.mean(0); span = np.ptp(V, 0)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(max(span[1], span[2]) * 1.35)
    cam.location = (c[0] + 10 * max(span), c[1], ground + 0.45 * H)
    cam.rotation_euler = (math.pi / 2, 0, math.pi / 2); sc.camera = cam
    me = bpy.data.meshes.new('floor')
    R = max(span) * 2
    me.from_pydata([(-R, -R, ground - 0.001), (R, -R, ground - 0.001), (R, R, ground - 0.001), (-R, R, ground - 0.001)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('floor', me); sc.collection.objects.link(fl)
    mat = bpy.data.materials.new('floorm'); mat.diffuse_color = (0.25, 0.35, 0.8, 1); me.materials.append(mat)
    paths = []
    for a in sorted(bpy.data.actions, key=lambda a: clean(a.name)):
        set_action(arm, a)
        f0, f1 = a.frame_range
        for q in (0, 0.25, 0.5, 0.75):
            f = int(round(f0 + (f1 - f0) * q)); sc.frame_set(f)
            p = os.path.join(outdir, f'{tag}_{clean(a.name)}_{int(q * 100):02d}.png')
            sc.render.filepath = p; bpy.ops.render.render(write_still=True); paths.append(p)
    arm.animation_data.action = None
    return paths


def main():
    global DROP
    if arg('--cfg') and os.path.exists(arg('--cfg')):
        CFG.update(json.load(open(arg('--cfg'))))
    DROP = CFG.get('pelvis_drop', DROP)
    arm = load(os.path.abspath(arg('--glb')))
    objs = skinned(arm)
    rest(arm, True)
    V = world_verts(objs); H = float(np.ptp(V[:, 2])); ground = float(V[:, 2].min())
    rest(arm, False)
    own = owners(arm, objs)
    feet = find_feet(arm, objs, ground, H, own)
    rep = dict(src=arg('--glb'), H=H, feet=[b.name for b in feet], bones=len(arm.data.bones))
    kind = CFG.get('gait') or arg('--gait', 'auto')
    if kind == 'auto':
        n = len(feet)
        kind = 'biped_walk' if n == 2 else ('quad_trot' if n == 4 else ('octo_tetrapod' if n == 8 else None))
    rep['gait'] = kind
    if arg('--sheet') and '--fix' in argv:
        rep['sheet_before'] = sheet(arm, objs, arg('--sheet'), 'before', ground, H)
    if '--fix' in argv:
        rep['before'] = qa(arm, objs, H, ground, feet, own)
        rep['fix'] = {}
        for a in list(bpy.data.actions):
            nm = clean(a.name)
            rep['fix'][nm] = fix_action(arm, objs, own, a, H, ground, feet, nm == 'move', kind)
        export(arm, os.path.abspath(arg('--fix')))
        # measure the exported file, not the in-memory scene
        arm = load(os.path.abspath(arg('--fix'))); objs = skinned(arm)
        own = owners(arm, objs); feet = find_feet(arm, objs, ground, H, own)
    rep['clips'] = qa(arm, objs, H, ground, feet, own)
    if arg('--sheet') and '--fix' not in argv:
        t = arg('--sheet-tag', 'qa')
        rep['sheet_' + t] = sheet(arm, objs, arg('--sheet'), t, ground, H)
    json.dump(rep, open(arg('--qa'), 'w'), indent=1)
    print('CLIPKIT', json.dumps(rep['clips']))


main()
