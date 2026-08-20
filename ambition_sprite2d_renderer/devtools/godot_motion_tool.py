"""Generate and round-trip the minimal Godot pose-authoring frontend.

Godot is deliberately downstream of Ambition's SVG rig metadata + motion JSON.
This tool prepares disposable `.tscn` pose sheets and preview textures, then
normalizes Godot's edited Bone2D transforms back into the authoritative pose
files through the Python motion IR.

The generated project uses only stable Godot 4.6 scene primitives:
Skeleton2D/Bone2D, Sprite2D, Label, Node2D, and a small EditorPlugin export
bridge.  No Godot resource is required by ordinary sprite regeneration.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from typing import Iterable, Mapping, Sequence

from PIL import Image

from ambition_sprite2d_renderer.authoring.motion_ir import (
    CharacterMotionBinding,
    PoseDefinition,
    PoseState,
    PreparedCharacterMotion,
    Transform2D,
    svg_reference_space,
)
from ambition_sprite2d_renderer.authoring.svg_parts import rasterize_subset

GODOT_EXPORT_SCHEMA = "ambition-godot-pose-export-v1"
GODOT_SHEET_SCHEMA = "ambition-godot-pose-sheet-v1"
DEFAULT_PROJECT_REL = Path("godot/pose_editor")
GODOT_VERSION_REL = DEFAULT_PROJECT_REL / "GODOT_VERSION"
DEFAULT_BINDINGS = (
    Path("ambition_sprite2d_renderer/data/characters/fighting_polygon_sword/fighting_polygon_sword.motion.json"),
    Path("ambition_sprite2d_renderer/data/characters/fighting_polygon_brawler/fighting_polygon_brawler.motion.json"),
)

_EPS = 1e-7
_PHASE_ORDER = {
    "idle": 0,
    "crouch": 1,
    "anticipation": 10,
    "startup": 11,
    "extension": 20,
    "contact": 30,
    "hold": 40,
    "release": 50,
    "follow_through": 60,
    "recovery": 70,
}
_ACTION_ORDER = {
    "basics": 0,
    "jab": 10,
    "ftilt": 20,
    "grab": 30,
    "pummel": 40,
    "throw_forward": 50,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _round(value: float, digits: int = 6) -> float:
    value = round(float(value), digits)
    return 0.0 if abs(value) < 0.5 * 10 ** (-digits) else value


def _rotate(point: tuple[float, float], degrees: float) -> tuple[float, float]:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def _godot_string(value: str) -> str:
    # Godot's quoted-string escape grammar accepts JSON's common escapes.
    return json.dumps(value, ensure_ascii=False)


def _godot_float(value: float) -> str:
    value = _round(value, 9)
    if value == 0.0:
        return "0.0"
    text = f"{value:.9f}".rstrip("0").rstrip(".")
    return text if "." in text else text + ".0"


def _vec2(value: tuple[float, float]) -> str:
    return f"Vector2({_godot_float(value[0])}, {_godot_float(value[1])})"


def _transform2d(transform: Transform2D) -> str:
    angle = math.radians(transform.rotation_deg)
    sx, sy = transform.scale
    c, s = math.cos(angle), math.sin(angle)
    # Godot Transform2D stores its X and Y basis columns followed by origin.
    xx, xy = c * sx, s * sx
    yx, yy = -s * sy, c * sy
    x, y = transform.position
    return (
        "Transform2D("
        f"{_godot_float(xx)}, {_godot_float(xy)}, "
        f"{_godot_float(yx)}, {_godot_float(yy)}, "
        f"{_godot_float(x)}, {_godot_float(y)})"
    )


def _node_name(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not clean:
        clean = "Pose"
    if clean[0].isdigit():
        clean = "Pose_" + clean
    return clean


def _repo_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


@dataclass(frozen=True)
class PartTexture:
    part_id: str
    path: Path
    res_path: str
    offset_px: tuple[int, int]
    size_px: tuple[int, int]
    pivot_in_crop_px: tuple[float, float]
    reference_px_per_user: float
    local_position: tuple[float, float]
    local_rotation_deg: float
    local_scale: tuple[float, float]
    z: int


@dataclass(frozen=True)
class RigPreviewBounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


def _render_part_textures(
    prepared: PreparedCharacterMotion,
    *,
    project_dir: Path,
    dpi: float = 96.0,
) -> tuple[dict[str, PartTexture], RigPreviewBounds]:
    rig = prepared.rig
    character = prepared.binding.character
    texture_dir = project_dir / "generated" / "textures" / character
    texture_dir.mkdir(parents=True, exist_ok=True)
    reference = svg_reference_space(rig.source_svg, dpi=dpi)
    ppu = reference.reference_px_per_user_x
    if not math.isclose(ppu, reference.reference_px_per_user_y, rel_tol=1e-7, abs_tol=1e-9):
        raise ValueError("Godot rigid preview requires a uniform SVG viewport scale")

    records: dict[str, PartTexture] = {}
    bounds: list[tuple[float, float, float, float]] = []
    vx, vy, _vw, _vh = reference.viewbox
    for part in rig.parts:
        image, offset, _legacy_ppu = rasterize_subset(
            rig.source_svg,
            rig.source_label,
            list(part.elements),
            dpi,
        )
        if image is None:
            raise ValueError(
                f"{rig.source_svg}: Godot preview part {part.id!r} rendered empty"
            )
        filename = f"{_node_name(part.id).lower()}.png"
        output = texture_dir / filename
        image.save(output)
        pivot_ref = reference.user_to_reference(part.pivot)
        pivot_crop = (pivot_ref[0] - offset[0], pivot_ref[1] - offset[1])
        pivot_user = (pivot_crop[0] / ppu, pivot_crop[1] / ppu)
        local_position = _rotate((-pivot_user[0], -pivot_user[1]), -part.bind_world_rotation_deg)
        scale = (1.0 / ppu, 1.0 / ppu)
        res_path = "res://" + output.relative_to(project_dir).as_posix()
        records[part.id] = PartTexture(
            part_id=part.id,
            path=output,
            res_path=res_path,
            offset_px=(int(offset[0]), int(offset[1])),
            size_px=image.size,
            pivot_in_crop_px=pivot_crop,
            reference_px_per_user=ppu,
            local_position=(_round(local_position[0]), _round(local_position[1])),
            local_rotation_deg=_round(-part.bind_world_rotation_deg),
            local_scale=(_round(scale[0], 9), _round(scale[1], 9)),
            z=int(round(part.z)),
        )
        x0 = vx + offset[0] / ppu - rig.root_anchor[0]
        y0 = vy + offset[1] / ppu - rig.root_anchor[1]
        x1 = x0 + image.width / ppu
        y1 = y0 + image.height / ppu
        bounds.append((x0, y0, x1, y1))

    if not bounds:
        raise ValueError(f"{rig.source_svg}: rig has no previewable parts")
    return records, RigPreviewBounds(
        min(v[0] for v in bounds),
        min(v[1] for v in bounds),
        max(v[2] for v in bounds),
        max(v[3] for v in bounds),
    )


def _pose_rows(prepared: PreparedCharacterMotion) -> list[list[PoseDefinition]]:
    poses = list(prepared.library.poses.values())
    prefix = "humanoid/fighting_polygon/"
    grouped: dict[str, list[PoseDefinition]] = {}
    for pose in poses:
        tail = pose.id[len(prefix) :] if pose.id.startswith(prefix) else pose.id
        bits = tail.split("/")
        group = bits[0] if len(bits) > 1 else "basics"
        grouped.setdefault(group, []).append(pose)

    def group_key(name: str) -> tuple[int, str]:
        return (_ACTION_ORDER.get(name, 1000), name)

    def pose_key(pose: PoseDefinition) -> tuple[int, str]:
        phase = pose.id.rsplit("/", 1)[-1]
        return (_PHASE_ORDER.get(phase, 1000), pose.id)

    return [sorted(grouped[name], key=pose_key) for name in sorted(grouped, key=group_key)]


def _actual_bone_transform(rest: Transform2D, delta: Transform2D) -> Transform2D:
    return Transform2D(
        position=(rest.position[0] + delta.position[0], rest.position[1] + delta.position[1]),
        rotation_deg=rest.rotation_deg + delta.rotation_deg,
        scale=(rest.scale[0] * delta.scale[0], rest.scale[1] * delta.scale[1]),
    )


def _bone_gizmo(prepared: PreparedCharacterMotion, bone_id: str) -> tuple[float, float]:
    bone = prepared.rig.bone_by_id[bone_id]
    if bone.length > 1e-4:
        # The rest transform already points local +X toward the authored tip.
        return bone.length, 0.0
    for child in prepared.rig.bones:
        if child.parent != bone_id:
            continue
        x, y = child.rest.position
        length = math.hypot(x, y)
        if length > 1e-4:
            return length, math.degrees(math.atan2(y, x))
    # A terminal organizational bone still needs a usable editor handle. This
    # affects only Bone2D's gizmo; it is not part of Ambition rest geometry.
    return 36.0, 0.0


def _editor_state_for_export(state: PoseState, bone_ids: Iterable[str]) -> dict[str, object]:
    # Generated expected exports intentionally contain complete editor-facing
    # transforms. apply-export runs them through PoseState.to_dict(), which is
    # the canonical sparse/rounded serialization boundary.
    return {
        "root": {
            "position": [_round(v) for v in state.root.position],
            "rotation_deg": _round(state.root.rotation_deg),
            "scale": [_round(v) for v in state.root.scale],
        },
        "bones": {
            bone_id: {
                "position": [_round(v) for v in state.bones.get(bone_id, Transform2D()).position],
                "rotation_deg": _round(state.bones.get(bone_id, Transform2D()).rotation_deg),
                "scale": [_round(v) for v in state.bones.get(bone_id, Transform2D()).scale],
            }
            for bone_id in sorted(bone_ids)
        },
        "parameters": {name: _round(value) for name, value in sorted(state.parameters.items())},
    }


def _write_pose_sheet(
    prepared: PreparedCharacterMotion,
    textures: Mapping[str, PartTexture],
    bounds: RigPreviewBounds,
    *,
    project_dir: Path,
    repo: Path,
) -> Path:
    character = prepared.binding.character
    output = project_dir / "generated" / f"{character}_pose_sheet.tscn"
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

    root_name = _node_name(character) + "PoseSheet"
    binding_path = _repo_relative(prepared.binding.path, repo)
    lines.extend(
        [
            f'[node name={_godot_string(root_name)} type="Node2D"]',
            f'metadata/ambition_schema = {_godot_string(GODOT_SHEET_SCHEMA)}',
            f'metadata/ambition_character = {_godot_string(character)}',
            f'metadata/ambition_binding_path = {_godot_string(binding_path)}',
            f'metadata/ambition_rig_profile = {_godot_string(prepared.rig.profile)}',
            "",
        ]
    )

    margin = 48.0
    label_height = 42.0
    tile_width = max(260.0, bounds.width + margin * 2.0)
    tile_height = max(340.0, bounds.height + label_height + margin * 2.0)
    rows = _pose_rows(prepared)
    bone_by_id = prepared.rig.bone_by_id

    for row_index, row in enumerate(rows):
        for column_index, pose in enumerate(row):
            cell_name = _node_name(pose.id.replace("humanoid/fighting_polygon/", ""))
            cell_path = cell_name
            layout_x = column_index * tile_width
            layout_y = row_index * tile_height
            label = pose.id.replace("humanoid/fighting_polygon/", "")
            state = pose.state
            parameters_json = json.dumps(dict(state.parameters), sort_keys=True, separators=(",", ":"))
            lines.extend(
                [
                    f'[node name={_godot_string(cell_name)} type="Node2D" parent="."]',
                    f'position = {_vec2((layout_x, layout_y))}',
                    f'metadata/ambition_pose_id = {_godot_string(pose.id)}',
                    f'metadata/ambition_parameters_json = {_godot_string(parameters_json)}',
                    "",
                    f'[node name="PoseLabel" type="Label" parent={_godot_string(cell_path)}]',
                    f'offset_left = {_godot_float(margin)}',
                    "offset_top = 8.0",
                    f'offset_right = {_godot_float(tile_width - margin)}',
                    "offset_bottom = 38.0",
                    f'text = {_godot_string(label)}',
                    "theme_override_font_sizes/font_size = 22",
                    "",
                    f'[node name="LayoutAnchor" type="Node2D" parent={_godot_string(cell_path)}]',
                    f'position = {_vec2((margin - bounds.min_x, label_height + margin - bounds.min_y))}',
                    "metadata/_edit_lock_ = true",
                    "",
                    f'[node name="RigRoot" type="Node2D" parent={_godot_string(cell_path + "/LayoutAnchor")}]',
                    f'position = {_vec2(state.root.position)}',
                    f'rotation = {_godot_float(math.radians(state.root.rotation_deg))}',
                    f'scale = {_vec2(state.root.scale)}',
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
                gizmo_length, gizmo_angle_deg = _bone_gizmo(prepared, bone.id)
                lines.extend(
                    [
                        f'[node name={_godot_string(bone.id)} type="Bone2D" parent={_godot_string(parent_path)}]',
                        f'position = {_vec2(actual.position)}',
                        f'rotation = {_godot_float(math.radians(actual.rotation_deg))}',
                        f'scale = {_vec2(actual.scale)}',
                        f'rest = {_transform2d(bone.rest)}',
                        "autocalculate_length_and_angle = false",
                        f'length = {_godot_float(gizmo_length)}',
                        f'bone_angle = {_godot_float(math.radians(gizmo_angle_deg))}',
                        f'metadata/ambition_bone_id = {_godot_string(bone.id)}',
                        f'metadata/ambition_source_rotation_delta_deg = {_godot_float(delta.rotation_deg)}',
                        "",
                    ]
                )

            for part in prepared.rig.parts:
                texture = textures[part.id]
                parent_path = node_path_by_bone[part.bone]
                sprite_name = "Art_" + _node_name(part.id)
                visible = True
                if part.opacity_parameter:
                    visible = state.parameters.get(part.opacity_parameter, 0.0) > 0.01
                lines.extend(
                    [
                        f'[node name={_godot_string(sprite_name)} type="Sprite2D" parent={_godot_string(parent_path)}]',
                        f'texture = ExtResource({_godot_string(texture_ids[part.id])})',
                        "centered = false",
                        f'position = {_vec2(texture.local_position)}',
                        f'rotation = {_godot_float(math.radians(texture.local_rotation_deg))}',
                        f'scale = {_vec2(texture.local_scale)}',
                        f'z_index = {texture.z}',
                        f'visible = {str(visible).lower()}',
                        "metadata/_edit_lock_ = true",
                        "",
                    ]
                )

    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf8")
    return output


def _write_expected_export(
    prepared: PreparedCharacterMotion,
    *,
    project_dir: Path,
    repo: Path,
    scene_path: Path,
) -> Path:
    output = project_dir / "generated" / "expected_exports" / f"{prepared.binding.character}.poses.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": GODOT_EXPORT_SCHEMA,
        "character": prepared.binding.character,
        "binding_path": _repo_relative(prepared.binding.path, repo),
        "source_scene": "res://" + scene_path.relative_to(project_dir).as_posix(),
        "poses": [
            {"id": pose.id, "state": _editor_state_for_export(pose.state, prepared.rig.bone_by_id)}
            for pose in sorted(prepared.library.poses.values(), key=lambda item: item.id)
        ],
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")
    return output


def _write_workspace_manifest(
    prepared: PreparedCharacterMotion,
    textures: Mapping[str, PartTexture],
    bounds: RigPreviewBounds,
    *,
    project_dir: Path,
    repo: Path,
    scene_path: Path,
) -> Path:
    output = project_dir / "generated" / "manifests" / f"{prepared.binding.character}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "ambition-godot-workspace-v1",
        "character": prepared.binding.character,
        "binding_path": _repo_relative(prepared.binding.path, repo),
        "source_svg": _repo_relative(prepared.rig.source_svg, repo),
        "rig_view": prepared.rig.view_id,
        "rig_profile": prepared.rig.profile,
        "scene": "res://" + scene_path.relative_to(project_dir).as_posix(),
        "bounds_from_rig_root": [
            _round(bounds.min_x),
            _round(bounds.min_y),
            _round(bounds.max_x),
            _round(bounds.max_y),
        ],
        "parts": {
            part_id: {
                "texture": record.res_path,
                "offset_px": list(record.offset_px),
                "size_px": list(record.size_px),
                "pivot_in_crop_px": [_round(v) for v in record.pivot_in_crop_px],
                "reference_px_per_rig_unit": _round(record.reference_px_per_user, 9),
            }
            for part_id, record in sorted(textures.items())
        },
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")
    return output


def prepare_binding(
    binding_path: Path,
    *,
    project_dir: Path,
    repo: Path,
    dpi: float = 96.0,
) -> dict[str, Path]:
    binding = CharacterMotionBinding.load(binding_path)
    prepared = binding.load_prepared()
    textures, bounds = _render_part_textures(prepared, project_dir=project_dir, dpi=dpi)
    scene = _write_pose_sheet(prepared, textures, bounds, project_dir=project_dir, repo=repo)
    expected = _write_expected_export(
        prepared, project_dir=project_dir, repo=repo, scene_path=scene
    )
    manifest = _write_workspace_manifest(
        prepared,
        textures,
        bounds,
        project_dir=project_dir,
        repo=repo,
        scene_path=scene,
    )
    return {"scene": scene, "expected_export": expected, "manifest": manifest}


def prepare_workspace(
    binding_paths: Iterable[Path],
    *,
    project_dir: Path,
    repo: Path,
    clean: bool = True,
) -> list[dict[str, Path]]:
    generated = project_dir / "generated"
    if clean and generated.exists():
        shutil.rmtree(generated)
    generated.mkdir(parents=True, exist_ok=True)
    return [
        prepare_binding(path, project_dir=project_dir, repo=repo)
        for path in binding_paths
    ]


def _pose_definition_from_export(existing: PoseDefinition, raw_state: Mapping[str, object]) -> PoseDefinition:
    state = PoseState.from_dict(raw_state)
    return PoseDefinition(
        id=existing.id,
        state=state,
        rig_profile=existing.rig_profile,
        source=existing.source,
        path=existing.path,
    )


def _state_max_error(a: PoseState, b: PoseState) -> float:
    values: list[float] = []

    def compare_transform(left: Transform2D, right: Transform2D) -> None:
        values.extend(abs(x - y) for x, y in zip(left.position, right.position))
        # Static pose rotations are equivalent modulo 360. Compare the nearest
        # winding while the generated scene's source hint preserves unchanged
        # authored winding where Godot itself normalizes an angle.
        delta = left.rotation_deg - right.rotation_deg
        delta = (delta + 180.0) % 360.0 - 180.0
        values.append(abs(delta))
        values.extend(abs(x - y) for x, y in zip(left.scale, right.scale))

    compare_transform(a.root, b.root)
    for name in set(a.bones) | set(b.bones):
        compare_transform(a.bones.get(name, Transform2D()), b.bones.get(name, Transform2D()))
    for name in set(a.parameters) | set(b.parameters):
        values.append(abs(a.parameters.get(name, 0.0) - b.parameters.get(name, 0.0)))
    return max(values, default=0.0)


def load_export(path: Path) -> Mapping[str, object]:
    raw = json.loads(path.read_text(encoding="utf8"))
    if raw.get("schema") != GODOT_EXPORT_SCHEMA:
        raise ValueError(f"{path}: expected schema {GODOT_EXPORT_SCHEMA!r}")
    if not isinstance(raw.get("poses"), list):
        raise ValueError(f"{path}: export lacks a pose list")
    return raw


def _validate_export_state(state: PoseState, *, pose_id: str, bone_ids: set[str]) -> None:
    unknown = sorted(set(state.bones) - bone_ids)
    if unknown:
        raise ValueError(f"pose {pose_id!r} references unknown bones {unknown}")
    for label, transform in [("root", state.root), *sorted(state.bones.items())]:
        values = [*transform.position, transform.rotation_deg, *transform.scale]
        if any(not math.isfinite(float(value)) for value in values):
            raise ValueError(f"pose {pose_id!r} {label!r} contains non-finite transform values")
        if transform.scale[0] <= 0.0 or transform.scale[1] <= 0.0:
            raise ValueError(f"pose {pose_id!r} {label!r} has non-positive scale")
        if any(abs(value - 1.0) > _EPS for value in transform.scale):
            raise ValueError(
                f"pose {pose_id!r} {label!r} uses scale {transform.scale}; "
                "the Godot pilot currently permits translation/rotation only so the "
                "existing renderer projection remains lossless"
            )
    if abs(state.root.rotation_deg) > _EPS:
        raise ValueError(
            f"pose {pose_id!r} root rotation is not supported by the current renderer projection"
        )
    for name, value in state.parameters.items():
        if not math.isfinite(float(value)):
            raise ValueError(f"pose {pose_id!r} parameter {name!r} is non-finite")


def apply_export(
    export_path: Path,
    *,
    repo: Path,
    binding_path: Path | None = None,
    check_only: bool = False,
    tolerance: float = 1e-4,
) -> tuple[int, float]:
    raw = load_export(export_path)
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
    for item in raw["poses"]:  # type: ignore[index]
        if not isinstance(item, Mapping):
            raise ValueError(f"{export_path}: pose export entry is not an object")
        pose_id = str(item.get("id") or "")
        if not pose_id or pose_id in seen:
            raise ValueError(f"{export_path}: missing or duplicate pose id {pose_id!r}")
        seen.add(pose_id)
        existing = prepared.library.poses.get(pose_id)
        if existing is None:
            raise ValueError(f"{export_path}: unknown pose {pose_id!r}")
        state_raw = item.get("state")
        if not isinstance(state_raw, Mapping):
            raise ValueError(f"{export_path}: pose {pose_id!r} lacks state")
        candidate = _pose_definition_from_export(existing, state_raw)
        errors = prepared.library.validate(prepared.rig)
        _validate_export_state(
            candidate.state,
            pose_id=pose_id,
            bone_ids=set(prepared.rig.bone_by_id),
        )
        if errors:
            raise ValueError(f"{binding.path}: existing motion library is invalid: {'; '.join(errors)}")
        error = _state_max_error(existing.state, candidate.state)
        worst = max(worst, error)
        if error > tolerance:
            changed += 1
        if not check_only:
            if candidate.path is None:
                raise ValueError(f"pose {pose_id!r} has no source path")
            candidate.path.write_text(json.dumps(candidate.to_dict(), indent=2) + "\n", encoding="utf8")

    missing = sorted(set(prepared.library.poses) - seen)
    if missing:
        raise ValueError(f"{export_path}: export omitted poses {missing}")
    return changed, worst


def _pinned_godot_version(repo: Path) -> str:
    version_path = repo / GODOT_VERSION_REL
    version = version_path.read_text(encoding="utf8").strip()
    if not version:
        raise ValueError(f"empty Godot version pin: {version_path}")
    return version


def _reports_godot_version(path: Path, version: str) -> bool:
    try:
        result = subprocess.run(
            [str(path), "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.stdout.strip().startswith(version + ".")


def _find_godot(explicit: str | None, repo: Path) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.exists() else None

    version = _pinned_godot_version(repo)
    local = sorted((repo / "tpl").glob(f"Godot_v{version}-stable_linux.*"))
    if local:
        return local[0]

    for name in ("godot4", "godot"):
        found = shutil.which(name)
        if found:
            path = Path(found)
            if _reports_godot_version(path, version):
                return path
    return None


def _missing_godot_message(repo: Path) -> str:
    version = _pinned_godot_version(repo)
    return (
        f"Godot executable not found; run ./scripts/install_godot.py to install the pinned "
        f"Godot {version} editor under tpl/, put godot/godot4 on PATH, or pass --godot"
    )


def _binding_paths(raw: Sequence[str], repo: Path) -> list[Path]:
    paths = [Path(value) for value in raw] if raw else list(DEFAULT_BINDINGS)
    return [(path if path.is_absolute() else repo / path).resolve() for path in paths]


def _cmd_prepare(args: argparse.Namespace) -> int:
    repo = repo_root()
    project_dir = (repo / args.project).resolve()
    outputs = prepare_workspace(
        _binding_paths(args.bindings, repo),
        project_dir=project_dir,
        repo=repo,
        clean=not args.keep_generated,
    )
    for item in outputs:
        print(item["scene"].relative_to(repo))
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    repo = repo_root()
    binding = None
    if args.binding:
        candidate = Path(args.binding).expanduser()
        binding = (candidate if candidate.is_absolute() else repo / candidate).resolve()
    export = Path(args.export).expanduser()
    export = (export if export.is_absolute() else Path.cwd() / export).resolve()
    changed, worst = apply_export(
        export,
        repo=repo,
        binding_path=binding,
        check_only=args.check,
        tolerance=args.tolerance,
    )
    verb = "would change" if args.check else "updated"
    print(f"{verb} {changed} pose(s); worst source delta={worst:.6g}")
    return 0


def _cmd_open(args: argparse.Namespace) -> int:
    repo = repo_root()
    project_dir = (repo / args.project).resolve()
    outputs = prepare_workspace(
        _binding_paths(args.bindings, repo),
        project_dir=project_dir,
        repo=repo,
        clean=True,
    )
    godot = _find_godot(args.godot, repo)
    if godot is None:
        raise SystemExit(_missing_godot_message(repo))
    scene = outputs[0]["scene"]
    command = [str(godot), "--editor", "--path", str(project_dir), str(scene)]
    return subprocess.call(command, cwd=repo)


def _cmd_headless_check(args: argparse.Namespace) -> int:
    repo = repo_root()
    project_dir = (repo / args.project).resolve()
    outputs = prepare_workspace(
        _binding_paths(args.bindings, repo),
        project_dir=project_dir,
        repo=repo,
        clean=True,
    )
    godot = _find_godot(args.godot, repo)
    if godot is None:
        raise SystemExit(_missing_godot_message(repo))
    for item in outputs:
        scene = item["scene"]
        out = project_dir / "generated" / "exports" / (scene.stem.replace("_pose_sheet", "") + ".poses.json")
        command = [
            str(godot),
            "--headless",
            "--path",
            str(project_dir),
            "--script",
            "res://scripts/headless_export.gd",
            "--",
            "--scene",
            "res://" + scene.relative_to(project_dir).as_posix(),
            "--output",
            "res://" + out.relative_to(project_dir).as_posix(),
        ]
        subprocess.run(command, cwd=repo, check=True)
        changed, worst = apply_export(out, repo=repo, check_only=True)
        if changed:
            raise SystemExit(
                f"Godot round-trip drifted {changed} pose(s) for {scene.name}; worst delta={worst}"
            )
        print(f"{scene.name}: round-trip OK; worst delta={worst:.6g}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="generate disposable Godot pose sheets and preview textures")
    prepare.add_argument("bindings", nargs="*", help="motion binding JSON paths; defaults to both Fighting Polygons")
    prepare.add_argument("--project", default=str(DEFAULT_PROJECT_REL))
    prepare.add_argument("--keep-generated", action="store_true", help="do not clear the generated workspace first")
    prepare.set_defaults(func=_cmd_prepare)

    apply = sub.add_parser("apply-export", help="validate and normalize a Godot pose export into pose JSON")
    apply.add_argument("export")
    apply.add_argument("--binding", help="override the binding embedded in the export bundle")
    apply.add_argument("--check", action="store_true", help="compare only; do not modify source pose files")
    apply.add_argument("--tolerance", type=float, default=1e-4)
    apply.set_defaults(func=_cmd_apply)

    open_cmd = sub.add_parser("open", help="prepare the pilot and open the first pose sheet in Godot")
    open_cmd.add_argument("bindings", nargs="*")
    open_cmd.add_argument("--project", default=str(DEFAULT_PROJECT_REL))
    open_cmd.add_argument("--godot", help="Godot executable; defaults to PATH or the repo-local pinned install")
    open_cmd.set_defaults(func=_cmd_open)

    check = sub.add_parser("headless-check", help="prepare and verify a Godot scene -> export -> IR round trip")
    check.add_argument("bindings", nargs="*")
    check.add_argument("--project", default=str(DEFAULT_PROJECT_REL))
    check.add_argument("--godot", help="Godot executable; defaults to PATH or the repo-local pinned install")
    check.set_defaults(func=_cmd_headless_check)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
