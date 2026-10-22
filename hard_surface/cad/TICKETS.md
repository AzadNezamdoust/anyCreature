# Core tickets (filed by lanes that do not own cadkit core / cadkit/tools)

## From the fast-iteration lane (cadkit/fast, 2026-10-22)

T1. **Import cost: `import build123d` = 41-43 s on the loaded dev box** (`-X importtime`: build123d.brep_from_stl
    15 s, build_common 15 s, sklearn 12 s pulled in transitively). Every cold worker/round pays it. cadkit/fast
    works around it with a warm daemon (serve.py); core could lazy-import (avoid sklearn / brep_from_stl at
    `from cadkit import *`) so cold workers + the MCP server start in seconds.

T2. **Op-level API for caching / history.** cadkit/fast caches by wrapping the names `from cadkit import *` binds
    (cut/fuse/common/safe_fillet/... + build123d fillet/extrude/revolve/loft/sweep/offset). Ops called through
    Python operators (`a - b`, `a + b`, `a & b`) and kit-internal helpers are not cached. Ask: route operators +
    all kit ops through one `ops.call(name, fn, *args)` hook so caching / timing / per-op timeouts are uniform.

T3. **Stable sub-shape identity.** Edge/face args are keyed by a geometric fingerprint (BREP text is unstable:
    location-table order and "-0" differ between a fresh shape and its BinTools round-trip). A kit-provided
    `persistent_id(subshape, parent)` (TopExp map index on a provenance-keyed parent) would make keys exact
    and cheaper.

T4. **`refs.tag()` history across cache hits.** Tags set inside a cached op are not re-created on a hit (only
    LOG entries are replayed). Tags set at model level (the normal case) are fine. Ask: tags as data on the
    returned shape (label / attribute) instead of a module global, so they survive serialisation.

T5. **Fillet shrink is the norm on replicas**: L3 gate reports 'housing rim' 14 -> 9.6, 'trigger housing rim'
    8 -> 4, 'grip rim' 9 -> 6.2, 'foot rim' 6 -> 2.0, 'battery rim' split_partial. COURSE_CORRECTION says silent
    shrink = fail; the gate now fails it, kernel lane should own the root cause (profile corners tighter than
    the rim radius -> needs variable-radius or profile-corner pre-rounding).

T6. **G1 breaks on main surfaces**: L3 housing 162/186 smooth edges tangent (max 2.4-3.3 deg), grip 280/304
    (max 2.9 deg) - from polyline profiles with 2D vertex fillets that did not apply (side_solid fallback loop).
    Spline/arc-chain profile helper with guaranteed tangency would fix the class.

T7. **Worker (cadkit/worker.py) exits through OCCT teardown** - `python -m cadkit.worker` wall time was 45 s vs
    38.6 s internal on L3 and 143 s vs 116 s on L4. Use `os._exit` after flushing state.json (cadkit/fast does).

T8. **Body validity is checked only per final part.** Feature checklist needs kit queries that return
    feature geometry by name (boss/hole/rib) - today the gate finds features by part bbox, region or nearest
    cylinder; first-class feature records from feature ops (lip/boss/rib, COURSE_CORRECTION step 5) would let
    the gate check each by name.
