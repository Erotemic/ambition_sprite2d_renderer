import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image
import pytest

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.devtools.godot_clip_authoring import (
    DEFAULT_CLIP_PILOT,
    GODOT_CLIP_SHEET_SCHEMA,
    apply_clip_export,
    clip_sample_plan,
    render_clip_preview,
    _value_track_lines,
)
from ambition_sprite2d_renderer.devtools.godot_motion_tool import (
    DEFAULT_BINDINGS,
    _find_godot,
    _import_godot_resources,
    prepare_binding,
    repo_root,
)


def _binding() -> CharacterMotionBinding:
    return CharacterMotionBinding.load(repo_root() / DEFAULT_BINDINGS[0])


def _copy_fighting_polygon_sword_sources(tmp_path: Path) -> tuple[Path, Path]:
    source_repo = repo_root()
    temp_repo = tmp_path / "repo"
    character_rel = Path("ambition_sprite2d_renderer/data/characters/fighting_polygon_sword")
    library_rel = Path("ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1")
    shutil.copytree(source_repo / character_rel, temp_repo / character_rel)
    shutil.copytree(source_repo / library_rel, temp_repo / library_rel)
    return temp_repo, temp_repo / character_rel / "fighting_polygon_sword.motion.json"


def _expected_export(tmp_path: Path, *, isolated: bool = False):
    if isolated:
        repo, binding_path = _copy_fighting_polygon_sword_sources(tmp_path)
        binding = CharacterMotionBinding.load(binding_path)
    else:
        repo = repo_root()
        binding = _binding()
    project = tmp_path / "godot_project"
    output = prepare_binding(binding.path, project_dir=project, repo=repo)
    return repo, binding, output


def _write_export(tmp_path: Path, raw: dict, name: str = "edited.clips.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf8")
    return path


def _clip(raw: dict, clip_id: str) -> dict:
    return next(item for item in raw["clips"] if item["id"] == clip_id)


def _track(clip: dict, target: str) -> dict:
    return next(item for item in clip["tracks"] if item["target"] == target)


def _key_at(track: dict, at_s: float) -> dict:
    return next(key for key in track["keys"] if key["at_s"] == pytest.approx(at_s))


def test_generated_clip_sheet_uses_native_animation_player_tracks(tmp_path):
    _repo, binding, output = _expected_export(tmp_path)
    prepared = binding.load_prepared()
    scene = output["clip_scene"].read_text(encoding="utf8")

    assert f'metadata/ambition_schema = "{GODOT_CLIP_SHEET_SCHEMA}"' in scene
    assert scene.count('type="AnimationPlayer"') == len(DEFAULT_CLIP_PILOT)
    assert scene.count('type="Animation"') == len(DEFAULT_CLIP_PILOT)
    assert scene.count('type="AnimationLibrary"') == len(DEFAULT_CLIP_PILOT)
    assert 'tracks/0/path = NodePath("LayoutAnchor/RigRoot:position")' in scene
    assert ':rotation")' in scene
    assert ':rotation_degrees")' not in scene
    assert 'Skeleton2D/pelvis/torso/near_arm_u:rotation' in scene
    assert 'interp = 1' in scene
    assert 'interp = 3' not in scene
    assert 'interp = 4' not in scene
    assert "step = 0.016666667" in scene
    assert "RigDocument" not in scene

    for clip_id in DEFAULT_CLIP_PILOT:
        clip = prepared.library.clips[clip_id]
        assert f'resource_name = "{clip_id}"' in scene
        assert f'length = {clip.duration_s}' in scene or f'length = {clip.duration_s:.1f}' in scene


def test_hold_projection_uses_godot_discrete_update_not_nearest_interpolation():
    lines = _value_track_lines(
        0,
        path="Bone:rotation",
        times=[0.0, 1.0],
        values=["0.0", "1.0"],
        interpolation="hold",
        loop_wrap=False,
    )
    text = "\n".join(lines)
    assert "tracks/0/interp = 1" in text
    assert '"update": 1' in text


def test_expected_clip_export_round_trips_without_source_drift(tmp_path):
    repo, _binding_obj, output = _expected_export(tmp_path)
    changed, worst = apply_clip_export(
        output["expected_clip_export"], repo=repo, check_only=True
    )
    assert changed == 0
    assert worst <= 2e-6


def test_one_animation_transform_edit_changes_only_one_clip(tmp_path, capsys):
    repo, _binding_obj, output = _expected_export(tmp_path, isolated=True)
    raw = json.loads(output["expected_clip_export"].read_text(encoding="utf8"))
    rotation = _track(_clip(raw, "jab"), "bone.near_arm_u.rotation_deg")
    _key_at(rotation, 0.09)["value"] += 17.0
    edited = _write_export(tmp_path, raw)

    clip_dir = repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/clips"
    before = {path: path.read_bytes() for path in clip_dir.glob("*.clip.json")}
    changed, worst = apply_clip_export(edited, repo=repo, check_only=False)
    changed_paths = [path for path in before if path.read_bytes() != before[path]]

    assert changed == 1
    assert worst == pytest.approx(17.0)
    assert [path.name for path in changed_paths] == ["jab.clip.json"]
    assert "updated clip:" in capsys.readouterr().out


def test_clip_local_edit_becomes_sparse_track_without_mutating_named_pose(tmp_path):
    repo, _binding_obj, output = _expected_export(tmp_path, isolated=True)
    raw = json.loads(output["expected_clip_export"].read_text(encoding="utf8"))
    rotation = _track(_clip(raw, "jab"), "bone.near_arm_u.rotation_deg")
    _key_at(rotation, 0.09)["value"] += 12.0
    edited = _write_export(tmp_path, raw)

    changed, _worst = apply_clip_export(edited, repo=repo, check_only=False)
    assert changed == 1

    source = json.loads(
        (repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/clips/jab.clip.json")
        .read_text(encoding="utf8")
    )
    pose_key = source["pose_keys"][2]
    assert pose_key["pose"] == "humanoid/fighting_polygon/jab/contact"
    assert "overrides" not in pose_key
    saved = next(track for track in source["tracks"] if track["target"] == "bone.near_arm_u.rotation_deg")
    assert _key_at(saved, 0.09)["value"] == pytest.approx(_key_at(rotation, 0.09)["value"] )


def test_individual_property_key_can_be_inserted_at_arbitrary_time(tmp_path):
    repo, _binding_obj, output = _expected_export(tmp_path, isolated=True)
    raw = json.loads(output["expected_clip_export"].read_text(encoding="utf8"))
    rotation = _track(_clip(raw, "jab"), "bone.near_arm_u.rotation_deg")
    rotation["keys"].append({"at_s": 0.073, "value": -77.0})
    rotation["keys"].sort(key=lambda key: key["at_s"])
    edited = _write_export(tmp_path, raw)

    changed, _worst = apply_clip_export(edited, repo=repo, check_only=False)
    assert changed == 1
    source = json.loads(
        (repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/clips/jab.clip.json")
        .read_text(encoding="utf8")
    )
    saved = next(track for track in source["tracks"] if track["target"] == "bone.near_arm_u.rotation_deg")
    assert _key_at(saved, 0.073)["value"] == pytest.approx(-77.0)
    assert source["pose_keys"][2]["pose"] == "humanoid/fighting_polygon/jab/contact"


def test_individual_property_key_can_be_deleted(tmp_path):
    repo, _binding_obj, output = _expected_export(tmp_path, isolated=True)
    raw = json.loads(output["expected_clip_export"].read_text(encoding="utf8"))
    rotation = _track(_clip(raw, "jab"), "bone.near_arm_u.rotation_deg")
    rotation["keys"] = [key for key in rotation["keys"] if abs(key["at_s"] - 0.09) > 1e-8]
    edited = _write_export(tmp_path, raw)

    changed, _worst = apply_clip_export(edited, repo=repo, check_only=False)
    assert changed == 1
    source = json.loads(
        (repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/clips/jab.clip.json")
        .read_text(encoding="utf8")
    )
    saved = next(track for track in source["tracks"] if track["target"] == "bone.near_arm_u.rotation_deg")
    assert all(abs(key["at_s"] - 0.09) > 1e-8 for key in saved["keys"])


def test_rotation_winding_is_not_normalized_on_import(tmp_path):
    repo, _binding_obj, output = _expected_export(tmp_path, isolated=True)
    raw = json.loads(output["expected_clip_export"].read_text(encoding="utf8"))
    rotation = _track(_clip(raw, "jab"), "bone.near_arm_u.rotation_deg")
    contact = _key_at(rotation, 0.09)
    original = contact["value"]
    contact["value"] = original + 360.0
    edited = _write_export(tmp_path, raw)

    changed, worst = apply_clip_export(edited, repo=repo, check_only=False)
    assert changed == 1
    assert worst == pytest.approx(360.0)
    source = json.loads(
        (repo / "ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1/clips/jab.clip.json")
        .read_text(encoding="utf8")
    )
    saved = next(track for track in source["tracks"] if track["target"] == "bone.near_arm_u.rotation_deg")
    assert _key_at(saved, 0.09)["value"] == pytest.approx(original + 360.0)


def test_clip_export_omits_sprite_publication_sampling(tmp_path):
    _repo, _binding_obj, output = _expected_export(tmp_path)
    raw = json.loads(output["expected_clip_export"].read_text(encoding="utf8"))
    jab = _clip(raw, "jab")
    assert "sampling" not in jab
    assert "tracks" in jab


def test_render_clip_preview_uses_normal_sprite_renderer(tmp_path):
    gif = tmp_path / "jab.gif"
    strip = tmp_path / "jab.png"
    rendered_gif, rendered_strip = render_clip_preview(
        _binding().path, "jab", output=gif, strip_output=strip
    )

    assert rendered_gif == gif
    assert rendered_strip == strip
    assert gif.stat().st_size > 0
    assert strip.stat().st_size > 0
    plan = clip_sample_plan(_binding().path, "jab")
    with Image.open(gif) as image:
        assert getattr(image, "n_frames", 1) == plan.frame_count
    with Image.open(strip) as image:
        assert image.width > image.height
        assert image.getbbox() is not None


def test_committed_clip_frontend_is_animationplayer_adapter_not_authority():
    repo = repo_root()
    project = repo / "godot" / "pose_editor"
    plugin = (project / "addons/ambition_pose_editor/plugin.gd").read_text(encoding="utf8")
    exporter = (project / "addons/ambition_pose_editor/clip_export.gd").read_text(encoding="utf8")
    headless = (project / "scripts/headless_clip_export.gd").read_text(encoding="utf8")

    assert "Export Ambition Clip Sheet" in plugin
    assert "AnimationPlayer" in exporter
    assert "Animation.TYPE_VALUE" in exporter
    assert 'node_path + ":rotation"' in exporter
    assert "rotation_degrees" not in exporter
    assert "rad_to_deg(float(value) - rest_rotation)" in exporter
    assert "_validate_synchronized_keys" not in exporter
    assert "Animation.UPDATE_DISCRETE" in exporter
    assert "nearest is not a hold" in exporter
    assert "RigDocument" not in exporter
    assert "ambition-godot-clip-export-v2" in exporter
    assert "ClipExport.write_export" in headless


def test_godot_headless_can_round_trip_generated_clips_when_available(tmp_path):
    repo = repo_root()
    godot = _find_godot(None, repo)
    if godot is None:
        pytest.skip("pinned Godot executable not available in test environment")

    project = tmp_path / "pose_editor"
    shutil.copytree(
        repo / "godot" / "pose_editor",
        project,
        ignore=shutil.ignore_patterns("generated", ".godot"),
    )
    output = prepare_binding(_binding().path, project_dir=project, repo=repo)
    _import_godot_resources(godot, project, cwd=repo)
    export = project / "generated" / "exports" / "headless.clips.json"
    scene_res = "res://" + output["clip_scene"].relative_to(project).as_posix()
    export_res = "res://" + export.relative_to(project).as_posix()
    subprocess.run(
        [
            str(godot),
            "--headless",
            "--path",
            str(project),
            "--script",
            "res://scripts/headless_clip_export.gd",
            "--",
            "--scene",
            scene_res,
            "--output",
            export_res,
        ],
        check=True,
        timeout=60,
    )
    changed, worst = apply_clip_export(export, repo=repo, check_only=True)
    assert changed == 0
    assert worst <= 1e-4
