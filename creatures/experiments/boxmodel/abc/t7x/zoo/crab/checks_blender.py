"""Every-round checks (Blender): 18-view sphere orbit (EEVEE beauty), hero, 3/4 face close-up, and the separation
check (neighbouring legs and claws) measured on the rest mesh plus two low views that show the gaps.
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
head = Vector((0.0, -0.11, 0.2))
f2 = dict(frame, centre=list(head), size=[0.2, 0.2, 0.2])
K.VIEWS['face34'] = (Vector((0.75, -1, 0.35)).normalized(), Vector((0, 0, 1)))
K.camera(f2, 'face34', fill=1.0)
K._render(os.path.join(out, 'face_34.png'), 1024)
# separation on the rest mesh (crab): every body vertex goes to its heaviest bone; each limb is its distal bones
# (legs: segments b and c; claw: carpus, palm, finger; the movable finger alone); gaps between neighbouring limbs
dg = bpy.context.evaluated_depsgraph_get()
G = {}
for o in meshes:
    if not o.name.startswith('body'):
        continue
    names = {g.index: g.name for g in o.vertex_groups}
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    src_me = o.data
    for v in src_me.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda x: x.weight)
        G.setdefault(names[g.group], []).append(o.matrix_world @ me.vertices[v.index].co)
    oe.to_mesh_clear()
def limb(names):
    return [p for n in names for p in G.get(n, [])]
L = {}
for sd in 'LR':
    for n in range(1, 5):
        L[f'leg{n}.{sd}'] = limb([f'leg{n}b.{sd}', f'leg{n}c.{sd}'])
    L[f'claw.{sd}'] = limb([f'carpus.{sd}', f'palm.{sd}', f'finger.{sd}'])
    L[f'dactyl.{sd}'] = limb([f'dactyl.{sd}'])
def gap(A, B):
    return round(min(((a - b).length for a in A for b in B), default=-1), 4)
res = {}
for sd in 'LR':
    seq = [f'claw.{sd}', f'leg1.{sd}', f'leg2.{sd}', f'leg3.{sd}', f'leg4.{sd}']
    for a, b in zip(seq, seq[1:]):
        res[f'{a}_vs_{b}'] = gap(L[a], L[b])
    # the fixed finger is the palm shell past the palm front (y < -0.206); the movable finger past its root (y < -0.215) (fix pass: claw moved)
    res[f'dactyl.{sd}_vs_fixed_finger.{sd}'] = gap([p for p in L[f'dactyl.{sd}'] if p.y < -0.247], [p for p in G.get(f'palm.{sd}', []) if p.y < -0.238])
res['claw.L_vs_claw.R'] = gap(L['claw.L'], L['claw.R'])
res['counts'] = {k: len(v) for k, v in L.items()}
res['verdict'] = 'PASS' if min(v for k, v in res.items() if k != 'counts') > 0.01 else 'FAIL'
json.dump(res, open(os.path.join(out, 'separation.json'), 'w'), indent=1)
print('SEPARATION', json.dumps(res))
