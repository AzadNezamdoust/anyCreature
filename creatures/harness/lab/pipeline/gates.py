"""gates.py - cheap automatic geometry gates, run BEFORE any LLM judge (venv python: trimesh + scipy).

    E:/gen3d/venv/Scripts/python.exe gates.py <mesh.obj> [<mesh2.obj> ...] [--ref ref_rgba.png] [--json out.json]

Per mesh (canonical frame: y up, long axis x, lateral z - same as clean8/render.py):
  watertight   trimesh.is_watertight after clean8
  floor_slab   area of near-zero-thickness horizontal sheet in the bottom 4% band / footprint (clean8's test)
  thin_parts   connected blobs that vanish under a 1-voxel morphological opening (96^3 grid), size >= 6 voxels
  symmetry     IoU of the voxel occupancy with its mirror across the lateral (z) mid-plane
  sil_iou      best IoU (over yaw 0..330 step 30, 15k-face subsample, both mirror flips) of the mesh's orthographic silhouette vs the
               reference alpha mask, both cropped to bbox and fitted into 128^2 (weak: hero is a 3/4 view)
pass = all of: watertight, floor_slab < 0.02, thin_parts <= 12, symmetry >= 0.55, sil_iou >= 0.45 (if --ref).
Thresholds are first-cut (calibrated on wolf h21 seeds, see RESULTS.md auto-judge log); change TH below.
"""
import sys, json, math, numpy as np

TH = dict(floor_slab=0.02, thin_parts=12, symmetry=0.55, sil_iou=0.45)
N = 96


def canon(m):
    import trimesh
    v = m.vertices - (m.bounds[0] + m.bounds[1]) / 2
    e = np.ptp(v, 0)
    if e[2] > e[0]: v = v[:, [2, 1, 0]] * np.array([1, 1, -1])
    return trimesh.Trimesh(v / np.ptp(v, 0).max(), m.faces, process=False)


def floor_slab(m, band=0.04, thin=0.012):
    lo, hi = m.bounds; ext = hi - lo; H = ext.max()
    c = m.triangles_center; n = m.face_normals
    cand = np.where(c[:, 1] < lo[1] + band * H)[0]
    if len(cand) == 0: return 0.0
    o = c[cand] - n[cand] * 1e-5 * H
    loc, ri, _ = m.ray.intersects_location(o, -n[cand], multiple_hits=False)
    d = np.full(len(cand), np.inf); d[ri] = np.linalg.norm(loc - o[ri], axis=1)
    sheet = cand[d < thin * H]
    a = m.area_faces[sheet][np.abs(n[sheet, 1]) > 0.8].sum() / 2
    return float(a / max(ext[0] * ext[2], 1e-9))


def voxels(m):
    vg = m.voxelized(pitch=1.0 / N).fill()
    return vg.matrix.astype(bool)


def thin_parts(occ):
    from scipy import ndimage
    opened = ndimage.binary_opening(occ, structure=ndimage.generate_binary_structure(3, 1), iterations=1)
    lab, n = ndimage.label(occ & ~opened)
    if n == 0: return 0
    sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    return int((sz >= 6).sum())


def symmetry(occ):
    # lateral axis = z (index 2); mirror about the occupancy's own z centre
    z = np.where(occ.any((0, 1)))[0]
    if len(z) == 0: return 0.0
    a = occ[:, :, z[0]:z[-1] + 1]; b = a[:, :, ::-1]
    return float((a & b).sum() / max((a | b).sum(), 1))


def fit(mask, S=128):
    from PIL import Image
    ys, xs = np.where(mask)
    if len(xs) == 0: return np.zeros((S, S), bool)
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape; s = (S - 4) / max(h, w)
    im = Image.fromarray(crop.astype(np.uint8) * 255).resize((max(1, int(w * s)), max(1, int(h * s))))
    out = np.zeros((S, S), np.uint8); oy, ox = (S - im.height) // 2, (S - im.width) // 2
    out[oy:oy + im.height, ox:ox + im.width] = np.asarray(im)
    return out > 127


def sil_iou(m, ref_png):
    from PIL import Image, ImageDraw
    ref = fit(np.asarray(Image.open(ref_png).convert('RGBA'))[..., 3] > 128)
    V = m.vertices; F = m.faces
    best = 0.0
    for yaw in range(0, 360, 30):
        a = math.radians(yaw); R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        P = V @ R.T; S = 256
        p = (P[:, :2] - P[:, :2].min(0)) / max(np.ptp(P[:, :2], 0).max(), 1e-9) * (S - 1)
        im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
        tri = p[F]; tri[..., 1] = S - 1 - tri[..., 1]
        for t in tri[:: max(1, len(F) // 15000)]: d.polygon([tuple(q) for q in t], fill=255)
        from PIL import ImageFilter
        sil = fit(np.asarray(im.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))) > 0)   # close subsample gaps
        for s in (sil, sil[:, ::-1]):
            best = max(best, float((s & ref).sum() / max((s | ref).sum(), 1)))
    return best


def gate(path, ref=None):
    import trimesh
    m = trimesh.load(path, force='mesh', process=False)
    r = dict(mesh=path, faces=int(len(m.faces)), watertight=bool(m.is_watertight))
    mc = canon(m)
    r['floor_slab'] = round(floor_slab(mc), 4)
    occ = voxels(mc)
    r['thin_parts'] = thin_parts(occ)
    r['symmetry'] = round(symmetry(occ), 3)
    if ref: r['sil_iou'] = round(sil_iou(mc, ref), 3)
    fails = []
    if not r['watertight']: fails.append('not watertight')
    if r['floor_slab'] >= TH['floor_slab']: fails.append(f"floor slab {r['floor_slab']}")
    if r['thin_parts'] > TH['thin_parts']: fails.append(f"thin parts {r['thin_parts']}")
    if r['symmetry'] < TH['symmetry']: fails.append(f"symmetry {r['symmetry']}")
    if ref and r['sil_iou'] < TH['sil_iou']: fails.append(f"silhouette IoU {r['sil_iou']}")
    r['fails'] = fails; r['pass'] = not fails
    return r


if __name__ == '__main__':
    a = sys.argv[1:]; ref = out = None
    if '--ref' in a: i = a.index('--ref'); ref = a[i + 1]; del a[i:i + 2]
    if '--json' in a: i = a.index('--json'); out = a[i + 1]; del a[i:i + 2]
    res = [gate(p, ref) for p in a]
    for r in res: print(('PASS ' if r['pass'] else 'FAIL ') + json.dumps(r), flush=True)
    if out: json.dump(res, open(out, 'w'), indent=1)
