#!/usr/bin/env python3
"""Shared judge sheet for every creature-method experiment: one renderer, so
methods are compared on geometry alone.

    python render.py <mesh.obj|model.glb> <sheet.png>

Sheet (3x2, 1536x1024): shaded 3/4 front, shaded side, shaded 3/4 back /
silhouette side, front, top. Orthographic. y is up; the longest horizontal axis
is turned to x so every creature is framed the same way.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]


def load(path):
    if path.lower().endswith('.glb'):
        import outline as O
        return O.triangles(path)
    V, F = [], []
    for line in open(path, encoding='utf-8', errors='ignore'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            V.append([float(x) for x in p[1:4]])
        elif p[0] == 'f':
            idx = [int(q.split('/')[0]) for q in p[1:]]
            idx = [i - 1 if i > 0 else len(V) + i for i in idx]
            for k in range(1, len(idx) - 1):
                F.append([idx[0], idx[k], idx[k + 1]])
    return np.array(V, float), np.array(F, int)


def canon(V):
    V = V - (V.min(0) + V.max(0)) / 2
    ext = np.ptp(V, 0)
    if ext[2] > ext[0]:                       # long axis to x
        V = V[:, [2, 1, 0]] * np.array([1, 1, -1])
    return V / np.ptp(V, 0).max()


def rot(yaw, pitch):
    a, e = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Ry


_GL = None


def draw_gl(V, F, R, res, shaded):
    """GPU path: depth-tested, smooth vertex normals, 4x MSAA."""
    global _GL
    import moderngl
    if _GL is None:
        ctx = moderngl.create_standalone_context()
        prog = ctx.program(vertex_shader='''#version 330
            in vec3 p; in vec3 n; uniform mat3 R; uniform float s;
            out vec3 vn;
            void main(){ vec3 q = R*p; vn = R*n;
              gl_Position = vec4(q.x*s, q.y*s, q.z*0.5, 1.0); }''',
            fragment_shader='''#version 330
            in vec3 vn; uniform int shaded; out vec4 o;
            void main(){ if(shaded==0){ o=vec4(0,0,0,1); return; }
              vec3 N = normalize(vn); if(!gl_FrontFacing) N = -N;
              vec3 L = normalize(vec3(-0.45,0.65,-0.6));
              float d = abs(dot(N,L)); float rim = pow(1.0-abs(N.z),3.0);
              float g = 0.18 + 0.72*d + 0.12*rim; o = vec4(vec3(g),1); }''')
        _GL = (ctx, prog)
    ctx, prog = _GL
    W = V @ R.T
    s = 0.86 * 2 / max(np.ptp(W[:, 0]), np.ptp(W[:, 1]))
    c = (W.max(0) + W.min(0)) / 2
    Vc = V - c @ R                                   # centre in view space
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    data = np.hstack([Vc, N]).astype('f4')[F.reshape(-1)]
    vbo = ctx.buffer(data.tobytes())
    vao = ctx.vertex_array(prog, [(vbo, '3f 3f', 'p', 'n')])
    fbo = ctx.simple_framebuffer((res, res), samples=4)
    out = ctx.simple_framebuffer((res, res))
    fbo.use(); ctx.enable(moderngl.DEPTH_TEST); ctx.clear(1, 1, 1, 1)
    prog['R'].write(R.T.astype('f4').tobytes())     # GLSL column-major
    prog['s'].value = float(s)
    prog['shaded'].value = int(shaded)
    # flip z so +z (far, camera at -z) is deeper
    prog['R'].write((np.diag([1, 1, -1]) @ R).T.astype('f4').tobytes())
    vao.render()
    ctx.copy_framebuffer(out, fbo)
    img = Image.frombytes('RGB', (res, res), out.read()).convert('L').transpose(Image.FLIP_TOP_BOTTOM)
    for o in (vao, vbo, fbo, out):
        o.release()
    return img


def draw(V, F, R, res, shaded, ref=None):
    try:
        return draw_gl(V, F, R, res, shaded)
    except Exception:
        pass
    W = V @ R.T
    s = res * 0.86 / (ref if ref else max(np.ptp(W[:, 0]), np.ptp(W[:, 1])))
    x = res / 2 + W[:, 0] * s
    y = res / 2 - W[:, 1] * s
    img = Image.new('L', (res, res), 255)
    d = ImageDraw.Draw(img)
    if not shaded:
        for a, b, c in F:
            d.polygon([(x[a], y[a]), (x[b], y[b]), (x[c], y[c])], fill=0)
        return img
    n = np.cross(W[F[:, 1]] - W[F[:, 0]], W[F[:, 2]] - W[F[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    L = np.array([-0.45, 0.65, -0.6]); L /= np.linalg.norm(L)
    lam = np.nan_to_num(np.abs(n @ L))                       # two-sided: methods differ in winding
    g = (55 + 185 * lam).astype(int)
    for i in np.argsort(W[F].mean(1)[:, 2])[::-1]:   # far (+z) first, camera at -z
        a, b, c = F[i]
        d.polygon([(x[a], y[a]), (x[b], y[b]), (x[c], y[c])], fill=int(g[i]))
    return img


def sheet(path, out, res=512):
    V, F = load(path)
    ok = np.isfinite(V).all(1); F = F[ok[F].all(1)]; V = np.where(np.isfinite(V), V, 0.0); V[~ok] = V[ok].mean(0); V = canon(V)
    views = [(rot(-35, -20), True, '3/4 front'), (rot(0, 0), True, 'side'),
             (rot(145, -20), True, '3/4 back'), (rot(0, 0), False, 'side'),
             (rot(90, 0), False, 'front'), (rot(0, -90), False, 'top')]
    img = Image.new('L', (res * 3, res * 2), 255)
    dr = ImageDraw.Draw(img)
    for i, (R, sh, name) in enumerate(views):
        img.paste(draw(V, F, R, res, sh), ((i % 3) * res, (i // 3) * res))
        dr.text(((i % 3) * res + 8, (i // 3) * res + 8), name, fill=140)
    img.save(out)
    return len(V), len(F)


if __name__ == '__main__':
    # several mesh/sheet pairs per call share one GL context (context creation is ~13-17 s on the dev box; render ~2 s)
    a = sys.argv[1:]
    for m, o in zip(a[0::2], a[1::2]):
        v, f = sheet(m, o)
        print(f'{o}: {v} verts, {f} tris', flush=True)
