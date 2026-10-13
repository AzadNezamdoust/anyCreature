import sys; sys.argv=['x']; import make, trimesh, glob
for d in sys.stdin.read().split():
    m=trimesh.load(d+'/mesh.obj',force='mesh'); f,p=make.finalize(m); f.export(d+'/final.obj'); print(d,len(f.faces),p,f.extents.round(2),flush=True)
