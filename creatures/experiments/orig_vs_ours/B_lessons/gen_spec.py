"""Generates crocodile.json from the measured brief (L = 2.0 m). Numbers trace to brief.md."""
import json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
L = 2.0
def m(u): return round(u * L, 4)

SA = 28          # planar look: walls 30 deg on 12 sides -> crisp flat planes
OLIVE, CREAM, SCUTE = '#6e7a46', '#d8c693', '#4a5624'

# --- skeleton (absolute metres) ---
J = {
  'Hips':     [0, 0.170, 0.00],
  'Spine':    [0, 0.172, 0.20],
  'Chest':    [0, 0.170, 0.42],
  'Neck':     [0, 0.166, 0.60],
  'HeadRoot': [0, 0.168, 0.55],
  'Skull':    [0, 0.182, 0.70],
  'Snout':    [0, 0.170, 0.76],
  'Nose':     [0, 0.148, 0.975],
  'TailRoot': [0, 0.168, 0.06],
  'T1':       [0.00, 0.152, -0.20],
  'T2':       [0.04, 0.122, -0.55],
  'TailTip':  [0.11, 0.085, -0.97],
  'LFShoulder': [0.085, 0.150, 0.45],
  'LFElbow':    [0.185, 0.120, 0.45],
  'LFWrist':    [0.205, 0.040, 0.47],
  'LFToe':      {'from': 'LFWrist', 'side': 0.02, 'fwd': 0.03, 'ground': 0.018},
  'LBHip':      [0.085, 0.150, 0.11],
  'LBKnee':     [0.195, 0.125, 0.13],
  'LBAnkle':    [0.215, 0.040, 0.09],
  'LBToe':      {'from': 'LBAnkle', 'side': 0.02, 'fwd': 0.03, 'ground': 0.018},
}
chains = {
  'body': ['Hips', 'Spine', 'Chest', 'Neck'],
  'head': ['HeadRoot', 'Skull', 'Snout', 'Nose'],
  'tail': ['TailRoot', 'T1', 'T2', 'TailTip'],
  'LFrontLeg': ['LFShoulder', 'LFElbow', 'LFWrist', 'LFToe'],
  'LBackLeg': ['LBHip', 'LBKnee', 'LBAnkle', 'LBToe'],
}
belly = lambda t=None: dict({'from': 92, 'to': 180, 'color': CREAM, 'feather': 50}, **({'t': t} if t else {}))

# profiles: [t, half-width, half-height, opts]  (brief: trunk w 0.14 L, h 0.10 L)
body_prof = [[0.0, 0.118, 0.092, {'exp': 2.6}],
             [0.30, 0.140, 0.100, {'exp': 2.7, 'bias': -0.15}],
             [0.62, 0.142, 0.100, {'exp': 2.7, 'bias': -0.15}],
             [0.86, 0.118, 0.088, {'exp': 2.6, 'bias': -0.05}],
             [1.0, 0.098, 0.078, {'exp': 2.6}]]
head_prof = [[0.0, 0.092, 0.072, {'exp': 3.0}],
             [0.28, 0.104, 0.074, {'exp': 3.2, 'taper': 0.25}],          # skull, widest
             [0.40, 0.084, 0.056, {'exp': 3.2, 'taper': 0.15, 'sharp': True}],  # eye step -> snout
             [0.72, 0.064, 0.044, {'exp': 3.2, 'taper': 0.1}],
             [1.0, 0.054, 0.036, {'exp': 3.0}]]
tail_prof = [[0.0, 0.118, 0.092, {'exp': 2.6}],
             [0.25, 0.088, 0.078, {'exp': 2.6}],
             [0.55, 0.050, 0.058, {'exp': 2.4}],
             [0.80, 0.026, 0.036],
             [1.0, 0.010, 0.012]]
fleg_prof = [[0.0, 0.070, 0.070], [0.25, 0.060, 0.055], ['LFElbow', 0.046, 0.046], [0.75, 0.036, 0.038], [1.0, 0.034, 0.030]]
bleg_prof = [[0.0, 0.078, 0.076], [0.25, 0.068, 0.060], ['LBKnee', 0.050, 0.050], [0.75, 0.038, 0.040], [1.0, 0.035, 0.030]]

volumes = [
  {'chain': 'body', 'material': 'skin_body', 'frame': 'up', 'sides': 10, 'ring_step': 0.06,
   'profile': body_prof, 'caps': ['dome', 'dome'], 'cap_depth': [0.5, 0.5], 'colors': {'arcs': [belly()]}},
  {'chain': 'head', 'material': 'skin_head', 'frame': 'up', 'sides': 12, 'ring_step': 0.05,
   'profile': head_prof, 'caps': ['none', 'dome'], 'cap_depth': [0.5, 0.45], 'colors': {'arcs': [belly()]}},
  {'chain': 'tail', 'material': 'skin_tail', 'frame': 'up', 'sides': 10, 'ring_step': 0.07,
   'profile': tail_prof, 'caps': ['none', 'dome'], 'cap_depth': [0.5, 0.8], 'colors': {'arcs': [belly([0.0, 0.85])]}},
  {'chain': 'LFrontLeg', 'material': 'skin_leg', 'sides': 10, 'ring_step': 0.03, 'profile': fleg_prof,
   'caps': ['none', 'dome'], 'cap_depth': [0.5, 0.5]},
  {'chain': 'LBackLeg', 'material': 'skin_leg', 'sides': 10, 'ring_step': 0.03, 'profile': bleg_prof,
   'caps': ['none', 'dome'], 'cap_depth': [0.5, 0.5]},
]

# --- top surface along z (centre y + half-height), for seating the scute row ---
def lerp(a, b, f): return a + (b - a) * f
def top_y(z):
    if z >= 0:   # body: Hips z0 .. Neck z0.6
        t = z / 0.60
        pts = [(p[0], p[2]) for p in body_prof]; cy = 0.170 - 0.004 * t
    else:        # tail: z 0 .. -0.97 (approx arc-length on z)
        t = (0.06 - z) / 1.03
        pts = [(p[0], p[2]) for p in tail_prof]
        cy = lerp(0.168, 0.085, t) if t > 0.6 else lerp(0.168, 0.120, t / 0.64)
    for (t0, h0), (t1, h1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return cy + lerp(h0, h1, (t - t0) / (t1 - t0))
    return cy + pts[-1][1]
def tail_x(z):  # tail drifts to +x
    t = (0.06 - z) / 1.03
    return 0.0 if t < 0.33 else lerp(0.0, 0.11, (t - 0.33) / 0.67) ** 1.0
def nearest_host(z):
    cand = [('Hips', J['Hips']), ('Spine', J['Spine']), ('Chest', J['Chest']), ('Neck', J['Neck'])] if z >= 0 else \
           [('TailRoot', J['TailRoot']), ('T1', J['T1']), ('T2', J['T2']), ('TailTip', J['TailTip'])]
    return min(cand, key=lambda c: abs(c[1][2] - z))

parts = []
# 11 dorsal scutes, back + tail, shrinking toward the tail tip (brief: r 0.016 L -> 0.006 L)
N = 11
zs = [0.50 - i * (1.30 / (N - 1)) for i in range(N)]   # z 0.50 .. -0.80
for i, z in enumerate(zs):
    f = i / (N - 1)
    r = round(lerp(m(0.016), m(0.006), f), 4)
    h = round(r * 1.25, 4)
    x = tail_x(z) if z < 0 else 0.0
    y = top_y(z) - r * 0.45
    hn, hp = nearest_host(z)
    parts.append({'name': f'scute_{i+1:02d}', 'type': 'curve', 'host': hn, 'material': 'scute',
                  'join': 'insert', 'sides': 8, 'shade': 'flesh',
                  'offset': [round(x - hp[0], 4), round(y - hp[1], 4), round(z - hp[2], 4)],
                  'dir': [0, 1, -0.25],
                  'segments': [{'len': round(h * 0.6, 4), 'r': [r, round(r * 1.3, 4)]},
                               {'len': round(h * 0.4, 4), 'r': [round(r * 0.75, 4), round(r * 0.95, 4)]}],
                  'cap': 'dome', 'cap_depth': 0.9, 'smooth_angle': SA})

# chunky blunt teeth: 3 per side down from the upper jaw edge (brief r 0.008 L)
for k, (z, hw, cy, hh) in enumerate([(0.80, 0.075, 0.166, 0.050), (0.88, 0.064, 0.159, 0.043), (0.95, 0.057, 0.151, 0.038)]):
    hn = 'Snout' if z < 0.9 else 'Nose'; hp = J[hn]
    parts.append({'name': f'tooth_{k+1}', 'type': 'curve', 'host': hn, 'material': 'tooth', 'mirrored': True,
                  'join': 'insert', 'sides': 6,
                  'offset': [round(hw * 0.86 - hp[0], 4), round(cy - hh * 0.55 - hp[1], 4), round(z - hp[2], 4)],
                  'dir': [0.25, -1, 0.05],
                  'segments': [{'len': 0.022, 'r': 0.013}, {'len': 0.018, 'r': 0.008, 'taper': True}],
                  'cap': 'dome', 'cap_depth': 0.6, 'smooth_angle': SA})

parts += [
  {'name': 'eye', 'type': 'eye', 'host': 'Skull', 'material': 'eye', 'size': 0.02,
   'anchor': {'chain': 'head', 't': 0.30, 'around': 50}, 'sink': 0.3,
   'pupil': {'material': 'pupil', 'size': 0.6}},
  {'name': 'front_foot', 'type': 'paw', 'host': 'LFToe', 'material': 'foot', 'mirrored': True,
   'size': [0.085, 0.095, 0.034], 'toes': 4, 'dir': [0.45, 0, 0.9], 'claws': True, 'claw_material': 'claw'},
  {'name': 'back_foot', 'type': 'paw', 'host': 'LBToe', 'material': 'foot', 'mirrored': True,
   'size': [0.095, 0.10, 0.036], 'toes': 4, 'dir': [0.55, 0, 0.83], 'claws': True, 'claw_material': 'claw'},
]

anims = {
  'idle': {'duration': 2.6, 'loop': True, 'tracks': {
    'Hips': {'ty': [[0, 0], [0.5, 0.004], [1, 0]]},
    'Skull': {'rx': [[0, 0], [0.5, -2], [1, 0]]},
    'T1': {'ry': [[0, 4], [0.5, -4], [1, 4]]},
    'T2': {'ry': [[0, -3], [0.25, 4], [0.75, -5], [1, -3]]}}},
  'move': {'duration': 1.0, 'loop': True, 'mirror_phase': 0.5, 'tracks': {
    'LFShoulder': {'rx': [[0, -22], [0.5, 18], [1, -22]], 'rz': [[0, 0], [0.5, 0], [0.75, 14], [1, 0]]},
    'LBHip': {'rx': [[0, 18], [0.5, -22], [1, 18]], 'rz': [[0, 0], [0.25, 14], [0.5, 0], [1, 0]]},
    'Spine': {'ry': [[0, 5], [0.5, -5], [1, 5]]},
    'T1': {'ry': [[0, -7], [0.5, 7], [1, -7]]},
    'T2': {'ry': [[0, -6], [0.5, 8], [1, -6]]}}},
  'attack': {'duration': 0.8, 'loop': False, 'tracks': {
    'Hips': {'tz': [[0, 0], [0.3, -0.08], [0.55, 0.38], [0.8, 0.12], [1, 0]]},
    'Neck': {'rx': [[0, 0], [0.3, -8], [0.55, 5], [1, 0]]},
    'Skull': {'rx': [[0, 0], [0.3, -8], [0.55, 6], [1, 0]]},
    'T1': {'ry': [[0, 0], [0.3, 12], [0.6, -14], [1, 0]]},
    'LFShoulder': {'rx': [[0, 0], [0.3, 10], [0.55, -16], [1, 0]]},
    'LBHip': {'rx': [[0, 0], [0.3, -10], [0.55, 14], [1, 0]]}}},
}
jr = {
  'Hips': {'rx': [-15, 15], 'ry': [-15, 15], 'rz': [-10, 10]},
  'Spine': {'rx': [-15, 15], 'ry': [-20, 20], 'rz': [-10, 10]},
  'Chest': {'rx': [-15, 15], 'ry': [-20, 20]},
  'Neck': {'rx': [-25, 20], 'ry': [-30, 30]},
  'HeadRoot': {'rx': [-20, 15], 'ry': [-30, 30]},
  'Skull': {'rx': [-20, 15], 'ry': [-20, 20]},
  'Snout': {'rx': [-5, 5]}, 'Nose': {'rx': [-5, 5]},
  'TailRoot': {'rx': [-20, 20], 'ry': [-35, 35]},
  'T1': {'rx': [-20, 20], 'ry': [-35, 35]},
  'T2': {'rx': [-20, 20], 'ry': [-40, 40]},
  'TailTip': {'rx': [-20, 20], 'ry': [-40, 40]},
  'LFShoulder': {'rx': [-40, 40], 'ry': [-30, 30], 'rz': [-30, 40]},
  'LFElbow': {'rx': [-30, 30]}, 'LFWrist': {'rx': [-30, 30]}, 'LFToe': {'rx': [-20, 20]},
  'LBHip': {'rx': [-40, 40], 'ry': [-30, 30], 'rz': [-30, 40]},
  'LBKnee': {'rx': [-30, 30]}, 'LBAnkle': {'rx': [-30, 30]}, 'LBToe': {'rx': [-20, 20]},
}
spec = {
  'name': 'crocodile', 'height': float(sys.argv[1]) if len(sys.argv) > 1 else 0.31,
  'smooth_angle': SA,
  'shading': {'normals': {'flesh': 0.0}},
  'palette': {
    'skin_body': {'color': OLIVE, 'rough': 0.9}, 'skin_head': {'color': OLIVE, 'rough': 0.9},
    'skin_tail': {'color': OLIVE, 'rough': 0.9}, 'skin_leg': {'color': OLIVE, 'rough': 0.9},
    'foot': {'color': '#646f42', 'rough': 0.9}, 'scute': {'color': SCUTE, 'rough': 0.85},
    'claw': {'color': '#3a3b3d', 'rough': 0.6}, 'tooth': {'color': '#ece3c6', 'rough': 0.5},
    'eye': {'color': '#e3a21c', 'rough': 0.3}, 'pupil': {'color': '#161616', 'rough': 0.3}},
  'joints': J, 'chains': chains,
  'attach': {'head': 'Neck', 'tail': 'Hips', 'LFrontLeg': 'Chest', 'LBackLeg': 'Hips'},
  'mirror': ['LFrontLeg', 'LBackLeg'],
  'touch': [['body', 'tail'], ['body', 'head']],
  'function': {'body': 'axis', 'head': 'effector', 'tail': 'ornament', 'LFrontLeg': 'locomotion', 'LBackLeg': 'locomotion'},
  'claims': [
    {'type': 'part_exists', 'part': 'skin_tail', 'stage': 'MID', 'label': 'signature part must exist', 'enforce': 'block', 'when': 'verify'},
    {'type': 'part_signature', 'part': 'skin_tail', 'view': 'side', 'min_share': 0.16, 'or_min_span': 0.12, 'stage': 'MID', 'label': 'signature presence', 'enforce': 'advise', 'when': 'allocate'},
    {'type': 'focal_contrast', 'a': 'skin_head', 'b': 'scute', 'min_ratio': 2, 'stage': 'MID', 'label': 'focal points must not be equal weight', 'enforce': 'advise', 'when': 'allocate'},
    {'type': 'share_hierarchy', 'primary': ['skin_body', 'skin_tail'], 'secondary': ['skin_head'], 'tertiary': ['scute', 'foot', 'tooth', 'claw', 'eye'], 'stage': 'MID', 'label': '631 hierarchy', 'enforce': 'advise', 'when': 'allocate'},
    {'type': 'orbit_consistent', 'stage': 'LOW', 'enforce': 'advise', 'when': 'verify'},
    {'type': 'head_reads', 'stage': 'LOW', 'enforce': 'advise', 'when': 'verify'},
    {'type': 'rig_skinned', 'stage': 'HIGH', 'enforce': 'block', 'when': 'verify'},
    {'type': 'anim_named', 'names': ['idle', 'move', 'attack'], 'stage': 'HIGH', 'enforce': 'block', 'when': 'verify'},
    {'type': 'saturation_area', 'view': 'tq', 'min': 0.1, 'max': 0.5, 'stage': 'HIGH', 'enforce': 'advise', 'when': 'allocate'},
    {'type': 'tri_budget', 'min': 4000, 'max': 9000, 'stage': 'LOW', 'enforce': 'advise', 'when': 'allocate'}],
  'volumes': volumes, 'parts': parts, 'animations': anims, 'joint_range': jr,
}
out = os.path.join(HERE, 'crocodile.json')
json.dump(spec, open(out, 'w'), indent=1)
print('wrote', out)
