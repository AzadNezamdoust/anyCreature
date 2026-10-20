from kit import *
# great white shark. BL = snout tip (x=+0.5) -> caudal fin base (x=-0.5). Swimming pose, held above ground.
b = Body(kin=0.01)
Y = 0.45
def X(px): return 0.5 - px
prof = [(0.0, 0.012, 0.012, 0.0), (0.04, 0.045, 0.04, -0.005), (0.10, 0.077, 0.068, -0.006), (0.20, 0.098, 0.088, -0.004), (0.29, 0.112, 0.096, 0.0),
        (0.36, 0.12, 0.098, 0.004), (0.50, 0.11, 0.088, 0.006), (0.65, 0.083, 0.062, 0.005), (0.80, 0.052, 0.038, 0.004), (0.95, 0.027, 0.024, 0.004), (1.02, 0.03, 0.02, 0.006)]
b.group(loft([(X(p), Y + o, 0) for p, d, w, o in prof], [(d, w, 0, 2.15) for p, d, w, o in prof], up=(0, 1, 0), sub=5), 0, 0)
# belly flattening under the head (ventral plane) and conical snout
flatten(b, V(X(0.12), Y - 0.072, 0), (0, -1, 0), (0.12, 0.05, 0.03), k=0.02, mirror=False, axis=(1, 0, 0))
# five gill slits ahead of the pectoral
for i in range(5):
    px = 0.20 + 0.02 * i
    groove(b, [V(X(px), Y + 0.05, 0.07), V(X(px + 0.004), Y, 0.098), V(X(px + 0.008), Y - 0.05, 0.085)], 0.006, 0.004, normal=(0, 0, 1))
# eye (small, black-round) and mouth under the snout
blob(b, V(X(0.08), Y + 0.02, 0.052), (0.007, 0.007, 0.005), k=0.003, mirror=True)
blob(b, V(X(0.08), Y + 0.02, 0.05), (0.012, 0.009, 0.006), k=0.003, mirror=True, sub=True)
for zz in np.linspace(-0.055, 0.055, 9):
    pass
groove(b, [V(X(0.135), Y - 0.055, 0.058), V(X(0.09), Y - 0.068, 0.0), V(X(0.135), Y - 0.055, -0.058)], 0.012, 0.008, normal=(0, -1, 0), mirror=False)
# fins
top = lambda px: Y + np.interp(px, [p for p, *_ in prof], [d + o for p, d, w, o in prof])
bot = lambda px: Y + np.interp(px, [p for p, *_ in prof], [-d + o for p, d, w, o in prof])
D1 = (V(X(0.38), top(0.38) - 0.01, 0), V(X(0.505), top(0.505) - 0.01, 0), V(X(0.48), top(0.43) + 0.115, 0))
foil(b, D1[0], D1[1], D1[2], 0.012)
foil(b, D1[1], V(X(0.56), top(0.56) - 0.01, 0), D1[2], 0.008)
D2 = (V(X(0.75), top(0.75) - 0.005, 0), V(X(0.79), top(0.79) - 0.005, 0), V(X(0.80), top(0.75) + 0.028, 0))
foil(b, D2[0], D2[1], D2[2], 0.004)
AN = (V(X(0.77), bot(0.77) + 0.005, 0), V(X(0.81), bot(0.81) + 0.005, 0), V(X(0.82), bot(0.77) - 0.026, 0))
foil(b, AN[0], AN[1], AN[2], 0.004)
PC = (V(X(0.285), Y - 0.06, 0.07), V(X(0.365), Y - 0.06, 0.06), V(X(0.385), Y - 0.14, 0.23))
foil(b, PC[0], PC[1], PC[2], 0.011, mirror=True)
foil(b, PC[1], V(X(0.40), Y - 0.07, 0.07), PC[2], 0.008, mirror=True)
PV = (V(X(0.57), bot(0.57) + 0.012, 0.03), V(X(0.62), bot(0.62) + 0.012, 0.025), V(X(0.645), bot(0.6) - 0.025, 0.055))
foil(b, PV[0], PV[1], PV[2], 0.005, mirror=True)
CB = V(X(1.0), Y + 0.006, 0)
CU = CB + V(-0.285, 0.093, 0); CL = CB + V(-0.16, -0.135, 0)
foil(b, CB + V(0.04, 0.02, 0), CB + V(-0.03, 0.0, 0), CU, 0.012)
foil(b, CB + V(-0.03, 0.0, 0), CB + V(-0.17, 0.035, 0), CU, 0.008)
foil(b, CB + V(0.03, -0.015, 0), CB + V(-0.03, -0.005, 0), CL, 0.011)
foil(b, CB + V(-0.03, -0.005, 0), CB + V(-0.11, -0.05, 0), CL, 0.008)
blob(b, CB + V(0.04, 0, 0.022), (0.06, 0.01, 0.01), k=0.008, mirror=True)   # caudal keel
pts = dict(bl0=V(X(0), Y, 0), bl1=CB, gill5=V(X(0.28), Y, 0.09), gill1=V(X(0.20), Y, 0.09), headmid=V(X(0.15), Y, 0), eye=V(X(0.08), Y + 0.02, 0.05),
           mouth=V(X(0.09), Y - 0.068, 0), maxd=V(X(0.36), Y, 0), pecw=V(X(0.30), Y, 0), pec_lo=V(X(0.30), Y - 0.05, 0), ped=V(X(0.95), Y, 0),
           pec0=PC[0], pec1=PC[1], pec_tip=PC[2], d1_0=D1[0], d1_1=D1[1], d1_tip=D1[2], d2_0=D2[0], d2_tip=D2[2], pv0=PV[0], pv_tip=PV[2], an0=AN[0],
           cu_tip=CU, cl_tip=CL)
export(b, 'shark', pts, values=dict(eye_d=0.014))
