"""Godot AnimationPlayer frontend for Ambition motion clips.

Godot is allowed to behave like an animation editor: property tracks may have
independent key times, keys may be inserted or deleted, and clip-local edits are
serialized as sparse Ambition scalar tracks.  Named pose keys remain the
whole-body semantic backbone; they are not inferred from synchronized Godot key
columns.

Generated Godot scenes/resources remain disposable.  The durable source is the
Ambition motion IR, and sprite sampling remains a separate backend policy.
"""

from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image

from ambition_sprite2d_renderer.authoring.motion_evaluation import (
    effective_scalar_track,
    pose_backbone_track,
    sample_clip_state,
    sample_scalar_track,
    semantic_scalar_targets,
)
from ambition_sprite2d_renderer.authoring.motion_ir import (
    CharacterMotionBinding,
    ClipDefinition,
    PoseState,
    PreparedCharacterMotion,
    ScalarKey,
    ScalarTrack,
    Transform2D,
)
from ambition_sprite2d_renderer.authoring.sprite_sampling import (
    SpriteBakeProfile,
    SpriteSamplePlan,
    adaptive_sample_plan,
    uniform_compatibility_plan,
)

GODOT_CLIP_EXPORT_SCHEMA = "ambition-godot-clip-export-v2"
GODOT_CLIP_SHEET_SCHEMA = "ambition-godot-clip-sheet-v2"
DEFAULT_CLIP_PILOT = ("jab", "walk", "grab", "pummel", "throw_forward")

_EPS = 1e-7


def _round(value: float, digits: int = 6) -> float:
    value = round(float(value), digits)
    return 0.0 if abs(value) < 0.5 * 10 ** (-digits) else value


def _godot_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _godot_float(value: float) -> str:
    value = _round(value, 9)
    if value == 0.0:
        return "0.0"
    text = f"{value:.9f}".rstrip("0").rstrip(".")
    return text if "." in text else text + ".0"


def _vec2(value: tuple[float, float]) -> str:
    return f"Vector2({_godot_float(value[0])}, {_godot_float(value[1])})"


def _node_name(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not clean:
        clean = "Clip"
    if clean[0].isdigit():
        clean = "Clip_" + clean
    return clean


def _repo_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _actual_bone_transform(rest: Transform2D, delta: Transform2D) -> Transform2D:
    return Transform2D(
        position=(rest.position[0] + delta.position[0], rest.position[1] + delta.position[1]),
        rotation_deg=rest.rotation_deg + delta.rotation_deg,
        scale=(rest.scale[0] * delta.scale[0], rest.scale[1] * delta.scale[1]),
    )


def _clip_states(prepared: PreparedCharacterMotion, clip: ClipDefinition) -> list[PoseState]:
    return [prepared.library.resolve_pose_key(key) for key in clip.pose_keys]


def _supported_visual_targets(prepared: PreparedCharacterMotion) -> tuple[str, ...]:
    return semantic_scalar_targets(bone.id for bone in prepared.rig.bones)


def _track_interpolation(track: ScalarTrack) -> str:
    kinds = {key.interpolation for key in track.keys}
    if not kinds:
        raise ValueError(f"track {track.target!r} has no keys")
    if len(kinds) != 1:
        raise ValueError(
            f"track {track.target!r} mixes interpolation modes {sorted(kinds)}; "
            "Godot value tracks use one interpolation mode per property track"
        )
    interpolation = next(iter(kinds))
    if interpolation not in {"linear", "hold"}:
        raise ValueError(
            f"track {track.target!r} uses {interpolation!r}; the Godot motion frontend "
            "currently round-trips linear and hold interpolation"
        )
    return interpolation


def _validate_editor_clip(prepared: PreparedCharacterMotion, clip: ClipDefinition) -> None:
    if not clip.pose_keys and not clip.tracks:
        raise ValueError(f"clip {clip.id!r} contains no motion")
    for key in clip.pose_keys:
        if key.interpolation not in {"linear", "hold"}:
            raise ValueError(
                f"clip {clip.id!r} pose backbone uses {key.interpolation!r}; the Godot "
                "frontend currently projects linear/hold backbone interpolation"
            )
    for state in _clip_states(prepared, clip):
        if state.parameters:
            # Parameter channels remain legal source data, but a pose-key
            # parameter would change through the whole-body backbone and is not
            # currently represented by a Godot node property.
            raise ValueError(
                f"clip {clip.id!r} varies pose parameters; move them to independent "
                "parameter tracks before editing this clip in Godot"
            )
        root_values = [*state.root.position, state.root.rotation_deg, *state.root.scale]
        if any(not math.isfinite(float(value)) for value in root_values):
            raise ValueError(f"clip {clip.id!r} root contains non-finite values")
        if abs(state.root.rotation_deg) > _EPS:
            raise ValueError(
                f"clip {clip.id!r} uses root rotation, unsupported by the retained renderer projection"
            )
        if any(abs(value - 1.0) > _EPS for value in state.root.scale):
            raise ValueError(
                f"clip {clip.id!r} uses root scale, unsupported by the retained renderer projection"
            )
        for bone_id, transform in state.bones.items():
            values = [*transform.position, transform.rotation_deg, *transform.scale]
            if any(not math.isfinite(float(value)) for value in values):
                raise ValueError(f"clip {clip.id!r} bone {bone_id!r} contains non-finite values")
            if any(abs(value - 1.0) > _EPS for value in transform.scale):
                raise ValueError(
                    f"clip {clip.id!r} uses scale on bone {bone_id!r}, unsupported by the retained renderer projection"
                )

    supported = set(_supported_visual_targets(prepared))
    for track in clip.tracks:
        if track.target in supported:
            _track_interpolation(track)
            continue
        # Nonvisual parameter tracks are preserved in source but are not emitted
        # as Godot node tracks.  Other transform targets would silently disappear
        # from the editor, so reject those at this compatibility boundary.
        if track.target.startswith("parameter."):
            continue
        raise ValueError(
            f"clip {clip.id!r} uses visual track {track.target!r} that the current Godot "
            "frontend/renderer seam cannot represent losslessly"
        )


def _godot_interp(interpolation: str) -> int:
    if interpolation in {"linear", "hold"}:
        # A hold is represented by Godot's discrete value-track update mode,
        # not INTERPOLATION_NEAREST (which chooses the nearest key).
        return 1  # Animation.INTERPOLATION_LINEAR
    raise ValueError(f"unsupported Godot projection interpolation {interpolation!r}")


def _packed_floats(values: Iterable[float]) -> str:
    return "PackedFloat32Array(" + ", ".join(_godot_float(value) for value in values) + ")"


def _value_track_lines(
    index: int,
    *,
    path: str,
    times: Sequence[float],
    values: Sequence[str],
    interpolation: str,
    loop_wrap: bool,
) -> list[str]:
    transitions = [1.0] * len(times)
    return [
        f'tracks/{index}/type = "value"',
        f"tracks/{index}/imported = false",
        f"tracks/{index}/enabled = true",
        f"tracks/{index}/path = NodePath({_godot_string(path)})",
        f"tracks/{index}/interp = {_godot_interp(interpolation)}",
        f"tracks/{index}/loop_wrap = {str(loop_wrap).lower()}",
        f"tracks/{index}/keys = {{",
        f'"times": {_packed_floats(times)},',
        f'"transitions": {_packed_floats(transitions)},',
        f'"update": {1 if interpolation == "hold" else 0},',
        f'"values": [{", ".join(values)}]',
        "}",
    ]


def _scalar_curve(
    prepared: PreparedCharacterMotion,
    clip: ClipDefinition,
    target: str,
) -> ScalarTrack:
    track = effective_scalar_track(prepared.library, clip, target)
    _track_interpolation(track)
    return track


def _vector_curve(
    prepared: PreparedCharacterMotion,
    clip: ClipDefinition,
    x_target: str,
    y_target: str,
) -> tuple[list[float], list[tuple[float, float]], str]:
    x_track = _scalar_curve(prepared, clip, x_target)
    y_track = _scalar_curve(prepared, clip, y_target)
    x_interp = _track_interpolation(x_track)
    y_interp = _track_interpolation(y_track)
    if x_interp != y_interp:
        raise ValueError(
            f"Godot exposes position as one Vector2 track, but {x_target!r} uses {x_interp!r} "
            f"while {y_target!r} uses {y_interp!r}"
        )
    times = sorted({key.at_s for key in x_track.keys} | {key.at_s for key in y_track.keys})
    values = [
        (
            sample_scalar_track(x_track, at_s, duration_s=clip.duration_s, loop=clip.loop),
            sample_scalar_track(y_track, at_s, duration_s=clip.duration_s, loop=clip.loop),
        )
        for at_s in times
    ]
    return times, values, x_interp


def _animation_subresources(
    prepared: PreparedCharacterMotion,
    clip: ClipDefinition,
    *,
    ordinal: int,
) -> tuple[list[str], str]:
    _validate_editor_clip(prepared, clip)
    animation_id = f"Animation_{ordinal}_{_node_name(clip.id)}"
    library_id = f"AnimationLibrary_{ordinal}_{_node_name(clip.id)}"
    lines = [
        f'[sub_resource type="Animation" id={_godot_string(animation_id)}]',
        f"resource_name = {_godot_string(clip.id)}",
        f"length = {_godot_float(clip.duration_s)}",
    ]
    if clip.loop:
        lines.append("loop_mode = 1")
    # Editor grid preference only.  It is intentionally unrelated to sprite
    # publication cadence; arbitrary-time keys are accepted on export.
    lines.append("step = 0.016666667")

    track_index = 0
    root_times, root_values, root_interp = _vector_curve(
        prepared, clip, "root.position.x", "root.position.y"
    )
    lines.extend(
        _value_track_lines(
            track_index,
            path="LayoutAnchor/RigRoot:position",
            times=root_times,
            values=[_vec2(value) for value in root_values],
            interpolation=root_interp,
            loop_wrap=clip.loop,
        )
    )
    track_index += 1

    track_path_by_bone: dict[str, str] = {}
    for bone in prepared.rig.bones:
        if bone.parent:
            bone_path = track_path_by_bone[bone.parent] + "/" + bone.id
        else:
            bone_path = f"LayoutAnchor/RigRoot/Skeleton2D/{bone.id}"
        track_path_by_bone[bone.id] = bone_path

        position_times, position_deltas, position_interp = _vector_curve(
            prepared,
            clip,
            f"bone.{bone.id}.position.x",
            f"bone.{bone.id}.position.y",
        )
        position_values = [
            (bone.rest.position[0] + value[0], bone.rest.position[1] + value[1])
            for value in position_deltas
        ]
        lines.extend(
            _value_track_lines(
                track_index,
                path=bone_path + ":position",
                times=position_times,
                values=[_vec2(value) for value in position_values],
                interpolation=position_interp,
                loop_wrap=clip.loop,
            )
        )
        track_index += 1

        rotation_track = _scalar_curve(prepared, clip, f"bone.{bone.id}.rotation_deg")
        rotation_interp = _track_interpolation(rotation_track)
        lines.extend(
            _value_track_lines(
                track_index,
                path=bone_path + ":rotation",
                times=[key.at_s for key in rotation_track.keys],
                values=[
                    _godot_float(math.radians(bone.rest.rotation_deg + key.value))
                    for key in rotation_track.keys
                ],
                interpolation=rotation_interp,
                loop_wrap=clip.loop,
            )
        )
        track_index += 1

    lines.extend(
        [
            "",
            f'[sub_resource type="AnimationLibrary" id={_godot_string(library_id)}]',
            "_data = {",
            f"{_godot_string(clip.id)}: SubResource({_godot_string(animation_id)})",
            "}",
            "",
        ]
    )
    return lines, library_id



def write_clip_sheet(
    prepared: PreparedCharacterMotion,
    textures: Mapping[str, Any],
    bounds: Any,
    *,
    project_dir: Path,
    repo: Path,
    clip_ids: Sequence[str] = DEFAULT_CLIP_PILOT,
) -> Path:
    """Generate one ordinary AnimationPlayer cell per selected Ambition clip."""

    selected: list[ClipDefinition] = []
    for clip_id in clip_ids:
        try:
            clip = prepared.library.clips[clip_id]
        except KeyError as exc:
            raise ValueError(f"motion library has no clip {clip_id!r}") from exc
        _validate_editor_clip(prepared, clip)
        selected.append(clip)

    character = prepared.binding.character
    output = project_dir / "generated" / f"{character}_clip_sheet.tscn"
    output.parent.mkdir(parents=True, exist_ok=True)

    texture_ids: dict[str, str] = {}
    lines: list[str] = ["[gd_scene format=3]", ""]
    for index, part in enumerate(prepared.rig.parts, start=1):
        texture = textures[part.id]
        ext_id = f"tex_{index}"
        texture_ids[part.id] = ext_id
        lines.append(
            f'[ext_resource type="Texture2D" path={_godot_string(texture.res_path)} id={_godot_string(ext_id)}]'
        )
    lines.append("")

    library_ids: dict[str, str] = {}
    for ordinal, clip in enumerate(selected, start=1):
        resource_lines, library_id = _animation_subresources(prepared, clip, ordinal=ordinal)
        lines.extend(resource_lines)
        library_ids[clip.id] = library_id

    root_name = _node_name(character) + "ClipSheet"
    binding_path = _repo_relative(prepared.binding.path, repo)
    lines.extend(
        [
            f'[node name={_godot_string(root_name)} type="Node2D"]',
            f'metadata/ambition_schema = {_godot_string(GODOT_CLIP_SHEET_SCHEMA)}',
            f'metadata/ambition_character = {_godot_string(character)}',
            f'metadata/ambition_binding_path = {_godot_string(binding_path)}',
            f'metadata/ambition_rig_profile = {_godot_string(prepared.rig.profile)}',
            "",
        ]
    )

    margin = 48.0
    label_height = 58.0
    tile_width = max(300.0, float(bounds.width) + margin * 2.0)
    tile_height = max(360.0, float(bounds.height) + label_height + margin * 2.0)
    columns = 3
    bone_by_id = prepared.rig.bone_by_id

    for index, clip in enumerate(selected):
        state = sample_clip_state(prepared.library, clip, 0.0, bone_ids=prepared.rig.bone_by_id)
        cell_name = _node_name(clip.id)
        cell_path = cell_name
        layout_x = (index % columns) * tile_width
        layout_y = (index // columns) * tile_height
        sampling_text = f"legacy sprite {clip.frame_count} x {clip.frame_duration_ms} ms"
        label = f"{clip.id}  |  {clip.duration_s * 1000.0:.0f} ms  |  {sampling_text}"
        lines.extend(
            [
                f'[node name={_godot_string(cell_name)} type="Node2D" parent="."]',
                f"position = {_vec2((layout_x, layout_y))}",
                f'metadata/ambition_clip_id = {_godot_string(clip.id)}',
                f"metadata/ambition_sampling_frame_count = {clip.frame_count}",
                f"metadata/ambition_sampling_frame_duration_ms = {clip.frame_duration_ms}",
                f"metadata/ambition_pose_anchor_count = {len(clip.pose_keys)}",
                "",
                f'[node name="ClipLabel" type="Label" parent={_godot_string(cell_path)}]',
                f"offset_left = {_godot_float(margin)}",
                "offset_top = 8.0",
                f"offset_right = {_godot_float(tile_width - margin)}",
                "offset_bottom = 48.0",
                f"text = {_godot_string(label)}",
                "theme_override_font_sizes/font_size = 19",
                "",
                f'[node name="LayoutAnchor" type="Node2D" parent={_godot_string(cell_path)}]',
                f"position = {_vec2((margin - bounds.min_x, label_height + margin - bounds.min_y))}",
                "metadata/_edit_lock_ = true",
                "",
                f'[node name="RigRoot" type="Node2D" parent={_godot_string(cell_path + "/LayoutAnchor")}]',
                f"position = {_vec2(state.root.position)}",
                'metadata/ambition_role = "rig_root"',
                "",
                f'[node name="Skeleton2D" type="Skeleton2D" parent={_godot_string(cell_path + "/LayoutAnchor/RigRoot")}]',
                "",
            ]
        )

        node_path_by_bone: dict[str, str] = {}
        for bone in prepared.rig.bones:
            delta = state.bones.get(bone.id, Transform2D())
            actual = _actual_bone_transform(bone.rest, delta)
            if bone.parent:
                parent_path = node_path_by_bone[bone.parent]
            else:
                parent_path = cell_path + "/LayoutAnchor/RigRoot/Skeleton2D"
            bone_path = parent_path + "/" + bone.id
            node_path_by_bone[bone.id] = bone_path
            # Explicit gizmo dimensions avoid leaf-bone fallback warnings.  The
            # actual motion keys are still driven exclusively by rest + delta.
            gizmo_length = bone.length if bone.length > 1e-4 else 36.0
            lines.extend(
                [
                    f'[node name={_godot_string(bone.id)} type="Bone2D" parent={_godot_string(parent_path)}]',
                    "auto_calculate_length_and_angle = false",
                    f"length = {_godot_float(gizmo_length)}",
                    "bone_angle = 0.0",
                    f"position = {_vec2(actual.position)}",
                    f"rotation = {_godot_float(math.radians(actual.rotation_deg))}",
                    f"rest = Transform2D({_godot_float(math.cos(math.radians(bone.rest.rotation_deg)))}, {_godot_float(math.sin(math.radians(bone.rest.rotation_deg)))}, {_godot_float(-math.sin(math.radians(bone.rest.rotation_deg)))}, {_godot_float(math.cos(math.radians(bone.rest.rotation_deg)))}, {_godot_float(bone.rest.position[0])}, {_godot_float(bone.rest.position[1])})",
                    f'metadata/ambition_bone_id = {_godot_string(bone.id)}',
                    "",
                ]
            )

        for part in prepared.rig.parts:
            texture = textures[part.id]
            parent_path = node_path_by_bone[part.bone]
            sprite_name = "Art_" + _node_name(part.id)
            lines.extend(
                [
                    f'[node name={_godot_string(sprite_name)} type="Sprite2D" parent={_godot_string(parent_path)}]',
                    f"texture = ExtResource({_godot_string(texture_ids[part.id])})",
                    "centered = false",
                    f"position = {_vec2(texture.local_position)}",
                    f"rotation = {_godot_float(math.radians(texture.local_rotation_deg))}",
                    f"scale = {_vec2(texture.local_scale)}",
                    f"z_index = {texture.z}",
                    "metadata/_edit_lock_ = true",
                    "",
                ]
            )

        lines.extend(
            [
                f'[node name="AnimationPlayer" type="AnimationPlayer" parent={_godot_string(cell_path)}]',
                'root_node = NodePath("..")',
                "libraries = {",
                f'"": SubResource({_godot_string(library_ids[clip.id])})',
                "}",
                f'metadata/ambition_clip_id = {_godot_string(clip.id)}',
                "",
            ]
        )

    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf8")
    return output


def _export_track_dict(track: ScalarTrack) -> dict[str, object]:
    interpolation = _track_interpolation(track)
    return {
        "target": track.target,
        "interpolation": interpolation,
        "keys": [
            {"at_s": _round(key.at_s), "value": _round(key.value)}
            for key in track.keys
        ],
    }


def _semantic_export_tracks(
    prepared: PreparedCharacterMotion,
    clip: ClipDefinition,
) -> list[dict[str, object]]:
    tracks: list[ScalarTrack] = []

    def add_vector(x_target: str, y_target: str) -> None:
        times, values, interpolation = _vector_curve(
            prepared, clip, x_target, y_target
        )
        tracks.extend(
            (
                ScalarTrack(
                    target=x_target,
                    keys=tuple(
                        ScalarKey(at_s=at_s, value=value[0], interpolation=interpolation)
                        for at_s, value in zip(times, values)
                    ),
                ),
                ScalarTrack(
                    target=y_target,
                    keys=tuple(
                        ScalarKey(at_s=at_s, value=value[1], interpolation=interpolation)
                        for at_s, value in zip(times, values)
                    ),
                ),
            )
        )

    add_vector("root.position.x", "root.position.y")
    for bone in prepared.rig.bones:
        add_vector(
            f"bone.{bone.id}.position.x",
            f"bone.{bone.id}.position.y",
        )
        tracks.append(_scalar_curve(prepared, clip, f"bone.{bone.id}.rotation_deg"))
    return [_export_track_dict(track) for track in tracks]


def write_expected_clip_export(
    prepared: PreparedCharacterMotion,
    *,
    project_dir: Path,
    repo: Path,
    scene_path: Path,
    clip_ids: Sequence[str] = DEFAULT_CLIP_PILOT,
) -> Path:
    output = project_dir / "generated" / "expected_exports" / f"{prepared.binding.character}.clips.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    clips: list[dict[str, object]] = []
    for clip_id in clip_ids:
        clip = prepared.library.clips[clip_id]
        _validate_editor_clip(prepared, clip)
        clips.append(
            {
                "id": clip.id,
                "duration_s": _round(clip.duration_s),
                "loop": clip.loop,
                "tracks": _semantic_export_tracks(prepared, clip),
            }
        )
    payload = {
        "schema": GODOT_CLIP_EXPORT_SCHEMA,
        "character": prepared.binding.character,
        "binding_path": _repo_relative(prepared.binding.path, repo),
        "source_scene": "res://" + scene_path.relative_to(project_dir).as_posix(),
        "clips": clips,
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")
    return output


def load_clip_export(path: Path) -> Mapping[str, object]:
    raw = json.loads(path.read_text(encoding="utf8"))
    if raw.get("schema") != GODOT_CLIP_EXPORT_SCHEMA:
        raise ValueError(f"{path}: expected schema {GODOT_CLIP_EXPORT_SCHEMA!r}")
    if not isinstance(raw.get("clips"), list):
        raise ValueError(f"{path}: export lacks a clip list")
    return raw


def _track_from_export(
    raw: Mapping[str, object],
    *,
    clip_id: str,
    duration_s: float,
    supported_targets: set[str],
    tolerance: float,
) -> ScalarTrack:
    target = str(raw.get("target") or "")
    if target not in supported_targets:
        raise ValueError(f"clip {clip_id!r} exported unsupported or unknown track {target!r}")
    interpolation = str(raw.get("interpolation") or "")
    if interpolation not in {"linear", "hold"}:
        raise ValueError(
            f"clip {clip_id!r} track {target!r} uses {interpolation!r}; "
            "the current Godot seam round-trips linear and hold interpolation"
        )
    keys_raw = raw.get("keys")
    if not isinstance(keys_raw, list) or not keys_raw:
        raise ValueError(f"clip {clip_id!r} track {target!r} must contain at least one key")
    keys: list[ScalarKey] = []
    previous = -math.inf
    for index, raw_key in enumerate(keys_raw):
        if not isinstance(raw_key, Mapping):
            raise ValueError(f"clip {clip_id!r} track {target!r} key {index} is not an object")
        at_s = float(raw_key.get("at_s", math.nan))
        value = float(raw_key.get("value", math.nan))
        if not math.isfinite(at_s) or not math.isfinite(value):
            raise ValueError(f"clip {clip_id!r} track {target!r} contains non-finite key data")
        if at_s < -tolerance or at_s > duration_s + tolerance:
            raise ValueError(
                f"clip {clip_id!r} track {target!r} key at {at_s} lies outside duration {duration_s}"
            )
        at_s = max(0.0, min(duration_s, at_s))
        if at_s <= previous + _EPS and keys:
            raise ValueError(
                f"clip {clip_id!r} track {target!r} keys must have unique increasing times"
            )
        previous = at_s
        keys.append(
            ScalarKey(at_s=_round(at_s), value=_round(value), interpolation=interpolation)
        )
    return ScalarTrack(target=target, keys=tuple(keys))


def _track_probe_times(left: ScalarTrack, right: ScalarTrack, duration_s: float) -> list[float]:
    points = {0.0, duration_s}
    points.update(key.at_s for key in left.keys)
    points.update(key.at_s for key in right.keys)
    ordered = sorted(max(0.0, min(duration_s, value)) for value in points)
    probes = set(ordered)
    for a, b in zip(ordered, ordered[1:]):
        if b - a > 1e-9:
            probes.add((a + b) * 0.5)
    return sorted(probes)


def _track_max_error(
    left: ScalarTrack,
    right: ScalarTrack,
    *,
    duration_s: float,
    loop: bool,
) -> float:
    worst = 0.0
    for at_s in _track_probe_times(left, right, duration_s):
        # Sampling a looping curve exactly at duration wraps to zero, which is
        # the intended animation boundary.  Midpoint probes catch interpolation
        # differences inside every ordinary segment.
        a = sample_scalar_track(left, at_s, duration_s=duration_s, loop=loop)
        b = sample_scalar_track(right, at_s, duration_s=duration_s, loop=loop)
        worst = max(worst, abs(a - b))
    return worst


def _tracks_equivalent(
    left: ScalarTrack,
    right: ScalarTrack,
    *,
    duration_s: float,
    loop: bool,
    tolerance: float,
) -> bool:
    return _track_max_error(
        left, right, duration_s=duration_s, loop=loop
    ) <= tolerance


def _simplify_track(track: ScalarTrack, tolerance: float) -> ScalarTrack:
    """Drop keys that do not change the represented linear/hold curve."""

    keys = list(track.keys)
    if len(keys) <= 2:
        return track
    interpolation = _track_interpolation(track)
    changed = True
    while changed and len(keys) > 2:
        changed = False
        for index in range(1, len(keys) - 1):
            prev_key, key, next_key = keys[index - 1], keys[index], keys[index + 1]
            redundant = False
            if interpolation == "hold":
                redundant = abs(key.value - prev_key.value) <= tolerance
            else:
                span = next_key.at_s - prev_key.at_s
                if span > 1e-9:
                    u = (key.at_s - prev_key.at_s) / span
                    expected = prev_key.value + (next_key.value - prev_key.value) * u
                    redundant = abs(key.value - expected) <= tolerance
            if redundant:
                del keys[index]
                changed = True
                break
    return ScalarTrack(target=track.target, keys=tuple(keys))


def _candidate_visual_tracks(
    prepared: PreparedCharacterMotion,
    existing: ClipDefinition,
    exported: Sequence[Mapping[str, object]],
    *,
    duration_s: float,
    loop: bool,
    tolerance: float,
) -> tuple[tuple[ScalarTrack, ...], float]:
    supported_order = _supported_visual_targets(prepared)
    supported = set(supported_order)
    by_target: dict[str, ScalarTrack] = {}
    for raw_track in exported:
        track = _track_from_export(
            raw_track,
            clip_id=existing.id,
            duration_s=duration_s,
            supported_targets=supported,
            tolerance=tolerance,
        )
        if track.target in by_target:
            raise ValueError(f"clip {existing.id!r} exported duplicate track {track.target!r}")
        by_target[track.target] = track
    missing = [target for target in supported_order if target not in by_target]
    if missing:
        raise ValueError(
            f"clip {existing.id!r} export omitted generated visual tracks: {missing}"
        )

    replacements: dict[str, ScalarTrack | None] = {}
    worst = 0.0
    for target in supported_order:
        edited = by_target[target]
        current = effective_scalar_track(prepared.library, existing, target)
        error = _track_max_error(current, edited, duration_s=duration_s, loop=loop)
        worst = max(worst, error)
        if error <= tolerance:
            continue
        backbone = pose_backbone_track(prepared.library, existing, target)
        if _tracks_equivalent(
            edited,
            backbone,
            duration_s=duration_s,
            loop=loop,
            tolerance=tolerance,
        ):
            replacements[target] = None
        else:
            replacements[target] = _simplify_track(edited, tolerance)

    output: list[ScalarTrack] = []
    emitted: set[str] = set()
    for track in existing.tracks:
        if track.target not in supported:
            output.append(track)
            continue
        if track.target in replacements:
            replacement = replacements[track.target]
            if replacement is not None:
                output.append(replacement)
            emitted.add(track.target)
        else:
            output.append(track)
            emitted.add(track.target)
    for target in supported_order:
        if target in emitted or target not in replacements:
            continue
        replacement = replacements[target]
        if replacement is not None:
            output.append(replacement)
    return tuple(output), worst


def apply_clip_export(
    export_path: Path,
    *,
    repo: Path,
    binding_path: Path | None = None,
    check_only: bool = False,
    tolerance: float = 1e-4,
) -> tuple[int, float]:
    """Apply ordinary Godot property-track edits to Ambition clip source.

    Pose keys remain the semantic whole-body backbone.  Edited Godot transform
    curves become independent scalar tracks, so property keys may be inserted,
    deleted, or retimed without manufacturing synchronized whole-body columns.
    """

    raw = load_clip_export(export_path)
    if binding_path is None:
        embedded = str(raw.get("binding_path") or "")
        if not embedded:
            raise ValueError(f"{export_path}: export does not name its Ambition binding")
        binding_path = repo / embedded
    binding = CharacterMotionBinding.load(binding_path)
    prepared = binding.load_prepared()
    if raw.get("character") != binding.character:
        raise ValueError(
            f"{export_path}: character {raw.get('character')!r} does not match binding {binding.character!r}"
        )

    changed = 0
    worst = 0.0
    seen: set[str] = set()
    for item in raw["clips"]:  # type: ignore[index]
        if not isinstance(item, Mapping):
            raise ValueError(f"{export_path}: clip export entry is not an object")
        clip_id = str(item.get("id") or "")
        if not clip_id or clip_id in seen:
            raise ValueError(f"{export_path}: missing or duplicate clip id {clip_id!r}")
        seen.add(clip_id)
        existing = prepared.library.clips.get(clip_id)
        if existing is None:
            raise ValueError(f"{export_path}: unknown clip {clip_id!r}")
        _validate_editor_clip(prepared, existing)

        duration_raw = float(item.get("duration_s", math.nan))
        if not math.isfinite(duration_raw) or duration_raw <= 0.0:
            raise ValueError(f"{export_path}: clip {clip_id!r} has invalid duration {duration_raw}")
        duration = (
            existing.duration_s
            if abs(duration_raw - existing.duration_s) <= tolerance
            else _round(duration_raw)
        )
        loop = bool(item.get("loop", False))
        if any(key.at_s > duration + tolerance for key in existing.pose_keys):
            raise ValueError(
                f"{export_path}: clip {clip_id!r} duration {duration} would truncate a semantic pose anchor"
            )
        for source_track in existing.tracks:
            if any(key.at_s > duration + tolerance for key in source_track.keys):
                raise ValueError(
                    f"{export_path}: clip {clip_id!r} duration {duration} would truncate source track {source_track.target!r}"
                )

        tracks_raw = item.get("tracks")
        if not isinstance(tracks_raw, list):
            raise ValueError(f"{export_path}: clip {clip_id!r} lacks exported property tracks")
        typed_tracks: list[Mapping[str, object]] = []
        for entry in tracks_raw:
            if not isinstance(entry, Mapping):
                raise ValueError(f"{export_path}: clip {clip_id!r} contains a non-object track")
            typed_tracks.append(entry)
        tracks, track_error = _candidate_visual_tracks(
            prepared,
            existing,
            typed_tracks,
            duration_s=duration,
            loop=loop,
            tolerance=tolerance,
        )
        worst = max(
            worst,
            track_error,
            abs(duration_raw - existing.duration_s),
            1.0 if loop != existing.loop else 0.0,
        )
        candidate = replace(
            existing,
            loop=loop,
            duration_s=duration,
            tracks=tracks,
        )
        if candidate.to_dict() == existing.to_dict():
            continue

        changed += 1
        if candidate.path is None:
            raise ValueError(f"clip {clip_id!r} has no source path")
        try:
            display_path = candidate.path.resolve().relative_to(repo.resolve())
        except ValueError:
            display_path = candidate.path
        if check_only:
            print(f"would update clip: {display_path}")
        else:
            candidate.path.write_text(
                json.dumps(candidate.to_dict(), indent=2) + "\n", encoding="utf8"
            )
            print(f"updated clip: {display_path}")

    if not seen:
        raise ValueError(f"{export_path}: export contains no clips")
    return changed, worst


def clip_sample_plan(
    binding_path: Path,
    clip_id: str,
    *,
    profile: SpriteBakeProfile = SpriteBakeProfile(),
    uniform_compatibility: bool = False,
) -> SpriteSamplePlan:
    """Plan sprite publication independently from authored animation keys."""

    binding = CharacterMotionBinding.load(binding_path)
    prepared = binding.load_prepared()
    if clip_id not in prepared.library.clips:
        choices = ", ".join(sorted(prepared.library.clips))
        raise ValueError(f"unknown clip {clip_id!r}; available clips: {choices}")
    planner = uniform_compatibility_plan if uniform_compatibility else adaptive_sample_plan
    return planner(prepared, clip_id, profile)


def render_clip_preview(
    binding_path: Path,
    clip_id: str,
    *,
    output: Path,
    strip_output: Path | None = None,
    profile: SpriteBakeProfile = SpriteBakeProfile(),
    legacy_sampling: bool = False,
) -> tuple[Path, Path | None]:
    """Render a clip from continuous motion using an independent sprite plan.

    The default is the non-uniform adaptive plan.  ``legacy_sampling`` exists
    only as a comparison aid while the shipped sheet format still carries its
    historical uniform sampling fields.
    """

    binding = CharacterMotionBinding.load(binding_path)
    prepared = binding.load_prepared()
    try:
        clip = prepared.library.clips[clip_id]
    except KeyError as exc:
        choices = ", ".join(sorted(prepared.library.clips))
        raise ValueError(f"unknown clip {clip_id!r}; available clips: {choices}") from exc
    doc = prepared.to_rig_document()
    if legacy_sampling:
        sample_times = tuple(
            index * clip.frame_duration_ms / 1000.0
            for index in range(clip.frame_count)
        )
        durations = tuple(
            clip.frame_duration_ms / 1000.0 for _ in range(clip.frame_count)
        )
    else:
        plan = adaptive_sample_plan(prepared, clip_id, profile)
        sample_times = plan.sample_times
        durations = tuple(sample.duration_s for sample in plan.samples)

    frames = [
        doc.render_at(clip_id, round(at_s / max(clip.duration_s, 1e-9), 9))
        for at_s in sample_times
    ]
    if not frames:
        raise ValueError(f"clip {clip_id!r} rendered no frames")
    output.parent.mkdir(parents=True, exist_ok=True)
    gif_durations = [max(1, int(round(duration * 1000.0))) for duration in durations]
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=gif_durations,
        loop=0,
        disposal=2,
    )

    if strip_output is not None:
        strip_output.parent.mkdir(parents=True, exist_ok=True)
        width = sum(frame.width for frame in frames)
        height = max(frame.height for frame in frames)
        strip = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        x = 0
        for frame in frames:
            strip.alpha_composite(frame.convert("RGBA"), (x, 0))
            x += frame.width
        strip.save(strip_output)
    return output, strip_output

