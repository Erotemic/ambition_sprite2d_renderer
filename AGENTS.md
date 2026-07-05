# Agent Notes: Sprite Renderer Tests

This submodule contains renderer framework code and authored sprite content. Keep
those two concerns separate when adding tests.

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
