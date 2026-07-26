from __future__ import annotations

import copy

import pytest

from ambition_sprite2d_renderer.authoring.gameplay_geometry import (
    ExistingGeometryError,
    collision_entry,
    generate_collision,
    generate_hitbox,
    generate_hurtboxes,
    convert_shape,
    entry_shapes,
    geometry_root,
    hitbox_entry,
    hurtbox_clip_binding,
    hurtbox_entry,
    hurtbox_profile_users,
    hurtbox_profiles,
    hurtbox_source,
    make_hurtbox_override,
    remove_hurtbox_override,
    point_in_shape,
    polygon_is_convex,
    translate_shape,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


def _test_doc() -> RigDocument:
    data = {
        "name": "geometry_test",
        "frame": {
            "width": 64,
            "height": 64,
            "supersample": 1,
            "ground_y": 56.0,
            "center_x": 32.0,
            "ankle_h": 0.0,
        },
        "palette": {"body": "#FFFFFFFF"},
        "bones": [
            {"name": "root", "parent": None, "offset": [0, -20], "length": 0, "rest_angle": 0},
            {"name": "hand", "parent": "root", "offset": [8, -6], "length": 10, "rest_angle": 0},
        ],
        "parts": [
            {
                "name": "body",
                "bone": "root",
                "z": 0,
                "kind": "polygon",
                "points": [[-6, -10], [6, -10], [6, 10], [-6, 10]],
                "fill": "body",
            },
            {
                "name": "arm",
                "bone": "hand",
                "z": 1,
                "kind": "capsule",
                "a": [0, 0],
                "b": [10, 0],
                "radius": 2,
                "fill": "body",
            },
        ],
        "clips": {
            "idle": {"loop": True, "frames": 2, "duration_ms": 100, "channels": {}},
            "attack_side": {
                "loop": False,
                "frames": 3,
                "duration_ms": 80,
                "channels": {
                    "hand": {"keys": [[0.0, -20], [0.5, 10], [1.0, 30]]},
                    "slash": {"keys": [[0.0, 0], [0.5, 1], [1.0, 0]]},
                },
            },
        },
        "ik_legs": [],
        "ik_chains": [],
    }
    return RigDocument(copy.deepcopy(data))


def test_geometry_inspection_does_not_create_block():
    doc = _test_doc()
    assert collision_entry(doc) is None
    assert "gameplay_geometry" not in doc.data
    assert geometry_root(doc, create=False) == {}


def test_generate_collision_and_hurtboxes_are_saved_authoring_data():
    doc = _test_doc()
    result = generate_collision(doc)
    assert result.count == 1
    collision = collision_entry(doc)
    assert entry_shapes(collision)[0]["w"] > 0
    assert collision["provenance"]["method"] == "reference_alpha_bbox_v1"

    result = generate_hurtboxes(doc)
    assert result.count >= 1
    assert entry_shapes(hurtbox_entry(doc, "idle"))[0]["h"] > 0
    assert hurtbox_clip_binding(doc, "idle")["profile"] in hurtbox_profiles(doc)
    assert hurtbox_source(doc, "idle").kind == "profile"


def test_generators_are_non_destructive_by_default():
    doc = _test_doc()
    generate_collision(doc)
    original = copy.deepcopy(collision_entry(doc))
    with pytest.raises(ExistingGeometryError):
        generate_collision(doc)
    assert collision_entry(doc) == original


def test_generate_hitbox_has_window_and_empty_presentation_bindings():
    doc = _test_doc()
    result = generate_hitbox(doc, "attack_side")
    assert result.count == 1
    entry = hitbox_entry(doc, "attack_side")
    assert entry["active_frames"] == [1, 1]
    assert entry_shapes(entry)[0]["w"] > 0
    assert entry["bindings"] == {"vfx": [], "sfx": []}
    assert entry["provenance"]["terminal"] == "hand"


def test_generated_geometry_is_not_used_by_rendering():
    doc = _test_doc()
    before = doc.render_at("idle", 0.0, supersample=1).tobytes()
    generate_collision(doc)
    generate_hurtboxes(doc)
    generate_hitbox(doc, "attack_side")
    after = doc.render_at("idle", 0.0, supersample=1).tobytes()
    assert before == after


def test_player_robot_builder_preserves_existing_geometry(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    script = Path(__file__).parents[1] / "scripts" / "build_player_robot_svg.py"
    spec = importlib.util.spec_from_file_location("build_player_robot_svg_test", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    rig_path = tmp_path / "player_robot.rig.json"
    rig_path.write_text(
        '{"gameplay_geometry":{"version":1,"collision":{"shape":{"kind":"rect","x":1,"y":2,"w":3,"h":4}}}}',
        encoding="utf8",
    )
    monkeypatch.setattr(module, "RIG_JSON", rig_path)
    preserved = module._preserved_gameplay_geometry()
    assert preserved["collision"]["shape"]["w"] == 3


def test_shape_conversion_translation_and_hit_testing():
    rect = {"name": "body", "kind": "rect", "x": 10.0, "y": 20.0, "w": 30.0, "h": 40.0}
    capsule = convert_shape(rect, "capsule")
    assert capsule["name"] == "body"
    assert point_in_shape(capsule, (25.0, 40.0))
    translate_shape(capsule, 5.0, -2.0)
    assert point_in_shape(capsule, (30.0, 38.0))

    polygon = convert_shape(rect, "polygon")
    assert polygon_is_convex(polygon["points"])
    assert point_in_shape(polygon, (25.0, 40.0))
    assert not point_in_shape(polygon, (0.0, 0.0))


def test_legacy_singular_shape_migrates_only_for_mutation():
    entry = {"shape": {"kind": "circle", "cx": 2, "cy": 3, "r": 4}}
    viewed = entry_shapes(entry)
    assert viewed[0]["kind"] == "circle"
    assert "shape" in entry and "shapes" not in entry
    mutated = entry_shapes(entry, create=True)
    assert mutated[0]["r"] == 4
    assert "shape" not in entry and "shapes" in entry


def test_shared_hurtbox_profile_edits_propagate_and_override_detaches():
    doc = _test_doc()
    generate_hurtboxes(doc)
    idle_binding = hurtbox_clip_binding(doc, "idle")
    attack_binding = hurtbox_clip_binding(doc, "attack_side")

    # Force two clips to demonstrate the same shared-profile semantics even if
    # the visual clustering correctly generated separate defaults for them.
    attack_binding.clear()
    attack_binding["profile"] = idle_binding["profile"]
    profile_name = idle_binding["profile"]
    assert hurtbox_profile_users(doc, profile_name) == ("attack_side", "idle")

    idle_shape = entry_shapes(hurtbox_entry(doc, "idle"))[0]
    attack_shape = entry_shapes(hurtbox_entry(doc, "attack_side"))[0]
    assert idle_shape is attack_shape
    idle_shape["x"] += 3.0
    assert entry_shapes(hurtbox_entry(doc, "attack_side"))[0]["x"] == idle_shape["x"]

    override = make_hurtbox_override(doc, "attack_side")
    override_shape = entry_shapes(override)[0]
    assert override_shape is not idle_shape
    override_shape["x"] += 10.0
    assert entry_shapes(hurtbox_entry(doc, "idle"))[0]["x"] != override_shape["x"]
    assert hurtbox_source(doc, "attack_side").kind == "override"
    assert hurtbox_profile_users(doc, profile_name) == ("idle",)

    assert remove_hurtbox_override(doc, "attack_side")
    assert hurtbox_source(doc, "attack_side").kind == "profile"
    assert entry_shapes(hurtbox_entry(doc, "attack_side"))[0] is idle_shape


def test_generated_hurtboxes_use_fewer_profiles_than_clips_when_shapes_match():
    doc = _test_doc()
    # Both clips are deliberately changed to the same visual pose family and
    # dimensions so the profile generator should share one result.
    doc.data["clips"]["attack_side"]["channels"] = {}
    result = generate_hurtboxes(doc)
    assert result.count < len(doc.clips)
    assert hurtbox_clip_binding(doc, "idle")["profile"] == hurtbox_clip_binding(doc, "attack_side")["profile"]


def test_hurtbox_generation_is_non_destructive_by_default():
    doc = _test_doc()
    generate_hurtboxes(doc)
    original = copy.deepcopy(doc.data["gameplay_geometry"]["hurtboxes"])
    with pytest.raises(ExistingGeometryError):
        generate_hurtboxes(doc)
    assert doc.data["gameplay_geometry"]["hurtboxes"] == original
