# Design notes

## Universal target contract

The renderer unifies **registered outputs**, not character internals.
Publishing a character target reproducibly produces the runtime-facing visual
artifacts needed by the game:

- one or more sprite-sheet image pages,
- animation/frame layout metadata,
- actor metadata such as body geometry, anchors, sockets, and animation
  bindings where available, and
- canonical review output, and
- for portrait-capable characters, an independent portrait-sheet image and
  named-clip manifest.

The contract does not prescribe how the character is drawn or posed before the
artifacts are assembled.

## Plural authoring families

A character may be authored with bespoke procedural Python, a config-driven
`CharacterGenerator`, shared family helpers, a bone/rig document, SVG parts, a
scene graph, or a specialized hybrid. These are implementation families beneath
the same target/publishing boundary.

A rig is always optional. Use one when articulated parts, IK, reusable poses, or
an editor-backed workflow improve the character. Do not migrate a distinctive
procedural or specialized renderer onto a rig merely to make the repository
look uniform. Conversely, consolidate targets into a shared family when several
characters genuinely use the same anatomy, composition, or pose model.

The two registry authoring surfaces are orthogonal to those families:

- **module-authored targets** expose Python publishing hooks and may use any
  internal family;
- **config-authored targets** bind YAML jobs to a `CharacterGenerator`, whose
  implementation may itself be procedural, rigged, part-based, or hybrid.

## Config-driven character pipeline

Robot, goblin, boss, sandbag, and related targets use a shared config-driven
pipeline:

1. load a small YAML job,
2. choose a target generator,
3. sample a deterministic spec,
4. render animation frames,
5. compose a labeled sprite sheet and manifests.

This pipeline keeps target-specific drawing isolated while config shape,
manifest shape, body metrics, canonical previews, and generated-sheet naming
stay stable. It is a useful family/publishing surface, not the required internal
shape of every character.

## Shared animation vocabulary

`animation_vocab.py` is the canonical place for row names. The core vocabulary
matches the runtime character grid:

```text
idle, walk, run, jump, fall, slash, hit, death, blink_out, blink_in, dash
```

The extended review vocabulary covers player mechanics that exist or are likely
near-term but do not yet have a complete Rust animation selector:

```text
crouch, wall_slide, wall_jump, ledge_grab, climb, swim, interact, talk, block
```

Extended rows should be generated in Python first, reviewed visually, and then
wired into Rust deliberately in a later integration pass.

## Robot target

The side-view robot remains the primary player-character design reference. It
now supports the core runtime rows plus an extended review set for mechanics
that previously fell back to weak or mismatched poses:

- crouch / compressed idle,
- wall slide,
- wall jump,
- ledge grab / pull-up,
- climb,
- swim,
- interact,
- talk,
- block / guard.

`configs/robot.yaml` stays runtime-compatible. `configs/player_extended.yaml`
is the review sheet for the richer set.

## Sandbag target

Sandbag is no longer only a tack-on renderer. `SandbagGenerator` wraps the
same procedural sandbag drawing code behind `CharacterGenerator`, and
`configs/sandbag.yaml` renders an 11-row runtime-compatible sheet with
`crop: false` so 128×128 cells are preserved.

The tack-on command renders the sparse idle/hit/death output:

```bash
python -m ambition_sprite2d_renderer sheet sandbag
```

## Variants

`draw-all` uses the config filename as the output stem. This allows several
jobs for the same generator without overwriting outputs:

```text
robot_spritesheet.png
robot_runner_spritesheet.png
robot_guardian_spritesheet.png
player_extended_spritesheet.png
```

Future variants should normally be new YAML jobs when they remain members of
the same generator family. Add new target code when a variant needs a different
body plan, construction technique, or renderer.

## Portrait product

A dialog portrait is a separately published sprite-sheet product:

```text
<target>_portraits.png
<target>_portraits.ron
```

The manifest names a required `default` clip and is already shaped for later
static expressions and animated clips. The runtime catalog references this
product independently from the gameplay sheet.

Portrait production remains family-specific:

- config-driven `CharacterGenerator` targets receive a default compositor that
  rerenders a canonical pose at high source resolution and frames it from a
  logical face guide;
- module-authored characters opt in with `render_portraits`, which may reuse a
  procedural family helper, render an SVG/rig document at a larger scale, or
  draw custom portrait-specific detail;
- targets that cannot natively rerender must provide an explicit portrait path
  rather than enlarge pixels from the gameplay sheet.

`FaceGuide` is cross-family authoring metadata. It describes a logical face
region in the source character canvas and does not imply bones, IK, or a rig.
The common portrait packer owns only the published PNG/RON vocabulary; it does
not own the character's pose representation.

## Optional rig family and cross-family metadata

The rig-related modules provide reusable articulated-character machinery such
as bones, sockets, part ordering, pose validation, IK, and editor-backed rig
documents. Those concepts are valuable for characters that benefit from them;
they are not prerequisites for character registration or publication.

Some metadata is useful across all authoring families and must not be confused
with rig internals:

- a `FaceGuide` or portrait framing region can be emitted by direct Python,
  SVG, rigged, or specialized renderers;
- gameplay sockets and anchors may be authored directly, derived from pixels,
  or exported from a rig;
- body bounds and feet positions are normally measured from rendered frames;
- default poses and animation semantics describe published assets, not the
  method used to construct them.

Keep rig-only data private unless a published consumer needs it. Promote a
concept into shared metadata because sheets, portraits, or runtime systems use
it — not because one family happens to represent it with bones.

## Side-view walk-cycle baseline

Several side-facing biped families share one authored walk/run philosophy: an
8-frame contact/down/passing/up loop driven by ankle targets, with the knee
solved by a two-bone IK pass and an explicit near/far limb draw order. This
produces planted feet, cleaner silhouettes, and more stable depth reads than
the older direct-angle-only leg swing.

See `walk_cycle_baseline.md` for the practical recipe, the target list, and the
warning that mostly-front-facing characters such as ninja should not borrow
this side-profile treatment merely because both are humanoid.

## Package standards

- Keep target code under `ambition_sprite2d_renderer/targets/<category>/`
  where category is one of `characters/`, `props/`, `tiles/`, `icons/`,
  `projectiles/`.
  The registry walks these dirs at import time; see
  [`registry/discovery.py`](../ambition_sprite2d_renderer/registry/discovery.py)
  for the discovery contract and the README's "Adding a new sprite"
  section for the practical walkthrough.
- Generic helpers (drawing primitives and sheet-building infrastructure) live
  under `authoring/` —
  [`sheet_build.py`](../ambition_sprite2d_renderer/authoring/sheet_build.py) and
  [`common_draw.py`](../ambition_sprite2d_renderer/authoring/common_draw.py);
  the RON emitter and measure primitives live in
  [`core/`](../ambition_sprite2d_renderer/core/).
- Character-family helpers shared by several related characters live under
  `targets/characters/` with a leading underscore so discovery skips them — see
  `_pirate_common.py`. A family helper may be procedural, rigged, part-based, or
  hybrid.
- Keep abandoned experiments quarantined (see `pca_legacy/` at the repo root),
  never on the live render path.
- Keep each family API as small as its use cases allow. Do not invent a global
  pose or rig abstraction solely to make unrelated characters conform.
- Keep YAML jobs human-editable and deterministic where YAML is the chosen
  authoring surface.
- Keep generated sprite sheets and manifests outside the package, normally in
  `generated/` or a deliberate asset install destination.
