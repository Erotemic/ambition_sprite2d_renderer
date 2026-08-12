from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
from types import SimpleNamespace

from PIL import Image

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
    author_pca_combat_clips(data)
    authored_once = deepcopy(data["clips"])
    author_pca_combat_clips(data)
    assert data["clips"] == authored_once

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
        assert name in data["clips"]
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


def test_pca_doc_cache_preserves_rig_owned_render_caches(monkeypatch):
    calls = []

    class FakeDoc:
        def __init__(self):
            self.data = {}
            self.clips = {name: {} for name, _frames, _duration in PCA_ROWS}

    def fake_load(path):
        calls.append(path)
        return FakeDoc()

    target._load_doc_cached.cache_clear()
    monkeypatch.setattr(target.RigDocument, "load", fake_load)
    monkeypatch.setattr(target, "author_pca_combat_clips", lambda data: data)

    first = target._load_doc_cached("/tmp/pca.rig.json", 1, 2)
    second = target._load_doc_cached("/tmp/pca.rig.json", 1, 2)
    revised = target._load_doc_cached("/tmp/pca.rig.json", 2, 2)

    assert first is second
    assert revised is not first
    assert calls == ["/tmp/pca.rig.json", "/tmp/pca.rig.json"]
    target._load_doc_cached.cache_clear()


def test_pca_plain_rows_skip_effect_compositor(monkeypatch):
    image = FxCanvas((8, 8), scale=1).finish()

    class FakeDoc:
        def render_at(self, animation, t, *, solved, padding, supersample):
            assert animation == "idle"
            assert t == 0.25
            assert solved == ("world", "params")
            assert padding == target.PADDING
            assert supersample == target.RIG_RENDER_SUPERSAMPLE == 1
            return image

    monkeypatch.setattr(target, "_doc", lambda: FakeDoc())
    monkeypatch.setattr(
        target,
        "_frame_solution",
        lambda animation, frame_idx, frame_count: (0.25, ("world", "params")),
    )
    monkeypatch.setattr(
        target,
        "compose_rig_frame",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("FX compositor used for idle")),
    )

    assert target.render_frame("idle", 0, 8) is image


def test_pca_effect_rows_reuse_precomputed_solution(monkeypatch):
    image = FxCanvas((8, 8), scale=1).finish()
    solved = ({"bone": object()}, {"phase": 0.5})
    seen = {}

    class FakeDoc:
        pass

    doc = FakeDoc()
    monkeypatch.setattr(target, "_doc", lambda: doc)
    monkeypatch.setattr(
        target,
        "_frame_solution",
        lambda animation, frame_idx, frame_count: (0.5, solved),
    )

    def fake_compose(*args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return image

    monkeypatch.setattr(target, "compose_rig_frame", fake_compose)
    assert target.render_frame("shoot", 3, 8) is image
    assert seen["args"][:4] == (doc, "shoot", 3, 8)
    assert seen["kwargs"]["solved"] is solved
    assert seen["kwargs"]["rig_supersample"] == target.RIG_RENDER_SUPERSAMPLE == 1


def test_compose_rig_frame_forwards_rig_supersample():
    seen = {}

    class FakeDoc:
        frame = {"width": 20, "height": 30, "render_scale": 3}

        def frame_time(self, animation, frame_idx, frame_count):
            return 0.25

        def solve(self, animation, t):
            return ({}, {})

        def render_at(self, animation, t, *, solved, padding, supersample):
            seen["animation"] = animation
            seen["t"] = t
            seen["solved"] = solved
            seen["padding"] = padding
            seen["supersample"] = supersample
            return FxCanvas((60, 90), scale=1).finish()

    image = compose_rig_frame(
        FakeDoc(),
        "idle",
        0,
        1,
        padding=0,
        solved=({}, {}),
        rig_supersample=1,
    )
    assert image.size == (60, 90)
    assert seen == {
        "animation": "idle",
        "t": 0.25,
        "solved": ({}, {}),
        "padding": 0,
        "supersample": 1,
    }


def test_fx_canvas_dirty_only_after_drawing():
    canvas = FxCanvas((16, 16), scale=1)
    assert not canvas.dirty
    canvas.line([(1.0, 1.0), (4.0, 4.0)], (255, 255, 255, 255))
    assert canvas.dirty


def test_compose_rig_frame_skips_empty_effect_finishes(monkeypatch):
    import ambition_sprite2d_renderer.targets.characters._svg_fighter_effects as effects

    class FakeDoc:
        frame = {"width": 8, "height": 8, "render_scale": 1}

        def frame_time(self, animation, frame_idx, frame_count):
            return 0.5

        def solve(self, animation, t):
            return ({}, {})

        def render_at(self, animation, t, *, solved, padding, supersample):
            return Image.new("RGBA", (8, 8), (10, 20, 30, 255))

    finish_calls = []
    original_finish = effects.FxCanvas.finish

    def counting_finish(self):
        finish_calls.append(self.dirty)
        return original_finish(self)

    monkeypatch.setattr(effects.FxCanvas, "finish", counting_finish)
    image = effects.compose_rig_frame(
        FakeDoc(),
        "idle",
        0,
        1,
        behind=lambda canvas, t, world, params: None,
        front=lambda canvas, t, world, params: None,
    )

    assert finish_calls == []
    assert image.getpixel((0, 0)) == (10, 20, 30, 255)
