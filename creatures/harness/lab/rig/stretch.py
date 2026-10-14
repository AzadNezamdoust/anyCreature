import sys; sys.argv=['x']; exec(open('E:/gen3d/rig/verify.py').read().split('if __name__')[0])
import numpy as np
for a in ['wolf','horse']:
  R,I,*_=pose('E:/gen3d/rig/out/%s_rigged.glb'%a,None,0)
  e=np.r_[I[:,[0,1]],I[:,[1,2]],I[:,[2,0]]]; l0=np.linalg.norm(R[e[:,0]]-R[e[:,1]],axis=1); ok=l0>2e-3
  for an,t in (('walk',0),('walk',.25),('walk',.5),('walk',.75),('idle',.55)):
    P=pose('E:/gen3d/rig/out/%s_rigged.glb'%a,an,t)[0]; r=np.linalg.norm(P[e[:,0]]-P[e[:,1]],axis=1)[ok]/l0[ok]
    print(a,an,t,'stretch p0.1 %.2f p99.9 %.2f min %.2f max %.2f'%(*np.percentile(r,[0.1,99.9]),r.min(),r.max()))
