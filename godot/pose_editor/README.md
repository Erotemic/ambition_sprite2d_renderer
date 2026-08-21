# Ambition Godot motion-authoring pilot

This Godot project is an editor frontend over Ambition's SVG rig metadata and
motion JSON. It is not an authoritative character format and is not part of the
normal sprite-rendering or game-runtime dependency chain.

Install the exact editor version pinned by this project from the repository root:

```bash
./scripts/install_godot.py
```

This installs a checksum-verified official Linux editor under the ignored `tpl/`
directory. It supports x86_64 and arm64 and does not install export templates,
because this authoring frontend does not export Godot games.

## Static pose sheet

Generate the pilot workspace:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool prepare
```

Then open the generated pose sheet with the normal helper; it discovers the
repo-local pinned binary automatically. `open` performs a headless Godot import
pass first so the freshly generated preview PNGs are available to ResourceLoader
before the editor loads the generated scene:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool open
```

Every canonical pose is a complete independently editable `Skeleton2D` in the
ordinary 2D viewport. The art is preview-only PNG material generated from the
original SVG parts; source SVG remains authoritative.

For this pilot, edit bone translation and rotation (and root translation). The
Ambition import validator rejects bone/root scaling and root rotation because
the retained renderer compatibility projection cannot represent those operations
losslessly yet. This is a pilot-boundary restriction, not a limitation of the
motion IR itself.

After editing, choose **Project > Tools > Export Ambition Pose Sheet**. Godot
writes a neutral export bundle under `generated/exports/`. Apply that bundle
through Python so schema validation, sparse normalization, and source metadata
remain owned by Ambition. The importer preserves source pose files byte-for-byte
when Godot differs only within the round-trip tolerance, so editing one pose
should normally modify exactly one `.pose.json` file:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    apply-export godot/pose_editor/generated/exports/pointed_polygon.poses.json
```

For a quick visual acceptance check, render a single named pose through the
normal Python sprite-renderer seam instead of rebuilding the whole gameplay
sheet:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    render-pose humanoid/fighting_polygon/jab/contact
```

## AnimationPlayer clip authoring

The clip frontend generates ordinary Godot `AnimationPlayer` resources from
Ambition clips without changing authority. Open the Fighting Polygon clip sheet:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool open-clips
```

The current sheet exposes `jab`, `walk`, `grab`, `pummel`, and `throw_forward`
side-by-side. Each cell has its own `Skeleton2D` and `AnimationPlayer`. Use the
normal Godot Animation panel: play, scrub, hand-pose a bone, key its native
Transform property, insert keys at arbitrary times, delete keys, or retime an
individual property track. There is no requirement that the rest of the body
have a key at the same time.

The scene is generated in the SVG rig's native horizontal facing. A character
binding may adapt a shared motion library whose source deltas were authored in
the opposite facing; that reflection happens during preparation, and Python
reverses it when an edit is written back to the shared library. Pose what you
see in Godot. Do not manually mirror a west-facing character to compensate for
the source library's orientation.

The generated timeline represents animation, not sprite frames.
`Animation.length` is the authored clip `duration_s`, and its 1/60-second `step`
is only an editor-grid preference. Existing `sampling.frame_count` /
`frame_duration_ms` values are legacy game-sheet publication metadata and do not
constrain Godot key placement.

Named poses remain Ambition semantic anchors underneath the generated animation.
If a Godot property curve differs from the pose backbone, export stores that
property as a clip-local Ambition scalar track; it does not mutate the shared
named pose or create synchronized whole-body snapshots. Unedited properties keep
inheriting their named-pose backbone.

The current editable transform subset is root translation and bone
translation/rotation. Linear and hold/discrete tracks round-trip, including
arbitrary insertion/deletion/retiming. Native Godot Rotation tracks use radians
in the editor and convert to unwrapped Ambition degrees on export. Scale, root
rotation, cubic/custom easing, added unrelated property tracks, and whole-track
deletion are rejected explicitly until the retained renderer/schema boundary can
preserve them losslessly.

After editing, choose **Project > Tools > Export Ambition Clip Sheet**. Check the
neutral export before writing source:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    apply-clip-export --check \
    godot/pose_editor/generated/exports/pointed_polygon.clips.json
```

Then apply it:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    apply-clip-export \
    godot/pose_editor/generated/exports/pointed_polygon.clips.json
```

### Sprite sampling is a backend policy

The clip can now be evaluated continuously at arbitrary seconds. Sprite frames
are chosen separately. Inspect the economical non-uniform bake plan with:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    sample-plan jab
```

The default adaptive profile subdivides when joint motion exceeds 3 pixels, bone
orientation deviates by more than 7.5 degrees, or one bitmap would otherwise be
held for more than 250 ms, with a default budget of 16 frames. Named pose anchors
and animation markers are preserved as mandatory sample points.

The current game-facing sheet format still wants one duration per animation row.
To see the smallest uniform cadence satisfying the same quality budget:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    sample-plan jab --uniform-compatibility
```

For review, `render-clip` uses the non-uniform adaptive plan and writes variable
GIF frame holds. It does not change the shipped sheet metadata:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    render-clip jab \
    --output /tmp/fighting_polygon_jab.gif \
    --strip /tmp/fighting_polygon_jab.png
```

Use `--legacy-sampling` when you specifically want an A/B render of the old
fixed publication samples.

The integration check asks Godot itself to load and export the generated
AnimationPlayer resources, then compares them with Ambition source without
writing:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    headless-clip-check
```

## Generated-resource boundary

`generated/` and Godot's `.godot/` import cache are disposable and ignored by
Git. The pilot also ignores Godot's generated `*.gd.uid` script sidecars: all
committed plugin/script references are path-based and every UID-bearing generated
scene/resource is disposable, so the sidecars provide no durable identity that
Ambition needs to preserve. Only this small project/plugin plus the Ambition
SVG/motion sources belong in source control.

The static-pose headless round-trip remains available as well:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool headless-check
```
