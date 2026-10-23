# Night log 2026-10-23 (01:31 → 09:34)

## Morning summary
(written at end)

## Owner picks needed
- tiger attack: quick lifted step pops ~5% H in one frame (slightly abrupt) — accept or soften?

## Log
| time | creature/item | change | gates | verdict | image |
|---|---|---|---|---|---|
| 02:12 | clips round 2 (11 creatures) | toe-roll, pelvis drop, final IK solve, per-creature clips.json, crab tetrapod gait, octopus name-clash fix | clip gate 40/40 (was 29/40), mesh/skin identity PASS | ADOPT | zoo/clip_audit.md |
| 03:02 | werewolf | kit/smooth_borders after body paint (iters 8), s4 r33 | stairs 33->13, 3-to-1 22->0, 14 cuts, 87 relaxed (6 undone); kit gates PASS, junction PASS, clips PASS after --fix-clips (move pen 0.94->0.004); detail gate FAIL pre-existing (finger tips 9.6 mm < 26.6, untouched) | ADOPT (judge B/after both orders: saddle V clean) | werewolf/border_before_after.jpg |
| 03:21 | hippo | kit/smooth_borders after body paint (iters 8), s4 r08 | stairs 11->6, 3-to-1 8->0, 7 cuts, 29 relaxed (8 undone); kit gates PASS, junction PASS, eyes PASS, clips PASS (after --fix-clips); detail gate FAIL pre-existing (tier-3 count 4 < 12) | ADOPT (after wins both orders: rounded belly patch) | hippo/border_before_after.jpg |
| 03:22 | turtle | weakfix s4 r32 (stage 2 only, lock kept): 2 neck fold loops (ridges/grooves), chin step, jaw crease + dark mouth line, hooked upper beak (planar shear), dark paint upper beak only; rump shelves NOT done | kit gates PASS except drift FAIL piece_shell (new kit drift anchors 02:05, shell/legs untouched by this edit); junction PASS (upperarm knife 0/strip 0.49 r, thigh 0.35/0.88 r, eyes .26/.65/.62); clips PASS after --fix-clips (move pen 3.25->0.16); detail FAIL 5 groups (pre-existing, tier 2 wants 6); 3,760 tris | ADOPT (Opus judges: variant wins both orders) | turtle/stage4/close_0_colour.png |
