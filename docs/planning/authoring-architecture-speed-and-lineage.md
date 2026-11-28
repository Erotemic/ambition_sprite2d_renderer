# Character authoring: architecture, speed, and lineage

**Status:** proposed implementation plan, 2026-11-27. This is a design and
migration document, not a claim that the proposed infrastructure has landed.

**Scope:** the character-authoring submodule (historically named the sprite
renderer), its shared Python infrastructure, and the seams with the existing
publication and runtime systems. Keep the submodule name and ownership boundary.

**Basis:** Ambition snapshot `a5c5030a7f45`, sprite submodule `d460b623659a`,
plus the recent experimental Roo wallaroo/parts/hierarchy/cloth and elemental
overlays. Recheck the current checkout before implementation. Names of proposed
interfaces below are descriptive, not new APIs to create on sight.

## 1. Objective and design rules

Make it pleasant for a human (or an agent) to author, understand, modify, render,
and retain a character. Make the simplest correct implementation the easiest to
find. Make fast regeneration a property of the architecture, not a separate
renderer that drifts from the real one. Preserve the art and the distinct visual
history of the cast as shared machinery improves.

Three kinds of reuse matter:

- **Mathematics:** one implementation of a mathematical operation for a given
  contract (coordinate convention, units, edge cases). No new two-bone IK solver
  just because a new character has knees.
- **Construction:** reusable local art, attachment frames, motion evaluation,
  and family-specific building blocks, without forcing unrelated characters into
  one anatomical model.
- **Work:** evaluate, draw, rasterize, pack, and validate only what is needed,
  at the appropriate granularity. Reuse the results when their inputs agree.

A good abstraction is named for something an author understands, has a small
contract, has at least one real consumer, and makes the consumer simpler. For a
new cross-family abstraction require a second genuinely different consumer or a
clear existing duplicate to migrate. Do not make a new framework in parallel
with one that already does the job. Prefer extension, consolidation, and removal
of obsolete paths. Allow deliberately bespoke art and specialized mathematics
when the reason is concrete.

### Existing boundaries to retain

- Read [README](../../README.md), [GOALS](../../GOALS.md), [AGENTS](../../AGENTS.md),
  [design](../design.md), and the [motion authoring guide](../agent_motion_authoring.md).
  This document elaborates those directions; it does not replace them.
- The registered `Target` and its published products are the universal contract.
  `FrameSource` is a useful optional authoring adapter, not a required base class.
  A rig is optional. Procedural Python, SVG, config jobs, chargen, and hybrids
  remain legitimate. Static props and effects should not acquire a skeleton just
  to use shared geometry or rendering.
- This repository owns authored material, values, and authoring tools. The main
  repository owns the meaning of runtime schemas, rules, and simulation. A
  shared secondary-motion authoring model is appropriate here; live response to
  physics and the runtime interpretation of published data belong in the engine.
- No baked drop shadows; no new binary art committed; no new worktrees in agent
  workflows. Do not change gameplay identity, hitboxes, sockets, move timings, or
  skin mechanics as incidental consequences of rendering cleanup.

## 2. A small vocabulary for authors

| Concept | Author's question | Meaning |
|---|---|---|
| Shape | What does it look like? | Local geometry and paint: paths, fills, strokes, images, material effects. |
| Part | What moves together? | Local artwork with a stable identity and a pivot. It can change appearance without changing identity. |
| Rig | How is it attached? | Named coordinate frames and their parent relationships, possibly with constraints. No requirement that each joint has artwork. |
| Pose | Where is everything now? | A configuration or intent: joint transforms, targets, parameters, visibility, expression, view. |
| Motion | How does it change? | A time-dependent function or authored clip producing pose values. |
| Scene | What should be drawn now? | Resolved artwork, transforms, order, visibility, and optional effects. |
| Look | What version of the character is this? | A maintained appearance recipe selecting materials, proportions, art, and compatible motion/rig bindings. |

These are concepts, not seven compulsory classes or inheritance levels. A
projectile can be a function of phase that draws a shape. Chlorine can evaluate
several gas volumes directly. Roo can place parts on a rig. A look can point to a
plain existing target; it need not be a new format. The test is whether an author
can explain how an image was made by reading the source, not how many layers of
objects it passes through.

### 2.1 Geometry and coordinate conventions

Use plain tuples and numbers for ordinary geometry. The geometry-only portion
should be importable with the standard library. Use the existing `core/` and
`authoring/` boundary; the README allows Pillow in the render core but pure
mathematics need not import it. Consolidate vector arithmetic, dot/cross products,
rotation, transforms, interpolation, curves, and bounds. Prefer existing names
with documented conventions over a new vector class or overloaded operators.

Document the existing screen convention (x right, y down, clockwise-positive
angles, usually degrees in authoring). Convert explicitly to other conventions:
`part_flipbook`/hierarchy rotation radians, SVG units and affine transforms,
chargen's 3D coordinates, and runtime world coordinates. Preserve each legacy
caller's angle zero, bend sign, length, scale, and target-clamping semantics
through adapters. A reflection is not a rotation; specify handedness and local
versus world transforms explicitly. Do not silently normalize a legacy convention.

A reusable IK result should make the effective reachable target and joint
positions available (or have an explicit adapter to obtain them). Document
unreachable, coincident, straight, folded, and zero-length cases. Use
`authoring/skeleton.py:two_bone_ik` and `two_bone_ik_points` as the starting point;
inspect their actual contracts before migrating callers. A shared solver should
not import character palettes, motion libraries, or a drawing backend.

### 2.2 Local artwork and stable attachment frames

Use `draw.part()` and the existing local-paint/recording infrastructure rather
than adding another drawing DSL. Art for a boot, eye, watch, or sleeve is a
function of its local parameters, not of the absolute pose. Place it by an
explicit transform. For example (schematic, using the existing part scope):

```python
with draw.part('watch', watch_pivot, watch_angle):
    draw_pocket_watch(draw, radius, palette)
```

The watch drawing should not need to know what clip Roo is playing. The pivot
and local shape are separate so a change of angle does not require new pixels.
A joint can exist without ink; a part may share a joint with other art. Keep
logical track IDs distinct from atlas texture IDs and display names. Preserve
identity when the same part changes texture, face expression, or view. Keep
layer order independent of parent order: e.g., a hand can belong to a forearm
and still draw over the head. Specify visibility and near/far depth explicitly.
A physical left/right limb is not necessarily always the near/far limb.

Use the existing `DrawRecorder`, `PillowPartDraw`, `shape_rig`, SVG parts and
scene machinery. Support native SVG and direct raster output, but do not require
all Pillow paint operations (especially procedural effects) to round-trip through
SVG. Prefer reusable part art for articulation; use directly painted frames
where deformation, material, or cost warrants it. The choice is per character
or layer, not an architectural ranking.

### 2.3 Pose evaluation and motion composition

Treat a pose as values and motion as a function of time. Preserve hand-authored
angles, procedural cycles, and semantic targets as valid inputs. Where an artist
means "put the hand here", solve the limb from the target; where the artist
means "swing by this angle", FK is the clearer representation. Reuse the existing
`motion_ir.py`, `motion_evaluation.py`, `motion_authoring.py`, `motion_retarget.py`,
`skeleton.py`, and `articulation_layers.py:PoseComposer`; reconcile their overlap
rather than writing another clip representation.

A useful evaluated-pose boundary for articulated families includes the local and
world joint frames, resolved contact constraints, view/appearance channels,
ordered visible part placements, and relevant landmarks. The precise type can
follow the current evaluator. Compute the pose once per requested sample and
consume it for artwork, body-rig products, socket transforms, and previews.
Keep logical (unscaled) coordinates separate from output raster size, and do not
make procedural targets manufacture irrelevant joints or geometry.

Compose locomotion, action, expression and secondary motion with explicit channel
ownership and deterministic precedence. Keep motion time, playback rate, phase,
and bake sampling distinct. Preserve planted feet, authored impact holds, sharp
changes in visibility, and event times. Smoothness is not indiscriminate blending
of every value. Use the existing `sprite_sampling.py` adaptive sample machinery
where supported, with mandatory key/contact/event boundaries and the correct
runtime interpolation oracle. Avoid increasing all frame counts as a substitute
for stable attachments and appropriate interpolation.

Recent Roo hierarchy work is an experimental concrete starting point. Generalize
its graph only after reviewing the existing rig structures and runtime contract.
A child's position/rotation should interpolate in its parent's frame. Specify
scale inheritance rather than assuming pixel-scale changes represent bone-length
changes. Texture selection and z-order are independent. Account for shortest
angle arcs versus deliberately authored spins, reflections, disappearing parts,
and parent availability. Derive hierarchy data from the authored rig as far as
possible, not a second hand-maintained graph of texture names. Existing targets
without hierarchy must retain their old behavior. Engine changes require both
Python/Rust parity and runtime verification, not just attractive offline GIFs.

### 2.4 Multiview and secondary motion

A part can have independently drawn views with corresponding local anchors;
choose views from orientation and use explicit visibility/depth. The source can
be 2D contours, authored SVG, or projection of simple 3D geometry. Reuse chargen
projection math when appropriate (`chargen/geometry.py`, `pose3d.py`) without
imposing chargen anatomy. A genuine turn can expose the far eye, change muzzle
contour and depth order, and move a tail behind the body. Squeezing the finished
sprite horizontally is not a substitute. Maintain the same physical side for an
asymmetric scar, holster, etc., unless a deliberate mirrored art variant is
specified. Distinct directional textures may still change discretely; interpolate
joint transforms independently. Do not promise arbitrary continuous texture morphs.

Secondary motion should describe an attachment chain, rest orientations, lengths,
stiffness, damping, gravity influence, inertia and angle limits. Use a small
shared mathematical model for coat panels, scarf ends, ears, chains and tails.
Roo's cloth should attach to the waist, not inherit leg rotations. Hem segments
move more freely than roots. Preserve useful authored motion for extreme poses.
Offline motion evaluation must be deterministic: a frame requested out of order
must not depend on a previous random render call. For stateful dynamics, define
initial state, time step, reset/loop semantics, and precomputation or checkpointing.
The engine can later simulate secondary motion from real acceleration and gravity;
keep those runtime effects visual, bounded, and separate from gameplay geometry.
A general deformable cloth/mesh solver is not a prerequisite for the first pass.

## 3. Make direct rendering easy and dependency-light

The existing dependency direction is `core <- authoring <- targets`; registration,
publication, editor bridges, and history tooling should consume it, not be imported
by mathematical helpers. Preserve the two existing target-registration surfaces.

```text
shape / local art  +  optional motion / rig / constraints
                  -> evaluated scene (or direct paint)
                  -> native raster / recording / optional SVG rasterizer
                  -> frame source or target product hooks
                  -> existing publisher, validation, quality tiers, atlases
```

This is a dataflow, not a mandatory new scene serialization layer. Allow a
character module to render one native frame with Python and Pillow without
importing all other character generators, Qt, a history store, or a packer.
Use lazy target/generator resolution and local imports at optional capability
boundaries. Inspect `registry/discovery.py`, `registry/character_generators.py`,
and `authoring/canonical.py`: the latter imports the generator roster even for
single-target still rendering. The prior missing-`resvg_py` failures show how an
unrelated SVG consumer can block direct procedural work. Audit actual transitive
imports before changing package extras; NumPy, YAML, resvg, lxml, Rich, and rectpack
are legitimate where used. Do not remove a declared dependency until consumers
are migrated. Keep production backend selection explicit: CairoSVG fallback is
not necessarily pixel-equivalent to native resvg and should not silently publish
as the native backend. Keep Qt and archive tooling off the render path.

Expose an easy, documented single-frame path for each authoring surface, reusing
`FrameSource`/`Target.render_canonical` or family hooks where appropriate. It must
not implicitly render every clip or publish the runtime bundle. Keep previews,
canonical stills, portrait renders (native resolution), full gameplay products,
and installed/published products distinct. Fast review is not publication evidence.

## 4. Character lineage is a first-class design constraint

Follow the parent repository's
[`character-generations.md`](../../../../docs/planning/game/character-generations.md)
and [maintained lineage workflow](../../../../docs/tools/generated-visual-tools.md#maintained-character-lineage-variants).
The archive is for evidence and research, not a production dependency. Keep the
historical package `design_history/` isolated from the installed renderer.

### 4.1 Distinguish identities and costs

| Identifier | Purpose | Does not imply |
|---|---|---|
| Character/catalog ID | Gameplay identity, kit and simulation | A unique renderer or single visual look |
| Lineage | Character as known to the player/design history | An art construction family |
| Era | Visually distinct holistic historical appearance | One era per commit or per refactor |
| Maintained variant ID | Current render source for a look | A published or selected skin |
| Target ID | Registered render/publish product identity | A new gameplay character |
| Part/rig family | Reused construction and posing infrastructure | Shared lore, ancestry, or lineage |
| Source revision/provenance | Evidence of a prior render or authorship | Executable source selection for maintained looks |

These dimensions are related, not interchangeable. A pirate family can serve
multiple distinct lineages. One lineage can have both a human and a wallaroo
look. Some intentionally separate character versions (including robot versions
with different mechanics) stay separate identities even if visually related.
Do not infer a new gameplay character from a target suffix or conflate skins
with forms having mechanics. See the parent plan for the exact `WornSkin` rules.

### 4.2 Keep the look, not a copy of its renderer

The current `ambition_sprite2d_renderer/data/lineage_variants.yaml` maps a
maintained variant to a current registered target or config; extend that catalog
only when an actual source-selection need arises. Existing supported forms can
reference current SVGs, rig data, configs and family implementations through
those targets. Preserve the important artistic choices as current authored data
or compact local drawing functions, not copies of historical Python pipelines.
A preserved look can use the latest common IK, part rendering, and motion tools
while retaining its old proportions, shapes, palette, and characteristic style.
Use explicit overrides for old silhouettes that cannot be expressed with the
current family. Do not create a giant conditional function with one branch per
historical commit or an inheritance chain of every redesign.

For a major redesign, first check which old look is worth preserving. Save or
identify its source recipe and representative reference, then author the new
look. If migration has no intentional artistic change, do not register a new era.
For Roo, the original shared human pirate and the wallaroo are candidate distinct
looks; small coat articulation revisions are not automatically distinct eras.
The maintained variant representation must be able to express both without
freezing two obsolete implementations of the same sword rig. This is an example
of the direction, not a decision to ship either as an extra skin today.

Old variants need the animation vocabulary appropriate to their use, not forced
modern Smash pose parity. Retarget modern posing only where useful and compatible;
record missing-row fallbacks. Skin appearance must not change the worn character's
body, combat geometry, move timing, or other simulation. Preserve historical
chronology and provenance independently of a normalized source; a refactor or
algorithmic speedup must not retroactively attribute old art to the refactor's
author. `design_history/lineages.yaml` and `variations.yaml` are historical indices,
not a verified census of distinct looks. Keep the documented visual audit and
curation step; do not coalesce eras solely by pixel-distance thresholds.

### 4.3 Lineage rendering should be inexpensive

Use three distinct work products, with no implicit escalation:

1. **Archive references:** optional research/review via existing archive tooling;
   preserve its cached evidence. Do not run archive replay as part of normal art
   generation, or create new agent worktrees to recover a look. If references
   aren't available, report the gap instead of making history up.
2. **Maintained stills / selected pose strips:** current `lineages.sh` default
   path. Render only the requested looks and review poses. Do not publish sheets,
   portraits, all tiers, or every move just to inspect a historical silhouette.
3. **Curated shipping generations:** ordinary registered targets/products and
   publisher. Explicit selection, with size/time/coverage measurements; no quota
   and no automatic publication of all history. Use the ordinary quality products
   and skin rules, not a parallel historical-asset system.

Concrete cleanup: `lineage_variants.py:render` currently calls
`discover_all_targets()` for every variant task; `main` submits one task per
variant and reconstructs the report afterwards. Resolve selected recipes once
per source snapshot, or initialize the registry once per worker if objects are
not safe to serialize. Reuse native canonical hooks and avoid redundant PNG
encode/decode passes only if the output and crop contract are preserved. Add
incremental still reuse based on the current source recipe and its transitive
inputs, image hash, backend/options and crop policy; reference-commit/label edits
alone should not invalidate pixels. The existing partial manifest merge checks
whether the source selector is unchanged, not whether transitive source content
is current. Extend its evidence so unchanged-selector but edited-source stills
are reported stale, and unselected failures/stale entries cannot be presented as
fresh. Reuse the existing publication/read-record machinery where sensible; a
review still need not become a full runtime bundle. Keep cache files and generated
images ignored, and preserve existing inspector distinctions.

Across compatible looks, share local art, prepared rigs, static pose evaluation,
and motion definitions when inputs actually match. Avoid keying solely on
character ID or lineage, since palette, proportions, rig, view, and quality can
change. Do not share pose results across different anatomical bindings without
proof of equivalence. Include lineage look identity and dependency evidence in
review provenance even when a raster is physically deduplicated. Do not combine
all historical looks in one huge atlas just to deduplicate parts: preserve product
locality, independent publication, and memory budgets. Consider cross-target
sharing only within the existing shared-atlas policy and after measuring benefit.

## 5. Speed is a design objective, not a quality toggle

Distinguish (a) edit-to-preview latency, (b) cold target regeneration, (c) warm
incremental regeneration and roster throughput, (d) lineage review throughput,
and (e) runtime draw/interpolation cost and packaged asset size. Improving one
can make another worse. For example more parts can reduce texture bytes but add
draw instances and metadata. Measure each separately. No default reduction of
resolution, supersampling, validation, or motion quality to claim a speedup.

### 5.1 Existing machinery to extend, not replace

- Parent `scripts/regen/sprites.sh` plans selected products and immutable bundles
  from a source snapshot, records read files/listed directories and policy rows,
  reuses current recipes, and supports multi-target jobs and atomic publication.
  `--only-missing`/`--missing-only` retains even stale selected bundles; it is not
  a freshness check. Use `--plan`, `--check`, `--audit` and the documented reports.
  See [sprite publication](../../../../docs/tools/sprite-publication.md).
- `publication.py`, `publication_store.py`, `read_record.py`, `products.py`,
  `build_selection.py`, `quality.py`, and `provenance.py` already supply much of
  the planning and evidence system. No replacement build system.
- `shape_rig`, `svg_parts`, `part_flipbook`, `sheet_build`, `frame_source`, and
  `sprite_sampling` already contain part reuse, windowed rasterization, recording,
  packing, sampling and replay paths. The existing SVG transform cache and bounded
  rotation worker pool are configurable. Read their cache keys and ownership before
  adding another cache. MaxRects packing already abandoned expensive exhaustive
  size searches; do not reintroduce them.
- `core/memory_budget.py` provides allocation guards; it is not a global concurrent
  scheduler. Existing publication worker cap is six, with default up to six and
  about half the CPUs. Coordinate nested worker pools and memory estimates instead
  of multiplying workers at each level. Keep profiler instrumentation optional.

### 5.2 Initial evidence and benchmark design

Previous exploratory session, same snapshot plus overlays (not remeasured in
this documentation pass): 12 Chlorine idle frames spent about 43% of the sampled
render in Gaussian blur and 38% in Bezier evaluation; 33 Roo frames across four
clips spent about 26% of the sampled part build in Pillow transforms. A bounded
Bezier-sampling cache prototype reduced the median time for 37 representative
Chlorine frames from 3.36 s to 2.82 s (~1.19x), with all 37 pixel-identical and
~99% cache hits. These are local microbenchmarks, not whole-roster speedups or
current baseline guarantees. Reproduce with recorded inputs before landing.

Extend `scripts/profile_benchmarks.py` (already has quick/representative suites,
explicit targets, repeat count, isolated reports) rather than starting a second
profiling tool. Use the unprofiled timing path for speed comparisons and profiles
for diagnosis; if an unprofiled suite mode is missing, add one there. Start with:

| Case | Representative | Questions |
|---|---|---|
| Direct static/short procedural | Existing cheap prop or enemy | Import + one-frame overhead; does any full-sheet work run? |
| Procedural material | Chlorine; Bromine if present | Curve sampling, local blur/composite, allocation costs |
| Articulated procedural | `pirate_admiral` (Roo) | Pose evaluation, part capture, raster reuse, keyframe + tween parity |
| SVG rig | `oiler` or `noether` | Native subset rasterization, rotations, cache reuse |
| Chargen | `alice_v2` and a compatible second body | Projected art, view/rig binding, retargeting |
| Stress | One existing large boss/long animation from profile results | Peak RSS, page count, decode/packing/validation costs |
| Lineage | Alice maintained variants and one other multi-look lineage | Canonical-only, no-archive repeat, targeted invalidation |

Keep the existing representative targets as a broader regression set. Use
registered IDs verified in the current checkout. Record commit/snapshot, recipe,
Python/Pillow/resvg versions, backend, seed, size/tier, job/rotation limits,
CPU/memory environment, and whether caches are cold, warm or forced. Distinguish
process startup/discovery, preparation/evaluation, local art rasterization,
composition, packing, validation, serialization, portraits, tier conversion,
and bundle selection/install where applicable. Record wall and CPU time, peak
RSS (include worker processes), generated pixels/texels, part/texture/draw counts,
cache hit/miss counts and bytes, output bytes by tier, and number of executed
stages. Report medians and spread over at least three unprofiled repetitions;
use a single worker for attribution and actual production parallelism for
throughput. Use isolated output/cache locations or the existing force controls,
not another Git worktree. Leave benchmarks out of normal pytest.

Proposed initial performance budgets (engineering targets to ratify after a
baseline, not current measured results):

- An unchanged request on a warm accepted cache executes zero art render, pack,
  or tier-conversion stages for those unchanged products. A doc-only change
  should not invalidate art recipes that do not read the doc. A selected lineage
  label or provenance-only change should rebuild metadata, not pixels.
- Single-frame/canonical preview must not generate a full sheet unless an
  explicitly reported legacy fallback is unavoidable. Aim for subsecond warm
  single-frame feedback on ordinary targets on a reference development machine,
  excluding application/editor startup; establish separate realistic budgets
  for heavy SVGs and bosses.
- An appearance-only change invalidates dependent art, not independent motion
  compilation; a changed clip invalidates its affected poses rather than all
  local artwork. Start by measuring and reusing within a target before introducing
  persistent partial-target caching. Correct dependency invalidation is mandatory.
- For behavior-preserving cleanup, investigate median slowdowns above 5% on the
  representative suite when larger than measurement noise. For an optimization
  require an evidenced meaningful improvement (e.g. 10% on its named stage or
  target, or a clear memory/latency win), report the end-to-end tradeoff, and do not
  demand a fictitious global speedup. Allow justified, documented art improvements
  to cost more. No fragile wall-time thresholds in ordinary unit tests.
- Record full/derived tier bytes and peak memory; keep within existing allocation
  reserve and configured worker budgets. Do not ship more lineage skins by default
  just because generation is faster. Assess Android package and in-game CPU/GPU
  costs using real products on target hardware. Set runtime draw/time budgets
  with the main repo's measurements rather than extrapolating from PNG sizes.

### 5.3 Optimization order

Prefer eliminating work over making redundant work faster.

| Priority | Work | Correctness / cost gate |
|---|---|---|
| A | Isolate discovery/imports, canonical-only render, once-per-worker registry; use existing incremental publisher | Same selected products; unrelated backends absent do not block direct preview; no unnecessary rebuild |
| A | Consolidate pure curves/vectors/IK; cache immutable sampled local contours (bounded) | Exact results for unchanged semantics; explicit migration adapters; pixel parity |
| A | Evaluate shared pose once for art and metadata; precompile tracks/constant transforms; reuse canonical from compatible render | Keyframes, contact, sockets and body metrics agree; native portraits retain resolution |
| B | Cache local part rasters by complete art/view/material/quality inputs; keep stable pivots; avoid painting/rotating only to discard pixels in recording | Recording and replay use same semantics, including alpha, ordering, pivots, grouping and erasers |
| B | Use tight effect regions (blur halos included), precompute constant masks, limit supersampling intermediates and allocations without changing output | Correct transparent edges, filter support and bounds; no cropped effects; representative parity |
| B | Avoid duplicate whole-sheet composition/validation/packing when already-proven artifacts or reusable intermediates suffice | Same validation coverage; current-input evidence; final product bytes and metadata verified |
| C | Tune parallelism and clip/frame memory retention; shared intermediate disk cache if profiles justify it | Determinism, memory reserve, bounded queues, failure isolation, no nested oversubscription |
| C | More adaptive sampling or runtime blending work where supported | Mandatory events, interpolation/pose error budget, runtime parity, measured draw cost |

Recording-only optimizations deserve care. Current part builders sometimes paint,
reduce, capture, and replay to establish equivalence. Do not assume an apparently
redundant transform is redundant when it is the independent reference for a
parity check. Separate authoritative publication checks from optional review
images. Use existing parity/equivalence facilities and hash validated inputs
before reusing evidence. Native tier rendering versus derived quality conversion
must preserve the declared product semantics. No silent skips of validators.

### 5.4 Cache design

Keep caching out of character art authoring wherever practical. Cache the
smallest useful deterministic artifact, with explicit ownership and bounded
memory. Use immutable input values or canonical content digests, not object IDs,
mutable arrays, or filename alone. A cache should not return a mutable Pillow
image that a consumer can accidentally paint into and corrupt for everyone else.
Use copies or clear immutable ownership conventions. For transforms include pivot,
logical scale, subpixel phase, resampling/rotation convention, alpha treatment,
and destination quality; for local rasters include geometry, appearance/view,
resolved palette, backend/version, rasterization options and scale. For pose
results include motion, rig/look binding, time, constraints, seed and context
needed by the evaluation. Avoid hashing entire source trees for each frame.

Layer the work: compiled motion/rig per source instance; bounded local geometry
and part/transform caches per worker; product-level persistence through existing
recipe evidence. Consider persistent intermediate reuse across targets/lineages
only when cold profiles show a real saving after key computation, disk I/O, and
validation overhead. Do not store binaries in Git. Prefer compact reusable data
rather than every unique rotated frame forever. Define clear/reset behavior,
versioned keys, atomic writes, no cache poisoning on failure, and debug hit/miss
counters. Always allow a cold build from the current source without any cache.

## 6. Canonical authoring inventory and migration strategy

The following is an initial map of real source modules, not a directive to move
everything to a new path. Audit signatures and dependency edges; document a
canonical import for each contract as consolidation lands.

| Author need | Start with |
|---|---|
| IK, rotations, FK | `authoring/skeleton.py`, `rig.py`, current transform helpers; consolidate duplicated math |
| Curves and paint primitives | `core/draw.py`, `authoring/common_draw.py`, `sheet_build.py`; promote the common subset of `_clockwork_enemy_art.py` and `_magic_character_art.py` |
| Pose composition and clips | `motion_ir.py`, `motion_evaluation.py`, `motion_authoring.py`, `articulation_layers.py`, `animation_constraints.py`, `animation_keys.py` |
| Gaits and foot contact | `surface_gait.py`, existing rig constraints and [walk cycle baseline](../walk_cycle_baseline.md) |
| Local art/pivots and draw order | `draw_recorder.py`, `shape_rig.py`, `svg_parts.py`, `svg_scene.py`, `rigdoc.py` |
| Part publication and interpolation | `part_flipbook.py`, recent `part_hierarchy.py` overlay, `sprite_sampling.py`; runtime is the contract owner |
| Body geometry and sockets | `body_rig.py`, `rig_gameplay_body.py`, `gameplay_geometry.py`, `core/measure.py`, actor contract |
| Multiview anatomy | `chargen/geometry.py`, `pose3d.py`, `rig.py`, `motion_retarget.py`; reuse only appropriate portions |
| Single-frame and published output | `FrameSource`, `Target`, `canonical.py`, `portrait.py`, `sheet_build.py`, existing publisher |
| Maintained visual looks | `data/lineage_variants.yaml`, `lineage_variants.py`, normal target/config authoring |
| Historical evidence | `design_history/` (isolated) and parent lineage plan |

Start the IK migration with concrete duplicates previously identified in Alice,
Oiler, Goblin, Toon, Robot, Sanic, Vikings, Runge-Kutta, heavy pirate and Math Show
prizes. Verify the actual current implementations, classify by semantics and
migrate in small groups. Use thin adapters for legitimate convention differences;
do not maintain several copies of triangle solving. Test unreachable targets and
singular poses, including the returned end point, not just the intermediate joint.
Retire wrappers when all callers use the same contract. Likewise consolidate
identical Canvas and Bezier helpers now shared across clockwork, magic, and
unrelated elemental targets. Generic drawing infrastructure must not depend on a
particular enemy's private art. Preserve output first, then improve art separately.

### Prevent duplication from returning

- Add a short task-oriented canonical API guide, linked from `AGENTS.md`, with
  runnable minimal examples for direct paint, procedural animation, and reusable
  articulated parts. Update it alongside migrations; it should tell an agent where
  to start, not enumerate every historical helper.
- Before adding generic math, search existing core/authoring and family helpers.
  If a shared operation is missing a case, improve it with the relevant contract
  and migrate consumers rather than writing a private solver. New specialized
  code is permitted with a concrete reason and ownership in the appropriate layer.
- An extracted helper is not a completed consolidation until real callers migrate.
  Include deletion/adapter counts and changed import paths in the handoff.
- Build an AST-based duplicate inventory/ratchet using normalized syntax and
  candidate names for math, interpolation, and drawing helpers. Start report-only;
  classify actual duplicates versus same-name different contracts. Track the
  reviewed legacy exceptions (file/symbol and reason), then fail on new confirmed
  duplication or forbidden cross-layer imports. Avoid false-positive-driven busywork
  and arbitrary "no function named lerp" rules. Do not freeze artistic code style.
- Add lightweight import-smoke checks for geometry-only and single-target rendering
  without unrelated optional capabilities; use subprocesses to avoid import-cache
  false positives. Do not make full art renders a prerequisite for every new target.

## 7. Implementation sequence and exit criteria

The plan is incremental. Keep every step usable and independently reviewable;
separate behavior-preserving migrations from deliberate artistic changes. Avoid
rewriting rig formats, changing game schemas or implementing a universal scene
language as prerequisites to basic consolidation.

| Phase | Work | Exit criteria |
|---|---|---|
| 0. Evidence | Inventory existing APIs/imports and exact duplicate groups; baseline profiles, published output/pose contracts and maintained look references | Reproducible benchmark commands and evidence; selected migration candidates; no speculative new abstractions |
| 1. Math | Canonical vector/transform/IK/curve/easing contracts, adapters and bounded Bezier cache; migrate duplicates | Same semantics/pixels where required, generic invariants, actual caller migration, measured speed/memory |
| 2. Paint and preview | Consolidate Canvas/paint helpers; lazy discovery/backends; canonical-only and lineage worker improvements | Direct low-dependency render works, at least two families consume common helpers, repeat lineage review measured, no archive dependency |
| 3. Adoption | Canonical API guide, AGENTS update, duplicate inventory/ratchet; document family boundaries | New characters have a clear path, confirmed duplicates cannot silently accumulate, legacy exceptions explicit |
| 4. Pose and parts | Reconcile existing motion/rig layers and evaluated-pose result, reuse for paint/body/sockets; stabilize track IDs and hierarchy | Roo and a distinct articulated family use shared machinery; keyframe and intermediate/runtime contracts hold; no duplicate joint evaluation where avoidable |
| 5. Reusable motion construction | Shared limb construction, multiview attachments, contact constraints, secondary-motion chain | Roo coat/tail/watch and another consumer genuinely share the model; predictable rendering out of order, correct near/far order and joint pivots |
| 6. Performance | Profile full pipeline; remove redundant recording/rasterization/composition/replay, region filtering, memory and parallelism improvements | Representative benchmark before/after and evidence gates; no loss of validation or art fidelity |
| 7. Lineage and family migration | Normalize selected historical looks into current sources, compare with references, incremental review cache and curated publication | Offline maintained rendering, visual review and provenance preserved, explicit package/quality and skin coverage report |

Lineage preservation is required in *every* phase; phase 7 is the wider migration,
not the first time to think about old art. Likewise speed is measured from phase 0
onward. Tackle the lineage still/cache work earlier when profiles justify it.
Suggested reference consumers are Roo (articulated procedural), Chlorine (material
procedural), Alice/Bob (chargen), and one native SVG rig. Keep other character
families usable throughout; avoid a flag-day conversion of the entire roster.

### Verification and handoff for each change

- Use a small number of mathematical and renderer-invariant tests: finite IK,
  attachment length/pivots, loop/contact semantics, view ordering, stable identity,
  cache invalidation, import isolation, and deterministic evaluation. Follow the
  submodule AGENTS test policy. Use `equivalence_harness.py`, `core/equivalence.py`,
  existing parity/part replay tests and pose sampling tools for representative
  render comparisons. Preserve original bytes where this is the contract; use
  existing transparent-pixel/parity tolerances where the pipeline already does.
- Compare key poses, intermediate poses, and clip transitions at stable world
  anchors, not individually fitted thumbnails. Check quality tiers, bounds,
  sockets and runtime-readable manifests when affected. A deliberately changed
  image requires review and explicit rationale, not a relaxed parity threshold.
- Check both cold and warm paths, changing one dependency at a time; verify a
  different look, backend or quality cannot reuse the wrong artifact. Check a
  scoped lineage render retains/report-stales other rows correctly. Test missing
  archive and missing unrelated optional dependencies. Do not mark stale review
  material as current.
- When changing runtime interpretation, include Rust tests/compile checks and
  game playback/performance verification (report unavailable tooling honestly).
  Keep semantic geometry and skin mechanics unchanged unless separately authorized.
- Deliver a source-only overlay with explicit affected paths, submodule commit
  commands and parent gitlink update. Give real generator previews and benchmark
  evidence when implementing art/performance. No broad staging, no generated
  binary assets in commits, no new worktrees. If a benchmark or validation is not
  run, state that; do not use a passing preview as a substitute.

## 8. First implementation increment

After this planning document, start with phases 0-1: reproduce the small Bezier
cache result, inventory exact duplicate math and their semantic differences,
consolidate the canonical IK solver and migrate a manageable first set of callers,
and record the API inventory and equivalence evidence. In parallel identify the
cheapest dependency-isolation and maintained-lineage review improvement; do not
turn the first patch into a general rig rewrite. Subsequent overlays should
advance the shared infrastructure, not just add new helper files. Keep unresolved
API names, runtime dynamics, persistent intermediate cache design, and shipping
skin curation as decisions to make with evidence during the appropriate phase.

Success is a renderer that is fast enough to iterate on, simple enough to read,
and cheap enough to retain important older looks: **one implementation of the
mathematics, several legitimate ways to express the artwork, one publication
pipeline, and maintained lineages that share current infrastructure.**
