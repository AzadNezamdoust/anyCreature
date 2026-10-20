from kit import *
# African bush elephant, BL = 1 (chest x=+0.5 .. buttock x=-0.5)
b = Body(kin=0.02)
st = [(0.50, 0.86, 0.56, 0.17), (0.32, 0.975, 0.44, 0.235), (0.10, 0.955, 0.415, 0.25), (-0.12, 0.925, 0.41, 0.245),
      (-0.32, 0.915, 0.47, 0.19), (-0.50, 0.80, 0.60, 0.12)]
torso(b, st, box=2.3, ridge=0.0)
blob(b, (0.33, 0.93, 0.13), (0.16, 0.08, 0.06), axis=(1, -1.5, 0), k=0.06, mirror=True)   # scapula mass
FZ, HZ = 0.16, 0.118
F = dict(shoulder=(0.38, 0.80, FZ), elbow=(0.335, 0.50, FZ), carpus=(0.36, 0.22, FZ), foot=(0.37, 0.0, FZ))
limb(b, [(0.37, 0.84, FZ * .7), F['shoulder'], F['elbow'], F['carpus'], (0.37, 0.09, FZ)], [0.10, 0.095, 0.072, 0.064, 0.075], k=0.06)
blob(b, (0.30, 0.52, FZ), (0.05, 0.06, 0.05), k=0.03, mirror=True)   # olecranon behind (elbow bends back)
pillar_foot(b, F['foot'], 0.078, 0.075, 0.10)
Hh = dict(hip=(-0.35, 0.81, HZ), stifle=(-0.30, 0.48, HZ + .01), hock=(-0.36, 0.25, HZ), foot=(-0.355, 0.0, HZ))
limb(b, [(-0.34, 0.82, HZ * .7), Hh['hip'], Hh['stifle'], Hh['hock'], (-0.355, 0.09, HZ)], [0.09, 0.095, 0.08, 0.066, 0.07], k=0.07)
blob(b, (-0.26, 0.49, HZ + .02), (0.04, 0.05, 0.04), k=0.03, mirror=True)   # patella forward
blob(b, (-0.41, 0.27, HZ), (0.035, 0.03, 0.03), k=0.02, mirror=True)        # heel point of hock behind
pillar_foot(b, Hh['foot'], 0.085, 0.065, 0.09, nails=4)
# head: high domed cranium, deep face, trunk, tusks, fan ears
blob(b, (0.62, 0.98, 0), (0.15, 0.19, 0.16), axis=(1, 0.3, 0), k=0.06)
blob(b, (0.74, 0.88, 0), (0.10, 0.16, 0.13), axis=(1, -0.6, 0), k=0.06)
blob(b, (0.66, 0.78, 0), (0.09, 0.05, 0.08), k=0.04)                 # lower jaw / lip
limb(b, [(0.50, 1.02, 0), (0.42, 0.97, 0)], [0.17, 0.2], k=0.08, mirror=False, flat=1.0)  # short thick neck
TR = [(0.82, 0.90, 0), (0.88, 0.70, 0), (0.92, 0.48, 0), (0.93, 0.28, 0), (0.95, 0.15, 0)]
b.group(loft(TR, [(0.095, 0.10), (0.075, 0.08), (0.06, 0.062), (0.045, 0.048), (0.035, 0.036)], up=(1, 0, 0), sub=4), 0, 0.05)
for i in range(14):   # trunk rings
    t = 0.12 + 0.8 * i / 13; P = catmull(TR, 6); p = P[int(t * (len(P) - 1))]
    blob(b, p, (0.012, 0.004, 0.05), axis=(0, 1, 0), up=(1, 0, 0), k=0.006, sub=True)
TU = [(0.80, 0.74, 0.07), (0.95, 0.56, 0.09), (1.07, 0.55, 0.075)]
b.group(loft(TU, [(0.03, 0.03), (0.024, 0.024), (0.008, 0.008)], up=(1, 0, 0), sub=4), 0, 0.01, mirror=True)
blob(b, (0.80, 0.76, 0.07), (0.05, 0.04, 0.04), k=0.03, mirror=True)  # tusk sheath (upper jaw)
blob(b, (0.48, 0.93, 0.225), (0.18, 0.21, 0.022), axis=(1, 0, 0.3), k=0.012, mirror=True)  # ear plate
blob(b, (0.45, 0.78, 0.23), (0.12, 0.10, 0.018), axis=(1, 0, 0.25), k=0.03, mirror=True)  # drooping lower lobe
blob(b, (0.74, 0.97, 0.145), (0.012, 0.01, 0.01), k=0.004, mirror=True)  # eye
T = [(-0.49, 0.83, 0), (-0.55, 0.62, 0), (-0.57, 0.40, 0), (-0.58, 0.22, 0)]
tail(b, T, 0.035, 0.012, k=0.03)
pts = dict(bl0=(0.50, 0.7, 0), bl1=(-0.50, 0.7, 0), forehead=(0.83, 0.98, 0), occiput=(0.50, 1.05, 0), head_top=(0.62, 1.17, 0), jaw_low=(0.66, 0.73, 0),
           trunk0=TR[0], trunk1=TR[1], trunk2=TR[2], trunk3=TR[3], withers_front=(0.42, 0.99, 0), withers=(0.32, 0.975, 0), croup=(-0.32, 0.915, 0),
           girth=(0.18, 0.7, 0), belly=(0.0, 0.41, 0), shoulder=F['shoulder'], elbow=F['elbow'], carpus=F['carpus'], carpus_low=(0.36, 0.095, FZ),
           ffoot=(0.37, 0.04, FZ), hip=Hh['hip'], stifle=Hh['stifle'], hock=Hh['hock'], hfoot=(-0.355, 0.04, HZ), fcol=(0.35, 0.36, FZ),
           tail0=T[0], tail1=T[1], tail2=(-0.58, 0.22, 0), tailg=(-0.545, 0.64, 0), hipx=(-0.35, 0.8, 0), ear_top=(0.47, 1.14, 0.2), ear_bot=(0.47, 0.68, 0.2),
           ear_front=(0.65, 0.91, 0.2), ear_back=(0.29, 0.91, 0.2), tusk0=TU[0], tusk1=TU[1], tusk2=TU[2])
export(b, 'elephant', pts, values=dict(ear_area=float(np.pi * 0.18 * 0.23)))
