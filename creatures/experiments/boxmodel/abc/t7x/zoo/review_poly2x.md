# Poly 2x pass review (before3 vs stage4)

Evidence: each creature's before_after3.jpg (hero view) and zoo20_poly2x.jpg. The orbit18 sheets were NOT opened in this pass, so the "reads from every angle" rule was not checked. Run an orbit check on every MIX or REVERT before acting on it.

| creature | BETTER | WORSE | verdict | instruction |
|---|---|---|---|---|
| fox | torso loft rounder; ruff tidier | back is now faceted with lumpy banding; lost the crisp shoulder and hip planes | MIX | Keep the head, ruff and tail; restore the before3 torso loft (fewer rings, one clean shoulder/hip break). |
| bear | ears; snout taper slightly cleaner | body is now a stack of vertical rib-bands; lost the strong hump and shoulder planes; reads as a barrel | MIX | Restore the before3 torso and hump (big flat planes, a clear shoulder hump); keep the new head and legs. |
| boar | eye now visible; cheek panel cleaner | torso rib-banding; back crest flatter; mane plane lost | MIX | Restore the before3 torso/back loft with its hard dorsal ridge; keep the new head and eye. |
| tiger | face and cheek ruff a little crisper | chest/ruff is now lumpy; leg banding is noisy; torso less boxy | MIX | Restore the before3 chest/ruff and legs; keep the new head and torso stripes. |
| stag | body silhouette slightly smoother | lost faceted muscle planes on the torso; a more generic tube | REVERT (mild) | Use before3; the 2x pass adds nothing that reads. |
| snake | smoother curve along the body | neck pinches and wobbles behind the head; pattern blocks break up | MIX | Restore the before3 neck/head junction (no pinch); keep the denser body curve. |
| crocodile | smoother body side | scutes smaller and flatter; snout plane softer; side pattern noise | REVERT | Use before3; it has bolder scutes and a crisper snout. |
| shark | cleaner body taper toward the tail | none significant | KEEP | n/a |
| koi | tail peduncle and body taper read as a fish better | the peduncle is a ribbed tube; the head lost its bold flat planes | MIX | Keep the new body/tail; restore the before3 head planes and cut the peduncle to fewer rings. |
| chameleon | casque and body rounder; colour bands clearer | knee "fins" now look like stray spikes; leg planes noisier | MIX | Keep the new body and casque; restore the before3 legs (no flared knee spikes). |
| dragon | neck and belly plate smoother | torso slightly softer; otherwise near-identical | KEEP | n/a |
| goblin | head shape fine | eye is now tiny and half-hidden under the brow (breaks the small-round-lens-eye rule); brow overhang is wrong | MIX | Keep the new body; restore the before3 head/brow and eye size and position. |
| golem | none clear | the planes are rounded off and the rock blocks turn into blobby rings; the head pokes out like a bulb; the shoulder moss is lumpy | REVERT | Use before3; a golem needs hard rock planes. |
| ogre | arms rounder | the eyes are lost into a visor-like brow slit; belly and arms are ring-banded; the head is helmet-like | REVERT | Use before3; it has a readable face and crisper belly planes. |
| knight | helm curvature and pauldron a little nicer | limbs are ringed and wobbly; armour should be crisp | MIX | Keep the new helm; restore the before3 arms, legs and torso plates. |
| octopus | mantle and arm taper smoother and more organic | the eye is now hidden or nearly invisible | MIX | Keep the new mantle and arms; restore the before3 eye size and placement (visible yellow lens). |
| spider | legs are thinner, longer and closer to the reference; abdomen rounder | cephalothorax facets slightly soft | KEEP | n/a |
| crab | carapace and claw slightly fuller | legs are more ringed; little visible gain | KEEP (marginal) | n/a, or restore the before3 walking legs if the rings show in motion. |
| owl | face disc and brow better; eyes still read | the breast is now a soft wobbly bib; lost the crisp chest facets | MIX | Keep the new head; restore the before3 chest/breast planes. |
| raven_wyvern | near-identical; the beak is a touch cleaner | a dark band appears on the beak base | KEEP | n/a |

## Lessons
1. Extra polygons help on long tapering organic forms (shark, koi, spider and octopus legs, snake body curves, dragon neck), where the silhouette gets smoother without needing hard planes.
2. Extra rings hurt on big masses that should be blocky (bear, boar, golem, ogre, knight, croc). Uniform loft rings make vertical rib-banding and lumps, and kill the t7 flat planes. Add density only where the silhouette bends, never evenly.
3. Re-lofting the head moved or shrank the eyes and changed the brows (goblin, ogre, octopus). Lock the head, eye and brow geometry from before3 during any density pass, and re-check eye visibility in every view.
