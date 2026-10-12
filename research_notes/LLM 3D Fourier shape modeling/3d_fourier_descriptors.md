# 3D generalizations of 2D Fourier outline descriptors for creature bodies

Note: web search returned abstracts/summaries, not full paper texts. Quantitative claims (coefficient counts, animal-shape results) were largely NOT found and are listed under Gaps. Uncited reasoning is in Inferences only.

## 1. SPHARM (Brechbuhler, Styner): mechanism, star-shape limit, area-preserving mapping, coefficient counts

### Takeaway
SPHARM is the direct 3D analogue of elliptic Fourier descriptors: map a genus-0 surface to the sphere, expand x,y,z as spherical harmonics. Because the map is a parametrization (not a radial function), it is not limited to star-shaped objects, but it is hard to compute, global, and suffers Gibbs ringing.

### Cited Findings
- Brechbuhler, Gerig, Kubler (1995, CVIU 61(2):154-170) map a simply connected 3D object surface onto the unit sphere and expand its coordinates in spherical harmonics, extending elliptic Fourier descriptors of 2D closed curves to 3D. The mapping is a constrained optimization with a heat-conduction initial guess; rotating the parameter net and object to standard positions gives pose/size-invariant descriptors. — [Search summary of CVIU paper](https://www.datalearner.com/academic/journal-papers/1077-3142/volumes-and-issues/2/paper-detail/70695)
- Thesis summary: the parametrization preserves true area ratios in parameter space (area-preserving, which is what lets non-star-shaped genus-0 shapes be handled). — [Brechbuhler ETH thesis](https://www.research-collection.ethz.ch/server/api/core/bitstreams/3a81391a-f193-472f-aa8f-173593d8ba2c/content) (as relayed by search summary; not read in full)
- SPHARM is a hierarchical, global, multi-scale boundary description for objects of spherical topology; truncating degree gives different levels of detail. The original parametrization only worked on voxel surfaces; later work extended to general triangle meshes. — [PMC3062073](https://pmc.ncbi.nlm.nih.gov/articles/PMC3062073), [Springer chapter](https://rd.springer.com/content/pdf/10.1007/11566465_9.pdf) (search summaries)
- SPHARM-PDM (Styner et al. 2006) converts segmentations to SPHARM then to a sampled triangulated surface; its main limitation is requirement of spherical topology. — [Insight Journal](https://insight-journal.org/browse/publication/101)
- Classic SPHARM shows Gibbs ringing on discontinuous/rapidly changing data; a weighted (smoothed) variant reduces it. One hippocampus study chose truncation degree L=20 as acceptable smoothing. — [Chung poster](https://pages.stat.wisc.edu/~mchung/papers/SSP/SSP2007.asymmetry.poster.pdf), [arXiv 1707.05961](https://arxiv.org/pdf/1707.05961)

### Inferences
- A degree-L expansion has 3(L+1)^2 real coefficients (standard SH counting): L=4 -> 75, L=10 -> 363, L=20 -> 1323. L=20 is blob+bumps, not thin legs/ears.
- Thin appendages (legs, tails, ears) force the spherical map to devote huge sphere area to tiny surface regions or the reverse; low-degree truncation will blunt/round them and ring around them.
- Authoring SPHARM by hand is very hard: coefficients mix position and parametrization; low degrees (1-3) are human-interpretable (ellipsoid, bends), higher ones are not.

### Gaps
- Exact detail on how non-star-shaped objects are handled and the exact area-preserving optimization: not found beyond abstracts.
- No source found giving coefficient counts needed for recognizable animals.

## 2. Other bases: closed space curves, radial/star-shaped SH, Laplace-Beltrami (manifold harmonics), spherical wavelets, Shape-DNA, Kazhdan descriptors

### Takeaway
Manifold harmonics and spherical wavelets are mesh-dependent analysis tools (need an existing shape); Kazhdan's SH descriptors and Shape-DNA are for retrieval, not reconstruction/authoring. Radial SH (r(theta,phi)) is the simplest authorable one but star-shaped only.

### Cited Findings
- Manifold harmonics (Vallet & Levy 2008, CGF 27(2):251-260): eigenfunctions of the Laplace-Beltrami operator give a Fourier-like transform on a triangle mesh; computing eigenvectors is expensive; eigenfunctions are global; the approach cannot preserve creases and the Laplacian is geometry-dependent. — [Search summary of Vallet-Levy](https://diglib.eg.org/handle/10.2312/CGF.v27i2pp251-260), [Vallet08 PDF](https://www.cs.jhu.edu/~misha/ReadingSeminar/Papers/Vallet08.pdf), [arXiv 2107.07379](https://arxiv.org/pdf/2107.07379)
- Localized manifold harmonics (Melzi 2017) and compressed manifold modes (Neumann 2014) address global support. — same arXiv survey above
- Kazhdan, Funkhouser, Rusinkiewicz (SGP 2003): decompose spherical functions on concentric spheres into SH; per-band norms are rotation invariant; yields compact descriptors for retrieval (information loss: not invertible to shape). — [Kazhdan 2003](https://www.cs.princeton.edu/~funk/sgp03.pdf)
- Spherical wavelets (Schroder & Sweldens 1995; applied to 3D shapes by Nain/Tannenbaum): local multiscale basis on spherical-topology meshes; outperforms PCA for small training sets; biorthogonal version has aliasing. — [Georgia Tech](https://repository.gatech.edu/entities/publication/31daaa57-3cdc-447a-aeee-79d355d0d57c), [NA-MIC](https://www.na-mic.org/wiki/NA-MIC/Projects/Structural/Shape_Analysis/3D_Shape_Analysis_Using_Spherical_Wavelets)
- Shape-DNA (Reuter, Wolter, Peinecke 2006): Laplace-Beltrami eigenvalue fingerprint; isometry invariant, no registration needed. Spectrum alone is not a reconstruction. — [arXiv 1110.5015](https://arxiv.org/pdf/1110.5015), [Reuter slides](https://www.math.ucdavis.edu/~saito/confs/ICIAM07/reuter.pdf)

### Inferences
- 3D elliptic Fourier of closed space curves (x(t),y(t),z(t) each a Fourier series) is trivially authorable but describes a 1D curve (spine, leg centerline, outline contour), not a surface -- useful as a component, not as a body model. (No source found; standard math.)
- Radial SH (r = sum a_lm Y_lm) needs star-shapedness; a quadruped with splayed legs/long tail is not star-shaped about any point in general (legs fine from the torso center, but ears/tail curling back and legs adjacent to body can occlude). Mild star-shaped violations produce multi-valued rays.
- Toroidal/cylindrical harmonics: no creature-specific source found; cylindrical (z, phi) series suit tube-like limbs/torsos but not branching.

### Gaps
- No sources found on toroidal harmonics for creatures or on 3D Fourier descriptors of space curves specifically.

## 3. Generalized cylinders, Fourier cross-sections, skeletal models (m-reps / s-reps)

### Takeaway
Branching skeleton + per-segment swept Fourier cross-sections is the best-fitting structure for creatures (legs, tail, ears each a tube); m-reps/s-reps formalize the skeleton+radius idea but are fit-to-data tools for single-sheet organs.

### Cited Findings
- A generalized cylinder is a cross-section swept along an axis, with the section in a Frenet-Serret frame; very flexible and capable of modeling many real-world objects. — [arXiv 1911.00571](https://arxiv.org/pdf/1911.00571), [UIUC potential-based GC](https://experts.illinois.edu/en/publications/a-potential-based-generalized-cylinder-representation/)
- Aguado, Montiel, Zaluska (1999, ACM TOG) "Modeling Generalized Cylinders via Fourier Morphing" exists (Fourier-descriptor cross-sections morphed along axis); only the title found, mechanism not verified. — [Southampton eprints](https://eprints.soton.ac.uk/253717)
- Cochlea model: centerline in cylindrical coordinates with a closed planar cross-section under varying affine transform. — [arXiv 2105.02045](https://arxiv.org/pdf/2105.02045)
- M-reps (Pizer et al.): sampled medial atoms (position, width, local frame) from which the boundary is derived; capture bending/twisting. Continuous m-reps use cubic B-splines for medial locus + thickness. S-reps: smooth skeletal sheet with spokes whose envelope is the implied boundary. — [Pizer m-rep PDF](https://midag.cs.unc.edu/pubs/papers/mreps-2000/mrep-pizer.PDF), [Yushkevich cm-reps](https://www.sci.utah.edu/~gerig/CS7960-S2010/handouts/yushkevich02continuous.pdf), [arXiv 2409.04079](https://arxiv.org/html/2409.04079v1)

### Inferences
- Skeleton-with-radius models are very LLM-authorable: a tree of 3D polylines/splines, each with radius(t) and optional Fourier ellipse/lobed cross-section; coefficient counts are tiny (e.g., ~6-12 numbers per cross-section harmonic set).
- Junction blending (where leg meets torso) needs smooth union (e.g., SDF smooth-min); not covered by the sources.
- M-reps/s-reps target organs of topologically simple (slab/tube) shape; no evidence found of use for whole animals.

### Gaps
- Content of Aguado et al. unverified. No animal-specific generalized-cylinder source found.

## 4. Coefficient counts for recognizable animals; Gibbs/ringing; what can be AUTHORED by a human/LLM

### Takeaway
No published figure found for coefficients needed for recognizable animals. Ringing at sharp features is documented for SPHARM. Authorability ranking (inference): skeleton+tube/cross-section Fourier > radial SH (star-shaped, low degree) > SPHARM > manifold harmonics/wavelets (need existing mesh).

### Cited Findings
- Gibbs ringing in SPHARM and its mitigation by weighting: [Chung poster](https://pages.stat.wisc.edu/~mchung/papers/SSP/SSP2007.asymmetry.poster.pdf). Vallet-Levy cannot preserve creases: [arXiv 2107.07379](https://arxiv.org/pdf/2107.07379).
- Hippocampus SPHARM at L=20 gave "acceptable smoothing" (organ, not animal): [arXiv 1707.05961](https://arxiv.org/pdf/1707.05961).

### Inferences
- Ringing mitigations: Hanning/Lanczos-style per-degree weighting (Fourier sigma factors), or sum smooth components (blobs) with SDF-union rather than one global series.
- Practical recipe for a creature: global low-order SH/Fourier for the torso+head envelope, plus separate tube limbs (axis spline + Fourier cross-section) smoothly unioned; add detail via displacement series. Hand/LLM-authored high-degree SH is infeasible because coefficients lack intuitive meaning.
- Per-leg-per-ear coefficient budgets for an authored model would be ~100-300 numbers total; this is an estimate, not sourced.

### Gaps
- No empirical study located measuring recognizability vs coefficient count for animal meshes (e.g., SHREC/McGill datasets reconstructed by SPHARM). Recommend targeted search or running an experiment in the repo's harness (harness/fourier3d.py exists untracked).
- No source on LLM authoring of such representations.
