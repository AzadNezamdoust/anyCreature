"""check.py <animal>  -> reads <animal>_landmarks.json + <animal>.obj, prints canon PASS/FAIL.
Landmarks are in model units; everything is normalised by BL = |x(bl0) - x(bl1)|.
Spec mini-language (per measure):
  d:a,b        straight distance             y:a        height above ground
  pl:a,b,c..   polyline length                dx:a,b / dy:a,b  |x| / |y| difference
  md:a         mesh midline depth at x(a)  (|z|<.02 band: top - bottom)
  mlow:a       mesh midline lowest y at x(a) (belly clearance)
  mw:a,b       mesh full width (z) at x(a), vertices above y(b)
  lz:a,r       local z-extent of mesh within box r (BL units) around a  (girth / hoof width)
  lx:a,r       local x-extent ;  ly:a,r  local y-extent
  px:a         x(bl0) - x(a)   (position along body from snout / chest point)
  ang:a,b      angle of a->b below horizontal (deg) ; angv:a,b  angle from vertical (deg)
  r:<s1>/<s2>  ratio of two specs ('|' separates args inside)   v:name  declared value
"""
import sys, json, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

SPEC = {
 'wolf': {
  'head_length': 'd:snout,occiput', 'head_height': 'd:head_top,jaw_low', 'muzzle_length_fraction_of_head': 'r:d|stop|snout/d|snout|occiput',
  'neck_length': 'd:poll,withers', 'withers_height': 'y:withers', 'hip_height': 'y:croup', 'chest_depth': 'md:girth',
  'belly_clearance': 'mlow:belly', 'fore_scapula': 'd:scap_top,shoulder', 'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,carpus',
  'fore_cannon': 'd:carpus,ffet', 'fore_paw': 'd:ffet,ftoe', 'elbow_height': 'y:elbow', 'hind_thigh': 'd:hip,stifle', 'hind_shin': 'd:stifle,hock',
  'hind_cannon': 'd:hock,hfet', 'hind_paw': 'd:hfet,htoe', 'hock_height': 'y:hock', 'tail_length': 'pl:tail0,tail1,tail2,tail3',
  'tail_base_girth_diameter': 'lz:tailg,0.04', 'ear_length': 'd:ear_base,ear_tip', 'body_width_ribs': 'mw:girth,elbow', 'body_width_hips': 'mw:hipx,stifle',
  'chest_width_front': 'mwb:shoulder,elbow,shoulder', 'paw_width_fore': 'lz:fpaw,0.035'},
 'horse': {
  'head_length': 'd:snout,poll', 'head_height_at_jowl': 'd:head_top,jaw_low', 'muzzle_depth': 'd:muz_top,muz_bot',
  'neck_length_poll_to_withers': 'd:poll,withers', 'withers_height': 'y:withers', 'hip_height_croup': 'y:croup', 'chest_depth': 'md:girth',
  'belly_clearance': 'mlow:belly', 'elbow_height': 'y:elbow', 'fore_scapula': 'd:scap_top,shoulder', 'fore_upper_arm': 'd:shoulder,elbow',
  'fore_forearm': 'd:elbow,carpus', 'fore_cannon': 'd:carpus,ffet', 'fore_pastern': 'd:ffet,fcor', 'hoof_height': 'y:fcor', 'hoof_width': 'lz:fhoof,0.07',
  'knee_height': 'y:carpus', 'hind_thigh': 'd:hip,stifle', 'hind_gaskin': 'd:stifle,hock', 'hind_cannon': 'd:hock,hfet', 'hind_pastern': 'd:hfet,hcor',
  'hock_height': 'y:hock', 'stifle_height': 'y:stifle', 'tail_dock_length': 'pl:tail0,tail1,tail2', 'tail_hair_total_length': 'pl:tail0,tail1,tail2,tail3',
  'tail_base_girth_diameter': 'lz:tailg,0.04', 'ear_length': 'd:ear_base,ear_tip', 'eye_position_from_poll_fraction_of_head': 'r:d|poll|eye/d|poll|snout',
  'body_width_ribs': 'mw:girth,elbow', 'body_width_hips': 'mw:hipx,stifle', 'shoulder_slope_degrees': 'ang:scap_top,shoulder'},
 'elephant': {
  'head_length_forehead_to_occiput': 'd:forehead,occiput', 'head_height': 'd:head_top,jaw_low', 'trunk_length': 'pl:trunk0,trunk1,trunk2,trunk3',
  'neck_length': 'd:occiput,withers_front', 'withers_height': 'y:withers', 'hip_height': 'y:croup', 'chest_depth': 'md:girth', 'belly_clearance': 'mlow:belly',
  'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,carpus', 'fore_foot_height': 'y:carpus_low', 'fore_foot_diameter': 'lx:ffoot,0.11',
  'wrist_height': 'y:carpus', 'hind_thigh': 'd:hip,stifle', 'hind_shin': 'd:stifle,hock', 'hind_foot_diameter': 'lz:hfoot,0.1', 'hock_height': 'y:hock',
  'knee_stifle_height': 'y:stifle', 'tail_length': 'pl:tail0,tail1,tail2', 'tail_base_girth_diameter': 'lz:tailg,0.04', 'ear_length_african': 'd:ear_top,ear_bot',
  'ear_width_african': 'd:ear_front,ear_back', 'ear_area_african_fraction_of_body_length_squared': 'v:ear_area', 'tusk_visible_length_african_male': 'pl:tusk0,tusk1,tusk2',
  'body_width_ribs': 'mw:girth,elbow', 'body_width_hips': 'mw:hipx,stifle', 'leg_column_diameter_fore': 'lx:fcol,0.1'},
 'giraffe': {
  'head_length': 'd:snout,poll', 'head_height': 'd:head_top,jaw_low', 'neck_length': 'd:poll,withers_front', 'neck_base_diameter': 'v:neck_base_d',
  'ossicone_length': 'd:oss0,oss1', 'withers_height': 'y:withers', 'hip_height': 'y:croup', 'total_height_to_crown': 'y:crown', 'chest_depth': 'md:girth',
  'belly_clearance': 'mlow:belly', 'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,carpus', 'fore_cannon': 'd:carpus,ffet', 'fore_pastern': 'd:ffet,fcor',
  'knee_height': 'y:carpus', 'hind_thigh': 'd:hip,stifle', 'hind_shin': 'd:stifle,hock', 'hind_cannon': 'd:hock,hfet', 'hock_height': 'y:hock',
  'tail_dock_length': 'pl:tail0,tail1,tail2', 'tail_with_tuft_length': 'pl:tail0,tail1,tail2,tail3', 'tail_base_girth_diameter': 'lz:tailg,0.035',
  'ear_length': 'd:ear_base,ear_tip', 'hoof_width': 'lz:fhoof,0.07', 'body_width_ribs': 'mw:girth,elbow', 'body_width_hips': 'mw:hipx,stifle'},
 'crocodile': {
  'head_length': 'd:snout,occiput', 'head_height': 'ly:headmid,0.01,0.2', 'head_width_at_jaw_joint': 'lz:jawjoint,0.01,0.2', 'snout_width_at_tip_fraction_of_head': 'r:lz|snoutw|0.01|0.2/d|snout|occiput',
  'neck_length': 'd:occiput,shoulder_c', 'hip_height_resting': 'y:croup', 'withers_height_resting': 'y:withers', 'chest_depth': 'md:girth',
  'belly_clearance_resting': 'mlow:belly', 'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,wrist', 'fore_hand': 'd:wrist,ftoe',
  'hind_thigh': 'd:hip,knee', 'hind_shin': 'd:knee,ankle', 'hind_foot': 'd:ankle,htoe', 'hock_height_resting': 'y:ankle', 'tail_length': 'pl:vent,tail1,tail2,tail3',
  'tail_base_girth_height': 'ly:tailg,0.01,0.25', 'tail_base_girth_width': 'lz:tailg,0.01,0.25', 'tail_single_keel_starts_at_fraction_of_tail': 'v:keel_merge',
  'body_width_ribs': 'mw:girth,belly', 'body_width_hips': 'mw:hipx,belly', 'eye_height_above_skull_table': 'dy:eye_top,skull_table',
  'total_length_head_to_tail_tip': 'pl:snout,occiput,vent,tail1,tail2,tail3'},
 'eagle': {
  'head_length_bill_tip_to_occiput': 'd:bill_tip,occiput', 'head_height': 'd:head_top,head_bot', 'bill_length_exposed_culmen': 'd:cere,bill_tip',
  'bill_depth': 'd:bill_top,bill_bot', 'neck_length': 'd:neck0,occiput', 'perched_height_perch_to_crown': 'dy:crown,perch', 'chest_depth': 'v:chest_depth',
  'body_width_at_breast': 'mw:breast,breast_lo', 'tibia_feathered_trouser': 'd:knee,ankle', 'tarsus_length': 'd:ankle,foot', 'tarsus_exposed_above_toes': 'd:trouser_end,foot',
  'toe_span_front_to_hallux': 'd:toe_front,hallux_tip', 'hallux_talon_length': 'd:hallux_base,hallux_tip', 'tail_length': 'd:tail_base,tail_tip',
  'tail_base_width': 'lz:tail_base_m,0.02,0.3', 'folded_wing_wrist_to_tip': 'd:wrist,wing_tip', 'wingtip_vs_tail_tip_bald': 'v:wingtip_vs_tail',
  'eye_diameter': 'v:eye_d', 'body_axis_angle_from_vertical_degrees': 'angv:bl1,bl0'},
 'shark': {
  'head_length_snout_to_5th_gill': 'px:gill5', 'head_height': 'ly:headmid,0.01,0.2', 'snout_tip_to_eye': 'px:eye', 'snout_tip_to_mouth': 'px:mouth',
  'mouth_width': 'lz:mouth,0.012,0.1', 'eye_diameter': 'v:eye_d', 'body_max_depth': 'md:maxd', 'body_width_at_pectorals': 'mw:pecw,pec_lo',
  'position_of_max_depth': 'px:maxd', 'caudal_peduncle_depth': 'md:ped', 'gill_slit_region_length': 'dx:gill1,gill5', 'pectoral_fin_length': 'd:pec0,pec_tip',
  'pectoral_fin_base': 'd:pec0,pec1', 'pectoral_origin': 'px:pec0', 'first_dorsal_height': 'dy:d1_tip,d1_0', 'first_dorsal_base': 'd:d1_0,d1_1',
  'first_dorsal_origin': 'px:d1_0', 'second_dorsal_height': 'dy:d2_tip,d2_0', 'second_dorsal_origin': 'px:d2_0', 'pelvic_fin_origin': 'px:pv0',
  'pelvic_fin_length': 'd:pv0,pv_tip', 'anal_fin_origin': 'px:an0', 'caudal_upper_lobe_length': 'd:bl1,cu_tip',
  'caudal_lower_lobe_fraction_of_upper_white_shark': 'r:d|bl1|cl_tip/d|bl1|cu_tip', 'total_length_including_tail': 'px:cu_tip'},
 'frog': {
  'head_length_snout_to_occiput': 'd:snout,occiput', 'head_width': 'mwb:headw,headw_lo,headw_hi', 'head_height': 'md:headh', 'eye_diameter': 'v:eye_d',
  'eye_protrusion_above_skull': 'dy:eye_top,skull_top', 'tympanum_diameter': 'v:tymp_d', 'interorbital_width': 'v:interorb',
  'sitting_height_ground_to_sacral_hump': 'y:sacrum', 'sitting_height_ground_to_eye_top': 'y:eye_top', 'body_width_max': 'mw:bodyw,belly_ref',
  'belly_clearance_sitting': 'mlow:belly', 'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,wrist', 'fore_hand_with_fingers': 'd:wrist,ftoe',
  'hind_thigh': 'd:hip,knee', 'hind_shin_tibiofibula': 'd:knee,heel', 'hind_tarsus': 'd:heel,tarsus_end', 'hind_foot_with_toes': 'd:tarsus_end,htoe',
  'hind_limb_total': 'pl:hip,knee,heel,tarsus_end,htoe', 'knee_position_sitting_fraction_along_body': 'px:knee', 'heel_position_sitting_fraction_along_body': 'px:heel'},
 'tortoise': {
  'carapace_width': 'mw:shellmid,shell_lo', 'carapace_height': 'dy:shell_top,shell_lo', 'plastron_length': 'd:plas0,plas1', 'head_length': 'd:snout,occiput',
  'head_height': 'ly:headmid,0.01,0.2', 'head_width': 'lz:headmid,0.01,0.2', 'neck_length_extended': 'd:occiput,neck0', 'standing_height_ground_to_shell_top': 'y:shell_top',
  'belly_clearance_plastron_to_ground': 'mlow:shellmid', 'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,fwrist', 'fore_foot_height': 'y:fwrist',
  'forelimb_exposed_length_shell_edge_to_ground': 'y:fexp', 'forelimb_column_width': 'lx:fcol,0.1', 'hind_thigh': 'd:hip,knee', 'hind_shin': 'd:knee,hankle',
  'hind_foot_diameter': 'lx:hfoot,0.08', 'hindlimb_exposed_length': 'y:hexp', 'tail_length': 'd:tail0,tail1', 'tail_base_girth_diameter': 'lz:tailg,0.01,0.1',
  'body_width_ribs': 'mw:shellmid,shell_lo', 'body_width_hips': 'mw:hipx,hipx'},
 'kangaroo': {
  'head_length': 'd:snout,occiput', 'head_height': 'd:head_top,jaw_low', 'muzzle_length_fraction_of_head': 'r:d|stop|snout/d|snout|occiput', 'ear_length': 'd:ear_base,ear_tip',
  'neck_length': 'd:occiput,neck0', 'resting_height_ground_to_crown': 'y:crown', 'hip_height_resting': 'y:hip', 'shoulder_height_resting': 'y:shoulder',
  'chest_depth': 'v:chest_depth', 'belly_clearance_resting': 'mlow:belly_low', 'fore_upper_arm': 'd:shoulder,elbow', 'fore_forearm': 'd:elbow,wrist', 'fore_hand': 'd:wrist,ftoe',
  'forelimb_total': 'pl:shoulder,elbow,wrist,ftoe', 'hind_thigh': 'd:hip,knee', 'hind_shin': 'd:knee,heel', 'hind_metatarsus': 'd:heel,mtp', 'hind_toes_4th_toe': 'd:mtp,htoe',
  'hind_foot_total_heel_to_claw': 'd:heel,htoe', 'hindlimb_total': 'pl:hip,knee,heel,mtp,htoe', 'hind_to_fore_limb_ratio': 'r:pl|hip|knee|heel|mtp|htoe/pl|shoulder|elbow|wrist|ftoe',
  'hock_height_resting': 'y:heel', 'tail_length': 'pl:tail0,tail1,tail2,tail3', 'tail_base_girth_diameter': 'lz:tailg,0.01,0.2', 'tail_base_girth_height': 'v:tail_h',
  'thigh_width_side_view': 'v:thigh_w', 'body_width_ribs': 'mwb:girth,rib_lo,rib_hi', 'body_width_hips': 'v:hip_w', 'spine_angle_from_vertical_resting_degrees': 'angv:bl1,bl0'},
}


def load_obj(p):
    V = []
    for line in open(p):
        if line.startswith('v '): V.append([float(x) for x in line.split()[1:4]])
    return np.array(V)


class M:
    def __init__(s, L, V):
        s.P = {k: np.array(v, float) for k, v in L['points'].items()}; s.vals = L.get('values', {}); s.V = V
        s.BL = abs(s.P['bl0'][0] - s.P['bl1'][0]) if 'bl_len' not in L else L['bl_len']
        s.h = 0.012 * s.BL
    def p(s, n): return s.P[n]
    def ev(s, spec):
        kind, arg = spec.split(':', 1)
        a = arg.replace('|', ',').split(',') if kind == 'r' else arg.split(',')
        P, V, B = s.p, s.V, s.BL
        if kind == 'r':
            n, d = arg.split('/'); return s.ev(n.replace('|', ':', 1).replace('|', ',')) / s.ev(d.replace('|', ':', 1).replace('|', ','))
        if kind == 'd': return np.linalg.norm(P(a[0]) - P(a[1])) / B
        if kind == 'pl': return sum(np.linalg.norm(P(a[i]) - P(a[i + 1])) for i in range(len(a) - 1)) / B
        if kind == 'y': return P(a[0])[1] / B
        if kind == 'dx': return abs(P(a[0])[0] - P(a[1])[0]) / B
        if kind == 'dy': return (P(a[0])[1] - P(a[1])[1]) / B
        if kind == 'px': return abs(P('bl0')[0] - P(a[0])[0]) / B
        if kind == 'v': return s.vals[a[0]]
        if kind in ('ang', 'angv'):
            v = P(a[1]) - P(a[0]); ang = math.degrees(math.atan2(-v[1], math.hypot(v[0], v[2])))
            return abs(ang) if kind == 'ang' else 90 - abs(ang)
        x0 = P(a[0])[0]; band = V[np.abs(V[:, 0] - x0) < s.h]
        if kind == 'md':
            m = band[np.abs(band[:, 2]) < 0.02 * B]; return (m[:, 1].max() - m[:, 1].min()) / B
        if kind == 'mlow':
            m = band[np.abs(band[:, 2]) < 0.02 * B]; return m[:, 1].min() / B
        if kind == 'mw':
            m = band[band[:, 1] > P(a[1])[1]]; return (m[:, 2].max() - m[:, 2].min()) / B
        if kind == 'mwb':
            m = band[(band[:, 1] > P(a[1])[1]) & (band[:, 1] < P(a[2])[1])]; return (m[:, 2].max() - m[:, 2].min()) / B
        if kind in ('lz', 'lx', 'ly'):
            r = float(a[1]) * B; R = float(a[2]) * B if len(a) > 2 else r; c = P(a[0]); ax = {'lx': 0, 'ly': 1, 'lz': 2}[kind]
            lim = np.full(3, r); lim[ax] = R; m = V[np.all(np.abs(V - c) < lim, 1)]
            return (m[:, ax].max() - m[:, ax].min()) / B
        raise ValueError(spec)


def run(animal, quiet=False):
    L = json.load(open(os.path.join(HERE, animal + '_landmarks.json')))
    V = load_obj(os.path.join(HERE, animal + '.obj'))
    canon = json.load(open(os.path.join(HERE, 'canon.json')))[animal]['measures']
    m = M(L, V); npass = ntot = 0; fails = []
    for name, rng in canon.items():
        spec = SPEC[animal].get(name)
        if spec is None or not isinstance(rng, list):
            if not quiet: print(f'  {name:55s} n/a  (canon {rng})')
            continue
        try: val = m.ev(spec)
        except Exception as e:
            print(f'  {name:55s} ERROR {e!r}'); ntot += 1; fails.append(name); continue
        lo, hi = rng; ok = lo - 1e-3 <= val <= hi + 1e-3; ntot += 1; npass += ok
        if not ok: fails.append(name)
        if not quiet or not ok: print(f'  {name:55s} {val:8.3f}  [{lo}, {hi}]  {"PASS" if ok else "FAIL"}')
    print(f'{animal}: {npass}/{ntot} PASS  (BL={m.BL:.3f}, verts={len(V)})')
    return npass, ntot, fails


if __name__ == '__main__':
    for a in [x for x in sys.argv[1:] if not x.startswith('-')]: run(a, quiet='-q' in sys.argv)
