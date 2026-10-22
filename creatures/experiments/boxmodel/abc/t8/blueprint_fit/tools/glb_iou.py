"""Silhouette IoU of a GLB (rest pose, all meshes) vs sheet_masks.npz, side/front/top, on the sheet_masks grid.
usage: glb_iou.py <glb> <sheet_masks.npz> [overlay.png]  -> prints json {view: iou, ...}"""
import sys, json, struct, numpy as np
from PIL import Image, ImageDraw
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_masks import GRID, G

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def load(path, keep=lambda n: True):
    b = open(path, 'rb').read()
    jl = struct.unpack_from('<I', b, 12)[0]; J = json.loads(b[20:20 + jl])
    off = 20 + jl; bl = struct.unpack_from('<I', b, off)[0]; BIN = b[off + 8: off + 8 + bl]
    def acc(i):
        a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]
        o = v.get('byteOffset', 0) + a.get('byteOffset', 0); n = NC[a['type']]; dt = CT[a['componentType']]
        st = v.get('byteStride', 0) or n * np.dtype(dt).itemsize
        raw = np.frombuffer(BIN, np.uint8, count=st * (a['count'] - 1) + n * np.dtype(dt).itemsize, offset=o)
        out = np.lib.stride_tricks.as_strided(raw.view(np.uint8), (a['count'], n * np.dtype(dt).itemsize), (st, 1)).copy()
        return out.view(dt).reshape(a['count'], n)
    def mat(nd_):
        if 'matrix' in nd_: return np.array(nd_['matrix']).reshape(4, 4).T
        t = nd_.get('translation', [0, 0, 0]); r = nd_.get('rotation', [0, 0, 0, 1]); s = nd_.get('scale', [1, 1, 1])
        x, y, z, w = r
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        M = np.eye(4); M[:3, :3] = R * np.array(s); M[:3, 3] = t; return M
    tris = []
    def walk(i, P):
        nd_ = J['nodes'][i]; M = P @ mat(nd_)
        if 'mesh' in nd_ and keep(nd_.get('name', '')):
            Mm = np.eye(4) if 'skin' in nd_ else M
            for pr in J['meshes'][nd_['mesh']]['primitives']:
                p = acc(pr['attributes']['POSITION']).astype(float)
                p = (Mm @ np.c_[p, np.ones(len(p))].T).T[:, :3]
                idx = acc(pr['indices']).reshape(-1, 3) if 'indices' in pr else np.arange(len(p)).reshape(-1, 3)
                q = np.c_[p[:, 0], -p[:, 2], p[:, 1]]          # glTF Y-up -> Blender Z-up
                tris.append(q[idx])
        for c in nd_.get('children', []): walk(c, M)
    for r in J['scenes'][J.get('scene', 0)]['nodes']: walk(r, np.eye(4))
    return np.concatenate(tris)

AX = {'side': (1, 2), 'front': (0, 2), 'top': (0, 1)}

def raster(tris, view):
    (u0, u1), (v0, v1) = GRID[view]; W = int(round((u1 - u0) / G)); H = int(round((v1 - v0) / G))
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im); a, b = AX[view]
    T = tris[:, :, [a, b]]
    T = np.stack([(T[..., 0] - u0) / G, (T[..., 1] - v0) / G], -1)
    for t in T:
        d.polygon([tuple(p) for p in t], fill=255)
    return np.asarray(im) > 0

def ious(tris, M):
    out = {}
    for v in ('side', 'front', 'top'):
        m = raster(tris, v); s = M[v][:m.shape[0], :m.shape[1]]
        out[v] = round(float((m & s).sum() / max(1, (m | s).sum())), 4)
        out[v + '_area_ratio'] = round(float(m.sum() / max(1, s.sum())), 3)
    out['mean'] = round((out['side'] + out['front'] + out['top']) / 3, 4)
    return out

def overlay(tris, M, path):
    ims = []
    for v in ('side', 'front', 'top'):
        m = raster(tris, v); s = M[v][:m.shape[0], :m.shape[1]]
        rgb = np.full(m.shape + (3,), 255, np.uint8)
        rgb[s & ~m] = (230, 120, 120); rgb[m & ~s] = (120, 140, 230); rgb[m & s] = (150, 150, 150)
        ims.append(Image.fromarray(rgb[::-1]))
    H = max(i.size[1] for i in ims); out = Image.new('RGB', (sum(i.size[0] for i in ims), H), 'white'); x = 0
    for i in ims: out.paste(i, (x, 0)); x += i.size[0]
    out.save(path)

if __name__ == '__main__':
    tris = load(sys.argv[1]); M = dict(np.load(sys.argv[2]))
    r = ious(tris, M); print(json.dumps(r))
    if len(sys.argv) > 3: overlay(tris, M, sys.argv[3])
