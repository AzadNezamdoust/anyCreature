from kit import *
# bald eagle perched on a post. BL = breast (neck base) -> vent along the body axis. Perch top at Y0.
b = Body(kin=0.012)
Y0 = 0.30
def Q(x, y, z=0.0): return V(x, y + Y0, z)
B0, B1 = Q(0.30, 1.15), Q(-0.40, 0.44)          # breast/neck base, vent ; axis 45 deg from vertical
ax = nrm(B1 - B0); C = lerp(B0, B1, 0.45)
b.add(f_ell(C, ax, (1, 1, 0), (0.60, 0.27, 0.18)), k=0.02)                       # body: deep keel-chest
blob(b, lerp(B0, B1, 0.2) + V(0.07, -0.02, 0), (0.25, 0.20, 0.15), axis=ax, k=0.08)   # breast mass
# post / stump (ground to perch)
limb(b, [V(0.03, 0.0, 0), V(0.03, Y0 - 0.02, 0)], [0.17, 0.16], k=0.0, mirror=False, up=(1, 0, 0))
# neck + head
OC = Q(0.45, 1.34)
limb(b, [B0 + V(-0.02, -0.03, 0), lerp(B0, OC, .5) + V(0.03, 0, 0), OC], [0.17, 0.13, 0.11], k=0.06, mirror=False)
HC = Q(0.58, 1.37)
blob(b, HC, (0.16, 0.10, 0.12), axis=(1, -0.15, 0), k=0.06)
blob(b, Q(0.61, 1.425, 0.065), (0.07, 0.025, 0.035), axis=(1, -0.1, 0), k=0.02, mirror=True)   # brow ridge
blob(b, Q(0.63, 1.39, 0.095), (0.034, 0.034, 0.02), k=0.005, mirror=True)                       # eye (forward set)
CERE, TIP = Q(0.71, 1.36), Q(0.84, 1.26)
b.group(loft([CERE, Q(0.78, 1.36), Q(0.84, 1.32), TIP], [(0.045, 0.04, 0, 2.2), (0.04, 0.03, 0, 2.2), (0.025, 0.018, 0, 2.2), (0.005, 0.005, 0, 2)], up=(0, 1, 0), sub=4), 0, 0.02)
b.group(loft([Q(0.71, 1.31), Q(0.79, 1.30)], [(0.02, 0.035), (0.01, 0.02)], up=(0, 1, 0)), 0, 0.01)   # lower mandible
b.sub(f_seg(Q(0.65, 1.325), Q(0.82, 1.31), (0.004, 0.08, 0, 3), (0.003, 0.05, 0, 3), up=(0, 1, 0)), k=0.002)  # gape line
# legs: feathered trousers over tibia, bare scaled tarsus, big toes + talons
LZ = 0.10
KN, AN, FT, TE = Q(-0.01, 0.70, LZ), Q(0.04, 0.345, LZ), V(0.08, Y0 + 0.02, LZ), Q(0.06, 0.24, LZ)
limb(b, [Q(-0.04, 0.55, LZ * .6), KN, lerp(KN, AN, .6), TE], [0.10, 0.10, 0.075, 0.045], k=0.05)    # trousers
limb(b, [lerp(KN, AN, .6), AN, FT + V(0, 0.02, 0)], [0.028, 0.026, 0.028], k=0.01)                  # tarsus
def toe(a, tip, r):
    limb(b, [a, lerp(a, tip, .5) + V(0, 0.015, 0), tip], [r, r * .9, r * .7], k=0.008, up=(0, 1, 0))
    t2 = tip + nrm(tip - a) * 0.045 + V(0, -0.02, 0)
    b.add(f_seg(tip + V(0, 0.01, 0), t2, (r * .7, r * .6, 0, 2), (0.002, 0.002, 0, 2), up=(0, 1, 0)), k=0.004, mirror=True)
for tz in (-0.04, 0.0, 0.045):
    toe(FT, V(0.20, Y0 + 0.015, LZ + tz), 0.02)
toe(FT, V(0.0, Y0 + 0.015, LZ), 0.024)   # hallux
# tail: broad flat fan continuing the body axis
TB = B1 + V(-0.02, 0.03, 0); TT = TB + ax * 0.82
b.group(loft([TB, lerp(TB, TT, .5), TT], [(0.025, 0.11, 0, 2.6), (0.02, 0.13, 0, 2.8), (0.012, 0.15, 0, 3.5)], up=np.cross(ax, (0, 0, 1)), sub=3), 0, 0.03)
# folded wings: covert shield over the shoulder + stacked pointed primaries reaching the tail tip
WR = Q(0.20, 1.00, 0.17); WT = TT + V(0.03, 0.01, 0.0)
wing_dir = nrm(WT - WR); wup = np.cross(wing_dir, (0, 0, 1))
b.group(loft([Q(0.22, 1.06, 0.14), WR, lerp(WR, WT, .25) + V(0, 0, 0.0), lerp(WR, WT, .5) + V(0, 0, -0.06)],
             [(0.10, 0.045, 0, 2.4), (0.17, 0.05, 0, 2.6), (0.18, 0.045, 0, 2.6), (0.11, 0.03, 0, 2.2)], up=wup, sub=4), 0, 0.03, mirror=True)
for i in range(6):   # stacked primaries / secondaries, pointed, crossing over the tail near its tip
    t0 = 0.40 + i * 0.05; root = lerp(WR, WT, t0); root[2] = 0.17 - 0.12 * t0
    tip = WT - wing_dir * 0.05 * i + wup * (0.015 * i); tip[2] = 0.035 + 0.012 * i
    b.group(loft([root, lerp(root, tip, .6), tip], [(0.05, 0.012, 0, 2), (0.045, 0.01, 0, 2), (0.004, 0.004, 0, 2)], up=wup, sub=3), 0, 0.006, mirror=True)
TT_ = TT; tail_tip_along = np.dot(TT_ - B0, ax); wing_tip_along = np.dot(WT - B0, ax)
pts = dict(bl0=B0, bl1=B1, bill_tip=TIP, occiput=OC, head_top=Q(0.56, 1.47), head_bot=Q(0.56, 1.27), cere=CERE, bill_top=Q(0.73, 1.405), bill_bot=Q(0.73, 1.315),
           neck0=B0, crown=Q(0.56, 1.47), perch=V(0.08, Y0, 0), breast=lerp(B0, B1, .3), breast_lo=lerp(B0, B1, .3) - V(0, 0.15, 0),
           knee=KN, ankle=AN, foot=FT, trouser_end=TE, toe_front=V(0.20 + 0.045, Y0, LZ), hallux_tip=V(-0.045, Y0, LZ), hallux_base=V(0.04, Y0, LZ),
           tail_base=TB, tail_base_m=TB + ax * 0.12, tail_tip=TT, wrist=WR, wing_tip=WT)
export(b, 'eagle', pts, values=dict(chest_depth=0.52, eye_d=0.068, wingtip_vs_tail=float((wing_tip_along - tail_tip_along))), bl_len=1.0)
