# frog (t7) NOTES

No reference folder: stage 0 blueprint written by hand (side/front/top) from the brief's sizes.

## Stage 1
- r01: Critique: eyes are tall square posts (read as rabbit ears in az000/az180); 4 self-intersections. Diagnosis: eye chain E1/E2 rise 0.095 above the head with a narrow top. Fix: shorter, wider bulge (E1 wider than base at z .228, E2 at .262); added a HIT debug print to locate the intersections. 460 tris.
- r02: eyes now low wide bulges (better; still boxy from the top). Critique: 2 hits, at the knee (0.26,-0.045) and the heel (0.31,0.16): the 90-degree single-step turns tie in the corner matching and twist. Fix: a `bend()` U-turn in three 60-degree sections swinging round a pivot at the inside of the fold (knee pivot (0.258,-0.035), heel pivot (0.316,0.14)).
- r03: gates PASS (492 tris). Critique: from the top the hind leg is a thin hairpin (thigh and shin parallel planks), and the thigh is no drumstick; lizard, not frog. Diagnosis: thigh sections h .038/.032, ankle straight behind the knee (x .292). Fix: fatter thigh (h .046, v .048 at the hip; .036/.040 at the knee) and the shin angled out (ankle x .315) so the Z opens in plan; foot re-seated outside it.
- r04: leg Z opens a little in plan; thigh fatter (492 tris). Critique: side view reads as a long loaf/slug, not a squat pear frog: the rump is high off the ground and narrow. Diagnosis: RINGS 6-9 (zb .028-.04, hw .135-.14, gentle top drop). Fix: pear profile: rear rings sit down (zb .012-.02), widest at R6 (hw .146), steeper drop over the rump, taller rear side band (lip gap .052/.056) so the thigh root is broader.
- r05: pear body sits down on the rump (better from az090/az135; 492 tris). Critique: the hind leg is still a stack of crates (az090, hero): square sections with vertical walls. Diagnosis: sec() gives rectangles. Fix: trapezoid sections (top edge narrowed: thigh .5, knee .55-.6, shin .6, foot .75-.8) so the thigh reads as a mound and the shin/foot as bevelled slabs.
- r06: trapezoid sections: the leg now reads as a folded frog Z in plan and a mound from the side (492 tris). Critique: the eye bulges are square boxes from the top and the front (az000, top). Diagnosis: E2 is the same square as E1. Fix: E2 top turned 40 degrees about Z, so the bulge shows eight corners (a faceted dome) instead of a box.
- r07: eye tops turned 40 deg read as faceted domes. Reads as a squat frog from every view: LOCKED (492 tris, edge sha faa91e5daccc7ee0). Min blueprint IoU 0.778 (top; my own hand-drawn blueprint over-estimated the knee spread).

## Stage 2
- r01: hip loop (thigh root) and shoulder loop (upper arm) for the bends; eye socket inset on each eye-bulge top; upper lip overhang (chin verts back .008), throat sac (-.006), dorsolateral ridge (v1 of rings 4-8 up .007, out .004).
- r01 result: all gates PASS, min IoU vs stage 1 0.986, 572 tris. Note: the second loop's edge pick landed on the R4-R5 body band, so it became a chest loop (runs on down the front of the upper arm); reason text corrected, kept because the head nods there.

## Stage 3
- r01: palette skin/spot/belly/gold/black (5). Mouth = the lip strip faces (v3-v4 band, head rings) painted black; jaw/throat and underside cream. Pieces: gold faceted eye domes in the sockets, horizontal black pupils looking out-forward, 8 irregular dark back/thigh spots, 3 splayed fingers with cream pads per hand, 4 long toes with pads and a dark webbing plate per foot.
- r01 result: reads as a frog (gold domed eyes, black mouth line, spots, webbed feet); 1412 tris. FAIL slivers 2.5%. Critique: toe/finger side faces and the 3 mm webbing plate edges are long thin slivers (yellow on the feet in TECH QA); also the eye bulge's overhanging sides were caught by the belly rule (beige, az090).
- r02: Fix: thicker toes/fingers (tip half-height .005-.0055) and a 5 mm web plate; belly rule limited to z < .15 (paint bug, no geometry).
- r02 result: all gates PASS, slivers 0.8%, 1412 tris, eye bulges green again.

## Stage 4
- r01: rig from J (hips, chest, head, jaw, throat, eye.L/R, arm/forearm/hand, thigh/shin/foot/toes, roll auto). Heat weights, then the head split by hand at the mouth line (jaw below, head above), the throat patch to its own bone, each eye bulge 100% to its eye bone; all pieces bound with body= weights. Clips: idle 48 f (throat pulse x2, blink = eyes retract 12 mm like a real frog), move 24 f (crouch, hop with leg extension, land), attack 24 f (lunge, head up, jaw snaps open ~30 deg showing the black mouth, close).
- r01 result: FAIL fold-overs 1.27% of tris (0.13% of area), all 18 on the toe-fan piece; move f12 shows the foot pitched onto its edge. Attack reads well (the jaw opens on the black lip strip); legs extend back in the hop.
- r02: Fix: no foot pitch in the hop; the toe fan and the foot end under it (within 3 cm of the toes joint) are weighted 100% to the toes bone, so the fan moves rigidly.
- r02 result: all gates PASS (hit 0, float 0, z-fight 0, slivers 0.8%, fold-overs 0.00% tris / 0.00% area, drift 0, lock PASS, glbcheck OK). Review packet built.

## Triangles per stage
- s1 492 (locked, edge sha faa91e5daccc7ee0); s2 572; s3/s4 1412 total with pieces.

## Conflicts / decisions
- Brief asks for a tongue lash. A tongue piece that shoots out of the mouth would trip the drift gate (no piece may leave the body in a pose), so the attack is a lunge plus a jaw snap that opens the black lip strip. No tongue piece.
- Width with the feet is about 0.81 m (target 0.8).
