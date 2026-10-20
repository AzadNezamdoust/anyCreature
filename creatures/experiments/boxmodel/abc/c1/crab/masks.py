"""Hand edits of the carve input (crab): the carve keeps the carapace and the two claws only.
A visual hull turns eight splayed legs into walls (round 1), so every view's mask is clipped to
KEEP polygons (world metres) and the walking legs are extruded by hand in stage 1.
side: (y, z); front: (x, z) (x >= 0, mirrored); top: (x, y) (x >= 0, mirrored)."""
import math

def ellipse(cx, cy, rx, ry, n=48):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]

KEEP = {
    'side': [
        # carapace + belly (below the eye ball, above the leg tips)
        [(-0.33, 0.325), (-0.18, 0.355), (-0.05, 0.395), (0.25, 0.36), (0.42, 0.25), (0.40, 0.14),
         (0.30, 0.09), (-0.05, 0.09), (-0.20, 0.15), (-0.30, 0.22)],
        # the claw: arm, palm, both fingers
        [(-0.68, 0.20), (-0.55, 0.30), (-0.40, 0.33), (-0.28, 0.29), (-0.15, 0.27), (-0.11, 0.18),
         (-0.20, 0.11), (-0.32, 0.08), (-0.45, 0.04), (-0.60, 0.07), (-0.68, 0.11)],
    ],
    'front': [
        [(-0.01, -0.01), (0.47, -0.01), (0.47, 0.42), (-0.01, 0.42)],
    ],
    'top': [
        # carapace disc (x, y)
        [(x, y) for y, x in ellipse(0.045, 0.0, 0.34, 0.315)],
        # the claw, legs excluded, the eye ball excluded
        [(0.05, -0.72), (0.50, -0.72), (0.50, -0.30), (0.40, -0.22), (0.33, -0.16), (0.20, -0.12),
         (0.22, -0.30), (0.12, -0.45)],
    ],
}
