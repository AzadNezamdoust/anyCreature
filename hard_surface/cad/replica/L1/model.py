"""L1 replica: (a) official Raspberry Pi 4 case, red/white; (b) ISO 4017 M8x40 hex bolt.
Sources: see REFS.md. [R1]=RS/PiShop listing 97x70x25 mm; [R2]=RPi4 mechanical drawing (port positions);
[R3]=raspberrypi.com product photo (form, part break, cut-out layout); [B1]=fasteners.eu ISO 4017 table + drawing.
Axes: X length (USB/Ethernet end at +X), Y width (side ports at -Y), Z up. mm.
"""
import math

from cadkit import *

UNITS = "mm"
# ---------------------------------------------------------------- case [R1] outer envelope
CL, CW, CH = 97.0, 70.0, 25.0          # [R1] 97 x 70 x 25 mm
R_PLAN = 6.0                            # [R3] vertical corner radius (photo est. vs 70 mm width)
R_TOP = 5.0                             # [R3] lid top edge radius (photo est.)
R_BOT = 1.5                             # [R3] base bottom edge
WALL = 2.0                              # typical moulded wall (est.)
Z_SPLIT = 7.0                           # [R3] red base height (≈ 0.28 H measured on photo end face)
Z_SIDE = 18.0                           # [R3] red side panel height on port side (≈ 0.72 H on photo)
SIDE_T = 4.0                            # depth into Y of red side panel region (> WALL)
# board placement [R2]: 85x56, Pi4 port edge parallel to -Y wall
BX0 = -CL / 2 + 6.0                     # board USB-C-end edge x (est.: 12 mm slack, ports end flush at +X)
BY0 = -CW / 2 + 7.0                     # board port edge y
BZ = 4.0                                # board underside (standoff height est.)
PCB = 1.4
ZT = BZ + PCB                           # board top
SIDE_PORTS = [  # (x from board edge [R2], w, h, z-centre, kind)
    (3.5 + 7.7, 9.6, 3.6, ZT + 1.6, "usbc"),
    (3.5 + 7.7 + 14.8, 7.5, 3.4, ZT + 1.5, "hdmi"),
    (3.5 + 7.7 + 14.8 + 13.5, 7.5, 3.4, ZT + 1.5, "hdmi"),
    (3.5 + 7.7 + 14.8 + 13.5 + 14.0, 6.6, 6.6, ZT + 3.0, "audio"),   # 53.5 [R2]
]
END_PORTS = [  # (y from port edge [R2], w, h, kind)  heights Z=16 / 13.5 [R2]
    (9.0, 14.6, 16.4, "usb"), (27.0, 14.6, 16.4, "usb"), (45.75, 16.6, 13.9, "eth")]


def rbox(l, w, h, rp, z0=0.0):
    b = Pos(0, 0, z0) * Box(l, w, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return safe_fillet(b, b.edges().filter_by(Axis.Z), rp, label="plan corners")


outer = rbox(CL, CW, CH, R_PLAN)
outer = safe_fillet(outer, outer.edges().group_by(Axis.Z)[-1], R_TOP, label="lid top edge")
outer = safe_fillet(outer, outer.edges().group_by(Axis.Z)[0], R_BOT, label="base bottom edge")
inner = rbox(CL - 2 * WALL, CW - 2 * WALL, CH - 2 * WALL, R_PLAN - WALL, WALL)
inner = safe_fillet(inner, inner.edges().group_by(Axis.Z)[-1], R_TOP - WALL, label="inner top")
shell = cut(outer, inner, "hollow")

# recessed rounded panel framing the side ports [R3: inset frame around USB-C..audio]
x0, x1 = BX0 + 3.5 + 7.7 - 8.0, BX0 + 53.5 + 6.0
rec = Pos((x0 + x1) / 2, -CW / 2, ZT + 2.0) * Box(x1 - x0, 1.6, 11.0)
rec = safe_fillet(rec, rec.edges().filter_by(Axis.Y), 3.0, label="recess corners")
shell = cut(shell, rec, "port recess")
# side-port window: one rounded slot through the red side panel framing all 4 ports [R3]
for xb, w, h, zc, k in SIDE_PORTS:
    c = Pos(BX0 + xb, -CW / 2, zc) * Box(w, 3 * WALL, h)
    if k == "audio":
        c = Pos(BX0 + xb, -CW / 2, zc) * (Rot(90, 0, 0) * Cylinder(w / 2, 3 * WALL))
    shell = cut(shell, c, f"port {k}")
for yb, w, h, k in END_PORTS:
    c = Pos(CL / 2, BY0 + yb, ZT + h / 2 - 0.2) * Box(3 * WALL, w, h)
    shell = cut(shell, c, f"end {k}")
# micro-SD access notch at -X end, under board [R2]/[R3 not visible -> est.]
shell = cut(shell, Pos(-CL / 2, BY0 + 28, BZ - 1.0) * Box(3 * WALL, 14, 3), "sd notch")

# red/white split region: base below Z_SPLIT + port-side panel with S-curve drop toward +X end [R3]
xs0, xs1 = CL / 2 - 26.0, CL / 2 - 12.0
sp = Spline((xs1, Z_SPLIT), (0.5 * (xs0 + xs1), 0.5 * (Z_SPLIT + Z_SIDE)), (xs0, Z_SIDE),
            tangents=((-1, 0), (-1, 0)))
w_side = Wire([Line((-CL, -1), (CL, -1)), Line((CL, -1), (CL, Z_SPLIT)), Line((CL, Z_SPLIT), (xs1, Z_SPLIT)), sp,
               Line((xs0, Z_SIDE), (-CL, Z_SIDE)), Line((-CL, Z_SIDE), (-CL, -1))])
panel = extrude(Plane.XZ * make_face(w_side), amount=-SIDE_T)     # Plane.XZ normal -Y -> -amount goes +Y
panel = Pos(0, -CW / 2 - 1, 0) * panel
region = fuse(Box(2 * CL, 2 * CW, Z_SPLIT + 1, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(Pos(0, 0, Z_SPLIT)),
              panel, "split region")
red = common(shell, region, "red base")
white = cut(shell, region, "white lid")

# visible board connectors (silver/blue) behind the cut-outs [R2 heights]
metal = None
for yb, w, h, k in END_PORTS:
    b = Pos(BX0 + 85 - 10, BY0 + yb, ZT) * Box(21 if k == "eth" else 17.5, w - 1.4, h - 0.6,
                                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    b = Pos(4.0 if k == "usb" else 1.0, 0, 0) * b
    b = cut(b, Pos(CL / 2 - 1, BY0 + yb, ZT + h / 2) * Box(12, w - 3.4, h - 4.5), f"{k} mouth")
    metal = b if metal is None else fuse(metal, b, "conn")
for xb, w, h, zc, k in SIDE_PORTS:
    if k == "audio":
        b = Pos(BX0 + xb, BY0 + 6, zc) * (Rot(90, 0, 0) * Cylinder(3.0, 14))
        b = cut(b, Pos(BX0 + xb, BY0, zc) * (Rot(90, 0, 0) * Cylinder(1.75, 20)), "jack bore")
    else:
        b = Pos(BX0 + xb, BY0 + 3.5, zc) * Box(w - 1.6, 8, h - 0.6)
        b = cut(b, Pos(BX0 + xb, BY0 - 1, zc) * Box(w - 2.6, 8, h - 1.8), f"{k} mouth")
    metal = fuse(metal, b, "conn")
board = Pos(BX0 + 42.5, BY0 + 28, BZ) * Box(85, 56, PCB, align=(Align.CENTER, Align.CENTER, Align.MIN))
board = safe_fillet(board, board.edges().filter_by(Axis.Z), 3.0, label="pcb corners")   # [R2] r=3

# ---------------------------------------------------------------- ISO 4017 M8x40 [B1]
D, P, LEN = 8.0, 1.25, 40.0            # [B1]
S, K, E = 13.0, 5.3, 14.38             # across flats, head height, across corners (min, class A) [B1]
DW, C = 11.63, 0.4                     # washer face dia min, washer-face height (c 0.15..0.6) [B1]
CHAMF = 30.0                           # [B1] head top chamfer 15-30 deg
D1 = D - 1.226869 * P                  # minor dia (ISO 724 d3)
OX = 0.0; OY = CW / 2 + 40             # bolt placed beside the case, axis along X, head at -X
hexp = RegularPolygon(S / 2, 6, major_radius=False)
head = extrude(hexp, K - C)
# 30 deg chamfer cone on top corners: revolve a profile and intersect
r_ch = S / 2 * 0.95
cone = revolve(Plane.XZ * make_face(Polyline((0, 0), (E, 0), (E, K - C - (E - r_ch) * math.tan(math.radians(CHAMF))),
                                              (r_ch, K - C), (0, K - C), close=True)), Axis.Z)
head = common(head, cone, "head chamfer")
wf = Pos(0, 0, -C) * Cylinder(DW / 2, C, align=(Align.CENTER, Align.CENTER, Align.MIN))
head = Pos(0, 0, C) * head
head = fuse(head, wf, "washer face")
shank = Pos(0, 0, -LEN) * Cylinder(D1 / 2, LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
# helical ISO metric thread: 60 deg triangle swept along a helix (full thread, l<=..: ISO 4017 = fully threaded)
h_th = (D - D1) / 2
thr_len = LEN - 1.2
hx = helix(P, thr_len, D1 / 2, center=(0, 0, -LEN + 0.6))
try:
    prof_t = Pos(0, 0, -LEN + 0.6) * make_face(Plane.XZ * Polyline((D1 / 2 - 0.05, -P * 0.45), (D / 2, -P / 16),
                                                                    (D / 2, P / 16), (D1 / 2 - 0.05, P * 0.45),
                                                                    close=True))
    thread = sweep(prof_t, path=hx, is_frenet=True)
    bolt = fuse(shank, thread, "thread")
except Exception as ex:  # noqa: BLE001
    LOG.append({"op": "thread", "status": "fallback", "err": str(ex)[:200]})
    bolt = Pos(0, 0, -LEN) * Cylinder(D / 2, LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
# point chamfer (u <= 2P, 45 deg to minor dia) and first-turn run-out under head [B1]
pt = revolve(Plane.XZ * make_face(Polyline((0, -LEN), (D1 / 2 - 0.3, -LEN), (D / 2 + 0.5, -LEN + h_th + 0.8),
                                           (D / 2 + 0.5, 1), (0, 1), close=True)), Axis.Z)
bolt = common(bolt, pt, "point chamfer")
bolt = fuse(bolt, head, "head")
bolt = Pos(-LEN / 2 + OX, OY, E / 2) * (Rot(0, 90, 0) * bolt)

PARTS = {"case_lid_white": (white, "#f2f2f0"), "case_base_red": (red, "#c51a4a"),
         "connectors": (metal, "#b8bcc2"), "pcb": (board, "#1e6b3a"), "bolt_M8x40": (bolt, "#8a8d92")}
SPEC = {"case_L": CL / 1000, "case_W": CW / 1000}
