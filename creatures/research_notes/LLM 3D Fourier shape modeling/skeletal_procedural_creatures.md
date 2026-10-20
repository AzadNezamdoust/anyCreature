# Skeleton-driven procedural creature modeling and compact parametric animal shape models

## Skeleton-to-surface authoring (Spore, B-Mesh, Blender Skin, ZSpheres, sweeps)

### Takeaway
Skeleton + per-node radius ("balls") is the established compact recipe: Spore uses a metaball skin over a spine and limbs, and B-Mesh uses a skeleton with key balls to produce a quad-dominant base mesh. Blender's Skin modifier is a simplified B-Mesh. Hecker states Spore's recipe stays "very small", but he gives no byte count.

### Cited Findings
- Spore regenerates the skin in real time as the player reshapes the torso and attaches or detaches limbs. The skin is one implicit surface of spherical metaballs. Hecker chose it because topological robustness mattered more than local control. — [Hecker, Liner Notes for Spore](https://www.chrishecker.com/My_Liner_Notes_for_Spore)
- Each Spore metaball is a 4th-order polynomial in squared distance, f = s[(p-c)^2/R^2 - 1]^4. It has center c, radius R and scale s (the "goopiness" control). Ellipsoidal metaballs were judged too slow. — [Hecker](https://www.chrishecker.com/My_Liner_Notes_for_Spore)
- In Spore, bone weights come from which body part generated each metaball. Large spine segments and fat torsos can shear (a fix was prototyped but not shipped). The skin is one surface, so it allows webbing between limbs (bat wings). — [Hecker](https://www.chrishecker.com/My_Liner_Notes_for_Spore)
- Spore body parts are pre-authored Maya "Rigblocks" with parameterized deformation handles. Players never edit polygons, which keeps the creature recipe small for Sporepedia transfer. No parameter counts were given. — [Hecker](https://www.chrishecker.com/My_Liner_Notes_for_Spore)
- Spore animation is procedural retargeting to unknown user morphologies: SIGGRAPH 2008 paper "Real-time Motion Retargeting to Highly Varied User-Created Morphologies" and GDC 2007 talk "How To Animate a Character You've Never Seen Before". — [Hecker paper page](https://www.chrishecker.com/Real-time_Motion_Retargeting_to_Highly_Varied_User-Created_Morphologies), [talk page](https://chrishecker.com/How_To_Animate_a_Character_You%27ve_Never_Seen_Before)
- B-Mesh (Ji, Liu, Wang, Computer Graphics Forum 29(7):2169-2177, 2010): the user sketches a 1D skeleton and places "key balls" at its nodes. The system generates a quad-dominant initial mesh, then refines it by subdivision and an evolution step. Edge flow follows the skeleton, which suits sculpting and skeleton animation. The skeleton and balls stay editable. — [EG DL](https://diglib.eg.org/handle/10.2312/CGF.v29i7pp2169-2177)
- Blender's Skin modifier was partly based on B-Mesh but omits the evolution step, the mesh fairing and the auxiliary balls. — [search summary citing Blender commit log](https://miikahweb.com/fi/blender/git-logs/commit/8801330c18b063e341e8263131c91695cd1b7bdf)
- There is an open-source Qt/OpenGL B-Mesh implementation. — [CorentinDumery/BMesh](https://github.com/CorentinDumery/BMesh)
- A related skeleton-to-quad paper exists (Usai et al. 2015). — [skel_to_quad PDF](https://vcg-legacy.isti.cnr.it/Publications/2015/ULPTS15/skel_to_quad.pdf). I did not read it.

### Inferences
- A minimal authoring schema is a tree of nodes, each with position, radius (optionally 2-axis elliptical), a parent link and a limb type. That is roughly 4-8 numbers per node. A quadruped needs about 25-40 nodes, so the recipe is roughly 150-300 floats. This is my estimate, not a sourced number.
- Spore's per-part "goopiness" scale and Skin-modifier radii are the analog of cross-section parameters. Generalized-cylinder sweeps with varying cross-sections (an elliptical profile per node, interpolated) are a natural generalization.

### Gaps
- ZBrush ZSpheres docs, GDC talks and sweep-surface/generalized-cylinder literature were not researched in this pass. Nothing is reported on them.
- The Blender Skin modifier manual body (radius, root, loose ends, Create Armature) was not retrievable (the fetch returned only navigation). Only the B-Mesh lineage is confirmed.
- Spore's actual recipe size in bytes: not found.

## Parametric animal shape models (SMAL, BARC)

### Takeaway
SMAL is a linear-blend-skinned template (about 3.9k vertices, 35 joints) with a PCA-based shape space and per-species Gaussians. It spans cats, dogs, horses, cows and hippos. The shape parameter count commonly used is 41. The original paper is inconsistent about training-set size and PCA dimension, so check it before quoting. BARC refines the dog shape space.

### Cited Findings
- SMAL (Zuffi, Kanazawa, Jacobs, Black, CVPR 2017) was built from 3D scans of toy figurines in arbitrary poses. The shape space covers lions, cats, dogs, horses, cows and hippos. — [CVF page](https://openaccess.thecvf.com/content_cvpr_2017/html/Zuffi_3D_Menagerie_Modeling_CVPR_2017_paper.html)
- The paper's template is a lioness mesh segmented into 33 parts, made symmetric. The pose vector is 3N = 99 values plus 3 for translation. Shape space is PCA on pose-normalized registered meshes. The generic prior is a zero-mean Gaussian with the PCA eigenvalues; family models are Gaussians over each class's PCA coefficients. Co-registration used a 30-dimensional shape space. — [ar5iv](https://ar5iv.arxiv.org/html/1611.07700)
- The paper lists 13 species in 5 families (Felidae, Canidae, Equidae, Bovidae, Hippopotamidae). Per-species counts sum to 451 scans in the text I retrieved, but the text also says 4141 and "41 scans". These conflict; the fetch tool summary may be unreliable. Variance explained is not reported. — [ar5iv](https://ar5iv.arxiv.org/html/1611.07700)
- Standard released SMAL: shape beta in R^41 ("derived from 41 scans of figurines"), pose 35 joints x 3 axis-angle, V in R^(3889x3), F in N^(7774x3), joints regressed linearly from vertices (35x3889). The 35-joint version adds ear articulation to the original 33. — [AniMer](https://arxiv.org/pdf/2412.00837), [Three-D Safari](https://arxiv.org/pdf/1908.07201)
- Per-part analytic deformations in SMAL: 7 per part (global scale, x/y/z scale, 3 stretches). — [ar5iv](https://ar5iv.arxiv.org/html/1611.07700)
- Fitting to an image with 19 keypoints plus a tail tip takes under a minute. — [ar5iv](https://ar5iv.arxiv.org/html/1611.07700)
- BARC (Rüegg, Zuffi, Schindler, Black, CVPR 2022) builds on SMAL and modifies the shape space to suit dogs. It uses breed-similarity and breed-classification losses, and a cladogram of 161 dog breeds. — [arXiv 2203.15536](https://arxiv.org/abs/2203.15536), [project](https://barc.is.tue.mpg.de/)
- hSMAL is a horse-specific SMAL variant. — [cv4horses](https://sites.google.com/view/cv4horses)

### Inferences
- For wolf/dog/horse/cat, SMAL says a handful of PCA coefficients (in the tens at most, 41 total available) plus the 99-value pose is enough for a coarse body. The body proportions are low-dimensional.
- Quality from few coefficients is not quantified in what I found (no variance-explained figure).

### Gaps
- SMALR (Zuffi 2018) was not researched.
- Exact SMAL variance explained per PC, and the training-scan count discrepancy (41 vs 451 vs 4141), are unresolved. Check the paper PDF.
- BARC's shape-parameter counts were not extracted (the PDF exceeded the fetch size limit).

## Orthogonal bases (PCA, Fourier, DCT, spherical harmonics) for compact comparison

### Takeaway
Low-order spherical harmonics capture general shape and discard fine detail, and PCA over the coefficients gives a population shape space. Sources found are general, not animal-specific.

### Cited Findings
- Dropping higher-order harmonics keeps the general form and discards fine surface detail; a few leading harmonics suffice for product shape. — [search results, springer chapter](https://link.springer.com/chapter/10.1007/978-3-540-73321-8_11)
- PCA is the main tool for summarizing SH coefficients across a population (Dette, Melas, Pepelyshev). — [TU Dortmund](https://eldorado.tu-dortmund.de/items/5e368b3f-c1f8-4ec7-9754-9d6671fbeade)
- Rotation-invariant SH descriptors shorten the descriptor and ease comparison of unaligned models (Kazhdan et al. 2003). — [Princeton](https://pixl.cs.princeton.edu/pubs/Kazhdan_2003_RIS/index.php)
- CAESAR-based work uses PCA for facial surfaces, SH for the whole head, and Fourier descriptors for body silhouettes. — [BMVC 1999](https://bmva-archive.org.uk/bmvc/1999/papers/33.pdf)

### Inferences
- Low frequency maps to overall proportion and high frequency to detail. This is supported generally but not shown for animals in these sources. A star-shaped (single radius function) SH fit fails for limbs and tails; apply it per body part or along skeleton arc length (1D Fourier/DCT of radius series per limb) instead. This is a design inference.

### Gaps
- No animal-specific Fourier/DCT compactness numbers found. No parameter-count benchmarks.

## Rigged GLB via auto skinning

### Takeaway
Skeleton-proximity weights smoothed by diffusion are the standard auto-skinning approach (Pinocchio). If the mesh is generated from the skeleton, per-part weights come for free, as in Spore.

### Cited Findings
- Pinocchio (Baran and Popović, SIGGRAPH 2007) embeds a template skeleton in the mesh. It assigns bone weights by proximity, smoothed by a diffusion equilibrium equation. It typically rigs a character in under a minute and correctly rigged 13 of 16 test biped characters automatically (the other 3 with one hint). It produces LBS artifacts and no blend shapes. — [Pinocchio PDF](https://people.csail.mit.edu/ibaran/papers/2007-SIGGRAPH-Pinocchio.pdf), [CSAIL abstract](https://publications.csail.mit.edu/abstracts/abstracts07/ibaran/ibaran.html)
- Spore derives weights from the generating part of each metaball. — [Hecker](https://www.chrishecker.com/My_Liner_Notes_for_Spore)
- SMAL itself is LBS with linear joint regression from vertices. — [AniMer](https://arxiv.org/pdf/2412.00837)

### Inferences
- GLB export needs skin joints, inverse bind matrices and per-vertex JOINTS_0/WEIGHTS_0 (max 4 influences). That is glTF spec knowledge I did not source here.
- Blender's Skin modifier plus Create Armature plus automatic weights is a plausible offline path, but I could not verify the docs.

### Gaps
- No GLB/glTF-specific auto-skinning sources were searched.
- Other auto-skinners (bounded biharmonic weights, RigNet) were not researched.
