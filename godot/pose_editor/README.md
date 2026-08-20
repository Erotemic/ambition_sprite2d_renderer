# Ambition Godot pose-authoring pilot

This Godot project is an editor frontend over Ambition's SVG rig metadata and
motion JSON. It is not an authoritative character format and is not part of the
normal sprite-rendering or game-runtime dependency chain.

Generate the pilot workspace from the repository root:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool prepare
```

Then open either generated pose sheet in Godot 4.6.x:

```bash
godot --editor --path godot/pose_editor \
    godot/pose_editor/generated/fighting_polygon_sword_pose_sheet.tscn
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
remain owned by Ambition:

```bash
uv run python -m ambition_sprite2d_renderer.devtools.godot_motion_tool \
    apply-export godot/pose_editor/generated/exports/fighting_polygon_sword.poses.json
```

Regenerate the workspace afterward. An unchanged edit/export/apply/regenerate
round trip should return the same pose transforms within the motion IR's
serialized tolerance.

`generated/` and Godot's `.godot/` import cache are disposable and ignored by
Git. Only this small project/plugin plus the Ambition SVG/motion sources belong
in source control.
