from kit import *
# grey wolf, body length (chest point -> buttock) = 1.0 ; chest point x=+0.5, buttock x=-0.5
b = Body(kin=0.014)
FZ, HZ = 0.046, 0.052
st = [(0.48, 0.80, 0.60, 0.07), (0.33, 0.905, 0.505, 0.105), (0.13, 0.885, 0.50, 0.12), (-0.05, 0.865, 0.545, 0.112),
      (-0.22, 0.855, 0.615, 0.092), (-0.37, 0.875, 0.635, 0.098), (-0.50, 0.79, 0.67, 0.07)]
torso(b, st, box=2.8, scap=dict(top=(0.27, 0.83, 0.06), point=(0.37, 0.63, 0.06), width=0.045), keel=((0.47, 0.58, 0), 0.03, 0.18), ridge=0)
H = Head((0.53, 1.10, 0), 22, 0.27)
neck(b, (0.34, 0.76, 0), H.P(0.12, -0.2), (0.125, 0.085), (0.09, 0.075), crest=0.025)
skull(b, H, cranium_w=0.25, cranium_h=0.26, muzzle_w=0.11, muzzle_h=0.15, jaw_depth=0.26, eye_r=0.04, eye_at=0.40, stop=0.06, nose='dog')
ear(b, H.P(0.10, 0.06, 0.13), H.P(0.04, 0.42, 0.17), 0.055, thick=0.006, out=(0.8, 0, 0.5), cup=0.8)
FJ = dict(scap_top=(0.26, 0.81, FZ), shoulder=(0.36, 0.62, FZ + .01), elbow=(0.24, 0.445, FZ), carpus=(0.25, 0.185, FZ - .005),
          fetlock=(0.26, 0.055, FZ - .005), ground=(0.30, 0.0, FZ - .005))
foreleg(b, FJ, g=0.036, foot='paw', k_body=0.04, toe=dict(width=0.085, toe_len=0.055, claw=0.016))
HJ = dict(hip=(-0.37, 0.69, HZ), buttock=(-0.48, 0.70, 0.04), stifle=(-0.25, 0.49, 0.06), hock=(-0.38, 0.26, HZ),
          fetlock=(-0.37, 0.095, HZ), ground=(-0.33, 0.0, HZ))
hindleg(b, HJ, g=0.031, tg=0.021, foot='paw', k_body=0.05, toe=dict(width=0.08, toe_len=0.052, claw=0.016))
T = [(-0.48, 0.83, 0), (-0.58, 0.74, 0), (-0.64, 0.56, 0), (-0.66, 0.41, 0)]
tail(b, T, 0.042, 0.022, plume=dict(length=0.12, count=36, thick=0.016, gravity=0.35, spread=0.25, start=0.25,
                                     taper=lambda t: 0.6 + 0.6 * np.sin(np.pi * min(t * 1.2, 1))))
mass(b, (0.26, 0.66, 0.0), (1, -0.4, 0), (0.15, 0.12, 0.05), k=0.07)   # shoulder/triceps
ruff(b, (0.36, 0.78, 0), H.P(0.05, -0.3), 0.115, count=0, length=0.04, k=0.07)
pts = dict(bl0=(0.50, 0.62, 0), bl1=(-0.50, 0.70, 0), snout=H.P(1.06, -0.15 * .75), occiput=H.P(-0.09, -0.05), stop=H.P(0.5, -0.1),
           head_top=H.P(0.2, 0.15), jaw_low=H.P(0.3, -0.505), poll=H.o, withers=(0.30, 0.905, 0), croup=(-0.37, 0.875, 0),
           girth=(0.13, 0.7, 0), belly=(-0.05, 0.55, 0), hipx=(-0.36, 0.8, 0), scap_top=FJ['scap_top'], shoulder=FJ['shoulder'],
           elbow=FJ['elbow'], carpus=FJ['carpus'], ffet=FJ['fetlock'], ftoe=(0.33, 0.02, FZ), fpaw=(0.31, 0.03, FZ),
           hip=HJ['hip'], stifle=HJ['stifle'], hock=HJ['hock'], hfet=HJ['fetlock'], htoe=(-0.31, 0.03, HZ),
           tail0=T[0], tail1=T[1], tail2=T[2], tail3=T[3], tailg=(-0.52, 0.80, 0),
           ear_base=H.P(0.10, 0.06, 0.13), ear_tip=H.P(0.04, 0.42, 0.17))
export(b, 'wolf', pts)
