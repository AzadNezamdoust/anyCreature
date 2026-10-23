"""Snake checks (Blender): views of a GLB, optionally BENT into the plan S first (stage 1-3 GLBs are straight).
    blender -b --factory-startup -P checks_blender.py -- <glb> <outdir> [bend] [quick]"""
import bpy, sys, os, json, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(HERE, '..', '..', '..', 'kit')
sys.path.insert(0, KIT); sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], '--', '--jobs', 'x']
src = open(os.path.join(KIT, 'render_glb.py'), encoding='utf-8').read().replace('\nmain()\n', '\n')
RG = {'__file__': os.path.join(KIT, 'render_glb.py'), '__name__': 'render_glb'}
exec(compile(src, 'render_glb', 'exec'), RG)
import bmkit as K
import snake_shape as SS
from mathutils import Vector
argv = sys.orig_argv[sys.orig_argv.index('--') + 1:]
glb, out = argv[0], argv[1]
bend, quick = 'bend' in argv[2:], 'quick' in argv[2:]
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
K.VIEWS.update(V)
meshes, frame = RG['load'](glb)
if bend:
    for o in meshes:
        mw, mi = o.matrix_world.copy(), o.matrix_world.inverted()
        for v in o.data.vertices:
            v.co = mi @ Vector(SS.bend(tuple(mw @ v.co)))
        o.data.update()
    lo = [min((o.matrix_world @ v.co)[i] for o in meshes for v in o.data.vertices) for i in range(3)]
    hi = [max((o.matrix_world @ v.co)[i] for o in meshes for v in o.data.vertices) for i in range(3)]
    frame = dict(frame, centre=[(a + b) / 2 for a, b in zip(lo, hi)], size=[b - a for a, b in zip(lo, hi)])
RG['beauty_setup'](frame)
names = [f'h{a:03d}' for a in range(0, 360, 45)] + ['top', 'hero'] + ([] if quick else [f'u{a:03d}' for a in (0, 90, 180, 270)] + [f'l{a:03d}' for a in (0, 90, 180, 270)] + ['bottom'])
for v in names:
    if v in ('bottom',) or v.startswith('l'):
        g = bpy.data.objects.get('_ground')
        if g:
            bpy.data.objects.remove(g, do_unlink=True)
    K.camera(frame, v, fill=1.1)
    K._render(os.path.join(out, f'{v}.png'), 640 if v != 'hero' else 1024)
head = Vector(SS.bend((0.0, -0.45, 0.44)))
f2 = dict(frame, centre=list(head), size=[0.30, 0.30, 0.30])
K.VIEWS['face34'] = (Vector((0.75, -1, 0.25)).normalized(), Vector((0, 0, 1)))
K.camera(f2, 'face34', fill=1.0)
K._render(os.path.join(out, 'face_34.png'), 1024)
print('CHECKS done', out)
