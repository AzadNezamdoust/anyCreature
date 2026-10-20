from kit import *
# light riding horse, BL (point of shoulder/chest -> point of buttock) = 1.0, chest x=+0.5, buttock x=-0.5
b = Body(kin=0.014)
FZ, HZ = 0.105, 0.10
st = [(0.50, 0.90, 0.64, 0.10), (0.30, 1.005, 0.52, 0.135), (0.10, 0.99, 0.505, 0.15), (-0.10, 0.975, 0.51, 0.15),
      (-0.28, 0.985, 0.57, 0.14), (-0.42, 0.99, 0.66, 0.13), (-0.50, 0.92, 0.74, 0.09)]
torso(b, st, box=2.6, scap=dict(top=(0.29, 0.94, 0.10), point=(0.46, 0.74, 0.12), width=0.06), keel=((0.50, 0.66, 0), 0.03, 0.2), ridge=0.008)
H = Head((0.515, 1.345, 0), 55, 0.395)
P0 = (0.42, 0.88, 0)
neck(b, P0, H.P(0.12, -0.22), (0.12, 0.08), (0.07, 0.05), crest=0.012)
crest_mane(b, P0, H.P(0.12, -0.22), (0.12, 0.08), (0.07, 0.05), 0.012, 0.03, 0.035)
skull(b, H, cranium_w=0.17, cranium_h=0.22, muzzle_w=0.11, muzzle_h=0.13, jaw_depth=0.235, eye_at=0.33, nose='horse', s0=0.09)
ear(b, H.P(0.04, 0.02, 0.07), H.P(-0.02, 0.34, 0.10), 0.04, thick=0.008, out=(0.6, 0, 0.8))
mass(b, (0.45, 0.66, 0.06), (1, -0.3, 0), (0.07, 0.07, 0.05), k=0.04)   # pectoral
FJ = dict(scap_top=(0.29, 0.944, FZ), shoulder=(0.47, 0.73, FZ + .01), elbow=(0.32, 0.60, FZ), carpus=(0.33, 0.312, FZ - .01),
          fetlock=(0.33, 0.122, FZ - .01), coronet=(0.375, 0.065, FZ - .01), ground=(0.41, 0.0, FZ - .01), hoof_g=0.07)
foreleg(b, FJ, g=0.054, k_body=0.05)
HJ = dict(hip=(-0.30, 0.90, HZ), buttock=(-0.50, 0.90, 0.07), stifle=(-0.20, 0.63, HZ + 0.02), hock=(-0.38, 0.36, HZ - .01),
          fetlock=(-0.37, 0.14, HZ - .01), coronet=(-0.32, 0.07, HZ - .01), ground=(-0.285, 0.0, HZ - .01), hoof_g=0.065)
hindleg(b, HJ, g=0.054, tg=0.04, k_body=0.06)
T = [(-0.47, 0.97, 0), (-0.57, 0.87, 0), (-0.62, 0.74, 0)]
tail_locks(b, T, 0.042, 0.44, n=5, spread=0.5)
pts = dict(bl0=(0.50, 0.70, 0), bl1=(-0.50, 0.90, 0), snout=H.P(1.0, -0.13 * 1.45), poll=H.o, head_top=H.P(0.18, 0.05), jaw_low=H.P(0.25, -0.445),
           muz_top=H.P(0.85, -0.12 + 0.12), muz_bot=H.P(0.85, -0.12 - 0.13), eye=H.P(0.33, -0.066),
           withers=(0.28, 1.005, 0), croup=(-0.42, 0.99, 0), girth=(0.18, 0.8, 0), belly=(-0.05, 0.5, 0), hipx=(-0.36, 0.9, 0),
           scap_top=FJ['scap_top'], shoulder=FJ['shoulder'], elbow=FJ['elbow'], carpus=FJ['carpus'], ffet=FJ['fetlock'], fcor=FJ['coronet'],
           fhoof=(0.40, 0.03, FZ - .01), hip=HJ['hip'], stifle=HJ['stifle'], hock=HJ['hock'], hfet=HJ['fetlock'], hcor=HJ['coronet'],
           tail0=T[0], tail1=T[1], tail2=T[2], tail3=(-0.66, 0.30, 0), tailg=(-0.50, 0.94, 0),
           ear_base=H.P(0.04, 0.02, 0.07), ear_tip=H.P(-0.02, 0.34, 0.10))
export(b, 'horse', pts)
