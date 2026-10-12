from kit import *
# sulcata-type tortoise, standing, head out. BL = straight carapace length: front x=+0.5, rear x=-0.5
b = Body(kin=0.01)
Y0, HH, LL, WW = 0.14, 0.48, 0.5, 0.37
def surf(x, z, lift=0.0):
    q = max(1 - (x / LL) ** 2 - (z / WW) ** 2, 0.0); return V(x, Y0 + HH * np.sqrt(q) + lift, z)
# carapace dome (upper half of an ellipsoid, slightly boxy) cut flat at the marginal line
dome = f_seg(V(LL - 0.01, Y0, 0), V(-LL + 0.01, Y0, 0), (HH, WW, 0, 2.15), (HH, WW, 0, 2.15), up=(0, 1, 0))
b.add(f_ell(V(0, Y0, 0), (1, 0, 0), (0, 1, 0), (LL, HH, WW)), k=0.0)
b.sub(f_box(V(0, Y0 - 0.25, 0), (0.7, 0.25, 0.6), (1, 0, 0), (0, 1, 0)), k=0.0)
# marginal rim: flared skirt, lifted over the neck (nuchal) and over the tail
for i in range(48):
    a = 2 * np.pi * i / 48; c, s = np.cos(a), np.sin(a)
    flare = 0.05 * max(c, 0) ** 4 + 0.03 * max(-c, 0) ** 6
    p = V(LL * 1.01 * c, Y0 + 0.02 + flare, WW * 1.02 * s)
    blob(b, p, (0.05, 0.022, 0.035), axis=(-s, 0, c), k=0.012)
# plastron
blob(b, (0.0, Y0 + 0.01, 0), (0.435, 0.03, 0.30), k=0.03)
# scute seams: 5 vertebrals, 4 costals per side, 11 marginals per side
vx = np.linspace(0.40, -0.40, 6)
for x in vx:   # vertebral / costal transverse seams
    groove(b, [surf(x, -0.27, 0.004), surf(x, -0.1, 0.004), surf(x, 0.0, 0.004), surf(x, 0.1, 0.004), surf(x, 0.27, 0.004)], 0.008, 0.006, normal=(0, 1, 0), mirror=False)
for sg in (1, -1):
    groove(b, [surf(x, sg * 0.10, 0.004) for x in np.linspace(0.42, -0.42, 9)], 0.008, 0.006, normal=(0, 1, 0), mirror=False)          # vertebral/costal border
    groove(b, [surf(x, sg * 0.31, 0.004) for x in np.linspace(0.36, -0.36, 9)], 0.008, 0.006, normal=(0, 0, sg), mirror=False)         # costal/marginal border
    for x in np.linspace(0.30, -0.30, 3):   # costal divisions (4 costals per side)
        groove(b, [surf(x, sg * 0.10, 0.004), surf(x * 1.05, sg * 0.21, 0.004), surf(x * 1.1, sg * 0.31, 0.004)], 0.008, 0.006, normal=(0, 1, 0), mirror=False)
    for j in range(12):   # marginal divisions: 11 marginals per side + nuchal
        a = np.radians(8 + 164 * j / 11); c, s = np.cos(a), np.sin(a) * sg
        p0 = V(LL * 0.93 * c, Y0 + 0.07, WW * 0.93 * s); p1 = V(LL * 1.06 * c, Y0 + 0.01, WW * 1.06 * s)
        groove(b, [p0, lerp(p0, p1, .5) + V(0, 0.01, 0), p1], 0.007, 0.005, normal=(c, 0.3, s), mirror=False)
# growth rings: one inset ring on each vertebral scute
for i in range(5):
    xc = (vx[i] + vx[i + 1]) / 2
    groove(b, [surf(xc + 0.05, 0.0, 0.003), surf(xc, 0.05, 0.003), surf(xc - 0.05, 0.0, 0.003), surf(xc, -0.05, 0.003), surf(xc + 0.05, 0.0, 0.003)], 0.004, 0.004, normal=(0, 1, 0), mirror=False)
# neck + small blunt beaked head
NK0, OC, SN = V(0.40, 0.25, 0), V(0.70, 0.43, 0), V(0.91, 0.385, 0)
limb(b, [NK0, V(0.56, 0.31, 0), OC], [0.075, 0.062, 0.058], k=0.03, mirror=False)
blob(b, (0.78, 0.42, 0), (0.095, 0.068, 0.068), axis=(1, -0.25, 0), k=0.03)
blob(b, (0.855, 0.40, 0), (0.06, 0.06, 0.058), axis=(1, -0.4, 0), k=0.03)
b.sub(f_seg(V(0.76, 0.38, 0), V(0.93, 0.375, 0), (0.003, 0.08, 0, 3), (0.003, 0.08, 0, 3), up=(0, 1, 0)), k=0.002)   # beak line
blob(b, (0.78, 0.445, 0.055), (0.018, 0.018, 0.012), k=0.004, mirror=True)   # eye
# forelimbs: flattened armoured columns, elbow bent so the foot plants forward
F = dict(shoulder=(0.30, 0.22, 0.16), elbow=(0.43, 0.24, 0.29), fwrist=(0.45, 0.07, 0.30))
b.group(loft([F['shoulder'], F['elbow'], F['fwrist'], (0.46, 0.0, 0.30)], [(0.06, 0.05, 0, 2.2), (0.08, 0.05, 0, 2.4), (0.085, 0.05, 0, 2.6), (0.09, 0.055, 0, 2.6)], up=(1, 0, 0), sub=4), 0, 0.03, mirror=True)
for yy in (0.10, 0.15, 0.20):
    for dx in (-0.04, 0.0, 0.04):
        blob(b, (0.45 + dx + 0.05, yy, 0.30), (0.025, 0.02, 0.01), axis=(0, 0, 1), up=(0, 1, 0), k=0.004, mirror=True)  # large front scales
pillar_foot(b, (0.46, 0.0, 0.30), 0.08, 0.06, 0.07, nails=5)
# hind limbs: round pillars
Hh = dict(hip=(-0.30, 0.20, 0.18), knee=(-0.44, 0.22, 0.29), hankle=(-0.44, 0.085, 0.29))
limb(b, [Hh['hip'], Hh['knee'], Hh['hankle'], (-0.44, 0.0, 0.29)], [0.06, 0.065, 0.06, 0.06], k=0.03)
pillar_foot(b, (-0.44, 0.0, 0.29), 0.06, 0.06, 0.06, nails=4)
limb(b, [(-0.46, 0.16, 0), (-0.58, 0.11, 0)], [0.042, 0.008], k=0.02, mirror=False)   # tail
pts = dict(bl0=(0.5, 0.2, 0), bl1=(-0.5, 0.2, 0), shellmid=(0.0, 0.2, 0), shell_lo=(0.0, Y0, 0), shell_top=(0.0, Y0 + HH, 0), plas0=(0.435, Y0, 0), plas1=(-0.435, Y0, 0),
           snout=SN, occiput=OC, headmid=V(0.79, 0.42, 0), neck0=NK0, shoulder=F['shoulder'], elbow=F['elbow'], fwrist=F['fwrist'], fexp=(0.42, 0.23, 0.30),
           fcol=(0.44, 0.13, 0.30), hip=Hh['hip'], knee=Hh['knee'], hankle=Hh['hankle'], hfoot=(-0.44, 0.03, 0.29), hexp=(-0.44, 0.18, 0.29),
           tail0=(-0.46, 0.16, 0), tail1=(-0.58, 0.11, 0), tailg=(-0.52, 0.15, 0), hipx=(-0.26, 0.17, 0))
export(b, 'tortoise', pts)
