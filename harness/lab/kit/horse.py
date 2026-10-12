from kit import *
b = Body()
torso(b, [(0.80, 1.42, 1.00, 0.17), (0.52, 1.74, 0.85, 0.22), (0.30, 1.62, 0.82, 0.27), (0.02, 1.54, 0.84, 0.29), (-0.22, 1.53, 0.92, 0.28),
          (-0.42, 1.58, 1.04, 0.26), (-0.66, 1.57, 1.12, 0.24), (-0.86, 1.44, 1.17, 0.15)],
      scap=dict(top=(0.42, 1.50, 0.15), point=(0.72, 1.20, 0.19), width=0.09), keel=((0.84, 1.04, 0), 0.05, 0.3), ridge=0)
H = Head((1.06, 2.08, 0), 58, 0.62)
neck(b, (0.66, 1.30, 0), H.P(0.12, -0.22), (0.30, 0.17), (0.12, 0.075), crest=0.02,
     mane=dict(style='solid', length=0.035, thick=0.04))
skull(b, H, cranium_w=0.17, cranium_h=0.22, muzzle_w=0.11, muzzle_h=0.13, jaw_depth=0.30, nose='horse')
ear(b, H.P(0.04, 0.02, 0.07), H.P(-0.02, 0.27, 0.10), 0.045, thick=0.008, out=(0.6, 0, 0.8))
foreleg(b, dict(scap_top=(0.42, 1.50, 0.2), shoulder=(0.70, 1.16, 0.21), elbow=(0.48, 0.98, 0.19), carpus=(0.50, 0.52, 0.17),
                fetlock=(0.50, 0.24, 0.16), coronet=(0.55, 0.09, 0.16), ground=(0.60, 0.0, 0.16)), g=0.072)
hindleg(b, dict(hip=(-0.60, 1.32, 0.22), buttock=(-0.88, 1.30, 0.16), stifle=(-0.33, 1.02, 0.22), hock=(-0.70, 0.56, 0.17),
                fetlock=(-0.66, 0.24, 0.16), coronet=(-0.61, 0.09, 0.16), ground=(-0.56, 0.0, 0.16)), g=0.075)
tail(b, [(-0.87, 1.46, 0), (-0.96, 1.34, 0), (-1.0, 1.14, 0)], 0.06, 0.035,
     plume=dict(length=0.75, count=26, thick=0.026, gravity=0.85, spread=0.2, start=0.15))
# jugular groove: throatlatch -> base of neck, lower third of neck side
groove(b, [H.P(0.2, -0.55, 0.11), lerp(H.P(0.2, -0.55, 0.11), (0.78, 1.30, 0.17), .5) + V(0, -.03, 0.02), (0.78, 1.30, 0.17)], 0.006, 0.05)
b.mesh(r'C:\lab4\horse.obj', n=330)
