"""Every-round checks (Blender): 18-view sphere orbit (EEVEE beauty), hero, 3/4 face close-up, and the separation
check (tail vs hind legs, fore L vs fore R) measured on the rest mesh plus two low views that show the gaps.
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
head = Vector((0.0, -0.08, 0.25))
f2 = dict(frame, centre=list(head), size=[0.2, 0.2, 0.2])
K.VIEWS['face34'] = (Vector((0.75, -1, 0.25)).normalized(), Vector((0, 0, 1)))
K.camera(f2, 'face34', fill=1.0)
K._render(os.path.join(out, 'face_34.png'), 1024)
# separation on the rest mesh (octopus): the 8 arms past r 0.17 from the crown, sorted by azimuth; each neighbour pair's gap
dg = bpy.context.evaluated_depsgraph_get()
P = []
for o in meshes:
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    P += [(o.name, o.matrix_world @ v.co) for v in me.vertices]
    oe.to_mesh_clear()
body = [p for n, p in P if n.startswith('body')] or [p for n, p in P]
hub = Vector((0.0, -0.05, 0.0))
H = [0, 20, 57, 112, 155, 205, 248, 303, 340]
heads = [20, 57, 112, 155, -155, -112, -57, -20]
groups = {h: [] for h in heads}
for p in body:
    d = Vector((p.x, p.y - hub.y))
    if d.length < 0.17:
        continue
    az = math.degrees(math.atan2(p.x, -(p.y - hub.y)))
    h = min(heads, key=lambda q: abs((az - q + 180) % 360 - 180))
    groups[h].append(p)
order = sorted(heads, key=lambda q: q % 360)
def gap(A, B):
    return round(min(((a - b).length for a in A for b in B), default=-1), 4)
res = {f'arm{a}_vs_arm{b}': gap(groups[a], groups[b]) for a, b in zip(order, order[1:] + order[:1])}
res['counts'] = {str(h): len(g) for h, g in groups.items()}
res['verdict'] = 'PASS' if min(v for k, v in res.items() if k != 'counts') > 0.01 else 'FAIL'
json.dump(res, open(os.path.join(out, 'separation.json'), 'w'), indent=1)
print('SEPARATION', json.dumps(res))
