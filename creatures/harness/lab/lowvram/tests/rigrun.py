import sys; sys.path.insert(0, 'E:/gen3d/rig'); import rig, trimesh
from scipy import ndimage
def voxelize(V, T):   # rig.voxelize + leak-proof fill: if the shell leaks (fill ~ shell), close 1-voxel gaps first
    vg = trimesh.Trimesh(V, T, process=False).voxelized(rig.P); shell = vg.matrix.copy()
    solid = ndimage.binary_fill_holes(shell)
    if solid.sum() < 2 * shell.sum():
        solid = ndimage.binary_fill_holes(ndimage.binary_closing(shell, iterations=2)) | shell
        print('voxelize: shell leaked -> closed gaps', flush=True)
    return solid, vg.transform[:3, 3]
rig.voxelize = voxelize
a, src, here = sys.argv[1:4]; rig.SRC = src; rig.HERE = here; rig.main(a)
