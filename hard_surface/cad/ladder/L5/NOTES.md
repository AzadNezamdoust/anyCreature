# L5 coupe - final r8 (8 rounds); NOT clean
- Build 72 s, ~150 lines. Flare blends and arch rim fillets FAILED/skipped. Light pockets needed fuzzy (0.5 mm), leaving jagged nose geometry. Glass, shut lines and wheels OK.
- One loft through 13 full-car sections (rocker, shoulder, belt, tumblehome, roof), recessed glass + glass bodies, door/hood/decklid shut lines, flared arches, recessed head/tail lights + lenses, front intake, revolved tyres + 5-spoke rims.
- Broke: OCCT offset_3d returned an INVALID solid (vol 1e-4 of the body) -> "parametric offset" by re-lofting shrunk sections. A narrow tail station broke the offset (weights). Body minus inner skin failed everywhere -> cut tools with the inner loft instead. The mm->m B-rep scale broke located parts in glTF -> export with unit=MM.
- r8 renders show faceted dents on the big trimmed loft face plus the jagged intake/light area. r3 (old taller body) rendered smoother.
- vs real CAD: recognisable coupe silhouette. Far from class-A: one loft gives no feature-line control, zebra is wavy, nose and tail are blunt caps, no real fillets on flares or shut lines.
