"""clean.py in.obj out.obj : floor removal, hole close, gentle smooth, isotropic remesh, decimate <=100k, y-up/x-long."""
import sys, numpy as np, trimesh, pymeshlab as ml
from make import largest_component, remove_floor_sheet, remove_base_plate

def to_ms(m):
    ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(m.vertices.astype(np.float64), m.faces.astype(np.int32))); return ms
def from_ms(ms):
    c = ms.current_mesh(); return trimesh.Trimesh(c.vertex_matrix(), c.face_matrix(), process=True)

def clean(m, target=100_000, smooth_steps=4, remesh=True):
    m = largest_component(m)
    m, _ = remove_floor_sheet(m); m, _ = remove_base_plate(m)
    ms = to_ms(m)
    ms.meshing_remove_duplicate_vertices(); ms.meshing_remove_unreferenced_vertices()
    ms.meshing_repair_non_manifold_edges(); ms.meshing_repair_non_manifold_vertices()
    ms.meshing_close_holes(maxholesize=100000, newfaceselected=False, selfintersection=False)
    ms.apply_coord_taubin_smoothing(stepsmoothnum=smooth_steps, lambda_=0.5, mu=-0.53)
    if remesh:
        diag = ms.current_mesh().bounding_box().diagonal()
        # edge length giving ~1.6x target tris before decimation
        A = ms.get_geometric_measures()["surface_area"]
        L = np.sqrt(4 * A / (np.sqrt(3) * 1.6 * target))
        ms.meshing_isotropic_explicit_remeshing(iterations=3, targetlen=ml.PureValue(L), featuredeg=60)
    if ms.current_mesh().face_number() > target:
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target*0.98), preservenormal=True, planarquadric=True)
    ms.meshing_repair_non_manifold_edges(); ms.meshing_close_holes(maxholesize=100000, selfintersection=False)
    m = largest_component(from_ms(ms)); trimesh.repair.fill_holes(m); m.fix_normals()
    v = m.vertices - m.vertices.mean(0)
    w, e = np.linalg.eigh(np.cov(v[:, [0, 2]].T)); ax = e[:, np.argmax(w)]
    m.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(ax[1], ax[0]), [0, 1, 0]))
    x, y = m.vertices[:, 0], m.vertices[:, 1]; lo, hi = x.min(), x.max(); L = hi - lo
    if y[x > hi - .2 * L].max() > y[x < lo + .2 * L].max():
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))
    b = m.bounds; m.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2])
    return m

if __name__ == "__main__":
    m = clean(trimesh.load(sys.argv[1], force="mesh"))
    m.export(sys.argv[2]); print(sys.argv[2], len(m.faces), "watertight", m.is_watertight)
