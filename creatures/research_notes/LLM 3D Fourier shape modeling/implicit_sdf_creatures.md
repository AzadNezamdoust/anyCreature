# Implicit / SDF / skeleton-based implicit modeling of organic creatures

Research caveat: iquilezles.org article URLs (smin, distfunctions) returned 404 and Shadertoy returned 403 to the fetcher, so IQ-specific numbers could not be verified from primary pages. Items from background knowledge are placed under Inferences or Gaps, not Cited Findings.

## 1. SDF primitives, smooth min, domain ops, ShaderToy creatures

### Takeaway
SDF scenes are built by min/max booleans over primitives; replacing hard min with smooth min removes the crease between overlapping parts. Famous IQ creature shaders (Snail, Selfie Girl) exist as pure-formula scenes, but I could not retrieve their primitive/parameter counts.

### Cited Findings
- Union/intersection of SDFs A(p), B(p) are min(A,B) and max(A,B); adding/subtracting a constant grows/shrinks (rounds) a shape — [search summary of SDF tutorial](https://varun.ca/ray-march-sdf/) (via web search snippet).
- IQ's "Selfie Girl" is an animated character drawn by a single complex shader equation, explained in a ~25 min video — [MetaFilter](https://metafilter.com/194834/Paint-the-universe-with-geometry-smoothstep-and-noise).
- IQ's pixel-shader Snail is at shadertoy.com/view/ld3Gz2 — [I Programmer](https://www.i-programmer.info/news/144-graphics-and-games/9307-build-your-own-pixel-shader-snail.html).
- IQ gave a SIGGRAPH (SF chapter) talk "Unlocking Creativity with Signed Distance Fields" — [SIGGRAPH SF](https://san-francisco.siggraph.org/?p=5157).

### Inferences
- (Background knowledge, unverified here) IQ's smin variants: polynomial quadratic `h=max(k-|a-b|,0)/k; min(a,b)-h*h*k/4`, cubic, exponential, power; polynomial is cheap and gives local support; exponential is associative (order-independent) but has global support. Round-cone / capsule / ellipsoid are the standard limb primitives; ellipsoid is only a distance bound. Verify at iquilezles.org/articles/smin and /distfunctions.
- Domain ops (symmetry via abs(x), repetition, twist/bend, displacement) halve authoring cost for bilaterally symmetric creatures.

### Gaps
- Primitive/parameter counts for Snail and Selfie Girl: not retrievable (403/404). Needs manual read of shader source.

## 2. Convolution surfaces, Blobtree, metaballs, meshing

### Takeaway
Skeleton-based implicit surfaces (Bloomenthal convolution surfaces, Wyvill Blobtree) generate smooth organic blends from skeleton segments plus radii; mesh with marching cubes (or dual contouring) for game use.

### Cited Findings
- Bloomenthal & Shoemake (SIGGRAPH 1991) extended Blinn's blobs by 3D convolution with skeletons of polygons or curves; Bloomenthal's work treats conditions for seamless, bulge-free convolution surfaces — [Calgary BlobTree tree-modeling paper / search summary](https://cspages.ucalgary.ca/~blob/pdf/2004_cgi_tree_modeling.pdf), [Unchained Geometry papers](https://unchainedgeometry.com/JBloom/papers.html).
- Book: Bloomenthal (ed.), "Introduction to Implicit Surfaces", with chapter "Convolution of Skeletons" (algebraic blends, branching objects) and Wyvill chapters on animation — [Elsevier](https://shop.elsevier.com/books/introduction-to-implicit-surfaces/bloomenthal/978-0-08-050928-0).
- BlobTree: tree with primitives as leaves and operators (blend, bounded blend, CSG, precise contact modeling, warping) as interior nodes; evaluation = tree traversal; formulated in 1999 (WGG99) — [Calgary](https://cspages.ucalgary.ca/~blob/webpapers/05/aesthetics.pdf).
- Calgary 2004 tree paper argues summing distance-based skeletal primitives avoids convolution surfaces' cost and complexity while giving bulge-free blends — [Galbraith, MacMurchy, Wyvill](https://cspages.ucalgary.ca/~blob/pdf/2004_cgi_tree_modeling.pdf).
- Wyvill: any object can be a skeleton element provided point-to-skeleton distance is computable — [Wyvill/Kacic-Alesic via search summary](https://graphicsinterface.org/wp-content/uploads/gi1991-31.pdf).
- Metaballs: summed finite-support falloff fields thresholded to an isosurface; Wyvill's soft-object model is smoother; falloff may use distance to lines/surfaces; render via raycasting or marching cubes — [Wikipedia Metaballs](https://en.wikipedia.org/wiki/Metaballs).

### Inferences
- Segment (capsule/round-cone) skeleton + per-end radius + smin is effectively a cheap "distance-based" skeleton implicit, matching the Calgary alternative to convolution.
- Marching cubes on a 64^3-128^3 grid then decimation/retopo is the usual route; dual contouring preserves sharp features (not needed for organic). Unverified here.

### Gaps
- ZSpheres/skin surfaces, RBF implicits, sphere-tracing papers, dual contouring numbers: not researched with sources (tool-call budget, fetch failures).

## 3. SDF + Fourier/series radius; spectral features in neural SDFs

### Takeaway
No source found for "Fourier-series radius along a segment" as an established technique; it is a natural extension (radius r(t)=a0+sum a_k cos(kt)+b_k sin(kt) in a round-cone/revolved profile). Neural SDFs do use Fourier features/SIREN to overcome spectral bias.

### Cited Findings
- Plain MLPs have spectral bias; Fourier feature mapping makes the NTK stationary with tunable bandwidth (Tancik et al.) — [summary](https://wiki.davidl.me/view/Fourier_Features_Let_Networks_Learn_High_Frequency_Functions_in_Low_Dimensional_Domains), [arXiv 2006.10739](https://fugumt.com/fugumt/paper_check/2006.10739v1_enmode).
- SIREN uses sinusoidal activations; can hit a spectral bottleneck at high frequencies; fixed by noisy init (WINNER) — [arXiv 2509.09719](https://arxiv.org/html/2509.09719v2).
- For neural SDFs, PE-equipped MLPs show noisy artifacts; effective frequency exceeds PE band — [arXiv 2401.01391](https://arxiv.org/html/2401.01391v1) (single preprint, not peer-reviewed-checked).
- Random Fourier features are sensitive to scale sigma; PE parameter cost grows with embedding dim — same sources above.

### Inferences
- A hand-authored "Fourier-radius" tube is a closed-form, compact (about 2K+1 coefficients per limb) analogue of these learned encodings, with exact interpretability; keep |r'| below 1 to keep the SDF a near-valid bound.

### Gaps
- No literature on Fourier-series-radius capsules specifically.

## 4. Strengths/limits for game assets

### Takeaway
Implicit models are extremely compact and authorable by formula, and fix tube seams via smooth blending, but game use needs a bake step to meshes with retopology, UVs and skin weights.

### Cited Findings
- Meshing metaballs/implicits is commonly done with marching cubes — [Wikipedia](https://en.wikipedia.org/wiki/Metaballs).
- Selfie Girl runs real-time but may be slow on weak GPUs (full raymarch is heavy) — [MetaFilter](https://metafilter.com/194834/Paint-the-universe-with-geometry-smoothstep-and-noise).

### Inferences
- Seams: smin/blobtree blend radius k controls fillet size; larger k bulges/loses detail; exponential/polynomial differ in locality.
- Topology/UVs: marching cubes output is uneven triangles with no UV layout; needs remesh (quad remesh/decimation) and automatic UV unwrap; poly budget controlled by grid resolution plus decimation.
- Rigging: skeleton is already the model's source, so bone weights can be derived from per-segment field contributions; useful advantage. Unverified in sources.
- For a 2070-mobile-class baseline, bake to mesh once rather than raymarch at runtime.

### Gaps
- Concrete poly budgets, UV/rigging pipeline sources, and benchmarks not found.
