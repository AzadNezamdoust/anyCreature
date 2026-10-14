# Reference-image prompt pack (Nano Banana / GPT Image)

Use these in Antigravity (Nano Banana) or ChatGPT (GPT Image) to make the
reference images the 3D pipeline consumes. Quality of the 3D model is capped
by these images — every lab round showed it.

## Where to put the results

    E:\gen3d\inbox\<animal>\hero.png    3/4 view (required)
    E:\gen3d\inbox\<animal>\side.png    true side, facing left (recommended)
    E:\gen3d\inbox\<animal>\front.png   straight front (recommended)
    E:\gen3d\inbox\<animal>\back.png    straight back (optional)

Square, 1024 px or larger, PNG. Any background works if it is plain; white is best.

## Rules that matter for 3D (keep in every prompt)

- ONE animal, full body, nothing cropped, nothing overlapping it.
- Neutral standing pose (or the natural resting pose), legs apart and all visible.
- Flat, even, shadowless studio lighting; no cast shadow, no floor, no ground line.
- Plain pure-white background. No props, text, frame or vignette.
- Realistic proportions, natural colours, sharp fur/skin/feather detail.
- Orthographic-looking camera (long lens), no strong perspective.

## Step 1 — hero image (one per animal)

> A photorealistic adult {ANIMAL_DESCRIPTION}, standing in a neutral pose,
> seen from a three-quarter front view, full body visible from nose to tail
> tip, all legs separated and visible. Flat even studio lighting, no
> shadows, no floor, isolated on a pure white background. Sharp natural
> detail, realistic anatomy and proportions, long-lens camera.

## Step 2 — consistent views (Nano Banana: edit the hero image; GPT Image: attach the hero)

> Show this exact same {ANIMAL}, identical colours, markings, proportions
> and pose, from a {VIEW}. Full body, flat shadowless lighting, pure white
> background, no floor, long-lens orthographic-looking camera.

{VIEW} = "true side view, facing left" / "straight front view" / "straight back view".
Check the three views match the hero (same markings, same leg positions). Regenerate any that drift.

## Per-animal descriptions ({ANIMAL_DESCRIPTION})

| animal | description | notes for the 3D step |
|---|---|---|
| wolf | grey wolf, lean deep chest, long legs, thick neck ruff, bushy tail hanging down, erect ears | tail must hang clear of the hind legs |
| horse | bay horse standing square, no saddle or bridle, mane and tail natural | tail clear of the hocks |
| elephant | African bush elephant, trunk hanging down, tusks, ears relaxed against the body | ears slightly away from the neck |
| giraffe | reticulated giraffe, neck as long as its legs, back sloping straight from high withers, two ossicones | whole neck in frame |
| crocodile | Nile crocodile in a belly-low sprawl, legs splayed sideways, long tail straight behind, mouth closed | NOT standing upright |
| eagle | bald eagle perched upright, wings folded, talons gripping a short thin branch | branch short, nothing else |
| shark | great white shark swimming level, fins fully visible, mouth closed | side view most important |
| frog | green tree frog sitting, hind legs folded, front legs straight, toe pads visible | toes separated |
| tortoise | Galapagos giant tortoise standing, head and neck extended, legs visible below the shell | legs not hidden by shell rim |
| kangaroo | red kangaroo standing upright on its hind feet, thick tail touching the ground behind, small forearms in front | realistic, not cartoon |
