# Agent Notes: Sprite Renderer Tests

This submodule contains renderer framework code and authored sprite content. Keep
those two concerns separate when adding tests.

## Authoring architecture

The universal contract is a registered target that reproducibly publishes
sprite-sheet page(s), animation/frame metadata, actor metadata, and review
artifacts. The target's internal drawing or posing representation is not part of
that contract.

Character rigs are optional. Some characters use bone or SVG rigs; others use
config-driven procedural generators, shared family helpers, scene graphs, or
bespoke Python drawing. Do not migrate a target onto a rig merely for
consistency, and do not describe direct procedural rendering as a temporary
legacy path when it remains the clearest expression of the art.

Unify at the family level when multiple related targets genuinely share anatomy,
pose math, part composition, or animation construction. Keep cross-family output
metadata such as bounds, anchors, sockets, face guides, and default poses
independent of rig internals.

## Test policy

Prefer tests that protect renderer and tooling invariants:

- sheet-builder manifest shape, paths, and sidecar generation
- registry discovery and install/copy contracts
- packing, cropping, scaling, alpha compositing, and frame extraction
- schema serialization and editor/rig math
- runtime-facing contracts that game code truly depends on

Avoid tests that merely freeze authored content decisions:

- exact animation row lists or frame counts for one character unless runtime code
  directly depends on that exact vocabulary
- exact tile names, prop names, palette tokens, or preview inventory for a single
  content set
- pixel-count or color-count assertions for art direction
- slow full-sheet renders whose only assertion is that a named art asset still
  exists

When a content target needs review, render it with the CLI and inspect the
preview artifacts. Keep that as a manual or optional visual-review workflow, not
as normal pytest coverage.

## Recommended pattern

Use a small number of representative render-basis tests to exercise each
renderer surface: config-authored characters, module-authored props/tiles, and
sidecar/manifest generation. These tests should assert generic properties such
as non-empty images, valid YAML shape, valid RON sidecars, and installable file
contracts. They should not assert that a specific authored sprite sheet kept the
same artistic choices.

When adding a new content target, do not add a new per-target test by default.
Add tests only when the change introduces reusable renderer behavior or a real
runtime-facing contract.
