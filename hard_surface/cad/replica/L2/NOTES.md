# Replica L2: Logitech G502 HERO (final = r4)

Refs: REFS.md (official logitechg.com gallery shots and the Logitech spec sheet: 132 x 75 x 40 mm). No true dimension drawing exists publicly.
Method: `ref_extract.py` registers the top and right-profile shots to the spec length and height. It extracts a 33-station table (left/right width, crest, underside lift). `model.py` lofts superellipse sections through the smoothed table, so there are no hand-styled curves. The thumb rest is a separate lofted part. Shut lines are surface-following grooves. Wheel slot + 18-notch wheel, G9 and mode button caps, G4/G5/G6 thumb buttons and the DPI LED bar are caps that follow the skin.
Run: `venv_cad python replica/L2/round.py <N>` -> out/replica/L2/rN (IoU, overlays, hq render).

## Rounds
| r | IoU top | IoU side | change / failure |
|---|---|---|---|
| 1 | 0.947 | 0.941 | body + thumb rest. A half-space `cut` of the loft failed all 3 paths, so I used `split` instead. The IoU script only read part 0 |
| 2 | 0.973 | 0.941 | fixed the IoU loader (body only, no features yet) |
| 3 | 0.965 | 0.965 | features added. Hangs: body - inner loft >500 s; full-body groove cut failed (coincident faces); 0.5 mm fillet on thumb caps >10 min. Fixes: per-fence small booleans with tool poking 1.6 mm out, 19 stations instead of 33, cap fillets dropped |
| 4 | 0.965 | 0.966 | table smoothed ([1,2,1] x2) because the r3 zebra was lumpy. Blunt nose and tail end stations replaced the r3 "beak" |

## Dimension errors (r4)
| dim | spec | model | err |
|---|---|---|---|
| length | 132 | 132.0 | 0 |
| width | 75 | 76.2 | +1.2 (+1.6 %): the top photo has perspective and reads 76.5 |
| height | 40 | 41.0 | +1.0: the wheel crown sits proud of the crest |
| plan outline, per 10 mm station | | | <=1.2 mm, except nose -2.2 and tail +1.8 |
| side crest | | | <=1.0 mm |
| side underside | | | up to 2 mm at X=-40 |

## Kit gaps (implemented locally, cadkit/ not edited)
- `cut(loft, half-space box)` fails on a 33-section loft (plain, fuzzy and manifold all fail). Workaround: `split(Plane.XY).fix()`; the split result was invalid until fix().
- `offset()` (OCCT offset_3d) fails on this loft. Workaround: analytic offset by re-lofting the inflated stations (`main_loft(d)`).
- Booleans between two near-parallel lofts (skin layer) hang for more than 500 s. Workaround: per-fence (fence&outer) - (fence&inner).
- An empty `common` raises CadOpError. It is caught; 2 events are logged per build, and this is expected.
- `safe_fillet` on thin curved caps hung for more than 10 min. It needs a timeout in the kit.

## Remaining defects
- Side refs are elevated product shots, not orthographic. The Z of the side shut lines, the thumb button X positions and the thumb rest height are estimates: the top and left views disagree by about 8 mm on button X.
- The thumb rest is a rounded pod. On the real mouse it is a flared shelf with a sharp moulded edge and triangle texture.
- Nose: the two primary-button tips and the cable notch between them are not split. There is no cable or strain relief.
- The DPI buttons G7/G8 are outlined only; the real ones are raised, angled keys.
- No G logo, no grip texture, no underside (feet, weight door, sensor window).
- Cap edges are sharp (fillet hung). The zebra still shows mild waviness at the X=-16 / +32 stations and a crease where the thumb rest meets the body (G0, separate part).
- The pad underside is near-flat, so the loft's lifted ends dip slightly.
