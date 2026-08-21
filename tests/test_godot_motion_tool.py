import json
from pathlib import Path
import shutil
import subprocess

import pytest

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.devtools.godot_motion_tool import (
    DEFAULT_BINDINGS,
    GODOT_SHEET_SCHEMA,
    _bone_gizmo,
    _find_godot,
    _import_godot_resources,
    _render_part_textures,
    _rotate,
    apply_export,
    prepare_binding,
    render_pose_preview,
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
    assert "auto_calculate_length_and_angle = false" in scene
    first_bone = scene.index('type="Bone2D"')
    next_node = scene.find("\n[node ", first_bone + 1)
    first_bone_block = scene[first_bone:next_node]
    assert first_bone_block.index("auto_calculate_length_and_angle = false") < first_bone_block.index("rest = Transform2D(")
    # Bone2D's text-scene property is degrees; set_bone_angle() itself uses radians.
    first_bone_id = prepared.rig.bones[0].id
    _gizmo_length, gizmo_angle_deg = _bone_gizmo(prepared, first_bone_id)
    angle_line = next(line for line in first_bone_block.splitlines() if line.startswith("bone_angle = "))
    assert float(angle_line.split("=", 1)[1]) == pytest.approx(gizmo_angle_deg, abs=1e-9)
    assert "autocalculate_length_and_angle" not in scene
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


def test_generated_godot_resources_are_imported_before_headless_scene_load(monkeypatch, tmp_path):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    godot = Path("/opt/godot")
    project = tmp_path / "pose_editor"
    _import_godot_resources(godot, project, cwd=tmp_path)

    assert calls == [
        (
            [str(godot), "--headless", "--path", str(project), "--import"],
            {"cwd": tmp_path, "check": True},
        )
    ]


def test_pilot_ignores_editor_generated_script_uid_sidecars():
    ignored = (repo_root() / ".gitignore").read_text(encoding="utf8")
    assert "godot/pose_editor/**/*.gd.uid" in ignored


def test_godot_headless_can_parse_and_export_generated_scene_when_available(tmp_path):
    repo = repo_root()
    godot = _find_godot(None, repo)
    if godot is None:
        pytest.skip("pinned Godot executable not available in test environment")

    project = tmp_path / "pose_editor"
    shutil.copytree(repo / "godot" / "pose_editor", project, ignore=shutil.ignore_patterns("generated", ".godot"))
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    _import_godot_resources(godot, project, cwd=repo)
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


def _copy_fighting_polygon_sword_sources(tmp_path: Path) -> tuple[Path, Path]:
    source_repo = repo_root()
    temp_repo = tmp_path / "repo"
    character_rel = Path(
        "ambition_sprite2d_renderer/data/characters/fighting_polygon_sword"
    )
    library_rel = Path(
        "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1"
    )
    shutil.copytree(source_repo / character_rel, temp_repo / character_rel)
    shutil.copytree(source_repo / library_rel, temp_repo / library_rel)
    return temp_repo, temp_repo / character_rel / "fighting_polygon_sword.motion.json"


def test_apply_export_preserves_sub_tolerance_godot_noise(tmp_path):
    temp_repo, binding_path = _copy_fighting_polygon_sword_sources(tmp_path)
    project = tmp_path / "godot_project"
    output = prepare_binding(binding_path, project_dir=project, repo=temp_repo)
    raw = json.loads(output["expected_export"].read_text(encoding="utf8"))
    contact = next(item for item in raw["poses"] if item["id"].endswith("jab/contact"))
    contact["state"]["bones"]["near_arm_u"]["rotation_deg"] += 0.000006
    edited = tmp_path / "godot_noise.json"
    edited.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")

    pose_paths = sorted(
        (temp_repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/poses")
        .glob("*.pose.json")
    )
    before = {path: path.read_bytes() for path in pose_paths}
    changed, worst = apply_export(
        edited,
        repo=temp_repo,
        check_only=False,
        tolerance=1e-4,
    )

    assert changed == 0
    assert worst == pytest.approx(0.000006)
    assert {path: path.read_bytes() for path in pose_paths} == before


def test_apply_export_writes_only_meaningfully_edited_pose(tmp_path, capsys):
    temp_repo, binding_path = _copy_fighting_polygon_sword_sources(tmp_path)
    project = tmp_path / "godot_project"
    output = prepare_binding(binding_path, project_dir=project, repo=temp_repo)
    raw = json.loads(output["expected_export"].read_text(encoding="utf8"))
    contact = next(item for item in raw["poses"] if item["id"].endswith("jab/contact"))
    contact["state"]["bones"]["near_arm_u"]["rotation_deg"] += 12.0
    edited = tmp_path / "one_pose_edit.json"
    edited.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")

    pose_paths = sorted(
        (temp_repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/poses")
        .glob("*.pose.json")
    )
    contact_path = next(path for path in pose_paths if path.name.endswith("jab__contact.pose.json"))
    source_before = json.loads(contact_path.read_text(encoding="utf8"))
    source_angle_before = source_before["state"]["bones"]["near_arm_u"]["rotation_deg"]
    before = {path: path.read_bytes() for path in pose_paths}
    changed, worst = apply_export(edited, repo=temp_repo, check_only=False)
    changed_paths = [path for path in pose_paths if path.read_bytes() != before[path]]

    assert changed == 1
    assert worst == pytest.approx(12.0)
    assert len(changed_paths) == 1
    assert changed_paths[0].name == "humanoid__fighting_polygon__jab__contact.pose.json"
    source_after = json.loads(changed_paths[0].read_text(encoding="utf8"))
    # Godot edits the sword in its west-facing character-local frame.  The
    # shared source library remains east-facing, so write-back applies the
    # inverse reflection rather than contaminating the brawler's source data.
    assert source_after["state"]["bones"]["near_arm_u"]["rotation_deg"] == pytest.approx(
        source_angle_before - 12.0
    )
    output_text = capsys.readouterr().out
    assert "updated pose:" in output_text
    assert changed_paths[0].relative_to(temp_repo).as_posix() in output_text


def test_render_pose_preview_uses_production_renderer_seam(tmp_path):
    output = tmp_path / "jab_contact.png"
    rendered = render_pose_preview(
        _binding().path,
        "humanoid/fighting_polygon/jab/contact",
        output=output,
    )

    assert rendered == output
    assert output.exists()
    from PIL import Image

    with Image.open(output) as image:
        assert image.width > 0
        assert image.height > 0
        assert image.getbbox() is not None


def test_check_only_reports_pose_path_without_writing(tmp_path, capsys):
    temp_repo, binding_path = _copy_fighting_polygon_sword_sources(tmp_path)
    project = tmp_path / "godot_project"
    output = prepare_binding(binding_path, project_dir=project, repo=temp_repo)
    raw = json.loads(output["expected_export"].read_text(encoding="utf8"))
    contact = next(item for item in raw["poses"] if item["id"].endswith("jab/contact"))
    contact["state"]["bones"]["near_arm_u"]["rotation_deg"] += 8.0
    edited = tmp_path / "check_only.json"
    edited.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")

    target = (
        temp_repo
        / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/poses"
        / "humanoid__fighting_polygon__jab__contact.pose.json"
    )
    before = target.read_bytes()
    changed, _worst = apply_export(edited, repo=temp_repo, check_only=True)

    assert changed == 1
    assert target.read_bytes() == before
    output_text = capsys.readouterr().out
    assert "would update pose:" in output_text
    assert target.relative_to(temp_repo).as_posix() in output_text
