import numpy as np
from sdf2 import *

def _seg(s,a,b,ra,rb,fy=1.0,fz=1.0,up=(1,0,0),m=False):
    """tapered capsule a->b, cross-section elliptical: half-axes r*fy (toward 'up' side), r*fz (lateral)"""
    a=np.asarray(a,float);b=np.asarray(b,float);L=np.linalg.norm(b-a)
    ax,t,sd=frame(a,b,up); x,y,z=s.rel(a,m)
    X=x*ax[0]+y*ax[1]+z*ax[2];Y=x*t[0]+y*t[1]+z*t[2];Z=x*sd[0]+y*sd[1]+z*sd[2]
    h=np.clip(X/L,0,1); r=ra+(rb-ra)*h
    q=np.sqrt((X-h*L)**2+(Y/fy)**2+(Z/fz)**2)
    return (q-r)*min(fy,fz)
F.seg=_seg

def build3(fn,out,bounds,n=330,target=78000,smooth=10):
    return build(fn,out,bounds,n=n,target=target,smooth=smooth)
