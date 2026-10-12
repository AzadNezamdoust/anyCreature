from kit import *
# giraffe, BL = 1 (chest x=+0.5 .. buttock x=-0.5)
b = Body(kin=0.014)
FZ, HZ = 0.10, 0.09
st = [(0.50, 1.28, 0.99, 0.12), (0.28, 1.40, 0.89, 0.165), (0.08, 1.36, 0.89, 0.175), (-0.12, 1.31, 0.92, 0.165),
      (-0.30, 1.255, 0.97, 0.145), (-0.50, 1.17, 1.03, 0.10)]
torso(b, st, box=2.4, scap=dict(top=(0.27, 1.38, 0.10), point=(0.47, 1.30, 0.12), width=0.06), keel=((0.50, 1.02, 0), 0.03, 0.2), ridge=0.01)
cord(b, [(0.42, 1.36, 0), (0.30, 1.43, 0), (0.15, 1.40, 0)], 0.03, 0.04, mirror=False, up=(0, 1, 0))   # withers spine ridge
H = Head((0.95, 2.28, 0), 58, 0.285)
NB = (0.40, 1.30, 0)
neck(b, NB, H.P(0.10, -0.25), (0.16, 0.12), (0.055, 0.042), crest=0.0, k=0.08)
cord(b, [NB + V(-0.05, 0.14, 0), lerp(NB, H.o, .5) + V(-0.07, 0.05, 0), H.o + V(-0.04, -0.03, 0)], 0.015, 0.012, mirror=False, up=(0, 1, 0))  # short mane
skull(b, H, cranium_w=0.20, cranium_h=0.24, muzzle_w=0.12, muzzle_h=0.15, jaw_depth=0.26, eye_r=0.05, eye_at=0.36, nose='horse', s0=0.08)
bump(b, H.P(0.42, 0.04), (0.04, 0.03, 0.025), axis=H.u, up=H.v, mirror=False)   # median boss
horn(b, H.P(0.06, 0.08, 0.07), H.P(0.02, 0.22, 0.08), H.P(-0.02, 0.36, 0.085), 0.022)
blob(b, H.P(-0.02, 0.37, 0.085), (0.022, 0.02, 0.022), k=0.008, mirror=True)   # knob tip
ear(b, H.P(0.05, -0.02, 0.10), H.P(0.02, 0.0, 0.10 + 0.46), 0.035, thick=0.007, out=(0.4, 0.6, 0.6))
FJ = dict(scap_top=(0.27, 1.38, FZ), shoulder=(0.47, 1.34, FZ + .01), elbow=(0.33, 1.02, FZ), carpus=(0.36, 0.57, FZ - .01),
          fetlock=(0.36, 0.16, FZ - .01), coronet=(0.40, 0.08, FZ - .01), ground=(0.43, 0.0, FZ - .01), hoof_g=0.065)
foreleg(b, FJ, g=0.042, k_body=0.05)
HJ = dict(hip=(-0.36, 1.15, HZ), buttock=(-0.50, 1.13, 0.06), stifle=(-0.16, 0.82, HZ + 0.02), hock=(-0.42, 0.52, HZ - .01),
          fetlock=(-0.40, 0.15, HZ - .01), coronet=(-0.35, 0.075, HZ - .01), ground=(-0.32, 0.0, HZ - .01), hoof_g=0.06)
hindleg(b, HJ, g=0.042, tg=0.028, k_body=0.06)
T = [(-0.48, 1.20, 0), (-0.55, 1.00, 0), (-0.58, 0.80, 0)]
tail(b, T, 0.03, 0.014, k=0.03)
tail_locks(b, [(-0.575, 0.86, 0), (-0.58, 0.78, 0)], 0.03, 0.44, n=5, spread=0.4)
pts = dict(bl0=(0.50, 1.1, 0), bl1=(-0.50, 1.1, 0), snout=H.P(1.0, -0.15 * 1.45), poll=H.o, head_top=H.P(0.25, 0.06), jaw_low=H.P(0.25, -0.49),
           withers_front=NB, oss0=H.P(0.06, 0.08, 0.07), oss1=H.P(-0.02, 0.39, 0.085), crown=H.P(-0.02, 0.39, 0),
           withers=(0.28, 1.43, 0), croup=(-0.30, 1.255, 0), girth=(0.15, 1.1, 0), belly=(-0.05, 0.9, 0), hipx=(-0.36, 1.2, 0),
           shoulder=FJ['shoulder'], elbow=FJ['elbow'], carpus=FJ['carpus'], ffet=FJ['fetlock'], fcor=FJ['coronet'], fhoof=(0.42, 0.03, FZ - .01),
           hip=HJ['hip'], stifle=HJ['stifle'], hock=HJ['hock'], hfet=HJ['fetlock'],
           tail0=T[0], tail1=T[1], tail2=T[2], tail3=(-0.60, 0.34, 0), tailg=(-0.536, 1.04, 0),
           ear_base=H.P(0.05, -0.02, 0.10), ear_tip=H.P(0.02, 0.0, 0.56))
export(b, 'giraffe', pts, values=dict(neck_base_d=0.32))
