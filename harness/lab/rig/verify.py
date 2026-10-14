"""Pose a rigged GLB with numpy LBS at given times, write OBJs, plus a joint-overlay plot.
    python verify.py out/wolf_rigged.glb anim t1 t2 ...
"""
import sys, json, struct, numpy as np, os
def glb(path):
    b = open(path, 'rb').read(); jl = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + jl]); bin_ = b[20 + jl + 8:]
    def acc(i):
        a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        return np.frombuffer(bin_, dt, a['count'] * n, bv.get('byteOffset', 0)).reshape(a['count'], n)
    return g, acc
def qm(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def pose(path, anim, t):
    g, acc = glb(path)
    pr = g['meshes'][0]['primitives'][0]; at = pr['attributes']
    V = acc(at['POSITION']).astype(float); Jn = acc(at['JOINTS_0']); Wt = acc(at['WEIGHTS_0'])
    I = acc(pr['indices']).reshape(-1, 3)
    skin = g['skins'][0]; joints = skin['joints']; ibm = acc(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    nodes = g['nodes']; par = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
    loc = {i: [np.array(n.get('translation', [0, 0, 0]), float), np.array(n.get('rotation', [0, 0, 0, 1]), float)] for i, n in enumerate(nodes)}
    if anim:
        a = [x for x in g['animations'] if x['name'] == anim][0]
        for ch in a['channels']:
            s = a['samplers'][ch['sampler']]; ti = acc(s['input'])[:, 0]; vo = acc(s['output'])
            tt = t * ti[-1]; k = min(np.searchsorted(ti, tt, 'right') - 1, len(ti) - 2); f = (tt - ti[k]) / (ti[k + 1] - ti[k])
            v = vo[k] * (1 - f) + vo[k + 1] * f
            if ch['target']['path'] == 'rotation': v = v / np.linalg.norm(v)
            loc[ch['target']['node']][0 if ch['target']['path'] == 'translation' else 1] = v
    W = {}
    def world(i):
        if i in W: return W[i]
        M = np.eye(4); M[:3, :3] = qm(loc[i][1]); M[:3, 3] = loc[i][0]
        W[i] = world(par[i]) @ M if i in par else M; return W[i]
    S = np.array([world(j) @ ibm[k] for k, j in enumerate(joints)])
    Vh = np.c_[V, np.ones(len(V))]
    P = np.einsum('vk,vkij,vj->vi', Wt, S[Jn], Vh)[:, :3]
    Jw = np.array([world(j)[:3, 3] for j in joints])
    return P, I, Jw, [nodes[j]['name'] for j in joints], [joints.index(par[j]) if par.get(j) in joints else -1 for j in joints]
def write_obj(p, P, I):
    with open(p, 'w') as f:
        f.writelines('v %.5f %.5f %.5f\n' % tuple(v) for v in P)
        f.writelines('f %d %d %d\n' % tuple(t + 1) for t in I)
if __name__ == '__main__':
    path, anim = sys.argv[1], sys.argv[2]
    base = os.path.splitext(path)[0]
    for t in map(float, sys.argv[3:]):
        P, I, Jw, nm, pa = pose(path, None if anim == 'rest' else anim, t)
        write_obj('%s_%s_%.2f.obj' % (base, anim, t), P, I)
        # minimum edge length ratio vs rest (collapse detector)
        R = pose(path, None, 0)[0]
        e = np.r_[I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]
        r = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1) / np.maximum(np.linalg.norm(R[e[:, 0]] - R[e[:, 1]], axis=1), 1e-9)
        print(anim, t, 'edge stretch min %.2f max %.2f  minY %.3f' % (r.min(), r.max(), P[:, 1].min()))
        if anim == 'rest':
            import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(16, 6))
            for a_, (u, v) in zip(ax, ((2, 1), (0, 1))):
                a_.scatter(P[:, u], P[:, v], s=1, c='0.8'); a_.set_aspect('equal')
                for k, p in enumerate(pa):
                    if p >= 0: a_.plot(Jw[[p, k], u], Jw[[p, k], v], 'r-')
                a_.scatter(Jw[:, u], Jw[:, v], s=12, c='b')
            for k, n in enumerate(nm): ax[0].annotate(n, Jw[k, [2, 1]], fontsize=6)
            fig.savefig(base + '_skeleton.png', dpi=90, bbox_inches='tight')
