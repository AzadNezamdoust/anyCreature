"""Diagnostic: where the junction probe's knife folds and seam strips sit (positions, angles).
    blender -b --factory-startup -P knifedump.py -- <glb>"""
import sys, os
import numpy as np
KIT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'kit'))
sys.path.insert(0, KIT)
import junctions as JN

glb = sys.argv[sys.argv.index('--') + 1]
RG = JN._render_glb()
meshes, frame = RG['load'](glb)
m = JN.Model(meshes)
J = JN.find_junctions(m)
g = m.geo[m.body.name]
trees = [g.bvh()] + [m.geo[o.name].bvh() for o in m.pieces]
for j in J:
    if j['name'].endswith('.R'):
        continue
    reg = JN.region(g, j)
    folds = JN._fold_angles(g, reg)
    ex = JN.exposure(m, g, set(int(t) for t in reg) | {t for f in folds for t in (f[3], f[4])}, trees)
    seen = lambda t: ex.get(int(t), 0) >= JN.L_['EXPOSED']
    kn = [f for f in folds if f[2] and (seen(f[3]) or seen(f[4])) and f[1] > JN.L_['KNIFE_DEG']]
    print('JUNCTION', j['name'], 'r', round(j['r'], 3), 'root', np.round(j['root'], 3))
    for e, ang, cc, t1, t2 in kn:
        a, b = g.V[e[0]], g.V[e[1]]
        print('  knife %.0f deg  len %.3f  at %s -> %s  seen %d/%d' % (ang, np.linalg.norm(a - b), np.round(a, 3), np.round(b, 3), ex.get(int(t1), 0), ex.get(int(t2), 0)))
    medw = float(np.median(np.sqrt(2 * g.A[reg])))
    creased = {}
    for e, ang, cc, t1, t2 in folds:
        if ang > JN.L_['STRIP_CREASE_DEG']:
            creased[t1] = creased[t2] = True
    thin = [int(t) for t in reg if seen(t) and g.width[t] < JN.L_['STRIP_W'] * medw
            and g.longest[t] > JN.L_['STRIP_ASPECT'] * g.width[t] and creased.get(int(t))]
    for c in JN._components(g, thin):
        P = g.V[np.unique(g.T[c])]
        ln = float(np.ptp((P - P.mean(0)) @ JN._pca1(P))) if len(P) > 2 else 0.0
        if ln > j['r']:
            print('  strip len %.3f  n %d  centre %s  bbox %s..%s' % (ln, len(c), np.round(P.mean(0), 3), np.round(P.min(0), 3), np.round(P.max(0), 3)))
