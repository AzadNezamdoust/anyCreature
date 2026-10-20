"""ftest — functional tests for a box-model creature build.

    py -3.11 experiments/boxmodel/kit/ftest.py <build_dir> [--body quadruped|biped|bird|octopus|snake|fish|arthropod]
                                                            [--budget N]

Finds the stage-4 glb of <build_dir> (stage4/*.glb, else *.glb), re-imports it in a factory-startup
headless Blender 5.x (one process), measures it, writes <build_dir>/ftest.json and prints a
PASS/FAIL/SKIP table. Every check carries one headline number and its threshold; composite checks
list their sub-measurements. The script never changes a threshold to make a build pass.

Checks (the numbers are in metres / degrees unless stated):
  glb            glbcheck OK; re-import agrees with the file on tris, joints, clip names; bbox min z ~ 0
  weights        every skinned vertex weighted, sum 1 +- 1e-3, <= 4 influences, no NaN
  clips          idle / move / attack (swim instead of move for octopus and fish) exist with > 1 frame;
                 loop clips: first pose == last pose within 0.1 deg per bone
  joint_area     per joint (a deform bone and a deform child): the convex-hull area of the body vertices in
                 a +-r slab at the joint (projected on the plane normal to the bisector of the two bones)
                 at the clip extreme frames >= 0.7 x rest
  self_intersect body triangles that cross another body triangle (triangles sharing a vertex excluded),
                 at rest and on every 4th frame of every clip
  foot_contact   quadruped / biped / bird: rest foot lowest vertex z 0 +- 0.01, nothing below -0.01 on any
                 frame, stance slide < 0.02 in the move clip. Other bodies: nothing below -0.01 only
  eye_fit        lid ring (body vertices round the eye) to eyeball surface 0-2 mm, no penetration
  mesh           body manifold, no n-gons, tris within budget, stage-1 lock unchanged

Interpretation notes (the spec was silent):
  - "swim for octopus and fish" replaces `move` (clips needed: idle, swim, attack).
  - loop clips are idle, move, swim, walk, run, fly; attack and curl are one-shots.
  - the lock check reads stage1_lock.json and the stage-4 lock_assert.json the kit wrote (bmkit.assert_lock);
    without stage1_lock.json it SKIPs.
"""
import json, os, sys, glob, subprocess, struct, tempfile, math

try:
    import bpy                                       # inside Blender: run the measurements
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

KIT = os.path.dirname(os.path.abspath(__file__))

BODIES = ('quadruped', 'biped', 'bird', 'octopus', 'snake', 'fish', 'arthropod')
FOOT_BODIES = ('quadruped', 'biped', 'bird')
BUDGET = {'quadruped': 8000, 'octopus': 10000, 'biped': 5000, 'bird': 5000, 'snake': 5000,
          'fish': 5000, 'arthropod': 5000}
CREATURE_BODY = {}
for _b, _names in {'quadruped': 'wolf fox bear boar stag tiger horse elephant rabbit crocodile chameleon frog '
                                'sea_turtle turtle dragon',
                   'bird': 'owl eagle penguin raven_wyvern wyvern',
                   'arthropod': 'crab rhino_beetle beetle spider scorpion',
                   'octopus': 'octopus', 'fish': 'shark koi', 'snake': 'snake',
                   'biped': 'character giant goblin gorilla'}.items():
    for _n in _names.split():
        CREATURE_BODY[_n] = _b
CREATURE_BUDGET = {'dragon': 10000}
LOOPS = {'idle', 'move', 'swim', 'walk', 'run', 'fly'}

# thresholds
W_SUM_TOL = 1e-3
W_MAX_INFL = 4
LOOP_DEG = 0.1
AREA_MIN = 0.7
FOOT_REST = 0.01
BELOW = -0.01
STANCE_Z = 0.01
SLIDE = 0.02
EYE_GAP_MM = (0.0, 2.0)
BBOX_Z = 0.01


# ============================================================================ result plumbing
def sub(name, value, op, thr, unit=''):
    """One measurement against one threshold. op: le ge eq abs_le range. value None = SKIP."""
    s = dict(name=name, value=None if value is None else (round(float(value), 5) if not isinstance(value, int) else value),
             op=op, threshold=thr, unit=unit)
    if value is None:
        s['status'] = 'SKIP'
    elif op == 'le':
        s['status'] = 'PASS' if value <= thr else 'FAIL'
    elif op == 'ge':
        s['status'] = 'PASS' if value >= thr else 'FAIL'
    elif op == 'eq':
        s['status'] = 'PASS' if value == thr else 'FAIL'
    elif op == 'abs_le':
        s['status'] = 'PASS' if abs(value) <= thr else 'FAIL'
    elif op == 'range':
        s['status'] = 'PASS' if thr[0] <= value <= thr[1] else 'FAIL'
    return s


def _badness(s):
    """How close a sub is to failing (>= 1 = failing), to pick the headline of a composite."""
    v, t, op = s['value'], s['threshold'], s['op']
    if s['status'] == 'FAIL':
        return 1e9
    if v is None:
        return -1
    try:
        if op == 'le':
            return v / t if t else 0.0
        if op == 'ge':
            return t / v if v else 1e9
        if op == 'abs_le':
            return abs(v) / t if t else 0.0
        if op == 'range':
            mid, half = (t[0] + t[1]) / 2, (t[1] - t[0]) / 2
            return abs(v - mid) / half if half else 0.0
    except Exception:
        pass
    return 0.0


def check(name, subs, note=None):
    live = [s for s in subs if s['status'] != 'SKIP']
    if not live:
        st = 'SKIP'
    else:
        st = 'FAIL' if any(s['status'] == 'FAIL' for s in live) else 'PASS'
    head = max(live, key=_badness) if live else (subs[0] if subs else None)
    c = dict(name=name, status=st, value=head['value'] if head else None,
             threshold=head['threshold'] if head else None, op=head['op'] if head else None,
             unit=head['unit'] if head else '', measured=head['name'] if head else '', subs=subs)
    if note:
        c['note'] = note
    return c


def errcheck(name, e):
    return dict(name=name, status='FAIL', value=None, threshold=None, op=None, unit='', measured='crashed',
                subs=[], note='%s: %s' % (type(e).__name__, str(e).splitlines()[0][:160] if str(e) else ''))


def fmt_thr(op, t, unit):
    u = (' ' + unit) if unit else ''
    if op == 'range':
        return '%g..%g%s' % (t[0], t[1], u)
    sym = {'le': '<=', 'ge': '>=', 'eq': '==', 'abs_le': '|x|<='}[op]
    return '%s %g%s' % (sym, t, u)


def fmt_val(v):
    if v is None:
        return '-'
    if isinstance(v, int):
        return str(v)
    return '%.4g' % v


# ============================================================================ driver (system Python)
def read_glb_json(path):
    with open(path, 'rb') as f:
        magic, ver, ln = struct.unpack('<4sII', f.read(12))
        clen, ctype = struct.unpack('<II', f.read(8))
        return json.loads(f.read(clen).decode('utf-8'))


def glb_facts(path):
    j = read_glb_json(path)
    acc = j.get('accessors', [])
    tris = 0
    for n in j.get('nodes', []):
        if 'mesh' not in n:
            continue
        for p in j['meshes'][n['mesh']]['primitives']:
            if p.get('mode', 4) != 4:
                continue
            a = acc[p['indices']] if 'indices' in p else acc[p['attributes']['POSITION']]
            tris += a['count'] // 3
    joints = set()
    for s in j.get('skins', []):
        joints |= set(s.get('joints', []))
    modes = sorted({p.get('mode', 4) for m in j.get('meshes', []) for p in m['primitives']})
    return dict(tris=tris, joints=len(joints), actions=sorted(a.get('name', '') for a in j.get('animations', [])),
                prim_modes=modes)


def blender_exe():
    if os.environ.get('BLENDER'):
        return os.environ['BLENDER']
    import shutil
    found = sorted(glob.glob(os.path.join(os.environ.get('ProgramFiles', ''), 'Blender*', 'Blender 5*', 'blender.exe')))
    return found[-1] if found else (shutil.which('blender') or 'blender')


def find_glb(cdir):
    for pat in (os.path.join(cdir, 'stage4', '*.glb'), os.path.join(cdir, '*.glb')):
        g = sorted(glob.glob(pat))
        if g:
            name = os.path.basename(os.path.normpath(cdir)) + '.glb'
            return next((x for x in g if os.path.basename(x) == name), g[0])
    return None


def run_glbcheck(glb):
    sys.path.insert(0, KIT)
    import run as kitrun
    out = os.path.join(tempfile.mkdtemp(), 'glbcheck.txt')
    rc, tail = kitrun.glbcheck(glb, out)
    errs = [l for l in open(out, encoding='utf-8').read().splitlines() if l.startswith('FAIL')]
    return rc, len(errs), tail[-1] if tail else ''


def driver():
    import argparse
    ap = argparse.ArgumentParser(description='functional tests for a box-model creature build')
    ap.add_argument('build_dir')
    ap.add_argument('--body', choices=BODIES)
    ap.add_argument('--budget', type=int)
    a = ap.parse_args()
    cdir = os.path.abspath(a.build_dir)
    name = os.path.basename(os.path.normpath(cdir))
    glb = find_glb(cdir)
    if not glb:
        print('no glb under', a.build_dir)
        return 2
    body = a.body or CREATURE_BODY.get(name, 'quadruped')
    budget = a.budget or CREATURE_BUDGET.get(name) or BUDGET[body]
    rc, nerr, last = run_glbcheck(glb)
    pre = dict(glb=os.path.relpath(glb, cdir).replace('\\', '/'), body=body, budget=budget,
               glbcheck=dict(rc=rc, errors=nerr, last=last), facts=glb_facts(glb), name=name)
    lock = {}
    for k, fn in (('lock', 'stage1_lock.json'), ('assert', 'lock_assert.json')):
        p = os.path.join(cdir, fn)
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            lock[k] = {x: d.get(x) for x in ('edge_hash', 'lock_edge_hash', 'collapsed_edge_hash', 'verdict', 'errors', 'tris')}
    pre['lock'] = lock
    tmp = tempfile.mkdtemp()
    pj, oj = os.path.join(tmp, 'pre.json'), os.path.join(tmp, 'out.json')
    json.dump(pre, open(pj, 'w'))
    cmd = [blender_exe(), '-b', '--factory-startup', '--python-exit-code', '3', '-P', os.path.abspath(__file__),
           '--', '--glb', glb, '--pre', pj, '--out', oj]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if not os.path.exists(oj):
        tail = '\n'.join((p.stdout + p.stderr).splitlines()[-25:])
        print('Blender produced no result (rc=%s)\n%s' % (p.returncode, tail))
        return 3
    res = json.load(open(oj, encoding='utf-8'))
    summ = {s: sum(1 for c in res['checks'] if c['status'] == s) for s in ('PASS', 'FAIL', 'SKIP')}
    res['summary'] = summ
    outp = os.path.join(cdir, 'ftest.json')
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1)
        f.write('\n')
    print_table(res)
    return 0 if summ['FAIL'] == 0 else 1


def print_table(res):
    print('ftest  %s  body=%s  tri budget=%s  glb=%s' % (res['name'], res['body'], res['budget'], res['glb']))
    W = 15
    print('%-*s %-5s %-12s %-16s %s' % (W, 'check', '', 'value', 'threshold', 'measured'))
    print('-' * 78)
    for c in res['checks']:
        thr = fmt_thr(c['op'], c['threshold'], c['unit']) if c['op'] else '-'
        print('%-*s %-5s %-12s %-16s %s' % (W, c['name'], c['status'], fmt_val(c['value']), thr, c['measured']))
        if c.get('note'):
            print('%-*s       note: %s' % (W, '', c['note']))
        for s in c['subs']:
            print('%-*s   %-5s %-12s %-16s %s' % (W, '', s['status'], fmt_val(s['value']),
                                                  fmt_thr(s['op'], s['threshold'], s['unit']), s['name']))
    print('-' * 78)
    print('PASS %(PASS)d  FAIL %(FAIL)d  SKIP %(SKIP)d' % res['summary'])


# ============================================================================ measurements (inside Blender)
if IN_BLENDER:
    import numpy as np
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    class Scene:
        """The re-imported glb and every pose sampled once: world vertices of every skinned mesh, the
        world head / tail / local rotation of every bone, at rest and on every frame of every clip."""

        def __init__(self, glb):
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=glb)
            objs = list(bpy.data.objects)
            self.rig = next((o for o in objs if o.type == 'ARMATURE'), None)
            meshes = [o for o in objs if o.type == 'MESH' and (any(m.type == 'ARMATURE' for m in o.modifiers)
                                                              or (self.rig and o.parent is self.rig))]
            if not meshes:                  # an unskinned export: every mesh except the importer's bone shape
                meshes = [o for o in objs if o.type == 'MESH' and not o.name.startswith('Icosphere')]
            self.meshes = meshes
            self.body = next((o for o in meshes if o.name.lower() == 'body'),
                             max(meshes, key=lambda o: len(o.data.vertices)))
            self.bones = list(self.rig.data.bones) if self.rig else []
            self.bidx = {b.name: i for i, b in enumerate(self.bones)}
            self.deform = [b.use_deform for b in self.bones]
            self.actions = {a.name: a for a in bpy.data.actions}
            self.tris = {o.name: self._tris(o) for o in meshes}
            self.W = {}                     # per mesh (nv, nbones) deform-bone weights
            self.rest = self.pose_rest()
            self.clips = {}
            for n, a in sorted(self.actions.items()):
                self.clips[n] = self.sample_clip(a)

        # ----------------------------------------------------------- geometry
        @staticmethod
        def _tris(o):
            me = o.data
            me.calc_loop_triangles()
            a = np.empty(len(me.loop_triangles) * 3, np.int64)
            me.loop_triangles.foreach_get('vertices', a)
            return a.reshape(-1, 3)

        def verts(self, o):
            dg = bpy.context.evaluated_depsgraph_get()
            oe = o.evaluated_get(dg)
            me = oe.to_mesh()
            a = np.empty(len(me.vertices) * 3, np.float32)
            me.vertices.foreach_get('co', a)
            oe.to_mesh_clear()
            M = np.array(oe.matrix_world, dtype=np.float64)
            return a.reshape(-1, 3).astype(np.float64) @ M[:3, :3].T + M[:3, 3]

        def snap(self):
            bpy.context.view_layer.update()
            M = np.array(self.rig.matrix_world, dtype=np.float64) if self.rig else np.eye(4)
            n = len(self.bones)
            head, tail, quat = np.zeros((n, 3)), np.zeros((n, 3)), np.zeros((n, 4))
            if self.rig:
                for i, b in enumerate(self.bones):
                    pb = self.rig.pose.bones[b.name]
                    head[i] = M[:3, :3] @ np.array(pb.head) + M[:3, 3]
                    tail[i] = M[:3, :3] @ np.array(pb.tail) + M[:3, 3]
                    quat[i] = pb.matrix_basis.to_quaternion()
            return dict(verts={o.name: self.verts(o) for o in self.meshes}, head=head, tail=tail, quat=quat)

        def zero_pose(self):
            for b in self.rig.pose.bones:
                b.location = (0, 0, 0); b.scale = (1, 1, 1)
                b.rotation_quaternion = (1, 0, 0, 0); b.rotation_euler = (0, 0, 0)
                b.rotation_axis_angle = (0, 0, 1, 0)

        def pose_rest(self):
            if self.rig is None:
                return self.snap()
            if self.rig.animation_data:
                self.rig.animation_data.action = None
            self.zero_pose()
            bpy.context.scene.frame_set(1)
            s = self.snap()
            # vertex weights (needs the bone index map)
            for o in self.meshes:
                g = {x.index: x.name for x in o.vertex_groups}
                W = np.zeros((len(o.data.vertices), max(1, len(self.bones))))
                for v in o.data.vertices:
                    for x in v.groups:
                        j = self.bidx.get(g.get(x.group))
                        if j is not None:
                            W[v.index, j] += x.weight
                self.W[o.name] = W
            return s

        def sample_clip(self, act):
            ad = self.rig.animation_data or self.rig.animation_data_create()
            self.zero_pose()
            ad.action = act
            if getattr(ad, 'action_slot', 1) is None and len(getattr(act, 'slots', [])):
                ad.action_slot = act.slots[0]
            a, b = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
            fr = {}
            for f in range(a, b + 1):
                bpy.context.scene.frame_set(f)
                fr[f] = self.snap()
            ad.action = None
            self.zero_pose()
            return dict(range=(a, b), frames=fr)

    def qangle(q0, q1):
        d = np.abs((q0 * q1).sum(-1)).clip(0, 1)
        return np.degrees(2 * np.arccos(d))

    def hull_area(P):
        pts = sorted(set(map(tuple, np.round(P, 9).tolist())))
        if len(pts) < 3:
            return 0.0

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lo, up = [], []
        for p in pts:
            while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
                lo.pop()
            lo.append(p)
        for p in reversed(pts):
            while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
                up.pop()
            up.append(p)
        h = lo[:-1] + up[:-1]
        return abs(sum(h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1] for i in range(len(h)))) / 2

    def section_area(V, c, n):
        a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
        u = np.cross(n, a); u /= np.linalg.norm(u)
        v = np.cross(n, u)
        d = V - c
        return hull_area(np.stack([d @ u, d @ v], 1))

    def canon_ids(V, tol=1e-5):
        """Weld by position (the glb importer splits vertices at hard edges / material seams): id per vertex."""
        from mathutils.kdtree import KDTree
        kd = KDTree(len(V))
        for i, v in enumerate(V):
            kd.insert(Vector(v.tolist()), i)
        kd.balance()
        ids = -np.ones(len(V), np.int64)
        for i, v in enumerate(V):
            if ids[i] >= 0:
                continue
            for _, j, _ in kd.find_range(Vector(v.tolist()), tol):
                if ids[j] < 0:
                    ids[j] = i
        return ids

    # ------------------------------------------------------------------ checks
    def c_glb(S, pre):
        subs = [sub('glbcheck errors', max(pre['glbcheck']['errors'], int(pre['glbcheck']['rc'] != 0)), 'eq', 0)]
        f = pre['facts']
        tri_bl = int(sum(len(t) for t in S.tris.values()))
        subs.append(sub('tris: |file - reimport|', abs(f['tris'] - tri_bl), 'eq', 0))
        subs.append(sub('joints: |file - reimport|', abs(f['joints'] - len(S.bones)), 'eq', 0))
        a1, a2 = set(f['actions']), set(S.actions)
        subs.append(sub('clip names mismatched', len(a1 ^ a2), 'eq', 0))
        zmin = min(float(v[:, 2].min()) for v in S.rest['verts'].values())
        subs.append(sub('bbox min z at rest', zmin, 'abs_le', BBOX_Z, 'm'))
        note = '%d tris, %d joints, clips %s' % (tri_bl, len(S.bones), '/'.join(sorted(S.actions)))
        return check('glb', subs, note)

    def c_weights(S, pre):
        nan = bad_sum = over = unw = 0
        worst_sum = 0.0
        maxinf = 0
        for o in S.meshes:
            g = {x.index: x.name for x in o.vertex_groups}
            for v in o.data.vertices:
                ws = [x.weight for x in v.groups if x.weight > 1e-9 and g.get(x.group) in S.bidx and S.deform[S.bidx[g[x.group]]]]
                if any(w != w for w in (x.weight for x in v.groups)):
                    nan += 1
                    continue
                s = sum(ws)
                if not ws or s <= 1e-6:
                    unw += 1
                else:
                    worst_sum = max(worst_sum, abs(s - 1))
                    bad_sum += abs(s - 1) > W_SUM_TOL
                    maxinf = max(maxinf, len(ws))
                    over += len(ws) > W_MAX_INFL
        subs = [sub('unweighted vertices', unw, 'eq', 0), sub('max |sum - 1|', worst_sum, 'le', W_SUM_TOL),
                sub('vertices over 4 influences', over, 'eq', 0), sub('NaN weights', nan, 'eq', 0)]
        return check('weights', subs, 'max influences %d' % maxinf)

    def required_clips(body):
        return ['idle', 'swim' if body in ('octopus', 'fish') else 'move', 'attack']

    def c_clips(S, pre):
        need = required_clips(pre['body'])
        low = {n.lower(): n for n in S.clips}
        miss = [n for n in need if n not in low]
        frames = [S.clips[low[n]]['range'][1] - S.clips[low[n]]['range'][0] + 1 for n in need if n in low]
        subs = [sub('required clips missing', len(miss), 'eq', 0),
                sub('min frames of a required clip', min(frames) if frames else 0, 'ge', 2)]
        worst, who = 0.0, ''
        for n, c in S.clips.items():
            if n.lower() not in LOOPS:
                continue
            fr = c['frames']
            a, b = c['range']
            d = float(qangle(fr[a]['quat'], fr[b]['quat']).max()) if b > a else 0.0
            if d >= worst:
                worst, who = d, n
        loops = [n for n in S.clips if n.lower() in LOOPS]
        subs.append(sub('loop clip first vs last pose' + (' (%s)' % who if who else ''), worst if loops else None,
                        'le', LOOP_DEG, 'deg'))
        motion = {n: round(float(max(qangle(c['frames'][c['range'][0]]['quat'], f['quat']).max() for f in c['frames'].values())), 1)
                  for n, c in S.clips.items()}
        return check('clips', subs, 'need %s, missing %s; max bone rotation per clip (deg) %s'
                     % ('/'.join(need), '/'.join(miss) or 'none', motion))

    def c_joint_area(S, pre):
        body = S.body.name
        Wb = S.W[body]
        Vr = S.rest['verts'][body]
        H, T = S.rest['head'], S.rest['tail']
        L = np.linalg.norm(T - H, axis=1)
        joints = []
        for c, b in enumerate(S.bones):
            p = S.bidx.get(b.parent.name) if b.parent else None
            if p is None or not (S.deform[p] and S.deform[c]):
                continue
            joints.append((p, c))

        def axis(snap, p, c):
            dp = snap['tail'][p] - snap['head'][p]
            dc = snap['tail'][c] - snap['head'][c]
            dp /= max(np.linalg.norm(dp), 1e-12)
            dc /= max(np.linalg.norm(dc), 1e-12)
            n = dp + dc
            return n / np.linalg.norm(n) if np.linalg.norm(n) > 1e-6 else dp

        use, A0 = {}, {}
        for p, c in joints:
            n = axis(S.rest, p, c)
            r = 0.25 * min(L[p], L[c])
            m = (np.abs((Vr - H[c]) @ n) <= r) & (Wb[:, p] + Wb[:, c] >= 0.3)
            if m.sum() < 8:
                continue
            a0 = section_area(Vr[m], H[c], n)
            if a0 < 1e-9:
                continue
            use[(p, c)] = m
            A0[(p, c)] = a0
        worst, who, nj, ev = 1e9, '', len(use), 0
        for clip, cd in S.clips.items():
            fr = cd['frames']
            fs = sorted(fr)
            ang = np.stack([qangle(fr[fs[0]]['quat'], fr[f]['quat']) for f in fs])      # (frames, bones)
            ext = {i: fs[int(ang[:, i].argmax())] for i in range(len(S.bones))}
            for (p, c), m in use.items():
                for f in {ext[p], ext[c]}:
                    sn = fr[f]
                    n = axis(sn, p, c)
                    a = section_area(sn['verts'][body][m], sn['head'][c], n)
                    ev += 1
                    ratio = a / A0[(p, c)]
                    if ratio < worst:
                        worst, who = ratio, '%s/%s %s f%d' % (S.bones[p].name, S.bones[c].name, clip, f)
        if not use or worst == 1e9:
            return check('joint_area', [sub('min section area / rest', None, 'ge', AREA_MIN)],
                         'no testable joint (%d joints, none with >= 8 slab vertices) or no clips' % len(joints))
        return check('joint_area', [sub('min section area / rest', worst, 'ge', AREA_MIN)],
                     'worst %s; %d joints tested of %d, %d evaluations' % (who, nj, len(joints), ev))

    def c_self_intersect(S, pre):
        o = S.body
        tri = S.tris[o.name]
        inv = canon_ids(S.rest['verts'][o.name])
        tc = inv[tri]
        tris = tri.tolist()

        def hits(V):
            tree = BVHTree.FromPolygons([tuple(v) for v in V.tolist()], tris, all_triangles=True)
            pr = np.array([(i, j) for i, j in tree.overlap(tree) if i < j], dtype=np.int64).reshape(-1, 2)
            if not len(pr):
                return 0
            a, b = tc[pr[:, 0]], tc[pr[:, 1]]
            share = (a[:, :, None] == b[:, None, :]).any((1, 2))
            return int((~share).sum())

        worst, where, frames = hits(S.rest['verts'][o.name]), 'rest', 1
        for clip, cd in S.clips.items():
            for k, f in enumerate(sorted(cd['frames'])):
                if k % 4:
                    continue
                frames += 1
                h = hits(cd['frames'][f]['verts'][o.name])
                if h > worst:
                    worst, where = h, '%s f%d' % (clip, f)
        return check('self_intersect', [sub('crossing triangle pairs, worst frame', worst, 'eq', 0)],
                     'worst at %s, %d frames, %d body tris' % (where, frames, len(tri)))

    FOOT_RE = ('paw', 'foot', 'toe', 'hoof', 'talon', 'claw')

    def foot_groups(S):
        isf = [any(k in b.name.lower() for k in FOOT_RE) and S.deform[i] for i, b in enumerate(S.bones)]
        groups = {}
        for i, b in enumerate(S.bones):
            if isf[i] and not (b.parent and isf[S.bidx[b.parent.name]]):
                members = [i]
                st = [i]
                while st:
                    x = st.pop()
                    for ch in S.bones[x].children:
                        j = S.bidx[ch.name]
                        if isf[j]:
                            members.append(j); st.append(j)
                groups[b.name] = members
        return groups

    def c_foot_contact(S, pre):
        body = pre['body']
        allz = [float(v[:, 2].min()) for v in S.rest['verts'].values()]
        low, lowat = min(allz), 'rest'
        for cn, cd in S.clips.items():
            for f, sn in cd['frames'].items():
                z = min(float(v[:, 2].min()) for v in sn['verts'].values())
                allz.append(z)
                if z < low:
                    low, lowat = z, '%s f%d' % (cn, f)
        lowname = 'lowest vertex over all frames (%s)' % lowat
        subs = []
        note = None
        if body in FOOT_BODIES:
            groups = foot_groups(S)
            gv = {}
            for g, mem in groups.items():
                gv[g] = {o.name: S.W[o.name][:, mem].sum(1) >= 0.5 for o in S.meshes}
            subs.append(sub('foot groups found', len(groups), 'ge', 2 if body != 'quadruped' else 4))
            rest_off = 0.0
            for g in groups:
                zs = [float(S.rest['verts'][n][m, 2].min()) for n, m in gv[g].items() if m.any()]
                if zs:
                    rest_off = max(rest_off, abs(min(zs)))
            subs.append(sub('rest: worst foot lowest-vertex |z|', rest_off if groups else None, 'le', FOOT_REST, 'm'))
            subs.append(sub(lowname, min(allz), 'ge', BELOW, 'm'))
            mv = next((n for n in S.clips if n.lower() == 'move'), None) or \
                next((n for n in S.clips if n.lower() in ('walk', 'run')), None)
            slide, who = None, ''
            if mv and groups:
                cd = S.clips[mv]
                fs = sorted(cd['frames'])
                for g in groups:
                    zmin, pos = [], []
                    for f in fs:
                        best = (1e9, None)
                        for n, m in gv[g].items():
                            if not m.any():
                                continue
                            V = cd['frames'][f]['verts'][n][m]
                            k = int(V[:, 2].argmin())
                            if V[k, 2] < best[0]:
                                best = (float(V[k, 2]), None)
                        zmin.append(best[0])
                    st = [z < STANCE_Z for z in zmin]
                    runs, i = [], 0
                    while i < len(fs):
                        if st[i]:
                            j = i
                            while j + 1 < len(fs) and st[j + 1]:
                                j += 1
                            runs.append(list(range(i, j + 1)))
                            i = j + 1
                        else:
                            i += 1
                    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(fs) - 1 and mv.lower() in LOOPS:
                        runs = [runs[-1] + runs[0]] + runs[1:-1]
                    for run in runs:
                        mid = run[len(run) // 2]
                        # the vertex lowest at mid-stance, followed through the span
                        pick = None
                        for n, m in gv[g].items():
                            if not m.any():
                                continue
                            idx = np.where(m)[0]
                            V = cd['frames'][fs[mid]]['verts'][n][idx]
                            k = int(V[:, 2].argmin())
                            if pick is None or V[k, 2] < pick[0]:
                                pick = (float(V[k, 2]), n, int(idx[k]))
                        xy = np.array([cd['frames'][fs[i]]['verts'][pick[1]][pick[2], :2] for i in run])
                        d = float(np.linalg.norm(xy[:, None] - xy[None], axis=2).max()) if len(run) > 1 else 0.0
                        if slide is None or d > slide:
                            slide, who = d, '%s frames %d-%d' % (g, fs[run[0]], fs[run[-1]])
            subs.append(sub('stance slide in move clip' + (' (%s)' % who if who else ''),
                            slide, 'le', SLIDE, 'm'))
            if mv:
                fs_ = sorted(S.clips[mv]['frames'])
                root = next((i for i, b in enumerate(S.bones) if b.parent is None), 0)
                tr = float(np.linalg.norm(S.clips[mv]['frames'][fs_[-1]]['head'][root] - S.clips[mv]['frames'][fs_[0]]['head'][root]))
                note = 'root bone %s travels %.3f m from first to last frame of %s' % (S.bones[root].name, tr, mv)
            if slide is None:
                note = 'no stance span in the move clip (no move clip, or no foot reaches z < 0.01)' if groups else \
                    'no foot bones matched %s' % '/'.join(FOOT_RE)
        else:
            subs.append(sub(lowname, min(allz), 'ge', BELOW, 'm'))
        return check('foot_contact', subs, note)

    def c_eye_fit(S, pre):
        eyes = [o for o in S.meshes if 'eye' in o.name.lower()]
        if not eyes:
            eyes = [o for o in S.meshes if any(s.material and 'eye' in s.material.name.lower() for s in o.material_slots)]
        eyes = [o for o in eyes if o is not S.body]
        if not eyes:
            return check('eye_fit', [sub('lid ring to eyeball gap', None, 'range', EYE_GAP_MM, 'mm')],
                         'no object or material named *eye*')
        Vb = S.rest['verts'][S.body.name]
        gaps, pens = [], []
        for o in eyes:
            V, tri = S.rest['verts'][o.name], S.tris[o.name]
            inv = canon_ids(V)
            parent = list(range(inv.max() + 1))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            for t in inv[tri]:
                parent[find(t[1])] = find(t[0]); parent[find(t[2])] = find(t[0])
            comp = np.array([find(i) for i in inv])
            for root in sorted(set(comp.tolist())):
                tm = np.array([comp[t[0]] == root for t in tri])
                if tm.sum() < 8:
                    continue
                vs = np.unique(tri[tm])
                cen = V[vs].mean(0)
                R = float(np.linalg.norm(V[vs] - cen, axis=1).max())
                tree = BVHTree.FromPolygons([tuple(v) for v in V.tolist()], tri[tm].tolist(), all_triangles=True)
                near = np.where(np.linalg.norm(Vb - cen, axis=1) <= 3 * R)[0]
                if not len(near):
                    near = np.array([int(np.linalg.norm(Vb - cen, axis=1).argmin())])
                best_gap, best_pen = 1e9, 0.0
                for i in near:
                    p = Vector(Vb[i].tolist())
                    loc, nrm, _, d = tree.find_nearest(p)
                    s = d if (p - loc).dot(nrm) >= 0 else -d
                    if s < 0:
                        best_pen = min(best_pen, s)
                    elif s < best_gap:
                        best_gap = s
                gaps.append((best_gap * 1000, o.name))
                pens.append(best_pen * 1000)
        if not gaps:
            return check('eye_fit', [sub('lid ring to eyeball gap', None, 'range', EYE_GAP_MM, 'mm')], 'no eyeball shell found')
        gmax = max(g for g, _ in gaps)
        subs = [sub('worst lid-ring gap', gmax, 'range', EYE_GAP_MM, 'mm'),
                sub('deepest body vertex inside an eyeball', -min(pens), 'le', 0.0, 'mm')]
        return check('eye_fit', subs, '%d eyeball shells (%s)' % (len(gaps), ', '.join(sorted({n for _, n in gaps}))))

    def c_mesh(S, pre):
        bm = bmesh.new()
        me = S.body.data
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bad = sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
        ngon = sum(1 for o in S.meshes for p in o.data.polygons if p.loop_total > 3)
        ngon += sum(1 for m in pre['facts']['prim_modes'] if m != 4)
        tris = int(sum(len(t) for t in S.tris.values()))
        subs = [sub('body non-manifold edges (welded)', bad, 'eq', 0), sub('n-gons / non-triangle primitives', ngon, 'eq', 0),
                sub('triangles (budget)', tris, 'le', pre['budget'])]
        lk = pre.get('lock', {})
        if 'lock' in lk:
            h = lk['lock']['edge_hash']
            a = lk.get('assert')
            if a is None:
                subs.append(sub('lock: lock_assert.json missing (1 = not verified)', 1, 'eq', 0))
            else:
                ok = a.get('verdict') == 'PASS' and a.get('collapsed_edge_hash') == h and a.get('lock_edge_hash') == h
                subs.append(sub('lock edge hash changed (0 = unchanged)', 0 if ok else 1, 'eq', 0))
        else:
            subs.append(sub('lock edge hash changed', None, 'eq', 0))
        return check('mesh', subs, 'body %d tris' % len(S.tris[S.body.name]))

    def inner():
        a = sys.argv[sys.argv.index('--') + 1:]
        g = lambda k: a[a.index(k) + 1]
        pre = json.load(open(g('--pre'), encoding='utf-8'))
        S = Scene(g('--glb'))
        out = []
        for fn in (c_glb, c_weights, c_clips, c_joint_area, c_self_intersect, c_foot_contact, c_eye_fit, c_mesh):
            try:
                out.append(fn(S, pre))
            except Exception as e:                                       # noqa: BLE001 - reported as FAIL
                import traceback
                traceback.print_exc()
                out.append(errcheck(fn.__name__[2:], e))
        res = dict(name=pre['name'], body=pre['body'], budget=pre['budget'], glb=pre['glb'], checks=out)
        json.dump(res, open(g('--out'), 'w', encoding='utf-8'))


if __name__ == '__main__':
    if IN_BLENDER:
        inner()
    else:
        sys.exit(driver())
