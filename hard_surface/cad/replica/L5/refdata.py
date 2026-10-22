"""Porsche 911 Carrera S (992.1) coupe - reference data, registered to spec dimensions.

All pixel traces were read off gridded crops of the photos listed in REFS.md (refs/L5/, git-ignored).
Model frame: mm, front -X, left -Y, Z up, ground Z=0, car centred on X (bbox mid-length) and Y.

Registration (photos are telephoto / near-ortho, NOT true orthographic blueprints):
  SIDE  (S1 = Porsche_992_Carrera_S.jpg, car faces +x in image): x is registered PIECEWISE-LINEAR through four
        known stations (rear end, rear axle, front axle, front end) so overall length AND wheelbase both match
        spec; z is registered by ground line + roof height (H). This absorbs the depth difference between
        centreline features (roof/ends) and the near-side wheels.
  FRONT (F1 = White_9) and REAR (R1 = White_16): anisotropic box registration to spec W x H (camera above
        the car, so heights are only approximate).
"""
import numpy as np

# ---------------- spec (sources: REFS.md S-1 Porsche/Wikipedia, S-2 auto-motor-und-sport test data)
L = 4519.0          # length mm (Porsche spec, Wikipedia 992 range low end = Carrera coupe)
W = 1852.0          # width w/o mirrors (ams, Wikipedia)
H = 1298.0          # height (ams test car 1298; Porsche quotes 1300 for Carrera S)
WB = 2450.0         # wheelbase (Porsche, ams, Wikipedia)
TRACK_F = 1591.0    # ams
TRACK_R = 1557.0    # ams
# Carrera S standard tyres (Porsche 992.1 Carrera S spec): 245/35 ZR20 front, 305/30 ZR21 rear
TYRE_F = (245.0, 0.35, 20)
TYRE_R = (305.0, 0.30, 21)


def tyre_d(t):
    w, ar, rim = t
    return rim * 25.4 + 2 * w * ar


R_TF, R_TR = tyre_d(TYRE_F) / 2, tyre_d(TYRE_R) / 2   # 339.75, 358.35

# ---------------- SIDE photo S1 (1920x1440) key pixels
S_GROUND = 1000.0
S_ROOF = 435.0
S_XREAR, S_XAR, S_XAF, S_XFRONT = 25.0, 457.0, 1525.0, 1900.0   # rear end, rear axle, front axle, front end
S_ZS = H / (S_GROUND - S_ROOF)                                  # 2.297 mm/px
_ovh = L - WB
_pf, _pr = S_XFRONT - S_XAF, S_XAR - S_XREAR
OVH_F = _ovh * _pf / (_pf + _pr)        # front overhang from photo ratio  (~961 mm)
OVH_R = _ovh - OVH_F                    # (~1108 mm)
X_FRONT, X_REAR = -L / 2, L / 2
X_AF = X_FRONT + OVH_F                  # front axle X
X_AR = X_AF + WB                        # rear axle X
_SX_PX = [S_XREAR, S_XAR, S_XAF, S_XFRONT]
_SX_MM = [X_REAR, X_AR, X_AF, X_FRONT]


def side_px2mm(px, py):
    """Side-photo pixel -> model (X, Z) mm."""
    x = np.interp(px, _SX_PX, _SX_MM)
    return float(x), float((S_GROUND - py) * S_ZS)


def side_mm2px(x, z):
    px = np.interp(-np.asarray(x, float), [-m for m in _SX_MM], _SX_PX)
    return px, S_GROUND - np.asarray(z, float) / S_ZS


# outer silhouette (rear end -> roof -> nose -> sill -> arches), wheels added separately as circles
SIDE_OUTLINE_PX = [
    (30, 680), (75, 637), (100, 612), (150, 585), (200, 565), (300, 535), (400, 510), (500, 485), (600, 465),
    (700, 450), (850, 440), (950, 435), (1000, 440), (1060, 470), (1160, 520), (1260, 570), (1360, 605),
    (1460, 615), (1560, 630), (1635, 650), (1685, 680), (1735, 725), (1785, 750), (1850, 765), (1895, 780),
    (1900, 820), (1895, 920), (1885, 935), (1710, 940), (1690, 920),
    (1680, 820), (1650, 745), (1585, 705), (1510, 692), (1435, 710), (1385, 760), (1360, 830), (1355, 925),
    (1300, 930), (900, 930), (640, 925), (635, 920),
    (630, 820), (600, 720), (550, 680), (450, 665), (350, 700), (300, 770), (280, 920), (100, 900), (40, 870),
    (25, 820), (25, 770)]
SIDE_WHEELS_PX = [(457, 845, 167), (1525, 865, 155)]   # tyre circles in the photo (cx, cy, r)
# top silhouette only (centreline roof/deck + front fender crown), rear->front
SIDE_TOP_PX = SIDE_OUTLINE_PX[1:26]
# side glass (DLO) outline
SIDE_DLO_PX = [(480, 570), (550, 530), (700, 490), (850, 478), (950, 477), (1050, 487), (1150, 525),
               (1240, 600), (1235, 612), (950, 602), (750, 600), (500, 585)]
DOOR_FRONT_PX = [(1270, 635), (1300, 770), (1290, 895)]
DOOR_REAR_PX = [(750, 630), (750, 720), (780, 800), (825, 860), (900, 890)]
DOOR_BOTTOM_PY = 905
MIRROR_PX = (1090, 1200, 580, 655)
HANDLE_PX = (780, 850, 695, 706)
FUEL_PX = (1345, 1435, 645, 690)
TAIL_PX = (30, 270, 640, 668)          # tail light band seen from the side
HEADLIGHT_SIDE_PX = (1650, 1765, 640, 735)
SILL_PY = 930
NOSE_BOTTOM_PY = 940
REAR_BOTTOM_PY = 910
ARCH_TOP_PY = {"R": 665, "F": 692}

# ---------------- FRONT photo F1 (1920x1440)
F_GROUND, F_ROOF = 1250.0, 288.0
F_XL, F_XR = 265.0, 1690.0
F_CX = (F_XL + F_XR) / 2
F_SY = W / (F_XR - F_XL)
F_SZ = H / (F_GROUND - F_ROOF)
# right half silhouette (centre top -> right side -> bottom centre), mirrored for the left
FRONT_HALF_PX = [(977, 288), (1300, 298), (1340, 330), (1400, 450), (1465, 570), (1500, 600), (1600, 650),
                 (1660, 720), (1690, 820), (1690, 1000), (1680, 1150), (1660, 1215), (1650, 1250), (1520, 1250),
                 (1500, 1225), (977, 1228)]
FRONT_MIRROR_PX = [(1520, 495), (1640, 500), (1645, 560), (1580, 590), (1515, 590)]
FRONT_HEADLIGHT_PX = (1530, 765, 95, 105)      # centre x, y, rx, ry
FRONT_INTAKE_SIDE_PX = (1270, 1640, 990, 1200)
FRONT_INTAKE_MID_PX = (680, 1270, 1100, 1200)
FRONT_WS_BASE_PX = (500, 1465, 570)            # windshield base span

# ---------------- REAR photo R1 (1920x1440)
R_GROUND, R_ROOF = 1085.0, 418.0
R_XL, R_XR = 490.0, 1615.0
R_CX = (R_XL + R_XR) / 2
R_SY = W / (R_XR - R_XL)
R_SZ = H / (R_GROUND - R_ROOF)
REAR_HALF_PX = [(1052, 418), (1310, 440), (1350, 470), (1380, 520), (1420, 600), (1460, 640), (1540, 660),
                (1580, 690), (1610, 740), (1615, 800), (1615, 950), (1605, 1060), (1600, 1085), (1520, 1085),
                (1500, 1070), (1052, 1072)]
REAR_MIRROR_PX = [(1535, 575), (1635, 585), (1630, 640), (1545, 640)]
REAR_TAIL_PY = (745, 790)
REAR_EXHAUST_PX = [(730, 1015, 45, 30), (1225, 1015, 45, 30)]


def front_px2mm(px, py, cx=None, sy=None):
    return (px - F_CX) * F_SY, (F_GROUND - py) * F_SZ


def rear_px2mm(px, py):
    return (px - R_CX) * R_SY, (R_GROUND - py) * R_SZ


def side_poly_mm(pts):
    return [side_px2mm(*p) for p in pts]


if __name__ == "__main__":
    print("overhang F/R", round(OVH_F), round(OVH_R), "axles", round(X_AF), round(X_AR))
    print("tyre r F/R", R_TF, R_TR, "S_ZS", S_ZS)
    for p in SIDE_TOP_PX:
        print(p, [round(v) for v in side_px2mm(*p)])
