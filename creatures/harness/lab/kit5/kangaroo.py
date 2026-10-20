from kit import *
# red kangaroo resting on the hind-foot + tail tripod. BL = chest point -> buttock along the spine (1.0)
b = Body(kin=0.012)
BT = V(-0.30, 0.75, 0); AX = V(np.sin(np.radians(40)), np.cos(np.radians(40)), 0); BC = BT + AX * 1.0   # spine 40 deg from vertical
S = [BT + V(0.02, 0.02, 0), BT + AX * 0.25 + V(0.03, -0.03, 0), BT + AX * 0.5 + V(0.04, -0.03, 0), BT + AX * 0.78 + V(0.02, -0.01, 0), BC - AX * 0.02]
b.group(loft(S, [(0.20, 0.17, 0.0, 2.2), (0.235, 0.19, -0.02, 2.2), (0.22, 0.155, -0.04, 2.2), (0.20, 0.15, -0.02, 2.2), (0.12, 0.11, 0, 2.2)], up=(-AX[1], AX[0], 0), sub=5), 0, 0)
# neck + head (long narrow muzzle), big upright ears
OC = V(0.40, 1.82, 0); SN = V(0.755, 1.72, 0)
limb(b, [BC - AX * 0.05, lerp(BC, OC, .5) + V(0.03, 0, 0), OC + V(0.02, -0.04, 0)], [0.12, 0.085, 0.075], k=0.05, mirror=False)
H = Head(OC, 16, 0.335)
skull(b, H, cranium_w=0.30, cranium_h=0.30, muzzle_w=0.14, muzzle_h=0.17, jaw_depth=0.17, eye_r=0.05, eye_at=0.36, stop=0.02, nose='dog', s0=0.08)
ear(b, H.P(0.10, 0.10, 0.08), H.P(-0.06, 0.78, 0.14), 0.07, thick=0.008, out=(0.8, 0, 0.6), cup=0.8)
# hind limbs: massive thigh, long tibia, foot flat on ground heel->toe
Hh = dict(hip=V(-0.12, 0.92, 0.14), knee=V(0.30, 0.70, 0.17), heel=V(-0.15, 0.04, 0.12), mtp=V(0.33, 0.02, 0.12), htoe=V(0.54, 0.01, 0.12))
b.add(f_ell(lerp(Hh['hip'], Hh['knee'], .45) + V(-0.04, -0.03, 0.0), Hh['knee'] - Hh['hip'], (0, 1, 0), (0.30, 0.165, 0.12)), k=0.06, mirror=True)  # thigh mass
limb(b, [Hh['knee'], lerp(Hh['knee'], Hh['heel'], .3) + V(-0.03, 0, 0), lerp(Hh['knee'], Hh['heel'], .75), Hh['heel'] + V(0, 0.03, 0)], [0.075, 0.075, 0.045, 0.04], k=0.04)
b.add(f_ell(lerp(Hh['knee'], Hh['heel'], .3) + V(-0.06, 0.0, 0), Hh['heel'] - Hh['knee'], (1, 0, 0), (0.16, 0.06, 0.05)), k=0.03, mirror=True)   # calf
limb(b, [Hh['heel'] + V(-0.02, 0.03, 0), Hh['mtp'] + V(0, 0.025, 0), Hh['htoe'] + V(0, 0.015, 0)], [0.045, 0.04, 0.022], k=0.025, up=(0, 1, 0), flat=1.25)
b.add(f_seg(Hh['htoe'] + V(0, 0.015, 0), Hh['htoe'] + V(0.04, 0.0, 0), (0.012, 0.012, 0, 2), (0.002, 0.002, 0, 2), up=(0, 1, 0)), k=0.004, mirror=True)
# tail: thick base, tapering, resting on the ground (third leg)
T = [V(-0.33, 0.72, 0), V(-0.55, 0.35, 0), V(-0.85, 0.11, 0), V(-1.20, 0.045, 0)]
b.group(loft(T, [(0.145, 0.132, 0, 2.1), (0.10, 0.09, 0, 2.1), (0.06, 0.055, 0, 2.1), (0.03, 0.028, 0, 2.1)], up=(0, 1, 0), sub=5), 0, 0.06)
# forelimbs: small, held bent against the chest, 5 clawed fingers
F = dict(shoulder=V(0.25, 1.35, 0.12), elbow=V(0.30, 1.08, 0.15), wrist=V(0.57, 1.12, 0.12), ftoe=V(0.66, 1.01, 0.12))
limb(b, [F['shoulder'], F['elbow'], F['wrist']], [0.05, 0.035, 0.022], k=0.03)
for i in range(5):
    zz = (i - 2) * 0.012; tip = F['ftoe'] + V(0, 0, zz)
    limb(b, [F['wrist'], lerp(F['wrist'], tip, .5) + V(0.01, 0, zz * .5), tip], [0.012, 0.009, 0.005], k=0.004)
blob(b, (0.13, 0.80, 0), (0.15, 0.15, 0.12), axis=AX, k=0.07)   # pouch / lower belly
pts = dict(bl0=BC, bl1=BT, snout=SN, occiput=OC, stop=H.P(0.45, -0.1), head_top=H.P(0.2, 0.2), jaw_low=H.P(0.3, -0.45), ear_base=H.P(0.10, 0.10, 0.08), ear_tip=H.P(-0.06, 0.78, 0.14),
           neck0=BC, crown=V(0.40, 1.87, 0), hip=Hh['hip'], shoulder=F['shoulder'], belly_low=V(0.10, 0.6, 0), elbow=F['elbow'], wrist=F['wrist'], ftoe=F['ftoe'],
           knee=Hh['knee'], heel=Hh['heel'], mtp=Hh['mtp'], htoe=Hh['htoe'], tail0=T[0], tail1=T[1], tail2=T[2], tail3=T[3], tailg=V(-0.45, 0.52, 0), girth=V(0.15, 1.2, 0), rib_lo=V(0.15, 1.15, 0), rib_hi=V(0.15, 1.45, 0))
export(b, 'kangaroo', pts, values=dict(chest_depth=0.44, thigh_w=0.33, hip_w=0.42, tail_h=0.29), bl_len=1.0)
