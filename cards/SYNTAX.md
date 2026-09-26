# Spec JSON — the whole language on one page

```jsonc
{
 "height": 1.85,        // real-world metres, ground to crown — the engine verifies ±15%
 "palette": { "skin_torso": {"color":"#8a8a80","rough":0.95}, ... },  // one material PER PART
 "sections": { "flute": [[1,0],[0.6,0.4],...] },   // named 2D outlines, CONCAVE allowed (bark, crescents)

 "smooth_angle": 50,    // default: faces meeting at a vertex average when their normals sit within
                        // this many degrees; the vertex splits only at a REAL crease. Override per
                        // volume and per part. "faceted":true == smooth_angle 0.
 "shading": {           // THE L1-L8 STACK. Every field below is optional and every
                        // default is the settled value — you normally write NOTHING
                        // here except `pattern.color`, which is a MID decision.
   "pattern": {"color":"#ffffff","sharpness":0.45,"amount":1.0,"scale":0.06},
                        // L2. Omit `color` and there is no pattern. Flesh only.
   "ramp":   {"bottom":"#8f8d8f","mid":"#dcdcdc","top":"#fff8ec","pm":0.30,"wm":0.30},
                        // L3. Top-to-bottom, multiplied over everything but features. A
                        // GENTLE grounding — a little darker at the feet, warmer at the
                        // crown. (1.3.2 ran from #001370: navy paws and a waterline.)
   "boost":  {"y0":0.00,"y1":0.40,"gamma":0.30,"dL":0.03,"dC":1.25},
                        // L4. Brighter AND more saturated up top, EXACTLY nothing below
                        // y0 (identity, not "almost"). Chroma walks back to the sRGB
                        // edge instead of clamping — clamping turns the hue.
   "bleed":  {"radius":0.025,"sharpness":0.35,"amount":0.45},   // L5 hardware into flesh
   "hardsh": {"amount":0.54,"gamma":0.70},                      // L6 shadow on hardware
   "bodysh": {"lights":4,"rot":4,"elev":17,"amount":0.20,"gamma":1.95},  // L7 on flesh
   "normals":{"flesh":0.30,    // L8 — the ONLY layer that leaves COLOR_0 and goes into
                        // the file's NORMAL, so the user's lighting reacts to it. 0.30:
                        // at 0.90 every flesh normal is a cylinder's and the profile
                        // (chest swell, thigh taper, the stop) stops shading at all.
              "junction":1.0, "junction_band":0.06,
              "junction_skin":1.0, "junction_skin_band":0.09},
                        // junction normals: every attached flesh piece — a limb on its
                        // `attach` host, a paw / ear / tuft on the chain it grows from —
                        // takes its HOST's normal within junction_band x model height of
                        // the host surface, so a leg shades continuously into the torso
                        // instead of showing a lit intersection edge. 0 turns it off.
                        // junction SKIN: the same pieces blend their skin WEIGHTS toward the
                        // host's own skin, linearly over junction_skin_band (wider: a bend
                        // needs room), so the root of a limb deforms with the body and the
                        // seam stays gone MID-CLIP — a normal copied in bind pose used to
                        // rotate with the limb bone and the seam came back at every step.
                        // Only the share of a vertex that follows the chain's ROOT joint
                        // moves to the host, the band is also measured along the limb
                        // (a limb lying against its host is not "at the junction" to the
                        // elbow), and a root joint that swings far in the clips gets a
                        // shallower blend (the build says how much and why) — a full
                        // blend under a 152° shoulder raise tore the rings in the band.
                        // Runs before the checks, so anim_integrity sweeps what ships.
   "stack": true },     // false = the 1.2.0 ramp-and-grain instead (gradient/noise below)
                        // legacy, only read when stack:false:
                        // "gradient":{"top":0.30,"bottom":-0.88}, "noise":{"size":0.018,"amount":0.26}
                        // noise.size = FRACTION OF THE MODEL DIAGONAL, not metres.
 "build": "rigid",      // robots/constructs/golems/vehicles ONLY — lifts the faceted_body BLOCK

 "joints": {
   "Hips": [0, 0.9, 0],                            // absolute [x,y,z], y up, z forward
   "Chest": {"from":"Hips","fwd":0.1,"up":0.5},    // relational: fwd=+z up=+y side=+x
   "TailTip": {"from":"Tail2","dir":[0,-1,-0.4],"len":0.3},
   "LToe": {"from":"LKnee","fwd":0.1,"ground":0.03}  // ground = absolute Y (feet)
 },
 "joints_R": { "RElbow": {"from":"Chest","side":-0.3,"up":0.25} },
   // optional: reposition auto-mirrored R* joints — pairs GROW symmetric but the
   // bind POSE staggers (raised right arm); the mirrored skin follows its joints.
   // A FEW CENTIMETRES ONLY. The twin's mesh is grown on the LEFT bone path and
   // then dragged onto the right joints by translation, so a large offset shears
   // the volume instead of posing it: past ~10% of the limb's length it starts
   // squashing, past ~35% the right thigh comes out 40% of the left's depth with
   // its width untouched. mirror_distortion BLOCKs that. For a genuinely
   // different pose, take the limb OUT of "mirror" and author it as its own chain.
 "chains": { "torso":["Hips","Spine","Chest"], "LArm":[...], ... },
 "attach": { "LArm":"Chest", "head":"Neck" },      // every non-root chain → its host joint
 "mirror": ["LArm","LLeg"],                        // auto right-side twins (joints, meshes, anims)
 "touch": [["torso","tail"]],                      // declared connections MUST overlap or BLOCK

 "volumes": [{
   "chain":"torso", "material":"skin_torso", "sides":14, "frame":"up",
   "profile":[[0,0.3,0.35], [0.6,0.42,0.5,{"bias":-0.1,"sharp":true}], [1,0.2,0.22]],
     // rows [t, half-width, half-height, opts]; exp 2.5-4=boxy slab; bias<0 belly-full;
     // sharp = hard SILHOUETTE break, and it only bites when the radius STEPS
     //   across it (>=15%). The flag between two rings of the same radius is a
     //   no-op. It changes nothing.
   "smooth_angle": 30,     // per-volume override of the crease angle. The wall angle
     //   is 360/sides; smooth_angle welds every edge under it. Leave the default 50
     //   on an organic mass — a body dropped under its wall angle facets into
     //   planar strips. It is NOT the soft_mass lever (that is the profile).
   "soft": true,           // OPT-OUT for soft_mass: this mass really is meant to be
     //   a smooth organic lump (a slug, a bladder, a droplet). Deliberate, not default.
     //   soft_mass measures FORM: the share of a volume's walls that lean off its
     //   bone by 8°+. A tube of one radius scores 0 and is refused; a profile that
     //   swells and narrows scores 30-60%. sides and smooth_angle do not move it.
   "shade": "flesh",                               // OPTIONAL. flesh | hard | fx — which shading
     // class this piece belongs to. The default is right almost always: volumes, hands and paws
     // are flesh; spikes, curves, membranes and fins are hard; eyes are fx (no layer, no shadow).
     // Write it when the default is wrong for THIS creature: a trunk is a `curve` that is flesh;
     // an armour plate grown as a volume is a volume that is hard. The build prints which pieces
     // landed in which class ("info: shade class ..."), so check that line rather than guessing.
     // "faceted":true on a VOLUME is a BLOCK (faceted_body) — an 800-tri torso becomes 800 shards
     // and AO bakes the mess into COLOR_0. Break a body with "sharp" rows or a lower smooth_angle.
   "caps":["dome","dome"], "ring_step":0.05,
   "cap_depth":[0.9,0.6], "cap_rings":3,   // a dome is a REAL dome (1.4): cap_rings extra
     //   shrinking rings lifted along the axis, depth = cap_depth x the end ring's smaller
     //   radius (default 0.8). 0.5 is a flattened rump, 0.9 a round muzzle tip.
     //   "none" leaves that end ring OPEN — only right when the ring is buried inside the
     //   mass the chain grows from or into (a limb root in the torso). An open ring that is
     //   not inside another body shows the background through its mouth in any renderer
     //   that culls back faces: open_end BLOCKs at a third of the ring exposed, warns at a
     //   tenth (root_containment already owns an attached chain's root ring). A chain that
     //   ENDS inside the next mass (neck into head) wants "dome" there, not "none" — a dome
     //   narrows, so it also has to reach INTO that mass, and the next mass's root ring has
     //   to sit inside this one.
   // "frame": "up" keeps every ring's 0° on top along a chain that bends (a tail that droops,
   // a neck that curves); the default frame starts 0° on top and carries it along the chain
   // without twist (parallel transport). Both hold 0° = TOP on any chain that lies down,
   // forward or backward — until the fourth pass the default frame started 0° at the
   // BELLY on a lying chain and "up" turned it to the belly on a backward one, so every
   // head and tail arc shipped inverted. A chain that STANDS (its overall direction within
   // ~25° of vertical — a leg, even with a slanted thigh) keeps the X reference: 0° = inner,
   // 90° = front, 180° = outer. 90° is +U: the +X side on a forward chain, the -X side on a
   // backward one — a mirrored part covers both, a one-sided anchor should read the build's
   // "faces ..." line. The compiler warns when a chain's 0° is not where these rules say.
   "colors": { "arcs":[                                              // 0°=spine 180°=belly
     {"from":0,"to":52,"color":"#57513f","feather":16},              // saddle, soft lower edge
     {"from":44,"to":118,"color":"#b07a44","t":[0.05,0.75],"feather":24,"feather_t":0.08},
     {"from":0,"to":180,"color":"#3f3e40","t":[0.75,1.0]} ] }        // dark tip, all round
     // arcs are applied in order, later over earlier. "t":[t0,t1] limits a band ALONG the
     // chain (default the whole of it; dome caps belong to the end row they extend).
     // "feather" (degrees) and "feather_t" (a fraction of the chain) ramp the band's weight
     // (smoothstep) from 0 at its edge to 1 that far inside — a saddle that melts into the
     // flank instead of stopping on a ring line. The ramp is RESOLVED BY THE VERTICES: a
     // feather narrower than the ring step (360/sides) lands between two vertices and does
     // nothing (the compiler warns), one just wider puts a single kink on the ramp. A
     // gradient needs 2-3 vertices inside it: write feathers at 2-3x the step (16 sides
     // → 45-70°), feather_t at 2-3x the ring spacing in t (~ring_step / chain length).
     // arcs ONLY — colors.gradient / colors.noise are ignored (info: line); see "shading" above
 }],

 "parts": [
  { "type":"curve", "host":"Head", "material":"tusk", "mirrored":true,   // CURVED horn/tusk/trunk
    "join":"insert",                 // how it meets the body: insert (base buried, verified) /
                                     // extrude (grows out of the skin) / snap (rides an anchor) /
                                     // place (deliberately free) — undeclared floating roots warn
    "offset":[0.06,0,0.1], "dir":[0.3,-0.6,0.7], "sides":8,
    "segments":[ {"len":0.1,"r":0.035,"ahead":20}, {"len":0.1,"r":0.028,"rise":35},
                 {"len":0.08,"r":0.015,"rise":30,"taper":true} ],
    "roll":0, "cap":"dome" },        // 1.4: "r":[rw,rh] makes an ELLIPTICAL section (an
    // ear, a paddle tusk, a flattened tail); "roll" turns it in its plane (degrees);
    // "cap":"dome" rounds the far end (a tongue, an ear) — default is the flat fan.
    // steering is per-segment and ADDS UP down the chain. rise/fall/ahead/behind
    // pull the heading that many degrees toward that world axis; coil swings it in
    // the carried plane (rings, spirals); taper pinches the far end.
    // Four mild segments can finish somewhere you did not predict — the compiler
    // reports the accumulated total (info: ... accumulated to 123°). Read that line.
    // "colors": { "arcs": [ {"from":95,"to":180,"color":"#cdb9a2","feather":60} ] }
    // a curve takes colors.arcs like a volume (the pale INSIDE of an ear, the dark upper
    // edge of a horn): t runs 0 at the root to 1 at the far end, and the angle is read in
    // the curve's OWN frame, not the body's, so the compiler prints where 0°/90°/180° face
    // ("info: curve 'ear': colours — 0° faces down-back-side ..."). Read that line too.

  { "type":"curve", "name":"claw_mid", "host_part":"toe_mid", "at":0.88,   // A PART ON A PART
    "material":"claw", "join":"insert", "mirrored":true, "offset":[0,0.003,0],
    "segments":[ {"len":0.03,"r":0.0085}, {"len":0.03,"r":0.006,"fall":55,"taper":true} ] },
    // "host_part" seats a part on an EARLIER part instead of on a joint: a claw on a curve
    // toe, a barb on a spine, a bell on a tentacle. "at" is 0..1 along the host's centreline
    // (a curve or a spike; default 1 = the far end); the origin lands there plus "offset",
    // "dir" defaults to the centreline's tangent, and the skin weights are INHERITED from the
    // host, so it moves with whatever the host moves with. part_attachment / part_seat /
    // contrast_adjacent measure it against the host PART's own surface and material. A host
    // with no centreline (a fin, a paw, a hand) seats it at the host's joint + offset and needs
    // a "dir". The host must be listed BEFORE the part it carries. Not for eye / membrane /
    // tufts, which place themselves. The build prints where the part landed ("info: part
    // 'claw_mid': seated on part \"toe_mid\" at 0.88 of its length [...]").

  { "type":"membrane", "name":"wing", "material":"wing_skin", "mirrored":true,  // skin between rib chains
    "cusp":0.25, "along":8, "across":3,
    "ribs":[ {"chain":"LArm"}, {"chain":"LFing2"}, {"chain":"LFing3"}, {"chain":"LTrail"} ],
    "colors": { "arcs":[ {"u":[0,0.22],"color":"#3a2f52","feather_u":0.22},     // darker leading edge
                         {"t":[0.55,1],"color":"#8a74b4","feather_t":0.45} ],   // paler toward the tip
                "veins": {"color":"#4a3b6a","width":0.4} } },                    // ribs show through
    // along = samples down each rib · across = columns between neighbouring ribs
    // cusp = how deeply the trailing edge scoops · per-rib "shorten":0.2 pulls one rib in
    // Ribs run leading→trailing and the LAST one has to come back to the body.
    // Leave it out at the far end and the silhouette never encloses — it reads as
    // spread fingers, not one sheet. The compiler measures the root gap and warns.
    // colors: a sheet has no rings, so its bands are written in the sheet's OWN frame —
    // "u" ACROSS (0 = the leading rib, 1 = the trailing rib) and "t" ALONG (0 root, 1 tip),
    // later arcs over earlier, feather_u / feather_t as fractions of the sheet. "veins"
    // darkens a band centred on each rib column, `width` as a fraction of the rib spacing.
    // Resolved by the vertices like every arc: a feather under 1/((ribs-1) x across) or a
    // vein under 1/across lands between two vertices and ships a hard edge (the compiler
    // warns with the numbers). The build prints which rib is u 0 and which is u 1.
    // COLOUR BUDGET: a spread wing is ~30% of the hero view by itself, and the saturated-
    // area ruler reads the SHIPPED colour, which the shading stack pushes ~0.1 above the
    // palette's HSV S on mid-saturation surfaces (a #6e5a98 wing, S 0.41, ships 64% of its
    // vertices at S >= 0.50). Keep a supporting membrane's palette under ~S 0.35, and spend
    // the loud colour on a smaller signature; a leading edge or veins can be darker without
    // being louder.

  { "type":"fin", "host":"Skull", "material":"plate", "thickness":0.02, "mirrored":true,
    "anchor":{"chain":"head","t":0.4,"around":60},   // around: 0=spine 90=side 180=belly
    // ⚠ that mapping is the BODY chain's frame. `around` is read in the host
    // SECTION's frame, so on a chain running vertically (a leg) the same numbers
    // point elsewhere: 0=inner, 90=FRONT, 180=OUTER, 270=back. Aiming a plate at
    // the outside of a thigh with 90 lands it on the front. The compiler prints
    // the world direction each anchored part actually faces — read that line,
    // do not reason from this comment.
    "udir":[0,0,1], "vdir":[0,1,0], "points":[[0,0],[0.1,0.02],[0.05,0.15]],
    "bevel":0.3,        // 1.4: the two faces shrink toward the centroid by this fraction and
                        // the full outline becomes a mid rim — a lens with a chamfered edge
                        // instead of a slab of card. Scales, leaves, shields, ears.
    "faceted":true },   // PARTS may face freely (or set "smooth_angle") — only VOLUMES are blocked
    // by default the host surface wins: an anchored part is snapped flat onto the
    // surface normal, and the direction you wrote survives only as a reported
    // difference. Set "conform":false when that written direction was the point.

  { "type":"eye", "host":"Brow", "material":"eye", "size":0.028,
    "anchor":{"chain":"head","t":0.4,"around":62},    // both eyes from one entry; side of head ≈55-70
    "sink":0.5,                                       // fraction of the radius buried (default 0.35)
    "pupil":{"material":"pupil","size":0.55} },       // 1.4: the engine seats a darker sphere on the
    // FRONT of the iris where it actually landed. An eye is a VALUE STEP, not a coloured dot —
    // without a pupil the eye_pupil measure warns. "look":[x,y,z] aims it; default is ahead.

  { "type":"hand", "host":"LWrist", "material":"skin_hand", "mirrored":true,  // palm + 4 fingers + OPPOSABLE thumb
    "size":0.17,                          // palm length — the whole hand scales from it
    "dir":[0.1,-0.9,0.35], "up":[0,0,1],  // dir = where the knuckles point; up = back of the hand
    "curl":0.35, "spread":0.5,            // relaxed curl / finger fan; "fist":true = folded, thumb wrapped
    "join":"extrude" },

  { "type":"paw", "toes":4, "host":"LToe", "material":"skin_fist", "size":[0.3,0.25,0.2], "mirrored":true,
    "claws":true, "claw_material":"claw" }   // 1.4: a rounded-box pad whose FRONT is the toes
    // (default 4; "toes":0 for a plain pad), each half-buried so AO hides the join. Claws are a
    // second mesh (`<name>.claws`, hard-shaded, join "place") in claw_material — dark claws on a
    // light foot are what make a foot read at thumbnail size. "dir" turns it in the ground plane.

  { "type":"tufts", "name":"ruff", "material":"fur_ruff", "mirrored":true,   // FUR that leaves the
    "anchor":{"chain":"body","t":0.9,"around":[45,180]},                     // silhouette: a ruff,
    "rows":2, "span":0.12, "count":7,                                         // a mane, a bushy
    "length":0.17, "width":0.10, "thick":0.05,                                // tail, cheek beards
    "sweep":-1.2, "droop":0.55, "flare":0.9, "jitter":0.3, "sides":6,
    "bulge":0.95, "tip_color":"#e2d7bd" }              // root_color overrides the root end
    // A crown of short fur CLUMPS seated on a volume's surface, each rooted under the skin:
    // a root ring, a full ring a third of the way out (`bulge` x width — 0.6 a blade, 1.3 a
    // pom), a shoulder ring and a tip, so the outline is a lobe that pinches to a point, not
    // a paper spike. Each clump carries a colour ramp: the ROOT takes the colour of the skin
    // it grows from (it never stands off the body) and the TIP takes the material (or
    // tip_color) — cream tips over a grey neck is what a ruff looks like. Fewer, larger
    // clumps at 5-6 sides read as fur; many narrow 4-sided ones read as a gear.
    // `around` is [from,to] in the section's frame (0 spine, 90 side, 180 belly), or one
    // angle for a single column; `rows` rings of tufts spread over `span` along t; `count` per
    // row. Direction = surface normal x flare + chain tangent x sweep (+1 toward the chain's
    // end, -1 back toward its start) + world down x droop. `jitter` alternates lengths so the
    // edge reads as fur, not a gear. Tufts are FLESH: they take the seam blend, the body light
    // and the junction normals, so they belong to the mass they grow from. They also ride
    // the skin of the ring they sit on (a ruff across two neck joints bends with the neck),
    // so "host" may be left out. A lofted tube cannot make a ruff — a fatter ring is a ring.
    // A tuft in its host's own material is fur, not a part: contrast_adjacent leaves it alone.
 ],

 "animations": {
   "move":   { "duration":0.95, "loop":true, "mirror_phase":0.5,
     "tracks": { "LFrontRoot": {"rx":[[0,-26],[0.5,28],[1,-26]]} } },   // rx..tz keys [fraction,deg|m]
   "attack": { "duration":0.7, "loop":false, "tracks": { ... } }
     // attack must COMMIT FORWARD — either route passes (attack_reach):
     //   REACH: something ends ≥15% of the body span past the bind front, or
     //   SWING: some part travels forward ≥45% of ITS OWN length.
     // You do NOT have to lunge. Planted on the spot, winding a limb, tail or
     // weapon BACK and sweeping it FORWARD counts. A sideways sweep does not —
     // the strike has to commit at the space in front of the body.
 },
 "style": "heavy",     // ONLY if 1:1 segment rhythm is the design (relaxes the 50:50 gate)
 "ao": false,          // debug only — vertex AO bakes automatically otherwise
 "embed_spec": false,  // opt OUT of the embedded birth certificate (default: the GLB carries its own spec)
 "keep_uv": true,      // opt-in UV atlas (TEXCOORD_0) for downstream texture bakes
 "qa_isolate": true    // MID part-isolation builds only: skips whole-body checks
}
```
`BLOCK:` = build refused (fix, costs no round) · `warn:` = a measure, you judge ·
`info:` = the compiler telling you what actually happened — always read them.
Shipped GLBs auto-merge primitives per material and export public bone names
(`LArm1Sh` convention) — internal spec names never leak.

---

## `function` — what each chain is FOR  (1.3.2)

```jsonc
"function": {
  "body":   "axis",         // the load-bearing spine of the creature
  "LArm":   "locomotion",   // what moves it: legs, wings, fins, wheels
  "RArm":   "locomotion",
  "LLeg":   "effector",     // the end that reaches out and contacts the world
  "case":   "ornament"      // carried, not load-bearing, does no work
}
```

Keys are chain names. A chain listed in `mirror` covers its twin automatically.
A part bolted onto a chain inherits that chain's function, so `"neck": "effector"`
covers the blade mounted on the neck; naming the part directly also works.

Four words, all manufacturing vocabulary. Nothing here says how hard a thing hits or
what it is worth in a fight — that is the receiving system's business. Today only
`effector` changes what a check does (`effector_leads`, `attack_windup`); the other
three are recorded for the receiving system and not yet read by any check.

**A declaration is not a label; it is a claim the engine checks:**

| check | what the declaration has to pay for |
|---|---|
| `effector_leads` | at the frame the attack reaches furthest, the effector is the frontmost mesh |
| `attack_windup` | the effector winds back 5% of its travel, or swings 15% out to the side |
| `gait_footfall` | a locomotion chain that touches ground lands in FRONT of where it lifts |
| `self_clip` | nothing that starts far apart ends up inside something else |
| `clip_closes` | a non-looping clip returns to its first frame |
| `ground_clip` | nothing goes below the plane the creature stands on |

`harness/autofix.mjs` fixes the arithmetic ones before a round is spent — the ground
offset, the loop closure, and the compensation of joints that must hold their own aim
while the body turns for some other purpose. It never touches the decisions: which way
a leg swings, what the creature attacks with, how far it lunges.

## `joint_range` — how far each joint turns  (1.3.2)

```jsonc
"joint_range": {
  "LKnee":  { "rx": [-130, 10] },              // a knee is a hinge, one way
  "LSh":    { "rx": [-50, 90], "ry": [-60, 60], "rz": [-70, 70] },
  "Beak":   { "rx": [-10, 40] },               // opens, does not close past shut
  "BallTop":{ "rx": [-35, 35], "ry": "free" }  // hangs on a chain, spins freely
}
```

Degrees, per axis, in the joint's **own frame** — the same frame and the same axis
names (`rx`/`ry`/`rz`) the animation tracks use, so a limit and a track compare
directly.

- **An axis you leave out is LOCKED at 0**, not free. A table with holes in it is a
  table that checks nothing, and one axis per joint is the common case anyway.
  `"free"` opts an axis out on purpose — a rotor, a wheel, a weight on a chain.
- **Declare the L side only.** The R twin is generated: `ry` and `rz` negate, which
  swaps the ends of the interval, so `[-10, 90]` becomes `[-90, 10]`. Writing both
  sides by hand is how mirrored limbs get broken. Writing `R…` explicitly overrides,
  for a body that really is asymmetric.
- **Write what the ANIMAL can do**, not what your clip happens to use. A limit is a
  fact about the body; a track is one use of it. If they are the same numbers, the
  declaration is not saying anything.

**What the declaration has to pay for:**

| failure | what it means | the fix |
|---|---|---|
| undeclared | a clip turns a joint with no entry | write the entry |
| overrun | a track leaves its own declared interval | fix the track, or the number — one of them, not both |
| unreachable | the body collides before the declared limit | tighten the number to the angle the engine reports |

`unreachable` is the one worth understanding. You know a gorilla's shoulder swings 60°
back; you do not know that THIS gorilla has a wrecking ball hanging off a crane on its
back, so its arm stops at 53°. The engine sweeps every declared bound against the actual
geometry and reports the last angle that clears. Authored knowledge, checked arithmetic —
neither one alone is enough.

## `name` on every part — the identity channel  (1.3.2)

```jsonc
"parts": [
  { "name": "nose_leaf",  "type": "fin",   "host": "Muzzle", "material": "paw" },
  { "name": "foot_claws", "type": "paw",   "host": "LToe",   "material": "paw", "mirrored": true },
  { "name": "left_tusk",  "type": "curve", "host": "Muzzle", "material": "tusk" }
]
```

Required, and unique within the creature. It may not reuse a chain name, because
volumes are identified by their chain.

**Why it is not optional, and why the material cannot do the job.** A material is a
CLASS — "this is horn", "this is brass pipe". Many parts share one on purpose, and the
GLB merges primitives one per material so a body with forty plates does not ship forty
draw calls. That makes a material name structurally unable to answer *which part is
this*: above, `paw` names both a foot pad and a nose-leaf, and anything that groups by
material adds the two together. Naming is the fix, and it costs nothing — you already
know what you are building at the moment you write the part.

Name the THING, not its type and host. `spike@Skull` is a description of where you put
something, and two spikes on one skull share it; `left_horn` and `right_horn` are names.

The engine writes each name into the file as `asset.extras.part_spans`, with the exact
vertex range that part owns — so a checker, the Arena importer or `graft.py` can point
at one piece of geometry without a single extra material.
