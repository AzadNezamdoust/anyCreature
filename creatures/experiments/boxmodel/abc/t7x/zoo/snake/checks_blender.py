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
import numpy as np
_PTS = np.array([tuple(o.matrix_world @ p.co) for o in bpy.data.objects if o.type == 'MESH' and o.name != '_ground'
                 for p in o.data.vertices])
def fit_camera(v, fill=0.86):
    """Frame on the model's projected extent in this view (a long flat snake is tiny on a bounding sphere)."""
    K.camera(frame, v, fill=1.1)
    cam = bpy.context.scene.camera
    d, up = K._view_dir(v)
    d = Vector(d).normalized(); r = Vector(up).cross(d).normalized(); u = d.cross(r)
    P = _PTS
    pr, pu = P @ np.array(r), P @ np.array(u)
    c = Vector(r) * (pr.max() + pr.min()) / 2 + Vector(u) * (pu.max() + pu.min()) / 2 + d * float((P @ np.array(d)).mean())
    ext = max(pr.max() - pr.min(), pu.max() - pu.min()) / fill
    depth = float((P @ np.array(d)).max() - (P @ np.array(d)).mean())
    dist = ext / 2 / math.tan(K.FOV / 2) + depth
    K._aim(cam, c + d * dist, c, up)
order = [v for v in names + ['hero'] if v not in low] + low
for v in order:
    if v == 'bottom':                                  # views from below: no ground plane between camera and model
        g = bpy.data.objects.get('_ground')
        if g:
            bpy.data.objects.remove(g, do_unlink=True)
    fit_camera(v)
    K._render(os.path.join(out, f'{v}.png'), 640 if v != 'hero' else 1024)
