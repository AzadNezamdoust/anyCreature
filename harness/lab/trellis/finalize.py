"""finalize.py <animal> <seed>: final.obj/.png = cleaned seed; final.glb = cleaned mesh + vertex colors (nearest raw vertex)."""
import sys, shutil, trimesh, numpy as np
from scipy.spatial import cKDTree
a, s = sys.argv[1], sys.argv[2]; d = f'E:/gen3d/trellis/{a}'
shutil.copy(f'{d}/clean_s{s}.obj', f'{d}/final.obj'); shutil.copy(f'{d}/sheet_s{s}.png', f'{d}/final.png')
raw = trimesh.load(f'{d}/raw_s{s}.glb', force='mesh'); c = trimesh.load(f'{d}/final.obj', force='mesh', process=False)
# clean8 re-orients/rescales: align by fitting bbox of raw (y-up already) to clean via PCA-free min/max per axis after
# matching the axis order (longest horizontal -> x)
rv = raw.vertices.copy(); ext = np.ptp(rv, 0)
if ext[2] > ext[0]: rv = rv[:, [2, 1, 0]]
cv = c.vertices
rv = (rv - rv.min(0)) / np.ptp(rv, 0) * np.ptp(cv, 0) + cv.min(0)
d2a, idx = cKDTree(rv).query(cv)
d2b, idx2 = cKDTree(rv * [-1, 1, 1] + [cv[:, 0].max() + cv[:, 0].min(), 0, 0]).query(cv)  # x-flip candidate
if d2b.mean() < d2a.mean(): idx = idx2
col = raw.visual.vertex_colors[idx]
trimesh.Trimesh(cv, c.faces, vertex_colors=col, process=False).export(f'{d}/final.glb')
print(a, s, 'color-match mean dist', round(float(min(d2a.mean(), d2b.mean())), 4))
