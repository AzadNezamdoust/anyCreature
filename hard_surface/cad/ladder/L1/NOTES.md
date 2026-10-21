# L1 bracket + knob - final r6 (6 rounds; r1-3 failures, 2 of them kit bugs)
- Build 8-22 s, 74 lines, 18 ops (8 fillet/chamfer, 10 booleans), 0 fuzzy, 0 manifold. 20 fillet retries; flute fillet reduced 0.5 to 0.45 mm.
- Checklist: counterbores + chamfered mouths, slot, 6 mm inner / 12 mm outer bend, 1.5 mm fillet on all body edges, revolved knob with dished top and filleted flutes. All met.
- Broke: authored in metres, fillets failed at r=0 (OCCT tolerance) -> kit `UNITS="mm"`. Filleting all edges after drilling collapsed the bisection to 0.25 mm -> fillet before holes, plus kit split-retry.
- vs real CAD: looks like a real machined part. No threads or cosmetic hole callouts.
