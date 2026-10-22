"""Regression capture: L3 DCD777 side-profile polylines (replica/L3/model.py HOUSE / GRIP). As a periodic-spline
extrusion + rim fillet (r 14 / 9) this crashed OCCT (heap corruption 0xc0000374) / hung > 600 s in safe_fillet."""
from build123d import Plane, Spline, Vector, extrude, make_face

HOUSE = ([(-79, 29.3), (-66, 29.8), (-36, 29.4), (-30, 32.0), (-24, 32.6), (-12, 31.6), (-7, 29.1), (-3.5, 20.0),
          (-1.5, 0.0), (-3.0, -16.6), (-7.0, -23.7), (-12, -32.5), (-20, -35.0), (-79, -33.0)], 14.0)
GRIP = ([(-86, -40), (-80.2, -72.3), (-78.5, -79.2), (-77.1, -89.6), (-75.0, -96.5), (-72.5, -103.5),
         (-70.2, -110.4), (-69.1, -117.3), (-69.1, -124.3), (-70.5, -132), (-31.5, -132), (-31.9, -120.8),
         (-31.3, -110.4), (-31.6, -96.5), (-32.9, -89.6), (-34.0, -82.7), (-35.9, -75.7), (-37.7, -68.8),
         (-38.8, -61.9), (-39.0, -54.9), (-38.4, -48.0), (-37.0, -40)], 9.0)


def slab(prof, width=60.0):
    pts, r = prof
    s = extrude(make_face(Plane.XZ * Spline(*[Vector(x, z) for x, z in pts], periodic=True)), amount=width / 2,
                both=True)
    rim = [e for e in s.edges() if abs(abs(e.center().Y) - width / 2) < 1e-3]
    return s, rim, r
