"""clean8.py in.obj out.obj : no floor slicing; drop floaters + thin floor sheets only; faired small-hole fill;
feature-preserving light smoothing; quadric decimate <=100k; y-up/x-long orient."""
import sys, numpy as np, trimesh, pymeshlab as ml

def to_ms(m):
    ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(m.vertices.astype(np.float64), m.faces.astype(np.int32))); return ms
def from_ms(ms):
    c = ms.current_mesh(); return trimesh.Trimesh(c.vertex_matrix(), c.face_matrix(), process=True)

def drop_floaters(m, frac=0.03):
    parts = m.split(only_watertight=False)
    if len(parts) <= 1: return m
    big = max(len(p.faces) for p in parts)
    return trimesh.util.concatenate([p for p in parts if len(p.faces) >= frac * big])

def remove_thin_sheet(m, band=0.04, thin=0.012, min_frac=0.03):
    """Delete only near-zero-thickness horizontal faces near the bottom (floor sheet). Never slices limbs."""
    lo, hi = m.bounds; ext = hi - lo; H = ext.max()   # scale by longest extent (flat animals)
    c = m.triangles_center; n = m.face_normals
    cand = np.where(c[:, 1] < lo[1] + band * H)[0]
    if len(cand) == 0: return m, 0.0
    o = c[cand] - n[cand] * 1e-5 * H
    loc, ri, _ = m.ray.intersects_location(o, -n[cand], multiple_hits=False)
    d = np.full(len(cand), np.inf); d[ri] = np.linalg.norm(loc - o[ri], axis=1)
    sheet = cand[d < thin * H]
    a = m.area_faces[sheet][np.abs(n[sheet, 1]) > 0.8].sum() / 2
    if a < min_frac * ext[0] * ext[2]: return m, 0.0
    keep = np.ones(len(m.faces), bool); keep[sheet] = False
    m2 = trimesh.Trimesh(m.vertices, m.faces[keep], process=True)
    parts = m2.split(only_watertight=False)
    m2 = max(parts, key=lambda p: len(p.faces))  # creature stays; sheet shreds dropped
    return m2, a / (ext[0] * ext[2])

def faired_fill(ms, maxhole=400):
    ms.set_selection_none()
    try:
        ms.meshing_close_holes(maxholesize=maxhole, selected=False, newfaceselected=True, selfintersection=False, refinehole=True)
    except Exception:
        ms.meshing_close_holes(maxholesize=maxhole, newfaceselected=True, selfintersection=False)
    if ms.current_mesh().selected_face_number() > 0:
        ms.compute_selection_transfer_face_to_vertex(inclusive=False)
        ms.apply_coord_laplacian_smoothing(stepsmoothnum=15, selected=True, cotangentweight=True)
    ms.set_selection_none()

def clean(m, target=100_000, sheet_rm=True):
    m = drop_floaters(m)
    m, sheet = remove_thin_sheet(m) if sheet_rm else (m, 0.0)
    ms = to_ms(m)
    ms.meshing_remove_duplicate_vertices(); ms.meshing_remove_unreferenced_vertices()
    ms.meshing_repair_non_manifold_edges(); ms.meshing_repair_non_manifold_vertices()
    faired_fill(ms)
    ms.apply_coord_two_steps_smoothing(stepsmoothnum=2, normalthr=40, stepnormalnum=8, stepfitnum=8)
    if ms.current_mesh().face_number() > target:
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target * 0.98), preservenormal=True, preservetopology=True, planarquadric=True)
    ms.meshing_repair_non_manifold_edges(); faired_fill(ms)
    m = from_ms(ms); m = drop_floaters(m); m.fix_normals()
    v = m.vertices - m.vertices.mean(0)
    w, e = np.linalg.eigh(np.cov(v[:, [0, 2]].T)); ax = e[:, np.argmax(w)]
    m.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(ax[1], ax[0]), [0, 1, 0]))
    x, y = m.vertices[:, 0], m.vertices[:, 1]; lo, hi = x.min(), x.max(); L = hi - lo
    if y[x > hi - .2 * L].max() > y[x < lo + .2 * L].max():
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))
    b = m.bounds; m.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2])
    return m, sheet

if __name__ == "__main__":
    m, sheet = clean(trimesh.load(sys.argv[1], force="mesh"), sheet_rm="--nosheet" not in sys.argv)
    m.export(sys.argv[2]); print(sys.argv[2], len(m.faces), "watertight", m.is_watertight, "sheet", round(sheet, 3))
