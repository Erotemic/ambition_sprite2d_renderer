from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
from types import SimpleNamespace

from ambition_sprite2d_renderer.targets.characters._svg_fighter_effects import FxCanvas, compose_rig_frame
from ambition_sprite2d_renderer.targets.characters.pca_combat_authoring import author_pca_combat_clips
from ambition_sprite2d_renderer.targets.characters.pca_effects import (
    EFFECTFUL_ANIMATIONS,
    draw_pca_behind,
    draw_pca_front,
)
from ambition_sprite2d_renderer.targets.characters.pca_gameplay import (
    ATTACK_HITBOXES,
    hurtbox_parts_for_rows,
)
from ambition_sprite2d_renderer.targets.characters.pca_motion import PCA_ROWS, POSE_ALIASES
from ambition_sprite2d_renderer.targets.characters import perfect_cellular_automaton as target


ROOT = Path(__file__).resolve().parents[1]
RIG = ROOT / "ambition_sprite2d_renderer" / "targets" / "characters" / "rigged" / "perfect_cellular_automaton.rig.json"


def _fake_world():
    def bone(x, y):
        return SimpleNamespace(origin=(float(x), float(y)))

    return {
        "pelvis": bone(64, 108),
        "torso": bone(64, 84),
        "head": bone(64, 52),
        "near_arm_hand": bone(43, 111),
        "far_arm_hand": bone(88, 108),
        "near_leg_foot": bone(52, 162),
        "far_leg_foot": bone(72, 162),
    }


def test_pca_has_full_authored_geometry_surface():
    hurt = hurtbox_parts_for_rows(PCA_ROWS)
    assert len(PCA_ROWS) >= 130
    assert set(hurt) == {name for name, _frames, _duration in PCA_ROWS}

    expected_attacks = {
        "jab",
        "dash_attack",
        "smash_forward",
        "smash_up",
        "smash_down",
        "air_neutral",
        "air_forward",
        "air_back",
        "air_up",
        "air_down",
        "shoot",
        "special",
        "charge",
        "fly",
        "final_smash",
        "grab",
        "pummel",
        "throw_forward",
        "throw_back",
        "throw_up",
        "throw_down",
    }
    assert expected_attacks <= set(ATTACK_HITBOXES)
    assert len(ATTACK_HITBOXES) >= 30

    row_frames = {name: frames for name, frames, _duration in PCA_ROWS}
    for name, hitbox in ATTACK_HITBOXES.items():
        assert name in row_frames
        active = hitbox.get("active_frames") or []
        assert active
        assert min(active) >= 0
        assert max(active) < row_frames[name]


def test_pca_combat_authoring_graduates_key_aliases_to_bespoke_clips():
    data = json.loads(RIG.read_text(encoding="utf8"))
    before = deepcopy(data["clips"])
    author_pca_combat_clips(data)

    for name in (
        "parry",
        "dash_attack",
        "smash_forward",
        "smash_up",
        "smash_down",
        "grab",
        "throw_forward",
        "throw_back",
        "throw_up",
        "throw_down",
        "final_smash",
    ):
        assert data["clips"][name] != before[name]
        alias = POSE_ALIASES.get(name)
        if alias and alias in data["clips"]:
            assert data["clips"][name]["channels"] != data["clips"][alias]["channels"]


def test_every_pca_signature_effect_draws_pixels():
    world = _fake_world()
    params = {}
    for animation in EFFECTFUL_ANIMATIONS:
        canvas = FxCanvas((164, 228), scale=1, origin=(18, 18))
        draw_pca_behind(animation, canvas, 0.52, world, params)
        draw_pca_front(animation, canvas, 0.52, world, params)
        assert canvas.finish().getchannel("A").getbbox() is not None, animation


def test_fx_canvas_unit_scale_supports_high_resolution_rig_docs():
    canvas = FxCanvas((90, 90), scale=1, unit_scale=3)
    assert canvas.p((2.0, 3.0)) == (6, 9)
    canvas.line([(2.0, 3.0), (8.0, 3.0)], (255, 255, 255, 255), 1.0)
    bbox = canvas.finish().getchannel("A").getbbox()
    assert bbox is not None
    assert bbox[0] <= 6 <= bbox[2]


def test_pca_dedicated_target_publishes_scaled_anchor_space():
    meta = target.frame_meta("idle", 0, 10)
    anchors = meta["anchors"]
    assert {"cell_core", "pelvis", "head", "forward_hand", "rear_hand", "near_foot", "far_foot"} <= set(anchors)
    assert anchors["forward_hand"]["x"] > anchors["rear_hand"]["x"]
    for point in anchors.values():
        assert 0 <= point["x"] <= target.FRAME_SIZE[0]
        assert 0 <= point["y"] <= target.FRAME_SIZE[1]


def test_compose_rig_frame_honors_document_render_scale():
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

    doc = RigDocument(
        {
            "name": "fx_scale_probe",
            "frame": {
                "width": 20,
                "height": 30,
                "ground_y": 25.0,
                "center_x": 10.0,
                "supersample": 1,
                "render_scale": 3,
            },
            "palette": {"body": "#FFFFFFFF"},
            "bones": [{"name": "root", "parent": None, "offset": [0, -10], "length": 0, "rest_angle": 0}],
            "parts": [{"name": "body", "bone": "root", "z": 0, "kind": "circle", "center": [0, 0], "radius": 2, "fill": "body"}],
            "clips": {"idle": {"loop": True, "frames": 1, "duration_ms": 100, "channels": {}}},
            "ik_legs": [],
            "ik_chains": [],
        }
    )

    def fx(canvas, _t, _world, _params):
        canvas.ellipse((10, 10), 2, 2, (255, 255, 255, 255))

    image = compose_rig_frame(doc, "idle", 0, 1, behind=fx, padding=2)
    assert image.size == ((20 + 4) * 3, (30 + 4) * 3)
    assert image.getchannel("A").getbbox() is not None
