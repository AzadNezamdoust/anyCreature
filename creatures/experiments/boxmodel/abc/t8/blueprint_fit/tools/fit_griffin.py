"""Silhouette-fitting optimizer for the griffin blueprint (topology fixed).
Surrogate silhouettes: convex hulls of consecutive loft sections / leg sections / wing key arcs (mirrored),
plus the stage-3 pieces (feet, claws, eye, tuft) rasterised from the baseline GLB as a fixed layer.
Objective: mean IoU (side, front, top) vs sheet masks - smoothness - drift from 1.0.
usage: fit_griffin.py <candidate dir> <sheet_masks.npz> <baseline glb>"""
import sys, os, json, math, time, numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sheet_masks as SM
SM.G = 0.01                    # fit at 1 cm (masks downsampled 2x); final IoU is measured at 5 mm on the GLB
from sheet_masks import GRID, G
import glb_iou as GI
cand, masks_p, base_glb = sys.argv[1:4]
sys.path.insert(0, cand)
import griffin_bp as BP
M = {k: v[::2, ::2] for k, v in np.load(masks_p).items()}
AX = GI.AX
VIEWS = ('side', 'front', 'top')
SIZE = {v: (int(round((GRID[v][0][1] - GRID[v][0][0]) / G)), int(round((GRID[v][1][1] - GRID[v][1][0]) / G))) for v in VIEWS}
fixed_tris = GI.load(base_glb, keep=lambda n: n.startswith('piece_') and n != 'piece_wing')
FIXED = {v: GI.raster(fixed_tris, v) for v in VIEWS}

def superell(c, rx, ry, n=12, p=3.0):
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n; ct, st = math.cos(t), math.sin(t)
        out.append((c[0] + rx * np.sign(ct) * abs(ct) ** (2 / p), c[1] + ry * np.sign(st) * abs(st) ** (2 / p), c[2]))
    return out

def mirror(pts):
    return pts + [(-x, y, z) for x, y, z in pts]

def chains(secs, fore, hind, wk):
    """lists of consecutive 3D point sets; each pair -> one hull polygon per view"""
    C = []
    C.append([mirror(BP.sec_pts(*s[1:])) for s in secs])
    idx = [s[0] for s in secs]
    for which, legs in (('fore', fore), ('hind', hind)):
        nm, S, j0, F = BP.REGIONS[which]; i0 = idx.index(nm)
        reg = [BP.sec_pts(*secs[i][1:])[j] for i in range(i0, i0 + S + 1) for j in range(j0, j0 + F + 1)]
        L = [reg] + [superell(c, rx, ry) for c, rx, ry in legs]
        C.append([P + [(-x, y, z) for x, y, z in P] for P in L])       # both legs in one set per station (hull per side below)
    wing = []
    for y, e0, e2, e4 in wk:
        arc = [(e0[0], y, e0[1]), (e2[0], y, e2[1]), (e4[0], y, e4[1])]
        wing.append(arc)
    C.append(('wing', wing))
    return C

def raster(secs, fore, hind, wk):
    out = {}
    for v in VIEWS:
        (u0, u1), (v0, v1) = GRID[v]; W, H = SIZE[v]
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im); a, b = AX[v]
        def poly(P):
            q = np.array([((p[a] - u0) / G, (p[b] - v0) / G) for p in P])
            try:
                h = ConvexHull(q); d.polygon([tuple(q[i]) for i in h.vertices], fill=255)
            except Exception:
                pass
        for ch in chains(secs, fore, hind, wk):
            if isinstance(ch, tuple):                   # wing, one side + mirror
                for sg in (1, -1):
                    for A, B in zip(ch[1], ch[1][1:]):
                        poly([(sg * x, y, z) for x, y, z in A + B])
                continue
            for A, B in zip(ch, ch[1:]):
                if len(A) != 26 and v != 'side':     # legs: hull each side separately
                    for sg in (1, -1):
                        poly([p for p in A + B if p[0] * sg >= 0])
                else:
                    poly(A + B)
        out[v] = (np.asarray(im) > 0) | FIXED[v]
    return out

def score(R):
    r = {}
    for v in VIEWS:
        m = R[v]; s = M[v][:m.shape[0], :m.shape[1]]
        r[v] = float((m & s).sum() / max(1, (m | s).sum()))
    return r

NK = BP.NK
def unpack(x):
    return dict(kW=list(x[0:NK]), kT=list(x[NK:2 * NK]), kB=list(x[2 * NK:3 * NK]), fr=x[3 * NK], hr=x[3 * NK + 1], wz=x[3 * NK + 2])

LO = np.r_[[0.85] * (3 * NK), 0.85, 0.85, -0.05]; HI = np.r_[[1.40] * (3 * NK), 1.30, 1.30, 0.08]
def obj(x):
    x = np.clip(x, LO, HI)
    p = unpack(x)
    s = score(raster(*BP.apply(p)))
    k = x[:3 * NK].reshape(3, NK)
    smooth = float((np.diff(k, 2, axis=1) ** 2).sum())
    global NF; NF += 1
    if NF % 100 == 0: print('eval', NF, round(-(s['side'] + s['front'] + s['top']) / 3, 4), flush=True)
    return -(s['side'] + s['front'] + s['top']) / 3 + 0.5 * smooth

NF = 0
x0 = np.r_[[1.0] * (3 * NK), 1.0, 1.0, 0.0]
t0 = time.time()
s0 = score(raster(*BP.apply(unpack(x0))))
print('surrogate baseline', {k: round(v, 4) for k, v in s0.items()}, 'eval %.3fs' % (time.time() - t0))
# pattern search (IoU on a raster is piecewise flat: Powell's line search stalls on the knots)
x = x0.copy(); fx = obj(x)
for step in (0.10, 0.05, 0.025):
    for _pass in range(2):
        moved = False
        for i in range(len(x)):
            st = step * (1.0 if i < 3 * NK + 2 else 0.4)
            for sg in (1, -1):
                y = x.copy(); y[i] = np.clip(y[i] + sg * st, LO[i], HI[i]); fy = obj(y)
                if fy < fx - 1e-5:
                    x, fx, moved = y, fy, True; break
        print('step', step, 'pass', _pass, 'obj', round(fx, 4), flush=True)
        if not moved: break
class _B: pass
best = _B(); best.nfev = NF
p = unpack(x)
s1 = score(raster(*BP.apply(p)))
print('surrogate fitted', {k: round(v, 4) for k, v in s1.items()}, 'nfev', best.nfev, '%.0fs' % (time.time() - t0))
secs, fore, hind, wk = BP.apply(p)
bp = BP.blueprint(secs, fore, hind, wk)
bp['fit'] = dict(method='Powell on surrogate hull silhouettes vs sheet masks, topology fixed', params={k: (np.round(v, 4).tolist() if isinstance(v, list) else round(float(v), 4)) for k, v in p.items()},
                 surrogate_iou_before={k: round(v, 4) for k, v in s0.items()}, surrogate_iou_after={k: round(v, 4) for k, v in s1.items()},
                 nfev=int(best.nfev), seconds=round(time.time() - t0))
json.dump(bp, open(os.path.join(cand, 'blueprint_fit.json'), 'w'), indent=1)
json.dump(BP.blueprint(), open(os.path.join(cand, 'blueprint_typed_base.json'), 'w'), indent=1)
# preview
for tag, R in (('before', raster(*BP.apply(unpack(x0)))), ('after', raster(secs, fore, hind, wk))):
    ims = []
    for v in VIEWS:
        m = R[v]; s = M[v][:m.shape[0], :m.shape[1]]; rgb = np.full(m.shape + (3,), 255, np.uint8)
        rgb[s & ~m] = (230, 120, 120); rgb[m & ~s] = (120, 140, 230); rgb[m & s] = (150, 150, 150); ims.append(Image.fromarray(rgb[::-1]))
    out = Image.new('RGB', (sum(i.size[0] for i in ims), max(i.size[1] for i in ims)), 'white'); xo = 0
    for i in ims: out.paste(i, (xo, 0)); xo += i.size[0]
    out.save(os.path.join(cand, f'fit_surrogate_{tag}.png'))
print(json.dumps(bp['fit']['params']))
