"""Kit self-test: a crude box dog through all four stages, plus deliberate
violations the gates must catch. Not a creature — a test of the rules.

    py -3.11 experiments/boxmodel/kit/selftest/check.py

BMK_BREAK (env) injects one violation:
    unlogged    a stage-2 subdivide outside a topo block
    stage3edit  stage 3 moves a base vertex
    s1edit      stage 1 changes after the lock
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from bmkit import *

BREAK = os.environ.get('BMK_BREAK', '')
META = dict(creature='selftest_dog', model='kit', engine_glb='example/wolf.glb',
            stage1_tris=(60, 1500), total_tris=(60, 3000))


def hring(bm, y, cz, rx, rz, boxy=0.75):
    return ring(bm, [(0, y, cz + rz), (boxy * rx, y, cz + 0.75 * rz), (rx, y, cz),
                     (boxy * rx, y, cz - 0.75 * rz), (0, y, cz - rz)])


def stage1(k):
    bm = bmesh.new()
    spec = [(0.45, 0.60, 0.14, 0.16), (0.20, 0.62, 0.18, 0.20), (-0.10, 0.60, 0.16, 0.18),
            (-0.40, 0.63, 0.19, 0.22), (-0.58, 0.72, 0.14, 0.15), (-0.72, 0.85, 0.12, 0.12),
            (-0.90, 0.90, 0.13, 0.12), (-1.05, 0.86, 0.08, 0.07), (-1.15, 0.85 + (0.01 if BREAK == 's1edit' else 0), 0.05, 0.04)]
    rings = [hring(bm, *s) for s in spec]
    for r0, r1 in zip(rings, rings[1:]):
        bridge(bm, r0, r1)
    cap(bm, rings[0])
    cap(bm, list(reversed(rings[-1])))
    recalc_normals(bm)
    # legs: extrude the lower-side quad under the hip and under the chest, downward
    for (y0, y1), fz in (((0.45, 0.20), 0.54), ((-0.10, -0.40), 0.53)):
        f = face_near(bm, (0.145, (y0 + y1) / 2, fz))
        r = extrude(bm, [f])
        vs = r['verts']
        yc, cx = (y0 + y1) / 2, 0.12
        # place the new quad as a horizontal rectangle under the body
        xs = sorted(vs, key=lambda v: v.co.x)
        for v in xs[:2]:
            v.co.x = cx - 0.05
        for v in xs[2:]:
            v.co.x = cx + 0.05
        ys = sorted(vs, key=lambda v: v.co.y)
        for v in ys[:2]:
            v.co.y = yc - 0.06
        for v in ys[2:]:
            v.co.y = yc + 0.06
        for v in vs:
            v.co.z = 0.30
        f2 = r['faces'][0]
        r2 = extrude(bm, [f2], offset=(0, 0, -0.26))
        scale(r2['verts'], 0.8)
        r3 = extrude(bm, [r2['faces'][0]], offset=(0, -0.04, -0.03))
    recalc_normals(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'loop', 'waist loop: the belly tuck needs a ring between hip and chest'):
        e = edge_near(bm, (0.17, 0.05, 0.62))
        loopcut(bm, e, t=0.5)
    with k.topo(bm, 'loop', 'second loop at the shoulder, for the bend'):
        e = edge_near(bm, (0.17, -0.49, 0.67))
        loopcut(bm, e, t=0.4)
    rows = edge_ring(edge_near(bm, (0.11, -0.97, 0.99)))
    with k.topo(bm, 'chamfer', 'brow crease'):
        chamfer(bm, edge_near(bm, (0.10, -0.90, 1.0)), frac=0.2)
    with k.topo(bm, 'inset', 'eye socket: a loop in the face'):
        inset(bm, [face_near(bm, (0.12, -0.97, 0.93), n=(1, 0, 0))], 0.35, depth=-0.005)
    if BREAK == 'unlogged':
        bmesh.ops.subdivide_edges(bm, edges=[edge_near(bm, (0.2, 0.3, 0.6))], cuts=1)
    # a belly tuck: pull the lowest waist verts up
    for v in verts_where(bm, lambda c: abs(c.y - 0.05) < 0.02 and c.z < 0.5):
        v.co.z += 0.03
    commit(body, bm)
    apply_mirror(body)
    bm = edit(body)
    tip = vert_near(bm, (0.0, -1.15, 0.89))      # asymmetry after the mirror: nudge the nose
    tip.co.x += 0.004
    commit(body, bm)


def stage3(k, body):
    if BREAK == 'stage3edit':
        bm = edit(body); bm.verts[5].co.z += 0.01; commit(body, bm)
    paint(body, {'fur': '#7d6e60', 'back': '#4e4640', 'belly': '#d8c9a8', 'nose': '#1c1a19'},
          lambda c, n, i: 'nose' if c.y < -1.1 else 'belly' if n.z < -0.5 else 'back' if n.z > 0.7 else 'fur')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=0.04)
    for v in bm.verts:
        v.co += Vector((0.1, -0.95, 0.95))
    eye = object_from_bm('eye', bm, mirror=True)
    paint(eye, {'eye': '#f0c040'}, lambda c, n, i: 'eye')
    return [eye]


def stage4(k, body, pieces):
    rig = armature([('hips', (0, 0.3, 0.62), (0, 0.0, 0.62), None),
                    ('chest', (0, 0.0, 0.62), (0, -0.5, 0.66), 'hips', True),
                    ('neck', (0, -0.5, 0.66), (0, -0.8, 0.88), 'chest', True),
                    ('head', (0, -0.8, 0.88), (0, -1.15, 0.86), 'neck', True),
                    ('thigh.L', (0.12, 0.33, 0.5), (0.12, 0.33, 0.3), 'hips'),
                    ('shin.L', (0.12, 0.33, 0.3), (0.12, 0.29, 0.02), 'thigh.L', True),
                    ('arm.L', (0.12, -0.25, 0.5), (0.12, -0.25, 0.3), 'chest'),
                    ('fore.L', (0.12, -0.25, 0.3), (0.12, -0.29, 0.02), 'arm.L', True)])
    skin(body, rig)
    for p in pieces:
        bind(p, rig, bone='head')
    clip(rig, 'idle', {1: {}, 24: {'chest': (3, 0, 0), 'head': (-6, 0, 0)}, 48: {}})
    clip(rig, 'move', {1: {'thigh.L': (20, 0, 0), 'arm.L': (-20, 0, 0)},
                       12: {'thigh.L': (-20, 0, 0), 'arm.L': (20, 0, 0)},
                       24: {'thigh.L': (20, 0, 0), 'arm.L': (-20, 0, 0)}})
    clip(rig, 'attack', {1: {}, 8: {'neck': (-25, 0, 0), 'head': (15, 0, 0)}, 20: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
