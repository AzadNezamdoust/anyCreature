> SUPERSEDED (owner 2026-10-09): written by a GPT session; its later single-image route produced models the owner rejected. Authority is WORKFLOW-V10.md + HANDOFF.md.

# LLMModeling workflow v11

Evaluated on the completed 30-model campaign with independent final appearance reviews and current helper audits. The protected v10 milestone and its pre-campaign backup remain the recovery baseline. This workflow is for stylized polygonal game props built from the supplied concept and turnaround images. It does not establish functional weapon internals, engineering certification, or measured mass.

## Evidence comes before a rating

Use four separate decisions: source agreement, mesh validity, visible motion/export validity, and owner acceptance. A model can pass a silhouette threshold and still lose a canopy facet or grip rib. A visually strong rocket launcher can fail its declared mass range. A correctly exported animation can reproduce an already-colliding lever. Keep each result and its scope visible; do not collapse them into a single green badge.

The campaign evidence lives in [the gallery](out/campaign-30/gallery.html), individual root receipts, [the final artifact matrix](out/campaign-30/artifact-matrix-final.md), and [the assessment](out/campaign-30/ASSESSMENT.md). Independent final appearance reviews cover all three sets, with a separately preserved corrected sci-fi review. Their scores are visual judgments under a shared rubric, not percent accuracy. Historical pre-polish ratings use different conditions and are unsuitable for a causal before/after claim.

## Roles, ownership and capacity

Pin builders to `gpt-6.1-sol` with high reasoning and independent reviewers to `gpt-6-astra` with high reasoning. Root owns source-priority decisions, shared helper changes, integration and final acceptance of worker evidence. A builder owns one subject's mutable build and rig folder. A reviewer receives a separate immutable appearance packet and never reads implementation, current performance metrics, author reports, or earlier reviews.

An army can work across subjects and read-only audits, but only an explicitly granted subject may render. Use a bounded heavy-job queue, at most three simultaneous Blender jobs, and a single writer per subject. Waiting for a permit is not a reason to reread the entire project or poll continuously. Workers prepare a concrete patch and commands while queued, then return a compact receipt with exact files, hashes, failed attempts, inspected views and remaining uncertainty. Preserve full evidence in files, not repeated terminal transcripts.

## 1. Protect and register

Before edits, preserve the current milestone tag and snapshot its uncommitted/generated artifacts with a hash manifest and restore instructions. A Git tag alone does not protect ignored meshes, images or local edits. Keep rollback material outside mutable model folders. Restore into a separate checkout first and refuse conflicts; never reset the user's current workspace to test recovery.

Freeze the concept, four source views, decided facts, frame, camera, style keys, triangle budget and gate thresholds. Record source contradictions before modeling: which view or explicit fact governs a conflicting feature, and which alternative is excluded. Reject a reference set that is too contradictory for the intended precision, or proceed with an explicit source-limit record. The campaign's frozen source sets already contain misses against their inherited setup targets; later mesh work cannot repair the source by quietly changing its camera or dimensions.

## 2. Build solid form, then local detail

Write a constrained part plan in metres: named parts, placement, dimensions, attachment, primitive/profile choice, materials, and which source features support it. Use polygonal shells and panels for broad bodies, glazing and covers. Real source-required rods, guards, coils and tubes remain appropriate for those parts; tubular outlines are insufficient substitutes for broad surfaces.

Start with the large envelope and supported openings. Compare all five source/current images after every substantive pass. Measure original images under the frozen registration; do not warp or globally shift the render to improve a local feature. Once the envelope is stable, spend triangles on source-visible internal contours, repeated feature counts, bevels, ribs and seating transitions. Keep hidden detail modest and record unsupported depths as assumptions.

Save every pass's build, static GLB, stats and comparison before choosing the keeper. Require at least six substantive passes overall and preserve rejected attempts. Select the current keeper explicitly: canonical build and static GLB must match its saved snapshots. Keep topology, triangle budget, look thresholds and frozen source hashes unchanged. After Boolean or material edits, inspect actual material-slot indices and refresh world matrices before judging cross-object faces.

## 3. Review the actual keeper once

Generate indexed detail crops from the selected keeper. A crop index should bind subject, keeper, build hash, static GLB hash, image hashes and view rows. Use all five overview pairs and all indexed sheets; a selected-view detail crop may contain fewer than five rows if its coverage is stated. A montage never replaces examination of the original images.

Prepare a new immutable intake containing only source/current images, decided facts, frame, view metadata, neutral source-priority notes and crops. Its overview contains labels and copied pixels without numeric score footers. Historical source-generation statistics must be removed from derived reviewer notes while preserving every source-priority decision; retain the original notes and a transformation audit outside the review packet. The campaign's existing final packets still exposed historical source-generation numbers in raw READMEs, so their results carry that limitation.

Use one rubric for final cohort comparison: shape 3, detail/count 2, location/proportions 2, flat colour 1, source-consistent multi-view coherence 2. Ask for measurements and exclusions, not a minimum defect count. A reviewer may legitimately find one remaining defect. Review completion requires explicit `ReviewStatus: COMPLETE` and actual image coverage; file presence, a provisional score, or an in-progress report does not unlock polish.

Root checks each proposed correction against the frozen images and facts. Execute one K1 response with at least two additional substantive passes. Mark every finding done, partial, rejected for a stated source conflict, or unresolved. Do not silently begin a second K1 after a final assessment. Final crop selection must follow the examined receipt whenever crops live in a snapshot folder. Ray uses `k1-pass10-crops`, Bubble `keeper11-crops`, Goo `k1-crops`, and Shrink `closeups-k1`; their older canonical crops remain preserved. The helper validates the selected index, sheets and all five primary current renders against the receipt before creating an overview or writing a packet. A sealed campaign must reject a later build until it receives a new examination; start new modeling studies in a separate campaign rather than reusing a stale seal.

## 4. Declare motion before testing it

Build the final visible geometry first. Then declare joint axes and pivots, supported moving parts, ranges, clips, sockets, local seating exceptions, collision tolerance, density assumptions and mass interval before the first S4 test. Tiny controls unsupported by the generic minimum travel remain static limitations; enlarging their travel just to pass is not evidence. Decorative sci-fi controls receive explicitly fictional previews, with no invented operational internals.

Test pivots, grouping, local clearance, the declared collider approximations and scoped simulation, and export the current rig. Freshness and success are different: an up-to-date failed rig is still valid evidence of a failure. Preserve failed clearances and mass intervals. Different joint limits must remain separately labelled in summaries; never summarize a feed-cover range with a bipod's clearance.

Decode the actual exported GLB BIN, not a duplicated author curve. Apply the complete parent hierarchy and preserved rest transforms. Check keys, interval midpoints, semantic ranges, and declared combined poses. Reconstruct relevant world vertices and compare them with the source geometry. Verify clip/channel identity, geometry, material slots, socket placements and rest pose after regrouping/export. Continuous spinning joints need phase-safe interpolation rather than a long quaternion arc or a mislabeled linear interpolation shortcut.

Render the full-object union of selected actual extrema and separately labelled limit diagnostics with at least 6% framing margin. Keep signed angle, clip time and provenance on each sheet. A declared-limit diagnostic is not an actual authored simultaneous event. Finite key/midpoint checks and triangle crossing proxies do not establish continuous, volumetric or hidden-internal clearance; full containment and tangency can be missed. A passing gate also does not establish connected support kinematics: the rocket truck's parked lower support separates visibly at its elevated launcher pose.

## 5. Prove filled surfaces and seal delivery

Open a current no-outline colour/clay preview of the exported mesh and inspect its filled faces. Bind keeper/build/static/export identities and exact PNG bytes. This distinguishes outline shading from missing broad surfaces, but merely having polygon faces does not prove every shape is source-correct or every enclosed volume is mechanically valid.

Root examines the current comparison, indexed detail representatives, actual exported motion and surface preview, then seals a subject receipt with current hashes, coverage, assumptions and retained failures. A final cohort reviewer evaluates all subjects without triggering another polish cycle. Keep all failed artifacts and historical review packets; if bytes or metadata differ, use a new intake suffix instead of rewriting evidence.

Deliver a 30-row current artifact matrix, grouped contact sheet, browsable detail pages, static and animated GLBs, individual scoped receipts, final appearance reports, recovery instructions, and an assessment separating visual quality from numerical and mechanical limits. Hash-check frozen sources, checkpoint artifacts and every selected delivery file. Verify gallery links and displayed failures in the browser. Owner acceptance remains a separate human decision; the agent can finish this modeling/evaluation campaign with honestly documented failed checks.

## Current helper commands

Run from `hard_surface`. Read the subject's declared workflow and use its existing Blender build/rig commands for geometry; these commands prepare and verify review/delivery evidence only.

```powershell
node out/campaign-30/prepare-blind-intake.mjs subject_slug final-audit-v11
# A final snapshot crop folder, when required:
node out/campaign-30/prepare-blind-intake.mjs ray_pistol final-audit-v11 k1-pass10-crops
node out/campaign-30/evidence-regression.mjs
node out/campaign-30/generate-detail-pages.mjs
node out/campaign-30/generate-gallery.mjs
```

The current dependency-bound regression result is `out/campaign-30/evidence-regression-results.json`: 59 passed, zero failed or skipped. The regression source is hashed separately; the report itself binds seven helper dependencies. [The latest independent review](out/campaign-30/workflow-primary-stats-final-review.md) passed its narrow primary-render, stats and final-navigation scope with 25 bounded probes. The wider six-finding audit and its re-review remain preserved. All 120 future packet metadata inputs are checked separately by `verify-neutral-metadata.mjs`. Existing reviewer packets are immutable. New helper revisions require their own report and independent review; an earlier approval does not cover a later crop-selection, note-redaction or primary-render change. Missing or malformed stats, selected indexes and selected sheets must produce an evidence-changed detail placeholder and allow the remaining subjects to refresh.
