# Goals

Long-arc directions for `ambition_sprite2d_renderer`. This doc is the
north star — read it before doing structural work, and update it when
a goal lands or shifts.

## 1. Coherent authoring families, stable published contract

**The universal contract is the published asset, not the character's internal
representation.** A registered target may use whichever authoring method best
serves its artistic intent, but publishing it must reproducibly produce the
sprite-sheet pages and rich metadata that runtime consumers need.

Current character authoring includes several legitimate families:

- bespoke procedural Python drawing,
- config-driven `CharacterGenerator` implementations,
- shared procedural helpers for related casts such as the pirates,
- bone/rig-document and SVG-part renderers,
- scene-graph and multipart boss pipelines, and
- specialized hybrids for characters whose silhouettes or motion need them.

A rig is one optional family tool. It is not the canonical representation of a
character, and a target should not be migrated to a rig merely for consistency.
Likewise, direct Python drawing is not a temporary legacy path when it is the
clearest way to express a design.

**Where we are:** useful families already exist, but their boundaries are
uneven. `_pirate_common` successfully shares one parametric rig across related
pirates; `toon_side` shares procedural anatomy and pose code across many presets
but has grown into a large archetype switch; several distinctive characters use
purpose-built Python or SVG/rig pipelines. Some repeated anatomy, pose math,
framing, and sheet plumbing can be unified, but not all repeated-looking code
represents the same artistic abstraction.

**Where we want to be:**

- Each character uses the smallest appropriate authoring family.
- Families share genuine repeated machinery: pose math, anatomy primitives,
  palette handling, part composition, framing helpers, or animation recipes.
- Bespoke targets remain bespoke when sharing would flatten their silhouette,
  motion, or construction.
- Every registered character publishes the same validated runtime-facing
  gameplay products: sprite-sheet image page(s), animation/frame layout
  metadata, actor metadata, and canonical review output. Portrait-capable
  characters additionally publish an independent portrait sheet and named-clip
  manifest without prescribing how the source portrait is rendered.
- Cross-family metadata such as body bounds, anchors, sockets, face guides, and
  default poses can be authored or derived without requiring a bone rig.
- A renderer advertises capabilities honestly. Producing a requested raster
  size by resizing an already-rendered image is not the same capability as
  rerendering the character at that resolution.

**Why this matters:**

- **Artistic freedom stays explicit.** The authoring system follows the sprite's
  intended form rather than forcing every character through humanoid bones or a
  common silhouette.
- **Duplication is reduced at the right level.** Related characters can share a
  family without turning family-specific abstractions into global mandates.
- **Runtime integration stays simple.** The game consumes sheets and metadata;
  it does not need to know whether a character was painted procedurally, posed
  with bones, assembled from SVG parts, or generated from YAML.
- **New presentation products remain possible.** Portraits, thumbnails, and
  selection cards can be added to the publishing contract while each family
  chooses an appropriate native rendering path.

**Signs we've gotten there:**

- The README and agent guidance clearly state that rigs are optional.
- Generator families have names, documented ownership, and examples of when to
  use them.
- Shared helpers are extracted where several targets genuinely use the same
  concept; no repository-wide base rig is required.
- Large family modules such as `toon_side.py` are split along cohesive artistic
  or rendering boundaries rather than mechanically into one file per preset.
- Publishing validates the common sheet/manifest/actor-metadata contract for
  every registered target regardless of family.
- Tests use representative family fixtures and the cheapest faithful render
  path available; they do not require every target to support arbitrary native
  scaling.

**Concrete steps that move us toward this:**

- Inventory the current authoring families and document the intended extension
  point for each.
- Extract repeated helpers inside a family when the abstraction is already
  demonstrated by multiple characters.
- Split monolithic family modules around stable concepts such as anatomy,
  palettes, poses, and archetype-specific adornment.
- Add shared output metadata types when runtime or presentation consumers need
  them, while keeping their production independent of any one family.
- Add new publishing products through the target/output contract, then provide
  family-level defaults and bespoke overrides where appropriate.

## 2. Unified Target abstraction

**Where we are:** ✅ — one unified `Target` class (module-authored /
config-authored constructors) landed in
[`registry/discovery.py`](ambition_sprite2d_renderer/registry/discovery.py).
Discovery walks tack-ons + main YAML configs + review NPC configs and
returns one unified `dict[str, Target]`. CLI consumers use the registry
uniformly — `canonical <name>` / `sheet <name>` / `publish <name>` work
without caring which authoring surface produced the target.

The `Target` abstraction unifies discovery, publishing, installation, and
runtime-facing outputs. It does **not** imply a universal pose model, rig,
renderer implementation, or source-file format.

**Open follow-ups:**

- Bulk-port tack-on targets to expose the optional `render_canonical`
  hook (a small wrapper around `sheet_build.write_canonical`) where it
  removes the gallery's slow full-sheet fallback.
- ✅ Static dialog portraits are a first-class character-target output:
  config generators have a native high-resolution default, module targets have
  a fresh-canonical fallback, families may expose custom `render_portraits`, and
  publish/install carry the PNG/RON product.
- ✅ Full Hall default coverage, convention-derived catalog paths, a hard
  regeneration coverage gate, and portrait-gallery review tooling have landed.
- Add named expression/animation selection without imposing a common pose
  representation.
- Consolidate config and module machinery only where doing so simplifies the
  target/output contract; preserve both surfaces when they remain useful.

## 3. Test strategy

**Where we are:** the test suite is mostly "did the render pipeline
crash?" smokes. Some renders take seconds at full resolution, and many
assertions only check that `render()` produced a file at the expected path. The
genuine value is in:

- animation and manifest contracts,
- schema and sidecar validation,
- shared renderer-family invariants,
- crop/packing/measurement behavior,
- pose or rig math where a family actually uses it, and
- runtime-facing metadata that game code consumes.

**Where we want to be:** tests protect the common published contract and the
reusable invariants of each authoring family. Use low-resolution or reduced
fixtures when they faithfully exercise the implementation, but do not create a
false global requirement that every artistic pipeline rerender natively at any
size.

**Interim policy:** tests that require expensive full-resolution rendering and
have no cheaper faithful equivalent may use `@pytest.mark.slow_render` and run
explicitly with `pytest --run-slow-render`. Prefer a small number of
representative family tests over one expensive smoke test per authored target.

The point is not to freeze art direction. The point is to catch failures in the
registry, publishing contract, manifests, metadata, compositing, measurement,
and reusable family machinery.

## 4. Documentation

**Where we are:** README covers the CLI surface, the "Adding a new
sprite" walkthrough, and the category split. `docs/design.md`
captures architecture rationale. `registry/discovery.py`'s module
docstring is the authoritative current `Target` API contract.

**Where we want to be:**

- README stays as the practical walkthrough and family-selection guide.
- This file (`GOALS.md`) stays as the strategic direction.
- `docs/design.md` stays as architecture rationale, kept in sync with what's
  actually in the code.
- `registry/discovery.py`'s docstring stays as the current API spec.
- Agent guidance explicitly prevents "unify all characters onto one rig" work
  unless a fresh project decision replaces this plural-authoring stance.

Each document has one job. None of them should imply that an internal authoring
family is the runtime contract.
