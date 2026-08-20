# Ambition Godot pose-authoring pilot

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

For this first pilot, edit bone translation and rotation (and root translation).
The Ambition import validator rejects bone/root scaling and root rotation because
the retained renderer compatibility projection cannot represent those operations
losslessly yet. This is a pilot-boundary restriction, not a limitation of the
motion IR itself.

After editing, choose **Project > Tools > Export Ambition Pose Sheet**. Godot
writes a neutral export bundle under `generated/exports/`. Apply that bundle
through Python so schema validation, sparse normalization, and source metadata
remain owned by Ambition. The importer preserves source pose files byte-for-byte
when Godot differs only within the round-trip tolerance, so editing one pose should
normally modify exactly one `.pose.json` file:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    apply-export godot/pose_editor/generated/exports/fighting_polygon_sword.poses.json
```

Regenerate the workspace afterward. An unchanged edit/export/apply/regenerate
round trip should return the same pose transforms within the motion IR's
serialized tolerance.

For a quick visual acceptance check, render a single named pose through the
normal Python sprite-renderer seam instead of rebuilding the whole gameplay
sheet:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    render-pose humanoid/fighting_polygon/jab/contact
```

The command writes a PNG under `generated/godot_pose_previews/` by default.
This preview is produced from the authoritative SVG + motion IR through the
same temporary RigDocument compatibility projection used by sheet generation;
it does not read the generated Godot scene.

`generated/` and Godot's `.godot/` import cache are disposable and ignored by
Git. The pilot also ignores Godot's generated `*.gd.uid` script sidecars: all
committed plugin/script references are path-based and every UID-bearing generated
scene/resource is disposable, so the sidecars provide no durable identity that
Ambition needs to preserve. Only this small project/plugin plus the Ambition
SVG/motion sources belong in source control.

The headless round-trip command performs the same import warm-up before loading
any generated scene:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool headless-check
```
