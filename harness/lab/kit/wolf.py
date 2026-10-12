from kit import *
b = Body(kin=0.014)
torso(b, [(0.37, 0.68, 0.42, 0.105), (0.22, 0.84, 0.35, 0.12), (0.04, 0.78, 0.37, 0.115), (-0.16, 0.76, 0.55, 0.08),
          (-0.34, 0.76, 0.58, 0.085), (-0.50, 0.70, 0.59, 0.07)], box=2.8,
      scap=dict(top=(0.18, 0.78, 0.09), point=(0.33, 0.58, 0.11), width=0.045), keel=((0.39, 0.44, 0), 0.03, 0.15), ridge=0)
H = Head((0.50, 0.90, 0), 16, 0.27)
neck(b, (0.30, 0.66, 0), H.P(0.12, -0.18), (0.16, 0.13), (0.095, 0.085), crest=0.03)
skull(b, H, cranium_w=0.24, cranium_h=0.24, muzzle_w=0.11, muzzle_h=0.15, jaw_depth=0.16, eye_r=0.04, eye_at=0.36,
      stop=0.05, nose='dog')
ear(b, H.P(0.12, 0.05, 0.12), H.P(0.06, 0.38, 0.17), 0.05, thick=0.006, out=(0.8, 0, 0.5), cup=0.8)
foreleg(b, dict(scap_top=(0.18, 0.76, 0.1), shoulder=(0.34, 0.56, 0.10), elbow=(0.24, 0.40, 0.09), carpus=(0.26, 0.15, 0.075),
                fetlock=(0.27, 0.07, 0.075), ground=(0.30, 0.0, 0.075)), g=0.032, foot='paw', k_body=0.04, toe=dict(width=0.085, toe_len=0.06, claw=0.016))
hindleg(b, dict(hip=(-0.40, 0.64, 0.075), buttock=(-0.52, 0.62, 0.06), stifle=(-0.27, 0.42, 0.095), hock=(-0.44, 0.17, 0.075),
                fetlock=(-0.41, 0.07, 0.075), ground=(-0.38, 0.0, 0.075)), g=0.032, foot='paw', k_body=0.05, toe=dict(width=0.08, toe_len=0.056, claw=0.016))
tail(b, [(-0.44, 0.70, 0), (-0.54, 0.66, 0), (-0.63, 0.55, 0), (-0.68, 0.40, 0), (-0.69, 0.27, 0)], 0.045, 0.022,
     plume=dict(length=0.14, count=40, thick=0.016, gravity=0.3, spread=0.25, start=0.25, taper=lambda t: 0.6 + 0.6 * np.sin(np.pi * min(t * 1.2, 1))))
# neck: trapezius cord along upper neck, sternocephalicus cord throat -> sternum, ruff collar
#cord(b, [(0.25, 0.80, 0.05), (0.36, 0.84, 0.05), (0.46, 0.86, 0.045)], 0.012, 0.02)
#cord(b, H.P(0.25, -0.75, 0.07)[None].tolist() + [[0.44, 0.58, 0.07], [0.38, 0.46, 0.04]], 0.012, 0.018)
mass(b, (0.22, 0.60, 0.04), (1, -0.4, 0), (0.17, 0.15, 0.08), k=0.08)   # shoulder/triceps bulk
mass(b, (-0.40, 0.60, 0.05), (1, -0.3, 0), (0.13, 0.12, 0.06), k=0.05)   # haunch
ruff(b, (0.31, 0.66, 0), H.P(0.05, -0.3), 0.16, count=10, length=0.04, k=0.07)
b.mesh(r'C:\lab4\wolf.obj', n=330)
