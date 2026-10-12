import sys, numpy as np
from sdf3 import *
import animals2, animals3
from animals2 import pawpad
from animals3 import LP

FY,FZ=1.25,0.78
T=1.0  # limb thickness multiplier

def hoofend(g,fet,paw,s,m):
    h=paw+(-0.035*s,0,0)
    g.append((g_seg(fet,h+(0,0.035*s,0),0.024*s,0.03*s,m),0.02*s))
    g.append((F_.sph(fet+(0.004*s,0,0),0.03*s,m=m),0.02*s))
    g.append((F_.rbox(h+(0,0.024*s,0),(0.046*s,0.024*s,0.04*s),0.01*s,ax=(1,-0.4,0),m=m),0.012*s))

F_=None
def g_seg(a,b,ra,rb,m,fy=FY,fz=FZ):
    return F_.seg(a,b,ra*T,rb*T,fy,fz,up=(1,0,0),m=m)

def _combine(f,parts,k):
    d=None
    for e,kk in parts: d=e if d is None else smin(d,e,kk)
    f.add(d,k)

def foreleg(f,top,sh,el,wr,paw,s,m=True,hoof=False):
    global F_; F_=f
    top,sh,el,wr,paw=[np.asarray(p,float) for p in (top,sh,el,wr,paw)]
    P=[]
    P.append((f.seg(top,sh+(0.02*s,0.02*s,-0.01*s),0.05*s,0.035*s,2.0,0.4,up=(1,0,0),m=m),0))       # scapula blade
    P.append((f.sph(top+(0.01*s,-0.01*s,0),0.03*s,m=m),0.03*s))
    P.append((f.oell(sh+(-0.015*s,0.03*s,0.008*s),sh+(-0.01*s,-0.07*s,0.01*s),0.05*s,0.045*s,m=m),0.03*s))   # point of shoulder/deltoid
    P.append((g_seg(sh,el,0.05*s,0.04*s,m),0.03*s))                                               # humerus
    P.append((f.oell(sh+(0.06*s,0.02*s,0),el+(0.035*s,0.045*s,0),0.075*s,0.055*s,up=(1,0,0),m=m),0.04*s))  # triceps (back)
    P.append((f.oell(sh+(-0.03*s,-0.03*s,0),el+(-0.02*s,0.03*s,0),0.035*s,0.03*s,m=m),0.02*s))    # biceps front
    P.append((f.ell(el+(0.05*s,0.005*s,-0.005*s),(0.022*s,0.03*s,0.02*s),m=m),0.012*s))          # olecranon
    P.append((g_seg(el,wr,0.038*s,0.02*s,m,1.15,0.8),0.02*s))                                     # radius
    fa=el+(wr-el)*0.55
    P.append((f.oell(el+(-0.012*s,-0.005*s,0.006*s),fa+(-0.006*s,0,0.004*s),0.04*s,0.033*s,up=(1,0,0),m=m),0.025*s))  # forearm belly front-lat
    P.append((f.oell(el+(0.02*s,-0.01*s,-0.004*s),fa+(0.012*s,0.02*s,0),0.03*s,0.025*s,up=(1,0,0),m=m),0.02*s))       # flexors back
    P.append((f.rbox(wr,(0.026*s,0.03*s,0.024*s),0.014*s,ax=tuple(wr-el),up=(1,0,0),m=m),0.012*s))                 # carpus
    P.append((f.sph(wr+(0.025*s,0.005*s,0),0.014*s,m=m),0.008*s))                                  # accessory carpal
    if hoof:
        fet=paw+(0.02*s,0.075*s,0)
        P.append((g_seg(wr,fet,0.019*s,0.02*s,m,1.3,0.7),0.01*s))
        P.append((f.cap(wr+(0.02*s,-0.03*s,0),fet+(0.022*s,0.012*s,0),0.008*s,0.009*s,m=m),0.01*s))  # flexor tendon
        hoofend(P,fet,paw,s,m)
    else:
        P.append((g_seg(wr,paw+(-0.02*s,0.03*s,0),0.02*s,0.019*s,m,1.2,0.85),0.01*s))
        P.append((f.cap(wr+(0.018*s,-0.02*s,0),paw+(0.0,0.04*s,0),0.007*s,0.006*s,m=m),0.008*s))
    _combine(f,P,0.09*s)
    if not hoof: pawpad(f,paw,s,m)

def hindleg(f,hip,kn,hk,fet,paw,s,m=True,hoof=False):
    global F_; F_=f
    hip,kn,hk,fet,paw=[np.asarray(p,float) for p in (hip,kn,hk,fet,paw)]
    P=[]
    P.append((f.ell(hip+(-0.06*s,0.03*s,-0.01*s),(0.035*s,0.03*s,0.03*s),m=m),0))                   # tuber coxae
    P.append((f.ell(hip+(0.12*s,0.0,-0.02*s),(0.03*s,0.03*s,0.03*s),m=m),0.03*s))                   # ischium
    P.append((g_seg(hip,kn,0.05*s,0.04*s,m),0.03*s))                                               # femur
    P.append((f.oell(hip+(-0.07*s,0.0,0),kn+(-0.025*s,0.04*s,0),0.085*s,0.07*s,up=(1,0,0),m=m),0.05*s))   # quadriceps front
    P.append((f.oell(hip+(0.11*s,0.0,0),kn+(0.075*s,-0.07*s,0),0.08*s,0.06*s,up=(1,0,0),m=m),0.05*s))     # hamstrings back
    P.append((f.oell(hip+(0.02*s,0.02*s,0.02*s),kn+(0.02*s,0.06*s,0.02*s),0.07*s,0.05*s,up=(1,0,0),m=m),0.04*s))  # lateral thigh
    P.append((f.ell(kn+(-0.03*s,0.0,0),(0.022*s,0.03*s,0.022*s),m=m),0.012*s))                   # patella
    P.append((g_seg(kn,hk,0.036*s,0.02*s,m,1.15,0.8),0.02*s))                                     # tibia
    gm=kn+(hk-kn)*0.45
    P.append((f.oell(kn+(0.035*s,-0.01*s,0),gm+(0.035*s,0,0),0.045*s,0.035*s,up=(1,0,0),m=m),0.03*s))  # gastrocnemius
    P.append((f.cap(gm+(0.04*s,0,0),hk+(0.04*s,0.015*s,0),0.012*s,0.009*s,m=m),0.015*s))         # achilles
    P.append((f.ell(hk+(0.04*s,0.012*s,0),(0.02*s,0.024*s,0.016*s),m=m),0.01*s))                  # calcaneus
    P.append((f.rbox(hk,(0.026*s,0.028*s,0.024*s),0.013*s,ax=tuple(fet-hk),up=(1,0,0),m=m),0.012*s))
    if hoof:
        P.append((g_seg(hk,fet,0.02*s,0.02*s,m,1.3,0.7),0.01*s))
        P.append((f.cap(hk+(0.03*s,-0.02*s,0),fet+(0.022*s,0.012*s,0),0.008*s,0.009*s,m=m),0.01*s))
        hoofend(P,fet,paw,s,m)
    else:
        P.append((g_seg(hk,fet,0.021*s,0.018*s,m,1.2,0.85),0.01*s))
        P.append((g_seg(fet,paw+(-0.02*s,0.03*s,0),0.018*s,0.019*s,m,1.2,0.9),0.01*s))
    _combine(f,P,0.1*s)
    if not hoof: pawpad(f,paw,s,m)

animals2.foreleg=foreleg; animals2.hindleg=hindleg
animals3.foreleg=foreleg; animals3.hindleg=hindleg

def torso_detail(f,sp,keel,s,tuck=None):
    """sp: list of spine points (front->back); keel: sternum point"""
    for i in range(len(sp)-1):
        f.add(f.cap(sp[i],sp[i+1],0.022*s,0.022*s),0.05*s)
    f.add(f.ell(keel,(0.08*s,0.05*s,0.04*s)),0.08*s)
    if tuck is not None: f.sub(f.ell(*tuck),0.1*s)

def ear(f,base,tip,w,th,out,m=True,k=0.02):
    """thick leaf ear: base centre, tip, base half-width w along 'out' dir, cupped inner"""
    base,tip,out=[np.asarray(p,float) for p in (base,tip,out)]
    a=base-out*w; b=base+out*w
    d=f.tri(a,b,tip,th,m=m)
    f.add(d,k)
    n=np.cross(b-a,tip-a); n=n/np.linalg.norm(n)
    c=(a+b+tip)/3
    if n[0]>0: n=-n          # cup faces forward (-x)
    sh=n*th*1.2
    f.sub(f.tri(a+(tip-a)*0.12+out*w*0.25+sh,b+(tip-b)*0.12-out*w*0.25+sh,tip+(base-tip)*0.12+sh,th*0.9,m=m),th*0.5)

def leafear(f,base,tip,w,fl,side,m=True):
    base,tip=np.asarray(base,float),np.asarray(tip,float)
    mid=base+(tip-base)*0.45
    f.add(smin(f.seg(base,mid,w*0.7,w,1.0,fl,up=side,m=m),f.seg(mid,tip,w,w*0.15,1.0,fl,up=side,m=m),w*0.5),w*0.5)
    sh=np.array([-w*fl*0.8,0,0])
    f.sub(smin(f.seg(base+(tip-base)*0.15+sh,mid+sh,w*0.5,w*0.8,1.0,fl*0.8,up=side,m=m),f.seg(mid+sh,tip+(base-tip)*0.1+sh,w*0.8,w*0.1,1.0,fl*0.8,up=side,m=m),w*0.4),w*0.15)

def canid_head(f,o,S):
    o=np.asarray(o,float)
    P=lambda x,y,z:o+np.array([x,y,z])*S
    R=lambda *r:tuple(np.array(r)*S)
    f.add(f.ell(P(0,0,0),R(0.11,0.09,0.09)),0.05*S)                              # cranium
    f.add(f.ell(P(0.03,-0.05,0.0),R(0.09,0.07,0.08)),0.05*S)                     # occiput/jaw hinge mass
    f.add(f.ell(P(-0.075,0.04,0.045),R(0.05,0.03,0.035),m=True),0.025*S)          # brow ridge
    f.add(f.ell(P(-0.06,-0.035,0.068),R(0.08,0.038,0.03),m=True),0.03*S)          # zygomatic arch
    f.add(f.ell(P(0.0,-0.05,0.065),R(0.06,0.05,0.03),m=True),0.035*S)             # masseter
    mz=f.rbox(P(-0.2,-0.02,0),R(0.12,0.045,0.042),0.03*S,ax=(1,0.12,0))           # muzzle box
    f.add(mz,0.05*S)
    f.add(f.ell(P(-0.16,0.025,0),R(0.08,0.02,0.035)),0.03*S)                     # nasal bridge
    f.add(f.ell(P(-0.315,-0.0,0),R(0.025,0.026,0.03)),0.012*S)                   # nose leather
    f.add(f.rbox(P(-0.17,-0.075,0),R(0.13,0.016,0.032),0.014*S,ax=(1,0.08,0)),0.025*S)  # lower jaw
    f.sub(f.cap(P(-0.3,-0.058,0.025),P(-0.06,-0.06,0.058),0.005*S,m=True),0.004*S)  # mouth slit
    f.sub(f.sph(P(-0.335,0.005,0.012),0.008*S,m=True),0.004*S)                    # nostrils
    f.sub(f.ell(P(-0.1,0.018,0.058),R(0.022,0.012,0.03),m=True),0.006*S)          # socket
    f.add(f.ell(P(-0.097,0.017,0.05),R(0.013,0.009,0.011),m=True),0.002*S)        # eyeball
    ear(f,P(0.02,0.075,0.055),P(0.035,0.22,0.085),0.045*S,0.008*S,(0.1,0.15,1.0),k=0.02*S)
    f.add(f.seg(P(0.04,0.08,0.055),P(0.04,0.2,0.08),0.03*S,0.004*S,1.0,1.0,up=(1,0,0),m=True),0.02*S)   # ear back cone

def wolf(f):
    global T; T=1.3
    f.add(f.oell((-0.6,0.8,0),(0.0,0.84,0),0.22,0.15))             # ribcage (narrow, deep)
    f.add(f.ell((-0.45,0.74,0),(0.24,0.22,0.15)),0.1)
    f.add(f.ell((-0.38,0.9,0),(0.26,0.12,0.15)),0.08)               # upper ribs wider top
    f.add(f.oell((0.0,0.82,0),(0.42,0.84,0),0.12,0.11),0.12)         # loin
    f.add(f.ell((0.42,0.84,0),(0.16,0.14,0.13)),0.08)               # croup
    f.add(f.ell((-0.4,0.98,0),(0.2,0.06,0.09)),0.06)                # withers
    f.sub(f.ell((0.2,0.5,0),(0.3,0.1,0.3)),0.12)                    # tuck-up
    torso_detail(f,[(-0.45,1.0,0),(-0.1,0.94,0),(0.2,0.9,0),(0.45,0.94,0)],(-0.62,0.62,0),1.0)
    # neck + ruff
    f.add(f.oell((-0.55,0.86,0),(-0.9,1.1,0),0.15,0.12),0.1)
    f.add(f.oell((-0.55,0.92,0),(-0.85,0.98,0),0.16,0.14),0.08)
    for i in range(6):   # ruff tufts
        a=i/5
        f.add(f.oell((-0.62-0.1*a,0.72+0.2*a,0.05),(-0.72-0.1*a,0.64+0.2*a,0.12),0.035,0.03,m=True),0.04)
    canid_head(f,(-0.95,1.12,0),1.3)
    foreleg(f,(-0.38,1.0,0.1),(-0.56,0.68,0.13),(-0.5,0.46,0.13),(-0.52,0.13,0.12),(-0.55,0.0,0.12),1.25)
    hindleg(f,(0.42,0.84,0.12),(0.32,0.52,0.14),(0.55,0.24,0.13),(0.53,0.08,0.12),(0.5,0.0,0.12),1.1)
    # tail: bone + fur volume tapered, tufted tip
    f.add(f.cap((0.55,0.9,0),(0.68,0.82,0),0.04,0.035),0.05)
    f.add(f.cap((0.66,0.84,0),(0.78,0.7,0),0.04,0.05),0.05)
    f.add(f.oell((0.7,0.78,0),(1.13,0.3,0),0.075,0.065,up=(1,1,0)),0.05)
    f.add(f.oell((0.95,0.5,0),(1.15,0.27,0),0.045,0.04,up=(1,1,0)),0.03)

ANIM=dict(animals3.ANIM)
def horse(f):
    global T; T=1.1
    animals3.horse(f)
    f.add(f.seg((-0.48,1.74,0),(-1.06,2.24,0),0.035,0.03,2.2,0.45,up=(-1,1,0)),0.05)     # mane volume
    for i in range(7):
        t=i/6; x=-0.5-0.55*t; y=1.74+0.48*t
        f.add(f.seg((x,y,0.0),(x+0.06,y-0.17,0.07),0.03,0.008,1.6,0.5,up=(1,0,0),m=True),0.03)   # mane locks falling right/left
def kangaroo(f):
    f.add(f.seg((0.13,0.6,0),(-0.04,1.18,0),0.2,0.12,1.05,0.82,up=(1,0,0)))
    f.add(f.ell((0.1,0.62,0),(0.2,0.2,0.18)),0.12)
    f.add(f.ell((0.2,0.72,0),(0.12,0.14,0.15)),0.08)
    f.add(f.ell((-0.06,1.1,0),(0.1,0.14,0.13)),0.08)
    f.add(f.ell((-0.11,1.05,0),(0.04,0.1,0.05)),0.06)
    f.add(f.ell((0.0,1.2,0.07),(0.05,0.06,0.04),m=True),0.06)
    f.sub(f.ell((-0.22,0.88,0),(0.06,0.12,0.2)),0.08)
    for i in range(6):
        t=i/5; f.add(f.sph((0.26-0.22*t,0.7+0.5*t,0),0.03),0.06)
    f.add(f.seg((-0.04,1.22,0),(-0.12,1.5,0),0.075,0.06,1.1,0.85,up=(1,0,0)),0.07)
    P,R=LP((-0.14,1.58,0),1.35)
    f.add(f.ell(P(0,0,0),R(0.085,0.075,0.07)),0.04)
    f.add(f.ell(P(-0.04,0.03,0.035),R(0.04,0.02,0.03),m=True),0.02)
    f.add(f.ell(P(-0.04,-0.035,0.05),R(0.055,0.03,0.025),m=True),0.02)
    f.add(f.rbox(P(-0.13,-0.03,0),R(0.09,0.04,0.035),0.025*1.35,ax=(1,0.2,0)),0.04)
    f.add(f.ell(P(-0.215,-0.035,0),R(0.025,0.028,0.032)),0.02)
    f.add(f.rbox(P(-0.12,-0.075,0),R(0.08,0.012,0.022),0.01*1.35,ax=(1,0.15,0)),0.02)
    f.sub(f.ell(P(-0.06,0.012,0.056),R(0.018,0.012,0.022),m=True),0.006)
    f.add(f.ell(P(-0.057,0.011,0.05),R(0.012,0.009,0.008),m=True),0.002)
    f.sub(f.sph(P(-0.24,-0.03,0.014),0.008,m=True),0.004)
    f.sub(f.cap(P(-0.22,-0.065,0),P(-0.11,-0.06,0.035),0.004,m=True),0.004)
    leafear(f,P(0.02,0.06,0.045),P(0.06,0.25,0.085),0.045*1.35,0.3,(0,0,1))
    f.add(f.seg((-0.07,1.16,0.11),(-0.17,0.98,0.15),0.045,0.035,1.2,0.8,up=(1,0,0),m=True),0.05)
    f.add(f.oell((-0.09,1.12,0.12),(-0.14,1.0,0.15),0.04,0.035,m=True),0.03)
    f.add(f.sph((-0.15,0.98,0.155),0.025,m=True),0.015)
    f.add(f.seg((-0.17,0.98,0.15),(-0.27,0.86,0.12),0.035,0.02,1.2,0.8,up=(1,0,0),m=True),0.02)
    f.add(f.oell((-0.18,0.97,0.15),(-0.24,0.9,0.13),0.035,0.03,m=True),0.02)
    f.add(f.ell((-0.28,0.85,0.12),(0.025,0.022,0.025),m=True),0.01)
    for dz in (-0.02,-0.007,0.007,0.02):
        f.add(f.seg((-0.29,0.845,0.12+dz*0.5),(-0.33,0.8,0.12+dz),0.009,0.003,1,1,m=True),0.006)
    hp=np.array([0.16,0.6,0.15]);kn=np.array([-0.1,0.36,0.17]);hk=np.array([0.21,0.07,0.15])
    L=[f.seg(hp,kn,0.08,0.06,1.2,0.75,up=(1,0,0),m=True),
       f.oell(hp+(-0.05,0.1,0),kn+(-0.03,0.05,0),0.16,0.12,up=(1,0,0),m=True),
       f.oell(hp+(0.12,0.08,-0.02),kn+(0.12,-0.04,0),0.12,0.1,up=(1,0,0),m=True),
       f.ell(kn+(-0.03,0,0),(0.03,0.035,0.03),m=True),
       f.seg(kn,hk,0.05,0.025,1.3,0.75,up=(1,0,0),m=True),
       f.oell(kn+(0.03,-0.02,0),kn+(hk-kn)*0.5+(0.04,0,0),0.05,0.04,up=(1,0,0),m=True),
       f.cap(kn+(hk-kn)*0.5+(0.045,0,0),hk+(0.045,0.02,0),0.013,0.01,m=True),
       f.ell(hk+(0.04,0.01,0),(0.025,0.028,0.022),m=True),
       f.seg(hk,(-0.18,0.03,0.15),0.03,0.022,0.9,1.0,up=(0,1,0),m=True),
       f.seg((-0.18,0.03,0.15),(-0.28,0.012,0.15),0.022,0.007,0.8,1.0,up=(0,1,0),m=True),
       f.seg((-0.1,0.025,0.12),(-0.2,0.012,0.115),0.014,0.005,0.8,1.0,up=(0,1,0),m=True)]
    d=L[0]
    for e in L[1:]: d=smin(d,e,0.03)
    f.add(d,0.1)
    f.add(f.seg((0.28,0.58,0),(0.6,0.24,0),0.1,0.065,1.0,0.85,up=(1,1,0)),0.08)
    f.add(f.seg((0.6,0.24,0),(1.25,0.035,0),0.065,0.018,1.0,0.85,up=(1,1,0)),0.05)
def crocodile(f):
    # torso: flat-topped, wide, belly sagging near ground; ribcage wider than waist
    f.add(f.seg((-0.85,0.27,0),(0.55,0.25,0),0.17,0.15,0.9,2.0,up=(0,1,0)))
    f.add(f.ell((-0.45,0.25,0),(0.4,0.15,0.36)),0.12)                     # ribcage
    f.add(f.ell((0.35,0.24,0),(0.3,0.15,0.32)),0.12)                      # hips
    f.add(f.ell((-0.1,0.15,0),(0.6,0.08,0.3)),0.1)                        # belly
    f.add(f.seg((-0.85,0.27,0),(-1.3,0.27,0),0.15,0.12,0.85,1.5,up=(0,1,0)),0.1)  # neck
    f.add(f.ell((-1.05,0.25,0.15),(0.12,0.08,0.08),m=True),0.08)            # neck/jaw muscle
    # tail: laterally compressed, tapering, double crest -> single
    f.add(f.seg((0.4,0.26,0),(1.4,0.24,0),0.15,0.1,1.15,0.85,up=(0,1,0)),0.12)
    f.add(f.seg((1.4,0.24,0),(2.55,0.2,0),0.1,0.015,1.4,0.6,up=(0,1,0)),0.06)
    # head: flat triangular skull table + long snout, separate lower jaw
    P,R=LP((-1.45,0.3,0),1.0)
    f.add(f.rbox(P(-0.02,0.0,0),R(0.16,0.07,0.17),0.05,ax=(1,0,0)),0.08)    # skull table
    sn=f.seg(P(-0.1,0.0,0),P(-0.88,-0.01,0),0.06,0.035,0.85,2.6,up=(0,1,0))
    f.add(sn,0.1)
    f.add(f.ell(P(-0.88,0.0,0),R(0.07,0.045,0.08)),0.04)                   # nose rosette
    f.add(f.seg(P(0.05,-0.06,0),P(-0.85,-0.06,0),0.05,0.025,0.6,2.8,up=(0,1,0)),0.03)  # lower jaw
    f.add(f.ell(P(0.08,-0.06,0.15),R(0.12,0.05,0.05),m=True),0.05)         # jaw hinge / pterygoid
    f.sub(f.cap(P(-0.9,-0.035,0.06),P(0.12,-0.035,0.19),0.006,m=True),0.005)       # mouth line
    for i in range(14):
        x=-0.86+i*0.07; z=0.06+0.12*(i/13)+(0.015 if i in (2,3,9) else 0)
        L=0.03 if i not in (3,9) else 0.05
        f.add(f.seg(P(x,-0.03,z),P(x+0.005,-0.03-L*(1 if i%2 else -0.6),z+0.006),0.007,0.002,1,1,m=True),0.003)
    f.add(f.ell(P(-0.08,0.07,0.09),R(0.06,0.045,0.045),m=True),0.025)       # orbit bosses
    f.sub(f.ell(P(-0.08,0.085,0.115),R(0.03,0.015,0.02),m=True),0.006)      # eye slit socket
    f.add(f.ell(P(-0.08,0.083,0.105),R(0.022,0.012,0.012),m=True),0.002)
    f.add(f.ell(P(-0.9,0.05,0.025),R(0.035,0.02,0.025),m=True),0.012)      # nostril bump
    f.sub(f.sph(P(-0.91,0.07,0.025),0.01,m=True),0.004)
    for i in range(6):  # snout ridges
        f.add(f.ell(P(-0.25-0.1*i,0.055,0.04),R(0.04,0.008,0.012),m=True),0.02)
    # scutes: paired keeled osteoderms, 4 rows on back, 2 rows tail -> 1
    for i in range(30):
        x=-1.15+i*0.12
        if x<0.55: yb=0.4+0.02*np.exp(-((x+0.3)/0.6)**2); rows=(0.05,0.14) if x>-0.9 else (0.05,)
        else: yb=0.38-0.06*(x-0.55); rows=(0.06,) if x<1.6 else (0.0,)
        for zz in rows:
            tz=0.035 if zz>0 else 0.025
            f.add(f.rbox((x,yb-0.01,zz),(0.045,0.03,tz),0.012,m=True),0.025)
            f.add(f.tri((x-0.04,yb+0.012,zz),(x+0.045,yb+0.012,zz),(x+0.025,yb+0.05+0.02*(x>0.55),zz),0.006,m=True),0.008)
    # sprawled limbs: elbow out, forearm down, splayed digits
    def leg(sh,el,wr,s,m=True,toes=5):
        sh,el,wr=[np.asarray(p,float) for p in (sh,el,wr)]
        P_=[f.seg(sh,el,0.08*s,0.055*s,1.3,0.8,up=(0,1,0),m=m),
            f.ell(el+(0.02*s,0.0,0.01*s),(0.04*s,0.045*s,0.04*s),m=m),
            f.seg(el,wr,0.05*s,0.03*s,1.1,0.85,up=(1,0,0),m=m),
            f.oell(el,el+(wr-el)*0.6+(-0.01*s,0,0),0.04*s,0.035*s,m=m),
            f.ell(wr+(-0.03*s,-0.005*s,0.0),(0.06*s,0.02*s,0.05*s),m=m)]
        for j,a in enumerate(np.linspace(-0.7,0.7,toes)):
            d=np.array([-np.cos(a),0,np.sin(a)])
            tip=wr+d*0.13*s*(1-0.25*abs(a))+(0,-0.015*s,0)
            P_.append(f.seg(wr+(-0.03*s,-0.005*s,0),tip,0.016*s,0.006*s,0.8,1.2,up=(0,1,0),m=m))
            P_.append(f.seg(tip,tip+d*0.025*s+(0,-0.008*s,0),0.006*s,0.002*s,1,1,m=m))
        d=P_[0]
        for e in P_[1:]: d=smin(d,e,0.02*s)
        f.add(d,0.08*s)
    leg((-0.65,0.25,0.25),(-0.6,0.24,0.45),(-0.68,0.03,0.5),1.35)
    leg((0.38,0.25,0.25),(0.55,0.27,0.48),(0.42,0.035,0.56),1.6)
ANIM['crocodile']=(crocodile,((-2.5,2.75),(0,0.75),(-0.8,0.8)))
ANIM['kangaroo']=(kangaroo,((-0.5,1.35),(0,1.95),(-0.35,0.35)))
ANIM['horse']=(horse,((-1.7,1.25),(0,2.5),(-0.5,0.5)))
ANIM['wolf']=(wolf,((-1.45,1.3),(0,1.45),(-0.4,0.4)))
if __name__=='__main__':
    import subprocess
    for a in sys.argv[1:]:
        fn,b=ANIM[a]; out=r'C:\lab3\%s.obj'%a
        build3(fn,out,b)
        subprocess.run(['python',r'C:\lab3\render.py',out,out[:-3]+'png'])
