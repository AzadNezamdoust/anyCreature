"""Every-round checks (Blender): 18-view sphere orbit (EEVEE beauty), hero, 3/4 face close-up, and the separation
check (tail vs hind legs, fore L-R, hind L-R) measured on the rest mesh plus two low views that show the gaps.
    blender -b --factory-startup -P checks_blender.py -- <glb> <outdir>"""
import bpy, sys, os, json, math
KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'kit')
sys.path.insert(0, KIT)
sys.argv = [sys.argv[0], '--', '--jobs', 'x']           # render_glb's module-level main() is skipped below
import importlib.util
src = open(os.path.join(KIT, 'render_glb.py'), encoding='utf-8').read().replace('\nmain()\n', '\n')
RG = {'__file__': os.path.join(KIT, 'render_glb.py'), '__name__': 'render_glb'}
exec(compile(src, 'render_glb', 'exec'), RG)
import bmkit as K
from mathutils import Vector
argv = sys.orig_argv[sys.orig_argv.index('--') + 1:]
glb, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)

def d(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
V = {}
for az in range(0, 360, 45):
    V[f'h{az:03d}'] = (d(az, 0), Vector((0, 0, 1)))
V['top'] = (Vector((0, 0, 1)), Vector((0, -1, 0)))
V['bottom'] = (Vector((0, 0, -1)), Vector((0, -1, 0)))
for az in (0, 90, 180, 270):
    V[f'u{az:03d}'] = (d(az, 45), Vector((0, 0, 1)))
    V[f'l{az:03d}'] = (d(az, -45), Vector((0, 0, 1)))
V['hero'] = (Vector((1, -1, 0.5)).normalized(), Vector((0, 0, 1)))
V['sep_rear_low'] = (d(180, -8), Vector((0, 0, 1)))
V['sep_side_low'] = (d(90, -5), Vector((0, 0, 1)))
V['sep_front_low'] = (d(0, -8), Vector((0, 0, 1)))
K.VIEWS.update(V)

meshes, frame = RG['load'](glb)
RG['beauty_setup'](frame)
names = [f'h{a:03d}' for a in range(0, 360, 45)] + ['top', 'bottom'] + [f'u{a:03d}' for a in (0, 90, 180, 270)] + [f'l{a:03d}' for a in (0, 90, 180, 270)]
low = ['bottom'] + [f'l{a:03d}' for a in (0, 90, 180, 270)]
order = [v for v in names + ['hero', 'sep_rear_low', 'sep_side_low', 'sep_front_low'] if v not in low] + low
for v in order:
    if v == 'bottom':                                  # views from below: no ground plane between camera and model
        g = bpy.data.objects.get('_ground')
        if g:
            bpy.data.objects.remove(g, do_unlink=True)
    K.camera(frame, v, fill=1.1)
    K._render(os.path.join(out, f'{v}.png'), 640 if v != 'hero' else 1024)
# face 3/4 close-up
head = Vector((0.0, -0.92, 1.40))
f2 = dict(frame, centre=list(head), size=[0.5, 0.5, 0.5])
K.VIEWS['face34'] = (Vector((0.75, -1, 0.3)).normalized(), Vector((0, 0, 1)))
K.camera(f2, 'face34', fill=1.0)
K._render(os.path.join(out, 'face_34.png'), 1024)
# separation on the rest mesh (stag): each body vertex goes to its heaviest bone; limbs are their distal bones
G = {}
for o in meshes:
    if not o.name.startswith('body'):
        continue
    vg = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda x: x.weight)
        if g.weight < 0.6:
            continue
        G.setdefault(vg[g.group], []).append(o.matrix_world @ v.co)
def limb(ns):
    return [p for n in ns for p in G.get(n, [])]
from mathutils.kdtree import KDTree
def gap(A, B):
    if not A or not B:
        return -1
    kd = KDTree(len(B))
    for i, p in enumerate(B):
        kd.insert(p, i)
    kd.balance()
    return round(min(kd.find(p)[2] for p in A), 4)
res = {}
for sd in 'LR':
    res['tail_vs_hind.' + sd] = gap(limb(['tail0']), limb(['shin.' + sd, 'foot.' + sd, 'toe.' + sd]))
res['foreL_vs_foreR'] = gap(limb(['forearm.L', 'paw.L']), limb(['forearm.R', 'paw.R']))
res['hindL_vs_hindR'] = gap(limb(['shin.L', 'foot.L', 'toe.L']), limb(['shin.R', 'foot.R', 'toe.R']))
res['verdict'] = 'PASS' if min(res.values()) > 0.01 else 'FAIL'
json.dump(res, open(os.path.join(out, 'separation.json'), 'w'), indent=1)
print('SEPARATION', json.dumps(res))
