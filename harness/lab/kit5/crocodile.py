from kit import *
# Nile crocodile resting belly-down. BL = back of skull (x=+0.5) -> vent (x=-0.5)
b = Body(kin=0.01)
st = [(0.47, 0.16, 0.03, 0.12), (0.30, 0.225, 0.0, 0.18), (0.05, 0.235, -0.02, 0.215), (-0.20, 0.232, -0.02, 0.205),
      (-0.40, 0.225, -0.01, 0.165), (-0.55, 0.215, 0.0, 0.12)]
torso(b, st, box=2.6, ridge=0)
# tail: oval-tall, laterally flattened, tapering
TP = [(-0.50, 0.12, 0), (-0.95, 0.10, 0.05), (-1.40, 0.07, 0.03), (-1.88, 0.045, -0.05)]
b.group(loft(TP, [(0.135, 0.105, 0, 2.2), (0.10, 0.06, 0, 2.2), (0.065, 0.03, 0, 2.2), (0.03, 0.01, 0, 2.2)], up=(0, 1, 0), sub=6), 0, 0.05)
# dorsal scutes: double row on trunk and first 40% of tail, single keel after
P = catmull(TP, 12)
for i in range(0, len(P) - 2, 2):
    t = i / (len(P) - 1); p = P[i]; r = (np.interp(t, [0, 1/3, 2/3, 1], [0.135, 0.10, 0.065, 0.03]), np.interp(t, [0, 1/3, 2/3, 1], [0.105, 0.06, 0.03, 0.01]))
    if t < 0.4:
        for sg in (1, -1): blob(b, p + V(0, r[0] * 0.9, sg * r[1] * 0.4), (0.025, 0.02 * (1 - t) + 0.006, 0.008), k=0.01)
    else:
        blob(b, p + V(0, r[0] * 0.88, 0), (0.03, 0.03 * (1.15 - t), 0.006), k=0.01)
for x in np.arange(0.38, -0.5, -0.06):   # back osteoderm rows
    for z in (0.04, 0.09, 0.14):
        blob(b, (x, 0.232 - 0.15 * (z / 0.2) ** 2 * 0.3, z), (0.022, 0.012, 0.016), k=0.005, mirror=True)
# head: flat wide skull, V-tapering snout, skull table
HY = 0.07
hp = [(0.47, HY, 0), (0.55, HY, 0), (0.70, HY - 0.005, 0), (0.85, HY - 0.01, 0), (0.93, HY - 0.012, 0)]
b.group(loft(hp, [(0.06, 0.125, 0, 2.6), (0.055, 0.12, 0, 2.6), (0.04, 0.09, 0, 2.5), (0.033, 0.065, 0, 2.4), (0.03, 0.08, 0, 2.2)], up=(0, 1, 0), sub=4), 0, 0.03)
b.group(loft([(0.47, 0.09, 0), (0.55, 0.11, 0)], [(0.04, 0.11), (0.03, 0.10)], sub=2), 0, 0.03)   # neck/skull table
b.sub(f_seg((0.56, HY - 0.008, 0), (0.95, HY - 0.012, 0), (0.0035, 0.2, 0, 3), (0.0035, 0.2, 0, 3), up=(0, 1, 0)), k=0.002)  # mouth line
for x in np.arange(0.57, 0.92, 0.025):   # teeth along both jaws (visible, closed mouth)
    w = np.interp(x, [0.55, 0.70, 0.85, 0.93], [0.12, 0.09, 0.065, 0.07])
    b.add(f_seg((x, HY - 0.005, w * 0.92), (x, HY - 0.03, w * 0.95), (0.006, 0.006, 0, 2), (0.001, 0.001, 0, 2), up=(1, 0, 0)), k=0.002, mirror=True)
b.add(f_seg((0.885, HY - 0.012, 0.062), (0.885, HY + 0.03, 0.067), (0.008, 0.008, 0, 2), (0.001, 0.001, 0, 2), up=(1, 0, 0)), k=0.002, mirror=True)  # 4th lower tooth in notch
blob(b, (0.58, HY + 0.07, 0.045), (0.03, 0.022, 0.022), k=0.012, mirror=True)   # eye bulge on skull table
blob(b, (0.92, HY + 0.035, 0.018), (0.02, 0.012, 0.012), k=0.01, mirror=True)   # nostril mound
# limbs (left; mirrored): sprawled, low
F = dict(shoulder=(0.35, 0.12, 0.15), elbow=(0.33, 0.10, 0.295), wrist=(0.40, 0.02, 0.36), ftoe=(0.50, 0.01, 0.40))
limb(b, [F['shoulder'], F['elbow'], F['wrist']], [0.045, 0.035, 0.022], k=0.03, up=(0, 1, 0))
Hh = dict(hip=(-0.40, 0.12, 0.15), knee=(-0.33, 0.13, 0.335), ankle=(-0.43, 0.06, 0.44), htoe=(-0.25, 0.01, 0.52))
limb(b, [Hh['hip'], Hh['knee'], Hh['ankle']], [0.07, 0.045, 0.028], k=0.04, up=(0, 1, 0))
def digits(base, tips, r, claws):
    for i, tp in enumerate(tips):
        limb(b, [base, lerp(base, tp, .6) + V(0, 0.008, 0), tp], [r, r * .8, r * .45], k=0.012, up=(0, 1, 0))
        if i < claws: b.add(f_seg(tp, np.asarray(tp) + V(0.012, -0.006, 0), (r * .4, r * .4, 0, 2), (0.001, 0.001, 0, 2), up=(0, 1, 0)), k=0.003, mirror=True)
digits(F['wrist'], [(0.48, 0.012, 0.32), (0.50, 0.012, 0.36), (0.50, 0.012, 0.40), (0.47, 0.012, 0.44), (0.43, 0.012, 0.46)], 0.011, 3)
digits(Hh['ankle'], [(-0.29, 0.012, 0.44), (-0.26, 0.012, 0.49), (-0.25, 0.012, 0.52), (-0.28, 0.012, 0.56)], 0.013, 3)
blob(b, (-0.31, 0.012, 0.50), (0.04, 0.003, 0.05), k=0.008, mirror=True)   # web between hind toes
pts = dict(bl0=(0.5, 0.1, 0), bl1=(-0.5, 0.1, 0), snout=(0.96, HY, 0), occiput=(0.5, HY, 0), headmid=(0.62, HY, 0), jawjoint=(0.53, HY, 0),
           snoutw=(0.93, HY - 0.01, 0), shoulder_c=(0.35, 0.12, 0), withers=(0.30, 0.225, 0), croup=(-0.40, 0.225, 0), girth=(0.05, 0.1, 0),
           belly=(0.0, 0.01, 0), hipx=(-0.49, 0.1, 0), shoulder=F['shoulder'], elbow=F['elbow'], wrist=F['wrist'], ftoe=F['ftoe'],
           hip=Hh['hip'], knee=Hh['knee'], ankle=Hh['ankle'], htoe=Hh['htoe'], vent=TP[0], tail1=TP[1], tail2=TP[2], tail3=(-1.90, 0.045, -0.05),
           tailg=(-0.62, 0.12, 0), eye_top=(0.58, HY + 0.092, 0.045), skull_table=(0.58, HY + 0.065, 0))
export(b, 'crocodile', pts, values=dict(keel_merge=0.4))
