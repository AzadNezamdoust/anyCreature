"""Skin-weight refinement after bone heat (t8/weights, 2026-10-22). Runs inside Blender.

refine(body, rig, **cfg) rewrites the deform vertex groups of `body` (bone heat already applied):
  1. side cleanup   - a '.L' bone never weights a vertex on -X (and '.R' on +X) beyond the seam band
                      (stops the groin knife fold / cross-thigh leaks bone heat makes between the legs);
  2. joint falloff  - per joint (deform bone with a deform parent), inside a capsule round the pivot, the
                      parent/child split is replaced by a smoothstep along the child axis whose width is set
                      per joint role (`falloff`), blended back to heat at the capsule rim. Fixes belly verts
                      owned by the thigh (crouch pinch), ragged heat at elbows/knees and the deltoid seam;
  3. smoothing      - Laplacian smoothing of the weights inside the joint zones (topology neighbours);
  4. cap / prune / normalise to `max_inf` influences, then mirror-exact (-X copies its +X twin, L/R swapped).
Works on welded (kit) and glTF-split (imported) meshes: vertices are canonicalised by position.
Export-safe: plain LBS vertex weights only (no drivers, no Preserve Volume / DQS, no extra bones), so a
game engine deforms exactly like the ROM gate measures. Returns a stats dict.
"""
import math
import numpy as np

DEFAULT = dict(   # v2 = the t8/weights werewolf pilot winner (cfg e5)
    seam=0.012,                 # |x| band (m) treated as the mirror seam
    falloff=dict(root=0.85, mid=1.4, distal=0.45, spine=0.9, tail=0.7, other=0.6),    # blend half-width / joint r
    centre=dict(root=0.0, mid=0.7, distal=0.0, spine=0.0, tail=0.0, other=0.0),       # blend centre / joint r (+ = child-ward)
    zone=2.2,                   # capsule half-length along the axis / joint r
    radial=(1.15, 1.5),         # full parametric inside radial < a*r, back to heat at b*r
    smooth_iters=2, smooth_lam=0.5, smooth_zone=1.8, smooth_roles=('mid', 'distal'),
    joint_falloff=True, mix=dict(mid=1.0),   # share of the parametric split per role (0 / missing = keep heat)
    max_inf=4, prune=0.01,
    side_clean=False,           # L/R hard split at the seam: measured worse (groin stretch 2.4), off
    helpers=('root', 'mid', 'distal'),   # roles that get a half-rotation helper bone (add_helpers); () = none
    skip=('ear', 'eye', 'jaw', 'tongue', 'lid', 'horn', 'antler', 'tuft'),
)

HELPER = '_mid'


def helper_name(child):
    for s in ('.L', '.R'):
        if child.endswith(s):
            return child[:-2] + HELPER + s
    return child + HELPER


def helper_source(name):
    """'forearm_mid.L' -> 'forearm.L' (None when not a helper name)."""
    for s in ('.L', '.R', ''):
        if s and not name.endswith(s):
            continue
        base = name[:-2] if s else name
        if base.endswith(HELPER):
            return base[:-len(HELPER)] + s
    return None


def add_helpers(rig, roles=('root', 'mid', 'distal'), constraint=True):
    """Half-rotation helper bones (export-safe volume preservation for plain LBS): for every side limb joint whose
    role is in `roles`, a short deform bone '<child>_mid<side>' with the child's head and rest frame, parented to the
    child's parent. With constraint=True it gets COPY_ROTATION (local / local, influence 0.5) of the child, so it
    turns half the joint angle; the glTF export (force sampling) bakes that into every clip, so engines need no
    constraint. Vertices in the joint's blend band are weighted parent -> helper -> child (refine), so a vertex at
    the middle of the band ROTATES by half the angle instead of collapsing to the LBS chord (elbow / knee collapse,
    thigh-belly pinch, deltoid seam). Returns [(helper, child)]."""
    import bpy
    todo = []
    for b in rig.data.bones:
        if not b.use_deform or helper_source(b.name) or not b.name.endswith(('.L', '.R')):
            continue
        par = b.parent
        while par is not None and not par.use_deform:
            par = par.parent
        if par is None or role(b) not in roles or helper_name(b.name) in rig.data.bones:
            continue
        if any(b.name.lower().startswith(s) for s in DEFAULT['skip']):
            continue
        todo.append((helper_name(b.name), b.name, par.name))
    if not todo:
        return []
    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        eb = rig.data.edit_bones
        for hn, cn, pn in todo:
            c = eb[cn]
            h = eb.new(hn)
            h.head = c.head.copy()
            h.tail = c.head + (c.tail - c.head) * 0.35
            h.roll = c.roll
            h.parent = eb[pn]
            h.use_connect = False
            h.use_deform = True
        bpy.ops.object.mode_set(mode='OBJECT')
    if constraint:
        for hn, cn, pn in todo:
            pb = rig.pose.bones[hn]
            k = pb.constraints.new('COPY_ROTATION')
            k.target, k.subtarget = rig, cn
            k.owner_space = k.target_space = 'LOCAL'
            k.mix_mode = 'REPLACE'
            k.influence = 0.5
    bpy.context.view_layer.objects.active = prev
    return [(hn, cn) for hn, cn, pn in todo]


def sync_helpers(rig):
    """Pose-time emulation of the helper constraint for rigs re-imported from glTF (no constraints there):
    helper local rotation = slerp(identity, child local rotation, 0.5). Call after posing, before evaluating."""
    from mathutils import Quaternion
    PB = rig.pose.bones
    n = 0
    for pb in PB:
        src = helper_source(pb.name)
        if not src or src not in PB:
            continue
        s = PB[src]
        q = s.rotation_quaternion.copy() if s.rotation_mode == 'QUATERNION' else s.rotation_euler.to_quaternion()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion().slerp(q, 0.5)
        n += 1
    return n


def _merge(cfg):
    c = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT.items()}
    for k, v in (cfg or {}).items():
        if isinstance(v, dict) and isinstance(c.get(k), dict):
            c[k].update(v)
        else:
            c[k] = v
    return c


def mirror_name(n):
    if n.endswith('.L'):
        return n[:-2] + '.R'
    if n.endswith('.R'):
        return n[:-2] + '.L'
    return n


def role(bone):
    """root (limb leaves the torso), mid (2nd limb segment), distal (3rd+), spine, tail, other."""
    n = bone.name.lower()
    if any(s in n for s in ('tail', 'trunk')):
        return 'tail'
    side = bone.name.endswith(('.L', '.R'))
    if not side:
        return 'spine'
    d, p = 0, bone
    while p.parent is not None and p.parent.name.endswith(('.L', '.R')):
        d += 1
        p = p.parent
    return ('root', 'mid', 'distal')[min(d, 2)]


def bone_table(rig):
    M = rig.matrix_world
    out = {}
    for b in rig.data.bones:
        if not b.use_deform:
            continue
        h, t = np.array(M @ b.head_local), np.array(M @ b.tail_local)
        par = b.parent
        while par is not None and not par.use_deform:
            par = par.parent
        out[b.name] = dict(bone=b, head=h, tail=t, dir=(t - h) / max(np.linalg.norm(t - h), 1e-9),
                           length=float(np.linalg.norm(t - h)), parent=par.name if par is not None else None,
                           role=role(b))
    return out


def _seg_dist(P, a, b):
    d = b - a
    t = np.clip(((P - a) @ d) / max(d @ d, 1e-12), 0, 1)
    return np.linalg.norm(a + t[:, None] * d - P, axis=1)


def refine(body, rig, **cfg):
    c = _merge(cfg)
    me = body.data
    nv = len(me.vertices)
    W_ = body.matrix_world
    P = np.array([tuple(W_ @ v.co) for v in me.vertices])
    keymap, C = {}, np.zeros(nv, int)
    for i, p in enumerate(P):
        C[i] = keymap.setdefault((round(p[0], 5), round(p[1], 5), round(p[2], 5)), len(keymap))
    nc = len(keymap)
    first = np.zeros(nc, int)
    first[C[::-1]] = np.arange(nv)[::-1]
    Q = P[first]
    helpers = add_helpers(rig, tuple(c['helpers']), c.get('helper_constraint', True)) if c['helpers'] else []
    B = bone_table(rig)
    names = sorted(B)
    bi = {n: i for i, n in enumerate(names)}
    nb = len(names)
    gname = {g.index: g.name for g in body.vertex_groups}
    W = np.zeros((nc, nb))
    cnt = np.zeros(nc)
    for v in me.vertices:
        ci = C[v.index]
        cnt[ci] += 1
        for g in v.groups:
            n = gname.get(g.group)
            if n in bi:
                W[ci, bi[n]] += g.weight
    W /= np.maximum(cnt, 1)[:, None]
    # adjacency (canonical)
    nbr = [set() for _ in range(nc)]
    for e in me.edges:
        a, b = C[e.vertices[0]], C[e.vertices[1]]
        if a != b:
            nbr[a].add(b); nbr[b].add(a)
    for p_ in me.polygons:          # glTF-split meshes: connect polygon rings too
        vs = [C[i] for i in p_.vertices]
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            if a != b:
                nbr[a].add(b); nbr[b].add(a)
    seg = np.stack([_seg_dist(Q, B[n]['head'], B[n]['tail']) for n in names], 1)

    def renorm(Wm):
        s = Wm.sum(1)
        bad = s < 1e-6
        if bad.any():
            Wm[bad] = 0
            Wm[bad, np.argmin(seg[bad], 1)] = 1.0
            s = Wm.sum(1)
        return Wm / s[:, None]

    W = renorm(W)
    stats = dict(verts=nv, canon=nc, bones=nb, helpers=len(helpers))

    # 1. side cleanup
    Lm = np.array([n.endswith('.L') for n in names]); Rm = np.array([n.endswith('.R') for n in names])
    neg, pos = Q[:, 0] < -c['seam'], Q[:, 0] > c['seam']
    before = W.copy()
    if c['side_clean']:
        W[np.ix_(neg, Lm)] = 0
        W[np.ix_(pos, Rm)] = 0
    else:
        neg = np.zeros(nc, bool); pos = neg
    stats['side_cleaned'] = int((np.abs(before - W).sum(1) > 1e-6).sum())
    W = renorm(W)

    # 2. joint falloff
    dom = np.argmax(W, 1)
    zones = np.zeros(nc, bool)
    joints = []
    for n in names:
        j = B[n]
        if helper_source(n):
            continue
        if j['parent'] is None or j['parent'] not in bi or any(n.lower().startswith(s) for s in c['skip']):
            continue
        ib, ip = bi[n], bi[j['parent']]
        h0, ax = j['head'], j['dir']
        d = Q - h0
        hh = d @ ax
        rad = np.linalg.norm(d - np.outer(hh, ax), axis=1)
        sel = (np.abs(hh) < 0.25 * j['length']) & np.isin(dom, [ib, ip]) & (rad < 2.0 * j['length'])
        r = float(np.median(rad[sel])) if sel.sum() >= 6 else 0.3 * j['length']
        r = max(min(r, 1.2 * j['length']), 0.05 * j['length'])
        R = j['role']
        a = c['falloff'].get(R, 0.6) * r
        cen = c['centre'].get(R, 0.0) * r
        S = W[:, ib] + W[:, ip]
        ra, rb = c['radial']
        alpha = np.clip((rb * r - rad) / max((rb - ra) * r, 1e-9), 0, 1)
        inzone = (np.abs(hh) < c['zone'] * r) & (alpha > 0) & (S > 1e-4)
        hb = bi.get(helper_name(n))
        # a vertex heat gave to neither of the two keeps its weights
        inzone &= (W[:, ib] + W[:, ip]) >= 0.5 * W.sum(1)
        u = np.clip((hh - cen + a) / (2 * a), 0, 1)
        t = u * u * (3 - 2 * u)
        theat = np.where(S > 1e-9, W[:, ib] / np.maximum(S, 1e-9), 0)
        mx = c['mix'].get(R, 0.0) if isinstance(c['mix'], dict) else c['mix']
        alpha = alpha * (mx if c['joint_falloff'] else 0.0)
        tn = alpha * t + (1 - alpha) * theat
        idx = np.where(inzone)[0]
        if hb is None:
            W[idx, ib] = S[idx] * tn[idx]
            W[idx, ip] = S[idx] * (1 - tn[idx])
        else:       # parent -> helper (half angle) -> child: piecewise-linear in t
            q = tn[idx]
            W[idx, ip] = S[idx] * np.clip(1 - 2 * q, 0, 1)
            W[idx, hb] = S[idx] * (1 - np.abs(2 * q - 1))
            W[idx, ib] = S[idx] * np.clip(2 * q - 1, 0, 1)
        if R in c['smooth_roles']:
            zones |= (np.linalg.norm(d, axis=1) < c['smooth_zone'] * r)
        joints.append(dict(bone=n, role=R, r=round(r, 4), blend=round(a, 4), verts=int(len(idx))))
    stats['joints'] = joints
    W = renorm(W)

    # 3. Laplacian smoothing in the joint zones
    zi = np.where(zones)[0]
    for _ in range(c['smooth_iters']):
        Wn = W.copy()
        for i in zi:
            if nbr[i]:
                Wn[i] = (1 - c['smooth_lam']) * W[i] + c['smooth_lam'] * W[list(nbr[i])].mean(0)
        W = Wn
        W[np.ix_(neg, Lm)] = 0
        W[np.ix_(pos, Rm)] = 0
        W = renorm(W)
    stats['smoothed'] = int(len(zi))

    # 4. mirror-exact, then cap / prune / normalise
    from mathutils.kdtree import KDTree
    kd = KDTree(nc)
    for i, q in enumerate(Q):
        kd.insert(q, i)
    kd.balance()
    perm = np.array([bi.get(mirror_name(n), k) for k, n in enumerate(names)])
    mir = 0
    for i, q in enumerate(Q):
        if q[0] < -c['seam']:
            _, j, dd = kd.find((-q[0], q[1], q[2]))
            if dd < 1e-4:
                W[i] = W[j][perm]
                mir += 1
        elif abs(q[0]) <= c['seam']:
            W[i] = 0.5 * (W[i] + W[i][perm])
    W = renorm(W)
    if W.shape[1] > c['max_inf']:
        drop = np.argsort(-W, 1)[:, c['max_inf']:]
        np.put_along_axis(W, drop, 0.0, 1)
    W[W < c['prune']] = 0
    W = renorm(W)
    stats['mirrored'] = mir
    stats['max_influences'] = int((W > 0).sum(1).max())

    # write back
    for n in names:
        vg = body.vertex_groups.get(n) or body.vertex_groups.new(name=n)
        vg.remove(list(range(nv)))
    groups = {n: body.vertex_groups[n] for n in names}
    for k, n in enumerate(names):
        col = W[C, k]
        nz = np.where(col > 0)[0]
        # group by identical weight value is slow to build; add per vertex
        g = groups[n]
        for vi in nz:
            g.add([int(vi)], float(col[vi]), 'REPLACE')
    print('WEIGHTS refine', {k: v for k, v in stats.items() if k != 'joints'})
    return stats
