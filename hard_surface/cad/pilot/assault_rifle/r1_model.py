from cadkit import *
import math

GM, BK, OR = "#3a3d42", "#1f2023", "#ff6a00"
BZ = 0.17  # bore axis height


def prof(pts, w, y0=0.0):
    """XZ polygon extruded symmetric in Y (width w), centred at y0."""
    sk = Plane.XZ * Polygon(*pts, align=None)
    return Pos(0, y0, 0) * extrude(sk, amount=w / 2, both=True)


def cylx(r, x0, x1, z=BZ, sides=None):
    L = x1 - x0
    if sides:
        sk = Plane.YZ * RegularPolygon(r, sides, major_radius=False)
        s = extrude(sk, amount=L)
    else:
        s = Rot(0, 90, 0) * Cylinder(r, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(x0, 0, z) * s


def ch(s, r, label, sel=None):
    return safe_chamfer(s, sel if sel is not None else s.edges(), r, label=label)


# ---------------- barrel group (gunmetal)
barrel = cylx(0.009, -0.41, -0.20)
brake = cylx(0.017, -0.45, -0.40, sides=8)
brake = ch(brake, 0.003, "brake", brake.edges().filter_by(Axis.X, reverse=True))
for x in (-0.437, -0.418):
    slot = Pos(x, 0, BZ) * Box(0.010, 0.05, 0.007)
    brake = cut(brake, slot, label="brake_slot")
barrel = fuse(barrel, brake, label="barrel+brake")
# front sight tower: triangle frame
tower = prof([(-0.285, BZ), (-0.245, BZ), (-0.262, 0.238), (-0.268, 0.238)], 0.012)
hole = prof([(-0.276, BZ + 0.012), (-0.254, BZ + 0.012), (-0.264, 0.222)], 0.03)
tower = cut(tower, hole, label="tower_window")
tower = fuse(tower, cylx(0.014, -0.29, -0.24), label="tower_collar")
barrel = fuse(barrel, tower, label="barrel+tower")

# ---------------- handguard octagon + vents
hg = cylx(0.031, -0.235, -0.05, sides=8)
hg = Pos(0, 0, 0) * hg
hg = ch(hg, 0.003, "hg_ends", hg.edges().filter_by(Axis.X, reverse=True))
for x in (-0.17, -0.13, -0.09):
    vent = Pos(x, 0, BZ - 0.002) * Rot(90, 0, 0) * extrude(SlotCenterToCenter(0.022, 0.009), amount=0.04, both=True)
    hg = cut(hg, vent, label="hg_vent")
band = cylx(0.033, -0.25, -0.235, sides=8)

# ---------------- receiver
upper = prof([(-0.06, 0.14), (0.17, 0.14), (0.17, 0.206), (-0.06, 0.206)], 0.046)
upper = ch(upper, 0.004, "upper", upper.edges().filter_by(Axis.X))
lower = prof([(-0.02, 0.105), (0.075, 0.105), (0.12, 0.13), (0.16, 0.13), (0.16, 0.142), (-0.02, 0.142)], 0.042)
lower = ch(lower, 0.003, "lower", lower.edges().filter_by(Axis.Y))
receiver = fuse(upper, lower, label="upper+lower")
# rail with ridges
rail = Pos(-0.06, 0, 0.206) * Box(0.225, 0.026, 0.008, align=(Align.MIN, Align.CENTER, Align.MIN))
rail_hg = Pos(-0.235, 0, 0.196) * Box(0.175, 0.026, 0.018, align=(Align.MIN, Align.CENTER, Align.MIN))
rail = fuse(rail, rail_hg, label="rail_ext")
ridges = [Pos(-0.228 + i * 0.0155, 0, 0.214) * Box(0.008, 0.026, 0.006, align=(Align.MIN, Align.CENTER, Align.MIN))
          for i in range(25)]
rail = fuse(rail, ridges, label="rail_ridges")
receiver = fuse(receiver, rail, label="receiver+rail")
rsight = prof([(0.125, 0.214), (0.165, 0.214), (0.16, 0.255), (0.135, 0.255)], 0.03)
rsight = ch(rsight, 0.003, "rsight", rsight.edges().filter_by(Axis.Y))
notch = Pos(0.147, 0, 0.255) * Box(0.04, 0.008, 0.016)
rsight = cut(rsight, notch, label="rsight_notch")
receiver = fuse(receiver, rsight, label="receiver+rsight")
# trigger guard
tg = prof([(0.075, 0.105), (0.13, 0.105), (0.13, 0.095), (0.075, 0.095)], 0.012)
tg = fuse(tg, prof([(0.122, 0.095), (0.132, 0.095), (0.132, 0.13), (0.122, 0.13)], 0.012), label="tg_post")
tg = ch(tg, 0.002, "tg", tg.edges().filter_by(Axis.Y))
receiver = fuse(receiver, tg, label="receiver+tg")
selector = Pos(0.128, -0.024, 0.155) * Box(0.006, 0.006, 0.022)
selector = fuse(selector, Pos(0.128, -0.026, 0.165) * Box(0.016, 0.004, 0.005), label="sel_lever")

# ---------------- grip, stock (polymer)
grip = prof([(0.115, 0.13), (0.155, 0.13), (0.205, 0.04), (0.165, 0.035)], 0.034)
grip = ch(grip, 0.005, "grip", grip.edges().filter_by(Axis.Y))
tube = prof([(0.165, 0.15), (0.40, 0.165), (0.40, 0.21), (0.165, 0.205)], 0.04)
butt = prof([(0.39, 0.07), (0.45, 0.07), (0.45, 0.245), (0.39, 0.235)], 0.046)
strut = prof([(0.30, 0.16), (0.39, 0.16), (0.39, 0.08), (0.375, 0.08)], 0.02)
stock = fuse(tube, [butt, strut], label="stock")
stock = ch(stock, 0.004, "stock", stock.edges().filter_by(Axis.Y))

# ---------------- magazine (curved: forward rake)
mag_pts = [(0.005, 0.11), (0.065, 0.11), (0.05, 0.06), (0.03, 0.015), (-0.025, 0.015), (-0.005, 0.06)]
mag = prof(mag_pts, 0.03)
mag = ch(mag, 0.003, "mag", mag.edges().filter_by(Axis.Y))
floor = prof([(-0.032, 0.0), (0.035, 0.0), (0.033, 0.016), (-0.028, 0.016)], 0.036)
floor = ch(floor, 0.002, "floor", floor.edges())
trigger = prof([(0.098, 0.13), (0.106, 0.13), (0.104, 0.108), (0.096, 0.112)], 0.006)
knob = Pos(0.05, -0.027, 0.19) * Box(0.016, 0.01, 0.012)
knob = ch(knob, 0.002, "knob")

PARTS = {
    "barrel": (barrel, GM),
    "handguard": (hg, BK),
    "hg_band": (band, OR),
    "receiver": (receiver, GM),
    "selector": (selector, GM),
    "grip": (grip, BK),
    "stock": (stock, BK),
    "magazine": (mag, BK),
    "mag_floor": (floor, OR),
    "trigger": (trigger, GM),
    "charging_knob": (knob, OR),
}
SPEC = {"L": 0.90, "W": 0.07, "H": 0.26}
TRI_BUDGET = 8000
