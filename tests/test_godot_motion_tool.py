import json
from pathlib import Path
import shutil
import subprocess

import pytest

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.devtools.godot_motion_tool import (
    DEFAULT_BINDINGS,
    GODOT_SHEET_SCHEMA,
    _render_part_textures,
    _rotate,
    apply_export,
    prepare_binding,
    repo_root,
)


def _binding(index=0):
    return CharacterMotionBinding.load(repo_root() / DEFAULT_BINDINGS[index])


def test_prepare_generates_literal_pose_sheet_from_neutral_ir(tmp_path):
    repo = repo_root()
    project = tmp_path / "godot_project"
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    prepared = _binding().load_prepared()
    scene = output["scene"].read_text(encoding="utf8")

    assert f'metadata/ambition_schema = "{GODOT_SHEET_SCHEMA}"' in scene
    assert scene.count('metadata/ambition_pose_id = ') == len(prepared.library.poses)
    assert scene.count('type="Bone2D"') == len(prepared.library.poses) * len(prepared.rig.bones)
    assert scene.count('type="Sprite2D"') == len(prepared.library.poses) * len(prepared.rig.parts)
    assert "rest = Transform2D(" in scene
    assert "autocalculate_length_and_angle = false" in scene
    assert "AnimationPlayer" not in scene
    assert "RigDocument" not in scene


def test_generated_art_bind_transform_places_source_pivot_on_bone_origin(tmp_path):
    prepared = _binding().load_prepared()
    textures, _bounds = _render_part_textures(prepared, project_dir=tmp_path)
    for record in textures.values():
        scaled_pivot = (
            record.pivot_in_crop_px[0] * record.local_scale[0],
            record.pivot_in_crop_px[1] * record.local_scale[1],
        )
        rotated = _rotate(scaled_pivot, record.local_rotation_deg)
        landed = (rotated[0] + record.local_position[0], rotated[1] + record.local_position[1])
        assert landed == pytest.approx((0.0, 0.0), abs=2e-6)


def test_expected_generated_export_round_trips_without_source_drift(tmp_path):
    repo = repo_root()
    project = tmp_path / "godot_project"
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    changed, worst = apply_export(output["expected_export"], repo=repo, check_only=True)
    assert changed == 0
    assert worst <= 2e-6


def test_export_comparison_detects_a_real_pose_edit(tmp_path):
    repo = repo_root()
    project = tmp_path / "godot_project"
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    raw = json.loads(output["expected_export"].read_text(encoding="utf8"))
    contact = next(item for item in raw["poses"] if item["id"].endswith("jab/contact"))
    contact["state"]["bones"]["near_arm_u"]["rotation_deg"] += 5.0
    edited = tmp_path / "edited.json"
    edited.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")

    changed, worst = apply_export(edited, repo=repo, check_only=True)
    assert changed == 1
    assert worst == pytest.approx(5.0)



def test_apply_export_rejects_scale_that_renderer_projection_cannot_preserve(tmp_path):
    repo = repo_root()
    project = tmp_path / "godot_project"
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    raw = json.loads(output["expected_export"].read_text(encoding="utf8"))
    contact = next(item for item in raw["poses"] if item["id"].endswith("jab/contact"))
    contact["state"]["bones"]["near_arm_u"]["scale"] = [1.1, 1.0]
    edited = tmp_path / "scaled.json"
    edited.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")

    with pytest.raises(ValueError, match="translation/rotation only"):
        apply_export(edited, repo=repo, check_only=True)


def test_apply_export_rejects_root_rotation_until_renderer_projection_supports_it(tmp_path):
    repo = repo_root()
    project = tmp_path / "godot_project"
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    raw = json.loads(output["expected_export"].read_text(encoding="utf8"))
    contact = next(item for item in raw["poses"] if item["id"].endswith("jab/contact"))
    contact["state"]["root"]["rotation_deg"] = 2.0
    edited = tmp_path / "root_rotated.json"
    edited.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")

    with pytest.raises(ValueError, match="root rotation"):
        apply_export(edited, repo=repo, check_only=True)

def test_committed_godot_project_is_a_small_replaceable_frontend():
    repo = repo_root()
    project = repo / "godot" / "pose_editor"
    config = (project / "project.godot").read_text(encoding="utf8")
    plugin = (project / "addons" / "ambition_pose_editor" / "plugin.gd").read_text(encoding="utf8")
    exporter = (project / "addons" / "ambition_pose_editor" / "pose_export.gd").read_text(encoding="utf8")

    assert 'config/features=PackedStringArray("4.6", "GL Compatibility")' in config
    assert 'res://addons/ambition_pose_editor/plugin.cfg' in config
    assert "add_tool_menu_item" in plugin
    assert "EditorInterface.get_edited_scene_root()" in plugin
    assert "Bone2D" in exporter
    assert ".rest" in exporter
    assert "RigDocument" not in exporter
    assert "FileAccess" in exporter


def test_godot_headless_can_parse_and_export_generated_scene_when_available(tmp_path):
    repo = repo_root()
    candidates = [shutil.which("godot4"), shutil.which("godot")]
    candidates += [str(path) for path in sorted((repo / "tpl").glob("Godot_v*-stable_linux.x86_64"))]
    godot = next((Path(value) for value in candidates if value and Path(value).exists()), None)
    if godot is None:
        pytest.skip("Godot 4.x executable not available in test environment")

    project = tmp_path / "pose_editor"
    shutil.copytree(repo / "godot" / "pose_editor", project, ignore=shutil.ignore_patterns("generated", ".godot"))
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    export = project / "generated" / "exports" / "headless.json"
    scene_res = "res://" + output["scene"].relative_to(project).as_posix()
    export_res = "res://" + export.relative_to(project).as_posix()
    subprocess.run(
        [
            str(godot),
            "--headless",
            "--path",
            str(project),
            "--script",
            "res://scripts/headless_export.gd",
            "--",
            "--scene",
            scene_res,
            "--output",
            export_res,
        ],
        check=True,
        timeout=60,
    )
    changed, worst = apply_export(export, repo=repo, check_only=True)
    assert changed == 0
    assert worst <= 1e-4
