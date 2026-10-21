"""L1 easy: machined aluminium angle bracket with a gusset + a knurl-free control knob.
Checklist: counterbored holes, chamfered hole mouths, constant fillets on ALL edges, filleted internal bend."""
from cadkit import *

mm = 1.0  # authored in mm (UNITS below); worker scales to metres
T = 8 * mm                        # plate thickness
L, W, H = 90 * mm, 50 * mm, 60 * mm

# --- L profile in XZ (base along X, upright at rear +X), extruded along Y, with an inner bend radius
prof = Polygon((0, 0), (L, 0), (L, H), (L - T, H), (L - T, T), (0, T), align=None)
br = extrude(Plane.XZ * prof, amount=-W)               # Plane.XZ normal is -Y -> amount -W goes +Y
br = Pos(-L / 2, -W / 2, 0) * br
# inner bend fillet (the concave edge) and outer bend
inner = br.edges().filter_by(Axis.Y).filter_by_position(Axis.X, L / 2 - T - 1e-4, L / 2 - T + 1e-4) \
    .filter_by_position(Axis.Z, T - 1e-4, T + 1e-4)
br = safe_fillet(br, inner, 6 * mm, label="inner bend")
outer = br.edges().filter_by(Axis.Y).filter_by_position(Axis.X, L / 2 - 1e-4, L / 2 + 1e-4) \
    .filter_by_position(Axis.Z, -1e-4, 1e-4)
br = safe_fillet(br, outer, 12 * mm, label="outer bend")

# --- two triangular gussets
for y in (-W / 2 + 4 * mm, W / 2 - 4 * mm - 6 * mm):
    g = Polygon((L / 2 - T, T), (L / 2 - T, T + 32 * mm), (L / 2 - T - 32 * mm, T), align=None)
    g = Pos(0, y, 0) * extrude(Plane.XZ * g, amount=-6 * mm)
    br = fuse(br, g, "gusset")

# --- body edges: constant fillet on every sharp edge BEFORE drilling (machinist order, keeps fillet sets clean)
br = safe_fillet(br, [e for e in br.edges()], 1.5 * mm, label="all body edges")

# --- counterbored holes in the base (2) and the upright (2)
for x in (-L / 2 + 16 * mm, -L / 2 + 42 * mm):
    for y in (-12 * mm, 12 * mm) if x > -L / 2 + 20 * mm else (0,):
        hole = Pos(x, y, -1 * mm) * Cylinder(3.3 * mm, T + 2 * mm, align=(Align.CENTER, Align.CENTER, Align.MIN))
        bore = Pos(x, y, T - 3.5 * mm) * Cylinder(5.5 * mm, 4 * mm, align=(Align.CENTER, Align.CENTER, Align.MIN))
        br = cut(br, hole + bore, "cbore base")
for y in (-13 * mm, 13 * mm):
    z = 42 * mm
    hole = Pos(L / 2 + 1 * mm, y, z) * (Rot(0, -90, 0) * Cylinder(3.3 * mm, T + 2 * mm,
                                                           align=(Align.CENTER, Align.CENTER, Align.MIN)))
    bore = Pos(L / 2 - T + 3.5 * mm, y, z) * (Rot(0, 90, 0) * Cylinder(5.5 * mm, 4 * mm,
                                                                  align=(Align.CENTER, Align.CENTER, Align.MIN)))
    br = cut(br, hole + bore, "cbore upright")
# slot in base
slot = Pos(15 * mm, 0, -1 * mm) * extrude(SlotCenterToCenter(14 * mm, 6.6 * mm, rotation=90), T + 2 * mm)
br = cut(br, slot, "slot")

# --- edge treatment: chamfer hole mouths (circular edges on outer faces), fillet everything else
mouths = [e for e in br.edges() if e.geom_type == GeomType.CIRCLE and abs(e.radius - 5.5 * mm) < 1e-5
          and (abs(e.center().Z - T) < 1e-5 or abs(e.center().X - (L / 2 - T)) < 1e-5)]
br = safe_chamfer(br, mouths, 0.8 * mm, label="cbore mouths")
slot_e = [e for e in br.edges() if abs(e.center().X - (15 * mm)) < 9 * mm and abs(e.center().Y) < 4 * mm
          and abs(e.center().Z - T) < 1e-4 and e.geom_type in (GeomType.CIRCLE, GeomType.LINE)]
br = safe_fillet(br, slot_e, 0.6 * mm, label="slot rim")

# --- knob on a stud (separate part): revolved profile with a fillet+chamfer+grip flutes
kp = Polyline((0, 0), (14 * mm, 0), (14.5 * mm, 3 * mm), (13 * mm, 15 * mm), (0, 15 * mm), close=True)
knob = revolve(Plane.XZ * make_face(kp), Axis.Z)
knob = safe_fillet(knob, knob.edges().filter_by(GeomType.CIRCLE).filter_by_position(Axis.Z, 14.9 * mm, 15.1 * mm),
                   3.5 * mm, label="knob crown")
knob = safe_chamfer(knob, knob.edges().filter_by(GeomType.CIRCLE).filter_by_position(Axis.Z, -1e-4, 1e-4),
                    0.6 * mm, label="knob base")
knob = cut(knob, Pos(0, 0, 15 * mm + 30 * mm) * Sphere(30.6 * mm), "dished top")
flutes = [Rot(0, 0, i * 30) * Pos(15.6 * mm, 0, 2.2 * mm) * Cylinder(2.2 * mm, 20 * mm,
                                                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
          for i in range(12)]
knob = cut(knob, flutes, "flutes")
fl = [e for e in knob.edges() if e.geom_type != GeomType.CIRCLE and e.length > 3 * mm
      and 11 * mm < (e.center().X ** 2 + e.center().Y ** 2) ** 0.5 < 15 * mm]
knob = safe_fillet(knob, fl, 0.5 * mm, label="flute edges")
knob = Pos(-L / 2 + 16 * mm, 0, T + 0.5 * mm) * knob

PARTS = {"bracket": (br, "#b8bcc2"), "knob": (knob, "#2a2c30")}
SPEC = {"L": 0.090, "W": 0.050, "H": 0.060}
UNITS = "mm"
