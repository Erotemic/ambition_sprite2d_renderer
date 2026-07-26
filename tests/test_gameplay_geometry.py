from __future__ import annotations

import copy

import pytest

from ambition_sprite2d_renderer.authoring.gameplay_geometry import (
    ExistingGeometryError,
    collision_entry,
    generate_collision,
    generate_hitbox,
    generate_hurtboxes,
    geometry_root,
    hitbox_entry,
    hurtbox_entry,
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
    assert collision["shape"]["w"] > 0
    assert collision["provenance"]["method"] == "reference_alpha_bbox_v1"

    result = generate_hurtboxes(doc)
    assert result.count == 2
    assert hurtbox_entry(doc, "idle")["shape"]["h"] > 0
    assert hurtbox_entry(doc, "attack_side")["provenance"]["frames"] == 3


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
    assert entry["shapes"][0]["w"] > 0
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
