from kit import *
# bullfrog, sitting. BL = snout-vent length: snout x=+0.5, vent x=-0.5
b = Body(kin=0.01)
st = [(0.50, 0.25, 0.17, 0.05), (0.42, 0.31, 0.12, 0.14), (0.30, 0.345, 0.13, 0.20), (0.18, 0.395, 0.08, 0.22), (0.02, 0.43, 0.04, 0.285),
      (-0.20, 0.50, 0.02, 0.30), (-0.34, 0.45, 0.03, 0.24), (-0.50, 0.24, 0.05, 0.09)]
torso(b, st, box=2.2, ridge=0)
for sg in (1,):   # dorsolateral folds
    cord(b, [(0.12, 0.40, 0.17), (-0.05, 0.45, 0.20), (-0.25, 0.47, 0.19), (-0.40, 0.38, 0.14)], 0.012, 0.02)
blob(b, (-0.22, 0.47, 0), (0.10, 0.04, 0.08), k=0.04)   # sacral hump
# mouth line, eyes, tympanum
groove(b, [(0.49, 0.20, 0.04), (0.38, 0.19, 0.14), (0.22, 0.19, 0.20), (0.12, 0.22, 0.215)], 0.008, 0.01)
EY = (0.22, 0.40, 0.105)
blob(b, EY, (0.062, 0.06, 0.058), k=0.015, mirror=True)
blob(b, (0.235, 0.405, 0.135), (0.035, 0.035, 0.03), k=0.005, mirror=True)   # cornea bulge
blob(b, (0.24, 0.43, 0.08), (0.05, 0.012, 0.04), axis=(1, 0, 0), k=0.01, mirror=True)  # upper lid
blob(b, (0.09, 0.30, 0.215), (0.05, 0.05, 0.012), k=0.006, mirror=True)        # tympanum disc
blob(b, (0.09, 0.30, 0.228), (0.042, 0.042, 0.008), k=0.004, mirror=True, sub=True)
blob(b, (0.48, 0.26, 0.03), (0.01, 0.008, 0.008), k=0.004, mirror=True, sub=True)  # nostril
# forelimbs: short, forearms down-forward, 4 unwebbed fingers
F = dict(shoulder=(0.12, 0.18, 0.18), elbow=(-0.03, 0.06, 0.29), wrist=(0.18, 0.03, 0.33), ftoe=(0.41, 0.01, 0.38))
limb(b, [F['shoulder'], F['elbow'], F['wrist']], [0.05, 0.04, 0.025], k=0.04, up=(0, 1, 0))
for zz, L in ((-0.06, 0.17), (-0.02, 0.23), (0.03, 0.22), (0.07, 0.15)):
    tip = V(F['wrist'][0] + L, 0.012, F['wrist'][2] + zz * 2.0)
    limb(b, [F['wrist'], lerp(F['wrist'], tip, .5) + V(0, 0.01, 0), tip], [0.016, 0.012, 0.01], k=0.008, up=(0, 1, 0))
    blob(b, tip, (0.014, 0.01, 0.014), k=0.004, mirror=True)
# hind limbs: Z fold, knee out-forward beside the flank, heel at the vent, long webbed foot
Hh = dict(hip=(-0.42, 0.18, 0.13), knee=(-0.28, 0.32, 0.54), heel=(-0.47, 0.10, 0.10), tarsus_end=(-0.22, 0.03, 0.18), htoe=(0.27, 0.012, 0.30))
limb(b, [Hh['hip'], lerp(Hh['hip'], Hh['knee'], .45) + V(0, 0.02, 0), Hh['knee']], [0.085, 0.07, 0.04], k=0.03, up=(0, 1, 0))
limb(b, [Hh['knee'], lerp(Hh['knee'], Hh['heel'], .4) + V(0, 0.0, 0.03), Hh['heel']], [0.035, 0.045, 0.025], k=0.012, up=(0, 1, 0))
limb(b, [Hh['heel'], Hh['tarsus_end']], [0.03, 0.025], k=0.02, up=(0, 1, 0))
te = np.asarray(Hh['tarsus_end'])
toes = [(0.30, 0.10), (0.40, 0.04), (0.495, -0.02), (0.42, -0.08), (0.30, -0.13)]   # (length, z offset at tip)
tips = []
for L, dz in toes:
    tip = V(te[0] + L, 0.012, te[2] + 0.12 + dz * 1.4); tips.append(tip)
    limb(b, [te, lerp(te, tip, .5) + V(0, 0.012, 0), tip], [0.016, 0.012, 0.009], k=0.006, up=(0, 1, 0))
    blob(b, tip, (0.012, 0.008, 0.012), k=0.003, mirror=True)
for i in range(4):   # webbing between toes
    b.add(f_tri(te + V(0.02, 0.008, 0), tips[i] - (tips[i] - te) * 0.12 + V(0, -0.002, 0), tips[i + 1] - (tips[i + 1] - te) * 0.12 + V(0, -0.002, 0), 0.0075), k=0.006, mirror=True)
pts = dict(bl0=(0.5, 0.2, 0), bl1=(-0.5, 0.2, 0), snout=(0.515, 0.21, 0), occiput=(0.16, 0.36, 0), headw=(0.20, 0.0, 0), headw_lo=(0.20, 0.12, 0), headw_hi=(0.20, 0.6, 0), headh=(0.36, 0.2, 0),
           eye_top=(0.22, 0.46, 0.105), skull_top=(0.22, 0.40, 0.0), sacrum=(-0.22, 0.51, 0), bodyw=(-0.12, 0.2, 0), belly_ref=(0, 0.0, 0), belly=(-0.05, 0.02, 0),
           shoulder=F['shoulder'], elbow=F['elbow'], wrist=F['wrist'], ftoe=F['ftoe'], hip=Hh['hip'], knee=Hh['knee'], heel=Hh['heel'],
           tarsus_end=Hh['tarsus_end'], htoe=tips[2])
export(b, 'frog', pts, values=dict(eye_d=0.12, tymp_d=0.10, interorb=0.09))
