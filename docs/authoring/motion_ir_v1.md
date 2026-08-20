# Ambition character motion IR v1

The motion IR is the schema seam between character-authoring sources and editor
frontends. Godot, PySide, procedural generators, and agent tools may all read or
write these semantics. None of their native scene/widget/solver models are part
of the contract.

The first pilot is the Fighting Polygon sword/brawler pair. It intentionally
keeps the existing sprite publication API and generated sheet/manifest contract
unchanged while replacing the editable motion authority beneath it.

## Authority

A character's static rig and motion have separate authorities:

```text
SVG
  artwork
  views
  markers / rest geometry
  bone topology
  part -> bone bindings
  art bind pivots
  z order
        +
Ambition motion JSON
  named rest-relative poses
  clips and timing
  interpolation
  optional scalar tracks
  animation markers
        |
        v
PreparedCharacterMotion
        |
        +--> Godot authoring frontend
        +--> PySide authoring frontend
        +--> Python renderer compatibility projection
```

The SVG's `ambition-svg-rig-v1` metadata remains authoritative for static rig
geometry. Motion JSON must not duplicate rest pivots or rest bone transforms.
A frontend derives those from the SVG when it opens a character.

Gameplay hitboxes, damage, capture rules, cancel windows, rollback state, and
other fighter semantics remain outside this representation.

## Character binding

Each character has one small `*.motion.json` binding. It chooses an SVG view, a
motion library, and the presentation mapping needed by the existing sheet
renderer. Sword and brawler have distinct SVG bindings but deliberately point at
the same motion library in the pilot.

The render mapping is presentation data rather than pose data:

```text
frame_point_px = root_anchor_px
               + (rig_point - svg_rig_root) * frame_px_per_rig_unit
```

This preserves the current publication frame without making 128x192 sprite
pixels the coordinate system of the authored pose library.

## Motion library

A library is a directory with a small `library.json` manifest and independently
mergeable pose/clip files:

```text
library.json
poses/
    humanoid__fighting_polygon__idle.pose.json
    humanoid__fighting_polygon__jab__contact.pose.json
clips/
    idle.clip.json
    jab.clip.json
    ...
```

`library.json` names roots rather than enumerating every file. This avoids a
central merge hotspot when different agents add or edit independent poses and
clips.

The v1 coordinate contract is serialized explicitly:

```json
{
  "linear_unit": "rig_user_unit",
  "x_axis": "right",
  "y_axis": "down",
  "rotation_unit": "degrees",
  "positive_rotation": "clockwise",
  "bone_transform": "parent_local_delta_from_svg_rest"
}
```

`rig_user_unit` means the root SVG's user-space unit for the selected rig view.
This is deliberately not a Godot unit or a sprite pixel.

## Pose

A pose is a sparse whole-body state. Bone transforms are parent-local deltas
from the SVG rest rig, not absolute/world transforms:

```json
{
  "schema": "ambition-pose-v1",
  "id": "humanoid/fighting_polygon/jab/contact",
  "rig_profile": "humanoid-articulated-v1",
  "state": {
    "root": {"position": [16.28, 0.0]},
    "bones": {
      "torso": {"rotation_deg": 8.648},
      "near_arm_u": {"rotation_deg": -103.284},
      "near_arm_l": {"rotation_deg": 5.948}
    }
  }
}
```

Missing values mean identity deltas. The rest pose therefore requires no
repeated transform table in every pose.

A named pose is reusable source data, not a claim that raw transforms fit every
future humanoid. `rig_profile` states the topology/profile it was authored for.
Retargeting between different proportions remains an explicit preparation step.
The Fighting Polygon v1 namespace is intentionally pilot-specific rather than a
universal humanoid inheritance language.

## Clip

A clip is pose-centric. It records timeline duration independently from sprite
sampling and can refer to whole-body named poses:

```json
{
  "schema": "ambition-clip-v1",
  "id": "jab",
  "loop": false,
  "duration_s": 0.225,
  "sampling": {
    "frame_count": 5,
    "frame_duration_ms": 45
  },
  "pose_keys": [
    {"at_s": 0.0, "frame": 0, "state": {}},
    {"at_s": 0.045, "frame": 1,
     "pose": "humanoid/fighting_polygon/jab/anticipation"},
    {"at_s": 0.09, "frame": 2,
     "pose": "humanoid/fighting_polygon/jab/contact"}
  ]
}
```

A key may contain an inline state or reference one named pose. Pose references
may carry local overrides when a clip needs a deviation from a canonical pose.

`tracks` are available for properties that genuinely need independent
continuous curves. Their targets are backend-neutral semantic paths such as:

```text
root.position.x
bone.near_arm_u.rotation_deg
bone.near_hand.position.y
parameter.body_opacity
```

The core model is therefore not restricted to stop-motion pose sequences, but
it also does not reduce every animation to unrelated property channels.

`markers` are optional named animation synchronization hints. They are not
fighter gameplay timing authority.

## IK and procedural animation

IK, foot targets, expression channels, and similar solver controls are authoring
mechanisms, not permanent pose semantics. A frontend may use IK while editing;
on save/export the resulting parent-local FK transforms are sufficient for a
normal pose.

The migration utility follows the same rule. It evaluates the legacy
`RigDocument` at every published frame and bakes the solved FK state. Legacy
expression and IK channel names therefore do not survive in the new source.
Procedural Python authoring may remain useful, but its durable output should be
poses/clips in this IR.

## Current renderer compatibility

The Python renderer still consumes `RigDocument` internally. During the pilot,
`PreparedCharacterMotion.to_rig_document()` creates a disposable in-memory
projection containing direct FK channels. This is an adapter, not a second
editable authority.

The Fighting Polygon target modules load their `*.motion.json` bindings and
construct this projection before calling the same sheet-building APIs they used
before. Consequently the game-facing spritesheet and manifest seam does not
change during the schema migration.

## Agent tooling

`motion_ir_tool` provides compact schema-oriented operations:

```bash
python -m ambition_sprite2d_renderer.devtools.motion_ir_tool \
    describe ambition_sprite2d_renderer/data/characters/fighting_polygon_sword/fighting_polygon_sword.motion.json

python -m ambition_sprite2d_renderer.devtools.motion_ir_tool \
    validate ambition_sprite2d_renderer/data/characters/fighting_polygon_sword/fighting_polygon_sword.motion.json
```

`migrate-legacy` and `compare-legacy` are transition tools. They are useful for
bringing another legacy rig across the seam and verifying every published pose,
but they do not define the long-term authoring model.

## Godot mapping

The intended Godot mapping is deliberately mechanical:

- SVG rig bone -> `Bone2D`;
- SVG marker-derived rest transform -> `Bone2D.rest` / local rest transform;
- pose bone delta -> local pose transform;
- clip pose key -> timed transform key or application of a named pose;
- scalar track -> ordinary animation property track;
- animation marker -> editor timeline marker where useful;
- preview-only SVG part raster -> `Sprite2D` rigidly attached to its bone.

Godot scenes/resources are generated/editor-facing products. The JSON + SVG
schema remains sufficient to reconstruct the authoring workspace in another
frontend.

## Godot pose-sheet pilot

The first concrete editor frontend lives under `godot/pose_editor/`. It is a
small Godot 4.6 project plus an `EditorPlugin`; generated scenes, preview PNGs,
and export bundles are disposable and ignored by Git. The exact supported editor
patch is pinned in `godot/pose_editor/GODOT_VERSION`. Install that version
repo-locally with:

```bash
./scripts/install_godot.py
```

The installer downloads the official Linux editor release, verifies its pinned
SHA-512 checksum, and installs only the executable under ignored `tpl/`. Normal
sprite regeneration therefore remains independent of Godot. A version bump is
an explicit repository change rather than an implicit update to whatever release
is newest on the network.

Prepare both Fighting Polygon sheets from the authoritative SVG + motion sources:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool prepare
```

The generator creates one literal multi-skeleton scene per character. Every
canonical named pose is a complete `Skeleton2D` in the ordinary 2D viewport, so
idle, anticipation, contact, recovery, and other poses can be compared and
manipulated side-by-side rather than reduced to timeline thumbnails.

The mapping is intentionally direct:

```text
Ambition RigDefinition          Godot generated scene
-----------------------         ---------------------
rig root                         RigRoot Node2D
bone parent/local rest           Bone2D hierarchy + Bone2D.rest
pose root delta                  RigRoot transform
pose bone delta                  Bone2D transform relative to rest
rigid SVG part                   preview-only cropped Sprite2D under its bone
part z                           Sprite2D.z_index
```

The preview texture's source-space bind pivot is attached to the Bone2D origin.
At rest, the child texture transform cancels the part's authored bind angle; as
the bone is manipulated, ordinary Godot parent transforms produce the same
rigid cutout behavior as the Python renderer. Godot rasterization is not part of
the shipped asset contract: these PNGs exist only to make the editor useful.

The generated scene is not source of truth. A small plugin exposes **Project >
Tools > Export Ambition Pose Sheet** and writes an
`ambition-godot-pose-export-v1` bundle under `generated/exports/`. Python then
validates and normalizes it back into the existing independent `.pose.json`
files:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    apply-export godot/pose_editor/generated/exports/fighting_polygon_sword.poses.json
```

This two-step export is deliberate. GDScript does not own Ambition's canonical
JSON serialization, validation, sparse-state rules, or source metadata. The
Godot plugin reports edited transforms; the Python schema layer decides whether
and how those become authoritative pose files.

The pilot currently accepts bone translation/rotation and root translation from
Godot. Bone/root scale and root rotation are rejected at the Python boundary
because the retained `RigDocument` renderer projection cannot consume them
losslessly. Keeping that restriction at the compatibility seam prevents an
editor feature from silently creating source that ordinary sprite regeneration
cannot publish. The neutral IR can support those transforms once the renderer
no longer depends on the legacy projection.

A headless round-trip check is also available when Godot is installed:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    headless-check
```

It prepares the scenes, asks Godot itself to load and export them, and compares
the result against the source poses without writing. This is the guard against
coordinate/sign/winding drift at the editor boundary.

The pilot intentionally does not yet make Godot's `AnimationPlayer`, IK
modification stack, `.tscn`, or `.tres` resources authoritative. The next
question after pose editing proves stable is how much of ordinary
`AnimationPlayer` can be generated from `ClipLibrary` while preserving the same
one-way generated-resource boundary.
