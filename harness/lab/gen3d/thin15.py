"""thin15.py in.obj out.obj [--res 512] [--tmin 0.012] : thin-part REPAIR for raw image->3D meshes.

1. drop tiny floating fragments (<2% of largest component) + floor sheet (clean8 rule, never slices limbs)
2. detect thin faces: inward ray thickness < tmin*L, inward ray miss (open sheet / flipped), or touching an open boundary
3. rebuild one watertight surface from a voxel field at res^3:
     body  = signed distance of filled (closed) occupancy
     sheets= unsigned distance - r   (r = tmin*L/2)  only inside a mask around thin faces  -> SOLIDIFIED, rim closed
   marching cubes; every vertex outside the thin mask is snapped back onto the original surface (rest untouched)
4. clean8 tail: faired small-hole fill, feature-preserving smoothing, quadric decimate <=100k, y-up orient
"""
import sys, numpy as np, trimesh
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
sys.path.insert(0, r"E:\gen3d")
import clean8


def arg(name, d):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else d


def thin_faces(m, tmin):
    L = m.extents.max(); n = m.face_normals; c = m.triangles_center
    o = c - n * 1e-5 * L
    loc, ri, _ = m.ray.intersects_location(o, -n, multiple_hits=False)
    d = np.full(len(c), np.inf); d[ri] = np.linalg.norm(loc - o[ri], axis=1)
    thin = d < tmin * L
    miss = ~np.isfinite(d)
    # open boundary faces (+1 ring)
    e = m.edges_sorted; key = e[:, 0].astype(np.int64) * len(m.vertices) + e[:, 1]
    u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    bv = np.unique(e[cnt[inv] == 1])
    vb = np.zeros(len(m.vertices), bool); vb[bv] = True
    bnd = vb[m.faces].any(1)
    return thin | miss | bnd, dict(thin=int(thin.sum()), miss=int(miss.sum()), bnd=int(bnd.sum()))


def repair(m, res=512, tmin=0.012):
    lo, hi = m.bounds; L = (hi - lo).max(); h = L / res
    pad = int(np.ceil(tmin * L / h)) + 6
    org = lo - pad * h; shape = np.ceil((hi - lo) / h).astype(int) + 2 * pad + 1
    tf, stats = thin_faces(m, tmin)
    # dense surface samples -> voxels
    npts = int(min(8e6, max(2e6, m.area / (h * h) * 6)))
    P, fi = trimesh.sample.sample_surface_even(m, npts) if False else trimesh.sample.sample_surface(m, npts)
    P = np.vstack([P, m.vertices]); fi = np.concatenate([fi, -np.ones(len(m.vertices), int)])
    ijk = np.clip(np.round((P - org) / h).astype(int), 0, shape - 1)
    surf = np.zeros(shape, bool); surf[tuple(ijk.T)] = True
    # closed occupancy: close small gaps, fill, undo
    k = int(arg("--close", 4))
    sc = nd.binary_dilation(surf, iterations=k)
    solid = nd.binary_fill_holes(sc)
    solid = nd.binary_erosion(solid, iterations=k) | surf
    inside = nd.binary_fill_holes(solid)
    dout = nd.distance_transform_edt(~inside); din = nd.distance_transform_edt(inside)
    sdf = np.where(inside, -din + 0.5, dout - 0.5)  # voxel units
    # unsigned distance to surface + thin mask
    udf = nd.distance_transform_edt(~surf)
    r = 0.5 * tmin * L / h
    # thin = surface voxels whose filled solid has no interior deeper than r nearby (sheets, ragged plates);
    # robust to internal double shells (they are filled over) unlike ray thickness
    R = int(np.ceil(3 * r)) + 2  # wide window: loose skins lying on a solid body are not thin parts
    deep = nd.maximum_filter(din, size=2 * R + 1)
    ext = nd.binary_dilation(~inside, iterations=2)  # only exterior-facing surface
    tm = surf & ext & (deep < r + 0.5)
    sel = fi >= 0; sel[sel] = tf[fi[sel]]
    tm2 = np.zeros(shape, bool); tm2[tuple(ijk[sel].T)] = True
    stats["thin_vox"] = int(tm.sum())
    mask = nd.binary_dilation(tm, iterations=int(np.ceil(r)) + 3)
    f = sdf.copy()
    f[mask] = np.minimum(sdf[mask], udf[mask] - r)
    f = nd.gaussian_filter(f, 0.7)
    V, F, _, _ = marching_cubes(f, 0.0)
    out = trimesh.Trimesh(V * h + org, F[:, ::-1], process=True)
    # snap vertices outside the (wider) thin mask back to the original surface
    import fast_simplification as fs
    if len(out.faces) > 400_000:
        v_, f_ = fs.simplify(out.vertices, out.faces, target_reduction=1 - 400_000 / len(out.faces))
        out = trimesh.Trimesh(v_, f_, process=True)
    keepmask = nd.binary_dilation(mask, iterations=2)
    vi = np.clip(np.round((out.vertices - org) / h).astype(int), 0, shape - 1)
    far = ~keepmask[tuple(vi.T)]
    snapped, dd, _ = trimesh.proximity.closest_point(m, out.vertices[far])  # exact closest point
    ok = dd < 10 * h  # only snap where the reconstruction is near the original
    vv = out.vertices.copy(); idx = np.where(far)[0][ok]; vv[idx] = snapped[ok]
    out = trimesh.Trimesh(vv, out.faces, process=False)
    stats.update(faces=len(m.faces), thinfrac=round(float(tf.mean()), 3), mask_vox=int(mask.sum()),
                 snapped=round(float(len(idx) / len(vv)), 3))
    return out, stats


def main():
    src, dst = sys.argv[1], sys.argv[2]
    m = trimesh.load(src, force="mesh"); m.merge_vertices()
    m = clean8.drop_floaters(m, 0.03)
    m, sheet = clean8.remove_thin_sheet(m)
    out, st = repair(m, int(arg("--res", 512)), arg("--tmin", 0.012))
    out = trimesh.Trimesh(*map(np.asarray, (out.vertices, out.faces)), process=True)
    fin, _ = clean8.clean(out, sheet_rm=False)
    if len(fin.faces) > 100_000:
        import fast_simplification as fs
        v, f = fs.simplify(fin.vertices, fin.faces, target_reduction=1 - 99_000 / len(fin.faces))
        fin = trimesh.Trimesh(v, f, process=True)
    fin.export(dst)
    print(dst, len(fin.faces), "wt", fin.is_watertight, "sheet", round(sheet, 3), st, flush=True)


if __name__ == "__main__":
    main()
